import { useMemo, useState, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Brain, Download, Loader2, RefreshCw } from "lucide-react";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

import { analyticsApi } from "@/api/endpoints/analytics";
import { productsApi } from "@/api/endpoints/products";
import { reportsApi } from "@/api/endpoints/reports";
import { getApiErrorMessage } from "@/api/client";
import { useAuthStore } from "@/app/store";
import {
  ABC_CLASSES,
  CREDIT_RISK_LEVELS,
  ML_MODEL_TYPES,
  XYZ_CLASSES,
  type CreditRiskLevel,
  type MlModelType,
} from "@/types/analytics";
import { formatCurrency, formatDateTime, formatNumber } from "@/utils/format";

// ── Palette ──────────────────────────────────────────────────────────────────

const C = {
  primary:   "#2563EB",
  secondary: "#10B981",
  warning:   "#F59E0B",
  danger:    "#EF4444",
  muted:     "#94A3B8",
  purple:    "#8B5CF6",
  pink:      "#EC4899",
  cyan:      "#06B6D4",
  orange:    "#F97316",
};

const ABC_COLOR: Record<string, string>  = { A: C.primary, B: C.secondary, C: C.muted };
const RISK_COLOR: Record<string, string> = { ELEVE: C.danger, MOYEN: C.warning, FAIBLE: C.secondary };
const SEG_PALETTE = [C.primary, C.secondary, C.purple, C.warning, C.danger, C.cyan, C.pink, C.orange];

// ── Onglets ──────────────────────────────────────────────────────────────────

const TABS = [
  { id: "dashboard", label: "Tableau de bord"     },
  { id: "forecast",  label: "Prévisions de demande"},
  { id: "abc-xyz",   label: "ABC / XYZ"            },
  { id: "rfm",       label: "Segmentation RFM"     },
  { id: "credit",    label: "Scoring crédit"       },
  { id: "anomalies", label: "Anomalies"            },
  { id: "cohorts",   label: "Cohortes clients"     },
  { id: "clv",       label: "Valeur vie client"    },
  { id: "ml",        label: "Modèles IA"           },
] as const;

type TabId = (typeof TABS)[number]["id"];

const RISK_BADGE: Record<CreditRiskLevel, string> = {
  ELEVE:  "badge-danger",
  MOYEN:  "badge-warning",
  FAIBLE: "badge-success",
};

const MODEL_LABELS: Record<MlModelType, string> = {
  DEMAND_FORECAST:   "Prévision de la demande",
  CREDIT_SCORING:    "Scoring crédit",
  ANOMALY_DETECTION: "Détection d'anomalies",
  ABC_XYZ:           "Classification ABC/XYZ",
  RFM_SEGMENTATION:  "Segmentation RFM",
};

// ── Hook hauteur de graphique responsive ─────────────────────────────────────

function useChartHeight(desktop = 280, mobile = 200) {
  const [height, setHeight] = useState(() =>
    typeof window !== "undefined" && window.innerWidth < 640 ? mobile : desktop
  );
  useEffect(() => {
    const fn = () => setHeight(window.innerWidth < 640 ? mobile : desktop);
    window.addEventListener("resize", fn);
    return () => window.removeEventListener("resize", fn);
  }, [desktop, mobile]);
  return height;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function downloadBlob(blob: Blob, filename: string) {
  const url  = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href     = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// ── Custom Recharts tooltips ──────────────────────────────────────────────────

function CurrencyTip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-surface bg-white p-3 text-xs shadow-lg">
      <p className="mb-1 font-semibold text-primary-dark">{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}: <strong>{formatCurrency(p.value)}</strong>
        </p>
      ))}
    </div>
  );
}

function TrendTip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-surface bg-white p-3 text-xs shadow-lg">
      <p className="mb-1 font-semibold text-primary-dark">{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}:{" "}
          <strong>
            {p.dataKey === "sales_count" ? formatNumber(p.value) : formatCurrency(p.value)}
          </strong>
        </p>
      ))}
    </div>
  );
}

function ScatterTip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload ?? {};
  return (
    <div className="rounded-lg border border-surface bg-white p-3 text-xs shadow-lg">
      {d.name     && <p className="mb-1 font-semibold text-primary-dark">{d.name}</p>}
      {d.x        !== undefined && <p>Récence : <strong>{formatNumber(d.x)} j</strong></p>}
      {d.y        !== undefined && <p>Fréquence : <strong>{formatNumber(d.y)}</strong></p>}
      {d.z        !== undefined && <p>Montant : <strong>{formatCurrency(d.z)}</strong></p>}
      {d.remise   !== undefined && <p>Remise : <strong>{d.remise} %</strong></p>}
      {d.score    !== undefined && <p>Score : <strong>{d.score.toFixed(2)}</strong></p>}
      {d.cashier  && <p>Caissier : <strong>{d.cashier}</strong></p>}
    </div>
  );
}

// ── AnalyticsPage ─────────────────────────────────────────────────────────────

/**
 * Tableau de bord analytique et IA (RF-24 à RF-29).
 * Chaque onglet combine graphiques Recharts + tableau détaillé.
 */
export default function AnalyticsPage() {
  const user        = useAuthStore((s) => s.user);
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const canTrain    = hasPermission("ml:train");
  const queryClient = useQueryClient();

  const [tab,        setTab]        = useState<TabId>("dashboard");
  const [branchId,   setBranchId]   = useState(user?.branch_id ?? "");
  const [days,       setDays]       = useState(30);
  const [alertsOnly, setAlertsOnly] = useState(false);
  const [abcClass,   setAbcClass]   = useState("");
  const [xyzClass,   setXyzClass]   = useState("");
  const [riskLevel,  setRiskLevel]  = useState("");
  const [exporting,  setExporting]  = useState(false);
  const [exportError,setExportError]= useState<string | null>(null);

  // Hauteurs de graphiques adaptées au viewport
  const chartH     = useChartHeight(280, 200);
  const chartHSm   = useChartHeight(260, 190);
  const chartHBar  = useChartHeight(300, 220);

  // ── Queries ────────────────────────────────────────────────────────────────

  const branchesQuery = useQuery({
    queryKey: ["branches"],
    queryFn:  productsApi.branches,
    enabled:  !user?.branch_id,
  });

  const salesTrendQuery = useQuery({
    queryKey: ["analytics-sales-trend", branchId, days],
    queryFn:  () => analyticsApi.salesTrend({ branch_id: branchId || undefined, days }),
    enabled:  tab === "dashboard",
  });

  const dashboardQuery = useQuery({
    queryKey: ["analytics-dashboard", branchId, days],
    queryFn:  () => analyticsApi.dashboard({ branch_id: branchId || undefined, days }),
    enabled:  tab === "dashboard",
  });

  const forecastQuery = useQuery({
    queryKey: ["analytics-forecast", branchId, alertsOnly],
    queryFn:  () => analyticsApi.forecast({ branch_id: branchId || undefined, alerts_only: alertsOnly || undefined }),
    enabled:  tab === "forecast",
  });

  const abcXyzQuery = useQuery({
    queryKey: ["analytics-abc-xyz", abcClass, xyzClass],
    queryFn:  () => analyticsApi.abcXyz({ abc_class: abcClass || undefined, xyz_class: xyzClass || undefined }),
    enabled:  tab === "abc-xyz",
  });

  const rfmQuery = useQuery({
    queryKey: ["analytics-rfm"],
    queryFn:  () => analyticsApi.rfmSegments(),
    enabled:  tab === "rfm",
  });

  const creditQuery = useQuery({
    queryKey: ["analytics-credit", riskLevel],
    queryFn:  () => analyticsApi.creditScores({ risk_level: riskLevel || undefined }),
    enabled:  tab === "credit",
  });

  const anomaliesQuery = useQuery({
    queryKey: ["analytics-anomalies", branchId],
    queryFn:  () => analyticsApi.anomalies({ branch_id: branchId || undefined }),
    enabled:  tab === "anomalies",
  });

  const mlModelsQuery = useQuery({
    queryKey: ["ml-models"],
    queryFn:  analyticsApi.mlModels,
    enabled:  tab === "ml",
  });

  const cohortsQuery = useQuery({
    queryKey: ["analytics-cohorts"],
    queryFn:  () => analyticsApi.cohorts({ months: 12 }),
    enabled:  tab === "cohorts",
    staleTime: 300_000,
  });

  const clvQuery = useQuery({
    queryKey: ["analytics-clv"],
    queryFn:  () => analyticsApi.clv({ limit: 50 }),
    enabled:  tab === "clv",
    staleTime: 300_000,
  });

  const trainMutation = useMutation({
    mutationFn: (modelType: MlModelType) => analyticsApi.trainModel(modelType),
    onSuccess:  () => queryClient.invalidateQueries({ queryKey: ["ml-models"] }),
  });

  const handleExport = async () => {
    setExportError(null);
    setExporting(true);
    try {
      const blob = await reportsApi.exportPdf({ branch_id: branchId || undefined, days });
      downloadBlob(blob, `rapport-tableau-de-bord-${days}j.pdf`);
    } catch (error) {
      setExportError(getApiErrorMessage(error, "Impossible de générer l'export PDF."));
    } finally {
      setExporting(false);
    }
  };

  // ── Données dérivées pour graphiques ──────────────────────────────────────

  /** ABC : répartition CA par classe (Pie) */
  const abcPieData = useMemo(() => {
    const totals: Record<string, number> = { A: 0, B: 0, C: 0 };
    abcXyzQuery.data?.items.forEach((i) => { totals[i.abc_class] += i.revenue; });
    return Object.entries(totals)
      .filter(([, v]) => v > 0)
      .map(([abc, value]) => ({ name: `Classe ${abc}`, abc, value }));
  }, [abcXyzQuery.data]);

  /** ABC : nombre de produits par classe combinée (Bar) */
  const abcCountData = useMemo(() => {
    const counts: Record<string, number> = {};
    abcXyzQuery.data?.items.forEach((i) => {
      counts[i.combined_class] = (counts[i.combined_class] ?? 0) + 1;
    });
    return Object.entries(counts)
      .map(([name, count]) => ({ name, count, abc: name[0] }))
      .sort((a, b) => b.count - a.count);
  }, [abcXyzQuery.data]);

  /** RFM : Scatter groupé par segment */
  const rfmScatterGroups = useMemo(() => {
    const groups: Record<string, Array<{ x: number; y: number; z: number; name: string }>> = {};
    rfmQuery.data?.items.forEach((i) => {
      if (!groups[i.segment_label]) groups[i.segment_label] = [];
      groups[i.segment_label].push({ x: i.recency_days, y: i.frequency, z: i.monetary, name: i.customer_name });
    });
    return Object.entries(groups).map(([seg, data], idx) => ({
      seg,
      data,
      color: SEG_PALETTE[idx % SEG_PALETTE.length],
    }));
  }, [rfmQuery.data]);

  /** RFM : count par segment (Bar horizontal) */
  const rfmSegCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    rfmQuery.data?.items.forEach((i) => {
      counts[i.segment_label] = (counts[i.segment_label] ?? 0) + 1;
    });
    return Object.entries(counts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count);
  }, [rfmQuery.data]);

  /** Crédit : distribution par niveau de risque (Pie) */
  const creditPieData = useMemo(() => {
    const counts: Record<string, number> = { ELEVE: 0, MOYEN: 0, FAIBLE: 0 };
    creditQuery.data?.items.forEach((i) => { counts[i.risk_level] += 1; });
    const labels: Record<string, string> = { ELEVE: "Risque élevé", MOYEN: "Risque moyen", FAIBLE: "Faible risque" };
    return Object.entries(counts)
      .filter(([, v]) => v > 0)
      .map(([key, value]) => ({ name: labels[key] ?? key, value, key }));
  }, [creditQuery.data]);

  /** Crédit : top 10 par score (Bar horizontal) */
  const creditTopBar = useMemo(() =>
    (creditQuery.data?.items ?? [])
      .slice()
      .sort((a, b) => b.score - a.score)
      .slice(0, 10)
      .map((i) => ({ name: i.customer_name, score: i.score, risk: i.risk_level })),
  [creditQuery.data]);

  /** Anomalies : scatter remise vs score */
  const anomalyScatter = useMemo(() =>
    (anomaliesQuery.data?.items ?? []).map((i) => ({
      remise:  i.remise_taux,
      score:   i.score,
      montant: i.montant_total,
      cashier: i.cashier_name,
      name:    i.reference,
    })),
  [anomaliesQuery.data]);

  /** Prévisions : top 12 produits pour bar chart */
  const forecastBar = useMemo(() =>
    (forecastQuery.data?.items ?? []).slice(0, 12).map((i) => ({
      name:      i.product_name.length > 14 ? i.product_name.slice(0, 13) + "…" : i.product_name,
      stock:     i.stock_disponible,
      seuil:     i.seuil_min,
      prevision: i.stock_prevu_j7,
    })),
  [forecastQuery.data]);

  // ── JSX ───────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-primary-dark">Analytique &amp; IA</h1>
        <p className="text-sm text-muted">
          Tableau de bord avancé, prévisions, scoring et détection d'anomalies (RF-24 à RF-29)
        </p>
      </div>

      <div className="card space-y-4">

        {/* ── Navigation par onglets (scroll horizontal sur mobile) ── */}
        <div className="flex gap-2 overflow-x-auto pb-1 no-scrollbar">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              className={`shrink-0 ${tab === t.id ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* ── Filtres contextuels ── */}
        <div className="flex flex-wrap items-center gap-3">
          {!user?.branch_id && (tab === "dashboard" || tab === "forecast" || tab === "anomalies") && (
            <select className="input max-w-xs" value={branchId} onChange={(e) => setBranchId(e.target.value)}>
              <option value="">Tous les sites</option>
              {(branchesQuery.data ?? []).map((b) => (
                <option key={b.id} value={b.id}>{b.name}</option>
              ))}
            </select>
          )}

          {tab === "dashboard" && (
            <>
              <select className="input max-w-[10rem]" value={days} onChange={(e) => setDays(Number(e.target.value))}>
                <option value={7}>7 derniers jours</option>
                <option value={30}>30 derniers jours</option>
                <option value={90}>90 derniers jours</option>
              </select>
              <button type="button" className="btn-secondary" disabled={exporting} onClick={handleExport}>
                {exporting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
                Exporter en PDF
              </button>
            </>
          )}

          {tab === "forecast" && (
            <label className="flex items-center gap-2 text-sm text-primary-dark">
              <input type="checkbox" checked={alertsOnly} onChange={(e) => setAlertsOnly(e.target.checked)} />
              Alertes de rupture uniquement
            </label>
          )}

          {tab === "abc-xyz" && (
            <>
              <select className="input max-w-[10rem]" value={abcClass} onChange={(e) => setAbcClass(e.target.value)}>
                <option value="">Toutes classes ABC</option>
                {ABC_CLASSES.map((c) => <option key={c} value={c}>Classe {c}</option>)}
              </select>
              <select className="input max-w-[10rem]" value={xyzClass} onChange={(e) => setXyzClass(e.target.value)}>
                <option value="">Toutes classes XYZ</option>
                {XYZ_CLASSES.map((c) => <option key={c} value={c}>Classe {c}</option>)}
              </select>
            </>
          )}

          {tab === "credit" && (
            <select className="input max-w-[12rem]" value={riskLevel} onChange={(e) => setRiskLevel(e.target.value)}>
              <option value="">Tous les niveaux de risque</option>
              {CREDIT_RISK_LEVELS.map((r) => <option key={r} value={r}>Risque {r.toLowerCase()}</option>)}
            </select>
          )}
        </div>

        {exportError && (
          <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{exportError}</div>
        )}

        {/* ════════════════════════════════════
            TABLEAU DE BORD (RF-24)
        ════════════════════════════════════ */}
        {tab === "dashboard" && (
          <div className="space-y-6">

            {/* Tendance CA / Marge */}
            <Section title={`Évolution du CA et de la marge — ${days} derniers jours`}>
              {salesTrendQuery.isLoading && <ChartSkeleton />}
              {salesTrendQuery.data?.items.length === 0 && (
                <p className="py-10 text-center text-sm text-muted">Aucune vente sur la période.</p>
              )}
              {salesTrendQuery.data && salesTrendQuery.data.items.length > 0 && (
                <ResponsiveContainer width="100%" height={chartH}>
                  <AreaChart data={salesTrendQuery.data.items} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                    <defs>
                      <linearGradient id="gCA" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor={C.primary}   stopOpacity={0.25} />
                        <stop offset="95%" stopColor={C.primary}   stopOpacity={0}    />
                      </linearGradient>
                      <linearGradient id="gMarge" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor={C.secondary} stopOpacity={0.25} />
                        <stop offset="95%" stopColor={C.secondary} stopOpacity={0}    />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(d: string) => d.slice(5)} />
                    <YAxis tick={{ fontSize: 11 }} tickFormatter={(v: number) =>
                      v >= 1_000_000 ? `${(v / 1_000_000).toFixed(1)}M`
                      : v >= 1_000 ? `${(v / 1_000).toFixed(0)}k`
                      : String(v)
                    } />
                    <Tooltip content={<TrendTip />} />
                    <Legend />
                    <Area type="monotone" dataKey="revenue"     name="Chiffre d'affaires" stroke={C.primary}   fill="url(#gCA)"    strokeWidth={2} dot={false} />
                    <Area type="monotone" dataKey="margin"      name="Marge"               stroke={C.secondary} fill="url(#gMarge)" strokeWidth={2} dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </Section>

            {/* KPIs + Bar sites */}
            <QueryState query={dashboardQuery} errorMessage="Impossible de charger le tableau de bord analytique.">
              {(data) => (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <KpiCard label="Nombre de ventes"  value={formatNumber(data.consolidated.sales_count)} />
                    <KpiCard label="Chiffre d'affaires" value={formatCurrency(data.consolidated.revenue)}  />
                    <KpiCard label="Marge brute"        value={formatCurrency(data.consolidated.margin)}   />
                    <KpiCard label="Taux de marge"      value={`${data.consolidated.margin_rate_pct} %`} accent />
                  </div>

                  {data.branches.length > 1 && (
                    <Section title="Comparaison des sites — CA et marge">
                      <ResponsiveContainer width="100%" height={chartHSm}>
                        <BarChart
                          data={data.branches.map((b) => ({
                            name:  b.branch_name,
                            "CA":  Number(b.revenue),
                            Marge: Number(b.margin),
                          }))}
                          margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                          <YAxis tick={{ fontSize: 11 }} tickFormatter={(v: number) =>
                            v >= 1_000_000 ? `${(v / 1_000_000).toFixed(1)}M`
                            : v >= 1_000 ? `${(v / 1_000).toFixed(0)}k`
                            : String(v)
                          } />
                          <Tooltip content={<CurrencyTip />} />
                          <Legend />
                          <Bar dataKey="CA"    fill={C.primary}   radius={[4, 4, 0, 0]} />
                          <Bar dataKey="Marge" fill={C.secondary} radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </Section>
                  )}

                  <div>
                    <h3 className="mb-2 text-sm font-semibold text-primary-dark">Détail par site</h3>
                    <div className="overflow-x-auto">
                      <table className="table-base">
                        <thead>
                          <tr>
                            <th>Site</th>
                            <th className="text-right">Nb ventes</th>
                            <th className="text-right">Chiffre d'affaires</th>
                            <th className="text-right">Coût</th>
                            <th className="text-right">Marge</th>
                            <th className="text-right">Taux de marge</th>
                          </tr>
                        </thead>
                        <tbody>
                          {data.branches.map((b) => (
                            <tr key={b.branch_id}>
                              <td className="font-medium text-primary-dark">{b.branch_name}</td>
                              <td className="text-right">{formatNumber(b.sales_count)}</td>
                              <td className="text-right">{formatCurrency(b.revenue)}</td>
                              <td className="text-right">{formatCurrency(b.cost)}</td>
                              <td className="text-right">{formatCurrency(b.margin)}</td>
                              <td className="text-right">{b.margin_rate_pct} %</td>
                            </tr>
                          ))}
                          <tr className="font-semibold">
                            <td>TOTAL CONSOLIDÉ</td>
                            <td className="text-right">{formatNumber(data.consolidated.sales_count)}</td>
                            <td className="text-right">{formatCurrency(data.consolidated.revenue)}</td>
                            <td className="text-right">{formatCurrency(data.consolidated.cost)}</td>
                            <td className="text-right">{formatCurrency(data.consolidated.margin)}</td>
                            <td className="text-right">{data.consolidated.margin_rate_pct} %</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </QueryState>
          </div>
        )}

        {/* ════════════════════════════════════
            PRÉVISIONS DE DEMANDE (RF-25)
        ════════════════════════════════════ */}
        {tab === "forecast" && (
          <QueryState query={forecastQuery} errorMessage="Impossible de charger les prévisions de demande.">
            {(data) => (
              <div className="space-y-6">
                {forecastBar.length > 0 && (
                  <Section title="Stock disponible vs seuil minimum vs stock prévu J+7 (Top 12)">
                    <ResponsiveContainer width="100%" height={chartHBar}>
                      <BarChart data={forecastBar} margin={{ top: 5, right: 20, left: 10, bottom: 60 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                        <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" interval={0} />
                        <YAxis tick={{ fontSize: 11 }} />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="stock"     name="Stock disponible" fill={C.primary}   radius={[4, 4, 0, 0]} />
                        <Bar dataKey="seuil"     name="Seuil minimum"    fill={C.warning}   radius={[4, 4, 0, 0]} />
                        <Bar dataKey="prevision" name="Stock prévu J+7"  fill={C.secondary} radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </Section>
                )}

                {data.items.filter((i) => i.alerte_rupture).length > 0 && (
                  <div className="flex items-center gap-2 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
                    <AlertTriangle className="h-4 w-4 shrink-0" />
                    <strong>{data.items.filter((i) => i.alerte_rupture).length} produit(s)</strong>
                    &nbsp;en risque de rupture dans les 7 prochains jours.
                  </div>
                )}

                <div className="overflow-x-auto">
                  <table className="table-base">
                    <thead>
                      <tr>
                        <th>SKU</th>
                        <th>Produit</th>
                        <th className="text-right">Stock dispo</th>
                        <th className="text-right">Seuil mini</th>
                        <th className="text-right">Prév. 7j</th>
                        <th className="text-right">Prév. 30j</th>
                        <th className="text-right">Stock J+7</th>
                        <th className="text-right">Qté recommandée</th>
                        <th>Alerte</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.items.length === 0 && (
                        <tr><td colSpan={9} className="text-center text-muted">Aucune prévision disponible.</td></tr>
                      )}
                      {data.items.map((item) => (
                        <tr key={`${item.product_id}-${item.branch_id}`}>
                          <td className="font-mono text-xs text-muted">{item.product_sku}</td>
                          <td className="font-medium text-primary-dark">{item.product_name}</td>
                          <td className="text-right">{formatNumber(item.stock_disponible)}</td>
                          <td className="text-right">{formatNumber(item.seuil_min)}</td>
                          <td className="text-right">{formatNumber(item.forecast_7d)}</td>
                          <td className="text-right">{formatNumber(item.forecast_30d)}</td>
                          <td className="text-right">{formatNumber(item.stock_prevu_j7)}</td>
                          <td className="text-right">{formatNumber(item.quantite_recommandee)}</td>
                          <td>
                            {item.alerte_rupture
                              ? <span className="badge badge-danger"><AlertTriangle className="mr-1 h-3 w-3" />Rupture</span>
                              : <span className="badge badge-success">OK</span>
                            }
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </QueryState>
        )}

        {/* ════════════════════════════════════
            ABC / XYZ (RF-26)
        ════════════════════════════════════ */}
        {tab === "abc-xyz" && (
          <QueryState query={abcXyzQuery} errorMessage="Impossible de charger la classification ABC/XYZ.">
            {(data) => (
              <div className="space-y-6">
                <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                  {/* Pie : CA par classe ABC */}
                  <Section title="Part du CA par classe ABC">
                    {abcPieData.length > 0 ? (
                      <ResponsiveContainer width="100%" height={chartHSm}>
                        <PieChart>
                          <Pie
                            data={abcPieData}
                            dataKey="value"
                            nameKey="name"
                            cx="50%" cy="50%"
                            outerRadius={90} innerRadius={45}
                            label={({ name, percent }: { name?: string; percent?: number }) => `${name ?? ""} — ${((percent ?? 0) * 100).toFixed(1)} %`}
                            labelLine={false}
                          >
                            {abcPieData.map((e) => <Cell key={e.abc} fill={ABC_COLOR[e.abc] ?? C.muted} />)}
                          </Pie>
                          <Tooltip formatter={(v) => formatCurrency(Number(v ?? 0))} />
                          <Legend />
                        </PieChart>
                      </ResponsiveContainer>
                    ) : (
                      <p className="py-10 text-center text-sm text-muted">Aucune donnée.</p>
                    )}
                  </Section>

                  {/* Bar : produits par classe combinée */}
                  <Section title="Nombre de produits par classe ABC × XYZ">
                    {abcCountData.length > 0 ? (
                      <ResponsiveContainer width="100%" height={chartHSm}>
                        <BarChart data={abcCountData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                          <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                          <Tooltip formatter={(v) => [formatNumber(Number(v ?? 0)), "Produits"]} />
                          <Bar dataKey="count" name="Produits" radius={[4, 4, 0, 0]}>
                            {abcCountData.map((e) => <Cell key={e.name} fill={ABC_COLOR[e.abc] ?? C.muted} />)}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <p className="py-10 text-center text-sm text-muted">Aucune donnée.</p>
                    )}
                  </Section>
                </div>

                <div className="overflow-x-auto">
                  <table className="table-base">
                    <thead>
                      <tr>
                        <th>SKU</th>
                        <th>Produit</th>
                        <th className="text-right">CA</th>
                        <th>Classe ABC</th>
                        <th className="text-right">Coeff. variation</th>
                        <th>Classe XYZ</th>
                        <th>Classe combinée</th>
                        <th>Stock mort</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.items.length === 0 && (
                        <tr><td colSpan={8} className="text-center text-muted">Aucune donnée de classification disponible.</td></tr>
                      )}
                      {data.items.map((item) => (
                        <tr key={item.product_id} className={item.dead_stock ? "bg-red-50/40" : ""}>
                          <td className="font-mono text-xs text-muted">{item.product_sku}</td>
                          <td className="font-medium text-primary-dark">{item.product_name}</td>
                          <td className="text-right">{formatCurrency(item.revenue)}</td>
                          <td><span className="badge badge-info">{item.abc_class}</span></td>
                          <td className="text-right">{item.cv != null ? item.cv.toFixed(2) : "—"}</td>
                          <td><span className="badge badge-info">{item.xyz_class}</span></td>
                          <td className="font-semibold">{item.combined_class}</td>
                          <td>
                            {item.dead_stock
                              ? <span className="badge badge-danger">⚠ Mort</span>
                              : <span className="text-xs text-muted">—</span>
                            }
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </QueryState>
        )}

        {/* ════════════════════════════════════
            SEGMENTATION RFM (RF-26)
        ════════════════════════════════════ */}
        {tab === "rfm" && (
          <QueryState query={rfmQuery} errorMessage="Impossible de charger la segmentation RFM.">
            {(data) => (
              <div className="space-y-6">
                <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                  {/* Scatter : Récence × Fréquence (taille = Montant) */}
                  <Section title="Nuage RFM — Récence vs Fréquence (taille ∝ Montant)">
                    {rfmScatterGroups.length > 0 ? (
                      <ResponsiveContainer width="100%" height={chartH}>
                        <ScatterChart margin={{ top: 10, right: 20, left: 0, bottom: 30 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                          <XAxis
                            dataKey="x"
                            name="Récence (j)"
                            type="number"
                            tick={{ fontSize: 11 }}
                            label={{ value: "Récence (jours)", position: "insideBottom", offset: -18, fontSize: 11 }}
                          />
                          <YAxis
                            dataKey="y"
                            name="Fréquence"
                            type="number"
                            tick={{ fontSize: 11 }}
                            label={{ value: "Fréquence", angle: -90, position: "insideLeft", fontSize: 11 }}
                          />
                          <ZAxis dataKey="z" name="Montant" range={[40, 400]} />
                          <Tooltip content={<ScatterTip />} />
                          <Legend />
                          {rfmScatterGroups.map(({ seg, data: sdata, color }) => (
                            <Scatter key={seg} name={seg} data={sdata} fill={color} fillOpacity={0.75} />
                          ))}
                        </ScatterChart>
                      </ResponsiveContainer>
                    ) : (
                      <p className="py-10 text-center text-sm text-muted">Aucun client segmenté.</p>
                    )}
                  </Section>

                  {/* Bar : nombre de clients par segment */}
                  <Section title="Distribution des segments clients">
                    {rfmSegCounts.length > 0 ? (
                      <ResponsiveContainer width="100%" height={chartH}>
                        <BarChart data={rfmSegCounts} layout="vertical" margin={{ top: 5, right: 20, left: 90, bottom: 5 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                          <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} />
                          <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={90} />
                          <Tooltip formatter={(v) => [formatNumber(Number(v ?? 0)), "Clients"]} />
                          <Bar dataKey="count" name="Clients" radius={[0, 4, 4, 0]}>
                            {rfmSegCounts.map((e, i) => (
                              <Cell key={e.name} fill={SEG_PALETTE[i % SEG_PALETTE.length]} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <p className="py-10 text-center text-sm text-muted">Aucune donnée.</p>
                    )}
                  </Section>
                </div>

                <div className="overflow-x-auto">
                  <table className="table-base">
                    <thead>
                      <tr>
                        <th>Client</th>
                        <th className="text-right">Récence (j)</th>
                        <th className="text-right">Fréquence</th>
                        <th className="text-right">Valeur</th>
                        <th>Segment</th>
                        <th>Action recommandée</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.items.length === 0 && (
                        <tr><td colSpan={6} className="text-center text-muted">Aucun client segmenté.</td></tr>
                      )}
                      {data.items.map((item) => (
                        <tr key={item.customer_id}>
                          <td className="font-medium text-primary-dark">{item.customer_name}</td>
                          <td className="text-right">{formatNumber(item.recency_days)}</td>
                          <td className="text-right">{formatNumber(item.frequency)}</td>
                          <td className="text-right">{formatCurrency(item.monetary)}</td>
                          <td><span className="badge badge-info">{item.segment_label}</span></td>
                          <td className="text-xs text-muted">{item.recommended_action}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </QueryState>
        )}

        {/* ════════════════════════════════════
            SCORING CRÉDIT (RF-27)
        ════════════════════════════════════ */}
        {tab === "credit" && (
          <QueryState query={creditQuery} errorMessage="Impossible de charger le scoring crédit.">
            {(data) => (
              <div className="space-y-6">
                <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                  {/* Pie : distribution risque */}
                  <Section title="Distribution du risque crédit">
                    {creditPieData.length > 0 ? (
                      <ResponsiveContainer width="100%" height={chartHSm}>
                        <PieChart>
                          <Pie
                            data={creditPieData}
                            dataKey="value"
                            nameKey="name"
                            cx="50%" cy="50%"
                            outerRadius={90} innerRadius={45}
                            label={({ name, percent }: { name?: string; percent?: number }) => `${name ?? ""} — ${((percent ?? 0) * 100).toFixed(0)} %`}
                            labelLine={false}
                          >
                            {creditPieData.map((e) => <Cell key={e.key} fill={RISK_COLOR[e.key] ?? C.muted} />)}
                          </Pie>
                          <Tooltip formatter={(v) => [formatNumber(Number(v ?? 0)), "Clients"]} />
                          <Legend />
                        </PieChart>
                      </ResponsiveContainer>
                    ) : (
                      <p className="py-10 text-center text-sm text-muted">Aucune donnée.</p>
                    )}
                  </Section>

                  {/* Bar horizontal : Top 10 scores */}
                  <Section title="Top 10 clients par score crédit">
                    {creditTopBar.length > 0 ? (
                      <ResponsiveContainer width="100%" height={chartHSm}>
                        <BarChart data={creditTopBar} layout="vertical" margin={{ top: 5, right: 20, left: 90, bottom: 5 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                          <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} />
                          <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={90} />
                          <Tooltip formatter={(v) => [formatNumber(Number(v ?? 0)), "Score"]} />
                          <ReferenceLine x={70} stroke={C.secondary} strokeDasharray="4 4" />
                          <ReferenceLine x={40} stroke={C.danger}    strokeDasharray="4 4" />
                          <Bar dataKey="score" name="Score crédit" radius={[0, 4, 4, 0]}>
                            {creditTopBar.map((e) => (
                              <Cell key={e.name} fill={RISK_COLOR[e.risk] ?? C.muted} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <p className="py-10 text-center text-sm text-muted">Aucune donnée.</p>
                    )}
                  </Section>
                </div>

                <div className="overflow-x-auto">
                  <table className="table-base">
                    <thead>
                      <tr>
                        <th>Client</th>
                        <th className="text-right">Score</th>
                        <th>Niveau de risque</th>
                        <th className="text-right">Achats à crédit</th>
                        <th className="text-right">Montant moyen</th>
                        <th className="text-right">Délai moyen (j)</th>
                        <th className="text-right">Taux de retard</th>
                        <th className="text-right">Solde dû</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.items.length === 0 && (
                        <tr><td colSpan={8} className="text-center text-muted">Aucun score crédit disponible.</td></tr>
                      )}
                      {data.items.map((item) => (
                        <tr key={item.customer_id}>
                          <td className="font-medium text-primary-dark">{item.customer_name}</td>
                          <td className="text-right">{item.score}</td>
                          <td><span className={`badge ${RISK_BADGE[item.risk_level]}`}>{item.risk_level}</span></td>
                          <td className="text-right">{formatNumber(item.nb_achats_credit_total)}</td>
                          <td className="text-right">{formatCurrency(item.montant_moyen_achat)}</td>
                          <td className="text-right">{item.delai_moyen_remboursement_jours}</td>
                          <td className="text-right">{(item.taux_retard * 100).toFixed(1)} %</td>
                          <td className="text-right">{formatCurrency(item.solde_du_actuel)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </QueryState>
        )}

        {/* ════════════════════════════════════
            ANOMALIES (RF-28)
        ════════════════════════════════════ */}
        {tab === "anomalies" && (
          <QueryState query={anomaliesQuery} errorMessage="Impossible de charger les anomalies.">
            {(data) => (
              <div className="space-y-6">
                <Section title="Score d'anomalie vs taux de remise (chaque point = une vente, taille ∝ montant)">
                  {anomalyScatter.length > 0 ? (
                    <ResponsiveContainer width="100%" height={chartH}>
                      <ScatterChart margin={{ top: 10, right: 20, left: 0, bottom: 30 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                        <XAxis
                          dataKey="remise"
                          name="Remise (%)"
                          type="number"
                          domain={[0, 100]}
                          tick={{ fontSize: 11 }}
                          label={{ value: "Taux de remise (%)", position: "insideBottom", offset: -18, fontSize: 11 }}
                        />
                        <YAxis
                          dataKey="score"
                          name="Score anomalie"
                          type="number"
                          tick={{ fontSize: 11 }}
                          label={{ value: "Score anomalie", angle: -90, position: "insideLeft", fontSize: 11 }}
                        />
                        <ZAxis dataKey="montant" name="Montant" range={[30, 250]} />
                        <Tooltip content={<ScatterTip />} />
                        <ReferenceLine
                          y={0.5}
                          stroke={C.warning}
                          strokeDasharray="4 4"
                          label={{ value: "Seuil alerte", fontSize: 10, fill: C.warning, position: "right" }}
                        />
                        <Scatter name="Ventes" data={anomalyScatter} fill={C.danger} fillOpacity={0.65} />
                      </ScatterChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="py-10 text-center text-sm text-muted">Aucune anomalie détectée.</p>
                  )}
                </Section>

                {data.items.length > 0 && (
                  <div className="flex items-center gap-2 rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-700">
                    <AlertTriangle className="h-4 w-4 shrink-0" />
                    <strong>{data.items.length} vente(s)</strong>&nbsp;signalée(s) comme anomalie. Analysez les motifs avant toute décision.
                  </div>
                )}

                <div className="overflow-x-auto">
                  <table className="table-base">
                    <thead>
                      <tr>
                        <th>Référence</th>
                        <th>Caissier</th>
                        <th className="text-right">Montant total</th>
                        <th className="text-right">Remise</th>
                        <th className="text-right">Score</th>
                        <th>Motifs</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.items.length === 0 && (
                        <tr><td colSpan={6} className="text-center text-muted">Aucune anomalie détectée.</td></tr>
                      )}
                      {data.items.map((item) => (
                        <tr key={item.sale_id}>
                          <td className="font-mono text-xs text-muted">{item.reference}</td>
                          <td>{item.cashier_name}</td>
                          <td className="text-right">{formatCurrency(item.montant_total)}</td>
                          <td className="text-right">{item.remise_taux} %</td>
                          <td className="text-right font-semibold text-amber-600">{item.score.toFixed(2)}</td>
                          <td className="text-xs text-muted">{item.reasons.join(", ")}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </QueryState>
        )}

        {/* ════════════════════════════════════
            COHORTES CLIENTS (Feature E)
        ════════════════════════════════════ */}
        {tab === "cohorts" && (
          <QueryState query={cohortsQuery} errorMessage="Impossible de charger les cohortes.">
            {(data) => (
              <div className="space-y-6">
                {/* Statistiques globales */}
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <KpiCard label="Cohortes analysées"   value={String(data.cohorts.length)} />
                  <KpiCard label="Horizont max analysé" value={`M+${data.max_months}`} />
                  <KpiCard
                    label="Clients total"
                    value={formatNumber(data.cohorts.reduce((s, c) => s + c.size, 0))}
                  />
                  <KpiCard
                    label="Rét. M+1 moyenne"
                    value={
                      data.cohorts.length
                        ? (() => {
                            const rates = data.cohorts
                              .map((c) => c.retention.find((r) => r.month === 1)?.rate ?? 0);
                            return (rates.reduce((a, b) => a + b, 0) / rates.length).toFixed(1) + " %";
                          })()
                        : "—"
                    }
                  />
                </div>

                {/* Heatmap de rétention */}
                <div className="overflow-x-auto rounded-xl border border-surface bg-white shadow-sm">
                  <div className="px-5 py-4">
                    <h3 className="mb-1 text-sm font-semibold text-primary-dark">
                      Matrice de rétention (% de clients encore actifs)
                    </h3>
                    <p className="mb-3 text-xs text-muted">
                      Chaque ligne = cohorte d'acquisition. Chaque colonne = M+N mois après le 1er achat.
                    </p>
                  </div>
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-surface bg-surface/50">
                        <th className="px-4 py-2 text-left font-semibold text-muted whitespace-nowrap">Cohorte</th>
                        <th className="px-3 py-2 text-center font-semibold text-muted">Taille</th>
                        {Array.from({ length: Math.min(data.max_months + 1, 13) }, (_, i) => (
                          <th key={i} className="px-3 py-2 text-center font-semibold text-muted whitespace-nowrap">
                            {i === 0 ? "M+0" : `M+${i}`}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {data.cohorts.map((cohort) => (
                        <tr key={cohort.cohort} className="border-b border-surface last:border-0">
                          <td className="px-4 py-2 font-medium text-primary-dark whitespace-nowrap">
                            {cohort.cohort}
                          </td>
                          <td className="px-3 py-2 text-center text-muted">{cohort.size}</td>
                          {Array.from({ length: Math.min(data.max_months + 1, 13) }, (_, i) => {
                            const point = cohort.retention.find((r) => r.month === i);
                            const rate = point?.rate ?? 0;
                            const opacity = i === 0 ? 1 : Math.min(rate / 100, 1);
                            const bg = i === 0
                              ? "bg-indigo-600 text-white"
                              : rate === 0
                              ? "bg-surface text-muted"
                              : rate >= 50
                              ? "bg-green-500 text-white"
                              : rate >= 20
                              ? "bg-amber-400 text-white"
                              : "bg-red-300 text-white";
                            return (
                              <td
                                key={i}
                                className={`px-3 py-2 text-center font-medium ${bg}`}
                                style={{ opacity: i === 0 ? 1 : 0.5 + opacity * 0.5 }}
                                title={point ? `${point.count} clients — ${rate}%` : "Aucune donnée"}
                              >
                                {point ? `${rate}%` : "—"}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* BarChart rétention M+1 par cohorte */}
                <div className="rounded-xl border border-surface bg-white p-5 shadow-sm">
                  <h3 className="mb-4 text-sm font-semibold text-primary-dark">
                    Taux de rétention M+1 par cohorte
                  </h3>
                  <ResponsiveContainer width="100%" height={240}>
                    <BarChart
                      data={data.cohorts.map((c) => ({
                        cohort: c.cohort,
                        "Rét. M+1 (%)": c.retention.find((r) => r.month === 1)?.rate ?? 0,
                        "Rét. M+3 (%)": c.retention.find((r) => r.month === 3)?.rate ?? 0,
                      }))}
                      margin={{ top: 10, right: 20, left: 0, bottom: 10 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                      <XAxis dataKey="cohort" tick={{ fontSize: 10 }} />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} unit="%" />
                      <Tooltip formatter={(v, name) => [`${v as number}%`, String(name)]} />
                      <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11 }} />
                      <Bar dataKey="Rét. M+1 (%)" fill="#4f46e5" radius={[3, 3, 0, 0]} />
                      <Bar dataKey="Rét. M+3 (%)" fill="#16a34a" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </QueryState>
        )}

        {/* ════════════════════════════════════
            CLV — VALEUR VIE CLIENT (Feature F)
        ════════════════════════════════════ */}
        {tab === "clv" && (
          <QueryState query={clvQuery} errorMessage="Impossible de charger les données CLV.">
            {(data) => (
              <div className="space-y-6">
                {/* KPI stats globales */}
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <KpiCard label="Clients analysés"  value={formatNumber(data.count)} accent />
                  <KpiCard label="CLV moyenne"        value={formatCurrency(data.stats.clv_moyen)} accent />
                  <KpiCard label="CLV médiane"        value={formatCurrency(data.stats.clv_median)} />
                  <KpiCard label="CLV max"            value={formatCurrency(data.stats.clv_max)} />
                </div>

                {/* Top 10 BarChart */}
                <div className="rounded-xl border border-surface bg-white p-5 shadow-sm">
                  <h3 className="mb-4 text-sm font-semibold text-primary-dark">
                    Top 10 clients par CLV estimée
                  </h3>
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart
                      data={data.items.slice(0, 10).map((c) => ({
                        name: c.name.length > 15 ? c.name.slice(0, 14) + "…" : c.name,
                        CLV: c.clv_estime,
                      }))}
                      layout="vertical"
                      margin={{ top: 5, right: 30, left: 60, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" horizontal={false} />
                      <XAxis
                        type="number"
                        tick={{ fontSize: 10 }}
                        tickFormatter={(v) =>
                          new Intl.NumberFormat("fr-FR", { notation: "compact" }).format(v as number)
                        }
                      />
                      <YAxis type="category" dataKey="name" tick={{ fontSize: 10 }} width={60} />
                      <Tooltip formatter={(v) => [formatCurrency(v as number), "CLV estimée"]} />
                      <Bar dataKey="CLV" fill="#4f46e5" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Tableau complet */}
                <div className="overflow-x-auto rounded-xl border border-surface bg-white shadow-sm">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-surface bg-surface/50">
                        <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted">#</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted">Client</th>
                        <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted">CA total</th>
                        <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted">Commandes</th>
                        <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted">Panier moy.</th>
                        <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted">Durée rel.</th>
                        <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted">Fréq./mois</th>
                        <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted">Confiance</th>
                        <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-muted">CLV estimée</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.items.length === 0 && (
                        <tr>
                          <td colSpan={9} className="py-8 text-center text-sm text-muted">
                            Aucune donnée disponible.
                          </td>
                        </tr>
                      )}
                      {data.items.map((item, idx) => (
                        <tr key={item.customer_id} className="border-b border-surface last:border-0 hover:bg-surface/30">
                          <td className="px-4 py-3 text-muted">{idx + 1}</td>
                          <td className="px-4 py-3">
                            <div className="font-medium text-primary-dark">{item.name}</div>
                            {item.customer_type && (
                              <div className="text-xs text-muted">{item.customer_type}</div>
                            )}
                          </td>
                          <td className="px-4 py-3 text-right">{formatCurrency(item.ca_total)}</td>
                          <td className="px-4 py-3 text-right">{item.nb_commandes}</td>
                          <td className="px-4 py-3 text-right">{formatCurrency(item.panier_moyen)}</td>
                          <td className="px-4 py-3 text-right text-muted">{item.duree_mois} mois</td>
                          <td className="px-4 py-3 text-right text-muted">{item.frequence_mensuelle.toFixed(2)}</td>
                          <td className="px-4 py-3 text-right">
                            {item.data_confidence != null ? (
                              <span className={`text-xs font-medium ${item.data_confidence >= 0.8 ? "text-green-600" : item.data_confidence >= 0.4 ? "text-amber-600" : "text-red-500"}`}>
                                {Math.round(item.data_confidence * 100)} %
                              </span>
                            ) : "—"}
                          </td>
                          <td className="px-4 py-3 text-right">
                            <span className="font-semibold text-indigo-700">
                              {formatCurrency(item.clv_estime)}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </QueryState>
        )}

        {/* ════════════════════════════════════
            MODÈLES IA (RF-29)
        ════════════════════════════════════ */}
        {tab === "ml" && (
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
              {ML_MODEL_TYPES.map((modelType) => (
                <button
                  key={modelType}
                  type="button"
                  className="btn-secondary"
                  disabled={!canTrain || trainMutation.isPending}
                  title={!canTrain ? "Permission ml:train requise" : undefined}
                  onClick={() => trainMutation.mutate(modelType)}
                >
                  {trainMutation.isPending && trainMutation.variables === modelType
                    ? <Loader2 className="h-4 w-4 animate-spin" />
                    : <Brain className="h-4 w-4" />
                  }
                  Entraîner : {MODEL_LABELS[modelType]}
                </button>
              ))}
              <button
                type="button"
                className="btn-ghost"
                onClick={() => queryClient.invalidateQueries({ queryKey: ["ml-models"] })}
              >
                <RefreshCw className="h-4 w-4" />
                Actualiser
              </button>
            </div>

            {trainMutation.isError && (
              <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
                {getApiErrorMessage(trainMutation.error, "Impossible de lancer l'entraînement.")}
              </div>
            )}
            {trainMutation.isSuccess && (
              <div className="rounded-lg bg-green-50 px-4 py-3 text-sm text-green-700">
                Entraînement « {MODEL_LABELS[trainMutation.data.model_type as MlModelType] ?? trainMutation.data.model_type} »
                {trainMutation.data.status === "queued" ? " planifié." : " terminé."}
              </div>
            )}

            <QueryState query={mlModelsQuery} errorMessage="Impossible de charger le registre des modèles.">
              {(models) => (
                <div className="overflow-x-auto">
                  <table className="table-base">
                    <thead>
                      <tr>
                        <th>Type de modèle</th>
                        <th>Version</th>
                        <th>Algorithme</th>
                        <th>Entraîné le</th>
                        <th>Statut</th>
                        <th>Run MLflow</th>
                      </tr>
                    </thead>
                    <tbody>
                      {models.length === 0 && (
                        <tr><td colSpan={6} className="text-center text-muted">Aucun modèle entraîné pour le moment.</td></tr>
                      )}
                      {models.map((model) => (
                        <tr key={model.id}>
                          <td className="font-medium text-primary-dark">
                            {MODEL_LABELS[model.model_type as MlModelType] ?? model.model_type}
                          </td>
                          <td>{model.version}</td>
                          <td>{model.algorithm}</td>
                          <td className="whitespace-nowrap text-xs text-muted">{formatDateTime(model.trained_at)}</td>
                          <td>
                            {model.is_active
                              ? <span className="badge badge-success">Actif</span>
                              : <span className="badge badge-warning">Inactif</span>
                            }
                          </td>
                          <td className="font-mono text-xs text-muted">{model.mlflow_run_id ?? "-"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </QueryState>
          </div>
        )}

      </div>
    </div>
  );
}

// ── Sous-composants ───────────────────────────────────────────────────────────

function KpiCard({ label, value, accent = false }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className={`card ${accent ? "border-l-4 border-l-primary" : ""}`}>
      <p className="text-xs text-muted">{label}</p>
      <p className="text-lg font-semibold text-primary-dark">{value}</p>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="mb-3 text-sm font-semibold