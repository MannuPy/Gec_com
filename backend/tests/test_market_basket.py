"""
Tests unitaires — Market Basket Analysis (app/ml/market_basket.py).

Fonctions testées :
  - _fallback_cooccurrence : algorithme co-occurrence (pur Python, 0 DB)
  - _apriori_rules         : algorithme Apriori via mlxtend (si disponible)

Aucun accès DB requis — les fonctions sont testées directement avec des
listes de transactions en entrée.
"""
import pytest
import pandas as pd

# Fonctions pures testables sans DB
from app.ml.market_basket import _fallback_cooccurrence, HAS_MLXTEND

if HAS_MLXTEND:
    from app.ml.market_basket import _apriori_rules


# ---------------------------------------------------------------------------
# Jeux de données de test
# ---------------------------------------------------------------------------

TRANSACTIONS_RICHES = [
    ["clé_plate", "tournevis", "huile_moteur"],
    ["clé_plate", "tournevis"],
    ["huile_moteur", "filtre_huile"],
    ["clé_plate", "huile_moteur", "filtre_huile"],
    ["tournevis", "clé_plate"],
    ["filtre_huile", "huile_moteur"],
    ["clé_plate", "tournevis", "filtre_huile"],
    ["huile_moteur", "clé_plate"],
    ["tournevis", "filtre_huile"],
    ["clé_plate", "filtre_huile"],
]

TRANSACTIONS_MINIMALES = [
    ["produit_A", "produit_B"],
    ["produit_A", "produit_C"],
    ["produit_B", "produit_C"],
]

TRANSACTIONS_MONO_PRODUIT = [
    ["clé_plate"],
    ["tournevis"],
    ["huile_moteur"],
]


# ---------------------------------------------------------------------------
# Tests _fallback_cooccurrence
# ---------------------------------------------------------------------------

class TestFallbackCooccurrence:

    def test_retourne_liste(self):
        """La fonction retourne bien une liste."""
        result = _fallback_cooccurrence(TRANSACTIONS_RICHES)
        assert isinstance(result, list)

    def test_regles_non_vides_sur_transactions_riches(self):
        """Avec suffisamment de transactions, au moins une règle est produite."""
        result = _fallback_cooccurrence(TRANSACTIONS_RICHES)
        assert len(result) > 0

    def test_structure_d_une_regle(self):
        """Chaque règle contient les clés attendues avec les bons types."""
        result = _fallback_cooccurrence(TRANSACTIONS_RICHES)
        assert len(result) > 0
        rule = result[0]
        assert "antecedent" in rule
        assert "consequent" in rule
        assert "support" in rule
        assert "confidence" in rule
        assert "lift" in rule
        assert isinstance(rule["support"], float)
        assert isinstance(rule["confidence"], float)
        assert isinstance(rule["lift"], float)

    def test_support_dans_bornes(self):
        """Le support est compris entre 0 et 1 pour toutes les règles."""
        result = _fallback_cooccurrence(TRANSACTIONS_RICHES)
        for rule in result:
            assert 0.0 <= rule["support"] <= 1.0, (
                f"Support hors bornes : {rule['support']}"
            )

    def test_confidence_dans_bornes(self):
        """La confiance est comprise entre 0 et 1 pour toutes les règles."""
        result = _fallback_cooccurrence(TRANSACTIONS_RICHES)
        for rule in result:
            assert 0.0 <= rule["confidence"] <= 1.0, (
                f"Confidence hors bornes : {rule['confidence']}"
            )

    def test_tri_par_frequence(self):
        """
        Les règles co-occurrence sont triées par fréquence (pair_counts.most_common),
        pas par lift. La paire la plus fréquente arrive en premier.
        """
        result = _fallback_cooccurrence(TRANSACTIONS_RICHES)
        if len(result) > 1:
            # co_occurrences décroissant (tri most_common)
            counts = [r["co_occurrences"] for r in result]
            assert counts == sorted(counts, reverse=True)

    def test_transactions_vides_retourne_liste_vide(self):
        """Un input vide ne lève pas d'exception et retourne une liste vide."""
        result = _fallback_cooccurrence([])
        assert result == []

    def test_transactions_mono_produit_retourne_liste_vide(self):
        """Des transactions à un seul produit ne peuvent pas former de paires."""
        result = _fallback_cooccurrence(TRANSACTIONS_MONO_PRODUIT)
        assert result == []

    def test_top_n_limite_le_nombre_de_regles(self):
        """Le paramètre top_n limite le nombre de règles retournées."""
        result = _fallback_cooccurrence(TRANSACTIONS_RICHES, top_n=3)
        assert len(result) <= 3

    def test_produits_attendus_presents(self):
        """Les produits fréquents apparaissent dans les règles produites."""
        result = _fallback_cooccurrence(TRANSACTIONS_RICHES)
        tous_les_produits = set()
        for rule in result:
            tous_les_produits.add(rule["antecedent"])
            tous_les_produits.add(rule["consequent"])
        # clé_plate est dans la majorité des transactions — doit apparaître
        assert "clé_plate" in tous_les_produits


# ---------------------------------------------------------------------------
# Tests _apriori_rules (seulement si mlxtend est installé)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not HAS_MLXTEND, reason="mlxtend non installé")
class TestAprioriRules:

    def test_retourne_dataframe(self):
        """La fonction retourne un DataFrame pandas."""
        result = _apriori_rules(TRANSACTIONS_RICHES, min_support=0.1)
        assert isinstance(result, pd.DataFrame)

    def test_colonnes_attendues(self):
        """Le DataFrame contient les colonnes de règles d'association standard."""
        result = _apriori_rules(TRANSACTIONS_RICHES, min_support=0.1)
        if not result.empty:
            for col in ["support", "confidence", "lift", "antecedents", "consequents"]:
                assert col in result.columns

    def test_support_minimum_respecte(self):
        """Toutes les règles respectent le seuil min_support."""
        result = _apriori_rules(TRANSACTIONS_RICHES, min_support=0.3)
        if not result.empty:
            assert (result["support"] >= 0.3).all()

    def test_confidence_minimum_respecte(self):
        """Toutes les règles respectent le seuil min_confidence."""
        result = _apriori_rules(
            TRANSACTIONS_RICHES, min_support=0.1, min_confidence=0.5
        )
        if not result.empty:
            assert (result["confidence"] >= 0.5).all()

    def test_transactions_vides_retourne_dataframe_vide(self):
        """Un input vide retourne un DataFrame vide sans lever d'exception."""
        result = _apriori_rules([], min_support=0.1)
        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_support_trop_eleve_retourne_vide(self):
        """Un min_support=1.0 (impossible sauf transaction universelle) → DataFrame vide."""
        result = _apriori_rules(TRANSACTIONS_RICHES, min_support=1.0)
        assert result.empty

    def test_tri_par_lift_decroissant(self):
        """Les règles sont triées par lift décroissant."""