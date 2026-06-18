import { apiClient } from "@/api/client";
import type {
  Reception,
  ReceptionCreatePayload,
  ReceptionListParams,
  Supplier,
  SupplierWritePayload,
} from "@/types/supplier";

export const suppliersApi = {
  list: (params: { is_active?: boolean } = {}) =>
    apiClient.get<Supplier[]>("/suppliers", { params }).then((r) => r.data),

  get: (id: string) => apiClient.get<Supplier>(`/suppliers/${id}`).then((r) => r.data),

  create: (payload: SupplierWritePayload) =>
    apiClient.post<Supplier>("/suppliers", payload).then((r) => r.data),

  update: (id: string, payload: SupplierWritePayload) =>
    apiClient.put<Supplier>(`/suppliers/${id}`, payload).then((r) => r.data),

  receptions: {
    list: (params: ReceptionListParams = {}) =>
      apiClient.get<Reception[]>("/receptions", { params }).then((r) => r.data),

    get: (id: string) => apiClient.get<Reception>(`/receptions/${id}`).then((r) => r.data),

    create: (payload: ReceptionCreatePayload) =>
      apiClient.post<Reception>("/receptions", payload).then((r) => r.data),

    validate: (id: string) =>
      apiClient.post<Reception>(`/receptions/${id}/validate`).then((r) => r.data),
  },
};
