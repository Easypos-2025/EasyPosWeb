<template>
  <div class="pq-view">
    <!-- KPI Bar -->
    <div class="kpi-bar">
      <div class="kpi-card kpi-primary">
        <i class="bi bi-car-front-fill kpi-icon"></i>
        <div class="kpi-body">
          <span class="kpi-val">{{ stats.vehiculos_activos ?? '—' }}</span>
          <span class="kpi-label">Activos Ahora</span>
        </div>
      </div>
      <div class="kpi-card kpi-info">
        <i class="bi bi-p-circle-fill kpi-icon"></i>
        <div class="kpi-body">
          <span class="kpi-val">{{ stats.plazas_disponibles ?? '—' }}</span>
          <span class="kpi-label">Plazas Disp.</span>
        </div>
      </div>
      <div class="kpi-card kpi-success">
        <i class="bi bi-box-arrow-right kpi-icon"></i>
        <div class="kpi-body">
          <span class="kpi-val">{{ stats.salidas_dia ?? '—' }}</span>
          <span class="kpi-label">Salidas Hoy</span>
        </div>
      </div>
      <div class="kpi-card kpi-money">
        <i class="bi bi-cash-coin kpi-icon"></i>
        <div class="kpi-body">
          <span class="kpi-val">${{ (stats.recaudo_dia || 0).toLocaleString() }}</span>
          <span class="kpi-label">Recaudo Hoy</span>
        </div>
      </div>
      <div class="kpi-card kpi-warn" v-if="stats.morosos">
        <i class="bi bi-exclamation-triangle-fill kpi-icon"></i>
        <div class="kpi-body">
          <span class="kpi-val">{{ stats.morosos }}</span>
          <span class="kpi-label">Morosos</span>
        </div>
      </div>
    </div>

    <!-- Búsqueda QR / Placa -->
    <div class="pq-card search-bar">
      <div class="search-input-wrap">
        <i class="bi bi-search"></i>
        <input v-model="busqueda" class="search-input" placeholder="Buscar por placa o token QR..."
               @keydown.enter="buscarVehiculo" />
      </div>
      <button class="btn-pq-primary" @click="buscarVehiculo">
        <i class="bi bi-arrow-right"></i> Buscar
      </button>
    </div>

    <!-- Vehículos activos -->
    <div class="section-title">
      <h3><i class="bi bi-car-front-fill"></i> Vehículos en Parqueadero</h3>
      <button class="btn-refresh" @click="cargar" :disabled="loading">
        <i class="bi bi-arrow-clockwise"></i>
      </button>
    </div>

    <div v-if="loading" class="pq-loader">Cargando...</div>
    <div v-else-if="!activos.length" class="pq-empty">
      <i class="bi bi-car-front" style="font-size:2.5rem;opacity:.3"></i>
      <p>No hay vehículos activos en este momento</p>
    </div>

    <div v-else class="vehiculos-grid">
      <div v-for="v in activos" :key="v.id" class="vehiculo-card" @click="abrirSalida(v)">
        <div class="vc-foto">
          <img v-if="v.foto_url" :src="v.foto_url" class="vc-img" />
          <i v-else class="bi bi-car-front-fill" style="font-size:36px;color:#94a3b8"></i>
        </div>
        <div class="vc-placa">{{ v.placa }}</div>
        <div class="vc-servicio">
          <span class="tag-cat" :style="{ background: (v.categoria_color || '#3b82f6') + '22', color: v.categoria_color || '#3b82f6' }">
            {{ v.categoria_nombre || v.servicio_nombre }}
          </span>
        </div>
        <div class="vc-tiempo"><i class="bi bi-clock"></i> {{ formatTiempo(v.hora_ingreso) }}</div>
        <div class="vc-valor">${{ (v.valor_actual || 0).toLocaleString() }}</div>
        <div class="vc-action">
          <button class="btn-cobrar" @click.stop="abrirSalida(v)">
            <i class="bi bi-cash-coin"></i> Cobrar
          </button>
        </div>
      </div>
    </div>

    <!-- Modal cobro / salida -->
    <div v-if="modalSalida" class="pq-overlay" @click.self="modalSalida = false">
      <div class="pq-modal">
        <div class="pq-modal-head">
          <h3><i class="bi bi-cash-coin" style="color:#f59e0b"></i> Registrar Salida</h3>
          <button class="btn-close" @click="modalSalida = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div v-if="ingresoSeleccionado" class="pq-modal-body">
          <div v-if="ingresoSeleccionado.foto_url" class="foto-resumen">
            <img :src="ingresoSeleccionado.foto_url" />
          </div>
          <div class="resumen-salida">
            <div class="rs-row"><span>Placa</span><strong>{{ ingresoSeleccionado.placa }}</strong></div>
            <div class="rs-row"><span>Servicio</span><span>{{ ingresoSeleccionado.servicio_nombre }}</span></div>
            <div class="rs-row"><span>Ingreso</span><span>{{ formatFechaHora(ingresoSeleccionado.hora_ingreso) }}</span></div>
            <div class="rs-row"><span>Tiempo</span><span>{{ formatMinutos(ingresoSeleccionado.minutos_transcurridos) }}</span></div>
            <div class="rs-row rs-total"><span>Valor a Cobrar</span><strong>${{ (ingresoSeleccionado.valor_actual || 0).toLocaleString() }}</strong></div>
          </div>

          <label>Forma de Pago</label>
          <select v-model="pagoForm.forma_pago" class="pq-input">
            <option value="efectivo">Efectivo</option>
            <option value="transferencia">Transferencia</option>
            <option value="otro">Otro</option>
          </select>

          <label>Valor Cobrado</label>
          <input type="number" v-model.number="pagoForm.valor_cobrado" class="pq-input" />
        </div>
        <div class="pq-modal-foot">
          <button class="btn-pq-ghost btn-danger-ghost" @click="cancelarIngreso">
            <i class="bi bi-x-circle"></i> Cancelar Ingreso
          </button>
          <button class="btn-pq-ghost" @click="modalSalida = false">Cerrar</button>
          <button class="btn-pq-primary" :disabled="pagando" @click="confirmarSalida">
            <i class="bi" :class="pagando ? 'bi-hourglass-split' : 'bi-check2-circle'"></i>
            {{ pagando ? 'Procesando...' : 'Confirmar Pago' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useCompanyStore } from '@/stores/companyStore'
import { useModuleName } from '@/composables/useModuleName'
import { showToast } from '@/utils/toast'
import api from '@/services/apis'

const companyStore = useCompanyStore()
const { moduleName } = useModuleName()

const stats = ref({})
const activos = ref([])
const loading = ref(true)
const pagando = ref(false)
const modalSalida = ref(false)
const ingresoSeleccionado = ref(null)
const busqueda = ref('')
const pagoForm = ref({ forma_pago: 'efectivo', valor_cobrado: 0 })

const cid = () => companyStore.selectedCompany?.id_company

let timer = null

function formatTiempo(hora) {
  const h = new Date(hora)
  const diff = Math.floor((Date.now() - h) / 60000)
  if (diff < 60) return `${diff} min`
  return `${Math.floor(diff / 60)}h ${diff % 60}min`
}

function formatFechaHora(dt) {
  return new Date(dt).toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' })
}

function formatMinutos(min) {
  if (!min) return '0 min'
  if (min < 60) return `${min} min`
  return `${Math.floor(min / 60)}h ${min % 60}min`
}

async function cargar() {
  loading.value = true
  try {
    const [statsR, activosR] = await Promise.all([
      api.get('/parqueadero/stats', { params: { company_id: cid() } }),
      api.get('/parqueadero/ingresos', { params: { company_id: cid(), estado: 'activo' } }),
    ])
    stats.value = statsR.data
    activos.value = activosR.data
  } catch { /* silencioso */ }
  finally { loading.value = false }
}

async function buscarVehiculo() {
  if (!busqueda.value.trim()) return
  try {
    // Intentar por QR primero, luego por placa
    let item = null
    const q = busqueda.value.trim().toUpperCase()
    if (q.length <= 20 && /^[A-Z0-9]+$/.test(q)) {
      // Puede ser token QR o placa
      const found = activos.value.find(v => v.placa === q || v.qr_token === q)
      if (found) {
        item = found
      } else {
        try {
          const { data } = await api.get(`/parqueadero/ingresos/by-qr/${q}`, { params: { company_id: cid() } })
          item = data
        } catch { /* no es QR */ }
      }
    }
    if (item) {
      abrirSalida(item)
    } else {
      showToast('Vehículo no encontrado en parqueadero activo', 'warn')
    }
  } catch { showToast('Error en búsqueda', 'error') }
}

function abrirSalida(v) {
  ingresoSeleccionado.value = v
  pagoForm.value = { forma_pago: 'efectivo', valor_cobrado: v.valor_actual || 0 }
  modalSalida.value = true
}

async function confirmarSalida() {
  pagando.value = true
  try {
    await api.post(`/parqueadero/ingresos/${ingresoSeleccionado.value.id}/pagar`, pagoForm.value, {
      params: { company_id: cid() }
    })
    showToast('Pago registrado — vehículo salió', 'success')
    modalSalida.value = false
    cargar()
  } catch { showToast('Error al registrar pago', 'error') }
  finally { pagando.value = false }
}

async function cancelarIngreso() {
  if (!confirm('¿Cancelar este ingreso? No se registrará pago.')) return
  try {
    await api.put(`/parqueadero/ingresos/${ingresoSeleccionado.value.id}/cancelar`, {}, {
      params: { company_id: cid() }
    })
    showToast('Ingreso cancelado', 'success')
    modalSalida.value = false
    cargar()
  } catch { showToast('Error al cancelar', 'error') }
}

onMounted(() => {
  cargar()
  // Auto-refresh cada 90 segundos
  timer = setInterval(cargar, 90000)
})

onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.pq-view { padding: 16px; }

/* KPI Bar */
.kpi-bar { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; }
.kpi-card { display: flex; align-items: center; gap: 12px; background: var(--card-bg, #fff); border-radius: 12px; padding: 14px 18px; flex: 1; min-width: 150px; box-shadow: 0 1px 6px rgba(0,0,0,.07); border-top: 3px solid transparent; }
.kpi-primary { border-top-color: #3b82f6; }
.kpi-info    { border-top-color: #06b6d4; }
.kpi-success { border-top-color: #22c55e; }
.kpi-money   { border-top-color: #f59e0b; }
.kpi-warn    { border-top-color: #ef4444; }
.kpi-icon { font-size: 26px; color: var(--kpi-icon-color, #94a3b8); }
.kpi-primary .kpi-icon { color: #3b82f6; }
.kpi-info    .kpi-icon { color: #06b6d4; }
.kpi-success .kpi-icon { color: #22c55e; }
.kpi-money   .kpi-icon { color: #f59e0b; }
.kpi-warn    .kpi-icon { color: #ef4444; }
.kpi-body { display: flex; flex-direction: column; }
.kpi-val { font-size: 22px; font-weight: 800; line-height: 1; }
.kpi-label { font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: .4px; }

/* Search bar */
.search-bar { display: flex; gap: 10px; align-items: center; margin-bottom: 20px; padding: 12px 16px; }
.search-input-wrap { flex: 1; display: flex; align-items: center; gap: 8px; background: var(--input-bg, #f8fafc); border: 1.5px solid var(--border, #e2e8f0); border-radius: 8px; padding: 8px 12px; }
.search-input-wrap i { color: #94a3b8; }
.search-input { border: none; background: none; outline: none; width: 100%; font-size: 14px; }

/* Section title */
.section-title { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.section-title h3 { margin: 0; font-size: 16px; font-weight: 700; display: flex; align-items: center; gap: 8px; }
.btn-refresh { background: none; border: 1px solid var(--border, #e2e8f0); border-radius: 8px; padding: 6px 10px; cursor: pointer; font-size: 16px; }

.pq-loader { text-align: center; padding: 60px; opacity: .5; }
.pq-empty { text-align: center; padding: 60px 20px; opacity: .5; }
.pq-empty i { display: block; margin-bottom: 12px; }

/* Grid de vehículos */
.vehiculos-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 14px; }
.vehiculo-card {
  background: var(--card-bg, #fff); border-radius: 12px; padding: 0; overflow: hidden;
  box-shadow: 0 1px 8px rgba(0,0,0,.08); cursor: pointer;
  transition: transform .15s, box-shadow .15s;
  display: flex; flex-direction: column; align-items: center;
}
.vehiculo-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,.12); }
.vc-foto { width: 100%; height: 130px; background: #f1f5f9; display: flex; align-items: center; justify-content: center; overflow: hidden; }
.vc-img { width: 100%; height: 100%; object-fit: cover; }
.vc-placa { font-size: 22px; font-weight: 900; letter-spacing: 3px; padding: 10px 14px 4px; }
.vc-servicio { padding: 0 14px 6px; }
.vc-tiempo { font-size: 12px; color: #64748b; padding: 0 14px 4px; display: flex; align-items: center; gap: 4px; }
.vc-valor { font-size: 20px; font-weight: 800; color: #16a34a; padding: 0 14px 10px; }
.vc-action { width: 100%; padding: 0 14px 14px; }
.tag-cat { padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; }
.btn-cobrar { width: 100%; background: #3b82f6; color: #fff; border: none; border-radius: 8px; padding: 9px; font-size: 14px; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px; }
.btn-cobrar:hover { background: #2563eb; }

/* Buttons */
.btn-pq-primary { background: #3b82f6; color: #fff; border: none; border-radius: 8px; padding: 8px 18px; font-size: 14px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; white-space: nowrap; }
.btn-pq-primary:hover { background: #2563eb; }
.btn-pq-primary:disabled { opacity: .6; cursor: not-allowed; }
.btn-pq-ghost { background: transparent; border: 1.5px solid #94a3b8; color: inherit; border-radius: 8px; padding: 8px 14px; font-size: 13px; cursor: pointer; display: flex; align-items: center; gap: 6px; }
.btn-danger-ghost { border-color: #fca5a5; color: #dc2626; }

/* Modal */
.pq-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 16px; }
.pq-modal { background: var(--modal-bg, #fff); border-radius: 14px; width: 100%; max-width: 420px; overflow: hidden; }
.pq-modal-head { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--border, #e2e8f0); }
.pq-modal-head h3 { margin: 0; font-size: 17px; display: flex; align-items: center; gap: 8px; }
.btn-close { background: none; border: none; cursor: pointer; font-size: 18px; color: #64748b; }
.pq-modal-body { padding: 20px; display: flex; flex-direction: column; gap: 12px; }
.pq-modal-foot { display: flex; gap: 8px; justify-content: flex-end; padding: 14px 20px; border-top: 1px solid var(--border, #e2e8f0); flex-wrap: wrap; }
.pq-input { width: 100%; padding: 8px 12px; border: 1.5px solid var(--border, #e2e8f0); border-radius: 8px; font-size: 14px; background: var(--input-bg, #f8fafc); box-sizing: border-box; }
.pq-input:focus { outline: none; border-color: #3b82f6; }

.foto-resumen { width: 100%; height: 140px; border-radius: 8px; overflow: hidden; }
.foto-resumen img { width: 100%; height: 100%; object-fit: cover; }
.resumen-salida { background: #f8fafc; border-radius: 10px; padding: 14px; display: flex; flex-direction: column; gap: 8px; }
.rs-row { display: flex; justify-content: space-between; font-size: 14px; }
.rs-row span:first-child { color: #64748b; }
.rs-total { border-top: 1.5px solid #e2e8f0; padding-top: 8px; font-size: 16px; }
.rs-total strong { color: #16a34a; font-size: 20px; }

/* Cards */
.pq-card { background: var(--card-bg, #fff); border-radius: 12px; padding: 16px; box-shadow: 0 1px 6px rgba(0,0,0,.07); }

@media (max-width: 768px) {
  .kpi-bar { gap: 8px; }
  .kpi-card { min-width: calc(50% - 8px); padding: 12px 14px; }
  .vehiculos-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); }
}
@media (max-width: 576px) {
  .pq-view { padding: 10px; }
  .kpi-card { min-width: calc(50% - 4px); }
  .pq-modal { border-radius: 0; max-width: 100%; }
  .search-bar { flex-direction: column; }
  .pq-modal-foot { justify-content: stretch; }
  .pq-modal-foot > * { flex: 1; justify-content: center; }
}
</style>
