import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
// @ts-ignore
import path from "path";

export default defineConfig({
  server: {
    host: "127.0.0.1",
    port: 8080,
    proxy: {
      // Frontend now uses /api/v1 directly (see services/api.ts), so the dev
      // proxy is a straight pass-through to FastAPI on 8000.
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    },
    hmr: {
      overlay: false,
    },
  },
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
    dedupe: ["react", "react-dom", "react/jsx-runtime", "react/jsx-dev-runtime"],
  },
});