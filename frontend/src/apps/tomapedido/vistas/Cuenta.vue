<template>
  <div class="pantalla">
    <header class="barra">
      <button class="barra__btn" @click="$router.replace('/cuentas')"><Icono nombre="atras" /></button>
      <div class="barra__titulo">
        <h1>{{ pedido?.mesa || textos.cuenta }}</h1>
        <small v-if="pedido">{{ pedido.cliente.nombre }} · {{ pedido.hora }}</small>
      </div>
      <button class="barra__btn" title="Actualizar" @click="cargar"><Icono nombre="refrescar" /></button>
    </header>

    <main class="contenido">
      <div v-if="cargando && !pedido" class="cargando"><span class="giro"></span></div>

      <div v-if="pedido" class="tarjeta lista">
        <div v-for="l in pedido.lineas" :key="l.depende" class="linea">
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
            <button v-if="l.puede_quitar" class="quitar" :disabled="quitando" title="Quitar" @click="quitar(l)">
              <Icono nombre="basura" :tam="18" />
            </button>
          </div>
        </div>
        <div class="total"><span>Total</span><b>{{ pesos(pedido.total) }}</b></div>
      </div>
      <p class="nota">Solo puede quitar {{ t("productos") }} que aún no se han impreso.</p>
    </main>

    <div class="accion-fija">
      <button class="btn btn--primario btn--bloque" :disabled="!pedido"
              @click="$router.push({ path: '/pedido', query: { nro } })">
        <Icono nombre="mas" /> Agregar {{ t("productos") }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue"
import { useRoute, useRouter } from "vue-router"
import Icono from "../componentes/Icono.vue"
import { api } from "../api"
import { cantidad, pesos } from "../formato"
import { showConfirm, showToast } from "@/utils/toast"
import { t, textos } from "../textos"

const route = useRoute()
const router = useRouter()
const nro = String(route.query.nro || "")
const pedido = ref(null)
const cargando = ref(false)
const quitando = ref(false)
let temporizador = null

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

async function quitar(l) {
  if (!(await showConfirm(`¿Quitar ${l.nombre} del pedido?`, "Sí, quitar"))) return
  quitando.value = true
  try {
    const r = await api.post("/pedido/quitar", { nro_pedido: nro, depende: l.depende })
    if (r.pedido_eliminado) {
      showToast("El pedido quedó vacío y se eliminó.", "info", 2500)
      return router.replace("/cuentas")
    }
    showToast(`${textos.producto} quitado`, "success", 1200)
    await cargar()
  } catch (e) {
    showToast(e.message, "error", 3500)
    await cargar()
  } finally {
    quitando.value = false
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
.quitar { width: 38px; height: 38px; border: 0; border-radius: 10px; background: var(--rojo-claro); color: var(--rojo); display: inline-flex; align-items: center; justify-content: center; }
.total { display: flex; justify-content: space-between; align-items: center; padding: 14px 0 10px; font-size: 18px; }
.total b { font-size: 22px; color: var(--azul); }
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
  .lista { padding: 2px 12px; }
  .total { font-size: 16px; }
}
</style>
