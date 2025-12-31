import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // Explicitly bind to all network interfaces
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5001', // Production backend
        changeOrigin: true,
      }
    }
  }
})
