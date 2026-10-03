<template>
  <div class="em-wrap">
    <!-- ── Encabezado ── -->
    <div class="em-head">
      <div class="em-title"><i class="bi bi-bug"></i> {{ title }}</div>
      <button class="em-btn em-btn--ghost" :disabled="loading" @click="reloadAll">
        <i class="bi bi-arrow-clockwise"></i><span class="hide-xs"> Actualizar</span>
      </button>
    </div>

    <!-- ── KPIs ── -->
    <div class="em-kpis">
      <div class="em-kpi"><span class="em-kpi-v">{{ summary.sin_resolver }}</span><span class="em-kpi-l">Sin resolver</span></div>
      <div class="em-kpi em-kpi--crit"><span class="em-kpi-v">{{ summary.criticos }}</span><span class="em-kpi-l">Críticos</span></div>
      <div class="em-kpi"><span class="em-kpi-v">{{ summary.nuevos_24h }}</span><span class="em-kpi-l">Nuevos 24 h</span></div>
      <div class="em-kpi"><span class="em-kpi-v">{{ summary.empresas_afectadas }}</span><span class="em-kpi-l">Empresas afectadas</span></div>
      <div class="em-kpi em-kpi--warn"><span class="em-kpi-v">{{ summary.regresiones }}</span><span class="em-kpi-l">Regresiones</span></div>
      <div class="em-kpi em-kpi--sec"><span class="em-kpi-v">{{ summary.seguridad }}</span><span class="em-kpi-l">Seguridad</span></div>
      <div class="em-kpi em-kpi--ver"><span class="em-kpi-v">{{ summary.version }}</span><span class="em-kpi-l">Versión desactualizada</span></div>
    </div>

    <!-- ── Pestañas ── -->
    <div class="em-tabs">
      <button v-for="t in TABS" :key="t.key" :class="['em-tab', tab === t.key && 'active']" @click="setTab(t.key)">
        {{ t.label }} <span class="em-tab-count">{{ counts[t.key] ?? 0 }}</span>
      </button>
    </div>

    <!-- ── Filtros ── -->
    <div class="em-filters">
      <input v-model.trim="f.q" class="em-input em-input--q" maxlength="100"
             placeholder="Buscar ref, título, endpoint o vista…" @keyup.enter="search" />
      <select v-model="f.tipo" class="em-input" @change="search">
        <option value="">Todos los tipos</option>
        <option v-for="t in TIPOS" :key="t" :value="t">{{ tipoLabel(t) }}</option>
      </select>
      <select v-model="f.nivel" class="em-input" @change="search">
        <option value="">Todos los niveles</option>
        <option v-for="n in NIVELES" :key="n" :value="n">{{ n }}</option>
      </select>
      <input v-model.number="f.company" type="number" min="1" class="em-input em-input--id"
             placeholder="ID empresa" @keyup.enter="search" />
      <div class="em-date"><CustomDatePicker v-model="f.desde" placeholder="Desde" @update:modelValue="search" /></div>
      <div class="em-date"><CustomDatePicker v-model="f.hasta" placeholder="Hasta" @update:modelValue="search" /></div>
      <button class="em-btn" @click="search"><i class="bi bi-search"></i></button>
      <button class="em-btn em-btn--ghost" title="Limpiar filtros" @click="clearFilters"><i class="bi bi-x-lg"></i></button>
      <button v-if="tab === 'sin_resolver' && summary.version > 0" class="em-btn em-btn--ver" @click="resolverVersion">
        <i class="bi bi-check2-all"></i> Resolver versión desactualizada ({{ summary.version }})
      </button>
    </div>

    <!-- ── Listado ── -->
    <div class="em-list">
      <div v-if="loading" class="em-empty">Cargando…</div>
      <div v-else-if="!items.length" class="em-empty">
        {{ tab === 'sin_resolver' ? 'Sin errores pendientes 🎉' : 'Sin registros en los últimos 120 días' }}
      </div>
      <table v-else class="em-table">
        <thead>
          <tr>
            <th>Ref</th><th>Tipo / Nivel</th><th>Error</th><th class="tc">Ocurr.</th><th class="tc">Empresas</th>
            <th>{{ tab === 'sin_resolver' ? 'Última vez' : 'Resuelto' }}</th><th>Estado</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="g in items" :key="g.id" @click="openGroup(g.id)">
            <td data-l="Ref"><span class="em-ref">{{ g.ref_code }}</span></td>
            <td data-l="Tipo">
              <span :class="['em-tipo', `em-tipo--${g.tipo_error}`]">{{ tipoLabel(g.tipo_error) }}</span>
              <span :class="['em-nivel', `em-nivel--${g.nivel}`]">{{ g.nivel }}</span>
            </td>
            <td data-l="Error" class="em-td-title">
              <div class="em-g-title">{{ g.titulo }}</div>
              <div class="em-g-sub">
                {{ g.endpoint || g.vista || '—' }}
                <span v-if="g.first_company"> · 1ª: {{ g.first_company }}</span>
              </div>
            </td>
            <td data-l="Ocurrencias" class="tc">{{ fmtNum(g.total_ocurrencias) }}</td>
            <td data-l="Empresas" class="tc">{{ fmtNum(g.total_empresas) }}</td>
            <td data-l="Fecha" class="tm">{{ fmtDT(tab === 'sin_resolver' ? g.last_seen : g.resuelto_en) }}</td>
            <td data-l="Estado">
              <span :class="['em-estado', `em-estado--${g.estado}`]">{{ estadoLabel(g.estado) }}</span>
              <span v-if="g.regresiones > 0" class="em-regr" title="Reapareció después de resuelto">↺ {{ g.regresiones }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="total > pageSize" class="em-pager">
      <button class="em-btn em-btn--ghost" :disabled="page <= 1" @click="goPage(page - 1)"><i class="bi bi-chevron-left"></i></button>
      <span>Página {{ page }} de {{ pages }} · {{ fmtNum(total) }} errores</span>
      <button class="em-btn em-btn--ghost" :disabled="page >= pages" @click="goPage(page + 1)"><i class="bi bi-chevron-right"></i></button>
    </div>

    <!-- ── Detalle ── -->
    <div v-if="sel" class="em-overlay" @click.self="sel = null">
      <div class="em-drawer">
        <div class="em-d-head">
          <div>
            <div class="em-d-ref">{{ sel.group.ref_code }}
              <span :class="['em-tipo', `em-tipo--${sel.group.tipo_error}`]">{{ tipoLabel(sel.group.tipo_error) }}</span>
              <span :class="['em-nivel', `em-nivel--${sel.group.nivel}`]">{{ sel.group.nivel }}</span>
            </div>
            <div class="em-d-title">{{ sel.group.titulo }}</div>
          </div>
          <button class="em-x" @click="sel = null"><i class="bi bi-x-lg"></i></button>
        </div>

        <div class="em-d-body">
          <!-- Resumen -->
          <div class="em-grid">
            <div><label>Estado</label><span :class="['em-estado', `em-estado--${sel.group.estado}`]">{{ estadoLabel(sel.group.estado) }}</span>
              <span v-if="sel.group.regresiones > 0" class="em-regr">↺ {{ sel.group.regresiones }} regresión(es)</span></div>
            <div><label>Ocurrencias</label>{{ fmtNum(sel.group.total_ocurrencias) }} en {{ fmtNum(sel.group.total_empresas) }} empresa(s)</div>
            <div><label>Endpoint</label><code>{{ sel.group.endpoint || '—' }}</code></div>
            <div><label>Vista</label><code>{{ sel.group.vista || '—' }}</code><span v-if="sel.group.modulo"> · {{ sel.group.modulo }}</span></div>
            <div><label>Primera vez</label>{{ fmtDT(sel.group.first_seen) }} · {{ sel.group.first_company || 'Sin empresa' }}</div>
            <div><label>Última vez</label>{{ fmtDT(sel.group.last_seen) }} · {{ sel.group.last_company || '—' }}</div>
            <div v-if="sel.group.resuelto_en" class="em-span2"><label>{{ sel.group.estado === 'IGNORADO' ? 'Ignorado' : 'Resuelto' }}</label>
              {{ fmtDT(sel.group.resuelto_en) }} · {{ sel.group.resuelto_por_nombre || '—' }}
              <span v-if="sel.group.version_solucion"> · v{{ sel.group.version_solucion }}</span></div>
            <div v-if="sel.group.nota_solucion" class="em-span2"><label>Nota de solución</label>{{ sel.group.nota_solucion }}</div>
          </div>

          <!-- Acciones -->
          <div class="em-actions">
            <textarea v-model="act.nota" class="em-input em-nota" maxlength="2000" rows="2"
                      placeholder="Nota de la solución (obligatoria para Resuelto)"></textarea>
            <input v-model.trim="act.version" class="em-input" maxlength="40" placeholder="Versión (opcional)" />
            <div class="em-act-btns">
              <button class="em-btn em-btn--ok" :disabled="saving" @click="setEstado('RESUELTO')"><i class="bi bi-check2-circle"></i> Resuelto</button>
              <button v-if="sel.group.estado !== 'EN_REVISION'" class="em-btn em-btn--rev" :disabled="saving" @click="setEstado('EN_REVISION')"><i class="bi bi-eye"></i> En revisión</button>
              <button v-if="sel.group.estado !== 'IGNORADO'" class="em-btn em-btn--ghost" :disabled="saving" @click="setEstado('IGNORADO')"><i class="bi bi-slash-circle"></i> Ignorar</button>
              <button v-if="['RESUELTO','IGNORADO'].includes(sel.group.estado)" class="em-btn em-btn--ghost" :disabled="saving" @click="setEstado('NUEVO')"><i class="bi bi-arrow-counterclockwise"></i> Reabrir</button>
              <button class="em-btn em-btn--dark" @click="copyReport"><i class="bi bi-clipboard"></i> Copiar reporte</button>
            </div>
          </div>

          <!-- Detalle de la ocurrencia -->
          <div class="em-sec-title">
            Detalle
            <select v-if="sel.details.length > 1" v-model="detIdx" class="em-input em-input--sm">
              <option v-for="(d, i) in sel.details" :key="d.id" :value="i">
                {{ d.es_regresion ? 'Regresión' : 'Primera ocurrencia' }} · {{ fmtDT(d.fecha_hora) }}
              </option>
            </select>
          </div>
          <div v-if="det" class="em-grid">
            <div><label>Fecha</label>{{ fmtDT(det.fecha_hora) }}</div>
            <div><label>Empresa</label>{{ det.company_name || '—' }} <span v-if="det.company_id">(#{{ det.company_id }})</span></div>
            <div><label>Perfil</label>{{ det.perfil || '—' }}</div>
            <div><label>Usuario</label>{{ det.username || '—' }} <span v-if="det.rol">({{ det.rol }})</span></div>
            <div><label>Id_Caja</label>{{ det.id_caja || '—' }}</div>
            <div><label>Petición</label><code>{{ det.http_method || '' }} {{ det.path_real || '—' }}</code> <span v-if="det.http_status">· {{ det.http_status }}</span></div>
            <div><label>Vista</label><code>{{ det.vista_real || '—' }}</code><span v-if="det.componente"> · {{ det.componente }}</span></div>
            <div><label>Toast</label>{{ det.toast_mostrado ? (det.toast_mensaje || 'Sí') : 'No se mostró' }}</div>
            <div><label>Versión cliente / servidor</label>{{ det.version_cliente || '—' }} / {{ det.version_servidor || '—' }}</div>
            <div><label>Dispositivo</label>{{ det.dispositivo || '—' }} · {{ det.ip || '—' }}</div>
            <div class="em-span2"><label>Navegador</label><span class="em-ua">{{ det.user_agent || '—' }}</span></div>
          </div>
          <div v-else class="em-empty em-empty--sm">Sin detalle (depurado por retención).</div>

          <template v-if="det">
            <div class="em-sec-title">Mensaje</div>
            <pre class="em-pre">{{ det.mensaje || '—' }}</pre>
            <template v-if="det.stack_trace">
              <div class="em-sec-title">Stack trace</div>
              <pre class="em-pre em-pre--stack">{{ det.stack_trace }}</pre>
            </template>
            <template v-if="det.payload">
              <div class="em-sec-title">Payload (saneado)</div>
              <pre class="em-pre">{{ pretty(det.payload) }}</pre>
            </template>
            <template v-if="det.query_params">
              <div class="em-sec-title">Parámetros URL</div>
              <pre class="em-pre">{{ pretty(det.query_params) }}</pre>
            </template>
          </template>

          <!-- Empresas afectadas -->
          <div class="em-sec-title">Empresas afectadas ({{ sel.companies.length }})</div>
          <div v-if="sel.companies.length" class="em-comp-list">
            <div v-for="c in sel.companies" :key="c.company_id" class="em-comp">
              <span class="em-comp-name">{{ c.company_name || 'Empresa' }} <small>#{{ c.company_id }}</small></span>
              <span class="em-comp-n">{{ fmtNum(c.ocurrencias) }}×</span>
              <span class="em-comp-d">{{ fmtDT(c.last_seen) }}</span>
            </div>
          </div>
          <div v-else class="em-empty em-empty--sm">Sin empresa identificada (sesión anónima o pública).</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from "vue"
import api from "@/services/apis"
import { showToast, showConfirm } from "@/utils/toast"
import CustomDatePicker from "@/components/common/CustomDatePicker.vue"
import { useModuleName } from "@/composables/useModuleName"

const { moduleName } = useModuleName()
const title = computed(() => moduleName.value || "Monitor de Errores")

const TABS = [
  { key: "sin_resolver", label: "Sin resolver" },
  { key: "resueltos",    label: "Resueltos" },
  { key: "ignorados",    label: "Ignorados" },
]
const TIPOS = ["SERVIDOR", "BASE_DATOS", "VISTA", "RED", "SINCRONIZACION", "IMPRESION", "INTEGRACION", "SEGURIDAD", "VERSION_DESACTUALIZADA"]
const NIVELES = ["CRITICO", "ERROR", "ADVERTENCIA"]
const TIPO_LABEL = {
  SERVIDOR: "Servidor", BASE_DATOS: "Base de datos", VISTA: "Vista", RED: "Red", SINCRONIZACION: "Sincronización",
  IMPRESION: "Impresión", INTEGRACION: "Integración", SEGURIDAD: "Seguridad", VERSION_DESACTUALIZADA: "Versión desactualizada",
}
const ESTADO_LABEL = { NUEVO: "Nuevo", EN_REVISION: "En revisión", RESUELTO: "Resuelto", IGNORADO: "Ignorado" }
const tipoLabel = t => TIPO_LABEL[t] || t
const estadoLabel = e => ESTADO_LABEL[e] || e

const summary = ref({ sin_resolver: 0, criticos: 0, nuevos_24h: 0, empresas_afectadas: 0, regresiones: 0, seguridad: 0, version: 0 })
const tab = ref("sin_resolver")
const items = ref([])
const counts = ref({})
const total = ref(0)
const page = ref(1)
const pageSize = 25
const pages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
const loading = ref(false)
const saving = ref(false)
const f = reactive({ q: "", tipo: "", nivel: "", company: null, desde: "", hasta: "" })

const sel = ref(null)
const detIdx = ref(0)
const det = computed(() => sel.value?.details?.[detIdx.value] || null)
const act = reactive({ nota: "", version: "" })

const fmtNum = n => new Intl.NumberFormat("es-CO").format(Number(n || 0))
function fmtDT(v) {
  if (!v) return "—"
  const d = new Date(String(v).replace(" ", "T"))
  if (isNaN(d)) return String(v)
  return d.toLocaleString("es-CO", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" })
}
function pretty(v) {
  try { return JSON.stringify(typeof v === "string" ? JSON.parse(v) : v, null, 2) } catch { return String(v) }
}

async function loadSummary() {
  try { summary.value = (await api.get("/api/error-log/summary")).data } catch { /* sin datos */ }
}

async function loadGroups() {
  loading.value = true
  try {
    const params = { tab: tab.value, page: page.value, page_size: pageSize }
    if (f.q) params.q = f.q
    if (f.tipo) params.tipo = f.tipo
    if (f.nivel) params.nivel = f.nivel
    if (f.company) params.company = f.company
    if (f.desde) params.desde = f.desde
    if (f.hasta) params.hasta = f.hasta
    const { data } = await api.get("/api/error-log/groups", { params })
    items.value = data.items
    total.value = data.total
    counts.value = data.counts
  } catch (e) {
    showToast(e.response?.data?.detail || "No se pudo cargar el listado", "error")
  } finally {
    loading.value = false
  }
}

function reloadAll() { loadSummary(); loadGroups() }
function search() { page.value = 1; loadGroups() }
function setTab(t) { tab.value = t; search() }
function goPage(p) { page.value = p; loadGroups() }
function clearFilters() { Object.assign(f, { q: "", tipo: "", nivel: "", company: null, desde: "", hasta: "" }); search() }

async function openGroup(id) {
  try {
    const { data } = await api.get(`/api/error-log/groups/${id}`)
    sel.value = data
    detIdx.value = 0
    act.nota = data.group.nota_solucion || ""
    act.version = ""
  } catch (e) {
    showToast(e.response?.data?.detail || "No se pudo abrir el error", "error")
  }
}

async function setEstado(estado) {
  if (estado === "RESUELTO" && (act.nota || "").trim().length < 3) {
    return showToast("Escriba la nota de la solución", "warning", 2500)
  }
  saving.value = true
  try {
    await api.patch(`/api/error-log/groups/${sel.value.group.id}/estado`, {
      estado, nota: act.nota || null, version: act.version || null,
    })
    showToast(`Marcado como ${estadoLabel(estado)}`)
    sel.value = null
    reloadAll()
  } catch (e) {
    showToast(e.response?.data?.detail || "No se pudo actualizar", "error")
  } finally {
    saving.value = false
  }
}

async function resolverVersion() {
  if (!(await showConfirm(`¿Marcar como resueltos los ${summary.value.version} errores por versión desactualizada?`, "Sí, resolver"))) return
  try {
    const { data } = await api.post("/api/error-log/groups/resolver-version", {})
    showToast(`${data.resueltos} errores resueltos`)
    reloadAll()
  } catch (e) {
    showToast(e.response?.data?.detail || "No se pudo resolver", "error")
  }
}

function buildReport() {
  const g = sel.value.group
  const d = det.value || {}
  const L = [
    `## ${g.ref_code} · ${g.tipo_error} · ${g.nivel}`,
    `**Título:** ${g.titulo}`,
    `**Clase:** ${g.clase_error || "—"}`,
    `**Endpoint:** ${g.endpoint || "—"}`,
    `**Vista:** ${d.vista_real || g.vista || "—"}${d.componente ? `  ·  Componente: ${d.componente}` : ""}`,
    `**Ocurrencias:** ${g.total_ocurrencias} en ${g.total_empresas} empresas`,
    `**Primera vez:** ${g.first_seen} · Empresa ${d.company_id || "—"} (${d.company_name || g.first_company || "—"}) · Perfil ${d.perfil || "—"} · Usuario ${d.username || "—"} (${d.rol || "—"}) · Id_Caja ${d.id_caja || "—"}`,
    `**Última vez:** ${g.last_seen} · Empresa ${g.last_company_id || "—"}`,
    `**Estado:** ${g.estado}${g.regresiones ? ` · ${g.regresiones} regresión(es)` : ""}`,
    `**Versión cliente / servidor:** ${d.version_cliente || "—"} / ${d.version_servidor || "—"}`,
    `**Petición:** ${d.http_method || ""} ${d.path_real || "—"} ${d.http_status ? `(${d.http_status})` : ""}`,
    `**Toast mostrado:** ${d.toast_mostrado ? `"${d.toast_mensaje || ""}"` : "No"}`,
    "", "### Mensaje", "```", d.mensaje || "—", "```",
  ]
  if (d.payload) L.push("", "### Payload (saneado)", "```json", pretty(d.payload), "```")
  if (d.stack_trace) L.push("", "### Stack trace", "```", d.stack_trace, "```")
  return L.join("\n")
}

async function copyReport() {
  try {
    await navigator.clipboard.writeText(buildReport())
    showToast("Reporte copiado")
  } catch {
    showToast("No se pudo copiar (el navegador bloqueó el portapapeles)", "warning", 2500)
  }
}

watch(sel, v => { document.body.style.overflow = v ? "hidden" : "" })

onMounted(reloadAll)
</script>

<style scoped>
.em-wrap { padding: 16px 0 32px; }
.em-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
.em-title { font-size: 18px; font-weight: 700; color: #1e293b; display: flex; align-items: center; gap: 8px; }

/* KPIs */
.em-kpis { display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px; margin-bottom: 16px; }
.em-kpi { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px; display: flex; flex-direction: column; gap: 2px; border-left: 4px solid #2563eb; }
.em-kpi--crit { border-left-color: #dc2626; }
.em-kpi--warn { border-left-color: #f59e0b; }
.em-kpi--sec  { border-left-color: #7c3aed; }
.em-kpi--ver  { border-left-color: #64748b; }
.em-kpi-v { font-size: 22px; font-weight: 800; color: #0f172a; }
.em-kpi-l { font-size: 12px; color: #64748b; }

/* Tabs */
.em-tabs { display: flex; gap: 6px; border-bottom: 2px solid #e2e8f0; margin-bottom: 12px; overflow-x: auto; }
.em-tab { background: none; border: none; padding: 10px 14px; font-weight: 600; color: #64748b; border-bottom: 3px solid transparent; margin-bottom: -2px; white-space: nowrap; }
.em-tab.active { color: #1d4ed8; border-bottom-color: #1d4ed8; }
.em-tab-count { background: #e2e8f0; color: #334155; border-radius: 10px; padding: 1px 8px; font-size: 12px; margin-left: 4px; }
.em-tab.active .em-tab-count { background: #dbeafe; color: #1d4ed8; }

/* Filtros */
.em-filters { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 12px; }
.em-input { border: 1px solid #cbd5e1; border-radius: 8px; padding: 8px 10px; font-size: 14px; background: #fff; color: #0f172a; }
.em-input--q { flex: 1 1 240px; min-width: 0; }
.em-input--id { width: 120px; }
.em-input--sm { padding: 4px 8px; font-size: 13px; margin-left: 8px; }
.em-date { width: 150px; }

.em-btn { border: none; border-radius: 8px; padding: 8px 14px; font-weight: 600; font-size: 14px; background: #2563eb; color: #fff; display: inline-flex; align-items: center; gap: 6px; }
.em-btn:disabled { opacity: .55; }
.em-btn--ghost { background: #f1f5f9; color: #334155; }
.em-btn--ok { background: #16a34a; }
.em-btn--rev { background: #f59e0b; }
.em-btn--dark { background: #0f172a; }
.em-btn--ver { background: #64748b; }

/* Tabla */
.em-list { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden; }
.em-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.em-table th { background: #f8fafc; color: #475569; font-size: 12px; text-transform: uppercase; padding: 10px; text-align: left; }
.em-table td { padding: 10px; border-top: 1px solid #f1f5f9; vertical-align: top; }
.em-table tbody tr { cursor: pointer; }
.em-table tbody tr:hover { background: #f8fafc; }
.tc { text-align: center !important; }
.tm { white-space: nowrap; color: #475569; }
.em-td-title { max-width: 420px; }
.em-g-title { font-weight: 600; color: #0f172a; word-break: break-word; display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.em-g-sub { font-size: 12px; color: #64748b; word-break: break-all; }
.em-ref { font-family: ui-monospace, monospace; font-weight: 700; color: #1d4ed8; white-space: nowrap; }
.em-empty { padding: 32px; text-align: center; color: #64748b; }
.em-empty--sm { padding: 12px; }

.em-tipo { display: inline-block; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px; background: #e2e8f0; color: #334155; margin: 0 4px 4px 0; white-space: nowrap; }
.em-tipo--SERVIDOR { background: #fee2e2; color: #991b1b; }
.em-tipo--BASE_DATOS { background: #fef3c7; color: #92400e; }
.em-tipo--VISTA { background: #dbeafe; color: #1e40af; }
.em-tipo--RED { background: #e0f2fe; color: #075985; }
.em-tipo--SINCRONIZACION { background: #dcfce7; color: #166534; }
.em-tipo--IMPRESION { background: #f3e8ff; color: #6b21a8; }
.em-tipo--INTEGRACION { background: #ffedd5; color: #9a3412; }
.em-tipo--SEGURIDAD { background: #ede9fe; color: #5b21b6; }
.em-tipo--VERSION_DESACTUALIZADA { background: #f1f5f9; color: #475569; }
.em-nivel { display: inline-block; font-size: 10px; font-weight: 800; padding: 1px 6px; border-radius: 4px; white-space: nowrap; }
.em-nivel--CRITICO { background: #dc2626; color: #fff; }
.em-nivel--ERROR { background: #fb923c; color: #fff; }
.em-nivel--ADVERTENCIA { background: #fde68a; color: #78350f; }
.em-estado { display: inline-block; font-size: 12px; font-weight: 700; padding: 2px 8px; border-radius: 10px; white-space: nowrap; }
.em-estado--NUEVO { background: #fee2e2; color: #b91c1c; }
.em-estado--EN_REVISION { background: #fef3c7; color: #92400e; }
.em-estado--RESUELTO { background: #dcfce7; color: #166534; }
.em-estado--IGNORADO { background: #e2e8f0; color: #475569; }
.em-regr { font-size: 12px; font-weight: 700; color: #b45309; margin-left: 6px; white-space: nowrap; }

.em-pager { display: flex; justify-content: center; align-items: center; gap: 12px; margin-top: 12px; color: #475569; font-size: 14px; }

/* Drawer */
.em-overlay { position: fixed; inset: 0; background: rgba(15, 23, 42, .45); z-index: 1500; display: flex; justify-content: flex-end; }
.em-drawer { width: min(860px, 100%); height: 100%; background: #f8fafc; display: flex; flex-direction: column; box-shadow: -8px 0 24px rgba(0,0,0,.15); }
.em-d-head { display: flex; justify-content: space-between; gap: 12px; padding: 16px; background: #0f172a; color: #fff; }
.em-d-ref { font-family: ui-monospace, monospace; font-weight: 800; font-size: 16px; display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.em-d-title { margin-top: 6px; font-size: 14px; color: #cbd5e1; word-break: break-word; }
.em-x { background: none; border: none; color: #fff; font-size: 20px; align-self: flex-start; }
.em-d-body { overflow-y: auto; padding: 16px; flex: 1; }
.em-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 16px; background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px; font-size: 14px; color: #0f172a; }
.em-grid label { display: block; font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; margin-bottom: 2px; }
.em-grid code { color: #1e293b; background: #f1f5f9; padding: 1px 4px; border-radius: 4px; word-break: break-all; }
.em-span2 { grid-column: span 2; }
.em-ua { font-size: 12px; color: #475569; word-break: break-all; }
.em-actions { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px; margin-top: 12px; display: flex; flex-direction: column; gap: 8px; }
.em-nota { resize: vertical; }
.em-act-btns { display: flex; flex-wrap: wrap; gap: 8px; }
.em-sec-title { font-weight: 700; color: #1e293b; margin: 16px 0 6px; display: flex; align-items: center; flex-wrap: wrap; }
.em-pre { background: #0f172a; color: #e2e8f0; border-radius: 8px; padding: 12px; font-size: 12px; white-space: pre-wrap; word-break: break-word; max-height: 320px; overflow: auto; margin: 0; }
.em-pre--stack { max-height: 420px; }
.em-comp-list { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; max-height: 260px; overflow-y: auto; }
.em-comp { display: grid; grid-template-columns: 1fr auto auto; gap: 12px; padding: 8px 12px; border-top: 1px solid #f1f5f9; font-size: 13px; }
.em-comp:first-child { border-top: none; }
.em-comp-name small { color: #94a3b8; }
.em-comp-n { font-weight: 700; color: #1d4ed8; }
.em-comp-d { color: #64748b; white-space: nowrap; }

@media (max-width: 1200px) {
  .em-kpis { grid-template-columns: repeat(4, 1fr); }
}

/* Tablet / móvil grande: la tabla pasa a tarjetas */
@media (max-width: 768px) {
  .em-kpis { grid-template-columns: repeat(3, 1fr); gap: 8px; }
  .em-kpi { padding: 10px; }
  .em-kpi-v { font-size: 18px; }
  .em-input--q { flex-basis: 100%; }
  .em-filters select { flex: 1 1 45%; }
  .em-date { flex: 1 1 45%; width: auto; }
  .em-input--id { flex: 1 1 45%; width: auto; }
  .em-list { background: none; border: none; }
  .em-table thead { display: none; }
  .em-table, .em-table tbody, .em-table tr, .em-table td { display: block; width: 100%; }
  .em-table tr { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; margin-bottom: 10px; padding: 8px 4px; }
  .em-table td { border: none; padding: 4px 10px; display: flex; justify-content: space-between; gap: 10px; text-align: right; }
  .em-table td::before { content: attr(data-l); font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; text-align: left; flex-shrink: 0; }
  .em-td-title { max-width: none; flex-direction: column; text-align: left !important; }
  .tc { text-align: right !important; }
  .em-grid { grid-template-columns: 1fr; }
  .em-span2 { grid-column: span 1; }
}

/* Móvil pequeño */
@media (max-width: 576px) {
  .em-kpis { grid-template-columns: repeat(2, 1fr); }
  .em-kpi-l { font-size: 11px; }
  .em-title { font-size: 16px; }
  .hide-xs { display: none; }
  .em-filters select, .em-date, .em-input--id { flex-basis: 100%; }
  .em-btn--ver { width: 100%; justify-content: center; }
  .em-d-body { padding: 10px; }
  .em-act-btns .em-btn { flex: 1 1 45%; justify-content: center; }
  .em-comp { grid-template-columns: 1fr auto; }
  .em-comp-d { grid-column: span 2; }
}
</style>
