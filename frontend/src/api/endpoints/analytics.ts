import { apiClient } from "@/api/client";
import type {
  AbcXyzItem,
  AbcXyzParams,
  AdvancedDashboard,
  AdvancedDashboardParams,
  AnalyticsItemsResponse,
  AnomalyItem,
  AnomalyParams,
  CreditScoreItem,
  CreditScoreParams,
  DemandForecastItem,
  DemandForecastParams,
  MlModel,
  MlModelType,
  MlTrainResult,
  RfmSegmentItem,
  RfmSegmentParams,
  SalesTrendItem,
} from "@/types/analytics";

export const analyticsApi = {
  /** RF-24 : tendance des ventes jour par jour (séries temporelles pour graphiques). */
  salesTrend: (params: AdvancedDashboardParams = {}) =>
    apiClient
      .get<AnalyticsItemsResponse<SalesTrendItem>>("/analytics/sales-trend", { params })
      .then((r) => r.data),

  /** RF-24 : tableau de bord étendu (marges, multi-site, consolidé). */
  dashboard: (params: AdvancedDashboardParams = {}) =>
    apiClient.get<AdvancedDashboard>("/analytics/dashboard", { params }).then((r) => r.data),

  /** RF-25 : prévisions de demande / alertes de rupture de stock. */
  forecast: (params: DemandForecastParams = {}) =>
    apiClient
      .get<AnalyticsItemsResponse<DemandForecastItem>>("/analytics/forecast", { params })
      .then((r) => r.data),

  /** RF-25 : prévision détaillée pour un couple produit/site. */
  forecastDetail: (productId: string, branchId: string) =>
    apiClient
      .get<DemandForecastItem>(`/analytics/forecast/${productId}/${branchId}`)
      .then((r) => r.data),

  /** RF-27 : scoring crédit des clients. */
  creditScores: (params: CreditScoreParams = {}) =>
    apiClient
      .get<AnalyticsItemsResponse<CreditScoreItem>>("/analytics/credit-scores", { params })
      .then((r) => r.data),

  /** RF-28 : ventes signalées comme anomalies. */
  anomalies: (params: AnomalyParams = {}) =>
    apiClient
      .get<AnalyticsItemsResponse<AnomalyItem>>("/analytics/anomalies", { params })
      .then((r) => r.data),

  /** RF-26 : classification ABC/XYZ des produits. */
  abcXyz: (params: AbcXyzParams = {}) =>
    apiClient.get<AnalyticsItemsResponse<AbcXyzItem>>("/analytics/abc-xyz", { params }).then((r) => r.data),

  /** RF-26 : segmentation RFM des clients. */
  rfmSegments: (params: RfmSegmentParams = {}) =>
    apiClient
      .get<AnalyticsItemsResponse<RfmSegmentItem>>("/analytics/rfm-segments", { params })
      .then((r) => r.data),

  /** Registre des modèles ML entraînés (RNF-17, RG-40). */
  mlModels: () => apiClient.get<{ items: MlModel[] }>("/analytics/ml/models").then((r) => r.data.items),

  /** RF-29 : déclenche l'entraînement d'un modèle ML. */
  trainModel: (modelType: MlModelType | string, async = false) =>
    apiClient
      .post<MlTrainResult>(`/analytics/ml/train/${modelType}`, undefined, {
        params: async ? { async: "true" } : undefined,
      })
      .then((r) => r.data),
};
