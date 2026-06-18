/**
 * Synchronisation automatique des ventes saisies hors-ligne (RF-20, RG-28 à
 * RG-30, cf. docs/26-GESTION-OFFLINE-PWA.md §26.5/§26.6).
 *
 * La synchronisation se déclenche automatiquement :
 *  - au retour de connexion réseau (événement `online`) ;
 *  - au focus de l'onglet (`window.focus`) ;
 *  - à intervalle régulier (1 min) pendant la session.
 *
 * Cycle :
 *  1. Récupère les ventes locales `sync_status = PENDING` ;
 *  2. Les envoie par lot à `POST /sales/sync` ;
 *  3. Met à jour `sync_status` selon la réponse du serveur :
 *     - VALIDEE / DEJA_SYNCHRONISE -> SYNCED
 *     - EN_CONFLIT                 -> CONFLICT (conflit de stock)
 *     - ERREUR / échec réseau      -> reste PENDING (nouvel essai)
 *
 * Aucune vente n'est jamais supprimée localement avant confirmation
 * explicite (`SYNCED`/`CONFLICT`) — cf. principe directeur §26.6.
 */
import { useEffect, useState } from "react";

import { salesApi } from "@/api/endpoints/sales";
import { db, type OfflineSaleSyncStatus } from "@/offline/db";
import { useOnlineStatus } from "@/offline/useOnlineStatus";

const SYNC_INTERVAL_MS = 60 * 1000; // 1 min

let syncInFlight = false;

/**
 * Envoie les ventes hors-ligne en attente au serveur. Sans effet si hors-
 * ligne, si aucune vente n'est en attente, ou si une synchronisation est déjà
 * en cours (verrou simple pour éviter les envois concurrents).
 */
export async function syncPendingSales(): Promise<void> {
  if (typeof navigator !== "undefined" && !navigator.onLine) return;
  if (syncInFlight) return;

  const pending = await db.sales.where("sync_status").equals("PENDING").toArray();
  if (pending.length === 0) return;

  syncInFlight = true;

  try {
    await db.sales
      .where("sync_status")
      .equals("PENDING")
      .modify({ sync_status: "SYNCING" as OfflineSaleSyncStatus });

    const payload = pending.map((sale) => ({
      offline_uuid: sale.offline_uuid,
      branch_id: sale.branch_id,
      customer_id: sale.customer_id,
      payment_type: sale.payment_type,
      discount_rate: sale.discount_rate,
      created_at_local: sale.created_at_local,
      lines: sale.lines.map((line) => ({
        product_id: line.product_id,
        quantity: line.quantity,
      })),
    }));

    const { results } = await salesApi.sync(payload);

    for (const result of results) {
      let syncStatus: OfflineSaleSyncStatus;
      switch (result.status) {
        case "VALIDEE":
        case "DEJA_SYNCHRONISE":
          syncStatus = "SYNCED";
          break;
        case "EN_CONFLIT":
          syncStatus = "CONFLICT";
          break;
        default:
          // ERREUR ou statut inconnu : on retentera plus tard.
          syncStatus = "PENDING";
      }

      await db.sales.update(result.offline_uuid, {
        sync_status: syncStatus,
        sync_message: result.message ?? null,
        server_sale_id: result.sale_id ?? null,
      });
    }
  } catch {
    // Échec réseau global pendant l'envoi : on remet les ventes en attente
    // pour qu'elles soient retentées au prochain cycle / retour réseau.
    await db.sales
      .where("sync_status")
      .equals("SYNCING")
      .modify({ sync_status: "PENDING" as OfflineSaleSyncStatus });
  } finally {
    syncInFlight = false;
  }
}

/**
 * Déclenche la synchronisation automatiquement au retour réseau, au focus
 * de l'application et à intervalle régulier (§26.3/§26.5).
 */
export function useSyncOfflineSales(): void {
  const isOnline = useOnlineStatus();

  useEffect(() => {
    if (!isOnline) return;

    void syncPendingSales();

    const interval = setInterval(() => {
      void syncPendingSales();
    }, SYNC_INTERVAL_MS);

    const handleFocus = () => {
      void syncPendingSales();
    };
    window.addEventListener("focus", handleFocus);

    return () => {
      clearInterval(interval);
      window.removeEventListener("focus", handleFocus);
    };
  }, [isOnline]);
}

export interface PendingSyncCounts {
  /** Ventes en attente d'envoi ou en cours d'envoi. */
  pending: number;
  /** Ventes synchronisées mais en conflit de stock (§26.6/§26.8). */
  conflicts: number;
}

/**
 * Compte les ventes locales en attente de synchronisation et en conflit,
 * pour affichage des badges/bannières (§26.8).
 */
export function usePendingSyncCounts(): PendingSyncCounts {
  const [counts, setCounts] = useState<PendingSyncCounts>({ pending: 0, conflicts: 0 });

  useEffect(() => {
    let cancelled = false;

    const update = async () => {
      const [pending, syncing, conflicts] = await Promise.all([
        db.sales.where("sync_status").equals("PENDING").count(),
        db.sales.where("sync_status").equals("SYNCING").count(),
        db.sales.where("sync_status").equals("CONFLICT").count(),
      ]);
      if (!cancelled) setCounts({ pending: pending + syncing, conflicts });
    };

    void update();
    const interval = setInterval(update, 5000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return counts;
}
