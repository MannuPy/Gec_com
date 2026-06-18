import { apiClient } from "@/api/client";
import type { Paginated } from "@/types/api";
import type {
  StockAdjustmentPayload,
  StockItem,
  StockMovement,
  StockMovementListParams,
} from "@/types/stock";

export const stockApi = {
  list: (params: { branch_id?: string; below_min?: boolean } = {}) =>
    apiClient.get<StockItem[]>("/stock", { params }).then((r) => r.data),

  movements: (params: StockMovementListParams = {}) =>
    apiClient.get<Paginated<StockMovement>>("/stock/movements", { params }).then((r) => r.data),

  adjust: (payload: StockAdjustmentPayload) =>
    apiClient.post<StockMovement>("/stock/adjustments", payload).then((r) => r.data),
};
