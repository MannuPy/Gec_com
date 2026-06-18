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

  /** RF-19 : recu de vente au format PDF (ticket 80mm). */
  receiptPdf: (id: string) =>
    apiClient.get<Blob>(`/sales/${id}/receipt`, { responseType: "blob" }).then((r) => r.data),

  /** Synchronisation différée des ventes saisies hors-ligne (RF-20, RG-28 à RG-30). */
  sync: (sales: SaleSyncItemPayload[]) =>
    apiClient.post<SaleSyncBatchResponse>("/sales/sync", { sales }).then((r) => r.data),
};
