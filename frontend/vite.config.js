import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    host: true,       // 🔥 CLAVE
    port: 5173,
    strictPort: true,

    // 🔥 NUEVO (PERMITE NGROK)
    allowedHosts: ["uncavalierly-homonymic-dorotha.ngrok-free.dev"]

  }
})