<template>
  <div>
    <div class="cab">
      <h2>Dispositivos</h2>
      <button class="btn btn--chico" @click="cargar"><Icono nombre="refrescar" :tam="16" /> Actualizar</button>
    </div>
    <div v-if="limite" class="cupo" :class="{ 'cupo--lleno': registrados >= limite }">
      <b>{{ registrados }} de {{ limite }}</b> dispositivos autorizados
      <span v-if="registrados >= limite"> · Cupo lleno: elimine un dispositivo que ya no se use para activar otro.</span>
    </div>
    <p class="nota">Conectado = el dispositivo se comunicó con la caja en el último minuto y medio.
      La activación de dispositivos nuevos se sigue haciendo en el programa de escritorio.</p>

    <div v-if="cargando && !lista.length" class="cargando"><span class="giro"></span></div>
    <p v-else-if="!lista.length" class="vacio">No hay dispositivos registrados.</p>

    <div class="disps">
      <div v-for="d in lista" :key="d.id" class="disp tarjeta">
        <div class="disp__cab">
          <span class="disp__ico" :class="estado(d).clase"><Icono nombre="celular" /></span>
          <div class="disp__tit">
            <b>{{ d.nombre_dispositivo }}</b>
            <small>{{ d.usuario }} · código {{ d.cod_empleado }}</small>
          </div>
        </div>
        <span class="estado" :class="estado(d).clase">{{ estado(d).texto }}</span>
        <dl>
          <dt>Último contacto</dt><dd>{{ fecha(d.ultimo_acceso) }}</dd>
          <dt>IP</dt><dd>{{ d.ultima_ip || "—" }}</dd>
          <dt>Pedidos abiertos</dt><dd>{{ d.pedidos }}</dd>
          <dt>En el escritorio</dt><dd>{{ d.activo_escritorio ? "Activo" : "Inactivo / sin activar" }}</dd>
        </dl>
        <div class="disp__acc">
          <button class="btn btn--chico" @click="eliminar(d)"><Icono nombre="basura" :tam="16" /> Eliminar</button>
          <button v-if="!d.revocado" class="btn btn--chico btn--peligro" @click="bloquear(d)">Bloquear</button>
          <button v-else class="btn btn--chico btn--primario" @click="habilitar(d)">Habilitar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { inject, onBeforeUnmount, onMounted, ref } from "vue"
import Icono from "../../componentes/Icono.vue"
import { api } from "../../api"
import { showConfirm, showToast } from "@/utils/toast"

const recargarResumen = inject("recargarResumen")
const lista = ref([])
const limite = ref(null)
const registrados = ref(0)
const cargando = ref(false)
let temporizador = null

const hora = (v) => new Date(v).toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" })
const fecha = (v) => (v ? new Date(v).toLocaleString("es-CO", { dateStyle: "short", timeStyle: "short" }) : "—")

function estado(d) {
  if (d.revocado) return { texto: "Bloqueado", clase: "e--gris" }
  if (!d.activo_escritorio) return { texto: "Sin activar", clase: "e--gris" }
  if (d.conectado) return { texto: "Conectado", clase: "e--verde" }
  return { texto: d.ultimo_acceso ? `Sin conexión desde las ${hora(d.ultimo_acceso)}` : "Nunca ha ingresado", clase: "e--rojo" }
}

async function cargar() {
  cargando.value = true
  try {
    const r = await api.admin.get("/dispositivos")
    lista.value = r.dispositivos
    limite.value = r.limite
    registrados.value = r.registrados
  }
  catch (e) { showToast(e.message, "error", 3000) }
  finally { cargando.value = false }
}

async function bloquear(d) {
  if (!(await showConfirm(`¿Bloquear "${d.nombre_dispositivo}"? Se cerrará su sesión y no podrá tomar pedidos.`, "Sí, bloquear"))) return
  try { await api.admin.post(`/dispositivos/${d.id}/bloquear`); await cargar(); recargarResumen() }
  catch (e) { showToast(e.message, "error", 3000) }
}

// Cambios de personal: libera el cupo para activar otro dispositivo (el mesero y sus pedidos se conservan)
async function eliminar(d) {
  const aviso = d.pedidos
    ? `"${d.nombre_dispositivo}" tiene ${d.pedidos} pedidos abiertos; seguirán en caja, pero este dispositivo no podrá continuarlos. `
    : ""
  if (!(await showConfirm(`${aviso}¿Eliminar "${d.nombre_dispositivo}"? Libera su cupo; para volver a usarlo tendrá que registrarse y activarse de nuevo.`, "Sí, eliminar"))) return
  try {
    await api.admin.post(`/dispositivos/${d.id}/eliminar`)
    showToast("Dispositivo eliminado", "success", 1500)
    await cargar(); recargarResumen()
  } catch (e) { showToast(e.message, "error", 5000) }
}

async function habilitar(d) {
  try { await api.admin.post(`/dispositivos/${d.id}/habilitar`); await cargar(); recargarResumen() }
  catch (e) { showToast(e.message, "error", 3000) }
}

onMounted(() => { cargar(); temporizador = setInterval(cargar, 30000) })
onBeforeUnmount(() => clearInterval(temporizador))
</script>

<style scoped>
.cab { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.cab h2 { margin: 0; font-size: 20px; }
.nota { color: var(--texto-suave); font-size: 14px; margin: 0 0 12px; }
.disps { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
.cupo { margin: 0 0 8px; padding: 10px 12px; border-radius: 10px; background: var(--azul-claro); color: var(--navy); font-size: 14px; }
.cupo--lleno { background: var(--rojo-claro); color: var(--rojo); }
.disp { padding: 14px; display: flex; flex-direction: column; gap: 10px; }
.disp__cab { display: flex; align-items: center; gap: 10px; }
.disp__ico { width: 40px; height: 40px; flex-shrink: 0; border-radius: 12px; display: inline-flex; align-items: center; justify-content: center; }
.disp__tit { flex: 1; min-width: 0; }
.disp__tit b { display: block; overflow-wrap: anywhere; line-height: 1.25; }
.disp__tit small { color: var(--texto-suave); }
.estado { align-self: flex-start; font-size: 12px; font-weight: 700; padding: 3px 10px; border-radius: 999px; }
.e--verde { background: var(--verde-claro); color: var(--verde); }
.e--rojo { background: var(--rojo-claro); color: var(--rojo); }
.e--gris { background: #e2e8f0; color: #475569; }
dl { display: grid; grid-template-columns: auto 1fr; gap: 4px 12px; font-size: 14px; margin: 0; }
dt { color: var(--texto-suave); }
dd { margin: 0; font-weight: 600; }
.disp__acc { display: flex; justify-content: flex-end; gap: 8px; flex-wrap: wrap; }

@media (max-width: 768px) {
  .disps { grid-template-columns: 1fr; }
}
@media (max-width: 576px) {
  .disp__acc .btn { flex: 1; }
}
</style>
