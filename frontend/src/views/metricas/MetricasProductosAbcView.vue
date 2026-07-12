<template>
  <div class="metricas-abc">

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
          <label class="form-label mb-1 small fw-semibold">Mes</label>
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
          <label class="form-label mb-1 small fw-semibold">Vista</label>
          <select v-model="vistaActiva" class="form-select form-select-sm">
            <option value="anual">Año completo</option>
            <option value="mensual">Mes seleccionado</option>
          </select>
        </div>
        <div class="col-12 col-md-3 col-lg-2">
          <button class="btn btn-warning btn-sm w-100 text-dark fw-semibold" @click="cargarTodo" :disabled="cargando">
            <span v-if="cargando" class="spinner-border spinner-border-sm me-1"></span>
            <i v-else class="bi bi-arrow-clockwise me-1"></i>Cargar
          </button>
        </div>
      </div>
    </div>

    <!-- ── KPI Resumen ABC ─────────────────────────────────────────── -->
    <div class="row g-2 mb-3" v-if="datoActual">
      <div class="col-4" v-for="cls in ['A','B','C']" :key="cls">
        <div class="kpi-card card p-3 text-center" :class="`kpi-${cls.toLowerCase()}`">
          <div class="kpi-badge">{{ cls }}</div>
          <div class="kpi-count">{{ datoActual.resumen_abc[cls]?.count || 0 }} productos</div>
          <div class="kpi-value">{{ fmt(datoActual.resumen_abc[cls]?.total || 0) }}</div>
          <div class="kpi-pct">{{ datoActual.resumen_abc[cls]?.pct || 0 }}% del total</div>
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
    <!-- TAB 1: Valores — Ranking + ABC                              -->
    <!-- ════════════════════════════════════════════════════════════ -->
    <div v-if="activeTab === 'valores'" class="tab-content card p-3">
      <div v-if="!datoActual" class="text-center text-muted py-4">
        <i class="bi bi-trophy fs-1 d-block mb-2 opacity-25"></i>
        Selecciona período y tipo, luego pulsa <strong>Cargar</strong>.
      </div>
      <div v-else>
        <!-- Barra de búsqueda -->
        <div class="row mb-2 align-items-center">
          <div class="col-12 col-md-5">
            <input v-model="busqueda" class="form-control form-control-sm"
              placeholder="Filtrar por nombre de producto...">
          </div>
          <div class="col-12 col-md-7 mt-2 mt-md-0 d-flex gap-2 flex-wrap">
            <button v-for="cls in ['Todos','A','B','C']" :key="cls"
              class="filter-btn" :class="{ active: filtroClase === cls, [`cls-${cls.toLowerCase()}`]: cls !== 'Todos' }"
              @click="filtroClase = cls">
              {{ cls === 'Todos' ? 'Todos' : `Clase ${cls}` }}
            </button>
          </div>
        </div>

        <div class="table-responsive">
          <table class="table table-sm table-hover align-middle abc-table">
            <thead class="table-dark">
              <tr>
                <th>#</th>
                <th>Producto</th>
                <th class="text-end">Cantidad</th>
                <th class="text-end">Total Venta</th>
                <th class="text-end">% Indiv.</th>
                <th class="text-end">% Acum.</th>
                <th class="text-center">Clase</th>
                <th>Participación</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in productosFiltrados" :key="p.rank"
                :class="{ 'row-a': p.clase==='A', 'row-b': p.clase==='B', 'row-c': p.clase==='C' }">
                <td class="text-muted small">{{ p.rank }}</td>
                <td class="producto-nombre">{{ p.producto }}</td>
                <td class="text-end">{{ fmtNum(p.cantidad) }}</td>
                <td class="text-end fw-semibold">{{ fmt(p.total) }}</td>
                <td class="text-end">{{ p.pct }}%</td>
                <td class="text-end">{{ p.pct_acum }}%</td>
                <td class="text-center">
                  <span class="badge" :class="`badge-${p.clase.toLowerCase()}`">{{ p.clase }}</span>
                </td>
                <td style="min-width:80px">
                  <div class="progress" style="height:7px">
                    <div class="progress-bar" :class="`bar-${p.clase.toLowerCase()}`"
                      :style="{ width: p.pct + '%' }"></div>
                  </div>
                </td>
              </tr>
            </tbody>
            <tfoot class="table-secondary fw-bold">
              <tr>
                <td colspan="3">Total — {{ datoActual.productos.length }} productos</td>
                <td class="text-end">{{ fmt(totalMostrado) }}</td>
                <td colspan="4"></td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>

    <!-- ════════════════════════════════════════════════════════════ -->
    <!-- TAB 2: Gráfico                                              -->
    <!-- ════════════════════════════════════════════════════════════ -->
    <div v-if="activeTab === 'grafico'" class="tab-content card p-3">
      <div v-if="!datoActual" class="text-center text-muted py-4">
        <i class="bi bi-graph-up-arrow fs-1 d-block mb-2 opacity-25"></i>
        Selecciona período y tipo, luego pulsa <strong>Cargar</strong>.
      </div>
      <div v-else>
        <!-- Selector tipo gráfico -->
        <div class="d-flex flex-wrap align-items-center gap-2 mb-3">
          <span class="small text-muted me-1">Tipo de gráfico:</span>
          <button v-for="ct in chartTypes" :key="ct.id"
            class="chart-type-btn" :class="{ active: chartType === ct.id }"
            @click="chartType = ct.id">
            <i :class="ct.icon + ' me-1'"></i>{{ ct.label }}
          </button>
        </div>
        <div class="chart-wrapper">
          <canvas ref="canvasChart"></canvas>
        </div>
        <p class="text-muted small mt-2" v-if="chartType === 'pareto'">
          Curva de Pareto — eje izquierdo: ventas por producto · eje derecho: % acumulado
        </p>
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
const vistaActiva   = ref('anual')
const cargando      = ref(false)
const activeTab     = ref('valores')
const chartType     = ref('barraH')
const busqueda      = ref('')
const filtroClase   = ref('Todos')

const datoAnual   = ref(null)
const datoMensual = ref(null)
const canvasChart = ref(null)
let chartInst     = null

const years = Array.from({ length: 6 }, (_, i) => now.getFullYear() - i)
const mesesOpciones = [
  { v: 1, l: 'Enero' }, { v: 2, l: 'Febrero' }, { v: 3, l: 'Marzo' },
  { v: 4, l: 'Abril' }, { v: 5, l: 'Mayo' }, { v: 6, l: 'Junio' },
  { v: 7, l: 'Julio' }, { v: 8, l: 'Agosto' }, { v: 9, l: 'Septiembre' },
  { v: 10, l: 'Octubre' }, { v: 11, l: 'Noviembre' }, { v: 12, l: 'Diciembre' },
]
const tabs = [
  { id: 'valores', label: 'Valores / Ranking', icon: 'bi bi-table' },
  { id: 'grafico', label: 'Gráficos',          icon: 'bi bi-graph-up-arrow' },
]
const chartTypes = [
  { id: 'barraH',   label: 'Ranking',    icon: 'bi bi-bar-chart-steps' },
  { id: 'bar',      label: 'Barras',     icon: 'bi bi-bar-chart' },
  { id: 'pie',      label: 'Pastel ABC', icon: 'bi bi-pie-chart' },
  { id: 'doughnut', label: 'Dona ABC',   icon: 'bi bi-circle' },
  { id: 'pareto',   label: 'Pareto',     icon: 'bi bi-graph-up' },
]

// ── Computed ────────────────────────────────────────────────────────
const datoActual = computed(() =>
  vistaActiva.value === 'mensual' ? datoMensual.value : datoAnual.value
)

const productosFiltrados = computed(() => {
  if (!datoActual.value) return []
  return datoActual.value.productos.filter(p => {
    const porClase = filtroClase.value === 'Todos' || p.clase === filtroClase.value
    const porBusq  = !busqueda.value || p.producto.toLowerCase().includes(busqueda.value.toLowerCase())
    return porClase && porBusq
  })
})

const totalMostrado = computed(() =>
  productosFiltrados.value.reduce((acc, p) => acc + p.total, 0)
)

// ── Formato ─────────────────────────────────────────────────────────
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
function fmtNum(v) { return new Intl.NumberFormat('es-CO').format(Math.round(v)) }

// ── Colores ABC ──────────────────────────────────────────────────────
const ABC_COLORS = {
  A: { bg: 'rgba(25,135,84,.8)', border: 'rgba(25,135,84,1)' },
  B: { bg: 'rgba(255,193,7,.8)', border: 'rgba(255,193,7,1)' },
  C: { bg: 'rgba(220,53,69,.8)', border: 'rgba(220,53,69,1)' },
}

// ── Carga ────────────────────────────────────────────────────────────
async function cargarTodo() {
  cargando.value = true
  try {
    const cid = companyStore.selectedCompany?.id
    const base = { tipo: selectedTipo.value, company_id: cid }
    const [resA, resM] = await Promise.all([
      api.get('/api/metricas/productos-abc/anual',   { params: { ...base, year: selectedYear.value } }),
      api.get('/api/metricas/productos-abc/mensual', { params: { ...base, year: selectedYear.value, month: selectedMonth.value } }),
    ])
    datoAnual.value   = resA.data
    datoMensual.value = resM.data
  } catch (e) {
    console.error('Error cargando ABC:', e)
  } finally {
    cargando.value = false
  }
}

// ── Gráficos ─────────────────────────────────────────────────────────
const TOP_N = 20

function buildChart() {
  if (!datoActual.value || !canvasChart.value) return
  if (chartInst) { chartInst.destroy(); chartInst = null }

  const tops = [...datoActual.value.productos].slice(0, TOP_N)

  if (chartType.value === 'pie' || chartType.value === 'doughnut') {
    // Distribución ABC
    const res = datoActual.value.resumen_abc
    chartInst = new Chart(canvasChart.value, {
      type: chartType.value,
      data: {
        labels: ['Clase A', 'Clase B', 'Clase C'],
        datasets: [{
          data: [res.A?.total || 0, res.B?.total || 0, res.C?.total || 0],
          backgroundColor: [ABC_COLORS.A.bg, ABC_COLORS.B.bg, ABC_COLORS.C.bg],
          borderColor: [ABC_COLORS.A.border, ABC_COLORS.B.border, ABC_COLORS.C.border],
          borderWidth: 2,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: true,
        plugins: {
          legend: { position: 'bottom' },
          tooltip: {
            callbacks: { label: ctx => ` ${ctx.label}: ${fmt(ctx.parsed)} (${res[ctx.label.slice(-1)]?.pct || 0}%)` },
          },
        },
      },
    })
    return
  }

  if (chartType.value === 'pareto') {
    // Barras + línea acumulada (Pareto)
    chartInst = new Chart(canvasChart.value, {
      data: {
        labels: tops.map(p => p.producto.length > 18 ? p.producto.substring(0, 18) + '…' : p.producto),
        datasets: [
          {
            type: 'bar',
            label: 'Ventas',
            data: tops.map(p => p.total),
            backgroundColor: tops.map(p => ABC_COLORS[p.clase].bg),
            borderColor: tops.map(p => ABC_COLORS[p.clase].border),
            borderWidth: 1,
            borderRadius: 3,
            yAxisID: 'y',
          },
          {
            type: 'line',
            label: '% Acumulado',
            data: tops.map(p => p.pct_acum),
            borderColor: 'rgba(13,110,253,1)',
            backgroundColor: 'rgba(13,110,253,.1)',
            fill: true,
            tension: 0.2,
            yAxisID: 'y2',
            pointRadius: 3,
          },
        ],
      },
      options: {
        responsive: true, maintainAspectRatio: true,
        plugins: {
          legend: { position: 'top' },
          tooltip: {
            callbacks: {
              label: ctx => ctx.dataset.yAxisID === 'y2'
                ? ` ${ctx.parsed.y.toFixed(1)}%`
                : ` ${fmt(ctx.parsed.y)}`,
            },
          },
        },
        scales: {
          y:  { beginAtZero: true, ticks: { callback: v => fmt(v) }, grid: { color: 'rgba(0,0,0,0.05)' } },
          y2: { beginAtZero: true, max: 100, position: 'right', ticks: { callback: v => v + '%' }, grid: { display: false } },
          x:  { grid: { display: false } },
        },
      },
    })
    return
  }

  // barraH y bar — ranking de productos
  const isH = chartType.value === 'barraH'
  const labels = tops.map(p => p.producto.length > 22 ? p.producto.substring(0, 22) + '…' : p.producto)
  chartInst = new Chart(canvasChart.value, {
    type: isH ? 'bar' : 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Total Venta',
        data: tops.map(p => p.total),
        backgroundColor: tops.map(p => ABC_COLORS[p.clase].bg),
        borderColor:     tops.map(p => ABC_COLORS[p.clase].border),
        borderWidth: 1,
        borderRadius: 3,
      }],
    },
    options: {
      indexAxis: isH ? 'y' : 'x',
      responsive: true, maintainAspectRatio: true,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => ` ${fmt(ctx.parsed[isH ? 'x' : 'y'])}` } },
      },
      scales: {
        [isH ? 'x' : 'y']: {
          beginAtZero: true,
          ticks: { callback: v => fmt(v) },
          grid: { color: 'rgba(0,0,0,0.05)' },
        },
        [isH ? 'y' : 'x']: { grid: { display: false } },
      },
    },
  })
}

watch([activeTab, datoActual, chartType], async ([tab]) => {
  if (tab === 'grafico' && datoActual.value) { await nextTick(); buildChart() }
})
watch(chartType, async () => {
  if (activeTab.value === 'grafico' && datoActual.value) { await nextTick(); buildChart() }
})
watch(vistaActiva, async () => {
  if (activeTab.value === 'grafico' && datoActual.value) { await nextTick(); buildChart() }
})

onUnmounted(() => chartInst?.destroy())
</script>

<style scoped>
.metricas-abc { padding: 1rem; max-width: 1100px; }
.filtros-bar { border-left: 4px solid #ffc107; }

/* KPI ABC */
.kpi-card { border-top: 4px solid #dee2e6; transition: box-shadow .2s; }
.kpi-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.1); }
.kpi-a { border-top-color: #198754; }
.kpi-b { border-top-color: #ffc107; }
.kpi-c { border-top-color: #dc3545; }
.kpi-badge { font-size: 1.6rem; font-weight: 900; line-height: 1; }
.kpi-a .kpi-badge { color: #198754; }
.kpi-b .kpi-badge { color: #ffc107; }
.kpi-c .kpi-badge { color: #dc3545; }
.kpi-count { font-size: .78rem; color: #6c757d; }
.kpi-value { font-size: .95rem; font-weight: 700; margin: .15rem 0; word-break: break-all; }
.kpi-pct { font-size: .7rem; color: #6c757d; }

/* Tabs */
.tabs-bar { display: flex; gap: .5rem; flex-wrap: wrap; }
.tab-btn {
  padding: .45rem 1rem; border: 1px solid #dee2e6; border-radius: .375rem;
  background: #fff; font-size: .85rem; cursor: pointer; color: #495057; transition: all .15s;
}
.tab-btn:hover { background: #fffbea; border-color: #ffc107; color: #856404; }
.tab-btn.active { background: #ffc107; border-color: #ffc107; color: #212529; font-weight: 700; }

.tab-content { min-height: 180px; }

/* Filtros clase */
.filter-btn {
  padding: .3rem .7rem; border: 1px solid #dee2e6; border-radius: .375rem;
  background: #fff; font-size: .78rem; cursor: pointer; color: #495057; transition: all .15s;
}
.filter-btn.active { background: #6c757d; border-color: #6c757d; color: #fff; font-weight: 600; }
.filter-btn.cls-a.active { background: #198754; border-color: #198754; }
.filter-btn.cls-b.active { background: #ffc107; border-color: #ffc107; color: #212529; }
.filter-btn.cls-c.active { background: #dc3545; border-color: #dc3545; }

/* Tabla */
.abc-table thead th { font-size: .78rem; white-space: nowrap; }
.abc-table td { white-space: nowrap; }
.producto-nombre { max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: .82rem; }
.row-a { background-color: rgba(25,135,84,.04); }
.row-b { background-color: rgba(255,193,7,.06); }
.row-c { background-color: rgba(220,53,69,.04); }

.badge-a { background-color: #198754; }
.badge-b { background-color: #ffc107; color: #212529; }
.badge-c { background-color: #dc3545; }

.bar-a { background-color: #198754; }
.bar-b { background-color: #ffc107; }
.bar-c { background-color: #dc3545; }

/* Gráfico */
.chart-wrapper { position: relative; max-height: 420px; }
.chart-type-btn {
  padding: .3rem .7rem; border: 1px solid #dee2e6; border-radius: .375rem;
  background: #fff; font-size: .78rem; cursor: pointer; color: #495057; transition: all .15s;
}
.chart-type-btn:hover { background: #fffbea; border-color: #ffc107; color: #856404; }
.chart-type-btn.active { background: #ffc107; border-color: #ffc107; color: #212529; font-weight: 700; }

@media (max-width: 768px) {
  .metricas-abc { padding: .5rem; }
  .kpi-value { font-size: .85rem; }
  .chart-wrapper { max-height: 280px; }
  .abc-table th, .abc-table td { font-size: .73rem; }
  .producto-nombre { max-width: 140px; }
}
@media (max-width: 576px) {
  .tab-btn, .chart-type-btn, .filter-btn { font-size: .7rem; padding: .28rem .48rem; }
  .chart-wrapper { max-height: 220px; }
  .kpi-badge { font-size: 1.2rem; }
  .kpi-value { font-size: .78rem; }
}
</style>
