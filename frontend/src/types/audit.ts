/** Cf. backend/app/blueprints/users/schemas.py (AuditLogSchema) */

export interface AuditLog {
  id: string;
  user_id: string | null;
  user_name: string | null;
  event_type: string;
  entity_type: string | null;
  entity_id: string | null;
  description: string | null;
  metadata_json: unknown;
  created_at: string;
}

export interface AuditLogListParams {
  event_type?: string;
  user_id?: string;
  page?: number;
  per_page?: number;
}
