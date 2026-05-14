<template>
  <div class="myads-root">

    <!-- KPI Bar -->
    <div class="kpi-bar">
      <div class="kpi-card" v-for="k in kpis" :key="k.label">
        <i :class="`bi ${k.icon}`" :style="`color:${k.color}`"></i>
        <div class="kpi-info">
          <span class="kpi-val">{{ stats[k.key] ?? 0 }}</span>
          <span class="kpi-lbl">{{ k.label }}</span>
        </div>
      </div>
    </div>

    <!-- Header -->
    <div class="section-header">
      <h5 class="section-title">
        <i class="bi bi-megaphone me-2"></i>Mis Pautas Publicitarias
      </h5>
      <button class="btn-new" @click="openNew">
        <i class="bi bi-plus-lg me-1"></i>Nueva Pauta
      </button>
    </div>

    <!-- Table -->
    <div class="table-wrap">
      <div v-if="loading" class="empty-state">
        <div class="spinner-border spinner-border-sm text-secondary me-2"></div>
        Cargando...
      </div>
      <div v-else-if="!ads.length" class="empty-state">
        <i class="bi bi-megaphone" style="font-size:2.5rem;opacity:.3"></i>
        <p class="mt-2 mb-0">Aún no tienes pautas. Crea tu primera pauta y llega a todos nuestros asociados.</p>
      </div>
      <table v-else class="ads-table">
        <thead>
          <tr>
            <th>Título</th>
            <th>Estado</th>
            <th>Slot</th>
            <th>Perfil</th>
            <th>Inicio</th>
            <th>Fin</th>
            <th>Imp.</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ad in ads" :key="ad.id">
            <td class="td-title">{{ ad.title }}</td>
            <td><span class="status-badge" :class="ad.status">{{ statusLabel(ad.status) }}</span></td>
            <td class="td-center">{{ ad.slot_position || '—' }}</td>
            <td>{{ ad.target_profile_name || 'Todos' }}</td>
            <td>{{ fmtDate(ad.start_date) }}</td>
            <td>{{ fmtDate(ad.end_date) }}</td>
            <td class="td-center">{{ ad.impressions }}</td>
            <td class="td-actions">
              <button class="btn-act btn-view" @click="openDetail(ad)" title="Ver detalle">
                <i class="bi bi-eye"></i>
              </button>
              <button
                v-if="ad.status === 'pending' || ad.status === 'rejected'"
                class="btn-act btn-edit" @click="openEdit(ad)" title="Editar"
              ><i class="bi bi-pencil"></i></button>
              <button
                v-if="ad.status === 'expired' || ad.status === 'rejected'"
                class="btn-act btn-renew" @click="openRenew(ad)" title="Renovar"
              ><i class="bi bi-arrow-clockwise"></i></button>
              <button
                v-if="['pending','rejected','expired'].includes(ad.status)"
                class="btn-act btn-del" @click="deleteAd(ad)" title="Eliminar"
              ><i class="bi bi-trash3"></i></button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- MODAL: Create / Edit -->
    <div v-if="showModal" class="modal-backdrop" @click.self="closeModal">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="modal-title">
            <i class="bi bi-megaphone-fill me-2"></i>{{ editing ? 'Editar Pauta' : 'Nueva Pauta' }}
          </h6>
          <button class="btn-close-modal" @click="closeModal"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-body">

          <!-- Datos generales -->
          <div class="form-section-label">Información de la pauta</div>
          <div class="form-row">
            <label class="form-lbl">Título *</label>
            <input v-model="form.title" class="form-ctrl" maxlength="200" placeholder="Ej: Promoción de temporada" />
          </div>
          <div class="form-row">
            <label class="form-lbl">Descripción</label>
            <textarea v-model="form.description" class="form-ctrl" rows="2" placeholder="Descripción breve de la pauta"></textarea>
          </div>
          <div class="form-row">
            <label class="form-lbl">URL destino (debe iniciar con https://)</label>
            <input v-model="form.cta_url" class="form-ctrl" placeholder="https://wa.me/57300..." />
          </div>
          <div class="form-row-2">
            <div>
              <label class="form-lbl">Fecha inicio *</label>
              <input v-model="form.start_date" type="date" class="form-ctrl" />
            </div>
            <div>
              <label class="form-lbl">Fecha fin *</label>
              <input v-model="form.end_date" type="date" class="form-ctrl" />
            </div>
          </div>
          <div class="form-row">
            <label class="form-lbl">Perfil objetivo</label>
            <select v-model="form.target_profile_id" class="form-ctrl">
              <option :value="null">Todos los perfiles</option>
              <option v-for="p in profiles" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
          </div>
          <div class="form-row">
            <label class="form-lbl">Notas para el administrador</label>
            <textarea v-model="form.notes_to_admin" class="form-ctrl" rows="2" placeholder="Instrucciones especiales, preferencias de slot, etc."></textarea>
          </div>

          <!-- Piezas multimedia -->
          <div class="form-section-label mt-3">
            Piezas multimedia
            <span class="pieces-hint">(máx. 3 — imagen/video 8MB c/u)</span>
          </div>

          <!-- Existing pieces -->
          <div v-if="form.pieces.length" class="pieces-list">
            <div v-for="(piece, pi) in form.pieces" :key="piece.id || pi" class="piece-item">
              <div class="piece-preview">
                <img v-if="piece.piece_type === 'image'" :src="piece.media_url" class="piece-thumb" />
                <div v-else-if="piece.piece_type === 'video'" class="piece-icon"><i class="bi bi-camera-video-fill"></i></div>
                <div v-else-if="piece.piece_type === 'youtube'" class="piece-icon yt"><i class="bi bi-youtube"></i></div>
                <div v-else class="piece-icon txt"><i class="bi bi-type"></i></div>
              </div>
              <span class="piece-label">{{ pieceLabel(piece) }}</span>
              <button v-if="editing" class="btn-del-piece" @click="deletePiece(piece, pi)">
                <i class="bi bi-trash3"></i>
              </button>
            </div>
          </div>

          <!-- Add piece buttons (only available after save if editing) -->
          <div v-if="editing && form.pieces.length < 3" class="add-piece-row">
            <label class="btn-add-piece" title="Subir imagen o video">
              <i class="bi bi-upload me-1"></i>Subir archivo
              <input type="file" accept=".jpg,.jpeg,.png,.webp,.mp4,.mov,.webm" @change="uploadPiece" class="hidden-input" />
            </label>
            <button class="btn-add-piece" @click="showYTForm = !showYTForm">
              <i class="bi bi-youtube me-1"></i>YouTube
            </button>
            <button class="btn-add-piece" @click="showTextForm = !showTextForm">
              <i class="bi bi-type me-1"></i>Texto
            </button>
          </div>
          <div v-if="!editing" class="pieces-note">
            <i class="bi bi-info-circle me-1"></i>Guarda la pauta primero para agregar piezas multimedia.
          </div>

          <!-- YouTube sub-form -->
          <div v-if="showYTForm" class="sub-form">
            <input v-model="ytId" class="form-ctrl" placeholder="ID del video YouTube (ej: dQw4w9WgXcQ)" maxlength="20" />
            <button class="btn-sub-save" @click="addYoutube"><i class="bi bi-plus me-1"></i>Agregar</button>
            <button class="btn-sub-cancel" @click="showYTForm=false;ytId=''">Cancelar</button>
          </div>

          <!-- Text sub-form -->
          <div v-if="showTextForm" class="sub-form">
            <textarea v-model="textContent" class="form-ctrl" rows="3" maxlength="500" placeholder="Texto de la pieza (máx. 500 caracteres)"></textarea>
            <button class="btn-sub-save" @click="addText"><i class="bi bi-plus me-1"></i>Agregar</button>
            <button class="btn-sub-cancel" @click="showTextForm=false;textContent=''">Cancelar</button>
          </div>

          <!-- Comprobante de pago -->
          <div class="form-section-label mt-3">Comprobante de pago</div>
          <div v-if="form.payment" class="payment-status">
            <i class="bi bi-receipt me-1"></i>
            Pago registrado —
            <span class="pay-status-badge" :class="form.payment.status">{{ payStatusLabel(form.payment.status) }}</span>
          </div>
          <div v-if="editing" class="form-row">
            <label class="btn-add-piece" title="Subir comprobante">
              <i class="bi bi-upload me-1"></i>{{ form.payment ? 'Reemplazar comprobante' : 'Subir comprobante' }}
              <input type="file" accept=".jpg,.jpeg,.png,.pdf,.webp" @change="uploadPayment" class="hidden-input" />
            </label>
          </div>

          <!-- Rejection reason -->
          <div v-if="form.rejection_reason" class="rejection-box">
            <i class="bi bi-x-circle me-1"></i>
            <strong>Rechazada:</strong> {{ form.rejection_reason }}
          </div>

        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeModal">Cancelar</button>
          <button class="btn-save" :disabled="saving" @click="saveAd">
            <span v-if="saving" class="spinner-border spinner-border-sm me-1"></span>
            {{ editing ? 'Guardar cambios' : 'Crear pauta' }}
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL: Renew -->
    <div v-if="showRenewModal" class="modal-backdrop" @click.self="showRenewModal=false">
      <div class="modal-box modal-sm">
        <div class="modal-header">
          <h6 class="modal-title"><i class="bi bi-arrow-clockwise me-2"></i>Renovar Pauta</h6>
          <button class="btn-close-modal" @click="showRenewModal=false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-body">
          <p class="mb-3 text-secondary" style="font-size:.85rem">
            Se clonarán todas las piezas sin necesidad de re-subirlas. Solo actualiza las fechas y un mensaje al admin si lo deseas.
          </p>
          <div class="form-row-2">
            <div>
              <label class="form-lbl">Nueva fecha inicio *</label>
              <input v-model="renewForm.start_date" type="date" class="form-ctrl" />
            </div>
            <div>
              <label class="form-lbl">Nueva fecha fin *</label>
              <input v-model="renewForm.end_date" type="date" class="form-ctrl" />
            </div>
          </div>
          <div class="form-row mt-2">
            <label class="form-lbl">Notas al administrador</label>
            <textarea v-model="renewForm.notes_to_admin" class="form-ctrl" rows="2" placeholder="Renovación de pauta..."></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showRenewModal=false">Cancelar</button>
          <button class="btn-save" :disabled="saving" @click="confirmRenew">
            <span v-if="saving" class="spinner-border spinner-border-sm me-1"></span>
            Renovar
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import api from "@/services/apis"
import { useModuleName } from "@/composables/useModuleName"

const { moduleName } = useModuleName()

const ads      = ref([])
const stats    = ref({})
const profiles = ref([])
const loading  = ref(false)
const saving   = ref(false)

const showModal    = ref(false)
const editing      = ref(false)
const showYTForm   = ref(false)
const showTextForm = ref(false)
const ytId         = ref("")
const textContent  = ref("")

const showRenewModal = ref(false)
const renewTarget    = ref(null)
const renewForm      = ref({ start_date: "", end_date: "", notes_to_admin: "" })

const form = ref(emptyForm())

const kpis = [
  { key: "active",   label: "Activas",   icon: "bi-broadcast",       color: "#22c55e" },
  { key: "pending",  label: "Pendientes",icon: "bi-hourglass-split",  color: "#f59e0b" },
  { key: "approved", label: "Aprobadas", icon: "bi-check-circle",     color: "#3b82f6" },
  { key: "expired",  label: "Expiradas", icon: "bi-calendar-x",       color: "#6b7280" },
]

function emptyForm() {
  return {
    id: null, title: "", description: "", cta_url: "", notes_to_admin: "",
    target_profile_id: null, start_date: "", end_date: "",
    pieces: [], payment: null, rejection_reason: null,
  }
}

async function loadAll() {
  loading.value = true
  try {
    const [adsRes, statsRes, profRes] = await Promise.all([
      api.get("/ads/my"),
      api.get("/ads/my/stats"),
      api.get("/business-profiles/"),
    ])
    ads.value      = adsRes.data
    stats.value    = statsRes.data
    profiles.value = profRes.data.filter(p => p.is_active && !p.name?.toLowerCase().includes("sysadmin"))
  } finally {
    loading.value = false
  }
}

function openNew() {
  form.value = emptyForm()
  editing.value   = false
  showYTForm.value  = false
  showTextForm.value = false
  showModal.value = true
}

function openEdit(ad) {
  form.value = {
    id: ad.id, title: ad.title, description: ad.description || "",
    cta_url: ad.cta_url || "", notes_to_admin: ad.notes_to_admin || "",
    target_profile_id: ad.target_profile_id || null,
    start_date: ad.start_date || "", end_date: ad.end_date || "",
    pieces: [...(ad.pieces || [])],
    payment: ad.payments?.[0] || null,
    rejection_reason: ad.rejection_reason || null,
  }
  editing.value   = true
  showYTForm.value  = false
  showTextForm.value = false
  showModal.value = true
}

function openDetail(ad) {
  openEdit(ad)
}

function openRenew(ad) {
  renewTarget.value = ad
  renewForm.value = { start_date: "", end_date: "", notes_to_admin: "" }
  showRenewModal.value = true
}

function closeModal() {
  showModal.value    = false
  showYTForm.value   = false
  showTextForm.value = false
  ytId.value = ""
  textContent.value = ""
}

async function saveAd() {
  if (!form.value.title.trim()) return alert("El título es requerido")
  if (!form.value.start_date || !form.value.end_date) return alert("Las fechas son requeridas")
  saving.value = true
  try {
    const payload = {
      title: form.value.title, description: form.value.description,
      cta_url: form.value.cta_url || null, notes_to_admin: form.value.notes_to_admin,
      target_profile_id: form.value.target_profile_id,
      start_date: form.value.start_date, end_date: form.value.end_date,
    }
    let saved
    if (editing.value) {
      const res = await api.put(`/ads/${form.value.id}`, payload)
      saved = res.data
    } else {
      const res = await api.post("/ads/", payload)
      saved = res.data
      form.value.id = saved.id
      editing.value = true
    }
    form.value.pieces = saved.pieces || []
    await loadAll()
  } catch (e) {
    alert(e.response?.data?.detail || "Error al guardar la pauta")
  } finally {
    saving.value = false
  }
}

async function uploadPiece(e) {
  const file = e.target.files[0]
  if (!file) return
  saving.value = true
  try {
    const fd = new FormData()
    fd.append("file", file)
    const res = await api.post(`/ads/${form.value.id}/pieces/upload`, fd, {
      headers: { "Content-Type": "multipart/form-data" }
    })
    form.value.pieces.push(res.data)
    await loadAll()
  } catch (err) {
    alert(err.response?.data?.detail || "Error al subir el archivo")
  } finally {
    saving.value = false
    e.target.value = ""
  }
}

async function addYoutube() {
  if (!ytId.value.trim()) return
  saving.value = true
  try {
    const res = await api.post(`/ads/${form.value.id}/pieces/youtube`, { youtube_id: ytId.value.trim() })
    form.value.pieces.push(res.data)
    showYTForm.value = false
    ytId.value = ""
    await loadAll()
  } catch (err) {
    alert(err.response?.data?.detail || "Error al agregar YouTube")
  } finally {
    saving.value = false
  }
}

async function addText() {
  if (!textContent.value.trim()) return
  saving.value = true
  try {
    const res = await api.post(`/ads/${form.value.id}/pieces/text`, { text_content: textContent.value.trim() })
    form.value.pieces.push(res.data)
    showTextForm.value = false
    textContent.value = ""
    await loadAll()
  } catch (err) {
    alert(err.response?.data?.detail || "Error al agregar texto")
  } finally {
    saving.value = false
  }
}

async function deletePiece(piece, pi) {
  if (!confirm("¿Eliminar esta pieza?")) return
  try {
    await api.delete(`/ads/${form.value.id}/pieces/${piece.id}`)
    form.value.pieces.splice(pi, 1)
    await loadAll()
  } catch (err) {
    alert(err.response?.data?.detail || "Error al eliminar pieza")
  }
}

async function uploadPayment(e) {
  const file = e.target.files[0]
  if (!file) return
  saving.value = true
  try {
    const fd = new FormData()
    fd.append("file", file)
    const res = await api.post(`/ads/${form.value.id}/payment`, fd, {
      headers: { "Content-Type": "multipart/form-data" }
    })
    form.value.payment = res.data
    await loadAll()
  } catch (err) {
    alert(err.response?.data?.detail || "Error al subir comprobante")
  } finally {
    saving.value = false
    e.target.value = ""
  }
}

async function deleteAd(ad) {
  if (!confirm(`¿Eliminar la pauta "${ad.title}"?`)) return
  try {
    await api.delete(`/ads/${ad.id}`)
    await loadAll()
  } catch (err) {
    alert(err.response?.data?.detail || "Error al eliminar")
  }
}

async function confirmRenew() {
  if (!renewForm.value.start_date || !renewForm.value.end_date) return alert("Las fechas son requeridas")
  saving.value = true
  try {
    await api.post(`/ads/${renewTarget.value.id}/renew`, renewForm.value)
    showRenewModal.value = false
    await loadAll()
  } catch (err) {
    alert(err.response?.data?.detail || "Error al renovar")
  } finally {
    saving.value = false
  }
}

function statusLabel(s) {
  const map = { pending:"Pendiente", approved:"Aprobada", active:"Activa", paused:"Pausada", expired:"Expirada", rejected:"Rechazada" }
  return map[s] || s
}
function payStatusLabel(s) {
  const map = { pending:"Pendiente", verified:"Verificado", rejected:"Rechazado" }
  return map[s] || s
}
function pieceLabel(p) {
  if (p.piece_type === "image")   return "Imagen"
  if (p.piece_type === "video")   return "Video"
  if (p.piece_type === "youtube") return `YouTube: ${p.youtube_id}`
  if (p.piece_type === "text")    return `Texto: ${(p.text_content || "").slice(0, 30)}...`
  return p.piece_type
}
function fmtDate(d) {
  if (!d) return "—"
  const [y, m, dd] = d.split("-")
  return `${dd}/${m}/${y}`
}

onMounted(loadAll)
</script>

<style scoped>
.myads-root { padding: 16px; max-width: 1100px; margin: 0 auto; }

/* KPI Bar */
.kpi-bar {
  display: flex; gap: 12px; margin-bottom: 18px; flex-wrap: wrap;
}
.kpi-card {
  flex: 1; min-width: 110px;
  background: var(--card-bg, #fff);
  border-radius: 10px; padding: 12px 14px;
  display: flex; align-items: center; gap: 10px;
  box-shadow: 0 1px 4px rgba(0,0,0,.08);
}
.kpi-card .bi { font-size: 22px; flex-shrink: 0; }
.kpi-info { display: flex; flex-direction: column; }
.kpi-val  { font-size: 20px; font-weight: 800; line-height: 1; }
.kpi-lbl  { font-size: 11px; opacity: .6; }

/* Section header */
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.section-title  { font-size: 15px; font-weight: 700; margin: 0; }
.btn-new {
  background: #2563eb; color: #fff; border: none;
  border-radius: 8px; padding: 7px 14px; font-size: 13px; font-weight: 600;
  cursor: pointer; display: flex; align-items: center; transition: background .15s;
}
.btn-new:hover { background: #1d4ed8; }

/* Table */
.table-wrap {
  background: var(--card-bg, #fff);
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0,0,0,.08);
  overflow-x: auto;
}
.empty-state {
  text-align: center; padding: 40px 20px;
  color: #9ca3af; display: flex; flex-direction: column; align-items: center; gap: 8px;
}
.ads-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.ads-table th {
  padding: 10px 12px; background: rgba(0,0,0,.04); font-weight: 700;
  text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: .4px;
  white-space: nowrap;
}
.ads-table td { padding: 10px 12px; border-top: 1px solid rgba(0,0,0,.06); vertical-align: middle; }
.td-title { max-width: 180px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.td-center { text-align: center; }
.td-actions { display: flex; gap: 4px; }

.status-badge {
  display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 700;
}
.status-badge.pending  { background: rgba(245,158,11,.15);  color: #d97706; }
.status-badge.approved { background: rgba(59,130,246,.15);  color: #2563eb; }
.status-badge.active   { background: rgba(34,197,94,.15);   color: #16a34a; }
.status-badge.paused   { background: rgba(107,114,128,.15); color: #6b7280; }
.status-badge.expired  { background: rgba(107,114,128,.1);  color: #9ca3af; }
.status-badge.rejected { background: rgba(239,68,68,.15);   color: #dc2626; }

.btn-act {
  width: 28px; height: 28px; border: none; border-radius: 6px; cursor: pointer;
  display: flex; align-items: center; justify-content: center; font-size: 13px;
}
.btn-view  { background: rgba(59,130,246,.1);  color: #2563eb; }
.btn-edit  { background: rgba(245,158,11,.1);  color: #d97706; }
.btn-renew { background: rgba(34,197,94,.1);   color: #16a34a; }
.btn-del   { background: rgba(239,68,68,.1);   color: #dc2626; }

/* Modal */
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(0,0,0,.5);
  display: flex; align-items: center; justify-content: center; z-index: 3000; padding: 16px;
}
.modal-box {
  background: var(--card-bg, #fff); border-radius: 14px; width: 100%; max-width: 560px;
  max-height: 90vh; overflow-y: auto; display: flex; flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,.3);
}
.modal-sm { max-width: 400px; }
.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; border-bottom: 1px solid rgba(0,0,0,.08); flex-shrink: 0;
}
.modal-title { font-size: 15px; font-weight: 700; margin: 0; }
.btn-close-modal { background: none; border: none; font-size: 16px; cursor: pointer; opacity: .5; }
.btn-close-modal:hover { opacity: 1; }
.modal-body { padding: 16px 20px; flex: 1; overflow-y: auto; }
.modal-footer {
  display: flex; justify-content: flex-end; gap: 8px;
  padding: 12px 20px; border-top: 1px solid rgba(0,0,0,.08); flex-shrink: 0;
}
.btn-cancel { background: none; border: 1px solid rgba(0,0,0,.15); border-radius: 7px; padding: 7px 16px; font-size: 13px; cursor: pointer; }
.btn-save   { background: #2563eb; color: #fff; border: none; border-radius: 7px; padding: 7px 18px; font-size: 13px; font-weight: 700; cursor: pointer; }
.btn-save:disabled { opacity: .5; cursor: not-allowed; }

.form-section-label {
  font-size: 10px; font-weight: 700; letter-spacing: .5px; text-transform: uppercase;
  opacity: .5; margin-bottom: 8px; margin-top: 4px;
}
.pieces-hint { font-weight: 400; margin-left: 6px; }
.form-row { margin-bottom: 10px; }
.form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }
.form-lbl { font-size: 11px; font-weight: 600; display: block; margin-bottom: 4px; opacity: .75; }
.form-ctrl {
  width: 100%; border: 1px solid rgba(0,0,0,.15); border-radius: 6px;
  padding: 7px 10px; font-size: 13px; background: transparent;
  color: inherit; box-sizing: border-box;
}
.form-ctrl:focus { outline: none; border-color: #2563eb; }

/* Pieces */
.pieces-list { display: flex; flex-direction: column; gap: 6px; margin-bottom: 8px; }
.piece-item  { display: flex; align-items: center; gap: 8px; background: rgba(0,0,0,.04); border-radius: 7px; padding: 6px 10px; }
.piece-preview { width: 36px; height: 36px; border-radius: 6px; overflow: hidden; flex-shrink: 0; background: rgba(0,0,0,.08); display: flex; align-items: center; justify-content: center; }
.piece-thumb { width: 100%; height: 100%; object-fit: cover; }
.piece-icon  { font-size: 18px; color: #3b82f6; }
.piece-icon.yt  { color: #ef4444; }
.piece-icon.txt { color: #8b5cf6; }
.piece-label { flex: 1; font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.btn-del-piece { background: none; border: none; color: #dc2626; cursor: pointer; font-size: 14px; }

.add-piece-row { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; }
.btn-add-piece {
  display: flex; align-items: center; gap: 4px; padding: 6px 12px;
  border: 1.5px dashed rgba(0,0,0,.2); border-radius: 7px; font-size: 12px;
  cursor: pointer; background: transparent; color: inherit; transition: border-color .15s;
}
.btn-add-piece:hover { border-color: #2563eb; color: #2563eb; }
.hidden-input { display: none; }

.pieces-note {
  font-size: 11px; color: #6b7280; background: rgba(0,0,0,.04);
  padding: 8px 10px; border-radius: 6px; margin-bottom: 8px;
}

.sub-form { background: rgba(0,0,0,.04); border-radius: 8px; padding: 10px; margin-bottom: 8px; display: flex; gap: 8px; align-items: flex-start; flex-wrap: wrap; }
.btn-sub-save   { background: #2563eb; color: #fff; border: none; border-radius: 6px; padding: 6px 12px; font-size: 12px; cursor: pointer; white-space: nowrap; }
.btn-sub-cancel { background: none; border: 1px solid rgba(0,0,0,.15); border-radius: 6px; padding: 6px 12px; font-size: 12px; cursor: pointer; white-space: nowrap; }

.payment-status { font-size: 12px; margin-bottom: 8px; display: flex; align-items: center; gap: 6px; }
.pay-status-badge { padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 700; }
.pay-status-badge.pending  { background: rgba(245,158,11,.15); color: #d97706; }
.pay-status-badge.verified { background: rgba(34,197,94,.15);  color: #16a34a; }
.pay-status-badge.rejected { background: rgba(239,68,68,.15);  color: #dc2626; }

.rejection-box {
  background: rgba(239,68,68,.08); border: 1px solid rgba(239,68,68,.2);
  border-radius: 8px; padding: 10px 12px; font-size: 12px; color: #dc2626; margin-top: 10px;
}
.mt-2 { margin-top: 8px; }
.mt-3 { margin-top: 14px; }

@media (max-width: 768px) {
  .form-row-2 { grid-template-columns: 1fr; }
  .kpi-bar    { gap: 8px; }
  .kpi-card   { min-width: 80px; padding: 8px 10px; }
}
@media (max-width: 576px) {
  .myads-root { padding: 10px; }
  .ads-table th, .ads-table td { padding: 8px; font-size: 12px; }
}
</style>
