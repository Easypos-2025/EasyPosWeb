<template>
  <!-- Versión instalada del agente (la misma que muestra el panel y la nube); sirve para saber si
       la sede ya tomó la última actualización -->
  <p class="version">Versión {{ agente.version || build }}</p>
</template>

<script setup>
import { agente } from "../api"

const build = typeof __APP_BUILD__ !== "undefined" ? __APP_BUILD__ : "dev"
</script>

<style scoped>
.version { margin: 18px 0 0; text-align: center; font-size: 12px; color: var(--texto-suave); }
</style>
