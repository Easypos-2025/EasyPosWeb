/**
 * Mini-app "Toma de Pedidos" que sirve el Agente Local en la red del negocio.
 * Compilación aparte de la app principal (no lleva dashboard, caja ni menú):
 *   npm run build:tomapedido   →  frontend/dist_tomapedido/
 * Sin CDN: en la red local puede no haber internet; todo va empaquetado.
 */
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import { execSync } from 'child_process'

const gitHash   = (() => { try { return execSync('git rev-parse --short HEAD').toString().trim() } catch { return 'local' } })()
const buildDate = new Date().toISOString().slice(2, 10).replace(/-/g, '.')

export default defineConfig({
  root: path.resolve(__dirname, 'src/apps/tomapedido'),
  base: './',
  define: { __APP_BUILD__: JSON.stringify(`${buildDate}·${gitHash}`) },
  plugins: [vue()],
  resolve: {
    alias: [
      // El Monitor de Errores es de la nube: no se empaqueta (traería el cliente de la API de la nube)
      { find: '@/utils/errorReporter', replacement: path.resolve(__dirname, 'src/apps/tomapedido/sinReporte.js') },
      { find: '@', replacement: path.resolve(__dirname, './src') },
    ],
  },
  build: {
    outDir: path.resolve(__dirname, 'dist_tomapedido'),
    emptyOutDir: true,
  },
  server: {
    host: true,
    port: 5174,
    // En desarrollo la API la atiende el agente: python -m agente_local
    proxy: { '/api/ag': 'http://127.0.0.1:8090' },
  },
})
