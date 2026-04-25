<template>
  <div class="page-container">

    <!-- ENCABEZADO -->
    <div class="page-header">
      <div>
        <h1 class="page-title">
          <i class="bi bi-person-check"></i> Mis Tareas
        </h1>
        <p class="page-subtitle">Tareas asignadas a ti — actualiza el avance y el estado</p>
      </div>
    </div>

    <!-- MINI KPIs -->
    <div class="mini-kpis">
      <div class="mini-kpi">
        <span class="mk-value">{{ counts.pendiente }}</span>
        <span class="mk-label">Pendientes</span>
      </div>
      <div class="mini-kpi mk-progreso">
        <span class="mk-value">{{ counts.progreso }}</span>
        <span class="mk-label">En Progreso</span>
      </div>
      <div class="mini-kpi mk-revision">
        <span class="mk-value">{{ counts.revision }}</span>
        <span class="mk-label">En Revisión</span>
      </div>
      <div class="mini-kpi mk-finalizada">
        <span class="mk-value">{{ counts.finalizada }}</span>
        <span class="mk-label">Finalizadas</span>
      </div>
      <div class="mini-kpi mk-atrasada">
        <span class="mk-value">{{ counts.atrasadas }}</span>
        <span class="mk-label">Atrasadas</span>
      </div>
    </div>

    <!-- FILTRO RÁPIDO -->
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
      <i class="bi bi-arrow-repeat spin"></i> Cargando tus tareas...
    </div>

    <!-- SIN TAREAS -->
    <div v-else-if="filtered.length === 0" class="empty-state">
      <i class="bi bi-clipboard-check"></i>
      <p>No tienes tareas en este estado</p>
    </div>

    <!-- TARJETAS DE TAREAS -->
    <div v-else class="task-grid">
      <div
        v-for="task in filtered"
        :key="task.id"
        class="task-card"
        :class="{ 'card-overdue': isOverdue(task) }"
      >
        <!-- CABECERA DE LA TARJETA -->
        <div class="card-header">
          <span class="status-badge" :class="statusClass(task.status_id)">
            {{ task.status_name }}
          </span>
          <span v-if="isOverdue(task)" class="overdue-chip">
            <i class="bi bi-exclamation-triangle-fill"></i> Atrasada
          </span>
        </div>

        <!-- TÍTULO Y DESCRIPCIÓN -->
        <h3 class="card-title">{{ task.title }}</h3>
        <p v-if="task.description" class="card-desc">{{ task.description }}</p>

        <!-- INFO SECUNDARIA -->
        <div class="card-meta">
          <span v-if="task.asset_id">
            <i class="bi bi-building"></i> {{ assetName(task.asset_id) }}
          </span>
          <span v-if="task.due_date" :class="isOverdue(task) ? 'meta-danger' : ''">
            <i class="bi bi-calendar3"></i> {{ fmtDate(task.due_date) }}
          </span>
          <span v-if="task.budget_labor_cost > 0">
            <i class="bi bi-cash"></i> ${{ task.budget_labor_cost.toLocaleString('es-CO') }}
          </span>
        </div>

        <!-- BARRA DE AVANCE -->
        <div class="progress-section">
          <div class="progress-header">
            <span>Avance</span>
            <strong>{{ task.progress }}%</strong>
          </div>
          <div class="progress-track">
            <div
              class="progress-fill"
              :class="task.progress === 100 ? 'fill-green' : 'fill-blue'"
              :style="{ width: task.progress + '%' }"
            ></div>
          </div>
        </div>

        <!-- ACCIONES -->
        <div class="card-actions">
          <button
            class="btn-action-main"
            @click="openUpdate(task)"
            :disabled="[5,6].includes(task.status_id)"
            :title="[5,6].includes(task.status_id) ? 'Tarea cerrada' : 'Actualizar avance'"
          >
            <i class="bi bi-pencil-square"></i>
            Actualizar avance
          </button>

          <!-- Evidencias -->
          <button
            class="btn-action-sec"
            @click="$router.push(`/tasks/${task.id}/evidencias`)"
            title="Ver y agregar evidencias"
          >
            <i class="bi bi-camera"></i>
            Evidencias
          </button>

          <!-- Materiales y Gastos -->
          <button class="btn-action-sec"
            @click="$router.push(`/tasks/${task.id}/materiales`)"
            title="Materiales y gastos">
            <i class="bi bi-tools"></i> Materiales
          </button>

          <!-- Reportes de avance -->
          <button class="btn-action-sec"
            @click="$router.push(`/tasks/${task.id}/reportes`)"
            title="Reportes de avance">
            <i class="bi bi-bar-chart-steps"></i> Reportes
          </button>
        </div>

      </div>
    </div>

    <!-- MODAL ACTUALIZAR AVANCE -->
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
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

const tasks   = ref([])
const assets  = ref([])
const statuses = ref([])
const loading  = ref(true)
const saving   = ref(false)
const showModal = ref(false)
const editing   = ref({})
const activeTab = ref("all")

const updateForm = ref({ progress: 0, status_id: 1 })

// ── Contadores ───────────────────────────────────────────────────
const counts = computed(() => ({
  pendiente:  tasks.value.filter(t => t.status_id === 1).length,
  progreso:   tasks.value.filter(t => t.status_id === 3).length,
  revision:   tasks.value.filter(t => t.status_id === 4).length,
  finalizada: tasks.value.filter(t => t.status_id === 5).length,
  atrasadas:  tasks.value.filter(t => isOverdue(t)).length,
}))

const tabs = computed(() => [
  { label: "Todas",        value: "all",       count: tasks.value.length },
  { label: "Pendientes",   value: "pending",   count: counts.value.pendiente },
  { label: "En Progreso",  value: "progress",  count: counts.value.progreso },
  { label: "En Revisión",  value: "revision",  count: counts.value.revision },
  { label: "Finalizadas",  value: "done",      count: counts.value.finalizada },
])

const filtered = computed(() => {
  const map = { all: null, pending: 1, progress: 3, revision: 4, done: 5 }
  const sid = map[activeTab.value]
  return sid === null
    ? tasks.value
    : tasks.value.filter(t => t.status_id === sid)
})

const statusesActivos = computed(() =>
  statuses.value.filter(s => s.id !== 6)  // excluir Cancelada (solo admin puede cancelar)
)

// ── Helpers ──────────────────────────────────────────────────────
const STATUS_CLASSES = {
  1: "badge-orange", 2: "badge-blue", 3: "badge-green",
  4: "badge-purple", 5: "badge-darkgreen", 6: "badge-red",
}
function statusClass(id) { return STATUS_CLASSES[id] || "badge-gray" }
function assetName(id)   { return assets.value.find(a => a.id === id)?.name || "—" }
function isOverdue(t)    { return t.due_date && new Date(t.due_date) < new Date() && ![5,6].includes(t.status_id) }
function fmtDate(iso) {
  if (!iso) return ""
  return new Date(iso).toLocaleDateString("es-CO", { day:"2-digit", month:"short", year:"numeric" })
}

// ── Datos ────────────────────────────────────────────────────────
async function load() {
  loading.value = true
  try {
    const [myRes, assetsRes, statusRes] = await Promise.all([
      api.get("/tasks/my-tasks"),
      api.get("/tasks/assets-list"),
      api.get("/task-status/"),
    ])
    tasks.value   = myRes.data
    assets.value  = assetsRes.data
    statuses.value = statusRes.data
  } catch {
    showToast("Error cargando tareas", "error")
  } finally {
    loading.value = false
  }
}

// ── Actualizar avance ────────────────────────────────────────────
function openUpdate(task) {
  editing.value = task
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
.page-title     { font-size: 20px; font-weight: 700; color: #1e293b; display:flex; align-items:center; gap:8px; }
.page-subtitle  { font-size: 13px; color: #64748b; margin-top: 4px; }

/* MINI KPIS */
.mini-kpis { display:flex; gap:12px; margin-bottom:20px; flex-wrap:wrap; }
.mini-kpi {
  flex: 1; min-width: 100px;
  background: #fff; border-radius: 12px; padding: 12px 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.07);
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  border-top: 3px solid #e2e8f0;
}
.mk-value    { font-size: 22px; font-weight: 800; color: #1e293b; }
.mk-label    { font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.4px; }
.mk-progreso  { border-top-color: #22c55e; }
.mk-revision  { border-top-color: #7c3aed; }
.mk-finalizada{ border-top-color: #065f46; }
.mk-atrasada  { border-top-color: #ef4444; }
.mk-atrasada .mk-value { color: #ef4444; }

/* FILTER TABS */
.filter-tabs { display:flex; gap:8px; margin-bottom:20px; flex-wrap:wrap; }
.filter-tab  {
  padding: 6px 14px; border-radius: 20px;
  border: 1px solid #e2e8f0; background: #f8fafc;
  font-size: 13px; font-weight: 500; cursor: pointer;
  display: flex; align-items: center; gap: 6px;
  transition: all 0.15s;
}
.filter-tab:hover { border-color: #3b82f6; background: #eff6ff; }
.filter-tab.active { background: #3b82f6; border-color: #3b82f6; color: #fff; }
.filter-tab.active .tab-count { background: rgba(255,255,255,0.25); }
.tab-count { font-size: 11px; background: #e2e8f0; color: #475569; border-radius: 10px; padding: 1px 7px; }

/* STATES */
.loading-center { padding: 60px; text-align: center; color: #94a3b8; font-size: 15px; }
.empty-state    { padding: 60px; text-align: center; color: #94a3b8; }
.empty-state .bi { font-size: 42px; display: block; margin-bottom: 12px; }

/* GRID DE TARJETAS */
.task-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }

.task-card {
  background: #fff; border-radius: 14px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.08);
  padding: 18px; display: flex; flex-direction: column; gap: 10px;
  border-left: 4px solid #e2e8f0;
  transition: box-shadow 0.2s;
}
.task-card:hover { box-shadow: 0 4px 14px rgba(0,0,0,0.12); }
.card-overdue   { border-left-color: #ef4444; }

.card-header { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.overdue-chip { font-size: 11px; color: #ef4444; font-weight: 700; display:flex; align-items:center; gap:3px; }

.card-title { font-size: 15px; font-weight: 700; color: #1e293b; margin: 0; line-height: 1.3; }
.card-desc  { font-size: 13px; color: #64748b; margin: 0; line-height: 1.4;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

.card-meta  { display: flex; flex-wrap: wrap; gap: 10px; font-size: 12px; color: #94a3b8; }
.card-meta span { display: flex; align-items: center; gap: 4px; }
.meta-danger { color: #ef4444 !important; }

/* PROGRESS */
.progress-section { display: flex; flex-direction: column; gap: 5px; }
.progress-header  { display: flex; justify-content: space-between; font-size: 12px; color: #64748b; }
.progress-track   { height: 7px; background: #f1f5f9; border-radius: 4px; overflow: hidden; }
.progress-fill    { height: 100%; border-radius: 4px; transition: width 0.4s; }
.fill-blue  { background: #3b82f6; }
.fill-green { background: #22c55e; }

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
  font-size: 13px; cursor: pointer;
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

/* RESPONSIVE */
@media (max-width: 640px) {
  .task-grid { grid-template-columns: 1fr; }
  .mini-kpis { gap: 8px; }
  .mini-kpi  { min-width: 70px; }
}
</style>
