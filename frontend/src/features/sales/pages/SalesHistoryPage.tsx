import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Download, Loader2, Undo2 } from "lucide-react";

import { productsApi } from "@/api/endpoints/products";
import { salesApi } from "@/api/endpoints/sales";
import { getApiErrorMessage } from "@/api/client";
import { useAuthStore } from "@/app/store";
import { Modal } from "@/components/Modal";
import { SALE_STATUSES, type RefundLinePayload, type Sale, type SaleStatus } from "@/types/sale";
import { formatCurrency, formatDateTime, formatNumber } from "@/utils/format";

const PER_PAGE = 20;

const STATUS_LABELS: Record<string, string> = {
  VALIDEE: "Validée",
  ANNULEE: "Annulée",
  AVOIR_EMIS: "Avoir émis",
  EN_ATTENTE_SYNC: "En attente sync",
  EN_CONFLIT: "En conflit",
  EN_ATTENTE_APPROBATION: "En attente d'approbation",
};

const STATUS_BADGES: Record<string, string> = {
  VALIDEE: "badge-success",
  ANNULEE: "badge-danger",
  AVOIR_EMIS: "badge-info",
  EN_ATTENTE_SYNC: "badge-warning",
  EN_CONFLIT: "badge-danger",
  EN_ATTENTE_APPROBATION: "badge-warning",
};

/** RF-19 : télécharge le reçu PDF d'une vente et l'ouvre dans le navigateur. */
function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Historique des ventes & avoirs (RF-25) : consultation des ventes,
 * détail des lignes et émission d'avoirs (retours, RG-29/30).
 * Cf. GET /api/v1/sales, POST /sales/:id/refund.
 */
export default function SalesHistoryPage() {
  const user = useAuthStore((s) => s.user);
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const canRefund = hasPermission("sales:refund");
  const queryClient = useQueryClient();

  const [branchId, setBranchId] = useState(user?.branch_id ?? "");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [detail, setDetail] = useState<Sale | null>(null);
  const [receiptError, setReceiptError] = useState<string | null>(null);
  const [downloadingReceiptId, setDownloadingReceiptId] = useState<string | null>(null);

  const handleDownloadReceipt = async (sale: Sale) => {
    setReceiptError(null);
    setDownloadingReceiptId(sale.id);
    try {
      const blob = await salesApi.receiptPdf(sale.id);
      downloadBlob(blob, `recu-${sale.reference}.pdf`);
    } catch (error) {
      setReceiptError(getApiErrorMessage(error, "Impossible de générer le reçu PDF."));
    } finally {
      setDownloadingReceiptId(null);
    }
  };

  const branchesQuery = useQuery({
    queryKey: ["branches"],
    queryFn: productsApi.branches,
    enabled: !user?.branch_id,
  });

  const salesQuery = useQuery({
    queryKey: ["sales-history", branchId, status, page],
    queryFn: () =>
      salesApi.list({
        branch_id: branchId || undefined,
        status: status || undefined,
        page,
        per_page: PER_PAGE,
      }),
  });

  const sales = salesQuery.data?.data ?? [];
  const meta = salesQuery.data?.meta;
  const totalPages = meta ? Math.max(1, Math.ceil(meta.total / meta.per_page)) : 1;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-primary-dark">Historique des ventes</h1>
        <p className="text-sm text-muted">Consultation des ventes et émission d'avoirs</p>
      </div>

      <div className="card space-y-4">
        <div className="flex flex-wrap gap-3">
          {!user?.branch_id && (
            <select
              className="input max-w-xs"
              value={branchId}
              onChange={(e) => {
                setBranchId(e.target.value);
                setPage(1);
              }}
            >
              <option value="">Tous les sites</option>
              {(branchesQuery.data ?? []).map((branch) => (
                <option key={branch.id} value={branch.id}>
                  {branch.name}
                </option>
              ))}
            </select>
          )}

          <select
            className="input max-w-xs"
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
          >
            <option value="">Tous les statuts</option>
            {SALE_STATUSES.map((s) => (
              <option key={s} value={s}>
                {STATUS_LABELS[s] ?? s}
              </option>
            ))}
          </select>
        </div>

        {salesQuery.isLoading && (
          <div className="flex items-center gap-2 text-muted">
            <Loader2 className="h-4 w-4 animate-spin" />
            Chargement...
          </div>
        )}

        {salesQuery.isError && (
          <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
            {getApiErrorMessage(salesQuery.error, "Impossible de charger l'historique des ventes.")}
          </div>
        )}

        {receiptError && (
          <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{receiptError}</div>
        )}

        {salesQuery.isSuccess && (
          <>
            <div className="overflow-x-auto">
              <table className="table-base">
                <thead>
                  <tr>
                    <th>Référence</th>
                    <th>Date</th>
                    <th>Site</th>
                    <th>Client</th>
                    <th>Caissier</th>
                    <th className="text-right">Total</th>
                    <th>Paiement</th>
                    <th>Statut</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {sales.length === 0 && (
                    <tr>
                      <td colSpan={9} className="text-center text-muted">
                        Aucune vente trouvée.
                      </td>
                    </tr>
                  )}
                  {sales.map((sale) => (
                    <tr key={sale.id}>
                      <td className="font-mono text-xs text-muted">{sale.reference}</td>
                      <td className="whitespace-nowrap text-xs text-muted">{formatDateTime(sale.created_at)}</td>
                      <td>{sale.branch_name}</td>
                      <td>{sale.customer_name ?? "Comptant"}</td>
                      <td>{sale.cashier_name}</td>
                      <td className="text-right font-medium text-primary-dark">{formatCurrency(sale.total)}</td>
                      <td>{sale.payment_type === "CREDIT" ? "Crédit" : "Comptant"}</td>
                      <td>
                        <span className={`badge ${STATUS_BADGES[sale.status] ?? "badge-info"}`}>
                          {STATUS_LABELS[sale.status] ?? sale.status}
                        </span>
                      </td>
                      <td className="text-right">
                        <div className="flex justify-end gap-2">
                          <button
                            type="button"
                            className="btn-secondary"
                            disabled={downloadingReceiptId === sale.id}
                            title="Télécharger le reçu PDF"
                            onClick={() => handleDownloadReceipt(sale)}
                          >
                            {downloadingReceiptId === sale.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Download className="h-4 w-4" />
                            )}
                            Reçu
                          </button>
                          <button type="button" className="btn-secondary" onClick={() => setDetail(sale)}>
                            Détails
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {meta && (
              <div className="flex items-center justify-between border-t border-surface pt-3 text-sm text-muted">
                <span>
                  {formatNumber(meta.total)} vente{meta.total === 1 ? "" : "s"} - page {meta.page} / {totalPages}
                </span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    className="btn-secondary"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Précédent
                  </button>
                  <button
                    type="button"
                    className="btn-secondary"
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  >
                    Suivant
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {detail && (
        <Modal title={`Vente ${detail.reference}`} onClose={() => setDetail(null)} widthClassName="max-w-2xl">
          <SaleDetail
            sale={detail}
            canRefund={canRefund}
            onRefunded={(s) => {
              queryClient.invalidateQueries({ queryKey: ["sales-history"] });
              setDetail(s);
            }}
          />
        </Modal>
      )}
    </div>
  );
}

interface SaleDetailProps {
  sale: Sale;
  canRefund: boolean;
  onRefunded: (s: Sale) => void;
}

function SaleDetail({ sale, canRefund, onRefunded }: SaleDetailProps) {
  const [refundMode, setRefundMode] = useState(false);
  const [quantities, setQuantities] = useState<Record<string, string>>({});
  const [reason, setReason] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const refundMutation = useMutation({
    mutationFn: () => {
      const lines: RefundLinePayload[] = sale.lines
        .map((l) => ({ product_id: l.product_id, quantity: Number(quantities[l.id] ?? 0) }))
        .filter((l) => l.quantity > 0);
      return salesApi.refund(sale.id, { lines, reason: reason.trim() });
    },
    onSuccess: onRefunded,
    onError: (error) => setFormError(getApiErrorMessage(error, "Impossible d'émettre l'avoir.")),
  });

  const handleSubmit = () => {
    setFormError(null);
    const totalQty = sale.lines.reduce((sum, l) => sum + Number(quantities[l.id] ?? 0), 0);
    if (totalQty <= 0) {
      setFormError("Indiquez au moins une quantité à retourner.");
      return;
    }
    if (reason.trim().length < 3) {
      setFormError("Le motif de l'avoir est obligatoire (3 caractères minimum).");
      return;
    }
    refundMutation.mutate();
  };

  const canShowRefundAction = canRefund && sale.status === "VALIDEE";

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-muted">
        <span>
          {sale.branch_name} - {sale.customer_name ?? "Client comptant"} - {sale.cashier_name}
        </span>
        <span className={`badge ${STATUS_BADGES[sale.status] ?? "badge-info"}`}>
          {STATUS_LABELS[sale.status] ?? sale.status}
        </span>
      </div>

      <div className="overflow-x-auto">
      <table className="table-base">
        <thead>
          <tr>
            <th>Produit</th>
            <th className="text-right">Qté vendue</th>
            <th className="text-right">Prix unitaire</th>
            <th className="text-right">Total ligne</th>
            {refundMode && <th className="text-right">Qté à retourner</th>}
          </tr>
        </thead>
        <tbody>
          {sale.lines.map((line) => (
            <tr key={line.id}>
              <td>
                <div className="font-medium text-primary-dark">{line.product_name}</div>
                <div className="text-xs text-muted">{line.product_sku}</div>
              </td>
              <td className="text-right">{line.quantity}</td>
              <td className="text-right">{formatCurrency(line.unit_price_applied)}</td>
              <td className="text-right">{formatCurrency(line.line_total)}</td>
              {refundMode && (
                <td className="text-right">
                  <input
                    type="number"
                    min="0"
                    max={line.quantity}
                    step="1"
                    className="input w-20 text-right"
                    value={quantities[line.id] ?? ""}
                    onChange={(e) => setQuantities((q) => ({ ...q, [line.id]: e.target.value }))}
                  />
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
      </div>

      <div className="space-y-1 text-right text-sm">
        <p className="text-muted">Sous-total : {formatCurrency(sale.subtotal)}</p>
        {Number(sale.discount_amount) > 0 && (
          <p className="text-muted">
            Remise ({sale.discount_rate}%) : -{formatCurrency(sale.discount_amount)}
          </p>
        )}
        <p className="text-lg font-semibold text-primary-dark">Total : {formatCurrency(sale.total)}</p>
      </div>

      {refundMode && (
        <div>
          <label className="label">Motif de l'avoir</label>
          <textarea className="input" rows={2} value={reason} onChange={(e) => setReason(e.target.value)} />
        </div>
      )}

      {formError && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{formError}</div>}

      {canShowRefundAction && (
        <div className="flex justify-end gap-2 border-t border-surface pt-3">
          {!refundMode ? (
            <button type="button" className="btn-danger" onClick={() => setRefundMode(true)}>
              <Undo2 className="h-4 w-4" />
              Émettre un avoir
            </button>
          ) : (
            <>
              <button type="button" className="btn-secondary" onClick={() => setRefundMode(false)}>
                Annuler
              </button>
              <button type="button" className="btn-primary" disabled={refundMutation.isPending} onClick={handleSubmit}>
                {refundMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                Confirmer l'avoir
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
