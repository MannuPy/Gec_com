/** Cf. backend/app/blueprints/reports/routes.py (dashboard_summary). */
export interface TopProduct {
  product_id: string;
  name: string;
  sku: string;
  quantity_sold: number;
}

export interface DashboardSummary {
  sales_today_total: string;
  sales_today_count: number;
  average_basket: string;
  low_stock_count: number;
  top_products_today: TopProduct[];
}

/**
 * Tableau de bord temps reel (RF-24/RF-28/RF-26/RF-25, doc 22-DASHBOARD-BI.md
 * §22.2/§22.5, adapte en SSE/polling). Cf. backend
 * app/services/analytics_service.py:compute_dashboard_realtime et
 * GET /reports/dashboard/realtime | /reports/dashboard/stream.
 */
export type DashboardAlertType = "RUPTURE_STOCK" | "ANOMALIE" | "CREDIT_RISK";
export type DashboardAlertSeverity = "INFO" | "WARNING" | "CRITICAL";

export interface DashboardAlert {
  type: DashboardAlertType;
  severity: DashboardAlertSeverity;
  message: string;
  entity_id: string | null;
}

export interface DashboardRealtimeKpis {
  ca_jour: string;
  ca_mois: string;
  marge_pct: number;
  panier_moyen: string;
}

/** Cf. app/ml/abc_xyz.py:latest() */
export interface AbcXyzEntry {
  product_id: string;
  model_id: string;
  created_at: string;
  product_sku: string;
  product_name: string;
  revenue: number;
  abc_class: "A" | "B" | "C";
  cv: number;
  xyz_class: "X" | "Y" | "Z";
  combined_class: string;
}

/** Cf. app/ml/rfm_segmentation.py:latest() */
export interface RfmSegmentEntry {
  customer_id: string;
  model_id: string;
  created_at: string;
  customer_name: string | null;
  recency_days: number;
  frequency: number;
  monetary: number;
  segment: string;
  segment_label: string;
  recommended_action: string;
}

export interface DashboardRealtime {
  generated_at: string;
  kpis: DashboardRealtimeKpis;
  alerts: DashboardAlert[];
  abc_xyz: AbcXyzEntry[];
  rfm_segments: RfmSegmentEntry[];
}
