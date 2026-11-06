import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/auth': 'http://127.0.0.1:8000',
      '/analysis': 'http://127.0.0.1:8000',
      '/uploads': 'http://127.0.0.1:8000',
      '/library/cases': 'http://127.0.0.1:8000',
    },
  },
})
