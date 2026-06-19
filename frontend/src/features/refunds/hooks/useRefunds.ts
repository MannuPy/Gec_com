import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { salesApi } from "@/api/endpoints/sales";

export const PENDING_REFUNDS_KEY = ["refunds", "pending"] as const;

export function usePendingRefunds() {
  return useQuery({
    queryKey: PENDING_REFUNDS_KEY,
    queryFn: () => salesApi.listPendingRefunds(),
    refetchInterval: 30_000, // rafraîchit toutes les 30s
  });
}

export function useApproveRefund() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (saleId: string) => salesApi.approveRefund(saleId),
    onSuccess: () => qc.invalidateQueries({ queryKey: PENDING_REFUNDS_KEY }),
  });
}

export function useRejectRefund() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ saleId, reason }: { saleId: string; reason?: string }) =>
      salesApi.rejectRefund(saleId, reason),
    onSuccess: () => qc.invalidateQueries({ queryKey: PENDING_REFUNDS_KEY }),
  });
}
