import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Ban, ChevronLeft, ChevronRight, ClipboardCheck, Loader2, Plus } from "lucide-react";

import { inventoryApi } from "@/api/endpoints/inventory";
import { productsApi } from "@/api/endpoints/products";
import { getApiErrorMessage } from "@/api/client";
import { useAuthStore } from "@/app/store";
import { Modal } from "@/components/Modal";
import {
  STOCK_COUNT_STATUSES,
  type StockCount,
  type StockCountDetail,
  type StockCountLineUpdate,
  type StockCountStatus,
} from "@/types/inventory";
import { formatDateTime, formatNumber } from "@/utils/format";

const PER_PAGE = 20;

const STATUS_LABELS: Record<StockCountStatus, string> = {
  EN_COURS: "En cours",
  VALIDE: "Validée",
  ANNULE: "Annulée",
};

const STATUS_BADGES: Record<StockCountStatus, string> = {
  EN_COURS: "badge-warning",
  VALIDE: "badge-success",
  ANNULE: "badge-danger",
};

/**
 * Inventaire physique (RF-21 à RF-23) : ouverture de sessions de comptage,
 * saisie des quantités comptées et validation (génération des ajustements
 * de stock RG-33).
 * Cf. GET/POST /api/v1/inventory/counts.
 */
export default function InventoryPage() {
  const user = useAuthStore((s) => s.user);
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const canWrite = hasPermission("inventory:write");
  const queryClient = useQueryClient();

  const [branchId, setBranchId] = useState(user?.branch_id ?? "");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [openCountId, setOpenCountId] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);

  const branchesQuery = useQuery({
    queryKey: ["branches"],
    queryFn: productsApi.branches,
    enabled: !user?.branch_id,
  });

  const countsQuery = useQuery({
    queryKey: ["stock-counts", branchId, status, page],
    queryFn: () =>
      inventoryApi.list({
        branch_id: branchId || undefined,
        status: status || undefined,
        page,
        per_page: PER_PAGE,
      }),
  });

  const counts = countsQuery.data?.data ?? [];
  const meta = countsQuery.data?.meta;
  const totalPages = meta ? Math.max(1, Math.ceil(meta.total / meta.per_page)) : 1;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold text-primary-dark">Inventaire physique</h1>
          <p className="text-sm text-muted">Sessions de comptage et régularisation du stock (RF-21 à RF-23)</p>
        </div>
        {canWrite && (
          <button type="button" className="btn-primary" onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4" />
            Nouvelle session
          </button>
        )}
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
            {STOCK_COUNT_STATUSES.map((s) => (
              <option key={s} value={s}>
                {STATUS_LABELS[s]}
              </option>
            ))}
          </select>
        </div>

        {countsQuery.isLoading && (
          <div className="flex items-center gap-2 text-muted">
            <Loader2 className="h-4 w-4 animate-spin" />
            Chargement...
          </div>
        )}

        {countsQuery.isError && (
          <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
            {getApiErrorMessage(countsQuery.error, "Impossible de charger les sessions d'inventaire.")}
          </div>
        )}

        {countsQuery.isSuccess && (
          <>
            <div className="overflow-x-auto">
              <table className="table-base">
                <thead>
                  <tr>
                    <th>Référence</th>
                    <th>Site</th>
                    <th>Statut</th>
                    <th>Ouverte par</th>
                    <th>Date d'ouverture</th>
                    <th className="text-right">Lignes</th>
                    <th className="text-right">Écarts</th>
                    <th>Validée</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {counts.length === 0 && (
                    <tr>
                      <td colSpan={9} className="text-center text-muted">
                        Aucune session d'inventaire trouvée.
                      </td>
                    </tr>
                  )}
                  {counts.map((count: StockCount) => (
                    <tr key={count.id}>
                      <td className="font-mono text-xs text-muted">{count.reference}</td>
                      <td>{count.branch_name}</td>
                      <td>
                        <span className={`badge ${STATUS_BADGES[count.status]}`}>{STATUS_LABELS[count.status]}</span>
                      </td>
                      <td>{count.created_by_name}</td>
                      <td className="whitespace-nowrap text-xs text-muted">{formatDateTime(count.created_at)}</td>
                      <td className="text-right">{formatNumber(count.lines_count)}</td>
                      <td className={`text-right ${count.lines_with_variance > 0 ? "font-semibold text-amber-600" : ""}`}>
                        {formatNumber(count.lines_with_variance)}
                      </td>
                      <td className="text-xs text-muted">
                        {count.validated_by_name
                          ? `${count.validated_by_name} - ${formatDateTime(count.validated_at as string)}`
                          : "-"}
                      </td>
                      <td className="text-right">
                        <button type="button" className="btn-secondary" onClick={() => setOpenCountId(count.id)}>
                          Ouvrir
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {meta && (
              <div className="flex items-center justify-between border-t border-surface pt-3 text-sm text-muted">
                <span>
                  {formatNumber(meta.total)} session{meta.total === 1 ? "" : "s"} - page {meta.page} / {totalPages}
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

      {createOpen && (
        <CreateCountModal
          defaultBranchId={user?.branch_id ?? ""}
          branches={branchesQuery.data ?? []}
          onClose={() => setCreateOpen(false)}
          onCreated={(count) => {
            queryClient.invalidateQueries({ queryKey: ["stock-counts"] });
            setCreateOpen(false);
            setOpenCountId(count.id);
          }}
        />
      )}

      {openCountId && (
        <CountDetailModal
          countId={openCountId}
          canWrite={canWrite}
          onClose={() => setOpenCountId(null)}
          onChanged={() => queryClient.invalidateQueries({ queryKey: ["stock-counts"] })}
        />
      )}
    </div>
  );
}

interface CreateCountModalProps {
  defaultBranchId: string;
  branches: { id: string; name: string }[];
  onClose: () => void;
  onCreated: (count: StockCountDetail) => void;
}

function CreateCountModal({ defaultBranchId, branches, onClose, onCreated }: CreateCountModalProps) {
  const [branchId, setBranchId] = useState(defaultBranchId);
  const [formError, setFormError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: () => inventoryApi.create({ branch_id: branchId }),
    onSuccess: onCreated,
    onError: (error) => setFormError(getApiErrorMessage(error, "Impossible d'ouvrir la session d'inventaire.")),
  });

  const handleSubmit = () => {
    setFormError(null);
    if (!branchId) {
      setFormError("Veuillez sélectionner un site.");
      return;
    }
    createMutation.mutate();
  };

  return (
    <Modal title="Nouvelle session d'inventaire" onClose={onClose}>
      <div className="space-y-4">
        <div>
          <label className="label">Site</label>
          <select className="input" value={branchId} onChange={(e) => setBranchId(e.target.value)} disabled={!!defaultBranchId}>
            <option value="">Sélectionner un site</option>
            {branches.map((branch) => (
              <option key={branch.id} value={branch.id}>
                {branch.name}
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-muted">
            Une ligne sera créée pour chaque produit actif disposant d'un stock sur ce site.
          </p>
        </div>

        {formError && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{formError}</div>}

        <div className="flex justify-end gap-2 pt-2">
          <button type="button" className="btn-secondary" onClick={onClose}>
            Annuler
          </button>
          <button type="button" className="btn-primary" disabled={createMutation.isPending} onClick={handleSubmit}>
            {createMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            Ouvrir la session
          </button>
        </div>
      </div>
    </Modal>
  );
}

interface CountDetailModalProps {
  countId: string;
  canWrite: boolean;
  onClose: () => void;
  onChanged: () => void;
}

function CountDetailModal({ countId, canWrite, onClose, onChanged }: CountDetailModalProps) {
  const [counted, setCounted] = useState<Record<string, string>>({});
  const [comments, setComments] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);

  const detailQuery = useQuery({
    queryKey: ["stock-count", countId],
    queryFn: () => inventoryApi.get(countId),
  });

  const saveMutation = useMutation({
    mutationFn: (lines: StockCountLineUpdate[]) => inventoryApi.updateLines(countId, { lines }),
    onSuccess: () => {
      setFormError(null);
      detailQuery.refetch();
      onChanged();
    },
    onError: (error) => setFormError(getApiErrorMessage(error, "Impossible d'enregistrer les quantités comptées.")),
  });

  const validateMutation = useMutation({
    mutationFn: () => inventoryApi.validate(countId),
    onSuccess: () => {
      setFormError(null);
      detailQuery.refetch();
      onChanged();
    },
    onError: (error) => setFormError(getApiErrorMessage(error, "Impossible de valider la session d'inventaire.")),
  });

  const cancelMutation = useMutation({
    mutationFn: () => inventoryApi.cancel(countId),
    onSuccess: () => {
      setFormError(null);
      detailQuery.refetch();
      onChanged();
    },
    onError: (error) => setFormError(getApiErrorMessage(error, "Impossible d'annuler la session d'inventaire.")),
  });

  const count = detailQuery.data;
  const isEditable = count?.status === "EN_COURS";

  const handleSave = () => {
    setFormError(null);
    if (!count) return;

    const lines: StockCountLineUpdate[] = [];
    for (const line of count.lines) {
      const raw = counted[line.id];
      if (raw === undefined || raw.trim() === "") continue;
      const value = Number(raw);
      if (!Number.isInteger(value) || value < 0) {
        setFormError(`Quantité invalide pour ${line.product_name} : un entier positif est attendu.`);
        return;
      }
      lines.push({
        product_id: line.product_id,
        counted_quantity: value,
        comment: comments[line.id]?.trim() || undefined,
      });
    }

    if (lines.length === 0) {
      setFormError("Saisissez au moins une quantité comptée.");
      return;
    }

    saveMutation.mutate(lines);
  };

  return (
    <Modal title={count ? `Session ${count.reference}` : "Session d'inventaire"} onClose={onClose} widthClassName="max-w-4xl">
      {detailQuery.isLoading && (
        <div className="flex items-center gap-2 text-muted">
          <Loader2 className="h-4 w-4 animate-spin" />
          Chargement...
        </div>
      )}

      {detailQuery.isError && (
        <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
          {getApiErrorMessage(detailQuery.error, "Impossible de charger la session d'inventaire.")}
        </div>
      )}

      {count && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-muted">
            <span>
              {count.branch_name} - Ouverte par {count.created_by_name} le {formatDateTime(count.created_at)}
            </span>
            <span className={`badge ${STATUS_BADGES[count.status]}`}>{STATUS_LABELS[count.status]}</span>
          </div>

          <div className="overflow-x-auto">
            <table className="table-base">
              <thead>
                <tr>
                  <th>Produit</th>
                  <th className="text-right">Stock théorique</th>
                  <th className="text-right">Quantité comptée</th>
                  <th className="text-right">Écart</th>
                  <th>Commentaire</th>
                </tr>
              </thead>
              <tbody>
                {count.lines.map((line) => {
                  const hasVariance = line.variance !== null && line.variance !== 0;
                  return (
                    <tr key={line.id}>
                      <td>
                        <div className="font-medium text-primary-dark">{line.product_name}</div>
                        <div className="text-xs text-muted">{line.product_sku}</div>
                      </td>
                      <td className="text-right">{formatNumber(line.theoretical_quantity)}</td>
                      <td className="text-right">
                        {isEditable ? (
                          <input
                            type="number"
                            min="0"
                            step="1"
                            className="input w-24 text-right"
                            value={counted[line.id] ?? (line.counted_quantity ?? "")}
                            onChange={(e) => setCounted((c) => ({ ...c, [line.id]: e.target.value }))}
                          />
                        ) : (
                          formatNumber(line.counted_quantity ?? 0)
                        )}
                      </td>
                      <td className={`text-right ${hasVariance ? "font-semibold text-amber-600" : ""}`}>
                        {line.variance === null ? "-" : `${line.variance > 0 ? "+" : ""}${formatNumber(line.variance)}`}
                        {line.variance_pct !== null ? ` (${line.variance_pct.toFixed(1)}%)` : ""}
                      </td>
                      <td>
                        {isEditable ? (
                          <input
                            type="text"
                            className="input w-full"
                            placeholder={hasVariance ? "Justification requise si écart > seuil" : "Optionnel"}
                            value={comments[line.id] ?? line.comment ?? ""}
                            onChange={(e) => setComments((c) => ({ ...c, [line.id]: e.target.value }))}
                          />
                        ) : (
                          <span className="text-xs text-muted">{line.comment ?? "-"}</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {count.adjustments_applied !== undefined && (
            <p className="text-sm text-muted">
              {formatNumber(count.adjustments_applied)} ajustement{count.adjustments_applied === 1 ? "" : "s"} de stock appliqué
              {count.adjustments_applied === 1 ? "" : "s"} lors de la validation.
            </p>
          )}

          {formError && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{formError}</div>}

          {canWrite && isEditable && (
            <div className="flex flex-wrap justify-between gap-2 border-t border-surface pt-3">
              {/* Bouton annulation — à gauche */}
              <button
                type="button"
                className="btn-ghost text-red-600 hover:bg-red-50"
                disabled={cancelMutation.isPending}
                onClick={() => {
                  if (window.confirm("Annuler cette session d'inventaire ? Aucun ajustement de stock ne sera effectué.")) {
                    cancelMutation.mutate();
                  }
                }}
              >
                {cancelMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Ban className="h-4 w-4" />
                )}
                Annuler la session
              </button>

              {/* Enregistrer + Valider — à droite */}
              <div className="flex gap-2">
                <button type="button" className="btn-secondary" disabled={saveMutation.isPending} onClick={handleSave}>
                  {saveMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                  Enregistrer les quantités
                </button>
                <button
                  type="button"
                  className="btn-primary"
                  disabled={validateMutation.isPending}
                  onClick={() => validateMutation.mutate()}
                >
                  {validateMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <ClipboardCheck className="h-4 w-4" />
                  )}
                  Valider la session
                </button>
              </div>
            </div>
          )}

          {/* Affichage si session annulée */}
          {count?.status === "ANNULE" && (
            <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 border-t border-surface mt-3">
              Session annulée{count.cancelled_by_name ? ` par ${count.cancelled_by_name}` : ""}. Aucun ajustement de stock effectué.
            </div>
          )}
        </div>
      )}
    </Modal>
  );
}
