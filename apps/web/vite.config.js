import { defineConfig, loadEnv } from 'vite';
import { normalizeApiUrl } from './src/config/api.js';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { fileURLToPath } from 'node:url';

export default defineConfig(({ mode }) => {
  const env = loadEnv(
    mode,
    fileURLToPath(new URL('../..', import.meta.url)),
    ''
  );

  const port = Number(env.WEB_PORT || 5173);

  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error('Invalid WEB_PORT');
  }

  const apiUrl = normalizeApiUrl(env.API_URL);

  const allowedHost = env.WEB_ALLOWED_HOST?.trim();

  if (!allowedHost) {
    throw new Error('Missing required environment variable: WEB_ALLOWED_HOST');
  }

  return {
    envPrefix: [],

    define: {
      'import.meta.env.API_URL': JSON.stringify(apiUrl),
    },

    plugins: [
      react(),
      tailwindcss(),
    ],

    server: {
      host: '127.0.0.1',
      port,
      strictPort: true,
    },

    preview: {
      host: '0.0.0.0',
      allowedHosts: [allowedHost],
    },
  };
});