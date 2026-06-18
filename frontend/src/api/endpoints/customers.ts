import { apiClient } from "@/api/client";
import type { Customer, CustomerWritePayload } from "@/types/customer";

export const customersApi = {
  list: (search?: string) =>
    apiClient
      .get<Customer[]>("/sales/customers", { params: search ? { search } : undefined })
      .then((r) => r.data),

  get: (id: string) => apiClient.get<Customer>(`/sales/customers/${id}`).then((r) => r.data),

  create: (payload: CustomerWritePayload) =>
    apiClient.post<Customer>("/sales/customers", payload).then((r) => r.data),

  update: (id: string, payload: CustomerWritePayload) =>
    apiClient.put<Customer>(`/sales/customers/${id}`, payload).then((r) => r.data),
};
