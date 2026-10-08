<template>
  <div class="sh-container">

    <!-- Header -->
    <div class="sh-header">
      <h2 class="sh-title"><i class="bi bi-question-circle-fill me-2"></i>{{ moduleName || 'Gestión de Ayuda' }}</h2>
      <button class="sh-btn-new" @click="openNew">
        <i class="bi bi-plus-lg me-1"></i> Nuevo artículo
      </button>
    </div>

    <!-- Filtros -->
    <div class="sh-filters">
      <div class="sh-search-wrap">
        <i class="bi bi-search"></i>
        <input v-model="filterKeyword" class="sh-input sh-search" placeholder="Buscar por título, descripción o palabras clave…" />
      </div>
      <select v-model="filterProfile" class="sh-select">
        <option value="">Todos los perfiles</option>
        <option value="__general__">General (sin perfil)</option>
        <option v-for="p in profiles" :key="p.id" :value="p.id">{{ p.name }}</option>
      </select>
      <select v-model="filterCategory" class="sh-select">
        <option value="">Todas las categorías</option>
        <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
      </select>
      <button v-if="filterKeyword || filterProfile || filterCategory" class="sh-btn-clear" @click="clearFilters" title="Limpiar filtros">
        <i class="bi bi-x-lg"></i>
      </button>
    </div>

    <!-- Tabla -->
    <div class="sh-table-wrap">
      <div v-if="loading" class="sh-loading">
        <div class="spinner-border text-primary" role="status"></div>
      </div>
      <table v-else class="sh-table">
        <thead>
          <tr>
            <th>#</th><th>Perfil</th><th>Ruta vista</th><th>Categoría</th><th>Título</th><th>Medio</th><th>Orden</th><th>Activo</th><th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in filteredArticles" :key="a.id" :class="{ 'row-inactive': !a.is_active }">
            <td class="sh-id">{{ a.id }}</td>
            <td><span class="sh-badge" :class="a.profile_id ? 'badge-profile' : 'badge-general'">{{ profileName(a.profile_id) }}</span></td>
            <td class="sh-route"><span v-if="a.view_route" class="sh-route-badge">{{ a.view_route }}</span><span v-else class="sh-no-gif">—</span></td>
            <td><span class="sh-cat">{{ a.category }}</span></td>
            <td class="sh-ttl" :title="a.title">{{ a.title }}</td>
            <td>
              <template v-if="a.gif_url">
                <video v-if="isVideo(a.gif_url)" :src="a.gif_url" class="sh-gif-thumb" muted preload="metadata"></video>
                <img v-else :src="a.gif_url" class="sh-gif-thumb" :alt="a.title" loading="lazy" />
              </template>
              <span v-else class="sh-no-gif">—</span>
            </td>
            <td class="sh-order">{{ a.order_index }}</td>
            <td>
              <span class="sh-active" :class="a.is_active ? 'active-yes' : 'active-no'">
                {{ a.is_active ? 'Sí' : 'No' }}
              </span>
            </td>
            <td class="sh-actions">
              <button class="sh-btn-icon" title="Editar" @click="openEdit(a)"><i class="bi bi-pencil"></i></button>
              <button class="sh-btn-icon sh-btn-del" title="Eliminar" @click="deleteArticle(a)"><i class="bi bi-trash"></i></button>
            </td>
          </tr>
          <tr v-if="!filteredArticles.length">
            <td colspan="9" class="sh-empty">{{ articles.length ? 'Sin resultados para los filtros aplicados' : 'No hay artículos' }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal crear/editar -->
    <teleport to="body">
      <div v-if="modal.open" class="sh-overlay" @click.self="closeModal">
        <div class="sh-modal">

          <div class="sh-modal-header">
            <span><i class="bi bi-pencil-square me-2"></i>{{ modal.id ? 'Editar artículo' : 'Nuevo artículo' }}</span>
            <button class="sh-modal-close" @click="closeModal"><i class="bi bi-x-lg"></i></button>
          </div>

          <div class="sh-modal-body">
            <div class="sh-row2">
              <div class="sh-field">
                <label class="sh-label">Perfil</label>
                <select v-model="form.profile_id" class="sh-select">
                  <option :value="null">General (todos los perfiles)</option>
                  <option v-for="p in profiles" :key="p.id" :value="p.id">{{ p.name }}</option>
                </select>
              </div>
              <div class="sh-field">
                <label class="sh-label">Categoría</label>
                <input v-model="form.category" class="sh-input" placeholder="Ej: Usuarios, Inventario…" list="cat-list" maxlength="100" />
                <datalist id="cat-list">
                  <option v-for="c in categories" :key="c" :value="c" />
                </datalist>
              </div>
            </div>

            <div class="sh-field">
              <label class="sh-label">Título *</label>
              <input v-model="form.title" class="sh-input" placeholder="Ej: Cómo crear un usuario" maxlength="200" />
            </div>

            <div class="sh-field">
              <label class="sh-label">
                Vista asociada
                <span class="sh-hint">— el botón ? de esa vista abrirá este artículo directamente</span>
              </label>
              <select class="sh-select" @change="onModuleSelect($event)">
                <option value="">— Seleccionar vista del sistema —</option>
                <optgroup label="Vistas del asociado">
                  <option
                    v-for="m in modules.filter(x => !x.is_sysadmin)"
                    :key="m.id"
                    :value="m.route"
                    :selected="form.view_route === m.route"
                  >{{ m.name }} — {{ m.route }}</option>
                </optgroup>
                <optgroup label="Vistas SYSADMIN">
                  <option
                    v-for="m in modules.filter(x => x.is_sysadmin)"
                    :key="m.id"
                    :value="m.route"
                    :selected="form.view_route === m.route"
                  >{{ m.name }} — {{ m.route }}</option>
                </optgroup>
              </select>
              <div class="sh-route-manual">
                <span class="sh-hint">Ruta seleccionada:</span>
                <code class="sh-route-code">{{ form.view_route || '(ninguna)' }}</code>
                <button v-if="form.view_route" type="button" class="sh-clear-route" @click="form.view_route = ''" title="Limpiar">
                  <i class="bi bi-x"></i>
                </button>
              </div>
            </div>

            <div class="sh-field">
              <label class="sh-label">Descripción</label>
              <textarea v-model="form.description" class="sh-textarea" rows="5" placeholder="Explica el proceso paso a paso…"></textarea>
            </div>

            <div class="sh-field">
              <label class="sh-label">Palabras clave <span class="sh-hint">(separadas por coma, para búsqueda)</span></label>
              <input v-model="form.keywords" class="sh-input" placeholder="Ej: usuario, crear, acceso, contraseña" maxlength="500" />
            </div>

            <div class="sh-row2">
              <div class="sh-field">
                <label class="sh-label">Orden</label>
                <input v-model.number="form.order_index" type="number" class="sh-input" min="0" />
              </div>
              <div class="sh-field">
                <label class="sh-label">Activo</label>
                <select v-model="form.is_active" class="sh-select">
                  <option :value="1">Sí</option>
                  <option :value="0">No</option>
                </select>
              </div>
            </div>

            <!-- GIF / imagen / video -->
            <div class="sh-field">
              <label class="sh-label">GIF / Imagen / Video <span class="sh-hint">(máx. {{ MAX_MB }} MB — GIF, PNG, JPG, WEBP, MP4, WEBM)</span></label>
              <div class="sh-gif-area">
                <div v-if="form.gif_url" class="sh-gif-preview">
                  <video v-if="isVideo(form.gif_url)" :src="form.gif_url" class="sh-gif-img" autoplay loop muted playsinline></video>
                  <img v-else :src="form.gif_url" alt="preview" class="sh-gif-img" />
                  <button class="sh-gif-remove" @click="form.gif_url = ''" title="Quitar (se aplica al guardar)">
                    <i class="bi bi-x-circle-fill"></i>
                  </button>
                </div>
                <div v-else class="sh-gif-placeholder">
                  <i class="bi bi-image"></i>
                  <span>Sin archivo asignado</span>
                </div>

                <div v-if="uploading" class="sh-progress">
                  <div class="sh-progress-bar" :style="{ width: uploadPct + '%' }"></div>
                  <span class="sh-progress-txt">{{ uploadPct }}%</span>
                </div>

                <div class="sh-gif-actions">
                  <label class="sh-btn-upload" :class="{ disabled: !modal.id || uploading }">
                    <i class="bi bi-upload me-1"></i>
                    {{ uploading ? 'Subiendo…' : 'Subir archivo' }}
                    <input
                      v-if="modal.id"
                      type="file"
                      accept=".gif,.webp,.png,.jpg,.jpeg,.mp4,.webm"
                      style="display:none"
                      :disabled="uploading"
                      @change="uploadGif"
                    />
                  </label>
                  <span v-if="!modal.id" class="sh-hint">Guarda primero el artículo para poder subir el archivo</span>
                </div>
              </div>
            </div>

          </div>

          <div class="sh-modal-footer">
            <button class="sh-btn-cancel" @click="closeModal">Cerrar</button>
            <button class="sh-btn-save" :disabled="saving || uploading" @click="saveArticle">
              <i v-if="saving" class="bi bi-arrow-repeat spin me-1"></i>
              <i v-else class="bi bi-check-lg me-1"></i>
              {{ saving ? 'Guardando…' : 'Guardar' }}
            </button>
          </div>

        </div>
      </div>
    </teleport>

  </div>
</template>

<script setup>
import { ref, computed } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import { useModuleName } from "@/composables/useModuleName"

const MAX_MB       = 20   // igual que MAX_GIF_MB en help_router.py
const ALLOWED_EXT  = ["gif", "webp", "png", "jpg", "jpeg", "mp4", "webm"]

const { moduleName } = useModuleName()

const articles       = ref([])
const profiles       = ref([])
const modules        = ref([])   // system_modules con ruta
const loading        = ref(false)
const saving         = ref(false)
const uploading      = ref(false)
const uploadPct      = ref(0)
const filterProfile  = ref("")
const filterCategory = ref("")
const filterKeyword  = ref("")

const modal = ref({ open: false, id: null })
const form  = ref(emptyForm())

function emptyForm() {
  return { profile_id: null, view_route: "", category: "General", title: "", description: "", keywords: "", gif_url: "", order_index: 0, is_active: 1 }
}

function isVideo(url) {
  return /\.(mp4|webm)(\?|$)/i.test(url || "")
}

const categories = computed(() => [...new Set(articles.value.map(a => a.category).filter(Boolean))].sort())

const filteredArticles = computed(() => {
  const kw  = filterKeyword.value.trim().toLowerCase()
  return articles.value.filter(a => {
    if (filterProfile.value === "__general__" && a.profile_id !== null) return false
    if (filterProfile.value && filterProfile.value !== "__general__" && a.profile_id !== filterProfile.value) return false
    if (filterCategory.value && a.category !== filterCategory.value) return false
    if (kw && ![a.title, a.description, a.keywords, a.category].some(f => f?.toLowerCase().includes(kw))) return false
    return true
  })
})

function clearFilters() {
  filterKeyword.value  = ""
  filterProfile.value  = ""
  filterCategory.value = ""
}

function profileName(id) {
  if (!id) return "General"
  return profiles.value.find(p => p.id === id)?.name || `Perfil ${id}`
}

async function loadArticles() {
  loading.value = true
  try {
    const res = await api.get("/help/admin/list")
    articles.value = res.data
  } catch (e) {
    articles.value = []
    showToast(e.response?.data?.detail || "Error al cargar artículos", "error")
  } finally { loading.value = false }
}

async function loadProfiles() {
  try {
    const res = await api.get("/business-profiles/")
    profiles.value = res.data.data ?? res.data
  } catch {}
}

async function loadModules() {
  try {
    const res = await api.get("/system-modules/flat/")
    // Solo los que tienen ruta propia (excluir grupos/padres sin ruta)
    modules.value = res.data.filter(m => m.route && m.route.trim() !== "")
  } catch {}
}

function onModuleSelect(e) {
  form.value.view_route = e.target.value || ""
}

function openNew() {
  form.value  = emptyForm()
  modal.value = { open: true, id: null }
}
function openEdit(a) {
  form.value  = { ...a }
  modal.value = { open: true, id: a.id }
}
function closeModal() {
  if (uploading.value) return
  modal.value.open = false
}

async function saveArticle() {
  if (!form.value.title.trim()) return showToast("El título es requerido", "warning")
  saving.value = true
  try {
    if (modal.value.id) {
      await api.put(`/help/${modal.value.id}`, form.value)
      showToast("Artículo actualizado", "success")
    } else {
      const res = await api.post("/help/", form.value)
      modal.value.id = res.data.id
      showToast("Artículo creado. Ahora puedes subir el archivo.", "success", 2500)
    }
    await loadArticles()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error al guardar", "error")
  } finally {
    saving.value = false
  }
}

async function uploadGif(e) {
  const file = e.target.files?.[0]
  e.target.value = ""
  if (!file || !modal.value.id) return

  const ext = (file.name.split(".").pop() || "").toLowerCase()
  if (!ALLOWED_EXT.includes(ext)) {
    return showToast("Formato no permitido. Usa GIF, PNG, JPG, WEBP, MP4 o WEBM", "warning", 3000)
  }
  const mb = file.size / (1024 * 1024)
  if (mb > MAX_MB) {
    return showToast(`El archivo pesa ${mb.toFixed(1)} MB y el máximo es ${MAX_MB} MB. Conviértelo a MP4/WEBM o redúcelo.`, "warning", 4500)
  }

  uploading.value = true
  uploadPct.value = 0
  try {
    const fd = new FormData()
    fd.append("file", file)
    const res = await api.post(`/help/${modal.value.id}/upload-gif`, fd, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 0,
      onUploadProgress: (ev) => {
        if (ev.total) uploadPct.value = Math.round((ev.loaded * 100) / ev.total)
      },
    })
    form.value.gif_url = res.data.gif_url
    await loadArticles()
    showToast("Archivo subido", "success")
  } catch (err) {
    const status = err.response?.status
    const msg = status === 413
      ? `El archivo supera el máximo permitido (${MAX_MB} MB)`
      : (err.response?.data?.detail || "Error al subir el archivo")
    showToast(msg, "error", 3500)
  } finally {
    uploading.value = false
  }
}

async function deleteArticle(a) {
  const { isConfirmed } = await window.Swal.fire({
    title: "¿Eliminar artículo?",
    text: `"${a.title}"`,
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, eliminar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#ef4444",
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/help/${a.id}`)
    showToast("Artículo eliminado", "success")
    await loadArticles()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error al eliminar", "error")
  }
}

loadProfiles()
loadModules()
loadArticles()
</script>

<style scoped>
.sh-container { padding: 24px; max-width: 1200px; }

.sh-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px; flex-wrap: wrap; gap: 10px;
}
.sh-title { font-size: 20px; font-weight: 700; color: #0f172a; margin: 0; display: flex; align-items: center; }
.sh-title .bi { color: #2563eb; }

.sh-btn-new {
  display: flex; align-items: center; gap: 6px;
  background: #2563eb; color: #fff; border: none;
  border-radius: 8px; padding: 9px 18px; font-size: 13px;
  font-weight: 600; cursor: pointer; transition: background .15s;
  box-shadow: 0 2px 6px rgba(37,99,235,.25);
}
.sh-btn-new:hover { background: #1d4ed8; }

/* ── Filtros ── */
.sh-filters {
  display: flex; flex-wrap: wrap; gap: 8px;
  margin-bottom: 14px; align-items: center;
}
.sh-search-wrap { position: relative; flex: 1; min-width: 220px; }
.sh-search-wrap .bi {
  position: absolute; left: 12px; top: 50%; transform: translateY(-50%);
  color: #94a3b8; font-size: 14px; pointer-events: none;
}
.sh-search { padding-left: 34px !important; }
.sh-btn-clear {
  background: #fff; border: 1px solid #cbd5e1; color: #64748b;
  border-radius: 8px; padding: 7px 10px; cursor: pointer; font-size: 13px;
  transition: background .15s, color .15s;
}
.sh-btn-clear:hover { background: #fef2f2; color: #dc2626; border-color: #fca5a5; }

.sh-select {
  background: #fff; color: #1e293b; border: 1px solid #cbd5e1;
  border-radius: 8px; padding: 8px 12px; font-size: 13px; min-width: 200px; outline: none;
}

/* ── Tabla ── */
.sh-table-wrap {
  overflow-x: auto; background: #fff;
  border: 1px solid #e2e8f0; border-radius: 12px;
  box-shadow: 0 1px 3px rgba(15,23,42,.06);
}
.sh-table {
  width: 100%; border-collapse: collapse;
  font-size: 13px; color: #1e293b;
}
.sh-table th {
  background: #f1f5f9; color: #475569; font-weight: 700; font-size: 12px;
  text-transform: uppercase; letter-spacing: .3px;
  padding: 11px 12px; text-align: left; border-bottom: 1px solid #e2e8f0;
  white-space: nowrap;
}
.sh-table td { padding: 10px 12px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.sh-table tbody tr:nth-child(even) td { background: #fafbfc; }
.sh-table tbody tr:hover td { background: #eff6ff; }
.sh-table tbody tr:last-child td { border-bottom: none; }
.row-inactive td { opacity: .6; }

.sh-id    { color: #64748b; font-size: 12px; font-weight: 600; }
.sh-order { color: #334155; font-weight: 600; text-align: center; }
.sh-cat {
  display: inline-block; font-size: 12px; font-weight: 600;
  background: #f5f3ff; color: #6d28d9; border: 1px solid #ddd6fe;
  border-radius: 6px; padding: 2px 8px; white-space: nowrap;
}
.sh-ttl { font-weight: 600; color: #0f172a; max-width: 260px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.sh-badge {
  font-size: 11px; font-weight: 700; border-radius: 20px; padding: 3px 10px; white-space: nowrap;
}
.badge-general { background: #e0f2fe; border: 1px solid #bae6fd; color: #0369a1; }
.badge-profile { background: #fef3c7; border: 1px solid #fde68a; color: #92400e; }

.sh-gif-thumb {
  width: 52px; height: 34px; object-fit: cover; border-radius: 6px;
  border: 1px solid #e2e8f0; background: #f1f5f9; display: block;
}
.sh-no-gif    { color: #94a3b8; }
.sh-route     { max-width: 180px; }
.sh-route-badge {
  font-size: 11px; background: #eff6ff; color: #1d4ed8;
  border: 1px solid #bfdbfe; border-radius: 4px; padding: 2px 6px;
  font-family: monospace; word-break: break-all;
}
.sh-route-manual {
  display: flex; align-items: center; gap: 8px; margin-top: 6px; flex-wrap: wrap;
}
.sh-route-code {
  font-size: 12px; background: #eff6ff; color: #1d4ed8;
  border-radius: 4px; padding: 3px 8px; font-family: monospace;
}
.sh-clear-route {
  background: none; border: none; color: #64748b; cursor: pointer;
  font-size: 14px; padding: 0 2px; line-height: 1;
}
.sh-clear-route:hover { color: #dc2626; }

.sh-active { font-size: 11px; font-weight: 700; border-radius: 20px; padding: 3px 10px; }
.active-yes { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
.active-no  { background: #fee2e2; color: #b91c1c; border: 1px solid #fecaca; }

.sh-actions { display: flex; gap: 6px; white-space: nowrap; justify-content: flex-end; }
.sh-btn-icon {
  background: #fff; border: 1px solid #cbd5e1; color: #475569;
  border-radius: 6px; padding: 4px 9px; cursor: pointer; font-size: 13px;
  transition: background .15s, color .15s;
}
.sh-btn-icon:hover       { background: #eff6ff; color: #1d4ed8; border-color: #93c5fd; }
.sh-btn-del:hover        { background: #fef2f2; color: #dc2626; border-color: #fca5a5; }
.sh-empty { text-align: center; color: #64748b; padding: 28px; }
.sh-loading { display: flex; justify-content: center; padding: 40px; }

/* ── Modal ── */
.sh-overlay {
  position: fixed; inset: 0; background: rgba(15,23,42,.5);
  display: flex; align-items: center; justify-content: center;
  z-index: 9999; padding: 16px;
}
.sh-modal {
  background: #fff; border: 1px solid #e2e8f0;
  border-radius: 14px; width: 100%; max-width: 600px;
  max-height: 90vh; overflow-y: auto;
  box-shadow: 0 20px 60px rgba(15,23,42,.25);
}
.sh-modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px 12px; border-bottom: 1px solid #e2e8f0;
  font-size: 15px; font-weight: 700; color: #0f172a; gap: 10px;
  position: sticky; top: 0; background: #fff; z-index: 1;
}
.sh-modal-close {
  background: transparent; border: none; color: #64748b;
  font-size: 16px; cursor: pointer; padding: 4px 6px; border-radius: 6px;
}
.sh-modal-close:hover { color: #dc2626; background: #fef2f2; }

.sh-modal-body {
  padding: 20px; display: flex; flex-direction: column; gap: 14px;
}
.sh-modal-footer {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 14px 20px 18px; border-top: 1px solid #e2e8f0;
  position: sticky; bottom: 0; background: #fff;
}
.sh-row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.sh-field { display: flex; flex-direction: column; gap: 5px; }
.sh-label {
  font-size: 11px; font-weight: 700; color: #475569;
  text-transform: uppercase; letter-spacing: .4px;
}
.sh-hint { font-weight: 400; text-transform: none; letter-spacing: 0; color: #64748b; font-size: 12px; }
.sh-input, .sh-textarea {
  background: #fff;
  color: #1e293b;
  border: 1px solid #cbd5e1;
  border-radius: 8px; padding: 8px 12px; font-size: 13px; outline: none;
  transition: border-color .2s;
  width: 100%;
}
.sh-input::placeholder, .sh-textarea::placeholder { color: #94a3b8; }
.sh-input:focus, .sh-textarea:focus, .sh-select:focus {
  border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,.15);
}
.sh-textarea {
  resize: vertical;
  font-family: inherit;
  line-height: 1.5;
}

/* ── GIF area ── */
.sh-gif-area { display: flex; flex-direction: column; gap: 10px; }
.sh-gif-preview { position: relative; display: inline-block; max-width: 280px; }
.sh-gif-img { width: 100%; border-radius: 8px; border: 1px solid #e2e8f0; display: block; }
.sh-gif-remove {
  position: absolute; top: -8px; right: -8px; background: #ef4444;
  border: none; color: #fff; border-radius: 50%; width: 22px; height: 22px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; font-size: 13px; padding: 0;
}
.sh-gif-placeholder {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 6px; padding: 24px;
  background: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 8px;
  color: #64748b; font-size: 13px; max-width: 280px;
}
.sh-gif-placeholder .bi { font-size: 28px; }

.sh-progress {
  position: relative; height: 20px; max-width: 280px;
  background: #e2e8f0; border-radius: 10px; overflow: hidden;
}
.sh-progress-bar { height: 100%; background: #3b82f6; transition: width .2s; }
.sh-progress-txt {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; color: #0f172a;
}

.sh-gif-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.sh-btn-upload {
  display: inline-flex; align-items: center; gap: 6px;
  background: #eff6ff; border: 1px solid #bfdbfe; color: #1d4ed8;
  border-radius: 8px; padding: 7px 14px; font-size: 12px; font-weight: 600;
  cursor: pointer; transition: background .15s, color .15s; margin: 0;
}
.sh-btn-upload:hover:not(.disabled) { background: #dbeafe; }
.sh-btn-upload.disabled { opacity: .45; cursor: not-allowed; }

.sh-btn-cancel {
  background: #fff; color: #475569; border: 1px solid #cbd5e1;
  border-radius: 8px; font-size: 13px; padding: 8px 18px; cursor: pointer;
}
.sh-btn-cancel:hover { background: #f1f5f9; }
.sh-btn-save {
  display: flex; align-items: center; gap: 6px;
  background: #2563eb; color: #fff; border: none;
  border-radius: 8px; font-size: 13px; font-weight: 600;
  padding: 8px 20px; cursor: pointer; transition: background .15s;
}
.sh-btn-save:hover:not(:disabled) { background: #1d4ed8; }
.sh-btn-save:disabled { opacity: .5; cursor: not-allowed; }

.spin { animation: spin .7s linear infinite; }
@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }

/* Tablet */
@media (max-width: 992px) {
  .sh-table th:nth-child(3),
  .sh-table td:nth-child(3) { display: none; }
}
@media (max-width: 768px) {
  .sh-container { padding: 16px; }
  .sh-row2 { grid-template-columns: 1fr; }
  .sh-filters { flex-direction: column; align-items: stretch; }
  .sh-search-wrap, .sh-select { width: 100%; min-width: unset; }
  .sh-btn-clear { align-self: flex-end; }
  .sh-table th:nth-child(6),
  .sh-table td:nth-child(6),
  .sh-table th:nth-child(7),
  .sh-table td:nth-child(7) { display: none; }
  .sh-ttl { max-width: 180px; }
}
@media (max-width: 576px) {
  .sh-container { padding: 12px; }
  .sh-title { font-size: 17px; }
  .sh-btn-new { width: 100%; justify-content: center; }
  .sh-table th:nth-child(1),
  .sh-table td:nth-child(1),
  .sh-table th:nth-child(4),
  .sh-table td:nth-child(4) { display: none; }
  .sh-table td, .sh-table th { padding: 9px 8px; }
  .sh-ttl { max-width: 130px; }
  .sh-modal { max-height: 94vh; border-radius: 12px; }
  .sh-modal-body { padding: 16px; }
  .sh-gif-preview, .sh-gif-placeholder, .sh-progress { max-width: 100%; }
}
</style>
