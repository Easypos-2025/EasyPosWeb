<template>
  <div class="sh-container">

    <!-- Header -->
    <div class="sh-header">
      <h2 class="sh-title"><i class="bi bi-question-circle-fill me-2"></i>Gestión de Ayuda</h2>
      <button class="sh-btn-new" @click="openNew">
        <i class="bi bi-plus-lg me-1"></i> Nuevo artículo
      </button>
    </div>

    <!-- Filtros -->
    <div class="sh-filters">
      <select v-model="filterProfile" class="sh-select" @change="loadArticles">
        <option value="">Todos los perfiles</option>
        <option :value="null">General (sin perfil)</option>
        <option v-for="p in profiles" :key="p.id" :value="p.id">{{ p.name }}</option>
      </select>
    </div>

    <!-- Tabla -->
    <div class="sh-table-wrap">
      <div v-if="loading" class="sh-loading">
        <div class="spinner-border text-primary" role="status"></div>
      </div>
      <table v-else class="sh-table">
        <thead>
          <tr>
            <th>#</th><th>Perfil</th><th>Categoría</th><th>Título</th><th>GIF</th><th>Orden</th><th>Activo</th><th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in articles" :key="a.id">
            <td class="sh-id">{{ a.id }}</td>
            <td><span class="sh-badge" :class="a.profile_id ? 'badge-profile' : 'badge-general'">{{ profileName(a.profile_id) }}</span></td>
            <td class="sh-cat">{{ a.category }}</td>
            <td class="sh-ttl">{{ a.title }}</td>
            <td>
              <img v-if="a.gif_url" :src="a.gif_url" class="sh-gif-thumb" :alt="a.title" />
              <span v-else class="sh-no-gif">—</span>
            </td>
            <td>{{ a.order_index }}</td>
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
          <tr v-if="!articles.length">
            <td colspan="8" class="sh-empty">No hay artículos</td>
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
                <input v-model="form.category" class="sh-input" placeholder="Ej: Usuarios, Inventario…" list="cat-list" />
                <datalist id="cat-list">
                  <option v-for="c in categories" :key="c" :value="c" />
                </datalist>
              </div>
            </div>

            <div class="sh-field">
              <label class="sh-label">Título *</label>
              <input v-model="form.title" class="sh-input" placeholder="Ej: Cómo crear un usuario" />
            </div>

            <div class="sh-field">
              <label class="sh-label">Descripción</label>
              <textarea v-model="form.description" class="sh-textarea" rows="4" placeholder="Explica el proceso paso a paso…"></textarea>
            </div>

            <div class="sh-field">
              <label class="sh-label">Palabras clave <span class="sh-hint">(separadas por coma, para búsqueda)</span></label>
              <input v-model="form.keywords" class="sh-input" placeholder="Ej: usuario, crear, acceso, contraseña" />
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

            <!-- GIF -->
            <div class="sh-field">
              <label class="sh-label">GIF / Imagen</label>
              <div class="sh-gif-area">
                <div v-if="form.gif_url" class="sh-gif-preview">
                  <img :src="form.gif_url" alt="preview" class="sh-gif-img" />
                  <button class="sh-gif-remove" @click="form.gif_url = ''" title="Quitar imagen">
                    <i class="bi bi-x-circle-fill"></i>
                  </button>
                </div>
                <div v-else class="sh-gif-placeholder">
                  <i class="bi bi-image"></i>
                  <span>Sin GIF asignado</span>
                </div>
                <div class="sh-gif-actions">
                  <label class="sh-btn-upload" :class="{ disabled: !modal.id }">
                    <i class="bi bi-upload me-1"></i>
                    {{ uploading ? 'Subiendo…' : 'Subir GIF' }}
                    <input
                      v-if="modal.id"
                      type="file"
                      accept=".gif,.webp,.png,.jpg,.jpeg"
                      style="display:none"
                      :disabled="uploading"
                      @change="uploadGif"
                    />
                  </label>
                  <span v-if="!modal.id" class="sh-hint">Guarda primero para poder subir el GIF</span>
                </div>
              </div>
            </div>

          </div>

          <div class="sh-modal-footer">
            <button class="sh-btn-cancel" @click="closeModal">Cancelar</button>
            <button class="sh-btn-save" :disabled="saving" @click="saveArticle">
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

const articles      = ref([])
const profiles      = ref([])
const loading       = ref(false)
const saving        = ref(false)
const uploading     = ref(false)
const filterProfile = ref("")

const modal = ref({ open: false, id: null })
const form  = ref(emptyForm())

function emptyForm() {
  return { profile_id: null, category: "General", title: "", description: "", keywords: "", gif_url: "", order_index: 0, is_active: 1 }
}

// Categorías únicas para datalist
const categories = computed(() => [...new Set(articles.value.map(a => a.category).filter(Boolean))])

function profileName(id) {
  if (!id) return "General"
  return profiles.value.find(p => p.id === id)?.name || `Perfil ${id}`
}

async function loadArticles() {
  loading.value = true
  try {
    const params = filterProfile.value !== "" ? { profile_id: filterProfile.value === null ? "null" : filterProfile.value } : {}
    const res = await api.get("/help/admin/list", { params })
    articles.value = res.data
  } catch { articles.value = [] }
  finally { loading.value = false }
}

async function loadProfiles() {
  try {
    const res = await api.get("/business-profiles/")
    profiles.value = res.data.data ?? res.data
  } catch {}
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
      showToast("Artículo creado. Ahora puedes subir el GIF.", "success")
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
  if (!file || !modal.value.id) return
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append("file", file)
    const res = await api.post(`/help/${modal.value.id}/upload-gif`, fd, {
      headers: { "Content-Type": "multipart/form-data" }
    })
    form.value.gif_url = res.data.gif_url
    await loadArticles()
    showToast("GIF subido", "success")
  } catch (e) {
    showToast(e.response?.data?.detail || "Error al subir GIF", "error")
  } finally {
    uploading.value = false
    e.target.value = ""
  }
}

async function deleteArticle(a) {
  const { isConfirmed } = await window.Swal.fire({
    title: "¿Eliminar artículo?",
    text: `"${a.title}"`,
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, eliminar",
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
loadArticles()
</script>

<style scoped>
.sh-container { padding: 24px; max-width: 1000px; }

.sh-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px; flex-wrap: wrap; gap: 10px;
}
.sh-title { font-size: 18px; font-weight: 700; color: #e2e8f0; }

.sh-btn-new {
  display: flex; align-items: center; gap: 6px;
  background: #1d4ed8; color: #fff; border: none;
  border-radius: 8px; padding: 9px 18px; font-size: 13px;
  font-weight: 600; cursor: pointer; transition: background .15s;
}
.sh-btn-new:hover { background: #2563eb; }

.sh-filters { margin-bottom: 14px; }

.sh-select {
  background: #1e293b; color: #e2e8f0; border: 1px solid #334155;
  border-radius: 8px; padding: 7px 12px; font-size: 13px; min-width: 200px;
}

/* ── Tabla ── */
.sh-table-wrap { overflow-x: auto; }
.sh-table {
  width: 100%; border-collapse: collapse;
  font-size: 13px; color: #e2e8f0;
}
.sh-table th {
  background: #0f172a; color: #94a3b8; font-weight: 700;
  padding: 10px 12px; text-align: left; border-bottom: 1px solid #334155;
  white-space: nowrap;
}
.sh-table td { padding: 10px 12px; border-bottom: 1px solid #1e293b; vertical-align: middle; }
.sh-table tr:hover td { background: rgba(59,130,246,.04); }

.sh-id  { color: #475569; font-size: 11px; }
.sh-cat { color: #94a3b8; }
.sh-ttl { font-weight: 600; max-width: 220px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.sh-badge {
  font-size: 11px; font-weight: 700; border-radius: 20px; padding: 2px 9px;
}
.badge-general { background: #1e293b; border: 1px solid #334155; color: #64748b; }
.badge-profile { background: rgba(59,130,246,.15); border: 1px solid rgba(59,130,246,.3); color: #93c5fd; }

.sh-gif-thumb { width: 48px; height: 32px; object-fit: cover; border-radius: 4px; }
.sh-no-gif    { color: #475569; }

.sh-active { font-size: 11px; font-weight: 700; border-radius: 20px; padding: 2px 8px; }
.active-yes { background: rgba(34,197,94,.15); color: #4ade80; }
.active-no  { background: rgba(239,68,68,.1);  color: #f87171; }

.sh-actions { display: flex; gap: 6px; white-space: nowrap; }
.sh-btn-icon {
  background: transparent; border: 1px solid #334155; color: #94a3b8;
  border-radius: 6px; padding: 4px 8px; cursor: pointer; font-size: 13px;
  transition: background .15s, color .15s;
}
.sh-btn-icon:hover       { background: #1e3a5f; color: #93c5fd; border-color: #3b82f6; }
.sh-btn-del:hover        { background: rgba(239,68,68,.15); color: #f87171; border-color: #ef4444; }
.sh-empty { text-align: center; color: #64748b; padding: 24px; }
.sh-loading { display: flex; justify-content: center; padding: 40px; }

/* ── Modal ── */
.sh-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.6);
  display: flex; align-items: center; justify-content: center;
  z-index: 9999; padding: 16px;
}
.sh-modal {
  background: #1e293b; border: 1px solid #334155;
  border-radius: 14px; width: 100%; max-width: 580px;
  max-height: 90vh; overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0,0,0,.5);
}
.sh-modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px 12px; border-bottom: 1px solid #334155;
  font-size: 15px; font-weight: 700; color: #e2e8f0; gap: 10px;
  position: sticky; top: 0; background: #1e293b; z-index: 1;
}
.sh-modal-close {
  background: transparent; border: none; color: #64748b;
  font-size: 16px; cursor: pointer; padding: 4px 6px; border-radius: 6px;
}
.sh-modal-close:hover { color: #f87171; }

.sh-modal-body {
  padding: 20px; display: flex; flex-direction: column; gap: 14px;
}
.sh-modal-footer {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 14px 20px 18px; border-top: 1px solid #334155;
  position: sticky; bottom: 0; background: #1e293b;
}
.sh-row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.sh-field { display: flex; flex-direction: column; gap: 5px; }
.sh-label {
  font-size: 11px; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: .4px;
}
.sh-hint { font-weight: 400; text-transform: none; letter-spacing: 0; color: #475569; }
.sh-input, .sh-textarea {
  background: #0f172a !important;
  color: #e2e8f0 !important;
  border: 1px solid #334155;
  border-radius: 8px; padding: 8px 12px; font-size: 13px; outline: none;
  transition: border-color .2s;
  width: 100%;
}
.sh-input:focus, .sh-textarea:focus, .sh-select:focus {
  border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,.2);
}
.sh-textarea {
  resize: vertical;
  font-family: inherit;
  line-height: 1.5;
}

/* ── GIF area ── */
.sh-gif-area { display: flex; flex-direction: column; gap: 10px; }
.sh-gif-preview { position: relative; display: inline-block; max-width: 260px; }
.sh-gif-img { width: 100%; border-radius: 8px; border: 1px solid #334155; }
.sh-gif-remove {
  position: absolute; top: -8px; right: -8px; background: #ef4444;
  border: none; color: #fff; border-radius: 50%; width: 22px; height: 22px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; font-size: 13px; padding: 0;
}
.sh-gif-placeholder {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 6px; padding: 24px;
  background: #0f172a; border: 2px dashed #334155; border-radius: 8px;
  color: #475569; font-size: 13px; max-width: 260px;
}
.sh-gif-placeholder .bi { font-size: 28px; }

.sh-gif-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.sh-btn-upload {
  display: inline-flex; align-items: center; gap: 6px;
  background: #0f172a; border: 1px solid #334155; color: #94a3b8;
  border-radius: 8px; padding: 7px 14px; font-size: 12px; font-weight: 600;
  cursor: pointer; transition: background .15s, color .15s;
}
.sh-btn-upload:hover:not(.disabled) { background: #1e3a5f; color: #93c5fd; border-color: #3b82f6; }
.sh-btn-upload.disabled { opacity: .4; cursor: not-allowed; }

.sh-btn-cancel {
  background: #0f172a; color: #94a3b8; border: 1px solid #334155;
  border-radius: 8px; font-size: 13px; padding: 8px 18px; cursor: pointer;
}
.sh-btn-save {
  display: flex; align-items: center; gap: 6px;
  background: #1d4ed8; color: #fff; border: none;
  border-radius: 8px; font-size: 13px; font-weight: 600;
  padding: 8px 20px; cursor: pointer; transition: background .15s;
}
.sh-btn-save:hover:not(:disabled) { background: #2563eb; }
.sh-btn-save:disabled { opacity: .5; cursor: not-allowed; }

.spin { animation: spin .7s linear infinite; }
@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }

@media (max-width: 768px) {
  .sh-container { padding: 16px; }
  .sh-row2 { grid-template-columns: 1fr; }
  .sh-table th:nth-child(6),
  .sh-table td:nth-child(6) { display: none; }
}
@media (max-width: 576px) {
  .sh-container { padding: 12px; }
}
</style>
