# 22. Dashboard BI — Tableaux de bord décisionnels

> **Dernière mise à jour :** 1er juillet 2026 — mise à jour conformité code v2.

## 22.1 Vue d'ensemble

GesCom-BF expose **4 tableaux de bord** distincts :

| Dashboard | Audience | URL Frontend | Endpoints Backend |
|---|---|---|---|
| Tableau de bord principal | ADMIN | `/` (DashboardPage) | `GET /reports/dashboard` + `/realtime` |
| Analytique avancé | ADMIN | `/analytique` (AnalyticsPage) | `GET /analytics/*` |
| Performance vendeur | VENDEUR | `/mon-tableau-de-bord` (VendeurDashboardPage) | `GET /reports/vendeur/dashboard` |
| Comparatif succursales | ADMIN | `/comparatif` (BranchComparePage) | `GET /reports/branches/compare` |

## 22.2 Dashboard principal — Données du jour

### Endpoint statique (indicateurs du jour)

`GET /api/v1/reports/dashboard`

```json
{
  "sales_today_total": "2450000",
  "sales_today_count": 18,
  "average_basket": "136111",
  "low_stock_count": 7,
  "top_products_today": [
    { "product_id": "uuid", "name": "Ciment 50kg", "sku": "CIM-50", "quantity_sold": 24 }
  ]
}
```

### Endpoint temps réel (KPIs + alertes IA + ML)

`GET /api/v1/reports/dashboard/realtime`

```json
{
  "generated_at": "2024-06-15T14:32:00",
  "kpis": {
    "ca_jour": "2450000", "ca_mois": "48200000",
    "marge_pct": 18.5, "panier_moyen": "136111"
  },
  "alerts": [
    { "type": "RUPTURE_STOCK", "severity": "CRITICAL", "message": "...", "entity_id": "..." },
    { "type": "ANOMALIE",      "severity": "WARNING",  "message": "...", "entity_id": "..." },
    { "type": "CREDIT_RISK",   "severity": "WARNING",  "message": "...", "entity_id": "..." }
  ],
  "abc_xyz": [...],
  "rfm_segments": [...]
}
```

## 22.3 Architecture SSE / Polling (RF-24)

### Flux SSE (mode normal)

`GET /api/v1/reports/dashboard/stream`

- Connexion via `fetch()` (pas `EventSource`) pour envoyer le header `Authorization: Bearer <token>`
- Chaque 30 secondes : snapshot `compute_dashboard_realtime()` → événement SSE `data: {json}`
- Reconnexion automatique après 5 secondes si connexion fermée

### Mode PythonAnywhere (DISABLE_SSE=true)

- Le serveur envoie : `event: sse-disabled\ndata: {}\n\n` puis un snapshot unique
- Le frontend détecte `sse-disabled` → bascule sur polling `GET /realtime` toutes les 15 secondes
- Compatible environnement mono-worker PythonAnywhere

### Protection React 18 Strict Mode

```typescript
// Variable de closure LOCALE (pas useRef) pour éviter les doubles connexions :
let isActive = true;   // propre à chaque invocation de useEffect
```

## 22.4 Dashboard vendeur — Performance individuelle

`GET /api/v1/reports/vendeur/dashboard` (JWT → cashier_id auto)

```json
{
  "cashier": { "id": "uuid", "full_name": "Idrissa Kaboré", "branch_name": "Boutique Nord" },
  "kpis_jour": { "ca_jour": 145000, "nb_ventes": 8, "panier_moyen": 18125 },
  "kpis_mois": { "ca_mois": 3250000, "nb_ventes": 142, "commission_estimee": 65000 },
  "progression_objectif_pct": 65.0,
  "historique_par_heure": [{"heure": 8, "ca": 45000}],
  "top_produits_mois": [...],
  "dernieres_ventes": [...]
}
```

**Config :** `COMMISSION_RATE` (2% par défaut), `VENDEUR_MONTHLY_TARGET` (500 000 FCFA par défaut)

## 22.5 Dashboard analytique étendu (`/analytique`)

Page `AnalyticsPage.tsx` avec **12 onglets** :

| Onglet | Endpoint | Visualisation |
|---|---|---|
| Vue d'ensemble | `/analytics/dashboard` + `/sales-trend` | AreaChart tendance CA, BarChart top produits |
| Prévisions demande | `/analytics/forecast` | Tableau alertes rupture + quantité recommandée + `data_confidence` |
| Scoring crédit | `/analytics/credit-scores` + `/analytics/credit-scores/<id>/explain` | Tableau score coloré + BarChart distribution + SHAP explicabilité (détail par client) |
| Anomalies | `/analytics/anomalies` | Tableau ventes signalées + raisons enrichies (10+ règles) |
| ABC/XYZ | `/analytics/abc-xyz` | Tableau + BarChart CA par classe *(analytique BI)* |
| Segmentation RFM | `/analytics/rfm-segments` + `/analytics/rfm-segments/evaluate-k` | Tableau + BarChart — 4 segments toujours affichés (actif/inactif) ; `evaluate-k` retourne scores Silhouette/Elbow pour choix K optimal |
| Churn Risk | `/analytics/churn-risk` | Tableau probabilité de churn + niveau de risque + action recommandée |
| Market Basket | `/analytics/basket` | Tableau règles d'association (support/confiance/lift) |
| Élasticité prix | `/analytics/price-elasticity` | Tableau élasticité + recommandation tarifaire |
| Contexte africain BF | `/analytics/african-context` | KPIs : saison pluies, weekend boost, stress trésorerie, crédit informel |
| Modèles ML | `/analytics/ml/models` | Registre avec métriques et algorithmes |
| Cohortes + CLV | `/analytics/cohorts` + `/analytics/clv` | Heatmap rétention + top 10 CLV |

## 22.6 Comparatif inter-succursales (`/comparatif`)

`GET /api/v1/reports/branches/compare?date_debut=2024-01-01&date_fin=2024-06-30`

**Visualisations (BranchComparePage.tsx) :**

- **RadarChart Recharts** : 5 axes normalisés 0-100 (CA, Nb ventes, Panier moyen, Marge %, Clients actifs) — une courbe par succursale, couleurs distinctives
- **BarChart CA/Marge** : côte à côte par succursale
- **BarChart évolution mensuelle** : CA mensuel par succursale
- **Cards KPI** : par succursale avec couleur dédiée
- **Tableau récapitulatif** : marge_pct colorée (vert ≥ 20%, ambre ≥ 10%, rouge < 10%)

## 22.7 Bibliothèque graphique — Recharts

| Composant Recharts | Utilisé pour |
|---|---|
| `<AreaChart>` | Tendance ventes, historique heure par heure vendeur |
| `<BarChart>` | ABC/XYZ, top produits, RFM, CLV, évolution mensuelle |
| `<RadarChart>` | Comparatif inter-succursales (5 axes normalisés) |
| `<PieChart>` | Répartition par segment (optionnel) |

**Particularités TypeScript Recharts :**
- `formatter={(v) => [fmt(v as number), "CA"]}` — cast explicite requis
- `labelFormatter={(label) => fmtHeure(label as number)}` — cast requis

## 22.8 React Query — Chargement différé

Chaque onglet de l'AnalyticsPage charge ses données uniquement quand il est sélectionné :

```typescript
const cohortsQuery = useQuery({
  queryKey: ["analytics", "cohorts", { months }],
  queryFn: () => analyticsApi.cohorts({ months }),
  enabled: tab === "cohorts",   // ← lazy loading
  staleTime: 300_000,           // 5 minutes de fraîcheur
});
```

## 22.9 Codage couleur standardisé

| Contexte | Couleur | Seuil |
|---|---|---|
| Risque crédit FAIBLE / classe A / Marge OK | Vert `green-*` | Score ≥ 71, marge ≥ 20% |
| Risque MOYEN / classe B | Ambre `amber-*` | Score 41-70, marge ≥ 10% |
| Risque ÉLEVÉ / classe C | Rouge `red-*` | Score ≤ 40, marge < 10% |
| Rétention cohorte M+0 | Indigo | 100% (référence) |
| CLV estimée | Indigo `indigo-700` | — |

## 22.10 Permissions RBAC

| Dashboard | Permission | Rôles |
|---|---|---|
| Dashboard principal | `reports:read` | ADMIN |
| Analytique + ML | `analytics:read` | ADMIN |
| Dashboard vendeur | `reports:read` (propre au JWT) | VENDEUR, ADMIN |
| Comparatif succursales | `reports:read` | ADMIN |
| Cohortes + CLV | `analytics:read` | ADMIN |
