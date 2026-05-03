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
      <i v-if="uploading" class="bi bi-hourglass-split spin"></i>
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
      <div v-if="showCropper" class="ic-overlay">
        <div class="ic-modal">

          <div class="ic-header">
            <span class="ic-title"><i class="bi bi-crop me-2"></i>Recortar imagen</span>
            <div class="ic-ratio-btns">
              <button :class="{ active: cropRatio === 0 }"    @click="cropRatio = 0">Libre</button>
              <button :class="{ active: cropRatio === 1 }"    @click="cropRatio = 1">1:1</button>
              <button :class="{ active: cropRatio === 16/9 }" @click="cropRatio = 16/9">16:9</button>
              <button :class="{ active: cropRatio === 4/3 }"  @click="cropRatio = 4/3">4:3</button>
            </div>
            <button class="ic-close" @click="cancelCrop"><i class="bi bi-x-lg"></i></button>
          </div>

          <div class="ic-area">
            <Cropper
              ref="cropperRef"
              :src="rawSrc"
              image-restriction="none"
              :auto-zoom="true"
              :stencil-props="{ movable: true, resizable: true, aspectRatio: cropRatio || undefined }"
            />
          </div>

          <div class="ic-footer">
            <button class="ic-btn-cancel" @click="cancelCrop">Cancelar</button>
            <button class="ic-btn-confirm" @click="confirmCrop" :disabled="uploading">
              <i v-if="uploading" class="bi bi-hourglass-split spin me-1"></i>
              <i v-else class="bi bi-check-lg me-1"></i>
              {{ uploading ? 'Subiendo...' : 'Subir imagen' }}
            </button>
          </div>

        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref } from "vue"
import { Cropper } from "vue-advanced-cropper"
import "vue-advanced-cropper/dist/style.css"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

const props = defineProps({
  noveltyId: { type: Number, required: true }
})
const emit = defineEmits(["uploaded"])

const fileInput  = ref(null)
const cropperRef = ref(null)
const rawSrc     = ref("")
const showCropper = ref(false)
const uploading  = ref(false)
const cropRatio  = ref(0)   // 0 = libre

function onFileChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  if (rawSrc.value) URL.revokeObjectURL(rawSrc.value)
  rawSrc.value   = URL.createObjectURL(file)
  showCropper.value = true
  e.target.value = ""
}

async function confirmCrop() {
  if (!cropperRef.value) return
  uploading.value = true
  try {
    const { canvas } = cropperRef.value.getResult()
    if (!canvas) { showToast("No se pudo obtener el recorte", "error"); return }

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
  showCropper.value = false
  URL.revokeObjectURL(rawSrc.value)
  rawSrc.value = ""
  cropRatio.value = 0
}
</script>

<style scoped>
/* Botón disparador */
.btn-upload-ev {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 6px 12px; border-radius: 8px;
  background: #3b82f6; color: #fff;
  font-size: 12px; font-weight: 600;
  cursor: pointer; border: none;
  transition: background 0.15s;
  user-select: none;
}
.btn-upload-ev:hover   { background: #2563eb; }
.btn-upload-ev.loading { opacity: 0.7; cursor: not-allowed; }

/* Overlay */
.ic-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.75);
  display: flex; align-items: center; justify-content: center;
  z-index: 9000; padding: 16px;
}

/* Modal */
.ic-modal {
  background: #fff; border-radius: 16px;
  width: 100%; max-width: 680px;
  max-height: 92vh;
  display: flex; flex-direction: column;
  box-shadow: 0 25px 70px rgba(0,0,0,0.4);
  overflow: hidden;
}

/* Header */
.ic-header {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 18px; border-bottom: 1px solid #f1f5f9;
  flex-wrap: wrap; flex-shrink: 0;
}
.ic-title {
  font-size: 15px; font-weight: 700; color: #1e293b;
  display: flex; align-items: center; flex-shrink: 0;
}

/* Botones de ratio */
.ic-ratio-btns { display: flex; gap: 5px; flex: 1; }
.ic-ratio-btns button {
  padding: 4px 11px; border-radius: 20px;
  border: 1px solid #e2e8f0; background: #f8fafc;
  font-size: 12px; font-weight: 500; cursor: pointer;
  transition: all 0.15s; color: #475569;
}
.ic-ratio-btns button.active {
  background: #3b82f6; border-color: #3b82f6; color: #fff;
}
.ic-ratio-btns button:hover:not(.active) { border-color: #94a3b8; }

.ic-close {
  background: none; border: none; font-size: 17px;
  cursor: pointer; color: #94a3b8; margin-left: auto; flex-shrink: 0;
}
.ic-close:hover { color: #1e293b; }

/* Área cropper */
.ic-area {
  flex: 1; min-height: 300px; max-height: 55vh;
  background: #1e293b; overflow: hidden; position: relative;
}

/* Footer */
.ic-footer {
  padding: 12px 18px; border-top: 1px solid #f1f5f9;
  display: flex; justify-content: flex-end; gap: 8px;
  flex-shrink: 0;
}

.ic-btn-cancel {
  padding: 8px 18px; border-radius: 8px;
  border: 1px solid #e2e8f0; background: #f8fafc;
  color: #475569; font-size: 13px; font-weight: 500;
  cursor: pointer; transition: background 0.15s;
}
.ic-btn-cancel:hover { background: #e2e8f0; }

.ic-btn-confirm {
  padding: 8px 20px; border-radius: 8px;
  background: #3b82f6; color: #fff;
  border: none; font-size: 13px; font-weight: 600;
  cursor: pointer; display: flex; align-items: center;
  transition: background 0.15s;
}
.ic-btn-confirm:hover:not(:disabled) { background: #2563eb; }
.ic-btn-confirm:disabled { opacity: 0.65; cursor: not-allowed; }

.spin { display: inline-block; animation: spin 0.8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

@media (max-width: 600px) {
  .ic-footer   { flex-direction: column; }
  .ic-area     { min-height: 220px; }
  .ic-ratio-btns { flex-wrap: wrap; }
}
</style>
