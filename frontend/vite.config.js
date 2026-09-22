import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Vite dev server config.
// The /api proxy forwards API calls to the FastAPI backend (added in Phase 6),
// so the frontend can call `/api/...` without CORS issues during development.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
