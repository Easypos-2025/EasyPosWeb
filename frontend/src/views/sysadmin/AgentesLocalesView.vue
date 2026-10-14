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

    <!-- Versión vigente del agente (las sedes se actualizan solas: botón del panel o al abrir turno) -->
    <div class="al-version">
      <div>
        <span>Versión vigente</span>
        <b>{{ vigente?.version || "Sin publicar" }}</b>
        <small v-if="vigente">{{ fechaHora(vigente.publicado_en) }}{{ vigente.notas ? " · " + vigente.notas : "" }}</small>
      </div>
      <div class="al-version-cont">
        <span class="al-estado al-estado--ok">{{ alDia }} al día</span>
        <span v-if="atrasadas" class="al-estado al-estado--warn">{{ atrasadas }} por actualizar</span>
      </div>
      <button v-if="versiones.length > 1" class="al-btn al-btn--ghost" @click="verVersiones = !verVersiones">
        <i class="bi bi-clock-history"></i> Versiones
      </button>
    </div>
    <div v-if="verVersiones" class="al-versiones">
      <div v-for="v in versiones" :key="v.id" class="al-ver" :class="{ 'al-ver--vigente': v.vigente }">
        <div><b>{{ v.version }}</b><small>{{ fechaHora(v.publicado_en) }} · {{ v.sedes }} sedes · {{ Math.round(v.tamano / 1048576) }} MB</small>
          <small v-if="v.notas">{{ v.notas }}</small></div>
        <span v-if="v.vigente" class="al-estado al-estado--ok">Vigente</span>
        <button v-else class="al-btn al-btn--ghost" @click="hacerVigente(v)">Volver a esta</button>
      </div>
    </div>

    <!-- Filtros: por nombre o código y por estado -->
    <div v-if="agentes.length" class="al-filtros">
      <div class="al-buscar">
        <i class="bi bi-search"></i>
        <input v-model="busqueda" class="form-control" placeholder="Buscar por empresa o código" />
        <button v-if="busqueda" class="al-buscar-x" title="Limpiar" @click="busqueda = ''"><i class="bi bi-x-lg"></i></button>
      </div>
      <div class="al-chips">
        <button v-for="f in FILTROS" :key="f.id" class="al-chip" :class="{ 'al-chip--activo': filtro === f.id }"
                @click="filtro = f.id">{{ f.texto }} <b>{{ conteo[f.id] }}</b></button>
      </div>
    </div>

    <div v-if="cargando && !agentes.length" class="al-vacio">Cargando…</div>
    <div v-else-if="!agentes.length" class="al-vacio">No hay agentes asignados.</div>
    <div v-else-if="!filtrados.length" class="al-vacio">Ningún agente coincide con la búsqueda.</div>

    <!-- Tarjetas compactas: al tocar una se abre el detalle con sus acciones -->
    <div class="al-lista">
      <button v-for="a in filtrados" :key="a.id" type="button" class="al-card" @click="selId = a.id">
        <!-- Estado en su propia fila: el nombre de la empresa queda completo (hasta dos líneas) -->
        <div class="al-card-estado">
          <span class="al-estado" :class="estado(a).clase">{{ estado(a).texto }}</span>
          <small class="al-card-cod">Código {{ a.codigo }}</small>
        </div>
        <b class="al-card-emp" :title="a.empresa">{{ a.empresa }}</b>
        <div class="al-card-pie">
          <span><i class="bi bi-box-seam"></i> {{ a.version || "—" }}
            <i v-if="a.version && vigente" :class="a.al_dia ? 'bi bi-check-circle-fill al-ok' : 'bi bi-arrow-up-circle-fill al-warn'"
               :title="a.al_dia ? 'Al día' : 'Por actualizar'"></i></span>
          <span><i class="bi bi-clock"></i> {{ fechaHora(a.ultimo_contacto) }}</span>
        </div>
        <span v-if="a.forzar_actualizacion && !a.al_dia" class="al-card-forzada"><i class="bi bi-hourglass-split"></i> Actualización forzada</span>
      </button>
    </div>

    <!-- Detalle del agente con sus acciones -->
    <div v-if="sel" class="al-velo" @click.self="selId = null">
      <div class="al-modal al-detalle">
        <div class="al-card-top">
          <div class="al-emp">
            <b>{{ sel.empresa }}</b>
            <small>Código {{ sel.codigo }} · clave {{ sel.clave_prefijo }}…</small>
          </div>
          <span class="al-estado" :class="estado(sel).clase">{{ estado(sel).texto }}</span>
          <button class="al-cerrar" title="Cerrar" @click="selId = null"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="al-datos">
          <div><span>URL local</span><b>{{ sel.url_local || "—" }}</b></div>
          <div><span>IP pública</span><b>{{ sel.ip_publica || "—" }}</b></div>
          <div><span>Versión</span><b>{{ sel.version || "—" }}
            <i v-if="sel.version && vigente" :class="sel.al_dia ? 'bi bi-check-circle-fill al-ok' : 'bi bi-arrow-up-circle-fill al-warn'"
               :title="sel.al_dia ? 'Al día' : 'Por actualizar'"></i></b></div>
          <div><span>Último contacto</span><b>{{ fechaHora(sel.ultimo_contacto) }}</b></div>
          <div v-if="sel.actualizacion" class="al-full"><span>Última actualización ({{ fechaHora(sel.actualizacion_en) }})</span>
            <b :class="sel.actualizacion.startsWith('OK') ? 'al-ok' : 'al-warn'">{{ sel.actualizacion }}</b></div>
        </div>
        <div class="al-acc">
          <button class="al-btn al-btn--ghost" @click="regenerar(sel)"><i class="bi bi-key"></i> Nueva clave</button>
          <!-- Sede atrasada: se actualiza apenas tenga la versión descargada (máx. 1 min tras su próximo latido) -->
          <span v-if="sel.forzar_actualizacion && !sel.al_dia" class="al-forzada"><i class="bi bi-hourglass-split"></i> Actualización forzada pendiente</span>
          <button v-else-if="sel.activo && sel.version && vigente && !sel.al_dia" class="al-btn al-btn--ghost" @click="forzar(sel)">
            <i class="bi bi-arrow-up-circle"></i> Forzar actualización
          </button>
          <button class="al-btn" :class="sel.activo ? 'al-btn--peligro' : 'al-btn--ok'" @click="alternar(sel)">
            <i :class="sel.activo ? 'bi bi-pause-circle' : 'bi bi-play-circle'"></i> {{ sel.activo ? "Desactivar" : "Activar" }}
          </button>
          <button class="al-btn al-btn--peligro" @click="pedirEliminar(sel)">
            <i class="bi bi-trash"></i> Eliminar
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
            <option v-for="e in $ordenAlfa(empresasLibres, 'name')" :key="e.id" :value="e.id">{{ e.name }}</option>
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

    <!-- Eliminar: libera la empresa y el código; se confirma escribiendo el código -->
    <div v-if="porEliminar" class="al-velo" @click.self="porEliminar = null">
      <form class="al-modal" @submit.prevent="eliminar">
        <h3><i class="bi bi-trash"></i> Eliminar agente</h3>
        <p class="al-aviso">Se elimina el agente de <b>{{ porEliminar.empresa }}</b>: la empresa y el código quedan libres
          para asignarlos de nuevo y el agente instalado con esta clave deja de comunicarse con la nube de inmediato.
          En el PC donde estaba instalado, desinstálelo con el instalador.</p>
        <label class="al-campo">
          <span>Para confirmar escriba el código <b>{{ porEliminar.codigo }}</b></span>
          <input v-model.trim="porEliminar.confirmacion" class="form-control" maxlength="20" autocomplete="off" />
        </label>
        <div class="al-modal-acc">
          <button type="button" class="al-btn al-btn--ghost" @click="porEliminar = null">Cancelar</button>
          <button class="al-btn al-btn--peligro" :disabled="guardando || porEliminar.confirmacion !== porEliminar.codigo">
            Eliminar
          </button>
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
const porEliminar = ref(null)
const versiones = ref([])
const verVersiones = ref(false)
const vigente = computed(() => versiones.value.find(v => v.vigente) || null)
const activos = computed(() => agentes.value.filter(a => a.activo && a.version))
const alDia = computed(() => activos.value.filter(a => a.al_dia).length)
const atrasadas = computed(() => activos.value.length - alDia.value)

// Filtros de la lista (nombre o código, sin tildes ni mayúsculas) y por estado
const FILTROS = [
  { id: "todos", texto: "Todos" }, { id: "linea", texto: "En línea" }, { id: "sin", texto: "Sin contacto" },
  { id: "atrasado", texto: "Por actualizar" }, { id: "inactivo", texto: "Inactivos" },
]
const CUMPLE = {
  todos: () => true,
  linea: a => a.activo && a.en_linea,
  sin: a => a.activo && !a.en_linea,
  atrasado: a => a.activo && a.version && !a.al_dia,
  inactivo: a => !a.activo,
}
const busqueda = ref("")
const filtro = ref("todos")
const selId = ref(null)
const sel = computed(() => agentes.value.find(a => a.id === selId.value) || null)
const normal = (t) => String(t || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase()
const conteo = computed(() => Object.fromEntries(FILTROS.map(f => [f.id, agentes.value.filter(CUMPLE[f.id]).length])))
const filtrados = computed(() => {
  const q = normal(busqueda.value.trim())
  return agentes.value.filter(a => CUMPLE[filtro.value](a)
    && (!q || normal(a.empresa).includes(q) || normal(a.codigo).includes(q)))
})

function pedirEliminar(a) {
  porEliminar.value = { ...a, confirmacion: "" }
  selId.value = null
}

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
    const [ag, ve] = await Promise.all([api.get("/api/agentes-locales"), api.get("/api/agentes-locales/versiones")])
    agentes.value = ag.data
    versiones.value = ve.data
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

async function eliminar() {
  const a = porEliminar.value
  guardando.value = true
  try {
    await api.delete(`/api/agentes-locales/${a.id}`, { data: { codigo: a.confirmacion } })
    showToast(`Agente de ${a.empresa} eliminado`, "success")
    porEliminar.value = null
    await cargar()
  } catch (e) {
    showToast(e.response?.data?.detail || "No se pudo eliminar el agente.", "error")
  } finally {
    guardando.value = false
  }
}

async function forzar(a) {
  if (!(await showConfirm(`El agente de ${a.empresa} se actualizará a la versión ${vigente.value.version} apenas la descargue; `
    + "sus dispositivos quedan sin conexión menos de un minuto. ¿Forzar la actualización?", "Sí, forzar"))) return
  try {
    await api.post(`/api/agentes-locales/${a.id}/forzar`)
    showToast("Se actualizará en su próximo contacto con la nube", "success")
    await cargar()
  } catch (e) {
    showToast(e.response?.data?.detail || "No se pudo forzar la actualización.", "error")
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

async function hacerVigente(v) {
  if (!(await showConfirm(`¿Volver a la versión ${v.version}? Las sedes la instalarán como actualización.`, "Sí, volver"))) return
  try {
    await api.post(`/api/agentes-locales/versiones/${v.id}/vigente`)
    showToast("Versión vigente cambiada", "success", 1500)
    await cargar()
  } catch (e) {
    showToast(e.response?.data?.detail || "No fue posible cambiar la versión", "error", 3500)
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
.al-version { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; background: #fff; border-radius: 14px; padding: 12px 16px; margin-bottom: 12px;
              box-shadow: 0 1px 3px rgba(15,23,42,.08); }
.al-version > div:first-child { flex: 1; min-width: 200px; }
.al-version span { display: block; font-size: 12px; color: #64748b; }
.al-version b { font-size: 16px; }
.al-version small { display: block; color: #64748b; }
.al-version-cont { display: flex; gap: 6px; }
.al-versiones { background: #fff; border-radius: 14px; padding: 6px 16px; margin-bottom: 12px; }
.al-ver { display: flex; align-items: center; gap: 10px; padding: 10px 0; border-bottom: 1px solid #e2e8f0; }
.al-ver:last-child { border-bottom: 0; }
.al-ver > div { flex: 1; }
.al-ver small { display: block; color: #64748b; }
.al-ver--vigente b { color: #166534; }
.al-ok { color: #16a34a; }
.al-warn { color: #d97706; }
.al-full { grid-column: 1 / -1; }
.al-vacio { text-align: center; color: #64748b; padding: 30px; }
.al-filtros { display: flex; flex-direction: column; gap: 10px; margin-bottom: 12px; }
.al-buscar { position: relative; max-width: 420px; }
.al-buscar > i { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: #94a3b8; }
.al-buscar .form-control { padding-left: 36px; padding-right: 36px; min-height: 40px; border-radius: 10px; }
.al-buscar-x { position: absolute; right: 6px; top: 50%; transform: translateY(-50%); border: 0; background: none; color: #64748b; padding: 6px; }
.al-chips { display: flex; gap: 6px; flex-wrap: wrap; }
.al-chip { border: 1px solid #e2e8f0; background: #fff; color: #334155; border-radius: 999px; padding: 5px 12px; font-size: 13px; font-weight: 600; }
.al-chip b { margin-left: 4px; color: #64748b; }
.al-chip--activo { background: #1e3a5f; border-color: #1e3a5f; color: #fff; }
.al-chip--activo b { color: #cbd5e1; }
.al-lista { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.al-card { text-align: left; border: 1px solid transparent; background: #fff; border-radius: 14px; box-shadow: 0 1px 3px rgba(15,23,42,.08), 0 4px 12px rgba(15,23,42,.06);
           padding: 12px 14px; display: flex; flex-direction: column; gap: 4px; min-width: 0; color: inherit; transition: border-color .15s, transform .15s; }
.al-card:hover { border-color: #93c5fd; transform: translateY(-1px); }
.al-card-emp { font-size: 15px; min-width: 0; line-height: 1.25; overflow: hidden; word-break: break-word;
               display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; }
.al-card-estado { display: flex; justify-content: space-between; align-items: center; gap: 8px; min-width: 0; }
.al-card-estado .al-card-cod { white-space: nowrap; }
.al-card-cod { color: #64748b; font-size: 13px; }
.al-card-pie { display: flex; justify-content: space-between; gap: 8px; flex-wrap: wrap; font-size: 12px; color: #475569; margin-top: 4px; }
.al-card-forzada { align-self: flex-start; font-size: 11px; font-weight: 600; color: #b45309; background: #fef3c7; border-radius: 6px; padding: 2px 8px; margin-top: 2px; }
.al-detalle { max-width: 620px; display: flex; flex-direction: column; gap: 14px; max-height: 90vh; overflow-y: auto; }
.al-detalle .al-emp { flex: 1; min-width: 0; }
.al-cerrar { border: 0; background: #f1f5f9; color: #475569; border-radius: 8px; width: 34px; height: 34px; flex-shrink: 0; }
.al-card-top { display: flex; justify-content: space-between; gap: 10px; align-items: flex-start; min-width: 0; }
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
.al-forzada { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600; color: #b45309;
              background: #fef3c7; border-radius: 8px; padding: 6px 10px; }
.al-modal { width: 100%; max-width: 480px; background: #fff; border-radius: 16px; padding: 20px; }
.al-modal h3 { margin: 0 0 14px; font-size: 18px; display: flex; gap: 8px; align-items: center; }
.al-campo { display: block; margin-bottom: 12px; }
.al-campo span { display: block; font-size: 13px; font-weight: 600; color: #64748b; margin-bottom: 4px; }
.al-modal-acc { display: flex; justify-content: flex-end; gap: 8px; margin-top: 14px; }
.al-aviso { font-size: 14px; color: #92400e; background: #fef3c7; border-radius: 10px; padding: 10px 12px; }
.al-clave { font-family: Consolas, monospace; font-size: 14px; background: #f1f5f9; border-radius: 10px; padding: 12px; word-break: break-all; user-select: all; }

@media (max-width: 1024px) {
  .al-lista { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  .al-lista { gap: 10px; }
  .al-buscar { max-width: none; }
}
@media (max-width: 576px) {
  .al-wrap { padding: 10px; }
  .al-lista { grid-template-columns: 1fr; }
  .al-datos { grid-template-columns: 1fr; }
  .al-chips { flex-wrap: nowrap; overflow-x: auto; padding-bottom: 2px; }
  .al-chip { flex-shrink: 0; }
  .hide-xs { display: none; }
  .al-acc .al-btn { flex: 1; justify-content: center; }
}
</style>
