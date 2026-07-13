<template>
  <div class="metricas-ventas">

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
        <div class="col-6 col-md-3 col-lg-2">
          <button class="btn btn-success btn-sm w-100" @click="descargarExcel" :disabled="descargando">
            <span v-if="descargando" class="spinner-border spinner-border-sm me-1"></span>
            <i v-else class="bi bi-file-earmark-excel me-1"></i>Excel
          </button>
        </div>
      </div>
    </div>

    <!-- ── KPI Cards ──────────────────────────────────────────────── -->
    <div class="row g-2 mb-3" v-if="anual">
      <div class="col-6 col-md-3">
        <div class="kpi-card card p-3 text-center">
          <div class="kpi-icon text-primary"><i class="bi bi-currency-dollar fs-4"></i></div>
          <div class="kpi-value">{{ fmt(anual.total_general) }}</div>
          <div class="kpi-label">Total {{ anual.year }}</div>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="kpi-card card p-3 text-center">
          <div class="kpi-icon text-success"><i class="bi bi-trophy fs-4"></i></div>
          <div class="kpi-value">{{ mejorMes?.nombre_mes || '—' }}</div>
          <div class="kpi-label">Mejor Mes · {{ fmt(mejorMes?.total || 0) }}</div>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="kpi-card card p-3 text-center">
          <div class="kpi-icon text-info"><i class="bi bi-bar-chart fs-4"></i></div>
          <div class="kpi-value">{{ fmt(promedioMensual) }}</div>
          <div class="kpi-label">Promedio Mensual</div>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="kpi-card card p-3 text-center">
          <div class="kpi-icon text-warning"><i class="bi bi-receipt fs-4"></i></div>
          <div class="kpi-value">{{ anual.count_general }}</div>
          <div class="kpi-label">Documentos {{ anual.year }}</div>
        </div>
      </div>
    </div>

    <!-- ── Tabs ───────────────────────────────────────────────────── -->
    <div class="tabs-bar mb-3">
      <button
        v-for="t in tabs" :key="t.id"
        class="tab-btn"
        :class="{ active: activeTab === t.id }"
        @click="activeTab = t.id"
      >
        <i :class="t.icon + ' me-1'"></i>{{ t.label }}
      </button>
    </div>

    <!-- ════════════════════════════════════════════════════════════ -->
    <!-- TAB 1: Valores                                              -->
    <!-- ════════════════════════════════════════════════════════════ -->
    <div v-if="activeTab === 'valores'" class="tab-content card p-3">
      <div v-if="!anual" class="text-center text-muted py-4">
        <i class="bi bi-bar-chart-line fs-1 d-block mb-2 opacity-25"></i>
        Selecciona año y tipo, luego pulsa <strong>Cargar</strong>.
      </div>
      <div v-else class="table-responsive">
        <table class="table table-sm table-hover align-middle metricas-table">
          <thead class="table-dark">
            <tr>
              <th>#</th>
              <th>Mes</th>
              <th class="text-end">Documentos</th>
              <th class="text-end">Total</th>
              <th class="text-end">% del Año</th>
              <th>Barra</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="m in anual.meses" :key="m.mes"
              :class="{ 'fw-semibold text-primary': m.mes === mejorMes?.mes }"
            >
              <td class="text-muted small">{{ m.mes }}</td>
              <td>{{ m.nombre_mes }}</td>
              <td class="text-end">{{ m.count }}</td>
              <td class="text-end">{{ fmt(m.total) }}</td>
              <td class="text-end">{{ pct(m.total, anual.total_general) }}%</td>
              <td style="min-width:80px">
                <div class="progress" style="height:8px">
                  <div
                    class="progress-bar bg-primary"
                    :style="{ width: pct(m.total, anual.total_general) + '%' }"
                  ></div>
                </div>
              </td>
            </tr>
          </tbody>
          <tfoot class="table-secondary fw-bold">
            <tr>
              <td colspan="2">Total {{ anual.year }}</td>
              <td class="text-end">{{ anual.count_general }}</td>
              <td class="text-end">{{ fmt(anual.total_general) }}</td>
              <td class="text-end">100%</td>
              <td></td>
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
        <i class="bi bi-graph-up-arrow fs-1 d-block mb-2 opacity-25"></i>
        Selecciona año y tipo, luego pulsa <strong>Cargar</strong>.
      </div>
      <div v-else>
        <p class="text-muted small mb-2">
          Ventas {{ tipoLabel }} — {{ anual.year }}
        </p>
        <div class="chart-wrapper">
          <canvas ref="canvasAnual"></canvas>
        </div>
      </div>
    </div>

    <!-- ════════════════════════════════════════════════════════════ -->
    <!-- TAB 3: Semana a Semana                                      -->
    <!-- ════════════════════════════════════════════════════════════ -->
    <div v-if="activeTab === 'semana'" class="tab-content card p-3">
      <div v-if="!mensual" class="text-center text-muted py-4">
        <i class="bi bi-calendar3-week fs-1 d-block mb-2 opacity-25"></i>
        Selecciona mes y tipo, luego pulsa <strong>Cargar</strong>.
      </div>
      <div v-else>
        <p class="text-muted small mb-2">
          Ventas {{ tipoLabel }} — {{ mensual.nombre_mes }} {{ mensual.year }}
          · Total: <strong>{{ fmt(mensual.total_mes) }}</strong>
          · {{ mensual.count_mes }} documentos
        </p>

        <!-- Gráfico diario -->
        <div class="chart-wrapper mb-4">
          <canvas ref="canvasMensual"></canvas>
        </div>

        <!-- Tabla por semanas -->
        <div v-for="sem in semanas" :key="sem.num" class="mb-3">
          <div class="semana-header d-flex justify-content-between align-items-center mb-1">
            <span class="badge bg-primary">Semana {{ sem.num }}</span>
            <span class="text-muted small">
              {{ sem.dias.length }} día(s) con ventas ·
              <strong>{{ fmt(sem.total) }}</strong> ·
              {{ sem.count }} doc.
            </span>
          </div>
          <div class="table-responsive">
            <table class="table table-sm align-middle mb-0 semana-table">
              <thead class="table-light">
                <tr>
                  <th>Fecha</th>
                  <th>Día</th>
                  <th class="text-end">Docs</th>
                  <th class="text-end">Total</th>
                  <th>Barra</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="d in sem.dias" :key="d.fecha">
                  <td class="text-muted small">{{ d.fecha }}</td>
                  <td>{{ d.dia_nombre }}</td>
                  <td class="text-end">{{ d.count }}</td>
                  <td class="text-end fw-semibold">{{ fmt(d.total) }}</td>
                  <td style="min-width:70px">
                    <div class="progress" style="height:6px">
                      <div
                        class="progress-bar bg-info"
                        :style="{ width: pct(d.total, mensual.total_mes) + '%' }"
                      ></div>
                    </div>
                  </td>
                </tr>
              </tbody>
              <tfoot class="fw-bold table-secondary">
                <tr>
                  <td colspan="2">Subtotal Sem. {{ sem.num }}</td>
                  <td class="text-end">{{ sem.count }}</td>
                  <td class="text-end">{{ fmt(sem.total) }}</td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </div>
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

// ── Estado ─────────────────────────────────────────────────────────────
const now = new Date()
const selectedYear  = ref(now.getFullYear())
const selectedMonth = ref(now.getMonth() + 1)
const selectedTipo  = ref('ambos')
const cargando      = ref(false)
const descargando   = ref(false)
const activeTab     = ref('valores')

const anual   = ref(null)
const mensual = ref(null)

const canvasAnual   = ref(null)
const canvasMensual = ref(null)
let chartAnual   = null
let chartMensual = null

// ── Opciones estáticas ─────────────────────────────────────────────────
const years = Array.from({ length: 6 }, (_, i) => now.getFullYear() - i)

const mesesOpciones = [
  { v: 1,  l: 'Enero' },   { v: 2,  l: 'Febrero' }, { v: 3,  l: 'Marzo' },
  { v: 4,  l: 'Abril' },   { v: 5,  l: 'Mayo' },    { v: 6,  l: 'Junio' },
  { v: 7,  l: 'Julio' },   { v: 8,  l: 'Agosto' },  { v: 9,  l: 'Septiembre' },
  { v: 10, l: 'Octubre' }, { v: 11, l: 'Noviembre' },{ v: 12, l: 'Diciembre' },
]

const tabs = [
  { id: 'valores', label: 'Valores',          icon: 'bi bi-table' },
  { id: 'grafico', label: 'Gráfico Anual',    icon: 'bi bi-bar-chart-line' },
  { id: 'semana',  label: 'Semana a Semana',  icon: 'bi bi-calendar3-week' },
]

// ── Computed ───────────────────────────────────────────────────────────
const tipoLabel = computed(() => ({
  ambos: 'Facturas + Recibos', facturas: 'Facturas', recibos: 'Recibos',
}[selectedTipo.value]))

const mejorMes = computed(() => {
  if (!anual.value) return null
  return [...anual.value.meses].sort((a, b) => b.total - a.total)[0]
})

const promedioMensual = computed(() => {
  if (!anual.value) return 0
  const conVentas = anual.value.meses.filter(m => m.total > 0)
  return conVentas.length ? anual.value.total_general / conVentas.length : 0
})

const semanas = computed(() => {
  if (!mensual.value) return []
  const mapa = {}
  for (const d of mensual.value.dias) {
    const s = d.semana_del_mes
    if (!mapa[s]) mapa[s] = { num: s, dias: [], total: 0, count: 0 }
    mapa[s].dias.push(d)
    mapa[s].total += d.total
    mapa[s].count += d.count
  }
  return Object.values(mapa).sort((a, b) => a.num - b.num)
})

// ── Formato moneda ─────────────────────────────────────────────────────
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

function pct(value, total) {
  if (!total) return '0.0'
  return ((value / total) * 100).toFixed(1)
}

// ── Descarga Excel ─────────────────────────────────────────────────────
async function descargarExcel() {
  descargando.value = true
  try {
    const cid = companyStore.selectedCompany?.id
    const params = new URLSearchParams({
      year: selectedYear.value,
      month: selectedMonth.value,
      tipo: selectedTipo.value,
      ...(cid ? { company_id: cid } : {}),
    })
    const token = localStorage.getItem('token') || sessionStorage.getItem('token') || ''
    const res = await fetch(`/api/metricas/export-excel?${params}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!res.ok) throw new Error('Error al generar Excel')
    const blob = await res.blob()
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `ventas_${selectedYear.value}-${String(selectedMonth.value).padStart(2,'0')}_${selectedTipo.value}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error(e)
  } finally {
    descargando.value = false
  }
}

// ── Carga de datos ─────────────────────────────────────────────────────
async function cargarTodo() {
  cargando.value = true
  try {
    const cid = companyStore.selectedCompany?.id
    const [resAnual, resMensual] = await Promise.all([
      api.get('/api/metricas/ventas/anual', {
        params: { year: selectedYear.value, tipo: selectedTipo.value, company_id: cid },
      }),
      api.get('/api/metricas/ventas/mensual', {
        params: { year: selectedYear.value, month: selectedMonth.value, tipo: selectedTipo.value, company_id: cid },
      }),
    ])
    anual.value   = resAnual.data
    mensual.value = resMensual.data
  } catch (e) {
    console.error('Error cargando métricas:', e)
  } finally {
    cargando.value = false
  }
}

// ── Gráficos ───────────────────────────────────────────────────────────
const CHART_COLORS = {
  primary:     'rgba(13, 110, 253, 0.85)',
  primaryBorder:'rgba(13, 110, 253, 1)',
  info:        'rgba(13, 202, 240, 0.85)',
  infoBorder:  'rgba(13, 202, 240, 1)',
}

function buildChartAnual() {
  if (!anual.value || !canvasAnual.value) return
  if (chartAnual) { chartAnual.destroy(); chartAnual = null }

  const labels = anual.value.meses.map(m => m.nombre_mes.substring(0, 3))
  const data   = anual.value.meses.map(m => m.total)

  chartAnual = new Chart(canvasAnual.value, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: tipoLabel.value,
        data,
        backgroundColor: CHART_COLORS.primary,
        borderColor:     CHART_COLORS.primaryBorder,
        borderWidth: 1,
        borderRadius: 4,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ' ' + fmt(ctx.parsed.y),
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { callback: v => fmt(v) },
          grid: { color: 'rgba(0,0,0,0.05)' },
        },
        x: { grid: { display: false } },
      },
    },
  })
}

function buildChartMensual() {
  if (!mensual.value || !canvasMensual.value) return
  if (chartMensual) { chartMensual.destroy(); chartMensual = null }

  const labels = mensual.value.dias.map(d => `${d.dia} ${d.dia_abrev}`)
  const data   = mensual.value.dias.map(d => d.total)

  chartMensual = new Chart(canvasMensual.value, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: tipoLabel.value,
        data,
        backgroundColor: CHART_COLORS.info,
        borderColor:     CHART_COLORS.infoBorder,
        borderWidth: 1,
        borderRadius: 3,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ' ' + fmt(ctx.parsed.y),
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { callback: v => fmt(v) },
          grid: { color: 'rgba(0,0,0,0.05)' },
        },
        x: { grid: { display: false } },
      },
    },
  })
}

// Reconstruir gráfico cuando cambia el tab activo o los datos
watch([activeTab, anual], async ([tab]) => {
  if (tab === 'grafico' && anual.value) {
    await nextTick()
    buildChartAnual()
  }
})

watch([activeTab, mensual], async ([tab]) => {
  if (tab === 'semana' && mensual.value) {
    await nextTick()
    buildChartMensual()
  }
})

onUnmounted(() => {
  chartAnual?.destroy()
  chartMensual?.destroy()
})
</script>

<style scoped>
.metricas-ventas {
  padding: 1rem;
  max-width: 1100px;
}

/* ── Filtros ─────────────────────────────────────── */
.filtros-bar { border-left: 4px solid #0d6efd; }

/* ── KPI Cards ───────────────────────────────────── */
.kpi-card {
  border-top: 3px solid #0d6efd;
  transition: box-shadow .2s;
}
.kpi-card:hover { box-shadow: 0 4px 12px rgba(13,110,253,.15); }
.kpi-icon { margin-bottom: .25rem; }
.kpi-value {
  font-size: 1.1rem;
  font-weight: 700;
  line-height: 1.2;
  color: #212529;
  word-break: break-all;
}
.kpi-label { font-size: .72rem; color: #6c757d; margin-top: .15rem; }

/* ── Tabs ────────────────────────────────────────── */
.tabs-bar { display: flex; gap: .5rem; flex-wrap: wrap; }
.tab-btn {
  padding: .45rem 1rem;
  border: 1px solid #dee2e6;
  border-radius: .375rem;
  background: #fff;
  font-size: .85rem;
  cursor: pointer;
  transition: all .15s;
  color: #495057;
}
.tab-btn:hover { background: #f0f4ff; border-color: #0d6efd; color: #0d6efd; }
.tab-btn.active {
  background: #0d6efd;
  border-color: #0d6efd;
  color: #fff;
  font-weight: 600;
}

/* ── Tab Content ─────────────────────────────────── */
.tab-content { min-height: 200px; }

/* ── Tabla métricas ──────────────────────────────── */
.metricas-table thead th { font-size: .8rem; }
.metricas-table td, .metricas-table th { white-space: nowrap; }

/* ── Gráfico ─────────────────────────────────────── */
.chart-wrapper { position: relative; max-height: 380px; }

/* ── Semana header ───────────────────────────────── */
.semana-header { padding: .4rem .6rem; background: #f8f9fa; border-radius: .375rem; }
.semana-table thead th { font-size: .78rem; }

/* ════════ Responsive ══════════════════════════════ */
@media (max-width: 768px) {
  .metricas-ventas { padding: .5rem; }
  .kpi-value { font-size: .95rem; }
  .chart-wrapper { max-height: 260px; }
  .tab-btn { font-size: .78rem; padding: .35rem .7rem; }
  .metricas-table th, .metricas-table td { font-size: .75rem; }
}

@media (max-width: 576px) {
  .tabs-bar { gap: .3rem; }
  .tab-btn { font-size: .72rem; padding: .3rem .55rem; }
  .kpi-value { font-size: .85rem; }
  .kpi-label { font-size: .65rem; }
  .chart-wrapper { max-height: 200px; }
}
</style>
