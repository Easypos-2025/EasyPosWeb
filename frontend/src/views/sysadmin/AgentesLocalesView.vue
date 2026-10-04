<template>
  <div class="al-wrap">
    <div class="al-head">
      <div class="al-title"><i class="bi bi-hdd-network"></i> {{ title }}</div>
      <div class="al-head-acc">
        <button class="al-btn al-btn--ghost" :disabled="cargando" @click="cargar">
          <i class="bi bi-arrow-clockwise"></i><span class="hide-xs"> Actualizar</span>
        </button>
        <button class="al-btn" @click="abrirNuevo"><i class="bi bi-plus-lg"></i> Asignar agente</button>
      </div>
    </div>
    <p class="al-nota">
      Servicio que corre en el PC de caja de cada empresa para la toma de pedidos contra la base de datos del
      escritorio. Cada empresa tiene su propia clave; el código es el mismo del directorio del escritorio.
    </p>

    <div v-if="cargando && !agentes.length" class="al-vacio">Cargando…</div>
    <div v-else-if="!agentes.length" class="al-vacio">No hay agentes asignados.</div>

    <div class="al-lista">
      <div v-for="a in agentes" :key="a.id" class="al-card">
        <div class="al-card-top">
          <div class="al-emp">
            <b>{{ a.empresa }}</b>
            <small>Código {{ a.codigo }} · clave {{ a.clave_prefijo }}…</small>
          </div>
          <span class="al-estado" :class="estado(a).clase">{{ estado(a).texto }}</span>
        </div>
        <div class="al-datos">
          <div><span>URL local</span><b>{{ a.url_local || "—" }}</b></div>
          <div><span>IP pública</span><b>{{ a.ip_publica || "—" }}</b></div>
          <div><span>Versión</span><b>{{ a.version || "—" }}</b></div>
          <div><span>Último contacto</span><b>{{ fechaHora(a.ultimo_contacto) }}</b></div>
        </div>
        <div class="al-acc">
          <button class="al-btn al-btn--ghost" @click="regenerar(a)"><i class="bi bi-key"></i> Nueva clave</button>
          <button class="al-btn" :class="a.activo ? 'al-btn--peligro' : 'al-btn--ok'" @click="alternar(a)">
            <i :class="a.activo ? 'bi bi-pause-circle' : 'bi bi-play-circle'"></i> {{ a.activo ? "Desactivar" : "Activar" }}
          </button>
        </div>
      </div>
    </div>

    <!-- Asignar agente -->
    <div v-if="nuevo" class="al-velo" @click.self="nuevo = null">
      <form class="al-modal" @submit.prevent="crear">
        <h3>Asignar agente</h3>
        <label class="al-campo">
          <span>Empresa</span>
          <select v-model="nuevo.company_id" class="form-control" required>
            <option :value="null" disabled>Seleccione…</option>
            <option v-for="e in empresasLibres" :key="e.id" :value="e.id">{{ e.name }}</option>
          </select>
        </label>
        <label class="al-campo">
          <span>Código (el del directorio del escritorio, ej. 2022006)</span>
          <input v-model.trim="nuevo.codigo" class="form-control" maxlength="20" required pattern="[A-Za-z0-9_\-]{2,20}" />
        </label>
        <div class="al-modal-acc">
          <button type="button" class="al-btn al-btn--ghost" @click="nuevo = null">Cancelar</button>
          <button class="al-btn" :disabled="guardando || !nuevo.company_id || !nuevo.codigo">Asignar</button>
        </div>
      </form>
    </div>

    <!-- Clave: se muestra una sola vez -->
    <div v-if="claveMostrada" class="al-velo">
      <div class="al-modal">
        <h3><i class="bi bi-key"></i> Clave del agente</h3>
        <p class="al-aviso">Cópiela ahora y colóquela en el instalador del agente de <b>{{ claveMostrada.empresa }}</b>.
          No se vuelve a mostrar; si se pierde, genere una nueva.</p>
        <div class="al-clave">{{ claveMostrada.clave }}</div>
        <div class="al-modal-acc">
          <button class="al-btn al-btn--ghost" @click="copiar"><i class="bi bi-clipboard"></i> Copiar</button>
          <button class="al-btn" @click="claveMostrada = null">Ya la guardé</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue"
import api from "@/services/apis"
import { showConfirm, showToast } from "@/utils/toast"
import { useModuleName } from "@/composables/useModuleName"

const { moduleName } = useModuleName()
const title = computed(() => moduleName.value || "Agentes Locales")

const agentes = ref([])
const empresas = ref([])
const cargando = ref(false)
const guardando = ref(false)
const nuevo = ref(null)
const claveMostrada = ref(null)

const empresasLibres = computed(() => {
  const usadas = new Set(agentes.value.map(a => a.company_id))
  return empresas.value.filter(e => !usadas.has(e.id))
})

function estado(a) {
  if (!a.activo) return { texto: "Inactivo", clase: "al-estado--off" }
  if (a.en_linea) return { texto: "En línea", clase: "al-estado--ok" }
  return { texto: a.ultimo_contacto ? "Sin contacto" : "Sin instalar", clase: "al-estado--warn" }
}

function fechaHora(v) {
  if (!v) return "—"
  try { return new Date(v).toLocaleString("es-CO", { dateStyle: "short", timeStyle: "short" }) } catch { return v }
}

async function cargar() {
  cargando.value = true
  try {
    agentes.value = (await api.get("/api/agentes-locales")).data
  } catch (e) {
    showToast(e.response?.data?.detail || "No fue posible cargar los agentes", "error", 3000)
  } finally {
    cargando.value = false
  }
}

async function abrirNuevo() {
  if (!empresas.value.length) {
    try { empresas.value = (await api.get("/companies/")).data } catch { /* lista vacía */ }
  }
  nuevo.value = { company_id: null, codigo: "" }
}

async function crear() {
  guardando.value = true
  try {
    const { data } = await api.post("/api/agentes-locales", nuevo.value)
    const emp = empresas.value.find(e => e.id === nuevo.value.company_id)
    claveMostrada.value = { clave: data.clave, empresa: emp?.name || "" }
    nuevo.value = null
    await cargar()
  } catch (e) {
    showToast(e.response?.data?.detail || "No fue posible asignar el agente", "error", 3500)
  } finally {
    guardando.value = false
  }
}

async function regenerar(a) {
  if (!(await showConfirm(`La clave actual de ${a.empresa} dejará de funcionar. ¿Generar una nueva?`, "Sí, generar"))) return
  try {
    const { data } = await api.post(`/api/agentes-locales/${a.id}/clave`)
    claveMostrada.value = { clave: data.clave, empresa: a.empresa }
    await cargar()
  } catch (e) {
    showToast(e.response?.data?.detail || "No fue posible generar la clave", "error", 3500)
  }
}

async function alternar(a) {
  if (a.activo && !(await showConfirm(`¿Desactivar el agente de ${a.empresa}? Dejará de reportar a la nube.`, "Sí, desactivar"))) return
  try {
    await api.patch(`/api/agentes-locales/${a.id}`, { activo: !a.activo })
    await cargar()
  } catch (e) {
    showToast(e.response?.data?.detail || "No fue posible actualizar", "error", 3500)
  }
}

async function copiar() {
  try {
    await navigator.clipboard.writeText(claveMostrada.value.clave)
    showToast("Clave copiada", "success", 1200)
  } catch {
    showToast("No se pudo copiar; selecciónela y cópiela", "warning", 2500)
  }
}

onMounted(cargar)
</script>

<style scoped>
.al-wrap { padding: 16px; max-width: 1200px; margin: 0 auto; }
.al-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
.al-title { font-size: 20px; font-weight: 700; display: flex; align-items: center; gap: 8px; }
.al-head-acc { display: flex; gap: 8px; }
.al-nota { color: #64748b; font-size: 14px; margin: 8px 0 16px; }
.al-vacio { text-align: center; color: #64748b; padding: 30px; }
.al-lista { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.al-card { background: #fff; border-radius: 14px; box-shadow: 0 1px 3px rgba(15,23,42,.08), 0 4px 12px rgba(15,23,42,.06); padding: 14px; display: flex; flex-direction: column; gap: 12px; }
.al-card-top { display: flex; justify-content: space-between; gap: 10px; align-items: flex-start; }
.al-emp b { display: block; font-size: 16px; }
.al-emp small { color: #64748b; }
.al-estado { flex-shrink: 0; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; }
.al-estado--ok { background: #dcfce7; color: #166534; }
.al-estado--warn { background: #fef3c7; color: #92400e; }
.al-estado--off { background: #e2e8f0; color: #475569; }
.al-datos { display: grid; grid-template-columns: 1fr 1fr; gap: 6px 14px; font-size: 13px; }
.al-datos span { display: block; color: #64748b; }
.al-datos b { word-break: break-all; }
.al-acc { display: flex; gap: 8px; justify-content: flex-end; flex-wrap: wrap; }
.al-btn { display: inline-flex; align-items: center; gap: 6px; min-height: 38px; padding: 0 14px; border: 0; border-radius: 10px; background: #2563eb; color: #fff; font-weight: 600; font-size: 14px; }
.al-btn:disabled { opacity: .55; }
.al-btn--ghost { background: #f1f5f9; color: #1e293b; }
.al-btn--peligro { background: #fee2e2; color: #b91c1c; }
.al-btn--ok { background: #dcfce7; color: #166534; }
.al-velo { position: fixed; inset: 0; z-index: 1050; background: rgba(15,23,42,.45); display: flex; align-items: center; justify-content: center; padding: 16px; }
.al-modal { width: 100%; max-width: 480px; background: #fff; border-radius: 16px; padding: 20px; }
.al-modal h3 { margin: 0 0 14px; font-size: 18px; display: flex; gap: 8px; align-items: center; }
.al-campo { display: block; margin-bottom: 12px; }
.al-campo span { display: block; font-size: 13px; font-weight: 600; color: #64748b; margin-bottom: 4px; }
.al-modal-acc { display: flex; justify-content: flex-end; gap: 8px; margin-top: 14px; }
.al-aviso { font-size: 14px; color: #92400e; background: #fef3c7; border-radius: 10px; padding: 10px 12px; }
.al-clave { font-family: Consolas, monospace; font-size: 14px; background: #f1f5f9; border-radius: 10px; padding: 12px; word-break: break-all; user-select: all; }

@media (max-width: 768px) {
  .al-lista { grid-template-columns: 1fr; }
}
@media (max-width: 576px) {
  .al-wrap { padding: 10px; }
  .al-datos { grid-template-columns: 1fr; }
  .hide-xs { display: none; }
  .al-acc .al-btn { flex: 1; justify-content: center; }
}
</style>
