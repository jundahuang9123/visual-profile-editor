import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/schema': 'http://localhost:8000',
      '/validate': 'http://localhost:8000',
      '/export': 'http://localhost:8000',
    },
  },
});
