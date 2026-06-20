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

      {/* ---- Historique des ventes du jour par heure ---- */}
      {historique.length > 0 && (
        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">
            Ventes par heure (aujourd'hui)
          </h2>
          <div className="rounded-xl border border-surface bg-white p-4 shadow-sm">
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={historique} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="caGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563EB" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#2563EB" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                <XAxis dataKey="heure" tickFormatter={(h) => fmtHeure(h as number)} tick={{ fontSize: 11 }} />
                <YAxis
                  tick={{ fontSize: 10 }}
                  tickFormatter={(v) => new Intl.NumberFormat("fr-FR", { notation: "compact" }).format(v as number)}
                />
                <Tooltip
                  labelFormatter={(label) => fmtHeure(label as number)}
                  formatter={(v) => [fmt(v as number), "CA"]}
                />
                <Area
                  type="monotone"
                  dataKey="ca"
                  stroke="#2563EB"
                  strokeWidth={2}
                  fill="url(#caGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}

      {/* ---- Top 5 produits du mois ---- */}
      {top_produits_mois.length > 0 && (
        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">
            Top 5 produits ce mois
          </h2>
          <div className="rounded-xl border border-surface bg-white p-4 shadow-sm">
            <ResponsiveContainer width="100%" height={180}>
              <BarChart
                data={top_produits_mois.slice(0, 5)}
                layout="vertical"
                margin={{ top: 0, right: 20, left: 60, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" horizontal={false} />
                <XAxis
                  type="number"
                  tick={{ fontSize: 10 }}
                  tickFormatter={(v) => new Intl.NumberFormat("fr-FR", { notation: "compact" }).format(v as number)}
                />
                <YAxis
                  type="category"
                  dataKey="product_name"
                  tick={{ fontSize: 10 }}
                  width={60}
                  tickFormatter={(v: string) => v.length > 10 ? v.slice(0, 9) + "…" : v}
                />
                <Tooltip
                  formatter={(_v, _name, p) => [
                    fmt((p.payload as VendeurTopProduit).ca as number),
                    "CA",
                  ]}
                />
                <Bar dataKey="ca" fill="#10B981" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}

      {/* ---- Dernières ventes ---- */}
      {dernieres_ventes.length > 0 && (
        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">
            Dernières ventes
          </h2>
          <div className="overflow-x-auto rounded-xl border border-surface bg-white shadow-sm">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface bg-surface/50">
                  <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted">
                    Date
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted">
                    Réf.
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted">
                    Client
                  </th>
                  <th className="px-3 py-2 text-right text-xs font-semibold uppercase tracking-wide text-muted">
                    Total
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted">
                    Paiement
                  </th>
                </tr>
              </thead>
              <tbody>
                {dernieres_ventes.map((v: VendeurDerniereVente) => (
                  <tr key={v.id} className="border-b border-surface last:border-0 hover:bg-surface/30">
                    <td className="whitespace-nowrap px-3 py-2 text-xs text-muted">
                      {fmtDate(v.created_at)}
                    </td>
                    <td className="px-3 py-2 font-mono text-xs text-primary-dark">{v.reference}</td>
                    <td className="px-3 py-2 text-xs text-primary-dark">
                      {v.customer_name || <span className="text-muted italic">—</span>}
                    </td>
                    <td className="px-3 py-2 text-right text-xs font-semibold text-primary-dark">
                      {fmt(v.total)}
                    </td>
                    <td className="px-3 py-2 text-xs text-muted">
                      {PAYMENT_LABELS[v.payment_type] ?? v.payment_type}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
