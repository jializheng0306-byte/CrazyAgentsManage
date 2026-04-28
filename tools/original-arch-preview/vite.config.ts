import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  base: './',
  plugins: [react()],
  build: {
    outDir: '../../src/webui/static/original-arch-preview',
    emptyOutDir: true,
  },
});
