export const PAYMENT_TYPES = ["CASH", "CREDIT"] as const;
export type PaymentType = (typeof PAYMENT_TYPES)[number];

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

export interface SaleSyncLinePayload {
  product_id: string;
  quantity: number;
}

export interface SaleSyncItemPayload {
  offline_uuid: string;
  branch_id: string;
  customer_id?: string | null;
  payment_type?: PaymentType;
  discount_rate?: number;
  created_at_local?: string | null;
  lines: SaleSyncLinePayload[];
}

export const SALE_SYNC_RESULT_STATUSES = [
  "VALIDEE",
  "EN_CONFLIT",
  "DEJA_SYNCHRONISE",
  "ERREUR",
] as const;
export type SaleSyncResultStatus = (typeof SALE_SYNC_RESULT_STATUSES)[number];

export interface SaleSyncResult {
  offline_uuid: string;
  status: SaleSyncResultStatus | string;
  sale_id: string | null;
  message: string | null;
}

export interface SaleSyncBatchResponse {
  results: SaleSyncResult[];
}

export interface RefundHistoryItem extends Sale {
  admin_name: string | null;
  rejection_reason: string | null;
}

export interface RefundHistoryParams {
  status?: "AVOIR_EMIS" | "ANNULEE";
}
