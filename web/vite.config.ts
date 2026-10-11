import { defineConfig } from "vite";

// Dev only: proxy the API so the browser stays same-origin; production serves dist from FastAPI.
export default defineConfig({
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },
});
