/**
 * Types du blueprint `inventory` : inventaire physique (RF-21 à RF-23).
 * Cf. backend/app/blueprints/inventory/schemas.py et routes.py.
 */

export const STOCK_COUNT_STATUSES = ["EN_COURS", "VALIDE", "ANNULE"] as const;
export type StockCountStatus = (typeof STOCK_COUNT_STATUSES)[number];

export interface StockCountLine {
  id: string;
  product_id: string;
  product_sku: string;
  product_name: string;
  theoretical_quantity: number;
  counted_quantity: number | null;
  variance: number | null;
  variance_pct: number | null;
  comment: string | null;
}

export interface StockCount {
  id: string;
  reference: string;
  branch_id: string;
  branch_name: string;
  status: StockCountStatus;
  created_by_id: string;
  created_by_name: string;
  validated_by_id: string | null;
  validated_by_name: string | null;
  validated_at: string | null;
  cancelled_by_id: string | null;
  cancelled_by_name: string | null;
  created_at: string;
  lines_count: number;
  lines_with_variance: number;
}

export interface StockCountDetail extends StockCount {
  lines: StockCountLine[];
  adjustments_applied?: number;
}

export interface StockCountListParams {
  branch_id?: string;
  status?: StockCountStatus | string;
  page?: number;
  per_page?: number;
}

export interface StockCountCreatePayload {
  branch_id: string;
}

export interface StockCountLineUpdate {
  product_id: string;
  counted_quantity: number;
  comment?: string;
}

exp