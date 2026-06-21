import { apiClient } from "@/api/client";
import type { Paginated } from "@/types/api";
import type {
  StockCount,
  StockCountCreatePayload,
  StockCountDetail,
  StockCountLinesUpdatePayload,
  StockCountListParams,
} from "@/types/inventory";

export const inventoryApi = {
  /** Liste paginée des sessions d'inventaire (RF-21). */
  list: (params: StockCountListParams = {}) =>
    apiClient.get<Paginated<StockCount>>("/inventory/counts", { params }).then((r) => r.data),

  /** Détail d'une session d'inventaire avec ses lignes. */
  get: (countId: string) =>
    apiClient.get<StockCountDetail>(`/inventory/counts/${countId}`).then((r) => r.data),

  /** RF-21 : ouvre une nouvelle session d'inventaire pour un site. */
  create: (payload: StockCountCreatePayload) =>
    apiClient.post<StockCountDetail>("/inventory/counts", payload).then((r) => r.data),

  /** RF-22 : saisit les quantités comptées (écarts calculés automatiquement). */
  updateLines: (countId: string, payload: StockCountLinesUpdatePayload) =>
    apiClient
      .patch<StockCountDetail>(`/inventory/counts/${countId}/lines`, payload)
      .then((r) => r.data),

  /** RF-23 : valide la session et génère les ajustements de stock. */
  validate: (countId: string) =>
    apiClient.post<StockCountDetail>(`/inventory/counts/${countId}/validate`).then((r) => r.data),

  /** Annule (abandonne) une session EN_COURS sans ajustement de stock. */
  cancel: (countId: string) =>
    apiClient.post<StockCountDetail>(`/inventory/counts/${countId}/cancel`).then((r) => r.data),
};
