<template>
  <div class="dash-sc">

    <!-- Marca de agua -->
    <div class="wm-bg" aria-hidden="true">
      <i class="bi bi-car-front   wm-icon-1"></i>
      <i class="bi bi-tools       wm-icon-2"></i>
      <i class="bi bi-droplet     wm-icon-3"></i>
    </div>

    <!-- Header -->
    <div class="dash-header">
      <div class="dash-header-left">
        <h6 class="dash-empresa">{{ empresa }}</h6>
        <span class="dash-perfil-tag">
          <i class="bi bi-tools"></i> Talleres / Lavaderos / Latonería
        </span>
      </div>
      <span class="dash-fecha">{{ fechaHoy }}</span>
    </div>

    <!-- Accesos directos -->
    <p class="section-label">
      <i class="bi bi-lightning-charge-fill"></i> Accesos directos
    </p>
    <div class="accesos-grid">
      <button class="acceso-card" @click="ir('/talleres/ordenes')">
        <div class="ac-icon orange"><i class="bi bi-clipboard2-plus-fill"></i></div>
        <span class="ac-label">Nueva<br>Orden</span>
        <i class="bi bi-chevron-right ac-arrow"></i>
      </button>
      <button class="acceso-card" @click="showSearch = true">
        <div class="ac-icon blue"><i class="bi bi-search"></i></div>
        <span class="ac-label">Buscar<br>Órdenes</span>
        <i class="bi bi-chevron-right ac-arrow"></i>
      </button>
      <button class="acceso-card" @click="ir('/talleres/caja')">
        <div class="ac-icon purple"><i class="bi bi-cash-stack"></i></div>
        <span class="ac-label">Cierre<br>de Caja</span>
        <i class="bi bi-chevron-right ac-arrow"></i>
      </button>
      <button class="acceso-card" @click="ir('/talleres/convenios')">
        <div class="ac-icon green"><i class="bi bi-building-fill"></i></div>
        <span class="ac-label">Convenios</span>
        <i class="bi bi-chevron-right ac-arrow"></i>
      </button>
      <button class="acceso-card" @click="ir('/talleres/liquidacion')">
        <div class="ac-icon amber"><i class="bi bi-cash-coin"></i></div>
        <span class="ac-label">Liquidar<br>Operarios</span>
        <i class="bi bi-chevron-right ac-arrow"></i>
      </button>
    </div>

    <!-- KPI Bar -->
    <p class="section-label" style="margin-top:18px">
      <i class="bi bi-bar-chart-line-fill"></i> Estado del taller hoy
      <button class="refresh-btn" :class="{ spin: loadingKpi }" @click="cargarKpi(false)" title="Actualizar">
        <i class="bi bi-arrow-clockwise"></i>
      </button>
    </p>

    <div class="kpi-grid">

      <!-- Órdenes abiertas hoy -->
      <button class="kpi-card kpi-blue" :disabled="loadingKpi" @click="abrirModal('abiertas')">
        <div class="kpi-icon"><i class="bi bi-clipboard2-plus-fill"></i></div>
        <div class="kpi-body">
          <span class="kpi-label">Órdenes abiertas hoy</span>
          <span class="kpi-value">
            <i v-if="loadingKpi" class="bi bi-hourglass-split spin"></i>
            <template v-else>{{ kpi.ordenes_hoy }}</template>
          </span>
          <span class="kpi-sub">Aperturadas en el día</span>
        </div>
        <i class="bi bi-chevron-right kpi-arrow"></i>
      </button>

      <!-- Vehículos en patio -->
      <button class="kpi-card kpi-orange" :disabled="loadingKpi" @click="abrirModal('en_proceso')">
        <div class="kpi-icon"><i class="bi bi-car-front-fill"></i></div>
        <div class="kpi-body">
          <span class="kpi-label">Vehículos en patio</span>
          <span class="kpi-value">
            <i v-if="loadingKpi" class="bi bi-hourglass-split spin"></i>
            <template v-else>{{ kpi.en_proceso }}</template>
          </span>
          <span class="kpi-sub">En proceso</span>
        </div>
        <i class="bi bi-chevron-right kpi-arrow"></i>
      </button>

      <!-- Listos para entregar -->
      <button class="kpi-card kpi-green" :disabled="loadingKpi" @click="abrirModal('listos')">
        <div class="kpi-icon"><i class="bi bi-check-circle-fill"></i></div>
        <div class="kpi-body">
          <span class="kpi-label">Listos para entregar</span>
          <span class="kpi-value">
            <i v-if="loadingKpi" class="bi bi-hourglass-split spin"></i>
            <template v-else>{{ kpi.listos_entrega }}</template>
          </span>
          <span class="kpi-sub">Terminados, sin entregar</span>
        </div>
        <i class="bi bi-chevron-right kpi-arrow"></i>
      </button>

      <!-- CxC Convenios -->
      <button class="kpi-card kpi-amber" :disabled="loadingKpi" @click="abrirModal('convenios')">
        <div class="kpi-icon"><i class="bi bi-building-fill"></i></div>
        <div class="kpi-body">
          <span class="kpi-label">Convenios pendientes</span>
          <span class="kpi-value">
            <i v-if="loadingKpi" class="bi bi-hourglass-split spin"></i>
            <template v-else>{{ kpi.convenios_pendientes }}</template>
          </span>
          <span class="kpi-sub">Órdenes por facturar</span>
        </div>
        <i class="bi bi-chevron-right kpi-arrow"></i>
      </button>

      <!-- Repuestos bajo stock -->
      <button class="kpi-card kpi-red" :disabled="loadingKpi" @click="abrirModal('stock')">
        <div class="kpi-icon"><i class="bi bi-exclamation-triangle-fill"></i></div>
        <div class="kpi-body">
          <span class="kpi-label">Repuestos bajo stock</span>
          <span class="kpi-value">
            <i v-if="loadingKpi" class="bi bi-hourglass-split spin"></i>
            <template v-else>{{ kpi.bajo_stock }}</template>
          </span>
          <span class="kpi-sub">Por debajo del mínimo</span>
        </div>
        <i class="bi bi-chevron-right kpi-arrow"></i>
      </button>

    </div>

    <!-- Modal detalle -->
    <Teleport to="body">
      <div v-if="modal.visible" class="modal-overlay" @click.self="cerrarModal">
        <div class="modal-panel">
          <div class="modal-head">
            <span class="modal-title">
              <i :class="modal.icono"></i> {{ modal.titulo }}
            </span>
            <div class="modal-head-actions">
              <button
                v-if="!modal.loading && modal.items.length > 0"
                class="btn-print" @click="imprimirModal"
              >
                <i class="bi bi-printer-fill"></i>
                <span class="btn-txt">Imprimir</span>
              </button>
              <button class="modal-close" @click="cerrarModal">
                <i class="bi bi-x-lg"></i>
              </button>
            </div>
          </div>

          <div v-if="modal.loading" class="modal-loading">
            <i class="bi bi-hourglass-split spin"></i> Cargando...
          </div>
          <div v-else-if="modal.items.length === 0" class="modal-empty">
            <i class="bi bi-check-circle"></i> Sin registros
          </div>

          <div v-if="!modal.loading && modal.items.length > 0" class="modal-scroll" id="print-area">
            <table class="det-table">
              <thead>
                <tr>
                  <th v-for="col in modal.cols" :key="col.key">{{ col.label }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="it in modal.items" :key="it.id"
                    style="cursor:pointer"
                    @click="irOrden(it.id)">
                  <td v-for="col in modal.cols" :key="col.key">
                    <template v-if="col.type === 'badge'">
                      <span :class="['badge-estado', `be-${it[col.key]}`]">{{ labelEstado(it[col.key]) }}</span>
                    </template>
                    <template v-else-if="col.type === 'money'">
                      {{ fmt(it[col.key]) }}
                    </template>
                    <template v-else-if="col.type === 'date'">
                      {{ fmtFecha(it[col.key]) }}
                    </template>
                    <template v-else>{{ it[col.key] ?? '—' }}</template>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-if="!modal.loading && modal.items.length > 0" class="modal-foot">
            {{ modal.items.length }} registro{{ modal.items.length !== 1 ? 's' : '' }}
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Modal búsqueda de órdenes -->
    <SearchOrdenesModal v-if="showSearch" @close="showSearch = false" />

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useCompanyStore } from '@/stores/companyStore'
import api from '@/services/apis'
import SearchOrdenesModal from '@/components/talleres/SearchOrdenesModal.vue'

const companyStore = useCompanyStore()
const router       = useRouter()

const empresa   = computed(() => companyStore.selectedCompany?.name ?? '')
const companyId = computed(() => companyStore.selectedCompany?.id)

const fechaHoy = computed(() =>
  new Intl.DateTimeFormat('es-CO', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
  }).format(new Date())
)

const showSearch = ref(false)

function ir(ruta)     { router.push(ruta) }
function irOrden(id)  { cerrarModal(); router.push(`/talleres/ordenes?id=${id}`) }

// ── KPI ────────────────────────────────────────────────────────────────────
const loadingKpi = ref(false)
const kpi = ref({
  ordenes_hoy: 0, en_proceso: 0, listos_entrega: 0,
  convenios_pendientes: 0, bajo_stock: 0,
})

async function cargarKpi(silencioso = false) {
  if (!companyId.value) return
  if (!silencioso) loadingKpi.value = true
  try {
    const { data } = await api.get('/api/talleres/kpi', {
      params: { company_id: companyId.value }
    })
    kpi.value = data
  } catch { /* silencioso */ } finally {
    loadingKpi.value = false
  }
}

let _timer = null
function _startRefresh() { _stopRefresh(); _timer = setInterval(() => cargarKpi(true), 20000) }
function _stopRefresh()  { if (_timer) { clearInterval(_timer); _timer = null } }
function _onVisible()    { if (!document.hidden) cargarKpi(true) }

onMounted(() => { cargarKpi(); _startRefresh(); document.addEventListener('visibilitychange', _onVisible) })
onUnmounted(() => { _stopRefresh(); document.removeEventListener('visibilitychange', _onVisible) })
watch(companyId, v => { if (v) { cargarKpi(); _startRefresh() } })

// ── Modal ──────────────────────────────────────────────────────────────────
const COLS_ORDENES = [
  { key: 'numero_orden',    label: 'N° Orden' },
  { key: 'placa_vehiculo',  label: 'Placa' },
  { key: 'cliente_nombre',  label: 'Cliente' },
  { key: 'fecha_ingreso',   label: 'Ingreso',  type: 'date' },
  { key: 'jefe_nombre',     label: 'Jefe' },
  { key: 'total_orden',     label: 'Total',    type: 'money' },
  { key: 'estado',          label: 'Estado',   type: 'badge' },
]

const CFG = {
  abiertas:  { titulo: 'Órdenes Abiertas Hoy',      icono: 'bi bi-clipboard2-plus-fill',     endpoint: '/api/talleres/ordenes', params: { estado: 'abierta' },     cols: COLS_ORDENES },
  en_proceso:{ titulo: 'Vehículos en Patio',         icono: 'bi bi-car-front-fill',           endpoint: '/api/talleres/ordenes', params: { estado: 'en_proceso' },   cols: COLS_ORDENES },
  listos:    { titulo: 'Listos para Entregar',       icono: 'bi bi-check-circle-fill',        endpoint: '/api/talleres/ordenes', params: { estado: 'terminada' },    cols: COLS_ORDENES },
  convenios: { titulo: 'Órdenes Convenio Pendientes',icono: 'bi bi-building-fill',            endpoint: '/api/talleres/ordenes', params: { estado_fact: 'convenio_pendiente' }, cols: COLS_ORDENES },
  stock:     { titulo: 'Repuestos Bajo Stock',       icono: 'bi bi-exclamation-triangle-fill',endpoint: null, params: {},                           cols: [] },
}

const modal = ref({ visible: false, tipo: '', titulo: '', icono: '', loading: false, items: [], cols: [] })

async function abrirModal(tipo) {
  const cfg = CFG[tipo]
  if (!cfg.endpoint) return
  modal.value = { visible: true, tipo, titulo: cfg.titulo, icono: cfg.icono, loading: true, items: [], cols: cfg.cols }
  document.body.style.overflow = 'hidden'
  try {
    const { data } = await api.get(cfg.endpoint, {
      params: { company_id: companyId.value, page_size: 100, ...cfg.params }
    })
    modal.value.items = data.items ?? data
  } catch {
    modal.value.items = []
  } finally {
    modal.value.loading = false
  }
}

function cerrarModal() { modal.value.visible = false; document.body.style.overflow = '' }

// ── Helpers ────────────────────────────────────────────────────────────────
const LABELS_ESTADO = {
  abierta: 'Abierta', en_proceso: 'En proceso', terminada: 'Terminada',
  entregada: 'Entregada', cancelada: 'Cancelada',
}
function labelEstado(v) { return LABELS_ESTADO[v] ?? v }

function fmt(v) {
  if (v == null || v === '') return '—'
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v)
}
function fmtFecha(v) {
  if (!v) return '—'
  return new Intl.DateTimeFormat('es-CO', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(v))
}

function imprimirModal() {
  const area = document.getElementById('print-area')
  if (!area) return
  const win = window.open('', '_blank', 'width=960,height=600')
  win.document.write(`<!DOCTYPE html><html><head><meta charset="utf-8">
    <title>${modal.value.titulo}</title>
    <style>
      body { font-family: Arial, sans-serif; font-size: 12px; margin: 16px; color: #222; }
      h2 { font-size: 14px; margin: 0 0 4px; }
      p  { font-size: 11px; color: #666; margin: 0 0 12px; }
      table { width: 100%; border-collapse: collapse; }
      th { background: #1e3a5f; color: #fff; padding: 6px 8px; text-align: left; font-size: 11px; }
      td { padding: 5px 8px; border-bottom: 1px solid #e2e8f0; font-size: 11.5px; }
      tr:nth-child(even) td { background: #f8fafc; }
    </style></head><body>
    <h2>${empresa.value} — ${modal.value.titulo}</h2>
    <p>Generado: ${new Date().toLocaleString('es-CO')}</p>
    ${area.innerHTML}
    </body></html>`)
  win.document.close(); win.focus()
  setTimeout(() => { win.print(); win.close() }, 400)
}
</script>

<style scoped>
/* ── Contenedor ── */
.dash-sc {
  position: relative;
  min-height: 80vh;
  padding: 0 24px 48px;
  overflow: hidden;
}

/* ── Marca de agua ── */
.wm-bg { position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden; }
.wm-icon-1 { position: absolute; font-size: 420px; color: #1e3a5f; opacity: 0.04;  bottom: -80px; right: -60px; transform: rotate(-8deg); }
.wm-icon-2 { position: absolute; font-size: 160px; color: #ea580c; opacity: 0.045; top: 50px;  left: -20px; transform: rotate(15deg); }
.wm-icon-3 { position: absolute; font-size: 100px; color: #3b82f6; opacity: 0.045; top: 200px; right: 22%;  transform: rotate(-25deg); }

/* ── Header ── */
.dash-header {
  position: relative; z-index: 1;
  display: flex; align-items: flex-start; justify-content: space-between; gap: 12px;
  padding: 16px 0 12px; border-bottom: 1px solid #e2e8f0; margin-bottom: 14px;
}
.dash-empresa    { margin: 0 0 4px; font-size: 20px; font-weight: 700; color: #1e3a5f; line-height: 1.2; }
.dash-perfil-tag {
  display: inline-flex; align-items: center; gap: 5px; font-size: 12px; font-weight: 600;
  color: #ea580c; background: #fff7ed; border: 1px solid #fdba74;
  border-radius: 20px; padding: 2px 10px; text-transform: uppercase; letter-spacing: 0.5px;
}
.dash-fecha { font-size: 13px; color: #64748b; white-space: nowrap; padding-top: 2px; text-transform: capitalize; }

/* ── Section label ── */
.section-label {
  position: relative; z-index: 1;
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.8px; color: #64748b; margin: 0 0 8px;
  display: flex; align-items: center; gap: 6px;
}
.section-label .bi { color: #ea580c; font-size: 13px; }
.refresh-btn {
  margin-left: auto; background: none; border: none; cursor: pointer;
  font-size: 14px; color: #94a3b8; padding: 0; line-height: 1;
  transition: color 0.2s;
}
.refresh-btn:hover { color: #1e3a5f; }
.refresh-btn.spin i { display: inline-block; animation: spin 1s linear infinite; }

/* ── Accesos directos ── */
.accesos-grid {
  position: relative; z-index: 1;
  display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 0;
}
.acceso-card {
  display: inline-flex; align-items: center; gap: 8px;
  background: #fff; border: 1.5px solid #e2e8f0; border-radius: 10px;
  padding: 8px 14px; cursor: pointer; text-align: left;
  transition: all 0.18s ease; box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  flex: 1; min-width: 130px;
}
.acceso-card:hover { box-shadow: 0 4px 14px rgba(0,0,0,0.10); border-color: #1e3a5f; }
.ac-icon {
  flex-shrink: 0; width: 30px; height: 30px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center; font-size: 15px;
}
.ac-icon.orange { background: #fff7ed; color: #ea580c; }
.ac-icon.blue   { background: #dbeafe; color: #1d4ed8; }
.ac-icon.green  { background: #d1fae5; color: #065f46; }
.ac-icon.amber  { background: #fef3c7; color: #d97706; }
.ac-icon.purple { background: #f3e8ff; color: #7c3aed; }
.ac-label  { flex: 1; font-size: 13px; font-weight: 700; color: #1e3a5f; line-height: 1.2; }
.ac-arrow  { font-size: 11px; color: #cbd5e1; flex-shrink: 0; }

/* ── KPI grid ── */
.kpi-grid {
  position: relative; z-index: 1;
  display: grid; grid-template-columns: 1fr; gap: 10px;
}
.kpi-card {
  display: flex; align-items: center; gap: 10px;
  background: #fff; border: 1.5px solid #e2e8f0; border-radius: 12px;
  padding: 12px 10px; cursor: pointer; text-align: left; width: 100%;
  transition: all 0.2s ease; box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.kpi-card:hover  { transform: translateY(-2px); box-shadow: 0 4px 14px rgba(0,0,0,0.10); }
.kpi-card:disabled { cursor: default; transform: none; }
.kpi-icon {
  flex-shrink: 0; width: 36px; height: 36px; border-radius: 9px;
  display: flex; align-items: center; justify-content: center; font-size: 17px;
}
/* Variantes de color */
.kpi-blue   { border-left: 4px solid #3b82f6; }
.kpi-blue   .kpi-icon { background: #dbeafe; color: #1d4ed8; }
.kpi-blue:hover   { box-shadow: 0 6px 20px rgba(59,130,246,0.18); }
.kpi-orange { border-left: 4px solid #f97316; }
.kpi-orange .kpi-icon { background: #ffedd5; color: #ea580c; }
.kpi-orange:hover { box-shadow: 0 6px 20px rgba(249,115,22,0.18); }
.kpi-green  { border-left: 4px solid #22c55e; }
.kpi-green  .kpi-icon { background: #dcfce7; color: #16a34a; }
.kpi-green:hover  { box-shadow: 0 6px 20px rgba(34,197,94,0.18); }
.kpi-amber  { border-left: 4px solid #f59e0b; }
.kpi-amber  .kpi-icon { background: #fef3c7; color: #d97706; }
.kpi-amber:hover  { box-shadow: 0 6px 20px rgba(245,158,11,0.18); }
.kpi-red    { border-left: 4px solid #ef4444; }
.kpi-red    .kpi-icon { background: #fee2e2; color: #dc2626; }
.kpi-red:hover    { box-shadow: 0 6px 20px rgba(239,68,68,0.18); }

.kpi-body  { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px; }
.kpi-label { font-size: 10px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.4px; }
.kpi-value { font-size: 22px; font-weight: 800; color: #0f172a; line-height: 1.1; }
.kpi-sub   { font-size: 10px; color: #94a3b8; }
.kpi-arrow { font-size: 13px; color: #cbd5e1; flex-shrink: 0; }

/* ── Badges estado ── */
.badge-estado { display: inline-block; padding: 2px 8px; border-radius: 20px; font-size: 11px; font-weight: 600; }
.be-abierta    { background: #dbeafe; color: #1d4ed8; }
.be-en_proceso { background: #ffedd5; color: #ea580c; }
.be-terminada  { background: #dcfce7; color: #16a34a; }
.be-entregada  { background: #f0fdf4; color: #15803d; }
.be-cancelada  { background: #fee2e2; color: #dc2626; }

/* ── Spinner ── */
.spin { display: inline-block; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Modal ── */
.modal-overlay {
  position: fixed; inset: 0; z-index: 9000;
  background: rgba(15,36,72,0.55); backdrop-filter: blur(3px);
  display: flex; align-items: flex-end;
}
.modal-panel {
  width: 100%; max-height: 90vh; background: #fff;
  border-radius: 20px 20px 0 0; display: flex; flex-direction: column;
  box-shadow: 0 -8px 40px rgba(0,0,0,0.20); animation: slideUp 0.25s ease;
}
@keyframes slideUp { from { transform: translateY(100%); } to { transform: translateY(0); } }
.modal-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 20px 14px; border-bottom: 1px solid #e2e8f0; flex-shrink: 0;
}
.modal-title { font-size: 15px; font-weight: 700; color: #1e3a5f; display: flex; align-items: center; gap: 8px; }
.modal-head-actions { display: flex; align-items: center; gap: 8px; }
.btn-print {
  display: flex; align-items: center; gap: 6px;
  background: #1e3a5f; color: #fff; border: none; border-radius: 8px;
  padding: 6px 12px; font-size: 13px; font-weight: 600; cursor: pointer;
}
.btn-print:hover { background: #2d4f80; }
.btn-txt { display: none; }
.modal-close {
  background: #f1f5f9; border: none; border-radius: 8px;
  width: 32px; height: 32px; cursor: pointer; color: #64748b; font-size: 14px;
  display: flex; align-items: center; justify-content: center;
}
.modal-close:hover { background: #e2e8f0; color: #1e3a5f; }
.modal-loading, .modal-empty {
  flex: 1; display: flex; align-items: center; justify-content: center;
  gap: 10px; color: #64748b; font-size: 14px; padding: 40px;
}
.modal-empty .bi { color: #22c55e; font-size: 22px; }
.modal-scroll { flex: 1; overflow: auto; }
.modal-foot   { padding: 10px 20px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #94a3b8; flex-shrink: 0; }

/* ── Tabla ── */
.det-table { width: 100%; border-collapse: collapse; font-size: 12.5px; min-width: 640px; }
.det-table thead tr { background: #f8fafc; }
.det-table th {
  padding: 10px 12px; text-align: left; font-size: 11px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.4px; color: #64748b;
  white-space: nowrap; border-bottom: 1px solid #e2e8f0;
  position: sticky; top: 0; background: #f8fafc; z-index: 1;
}
.det-table td { padding: 10px 12px; border-bottom: 1px solid #f1f5f9; color: #334155; vertical-align: middle; }
.det-table tbody tr:hover { background: #f8fafc; }

/* ── Responsive ── */
@media (max-width: 768px) {
  .dash-sc      { padding: 0 16px 40px; }
  .kpi-grid     { grid-template-columns: 1fr; gap: 8px; }
  .kpi-card     { padding: 10px; }
  .kpi-value    { font-size: 20px; }
  .accesos-grid { gap: 8px; }
  .acceso-card  { min-width: 120px; }
  .dash-header  { flex-direction: column; gap: 4px; }
  .dash-fecha   { font-size: 12px; }
  .wm-icon-1    { font-size: 280px; }
  .wm-icon-2    { font-size: 110px; }
  .modal-panel  { max-height: 92vh; }
  .btn-txt      { display: inline; }
}

@media (max-width: 576px) {
  .dash-sc      { padding: 0 12px 32px; }
  .kpi-grid     { grid-template-columns: 1fr; }
  .acceso-card  { min-width: 110px; }
  .kpi-icon     { width: 32px; height: 32px; font-size: 15px; }
  .kpi-value    { font-size: 19px; }
  .kpi-label    { font-size: 9.5px; }
  .dash-empresa { font-size: 17px; }
  .wm-icon-1    { font-size: 200px; bottom: -40px; right: -20px; }
  .wm-icon-2    { font-size: 80px; }
  .wm-icon-3    { display: none; }
  .modal-panel  { max-height: 95vh; border-radius: 16px 16px 0 0; }
  .btn-txt      { display: inline; }
}

@media (min-width: 900px) {
  .modal-overlay { align-items: center; justify-content: center; }
  .modal-panel   { width: 92%; max-width: 1100px; max-height: 82vh; border-radius: 16px; animation: fadeScale 0.2s ease; }
  .kpi-grid      { grid-template-columns: repeat(3, 1fr); max-width: 100%; }
  .kpi-value     { font-size: 26px; }
  .btn-txt       { display: inline; }
}

@media (min-width: 1400px) {
  .kpi-grid { grid-template-columns: repeat(5, 1fr); }
}

@keyframes fadeScale { from { opacity: 0; transform: scale(0.96); } to { opacity: 1; transform: scale(1); } }
</style>
