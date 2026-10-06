<template>
  <div class="pantalla">
    <header class="barra">
      <div class="barra__titulo">
        <h1>{{ textos.cuentas }} abiertas</h1>
        <small>{{ sesion.mesero?.nombre }} · {{ sesion.nombre_dispositivo }}</small>
      </div>
      <button v-if="puedeCompleta" class="barra__btn" :title="completa ? 'Salir de pantalla completa' : 'Pantalla completa'"
              @click="alternarCompleta"><Icono :nombre="completa ? 'contraer' : 'expandir'" /></button>
      <button class="barra__btn" title="Actualizar" @click="cargar"><Icono nombre="refrescar" /></button>
      <button class="barra__btn" title="Salir" @click="salir"><Icono nombre="salir" /></button>
    </header>

    <main class="contenido">
      <!-- Versión nueva del agente: los meseros la pueden instalar (usan más esta pantalla que el panel) -->
      <div v-if="actualizacion.lista || actualizacion.aplicando" class="aviso-act tarjeta">
        <span class="aviso-act__ico"><Icono nombre="refrescar" :tam="22" /></span>
        <div class="aviso-act__txt">
          <template v-if="actualizacion.aplicando">
            <b>Actualizando la toma de pedidos…</b>
            <small>Vuelve sola en menos de un minuto.</small>
          </template>
          <template v-else>
            <b>Actualización disponible: versión {{ actualizacion.nueva }}</b>
            <small v-if="actualizacion.notas">{{ actualizacion.notas }}</small>
            <small>Si no la aplica ahora, se instala sola al abrir el próximo turno.</small>
          </template>
        </div>
        <button v-if="!actualizacion.aplicando" class="btn btn--primario aviso-act__btn" :disabled="actualizando"
                @click="actualizar">Actualizar ahora</button>
      </div>
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
import TarjetaCuenta from "../componentes/TarjetaCuenta.vue"
import { actualizacion, api, preferencias } from "../api"
import { cerrarSesion, sesion } from "../sesion"
import { t, textos } from "../textos"
import { showConfirm, showToast } from "@/utils/toast"

const router = useRouter()
const cuentas = ref([])
const cargando = ref(false)
const actualizando = ref(false)
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

async function actualizar() {
  if (!(await showConfirm("Mientras se actualiza (menos de un minuto) ningún dispositivo podrá tomar pedidos. "
    + "Los pedidos ya enviados no se pierden. ¿Actualizar ahora?", "Sí, actualizar"))) return
  actualizando.value = true
  try {
    await api.post("/actualizar")
    actualizacion.aplicando = true
    showToast("Actualizando… la toma de pedidos vuelve en menos de un minuto.", "info", 5000)
  } catch (e) {
    showToast(e.message, "error", 4000)
  } finally {
    actualizando.value = false
  }
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
.aviso-act { display: flex; align-items: center; gap: 12px; padding: 14px; margin-bottom: 12px; border: 2px solid var(--azul); }
.aviso-act__ico { width: 44px; height: 44px; flex-shrink: 0; border-radius: 12px; background: var(--azul-claro); color: var(--azul);
                  display: inline-flex; align-items: center; justify-content: center; }
.aviso-act__txt { flex: 1; min-width: 0; }
.aviso-act__txt b { display: block; }
.aviso-act__txt small { display: block; color: var(--texto-suave); font-size: 13px; overflow-wrap: anywhere; }
.aviso-act__btn { flex-shrink: 0; }
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
  .aviso-act { flex-wrap: wrap; }
  .aviso-act__btn { width: 100%; }
}
@media (max-width: 576px) {
  .cuentas { gap: 12px; }
}
</style>
