import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";
import path from "path";

// Cf. 10-FRONTEND-REACT.md — Vite + React + TS + Tailwind.
// Cf. 26-GESTION-OFFLINE-PWA.md §26.9 — configuration du Service Worker (Workbox).
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["icons/*.png"],
      manifest: {
        name: "GesCom-BF",
        short_name: "GesCom",
        description: "Gestion commerciale multi-sites — caisse, stock, ventes (Burkina Faso).",
        start_url: "/",
        display: "standalone",
        background_color: "#ffffff",
        theme_color: "#0f766e",
        icons: [
          { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
          {
            src: "/icons/maskable-icon-512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "maskable",
          },
        ],
      },
      workbox: {
        // Synchronisation incrémentale du catalogue/stock (26.7) : on laisse
        // la requête réseau prioritaire (NetworkFirst) avec repli sur le
        // cache si le réseau est indisponible (mode hors-ligne, RF-20).
        runtimeCaching: [
          {
            urlPattern: /\/api\/v1\/products/,
            handler: "NetworkFirst",
            options: {
              cacheName: "products-cache",
              networkTimeoutSeconds: 3,
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            urlPattern: /\/api\/v1\/stock/,
            handler: "NetworkFirst",
            options: {
              cacheName: "stock-cache",
              networkTimeoutSeconds: 3,
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            urlPattern: /\/api\/v1\/sales\/discounts\/rates/,
            handler: "NetworkFirst",
            options: {
              cacheName: "discount-rates-cache",
              networkTimeoutSeconds: 3,
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            urlPattern: /\.(?:png|jpg|jpeg|svg|woff2?)$/,
            handler: "CacheFirst",
            options: {
              cacheName: "static-assets",
              expiration: { maxEntries: 100, maxAgeSeconds: 60 * 60 * 24 * 30 },
            },
          },
        ],
      },
      devOptions: {
        enabled: false,
      },
    }),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: true,
    port: 5173,
    proxy: {
      // En dev, le frontend appelle /api/v1/* et Vite relaie vers Flask.
      "/api": {
        target: process.env.VITE_API_PROXY_TARGET || "http://localhost:5000",
        changeOrigin: true,
      },
    },
  },
});
