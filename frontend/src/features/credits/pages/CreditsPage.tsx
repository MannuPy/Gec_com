/**
 * Page Suivi des crédits — GesCom-BF
 *
 * KPIs + filtres + graphiques + tableau clients débiteurs
 * Actions : Réduire le crédit (paiement partiel) / Solder (paiement total)
 * Exports : Excel + PDF imprimable
 * Historique : SOLDÉ / EN COURS / NON COMMENCÉ
 */
import { useState, useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  CreditCard,
  Download,
  FileText,
  Filter,
  Search,
  Users,
  AlertTriangle,
  CheckCircle2,
  X,
  History,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { useCredits, useSettleCredit, useExportCreditsExcel, useExportCreditsPdf, useCreditHistory } from "../hooks/useCredits";
import { productsApi } from "@/api/endpoints/products";
import { useQuery } from "@tanstack/react-query";
import type { Customer } from "@/types/customer";
import type { CreditHistoryItem, CreditHistoryStatus } from "@/types/customer";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmt(v: string | number) {
  const n = typeof v === "string" ? parseFloat(v) : v;
  if (isNaN(n)) return "0";
  return n.toLocaleString("fr-FR") + " FCFA";
}

function riskLevel(customer: Customer): "FAIBLE" | "MOYEN" | "ÉLEVÉ" {
  const balance = parseFloat(customer.credit_balance);
  const limit = parseFloat(customer.credit_limit);
  if (limit <= 0) return "MOYEN";
  const pct = balance / limit;
  if (pct > 1) return "ÉLEVÉ";
  if (pct > 0.7) return "MOYEN";
  return "FAIBLE";
}

const RISK_COLORS: Record<string, string> = {
  FAIBLE: "#22c55e",
  MOYEN: "#f59e0b",
  ÉLEVÉ: "#ef4444",
};

const CREDIT_STATUS_LABELS: Record<CreditHistoryStatus, string> = {
  SOLDE: "Soldé",
  EN_COURS: "En cours",
  NON_COMMENCE: "Non commencé",
};

const CREDIT_STATUS_COLORS: Record<CreditHistoryStatus, string> = {
  SOLDE: "#22c55e",
  EN_COURS: "#f59e0b",
  NON_COMMENCE: "#ef4444",
};

const PAYMENT_STATUS_LABELS: Record<string, string> = {
  PAID: "Payé",
  PENDING: "En attente",
  LATE: "En retard",
  CANCELLED: "Annulé",
};

const PAYMENT_STATUS_COLORS: Record<string, string> = {
  PAID: "#22c55e",
  PENDING: "#f59e0b",
  LATE: "#ef4444",
  CANCELLED: "#94a3b8",
};

// ---------------------------------------------------------------------------
// Modal historique crédit
// ---------------------------------------------------------------------------

interface CreditHistoryModalProps {
  onClose: () => void;
}

function CreditHistoryModal({ onClose }: CreditHistoryModalProps) {
  const [statusFilter, setStatusFilter] = useState<CreditHistoryStatus | "">("");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const { data: history = [], isLoading } = useCreditHistory(
    statusFilter ? { credit_status: statusFilter } : {}
  );

  function fmtDate(iso: string) {
    return new Date(iso).toLocaleDateString("fr-FR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 p-4 pt-16 overflow-y-auto">
      <div className="w-full max-w-3xl rounded-xl bg-white shadow-2xl">
        {/* En-tête */}
        <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
          <div className="flex items-center gap-2">
            <History className="h-5 w-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">Historique des crédits</h2>
          </div>
          <button onClick={onClose} className="rounded-lg p-1 text-gray-400 hover:bg-gray-100">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Filtres statut */}
        <div className="flex flex-wrap gap-2 border-b border-gray-100 px-6 py-3">
          {(["", "SOLDE", "EN_COURS", "NON_COMMENCE"] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s as CreditHistoryStatus | "")}
              className={[
                "rounded-full px-3 py-1 text-xs font-medium transition-colors",
                statusFilter === s
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200",
              ].join(" ")}
            >
              {s === "" ? "Tous" : CREDIT_STATUS_LABELS[s as CreditHistoryStatus]}
            </button>
          ))}
        </div>

        {/* Liste */}
        <div className="max-h-[60vh] overflow-y-auto px-4 py-3">
          {isLoading ? (
            <div className="py-8 text-center text-sm text-gray-400">Chargement...</div>
          ) : history.length === 0 ? (
            <div className="py-8 text-center text-sm text-gray-400">
              Aucun historique de crédit trouvé.
            </div>
          ) : (
            <div className="space-y-2">
              {history.map((item: CreditHistoryItem) => {
                const expanded = expandedId === item.customer_id;
                return (
                  <div
                    key={item.customer_id}
                    className="rounded-lg border border-gray-200 bg-gray-50"
                  >
                    <div
                      className="flex cursor-pointer flex-wrap items-center justify-between gap-3 p-3"
                      onClick={() => setExpandedId(expanded ? null : item.customer_id)}
                    >
                      <div>
                        <p className="font-medium text-gray-900">{item.customer_name}</p>
                        {item.customer_phone && (
                          <p className="text-xs text-gray-400">{item.customer_phone}</p>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-3">
                        <span
                          className="rounded-full px-2.5 py-0.5 text-xs font-semibold"
                          style={{
                            background: CREDIT_STATUS_COLORS[item.credit_status] + "22",
                            color: CREDIT_STATUS_COLORS[item.credit_status],
                          }}
                        >
                          {CREDIT_STATUS_LABELS[item.credit_status]}
                        </span>
                        <div className="text-right">
                          <p className="text-xs text-gray-500">Encours</p>
                          <p className="text-sm font-bold text-gray-900">
                            {parseFloat(item.credit_balance).toLocaleString("fr-FR")} FCFA
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-gray-500">Payé</p>
                          <p className="text-sm font-semibold text-green-600">
                            {parseFloat(item.total_paid_amount).toLocaleString("fr-FR")} FCFA
                          </p>
                        </div>
                        <div className="flex items-center gap-1 text-xs text-gray-400">
                          {item.paid_payments}/{item.total_payments} échéances
                          {expanded ? (
                            <ChevronUp className="h-3.5 w-3.5" />
                          ) : (
                            <ChevronDown className="h-3.5 w-3.5" />
                          )}
                        </div>
                      </div>
                    </div>

                    {expanded && (
                      <div className="border-t border-gray-200 px-3 pb-3 pt-2">
                        {item.payments.length === 0 ? (
                          <p className="text-xs text-gray-400 italic">Aucun paiement enregistré.</p>
                        ) : (
                          <table className="w-full text-xs">
                            <thead className="text-gray-500">
                              <tr>
                                <th className="pb-1 text-left">Référence vente</th>
                                <th className="pb-1 text-right">Montant</th>
                                <th className="pb-1 text-center">Échéance</th>
                                <th className="pb-1 text-center">Payé le</th>
                                <th className="pb-1 text-center">Statut</th>
                                <th className="pb-1 text-left">Note</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                              {item.payments.map((p) => (
                                <tr key={p.id}>
                                  <td className="py-1 text-gray-600">
                                    {p.sale_reference ?? "—"}
                                  </td>
                                  <td className="py-1 text-right font-medium text-gray-900">
                                    {parseFloat(p.amount).toLocaleString("fr-FR")}
                                  </td>
                                  <td className="py-1 text-center text-gray-500">
                                    {fmtDate(p.due_date)}
                                  </td>
                                  <td className="py-1 text-center text-gray-500">
                                    {p.paid_date ? fmtDate(p.paid_date) : "—"}
                                  </td>
                                  <td className="py-1 text-center">
                                    <span
                                      className="rounded-full px-2 py-0.5 font-medium"
                                      style={{
                                        background:
                                          (PAYMENT_STATUS_COLORS[p.status] ?? "#94a3b8") + "22",
                                        color: PAYMENT_STATUS_COLORS[p.status] ?? "#94a3b8",
                                      }}
                                    >
                                      {PAYMENT_STATUS_LABELS[p.status] ?? p.status}
                                    </span>
                                  </td>
                                  <td className="py-1 text-gray-500">{p.note ?? "—"}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        )}
                        {item.total_payments > 10 && (
                          <p className="mt-1 text-xs text-gray-400 italic">
                            Affiche les 10 derniers paiements sur {item.total_payments}.
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="border-t border-gray-100 px-6 py-3 text-right">
          <button
            onClick={onClose}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Fermer
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Modal paiement
// ---------------------------------------------------------------------------

interface SettleModalProps {
  customer: Customer;
  mode: "partial" | "full";
  onClose: () => void;
  onConfirm: (amount: number, note: string) => void;
  isPending: boolean;
}

function SettleModal({ customer, mode, onClose, onConfirm, isPending }: SettleModalProps) {
  const maxAmount = parseFloat(customer.credit_balance);
  const [amount, setAmount] = useState(mode === "full" ? maxAmount : 0);
  const [note, setNote] = useState("");
  const [error, setError] = useState("");

  function handleSubmit() {
    if (amount <= 0) { setError("Le montant doit être positif."); return; }
    if (amount > maxAmount) { setError(`Maximum : ${maxAmount.toLocaleString("fr-FR")} FCFA`); return; }
    onConfirm(amount, note);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">
            {mode === "full" ? "Solder le crédit" : "Réduire le crédit"}
          </h2>
          <button onClick={onClose} className="rounded-lg p-1 text-gray-400 hover:bg-gray-100">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="mb-4 rounded-lg bg-blue-50 p-3">
          <p className="text-sm font-medium text-blue-900">{customer.full_name}</p>
          <p className="text-xs text-blue-700">
            Encours actuel : <span className="font-bold">{fmt(customer.credit_balance)}</span>
          </p>
        </div>

        <div className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Montant à encaisser (FCFA)
            </label>
            <input
              type="number"
              min={1}
              max={maxAmount}
              value={amount}
              onChange={(e) => { setAmount(parseFloat(e.target.value) || 0); setError(""); }}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              disabled={mode === "full"}
            />
            {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
          </div>

          {mode === "partial" && (
            <p className="text-xs text-gray-500">
              Encours restant après paiement :{" "}
              <span className="font-medium text-gray-700">
                {(maxAmount - amount).toLocaleString("fr-FR")} FCFA
              </span>
            </p>
          )}

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Note (optionnel)
            </label>
            <input
              type="text"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Ex. : Versement espèces, chèque n°..."
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            />
          </div>
        </div>

        <div className="mt-6 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Annuler
          </button>
          <button
            onClick={handleSubmit}
            disabled={isPending}
            className="flex-1 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {isPending ? "Traitement..." : "Confirmer"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page principale
// ---------------------------------------------------------------------------

export default function CreditsPage() {
  const [branchId, setBranchId] = useState("");
  const [customerType, setCustomerType] = useState("");
  const [search, setSearch] = useState("");
  const [modal, setModal] = useState<{ customer: Customer; mode: "partial" | "full" } | null>(null);
  const [showHistory, setShowHistory] = useState(false);

  const { data: customers = [], isLoading } = useCredits({
    branch_id: branchId || undefined,
    customer_type: (customerType as "SIMPLE" | "TECHNICIEN") || undefined,
  });

  const branchesQuery = useQuery({
    queryKey: ["branches"],
    queryFn: productsApi.branches,
  });

  const settle = useSettleCredit();
  const exportXlsx = useExportCreditsExcel();
  const exportPdf = useExportCreditsPdf(branchId || undefined);

  // ---- Filtres locaux ----
  const filtered = useMemo(() => {
    if (!search) return customers;
    const q = search.toLowerCase();
    return customers.filter(
      (c) => c.full_name.toLowerCase().includes(q) || (c.phone ?? "").includes(q)
    );
  }, [customers, search]);

  // ---- KPIs ----
  const totalEncours = filtered.reduce((s, c) => s + parseFloat(c.credit_balance), 0);
  const nbClients = filtered.length;
  const nbEleve = filtered.filter((c) => riskLevel(c) === "ÉLEVÉ").length;
  const nbSolde = filtered.filter((c) => parseFloat(c.credit_balance) <= 0).length;

  // ---- Données graphiques ----
  const top10 = [...filtered]
    .sort((a, b) => parseFloat(b.credit_balance) - parseFloat(a.credit_balance))
    .slice(0, 10)
    .map((c) => ({ name: c.full_name.split(" ")[0], encours: parseFloat(c.credit_balance) }));

  const riskDistrib = [
    { name: "FAIBLE", value: filtered.filter((c) => riskLevel(c) === "FAIBLE").length },
    { name: "MOYEN", value: filtered.filter((c) => riskLevel(c) === "MOYEN").length },
    { name: "ÉLEVÉ", value: filtered.filter((c) => riskLevel(c) === "ÉLEVÉ").length },
  ].filter((d) => d.value > 0);

  function handleSettle(amount: number, note: string) {
    if (!modal) return;
    settle.mutate(
      { customerId: modal.customer.id, payload: { amount: String(amount), note: note || undefined } },
      { onSuccess: () => setModal(null) }
    );
  }

  return (
    <div className="space-y-6">
      {/* ---- En-tête ---- */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Suivi des crédits</h1>
          <p className="text-sm text-gray-500">Encours clients · paiements partiels et soldages</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setShowHistory(true)}
            className="flex items-center gap-2 rounded-lg border border-purple-300 bg-purple-50 px-3 py-2 text-sm font-medium text-purple-700 hover:bg-purple-100"
          >
            <History className="h-4 w-4" />
            Historique
          </button>
          <button
            onClick={() => exportXlsx.mutate()}
            disabled={exportXlsx.isPending}
            className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            <Download className="h-4 w-4" />
            {exportXlsx.isPending ? "Export..." : "Excel"}
          </button>
          <button
            onClick={() => exportPdf.mutate()}
            disabled={exportPdf.isPending}
            className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            <FileText className="h-4 w-4" />
            {exportPdf.isPending ? "Export..." : "PDF relance"}
          </button>
        </div>
      </div>

      {/* ---- KPI cards ---- */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-200">
          <div className="flex items-center gap-2 text-gray-500">
            <CreditCard className="h-4 w-4" />
            <span className="text-xs font-medium">Encours total</span>
          </div>
          <p className="mt-2 text-xl font-bold text-gray-900">{totalEncours.toLocaleString("fr-FR")}</p>
          <p className="text-xs text-gray-400">FCFA</p>
        </div>
        <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-200">
          <div className="flex items-center gap-2 text-gray-500">
            <Users className="h-4 w-4" />
            <span className="text-xs font-medium">Clients débiteurs</span>
          </div>
          <p className="mt-2 text-xl font-bold text-gray-900">{nbClients}</p>
          <p className="text-xs text-gray-400">clients avec encours</p>
        </div>
        <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-200">
          <div className="flex items-center gap-2 text-red-500">
            <AlertTriangle className="h-4 w-4" />
            <span className="text-xs font-medium">Risque ÉLEVÉ</span>
          </div>
          <p className="mt-2 text-xl font-bold text-red-600">{nbEleve}</p>
          <p className="text-xs text-gray-400">limite dépassée</p>
        </div>
        <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-200">
          <div className="flex items-center gap-2 text-green-500">
            <CheckCircle2 className="h-4 w-4" />
            <span className="text-xs font-medium">Soldés ce mois</span>
          </div>
          <p className="mt-2 text-xl font-bold text-green-600">{nbSolde}</p>
          <p className="text-xs text-gray-400">crédits clôturés</p>
        </div>
      </div>

      {/* ---- Filtres ---- */}
      <div className="flex flex-wrap items-center gap-3 rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-200">
        <Filter className="h-4 w-4 text-gray-400 shrink-0" />
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Rechercher un client..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="rounded-lg border border-gray-300 pl-8 pr-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>
        <select
          value={customerType}
          onChange={(e) => setCustomerType(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
        >
          <option value="">Tous types</option>
          <option value="SIMPLE">Simple</option>
          <option value="TECHNICIEN">Technicien</option>
        </select>
        <select
          value={branchId}
          onChange={(e) => setBranchId(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
        >
          <option value="">Tous les sites</option>
          {(branchesQuery.data ?? []).map((branch) => (
            <option key={branch.id} value={branch.id}>{branch.name}</option>
          ))}
        </select>
        {(branchId || customerType || search) && (
          <button
            onClick={() => { setBranchId(""); setCustomerType(""); setSearch(""); }}
            className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700"
          >
            <X className="h-3.5 w-3.5" /> Réinitialiser
          </button>
        )}
      </div>

      {/* ---- Graphiques ---- */}
      {filtered.length > 0 && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-200">
            <h3 className="mb-4 text-sm font-semibold text-gray-700">Top 10 débiteurs (FCFA)</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={top10} layout="vertical" margin={{ left: 60, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 10 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={60} />
                <Tooltip formatter={(v) => [`${(v as number).toLocaleString("fr-FR")} FCFA`, "Encours"]} />
                <Bar dataKey="encours" fill="#0439D9" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-200">
            <h3 className="mb-4 text-sm font-semibold text-gray-700">Répartition du risque crédit</h3>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={riskDistrib}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={({ name, percent }: { name?: string; percent?: number }) =>
                    `${name ?? ""} ${((percent ?? 0) * 100).toFixed(0)} %`
                  }
                >
                  {riskDistrib.map((entry) => (
                    <Cell key={entry.name} fill={RISK_COLORS[entry.name] ?? "#94a3b8"} />
                  ))}
                </Pie>
                <Legend />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* ---- Tableau clients ---- */}
      <div className="rounded-xl bg-white shadow-sm ring-1 ring-gray-200">
        <div className="border-b border-gray-100 px-4 py-3">
          <h3 className="text-sm font-semibold text-gray-700">
            Clients débiteurs ({filtered.length})
          </h3>
        </div>
        {isLoading ? (
          <div className="p-8 text-center text-sm text-gray-400">Chargement...</div>
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center text-sm text-gray-400">
            Aucun client avec un encours crédit actif.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-xs text-gray-500">
                <tr>
                  <th className="px-4 py-3 text-left">Client</th>
                  <th className="px-4 py-3 text-left">Type</th>
                  <th className="px-4 py-3 text-right">Encours</th>
                  <th className="px-4 py-3 text-right">Limite</th>
                  <th className="px-4 py-3 text-center">Risque</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.map((c) => {
                  const risk = riskLevel(c);
                  const balance = parseFloat(c.credit_balance);
                  const limit = parseFloat(c.credit_limit);
                  return (
                    <tr key={c.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <p className="font-medium text-gray-900">{c.full_name}</p>
                        {c.phone && <p className="text-xs text-gray-400">{c.phone}</p>}
                      </td>
                      <td className="px-4 py-3">
                        <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                          {c.customer_type}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right font-semibold text-gray-900">
                        {balance.toLocaleString("fr-FR")}
                      </td>
                      <td className="px-4 py-3 text-right text-gray-500">
                        {limit > 0 ? limit.toLocaleString("fr-FR") : "—"}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className="rounded-full px-2 py-0.5 text-xs font-medium"
                          style={{
                            background: RISK_COLORS[risk] + "22",
                            color: RISK_COLORS[risk],
                          }}
                        >
                          {risk}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => setModal({ customer: c, mode: "partial" })}
                            className="rounded-lg border border-blue-300 bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700 hover:bg-blue-100"
                          >
                            Réduire
                          </button>
                          <button
                            onClick={() => setModal({ customer: c, mode: "full" })}
                            className="rounded-lg border border-green-300 bg-green-50 px-2.5 py-1 text-xs font-medium text-green-700 hover:bg-green-100"
                          >
                            Solder
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ---- Modal paiement ---- */}
      {modal && (
        <SettleModal
          customer={modal.customer}
          mode={modal.mode}
          onClose={() => setModal(null)}
          onConfirm={handleSettle}
          isPending={settle.isPending}
        />
      )}

      {/* ---- Modal historique ---- */}
      {showHistory && <CreditHistoryModal onClose={() => setShowHistory(false)} />}
    </div>
  );
}
