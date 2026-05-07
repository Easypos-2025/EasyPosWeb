<template>
  <div class="amg-wrap">

    <!-- GRID DE ARCHIVOS EXISTENTES -->
    <div v-if="media.length > 0" class="amg-grid">
      <div v-for="m in media" :key="m.id" class="amg-item">

        <!-- IMAGEN -->
        <template v-if="m.file_type === 'image'">
          <img :src="m.file_url" class="amg-thumb" @click="openLightbox(m)" loading="lazy" />
        </template>

        <!-- VIDEO -->
        <template v-else>
          <div class="amg-video-thumb" @click="openLightbox(m)">
            <i class="bi bi-play-circle-fill"></i>
            <span class="amg-video-label">{{ m.file_name }}</span>
          </div>
        </template>

        <!-- BOTÓN ELIMINAR -->
        <button class="amg-del" @click.stop="remove(m)" title="Eliminar">
          <i class="bi bi-trash-fill"></i>
        </button>

        <!-- INDICADOR TIPO -->
        <span class="amg-type-badge">
          <i :class="m.file_type === 'image' ? 'bi bi-image' : 'bi bi-camera-video'"></i>
        </span>
      </div>
    </div>

    <div v-else class="amg-empty">
      <i class="bi bi-images"></i>
      <p>Sin fotos aún. Sube la primera imagen.</p>
    </div>

    <!-- ZONA DE UPLOAD -->
    <div v-if="media.length < MAX_FILES && !uploading" class="amg-upload-area">
      <label
        class="amg-drop-zone"
        :class="{ dragging: isDragging }"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="onDrop"
      >
        <i class="bi bi-cloud-arrow-up"></i>
        <span class="dz-title">Arrastra o toca para subir</span>
        <span class="dz-hint">JPG, PNG, WEBP, GIF — máx. 10 MB · MP4, MOV — máx. 100 MB</span>
        <span class="dz-count">{{ media.length }} / {{ MAX_FILES }} archivos</span>
        <input
          ref="fileInput"
          type="file"
          :accept="ACCEPT"
          @change="onFileChange"
          hidden
        />
      </label>
      <!-- Captura cámara en móvil -->
      <label v-if="isMobile" class="amg-camera-btn">
        <i class="bi bi-camera"></i> Tomar foto
        <input type="file" accept="image/*" capture="environment" @change="onFileChange" hidden />
      </label>
    </div>

    <!-- BARRA DE PROGRESO -->
    <div v-if="uploading" class="amg-progress-wrap">
      <div class="amg-progress-bar" :style="{ width: progress + '%' }"></div>
      <span class="amg-progress-label">Subiendo... {{ progress }}%</span>
    </div>

    <!-- LÍMITE ALCANZADO -->
    <div v-if="media.length >= MAX_FILES" class="amg-limit-msg">
      <i class="bi bi-info-circle"></i>
      Límite de {{ MAX_FILES }} archivos alcanzado. Elimina uno para agregar más.
    </div>

    <!-- LIGHTBOX -->
    <teleport to="body">
      <div v-if="lightbox" class="amg-lightbox" @click.self="lightbox = null">
        <button class="amg-lb-close" @click="lightbox = null"><i class="bi bi-x-lg"></i></button>

        <button v-if="lightboxIndex > 0" class="amg-lb-nav amg-lb-prev" @click="lightboxPrev">
          <i class="bi bi-chevron-left"></i>
        </button>
        <button v-if="lightboxIndex < media.length - 1" class="amg-lb-nav amg-lb-next" @click="lightboxNext">
          <i class="bi bi-chevron-right"></i>
        </button>

        <div class="amg-lb-content">
          <img v-if="lightbox.file_type === 'image'" :src="lightbox.file_url" class="amg-lb-img" />
          <video v-else :src="lightbox.file_url" controls class="amg-lb-video" autoplay />
          <p class="amg-lb-name">{{ lightbox.file_name }}</p>
        </div>
      </div>
    </teleport>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

const props = defineProps({
  assetId: { type: Number, required: true },
})

const MAX_FILES = 20
const ACCEPT    = "image/jpeg,image/png,image/webp,image/gif,video/mp4,video/quicktime,video/webm,video/avi"

const media      = ref([])
const uploading  = ref(false)
const progress   = ref(0)
const isDragging = ref(false)
const lightbox   = ref(null)
const lightboxIndex = ref(0)
const fileInput  = ref(null)

const isMobile = computed(() => /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent))

function fullMediaUrl(u) {
  if (!u) return ""
  if (/^https?:\/\//i.test(u)) return u
  const base = import.meta.env.VITE_API_URL || ""
  return `${base}${u.startsWith("/") ? u : "/" + u}`
}

async function load() {
  try {
    const res = await api.get(`/asset-media/${props.assetId}`)
    media.value = res.data.map(m => ({ ...m, file_url: fullMediaUrl(m.file_url) }))
  } catch {
    showToast("Error cargando archivos del activo", "error")
  }
}

function openLightbox(m) {
  lightboxIndex.value = media.value.findIndex(x => x.id === m.id)
  lightbox.value = m
}
function lightboxPrev() {
  if (lightboxIndex.value > 0) {
    lightboxIndex.value--
    lightbox.value = media.value[lightboxIndex.value]
  }
}
function lightboxNext() {
  if (lightboxIndex.value < media.value.length - 1) {
    lightboxIndex.value++
    lightbox.value = media.value[lightboxIndex.value]
  }
}

function onDrop(e) {
  isDragging.value = false
  const file = e.dataTransfer.files[0]
  if (file) uploadFile(file)
}

function onFileChange(e) {
  const file = e.target.files[0]
  if (file) uploadFile(file)
  e.target.value = ""
}

async function uploadFile(file) {
  if (media.value.length >= MAX_FILES) {
    showToast(`Límite de ${MAX_FILES} archivos alcanzado`, "warning")
    return
  }

  const ALLOWED = ["image/jpeg","image/png","image/webp","image/gif","video/mp4","video/quicktime","video/webm","video/avi"]
  if (!ALLOWED.includes(file.type)) {
    showToast("Formato no permitido. Usa JPG, PNG, WEBP, GIF, MP4 o MOV", "error")
    return
  }

  const isVideo    = file.type.startsWith("video/")
  const limitBytes = isVideo ? 100 * 1024 * 1024 : 10 * 1024 * 1024
  if (file.size > limitBytes) {
    showToast(`El archivo supera el límite de ${isVideo ? "100" : "10"} MB`, "error")
    return
  }

  uploading.value = true
  progress.value  = 0

  try {
    const fd = new FormData()
    fd.append("file", file)
    await api.post(`/asset-media/${props.assetId}`, fd, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (e) => {
        if (e.total) progress.value = Math.round((e.loaded / e.total) * 100)
      },
    })
    showToast("Archivo subido correctamente", "success")
    await load()
  } catch (err) {
    showToast(err.response?.data?.detail || "Error subiendo archivo", "error")
  } finally {
    uploading.value = false
    progress.value  = 0
  }
}

async function remove(m) {
  const { isConfirmed } = await window.Swal.fire({
    title: "¿Eliminar archivo?",
    text: m.file_name,
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, eliminar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#ef4444",
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/asset-media/${m.id}`)
    showToast("Archivo eliminado", "success")
    if (lightbox.value?.id === m.id) lightbox.value = null
    await load()
  } catch (err) {
    showToast(err.response?.data?.detail || "Error eliminando archivo", "error")
  }
}

watch(() => props.assetId, (id) => { if (id) load() })
onMounted(() => { if (props.assetId) load() })
</script>

<style scoped>
.amg-wrap { display: flex; flex-direction: column; gap: 14px; }

/* Grid */
.amg-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  gap: 10px;
}
.amg-item {
  position: relative;
  border-radius: 10px;
  overflow: hidden;
  background: #f1f5f9;
  aspect-ratio: 1;
  cursor: pointer;
}
.amg-item:hover .amg-del { opacity: 1; }
.amg-thumb {
  width: 100%; height: 100%;
  object-fit: cover;
  transition: transform .2s;
}
.amg-item:hover .amg-thumb { transform: scale(1.04); }

.amg-video-thumb {
  width: 100%; height: 100%;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 6px; background: #1e293b; color: #fff;
}
.amg-video-thumb .bi { font-size: 28px; color: #60a5fa; }
.amg-video-label { font-size: 10px; color: #94a3b8; padding: 0 6px; text-align: center; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 100%; }

.amg-del {
  position: absolute; top: 5px; right: 5px;
  background: rgba(239,68,68,.85); border: none; border-radius: 6px;
  color: #fff; width: 26px; height: 26px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; font-size: 12px;
  opacity: 0; transition: opacity .15s;
  z-index: 2;
}
.amg-del:hover { background: #ef4444; }

.amg-type-badge {
  position: absolute; bottom: 5px; left: 5px;
  background: rgba(0,0,0,.55); color: #fff;
  border-radius: 4px; padding: 2px 5px; font-size: 11px;
}

/* Empty */
.amg-empty {
  text-align: center; color: #94a3b8; padding: 24px 0; font-size: 14px;
}
.amg-empty .bi { font-size: 32px; display: block; margin-bottom: 8px; }

/* Upload zone */
.amg-upload-area { display: flex; flex-direction: column; gap: 8px; }
.amg-drop-zone {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 4px; padding: 18px 12px;
  border: 2px dashed #cbd5e1; border-radius: 10px;
  cursor: pointer; transition: border-color .15s, background .15s;
  background: #f8fafc; color: #64748b; text-align: center;
}
.amg-drop-zone:hover, .amg-drop-zone.dragging {
  border-color: #3b82f6; background: #eff6ff;
}
.amg-drop-zone .bi { font-size: 26px; color: #3b82f6; }
.dz-title { font-size: 14px; font-weight: 600; color: #374151; }
.dz-hint  { font-size: 11px; color: #94a3b8; }
.dz-count { font-size: 11px; font-weight: 600; color: #3b82f6; }

.amg-camera-btn {
  display: flex; align-items: center; justify-content: center; gap: 6px;
  padding: 9px; border: 1px solid #e2e8f0; border-radius: 8px;
  background: #f8fafc; font-size: 13px; font-weight: 600; color: #475569;
  cursor: pointer; transition: background .15s;
}
.amg-camera-btn:hover { background: #e2e8f0; }

/* Progress */
.amg-progress-wrap {
  background: #f1f5f9; border-radius: 8px; overflow: hidden; height: 28px;
  position: relative;
}
.amg-progress-bar {
  height: 100%; background: linear-gradient(90deg, #3b82f6, #06b6d4);
  transition: width .2s; border-radius: 8px;
}
.amg-progress-label {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 600; color: #1e293b;
}

/* Limit msg */
.amg-limit-msg {
  background: #fff7ed; border: 1px solid #fed7aa; border-radius: 8px;
  padding: 10px 14px; font-size: 13px; color: #9a3412;
  display: flex; align-items: center; gap: 8px;
}

/* Lightbox */
.amg-lightbox {
  position: fixed; inset: 0; background: rgba(0,0,0,.92);
  display: flex; align-items: center; justify-content: center;
  z-index: 9999; padding: 20px;
}
.amg-lb-close {
  position: absolute; top: 16px; right: 16px;
  background: rgba(255,255,255,.15); border: none; border-radius: 8px;
  color: #fff; width: 38px; height: 38px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; font-size: 18px; transition: background .15s;
}
.amg-lb-close:hover { background: rgba(255,255,255,.3); }

.amg-lb-nav {
  position: absolute; top: 50%; transform: translateY(-50%);
  background: rgba(255,255,255,.15); border: none; border-radius: 8px;
  color: #fff; width: 44px; height: 44px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; font-size: 20px; transition: background .15s;
}
.amg-lb-nav:hover { background: rgba(255,255,255,.3); }
.amg-lb-prev { left: 16px; }
.amg-lb-next { right: 16px; }

.amg-lb-content { display: flex; flex-direction: column; align-items: center; gap: 10px; max-width: 90vw; }
.amg-lb-img   { max-width: 88vw; max-height: 82vh; border-radius: 10px; object-fit: contain; }
.amg-lb-video { max-width: 88vw; max-height: 80vh; border-radius: 10px; }
.amg-lb-name  { color: #94a3b8; font-size: 12px; margin: 0; }

@media (max-width: 576px) {
  .amg-grid { grid-template-columns: repeat(3, 1fr); }
}
</style>
