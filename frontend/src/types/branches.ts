/** Types pour le comparatif inter-succursales (Feature C) */

export interface BranchKpi {
  branch_id: string;
  branch_name: string;
  is_depot: boolean;
  ca: number;
  nb_ventes: number;
  panier_moyen: number;
  marge_brute: number;
  marge_pct: number;
  nb_clients_actifs: number;
  top_product: string;
}

/** Ligne du RadarChart : une métrique avec un score 0-100 par succursale */
export type RadarRow = { metric: string } & Record<string, number>;

/** Ligne d'évolution mensuelle : un mois avec le CA de chaque succursale */
export type EvolutionRow = { mois: string } & Record<string, number>;

export interface BranchesCompare {
  periode: { debut: string; fin: string };
  kpis: BranchKpi[];
  radar_data: RadarRow[];
  evolution: EvolutionRow[];
  branch_names: string[];
}
