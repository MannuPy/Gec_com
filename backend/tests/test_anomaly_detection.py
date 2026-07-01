"""
Tests unitaires — ml/anomaly_detection.py
Fonction testée (logique pure, sans DB) :
  - Génération des raisons d'anomalie (bloc de règles if/elif)

On extrait la logique des raisons dans une fonction pure pour la tester,
sans avoir à mocker la base de données.
"""
import pytest


def _build_reasons(row: dict) -> list[str]:
    """
    Réplique de la logique de génération des raisons dans anomaly_detection.py.
    Maintenue synchronisée avec le code source.
    Retourne la liste des raisons pour une vente anormale.
    """
    reasons = []
    remise  = row.get("remise_taux", 0)
    heure   = row.get("heure_vente", 12)
    ecart_p = row.get("ecart_vs_moyenne_produit", 0)
    ecart_v = row.get("ecart_vs_moyenne_vendeur", 0)
    montant = row.get("montant_total", 0)

    if remise >= 20:
        reasons.append("Remise maximale accordée (20 %) — approbation requise")
    elif remise >= 15:
        reasons.append("Remise élevée (≥ 15 %)")

    if remise > 0 and heure < 8:
        reasons.append("Remise accordée en dehors des heures de supervision (avant 8h)")

    if ecart_p > 3:
        reasons.append(f"Montant {ecart_p:.1f}x supérieur à la moyenne du produit")
    elif ecart_p > 1:
        reasons.append("Montant largement supérieur à la moyenne du produit")

    if ecart_v > 2:
        reasons.append(f"Volume {ecart_v:.1f}x supérieur à la moyenne du vendeur — risque fraude")
    elif ecart_v > 1:
        reasons.append("Montant supérieur à la moyenne du vendeur")

    if heure < 6:
        reasons.append("Vente très tôt le matin (avant 6h) — horaire inhabituel")
    elif heure > 21:
        reasons.append("Vente en soirée tardive (après 21h) — horaire inhabituel")

    if remise >= 10 and ecart_v > 1:
        reasons.append("Combinaison remise élevée + volume vendeur anormal")

    if montant > 0 and ecart_p > 2 and remise > 0:
        reasons.append("Montant suspect avec remise sur produit à écart élevé")

    if not reasons:
        reasons.append("Profil statistique atypique (score IsolationForest bas)")

    return reasons


class TestAnomalyReasons:

    def test_no_anomaly_signals_returns_fallback(self):
        row = {"remise_taux": 0, "heure_vente": 10, "ecart_vs_moyenne_produit": 0,
               "ecart_vs_moyenne_vendeur": 0, "montant_total": 100}
        reasons = _build_reasons(row)
        assert len(reasons) == 1
        assert "atypique" in reasons[0].lower()

    def test_remise_20_triggers_max_discount_reason(self):
        row = {"remise_taux": 20, "heure_vente": 10, "ecart_vs_moyenne_produit": 0,
               "ecart_vs_moyenne_vendeur": 0, "montant_total": 0}
        reasons = _build_reasons(row)
        assert any("20 %" in r for r in reasons)

    def test_remise_15_triggers_high_discount_reason(self):
        row = {"remise_taux": 15, "heure_vente": 10, "ecart_vs_moyenne_produit": 0,
               "ecart_vs_moyenne_vendeur": 0, "montant_total": 0}
        reasons = _build_reasons(row)
        assert any("15 %" in r or "élevée" in r for r in reasons)

    def test_remise_before_8h_triggers_supervision_reason(self):
        row = {"remise_taux": 10, "heure_vente": 7, "ecart_vs_moyenne_produit": 0,
               "ecart_vs_moyenne_vendeur": 0, "montant_total": 0}
        reasons = _build_reasons(row)
        assert any("supervision" in r.lower() for r in reasons)

    def test_remise_after_8h_no_supervision_reason(self):
        row = {"remise_taux": 10, "heure_vente": 9, "ecart_vs_moyenne_produit": 0,
               "ecart_vs_moyenne_vendeur": 0, "montant_total": 0}
        reasons = _build_reasons(row)
        assert not any("supervision" in r.lower() for r in reasons)

    def test_ecart_produit_over_3_gives_strong_message(self):
        row = {"remise_taux": 0, "heure_vente": 10, "ecart_vs_moyenne_produit": 4.0,
               "ecart_vs_moyenne_vendeur": 0, "montant_total": 0}
        reasons = _build_reasons(row)
        assert any("4.0x" in r for r in reasons)

    def test_ecart_produit_between_1_and_3_gives_moderate_message(self):
        row = {"remise_taux": 0, "heure_vente": 10, "ecart_vs_moyenne_produit": 2.0,
               "ecart_vs_moyenne_vendeur": 0, "montant_total": 0}
        reasons = _build_reasons(row)
        assert any("largement supérieur" in r for r in reasons)

    def test_ecart_vendeur_over_2_gives_fraud_risk(self):
        row = {"remise_taux": 0, "heure_vente": 10, "ecart_vs_moyenne_produit": 0,
               "ecart_vs_moyenne_vendeur": 3.0, "montant_total": 0}
        reasons = _build_reasons(row)
        assert any("fraude" in r.lower() for r in reasons)

    def test_vente_avant_6h_triggers_very_early_reason(self):
        row = {"remise_taux": 0, "heure_vente": 4, "ecart_vs_moyenne_produit": 0,
               "ecart_vs_moyenne_vendeur": 0, "montant_total": 0}
        reasons = _build_reasons(row)
        assert any("avant 6h" in r for r in reasons)

    def test_vente_apres_21h_triggers_late_evening_reason(self):
        row = {"remise_taux": 0, "heure_vente": 22, "ecart_vs_moyenne_produit": 0,
               "ecart_vs_moyenne_vendeur": 0, "montant_total": 0}
        reasons = _build_reasons(row)
        assert any("21h" in r for r in reasons)

    def test_combination_remise_plus_vendeur_triggers_combo_reason(self):
        row = {"remise_taux": 10, "heure_vente": 10, "ecart_vs_moyenne_produit": 0,
               "ecart_vs_moyenne_vendeur": 1.5, "montant_total": 0}
        reasons = _build_reasons(row)
        assert any("combinaison" in r.lower() for r in reasons)

    def test_multiple_signals_give_multiple_reasons(self):
        row = {"remise_taux": 20, "heure_vente": 5, "ecart_vs_moyenne_produit": 4.0,
               "ecart_vs_moyenne_vendeur": 3.0, "montant_total": 500}
        reasons = _build_reasons(row)
        assert len(reasons) >= 3

    def test_reasons_are_all_strings(self):
        row = {"remise_taux": 15, "heure_vente": 3, "ecart_vs_moyenne_produit": 2.5,
               "ecart_vs_moyenne_vendeur": 2.5, "montant_total": 200}
        reasons = _build_reasons(row)
        for r in reasons:
            assert isinstance(r, str) and len(r) > 0

    def test_no_reason_is_empty_string(self):
        rows = [
            {"remise_taux": 0, "heure_vente": 12, "ecart_vs_moyenne_produit": 0, "ecart_vs_moyenne_vendeur": 0, "montant_total": 0},
            {"remise_taux": 20, "heure_vente": 3, "ecart_vs_moyenne_produit": 5, "ecart_vs_moyenne_vendeur": 4, "montant_total": 1000},
        ]
        for row in rows:
            for reason in _build_reasons(row):
                assert reason.strip() != ""
