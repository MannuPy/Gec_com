import { useEffect, useRef, useState } from "react";

import { reportsApi } from "@/api/endpoints/reports";
import { useAuthStore } from "@/app/store";
import type { DashboardRealtime } from "@/types/dashboard";

const POLL_INTERVAL_MS = 15_000;
const RECONNECT_DELAY_MS = 5_000;

interface DashboardStreamState {
  data: DashboardRealtime | null;
  isLoading: boolean;
  isLive: boolean;
  error: string | null;
}

/**
 * Tableau de bord temps reel (RF-24/RF-25/RF-26/RF-28, doc
 * 22-DASHBOARD-BI.md §22.2/§22.5 - adapte en SSE/polling, cf. decision
 * projet : pas de WebSocket/Redis).
 *
 * Consomme `GET /reports/dashboard/stream` (Server-Sent Events) via
 * `fetch` + `ReadableStream`, car `EventSource` ne permet pas d'envoyer
 * l'en-tete `Authorization: Bearer <token>` requis par l'API (JWT, RG-36).
 *
 * En cas d'echec (navigateur sans support du streaming, proxy bloquant le
 * SSE, etc.), bascule automatiquement sur du polling via
 * `GET /reports/dashboard/realtime` toutes les `POLL_INTERVAL_MS`.
 */
export function useDashboardStream(branchId?: string | null): DashboardStreamState {
  const accessToken = useAuthStore((s) => s.accessToken);

  const [data, setData] = useState<DashboardRealtime | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLive, setIsLive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Evite de demarrer plusieurs flux/polls concurrents lors des re-renders.
  const activeRef = useRef(false);
  // Reflete `isLive` de facon synchrone pour la boucle de polling (le
  // polling ne sert que de repli quand le flux SSE n'est pas actif).
  const isLiveRef = useRef(false);

  useEffect(() => {
    if (!accessToken) {
      return;
    }

    activeRef.current = true;
    isLiveRef.current = false;
    let abortController: AbortController | null = null;
    let pollTimer: ReturnType<typeof setTimeout> | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    const applyPayload = (payload: DashboardRealtime, live: boolean) => {
      if (!activeRef.current) return;
      setData(payload);
      setIsLoading(false);
      setIsLive(live);
      isLiveRef.current = live;
      setError(null);
    };

    const poll = async () => {
      while (activeRef.current) {
        await new Promise((resolve) => {
          pollTimer = setTimeout(resolve, POLL_INTERVAL_MS);
        });
        if (!activeRef.current || isLiveRef.current) continue;
        try {
          const payload = await reportsApi.realtime(branchId);
          applyPayload(payload, false);
        } catch {
          if (activeRef.current) {
            setIsLoading(false);
            setError("Impossible de charger les indicateurs temps reel.");
          }
        }
      }
    };

    const connectStream = async () => {
      abortController = new AbortController();
      try {
        const response = await fetch(reportsApi.realtimeStreamUrl(branchId), {
          headers: { Authorization: `Bearer ${accessToken}` },
          signal: abortController.signal,
        });

        if (!response.ok || !response.body) {
          throw new Error(`SSE indisponible (HTTP ${response.status})`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        // Detecte si le serveur a envoye `sse-disabled` (mode DISABLE_SSE=true,
        // ex. PythonAnywhere/uWSGI mono-worker). Dans ce cas on attend
        // POLL_INTERVAL_MS avant de se reconnecter pour eviter une boucle rapide.
        let sseDisabled = false;

        while (activeRef.current) {
          const { value, done } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const events = buffer.split("\n\n");
          buffer = events.pop() ?? "";

          for (const rawEvent of events) {
            const lines = rawEvent.split("\n");
            const eventLine = lines.find((line) => line.startsWith("event: "));
            const dataLine = lines.find((line) => line.startsWith("data: "));

            const eventType = eventLine ? eventLine.slice("event: ".length).trim() : "message";

            if (eventType === "sse-disabled") {
              // Backend en mode mono-shot : fermeture immediate apres 1 snapshot.
              // Basculer sur polling pur et attendre avant de ré-essayer le SSE.
              sseDisabled = true;
              setIsLive(false);
              isLiveRef.current = false;
              break;
            }

            if (!dataLine) continue;

            try {
              const payload = JSON.parse(dataLine.slice("data: ".length)) as DashboardRealtime;
              applyPayload(payload, true);
            } catch {
              // Evenement non-JSON (commentaire de heartbeat) : on l'ignore.
            }
          }

          if (sseDisabled) break;
        }

        // Le flux se termine normalement (DASHBOARD_STREAM_MAX_EVENTS atteint)
        // ou via sse-disabled (mode DISABLE_SSE=true).
        if (activeRef.current) {
          if (sseDisabled) {
            // Attendre POLL_INTERVAL_MS pour eviter une boucle de connexions
            // rapides : le backend se fermera a nouveau immediatement.
            reconnectTimer = setTimeout(() => {
              if (activeRef.current) connectStream();
            }, POLL_INTERVAL_MS);
          } else {
            // Flux SSE complet clos normalement : reconnexion directe.
            connectStream();
          }
        }
      } catch {
        if (!activeRef.current) return;
        // Repli sur le polling, puis nouvelle tentative SSE plus tard.
        setIsLive(false);
        isLiveRef.current = false;
        reconnectTimer = setTimeout(() => {
          if (activeRef.current) connectStream();
        }, RECONNECT_DELAY_MS);
      }
    };

    // Chargement initial immediat (snapshot), puis flux temps reel avec
    // repli polling en cas d'echec.
    reportsApi
      .realtime(branchId)
      .then((payload) => applyPayload(payload, false))
      .catch(() => setIsLoading(false))
      .finally(() => {
        connectStream();
        poll();
      });

    return () => {
      activeRef.current = false;
      abortController?.abort();
      if (pollTimer) clearTimeout(pollTimer);
      if (reconnectTimer) clearTimeout(reconnectTimer);
    };
  }, [accessToken, branchId]);

  return { data, isLoading, isLive, error };
}
