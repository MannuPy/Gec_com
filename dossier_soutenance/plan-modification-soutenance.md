# Plan de Modification — Soutenance Fin Juillet 2026
## GesCom-BF — Génie Logiciel, Option Analyse de Données

> **Dernière mise à jour :** 1er juillet 2026 — conformité code v2 post-corrections soutenance.

> **Date de référence :** 23 juin 2026  
> **Deadline soutenance :** ~25 juillet 2026 (5 semaines)  
> **Objectif :** Projet de qualité démontrant un vrai travail analytique au jury

---

## PRÉAMBULE — CE QUE TON PROJET FAIT DÉJÀ (à valoriser)

Avant de lister les modifications, voici les fonctionnalités **déjà opérationnelles** que beaucoup d'étudiants n'ont pas et que tu dois présenter comme des réalisations dans ton rapport.

| Fonctionnalité | Fichier | Ce que ça démontre |
|---|---|---|
| AuditLog complet (`AuditLog.record()`) | `app/models/audit.py` | Traçabilité, sécurité |
| Révocation JWT (`TokenBlocklist`) — table SQL, pas Redis | `app/models/auth.py` | Gestion sécurisée des sessions |
| Erreurs standardisées (`ApiError`) | `app/utils/errors.py` | Qualité API, maintenabilité |
| Cross-validation RF vs LogReg | `app/ml/credit_scoring.py` | Comparaison d'algorithmes scientifique |
| Isolation Forest + Z-Score fallback | `app/ml/anomaly_detection.py` | Détection d'anomalies avec fallback |
| Classification ABC/XYZ déterministe | `app/ml/abc_xyz.py` | Analyse de portefeuille produits |
| **Analyse de cohortes complète** | `analytics/routes.py` → `/cohorts` | Rétention clients par mois d'acquisition |
| **Customer Lifetime Value (CLV) + `data_confidence`** | `analytics/routes.py` → `/clv` | Valeur vie client avec indice de confiance |
| Segmentation RFM + K-Means (k optimal Silhouette/Elbow) | `app/ml/rfm_segmentation.py` | Segmentation clients multi-critères + validation méthodologique |
| **Churn Probability (RFM-based)** | `rfm_segmentation.py` → `/churn-risk` | Probabilité de désengagement par client |
| **SHAP Explicabilité Scoring Crédit** | `credit_scoring.py` → `/credit-scores/<id>/explain` | XAI — IA Explicable, TreeExplainer |
| **Market Basket Analysis (Apriori)** | `app/ml/market_basket.py` → `/basket` | Règles d'association, vente croisée |
| **Price Elasticity Analysis** | `app/services/price_elasticity_service.py` → `/price-elasticity` | Économétrie, régression log-log |
| **Prophet + features africaines actifs** | `app/ml/demand_forecast.py` | Prévisions avec calendrier burkinabè |
| **African Context endpoint** | `analytics/routes.py` → `/african-context` | Feature engineering domaine-spécifique |
| Architecture multi-tenant | `app/utils/tenant.py` | Architecture SaaS réelle |
| Registre MLflow des modèles | `ml/common.py` | Traçabilité des entraînements ML |
| Flask-Limiter 3.8.0 (`memory://`) | `app/extensions.py` | Rate limiting sans Redis |
| **155 tests** (127 ML + 17 intégration + 15 sécurité + 12 RBAC) | `test_integration_api.py`, `test_security_rbac.py`, `test_rbac_roles.py` | Qualité, couverture, CI/CD |
| CI/CD GitHub Actions + `sshpass` | `.github/workflows/` | Déploiement automatique |
| **10 migrations Alembic** | `backend/migrations/versions/` | Gestion évolutive du schéma |
| Sentry SDK optionnel | `app/__init__.py` | Monitoring production |
| **RF-05 : `must_change_password`** | `require_permission()` → 403 `PASSWORD_CHANGE_REQUIRED` | Sécurité — changement de MDP forcé |
| **RF-16/RG-23 : `approved_by_id` obligatoire** | `sale_service.create_sale()` → 422 | Validation remises côté serveur |

---

## STRUCTURE DU PLAN

Le plan est organisé en **5 phases** sur 5 semaines :

```
Semaine 1 (23-29 juin)  → Phase 0 : Corrections critiques + Nettoyage
Semaine 2 (30 juin-6 juil) → Phase 1 : Enrichissement Analytics (hautes valeur/faible risque)
Semaine 3 (7-13 juil)   → Phase 2 : Nouveaux modules Analytics
Semaine 4 (14-20 juil)  → Phase 3 : Rapport de soutenance (rédaction)
Semaine 5 (21-27 juil)  → Phase 4 : Finalisation, tests, préparation orale
```

---

## PHASE 0 — CORRECTIONS CRITIQUES ✅ TOUTES RÉALISÉES
### Semaine 1 | Toutes complétées

---

### 0.1 — ✅ Supprimer le fallback SHA-256 dans le scoring crédit — RÉALISÉ
**Priorité : CRITIQUE** | **Statut : Complété**

**Problème :** Le code actuel génère des scores de crédit à partir d'un hash SHA-256 du `customer_id` quand les données sont insuffisantes. Ce n'est pas de l'IA — c'est du hasard déterministe. Si un jury découvre ça, c'est rédhibitoire.

**Fichier à modifier :** `backend/app/ml/credit_scoring.py`

**Ce qu'il faut faire :**
Trouver la fonction `_deterministic_repayment_stats()` et la remplacer par un retour explicite "données insuffisantes" au lieu d'une simulation.

```python
# AVANT (à supprimer) :
def _deterministic_repayment_stats(customer_id: str) -> tuple[float, float]:
    digest = hashlib.sha256(customer_id.encode("utf-8")).digest()
    seed = int.from_bytes(digest[:4], "big")
    rng = np.random.RandomState(seed)
    taux_retard = float(rng.beta(2, 5))
    ...

# APRÈS (remplacer par) :
def _insufficient_data_result(customer_id: str) -> dict:
    """Retourne un résultat explicite quand les données sont insuffisantes."""
    return {
        "customer_id": customer_id,
        "score": None,
        "risk_level": "INDETERMINATE",
        "confidence": 0.0,
        "reason": "Historique d'achats insuffisant pour calculer un score fiable",
        "minimum_required_purchases": 5,
    }
```

**Trouver aussi :** Toute ligne qui importe ou appelle `hashlib` dans `credit_scoring.py` et supprimer ces appels.

**Information capitale :** Vérifier combien de clients déclenchent ce fallback dans ta base de test — si c'est beaucoup, tu dois l'expliquer dans le rapport.

---

### 0.2 — ✅ Prophet activé dans la prévision de demande — RÉALISÉ
**Priorité : HAUTE** | **Statut : Complété**

**Contexte :** `prophet` est **déjà dans `requirements.txt`** (version 1.1.5) et **déjà importé** dans `demand_forecast.py` avec le flag `HAS_PROPHET`. Il suffit d'écrire la fonction qui l'utilise.

**Fichier à modifier :** `backend/app/ml/demand_forecast.py`

**Ce qu'il faut faire :** Ajouter la fonction `_forecast_prophet()` et l'intégrer dans `_forecast_series()`.

```python
def _forecast_prophet(series: pd.Series) -> tuple[float, float, str]:
    """
    Prévision Prophet avec regresseurs saisonniers africains.
    Nécessite au moins 30 jours d'historique.
    """
    from prophet import Prophet

    # Format attendu par Prophet : colonnes 'ds' et 'y'
    df_prophet = pd.DataFrame({
        "ds": series.index,
        "y": series.values.astype(float),
    })

    # Créer le modèle avec saisonnalité hebdomadaire (commerce de détail africain)
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        seasonality_mode="multiplicative",  # Adapté aux pics forts (Tabaski, etc.)
    )

    # Ajouter les événements burkinabè comme regresseurs
    burkina_events = pd.DataFrame([
        # Format : nom, ds (date), lower_window, upper_window
        {"holiday": "tabaski",       "ds": "2025-06-07", "lower_window": -7, "upper_window": 3},
        {"holiday": "tabaski",       "ds": "2026-05-27", "lower_window": -7, "upper_window": 3},
        {"holiday": "ramadan_start", "ds": "2025-03-01", "lower_window": -3, "upper_window": 30},
        {"holiday": "ramadan_start", "ds": "2026-02-18", "lower_window": -3, "upper_window": 30},
        {"holiday": "independence",  "ds": "2025-08-05", "lower_window": -1, "upper_window": 1},
        {"holiday": "independence",  "ds": "2026-08-05", "lower_window": -1, "upper_window": 1},
        {"holiday": "noel",          "ds": "2025-12-25", "lower_window": -5, "upper_window": 2},
        {"holiday": "noel",          "ds": "2026-12-25", "lower_window": -5, "upper_window": 2},
    ])

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        seasonality_mode="multiplicative",
        holidays=burkina_events,
    )

    model.fit(df_prophet)

    # Générer les prévisions futures (30 jours)
    future = model.make_future_dataframe(periods=30, freq="D")
    forecast = model.predict(future)

    # Extraire seulement les 30 jours futurs
    future_forecast = forecast.tail(30)
    preds = future_forecast["yhat"].clip(lower=0).values

    forecast_7d = float(preds[:7].sum())
    forecast_30d = float(preds.sum())

    return forecast_7d, forecast_30d, "PROPHET_BURKINA_HOLIDAYS"


def _forecast_series(series: pd.Series) -> tuple[float, float, str]:
    """Cascade : Prophet → LinearRegression → Seasonal Naive"""
    if HAS_PROPHET and len(series) >= 30:
        try:
            return _forecast_prophet(series)
        except Exception:
            pass  # Bascule sur LinearRegression si Prophet échoue

    if HAS_SKLEARN and len(series) >= MIN_HISTORY_DAYS:
        return _forecast_sklearn(series)

    return _forecast_seasonal_naive(series)
```

**Information capitale :**
- `MIN_HISTORY_DAYS = 14` dans le fichier actuel — Prophet nécessite min 30 jours. OK à laisser car la cascade gère ça.
- Prophet peut être lent sur PythonAnywhere (CPU limité). Tester sur un petit dataset d'abord.
- Si trop lent : lancer via le cron PythonAnywhere la nuit (voir Phase 0.4).

---

### 0.3 — ✅ Flask-Limiter (Rate Limiting) — RÉALISÉ
**Priorité : MOYENNE** | **Statut : Complété**

**Implémenté :** Flask-Limiter 3.8.0 avec `storage_uri="memory://"` (sans Redis, adapté PythonAnywhere). Installé dans `requirements.txt`.

**Package installé :** `Flask-Limiter==3.8.0`

**Fichiers à modifier :**
1. `backend/app/extensions.py` — ajouter l'initialisation du limiter
2. `backend/app/blueprints/auth/routes.py` — ajouter les décorateurs
3. `backend/config/production.py` — configurer les limites

```python
# extensions.py — ajouter :
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def _get_real_ip():
    """Lit l'IP réelle même derrière un proxy (Cloudflare, Nginx)."""
    from flask import request
    return (
        request.headers.get("CF-Connecting-IP")
        or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.remote_addr
    )

limiter = Limiter(key_func=_get_real_ip, default_limits=[])

# Dans create_app() :
limiter.init_app(app)
```

```python
# auth/routes.py — ajouter sur les routes sensibles :
from app.extensions import limiter

@auth_bp.post("/login")
@limiter.limit("10 per minute; 50 per hour")
def login():
    ...

@auth_bp.post("/register")
@limiter.limit("3 per hour")
def register():
    ...
```

---

### 0.4 — ✅ Script Cron PythonAnywhere pour l'entraînement ML — RÉALISÉ
**Priorité : MOYENNE** | **Statut : Complété**

**Implémenté :** `scripts/cron_train_all.py` à la racine du dépôt. Planifié via PythonAnywhere Tasks (quotidien 02:00). Celery et Redis ont été **supprimés** — remplacés par threads Python natifs (à la demande) et ce script cron (planifié).

**Commande cron correcte :**
```
/home/<username>/.virtualenvs/gescom-bf/bin/python /home/<username>/gescom-bf/scripts/cron_train_all.py
```

**Fichier créé :** `scripts/cron_train_all.py` (racine du dépôt, pas dans `backend/`)

```python
#!/usr/bin/env python3
"""
Script d'entraînement nocturne des modèles ML.
À configurer comme tâche planifiée PythonAnywhere :
  Schedule: Daily at 02:00
  Command: /home/<username>/.virtualenvs/<venv>/bin/python /home/<username>/gescom/backend/scripts/cron_train_all.py
"""
import sys
import os
import logging

# Ajouter le répertoire backend au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("/tmp/gescom_ml_training.log"),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger("cron_train_all")

from app import create_app

app = create_app()

def run_all():
    with app.app_context():
        results = {}

        # 1. Prévision de demande
        try:
            from app.ml import demand_forecast
            results["demand_forecast"] = demand_forecast.train(months=6)
            logger.info("demand_forecast: %s", results["demand_forecast"])
        except Exception as e:
            logger.error("demand_forecast FAILED: %s", e)
            results["demand_forecast"] = {"status": "error", "error": str(e)}

        # 2. Scoring crédit
        try:
            from app.ml import credit_scoring
            results["credit_scoring"] = credit_scoring.train()
            logger.info("credit_scoring: %s", results["credit_scoring"])
        except Exception as e:
            logger.error("credit_scoring FAILED: %s", e)
            results["credit_scoring"] = {"status": "error", "error": str(e)}

        # 3. Détection d'anomalies
        try:
            from app.ml import anomaly_detection
            results["anomaly_detection"] = anomaly_detection.train(days=90)
            logger.info("anomaly_detection: %s", results["anomaly_detection"])
        except Exception as e:
            logger.error("anomaly_detection FAILED: %s", e)

        # 4. ABC/XYZ
        try:
            from app.ml import abc_xyz
            results["abc_xyz"] = abc_xyz.train(months=6)
            logger.info("abc_xyz: %s", results["abc_xyz"])
        except Exception as e:
            logger.error("abc_xyz FAILED: %s", e)

        # 5. RFM Segmentation (avec évaluation du k optimal — voir Phase 1.1)
        try:
            from app.ml import rfm_segmentation
            results["rfm_segmentation"] = rfm_segmentation.train(months=12)
            logger.info("rfm_segmentation: %s", results["rfm_segmentation"])
        except Exception as e:
            logger.error("rfm_segmentation FAILED: %s", e)

        # 6. Market Basket Analysis (après Phase 2.1)
        try:
            from app.ml import market_basket
            results["market_basket"] = market_basket.train(months=6)
            logger.info("market_basket: %s", results["market_basket"])
        except Exception as e:
            logger.error("market_basket: non disponible ou erreur - %s", e)

        logger.info("=== ENTRAÎNEMENT TERMINÉ === Résultats: %s", results)
        return results

if __name__ == "__main__":
    run_all()
```

**Sur PythonAnywhere :**
- Aller dans "Tasks" → "Add a new scheduled task"
- Heure : `02:00`
- Commande : `/home/<username>/.virtualenvs/<venv>/bin/python /home/<username>/gescom/backend/scripts/cron_train_all.py`

---

### 0.5 — ✅ Threading pour l'endpoint d'entraînement manuel — RÉALISÉ
**Priorité : MOYENNE** | **Statut : Complété**

**Implémenté :** `POST /analytics/ml/train/<type>` lance maintenant un `threading.Thread(daemon=True)` et retourne HTTP 202 immédiatement.

**Fichier à modifier :** `backend/app/blueprints/analytics/routes.py`

```python
# Modifier la fin de trigger_training() et trigger_training_body() :
import threading

# Remplacer :
result = task.run()
return jsonify({"status": "completed", "model_type": model_type_normalized, "result": result})

# Par :
thread = threading.Thread(target=task.run, daemon=True, name=f"ml_{model_type_normalized}")
thread.start()
return jsonify({
    "status": "started",
    "model_type": model_type_normalized,
    "message": "Entraînement lancé en arrière-plan. Résultats disponibles dans /ml/models."
}), 202
```

---

## PHASE 1 — ENRICHISSEMENT ANALYTICS ✅ TOUTES RÉALISÉES
### Semaine 2 | Toutes complétées

---

### 1.1 — ✅ Évaluation rigoureuse du K optimal (Silhouette + Elbow) — RÉALISÉ
**Priorité : HAUTE** | **Statut : Complété**

**Implémenté dans :** `backend/app/ml/rfm_segmentation.py` — fonction `evaluate_optimal_k()`. Endpoint `/analytics/rfm-segments/evaluate-k` expose les scores pour k=2 à k=8.

**Contexte original :** k=4 était codé en dur sans justification méthodologique.

**Ce qu'il faut ajouter :**
```python
# Nouvelle fonction à ajouter AVANT la fonction train() :

def evaluate_optimal_k(X_scaled: np.ndarray, k_range: range = range(2, 9)) -> dict:
    """
    Évalue le nombre optimal de clusters via :
    - Score de silhouette (qualité intra-cluster vs inter-cluster)
    - Index de Davies-Bouldin (compacité des clusters, plus bas = mieux)
    - Inertie (méthode du coude)
    """
    from sklearn.metrics import silhouette_score, davies_bouldin_score

    evaluation = []
    for k in k_range:
        if len(X_scaled) < k * 3:  # Besoin d'au moins 3 points par cluster
            break
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)

        sil = float(silhouette_score(X_scaled, labels))
        db = float(davies_bouldin_score(X_scaled, labels))
        inertia = float(km.inertia_)

        evaluation.append({
            "k": k,
            "silhouette_score": round(sil, 4),
            "davies_bouldin_index": round(db, 4),
            "inertia": round(inertia, 2),
        })

    if not evaluation:
        return {"optimal_k": 4, "evaluation": [], "method": "DEFAULT"}

    # Sélection par score de silhouette maximal
    best = max(evaluation, key=lambda r: r["silhouette_score"])

    interp = "Excellente séparation" if best["silhouette_score"] >= 0.71 else \
             "Bonne séparation" if best["silhouette_score"] >= 0.51 else \
             "Séparation faible — chevauchement partiel" if best["silhouette_score"] >= 0.26 else \
             "Aucune structure naturelle détectée"

    return {
        "optimal_k": best["k"],
        "optimal_silhouette": best["silhouette_score"],
        "optimal_davies_bouldin": best["davies_bouldin_index"],
        "evaluation": evaluation,
        "interpretation": interp,
        "method": "MAX_SILHOUETTE",
    }
```

**Modifier la fonction `train()` :**
```python
def train(months: int = 12, n_clusters: int = None) -> dict:
    # ... code existant pour charger df ...

    # Étape 1 : Préparer et scaler les features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[["recency", "frequency", "monetary"]])

    # Étape 2 : Évaluer le k optimal (si assez de données)
    k_eval = {}
    if len(df) >= 20:
        k_eval = evaluate_optimal_k(X_scaled)
        if n_clusters is None:
            n_clusters = k_eval.get("optimal_k", 4)
    else:
        n_clusters = n_clusters or 4

    # Étape 3 : Entraîner le K-Means avec le k optimal
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)

    # ... reste du code existant ...

    # Ajouter k_eval dans les métriques stockées :
    metrics = {
        "n_clients": len(df),
        "n_clusters": n_clusters,
        "k_evaluation": k_eval,
        # ... autres métriques existantes
    }
```

**Endpoint à ajouter dans `analytics/routes.py` :**
```python
@analytics_bp.get("/rfm-segments/evaluate-k")
@require_permission("analytics:read")
def rfm_k_evaluation():
    """Retourne l'évaluation du nombre optimal de clusters (Silhouette + Elbow)."""
    from app.ml.rfm_segmentation import evaluate_optimal_k
    from sklearn.preprocessing import StandardScaler
    from app.ml import rfm_segmentation
    import numpy as np

    df = rfm_segmentation._load_rfm_from_feature_store() or \
         rfm_segmentation._load_rfm_dataframe_direct()
    if df.empty:
        return jsonify({"error": "Données insuffisantes"}), 400

    scaler = StandardScaler()
    X = scaler.fit_transform(df[["recency", "frequency", "monetary"]])
    result = evaluate_optimal_k(X)
    return jsonify(result)
```

---

### 1.2 — ✅ SHAP : Explicabilité du Scoring Crédit — RÉALISÉ
**Priorité : HAUTE** | **Statut : Complété**

**Implémenté dans :** `backend/app/ml/credit_scoring.py` — `explain_credit_score()` avec `shap.TreeExplainer`. Endpoint `/analytics/credit-scores/<id>/explain`.

**Package installé :** `shap==0.45.1`

**Fichier modifié :** `backend/app/ml/credit_scoring.py`

**Information capitale :** SHAP pour RandomForest (`TreeExplainer`) ne nécessite pas de recalcul du modèle — il s'applique sur le modèle déjà entraîné et sauvegardé dans `artifact_path`. Mais il faut que l'artefact sauvegarde bien l'objet `rf_model`.

**Vérifier d'abord** dans `credit_scoring.py` comment l'artefact est sauvegardé (chercher `joblib.dump` ou `register_model(artifact_path=...)`). L'objet RF doit être accessible.

```python
# Ajouter en haut du fichier :
try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False

# Labels des features en français (adapter selon les vraies feature columns)
FEATURE_LABELS_FR = {
    "nb_achats_credit_total":           "Nombre total d'achats à crédit",
    "montant_moyen_achat":              "Montant moyen par achat (FCFA)",
    "delai_moyen_remboursement_jours":  "Délai moyen de remboursement (jours)",
    "taux_retard":                      "Taux de retard de paiement",
    "anciennete_client_mois":           "Ancienneté client (mois)",
    "frequence_achat_mensuelle":        "Fréquence d'achat mensuelle",
    "solde_du_actuel":                  "Solde dû actuellement (FCFA)",
}


def explain_credit_score(customer_id: str) -> dict:
    """
    Explication SHAP du score crédit d'un client.
    Retourne les contributions de chaque feature au score final.
    """
    if not HAS_SKLEARN or not HAS_SHAP:
        return {"available": False, "reason": "Bibliothèques SHAP non disponibles"}

    # Charger les features du client depuis la feature store
    df = _load_customer_features_from_feature_store()
    if df is None or df.empty:
        df_raw = _load_customer_features_direct()
        if not df_raw:
            return {"available": False, "reason": "Aucune donnée disponible"}
        df = pd.DataFrame(df_raw)

    customer_row = df[df["customer_id"] == customer_id]
    if customer_row.empty:
        return {"available": False, "reason": "Client introuvable dans la feature store"}

    # Charger le modèle actif
    active_model = MLModel.query.filter_by(
        model_type=MODEL_TYPE, is_active=True
    ).first()
    if not active_model or not active_model.artifact_path:
        return {"available": False, "reason": "Aucun modèle entraîné disponible"}

    try:
        import joblib
        model_data = joblib.load(active_model.artifact_path)
    except Exception as e:
        return {"available": False, "reason": f"Impossible de charger l'artefact: {e}"}

    rf_model = model_data.get("rf_model") or model_data.get("model")
    if rf_model is None:
        return {"available": False, "reason": "Clé 'rf_model' introuvable dans l'artefact"}

    # Vérifier que les colonnes features correspondent
    feature_cols = [c for c in FEATURE_LABELS_FR.keys() if c in customer_row.columns]
    if not feature_cols:
        feature_cols = [c for c in customer_row.columns if c != "customer_id"]

    X = customer_row[feature_cols].fillna(0)

    # Calculer les valeurs SHAP
    explainer = shap.TreeExplainer(rf_model)
    shap_values = explainer.shap_values(X)

    # Pour RandomForestClassifier, shap_values est une liste [classe_0, classe_1]
    # On prend les valeurs pour la classe 1 (bon payeur = score élevé)
    if isinstance(shap_values, list):
        shap_vals_class1 = shap_values[1][0]
    else:
        shap_vals_class1 = shap_values[0]

    contributions = {}
    for col, val in zip(feature_cols, shap_vals_class1):
        label = FEATURE_LABELS_FR.get(col, col)
        contributions[label] = round(float(val), 4)

    # Trier par impact absolu décroissant
    sorted_contribs = sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)

    # Générer des phrases explicatives en français
    explanations = []
    for label, shap_val in sorted_contribs[:5]:
        if abs(shap_val) < 0.005:
            continue
        if shap_val > 0:
            explanations.append(f"✓ {label} réduit le risque ({shap_val:+.3f})")
        else:
            explanations.append(f"✗ {label} augmente le risque ({shap_val:+.3f})")

    base_val = float(explainer.expected_value[1]) if isinstance(explainer.expected_value, list) \
               else float(explainer.expected_value)

    return {
        "available": True,
        "customer_id": customer_id,
        "base_value": round(base_val, 4),
        "contributions": dict(sorted_contribs),
        "top_factors": explanations,
        "interpretation": "Valeurs positives = réduisent le risque. Valeurs négatives = augmentent le risque.",
        "model_version": active_model.version,
    }
```

**Endpoint à ajouter dans `analytics/routes.py` :**
```python
@analytics_bp.get("/credit-scores/<customer_id>/explain")
@require_permission("analytics:read")
def explain_credit_score_view(customer_id: str):
    """Explication SHAP des facteurs influençant le score crédit d'un client."""
    from app.ml.credit_scoring import explain_credit_score
    result = explain_credit_score(customer_id)
    if not result.get("available"):
        return jsonify(result), 422
    return jsonify(result)
```

**Information capitale :** Vérifier dans `credit_scoring.py` la ligne qui sauvegarde l'artefact. Elle doit sauvegarder un dict avec la clé `"rf_model"` ou `"model"`. Si ce n'est pas le cas, modifier l'appel `register_model(artifact_path=...)` pour qu'il sauvegarde `{"rf_model": rf, "logreg": logreg, "scaler": scaler}`.

---

### 1.3 — ✅ Churn Probability basée sur RFM — RÉALISÉ
**Priorité : MOYENNE** | **Statut : Complété**

**Implémenté dans :** `backend/app/ml/rfm_segmentation.py` — `compute_churn_probability()`. Endpoint `/analytics/churn-risk`.

```python
def compute_churn_probability(df_rfm: pd.DataFrame,
                               churn_threshold_days: int = 90) -> pd.DataFrame:
    """
    Probabilité de churn par décroissance exponentielle calibrée.
    P(churn) = 1 - exp(-λ × recency) avec λ calibré sur la médiane
    """
    if df_rfm.empty:
        return df_rfm

    median_recency = df_rfm["recency"].median()
    lambda_param = np.log(2) / max(median_recency, 1)

    df_rfm = df_rfm.copy()
    df_rfm["churn_probability"] = (
        1 - np.exp(-lambda_param * df_rfm["recency"])
    ).clip(0, 1).round(4)

    # Ajustement par la fréquence
    freq_weight = (df_rfm["frequency"] / df_rfm["frequency"].max()).fillna(0)
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
```

**Intégrer dans `train()` :** Après le calcul des segments, appeler `compute_churn_probability(df)` et stocker `churn_probability` et `churn_risk` dans le `payload` de chaque prédiction.

**Endpoint à ajouter dans `analytics/routes.py` :**
```python
@analytics_bp.get("/churn-risk")
@require_permission("analytics:read")
def churn_risk_view():
    """Probabilité de churn par client basée sur le modèle RFM."""
    from app.ml import rfm_segmentation
    min_prob = float(request.args.get("min_probability", 0.6))
    results = rfm_segmentation.latest()
    at_risk = [
        r for r in results
        if r.get("churn_probability", 0) >= min_prob
    ]
    at_risk.sort(key=lambda r: r.get("churn_probability", 0), reverse=True)
    return jsonify({"items": at_risk, "count": len(at_risk), "min_probability": min_prob})
```

---

### 1.4 — Anomaly Detection : Enrichir les raisons détectées
**Priorité : BASSE** | **Durée : 2h** | **Risque : Zéro**

**Fichier à modifier :** `backend/app/ml/anomaly_detection.py`

Le code actuel génère déjà des raisons ("Remise élevée", "Vente hors horaires"). Ajouter 2 raisons supplémentaires pour plus de richesse analytique.

```python
# Dans la boucle d'analyse des anomalies, ajouter après les raisons existantes :

# Détecter les patterns de fraude spécifiques au commerce burkinabè
if row.get("remise_taux", 0) > 0 and row.get("heure_vente", 12) < 8:
    reasons.append("Remise accordée en dehors des heures de supervision")

if row.get("ecart_vs_moyenne_vendeur", 0) > 2:
    reasons.append(f"Volume {row['ecart_vs_moyenne_vendeur']:.1f}x supérieur à la moyenne du vendeur")
```

---

## PHASE 2 — NOUVEAUX MODULES ANALYTICS ✅ TOUS RÉALISÉS
### Semaine 3 | Tous complétés

---

### 2.1 — ✅ Market Basket Analysis (Analyse du Panier d'Achat) — RÉALISÉ
**Priorité : HAUTE** | **Statut : Complété**

**Implémenté :** `backend/app/ml/market_basket.py` (Apriori via mlxtend, fallback co-occurrence). Endpoints `GET /analytics/basket`, `POST /analytics/basket/train`.

**Package installé :** `mlxtend==0.23.1`

Le code complet de ce module se trouve dans le document `conflits-et-innovations-analytics.md`.

**Résumé de ce que le module fait :**
- Charge les transactions (ventes validées) comme listes de produits
- Applique l'algorithme Apriori pour trouver les associations fréquentes
- Calcule support, confiance, lift pour chaque règle
- Fallback co-occurrence simple si mlxtend indisponible
- Stocke les résultats dans la table `predictions`
- Filtre par site (`branch_id`), lift minimum, et nom de produit

**Enregistrer dans `ml_tasks.py` :**
```python
@celery_app.task(name="app.tasks.ml_tasks.compute_market_basket_task")
def compute_market_basket_task(months: int = 6) -> dict:
    from app.ml import market_basket
    result = market_basket.train(months=months)
    logger.info("compute_market_basket_task: %s", result)
    return result

# Ajouter dans TRAIN_FUNCTIONS :
TRAIN_FUNCTIONS = {
    ...
    "MARKET_BASKET": compute_market_basket_task,
}
```

**Endpoints à ajouter dans `analytics/routes.py` :**
```python
@analytics_bp.get("/basket")
@require_permission("analytics:read")
def market_basket_view():
    """Règles d'association produits — recommandations de vente croisée."""
    from app.ml import market_basket
    branch_id = request.args.get("branch_id")
    min_lift = float(request.args.get("min_lift", 1.2))
    product = request.args.get("product")
    results = market_basket.latest(branch_id=branch_id, min_lift=min_lift,
                                   product_name=product)
    return jsonify({"items": results, "count": len(results)})


@analytics_bp.post("/basket/train")
@require_permission("ml:train")
def train_market_basket():
    """Lance l'entraînement du modèle Market Basket en arrière-plan."""
    from app.tasks.ml_tasks import compute_market_basket_task
    data = request.get_json(silent=True) or {}
    threading.Thread(
        target=compute_market_basket_task.run,
        kwargs={"months": data.get("months", 6)},
        daemon=True
    ).start()
    return jsonify({"message": "Entraînement Market Basket lancé"}), 202
```

---

### 2.2 — ✅ Analyse de l'Élasticité des Remises (Price Elasticity) — RÉALISÉ
**Priorité : MOYENNE** | **Statut : Complété**

**Implémenté :** `backend/app/services/price_elasticity_service.py` (régression log-log, pandas, règles déterministes). Endpoint `GET /analytics/price-elasticity`.

Le code complet se trouve dans `conflits-et-innovations-analytics.md`.

**Ce que le service calcule :**
- Pour chaque produit avec assez de données (≥20 ventes) :
  - Élasticité via régression log-log : `ln(quantité) = α + β × ln(1 - taux_remise)`
  - β = élasticité (< -1 : remise rentable, > -1 : remise non rentable)
  - R² de la régression pour évaluer la fiabilité
  - Recommandation automatique en français

**Endpoint :**
```python
@analytics_bp.get("/price-elasticity")
@require_permission("analytics:read")
def price_elasticity_view():
    """Analyse de l'élasticité des remises par produit."""
    from app.services.price_elasticity_service import compute_elasticity
    branch_id = request.args.get("branch_id")
    months = int(request.args.get("months", 6))
    results = compute_elasticity(months=months, branch_id=branch_id)
    return jsonify({"items": results, "count": len(results)})
```

---

### 2.3 — ✅ Features Contextuelles Africaines + Endpoint African Context — RÉALISÉ
**Priorité : HAUTE** | **Statut : Complété**

**Implémenté :** Features africaines intégrées dans `demand_forecast.py` (`_add_african_context_features()`). Endpoint `GET /analytics/african-context` expose le contexte calendaire actif (Tabaski, saison des pluies, rentrée scolaire, semaine de paie).

**Enrichissement supplémentaire :** Ajouter une fonction qui calcule et expose quelles "périodes africaines" sont actives aujourd'hui.

**Fichier à modifier :** `backend/app/blueprints/analytics/routes.py`

```python
@analytics_bp.get("/african-context")
@require_permission("analytics:read")
def african_context_view():
    """
    Retourne le contexte calendaire africain actuel (Burkina Faso).
    Utilisé par le frontend pour afficher des alertes de stock contextuelles.
    """
    from datetime import date
    today = date.today()
    month = today.month
    day = today.day

    contexts = []

    if month == 6 and day >= 1 or (month == 7 and day <= 10):
        contexts.append({
            "event": "TABASKI_SEASON",
            "label": "Période Tabaski",
            "impact": "Forte demande alimentaire, habillement, cadeaux",
            "stock_recommendation": "Augmenter les stocks alimentaires et textiles de 40-60%",
            "active": True,
        })

    if month in [6, 7, 8, 9]:
        contexts.append({
            "event": "SAISON_PLUIES",
            "label": "Saison des pluies",
            "impact": "Accès difficile dans certaines zones, stocks préventifs nécessaires",
            "stock_recommendation": "Constituer des réserves pour 45-60 jours",
            "active": True,
        })

    if month == 9 and day <= 20:
        contexts.append({
            "event": "RENTREE_SCOLAIRE",
            "label": "Rentrée scolaire",
            "impact": "Forte demande en fournitures, cartables, uniformes",
            "stock_recommendation": "Augmenter les stocks en articles scolaires",
            "active": True,
        })

    if day >= 25:
        contexts.append({
            "event": "SEMAINE_PAIE",
            "label": "Semaine de paie",
            "impact": "Pouvoir d'achat accru — pic de ventes habituellement observé",
            "stock_recommendation": "Assurer la disponibilité des articles à forte rotation",
            "active": True,
        })

    return jsonify({
        "date": today.isoformat(),
        "active_contexts": contexts,
        "count": len(contexts),
    })
```

---

## PHASE 3 — RAPPORT DE SOUTENANCE
### Semaine 4 | Plan complet dans `plan-rapport-soutenance.md`

Cette semaine est **entièrement dédiée à l'écriture du rapport**. Ne pas coder.

### Priorité de rédaction par chapitre

| Chapitre | Contenu clé à mettre en avant | Urgent |
|---|---|---|
| Ch. 2 — Contexte | Problèmes du commerce burkinabè, justification SaaS, limites des tableurs Excel | OUI |
| Ch. 3 — Conception | Diagramme de classes ML, use cases, architecture multi-tenant | OUI |
| Ch. 5 — Méthodologie Analytique | C'est LE chapitre de ta spécialité — voir ci-dessous | CRITIQUE |
| Ch. 6 — Résultats | Screenshots des dashboards, métriques, graphiques | OUI |
| Ch. 7 — Discussion | Limites honnêtes, perspective PythonAnywhere → PostgreSQL | OUI |

### Chapitre 5 — Ce que tu dois absolument y mettre

Ce chapitre doit montrer que tu maîtrises l'analyse de données. Structure recommandée :

**5.1 Prétraitement des données**
- Feature Store (fs_customer_rfm, fs_transaction_features)
- Normalisation StandardScaler sur RFM
- Gestion des valeurs manquantes par module

**5.2 Segmentation clients (RFM + K-Means)**
- Calcul des scores R, F, M avec formules
- Justification du k par la méthode du coude ET le score de silhouette
- Matrice des centroïdes par cluster
- Interprétation des 4 segments (Champions, Fidèles, À risque, Perdus)

**5.3 Scoring Crédit**
- Features sélectionnées et leur justification métier
- Comparaison RandomForest vs Logistic Regression via StratifiedKFold
- Métriques : Accuracy, F1, AUC
- Explication SHAP des décisions (après Phase 1.2)

**5.4 Prévision de Demande**
- Comparaison LinearRegression vs Prophet
- Métriques : MAE, RMSE, MAPE
- Intégration des calendriers culturels burkinabè

**5.5 Détection d'Anomalies**
- Isolation Forest : principe du contamination parameter
- Features utilisées et justification
- Taux d'anomalies observé, analyse des faux positifs

**5.6 Analyse du Panier d'Achat (Market Basket)**
- Principe algorithme Apriori
- Seuils support/confiance/lift choisis et justification
- Top 10 règles découvertes (avec les vraies données)

**5.7 Customer Lifetime Value**
- Formule CLV = panier_moyen × fréquence × durée_vie_estimée
- Indice de confiance par nombre d'achats
- Distribution CLV dans la base client

**5.8 Analyse de Cohortes**
- Matrice de rétention : lecture et interprétation
- Taux de rétention M+1, M+3, M+6

---

## PHASE 4 — FINALISATION
### Semaine 5 | Durée estimée : 8 heures de travail technique

---

### 4.1 — Tests complets
**Durée : 3h**

Tester chaque endpoint ML avec des données réelles :
```bash
# Test de chaque endpoint analytics :
curl -H "Authorization: Bearer <token>" https://<app>.pythonanywhere.com/api/v1/analytics/forecast
curl -H "Authorization: Bearer <token>" https://<app>.pythonanywhere.com/api/v1/analytics/rfm-segments/evaluate-k
curl -H "Authorization: Bearer <token>" https://<app>.pythonanywhere.com/api/v1/analytics/credit-scores/<id>/explain
curl -H "Authorization: Bearer <token>" https://<app>.pythonanywhere.com/api/v1/analytics/basket
curl -H "Authorization: Bearer <token>" https://<app>.pythonanywhere.com/api/v1/analytics/price-elasticity
curl -H "Authorization: Bearer <token>" https://<app>.pythonanywhere.com/api/v1/analytics/churn-risk
```

### 4.2 — Captures d'écran pour le rapport
**Durée : 2h**

Générer et capturer :
- Dashboard principal avec données réelles
- Graphique d'évolution RFM (scatter plot R vs F coloré par cluster)
- Tableau des règles d'association (Market Basket)
- Explication SHAP d'un client (format texte)
- Matrice de rétention cohort (heatmap)
- Prévisions de demande avec Prophet (graphique)

### 4.3 — Préparer la démonstration orale
**Durée : 3h**

Scénario de démo recommandé (10 minutes) :
1. Login → Dashboard → montrer les KPIs en temps réel
2. Analytics → RFM → montrer les 4 segments + churn risk
3. Analytics → Crédit → chercher un client → montrer le score + explication SHAP
4. Analytics → Paniers → montrer les règles d'association par produit
5. Analytics → Prévisions → montrer les alertes de rupture
6. ML Models → montrer le registre des entraînements (traçabilité MLflow)

---

## RÉCAPITULATIF — TOUTES LES MODIFICATIONS

### Modifications RÉALISÉES (toutes complétées avant la soutenance)

| Ref | Modification | Fichiers | Statut |
|---|---|---|---|
| 0.1 | Supprimer SHA-256 fallback → INDETERMINATE | `credit_scoring.py` | ✅ |
| 0.2 | Activer Prophet + holidays BF + features africaines | `demand_forecast.py` | ✅ |
| 0.3 | Flask-Limiter 3.8.0 rate limiting (`memory://`) | `extensions.py`, `auth/routes.py` | ✅ |
| 0.4 | Script cron PythonAnywhere (racine dépôt) | `scripts/cron_train_all.py` | ✅ |
| 0.5 | Threading entraînement manuel (HTTP 202) | `analytics/routes.py` | ✅ |
| 1.1 | Silhouette + Elbow K-Means + endpoint evaluate-k | `rfm_segmentation.py`, `analytics/routes.py` | ✅ |
| 1.2 | SHAP explicabilité crédit (TreeExplainer) | `credit_scoring.py`, `analytics/routes.py` | ✅ |
| 1.3 | Churn probability RFM + endpoint churn-risk | `rfm_segmentation.py`, `analytics/routes.py` | ✅ |
| 2.1 | Market Basket Analysis (Apriori, mlxtend) | `ml/market_basket.py`, `analytics/routes.py` | ✅ |
| 2.2 | Élasticité des remises (Price Elasticity) | `services/price_elasticity_service.py`, `analytics/routes.py` | ✅ |
| 2.3 | Contexte africain endpoint + `_add_african_context_features()` | `analytics/routes.py`, `demand_forecast.py` | ✅ |

**Celery et Redis supprimés** — remplacés par threads Python natifs + `scripts/cron_train_all.py`.  
**Tests :** 155 (127 ML unitaires + 17 intégration `test_integration_api.py` + 15 sécurité `test_security_rbac.py` + 12 RBAC `test_rbac_roles.py`).  
**CI/CD :** GitHub Actions avec `sshpass` + secret `PA_SSH_PASSWORD`. Pipeline bloque si tests échouent.  
**RF-05 :** `must_change_password=True` → 403 `PASSWORD_CHANGE_REQUIRED` sur toutes routes via `require_permission()`.  
**RF-16/RG-23 :** `approved_by_id` obligatoire si `discount_rate > 0`, validé dans `sale_service.create_sale()` → 422.  
**SSE :** Désactivé sur PythonAnywhere (`DISABLE_SSE=true`) — fallback polling React Query.  
**Migrations :** 10 migrations Alembic dans `backend/migrations/versions/`.  
**Sentry :** S'active si `SENTRY_DSN` défini dans l'env.

---

### Modifications initialement "conseillées" — toutes réalisées

| Modification | Fichiers | Statut |
|---|---|---|
| Enrichir les raisons anomalies (Phase 1.4) | `anomaly_detection.py` | ✅ |
| Endpoint `/health` de monitoring | `app/__init__.py` | ✅ |
| `data_confidence` dans les prévisions | `demand_forecast.py` | ✅ |
| Sentry SDK pour monitoring erreurs (optionnel) | `requirements.txt`, `app/__init__.py` | ✅ |
| Supprimer `redis` et `celery` de requirements | `requirements.txt` | ✅ — Celery/Redis supprimés |

---

### Modifications NON RECOMMANDÉES avant la soutenance (trop risquées)

| Modification | Raison de l'exclusion |
|---|---|
| JWT → httpOnly cookies | Conflit majeur frontend/backend, 6h+ de migration, risque régression élevé |
| Migration PostgreSQL | Impossible sur PythonAnywhere sans changer d'hébergeur |
| PWA offline (Service Worker) | Semaines de travail, hors scope pour la soutenance |
| CinetPay / WhatsApp API | Nécessite comptes business et approbation externe |
| Migration vers Vercel | Bénéfice faible, nouvelle configuration à tester |

---

## INFORMATIONS CAPITALES POUR L'IMPLÉMENTATION

### Structure exacte du projet
```
backend/
├── app/
│   ├── blueprints/
│   │   ├── analytics/routes.py     ← Ajouter tous les nouveaux endpoints ici
│   │   └── auth/routes.py          ← Ajouter @limiter.limit()
│   ├── ml/
│   │   ├── credit_scoring.py       ← Supprimer SHA-256, ajouter SHAP
│   │   ├── demand_forecast.py      ← Ajouter Prophet + features africaines
│   │   ├── rfm_segmentation.py     ← Ajouter Silhouette + Churn
│   │   ├── anomaly_detection.py    ← Enrichir les raisons
│   │   └── market_basket.py        ← NOUVEAU MODULE
│   ├── services/
│   │   └── price_elasticity_service.py ← NOUVEAU SERVICE
│   ├── tasks/
│   │   └── ml_tasks.py             ← Enregistrer MARKET_BASKET
│   └── extensions.py               ← Ajouter Flask-Limiter
└── scripts/
    └── cron_train_all.py           ← NOUVEAU SCRIPT
```

### Packages installés (tous dans requirements.txt)
```
shap==0.45.1            # SHAP explicabilité (TreeExplainer)
mlxtend==0.23.1         # Market Basket Apriori
Flask-Limiter==3.8.0    # Rate limiting (storage_uri="memory://")
prophet                 # Prévisions de demande + calendrier BF (déjà présent)
```

> Celery et Redis ont été **supprimés** de requirements.txt — non utilisés sur PythonAnywhere.

### Convention de nommage des modèles ML dans TRAIN_FUNCTIONS
```python
TRAIN_FUNCTIONS = {
    "DEMAND_FORECAST":    train_demand_forecast_task,
    "CREDIT_SCORING":     train_credit_scoring_task,
    "ANOMALY_DETECTION":  detect_anomalies_task,
    "ABC_XYZ":            compute_abc_xyz_task,
    "RFM_SEGMENTATION":   compute_rfm_segments_task,
    "MARKET_BASKET":      compute_market_basket_task,  ← à ajouter
}
```

### Pattern des endpoints analytics existants
Tous les endpoints analytics suivent ce pattern :
```python
@analytics_bp.get("/nom-endpoint")
@require_permission("analytics:read")
def nom_endpoint():
    """Docstring décrivant le RF correspondant."""
    # Filtres optionnels via request.args
    # Appel au module ML via from app.ml import module; module.latest()
    # Retourne toujours {"items": list, "count": int}
```

### Configuration PythonAnywhere
- **CPU limit :** Prophet peut être lent (30-90 sec). Le cron nocturne (`scripts/cron_train_all.py`, 02:00) gère ça.
- **MySQL 8.0 :** Toutes les tables ML existent (`ml_models`, `predictions`, feature stores, `token_blocklist`). 10 migrations Alembic appliquées.
- **SSE :** Désactivé (`DISABLE_SSE=true`) — fallback polling React Query.
- **Celery/Redis :** SUPPRIMÉS. Threads Python natifs pour l'entraînement à la demande (HTTP 202).
- **Cron correct :** `/home/<username>/.virtualenvs/gescom-bf/bin/python /home/<username>/gescom-bf/scripts/cron_train_all.py`
- **CI/CD :** GitHub Actions avec `sshpass` + secret `PA_SSH_PASSWORD` (pas de clés SSH).

### Métriques à présenter au jury pour chaque module

| Module | Métriques à montrer |
|---|---|
| RFM + K-Means | Silhouette score, Davies-Bouldin, inertie (Elbow), distribution des clusters, churn rate par segment |
| Churn Probability | % clients CRITIQUE, ELEVE, MODERE, FAIBLE + actions recommandées |
| Crédit Scoring | Accuracy RF, Accuracy LogReg, F1-score, AUC, top 3 facteurs SHAP par client |
| SHAP Explicabilité | Contributions par feature (positives/négatives), valeur de base, top 4 facteurs en français |
| Prévision Prophet | MAE, RMSE, algorithme utilisé (Prophet/Linear/Naïf), nb alertes rupture, `data_confidence` |
| Anomalies | N ventes analysées, taux d'anomalies (%), raisons les plus fréquentes |
| ABC/XYZ | % CA des produits A, nb produits Z (dead stock), valeur immobilisée |
| Market Basket | Nb règles découvertes, lift moyen, top 5 associations (Apriori/co-occurrence) |
| Price Elasticity | Élasticité par produit, R², recommandation politique de remise |
| CLV + data_confidence | CLV moyen, médiane, top 10 clients, indice de confiance |
| Cohortes | Taux de rétention M+1 et M+3, cohorte la plus fidèle |
| Tests CI/CD | 155 tests (127 ML + 17 intégration + 15 sécurité + 12 RBAC), pipeline bloquant |

---

*Plan généré le 23 juin 2026 — basé sur la lecture complète du code source*  
*Mis à jour le 1er juillet 2026 — toutes les phases 0, 1, 2 marquées comme réalisées (code v2 post-corrections).*
