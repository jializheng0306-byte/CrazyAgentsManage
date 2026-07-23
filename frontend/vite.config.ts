import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Multi-entry: graph + agent are separate SPA bundles (ADR-002).
// Build outputs to dist/ which Flask serves statically (same-origin → cookie auth).
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      input: {
        graph: 'index.html',
        agent: 'agent.html',
      },
    },
    outDir: 'dist',
  },
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:5000',
    },
  },
});
