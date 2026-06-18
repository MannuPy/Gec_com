import { lazy, Suspense } from "react";
import { createBrowserRouter } from "react-router-dom";

import { AppLayout } from "@/layouts/AppLayout";
import { ProtectedRoute, RequirePermission } from "@/components/ProtectedRoute";
import NotFoundPage from "@/pages/NotFoundPage";

const LoginPage = lazy(() => import("@/features/auth/pages/LoginPage"));
const ChangePasswordPage = lazy(() => import("@/features/auth/pages/ChangePasswordPage"));
const DashboardPage = lazy(() => import("@/features/dashboard/pages/DashboardPage"));
const ProductsPage = lazy(() => import("@/features/products/pages/ProductsPage"));
const POSPage = lazy(() => import("@/features/sales/pages/POSPage"));
const CustomersPage = lazy(() => import("@/features/customers/pages/CustomersPage"));
const StockPage = lazy(() => import("@/features/stock/pages/StockPage"));
const SuppliersPage = lazy(() => import("@/features/suppliers/pages/SuppliersPage"));
const TransfersPage = lazy(() => import("@/features/transfers/pages/TransfersPage"));
const UsersPage = lazy(() => import("@/features/users/pages/UsersPage"));
const AuditLogPage = lazy(() => import("@/features/audit/pages/AuditLogPage"));
const SalesHistoryPage = lazy(() => import("@/features/sales/pages/SalesHistoryPage"));
const AnalyticsPage = lazy(() => import("@/features/analytics/pages/AnalyticsPage"));
const InventoryPage = lazy(() => import("@/features/inventory/pages/InventoryPage"));

function Loading() {
  return (
    <div className="flex h-screen items-center justify-center bg-surface text-muted">
      Chargement...
    </div>
  );
}

function withSuspense(element: React.ReactNode) {
  return <Suspense fallback={<Loading />}>{element}</Suspense>;
}

export const router = createBrowserRouter([
  {
    path: "/login",
    element: withSuspense(<LoginPage />),
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        // RF-05 : page de changement de mot de passe obligatoire, en dehors
        // de l'AppLayout (pas de menu/navigation avant le changement).
        path: "changer-mot-de-passe",
        element: withSuspense(<ChangePasswordPage />),
      },
      {
        element: <AppLayout />,
        children: [
          {
            element: <RequirePermission permission="reports:read" />,
            children: [{ index: true, element: withSuspense(<DashboardPage />) }],
          },
          {
            element: <RequirePermission permission="products:read" />,
            children: [{ path: "produits", element: withSuspense(<ProductsPage />) }],
          },
          {
            element: <RequirePermission permission="sales:create" />,
            children: [{ path: "caisse", element: withSuspense(<POSPage />) }],
          },
          {
            element: <RequirePermission permission="sales:read" />,
            children: [{ path: "ventes", element: withSuspense(<SalesHistoryPage />) }],
          },
          {
            element: <RequirePermission permission="customers:read" />,
            children: [{ path: "clients", element: withSuspense(<CustomersPage />) }],
          },
          {
            element: <RequirePermission permission="stock:read" />,
            children: [{ path: "stock", element: withSuspense(<StockPage />) }],
          },
          {
            element: <RequirePermission permission="suppliers:read" />,
            children: [{ path: "fournisseurs", element: withSuspense(<SuppliersPage />) }],
          },
          {
            element: <RequirePermission permission="transfers:read" />,
            children: [{ path: "transferts", element: withSuspense(<TransfersPage />) }],
          },
          {
            element: <RequirePermission permission="users:read" />,
            children: [{ path: "utilisateurs", element: withSuspense(<UsersPage />) }],
          },
          {
            element: <RequirePermission permission="users:read" />,
            children: [{ path: "audit", element: withSuspense(<AuditLogPage />) }],
          },
          {
            element: <RequirePermission permission="analytics:read" />,
            children: [{ path: "analytique", element: withSuspense(<AnalyticsPage />) }],
          },
          {
            element: <RequirePermission permission="inventory:read" />,
            children: [{ path: "inventaire", element: withSuspense(<InventoryPage />) }],
          },
        ],
      },
    ],
  },
  {
    path: "*",
    element: withSuspense(<NotFoundPage />),
  },
]);
