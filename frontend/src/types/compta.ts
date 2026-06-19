/**
 * Types pour le module comptabilité simplifié (RF-COMPTA-01).
 */

export interface ComptaBranch {
  id: string;
  name: string;
}

export interface ComptaRecettes {
  total: number;
  cash: number;
  credit: number;
  nb_ventes: number;
}

export interface ComptaDepenses {
  total: number;
  nb_receptions: number;
}

export interface ComptaEvolutionJour {
  date: string; // YYYY-MM-DD
  recettes: number;
  depenses: number;
  balance_jour: number;
}

export interface ComptaJournalEntry {
  date: string | null; // ISO datetime
  type: "RECETTE" | "DEPENSE";
  reference: string;
  libelle: string;
  montant: number;
  branch: string;
  solde_cumul: number;
}

export interface ComptaSummary {
  periode: {
    debut: string; // YYYY-MM-DD
    fin: string;   // YYYY-MM-DD
  };
  branches: ComptaBranch[];
  recettes: ComptaRecettes;
  depenses: ComptaDepenses;
  balance: number;
  evolution_journaliere: ComptaEvolutionJour[];
  journal: ComptaJournalEntry[];
}
