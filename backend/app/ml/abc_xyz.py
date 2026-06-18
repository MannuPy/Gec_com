"""
Classification ABC/XYZ des produits (cf. 20-MACHINE-LEARNING.md §20.1).

- **ABC** : classement par contribution cumulée au chiffre d'affaires
  (A = 80% du CA cumulé, B = 15% suivants, C = les 5% restants).
- **XYZ** : régularité de la demande, mesurée par le coefficient de
  variation (écart-type / moyenne) de la demande hebdomadaire
  (X = régulier CV < 0.5, Y = variable 0.5-1, Z = irrégulier CV > 1).

Algorithme déterministe (règles pandas) — aucune dépendance ML lourde,
fréquence de réentraînement hebdomadaire (tâche Celery `compute_abc_xyz_task`).
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

from app.extensions import db
from app.ml.common import register_model, record_predictions, MLflowRun
from app.models import Product, Sale, SaleLine, SaleStatus

PREDICTION_TYPE = "ABC_XYZ"
MODEL_TYPE = "ABC_XYZ"


def _load_sales_dataframe(months: int = 6) -> pd.DataFrame:
    cutoff = datetime.utcnow() - timedelta(days=months * 30)
    rows = (
        db.session.query(
            SaleLine.product_id,
            Sale.created_at,
            SaleLine.quantity,
            SaleLine.line_total,
        )
        .join(Sale, SaleLine.sale_id == Sale.id)
        .filter(Sale.status == SaleStatus.VALIDEE.value, Sale.created_at >= cutoff)
        .all()
    )
    return pd.DataFrame(rows, columns=["product_id", "created_at", "quantity", "line_total"])


def compute_abc_xyz(months: int = 6) -> pd.DataFrame:
    """Retourne un DataFrame indexé par `product_id` avec colonnes
    `revenue`, `abc_class`, `cv`, `xyz_class`."""
    df = _load_sales_dataframe(months)
    products = {p.id: p for p in Product.query.filter_by(is_active=True).all()}

    if df.empty:
        return pd.DataFrame(
            columns=["product_id", "revenue", "abc_class", "cv", "xyz_class"]
        )

    df["line_total"] = df["line_total"].astype(float)
    df["week"] = pd.to_datetime(df["created_at"]).dt.to_period("W").apply(lambda p: p.start_time)

    # --- ABC : contribution au CA cumulé ---
    revenue_by_product = df.groupby("product_id")["line_total"].sum().sort_values(ascending=False)
    total_revenue = revenue_by_product.sum()
    cumulative = revenue_by_product.cumsum() / total_revenue if total_revenue else revenue_by_product.cumsum()

    abc_classes = {}
    for product_id, cum_share in cumulative.items():
        if cum_share <= 0.80:
            abc_classes[product_id] = "A"
        elif cum_share <= 0.95:
            abc_classes[product_id] = "B"
        else:
            abc_classes[product_id] = "C"

    # --- XYZ : coefficient de variation de la demande hebdomadaire ---
    weekly = df.groupby(["product_id", "week"])["quantity"].sum().reset_index()
    cv_by_product = {}
    for product_id, group in weekly.groupby("product_id"):
        mean = group["quantity"].mean()
        std = group["quantity"].std(ddof=0) or 0.0
        cv = (std / mean) if mean else float("inf")
        cv_by_product[product_id] = cv

    rows = []
    for product_id in revenue_by_product.index:
        cv = cv_by_product.get(product_id, float("inf"))
        if cv < 0.5:
            xyz = "X"
        elif cv <= 1.0:
            xyz = "Y"
        else:
            xyz = "Z"
        rows.append(
            {
                "product_id": product_id,
                "product_name": products[product_id].name if product_id in products else None,
                "product_sku": products[product_id].sku if product_id in products else None,
                "revenue": float(revenue_by_product[product_id]),
                "abc_class": abc_classes[product_id],
                "cv": None if cv == float("inf") else round(float(cv), 3),
                "xyz_class": xyz,
            }
        )

    return pd.DataFrame(rows)


def train(months: int = 6) -> dict:
    """Calcule la classification ABC/XYZ et l'enregistre dans `predictions`."""
    df = compute_abc_xyz(months)

    metrics = {
        "n_products": float(len(df)),
        "n_class_a": float((df["abc_class"] == "A").sum()) if not df.empty else 0.0,
        "n_class_b": float((df["abc_class"] == "B").sum()) if not df.empty else 0.0,
        "n_class_c": float((df["abc_class"] == "C").sum()) if not df.empty else 0.0,
    }

    with MLflowRun(MODEL_TYPE) as run:
        run.log_params({"months": months})
        run.log_metrics(metrics)

        model = register_model(
            model_type=MODEL_TYPE,
            algorithm="PANDAS_RULES_ABC_XYZ",
            metrics=metrics,
            mlflow_run_id=run.run_id,
        )

    entries = [
        {
            "entity_type": "product",
            "entity_id": row["product_id"],
            "payload": {
                "product_sku": row["product_sku"],
                "product_name": row["product_name"],
                "revenue": row["revenue"],
                "abc_class": row["abc_class"],
                "cv": row["cv"],
                "xyz_class": row["xyz_class"],
                "combined_class": f"{row['abc_class']}{row['xyz_class']}",
            },
        }
        for _, row in df.iterrows()
    ]
    record_predictions(model, PREDICTION_TYPE, entries)
    db.session.commit()

    return {"model_id": model.id, "version": model.version, "metrics": metrics, "n_products": len(df)}


def latest() -> list[dict]:
    from app.ml.common import latest_predictions

    return [
        {"product_id": p.entity_id, "model_id": p.model_id, "created_at": p.created_at.isoformat(), **p.payload_json}
        for p in latest_predictions(PREDICTION_TYPE)
    ]
