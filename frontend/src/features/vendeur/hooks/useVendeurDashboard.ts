import { useQuery } from "@tanstack/react-query";
import { reportsApi } from "@/api/endpoints/reports";

export const VENDEUR_DASHBOARD_KEY = ["vendeur-dashboard"] as const;

/** Récupère le tableau de bord de performance individuelle du vendeur connecté. */
export function useVendeurDashboard() {
  return useQuery({
    queryKey: VENDEUR_DASHBOARD_KEY,
    queryFn: () => reportsApi.vendeurDashboard(),
    refetchInterval: 60_000, // rafraîchissement automatique toutes les 60s
    staleTime: 30_000,
  });
}
