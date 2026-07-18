import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // In dev the FastAPI backend runs separately; same-origin in production.
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
});
