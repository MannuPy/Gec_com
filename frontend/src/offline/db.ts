/**
 * Base de données locale (IndexedDB via Dexie.js) pour le mode Offline-First.
 *
 * Cf. docs/26-GESTION-OFFLINE-PWA.md §26.4 — Modèle de données local.
 *
 * Deux tables principales :
 *  - `products` : snapshot du catalogue + stock, rafraîchi en ligne (§26.7) ;
 *  - `sales`    : ventes saisies hors-ligne, en attente de synchronisation
 *                 (`POST /sales/sync`, RG-28 à RG-30).
 */
import Dexie, { type Table } from "dexie";

// ---------------------------------------------------------------------------
// Catalogue produits (snapshot pour utilisation hors-ligne)
// ---------------------------------------------------------------------------

export interface CachedProduct {
  id: string;
  sku: string;
  barcode: string | null;
  name: string;
  /** Désignation en mooré (RF-09), affichage bilingue du libellé produit. */
  name_moore: string | null;
  category_name: string | null;
  unit: string;
  simple_price: number;
  technician_price: number;
  stock_quantity: number;
  min_stock_threshold: number;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Ventes saisies hors-ligne (§26.4 à §26.6)
// ---------------------------------------------------------------------------

export type OfflineSaleSyncStatus = "PENDING" | "SYNCING" | "SYNCED" | "CONFLICT";

export interface OfflineSaleLine {
  product_id: string;
  quantity: number;
  unit_price_applied: number;
}

export interface OfflineSale {
  offline_uuid: string; // généré côté client (UUID v4)
  branch_id: string;
  cashier_id: string;
  customer_id: string | null;
  payment_type: "CASH" | "CREDIT";
  discount_rate: number;
  lines: OfflineSaleLine[];
  created_at_local: string; // horodatage poste de caisse (ISO 8601)
  sync_status: OfflineSaleSyncStatus;
  // Renseigné après synchronisation (succès ou conflit)
  sync_message: string | null;
  server_sale_id: string | null;
}

// ---------------------------------------------------------------------------
// Base Dexie
// ---------------------------------------------------------------------------

export class GesComDB extends Dexie {
  products!: Table<CachedProduct, string>;
  sales!: Table<OfflineSale, string>;

  constructor() {
    super("gescom_bf_offline");
    this.version(1).stores({
      products: "id, sku, barcode, name, updated_at",
      sales: "offline_uuid, sync_status, created_at_local",
    });
    // v2 : suppression de la table discountRates (remises libres)
    this.version(2).stores({
      products: "id, sku, barcode, name, updated_at",
      sales: "offline_uuid, sync_status, created_at_local",
    });
  }
}

export const db = new GesComDB();
