<!--
  ImageCropperUpload
  Props:
    noveltyId — ID de la novedad a la que se sube la evidencia
  Emits:
    uploaded(evidence) — cuando la imagen recortada se sube exitosamente
-->
<template>
  <div class="icu-root">
    <ImageUploaderPro
      label="Foto"
      output-format="jpeg"
      :output-quality="0.88"
      :show-remove="false"
      @change="onImageReady"
    />
    <div v-if="uploading" class="icu-uploading">
      <i class="bi bi-hourglass-split spin me-1"></i> Subiendo...
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ImageUploaderPro from '@/components/common/ImageUploaderPro.vue'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'

const props   = defineProps({ noveltyId: { type: Number, required: true } })
const emit    = defineEmits(['uploaded'])
const uploading = ref(false)

async function onImageReady(blob) {
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', blob, `novedad_${props.noveltyId}_${Date.now()}.jpg`)
    const res = await api.post(
      `/novelties/${props.noveltyId}/evidence`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    emit('uploaded', res.data)
    showToast('Imagen subida correctamente', 'success')
  } catch (e) {
    showToast(e.response?.data?.detail || 'Error subiendo imagen', 'error')
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.icu-root     { display: flex; flex-direction: column; gap: 6px; }
.icu-uploading {
  font-size: 12px; color: #64748b;
  display: flex; align-items: center;
}
.spin { animation: spin .8s linear infinite; display: inline-block; }
@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }
</style>
