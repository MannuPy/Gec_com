/**
 * Module comptabilité simplifié — GesCom-BF (RF-COMPTA-01)
 *
 * Bilan recettes / dépenses par succursale et période :
 * - KPI cards : recettes, dépenses, balance
 * - Graphique évolution journalière (BarChart empilé)
 * - Journal de caisse chronologique avec solde cumulatif
 * - Filtres : succursale, date début / fin
 */
import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  TrendingUp,
  TrendingDown,
  Scale,
  RefreshCw,
  AlertCircle,
  ArrowUpCircle,
  ArrowDownCircle,
} from "lucide-react";
import { useComptaSummary } from "../hooks/useComptaSummary";
import type { ComptaJournalEntry } from "@/types/compta";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmt(v: number): string {
  return v.toLocaleString("fr-FR") + " FCFA";
}

function fmtDate(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return (
    d.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit", year: "2-digit" }) +
    " " +
    d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })
  );
}

function today(): string {
  return new Date().toISOString().split("T")[0];
}

function firstDayOfMonth(): string {
  const d = new Date();
  return new Date(d.getFullYear(), d.getMonth(), 1).toISOString().split("T")[0];
}

// ---------------------------------------------------------------------------
// Sous-composants
// ---------------------------------------------------------------------------

interface KpiCardProps {
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ReactNode;
  colorClass: string;
}

function KpiCard({ title, value, subtitle, icon, colorClass }: KpiCardProps) {
  return (
    <div className="rounded-xl border border-surface bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium uppercase tracking-wide text-muted">{title}</p>
          <p className={"mt-1 truncate text-xl font-bold " + colorClass}>{value}</p>
          {subtitle && <p className="mt-0.5 text-xs text-muted">{subtitle}</p>}
        </div>
        <div className={"shrink-0 rounded-lg p-2 " + colorClass.replace("text-", "bg-").replace("600", "50")}>
          {icon}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page principale
// ---------------------------------------------------------------------------

export default function ComptaPage() {
  const [branchId, setBranchId] = useState("");
  const [datDebut, setDatDebut] = useState(firstDayOfMonth());
  const [datFin, setDatFin] = useState(today());

  const { data, isLoading, isError, refetch, isFetching } = useComptaSummary({
    branchId: branchId || undefined,
    datDebut,
    datFin,
  });

  // ---- Chargement ----
  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center text-muted">
        <RefreshCw className="mr-2 h-5 w-5 animate-spin" />
        Chargement du bilan comptable…
      </div>
    );
  }

  // ---- Erreur ----
  if (isError || !data) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3 text-muted">
        <AlertCircle className="h-8 w-8 text-red-400" />
        <p>Impossible de charger les données.</p>
        <button
          type="button"
          className="btn-primary px-4 py-2 text-sm"
          onClick={() => void refetch()}
        >
          Réessayer
        </button>
      </div>
    );
  }

  const { recettes, depenses, balance, evolution_journaliere, journal, branches, periode } = data;
  const balancePositive = balance >= 0;

  return (
    <div className="space-y-6">
      {/* ---- En-tête ---- */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-primary-dark">Comptabilité simplifiée</h1>
          <p className="mt-1 text-sm text-muted">
            Période : {new Date(periode.debut).toLocaleDateString("fr-FR")} →{" "}
            {new Date(periode.fin).toLocaleDateString("fr-FR")}
          </p>
        </div>
        <button
          type="button"
          onClick={() => void refetch()}
          disabled={isFetching}
          className="btn-ghost flex items-center gap-1.5 px-3 py-2 text-sm"
        >
          <RefreshCw className={"h-4 w-4 " + (isFetching ? "animate-spin" : "")} />
          Actualiser
        </button>
      </div>

      {/* ---- Filtres ---- */}
      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-surface bg-white p-4 shadow-sm">
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-muted">Succursale</label>
          <select
            value={branchId}
            onChange={(e) => setBranchId(e.target.value)}
            className="input-field h-9 min-w-[180px] text-sm"
          >
            <option value="">Toutes les succursales</option>
            {branches.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-muted">Du</label>
          <input
            type="date"
            value={datDebut}
            onChange={(e) => setDatDebut(e.target.value)}
            className="input-field h-9 text-sm"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-muted">Au</label>
          <input
            type="date"
            value={datFin}
            onChange={(e) => setDatFin(e.target.value)}
            className="input-field h-9 text-sm"
          />
        </div>
      </div>

      {/* ---- KPI Cards ---- */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <KpiCard
          title="Recettes"
          value={fmt(recettes.total)}
          subtitle={recettes.nb_ventes + " ventes (cash : " + fmt(recettes.cash) + ")"}
          icon={<TrendingUp className="h-5 w-5" />}
          colorClass="text-green-600"
        />
        <KpiCard
          title="Dépenses"
          value={fmt(depenses.total)}
          subtitle={depenses.nb_receptions + " réception(s) fournisseur"}
          icon={<TrendingDown className="h-5 w-5" />}
          colorClass="text-red-600"
        />
        <KpiCard
          title="Balance (bénéfice brut)"
          value={fmt(balance)}
          subtitle={balancePositive ? "Excédent" : "Déficit"}
          icon={<Scale className="h-5 w-5" />}
          colorClass={balancePositive ? "text-blue-600" : "text-amber-600"}
        />
      </div>

      {/* ---- Graphique évolution journalière ---- */}
      {evolution_journaliere.length > 0 && (
        <div className="rounded-xl border border-surface bg-white p-4 shadow-sm">
          <h2 className="mb-4 text-sm font-semibold text-primary-dark">
            Évolution journalière — Recettes vs Dépenses
          </h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart
              data={evolution_journaliere}
              margin={{ top: 5, right: 10, left: 0, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 10 }}
                tickFormatter={(v: string) => {
                  const d = new Date(v);
                  return d.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit" });
                }}
              />
              <YAxis
                tick={{ fontSize: 10 }}
                tickFormatter={(v: number) => (v >= 1000 ? Math.round(v / 1000) + "k" : String(v))}
                width={45}
              />
              <Tooltip
                formatter={(v, name) => [fmt(v as number), String(name)]}
                labelFormatter={(label) =>
                  new Date(String(label)).toLocaleDateString("fr-FR", {
                    weekday: "short",
                    day: "2-digit",
                    month: "short",
                  })
                }
              />
              <Legend />
              <Bar dataKey="recettes" name="Recettes" fill="#16a34a" radius={[3, 3, 0, 0]} />
              <Bar dataKey="depenses" name="Dépenses" fill="#dc2626" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* ---- Journal de caisse ---- */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">
          Journal de caisse ({journal.length} opérations)
        </h2>
        {journal.length === 0 ? (
          <p className="rounded-xl border border-surface bg-white p-6 text-center text-sm text-muted">
            Aucune opération sur la période sélectionnée.
          </p>
        ) : (
          <div className="overflow-hidden rounded-xl border border-surface bg-white shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-primary-dark text-white">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium">Date</th>
                    <th className="px-4 py-3 text-left font-medium">Type</th>
                    <th className="px-4 py-3 text-left font-medium">Référence</th>
                    <th className="px-4 py-3 text-left font-medium">Libellé</th>
                    <th className="px-4 py-3 text-left font-medium">Succursale</th>
                    <th className="px-4 py-3 text-right font-medium">Montant</th>
                    <th className="px-4 py-3 text-right font-medium">Solde cumulé</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface">
                  {journal.map((entry: ComptaJournalEntry, i: number) => {
                    const isRecette = entry.type === "RECETTE";
                    return (
                      <tr key={i} className={i % 2 === 0 ? "bg-white" : "bg-gray-50/50"}>
                        <td className="whitespace-nowrap px-4 py-3 text-xs text-muted">
                          {fmtDate(entry.date)}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={
                              "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium " +
                              (isRecette
                                ? "bg-green-100 text-green-700"
                                : "bg-red-100 text-red-700")
                            }
                          >
                            {isRecette ? (
                              <ArrowUpCircle className="h-3 w-3" />
                            ) : (
                              <ArrowDownCircle className="h-3 w-3" />
                            )}
                            {isRecette ? "Recette" : "Dépense"}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-mono text-xs text-primary-dark">
                          {entry.reference}
                        </td>
                        <td className="max-w-[200px] truncate px-4 py-3 text-muted">
                          {entry.libelle}
                        </td>
                        <td className="px-4 py-3 text-xs text-muted">{entry.branch}</td>
                        <td
                          className={
                            "px-4 py-3 text-right font-semibold " +
                            (isRecette ? "text-green-600" : "text-red-600")
                          }
                        >
                          {isRecette ? "+" : "−"} {fmt(entry.montant)}
                        </td>
                        <td
                          className={
                            "px-4 py-3 text-right font-bold " +
                            (entry.solde_cumul >= 0 ? "text-primary-dark" : "text-amber-600")
                          }
                        >
                          {fmt(entry.solde_cumul)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
