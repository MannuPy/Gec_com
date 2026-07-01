# Modules Analytiques, Prédictifs, Machine Learning et IA — GesCom-BF
## Documentation exhaustive — État au 24 juin 2026 (après corrections pré-soutenance)

---

## Table des matières

1. [Vue d'ensemble et positionnement stratégique](#1-vue-densemble-et-positionnement-stratégique)
2. [Architecture générale des modules IA](#2-architecture-générale-des-modules-ia)
3. [Module 1 — Classification ABC/XYZ des produits](#3-module-1--classification-abcxyz-des-produits)
4. [Module 2 — Prévision de demande et alertes de rupture](#4-module-2--prévision-de-demande-et-alertes-de-rupture)
5. [Module 3 — Scoring crédit client](#5-module-3--scoring-crédit-client)
6. [Module 4 — Segmentation client RFM](#6-module-4--segmentation-client-rfm)
7. [Module 5 — Détection d'anomalies sur les ventes](#7-module-5--détection-danomalies-sur-les-ventes)
8. [Module 6 — Analyse de cohortes clients](#8-module-6--analyse-de-cohortes-clients)
9. [Module 7 — Customer Lifetime Value (CLV)](#9-module-7--customer-lifetime-value-clv)
10. [Module 8 — Tableau de bord décisionnel temps réel](#10-module-8--tableau-de-bord-décisionnel-temps-réel)
11. [Module 9 — Comparatif inter-succursales](#11-module-9--comparatif-inter-succursales)
12. [Pipeline ETL et Feature Store](#12-pipeline-etl-et-feature-store)
13. [Registre des modèles et traçabilité](#13-registre-des-modèles-et-traçabilité)
14. [Intégration MLflow](#14-intégration-mlflow)
15. [Tâches Celery et automatisation](#15-tâches-celery-et-automatisation)
16. [API REST — Endpoints analytiques](#16-api-rest--endpoints-analytiques)
17. [Frontend — AnalyticsPage et visualisations](#17-frontend--analyticspage-et-visualisations)
18. [Exigences, contraintes et décisions techniques](#18-exigences-contraintes-et-décisions-techniques)
19. [Impacts métier et ROI attendu](#19-impacts-métier-et-roi-attendu)
20. [Limites actuelles et perspectives](#20-limites-actuelles-et-perspectives)
21. [Nouveaux modules — corrections pré-soutenance](#21-nouveaux-modules--corrections-pré-soutenance)

---

## 1. Vue d'ensemble et positionnement stratégique

### 1.1 Contexte métier

GesCom-BF est un logiciel de gestion commerciale SaaS multi-succursales destiné aux PME burkinabè (commerce de détail, quincaillerie, matériaux de construction). Le marché visé est caractérisé par :

- **Gestion de crédit informelle** : les clients paient à terme sans système de scoring formel → risque d'impayés élevé
- **Approvisionnement empirique** : les commandes fournisseurs sont décidées "à l'œil" → surstock ou rupture fréquente
- **Multiples points de vente** (succursales + dépôt) sans vision consolidée des performances
- **Fragilité du contrôle interne** : remises excessives, ventes hors horaires, anomalies non détectées

### 1.2 Pourquoi une couche analytique et IA ?

La couche analytique/IA est **le facteur différenciant** de GesCom-BF face aux logiciels de caisse classiques. Elle répond à une demande concrète des commerçants :

| Problème terrain | Solution IA/Analytique |
|---|---|
| "Je ne sais pas quand commander mon stock" | Prévision de demande → alerte rupture automatique |
| "Je ne sais pas si ce client peut prendre à crédit" | Score de solvabilité 0-100 par client |
| "J'ai peur que mon caissier fasse des remises abusives" | Détection d'anomalies Isolation Forest |
| "Je ne sais pas quels produits sont vraiment rentables" | Classification ABC/XYZ |
| "Je n'arrive pas à segmenter mes clients pour les relances" | Segmentation RFM K-Means |
| "Je ne sais pas combien rapporte un client sur sa durée de vie" | CLV estimée par client |
| "Je veux comparer mes succursales objectivement" | Radar chart comparatif normalisé |
| "Je veux savoir quels clients je risque de perdre" | Analyse de cohortes rétention M+0..M+12 |

### 1.3 Référentiel des exigences (RF)

| Code RF | Description |
|---|---|
| RF-24 | Tableau de bord étendu : marges, multi-site, consolidé |
| RF-25 | Prévisions de demande et alertes de rupture |
| RF-26 | Classification ABC/XYZ et segmentation RFM |
| RF-27 | Scoring crédit client |
| RF-28 | Détection d'anomalies sur les ventes |
| RF-29 | Déclenchement du ré-entraînement des modèles |
| Feature C | Tableau de bord comparatif inter-succursales |
| Feature E | Analyse de cohortes clients |
| Feature F | Customer Lifetime Value (CLV) |
| RG-38 | Alerte automatique si stock < seuil minimum |
| RG-40 | Traçabilité : chaque prédiction liée à son modèle source |
| RNF-17 | Registre versionné des modèles ML entraînés |

---

## 2. Architecture générale des modules IA

### 2.1 Structure des fichiers

```
backend/app/
├── ml/
│   ├── __init__.py
│   ├── common.py             # utilitaires partagés : persistance, MLflow, registre
│   ├── abc_xyz.py            # Classification ABC/XYZ
│   ├── demand_forecast.py    # Prévision de demande + alertes rupture
│   ├── credit_scoring.py     # Scoring crédit client
│   ├── rfm_segmentation.py   # Segmentation RFM K-Means
│   └── anomaly_detection.py  # Détection anomalies Isolation Forest
├── services/
│   ├── analytics_service.py  # KPIs dashboard, tendance ventes, top produits
│   └── etl_service.py        # Pipeline ETL + Feature Store
├── blueprints/
│   ├── analytics/routes.py   # Endpoints /analytics/* (ML + cohortes + CLV)
│   └── reports/routes.py     # Endpoints /reports/* (dashboard + comparatif)
├── tasks/
│   ├── ml_tasks.py           # Tâches Celery d'entraînement
│   └── etl_tasks.py          # Tâches Celery ETL
└── models/
    ├── ml.py                 # MLModel + Prediction (registre)
    └── feature_store.py      # Tables intermédiaires Feature Store
```

### 2.2 Flux de données général

```
Données opérationnelles (sales, sale_lines, customers, stock)
          │
          ▼
    [Pipeline ETL]          ← etl_service.py (Celery quotidien)
    extract_and_clean()
    validate_quality()
    build_features()
          │
          ▼
    [Feature Store]         ← Tables fs_daily_sales, fs_customer_rfm,
                               fs_customer_credit_features, fs_transaction_features
          │
          ▼
    [Modules ML]            ← app/ml/*.py (train + latest)
    - abc_xyz
    - demand_forecast
    - credit_scoring
    - rfm_segmentation
    - anomaly_detection
          │
          ▼
    [Registre MLModel]      ← Table ml_models (version, algo, métriques, MLflow)
    [Predictions]           ← Table predictions (entity_id, payload_json)
          │
          ▼
    [Endpoints API REST]    ← /analytics/* /reports/*
          │
          ▼
    [Frontend AnalyticsPage] ← Graphiques Recharts (BarChart, RadarChart, AreaChart...)
```

### 2.3 Principe de repli (fallback)

**Tous les modules ML ont un repli automatique** quand les dépendances lourdes (scikit-learn, Prophet, XGBoost) sont absentes ou quand les données sont insuffisantes :

| Module | Technique réelle | Catégorie | Mode repli |
|---|---|---|---|
| ABC/XYZ | Règles pandas déterministes (cumsum + CV) — **pas de ML** | **Analytique BI** | Identique |
| Prévision demande | **Prophet 1.1.5** (holidays BF) + sklearn.LinearRegression | **ML supervisé** | Seasonal Naive |
| Scoring crédit | Random Forest + Logistic Regression cross-validés + SHAP | **ML supervisé** | Score pondéré par règles |
| Segmentation RFM | K-Means auto-k (Silhouette/Elbow) | **ML non supervisé** | Segmentation par quartiles |
| Churn probability | Décroissance exponentielle `P=1-exp(-λ×R)` — **pas de ML** | **Heuristique statistique** | — |
| Anomalies | Isolation Forest | **ML non supervisé** | Z-score (règle statistique) |

---

## 3. Module 1 — Classification ABC/XYZ des produits *(Analytique BI — pas de ML)*

> **Note** : ce module est une classification déterministe par règles métier (pandas). Ce n'est pas du Machine Learning. Voir justification en §3.2.

### 3.1 Besoin métier

Un commerçant typique gère 200 à 2000 références produits. Sans classification, il traite tous les produits de la même façon : même fréquence de commande, même espace de stockage, même attention commerciale. En réalité :
- 20% des produits génèrent 80% du CA → doivent être prioritaires
- Certains produits se vendent régulièrement → stock de sécurité justifié
- D'autres produits sont imprévisibles → commande à la demande

### 3.2 Définition des classes

**Classe ABC — contribution au chiffre d'affaires cumulé :**

| Classe | Seuil cumulé | Signification |
|---|---|---|
| A | 0–80% du CA total | Produits stratégiques — priorité absolue |
| B | 80–95% du CA total | Produits importants — suivi régulier |
| C | 95–100% du CA total | Produits secondaires — stock minimal |

**Classe XYZ — régularité de la demande (coefficient de variation) :**

| Classe | CV = σ/μ | Signification |
|---|---|---|
| X | CV < 0,5 | Demande régulière et prévisible |
| Y | 0,5 ≤ CV ≤ 1,0 | Demande variable mais gérable |
| Z | CV > 1,0 | Demande très irrégulière |

**Combinaison AX / AY / AZ... (9 classes) :**

| | X (régulier) | Y (variable) | Z (irrégulier) |
|---|---|---|---|
| **A (fort CA)** | AX : stock de sécurité, commande auto | AY : suivi hebdo | AZ : commande à la demande |
| **B (moyen CA)** | BX : stock modéré | BY : examen mensuel | BZ : alerte rupture |
| **C (faible CA)** | CX : stock minimal | CY : à évaluer | CZ : à déréférencer ? |

### 3.3 Implémentation technique

**Fichier :** `backend/app/ml/abc_xyz.py`

**Algorithme :**

```python
# Étape 1 — Charger les ventes des 6 derniers mois
df = _load_sales_dataframe(months=6)
# → requête SaleLine ⋈ Sale (VALIDEE), colonnes : product_id, quantity, line_total, created_at

# Étape 2 — ABC : tri par CA décroissant, cumsum normalisé
revenue_by_product = df.groupby("product_id")["line_total"].sum().sort_values(ascending=False)
cumulative = revenue_by_product.cumsum() / total_revenue
abc_class = "A" si cumul ≤ 0.80, "B" si cumul ≤ 0.95, sinon "C"

# Étape 3 — XYZ : coefficient de variation de la demande hebdomadaire
weekly = df.groupby(["product_id", "week"])["quantity"].sum()
cv = std / mean  # par product_id
xyz_class = "X" si cv < 0.5, "Y" si cv ≤ 1.0, sinon "Z"

# Étape 4 — Persister dans predictions + registre ml_models
record_predictions(model, "ABC_XYZ", entries)
```

**Algorithme utilisé :** `PANDAS_RULES_ABC_XYZ` — règles métier déterministes, **pas de ML**. Résultat identique pour les mêmes données. Justification : méthode standard en gestion des stocks (Pareto/ABC depuis les années 1950), suffisante et pertinente pour les PME burkinabè sans historique labellisé.

**Métriques trackées :** `n_products`, `n_class_a`, `n_class_b`, `n_class_c`

**Fréquence :** tâche Celery `compute_abc_xyz_task` — hebdomadaire

### 3.4 Données d'entrée

| Champ | Table | Description |
|---|---|---|
| `product_id` | `sale_lines` | Identifiant produit |
| `quantity` | `sale_lines` | Quantité vendue par transaction |
| `line_total` | `sale_lines` | CA généré par ligne |
| `created_at` | `sales` | Date de la vente (pour agrégation hebdo) |
| Filtre | `sales.status = 'VALIDEE'` | Exclure les ventes annulées |

### 3.5 Sortie API

`GET /api/v1/analytics/abc-xyz?abc_class=A&xyz_class=X`

```json
{
  "items": [
    {
      "product_id": "uuid",
      "product_sku": "CIMENT-50KG",
      "product_name": "Ciment 50kg",
      "revenue": 1250000.0,
      "abc_class": "A",
      "cv": 0.32,
      "xyz_class": "X",
      "combined_class": "AX"
    }
  ],
  "count": 12
}
```

### 3.6 Affichage frontend

- **Tableau interactif** avec tri et filtre par classe ABC ou XYZ
- **BarChart Recharts** — CA par classe A/B/C
- **Badges colorés** — AX en vert (idéal), AZ/BZ en orange (risque), CZ en rouge

### 3.7 Impact métier

- Identifier les 20% de produits générant 80% du CA → ne jamais rompre sur ceux-là
- Prioriser les commandes fournisseurs sur les AX (stratégiques + prévisibles)
- Réduire le stock des CZ (faible CA + irrégulier) → libère du capital
- Argument de vente : les concurrents ne proposent pas ce niveau d'analyse

---

## 4. Module 2 — Prévision de demande et alertes de rupture

### 4.1 Besoin métier

La rupture de stock est la **première cause de perte de CA** dans le commerce de détail. Pour un commerçant Burkinabè :
- Il commande "quand le stock est vide" → perte de ventes pendant les délais d'approvisionnement (2-7 jours)
- Il sur-commande par peur → capital immobilisé, produits périmés
- Les pics de demande (Tabaski, fin de mois, rentrée scolaire) sont imprévisibles sans outil

**Objectif :** prédire la demande à 7 et 30 jours par couple (produit, succursale), calculer la date probable de rupture et recommander une quantité de commande.

### 4.2 Algorithmes implémentés (avec repli automatique)

Le système choisit le meilleur algorithme disponible :

**Niveau 3 (optimal) — Prophet + XGBoost résidus :**
- Prophet pour la tendance et la saisonnalité (jours fériés BF intégrés)
- XGBoost sur les résidus Prophet
- Conditions : `prophet` ET `xgboost` installés, historique ≥ 14 jours
- Algorithme tracé : `PROPHET+XGBOOST_RESIDUALS`

**Niveau 2 — sklearn LinearRegression avec saisonnalité :**
- Régression linéaire sur l'indice temporel + variables indicatrices jour de la semaine
- Conditions : `scikit-learn` installé, historique ≥ 14 jours
- Algorithme tracé : `SKLEARN_LINEAR_TREND`

**Niveau 1 (repli) — Seasonal Naive :**
- Moyenne par jour de la semaine sur l'historique disponible
- Toujours disponible, même sans dépendances ML
- Algorithme tracé : `SEASONAL_NAIVE`

### 4.3 Implémentation technique

**Fichier :** `backend/app/ml/demand_forecast.py`

```python
# Chargement des ventes journalières par (product_id, branch_id)
daily = _load_daily_demand(months=6)
# → SaleLine ⋈ Sale, groupby product_id + branch_id + date, sum(quantity)

# Pour chaque série (product_id, branch_id) :
series = group.set_index("date")["quantity"].sort_index()
series = series.reindex(full_date_range, fill_value=0)  # remplir les jours sans vente

forecast_7d, forecast_30d, algorithm = _forecast_series(series)

# Calcul de l'alerte :
stock_prevu_j7 = stock_disponible - forecast_7d
is_alert = (stock_disponible < seuil_min) OR (stock_prevu_j7 < 0)

# Quantité recommandée avec marge de sécurité (config: 10%)
quantite_recommandee = max(0, forecast_30d - stock_disponible) * (1 + safety_margin)
```

### 4.4 Features utilisées

| Feature | Description | Source |
|---|---|---|
| Demande journalière (série temporelle) | Quantité vendue par jour | `sale_lines.quantity` groupé par date |
| Saisonnalité hebdomadaire | Indicatrices lundi-dimanche | Dérivé de `created_at` |
| Tendance linéaire | Index temporel | Calculé algorithmiquement |
| Stock disponible actuel | Pour calculer la date de rupture | `stock.quantity` |
| Seuil minimum | Seuil d'alerte réapprovisionnement | `products.min_stock_threshold` |

### 4.5 Paramètres configurables

| Paramètre | Valeur par défaut | Config key |
|---|---|---|
| Fenêtre historique | 6 mois | `months` (arg `train()`) |
| Historique minimum | 14 jours | `MIN_HISTORY_DAYS = 14` |
| Marge de sécurité | 10% | `FORECAST_SAFETY_MARGIN` |
| Horizon prévision | 7 et 30 jours | Fixé dans le code |

### 4.6 Sortie et alertes

`GET /api/v1/analytics/forecast?alerts_only=true&branch_id=uuid`

```json
{
  "items": [
    {
      "product_id": "uuid",
      "product_name": "Fer à béton 10mm",
      "product_sku": "FER-10",
      "branch_id": "uuid",
      "forecast_7d": 45.0,
      "forecast_30d": 180.0,
      "stock_disponible": 12,
      "seuil_min": 20,
      "stock_prevu_j7": -33.0,
      "alerte_rupture": true,
      "quantite_recommandee": 186.0,
      "algorithm": "SKLEARN_LINEAR_TREND"
    }
  ]
}
```

**Intégration tableau de bord :** les alertes de rupture apparaissent dans le widget "Alertes IA" du tableau de bord temps réel (type `RUPTURE_STOCK`, severity `CRITICAL` si stock = 0, `WARNING` si stock < seuil prévu J+7).

### 4.7 Impact métier

- Réduction des ruptures de stock estimée à 30-40% (benchmark littérature PME retail)
- Quantification des besoins fournisseurs : base pour la négociation des volumes
- Réduction du surstock : commande calculée, pas estimée
- Délai avant rupture visible = temps d'action pour le commerçant

---

## 5. Module 3 — Scoring crédit client

### 5.1 Besoin métier

En Afrique de l'Ouest, le crédit informel (vente à terme, "créance") est une pratique courante entre commerçants et clients réguliers. Sans système de scoring :
- Le commerçant accorde du crédit "à l'instinct" ou selon la relation personnelle
- Les impayés représentent 10-20% du crédit accordé (estimation terrain)
- Aucune traçabilité des comportements de remboursement

**Objectif :** attribuer à chaque client un **score de solvabilité 0-100** et un **niveau de risque** (FAIBLE / MOYEN / ÉLEVÉ) pour guider les décisions d'octroi de crédit.

### 5.2 Score et niveaux de risque

```
Score 0-40   → Risque ÉLEVÉ   : ne pas étendre le crédit
Score 41-70  → Risque MOYEN   : crédit limité avec suivi
Score 71-100 → Risque FAIBLE  : crédit accordé normalement
```

### 5.3 Features utilisées

| Feature | Description | Source |
|---|---|---|
| `nb_achats_credit_total` | Nombre de ventes à crédit | `sales (payment_type=CREDIT)` |
| `montant_moyen_achat` | Panier moyen crédit | `AVG(sales.total)` |
| `delai_moyen_remboursement_jours` | Délai moyen de remboursement | `customer_payments` (si REAL) ou simulation |
| `taux_retard` | % de paiements en retard (>30j) | `customer_payments` ou simulation déterministe |
| `anciennete_client_mois` | Ancienneté en mois | `(now - customer.created_at) / 30` |
| `frequence_achat_mensuelle` | Achats/mois | `nb_achats / ancienneté` |
| `solde_du_actuel` | Encours de crédit actuel | `customer.credit_balance` |
| `is_technicien` | Type TECHNICIEN (crédit privilégié) | `customer.customer_type` |

### 5.4 Double source de données

**Source REAL (prioritaire) :** si la table `fs_customer_credit_features` contient des données calculées par le pipeline ETL depuis les paiements réels (`customer_payments`), elles sont utilisées en priorité.

**Source SIMULATED (repli) :** en l'absence de données réelles de paiement (`CustomerPayment`), le module utilise le proxy `credit_balance` du modèle `Customer` comme estimateur du solde dû. Source tracée `FeatureDataSource.SIMULATED`. Le fallback SHA-256 déterministe a été supprimé (cf. module 0.1 — corrections pré-soutenance).
- Même customer_id → même score (reproductible)
- Distribution réaliste : `taux_retard ~ Beta(2, 5)` (~15% de retards en moyenne)
- La source est tracée dans `payload_json.data_source`

### 5.5 Algorithmes ML

**Mode ML (≥ 20 clients avec crédit, scikit-learn disponible) :**

```python
# Random Forest (modèle principal)
rf = RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42)
# Logistic Regression (comparatif)
logreg = LogisticRegression(max_iter=1000)

# Validation croisée stratifiée (minimum 2-5 folds selon données)
skf = StratifiedKFold(n_splits=min(5, min_class_count))
rf_acc = cross_val_score(rf, X, y, cv=skf, scoring="accuracy").mean()
logreg_acc = cross_val_score(logreg, X, y, cv=skf, scoring="accuracy").mean()

# Score final = proba de la classe "bon_payeur" × 100
scores = rf.predict_proba(X)[:, 1] * 100
```

**Mode règles (repli) :**

```python
score = (1 - taux_retard) × 70
       + clip(1 - delai_moyen / 90, 0, 1) × 20
       + clip(frequence_achat_mensuelle, 0, 1) × 10
```

### 5.6 Métriques trackées

| Métrique | Description |
|---|---|
| `n_customers` | Nombre de clients analysés |
| `n_bon_payeur` | Nombre de clients classés bons payeurs |
| `random_forest_cv_accuracy` | Précision RF en cross-validation |
| `logistic_regression_cv_accuracy` | Précision LogReg en cross-validation |
| `cv_folds` | Nombre de folds utilisés |
| `n_data_source_real` | Clients avec données de remboursement réelles |
| `n_data_source_simulated` | Clients avec données simulées |

### 5.7 Sortie API

`GET /api/v1/analytics/credit-scores?risk_level=ELEVE`

```json
{
  "items": [
    {
      "customer_id": "uuid",
      "customer_name": "Moussa Traoré",
      "score": 28.5,
      "risk_level": "ELEVE",
      "nb_achats_credit_total": 8,
      "montant_moyen_achat": 45000.0,
      "delai_moyen_remboursement_jours": 52.3,
      "taux_retard": 0.625,
      "anciennete_client_mois": 7.2,
      "frequence_achat_mensuelle": 1.11,
      "solde_du_actuel": 125000.0,
      "data_source": "SIMULATED"
    }
  ]
}
```

**Intégration tableau de bord :** les clients à risque ÉLEVÉ génèrent une alerte `CREDIT_RISK` dans le widget "Alertes IA" du dashboard.

### 5.8 Impact métier

- Réduction des impayés : décision de crédit basée sur données, pas sur relation
- Segmentation du risque : traitement différencié (plafond de crédit modulé)
- Historique : chaque entraînement est versionné → traçabilité en cas de litige
- Base pour un système de fidélité : bons payeurs = avantages commerciaux

---

## 6. Module 4 — Segmentation client RFM

### 6.1 Besoin métier

Tous les clients ne se ressemblent pas. Cibler une action commerciale (relance, promotion, récompense) sans segmentation revient à envoyer la même communication à tout le monde → taux de conversion faible, coût élevé. RFM permet de **segmenter automatiquement** les clients selon leur comportement d'achat réel.

### 6.2 Dimensions RFM

| Dimension | Définition | Calcul |
|---|---|---|
| **R — Récence** | Depuis combien de jours le client a acheté | `(now - MAX(sale.created_at)).days` |
| **F — Fréquence** | Nombre d'achats sur la période | `COUNT(sales)` |
| **M — Montant** | CA total généré | `SUM(sale_lines.line_total)` |

**Période d'analyse :** 12 mois glissants (configurable)

### 6.3 Segments définis

| Segment | Signification | Critère (clustering) | Action recommandée |
|---|---|---|---|
| `CHAMPIONS` | Clients récents, fréquents, gros acheteurs | Faible R, fort F et M | Programme de fidélité, crédit étendu |
| `REGULIERS` | Clients récents mais dépenses modérées | Faible R, faible M | Relances ciblées, upselling |
| `A_RISQUE` | Clients anciens qui ont cessé d'acheter | Fort R, fort M historique | Campagne de réactivation |
| `OCCASIONNELS` | Clients rares et faibles dépenses | Fort R, faible M | Communication standard |

### 6.4 Algorithme K-Means (mode ML)

```python
# Normalisation des features (obligatoire pour K-Means)
X_scaled = StandardScaler().fit_transform(df[["recency", "frequency", "monetary"]])

# K-Means avec 4 clusters, 10 initialisations (k-means++ par défaut)
kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
df["cluster"] = kmeans.fit_predict(X_scaled)

# Attribution des labels sémantiques :
# tri des centres par score = F + M - R (Champions = fort score)
centers["score"] = centers["frequency"] + centers["monetary"] - centers["recency"]
ranking = centers["score"].sort_values(ascending=False).index
cluster_to_label = {cluster: label for cluster, label in zip(ranking, LABELS)}
```

**Repli (K-Means indisponible ou < 4 clients) :** segmentation par médiane de R et de FM — déterministe, pas de ML.

### 6.5 Double source de données

**Feature Store (priorité) :** table `fs_customer_rfm` calculée par le pipeline ETL.

**Calcul direct (repli) :** requête directe sur `sales ⋈ sale_lines` — plus lent mais toujours disponible.

### 6.6 Sortie API

`GET /api/v1/analytics/rfm-segments?segment=CHAMPIONS`

```json
{
  "items": [
    {
      "customer_id": "uuid",
      "customer_name": "Fatimata Ouédraogo",
      "recency_days": 3,
      "frequency": 24,
      "monetary": 850000.0,
      "segment": "CHAMPIONS",
      "segment_label": "Champions",
      "recommended_action": "Programme de fidelite, credit etendu"
    }
  ]
}
```

**Intégration dashboard :** les 8 premiers segments RFM s'affichent dans un tableau récapitulatif de la page d'accueil (section "Segmentation client").

### 6.7 Impact métier

- Personnalisation des relances commerciales → meilleur taux de retour
- Identification des clients à risque de départ (`A_RISQUE`) → action préventive
- Base objective pour les décisions de fidélisation
- Argument concurrentiel : segmentation automatique sans Excel

---

## 7. Module 5 — Détection d'anomalies sur les ventes

### 7.1 Besoin métier

Dans le secteur du commerce informel, la fraude et les erreurs de saisie sont fréquentes :
- Remises excessives accordées sans autorisation (rabais familial non autorisé)
- Ventes à des prix anormalement bas (complicité client-vendeur)
- Ventes hors horaires habituels (fraude nocturne)
- Montants très éloignés de la moyenne (erreur de saisie ×10)

**Objectif :** signaler automatiquement les ventes statistiquement anormales pour l'audit de l'administrateur.

### 7.2 Features d'anomalie

| Feature | Description | Calcul |
|---|---|---|
| `montant_total` | Montant total de la vente | `sale.total` |
| `remise_taux` | Taux de remise (%) | `sale.discount_rate` |
| `heure_vente` | Heure de la vente (0-23) | `sale.created_at.hour` |
| `ecart_vs_moyenne_produit` | Écart du montant à la moyenne produit | `(montant - μ_produit) / μ_produit` |
| `ecart_vs_moyenne_vendeur` | Écart du montant à la moyenne vendeur | `(montant - μ_vendeur) / μ_vendeur` |

### 7.3 Algorithme Isolation Forest

```python
from sklearn.ensemble import IsolationForest

# contamination = proportion attendue d'anomalies (config: 2%)
model = IsolationForest(
    n_estimators=200,
    contamination=contamination,  # ANOMALY_CONTAMINATION config (default 0.02)
    random_state=42
)
model.fit(X)  # X = matrix des 5 features

# score de décision : plus le score est négatif, plus la vente est anormale
scores = model.decision_function(X)
threshold = np.quantile(scores, contamination)
is_anomaly = scores < threshold
```

**Pourquoi Isolation Forest ?**
- Pas besoin de données labellisées (non-supervisé)
- Efficace en haute dimension
- Rapide sur des datasets de taille moyenne (< 100k ventes)
- Interprétable via les "raisons" calculées a posteriori

**Repli Z-score :** si scikit-learn absent, anomalie = montant à plus de 3 écarts-types de la moyenne (règle statistique classique).

### 7.4 Règles de qualification des raisons

Après la détection, des raisons lisibles sont calculées pour chaque anomalie :

```python
if remise_taux >= 15:     → "Remise élevée"
if ecart_produit > 1.0:   → "Montant largement supérieur à la moyenne du produit"
if ecart_vendeur > 1.0:   → "Montant largement supérieur à la moyenne du vendeur"
if heure < 6 or heure > 21: → "Vente hors horaires habituels"
# Si aucune règle : "Profil statistique atypique"
```

### 7.5 Paramètres configurables

| Paramètre | Valeur par défaut | Variable d'environnement |
|---|---|---|
| Fenêtre d'analyse | 90 jours | `days` (arg `train()`) |
| Taux de contamination | 2% | `ANOMALY_CONTAMINATION` |

### 7.6 Sortie API

`GET /api/v1/analytics/anomalies?branch_id=uuid`

```json
{
  "items": [
    {
      "entity_id": "sale-uuid",
      "reference": "VTE-2024-001234",
      "branch_id": "uuid",
      "cashier_name": "Idrissa Kaboré",
      "montant_total": 520000.0,
      "remise_taux": 25,
      "score": -0.1823,
      "reasons": ["Remise élevée", "Montant largement supérieur à la moyenne du vendeur"]
    }
  ]
}
```

**Intégration dashboard :** les anomalies récentes génèrent des alertes `ANOMALIE` de severity `WARNING` dans le tableau de bord temps réel.

### 7.7 Impact métier

- Réduction de la fraude interne (dissuasion + détection)
- Audit facilité : l'admin ne parcourt pas toutes les ventes, il traite les signalements
- Confiance accrue dans les données → décisions plus fiables
- Base pour un futur module de contrôle interne

---

## 8. Module 6 — Analyse de cohortes clients

### 8.1 Besoin métier

Une question fondamentale pour tout commerçant : "Les clients que j'ai acquis le mois dernier, sont-ils fidèles ?" ou "Quelle proportion de mes clients de janvier sont encore actifs en juin ?"

L'analyse de cohortes répond à ces questions en groupant les clients par **mois d'acquisition** (premier achat) et en traçant leur **taux de rétention** mois après mois.

### 8.2 Définitions

**Cohorte :** groupe de clients ayant effectué leur premier achat le même mois (ex. "Cohorte Janvier 2024").

**Rétention M+N :** % de clients de la cohorte ayant **racheté** au moins une fois au N-ième mois après leur premier achat.

```
Rétention M+0 = 100% (par définition : tous ont acheté ce mois)
Rétention M+1 = % ayant acheté le mois suivant
Rétention M+3 = % encore actifs 3 mois après
...
Rétention M+12 = % encore actifs 12 mois après
```

### 8.3 Implémentation

**Fichier :** `backend/app/blueprints/analytics/routes.py` — endpoint `GET /analytics/cohorts`

```python
# 1. Charger toutes les ventes (customer_id, created_at) de la période
sales = Sale.query.filter(Sale.status == "VALIDEE", Sale.customer_id != None).all()

# 2. Calculer le premier achat de chaque client → définit sa cohorte
first_purchase[cid] = min(months of purchases for cid)

# 3. Index des mois d'achat par client
customer_months[cid] = set(months where cid bought)

# 4. Pour chaque cohorte et chaque delta (M+0 à M+12) :
target_month = cohort_month + delta  # arithmetic modulo 12
count = |{cid ∈ cohort : target_month ∈ customer_months[cid]}|
rate = count / size * 100
```

### 8.4 Calcul du mois cible

```python
# Arithmétique calendaire robuste (pas de modulo 12 naïf)
target_total = cy * 12 + cm - 1 + delta   # cy = cohort year, cm = cohort month (1-12)
ty, tm = divmod(target_total, 12)
tm += 1    # résultat : année ty, mois tm (1-12)
target_mois = f"{ty:04d}-{tm:02d}"
```

### 8.5 Paramètres

| Paramètre | Valeur par défaut | Max |
|---|---|---|
| `months` | 12 | 24 |

### 8.6 Sortie API

`GET /api/v1/analytics/cohorts?months=12`

```json
{
  "cohorts": [
    {
      "cohort": "2024-01",
      "size": 45,
      "retention": [
        {"month": 0, "month_label": "2024-01", "count": 45, "rate": 100.0},
        {"month": 1, "month_label": "2024-02", "count": 28, "rate": 62.2},
        {"month": 2, "month_label": "2024-03", "count": 19, "rate": 42.2},
        {"month": 3, "month_label": "2024-04", "count": 14, "rate": 31.1}
      ]
    }
  ],
  "max_months": 11
}
```

### 8.7 Visualisation frontend

**Heatmap de rétention :** tableau où chaque cellule (cohorte × M+N) est colorée :
- `indigo` : M+0 (100%)
- `vert` : taux ≥ 50%
- `ambre` : taux ≥ 20%
- `rouge` : taux < 20%

**BarChart comparatif :** Rétention M+1 et M+3 par cohorte (permet de comparer les classes d'acquisition).

**KPIs synthétiques :**
- Nombre de cohortes analysées
- Nombre total de clients analysés
- Rétention M+1 moyenne sur toutes les cohortes

### 8.8 Impact métier

- Mesurer l'efficacité des actions de fidélisation dans le temps
- Identifier les mois où la rétention chute → analyser les causes (concurrent ? saisonnalité ?)
- Comparer les cohortes issues de différentes périodes d'acquisition
- Base pour calculer le CLV de façon précise

---

## 9. Module 7 — Customer Lifetime Value (CLV)

### 9.1 Besoin métier

Combien rapporte un client à GesCom-BF **sur toute sa durée de vie** ? Cette question est cruciale pour :
- Justifier le coût d'acquisition d'un client (combien investir en prospection ?)
- Identifier les clients à haute valeur → traitement VIP
- Prioriser les actions de rétention (conserver un client CLV 500k FCFA avant un client CLV 50k)

### 9.2 Formule CLV

```
CLV = panier_moyen × fréquence_mensuelle × durée_vie_estimée_mois
```

| Composante | Calcul |
|---|---|
| `panier_moyen` | `ca_total / nb_commandes` |
| `fréquence_mensuelle` | `nb_commandes / durée_en_mois` (durée = premier à dernier achat) |
| `durée_vie_estimée_mois` | `max(24, durée_observée × 2)` — minimum 24 mois |

**Justification du `× 2` :** on estime que le client restera actif au moins aussi longtemps que la période déjà observée. Le minimum de 24 mois représente la durée de vie minimale réaliste pour un client ayant effectué au moins un achat.

**Exemple :**
```
Client ayant acheté 12 fois sur 6 mois pour 600 000 FCFA total :
- panier_moyen = 50 000 FCFA
- fréquence = 12 / 6 = 2 achats/mois
- durée_vie_estimée = max(24, 6×2) = 24 mois
- CLV = 50 000 × 2 × 24 = 2 400 000 FCFA
```

### 9.3 Implémentation

**Fichier :** `backend/app/blueprints/analytics/routes.py` — endpoint `GET /analytics/clv`

```python
rows = db.session.query(
    Sale.customer_id,
    func.count(Sale.id).label("nb_commandes"),
    func.sum(Sale.total).label("ca_total"),
    func.min(Sale.created_at).label("premier_achat"),
    func.max(Sale.created_at).label("dernier_achat"),
).filter(Sale.status == "VALIDEE", Sale.customer_id != None)
 .group_by(Sale.customer_id)
 .all()
```

### 9.4 Paramètres

| Paramètre | Valeur par défaut | Max | Description |
|---|---|---|---|
| `limit` | 50 | 200 | Nombre de clients retournés (triés par CLV décroissant) |
| `min_clv` | 0 | — | Filtre : CLV minimum pour apparaître |

### 9.5 Statistiques agrégées

L'endpoint retourne également des statistiques globales sur l'ensemble des CLV calculées :

```json
{
  "stats": {
    "clv_moyen": 1250000.0,
    "clv_median": 820000.0,
    "clv_max": 8500000.0,
    "clv_min": 12000.0
  }
}
```

### 9.6 Visualisation frontend

- **4 KPI cards** : clients analysés, CLV moyenne, CLV médiane, CLV max
- **BarChart horizontal** : Top 10 clients par CLV (avec nom)
- **Tableau complet** : tous les clients avec CLV estimée en indigo, triés par CLV décroissant

### 9.7 Limites et améliorations futures

**Limites actuelles :**
- CLV basée sur données historiques uniquement (pas de modélisation probabiliste)
- Ne prend pas en compte la marge (utilise le CA, pas le profit)
- Durée de vie estimée = heuristique simple (×2)

**Améliorations possibles :**
- Modèle Pareto/NBD pour prédire la probabilité d'achat futur
- Intégration de la marge produit pour un CLV "profit"
- Segmentation CLV × RFM pour une vision complète

---

## 10. Module 8 — Tableau de bord décisionnel temps réel

### 10.1 Architecture SSE / Polling

Le tableau de bord temps réel utilise **Server-Sent Events (SSE)** avec repli automatique sur polling toutes les 15 secondes.

**Pourquoi SSE et pas WebSocket ?**
- WebSocket nécessite un serveur stateful (Redis + Channels) → complexité
- SSE est unidirectionnel (serveur → client) et suffisant pour un dashboard
- SSE fonctionne sur HTTP/1.1 standard → compatible PythonAnywhere
- Le JWT Bearer Token peut être envoyé dans les headers HTTP (pas possible avec EventSource standard → implémentation fetch() personnalisée)

**Mode PythonAnywhere (DISABLE_SSE=true) :** le serveur envoie un seul snapshot puis ferme la connexion → le frontend bascule automatiquement sur polling pur.

### 10.2 Contenu du snapshot temps réel

`GET /api/v1/reports/dashboard/realtime`

```json
{
  "generated_at": "2024-06-15T14:32:00",
  "kpis": {
    "ca_jour": "2450000",
    "ca_mois": "48200000",
    "marge_pct": 18.5,
    "panier_moyen": "145000"
  },
  "alerts": [
    {
      "type": "RUPTURE_STOCK",
      "severity": "CRITICAL",
      "message": "Rupture prévue : Ciment 50kg (stock 5, qté recommandée 180)",
      "entity_id": "product-uuid"
    },
    {
      "type": "ANOMALIE",
      "severity": "WARNING",
      "message": "Vente atypique VTE-001234 : Remise élevée",
      "entity_id": "sale-uuid"
    },
    {
      "type": "CREDIT_RISK",
      "severity": "WARNING",
      "message": "Client à risque : Moussa Traoré (score 28)",
      "entity_id": "customer-uuid"
    }
  ],
  "abc_xyz": [...],        // dernières prédictions ABC/XYZ
  "rfm_segments": [...]    // derniers segments RFM
}
```

### 10.3 Calcul des KPIs temps réel

**Fichier :** `backend/app/services/analytics_service.py` — `compute_dashboard_realtime()`

```python
# CA jour : SUM(sales.total) WHERE status=VALIDEE AND created_at >= aujourd'hui 00:00
# CA mois : SUM(sales.total) WHERE created_at >= 1er du mois
# Marge % : (CA - coût) / CA × 100
#   coût = SUM(sale_lines.quantity × products.purchase_price)
# Panier moyen : CA_jour / nb_ventes_jour
```

### 10.4 Connexion frontend (useDashboardStream)

```typescript
// hooks/useDashboardStream.ts
// 1. Chargement initial : GET /reports/dashboard/realtime → snapshot immédiat
// 2. Connexion SSE via fetch() (pas EventSource) → header Authorization Bearer
// 3. Si sse-disabled reçu → basculer sur polling 15s
// 4. Si erreur → reconnexion après 5s
// 5. Protection React 18 Strict Mode : variable `isActive` de closure (pas useRef)
```

---

## 11. Module 9 — Comparatif inter-succursales

### 11.1 Besoin métier

Un propriétaire de plusieurs boutiques veut comparer objectivement leurs performances sans naviguer entre plusieurs tableaux de bord. Il veut savoir :
- Quelle succursale performe le mieux en CA ? en marge ? en clients actifs ?
- Quelle boutique a le meilleur panier moyen ?
- Comment évoluent les CA respectifs mois par mois ?

### 11.2 KPIs comparés par succursale

| KPI | Calcul |
|---|---|
| `ca` | `SUM(sales.total)` pour la période |
| `nb_ventes` | `COUNT(sales)` |
| `panier_moyen` | `ca / nb_ventes` |
| `marge_brute` | `ca - SUM(lines.quantity × product.purchase_price)` |
| `marge_pct` | `marge_brute / ca × 100` |
| `nb_clients_actifs` | `COUNT(DISTINCT customer_id)` sur la période |
| `top_product` | Produit le plus vendu (quantité) |

### 11.3 Normalisation Radar (0-100)

Pour permettre une comparaison visuelle sur un RadarChart, chaque métrique est normalisée de 0 à 100 par rapport au maximum observé entre toutes les succursales :

```python
for metric in ["ca", "nb_ventes", "panier_moyen", "marge_pct", "nb_clients_actifs"]:
    maxima = max(k[metric] for k in kpis) or 1
    for branch_kpi in kpis:
        radar_score = round(branch_kpi[metric] / maxima * 100, 1)
```

La succursale avec le maximum dans chaque métrique obtient un score de 100. Les autres sont positionnées relativement.

### 11.4 Évolution mensuelle

Le CA mensuel par succursale est agrégé via `func.date_format(Sale.created_at, "%Y-%m")` et retourné dans un format compatible BarChart Recharts :

```json
{
  "evolution": [
    {"mois": "2024-01", "Boutique Centre": 12500000, "Boutique Nord": 8200000},
    {"mois": "2024-02", "Boutique Centre": 13100000, "Boutique Nord": 9400000}
  ]
}
```

### 11.5 Visualisation frontend (BranchComparePage)

- **Cards KPI** par succursale, color-codées avec une couleur distinctive par boutique
- **RadarChart** (Recharts) : 5 axes (CA, Nb ventes, Panier moyen, Marge %, Clients actifs) — une ligne par succursale
- **BarChart CA/Marge** côte à côte par succursale
- **BarChart évolution mensuelle** — barres empilées/groupées par succursale
- **Tableau récapitulatif** avec marge_pct colorée : vert ≥ 20%, ambre ≥ 10%, rouge < 10%

---

## 12. Pipeline ETL et Feature Store

### 12.1 Rôle du pipeline ETL

Le pipeline ETL (`etl_service.py`) transforme les données opérationnelles brutes en **features optimisées** pour les modules ML. Sans ETL, chaque entraînement ML recalcule les mêmes agrégations depuis les données brutes (lent, redondant).

### 12.2 Étapes du pipeline

```
1. extract_and_clean(days=180)
   → Extraction sales + sale_lines sur 180 jours
   → Nettoyage : suppression lignes avec product_id/branch_id/quantity NULL
   → Rapport : n_raw, n_clean, n_dropped

2. validate_quality(dfs)
   → Vérification : quantité > 0, montant ≥ 0, pas de doublons
   → Si great_expectations disponible : validation étendue (profiling)
   → Lève EtlValidationError si qualité insuffisante → bloque les étapes suivantes

3. build_features(dfs)
   → fs_daily_sales : agrégation journalière (product, branch, date)
   → fs_customer_rfm : calcul Récence/Fréquence/Montant par client
   → fs_customer_credit_features : features crédit (avec données réelles si customer_payments)
   → fs_transaction_features : features anomalie par transaction
   → Upsert en base (replace si date/entity déjà présente)
```

### 12.3 Tables du Feature Store

| Table | Granularité | Mise à jour | Consommée par |
|---|---|---|---|
| `fs_daily_sales` | (produit, succursale, date) | Quotidienne | demand_forecast |
| `fs_customer_rfm` | (client) | Quotidienne | rfm_segmentation |
| `fs_customer_credit_features` | (client) | Quotidienne | credit_scoring |
| `fs_transaction_features` | (vente) | Quotidienne | anomaly_detection |

### 12.4 Gestion de la qualité des données

```python
class EtlValidationError(Exception):
    """Bloque le pipeline si qualité insuffisante"""

# Vérifications :
assert df["quantity"] > 0  # pas de ventes négatives
assert df["line_total"] >= 0  # pas de montants négatifs
assert no_duplicates(df, key=["sale_id", "product_id"])
# Si great_expectations disponible : profiling statistique étendu
```

### 12.5 Source réelle vs simulée pour le crédit

La donnée `taux_retard` (taux de retard de remboursement) est la feature la plus critique du scoring crédit. Deux sources :

**Source REAL :** calculée depuis `customer_payments` si le client a ≥ 3 paiements enregistrés. `taux_retard = count(payments where paid_date - due_date > 30) / total_payments`.

**Source SIMULATED :** si historique insuffisant (`CustomerPayment`), le proxy `Customer.credit_balance` est utilisé. Source tracée `FeatureDataSource.SIMULATED`. Le fallback SHA-256 déterministe a été supprimé car il ne constituait pas de la vraie IA.

---

## 13. Registre des modèles et traçabilité

### 13.1 Table `ml_models`

Chaque entraînement crée une entrée dans `ml_models` :

```sql
CREATE TABLE ml_models (
  id            UUID PRIMARY KEY,
  model_type    VARCHAR(32) NOT NULL,  -- 'DEMAND_FORECAST', 'CREDIT_SCORING', etc.
  version       VARCHAR(64) NOT NULL,  -- 'demand_forecast_20240615_143200'
  algorithm     VARCHAR(64) NOT NULL,  -- 'RANDOM_FOREST+LOGISTIC_REGRESSION_CV'
  metrics_json  JSON,                  -- métriques de performance
  artifact_path VARCHAR(500),          -- chemin .joblib (si sauvegardé)
  mlflow_run_id VARCHAR(64),           -- ID run MLflow (si disponible)
  trained_at    DATETIME NOT NULL,
  is_active     BOOLEAN NOT NULL DEFAULT TRUE
);
```

**Versionnage :** le format `{model_type}_{YYYYMMDD}_{HHMMSS}` garantit l'unicité. Lors d'un ré-entraînement, le modèle précédent est marqué `is_active=False`.

### 13.2 Table `predictions`

Chaque prédiction individuelle est liée à son modèle :

```sql
CREATE TABLE predictions (
  id              UUID PRIMARY KEY,
  model_id        UUID FK → ml_models.id,
  prediction_type VARCHAR(32),  -- 'DEMAND_FORECAST', 'CREDIT_SCORE', etc.
  entity_type     VARCHAR(32),  -- 'product', 'customer', 'sale'
  entity_id       UUID,         -- ID du produit, client ou vente
  payload_json    JSON,         -- toutes les valeurs prédites
  created_at      DATETIME
);
```

### 13.3 Types de prédictions

| `prediction_type` | `entity_type` | Contenu `payload_json` |
|---|---|---|
| `DEMAND_FORECAST` | `product` | forecast_7d, forecast_30d, alerte_rupture, quantite_recommandee |
| `CREDIT_SCORE` | `customer` | score, risk_level, features détaillées |
| `ANOMALY` | `sale` | score IF, reasons, montant, remise |
| `ABC_XYZ` | `product` | abc_class, xyz_class, cv, revenue |
| `RFM_SEGMENT` | `customer` | segment, recency, frequency, monetary |

### 13.4 API registre

`GET /api/v1/analytics/ml/models`

```json
{
  "items": [
    {
      "id": "uuid",
      "model_type": "CREDIT_SCORING",
      "version": "credit_scoring_20240615_143200",
      "algorithm": "RANDOM_FOREST+LOGISTIC_REGRESSION_CV",
      "metrics": {
        "n_customers": 142.0,
        "random_forest_cv_accuracy": 0.8732,
        "logistic_regression_cv_accuracy": 0.8541
      },
      "mlflow_run_id": "abc123def456",
      "trained_at": "2024-06-15T14:32:00",
      "is_active": true
    }
  ]
}
```

---

## 14. Intégration MLflow

### 14.1 Rôle de MLflow

MLflow est un outil open-source de suivi d'expériences ML (paramètres, métriques, artefacts). Dans GesCom-BF, il est **optionnel** :
- Si `mlflow` est installé → chaque entraînement est loggé dans MLflow (paramètres, métriques, run_id)
- Si `mlflow` est absent → le système fonctionne normalement, seuls `ml_models` et `predictions` sont utilisés

### 14.2 Configuration

```python
# .env ou config.py
MLFLOW_TRACKING_URI = "file:./mlruns"           # local (défaut)
# ou
MLFLOW_TRACKING_URI = "http://mlflow-server:5000"  # serveur distant
MLFLOW_EXPERIMENT_NAME = "gescom-bf"
```

### 14.3 Classe MLflowRun (no-op si absent)

```python
class MLflowRun:
    """Context manager no-op si MLflow est indisponible."""
    def __enter__(self): → démarrer mlflow.start_run() ou no-op
    def log_params(params): → mlflow.log_params() ou no-op
    def log_metrics(metrics): → mlflow.log_metrics() ou no-op
    def __exit__: → mlflow.end_run() ou no-op
```

### 14.4 Informations trackées par module

| Module | Params loggés | Métriques loggées |
|---|---|---|
| Prévision demande | months, safety_margin | n_series, n_alerts |
| Scoring crédit | — | n_customers, rf_accuracy, logreg_accuracy, cv_folds |
| Anomalies | days, contamination | n_sales, n_anomalies, anomaly_rate |
| ABC/XYZ | months | n_products, n_class_a/b/c |
| RFM | months, n_clusters | n_customers, n_champions/réguliers/etc. |

---

## 15. Tâches Celery et automatisation

### 15.1 Architecture Celery

Celery est un système de file de tâches distribuées. Il permet d'exécuter les entraînements ML **en arrière-plan** sans bloquer l'API Flask.

```
Flask API ──POST /ml/train/DEMAND_FORECAST──► Celery Worker
                                                    │
                                              train_demand_forecast_task()
                                                    │
                                              demand_forecast.train()
                                                    │
                                              register_model() + record_predictions()
```

**Broker par défaut :** Redis. **Repli :** exécution synchrone si Redis/Celery indisponible.

### 15.2 Tâches définies

| Tâche Celery | Modèle | Fréquence recommandée |
|---|---|---|
| `train_demand_forecast_task(months=6)` | Prévision demande | Hebdomadaire |
| `train_credit_scoring_task()` | Scoring crédit | Hebdomadaire |
| `detect_anomalies_task(days=90)` | Détection anomalies | Quotidienne |
| `compute_abc_xyz_task(months=6)` | ABC/XYZ | Hebdomadaire |
| `compute_rfm_segments_task(months=12, n_clusters=4)` | Segmentation RFM | Mensuelle |

### 15.3 Déclenchement manuel via API

`POST /api/v1/analytics/ml/train/DEMAND_FORECAST`

ou avec corps JSON :

`POST /api/v1/analytics/ml/train` + `{"model_type": "CREDIT_SCORING"}`

```json
// Réponse
{
  "model_id": "uuid",
  "version": "demand_forecast_20240615_143200",
  "metrics": {"n_series": 48, "n_alerts": 3},
  "n_series": 48,
  "n_alerts": 3
}
```

**Permission requise :** `ml:train` (rôle ADMIN uniquement)

### 15.4 TRAIN_FUNCTIONS (mapping)

```python
TRAIN_FUNCTIONS = {
    "DEMAND_FORECAST": train_demand_forecast_task,
    "CREDIT_SCORING": train_credit_scoring_task,
    "ANOMALY_DETECTION": detect_anomalies_task,
    "ABC_XYZ": compute_abc_xyz_task,
    # "RFM_SEGMENTATION" : non inclus dans TRAIN_FUNCTIONS (déclenché via schedule)
}
```

---

## 16. API REST — Endpoints analytiques

### 16.1 Blueprint `analytics` (`/api/v1/analytics/`)

| Méthode | Endpoint | Permission | Description |
|---|---|---|---|
| GET | `/sales-trend` | `analytics:read` | Tendance ventes jour/jour (RF-24) |
| GET | `/dashboard` | `analytics:read` | Dashboard étendu multi-sites (RF-24) |
| GET | `/forecast` | `analytics:read` | Prévisions demande + alertes rupture (RF-25) |
| GET | `/forecast/{product_id}/{branch_id}` | `analytics:read` | Prévision détaillée produit/site |
| GET | `/credit-scores` | `analytics:read` | Scoring crédit clients (RF-27) |
| GET | `/anomalies` | `analytics:read` | Ventes anomales (RF-28) |
| GET | `/abc-xyz` | `analytics:read` | Classification ABC/XYZ (RF-26) |
| GET | `/rfm-segments` | `analytics:read` | Segmentation RFM (RF-26) |
| GET | `/ml/models` | `analytics:read` | Registre des modèles (RNF-17) |
| POST | `/ml/train/<type>` | `ml:train` | Déclenchement entraînement (RF-29) |
| POST | `/ml/train` | `ml:train` | Déclenchement via body JSON |
| GET | `/cohorts` | `analytics:read` | Analyse de cohortes (Feature E) |
| GET | `/clv` | `analytics:read` | Customer Lifetime Value (Feature F) |

### 16.2 Blueprint `reports` (`/api/v1/reports/`)

| Méthode | Endpoint | Permission | Description |
|---|---|---|---|
| GET | `/dashboard` | `reports:read` | Indicateurs du jour (RF-23) |
| GET | `/dashboard/realtime` | `reports:read` | Snapshot temps réel |
| GET | `/dashboard/stream` | `reports:read` | Flux SSE temps réel |
| GET | `/vendeur/dashboard` | `reports:read` | Performance individuelle vendeur |
| GET | `/branches/compare` | `reports:read` | Comparatif inter-succursales (Feature C) |
| GET | `/compta/summary` | `reports:read` | Journal de caisse |
| GET | `/export` | `reports:read` | Export PDF dashboard |
| GET | `/export/sales` | `reports:read` | Export Excel ventes |
| GET | `/export/stock` | `reports:read` | Export Excel stock |

### 16.3 Paramètres communs

| Paramètre | Type | Présent dans | Description |
|---|---|---|---|
| `branch_id` | UUID | Tous | Filtrer par succursale |
| `days` | int | forecast, trend, dashboard | Fenêtre temporelle (défaut 30) |
| `alerts_only` | bool | forecast | N'afficher que les alertes rupture |
| `risk_level` | string | credit-scores | Filtrer par niveau (ELEVE/MOYEN/FAIBLE) |
| `abc_class` | A/B/C | abc-xyz | Filtrer par classe ABC |
| `months` | int | cohorts, CLV base | Fenêtre en mois |
| `limit` | int | clv | Nombre max de résultats |
| `min_clv` | float | clv | CLV minimum pour filtrer |
| `date_debut` | YYYY-MM-DD | branches/compare | Début de période |
| `date_fin` | YYYY-MM-DD | branches/compare | Fin de période |

---

## 17. Frontend — AnalyticsPage et visualisations

### 17.1 Structure de la page analytique

`/analytique` → `AnalyticsPage.tsx` (1371 lignes)

Onglets disponibles :

| Onglet | ID | Contenu principal |
|---|---|---|
| Vue d'ensemble | `overview` | Tendance CA, top produits, KPIs |
| Prévisions demande | `forecast` | Tableau alertes rupture |
| Scoring crédit | `credit` | Tableau clients avec score coloré |
| Anomalies | `anomalies` | Tableau ventes signalées |
| ABC/XYZ | `abc-xyz` | Tableau classification + BarChart |
| Segmentation RFM | `rfm` | Tableau segments + BarChart |
| Modèles ML | `ml` | Registre des modèles entraînés |
| Cohortes clients | `cohorts` | Heatmap rétention + BarChart |
| Valeur vie client | `clv` | Top 10 BarChart + tableau complet |

### 17.2 Bibliothèques de visualisation

**Recharts** (bibliothèque React officielle) :

| Composant Recharts | Utilisé pour |
|---|---|
| `AreaChart` | Tendance ventes (courbe avec remplissage) |
| `BarChart` | ABC/XYZ, Top produits, RFM, CLV, évolution CA |
| `RadarChart` | Comparatif inter-succursales (5 axes normalisés) |
| `PieChart` | Répartition par segment |
| `LineChart` | Cohortes (courbes de rétention) |

### 17.3 Chargement lazy (React Query)

Chaque onglet charge ses données **uniquement quand il est sélectionné** :

```typescript
const cohortsQuery = useQuery({
  queryKey: ["analytics", "cohorts", { months }],
  queryFn: () => analyticsApi.cohorts({ months }),
  enabled: tab === "cohorts",     // ← chargement uniquement si onglet actif
  staleTime: 300_000,             // données fraîches 5 minutes
});
```

### 17.4 Codage couleur standardisé

| Valeur | Couleur | Usage |
|---|---|---|
| Classe A / Champions / Risque FAIBLE | Vert `green-*` | Performance élevée |
| Classe B / Réguliers / Risque MOYEN | Ambre `amber-*` | Performance moyenne |
| Classe C / A risque / Risque ÉLEVÉ | Rouge `red-*` | Attention requise |
| M+0 cohortes | Indigo | Valeur de référence 100% |
| CLV estimée | Indigo `indigo-700` | Valeur calculée |
| Marge ≥ 20% | Vert | Bonne marge |
| Marge ≥ 10% | Ambre | Marge acceptable |
| Marge < 10% | Rouge | Marge insuffisante |

---

## 18. Exigences, contraintes et décisions techniques

### 18.1 Contraintes de déploiement

**PythonAnywhere (environnement de production initial) :**

| Contrainte | Impact | Solution |
|---|---|---|
| Pas de Redis | Celery ne fonctionne pas | Entraînement synchrone via API |
| Worker WSGI mono-thread | SSE coupe la connexion après 1 réponse | `DISABLE_SSE=true` → polling |
| MySQL (pas PostgreSQL) | `func.date_format()` au lieu de `func.date_trunc()` | Requêtes adaptées |
| Mémoire limitée (~512 MB) | Gros modèles ML impossibles | Prophet/XGBoost optionnels, repli sklearn |
| Pas de GPU | Deep Learning exclu | Algorithmes classiques uniquement |

**Docker (développement local) :**
- PostgreSQL + Redis disponibles
- Celery workers actifs
- MLflow local (`file:./mlruns`)
- Toutes les dépendances ML disponibles

### 18.2 Dépendances ML — optionnelles par design

```python
try:
    from sklearn.ensemble import RandomForestClassifier
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
```

**Toutes les dépendances ML sont importées avec try/except.** Si non disponibles, le repli est automatique. Cela permet de déployer sur un environnement minimal sans erreur d'import.

### 18.3 Décisions techniques clés

| Décision | Alternatives rejetées | Raison du choix |
|---|---|---|
| Stockage prédictions en base (table `predictions`) | Fichiers JSON, cache Redis | Persistance, requêtabilité, traçabilité |
| Feature Store en tables SQL | Pandas en mémoire | Partage entre modules, audit, rechargement sans recalcul |
| Repli algorithmique par niveau | Erreur si dépendance absente | Déploiement minimal fonctionnel |
| SSE pour temps réel | WebSocket | Unidirectionnel suffisant, pas de Redis requis |
| K-Means avec 4 clusters fixés | DBSCAN, clustering hiérarchique | Segments métier prédéfinis (Champions, etc.) |
| CLV heuristique (×2) | Pareto/NBD | Simplicité, données insuffisantes pour calibration |
| Données réelles CustomerPayment | Proxy credit_balance si historique absent | Traçabilité FeatureDataSource.REAL/SIMULATED |

### 18.4 Sécurité et permissions

| Endpoint | Permission RBAC | Rôles autorisés |
|---|---|---|
| `GET /analytics/*` | `analytics:read` | ADMIN uniquement |
| `POST /ml/train` | `ml:train` | ADMIN uniquement |
| `GET /reports/branches/compare` | `reports:read` | ADMIN uniquement |
| `GET /reports/dashboard/realtime` | `reports:read` | ADMIN, MAGASINIER |
| Cohortes, CLV | `analytics:read` | ADMIN uniquement |

---

## 19. Impacts métier et ROI attendu

### 19.1 Gains opérationnels directs

| Module | Gain estimé | Hypothèse |
|---|---|---|
| Prévision demande | -30% de ruptures de stock | Benchmark littérature PME retail |
| Scoring crédit | -20% d'impayés | Meilleure sélection des crédits accordés |
| Détection anomalies | -15% de fraude interne | Effet dissuasion + détection rapide |
| ABC/XYZ | -10% de surstock | Commandes calibrées sur les AX/BX |
| RFM | +8% de rétention client | Relances ciblées sur les A_RISQUE |
| CLV | Priorisation des VIP | Meilleure allocation des efforts commerciaux |

### 19.2 Valeur différenciante SaaS

La couche analytique justifie un **pricing premium** vis-à-vis des logiciels de caisse basiques :

- Les concurrents locaux (logiciels caisse simple) : 15 000 – 30 000 FCFA/mois
- GesCom-BF avec module IA : 50 000 – 80 000 FCFA/mois
- Valeur perçue : "l'IA paie sa propre facture" (réduction des impayés seule = plusieurs fois le prix de l'abonnement)

### 19.3 Argument de soutenabilité du mémoire

La couche analytique/IA permet de justifier l'option "Analyse de données" du mémoire par :
1. **Diversité des techniques** : ML supervisé, non-supervisé, séries temporelles, règles métier, analytique descriptive
2. **Intégration complète** : pipeline ETL → Feature Store → Modèles → API → Frontend
3. **Adaptation au contexte local** : données simulées déterministes, algorithmes légers pour PythonAnywhere
4. **Traçabilité complète** : registre de modèles, versionnage, MLflow optionnel

---

## 20. Limites actuelles et perspectives

### 20.1 État des modules après corrections pré-soutenance (juin 2026)

**✅ Corrections appliquées (12/12 modules) :**

| Module | Correction | Impact |
|---|---|---|
| 0.1 | SHA-256 supprimé → données réelles `CustomerPayment` | Scoring crédit 100% basé sur vraies données |
| 0.2 | Prophet activé + jours fériés BF | Prévisions saisonnières adaptées au contexte local |
| 0.3 | Flask-Limiter 3.8.0 | Protection brute-force `/login` et `/register` |
| 0.4 | Script cron `cron_train_all.py` | 6 modules entraînés automatiquement chaque nuit |
| 0.5 | Threading endpoint ML (app_context) | Entraînements manuels non bloquants (202 Accepted) |
| 1.1 | Silhouette + Elbow K optimal | K-Means scientifiquement justifié (k=2 à 8 évalués) |
| 1.2 | SHAP TreeExplainer | Scoring crédit explicable (LIME-like, niveau jury) |
| 1.3 | Churn probability | Décroissance exponentielle P=1-exp(-λ×R) |
| 1.4 | Anomaly reasons enrichies | +2 raisons : remise hors supervision, volume vendeur |
| 2.1 | Market Basket Analysis | Apriori + co-occurrence fallback |
| 2.2 | Price Elasticity | Log-log régression remise/quantité |
| 2.3 | African Context | Saisonnalité + stress trésorerie + crédit informel |

### 20.2 Limites résiduelles

**Données :**
- Prévision de demande : si Prophet non installé sur PythonAnywhere → LinearRegression (toujours meilleur que Seasonal Naive)

**Infrastructure :**
- Celery sans Redis → pas d'entraînement automatique planifié sur PythonAnywhere → entraînement manuel via API
- MLflow local (`file:./mlruns`) → pas d'UI MLflow accessible depuis le navigateur en production

**Algorithmes :**
- CLV basée sur heuristique simple (pas de Pareto/NBD probabiliste)
- Anomaly detection : pas de feedback humain (apprentissage actif) → le modèle ne s'améliore pas avec les corrections manuelles
- K-Means : pas de détermination automatique du nombre optimal de clusters (k=4 fixé)

### 20.2 Perspectives d'évolution

| Évolution | Impact | Complexité |
|---|---|---|
| Celery + Redis sur serveur dédié | Entraînements automatiques planifiés | Moyen |
| Pareto/NBD pour CLV probabiliste | CLV plus précise avec intervalles de confiance | Élevé |
| Prophet intégré PythonAnywhere | Prévisions saisonnières améliorées | Faible (config Python) |
| Feedback boucle anomalies | Réduction des faux positifs avec les corrections admin | Élevé |
| Deep Learning (LSTM) sur séries temporelles | Meilleure capture des patterns complexes | Très élevé |
| Recommandation produits | "Les clients qui achètent X achètent aussi Y" | Moyen |
| NLP sur noms produits | Recherche sémantique, déduplication catalogue | Moyen |
| Dashboard mobile PWA | Accès temps réel sur smartphone commerçant | Moyen |
| MLflow server mutualisé | Interface UI de suivi des expériences | Faible |
| A/B testing des modèles | Comparer deux algorithmes en production | Élevé |

---

## Annexe A — Dépendances Python ML

```txt
# Obligatoires (core)
flask==3.*
sqlalchemy>=2.0
pandas>=2.0
numpy>=1.24

# ML (optionnelles — repli automatique si absentes)
scikit-learn>=1.3       # Random Forest, IsolationForest, KMeans, LinearRegression
prophet>=1.1            # Prévision série temporelle
xgboost>=2.0            # Boosting pour résidus Prophet

# Tracking (optionnel)
mlflow>=2.0             # Suivi expériences

# Persistance artefacts (optionnel)
joblib>=1.3             # Sauvegarde modèles .joblib

# Validation qualité (optionnel)
great-expectations>=0.18  # Profiling données ETL

# File de tâches (optionnel)
celery[redis]>=5.3      # Entraînements asynchrones
redis>=5.0              # Broker Celery
```

---

## Annexe B — Variables d'environnement analytiques

| Variable | Valeur par défaut | Description |
|---|---|---|
| `DISABLE_SSE` | `False` | Désactiver SSE pour PythonAnywhere |
| `FORECAST_SAFETY_MARGIN` | `0.10` | Marge sécurité commande recommandée (10%) |
| `ANOMALY_CONTAMINATION` | `0.02` | Taux attendu d'anomalies (2%) |
| `COMMISSION_RATE` | `0.02` | Taux commission vendeur (2%) |
| `VENDEUR_MONTHLY_TARGET` | `500000` | Objectif mensuel vendeur (FCFA) |
| `ML_ARTIFACT_DIR` | `instance/ml_artifacts` | Répertoire de sauvegarde des modèles |
| `MLFLOW_TRACKING_URI` | `file:./mlruns` | URI MLflow |
| `MLFLOW_EXPERIMENT_NAME` | `gescom-bf` | Nom de l'expérience MLflow |

---

## Annexe C — Glossaire technique

| Terme | Définition |
|---|---|
| **Feature Store** | Tables SQL intermédiaires contenant les features pré-calculées pour les modèles ML |
| **ABC/XYZ** | Double classification produit : contribution CA (A/B/C) × régularité demande (X/Y/Z) |
| **RFM** | Récence / Fréquence / Montant — méthode de segmentation client |
| **CLV** | Customer Lifetime Value — valeur économique totale attendue d'un client |
| **Isolation Forest** | Algorithme ML non-supervisé pour détecter les anomalies par isolation d'observations |
| **K-Means** | Algorithme de clustering non-supervisé partitionnant les données en k groupes |
| **Cross-validation stratifiée** | Évaluation ML préservant la proportion de classes dans chaque fold |
| **Seasonal Naive** | Prévision par répétition de la moyenne par jour de semaine — repli simple |
| **SSE** | Server-Sent Events — protocole HTTP push unidirectionnel |
| **Celery** | Système de file de tâches distribuées pour Python |
| **MLflow** | Outil open-source de suivi d'expériences ML (params, métriques, artefacts) |
| **Contamination** | Paramètre Isolation Forest = proportion attendue d'anomalies dans les données |
| **CV (Coefficient de Variation)** | σ/μ — mesure de la régularité d'une série temporelle |
| **Cohorte** | Groupe de clients partageant le même mois de premier achat |
| **Rétention M+N** | % de clients d'une cohorte ayant racheté N mois après leur premier achat |
| **Feature** | Variable d'entrée utilisée par un modèle ML |
| **Payload JSON** | Données prédites stockées en JSON dans la table `predictions` |
| **RBAC** | Role-Based Access Control — contrôle d'accès par rôle |


---

## 21. Nouveaux modules — corrections pré-soutenance

### 21.1 Market Basket Analysis (`ml/market_basket.py`)

Analyse des associations entre produits achetés ensemble dans la même vente.

**Algorithme :**
```
1. mlxtend disponible → Apriori (min_support=0.01, min_confidence=0.3)
2. mlxtend absent     → Co-occurrence Counter (combinaisons paires)
```

**Résultat :** règles `{antécédents} → {conséquents}` avec support, confiance, lift.

**Usage métier :** recommandations de vente croisée ("Clients ayant acheté X ont aussi acheté Y").

Endpoints : `GET /analytics/basket`, `POST /analytics/basket/train`

---

### 21.2 Analyse d'Élasticité Prix (`services/price_elasticity_service.py`)

Mesure la sensibilité des volumes vendus aux variations de remise accordée.

**Modèle log-log :** `ln(quantité) = α + β × ln(1 - taux_remise)`

**Interprétation de β :**
- β > 0 : inélastique — la remise ne stimule pas les volumes
- -1 < β < 0 : légèrement élastique
- β < -1 : très élastique — baisser les remises réduit fortement les ventes

**Usage métier :** optimisation de la politique de remise (quand accorder 5%, 10%, 15%?).

Endpoint : `GET /analytics/price-elasticity?months=6`

---

### 21.3 Features Contextuelles Africaines (`/analytics/african-context`)

Calcul temps réel de métriques propres au contexte commercial burkinabè :

| Feature | Source | Description |
|---|---|---|
| Événements calendaires | Date système | Tabaski, saison pluies, rentrée, semaine paie |
| `saison_pluies` | `month in (6,7,8,9)` | Boolean — impact logistique |
| `weekend_boost` | `weekday in (4,5)` | Vendredi (prière +20%) / Samedi (marché +35%) |
| `indice_stress_tresorerie` | `CustomerPayment` (90j) | Taux LATE → LOW/MEDIUM/HIGH |
| `propension_credit_informel` | `Sale` ∩ `CustomerPayment` | % clients sans historique formel |

**Usage jury :** démontre la sensibilité du système au contexte africain local — différenciation forte vs. logiciels génériques.

---

### 21.4 SHAP — Explicabilité Scoring Crédit

**Problème :** les modèles Random Forest sont des "boîtes noires" — le jury peut remettre en cause leur utilisabilité si on ne peut pas expliquer une décision.

**Solution :** SHAP TreeExplainer retourne, pour chaque client, la contribution de chaque feature au score :

```json
{
  "customer_id": "uuid",
  "score": 78,
  "risk_level": "FAIBLE",
  "shap_factors": [
    {"feature": "taux_retard",     "label_fr": "Taux de retard",        "shap_value": -0.23, "direction": "negatif"},
    {"feature": "frequence_achat", "label_fr": "Fréquence d'achat",     "shap_value": +0.18, "direction": "positif"},
    ...
  ]
}
```

**Usage jury :** "Notre IA n'est pas une boîte noire — voici pourquoi ce client a un score de 78/100."

---

### 21.5 Probabilité de Churn (Segmentation RFM enrichie) — Heuristique statistique

> **Classification honnête** : ce module n'est **pas du Machine Learning**. C'est un **modèle heuristique statistique** à un seul paramètre, sans entraînement, sans données labellisées, sans split train/test, sans métrique AUC/F1.

**Formule :** décroissance exponentielle — `P(churn) = 1 - exp(-λ × recency)` où `λ = ln(2) / médiane_récence` (demi-vie = récence médiane).

**Ajustement fréquence :** `P_adj = P × (1 - 0.25 × freq_weight)` — les clients à haute fréquence ont une probabilité réduite de 25% au maximum.

**Justification du choix pour les PME burkinabè :** les PME ciblées n'ont pas d'historique de churns explicitement labellisés (aucun champ "date_résiliation", comportement de réachat implicite). Un modèle supervisé nécessiterait des centaines d'exemples positifs. La décroissance exponentielle est un standard en CRM analytique (théorie de la survie) applicable sans labellisation.

**Ce qu'il faut dire au jury :** *"Ce n'est pas un algorithme ML — c'est un modèle heuristique statistique, techniquement honnête et adapté au contexte des PME sans données labellisées. Un modèle supervisé (XGBoost sur churns historiques) est une évolution possible en post-déploiement."*

**Niveaux de risque :**
- FAIBLE (< 30%) → fidélité stable
- MODERE (30–60%) → surveillance
- ELEVE (60–80%) → relance personnalisée
- CRITIQUE (> 80%) → réactivation urgente

**Usage métier :** ciblage campagnes de réactivation, prioritisation des efforts commerciaux.

