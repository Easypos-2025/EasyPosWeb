import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import { execSync } from 'child_process'

const gitHash  = (() => { try { return execSync('git rev-parse --short HEAD').toString().trim() } catch { return 'local' } })()
const buildDate = new Date().toISOString().slice(2, 10).replace(/-/g, '.')   // "YY.MM.DD"

export default defineConfig({
  define: {
    __APP_BUILD__: JSON.stringify(`${buildDate}·${gitHash}`)
  },
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