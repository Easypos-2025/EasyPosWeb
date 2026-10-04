<template>
  <router-view />
  <SinConexion v-if="!conexion.ok" :probando="probando" @reintentar="probar" />
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from "vue"
import SinConexion from "./componentes/SinConexion.vue"
import { api, conexion, enviarCola } from "./api"
import { sesion } from "./sesion"

const probando = ref(false)
let latido = null
let reintento = null

// Latido: el panel de la caja sabe qué dispositivos están conectados y este detecta si perdió la conexión
async function latir() {
  try {
    if (sesion.token) await api.ping("/sesion/latido", "POST")
    else await api.ping("/salud")
  } catch { /* el aviso lo maneja conexion.ok */ }
}

async function probar() {
  probando.value = true
  try { await api.ping("/salud") } catch { /* sigue sin conexión */ } finally { probando.value = false }
}

// Sin conexión: reintenta seguido hasta que vuelva
watch(() => conexion.ok, (ok) => {
  clearInterval(reintento)
  if (!ok) reintento = setInterval(probar, 5000)
})

onMounted(() => {
  latir()
  enviarCola()
  latido = setInterval(latir, 30000)
})
onBeforeUnmount(() => { clearInterval(latido); clearInterval(reintento) })
</script>
