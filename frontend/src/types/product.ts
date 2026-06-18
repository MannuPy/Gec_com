/** Cf. backend/app/blueprints/products/schemas.py */

export const PRODUCT_UNITS = ["UNITE", "BOITE", "SAC", "LITRE", "METRE", "KG"] as const;
export type ProductUnit = (typeof PRODUCT_UNITS)[number];

export interface Branch {
  id: string;
  name: string;
  code: string;
  is_depot: boolean;
  address: string | null;
  phone: string | null;
  is_active: boolean;
}

export interface Category {
  id: string;
  name: string;
  description: string | null;
}

export interface CategoryWritePayload {
  name: string;
  description?: string | null;
}

export interface Brand {
  id: string;
  name: string;
}

export interface BrandWritePayload {
  name: string;
}

export interface Product {
  id: string;
  sku: string;
  barcode: string | null;
  name: string;
  /** Désignation en mooré (RF-09), affichage bilingue du libellé produit. */
  name_moore: string | null;
  description: string | null;
  category_id: string | null;
  category_name: string | null;
  brand_id: string | null;
  brand_name: string | null;
  unit: ProductUnit;
  simple_price: string;
  technician_price: string;
  purchase_price: string;
  min_stock_threshold: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductCreatePayload {
  sku: string;
  barcode?: string | null;
  name: string;
  name_moore?: string | null;
  description?: string | null;
  category_id?: string | null;
  brand_id?: string | null;
  unit?: ProductUnit;
  simple_price: string;
  technician_price: string;
  purchase_price?: string;
  min_stock_threshold?: number;
}

export interface ProductUpdatePayload {
  barcode?: string | null;
  name?: string;
  name_moore?: string | null;
  description?: string | null;
  category_id?: string | null;
  brand_id?: string | null;
  unit?: ProductUnit;
  simple_price?: string;
  technician_price?: string;
  purchase_price?: string;
  min_stock_threshold?: number;
  is_active?: boolean;
}

export interface ProductListParams {
  search?: string;
  category_id?: string;
  brand_id?: string;
  is_active?: boolean;
  page?: number;
  per_page?: number;
  /** Synchronisation incrémentale du catalogue hors-ligne (cf. 26-GESTION-OFFLINE-PWA.md §26.7). */
  updated_since?: string;
}
