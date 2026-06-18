import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  Banknote,
  Receipt,
  ShieldAlert,
  TrendingUp,
  Loader2,
  Wifi,
  WifiOff,
  BadgeAlert,
  PackageX,
  Sparkles,
  Users,
} from "lucide-react";

import { reportsApi } from "@/api/endpoints/reports";
import { salesApi } from "@/api/endpoints/sales";
import { getApiErrorMessage } from "@/api/client";
import { useAuthStore } from "@/app/store";
import { useDashboardStream } from "@/features/dashboard/hooks/useDashboardStream";
import type { DashboardAlert, DashboardAlertSeverity } from "@/types/dashboard";
import { formatCurrency, formatDateTime, formatNumber } from "@/utils/format";

/**
 * Tableau de bord : indicateurs du jour (RF-23).
 * Cf. GET /api/v1/reports/dashboard.
 */
export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const hasPermission = useAuthStore((s) => s.hasPermission);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["dashboard", user?.branch_id],
    queryFn: () => reportsApi.dashboard(user?.branch_id),
  });

  // Tableau de bord temps reel : KPIs + alertes IA (rupture de stock,
  // anomalies, clients a risque) + ABC/XYZ + segments RFM.
  // Cf. doc 22-DASHBOARD-BI.md §22.2/§22.5 (SSE/polling).
  const realtime = useDashboardStream(user?.branch_id);

  // Ventes hors-ligne synchronisées nécessitant une régularisation admin
  // (conflits de stock RG-29, remises en attente d'approbation RG-23).
  // Cf. docs/26-GESTION-OFFLINE-PWA.md §26.6/§26.8.
  const canReviewSyncIssues = hasPermission("sales:approve_discount");

  const conflictsQuery = useQuery({
    queryKey: ["sales", "conflicts"],
    queryFn: () => salesApi.list({ status: "EN_CONFLIT", per_page: 5 }),
    enabled: canReviewSyncIssues,
  });

  const pendingApprovalQuery = useQuery({
    queryKey: ["sales", "pending-approval"],
    queryFn: () => salesApi.list({ status: "EN_ATTENTE_APPROBATION", per_page: 5 }),
    enabled: canReviewSyncIssues,
  });

  const conflicts = conflictsQuery.data?.data ?? [];
  const pendingApproval = pendingApprovalQuery.data?.data ?? [];
  const syncIssuesCount =
    (conflictsQuery.data?.meta.total ?? 0) + (pendingApprovalQuery.data?.meta.total ?? 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-primary-dark">Tableau de bord</h1>
        <p className="text-sm text-muted">Vue d'ensemble de l'activite du jour</p>
      </div>

      {canReviewSyncIssues && syncIssuesCount > 0 && (
        <div className="card border-l-4 border-l-red-500">
          <h2 className="card-title flex items-center gap-2 text-red-700">
            <ShieldAlert className="h-4 w-4" />
            Ventes synchronisées à régulariser ({syncIssuesCount})
          </h2>
          <p className="text-sm text-muted">
            Ces ventes saisies hors-ligne ont été synchronisées mais nécessitent une vérification
            (conflit de stock RG-29 ou remise en attente d'approbation RG-23).
          </p>

          {conflicts.length > 0 && (
            <div className="mt-3">
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-red-700">
                Conflits de stock ({conflictsQuery.data?.meta.total})
              </p>
              <ul className="space-y-1 text-sm">
                {conflicts.map((sale) => (
                  <li key={sale.id} className="flex items-center justify-between gap-2">
                    <span>
                      <span className="font-medium text-primary-dark">{sale.reference}</span> —{" "}
                      {sale.branch_name} · {formatDateTime(sale.created_at)}
                    </span>
                    <span className="text-muted">{formatCurrency(sale.total)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {pendingApproval.length > 0 && (
            <div className="mt-3">
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-amber-700">
                Remises en attente d'approbation ({pendingApprovalQuery.data?.meta.total})
              </p>
              <ul className="space-y-1 text-sm">
                {pendingApproval.map((sale) => (
                  <li key={sale.id} className="flex items-center justify-between gap-2">
                    <span>
                      <span className="font-medium text-primary-dark">{sale.reference}</span> —{" "}
                      {sale.branch_name} · {formatDateTime(sale.created_at)} · remise {sale.discount_rate}%
                    </span>
                    <span className="text-muted">{formatCurrency(sale.total)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <Link to="/ventes" className="mt-3 inline-block text-sm font-medium text-primary hover:underline">
            Voir l'historique des ventes →
          </Link>
        </div>
      )}

      {isLoading && (
        <div className="flex items-center gap-2 text-muted">
          <Loader2 className="h-4 w-4 animate-spin" />
          Chargement des indicateurs...
        </div>
      )}

      {isError && (
        <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
          {getApiErrorMessage(error, "Impossible de charger le tableau de bord.")}
        </div>
      )}

      {data && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard
              icon={Banknote}
              label="Ventes du jour"
              value={formatCurrency(data.sales_today_total)}
              accent="bg-primary/10 text-primary"
            />
            <KpiCard
              icon={Receipt}
              label="Nombre de ventes"
              value={formatNumber(data.sales_today_count)}
              accent="bg-primary-light/10 text-primary-light"
            />
            <KpiCard
              icon={TrendingUp}
              label="Panier moyen"
              value={formatCurrency(data.average_basket)}
              accent="bg-muted/10 text-muted"
            />
            <KpiCard
              icon={AlertTriangle}
              label="Alertes stock bas"
              value={formatNumber(data.low_stock_count)}
              accent={
                data.low_stock_count > 0
                  ? "bg-amber-100 text-amber-700"
                  : "bg-green-100 text-green-700"
              }
            />
          </div>

          <div className="card">
            <h2 className="card-title">Produits les plus vendus aujourd'hui</h2>
            {data.top_products_today.length === 0 ? (
              <p className="text-sm text-muted">Aucune vente enregistree pour le moment.</p>
            ) : (
              <div className="overflow-x-auto">
              <table className="table-base">
                <thead>
                  <tr>
                    <th>SKU</th>
                    <th>Produit</th>
                    <th className="text-right">Quantite vendue</th>
                  </tr>
                </thead>
                <tbody>
                  {data.top_products_today.map((p) => (
                    <tr key={p.product_id}>
                      <td className="font-mono text-xs text-muted">{p.sku}</td>
                      <td>{p.name}</td>
                      <td className="text-right">{formatNumber(p.quantity_sold)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              </div>
            )}
          </div>
        </>
      )}

      {realtime.data && (
        <>
          <div>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-lg font-semibold text-primary-dark">Indicateurs temps reel</h2>
              <span
                className={`flex items-center gap-1 text-xs font-medium ${
                  realtime.isLive ? "text-green-700" : "text-muted"
                }`}
                title={
                  realtime.isLive
                    ? "Flux temps reel actif (SSE)"
                    : "Mode polling (rafraichissement periodique)"
                }
              >
                {realtime.isLive ? <Wifi className="h-3.5 w-3.5" /> : <WifiOff className="h-3.5 w-3.5" />}
                {realtime.isLive ? "Temps reel" : "Actualisation periodique"}
              </span>
            </div>
            <p className="text-xs text-muted">
              Derniere mise a jour : {formatDateTime(realtime.data.generated_at)}
            </p>
          </div>

          {realtime.error && (
            <div className="rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-700">{realtime.error}</div>
          )}

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard
              icon={Banknote}
              label="CA du jour"
              value={formatCurrency(realtime.data.kpis.ca_jour)}
              accent="bg-primary/10 text-primary"
            />
            <KpiCard
              icon={Banknote}
              label="CA du mois"
              value={formatCurrency(realtime.data.kpis.ca_mois)}
              accent="bg-primary-light/10 text-primary-light"
            />
            <KpiCard
              icon={TrendingUp}
              label="Marge (mois)"
              value={`${realtime.data.kpis.marge_pct.toFixed(1)} %`}
              accent="bg-muted/10 text-muted"
            />
            <KpiCard
              icon={Receipt}
              label="Panier moyen (jour)"
              value={formatCurrency(realtime.data.kpis.panier_moyen)}
              accent="bg-primary/10 text-primary"
            />
          </div>

          <div className="card">
            <h2 className="card-title flex items-center gap-2">
              <Sparkles className="h-4 w-4" />
              Alertes IA
            </h2>
            {realtime.data.alerts.length === 0 ? (
              <p className="text-sm text-muted">Aucune alerte en cours.</p>
            ) : (
              <ul className="space-y-2">
                {realtime.data.alerts.map((alert, index) => (
                  <AlertRow key={`${alert.type}-${alert.entity_id ?? index}`} alert={alert} />
                ))}
              </ul>
            )}
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <div className="card">
              <h2 className="card-title">Classement ABC/XYZ des produits</h2>
              {realtime.data.abc_xyz.length === 0 ? (
                <p className="text-sm text-muted">Aucune classification disponible pour le moment.</p>
              ) : (
                <div className="overflow-x-auto">
                <table className="table-base">
                  <thead>
                    <tr>
                      <th>Produit</th>
                      <th>Classe</th>
                      <th className="text-right">CA</th>
                    </tr>
                  </thead>
                  <tbody>
                    {realtime.data.abc_xyz.slice(0, 8).map((item) => (
                      <tr key={item.product_id}>
                        <td>{item.product_name}</td>
                        <td className="font-mono text-xs">{item.combined_class}</td>
                        <td className="text-right">{formatCurrency(item.revenue)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                </div>
              )}
            </div>

            <div className="card">
              <h2 className="card-title flex items-center gap-2">
                <Users className="h-4 w-4" />
                Segmentation client (RFM)
              </h2>
              {realtime.data.rfm_segments.length === 0 ? (
                <p className="text-sm text-muted">Aucun segment disponible pour le moment.</p>
              ) : (
                <div className="overflow-x-auto">
                <table className="table-base">
                  <thead>
                    <tr>
                      <th>Client</th>
                      <th>Segment</th>
                      <th className="text-right">Montant</th>
                    </tr>
                  </thead>
                  <tbody>
                    {realtime.data.rfm_segments.slice(0, 8).map((item) => (
                      <tr key={item.customer_id}>
                        <td>{item.customer_name ?? "—"}</td>
                        <td>{item.segment_label}</td>
                        <td className="text-right">{formatCurrency(item.monetary)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

interface KpiCardProps {
  icon: typeof Banknote;
  label: string;
  value: string;
  accent: string;
}

function KpiCard({ icon: Icon, label, value, accent }: KpiCardProps) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`flex h-11 w-11 items-center justify-center rounded-lg ${accent}`}>
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <p className="text-xs text-muted">{label}</p>
        <p className="text-lg font-semibold text-primary-dark">{value}</p>
      </div>
    </div>
  );
}

const ALERT_ICONS: Record<DashboardAlert["type"], typeof PackageX> = {
  RUPTURE_STOCK: PackageX,
  ANOMALIE: AlertTriangle,
  CREDIT_RISK: BadgeAlert,
};

const SEVERITY_STYLES: Record<DashboardAlertSeverity, string> = {
  INFO: "border-l-primary-light bg-primary-light/5 text-primary-dark",
  WARNING: "border-l-amber-500 bg-amber-50 text-amber-800",
  CRITICAL: "border-l-red-500 bg-red-50 text-red-800",
};

function AlertRow({ alert }: { alert: DashboardAlert }) {
  const Icon = ALERT_ICONS[alert.type] ?? AlertTriangle;
  return (
    <li c