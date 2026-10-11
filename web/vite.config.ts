import { defineConfig } from "vite";

// Relative asset paths work both behind FastAPI and under a GitHub Pages subpath.
// Dev only: proxy the API so the browser stays same-origin.
export default defineConfig({
  base: "./",
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },
});
