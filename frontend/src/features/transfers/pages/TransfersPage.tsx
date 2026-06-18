import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus, Search, Send, Trash2, Truck, XCircle } from "lucide-react";

import { productsApi } from "@/api/endpoints/products";
import { transfersApi } from "@/api/endpoints/transfers";
import { getApiErrorMessage } from "@/api/client";
import { useAuthStore } from "@/app/store";
import { Modal } from "@/components/Modal";
import type { Product } from "@/types/product";
import {
  TRANSFER_STATUSES,
  type ReceiveLinePayload,
  type Transfer,
  type TransferCreatePayload,
  type TransferLineWritePayload,
  type TransferStatus,
} from "@/types/transfer";
import { formatDateTime, formatNumber } from "@/utils/format";

const STATUS_LABELS: Record<TransferStatus, string> = {
  BROUILLON: "Brouillon",
  EN_TRANSIT: "En transit",
  RECU: "Reçu",
  ANNULE: "Annulé",
};

const STATUS_BADGES: Record<TransferStatus, string> = {
  BROUILLON: "badge-warning",
  EN_TRANSIT: "badge-info",
  RECU: "badge-success",
  ANNULE: "badge-danger",
};

/**
 * Transferts inter-sites (RF-19/RF-20) : brouillon -> envoi -> réception
 * (avec écarts éventuels, RG-14) ou annulation.
 * Cf. GET/POST /api/v1/transfers, POST /transfers/:id/{send,receive,cancel}.
 */
export default function TransfersPage() {
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const canWrite = hasPermission("transfers:write");
  const queryClient = useQueryClient();

  const [statusFilter, setStatusFilter] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [detail, setDetail] = useState<Transfer | null>(null);

  const branchesQuery = useQuery({
    queryKey: ["branches"],
    queryFn: productsApi.branches,
  });

  const transfersQuery = useQuery({
    queryKey: ["transfers", statusFilter],
    queryFn: () => transfersApi.list({ status: (statusFilter as TransferStatus) || undefined }),
  });

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["transfers"] });
    queryClient.invalidateQueries({ queryKey: ["stock"] });
  };

  const sendMutation = useMutation({
    mutationFn: (id: string) => transfersApi.send(id),
    onSuccess: (t) => {
      refresh();
      setDetail(t);
    },
  });

  const cancelMutation = useMutation({
    mutationFn: (id: string) => transfersApi.cancel(id),
    onSuccess: (t) => {
      refresh();
      setDetail(t);
    },
  });

  const transfers = transfersQuery.data ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold text-primary-dark">Transferts inter-sites</h1>
          <p className="text-sm text-muted">Mouvements de stock entre sites (dépôt et points de vente)</p>
        </div>
        {canWrite && (
          <button type="button" className="btn-primary" onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4" />
            Nouveau transfert
          </button>
        )}
      </div>

      <div className="card space-y-4">
        <select className="input max-w-xs" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">Tous les statuts</option>
          {TRANSFER_STATUSES.map((status) => (
            <option key={status} value={status}>
              {STATUS_LABELS[status]}
            </option>
          ))}
        </select>

        {transfersQuery.isLoading && (
          <div className="flex items-center gap-2 text-muted">
            <Loader2 className="h-4 w-4 animate-spin" />
            Chargement...
          </div>
        )}

        {transfersQuery.isError && (
          <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
            {getApiErrorMessage(transfersQuery.error, "Impossible de charger les transferts.")}
          </div>
        )}

        {transfersQuery.isSuccess && (
          <div className="overflow-x-auto">
            <table className="table-base">
              <thead>
                <tr>
                  <th>Référence</th>
                  <th>Origine</th>
                  <th>Destination</th>
                  <th>Statut</th>
                  <th>Créé le</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {transfers.length === 0 && (
                  <tr>
                    <td colSpan={6} className="text-center text-muted">
                      Aucun transfert trouvé.
                    </td>
                  </tr>
                )}
                {transfers.map((transfer) => (
                  <tr key={transfer.id}>
                    <td className="font-mono text-xs text-muted">{transfer.reference}</td>
                    <td className="font-medium text-primary-dark">{transfer.source_branch_name}</td>
                    <td className="font-medium text-primary-dark">{transfer.destination_branch_name}</td>
                    <td>
                      <span className={`badge ${STATUS_BADGES[transfer.status]}`}>{STATUS_LABELS[transfer.status]}</span>
                    </td>
                    <td className="whitespace-nowrap text-xs text-muted">{formatDateTime(transfer.created_at)}</td>
                    <td className="text-right">
                      <button type="button" className="btn-secondary" onClick={() => setDetail(transfer)}>
                        Détails
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {createOpen && (
        <TransferCreateModal
          branches={branchesQuery.data ?? []}
          onClose={() => setCreateOpen(false)}
          onSuccess={() => {
            refresh();
            setCreateOpen(false);
          }}
        />
      )}

      {detail && (
        <Modal title={`Transfert ${detail.reference}`} onClose={() => setDetail(null)} widthClassName="max-w-2xl">
          <TransferDetail
            transfer={detail}
            canWrite={canWrite}
            onSend={() => sendMutation.mutate(detail.id)}
            onCancel={() => cancelMutation.mutate(detail.id)}
            sendPending={sendMutation.isPending}
            cancelPending={cancelMutation.isPending}
            onReceived={(t) => {
              refresh();
              setDetail(t);
            }}
          />
        </Modal>
      )}
    </div>
  );
}

interface TransferDetailProps {
  transfer: Transfer;
  canWrite: boolean;
  onSend: () => void;
  onCancel: () => void;
  sendPending: boolean;
  cancelPending: boolean;
  onReceived: (t: Transfer) => void;
}

function TransferDetail({ transfer, canWrite, onSend, onCancel, sendPending, cancelPending, onReceived }: TransferDetailProps) {
  const [receiveMode, setReceiveMode] = useState(false);
  const [received, setReceived] = useState<Record<string, string>>(
    Object.fromEntries(transfer.lines.map((l) => [l.id, String(l.quantity_sent)]))
  );
  const [comments, setComments] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);

  const receiveMutation = useMutation({
    mutationFn: (lines: ReceiveLinePayload[]) => transfersApi.receive(transfer.id, { lines }),
    onSuccess: onReceived,
    onError: (error) => setFormError(getApiErrorMessage(error, "Impossible de confirmer la réception.")),
  });

  const handleReceiveSubmit = () => {
    setFormError(null);
    const lines: ReceiveLinePayload[] = transfer.lines.map((l) => {
      const qty = Number(received[l.id]);
      const variance = qty !== l.quantity_sent;
      return {
        line_id: l.id,
        quantity_received: Number.isFinite(qty) ? qty : 0,
        variance_comment: variance ? comments[l.id]?.trim() || "Écart constaté à la réception" : null,
      };
    });
    receiveMutation.mutate(lines);
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-muted">
        <span>
          {transfer.source_branch_name} → {transfer.destination_branch_name}
        </span>
        <span className={`badge ${STATUS_BADGES[transfer.status]}`}>{STATUS_LABELS[transfer.status]}</span>
      </div>

      <div className="overflow-x-auto">
      <table className="table-base">
        <thead>
          <tr>
            <th>Produit</th>
            <th className="text-right">Qté envoyée</th>
            {transfer.status === "RECU" && <th className="text-right">Qté reçue</th>}
            {receiveMode && <th className="text-right">Qté reçue</th>}
            {(transfer.status === "RECU" || receiveMode) && <th>Écart / commentaire</th>}
          </tr>
        </thead>
        <tbody>
          {transfer.lines.map((line) => (
            <tr key={line.id}>
              <td>
                <div className="font-medium text-primary-dark">{line.product_name}</div>
                <div className="text-xs text-muted">{line.product_sku}</div>
              </td>
              <td className="text-right">{formatNumber(line.quantity_sent)}</td>
              {transfer.status === "RECU" && !receiveMode && (
                <>
                  <td className="text-right">{line.quantity_received !== null ? formatNumber(line.quantity_received) : "-"}</td>
                  <td className="text-xs text-muted">{line.variance_comment ?? "-"}</td>
                </>
              )}
              {receiveMode && (
                <>
                  <td className="text-right">
                    <input
                      type="number"
                      min="0"
                      step="1"
                      className="input w-24 text-right"
                      value={received[line.id] ?? ""}
                      onChange={(e) => setReceived((r) => ({ ...r, [line.id]: e.target.value }))}
                    />
                  </td>
                  <td>
                    <input
                      type="text"
                      className="input"
                      placeholder="Commentaire si écart"
                      value={comments[line.id] ?? ""}
                      onChange={(e) => setComments((c) => ({ ...c, [line.id]: e.target.value }))}
                    />
                  </td>
                </>
              )}
            </tr>
          ))}
        </tbody>
      </table>
      </div>

      {formError && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{formError}</div>}

      {canWrite && transfer.status === "BROUILLON" && (
        <div className="flex justify-end gap-2 border-t border-surface pt-3">
          <button type="button" className="btn-danger" disabled={cancelPending} onClick={onCancel}>
            {cancelPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <XCircle className="h-4 w-4" />}
            Annuler
          </button>
          <button type="button" className="btn-primary" disabled={sendPending} onClick={onSend}>
            {sendPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            Envoyer
          </button>
        </div>
      )}

      {canWrite && transfer.status === "EN_TRANSIT" && (
        <div className="flex justify-end gap-2 border-t border-surface pt-3">
          {!receiveMode ? (
            <button type="button" className="btn-primary" onClick={() => setReceiveMode(true)}>
              <Truck className="h-4 w-4" />
              Confirmer la réception
            </button>
          ) : (
            <>
              <button type="button" className="btn-secondary" onClick={() => setReceiveMode(false)}>
                Annuler
              </button>
              <button type="button" className="btn-primary" disabled={receiveMutation.isPending} onClick={handleReceiveSubmit}>
                {receiveMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                Valider la réception
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}

interface TransferCreateModalProps {
  branches: { id: string; name: string }[];
  onClose: () => void;
  onSuccess: () => void;
}

interface DraftLine extends TransferLineWritePayload {
  product_name: string;
  product_sku: string;
}

function TransferCreateModal({ branches, onClose, onSuccess }: TransferCreateModalProps) {
  const user = useAuthStore((s) => s.user);
  const [sourceBranchId, setSourceBranchId] = useState(user?.branch_id ?? "");
  const [destinationBranchId, setDestinationBranchId] = useState("");
  const [lines, setLines] = useState<DraftLine[]>([]);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    const handle = setTimeout(() => setSearch(searchInput.trim()), 300);
    return () => clearTimeout(handle);
  }, [searchInput]);

  const productsQuery = useQuery({
    queryKey: ["transfer-products", search],
    queryFn: () => productsApi.list({ search: search || undefined, per_page: 8, is_active: true }),
    enabled: search.length > 0,
  });

  const createMutation = useMutation({
    mutationFn: (payload: TransferCreatePayload) => transfersApi.create(payload),
    onSuccess,
    onError: (error) => setFormError(getApiErrorMessage(error, "Impossible de créer le transfert.")),
  });

  const addProduct = (product: Product) => {
    if (lines.some((l) => l.product_id === product.id)) return;
    setLines((prev) => [
      ...prev,
      { product_id: product.id, product_name: product.name, product_sku: product.sku, quantity_sent: 1 },
    ]);
    setSearchInput("");
  };

  const updateQty = (productId: string, value: string) => {
    setLines((prev) =>
      prev.map((l) => (l.product_id === productId ? { ...l, quantity_sent: Math.max(1, Number(value) || 1) } : l))
    );
  };

  const removeLine = (productId: string) => {
    setLines((prev) => prev.filter((l) => l.product_id !== productId));
  };

  const handleSubmit = () => {
    setFormError(null);
    if (!sourceBranchId || !destinationBranchId) {
      setFormError("Veuillez sélectionner les sites d'origine et de destination.");
      return;
    }
    if (sourceBranchId === destinationBranchId) {
      setFormError("Le site d'origine et de destination doivent être différents.");
      return;
    }
    if (lines.length === 0) {
      setFormError("Ajoutez au moins une ligne de produit.");
      return;
    }
    createMutation.mutate({
      source_branch_id: sourceBranchId,
      destination_branch_id: destinationBranchId,
      lines: lines.map((l) => ({ product_id: l.product_id, quantity_sent: l.quantity_sent })),
    });
  };

  return (
    <Modal title="Nouveau transfert" onClose={onClose} widthClassName="max-w-2xl">
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Site d'origine</label>
            <select className="input" value={sourceBranchId} onChange={(e) => setSourceBranchId(e.target.value)}>
              <option value="">Sélectionner</option>
              {branches.map((branch) => (
                <option key={branch.id} value={branch.id}>
                  {branch.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Site de destination</label>
            <select className="input" value={destinationBranchId} onChange={(e) => setDestinationBranchId(e.target.value)}>
              <option value="">Sélectionner</option>
              {branches.map((branch) => (
                <option key={branch.id} value={branch.id}>
                  {branch.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="label">Ajouter un produit</label>
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
            <input
              type="text"
              className="input pl-9"
              placeholder="Rechercher par nom, SKU ou code-barres"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
          </div>
          {productsQuery.isSuccess && (productsQuery.data?.data ?? []).length > 0 && (
            <div className="mt-2 max-h-40 space-y-1 overflow-y-auto">
              {(productsQuery.data?.data ?? []).map((product) => (
                <button
                  key={product.id}
                  type="button"
                  className="flex w-full items-center justify-between rounded-lg border border-surface px-3 py-2 text-left hover:border-primary hover:bg-primary/5"
                  onClick={() => addProduct(product)}
                >
                  <span className="text-sm font-medium text-primary-dark">{product.name}</span>
                  <span className="text-xs text-muted">{product.sku}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {lines.length > 0 && (
          <div className="overflow-x-auto">
          <table className="table-base">
            <thead>
              <tr>
                <th>Produit</th>
                <th className="text-right">Quantité</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {lines.map((line) => (
                <tr key={line.product_id}>
                  <td>
                    <div className="font-medium text-primary-dark">{line.product_name}</div>
                    <div className="text-xs text-muted">{line.product_sku}</div>
                  </td>
                  <td className="text-right">
                    <input
                      type="number"
                      min="1"
                      step="1"
                      className="input w-20 text-right"
                      value={line.quantity_sent}
                      onChange={(e) => updateQty(line.product_id, e.target.value)}
                    />
                  </td>
                  <td className="text-right">
                    <button type="button" className="btn-ghost p-1.5 text-red-600" onClick={() => removeLine(line.product_id)}>
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        )}

        {formError && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{formError}</div>}

        <div className="flex justify-end gap-2 pt-2">
          <button type="button" className="btn-secondary" onClick={onClose}>
            Annuler
          </button>
          <button type="button" className="btn-primary" disabled={createMutation.isPending} onClick={handleSubmit}>
            {createMutation.isPending && <Loader2 className="h-4 w-4 animate