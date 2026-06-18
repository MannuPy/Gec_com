/** Cf. backend/app/blueprints/suppliers/schemas.py */

export interface Supplier {
  id: string;
  name: string;
  contact_name: string | null;
  phone: string | null;
  email: string | null;
  address: string | null;
  is_active: boolean;
}

export interface SupplierWritePayload {
  name: string;
  contact_name?: string | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  is_active?: boolean;
}

export const RECEPTION_STATUSES = ["BROUILLON", "VALIDEE"] as const;
export type ReceptionStatus = (typeof RECEPTION_STATUSES)[number];

export interface ReceptionLineWritePayload {
  product_id: string;
  quantity: number;
  unit_purchase_price: string;
}

export interface ReceptionCreatePayload {
  supplier_id: string;
  branch_id: string;
  lines: ReceptionLineWritePayload[];
}

export interface ReceptionLine {
  id: string;
  product_id: string;
  product_sku: string;
  product_name: string;
  quantity: number;
  unit_purchase_price: string;
}

export interface Reception {
  id: string;
  reference: string;
  supplier_id: string;
  supplier_name: string;
  branch_id: string;
  branch_name: string;
  status: ReceptionStatus;
  received_at: string | null;
  created_at: string;
  lines: ReceptionLine[];
  total_amount: string;
}

export interface ReceptionListParams {
  branch_id?: string;
  supplier_id?: string;
  status?: ReceptionStatus;
}
