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
            <i class="bi bi-bar-chart-steps"></i> Reportes de Avance
          </h1>
          <p class="page-subtitle" v-if="task">
            {{ task.title }}
            <span class="status-badge ms-2" :class="statusClass(task.status_id)">
              {{ task.status_name }}
            </span>
          </p>
        </div>
      </div>
    </div>

    <!-- BARRA DE PROGRESO ACTUAL -->
    <div class="progress-card" v-if="task">
      <div class="progress-info">
        <span class="prog-label">Avance actual de la tarea</span>
        <span class="prog-value">{{ task.progress }}%</span>
      </div>
      <div class="prog-track">
        <div class="prog-fill"
          :class="task.progress === 100 ? 'fill-green' : 'fill-blue'"
          :style="{ width: task.progress + '%' }">
        </div>
      </div>
      <div class="prog-footer">
        <span v-if="task.start_date">Inicio: {{ fmtDate(task.start_date) }}</span>
        <span v-if="task.due_date" :class="isOverdue ? 'text-danger' : ''">
          <i v-if="isOverdue" class="bi bi-exclamation-triangle-fill"></i>
          Límite: {{ fmtDate(task.due_date) }}
        </span>
        <span v-if="task.budget_labor_cost > 0">
          Presupuesto: ${{ fmt(task.budget_labor_cost) }}
        </span>
      </div>
    </div>

    <!-- FORMULARIO NUEVO REPORTE -->
    <div class="form-card">
      <h3 class="form-title">
        <i class="bi bi-plus-circle"></i> Registrar nuevo reporte de avance
      </h3>
      <div class="form-body">
        <div class="fg slider-group">
          <label>
            Porcentaje de avance al momento de este reporte:
            <strong class="prog-num">{{ repForm.progress_percent }}%</strong>
          </label>
          <input v-model.number="repForm.progress_percent"
            type="range" min="0" max="100" step="5" class="form-range" />
          <div class="range-marks">
            <span>0%</span><span>25%</span><span>50%</span><span>75%</span><span>100%</span>
          </div>
        </div>
        <div class="fg">
          <label>Descripción del trabajo realizado *</label>
          <textarea v-model="repForm.description" class="form-control" rows="3"
            data-v="repdesc"
            placeholder="Describe qué actividades se realizaron, novedades, materiales usados, etc."
            @input="clearErr" />
        </div>
        <button class="btn btn-primary" @click="addReport" :disabled="saving">
          <i v-if="saving" class="bi bi-arrow-repeat spin"></i>
          <i v-else class="bi bi-send"></i>
          {{ saving ? 'Guardando...' : 'Registrar reporte' }}
        </button>
      </div>
    </div>

    <!-- LÍNEA DE TIEMPO DE REPORTES -->
    <div class="timeline-header">
      <h3 class="section-title">
        <i class="bi bi-clock-history"></i>
        Historial de reportes ({{ reports.length }})
      </h3>
    </div>

    <div v-if="loading" class="loading-center">
      <i class="bi bi-arrow-repeat spin"></i>
    </div>

    <div v-else-if="reports.length === 0" class="empty-state">
      <i class="bi bi-journal-x"></i>
      <p>No hay reportes registrados aún</p>
    </div>

    <div v-else class="timeline">
      <div v-for="(r, idx) in reportsDesc" :key="r.id" class="tl-item">
        <!-- Línea y punto -->
        <div class="tl-left">
          <div class="tl-dot" :class="idx === 0 ? 'dot-blue' : 'dot-gray'"></div>
          <div class="tl-line" v-if="idx < reportsDesc.length - 1"></div>
        </div>
        <!-- Contenido -->
        <div class="tl-card">
          <div class="tl-header">
            <span class="tl-progress">
              <i class="bi bi-bar-chart-fill"></i>
              {{ r.progress_percent }}% de avance
            </span>
            <span class="tl-date">{{ fmtDateTime(r.created_at) }}</span>
            <button class="btn-del-tl" @click="delReport(r)" title="Eliminar reporte">
              <i class="bi bi-trash"></i>
            </button>
          </div>
          <p class="tl-desc">{{ r.description }}</p>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { useRoute } from "vue-router"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import { validateForm } from "@/utils/validate"

const route  = useRoute()
const taskId = route.params.taskId

const task    = ref(null)
const reports = ref([])
const loading = ref(true)
const saving  = ref(false)

const repForm = ref({ progress_percent: 0, description: "" })

const reportsDesc = computed(() => [...reports.value].reverse())

const isOverdue = computed(() =>
  task.value?.due_date &&
  new Date(task.value.due_date) < new Date() &&
  ![5, 6].includes(task.value?.status_id)
)

const STATUS_CLASSES = {
  1:"badge-orange", 2:"badge-blue", 3:"badge-green",
  4:"badge-purple", 5:"badge-darkgreen", 6:"badge-red",
}
function statusClass(id) { return STATUS_CLASSES[id] || "badge-gray" }
function fmt(n)          { return Number(n||0).toLocaleString("es-CO") }
function fmtDate(iso)    { return iso ? new Date(iso).toLocaleDateString("es-CO", { day:"2-digit", month:"short", year:"numeric" }) : "" }
function fmtDateTime(iso){ return iso ? new Date(iso).toLocaleString("es-CO", { day:"2-digit", month:"short", year:"numeric", hour:"2-digit", minute:"2-digit" }) : "" }
function clearErr(e)     { e.target.classList.remove("field-invalid") }

async function load() {
  loading.value = true
  try {
    const [taskRes, repRes] = await Promise.all([
      api.get(`/tasks/${taskId}`),
      api.get(`/task-progress/${taskId}`),
    ])
    task.value    = taskRes.data
    reports.value = repRes.data
    repForm.value.progress_percent = task.value.progress
  } catch {
    showToast("Error cargando datos", "error")
  } finally {
    loading.value = false
  }
}

async function addReport() {
  const check = validateForm([
    { value: repForm.value.description, selector: '[data-v="repdesc"]', label: "Descripción" }
  ])
  if (!check.valid) { showToast(check.message, "warning"); return }

  saving.value = true
  try {
    await api.post(`/task-progress/${taskId}`, repForm.value)
    // Actualizar el avance de la tarea al % del reporte
    await api.patch(`/tasks/${taskId}/progress`, {
      progress: repForm.value.progress_percent
    })
    showToast("Reporte registrado", "success")
    repForm.value.description = ""
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error guardando reporte", "error")
  } finally {
    saving.value = false
  }
}

async function delReport(r) {
  const { isConfirmed } = await window.Swal.fire({
    title: "¿Eliminar este reporte?", icon: "warning",
    showCancelButton: true, confirmButtonText: "Eliminar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  await api.delete(`/task-progress/${r.id}`)
  showToast("Reporte eliminado", "success")
  await load()
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 820px; }
.page-header    { display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:20px; }
.header-left    { display:flex; align-items:flex-start; gap:12px; }
.btn-back       { background:#f1f5f9; border:none; border-radius:8px; padding:8px 12px; cursor:pointer; font-size:16px; color:#475569; }
.btn-back:hover { background:#e2e8f0; }
.page-title     { font-size:20px; font-weight:700; color:#1e293b; margin:0 0 4px; display:flex; align-items:center; gap:8px; }
.page-subtitle  { font-size:13px; color:#64748b; margin:0; display:flex; align-items:center; gap:6px; }

/* PROGRESS CARD */
.progress-card { background:#fff; border-radius:14px; box-shadow:0 1px 6px rgba(0,0,0,0.08); padding:18px 22px; margin-bottom:20px; }
.progress-info { display:flex; justify-content:space-between; align-items:baseline; margin-bottom:10px; }
.prog-label    { font-size:13px; color:#64748b; }
.prog-value    { font-size:22px; font-weight:800; color:#1e293b; }
.prog-track    { height:10px; background:#f1f5f9; border-radius:5px; overflow:hidden; margin-bottom:10px; }
.prog-fill     { height:100%; border-radius:5px; transition:width 0.4s; }
.fill-blue  { background:#3b82f6; }
.fill-green { background:#22c55e; }
.prog-footer   { display:flex; flex-wrap:wrap; gap:14px; font-size:12px; color:#64748b; }
.text-danger   { color:#ef4444 !important; }

/* FORM */
.form-card  { background:#fff; border-radius:14px; box-shadow:0 1px 6px rgba(0,0,0,0.08); padding:18px 22px; margin-bottom:20px; }
.form-title { font-size:14px; font-weight:700; color:#475569; margin:0 0 16px; display:flex; align-items:center; gap:7px; }
.form-body  { display:flex; flex-direction:column; gap:14px; }
.fg         { display:flex; flex-direction:column; gap:5px; }
.fg label   { font-size:13px; font-weight:600; color:#374151; }
.slider-group { gap:8px; }
.prog-num   { color:#3b82f6; font-size:15px; margin-left:6px; }
.range-marks { display:flex; justify-content:space-between; font-size:10px; color:#94a3b8; margin-top:-2px; }

/* TIMELINE */
.timeline-header { margin-bottom:12px; }
.section-title   { font-size:15px; font-weight:700; color:#1e293b; display:flex; align-items:center; gap:8px; }
.loading-center  { padding:40px; text-align:center; color:#94a3b8; }
.empty-state     { padding:48px; text-align:center; color:#94a3b8; }
.empty-state .bi { font-size:38px; display:block; margin-bottom:10px; }

.timeline   { display:flex; flex-direction:column; }
.tl-item    { display:flex; gap:14px; }
.tl-left    { display:flex; flex-direction:column; align-items:center; width:20px; flex-shrink:0; }
.tl-dot     { width:14px; height:14px; border-radius:50%; flex-shrink:0; margin-top:16px; }
.dot-blue   { background:#3b82f6; box-shadow:0 0 0 3px #dbeafe; }
.dot-gray   { background:#cbd5e1; }
.tl-line    { flex:1; width:2px; background:#f1f5f9; margin-top:4px; min-height:24px; }

.tl-card    { flex:1; background:#fff; border-radius:12px; box-shadow:0 1px 4px rgba(0,0,0,0.07); padding:14px 16px; margin-bottom:12px; }
.tl-header  { display:flex; align-items:center; gap:10px; margin-bottom:8px; flex-wrap:wrap; }
.tl-progress { font-size:13px; font-weight:700; color:#3b82f6; display:flex; align-items:center; gap:5px; }
.tl-date    { font-size:11px; color:#94a3b8; margin-left:auto; }
.tl-desc    { font-size:13px; color:#1e293b; line-height:1.6; margin:0; white-space:pre-wrap; }

.btn-del-tl { background:none; border:none; color:#94a3b8; cursor:pointer; font-size:13px; padding:2px 6px; border-radius:5px; }
.btn-del-tl:hover { color:#ef4444; background:#fef2f2; }

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
</style>
