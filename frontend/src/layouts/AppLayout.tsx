import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  ArrowLeftRight,
  BarChart2,
  BookOpen,
  BrainCircuit,
  ClipboardList,
  CreditCard,
  LayoutDashboard,
  LogOut,
  Menu,
  Package,
  Receipt,
  RotateCcw,
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
  { to: "/mon-tableau-de-bord", label: "Ma performance", icon: BarChart2, permission: "sales:create" },
  { to: "/ventes", label: "Historique des ventes", icon: Receipt, permission: "sales:read" },
  { to: "/clients", label: "Clients", icon: Users, permission: "customers:read" },
  { to: "/stock", label: "Stock", icon: Warehouse, permission: "stock:read" },
  { to: "/inventaire", label: "Inventaire physique", icon: ClipboardList, permission: "inventory:read" },
  { to: "/fournisseurs", label: "Fournisseurs", icon: Truck, permission: "suppliers:read" },
  { to: "/transferts", label: "Transferts", icon: ArrowLeftRight, permission: "transfers:read" },
  { to: "/credits", label: "Credits clients", icon: CreditCard, permission: "customers:read" },
  { to: "/retours", label: "Retours produits", icon: RotateCcw, permission: "sales:read" },
  { to: "/comptabilite", label: "Comptabilite", icon: BookOpen, permission: "reports:read" },
  { to: "/analytique", label: "Analytique & IA", icon: BrainCircuit, permission: "analytics:read" },
  { to: "/utilisateurs", label: "Utilisateurs", icon: UserCog, permission: "users:read" },
  { to: "/audit", label: "Journal d'audit", icon: ScrollText, permission: "users:read" },
];

export function AppLayout() {
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const clearSession = useAuthStore((s) => s.clearSession);
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const visibleItems = NAV_ITEMS.filter((item) => !item.permission || hasPermission(item.permission));

  useSyncOfflineSales();

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch {
      // silencieux si token invalide
    } finally {
      clearSession();
      navigate("/login", { replace: true });
    }
  };

  const closeSidebar = () => setSidebarOpen(false);

  return (
    <div className="flex h-screen bg-surface text-primary-dark">
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/50 lg:hidden"
          onClick={closeSidebar}
          aria-hidden="true"
        />
      )}

      <aside
        className={clsx(
          "fixed inset-y-0 left-0 z-30 flex w-64 flex-col bg-primary-dark text-white",
          "transition-transform duration-300 ease-in-out",
          sidebarOpen ? "translate-x-0" : "-translate-x-full",
          "lg:relative lg:translate-x-0",
        )}
      >
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

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex items-center gap-3 border-b border-surface bg-white px-4 py-3 lg:hidden">
          <button
            type="button"
            onClick={() => setSidebarOpen(true)}
            className="rounded-lg p-1.5 text-muted hover:bg-surface"
            aria-label="Ouvrir le menu"
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="flex items-center gap-2">
            <Store className="h-5 w-5 text-primary" />
            <span className="font-semibold text-primary-dark">GesCom-BF</span>
          </div>
        </header>

        <div className="flex items-center justify-end gap-2 border-b border-surface bg-white px-3 py-1.5 sm:gap-3 sm:px-4 sm:py-2">
          <ConnectionBadge />
          <PendingSyncBadge />
          <button
            type="button"
            className="btn-ghost flex items-center gap-1.5 px-2 py-1 text-sm sm:px-4 sm:py-2"
            onClick={handleLogout}
            aria-label="Deconnexion"
          >
            <LogOut className="h-4 w-4 shrink-0" />
            <span className="hidden sm:inline">Deconnexion</span>
          </button>
        </div>

        <main className="flex-1 overflow-y-auto p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default AppLayout;
