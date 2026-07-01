/**
 * Types du blueprint `analytics` : dashboard avancé, prévisions, IA/ML
 * (RF-24 à RF-29). Cf. backend/app/blueprints/analytics/routes.py et
 * backend/app/blueprints/analytics/schemas.py.
 */

// ---------------------------------------------------------------------------
// RF-24 : tendance des ventes (séries temporelles)
// ---------------------------------------------------------------------------

export interface SalesTrendItem {
  date: string;       // "YYYY-MM-DD"
  revenue: number;
  sales_count: number;
  margin: number;
}

// ---------------------------------------------------------------------------
// RF-24 : tableau de bord étendu (marges, multi-site, consolidé)
// ---------------------------------------------------------------------------

export interface BranchAnalytics {
  branch_id: string;
  branch_name: string;
  sales_count: number;
  revenue: string;
  cost: string;
  margin: string;
  margin_rate_pct: number;
}

export interface ConsolidatedAnalytics {
  sales_count: number;
  revenue: string;
  cost: string;
  margin: string;
  margin_rate_pct: number;
}

export interface AdvancedDashboard {
  period_days: number;
  period_start: string;
  branches: BranchAnalytics[];
  consolidated: ConsolidatedAnalytics;
}

export interface AdvancedDashboardParams {
  branch_id?: string;
  days?: number;
}

// ---------------------------------------------------------------------------
// RF-25 : prévisions de demande / alertes de rupture de stock (RG-38)
// ---------------------------------------------------------------------------

export interface DemandForecastItem {
  product_id: string;
  branch_id: string;
  product_sku: string;
  product_name: string;
  forecast_7d: number;
  forecast_30d: number;
  stock_disponible: number;
  seuil_min: number;
  stock_prevu_j7: number;
  alerte_rupture: boolean;
  quantite_recommandee: number;
  algorithm: string;
  /** Fiabilité de la prévision : "HIGH" | "MEDIUM" | "LOW" (basé sur la taille de l'historique) */
  data_confidence: "HIGH" | "MEDIUM" | "LOW" | null;
}

export interface DemandForecastParams {
  alerts_only?: boolean;
  branch_id?: string;
  product_id?: string;
}

// ---------------------------------------------------------------------------
// RF-27 : scoring crédit des clients
// ---------------------------------------------------------------------------

export const CREDIT_RISK_LEVELS = ["ELEVE", "MOYEN", "FAIBLE"] as const;
export type CreditRiskLevel = (typeof CREDIT_RISK_LEVELS)[number];

export interface CreditScoreItem {
  customer_id: string;
  customer_name: string;
  score: number;
  risk_level: CreditRiskLevel;
  nb_achats_credit_total: number;
  montant_moyen_achat: number;
  delai_moyen_remboursement_jours: number;
  taux_retard: number;
  anciennete_client_mois: number;
  frequence_achat_mensuelle: number;
  solde_du_actuel: number;
}

export interface CreditScoreParams {
  risk_level?: CreditRiskLevel | string;
  customer_id?: string;
}

// ---------------------------------------------------------------------------
// RF-28 : détection d'anomalies sur les ventes
// ---------------------------------------------------------------------------

export interface AnomalyItem {
  sale_id: string;
  reference: string | null;     // peut être null si la vente n'a pas de référence
  branch_id: string;
  cashier_name: string | null;  // peut être null si le caissier a été supprimé
  montant_total: number;
  remise_taux: number;
  score: number;
  reasons: string[];
}

export interface AnomalyParams {
  branch_id?: string;
}

// ---------------------------------------------------------------------------
// RF-26 : classification ABC/XYZ des produits
// ---------------------------------------------------------------------------

export const ABC_CLASSES = ["A", "B", "C"] as const;
export type AbcClass = (typeof ABC_CLASSES)[number];

export const XYZ_CLASSES = ["X", "Y", "Z"] as const;
export type XyzClass = (typeof XYZ_CLASSES)[number];

export interface AbcXyzItem {
  product_id: string;
  product_sku: string;
  product_name: string;
  revenue: number;
  abc_class: AbcClass;
  cv: number | null;
  xyz_class: XyzClass;
  combined_class: string;
  dead_stock: boolean;
}

export interface AbcXyzParams {
  abc_class?: AbcClass | string;
  xyz_class?: XyzClass | string;
}

// ---------------------------------------------------------------------------
// RF-26 : segmentation RFM des clients + churn heuristique
// ---------------------------------------------------------------------------

export interface RfmSegmentItem {
  customer_id: string;
  customer_name: string;
  recency_days: number;
  frequency: number;
  monetary: number;
  segment: string;
  segment_label: string;
  recommended_action: string;
  // Churn heuristique (P = 1 - exp(-λ×R))
  churn_probability: number;
  churn_risk: "HIGH" | "MEDIUM" | "LOW";
  churn_action: string;
}

export interface RfmSegmentSummary {
  segment: string;
  label: string;
  recommended_action: string;
  count: number;
  active: boolean;
}

export interface RfmSegmentsResponse {
  items: RfmSegmentItem[];
  count: number;
  segment_summary: RfmSegmentSummary[];
  segments_actifs: string[];
}

export interface RfmSegmentParams {
  segment?: string;
}

// ---------------------------------------------------------------------------
// Churn risk — endpoint dédié /analytics/churn-risk
// ---------------------------------------------------------------------------

export interface ChurnRiskResponse {
  items: RfmSegmentItem[];
  count: number;
  min_probability: number;
}

// ---------------------------------------------------------------------------
// Market Basket Analysis — /analytics/basket (RF-26)
// ---------------------------------------------------------------------------

export interface MarketBasketRule {
  antecedents: string[];
  consequents: string[];
  support: number;
  confidence: number;
  lift: number;
  branch_id?: string | null;
}

export interface MarketBasketResponse {
  items: MarketBasketRule[];
  count: number;
}

// ---------------------------------------------------------------------------
// Élasticité prix — /analytics/price-elasticity
// ---------------------------------------------------------------------------

export interface PriceElasticityItem {
  product_id: string;
  product_name: string;
  elasticity: number | null;
  r_squared: number | null;
  interpretation: string;
  discount_policy_recommendation: string;
  data_points: number;
}

export interface PriceElasticityResponse {
  items: PriceElasticityItem[];
  count: number;
  diagnostic: string | null;
}

// ---------------------------------------------------------------------------
// Contexte africain BF — /analytics/african-context
// ---------------------------------------------------------------------------

export interface AfricanContextEvent {
  event: string;
  label: string;
  impact: string;
  stock_recommendation: string;
  active: boolean;
}

export interface WeekendBoostInfo {
  actif: boolean;
  jour: string;
  boost_estime_pct: number;
  recommandation: string;
}

export interface StressInfo {
  indice_stress_tresorerie: number | null;
  niveau: "LOW" | "MEDIUM" | "HIGH" | "UNKNOWN";
  label: string;
  taux_retard_pct?: number;
  paiements_analyses?: number;
  recommandation: string;
}

export interface CreditInformelInfo {
  propension_credit_informel: number | null;
  pct?: number;
  clients_actifs_90j?: number;
  clients_sans_historique_formel?: number;
  interpretation: string;
}

export interface AfricanContextResponse {
  date: string;
  active_contexts: AfricanContextEvent[];
  count: number;
  weekend_boost: WeekendBoostInfo;
  stress_tresorerie: StressInfo;
  credit_informel: CreditInformelInfo;
  saison_pluies: boolean;
}

// ---------------------------------------------------------------------------
// Évaluation K optimal — /analytics/rfm-segments/evaluate-k
// ---------------------------------------------------------------------------

export interface KMeansEvaluation {
  k: number;
  silhouette: number | null;
  davies_bouldin_index: number | null;
  inertia: number | null;
}

export interface RfmEvaluateKResponse {
  optimal_k: number;
  evaluation: KMeansEvaluation[];
  n_clients: number;
  interpretation?: string;
}

// ---------------------------------------------------------------------------
// Registre des modèles ML (RNF-17, RG-40) + entraînement (RF-29)
// ---------------------------------------------------------------------------

export const ML_MODEL_TYPES = [
  "DEMAND_FORECAST",
  "CREDIT_SCORING",
  "ANOMALY_DETECTION",
  "ABC_XYZ",
  "RFM_SEGMENTATION",
  "MARKET_BASKET",
] as const;
export type MlModelType = (typeof ML_MODEL_TYPES)[number];

export interface MlModel {
  id: string;
  model_type: MlModelType | string;
  version: string;
  algorithm: string;
  metrics: Record<string, unknown> | null;
  mlflow_run_id: string | null;
  trained_at: string;
  is_active: boolean;
}

export interface MlTrainResult {
  status: "completed" | "queued";
  model_type: string;
  result?: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Enveloppe generique pour les listes paginées renvoyées par l'API analytics
// (ex. /analytics/forecast, /analytics/credit-scores, /analytics/abc-xyz)
// ---------------------------------------------------------------------------

export interface AnalyticsItemsResponse<T> {
  items: T[];
  total?: number;
}

// ---------------------------------------------------------------------------
// Feature E — Analyse de cohortes clients
// ---------------------------------------------------------------------------

export interface CohortRetentionPoint {
  month: number;
  month_label: string;
  count: number;
  rate: number;
}

export interface Cohort {
  cohort: string;
  size: number;
  retention: CohortRetentionPoint[];
}

export interface CohortAnalysis {
  cohorts: Cohort[];
  max_months: number;
}

// ---------------------------------------------------------------------------
// Feature F — Customer Lifetime Value (CLV)
// ---------------------------------------------------------------------------

export interface ClvItem {
  customer_id: string;
  name: string;
  customer_type: string;
  nb_commandes: number;
  ca_total: number;
  panier_moyen: number;
  premier_achat: string | null;
  dernier_achat: string | null;
  duree_mois: number;
  frequence_mensuelle: number;
  clv_estime: number;
  duree_vie_estimee_mois: number;
  data_confidence: number | null;
}

export interface ClvStats {
  clv_moyen: number;
  clv_median: number;
  clv_max: number;
  clv_min: number;
}

export interface ClvResponse {
  items: ClvItem[];
  count: number;
  stats: ClvStats;
}
