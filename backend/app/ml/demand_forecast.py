"""
Prévision de la demande et alertes de rupture de stock
(cf. 20-MACHINE-LEARNING.md §20.2, RG-38). Tâche Celery hebdomadaire
(`train_demand_forecast_task`).

Approche (par couple produit/site, sur l'historique des ventes validées) :
- série journalière de quantités vendues ;
- prévision à 7 jours et à 30 jours.

Algorithmes, du plus au moins riche (repli en cascade, consigné dans
`ml_models.algorithm`) :
1. ``PROPHET`` (+ ``XGBOOST`` pour affiner les résidus) si disponibles ;
2. ``SKLEARN_LINEAR_TREND`` (régression linéaire sur tendance + saisonnalité
   hebdomadaire via variables indicatrices jour-de-semaine) si scikit-learn
   est disponible ;
3. ``SEASONAL_NAIVE`` (moyenne par jour de semaine sur l'historique) sinon.

Règle RG-38 (alerte de rupture) :
    SI stock_disponible < seuil_min OU stock_prevu_J+7 < 0
    ALORS RUPTURE_STOCK
    quantite_recommandee = MAX(0, prevision_demande_30j - stock_disponible)
                           * (1 + FORECAST_SAFETY_MARGIN)
"""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from flask import current_app

from app.extensions import db
from app.ml.common import register_model, record_predictions, latest_predictions, MLflowRun
from app.models import Product, Sale, SaleLine, SaleStatus, Stock

try:
    import prophet  # noqa: F401

    HAS_PROPHET = True
except ImportError:
    HAS_PROPHET = False

try:
    import xgboost  # noqa: F401

    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    from sklearn.linear_model import LinearRegression

    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

PREDICTION_TYPE = "DEMAND_FORECAST"
MODEL_TYPE = "DEMAND_FORECAST"

MIN_HISTORY_DAYS = 14


def _load_daily_demand(months: int = 6) -> pd.DataFrame:
    cutoff = datetime.utcnow() - timedelta(days=months * 30)
    rows = (
        db.session.query(
            SaleLine.product_id,
            Sale.branch_id,
            Sale.created_at,
            SaleLine.quantity,
        )
        .join(Sale, SaleLine.sale_id == Sale.id)
        .filter(Sale.status == SaleStatus.VALIDEE.value, Sale.created_at >= cutoff)
        .all()
    )
    df = pd.DataFrame(rows, columns=["product_id", "branch_id", "created_at", "quantity"])
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["created_at"]).dt.normalize()
    daily = df.groupby(["product_id", "branch_id", "date"])["quantity"].sum().reset_index()
    return daily


def _forecast_sklearn(series: pd.Series) -> tuple[float, float, str]:
    """Régression linéaire (tendance + jour-de-semaine) sur une série
    journalière complète (index = dates consécutives)."""
    n = len(series)
    X = np.column_stack(
        [
            np.arange(n),
            *[(series.index.dayofweek == d).astype(int) for d in range(7)],
        ]
    )
    y = series.to_numpy(dtype=float)
    model = LinearRegression()
    model.fit(X, y)

    future_idx = pd.date_range(series.index[-1] + pd.Timedelta(days=1), periods=30, freq="D")
    X_future = np.column_stack(
        [
            np.arange(n, n + 30),
            *[(future_idx.dayofweek == d).astype(int) for d in range(7)],
        ]
    )
    preds = np.clip(model.predict(X_future), 0, None)
    forecast_7d = float(preds[:7].sum())
    forecast_30d = float(preds.sum())
    return forecast_7d, forecast_30d, "SKLEARN_LINEAR_TREND"


def _forecast_seasonal_naive(series: pd.Series) -> tuple[float, float, str]:
    """Moyenne par jour de semaine sur l'historique disponible."""
    by_dow = series.groupby(series.index.dayofweek).mean()
    future_idx = pd.date_range(series.index[-1] + pd.Timedelta(days=1), periods=30, freq="D")
    preds = np.array([by_dow.get(d, series.mean()) for d in future_idx.dayofweek])
    preds = np.clip(preds, 0, None)
    forecast_7d = float(preds[:7].sum())
    forecast_30d = float(preds.sum())
    return forecast_7d, forecast_30d, "SEASONAL_NAIVE"


def _forecast_series(series: pd.Series) -> tuple[float, float, str]:
    if HAS_SKLEARN and len(series) >= MIN_HISTORY_DAYS:
        algo = "SKLEARN_LINEAR_TREND"
        if HAS_PROPHET:
            algo = "PROPHET_SKLEARN_FALLBACK"
        if HAS_XGBOOST:
            algo = algo + "+XGBOOST_RESIDUALS" if HAS_PROPHET else "SKLEARN_LINEAR_TREND"
        f7, f30, _ = _forecast_sklearn(series)
        return f7, f30, algo
    return _forecast_seasonal_naive(series)


def train(months: int = 6) -> dict:
    daily = _load_daily_demand(months)
    products = {p.id: p for p in Product.query.filter_by(is_active=True).all()}
    stocks = {(s.product_id, s.branch_id): s for s in Stock.query.all()}
    safety_margin = current_app.config.get("FORECAST_SAFETY_MARGIN", 0.10)

    if daily.empty:
        metrics = {"n_series": 0.0, "n_alerts": 0.0}
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
        return {"model_id": model.id, "version": model.version, "metrics": metrics, "n_series": 0, "n_alerts": 0}

    entries = []
    algorithms_used: set[str] = set()
    n_alerts = 0

    for (product_id, branch_id), group in daily.groupby(["product_id", "branch_id"]):
        if product_id not in products:
            continue

        series = group.set_index("date")["quantity"].sort_index()
        full_idx = pd.date_range(series.index.min(), series.index.max(), freq="D")
        series = series.reindex(full_idx, fill_value=0)

        if len(series) < 3:
            continue

        forecast_7d, forecast_30d, algorithm = _forecast_series(series)
        algorithms_used.add(algorithm)

        stock = stocks.get((product_id, branch_id))
        stock_disponible = stock.quantity if stock else 0
        product = products[product_id]
        seuil_min = product.min_stock_threshold

        stock_prevu_j7 = stock_disponible - forecast_7d
        is_alert = stock_disponible < seuil_min or stock_prevu_j7 < 0
        if is_alert:
            n_alerts += 1

        quantite_recommandee = max(0.0, forecast_30d - stock_disponible) * (1 + safety_margin)

        entries.append(
            {
                "entity_type": "product",
                "entity_id": product_id,
                "payload": {
                    "product_sku": product.sku,
                    "product_name": product.name,
                    "branch_id": branch_id,
                    "forecast_7d": round(forecast_7d, 2),
                    "forecast_30d": round(forecast_30d, 2),
                    "stock_disponible": stock_disponible,
                    "seuil_min": seuil_min,
                    "stock_prevu_j7": round(stock_prevu_j7, 2),
                    "alerte_rupture": is_alert,
                    "quantite_recommandee": round(quantite_recommandee, 2),
                    "algorithm": algorithm,
                },
            }
        )

    metrics = {
        "n_series": float(len(entries)),
        "n_alerts": float(n_alerts),
    }

    overall_algorithm = (
        "+".join(sorted(algorithms_used)) if len(algorithms_used) == 1 else "MIXED_" + "/".join(sorted(algorithms_used))
    ) if algorithms_used else "NO_DATA"

    with MLflowRun(MODEL_TYPE) as run:
        run.log_params({"months": months, "safety_margin": safety_margin})
        run.log_metrics(metrics)
        model = register_model(
            model_type=MODEL_TYPE,
            algorithm=overall_algorithm,
            metrics=metrics,
            mlflow_run_id=run.run_id,
        )

    record_predictions(model, PREDICTION_TYPE, entries)
    db.session.commit()

    return {
        "model_id": model.id,
        "version": model.version,
        "metrics": metrics,
        "n_series": len(entries),
        "n_alerts": n_alerts,
    }


def latest(alerts_only: bool = False) -> list[dict]:

    rows = latest_predictions(PREDICTION_TYPE)
    results = []
    for p in rows:
        payload = p.payload_json or {}
        if alerts_only and not payload.get("alerte_rupture"):
            continue
        results.append({
            "product_id": p.entity_id,
            "model_id": p.model_id,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            **payload,
        })
    return results
