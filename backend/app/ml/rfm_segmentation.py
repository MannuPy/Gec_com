"""
Segmentation client RFM (Recence / Frequence / Montant) par clustering
K-Means (cf. 20-MACHINE-LEARNING.md section 20.4). Frequence de
reentrainement : mensuelle (tache Celery `compute_rfm_segments_task`).

Repli : si scikit-learn est indisponible ou si le nombre de clients est
inferieur au nombre de clusters demandes, une segmentation par quartiles
(regles) est appliquee et consignee comme algorithme `RULE_BASED_QUANTILES`.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from app.extensions import db
from app.ml.common import register_model, record_predictions, latest_predictions, MLflowRun
from app.models import Customer, FsCustomerRfm, Sale, SaleLine, SaleStatus

try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

PREDICTION_TYPE = "RFM_SEGMENT"
MODEL_TYPE = "RFM_SEGMENTATION"

SEGMENT_LABELS = {
    "CHAMPIONS": "Champions",
    "REGULIERS": "Clients reguliers",
    "A_RISQUE": "A risque",
    "OCCASIONNELS": "Occasionnels",
}

SEGMENT_ACTIONS = {
    "CHAMPIONS": "Programme de fidelite, credit etendu",
    "REGULIERS": "Relances ciblees",
    "A_RISQUE": "Campagne de reactivation",
    "OCCASIONNELS": "Communication standard",
}


def _load_rfm_from_feature_store() -> pd.DataFrame | None:
    """Charge le RFM depuis la Feature Store (`fs_customer_rfm`, cf.
    21-PIPELINE-ETL.md section 21.6) si elle a ete alimentee par le pipeline
    ETL (`etl_build_features`).

    Retourne `None` si la table est vide, pour repli sur le calcul direct
    (`_load_rfm_dataframe_direct`)."""
    rows = FsCustomerRfm.query.all()
    if not rows:
        return None

    return pd.DataFrame(
        [
            {
                "customer_id": r.customer_id,
                "recency": r.recency_days,
                "frequency": r.frequency,
                "monetary": float(r.monetary),
            }
            for r in rows
        ]
    )


def _load_rfm_dataframe_direct(months: int = 12) -> pd.DataFrame:
    cutoff = datetime.utcnow() - timedelta(days=months * 30)
    rows = (
        db.session.query(
            Sale.customer_id,
            Sale.created_at,
            SaleLine.line_total,
        )
        .join(SaleLine, SaleLine.sale_id == Sale.id)
        .filter(
            Sale.status == SaleStatus.VALIDEE.value,
            Sale.created_at >= cutoff,
            Sale.customer_id.isnot(None),
        )
        .all()
    )
    df = pd.DataFrame(rows, columns=["customer_id", "created_at", "line_total"])
    if df.empty:
        return df

    df["line_total"] = df["line_total"].astype(float)
    now = datetime.utcnow()
    grouped = df.groupby("customer_id").agg(
        recency=("created_at", lambda s: (now - s.max()).days),
        frequency=("created_at", "count"),
        monetary=("line_total", "sum"),
    )
    return grouped.reset_index()


def _load_rfm_dataframe(months: int = 12) -> pd.DataFrame:
    """Charge le RFM (RF-26) : Feature Store en priorite
    (`fs_customer_rfm`, alimentee par `etl_build_features`), repli sur le
    calcul direct si elle est vide."""
    fs_df = _load_rfm_from_feature_store()
    if fs_df is not None:
        return fs_df
    return _load_rfm_dataframe_direct(months)


def _assign_segments_kmeans(df: pd.DataFrame, n_clusters: int = 4) -> tuple[pd.DataFrame, str]:
    X = df[["recency", "frequency", "monetary"]].to_numpy()
    X_scaled = StandardScaler().fit_transform(X)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df = df.copy()
    df["cluster"] = kmeans.fit_predict(X_scaled)

    # Ordonner les clusters : Champions = faible recence, forte frequence/montant
    centers = pd.DataFrame(kmeans.cluster_centers_, columns=["recency", "frequency", "monetary"])
    centers["score"] = centers["frequency"] + centers["monetary"] - centers["recency"]
    ranking = centers["score"].sort_values(ascending=False).index.tolist()

    labels = ["CHAMPIONS", "REGULIERS", "A_RISQUE", "OCCASIONNELS"][: len(ranking)]
    cluster_to_label = {cluster: labels[i] for i, cluster in enumerate(ranking)}
    df["segment"] = df["cluster"].map(cluster_to_label)
    return df, "KMEANS"


def _assign_segments_quantiles(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    df = df.copy()
    r_median = df["recency"].median()
    fm_median = (df["frequency"] + df["monetary"] / max(df["monetary"].max(), 1)).median()
    fm_score = df["frequency"] + df["monetary"] / max(df["monetary"].max(), 1)

    def label(row_recency: float, row_fm: float) -> str:
        if row_recency <= r_median and row_fm >= fm_median:
            return "CHAMPIONS"
        if row_recency <= r_median and row_fm < fm_median:
            return "REGULIERS"
        if row_recency > r_median and row_fm >= fm_median:
            return "A_RISQUE"
        return "OCCASIONNELS"

    df["segment"] = [label(r, fm) for r, fm in zip(df["recency"], fm_score)]
    return df, "RULE_BASED_QUANTILES"



def evaluate_optimal_k(X_scaled: "np.ndarray", k_range: range = range(2, 9)) -> dict:
    """
    Évalue le nombre optimal de clusters via :
    - Score de silhouette (qualité intra-cluster vs inter-cluster, plus haut = mieux)
    - Index de Davies-Bouldin (compacité des clusters, plus bas = mieux)
    - Inertie (méthode du coude / Elbow)

    Nécessite scikit-learn (appelée uniquement si HAS_SKLEARN=True).
    """
    from sklearn.metrics import silhouette_score, davies_bouldin_score

    evaluation = []
    for k in k_range:
        if len(X_scaled) < k * 3:   # au moins 3 points par cluster
            break
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)

        sil  = float(silhouette_score(X_scaled, labels))
        db   = float(davies_bouldin_score(X_scaled, labels))
        iner = float(km.inertia_)

        evaluation.append({
            "k":                    k,
            "silhouette_score":     round(sil,  4),
            "davies_bouldin_index": round(db,   4),
            "inertia":              round(iner, 2),
        })

    if not evaluation:
        return {"optimal_k": 4, "evaluation": [], "method": "DEFAULT"}

    best = max(evaluation, key=lambda r: r["silhouette_score"])

    if best["silhouette_score"] >= 0.71:
        interp = "Excellente séparation"
    elif best["silhouette_score"] >= 0.51:
        interp = "Bonne séparation"
    elif best["silhouette_score"] >= 0.26:
        interp = "Séparation faible — chevauchement partiel"
    else:
        interp = "Aucune structure naturelle détectée"

    return {
        "optimal_k":               best["k"],
        "optimal_silhouette":      best["silhouette_score"],
        "optimal_davies_bouldin":  best["davies_bouldin_index"],
        "evaluation":              evaluation,
        "interpretation":          interp,
        "method":                  "MAX_SILHOUETTE",
    }



def compute_churn_probability(df_rfm: pd.DataFrame,
                               churn_threshold_days: int = 90) -> pd.DataFrame:
    """
    Probabilité de churn par décroissance exponentielle calibrée.

    P(churn) = 1 - exp(-λ × recency)
    λ est calibré sur la médiane de recency (demi-vie = médiane).
    Ajustement par la fréquence : les acheteurs réguliers churner moins.
    """
    if df_rfm.empty:
        return df_rfm

    median_recency = df_rfm["recency"].median()
    lambda_param = np.log(2) / max(median_recency, 1)

    df_rfm = df_rfm.copy()
    df_rfm["churn_probability"] = (
        1 - np.exp(-lambda_param * df_rfm["recency"])
    ).clip(0, 1).round(4)

    # Atténuation par la fréquence (acheteur régulier = moins de risque de churn)
    freq_max = df_rfm["frequency"].max()
    freq_weight = (df_rfm["frequency"] / max(freq_max, 1)).fillna(0)
    df_rfm["churn_probability"] = (
        df_rfm["churn_probability"] * (1 - 0.25 * freq_weight)
    ).clip(0, 1).round(4)

    df_rfm["churn_risk"] = pd.cut(
        df_rfm["churn_probability"],
        bins=[0, 0.30, 0.60, 0.80, 1.0],
        labels=["FAIBLE", "MODERE", "ELEVE", "CRITIQUE"],
        include_lowest=True,
    ).astype(str)

    action_map = {
        "FAIBLE":   "Maintenir la relation standard",
        "MODERE":   "Envoyer une offre de fidélité",
        "ELEVE":    "Relance personnalisée recommandée",
        "CRITIQUE": "Contact direct urgent — risque de perte définitive",
    }
    df_rfm["churn_action"] = df_rfm["churn_risk"].map(action_map)
    return df_rfm


def train(months: int = 12, n_clusters: int = None) -> dict:
    df = _load_rfm_dataframe(months)

    if df.empty:
        metrics = {"n_customers": 0.0}
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
        return {"model_id": model.id, "version": model.version, "metrics": metrics, "n_customers": 0}

    # Évaluer le k optimal si sklearn disponible et données suffisantes
    k_eval: dict = {}
    if HAS_SKLEARN and len(df) >= 6:
        from sklearn.preprocessing import StandardScaler as _SS
        X_scaled = _SS().fit_transform(df[["recency", "frequency", "monetary"]])
        if len(df) >= 20:
            k_eval = evaluate_optimal_k(X_scaled)
        effective_k = n_clusters if n_clusters is not None else k_eval.get("optimal_k", 4)
        df, algorithm = _assign_segments_kmeans(df, effective_k)
    else:
        effective_k = n_clusters if n_clusters is not None else 4
        df, algorithm = _assign_segments_quantiles(df)

    # Calcul de la probabilité de churn pour chaque client
    df = compute_churn_probability(df)

    customers = {c.id: c for c in Customer.query.all()}

    segment_counts = df["segment"].value_counts().to_dict()
    # Garantir que les 4 segments apparaissent toujours dans les métriques,
    # même si k_optimal < 4 (ex: k=2 → seulement CHAMPIONS et REGULIERS produits).
    ALL_SEGMENTS = ["CHAMPIONS", "REGULIERS", "A_RISQUE", "OCCASIONNELS"]
    full_segment_counts = {seg: int(segment_counts.get(seg, 0)) for seg in ALL_SEGMENTS}
    metrics = {
        "n_customers": float(len(df)),
        "n_clusters_used": float(effective_k),
        "k_evaluation": k_eval,
        **{f"n_{k.lower()}": float(v) for k, v in full_segment_counts.items()},
        "segments_actifs": [s for s in ALL_SEGMENTS if full_segment_counts[s] > 0],
    }

    with MLflowRun(MODEL_TYPE) as run:
        run.log_params({"months": months, "n_clusters": effective_k})
        run.log_metrics(metrics)
        model = register_model(
            model_type=MODEL_TYPE,
            algorithm=algorithm,
            metrics=metrics,
            mlflow_run_id=run.run_id,
        )

    entries = []
    for _, row in df.iterrows():
        customer = customers.get(row["customer_id"])
        entries.append(
            {
                "entity_type": "customer",
                "entity_id": row["customer_id"],
                "payload": {
                    "customer_name": customer.full_name if customer else None,
                    "recency_days": int(row["recency"]),
                    "frequency": int(row["frequency"]),
                    "monetary": round(float(row["monetary"]), 2),
                    "segment": row["segment"],
                    "segment_label": SEGMENT_LABELS.get(row["segment"], row["segment"]),
                    "recommended_action": SEGMENT_ACTIONS.get(row["segment"], ""),
                    "churn_probability": float(row.get("churn_probability", 0.0)),
                    "churn_risk": row.get("churn_risk", "INCONNU"),
                    "churn_action": row.get("churn_action", ""),
                },
            }
        )

    record_predictions(model, PREDICTION_TYPE, entries)
    db.session.commit()

    return {"model_id": model.id, "version": model.version, "metrics": metrics, "n_customers": len(df)}


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
