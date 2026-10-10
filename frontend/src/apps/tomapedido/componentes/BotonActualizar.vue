<template>
  <!-- Versión nueva del agente en la barra superior: los meseros la pueden instalar desde la toma de
       pedidos (la usan más que el panel). Solo aparece cuando hay una versión lista. -->
  <button v-if="actualizacion.lista || actualizacion.aplicando" class="barra__btn act"
          :class="{ 'act--aplicando': actualizacion.aplicando }" :disabled="actualizacion.aplicando || enviando"
          :title="actualizacion.aplicando ? 'Actualizando…' : `Actualizar a la versión ${actualizacion.nueva}`"
          @click="actualizar">
    <span v-if="actualizacion.aplicando" class="giro act__giro"></span>
    <Icono v-else nombre="descargar" />
    <i v-if="!actualizacion.aplicando" class="act__punto"></i>
  </button>
</template>

<script setup>
import { ref } from "vue"
import Icono from "./Icono.vue"
import { actualizacion, api } from "../api"
import { showConfirm, showToast } from "@/utils/toast"

const enviando = ref(false)

async function actualizar() {
  const notas = actualizacion.notas ? ` ${actualizacion.notas.trim().replace(/\.?$/, ".")}` : ""
  if (!(await showConfirm(`Hay una versión nueva: ${actualizacion.nueva}.${notas} Mientras se actualiza (menos de un minuto) `
    + "ningún dispositivo podrá tomar pedidos. Los pedidos ya enviados no se pierden. "
    + "Si no la aplica ahora, se instala sola al abrir el próximo turno. ¿Actualizar ahora?", "Sí, actualizar"))) return
  enviando.value = true
  try {
    await api.post("/actualizar")
    actualizacion.aplicando = true
    showToast("Actualizando… la toma de pedidos vuelve en menos de un minuto.", "info", 5000)
  } catch (e) {
    showToast(e.message, "error", 4000)
  } finally {
    enviando.value = false
  }
}
</script>

<style scoped>
.act { position: relative; background: var(--ambar); color: #1e293b; }
.act:active { background: var(--ambar); filter: brightness(.92); }
.act--aplicando { background: rgba(255,255,255,.12); color: #fff; }
.act__punto { position: absolute; top: 5px; right: 5px; width: 9px; height: 9px; border-radius: 50%;
              background: var(--rojo); box-shadow: 0 0 0 2px var(--navy); animation: latir 1.4s ease-in-out infinite; }
.act__giro { width: 18px; height: 18px; border-width: 2px; }
@keyframes latir { 50% { transform: scale(1.35); } }

@media (max-width: 768px) {
  .act__punto { top: 4px; right: 4px; }
}
@media (max-width: 576px) {
  .act__punto { width: 8px; height: 8px; }
}
</style>
