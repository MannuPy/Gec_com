"""
Tests unitaires — ml/demand_forecast.py
Fonctions testées (pures, sans DB) :
  - _compute_data_confidence
  - _forecast_seasonal_naive
  - _forecast_sklearn
"""
import pytest
import pandas as pd
import numpy as np

# Import direct des fonctions pures — pas d'app_context nécessaire
from app.ml.demand_forecast import (
    _compute_data_confidence,
    _forecast_seasonal_naive,
    _forecast_sklearn,
)


class TestDataConfidence:
    """_compute_data_confidence(series_len, algorithm) → 'HIGH'|'MEDIUM'|'LOW'"""

    def test_prophet_many_points_is_high(self):
        assert _compute_data_confidence(60, "PROPHET_BURKINA_HOLIDAYS") == "HIGH"

    def test_prophet_many_points_boundary(self):
        assert _compute_data_confidence(61, "PROPHET_BURKINA_HOLIDAYS") == "HIGH"

    def test_prophet_few_points_is_medium(self):
        # Prophet avec 30-59 jours → MEDIUM
        assert _compute_data_confidence(30, "PROPHET_BURKINA_HOLIDAYS") == "MEDIUM"
        assert _compute_data_confidence(59, "PROPHET_BURKINA_HOLIDAYS") == "MEDIUM"

    def test_sklearn_sufficient_data_is_medium(self):
        assert _compute_data_confidence(14, "SKLEARN_LINEAR_TREND") == "MEDIUM"
        assert _compute_data_confidence(50, "SKLEARN_LINEAR_TREND") == "MEDIUM"

    def test_seasonal_naive_always_low(self):
        assert _compute_data_confidence(5, "SEASONAL_NAIVE") == "LOW"
        assert _compute_data_confidence(100, "SEASONAL_NAIVE") == "LOW"

    def test_prophet_very_few_points_is_low(self):
        # < 14 jours avec Prophet → LOW
        assert _compute_data_confidence(10, "PROPHET_BURKINA_HOLIDAYS") == "LOW"

    def test_unknown_algorithm_is_low(self):
        assert _compute_data_confidence(50, "UNKNOWN_ALGO") == "LOW"

    def test_zero_points_is_low(self):
        assert _compute_data_confidence(0, "SKLEARN_LINEAR_TREND") == "LOW"


class TestForecastSeasonalNaive:
    """_forecast_seasonal_naive(series) → (forecast_7d, forecast_30d, label)"""

    def _make_series(self, n_weeks=8, daily_mean=10):
        """Crée une série temporelle de n_weeks semaines avec moyenne daily_mean."""
        idx = pd.date_range("2025-01-01", periods=n_weeks * 7, freq="D")
        values = np.full(n_weeks * 7, float(daily_mean))
        return pd.Series(values, index=idx)

    def test_returns_tuple_of_three(self):
        s = self._make_series()
        result = _forecast_seasonal_naive(s)
        assert len(result) == 3

    def test_algorithm_label(self):
        _, _, label = _forecast_seasonal_naive(self._make_series())
        assert label == "SEASONAL_NAIVE"

    def test_forecast_7d_positive(self):
        s = self._make_series(daily_mean=5)
        f7, _, _ = _forecast_seasonal_naive(s)
        assert f7 > 0

    def test_forecast_30d_greater_than_7d(self):
        s = self._make_series(daily_mean=10)
        f7, f30, _ = _forecast_seasonal_naive(s)
        assert f30 > f7

    def test_constant_demand_forecast_approx(self):
        """Série constante à 10 unités/jour → ~70 unités sur 7 jours."""
        s = self._make_series(daily_mean=10)
        f7, f30, _ = _forecast_seasonal_naive(s)
        assert abs(f7 - 70) < 5   # tolérance ±5%
        assert abs(f30 - 300) < 20

    def test_zero_demand_gives_zero_forecast(self):
        s = self._make_series(daily_mean=0)
        f7, f30, _ = _forecast_seasonal_naive(s)
        assert f7 == 0.0
        assert f30 == 0.0


class TestForecastSklearn:
    """_forecast_sklearn(series) → (forecast_7d, forecast_30d, label)"""

    def _make_growing_series(self, n_days=30):
        idx = pd.date_range("2025-01-01", periods=n_days, freq="D")
        values = np.arange(1, n_days + 1, dtype=float)
        return pd.Series(values, index=idx)

    def test_returns_tuple_of_three(self):
        s = self._make_growing_series()
        result = _forecast_sklearn(s)
        assert len(result) == 3

    def test_algorithm_label(self):
        _, _, label = _forecast_sklearn(self._make_growing_series())
        assert label == "SKLEARN_LINEAR_TREND"

    def test_growing_series_forecast_positive(self):
        s = self._make_growing_series(60)
        f7, f30, _ = _forecast_sklearn(s)
        assert f7 > 0
        assert f30 > f7

    def test_forecast_30d_approx_4x_7d(self):
        """Sur tendance linéaire stable, 30j ≈ 4x 7j."""
        s = self._make_growing_series(60)
        f7, f30, _ = _forecast_sklearn(s)
        ratio = f30 / f7
        assert 3.0 < ratio < 6.0  # ratio approximatif raisonnable
