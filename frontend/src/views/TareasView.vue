<template>
  <div class="page-container">

    <!-- ENCABEZADO -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Gestión de Tareas</h1>
        <p class="page-subtitle">
          Total: <strong>{{ tasks.length }}</strong> tareas
        </p>
      </div>
      <button class="btn btn-primary" @click="openCreate">
        <i class="bi bi-plus-lg"></i> Nueva tarea
      </button>
    </div>

    <!-- FILTROS -->
    <div class="filters-row">
      <input v-model="search" class="form-control" placeholder="Buscar tarea..." style="max-width:260px" />
      <select v-model="filterStatus" class="form-select" style="max-width:180px">
        <option value="">Todos los estados</option>
        <option v-for="s in statuses" :key="s.id" :value="s.id">{{ s.name }}</option>
      </select>
    </div>

    <!-- TABLA -->
    <div class="table-card">
      <div v-if="loading" class="table-loading">
        <i class="bi bi-arrow-repeat spin"></i> Cargando...
      </div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Título</th>
            <th>Activo</th>
            <th>Ejecutor</th>
            <th class="text-center">Estado</th>
            <th class="text-center">Avance</th>
            <th>Fecha límite</th>
            <th class="text-center">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in filtered" :key="t.id" :class="{ 'row-incomplete': isIncomplete(t) }">
            <td class="text-muted">{{ t.id }}</td>
            <td>
              <strong>{{ t.title }}</strong>
              <div v-if="t.description" class="task-desc">{{ t.description }}</div>
              <span v-if="isIncomplete(t)" class="chip-incomplete">
                <i class="bi bi-exclamation-circle-fill"></i> Info incompleta
              </span>
            </td>
            <td class="text-muted">{{ assetName(t.asset_id) }}</td>
            <td class="text-muted">{{ workerName(t.worker_id) }}</td>
            <td class="text-center">
              <span class="status-badge" :class="statusClass(t.status_id)">
                {{ t.status_name }}
              </span>
            </td>
            <td class="text-center">
              <div class="progress-wrap">
                <div class="progress-bar-mini">
                  <div class="progress-fill" :style="{ width: t.progress + '%' }"
                    :class="t.progress === 100 ? 'fill-green' : 'fill-blue'"></div>
                </div>
                <span class="progress-label">{{ t.progress }}%</span>
              </div>
            </td>
            <td :class="isOverdue(t) ? 'text-danger' : 'text-muted'">
              <span v-if="t.due_date">
                <i v-if="isOverdue(t)" class="bi bi-exclamation-triangle-fill me-1"></i>
                {{ fmtDate(t.due_date) }}
              </span>
              <span v-else class="text-muted">—</span>
            </td>
            <td class="text-center">
              <div class="d-flex gap-1 justify-content-center">
                <button class="btn btn-warning btn-sm" @click="openEdit(t)" title="Editar">
                  <i class="bi bi-pencil"></i> Editar
                </button>
                <button class="btn btn-danger btn-sm" @click="handleDelete(t)" title="Eliminar">
                  <i class="bi bi-trash"></i>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="filtered.length === 0">
            <td colspan="8" class="text-center text-muted py-4">
              <i class="bi bi-clipboard-x" style="font-size:28px;display:block;margin-bottom:8px"></i>
              No hay tareas con estos filtros
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ══════════════════════════════════════════════
         MODAL CREAR (Fase 1 — campos mínimos)
    ══════════════════════════════════════════════ -->
    <div v-if="showModal && !editMode" class="modal-overlay" @click.self="closeModal">
      <div class="modal-box modal-create">
        <div class="modal-header-bar">
          <div>
            <h2>Nueva tarea</h2>
            <p class="modal-subtitle">Registro rápido — completar info después</p>
          </div>
          <button class="btn-close-x" @click="closeModal"><i class="bi bi-x-lg"></i></button>
        </div>

        <div class="modal-body-area">

          <!-- Título -->
          <div class="fg full">
            <label>Título de la tarea *</label>
            <input v-model="form.title" data-v="title" class="form-control"
              placeholder="Describe brevemente la tarea" @input="clearError" />
          </div>

          <!-- Activo -->
          <div class="fg full">
            <label>Activo sobre el que se realizará *</label>
            <select v-model="form.asset_id" data-v="asset" class="form-select" @change="clearError">
              <option :value="null">— Seleccionar activo —</option>
              <option v-for="a in assets" :key="a.id" :value="a.id">{{ a.name }}</option>
            </select>
          </div>

          <!-- Estado -->
          <div class="fg full">
            <label>Estado inicial</label>
            <div class="status-pills-create">
              <button type="button"
                class="status-pill-create"
                :class="{ active: form.status_id === 1 }"
                @click="form.status_id = 1; form.assigned_to = null">
                <span class="pill-dot dot-orange"></span>
                Sin Asignar
              </button>
              <button type="button"
                class="status-pill-create"
                :class="{ active: form.status_id === 2 }"
                @click="form.status_id = 2">
                <span class="pill-dot dot-blue"></span>
                Asignada
              </button>
            </div>
          </div>

          <!-- Asignado a (solo si Asignada) -->
          <Transition name="fade-down">
            <div v-if="form.status_id === 2" class="fg full">
              <label>Responsable / Asignado a *</label>
              <select v-model="form.assigned_to" data-v="assigned" class="form-select" @change="clearError">
                <option :value="null">— Seleccionar responsable —</option>
                <option v-for="u in users" :key="u.id" :value="u.id">{{ u.nombre }}</option>
              </select>
            </div>
          </Transition>

        </div>

        <div class="modal-footer-bar">
          <button class="btn btn-secondary" @click="closeModal">Cancelar</button>
          <button class="btn btn-primary" @click="save" :disabled="saving">
            <i v-if="saving" class="bi bi-arrow-repeat spin"></i>
            {{ saving ? 'Guardando...' : 'Registrar tarea' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════
         MODAL EDITAR (todos los campos)
    ══════════════════════════════════════════════ -->
    <div v-if="showModal && editMode" class="modal-overlay" @click.self="closeModal">
      <div class="modal-box">
        <div class="modal-header-bar">
          <h2>Editar tarea</h2>
          <button class="btn-close-x" @click="closeModal"><i class="bi bi-x-lg"></i></button>
        </div>

        <div class="modal-body-area">

          <!-- Título -->
          <div class="fg full">
            <label>Título *</label>
            <input v-model="form.title" data-v="title" class="form-control"
              placeholder="Describe brevemente la tarea" @input="clearError" />
          </div>

          <!-- Descripción -->
          <div class="fg full">
            <label>Descripción <span class="opt">(opcional)</span></label>
            <textarea v-model="form.description" class="form-control" rows="2"
              placeholder="Detalles adicionales de la tarea"></textarea>
          </div>

          <div class="form-row2">
            <!-- Activo -->
            <div class="fg">
              <label>Activo relacionado</label>
              <select v-model="form.asset_id" class="form-select">
                <option :value="null">— Sin activo —</option>
                <option v-for="a in assets" :key="a.id" :value="a.id">{{ a.name }}</option>
              </select>
            </div>

            <!-- Estado -->
            <div class="fg">
              <label>Estado</label>
              <select v-model="form.status_id" class="form-select">
                <option v-for="s in statuses" :key="s.id" :value="s.id">{{ s.name }}</option>
              </select>
            </div>
          </div>

          <div class="form-row2">
            <!-- Asignado a (Task Leader) -->
            <div class="fg">
              <label>Asignado a</label>
              <select v-model="form.assigned_to" class="form-select">
                <option :value="null">— Sin asignar —</option>
                <option v-for="u in users" :key="u.id" :value="u.id">{{ u.nombre }}</option>
              </select>
            </div>

            <!-- Ejecutor (Worker) -->
            <div class="fg">
              <div class="d-flex justify-content-between align-items-center mb-1">
                <label class="mb-0">Ejecutor / Profesional</label>
                <WorkersModal @updated="reloadWorkers" />
              </div>
              <select v-model="form.worker_id" class="form-select">
                <option :value="null">— Sin ejecutor —</option>
                <option v-for="w in workers" :key="w.id" :value="w.id">
                  {{ w.name }}{{ w.profession_name ? ' — ' + w.profession_name : '' }}
                </option>
              </select>
            </div>
          </div>

          <div class="form-row2">
            <!-- Fecha inicio -->
            <div class="fg">
              <label>Fecha inicio</label>
              <input v-model="form.start_date" type="date" class="form-control" />
            </div>

            <!-- Fecha límite -->
            <div class="fg">
              <label>Fecha límite</label>
              <input v-model="form.due_date" type="date" class="form-control" />
            </div>
          </div>

          <div class="form-row2">
            <!-- Presupuesto -->
            <div class="fg">
              <label>Presupuesto estimado ($)</label>
              <input v-model.number="form.budget_labor_cost" type="number" min="0"
                class="form-control" placeholder="0" />
            </div>

            <!-- Avance -->
            <div class="fg">
              <label>Avance actual: <strong>{{ form.progress }}%</strong></label>
              <input v-model.number="form.progress" type="range" min="0" max="100"
                class="form-range" />
            </div>
          </div>

        </div>

        <div class="modal-footer-bar">
          <button class="btn btn-secondary" @click="closeModal">Cancelar</button>
          <button class="btn btn-primary" @click="save" :disabled="saving">
            <i v-if="saving" class="bi bi-arrow-repeat spin"></i>
            {{ saving ? 'Guardando...' : 'Guardar tarea' }}
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
import { validateForm } from "@/utils/validate"
import WorkersModal from "@/components/WorkersModal.vue"

// ── Estado ──────────────────────────────────────────────────────
const tasks    = ref([])
const statuses = ref([])
const assets   = ref([])
const workers  = ref([])
const users    = ref([])
const loading  = ref(true)
const saving   = ref(false)
const showModal = ref(false)
const editMode  = ref(false)
const search    = ref("")
const filterStatus = ref("")

const emptyCreateForm = () => ({
  title: "", asset_id: null, status_id: 1, assigned_to: null
})

const emptyEditForm = () => ({
  id: null, title: "", description: "", asset_id: null, status_id: 1,
  assigned_to: null, worker_id: null,
  start_date: "", due_date: "", budget_labor_cost: 0,
  actual_labor_cost: 0, progress: 0
})

const form = ref(emptyCreateForm())

// ── Filtrado ─────────────────────────────────────────────────────
const filtered = computed(() =>
  tasks.value.filter(t => {
    const matchSearch = !search.value ||
      t.title.toLowerCase().includes(search.value.toLowerCase())
    const matchStatus = !filterStatus.value ||
      t.status_id === Number(filterStatus.value)
    return matchSearch && matchStatus
  })
)

// ── Helpers visuales ─────────────────────────────────────────────
const STATUS_CLASSES = {
  1: "badge-orange", 2: "badge-blue",     3: "badge-green",
  4: "badge-purple", 5: "badge-darkgreen", 6: "badge-red",
}

function statusClass(id) { return STATUS_CLASSES[id] || "badge-gray" }

function assetName(id) {
  const a = assets.value.find(x => x.id === id)
  return a ? a.name : "—"
}

function workerName(id) {
  const w = workers.value.find(x => x.id === id)
  return w ? w.name : "—"
}

function isIncomplete(t) {
  if (t.status_id === 1 && !t.assigned_to) return true
  if (t.status_id === 2 && (!t.worker_id || !t.due_date)) return true
  return false
}

async function reloadWorkers() {
  const res = await api.get("/workers/")
  workers.value = res.data
}

function fmtDate(iso) {
  if (!iso) return ""
  const d = new Date(iso)
  return d.toLocaleDateString("es-CO", { day: "2-digit", month: "2-digit", year: "numeric" })
}

function isOverdue(t) {
  return t.due_date && new Date(t.due_date) < new Date() && ![5, 6].includes(t.status_id)
}

function clearError(e) { e.target?.classList.remove("field-invalid") }

// ── Carga de datos ───────────────────────────────────────────────
async function loadAll() {
  loading.value = true

  const [tasksRes, statusRes, assetsRes, workersRes] = await Promise.allSettled([
    api.get("/tasks/"),
    api.get("/task-status/"),
    api.get("/assets/"),
    api.get("/workers/"),
  ])

  if (tasksRes.status   === "fulfilled") tasks.value    = tasksRes.value.data
  if (statusRes.status  === "fulfilled") statuses.value = statusRes.value.data
  if (assetsRes.status  === "fulfilled") assets.value   = assetsRes.value.data
  if (workersRes.status === "fulfilled") workers.value  = workersRes.value.data

  loading.value = false

  try {
    const usersRes = await api.get("/tasks/users-list")
    users.value = usersRes.data
  } catch { users.value = [] }
}

// ── Crear / Editar ───────────────────────────────────────────────
function openCreate() {
  form.value  = emptyCreateForm()
  editMode.value  = false
  showModal.value = true
}

function openEdit(task) {
  form.value = {
    id:                 task.id,
    title:              task.title,
    description:        task.description || "",
    asset_id:           task.asset_id,
    status_id:          task.status_id,
    assigned_to:        task.assigned_to,
    worker_id:          task.worker_id,
    start_date:         task.start_date?.split("T")[0] || "",
    due_date:           task.due_date?.split("T")[0] || "",
    budget_labor_cost:  task.budget_labor_cost || 0,
    actual_labor_cost:  task.actual_labor_cost || 0,
    progress:           task.progress || 0,
  }
  editMode.value  = true
  showModal.value = true
}

function closeModal() {
  document.querySelectorAll(".field-invalid").forEach(el => el.classList.remove("field-invalid"))
  showModal.value = false
}

async function save() {
  if (!editMode.value) {
    const rules = [
      { value: form.value.title,    selector: '[data-v="title"]',    label: "Título" },
      { value: form.value.asset_id, selector: '[data-v="asset"]',    label: "Activo" },
    ]
    if (form.value.status_id === 2) {
      rules.push({ value: form.value.assigned_to, selector: '[data-v="assigned"]', label: "Responsable" })
    }
    const check = validateForm(rules)
    if (!check.valid) { showToast(check.message, "warning"); return }
  } else {
    const check = validateForm([
      { value: form.value.title, selector: '[data-v="title"]', label: "Título" }
    ])
    if (!check.valid) { showToast(check.message, "warning"); return }
  }

  saving.value = true
  try {
    if (editMode.value) {
      await api.put(`/tasks/${form.value.id}`, form.value)
      showToast("Tarea actualizada correctamente", "success")
    } else {
      await api.post("/tasks/", form.value)
      showToast("Tarea registrada. Completa la información restante cuando sea posible.", "success")
    }
    closeModal()
    await loadAll()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error guardando tarea", "error")
  } finally {
    saving.value = false
  }
}

async function handleDelete(task) {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar "${task.title}"?`,
    text: "Esta acción no se puede deshacer.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, eliminar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/tasks/${task.id}`)
    showToast("Tarea eliminada", "success")
    await loadAll()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error eliminando tarea", "error")
  }
}

onMounted(loadAll)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1200px; }
.page-header    { display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:20px; flex-wrap:wrap; gap:12px; }
.page-title     { font-size:20px; font-weight:700; color:#1e293b; margin-bottom:4px; }
.page-subtitle  { font-size:13px; color:#64748b; }

.filters-row { display:flex; gap:12px; margin-bottom:16px; flex-wrap:wrap; }

/* TABLE */
.table-card   { background:#fff; border-radius:14px; box-shadow:0 1px 6px rgba(0,0,0,0.08); overflow-x:auto; }
.table-loading{ padding:40px; text-align:center; color:#94a3b8; }
.data-table   { width:100%; min-width:800px; border-collapse:collapse; font-size:14px; }
.data-table th{ background:#f8fafc; color:#475569; font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:0.4px; padding:12px 16px; border-bottom:1px solid #e2e8f0; }
.data-table td{ padding:12px 16px; border-bottom:1px solid #f1f5f9; vertical-align:middle; }
.data-table tr:last-child td { border-bottom:none; }
.data-table tr:hover td { background:#f8fafc; }
.row-incomplete td { background:#fffbeb !important; }
.text-center  { text-align:center; }
.text-muted   { color:#94a3b8 !important; font-size:13px; }
.text-danger  { color:#ef4444 !important; }

.task-desc { font-size:12px; color:#94a3b8; margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:260px; }
.chip-incomplete { display:inline-flex; align-items:center; gap:3px; font-size:10px; font-weight:600; color:#d97706; background:#fef3c7; padding:1px 7px; border-radius:10px; margin-top:3px; }

.badge-alert { background:#ef4444; color:#fff; font-size:9px; font-weight:800; border-radius:10px; padding:1px 5px; margin-left:4px; }

/* STATUS BADGES */
.status-badge   { font-size:11px; font-weight:700; padding:3px 10px; border-radius:20px; white-space:nowrap; }
.badge-orange   { background:#fff7ed; color:#c2410c; }
.badge-blue     { background:#dbeafe; color:#1e40af; }
.badge-green    { background:#dcfce7; color:#16a34a; }
.badge-purple   { background:#f3e8ff; color:#7c3aed; }
.badge-darkgreen{ background:#d1fae5; color:#065f46; }
.badge-red      { background:#fef2f2; color:#b91c1c; }
.badge-gray     { background:#f1f5f9; color:#64748b; }

/* PROGRESS */
.progress-wrap    { display:flex; align-items:center; gap:6px; justify-content:center; }
.progress-bar-mini{ width:60px; height:5px; background:#e2e8f0; border-radius:3px; overflow:hidden; }
.progress-fill    { height:100%; border-radius:3px; transition:width 0.3s; }
.fill-blue  { background:#3b82f6; }
.fill-green { background:#22c55e; }
.progress-label { font-size:11px; color:#64748b; min-width:28px; }

/* MODAL CREAR */
.modal-create .modal-subtitle { font-size:12px; color:#94a3b8; margin:2px 0 0; }

.status-pills-create { display:flex; gap:10px; }
.status-pill-create  { display:flex; align-items:center; gap:8px; padding:10px 18px; border:2px solid #e2e8f0; border-radius:10px; background:#fff; cursor:pointer; font-size:13px; font-weight:500; color:#374151; transition:all 0.15s; }
.status-pill-create:hover { border-color:#94a3b8; }
.status-pill-create.active { border-color: #3b82f6; background:#eff6ff; color:#1d4ed8; }
.pill-dot { width:10px; height:10px; border-radius:50%; flex-shrink:0; }
.dot-orange { background:#f97316; }
.dot-blue   { background:#3b82f6; }

/* Transición campos condicionales */
.fade-down-enter-active { transition: all 0.2s ease; }
.fade-down-leave-active { transition: all 0.15s ease; }
.fade-down-enter-from   { opacity:0; transform:translateY(-8px); }
.fade-down-leave-to     { opacity:0; transform:translateY(-8px); }

/* MODAL EDITAR */
.modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.45); display:flex; align-items:center; justify-content:center; z-index:1000; }
.modal-box     { background:#fff; border-radius:16px; width:680px; max-width:96vw; max-height:90vh; display:flex; flex-direction:column; box-shadow:0 20px 60px rgba(0,0,0,0.2); }
.modal-create  { width:480px; }
.modal-header-bar { display:flex; align-items:flex-start; justify-content:space-between; padding:18px 24px 14px; border-bottom:1px solid #f1f5f9; flex-shrink:0; }
.modal-header-bar h2 { font-size:17px; font-weight:700; color:#1e293b; margin:0; }
.modal-body-area  { padding:20px 24px; overflow-y:auto; display:flex; flex-direction:column; gap:14px; }
.modal-footer-bar { padding:14px 24px 18px; display:flex; justify-content:flex-end; gap:10px; border-top:1px solid #f1f5f9; flex-shrink:0; }

.form-row2 { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.fg        { display:flex; flex-direction:column; gap:4px; }
.fg.full   { width:100%; }
.fg label  { font-size:13px; font-weight:600; color:#374151; }
.opt       { font-weight:400; color:#94a3b8; }

.btn-close-x { background:none; border:none; font-size:18px; cursor:pointer; color:#94a3b8; }
.btn-close-x:hover { color:#1e293b; }

.form-range { accent-color:#3b82f6; }

.spin { display:inline-block; animation:spin 0.8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

@media (max-width: 768px) {
  .page-container { padding: 12px; }
  .form-row2      { grid-template-columns: 1fr; }
  .modal-box      { border-radius: 10px; max-height: 95vh; }
  .modal-create   { width: 95vw; }
  .status-pills-create { flex-direction: column; }
}
</style>
