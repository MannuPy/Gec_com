/** Cf. backend/app/blueprints/stock/schemas.py */

export const STOCK_MOVEMENT_TYPES = [
  "ENTREE_RECEPTION",
  "SORTIE_TRANSFERT",
  "ENTREE_TRANSFERT",
  "SORTIE_VENTE",
  "ENTREE_RETOUR_VENTE",
  "AJUSTEMENT_INVENTAIRE",
  "AJUSTEMENT_MANUEL",
] as const;
export type StockMovementType = (typeof STOCK_MOVEMENT_TYPES)[number];

export interface StockItem {
  id: string;
  product_id: string;
  product_sku: string;
  product_name: string;
  branch_id: string;
  branch_name: string;
  quantity: number;
  min_stock_threshold: number;
  below_min: boolean;
}

export interface StockMovement {
  id: string;
  product_id: string;
  product_name: string;
  branch_id: string;
  branch_name: string;
  movement_type: StockMovementType;
  quantity: number;
  reference_type: string | null;
  reference_id: string | null;
  comment: string | null;
  created_at: string;
}

export interface StockAdjustmentPayload {
  product_id: string;
  branch_id: string;
  quantity_delta: number;
  comment: string;
}

export interface StockMovementListParams {
  branch_id?: string;
  product_id?: string;
  page?: number;
  per_page?: number;
}
