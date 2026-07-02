"""
Score de credit client (cf. 20-MACHINE-LEARNING.md section 20.3).
Score final 0-100, niveau de risque : 0-40 ELEVE, 41-70 MOYEN, 71-100 FAIBLE.
"""
from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd

from app.extensions import db
from app.ml.common import register_model, record_predictions, latest_predictions, MLflowRun, save_artifact, next_version, get_active_model, load_artifact
from app.models import (
    Customer,
    CustomerPayment,
    CustomerPaymentStatus,
    CustomerType,
    FsCustomerCreditFeatures,
    PaymentType,
    Sale,
    SaleStatus,
)
from app.models.feature_store import FeatureDataSource

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_val_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False

PREDICTION_TYPE = "CREDIT_SCORE"
MODEL_TYPE = "CREDIT_SCORING"

MIN_SAMPLES_FOR_ML = 20
TAUX_RETARD_SEUIL = 0.20

FEATURE_LABELS_FR = {
    "nb_achats_credit_total":           "Nombre total d'achats à crédit",
    "montant_moyen_achat":              "Montant moyen par achat (FCFA)",
    "delai_moyen_remboursement_jours":  "Délai moyen de remboursement (jours)",
    "taux_retard":                      "Taux de retard de paiement",
    "anciennete_client_mois":           "Ancienneté client (mois)",
    "frequence_achat_mensuelle":        "Fréquence d'achat mensuelle",
    "solde_du_actuel":                  "Solde dû actuellement (FCFA)",
    "is_technicien":                    "Est technicien",
}


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

    # Calcul de la médiane globale des délais réels (tous CustomerPayment PAID avec paid_date).
    # Utilisée comme valeur neutre pour les clients sans historique de paiement.
    # Justification : un client inconnu est traité comme un client "moyen" — ni bon ni mauvais payeur.
    try:
        all_paid = CustomerPayment.query.filter(
            CustomerPayment.status == CustomerPaymentStatus.PAID.value,
            CustomerPayment.paid_date.isnot(None),
        ).all()
        global_delays = [max(0, (p.paid_date - p.due_date).days) for p in all_paid if p.due_date]
        median_delay_global = round(float(np.median(global_delays)), 1) if global_delays else 30.0
    except Exception:
        median_delay_global = 30.0  # valeur neutre par défaut si DB indisponible

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

        # Calcul reel depuis l historique des echeances CustomerPayment.
        # Remplace l ancienne simulation deterministe par hash SHA-256 (supprimee).
        payments = CustomerPayment.query.filter_by(customer_id=customer.id).all()
        if payments:
            closed = [
                p for p in payments
                if p.status in (CustomerPaymentStatus.PAID.value, CustomerPaymentStatus.LATE.value)
            ]
            late = [p for p in payments if p.status == CustomerPaymentStatus.LATE.value]
            taux_retard = round(len(late) / len(closed), 4) if closed else 0.0

            paid_with_dates = [
                p for p in payments
                if p.status == CustomerPaymentStatus.PAID.value and p.paid_date
            ]
            if paid_with_dates:
                delays = [max(0, (p.paid_date - p.due_date).days) for p in paid_with_dates]
                delai_moyen = round(float(np.mean(delays)), 1)
            else:
                # Paiements enregistrés mais sans paid_date → délai inconnu.
                # On utilise la médiane globale (neutre) plutôt que 0 (meilleur payeur).
                delai_moyen = median_delay_global
            data_source_val = FeatureDataSource.REAL.value
        else:
            # Aucun historique d echeances CustomerPayment.
            # Proxy conservateur : part de l encours non rembourse (credit_balance / total achats).
            total_credit = sum(float(s.total) for s in credit_sales)
            credit_bal = float(customer.credit_balance)
            taux_retard = round(min(credit_bal / total_credit, 1.0), 4) if total_credit > 0 else 0.0
            # Correction bug : delai_moyen = 0.0 donnait la meilleure valeur possible
            # aux clients sans historique, gonflant artificiellement leur score.
            # On utilise la médiane globale des délais réels comme valeur neutre.
            delai_moyen = median_delay_global
            data_source_val = FeatureDataSource.SIMULATED.value

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
                "data_source": data_source_val,
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


def _score_ml(df: pd.DataFrame) -> tuple[np.ndarray, dict, str, object]:
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
    return scores, metrics, "RANDOM_FOREST+LOGISTIC_REGRESSION_CV", rf


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
        scores, metrics, algorithm, rf_model = _score_ml(df)
        _artifact_version = next_version(MODEL_TYPE)
        artifact_path = save_artifact(
            {"rf_model": rf_model}, MODEL_TYPE, _artifact_version
        )
    else:
        scores, metrics, algorithm = _score_rule_based(df)
        artifact_path = None
        _artifact_version = None

    n_real = int((df["data_source"] == FeatureDataSource.REAL.value).sum())
    metrics["n_data_source_real"] = float(n_real)
    metrics["n_data_source_simulated"] = float(len(df) - n_real)
    metrics["note"] = (
        "taux_retard et delai_moyen_remboursement_jours : REAL si historique "
        "CustomerPayment disponible (due_date/paid_date/status), sinon SIMULATED "
        "(proxy = credit_balance / total_achats_credit, delai_moyen = médiane_globale_réelle ou 30j). "
        "La simulation deterministe par hash SHA-256 a ete supprimee."
    )

    with MLflowRun(MODEL_TYPE) as run:
        run.log_metrics({k: v for k, v in metrics.items() if isinstance(v, (int, float))})
        model = register_model(
            model_type=MODEL_TYPE,
            algorithm=algorithm,
            metrics=metrics,
            artifact_path=artifact_path,
            mlflow_run_id=run.run_id,
            version=_artifact_version,
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



def explain_credit_score(customer_id: str) -> dict:
    """
    Explication SHAP du score crédit d'un client.

    Utilise TreeExplainer sur le RandomForestClassifier sauvegardé dans
    l'artefact du modèle actif. Retourne les contributions SHAP de chaque
    feature au score final, triées par impact absolu décroissant.

    Disponible uniquement si sklearn et shap sont installés et qu'un modèle
    ML (non rule-based) a déjà été entraîné.
    """
    if not HAS_SKLEARN or not HAS_SHAP:
        return {"available": False, "reason": "Bibliothèques sklearn/SHAP non disponibles"}

    # Charger les features du client
    df = _load_customer_features_from_feature_store()
    if df is None or df.empty:
        df = _load_customer_features_direct()
    if df.empty:
        return {"available": False, "reason": "Aucune donnée client disponible"}

    customer_row = df[df["customer_id"] == customer_id]
    if customer_row.empty:
        return {"available": False, "reason": "Client introuvable dans les données"}

    # Charger le modèle actif
    active_model = get_active_model(MODEL_TYPE)
    if not active_model or not active_model.artifact_path:
        return {
            "available": False,
            "reason": "Aucun artefact de modèle disponible — lancer un entraînement ML d'abord",
        }

    model_data = load_artifact(active_model.artifact_path)
    if model_data is None:
        return {"available": False, "reason": "Artefact introuvable sur le disque"}

    rf_model = model_data.get("rf_model") if isinstance(model_data, dict) else model_data
    if rf_model is None:
        return {"available": False, "reason": "Clé 'rf_model' introuvable dans l'artefact"}

    # Features utilisées à l'entraînement
    feature_cols = [c for c in FEATURE_COLUMNS if c in customer_row.columns]
    X = customer_row[feature_cols].fillna(0)

    # Calcul SHAP (TreeExplainer — pas d'appel réseau, 100 % local)
    explainer = shap.TreeExplainer(rf_model)
    shap_values = explainer.shap_values(X)

    # RandomForestClassifier retourne une liste [classe_0, classe_1]
    # On prend classe_1 (bon payeur = score élevé)
    if isinstance(shap_values, list) and len(shap_values) > 1:
        shap_vals = shap_values[1][0]
    else:
        shap_vals = (shap_values[0] if isinstance(shap_values, list) else shap_values)[0]

    contributions = {
        FEATURE_LABELS_FR.get(col, col): round(float(val), 4)
        for col, val in zip(feature_cols, shap_vals)
    }
    sorted_contribs = sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)

    explanations = []
    for label, shap_val in sorted_contribs[:5]:
        if abs(shap_val) < 0.005:
            continue
        direction = "réduit le risque" if shap_val > 0 else "augmente le risque"
        sign = "✓" if shap_val > 0 else "✗"
        explanations.append(f"{sign} {label} {direction} ({shap_val:+.3f})")

    if isinstance(explainer.expected_value, (list, np.ndarray)):
        base_val = float(explainer.expected_value[1])
    else:
        base_val = float(explainer.expected_value)

    return {
        "available":      True,
        "customer_id":    customer_id,
        "base_value":     round(base_val, 4),
        "contributions":  dict(sorted_contribs),
        "top_factors":    explanations,
        "interpretation": "Valeurs positives = réduisent le risque. Valeurs négatives = augmentent le risque.",
        "model_version":  active_model.version,
    }


def latest() -> list[dict]:
    return [
        {
            "customer_id": p.entity_id,
            "model_id": p.model_id,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            **p.payload_json,
        }
        for p in latest_predictions(PREDICTION_TYPE)
    ]
