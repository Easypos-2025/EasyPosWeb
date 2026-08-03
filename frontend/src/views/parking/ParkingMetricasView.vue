<template>
  <div class="pkm-page">

    <!-- ══ FILTROS ══════════════════════════════════════════════════════════ -->
    <div class="pkm-filtros card p-3 mb-3">
      <!-- Atajos de período -->
      <div class="pkm-shortcuts">
        <button v-for="s in SHORTCUTS" :key="s.key"
          :class="['pkm-shortcut', { 'pkm-shortcut--act': shortcutActivo === s.key }]"
          @click="aplicarShortcut(s.key)">
          {{ s.label }}
        </button>
      </div>

      <!-- Rango personalizado -->
      <div v-if="shortcutActivo === 'custom'" class="pkm-custom-range">
        <div class="pkm-custom-field">
          <label>Desde</label>
          <CustomDatePicker v-model="filtros.desde" />
        </div>
        <div class="pkm-custom-field">
          <label>Hasta</label>
          <CustomDatePicker v-model="filtros.hasta" />
        </div>
      </div>

      <!-- Servicio + Agrupar + Consultar -->
      <div class="pkm-filtros-row">
        <div class="pkm-filtro-field">
          <label>Servicio</label>
          <select v-model="filtros.servicio" class="pkm-select">
            <option value="">Todos los servicios</option>
            <option v-for="s in serviciosDisponibles" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
        <div class="pkm-filtro-field">
          <label>Agrupar por</label>
          <select v-model="filtros.agrupar" class="pkm-select">
            <option value="dia">Día</option>
            <option value="mes">Mes</option>
          </select>
        </div>
        <button class="pkm-btn-consultar" :disabled="cargando" @click="cargar">
          <i v-if="cargando" class="bi bi-arrow-repeat spin"></i>
          <i v-else class="bi bi-search"></i>
          {{ cargando ? 'Consultando…' : 'Consultar' }}
        </button>
      </div>

      <div class="pkm-periodo-label">
        <i class="bi bi-calendar3"></i>
        {{ fmtFecha(filtros.desde) }} → {{ fmtFecha(filtros.hasta) }}
      </div>
    </div>

    <div v-if="cargando && !summary" class="pkm-loading">
      <i class="bi bi-arrow-repeat spin"></i> Cargando métricas…
    </div>

    <template v-else-if="summary">

      <!-- ══ KPI RESUMEN ════════════════════════════════════════════════════ -->
      <div class="pkm-kpi-bar">
        <div class="pkm-kpi pkm-kpi--ingresos">
          <i class="bi bi-car-front-fill"></i>
          <div>
            <span class="pkm-kpi-val">{{ summary.total_ordenes ?? 0 }}</span>
            <span class="pkm-kpi-lbl">Total ingresos</span>
          </div>
        </div>
        <div class="pkm-kpi pkm-kpi--recaudo">
          <i class="bi bi-cash-coin"></i>
          <div>
            <span class="pkm-kpi-val">{{ fmtMini(summary.recaudado) }}</span>
            <span class="pkm-kpi-lbl">Recaudado</span>
          </div>
        </div>
        <div class="pkm-kpi pkm-kpi--cobro">
          <i class="bi bi-check-circle-fill"></i>
          <div>
            <span class="pkm-kpi-val">{{ summary.con_cobro ?? 0 }}</span>
            <span class="pkm-kpi-lbl">Con cobro</span>
          </div>
        </div>
        <div class="pkm-kpi pkm-kpi--cortesia">
          <i class="bi bi-gift-fill"></i>
          <div>
            <span class="pkm-kpi-val">{{ summary.cortesias ?? 0 }}</span>
            <span class="pkm-kpi-lbl">Cortesías</span>
          </div>
        </div>
        <div class="pkm-kpi pkm-kpi--promedio">
          <i class="bi bi-graph-up-arrow"></i>
          <div>
            <span class="pkm-kpi-val">{{ fmtMini(promedioIngreso) }}</span>
            <span class="pkm-kpi-lbl">Promedio/ingreso</span>
          </div>
        </div>
      </div>

      <!-- ══ GRÁFICOS ════════════════════════════════════════════════════ -->
      <div class="pkm-charts-row">
        <div class="pkm-chart-card card p-3">
          <div class="pkm-chart-title"><i class="bi bi-bar-chart-fill"></i> Ingresos por {{ filtros.agrupar === 'mes' ? 'mes' : 'día' }}</div>
          <canvas ref="canvasIngresos" height="160"></canvas>
        </div>
        <div class="pkm-chart-card card p-3">
          <div class="pkm-chart-title"><i class="bi bi-currency-dollar"></i> Recaudado por {{ filtros.agrupar === 'mes' ? 'mes' : 'día' }}</div>
          <canvas ref="canvasRecaudo" height="160"></canvas>
        </div>
      </div>

      <!-- ══ TABLA POR SERVICIO ════════════════════════════════════════════ -->
      <div class="card p-3 mb-3">
        <div class="pkm-table-title"><i class="bi bi-list-check"></i> Por servicio</div>
        <div v-if="servicios.length === 0" class="pkm-empty-table">Sin datos para este período</div>
        <div v-else class="pkm-table-wrap">
          <table class="pkm-table">
            <thead>
              <tr>
                <th>Servicio</th>
                <th class="text-end">Usos</th>
                <th class="text-end">Unidades</th>
                <th class="text-end">Recaudado</th>
                <th class="text-end">% ingresos</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in servicios" :key="s.servicio">
                <td><span class="pkm-svc-pill">{{ s.servicio }}</span></td>
                <td class="text-end fw-semibold">{{ s.total_usos }}</td>
                <td class="text-end">{{ s.total_unidades }}</td>
                <td class="text-end">{{ fmt(s.recaudado) }}</td>
                <td class="text-end">
                  <div class="pkm-pct-bar-wrap">
                    <div class="pkm-pct-bar" :style="{ width: pctUsos(s.total_usos) + '%' }"></div>
                    <span>{{ pctUsos(s.total_usos) }}%</span>
                  </div>
                </td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td><strong>TOTAL</strong></td>
                <td class="text-end"><strong>{{ totalUsos }}</strong></td>
                <td class="text-end"><strong>{{ totalUnidades }}</strong></td>
                <td class="text-end"><strong>{{ fmt(summary.recaudado) }}</strong></td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      <!-- ══ TABLA POR PERÍODO ════════════════════════════════════════════ -->
      <div class="card p-3 mb-3">
        <div class="pkm-table-title">
          <i class="bi bi-calendar-week"></i>
          Por {{ filtros.agrupar === 'mes' ? 'mes' : 'día' }}
        </div>
        <div v-if="periodos.length === 0" class="pkm-empty-table">Sin datos para este período</div>
        <div v-else class="pkm-table-wrap">
          <table class="pkm-table">
            <thead>
              <tr>
                <th>{{ filtros.agrupar === 'mes' ? 'Mes' : 'Fecha' }}</th>
                <th class="text-end">Ingresos</th>
                <th class="text-end">Con cobro</th>
                <th class="text-end">Cortesías</th>
                <th class="text-end">Recaudado</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in periodos" :key="p.periodo">
                <td class="pkm-td-fecha">{{ p.periodo_label }}</td>
                <td class="text-end fw-semibold">{{ p.total_ordenes }}</td>
                <td class="text-end"><span class="pkm-badge pkm-badge--cobro">{{ p.con_cobro }}</span></td>
                <td class="text-end"><span class="pkm-badge pkm-badge--cortesia">{{ p.cortesias }}</span></td>
                <td class="text-end fw-semibold text-success">{{ fmt(p.recaudado) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </template>

    <div v-else-if="!cargando" class="pkm-empty">
      <i class="bi bi-bar-chart-line"></i>
      <p>Selecciona un período y pulsa <strong>Consultar</strong></p>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'
import { useCompanyStore } from '@/stores/companyStore'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'

Chart.register(...registerables)

const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id)

// ── Fecha helpers ─────────────────────────────────────────────────────────────
function hoyStr() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}
function primerDiaMes(offset = 0) {
  const d = new Date()
  d.setMonth(d.getMonth() + offset, 1)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-01`
}
function ultimoDiaMes(offset = 0) {
  const d = new Date()
  d.setMonth(d.getMonth() + offset + 1, 0)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}
function primerDiaSemana() {
  const d = new Date()
  const day = d.getDay()
  d.setDate(d.getDate() - (day === 0 ? 6 : day - 1))
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}
function primerDiaAnio() {
  return `${new Date().getFullYear()}-01-01`
}

const SHORTCUTS = [
  { key: 'hoy',      label: 'Hoy' },
  { key: 'semana',   label: 'Esta semana' },
  { key: 'mes',      label: 'Este mes' },
  { key: 'mes_ant',  label: 'Mes anterior' },
  { key: 'anio',     label: 'Este año' },
  { key: 'custom',   label: 'Personalizado' },
]

// ── Estado ────────────────────────────────────────────────────────────────────
const shortcutActivo = ref('mes')
const filtros = ref({ desde: primerDiaMes(), hasta: hoyStr(), servicio: '', agrupar: 'dia' })
const cargando = ref(false)
const summary  = ref(null)
const servicios = ref([])
const periodos  = ref([])
const serviciosDisponibles = ref([])

// ── Charts ────────────────────────────────────────────────────────────────────
const canvasIngresos = ref(null)
const canvasRecaudo  = ref(null)
let chartI = null
let chartR = null

// ── Computed ──────────────────────────────────────────────────────────────────
const totalUsos      = computed(() => servicios.value.reduce((s, x) => s + (x.total_usos || 0), 0))
const totalUnidades  = computed(() => servicios.value.reduce((s, x) => s + (x.total_unidades || 0), 0))
const promedioIngreso = computed(() => {
  const n = summary.value?.con_cobro || 0
  return n > 0 ? (summary.value.recaudado / n) : 0
})
function pctUsos(usos) {
  return totalUsos.value > 0 ? Math.round(usos / totalUsos.value * 100) : 0
}

// ── Atajos ────────────────────────────────────────────────────────────────────
function aplicarShortcut(key) {
  shortcutActivo.value = key
  const hoy = hoyStr()
  const map = {
    hoy:     { desde: hoy,              hasta: hoy },
    semana:  { desde: primerDiaSemana(), hasta: hoy },
    mes:     { desde: primerDiaMes(),   hasta: hoy },
    mes_ant: { desde: primerDiaMes(-1), hasta: ultimoDiaMes(-1) },
    anio:    { desde: primerDiaAnio(),  hasta: hoy },
    custom:  null,
  }
  if (map[key]) {
    filtros.value.desde = map[key].desde
    filtros.value.hasta = map[key].hasta
  }
  if (key !== 'custom') cargar()
}

// ── Carga ─────────────────────────────────────────────────────────────────────
async function cargar() {
  if (!companyId.value) return
  cargando.value = true
  try {
    const res = await api.get('/api/parking/metricas', {
      params: {
        company_id: companyId.value,
        desde:      filtros.value.desde,
        hasta:      filtros.value.hasta,
        servicio:   filtros.value.servicio || undefined,
        agrupar:    filtros.value.agrupar,
      },
    })
    summary.value             = res.data.summary
    servicios.value           = res.data.servicios
    periodos.value            = res.data.periodos
    serviciosDisponibles.value = res.data.servicios_disponibles
    await nextTick()
    buildCharts()
  } catch (e) {
    showToast(e?.response?.data?.detail || 'Error al cargar métricas', 'error', 3000)
  }
  cargando.value = false
}

// ── Charts ────────────────────────────────────────────────────────────────────
function buildCharts() {
  const labels  = periodos.value.map(p => String(p.periodo_label))
  const ingresos = periodos.value.map(p => p.total_ordenes)
  const recaudo  = periodos.value.map(p => Number(p.recaudado || 0))

  if (chartI) { chartI.destroy(); chartI = null }
  if (chartR) { chartR.destroy(); chartR = null }

  if (!canvasIngresos.value || !canvasRecaudo.value) return

  chartI = new Chart(canvasIngresos.value, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Con cobro',
          data: periodos.value.map(p => p.con_cobro),
          backgroundColor: 'rgba(13,110,253,.7)',
          borderColor: 'rgba(13,110,253,1)',
          borderWidth: 1, borderRadius: 4, stack: 'a',
        },
        {
          label: 'Cortesías',
          data: periodos.value.map(p => p.cortesias),
          backgroundColor: 'rgba(108,117,125,.5)',
          borderColor: 'rgba(108,117,125,1)',
          borderWidth: 1, borderRadius: 4, stack: 'a',
        },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } } },
      scales: {
        x: { stacked: true, grid: { display: false }, ticks: { font: { size: 10 } } },
        y: { stacked: true, beginAtZero: true, ticks: { stepSize: 1, font: { size: 10 } }, grid: { color: 'rgba(0,0,0,.05)' } },
      },
    },
  })

  chartR = new Chart(canvasRecaudo.value, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Recaudado',
        data: recaudo,
        backgroundColor: 'rgba(25,135,84,.7)',
        borderColor: 'rgba(25,135,84,1)',
        borderWidth: 1, borderRadius: 4,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => ' ' + fmt(ctx.parsed.y) } },
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 10 } } },
        y: { beginAtZero: true, ticks: { callback: v => fmtMini(v), font: { size: 10 } }, grid: { color: 'rgba(0,0,0,.05)' } },
      },
    },
  })
}

// ── Utilidades ────────────────────────────────────────────────────────────────
function fmt(val) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(val || 0)
}
function fmtMini(val) {
  if (!val) return '$0'
  if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`
  if (val >= 1000)    return `$${(val / 1000).toFixed(0)}K`
  return fmt(val)
}
function fmtFecha(str) {
  if (!str) return '—'
  const [y, m, d] = str.split('-')
  const meses = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic']
  return `${d} ${meses[parseInt(m)-1]} ${y}`
}

watch(companyId, (v) => { if (v) cargar() }, { immediate: true })

onUnmounted(() => {
  if (chartI) chartI.destroy()
  if (chartR) chartR.destroy()
})
</script>

<style scoped>
.pkm-page { padding: 16px; max-width: 1200px; margin: 0 auto; }

/* ── Filtros ── */
.pkm-filtros { display: flex; flex-direction: column; gap: 12px; }
.pkm-shortcuts { display: flex; flex-wrap: wrap; gap: 6px; }
.pkm-shortcut {
  padding: 6px 14px; border: 1.5px solid #dee2e6; border-radius: 20px;
  background: #fff; font-size: .82rem; cursor: pointer; transition: all .15s; font-weight: 500;
}
.pkm-shortcut:hover { border-color: #0d6efd; color: #0d6efd; }
.pkm-shortcut--act  { background: #0d6efd; color: #fff; border-color: #0d6efd; font-weight: 700; }

.pkm-custom-range { display: flex; gap: 12px; flex-wrap: wrap; align-items: flex-end; }
.pkm-custom-field { display: flex; flex-direction: column; gap: 4px; }
.pkm-custom-field label { font-size: .78rem; font-weight: 600; color: #495057; }

.pkm-filtros-row { display: flex; gap: 10px; align-items: flex-end; flex-wrap: wrap; }
.pkm-filtro-field { display: flex; flex-direction: column; gap: 4px; }
.pkm-filtro-field label { font-size: .78rem; font-weight: 600; color: #495057; }
.pkm-select { border: 1.5px solid #ced4da; border-radius: 8px; padding: 8px 12px; font-size: .88rem; outline: none; color: #212529; background: #fff; }
.pkm-select:focus { border-color: #0d6efd; }
.pkm-btn-consultar {
  display: flex; align-items: center; gap: 6px; padding: 9px 20px;
  border: none; border-radius: 8px; background: #0d6efd; color: #fff;
  font-size: .88rem; font-weight: 600; cursor: pointer; transition: background .15s;
}
.pkm-btn-consultar:hover:not(:disabled) { background: #0b5ed7; }
.pkm-btn-consultar:disabled { opacity: .6; cursor: default; }
.pkm-periodo-label { font-size: .78rem; color: #6c757d; display: flex; align-items: center; gap: 6px; }

/* ── KPI bar ── */
.pkm-kpi-bar { display: flex; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
.pkm-kpi {
  display: flex; align-items: center; gap: 12px; padding: 12px 18px;
  border-radius: 10px; color: #fff; font-weight: 600; flex: 1; min-width: 130px;
}
.pkm-kpi i { font-size: 1.4rem; opacity: .85; flex-shrink: 0; }
.pkm-kpi-val { display: block; font-size: 1.5rem; line-height: 1; }
.pkm-kpi-lbl { display: block; font-size: .7rem; opacity: .85; }
.pkm-kpi--ingresos  { background: #fd7e14; }
.pkm-kpi--recaudo   { background: #198754; }
.pkm-kpi--cobro     { background: #0d6efd; }
.pkm-kpi--cortesia  { background: #6f42c1; }
.pkm-kpi--promedio  { background: #20c997; }

/* ── Charts ── */
.pkm-charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 14px; }
.pkm-chart-card { display: flex; flex-direction: column; gap: 10px; }
.pkm-chart-title { font-size: .82rem; font-weight: 700; color: #495057; display: flex; align-items: center; gap: 6px; }
.pkm-chart-card canvas { min-height: 160px; max-height: 220px; }

/* ── Tablas ── */
.pkm-table-title { font-size: .82rem; font-weight: 700; color: #495057; margin-bottom: 12px; display: flex; align-items: center; gap: 6px; }
.pkm-table-wrap  { overflow-x: auto; }
.pkm-table { width: 100%; border-collapse: collapse; font-size: .85rem; }
.pkm-table th { padding: 8px 12px; border-bottom: 2px solid #e9ecef; color: #6c757d; font-size: .75rem; text-transform: uppercase; letter-spacing: .3px; white-space: nowrap; }
.pkm-table td { padding: 8px 12px; border-bottom: 1px solid #f1f3f5; vertical-align: middle; }
.pkm-table tbody tr:hover { background: #f8f9fa; }
.pkm-table tfoot td { padding: 10px 12px; border-top: 2px solid #e9ecef; border-bottom: none; font-weight: 700; }
.pkm-td-fecha { font-family: monospace; font-size: .8rem; }

.pkm-svc-pill { display: inline-flex; padding: 2px 10px; background: #e7f1ff; color: #084298; border-radius: 20px; font-size: .82rem; font-weight: 600; }
.pkm-badge { display: inline-flex; padding: 2px 8px; border-radius: 20px; font-size: .75rem; font-weight: 700; }
.pkm-badge--cobro    { background: #cfe2ff; color: #084298; }
.pkm-badge--cortesia { background: #e2d9f3; color: #432874; }

.pkm-pct-bar-wrap { display: flex; align-items: center; gap: 6px; justify-content: flex-end; }
.pkm-pct-bar { height: 6px; background: #0d6efd; border-radius: 3px; min-width: 4px; transition: width .3s; }

/* ── Estados vacíos ── */
.pkm-loading { text-align: center; padding: 60px; color: #6c757d; font-size: 1rem; }
.pkm-empty   { text-align: center; padding: 60px 20px; color: #adb5bd; }
.pkm-empty i { font-size: 3rem; display: block; margin-bottom: 12px; }
.pkm-empty-table { padding: 20px; text-align: center; color: #adb5bd; font-size: .88rem; }

.spin { animation: pkm-spin .8s linear infinite; }
@keyframes pkm-spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }

/* ── Responsive ── */
@media (max-width: 768px) {
  .pkm-charts-row { grid-template-columns: 1fr; }
  .pkm-kpi-bar { gap: 6px; }
  .pkm-kpi { padding: 10px 12px; min-width: 110px; }
  .pkm-kpi-val { font-size: 1.2rem; }
}
@media (max-width: 576px) {
  .pkm-page { padding: 10px; }
  .pkm-kpi-bar { display: grid; grid-template-columns: 1fr 1fr; }
  .pkm-filtros-row { flex-direction: column; align-items: stretch; }
  .pkm-btn-consultar { width: 100%; justify-content: center; }
}
</style>
