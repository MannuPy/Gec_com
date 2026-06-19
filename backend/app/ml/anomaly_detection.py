"""
Detection d'anomalies sur les ventes recentes via Isolation Forest
(cf. 20-MACHINE-LEARNING.md section 20.5).
"""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from flask import current_app

from app.extensions import db
from app.ml.common import register_model, record_predictions, latest_predictions, MLflowRun
from app.models import FsTransactionFeatures, Sale, SaleLine, SaleStatus, User

try:
    from sklearn.ensemble import IsolationForest
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

PREDICTION_TYPE = "ANOMALY"
MODEL_TYPE = "ANOMALY_DETECTION"

FEATURES = [
    "montant_total",
    "remise_taux",
    "heure_vente",
    "ecart_vs_moyenne_produit",
    "ecart_vs_moyenne_vendeur",
]


def _load_sales_dataframe_from_feature_store(days: int = 90) -> pd.DataFrame | None:
    cutoff = datetime.utcnow() - timedelta(days=days)
    rows = (
        FsTransactionFeatures.query.join(Sale, FsTransactionFeatures.sale_id == Sale.id)
        .filter(Sale.created_at >= cutoff)
        .all()
    )
    if not rows:
        return None

    return pd.DataFrame(
        [
            {
                "sale_id": r.sale_id,
                "reference": r.sale.reference if r.sale else None,
                "branch_id": r.branch_id,
                "cashier_id": r.cashier_id,
                "product_id": r.product_id,
                "montant_total": float(r.montant_total),
                "remise_taux": r.remise_taux,
                "heure_vente": r.heure_vente,
                "ecart_vs_moyenne_produit": r.ecart_vs_moyenne_produit,
                "ecart_vs_moyenne_vendeur": r.ecart_vs_moyenne_vendeur,
            }
            for r in rows
        ]
    )


def _load_sales_dataframe_direct(days: int = 90) -> pd.DataFrame:
    cutoff = datetime.utcnow() - timedelta(days=days)
    sales = (
        Sale.query.filter(
            Sale.status.in_([SaleStatus.VALIDEE.value, SaleStatus.EN_ATTENTE_APPROBATION.value]),
            Sale.created_at >= cutoff,
        )
        .all()
    )
    if not sales:
        return pd.DataFrame()

    rows = []
    for sale in sales:
        main_product_id = sale.lines[0].product_id if sale.lines else None
        rows.append(
            {
                "sale_id": sale.id,
                "reference": sale.reference,
                "branch_id": sale.branch_id,
                "cashier_id": sale.cashier_id,
                "product_id": main_product_id,
                "montant_total": float(sale.total),
                "remise_taux": int(sale.discount_rate),
                "heure_vente": sale.created_at.hour,
            }
        )
    df = pd.DataFrame(rows)

    product_mean = df.groupby("product_id")["montant_total"].transform("mean")
    cashier_mean = df.groupby("cashier_id")["montant_total"].transform("mean")
    df["ecart_vs_moyenne_produit"] = (df["montant_total"] - product_mean) / product_mean.replace(0, np.nan)
    df["ecart_vs_moyenne_vendeur"] = (df["montant_total"] - cashier_mean) / cashier_mean.replace(0, np.nan)
    df[["ecart_vs_moyenne_produit", "ecart_vs_moyenne_vendeur"]] = df[
        ["ecart_vs_moyenne_produit", "ecart_vs_moyenne_vendeur"]
    ].fillna(0.0)
    return df


def _load_sales_dataframe(days: int = 90) -> pd.DataFrame:
    fs_df = _load_sales_dataframe_from_feature_store(days)
    if fs_df is not None:
        return fs_df
    return _load_sales_dataframe_direct(days)


def _detect_isolation_forest(df: pd.DataFrame, contamination: float) -> tuple[pd.Series, pd.Series, str]:
    model = IsolationForest(n_estimators=200, contamination=contamination, random_state=42)
    X = df[FEATURES].to_numpy()
    model.fit(X)
    scores = pd.Series(model.decision_function(X), index=df.index)
    threshold = np.quantile(scores, contamination)
    is_anomaly = scores < threshold
    return scores, is_anomaly, "ISOLATION_FOREST"


def _detect_zscore(df: pd.DataFrame) -> tuple[pd.Series, pd.Series, str]:
    z = (df["montant_total"] - df["montant_total"].mean()) / (df["montant_total"].std(ddof=0) or 1)
    scores = -z.abs()
    is_anomaly = z.abs() > 3
    return scores, is_anomaly, "RULE_BASED_ZSCORE"


def train(days: int = 90) -> dict:
    df = _load_sales_dataframe(days)
    contamination = current_app.config.get("ANOMALY_CONTAMINATION", 0.02)

    if df.empty or len(df) < 10:
        metrics = {"n_sales": float(len(df)), "n_anomalies": 0.0}
        with MLflowRun(MODEL_TYPE) as run:
            run.log_metrics(metrics)
            model = register_model(
                model_type=MODEL_TYPE,
                algorithm="NO_DATA",
                metrics=metrics,
                mlflow_run_id=run.run_id,
            )
        record_predictions(model, PREDICTION_TYPE, [])
        db.session.commit()
        return {"model_id": model.id, "version": model.version, "metrics": metrics, "n_anomalies": 0}

    if HAS_SKLEARN:
        scores, is_anomaly, algorithm = _detect_isolation_forest(df, contamination)
    else:
        scores, is_anomaly, algorithm = _detect_zscore(df)

    df["score"] = scores
    df["is_anomaly"] = is_anomaly

    anomalies = df[df["is_anomaly"]].sort_values("score")
    metrics = {
        "n_sales": float(len(df)),
        "n_anomalies": float(len(anomalies)),
        "anomaly_rate": float(len(anomalies) / len(df)),
    }

    with MLflowRun(MODEL_TYPE) as run:
        run.log_params({"days": days, "contamination": contamination})
        run.log_metrics(metrics)
        model = register_model(
            model_type=MODEL_TYPE,
            algorithm=algorithm,
            metrics=metrics,
            mlflow_run_id=run.run_id,
        )

    users = {u.id: u for u in User.query.all()}
    entries = []
    for _, row in anomalies.iterrows():
        cashier = users.get(row["cashier_id"])
        reasons = []
        if row.get("remise_taux", 0) >= 15:
            reasons.append("Remise elevee")
        if row.get("ecart_vs_moyenne_produit", 0) > 1:
            reasons.append("Montant largement superieur a la moyenne du produit")
        if row.get("ecart_vs_moyenne_vendeur", 0) > 1:
            reasons.append("Montant largement superieur a la moyenne du vendeur")
        if row.get("heure_vente", 12) < 6 or row.get("heure_vente", 12) > 21:
            reasons.append("Vente hors horaires habituels")
        if not reasons:
            reasons.append("Profil statistique atypique")

        entries.append(
            {
                "entity_type": "sale",
                "entity_id": row["sale_id"],
                "payload": {
                    "reference": row.get("reference"),
                    "branch_id": row["branch_id"],
                    "cashier_name": cashier.full_name if cashier else None,
                    "montant_total": row["montant_total"],
                    "remise_taux": int(row.get("remise_taux", 0)),
                    "score": round(float(row["score"]), 4),
                    "reasons": reasons,
                },
            }
        )

    record_predictions(model, PREDICTION_TYPE, entries)
    db.session.commit()

    return {"model_id": model.id, "version": model.version, "metrics": metrics, "n_anomalies": len(entries)}


def latest() -> list[dict]:
    return [
        {
            "entity_id": p.entity_id,
            "model_id": p.model_id,
            "created_at": p.created_at.isoformat(),
            **p.payload_json,
        }
        for p in latest_predictions(PREDICTION_TYPE)
    ]
