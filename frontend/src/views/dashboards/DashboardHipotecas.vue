<template>
  <div class="dash-hip">

    <!-- Marca de agua de fondo -->
    <div class="wm-bg" aria-hidden="true">
      <i class="bi bi-house-door   wm-icon-1"></i>
      <i class="bi bi-calendar-check wm-icon-2"></i>
      <i class="bi bi-cash-stack   wm-icon-3"></i>
    </div>

    <!-- Header -->
    <div class="dash-header">
      <div class="dash-header-left">
        <h6 class="dash-empresa">{{ empresa }}</h6>
        <span class="dash-perfil-tag">
          <i class="bi bi-bank2"></i> Cobros - Hipotecas
        </span>
      </div>
      <span class="dash-fecha">{{ fechaHoy }}</span>
    </div>

    <!-- Banner bienvenida -->
    <div class="welcome-banner">
      <div class="wb-icon-wrap">
        <i class="bi bi-house-door"></i>
      </div>
      <div class="wb-text">
        <h5>Bienvenido a Cobros - Hipotecas</h5>
        <p>
          Administra préstamos e hipotecas, registra cobros y cuotas, controla
          tu cartera activa y lleva el seguimiento detallado de cada cliente
          con su calendario de pagos.
        </p>
      </div>
    </div>

    <!-- ─── KPI Bar ─────────────────────────────────────────── -->
    <p class="section-label">
      <i class="bi bi-bar-chart-line-fill"></i> Indicadores del mes
    </p>

    <div class="kpi-grid">

      <!-- KPI 1: Arriendos x Avisar -->
      <button
        class="kpi-card kpi-amber"
        :disabled="loadingKpi"
        @click="abrirModal('avisar')"
      >
        <div class="kpi-icon"><i class="bi bi-bell-fill"></i></div>
        <div class="kpi-body">
          <span class="kpi-label">Arriendos x Avisar</span>
          <span class="kpi-value">
            <template v-if="loadingKpi"><i class="bi bi-hourglass-split spin"></i></template>
            <template v-else>{{ kpi.arriendos_avisar }}</template>
          </span>
          <span class="kpi-sub">Este mes</span>
        </div>
        <i class="bi bi-chevron-right kpi-arrow"></i>
      </button>

      <!-- KPI 2: Arriendos x Vencer -->
      <button
        class="kpi-card kpi-orange"
        :disabled="loadingKpi"
        @click="abrirModal('vencer')"
      >
        <div class="kpi-icon"><i class="bi bi-calendar-x-fill"></i></div>
        <div class="kpi-body">
          <span class="kpi-label">Arriendos x Vencer</span>
          <span class="kpi-value">
            <template v-if="loadingKpi"><i class="bi bi-hourglass-split spin"></i></template>
            <template v-else>{{ kpi.arriendos_vencer }}</template>
          </span>
          <span class="kpi-sub">Este mes</span>
        </div>
        <i class="bi bi-chevron-right kpi-arrow"></i>
      </button>

      <!-- KPI 3: Créditos Atrasados -->
      <button
        class="kpi-card kpi-red"
        :disabled="loadingKpi"
        @click="abrirModal('creditos')"
      >
        <div class="kpi-icon"><i class="bi bi-exclamation-triangle-fill"></i></div>
        <div class="kpi-body">
          <span class="kpi-label">Créditos Atrasados</span>
          <span class="kpi-value">
            <template v-if="loadingKpi"><i class="bi bi-hourglass-split spin"></i></template>
            <template v-else>{{ kpi.creditos_atrasados }}</template>
          </span>
          <span class="kpi-sub-selector">
            Más de
            <select
              v-model="mesesFiltro"
              class="mes-select"
              @change.stop="recargarKpi"
              @click.stop
            >
              <option v-for="m in opcionesMeses" :key="m" :value="m">{{ m }} mes{{ m > 1 ? 'es' : '' }}</option>
            </select>
            de mora
          </span>
        </div>
        <i class="bi bi-chevron-right kpi-arrow"></i>
      </button>

    </div>

    <!-- ─── Modal detalle ──────────────────────────────────────── -->
    <Teleport to="body">
      <div v-if="modal.visible" class="modal-overlay" @click.self="cerrarModal">
        <div class="modal-panel">

          <div class="modal-head">
            <span class="modal-title">
              <i :class="modal.icono"></i> {{ modal.titulo }}
            </span>
            <button class="modal-close" @click="cerrarModal"><i class="bi bi-x-lg"></i></button>
          </div>

          <div v-if="modal.loading" class="modal-loading">
            <i class="bi bi-hourglass-split spin"></i> Cargando...
          </div>

          <div v-else-if="modal.items.length === 0" class="modal-empty">
            <i class="bi bi-check-circle"></i> Sin registros para este período
          </div>

          <!-- Tabla Arriendos -->
          <div v-else-if="modal.tipo !== 'creditos'" class="modal-scroll">
            <table class="det-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Cliente</th>
                  <th>Propiedad</th>
                  <th>Sector</th>
                  <th>Canon</th>
                  <th>Pagado hasta</th>
                  <th>{{ modal.tipo === 'avisar' ? 'Avisar' : 'Vence' }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(it, i) in modal.items" :key="it.Id_Arriendo">
                  <td>{{ i + 1 }}</td>
                  <td>
                    <span class="det-nombre">{{ it.cliente_nombre }}</span>
                    <span class="det-cedula">{{ it.cedula }}</span>
                  </td>
                  <td>{{ it.propiedad || it.propiedad_direccion }}</td>
                  <td>{{ it.sector }}</td>
                  <td class="det-money">{{ fmt(it.canon) }}</td>
                  <td>{{ fmtFecha(it.Pago_Hasta) }}</td>
                  <td :class="modal.tipo === 'avisar' ? 'det-amber' : 'det-orange'">
                    {{ fmtFecha(modal.tipo === 'avisar' ? it.Avisar : it.Vence) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Tabla Créditos -->
          <div v-else class="modal-scroll">
            <table class="det-table">
              <thead>
                <tr>
                  <th>Crédito</th>
                  <th>Cliente</th>
                  <th>Saldo</th>
                  <th>Cuota/mes</th>
                  <th>Meses mora</th>
                  <th>Total deuda</th>
                  <th>Acreedor</th>
                  <th>Ref. Jur.</th>
                  <th>Ref. Adic.</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="it in modal.items" :key="it.Nro_Credito">
                  <td class="det-nro">{{ it.Nro_Credito }}</td>
                  <td>
                    <span class="det-nombre">{{ it.cliente_nombre }}</span>
                    <span class="det-cedula">{{ it.cedula }}</span>
                  </td>
                  <td class="det-money">{{ fmt(it.Valor_Actual) }}</td>
                  <td class="det-money">{{ fmt(it.cuota_mes) }}</td>
                  <td class="det-red">{{ it.meses_deuda }}</td>
                  <td class="det-money det-red">{{ fmt(it.total_deuda) }}</td>
                  <td>{{ it.acreedor_nombre }}</td>
                  <td>{{ it.nro_juridico }}</td>
                  <td>{{ it.ref_adicional }}</td>
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

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useCompanyStore } from '@/stores/companyStore'
import api from '@/services/apis'

const companyStore = useCompanyStore()

const empresa = computed(() => companyStore.selectedCompany?.name ?? '')
const companyId = computed(() => companyStore.selectedCompany?.id)

const fechaHoy = computed(() =>
  new Intl.DateTimeFormat('es-CO', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
  }).format(new Date())
)

// ── KPI ────────────────────────────────────────────────────────────────────
const opcionesMeses = [1, 2, 3, 5, 6, 12]
const mesesFiltro   = ref(5)
const loadingKpi    = ref(false)
const kpi = ref({ arriendos_avisar: 0, arriendos_vencer: 0, creditos_atrasados: 0 })

async function cargarKpi() {
  if (!companyId.value) return
  loadingKpi.value = true
  try {
    const { data } = await api.get('/api/hipotecas/kpi', {
      params: { company_id: companyId.value, meses: mesesFiltro.value }
    })
    kpi.value = data
  } catch {
    // silencioso — valores quedan en 0
  } finally {
    loadingKpi.value = false
  }
}

function recargarKpi() { cargarKpi() }

onMounted(cargarKpi)
watch(companyId, (val) => { if (val) cargarKpi() })

// ── Modal ──────────────────────────────────────────────────────────────────
const modal = ref({
  visible: false,
  tipo: '',
  titulo: '',
  icono: '',
  loading: false,
  items: [],
})

const CONFIG_MODAL = {
  avisar:   { titulo: 'Arriendos x Avisar — Este mes',  icono: 'bi bi-bell-fill',                endpoint: '/api/hipotecas/kpi/arriendos-avisar' },
  vencer:   { titulo: 'Arriendos x Vencer — Este mes',  icono: 'bi bi-calendar-x-fill',           endpoint: '/api/hipotecas/kpi/arriendos-vencer' },
  creditos: { titulo: 'Créditos Atrasados',              icono: 'bi bi-exclamation-triangle-fill', endpoint: '/api/hipotecas/kpi/creditos-atrasados' },
}

async function abrirModal(tipo) {
  const cfg = CONFIG_MODAL[tipo]
  modal.value = { visible: true, tipo, titulo: cfg.titulo, icono: cfg.icono, loading: true, items: [] }
  document.body.style.overflow = 'hidden'
  try {
    const params = { company_id: companyId.value }
    if (tipo === 'creditos') params.meses = mesesFiltro.value
    const { data } = await api.get(cfg.endpoint, { params })
    modal.value.items = data.items
  } catch {
    modal.value.items = []
  } finally {
    modal.value.loading = false
  }
}

function cerrarModal() {
  modal.value.visible = false
  document.body.style.overflow = ''
}

// ── Formateo ───────────────────────────────────────────────────────────────
function fmt(v) {
  if (v == null || v === '') return '—'
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v)
}

function fmtFecha(v) {
  if (!v) return '—'
  const d = new Date(v + 'T00:00:00')
  return new Intl.DateTimeFormat('es-CO', { day: '2-digit', month: 'short', year: 'numeric' }).format(d)
}
</script>

<style scoped>
/* ───────────────── contenedor ───────────────── */
.dash-hip {
  position: relative;
  min-height: 80vh;
  padding: 0 24px 48px;
  overflow: hidden;
}

/* ───────────────── marca de agua ───────────────── */
.wm-bg { position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden; }
.wm-icon-1 { position: absolute; font-size: 420px; color: #065f46; opacity: 0.045; bottom: -80px; right: -60px; transform: rotate(-8deg); }
.wm-icon-2 { position: absolute; font-size: 160px; color: #0f2448; opacity: 0.05; top: 50px; left: -20px; transform: rotate(15deg); }
.wm-icon-3 { position: absolute; font-size: 100px; color: #10b981; opacity: 0.055; top: 200px; right: 22%; transform: rotate(-25deg); }

/* ───────────────── header ───────────────── */
.dash-header {
  position: relative; z-index: 1;
  display: flex; align-items: flex-start; justify-content: space-between; gap: 12px;
  padding: 24px 0 16px; border-bottom: 1px solid #e2e8f0; margin-bottom: 24px;
}
.dash-empresa { margin: 0 0 4px; font-size: 20px; font-weight: 700; color: #0f2448; line-height: 1.2; }
.dash-perfil-tag {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 12px; font-weight: 600; color: #065f46;
  background: #d1fae5; border: 1px solid #6ee7b7; border-radius: 20px;
  padding: 2px 10px; text-transform: uppercase; letter-spacing: 0.5px;
}
.dash-fecha { font-size: 13px; color: #64748b; white-space: nowrap; padding-top: 2px; text-transform: capitalize; }

/* ───────────────── banner bienvenida ───────────────── */
.welcome-banner {
  position: relative; z-index: 1;
  display: flex; align-items: center; gap: 20px;
  background: linear-gradient(135deg, #0f2448 0%, #065f46 100%);
  border-radius: 16px; padding: 28px; margin-bottom: 28px; overflow: hidden;
  box-shadow: 0 4px 20px rgba(15,36,72,0.20);
}
.wb-icon-wrap {
  flex-shrink: 0; width: 64px; height: 64px; border-radius: 16px;
  background: rgba(16,185,129,0.18); border: 1px solid rgba(16,185,129,0.35);
  display: flex; align-items: center; justify-content: center; font-size: 30px; color: #10b981;
}
.wb-text h5 { margin: 0 0 6px; font-size: 17px; font-weight: 700; color: #fff; }
.wb-text p  { margin: 0; font-size: 13.5px; color: #a7f3d0; line-height: 1.6; }

/* ───────────────── section label ───────────────── */
.section-label {
  position: relative; z-index: 1;
  font-size: 12px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.8px; color: #64748b; margin: 0 0 14px;
  display: flex; align-items: center; gap: 6px;
}
.section-label .bi { color: #10b981; font-size: 13px; }

/* ───────────────── KPI grid ───────────────── */
.kpi-grid {
  position: relative; z-index: 1;
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;
}

.kpi-card {
  display: flex; align-items: center; gap: 14px;
  background: #fff; border: 1.5px solid #e2e8f0; border-radius: 16px;
  padding: 18px 14px; cursor: pointer; text-align: left;
  transition: all 0.2s ease; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  width: 100%;
}
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.10); }
.kpi-card:disabled { cursor: default; transform: none; }

.kpi-icon {
  flex-shrink: 0; width: 48px; height: 48px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center; font-size: 22px;
}
.kpi-amber .kpi-icon { background: #fef3c7; color: #d97706; }
.kpi-orange .kpi-icon { background: #ffedd5; color: #ea580c; }
.kpi-red .kpi-icon    { background: #fee2e2; color: #dc2626; }

.kpi-amber { border-left: 4px solid #f59e0b; }
.kpi-orange { border-left: 4px solid #f97316; }
.kpi-red    { border-left: 4px solid #ef4444; }

.kpi-amber:hover  { border-color: #f59e0b; box-shadow: 0 6px 20px rgba(245,158,11,0.18); }
.kpi-orange:hover { border-color: #f97316; box-shadow: 0 6px 20px rgba(249,115,22,0.18); }
.kpi-red:hover    { border-color: #ef4444; box-shadow: 0 6px 20px rgba(239,68,68,0.18); }

.kpi-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.kpi-label { font-size: 11.5px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; line-height: 1.3; }
.kpi-value { font-size: 30px; font-weight: 800; color: #0f172a; line-height: 1.1; }
.kpi-sub   { font-size: 11px; color: #94a3b8; }

.kpi-sub-selector {
  display: flex; align-items: center; gap: 4px; flex-wrap: wrap;
  font-size: 11px; color: #94a3b8;
}
.mes-select {
  font-size: 11px; color: #0f2448; font-weight: 700;
  background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px;
  padding: 1px 4px; cursor: pointer; outline: none;
}
.mes-select:focus { border-color: #10b981; }

.kpi-arrow { font-size: 13px; color: #cbd5e1; flex-shrink: 0; }

/* ───────────────── spinner ───────────────── */
.spin { display: inline-block; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ───────────────── Modal overlay ───────────────── */
.modal-overlay {
  position: fixed; inset: 0; z-index: 9000;
  background: rgba(15,36,72,0.55); backdrop-filter: blur(3px);
  display: flex; align-items: flex-end;
}

.modal-panel {
  width: 100%; max-height: 90vh;
  background: #fff; border-radius: 20px 20px 0 0;
  display: flex; flex-direction: column;
  box-shadow: 0 -8px 40px rgba(0,0,0,0.20);
  animation: slideUp 0.25s ease;
}
@keyframes slideUp { from { transform: translateY(100%); } to { transform: translateY(0); } }

.modal-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 20px 14px; border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}
.modal-title { font-size: 15px; font-weight: 700; color: #0f2448; display: flex; align-items: center; gap: 8px; }
.modal-close  { background: #f1f5f9; border: none; border-radius: 8px; width: 32px; height: 32px; cursor: pointer; color: #64748b; font-size: 14px; display: flex; align-items: center; justify-content: center; }
.modal-close:hover { background: #e2e8f0; color: #0f2448; }

.modal-loading, .modal-empty {
  flex: 1; display: flex; align-items: center; justify-content: center;
  gap: 10px; color: #64748b; font-size: 14px; padding: 40px;
}
.modal-empty .bi { color: #10b981; font-size: 22px; }

.modal-scroll { flex: 1; overflow: auto; padding: 0; }

.modal-foot {
  padding: 10px 20px; border-top: 1px solid #e2e8f0;
  font-size: 12px; color: #94a3b8; flex-shrink: 0;
}

/* ───────────────── Tabla detalle ───────────────── */
.det-table {
  width: 100%; border-collapse: collapse; font-size: 12.5px;
  min-width: 640px;
}
.det-table thead tr { background: #f8fafc; }
.det-table th {
  padding: 10px 12px; text-align: left; font-size: 11px;
  font-weight: 700; text-transform: uppercase; letter-spacing: 0.4px;
  color: #64748b; white-space: nowrap; border-bottom: 1px solid #e2e8f0;
  position: sticky; top: 0; background: #f8fafc;
}
.det-table td { padding: 10px 12px; border-bottom: 1px solid #f1f5f9; color: #334155; vertical-align: top; }
.det-table tbody tr:hover { background: #f8fafc; }

.det-nombre { display: block; font-weight: 600; color: #0f2448; }
.det-cedula { display: block; font-size: 11px; color: #94a3b8; }
.det-nro    { font-weight: 700; color: #0f2448; }
.det-money  { font-weight: 600; color: #065f46; }
.det-red    { font-weight: 700; color: #dc2626; }
.det-amber  { font-weight: 600; color: #d97706; }
.det-orange { font-weight: 600; color: #ea580c; }

/* ───────────────── responsive ───────────────── */
@media (max-width: 768px) {
  .dash-hip { padding: 0 16px 40px; }
  .kpi-grid { grid-template-columns: 1fr; gap: 10px; }
  .kpi-card { padding: 14px 12px; }
  .kpi-value { font-size: 26px; }
  .welcome-banner { flex-direction: column; text-align: center; padding: 22px 20px; }
  .dash-header { flex-direction: column; gap: 6px; }
  .dash-fecha { font-size: 12px; }
  .wm-icon-1 { font-size: 280px; }
  .wm-icon-2 { font-size: 110px; }
  .modal-panel { max-height: 92vh; }
}

@media (max-width: 576px) {
  .dash-hip { padding: 0 12px 32px; }
  .kpi-grid { grid-template-columns: 1fr; gap: 10px; }
  .kpi-icon { width: 42px; height: 42px; font-size: 18px; }
  .kpi-value { font-size: 24px; }
  .kpi-label { font-size: 10.5px; }
  .dash-empresa { font-size: 17px; }
  .wb-icon-wrap { width: 50px; height: 50px; font-size: 24px; }
  .wb-text h5 { font-size: 15px; }
  .wb-text p  { font-size: 12.5px; }
  .wm-icon-1 { font-size: 200px; bottom: -40px; right: -20px; }
  .wm-icon-2 { font-size: 80px; }
  .wm-icon-3 { display: none; }
  .modal-panel { max-height: 95vh; border-radius: 16px 16px 0 0; }
}

/* Desktop: modal centrado en vez de bottom sheet */
@media (min-width: 900px) {
  .modal-overlay { align-items: center; justify-content: center; }
  .modal-panel {
    width: 92%; max-width: 1100px; max-height: 82vh;
    border-radius: 16px;
    animation: fadeScale 0.2s ease;
  }
  .kpi-grid { grid-template-columns: repeat(3, 1fr); }
  .kpi-value { font-size: 34px; }
}
@keyframes fadeScale {
  from { opacity: 0; transform: scale(0.96); }
  to   { opacity: 1; transform: scale(1); }
}
</style>
