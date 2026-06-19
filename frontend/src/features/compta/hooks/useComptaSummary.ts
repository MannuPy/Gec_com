import { useQuery } from "@tanstack/react-query";
import { reportsApi } from "@/api/endpoints/reports";

export interface ComptaFilters {
  branchId?: string;
  datDebut?: string; // YYYY-MM-DD
  datFin?: string;   // YYYY-MM-DD
}

export const COMPTA_SUMMARY_KEY = (filters: ComptaFilters) =>
  ["compta-summary", filters] as const;

export function useComptaSummary(filters: ComptaFilters = {}) {
  return useQuery({
    queryKey: COMPTA_SUMMARY_KEY(filters),
    queryFn: () => reportsApi.comptaSummary(filters),
    staleTime: 60_000,
  });
}
