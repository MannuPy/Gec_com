/** Cf. backend/app/blueprints/sales/schemas.py */

export const PAYMENT_TYPES = ["CASH", "CREDIT"] as const;
export type PaymentType = (typeof PAYMENT_TYPES)[number];

/** Taux de remise autorises (RG-22). Cf. backend/app/config.py ALLOWED_DISCOUNT_RATES. */
export const ALLOWED_DISCOUNT_RATES = [0, 5, 10, 15, 20] as const;

/** Seuil a partir duquel une approbation est requise (RG-23). */
export const DISCOUNT_APPROVAL_THRESHOLD = 10;

export const SALE_STATUSES = [
  "VALIDEE",
  "ANNULEE",
  "AVOIR_EMIS",
  "EN_ATTENTE_SYNC",
  "EN_CONFLIT",
  "EN_ATTENTE_APPROBATION",
] as const;
export type SaleStatus = (typeof SALE_STATUSES)[number];

export interface SaleLineCreate {
  product_id: string;
  quantity: number;
}

export interface SaleCreatePayload {
  branch_id: string;
  customer_id?: string | null;
  payment_type?: PaymentType;
  discount_rate?: number;
  approved_by_id?: string | null;
  lines: SaleLineCreate[];
}

export interface RefundLinePayload {
  product_id: string;
  quantity: number;
}

export interface RefundCreatePayload {
  lines: RefundLinePayload[];
  reason: string;
}

export interface SaleLine {
  id: string;
  product_id: string;
  product_sku: string;
  product_name: string;
  quantity: number;
  unit_price_applied: string;
  price_type: string;
  line_total: string;
}

export interface Sale {
  id: string;
  reference: string;
  branch_id: string;
  branch_name: string;
  cashier_id: string;
  cashier_name: string;
  customer_id: string | null;
  customer_name: string | null;
  subtotal: string;
  discount_rate: number;
  discount_amount: string;
  total: string;
  payment_type: PaymentType;
  status: SaleStatus | string;
  approved_by_id: string | null;
  approved_by_name: string | null;
  refund_of_sale_id: string | null;
  created_at: string;
  lines: SaleLine[];
}

export interface SaleListParams {
  branch_id?: string;
  status?: string;
  customer_id?: string;
  cashier_id?: string;
  page?: number;
  per_page?: number;
}

// ---------------------------------------------------------------------------
// Synchronisation hors-ligne (RF-20, RG-28 à RG-30)
// Cf. docs/26-GESTION-OFFLINE-PWA.md et backend/app/blueprints/sales/schemas.py
// ---------------------------------------------------------------------------

/** Taux de remise autorisés + seuil d'approbation (GET /sales/discounts/rates). */
export interface DiscountRatesResponse {
  allowed_rates: number[];
  approval_threshold: number;
}

export interface SaleSyncLinePayload {
  product_id: string;
  quantity: number;
}

/** Vente hors-ligne envoyée à POST /sales/sync. */
export interface SaleSyncItemPayload {
  offline_uuid: string;
  branch_id: string;
  customer_id?: string | null;
  payment_type?: PaymentType;
  discount_rate?: number;
  approved_by_id?: string | null;
  created_at_local?: string | null;
  lines: SaleSyncLinePayload[];
}

export const SALE_SYNC_RESULT_STATUSES = [
  "VALIDEE",
  "EN_CONFLIT",
  "EN_ATTENTE_APPROBATION",
  "DEJA_SYNCHRONISE",
  "ERREUR",
] as const;
export type SaleSyncResultStatus = (typeof SALE_SYNC_RESULT_STATUSES)[number];

/** Résultat de synchronisation pour une vente (POST /sales/sync). */
export interface SaleSyncResult {
  offline_uuid: string;
  status: SaleSyncResultStatus | string;
  sale_id: string | null;
  message: string | null;
}

export interface SaleSyncBatchResponse {
  results: SaleSyncResult[];
}
