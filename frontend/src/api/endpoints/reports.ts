import { apiClient } from "@/api/client";
import type { DashboardRealtime, DashboardSummary } from "@/types/dashboard";
import type { VendeurDashboard } from "@/types/vendeur";
import type { ComptaSummary } from "@/types/compta";
import type { BranchesCompare } from "@/types/branches";

export const reportsApi = {
  dashboard: (branchId?: string | null) =>
    apiClient
      .get<DashboardSummary>("/reports/dashboard", {
        params: branchId ? { branch_id: branchId } : undefined,
      })
      .then((r) => r.data),

  realtime: (branchId?: string | null) =>
    apiClient
      .get<DashboardRealtime>("/reports/dashboard/realtime", {
        params: branchId ? { branch_id: branchId } : undefined,
      })
      .then((r) => r.data),

  realtimeStreamUrl: (branchId?: string | null) => {
    const base = (import.meta.env.VITE_API_URL || "/api/v1").replace(/\/$/, "");
    const url = new URL(`${base}/reports/dashboard/stream`, window.location.origin);
    if (branchId) {
      url.searchParams.set("branch_id", branchId);
    }
    return url.toString();
  },

  exportPdf: (params: { branch_id?: string; days?: number } = {}) =>
    apiClient.get<Blob>("/reports/export", { params, responseType: "blob" }).then((r) => r.data),

  exportSalesExcel: (params: { branch_id?: string; days?: number } = {}) =>
    apiClient
      .get<Blob>("/reports/export/sales", { params, responseType: "blob" })
      .then((r) => r.data),

  exportStockExcel: (params: { branch_id?: string } = {}) =>
    apiClient
      .get<Blob>("/reports/export/stock", { params, responseType: "blob" })
      .then((r) => r.data),

  exportCreditsExcel: () =>
    apiClient.get<Blob>("/reports/export/credits", { responseType: "blob" }).then((r) => r.data),

  exportCreditsPdf: (params: { branch_id?: string } = {}) =>
    apiClient
      .get<Blob>("/reports/credits/pdf", { params, responseType: "blob" })
      .then((r) => r.data),

  vendeurDashboard: () =>
    apiClient.get<VendeurDashboard>("/reports/vendeur/dashboard").then((r) => r.data),

  branchesCompare: (params: { datDebut?: string; datFin?: string } = {}) => {
    const p: Record<string, string> = {};
    if (params.datDebut) p.date_debut = params.datDebut;
    if (params.datFin) p.date_fin = params.datFin;
    return apiClient
      .get<BranchesCompare>("/reports/branches/compare", {
        params: Object.keys(p).length ? p : undefined,
      })
      .then((r) => r.data);
  },

  comptaSummary: (params: { branchId?: string; datDebut?: string; datFin?: string } = {}) => {
    const p: Record<string, string> = {};
    if (params.branchId) p.branch_id = params.branchId;
    if (params.datDebut) p.date_debut = params.datDebut;
    if (params.datFin) p.date_fin = params.datFin;
    return apiClient
      .get<ComptaSummary>("/reports/compta/summary", {
        params: Object.keys(p).length ? p : undefined,
      })
      .then((r) => r.data);
  },
};
