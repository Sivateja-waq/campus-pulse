import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// /api calls go to Django during development, so no CORS setup needed
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
});
