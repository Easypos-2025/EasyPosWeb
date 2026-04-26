<template>
  <div class="page-wrap">

    <!-- ── HEADER ── -->
    <div class="page-header">
      <div class="page-header-left">
        <i class="bi bi-ticket-detailed page-icon"></i>
        <div>
          <h1 class="page-title">Tickets de Soporte</h1>
          <p class="page-sub">{{ roleLevel === 'sysadmin' ? 'Vista global · todos los asociados' : roleLevel === 'manager' ? 'Gestión de tickets de la empresa' : 'Mis solicitudes de soporte' }}</p>
        </div>
      </div>
      <button class="btn-primary" @click="openCreate">
        <i class="bi bi-plus-lg"></i> Nuevo Ticket
      </button>
    </div>

    <!-- ── KPI CHIPS ── -->
    <div class="kpi-row">
      <div class="kpi-chip kpi-open">
        <i class="bi bi-folder2-open"></i>
        <div><span class="kpi-num">{{ countByStatus('abierto') }}</span><span class="kpi-lbl">Abiertos</span></div>
      </div>
      <div class="kpi-chip kpi-process">
        <i class="bi bi-gear-wide-connected"></i>
        <div><span class="kpi-num">{{ countByStatus('en_proceso') }}</span><span class="kpi-lbl">En proceso</span></div>
      </div>
      <div class="kpi-chip kpi-done">
        <i class="bi bi-check2-circle"></i>
        <div><span class="kpi-num">{{ countByStatus('resuelto') }}</span><span class="kpi-lbl">Resueltos</span></div>
      </div>
      <div class="kpi-chip kpi-closed">
        <i class="bi bi-x-circle"></i>
        <div><span class="kpi-num">{{ countByStatus('cerrado') }}</span><span class="kpi-lbl">Cerrados</span></div>
      </div>
    </div>

    <!-- ── FILTROS ── -->
    <div class="filters-row">
      <div class="search-box">
        <i class="bi bi-search"></i>
        <input v-model="search" type="text" placeholder="Buscar por título..." />
      </div>

      <div class="filter-group">
        <label>Estado</label>
        <div class="tab-group">
          <button v-for="tab in statusTabs" :key="tab.value"
            class="tab-btn" :class="{ active: filterStatus === tab.value }"
            @click="filterStatus = tab.value">
            {{ tab.label }}
          </button>
        </div>
      </div>

      <div class="filter-group">
        <label>Prioridad</label>
        <div class="tab-group">
          <button v-for="tab in priorityTabs" :key="tab.value"
            class="tab-btn" :class="{ active: filterPriority === tab.value }"
            @click="filterPriority = tab.value">
            {{ tab.label }}
          </button>
        </div>
      </div>
    </div>

    <!-- ── LOADING ── -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>Cargando tickets...</span>
    </div>

    <!-- ── TABLA ── -->
    <div v-else-if="filtered.length" class="table-card">
      <table class="data-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Prioridad</th>
            <th>Título</th>
            <th v-if="roleLevel === 'sysadmin'">Empresa</th>
            <th v-if="roleLevel !== 'user'">Solicitante</th>
            <th>Estado</th>
            <th>Fecha</th>
            <th class="col-ev">Ev.</th>
            <th class="col-act">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in filtered" :key="t.id" @click="openDetail(t)" class="tr-click">
            <td class="td-id">#{{ String(t.id).padStart(4, '0') }}</td>
            <td>
              <span class="priority-badge" :class="`prio-${t.priority}`">
                <i :class="PRIORITY_ICONS[t.priority]"></i>
                {{ PRIORITY_LABELS[t.priority] }}
              </span>
            </td>
            <td class="td-title">{{ t.title }}</td>
            <td v-if="roleLevel === 'sysadmin'" class="td-company">{{ t.company_name }}</td>
            <td v-if="roleLevel !== 'user'" class="td-user">{{ t.user_name }}</td>
            <td>
              <span class="status-badge" :class="`st-${t.status}`">
                {{ STATUS_LABELS[t.status] }}
              </span>
            </td>
            <td class="td-date">{{ fmtDate(t.created_at) }}</td>
            <td class="td-ev">
              <span :class="{ 'ev-has': t.evidence_count > 0 }">
                <i class="bi bi-images"></i> {{ t.evidence_count }}
              </span>
            </td>
            <td class="td-actions" @click.stop>
              <button class="btn-tbl-edit"  @click="openEditDirect(t)" title="Editar"><i class="bi bi-pencil"></i></button>
              <button class="btn-tbl-del"   @click="handleDelete(t)"   title="Eliminar"><i class="bi bi-trash3"></i></button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ── EMPTY ── -->
    <div v-else class="empty-state">
      <i class="bi bi-inbox"></i>
      <p>{{ search || filterStatus !== 'all' || filterPriority !== 'all' ? 'Sin resultados para el filtro aplicado' : 'Aún no hay tickets registrados' }}</p>
      <button v-if="!search && filterStatus === 'all' && filterPriority === 'all'" class="btn-primary" @click="openCreate">
        Abrir primer ticket
      </button>
    </div>

    <!-- ══════════════════════════════════════════════
         MODAL CREAR / EDITAR
    ══════════════════════════════════════════════ -->
    <Teleport to="body">
      <div v-if="showFormModal" class="modal-overlay" @click.self="closeFormModal">
        <div class="modal-box">
          <div class="modal-header-bar">
            <h2>{{ editMode ? 'Editar Ticket' : 'Nuevo Ticket de Soporte' }}</h2>
            <button class="btn-close-x" @click="closeFormModal"><i class="bi bi-x-lg"></i></button>
          </div>

          <div class="modal-body">

            <div class="form-group" :class="{ 'has-error': errors.title }">
              <label>Título <span class="req">*</span></label>
              <input v-model="form.title" type="text" placeholder="Resumen del problema o solicitud" maxlength="200" />
              <span v-if="errors.title" class="error-msg">{{ errors.title }}</span>
            </div>

            <div class="form-row">
              <div class="form-group flex-1">
                <label>Prioridad</label>
                <div class="priority-selector">
                  <button
                    v-for="p in priorityOptions"
                    :key="p.value"
                    type="button"
                    class="prio-btn"
                    :class="[`prio-opt-${p.value}`, { active: form.priority === p.value }]"
                    @click="form.priority = p.value"
                  >
                    <i :class="p.icon"></i> {{ p.label }}
                  </button>
                </div>
              </div>
            </div>

            <div class="form-group" :class="{ 'has-error': errors.description }">
              <label>Descripción detallada <span class="req">*</span></label>
              <textarea v-model="form.description" rows="5"
                placeholder="Describe el problema con el mayor detalle posible: pasos para reproducirlo, mensajes de error, etc.">
              </textarea>
              <span v-if="errors.description" class="error-msg">{{ errors.description }}</span>
            </div>

          </div>

          <div class="modal-footer-bar">
            <button class="btn-secondary" @click="closeFormModal">Cancelar</button>
            <button class="btn-primary" :disabled="saving" @click="save">
              <span v-if="saving"><i class="bi bi-hourglass-split"></i> Guardando...</span>
              <span v-else><i class="bi bi-check-lg"></i> {{ editMode ? 'Actualizar' : 'Enviar Ticket' }}</span>
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ══════════════════════════════════════════════
         MODAL DETALLE + EVIDENCIAS
    ══════════════════════════════════════════════ -->
    <Teleport to="body">
      <div v-if="showDetail && activeTicket" class="modal-overlay" @click.self="closeDetail">
        <div class="modal-box modal-detail">

          <div class="modal-header-bar">
            <div class="detail-header-left">
              <div class="detail-id-row">
                <span class="ticket-num">#{{ String(activeTicket.id).padStart(4, '0') }}</span>
                <span class="status-badge" :class="`st-${activeTicket.status}`">{{ STATUS_LABELS[activeTicket.status] }}</span>
                <span class="priority-badge" :class="`prio-${activeTicket.priority}`">
                  <i :class="PRIORITY_ICONS[activeTicket.priority]"></i>
                  {{ PRIORITY_LABELS[activeTicket.priority] }}
                </span>
              </div>
              <h2>{{ activeTicket.title }}</h2>
            </div>
            <button class="btn-close-x" @click="closeDetail"><i class="bi bi-x-lg"></i></button>
          </div>

          <div class="modal-body detail-body">

            <div class="detail-meta">
              <span><i class="bi bi-person"></i> {{ activeTicket.user_name }}</span>
              <span v-if="roleLevel === 'sysadmin'"><i class="bi bi-building"></i> {{ activeTicket.company_name }}</span>
              <span><i class="bi bi-calendar3"></i> {{ fmtDate(activeTicket.created_at) }}</span>
            </div>

            <p class="detail-desc">{{ activeTicket.description }}</p>

            <!-- Cambio de estado (manager / sysadmin) -->
            <div v-if="roleLevel !== 'user'" class="status-change-section">
              <div class="section-label">
                <i class="bi bi-arrow-repeat"></i> Gestión del ticket
              </div>
              <div class="status-priority-row">
                <div class="mgmt-group">
                  <label>Estado</label>
                  <div class="status-btns">
                    <button v-for="st in statusOptions" :key="st.value"
                      class="status-opt-btn"
                      :class="[`sopt-${st.value}`, { active: activeTicket.status === st.value }]"
                      @click="changeField('status', st.value)"
                      :disabled="changingField">
                      <i :class="st.icon"></i> {{ st.label }}
                    </button>
                  </div>
                </div>
                <div class="mgmt-group">
                  <label>Prioridad</label>
                  <div class="status-btns">
                    <button v-for="p in priorityOptions" :key="p.value"
                      class="status-opt-btn"
                      :class="[`popt-${p.value}`, { active: activeTicket.priority === p.value }]"
                      @click="changeField('priority', p.value)"
                      :disabled="changingField">
                      <i :class="p.icon"></i> {{ p.label }}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Evidencias -->
            <div class="evidence-section">
              <div class="evidence-section-header">
                <h4><i class="bi bi-paperclip"></i> Evidencias adjuntas ({{ evidences.length }})</h4>
                <label class="btn-upload-ev" :class="{ loading: uploadingEv }">
                  <i v-if="uploadingEv" class="bi bi-hourglass-split"></i>
                  <i v-else class="bi bi-cloud-upload"></i>
                  <span>{{ uploadingEv ? 'Subiendo...' : 'Adjuntar' }}</span>
                  <input type="file" accept="image/*,video/mp4,video/quicktime,.pdf"
                    style="display:none" @change="uploadEvidence" :disabled="uploadingEv" />
                </label>
              </div>

              <div v-if="evidences.length" class="evidence-grid">
                <div v-for="ev in evidences" :key="ev.id" class="ev-item">
                  <img v-if="ev.file_type === 'image'" :src="apiBase + ev.file_url"
                    class="ev-thumb" @click="openLightbox(apiBase + ev.file_url)" alt="Evidencia" />
                  <div v-else-if="ev.file_type === 'video'" class="ev-video-thumb"
                    @click="openVideoModal(apiBase + ev.file_url)">
                    <i class="bi bi-play-circle-fill"></i><span>Video</span>
                  </div>
                  <div v-else class="ev-doc-thumb">
                    <i class="bi bi-file-earmark-text"></i>
                    <a :href="apiBase + ev.file_url" target="_blank">Ver</a>
                  </div>
                  <button class="btn-del-ev" @click.stop="deleteEvidence(ev)">
                    <i class="bi bi-trash3"></i>
                  </button>
                </div>
              </div>
              <p v-else class="no-evidence">Sin archivos adjuntos.</p>
            </div>

          </div>

          <div class="modal-footer-bar">
            <button class="btn-icon-sm" @click="openEditFromDetail">
              <i class="bi bi-pencil"></i> Editar
            </button>
            <button class="btn-danger-sm" @click="handleDelete(activeTicket)">
              <i class="bi bi-trash3"></i> Eliminar
            </button>
            <button class="btn-secondary" style="margin-left:auto" @click="closeDetail">Cerrar</button>
          </div>

        </div>
      </div>
    </Teleport>

    <!-- Lightbox imagen -->
    <Teleport to="body">
      <div v-if="lightboxUrl" class="lightbox" @click="lightboxUrl = null">
        <img :src="lightboxUrl" class="lightbox-img" @click.stop />
        <button class="lightbox-close" @click="lightboxUrl = null"><i class="bi bi-x-lg"></i></button>
      </div>
    </Teleport>

    <!-- Visor video -->
    <Teleport to="body">
      <div v-if="videoUrl" class="lightbox" @click="videoUrl = null">
        <video :src="videoUrl" class="lightbox-video" controls autoplay @click.stop></video>
        <button class="lightbox-close" @click="videoUrl = null"><i class="bi bi-x-lg"></i></button>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import { useCompanyStore } from "@/stores/companyStore"

const companyStore = useCompanyStore()
const apiBase      = import.meta.env.VITE_API_URL || ""

// ── Rol ─────────────────────────────────────────────
const storedUser = ref(null)
const roleLevel  = computed(() => {
  if (companyStore.isSystem) return "sysadmin"
  const role = storedUser.value?.role?.toLowerCase() || ""
  if (role.includes("admin") || role.includes("auditor")) return "manager"
  return "user"
})

// ── Data ────────────────────────────────────────────
const tickets       = ref([])
const loading       = ref(true)
const saving        = ref(false)
const search        = ref("")
const filterStatus  = ref("all")
const filterPriority = ref("all")

// ── Modales ─────────────────────────────────────────
const showFormModal  = ref(false)
const showDetail     = ref(false)
const editMode       = ref(false)
const activeTicket   = ref(null)
const evidences      = ref([])
const uploadingEv    = ref(false)
const changingField  = ref(false)
const lightboxUrl    = ref(null)
const videoUrl       = ref(null)
const errors         = ref({ title: "", description: "" })

const emptyForm = () => ({ id: null, title: "", description: "", priority: "media" })
const form      = ref(emptyForm())

// ── Constantes ──────────────────────────────────────
const STATUS_LABELS = {
  abierto:    "Abierto",
  en_proceso: "En proceso",
  resuelto:   "Resuelto",
  cerrado:    "Cerrado",
}

const PRIORITY_LABELS = { baja: "Baja", media: "Media", alta: "Alta", critica: "Crítica" }
const PRIORITY_ICONS  = {
  baja:    "bi bi-arrow-down-circle",
  media:   "bi bi-dash-circle",
  alta:    "bi bi-arrow-up-circle",
  critica: "bi bi-exclamation-circle-fill",
}

const statusTabs   = [
  { value: "all",        label: "Todos"      },
  { value: "abierto",    label: "Abiertos"   },
  { value: "en_proceso", label: "En proceso" },
  { value: "resuelto",   label: "Resueltos"  },
  { value: "cerrado",    label: "Cerrados"   },
]

const priorityTabs = [
  { value: "all",     label: "Todas"    },
  { value: "baja",    label: "Baja"     },
  { value: "media",   label: "Media"    },
  { value: "alta",    label: "Alta"     },
  { value: "critica", label: "Crítica"  },
]

const statusOptions = [
  { value: "abierto",    label: "Abierto",     icon: "bi bi-folder2-open"          },
  { value: "en_proceso", label: "En proceso",  icon: "bi bi-gear-wide-connected"   },
  { value: "resuelto",   label: "Resuelto",    icon: "bi bi-check2-circle"         },
  { value: "cerrado",    label: "Cerrado",     icon: "bi bi-x-circle"              },
]

const priorityOptions = [
  { value: "baja",    label: "Baja",    icon: "bi bi-arrow-down-circle"       },
  { value: "media",   label: "Media",   icon: "bi bi-dash-circle"             },
  { value: "alta",    label: "Alta",    icon: "bi bi-arrow-up-circle"         },
  { value: "critica", label: "Crítica", icon: "bi bi-exclamation-circle-fill" },
]

// ── Computed ────────────────────────────────────────
const filtered = computed(() =>
  tickets.value.filter(t => {
    const matchSearch   = !search.value ||
      t.title.toLowerCase().includes(search.value.toLowerCase())
    const matchStatus   = filterStatus.value   === "all" || t.status   === filterStatus.value
    const matchPriority = filterPriority.value === "all" || t.priority === filterPriority.value
    return matchSearch && matchStatus && matchPriority
  })
)

function countByStatus(status) {
  return tickets.value.filter(t => t.status === status).length
}

// ── Carga ───────────────────────────────────────────
async function load() {
  loading.value = true
  try {
    const res    = await api.get("/support-tickets")
    tickets.value = res.data
  } catch {
    showToast("Error cargando tickets", "error")
  } finally {
    loading.value = false
  }
}

// ── Crear / Editar ───────────────────────────────────
function openCreate() {
  form.value   = emptyForm()
  editMode.value  = false
  errors.value = { title: "", description: "" }
  showFormModal.value = true
}

function openEditDirect(t) {
  form.value   = { id: t.id, title: t.title, description: t.description, priority: t.priority }
  editMode.value  = true
  errors.value = { title: "", description: "" }
  showFormModal.value = true
}

function openEditFromDetail() {
  form.value   = { id: activeTicket.value.id, title: activeTicket.value.title, description: activeTicket.value.description, priority: activeTicket.value.priority }
  editMode.value  = true
  errors.value = { title: "", description: "" }
  showDetail.value    = false
  showFormModal.value = true
}

function closeFormModal() { showFormModal.value = false }

function validate() {
  errors.value = { title: "", description: "" }
  let ok = true
  if (!form.value.title.trim())       { errors.value.title       = "El título es obligatorio";       ok = false }
  if (!form.value.description.trim()) { errors.value.description = "La descripción es obligatoria";  ok = false }
  return ok
}

async function save() {
  if (!validate()) return
  saving.value = true
  try {
    const payload = { title: form.value.title, description: form.value.description, priority: form.value.priority }
    if (editMode.value) {
      await api.put(`/support-tickets/${form.value.id}`, payload)
      showToast("Ticket actualizado", "success")
    } else {
      await api.post("/support-tickets", payload)
      showToast("Ticket enviado correctamente", "success")
    }
    closeFormModal()
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error al guardar", "error")
  } finally {
    saving.value = false
  }
}

// ── Detalle ──────────────────────────────────────────
async function openDetail(t) {
  activeTicket.value = { ...t }
  evidences.value    = []
  showDetail.value   = true
  await loadEvidences(t.id)
}

function closeDetail() {
  showDetail.value  = false
  activeTicket.value = null
  evidences.value    = []
}

// ── Cambiar campo desde detalle ──────────────────────
async function changeField(field, value) {
  if (!activeTicket.value || changingField.value) return
  changingField.value = true
  try {
    const res = await api.put(`/support-tickets/${activeTicket.value.id}`, { [field]: value })
    activeTicket.value[field] = res.data[field]
    const idx = tickets.value.findIndex(t => t.id === activeTicket.value.id)
    if (idx !== -1) tickets.value[idx][field] = res.data[field]
    showToast("Actualizado", "success")
  } catch (e) {
    showToast(e.response?.data?.detail || "Error", "error")
  } finally {
    changingField.value = false
  }
}

// ── Eliminar ─────────────────────────────────────────
async function handleDelete(t) {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar ticket #${String(t.id).padStart(4, '0')}?`,
    text: "Se eliminarán también todas las evidencias adjuntas.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, eliminar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/support-tickets/${t.id}`)
    showToast("Ticket eliminado", "success")
    closeDetail()
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error al eliminar", "error")
  }
}

// ── Evidencias ───────────────────────────────────────
async function loadEvidences(ticketId) {
  try {
    const res    = await api.get(`/support-tickets/${ticketId}/evidence`)
    evidences.value = res.data
  } catch {}
}

async function uploadEvidence(e) {
  const file = e.target.files[0]
  if (!file || !activeTicket.value) return
  e.target.value  = ""
  uploadingEv.value = true
  const fd = new FormData()
  fd.append("file", file)
  try {
    await api.post(`/support-tickets/${activeTicket.value.id}/evidence`, fd, {
      headers: { "Content-Type": "multipart/form-data" }
    })
    await loadEvidences(activeTicket.value.id)
    const idx = tickets.value.findIndex(t => t.id === activeTicket.value.id)
    if (idx !== -1) tickets.value[idx].evidence_count = evidences.value.length
    showToast("Archivo adjuntado", "success")
  } catch (err) {
    showToast(err.response?.data?.detail || "Error al subir archivo", "error")
  } finally {
    uploadingEv.value = false
  }
}

async function deleteEvidence(ev) {
  const { isConfirmed } = await window.Swal.fire({
    title: "¿Eliminar este adjunto?", icon: "warning",
    showCancelButton: true, confirmButtonText: "Eliminar",
    cancelButtonText: "Cancelar", confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/support-tickets/evidence/${ev.id}`)
    await loadEvidences(activeTicket.value.id)
    const idx = tickets.value.findIndex(t => t.id === activeTicket.value.id)
    if (idx !== -1) tickets.value[idx].evidence_count = evidences.value.length
    showToast("Adjunto eliminado", "success")
  } catch { showToast("Error al eliminar adjunto", "error") }
}

function openLightbox(url) { lightboxUrl.value = url }
function openVideoModal(url) { videoUrl.value = url }

function fmtDate(iso) {
  if (!iso) return ""
  return new Date(iso).toLocaleDateString("es-CO", {
    day: "2-digit", month: "short", year: "numeric"
  })
}

onMounted(async () => {
  const stored = localStorage.getItem("user")
  if (stored) storedUser.value = JSON.parse(stored)
  await load()
})
</script>

<style scoped>

.page-wrap {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 100%;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.page-header-left { display: flex; align-items: center; gap: 14px; }

.page-icon { font-size: 32px; color: #6366f1; flex-shrink: 0; }

.page-title { font-size: 22px; font-weight: 700; margin: 0; color: var(--text-main, #1e293b); }
.page-sub   { font-size: 12px; color: var(--text-muted, #64748b); margin: 2px 0 0; }

/* ── KPI ── */
.kpi-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.kpi-chip {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 18px;
  border-radius: 12px;
  border: 1px solid var(--border, #e2e8f0);
  background: var(--card-bg, #fff);
  flex: 1;
  min-width: 120px;
}

.kpi-chip .bi { font-size: 24px; }
.kpi-num { display: block; font-size: 22px; font-weight: 800; line-height: 1; }
.kpi-lbl { display: block; font-size: 11px; color: var(--text-muted, #64748b); margin-top: 2px; }

.kpi-open    .bi { color: #3b82f6; }
.kpi-process .bi { color: #f59e0b; }
.kpi-done    .bi { color: #22c55e; }
.kpi-closed  .bi { color: #94a3b8; }

/* ── FILTROS ── */
.filters-row {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  flex-wrap: wrap;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--card-bg, #fff);
  border: 1px solid var(--border, #e2e8f0);
  border-radius: 8px;
  padding: 7px 14px;
  min-width: 220px;
}
.search-box input { border: none; outline: none; background: transparent; font-size: 13px; color: var(--text-main, #1e293b); width: 100%; }
.search-box .bi   { opacity: 0.4; font-size: 14px; }

.filter-group { display: flex; flex-direction: column; gap: 4px; }
.filter-group label { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-muted, #94a3b8); }

.tab-group { display: flex; gap: 4px; flex-wrap: wrap; }
.tab-btn {
  padding: 5px 12px;
  border-radius: 16px;
  border: 1px solid var(--border, #e2e8f0);
  background: var(--card-bg, #fff);
  font-size: 12px;
  cursor: pointer;
  color: var(--text-muted, #64748b);
  transition: all 0.15s;
}
.tab-btn.active { background: var(--primary, #3b82f6); border-color: var(--primary, #3b82f6); color: #fff; }

/* ── TABLA ── */
.table-card {
  background: var(--card-bg, #fff);
  border-radius: 12px;
  border: 1px solid var(--border, #e2e8f0);
  overflow: hidden;
}

.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }

.data-table th {
  padding: 11px 14px;
  text-align: left;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  color: var(--text-muted, #94a3b8);
  background: var(--input-bg, #f8fafc);
  border-bottom: 1px solid var(--border, #e2e8f0);
}

.data-table td { padding: 11px 14px; border-bottom: 1px solid var(--border, #f1f5f9); color: var(--text-main, #374151); }
.data-table tbody tr:last-child td { border-bottom: none; }

.tr-click { cursor: pointer; transition: background 0.12s; }
.tr-click:hover { background: var(--input-bg, #f8fafc); }

.td-id     { font-weight: 700; font-size: 12px; color: var(--text-muted, #94a3b8); white-space: nowrap; }
.td-title  { max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500; }
.td-company{ font-size: 12px; color: var(--text-muted, #64748b); white-space: nowrap; }
.td-user   { font-size: 12px; color: var(--text-muted, #64748b); white-space: nowrap; }
.td-date   { font-size: 11.5px; color: var(--text-muted, #94a3b8); white-space: nowrap; }
.td-ev     { text-align: center; font-size: 12px; color: var(--text-muted, #94a3b8); }
.ev-has    { color: #6366f1; font-weight: 700; }
.col-ev    { width: 50px; text-align: center; }
.col-act   { width: 80px; text-align: center; }
.td-actions { text-align: center; display: flex; gap: 4px; justify-content: center; }

.btn-tbl-edit, .btn-tbl-del {
  padding: 4px 8px;
  border-radius: 6px;
  border: none;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-tbl-edit { background: rgba(99,102,241,0.1); color: #6366f1; }
.btn-tbl-edit:hover { background: rgba(99,102,241,0.2); }
.btn-tbl-del  { background: rgba(239,68,68,0.1); color: #ef4444; }
.btn-tbl-del:hover  { background: rgba(239,68,68,0.2); }

/* Priority badges */
.priority-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 20px;
  white-space: nowrap;
}
.prio-baja    { background: rgba(148,163,184,0.15); color: #64748b; }
.prio-media   { background: rgba(59,130,246,0.12);  color: #2563eb; }
.prio-alta    { background: rgba(245,158,11,0.15);  color: #d97706; }
.prio-critica { background: rgba(239,68,68,0.15);   color: #dc2626; }

/* Status badges */
.status-badge {
  display: inline-flex;
  align-items: center;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: 20px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  white-space: nowrap;
}
.st-abierto    { background: rgba(59,130,246,0.12);  color: #2563eb; }
.st-en_proceso { background: rgba(245,158,11,0.15);  color: #d97706; }
.st-resuelto   { background: rgba(34,197,94,0.15);   color: #16a34a; }
.st-cerrado    { background: rgba(148,163,184,0.15); color: #64748b; }

/* ── EMPTY / LOADING ── */
.loading-state { display: flex; align-items: center; gap: 12px; padding: 48px; justify-content: center; color: var(--text-muted, #64748b); }
.spinner { width: 24px; height: 24px; border: 3px solid rgba(0,0,0,0.1); border-top-color: var(--primary, #3b82f6); border-radius: 50%; animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.empty-state { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 64px; color: var(--text-muted, #94a3b8); }
.empty-state .bi { font-size: 48px; opacity: 0.3; }
.empty-state p   { font-size: 14px; margin: 0; }

/* ── MODALES ── */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.55); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 16px; }

.modal-box {
  background: var(--card-bg, #fff);
  border-radius: 14px;
  width: 100%;
  max-width: 580px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  overflow: hidden;
}
.modal-detail { max-width: 800px; }

.modal-header-bar { display: flex; align-items: flex-start; justify-content: space-between; padding: 18px 20px; border-bottom: 1px solid var(--border, #e2e8f0); gap: 12px; }
.modal-header-bar h2 { font-size: 17px; font-weight: 700; margin: 0; color: var(--text-main, #1e293b); }

.detail-header-left { display: flex; flex-direction: column; gap: 7px; }
.detail-id-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.ticket-num { font-size: 13px; font-weight: 800; color: var(--text-muted, #94a3b8); }

.modal-body { padding: 20px; overflow-y: auto; flex: 1; display: flex; flex-direction: column; gap: 16px; }
.modal-footer-bar { display: flex; align-items: center; gap: 10px; padding: 14px 20px; border-top: 1px solid var(--border, #e2e8f0); }

/* Formulario */
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 13px; font-weight: 600; color: var(--text-main, #374151); }
.form-row { display: flex; gap: 12px; }
.flex-1 { flex: 1; }
.req { color: #ef4444; }

.form-group input,
.form-group textarea {
  border: 1px solid var(--border, #d1d5db);
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 13px;
  color: var(--text-main, #1e293b);
  background: var(--input-bg, #f9fafb);
  outline: none;
  resize: vertical;
  font-family: inherit;
  transition: border-color 0.15s;
}
.form-group input:focus,
.form-group textarea:focus { border-color: var(--primary, #3b82f6); background: #fff; }
.has-error input, .has-error textarea { border-color: #ef4444; }
.error-msg { font-size: 11px; color: #ef4444; }

.priority-selector { display: flex; gap: 6px; flex-wrap: wrap; }

.prio-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  border-radius: 20px;
  border: 1px solid var(--border, #e2e8f0);
  background: var(--card-bg, #fff);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
  color: var(--text-muted, #64748b);
}
.prio-opt-baja.active    { background: rgba(148,163,184,0.2); border-color: #94a3b8; color: #64748b; }
.prio-opt-media.active   { background: rgba(59,130,246,0.15);  border-color: #3b82f6; color: #2563eb; }
.prio-opt-alta.active    { background: rgba(245,158,11,0.15);  border-color: #f59e0b; color: #d97706; }
.prio-opt-critica.active { background: rgba(239,68,68,0.15);   border-color: #ef4444; color: #dc2626; }

/* Detalle */
.detail-meta { display: flex; gap: 16px; font-size: 12px; color: var(--text-muted, #64748b); flex-wrap: wrap; }
.detail-meta .bi { margin-right: 3px; }
.detail-desc { font-size: 14px; color: var(--text-main, #374151); line-height: 1.6; margin: 0; white-space: pre-wrap; }

/* Gestión de ticket */
.status-change-section {
  background: var(--input-bg, #f8fafc);
  border: 1px solid var(--border, #e2e8f0);
  border-radius: 10px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-label { font-size: 12px; font-weight: 700; color: var(--text-muted, #64748b); display: flex; align-items: center; gap: 6px; }

.status-priority-row { display: flex; gap: 20px; flex-wrap: wrap; }
.mgmt-group { display: flex; flex-direction: column; gap: 8px; flex: 1; min-width: 200px; }
.mgmt-group label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.4px; color: var(--text-muted, #94a3b8); }

.status-btns { display: flex; gap: 5px; flex-wrap: wrap; }

.status-opt-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  border-radius: 16px;
  border: 1px solid var(--border, #e2e8f0);
  background: var(--card-bg, #fff);
  font-size: 11.5px;
  cursor: pointer;
  color: var(--text-muted, #64748b);
  transition: all 0.15s;
}
.sopt-abierto.active    { background: rgba(59,130,246,0.15);  border-color: #3b82f6; color: #2563eb; }
.sopt-en_proceso.active { background: rgba(245,158,11,0.15);  border-color: #f59e0b; color: #d97706; }
.sopt-resuelto.active   { background: rgba(34,197,94,0.15);   border-color: #22c55e; color: #16a34a; }
.sopt-cerrado.active    { background: rgba(148,163,184,0.2);  border-color: #94a3b8; color: #64748b; }

.popt-baja.active    { background: rgba(148,163,184,0.2); border-color: #94a3b8; color: #64748b; }
.popt-media.active   { background: rgba(59,130,246,0.15);  border-color: #3b82f6; color: #2563eb; }
.popt-alta.active    { background: rgba(245,158,11,0.15);  border-color: #f59e0b; color: #d97706; }
.popt-critica.active { background: rgba(239,68,68,0.15);   border-color: #ef4444; color: #dc2626; }

/* Evidencias */
.evidence-section { display: flex; flex-direction: column; gap: 12px; }
.evidence-section-header { display: flex; align-items: center; justify-content: space-between; }
.evidence-section-header h4 { font-size: 14px; font-weight: 600; margin: 0; color: var(--text-main, #1e293b); display: flex; align-items: center; gap: 7px; }

.btn-upload-ev { display: flex; align-items: center; gap: 6px; padding: 6px 14px; border-radius: 8px; background: #6366f1; color: #fff; font-size: 12px; font-weight: 600; cursor: pointer; transition: background 0.15s; }
.btn-upload-ev:hover { background: #4f46e5; }
.btn-upload-ev.loading { background: #94a3b8; cursor: default; }

.evidence-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); gap: 10px; }
.ev-item { position: relative; border-radius: 8px; overflow: hidden; background: var(--input-bg, #f1f5f9); aspect-ratio: 1; }
.ev-thumb { width: 100%; height: 100%; object-fit: cover; cursor: pointer; transition: opacity 0.15s; }
.ev-thumb:hover { opacity: 0.85; }
.ev-video-thumb, .ev-doc-thumb { width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px; font-size: 11px; cursor: pointer; color: var(--text-muted, #64748b); }
.ev-video-thumb .bi { font-size: 28px; color: #6366f1; }
.ev-doc-thumb   .bi { font-size: 28px; color: #6366f1; }
.btn-del-ev { position: absolute; top: 4px; right: 4px; background: rgba(239,68,68,0.9); color: #fff; border: none; border-radius: 6px; padding: 3px 6px; font-size: 11px; cursor: pointer; opacity: 0; transition: opacity 0.15s; }
.ev-item:hover .btn-del-ev { opacity: 1; }
.no-evidence { font-size: 12px; color: var(--text-muted, #94a3b8); text-align: center; padding: 20px; margin: 0; }

/* Botones */
.btn-primary { display: flex; align-items: center; gap: 6px; padding: 9px 18px; background: #6366f1; color: #fff; border: none; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; transition: background 0.15s; }
.btn-primary:hover { background: #4f46e5; }
.btn-primary:disabled { background: #94a3b8; cursor: default; }

.btn-secondary { padding: 9px 18px; background: var(--input-bg, #f1f5f9); border: 1px solid var(--border, #e2e8f0); border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; color: var(--text-main, #374151); transition: background 0.15s; }
.btn-secondary:hover { background: #e2e8f0; }

.btn-close-x { background: none; border: none; font-size: 16px; cursor: pointer; color: var(--text-muted, #94a3b8); padding: 4px; flex-shrink: 0; transition: color 0.15s; }
.btn-close-x:hover { color: #ef4444; }

.btn-icon-sm { display: flex; align-items: center; gap: 5px; padding: 7px 14px; background: none; border: 1px solid var(--border, #e2e8f0); border-radius: 7px; font-size: 12px; cursor: pointer; color: var(--text-main, #374151); transition: background 0.15s; }
.btn-icon-sm:hover { background: var(--input-bg, #f1f5f9); }

.btn-danger-sm { display: flex; align-items: center; gap: 5px; padding: 7px 14px; background: none; border: 1px solid #fca5a5; border-radius: 7px; font-size: 12px; cursor: pointer; color: #ef4444; transition: background 0.15s; }
.btn-danger-sm:hover { background: rgba(239,68,68,0.08); }

/* Lightbox */
.lightbox { position: fixed; inset: 0; background: rgba(0,0,0,0.92); display: flex; align-items: center; justify-content: center; z-index: 2000; }
.lightbox-img   { max-width: 90vw; max-height: 90vh; border-radius: 8px; object-fit: contain; }
.lightbox-video { max-width: 90vw; max-height: 90vh; border-radius: 8px; }
.lightbox-close { position: absolute; top: 16px; right: 16px; background: rgba(255,255,255,0.1); border: none; color: #fff; font-size: 20px; border-radius: 8px; padding: 8px 10px; cursor: pointer; }
.lightbox-close:hover { background: rgba(255,255,255,0.2); }

/* ── RESPONSIVE ── */
@media (max-width: 768px) {
  .page-wrap { padding: 14px; gap: 14px; }
  .kpi-row   { gap: 8px; }
  .kpi-chip  { padding: 10px 14px; }
  .data-table .td-company, .data-table .td-user { display: none; }
  .modal-box { max-height: 95vh; }
  .status-priority-row { flex-direction: column; }
}
</style>
