# 20. Machine Learning — Modèles, Données et Métriques

> **Dernière mise à jour :** 24 juin 2026 — reflète l'état du code après corrections pré-soutenance (modules 0.1–2.3).
> Document détaillé → `docs/ANALYTIQUE-ML-IA-COMPLET.md`

## 20.1 Vue d'ensemble des modules analytiques et ML

> **Note de classification honnête** : tous les modules dans `ml/` ne sont pas du Machine Learning au sens strict. Le tableau ci-dessous précise la nature réelle de chaque technique.

| Module | Fichier | Technique réelle | Catégorie | Repli | Fréquence |
|---|---|---|---|---|---|
| ABC/XYZ produits | `ml/abc_xyz.py` | Règles pandas (CA cumulé + CV) — **aucun apprentissage** | **Analytique BI** | Identique | Hebdomadaire |
| Prévision demande | `ml/demand_forecast.py` | **Prophet 1.1.5** + sklearn LinearRegression | **ML supervisé** | Seasonal Naive | Hebdomadaire |
| Scoring crédit | `ml/credit_scoring.py` | Random Forest + LogReg + **SHAP TreeExplainer** | **ML supervisé** | Score règles pondérées | Hebdomadaire |
| Détection anomalies | `ml/anomaly_detection.py` | Isolation Forest + raisons enrichies | **ML non supervisé** | Z-score | Quotidienne |
| Segmentation RFM | `ml/rfm_segmentation.py` | K-Means auto-k (Silhouette/Elbow) | **ML non supervisé** | Quartiles | Mensuelle |
| Churn probability | `ml/rfm_segmentation.py` | Décroissance exponentielle `P=1-exp(-λ×R)` — **aucun entraînement** | **Heuristique statistique** | — | Mensuelle |
| Market Basket | `ml/market_basket.py` | **Apriori (mlxtend)** + co-occurrence fallback | **ML non supervisé** | Co-occurrence Counter | Hebdomadaire |

Service complémentaire :
| Service | Fichier | Technique |
|---|---|---|
| Élasticité prix | `services/price_elasticity_service.py` | Régression log-log |
| Contexte africain | `blueprints/analytics/routes.py` | Calcul temps réel (pas de modèle ML) |

## 20.2 Classification ABC/XYZ (`ml/abc_xyz.py`) — Analytique BI

> **Classification honnête** : ce module n'est **pas du Machine Learning**. C'est une **classification déterministe par règles métier** implémentée en pandas. Aucun algorithme d'apprentissage, aucun paramètre entraîné, résultat 100% reproductible à données identiques.

**Ce qu'il faut dire au jury** : *"ABC/XYZ est une méthode analytique BI classique — c'est la norme en gestion des stocks depuis les années 1950. Elle est pertinente et suffisante pour les PME burkinabè. Elle ne nécessite pas de ML."*

**ABC** — tri décroissant par CA, cumsum normalisé :
- A : 0–80 % du CA cumulé (produits stratégiques)
- B : 80–95 % (produits secondaires)
- C : 95–100 % (longue traîne)

**XYZ** — coefficient de variation (CV = σ/μ) de la demande hebdomadaire :
- X : CV < 0,5 (demande régulière — stock de sécurité justifié)
- Y : 0,5 ≤ CV ≤ 1,0 (demande variable)
- Z : CV > 1,0 (demande irrégulière — commande à la demande)

Données : `SaleLine.quantity`, `SaleLine.line_total` — 6 mois glissants, `Sale.status = 'VALIDEE'`
Endpoint : `GET /api/v1/analytics/abc-xyz`

## 20.3 Prévision de demande (`ml/demand_forecast.py`)

### Cascade de sélection d'algorithme

```
1. HAS_PROPHET et len(série) ≥ 30 jours → Prophet + jours fériés BF
2. HAS_SKLEARN                           → LinearRegression (index temp + dow)
3. Toujours disponible                   → Seasonal Naive (moyenne par jour de semaine)
```

### Jours fériés Burkina Faso (Prophet)

```python
burkina_events = pd.DataFrame([
    {"holiday": "Tabaski",              "ds": "2025-06-06", ...},
    {"holiday": "Tabaski",              "ds": "2026-05-26", ...},
    {"holiday": "Ramadan_fin",          "ds": "2025-03-30", ...},
    {"holiday": "Independance_BF",      "ds": "2025-08-05", ...},
    {"holiday": "Noel",                 "ds": "2025-12-25", ...},
])
```

Ces événements permettent à Prophet de capturer les pics de demande liés au calendrier islamique et aux fêtes nationales burkinabè.

### Alerte rupture de stock

```python
stock_prevu_j7 = stock.quantity - forecast_7d
is_alert = (stock.quantity < product.min_stock_threshold) OR (stock_prevu_j7 < 0)
quantite_recommandee = max(0, forecast_30d - stock.quantity) * (1 + FORECAST_SAFETY_MARGIN)
```

Endpoint : `GET /api/v1/analytics/forecast?alerts_only=true`

## 20.4 Scoring crédit (`ml/credit_scoring.py`)

### Score 0–100 → Niveaux de risque

| Score | Niveau | Action |
|---|---|---|
| 0–40 | ÉLEVÉ | Ne pas étendre le crédit |
| 41–70 | MOYEN | Crédit limité |
| 71–100 | FAIBLE | Crédit accordé normalement |

### 8 Features (labels FR)

| Feature | Label français |
|---|---|
| `nb_achats_credit_total` | Nombre d'achats à crédit |
| `montant_moyen_achat` | Montant moyen par achat |
| `delai_moyen_remboursement_jours` | Délai moyen de remboursement |
| `taux_retard` | Taux de retard de paiement |
| `anciennete_client_mois` | Ancienneté client (mois) |
| `frequence_achat_mensuelle` | Fréquence d'achat mensuelle |
| `solde_du_actuel` | Solde dû actuel |
| `is_technicien` | Est technicien de vente |

### Source de données (corrigée — SHA-256 supprimé)

- **REAL** (`FeatureDataSource.REAL`) : données réelles depuis `CustomerPayment` (si ≥ 3 paiements enregistrés)
- **SIMULATED** (`FeatureDataSource.SIMULATED`) : proxy `credit_balance` du modèle `Customer` si pas de données de paiement

> Le fallback SHA-256 déterministe a été **supprimé** — il n'était pas de la vraie IA mais une simulation reproductible. Le système utilise maintenant uniquement des données réelles ou un proxy observable.

### Algorithmes

- **ML** (≥ 20 clients, sklearn disponible) : `RandomForestClassifier(n_estimators=200)` + `LogisticRegressionCV`, cross-validation stratifiée 2–5 folds
- **Repli** : `score = (1-taux_retard)×70 + clip(1-delai/90,0,1)×20 + clip(freq,0,1)×10`

### Artefact ML et traçabilité

```python
# Sauvegarde du modèle RF pour SHAP
artifact_path = save_artifact({"rf_model": rf_model}, MODEL_TYPE, version)
register_model(model_type, version, algorithm, metrics, artifact_path=artifact_path)
```

### SHAP — Explicabilité (nouveau module 1.2)

```python
# explain_credit_score(customer_id) — app/ml/credit_scoring.py
explainer   = shap.TreeExplainer(rf_model)
shap_values = explainer.shap_values(X)
# shap_values est une liste [classe_0, classe_1]
# [1] = "bon payeur" — valeurs SHAP pour la classe positive
top_factors = sorted(zip(features, shap_values[1][0]), key=lambda x: abs(x[1]), reverse=True)
```

Endpoint : `GET /api/v1/analytics/credit-scores/<customer_id>/explain`

## 20.5 Détection d'anomalies (`ml/anomaly_detection.py`)

### Features (5)

`montant_total`, `remise_taux`, `heure_vente`, `ecart_vs_moyenne_produit`, `ecart_vs_moyenne_vendeur`

### Algorithme

- **Isolation Forest** : `n_estimators=200`, `contamination=0.02`
- **Repli Z-score** : `z = (montant - μ) / σ`, anomalie si |z| > 3

### Raisons d'anomalie (enrichies — module 1.4)

```python
if remise_taux >= 15:
    reasons.append("Remise élevée")
if ecart_produit > 1.0:
    reasons.append("Montant largement supérieur à la moyenne du produit")
if row.get("remise_taux", 0) > 0 and row.get("heure_vente", 12) < 8:
    reasons.append("Remise accordée en dehors des heures de supervision")   # NEW
if row.get("ecart_vs_moyenne_vendeur", 0) > 2:
    reasons.append(f"Volume {val:.1f}x supérieur à la moyenne du vendeur")  # NEW
if heure < 6 or heure > 21:
    reasons.append("Vente hors horaires habituels")
# Sinon :
reasons.append("Profil statistique atypique")
```

Endpoint : `GET /api/v1/analytics/anomalies`

## 20.6 Segmentation RFM (`ml/rfm_segmentation.py`)

### Dimensions RFM

- **R (Récence)** : `(now - MAX(created_at)).days`
- **F (Fréquence)** : `COUNT(sales)` sur 12 mois
- **M (Montant)** : `SUM(line_total)` sur 12 mois

### K optimal — Silhouette + Elbow (module 1.1)

```python
def evaluate_optimal_k(X_scaled):
    """Teste k=2 à 8, sélectionne par silhouette_score maximal."""
    results = []
    for k in range(2, 9):
        km = KMeans(n_clusters=k, n_init=10, random_state=42)
        labels = km.fit_predict(X_scaled)
        if len(set(labels)) < 2:
            continue
        results.append({
            "k": k,
            "silhouette":      silhouette_score(X_scaled, labels),
            "davies_bouldin":  davies_bouldin_score(X_scaled, labels),
            "inertia":         km.inertia_,
        })
    best = max(results, key=lambda r: r["silhouette"])
    return best["k"], results
```

- `train(n_clusters=None)` : appelle `evaluate_optimal_k()` si n_clusters non fourni
- Endpoint d'audit : `GET /api/v1/analytics/rfm-segments/evaluate-k`

### Probabilité de Churn (module 1.3) — Heuristique statistique

> **Classification honnête** : ce module n'est **pas du Machine Learning**. Il n'y a aucun entraînement, aucune donnée labellisée, aucun split train/test, aucune métrique AUC/F1. C'est une **formule analytique à un paramètre** calibré sur la médiane de la récence.

```python
def compute_churn_probability(df_rfm):
    """
    Modèle heuristique — décroissance exponentielle :
    P(churn) = 1 - exp(-λ × recency)
    λ = ln(2) / median_recency  (demi-vie = médiane de récence)
    Ajustement fréquence : P_adj = P × (1 - 0.25 × freq_weight)
    
    Pas d'entraînement. Pas de données labellisées.
    Valide pour une PME sans historique de churns explicites.
    """
```

**Justification du choix** : une PME burkinabè de 50–500 clients ne dispose pas de données labellisées "client churné / pas churné". Un modèle supervisé (RandomForest, XGBoost) nécessiterait des centaines d'exemples positifs. La décroissance exponentielle est un standard en CRM analytique pour estimer le risque de désengagement sans labels.

**Ce qu'il faut dire au jury** : *"Ce n'est pas un modèle ML — c'est un modèle heuristique statistique inspiré de la théorie de la survie. Il est justifié par l'absence de données labellisées dans le contexte des PME ciblées."*

Payload résultat :
```json
{
  "churn_probability": 0.73,
  "churn_risk": "ELEVE",
  "churn_action": "Réactivation urgente — bon de réduction personnalisé"
}
```

Endpoint : `GET /api/v1/analytics/churn-risk`

## 20.7 Market Basket Analysis (`ml/market_basket.py`)

### Algorithme principal : Apriori (mlxtend)

```python
HAS_MLXTEND = False
try:
    from mlxtend.frequent_patterns import apriori, association_rules
    HAS_MLXTEND = True
except ImportError:
    pass
```

### Cascade

1. **Apriori** (`HAS_MLXTEND=True`) : `min_support=0.01`, `min_confidence=0.3`, résultats triés par lift
2. **Co-occurrence** (fallback) : `Counter` + `combinations`, top N paires les plus fréquentes

### Endpoints

- `GET /api/v1/analytics/basket` — retourne les règles du dernier modèle entraîné
- `POST /api/v1/analytics/basket/train` — entraîne en arrière-plan (thread, 202 Accepted)

## 20.8 Analyse d'élasticité prix (`services/price_elasticity_service.py`)

### Modèle

**Log-log regression** : `ln(quantité) = α + β × ln(1 - taux_remise)`

β = élasticité prix :
- β > 0 : demande **inélastique** (remise n'améliore pas significativement les volumes)
- β < -1 : demande **élastique** (réduire les remises réduit les ventes)

### Source de données (colonnes corrigées)

- `Sale.discount_rate` (entier `{0, 5, 10, 15, 20}`) → converti en `/ 100.0`
- `SaleLine.unit_price_applied` (pas `unit_price` — colonne inexistante)

Endpoint : `GET /api/v1/analytics/price-elasticity?months=6`

## 20.9 Features Contextuelles Africaines (`routes.py → /african-context`)

Calcul temps réel (pas de modèle ML entraîné) :

| Feature | Description | Source |
|---|---|---|
| `active_contexts` | Événements actifs (Tabaski, saison pluies, rentrée, semaine paie) | Date système |
| `saison_pluies` | Boolean — juin à septembre | Date système |
| `weekend_boost` | Vendredi (+20%) / Samedi (+35%) — pics de fréquentation | `today.weekday()` |
| `indice_stress_tresorerie` | Taux de paiements LATE / total (90j). Seuils : <10%=LOW, <25%=MEDIUM, ≥25%=HIGH | `CustomerPayment` |
| `propension_credit_informel` | % clients actifs 90j sans historique `CustomerPayment` formel | `Sale` + `CustomerPayment` |

Endpoint : `GET /api/v1/analytics/african-context`

## 20.10 Registre des modèles et traçabilité (RNF-17)

### Table `ml_models`

```
id, model_type, version, algorithm, metrics_json, artifact_path, mlflow_run_id, trained_at, is_active
```

- **Versionnage** : `{model_type}_{YYYYMMDD}_{HHMMSS}`
- **Désactivation automatique** du modèle précédent à chaque ré-entraînement
- **`artifact_path`** : chemin vers le fichier `.joblib` sauvegardé par MLflow — requis pour SHAP

### Table `predictions`

```
id, model_id (FK), prediction_type, entity_type, entity_id, payload_json, created_at
```

### TRAIN_FUNCTIONS (6 modules enregistrés)

```python
TRAIN_FUNCTIONS = {
    "DEMAND_FORECAST":   compute_demand_forecast_task,
    "CREDIT_SCORING":    compute_credit_scoring_task,
    "ANOMALY_DETECTION": compute_anomaly_detection_task,
    "ABC_XYZ":           compute_abc_xyz_task,
    "RFM_SEGMENTATION":  compute_rfm_segmentation_task,
    "MARKET_BASKET":     compute_market_basket_task,
}
```

### Orchestration nocturne — `scripts/cron_train_all.py`

Le script `scripts/cron_train_all.py` (à la racine du projet, **pas dans `backend/`**) est l'unique tâche planifiée PythonAnywhere. Il exécute dans l'ordre :
1. `etl_extract_and_clean` → `etl_validate` → `etl_build_features` (pipeline ETL)
2. Les 6 modèles ML ci-dessus en séquence

Log : `logs/cron_train_all.log`. Exit code 1 si ≥ 1 erreur (PythonAnywhere notifie par email).

## 20.11 Dépendances ML (`requirements.txt`)

```txt
# Core ML
scikit-learn==1.5.1    # RF, IsolationForest, KMeans, LinearRegression, silhouette
pandas==2.2.2
numpy==1.26.4
joblib==1.4.2          # sérialisation artefacts

# Séries temporelles
prophet==1.1.5         # Prévision demande + jours fériés BF

# Boosting
xgboost==2.1.1         # Résidus Prophet (optionnel)

# Explicabilité
shap==0.45.1           # TreeExplainer scoring crédit (NEW)

# Association rules
mlxtend==0.23.1        # Algorithme Apriori (NEW, fallback co-occurrence si absent)

# Suivi
mlflow==2.14.3         # Registry modèles, artefacts
```

Toutes les dépendances sont **optionnelles avec fallback** : les flags `HAS_SKLEARN`, `HAS_PROPHET`, `HAS_SHAP`, `HAS_MLXTEND` permettent à l'application de fonctionner même si une bibliothèque est absente.
