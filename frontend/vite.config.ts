import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/admin': 'http://localhost:8000',
    }
  },
  define: {
    'process.env.VITE_API_BASE': JSON.stringify(process.env.VITE_API_BASE || 'http://localhost:8000')
  }
})
