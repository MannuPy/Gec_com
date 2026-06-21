# 20. Machine Learning — Modèles, Données et Métriques

> **Dernière mise à jour :** 19 juin 2026 — reflète le code réellement implémenté dans `backend/app/ml/`.
> Document exhaustif → `docs/ANALYTIQUE-ML-IA-COMPLET.md`

## 20.1 Vue d'ensemble des modèles

| Modèle | Fichier | Algorithme (ML) | Repli (sans sklearn) | Fréquence |
|---|---|---|---|---|
| ABC/XYZ produits | `ml/abc_xyz.py` | Règles pandas (déterministe) | Identique | Hebdomadaire |
| Prévision demande | `ml/demand_forecast.py` | sklearn LinearRegression + Prophet/XGBoost si dispo | Seasonal Naive | Hebdomadaire |
| Scoring crédit | `ml/credit_scoring.py` | Random Forest + LogReg cross-validés | Score par règles pondérées | Hebdomadaire |
| Détection anomalies | `ml/anomaly_detection.py` | Isolation Forest (n_estimators=200) | Z-score (montant_total) | Quotidienne |
| Segmentation RFM | `ml/rfm_segmentation.py` | K-Means (k=4, StandardScaler) | Segmentation par quartiles | Mensuelle |

## 20.2 Classification ABC/XYZ (`ml/abc_xyz.py`)

### Algorithme

**ABC** — tri décroissant par CA, cumsum normalisé :
- A : 0-80% du CA cumulé
- B : 80-95%
- C : 95-100%

**XYZ** — coefficient de variation (CV = σ/μ) de la demande hebdomadaire :
- X : CV < 0,5 (régulier)
- Y : 0,5 ≤ CV ≤ 1,0 (variable)
- Z : CV > 1,0 (irrégulier)

### Données d'entrée
- `sale_lines.quantity`, `sale_lines.line_total` — 6 mois glissants
- Filtre : `sales.status = 'VALIDEE'`

### Sortie
- Endpoint : `GET /api/v1/analytics/abc-xyz`
- Payload : `{ product_sku, product_name, revenue, abc_class, cv, xyz_class, combined_class }`
- Métriques : `n_products`, `n_class_a/b/c`

## 20.3 Prévision de demande (`ml/demand_forecast.py`)

### Algorithme (choix automatique)

1. **Prophet + XGBoost résidus** (si prophet ET xgboost installés, historique ≥ 14j) → `PROPHET+XGBOOST_RESIDUALS`
2. **sklearn LinearRegression** (si sklearn, historique ≥ 14j) → `SKLEARN_LINEAR_TREND`
   - Features : index temporel + indicatrices jour de semaine (lundi-dimanche)
   - Horizon : 7j et 30j
3. **Seasonal Naive** (toujours disponible) → `SEASONAL_NAIVE`
   - Moyenne par jour de semaine sur l'historique

### Calcul d'alerte rupture

```python
stock_prevu_j7 = stock.quantity - forecast_7d
is_alert = (stock.quantity < product.min_stock_threshold) OR (stock_prevu_j7 < 0)
quantite_recommandee = max(0, forecast_30d - stock.quantity) * (1 + FORECAST_SAFETY_MARGIN)
```

### Sortie
- Endpoint : `GET /api/v1/analytics/forecast?alerts_only=true`
- Intégration dashboard : alertes `RUPTURE_STOCK` dans le widget "Alertes IA"

## 20.4 Scoring crédit (`ml/credit_scoring.py`)

### Score 0-100 → Niveaux de risque

```
0-40   → ÉLEVÉ  : ne pas étendre le crédit
41-70  → MOYEN  : crédit limité
71-100 → FAIBLE : crédit accordé normalement
```

### Features (8)

`nb_achats_credit_total`, `montant_moyen_achat`, `delai_moyen_remboursement_jours`,
`taux_retard`, `anciennete_client_mois`, `frequence_achat_mensuelle`, `solde_du_actuel`, `is_technicien`

### Double source de données

- **REAL** : depuis `customer_payments` (si ≥ 3 paiements enregistrés)
- **SIMULATED** : hash SHA-256(customer_id) → graine → `taux_retard ~ Beta(2,5)` (déterministe et reproductible)

### Algorithmes

- **ML** (≥ 20 clients, sklearn) : Random Forest 200 arbres + LogReg, cross-validation stratifiée (2-5 folds)
- **Repli** : `score = (1-taux_retard)×70 + clip(1-delai/90,0,1)×20 + clip(freq,0,1)×10`

### Sortie
- Endpoint : `GET /api/v1/analytics/credit-scores?risk_level=ELEVE`
- Intégration dashboard : alertes `CREDIT_RISK` pour les clients niveau ÉLEVÉ

## 20.5 Détection d'anomalies (`ml/anomaly_detection.py`)

### Features (5)

`montant_total`, `remise_taux`, `heure_vente`, `ecart_vs_moyenne_produit`, `ecart_vs_moyenne_vendeur`

### Algorithme

- **Isolation Forest** : `n_estimators=200`, `contamination=ANOMALY_CONTAMINATION (0.02)`
- **Repli Z-score** : `z = (montant - μ) / σ`, anomalie si |z| > 3

### Qualification des raisons

```python
if remise_taux >= 15:      → "Remise élevée"
if ecart_produit > 1.0:    → "Montant largement supérieur à la moyenne du produit"
if ecart_vendeur > 1.0:    → "Montant largement supérieur à la moyenne du vendeur"
if heure < 6 or heure > 21: → "Vente hors horaires habituels"
# Sinon :                  → "Profil statistique atypique"
```

### Sortie
- Endpoint : `GET /api/v1/analytics/anomalies`
- Intégration dashboard : alertes `ANOMALIE` severity `WARNING`

## 20.6 Segmentation RFM (`ml/rfm_segmentation.py`)

### Dimensions

- **R (Récence)** : `(now - MAX(created_at)).days`
- **F (Fréquence)** : `COUNT(sales)` sur 12 mois
- **M (Montant)** : `SUM(line_total)` sur 12 mois

### Segments

| Segment | Critère | Action |
|---|---|---|
| CHAMPIONS | Faible R, fort F et M | Fidélité, crédit étendu |
| REGULIERS | Faible R, faible M | Relances ciblées |
| A_RISQUE | Fort R, fort M historique | Réactivation |
| OCCASIONNELS | Fort R, faible M | Communication standard |

### Algorithme

- **K-Means** : `k=4`, `StandardScaler`, `n_init=10`, `random_state=42`
  - Labels assignés par score = F + M - R sur les centres
- **Repli** : segmentation par médiane R et FM (déterministe)

### Double source de données
- Feature Store `fs_customer_rfm` (priorité)
- Calcul direct sur `sales ⋈ sale_lines` (repli)

## 20.7 Registre des modèles et traçabilité (RNF-17, RG-40)

### Table `ml_models`

Chaque entraînement crée une entrée :

```
id, model_type, version, algorithm, metrics_json, artifact_path, mlflow_run_id, trained_at, is_active
```

- **Versionnage :** `{model_type}_{YYYYMMDD}_{HHMMSS}`
- **Désactivation automatique** du modèle précédent à chaque ré-entraînement

### Table `predictions`

Chaque prédiction individuelle est tracée :

```
id, model_id (FK), prediction_type, entity_type, entity_id, payload_json, created_at
```

### API registre

`GET /api/v1/analytics/ml/models` — liste tous les modèles avec métriques

### Déclenchement entraînement (RF-29)

`POST /api/v1/analytics/ml/train/DEMAND_FORECAST` (permission `ml:train`, rôle ADMIN)

Types supportés : `DEMAND_FORECAST`, `CREDIT_SCORING`, `ANOMALY_DETECTION`, `ABC_XYZ`

## 20.8 MLflow (optionnel)

Intégration via classe `MLflowRun` no-op si `mlflow` non installé.

- `MLFLOW_TRACKING_URI` : `file:./mlruns` (local) ou URI serveur distant
- `MLFLOW_EXPERIMENT_NAME` : `gescom-bf`
- Loggé par run : paramètres d'entraînement + métriques + run_id stocké dans `ml_models.mlflow_run_id`

## 20.9 Dépendances (toutes optionnelles)

```txt
scikit-learn>=1.3   # Random Forest, IsolationForest, KMeans, LinearRegression
prophet>=1.1        # Prévision série temporelle (Prophet)
xgboost>=2.0        # Résidus Prophet
mlflow>=2.0         # Suivi expériences
joblib>=1.3         # Sauvegardes artefacts .joblib
great-expectations  # Validation qualité ETL
celery[redis]>=5.3  # Entraînements asynchrones
```
