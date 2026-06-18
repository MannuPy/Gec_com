import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  Brain,
  Download,
  Loader2,
  RefreshCw,
} from "lucide-react";

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

const TABS = [
  { id: "dashboard", label: "Tableau de bord" },
  { id: "forecast", label: "Prévisions de demande" },
  { id: "abc-xyz", label: "ABC / XYZ" },
  { id: "rfm", label: "Segmentation RFM" },
  { id: "credit", label: "Scoring crédit" },
  { id: "anomalies", label: "Anomalies" },
  { id: "ml", label: "Modèles IA" },
] as const;

type TabId = (typeof TABS)[number]["id"];

const RISK_BADGE: Record<CreditRiskLevel, string> = {
  ELEVE: "badge-danger",
  MOYEN: "badge-warning",
  FAIBLE: "badge-success",
};

const MODEL_TYPE_LABELS: Record<MlModelType, string> = {
  DEMAND_FORECAST: "Prévision de la demande",
  CREDIT_SCORING: "Scoring crédit",
  ANOMALY_DETECTION: "Détection d'anomalies",
  ABC_XYZ: "Classification ABC/XYZ",
  RFM_SEGMENTATION: "Segmentation RFM",
};

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Tableau de bord analytique et intelligence artificielle (RF-24 à RF-29).
 * Cf. blueprint `analytics` : dashboard étendu, prévisions de demande,
 * scoring crédit, détection d'anomalies, classification ABC/XYZ,
 * segmentation RFM et registre des modèles ML.
 */
export default function AnalyticsPage() {
  const user = useAuthStore((s) => s.user);
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const canTrain = hasPermission("ml:train");
  const queryClient = useQueryClient();

  const [tab, setTab] = useState<TabId>("dashboard");
  const [branchId, setBranchId] = useState(user?.branch_id ?? "");
  const [days, setDays] = useState(30);
  const [alertsOnly, setAlertsOnly] = useState(false);
  const [abcClass, setAbcClass] = useState("");
  const [xyzClass, setXyzClass] = useState("");
  const [riskLevel, setRiskLevel] = useState("");
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const branchesQuery = useQuery({
    queryKey: ["branches"],
    queryFn: productsApi.branches,
    enabled: !user?.branch_id,
  });

  const dashboardQuery = useQuery({
    queryKey: ["analytics-dashboard", branchId, days],
    queryFn: () => analyticsApi.dashboard({ branch_id: branchId || undefined, days }),
    enabled: tab === "dashboard",
  });

  const forecastQuery = useQuery({
    queryKey: ["analytics-forecast", branchId, alertsOnly],
    queryFn: () => analyticsApi.forecast({ branch_id: branchId || undefined, alerts_only: alertsOnly || undefined }),
    enabled: tab === "forecast",
  });

  const abcXyzQuery = useQuery({
    queryKey: ["analytics-abc-xyz", abcClass, xyzClass],
    queryFn: () => analyticsApi.abcXyz({ abc_class: abcClass || undefined, xyz_class: xyzClass || undefined }),
    enabled: tab === "abc-xyz",
  });

  const rfmQuery = useQuery({
    queryKey: ["analytics-rfm"],
    queryFn: () => analyticsApi.rfmSegments(),
    enabled: tab === "rfm",
  });

  const creditQuery = useQuery({
    queryKey: ["analytics-credit", riskLevel],
    queryFn: () => analyticsApi.creditScores({ risk_level: riskLevel || undefined }),
    enabled: tab === "credit",
  });

  const anomaliesQuery = useQuery({
    queryKey: ["analytics-anomalies", branchId],
    queryFn: () => analyticsApi.anomalies({ branch_id: branchId || undefined }),
    enabled: tab === "anomalies",
  });

  const mlModelsQuery = useQuery({
    queryKey: ["ml-models"],
    queryFn: analyticsApi.mlModels,
    enabled: tab === "ml",
  });

  const trainMutation = useMutation({
    mutationFn: (modelType: MlModelType) => analyticsApi.trainModel(modelType),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["ml-models"] }),
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-primary-dark">Analytique &amp; IA</h1>
        <p className="text-sm text-muted">
          Tableau de bord avancé, prévisions, scoring et détection d'anomalies (RF-24 à RF-29)
        </p>
      </div>

      <div className="card space-y-4">
        <div className="flex flex-wrap gap-2">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              className={tab === t.id ? "btn-primary" : "btn-secondary"}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {!user?.branch_id && (tab === "dashboard" || tab === "forecast" || tab === "anomalies") && (
            <select className="input max-w-xs" value={branchId} onChange={(e) => setBranchId(e.target.value)}>
              <option value="">Tous les sites</option>
              {(branchesQuery.data ?? []).map((branch) => (
                <option key={branch.id} value={branch.id}>
                  {branch.name}
                </option>
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
                {ABC_CLASSES.map((c) => (
                  <option key={c} value={c}>
                    Classe {c}
                  </option>
                ))}
              </select>
              <select className="input max-w-[10rem]" value={xyzClass} onChange={(e) => setXyzClass(e.target.value)}>
                <option value="">Toutes classes XYZ</option>
                {XYZ_CLASSES.map((c) => (
                  <option key={c} value={c}>
                    Classe {c}
                  </option>
                ))}
              </select>
            </>
          )}

          {tab === "credit" && (
            <select className="input max-w-[12rem]" value={riskLevel} onChange={(e) => setRiskLevel(e.target.value)}>
              <option value="">Tous les niveaux de risque</option>
              {CREDIT_RISK_LEVELS.map((r) => (
                <option key={r} value={r}>
                  Risque {r.toLowerCase()}
                </option>
              ))}
            </select>
          )}
        </div>

        {exportError && <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{exportError}</div>}

        {/* ---- Tableau de bord (RF-24) ---- */}
        {tab === "dashboard" && (
          <QueryState query={dashboardQuery} errorMessage="Impossible de charger le tableau de bord analytique.">
            {(data) => (
              <div className="space-y-4">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  <KpiCard label="Nombre de ventes" value={formatNumber(data.consolidated.sales_count)} />
                  <KpiCard label="Chiffre d'affaires" value={formatCurrency(data.consolidated.revenue)} />
                  <KpiCard label="Marge" value={formatCurrency(data.consolidated.margin)} />
                  <KpiCard label="Taux de marge" value={`${data.consolidated.margin_rate_pct} %`} />
                </div>

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
            )}
          </QueryState>
        )}

        {/* ---- Prévisions de demande (RF-25, RG-38) ---- */}
        {tab === "forecast" && (
          <QueryState query={forecastQuery} errorMessage="Impossible de charger les prévisions de demande.">
            {(data) => (
              <div className="overflow-x-auto">
                <table className="table-base">
                  <thead>
                    <tr>
                      <th>SKU</th>
                      <th>Produit</th>
                      <th className="text-right">Stock disponible</th>
                      <th className="text-right">Seuil mini</th>
                      <th className="text-right">Prévision 7j</th>
                      <th className="text-right">Prévision 30j</th>
                      <th className="text-right">Stock prévu J+7</th>
                      <th className="text-right">Qté recommandée</th>
                      <th>Alerte</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.items.length === 0 && (
                      <tr>
                        <td colSpan={9} className="text-center text-muted">
                          Aucune prévision disponible.
                        </td>
                      </tr>
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
                          {item.alerte_rupture ? (
                            <span className="badge badge-danger">
                              <AlertTriangle className="mr-1 h-3 w-3" />
                              Rupture
                            </span>
                          ) : (
                            <span className="badge badge-success">OK</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </QueryState>
        )}

        {/* ---- Classification ABC/XYZ (RF-26) ---- */}
        {tab === "abc-xyz" && (
          <QueryState query={abcXyzQuery} errorMessage="Impossible de charger la classification ABC/XYZ.">
            {(data) => (
              <div className="overflow-x-auto">
                <table className="table-base">
                  <thead>
                    <tr>
                      <th>SKU</th>
                      <th>Produit</th>
                      <th className="text-right">Chiffre d'affaires</th>
                      <th>Classe ABC</th>
                      <th className="text-right">Coefficient de variation</th>
                      <th>Classe XYZ</th>
                      <th>Classe combinée</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.items.length === 0 && (
                      <tr>
                        <td colSpan={7} className="text-center text-muted">
                          Aucune donnée de classification disponible.
                        </td>
                      </tr>
                    )}
                    {data.items.map((item) => (
                      <tr key={item.product_id}>
                        <td className="font-mono text-xs text-muted">{item.product_sku}</td>
                        <td className="font-medium text-primary-dark">{item.product_name}</td>
                        <td className="text-right">{formatCurrency(item.revenue)}</td>
                        <td>
                          <span className="badge badge-info">{item.abc_class}</span>
                        </td>
                        <td className="text-right">{item.cv.toFixed(2)}</td>
                        <td>
                          <span className="badge badge-info">{item.xyz_class}</span>
                        </td>
                        <td className="font-semibold">{item.combined_class}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </QueryState>
        )}

        {/* ---- Segmentation RFM (RF-26) ---- */}
        {tab === "rfm" && (
          <QueryState query={rfmQuery} errorMessage="Impossible de charger la segmentation RFM.">
            {(data) => (
              <div className="overflow-x-auto">
                <table className="table-base">
                  <thead>
                    <tr>
                      <th>Client</th>
                      <th className="text-right">Récence (jours)</th>
                      <th className="text-right">Fréquence</th>
                      <th className="text-right">Valeur (montant)</th>
                      <th>Segment</th>
                      <th>Action recommandée</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.items.length === 0 && (
                      <tr>
                        <td colSpan={6} className="text-center text-muted">
                          Aucun client segmenté.
                        </td>
                      </tr>
                    )}
                    {data.items.map((item) => (
                      <tr key={item.customer_id}>
                        <td className="font-medium text-primary-dark">{item.customer_name}</td>
                        <td className="text-right">{formatNumber(item.recency_days)}</td>
                        <td className="text-right">{formatNumber(item.frequency)}</td>
                        <td className="text-right">{formatCurrency(item.monetary)}</td>
                        <td>
                          <span className="badge badge-info">{item.segment_label}</span>
                        </td>
                        <td className="text-xs text-muted">{item.recommended_action}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </QueryState>
        )}

        {/* ---- Scoring crédit (RF-27) ---- */}
        {tab === "credit" && (
          <QueryState query={creditQuery} errorMessage="Impossible de charger le scoring crédit.">
            {(data) => (
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
                      <tr>
                        <td colSpan={8} className="text-center text-muted">
                          Aucun score crédit disponible.
                        </td>
                      </tr>
                    )}
                    {data.items.map((item) => (
                      <tr key={item.customer_id}>
                        <td className="font-medium text-primary-dark">{item.customer_name}</td>
                        <td className="text-right">{item.score}</td>
                        <td>
                          <span className={`badge ${RISK_BADGE[item.risk_level]}`}>{item.risk_level}</span>
                        </td>
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
            )}
          </QueryState>
        )}

        {/* ---- Détection d'anomalies (RF-28) ---- */}
        {tab === "anomalies" && (
          <QueryState query={anomaliesQuery} errorMessage="Impossible de charger les anomalies.">
            {(data) => (
              <div className="overflow-x-auto">
                <table className="table-base">
                  <thead>
                    <tr>
                      <th>Référence</th>
                      <th>Caissier</th>
                      <th className="text-right">Montant total</th>
                      <th className="text-right">Remise</th>
                      <th className="text-right">Score d'anomalie</th>
                      <th>Motifs</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.items.length === 0 && (
                      <tr>
                        <td colSpan={6} className="text-center text-muted">
                          Aucune anomalie détectée.
                        </td>
                      </tr>
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
            )}
          </QueryState>
        )}

        {/* ---- Registre des modèles ML + entraînement (RF-29) ---- */}
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
                  {trainMutation.isPending && trainMutation.variables === modelType ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Brain className="h-4 w-4" />
                  )}
                  Entraîner : {MODEL_TYPE_LABELS[modelType]}
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
                Entraînement « {MODEL_TYPE_LABELS[trainMutation.data.model_type as MlModelType] ?? trainMutation.data.model_type} »
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
                        <tr>
                          <td colSpan={6} className="text-center text-muted">
                            Aucun modèle entraîné pour le moment.
                          </td>
                        </tr>
                      )}
                      {models.map((model) => (
                        <tr key={model.id}>
                          <td className="font-medium text-primary-dark">
                            {MODEL_TYPE_LABELS[model.model_type as MlModelType] ?? model.model_type}
                          </td>
                          <td>{model.version}</td>
                          <td>{model.algorithm}</td>
                          <td className="whitespace-nowrap text-xs text-muted">{formatDateTime(model.trained_at)}</td>
                          <td>
                            {model.is_active ? (
                              <span className="badge badge-success">Actif</span>
                            ) : (
                              <span className="badge badge-warning">Inactif</span>
                            )}
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

function KpiCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="card">
      <p className="text-xs text-muted">{label}</p>
      <p className="text-lg font-semibold text-primary-dark">{value}</p>
    </div>
  );
}

interface QueryStateProps<T> {
  query: {
    isLoading: boolean;
    isError: boolean;
    error: unknown;
    data: T | undefined;
  };
  errorMessage: string;
  children: (data: T) => React.ReactNode;
}

function QueryState<T>({ query, errorMessage, children }: QueryStateProps<T>) {
  if (query.isLoading) {
    return (
      <div className="flex items-center gap-2 text-muted">
        <Loader2 className="h-4 w-4 animate-spin" />
        Chargement...
      </div>
    );
  }

  if (query.isError) {
    return <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{getApiErrorMessage(query.error, errorMessage)}</div>;
  }

  if (!query.data) return null;

  return <>{children(query.data)}</>;
}
