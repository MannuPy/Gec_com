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

export interface CreditSettlePayload {
  amount: string;
  note?: string;
}

export interface CreditSettleResponse {
  customer_id: string;
  amount_settled: string;
  new_credit_balance: string;
}

export interface CreditListParams {
  branch_id?: string;
  customer_type?: string;
}

export type CreditHistoryStatus = "SOLDE" | "EN_COURS" | "NON_COMMENCE";

export interface CustomerPaymentItem {
  id: string;
  sale_id: string | null;
  sale_reference: string | null;
  amount: string;
  due_date: string;
  paid_date: string | null;
  status: "PENDING" | "PAID" | "LATE" | "CANCELLED";
  note: string | null;
  created_at: string;
}

export interface CreditHistoryItem {
  customer_id: string;
  customer_name: string;
  customer_phone: string | null;
  customer_type: CustomerType;
  credit_balance: string;
  credit_limit: string;
  credit_status: CreditHistoryStatus;
  total_payments: number;
  paid_payments: number;
  total_paid_amount: string;
  payments: CustomerPaymentItem[];
}

export interface CreditHistoryParams {
  credit_status?: CreditHistoryStatus;
}
