import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Minus, Plus, Search, ShoppingCart, Trash2, WifiOff } from "lucide-react";

import { customersApi } from "@/api/endpoints/customers";
import { productsApi } from "@/api/endpoints/products";
import { salesApi } from "@/api/endpoints/sales";
import { getApiErrorMessage } from "@/api/client";
import { useAuthStore } from "@/app/store";
import { useCatalogSync } from "@/offline/catalogSync";
import { db, type CachedProduct, type OfflineSale, type OfflineSaleLine } from "@/offline/db";
import { useOnlineStatus } from "@/offline/useOnlineStatus";
import type { Product } from "@/types/product";
import type { Sale, SaleCreatePayload } from "@/types/sale";
import { formatCurrency } from "@/utils/format";

/**
 * Sous-ensemble de champs communs à `Product` (API) et `CachedProduct`
 * (IndexedDB, mode hors-ligne) — suffisant pour la recherche et le panier.
 * Cf. docs/26-GESTION-OFFLINE-PWA.md §26.4.
 */
interface POSProduct {
  id: string;
  sku: string;
  name: string;
  /** Désignation en mooré (RF-09), affichage bilingue du libellé produit. */
  name_moore?: string | null;
  unit: string;
  simple_price: string | number;
  technician_price: string | number;
}

interface CartLine {
  product: POSProduct;
  quantity: number;
}

/** Récépissé local d'une vente enregistrée hors-ligne (§26.5, §26.8). */
interface OfflineReceipt {
  offlineUuid: string;
  lines: { name: string; quantity: number; unitPrice: number; lineTotal: number }[];
  subtotal: number;
  discountRate: number;
  discountAmount: number;
  total: number;
  paymentType: "CASH" | "CREDIT";
  customerName: string | null;
}

const PRODUCT_PAGE_SIZE = 8;

/**
 * Caisse (POS) - UC-11/UC-12. Recherche produit, panier, remise (RG-22/23),
 * client + credit (RG-26), paiement, soumission a POST /sales (RG-24/25/27).
 *
 * Mode hors-ligne (RF-20, §26) : si le réseau est indisponible, la recherche
 * produit utilise le cache local (IndexedDB) et la vente est enregistrée
 * localement (`sync_status=PENDING`) en attendant la synchronisation.
 */
export default function POSPage() {
  const user = useAuthStore((s) => s.user);
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const queryClient = useQueryClient();
  const isOnline = useOnlineStatus();

  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [cart, setCart] = useState<CartLine[]>([]);
  const [discountRate, setDiscountRate] = useState(0);
  const [paymentType, setPaymentType] = useState<"CASH" | "CREDIT">("CASH");
  const [customerId, setCustomerId] = useState("");
  const [branchId, setBranchId] = useState(user?.branch_id ?? "");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [lastSale, setLastSale] = useState<Sale | null>(null);
  const [offlineReceipt, setOfflineReceipt] = useState<OfflineReceipt | null>(null);
  const [offlineProducts, setOfflineProducts] = useState<CachedProduct[]>([]);

  // Recherche debouncee pour eviter de spammer l'API a chaque frappe.
  useEffect(() => {
    const handle = setTimeout(() => setSearch(searchInput.trim()), 300);
    return () => clearTimeout(handle);
  }, [searchInput]);

  // Cache catalogue/remises pour le mode hors-ligne (§26.7).
  useCatalogSync(branchId || user?.branch_id || null);

  const branchesQuery = useQuery({
    queryKey: ["branches"],
    queryFn: productsApi.branches,
    enabled: !user?.branch_id && isOnline,
  });

  const productsQuery = useQuery({
    queryKey: ["pos-products", search],
    queryFn: () => productsApi.list({ search: search || undefined, per_page: PRODUCT_PAGE_SIZE, is_active: true }),
    enabled: isOnline,
  });

  // Recherche produit dans le cache local (IndexedDB) lorsque hors-ligne.
  useEffect(() => {
    if (isOnline) {
      setOfflineProducts([]);
      return;
    }

    let active = true;
    const term = search.trim().toLowerCase();

    const query = term
      ? db.products
          .filter(
            (p) =>
              p.name.toLowerCase().includes(term) ||
              (p.name_moore ?? "").toLowerCase().includes(term) ||
              p.sku.toLowerCase().includes(term) ||
              (p.barcode ?? "").toLowerCase().includes(term)
          )
          .limit(PRODUCT_PAGE_SIZE)
          .toArray()
      : db.products.orderBy("name").limit(PRODUCT_PAGE_SIZE).toArray();

    void query.then((rows) => {
      if (active) setOfflineProducts(rows);
    });

    return () => {
      active = false;
    };
  }, [isOnline, search]);

  const customersQuery = useQuery({
    queryKey: ["customers"],
    queryFn: () => customersApi.list(),
    enabled: isOnline,
  });

  const selectedCustomer = useMemo(
    () => (customersQuery.data ?? []).find((c) => c.id === customerId) ?? null,
    [customersQuery.data, customerId]
  );

  const priceType = selectedCustomer?.customer_type ?? "SIMPLE";

  const unitPriceFor = (product: POSProduct): number =>
    Number(priceType === "TECHNICIEN" ? product.technician_price : product.simple_price);

  const subtotal = cart.reduce((sum, line) => sum + unitPriceFor(line.product) * line.quantity, 0);
  const discountAmount = Math.round((subtotal * discountRate) / 100);
  const total = subtotal - discountAmount;

  const displayProducts: POSProduct[] = isOnline
    ? (productsQuery.data?.data ?? [])
    : offlineProducts;

  const stockById = useMemo(() => {
    const map = new Map<string, number>();
    if (!isOnline) {
      for (const p of offlineProducts) map.set(p.id, p.stock_quantity);
    }
    return map;
  }, [isOnline, offlineProducts]);

  const addToCart = (product: POSProduct) => {
    setCart((prev) => {
      const existing = prev.find((line) => line.product.id === product.id);
      if (existing) {
        return prev.map((line) =>
          line.product.id === product.id ? { ...line, quantity: line.quantity + 1 } : line
        );
      }
      return [...prev, { product, quantity: 1 }];
    });
  };

  const updateQuantity = (productId: string, quantity: number) => {
    if (quantity <= 0) {
      setCart((prev) => prev.filter((line) => line.product.id !== productId));
      return;
    }
    setCart((prev) =>
      prev.map((line) => (line.product.id === productId ? { ...line, quantity } : line))
    );
  };

  const removeFromCart = (productId: string) => {
    setCart((prev) => prev.filter((line) => line.product.id !== productId));
  };

  const resetCartState = () => {
    setCart([]);
    setDiscountRate(0);
    setCustomerId("");
    setPaymentType("CASH");
  };

  const createSaleMutation = useMutation({
    mutationFn: (payload: SaleCreatePayload) => salesApi.create(payload),
    onSuccess: (sale) => {
      setLastSale(sale);
      setOfflineReceipt(null);
      resetCartState();
      setSubmitError(null);
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["stock"] });
    },
    onError: (error) => {
      setSubmitError(getApiErrorMessage(error, "Impossible d'enregistrer la vente."));
    },
  });

  const runValidations = (): string | null => {
    if (!branchId) {
      return "Veuillez selectionner un site de vente.";
    }
    if (cart.length === 0) {
      return "Le panier est vide.";
    }
    if (paymentType === "CREDIT" && !customerId) {
      return "Une vente a credit necessite un client identifie (RG-26).";
    }
    if (discountRate < 0 || discountRate > 100) {
      return "Le taux de remise doit être compris entre 0 et 100.";
    }
    return null;
  };

  const submitOnline = () => {
    const payload: SaleCreatePayload = {
      branch_id: branchId,
      customer_id: customerId || null,
      payment_type: paymentType,
      discount_rate: discountRate,
      lines: cart.map((line) => ({ product_id: line.product.id, quantity: line.quantity })),
    };

    createSaleMutation.mutate(payload);
  };

  /**
   * Enregistre la vente dans IndexedDB (`sync_status=PENDING`) quand le
   * réseau est indisponible (§26.5). Le reçu local indique explicitement
   * que la synchronisation est différée.
   */
  const submitOffline = async () => {
    const offlineUuid =
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `offline-${Date.now()}-${Math.random().toString(36).slice(2)}`;

    const lines: OfflineSaleLine[] = cart.map((line) => ({
      product_id: line.product.id,
      quantity: line.quantity,
      unit_price_applied: unitPriceFor(line.product),
    }));

    const sale: OfflineSale = {
      offline_uuid: offlineUuid,
      branch_id: branchId,
      cashier_id: user?.id ?? "",
      customer_id: customerId || null,
      payment_type: paymentType,
      discount_rate: discountRate,
      lines,
      created_at_local: new Date().toISOString(),
      sync_status: "PENDING",
      sync_message: null,
      server_sale_id: null,
    };

    await db.sales.add(sale);

    setOfflineReceipt({
      offlineUuid,
      lines: cart.map((line) => ({
        name: line.product.name,
        quantity: line.quantity,
        unitPrice: unitPriceFor(line.product),
        lineTotal: unitPriceFor(line.product) * line.quantity,
      })),
      subtotal,
      discountRate,
      discountAmount,
      total,
      paymentType,
      customerName: selectedCustomer?.full_name ?? null,
    });
    setLastSale(null);
    resetCartState();
    setSubmitError(null);
  };

  const handleSubmit = () => {
    setSubmitError(null);

    const error = runValidations();
    if (error) {
      setSubmitError(error);
      return;
    }

    if (isOnline) {
      submitOnline();
    } else {
      void submitOffline();
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-primary-dark">Caisse</h1>
          <p className="text-sm text-muted">Enregistrer une vente et encaisser le client</p>
        </div>
        {!isOnline && (
          <div className="flex items-center gap-1.5 rounded-lg bg-amber-50 px-3 py-2 text-xs font-medium text-amber-700">
            <WifiOff className="h-4 w-4 shrink-0" />
            <span>Mode hors-ligne — catalogue en cache, ventes synchronisées au retour du réseau</span>
          </div>
        )}
      </div>

      {lastSale && (
        <div className="card border-l-4 border-l-primary">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="card-title">Vente enregistree : {lastSale.reference}</h2>
              <p className="text-sm text-muted">
                {lastSale.customer_name ?? "Client comptant"} - {lastSale.payment_type === "CREDIT" ? "Credit" : "Comptant"}
              </p>
            </div>
            <button type="button" className="btn-secondary" onClick={() => setLastSale(null)}>
              Fermer
            </button>
          </div>

          <div className="overflow-x-auto">
          <table className="table-base mt-4">
            <thead>
              <tr>
                <th>Produit</th>
                <th className="text-right">Qte</th>
                <th className="text-right">Prix unitaire</th>
                <th className="text-right">Total ligne</th>
              </tr>
            </thead>
            <tbody>
              {lastSale.lines.map((line) => (
                <tr key={line.id}>
                  <td>{line.product_name}</td>
                  <td className="text-right">{line.quantity}</td>
                  <td className="text-right">{formatCurrency(line.unit_price_applied)}</td>
                  <td className="text-right">{formatCurrency(line.line_total)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>

          <div className="mt-4 space-y-1 text-right text-sm">
            <p className="text-muted">Sous-total : {formatCurrency(lastSale.subtotal)}</p>
            {Number(lastSale.discount_amount) > 0 && (
              <p className="text-muted">
                Remise ({lastSale.discount_rate}%) : -{formatCurrency(lastSale.discount_amount)}
              </p>
            )}
            <p className="text-lg font-semibold text-primary-dark">
              Total : {formatCurrency(lastSale.total)}
            </p>
          </div>
        </div>
      )}

      {offlineReceipt && (
        <div className="card border-l-4 border-l-amber-500">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="card-title flex items-center gap-2">
                <WifiOff className="h-4 w-4 text-amber-600" />
                Vente enregistrée hors-ligne
              </h2>
              <p className="text-sm text-muted">
                {offlineReceipt.customerName ?? "Client comptant"} -{" "}
                {offlineReceipt.paymentType === "CREDIT" ? "Credit" : "Comptant"}
              </p>
              <p className="mt-1 text-xs font-medium text-amber-700">
                Hors-ligne — en attente de synchronisation (réf. locale {offlineReceipt.offlineUuid.slice(0, 8)})
              </p>
            </div>
            <button type="button" className="btn-secondary" onClick={() => setOfflineReceipt(null)}>
              Fermer
            </button>
          </div>

          <div className="overflow-x-auto">
          <table className="table-base mt-4">
            <thead>
              <tr>
                <th>Produit</th>
                <th className="text-right">Qte</th>
                <th className="text-right">Prix unitaire</th>
                <th className="text-right">Total ligne</th>
              </tr>
            </thead>
            <tbody>
              {offlineReceipt.lines.map((line, idx) => (
                <tr key={idx}>
                  <td>{line.name}</td>
                  <td className="text-right">{line.quantity}</td>
                  <td className="text-right">{formatCurrency(line.unitPrice)}</td>
                  <td className="text-right">{formatCurrency(line.lineTotal)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>

          <div className="mt-4 space-y-1 text-right text-sm">
            <p className="text-muted">Sous-total : {formatCurrency(offlineReceipt.subtotal)}</p>
            {offlineReceipt.discountAmount > 0 && (
              <p className="text-muted">
                Remise ({offlineReceipt.discountRate}%) : -{formatCurrency(offlineReceipt.discountAmount)}
              </p>
            )}
            <p className="text-lg font-semibold text-primary-dark">
              Total : {formatCurrency(offlineReceipt.total)}
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Recherche et selection de produits */}
        <div className="card lg:col-span-2">
          <h2 className="card-title">Produits</h2>

          <div className="relative mb-4">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
            <input
              type="text"
              className="input pl-9"
              placeholder="Rechercher par nom, SKU ou code-barres"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
          </div>

          {isOnline && productsQuery.isLoading && (
            <div className="flex items-center gap-2 text-muted">
              <Loader2 className="h-4 w-4 animate-spin" />
              Chargement...
            </div>
          )}

          {isOnline && productsQuery.isError && (
            <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
              {getApiErrorMessage(productsQuery.error, "Impossible de charger les produits.")}
            </div>
          )}

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {displayProducts.map((product) => {
              const offlineStock = stockById.get(product.id);
              return (
                <button
                  key={product.id}
                  type="button"
                  onClick={() => addToCart(product)}
                  className="flex items-center justify-between rounded-lg border border-surface px-4 py-3 text-left transition hover:border-primary hover:bg-primary/5"
                >
                  <div>
                    <p className="font-medium text-primary-dark">{product.name}</p>
                    {product.name_moore && (
                      <p className="text-xs text-muted">{product.name_moore}</p>
                    )}
                    <p className="text-xs text-muted">{product.sku}</p>
                    {!isOnline && offlineStock !== undefined && (
                      <p className="text-xs text-amber-600">Stock (cache) : {offlineStock}</p>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-primary">{formatCurrency(unitPriceFor(product))}</p>
                    <p className="text-xs text-muted">/ {product.unit}</p>
                  </div>
                </button>
              );
            })}

            {isOnline && productsQuery.isSuccess && displayProducts.length === 0 && (
              <p className="col-span-full text-sm text-muted">Aucun produit trouve.</p>
            )}

            {!isOnline && displayProducts.length === 0 && (
              <p className="col-span-full text-sm text-muted">
                Aucun produit en cache local. Connectez-vous au réseau au moins une fois pour
                synchroniser le catalogue (§26.7).
              </p>
            )}
          </div>
        </div>

        {/* Panier et encaissement */}
        <div className="card flex flex-col gap-4">
          <h2 className="card-title flex items-center gap-2">
            <ShoppingCart className="h-4 w-4" />
            Panier
          </h2>

          {cart.length === 0 ? (
            <p className="text-sm text-muted">Aucun article ajoute pour le moment.</p>
          ) : (
            <div className="space-y-3">
              {cart.map((line) => (
                <div key={line.product.id} className="flex items-center justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-primary-dark">{line.product.name}</p>
                    <p className="text-xs text-muted">{formatCurrency(unitPriceFor(line.product))}</p>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      className="btn-ghost p-1"
                      onClick={() => updateQuantity(line.product.id, line.quantity - 1)}
                    >
                      <Minus className="h-3.5 w-3.5" />
                    </button>
                    <span className="w-8 text-center text-sm font-medium">{line.quantity}</span>
                    <button
                      type="button"
                      className="btn-ghost p-1"
                      onClick={() => updateQuantity(line.product.id, line.quantity + 1)}
                    >
                      <Plus className="h-3.5 w-3.5" />
                    </button>
                    <button
                      type="button"
                      className="btn-ghost p-1 text-red-600"
                      onClick={() => removeFromCart(line.product.id)}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="space-y-3 border-t border-surface pt-3">
            {!user?.branch_id && (
              <div>
                <label className="label">Site de vente</label>
                <select className="input" value={branchId} onChange={(e) => setBranchId(e.target.value)}>
                  <option value="">Selectionner un site</option>
                  {(branchesQuery.data ?? []).map((branch) => (
                    <option key={branch.id} value={branch.id}>
                      {branch.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div>
              <label className="label">Client</label>
              <select
                className="input"
                value={customerId}
                onChange={(e) => setCustomerId(e.target.value)}
                disabled={!isOnline}
              >
                <option value="">Client comptant (tarif grand public)</option>
                {(customersQuery.data ?? []).map((customer) => (
                  <option key={customer.id} value={customer.id}>
                    {customer.full_name}
                    {customer.customer_type === "TECHNICIEN" ? " (technicien)" : ""}
                  </option>
                ))}
              </select>
              {!isOnline && (
                <p className="mt-1 text-xs text-muted">
                  Sélection client indisponible hors-ligne — vente au tarif grand public (§26.10).
                </p>
              )}
              {selectedCustomer && Number(selectedCustomer.credit_limit) > 0 && (
                <p className="mt-1 text-xs text-muted">
                  Encours actuel : {formatCurrency(selectedCustomer.credit_balance)} / limite{" "}
                  {formatCurrency(selectedCustomer.credit_limit)}
                </p>
              )}
            </div>

            <div>
              <label className="label">Remise (%)</label>
              <input
                type="number"
                className="input"
                min={0}
                max={100}
                step={1}
                value={discountRate}
                onChange={(e) => setDiscountRate(Math.max(0, Math.min(100, Number(e.target.value))))}
              />
            </div>

            <div>
              <label className="label">Mode de paiement</label>
              <div className="flex gap-2">
                <button
                  type="button"
                  className={paymentType === "CASH" ? "btn-primary flex-1" : "btn-secondary flex-1"}
                  onClick={() => setPaymentType("CASH")}
                >
                  Comptant
                </button>
                <button
                  type="button"
                  className={paymentType === "CREDIT" ? "btn-primary flex-1" : "btn-secondary flex-1"}
                  onClick={() => setPaymentType("CREDIT")}
                  disabled={!isOnline}
                  title={!isOnline ? "Vente à crédit indisponible hors-ligne" : undefined}
                >
                  Credit
                </button>
              </div>
            </div>
          </div>

          <div className="space-y-1 border-t border-surface pt-3 text-sm">
            <div className="flex justify-between text-muted">
              <span>Sous-total</span>
              <span>{formatCurrency(subtotal)}</span>
            </div>
            {discountRate > 0 && (
              <div className="flex justify-between text-muted">
                <span>Remise ({discountRate}%)</span>
                <span>-{formatCurrency(discountAmount)}</span>
              </div>
            )}
            <div className="flex justify-between text-lg font-semibold text-primary-dark">
              <span>Total</span>
              <span>{formatCurrency(total)}</span>
            </div>
          </div>

          {submitError && (
            <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{submitError}</div>
          )}

          <button
            type="button"
            className="btn-primary w-full"
            disabled={createSaleMutation.isPending}
            onClick={handleSubmit}
          >
            {createSaleMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <ShoppingCart className="h-4 w-4" />
            )}
            {isOnline ? "Encaisser" : "Encaisser (hors-ligne)"}
          </button>
        </div>
      </div>
    </div>
  );
}
