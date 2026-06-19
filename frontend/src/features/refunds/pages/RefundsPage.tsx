/**
 * Page Retours produits — GesCom-BF
 *
 * Workflow :
 *   1. Vendeur initie un retour via la page Historique des ventes
 *      (POST /sales/{id}/refund → statut EN_ATTENTE_APPROBATION)
 *   2. Admin voit ici la liste des retours en attente
 *   3. Admin clique "Approuver" → stock réintégré + remboursement client
 *      OU "Rejeter" → retour annulé, stock non réintégré
 */
import { useState } from "react";
import {
  CheckCircle2,
  XCircle,
  Clock,
  Package,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { usePendingRefunds, useApproveRefund, useRejectRefund } from "../hooks/useRefunds";
import type { Sale } from "@/types/sale";
import { useAuthStore } from "@/app/store";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmt(v: string | number) {
  const n = typeof v === "string" ? parseFloat(v) : v;
  if (isNaN(n)) return "0";
  return n.toLocaleString("fr-FR") + " FCFA";
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString("fr-FR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ---------------------------------------------------------------------------
// Carte retour individuel
// ---------------------------------------------------------------------------

interface RefundCardProps {
  refund: Sale;
  canApprove: boolean;
}

function RefundCard({ refund, canApprove }: RefundCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [showRejectInput, setShowRejectInput] = useState(false);

  const approve = useApproveRefund();
  const reject = useRejectRefund();

  const isProcessing = approve.isPending || reject.isPending;

  function handleApprove() {
    approve.mutate(refund.id);
  }

  function handleReject() {
    if (!showRejectInput) { setShowRejectInput(true); return; }
    if (!rejectReason.trim()) return;
    reject.mutate({ saleId: refund.id, reason: rejectReason });
  }

  return (
    <div className="rounded-xl bg-white shadow-sm ring-1 ring-orange-200">
      {/* En-tête */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-orange-100">
            <Package className="h-5 w-5 text-orange-600" />
          </div>
          <div>
            <p className="font-semibold text-gray-900">{refund.reference}</p>
            <p className="text-xs text-gray-500">
              Initié le {fmtDate(refund.created_at)}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="text-right">
            <p className="text-sm text-gray-500">Client</p>
            <p className="font-medium text-gray-900">{refund.customer_name ?? "—"}</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">Montant retour</p>
            <p className="font-bold text-orange-600">{fmt(refund.total)}</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">Vendeur</p>
            <p className="font-medium text-gray-900">{refund.cashier_name}</p>
          </div>
        </div>

        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 rounded-lg border border-gray-200 px-3 py-1.5 text-xs text-gray-500 hover:bg-gray-50"
        >
          {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          Produits ({refund.lines?.length ?? 0})
        </button>
      </div>

      {/* Détail des lignes (expand) */}
      {expanded && refund.lines && refund.lines.length > 0 && (
        <div className="border-t border-gray-100 px-4 pb-4 pt-3">
          <table className="w-full text-sm">
            <thead className="text-xs text-gray-500">
              <tr>
                <th className="pb-2 text-left">Produit</th>
                <th className="pb-2 text-center">Qté retournée</th>
                <th className="pb-2 text-right">Prix unitaire</th>
                <th className="pb-2 text-right">Total ligne</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {refund.lines.map((line) => (
                <tr key={line.id}>
                  <td className="py-1.5">
                    <p className="font-medium text-gray-900">{line.product_name}</p>
                    <p className="text-xs text-gray-400">{line.product_sku}</p>
                  </td>
                  <td className="py-1.5 text-center font-medium text-orange-600">{line.quantity}</td>
                  <td className="py-1.5 text-right text-gray-600">{fmt(line.unit_price_applied)}</td>
                  <td className="py-1.5 text-right font-medium text-gray-900">{fmt(line.line_total)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Avertissement + actions admin */}
      <div className="border-t border-orange-100 bg-orange-50 px-4 py-3 rounded-b-xl">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-orange-700">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span className="text-xs">
              En attente d'approbation admin. Le stock n'est pas encore réintégré.
            </span>
          </div>

          {canApprove ? (
            <div className="flex flex-wrap items-center gap-2">
              {showRejectInput && (
                <input
                  type="text"
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="Motif du rejet (obligatoire)..."
                  className="rounded-lg border border-red-300 px-3 py-1.5 text-xs focus:outline-none focus:border-red-500 w-64"
                  autoFocus
                />
              )}
              <button
                onClick={handleReject}
                disabled={isProcessing || (showRejectInput && !rejectReason.trim())}
                className="flex items-center gap-1.5 rounded-lg border border-red-300 bg-white px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
              >
                <XCircle className="h-3.5 w-3.5" />
                {showRejectInput ? "Confirmer le rejet" : "Rejeter"}
              </button>
              {showRejectInput && (
                <button
                  onClick={() => { setShowRejectInput(false); setRejectReason(""); }}
                  className="text-xs text-gray-500 hover:text-gray-700"
                >
                  Annuler
                </button>
              )}
              <button
                onClick={handleApprove}
                disabled={isProcessing}
                className="flex items-center gap-1.5 rounded-lg bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700 disabled:opacity-50"
              >
                <CheckCircle2 className="h-3.5 w-3.5" />
                {approve.isPending ? "Traitement..." : "Approuver"}
              </button>
            </div>
          ) : (
            <span className="text-xs text-gray-500 italic">Droits admin requis pour approuver.</span>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page principale
// ---------------------------------------------------------------------------

export default function RefundsPage() {
  const { data: refunds = [], isLoading } = usePendingRefunds();
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const canApprove = hasPermission("sales:refund");

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Retours produits</h1>
        <p className="text-sm text-gray-500">
          Retours initiés par les vendeurs — approbation requise pour réintégrer le stock
        </p>
      </div>

      {/* Bannière workflow */}
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-4">
        <h3 className="mb-2 text-sm font-semibold text-blue-900">Comment fonctionne le retour ?</h3>
        <div className="flex flex-wrap gap-4 text-xs text-blue-800">
          <div className="flex items-center gap-2">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-blue-200 font-bold text-blue-800">1</span>
            <span>Le vendeur initie le retour depuis la vente concernée</span>
          </div>
          <div className="flex items-center gap-2 text-blue-400">→</div>
          <div className="flex items-center gap-2">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-orange-200 font-bold text-orange-800">2</span>
            <span>Le retour apparaît ici en attente d'approbation</span>
          </div>
          <div className="flex items-center gap-2 text-blue-400">→</div>
          <div className="flex items-center gap-2">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-green-200 font-bold text-green-800">3</span>
            <span>L'admin approuve → stock réintégré + client remboursé</span>
          </div>
        </div>
      </div>

      {/* Compteur */}
      {!isLoading && (
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 rounded-full bg-orange-100 px-3 py-1">
            <Clock className="h-3.5 w-3.5 text-orange-600" />
            <span className="text-xs font-medium text-orange-700">
              {refunds.length} retour{refunds.length !== 1 ? "s" : ""} en attente
            </span>
          </div>
        </div>
      )}

      {/* Liste */}
      {isLoading ? (
        <div className="rounded-xl bg-white p-8 text-center text-sm text-gray-400">
          Chargement...
        </div>
      ) : refunds.length === 0 ? (
        <div className="rounded-xl bg-white p-12 text-center shadow-sm ring-1 ring-gray-200">
          <CheckCircle2 className="mx-auto mb-3 h-10 w-10 text-green-400" />
          <p className="font-medium text-gray-700">Aucun retour en attente</p>
          <p className="mt-1 text-sm text-gray-400">
            Les retours initiés par les vendeurs apparaîtront ici.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {refunds.map((refund) => (
            <RefundCard key={refund.id} refund={refund} canApprove={canApprove} />
          ))}
        </div>
      )}
    </div>
  );
}
