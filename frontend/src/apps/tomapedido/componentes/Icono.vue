<template>
  <svg class="icono" :width="tam" :height="tam" viewBox="0 0 24 24" fill="none" stroke="currentColor"
       stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <path v-for="(d, i) in trazos" :key="i" :d="d" />
  </svg>
</template>

<script setup>
// Íconos propios en SVG: la red del negocio puede no tener internet (sin CDN de fuentes)
import { computed } from "vue"

const props = defineProps({ nombre: { type: String, required: true }, tam: { type: [Number, String], default: 20 } })

const ICONOS = {
  atras:     ["M15 18l-6-6 6-6"],
  menu:      ["M3 6h18", "M3 12h18", "M3 18h18"],
  mas:       ["M12 5v14", "M5 12h14"],
  menos:     ["M5 12h14"],
  refrescar: ["M21 12a9 9 0 1 1-3-6.7", "M21 4v5h-5"],
  salir:     ["M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4", "M16 17l5-5-5-5", "M21 12H9"],
  buscar:    ["M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16z", "M21 21l-4.3-4.3"],
  carrito:   ["M6 6h15l-1.5 9h-12z", "M6 6L5 3H2", "M9 20a1 1 0 1 0 0-2 1 1 0 0 0 0 2z", "M18 20a1 1 0 1 0 0-2 1 1 0 0 0 0 2z"],
  basura:    ["M3 6h18", "M8 6V4h8v2", "M19 6l-1 14H6L5 6"],
  check:     ["M20 6L9 17l-5-5"],
  cerrar:    ["M18 6L6 18", "M6 6l12 12"],
  usuario:   ["M20 21a8 8 0 0 0-16 0", "M12 13a5 5 0 1 0 0-10 5 5 0 0 0 0 10z"],
  mesa:      ["M3 9h18", "M6 9v11", "M18 9v11", "M4 5h16v4H4z"],
  reloj:     ["M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z", "M12 7v5l3 2"],
  enviar:    ["M22 2L11 13", "M22 2l-7 20-4-9-9-4z"],
  impresora: ["M6 9V2h12v7", "M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2", "M6 14h12v8H6z"],
  lista:     ["M8 6h13", "M8 12h13", "M8 18h13", "M3 6h.01", "M3 12h.01", "M3 18h.01"],
  candado:   ["M5 11h14v10H5z", "M8 11V7a4 4 0 0 1 8 0v4"],
  wifi:      ["M5 12.5a10 10 0 0 1 14 0", "M8.5 16a5 5 0 0 1 7 0", "M12 20h.01", "M2 9a15 15 0 0 1 20 0"],
}
const trazos = computed(() => ICONOS[props.nombre] || [])
</script>

<style scoped>
.icono { flex-shrink: 0; vertical-align: middle; }
</style>
