/**
 * Synchronisation du catalogue (sens serveur -> client) pour le mode
 * Offline-First (cf. docs/26-GESTION-OFFLINE-PWA.md §26.7).
 *
 * - Catalogue produits + prix : synchronisation incrémentale via
 *   `GET /products?updated_since=...`.
 * - Stock de la boutique courante : `GET /stock?branch_id=...`.
 * - Taux de remise autorisés (RG-22) : `GET /sales/discounts/rates`.
 *
 * Le résultat est stocké dans IndexedDB (Dexie, cf. `offline/db.ts`) afin
 * d'être disponible pour la caisse (UC-11) lorsque le réseau est coupé.
 */
import { useEffect, useRef } from "react";

import { productsApi } from "@/api/endpoints/products";
import { salesApi } from "@/api/endpoints/sales";
import { stockApi } from "@/api/endpoints/stock";
import { db, type CachedProduct } from "@/offline/db";
import { useOnlineStatus } from "@/offline/useOnlineStatus";

const LAST_SYNC_KEY = "gescom_offline_catalog_synced_at";

// Garde-fou de pagination : 100 produits/page x 50 pages = 5000 produits par
// cycle de synchronisation. Au-delà (jusqu'à ~20 000, RNF-05), les pages
// suivantes seront récupérées lors du prochain cycle (incrémental).
const PAGE_SIZE = 100;
const MAX_PAGES_PER_SYNC = 50;

const PRODUCTS_REFRESH_INTERVAL_MS = 30 * 60 * 1000; // 30 min (§26.7)
const STOCK_REFRESH_INTERVAL_MS = 15 * 60 * 1000; // 15 min (§26.7)

/**
 * Récupère les pages de produits modifiés depuis la dernière synchronisation
 * et les place dans IndexedDB.
 */
async function syncProducts(): Promise<void> {
  const updatedSince = localStorage.getItem(LAST_SYNC_KEY) ?? undefined;
  const syncStartedAt = new Date().toISOString();

  let page = 1;
  let totalPages = 1;

  do {
    const result = await productsApi.list({
      page,
      per_page: PAGE_SIZE,
      updated_since: updatedSince,
    });

    const cached: CachedProduct[] = result.data.map((product) => ({
      id: product.id,
      sku: product.sku,
      barcode: product.barcode,
      name: product.name,
      name_moore: product.name_moore,
      category_name: product.category_name,
      unit: product.unit,
      simple_price: Number(product.simple_price),
      technician_price: Number(product.technician_price),
      stock_quantity: 0,
      min_stock_threshold: product.min_stock_threshold,
      updated_at: product.updated_at,
    }));

    if (cached.length > 0) {
      // On préserve le stock déjà connu pour les produits déjà en cache.
      const existing = await db.products.bulkGet(cached.map((p) => p.id));
      const merged = cached.map((p, idx) => ({
        ...p,
        stock_quantity: existing[idx]?.stock_quantity ?? 0,
      }));
      await db.products.bulkPut(merged);
    }

    totalPages = Math.max(1, Math.ceil(result.meta.total / result.meta.per_page));
    page += 1;
  } while (page <= totalPages && page <= MAX_PAGES_PER_SYNC);

  localStorage.setItem(LAST_SYNC_KEY, syncStartedAt);
}

/**
 * Met à jour les quantités en stock de la boutique courante dans le cache
 * produits (snapshot, cf. §26.7 — peut diverger du stock réel en cas de
 * ventes concurrentes hors-ligne, d'où la résolution de conflits §26.6).
 */
async function syncStock(branchId: string): Promise<void> {
  const stockItems = await stockApi.list({ branch_id: branchId });

  await db.transaction("rw", db.products, async () => {
    for (const item of stockItems) {
      const existing = await db.products.get(item.product_id);
      if (existing) {
        await db.products.update(item.product_id, {
          stock_quantity: item.quantity,
          min_stock_threshold: item.min_stock_threshold,
        });
      }
    }
  });
}

/** Met en cache les taux de remise autorisés (RG-22) et le seuil d'approbation (RG-23). */
async function syncDiscountRates(): Promise<void> {
  const rates = await salesApi.discountRates();

  await db.discountRates.clear();
  await db.discountRates.bulkAdd(
    rates.allowed_rates.map((rate) => ({
      id: `rate-${rate}`,
      rate,
      requires_approval: rate >= rates.approval_threshold,
    }))
  );
}

/**
 * Lance un cycle complet de synchronisation du catalogue. Ne fait rien si le
 * navigateur est hors-ligne. Les erreurs sont avalées : la synchronisation
 * sera retentée au prochain cycle / retour réseau.
 */
export async function refreshCatalogCache(branchId?: string | null): Promise<void> {
  if (typeof navigator !== "undefined" && !navigator.onLine) return;

  try {
    await syncProducts();
  } catch {
    // Réessai au prochain cycle.
  }

  if (branchId) {
    try {
      await syncStock(branchId);
    } catch {
      // Réessai au prochain cycle.
    }
  }

  try {
    await syncDiscountRates();
  } catch {
    // Réessai au prochain cycle.
  }
}

/**
 * Hook déclenchant la synchronisation du catalogue : au montage (si en
 * ligne), au retour de connexion, puis à intervalle régulier (§26.7).
 */
export function useCatalogSync(branchId?: string | null): void {
  const isOnline = useOnlineStatus();
  const lastBranchRef = useRef<string | null | undefined>(undefined);

  useEffect(() => {
    if (!isOnline) return;

    void refreshCatalogCache(branchId);
    lastBranchRef.current = branchId;

    const productsInterval = setInterval(() => {
      void refreshCatalogCache(branchId);
    }, PRODUCTS_REFRESH_INTERVAL_MS);

    const stockInterval = branchId
      ? setInterval(() => {
          void refreshCatalogCache(branchId);
        }, STOCK_REFRESH_INTERVAL_MS)
      : null;

    return () => {
      clearInterval(productsInterval);
      if (stockInterval) clearInterval(stockInterval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOnline, branchId]);
}
