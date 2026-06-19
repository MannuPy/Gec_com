/**
 * Types pour le tableau de bord vendeur individuel.
 * Cf. backend/app/blueprints/reports/routes.py (vendeur_dashboard).
 */

export interface VendeurCashier {
  id: string;
  full_name: string;
  branch_id: string | null;
  branch_name: string | null;
}

export interface VendeurKpisJour {
  ca_jour: string;
  nb_ventes: number;
  panier_moyen: string;
}

export interface VendeurKpisMois {
  ca_mois: string;
  nb_ventes: number;
  commission_estimee: string;
  objectif_mensuel: string;
  progression_pct: number;
  commission_rate_pct: number;
}

export interface VendeurHeure {
  heure: number;
  ca: number;
}

export interface VendeurTopProduit {
  product_id: string;
  name: string;
  sku: string;
  qte_vendue: number;
  ca: string;
}

export interface VendeurDerniereVente {
  id: string;
  reference: string;
  created_at: string | null;
  total: string;
  payment_type: string;
  customer_name: string | null;
  nb_lignes: number;
}

export interface VendeurDashboard {
  cashier: VendeurCashier;
  kpis_jour: VendeurKpisJour;
  kpis_mois: VendeurKpisMois;
  historique_jour: VendeurHeure[];
  top_produits_mois: VendeurTopProduit[];
  dernieres_ventes: VendeurDerniereVente[];
}
