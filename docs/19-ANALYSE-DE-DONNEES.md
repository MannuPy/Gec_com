# 19. Module Analyse de données — Vue d'ensemble

> **Dernière mise à jour :** 1er juillet 2026 — mise à jour conformité code v2.

## 19.1 Positionnement

Ce module constitue le **cœur différenciant** de GesCom-BF. Il transforme les données opérationnelles (ventes, stocks, clients) en aide à la décision actionnable pour l'administrateur. Il répond à l'option "Analyse de données" du mémoire.

## 19.2 Modules analytiques implémentés

| Module | Catégorie | Technique | Fichier | État |
|---|---|---|---|---|
| Classification ABC/XYZ | **Analytique BI** | Règles pandas déterministes (cumsum CA + CV) | `ml/abc_xyz.py` | ✅ Production |
| Prévision de demande | **ML supervisé** | Seasonal Naive → sklearn → Prophet (jours fériés BF) — avec `data_confidence` | `ml/demand_forecast.py` | ✅ Production |
| Scoring crédit client | **ML supervisé** | Rule-based → Random Forest + LogReg CV + **SHAP TreeExplainer** | `ml/credit_scoring.py` | ✅ Production |
| Segmentation RFM | **ML non supervisé** | Quantiles → K-Means auto-k (Silhouette/Elbow) — 4 segments toujours présents | `ml/rfm_segmentation.py` | ✅ Production |
| Probabilité de churn | **Heuristique statistique** | Décroissance exponentielle P=1-exp(-λ×R) — pas de ML | `ml/rfm_segmentation.py` | ✅ Production |
| Détection d'anomalies | **ML non supervisé** | Z-score → Isolation Forest + raisons enrichies (10+ règles) | `ml/anomaly_detection.py` | ✅ Production |
| Market Basket Analysis | **ML non supervisé** | Co-occurrence → Apriori (mlxtend) + règles d'association | `ml/market_basket.py` | ✅ Production |
| Élasticité prix | **Analytique statistique** | Régression log-log (ln(qty) ~ ln(price)) par produit | `services/price_elasticity_service.py` | ✅ Production |
| Indicateurs contexte africain BF | **Analytique BI** | Calcul temps réel (saison pluies, weekend boost, stress trésorerie, crédit informel) | `blueprints/analytics/routes.py` | ✅ Production |
| Analyse de cohortes clients | **Analytique BI** | Calcul direct SQL + Python | `blueprints/analytics/routes.py` | ✅ Production |
| Customer Lifetime Value (CLV) | **Heuristique** | Formule heuristique (panier moyen × fréquence × 24 mois) | `blueprints/analytics/routes.py` | ✅ Production |
| Dashboard temps réel | **BI** | SSE / Polling 15s | `services/analytics_service.py` | ✅ Production |
| Tendance des ventes | **Analytique BI** | Agrégation SQL journalière | `services/analytics_service.py` | ✅ Production |

## 19.3 Source des données

| Source | Tables | Fréquence de rafraîchissement |
|---|---|---|
| Historique des ventes | `sales`, `sale_lines` | Continue (ETL incrémental quotidien) |
| Mouvements de stock | `stock`, `stock_movements` | Continue |
| Clients | `customers`, `customer_payments` | À chaque transaction |
| Feature Store | `fs_daily_sales`, `fs_customer_rfm`, `fs_customer_credit_features`, `fs_transaction_features` | Quotidienne (pipeline ETL) |

## 19.4 Pipeline global

```
Données opérationnelles
    ↓
Pipeline ETL (etl_service.py)
    ↓
Feature Store (4 tables fs_*)
    ↓
Modules ML (app/ml/*.py)  ←── Repli si dépendances absentes
    ↓
Registre modèles (ml_models) + Prédictions (predictions)
    ↓
API REST (/analytics/* et /reports/*)
    ↓
Frontend AnalyticsPage + DashboardPage
```

## 19.5 Référence croisée

Pour la documentation exhaustive de chaque module :

- **Algorithmes ML, implémentation, formules :** `docs/ANALYTIQUE-ML-IA-COMPLET.md`
- **Modèles de données :** `docs/20-MACHINE-LEARNING.md`
- **Pipeline ETL :** `docs/21-PIPELINE-ETL.md`
- **Dashboard BI :** `docs/22-DASHBOARD-BI.md`
- **API REST :** `docs/17-API-REST.md`
