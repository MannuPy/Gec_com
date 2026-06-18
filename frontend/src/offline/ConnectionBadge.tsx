import { Wifi, WifiOff } from "lucide-react";
import clsx from "clsx";

import { useOnlineStatus } from "@/offline/useOnlineStatus";

/**
 * Pastille de connexion (cf. docs/26-GESTION-OFFLINE-PWA.md §26.8) :
 * - 🟢 En ligne : stock et prix garantis à jour ;
 * - 🟡 Hors-ligne : ventes enregistrées localement, synchronisées plus tard.
 */
export function ConnectionBadge() {
  const isOnline = useOnlineStatus();

  return (
    <span
      className={clsx(
        "flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium",
        isOnline ? "bg-green-100 text-green-700" : "bg-amber-100 text-amber-700"
      )}
      title={
        isOnline
          ? "Connexion active — stock et prix à jour"
          : "Hors-ligne — les ventes seront synchronisées au retour du réseau"
      }
    >
      {isOnline ? <Wifi className="h-3.5 w-3.5" /> : <WifiOff className="h-3.5 w-3.5" />}
      {isOnline ? "En ligne" : "Hors-ligne"}
    </span>
  );
}
