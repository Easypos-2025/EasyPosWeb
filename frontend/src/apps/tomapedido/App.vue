<template>
  <router-view />
  <SinConexion v-if="!conexion.ok" :probando="probando" @reintentar="probar" />
  <CajaCerrada v-else-if="mostrarCaja" :probando="probandoCaja" @reintentar="revisarCaja" />
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import SinConexion from "./componentes/SinConexion.vue"
import CajaCerrada from "./componentes/CajaCerrada.vue"
import { actualizacion, agente, api, caja, conexion, enviarCola, preferencias } from "./api"
import { sesion } from "./sesion"

const probando = ref(false)
const route = useRoute()
const router = useRouter()
// Pantallas donde recargar no hace perder nada (no en la toma de un pedido)
const SEGURAS = ["/cuentas", "/mesas", "/cuenta", "/ingresar", "/registro", "/espera"]
const esSegura = (ruta) => SEGURAS.includes(ruta) || ruta.startsWith("/admin")
let versionCargada = null
let recargarPendiente = false

function revisarVersion(version) {
  if (!version) return
  if (!versionCargada) { versionCargada = version; return }
  if (version !== versionCargada) {
    recargarPendiente = true
    if (esSegura(route.path)) location.reload()
  }
}
router.afterEach((to) => { if (recargarPendiente && esSegura(to.path)) location.reload() })
let latido = null
let reintento = null

// Latido: el panel de la caja sabe qué dispositivos están conectados y este detecta si perdió la conexión
async function latir() {
  try {
    const r = sesion.token ? await api.ping("/sesion/latido", "POST") : await api.ping("/salud")
    revisarVersion(r?.datos?.version)
    if (r?.datos?.version) agente.version = r.datos.version
    if (r?.datos?.caja) Object.assign(caja, r.datos.caja)
    // Dirección por nombre del PC de caja: guía al usuario si un día cambia la IP de la caja
    if (r?.datos?.pc) try { localStorage.setItem("ag_caja_pc", r.datos.pc) } catch { /* sin almacenamiento */ }
    if (r?.datos?.actualizacion) Object.assign(actualizacion, r.datos.actualizacion)
    if (r?.datos?.estilo && r.datos.estilo !== preferencias.estilo) {
      preferencias.estilo = r.datos.estilo
      try { localStorage.setItem("ag_estilo_tarjetas", r.datos.estilo) } catch { /* sin almacenamiento */ }
    }
  } catch { /* el aviso lo maneja conexion.ok */ }
}

async function probar() {
  probando.value = true
  try { await api.ping("/salud") } catch { /* sigue sin conexión */ } finally { probando.value = false }
}

// Caja cerrada: tapa la toma de pedidos (no el panel de administración ni el ingreso) hasta que
// abran el turno en el escritorio; mientras tanto se revisa cada pocos segundos
const SIN_CAJA = ["/ingresar", "/registro", "/espera"]
const mostrarCaja = computed(() => !!sesion.token && !caja.abierta && !route.path.startsWith("/admin")
  && !SIN_CAJA.includes(route.path))
const probandoCaja = ref(false)
let revisionCaja = null
async function revisarCaja() {
  probandoCaja.value = true
  try { await latir() } finally { probandoCaja.value = false }
}
watch(() => caja.abierta, (abierta) => {
  clearInterval(revisionCaja)
  if (!abierta) revisionCaja = setInterval(latir, 5000)
})

// Sin conexión: reintenta seguido hasta que vuelva
watch(() => conexion.ok, (ok) => {
  clearInterval(reintento)
  if (!ok) reintento = setInterval(probar, 5000)
})

// Pantalla completa (como F11): el navegador solo la permite tras un toque o clic del usuario, así
// que se activa en el primer toque de la toma de pedidos (no en el panel de administración).
// iPhone no la permite en páginas: allí sirve "Agregar a inicio" (abre sin la barra de Safari).
function pantallaCompleta() {
  const yaEsApp = window.matchMedia("(display-mode: standalone)").matches
  if (route.path.startsWith("/admin") || yaEsApp || !document.fullscreenEnabled || document.fullscreenElement) return
  document.documentElement.requestFullscreen?.({ navigationUI: "hide" }).catch(() => { /* el navegador no lo permitió */ })
}

onMounted(() => {
  document.addEventListener("pointerdown", pantallaCompleta, { once: true, capture: true })
  latir()
  enviarCola()
  latido = setInterval(latir, 30000)
})
onBeforeUnmount(() => {
  clearInterval(latido); clearInterval(reintento); clearInterval(revisionCaja)
  document.removeEventListener("pointerdown", pantallaCompleta, { capture: true })
})
</script>
