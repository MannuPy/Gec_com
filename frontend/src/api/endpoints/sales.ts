import { apiClient } from "@/api/client";
import type { Paginated } from "@/types/api";
import type {
  RefundCreatePayload,
  Sale,
  SaleCreatePayload,
  SaleListParams,
  SaleSyncBatchResponse,
  SaleSyncItemPayload,
} from "@/types/sale";

export const salesApi = {
  list: (params: SaleListParams = {}) =>
    apiClient.get<Paginated<Sale>>("/sales", { params }).then((r) => r.data),

  get: (id: string) => apiClient.get<Sale>(`/sales/${id}`).then((r) => r.data),

  create: (payload: SaleCreatePayload) =>
    apiClient.post<Sale>("/sales", payload).then((r) => r.data),

  refund: (id: string, payload: RefundCreatePayload) =>
    apiClient.post<Sale>(`/sales/${id}/refund`, payload).then((r) => r.data),

  receiptPdf: (id: string) =>
    apiClient.get<Blob>(`/sales/${id}/receipt`, { responseType: "blob" }).then((r) => r.data),

  sync: (sales: SaleSyncItemPayload[]) =>
    apiClient.post<SaleSyncBatchResponse>("/sales/sync", { sales }).then((r) => r.data),

  listPendingRefunds: () =>
    apiClient.get<Sale[]>("/sales/refunds/pending").then((r) => r.data),

  approveRefund: (saleId: string) =>
    apiClient.patch<Sale>(`/sales/${saleId}/refund/approve`).then((r) => r.data),

  rejectRefund: (saleId: string, reason?: string) =>
    apiClient.patch<Sale>(`/sales/${saleId}/refund/reject`, { reason }).then((r) => r.data),
};
