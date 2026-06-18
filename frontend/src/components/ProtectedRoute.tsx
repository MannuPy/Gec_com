import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuthStore } from "@/app/store";

/**
 * Protège les routes nécessitant une authentification.
 * Redirige vers /login en conservant l'URL d'origine (state.from).
 */
export function ProtectedRoute() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const location = useLocation();

  if (!accessToken) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  // RF-05 : changement de mot de passe obligatoire (compte créé ou
  // réinitialisé par un administrateur) -> on bloque l'accès au reste de
  // l'application jusqu'au changement.
  if (user?.must_change_password && location.pathname !== "/changer-mot-de-passe") {
    return <Navigate to="/changer-mot-de-passe" replace />;
  }

  return <Outlet />;
}

/**
 * Protège une route selon une permission RBAC donnée.
 * Affiche une page "Accès refusé" si l'utilisateur n'a pas la permission.
 */
export function RequirePermission({ permission }: { permission: string }) {
  const hasPermission = useAuthStore((s) => s.hasPermission);

  if (!hasPermission(permission)) {
    return (
      <div className="flex h-full flex-1 items-center justify-center p-8">
        <div className="card max-w-md text-center">
          <h2 className="card-title">Accès refusé</h2>
          <p className="text-sm text-muted">
            Vous n'avez pas les droits nécessaires pour accéder à cette page.
          </p>
        </div>
      </div>
    );
  }

  return <Outlet />;
}
