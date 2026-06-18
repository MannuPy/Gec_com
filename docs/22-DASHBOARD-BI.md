# 22. Dashboard BI / Tableau de bord décisionnel

## 22.1 Objectifs du tableau de bord

- Donner à l'administrateur une **vue temps réel** de l'activité (ventes, stock, marges) consolidée et par boutique.
- Afficher les **alertes IA** (ruptures prévues, anomalies, clients à risque) de façon actionnable.
- Permettre l'**export PDF** des rapports pour archivage / présentation (RF-29).

## 22.2 Architecture temps réel

```mermaid
flowchart LR
    A[Tâches Celery\n(prévisions, anomalies)] -->|publish| B[(Redis pub/sub)]
    B -->|subscribe| C[API Flask\nWebSocket Gateway]
    C -->|push| D[Dashboard React]
    D -->|GET initial| E[API REST /reports/dashboard]
    E --> F[(PostgreSQL)]
```

- **Chargement initial** : appel REST classique (`GET /reports/dashboard`) pour l'état courant.
- **Mises à jour live** : WebSocket pour les alertes (nouvelle anomalie, rupture imminente) — évite le polling et respecte RNF-01 (latence < 2s annoncée pour le rafraîchissement).

## 22.3 Sections du tableau de bord

| Section | Contenu | Source |
|---|---|---|
| **KPIs globaux** | CA du jour/mois, marge brute, nombre de ventes, panier moyen | `sales`, `sale_lines` agrégés |
| **Performance par boutique** | CA, marge, top 5 produits par boutique | Agrégation par `branch_id` |
| **Alertes stock** | Liste des produits en rupture imminente (7/14/30j) avec quantité recommandée | `predictions` (type RUPTURE_STOCK) |
| **Alertes anomalies** | Liste des transactions signalées (remise suspecte, vente atypique) | `predictions` (type ANOMALIE), WebSocket temps réel |
| **Crédit clients** | Top clients à risque (score faible), encours total | `customers`, `predictions` (type CREDIT_SCORE) |
| **ABC/XYZ** | Répartition des produits par classe, valeur immobilisée | `predictions` (type ABC_XYZ) |
| **Segmentation client (RFM)** | Répartition des segments, actions recommandées | Feature store `fs_customer_rfm` |

## 22.4 Maquette du dashboard (description — wireframe détaillé en `29-WIREFRAMES-UI.md`)

```text
┌─────────────────────────────────────────────────────────────────┐
│ GesCom-BF        [Entreprise X]      🔔 3 alertes    👤 Admin     │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                  │
│ │ CA jour │ │ CA mois │ │ Marge   │ │ Panier  │   KPIs globaux    │
│ │ 850 000 │ │18 500000│ │ 22,4 %  │ │ moyen   │                   │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘                  │
├─────────────────────────────────────────────────────────────────┤
│ Évolution CA (30j)              │  Alertes IA (temps réel)        │
│ [Graphique courbes par boutique]│  ⚠ Rupture J+5 : Vis 6mm (B.2)  │
│                                  │  ⚠ Remise 20% non approuvée     │
│                                  │  ⚠ Client K. score faible (32)  │
├─────────────────────────────────────────────────────────────────┤
│ Classification ABC/XYZ           │ Segmentation clients (RFM)      │
│ [Treemap / barres par classe]    │ [Diagramme en secteurs]         │
└─────────────────────────────────────────────────────────────────┘
```

## 22.5 Endpoint de référence

```yaml
/reports/dashboard:
  get:
    summary: Données consolidées du tableau de bord
    responses:
      '200':
        content:
          application/json:
            schema:
              type: object
              properties:
                kpis:
                  type: object
                  properties:
                    ca_jour: { type: number }
                    ca_mois: { type: number }
                    marge_pct: { type: number }
                    panier_moyen: { type: number }
                alerts:
                  type: array
                  items:
                    type: object
                    properties:
                      type: { type: string, enum: [RUPTURE_STOCK, ANOMALIE, CREDIT_RISK] }
                      severity: { type: string, enum: [INFO, WARNING, CRITICAL] }
                      message: { type: string }
                      entity_id: { type: string, format: uuid }
                abc_xyz: { type: array, items: { type: object } }
                rfm_segments: { type: array, items: { type: object } }
```

## 22.6 Export PDF des rapports (RF-29)

| Rapport exportable | Contenu |
|---|---|
| Rapport de ventes (période, boutique) | CA, marges, top produits, comparaison période précédente |
| Rapport de stock | Stock par site, valeur immobilisée, produits sous seuil |
| Rapport ABC/XYZ | Classification + recommandations de réapprovisionnement |
| Rapport d'audit | Journal filtré (événements, période) |

Génération via le service `reports/export_service.py` utilisant **WeasyPrint** (HTML → PDF) à partir de templates Jinja2, exécutée en tâche Celery pour les exports volumineux (notification par email/lien de téléchargement à la fin).

## 22.7 Visualisations recommandées (bibliothèques)

| Visualisation | Librairie | Données |
|---|---|---|
| Courbes d'évolution CA/marge | Recharts | `sales` agrégées par jour |
| Treemap ABC/XYZ | D3.js | `predictions` (ABC_XYZ) |
| Diagramme en secteurs RFM | Recharts | `fs_customer_rfm` |
| Jauge de couverture stock | Recharts (RadialBarChart) | `stock` vs `predictions` (RUPTURE_STOCK) |
| Flux d'alertes temps réel | Liste avec WebSocket | `predictions` (ANOMALIE), Redis pub/sub |
