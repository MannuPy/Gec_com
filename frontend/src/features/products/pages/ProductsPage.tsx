import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Loader2, Pencil, Plus, Search } from "lucide-react";

import { productsApi } from "@/api/endpoints/products";
import { stockApi } from "@/api/endpoints/stock";
import { getApiErrorMessage } from "@/api/client";
import { useAuthStore } from "@/app/store";
import { Modal } from "@/components/Modal";
import {
  PRODUCT_UNITS,
  type Product,
  type ProductCreatePayload,
  type ProductUpdatePayload,
} from "@/types/product";
import { formatCurrency, formatNumber } from "@/utils/format";

const PER_PAGE = 20;

const EMPTY_FORM = {
  sku: "",
  barcode: "",
  name: "",
  name_moore: "",
  description: "",
  category_id: "",
  brand_id: "",
  unit: "UNITE",
  simple_price: "",
  technician_price: "",
  purchase_price: "",
  min_stock_threshold: "0",
  is_active: true,
};

type ProductFormState = typeof EMPTY_FORM;

/**
 * Catalogue produits (RF-06/RF-07) : recherche, filtres categorie/marque,
 * pagination, stock du site courant, et CRUD complet (RF-08) via
 * modale de création/édition.
 * Cf. GET/POST/PATCH /api/v1/products, /categories, /brands, /stock.
 */
export default function ProductsPage() {
  const user = useAuthStore((s) => s.user);
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const canWrite = hasPermission("products:write");
  const queryClient = useQueryClient();

  const [search, setSearch] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [brandId, setBrandId] = useState("");
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Product | null>(null);

  const categoriesQuery = useQuery({
    queryKey: ["categories"],
    queryFn: productsApi.categories,
  });

  const brandsQuery = useQuery({
    queryKey: ["brands"],
    queryFn: productsApi.brands,
  });

  const productsQuery = useQuery({
    queryKey: ["products", { search, categoryId, brandId, page }],
    queryFn: () =>
      productsApi.list({
        search: search || undefined,
        category_id: categoryId || undefined,
        brand_id: brandId || undefined,
        page,
        per_page: PER_PAGE,
      }),
  });

  const canSeeStock = hasPermission("stock:read") && Boolean(user?.branch_id);

  const stockQuery = useQuery({
    queryKey: ["stock", user?.branch_id],
    queryFn: () => stockApi.list({ branch_id: user?.branch_id ?? undefined }),
    enabled: canSeeStock,
  });

  const stockByProduct = new Map<string, { quantity: number; belowMin: boolean }>();
  (stockQuery.data ?? []).forEach((item) => {
    stockByProduct.set(item.product_id, { quantity: item.quantity, belowMin: item.below_min });
  });

  const products = productsQuery.data?.data ?? [];
  const meta = productsQuery.data?.meta;
  const totalPages = meta ? Math.max(1, Math.ceil(meta.total / meta.per_page)) : 1;

  const resetToFirstPage = () => setPage(1);

  const openCreate = () => {
    setEditing(null);
    setModalOpen(true);
  };

  const openEdit = (product: Product) => {
    setEditing(product);
    setModalOpen(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold text-primary-dark">Produits</h1>
          <p className="text-sm text-muted">
            Catalogue des articles{user?.branch_name ? ` - stock du site ${user.branch_name}` : ""}
          </p>
        </div>
        {canWrite && (
          <button type="button" className="btn-primary" onClick={openCreate}>
            <Plus className="h-4 w-4" />
            Nouveau produit
          </button>
        )}
      </div>

      <div className="card space-y-4">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
            <input
              type="text"
              className="input pl-9"
              placeholder="Rechercher par nom, SKU ou code-barres"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                resetToFirstPage();
              }}
            />
          </div>

          <select
            className="input"
            value={categoryId}
            onChange={(e) => {
              setCategoryId(e.target.value);
              resetToFirstPage();
            }}
          >
            <option value="">Toutes les categories</option>
            {(categoriesQuery.data ?? []).map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>

          <select
            className="input"
            value={brandId}
            onChange={(e) => {
              setBrandId(e.target.value);
              resetToFirstPage();
            }}
          >
            <option value="">Toutes les marques</option>
            {(brandsQuery.data ?? []).map((brand) => (
              <option key={brand.id} value={brand.id}>
                {brand.name}
              </option>
            ))}
          </select>
        </div>

        {productsQuery.isLoading && (
          <div className="flex items-center gap-2 text-muted">
            <Loader2 className="h-4 w-4 animate-spin" />
            Chargement des produits...
          </div>
        )}

        {productsQuery.isError && (
          <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
            {getApiErrorMessage(productsQuery.error, "Impossible de charger les produits.")}
          </div>
        )}

        {productsQuery.isSuccess && (
          <>
            <div className="overflow-x-auto">
              <table className="table-base">
                <thead>
                  <tr>
                    <th>SKU</th>
                    <th>Produit</th>
                    <th>Categorie</th>
                    <th>Marque</th>
                    <th>Unite</th>
                    <th className="text-right">Prix public</th>
                    <th className="text-right">Prix technicien</th>
                    {canSeeStock && <th className="text-right">Stock</th>}
                    <th>Statut</th>
                    {canWrite && <th></th>}
                  </tr>
                </thead>
                <tbody>
                  {products.length === 0 && (
                    <tr>
                      <td colSpan={canSeeStock ? (canWrite ? 10 : 9) : canWrite ? 9 : 8} className="text-center text-muted">
                        Aucun produit ne correspond a ces criteres.
                      </td>
                    </tr>
                  )}
                  {products.map((product) => {
                    const stock = stockByProduct.get(product.id);
                    return (
                      <tr key={product.id}>
                        <td className="font-mono text-xs text-muted">{product.sku}</td>
                        <td>
                          <div className="font-medium text-primary-dark">{product.name}</div>
                          {product.name_moore && (
                            <div className="text-xs text-muted">{product.name_moore} (mooré)</div>
                          )}
                          {product.barcode && (
                            <div className="text-xs text-muted">{product.barcode}</div>
                          )}
                        </td>
                        <td>{product.category_name ?? "-"}</td>
                        <td>{product.brand_name ?? "-"}</td>
                        <td>{product.unit}</td>
                        <td className="text-right">{formatCurrency(product.simple_price)}</td>
                        <td className="text-right">{formatCurrency(product.technician_price)}</td>
                        {canSeeStock && (
                          <td className="text-right">
                            {stock ? (
                              <span
                                className={
                                  stock.belowMin ? "font-semibold text-amber-600" : "text-primary-dark"
                                }
                              >
                                {formatNumber(stock.quantity)}
                              </span>
                            ) : (
                              <span className="text-muted">-</span>
                            )}
                          </td>
                        )}
                        <td>
                          {product.is_active ? (
                            <span className="badge badge-success">Actif</span>
                          ) : (
                            <span className="badge badge-danger">Inactif</span>
                          )}
                        </td>
                        {canWrite && (
                          <td className="text-right">
                            <button type="button" className="btn-ghost p-1.5" onClick={() => openEdit(product)}>
                              <Pencil className="h-4 w-4" />
                            </button>
                          </td>
                        )}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {meta && (
              <div className="flex items-center justify-between border-t border-surface pt-3 text-sm text-muted">
                <span>
                  {formatNumber(meta.total)} produit{meta.total === 1 ? "" : "s"} - page {meta.page} / {totalPages}
                </span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    className="btn-secondary"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Precedent
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

      {modalOpen && (
        <ProductFormModal
          editing={editing}
          categories={categoriesQuery.data ?? []}
          brands={brandsQuery.data ?? []}
          onClose={() => setModalOpen(false)}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ["products"] });
            queryClient.invalidateQueries({ queryKey: ["categories"] });
            queryClient.invalidateQueries({ queryKey: ["brands"] });
            setModalOpen(false);
          }}
        />
      )}
    </div>
  );
}

interface ProductFormModalProps {
  editing: Product | null;
  categories: { id: string; name: string }[];
  brands: { id: string; name: string }[];
  onClose: () => void;
  onSuccess: () => void;
}

function ProductFormModal({ editing, categories, brands, onClose, onSuccess }: ProductFormModalProps) {
  const [form, setForm] = useState<ProductFormState>(
    editing
      ? {
          sku: editing.sku,
          barcode: editing.barcode ?? "",
          name: editing.name,
          name_moore: editing.name_moore ?? "",
          description: editing.description ?? "",
          category_id: editing.category_id ?? "",
          brand_id: editing.brand_id ?? "",
          unit: editing.unit,
          simple_price: editing.simple_price,
          technician_price: editing.technician_price,
          purchase_price: editing.purchase_price,
          min_stock_threshold: String(editing.min_stock_threshold),
          is_active: editing.is_active,
        }
      : EMPTY_FORM
  );
  const [newCategory, setNewCategory] = useState("");
  const [newBrand, setNewBrand] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const createCategoryMutation = useMutation({
    mutationFn: () => productsApi.createCategory({ name: newCategory.trim() }),
    onSuccess: (category) => {
      setForm((f) => ({ ...f, category_id: category.id }));
      setNewCategory("");
    },
  });

  const createBrandMutation = useMutation({
    mutationFn: () => productsApi.createBrand({ name: newBrand.trim() }),
    onSuccess: (brand) => {
      setForm((f) => ({ ...f, brand_id: brand.id }));
      setNewBrand("");
    },
  });

  const createMutation = useMutation({
    mutationFn: (payload: ProductCreatePayload) => productsApi.create(payload),
    onSuccess,
    onError: (error) => setFormError(getApiErrorMessage(error, "Impossible de créer le produit.")),
  });

  const updateMutation = useMutation({
    mutationFn: (payload: ProductUpdatePayload) => productsApi.update(editing!.id, payload),
    onSuccess,
    onError: (error) => setFormError(getApiErrorMessage(error, "Impossible de mettre à jour le produit.")),
  });

  const handleSubmit = () => {
    setFormError(null);
    if (!form.name.trim()) {
      setFormError("Le nom du produit est obligatoire.");
      return;
    }
    if (!form.simple_price || !form.technician_price) {
      setFormError("Les prix public et technicien sont obligatoires.");
      return;
    }

    if (editing) {
      updateMutation.mutate({
        barcode: form.barcode.trim() || null,
        name: form.name.trim(),
        name_moore: form.name_moore.trim() || null,
        description: form.description.trim() || null,
        category_id: form.category_id || null,
        brand_id: form.brand_id || null,
        unit: form.unit as ProductUpdatePayload["unit"],
        simple_price: form.simple_price,
        technician_price: form.technician_price,
        purchase_price: form.purchase_price || undefined,
        min_stock_threshold: Number(form.min_stock_threshold) || 0,
        is_active: form.is_active,
      });
      return;
    }

    if (!form.sku.trim()) {
      setFormError("Le SKU est obligatoire.");
      return;
    }
    createMutation.mutate({
      sku: form.sku.trim(),
      barcode: form.barcode.trim() || null,
      name: form.name.trim(),
      name_moore: form.name_moore.trim() || null,
      description: form.description.trim() || null,
      category_id: form.category_id || null,
      brand_id: form.brand_id || null,
      unit: form.unit as ProductCreatePayload["unit"],
      simple_price: form.simple_price,
      technician_price: form.technician_price,
      purchase_price: form.purchase_price || undefined,
      min_stock_threshold: Number(form.min_stock_threshold) || 0,
    });
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <Modal title={editing ? "Modifier le produit" : "Nouveau produit"} onClose={onClose} widthClassName="max-w-2xl">
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">SKU</label>
            <input
              type="text"
              className="input"
              value={form.sku}
              disabled={!!editing}
              onChange={(e) => setForm((f) => ({ ...f, sku: e.target.value }))}
            />
            {editing && <p className="mt-1 text-xs text-muted">Le SKU ne peut pas être modifié.</p>}
          </div>
          <div>
            <label className="label">Code-barres</label>
            <input
              type="text"
              className="input"
              value={form.barcode}
              onChange={(e) => setForm((f) => ({ ...f, barcode: e.target.value }))}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Nom (français)</label>
            <input
              type="text"
              className="input"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            />
          </div>
          <div>
            <label className="label">Nom (mooré)</label>
            <input
              type="text"
              className="input"
              placeholder="Désignation en mooré (RF-09)"
              value={form.name_moore}
              onChange={(e) => setForm((f) => ({ ...f, name_moore: e.target.value }))}
            />
          </div>
        </div>

        <div>
          <label className="label">Description</label>
          <textarea
            className="input"
            rows={2}
            value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Catégorie</label>
            <select
              className="input"
              value={form.category_id}
              onChange={(e) => setForm((f) => ({ ...f, category_id: e.target.value }))}
            >
              <option value="">Aucune</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
            <div className="mt-1 flex gap-2">
              <input
                type="text"
                className="input"
                placeholder="Nouvelle catégorie"
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
              />
              <button
                type="button"
                className="btn-secondary"
                disabled={!newCategory.trim() || createCategoryMutation.isPending}
                onClick={() => createCategoryMutation.mutate()}
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>
          </div>
          <div>
            <label className="label">Marque</label>
            <select
              className="input"
              value={form.brand_id}
              onChange={(e) => setForm((f) => ({ ...f, brand_id: e.target.value }))}
            >
              <option value="">Aucune</option>
              {brands.map((brand) => (
                <option key={brand.id} value={brand.id}>
                  {brand.name}
                </option>
              ))}
            </select>
            <div className="mt-1 flex gap-2">
              <input
                type="text"
                className="input"
                placeholder="Nouvelle marque"
                value={newBrand}
                onChange={(e) => setNewBrand(e.target.value)}
              />
              <button
                type="button"
                className="btn-secondary"
                disabled={!newBrand.trim() || createBrandMutation.isPending}
                onClick={() => createBrandMutation.mutate()}
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Unité</label>
            <select className="input" value={form.unit} onChange={(e) => setForm((f) => ({ ...f, unit: e.target.value }))}>
              {PRODUCT_UNITS.map((unit) => (
                <option key={unit} value={unit}>
                  {unit}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Seuil de stock minimum</label>
            <input
              type="number"
              min="0"
              step="1"
              className="input"
              value={form.min_stock_threshold}
              onChange={(e) => setForm((f) => ({ ...f, min_stock_threshold: e.target.value }))}
            />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="label">Prix public (FCFA)</label>
            <input
              type="number"
              min="0"
              step="1"
              className="input"
              value={form.simple_price}
              onChange={(e) => setForm((f) => ({ ...f, simple_price: e.target.value }))}
            />
          </div>
          <div>
            <label className="label">Prix technicien (FCFA)</label>
            <input
              type="number"
              min="0"
              step="1"
              className="input"
              value={form.technician_price}
              onChange={(e) => setForm((f) => ({ ...f, technician_price: e.target.value }))}
            />
          </div>
          <div>
            <label className="label">Prix d'achat (FCFA)</label>
            <input
              type="number"
              min="0"
              step="1"
              className="input"
              value={form.purchase_price}
              onChange={(e) => setForm((f) => ({ ...f, purchase_price: e.target.value }))}
            />
          </div>
        </div>

        {editing && (
          <label className="flex items-center gap-2 text-sm text-primary-dark">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
            />
            Produit actif
          </label>
        )}

        {formError && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{formError}</div>}

        <div className="flex justify-end gap-2 pt-2">
          <button type="button" className="btn-secondary" onClick={onClose}>
            Annuler
          </button>
          <button type="button" className="btn-primary" disabled={isPending} onClick={handleSubmit}>
            {isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            {editing ? "Enregistrer" : "Créer"}
          </button>
        </div>
      </div>
    </Modal>
  );
}
