<template>
  <div class="page-container">

    <!-- ENCABEZADO -->
    <div class="page-header">
      <div>
        <div class="title-row">
          <h1 class="page-title">
            <i class="bi bi-person-check"></i> Mis Tareas
          </h1>
          <!-- TOGGLE VISTA -->
          <div class="view-toggle">
            <button class="vt-btn" :class="{ active: viewMode === 'card' }" @click="viewMode = 'card'" title="Vista tarjetas">
              <i class="bi bi-grid"></i>
            </button>
            <button class="vt-btn" :class="{ active: viewMode === 'list' }" @click="viewMode = 'list'" title="Vista lista">
              <i class="bi bi-list-ul"></i>
            </button>
          </div>
        </div>
        <p class="page-subtitle">
          {{ isWorker ? 'Tareas asignadas a ti' : 'Todas las tareas — ' + tasks.length + ' registradas' }}
        </p>
      </div>
    </div>

    <!-- MINI KPIs (todos clickeables) -->
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

    <!-- FILTROS ADICIONALES (solo para roles no-Worker) -->
    <div v-if="!isWorker" class="filter-bar">
      <select v-model="filterWorker" class="form-select form-select-sm" style="max-width:220px">
        <option :value="null">Todos los ejecutores</option>
        <option v-for="w in workers" :key="w.id" :value="w.id">{{ w.name }}</option>
      </select>
      <button
        v-if="filterWorker !== null || activeTab !== 'all'"
        class="btn btn-sm btn-outline-secondary"
        @click="filterWorker = null; activeTab = 'all'"
      >
        <i class="bi bi-x-circle"></i> Limpiar filtros
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
    <div v-if="loading" class="loading-center">
      <i class="bi bi-arrow-repeat spin"></i> Cargando tareas...
    </div>

    <!-- SIN TAREAS -->
    <div v-else-if="filtered.length === 0" class="empty-state">
      <i class="bi bi-clipboard-check"></i>
      <p>No hay tareas con estos filtros</p>
    </div>

    <!-- VISTA TARJETAS -->
    <div v-else-if="viewMode === 'card'" class="task-grid">
      <div
        v-for="task in filtered"
        :key="task.id"
        class="task-card"
        :style="{ borderLeftColor: cardBorderColor(task) }"
        @click="goToDetail(task)"
        title="Ver detalle de la tarea"
      >
        <div class="card-header">
          <span class="status-badge" :class="statusClass(task.status_id)">
            {{ task.status_name }}
          </span>
          <span v-if="isOverdue(task)" class="overdue-chip">
            <i class="bi bi-exclamation-triangle-fill"></i> Atrasada
          </span>
        </div>
        <h3 class="card-title">{{ task.title }}</h3>
        <div v-if="task.asset_id" class="card-asset">
          <i class="bi bi-building"></i> {{ assetName(task.asset_id) }}
        </div>
        <div class="card-workers" v-if="task.assigned_to_name || task.worker_name">
          <span v-if="task.assigned_to_name" class="worker-chip">
            <i class="bi bi-person-check"></i> {{ task.assigned_to_name }}
          </span>
          <span v-if="task.worker_name" class="worker-chip worker-chip-exec">
            <i class="bi bi-tools"></i> {{ task.worker_name }}
          </span>
        </div>
        <div v-if="task.budget_labor_cost > 0" class="card-budget">
          <i class="bi bi-cash"></i>
          ${{ task.budget_labor_cost.toLocaleString('es-CO') }}
        </div>
        <div class="card-actions" @click.stop>
          <button
            v-if="isWorker"
            class="btn-action-main"
            @click.stop="openUpdate(task)"
            :disabled="[5,6].includes(task.status_id)"
            :title="[5,6].includes(task.status_id) ? 'Tarea cerrada' : 'Actualizar avance'"
          >
            <i class="bi bi-pencil-square"></i> Actualizar avance
          </button>
          <button v-else class="btn-action-main" @click.stop="goToDetail(task)">
            <i class="bi bi-eye"></i> Ver / Editar
          </button>
          <button class="btn-action-sec"
            @click.stop="$router.push('/tasks/' + task.id + '/evidencias')"
            title="Evidencias">
            <i class="bi bi-camera"></i>
          </button>
          <button class="btn-action-sec"
            @click.stop="$router.push('/tasks/' + task.id + '/materiales')"
            title="Materiales y gastos">
            <i class="bi bi-tools"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- VISTA LISTA -->
    <div v-else class="task-list">
      <div class="tl-header">
        <span class="tl-col tl-estado">Estado</span>
        <span class="tl-col tl-titulo">Título</span>
        <span class="tl-col tl-activo">Activo</span>
        <span class="tl-col tl-acciones"></span>
      </div>
      <div
        v-for="task in filtered"
        :key="task.id"
        class="tl-row"
        :class="{ 'tl-overdue': isOverdue(task) }"
        :style="{ borderLeftColor: cardBorderColor(task) }"
      >
        <span class="tl-col tl-estado">
          <span class="status-badge" :class="statusClass(task.status_id)">{{ task.status_name }}</span>
        </span>
        <span class="tl-col tl-titulo">
          <TaskTooltip :task="task" :asset-name="assetName(task.asset_id)">
            <span class="tl-title-text">{{ task.title }}</span>
          </TaskTooltip>
          <span v-if="isOverdue(task)" class="overdue-chip"><i class="bi bi-exclamation-triangle-fill"></i></span>
        </span>
        <span class="tl-col tl-activo">
          <TaskTooltip :task="task" :asset-name="assetName(task.asset_id)">
            <i v-if="task.asset_id" class="bi bi-building tl-activo-icon"></i>
            {{ task.asset_id ? assetName(task.asset_id) : '—' }}
          </TaskTooltip>
        </span>
        <span class="tl-col tl-acciones" @click.stop>
          <button v-if="isWorker" class="tl-btn tl-btn-pen"
            @click="openUpdate(task)"
            :disabled="[5,6].includes(task.status_id)"
            title="Actualizar avance">
            <i class="bi bi-pencil-square"></i>
          </button>
          <button v-else class="tl-btn tl-btn-eye"
            @click="goToDetail(task)" title="Ver / Editar">
            <i class="bi bi-eye"></i>
          </button>
          <button class="tl-btn tl-btn-cam"
            @click="$router.push('/tasks/' + task.id + '/evidencias')" title="Evidencias">
            <i class="bi bi-camera"></i>
          </button>
          <button class="tl-btn tl-btn-tool"
            @click="$router.push('/tasks/' + task.id + '/materiales')" title="Materiales">
            <i class="bi bi-tools"></i>
          </button>
        </span>
      </div>
    </div>

    <!-- MODAL ACTUALIZAR AVANCE (solo Worker role) -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-box">
        <div class="modal-header-bar">
          <h2>Actualizar avance</h2>
          <button class="btn-close-x" @click="showModal = false">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>

        <div class="modal-body-area">

          <div class="task-info-block">
            <strong>{{ editing.title }}</strong>
            <span class="status-badge ms-2" :class="statusClass(editing.status_id)">
              {{ editing.status_name }}
            </span>
          </div>

          <!-- Estado -->
          <div class="fg">
            <label>Nuevo estado</label>
            <div class="status-pills">
              <button
                v-for="s in statusesActivos"
                :key="s.id"
                class="status-pill"
                :class="[statusClass(s.id), { selected: updateForm.status_id === s.id }]"
                @click="updateForm.status_id = s.id"
              >
                {{ s.name }}
              </button>
            </div>
          </div>

          <!-- Avance -->
          <div class="fg">
            <label>
              Porcentaje de avance:
              <strong class="progress-number">{{ updateForm.progress }}%</strong>
            </label>
            <input
              v-model.number="updateForm.progress"
              type="range" min="0" max="100" step="5"
              class="form-range"
            />
            <div class="range-marks">
              <span>0%</span><span>25%</span><span>50%</span><span>75%</span><span>100%</span>
            </div>
          </div>

          <div v-if="updateForm.status_id === 5" class="alert-info">
            <i class="bi bi-info-circle"></i>
            Al marcar como <strong>Finalizada</strong> se registrará la fecha de cierre automáticamente.
          </div>

        </div>

        <div class="modal-footer-bar">
          <button class="btn btn-secondary" @click="showModal = false">Cancelar</button>
          <button class="btn btn-primary" @click="saveProgress" :disabled="saving">
            <i v-if="saving" class="bi bi-arrow-repeat spin"></i>
            {{ saving ? 'Guardando...' : 'Guardar' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { useRouter } from "vue-router"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import TaskTooltip from "@/components/TaskTooltip.vue"

const router = useRouter()

// ── Detección de rol ─────────────────────────────────────────
const userInfo = JSON.parse(localStorage.getItem("user") || "{}")
const isWorker = (userInfo.role || "").toLowerCase().includes("worker")

// ── Estado ──────────────────────────────────────────────────
const tasks    = ref([])
const assets   = ref([])
const workers  = ref([])
const statuses = ref([])
const loading  = ref(true)
const saving   = ref(false)
const showModal  = ref(false)
const editing    = ref({})
const activeTab    = ref("all")
const filterWorker = ref(null)
const viewMode     = ref("card")

const updateForm = ref({ progress: 0, status_id: 1 })

// ── Contadores ───────────────────────────────────────────────
const counts = computed(() => ({
  pendiente:   tasks.value.filter(t => t.status_id === 1).length,
  progreso:    tasks.value.filter(t => t.status_id === 3).length,
  revision:    tasks.value.filter(t => t.status_id === 4).length,
  finalizada:  tasks.value.filter(t => t.status_id === 5).length,
  atrasadas:   tasks.value.filter(t => isOverdue(t)).length,
  sinEjecutor: tasks.value.filter(t => !t.worker_id && ![5,6].includes(t.status_id)).length,
}))

const tabs = computed(() => [
  { label: "Todas",          value: "all",        count: tasks.value.length },
  { label: "Pendientes",     value: "pending",    count: counts.value.pendiente },
  { label: "En Progreso",    value: "progress",   count: counts.value.progreso },
  { label: "En Revisión",    value: "revision",   count: counts.value.revision },
  { label: "Finalizadas",    value: "done",       count: counts.value.finalizada },
  { label: "⚡ Atrasadas",   value: "overdue",    count: counts.value.atrasadas },
  { label: "Sin Ejecutor",   value: "unassigned", count: counts.value.sinEjecutor },
])

// ── Filtrado combinado ───────────────────────────────────────
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

  if (!isWorker && filterWorker.value !== null) {
    list = list.filter(t => t.worker_id === filterWorker.value)
  }

  return list
})

const statusesActivos = computed(() =>
  statuses.value.filter(s => s.id !== 6)
)

// ── Helpers ──────────────────────────────────────────────────
const STATUS_COLORS = {
  1: "#f97316", 2: "#3b82f6", 3: "#22c55e",
  4: "#7c3aed", 5: "#065f46", 6: "#ef4444",
}

const STATUS_CLASSES = {
  1: "badge-orange", 2: "badge-blue",      3: "badge-green",
  4: "badge-purple", 5: "badge-darkgreen", 6: "badge-red",
}

function cardBorderColor(task) {
  if (isOverdue(task)) return "#ef4444"
  return STATUS_COLORS[task.status_id] || "#e2e8f0"
}

function statusClass(id) { return STATUS_CLASSES[id] || "badge-gray" }
function assetName(id)   { return assets.value.find(a => a.id === id)?.name || "—" }
function isOverdue(t)    {
  return t.due_date && new Date(t.due_date) < new Date() && ![5, 6].includes(t.status_id)
}
function fmtDate(iso) {
  if (!iso) return ""
  return new Date(iso).toLocaleDateString("es-CO", {
    day: "2-digit", month: "short", year: "numeric"
  })
}
function setTab(tab) { activeTab.value = tab }

// ── Carga de datos ───────────────────────────────────────────
async function load() {
  loading.value = true
  try {
    const endpoint = isWorker ? "/tasks/my-tasks" : "/tasks/"
    const promises = [
      api.get(endpoint),
      api.get("/tasks/assets-list"),
      api.get("/task-status/"),
    ]
    if (!isWorker) promises.push(api.get("/workers/"))

    const results = await Promise.all(promises)
    tasks.value    = results[0].data
    assets.value   = results[1].data
    statuses.value = results[2].data
    if (!isWorker) workers.value = results[3].data
  } catch {
    showToast("Error cargando tareas", "error")
  } finally {
    loading.value = false
  }
}

// ── Navegación ───────────────────────────────────────────────
function goToDetail(task) {
  router.push(`/tasks/${task.id}/detalle`)
}

// ── Actualizar avance (solo Worker role) ─────────────────────
function openUpdate(task) {
  editing.value    = task
  updateForm.value = { progress: task.progress, status_id: task.status_id }
  showModal.value  = true
}

async function saveProgress() {
  saving.value = true
  try {
    await api.patch(`/tasks/${editing.value.id}/progress`, updateForm.value)
    showToast("Avance actualizado", "success")
    showModal.value = false
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error guardando", "error")
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1200px; }
.page-header    { margin-bottom: 20px; }
.title-row      { display:flex; align-items:center; gap:12px; }
.page-title     { font-size: 20px; font-weight: 700; color: #1e293b; display:flex; align-items:center; gap:8px; margin:0; }
.page-subtitle  { font-size: 13px; color: #64748b; margin-top: 4px; }

/* TOGGLE VISTA */
.view-toggle { display:flex; border:1px solid #e2e8f0; border-radius:8px; overflow:hidden; }
.vt-btn { padding:5px 10px; background:#f8fafc; border:none; cursor:pointer; color:#64748b; font-size:15px; transition:all 0.15s; }
.vt-btn:hover  { background:#e2e8f0; }
.vt-btn.active { background:#3b82f6; color:#fff; }

/* MINI KPIS */
.mini-kpis { display:flex; gap:12px; margin-bottom:20px; flex-wrap:wrap; }
.mini-kpi {
  flex: 1; min-width: 100px; cursor: pointer;
  background: #fff; border-radius: 12px; padding: 12px 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.07);
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  border-top: 3px solid #e2e8f0;
  transition: box-shadow 0.15s, transform 0.15s;
}
.mini-kpi:hover  { box-shadow: 0 3px 10px rgba(0,0,0,0.12); transform: translateY(-1px); }
.kpi-active      { box-shadow: 0 3px 10px rgba(0,0,0,0.15); transform: translateY(-2px); }
.mk-value    { font-size: 22px; font-weight: 800; color: #1e293b; }
.mk-label    { font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.4px; }
.mk-progreso  { border-top-color: #22c55e; }
.mk-revision  { border-top-color: #7c3aed; }
.mk-finalizada{ border-top-color: #065f46; }
.mk-atrasada  { border-top-color: #ef4444; }
.mk-atrasada .mk-value { color: #ef4444; }
.mk-atrasada.kpi-active { background: #fef2f2; }
.mk-sinasig   { border-top-color: #94a3b8; }
.mk-sinasig .mk-value { color: #64748b; }

/* FILTER BAR */
.filter-bar { display:flex; gap:10px; align-items:center; margin-bottom:14px; flex-wrap:wrap; }

/* FILTER TABS */
.filter-tabs { display:flex; gap:8px; margin-bottom:20px; flex-wrap:wrap; }
.filter-tab  {
  padding: 6px 14px; border-radius: 20px;
  border: 1px solid #e2e8f0; background: #f8fafc;
  font-size: 13px; font-weight: 500; cursor: pointer;
  display: flex; align-items: center; gap: 6px;
  transition: all 0.15s;
}
.filter-tab:hover  { border-color: #3b82f6; background: #eff6ff; }
.filter-tab.active { background: #3b82f6; border-color: #3b82f6; color: #fff; }
.filter-tab.active .tab-count { background: rgba(255,255,255,0.25); }
.filter-overdue.active { background: #ef4444; border-color: #ef4444; }
.tab-count { font-size: 11px; background: #e2e8f0; color: #475569; border-radius: 10px; padding: 1px 7px; }

/* STATES */
.loading-center { padding: 60px; text-align: center; color: #94a3b8; font-size: 15px; }
.empty-state    { padding: 60px; text-align: center; color: #94a3b8; }
.empty-state .bi { font-size: 42px; display: block; margin-bottom: 12px; }

/* GRID DE TARJETAS */
.task-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }

.task-card {
  background: #fff; border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  padding: 14px 16px; display: flex; flex-direction: column; gap: 8px;
  border-left: 4px solid #e2e8f0;
  transition: box-shadow 0.2s, transform 0.15s;
  cursor: pointer;
}
.task-card:hover { box-shadow: 0 4px 14px rgba(0,0,0,0.13); transform: translateY(-2px); }

.card-header { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.overdue-chip { font-size: 11px; color: #ef4444; font-weight: 700; display:flex; align-items:center; gap:3px; }

.card-title  { font-size: 14px; font-weight: 700; color: #1e293b; margin: 0; line-height: 1.3; }
.card-asset  { font-size: 12px; color: #475569; display:flex; align-items:center; gap:4px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.card-budget { font-size: 12px; color: #16a34a; font-weight: 600;
  display:flex; align-items:center; gap:4px; }

/* WORKER INFO */
.card-workers { display: flex; flex-wrap: wrap; gap: 6px; }
.worker-chip  {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 12px; font-weight: 500; color: #1e40af;
  background: #dbeafe; border-radius: 20px; padding: 2px 10px;
}
.worker-chip-exec { color: #065f46; background: #d1fae5; }


/* ACCIONES */
.card-actions { display: flex; gap: 8px; margin-top: 4px; }
.btn-action-main {
  flex: 1; padding: 8px; border-radius: 8px;
  background: #3b82f6; color: #fff; border: none; font-size: 13px;
  font-weight: 600; cursor: pointer; display: flex; align-items: center;
  justify-content: center; gap: 6px; transition: background 0.2s;
}
.btn-action-main:hover:not(:disabled) { background: #2563eb; }
.btn-action-main:disabled { opacity: 0.45; cursor: not-allowed; }

.btn-action-sec {
  padding: 8px 12px; border-radius: 8px;
  background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0;
  font-size: 14px; cursor: pointer;
  display: flex; align-items: center; gap: 6px;
  transition: background 0.15s;
}
.btn-action-sec:hover { background: #e2e8f0; }

/* STATUS BADGES */
.status-badge    { font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 20px; white-space: nowrap; }
.badge-orange    { background: #fff7ed; color: #c2410c; }
.badge-blue      { background: #dbeafe; color: #1e40af; }
.badge-green     { background: #dcfce7; color: #16a34a; }
.badge-purple    { background: #f3e8ff; color: #7c3aed; }
.badge-darkgreen { background: #d1fae5; color: #065f46; }
.badge-red       { background: #fef2f2; color: #b91c1c; }
.badge-gray      { background: #f1f5f9; color: #64748b; }

/* MODAL */
.modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.45); display:flex; align-items:center; justify-content:center; z-index:1000; }
.modal-box     { background:#fff; border-radius:16px; width:500px; max-width:95vw; box-shadow:0 20px 60px rgba(0,0,0,0.2); }
.modal-header-bar  { display:flex; align-items:center; justify-content:space-between; padding:18px 24px 14px; border-bottom:1px solid #f1f5f9; }
.modal-header-bar h2 { font-size:16px; font-weight:700; color:#1e293b; margin:0; }
.modal-body-area   { padding:20px 24px; display:flex; flex-direction:column; gap:16px; }
.modal-footer-bar  { padding:14px 24px 18px; display:flex; justify-content:flex-end; gap:10px; border-top:1px solid #f1f5f9; }

.task-info-block { padding:12px 14px; background:#f8fafc; border-radius:10px; font-size:14px; color:#1e293b; display:flex; align-items:center; flex-wrap:wrap; gap:8px; }
.fg { display:flex; flex-direction:column; gap:6px; }
.fg label { font-size:13px; font-weight:600; color:#374151; }

.status-pills { display:flex; flex-wrap:wrap; gap:8px; }
.status-pill  {
  padding: 6px 14px; border-radius: 20px; font-size: 12px;
  font-weight: 600; cursor: pointer; border: 2px solid transparent;
  transition: all 0.15s; opacity: 0.65;
}
.status-pill.selected { opacity: 1; border-color: currentColor; transform: scale(1.05); }

.progress-number { color: #3b82f6; font-size: 16px; margin-left: 6px; }
.range-marks { display:flex; justify-content:space-between; font-size:10px; color:#94a3b8; margin-top:-2px; }
.alert-info { background:#eff6ff; border:1px solid #bfdbfe; border-radius:8px; padding:10px 14px; font-size:13px; color:#1e40af; display:flex; align-items:center; gap:8px; }

.btn-close-x { background:none; border:none; font-size:18px; cursor:pointer; color:#94a3b8; }
.btn-close-x:hover { color:#1e293b; }
.spin { display:inline-block; animation:spin 0.8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

/* VISTA LISTA */
.task-list { display:flex; flex-direction:column; border:1px solid #e2e8f0; border-radius:12px; overflow:hidden; }
.tl-header {
  display:grid; grid-template-columns:115px 1fr 1fr 96px;
  gap:8px; padding:6px 12px; background:#f1f5f9;
  font-size:10px; font-weight:700; text-transform:uppercase;
  letter-spacing:0.5px; color:#94a3b8;
}
.tl-row {
  display:grid; grid-template-columns:115px 1fr 1fr 96px;
  gap:8px; padding:6px 12px; border-top:1px solid #f1f5f9;
  border-left:3px solid transparent; background:#fff;
  align-items:center; transition:background 0.12s;
}
.tl-row:hover { background:#f8fafc; }
.tl-overdue   { background:#fef2f2; }
.tl-overdue:hover { background:#fee2e2; }
.tl-col { font-size:12px; color:#374151; display:flex; align-items:center; gap:4px; min-width:0; }
.tl-titulo {
  gap:5px; background:#eff6ff; border-radius:5px; padding:2px 7px;
}
.tl-title-text { font-size:13px; font-weight:700; color:#1e293b; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.tl-activo {
  font-size:12px; color:#475569; font-weight:500;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
  background:#f0fdf4; border-radius:5px; padding:2px 7px;
}
.tl-activo-icon { color:#94a3b8; flex-shrink:0; }
.tl-acciones { gap:4px; justify-content:flex-end; }
.tl-btn {
  width:28px; height:28px; border:none; border-radius:6px;
  display:flex; align-items:center; justify-content:center;
  font-size:13px; cursor:pointer; transition:opacity 0.15s; flex-shrink:0;
}
.tl-btn:hover    { opacity:0.82; }
.tl-btn:disabled { opacity:0.35; cursor:not-allowed; }
.tl-btn-eye  { background:#dbeafe; color:#1d4ed8; }
.tl-btn-cam  { background:#d1fae5; color:#065f46; }
.tl-btn-pen  { background:#dbeafe; color:#1d4ed8; }
.tl-btn-tool { background:#ffedd5; color:#c2410c; }

@media (max-width: 640px) {
  .task-grid { grid-template-columns: 1fr; }
  .mini-kpis { gap: 8px; }
  .mini-kpi  { min-width: 70px; }
  .tl-header { display:none; }
  .tl-row    { grid-template-columns:1fr; gap:4px; }
}
</style>
