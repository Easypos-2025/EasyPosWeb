<template>
  <ImageUploaderPro
    :current-url="currentUrl"
    :output-width="800"
    output-format="webp"
    :output-quality="0.88"
    label="Sin foto"
    :show-remove="true"
    @change="emit('change', $event)"
    @remove="emit('remove')"
  />
</template>

<script setup>
import ImageUploaderPro from '@/components/common/ImageUploaderPro.vue'

defineProps({
  currentUrl: { type: String, default: null },
})
const emit = defineEmits(['change', 'remove'])
</script>
