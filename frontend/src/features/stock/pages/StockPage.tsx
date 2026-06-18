import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Loader2, Plus, Search } from "lucide-react";

import { productsApi } from "@/api/endpoints/products";
import { stockApi } from "@/api/endpoints/stock";
import { getApiErrorMessage } from "@/api/client";
import { useAuthStore } from "@/app/store";
import { Modal } from "@/components/Modal";
import type { Product } from "@/types/product";
import type { StockAdjustmentPayload, StockMovementType } from "@/types/stock";
import { formatDateTime, formatNumber } from "@/utils/format";

const PER_PAGE = 20;

const MOVEMENT_LABELS: Record<StockMovementType, string> = {
  ENTREE_RECEPTION: "Entrée réception",
  SORTIE_TRANSFERT: "Sortie transfert",
  ENTREE_TRANSFERT: "Entrée transfert",
  SORTIE_VENTE: "Sortie vente",
  ENTREE_RETOUR_VENTE: "Retour vente",
  AJUSTEMENT_INVENTAIRE: "Ajustement inventaire",
  AJUSTEMENT_MANUEL: "Ajustement manuel",
};

/**
 * Suivi des stocks (RF-13/RF-14) : niveaux par site, historique des
 * mouvements et ajustements manuels (RG-15).
 * Cf. GET /api/v1/stock, /stock/movements, POST /stock/adjustments.
 */
export default function StockPage() {
  const user = useAuthStore((s) => s.user);
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const canAdjust = hasPermission("stock:write");
  const queryClient = useQueryClient();

  const [tab, setTab] = useState<"niveaux" | "mouvements">("niveaux");
  const [branchId, setBranchId] = useState(user?.branch_id ?? "");
  const [belowMinOnly, setBelowMinOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);

  const branchesQuery = useQuery({
    queryKey: ["branches"],
    queryFn: productsApi.branches,
    enabled: !user?.branch_id,
  });

  const stockQuery = useQuery({
    queryKey: ["stock", branchId, belowMinOnly],
    queryFn: () => stockApi.list({ branch_id: branchId || undefined, below_min: belowMinOnly || undefined }),
    enabled: tab === "niveaux",
  });

  const movementsQuery = useQuery({
    queryKey: ["stock-movements", branchId, page],
    queryFn: () => stockApi.movements({ branch_id: branchId || undefined, page, per_page: PER_PAGE }),
    enabled: tab === "mouvements",
  });

  const stockItems = stockQuery.data ?? [];
  const movements = movementsQuery.data?.data ?? [];
  const meta = movementsQuery.data?.meta;
  const totalPages = meta ? Math.max(1, Math.ceil(meta.total / meta.per_page)) : 1;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold text-primary-dark">Stock</h1>
          <p className="text-sm text-muted">Niveaux de stock, mouvements et ajustements</p>
        </div>
        {canAdjust && (
          <button type="button" className="btn-primary" onClick={() => setModalOpen(true)}>
            <Plus className="h-4 w-4" />
            Ajustement
          </button>
        )}
      </div>

      <div className="card space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex gap-2">
            <button
              type="button"
              className={tab === "niveaux" ? "btn-primary" : "btn-secondary"}
              onClick={() => setTab("niveaux")}
            >
              Niveaux
            </button>
            <button
              type="button"
              className={tab === "mouvements" ? "btn-primary" : "btn-secondary"}
              onClick={() => {
                setTab("mouvements");
                setPage(1);
              }}
            >
              Mouvements
            </button>
          </div>

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

          {tab === "niveaux" && (
            <label className="flex items-center gap-2 text-sm text-primary-dark">
              <input
                type="checkbox"
                checked={belowMinOnly}
                onChange={(e) => setBelowMinOnly(e.target.checked)}
              />
              Sous le seuil minimum uniquement
            </label>
          )}
        </div>

        {tab === "niveaux" && (
          <>
            {stockQuery.isLoading && (
              <div className="flex items-center gap-2 text-muted">
                <Loader2 className="h-4 w-4 animate-spin" />
                Chargement...
              </div>
            )}

            {stockQuery.isError && (
              <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
                {getApiErrorMessage(stockQuery.error, "Impossible de charger le stock.")}
              </div>
            )}

            {stockQuery.isSuccess && (
              <div className="overflow-x-auto">
                <table className="table-base">
                  <thead>
                    <tr>
                      <th>SKU</th>
                      <th>Produit</th>
                      <th>Site</th>
                      <th className="text-right">Quantité</th>
                      <th className="text-right">Seuil mini</th>
                      <th>Statut</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stockItems.length === 0 && (
                      <tr>
                        <td colSpan={6} className="text-center text-muted">
                          Aucun article en stock pour ces critères.
                        </td>
                      </tr>
                    )}
                    {stockItems.map((item) => (
                      <tr key={item.id}>
                        <td className="font-mono text-xs text-muted">{item.product_sku}</td>
                        <td className="font-medium text-primary-dark">{item.product_name}</td>
                        <td>{item.branch_name}</td>
                        <td className={`text-right ${item.below_min ? "font-semibold text-amber-600" : ""}`}>
                          {formatNumber(item.quantity)}
                        </td>
                        <td className="text-right">{formatNumber(item.min_stock_threshold)}</td>
                        <td>
                          {item.below_min ? (
                            <span className="badge badge-warning">Sous le seuil</span>
                          ) : (
                            <span className="badge badge-success">OK</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}

        {tab === "mouvements" && (
          <>
            {movementsQuery.isLoading && (
              <div className="flex items-center gap-2 text-muted">
                <Loader2 className="h-4 w-4 animate-spin" />
                Chargement...
              </div>
            )}

            {movementsQuery.isError && (
              <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
                {getApiErrorMessage(movementsQuery.error, "Impossible de charger les mouvements.")}
              </div>
            )}

            {movementsQuery.isSuccess && (
              <>
                <div className="overflow-x-auto">
                  <table className="table-base">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Produit</th>
                        <th>Site</th>
                        <th>Type</th>
                        <th className="text-right">Quantité</th>
                        <th>Commentaire</th>
                      </tr>
                    </thead>
                    <tbody>
                      {movements.length === 0 && (
                        <tr>
                          <td colSpan={6} className="text-center text-muted">
                            Aucun mouvement trouvé.
                          </td>
                        </tr>
                      )}
                      {movements.map((movement) => (
                        <tr key={movement.id}>
                          <td className="whitespace-nowrap text-xs text-muted">
                            {formatDateTime(movement.created_at)}
                          </td>
                          <td className="font-medium text-primary-dark">{movement.product_name}</td>
                          <td>{movement.branch_name}</td>
                          <td>
                            <span className="badge badge-info">
                              {MOVEMENT_LABELS[movement.movement_type] ?? movement.movement_type}
                            </span>
                          </td>
                          <td className={`text-right font-medium ${movement.quantity >= 0 ? "text-green-700" : "text-red-700"}`}>
                            {movement.quantity >= 0 ? "+" : ""}
                            {formatNumber(movement.quantity)}
                          </td>
                          <td className="text-xs text-muted">{movement.comment ?? "-"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {meta && (
                  <div className="flex items-center justify-between border-t border-surface pt-3 text-sm text-muted">
                    <span>
                      {formatNumber(meta.total)} mouvement{meta.total === 1 ? "" : "s"} - page {meta.page} / {totalPages}
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
          </>
        )}
      </div>

      {modalOpen && (
        <AdjustmentModal
          defaultBranchId={user?.branch_id ?? ""}
          branches={branchesQuery.data ?? []}
          onClose={() => setModalOpen(false)}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ["stock"] });
            queryClient.invalidateQueries({ queryKey: ["stock-movements"] });
            setModalOpen(false);
          }}
        />
      )}
    </div>
  );
}

interface AdjustmentModalProps {
  defaultBranchId: string;
  branches: { id: string; name: string }[];
  onClose: () => void;
  onSuccess: () => void;
}

function AdjustmentModal({ defaultBranchId, branches, onClose, onSuccess }: AdjustmentModalProps) {
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [branchId, setBranchId] = useState(defaultBranchId);
  const [quantityDelta, setQuantityDelta] = useState("");
  const [comment, setComment] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    const handle = setTimeout(() => setSearch(searchInput.trim()), 300);
    return () => clearTimeout(handle);
  }, [searchInput]);

  const productsQuery = useQuery({
    queryKey: ["adjustment-products", search],
    queryFn: () => productsApi.list({ search: search || undefined, per_page: 8, is_active: true }),
    enabled: search.length > 0,
  });

  const adjustMutation = useMutation({
    mutationFn: (payload: StockAdjustmentPayload) => stockApi.adjust(payload),
    onSuccess,
    onError: (error) => setFormError(getApiErrorMessage(error, "Impossible d'enregistrer l'ajustement.")),
  });

  const handleSubmit = () => {
    setFormError(null);
    if (!selectedProduct) {
      setFormError("Veuillez sélectionner un produit.");
      return;
    }
    if (!branchId) {
      setFormError("Veuillez sélectionner un site.");
      return;
    }
    const delta = Number(quantityDelta);
    if (!Number.isInteger(delta) || delta === 0) {
      setFormError("La quantité doit être un entier non nul (positif ou négatif).");
      return;
    }
    if (comment.trim().length < 3) {
      setFormError("Un commentaire d'au moins 3 caractères est obligatoire (justification).");
      return;
    }
    adjustMutation.mutate({
      product_id: selectedProduct.id,
      branch_id: branchId,
      quantity_delta: delta,
      comment: comment.trim(),
    });
  };

  return (
    <Modal title="Ajustement de stock" onClose={onClose}>
      <div className="space-y-4">
        <div>
          <label className="label">Produit</label>
          {selectedProduct ? (
            <div className="flex items-center justify-between rounded-lg border border-surface px-3 py-2">
              <div>
                <p className="text-sm font-medium text-primary-dark">{selectedProduct.name}</p>
                <p className="text-xs text-muted">{selectedProduct.sku}</p>
              </div>
              <button type="button" className="btn-ghost text-xs" onClick={() => setSelectedProduct(null)}>
                Changer
              </button>
            </div>
          ) : (
            <>
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
                <div className="mt-2 max-h-48 space-y-1 overflow-y-auto">
                  {(productsQuery.data?.data ?? []).map((product) => (
                    <button
                      key={product.id}
                      type="button"
                      className="flex w-full items-center justify-between rounded-lg border border-surface px-3 py-2 text-left hover:border-primary hover:bg-primary/5"
                      onClick={() => setSelectedProduct(product)}
                    >
                      <span className="text-sm font-medium text-primary-dark">{product.name}</span>
                      <span className="text-xs text-muted">{product.sku}</span>
                    </button>
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        <div>
          <label className="label">Site</label>
          <select className="input" value={branchId} onChange={(e) => setBranchId(e.target.value)}>
            <option value="">Sélectionner un site</option>
            {branches.map((branch) => (
              <option key={branch.id} value={branch.id}>
                {branch.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="label">Quantité (+ ou -)</label>
          <input
            type="number"
            step="1"
            className="input"
            placeholder="Ex. -2 ou 5"
            value={quantityDelta}
            onChange={(e) => setQuantityDelta(e.target.value)}
          />
        </div>

        <div>
          <label className="label">Commentaire / justification</label>
          <textarea
            className="input"
            rows={2}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Ex. casse, inventaire physique, erreur de saisie..."
          />
        </div>

        {formError && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{formError}</div>}

        <div className="flex justify-end gap-2 pt-2">
          <button type="button" className="btn-secondary" onClick={onClose}>
            Annuler
          </button>
          <button type="button" className="btn-primary" disabled={adjustMutation.isPending} onClick={handleSubmit}>
            {adjustMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            Enregistrer
          </button>
        </div>
      </div>
    </Modal>
  );
}
