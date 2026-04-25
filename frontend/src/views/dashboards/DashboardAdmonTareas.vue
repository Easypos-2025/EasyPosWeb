<template>
  <div>
    <!-- KPI STRIP: porcentajes de salud del proyecto -->
    <KpiStrip :kpis="kpis" :loading="loadingStats" :show-labels="true" />

    <!-- MINI KPIs (conteos, todos clickeables) -->
    <div class="mini-kpis">
      <div class="mini-kpi" :class="{ 'kpi-active': activeTab === 'pending' }"
        @click="setTab('pending')">
        <span class="mk-value">{{ counts.pendiente }}</span>
        <span class="mk-label">Pendientes</span>
      </div>
      <div class="mini-kpi mk-progreso" :class="{ 'kpi-active': activeTab === 'progress' }"
        @click="setTab('progress')">
        <span class="mk-value">{{ counts.progreso }}</span>
        <span class="mk-label">En Progreso</span>
      </div>
      <div class="mini-kpi mk-revision" :class="{ 'kpi-active': activeTab === 'revision' }"
        @click="setTab('revision')">
        <span class="mk-value">{{ counts.revision }}</span>
        <span class="mk-label">En Revisión</span>
      </div>
      <div class="mini-kpi mk-finalizada" :class="{ 'kpi-active': activeTab === 'done' }"
        @click="setTab('done')">
        <span class="mk-value">{{ counts.finalizada }}</span>
        <span class="mk-label">Finalizadas</span>
      </div>
      <div class="mini-kpi mk-atrasada" :class="{ 'kpi-active': activeTab === 'overdue' }"
        @click="setTab('overdue')">
        <span class="mk-value">{{ counts.atrasadas }}</span>
        <span class="mk-label">⚡ Atrasadas</span>
      </div>
      <div class="mini-kpi mk-sinasig" :class="{ 'kpi-active': activeTab === 'unassigned' }"
        @click="setTab('unassigned')">
        <span class="mk-value">{{ counts.sinEjecutor }}</span>
        <span class="mk-label">Sin Ejecutor</span>
      </div>
    </div>

    <!-- FILTROS -->
    <div class="filter-bar">
      <select v-model="filterWorker" class="form-select form-select-sm" style="max-width:220px">
        <option :value="null">Todos los ejecutores</option>
        <option v-for="w in workers" :key="w.id" :value="w.id">{{ w.name }}</option>
      </select>
      <button
        v-if="filterWorker !== null || activeTab !== 'all'"
        class="btn btn-sm btn-outline-secondary"
        @click="filterWorker = null; activeTab = 'all'"
      >
        <i class="bi bi-x-circle"></i> Limpiar
      </button>
    </div>

    <!-- FILTER TABS -->
    <div class="filter-tabs">
      <button
        v-for="tab in tabs" :key="tab.value"
        class="filter-tab"
        :class="{ active: activeTab === tab.value }"
        @click="activeTab = tab.value"
      >
        {{ tab.label }}
        <span class="tab-count">{{ tab.count }}</span>
      </button>
    </div>

    <!-- LOADING -->
    <div v-if="loadingTasks" class="loading-center">
      <i class="bi bi-arrow-repeat spin"></i> Cargando tareas...
    </div>

    <!-- SIN TAREAS -->
    <div v-else-if="filtered.length === 0" class="empty-state">
      <i class="bi bi-clipboard-check"></i>
      <p>No hay tareas con estos filtros</p>
    </div>

    <!-- GRID DE TARJETAS -->
    <div v-else class="task-grid">
      <div
        v-for="task in filtered"
        :key="task.id"
        class="task-card"
        :style="{ borderLeftColor: cardBorderColor(task) }"
        @click="$router.push('/tasks/' + task.id + '/detalle')"
        title="Ver detalle"
      >
        <!-- CABECERA -->
        <div class="card-header">
          <span class="status-badge" :class="statusClass(task.status_id)">
            {{ task.status_name }}
          </span>
          <span v-if="isOverdue(task)" class="overdue-chip">
            <i class="bi bi-exclamation-triangle-fill"></i>
          </span>
        </div>

        <!-- TÍTULO -->
        <h3 class="card-title">{{ task.title }}</h3>

        <!-- ACTIVO -->
        <div v-if="task.asset_id" class="card-asset">
          <i class="bi bi-building"></i> {{ assetName(task.asset_id) }}
        </div>

        <!-- RESPONSABLE / EJECUTOR -->
        <div class="card-workers" v-if="task.assigned_to_name || task.worker_name">
          <span v-if="task.assigned_to_name" class="worker-chip">
            <i class="bi bi-person-check"></i> {{ task.assigned_to_name }}
          </span>
          <span v-if="task.worker_name" class="worker-chip worker-chip-exec">
            <i class="bi bi-tools"></i> {{ task.worker_name }}
          </span>
        </div>

        <!-- PRESUPUESTO -->
        <div v-if="task.budget_labor_cost > 0" class="card-budget">
          <i class="bi bi-cash"></i>
          ${{ task.budget_labor_cost.toLocaleString('es-CO') }}
        </div>

        <!-- ACCIONES -->
        <div class="card-actions" @click.stop>
          <button class="btn-action-main"
            @click.stop="$router.push('/tasks/' + task.id + '/detalle')">
            <i class="bi bi-eye"></i> Ver / Editar
          </button>
          <button class="btn-action-sec"
            @click.stop="$router.push('/tasks/' + task.id + '/evidencias')"
            title="Evidencias">
            <i class="bi bi-camera"></i>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { useRouter } from "vue-router"
import KpiStrip from "@/components/dashboard/KpiStrip.vue"
import api from "@/services/apis"

const router = useRouter()

// ── Estado ──────────────────────────────────────────────────
const stats       = ref({ total:0, pendiente:0, progreso:0, revision:0,
                           finalizada:0, cancelada:0, atrasadas:0, sin_ejecutor:0 })
const tasks       = ref([])
const assets      = ref([])
const workers     = ref([])
const loadingStats = ref(true)
const loadingTasks = ref(true)
const activeTab    = ref("all")
const filterWorker = ref(null)

// ── KPI Strip — porcentajes ──────────────────────────────────
const pct = (n) => {
  const t = stats.value.total
  if (!t) return "—"
  return Math.round((n / t) * 100) + "%"
}

const kpis = computed(() => [
  { icon: "bi-hourglass-split",        label: "% Pendientes",   value: pct(stats.value.pendiente) },
  { icon: "bi-play-circle-fill",       label: "% En Ejecución", value: pct(stats.value.progreso + stats.value.revision) },
  { icon: "bi-exclamation-triangle-fill", label: "% Atrasadas", value: pct(stats.value.atrasadas) },
  { icon: "bi-check2-circle",          label: "% Completadas",  value: pct(stats.value.finalizada) },
  { icon: "bi-person-dash",            label: "% Sin Ejecutor", value: pct(stats.value.sin_ejecutor) },
])

// ── Contadores para mini-KPIs ────────────────────────────────
const counts = computed(() => ({
  pendiente:   tasks.value.filter(t => t.status_id === 1).length,
  progreso:    tasks.value.filter(t => t.status_id === 3).length,
  revision:    tasks.value.filter(t => t.status_id === 4).length,
  finalizada:  tasks.value.filter(t => t.status_id === 5).length,
  atrasadas:   tasks.value.filter(t => isOverdue(t)).length,
  sinEjecutor: tasks.value.filter(t => !t.worker_id && ![5,6].includes(t.status_id)).length,
}))

const tabs = computed(() => [
  { label: "Todas",        value: "all",        count: tasks.value.length },
  { label: "Pendientes",   value: "pending",    count: counts.value.pendiente },
  { label: "En Progreso",  value: "progress",   count: counts.value.progreso },
  { label: "En Revisión",  value: "revision",   count: counts.value.revision },
  { label: "Finalizadas",  value: "done",       count: counts.value.finalizada },
  { label: "⚡ Atrasadas", value: "overdue",    count: counts.value.atrasadas },
  { label: "Sin Ejecutor", value: "unassigned", count: counts.value.sinEjecutor },
])

// ── Filtrado ─────────────────────────────────────────────────
const filtered = computed(() => {
  let list = tasks.value

  if (activeTab.value === "overdue") {
    list = list.filter(t => isOverdue(t))
  } else if (activeTab.value === "unassigned") {
    list = list.filter(t => !t.worker_id && ![5,6].includes(t.status_id))
  } else {
    const tabMap = { all: null, pending: 1, progress: 3, revision: 4, done: 5 }
    const sid = tabMap[activeTab.value]
    if (sid !== null && sid !== undefined) list = list.filter(t => t.status_id === sid)
  }

  if (filterWorker.value !== null) {
    list = list.filter(t => t.worker_id === filterWorker.value)
  }

  return list
})

// ── Helpers ──────────────────────────────────────────────────
const STATUS_COLORS = { 1:"#f97316",2:"#3b82f6",3:"#22c55e",4:"#7c3aed",5:"#065f46",6:"#ef4444" }
const STATUS_CLASSES = { 1:"badge-orange",2:"badge-blue",3:"badge-green",4:"badge-purple",5:"badge-darkgreen",6:"badge-red" }

function cardBorderColor(t) { return isOverdue(t) ? "#ef4444" : STATUS_COLORS[t.status_id] || "#e2e8f0" }
function statusClass(id)    { return STATUS_CLASSES[id] || "badge-gray" }
function assetName(id)      { return assets.value.find(a => a.id === id)?.name || "—" }
function isOverdue(t)       { return t.due_date && new Date(t.due_date) < new Date() && ![5,6].includes(t.status_id) }
function setTab(tab)        { activeTab.value = tab }

// ── Carga ────────────────────────────────────────────────────
onMounted(async () => {
  try {
    const statsRes = await api.get("/tasks/stats")
    stats.value = statsRes.data
  } catch {}
  loadingStats.value = false

  try {
    const [tasksRes, assetsRes, workersRes] = await Promise.all([
      api.get("/tasks/"),
      api.get("/tasks/assets-list"),
      api.get("/workers/"),
    ])
    tasks.value   = tasksRes.data
    assets.value  = assetsRes.data
    workers.value = workersRes.data
  } catch {}
  loadingTasks.value = false
})
</script>

<style scoped>
/* MINI KPIs */
.mini-kpis { display:flex; gap:10px; margin-bottom:16px; flex-wrap:wrap; }
.mini-kpi {
  flex:1; min-width:90px; cursor:pointer;
  background:#fff; border-radius:12px; padding:10px 14px;
  box-shadow:0 1px 4px rgba(0,0,0,0.07);
  display:flex; flex-direction:column; align-items:center; gap:3px;
  border-top:3px solid #e2e8f0;
  transition:box-shadow 0.15s, transform 0.15s;
}
.mini-kpi:hover  { box-shadow:0 3px 10px rgba(0,0,0,0.12); transform:translateY(-1px); }
.kpi-active      { box-shadow:0 3px 10px rgba(0,0,0,0.15); transform:translateY(-2px); }
.mk-value  { font-size:20px; font-weight:800; color:#1e293b; }
.mk-label  { font-size:10px; color:#94a3b8; text-transform:uppercase; letter-spacing:0.4px; }
.mk-progreso   { border-top-color:#22c55e; }
.mk-revision   { border-top-color:#7c3aed; }
.mk-finalizada { border-top-color:#065f46; }
.mk-atrasada   { border-top-color:#ef4444; }
.mk-atrasada .mk-value { color:#ef4444; }
.mk-sinasig    { border-top-color:#94a3b8; }
.mk-sinasig .mk-value  { color:#64748b; }

/* FILTER BAR */
.filter-bar { display:flex; gap:10px; align-items:center; margin-bottom:12px; flex-wrap:wrap; }

/* FILTER TABS */
.filter-tabs { display:flex; gap:6px; margin-bottom:16px; flex-wrap:wrap; }
.filter-tab {
  padding:5px 12px; border-radius:20px;
  border:1px solid #e2e8f0; background:#f8fafc;
  font-size:12px; font-weight:500; cursor:pointer;
  display:flex; align-items:center; gap:5px; transition:all 0.15s;
}
.filter-tab:hover  { border-color:#3b82f6; background:#eff6ff; }
.filter-tab.active { background:#3b82f6; border-color:#3b82f6; color:#fff; }
.filter-tab.active .tab-count { background:rgba(255,255,255,0.25); }
.tab-count { font-size:10px; background:#e2e8f0; color:#475569; border-radius:10px; padding:1px 6px; }

/* STATES */
.loading-center { padding:40px; text-align:center; color:#94a3b8; }
.empty-state    { padding:40px; text-align:center; color:#94a3b8; }
.empty-state .bi { font-size:36px; display:block; margin-bottom:8px; }

/* GRID */
.task-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(200px, 1fr)); gap:12px; }

.task-card {
  background:#fff; border-radius:12px;
  box-shadow:0 1px 4px rgba(0,0,0,0.08);
  padding:14px 16px; display:flex; flex-direction:column; gap:8px;
  border-left:4px solid #e2e8f0; cursor:pointer;
  transition:box-shadow 0.2s, transform 0.15s;
}
.task-card:hover { box-shadow:0 4px 14px rgba(0,0,0,0.12); transform:translateY(-2px); }

.card-header { display:flex; align-items:center; gap:6px; flex-wrap:wrap; }
.overdue-chip { font-size:11px; color:#ef4444; }
.card-title  { font-size:14px; font-weight:700; color:#1e293b; margin:0; line-height:1.3; }
.card-asset  { font-size:12px; color:#475569; display:flex; align-items:center; gap:4px;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.card-budget { font-size:12px; color:#16a34a; font-weight:600;
  display:flex; align-items:center; gap:4px; }

/* WORKERS */
.card-workers { display:flex; flex-wrap:wrap; gap:5px; }
.worker-chip  { display:inline-flex; align-items:center; gap:4px; font-size:11px;
  font-weight:500; color:#1e40af; background:#dbeafe; border-radius:20px; padding:2px 8px; }
.worker-chip-exec { color:#065f46; background:#d1fae5; }

/* ACCIONES */
.card-actions { display:flex; gap:6px; margin-top:2px; }
.btn-action-main {
  flex:1; padding:6px; border-radius:7px;
  background:#3b82f6; color:#fff; border:none; font-size:12px;
  font-weight:600; cursor:pointer; display:flex; align-items:center;
  justify-content:center; gap:5px; transition:background 0.2s;
}
.btn-action-main:hover { background:#2563eb; }
.btn-action-sec {
  padding:6px 10px; border-radius:7px;
  background:#f1f5f9; color:#475569; border:1px solid #e2e8f0;
  font-size:13px; cursor:pointer; transition:background 0.15s;
}
.btn-action-sec:hover { background:#e2e8f0; }

/* STATUS BADGES */
.status-badge    { font-size:11px; font-weight:700; padding:2px 9px; border-radius:20px; white-space:nowrap; }
.badge-orange    { background:#fff7ed; color:#c2410c; }
.badge-blue      { background:#dbeafe; color:#1e40af; }
.badge-green     { background:#dcfce7; color:#16a34a; }
.badge-purple    { background:#f3e8ff; color:#7c3aed; }
.badge-darkgreen { background:#d1fae5; color:#065f46; }
.badge-red       { background:#fef2f2; color:#b91c1c; }
.badge-gray      { background:#f1f5f9; color:#64748b; }

.spin { display:inline-block; animation:spin 0.8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

@media (max-width:640px) {
  .task-grid { grid-template-columns:1fr 1fr; }
  .mini-kpis { gap:6px; }
  .mini-kpi  { min-width:60px; }
}
</style>
