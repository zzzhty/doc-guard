import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const backendHost = process.env.BACKEND_HOST ?? "localhost";
const backendPort = process.env.BACKEND_PORT ?? "8000";
const backendTarget = process.env.DOCWATCHER_BACKEND_URL ?? `http://${backendHost}:${backendPort}`;

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/api": backendTarget,
    },
  },
});
