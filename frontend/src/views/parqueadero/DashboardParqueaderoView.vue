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
          <span class="kpi-val">${{ (stats.recaudo_dia || 0).toLocaleString('es-CO') }}</span>
          <span class="kpi-label">Recaudo Hoy</span>
        </div>
      </div>
      <!-- KPI Valor en Pista (calculado en tiempo real) -->
      <div class="kpi-card kpi-pista" v-if="activos.length">
        <i class="bi bi-stopwatch-fill kpi-icon"></i>
        <div class="kpi-body">
          <span class="kpi-val">${{ valorEnPista.toLocaleString('es-CO') }}</span>
          <span class="kpi-label">En Pista</span>
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

    <!-- Búsqueda: QR / Placa / Nro Recibo -->
    <div class="pq-card search-bar">
      <div class="search-group">
        <label class="search-label"><i class="bi bi-qr-code-scan"></i> QR / Token</label>
        <input v-model="busQR" class="search-input" placeholder="Escanea o escribe el token..."
               @keydown.enter="buscarPor('qr', busQR)" />
        <button class="btn-buscar" @click="buscarPor('qr', busQR)"><i class="bi bi-arrow-right"></i></button>
      </div>
      <div class="search-sep">|</div>
      <div class="search-group">
        <label class="search-label"><i class="bi bi-car-front-fill"></i> Placa</label>
        <input v-model="busPlaca" class="search-input pq-placa-mini" placeholder="AAA000"
               @input="busPlaca = busPlaca.toUpperCase()"
               @keydown.enter="buscarPor('placa', busPlaca)" />
        <button class="btn-buscar" @click="buscarPor('placa', busPlaca)"><i class="bi bi-arrow-right"></i></button>
      </div>
      <div class="search-sep">|</div>
      <div class="search-group">
        <label class="search-label"><i class="bi bi-receipt-cutoff"></i> Nro Recibo</label>
        <input v-model="busId" type="number" class="search-input" placeholder="Ej: 42"
               @keydown.enter="buscarPor('id', busId)" />
        <button class="btn-buscar" @click="buscarPor('id', busId)"><i class="bi bi-arrow-right"></i></button>
      </div>
    </div>

    <!-- Vehículos activos -->
    <div class="section-title">
      <h3><i class="bi bi-car-front-fill"></i> Vehículos en Parqueadero</h3>
      <div class="section-actions">
        <router-link to="/parqueadero/ingreso" class="btn-nuevo-ingreso">
          <i class="bi bi-box-arrow-in-right"></i> Ingresar Vehículo
        </router-link>
        <button class="btn-refresh" @click="cargar" :disabled="loading" title="Refrescar">
          <i class="bi bi-arrow-clockwise"></i>
        </button>
      </div>
    </div>

    <div v-if="loading" class="pq-loader">Cargando...</div>
    <div v-else-if="!activos.length" class="pq-empty">
      <i class="bi bi-car-front" style="font-size:2.5rem;opacity:.3"></i>
      <p>No hay vehículos activos en este momento</p>
      <router-link to="/parqueadero/ingreso" class="btn-nuevo-ingreso btn-nuevo-ingreso-lg">
        <i class="bi bi-box-arrow-in-right"></i> Ingresar primer vehículo
      </router-link>
    </div>

    <div v-else class="vehiculos-grid">
      <div v-for="v in activos" :key="v.id" class="vehiculo-card" @click="abrirSalida(v)">
        <div class="vc-foto">
          <img v-if="v.foto_url" :src="v.foto_url" class="vc-img" />
          <i v-else class="bi bi-car-front-fill" style="font-size:36px;color:#94a3b8"></i>
        </div>
        <div class="vc-id">#{{ v.id }}</div>
        <div class="vc-placa">{{ v.placa }}</div>
        <div class="vc-servicio">
          <span class="tag-cat" :style="{ background: (v.categoria_color || '#3b82f6') + '22', color: v.categoria_color || '#3b82f6' }">
            {{ v.categoria_nombre || v.servicio_nombre }}
          </span>
        </div>
        <div class="vc-tiempo"><i class="bi bi-clock"></i> {{ formatMinutos(minsTranscurridos(v)) }}</div>
        <div class="vc-valor">${{ calcValor(v).toLocaleString('es-CO') }}</div>
        <div class="vc-actions">
          <button class="btn-reimprimir" @click.stop="reimprimir(v)" title="Reimprimir ticket">
            <i class="bi bi-printer"></i>
          </button>
          <button class="btn-cobrar" @click.stop="abrirSalida(v)">
            <i class="bi bi-cash-coin"></i> Cobrar
          </button>
        </div>
      </div>
    </div>

    <!-- ══ Modal cobro / salida ══ -->
    <div v-if="modalSalida" class="pq-overlay" @click.self="cerrarModalSalida">
      <div class="pq-modal">
        <div class="pq-modal-head">
          <h3><i class="bi bi-cash-coin" style="color:#f59e0b"></i> Registrar Salida</h3>
          <button class="btn-close" @click="cerrarModalSalida"><i class="bi bi-x-lg"></i></button>
        </div>

        <div v-if="ingresoSeleccionado" class="pq-modal-body">
          <!-- Foto -->
          <div v-if="ingresoSeleccionado.foto_url" class="foto-resumen">
            <img :src="ingresoSeleccionado.foto_url" />
          </div>

          <!-- Resumen -->
          <div class="resumen-salida">
            <div class="rs-row rs-id"><span>Nro. Recibo</span><strong>#{{ ingresoSeleccionado.id }}</strong></div>
            <div class="rs-row"><span>Placa</span><strong>{{ ingresoSeleccionado.placa }}</strong></div>
            <div class="rs-row"><span>Servicio</span><span>{{ ingresoSeleccionado.servicio_nombre }}</span></div>
            <div class="rs-row"><span>Ingreso</span><span>{{ formatFechaHora(ingresoSeleccionado.hora_ingreso) }}</span></div>
            <div class="rs-row"><span>Tiempo</span><span>{{ formatMinutos(minsTranscurridos(ingresoSeleccionado)) }}</span></div>
            <div class="rs-row rs-total"><span>Valor a Cobrar</span><strong>${{ calcValor(ingresoSeleccionado).toLocaleString('es-CO') }}</strong></div>
          </div>

          <!-- Tipo documento: Factura / Recibo -->
          <div class="tipo-doc-row">
            <button
              class="btn-tipo-doc"
              :class="{ 'tipo-activo': pagoForm.tipo_documento === 'recibo' }"
              @click="pagoForm.tipo_documento = 'recibo'"
            >
              <i class="bi bi-journal-text"></i>
              <span>Recibo</span>
              <small>Sin DIAN</small>
            </button>
            <button
              class="btn-tipo-doc"
              :class="{ 'tipo-activo': pagoForm.tipo_documento === 'factura', 'tipo-disabled': !hasPE }"
              :disabled="!hasPE"
              :title="hasPE ? 'Factura electrónica DIAN' : 'La empresa no tiene POS Electrónico activo'"
              @click="hasPE && (pagoForm.tipo_documento = 'factura')"
            >
              <i class="bi bi-receipt-cutoff"></i>
              <span>Factura</span>
              <small>POS Electrónico</small>
              <span v-if="!hasPE" class="tipo-lock"><i class="bi bi-lock-fill"></i></span>
            </button>
          </div>

          <!-- Forma de pago -->
          <label class="field-label">Forma de Pago</label>
          <select v-model="pagoForm.forma_pago" class="pq-input">
            <option value="efectivo">Efectivo</option>
            <option value="transferencia">Transferencia</option>
            <option value="tarjeta">Tarjeta</option>
            <option value="otro">Otro</option>
          </select>

          <!-- Valor -->
          <label class="field-label">Valor Cobrado</label>
          <input type="number" v-model.number="pagoForm.valor_cobrado" class="pq-input pq-input-valor" />
        </div>

        <div class="pq-modal-foot">
          <template v-if="!confirmandoCancelar">
            <button class="btn-pq-ghost btn-danger-ghost" @click="confirmandoCancelar = true">
              <i class="bi bi-slash-circle"></i> Anular Ingreso
            </button>
            <button class="btn-pq-ghost" @click="ingresoSeleccionado && reimprimir(ingresoSeleccionado)" title="Reimprimir ticket">
              <i class="bi bi-printer"></i>
            </button>
            <button class="btn-pq-ghost" @click="cerrarModalSalida">Cerrar</button>
            <button class="btn-pq-primary" :disabled="pagando" @click="confirmarSalida">
              <i class="bi" :class="pagando ? 'bi-hourglass-split' : 'bi-check2-circle'"></i>
              {{ pagando ? 'Procesando...' : 'Confirmar Pago' }}
            </button>
          </template>
          <template v-else>
            <span class="confirm-warn">¿Anular #{{ ingresoSeleccionado?.id }}? El registro se conserva como "Anulado".</span>
            <button class="btn-pq-ghost" @click="confirmandoCancelar = false">No</button>
            <button class="btn-pq-ghost btn-danger-ghost" @click="ejecutarCancelacion">Sí, anular</button>
          </template>
        </div>
      </div>
    </div>

    <!-- ══ Componente reimprimir ticket ══ -->
    <ImprimirReciboParqueadero
      v-if="mostrarReimpresion && ingresoReimprimir"
      :datos="ingresoReimprimir"
      @close="mostrarReimpresion = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useCompanyStore } from '@/stores/companyStore'
import { useModuleName } from '@/composables/useModuleName'
import { showToast } from '@/utils/toast'
import api from '@/services/apis'
import ImprimirReciboParqueadero from '@/components/parqueadero/ImprimirReciboParqueadero.vue'

const companyStore = useCompanyStore()
const { moduleName } = useModuleName()

const stats   = ref({})
const activos = ref([])
const loading = ref(true)
const pagando = ref(false)
const modalSalida         = ref(false)
const confirmandoCancelar = ref(false)
const ingresoSeleccionado = ref(null)

// Reimprimir
const mostrarReimpresion = ref(false)
const ingresoReimprimir  = ref(null)

// Búsqueda
const busQR    = ref('')
const busPlaca = ref('')
const busId    = ref('')

const pagoForm = ref({ forma_pago: 'efectivo', valor_cobrado: 0, tipo_documento: 'recibo' })

const cid   = () => companyStore.selectedCompany?.id
const hasPE = computed(() => !!companyStore.billingConfig?.has_pos_electronico)

// ── Tiempo real ──────────────────────────────────────────────────────────────

const ahora = ref(Date.now())

function minsTranscurridos(v) {
  if (!v?.hora_ingreso) return 0
  const ingreso = new Date(String(v.hora_ingreso).replace(' ', 'T'))
  return Math.max(0, Math.floor((ahora.value - ingreso.getTime()) / 60000))
}

function calcValor(v) {
  const mins = minsTranscurridos(v)
  if (v.tipo_cobro === 'por_minuto') {
    return Math.round((v.tarifa_minuto || 0) * mins)
  }
  if (v.tipo_cobro === 'tarifa_plana') {
    const periodoMins = (v.periodo_horas || 12) * 60
    const periodos    = Math.max(1, Math.ceil(mins / periodoMins))
    return Math.round((v.tarifa_base || 0) + Math.max(0, periodos - 1) * (v.tarifa_adicional || 0))
  }
  if (v.tipo_cobro === 'mensualidad') return 0
  return v.valor_actual || 0
}

const valorEnPista = computed(() =>
  activos.value.reduce((sum, v) => sum + calcValor(v), 0)
)

let timerLocal    = null
let timerRefresh  = null

// ── Formateo ─────────────────────────────────────────────────────────────────

function formatFechaHora(dt) {
  if (!dt) return '—'
  const d = new Date(String(dt).replace(' ', 'T'))
  if (isNaN(d.getTime())) return String(dt)
  return d.toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' })
}

function formatMinutos(min) {
  if (!min) return '0 min'
  if (min < 60) return `${min} min`
  return `${Math.floor(min / 60)}h ${min % 60}min`
}

// ── Carga de datos ────────────────────────────────────────────────────────────

async function cargar(silent = false) {
  if (!cid()) return
  if (!silent) loading.value = true
  try {
    const [statsR, activosR] = await Promise.all([
      api.get('/api/parqueadero/stats',    { params: { company_id: cid() } }),
      api.get('/api/parqueadero/ingresos', { params: { company_id: cid(), estado: 'activo' } }),
    ])
    stats.value   = statsR.data
    activos.value = activosR.data
  } catch { /* silencioso */ }
  finally { if (!silent) loading.value = false }
}

// ── Búsqueda ──────────────────────────────────────────────────────────────────

async function buscarPor(tipo, valor) {
  const q = String(valor || '').trim().toUpperCase()
  if (!q) return

  let item = null

  if (tipo === 'id') {
    item = activos.value.find(v => String(v.id) === q)
    if (!item) {
      try {
        const { data } = await api.get(`/api/parqueadero/ingresos/${q}`, { params: { company_id: cid() } })
        if (data?.estado === 'activo') item = data
      } catch { /* no encontrado */ }
    }
  } else if (tipo === 'placa') {
    item = activos.value.find(v => v.placa === q)
  } else if (tipo === 'qr') {
    item = activos.value.find(v => v.placa === q || v.qr_token === q)
    if (!item) {
      try {
        const { data } = await api.get(`/api/parqueadero/ingresos/by-qr/${q}`, { params: { company_id: cid() } })
        item = data
      } catch { /* no es QR */ }
    }
  }

  if (item) {
    abrirSalida(item)
  } else {
    showToast('Vehículo no encontrado en parqueadero activo', 'warn')
  }
}

// ── Modal salida ──────────────────────────────────────────────────────────────

function cerrarModalSalida() {
  modalSalida.value         = false
  confirmandoCancelar.value = false
}

function abrirSalida(v) {
  ingresoSeleccionado.value = v
  pagoForm.value = {
    forma_pago:     'efectivo',
    valor_cobrado:  calcValor(v),
    tipo_documento: 'recibo',
  }
  confirmandoCancelar.value = false
  modalSalida.value         = true
}

async function confirmarSalida() {
  pagando.value = true
  try {
    await api.post(`/api/parqueadero/ingresos/${ingresoSeleccionado.value.id}/pagar`, {
      valor_cobrado: pagoForm.value.valor_cobrado,
      forma_pago:    pagoForm.value.forma_pago,
    }, { params: { company_id: cid() } })
    showToast(`Pago registrado — vehículo salió | Recibo #${ingresoSeleccionado.value.id}`, 'success')
    modalSalida.value = false
    cargar()
  } catch { showToast('Error al registrar pago', 'error') }
  finally { pagando.value = false }
}

async function ejecutarCancelacion() {
  try {
    await api.put(`/api/parqueadero/ingresos/${ingresoSeleccionado.value.id}/cancelar`, {}, {
      params: { company_id: cid() }
    })
    showToast(`Ingreso #${ingresoSeleccionado.value.id} anulado — el registro queda conservado`, 'success')
    cerrarModalSalida()
    cargar()
  } catch { showToast('Error al cancelar', 'error') }
}

// ── Reimprimir ticket ─────────────────────────────────────────────────────────

function reimprimir(v) {
  ingresoReimprimir.value = {
    id:                   v.id,
    placa:                v.placa,
    servicio_nombre:      v.servicio_nombre,
    hora_ingreso:         v.hora_ingreso,
    minutos_transcurridos: minsTranscurridos(v),
    valor_cobrado:        calcValor(v),
    forma_pago:           null,
    qr_token:             v.qr_token,
  }
  mostrarReimpresion.value = true
}

// ── Ciclo de vida ─────────────────────────────────────────────────────────────

watch(() => companyStore.selectedCompany?.id, id => { if (id) cargar() }, { immediate: true })

onMounted(() => {
  timerLocal   = setInterval(() => { ahora.value = Date.now() }, 30000)
  timerRefresh = setInterval(() => cargar(true), 90000)
})
onUnmounted(() => {
  clearInterval(timerLocal)
  clearInterval(timerRefresh)
})
</script>

<style scoped>
.pq-view { padding: 16px; }

/* ── KPI Bar ── */
.kpi-bar { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; }
.kpi-card { display: flex; align-items: center; gap: 12px; background: var(--card-bg,#fff); border-radius: 12px; padding: 14px 18px; flex: 1; min-width: 150px; box-shadow: 0 1px 6px rgba(0,0,0,.07); border-top: 3px solid transparent; }
.kpi-primary { border-top-color: #3b82f6; }
.kpi-info    { border-top-color: #06b6d4; }
.kpi-success { border-top-color: #22c55e; }
.kpi-money   { border-top-color: #f59e0b; }
.kpi-pista   { border-top-color: #8b5cf6; }
.kpi-warn    { border-top-color: #ef4444; }
.kpi-icon { font-size: 26px; }
.kpi-primary .kpi-icon { color: #3b82f6; }
.kpi-info    .kpi-icon { color: #06b6d4; }
.kpi-success .kpi-icon { color: #22c55e; }
.kpi-money   .kpi-icon { color: #f59e0b; }
.kpi-pista   .kpi-icon { color: #8b5cf6; }
.kpi-warn    .kpi-icon { color: #ef4444; }
.kpi-body  { display: flex; flex-direction: column; }
.kpi-val   { font-size: 22px; font-weight: 800; line-height: 1; }
.kpi-label { font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: .4px; }

/* ── Search bar ── */
.pq-card { background: var(--card-bg,#fff); border-radius: 12px; padding: 16px; box-shadow: 0 1px 6px rgba(0,0,0,.07); }
.search-bar { display: flex; align-items: center; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
.search-group { display: flex; align-items: center; gap: 6px; flex: 1; min-width: 160px; }
.search-label { font-size: 11px; font-weight: 700; color: #64748b; white-space: nowrap; display: flex; align-items: center; gap: 4px; }
.search-input { flex: 1; padding: 8px 10px; border: 1.5px solid var(--border,#e2e8f0); border-radius: 8px; font-size: 13px; background: var(--input-bg,#f8fafc); min-width: 0; outline: none; }
.search-input:focus { border-color: #3b82f6; }
.pq-placa-mini { text-transform: uppercase; font-weight: 700; letter-spacing: 1px; }
.search-sep { opacity: .2; font-size: 20px; flex-shrink: 0; }
.btn-buscar { background: #3b82f6; color: #fff; border: none; border-radius: 7px; padding: 7px 10px; cursor: pointer; flex-shrink: 0; }
.btn-buscar:hover { background: #2563eb; }

/* ── Section title ── */
.section-title { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.section-title h3 { margin: 0; font-size: 16px; font-weight: 700; display: flex; align-items: center; gap: 8px; }
.section-actions { display: flex; align-items: center; gap: 8px; }
.btn-refresh { background: none; border: 1px solid var(--border,#e2e8f0); border-radius: 8px; padding: 6px 10px; cursor: pointer; font-size: 16px; }

/* Botón acceso rápido a Ingresar */
.btn-nuevo-ingreso {
  display: inline-flex; align-items: center; gap: 6px;
  background: #3b82f6; color: #fff;
  border: none; border-radius: 8px;
  padding: 8px 16px; font-size: 13px; font-weight: 600;
  cursor: pointer; text-decoration: none;
  transition: background .15s;
}
.btn-nuevo-ingreso:hover { background: #2563eb; color: #fff; }
.btn-nuevo-ingreso-lg { margin-top: 16px; padding: 12px 24px; font-size: 15px; }

.pq-loader { text-align: center; padding: 60px; opacity: .5; }
.pq-empty  { text-align: center; padding: 60px 20px; opacity: .5; display: flex; flex-direction: column; align-items: center; }
.pq-empty i { display: block; margin-bottom: 12px; }

/* ── Grilla vehículos ── */
.vehiculos-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 14px; }
.vehiculo-card {
  background: var(--card-bg,#fff); border-radius: 12px; overflow: hidden;
  box-shadow: 0 1px 8px rgba(0,0,0,.08); cursor: pointer;
  transition: transform .15s, box-shadow .15s;
  display: flex; flex-direction: column; align-items: center;
}
.vehiculo-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,.12); }
.vc-foto  { width: 100%; height: 130px; background: #f1f5f9; display: flex; align-items: center; justify-content: center; overflow: hidden; }
.vc-img   { width: 100%; height: 100%; object-fit: cover; }
.vc-id    { font-size: 11px; font-weight: 700; color: #94a3b8; padding: 8px 14px 0; align-self: flex-start; letter-spacing: .5px; }
.vc-placa { font-size: 24px; font-weight: 900; letter-spacing: 3px; padding: 2px 14px 4px; }
.vc-servicio { padding: 0 14px 6px; }
.vc-tiempo   { font-size: 12px; color: #64748b; padding: 0 14px 4px; display: flex; align-items: center; gap: 4px; }
.vc-valor    { font-size: 20px; font-weight: 800; color: #16a34a; padding: 0 14px 10px; }
.vc-actions  { width: 100%; padding: 0 14px 14px; display: flex; gap: 6px; }
.tag-cat { padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; }

.btn-cobrar {
  flex: 1; background: #3b82f6; color: #fff; border: none;
  border-radius: 8px; padding: 9px; font-size: 14px; font-weight: 600;
  cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px;
}
.btn-cobrar:hover { background: #2563eb; }

.btn-reimprimir {
  background: #f1f5f9; color: #64748b; border: 1px solid #e2e8f0;
  border-radius: 8px; padding: 9px 10px; font-size: 14px;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: all .15s; flex-shrink: 0;
}
.btn-reimprimir:hover { background: #e2e8f0; color: #1e293b; }

/* ── Buttons ── */
.btn-pq-primary { background: #3b82f6; color: #fff; border: none; border-radius: 8px; padding: 8px 18px; font-size: 14px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; white-space: nowrap; }
.btn-pq-primary:hover { background: #2563eb; }
.btn-pq-primary:disabled { opacity: .6; cursor: not-allowed; }
.btn-pq-ghost { background: transparent; border: 1.5px solid #94a3b8; color: inherit; border-radius: 8px; padding: 8px 14px; font-size: 13px; cursor: pointer; display: flex; align-items: center; gap: 6px; }
.btn-danger-ghost { border-color: #fca5a5; color: #dc2626; }

/* ── Modal ── */
.pq-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 16px; }
.pq-modal   { background: var(--modal-bg,#fff); border-radius: 14px; width: 100%; max-width: 440px; overflow: hidden; max-height: 92vh; display: flex; flex-direction: column; }
.pq-modal-head { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--border,#e2e8f0); flex-shrink: 0; }
.pq-modal-head h3 { margin: 0; font-size: 17px; display: flex; align-items: center; gap: 8px; }
.btn-close { background: none; border: none; cursor: pointer; font-size: 18px; color: #64748b; }
.pq-modal-body { padding: 20px; display: flex; flex-direction: column; gap: 12px; overflow-y: auto; }
.pq-modal-foot { display: flex; gap: 8px; justify-content: flex-end; padding: 14px 20px; border-top: 1px solid var(--border,#e2e8f0); flex-wrap: wrap; flex-shrink: 0; }

.foto-resumen { width: 100%; height: 140px; border-radius: 8px; overflow: hidden; flex-shrink: 0; }
.foto-resumen img { width: 100%; height: 100%; object-fit: cover; }

.resumen-salida { background: #f8fafc; border-radius: 10px; padding: 14px; display: flex; flex-direction: column; gap: 8px; }
.rs-row { display: flex; justify-content: space-between; font-size: 14px; }
.rs-row span:first-child { color: #64748b; }
.rs-id strong { font-size: 18px; font-weight: 900; color: #1e3a5f; letter-spacing: 1px; }
.rs-total { border-top: 1.5px solid #e2e8f0; padding-top: 8px; font-size: 16px; }
.rs-total strong { color: #16a34a; font-size: 20px; }

.field-label { font-size: 12px; font-weight: 600; color: #475569; }
.pq-input { width: 100%; padding: 8px 12px; border: 1.5px solid var(--border,#e2e8f0); border-radius: 8px; font-size: 14px; background: var(--input-bg,#f8fafc); box-sizing: border-box; outline: none; }
.pq-input:focus { border-color: #3b82f6; }
.pq-input-valor { font-size: 20px; font-weight: 700; }

/* ── Tipo documento ── */
.tipo-doc-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.btn-tipo-doc {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 4px; padding: 12px 8px;
  border: 2px solid var(--border,#e2e8f0); border-radius: 10px;
  background: var(--card-bg,#fff); cursor: pointer;
  transition: all .2s; position: relative;
  font-family: inherit;
}
.btn-tipo-doc i      { font-size: 22px; color: #64748b; }
.btn-tipo-doc span   { font-size: 14px; font-weight: 700; color: #374151; }
.btn-tipo-doc small  { font-size: 10px; color: #94a3b8; }
.btn-tipo-doc:hover:not(.tipo-disabled) { border-color: #93c5fd; background: #eff6ff; }
.tipo-activo { border-color: #3b82f6 !important; background: #eff6ff !important; }
.tipo-activo i, .tipo-activo span { color: #1d4ed8; }
.tipo-disabled { opacity: .5; cursor: not-allowed; }
.tipo-lock { position: absolute; top: 6px; right: 8px; font-size: 11px; color: #94a3b8; }

.confirm-warn { flex: 1; font-size: 13px; color: #dc2626; font-weight: 600; display: flex; align-items: center; }

/* ── Responsive ── */
@media (max-width: 768px) {
  .kpi-bar { gap: 8px; }
  .kpi-card { min-width: calc(50% - 8px); padding: 12px 14px; }
  .vehiculos-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); }
  .search-bar { gap: 8px; }
  .search-sep { display: none; }
  .btn-nuevo-ingreso span { display: none; }
}
@media (max-width: 576px) {
  .pq-view { padding: 10px; }
  .kpi-card { min-width: calc(50% - 4px); }
  .pq-modal { border-radius: 0; max-width: 100%; max-height: 100vh; }
  .pq-modal-foot { justify-content: stretch; }
  .pq-modal-foot > * { flex: 1; justify-content: center; }
  .search-group { min-width: 100%; }
  .btn-nuevo-ingreso { padding: 8px 12px; }
}
</style>
