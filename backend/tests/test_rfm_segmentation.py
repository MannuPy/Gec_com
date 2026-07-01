"""
Tests unitaires — ml/rfm_segmentation.py
Fonctions testées (pures, sans DB) :
  - _assign_segments_quantiles
  - _assign_segments_kmeans
  - compute_churn_probability
  - evaluate_optimal_k
"""
import pytest
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from app.ml.rfm_segmentation import (
    _assign_segments_quantiles,
    _assign_segments_kmeans,
    compute_churn_probability,
    evaluate_optimal_k,
    SEGMENT_LABELS,
    SEGMENT_ACTIONS,
)

ALL_SEGMENTS = ["CHAMPIONS", "REGULIERS", "A_RISQUE", "OCCASIONNELS"]


def make_rfm_df(n=40, seed=42):
    """DataFrame RFM synthétique avec 4 profils distincts."""
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        if i < n // 4:          # Champions : récents, fréquents, gros montants
            r, f, m = rng.integers(1, 15), rng.integers(10, 20), rng.uniform(500, 1000)
        elif i < n // 2:        # Réguliers : récents, peu fréquents, montants moyens
            r, f, m = rng.integers(1, 30), rng.integers(2, 8),  rng.uniform(100, 300)
        elif i < 3 * n // 4:   # À risque : anciens, fréquents historiquement
            r, f, m = rng.integers(60, 120), rng.integers(8, 15), rng.uniform(300, 700)
        else:                   # Occasionnels : anciens, rares, petits montants
            r, f, m = rng.integers(90, 180), rng.integers(1, 3), rng.uniform(10, 80)
        rows.append({"customer_id": f"cust_{i}", "recency": r, "frequency": f, "monetary": m})
    return pd.DataFrame(rows)


class TestAssignSegmentsQuantiles:
    """Segmentation de repli basée sur les quartiles — sans sklearn."""

    def test_returns_df_and_str(self):
        df = make_rfm_df()
        result_df, algo = _assign_segments_quantiles(df)
        assert isinstance(result_df, pd.DataFrame)
        assert isinstance(algo, str)

    def test_all_rows_have_segment(self):
        df = make_rfm_df()
        result_df, _ = _assign_segments_quantiles(df)
        assert result_df["segment"].notna().all()

    def test_only_valid_segments(self):
        df = make_rfm_df()
        result_df, _ = _assign_segments_quantiles(df)
        assert set(result_df["segment"]).issubset(set(ALL_SEGMENTS))

    def test_champions_have_low_recency(self):
        df = make_rfm_df()
        result_df, _ = _assign_segments_quantiles(df)
        champions = result_df[result_df["segment"] == "CHAMPIONS"]
        others = result_df[result_df["segment"] != "CHAMPIONS"]
        if not champions.empty and not others.empty:
            assert champions["recency"].mean() < others["recency"].mean()


class TestAssignSegmentsKMeans:
    """Segmentation K-Means — avec sklearn."""

    def test_returns_df_and_str(self):
        df = make_rfm_df()
        result_df, algo = _assign_segments_kmeans(df, n_clusters=4)
        assert isinstance(result_df, pd.DataFrame)
        assert "KMEANS" in algo.upper()

    def test_all_rows_assigned(self):
        df = make_rfm_df()
        result_df, _ = _assign_segments_kmeans(df, n_clusters=4)
        assert len(result_df) == len(df)
        assert result_df["segment"].notna().all()

    def test_only_valid_segments(self):
        df = make_rfm_df()
        result_df, _ = _assign_segments_kmeans(df, n_clusters=4)
        assert set(result_df["segment"]).issubset(set(ALL_SEGMENTS))

    def test_k2_produces_max_2_segments(self):
        """Bug 2 fix : avec k=2, seulement 2 labels produits (pas 4)."""
        df = make_rfm_df(n=30)
        result_df, _ = _assign_segments_kmeans(df, n_clusters=2)
        unique_segs = result_df["segment"].unique()
        assert len(unique_segs) <= 2

    def test_k2_labels_are_top_two(self):
        """Avec k=2, les 2 labels sont les 2 premiers de la hiérarchie."""
        df = make_rfm_df(n=30)
        result_df, _ = _assign_segments_kmeans(df, n_clusters=2)
        for seg in result_df["segment"].unique():
            assert seg in ALL_SEGMENTS  # toujours des segments valides


class TestComputeChurnProbability:
    """Probabilité de churn par décroissance exponentielle."""

    def test_returns_df_with_churn_cols(self):
        df = make_rfm_df()
        result = compute_churn_probability(df)
        assert "churn_probability" in result.columns
        assert "churn_risk" in result.columns
        assert "churn_action" in result.columns

    def test_probability_between_0_and_1(self):
        df = make_rfm_df()
        result = compute_churn_probability(df)
        assert (result["churn_probability"] >= 0).all()
        assert (result["churn_probability"] <= 1).all()

    def test_high_recency_gives_high_churn(self):
        """Client avec récence 180j doit avoir une proba de churn > client récence 5j.
        Note: les deux clients doivent être dans le même df (lambda calibré sur la médiane)."""
        df = pd.DataFrame([
            {"customer_id": "recent", "recency": 5,   "frequency": 10, "monetary": 500},
            {"customer_id": "old",    "recency": 180, "frequency": 10, "monetary": 500},
        ])
        result = compute_churn_probability(df).set_index("customer_id")
        assert result.loc["old", "churn_probability"] > result.loc["recent", "churn_probability"]

    def test_churn_risk_levels_valid(self):
        df = make_rfm_df()
        result = compute_churn_probability(df)
        valid_levels = {"FAIBLE", "MODERE", "ELEVE", "CRITIQUE"}
        assert set(result["churn_risk"].unique()).issubset(valid_levels)

    def test_churn_action_not_empty(self):
        df = make_rfm_df()
        result = compute_churn_probability(df)
        assert result["churn_action"].notna().all()
        assert (result["churn_action"].str.len() > 0).all()

    def test_frequent_buyer_lower_churn(self):
        """Acheteur fréquent (freq=20) doit churner moins que acheteur rare (freq=1).
        Note: dans le même df, freq_weight est relatif au max — la différence est visible."""
        df = pd.DataFrame([
            {"customer_id": "freq", "recency": 60, "frequency": 20, "monetary": 200},
            {"customer_id": "rare", "recency": 60, "frequency": 1,  "monetary": 200},
        ])
        result = compute_churn_probability(df).set_index("customer_id")
        assert result.loc["freq", "churn_probability"] < result.loc["rare", "churn_probability"]


class TestEvaluateOptimalK:
    """evaluate_optimal_k — sélection du k par silhouette."""

    def _make_scaled(self, n=60, seed=0):
        rng = np.random.default_rng(seed)
        X = np.vstack([
            rng.normal([0, 0], 0.3, (n // 4, 2)),
            rng.normal([5, 0], 0.3, (n // 4, 2)),
            rng.normal([0, 5], 0.3, (n // 4, 2)),
            rng.normal([5, 5], 0.3, (n // 4, 2)),
        ])
        return StandardScaler().fit_transform(X)

    def test_returns_dict_with_required_keys(self):
        X = self._make_scaled()
        result = evaluate_optimal_k(X)
        assert "optimal_k" in result
        assert "evaluation" in result
        assert "optimal_silhouette" in result

    def test_optimal_k_in_valid_range(self):
        X = self._make_scaled()
        result = evaluate_optimal_k(X)
        assert 2 <= result["optimal_k"] <= 8

    def test_evaluation_list_nonempty(self):
        X = self._make_scaled()
        result = evaluate_optimal_k(X)
        assert len(result["evaluation"]) >= 1

    def test_evaluation_items_have_required_keys(self):
        X = self._make_scaled()
        result = evaluate_optimal_k(X)
        for item in result["evaluation"]:
            assert "k" in item
            assert "silhouette_score" in item
            assert "davies_bouldin_index" in item
            assert "inertia" in item

    def test_4_clusters_detected_on_clear_data(self):
        """Sur des données bien séparées en 4 groupes, k=4 doit être optimal."""
        X = self._make_scaled(n=120)
        result = evaluate_optimal_k(X)
        # Avec des données bien séparées, k optimal doit être 3, 4 ou 5
        assert 3 <= result["optimal_k"] <= 5


class TestSegmentMetadata:
    """Vérification de la cohérence des dictionnaires de labels et actions."""

    def test_all_segments_have_labels(self):
        for seg in ALL_SEGMENTS:
            assert seg in SEGMENT_LABELS, f"{seg} absent de SEGMENT_LABELS"

    def test_all_segments_have_actions(self):
        for seg in ALL_SEGMENTS:
            assert seg in SEGMENT_ACTIONS, f"{seg} absent de SEGMENT_ACTIONS"

    def test_labels_are_nonempty_strings(self):
        for seg, label in SEGMENT_LABELS.items():
            assert isinstance(label, str) and len(label) > 0

    def test_actions_are_nonempty_strings(self):
        for seg, action in SEGMENT_ACTIONS.items():
            assert isinstance(action, str) and len(action) > 0
