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

      <!-- IMAGEN: componente unificado (archivo + cámara + pegar + recorte) -->
      <ImageUploaderPro
        v-if="currentType === 'image'"
        :key="imageUploaderKey"
        label="Foto de la evidencia"
        :show-remove="false"
        :output-width="1200"
        output-format="jpeg"
        :output-quality="0.85"
        @change="onImageReady"
      />

      <template v-else>

        <!-- Zona de drop / selector (video / audio) -->
        <div v-if="!selectedFile" class="eu-field">
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

  </div>
</template>

<script setup>
import { ref, computed } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import ImageUploaderPro from "@/components/common/ImageUploaderPro.vue"

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
const imageFile      = ref(null)
const imageUploaderKey = ref(0)
const uploading      = ref(false)
const progress       = ref(0)
const isDragging     = ref(false)
const mediaDuration  = ref("")
const fileInput      = ref(null)
const cameraInput    = ref(null)
const isMobile       = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)

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
  if (currentType.value === "image") return !!imageFile.value
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

  selectedFile.value  = file
  previewUrl.value    = ""
  mediaDuration.value = ""

  previewUrl.value = URL.createObjectURL(file)
  if (sizeExceeded.value) {
    const limit = SIZE_LIMITS[currentType.value]
    showToast(
      `El archivo pesa ${formatBytes(file.size)} y supera el límite de ${limit} MB. Debes recortarlo antes de subirlo.`,
      "warning"
    )
  }
}

// ── Imagen: recibe blob ya recortado/comprimido de ImageUploaderPro ──
function onImageReady(blob) {
  if (!blob) return
  imageFile.value = new File([blob], `evidencia_${Date.now()}.jpg`, { type: blob.type || "image/jpeg" })
}

function onAudioMeta(e) {
  const s = Math.round(e.target.duration)
  if (!isFinite(s)) return
  const m = Math.floor(s / 60)
  mediaDuration.value = `${m}:${String(s % 60).padStart(2, "0")} min`
}

function resetFile() {
  selectedFile.value = null
  previewUrl.value    = ""
  imageFile.value     = null
  imageUploaderKey.value++
  mediaDuration.value = ""
  if (fileInput.value)   fileInput.value.value   = ""
  if (cameraInput.value) cameraInput.value.value = ""
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
      const toUpload = currentType.value === "image" ? imageFile.value : selectedFile.value
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
.meta-ok         { background: #dcfce7; color: #166534; }
.meta-warn       { background: #fef2f2; color: #b91c1c; }

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

.spin { display: inline-block; animation: spin 0.8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

@media (max-width: 480px) {
  .type-btn span { display: none; }
  .type-btn { padding: 8px 12px; border-radius: 50%; }
  .type-btn .bi { font-size: 16px; }
}
</style>
