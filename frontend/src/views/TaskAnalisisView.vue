<template>
  <div class="page-container">

    <!-- ENCABEZADO -->
    <div class="page-header">
      <div class="header-left">
        <button class="btn-back" @click="$router.back()">
          <i class="bi bi-arrow-left"></i>
        </button>
        <div>
          <h1 class="page-title">
            <i class="bi bi-graph-up-arrow"></i> Análisis de Ejecución
          </h1>
          <p class="page-subtitle" v-if="task">
            <strong>{{ task.title }}</strong>
            <span class="status-badge ms-2" :class="statusClass(task.status_id)">
              {{ task.status_name }}
            </span>
          </p>
        </div>
      </div>
      <button class="btn btn-outline-secondary" @click="window.print()">
        <i class="bi bi-printer"></i> Exportar PDF
      </button>
    </div>

    <div v-if="loading" class="loading-center">
      <i class="bi bi-arrow-repeat spin"></i> Calculando análisis...
    </div>

    <template v-else-if="task">

      <!-- ── TARJETAS DE MÉTRICAS ───────────────────────── -->
      <div class="metrics-grid">

        <!-- Tiempo -->
        <div class="metric-card" :class="timeStatus.card">
          <div class="metric-icon"><i class="bi bi-calendar-range"></i></div>
          <div class="metric-body">
            <span class="metric-label">Tiempo transcurrido</span>
            <span class="metric-value">{{ daysElapsed }} días</span>
            <span class="metric-sub">
              de {{ daysEstimated > 0 ? daysEstimated + ' estimados' : 'sin fecha límite' }}
            </span>
            <div class="metric-bar">
              <div class="mbar-fill" :class="timeStatus.bar"
                :style="{ width: Math.min(timePercent, 100) + '%' }"></div>
            </div>
            <span class="metric-deviation" :class="timeStatus.text">
              {{ timeStatus.label }}
            </span>
          </div>
        </div>

        <!-- Costo -->
        <div class="metric-card" :class="costStatus.card">
          <div class="metric-icon"><i class="bi bi-cash-stack"></i></div>
          <div class="metric-body">
            <span class="metric-label">Costo ejecutado</span>
            <span class="metric-value">${{ fmt(totalCost) }}</span>
            <span class="metric-sub">
              de ${{ fmt(task.budget_labor_cost) }} presupuestados
            </span>
            <div class="metric-bar">
              <div class="mbar-fill" :class="costStatus.bar"
                :style="{ width: Math.min(costPercent, 100) + '%' }"></div>
            </div>
            <span class="metric-deviation" :class="costStatus.text">
              {{ costStatus.label }}
            </span>
          </div>
        </div>

        <!-- Avance -->
        <div class="metric-card card-blue">
          <div class="metric-icon"><i class="bi bi-bar-chart-fill"></i></div>
          <div class="metric-body">
            <span class="metric-label">Avance actual</span>
            <span class="metric-value">{{ task.progress }}%</span>
            <span class="metric-sub">
              {{ task.progress === 100 ? 'Completado ✓' : (100 - task.progress) + '% pendiente' }}
            </span>
            <div class="metric-bar">
              <div class="mbar-fill mbar-blue"
                :style="{ width: task.progress + '%' }"></div>
            </div>
            <span class="metric-deviation">
              {{ reports.length }} reporte(s) registrado(s)
            </span>
          </div>
        </div>

        <!-- Materiales vs Gastos -->
        <div class="metric-card card-neutral">
          <div class="metric-icon"><i class="bi bi-pie-chart-fill"></i></div>
          <div class="metric-body">
            <span class="metric-label">Composición del costo</span>
            <span class="metric-value">${{ fmt(totalCost) }}</span>
            <div class="cost-breakdown">
              <div class="cb-item">
                <span class="cb-dot dot-blue"></span>
                <span>Materiales</span>
                <strong>${{ fmt(totalMaterials) }}</strong>
              </div>
              <div class="cb-item">
                <span class="cb-dot dot-amber"></span>
                <span>Gastos</span>
                <strong>${{ fmt(totalExpenses) }}</strong>
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- ── GRÁFICO DE AVANCE ──────────────────────────── -->
      <div class="chart-card" v-if="reports.length > 0 || task.progress > 0">
        <h3 class="chart-title">
          <i class="bi bi-graph-up"></i> Progreso en el tiempo
        </h3>
        <div class="chart-wrap">
          <svg :viewBox="`0 0 ${SVG_W} ${SVG_H}`" class="progress-svg"
            preserveAspectRatio="none">

            <!-- Grid lines -->
            <line v-for="y in [0,25,50,75,100]" :key="y"
              :x1="MARGIN_L" :y1="yPos(y)"
              :x2="SVG_W - MARGIN_R" :y2="yPos(y)"
              stroke="#f1f5f9" stroke-width="1" />

            <!-- Labels Y -->
            <text v-for="y in [0,25,50,75,100]" :key="`yl${y}`"
              :x="MARGIN_L - 6" :y="yPos(y) + 4"
              font-size="9" fill="#94a3b8" text-anchor="end">{{ y }}%</text>

            <!-- Línea esperada (0% → 100% en el tiempo estimado) -->
            <line v-if="daysEstimated > 0 && task.start_date"
              :x1="MARGIN_L" :y1="yPos(0)"
              :x2="SVG_W - MARGIN_R" :y2="yPos(100)"
              stroke="#e2e8f0" stroke-width="1.5" stroke-dasharray="5,4" />

            <!-- Línea de avance real -->
            <polyline
              :points="chartPoints"
              fill="none" stroke="#3b82f6" stroke-width="2.5"
              stroke-linecap="round" stroke-linejoin="round" />

            <!-- Área bajo la curva -->
            <polygon
              :points="chartArea"
              fill="url(#blueGrad)" opacity="0.15" />

            <!-- Puntos -->
            <circle v-for="(pt, i) in chartData" :key="i"
              :cx="pt.x" :cy="pt.y" r="4"
              fill="#3b82f6" stroke="#fff" stroke-width="2">
              <title>{{ pt.label }}</title>
            </circle>

            <!-- Gradiente -->
            <defs>
              <linearGradient id="blueGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#3b82f6" />
                <stop offset="100%" stop-color="#3b82f6" stop-opacity="0" />
              </linearGradient>
            </defs>

          </svg>

          <!-- Labels X -->
          <div class="chart-x-labels">
            <span v-for="(pt, i) in chartData" :key="i"
              class="x-label"
              :style="{ left: ((pt.x - MARGIN_L) / (SVG_W - MARGIN_L - MARGIN_R) * 100) + '%' }">
              {{ pt.dateLabel }}
            </span>
          </div>
        </div>

        <div class="chart-legend">
          <span class="legend-item">
            <span class="leg-line leg-real"></span> Avance real
          </span>
          <span class="legend-item" v-if="daysEstimated > 0">
            <span class="leg-line leg-expected"></span> Avance esperado
          </span>
        </div>
      </div>

      <!-- ── MATERIALES DETALLE ─────────────────────────── -->
      <div class="detail-card" v-if="materials.length > 0">
        <h3 class="detail-title"><i class="bi bi-boxes"></i> Materiales utilizados</h3>
        <table class="det-table">
          <thead>
            <tr><th>Material</th><th>Unidad</th><th class="text-right">Cant.</th>
              <th class="text-right">Costo unit.</th><th class="text-right">Total</th></tr>
          </thead>
          <tbody>
            <tr v-for="m in materials" :key="m.id">
              <td>{{ m.name }}</td>
              <td class="text-muted">{{ m.unit||'—' }}</td>
              <td class="text-right">{{ m.quantity }}</td>
              <td class="text-right text-muted">${{ fmt(m.unit_cost) }}</td>
              <td class="text-right"><strong>${{ fmt(m.total_cost) }}</strong></td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="total-row">
              <td colspan="4" class="text-right"><strong>Total materiales:</strong></td>
              <td class="text-right"><strong class="total-val">${{ fmt(totalMaterials) }}</strong></td>
            </tr>
          </tfoot>
        </table>
      </div>

      <!-- ── GASTOS DETALLE ─────────────────────────────── -->
      <div class="detail-card" v-if="expenses.length > 0">
        <h3 class="detail-title"><i class="bi bi-receipt"></i> Gastos pagados</h3>
        <table class="det-table">
          <thead>
            <tr><th>Concepto</th><th>Fecha</th><th>Recibo</th><th class="text-right">Monto</th></tr>
          </thead>
          <tbody>
            <tr v-for="e in expenses" :key="e.id">
              <td>{{ e.concept }}</td>
              <td class="text-muted">{{ fmtDate(e.payment_date) }}</td>
              <td class="text-muted">{{ e.receipt_ref||'—' }}</td>
              <td class="text-right"><strong>${{ fmt(e.amount) }}</strong></td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="total-row">
              <td colspan="3" class="text-right"><strong>Total gastos:</strong></td>
              <td class="text-right"><strong class="total-val">${{ fmt(totalExpenses) }}</strong></td>
            </tr>
          </tfoot>
        </table>
      </div>

    </template>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { useRoute } from "vue-router"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

const route  = useRoute()
const taskId = route.params.taskId

const task      = ref(null)
const materials = ref([])
const expenses  = ref([])
const reports   = ref([])
const loading   = ref(true)

// SVG dimensions
const SVG_W = 700, SVG_H = 200, MARGIN_L = 36, MARGIN_R = 16, MARGIN_T = 12, MARGIN_B = 20
function yPos(pct) { return MARGIN_T + (1 - pct / 100) * (SVG_H - MARGIN_T - MARGIN_B) }

// ── Computed metrics ──────────────────────────────────────────
const totalMaterials = computed(() => materials.value.reduce((s, m) => s + (m.total_cost||0), 0))
const totalExpenses  = computed(() => expenses.value.reduce((s, e) => s + (e.amount||0), 0))
const totalCost      = computed(() => totalMaterials.value + totalExpenses.value)

const daysElapsed = computed(() => {
  if (!task.value?.start_date) return 0
  const start = new Date(task.value.start_date)
  const end   = task.value.closed_at ? new Date(task.value.closed_at) : new Date()
  return Math.max(0, Math.ceil((end - start) / 86400000))
})

const daysEstimated = computed(() => {
  if (!task.value?.start_date || !task.value?.due_date) return 0
  const start = new Date(task.value.start_date)
  const end   = new Date(task.value.due_date)
  return Math.max(0, Math.ceil((end - start) / 86400000))
})

const timePercent = computed(() =>
  daysEstimated.value > 0 ? (daysElapsed.value / daysEstimated.value) * 100 : 0
)

const costPercent = computed(() =>
  task.value?.budget_labor_cost > 0
    ? (totalCost.value / task.value.budget_labor_cost) * 100
    : 0
)

function makeStatus(percent, labels) {
  if (percent <= 80)  return { card:"card-green",   bar:"mbar-green",  text:"text-green",  label: labels[0] }
  if (percent <= 100) return { card:"card-amber",   bar:"mbar-amber",  text:"text-amber",  label: labels[1] }
  return               { card:"card-red",     bar:"mbar-red",    text:"text-red",    label: labels[2] }
}

const timeStatus = computed(() => {
  if (daysEstimated.value === 0) return { card:"card-neutral", bar:"mbar-blue", text:"", label:"Sin fecha límite definida" }
  return makeStatus(timePercent.value, [
    `En tiempo (${Math.round(timePercent.value)}% del plazo)`,
    `Cerca del límite (${Math.round(timePercent.value)}%)`,
    `⚠ Excede el plazo en ${daysElapsed.value - daysEstimated.value} día(s)`,
  ])
})

const costStatus = computed(() => {
  if (!task.value?.budget_labor_cost) return { card:"card-neutral", bar:"mbar-blue", text:"", label:"Sin presupuesto definido" }
  return makeStatus(costPercent.value, [
    `Dentro del presupuesto (${Math.round(costPercent.value)}%)`,
    `Cerca del límite (${Math.round(costPercent.value)}%)`,
    `⚠ Excede presupuesto en $${fmt(totalCost.value - task.value.budget_labor_cost)}`,
  ])
})

// ── Gráfico SVG ───────────────────────────────────────────────
const chartData = computed(() => {
  const data = []
  // Punto inicial si hay fecha de inicio
  if (task.value?.start_date) {
    data.push({ date: new Date(task.value.start_date), pct: 0 })
  }
  reports.value.forEach(r => {
    data.push({ date: new Date(r.created_at), pct: r.progress_percent })
  })
  // Punto actual si el avance es > 0 y no hay reporte reciente con ese valor
  if (task.value?.progress > 0) {
    const last = data[data.length - 1]
    if (!last || last.pct !== task.value.progress) {
      data.push({ date: new Date(), pct: task.value.progress })
    }
  }
  if (data.length < 2) return []

  const minDate = data[0].date.getTime()
  const maxDate = data[data.length - 1].date.getTime()
  const rangeMs = maxDate - minDate || 1

  return data.map(d => ({
    x: MARGIN_L + ((d.date.getTime() - minDate) / rangeMs) * (SVG_W - MARGIN_L - MARGIN_R),
    y: yPos(d.pct),
    label: `${d.pct}% — ${d.date.toLocaleDateString("es-CO")}`,
    dateLabel: d.date.toLocaleDateString("es-CO", { day:"2-digit", month:"short" }),
  }))
})

const chartPoints = computed(() =>
  chartData.value.map(p => `${p.x},${p.y}`).join(" ")
)

const chartArea = computed(() => {
  if (!chartData.value.length) return ""
  const pts  = chartData.value.map(p => `${p.x},${p.y}`).join(" ")
  const last = chartData.value[chartData.value.length - 1]
  const first = chartData.value[0]
  return `${first.x},${yPos(0)} ${pts} ${last.x},${yPos(0)}`
})

// ── Helpers ───────────────────────────────────────────────────
const STATUS_CLASSES = {
  1:"badge-orange",2:"badge-blue",3:"badge-green",
  4:"badge-purple",5:"badge-darkgreen",6:"badge-red",
}
function statusClass(id) { return STATUS_CLASSES[id] || "badge-gray" }
function fmt(n)          { return Number(n||0).toLocaleString("es-CO") }
function fmtDate(iso)    { return iso ? new Date(iso).toLocaleDateString("es-CO", { day:"2-digit", month:"short", year:"numeric" }) : "" }

async function load() {
  loading.value = true
  try {
    const [tRes, mRes, eRes, rRes] = await Promise.all([
      api.get(`/tasks/${taskId}`),
      api.get(`/task-materials/${taskId}`),
      api.get(`/task-expenses/${taskId}`),
      api.get(`/task-progress/${taskId}`),
    ])
    task.value      = tRes.data
    materials.value = mRes.data
    expenses.value  = eRes.data
    reports.value   = rRes.data
  } catch {
    showToast("Error cargando análisis", "error")
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 960px; }
.page-header    { display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:20px; flex-wrap:wrap; gap:12px; }
.header-left    { display:flex; align-items:flex-start; gap:12px; }
.btn-back       { background:#f1f5f9; border:none; border-radius:8px; padding:8px 12px; cursor:pointer; font-size:16px; color:#475569; }
.btn-back:hover { background:#e2e8f0; }
.page-title     { font-size:20px; font-weight:700; color:#1e293b; margin:0 0 4px; display:flex; align-items:center; gap:8px; }
.page-subtitle  { font-size:13px; color:#64748b; margin:0; display:flex; align-items:center; gap:6px; }
.loading-center { padding:60px; text-align:center; color:#94a3b8; }

/* MÉTRICAS */
.metrics-grid { display:grid; grid-template-columns:repeat(2, 1fr); gap:14px; margin-bottom:20px; }
.metric-card  { background:#fff; border-radius:14px; box-shadow:0 1px 6px rgba(0,0,0,0.08); padding:18px; display:flex; gap:14px; align-items:flex-start; border-left:4px solid #e2e8f0; }
.metric-icon  { width:44px; height:44px; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:20px; flex-shrink:0; background:#f8fafc; color:#64748b; }
.metric-body  { display:flex; flex-direction:column; gap:3px; flex:1; min-width:0; }
.metric-label { font-size:11px; text-transform:uppercase; letter-spacing:0.4px; color:#94a3b8; font-weight:600; }
.metric-value { font-size:22px; font-weight:800; color:#1e293b; line-height:1; }
.metric-sub   { font-size:12px; color:#94a3b8; }
.metric-deviation { font-size:12px; font-weight:600; margin-top:2px; }

.metric-bar  { height:6px; background:#f1f5f9; border-radius:3px; overflow:hidden; margin:6px 0 2px; }
.mbar-fill   { height:100%; border-radius:3px; transition:width 0.6s ease; }
.mbar-green  { background:#22c55e; }
.mbar-amber  { background:#f59e0b; }
.mbar-red    { background:#ef4444; }
.mbar-blue   { background:#3b82f6; }

.card-green   { border-left-color:#22c55e; }
.card-green .metric-icon { background:#f0fdf4; color:#22c55e; }
.card-amber   { border-left-color:#f59e0b; }
.card-amber .metric-icon { background:#fffbeb; color:#f59e0b; }
.card-red     { border-left-color:#ef4444; }
.card-red .metric-icon   { background:#fef2f2; color:#ef4444; }
.card-blue    { border-left-color:#3b82f6; }
.card-blue .metric-icon  { background:#eff6ff; color:#3b82f6; }
.card-neutral { border-left-color:#94a3b8; }

.text-green { color:#16a34a; }
.text-amber { color:#d97706; }
.text-red   { color:#ef4444; }

/* COST BREAKDOWN */
.cost-breakdown { display:flex; flex-direction:column; gap:4px; margin-top:6px; }
.cb-item { display:flex; align-items:center; gap:6px; font-size:12px; color:#475569; }
.cb-item strong { margin-left:auto; color:#1e293b; }
.cb-dot  { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
.dot-blue  { background:#3b82f6; }
.dot-amber { background:#f59e0b; }

/* CHART */
.chart-card  { background:#fff; border-radius:14px; box-shadow:0 1px 6px rgba(0,0,0,0.08); padding:18px 20px; margin-bottom:16px; }
.chart-title { font-size:14px; font-weight:700; color:#475569; display:flex; align-items:center; gap:7px; margin:0 0 14px; }
.chart-wrap  { position:relative; }
.progress-svg { width:100%; height:180px; display:block; }
.chart-x-labels { position:relative; height:20px; margin-top:2px; }
.x-label { position:absolute; transform:translateX(-50%); font-size:10px; color:#94a3b8; white-space:nowrap; }
.chart-legend { display:flex; gap:16px; margin-top:6px; justify-content:center; }
.legend-item { display:flex; align-items:center; gap:6px; font-size:11px; color:#64748b; }
.leg-line    { width:20px; height:2px; border-radius:2px; }
.leg-real    { background:#3b82f6; }
.leg-expected { background:#e2e8f0; border:1px dashed #94a3b8; }

/* DETAIL TABLES */
.detail-card  { background:#fff; border-radius:14px; box-shadow:0 1px 6px rgba(0,0,0,0.08); overflow:hidden; margin-bottom:16px; }
.detail-title { font-size:14px; font-weight:700; color:#475569; display:flex; align-items:center; gap:7px; padding:14px 16px; border-bottom:1px solid #f1f5f9; margin:0; }
.det-table   { width:100%; border-collapse:collapse; font-size:13px; }
.det-table th { background:#f8fafc; color:#475569; font-weight:600; font-size:11px; text-transform:uppercase; letter-spacing:0.4px; padding:10px 14px; border-bottom:1px solid #e2e8f0; }
.det-table td { padding:11px 14px; border-bottom:1px solid #f1f5f9; vertical-align:middle; }
.det-table tr:last-child td { border-bottom:none; }
.total-row td { background:#f0fdf4 !important; }
.total-val    { font-size:15px; color:#16a34a; }
.text-right   { text-align:right; }
.text-muted   { color:#94a3b8 !important; font-size:12px; }

/* STATUS BADGES */
.status-badge    { font-size:11px; font-weight:700; padding:2px 9px; border-radius:20px; }
.badge-orange    { background:#fff7ed; color:#c2410c; }
.badge-blue      { background:#dbeafe; color:#1e40af; }
.badge-green     { background:#dcfce7; color:#16a34a; }
.badge-purple    { background:#f3e8ff; color:#7c3aed; }
.badge-darkgreen { background:#d1fae5; color:#065f46; }
.badge-red       { background:#fef2f2; color:#b91c1c; }
.badge-gray      { background:#f1f5f9; color:#64748b; }

.spin { display:inline-block; animation:spin 0.8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

@media (max-width:640px) { .metrics-grid { grid-template-columns:1fr; } }

@media print {
  .btn-back, .page-header button { display:none !important; }
  .page-container { padding:0; }
}
</style>
