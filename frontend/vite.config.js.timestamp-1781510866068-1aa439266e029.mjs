// vite.config.js
import { defineConfig } from "file:///sessions/funny-practical-gauss/mnt/gestion-commerciale-saas-doc/frontend/node_modules/vite/dist/node/index.js";
import react from "file:///sessions/funny-practical-gauss/mnt/gestion-commerciale-saas-doc/frontend/node_modules/@vitejs/plugin-react/dist/index.mjs";
import path from "path";
var __vite_injected_original_dirname = "/sessions/funny-practical-gauss/mnt/gestion-commerciale-saas-doc/frontend";
var vite_config_default = defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__vite_injected_original_dirname, "./src")
    }
  },
  server: {
    host: true,
    port: 5173,
    proxy: {
      // En dev, le frontend appelle /api/v1/* et Vite relaie vers Flask.
      "/api": {
        target: process.env.VITE_API_PROXY_TARGET || "http://localhost:5000",
        changeOrigin: true
      }
    }
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcuanMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCIvc2Vzc2lvbnMvZnVubnktcHJhY3RpY2FsLWdhdXNzL21udC9nZXN0aW9uLWNvbW1lcmNpYWxlLXNhYXMtZG9jL2Zyb250ZW5kXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ZpbGVuYW1lID0gXCIvc2Vzc2lvbnMvZnVubnktcHJhY3RpY2FsLWdhdXNzL21udC9nZXN0aW9uLWNvbW1lcmNpYWxlLXNhYXMtZG9jL2Zyb250ZW5kL3ZpdGUuY29uZmlnLmpzXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ltcG9ydF9tZXRhX3VybCA9IFwiZmlsZTovLy9zZXNzaW9ucy9mdW5ueS1wcmFjdGljYWwtZ2F1c3MvbW50L2dlc3Rpb24tY29tbWVyY2lhbGUtc2Fhcy1kb2MvZnJvbnRlbmQvdml0ZS5jb25maWcuanNcIjtpbXBvcnQgeyBkZWZpbmVDb25maWcgfSBmcm9tIFwidml0ZVwiO1xuaW1wb3J0IHJlYWN0IGZyb20gXCJAdml0ZWpzL3BsdWdpbi1yZWFjdFwiO1xuaW1wb3J0IHBhdGggZnJvbSBcInBhdGhcIjtcbi8vIENmLiAxMC1GUk9OVEVORC1SRUFDVC5tZCBcdTIwMTQgVml0ZSArIFJlYWN0ICsgVFMgKyBUYWlsd2luZC5cbmV4cG9ydCBkZWZhdWx0IGRlZmluZUNvbmZpZyh7XG4gICAgcGx1Z2luczogW3JlYWN0KCldLFxuICAgIHJlc29sdmU6IHtcbiAgICAgICAgYWxpYXM6IHtcbiAgICAgICAgICAgIFwiQFwiOiBwYXRoLnJlc29sdmUoX19kaXJuYW1lLCBcIi4vc3JjXCIpLFxuICAgICAgICB9LFxuICAgIH0sXG4gICAgc2VydmVyOiB7XG4gICAgICAgIGhvc3Q6IHRydWUsXG4gICAgICAgIHBvcnQ6IDUxNzMsXG4gICAgICAgIHByb3h5OiB7XG4gICAgICAgICAgICAvLyBFbiBkZXYsIGxlIGZyb250ZW5kIGFwcGVsbGUgL2FwaS92MS8qIGV0IFZpdGUgcmVsYWllIHZlcnMgRmxhc2suXG4gICAgICAgICAgICBcIi9hcGlcIjoge1xuICAgICAgICAgICAgICAgIHRhcmdldDogcHJvY2Vzcy5lbnYuVklURV9BUElfUFJPWFlfVEFSR0VUIHx8IFwiaHR0cDovL2xvY2FsaG9zdDo1MDAwXCIsXG4gICAgICAgICAgICAgICAgY2hhbmdlT3JpZ2luOiB0cnVlLFxuICAgICAgICAgICAgfSxcbiAgICAgICAgfSxcbiAgICB9LFxufSk7XG4iXSwKICAibWFwcGluZ3MiOiAiO0FBQTZZLFNBQVMsb0JBQW9CO0FBQzFhLE9BQU8sV0FBVztBQUNsQixPQUFPLFVBQVU7QUFGakIsSUFBTSxtQ0FBbUM7QUFJekMsSUFBTyxzQkFBUSxhQUFhO0FBQUEsRUFDeEIsU0FBUyxDQUFDLE1BQU0sQ0FBQztBQUFBLEVBQ2pCLFNBQVM7QUFBQSxJQUNMLE9BQU87QUFBQSxNQUNILEtBQUssS0FBSyxRQUFRLGtDQUFXLE9BQU87QUFBQSxJQUN4QztBQUFBLEVBQ0o7QUFBQSxFQUNBLFFBQVE7QUFBQSxJQUNKLE1BQU07QUFBQSxJQUNOLE1BQU07QUFBQSxJQUNOLE9BQU87QUFBQTtBQUFBLE1BRUgsUUFBUTtBQUFBLFFBQ0osUUFBUSxRQUFRLElBQUkseUJBQXlCO0FBQUEsUUFDN0MsY0FBYztBQUFBLE1BQ2xCO0FBQUEsSUFDSjtBQUFBLEVBQ0o7QUFDSixDQUFDOyIsCiAgIm5hbWVzIjogW10KfQo=
