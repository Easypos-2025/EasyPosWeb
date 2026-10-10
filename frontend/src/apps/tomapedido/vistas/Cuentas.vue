<template>
  <div class="pantalla">
    <header class="barra">
      <div class="barra__titulo">
        <h1>{{ textos.cuentas }} abiertas</h1>
        <small>{{ sesion.mesero?.nombre }} · {{ sesion.nombre_dispositivo }}</small>
        <VersionAgente en-barra />
      </div>
      <BotonActualizar />
      <button v-if="puedeCompleta" class="barra__btn" :title="completa ? 'Salir de pantalla completa' : 'Pantalla completa'"
              @click="alternarCompleta"><Icono :nombre="completa ? 'contraer' : 'expandir'" /></button>
      <button class="barra__btn" title="Actualizar" @click="cargar"><Icono nombre="refrescar" /></button>
      <button class="barra__btn" title="Salir" @click="salir"><Icono nombre="salir" /></button>
    </header>

    <main class="contenido">
      <div v-if="cargando && !cuentas.length" class="cargando"><span class="giro"></span></div>
      <div v-else-if="!cuentas.length" class="vacio">
        <Icono nombre="lista" :tam="40" />
        <p>No hay {{ t('cuentas') }} abiertas.</p>
      </div>

      <!-- Todas las cuentas (un dispositivo lo usan varios meseros), con el estilo de tarjetas de la web -->
      <div class="cuentas">
        <TarjetaCuenta v-for="c in cuentas" :key="c.nro_pedido" :cuenta="c" :estilo="preferencias.estilo"
                       :ahora="ahora" @abrir="abrir(c)" />
      </div>
    </main>

    <div class="accion-fija">
      <button class="btn btn--primario btn--bloque" @click="$router.push('/mesas')">
        <Icono nombre="mas" /> Nuevo pedido
      </button>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import Icono from "../componentes/Icono.vue"
import VersionAgente from "../componentes/VersionAgente.vue"
import BotonActualizar from "../componentes/BotonActualizar.vue"
import TarjetaCuenta from "../componentes/TarjetaCuenta.vue"
import { api, preferencias } from "../api"
import { cerrarSesion, sesion } from "../sesion"
import { t, textos } from "../textos"
import { showConfirm, showToast } from "@/utils/toast"

const router = useRouter()
const cuentas = ref([])
const cargando = ref(false)
const ahora = ref(Date.now())             // la alerta de "más de una hora abierta" se refresca con cada carga
let temporizador = null

// Pantalla completa (iPhone no la permite en páginas: allí se usa "Agregar a inicio")
const puedeCompleta = !!document.fullscreenEnabled
const completa = ref(!!document.fullscreenElement)
const alCambiarCompleta = () => { completa.value = !!document.fullscreenElement }
function alternarCompleta() {
  if (document.fullscreenElement) document.exitFullscreen().catch(() => {})
  else document.documentElement.requestFullscreen?.({ navigationUI: "hide" }).catch(() => {})
}

async function cargar() {
  cargando.value = true
  try {
    cuentas.value = await api.get("/pedidos")
    ahora.value = Date.now()
  } catch (e) {
    showToast(e.message, "error", 3000)
  } finally {
    cargando.value = false
  }
}

function abrir(c) {
  router.push({ path: "/cuenta", query: { nro: c.nro_pedido } })
}

async function salir() {
  if (!(await showConfirm("¿Cerrar la sesión en este dispositivo?", "Sí, salir"))) return
  try { await api.post("/sesion/salir") } catch { /* igual se cierra en el dispositivo */ }
  cerrarSesion()
  router.replace("/ingresar")
}

onMounted(() => {
  cargar(); temporizador = setInterval(cargar, 20000)
  document.addEventListener("fullscreenchange", alCambiarCompleta)
})
onBeforeUnmount(() => {
  clearInterval(temporizador)
  document.removeEventListener("fullscreenchange", alCambiarCompleta)
})
</script>

<style scoped>
.pantalla { min-height: 100vh; padding-bottom: 90px; }
.cuentas { display: flex; flex-wrap: wrap; justify-content: center; align-items: center; gap: 18px; padding: 6px 0 10px; }
.accion-fija {
  position: fixed; left: 0; right: 0; bottom: 0; z-index: 10;
  padding: 12px 16px calc(12px + env(safe-area-inset-bottom));
  background: linear-gradient(transparent, var(--fondo) 30%);
}
.accion-fija .btn { max-width: 520px; margin: 0 auto; display: flex; box-shadow: 0 6px 18px rgba(37, 99, 235, .35); }

@media (min-width: 769px) {
  .cuentas { gap: 24px; justify-content: flex-start; }
}
@media (max-width: 768px) {
  .cuentas { gap: 14px; }
}
@media (max-width: 576px) {
  .cuentas { gap: 12px; }
}
</style>
