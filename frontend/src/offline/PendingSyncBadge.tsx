import { AlertTriangle, RefreshCw } from "lucide-react";
import clsx from "clsx";

import { usePendingSyncCounts } from "@/offline/useSyncOfflineSales";

/**
 * Badge "N ventes en attente de synchronisation" + conflits (§26.8).
 * Visible vendeur (file d'attente) et admin (conflits à régulariser).
 */
export function PendingSyncBadge() {
  const { pending, conflicts } = usePendingSyncCounts();

  if (pending === 0 && conflicts === 0) return null;

  return (
    <div className="flex items-center gap-2">
      {pending > 0 && (
        <span
          className={clsx(
            "flex items-center gap-1.5 rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-700"
          )}
          title="Ventes enregistrées localement, en attente d'envoi au serveur"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          {pending} vente{pending > 1 ? "s" : ""} en attente de synchronisation
        </span>
      )}
      {conflicts > 0 && (
        <span
          className="flex items-center gap-1.5 rounded-full bg-red-100 px-3 py-1 text-xs font-medium text-red-700"
          title="Ventes synchronisées avec un conflit de stock — vérification nécessaire"
        >
          <AlertTriangle className="h-3.5 w-3.5" />
          {conflicts} vente{conflicts > 1 ? "s" : ""} en conflit
        </span>
      )}
    </div>
  );
}
