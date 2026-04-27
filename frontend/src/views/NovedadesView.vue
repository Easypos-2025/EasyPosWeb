<template>
  <div class="page-wrap">

    <!-- ── HEADER ── -->
    <div class="page-header">
      <div class="page-header-left">
        <i class="bi bi-exclamation-triangle page-icon"></i>
        <div>
          <h1 class="page-title">Registro de Novedades</h1>
          <p class="page-sub">{{ canManageAll ? 'Vista de gestión · todas las novedades de la empresa' : 'Mis novedades reportadas' }}</p>
        </div>
      </div>
      <button class="btn-primary" @click="openCreate">
        <i class="bi bi-plus-lg"></i> Nueva Novedad
      </button>
    </div>

    <!-- ── FILTROS ── -->
    <div class="filters-row">
      <div class="search-box">
        <i class="bi bi-search"></i>
        <input v-model="search" type="text" placeholder="Buscar por título..." />
      </div>

      <!-- Filtro por usuario (solo SYSADMIN / Admin) -->
      <select v-if="canManageAll" v-model="filterUserId" class="filter-select" @change="applyFilters">
        <option :value="null">Todos los usuarios</option>
        <option v-for="u in usersList" :key="u.id" :value="u.id">{{ u.nombre }}</option>
      </select>

      <!-- Filtros de fecha (todos los roles) -->
      <div class="date-filters">
        <input v-model="filterDateFrom" type="date" class="filter-date" title="Desde" @change="applyFilters" />
        <span class="date-sep">–</span>
        <input v-model="filterDateTo" type="date" class="filter-date" title="Hasta" @change="applyFilters" />
        <button
          v-if="filterDateFrom || filterDateTo || filterUserId"
          class="btn-clear-filter"
          @click="clearFilters"
          title="Limpiar filtros de fecha"
        >
          <i class="bi bi-x-circle"></i>
        </button>
      </div>

      <div class="status-tabs">
        <button
          v-for="tab in statusTabs"
          :key="tab.value"
          class="tab-btn"
          :class="{ active: filterStatus === tab.value }"
          @click="filterStatus = tab.value"
        >
          <span class="tab-dot" :class="`dot-${tab.value}`"></span>
          {{ tab.label }}
          <span class="tab-count">{{ countByStatus(tab.value) }}</span>
        </button>
      </div>
    </div>

    <!-- ── LOADING ── -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>Cargando novedades...</span>
    </div>

    <!-- ── CARDS GRID ── -->
    <div v-else-if="filtered.length" class="cards-grid">
      <div
        v-for="n in filtered"
        :key="n.id"
        class="novelty-card"
        :class="`card-${n.status}`"
        @click="openDetail(n)"
      >
        <div class="card-top">
          <span class="status-badge" :class="`badge-${n.status}`">
            {{ STATUS_LABELS[n.status] }}
          </span>
          <span class="card-date">{{ fmtDate(n.created_at) }}</span>
        </div>

        <h3 class="card-title">{{ n.title }}</h3>
        <p class="card-desc">{{ n.description }}</p>

        <div class="card-footer">
          <span class="card-author">
            <i class="bi bi-person"></i> {{ n.user_name }}
          </span>
          <span class="card-evid" :class="{ 'has-evid': n.evidence_count > 0 }">
            <i class="bi bi-images"></i> {{ n.evidence_count }}
          </span>
        </div>
      </div>
    </div>

    <!-- ── EMPTY ── -->
    <div v-else class="empty-state">
      <i class="bi bi-inbox"></i>
      <p>{{ search || filterStatus !== 'all' ? 'Sin resultados para el filtro aplicado' : 'Aún no hay novedades registradas' }}</p>
      <button v-if="!search && filterStatus === 'all'" class="btn-primary" @click="openCreate">
        Registrar primera novedad
      </button>
    </div>

    <!-- ══════════════════════════════════════════════
         MODAL CREAR / EDITAR
    ══════════════════════════════════════════════ -->
    <Teleport to="body">
      <div v-if="showFormModal" class="modal-overlay" @click.self="closeFormModal">
        <div class="modal-box">
          <div class="modal-header-bar">
            <h2>{{ editMode ? 'Editar Novedad' : 'Nueva Novedad' }}</h2>
            <button class="btn-close-x" @click="closeFormModal"><i class="bi bi-x-lg"></i></button>
          </div>

          <div class="modal-body">
            <div class="form-group" :class="{ 'has-error': errors.title }">
              <label>Título <span class="req">*</span></label>
              <input v-model="form.title" type="text" placeholder="Describe brevemente la novedad" maxlength="200" />
              <span v-if="errors.title" class="error-msg">{{ errors.title }}</span>
            </div>

            <div class="form-group" :class="{ 'has-error': errors.description }">
              <label>Descripción detallada <span class="req">*</span></label>
              <textarea v-model="form.description" rows="5" placeholder="Explica con detalle la situación encontrada..."></textarea>
              <span v-if="errors.description" class="error-msg">{{ errors.description }}</span>
            </div>
          </div>

          <div class="modal-footer-bar">
            <button class="btn-secondary" @click="closeFormModal">Cancelar</button>
            <button class="btn-primary" :disabled="saving" @click="save">
              <span v-if="saving"><i class="bi bi-hourglass-split"></i> Guardando...</span>
              <span v-else><i class="bi bi-check-lg"></i> {{ editMode ? 'Actualizar' : 'Registrar' }}</span>
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ══════════════════════════════════════════════
         MODAL DETALLE + EVIDENCIAS
    ══════════════════════════════════════════════ -->
    <Teleport to="body">
      <div v-if="showDetail && activeNovelty" class="modal-overlay" @click.self="closeDetail">
        <div class="modal-box modal-detail">

          <div class="modal-header-bar">
            <div class="detail-header-left">
              <span class="status-badge" :class="`badge-${activeNovelty.status}`">
                {{ STATUS_LABELS[activeNovelty.status] }}
              </span>
              <h2>{{ activeNovelty.title }}</h2>
            </div>
            <button class="btn-close-x" @click="closeDetail"><i class="bi bi-x-lg"></i></button>
          </div>

          <div class="modal-body detail-body">

            <!-- Info -->
            <div class="detail-meta">
              <span><i class="bi bi-person"></i> {{ activeNovelty.user_name }}</span>
              <span><i class="bi bi-calendar3"></i> {{ fmtDate(activeNovelty.created_at) }}</span>
            </div>

            <p class="detail-desc">{{ activeNovelty.description }}</p>

            <!-- Cambio de estado (solo ADMIN / AUDITOR) -->
            <div v-if="canManageAll" class="status-change-row">
              <label>Cambiar estado:</label>
              <div class="status-btns">
                <button
                  v-for="st in statusOptions"
                  :key="st.value"
                  class="status-opt-btn"
                  :class="[`opt-${st.value}`, { active: activeNovelty.status === st.value }]"
                  @click="changeStatus(st.value)"
                  :disabled="changingStatus"
                >
                  <i :class="st.icon"></i> {{ st.label }}
                </button>
              </div>
            </div>

            <!-- Evidencias -->
            <div class="evidence-section">
              <div class="evidence-section-header">
                <h4><i class="bi bi-images"></i> Evidencias ({{ evidences.length }})</h4>
                <ImageCropperUpload
                  :novelty-id="activeNovelty.id"
                  @uploaded="onEvidenceUploaded"
                />
              </div>

              <!-- Grid de evidencias -->
              <div v-if="evidences.length" class="evidence-grid">
                <div
                  v-for="ev in evidences"
                  :key="ev.id"
                  class="ev-item"
                >
                  <img
                    :src="apiBase + ev.file_url"
                    class="ev-thumb"
                    @click="openLightbox(apiBase + ev.file_url)"
                    alt="Evidencia"
                  />
                  <button class="btn-del-ev" @click.stop="deleteEvidence(ev)" title="Eliminar evidencia">
                    <i class="bi bi-trash3"></i>
                  </button>
                </div>
              </div>
              <div v-else class="no-evidence">
                <i class="bi bi-camera"></i>
                <p>Sin evidencias aún — presiona <strong>Foto</strong> para adjuntar imágenes</p>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="modal-footer-bar">
            <button class="btn-icon-sm" title="Editar novedad" @click="openEditFromDetail">
              <i class="bi bi-pencil"></i> Editar
            </button>
            <button class="btn-danger-sm" @click="handleDelete(activeNovelty)">
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


  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import { useCompanyStore } from "@/stores/companyStore"
import ImageCropperUpload from "@/components/ImageCropperUpload.vue"

const companyStore = useCompanyStore()
const apiBase      = import.meta.env.VITE_API_URL || ""

// ── Permisos ────────────────────────────────────────
const storedUser    = ref(null)
const canManageAll  = computed(() => {
  if (companyStore.isSystem) return true
  const role = storedUser.value?.role?.toLowerCase() || ""
  return role.includes("admin") || role.includes("auditor")
})

// ── Data ────────────────────────────────────────────
const novelties      = ref([])
const loading        = ref(true)
const saving         = ref(false)
const search         = ref("")
const filterStatus   = ref("all")
const filterUserId   = ref(null)   // solo SYSADMIN/Admin
const filterDateFrom = ref("")
const filterDateTo   = ref("")
const usersList      = ref([])     // para select de usuario (SYSADMIN)

// ── Modales ─────────────────────────────────────────
const showFormModal  = ref(false)
const showDetail     = ref(false)
const editMode       = ref(false)
const activeNovelty  = ref(null)
const evidences      = ref([])
const changingStatus = ref(false)
const lightboxUrl    = ref(null)

const errors = ref({ title: "", description: "" })

const emptyForm = () => ({ id: null, title: "", description: "" })
const form      = ref(emptyForm())

// ── Constantes ──────────────────────────────────────
const STATUS_LABELS = {
  all:       "Todas",
  pendiente: "Pendiente",
  revisada:  "Revisada",
  resuelta:  "Resuelta",
}

const statusTabs = [
  { value: "all",       label: "Todas"     },
  { value: "pendiente", label: "Pendiente" },
  { value: "revisada",  label: "Revisada"  },
  { value: "resuelta",  label: "Resuelta"  },
]

const statusOptions = [
  { value: "pendiente", label: "Pendiente", icon: "bi bi-hourglass"         },
  { value: "revisada",  label: "Revisada",  icon: "bi bi-eye"               },
  { value: "resuelta",  label: "Resuelta",  icon: "bi bi-check-circle-fill" },
]

// ── Computed ────────────────────────────────────────
const filtered = computed(() => {
  return novelties.value.filter(n => {
    const matchSearch = !search.value ||
      n.title.toLowerCase().includes(search.value.toLowerCase()) ||
      n.description.toLowerCase().includes(search.value.toLowerCase())
    const matchStatus = filterStatus.value === "all" || n.status === filterStatus.value
    return matchSearch && matchStatus
  })
})

function countByStatus(status) {
  if (status === "all") return novelties.value.length
  return novelties.value.filter(n => n.status === status).length
}

// ── Carga ───────────────────────────────────────────
async function load() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (filterUserId.value)   params.append("filter_user_id", filterUserId.value)
    if (filterDateFrom.value) params.append("date_from", filterDateFrom.value)
    if (filterDateTo.value)   params.append("date_to", filterDateTo.value)
    const res = await api.get(`/novelties?${params.toString()}`)
    novelties.value = res.data
  } catch {
    showToast("Error cargando novedades", "error")
  } finally {
    loading.value = false
  }
}

async function loadUsersList() {
  try {
    const res = await api.get("/novelties/users-list")
    usersList.value = Array.isArray(res.data) ? res.data : []
  } catch {
    usersList.value = []
  }
}

function applyFilters() { load() }
function clearFilters() {
  filterUserId.value   = null
  filterDateFrom.value = ""
  filterDateTo.value   = ""
  load()
}

// ── Formulario crear/editar ──────────────────────────
function openCreate() {
  form.value   = emptyForm()
  editMode.value  = false
  errors.value = { title: "", description: "" }
  showFormModal.value = true
}

function openEditFromDetail() {
  form.value   = { id: activeNovelty.value.id, title: activeNovelty.value.title, description: activeNovelty.value.description }
  editMode.value  = true
  errors.value = { title: "", description: "" }
  showDetail.value    = false
  showFormModal.value = true
}

function closeFormModal() {
  showFormModal.value = false
}

function validate() {
  errors.value = { title: "", description: "" }
  let ok = true
  if (!form.value.title.trim()) {
    errors.value.title = "El título es obligatorio"
    ok = false
  }
  if (!form.value.description.trim()) {
    errors.value.description = "La descripción es obligatoria"
    ok = false
  }
  return ok
}

async function save() {
  if (!validate()) return
  saving.value = true
  try {
    if (editMode.value) {
      await api.put(`/novelties/${form.value.id}`, { title: form.value.title, description: form.value.description })
      showToast("Novedad actualizada", "success")
    } else {
      const res = await api.post("/novelties", { title: form.value.title, description: form.value.description })
      closeFormModal()
      await load()
      // Abrir detalle automáticamente para que el usuario pueda agregar evidencias de inmediato
      await openDetail(res.data)
      showToast("Novedad registrada — agrega las evidencias fotográficas", "success")
      return
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
async function openDetail(n) {
  activeNovelty.value = { ...n }
  evidences.value     = []
  showDetail.value    = true
  await loadEvidences(n.id)
}

function closeDetail() {
  showDetail.value = false
  activeNovelty.value = null
  evidences.value     = []
}

// ── Cambiar estado ───────────────────────────────────
async function changeStatus(status) {
  if (!activeNovelty.value || changingStatus.value) return
  changingStatus.value = true
  try {
    const res = await api.put(`/novelties/${activeNovelty.value.id}`, { status })
    activeNovelty.value.status = res.data.status
    const idx = novelties.value.findIndex(n => n.id === activeNovelty.value.id)
    if (idx !== -1) novelties.value[idx].status = res.data.status
    showToast("Estado actualizado", "success")
  } catch (e) {
    showToast(e.response?.data?.detail || "Error", "error")
  } finally {
    changingStatus.value = false
  }
}

// ── Eliminar novedad ─────────────────────────────────
async function handleDelete(n) {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar "${n.title}"?`,
    text: "Se eliminarán también todas las evidencias adjuntas. Esta acción no se puede deshacer.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, eliminar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/novelties/${n.id}`)
    showToast("Novedad eliminada", "success")
    closeDetail()
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error al eliminar", "error")
  }
}

// ── Evidencias ───────────────────────────────────────
async function loadEvidences(noveltyId) {
  try {
    const res   = await api.get(`/novelties/${noveltyId}/evidence`)
    evidences.value = res.data
  } catch {}
}

async function onEvidenceUploaded(evidence) {
  evidences.value.push(evidence)
  const idx = novelties.value.findIndex(n => n.id === activeNovelty.value.id)
  if (idx !== -1) novelties.value[idx].evidence_count = evidences.value.length
}

async function deleteEvidence(ev) {
  const { isConfirmed } = await window.Swal.fire({
    title: "¿Eliminar esta evidencia?",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Eliminar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/novelties/evidence/${ev.id}`)
    await loadEvidences(activeNovelty.value.id)
    const idx = novelties.value.findIndex(n => n.id === activeNovelty.value.id)
    if (idx !== -1) novelties.value[idx].evidence_count = evidences.value.length
    showToast("Evidencia eliminada", "success")
  } catch {
    showToast("Error al eliminar evidencia", "error")
  }
}

// ── Lightbox / Video ─────────────────────────────────
function openLightbox(url) { lightboxUrl.value = url }

// ── Helpers ──────────────────────────────────────────
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
  if (canManageAll.value) await loadUsersList()
})
</script>

<style scoped>

/* ── LAYOUT ── */
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

.page-header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.page-icon {
  font-size: 32px;
  color: #f59e0b;
  flex-shrink: 0;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  margin: 0;
  color: var(--text-main, #1e293b);
}

.page-sub {
  font-size: 12px;
  color: var(--text-muted, #64748b);
  margin: 2px 0 0;
}

/* ── FILTROS ── */
.filters-row {
  display: flex;
  align-items: center;
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

.search-box input {
  border: none;
  outline: none;
  background: transparent;
  font-size: 13px;
  color: var(--text-main, #1e293b);
  width: 100%;
}

.search-box .bi { opacity: 0.4; font-size: 14px; }

.filter-select {
  padding: 7px 10px; border-radius: 8px;
  border: 1px solid var(--border, #e2e8f0);
  background: var(--card-bg, #fff);
  font-size: 13px; color: var(--text-main, #1e293b);
  min-width: 170px;
}

.date-filters {
  display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
}
.filter-date {
  padding: 7px 10px; border-radius: 8px;
  border: 1px solid var(--border, #e2e8f0);
  background: var(--card-bg, #fff);
  font-size: 13px; color: var(--text-main, #1e293b);
}
.date-sep { color: #94a3b8; font-size: 13px; }
.btn-clear-filter {
  background: none; border: none; color: #94a3b8;
  font-size: 16px; cursor: pointer; padding: 4px;
  border-radius: 6px; display: flex; align-items: center;
  transition: color 0.15s;
}
.btn-clear-filter:hover { color: #ef4444; }

.status-tabs {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 13px;
  border-radius: 20px;
  border: 1px solid var(--border, #e2e8f0);
  background: var(--card-bg, #fff);
  font-size: 12px;
  cursor: pointer;
  color: var(--text-muted, #64748b);
  transition: all 0.15s;
}

.tab-btn.active {
  background: var(--primary, #3b82f6);
  border-color: var(--primary, #3b82f6);
  color: #fff;
}

.tab-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}

.dot-all       { background: #94a3b8; }
.dot-pendiente { background: #f59e0b; }
.dot-revisada  { background: #3b82f6; }
.dot-resuelta  { background: #22c55e; }

.tab-count {
  background: rgba(0,0,0,0.08);
  border-radius: 10px;
  padding: 1px 6px;
  font-size: 10px;
  font-weight: 700;
}

.tab-btn.active .tab-count { background: rgba(255,255,255,0.25); }

/* ── LOADING / EMPTY ── */
.loading-state {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 48px;
  justify-content: center;
  color: var(--text-muted, #64748b);
}

.spinner {
  width: 24px; height: 24px;
  border: 3px solid rgba(0,0,0,0.1);
  border-top-color: var(--primary, #3b82f6);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 64px;
  color: var(--text-muted, #94a3b8);
}
.empty-state .bi { font-size: 48px; opacity: 0.3; }
.empty-state p   { font-size: 14px; margin: 0; }

/* ── CARDS ── */
.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.novelty-card {
  background: var(--card-bg, #fff);
  border: 1px solid var(--border, #e2e8f0);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
  display: flex;
  flex-direction: column;
  gap: 10px;
  border-left: 4px solid transparent;
}
.novelty-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0,0,0,0.1);
}

.card-pendiente { border-left-color: #f59e0b; }
.card-revisada  { border-left-color: #3b82f6; }
.card-resuelta  { border-left-color: #22c55e; }

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-date { font-size: 11px; color: var(--text-muted, #94a3b8); }

.card-title {
  font-size: 15px;
  font-weight: 600;
  margin: 0;
  color: var(--text-main, #1e293b);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-desc {
  font-size: 12.5px;
  color: var(--text-muted, #64748b);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.5;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
  padding-top: 8px;
  border-top: 1px solid var(--border, #f1f5f9);
}

.card-author {
  font-size: 11px;
  color: var(--text-muted, #94a3b8);
  display: flex;
  align-items: center;
  gap: 4px;
}

.card-evid {
  font-size: 11px;
  color: var(--text-muted, #94a3b8);
  display: flex;
  align-items: center;
  gap: 4px;
}
.card-evid.has-evid { color: #3b82f6; font-weight: 600; }

/* Status badges */
.status-badge {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.4px;
  padding: 3px 9px;
  border-radius: 20px;
  text-transform: uppercase;
}
.badge-pendiente { background: rgba(245,158,11,0.15); color: #d97706; }
.badge-revisada  { background: rgba(59,130,246,0.15); color: #2563eb; }
.badge-resuelta  { background: rgba(34,197,94,0.15);  color: #16a34a; }

/* ── MODALES ── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.modal-box {
  background: var(--card-bg, #fff);
  border-radius: 14px;
  width: 100%;
  max-width: 560px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  overflow: hidden;
}

.modal-detail { max-width: 720px; }

.modal-header-bar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 18px 20px;
  border-bottom: 1px solid var(--border, #e2e8f0);
  gap: 12px;
}

.modal-header-bar h2 {
  font-size: 17px;
  font-weight: 700;
  margin: 0;
  color: var(--text-main, #1e293b);
}

.detail-header-left {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.modal-footer-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid var(--border, #e2e8f0);
}

/* Formulario */
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 13px; font-weight: 600; color: var(--text-main, #374151); }
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

.has-error input,
.has-error textarea { border-color: #ef4444; }

.error-msg { font-size: 11px; color: #ef4444; }

/* Detalle */
.detail-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--text-muted, #64748b);
}
.detail-meta .bi { margin-right: 3px; }

.detail-desc {
  font-size: 14px;
  color: var(--text-main, #374151);
  line-height: 1.6;
  margin: 0;
  white-space: pre-wrap;
}

/* Cambio de estado */
.status-change-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  background: var(--input-bg, #f8fafc);
  border-radius: 10px;
  border: 1px solid var(--border, #e2e8f0);
  flex-wrap: wrap;
}

.status-change-row label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted, #64748b);
  white-space: nowrap;
}

.status-btns { display: flex; gap: 6px; flex-wrap: wrap; }

.status-opt-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  border-radius: 20px;
  border: 1px solid var(--border, #e2e8f0);
  background: var(--card-bg, #fff);
  font-size: 12px;
  cursor: pointer;
  color: var(--text-muted, #64748b);
  transition: all 0.15s;
}

.opt-pendiente.active { background: rgba(245,158,11,0.15); border-color: #f59e0b; color: #d97706; }
.opt-revisada.active  { background: rgba(59,130,246,0.15);  border-color: #3b82f6; color: #2563eb; }
.opt-resuelta.active  { background: rgba(34,197,94,0.15);   border-color: #22c55e; color: #16a34a; }

/* Evidencias */
.evidence-section { display: flex; flex-direction: column; gap: 12px; }

.evidence-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.evidence-section-header h4 {
  font-size: 14px;
  font-weight: 600;
  margin: 0;
  color: var(--text-main, #1e293b);
  display: flex;
  align-items: center;
  gap: 7px;
}

.btn-upload-ev {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 8px;
  background: var(--primary, #3b82f6);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-upload-ev:hover { background: #2563eb; }
.btn-upload-ev.loading { background: #94a3b8; cursor: default; }

.evidence-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  gap: 10px;
}

.ev-item {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  background: var(--input-bg, #f1f5f9);
  aspect-ratio: 1;
}

.ev-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
  cursor: pointer;
  transition: opacity 0.15s;
}
.ev-thumb:hover { opacity: 0.85; }

.ev-video-thumb,
.ev-doc-thumb {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 11px;
  cursor: pointer;
  color: var(--text-muted, #64748b);
}
.ev-video-thumb .bi { font-size: 28px; color: #3b82f6; }
.ev-doc-thumb   .bi { font-size: 28px; color: #6366f1; }

.btn-del-ev {
  position: absolute;
  top: 4px;
  right: 4px;
  background: rgba(239,68,68,0.9);
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 3px 6px;
  font-size: 11px;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s;
}
.ev-item:hover .btn-del-ev { opacity: 1; }

.no-evidence {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 24px 16px;
  color: var(--text-muted, #94a3b8);
  text-align: center;
}
.no-evidence .bi { font-size: 28px; opacity: 0.4; }
.no-evidence p   { font-size: 12px; margin: 0; line-height: 1.5; }

/* Botones */
.btn-primary {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 9px 18px;
  background: var(--primary, #3b82f6);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-primary:hover    { background: #2563eb; }
.btn-primary:disabled { background: #94a3b8; cursor: default; }

.btn-secondary {
  padding: 9px 18px;
  background: var(--input-bg, #f1f5f9);
  border: 1px solid var(--border, #e2e8f0);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  color: var(--text-main, #374151);
  transition: background 0.15s;
}
.btn-secondary:hover { background: #e2e8f0; }

.btn-close-x {
  background: none;
  border: none;
  font-size: 16px;
  cursor: pointer;
  color: var(--text-muted, #94a3b8);
  padding: 4px;
  flex-shrink: 0;
  transition: color 0.15s;
}
.btn-close-x:hover { color: #ef4444; }

.btn-icon-sm {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 7px 14px;
  background: none;
  border: 1px solid var(--border, #e2e8f0);
  border-radius: 7px;
  font-size: 12px;
  cursor: pointer;
  color: var(--text-main, #374151);
  transition: background 0.15s;
}
.btn-icon-sm:hover { background: var(--input-bg, #f1f5f9); }

.btn-danger-sm {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 7px 14px;
  background: none;
  border: 1px solid #fca5a5;
  border-radius: 7px;
  font-size: 12px;
  cursor: pointer;
  color: #ef4444;
  transition: background 0.15s;
}
.btn-danger-sm:hover { background: rgba(239,68,68,0.08); }

/* Lightbox */
.lightbox {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.92);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.lightbox-img {
  max-width: 90vw;
  max-height: 90vh;
  border-radius: 8px;
  object-fit: contain;
}

.lightbox-video {
  max-width: 90vw;
  max-height: 90vh;
  border-radius: 8px;
}

.lightbox-close {
  position: absolute;
  top: 16px;
  right: 16px;
  background: rgba(255,255,255,0.1);
  border: none;
  color: #fff;
  font-size: 20px;
  border-radius: 8px;
  padding: 8px 10px;
  cursor: pointer;
  transition: background 0.15s;
}
.lightbox-close:hover { background: rgba(255,255,255,0.2); }

/* ── RESPONSIVE ── */
@media (max-width: 768px) {
  .page-wrap   { padding: 14px; gap: 14px; }
  .page-title  { font-size: 17px; }
  .cards-grid  { grid-template-columns: 1fr; }
  .filters-row { flex-direction: column; align-items: stretch; }
  .modal-box   { max-height: 95vh; }
}
</style>
