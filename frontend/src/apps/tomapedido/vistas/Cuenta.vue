<template>
  <div class="pantalla">
    <header class="barra">
      <button class="barra__btn" @click="$router.replace('/cuentas')"><Icono nombre="atras" /></button>
      <div class="barra__titulo">
        <h1>{{ pedido?.mesa || textos.cuenta }}</h1>
        <small v-if="pedido">{{ pedido.mesero ? `${textos.mesero}: ${pedido.mesero} · ` : "" }}{{ pedido.cliente.nombre }} · {{ pedido.hora }}</small>
        <VersionAgente en-barra />
      </div>
      <!-- Número de comensales (solo si la empresa los pide: variables_del_sistema.Pedir_Cantidad_Comenzales) -->
      <button v-if="pedido?.pedir_comensales" class="barra__btn comensales" title="Cambiar número de comensales"
              @click="verComensales = true">
        <Icono nombre="personas" :tam="18" /><b>{{ pedido.comensales }}</b>
      </button>
      <BotonActualizar />
      <button class="barra__btn" title="Recargar la cuenta" @click="cargar"><Icono nombre="refrescar" /></button>
      <!-- Igual que la flecha (más visible): vuelve a las cuentas abiertas -->
      <button class="volver" @click="$router.replace('/cuentas')">Volver</button>
    </header>

    <main class="contenido">
      <div v-if="cargando && !pedido" class="cargando"><span class="giro"></span></div>

      <div v-if="pedido" class="tarjeta lista">
        <div v-for="l in lineasDesc" :key="l.depende" class="linea">
          <div class="linea__info">
            <b>{{ cantidad(l.cantidad) }} × {{ l.nombre }}</b>
            <small v-if="l.novedad">{{ l.novedad }}</small>
            <span class="estado" :class="l.impreso ? 'estado--impreso' : 'estado--pendiente'">
              <Icono :nombre="l.impreso ? 'impresora' : 'reloj'" :tam="13" />
              {{ l.impreso ? "Impreso" : "Por imprimir" }}
            </span>
          </div>
          <div class="linea__der">
            <b>{{ pesos(l.subtotal) }}</b>
          </div>
        </div>
        <div class="total"><span>Total</span><b>{{ pesos(pedido.total) }}</b></div>
      </div>
      <p class="nota">Lo enviado ya no se puede quitar desde aquí: para eliminar {{ t("productos") }} o la cuenta, solicítelo en caja.</p>
    </main>

    <div class="accion-fija">
      <button class="btn btn--primario btn--bloque" :disabled="!pedido"
              @click="$router.push({ path: '/pedido', query: { nro } })">
        <Icono nombre="mas" /> Agregar {{ t("productos") }}
      </button>
    </div>

    <TecladoComensales v-if="verComensales && pedido" :inicial="pedido.comensales" :titulo="pedido.mesa"
                       :guardando="guardandoComensales" @aceptar="guardarComensales" @cerrar="verComensales = false" />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue"
import { useRoute, useRouter } from "vue-router"
import Icono from "../componentes/Icono.vue"
import VersionAgente from "../componentes/VersionAgente.vue"
import BotonActualizar from "../componentes/BotonActualizar.vue"
import TecladoComensales from "../componentes/TecladoComensales.vue"
import { api } from "../api"
import { cantidad, pesos } from "../formato"
import { showToast } from "@/utils/toast"
import { t, textos } from "../textos"

const route = useRoute()
const router = useRouter()
const nro = String(route.query.nro || "")
const pedido = ref(null)
// Último ítem ingresado, primero en mostrar (Depende = primer ítem de la línea)
const lineasDesc = computed(() => [...(pedido.value?.lineas || [])].sort((a, b) => b.depende - a.depende))
const cargando = ref(false)
let temporizador = null

const verComensales = ref(false)
const guardandoComensales = ref(false)

async function guardarComensales(n) {
  if (n === pedido.value.comensales) { verComensales.value = false; return }
  guardandoComensales.value = true
  try {
    const r = await api.post("/pedido/comensales", { nro_pedido: nro, comensales: n })
    pedido.value.comensales = r.comensales
    verComensales.value = false
    showToast(`Comensales: ${r.comensales}`, "success", 1500)
  } catch (e) {
    showToast(e.message, "error", 4000)
    if (e.estado === 404) router.replace("/cuentas")
  } finally {
    guardandoComensales.value = false
  }
}

async function cargar() {
  cargando.value = true
  try {
    pedido.value = await api.get("/pedido", { nro })
  } catch (e) {
    showToast(e.message, "error", 3000)
    if (e.estado === 404) router.replace("/cuentas")     // ya se facturó o se eliminó
  } finally {
    cargando.value = false
  }
}

// El estado de impresión cambia cuando el escritorio imprime
onMounted(() => { cargar(); temporizador = setInterval(cargar, 15000) })
onBeforeUnmount(() => clearInterval(temporizador))
</script>

<style scoped>
.pantalla { min-height: 100vh; padding-bottom: 90px; }
.lista { padding: 4px 14px; max-width: 720px; margin: 0 auto; }
.linea { display: flex; justify-content: space-between; gap: 12px; padding: 12px 0; border-bottom: 1px solid var(--borde); }
.linea__info { min-width: 0; }
.linea__info b { display: block; word-break: break-word; }
.linea__info small { display: block; color: var(--texto-suave); font-size: 13px; }
.linea__der { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; flex-shrink: 0; }
.estado { display: inline-flex; align-items: center; gap: 4px; margin-top: 4px; padding: 2px 8px; border-radius: 999px; font-size: 12px; font-weight: 600; }
.estado--impreso { background: var(--verde-claro); color: var(--verde); }
.estado--pendiente { background: var(--ambar-claro); color: #92400e; }
.total { display: flex; justify-content: space-between; align-items: center; padding: 14px 0 10px; font-size: 18px; }
.total b { font-size: 22px; color: var(--azul); }
.comensales { width: auto; min-width: 40px; padding: 0 10px; gap: 5px; }
.comensales b { font-size: 16px; }
.volver { flex-shrink: 0; min-height: 38px; padding: 0 12px; border: 1.5px solid rgba(255,255,255,.5); border-radius: 10px; background: transparent; color: #fff; font-weight: 600; font-size: 14px; }
.volver:active { background: rgba(255,255,255,.15); }
.nota { text-align: center; color: var(--texto-suave); font-size: 13px; }
.accion-fija { position: fixed; left: 0; right: 0; bottom: 0; z-index: 10; padding: 12px 16px calc(12px + env(safe-area-inset-bottom)); background: linear-gradient(transparent, var(--fondo) 30%); }
.accion-fija .btn { max-width: 520px; margin: 0 auto; display: flex; box-shadow: 0 6px 18px rgba(37, 99, 235, .35); }

@media (min-width: 769px) {
  .lista { padding: 8px 20px; }
}
@media (max-width: 768px) {
  .total b { font-size: 20px; }
}
@media (max-width: 576px) {
  .barra { gap: 6px; padding: 0 8px; }
  .barra .barra__btn { width: 36px; height: 36px; }
  .barra .comensales { width: auto; padding: 0 8px; }
  .volver { padding: 0 9px; font-size: 13px; }
  .lista { padding: 2px 12px; }
  .total { font-size: 16px; }
}
</style>
