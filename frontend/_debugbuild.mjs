import { resolveConfig } from "vite";
const config = await resolveConfig({}, "build", "production");
console.log("plugins:", JSON.stringify(config.plugins.map(p => p.name)));
