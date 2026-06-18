import { apiClient } from "@/api/client";
import type {
  Transfer,
  TransferCreatePayload,
  TransferListParams,
  TransferReceivePayload,
} from "@/types/transfer";

export const transfersApi = {
  list: (params: TransferListParams = {}) =>
    apiClient.get<Transfer[]>("/transfers", { params }).then((r) => r.data),

  get: (id: string) => apiClient.get<Transfer>(`/transfers/${id}`).then((r) => r.data),

  create: (payload: TransferCreatePayload) =>
    apiClient.post<Transfer>("/transfers", payload).then((r) => r.data),

  send: (id: string) => apiClient.post<Transfer>(`/transfers/${id}/send`).then((r) => r.data),

  receive: (id: string, payload: TransferReceivePayload) =>
    apiClient.post<Transfer>(`/transfers/${id}/receive`, payload).then((r) => r.data),

  cancel: (id: string) => apiClient.post<Transfer>(`/transfers/${id}/cancel`).then((r) => r.data),
};
