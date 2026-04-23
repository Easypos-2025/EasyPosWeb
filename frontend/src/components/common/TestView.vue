<template>
  <div style="padding:20px">
    <h2>TEST CROPPER1</h2>
    <ImageUploader @update:image="img => result = img" />

    <img v-if="result" :src="result" style="margin-top:20px; width:150px"/>
  </div>
</template>

<script setup>
import { ref } from "vue"
import ImageUploader from "@/components/common/ImageUploader.vue"

const result = ref(null)
</script>