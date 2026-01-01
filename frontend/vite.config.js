import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  // Determine backend port based on environment
  // In development mode, use dev backend (5002)
  // In production/preview mode, use production backend (5001)
  const backendPort = mode === 'development' ? 5002 : 5001;

  return {
    plugins: [react()],
    server: {
      host: '0.0.0.0', // Explicitly bind to all network interfaces
      port: 3000,
      proxy: {
        '/api': {
          target: `http://localhost:${backendPort}`,
          changeOrigin: true,
        }
      }
    }
  }
})
