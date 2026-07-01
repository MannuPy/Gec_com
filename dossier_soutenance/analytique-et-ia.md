# Section Analytique & Intelligence Artificielle — GesCom-BF
## Document de soutenance — Description complète, implémentation et analyse critique

---

> **Dernière mise à jour :** 1er juillet 2026 — conformité code v2 post-corrections soutenance.

> **Projet :** GesCom-BF — Système de gestion commerciale multi-sites pour le Burkina Faso  
> **Section concernée :** Module Analytique & IA (`/analytique`)  
> **Technologies :** Flask 3 · SQLAlchemy 2 · scikit-learn · pandas · numpy · React 18 · TypeScript · Recharts

---

## Table des matières

1. [Vue d'ensemble de la section](#1-vue-densemble)
2. [Architecture générale](#2-architecture-générale)
3. [Tableau de bord analytique étendu](#3-tableau-de-bord-analytique-étendu)
4. [Prévisions de demande](#4-prévisions-de-demande)
5. [Classification ABC/XYZ des produits](#5-classification-abcxyz-des-produits)
6. [Segmentation RFM des clients](#6-segmentation-rfm-des-clients)
7. [Scoring crédit clients](#7-scoring-crédit-clients)
8. [Détection d'anomalies sur les ventes](#8-détection-danomalies-sur-les-ventes)
9. [Analyse de cohortes clients](#9-analyse-de-cohortes-clients)
10. [Valeur vie client (CLV)](#10-valeur-vie-client-clv)
11. [Registre & Entraînement des modèles ML](#11-registre--entraînement-des-modèles-ml)
12. [Bilan global — Avantages et limites](#12-bilan-global--avantages-et-limites)

---

## 1. Vue d'ensemble

La section **Analytique & IA** de GesCom-BF regroupe l'ensemble des fonctionnalités d'analyse avancée et d'intelligence artificielle du système. Elle est accessible depuis le menu latéral via l'entrée *"Analytique & IA"* et est protégée par la permission `analytics:read` (nécessite un rôle MANAGER ou ADMIN).

L'objectif de cette section est de transformer les données brutes de vente en **informations décisionnelles exploitables** : prévoir les ruptures de stock, identifier les clients à risque de crédit, détecter les fraudes potentielles, segmenter la clientèle et estimer la rentabilité à long terme de chaque client.

La section se divise en **9 onglets** :

| Onglet | Fonctionnalité | Permission requise |
|--------|---------------|-------------------|
| Tableau de bord | Indicateurs étendus (marges, multi-sites) | `analytics:read` |
| Prévisions de demande | Prévision stock et alertes rupture | `analytics:read` |
| ABC / XYZ | Classification des produits | `analytics:read` |
| Segmentation RFM | Segmentation clients | `analytics:read` |
| Scoring crédit | Score de risque crédit | `analytics:read` |
| Anomalies | Ventes suspectes | `analytics:read` |
| Cohortes clients | Rétention par cohorte d'acquisition | `analytics:read` |
| Valeur vie client | CLV estimé par client | `analytics:read` |
| Modèles IA | Registre & déclenchement d'entraînement | `analytics:read` / `ml:train` |

---

## 2. Architecture générale

### 2.1 Organisation du code

```
backend/
  app/
    blueprints/
      analytics/
        __init__.py        # Blueprint Flask "analytics_bp"
        routes.py          # Tous les endpoints /api/v1/analytics/*
        schemas.py         # Schémas marshmallow de sérialisation
    services/
      analytics_service.py # Requêtes SQL agrégées (dashboard, trend, top_products)
      etl_service.py       # Pipeline ETL pour alimenter la Feature Store
    ml/
      common.py            # Utilitaires partagés (persistance, MLflow, registre)
      demand_forecast.py   # Module prévision de demande
      abc_xyz.py           # Module classification ABC/XYZ
      rfm_segmentation.py  # Module segmentation RFM
      credit_scoring.py    # Module scoring crédit
      anomaly_detection.py # Module détection d'anomalies
    models/
      ml.py                # Modèles SQLAlchemy : MLModel, Prediction
      feature_store.py     # Feature Store : FsCustomerRfm, FsCustomerCreditFeatures, FsTransactionFeatures
    tasks/
      ml_tasks.py          # Déclenchement ML (threads Python natifs, sans Celery)

frontend/
  src/
    features/
      analytics/
        pages/
          AnalyticsPage.tsx  # Page principale, 9 onglets
    api/
      endpoints/
        analytics.ts         # Client HTTP vers /api/v1/analytics/*
    types/
      analytics.ts           # Types TypeScript de toutes les réponses ML
```

### 2.2 Flux de données général

```
┌─────────────────────────────────────────────────┐
│               Base de données MySQL              │
│  sales · sale_lines · products · stock ·        │
│  customers · customer_payments · branches       │
└──────────────────┬──────────────────────────────┘
                   │ SQLAlchemy ORM
                   ▼
┌─────────────────────────────────────────────────┐
│         ETL Pipeline (etl_service.py)           │
│  Calcule et matérialise les features dans la    │
│  Feature Store (fs_customer_rfm, etc.)          │
└──────────────────┬──────────────────────────────┘
                   │ Lecture Feature Store ou directe
                   ▼
┌─────────────────────────────────────────────────┐
│          Modules ML  (app/ml/*.py)              │
│  train() → entraîne le modèle                   │
│  latest() → retourne les prédictions en cache   │
└──────────────────┬──────────────────────────────┘
                   │ ORM : table predictions
                   ▼
┌─────────────────────────────────────────────────┐
│          Analytics Routes (routes.py)           │
│  GET /analytics/forecast, /abc-xyz, /rfm…       │
│  POST /analytics/ml/train/<type>                │
└──────────────────┬──────────────────────────────┘
                   │ JSON via Axios
                   ▼
┌─────────────────────────────────────────────────┐
│       AnalyticsPage.tsx  (React + Recharts)     │
│  9 onglets · graphiques · tableaux · filtres    │
└─────────────────────────────────────────────────┘
```

### 2.3 Modèle de persistance ML (base de données)

Deux tables dédiées stockent les résultats des modèles :

**Table `ml_models`**

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | UUID | Clé primaire |
| `model_type` | VARCHAR | Ex. `DEMAND_FORECAST`, `CREDIT_SCORING` |
| `version` | VARCHAR | Ex. `demand_forecast_20250601_143200` |
| `algorithm` | VARCHAR | Algorithme réellement utilisé |
| `metrics_json` | JSON | Métriques d'évaluation |
| `artifact_path` | VARCHAR | Chemin du fichier `.joblib` (si sauvegardé) |
| `mlflow_run_id` | VARCHAR | ID de run MLflow (optionnel) |
| `trained_at` | DATETIME | Horodatage d'entraînement |
| `is_active` | BOOLEAN | Un seul modèle actif par type |

**Table `predictions`**

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | UUID | Clé primaire |
| `model_id` | UUID | FK → `ml_models.id` |
| `prediction_type` | VARCHAR | Ex. `DEMAND_FORECAST`, `ABC_XYZ` |
| `entity_type` | VARCHAR | `product`, `customer`, `sale` |
| `entity_id` | UUID | ID de l'entité concernée |
| `payload_json` | JSON | Résultat complet de la prédiction |
| `created_at` | DATETIME | Date de la prédiction |

**Feature Store** (3 tables matérialisées par l'ETL) :
- `fs_customer_rfm` — métriques RFM précalculées par client
- `fs_customer_credit_features` — features de scoring crédit
- `fs_transaction_features` — features par transaction pour la détection d'anomalies

---

## 3. Tableau de bord analytique étendu

### 3.1 À quoi ça sert ?

Le tableau de bord analytique étendu offre une **vue consolidée des performances financières** de l'entreprise sur une période configurable (7, 30, 90 jours). Contrairement au tableau de bord opérationnel (qui montre uniquement le CA du jour), cet onglet expose les **marges brutes, la ventilation multi-sites et les alertes temps réel** issues des modèles ML.

### 3.2 Comment ça fonctionne ?

L'onglet se décompose en deux couches :

**Couche statique** (`GET /analytics/dashboard`) — calcul des marges sur la période :
- CA et nombre de ventes par succursale
- Coût d'achat des produits vendus (prix d'achat × quantité)
- Marge brute = CA − Coût
- Taux de marge (%) par site et consolidé

**Couche temps réel** (`GET /analytics/dashboard/realtime`) — snapshot instantané enrichi par les modèles ML :
- CA du jour et du mois
- Alertes de rupture de stock prévisionnelles (issues du module `demand_forecast`)
- Alertes sur les ventes atypiques (issues du module `anomaly_detection`)
- Alertes sur les clients à risque crédit élevé (issues du module `credit_scoring`)
- Classifications ABC/XYZ et segments RFM en cache

### 3.3 Implémentation backend

**Fichier :** `backend/app/services/analytics_service.py`

```python
def compute_dashboard(branch_id=None, days=30) -> dict:
    # Requête 1 : CA et nombre de ventes par succursale
    revenue_query = db.session.query(
        Sale.branch_id,
        Branch.name.label("branch_name"),
        func.sum(Sale.total).label("revenue"),
        func.count(Sale.id).label("sales_count"),
    ).join(Branch).filter(Sale.status == "VALIDEE", Sale.created_at >= period_start)

    # Requête 2 : coût d'achat (SaleLine.quantity × Product.purchase_price)
    cost_query = db.session.query(
        Sale.branch_id,
        func.sum(SaleLine.quantity * Product.purchase_price).label("cost"),
    ).join(SaleLine).join(Product).filter(...)

    # Fusion et calcul de la marge pour chaque site
    for row in branch_rows:
        marge = revenue - cost
        marge_rate = float(marge) / float(revenue) * 100
```

**Fichier :** `backend/app/blueprints/analytics/routes.py`

```python
@analytics_bp.get("/dashboard")
@require_permission("analytics:read")
def advanced_dashboard():
    return jsonify(compute_dashboard(branch_id, days))

@analytics_bp.get("/dashboard/realtime")
@require_permission("analytics:read")
def demand_forecast_view():
    # Appelle les modules ML via leur méthode latest()
    alerts = []
    for item in demand_forecast.latest(alerts_only=True): ...
    for item in anomaly_detection.latest(): ...
    for item in credit_scoring.latest(): ...
```

### 3.4 Implémentation frontend

**Fichier :** `frontend/src/features/analytics/pages/AnalyticsPage.tsx`

- `useQuery(["analytics-dashboard"])` → appelle `analyticsApi.dashboard()`
- `useQuery(["analytics-realtime"])` → appelle `analyticsApi.realtime()`
- **Graphiques Recharts :** `AreaChart` pour la tendance du CA, `BarChart` pour la comparaison des marges par site
- Les alertes temps réel sont affichées sous forme de bannières colorées (rouge = critique, orange = attention)

### 3.5 Avantages

- **Visibilité complète** : marge brute visible en un coup d'œil, impossible avec le tableau de bord opérationnel standard
- **Multi-sites** : consolidation automatique de toutes les succursales
- **Alertes proactives** : les 3 types d'alertes ML sont agrégés en un seul endpoint pour le manager

### 3.6 Inconvénients / Limites

- **Coût d'achat approximatif** : la marge est calculée avec le `purchase_price` figé dans la fiche produit. Si le prix d'achat varie selon la réception, la marge est inexacte
- **Pas de marge nette** : les charges fixes (loyer, salaires) ne sont pas modélisées
- **Dépendance aux modèles ML** : si aucun entraînement n'a été lancé, les alertes temps réel sont vides

---

## 4. Prévisions de demande

### 4.1 À quoi ça sert ?

Le module de **prévision de demande** analyse l'historique des ventes pour estimer les quantités qui seront vendues dans les **7 et 30 prochains jours**, pour chaque couple (produit, succursale). Il génère des **alertes de rupture de stock** lorsque le stock disponible ne couvre pas la demande prévue sur 7 jours.

**Cas d'usage concret :** un manager voit que le "Câble VGA 2m" a un stock de 3 unités au dépôt central, et que la prévision à 7 jours est de 8 unités vendues — le système déclenche une alerte et recommande de commander 6 unités supplémentaires.

### 4.2 Comment ça fonctionne ?

Le module suit un pipeline en 4 étapes :

```
1. Chargement des données
   └─ 6 mois de SaleLines groupées par (product_id, branch_id, date)
      → DataFrame pandas : série temporelle par couple produit/site

2. Choix d'algorithme (automatique)
   ├─ Si scikit-learn disponible ET historique ≥ 14 jours
   │    → LinearRegression avec features jour-de-semaine (0-6)
   └─ Sinon
        → Naive Saisonnier (moyenne par jour de la semaine)

3. Génération des prévisions
   └─ forecast_7d et forecast_30d pour chaque série

4. Calcul de l'alerte
   └─ alerte = stock_dispo < seuil_min OU (stock_dispo - forecast_7d) < 0
   └─ quantite_recommandee = max(0, forecast_30d - stock_dispo) × (1 + safety_margin)
```

**Algorithme LinearRegression (sklearn) :**

```python
# Features : numéro du jour (trend) + 7 dummies jour-de-semaine
X = np.column_stack([
    np.arange(n),                                    # tendance linéaire
    *[(series.index.dayofweek == d).astype(int)      # saisonnalité hebdo
      for d in range(7)],
])
model = LinearRegression().fit(X, y)
# Prédiction sur les 30 prochains jours, clippée à 0 (pas de ventes négatives)
preds = np.clip(model.predict(X_future), 0, None)
```

**Algorithme Naïf Saisonnier (repli) :**

```python
# Moyenne des ventes par jour de la semaine sur l'historique
by_dow = series.groupby(series.index.dayofweek).mean()
preds = [by_dow.get(d, series.mean()) for d in future_idx.dayofweek]
```

### 4.3 Implémentation base de données

- **Entrée :** tables `sale_lines` JOIN `sales` (filtrées sur `status = VALIDEE`)
- **Sortie :** table `predictions` (type `DEMAND_FORECAST`) — un enregistrement par couple (produit, site) avec le `payload_json` contenant :

```json
{
  "product_name": "Câble VGA 2m",
  "branch_id": "uuid-depot",
  "forecast_7d": 8.5,
  "forecast_30d": 34.2,
  "stock_disponible": 3,
  "seuil_min": 5,
  "alerte_rupture": true,
  "quantite_recommandee": 33.7,
  "algorithm": "SKLEARN_LINEAR_TREND"
}
```

### 4.4 Implémentation backend

**Endpoints :**

```
GET /api/v1/analytics/forecast
  ?alerts_only=true   → filtrer uniquement les alertes
  ?branch_id=uuid     → filtrer par site
  ?product_id=uuid    → filtrer par produit

GET /api/v1/analytics/forecast/<product_id>/<branch_id>
  → Détail d'une prévision précise

POST /api/v1/analytics/ml/train/DEMAND_FORECAST
  → Déclenche le réentraînement (permission ml:train)
```

**Fichier :** `backend/app/ml/demand_forecast.py`

- `train(months=6)` : charge, entraîne, persiste en base
- `latest(alerts_only=False)` : lit la table `predictions`, retourne la liste

### 4.5 Implémentation frontend

- **Filtre :** checkbox "Alertes uniquement", sélecteur succursale
- **Tableau :** produit, site, stock actuel, prévision J+7, prévision J+30, statut (🔴 Alerte / ✅ OK), quantité recommandée
- **Badge rouge** sur le badge de navigation si des alertes sont actives

### 4.6 Avantages

- **Repli automatique** : si scikit-learn n'est pas installé (environnement contraint), le système bascule sur un algorithme naïf sans planter
- **Prise en compte de la saisonnalité hebdomadaire** : les deux algorithmes intègrent le jour de la semaine
- **Safety margin configurable** : paramètre `FORECAST_SAFETY_MARGIN` dans la config Flask (défaut 10 %)
- **Alertes directement exploitables** : la quantité recommandée est calculée automatiquement

### 4.7 Inconvénients / Limites

- **Historique minimum de 14 jours** : une boutique qui vient d'ouvrir n'a aucune prévision pendant les 2 premières semaines
- **Pas de prise en compte des commandes fournisseurs en cours** : la quantité recommandée ne soustrait pas ce qui a déjà été commandé

> **Note :** Prophet (avec calendrier de fêtes burkinabè) et les features africaines de contexte (Tabaski, Ramadan, saison des pluies, semaine de paie) sont **implémentés et actifs**. La cascade est : Prophet (≥30 jours) → LinearRegression (≥14 jours) → Naïf saisonnier. Le champ `data_confidence` est inclus dans les prévisions. Le réentraînement nocturne est planifié via `scripts/cron_train_all.py` sur PythonAnywhere Tasks.

---

## 5. Classification ABC/XYZ des produits

### 5.1 À quoi ça sert ?

La classification **ABC/XYZ** est une méthode standard de gestion des stocks qui croise deux axes :

- **Axe ABC** (contribution au chiffre d'affaires cumulé) :
  - **A** : produits qui génèrent 80 % du CA → à surveiller en priorité
  - **B** : produits qui génèrent les 15 % suivants → gestion courante
  - **C** : produits qui génèrent les 5 % restants → à rationaliser ou éliminer

- **Axe XYZ** (régularité de la demande, mesurée par le coefficient de variation) :
  - **X** : demande régulière (CV < 0,5) → stock de sécurité faible
  - **Y** : demande variable (0,5 ≤ CV ≤ 1) → stock de sécurité modéré
  - **Z** : demande irrégulière (CV > 1) → gérer à la commande

**Exemple de lecture :** un produit classé **AX** est stratégique (fort CA) et prévisible (demande régulière) — c'est la catégorie à ne jamais laisser en rupture. Un produit **CZ** est peu rentable et imprévisible — candidat à la déréférencement.

### 5.2 Comment ça fonctionne ?

L'algorithme est entièrement déterministe (règles pandas, pas de ML) :

**Calcul ABC :**
```python
# 1. Regrouper les ventes par produit → CA par produit
revenue_by_product = df.groupby("product_id")["line_total"].sum().sort_values(ascending=False)
# 2. CA cumulé / CA total = part cumulée
cumulative = revenue_by_product.cumsum() / total_revenue
# 3. Attribution de la classe
if cum_share <= 0.80 → A
elif cum_share <= 0.95 → B
else → C
```

**Calcul XYZ :**
```python
# 1. Regrouper les ventes par (produit, semaine)
weekly = df.groupby(["product_id", "week"])["quantity"].sum()
# 2. Coefficient de variation = écart-type / moyenne
cv = std / mean
# 3. Attribution de la classe
if cv < 0.5 → X
elif cv <= 1.0 → Y
else → Z
```

**Cas particulier — stock mort :** les produits actifs sans aucune vente sur la période sont automatiquement classés **CZ** avec le flag `dead_stock=True`.

### 5.3 Implémentation base de données

- **Entrée :** tables `sale_lines` JOIN `sales` JOIN `products`
- **Sortie :** table `predictions` (type `ABC_XYZ`) — un enregistrement par produit avec :

```json
{
  "product_name": "Disjoncteur 16A",
  "abc_class": "A",
  "xyz_class": "X",
  "combined_class": "AX",
  "revenue": 485000.0,
  "cv": 0.31,
  "dead_stock": false
}
```

### 5.4 Implémentation backend

```
GET /api/v1/analytics/abc-xyz
  ?abc_class=A       → filtrer par classe ABC
  ?xyz_class=X       → filtrer par classe XYZ
```

### 5.5 Implémentation frontend

- **Tableau filtrable** par classe ABC et/ou XYZ
- **PieChart** de répartition A/B/C en nombre de produits et en CA
- **ScatterChart** CV vs CA pour visualiser la matrice ABC/XYZ
- **Badge "Stock mort"** mis en évidence en rouge pour les produits CZ sans ventes

### 5.6 Avantages

- **Algorithme déterministe** : pas de composant aléatoire, résultat reproductible
- **Pas de dépendance ML externe** : fonctionne avec pandas seul, disponible partout
- **Stock mort automatiquement détecté** : les produits invendus sur la période sont identifiés sans requête supplémentaire
- **Combinaison AX–CZ** : les 9 combinaisons possibles permettent des décisions fines de gestion

### 5.7 Inconvénients / Limites

- **Sensible à la durée de la période** : un produit saisonnier analysé hors saison sera faussement classé CZ
- **Basé uniquement sur le CA** : un produit à forte marge mais CA modéré sera sous-classé
- **Pas de prise en compte des coûts de stockage** : un produit encombrant CZ devrait être traité plus urgemment qu'un petit composant CZ

---

## 6. Segmentation RFM des clients

### 6.1 À quoi ça sert ?

La segmentation **RFM (Récence, Fréquence, Montant)** classe chaque client en fonction de son comportement d'achat selon trois axes :

- **R (Récence)** : depuis combien de jours ce client a-t-il acheté pour la dernière fois ?
- **F (Fréquence)** : combien de fois ce client a-t-il acheté sur la période ?
- **M (Montant)** : quel est le montant total de ses achats ?

Quatre segments sont définis :

| Segment | Caractéristiques | Action recommandée |
|---------|-----------------|-------------------|
| **CHAMPIONS** | Faible récence + forte fréquence + fort montant | Programme fidélité, crédit étendu |
| **REGULIERS** | Faible récence + faible fréquence ou montant | Relances ciblées |
| **A_RISQUE** | Forte récence + forte fréquence ou montant | Campagne de réactivation |
| **OCCASIONNELS** | Forte récence + faible fréquence et montant | Communication standard |

### 6.2 Comment ça fonctionne ?

Le système utilise **deux algorithmes en cascade** :

**Algorithme principal — K-Means (sklearn) :**
```python
# Normalisation des features RFM
X_scaled = StandardScaler().fit_transform(X)  # X = [recency, frequency, monetary]
# Clustering en 4 groupes
kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
clusters = kmeans.fit_predict(X_scaled)

# Attribution des labels : trier les centroïdes par score composite
# score = frequency + monetary - recency (clients récents, fréquents, dépensiers = Champions)
centers["score"] = centers["frequency"] + centers["monetary"] - centers["recency"]
```

**Algorithme de repli — Règles par quartiles :**
```python
# Si sklearn absent OU nombre de clients < 4
r_median = df["recency"].median()
fm_median = (df["frequency"] + df["monetary"] / max_monetary).median()
# Attribution par quadrant récence/fréquence-montant
if recency ≤ median AND fm ≥ median → CHAMPIONS
if recency ≤ median AND fm < median → REGULIERS
if recency > median AND fm ≥ median → A_RISQUE
else → OCCASIONNELS
```

**Priorisation Feature Store :** si la table `fs_customer_rfm` est alimentée par le pipeline ETL, elle est utilisée en priorité (données précalculées et optimisées). Sinon, le calcul se fait directement depuis les tables `sales` et `sale_lines`.

### 6.3 Implémentation base de données

- **Entrée (Feature Store) :** `fs_customer_rfm` (alimentée par `etl_service.py`)
- **Entrée (directe) :** `sales` JOIN `sale_lines` filtrées sur 12 mois
- **Sortie :** `predictions` (type `RFM_SEGMENT`) :

```json
{
  "customer_name": "Dramane Compaoré",
  "recency_days": 12,
  "frequency": 8,
  "monetary": 245000.0,
  "segment": "CHAMPIONS",
  "segment_label": "Champions",
  "recommended_action": "Programme de fidélité, crédit étendu"
}
```

### 6.4 Implémentation frontend

- **Tableau** de tous les clients avec leur segment et métriques RFM
- **PieChart** de répartition des segments en nombre de clients
- **ScatterChart** Récence vs Fréquence, taille des bulles = Montant, couleur = Segment
- **Filtre** par segment pour cibler un groupe précis

### 6.5 Avantages

- **Double algorithme** : K-Means pour une vraie segmentation data-driven, repli par règles si les données sont insuffisantes
- **Action recommandée incluse** : chaque segment inclut la stratégie marketing à appliquer
- **Feature Store** : si le pipeline ETL est actif, les calculs RFM ne bloquent pas le thread Flask

### 6.6 Inconvénients / Limites

- **4 segments fixes** : la réalité peut nécessiter une granularité plus fine (ex. : champions qui se désengagent)
- **Pas de score individuel continu** : on ne peut pas trier les clients du "plus champion" au "moins champion" à l'intérieur d'un segment

> **Note :** Le K optimal est déterminé automatiquement par la méthode du coude (inertie) et le score de Silhouette via `evaluate_optimal_k()`. L'endpoint `/analytics/rfm-segments/evaluate-k` expose les scores Silhouette et Elbow pour k=2 à k=8. La **Churn Probability** (décroissance exponentielle calibrée sur la médiane de récence, ajustée par la fréquence) est calculée et exposée dans chaque prédiction RFM.

---

## 7. Scoring crédit clients

### 7.1 À quoi ça sert ?

Le module de **scoring crédit** attribue à chaque client ayant des achats à crédit un **score entre 0 et 100** et un **niveau de risque** (FAIBLE / MOYEN / ÉLEVÉ). Ce score aide le manager à décider s'il doit accorder ou maintenir une ligne de crédit.

| Score | Niveau | Couleur |
|-------|--------|---------|
| 71 – 100 | FAIBLE | Vert |
| 41 – 70 | MOYEN | Orange |
| 0 – 40 | ÉLEVÉ | Rouge |

### 7.2 Comment ça fonctionne ?

**8 features utilisées :**

| Feature | Signification |
|---------|--------------|
| `nb_achats_credit_total` | Nombre d'achats à crédit |
| `montant_moyen_achat` | Panier moyen |
| `delai_moyen_remboursement_jours` | Délai moyen de règlement |
| `taux_retard` | Part des paiements en retard |
| `anciennete_client_mois` | Ancienneté du compte client |
| `frequence_achat_mensuelle` | Fréquence d'achat par mois |
| `solde_du_actuel` | Encours crédit actuel |
| `is_technicien` | Type de client (0/1) |

**Algorithme principal — Random Forest + Logistic Regression (sklearn) :**

```python
# Validation croisée stratifiée des deux modèles
skf = StratifiedKFold(n_splits=min(5, min_class_count))
rf_acc  = cross_val_score(RandomForestClassifier(200), X, y, cv=skf).mean()
lr_acc  = cross_val_score(LogisticRegression(), X, y, cv=skf).mean()

# Entraînement du Random Forest sur toutes les données
rf.fit(X, y)
# Score = probabilité d'être "bon payeur" × 100
scores = rf.predict_proba(X)[:, 1] * 100
```

**Algorithme de repli — Score par règles :**
```python
# Combinaison pondérée de 3 indicateurs
scores = (1 - taux_retard) * 70            # 70% du score = fiabilité de paiement
       + clip(1 - delai_moy / 90, 0, 1) * 20  # 20% = rapidité de règlement
       + clip(frequence_mensuelle, 0, 1) * 10  # 10% = engagement commercial
```

**Données de remboursement :** si les historiques de paiement réels (table `customer_payments`) sont insuffisants, le `taux_retard` et le `delai_moyen_remboursement_jours` sont **dérivés de façon déterministe** par hash SHA-256 de l'UUID client — garantissant la reproductibilité des scores entre deux entraînements, même sans données réelles.

### 7.3 Implémentation base de données

- **Entrée (Feature Store) :** `fs_customer_credit_features`
- **Entrée (directe) :** `customers` JOIN `sales` (filtré `payment_type = CREDIT`)
- **Variable cible :** `bon_payeur = 1` si `taux_retard < 0.20`, sinon `0`
- **Sortie :** `predictions` (type `CREDIT_SCORE`) :

```json
{
  "customer_name": "Issouf Traoré",
  "score": 32.5,
  "risk_level": "ELEVE",
  "nb_achats_credit_total": 4,
  "taux_retard": 0.75,
  "solde_du_actuel": 85000.0
}
```

### 7.4 Implémentation frontend

- **Tableau** trié par score croissant (plus risqué en haut)
- **Filtre** par niveau de risque (ÉLEVÉ / MOYEN / FAIBLE)
- **BarChart** horizontal : top 10 clients par encours vs score
- **Bouton "Ré-entraîner"** avec date du dernier entraînement

### 7.5 Avantages

- **Double algorithme** avec comparaison automatique des performances de Random Forest vs Régression Logistique (métriques de CV en sortie)
- **Condition d'activation ML** : le modèle ML ne s'active que si ≥ 20 clients et les 2 classes représentées — évite le surapprentissage sur un petit dataset
- **Reproductibilité** : hash déterministe pour les données simulées → même score à chaque entraînement

### 7.6 Inconvénients / Limites

- **Pas de seuil de décision configurable** : les seuils 40/70 sont hardcodés
- **Biais potentiel sur `is_technicien`** : inclure le type de client comme feature peut introduire un biais de discrimination commerciale

> **Note :** Le fallback SHA-256 (score fictif) a été **supprimé**. Quand les données de crédit sont insuffisantes, le système retourne `score: null, risk_level: "INDETERMINATE"` avec un message explicite. L'**explicabilité SHAP** (TreeExplainer sur le Random Forest) est implémentée via l'endpoint `/analytics/credit-scores/<id>/explain` — chaque score est accompagné des contributions de chaque feature et de phrases en français.

---

## 8. Détection d'anomalies sur les ventes

### 8.1 À quoi ça sert ?

Le module de **détection d'anomalies** identifie les ventes dont le profil statistique est inhabituel — potentiellement des erreurs de saisie, des fraudes internes ou des remises non autorisées. Chaque vente signalée est accompagnée des raisons qui l'ont rendue suspecte.

**Exemples d'anomalies détectées :**
- Vente avec une remise de 25 % sur un article habituellement vendu sans remise
- Vente effectuée à 2h du matin (hors des horaires habituels)
- Montant de la vente 3× supérieur à la moyenne du caissier

### 8.2 Comment ça fonctionne ?

**5 features utilisées :**

| Feature | Signification |
|---------|--------------|
| `montant_total` | Montant total de la vente |
| `remise_taux` | Taux de remise accordé (%) |
| `heure_vente` | Heure de création de la vente (0-23) |
| `ecart_vs_moyenne_produit` | Écart normalisé par rapport à la moyenne produit |
| `ecart_vs_moyenne_vendeur` | Écart normalisé par rapport à la moyenne du vendeur |

**Algorithme principal — Isolation Forest (sklearn) :**

```python
model = IsolationForest(n_estimators=200, contamination=0.02, random_state=42)
model.fit(X)
# score = decision_function → plus négatif = plus anormal
scores = model.decision_function(X)
threshold = np.quantile(scores, contamination)  # seuil dynamique
is_anomaly = scores < threshold
```

**Algorithme de repli — Z-Score :**
```python
# Si sklearn absent ou moins de 10 ventes
z = (montant_total - mean) / std
is_anomaly = z.abs() > 3   # ventes au-delà de 3 écarts-types
```

**Raisons verbalisées (post-traitement) :**
```python
if remise_taux >= 15: reasons.append("Remise élevée")
if ecart_vs_moyenne_produit > 1: reasons.append("Montant >> moyenne produit")
if ecart_vs_moyenne_vendeur > 1: reasons.append("Montant >> moyenne vendeur")
if heure_vente < 6 or heure_vente > 21: reasons.append("Vente hors horaires")
if not reasons: reasons.append("Profil statistique atypique")
```

### 8.3 Implémentation base de données

- **Entrée (Feature Store) :** `fs_transaction_features` (alimentée par l'ETL)
- **Entrée (directe) :** table `sales` sur 90 jours (statuts `VALIDEE` et `EN_ATTENTE_APPROBATION`)
- **Paramètre :** `ANOMALY_CONTAMINATION` (config Flask, défaut 2 %) = taux attendu d'anomalies
- **Sortie :** `predictions` (type `ANOMALY`) :

```json
{
  "sale_id": "uuid-vente",
  "reference": "VTE-20250601-0047",
  "branch_id": "uuid-site",
  "cashier_name": "Abdoul Kaboré",
  "montant_total": 185000.0,
  "remise_taux": 20,
  "score": -0.1523,
  "reasons": ["Remise élevée", "Montant >> moyenne vendeur"]
}
```

### 8.4 Implémentation frontend

- **Tableau** des ventes anomaliques triées par score (plus suspect en premier)
- **Filtre** par succursale
- **Badges de raisons** colorés pour chaque vente signalée
- **Lien vers la vente originale** depuis l'historique des ventes

### 8.5 Avantages

- **Unsupervised** : aucune donnée labellée de fraude n'est nécessaire — le modèle apprend la notion de "normal" depuis les données
- **Isolation Forest robuste** aux outliers multidimensionnels : combine 5 features simultanément
- **Raisons verbalisées** : l'utilisateur comprend pourquoi une vente est suspecte, pas seulement que le score est bas
- **Paramètre de contamination configurable** : adapté à l'environnement métier (PME vs grande enseigne)

### 8.6 Inconvénients / Limites

- **Taux de faux positifs** : 2 % de contamination = environ 1 vente sur 50 flagguée sans être vraiment suspecte
- **Pas de feedback utilisateur** : il n'existe pas de mécanisme pour valider ou rejeter une anomalie signalée, ce qui empêche l'apprentissage supervisé itératif
- **Sensible aux changements de comportement légitimes** : une promotion saisonnière avec remise de 20 % sera détectée comme anomalie

---

## 9. Analyse de cohortes clients

### 9.1 À quoi ça sert ?

L'analyse de **cohortes clients** mesure la **rétention** de chaque groupe de clients acquis le même mois. Elle répond à la question : *"Parmi les clients qui ont acheté pour la première fois en janvier 2025, combien reviennent en février ? En mars ?"*

C'est un indicateur clé de la **fidélisation client** et de la santé commerciale à long terme.

### 9.2 Comment ça fonctionne ?

L'algorithme est entièrement en Python (pas de ML) :

```python
# 1. Identifier le mois du premier achat pour chaque client
for customer_id, created_at in sales:
    cohort[customer_id] = min(cohort.get(customer_id, mois), mois)

# 2. Pour chaque mois (delta = 0, 1, 2, …)
for cohort_mois in cohorts_sorted:
    members = clients_de_cette_cohorte
    for delta in range(nb_months + 1):
        target_mois = cohort_mois + delta
        count = sum(1 for c in members if target_mois in customer_months[c])
        rate = count / size * 100   # % de rétention
```

### 9.3 Implémentation backend

**Endpoint :** `GET /api/v1/analytics/cohorts?months=12`

**Réponse :**
```json
{
  "cohorts": [
    {
      "cohort": "2025-01",
      "size": 23,
      "retention": [
        {"month": 0, "month_label": "2025-01", "count": 23, "rate": 100.0},
        {"month": 1, "month_label": "2025-02", "count": 15, "rate": 65.2},
        {"month": 2, "month_label": "2025-03", "count": 11, "rate": 47.8}
      ]
    }
  ],
  "max_months": 5
}
```

### 9.4 Implémentation frontend

- **Tableau de chaleur (heatmap)** : lignes = cohortes, colonnes = M+0, M+1, M+2… couleur = taux de rétention (vert = fort, rouge = faible)
- **AreaChart** de la rétention moyenne toutes cohortes confondues
- **Paramètre** : nombre de mois analysés (1–24)

### 9.5 Avantages

- **Aucune dépendance ML** : calcul purement analytique, résultat immédiat
- **Indicateur stratégique** : la rétention à M+3 est souvent plus prédictive de la santé d'une enseigne que le CA mensuel
- **Par cohorte mensuelle** : permet d'identifier si une campagne d'acquisition spécifique a généré des clients plus fidèles

### 9.6 Inconvénients / Limites

- **Sensible au volume** : avec moins de 10 clients par cohorte, les taux de rétention sont statistiquement non significatifs
- **Pas de segmentation par canal** : impossible de distinguer la rétention des clients acquis via promotion vs clients organiques
- **Calcul en mémoire** : charger 24 mois de ventes d'un coup peut être lent pour une base de données volumineuse

---

## 10. Valeur vie client (CLV)

### 10.1 À quoi ça sert ?

La **valeur vie client (CLV — Customer Lifetime Value)** estime combien un client rapportera à l'entreprise sur la durée de sa relation commerciale. C'est un indicateur fondamental pour prioriser les efforts de fidélisation : un client CLV élevé mérite plus d'attention qu'un client CLV faible.

### 10.2 Comment ça fonctionne ?

**Formule CLV :**

```
CLV = panier_moyen × fréquence_mensuelle × durée_vie_estimée_mois
```

**Estimation de la durée de vie :**
```python
# Durée historique = mois entre premier et dernier achat × 2 (extrapolation)
duree_vie_historique = delta_mois * 2

# Plafonnement par nombre d'achats (confiance dans l'estimation)
duree_vie_par_nb = nb_achats * 6  # 6 mois de crédit par achat

# Fusion : minimum des deux, plafonné à 36 mois, minimum 3 mois
duree_vie_estimee = max(3, min(36, duree_vie_par_nb, duree_vie_historique))

# Exception : client établi (≥ 4 achats) → on fait confiance à l'historique
if nb_achats >= 4:
    duree_vie_estimee = max(6, min(36, duree_vie_historique))
```

**Indice de confiance :**
```python
data_confidence = round(min(1.0, nb_achats / 5), 2)
# 1 achat → confiance 0.20 ; 5 achats et plus → confiance 1.00
```

### 10.3 Implémentation backend

**Endpoint :** `GET /api/v1/analytics/clv?limit=50&min_clv=10000`

**Réponse :** liste de clients avec CLV estimé, statistiques globales (moyenne, médiane, max, min).

### 10.4 Implémentation frontend

- **Tableau** trié par CLV décroissant avec colonne "Confiance" (barre de progression)
- **Filtres :** nombre maximum de clients, CLV minimum
- **Stats globales** : CLV moyen, médian, max
- **BarChart** : top 10 clients par CLV estimé

### 10.5 Avantages

- **Indice de confiance** : le système signale lui-même que le CLV d'un client à 1 achat est peu fiable
- **Anti-CLV irréaliste** : le plafonnement par `nb_achats × 6` évite qu'un client à un seul achat de 500 000 FCFA se retrouve avec un CLV de 18 millions
- **Filtre `min_clv`** : permet de ne voir que les clients qui méritent vraiment un investissement de fidélisation

### 10.6 Inconvénients / Limites

- **Formule simplifiée** : le modèle BG/NBD (Beta-Geometric/Negative Binomial Distribution), référence académique pour le CLV, n'est pas implémenté
- **Pas de prise en compte du churn** : la probabilité qu'un client soit déjà perdu n'est pas modélisée
- **Durée de vie extrapolée × 2** : l'hypothèse que la relation durera 2× la durée observée est arbitraire

---

## 11. Registre & Entraînement des modèles ML

### 11.1 À quoi ça sert ?

Le **registre des modèles** (`GET /analytics/ml/models`) offre une **traçabilité complète** de tous les entraînements ML : qui a lancé l'entraînement, quand, avec quel algorithme et quelles performances. C'est une exigence de **gouvernance des données** (RNF-17).

**L'entraînement** (`POST /analytics/ml/train`) permet à un utilisateur autorisé (`ml:train`) de déclencher manuellement ou automatiquement la mise à jour de n'importe quel modèle.

### 11.2 Comment ça fonctionne ?

**Déclenchement :**

```
POST /api/v1/analytics/ml/train/<model_type>
  → Lance l'entraînement dans un thread Python natif (threading.Thread, daemon=True)
  → Retourne immédiatement HTTP 202 Accepted — non bloquant

POST /api/v1/analytics/ml/train    (body JSON)
  → { "model_type": "DEMAND_FORECAST" }

Script cron nocturne (PythonAnywhere Tasks, 02:00 quotidien) :
  /home/<username>/.virtualenvs/gescom-bf/bin/python /home/<username>/gescom-bf/scripts/cron_train_all.py
```

> **Architecture sans Celery/Redis :** Celery et Redis ont été **supprimés** de la stack. L'entraînement à la demande utilise des threads Python natifs (`threading`). Le réentraînement planifié utilise `scripts/cron_train_all.py` via PythonAnywhere Tasks. La révocation JWT utilise la table SQL `token_blocklist` (pas Redis). Le rate limiting utilise Flask-Limiter 3.8.0 avec `storage_uri="memory://"`.

**Types entraînables :**
`DEMAND_FORECAST` · `CREDIT_SCORING` · `ANOMALY_DETECTION` · `ABC_XYZ` · `RFM_SEGMENTATION` · `MARKET_BASKET`

**Cycle de vie d'un modèle :**
```
train() → MLflowRun.__enter__()   → log params/metrics (si MLflow dispo)
       → register_model()         → désactive l'ancien modèle actif
                                  → purge les versions > keep_versions (défaut 3)
                                  → insère le nouveau modèle (is_active=True)
       → record_predictions()     → vide les anciennes prédictions
                                  → insère les nouvelles
       → db.session.commit()
       → MLflowRun.__exit__()     → end_run() MLflow
```

**Purge automatique des anciens modèles :**
```python
# Garder seulement les 3 dernières versions inactives
old_models = MLModel.query.filter_by(model_type=type, is_active=False)
    .order_by(MLModel.trained_at.desc())
    .offset(keep_versions)
    .all()
for old in old_models:
    os.remove(old.artifact_path)  # Supprime le fichier .joblib
    db.session.delete(old)        # Supprime de la base
```

### 11.3 Implémentation frontend

- **Tableau** de tous les modèles : type, version, algorithme, métriques, date, statut (actif/inactif)
- **Bouton "Ré-entraîner"** par type de modèle (visible uniquement avec `ml:train`)
- **Spinner** pendant l'entraînement synchrone
- **Invalidation automatique** des caches React Query après entraînement pour rafraîchir les graphiques

### 11.4 Avantages

- **Traçabilité complète** : chaque prédiction est liée à son modèle via `model_id`, lui-même daté et versionné
- **Non-bloquant** : l'entraînement à la demande s'exécute dans un thread daemon (`threading.Thread`) — le thread WSGI répond immédiatement HTTP 202
- **Planification automatique** : `scripts/cron_train_all.py` tourne chaque nuit à 02:00 via PythonAnywhere Tasks — tous les modèles sont réentraînés sans intervention manuelle
- **Intégration MLflow optionnelle** : si MLflow est déployé, les expériences sont automatiquement loguées ; sinon le code continue sans erreur
- **Purge automatique** : la table `ml_models` ne croît pas indéfiniment

### 11.5 Inconvénients / Limites

- **Threads sans suivi de statut** : un thread daemon ne renvoie pas d'état d'avancement — le frontend doit interroger `/ml/models` pour vérifier la fin de l'entraînement
- **MLflow optionnel** : en production sans MLflow, les métriques ne sont conservées que dans le champ JSON de `ml_models`, sans interface de comparaison graphique des runs

---

## 12. Bilan global — Avantages et limites

### 12.1 Points forts de l'approche

**1. Architecture "Graceful Degradation"**
Chaque module ML dispose d'un algorithme de repli : sklearn absent → naïf saisonnier (forecast), règles (RFM, scoring). Le système ne plante jamais par absence de bibliothèque.

**2. Séparation nette données / modèles / API**
La Feature Store sépare l'ETL de l'entraînement. Les routes Flask ne font que lire la table `predictions` via `latest()` — pas de calcul ML dans les routes.

**3. Pertinence des algorithmes pour le contexte**
Les algorithmes choisis (Isolation Forest, K-Means, LinearRegression) sont légers, interprétables et fonctionnent sur de petits datasets — adapté à une PME burkinabè avec quelques milliers de transactions.

**4. Tracabilité réglementaire**
Le registre `ml_models` avec version, algorithme, métriques et date répond aux exigences de gouvernance des données (RNF-17).

**5. Interface utilisateur riche**
9 onglets avec graphiques Recharts interactifs, filtres, tableaux paginés — tout dans une seule page sans navigation entre routes.

---

### 12.2 Limites et axes d'amélioration

**1. Données d'entraînement simulées**
Le `taux_retard` du scoring crédit est dérivé par hash faute d'historique réel. Les prédictions ML sont partiellement fondées sur des données artificielles — acceptable en phase de démarrage, mais à remplacer dès que l'historique est suffisant.

**2. ✅ Réentraînement automatique planifié**
`scripts/cron_train_all.py` est planifié via PythonAnywhere Tasks (quotidien à 02:00) — tous les modèles sont réentraînés automatiquement. L'entraînement à la demande utilise des threads Python natifs sans bloquer le WSGI.

**3. Performances sur grand volume**
L'analyse de cohortes et le CLV chargent toutes les ventes en mémoire Python. Pour une base de 100 000+ transactions, ces calculs seront lents — une matérialisation via vues SQL ou tâches asynchrones serait nécessaire.

**4. Absence de feedback loop**
Aucun mécanisme ne permet à l'utilisateur de confirmer ou d'infirmer une anomalie, un segment ou un score. Sans feedback, l'amélioration des modèles n'est pas possible de façon supervisée.

**5. ✅ Prévision enrichie avec Prophet et contexte africain**
Prophet (avec calendrier de fêtes burkinabè : Tabaski, Ramadan, Indépendance, Noël) est **implémenté et actif** pour les séries ≥30 jours. Les features africaines (saison des pluies, semaine de paie, rentrée scolaire) enrichissent également la régression linéaire. L'endpoint `/analytics/african-context` expose le contexte calendaire actif.

---

### 12.3 Tableau récapitulatif

| Fonctionnalité | Algorithme principal | Repli | Dépendance | Données d'entrée |
|---------------|---------------------|-------|-----------|-----------------|
| Dashboard analytique | SQL agrégé | — | Aucune | `sales`, `sale_lines`, `products` |
| Prévisions de demande | Prophet + features africaines | LinearRegression → Naïf saisonnier | prophet, scikit-learn | `sale_lines` (6 mois) |
| ABC/XYZ | Règles pandas | — | pandas | `sale_lines` (6 mois) |
| Segmentation RFM | K-Means (k optimal Silhouette/Elbow) | Quartiles | scikit-learn | `sales` (12 mois) |
| Churn Probability | Décroissance exponentielle RFM | — | numpy | `predictions` RFM |
| Scoring crédit | Random Forest + SHAP | Règles pondérées | scikit-learn, shap | `customers`, `sales` |
| Détection anomalies | Isolation Forest | Z-Score | scikit-learn | `sales` (90 jours) |
| Market Basket Analysis | Apriori (mlxtend) | Co-occurrence paires | mlxtend | `sale_lines` (6 mois) |
| Élasticité des remises | Régression log-log | Comparaison moyennes | scikit-learn | `sale_lines` (6 mois) |
| Cohortes clients | Calcul Python | — | Aucune | `sales` (N mois) |
| CLV | Formule heuristique + `data_confidence` | — | Aucune | `sales` agrégées |
| Registre ML | Registre BDD | — | MLflow (opt.), Sentry (opt.) | `ml_models` |

---

*Document généré pour la soutenance du projet GesCom-BF*  
*Dernière mise à jour : 1er juillet 2026 — conformité code v2 post-corrections soutenance.*
