import { apiClient } from "@/api/client";
import type {
  AbcXyzItem,
  AbcXyzParams,
  AdvancedDashboard,
  AdvancedDashboardParams,
  AfricanContextResponse,
  AnalyticsItemsResponse,
  AnomalyItem,
  AnomalyParams,
  ChurnRiskResponse,
  CreditScoreItem,
  CreditScoreParams,
  DemandForecastItem,
  DemandForecastParams,
  MarketBasketResponse,
  MlModel,
  MlModelType,
  MlTrainResult,
  PriceElasticityResponse,
  RfmEvaluateKResponse,
  RfmSegmentParams,
  RfmSegmentsResponse,
  SalesTrendItem,
  CohortAnalysis,
  ClvResponse,
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

  /** RF-26 : segmentation RFM des clients (avec résumé par segment et churn). */
  rfmSegments: (params: RfmSegmentParams = {}) =>
    apiClient
      .get<RfmSegmentsResponse>("/analytics/rfm-segments", { params })
      .then((r) => r.data),

  /** Clients à risque de churn (heuristique P=1-exp(-λ×R)). */
  churnRisk: (params: { min_probability?: number } = {}) =>
    apiClient
      .get<ChurnRiskResponse>("/analytics/churn-risk", { params })
      .then((r) => r.data),

  /** Market Basket Analysis — règles d'association produits (Apriori). */
  marketBasket: (params: { branch_id?: string; min_lift?: number; product?: string } = {}) =>
    apiClient
      .get<MarketBasketResponse>("/analytics/basket", { params })
      .then((r) => r.data),

  /** Entraîner le modèle Market Basket en arrière-plan. */
  trainMarketBasket: (months = 6) =>
    apiClient
      .post<{ status: string; message: string }>("/analytics/basket/train", { months })
      .then((r) => r.data),

  /** Élasticité prix par produit (régression log-log). */
  priceElasticity: (params: { branch_id?: string; months?: number } = {}) =>
    apiClient
      .get<PriceElasticityResponse>("/analytics/price-elasticity", { params })
      .then((r) => r.data),

  /** Contexte africain / BF — événements, weekend boost, stress trésorerie. */
  africanContext: () =>
    apiClient
      .get<AfricanContextResponse>("/analytics/african-context")
      .then((r) => r.data),

  /** Évaluation K optimal pour K-Means RFM (Silhouette + Davies-Bouldin + Elbow). */
  rfmEvaluateK: () =>
    apiClient
      .get<RfmEvaluateKResponse>("/analytics/rfm-segments/evaluate-k")
      .then((r) => r.data),

  /** Registre des modèles ML entraînés (RNF-17, RG-40). */
  mlModels: () => apiClient.get<{ items: MlModel[] }>("/analytics/ml/models").then((r) => r.data.items),

  /** RF-29 : déclenche l'entraînement d'un modèle ML côté serveur. */
  trainModel: (modelType: MlModelType) =>
    apiClient.post<MlTrainResult>("/analytics/ml/train", { model_type: modelType }).then((r) => r.data),

  /** Feature E : analyse de cohortes clients (rétention par mois d'acquisition). */
  cohorts: (params: { months?: number } = {}) =>
    apiClient.get<CohortAnalysis>("/analytics/cohorts", { params }).then((r) => r.data),

  /** Feature F : Customer Lifetime Value estimée. */
  clv: (params: { limit?: number; min_clv?: number } = {}) =>
    apiClient.get<ClvResponse>("/analytics/clv", { params }).then((r) => r.data),
};
