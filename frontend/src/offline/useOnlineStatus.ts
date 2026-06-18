import { useEffect, useState } from "react";

/**
 * Détecteur de connexion (cf. docs/26-GESTION-OFFLINE-PWA.md §26.3, §26.8).
 *
 * S'appuie sur `navigator.onLine` + les événements `online`/`offline` du
 * navigateur. Sert à afficher la pastille de connexion (🟢/🟡) et à
 * déclencher la synchronisation différée au retour réseau.
 */
export function useOnlineStatus(): boolean {
  const [isOnline, setIsOnline] = useState<boolean>(
    typeof navigator !== "undefined" ? navigator.onLine : true
  );

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  return isOnline;
}
