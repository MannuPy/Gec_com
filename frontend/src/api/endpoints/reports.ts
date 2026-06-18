import { apiClient } from "@/api/client";
import type { DashboardRealtime, DashboardSummary } from "@/types/dashboard";

export const reportsApi = {
  dashboard: (branchId?: string | null) =>
    apiClient
      .get<DashboardSummary>("/reports/dashboard", {
        params: branchId ? { branch_id: branchId } : undefined,
      })
      .then((r) => r.data),

  /**
   * Snapshot temps reel (KPIs + alertes IA + ABC/XYZ + segments RFM).
   * Cf. doc 22-DASHBOARD-BI.md §22.2/§22.5. Utilise pour le chargement
   * initial et comme repli "polling" du hook `useDashboardStream`.
   */
  realtime: (branchId?: string | null) =>
    apiClient
      .get<DashboardRealtime>("/reports/dashboard/realtime", {
        params: branchId ? { branch_id: branchId } : undefined,
      })
      .then((r) => r.data),

  /**
   * URL absolue du flux SSE `/reports/dashboard/stream` (utilisee par
   * `useDashboardStream` avec `fetch` + `ReadableStream`, car `EventSource`
   * ne permet pas d'envoyer l'en-tete `Authorization`).
   */
  realtimeStreamUrl: (branchId?: string | null) => {
    const base = (import.meta.env.VITE_API_URL || "/api/v1").replace(/\/$/, "");
    const url = new URL(`${base}/reports/dashboard/stream`, window.location.origin);
    if (branchId) {
      url.searchParams.set("branch_id", branchId);
    }
    return url.toString();
  },

  /** RF-29 : export PDF du tableau de bord etendu (marges, multi-site, consolide). */
  exportPdf: (params: { branch_id?: string; days?: number } = {}) =>
    apiClient.get<Blob>("/reports/export", { params, responseType: "blob" }).then((r) => r.data),
};
