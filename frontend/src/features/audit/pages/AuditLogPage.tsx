import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react";

import { auditApi } from "@/api/endpoints/audit";
import { getApiErrorMessage } from "@/api/client";
import { formatDateTime, formatNumber } from "@/utils/format";

const PER_PAGE = 30;

/**
 * Journal d'audit applicatif (RF-26, réservé ADMIN) : historique des
 * événements (créations, mises à jour, validations...) avec pagination
 * et filtre par type d'événement.
 * Cf. GET /api/v1/users/audit-logs.
 */
export default function AuditLogPage() {
  const [eventTypeInput, setEventTypeInput] = useState("");
  const [eventType, setEventType] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    const handle = setTimeout(() => {
      setEventType(eventTypeInput.trim().toUpperCase());
      setPage(1);
    }, 300);
    return () => clearTimeout(handle);
  }, [eventTypeInput]);

  const logsQuery = useQuery({
    queryKey: ["audit-logs", eventType, page],
    queryFn: () => auditApi.list({ event_type: eventType || undefined, page, per_page: PER_PAGE }),
  });

  const logs = logsQuery.data?.data ?? [];
  const meta = logsQuery.data?.meta;
  const totalPages = meta ? Math.max(1, Math.ceil(meta.total / meta.per_page)) : 1;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-primary-dark">Journal d'audit</h1>
        <p className="text-sm text-muted">Historique des actions réalisées dans l'application</p>
      </div>

      <div className="card space-y-4">
        <input
          type="text"
          className="input max-w-sm"
          placeholder="Filtrer par type d'événement (ex. SALE_CREATED)"
          value={eventTypeInput}
          onChange={(e) => setEventTypeInput(e.target.value)}
        />

        {logsQuery.isLoading && (
          <div className="flex items-center gap-2 text-muted">
            <Loader2 className="h-4 w-4 animate-spin" />
            Chargement...
          </div>
        )}

        {logsQuery.isError && (
          <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
            {getApiErrorMessage(logsQuery.error, "Impossible de charger le journal d'audit.")}
          </div>
        )}

        {logsQuery.isSuccess && (
          <>
            <div className="overflow-x-auto">
              <table className="table-base">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Utilisateur</th>
                    <th>Type d'événement</th>
                    <th>Entité</th>
                    <th>Description</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.length === 0 && (
                    <tr>
                      <td colSpan={5} className="text-center text-muted">
                        Aucun événement trouvé.
                      </td>
                    </tr>
                  )}
                  {logs.map((log) => (
                    <tr key={log.id}>
                      <td className="whitespace-nowrap text-xs text-muted">{formatDateTime(log.created_at)}</td>
                      <td>{log.user_name ?? "Système"}</td>
                      <td>
                        <span className="badge badge-info">{log.event_type}</span>
                      </td>
                      <td className="text-xs text-muted">
                        {log.entity_type ?? "-"}
                        {log.entity_id ? ` #${log.entity_id.slice(0, 8)}` : ""}
                      </td>
                      <td className="text-sm text-primary-dark">{log.description ?? "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {meta && (
              <div className="flex items-center justify-between border-t border-surface pt-3 text-sm text-muted">
                <span>
                  {formatNumber(meta.total)} événement{meta.total === 1 ? "" : "s"} - page {meta.page} / {totalPages}
                </span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    className="btn-secondary"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Précédent
                  </button>
                  <button
                    type="button"
                    className="btn-secondary"
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  >
                    Suivant
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
