/**
 * Tableau de bord comparatif inter-succursales — GesCom-BF (Feature C)
 *
 * Affiche côte à côte les KPIs de toutes les succursales :
 * - Cartes KPI par succursale (CA, ventes, panier, marge, clients actifs)
 * - RadarChart de performance normalisée 0-100
 * - BarChart / AreaChart d'évolution mensuelle du CA
 * - Filtres : date début / fin
 */
import { useState } from "react";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
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
  Store,
  Users,
  ShoppingBag,
  Percent,
  RefreshCw,
  AlertCircle,
} from "lucide-react";
import { useBranchesCompare } from "../hooks/useBranchesCompare";
import type { BranchKpi } from "@/types/branches";

// Palette de couleurs distinctives par succursale
const BRANCH_COLORS = ["#4f46e5", "#16a34a", "#ea580c", "#db2777", "#0891b2"];

function fmt(n: number) {
  return new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 }).format(n) + " FCFA";
}

function fmtPct(n: number) {
  return n.toFixed(1) + " %";
}

// ---------------------------------------------------------------------------
// Carte KPI d'une succursale
// ---------------------------------------------------------------------------
function BranchCard({ kpi, color }: { kpi: BranchKpi; color: string }) {
  return (
    <div className="rounded-xl border border-surface bg-white p-5 shadow-sm flex flex-col gap-4 min-w-0">
      {/* En-tête */}
      <div className="flex items-center gap-2">
        <div className="h-3 w-3 rounded-full" style={{ backgroundColor: color }} />
        <span className="font-semibold text-primary-dark truncate">{kpi.branch_name}</span>
        {kpi.is_depot && (
          <span className="ml-auto shrink-0 rounded-full bg-surface px-2 py-0.5 text-xs text-muted">
            Dépôt
          </span>
        )}
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-3">
        <Metric icon={TrendingUp} label="Chiffre d'affaires" value={fmt(kpi.ca)} color={color} />
        <Metric icon={ShoppingBag} label="Ventes" value={String(kpi.nb_ventes)} color={color} />
        <Metric
          icon={Store}
          label="Panier moyen"
          value={fmt(kpi.panier_moyen)}
          color={color}
        />
        <Metric icon={Percent} label="Marge brute" value={fmtPct(kpi.marge_pct)} color={color} />
        <Metric
          icon={Users}
          label="Clients actifs"
          value={String(kpi.nb_clients_actifs)}
          color={color}
        />
        <div className="col-span-2 rounded-lg bg-surface p-2">
          <p className="text-xs text-muted">Top produit</p>
          <p className="truncate text-sm font-medium text-primary-dark">
            {kpi.top_product || "—"}
          </p>
        </div>
      </div>
    </div>
  );
}

function Metric({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: typeof TrendingUp;
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div className="rounded-lg bg-surface p-2">
      <div className="flex items-center gap-1 text-muted">
        <Icon className="h-3 w-3 shrink-0" style={{ color }} />
        <span className="truncate text-xs">{label}</span>
      </div>
      <p className="mt-0.5 text-sm font-semibold text-primary-dark truncate">{value}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page principale
// ---------------------------------------------------------------------------
export default function BranchComparePage() {
  const today = new Date().toISOString().split("T")[0];
  const firstOfMonth = today.slice(0, 8) + "01";

  const [datDebut, setDatDebut] = useState(firstOfMonth);
  const [datFin, setDatFin] = useState(today);

  const { data, isLoading, isError, refetch } = useBranchesCompare({ datDebut, datFin });

  const branchNames = data?.branch_names ?? [];
  const kpis = data?.kpis ?? [];
  const radarData = data?.radar_data ?? [];
  const evolution = data?.evolution ?? [];

  return (
    <div className="space-y-6">
      {/* ── En-tête ─────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-primary-dark">Comparatif inter-succursales</h1>
          <p className="text-sm text-muted">Performance côte à côte de toutes les succursales</p>
        </div>
        <button
          type="button"
          onClick={() => refetch()}
          className="btn-ghost flex items-center gap-1.5 text-sm"
        >
          <RefreshCw className="h-4 w-4" />
          Actualiser
        </button>
      </div>

      {/* ── Filtres ──────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-end gap-4 rounded-xl border border-surface bg-white p-4 shadow-sm">
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-muted">Date début</label>
          <input
            type="date"
            value={datDebut}
            max={datFin}
            onChange={(e) => setDatDebut(e.target.value)}
            className="rounded-lg border border-surface bg-surface px-3 py-1.5 text-sm text-primary-dark"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-muted">Date fin</label>
          <input
            type="date"
            value={datFin}
            min={datDebut}
            max={today}
            onChange={(e) => setDatFin(e.target.value)}
            className="rounded-lg border border-surface bg-surface px-3 py-1.5 text-sm text-primary-dark"
          />
        </div>
      </div>

      {/* ── État ─────────────────────────────────────────────────────────── */}
      {isLoading && (
        <div className="flex h-40 items-center justify-center text-muted">
          Chargement des données...
        </div>
      )}
      {isError && (
        <div className="flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-red-700">
          <AlertCircle className="h-4 w-4 shrink-0" />
          Erreur lors du chargement. Vérifiez la connexion et réessayez.
        </div>
      )}

      {data && (
        <>
          {/* ── Cartes KPI côte à côte ──────────────────────────────────── */}
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {kpis.map((kpi, i) => (
              <BranchCard
                key={kpi.branch_id}
                kpi={kpi}
                color={BRANCH_COLORS[i % BRANCH_COLORS.length]}
              />
            ))}
          </div>

          {/* ── Graphiques ─────────────────────────────────────────────── */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* RadarChart de performance */}
            <div className="rounded-xl border border-surface bg-white p-5 shadow-sm">
              <h2 className="mb-4 text-sm font-semibold text-primary-dark">
                Radar de performance (score 0-100)
              </h2>
              {radarData.length > 0 ? (
                <ResponsiveContainer width="100%" height={320}>
                  <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="75%">
                    <PolarGrid stroke="#e5e7eb" />
                    <PolarAngleAxis
                      dataKey="metric"
                      tick={{ fontSize: 11, fill: "#6b7280" }}
                    />
                    <PolarRadiusAxis
                      angle={90}
                      domain={[0, 100]}
                      tick={{ fontSize: 9, fill: "#9ca3af" }}
                    />
                    {branchNames.map((name, i) => (
                      <Radar
                        key={name}
                        name={name}
                        dataKey={name}
                        stroke={BRANCH_COLORS[i % BRANCH_COLORS.length]}
                        fill={BRANCH_COLORS[i % BRANCH_COLORS.length]}
                        fillOpacity={0.15}
                        strokeWidth={2}
                      />
                    ))}
                    <Legend
                      iconType="circle"
                      iconSize={8}
                      wrapperStyle={{ fontSize: 12 }}
                    />
                    <Tooltip
                      formatter={(v) => [`${v as number}`, ""]}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              ) : (
                <p className="py-10 text-center text-sm text-muted">Aucune donnée</p>
              )}
            </div>

            {/* BarChart CA par succursale */}
            <div className="rounded-xl border border-surface bg-white p-5 shadow-sm">
              <h2 className="mb-4 text-sm font-semibold text-primary-dark">
                Chiffre d'affaires par succursale
              </h2>
              {kpis.length > 0 ? (
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart
                    data={kpis.map((k) => ({
                      name: k.branch_name,
                      CA: k.ca,
                      Marge: k.marge_brute,
                    }))}
                    margin={{ top: 10, right: 20, left: 0, bottom: 10 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                    <YAxis
                      tick={{ fontSize: 10 }}
                      tickFormatter={(v) =>
                        new Intl.NumberFormat("fr-FR", { notation: "compact" }).format(v as number)
                      }
                    />
                    <Tooltip
                      formatter={(v, name) => [fmt(v as number), String(name)]}
                    />
                    <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="CA" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Marge" fill="#16a34a" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <p className="py-10 text-center text-sm text-muted">Aucune donnée</p>
              )}
            </div>
          </div>

          {/* ── Évolution mensuelle ─────────────────────────────────────── */}
          {evolution.length > 0 && (
            <div className="rounded-xl border border-surface bg-white p-5 shadow-sm">
              <h2 className="mb-4 text-sm font-semibold text-primary-dark">
                Évolution mensuelle du CA par succursale
              </h2>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart
                  data={evolution}
                  margin={{ top: 10, right: 20, left: 0, bottom: 10 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                  <XAxis dataKey="mois" tick={{ fontSize: 11 }} />
                  <YAxis
                    tick={{ fontSize: 10 }}
                    tickFormatter={(v) =>
                      new Intl.NumberFormat("fr-FR", { notation: "compact" }).format(v as number)
                    }
                  />
                  <Tooltip
                    formatter={(v, name) => [fmt(v as number), String(name)]}
                    labelFormatter={(label) => `Mois : ${String(label)}`}
                  />
                  <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12 }} />
                  {branchNames.map((name, i) => (
                    <Bar
                      key={name}
                      dataKey={name}
                      fill={BRANCH_COLORS[i % BRANCH_COLORS.length]}
                      radius={[3, 3, 0, 0]}
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* ── Tableau récapitulatif ───────────────────────────────────── */}
          <div className="overflow-x-auto rounded-xl border border-surface bg-white shadow-sm">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface bg-surface/50">
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted">
                    Succursale
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted">
                    CA
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted">
                    Ventes
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted">
                    Panier moy.
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted">
                    Marge brute
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted">
                    Marge %
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted">
                    Clients
                  </th>
                </tr>
              </thead>
              <tbody>
                {kpis.map((kpi, i) => (
                  <tr key={kpi.branch_id} className="border-b border-surface last:border-0 hover:bg-surface/30">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div
                          className="h-2 w-2 rounded-full shrink-0"
                          style={{ backgroundColor: BRANCH_COLORS[i % BRANCH_COLORS.length] }}
                        />
                        <span className="font-medium text-primary-dark">{kpi.branch_name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right text-primary-dark">{fmt(kpi.ca)}</td>
                    <td className="px-4 py-3 text-right text-primary-dark">{kpi.nb_ventes}</td>
                    <td className="px-4 py-3 text-right text-primary-dark">
                      {fmt(kpi.panier_moyen)}
                    </td>
                    <td className="px-4 py-3 text-right text-primary-dark">
                      {fmt(kpi.marge_brute)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span
                        className={
                          kpi.marge_pct >= 20
                            ? "text-green-600 font-medium"
                            : kpi.marge_pct >= 10
                            ? "text-amber-600"
                            : "text-red-600"
                        }
                      >
                        {fmtPct(kpi.marge_pct)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right text-primary-dark">
                      {kpi.nb_clients_actifs}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
