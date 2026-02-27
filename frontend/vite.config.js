import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // This 'root' line is CRITICAL because your index.html is in the root
  // but your code is in the /frontend folder.
  root: '.', 
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      // We are grouping all these to point to our Flask backend
      '/api': 'http://127.0.0.1:5000',
      '/auth': 'http://127.0.0.1:5000',
      '/admin': 'http://127.0.0.1:5000',
      '/cases': 'http://127.0.0.1:5000',
      '/acts': 'http://127.0.0.1:5000',
      '/ai': 'http://127.0.0.1:5000'
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    // This ensures Vite finds your App.jsx even inside the frontend folder
    rollupOptions: {
      input: 'index.html'
    }
  }
})
