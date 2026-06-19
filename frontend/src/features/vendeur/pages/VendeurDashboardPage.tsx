/**
 * Tableau de bord vendeur — GesCom-BF
 *
 * Performance individuelle du vendeur connecté :
 * - KPIs du jour (CA, nb ventes, panier moyen)
 * - KPIs du mois + objectif + commission estimée
 * - Historique des ventes du jour par heure (AreaChart)
 * - Top 5 produits du mois (BarChart)
 * - Dernières 10 ventes (tableau)
 */
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";
import {
  ShoppingCart,
  TrendingUp,
  Wallet,
  Target,
  Award,
  RefreshCw,
  AlertCircle,
  User,
  Store,
} from "lucide-react";
import { useVendeurDashboard } from "../hooks/useVendeurDashboard";
import type { VendeurDerniereVente, VendeurTopProduit } from "@/types/vendeur";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmt(v: string | number): string {
  const n = typeof v === "string" ? parseFloat(v) : v;
  if (isNaN(n)) return "0 FCFA";
  return n.toLocaleString("fr-FR") + " FCFA";
}

function fmtHeure(h: number): string {
  return `${String(h).padStart(2, "0")}h`;
}

function fmtDate(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit", year: "2-digit" })
    + " " + d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

const PAYMENT_LABELS: Record<string, string> = {
  CASH: "Espèces",
  CREDIT: "Crédit",
  MOBILE_MONEY: "Mobile Money",
};

// ---------------------------------------------------------------------------
// Sous-composants
// ---------------------------------------------------------------------------

interface KpiCardProps {
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ReactNode;
  accent?: "blue" | "green" | "amber" | "purple";
}

function KpiCard({ title, value, subtitle, icon, accent = "blue" }: KpiCardProps) {
  const accentClasses: Record<string, string> = {
    blue: "text-blue-600 bg-blue-50",
    green: "text-green-600 bg-green-50",
    amber: "text-amber-600 bg-amber-50",
    purple: "text-purple-600 bg-purple-50",
  };
  return (
    <div className="rounded-xl border border-surface bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium uppercase tracking-wide text-muted">{title}</p>
          <p className="mt-1 truncate text-xl font-bold text-primary-dark">{value}</p>
          {subtitle && <p className="mt-0.5 text-xs text-muted">{subtitle}</p>}
        </div>
        <div className={"shrink-0 rounded-lg p-2 " + accentClasses[accent]}>{icon}</div>
      </div>
    </div>
  );
}

interface ProgressBarProps {
  pct: number;
  label: string;
}

function ProgressBar({ pct, label }: ProgressBarProps) {
  const clamped = Math.min(pct, 100);
  const color = pct >= 100 ? "bg-green-500" : pct >= 70 ? "bg-amber-400" : "bg-blue-500";
  return (
    <div className="mt-3">
      <div className="mb-1 flex justify-between text-xs text-muted">
        <span>{label}</span>
        <span className="font-semibold text-primary-dark">{pct.toFixed(1)} %</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-surface">
        <div
          className={"h-2 rounded-full transition-all duration-700 " + color}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page principale
// ---------------------------------------------------------------------------

export default function VendeurDashboardPage() {
  const { data, isLoading, isError, refetch, isFetching } = useVendeurDashboard();

  // ---- États de chargement / erreur ----
  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center text-muted">
        <RefreshCw className="mr-2 h-5 w-5 animate-spin" />
        Chargement de votre tableau de bord…
      </div>
    );
  }

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

  const { cashier, kpis_jour, kpis_mois, historique_jour, top_produits_mois, dernieres_ventes } = data;

  // Filtre historique : heures non nulles (+ context des heures ouvertes)
  const historique = historique_jour.filter((h) => h.heure >= 6 && h.heure <= 22);

  return (
    <div className="space-y-6">
      {/* ---- En-tête ---- */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-primary-dark">Mon tableau de bord</h1>
          <div className="mt-1 flex flex-wrap items-center gap-3 text-sm text-muted">
            <span className="flex items-center gap-1">
              <User className="h-4 w-4" />
              {cashier.full_name}
            </span>
            {cashier.branch_name && (
              <span className="flex items-center gap-1">
                <Store className="h-4 w-4" />
                {cashier.branch_name}
              </span>
            )}
          </div>
        </div>
        <button
          type="button"
          onClick={() => void refetch()}
          disabled={isFetching}
          className="btn-ghost flex items-center gap-1.5 px-3 py-2 text-sm"
          title="Actualiser"
        >
          <RefreshCw className={"h-4 w-4 " + (isFetching ? "animate-spin" : "")} />
          Actualiser
        </button>
      </div>

      {/* ---- KPIs du jour ---- */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">
          Aujourd'hui
        </h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <KpiCard
            title="CA du jour"
            value={fmt(kpis_jour.ca_jour)}
            icon={<TrendingUp className="h-5 w-5" />}
            accent="blue"
          />
          <KpiCard
            title="Ventes"
            value={String(kpis_jour.nb_ventes)}
            subtitle="transactions validées"
            icon={<ShoppingCart className="h-5 w-5" />}
            accent="green"
          />
          <KpiCard
            title="Panier moyen"
            value={fmt(kpis_jour.panier_moyen)}
            icon={<Wallet className="h-5 w-5" />}
            accent="amber"
            />
        </div>
      </section>

      {/* ---- KPIs du mois + objectif ---- */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">
          Ce mois-ci
        </h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <KpiCard
            title="CA du mois"
            value={fmt(kpis_mois.ca_mois)}
            subtitle={kpis_mois.nb_ventes + " ventes"}
            icon={<TrendingUp className="h-5 w-5" />}
            accent="blue"
          />
          <KpiCard
            title="Objectif mensuel"
            value={fmt(kpis_mois.objectif_mensuel)}
            icon={<Target className="h-5 w-5" />}
            accent="purple"
          />
          <div className="col-span-1 rounded-xl border border-surface bg-white p-4 shadow-sm sm:col-span-2">
            <p className="text-xs font-medium uppercase tracking-wide text-muted">
              Commission estimée ({kpis_mois.commission_rate_pct} %)
            </p>
            <p className="mt-1 text-xl font-bold text-green-600">
              {fmt(kpis_mois.commission_estimee)}
            </p>
            <ProgressBar
              pct={kpis_mois.progression_pct}
              label={"Progression vers l'objectif"}
            />
            <div className="mt-2 flex items-center gap-1">
              <Award className="h-4 w-4 text-amber-500" />
              <span className="text-xs text-muted">
                {kpis_mois.progression_pct >= 100
                  ? "Objectif atteint !"
                  : fmt(
                      Math.max(
                        0,
                        parseFloat(kpis_mois.objectif_mensuel) - parseFloat(kpis_mois.ca_mois),
                      ),
                    ) + " restant pour atteindre l'objectif"}
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* ---- Graphiques ---- */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Historique du jour par heure */}
        <div className="rounded-xl border border-surface bg-white p-4 shadow-sm">
          <h2 className="mb-4 text-sm font-semibold text-primary-dark">
            Ventes du jour par heure
          </h2>
          {historique.every((h) => h.ca === 0) ? (
            <p className="flex h-40 items-center justify-center text-sm text-muted">
              Aucune vente enregistrée aujourd'hui.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={historique} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="vendeurGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0439D9" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#0439D9" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="heure"
                  tickFormatter={fmtHeure}
                  tick={{ fontSize: 11 }}
                  interval={2}
                />
                <YAxis
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v) => (v >= 1000 ? Math.round(v / 1000) + "k" : String(v))}
                  width={40}
                />
                <Tooltip
                  formatter={(v) => [fmt(v as number), "CA"]}
                  labelFormatter={(label) => fmtHeure(label as number)}
                />
                <Area
                  type="monotone"
                  dataKey="ca"
                  stroke="#0439D9"
                  strokeWidth={2}
                  fill="url(#vendeurGradient)"
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Top produits du mois */}
        <div className="rounded-xl border border-surface bg-white p-4 shadow-sm">
          <h2 className="mb-4 text-sm font-semibold text-primary-dark">
            Top 5 produits (ce mois)
          </h2>
          {top_produits_mois.length === 0 ? (
            <p className="flex h-40 items-center justify-center text-sm text-muted">
              Aucune vente ce mois-ci.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart
                data={top_produits_mois}
                layout="vertical"
                margin={{ top: 0, right: 10, left: 0, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={false} />
                <XAxis
                  type="number"
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v) => (v >= 1000 ? Math.round(v / 1000) + "k" : String(v))}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={90}
                  tick={{ fontSize: 10 }}
                  tickFormatter={(v: string) => (v.length > 14 ? v.slice(0, 13) + "…" : v)}
                />
                <Tooltip
                  formatter={(_v, _name, p) => [
                    p.payload.qte_vendue + " unités — " + fmt(p.payload.ca),
                    p.payload.name,
                  ]}
                />
                <Bar
                  dataKey="qte_vendue"
                  fill="#0439D9"
                  radius={[0, 4, 4, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* ---- Dernières ventes ---- */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">
          Dernières ventes
        </h2>
        {dernieres_ventes.length === 0 ? (
          <p className="rounded-xl border border-surface bg-white p-6 text-center text-sm text-muted">
            Aucune vente enregistrée pour l'instant.
          </p>
        ) : (
          <div className="overflow-hidden rounded-xl border border-surface bg-white shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-primary-dark text-white">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium">Référence</th>
                    <th className="px-4 py-3 text-left font-medium">Date</th>
                    <th className="px-4 py-3 text-left font-medium">Client</th>
                    <th className="px-4 py-3 text-left font-medium">Paiement</th>
                    <th className="px-4 py-3 text-right font-medium">Articles</th>
                    <th className="px-4 py-3 text-right font-medium">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface">
                  {dernieres_ventes.map((vente: VendeurDerniereVente, i: number) => (
                    <tr
                      key={vente.id}
                      className={i % 2 === 0 ? "bg-white" : "bg-gray-50/50"}
                    >
                      <td className="px-4 py-3 font-mono text-xs text-primary-dark">
                        {vente.reference}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-muted">
                        {fmtDate(vente.created_at)}
                      </td>
                      <td className="px-4 py-3 text-muted">
                        {vente.customer_name ?? <span className="italic">Comptoir</span>}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={
                            "inline-flex rounded-full px-2 py-0.5 text-xs font-medium " +
                            (vente.payment_type === "CREDIT"
                              ? "bg-amber-100 text-amber-700"
                              : "bg-green-100 text-green-700")
                          }
                        >
                          {PAYMENT_LABELS[vente.payment_type] ?? vente.payment_type}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right text-muted">
                        {vente.nb_lignes}
                      </td>
                      <td className="px-4 py-3 text-right font-semibold text-primary-dark">
                        {fmt(vente.total)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
