import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Set base to './' so built assets load correctly even when hosted under a sub-path
// (avoids blank white screen when index.html is not at domain root)
export default defineConfig({
  base: './',
  plugins: [react()],
  server: {
    port: 3001,
    proxy: {
      '/api': {
        target: process.env.VITE_API_PROXY || 'http://127.0.0.1:8080',
        changeOrigin: true
      },
      '/calc': {
        target: process.env.VITE_API_PROXY || 'http://127.0.0.1:8080',
        changeOrigin: true
      }
    }
  }
});
