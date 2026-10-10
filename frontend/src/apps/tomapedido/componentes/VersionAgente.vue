<template>
  <!-- Versión instalada del agente (la misma que muestra el panel y la nube); sirve para saber si
       la sede ya tomó la última actualización. "en-barra": línea pequeña bajo el título de la barra superior -->
  <span v-if="enBarra" class="version-barra">v{{ version }}</span>
  <p v-else class="version">Versión {{ version }}</p>
</template>

<script setup>
import { computed } from "vue"
import { agente } from "../api"

defineProps({ enBarra: { type: Boolean, default: false } })

const build = typeof __APP_BUILD__ !== "undefined" ? __APP_BUILD__ : "dev"
const version = computed(() => agente.version || build)
</script>

<style scoped>
.version { margin: 18px 0 0; text-align: center; font-size: 12px; color: var(--texto-suave); }
.version-barra { display: block; font-size: 10px; line-height: 1.2; opacity: .6; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

@media (max-width: 576px) {
  .version-barra { font-size: 9.5px; }
}
</style>
