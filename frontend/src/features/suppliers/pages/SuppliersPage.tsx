import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Loader2, Plus, Search, Trash2 } from "lucide-react";

import { productsApi } from "@/api/endpoints/products";
import { suppliersApi } from "@/api/endpoints/suppliers";
import { getApiErrorMessage } from "@/api/client";
import { useAuthStore } from "@/app/store";
import { Modal } from "@/components/Modal";
import type { Product } from "@/types/product";
import type {
  Reception,
  ReceptionCreatePayload,
  ReceptionLineWritePayload,
  Supplier,
  SupplierWritePayload,
} from "@/types/supplier";
import { formatCurrency, formatDateTime } from "@/utils/format";

const EMPTY_SUPPLIER: SupplierWritePayload = {
  name: "",
  contact_name: "",
  phone: "",
  email: "",
  address: "",
  is_active: true,
};

/**
 * Fournisseurs & réceptions (RF-15 à RF-18) : gestion du référentiel
 * fournisseurs et des bons de réception (brouillon -> validation, RG-12/13).
 * Cf. GET/POST/PUT /api/v1/suppliers, GET/POST /receptions, POST /receptions/:id/validate.
 */
export default function SuppliersPage() {
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const canWriteSuppliers = hasPermission("suppliers:write");
  const canReadReceptions = hasPermission("receptions:read");
  const canWriteReceptions = hasPermission("receptions:write");
  const queryClient = useQueryClient();

  const [tab, setTab] = useState<"fournisseurs" | "receptions">("fournisseurs");

  const [supplierModalOpen, setSupplierModalOpen] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState<Supplier | null>(null);
  const [supplierForm, setSupplierForm] = useState<SupplierWritePayload>(EMPTY_SUPPLIER);
  const [supplierFormError, setSupplierFormError] = useState<string | null>(null);

  const [receptionModalOpen, setReceptionModalOpen] = useState(false);
  const [detailReception, setDetailReception] = useState<Reception | null>(null);

  const suppliersQuery = useQuery({
    queryKey: ["suppliers"],
    queryFn: () => suppliersApi.list(),
  });

  const receptionsQuery = useQuery({
    queryKey: ["receptions"],
    queryFn: () => suppliersApi.receptions.list(),
    enabled: tab === "receptions" && canReadReceptions,
  });

  const branchesQuery = useQuery({
    queryKey: ["branches"],
    queryFn: productsApi.branches,
    enabled: tab === "receptions",
  });

  const openCreateSupplier = () => {
    setEditingSupplier(null);
    setSupplierForm(EMPTY_SUPPLIER);
    setSupplierFormError(null);
    setSupplierModalOpen(true);
  };

  const openEditSupplier = (supplier: Supplier) => {
    setEditingSupplier(supplier);
    setSupplierForm({
      name: supplier.name,
      contact_name: supplier.contact_name ?? "",
      phone: supplier.phone ?? "",
      email: supplier.email ?? "",
      address: supplier.address ?? "",
      is_active: supplier.is_active,
    });
    setSupplierFormError(null);
    setSupplierModalOpen(true);
  };

  const saveSupplierMutation = useMutation({
    mutationFn: (payload: SupplierWritePayload) =>
      editingSupplier ? suppliersApi.update(editingSupplier.id, payload) : suppliersApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["suppliers"] });
      setSupplierModalOpen(false);
    },
    onError: (error) => setSupplierFormError(getApiErrorMessage(error, "Impossible d'enregistrer le fournisseur.")),
  });

  const handleSupplierSubmit = () => {
    setSupplierFormError(null);
    if (!supplierForm.name.trim()) {
      setSupplierFormError("Le nom du fournisseur est obligatoire.");
      return;
    }
    saveSupplierMutation.mutate({
      ...supplierForm,
      contact_name: supplierForm.contact_name?.trim() || null,
      phone: supplierForm.phone?.trim() || null,
      email: supplierForm.email?.trim() || null,
      address: supplierForm.address?.trim() || null,
    });
  };

  const validateMutation = useMutation({
    mutationFn: (id: string) => suppliersApi.receptions.validate(id),
    onSuccess: (reception) => {
      queryClient.invalidateQueries({ queryKey: ["receptions"] });
      queryClient.invalidateQueries({ queryKey: ["stock"] });
      setDetailReception(reception);
    },
  });

  const suppliers = suppliersQuery.data ?? [];
  const receptions = receptionsQuery.data ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold text-primary-dark">Fournisseurs & réceptions</h1>
          <p className="text-sm text-muted">Référentiel fournisseurs et bons de réception</p>
        </div>
        {tab === "fournisseurs" && canWriteSuppliers && (
          <button type="button" className="btn-primary" onClick={openCreateSupplier}>
            <Plus className="h-4 w-4" />
            Nouveau fournisseur
          </button>
        )}
        {tab === "receptions" && canWriteReceptions && (
          <button type="button" className="btn-primary" onClick={() => setReceptionModalOpen(true)}>
            <Plus className="h-4 w-4" />
            Nouvelle réception
          </button>
        )}
      </div>

      <div className="flex gap-2">
        <button
          type="button"
          className={tab === "fournisseurs" ? "btn-primary" : "btn-secondary"}
          onClick={() => setTab("fournisseurs")}
        >
          Fournisseurs
        </button>
        {canReadReceptions && (
          <button
            type="button"
            className={tab === "receptions" ? "btn-primary" : "btn-secondary"}
            onClick={() => setTab("receptions")}
          >
            Réceptions
          </button>
        )}
      </div>

      {tab === "fournisseurs" && (
        <div className="card">
          {suppliersQuery.isLoading && (
            <div className="flex items-center gap-2 text-muted">
              <Loader2 className="h-4 w-4 animate-spin" />
              Chargement...
            </div>
          )}

          {suppliersQuery.isError && (
            <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
              {getApiErrorMessage(suppliersQuery.error, "Impossible de charger les fournisseurs.")}
            </div>
          )}

          {suppliersQuery.isSuccess && (
            <div className="overflow-x-auto">
              <table className="table-base">
                <thead>
                  <tr>
                    <th>Nom</th>
                    <th>Contact</th>
                    <th>Téléphone</th>
                    <th>Email</th>
                    <th>Statut</th>
                    {canWriteSuppliers && <th></th>}
                  </tr>
                </thead>
                <tbody>
                  {suppliers.length === 0 && (
                    <tr>
                      <td colSpan={canWriteSuppliers ? 6 : 5} className="text-center text-muted">
                        Aucun fournisseur enregistré.
                      </td>
                    </tr>
                  )}
                  {suppliers.map((supplier) => (
                    <tr key={supplier.id}>
                      <td className="font-medium text-primary-dark">{supplier.name}</td>
                      <td>{supplier.contact_name ?? "-"}</td>
                      <td>{supplier.phone ?? "-"}</td>
                      <td>{supplier.email ?? "-"}</td>
                      <td>
                        {supplier.is_active ? (
                          <span className="badge badge-success">Actif</span>
                        ) : (
                          <span className="badge badge-danger">Inactif</span>
                        )}
                      </td>
                      {canWriteSuppliers && (
                        <td className="text-right">
                          <button type="button" className="btn-secondary" onClick={() => openEditSupplier(supplier)}>
                            Modifier
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === "receptions" && (
        <div className="card">
          {receptionsQuery.isLoading && (
            <div className="flex items-center gap-2 text-muted">
              <Loader2 className="h-4 w-4 animate-spin" />
              Chargement...
            </div>
          )}

          {receptionsQuery.isError && (
            <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
              {getApiErrorMessage(receptionsQuery.error, "Impossible de charger les réceptions.")}
            </div>
          )}

          {receptionsQuery.isSuccess && (
            <div className="overflow-x-auto">
              <table className="table-base">
                <thead>
                  <tr>
                    <th>Référence</th>
                    <th>Fournisseur</th>
                    <th>Site</th>
                    <th>Statut</th>
                    <th className="text-right">Montant total</th>
                    <th>Créée le</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {receptions.length === 0 && (
                    <tr>
                      <td colSpan={7} className="text-center text-muted">
                        Aucune réception enregistrée.
                      </td>
                    </tr>
                  )}
                  {receptions.map((reception) => (
                    <tr key={reception.id}>
                      <td className="font-mono text-xs text-muted">{reception.reference}</td>
                      <td className="font-medium text-primary-dark">{reception.supplier_name}</td>
                      <td>{reception.branch_name}</td>
                      <td>
                        {reception.status === "VALIDEE" ? (
                          <span className="badge badge-success">Validée</span>
                        ) : (
                          <span className="badge badge-warning">Brouillon</span>
                        )}
                      </td>
                      <td className="text-right">{formatCurrency(reception.total_amount)}</td>
                      <td className="whitespace-nowrap text-xs text-muted">{formatDateTime(reception.created_at)}</td>
                      <td className="text-right">
                        <button type="button" className="btn-secondary" onClick={() => setDetailReception(reception)}>
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
      )}

      {supplierModalOpen && (
        <Modal title={editingSupplier ? "Modifier le fournisseur" : "Nouveau fournisseur"} onClose={() => setSupplierModalOpen(false)}>
          <div className="space-y-4">
            <div>
              <label className="label">Nom</label>
              <input
                type="text"
                className="input"
                value={supplierForm.name}
                onChange={(e) => setSupplierForm((f) => ({ ...f, name: e.target.value }))}
              />
            </div>
            <div>
              <label className="label">Contact</label>
              <input
                type="text"
                className="input"
                value={supplierForm.contact_name ?? ""}
                onChange={(e) => setSupplierForm((f) => ({ ...f, contact_name: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Téléphone</label>
                <input
                  type="text"
                  className="input"
                  value={supplierForm.phone ?? ""}
                  onChange={(e) => setSupplierForm((f) => ({ ...f, phone: e.target.value }))}
                />
              </div>
              <div>
                <label className="label">Email</label>
                <input
                  type="email"
                  className="input"
                  value={supplierForm.email ?? ""}
                  onChange={(e) => setSupplierForm((f) => ({ ...f, email: e.target.value }))}
                />
              </div>
            </div>
            <div>
              <label className="label">Adresse</label>
              <textarea
                className="input"
                rows={2}
                value={supplierForm.address ?? ""}
                onChange={(e) => setSupplierForm((f) => ({ ...f, address: e.target.value }))}
              />
            </div>
            {editingSupplier && (
              <label className="flex items-center gap-2 text-sm text-primary-dark">
                <input
                  type="checkbox"
                  checked={supplierForm.is_active ?? true}
                  onChange={(e) => setSupplierForm((f) => ({ ...f, is_active: e.target.checked }))}
                />
                Fournisseur actif
              </label>
            )}
            {supplierFormError && (
              <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{supplierFormError}</div>
            )}
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" className="btn-secondary" onClick={() => setSupplierModalOpen(false)}>
                Annuler
              </button>
              <button
                type="button"
                className="btn-primary"
                disabled={saveSupplierMutation.isPending}
                onClick={handleSupplierSubmit}
              >
                {saveSupplierMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                {editingSupplier ? "Enregistrer" : "Créer"}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {receptionModalOpen && (
        <ReceptionCreateModal
          suppliers={suppliers}
          branches={branchesQuery.data ?? []}
          onClose={() => setReceptionModalOpen(false)}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ["receptions"] });
            setReceptionModalOpen(false);
          }}
        />
      )}

      {detailReception && (
        <Modal title={`Réception ${detailReception.reference}`} onClose={() => setDetailReception(null)} widthClassName="max-w-2xl">
          <div className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-muted">
              <span>
                {detailReception.supplier_name} - {detailReception.branch_name}
              </span>
              {detailReception.status === "VALIDEE" ? (
                <span className="badge badge-success">Validée</span>
              ) : (
                <span className="badge badge-warning">Brouillon</span>
              )}
            </div>

            <div className="overflow-x-auto">
            <table className="table-base">
              <thead>
                <tr>
                  <th>Produit</th>
                  <th className="text-right">Quantité</th>
                  <th className="text-right">Prix d'achat unitaire</th>
                  <th className="text-right">Total ligne</th>
                </tr>
              </thead>
              <tbody>
                {detailReception.lines.map((line) => (
                  <tr key={line.id}>
                    <td>
                      <div className="font-medium text-primary-dark">{line.product_name}</div>
                      <div className="text-xs text-muted">{line.product_sku}</div>
                    </td>
                    <td className="text-right">{line.quantity}</td>
                    <td className="text-right">{formatCurrency(line.unit_purchase_price)}</td>
                    <td className="text-right">
                      {formatCurrency(Number(line.unit_purchase_price) * line.quantity)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>

            <div className="text-right text-lg font-semibold text-primary-dark">
              Total : {formatCurrency(detailReception.total_amount)}
            </div>

            {detailReception.status === "BROUILLON" && canWriteReceptions && (
              <div className="flex justify-end gap-2 border-t border-surface pt-3">
                <button
                  type="button"
                  className="btn-primary"
                  disabled={validateMutation.isPending}
                  onClick={() => validateMutation.mutate(detailReception.id)}
                >
                  {validateMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <CheckCircle2 className="h-4 w-4" />
                  )}
                  Valider la réception (entrée en stock)
                </button>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}

interface ReceptionCreateModalProps {
  suppliers: Supplier[];
  branches: { id: string; name: string }[];
  onClose: () => void;
  onSuccess: () => void;
}

interface DraftLine extends ReceptionLineWritePayload {
  product_name: string;
  product_sku: string;
}

function ReceptionCreateModal({ suppliers, branches, onClose, onSuccess }: ReceptionCreateModalProps) {
  const user = useAuthStore((s) => s.user);
  const [supplierId, setSupplierId] = useState("");
  const [branchId, setBranchId] = useState(user?.branch_id ?? "");
  const [lines, setLines] = useState<DraftLine[]>([]);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    const handle = setTimeout(() => setSearch(searchInput.trim()), 300);
    return () => clearTimeout(handle);
  }, [searchInput]);

  const productsQuery = useQuery({
    queryKey: ["reception-products", search],
    queryFn: () => productsApi.list({ search: search || undefined, per_page: 8, is_active: true }),
    enabled: search.length > 0,
  });

  const createMutation = useMutation({
    mutationFn: (payload: ReceptionCreatePayload) => suppliersApi.receptions.create(payload),
    onSuccess,
    onError: (error) => setFormError(getApiErrorMessage(error, "Impossible de créer la réception.")),
  });

  const addProduct = (product: Product) => {
    if (lines.some((l) => l.product_id === product.id)) return;
    setLines((prev) => [
      ...prev,
      {
        product_id: product.id,
        product_name: product.name,
        product_sku: product.sku,
        quantity: 1,
        unit_purchase_price: product.purchase_price || "0",
      },
    ]);
    setSearchInput("");
  };

  const updateLine = (productId: string, field: "quantity" | "unit_purchase_price", value: string) => {
    setLines((prev) =>
      prev.map((l) =>
        l.product_id === productId
          ? { ...l, [field]: field === "quantity" ? Math.max(1, Number(value) || 1) : value }
          : l
      )
    );
  };

  const removeLine = (productId: string) => {
    setLines((prev) => prev.filter((l) => l.product_id !== productId));
  };

  const total = lines.reduce((sum, l) => sum + Number(l.unit_purchase_price || 0) * l.quantity, 0);

  const handleSubmit = () => {
    setFormError(null);
    if (!supplierId) {
      setFormError("Veuillez sélectionner un fournisseur.");
      return;
    }
    if (!branchId) {
      setFormError("Veuillez sélectionner un site de réception.");
      return;
    }
    if (lines.length === 0) {
      setFormError("Ajoutez au moins une ligne de produit.");
      return;
    }
    createMutation.mutate({
      supplier_id: supplierId,
      branch_id: branchId,
      lines: lines.map((l) => ({
        product_id: l.product_id,
        quantity: l.quantity,
        unit_purchase_price: l.unit_purchase_price,
      })),
    });
  };

  return (
    <Modal title="Nouvelle réception" onClose={onClose} widthClassName="max-w-2xl">
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Fournisseur</label>
            <select className="input" value={supplierId} onChange={(e) => setSupplierId(e.target.value)}>
              <option value="">Sélectionner</option>
              {suppliers.filter((s) => s.is_active).map((supplier) => (
                <option key={supplier.id} value={supplier.id}>
                  {supplier.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Site de réception</label>
            <select className="input" value={branchId} onChange={(e) => setBranchId(e.target.value)}>
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
                <th className="text-right">Prix d'achat unitaire</th>
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
                      value={line.quantity}
                      onChange={(e) => updateLine(line.product_id, "quantity", e.target.value)}
                    />
                  </td>
                  <td className="text-right">
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      className="input w-28 text-right"
                      value={line.unit_purchase_price}
                      onChange={(e) => updateLine(line.product_id, "unit_purchase_price", e.target.value)}
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

        {lines.length > 0 && (
          <p className="text-right text-sm font-semibold text-primary-dark">Total : {formatCurrency(total)}</p>
        )}

        {formError && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{formError}</div>}

        <div className="flex justify-end gap-2 pt-2">
          <button type="button" className="btn-secondary" onClick={onClose}>
            Annuler
          </button>
          <button type="button" className="btn-primary" disabled={createMutation.isPending} onClick={handleSubmit}>
            {createMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <CheckCircle2 className="h-4 w-4" />
            )}
            Enregistrer la réception
          </button>
        </div>
      </div>
    </Modal>
  );
}

