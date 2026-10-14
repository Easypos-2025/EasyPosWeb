<template>
  <section v-if="!oculto" class="tb">
    <div class="tb-head">
      <h3 class="tb-title"><i class="bi bi-boxes"></i> Sedes del grupo</h3>
      <span v-if="datos" class="tb-nota"><i class="bi bi-hourglass-split"></i> Bodega: {{ datos.traslados_bodega.pendientes }} traslado(s) pendiente(s)</span>
    </div>

    <div v-if="cargando && !datos" class="tb-state"><div class="spinner-border spinner-border-sm text-primary"></div></div>
    <div v-else-if="datos" class="tb-grid">
      <article v-for="s in datos.sedes" :key="s.id" class="tb-card" tabindex="0" role="button"
               @click="abrir(s)" @keydown.enter="abrir(s)">
        <div class="tb-card-head">
          <b>{{ s.nombre }}</b>
          <span v-if="s.agente.con_escritorio" class="tb-estado" :class="s.agente.en_linea ? 'tb-estado--on' : 'tb-estado--off'">
            <i class="bi bi-pc-display"></i> {{ s.agente.en_linea ? 'Activa' : 'Sin conexión' }}
          </span>
          <span v-else class="tb-estado tb-estado--web"><i class="bi bi-globe"></i> Solo web</span>
        </div>
        <div class="tb-ventas">
          <div><small>Recibos ({{ s.ventas.recibos.cantidad }})</small><b>{{ fmt(s.ventas.recibos.total) }}</b></div>
          <div><small>Facturas ({{ s.ventas.facturas.cantidad }})</small><b>{{ fmt(s.ventas.facturas.total) }}</b></div>
          <div class="tb-total"><small>Total</small><b>{{ fmt(s.ventas.total) }}</b></div>
        </div>
        <div class="tb-turnos">
          <small>Turnos abiertos</small>
          <span v-if="!s.turnos.length" class="tb-nota">Ninguno</span>
          <span v-for="(t, i) in s.turnos" :key="i" class="tb-turno"><i class="bi bi-cash-stack"></i> {{ t.caja }} · {{ t.cajero }}</span>
        </div>
        <div class="tb-tras">
          <span :class="{ 'tb-alerta': s.traslados.pendientes }"><i class="bi bi-hourglass-split"></i> {{ s.traslados.pendientes }} pendiente(s)</span>
          <span><i class="bi bi-check2-circle"></i> {{ s.traslados.aceptados }} aceptado(s)</span>
        </div>
      </article>
    </div>

    <!-- Resumen completo de una sede -->
    <div v-if="sel" class="tb-overlay" @click.self="sel = null">
      <div class="tb-modal">
        <div class="tb-modal-head">
          <b>{{ sel.sede.nombre }} · {{ fechaTexto }}</b>
          <button class="tb-x" @click="sel = null"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="tb-modal-body">
          <div class="tb-kpis">
            <div><small>Recibos ({{ sel.ventas.recibos.cantidad }})</small><b>{{ fmt(sel.ventas.recibos.total) }}</b></div>
            <div><small>Facturas ({{ sel.ventas.facturas.cantidad }})</small><b>{{ fmt(sel.ventas.facturas.total) }}</b></div>
            <div><small>Total</small><b>{{ fmt(sel.ventas.total) }}</b></div>
            <div><small>Ticket promedio</small><b>{{ fmt(sel.ventas.ticket_promedio) }}</b></div>
          </div>
          <div class="tb-cols">
            <div class="tb-bloque">
              <h4>Formas de pago</h4>
              <p v-if="!sel.formas_pago.length" class="tb-nota">Sin pagos en la fecha.</p>
              <div v-for="f in sel.formas_pago" :key="f.forma" class="tb-fila"><span>{{ f.forma }}</span><b>{{ fmt(f.total) }}</b></div>
            </div>
            <div class="tb-bloque">
              <h4>Más vendidos</h4>
              <p v-if="!sel.top_productos.length" class="tb-nota">Sin ventas en la fecha.</p>
              <div v-for="p in sel.top_productos" :key="p.producto" class="tb-fila"><span>{{ p.producto }} <small>× {{ fmtCant(p.cantidad) }}</small></span><b>{{ fmt(p.valor) }}</b></div>
            </div>
            <div class="tb-bloque">
              <h4>Turnos abiertos</h4>
              <p v-if="!sel.turnos.length" class="tb-nota">Ninguno.</p>
              <div v-for="(t, i) in sel.turnos" :key="i" class="tb-fila"><span>{{ t.caja }} · {{ t.cajero }}</span><small>{{ t.abierto_en }}</small></div>
              <p class="tb-nota">
                <template v-if="sel.agente.con_escritorio">Escritorio {{ sel.agente.en_linea ? 'conectado' : 'sin conexión' }}<template v-if="sel.agente.ultimo_contacto"> · último contacto {{ fechaHora(sel.agente.ultimo_contacto) }}</template></template>
                <template v-else>Sede solo web.</template>
              </p>
            </div>
            <div class="tb-bloque">
              <h4>Traslados</h4>
              <p v-if="!sel.traslados.length" class="tb-nota">Sin pendientes ni cargados en la fecha.</p>
              <div v-for="t in sel.traslados" :key="t.id" class="tb-fila">
                <span>#{{ t.numero }} {{ t.origen }} → {{ t.destino }}</span>
                <small :class="{ 'tb-alerta': t.estado !== 'CARGADO' }">{{ t.estado === 'CARGADO' ? 'Aceptado' : 'Pendiente' }}</small>
              </div>
              <router-link class="tb-link" to="/bodega-central/traslados" @click="sel = null"><i class="bi bi-truck"></i> Ver todos los traslados</router-link>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
// Tablero de la Bodega Central en el dashboard: una tarjeta por sede (ventas de la fecha por recibos y facturas,
// turnos abiertos, escritorio conectado, traslados pendientes y aceptados) y el total del grupo.
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'
import { fechaDashboard as fecha } from '@/composables/useVentasKpis'

const datos = ref(null)
const cargando = ref(false)
const oculto = ref(false)
const sel = ref(null)
let timer = null

const usuario = (() => { try { return JSON.parse(localStorage.getItem('user') || '{}') } catch { return {} } })()
const fmtMoneda = new Intl.NumberFormat(usuario.locale || 'es-CO', { style: 'currency', currency: usuario.currency_code || 'COP', maximumFractionDigits: 0 })
const fmt = (v) => fmtMoneda.format(Number(v) || 0)
const fmtCant = (v) => new Intl.NumberFormat('es-CO', { maximumFractionDigits: 2 }).format(Number(v) || 0)
const fechaHora = (v) => (v ? new Date(v).toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' }) : '')
const fechaTexto = computed(() => new Date(`${fecha.value}T12:00:00`).toLocaleDateString('es-CO', { dateStyle: 'long' }))

async function cargar() {
  cargando.value = true
  try { datos.value = (await api.get('/api/bodega-central/tablero', { params: { fecha: fecha.value } })).data }
  catch (e) { if (e?.response?.status === 403) oculto.value = true }      // rol sin acceso a la bodega: no se muestra
  cargando.value = false
}

async function abrir(s) {
  try { sel.value = (await api.get(`/api/bodega-central/tablero/sede/${s.id}`, { params: { fecha: fecha.value } })).data }
  catch (e) { showToast(e?.response?.data?.detail || 'Error cargando el resumen de la sede', 'error') }
}

watch(fecha, cargar)
onMounted(() => { cargar(); timer = setInterval(cargar, 120000) })
onBeforeUnmount(() => clearInterval(timer))
</script>

<style scoped>
.tb { margin: 16px 0; }
.tb-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 10px; }
.tb-title { font-size: 16px; font-weight: 800; color: #1e3a5f; margin: 0; display: flex; gap: 8px; align-items: center; }
.tb-state { display: flex; justify-content: center; padding: 20px; }
.tb-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
.tb-card { background: #fff; border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,.08); padding: 12px 14px; display: flex;
  flex-direction: column; gap: 10px; cursor: pointer; border: 1.5px solid transparent; }
.tb-card:hover, .tb-card:focus { border-color: #93c5fd; outline: none; }
.tb-card-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.tb-card-head b { font-size: 14px; color: #1e293b; word-break: break-word; }
.tb-estado { font-size: 11px; font-weight: 800; padding: 3px 8px; border-radius: 999px; white-space: nowrap; display: inline-flex; gap: 4px; }
.tb-estado--on { background: #dcfce7; color: #166534; }
.tb-estado--off { background: #fee2e2; color: #991b1b; }
.tb-estado--web { background: #e0e7ff; color: #3730a3; }
.tb-ventas { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; }
.tb-ventas div { display: flex; flex-direction: column; min-width: 0; }
.tb-ventas small, .tb-turnos small { font-size: 10.5px; color: #64748b; font-weight: 700; text-transform: uppercase; }
.tb-ventas b { font-size: 13.5px; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tb-total b { color: #15803d; }
.tb-turnos { display: flex; flex-direction: column; gap: 3px; }
.tb-turno { font-size: 12px; color: #334155; }
.tb-nota { font-size: 12px; color: #94a3b8; margin: 0; }
.tb-tras { display: flex; gap: 12px; font-size: 12px; color: #475569; flex-wrap: wrap; }
.tb-alerta { color: #b45309; font-weight: 700; }
.tb-overlay { position: fixed; inset: 0; background: rgba(15,23,42,.5); display: flex; align-items: center; justify-content: center; z-index: 1050; padding: 16px; }
.tb-modal { background: #fff; border-radius: 14px; width: 100%; max-width: 860px; max-height: 92vh; display: flex; flex-direction: column; }
.tb-modal-head { display: flex; justify-content: space-between; align-items: center; padding: 14px 16px; border-bottom: 1px solid #e2e8f0; }
.tb-modal-head b { color: #1e293b; }
.tb-x { border: none; background: none; font-size: 18px; color: #64748b; cursor: pointer; }
.tb-modal-body { padding: 14px 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
.tb-kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.tb-kpis div { background: #f8fafc; border-radius: 10px; padding: 8px 10px; display: flex; flex-direction: column; }
.tb-kpis small { font-size: 11px; color: #64748b; font-weight: 700; }
.tb-kpis b { font-size: 15px; color: #1e3a5f; }
.tb-cols { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.tb-bloque { border: 1px solid #e2e8f0; border-radius: 12px; padding: 10px 12px; display: flex; flex-direction: column; gap: 6px; }
.tb-bloque h4 { font-size: 13px; font-weight: 800; color: #1e3a5f; margin: 0; }
.tb-fila { display: flex; justify-content: space-between; gap: 8px; font-size: 13px; color: #334155; }
.tb-fila span { min-width: 0; word-break: break-word; }
.tb-fila small { color: #64748b; white-space: nowrap; }
.tb-link { font-size: 12.5px; font-weight: 700; color: #1d4ed8; text-decoration: none; }

@media (max-width: 768px) {
  .tb-grid { grid-template-columns: 1fr 1fr; }
  .tb-cols { grid-template-columns: 1fr; }
  .tb-kpis { grid-template-columns: 1fr 1fr; }
  .tb-overlay { align-items: flex-end; padding: 0; }
  .tb-modal { max-width: none; border-radius: 14px 14px 0 0; max-height: 94vh; }
}
@media (max-width: 576px) {
  .tb-grid { grid-template-columns: 1fr; }
  .tb-head { flex-direction: column; align-items: flex-start; gap: 4px; }
}
</style>
