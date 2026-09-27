import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    // The backend runs on :8000 during local development.
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    // ECharts is ~1.04 MB raw but only ~343 kB gzipped, and it is deliberately
    // isolated in its own long-lived chunk (see manualChunks below) so it
    // caches independently of app code. Raising the limit silences a warning
    // that reflects this intentional trade-off, not a regression.
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: {
        // ECharts is by far the heaviest dependency; keeping it in its own
        // chunk lets the browser cache it independently of app code.
        manualChunks: {
          echarts: ['echarts'],
          react: ['react', 'react-dom', 'react-router-dom'],
          motion: ['framer-motion'],
        },
      },
    },
  },
})
