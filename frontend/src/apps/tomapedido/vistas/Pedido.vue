<template>
  <div class="pantalla">
    <header class="barra">
      <button class="barra__btn" @click="volver"><Icono nombre="atras" /></button>
      <div class="barra__titulo">
        <h1>{{ nro ? "Agregar a " : "" }}{{ titulo }}</h1>
        <small>
          <button class="cliente-btn" :disabled="!!nro" @click="verCliente = true">
            <Icono nombre="usuario" :tam="13" /> {{ cliente?.nombre || "…" }}
          </button>
        </small>
      </div>
    </header>

    <div class="filtros" :class="{ 'filtros--ancho': esPC }">
      <div class="filtros__fila">
        <!-- Categorías en lista vertical: panel lateral (celular/tablet) o columna fija (PC) -->
        <button class="hamburguesa" title="Categorías" @click="alternarCategorias"><Icono nombre="menu" :tam="22" /></button>
        <div class="buscar">
          <Icono nombre="buscar" />
          <input v-model="texto" class="entrada" placeholder="Buscar producto" />
          <button v-if="texto" class="buscar__limpiar" @click="texto = ''"><Icono nombre="cerrar" :tam="16" /></button>
        </div>
      </div>
      <div class="chips">
        <button class="chip" :class="{ 'chip--activo': categoriaId === null }" @click="escogerCategoria(null)">Todo</button>
        <button v-for="c in carta?.categorias || []" :key="c.id" class="chip" :class="{ 'chip--activo': categoriaId === c.id }"
                @click="escogerCategoria(c.id)">{{ c.nombre }}</button>
      </div>
    </div>

    <div class="cuerpo" :class="{ 'cuerpo--lateral': esPC && lateralAbierto }">
      <aside v-if="esPC && lateralAbierto" class="lateral">
        <nav class="categorias">
          <button class="categoria" :class="{ 'categoria--activa': categoriaId === null && !texto }" @click="escogerCategoria(null)">
            <span>Todo</span><small>{{ carta?.platos.length || 0 }}</small>
          </button>
          <button v-for="c in carta?.categorias || []" :key="c.id" class="categoria"
                  :class="{ 'categoria--activa': categoriaId === c.id && !texto }" @click="escogerCategoria(c.id)">
            <span>{{ c.nombre }}</span><small>{{ conteo[c.id] || 0 }}</small>
          </button>
        </nav>
      </aside>
    <main class="contenido">
      <div v-if="cargando" class="cargando"><span class="giro"></span></div>
      <p v-else-if="!productos.length" class="vacio">No hay productos {{ texto ? "con ese nombre" : "en esta categoría" }}.</p>
      <div class="productos">
        <button v-for="p in productos" :key="p.id" class="producto tarjeta" @click="hojaProducto = p">
          <span class="producto__nombre">{{ p.nombre }}</span>
          <span class="producto__pie">
            <b>{{ p.pedir_precio ? "Precio libre" : pesos(p.precio) }}</b>
            <span v-if="etiqueta(p)" class="producto__tag">{{ etiqueta(p) }}</span>
          </span>
          <span v-if="enCarrito[p.id]" class="producto__cuenta">{{ cantidad(enCarrito[p.id]) }}</span>
        </button>
      </div>
    </main>
    </div>

    <!-- Panel de categorías (celular y tablet) -->
    <div v-if="verCategorias" class="velo velo--izq" @click.self="verCategorias = false">
      <aside class="cajon">
        <div class="cajon__cab">
          <b>Categorías</b>
          <button class="barra__btn" @click="verCategorias = false"><Icono nombre="cerrar" /></button>
        </div>
        <nav class="categorias">
          <button class="categoria" :class="{ 'categoria--activa': categoriaId === null && !texto }" @click="escogerCategoria(null)">
            <span>Todo</span><small>{{ carta?.platos.length || 0 }}</small>
          </button>
          <button v-for="c in carta?.categorias || []" :key="c.id" class="categoria"
                  :class="{ 'categoria--activa': categoriaId === c.id && !texto }" @click="escogerCategoria(c.id)">
            <span>{{ c.nombre }}</span><small>{{ conteo[c.id] || 0 }}</small>
          </button>
        </nav>
      </aside>
    </div>

    <div v-if="lineas.length" class="carrito-barra">
      <button class="btn btn--primario btn--bloque" @click="verCarrito = true">
        <Icono nombre="carrito" />
        <span>Ver pedido ({{ lineas.length }})</span>
        <b class="carrito-barra__total">{{ pesos(total) }}</b>
      </button>
    </div>

    <ProductoSheet v-if="hojaProducto" :plato="hojaProducto" :novedades="novedadesDe(hojaProducto)"
                   @agregar="agregar" @cerrar="hojaProducto = null" />
    <CarritoSheet v-if="verCarrito" :lineas="lineas" :titulo="titulo" :enviando="enviando"
                  @quitar="quitar" @enviar="enviar" @cerrar="verCarrito = false" />
    <ClienteSheet v-if="verCliente && config" :actual="cliente" :por-defecto="config.cliente_default"
                  @escoger="cambiarCliente" @cerrar="verCliente = false" />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue"
import { onBeforeRouteLeave, useRoute, useRouter } from "vue-router"
import Icono from "../componentes/Icono.vue"
import ProductoSheet from "../componentes/ProductoSheet.vue"
import CarritoSheet from "../componentes/CarritoSheet.vue"
import ClienteSheet from "../componentes/ClienteSheet.vue"
import { api } from "../api"
import { cantidad, pesos, valorLinea } from "../formato"
import { showConfirm, showToast } from "@/utils/toast"

const route = useRoute()
const router = useRouter()

// Modo: pedido nuevo en una mesa, cuenta nueva con nombre, o agregar a una cuenta abierta
const nro = route.query.nro || null
const mesa = route.query.mesa != null ? { id: Number(route.query.mesa), nombre: String(route.query.nombre) } : null
const cuentaNueva = route.query.cuenta ? String(route.query.cuenta) : null

const config = ref(null)
const cliente = ref(null)
const carta = ref(null)
const titulo = ref(mesa?.nombre || cuentaNueva?.toUpperCase() || "")
const categoriaId = ref(null)
const texto = ref("")
const lineas = ref([])
const cargando = ref(true)
const enviando = ref(false)
const hojaProducto = ref(null)
const verCarrito = ref(false)
const verCliente = ref(false)
let mesaBloqueo = mesa ? { id_mesa: mesa.id, mesa: mesa.nombre } : null
let enviado = false
let latido = null

const sinTildes = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
const productos = computed(() => {
  if (!carta.value) return []
  const t = sinTildes(texto.value.trim())
  return carta.value.platos.filter(p =>
    (t ? sinTildes(p.nombre).includes(t) : categoriaId.value === null || p.categoria === categoriaId.value))
})
const total = computed(() => lineas.value.reduce((s, l) => s + valorLinea(l.unitario, l.cantidad), 0))
const conteo = computed(() => (carta.value?.platos || []).reduce((m, p) => (m[p.categoria] = (m[p.categoria] || 0) + 1, m), {}))

// PC (> 1024 px): columna fija de categorías que el botón ☰ oculta o muestra; celular/tablet: panel lateral
const consultaPC = window.matchMedia("(min-width: 1025px)")
const esPC = ref(consultaPC.matches)
const verCategorias = ref(false)
const alCambiarAncho = (e) => { esPC.value = e.matches; verCategorias.value = false }
const lateralAbierto = ref((() => { try { return localStorage.getItem("ag_lateral") !== "0" } catch { return true } })())

function alternarCategorias() {
  if (!esPC.value) { verCategorias.value = true; return }
  lateralAbierto.value = !lateralAbierto.value
  try { localStorage.setItem("ag_lateral", lateralAbierto.value ? "1" : "0") } catch { /* sin almacenamiento */ }
}

function escogerCategoria(id) {
  categoriaId.value = id
  texto.value = ""
  verCategorias.value = false
  window.scrollTo({ top: 0, behavior: "smooth" })
}

const enCarrito = computed(() => lineas.value.reduce((m, l) => (m[l.id_plato] = (m[l.id_plato] || 0) + l.cantidad, m), {}))

function etiqueta(p) {
  if (p.armado === "menu") return "Menú del día"
  if (p.armado === "armado") return "Armar"
  if (p.presentaciones) return `${p.presentaciones.length} presentaciones`
  return ""
}
const novedadesDe = (p) => carta.value?.novedades?.[String(p.categoria)] || []

async function cargarCarta() {
  carta.value = await api.catalogo(cliente.value.id)
}

// Cambiar de cliente cambia la lista de precios: se recalcula lo que ya está en el carrito
async function cambiarCliente(c) {
  verCliente.value = false
  if (c.id === cliente.value?.id) return
  cliente.value = c
  cargando.value = true
  try {
    await cargarCarta()
    for (const l of lineas.value) {
      const p = carta.value.platos.find(x => x.id === l.id_plato)
      if (!p || p.pedir_precio) continue
      const pres = l.presentacion != null ? p.presentaciones?.find(x => x.id === l.presentacion) : null
      l.unitario = (pres ? pres.precio : p.precio) + l.adicional
    }
    showToast(`Precios de ${c.nombre}`, "info", 1800)
  } catch (e) {
    showToast(e.message, "error", 3000)
  } finally {
    cargando.value = false
  }
}

function agregar(linea) {
  lineas.value.push(linea)
  hojaProducto.value = null
  showToast(`${linea.nombre} agregado`, "success", 1000)
}

function quitar(l) {
  lineas.value = lineas.value.filter(x => x.clave !== l.clave)
  if (!lineas.value.length) verCarrito.value = false
}

async function enviar() {
  enviando.value = true
  const detalle = lineas.value.map(l => ({
    id_plato: l.id_plato, cantidad: l.cantidad, presentacion: l.presentacion, precio: l.precio,
    descripcion: l.descripcion, novedades: l.novedades, opciones: l.opciones,
  }))
  try {
    let numero = nro
    if (nro) {
      await api.post("/pedido/agregar", { nro_pedido: nro, lineas: detalle })
    } else {
      const r = await api.post("/pedidos", {
        ...(mesa ? { mesa } : { cuenta_nueva: cuentaNueva }),
        id_cliente: cliente.value.id, lineas: detalle,
      })
      numero = r.nro_pedido
      mesaBloqueo = null            // el agente libera la mesa al crear el pedido
    }
    enviado = true
    showToast("Pedido enviado", "success", 1800)
    router.replace({ path: "/cuenta", query: { nro: numero } })
  } catch (e) {
    showToast(e.message, "error", 4000)
  } finally {
    enviando.value = false
  }
}

async function bloquear() {
  if (!mesaBloqueo) return
  try { await api.post("/mesas/bloquear", mesaBloqueo) }
  catch (e) {
    showToast(e.message, "error", 4000)
    if (e.estado === 409) { mesaBloqueo = null; router.replace("/cuentas") }
  }
}

function volver() {
  router.back()
}

onBeforeRouteLeave(async () => {
  if (lineas.value.length && !enviado &&
      !(await showConfirm("Tiene productos sin enviar. ¿Salir y descartarlos?", "Sí, descartar"))) return false
  return true
})

onMounted(async () => {
  consultaPC.addEventListener("change", alCambiarAncho)
  try {
    config.value = await api.get("/config")
    cliente.value = config.value.cliente_default
    if (nro) {
      const p = await api.get("/pedido", { nro })
      cliente.value = p.cliente
      titulo.value = p.mesa
      mesaBloqueo = { id_mesa: p.id_mesa, mesa: p.mesa }
      await api.post("/mesas/bloquear", mesaBloqueo)
    }
    await cargarCarta()
    // Mantiene la mesa bloqueada mientras se toma el pedido (el bloqueo vence a los 10 min)
    if (mesaBloqueo) latido = setInterval(bloquear, 4 * 60 * 1000)
  } catch (e) {
    showToast(e.message, "error", 4000)
    mesaBloqueo = null
    router.replace("/cuentas")
  } finally {
    cargando.value = false
  }
})

onBeforeUnmount(() => {
  consultaPC.removeEventListener("change", alCambiarAncho)
  clearInterval(latido)
  if (mesaBloqueo) api.post("/mesas/liberar", mesaBloqueo).catch(() => {})
})
</script>

<style scoped>
.pantalla { min-height: 100vh; padding-bottom: 96px; }
.cliente-btn { display: inline-flex; align-items: center; gap: 4px; max-width: 100%; padding: 0; border: 0; background: none; color: inherit; font-size: 12px; opacity: .9; text-decoration: underline; text-underline-offset: 2px; }
.cliente-btn:disabled { text-decoration: none; cursor: default; }

.filtros { position: sticky; top: var(--barra-alto); z-index: 15; background: var(--fondo); padding: 10px 12px 0; max-width: 1100px; margin: 0 auto; }
.filtros--ancho { max-width: 1320px; }
.filtros__fila { display: flex; gap: 8px; margin-bottom: 8px; }
.hamburguesa { width: 48px; height: 48px; flex-shrink: 0; border-radius: 12px; border: 1.5px solid var(--borde); background: #fff; color: var(--navy); display: inline-flex; align-items: center; justify-content: center; }
.hamburguesa:active { background: var(--azul-claro); }
.buscar { position: relative; flex: 1; }
.buscar > .icono { position: absolute; left: 14px; top: 14px; color: var(--texto-suave); }
.buscar .entrada { padding-left: 42px; padding-right: 42px; }
.buscar__limpiar { position: absolute; right: 6px; top: 6px; width: 36px; height: 36px; border: 0; border-radius: 8px; background: var(--fondo); display: inline-flex; align-items: center; justify-content: center; }

/* Lista vertical de categorías (columna en PC y panel en celular/tablet) */
.categorias { display: flex; flex-direction: column; gap: 6px; }
.categoria {
  display: flex; align-items: center; justify-content: space-between; gap: 8px;
  min-height: 48px; padding: 0 14px; border: 0; border-radius: 12px; background: #fff;
  box-shadow: var(--sombra); text-align: left; font-weight: 600;
}
.categoria small { flex-shrink: 0; padding: 2px 8px; border-radius: 999px; background: var(--fondo); color: var(--texto-suave); font-size: 12px; }
.categoria--activa { background: var(--navy); color: #fff; }
.categoria--activa small { background: rgba(255, 255, 255, .18); color: #fff; }

.cuerpo--lateral { display: grid; grid-template-columns: 250px 1fr; max-width: 1320px; margin: 0 auto; }
.cuerpo--lateral .contenido { max-width: none; margin: 0; }
.lateral {
  position: sticky; top: calc(var(--barra-alto) + 112px); align-self: start;
  max-height: calc(100vh - var(--barra-alto) - 130px); overflow-y: auto; padding: 20px 0 20px 20px;
}

.velo.velo--izq { align-items: stretch; justify-content: flex-start; }
.cajon {
  width: min(82vw, 320px); height: 100%; display: flex; flex-direction: column;
  background: var(--fondo); animation: entrar .18s ease-out;
}
@keyframes entrar { from { transform: translateX(-30px); opacity: .6; } }
.cajon__cab {
  display: flex; align-items: center; justify-content: space-between; gap: 10px;
  padding: 10px 12px; padding-top: calc(10px + env(safe-area-inset-top));
  background: var(--navy); color: #fff; font-size: 17px;
}
.cajon .categorias { flex: 1; overflow-y: auto; padding: 12px; padding-bottom: calc(12px + env(safe-area-inset-bottom)); }

.productos { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
.producto {
  position: relative; display: flex; flex-direction: column; justify-content: space-between; gap: 10px;
  min-height: 96px; padding: 12px; border: 0; text-align: left;
}
.producto:active { transform: scale(.98); }
.producto__nombre { font-weight: 700; font-size: 15px; line-height: 1.25; word-break: break-word; }
.producto__pie { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 4px; }
.producto__pie b { color: var(--azul); }
.producto__tag { font-size: 11px; padding: 2px 8px; border-radius: 999px; background: var(--ambar-claro); color: #92400e; }
.producto__cuenta {
  position: absolute; top: -6px; right: -6px; min-width: 26px; height: 26px; padding: 0 6px;
  border-radius: 999px; background: var(--verde); color: #fff; font-size: 13px; font-weight: 700;
  display: inline-flex; align-items: center; justify-content: center;
}

.carrito-barra { position: fixed; left: 0; right: 0; bottom: 0; z-index: 30; padding: 10px 12px calc(10px + env(safe-area-inset-bottom)); background: linear-gradient(transparent, var(--fondo) 30%); }
.carrito-barra .btn { max-width: 620px; margin: 0 auto; display: flex; justify-content: flex-start; box-shadow: 0 6px 18px rgba(37, 99, 235, .35); }
.carrito-barra__total { margin-left: auto; }

@media (min-width: 1025px) {
  .cuerpo--lateral .productos { grid-template-columns: repeat(3, 1fr); }
}
@media (min-width: 1300px) {
  .cuerpo--lateral .productos { grid-template-columns: repeat(4, 1fr); }
}
@media (min-width: 769px) {
  .productos { grid-template-columns: repeat(4, 1fr); }
  .filtros { padding: 14px 20px 0; }
}
@media (max-width: 768px) and (min-width: 577px) {
  .productos { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 576px) {
  .productos { gap: 8px; }
  .producto { min-height: 88px; padding: 10px; }
  .producto__nombre { font-size: 14px; }
}
</style>
