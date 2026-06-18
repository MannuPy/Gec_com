import { VitePWA } from "vite-plugin-pwa";
const plugins = VitePWA({
  registerType: "autoUpdate",
  includeAssets: ["icons/*.png"],
  manifest: { name: "Test" },
});
console.log("type:", typeof plugins, Array.isArray(plugins));
console.log("count:", plugins.length);
for (const p of plugins) {
  console.log("- plugin:", p && p.name, "apply:", p && p.apply);
}
