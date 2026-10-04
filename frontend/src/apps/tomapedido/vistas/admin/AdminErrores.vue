<template>
  <div>
    <div class="cab">
      <h2>Errores</h2>
      <button class="btn btn--chico" @click="cargar"><Icono nombre="refrescar" :tam="16" /> Actualizar</button>
    </div>
    <div class="chips">
      <button v-for="p in PESTANAS" :key="p.v" class="chip" :class="{ 'chip--activo': estado === p.v }" @click="estado = p.v; cargar()">
        {{ p.l }}
      </button>
    </div>

    <div v-if="cargando && !lista.length" class="cargando"><span class="giro"></span></div>
    <p v-else-if="!lista.length" class="vacio">{{ estado === "abiertos" ? "No hay errores sin resolver." : "No hay registros." }}</p>

    <div v-for="e in lista" :key="e.id" class="err tarjeta" :class="'err--' + e.nivel.toLowerCase()">
      <div class="err__cab" @click="abierto = abierto === e.id ? null : e.id">
        <span class="nivel">{{ NIVEL[e.nivel] }}</span>
        <div class="err__tit">
          <b>{{ e.titulo }}</b>
          <small>{{ e.origen === "dispositivo" ? "Dispositivo" : "Agente" }} · {{ e.tipo }}
            {{ e.dispositivo ? "· " + e.dispositivo : "" }} · {{ e.ocurrencias }} {{ e.ocurrencias === 1 ? "vez" : "veces" }}
            · última {{ fecha(e.ultima) }}</small>
        </div>
        <span v-if="e.regresiones && e.estado !== 'RESUELTO'" class="regresion">Se repitió</span>
      </div>
      <div v-if="abierto === e.id" class="err__det">
        <dl>
          <dt>Primera vez</dt><dd>{{ fecha(e.primera) }}</dd>
          <dt>Pantalla / ruta</dt><dd>{{ e.vista || "—" }}</dd>
          <dt>IP</dt><dd>{{ e.ip || "—" }}</dd>
          <template v-if="e.estado === 'RESUELTO'"><dt>Solución</dt><dd>{{ e.nota }} ({{ fecha(e.resuelto_en) }})</dd></template>
        </dl>
        <pre v-if="e.mensaje">{{ e.mensaje }}</pre>
        <pre v-if="e.detalle" class="detalle">{{ e.detalle }}</pre>
        <div class="err__acc">
          <button class="btn btn--chico" @click="copiar(e)"><Icono nombre="copiar" :tam="16" /> Copiar para soporte</button>
          <button v-if="e.estado !== 'RESUELTO'" class="btn btn--chico btn--primario" @click="resolver = { e, nota: '' }">
            <Icono nombre="check" :tam="16" /> Marcar resuelto</button>
          <button v-else class="btn btn--chico" @click="reabrir(e)">Reabrir</button>
        </div>
      </div>
    </div>

    <div v-if="resolver" class="velo" @click.self="resolver = null">
      <form class="hoja" @submit.prevent="guardarResuelto">
        <div class="hoja__cab"><h2>Marcar resuelto</h2>
          <button type="button" class="cerrar" @click="resolver = null"><Icono nombre="cerrar" /></button></div>
        <div class="hoja__cuerpo">
          <p class="nota-tit">{{ resolver.e.titulo }}</p>
          <label class="campo"><span>¿Cómo se solucionó?</span>
            <textarea v-model.trim="resolver.nota" class="entrada" rows="4" maxlength="2000" required></textarea></label>
        </div>
        <div class="hoja__pie"><button class="btn btn--primario btn--bloque" :disabled="resolver.nota.length < 3">Guardar</button></div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { inject, onMounted, ref } from "vue"
import Icono from "../../componentes/Icono.vue"
import { api } from "../../api"
import { showToast } from "@/utils/toast"

const PESTANAS = [{ v: "abiertos", l: "Sin resolver" }, { v: "resueltos", l: "Resueltos" }, { v: "todos", l: "Todos" }]
const NIVEL = { CRITICO: "Crítico", ERROR: "Error", ADVERTENCIA: "Aviso" }
const recargarResumen = inject("recargarResumen")
const estado = ref("abiertos")
const lista = ref([])
const cargando = ref(false)
const abierto = ref(null)
const resolver = ref(null)

const fecha = (v) => (v ? new Date(v).toLocaleString("es-CO", { dateStyle: "short", timeStyle: "short" }) : "—")

async function cargar() {
  cargando.value = true
  try { lista.value = await api.admin.get("/errores", { estado: estado.value }) }
  catch (e) { showToast(e.message, "error", 3000) }
  finally { cargando.value = false }
}

// Texto completo para pegarlo al soporte técnico
async function copiar(e) {
  const t = [`Error: ${e.titulo}`, `Nivel: ${e.nivel} · Tipo: ${e.tipo} · Origen: ${e.origen}`,
             `Dispositivo: ${e.dispositivo || "—"} · IP: ${e.ip || "—"}`, `Pantalla/ruta: ${e.vista || "—"}`,
             `Veces: ${e.ocurrencias} · Primera: ${fecha(e.primera)} · Última: ${fecha(e.ultima)}`,
             e.mensaje ? `Mensaje: ${e.mensaje}` : "", e.detalle ? `Detalle:\n${e.detalle}` : ""].filter(Boolean).join("\n")
  try { await navigator.clipboard.writeText(t); showToast("Copiado", "success", 1200) }
  catch { showToast("No se pudo copiar automáticamente", "warning", 2500) }
}

async function guardarResuelto() {
  try {
    await api.admin.post(`/errores/${resolver.value.e.id}/resolver`, { nota: resolver.value.nota })
    resolver.value = null
    showToast("Marcado como resuelto", "success", 1500)
    await cargar(); recargarResumen()
  } catch (e) { showToast(e.message, "error", 3000) }
}

async function reabrir(e) {
  try { await api.admin.post(`/errores/${e.id}/reabrir`); await cargar(); recargarResumen() }
  catch (err) { showToast(err.message, "error", 3000) }
}

onMounted(cargar)
</script>

<style scoped>
.cab { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.cab h2 { margin: 0; font-size: 20px; }
.err { margin-bottom: 10px; border-left: 5px solid var(--ambar); overflow: hidden; }
.err--critico { border-left-color: #7f1d1d; }
.err--error { border-left-color: var(--rojo); }
.err__cab { display: flex; align-items: flex-start; gap: 10px; padding: 12px 14px; cursor: pointer; }
.nivel { flex-shrink: 0; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 999px; background: var(--fondo); }
.err__tit { flex: 1; min-width: 0; }
.err__tit b { display: block; word-break: break-word; }
.err__tit small { color: var(--texto-suave); }
.regresion { flex-shrink: 0; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 999px; background: var(--rojo-claro); color: var(--rojo); }
.err__det { padding: 0 14px 14px; }
dl { display: grid; grid-template-columns: auto 1fr; gap: 4px 12px; font-size: 14px; margin: 0 0 10px; }
dt { color: var(--texto-suave); }
dd { margin: 0; word-break: break-word; }
pre { white-space: pre-wrap; word-break: break-word; background: var(--fondo); border-radius: 10px; padding: 10px; font-size: 13px; margin: 0 0 10px; }
.detalle { max-height: 240px; overflow: auto; font-size: 12px; }
.err__acc { display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
.nota-tit { font-weight: 600; margin: 0 0 10px; }
textarea.entrada { resize: vertical; }

@media (max-width: 576px) {
  .err__acc .btn { flex: 1; }
  .err__cab { padding: 10px 12px; }
}
@media (max-width: 768px) {
  dl { grid-template-columns: 1fr; }
}
</style>
