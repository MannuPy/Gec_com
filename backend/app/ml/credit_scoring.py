"""
Score de credit client (cf. 20-MACHINE-LEARNING.md section 20.3).
Score final 0-100, niveau de risque : 0-40 ELEVE, 41-70 MOYEN, 71-100 FAIBLE.
"""
from __future__ import annotations

import hashlib
from datetime import datetime

import numpy as np
import pandas as pd

from app.extensions import db
from app.ml.common import register_model, record_predictions, latest_predictions, MLflowRun
from app.models import Customer, CustomerType, FsCustomerCreditFeatures, PaymentType, Sale, SaleStatus
from app.models.feature_store import FeatureDataSource

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_val_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

PREDICTION_TYPE = "CREDIT_SCORE"
MODEL_TYPE = "CREDIT_SCORING"

MIN_SAMPLES_FOR_ML = 20
TAUX_RETARD_SEUIL = 0.20


def _deterministic_repayment_stats(customer_id: str) -> tuple[float, float]:
    digest = hashlib.sha256(customer_id.encode("utf-8")).digest()
    seed = int.from_bytes(digest[:4], "big")
    rng = np.random.RandomState(seed)
    taux_retard = float(rng.beta(2, 5))
    delai = float(np.clip(taux_retard * 90 + rng.normal(0, 5), 0, 120))
    return round(taux_retard, 4), round(delai, 1)


def _load_customer_features_from_feature_store() -> pd.DataFrame | None:
    rows = FsCustomerCreditFeatures.query.all()
    if not rows:
        return None

    data = []
    for r in rows:
        data.append(
            {
                "customer_id": r.customer_id,
                "customer_name": r.customer.full_name if r.customer else None,
                "nb_achats_credit_total": r.nb_achats_credit_total,
                "montant_moyen_achat": float(r.montant_moyen_achat),
                "delai_moyen_remboursement_jours": r.delai_moyen_remboursement_jours,
                "taux_retard": r.taux_retard,
                "anciennete_client_mois": r.anciennete_client_mois,
                "frequence_achat_mensuelle": r.frequence_achat_mensuelle,
                "solde_du_actuel": float(r.solde_du_actuel),
                "is_technicien": 1 if r.is_technicien else 0,
                "bon_payeur": 1 if r.bon_payeur else 0,
                "data_source": r.data_source,
            }
        )
    return pd.DataFrame(data)


def _load_customer_features_direct() -> pd.DataFrame:
    customers = Customer.query.all()
    now = datetime.utcnow()

    rows = []
    for customer in customers:
        credit_sales = (
            Sale.query.filter_by(
                customer_id=customer.id,
                payment_type=PaymentType.CREDIT.value,
                status=SaleStatus.VALIDEE.value,
            ).all()
        )
        if not credit_sales:
            continue

        nb_achats = len(credit_sales)
        montant_moyen = float(np.mean([float(s.total) for s in credit_sales]))
        anciennete_mois = max((now - customer.created_at).days / 30.0, 1 / 30.0)
        frequence_mensuelle = nb_achats / anciennete_mois

        taux_retard, delai_moyen = _deterministic_repayment_stats(customer.id)

        rows.append(
            {
                "customer_id": customer.id,
                "customer_name": customer.full_name,
                "nb_achats_credit_total": nb_achats,
                "montant_moyen_achat": montant_moyen,
                "delai_moyen_remboursement_jours": delai_moyen,
                "taux_retard": taux_retard,
                "anciennete_client_mois": round(anciennete_mois, 2),
                "frequence_achat_mensuelle": round(frequence_mensuelle, 3),
                "solde_du_actuel": float(customer.credit_balance),
                "is_technicien": 1 if customer.customer_type == CustomerType.TECHNICIEN.value else 0,
                "bon_payeur": 1 if taux_retard < TAUX_RETARD_SEUIL else 0,
                "data_source": FeatureDataSource.SIMULATED.value,
            }
        )

    return pd.DataFrame(rows)


def _load_customer_features() -> pd.DataFrame:
    fs_df = _load_customer_features_from_feature_store()
    if fs_df is not None:
        return fs_df
    return _load_customer_features_direct()


FEATURE_COLUMNS = [
    "nb_achats_credit_total",
    "montant_moyen_achat",
    "delai_moyen_remboursement_jours",
    "taux_retard",
    "anciennete_client_mois",
    "frequence_achat_mensuelle",
    "solde_du_actuel",
    "is_technicien",
]


def _risk_level(score: float) -> str:
    if score <= 40:
        return "ELEVE"
    if score <= 70:
        return "MOYEN"
    return "FAIBLE"


def _score_ml(df: pd.DataFrame) -> tuple[np.ndarray, dict, str]:
    X = df[FEATURE_COLUMNS].to_numpy()
    y = df["bon_payeur"].to_numpy()

    n_splits = min(5, int(min(np.bincount(y))))
    n_splits = max(n_splits, 2)
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

    rf = RandomForestClassifier(n_estimators=200, random_state=42, max_depth=6)
    logreg = LogisticRegression(max_iter=1000)

    rf_acc = cross_val_score(rf, X, y, cv=skf, scoring="accuracy").mean()
    logreg_acc = cross_val_score(logreg, X, y, cv=skf, scoring="accuracy").mean()

    rf.fit(X, y)
    scores = rf.predict_proba(X)[:, 1] * 100

    metrics = {
        "n_customers": float(len(df)),
        "n_bon_payeur": float(y.sum()),
        "random_forest_cv_accuracy": round(float(rf_acc), 4),
        "logistic_regression_cv_accuracy": round(float(logreg_acc), 4),
        "cv_folds": float(n_splits),
    }
    return scores, metrics, "RANDOM_FOREST+LOGISTIC_REGRESSION_CV"


def _score_rule_based(df: pd.DataFrame) -> tuple[np.ndarray, dict, str]:
    scores = (
        (1 - df["taux_retard"]) * 70
        + np.clip(1 - df["delai_moyen_remboursement_jours"] / 90, 0, 1) * 20
        + np.clip(df["frequence_achat_mensuelle"], 0, 1) * 10
    )
    scores = np.clip(scores, 0, 100)
    metrics = {
        "n_customers": float(len(df)),
        "n_bon_payeur": float(df["bon_payeur"].sum()),
    }
    return scores.to_numpy(), metrics, "RULE_BASED_SCORING"


def train() -> dict:
    df = _load_customer_features()

    if df.empty:
        metrics = {"n_customers": 0.0, "note": "Aucun client avec historique de vente a credit."}
        with MLflowRun(MODEL_TYPE) as run:
            run.log_metrics({"n_customers": 0.0})
            model = register_model(
                model_type=MODEL_TYPE,
                algorithm="NO_DATA",
                metrics=metrics,
                mlflow_run_id=run.run_id,
            )
        record_predictions(model, PREDICTION_TYPE, [])
        db.session.commit()
        return {"model_id": model.id, "version": model.version, "metrics": metrics, "n_customers": 0}

    n_classes = df["bon_payeur"].nunique()
    use_ml = (
        HAS_SKLEARN
        and len(df) >= MIN_SAMPLES_FOR_ML
        and n_classes == 2
        and min(np.bincount(df["bon_payeur"])) >= 2
    )

    if use_ml:
        scores, metrics, algorithm = _score_ml(df)
    else:
        scores, metrics, algorithm = _score_rule_based(df)

    n_real = int((df["data_source"] == FeatureDataSource.REAL.value).sum())
    metrics["n_data_source_real"] = float(n_real)
    metrics["n_data_source_simulated"] = float(len(df) - n_real)
    metrics["note"] = (
        "taux_retard et delai_moyen_remboursement_jours : REAL si historique "
        "customer_payments suffisant, sinon derives de facon deterministe "
        "(hash customer.id) - cf. 20-MACHINE-LEARNING.md section 20.6.2"
    )

    with MLflowRun(MODEL_TYPE) as run:
        run.log_metrics({k: v for k, v in metrics.items() if isinstance(v, (int, float))})
        model = register_model(
            model_type=MODEL_TYPE,
            algorithm=algorithm,
            metrics=metrics,
            mlflow_run_id=run.run_id,
        )

    entries = []
    for (_, row), score in zip(df.iterrows(), scores):
        score = round(float(score), 1)
        entries.append(
            {
                "entity_type": "customer",
                "entity_id": row["customer_id"],
                "payload": {
                    "customer_name": row["customer_name"],
                    "score": score,
                    "risk_level": _risk_level(score),
                    "nb_achats_credit_total": int(row["nb_achats_credit_total"]),
                    "montant_moyen_achat": round(float(row["montant_moyen_achat"]), 2),
                    "delai_moyen_remboursement_jours": row["delai_moyen_remboursement_jours"],
                    "taux_retard": row["taux_retard"],
                    "anciennete_client_mois": row["anciennete_client_mois"],
                    "frequence_achat_mensuelle": row["frequence_achat_mensuelle"],
                    "solde_du_actuel": round(float(row["solde_du_actuel"]), 2),
                    "data_source": row.get("data_source", FeatureDataSource.SIMULATED.value),
                },
            }
        )

    record_predictions(model, PREDICTION_TYPE, entries)
    db.session.commit()

    return {
        "model_id": model.id,
        "version": model.version,
        "metrics": metrics,
        "n_customers": len(df),
    }


def latest() -> list[dict]:
    return [
        {
            "customer_id": p.entity_id,
            "model_id": p.model_id,
            "created_at": p.created_at.isoformat(),
            **p.payload_json,
        }
        for p in latest_predictions(PREDICTION_TYPE)
    ]
