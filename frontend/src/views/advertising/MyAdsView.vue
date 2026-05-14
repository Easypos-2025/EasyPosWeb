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
        <div class="spinner-border spinner-border-sm text-secondary me-2"></div>Cargando...
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
              <button class="btn-act btn-view" @click="openDetail(ad)" title="Ver / Editar">
                <i class="bi bi-eye"></i>
              </button>
              <button v-if="['pending','rejected'].includes(ad.status)"
                class="btn-act btn-edit" @click="openEdit(ad)" title="Editar">
                <i class="bi bi-pencil"></i>
              </button>
              <button v-if="['expired','rejected'].includes(ad.status)"
                class="btn-act btn-renew" @click="openRenew(ad)" title="Renovar">
                <i class="bi bi-arrow-clockwise"></i>
              </button>
              <button v-if="['pending','rejected','expired'].includes(ad.status)"
                class="btn-act btn-del" @click="deleteAd(ad)" title="Eliminar">
                <i class="bi bi-trash3"></i>
              </button>
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

          <!-- Empresa solicitante -->
          <div class="company-info-bar">
            <i class="bi bi-building me-2"></i>
            <span class="ci-label">Empresa:</span>
            <span class="ci-name">{{ companyName }}</span>
          </div>

          <!-- Info general -->
          <div class="form-section-label mt-2">Información de la pauta</div>
          <div class="form-row">
            <label class="form-lbl">Título *</label>
            <input v-model="form.title" class="form-ctrl" maxlength="200" placeholder="Ej: Promoción de temporada" />
          </div>
          <div class="form-row">
            <label class="form-lbl">Descripción</label>
            <textarea v-model="form.description" class="form-ctrl" rows="2" placeholder="Descripción breve"></textarea>
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

          <!-- Perfil + Precio -->
          <div class="form-row-2">
            <div>
              <label class="form-lbl">Perfil objetivo</label>
              <select v-model="form.target_profile_id" class="form-ctrl" @change="onProfileChange">
                <option :value="null">Todos los perfiles</option>
                <option v-for="p in profiles" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
            </div>
            <div>
              <label class="form-lbl">Valor de la pauta</label>
              <div class="price-display">
                <i class="bi bi-currency-dollar me-1"></i>
                <span class="price-val">{{ fmtPrice(currentPrice) }}</span>
                <span class="price-cur">COP</span>
              </div>
            </div>
          </div>

          <div class="form-row">
            <label class="form-lbl">Notas para el administrador</label>
            <textarea v-model="form.notes_to_admin" class="form-ctrl" rows="2" placeholder="Instrucciones especiales, preferencias de slot, etc."></textarea>
          </div>

          <!-- Piezas multimedia -->
          <div class="form-section-label mt-3">
            Piezas multimedia
            <span class="pieces-hint">(máx. 3 — imagen/video máx. 8 MB c/u)</span>
          </div>

          <div v-if="form.pieces.length" class="pieces-list">
            <div v-for="(piece, pi) in form.pieces" :key="piece.id || pi" class="piece-item">
              <div class="piece-preview">
                <img v-if="piece.piece_type === 'image'" :src="piece.media_url" class="piece-thumb" />
                <div v-else-if="piece.piece_type === 'video'" class="piece-icon"><i class="bi bi-camera-video-fill"></i></div>
                <div v-else-if="piece.piece_type === 'youtube'" class="piece-icon yt"><i class="bi bi-youtube"></i></div>
                <div v-else-if="piece.piece_type === 'social'" class="piece-icon social"><i :class="platformIcon(piece.social_platform)"></i></div>
                <div v-else class="piece-icon txt"><i class="bi bi-type"></i></div>
              </div>
              <span class="piece-label">{{ pieceLabel(piece) }}</span>
              <button v-if="editing" class="btn-del-piece" @click="deletePiece(piece, pi)">
                <i class="bi bi-trash3"></i>
              </button>
            </div>
          </div>

          <div v-if="editing && canEditAd && form.pieces.length < 3" class="add-piece-row">
            <label class="btn-add-piece" title="Subir imagen o video (máx. 8MB)">
              <i class="bi bi-upload me-1"></i>Subir archivo
              <input type="file" accept=".jpg,.jpeg,.png,.webp,.mp4,.mov,.webm"
                @change="uploadPiece" class="hidden-input" :disabled="saving" />
            </label>
            <button class="btn-add-piece" @click="showSocialForm = !showSocialForm">
              <i class="bi bi-play-circle me-1"></i>Video/Social
            </button>
            <button class="btn-add-piece" @click="showTextForm = !showTextForm">
              <i class="bi bi-type me-1"></i>Texto
            </button>
          </div>
          <div v-if="!editing" class="pieces-note">
            <i class="bi bi-info-circle me-1"></i>Guarda la pauta primero para agregar piezas multimedia.
          </div>

          <!-- Video/Social sub-form -->
          <div v-if="showSocialForm" class="sub-form">
            <div class="yt-input-wrap">
              <input v-model="socialInput" class="form-ctrl"
                placeholder="Pega la URL: YouTube, Instagram, TikTok, Facebook..."
                @paste.prevent="onSocialPaste" />
              <p class="yt-hint">Acepta: youtube.com, youtu.be, instagram.com/reel, tiktok.com, facebook.com/watch...</p>
              <div v-if="detectedPlatform" class="platform-detect">
                <i :class="platformIcon(detectedPlatform)"></i>
                {{ platformLabel(detectedPlatform) }} detectado
              </div>
            </div>
            <div class="sub-actions">
              <button class="btn-sub-save" @click="addSocial" :disabled="saving">
                <i class="bi bi-plus me-1"></i>Agregar
              </button>
              <button class="btn-sub-cancel" @click="showSocialForm=false;socialInput='';detectedPlatform=''">Cancelar</button>
            </div>
          </div>

          <!-- Text sub-form -->
          <div v-if="showTextForm" class="sub-form">
            <textarea v-model="textContent" class="form-ctrl" rows="3"
              maxlength="500" placeholder="Texto de la pieza (máx. 500 caracteres)"></textarea>
            <div class="sub-actions">
              <button class="btn-sub-save" @click="addText" :disabled="saving">
                <i class="bi bi-plus me-1"></i>Agregar
              </button>
              <button class="btn-sub-cancel" @click="showTextForm=false;textContent=''">Cancelar</button>
            </div>
          </div>

          <!-- Redes sociales del anunciante -->
          <div class="form-section-label mt-3">Redes sociales (se mostrarán como íconos en la pauta)</div>
          <div class="social-fields">
            <div class="social-field">
              <span class="social-icon-lbl"><i class="bi bi-instagram" style="color:#e1306c"></i></span>
              <input v-model="form.social_instagram" class="form-ctrl" :disabled="!canEditAd"
                placeholder="https://instagram.com/tunegocio" />
            </div>
            <div class="social-field">
              <span class="social-icon-lbl"><i class="bi bi-tiktok" style="color:#010101"></i></span>
              <input v-model="form.social_tiktok" class="form-ctrl" :disabled="!canEditAd"
                placeholder="https://tiktok.com/@tunegocio" />
            </div>
            <div class="social-field">
              <span class="social-icon-lbl"><i class="bi bi-facebook" style="color:#1877f2"></i></span>
              <input v-model="form.social_facebook" class="form-ctrl" :disabled="!canEditAd"
                placeholder="https://facebook.com/tunegocio" />
            </div>
            <div class="social-field">
              <span class="social-icon-lbl"><i class="bi bi-youtube" style="color:#ff0000"></i></span>
              <input v-model="form.social_youtube_channel" class="form-ctrl" :disabled="!canEditAd"
                placeholder="https://youtube.com/@tunegocio" />
            </div>
            <div class="social-field">
              <span class="social-icon-lbl"><i class="bi bi-globe2" style="color:#6b7280"></i></span>
              <input v-model="form.social_website" class="form-ctrl" :disabled="!canEditAd"
                placeholder="https://tunegocio.com" />
            </div>
          </div>

          <!-- Comprobante de pago -->
          <div class="form-section-label mt-3">Comprobante de pago</div>
          <div v-if="form.payment" class="payment-status">
            <i class="bi bi-receipt me-1"></i>
            Pago registrado —
            <span class="pay-status-badge" :class="form.payment.status">{{ payStatusLabel(form.payment.status) }}</span>
            <a v-if="form.payment.receipt_url" :href="form.payment.receipt_url" target="_blank" rel="noopener"
              class="btn-ver-comp">
              <i class="bi bi-eye me-1"></i>Ver comprobante
            </a>
          </div>
          <div v-if="form.payment?.status === 'verified'" class="info-box">
            <i class="bi bi-check-circle me-1"></i>Pago verificado. El administrador activará tu pauta próximamente.
          </div>
          <div v-else-if="editing && canPayAd" class="form-row">
            <label class="btn-add-piece" :class="{ 'uploading': saving }">
              <i class="bi bi-upload me-1"></i>
              {{ form.payment ? 'Reemplazar comprobante' : 'Subir comprobante de pago' }}
              <input type="file" accept=".jpg,.jpeg,.png,.pdf,.webp"
                @change="uploadPayment" class="hidden-input" :disabled="saving" />
            </label>
          </div>

          <!-- Rechazo -->
          <div v-if="form.rejection_reason" class="rejection-box">
            <i class="bi bi-x-circle me-1"></i>
            <strong>Rechazada:</strong> {{ form.rejection_reason }}
          </div>

        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeModal">Cerrar</button>
          <button v-if="!editing || canEditAd" class="btn-save" :disabled="saving" @click="saveAd">
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
            Se clonarán todas las piezas sin re-subirlas. Actualiza las fechas y agrega un mensaje al admin si lo deseas.
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
import { ref, computed, watch, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import { useCompanyStore } from "@/stores/companyStore"

const companyStore = useCompanyStore()
const companyName  = computed(() => companyStore.selectedCompany?.name || "—")

const ads      = ref([])
const stats    = ref({})
const profiles = ref([])
const loading  = ref(false)
const saving   = ref(false)

const priceAll    = ref(0)
const priceSingle = ref(0)

const showModal      = ref(false)
const editing        = ref(false)
const showSocialForm = ref(false)
const showTextForm   = ref(false)
const socialInput    = ref("")
const detectedPlatform = ref("")
const textContent    = ref("")

const canEditAd = computed(() => !editing.value || ["pending","rejected"].includes(form.value.status || ""))
const canPayAd  = computed(() => editing.value && ["pending","rejected","approved"].includes(form.value.status || ""))

const showRenewModal = ref(false)
const renewTarget    = ref(null)
const renewForm      = ref({ start_date: "", end_date: "", notes_to_admin: "" })

const form = ref(emptyForm())

const currentPrice = computed(() =>
  form.value.target_profile_id ? priceSingle.value : priceAll.value
)

const kpis = [
  { key: "active",   label: "Activas",   icon: "bi-broadcast",       color: "#22c55e" },
  { key: "pending",  label: "Pendientes",icon: "bi-hourglass-split",  color: "#f59e0b" },
  { key: "approved", label: "Aprobadas", icon: "bi-check-circle",     color: "#3b82f6" },
  { key: "expired",  label: "Expiradas", icon: "bi-calendar-x",       color: "#6b7280" },
]

function emptyForm() {
  return {
    id: null, title: "", description: "", cta_url: "", notes_to_admin: "",
    target_profile_id: null, start_date: "", end_date: "", status: "pending",
    social_instagram: "", social_tiktok: "", social_facebook: "",
    social_youtube_channel: "", social_website: "",
    pieces: [], payment: null, rejection_reason: null,
  }
}

// ── Detección de plataforma social ────────────────────────────────────────
function detectPlatform(url) {
  if (!url) return ""
  const s = url.trim().toLowerCase()
  try {
    const u = new URL(url.trim())
    const h = u.hostname.replace("www.", "")
    if (h === "youtube.com" || h === "youtu.be" || h === "m.youtube.com") return "youtube"
    if (h === "instagram.com") return "instagram"
    if (h === "tiktok.com" || h === "vm.tiktok.com") return "tiktok"
    if (h === "facebook.com" || h === "fb.com" || h === "fb.watch") return "facebook"
    if (h === "twitter.com" || h === "x.com") return "twitter"
  } catch {}
  if (s.includes("youtube") || s.includes("youtu.be")) return "youtube"
  if (s.includes("instagram")) return "instagram"
  if (s.includes("tiktok")) return "tiktok"
  if (s.includes("facebook") || s.includes("fb.com")) return "facebook"
  return ""
}

function platformIcon(p) {
  return { youtube:"bi bi-youtube", instagram:"bi bi-instagram", tiktok:"bi bi-tiktok",
           facebook:"bi bi-facebook", twitter:"bi bi-twitter-x" }[p] || "bi bi-play-circle"
}
function platformLabel(p) {
  return { youtube:"YouTube", instagram:"Instagram", tiktok:"TikTok",
           facebook:"Facebook", twitter:"Twitter/X" }[p] || "Social"
}

function onSocialPaste(e) {
  const pasted = (e.clipboardData || window.clipboardData).getData("text")
  socialInput.value      = pasted
  detectedPlatform.value = detectPlatform(pasted)
}

watch(socialInput, (v) => { detectedPlatform.value = detectPlatform(v) })

// ── Cargar datos ───────────────────────────────────────────────────────────
async function loadAll() {
  loading.value = true
  try {
    const [adsRes, statsRes, profRes, priceAll_, priceSingle_] = await Promise.all([
      api.get("/ads/my"),
      api.get("/ads/my/stats"),
      api.get("/business-profiles/"),
      api.get("/system-config/ad_price_all_profiles").catch(() => ({ data: { config_value: "80000" } })),
      api.get("/system-config/ad_price_single_profile").catch(() => ({ data: { config_value: "50000" } })),
    ])
    ads.value      = adsRes.data
    stats.value    = statsRes.data
    // El endpoint devuelve { data: [...] }
    const rawProfiles = Array.isArray(profRes.data) ? profRes.data : (profRes.data?.data ?? [])
    profiles.value = rawProfiles.filter(p => p.is_active && !p.name?.toLowerCase().includes("sysadmin"))
    priceAll.value    = parseInt(priceAll_.data?.config_value)    || 80000
    priceSingle.value = parseInt(priceSingle_.data?.config_value) || 50000
  } catch (e) {
    showToast("Error al cargar las pautas", "error")
  } finally {
    loading.value = false
  }
}

function onProfileChange() { /* price updates via computed */ }

// ── Modales ────────────────────────────────────────────────────────────────
function openNew() {
  form.value = emptyForm()
  editing.value        = false
  showSocialForm.value = false
  showTextForm.value   = false
  showModal.value      = true
}

function openEdit(ad) {
  form.value = {
    id: ad.id, title: ad.title, description: ad.description || "",
    cta_url: ad.cta_url || "", notes_to_admin: ad.notes_to_admin || "",
    target_profile_id: ad.target_profile_id || null,
    start_date: ad.start_date || "", end_date: ad.end_date || "",
    status: ad.status || "pending",
    social_instagram:       ad.social_instagram || "",
    social_tiktok:          ad.social_tiktok || "",
    social_facebook:        ad.social_facebook || "",
    social_youtube_channel: ad.social_youtube_channel || "",
    social_website:         ad.social_website || "",
    pieces: [...(ad.pieces || [])],
    payment: ad.payments?.[0] || null,
    rejection_reason: ad.rejection_reason || null,
  }
  editing.value        = true
  showSocialForm.value = false
  showTextForm.value   = false
  showModal.value      = true
}

function openDetail(ad) { openEdit(ad) }

function openRenew(ad) {
  renewTarget.value = ad
  renewForm.value = { start_date: "", end_date: "", notes_to_admin: "" }
  showRenewModal.value = true
}

function closeModal() {
  showModal.value      = false
  showSocialForm.value = false
  showTextForm.value   = false
  socialInput.value    = ""
  detectedPlatform.value = ""
  textContent.value    = ""
}

// ── CRUD pauta ─────────────────────────────────────────────────────────────
async function saveAd() {
  if (!form.value.title.trim())        return showToast("El título es requerido", "warning")
  if (!form.value.start_date)          return showToast("La fecha de inicio es requerida", "warning")
  if (!form.value.end_date)            return showToast("La fecha de fin es requerida", "warning")
  if (form.value.start_date > form.value.end_date)
                                       return showToast("La fecha fin debe ser mayor a la fecha inicio", "warning")
  saving.value = true
  try {
    const payload = {
      title:                  form.value.title,
      description:            form.value.description || null,
      cta_url:                form.value.cta_url || null,
      notes_to_admin:         form.value.notes_to_admin || null,
      target_profile_id:      form.value.target_profile_id || null,
      start_date:             form.value.start_date,
      end_date:               form.value.end_date,
      social_instagram:       form.value.social_instagram || null,
      social_tiktok:          form.value.social_tiktok || null,
      social_facebook:        form.value.social_facebook || null,
      social_youtube_channel: form.value.social_youtube_channel || null,
      social_website:         form.value.social_website || null,
    }
    let saved
    if (editing.value) {
      const res = await api.put(`/ads/${form.value.id}`, payload)
      saved = res.data
      showToast("Pauta actualizada", "success")
    } else {
      const res = await api.post("/ads/", payload)
      saved = res.data
      form.value.id = saved.id
      editing.value = true
      showToast("Pauta creada — ahora puedes agregar piezas y el comprobante", "success", 3000)
    }
    form.value.pieces = saved.pieces || []
    await loadAll()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error al guardar la pauta", "error", 3500)
  } finally {
    saving.value = false
  }
}

// ── Piezas ─────────────────────────────────────────────────────────────────
async function uploadPiece(e) {
  const file = e.target.files[0]
  e.target.value = ""
  if (!file) return
  saving.value = true
  try {
    const fd = new FormData()
    fd.append("file", file)
    // NO fijar Content-Type manualmente — Axios lo setea con boundary correcto
    const res = await api.post(`/ads/${form.value.id}/pieces/upload`, fd)
    form.value.pieces.push(res.data)
    showToast("Pieza agregada", "success")
    await loadAll()
  } catch (err) {
    showToast(err.response?.data?.detail || "Error al subir el archivo", "error", 3500)
  } finally {
    saving.value = false
  }
}

async function addSocial() {
  const url = socialInput.value.trim()
  if (!url) return showToast("Pega la URL del video o publicación", "warning", 3000)
  const platform = detectPlatform(url)
  if (!platform) return showToast("URL no reconocida. Acepta YouTube, Instagram, TikTok o Facebook", "warning", 3500)
  saving.value = true
  try {
    const res = await api.post(`/ads/${form.value.id}/pieces/social`, { url, platform })
    form.value.pieces.push(res.data)
    showSocialForm.value = false
    socialInput.value = ""
    detectedPlatform.value = ""
    showToast(`${platformLabel(platform)} agregado`, "success")
    await loadAll()
  } catch (err) {
    showToast(err.response?.data?.detail || "Error al agregar video/social", "error", 3500)
  } finally {
    saving.value = false
  }
}

async function addText() {
  if (!textContent.value.trim()) return showToast("El texto no puede estar vacío", "warning")
  saving.value = true
  try {
    const res = await api.post(`/ads/${form.value.id}/pieces/text`, { text_content: textContent.value.trim() })
    form.value.pieces.push(res.data)
    showTextForm.value = false
    textContent.value = ""
    showToast("Texto agregado", "success")
    await loadAll()
  } catch (err) {
    showToast(err.response?.data?.detail || "Error al agregar texto", "error", 3500)
  } finally {
    saving.value = false
  }
}

async function deletePiece(piece, pi) {
  const { isConfirmed } = await window.Swal.fire({
    title: "¿Eliminar esta pieza?",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, eliminar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/ads/${form.value.id}/pieces/${piece.id}`)
    form.value.pieces.splice(pi, 1)
    showToast("Pieza eliminada", "success")
    await loadAll()
  } catch (err) {
    showToast(err.response?.data?.detail || "Error al eliminar pieza", "error", 3500)
  }
}

// ── Pago ───────────────────────────────────────────────────────────────────
async function uploadPayment(e) {
  const file = e.target.files[0]
  e.target.value = ""
  if (!file) return
  saving.value = true
  try {
    const fd = new FormData()
    fd.append("file", file)
    // NO fijar Content-Type manualmente — Axios lo setea con boundary correcto
    const res = await api.post(`/ads/${form.value.id}/payment`, fd)
    form.value.payment = res.data
    showToast("Comprobante de pago registrado", "success")
    await loadAll()
  } catch (err) {
    showToast(err.response?.data?.detail || "Error al subir el comprobante", "error", 3500)
  } finally {
    saving.value = false
  }
}

// ── Eliminación y renovación ───────────────────────────────────────────────
async function deleteAd(ad) {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar la pauta?`,
    text: `"${ad.title}"`,
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, eliminar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/ads/${ad.id}`)
    showToast("Pauta eliminada", "success")
    await loadAll()
  } catch (err) {
    showToast(err.response?.data?.detail || "Error al eliminar", "error", 3500)
  }
}

async function confirmRenew() {
  if (!renewForm.value.start_date || !renewForm.value.end_date)
    return showToast("Las fechas son requeridas", "warning")
  saving.value = true
  try {
    await api.post(`/ads/${renewTarget.value.id}/renew`, renewForm.value)
    showRenewModal.value = false
    showToast("Pauta renovada exitosamente", "success")
    await loadAll()
  } catch (err) {
    showToast(err.response?.data?.detail || "Error al renovar", "error", 3500)
  } finally {
    saving.value = false
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────
function statusLabel(s) {
  return { pending:"Pendiente", approved:"Aprobada", active:"Activa",
           paused:"Pausada", expired:"Expirada", rejected:"Rechazada" }[s] || s
}
function payStatusLabel(s) {
  return { pending:"Pendiente", verified:"Verificado", rejected:"Rechazado" }[s] || s
}
function pieceLabel(p) {
  if (p.piece_type === "image")   return "Imagen"
  if (p.piece_type === "video")   return "Video"
  if (p.piece_type === "youtube") return `YouTube: ${p.youtube_id}`
  if (p.piece_type === "social")  return `${platformLabel(p.social_platform)}: ${(p.media_url||"").slice(0,35)}...`
  if (p.piece_type === "text")    return `Texto: ${(p.text_content || "").slice(0, 30)}...`
  return p.piece_type
}
function fmtDate(d) {
  if (!d) return "—"
  const [y, m, dd] = d.split("-")
  return `${dd}/${m}/${y}`
}
function fmtPrice(n) {
  if (!n) return "0"
  return new Intl.NumberFormat("es-CO").format(n)
}

onMounted(loadAll)
</script>

<style scoped>
.myads-root { padding: 16px; max-width: 1100px; margin: 0 auto; }

/* KPI Bar */
.kpi-bar { display: flex; gap: 12px; margin-bottom: 18px; flex-wrap: wrap; }
.kpi-card {
  flex: 1; min-width: 110px; background: var(--card-bg, #fff);
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
  background: var(--card-bg, #fff); border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0,0,0,.08); overflow-x: auto;
}
.empty-state { text-align: center; padding: 40px 20px; color: #9ca3af; display: flex; flex-direction: column; align-items: center; gap: 8px; }
.ads-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.ads-table th { padding: 10px 12px; background: rgba(0,0,0,.04); font-weight: 700; text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: .4px; white-space: nowrap; }
.ads-table td { padding: 10px 12px; border-top: 1px solid rgba(0,0,0,.06); vertical-align: middle; }
.td-title   { max-width: 180px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.td-center  { text-align: center; }
.td-actions { display: flex; gap: 4px; }

.status-badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 700; }
.status-badge.pending  { background: rgba(245,158,11,.15); color: #d97706; }
.status-badge.approved { background: rgba(59,130,246,.15); color: #2563eb; }
.status-badge.active   { background: rgba(34,197,94,.15);  color: #16a34a; }
.status-badge.paused   { background: rgba(107,114,128,.15); color: #6b7280; }
.status-badge.expired  { background: rgba(107,114,128,.1);  color: #9ca3af; }
.status-badge.rejected { background: rgba(239,68,68,.15);  color: #dc2626; }

.btn-act { width: 28px; height: 28px; border: none; border-radius: 6px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 13px; }
.btn-view  { background: rgba(59,130,246,.1);  color: #2563eb; }
.btn-edit  { background: rgba(245,158,11,.1);  color: #d97706; }
.btn-renew { background: rgba(34,197,94,.1);   color: #16a34a; }
.btn-del   { background: rgba(239,68,68,.1);   color: #dc2626; }

/* Modal */
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,.5); display: flex; align-items: center; justify-content: center; z-index: 3000; padding: 16px; }
.modal-box { background: var(--card-bg, #fff); border-radius: 14px; width: 100%; max-width: 560px; max-height: 90vh; overflow-y: auto; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,.3); }
.modal-sm  { max-width: 400px; }
.modal-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid rgba(0,0,0,.08); flex-shrink: 0; }
.modal-title  { font-size: 15px; font-weight: 700; margin: 0; }
.btn-close-modal { background: none; border: none; font-size: 16px; cursor: pointer; opacity: .5; }
.btn-close-modal:hover { opacity: 1; }
.modal-body   { padding: 16px 20px; flex: 1; overflow-y: auto; }
.modal-footer { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 20px; border-top: 1px solid rgba(0,0,0,.08); flex-shrink: 0; }
.btn-cancel { background: none; border: 1px solid rgba(0,0,0,.15); border-radius: 7px; padding: 7px 16px; font-size: 13px; cursor: pointer; }
.btn-save   { background: #2563eb; color: #fff; border: none; border-radius: 7px; padding: 7px 18px; font-size: 13px; font-weight: 700; cursor: pointer; }
.btn-save:disabled { opacity: .5; cursor: not-allowed; }

/* Company info bar */
.company-info-bar {
  display: flex; align-items: center; gap: 6px;
  background: rgba(37,99,235,.07); border: 1px solid rgba(37,99,235,.15);
  border-radius: 8px; padding: 8px 12px; font-size: 13px; margin-bottom: 4px;
}
.ci-label { font-weight: 600; opacity: .7; }
.ci-name  { font-weight: 700; color: #2563eb; }

/* Price display */
.price-display {
  display: flex; align-items: center; gap: 4px;
  background: rgba(16,185,129,.08); border: 1px solid rgba(16,185,129,.2);
  border-radius: 6px; padding: 7px 10px; font-size: 13px; min-height: 36px;
}
.price-val { font-weight: 800; color: #059669; font-size: 15px; }
.price-cur { font-size: 10px; font-weight: 600; opacity: .6; }

/* Form */
.form-section-label { font-size: 10px; font-weight: 700; letter-spacing: .5px; text-transform: uppercase; opacity: .5; margin-bottom: 8px; margin-top: 4px; }
.pieces-hint { font-weight: 400; margin-left: 6px; }
.form-row   { margin-bottom: 10px; }
.form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }
.form-lbl   { font-size: 11px; font-weight: 600; display: block; margin-bottom: 4px; opacity: .75; }
.form-ctrl  { width: 100%; border: 1px solid rgba(0,0,0,.15); border-radius: 6px; padding: 7px 10px; font-size: 13px; background: transparent; color: inherit; box-sizing: border-box; }
.form-ctrl:focus { outline: none; border-color: #2563eb; }
.mt-2 { margin-top: 8px; }
.mt-3 { margin-top: 14px; }

/* Pieces */
.pieces-list { display: flex; flex-direction: column; gap: 6px; margin-bottom: 8px; }
.piece-item  { display: flex; align-items: center; gap: 8px; background: rgba(0,0,0,.04); border-radius: 7px; padding: 6px 10px; }
.piece-preview { width: 36px; height: 36px; border-radius: 6px; overflow: hidden; flex-shrink: 0; background: rgba(0,0,0,.08); display: flex; align-items: center; justify-content: center; }
.piece-thumb { width: 100%; height: 100%; object-fit: cover; }
.piece-icon  { font-size: 18px; color: #3b82f6; }
.piece-icon.yt     { color: #ef4444; }
.piece-icon.social { color: #e1306c; }
.piece-icon.txt    { color: #8b5cf6; }
.piece-label { flex: 1; font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.btn-del-piece { background: none; border: none; color: #dc2626; cursor: pointer; font-size: 14px; }

.add-piece-row { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; }
.btn-add-piece {
  display: flex; align-items: center; gap: 4px; padding: 6px 12px;
  border: 1.5px dashed rgba(0,0,0,.2); border-radius: 7px; font-size: 12px;
  cursor: pointer; background: transparent; color: inherit; transition: border-color .15s;
}
.btn-add-piece:hover  { border-color: #2563eb; color: #2563eb; }
.btn-add-piece.uploading { opacity: .5; cursor: not-allowed; }
.hidden-input { display: none; }

.pieces-note { font-size: 11px; color: #6b7280; background: rgba(0,0,0,.04); padding: 8px 10px; border-radius: 6px; margin-bottom: 8px; }

.sub-form { background: rgba(0,0,0,.04); border-radius: 8px; padding: 10px; margin-bottom: 8px; display: flex; flex-direction: column; gap: 8px; }
.yt-input-wrap { display: flex; flex-direction: column; gap: 4px; }
.yt-hint { font-size: 10px; opacity: .5; margin: 0; }
.sub-actions { display: flex; gap: 8px; }
.btn-sub-save   { background: #2563eb; color: #fff; border: none; border-radius: 6px; padding: 6px 12px; font-size: 12px; cursor: pointer; white-space: nowrap; }
.btn-sub-save:disabled { opacity: .5; cursor: not-allowed; }
.btn-sub-cancel { background: none; border: 1px solid rgba(0,0,0,.15); border-radius: 6px; padding: 6px 12px; font-size: 12px; cursor: pointer; white-space: nowrap; }

.payment-status { font-size: 12px; margin-bottom: 8px; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.pay-status-badge { padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 700; }
.pay-status-badge.pending  { background: rgba(245,158,11,.15); color: #d97706; }
.pay-status-badge.verified { background: rgba(34,197,94,.15);  color: #16a34a; }
.pay-status-badge.rejected { background: rgba(239,68,68,.15);  color: #dc2626; }
.btn-ver-comp { font-size: 11px; color: #2563eb; text-decoration: none; display: flex; align-items: center; }

.rejection-box { background: rgba(239,68,68,.08); border: 1px solid rgba(239,68,68,.2); border-radius: 8px; padding: 10px 12px; font-size: 12px; color: #dc2626; margin-top: 10px; }
.info-box { background: rgba(34,197,94,.08); border: 1px solid rgba(34,197,94,.2); border-radius: 8px; padding: 8px 12px; font-size: 12px; color: #16a34a; margin-bottom: 8px; display: flex; align-items: center; }
.platform-detect { display: flex; align-items: center; gap: 6px; font-size: 11px; font-weight: 600; color: #2563eb; margin-top: 4px; }
.social-fields { display: flex; flex-direction: column; gap: 6px; margin-bottom: 4px; }
.social-field { display: flex; align-items: center; gap: 8px; }
.social-icon-lbl { width: 24px; text-align: center; font-size: 16px; flex-shrink: 0; }

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
