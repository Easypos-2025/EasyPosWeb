<template>
  <div class="page-container">

    <!-- ENCABEZADO -->
    <div class="page-header">
      <div class="header-left">
        <button class="btn-back" @click="$router.back()">
          <i class="bi bi-arrow-left"></i>
        </button>
        <div>
          <div class="title-row" v-if="task">
            <h1 class="page-title">{{ task.title }}</h1>
            <span class="status-badge" :class="statusClass(task.status_id)">
              {{ task.status_name }}
            </span>
            <span v-if="isOverdue" class="overdue-chip">
              <i class="bi bi-exclamation-triangle-fill"></i> Atrasada
            </span>
          </div>
          <p class="page-subtitle" v-if="task">
            Tarea #{{ task.id }}
            <span v-if="task.worker_name"> · Ejecutor: <strong>{{ task.worker_name }}</strong></span>
            <span v-if="task.assigned_to_name"> · Responsable: <strong>{{ task.assigned_to_name }}</strong></span>
          </p>
        </div>
      </div>
      <div class="header-actions" v-if="task">
        <!-- Factura / Recibo — visual, sin funcionalidad aún -->
        <div class="billing-group" title="Disponible próximamente">
          <button class="btn-billing btn-factura" disabled>
            <i class="bi bi-file-earmark-text"></i>
            <span>Factura</span>
            <span class="soon-chip">DIAN</span>
          </button>
          <button class="btn-billing btn-recibo" disabled>
            <i class="bi bi-receipt"></i>
            <span>Recibo</span>
          </button>
        </div>

        <template v-if="!isWorkerRole">
          <button class="btn btn-danger btn-sm" @click="handleDelete">
            <i class="bi bi-trash"></i>
          </button>
          <button class="btn btn-primary" @click="saveTask" :disabled="saving">
            <i v-if="saving" class="bi bi-arrow-repeat spin"></i>
            <i v-else class="bi bi-floppy"></i>
            {{ saving ? 'Guardando...' : 'Guardar cambios' }}
          </button>
        </template>
      </div>
    </div>

    <!-- LOADING -->
    <div v-if="loading" class="loading-center">
      <i class="bi bi-arrow-repeat spin"></i> Cargando tarea...
    </div>

    <template v-else-if="task">

      <!-- ═══════════════════════════════════════════════════
           SECCIÓN SUPERIOR: INFO / FORMULARIO
      ════════════════════════════════════════════════════ -->
      <div class="detail-card">

        <!-- Barra de avance siempre visible -->
        <div class="progress-top">
          <div class="progress-track-lg">
            <div class="progress-fill-lg"
              :style="{ width: (form.progress || 0) + '%', background: progressColor }"
            ></div>
          </div>
          <span class="progress-pct">{{ form.progress || 0 }}%</span>
        </div>

        <div class="form-grid">

          <!-- TÍTULO -->
          <div class="fg span2">
            <label>Título *</label>
            <input v-if="!isWorkerRole" v-model="form.title" class="form-control"
              data-v="title" @input="clearError" placeholder="Título de la tarea" />
            <div v-else class="read-field">{{ task.title }}</div>
          </div>

          <!-- DESCRIPCIÓN -->
          <div class="fg span2">
            <label>Descripción</label>
            <textarea v-if="!isWorkerRole" v-model="form.description" class="form-control"
              rows="2" placeholder="Detalles adicionales"></textarea>
            <div v-else class="read-field read-text">{{ task.description || '—' }}</div>
          </div>

          <!-- ACTIVO -->
          <div class="fg">
            <label>Activo relacionado</label>
            <select v-if="!isWorkerRole" v-model="form.asset_id" class="form-select">
              <option :value="null">— Sin activo —</option>
              <option v-for="a in assets" :key="a.id" :value="a.id">{{ a.name }}</option>
            </select>
            <div v-else class="read-field">{{ assetName(task.asset_id) }}</div>
          </div>

          <!-- ESTADO -->
          <div class="fg">
            <label>Estado</label>
            <select v-if="!isWorkerRole" v-model.number="form.status_id" class="form-select">
              <option v-for="s in statuses" :key="s.id" :value="s.id">{{ s.name }}</option>
            </select>
            <div v-else class="read-field">
              <span class="status-badge" :class="statusClass(task.status_id)">
                {{ task.status_name }}
              </span>
            </div>
          </div>

          <!-- ASIGNADO A -->
          <div class="fg">
            <label>Responsable (Task Leader)</label>
            <select v-if="!isWorkerRole" v-model="form.assigned_to" class="form-select">
              <option :value="null">— Sin asignar —</option>
              <option v-for="u in users" :key="u.id" :value="u.id">{{ u.nombre }}</option>
            </select>
            <div v-else class="read-field">{{ task.assigned_to_name || '—' }}</div>
          </div>

          <!-- EJECUTOR -->
          <div class="fg">
            <div class="d-flex justify-content-between align-items-center mb-1">
              <label class="mb-0">Ejecutor / Profesional</label>
              <WorkersModal v-if="!isWorkerRole" @updated="reloadWorkers" />
            </div>
            <select v-if="!isWorkerRole" v-model="form.worker_id" class="form-select">
              <option :value="null">— Sin ejecutor —</option>
              <option v-for="w in workers" :key="w.id" :value="w.id">
                {{ w.name }}{{ w.profession_name ? ' — ' + w.profession_name : '' }}
              </option>
            </select>
            <div v-else class="read-field">{{ task.worker_name || '—' }}</div>
          </div>

          <!-- FECHA INICIO -->
          <div class="fg">
            <label>Fecha inicio</label>
            <input v-if="!isWorkerRole" v-model="form.start_date" type="date"
              class="form-control" />
            <div v-else class="read-field">{{ fmtDate(task.start_date) || '—' }}</div>
          </div>

          <!-- FECHA LÍMITE -->
          <div class="fg">
            <label>Fecha límite</label>
            <input v-if="!isWorkerRole" v-model="form.due_date" type="date"
              class="form-control" :class="{ 'border-danger': isOverdue }" />
            <div v-else class="read-field" :class="{ 'text-danger': isOverdue }">
              {{ fmtDate(task.due_date) || '—' }}
            </div>
          </div>

          <!-- PRESUPUESTO -->
          <div class="fg">
            <label>Presupuesto estimado ($)</label>
            <input v-if="!isWorkerRole" v-model.number="form.budget_labor_cost"
              type="number" min="0" class="form-control" placeholder="0" />
            <div v-else class="read-field">
              ${{ (task.budget_labor_cost || 0).toLocaleString('es-CO') }}
            </div>
          </div>

          <!-- AVANCE -->
          <div class="fg">
            <label>Avance: <strong>{{ form.progress }}%</strong></label>
            <input v-if="!isWorkerRole" v-model.number="form.progress"
              type="range" min="0" max="100" class="form-range" />
            <div v-else class="read-field">{{ task.progress }}%</div>
          </div>

        </div>
      </div>

      <!-- ═══════════════════════════════════════════════════
           TABS INFERIORES
      ════════════════════════════════════════════════════ -->
      <div class="tabs-bar">
        <button class="tab-btn" :class="{ active: tab === 'evidencias' }"
          @click="tab = 'evidencias'">
          <i class="bi bi-camera"></i> Evidencias
          <span class="tab-badge">{{ evidences.length }}</span>
        </button>
        <button class="tab-btn" :class="{ active: tab === 'materiales' }"
          @click="tab = 'materiales'">
          <i class="bi bi-boxes"></i> Materiales
          <span class="tab-badge">{{ materials.length }}</span>
        </button>
        <button class="tab-btn" :class="{ active: tab === 'gastos' }"
          @click="tab = 'gastos'">
          <i class="bi bi-receipt"></i> Gastos
          <span class="tab-badge">{{ expenses.length }}</span>
        </button>
      </div>

      <!-- ──────────────── TAB: EVIDENCIAS ──────────────── -->
      <div v-if="tab === 'evidencias'">

        <!-- Formulario nueva evidencia (solo no-Worker) -->
        <div v-if="!isWorkerRole" class="sub-card">
          <h3 class="sub-title">Agregar evidencia</h3>
          <EvidenceUploader :task-id="taskId" @uploaded="onEvidenceUploaded" />
        </div>

        <!-- Galería -->
        <div v-if="evidences.length === 0" class="empty-section">
          <i class="bi bi-camera-video-off"></i>
          <p>No hay evidencias registradas</p>
        </div>

        <div v-else class="ev-gallery">
          <!-- Imágenes -->
          <div v-if="evidences.some(e => e.file_type === 'image')" class="ev-section">
            <h4 class="ev-section-title"><i class="bi bi-image"></i> Imágenes</h4>
            <div class="img-grid">
              <div v-for="ev in evidences.filter(e => e.file_type === 'image')" :key="ev.id"
                class="img-thumb-wrap">
                <img :src="apiBase + ev.file_path" class="img-thumb"
                  @click="lightboxUrl = apiBase + ev.file_path" />
                <p v-if="ev.description" class="thumb-desc">{{ ev.description }}</p>
                <span class="thumb-date">{{ fmtDateTime(ev.created_at) }}</span>
                <button v-if="!isWorkerRole" class="btn-del" @click="deleteEvidence(ev)">
                  <i class="bi bi-trash"></i>
                </button>
              </div>
            </div>
          </div>
          <!-- Textos -->
          <div v-if="evidences.some(e => e.file_type === 'text')" class="ev-section">
            <h4 class="ev-section-title"><i class="bi bi-text-paragraph"></i> Notas</h4>
            <div class="text-list">
              <div v-for="ev in evidences.filter(e => e.file_type === 'text')" :key="ev.id"
                class="text-item">
                <div class="text-body">{{ ev.description }}</div>
                <div class="text-footer">
                  <span>{{ fmtDateTime(ev.created_at) }}</span>
                  <button v-if="!isWorkerRole" class="btn-del" @click="deleteEvidence(ev)">
                    <i class="bi bi-trash"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>
          <!-- Videos y Audios -->
          <div v-if="evidences.some(e => ['video','audio'].includes(e.file_type))" class="ev-section">
            <h4 class="ev-section-title"><i class="bi bi-play-circle"></i> Videos / Audios</h4>
            <div v-for="ev in evidences.filter(e => ['video','audio'].includes(e.file_type))"
              :key="ev.id" class="media-item">
              <video v-if="ev.file_type === 'video'" :src="apiBase + ev.file_path"
                controls class="media-player" />
              <audio v-else :src="apiBase + ev.file_path" controls class="media-player" />
              <p v-if="ev.description" class="media-desc">{{ ev.description }}</p>
              <button v-if="!isWorkerRole" class="btn-del" @click="deleteEvidence(ev)">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </div>
        </div>

        <!-- Lightbox -->
        <div v-if="lightboxUrl" class="lightbox" @click="lightboxUrl = ''">
          <img :src="lightboxUrl" class="lightbox-img" />
          <button class="lightbox-close"><i class="bi bi-x-lg"></i></button>
        </div>
      </div>

      <!-- ──────────────── TAB: MATERIALES ──────────────── -->
      <div v-if="tab === 'materiales'">
        <div v-if="!isWorkerRole" class="sub-card">
          <h3 class="sub-title">Registrar material / herramienta</h3>
          <div class="form-row4">
            <div class="fg col2">
              <label>Nombre *</label>
              <input v-model="matForm.name" class="form-control"
                placeholder="Ej: Cemento, Taladro..." />
            </div>
            <div class="fg">
              <label>Unidad</label>
              <select v-model="matForm.unit" class="form-select">
                <option value="">—</option>
                <option v-for="u in units" :key="u" :value="u">{{ u }}</option>
              </select>
            </div>
            <div class="fg">
              <label>Cantidad</label>
              <input v-model.number="matForm.quantity" type="number" min="0.01"
                step="0.01" class="form-control" placeholder="1" />
            </div>
            <div class="fg">
              <label>Costo unit. ($)</label>
              <input v-model.number="matForm.unit_cost" type="number" min="0"
                class="form-control" placeholder="0" />
            </div>
            <div class="fg">
              <label>Total</label>
              <div class="total-display">
                ${{ fmt(matForm.quantity * matForm.unit_cost) }}
              </div>
            </div>
          </div>
          <button class="btn btn-primary btn-sm mt-3" @click="addMaterial" :disabled="savingMat">
            <i v-if="savingMat" class="bi bi-arrow-repeat spin"></i>
            <i v-else class="bi bi-plus-lg"></i>
            {{ savingMat ? 'Guardando...' : 'Agregar material' }}
          </button>
        </div>

        <div v-if="materials.length === 0" class="empty-section">
          <i class="bi bi-box-seam"></i><p>No hay materiales registrados</p>
        </div>
        <div v-else class="sub-card p-0">
          <table class="data-table">
            <thead>
              <tr>
                <th>Material</th>
                <th class="text-center">Unidad</th>
                <th class="text-center">Cant.</th>
                <th class="text-right">C. Unit.</th>
                <th class="text-right">Total</th>
                <th v-if="!isWorkerRole" class="text-center">Acción</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in materials" :key="m.id">
                <td><strong>{{ m.name }}</strong></td>
                <td class="text-center text-muted">{{ m.unit || '—' }}</td>
                <td class="text-center">{{ m.quantity }}</td>
                <td class="text-right text-muted">${{ fmt(m.unit_cost) }}</td>
                <td class="text-right"><strong>${{ fmt(m.total_cost) }}</strong></td>
                <td v-if="!isWorkerRole" class="text-center">
                  <button class="btn btn-danger btn-sm" @click="delMaterial(m)">
                    <i class="bi bi-trash"></i>
                  </button>
                </td>
              </tr>
              <tr class="total-row">
                <td :colspan="isWorkerRole ? 4 : 5" class="text-right">
                  <strong>Total materiales:</strong>
                </td>
                <td class="text-right">
                  <strong class="total-value">${{ fmt(totalMaterials) }}</strong>
                </td>
                <td v-if="!isWorkerRole"></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ──────────────── TAB: GASTOS ──────────────── -->
      <div v-if="tab === 'gastos'">
        <div v-if="!isWorkerRole" class="sub-card">
          <h3 class="sub-title">Registrar gasto pagado</h3>
          <div class="form-row4">
            <div class="fg col2">
              <label>Concepto *</label>
              <input v-model="expForm.concept" class="form-control"
                placeholder="Ej: Compra de materiales, Transporte..." />
            </div>
            <div class="fg">
              <label>Monto ($) *</label>
              <input v-model.number="expForm.amount" type="number" min="0"
                class="form-control" placeholder="0" />
            </div>
            <div class="fg">
              <label>Fecha de pago</label>
              <input v-model="expForm.payment_date" type="date" class="form-control" />
            </div>
            <div class="fg">
              <label>N° Recibo</label>
              <input v-model="expForm.receipt_ref" class="form-control" placeholder="Opcional" />
            </div>
          </div>
          <button class="btn btn-primary btn-sm mt-3" @click="addExpense" :disabled="savingExp">
            <i v-if="savingExp" class="bi bi-arrow-repeat spin"></i>
            <i v-else class="bi bi-plus-lg"></i>
            {{ savingExp ? 'Guardando...' : 'Registrar gasto' }}
          </button>
        </div>

        <div v-if="expenses.length === 0" class="empty-section">
          <i class="bi bi-receipt-cutoff"></i><p>No hay gastos registrados</p>
        </div>
        <div v-else class="sub-card p-0">
          <table class="data-table">
            <thead>
              <tr>
                <th>Concepto</th>
                <th class="text-center">Fecha</th>
                <th class="text-center">N° Recibo</th>
                <th class="text-right">Monto</th>
                <th v-if="!isWorkerRole" class="text-center">Acción</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="e in expenses" :key="e.id">
                <td><strong>{{ e.concept }}</strong></td>
                <td class="text-center text-muted">{{ fmtDate(e.payment_date) }}</td>
                <td class="text-center text-muted">{{ e.receipt_ref || '—' }}</td>
                <td class="text-right"><strong>${{ fmt(e.amount) }}</strong></td>
                <td v-if="!isWorkerRole" class="text-center">
                  <button class="btn btn-danger btn-sm" @click="delExpense(e)">
                    <i class="bi bi-trash"></i>
                  </button>
                </td>
              </tr>
              <tr class="total-row">
                <td :colspan="isWorkerRole ? 3 : 4" class="text-right">
                  <strong>Total gastos:</strong>
                </td>
                <td class="text-right">
                  <strong class="total-value">${{ fmt(totalExpenses) }}</strong>
                </td>
                <td v-if="!isWorkerRole"></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import { validateForm } from "@/utils/validate"
import WorkersModal from "@/components/WorkersModal.vue"
import EvidenceUploader from "@/components/EvidenceUploader.vue"

const route  = useRoute()
const router = useRouter()
const taskId = route.params.taskId
const apiBase = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"

// ── Rol ─────────────────────────────────────────────────────
const userInfo    = JSON.parse(localStorage.getItem("user") || "{}")
const isWorkerRole = (userInfo.role || "").toLowerCase().includes("worker")

// ── Estado principal ─────────────────────────────────────────
const task      = ref(null)
const assets    = ref([])
const workers   = ref([])
const users     = ref([])
const statuses  = ref([])
const loading   = ref(true)
const saving    = ref(false)
const tab       = ref("evidencias")

const form = ref({})

// ── Evidencias ───────────────────────────────────────────────
const evidences   = ref([])
const lightboxUrl = ref("")

// ── Materiales y Gastos ──────────────────────────────────────
const materials = ref([])
const expenses  = ref([])
const savingMat = ref(false)
const savingExp = ref(false)
const units     = ["unidad","kg","g","litros","ml","m","m²","m³","rollo","caja","bolsa","par"]
const matForm = ref({ name: "", unit: "", quantity: 1, unit_cost: 0 })
const expForm = ref({ concept: "", amount: 0, payment_date: "", receipt_ref: "" })

const totalMaterials = computed(() => materials.value.reduce((s, m) => s + (m.total_cost || 0), 0))
const totalExpenses  = computed(() => expenses.value.reduce((s, e) => s + (e.amount || 0), 0))

// ── Helpers ──────────────────────────────────────────────────
const STATUS_CLASSES = {
  1: "badge-orange", 2: "badge-blue",      3: "badge-green",
  4: "badge-purple", 5: "badge-darkgreen", 6: "badge-red",
}
const STATUS_COLORS = {
  1: "#f97316", 2: "#3b82f6", 3: "#22c55e",
  4: "#7c3aed", 5: "#065f46", 6: "#ef4444",
}

const isOverdue = computed(() =>
  task.value?.due_date &&
  new Date(task.value.due_date) < new Date() &&
  ![5, 6].includes(task.value.status_id)
)

const progressColor = computed(() => {
  const p = form.value.progress || 0
  if (p === 100) return "#22c55e"
  if (p >= 60)   return "#3b82f6"
  if (p >= 30)   return "#f97316"
  return "#e2e8f0"
})

function statusClass(id) { return STATUS_CLASSES[id] || "badge-gray" }
function assetName(id)   { return assets.value.find(a => a.id === id)?.name || "—" }
function fmt(n)          { return Number(n || 0).toLocaleString("es-CO", { minimumFractionDigits: 0 }) }
function fmtDate(iso) {
  if (!iso) return ""
  return new Date(iso).toLocaleDateString("es-CO", { day:"2-digit", month:"short", year:"numeric" })
}
function fmtDateTime(iso) {
  if (!iso) return ""
  return new Date(iso).toLocaleString("es-CO", {
    day:"2-digit", month:"short", year:"numeric", hour:"2-digit", minute:"2-digit"
  })
}
function clearError(e) { e.target.classList.remove("field-invalid") }

// ── Carga principal ──────────────────────────────────────────
async function load() {
  loading.value = true
  try {
    const [taskRes, assetsRes, workersRes, usersRes, statusRes, evRes, matRes, expRes] =
      await Promise.all([
        api.get(`/tasks/${taskId}`),
        api.get("/tasks/assets-list"),
        api.get("/workers/"),
        api.get("/users/"),
        api.get("/task-status/"),
        api.get(`/task-evidence/${taskId}`),
        api.get(`/task-materials/${taskId}`),
        api.get(`/task-expenses/${taskId}`),
      ])
    task.value      = taskRes.data
    assets.value    = assetsRes.data
    workers.value   = workersRes.data
    users.value     = usersRes.data
    statuses.value  = statusRes.data
    evidences.value = evRes.data
    materials.value = matRes.data
    expenses.value  = expRes.data

    form.value = {
      title:              task.value.title,
      description:        task.value.description || "",
      asset_id:           task.value.asset_id,
      status_id:          task.value.status_id,
      assigned_to:        task.value.assigned_to,
      worker_id:          task.value.worker_id,
      start_date:         task.value.start_date?.split("T")[0] || "",
      due_date:           task.value.due_date?.split("T")[0] || "",
      budget_labor_cost:  task.value.budget_labor_cost || 0,
      progress:           task.value.progress || 0,
    }
  } catch {
    showToast("Error cargando la tarea", "error")
  } finally {
    loading.value = false
  }
}

// ── Recargar ejecutores tras cambios en WorkersModal ─────────
async function reloadWorkers() {
  const res = await api.get("/workers/")
  workers.value = res.data
}

// ── Guardar tarea (no-Worker) ────────────────────────────────
async function saveTask() {
  const check = validateForm([
    { value: form.value.title, selector: '[data-v="title"]', label: "Título" }
  ])
  if (!check.valid) { showToast(check.message, "warning"); return }

  saving.value = true
  try {
    const res = await api.put(`/tasks/${taskId}`, form.value)
    task.value = res.data
    showToast("Tarea actualizada", "success")
  } catch (e) {
    showToast(e.response?.data?.detail || "Error guardando", "error")
  } finally {
    saving.value = false
  }
}

// ── Eliminar tarea (no-Worker) ───────────────────────────────
async function handleDelete() {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar "${task.value.title}"?`,
    text:  "Esta acción no se puede deshacer.",
    icon:  "warning",
    showCancelButton:  true,
    confirmButtonText: "Sí, eliminar",
    cancelButtonText:  "Cancelar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/tasks/${taskId}`)
    showToast("Tarea eliminada", "success")
    router.back()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error eliminando", "error")
  }
}

// ── Evidencias ───────────────────────────────────────────────
async function onEvidenceUploaded() {
  const res = await api.get(`/task-evidence/${taskId}`)
  evidences.value = res.data
}

async function deleteEvidence(ev) {
  const { isConfirmed } = await window.Swal.fire({
    title: "¿Eliminar evidencia?", icon: "warning",
    showCancelButton: true, confirmButtonText: "Eliminar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  await api.delete(`/task-evidence/${ev.id}`)
  showToast("Evidencia eliminada", "success")
  const res = await api.get(`/task-evidence/${taskId}`)
  evidences.value = res.data
}

// ── Materiales CRUD ──────────────────────────────────────────
async function addMaterial() {
  if (!matForm.value.name.trim()) { showToast("El nombre es obligatorio", "warning"); return }
  savingMat.value = true
  try {
    await api.post(`/task-materials/${taskId}`, matForm.value)
    showToast("Material registrado", "success")
    matForm.value = { name: "", unit: "", quantity: 1, unit_cost: 0 }
    const res = await api.get(`/task-materials/${taskId}`)
    materials.value = res.data
  } catch (e) {
    showToast(e.response?.data?.detail || "Error guardando", "error")
  } finally {
    savingMat.value = false
  }
}

async function delMaterial(m) {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar "${m.name}"?`, icon: "warning",
    showCancelButton: true, confirmButtonText: "Eliminar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  await api.delete(`/task-materials/${m.id}`)
  showToast("Material eliminado", "success")
  const res = await api.get(`/task-materials/${taskId}`)
  materials.value = res.data
}

// ── Gastos CRUD ──────────────────────────────────────────────
async function addExpense() {
  if (!expForm.value.concept.trim()) { showToast("El concepto es obligatorio", "warning"); return }
  if (!expForm.value.amount || expForm.value.amount <= 0) {
    showToast("El monto debe ser mayor a 0", "warning"); return
  }
  savingExp.value = true
  try {
    await api.post(`/task-expenses/${taskId}`, expForm.value)
    showToast("Gasto registrado", "success")
    expForm.value = { concept: "", amount: 0, payment_date: "", receipt_ref: "" }
    const res = await api.get(`/task-expenses/${taskId}`)
    expenses.value = res.data
  } catch (e) {
    showToast(e.response?.data?.detail || "Error guardando", "error")
  } finally {
    savingExp.value = false
  }
}

async function delExpense(e) {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar "${e.concept}"?`, icon: "warning",
    showCancelButton: true, confirmButtonText: "Eliminar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  await api.delete(`/task-expenses/${e.id}`)
  showToast("Gasto eliminado", "success")
  const res = await api.get(`/task-expenses/${taskId}`)
  expenses.value = res.data
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1000px; }

/* HEADER */
.page-header  { display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:20px; gap:12px; flex-wrap:wrap; }
.header-left  { display:flex; align-items:flex-start; gap:12px; }
.btn-back     { background:#f1f5f9; border:none; border-radius:8px; padding:8px 12px; cursor:pointer; font-size:16px; color:#475569; flex-shrink:0; margin-top:4px; }
.btn-back:hover { background:#e2e8f0; }
.title-row    { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.page-title   { font-size:20px; font-weight:700; color:#1e293b; margin:0; }
.page-subtitle { font-size:13px; color:#64748b; margin:4px 0 0; }
.header-actions { display:flex; gap:8px; align-items:center; flex-shrink:0; }
.overdue-chip { font-size:11px; color:#ef4444; font-weight:700; display:flex; align-items:center; gap:3px; }

/* PROGRESS TOP */
.progress-top { display:flex; align-items:center; gap:10px; margin-bottom:16px; }
.progress-track-lg { flex:1; height:10px; background:#f1f5f9; border-radius:6px; overflow:hidden; }
.progress-fill-lg  { height:100%; border-radius:6px; transition:width 0.4s, background 0.4s; }
.progress-pct { font-size:14px; font-weight:700; color:#1e293b; min-width:40px; text-align:right; }

/* DETAIL CARD */
.detail-card { background:#fff; border-radius:14px; box-shadow:0 1px 6px rgba(0,0,0,0.08); padding:20px 24px; margin-bottom:20px; }
.form-grid   { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
.fg          { display:flex; flex-direction:column; gap:4px; }
.fg label    { font-size:13px; font-weight:600; color:#374151; }
.span2       { grid-column: span 2; }
.read-field  { font-size:14px; color:#1e293b; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:8px 12px; min-height:38px; display:flex; align-items:center; }
.read-text   { align-items:flex-start; min-height:60px; white-space:pre-wrap; }
.text-danger { color:#ef4444 !important; }
.border-danger { border-color:#ef4444 !important; }

/* TABS */
.tabs-bar { display:flex; gap:4px; margin-bottom:16px; border-bottom:2px solid #f1f5f9; }
.tab-btn  { padding:10px 18px; border:none; background:none; font-size:14px; font-weight:600;
  color:#94a3b8; cursor:pointer; border-bottom:2px solid transparent; margin-bottom:-2px;
  display:flex; align-items:center; gap:8px; transition:all 0.15s; }
.tab-btn:hover  { color:#3b82f6; }
.tab-btn.active { color:#3b82f6; border-bottom-color:#3b82f6; }
.tab-badge { font-size:11px; background:#e2e8f0; color:#475569; border-radius:10px; padding:1px 8px; }

/* SUB-CARDS */
.sub-card  { background:#fff; border-radius:14px; box-shadow:0 1px 6px rgba(0,0,0,0.08); padding:18px 20px; margin-bottom:16px; }
.sub-card.p-0 { padding:0; overflow:hidden; }
.sub-title { font-size:14px; font-weight:700; color:#475569; margin:0 0 14px; }
.mt-2 { margin-top:8px; }
.mt-3 { margin-top:12px; }

/* EMPTY */
.loading-center { padding:60px; text-align:center; color:#94a3b8; }
.empty-section  { padding:40px; text-align:center; color:#94a3b8; margin-bottom:16px; }
.empty-section .bi { font-size:32px; display:block; margin-bottom:8px; }

/* EVIDENCIAS */
.ev-gallery      { display:flex; flex-direction:column; gap:20px; }
.ev-section      { background:#fff; border-radius:14px; box-shadow:0 1px 6px rgba(0,0,0,0.08); padding:16px 20px; }
.ev-section-title { font-size:13px; font-weight:700; color:#475569; display:flex; align-items:center; gap:6px; margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid #f1f5f9; }
.img-grid        { display:grid; grid-template-columns:repeat(auto-fill, minmax(150px, 1fr)); gap:10px; }
.img-thumb-wrap  { position:relative; border-radius:10px; overflow:hidden; background:#f8fafc; }
.img-thumb       { width:100%; height:130px; object-fit:cover; cursor:zoom-in; display:block; transition:opacity 0.2s; }
.img-thumb:hover { opacity:0.88; }
.thumb-desc  { font-size:11px; color:#64748b; padding:4px 8px; margin:0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.thumb-date  { font-size:10px; color:#94a3b8; padding:0 8px 6px; display:block; }
.btn-del     { position:absolute; top:6px; right:6px; background:rgba(239,68,68,0.85); border:none; border-radius:6px; color:#fff; width:26px; height:26px; display:flex; align-items:center; justify-content:center; cursor:pointer; font-size:12px; opacity:0; transition:opacity 0.15s; }
.img-thumb-wrap:hover .btn-del { opacity:1; }
.text-list  { display:flex; flex-direction:column; gap:10px; }
.text-item  { background:#fffbeb; border:1px solid #fde68a; border-radius:10px; padding:14px; }
.text-body  { font-size:14px; color:#1e293b; line-height:1.6; white-space:pre-wrap; }
.text-footer { display:flex; justify-content:space-between; align-items:center; margin-top:8px; }
.text-footer span { font-size:11px; color:#94a3b8; }
.text-footer .btn-del { position:static; opacity:1; }
.media-item  { background:#f8fafc; border-radius:10px; overflow:hidden; margin-bottom:12px; display:flex; flex-direction:column; }
.media-player { width:100%; max-height:240px; background:#000; }
.media-desc  { padding:10px 14px; font-size:13px; color:#64748b; }

/* TYPE SELECTOR */
.type-selector { display:flex; gap:8px; flex-wrap:wrap; }
.type-btn { display:flex; align-items:center; gap:6px; padding:6px 14px; border:1px solid #e2e8f0; border-radius:20px; background:#f8fafc; font-size:13px; font-weight:500; cursor:pointer; transition:all 0.15s; }
.type-btn:hover  { border-color:#3b82f6; color:#3b82f6; }
.type-btn.active { background:#3b82f6; border-color:#3b82f6; color:#fff; }
.file-drop { display:flex; flex-direction:column; align-items:center; justify-content:center; gap:8px; padding:20px; border:2px dashed #cbd5e1; border-radius:10px; cursor:pointer; transition:border-color 0.15s; color:#94a3b8; background:#f8fafc; }
.file-drop .bi { font-size:24px; }
.file-drop:hover    { border-color:#3b82f6; color:#3b82f6; }
.file-drop.has-file { border-color:#22c55e; color:#16a34a; background:#f0fdf4; }
.img-preview { max-height:160px; border-radius:8px; object-fit:contain; max-width:100%; margin-top:8px; }

/* MATERIALES / GASTOS FORM */
.form-row4    { display:grid; grid-template-columns:1fr 1fr 1fr 1fr auto; gap:10px; align-items:end; }
.fg.col2      { grid-column:span 2; }
.total-display { height:38px; display:flex; align-items:center; font-size:15px; font-weight:700; color:#22c55e; background:#f0fdf4; border-radius:8px; padding:0 12px; border:1px solid #bbf7d0; }

/* TABLE */
.data-table  { width:100%; border-collapse:collapse; font-size:14px; }
.data-table th { background:#f8fafc; color:#475569; font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:0.4px; padding:11px 14px; border-bottom:1px solid #e2e8f0; }
.data-table td { padding:12px 14px; border-bottom:1px solid #f1f5f9; vertical-align:middle; }
.data-table tr:last-child td { border-bottom:none; }
.data-table tr:hover td      { background:#f8fafc; }
.total-row td  { background:#f0fdf4 !important; }
.total-value   { font-size:15px; color:#16a34a; }
.text-center   { text-align:center; }
.text-right    { text-align:right; }
.text-muted    { color:#94a3b8 !important; font-size:13px; }

/* LIGHTBOX */
.lightbox      { position:fixed; inset:0; background:rgba(0,0,0,0.9); display:flex; align-items:center; justify-content:center; z-index:2000; cursor:zoom-out; }
.lightbox-img  { max-width:92vw; max-height:92vh; object-fit:contain; border-radius:4px; }
.lightbox-close { position:absolute; top:16px; right:20px; background:none; border:none; color:#fff; font-size:24px; cursor:pointer; }

/* STATUS BADGES */
.status-badge    { font-size:11px; font-weight:700; padding:3px 10px; border-radius:20px; white-space:nowrap; }
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
  .form-grid   { grid-template-columns:1fr; }
  .span2       { grid-column:span 1; }
  .form-row4   { grid-template-columns:1fr 1fr; }
  .fg.col2     { grid-column:span 2; }
}

/* ── BOTONES FACTURA / RECIBO ── */
.billing-group {
  display: flex;
  gap: 6px;
  opacity: 0.55;
  cursor: not-allowed;
}
.btn-billing {
  display: flex; align-items: center; gap: 5px;
  padding: 5px 12px; border-radius: 8px;
  font-size: 12px; font-weight: 600;
  border: 1.5px solid; cursor: not-allowed;
  position: relative;
}
.btn-factura {
  background: #eff6ff; border-color: #3b82f6; color: #1d4ed8;
}
.btn-recibo {
  background: #f0fdf4; border-color: #22c55e; color: #15803d;
}
.soon-chip {
  font-size: 9px; font-weight: 800; letter-spacing: 0.5px;
  background: #3b82f6; color: #fff;
  padding: 1px 5px; border-radius: 6px; margin-left: 2px;
}
</style>
