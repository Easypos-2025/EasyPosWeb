<template>
  <div>
    <div class="cab">
      <h2>Pedidos web</h2>
      <button class="btn btn--chico" :disabled="cargando" @click="cargar"><Icono nombre="refrescar" :tam="16" /> Actualizar</button>
    </div>
    <p class="sub">Pedidos y productos enviados desde EasyPosWeb. No pasan al escritorio ni se imprimen hasta que se acepten aquí
      o en la pantalla de pedidos web del programa de escritorio.</p>

    <div class="chips">
      <button class="chip" :class="{ 'chip--activo': vista === 'pendientes' }" @click="cambiarVista('pendientes')">
        Pendientes <b v-if="pendientes" class="cuenta">{{ pendientes }}</b></button>
      <button class="chip" :class="{ 'chip--activo': vista === 'procesados' }" @click="cambiarVista('procesados')">Procesados</button>
    </div>

    <div v-if="vista === 'procesados'" class="dia">
      <button class="btn btn--chico" title="Día anterior" @click="moverDia(-1)"><Icono nombre="atras" :tam="16" /></button>
      <b>{{ diaTexto }}</b>
      <button class="btn btn--chico" title="Día siguiente" :disabled="esHoy" @click="moverDia(1)">
        <Icono nombre="atras" :tam="16" style="transform: rotate(180deg)" /></button>
      <button v-if="!esHoy" class="btn btn--chico" @click="fecha = hoy(); cargar()">Hoy</button>
    </div>

    <div v-if="vista === 'pendientes' && lista.length" class="acciones">
      <label class="todos"><input type="checkbox" :checked="todosMarcados" @change="marcarTodos($event.target.checked)" />
        Marcar todos</label>
      <button class="btn btn--chico btn--primario" :disabled="!marcados.length" @click="abrir('ACEPTADO')">
        <Icono nombre="check" :tam="16" /> Aceptar ({{ marcados.length }})</button>
      <button class="btn btn--chico btn--peligro" :disabled="!marcados.length" @click="abrir('RECHAZADO')">
        <Icono nombre="cerrar" :tam="16" /> Rechazar ({{ marcados.length }})</button>
    </div>

    <div v-if="cargando && !lista.length" class="cargando"><span class="giro"></span></div>
    <p v-else-if="!lista.length" class="vacio">
      {{ vista === "pendientes" ? "No hay pedidos web pendientes." : "No hay pedidos procesados en esta fecha." }}</p>

    <div v-for="l in lista" :key="l.id" class="lote tarjeta" :class="'lote--' + l.estado.toLowerCase()">
      <div class="lote__cab">
        <input v-if="vista === 'pendientes' && l.estado !== 'ACEPTADO'" type="checkbox" class="marca"
               :checked="marcados.includes(l.id)" @change="alternar(l.id)" />
        <div class="lote__tit" @click="verDetalle(l)">
          <b>{{ l.mesa || "Sin mesa" }} · {{ l.tipo === "NUEVO" ? "Pedido nuevo" : "Productos agregados" }}</b>
          <small>{{ l.mesero || "—" }} · {{ l.items }} {{ l.items === 1 ? "producto" : "productos" }} · {{ hora(l.creado_en) }}</small>
        </div>
        <div class="lote__der">
          <b>{{ pesos(l.total) }}</b>
          <span class="estado">{{ ESTADO[l.estado] || l.estado }}</span>
        </div>
      </div>
      <p v-if="l.estado === 'ERROR'" class="aviso">{{ l.mensaje }}</p>
      <p v-if="l.estado === 'ACEPTADO'" class="info">Aceptado: pasando al escritorio…</p>
      <p v-if="l.estado === 'RECHAZADO'" class="info">Motivo: {{ l.motivo }}</p>
      <p v-if="vista === 'procesados'" class="info">
        {{ l.estado === "APLICADO" ? "Aceptado" : "Rechazado" }} por {{ l.procesado_por || "—" }}
        ({{ l.procesado_desde === "VB" ? "escritorio" : "panel" }}{{ l.pc ? " · " + l.pc : "" }}) · {{ hora(l.procesado_en) }}</p>

      <div v-if="detalle && detalle.id === l.id" class="det">
        <div v-for="d in detalle.detalle" :key="d.item" class="det__fila">
          <span class="det__cant">{{ cantidad(d.cantidad) }}</span>
          <div class="det__nom"><b>{{ d.nombre }}</b><small v-if="d.novedad">{{ d.novedad }}</small></div>
          <span>{{ pesos(d.valor) }}</span>
        </div>
        <small class="nro">Pedido {{ l.nro_pedido }} · enviado por {{ l.enviado_por || "—" }}</small>
      </div>
    </div>

    <div v-if="dialogo" class="velo" @click.self="dialogo = null">
      <form class="hoja" @submit.prevent="procesar">
        <div class="hoja__cab"><h2>{{ dialogo.accion === "ACEPTADO" ? "Aceptar" : "Rechazar" }} {{ marcados.length }}
          {{ marcados.length === 1 ? "pedido" : "pedidos" }}</h2>
          <button type="button" class="cerrar" @click="dialogo = null"><Icono nombre="cerrar" /></button></div>
        <div class="hoja__cuerpo">
          <p v-if="dialogo.accion === 'ACEPTADO'" class="sub">Pasan al escritorio y se envían a impresión.</p>
          <p v-else class="sub">Los productos salen del pedido en la web; solo quedan en el histórico. Deben montarse de nuevo si se desean.</p>
          <label class="campo"><span>Su nombre</span>
            <input v-model.trim="dialogo.por" class="entrada" maxlength="60" required autocomplete="off" /></label>
          <label v-if="dialogo.accion === 'RECHAZADO'" class="campo"><span>Motivo del rechazo</span>
            <textarea v-model.trim="dialogo.motivo" class="entrada" rows="3" maxlength="255" required></textarea></label>
        </div>
        <div class="hoja__pie">
          <button class="btn btn--bloque" :class="dialogo.accion === 'ACEPTADO' ? 'btn--primario' : 'btn--peligro'"
                  :disabled="enviando || dialogo.por.length < 2 || (dialogo.accion === 'RECHAZADO' && dialogo.motivo.length < 3)">
            {{ dialogo.accion === "ACEPTADO" ? "Aceptar" : "Rechazar" }}</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, inject, onBeforeUnmount, onMounted, ref } from "vue"
import Icono from "../../componentes/Icono.vue"
import { api } from "../../api"
import { cantidad, pesos } from "../../formato"
import { showToast } from "@/utils/toast"

const ESTADO = { PENDIENTE: "Pendiente", ACEPTADO: "Aceptado", APLICADO: "Aceptado", RECHAZADO: "Rechazado", ERROR: "No se pudo pasar" }
const CLAVE_NOMBRE = "ag_pw_nombre"

const recargarResumen = inject("recargarResumen", () => {})
const vista = ref("pendientes")
const lista = ref([])
const cargando = ref(false)
const marcados = ref([])
const detalle = ref(null)
const dialogo = ref(null)
const enviando = ref(false)

const hoy = () => new Intl.DateTimeFormat("en-CA", { timeZone: "America/Bogota" }).format(new Date())
const fecha = ref(hoy())
const esHoy = computed(() => fecha.value >= hoy())
const diaTexto = computed(() => new Date(fecha.value + "T12:00:00").toLocaleDateString("es-CO",
  { weekday: "long", day: "numeric", month: "long", year: "numeric" }))
const pendientes = computed(() => vista.value === "pendientes" ? lista.value.filter(l => l.estado !== "ACEPTADO").length : 0)
const seleccionables = computed(() => lista.value.filter(l => l.estado !== "ACEPTADO").map(l => l.id))
const todosMarcados = computed(() => seleccionables.value.length > 0 && seleccionables.value.every(i => marcados.value.includes(i)))
const hora = (v) => (v ? new Date(v).toLocaleString("es-CO", { dateStyle: "short", timeStyle: "short" }) : "—")
let temporizador = null

async function cargar() {
  cargando.value = true
  try {
    const r = await api.admin.get("/pedidos-web", vista.value === "pendientes" ? { vista: "pendientes" } : { vista: "procesados", fecha: fecha.value })
    lista.value = r.lotes
    marcados.value = marcados.value.filter(i => seleccionables.value.includes(i))
  } catch (e) { showToast(e.message, "error", 3500) }
  finally { cargando.value = false }
}

function cambiarVista(v) { vista.value = v; marcados.value = []; detalle.value = null; lista.value = []; cargar() }
function moverDia(n) {
  const d = new Date(fecha.value + "T12:00:00"); d.setDate(d.getDate() + n)
  fecha.value = d.toISOString().slice(0, 10); cargar()
}
function alternar(id) { marcados.value = marcados.value.includes(id) ? marcados.value.filter(i => i !== id) : [...marcados.value, id] }
function marcarTodos(si) { marcados.value = si ? [...seleccionables.value] : [] }

async function verDetalle(l) {
  if (detalle.value?.id === l.id) { detalle.value = null; return }
  try { detalle.value = await api.admin.get(`/pedidos-web/${l.id}`) } catch (e) { showToast(e.message, "error", 3500) }
}

function abrir(accion) {
  let por = ""
  try { por = localStorage.getItem(CLAVE_NOMBRE) || "" } catch { /* sin almacenamiento */ }
  dialogo.value = { accion, por, motivo: "" }
}

async function procesar() {
  const d = dialogo.value
  enviando.value = true
  try {
    const ruta = d.accion === "ACEPTADO" ? "/pedidos-web/aceptar" : "/pedidos-web/rechazar"
    const r = await api.admin.post(ruta, { ids: marcados.value, por: d.por, motivo: d.motivo || null })
    try { localStorage.setItem(CLAVE_NOMBRE, d.por) } catch { /* sin almacenamiento */ }
    showToast(r.procesados < marcados.value.length ? `${r.procesados} procesados (los demás ya los procesó otra persona)`
      : (d.accion === "ACEPTADO" ? "Aceptados: pasan al escritorio" : "Rechazados"), "success", 2500)
    dialogo.value = null
    marcados.value = []
    await cargar()
    recargarResumen()
  } catch (e) { showToast(e.message, "error", 4000) }
  finally { enviando.value = false }
}

// Pendientes: se refresca solo cada 10 s (mismo ritmo con el que el agente baja los pedidos)
onMounted(() => { cargar(); temporizador = setInterval(() => { if (vista.value === "pendientes" && !dialogo.value) cargar() }, 10000) })
onBeforeUnmount(() => clearInterval(temporizador))
</script>

<style scoped>
.cab { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.cab h2 { margin: 0; font-size: 20px; }
.sub { color: var(--texto-suave); font-size: 14px; margin: 0 0 10px; }
.cuenta { margin-left: 6px; min-width: 20px; height: 20px; padding: 0 6px; border-radius: 999px; background: var(--rojo); color: #fff;
          font-size: 12px; display: inline-flex; align-items: center; justify-content: center; }
.dia { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; }
.dia b { text-transform: capitalize; }
.acciones { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
.todos { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; margin-right: auto; cursor: pointer; }
.btn--peligro { background: var(--rojo); border-color: var(--rojo); color: #fff; }
.lote { padding: 12px 14px; margin-bottom: 10px; border-left: 5px solid var(--borde); }
.lote--pendiente { border-left-color: var(--ambar, #f59e0b); }
.lote--aceptado, .lote--aplicado { border-left-color: #16a34a; }
.lote--rechazado, .lote--error { border-left-color: var(--rojo); }
.lote__cab { display: flex; align-items: center; gap: 12px; }
.marca { width: 22px; height: 22px; flex-shrink: 0; cursor: pointer; }
.lote__tit { flex: 1; min-width: 0; cursor: pointer; display: flex; flex-direction: column; gap: 2px; }
.lote__tit small { color: var(--texto-suave); }
.lote__der { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
.estado { font-size: 12px; font-weight: 700; padding: 2px 8px; border-radius: 999px; background: var(--fondo); }
.aviso { margin: 8px 0 0; padding: 8px 10px; border-radius: 10px; background: var(--ambar-claro); color: #92400e; font-size: 14px; }
.info { margin: 8px 0 0; color: var(--texto-suave); font-size: 13px; }
.det { margin-top: 10px; padding-top: 10px; border-top: 1px dashed var(--borde); }
.det__fila { display: flex; align-items: flex-start; gap: 10px; padding: 4px 0; }
.det__cant { min-width: 36px; font-weight: 700; }
.det__nom { flex: 1; display: flex; flex-direction: column; }
.det__nom small { color: var(--texto-suave); }
.nro { display: block; margin-top: 6px; color: var(--texto-suave); word-break: break-all; }

@media (max-width: 768px) {
  .lote { padding: 10px 12px; }
}
@media (max-width: 576px) {
  .acciones .btn { flex: 1; }
  .todos { width: 100%; }
  .lote__cab { gap: 8px; }
  .lote__der b { font-size: 14px; }
}
</style>
