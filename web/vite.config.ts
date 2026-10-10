import { fileURLToPath, URL } from 'node:url';

import { lingui } from '@lingui/vite-plugin';
import tailwindcss from '@tailwindcss/vite';
import { tanstackRouter } from '@tanstack/router-plugin/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [
    tanstackRouter({ target: 'react', autoCodeSplitting: true }),
    react({ babel: { plugins: ['@lingui/babel-plugin-lingui-macro'] } }),
    lingui(),
    tailwindcss(),
  ],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    // In docker-compose.dev the api is reached through nginx on the same origin,
    // so no proxy is needed there. This proxy only serves `pnpm --filter web dev` outside Docker.
    proxy: {
      '/api': { target: process.env.VITE_API_PROXY ?? 'http://localhost:3000', changeOrigin: true },
    },
    allowedHosts: ['assistant.localhost', 'localhost'],
    watch: { usePolling: process.env.VITE_WATCH_POLL === '1' },
  },
  build: { sourcemap: true },
});
