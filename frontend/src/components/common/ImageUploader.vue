<template>
  <div class="uploader">

    <!-- FILA SUPERIOR -->
    <div class="uploader-toolbar">
      <span class="uploader-hint">
        Sube una imagen PNG, JPG o WEBP para usarla como logo de la empresa
      </span>
    </div>

    <!-- TRES CAJAS EN LÍNEA -->
    <div class="logo-boxes">

      <!-- 1. Editor con ImageUploaderPro -->
      <div class="logo-box logo-box--editor">
        <span class="box-label">Editar</span>
        <ImageUploaderPro
          :current-url="currentLogo"
          :output-width="400"
          :output-height="400"
          output-format="jpeg"
          :output-quality="0.8"
          label="Sin logo"
          :show-remove="false"
          @change="onBlobChange"
        />
      </div>

      <!-- 2. Vista previa -->
      <div class="logo-box logo-box--preview">
        <span class="box-label">Vista previa</span>
        <div class="box-inner">
          <img v-if="previewBase64" :src="previewBase64" class="box-img" />
          <div v-else class="box-empty">
            <i class="bi bi-eye"></i>
            <span>Previa</span>
          </div>
        </div>
      </div>

      <!-- 3. Logo actual -->
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
import { ref } from 'vue'
import ImageUploaderPro from '@/components/common/ImageUploaderPro.vue'

defineProps({ currentLogo: { type: String, default: '' } })
const emit = defineEmits(['update:image'])

const previewBase64 = ref(null)

function onBlobChange(blob) {
  const reader = new FileReader()
  reader.onload = e => {
    previewBase64.value = e.target.result
    emit('update:image', e.target.result)
  }
  reader.readAsDataURL(blob)
}
</script>

<style scoped>
.uploader { display: flex; flex-direction: column; gap: 12px; }

.uploader-toolbar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.uploader-hint    { font-size: 12px; color: #94a3b8; font-style: italic; }

.logo-boxes {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.logo-box         { display: flex; flex-direction: column; gap: 6px; }
.box-label        { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .5px; color: #64748b; }

.box-inner {
  height: 180px; border-radius: 12px; overflow: hidden;
  display: flex; align-items: center; justify-content: center;
  position: relative; background: #f8fafc;
}
.logo-box--preview .box-inner { border: 2px dashed #3b82f6; }
.logo-box--current .box-inner { border: 2px solid #94a3b8; background: #fff; }

.box-img   { max-width: 100%; max-height: 100%; object-fit: contain; border-radius: 8px; padding: 8px; }
.box-empty { display: flex; flex-direction: column; align-items: center; gap: 8px; color: #cbd5e1; }
.box-empty .bi   { font-size: 28px; }
.box-empty span  { font-size: 12px; }

@media (max-width: 768px) { .logo-boxes { grid-template-columns: 1fr 1fr; } }
@media (max-width: 576px) { .logo-boxes { grid-template-columns: 1fr; } .box-inner { height: 140px; } }
</style>
