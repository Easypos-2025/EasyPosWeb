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
            <i class="bi bi-camera"></i> Evidencias
          </h1>
          <p class="page-subtitle" v-if="task">
            Tarea: <strong>{{ task.title }}</strong>
          </p>
        </div>
      </div>
      <button class="btn btn-primary" @click="showForm = !showForm">
        <i class="bi" :class="showForm ? 'bi-x-lg' : 'bi-plus-lg'"></i>
        {{ showForm ? 'Cerrar formulario' : 'Agregar evidencia' }}
      </button>
    </div>

    <!-- FORMULARIO NUEVA EVIDENCIA (componente unificado) -->
    <transition name="slide">
      <div v-if="showForm" class="evidence-form-card">
        <h3 class="form-title">Nueva evidencia</h3>
        <EvidenceUploader :task-id="taskId" @uploaded="onUploaded" />
      </div>
    </transition>

    <!-- GALERÍA DE EVIDENCIAS -->
    <div v-if="loading" class="loading-center">
      <i class="bi bi-arrow-repeat spin"></i> Cargando evidencias...
    </div>

    <div v-else-if="evidences.length === 0 && !showForm" class="empty-state">
      <i class="bi bi-camera-video-off"></i>
      <p>Esta tarea aún no tiene evidencias registradas</p>
      <button class="btn btn-primary mt-3" @click="showForm = true">
        <i class="bi bi-plus-lg"></i> Agregar primera evidencia
      </button>
    </div>

    <div v-else-if="evidences.length > 0" class="evidence-gallery">

      <!-- Filtro por tipo -->
      <div class="gallery-tabs">
        <button class="gtab" :class="{ active: galleryTab === 'all' }" @click="galleryTab = 'all'">
          Todas ({{ evidences.length }})
        </button>
        <button v-for="t in usedTypes" :key="t.value"
          class="gtab" :class="{ active: galleryTab === t.value }"
          @click="galleryTab = t.value"
        >
          <i :class="'bi ' + t.icon"></i> {{ t.label }} ({{ typeCount(t.value) }})
        </button>
      </div>

      <!-- IMÁGENES -->
      <div v-if="hasType('image')" class="gallery-section">
        <h4 class="gallery-section-title"><i class="bi bi-image"></i> Imágenes</h4>
        <div class="img-grid">
          <div v-for="ev in byType('image')" :key="ev.id" class="img-thumb-wrap">
            <img
              :src="apiBase + ev.file_path"
              class="img-thumb"
              @click="openLightbox(apiBase + ev.file_path)"
            />
            <p v-if="ev.description" class="thumb-desc">{{ ev.description }}</p>
            <span class="thumb-date">{{ fmtDate(ev.created_at) }}</span>
            <button v-if="!isWorker" class="btn-del-ev" @click="deleteEvidence(ev)" title="Eliminar">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </div>
      </div>

      <!-- VIDEOS -->
      <div v-if="hasType('video')" class="gallery-section">
        <h4 class="gallery-section-title"><i class="bi bi-play-circle"></i> Videos</h4>
        <div class="video-list">
          <div v-for="ev in byType('video')" :key="ev.id" class="video-item">
            <video :src="apiBase + ev.file_path" controls class="video-player" />
            <div class="media-meta">
              <p v-if="ev.description">{{ ev.description }}</p>
              <span>{{ fmtDate(ev.created_at) }}</span>
              <button v-if="!isWorker" class="btn-del-ev" @click="deleteEvidence(ev)">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- AUDIOS -->
      <div v-if="hasType('audio')" class="gallery-section">
        <h4 class="gallery-section-title"><i class="bi bi-music-note-beamed"></i> Audios</h4>
        <div class="audio-list">
          <div v-for="ev in byType('audio')" :key="ev.id" class="audio-item">
            <i class="bi bi-music-note-beamed audio-icon"></i>
            <div class="audio-content">
              <p v-if="ev.description" class="audio-desc">{{ ev.description }}</p>
              <audio :src="apiBase + ev.file_path" controls />
              <span class="thumb-date">{{ fmtDate(ev.created_at) }}</span>
            </div>
            <button v-if="!isWorker" class="btn-del-ev" @click="deleteEvidence(ev)">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </div>
      </div>

      <!-- TEXTOS -->
      <div v-if="hasType('text')" class="gallery-section">
        <h4 class="gallery-section-title"><i class="bi bi-text-paragraph"></i> Notas de texto</h4>
        <div class="text-list">
          <div v-for="ev in byType('text')" :key="ev.id" class="text-item">
            <div class="text-body">{{ ev.description }}</div>
            <div class="text-footer">
              <span>{{ fmtDate(ev.created_at) }}</span>
              <button v-if="!isWorker" class="btn-del-ev" @click="deleteEvidence(ev)">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </div>
        </div>
      </div>

    </div>

    <!-- LIGHTBOX -->
    <div v-if="lightboxUrl" class="lightbox" @click="lightboxUrl = ''">
      <img :src="lightboxUrl" class="lightbox-img" />
      <button class="lightbox-close"><i class="bi bi-x-lg"></i></button>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { useRoute } from "vue-router"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import EvidenceUploader from "@/components/EvidenceUploader.vue"

const route    = useRoute()
const taskId   = route.params.taskId
const apiBase  = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"

const userInfo = JSON.parse(localStorage.getItem("user") || "{}")
const isWorker = (userInfo.role || "").toLowerCase().includes("worker")

const task        = ref(null)
const evidences   = ref([])
const loading     = ref(true)
const showForm    = ref(false)
const galleryTab  = ref("all")
const lightboxUrl = ref("")

const allTypes = [
  { value: "image", label: "Imagen", icon: "bi-image"          },
  { value: "video", label: "Video",  icon: "bi-play-circle"    },
  { value: "audio", label: "Audio",  icon: "bi-music-note-beamed" },
  { value: "text",  label: "Texto",  icon: "bi-text-paragraph" },
]

const usedTypes = computed(() =>
  allTypes.filter(t => evidences.value.some(e => e.file_type === t.value))
)

function typeCount(type) { return evidences.value.filter(e => e.file_type === type).length }
function hasType(type) {
  return galleryTab.value === "all"
    ? evidences.value.some(e => e.file_type === type)
    : galleryTab.value === type && evidences.value.some(e => e.file_type === type)
}
function byType(type) { return evidences.value.filter(e => e.file_type === type) }
function fmtDate(iso) {
  if (!iso) return ""
  return new Date(iso).toLocaleString("es-CO", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit"
  })
}

function openLightbox(url) { lightboxUrl.value = url }

async function load() {
  loading.value = true
  try {
    const [taskRes, evRes] = await Promise.all([
      api.get(`/tasks/${taskId}`),
      api.get(`/task-evidence/${taskId}`)
    ])
    task.value      = taskRes.data
    evidences.value = evRes.data
  } catch {
    showToast("Error cargando evidencias", "error")
  } finally {
    loading.value = false
  }
}

async function onUploaded() {
  showForm.value = false
  const res      = await api.get(`/task-evidence/${taskId}`)
  evidences.value = res.data
}

async function deleteEvidence(ev) {
  const { isConfirmed } = await window.Swal.fire({
    title: "¿Eliminar evidencia?",
    text:  "Se borrará el archivo del servidor.",
    icon:  "warning",
    showCancelButton: true,
    confirmButtonText: "Eliminar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/task-evidence/${ev.id}`)
    showToast("Evidencia eliminada", "success")
    const res = await api.get(`/task-evidence/${taskId}`)
    evidences.value = res.data
  } catch {
    showToast("Error eliminando", "error")
  }
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 960px; }
.page-header    { display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:20px; flex-wrap:wrap; gap:12px; }
.header-left    { display:flex; align-items:flex-start; gap:12px; }
.btn-back       { background:#f1f5f9; border:none; border-radius:8px; padding:8px 12px; cursor:pointer; font-size:16px; color:#475569; }
.btn-back:hover { background:#e2e8f0; }
.page-title     { font-size:20px; font-weight:700; color:#1e293b; display:flex; align-items:center; gap:8px; margin:0 0 4px; }
.page-subtitle  { font-size:13px; color:#64748b; margin:0; }

/* FORM CARD */
.evidence-form-card { background:#fff; border-radius:14px; box-shadow:0 1px 6px rgba(0,0,0,0.08); padding:20px 24px; margin-bottom:20px; }
.form-title { font-size:15px; font-weight:700; color:#1e293b; margin:0 0 14px; }

/* GALERÍA */
.loading-center { padding:60px; text-align:center; color:#94a3b8; }
.empty-state    { padding:60px; text-align:center; color:#94a3b8; }
.empty-state .bi { font-size:44px; display:block; margin-bottom:12px; }

.gallery-tabs { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:20px; }
.gtab {
  padding:6px 14px; border-radius:20px; border:1px solid #e2e8f0;
  background:#f8fafc; font-size:12px; font-weight:500; cursor:pointer;
  display:flex; align-items:center; gap:5px; transition:all 0.15s;
}
.gtab:hover  { border-color:#3b82f6; }
.gtab.active { background:#3b82f6; border-color:#3b82f6; color:#fff; }

.gallery-section { margin-bottom:28px; }
.gallery-section-title { font-size:14px; font-weight:700; color:#475569; display:flex; align-items:center; gap:7px; margin-bottom:14px; padding-bottom:8px; border-bottom:1px solid #f1f5f9; }

/* IMÁGENES */
.img-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(160px, 1fr)); gap:12px; }
.img-thumb-wrap { position:relative; border-radius:10px; overflow:hidden; background:#f8fafc; }
.img-thumb { width:100%; height:140px; object-fit:cover; cursor:zoom-in; display:block; transition:opacity 0.2s; }
.img-thumb:hover { opacity:0.88; }
.thumb-desc { font-size:11px; color:#64748b; padding:4px 8px; margin:0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.thumb-date { font-size:10px; color:#94a3b8; padding:0 8px 6px; display:block; }
.btn-del-ev { position:absolute; top:6px; right:6px; background:rgba(239,68,68,0.85); border:none; border-radius:6px; color:#fff; width:26px; height:26px; display:flex; align-items:center; justify-content:center; cursor:pointer; font-size:12px; opacity:0; transition:opacity 0.15s; }
.img-thumb-wrap:hover .btn-del-ev { opacity:1; }

/* VIDEOS */
.video-list { display:flex; flex-direction:column; gap:16px; }
.video-item { background:#f8fafc; border-radius:12px; overflow:hidden; display:flex; flex-direction:column; }
.video-player { width:100%; max-height:280px; background:#000; }
.media-meta  { padding:10px 14px; display:flex; align-items:center; gap:10px; font-size:13px; color:#64748b; }
.media-meta p { margin:0; flex:1; }
.media-meta .btn-del-ev { position:static; opacity:1; }

/* AUDIOS */
.audio-list { display:flex; flex-direction:column; gap:12px; }
.audio-item { background:#f8fafc; border-radius:12px; padding:14px 16px; display:flex; align-items:flex-start; gap:14px; }
.audio-icon { font-size:28px; color:#3b82f6; flex-shrink:0; margin-top:4px; }
.audio-content { flex:1; display:flex; flex-direction:column; gap:6px; }
.audio-content audio { width:100%; }
.audio-desc { font-size:13px; color:#1e293b; margin:0; }
.audio-item .btn-del-ev { position:static; opacity:1; align-self:flex-start; }

/* TEXTOS */
.text-list { display:flex; flex-direction:column; gap:12px; }
.text-item { background:#fffbeb; border:1px solid #fde68a; border-radius:12px; padding:16px; }
.text-body { font-size:14px; color:#1e293b; line-height:1.6; white-space:pre-wrap; }
.text-footer { display:flex; align-items:center; justify-content:space-between; margin-top:10px; }
.text-footer span { font-size:11px; color:#94a3b8; }
.text-footer .btn-del-ev { position:static; opacity:1; font-size:13px; width:28px; height:28px; }

/* LIGHTBOX */
.lightbox { position:fixed; inset:0; background:rgba(0,0,0,0.9); display:flex; align-items:center; justify-content:center; z-index:2000; cursor:zoom-out; }
.lightbox-img   { max-width:92vw; max-height:92vh; object-fit:contain; border-radius:4px; }
.lightbox-close { position:absolute; top:16px; right:20px; background:none; border:none; color:#fff; font-size:24px; cursor:pointer; }

/* TRANSITIONS */
.slide-enter-active, .slide-leave-active { transition:all 0.25s ease; }
.slide-enter-from, .slide-leave-to { opacity:0; transform:translateY(-10px); }

.spin { display:inline-block; animation:spin 0.8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
</style>
