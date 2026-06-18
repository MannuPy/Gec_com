import { apiClient } from "@/api/client";
import type { Paginated } from "@/types/api";
import type { AuditLog, AuditLogListParams } from "@/types/audit";

export const auditApi = {
  list: (params: AuditLogListParams = {}) =>
    apiClient.get<Paginated<AuditLog>>("/users/audit-logs", { params }).then((r) => r.data),
};
