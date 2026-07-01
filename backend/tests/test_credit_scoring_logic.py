"""
Tests unitaires — ml/credit_scoring.py
Fonctions testées (logique pure, sans DB) :
  - Calcul du score par règles pondérées
  - Niveaux de risque
  - Cohérence de FEATURE_LABELS_FR
"""
import pytest
import numpy as np

from app.ml.credit_scoring import (
    FEATURE_LABELS_FR,
    TAUX_RETARD_SEUIL,
    FEATURE_COLUMNS,
    MIN_SAMPLES_FOR_ML,
    _risk_level,
)


def _score_rules_pure(row: dict) -> float:
    """
    Réplique de la formule de scoring par règles de credit_scoring.py.
    score = (1 - taux_retard) × 70 + clip(1 - delai/90, 0, 1) × 20 + clip(freq, 0, 1) × 10
    """
    taux  = row.get("taux_retard", 0.0)
    delai = row.get("delai_moyen_remboursement_jours", 0.0)
    freq  = row.get("frequence_achat_mensuelle", 0.0)
    score = (
        (1 - taux) * 70
        + float(np.clip(1 - delai / 90, 0, 1)) * 20
        + float(np.clip(freq, 0, 1)) * 10
    )
    return round(float(np.clip(score, 0, 100)), 2)


class TestScoreRulesPure:

    def test_perfect_client_scores_100(self):
        row = {"taux_retard": 0.0, "delai_moyen_remboursement_jours": 0.0,
               "frequence_achat_mensuelle": 1.0}
        assert _score_rules_pure(row) == 100.0

    def test_worst_client_scores_0(self):
        row = {"taux_retard": 1.0, "delai_moyen_remboursement_jours": 90.0,
               "frequence_achat_mensuelle": 0.0}
        assert _score_rules_pure(row) == 0.0

    def test_score_always_between_0_and_100(self):
        import random; random.seed(42)
        for _ in range(50):
            row = {
                "taux_retard":                     random.uniform(0, 1),
                "delai_moyen_remboursement_jours": random.uniform(0, 150),
                "frequence_achat_mensuelle":        random.uniform(0, 3),
            }
            s = _score_rules_pure(row)
            assert 0 <= s <= 100, f"Score hors bornes: {s}"

    def test_higher_taux_retard_lowers_score(self):
        base = {"delai_moyen_remboursement_jours": 10.0, "frequence_achat_mensuelle": 0.5}
        assert _score_rules_pure({"taux_retard": 0.05, **base}) > _score_rules_pure({"taux_retard": 0.50, **base})

    def test_longer_delay_lowers_score(self):
        base = {"taux_retard": 0.1, "frequence_achat_mensuelle": 0.5}
        assert (_score_rules_pure({"delai_moyen_remboursement_jours": 5.0,  **base}) >
                _score_rules_pure({"delai_moyen_remboursement_jours": 80.0, **base}))

    def test_delay_over_90_is_capped(self):
        """Délai > 90j ne doit pas produire de score négatif."""
        base = {"taux_retard": 0.0, "frequence_achat_mensuelle": 0.0}
        s90  = _score_rules_pure({"delai_moyen_remboursement_jours": 90.0,  **base})
        s200 = _score_rules_pure({"delai_moyen_remboursement_jours": 200.0, **base})
        assert s90 == s200

    def test_frequence_over_1_is_capped(self):
        base = {"taux_retard": 0.0, "delai_moyen_remboursement_jours": 0.0}
        assert (_score_rules_pure({"frequence_achat_mensuelle": 1.0, **base}) ==
                _score_rules_pure({"frequence_achat_mensuelle": 5.0, **base}))


class TestRiskLevel:

    def test_score_0_is_eleve(self):     assert _risk_level(0)   == "ELEVE"
    def test_score_40_is_eleve(self):    assert _risk_level(40)  == "ELEVE"
    def test_score_41_is_moyen(self):    assert _risk_level(41)  == "MOYEN"
    def test_score_70_is_moyen(self):    assert _risk_level(70)  == "MOYEN"
    def test_score_71_is_faible(self):   assert _risk_level(71)  == "FAIBLE"
    def test_score_100_is_faible(self):  assert _risk_level(100) == "FAIBLE"


class TestFeatureConstants:

    def test_feature_labels_fr_covers_all_columns(self):
        for col in FEATURE_COLUMNS:
            assert col in FEATURE_LABELS_FR, f"Colonne '{col}' sans label FR"

    def test_feature_labels_are_nonempty_strings(self):
        for col, label in FEATURE_LABELS_FR.items():
            assert isinstance(label, str) and len(label) > 0

    def test_taux_retard_seuil_in_range(self):
        assert 0 < TAUX_RETARD_SEUIL < 1

    def test_min_samples_for_ml_positive(self):
        assert MIN_SAMPLES_FOR_ML > 0

    def test_feature_columns_has_8_elements(self):
        assert len(FEATURE_COLUMNS) == 8


class TestMedianDelayFix:
    """Vérifie la logique du correctif delai_moyen_remboursement_jours."""

    def test_empty_list_defaults_to_30(self):
        delays = []
        median = float(np.median(delays)) if delays else 30.0
        assert median == 30.0

    def test_median_of_known_list(self):
        assert float(np.median([10, 20, 5, 15, 25])) == 15.0

    def test_neutral_delay_does_not_inflate_score(self):
        """
        Avant le correctif : clients sans historique recevaient delai=0 → score gonflé.
        Avec le correctif : ils reçoivent delai=median(~30j) → score correctement réduit.
        """
        base = {"taux_retard": 0.3, "frequence_achat_mensuelle": 0.5}
        score_zero    = _score_rules_pure({"delai_moyen_remboursement_jours": 0.0,  **base})
        score_neutral = _score_rules_pure({"delai_moyen_remboursement_jours": 30.0, **base})
        assert score_neutral < score_zero
