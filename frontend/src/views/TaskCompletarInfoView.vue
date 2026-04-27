<template>
  <div class="page-container">

    <!-- ENCABEZADO -->
    <div class="page-header">
      <div>
        <h1 class="page-title">
          <i class="bi bi-clipboard-check"></i> Completar Información de Tareas
        </h1>
        <p class="page-subtitle">Tareas registradas que aún requieren información adicional</p>
      </div>
    </div>

    <!-- TABS -->
    <div class="tabs-row">
      <button class="tab-btn" :class="{ active: activeTab === 'sin_asignar' }" @click="activeTab = 'sin_asignar'">
        <i class="bi bi-person-x"></i> Sin Asignar
        <span class="tab-count tab-orange">{{ data.sin_asignar?.length || 0 }}</span>
      </button>
      <button class="tab-btn" :class="{ active: activeTab === 'info_incompleta' }" @click="activeTab = 'info_incompleta'">
        <i class="bi bi-exclamation-circle"></i> Info Incompleta
        <span class="tab-count tab-yellow">{{ data.info_incompleta?.length || 0 }}</span>
      </button>
    </div>

    <!-- LOADING -->
    <div v-if="loading" class="loading-state">
      <i class="bi bi-arrow-repeat spin"></i> Cargando tareas...
    </div>

    <!-- LISTA SIN ASIGNAR -->
    <div v-else-if="activeTab === 'sin_asignar'">
      <div v-if="!data.sin_asignar?.length" class="empty-state">
        <i class="bi bi-person-check"></i>
        <p>Todas las tareas tienen un responsable asignado</p>
      </div>
      <div v-else class="task-rows">
        <div v-for="t in data.sin_asignar" :key="t.id" class="task-row">
          <div class="task-row-info">
            <span class="task-id">#{{ t.id }}</span>
            <div class="task-main">
              <strong class="task-title">{{ t.title }}</strong>
              <span v-if="t.asset_id" class="task-asset">
                <i class="bi bi-building"></i> {{ assetName(t.asset_id) }}
              </span>
            </div>
            <span class="status-badge badge-orange">Sin Asignar</span>
          </div>
          <div class="task-row-action">
            <select v-model="assignMap[t.id]" class="form-select form-select-sm" style="min-width:200px">
              <option :value="null">— Seleccionar responsable —</option>
              <option v-for="u in users" :key="u.id" :value="u.id">{{ u.nombre }}</option>
            </select>
            <button class="btn btn-primary btn-sm" :disabled="!assignMap[t.id] || saving === t.id"
              @click="assignTask(t)">
              <i v-if="saving === t.id" class="bi bi-arrow-repeat spin"></i>
              <i v-else class="bi bi-person-check-fill"></i>
              Asignar
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- LISTA INFO INCOMPLETA -->
    <div v-else-if="activeTab === 'info_incompleta'">
      <div v-if="!data.info_incompleta?.length" class="empty-state">
        <i class="bi bi-check2-circle"></i>
        <p>Todas las tareas asignadas tienen su información completa</p>
      </div>
      <div v-else class="task-rows">
        <div v-for="t in data.info_incompleta" :key="t.id" class="task-row">
          <div class="task-row-info">
            <span class="task-id">#{{ t.id }}</span>
            <div class="task-main">
              <strong class="task-title">{{ t.title }}</strong>
              <span v-if="t.asset_id" class="task-asset">
                <i class="bi bi-building"></i> {{ assetName(t.asset_id) }}
              </span>
              <div class="missing-chips">
                <span v-if="!t.worker_id"    class="chip-miss"><i class="bi bi-tools"></i> Sin ejecutor</span>
                <span v-if="!t.due_date"     class="chip-miss"><i class="bi bi-calendar-x"></i> Sin fecha límite</span>
                <span v-if="!t.description"  class="chip-miss"><i class="bi bi-card-text"></i> Sin descripción</span>
              </div>
            </div>
            <div class="task-assigned">
              <i class="bi bi-person-check"></i>
              {{ t.assigned_to_name || '—' }}
            </div>
          </div>
          <button class="btn btn-outline-primary btn-sm" @click="openComplete(t)">
            <i class="bi bi-pencil-square"></i> Completar
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL COMPLETAR INFO -->
    <div v-if="showModal && editing" class="modal-overlay" @click.self="closeModal">
      <div class="modal-box">
        <div class="modal-header-bar">
          <div>
            <h2>Completar información</h2>
            <p class="modal-subtitle">#{{ editing.id }} — {{ editing.title }}</p>
          </div>
          <button class="btn-close-x" @click="closeModal"><i class="bi bi-x-lg"></i></button>
        </div>

        <div class="modal-body-area">

          <!-- Descripción -->
          <div class="fg">
            <label>Descripción</label>
            <textarea v-model="completeForm.description" class="form-control" rows="3"
              placeholder="Detalles de la tarea..."></textarea>
          </div>

          <div class="form-row2">
            <!-- Ejecutor -->
            <div class="fg">
              <label>Ejecutor / Profesional</label>
              <select v-model="completeForm.worker_id" class="form-select">
                <option :value="null">— Sin ejecutor —</option>
                <option v-for="w in workers" :key="w.id" :value="w.id">
                  {{ w.name }}{{ w.profession_name ? ' — ' + w.profession_name : '' }}
                </option>
              </select>
            </div>

            <!-- Asignado a -->
            <div class="fg">
              <label>Responsable</label>
              <select v-model="completeForm.assigned_to" class="form-select">
                <option :value="null">— Sin asignar —</option>
                <option v-for="u in users" :key="u.id" :value="u.id">{{ u.nombre }}</option>
              </select>
            </div>
          </div>

          <div class="form-row2">
            <!-- Fecha inicio -->
            <div class="fg">
              <label>Fecha inicio</label>
              <input v-model="completeForm.start_date" type="date" class="form-control" />
            </div>

            <!-- Fecha límite -->
            <div class="fg">
              <label>Fecha límite *</label>
              <input v-model="completeForm.due_date" type="date" class="form-control" />
            </div>
          </div>

          <!-- Presupuesto -->
          <div class="fg">
            <label>Presupuesto estimado ($)</label>
            <input v-model.number="completeForm.budget_labor_cost" type="number" min="0"
              class="form-control" placeholder="0" />
          </div>

        </div>

        <div class="modal-footer-bar">
          <button class="btn btn-secondary" @click="closeModal">Cancelar</button>
          <button class="btn btn-primary" @click="saveComplete" :disabled="savingModal">
            <i v-if="savingModal" class="bi bi-arrow-repeat spin"></i>
            {{ savingModal ? 'Guardando...' : 'Guardar cambios' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

const data        = ref({ sin_asignar: [], info_incompleta: [] })
const assets      = ref([])
const users       = ref([])
const workers     = ref([])
const loading     = ref(true)
const activeTab   = ref("sin_asignar")
const assignMap   = ref({})   // taskId → userId para asignación rápida
const saving      = ref(null) // taskId siendo guardado
const showModal   = ref(false)
const savingModal = ref(false)
const editing     = ref(null)

const completeForm = ref({
  description: "", worker_id: null, assigned_to: null,
  start_date: "", due_date: "", budget_labor_cost: 0
})

function assetName(id) {
  return assets.value.find(a => a.id === id)?.name || "—"
}

async function load() {
  loading.value = true
  try {
    const [incRes, assetsRes, usersRes, workersRes] = await Promise.allSettled([
      api.get("/tasks/incomplete-info"),
      api.get("/assets/"),
      api.get("/tasks/users-list"),
      api.get("/workers/"),
    ])
    if (incRes.status     === "fulfilled") data.value    = incRes.value.data
    if (assetsRes.status  === "fulfilled") assets.value  = assetsRes.value.data
    if (usersRes.status   === "fulfilled") users.value   = usersRes.value.data
    if (workersRes.status === "fulfilled") workers.value = workersRes.value.data
  } catch {
    showToast("Error cargando datos", "error")
  } finally {
    loading.value = false
  }
}

async function assignTask(task) {
  const userId = assignMap.value[task.id]
  if (!userId) return
  saving.value = task.id
  try {
    await api.put(`/tasks/${task.id}`, { ...task, assigned_to: userId, status_id: 2 })
    showToast("Responsable asignado correctamente", "success")
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error asignando responsable", "error")
  } finally {
    saving.value = null
  }
}

function openComplete(task) {
  editing.value = task
  completeForm.value = {
    description:        task.description || "",
    worker_id:          task.worker_id,
    assigned_to:        task.assigned_to,
    start_date:         task.start_date || "",
    due_date:           task.due_date || "",
    budget_labor_cost:  task.budget_labor_cost || 0,
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editing.value   = null
}

async function saveComplete() {
  savingModal.value = true
  try {
    await api.put(`/tasks/${editing.value.id}`, {
      ...editing.value,
      ...completeForm.value,
    })
    showToast("Información actualizada correctamente", "success")
    closeModal()
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error guardando cambios", "error")
  } finally {
    savingModal.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page-container  { padding: 24px; max-width: 1100px; }
.page-header     { margin-bottom: 20px; }
.page-title      { font-size: 20px; font-weight: 700; color: #1e293b; margin: 0; display: flex; align-items: center; gap: 8px; }
.page-subtitle   { font-size: 13px; color: #64748b; margin: 4px 0 0; }

.tabs-row  { display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
.tab-btn   { display: flex; align-items: center; gap: 7px; padding: 8px 18px; border: 2px solid #e2e8f0; border-radius: 10px; background: #fff; cursor: pointer; font-size: 13px; font-weight: 500; color: #64748b; transition: all 0.15s; }
.tab-btn:hover { border-color: #94a3b8; }
.tab-btn.active { border-color: #3b82f6; color: #1d4ed8; background: #eff6ff; }
.tab-count  { font-size: 11px; font-weight: 700; padding: 1px 7px; border-radius: 10px; }
.tab-orange { background: #fff7ed; color: #c2410c; }
.tab-yellow { background: #fef3c7; color: #b45309; }

.loading-state  { padding: 60px; text-align: center; color: #94a3b8; font-size: 15px; display: flex; align-items: center; justify-content: center; gap: 10px; }
.empty-state    { padding: 60px; text-align: center; color: #94a3b8; }
.empty-state .bi { font-size: 40px; display: block; margin-bottom: 10px; }

.task-rows  { display: flex; flex-direction: column; gap: 8px; }
.task-row   { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px 18px; display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.task-row-info { display: flex; align-items: center; gap: 12px; flex: 1; min-width: 0; flex-wrap: wrap; }
.task-id    { font-size: 11px; color: #94a3b8; font-weight: 600; white-space: nowrap; }
.task-main  { flex: 1; min-width: 0; }
.task-title { font-size: 14px; color: #1e293b; display: block; }
.task-asset { font-size: 12px; color: #64748b; display: flex; align-items: center; gap: 4px; margin-top: 2px; }
.task-assigned { font-size: 12px; color: #64748b; display: flex; align-items: center; gap: 4px; white-space: nowrap; }
.task-row-action { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }

.missing-chips { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }
.chip-miss { display: inline-flex; align-items: center; gap: 3px; font-size: 10px; font-weight: 600; color: #b45309; background: #fef3c7; padding: 2px 8px; border-radius: 10px; }

.status-badge  { font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 20px; white-space: nowrap; }
.badge-orange  { background: #fff7ed; color: #c2410c; }
.badge-blue    { background: #dbeafe; color: #1e40af; }

/* MODAL */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.45); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-box     { background: #fff; border-radius: 16px; width: 620px; max-width: 96vw; max-height: 90vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
.modal-header-bar { display: flex; align-items: flex-start; justify-content: space-between; padding: 18px 24px 14px; border-bottom: 1px solid #f1f5f9; flex-shrink: 0; }
.modal-header-bar h2 { font-size: 17px; font-weight: 700; color: #1e293b; margin: 0; }
.modal-subtitle  { font-size: 12px; color: #94a3b8; margin: 2px 0 0; }
.modal-body-area { padding: 20px 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
.modal-footer-bar{ padding: 14px 24px 18px; display: flex; justify-content: flex-end; gap: 10px; border-top: 1px solid #f1f5f9; flex-shrink: 0; }

.form-row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.fg        { display: flex; flex-direction: column; gap: 4px; }
.fg label  { font-size: 13px; font-weight: 600; color: #374151; }
.btn-close-x { background: none; border: none; font-size: 18px; cursor: pointer; color: #94a3b8; }
.btn-close-x:hover { color: #1e293b; }

.spin { display: inline-block; animation: spin 0.8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

@media (max-width: 640px) {
  .page-container { padding: 14px 12px; }
  .form-row2 { grid-template-columns: 1fr; }
  .task-row  { flex-direction: column; align-items: flex-start; }
}
</style>
