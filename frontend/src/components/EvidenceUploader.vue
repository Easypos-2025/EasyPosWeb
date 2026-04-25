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
      </div>

      <!-- Preview imagen (con compresión) -->
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
        <button class="btn-change" @click="resetFile">
          <i class="bi bi-arrow-repeat"></i> Cambiar imagen
        </button>
      </div>

      <!-- Preview video -->
      <div v-if="currentType === 'video' && selectedFile" class="media-preview-wrap">
        <video :src="previewUrl" controls class="video-preview" />
        <div class="media-info">
          <span class="meta-badge">{{ selectedFile.name }}</span>
          <span class="meta-badge" :class="fileSizeClass">{{ fileSize }}</span>
        </div>
        <button class="btn-change" @click="resetFile">
          <i class="bi bi-arrow-repeat"></i> Cambiar video
        </button>
      </div>

      <!-- Preview audio -->
      <div v-if="currentType === 'audio' && selectedFile" class="media-preview-wrap">
        <audio :src="previewUrl" controls class="audio-preview" />
        <div class="media-info">
          <span class="meta-badge">{{ selectedFile.name }}</span>
          <span class="meta-badge" :class="fileSizeClass">{{ fileSize }}</span>
        </div>
        <button class="btn-change" @click="resetFile">
          <i class="bi bi-arrow-repeat"></i> Cambiar audio
        </button>
      </div>

    </template>

    <!-- BARRA DE PROGRESO (visible durante upload) -->
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

// ── Props / Emits ────────────────────────────────────────────
const props = defineProps({
  taskId:   { type: [Number, String], required: true },
})
const emit = defineEmits(["uploaded"])

// ── Estado ───────────────────────────────────────────────────
const currentType   = ref("image")
const description   = ref("")
const selectedFile  = ref(null)
const previewUrl    = ref("")
const compressedBlob = ref(null)   // blob JPEG comprimido para imágenes
const originalSize  = ref("")
const compressedSize = ref("")
const savings       = ref(0)
const uploading     = ref(false)
const progress      = ref(0)
const isDragging    = ref(false)
const fileInput     = ref(null)

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

const dropIcon = computed(() => ({
  image: "bi-image",
  video: "bi-play-circle",
  audio: "bi-mic",
}[currentType.value] || "bi-file"))

const dropHint = computed(() => ({
  image: "JPG, PNG, WEBP — máx 10 MB",
  video: "MP4, MOV, WEBM — máx 20 MB",
  audio: "MP3, M4A, WAV — máx 15 MB",
}[currentType.value] || ""))

const fileSize = computed(() => {
  if (!selectedFile.value) return ""
  return formatBytes(selectedFile.value.size)
})

const fileSizeClass = computed(() => {
  if (!selectedFile.value) return ""
  const mb = selectedFile.value.size / (1024 * 1024)
  if (currentType.value === "video" && mb > 15) return "meta-warn"
  if (currentType.value === "audio" && mb > 10) return "meta-warn"
  return "meta-ok"
})

const canSubmit = computed(() => {
  if (currentType.value === "text") return description.value.trim().length > 0
  return selectedFile.value !== null
})

// ── Selección de tipo ─────────────────────────────────────────
function selectType(type) {
  currentType.value = type
  resetFile()
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
  selectedFile.value  = file
  compressedBlob.value = null
  previewUrl.value    = ""
  originalSize.value  = ""
  compressedSize.value = ""
  savings.value       = 0

  if (currentType.value === "image") {
    originalSize.value = formatBytes(file.size)
    try {
      const { blob, url } = await compressImage(file)
      compressedBlob.value = blob
      previewUrl.value     = url
      compressedSize.value = formatBytes(blob.size)
      savings.value = Math.round((1 - blob.size / file.size) * 100)
    } catch {
      // Si falla la compresión, usar el archivo original
      previewUrl.value    = URL.createObjectURL(file)
      compressedBlob.value = null
    }
  } else {
    previewUrl.value = URL.createObjectURL(file)
  }
}

function resetFile() {
  selectedFile.value   = null
  previewUrl.value     = ""
  compressedBlob.value = null
  originalSize.value   = ""
  compressedSize.value = ""
  savings.value        = 0
  if (fileInput.value) fileInput.value.value = ""
}

// ── Compresión de imagen (canvas nativo, sin dependencias) ────
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
      // Para imágenes usar el blob comprimido si existe; si no, el archivo original
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

  } catch (e) {
    showToast(e.response?.data?.detail || "Error subiendo evidencia", "error")
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
  if (bytes < 1024)           return bytes + " B"
  if (bytes < 1024 * 1024)    return (bytes / 1024).toFixed(1) + " KB"
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

/* PREVIEW IMAGEN */
.img-preview-wrap { display: flex; flex-direction: column; gap: 8px; }
.img-preview-thumb { width: 100%; max-height: 220px; object-fit: contain;
  border-radius: 10px; background: #f8fafc; border: 1px solid #e2e8f0; }
.img-meta { display: flex; gap: 8px; flex-wrap: wrap; }
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

.spin { display: inline-block; animation: spin 0.8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

@media (max-width: 480px) {
  .type-btn span { display: none; }
  .type-btn { padding: 8px 12px; border-radius: 50%; }
  .type-btn .bi { font-size: 16px; }
}
</style>
