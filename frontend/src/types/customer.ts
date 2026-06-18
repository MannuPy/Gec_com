/** Cf. backend/app/blueprints/sales/schemas.py */

export const CUSTOMER_TYPES = ["SIMPLE", "TECHNICIEN"] as const;
export type CustomerType = (typeof CUSTOMER_TYPES)[number];

export interface Customer {
  id: string;
  full_name: string;
  phone: string | null;
  customer_type: CustomerType;
  credit_balance: string;
  credit_limit: string;
  created_at: string;
}

export interface CustomerWritePayload {
  full_name: string;
  phone?: string | null;
  customer_type?: CustomerType;
  credit_limit?: string;
}
