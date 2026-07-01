"""
Prevision de la demande et alertes de rupture de stock
(cf. 20-MACHINE-LEARNING.md section 20.2, RG-38).
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
    by_dow = series.groupby(series.index.dayofweek).mean()
    future_idx = pd.date_range(series.index[-1] + pd.Timedelta(days=1), periods=30, freq="D")
    preds = np.array([by_dow.get(d, series.mean()) for d in future_idx.dayofweek])
    preds = np.clip(preds, 0, None)
    forecast_7d = float(preds[:7].sum())
    forecast_30d = float(preds.sum())
    return forecast_7d, forecast_30d, "SEASONAL_NAIVE"




def _forecast_prophet(series: pd.Series) -> tuple[float, float, str]:
    """
    Prevision avec Prophet + evenements calendaires du Burkina Faso.
    Necessite au moins 30 jours d historique.
    Prophet est installe (requirements.txt v1.1.5) et importe ici
    localement pour eviter une erreur d importation au demarrage si
    l installation est absente.
    """
    from prophet import Prophet  # import local — Prophet peut etre lent a charger

    # Evenements culturels du Burkina Faso comme regresseurs saisonniers
    burkina_events = pd.DataFrame([
        {"holiday": "tabaski",       "ds": "2025-06-07", "lower_window": -7, "upper_window": 3},
        {"holiday": "tabaski",       "ds": "2026-05-27", "lower_window": -7, "upper_window": 3},
        {"holiday": "ramadan_start", "ds": "2025-03-01", "lower_window": -3, "upper_window": 30},
        {"holiday": "ramadan_start", "ds": "2026-02-18", "lower_window": -3, "upper_window": 30},
        {"holiday": "independence",  "ds": "2025-08-05", "lower_window": -1, "upper_window": 1},
        {"holiday": "independence",  "ds": "2026-08-05", "lower_window": -1, "upper_window": 1},
        {"holiday": "noel",          "ds": "2025-12-25", "lower_window": -5, "upper_window": 2},
        {"holiday": "noel",          "ds": "2026-12-25", "lower_window": -5, "upper_window": 2},
    ])
    burkina_events["ds"] = pd.to_datetime(burkina_events["ds"])

    # Format Prophet : colonnes ds (date) et y (valeur)
    df_prophet = pd.DataFrame({
        "ds": pd.to_datetime(series.index),
        "y": series.values.astype(float),
    })

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        seasonality_mode="multiplicative",  # Adapte aux pics forts (Tabaski, etc.)
        holidays=burkina_events,
    )
    model.fit(df_prophet)

    # Previsions sur les 30 prochains jours
    future = model.make_future_dataframe(periods=30, freq="D")
    forecast = model.predict(future)

    # Extraire les 30 jours futurs (les N derniers du DataFrame predit)
    preds = forecast.tail(30)["yhat"].clip(lower=0).values
    forecast_7d = float(preds[:7].sum())
    forecast_30d = float(preds.sum())
    return forecast_7d, forecast_30d, "PROPHET_BURKINA_HOLIDAYS"


def _compute_data_confidence(series_len: int, algorithm: str) -> str:
    """Évalue la confiance dans la prévision selon la quantité de données et l'algorithme utilisé.

    Niveaux :
      HIGH   — Prophet + ≥ 60 jours de données historiques
      MEDIUM — LinearRegression + ≥ 14 jours, ou Prophet + 30-59 jours
      LOW    — Seasonal Naive, ou moins de 14 jours de données
    """
    if algorithm == "PROPHET_BURKINA_HOLIDAYS" and series_len >= 60:
        return "HIGH"
    if algorithm in ("PROPHET_BURKINA_HOLIDAYS", "SKLEARN_LINEAR_TREND") and series_len >= 14:
        return "MEDIUM"
    return "LOW"


def _forecast_series(series: pd.Series) -> tuple[float, float, str]:
    """Cascade d algorithmes : Prophet (>=30j) -> LinearRegression (>=14j) -> Seasonal Naive.

    Retourne (forecast_7d, forecast_30d, algorithm_reel_utilise).
    Le label reflete l algorithme REELLEMENT execute, pas celui souhaite.
    Prophet est utilise en priorite quand disponible et quand l historique
    est suffisant (>= 30 jours). En cas d erreur Prophet (CPU, memoire,
    donnees insuffisantes), bascule automatiquement sur LinearRegression.
    """
    if HAS_PROPHET and len(series) >= 30:
        try:
            return _forecast_prophet(series)
        except Exception:
            pass  # Bascule sur LinearRegression si Prophet echoue

    if HAS_SKLEARN and len(series) >= MIN_HISTORY_DAYS:
        return _forecast_sklearn(series)  # retourne "SKLEARN_LINEAR_TREND"

    return _forecast_seasonal_naive(series)  # retourne "SEASONAL_NAIVE"


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
                    "data_confidence": _compute_data_confidence(len(series), algorithm),
                    "nb_jours_historique": len(series),
                },
            }
        )

    metrics = {
        "n_series": float(len(entries)),
        "n_alerts": float(n_alerts),
    }

    if algorithms_used:
        if len(algorithms_used) == 1:
            overall_algorithm = next(iter(algorithms_used))
        else:
            overall_algorithm = "MIXED_" + "/".join(sorted(algorithms_used))
    else:
        overall_algorithm = "NO_DATA"

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
