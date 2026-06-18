/** Cf. backend/app/blueprints/transfers/schemas.py */

export const TRANSFER_STATUSES = ["BROUILLON", "EN_TRANSIT", "RECU", "ANNULE"] as const;
export type TransferStatus = (typeof TRANSFER_STATUSES)[number];

export interface TransferLineWritePayload {
  product_id: string;
  quantity_sent: number;
}

export interface TransferCreatePayload {
  source_branch_id: string;
  destination_branch_id: string;
  lines: TransferLineWritePayload[];
}

export interface ReceiveLinePayload {
  line_id: string;
  quantity_received: number;
  variance_comment?: string | null;
}

export interface TransferReceivePayload {
  lines: ReceiveLinePayload[];
}

export interface TransferLine {
  id: string;
  product_id: string;
  product_sku: string;
  product_name: string;
  quantity_sent: number;
  quantity_received: number | null;
  variance_comment: string | null;
}

export interface Transfer {
  id: string;
  reference: string;
  source_branch_id: string;
  source_branch_name: string;
  destination_branch_id: string;
  destination_branch_name: string;
  status: TransferStatus;
  created_at: string;
  sent_at: string | null;
  received_at: string | null;
  lines: TransferLine[];
}

export interface TransferListParams {
  branch_id?: string;
  status?: TransferStatus;
}
