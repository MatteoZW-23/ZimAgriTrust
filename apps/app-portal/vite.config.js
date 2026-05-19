import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3003,
    host: true,
  },
  // When served behind nginx at /app/, set base to /app/
  base: process.env.VITE_BASE_PATH || "/",
  resolve: {
    alias: {
      "@agritrust/shared": path.resolve(__dirname, "../../packages/shared/src/index.ts"),
    },
  },
  optimizeDeps: {
    include: ["react", "react-dom", "zustand", "axios", "lucide-react"],
  },
});
