<template>
  <div class="uploader">

    <!-- FILA SUPERIOR: selector de archivo + ratios -->
    <div class="uploader-toolbar">
      <label class="file-btn">
        <i class="bi bi-upload"></i>
        {{ imageUrl ? 'Cambiar imagen' : 'Seleccionar imagen' }}
        <input type="file" accept="image/*" @change="loadImage" hidden />
      </label>

      <div v-if="imageUrl" class="ratio-btns">
        <button class="btn btn-outline-secondary btn-sm" @click="setRatio(0)">Libre</button>
        <button class="btn btn-outline-secondary btn-sm" @click="setRatio(1)">Cuadrado</button>
        <button class="btn btn-outline-secondary btn-sm" @click="setRatio(16/9)">16:9</button>
        <button class="btn btn-outline-secondary btn-sm" @click="setRatio(4/3)">4:3</button>
      </div>

      <span v-if="!imageUrl" class="uploader-hint">
        Sube una imagen PNG o JPG para usarla como logo de la empresa
      </span>
    </div>

    <!-- TRES CAJAS EN LÍNEA -->
    <div class="logo-boxes" :class="{ 'has-image': imageUrl }">

      <!-- 1. Editor / Cropper -->
      <div class="logo-box logo-box--editor">
        <span class="box-label">Editar</span>
        <div class="box-inner">
          <div v-if="imageUrl" class="cropper-wrap">
            <Cropper
              :key="cropperKey"
              ref="cropperRef"
              :src="imageUrl"
              imageRestriction="none"
              :autoZoom="true"
              :default-size="defaultSize"
              :stencil-props="{ movable: true, resizable: true, aspectRatio: ratio }"
              @change="updatePreview"
            />
          </div>
          <div v-else class="box-empty">
            <i class="bi bi-image"></i>
            <span>Sin imagen</span>
          </div>
        </div>
      </div>

      <!-- 2. Vista previa -->
      <div class="logo-box logo-box--preview">
        <span class="box-label">Vista previa</span>
        <div class="box-inner">
          <img v-if="croppedImage" :src="croppedImage" class="box-img" />
          <div v-else class="box-empty">
            <i class="bi bi-eye"></i>
            <span>Previa</span>
          </div>
        </div>
      </div>

      <!-- 3. Logo actual (pasado desde el padre) -->
      <div class="logo-box logo-box--current">
        <span class="box-label">Logo actual</span>
        <div class="box-inner">
          <img v-if="currentLogo" :src="currentLogo" class="box-img" />
          <div v-else class="box-empty">
            <i class="bi bi-building"></i>
            <span>Sin logo</span>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref } from "vue"
import { Cropper } from "vue-advanced-cropper"
import "vue-advanced-cropper/dist/style.css"

const props = defineProps({
  currentLogo: { type: String, default: "" }
})

const emit = defineEmits(["update:image"])

const imageUrl     = ref(null)
const croppedImage = ref(null)
const cropperRef   = ref(null)
const ratio        = ref(0)
const cropperKey   = ref(0)

function loadImage(e) {
  const file = e.target.files[0]
  if (!file) return
  imageUrl.value     = URL.createObjectURL(file)
  croppedImage.value = null
  cropperKey.value++
}

function setRatio(value) { ratio.value = value }

function updatePreview({ canvas }) {
  if (!canvas) return

  // Redimensionar a máx 400×400 antes de guardar — reduce de ~1MB a ~20-40KB
  const MAX = 400
  let { width, height } = canvas

  if (width > MAX || height > MAX) {
    const scale = Math.min(MAX / width, MAX / height)
    width  = Math.round(width  * scale)
    height = Math.round(height * scale)
  }

  const resized = document.createElement("canvas")
  resized.width  = width
  resized.height = height
  resized.getContext("2d").drawImage(canvas, 0, 0, width, height)

  // JPEG al 80% — mucho más pequeño que PNG sin pérdida visible
  const base64 = resized.toDataURL("image/jpeg", 0.8)
  croppedImage.value = base64
  emit("update:image", base64)
}

const defaultSize = ({ imageSize }) => ({
  width:  imageSize.width  * 0.7,
  height: imageSize.height * 0.7
})
</script>

<style scoped>
.uploader { display: flex; flex-direction: column; gap: 12px; }

/* TOOLBAR */
.uploader-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.file-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 16px;
  background: #3b82f6;
  color: #fff;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.2s;
}
.file-btn:hover { background: #2563eb; }

.ratio-btns { display: flex; gap: 6px; flex-wrap: wrap; }

.uploader-hint {
  font-size: 12px;
  color: #94a3b8;
  font-style: italic;
}

/* TRES CAJAS */
.logo-boxes {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.logo-box {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.box-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #64748b;
}

.box-inner {
  height: 180px;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: #f8fafc;
}

.logo-box--editor .box-inner  { border: 2px dashed #ef4444; }
.logo-box--preview .box-inner { border: 2px dashed #3b82f6; }
.logo-box--current .box-inner { border: 2px solid #94a3b8; background: #fff; }

/* Cropper ocupa todo el box */
.cropper-wrap {
  position: absolute;
  inset: 0;
}

.cropper-wrap :deep(.vue-advanced-cropper) {
  width: 100% !important;
  height: 100% !important;
}

.box-img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 8px;
  padding: 8px;
}

.box-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #cbd5e1;
}
.box-empty .bi { font-size: 28px; }
.box-empty span { font-size: 12px; }

/* RESPONSIVE */
@media (max-width: 640px) {
  .logo-boxes { grid-template-columns: 1fr; }
  .box-inner  { height: 140px; }
}
</style>
