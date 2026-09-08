import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(), 
    tailwindcss()
  ],
  publicDir: '../../data/static',
  server: {
    host: '0.0.0.0',
    port: 5173, 
    watch: {
      usePolling: true,
    },
    proxy: {
      '/api': {
        target: process.env.VITE_PROXY_TARGET || 'http://backend:8000',
        changeOrigin: true,
      }
    }
  }
})
