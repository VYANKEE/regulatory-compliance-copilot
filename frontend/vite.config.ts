import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Dev me /api/* calls seedhe backend (uvicorn, port 8000) ko proxy
    // hote hain -- frontend code me hamesha relative '/api/...' path use
    // hota hai, CORS/base-URL switch production build me sirf env var se
    // (VITE_API_BASE_URL) hota hai, code change nahi.
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
