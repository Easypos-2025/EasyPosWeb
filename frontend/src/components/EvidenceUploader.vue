<template>
  <div class="eu-wrap">

    <!-- SELECTOR DE TIPO -->
    <div class="type-selector">
      <button
        v-for="t in types" :key="t.value"
        class="type-btn"
        :class="{ active: currentType === t.value }"
        @click="selectType(t.value)"
      >
        <i :class="'bi ' + t.icon"></i>
        <span>{{ t.label }}</span>
      </button>
    </div>

    <!-- DESCRIPCIÓN -->
    <div class="eu-field">
      <label>
        {{ currentType === 'text' ? 'Texto de la evidencia *' : 'Descripción (opcional)' }}
      </label>
      <textarea
        v-model="description"
        class="form-control"
        :rows="currentType === 'text' ? 3 : 2"
        :placeholder="currentType === 'text'
          ? 'Escribe aquí la descripción detallada de la evidencia...'
          : 'Agrega una descripción al archivo...'"
      ></textarea>
    </div>

    <!-- ÁREA DE ARCHIVO (no texto) -->
    <template v-if="currentType !== 'text'">

      <!-- INFO DE LÍMITES -->
      <div class="limits-bar">
        <i class="bi bi-info-circle"></i>
        <span>{{ limitsInfo }}</span>
      </div>

      <!-- Zona de drop / selector -->
      <div v-if="!selectedFile && !previewUrl" class="eu-field">
        <label
          class="drop-zone"
          :class="{ dragging: isDragging }"
          @dragover.prevent="isDragging = true"
          @dragleave="isDragging = false"
          @drop.prevent="onDrop"
        >
          <i class="bi" :class="dropIcon"></i>
          <span class="dz-title">Arrastra aquí o toca para seleccionar</span>
          <span class="dz-hint">{{ dropHint }}</span>
          <input
            ref="fileInput"
            type="file"
            :accept="acceptAttr"
            @change="onFileChange"
            hidden
          />
        </label>

        <!-- Captura directa desde cámara / micrófono (solo móvil) -->
        <label v-if="isMobile" class="camera-capture-btn">
          <i class="bi" :class="cameraIcon"></i>
          {{ cameraBtnLabel }}
          <input
            ref="cameraInput"
            type="file"
            :accept="captureAcceptAttr"
            :capture="captureAttr"
            @change="onFileChange"
            hidden
          />
        </label>
      </div>

      <!-- Preview imagen -->
      <div v-if="currentType === 'image' && previewUrl" class="img-preview-wrap">
        <img :src="previewUrl" class="img-preview-thumb" />
        <div class="img-meta">
          <span v-if="originalSize" class="meta-badge meta-original">
            Original: {{ originalSize }}
          </span>
          <span v-if="compressedSize" class="meta-badge meta-compressed">
            Comprimida: {{ compressedSize }}
            <span v-if="savings > 0" class="savings">–{{ savings }}%</span>
          </span>
        </div>
        <div class="img-actions">
          <button class="btn-change" @click="openCropper">
            <i class="bi bi-crop"></i> Recortar
          </button>
          <button class="btn-change" @click="resetFile">
            <i class="bi bi-arrow-repeat"></i> Cambiar imagen
          </button>
        </div>
      </div>

      <!-- Preview video -->
      <div v-if="currentType === 'video' && selectedFile" class="media-preview-wrap">
        <video :src="previewUrl" controls class="video-preview" />
        <div class="media-info">
          <span class="meta-badge">{{ selectedFile.name }}</span>
          <span class="meta-badge" :class="fileSizeClass">{{ fileSize }}</span>
          <span v-if="mediaDuration" class="meta-badge">{{ mediaDuration }}</span>
        </div>
        <div v-if="sizeExceeded" class="size-warning">
          <i class="bi bi-exclamation-triangle-fill"></i>
          El video pesa <strong>{{ fileSize }}</strong> y supera el límite de
          <strong>{{ SIZE_LIMITS.video }} MB</strong>. Recórtalo en tu dispositivo antes de subirlo.
        </div>
        <button class="btn-change" @click="resetFile">
          <i class="bi bi-arrow-repeat"></i> Cambiar video
        </button>
      </div>

      <!-- Preview audio -->
      <div v-if="currentType === 'audio' && selectedFile" class="media-preview-wrap">
        <audio :src="previewUrl" controls class="audio-preview" @loadedmetadata="onAudioMeta" />
        <div class="media-info">
          <span class="meta-badge">{{ selectedFile.name }}</span>
          <span class="meta-badge" :class="fileSizeClass">{{ fileSize }}</span>
          <span v-if="mediaDuration" class="meta-badge">{{ mediaDuration }}</span>
        </div>
        <div v-if="sizeExceeded" class="size-warning">
          <i class="bi bi-exclamation-triangle-fill"></i>
          El audio pesa <strong>{{ fileSize }}</strong> y supera el límite de
          <strong>{{ SIZE_LIMITS.audio }} MB</strong>. Recórtalo en tu dispositivo antes de subirlo.
        </div>
        <button class="btn-change" @click="resetFile">
          <i class="bi bi-arrow-repeat"></i> Cambiar audio
        </button>
      </div>

    </template>

    <!-- BARRA DE PROGRESO -->
    <div v-if="uploading" class="progress-area">
      <div class="progress-track">
        <div class="progress-fill" :style="{ width: progress + '%' }"></div>
      </div>
      <span class="progress-label">{{ progress < 100 ? progress + '%' : 'Procesando...' }}</span>
    </div>

    <!-- BOTÓN GUARDAR -->
    <div class="eu-actions">
      <button class="btn btn-primary" @click="submit" :disabled="uploading || !canSubmit">
        <i v-if="uploading" class="bi bi-arrow-repeat spin"></i>
        <i v-else class="bi bi-cloud-upload"></i>
        {{ uploading ? 'Subiendo...' : 'Guardar evidencia' }}
      </button>
      <slot name="extra-actions" />
    </div>

    <!-- MODAL RECORTE DE IMAGEN -->
    <div v-if="showCropper" class="crop-overlay" @click.self="cancelCrop">
      <div class="crop-box">
        <div class="crop-header">
          <span class="crop-title"><i class="bi bi-crop"></i> Recortar imagen</span>
          <div class="crop-ratio-btns">
            <button :class="{ active: cropRatio === 0 }"    @click="cropRatio = 0">Libre</button>
            <button :class="{ active: cropRatio === 1 }"    @click="cropRatio = 1">1:1</button>
            <button :class="{ active: cropRatio === 16/9 }" @click="cropRatio = 16/9">16:9</button>
            <button :class="{ active: cropRatio === 4/3 }"  @click="cropRatio = 4/3">4:3</button>
          </div>
        </div>
        <div class="crop-area">
          <Cropper
            ref="cropperRef"
            :src="rawImageUrl"
            imageRestriction="none"
            :autoZoom="true"
            :stencil-props="{ movable: true, resizable: true, aspectRatio: cropRatio }"
          />
        </div>
        <div class="crop-actions">
          <button class="btn btn-secondary btn-sm" @click="skipCrop">
            <i class="bi bi-skip-forward"></i> Sin recorte
          </button>
          <button class="btn btn-primary btn-sm" @click="confirmCrop">
            <i class="bi bi-check-lg"></i> Confirmar recorte
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from "vue"
import { Cropper } from "vue-advanced-cropper"
import "vue-advanced-cropper/dist/style.css"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

// ── Props / Emits ────────────────────────────────────────────
const props = defineProps({
  taskId: { type: [Number, String], required: true },
})
const emit = defineEmits(["uploaded"])

// ── Límites y formatos permitidos ────────────────────────────
const SIZE_LIMITS = { image: 10, video: 50, audio: 15 }

const ALLOWED_FORMATS = {
  image: ["image/jpeg", "image/png", "image/webp", "image/gif"],
  video: ["video/mp4", "video/quicktime", "video/webm"],
  audio: ["audio/mpeg", "audio/mp4", "audio/ogg", "audio/wav", "audio/x-m4a", "audio/aac"],
}

// ── Estado ───────────────────────────────────────────────────
const currentType    = ref("image")
const description    = ref("")
const selectedFile   = ref(null)
const previewUrl     = ref("")
const compressedBlob = ref(null)
const originalSize   = ref("")
const compressedSize = ref("")
const savings        = ref(0)
const uploading      = ref(false)
const progress       = ref(0)
const isDragging     = ref(false)
const mediaDuration  = ref("")
const fileInput      = ref(null)
const cameraInput    = ref(null)
const isMobile       = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)

// ── Estado del cropper ───────────────────────────────────────
const showCropper  = ref(false)
const rawImageUrl  = ref("")
const cropperRef   = ref(null)
const cropRatio    = ref(0)

// ── Tipos de evidencia ────────────────────────────────────────
const types = [
  { value: "image", label: "Imagen", icon: "bi-image"          },
  { value: "video", label: "Video",  icon: "bi-play-circle"    },
  { value: "audio", label: "Audio",  icon: "bi-mic"            },
  { value: "text",  label: "Texto",  icon: "bi-text-paragraph" },
]

// ── Computed helpers ─────────────────────────────────────────
const acceptAttr = computed(() => ({
  image: "image/jpeg,image/png,image/webp,image/gif",
  video: "video/mp4,video/quicktime,video/webm",
  audio: "audio/mpeg,audio/mp4,audio/ogg,audio/wav",
}[currentType.value] || "*"))

const captureAttr = computed(() => ({
  image: "environment",
  video: "environment",
  audio: "microphone",
}[currentType.value] || "environment"))

const captureAcceptAttr = computed(() => ({
  image: "image/*",
  video: "video/*",
  audio: "audio/*",
}[currentType.value] || "*"))

const cameraBtnLabel = computed(() => ({
  image: "Tomar foto",
  video: "Grabar video",
  audio: "Grabar audio",
}[currentType.value] || "Capturar"))

const cameraIcon = computed(() => ({
  image: "bi-camera",
  video: "bi-camera-video",
  audio: "bi-mic-fill",
}[currentType.value] || "bi-camera"))

const dropIcon = computed(() => ({
  image: "bi-image",
  video: "bi-play-circle",
  audio: "bi-mic",
}[currentType.value] || "bi-file"))

const dropHint = computed(() => ({
  image: "JPG, PNG, WEBP, GIF",
  video: "MP4, MOV, WEBM",
  audio: "MP3, M4A, WAV, OGG",
}[currentType.value] || ""))

const limitsInfo = computed(() => ({
  image: `Imágenes — máx ${SIZE_LIMITS.image} MB. Podrás recortar antes de guardar.`,
  video: `Videos — máx ${SIZE_LIMITS.video} MB. Si supera el límite recórtalo antes en tu dispositivo.`,
  audio: `Audios — máx ${SIZE_LIMITS.audio} MB. Si supera el límite recórtalo antes en tu dispositivo.`,
}[currentType.value] || ""))

const fileSize = computed(() => selectedFile.value ? formatBytes(selectedFile.value.size) : "")

const fileSizeClass = computed(() => {
  if (!selectedFile.value) return ""
  const mb = selectedFile.value.size / (1024 * 1024)
  const limit = SIZE_LIMITS[currentType.value]
  return limit && mb > limit ? "meta-warn" : "meta-ok"
})

const sizeExceeded = computed(() => {
  if (!selectedFile.value) return false
  const limit = SIZE_LIMITS[currentType.value]
  return !!limit && selectedFile.value.size / 1024 / 1024 > limit
})

const canSubmit = computed(() => {
  if (currentType.value === "text") return description.value.trim().length > 0
  if (!selectedFile.value) return false
  if (sizeExceeded.value) return false
  return true
})

// ── Selección de tipo ─────────────────────────────────────────
function selectType(type) {
  currentType.value = type
  resetFile()
}

// ── Validación de formato ─────────────────────────────────────
function isValidFormat(file) {
  const allowed = ALLOWED_FORMATS[currentType.value]
  if (!allowed) return true
  if (allowed.includes(file.type)) return true
  const ext  = file.name.split(".").pop().toUpperCase()
  const list = allowed.map(t => t.split("/")[1].replace("quicktime", "MOV").toUpperCase()).join(", ")
  showToast(`Formato .${ext} no permitido. Usa: ${list}`, "error")
  return false
}

// ── Manejo de archivo ─────────────────────────────────────────
function onDrop(e) {
  isDragging.value = false
  const f = e.dataTransfer.files[0]
  if (f) processFile(f)
}

function onFileChange(e) {
  const f = e.target.files[0]
  if (f) processFile(f)
}

async function processFile(file) {
  if (!isValidFormat(file)) return

  selectedFile.value   = file
  compressedBlob.value = null
  previewUrl.value     = ""
  originalSize.value   = ""
  compressedSize.value = ""
  savings.value        = 0
  mediaDuration.value  = ""

  if (currentType.value === "image") {
    originalSize.value = formatBytes(file.size)
    rawImageUrl.value  = URL.createObjectURL(file)
    cropRatio.value    = 0
    showCropper.value  = true
  } else {
    previewUrl.value = URL.createObjectURL(file)
    if (sizeExceeded.value) {
      const limit = SIZE_LIMITS[currentType.value]
      showToast(
        `El archivo pesa ${formatBytes(file.size)} y supera el límite de ${limit} MB. Debes recortarlo antes de subirlo.`,
        "warning"
      )
    }
  }
}

function onAudioMeta(e) {
  const s = Math.round(e.target.duration)
  if (!isFinite(s)) return
  const m = Math.floor(s / 60)
  mediaDuration.value = `${m}:${String(s % 60).padStart(2, "0")} min`
}

function resetFile() {
  selectedFile.value   = null
  previewUrl.value     = ""
  rawImageUrl.value    = ""
  compressedBlob.value = null
  originalSize.value   = ""
  compressedSize.value = ""
  savings.value        = 0
  mediaDuration.value  = ""
  showCropper.value    = false
  if (fileInput.value)   fileInput.value.value   = ""
  if (cameraInput.value) cameraInput.value.value = ""
}

// ── Cropper ───────────────────────────────────────────────────
function openCropper() {
  cropRatio.value   = 0
  showCropper.value = true
}

function cancelCrop() {
  // Cerrar sin cambios si ya hay preview
  if (previewUrl.value) {
    showCropper.value = false
  } else {
    resetFile()
  }
}

async function confirmCrop() {
  if (!cropperRef.value) return
  const { canvas } = cropperRef.value.getResult()
  if (!canvas) return
  await applyCanvas(canvas)
  showCropper.value = false
}

async function skipCrop() {
  // Comprimir sin recortar
  try {
    const { blob, url } = await compressImage(selectedFile.value)
    compressedBlob.value = blob
    previewUrl.value     = url
    compressedSize.value = formatBytes(blob.size)
    savings.value = Math.round((1 - blob.size / selectedFile.value.size) * 100)
  } catch {
    previewUrl.value    = rawImageUrl.value
    compressedBlob.value = null
  }
  showCropper.value = false
}

async function applyCanvas(canvas) {
  const MAX = 1200
  let { width, height } = canvas
  if (width > MAX) {
    height = Math.round(height * (MAX / width))
    width  = MAX
  }
  const resized = document.createElement("canvas")
  resized.width  = width
  resized.height = height
  resized.getContext("2d").drawImage(canvas, 0, 0, width, height)

  await new Promise((resolve) => {
    resized.toBlob((blob) => {
      if (!blob) { resolve(); return }
      compressedBlob.value = blob
      previewUrl.value     = URL.createObjectURL(blob)
      compressedSize.value = formatBytes(blob.size)
      savings.value = Math.round((1 - blob.size / selectedFile.value.size) * 100)
      resolve()
    }, "image/jpeg", 0.82)
  })
}

// ── Compresión de imagen (full, sin recorte) ──────────────────
function compressImage(file, maxWidth = 1200, quality = 0.82) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const img = new Image()
      img.onload = () => {
        let { width, height } = img
        if (width > maxWidth) {
          height = Math.round(height * (maxWidth / width))
          width  = maxWidth
        }
        const canvas = document.createElement("canvas")
        canvas.width  = width
        canvas.height = height
        canvas.getContext("2d").drawImage(img, 0, 0, width, height)
        canvas.toBlob(
          (blob) => {
            if (!blob) { reject(new Error("No blob")); return }
            resolve({ blob, url: URL.createObjectURL(blob) })
          },
          "image/jpeg",
          quality
        )
      }
      img.onerror = reject
      img.src = e.target.result
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

// ── Submit ───────────────────────────────────────────────────
async function submit() {
  if (!canSubmit.value) return

  uploading.value = true
  progress.value  = 0

  try {
    const fd = new FormData()
    fd.append("file_type",   currentType.value)
    fd.append("description", description.value.trim())

    if (currentType.value !== "text") {
      const toUpload = (currentType.value === "image" && compressedBlob.value)
        ? new File([compressedBlob.value], selectedFile.value.name.replace(/\.\w+$/, ".jpg"), { type: "image/jpeg" })
        : selectedFile.value
      fd.append("file", toUpload)
    }

    await api.post(`/task-evidence/${props.taskId}`, fd, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (e) => {
        if (e.total) progress.value = Math.round((e.loaded / e.total) * 100)
      },
    })

    showToast("Evidencia guardada correctamente", "success")
    reset()
    emit("uploaded")

  } catch (err) {
    const status = err.response?.status
    const detail = err.response?.data?.detail

    if (status === 413) {
      showToast("El servidor rechazó el archivo: supera el tamaño máximo permitido.", "error")
    } else if (status === 415) {
      showToast("Formato de archivo no soportado por el servidor.", "error")
    } else if (status === 422) {
      showToast(detail || "El archivo no pasó la validación del servidor.", "error")
    } else if (detail) {
      showToast(detail, "error")
    } else if (!err.response) {
      showToast("Sin conexión con el servidor. Verifica tu red e intenta de nuevo.", "error")
    } else {
      showToast(`Error ${status || ""} al subir el archivo. Intenta de nuevo.`, "error")
    }
  } finally {
    uploading.value = false
    progress.value  = 0
  }
}

function reset() {
  resetFile()
  description.value = ""
  currentType.value = "image"
}

// ── Utilidades ───────────────────────────────────────────────
function formatBytes(bytes) {
  if (bytes < 1024)        return bytes + " B"
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB"
  return (bytes / (1024 * 1024)).toFixed(2) + " MB"
}
</script>

<style scoped>
.eu-wrap { display: flex; flex-direction: column; gap: 14px; }

/* TIPO */
.type-selector { display: flex; gap: 8px; flex-wrap: wrap; }
.type-btn {
  display: flex; align-items: center; gap: 6px; padding: 7px 14px;
  border: 1px solid #e2e8f0; border-radius: 20px; background: #f8fafc;
  font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.15s;
  white-space: nowrap;
}
.type-btn span { display: inline; }
.type-btn:hover  { border-color: #3b82f6; color: #3b82f6; }
.type-btn.active { background: #3b82f6; border-color: #3b82f6; color: #fff; }

/* CAMPO */
.eu-field label:not(.drop-zone) {
  font-size: 13px; font-weight: 600; color: #374151;
  display: block; margin-bottom: 4px;
}

/* BARRA DE LÍMITES */
.limits-bar {
  display: flex; align-items: flex-start; gap: 7px;
  padding: 8px 12px; background: #f0f9ff; border: 1px solid #bae6fd;
  border-radius: 8px; font-size: 12px; color: #0369a1; line-height: 1.4;
}
.limits-bar .bi { flex-shrink: 0; margin-top: 1px; }

/* DROP ZONE */
.drop-zone {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 8px; padding: 28px 20px; border: 2px dashed #cbd5e1; border-radius: 12px;
  cursor: pointer; transition: all 0.2s; color: #94a3b8; background: #f8fafc;
  text-align: center;
}
.drop-zone .bi { font-size: 32px; }
.drop-zone:hover, .drop-zone.dragging { border-color: #3b82f6; color: #3b82f6; background: #eff6ff; }
.dz-title { font-size: 14px; font-weight: 600; }
.dz-hint  { font-size: 12px; }

/* BOTÓN CAPTURA CÁMARA */
.camera-capture-btn {
  display: flex; align-items: center; justify-content: center;
  gap: 8px; padding: 11px 20px; margin-top: 10px;
  border: 2px solid #3b82f6; border-radius: 12px;
  background: #eff6ff; color: #2563eb;
  font-size: 14px; font-weight: 600; cursor: pointer;
  transition: all 0.18s; width: 100%;
}
.camera-capture-btn .bi { font-size: 18px; }
.camera-capture-btn:active { background: #3b82f6; color: #fff; }

/* PREVIEW IMAGEN */
.img-preview-wrap { display: flex; flex-direction: column; gap: 8px; }
.img-preview-thumb { width: 100%; max-height: 220px; object-fit: contain;
  border-radius: 10px; background: #f8fafc; border: 1px solid #e2e8f0; }
.img-meta { display: flex; gap: 8px; flex-wrap: wrap; }
.img-actions { display: flex; gap: 8px; flex-wrap: wrap; }

/* ADVERTENCIA TAMAÑO */
.size-warning {
  display: flex; align-items: flex-start; gap: 8px;
  padding: 10px 12px; background: #fef2f2; border: 1px solid #fca5a5;
  border-radius: 8px; font-size: 12px; color: #b91c1c; line-height: 1.4;
}
.size-warning .bi { flex-shrink: 0; margin-top: 1px; color: #ef4444; }

/* META BADGES */
.meta-badge {
  font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 20px;
  background: #f1f5f9; color: #475569;
}
.meta-original   { background: #fef9c3; color: #854d0e; }
.meta-compressed { background: #dcfce7; color: #166534; }
.meta-ok         { background: #dcfce7; color: #166534; }
.meta-warn       { background: #fef2f2; color: #b91c1c; }
.savings { font-weight: 700; margin-left: 4px; }

/* PREVIEW MEDIA */
.media-preview-wrap { display: flex; flex-direction: column; gap: 8px; }
.video-preview { width: 100%; max-height: 220px; border-radius: 10px; background: #000; }
.audio-preview { width: 100%; }
.media-info    { display: flex; gap: 8px; flex-wrap: wrap; }

.btn-change {
  align-self: flex-start; background: none; border: 1px solid #cbd5e1;
  border-radius: 8px; padding: 5px 12px; font-size: 12px; color: #64748b; cursor: pointer;
  display: flex; align-items: center; gap: 5px;
}
.btn-change:hover { background: #f1f5f9; }

/* PROGRESO */
.progress-area  { display: flex; align-items: center; gap: 10px; }
.progress-track { flex: 1; height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden; }
.progress-fill  { height: 100%; background: #3b82f6; border-radius: 4px; transition: width 0.3s; }
.progress-label { font-size: 13px; font-weight: 700; color: #3b82f6; min-width: 48px; text-align: right; }

/* ACCIONES */
.eu-actions { display: flex; gap: 10px; align-items: center; }

/* MODAL RECORTE */
.crop-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.7);
  display: flex; align-items: center; justify-content: center;
  z-index: 2000; padding: 16px;
}
.crop-box {
  background: #fff; border-radius: 16px; width: 100%; max-width: 680px;
  max-height: 90vh; display: flex; flex-direction: column;
  box-shadow: 0 25px 60px rgba(0,0,0,0.35); overflow: hidden;
}
.crop-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px; border-bottom: 1px solid #f1f5f9; flex-wrap: wrap; gap: 8px;
}
.crop-title { font-size: 15px; font-weight: 700; color: #1e293b; display: flex; align-items: center; gap: 7px; }
.crop-ratio-btns { display: flex; gap: 6px; }
.crop-ratio-btns button {
  padding: 4px 12px; border-radius: 20px; border: 1px solid #e2e8f0;
  background: #f8fafc; font-size: 12px; font-weight: 500; cursor: pointer;
  transition: all 0.15s;
}
.crop-ratio-btns button.active { background: #3b82f6; border-color: #3b82f6; color: #fff; }
.crop-area {
  flex: 1; min-height: 300px; max-height: 55vh;
  background: #1e293b; overflow: hidden; position: relative;
}
.crop-area :deep(.vue-advanced-cropper) { width: 100% !important; height: 100% !important; }
.crop-actions {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 14px 18px; border-top: 1px solid #f1f5f9;
}

.spin { display: inline-block; animation: spin 0.8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

@media (max-width: 480px) {
  .type-btn span { display: none; }
  .type-btn { padding: 8px 12px; border-radius: 50%; }
  .type-btn .bi { font-size: 16px; }
  .crop-area { min-height: 220px; }
}
</style>
