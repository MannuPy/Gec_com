# 19. Module Analyse de données — Vue d'ensemble

> **Dernière mise à jour :** 19 juin 2026 — reflète l'état réel du code implémenté.

## 19.1 Positionnement

Ce module constitue le **cœur différenciant** de GesCom-BF. Il transforme les données opérationnelles (ventes, stocks, clients) en aide à la décision actionnable pour l'administrateur. Il répond à l'option "Analyse de données" du mémoire.

## 19.2 Modules analytiques implémentés

| Module | Technique | Fichier | État |
|---|---|---|---|
| Classification ABC/XYZ | Règles pandas (déterministe) | `ml/abc_xyz.py` | ✅ Production |
| Prévision de demande + alertes rupture | Seasonal Naive → sklearn → Prophet+XGBoost | `ml/demand_forecast.py` | ✅ Production |
| Scoring crédit client | Rule-based → Random Forest + LogReg CV | `ml/credit_scoring.py` | ✅ Production |
| Segmentation RFM | Quantiles → K-Means 4 clusters | `ml/rfm_segmentation.py` | ✅ Production |
| Détection d'anomalies | Z-score → Isolation Forest | `ml/anomaly_detection.py` | ✅ Production |
| Analyse de cohortes clients | Calcul direct SQL + Python | `blueprints/analytics/routes.py` | ✅ Production |
| Customer Lifetime Value (CLV) | Formule heuristique | `blueprints/analytics/routes.py` | ✅ Production |
| Dashboard temps réel | SSE / Polling 15s | `services/analytics_service.py` | ✅ Production |
| Comparatif inter-succursales | Normalisation 0-100 + Radar | `blueprints/reports/routes.py` | ✅ Production |
| Tendance des ventes | Agrégation SQL journalière | `services/analytics_service.py` | ✅ Production |

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
