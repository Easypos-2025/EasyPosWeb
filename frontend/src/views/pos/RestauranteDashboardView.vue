<template>
  <div class="rdash-container">

    <!-- ── Header ──────────────────────────────────────────── -->
    <div class="rdash-header">
      <div>
        <h5 class="rdash-title">
          <i class="bi bi-shop-window me-2 text-warning"></i>Dashboard Restaurante
        </h5>
        <small class="text-muted">{{ fechaLabel }}</small>
      </div>
      <div class="rdash-header-right">
        <input type="date" v-model="fecha" class="form-control form-control-sm date-pick" @change="cargarTodo" />
        <button class="btn btn-sm btn-outline-secondary" @click="cargarTodo" :disabled="cargando">
          <i class="bi" :class="cargando ? 'bi-arrow-repeat spin' : 'bi-arrow-clockwise'"></i>
        </button>
      </div>
    </div>

    <!-- ── KPI Bar ──────────────────────────────────────────── -->
    <div class="kpi-bar">
      <div class="kpi-card kpi-ventas">
        <div class="kpi-icon"><i class="bi bi-cash-stack"></i></div>
        <div class="kpi-body">
          <div class="kpi-label">Ventas del día</div>
          <div class="kpi-value">{{ formatCurrency(kpis.ventas_facturas?.total + kpis.ventas_recibos?.total) }}</div>
          <div class="kpi-sub">{{ (kpis.ventas_facturas?.count || 0) + (kpis.ventas_recibos?.count || 0) }} transacciones</div>
        </div>
      </div>

      <div class="kpi-card kpi-facturas">
        <div class="kpi-icon"><i class="bi bi-file-earmark-text"></i></div>
        <div class="kpi-body">
          <div class="kpi-label">Facturas</div>
          <div class="kpi-value">{{ formatCurrency(kpis.ventas_facturas?.total) }}</div>
          <div class="kpi-sub">{{ kpis.ventas_facturas?.count || 0 }} documentos</div>
        </div>
      </div>

      <div class="kpi-card kpi-recibos">
        <div class="kpi-icon"><i class="bi bi-receipt"></i></div>
        <div class="kpi-body">
          <div class="kpi-label">Recibos</div>
          <div class="kpi-value">{{ formatCurrency(kpis.ventas_recibos?.total) }}</div>
          <div class="kpi-sub">{{ kpis.ventas_recibos?.count || 0 }} documentos</div>
        </div>
      </div>

      <div class="kpi-card kpi-mesas" @click="$router.push('/pos/mesas')" style="cursor:pointer">
        <div class="kpi-icon"><i class="bi bi-table"></i></div>
        <div class="kpi-body">
          <div class="kpi-label">Mesas</div>
          <div class="kpi-value">{{ kpis.mesas?.ocupadas || 0 }} <span class="kpi-denom">/ {{ kpis.mesas?.total || 0 }}</span></div>
          <div class="kpi-sub">
            <span class="dot-free"></span>{{ kpis.mesas?.libres || 0 }} libre
            <span class="dot-bill ms-2"></span>{{ kpis.mesas?.cuenta || 0 }} cuenta
          </div>
        </div>
      </div>

      <div class="kpi-card kpi-comandas">
        <div class="kpi-icon"><i class="bi bi-clipboard-list"></i></div>
        <div class="kpi-body">
          <div class="kpi-label">En cocina</div>
          <div class="kpi-value">{{ kpis.comandas_abiertas?.count || 0 }}</div>
          <div class="kpi-sub">{{ formatCurrency(kpis.comandas_abiertas?.total) }} en curso</div>
        </div>
      </div>

      <div class="kpi-card" :class="(kpis.stock_alertas || 0) > 0 ? 'kpi-alerta' : 'kpi-stock-ok'"
           @click="(kpis.stock_alertas || 0) > 0 && scrollTo('stock')" style="cursor:pointer">
        <div class="kpi-icon"><i class="bi bi-exclamation-triangle"></i></div>
        <div class="kpi-body">
          <div class="kpi-label">Stock crítico</div>
          <div class="kpi-value">{{ kpis.stock_alertas || 0 }}</div>
          <div class="kpi-sub">{{ (kpis.stock_alertas || 0) > 0 ? 'insumos bajo mínimo' : 'Todo en orden' }}</div>
        </div>
      </div>
    </div>

    <!-- ── Cuerpo ──────────────────────────────────────────── -->
    <div class="rdash-body">

      <!-- Col izquierda: mesas + últimas transacciones -->
      <div class="rdash-col-main">

        <!-- Mini mapa de mesas -->
        <div class="rdash-section">
          <div class="section-header">
            <span><i class="bi bi-table me-2"></i>Estado de mesas</span>
            <router-link to="/pos/mesas" class="btn btn-xs btn-outline-primary">
              Ver todas <i class="bi bi-arrow-right ms-1"></i>
            </router-link>
          </div>
          <div v-if="cargandoMesas" class="text-center py-3">
            <div class="spinner-border spinner-border-sm text-primary"></div>
          </div>
          <div v-else-if="!zonas.length" class="text-center py-3 text-muted small">
            Sin zonas configuradas. <router-link to="/pos/zonas">Crear zonas</router-link>
          </div>
          <div v-else>
            <div v-for="zona in zonas" :key="zona.id" class="zona-mini">
              <div class="zona-mini-header" :style="{ color: zona.color }">
                <i :class="`bi ${zona.icon}`"></i> {{ zona.name }}
              </div>
              <div class="mesas-mini-grid">
                <div
                  v-for="mesa in mesasPorZona(zona.id)"
                  :key="mesa.id"
                  class="mesa-mini"
                  :class="`status-${mesa.status}`"
                  :title="`${mesa.name} — ${statusLabel(mesa.status)}`"
                >
                  <div class="mesa-mini-name">{{ mesa.name }}</div>
                  <div class="mesa-mini-status"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Últimas transacciones -->
        <div class="rdash-section">
          <div class="section-header">
            <span><i class="bi bi-clock-history me-2"></i>Últimas transacciones</span>
            <span class="badge bg-secondary-subtle text-secondary">{{ fecha === hoy ? 'Hoy' : fecha }}</span>
          </div>
          <div v-if="cargandoTx" class="text-center py-3">
            <div class="spinner-border spinner-border-sm text-primary"></div>
          </div>
          <div v-else-if="!transacciones.length" class="text-center py-3 text-muted small">
            Sin transacciones para esta fecha
          </div>
          <div v-else class="tx-table-wrap">
            <table class="tx-table">
              <thead>
                <tr><th>Hora</th><th>Tipo</th><th>N°</th><th class="text-end">Total</th></tr>
              </thead>
              <tbody>
                <tr v-for="tx in transacciones" :key="tx.tipo + tx.numero">
                  <td class="tx-hora">{{ tx.hora?.substring(0,5) }}</td>
                  <td>
                    <span class="badge-tx" :class="tx.tipo === 'Factura' ? 'tx-fact' : 'tx-rec'">
                      {{ tx.tipo }}
                    </span>
                  </td>
                  <td class="tx-num">{{ tx.numero }}</td>
                  <td class="text-end tx-total">{{ formatCurrency(tx.total) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Col derecha: stock crítico + comandas abiertas -->
      <div class="rdash-col-side">

        <!-- Stock crítico -->
        <div class="rdash-section" id="stock">
          <div class="section-header">
            <span><i class="bi bi-exclamation-triangle me-2 text-danger"></i>Stock crítico</span>
            <span v-if="stockAlertas.length" class="badge bg-danger">{{ stockAlertas.length }}</span>
          </div>
          <div v-if="cargandoStock" class="text-center py-3">
            <div class="spinner-border spinner-border-sm text-danger"></div>
          </div>
          <div v-else-if="!stockAlertas.length" class="stock-ok">
            <i class="bi bi-check-circle-fill text-success"></i>
            <span>Todos los insumos en nivel adecuado</span>
          </div>
          <div v-else class="stock-list">
            <div v-for="item in stockAlertas" :key="item.id" class="stock-item">
              <div class="stock-item-info">
                <div class="stock-item-name">{{ item.name }}</div>
                <div class="stock-item-unit">{{ item.unit_name || '' }}</div>
              </div>
              <div class="stock-item-nums">
                <span class="stock-actual" :class="item.stock_qty <= 0 ? 'text-danger' : 'text-warning'">
                  {{ formatNum(item.stock_qty) }}
                </span>
                <span class="stock-sep">/</span>
                <span class="stock-min text-muted">{{ formatNum(item.min_stock) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Comandas abiertas hoy -->
        <div class="rdash-section">
          <div class="section-header">
            <span><i class="bi bi-clipboard-list me-2"></i>En cocina ahora</span>
            <span class="badge bg-warning text-dark">{{ comandasAbiertas.length }}</span>
          </div>
          <div v-if="cargandoCmd" class="text-center py-3">
            <div class="spinner-border spinner-border-sm text-warning"></div>
          </div>
          <div v-else-if="!comandasAbiertas.length" class="text-center py-3 text-muted small">
            Sin comandas abiertas
          </div>
          <div v-else class="cmd-list">
            <div v-for="cmd in comandasAbiertas" :key="cmd.order_number" class="cmd-item">
              <div class="cmd-table">
                <i class="bi bi-table me-1"></i>{{ cmd.table_name || 'Sin mesa' }}
              </div>
              <div class="cmd-meta">
                <span class="cmd-hora">{{ cmd.hora_apertura?.substring(0,5) }}</span>
                <span class="cmd-items">{{ cmd.item_count }} ítem(s)</span>
              </div>
              <div class="cmd-total">{{ formatCurrency(cmd.amount) }}</div>
            </div>
          </div>
        </div>

      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'
import { useCompanyStore } from '@/stores/companyStore'

const companyStore = useCompanyStore()
const selectedCid  = computed(() => companyStore.selectedCompany?.id || undefined)

const hoy = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Bogota' }).format(new Date())
const fecha = ref(hoy)
const cargando = ref(false)
const cargandoMesas = ref(false)
const cargandoTx = ref(false)
const cargandoStock = ref(false)
const cargandoCmd = ref(false)

const kpis = ref({})
const zonas = ref([])
const mesas = ref([])
const transacciones = ref([])
const stockAlertas = ref([])
const comandasAbiertas = ref([])

const fechaLabel = computed(() => {
  if (fecha.value === hoy) return 'Hoy — ' + new Date().toLocaleDateString('es-CO', { weekday: 'long', day: 'numeric', month: 'long' })
  return new Date(fecha.value + 'T12:00:00').toLocaleDateString('es-CO', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
})

function formatCurrency(val) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(val || 0)
}
function formatNum(val) {
  return Number(val || 0).toLocaleString('es-CO', { maximumFractionDigits: 2 })
}
function mesasPorZona(zoneId) {
  return mesas.value.filter(m => m.zone_id === zoneId && m.is_active)
}
function statusLabel(s) {
  return s === 'free' ? 'Libre' : s === 'occupied' ? 'Ocupada' : 'Cuenta pedida'
}
function scrollTo(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
}

async function cargarKpis() {
  cargando.value = true
  try {
    const res = await api.get('/api/pos-dashboard/kpis', { params: { fecha: fecha.value, company_id: selectedCid.value } })
    kpis.value = res.data
  } catch { showToast('Error cargando KPIs', 'error') }
  finally { cargando.value = false }
}

async function cargarMesas() {
  cargandoMesas.value = true
  try {
    const [rz, rm] = await Promise.all([
      api.get('/api/pos/zonas', { params: { company_id: selectedCid.value } }),
      api.get('/api/pos/mesas', { params: { company_id: selectedCid.value } }),
    ])
    zonas.value = rz.data.filter(z => z.is_active)
    mesas.value = rm.data
  } catch { /* silencioso */ }
  finally { cargandoMesas.value = false }
}

async function cargarTransacciones() {
  cargandoTx.value = true
  try {
    const res = await api.get('/api/pos-dashboard/ultimas-transacciones', { params: { fecha: fecha.value, company_id: selectedCid.value } })
    transacciones.value = res.data
  } catch { /* silencioso */ }
  finally { cargandoTx.value = false }
}

async function cargarStock() {
  cargandoStock.value = true
  try {
    const res = await api.get('/api/pos-dashboard/stock-alertas', { params: { company_id: selectedCid.value } })
    stockAlertas.value = res.data
  } catch { /* silencioso */ }
  finally { cargandoStock.value = false }
}

async function cargarComandas() {
  cargandoCmd.value = true
  try {
    const res = await api.get('/api/pos-dashboard/abiertas', { params: { company_id: selectedCid.value } })
    comandasAbiertas.value = res.data
  } catch { /* silencioso */ }
  finally { cargandoCmd.value = false }
}

async function cargarTodo() {
  await Promise.all([
    cargarKpis(),
    cargarMesas(),
    cargarTransacciones(),
    cargarStock(),
    cargarComandas(),
  ])
}

onMounted(cargarTodo)
</script>

<style scoped>
.rdash-container { padding: 1rem; max-width: 1400px; }

/* Header */
.rdash-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  margin-bottom: 1.25rem; flex-wrap: wrap; gap: .5rem;
}
.rdash-title { margin: 0; font-size: 1.1rem; font-weight: 700; }
.rdash-header-right { display: flex; gap: .4rem; align-items: center; }
.date-pick { width: 140px; }

/* ── KPI Bar ── */
.kpi-bar {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: .75rem;
  margin-bottom: 1.25rem;
}
.kpi-card {
  background: #fff; border-radius: 10px; border: 1px solid #e5e7eb;
  padding: .85rem .9rem; display: flex; align-items: flex-start; gap: .6rem;
  box-shadow: 0 1px 3px rgba(0,0,0,.05); transition: box-shadow .2s;
}
.kpi-card:hover { box-shadow: 0 3px 10px rgba(0,0,0,.1); }
.kpi-icon {
  width: 38px; height: 38px; border-radius: 8px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 1.1rem;
}
.kpi-ventas .kpi-icon   { background: #dcfce7; color: #16a34a; }
.kpi-facturas .kpi-icon { background: #dbeafe; color: #2563eb; }
.kpi-recibos .kpi-icon  { background: #ede9fe; color: #7c3aed; }
.kpi-mesas .kpi-icon    { background: #fef3c7; color: #d97706; }
.kpi-comandas .kpi-icon { background: #fce7f3; color: #db2777; }
.kpi-alerta .kpi-icon   { background: #fee2e2; color: #dc2626; }
.kpi-stock-ok .kpi-icon { background: #dcfce7; color: #16a34a; }

.kpi-body { min-width: 0; }
.kpi-label { font-size: .7rem; color: #6b7280; font-weight: 500; text-transform: uppercase; letter-spacing: .02em; }
.kpi-value { font-size: 1.05rem; font-weight: 700; line-height: 1.2; margin: .1rem 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.kpi-denom { font-size: .75rem; font-weight: 400; color: #9ca3af; }
.kpi-sub { font-size: .68rem; color: #9ca3af; display: flex; align-items: center; gap: 3px; flex-wrap: wrap; }

.dot-free  { width: 7px; height: 7px; border-radius: 50%; background: #16a34a; display: inline-block; }
.dot-bill  { width: 7px; height: 7px; border-radius: 50%; background: #d97706; display: inline-block; }

/* ── Body grid ── */
.rdash-body {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 1rem;
  align-items: start;
}
.rdash-col-main, .rdash-col-side { display: flex; flex-direction: column; gap: 1rem; }

/* Section */
.rdash-section {
  background: #fff; border-radius: 10px; border: 1px solid #e5e7eb;
  overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.05);
}
.section-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: .7rem 1rem; border-bottom: 1px solid #f3f4f6;
  font-weight: 600; font-size: .85rem; background: #fafafa;
}
.btn-xs { padding: .2rem .55rem; font-size: .75rem; border-radius: 6px; }

/* Mesas mini */
.zona-mini { padding: .7rem 1rem; border-bottom: 1px solid #f3f4f6; }
.zona-mini:last-child { border-bottom: none; }
.zona-mini-header { font-size: .75rem; font-weight: 600; margin-bottom: .5rem; display: flex; align-items: center; gap: .3rem; }
.mesas-mini-grid { display: flex; flex-wrap: wrap; gap: .35rem; }
.mesa-mini {
  width: 52px; border-radius: 6px; padding: .3rem .2rem;
  text-align: center; font-size: .65rem; font-weight: 600;
  border: 1.5px solid transparent; cursor: default;
}
.mesa-mini.status-free        { background: #dcfce7; border-color: #bbf7d0; color: #15803d; }
.mesa-mini.status-occupied    { background: #fee2e2; border-color: #fecaca; color: #b91c1c; }
.mesa-mini.status-bill_requested { background: #fef3c7; border-color: #fde68a; color: #b45309; }
.mesa-mini-name { font-size: .65rem; font-weight: 600; }
.mesa-mini-status { width: 6px; height: 6px; border-radius: 50%; margin: 2px auto 0; }
.status-free .mesa-mini-status        { background: #16a34a; }
.status-occupied .mesa-mini-status    { background: #dc2626; }
.status-bill_requested .mesa-mini-status { background: #d97706; }

/* Transacciones */
.tx-table-wrap { padding: .25rem 0; overflow-x: auto; }
.tx-table { width: 100%; border-collapse: collapse; font-size: .8rem; }
.tx-table th { padding: .35rem .75rem; color: #6b7280; font-weight: 600; font-size: .7rem; text-transform: uppercase; border-bottom: 1px solid #f3f4f6; }
.tx-table td { padding: .45rem .75rem; border-bottom: 1px solid #f9fafb; }
.tx-table tr:last-child td { border-bottom: none; }
.tx-hora  { color: #6b7280; font-size: .75rem; }
.tx-num   { color: #374151; font-family: monospace; }
.tx-total { font-weight: 600; color: #111827; }
.badge-tx { font-size: .65rem; padding: 2px 7px; border-radius: 10px; font-weight: 600; }
.tx-fact { background: #dbeafe; color: #1d4ed8; }
.tx-rec  { background: #ede9fe; color: #6d28d9; }

/* Stock */
.stock-ok {
  display: flex; align-items: center; gap: .5rem;
  padding: .85rem 1rem; font-size: .82rem; color: #374151;
}
.stock-list { padding: .25rem 0; }
.stock-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: .5rem 1rem; border-bottom: 1px solid #f9fafb;
}
.stock-item:last-child { border-bottom: none; }
.stock-item-name { font-size: .8rem; font-weight: 500; }
.stock-item-unit { font-size: .68rem; color: #9ca3af; }
.stock-item-nums { display: flex; align-items: center; gap: .2rem; font-size: .82rem; font-weight: 600; }
.stock-sep { color: #d1d5db; }
.stock-min { font-weight: 400; font-size: .75rem; }

/* Comandas */
.cmd-list { padding: .25rem 0; }
.cmd-item {
  display: flex; align-items: center; gap: .5rem;
  padding: .5rem 1rem; border-bottom: 1px solid #f9fafb;
}
.cmd-item:last-child { border-bottom: none; }
.cmd-table { font-weight: 600; font-size: .8rem; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cmd-meta { display: flex; flex-direction: column; align-items: flex-end; gap: 1px; }
.cmd-hora  { font-size: .7rem; color: #6b7280; }
.cmd-items { font-size: .65rem; color: #9ca3af; }
.cmd-total { font-weight: 700; font-size: .8rem; color: #111827; white-space: nowrap; }

/* Spinner */
.spin { animation: spin .8s linear infinite; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Responsive ── */
@media (max-width: 1100px) {
  .kpi-bar { grid-template-columns: repeat(3, 1fr); }
  .rdash-body { grid-template-columns: 1fr; }
  .rdash-col-side { grid-row: 2; }
}
@media (max-width: 768px) {
  .kpi-bar { grid-template-columns: repeat(2, 1fr); gap: .5rem; }
  .kpi-value { font-size: .9rem; }
  .rdash-body { grid-template-columns: 1fr; }
}
@media (max-width: 576px) {
  .kpi-bar { grid-template-columns: 1fr 1fr; gap: .4rem; }
  .kpi-card { padding: .6rem .65rem; }
  .kpi-icon { width: 32px; height: 32px; font-size: .95rem; }
  .kpi-value { font-size: .85rem; }
  .rdash-container { padding: .6rem; }
  .date-pick { width: 120px; }
}
</style>
