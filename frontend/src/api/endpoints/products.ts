import { apiClient } from "@/api/client";
import type { Paginated } from "@/types/api";
import type {
  Branch,
  Brand,
  BrandWritePayload,
  Category,
  CategoryWritePayload,
  Product,
  ProductCreatePayload,
  ProductListParams,
  ProductUpdatePayload,
} from "@/types/product";

export const productsApi = {
  list: (params: ProductListParams = {}) =>
    apiClient.get<Paginated<Product>>("/products", { params }).then((r) => r.data),

  get: (id: string) => apiClient.get<Product>(`/products/${id}`).then((r) => r.data),

  create: (payload: ProductCreatePayload) =>
    apiClient.post<Product>("/products", payload).then((r) => r.data),

  update: (id: string, payload: ProductUpdatePayload) =>
    apiClient.patch<Product>(`/products/${id}`, payload).then((r) => r.data),

  branches: () => apiClient.get<Branch[]>("/branches").then((r) => r.data),

  categories: () => apiClient.get<Category[]>("/categories").then((r) => r.data),

  createCategory: (payload: CategoryWritePayload) =>
    apiClient.post<Category>("/categories", payload).then((r) => r.data),

  brands: () => apiClient.get<Brand[]>("/brands").then((r) => r.data),

  createBrand: (payload: BrandWritePayload) =>
    apiClient.post<Brand>("/brands", payload).then((r) => r.data),
};
