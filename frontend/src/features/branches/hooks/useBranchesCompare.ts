import { useQuery } from "@tanstack/react-query";
import { reportsApi } from "@/api/endpoints/reports";

export interface BranchCompareFilters {
  datDebut?: string; // YYYY-MM-DD
  datFin?: string;   // YYYY-MM-DD
}

export const BRANCHES_COMPARE_KEY = (filters: BranchCompareFilters) =>
  ["branches-compare", filters] as const;

export function useBranchesCompare(filters: BranchCompareFilters = {}) {
  return useQuery({
    queryKey: BRANCHES_COMPARE_KEY(filters),
    queryFn: () => reportsApi.branchesCompare(filters),
    staleTime: 120_000,
  });
}
