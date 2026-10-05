<template>
  <div class="pantalla">
    <header class="barra">
      <div class="barra__titulo">
        <h1>{{ textos.cuentas }} abiertas</h1>
        <small>{{ sesion.mesero?.nombre }} · {{ sesion.nombre_dispositivo }}</small>
      </div>
      <button class="barra__btn" title="Actualizar" @click="cargar"><Icono nombre="refrescar" /></button>
      <button class="barra__btn" title="Salir" @click="salir"><Icono nombre="salir" /></button>
    </header>

    <main class="contenido">
      <div v-if="cargando && !cuentas.length" class="cargando"><span class="giro"></span></div>
      <div v-else-if="!cuentas.length" class="vacio">
        <Icono nombre="lista" :tam="40" />
        <p>No hay {{ t('cuentas') }} abiertas.</p>
      </div>

      <div class="cuentas">
        <button v-for="c in cuentas" :key="c.nro_pedido" class="cuenta tarjeta" @click="abrir(c)">
          <div class="cuenta__mesa">
            <Icono nombre="mesa" :tam="18" />
            <span>{{ c.mesa }}</span>
          </div>
          <div class="cuenta__total">{{ pesos(c.total) }}</div>
          <!-- Todos ven todas: un dispositivo lo usan varios meseros -->
          <div v-if="c.mesero" class="cuenta__mesero"><Icono nombre="usuario" :tam="14" /> {{ c.mesero }}</div>
          <div class="cuenta__info">
            <span><Icono nombre="reloj" :tam="14" /> {{ c.hora }}</span>
            <span>{{ cantidad(c.unidades) }} {{ c.unidades === 1 ? t("producto") : t("productos") }}</span>
          </div>
        </button>
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
import { api } from "../api"
import { cantidad, pesos } from "../formato"
import { cerrarSesion, sesion } from "../sesion"
import { t, textos } from "../textos"
import { showConfirm, showToast } from "@/utils/toast"

const router = useRouter()
const cuentas = ref([])
const cargando = ref(false)
let temporizador = null

async function cargar() {
  cargando.value = true
  try {
    cuentas.value = await api.get("/pedidos")
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

onMounted(() => { cargar(); temporizador = setInterval(cargar, 20000) })
onBeforeUnmount(() => clearInterval(temporizador))
</script>

<style scoped>
.pantalla { min-height: 100vh; padding-bottom: 90px; }
.cuentas { display: grid; grid-template-columns: 1fr; gap: 10px; }
.cuenta {
  display: grid; grid-template-columns: 1fr auto; gap: 6px 10px; align-items: center;
  width: 100%; padding: 14px; border: 0; text-align: left;
}
.cuenta:active { transform: scale(.99); }
.cuenta__mesa { display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 17px; min-width: 0; }
.cuenta__mesa span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cuenta__total { font-weight: 800; font-size: 17px; color: var(--azul); }
.cuenta__mesero { grid-column: 1 / -1; display: flex; align-items: center; gap: 5px; font-size: 14px; font-weight: 600; color: var(--navy); overflow-wrap: anywhere; }
.cuenta__info { grid-column: 1 / -1; display: flex; justify-content: space-between; color: var(--texto-suave); font-size: 13px; }
.cuenta__info span { display: inline-flex; align-items: center; gap: 4px; }
.accion-fija {
  position: fixed; left: 0; right: 0; bottom: 0; z-index: 10;
  padding: 12px 16px calc(12px + env(safe-area-inset-bottom));
  background: linear-gradient(transparent, var(--fondo) 30%);
}
.accion-fija .btn { max-width: 520px; margin: 0 auto; display: flex; box-shadow: 0 6px 18px rgba(37, 99, 235, .35); }

@media (min-width: 769px) {
  .cuentas { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 768px) and (min-width: 577px) {
  .cuentas { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 576px) {
  .cuenta { padding: 12px; }
  .cuenta__mesa, .cuenta__total { font-size: 16px; }
}
</style>
