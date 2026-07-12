<template>
  <div class="metricas-forma-pago">

    <!-- ── Filtros ─────────────────────────────────────────────────── -->
    <div class="filtros-bar card p-3 mb-3">
      <div class="row g-2 align-items-end">
        <div class="col-6 col-md-3 col-lg-2">
          <label class="form-label mb-1 small fw-semibold">Año</label>
          <select v-model="selectedYear" class="form-select form-select-sm">
            <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
          </select>
        </div>
        <div class="col-6 col-md-3 col-lg-2">
          <label class="form-label mb-1 small fw-semibold">Mes (Tab 3)</label>
          <select v-model="selectedMonth" class="form-select form-select-sm">
            <option v-for="m in mesesOpciones" :key="m.v" :value="m.v">{{ m.l }}</option>
          </select>
        </div>
        <div class="col-6 col-md-3 col-lg-2">
          <label class="form-label mb-1 small fw-semibold">Tipo</label>
          <select v-model="selectedTipo" class="form-select form-select-sm">
            <option value="ambos">Facturas + Recibos</option>
            <option value="facturas">Solo Facturas</option>
            <option value="recibos">Solo Recibos</option>
          </select>
        </div>
        <div class="col-6 col-md-3 col-lg-2">
          <button class="btn btn-primary btn-sm w-100" @click="cargarTodo" :disabled="cargando">
            <span v-if="cargando" class="spinner-border spinner-border-sm me-1"></span>
            <i v-else class="bi bi-arrow-clockwise me-1"></i>Cargar
          </button>
        </div>
      </div>
    </div>

    <!-- ── KPI Cards ──────────────────────────────────────────────── -->
    <div class="row g-2 mb-3" v-if="anual">
      <div class="col-6 col-md-3" v-for="fp in anual.formas_pago.slice(0, 4)" :key="fp">
        <div class="kpi-card card p-3 text-center">
          <div class="kpi-icon text-primary"><i class="bi bi-credit-card fs-4"></i></div>
          <div class="kpi-value">{{ fmt(anual.totales_por_forma[fp] || 0) }}</div>
          <div class="kpi-label">{{ fp }}</div>
        </div>
      </div>
    </div>

    <!-- ── Tabs ───────────────────────────────────────────────────── -->
    <div class="tabs-bar mb-3">
      <button v-for="t in tabs" :key="t.id" class="tab-btn"
        :class="{ active: activeTab === t.id }" @click="activeTab = t.id">
        <i :class="t.icon + ' me-1'"></i>{{ t.label }}
      </button>
    </div>

    <!-- ════════════════════════════════════════════════════════════ -->
    <!-- TAB 1: Valores                                              -->
    <!-- ════════════════════════════════════════════════════════════ -->
    <div v-if="activeTab === 'valores'" class="tab-content card p-3">
      <div v-if="!anual" class="text-center text-muted py-4">
        <i class="bi bi-credit-card fs-1 d-block mb-2 opacity-25"></i>
        Selecciona año y tipo, luego pulsa <strong>Cargar</strong>.
      </div>
      <div v-else class="table-responsive">
        <table class="table table-sm table-hover align-middle fp-table">
          <thead class="table-dark">
            <tr>
              <th>#</th>
              <th>Mes</th>
              <th v-for="fp in anual.formas_pago" :key="fp" class="text-end">{{ fp }}</th>
              <th class="text-end">Total</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in anual.meses" :key="m.mes">
              <td class="text-muted small">{{ m.mes }}</td>
              <td>{{ m.nombre_mes }}</td>
              <td v-for="fp in anual.formas_pago" :key="fp" class="text-end">
                {{ m.total ? fmt(m.por_forma[fp] || 0) : '—' }}
              </td>
              <td class="text-end fw-semibold">{{ m.total ? fmt(m.total) : '—' }}</td>
            </tr>
          </tbody>
          <tfoot class="table-secondary fw-bold">
            <tr>
              <td colspan="2">Total {{ anual.year }}</td>
              <td v-for="fp in anual.formas_pago" :key="fp" class="text-end">
                {{ fmt(anual.totales_por_forma[fp] || 0) }}
              </td>
              <td class="text-end">{{ fmt(anual.total_general) }}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>

    <!-- ════════════════════════════════════════════════════════════ -->
    <!-- TAB 2: Gráfico Anual                                        -->
    <!-- ════════════════════════════════════════════════════════════ -->
    <div v-if="activeTab === 'grafico'" class="tab-content card p-3">
      <div v-if="!anual" class="text-center text-muted py-4">
        <i class="bi bi-graph-up fs-1 d-block mb-2 opacity-25"></i>
        Selecciona año y tipo, luego pulsa <strong>Cargar</strong>.
      </div>
      <div v-else>
        <div class="d-flex flex-wrap align-items-center gap-2 mb-3">
          <span class="small text-muted me-1">Tipo de gráfico:</span>
          <button v-for="ct in chartTypes" :key="ct.id"
            class="chart-type-btn" :class="{ active: chartType === ct.id }"
            @click="chartType = ct.id">
            <i :class="ct.icon + ' me-1'"></i>{{ ct.label }}
          </button>
        </div>
        <div class="chart-wrapper">
          <canvas ref="canvasAnual"></canvas>
        </div>
      </div>
    </div>

    <!-- ════════════════════════════════════════════════════════════ -->
    <!-- TAB 3: Detalle Mensual                                      -->
    <!-- ════════════════════════════════════════════════════════════ -->
    <div v-if="activeTab === 'mensual'" class="tab-content card p-3">
      <div v-if="!mensual" class="text-center text-muted py-4">
        <i class="bi bi-calendar3 fs-1 d-block mb-2 opacity-25"></i>
        Selecciona mes y tipo, luego pulsa <strong>Cargar</strong>.
      </div>
      <div v-else>
        <p class="text-muted small mb-3">
          {{ mensual.nombre_mes }} {{ mensual.year }} · Total:
          <strong>{{ fmt(mensual.total_mes) }}</strong>
        </p>

        <!-- KPI por forma de pago del mes -->
        <div class="row g-2 mb-3">
          <div class="col-6 col-md-3" v-for="fp in mensual.formas_pago" :key="fp">
            <div class="mini-kpi p-2 text-center rounded border">
              <div class="small fw-bold">{{ fmt(mensual.totales_por_forma[fp] || 0) }}</div>
              <div class="text-muted" style="font-size:.7rem">{{ fp }}</div>
            </div>
          </div>
        </div>

        <!-- Selector tipo gráfico -->
        <div class="d-flex flex-wrap align-items-center gap-2 mb-3">
          <span class="small text-muted me-1">Tipo de gráfico:</span>
          <button v-for="ct in chartTypes" :key="ct.id"
            class="chart-type-btn" :class="{ active: chartTypeMensual === ct.id }"
            @click="chartTypeMensual = ct.id">
            <i :class="ct.icon + ' me-1'"></i>{{ ct.label }}
          </button>
        </div>
        <div class="chart-wrapper mb-4">
          <canvas ref="canvasMensual"></canvas>
        </div>

        <!-- Tabla día a día -->
        <div class="table-responsive">
          <table class="table table-sm align-middle fp-table">
            <thead class="table-light">
              <tr>
                <th>Fecha</th>
                <th>Día</th>
                <th v-for="fp in mensual.formas_pago" :key="fp" class="text-end">{{ fp }}</th>
                <th class="text-end">Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="d in mensual.dias" :key="d.fecha">
                <td class="text-muted small">{{ d.fecha }}</td>
                <td>{{ d.dia_nombre }}</td>
                <td v-for="fp in mensual.formas_pago" :key="fp" class="text-end">
                  {{ d.total ? fmt(d.por_forma[fp] || 0) : '—' }}
                </td>
                <td class="text-end fw-semibold">{{ fmt(d.total) }}</td>
              </tr>
            </tbody>
            <tfoot class="table-secondary fw-bold">
              <tr>
                <td colspan="2">Total {{ mensual.nombre_mes }}</td>
                <td v-for="fp in mensual.formas_pago" :key="fp" class="text-end">
                  {{ fmt(mensual.totales_por_forma[fp] || 0) }}
                </td>
                <td class="text-end">{{ fmt(mensual.total_mes) }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onUnmounted } from 'vue'
import { Chart, registerables } from 'chart.js'
import api from '@/services/apis'
import { useCompanyStore } from '@/stores/companyStore'

Chart.register(...registerables)

const companyStore = useCompanyStore()
const now = new Date()

const selectedYear  = ref(now.getFullYear())
const selectedMonth = ref(now.getMonth() + 1)
const selectedTipo  = ref('ambos')
const cargando      = ref(false)
const activeTab     = ref('valores')
const chartType     = ref('bar')
const chartTypeMensual = ref('bar')

const anual   = ref(null)
const mensual = ref(null)

const canvasAnual   = ref(null)
const canvasMensual = ref(null)
let chartAnualInst   = null
let chartMensualInst = null

const years = Array.from({ length: 6 }, (_, i) => now.getFullYear() - i)
const mesesOpciones = [
  { v: 1, l: 'Enero' }, { v: 2, l: 'Febrero' }, { v: 3, l: 'Marzo' },
  { v: 4, l: 'Abril' }, { v: 5, l: 'Mayo' }, { v: 6, l: 'Junio' },
  { v: 7, l: 'Julio' }, { v: 8, l: 'Agosto' }, { v: 9, l: 'Septiembre' },
  { v: 10, l: 'Octubre' }, { v: 11, l: 'Noviembre' }, { v: 12, l: 'Diciembre' },
]
const tabs = [
  { id: 'valores', label: 'Valores',        icon: 'bi bi-table' },
  { id: 'grafico', label: 'Gráfico Anual',  icon: 'bi bi-bar-chart-line' },
  { id: 'mensual', label: 'Detalle Mes',    icon: 'bi bi-calendar3' },
]
const chartTypes = [
  { id: 'bar',       label: 'Barras',   icon: 'bi bi-bar-chart' },
  { id: 'line',      label: 'Líneas',   icon: 'bi bi-graph-up' },
  { id: 'pie',       label: 'Pastel',   icon: 'bi bi-pie-chart' },
  { id: 'doughnut',  label: 'Dona',     icon: 'bi bi-circle' },
]

const PALETTE = [
  'rgba(13,110,253,.8)', 'rgba(25,135,84,.8)', 'rgba(255,193,7,.8)',
  'rgba(220,53,69,.8)',  'rgba(13,202,240,.8)', 'rgba(111,66,193,.8)',
  'rgba(253,126,20,.8)', 'rgba(32,201,151,.8)',
]
const PALETTE_BORDER = PALETTE.map(c => c.replace('.8)', '1)'))

// ── Formato ────────────────────────────────────────────────────────
function fmt(value) {
  const cc = companyStore.selectedCompany?.currency_code || 'COP'
  try {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency', currency: cc, minimumFractionDigits: 0, maximumFractionDigits: 0,
    }).format(value)
  } catch {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency', currency: 'COP', minimumFractionDigits: 0, maximumFractionDigits: 0,
    }).format(value)
  }
}

// ── Carga ──────────────────────────────────────────────────────────
async function cargarTodo() {
  cargando.value = true
  try {
    const cid = companyStore.selectedCompany?.id
    const params = { year: selectedYear.value, tipo: selectedTipo.value, company_id: cid }
    const [resA, resM] = await Promise.all([
      api.get('/api/metricas/forma-pago/anual', { params }),
      api.get('/api/metricas/forma-pago/mensual', {
        params: { ...params, month: selectedMonth.value },
      }),
    ])
    anual.value   = resA.data
    mensual.value = resM.data
  } catch (e) {
    console.error('Error cargando forma de pago:', e)
  } finally {
    cargando.value = false
  }
}

// ── Construcción de gráficos ───────────────────────────────────────
function isPie(type) { return type === 'pie' || type === 'doughnut' }

function buildAnual() {
  if (!anual.value || !canvasAnual.value) return
  if (chartAnualInst) { chartAnualInst.destroy(); chartAnualInst = null }

  const { formas_pago, meses } = anual.value
  const labels = meses.map(m => m.nombre_mes.substring(0, 3))

  let data, options
  if (isPie(chartType.value)) {
    // Para pie/doughnut: totales por forma de pago
    data = {
      labels: formas_pago,
      datasets: [{
        data: formas_pago.map(fp => anual.value.totales_por_forma[fp] || 0),
        backgroundColor: PALETTE,
        borderColor: PALETTE_BORDER,
        borderWidth: 1,
      }],
    }
    options = {
      responsive: true, maintainAspectRatio: true,
      plugins: {
        legend: { position: 'bottom' },
        tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${fmt(ctx.parsed)}` } },
      },
    }
  } else {
    // Barras/Líneas: datasets por forma de pago, mes en X
    data = {
      labels,
      datasets: formas_pago.map((fp, i) => ({
        label: fp,
        data: meses.map(m => m.por_forma[fp] || 0),
        backgroundColor: PALETTE[i % PALETTE.length],
        borderColor: PALETTE_BORDER[i % PALETTE.length],
        borderWidth: chartType.value === 'line' ? 2 : 1,
        borderRadius: chartType.value === 'bar' ? 4 : 0,
        fill: false,
        tension: 0.3,
      })),
    }
    options = {
      responsive: true, maintainAspectRatio: true,
      plugins: {
        legend: { position: 'top' },
        tooltip: { callbacks: { label: ctx => ` ${ctx.dataset.label}: ${fmt(ctx.parsed.y)}` } },
      },
      scales: {
        y: {
          beginAtZero: true,
          stacked: chartType.value === 'bar',
          ticks: { callback: v => fmt(v) },
          grid: { color: 'rgba(0,0,0,0.05)' },
        },
        x: { stacked: chartType.value === 'bar', grid: { display: false } },
      },
    }
  }

  chartAnualInst = new Chart(canvasAnual.value, { type: chartType.value, data, options })
}

function buildMensual() {
  if (!mensual.value || !canvasMensual.value) return
  if (chartMensualInst) { chartMensualInst.destroy(); chartMensualInst = null }

  const { formas_pago, dias } = mensual.value
  const labels = dias.map(d => `${d.dia}`)

  let data, options
  if (isPie(chartTypeMensual.value)) {
    data = {
      labels: formas_pago,
      datasets: [{
        data: formas_pago.map(fp => mensual.value.totales_por_forma[fp] || 0),
        backgroundColor: PALETTE,
        borderColor: PALETTE_BORDER,
        borderWidth: 1,
      }],
    }
    options = {
      responsive: true, maintainAspectRatio: true,
      plugins: {
        legend: { position: 'bottom' },
        tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${fmt(ctx.parsed)}` } },
      },
    }
  } else {
    data = {
      labels,
      datasets: formas_pago.map((fp, i) => ({
        label: fp,
        data: dias.map(d => d.por_forma[fp] || 0),
        backgroundColor: PALETTE[i % PALETTE.length],
        borderColor: PALETTE_BORDER[i % PALETTE.length],
        borderWidth: chartTypeMensual.value === 'line' ? 2 : 1,
        borderRadius: chartTypeMensual.value === 'bar' ? 3 : 0,
        fill: false,
        tension: 0.3,
      })),
    }
    options = {
      responsive: true, maintainAspectRatio: true,
      plugins: {
        legend: { position: 'top' },
        tooltip: { callbacks: { label: ctx => ` ${ctx.dataset.label}: ${fmt(ctx.parsed.y)}` } },
      },
      scales: {
        y: {
          beginAtZero: true,
          stacked: chartTypeMensual.value === 'bar',
          ticks: { callback: v => fmt(v) },
          grid: { color: 'rgba(0,0,0,0.05)' },
        },
        x: { stacked: chartTypeMensual.value === 'bar', grid: { display: false } },
      },
    }
  }
  chartMensualInst = new Chart(canvasMensual.value, { type: chartTypeMensual.value, data, options })
}

// Watchers para recrear gráficos al cambiar tab o tipo
watch([activeTab, anual, chartType], async ([tab]) => {
  if (tab === 'grafico' && anual.value) { await nextTick(); buildAnual() }
})
watch(chartType, async () => {
  if (activeTab.value === 'grafico' && anual.value) { await nextTick(); buildAnual() }
})
watch([activeTab, mensual, chartTypeMensual], async ([tab]) => {
  if (tab === 'mensual' && mensual.value) { await nextTick(); buildMensual() }
})
watch(chartTypeMensual, async () => {
  if (activeTab.value === 'mensual' && mensual.value) { await nextTick(); buildMensual() }
})

onUnmounted(() => {
  chartAnualInst?.destroy()
  chartMensualInst?.destroy()
})
</script>

<style scoped>
.metricas-forma-pago { padding: 1rem; max-width: 1200px; }
.filtros-bar { border-left: 4px solid #198754; }
.kpi-card { border-top: 3px solid #198754; }
.kpi-value { font-size: 1rem; font-weight: 700; color: #212529; word-break: break-all; }
.kpi-label { font-size: .7rem; color: #6c757d; margin-top: .15rem; }
.kpi-icon { margin-bottom: .25rem; }
.mini-kpi { background: #f8f9fa; }

.tabs-bar { display: flex; gap: .5rem; flex-wrap: wrap; }
.tab-btn {
  padding: .45rem 1rem; border: 1px solid #dee2e6; border-radius: .375rem;
  background: #fff; font-size: .85rem; cursor: pointer; color: #495057; transition: all .15s;
}
.tab-btn:hover { background: #f0fff4; border-color: #198754; color: #198754; }
.tab-btn.active { background: #198754; border-color: #198754; color: #fff; font-weight: 600; }

.tab-content { min-height: 180px; }
.chart-wrapper { position: relative; max-height: 380px; }
.fp-table thead th { font-size: .78rem; white-space: nowrap; }
.fp-table td { white-space: nowrap; }

.chart-type-btn {
  padding: .3rem .7rem; border: 1px solid #dee2e6; border-radius: .375rem;
  background: #fff; font-size: .78rem; cursor: pointer; color: #495057; transition: all .15s;
}
.chart-type-btn:hover { background: #f0fff4; border-color: #198754; color: #198754; }
.chart-type-btn.active { background: #198754; border-color: #198754; color: #fff; font-weight: 600; }

@media (max-width: 768px) {
  .metricas-forma-pago { padding: .5rem; }
  .chart-wrapper { max-height: 260px; }
  .kpi-value { font-size: .88rem; }
  .fp-table th, .fp-table td { font-size: .73rem; }
}
@media (max-width: 576px) {
  .tab-btn, .chart-type-btn { font-size: .72rem; padding: .3rem .5rem; }
  .chart-wrapper { max-height: 210px; }
}
</style>
