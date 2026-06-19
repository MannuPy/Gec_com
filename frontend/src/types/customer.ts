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

/** Payload pour régler (partiellement ou totalement) l'encours d'un client. */
export interface CreditSettlePayload {
  amount: string;
  note?: string;
}

/** Réponse du endpoint POST /sales/customers/:id/settle */
export interface CreditSettleResponse {
  customer_id: string;
  amount_settled: string;
  new_credit_balance: string;
}

/** Filtres pour GET /sales/credits (liste des clients avec encours non nul). */
export interface CreditListParams {
  branch_id?: string;
  customer_type?: string;
}
