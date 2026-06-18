import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  ArrowLeftRight,
  BrainCircuit,
  ClipboardList,
  LayoutDashboard,
  LogOut,
  Menu,
  Package,
  Receipt,
  ScrollText,
  ShoppingCart,
  Store,
  Truck,
  UserCog,
  Users,
  Warehouse,
  X,
} from "lucide-react";
import clsx from "clsx";

import { useAuthStore } from "@/app/store";
import { authApi } from "@/api/endpoints/auth";
import { ConnectionBadge } from "@/offline/ConnectionBadge";
import { PendingSyncBadge } from "@/offline/PendingSyncBadge";
import { useSyncOfflineSales } from "@/offline/useSyncOfflineSales";

interface NavItem {
  to: string;
  label: string;
  icon: typeof LayoutDashboard;
  permission?: string;
}

const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Tableau de bord", icon: LayoutDashboard, permission: "reports:read" },
  { to: "/produits", label: "Produits", icon: Package, permission: "products:read" },
  { to: "/caisse", label: "Caisse", icon: ShoppingCart, permission: "sales:create" },
  { to: "/ventes", label: "Historique des ventes", icon: Receipt, permission: "sales:read" },
  { to: "/clients", label: "Clients", icon: Users, permission: "customers:read" },
  { to: "/stock", label: "Stock", icon: Warehouse, permission: "stock:read" },
  { to: "/inventaire", label: "Inventaire physique", icon: ClipboardList, permission: "inventory:read" },
  { to: "/fournisseurs", label: "Fournisseurs", icon: Truck, permission: "suppliers:read" },
  { to: "/transferts", label: "Transferts", icon: ArrowLeftRight, permission: "transfers:read" },
  { to: "/analytique", label: "Analytique & IA", icon: BrainCircuit, permission: "analytics:read" },
  { to: "/utilisateurs", label: "Utilisateurs", icon: UserCog, permission: "users:read" },
  { to: "/audit", label: "Journal d'audit", icon: ScrollText, permission: "users:read" },
];

/**
 * Layout principal — sidebar responsive :
 * - Mobile (<lg) : tiroir (drawer) ouvert via bouton hamburger, overlay cliquable pour fermer.
 * - Desktop (≥lg) : sidebar fixe w-64 toujours visible.
 *
 * Couleurs : palette Adobe Color (#011140 sidebar, #0439D9 actif, #F2F2F2 fond).
 */
export function AppLayout() {
  const user = useAuthStore((s) => s.user);
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const clearSession = useAuthStore((s) => s.clearSession);
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const visibleItems = NAV_ITEMS.filter((item) => !item.permission || hasPermission(item.permission));

  // Synchronisation différée des ventes hors-ligne (RF-20, §26.5/§26.6).
  useSyncOfflineSales();

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch {
      // Le logout échoue silencieusement si le token est déjà invalide.
    } finally {
      clearSession();
      navigate("/login", { replace: true });
    }
  };

  const closeSidebar = () => setSidebarOpen(false);

  return (
    <div className="flex h-screen bg-surface text-primary-dark">

      {/* ── Overlay mobile (fond semi-transparent) ───────────────────── */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/50 lg:hidden"
          onClick={closeSidebar}
          aria-hidden="true"
        />
      )}

      {/* ── Sidebar ──────────────────────────────────────────────────── */}
      <aside
        className={clsx(
          // Base : position fixe sur mobile (drawer), statique sur desktop
          "fixed inset-y-0 left-0 z-30 flex w-64 flex-col bg-primary-dark text-white",
          "transition-transform duration-300 ease-in-out",
          // Mobile : caché par défaut, slide-in quand ouvert
          sidebarOpen ? "translate-x-0" : "-translate-x-full",
          // Desktop (≥lg) : toujours visible, position dans le flux
          "lg:relative lg:translate-x-0",
        )}
      >
        {/* Logo + bouton fermeture (mobile seulement) */}
        <div className="flex items-center justify-between px-5 py-5">
          <div className="flex items-center gap-2">
            <Store className="h-6 w-6 text-primary-light" />
            <span className="text-lg font-semibold tracking-tight">GesCom-BF</span>
          </div>
          <button
            type="button"
            onClick={closeSidebar}
            className="rounded-lg p-1 text-white/60 hover:bg-white/10 hover:text-white lg:hidden"
            aria-label="Fermer le menu"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="mt-2 flex-1 space-y-1 overflow-y-auto px-3">
          {visibleItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              onClick={closeSidebar}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-white"
                    : "text-white/70 hover:bg-white/10 hover:text-white",
                )
              }
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span className="truncate">{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-white/10 px-6 py-4 text-xs text-white/50">
          GesCom-BF &middot; V1
        </div>
      </aside>

      {/* ── Zone de contenu ──────────────────────────────────────────── */}
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">

        {/* Topbar */}
        <header className="flex items-center justify-between border-b border-muted/20 bg-white px-4 py-3 md:px-6">
          {/* Bouton hamburger (mobile) + infos site */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              className="rounded-lg p-2 text-primary-dark hover:bg-surface lg:hidden"
              aria-label="Ouvrir le menu"
            >
              <Menu className="h-5 w-5" />
            </button>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-primary-dark">
                {user?.branch_name ?? "Tous les sites"}
              </p>
              <p className="text-xs text-muted">{roleLabel(user?.role)}</p>
            </div>
          </div>

          {/* Badges + infos utilisateur + déconnexion */}
          <div className="flex items-center gap-2 md:gap-4">
            <PendingSyncBadge />
            <ConnectionBadge />
            {/* Infos utilisateur : masquées sur très petits écrans */}
            <div className="hidden text-right sm:block">
              <p className="text-sm font-medium text-primary-dark">{user?.full_name}</p>
              <p className="text-xs text-muted">{user?.email}</p>
            </div>
            <button
              type="button"
              onClick={handleLogout}
              className="btn-ghost"
              title="Se déconnecter"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </header>

        {/* Contenu principal */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

function roleLabel(role?: string | null) {
  switch (role) {
    case "ADMIN":       return "Administrateur";
    case "MAGASINIER":  return "Magasinier";
    case "VENDEUR":     return "Vendeur";
    default:            return role ?? "";
  }
}
