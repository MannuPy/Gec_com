import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { customersApi } from "@/api/endpoints/customers";
import { reportsApi } from "@/api/endpoints/reports";
import type { CreditListParams, CreditSettlePayload, CreditHistoryParams } from "@/types/customer";

export const CREDITS_KEY = ["credits"] as const;
export const CREDITS_HISTORY_KEY = ["credits", "history"] as const;

export function useCredits(params: CreditListParams = {}) {
  return useQuery({
    queryKey: [...CREDITS_KEY, params],
    queryFn: () => customersApi.listCredits(params),
  });
}

export function useSettleCredit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ customerId, payload }: { customerId: string; payload: CreditSettlePayload }) =>
      customersApi.settleCredit(customerId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: CREDITS_KEY });
      qc.invalidateQueries({ queryKey: CREDITS_HISTORY_KEY });
    },
  });
}

export function useCreditHistory(params: CreditHistoryParams = {}) {
  return useQuery({
    queryKey: [...CREDITS_HISTORY_KEY, params],
    queryFn: () => customersApi.listCreditHistory(params),
  });
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function useExportCreditsExcel() {
  return useMutation({
    mutationFn: async () => {
      const blob = await reportsApi.exportCreditsExcel();
      downloadBlob(blob, "credits-clients.xlsx");
    },
  });
}

export function useExportCreditsPdf(branchId?: string) {
  return useMutation({
    mutationFn: async () => {
      const blob = await reportsApi.exportCreditsPdf(branchId ? { branch_id: branchId } : {});
      downloadBlob(blob, "rapport-credits.pdf");
    },
  });
}
