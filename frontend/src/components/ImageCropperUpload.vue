<!--
  ImageCropperUpload
  Props:
    noveltyId   — ID de la novedad a la que se sube la evidencia
  Emits:
    uploaded(evidence) — cuando la imagen recortada se sube exitosamente
-->
<template>
  <div>
    <!-- Botón disparador -->
    <label class="btn-upload-ev" :class="{ loading: uploading }" title="Subir foto">
      <i v-if="uploading" class="bi bi-hourglass-split"></i>
      <i v-else class="bi bi-camera"></i>
      <span>{{ uploading ? 'Subiendo...' : 'Foto' }}</span>
      <input
        type="file"
        accept="image/*"
        style="display:none"
        :disabled="uploading"
        @change="onFileChange"
        ref="fileInput"
      />
    </label>

    <!-- MODAL DE RECORTE -->
    <Teleport to="body">
      <div v-if="showCropper" class="cropper-overlay">
        <div class="cropper-modal">

          <div class="cropper-header">
            <h3><i class="bi bi-crop"></i> Recortar imagen</h3>
            <button class="cropper-close" @click="cancelCrop"><i class="bi bi-x-lg"></i></button>
          </div>

          <div class="cropper-area">
            <img ref="imgEl" :src="rawSrc" alt="preview" style="max-width:100%;display:block" />
          </div>

          <div class="cropper-footer">
            <div class="cropper-tools">
              <button class="tool-btn" @click="cropper?.rotate(-90)" title="Rotar izquierda">
                <i class="bi bi-arrow-counterclockwise"></i>
              </button>
              <button class="tool-btn" @click="cropper?.rotate(90)" title="Rotar derecha">
                <i class="bi bi-arrow-clockwise"></i>
              </button>
              <button class="tool-btn" @click="cropper?.reset()" title="Resetear">
                <i class="bi bi-arrow-repeat"></i>
              </button>
            </div>
            <div class="cropper-actions">
              <button class="btn-cancel-crop" @click="cancelCrop">Cancelar</button>
              <button class="btn-confirm-crop" @click="confirmCrop" :disabled="uploading">
                <i v-if="uploading" class="bi bi-hourglass-split spin"></i>
                <i v-else class="bi bi-check-lg"></i>
                {{ uploading ? 'Subiendo...' : 'Subir imagen' }}
              </button>
            </div>
          </div>

        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, nextTick, onBeforeUnmount } from "vue"
import Cropper from "cropperjs"
import "cropperjs/dist/cropper.css"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

const props = defineProps({
  noveltyId: { type: Number, required: true }
})
const emit = defineEmits(["uploaded"])

const fileInput  = ref(null)
const imgEl      = ref(null)
const rawSrc     = ref("")
const showCropper = ref(false)
const uploading  = ref(false)
let   cropper    = null

function onFileChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  // Liberar URL anterior
  if (rawSrc.value) URL.revokeObjectURL(rawSrc.value)
  rawSrc.value = URL.createObjectURL(file)
  showCropper.value = true
  // Resetear el input para permitir seleccionar el mismo archivo nuevamente
  e.target.value = ""

  nextTick(() => {
    if (cropper) { cropper.destroy(); cropper = null }
    cropper = new Cropper(imgEl.value, {
      aspectRatio: 4 / 3,
      viewMode: 1,
      autoCropArea: 0.9,
      responsive: true,
      guides: true,
      center: true,
      highlight: false,
      cropBoxMovable: true,
      cropBoxResizable: true,
    })
  })
}

async function confirmCrop() {
  if (!cropper) return
  uploading.value = true
  try {
    const canvas = cropper.getCroppedCanvas({
      maxWidth:  1200,
      maxHeight: 900,
      fillColor: "#fff",
      imageSmoothingEnabled: true,
      imageSmoothingQuality: "high",
    })

    const blob = await new Promise(resolve =>
      canvas.toBlob(resolve, "image/jpeg", 0.88)
    )

    const formData = new FormData()
    formData.append("file", blob, `novedad_${props.noveltyId}_${Date.now()}.jpg`)

    const res = await api.post(
      `/novelties/${props.noveltyId}/evidence`,
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    )
    emit("uploaded", res.data)
    showToast("Imagen subida correctamente", "success")
    cancelCrop()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error subiendo imagen", "error")
  } finally {
    uploading.value = false
  }
}

function cancelCrop() {
  if (cropper) { cropper.destroy(); cropper = null }
  showCropper.value = false
  URL.revokeObjectURL(rawSrc.value)
  rawSrc.value = ""
}

onBeforeUnmount(() => {
  if (cropper) cropper.destroy()
})
</script>

<style scoped>
/* Botón disparador — mismo estilo que el original de novedades */
.btn-upload-ev {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 6px 12px; border-radius: 8px;
  background: #3b82f6; color: #fff;
  font-size: 12px; font-weight: 600;
  cursor: pointer; border: none;
  transition: background 0.15s;
  user-select: none;
}
.btn-upload-ev:hover  { background: #2563eb; }
.btn-upload-ev.loading { opacity: 0.7; cursor: not-allowed; }

/* Overlay */
.cropper-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.7);
  display: flex; align-items: center; justify-content: center;
  z-index: 2000;
}

/* Modal */
.cropper-modal {
  background: #fff;
  border-radius: 16px;
  width: 680px;
  max-width: 96vw;
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 70px rgba(0,0,0,0.4);
  overflow: hidden;
}

.cropper-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid #f1f5f9;
  flex-shrink: 0;
}
.cropper-header h3 {
  font-size: 15px; font-weight: 700; color: #1e293b; margin: 0;
  display: flex; align-items: center; gap: 7px;
}
.cropper-close {
  background: none; border: none; font-size: 17px;
  cursor: pointer; color: #94a3b8;
}
.cropper-close:hover { color: #1e293b; }

.cropper-area {
  flex: 1;
  overflow: hidden;
  background: #0f172a;
  min-height: 0;
  max-height: 480px;
}
/* Estira el cropper al área disponible */
.cropper-area img { max-height: 480px; width: 100%; object-fit: contain; }

.cropper-footer {
  padding: 12px 20px;
  border-top: 1px solid #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  flex-wrap: wrap;
  gap: 10px;
}
.cropper-tools { display: flex; gap: 6px; }
.tool-btn {
  width: 34px; height: 34px;
  border: 1px solid #e2e8f0; border-radius: 8px;
  background: #f8fafc; color: #475569;
  font-size: 14px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s;
}
.tool-btn:hover { background: #e2e8f0; color: #1e293b; }

.cropper-actions { display: flex; gap: 8px; }
.btn-cancel-crop {
  padding: 7px 16px; border-radius: 8px;
  border: 1px solid #e2e8f0; background: #f8fafc;
  color: #475569; font-size: 13px; font-weight: 500;
  cursor: pointer; transition: background 0.15s;
}
.btn-cancel-crop:hover { background: #e2e8f0; }
.btn-confirm-crop {
  padding: 7px 18px; border-radius: 8px;
  background: #3b82f6; color: #fff;
  border: none; font-size: 13px; font-weight: 600;
  cursor: pointer; display: flex; align-items: center; gap: 6px;
  transition: background 0.15s;
}
.btn-confirm-crop:hover:not(:disabled) { background: #2563eb; }
.btn-confirm-crop:disabled { opacity: 0.65; cursor: not-allowed; }

.spin { display: inline-block; animation: spin 0.8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

@media (max-width: 600px) {
  .cropper-footer { flex-direction: column; align-items: stretch; }
  .cropper-tools  { justify-content: center; }
  .cropper-actions { flex-direction: column; }
}
</style>
