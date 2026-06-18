/**
 * Types du blueprint `analytics` : dashboard avancé, prévisions, IA/ML
 * (RF-24 à RF-29). Cf. backend/app/blueprints/analytics/routes.py et
 * backend/app/blueprints/analytics/schemas.py.
 */

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
  reference: string;
  branch_id: string;
  cashier_name: string;
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
  cv: number;
  xyz_class: XyzClass;
  combined_class: string;
}

export interface AbcXyzParams {
  abc_class?: AbcClass | string;
  xyz_class?: XyzClass | string;
}

// ---------------------------------------------------------------------------
// RF-26 : segmentation RFM des clients
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
}

export interface RfmSegmentParams {
  segment?: string;
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
  task_id?: string;
}

// ---------------------------------------------------------------------------
// Enveloppes génériques `{ items, count }` utilisées par plusieurs endpoints
// ---------------------------------------------------------------------------

export interface AnalyticsItemsResponse<T> {
  items: T[];
  count: number;
}
