<template>
  <div>
    <div class="cab">
      <h2>Catálogo de la web</h2>
      <button class="btn btn--chico" :disabled="cargando || trabajando" @click="cargar"><Icono nombre="refrescar" :tam="16" /> Revisar</button>
    </div>
    <p class="sub">Baja al programa de escritorio los platos creados o modificados en EasyPosWeb, sus impresoras, los datos de
      la sede y las fotos. <b>La web manda</b>: lo que cambió allá reemplaza lo del escritorio. No es automático: se hace
      con este botón (o desde el escritorio).</p>

    <div v-if="cargando && !datos" class="cargando"><span class="giro"></span></div>
    <p v-else-if="error" class="aviso">{{ error }}</p>

    <template v-else-if="datos">
      <div class="tarjeta panel">
        <h3>Pendiente de bajar</h3>
        <p v-if="!pend.total" class="vacio-chico">Todo está al día: la web no tiene cambios pendientes.</p>
        <ul v-else class="lista">
          <li v-if="pend.nuevos.length"><b>{{ pend.nuevos.length }}</b> plato(s) nuevo(s):
            <span class="nombres">{{ nombres(pend.nuevos) }}</span>
            <small>Se crean en el escritorio con su Id_Plato y quedan activos (en la web estaban inactivos esperando esto).</small></li>
          <li v-if="pend.modificados.length"><b>{{ pend.modificados.length }}</b> plato(s) modificado(s):
            <span class="nombres">{{ nombres(pend.modificados) }}</span></li>
          <li v-if="pend.sede">Datos de la sede (nombre del almacén, razón social, NIT, dirección, correos, logo).</li>
          <li class="nota">Siempre se revisan también las fotos de los platos.</li>
        </ul>
        <button class="btn btn--primario" :disabled="trabajando" @click="dialogo = { por: nombreGuardado() }">
          <span v-if="trabajando" class="giro" style="width:20px;height:20px;border-width:2px"></span>
          <template v-else><Icono nombre="descargar" /> Sincronizar ahora</template>
        </button>
      </div>

      <div v-if="ultimo" class="tarjeta panel">
        <h3>Última sincronización · {{ fecha(ultimo.fecha) }}</h3>
        <p class="sub">Por {{ ultimo.quien }}</p>
        <ul class="lista">
          <li><b>{{ ultimo.nuevos }}</b> plato(s) nuevo(s) · <b>{{ ultimo.actualizados }}</b> actualizado(s)</li>
          <li v-if="ultimo.sede">Datos de la sede actualizados</li>
          <li v-if="ultimo.fotos && !ultimo.fotos.error">Fotos: {{ ultimo.fotos.descargadas || 0 }} descargadas, {{ ultimo.fotos.asignadas || 0 }} asignadas</li>
        </ul>
        <div v-if="ultimo.avisos?.length" class="aviso">
          <b>Avisos</b>
          <ul><li v-for="(a, i) in ultimo.avisos" :key="i">{{ a }}</li></ul>
        </div>
      </div>
      <p v-else-if="datos.ultimo_texto" class="sub">Última sincronización: {{ datos.ultimo_texto }}</p>
    </template>

    <div v-if="dialogo" class="velo" @click.self="dialogo = null">
      <form class="hoja" @submit.prevent="sincronizar">
        <div class="hoja__cab"><h2>Sincronizar catálogo</h2>
          <button type="button" class="cerrar" @click="dialogo = null"><Icono nombre="cerrar" /></button></div>
        <div class="hoja__cuerpo">
          <p class="sub">Los cambios de la web reemplazan lo que tenga el escritorio en esos platos y en los datos de la sede.</p>
          <label class="campo"><span>Su nombre</span>
            <input v-model.trim="dialogo.por" class="entrada" maxlength="60" required autocomplete="off" /></label>
        </div>
        <div class="hoja__pie"><button class="btn btn--primario btn--bloque" :disabled="dialogo.por.length < 2">Sincronizar</button></div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue"
import Icono from "../../componentes/Icono.vue"
import { api } from "../../api"
import { showToast } from "@/utils/toast"

const CLAVE_NOMBRE = "ag_pw_nombre"
const datos = ref(null)
const ultimoLocal = ref(null)
const cargando = ref(false)
const trabajando = ref(false)
const error = ref("")
const dialogo = ref(null)

const pend = computed(() => datos.value?.pendientes || { nuevos: [], modificados: [], sede: false, total: 0 })
const ultimo = computed(() => ultimoLocal.value || datos.value?.ultimo || null)
const fecha = (v) => (v ? new Date(v).toLocaleString("es-CO", { dateStyle: "short", timeStyle: "short" }) : "—")
const nombres = (l) => l.slice(0, 8).map(x => x.nombre || `#${x.id}`).join(", ") + (l.length > 8 ? ` y ${l.length - 8} más` : "")
function nombreGuardado() { try { return localStorage.getItem(CLAVE_NOMBRE) || "" } catch { return "" } }

async function cargar() {
  cargando.value = true
  error.value = ""
  try { datos.value = await api.admin.get("/maestros") } catch (e) { error.value = e.message }
  finally { cargando.value = false }
}

async function sincronizar() {
  const por = dialogo.value.por
  dialogo.value = null
  trabajando.value = true
  try {
    ultimoLocal.value = await api.admin.post("/maestros/sincronizar", { por })
    try { localStorage.setItem(CLAVE_NOMBRE, por) } catch { /* sin almacenamiento */ }
    showToast("Catálogo sincronizado", "success", 2000)
    await cargar()
  } catch (e) { showToast(e.message, "error", 4500) }
  finally { trabajando.value = false }
}

onMounted(cargar)
</script>

<style scoped>
.cab { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.cab h2 { margin: 0; font-size: 20px; }
.sub { color: var(--texto-suave); font-size: 14px; margin: 0 0 10px; }
.panel { padding: 18px; max-width: 760px; margin-bottom: 12px; }
.panel h3 { font-size: 16px; margin: 0 0 10px; }
.lista { margin: 0 0 14px; padding-left: 20px; display: flex; flex-direction: column; gap: 8px; }
.lista small { display: block; color: var(--texto-suave); }
.nombres { color: var(--texto-suave); }
.nota { color: var(--texto-suave); font-size: 13px; list-style: none; margin-left: -20px; }
.vacio-chico { color: var(--texto-suave); margin: 0 0 14px; }
.aviso { margin-top: 12px; padding: 10px 12px; border-radius: 10px; background: var(--ambar-claro); color: #92400e; font-size: 14px; }
.aviso ul { margin: 6px 0 0; padding-left: 18px; }

@media (max-width: 768px) {
  .panel { max-width: none; }
}
@media (max-width: 576px) {
  .panel { padding: 14px; }
  .panel .btn { width: 100%; }
}
</style>
