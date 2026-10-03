<template>
  <div class="cc-page">
    <!-- ══ Encabezado ══ -->
    <div class="cc-head">
      <h2 class="cc-title"><i class="bi bi-calculator me-2"></i>{{ moduleName || 'Cuadre Caja' }}</h2>
      <TurnoIndicator />
    </div>

    <!-- ══ Filtros ══ -->
    <div class="cc-filtros">
      <div class="cc-modos">
        <button v-for="m in MODOS" :key="m.v" :class="['cc-modo', { active: f.modo === m.v }]" @click="cambiarModo(m.v)">
          <i :class="m.i"></i> {{ m.l }}
        </button>
      </div>
      <select v-if="f.modo === 'usuario'" v-model.number="f.user_id" class="cc-select" @change="cargar">
        <option :value="null" disabled>Seleccione el usuario</option>
        <option v-for="u in opc.usuarios" :key="u.id" :value="u.id">{{ u.nombre }}</option>
      </select>
      <select v-if="f.modo === 'caja'" v-model.number="f.closing_id" class="cc-select" @change="cargar">
        <option :value="null" disabled>Seleccione el Id_Caja</option>
        <option v-for="t in opc.turnos" :key="t.id" :value="t.id">
          #{{ t.id }} · {{ t.caja }} · {{ t.usuario || `Cajero ${t.user_id}` }}{{ t.cerrado ? ' (cerrado)' : ' (abierto)' }}{{ t.origen === 'escritorio' ? ' · escritorio' : '' }}
        </option>
      </select>
      <PeriodoSelector :modelValue="{ periodo: f.periodo, fecha: f.fecha }" :anteriores="puedeFecha"
                       :periodos="!!opc.permisos?.periodos" :hoy="opc.hoy" @update:modelValue="cambiarPeriodo" />
      <div v-if="opc.pos_electronico" class="cc-origen">
        <label v-for="o in ORIGENES" :key="o.v" :class="['cc-radio', { active: f.origen === o.v }]">
          <input type="radio" :value="o.v" v-model="f.origen" @change="cargar" /> {{ o.l }}
        </label>
      </div>
      <span v-if="estado" :class="['cc-estado', `cc-estado--${estado.c}`]"><i :class="estado.i"></i> {{ estado.t }}</span>
    </div>

    <div v-if="loading && !c" class="cc-state"><div class="spinner-border spinner-border-sm text-primary"></div></div>
    <div v-else-if="!c" class="cc-state cc-empty"><i class="bi bi-safe2"></i><p>{{ vacio }}</p></div>

    <!-- ══ Cuerpo ══ -->
    <div v-else :class="['cc-grid', { 'cc-loading': loading }]">
      <!-- Columna 1: desgloses y conteos -->
      <div class="cc-col">
        <section class="cc-card">
          <h3 class="cc-card-t cc-t--cyan">Desglose Venta</h3>
          <div class="cc-big"><span>Venta del Día</span><b>{{ fmt(c.venta.total) }}</b></div>
          <div class="cc-row"><span>Efectivo</span><b>{{ fmt(c.venta.efectivo) }}</b></div>
          <div class="cc-row"><span>Otros</span><b>{{ fmt(c.venta.otros) }}</b></div>
        </section>
        <section class="cc-card">
          <h3 class="cc-card-t cc-t--cyan">Desglose Domicilios</h3>
          <div class="cc-big"><span>Valor Domicilios</span><b>{{ fmt(c.domicilios.total) }}</b></div>
          <div class="cc-row"><span>Efectivo</span><b>{{ fmt(c.domicilios.efectivo) }}</b></div>
          <div class="cc-row"><span>Otros</span><b>{{ fmt(c.domicilios.otros) }}</b></div>
        </section>
        <section class="cc-card">
          <h3 class="cc-card-t cc-t--cyan">Desglose Propinas</h3>
          <div class="cc-big"><span>Propinas</span><b>{{ fmt(c.propinas.total) }}</b></div>
          <div class="cc-row"><span>Efectivo</span><b>{{ fmt(c.propinas.efectivo) }}</b></div>
          <div class="cc-row"><span>Otros</span><b>{{ fmt(c.propinas.otros) }}</b></div>
        </section>
        <section class="cc-card">
          <div class="cc-counts">
            <button class="cc-count" @click="verLista('cuentas')" :disabled="!c.conteos.cuentas">
              <span>Cuentas</span><b>{{ c.conteos.cuentas }}</b>
            </button>
            <button class="cc-count" @click="verLista('otros')" :disabled="!c.conteos.otros" title="Pagadas con una forma de pago diferente de efectivo">
              <span>Otros</span><b>{{ c.conteos.otros }}</b>
            </button>
            <button class="cc-count cc-count--red" @click="verLista('anuladas')" :disabled="!c.conteos.anuladas">
              <span>Anuladas</span><b>{{ c.conteos.anuladas }}</b>
            </button>
          </div>
          <div class="cc-rango">
            <div><span>{{ etiquetaDoc }} Inicial</span><b>{{ c.conteos.inicial || '—' }}</b></div>
            <div><span>{{ etiquetaDoc }} Final</span><b>{{ c.conteos.final || '—' }}</b></div>
          </div>
        </section>
      </div>

      <!-- Columna 2: entradas y salidas de efectivo (dinámicas) -->
      <div class="cc-col">
        <section class="cc-card">
          <h3 class="cc-card-t cc-t--lila">Entran Efectivo</h3>
          <div v-for="e in c.entran" :key="'e' + e.clave" class="cc-mov">
            <span class="cc-mov-l">{{ e.label }}</span>
            <button v-if="e.ver" class="cc-ver" @click="verMov(e.clave, e.label)">Ver</button>
            <CurrencyInput v-if="e.clave === 'base_inicial' && c.editable_bases" v-model="bases.inicial" class="cc-inp" @update:model-value="onBaseInicial" />
            <b v-else class="cc-mov-v">{{ fmt(e.clave === 'base_inicial' ? bases.inicial : e.valor) }}</b>
          </div>
          <div class="cc-total"><span>Total Ingresos</span><b>{{ fmt(totalEntran) }}</b></div>
        </section>
        <section class="cc-card">
          <h3 class="cc-card-t cc-t--lila">Salen Efectivo</h3>
          <div v-for="s in c.salen" :key="'s' + s.clave" class="cc-mov">
            <span class="cc-mov-l">{{ s.label }}</span>
            <button v-if="s.ver" class="cc-ver" @click="verMov(s.clave, s.label)">Ver</button>
            <CurrencyInput v-if="s.clave === 'base_final' && c.editable_bases" v-model="bases.final" class="cc-inp" @update:model-value="finalTocada = true" />
            <b v-else class="cc-mov-v">{{ fmt(s.clave === 'base_final' ? bases.final : s.valor) }}</b>
          </div>
          <div class="cc-total cc-total--red"><span>Total Egresos</span><b>{{ fmt(totalSalen) }}</b></div>
        </section>
        <section class="cc-card cc-entregar">
          <span>Dinero a Entregar</span>
          <b>{{ fmt(dineroEntregar) }}</b>
        </section>
      </div>

      <!-- Columna 3: formas de pago y venta por categoría -->
      <div class="cc-col">
        <section class="cc-card">
          <h3 class="cc-card-t cc-t--green">Formas de Pago</h3>
          <div v-if="!c.formas_pago.length" class="cc-none">Sin pagos</div>
          <div v-for="p in c.formas_pago" :key="p.name" class="cc-row"><span>{{ p.name }}</span><b>{{ fmt(p.valor) }}</b></div>
        </section>
        <section class="cc-card">
          <h3 class="cc-card-t cc-t--green">Venta x Categoría</h3>
          <div v-if="!c.categorias.length" class="cc-none">Sin ventas</div>
          <div class="cc-cats">
            <div v-for="x in c.categorias" :key="x.categoria" class="cc-cat">
              <span class="cc-cat-n">{{ x.categoria }}</span>
              <span class="cc-cat-q">{{ x.cantidad }}</span>
              <b>{{ fmt(x.valor) }}</b>
            </div>
          </div>
        </section>
      </div>
    </div>

    <!-- ══ Pie ══ -->
    <div class="cc-foot">
      <button class="cc-btn" :disabled="!c || !(c.documentos?.recibos?.length || c.documentos?.facturas?.length)" @click="abrirArticulos"><i class="bi bi-list-ul"></i> Lista Artículos</button>
      <button class="cc-btn cc-btn--warn" :disabled="!puedeCerrar || cerrando" :title="tituloCierre" @click="cerrarTurno">
        <i :class="cerrando ? 'bi bi-arrow-repeat spin' : 'bi bi-lock-fill'"></i> Cierre
      </button>
      <button class="cc-btn cc-btn--primary" :disabled="!c" @click="impOpc.show = true"><i class="bi bi-printer-fill"></i> Impresión</button>
      <button class="cc-btn" @click="salir"><i class="bi bi-box-arrow-left"></i> Salir</button>
    </div>

    <!-- ══ Modal: lista de cuentas / otros / anuladas ══ -->
    <div v-if="lista.show" class="cc-overlay" @click.self="lista.show = false">
      <div class="cc-modal">
        <div class="cc-modal-h"><b>{{ lista.titulo }}</b><button class="cc-x" @click="lista.show = false"><i class="bi bi-x-lg"></i></button></div>
        <div class="cc-modal-b">
          <table class="cc-tbl">
            <thead><tr><th>{{ etiquetaDoc }}</th><th v-if="lista.clave === 'otros'">Formas de pago</th><th class="ta-r">Valor</th></tr></thead>
            <tbody>
              <tr v-for="r in lista.rows" :key="r.numero">
                <td class="mono">{{ r.numero }}</td><td v-if="lista.clave === 'otros'">{{ r.formas }}</td><td class="ta-r">{{ fmt(r.valor) }}</td>
              </tr>
            </tbody>
            <tfoot><tr><td :colspan="lista.clave === 'otros' ? 2 : 1">{{ lista.rows.length }} {{ lista.rows.length === 1 ? 'registro' : 'registros' }}</td>
              <td class="ta-r">{{ fmt(lista.rows.reduce((a, r) => a + r.valor, 0)) }}</td></tr></tfoot>
          </table>
        </div>
      </div>
    </div>

    <!-- ══ Modal: detalle de un movimiento (Ver) ══ -->
    <div v-if="mov.show" class="cc-overlay" @click.self="mov.show = false">
      <div class="cc-modal">
        <div class="cc-modal-h"><b>{{ mov.titulo }}</b><button class="cc-x" @click="mov.show = false"><i class="bi bi-x-lg"></i></button></div>
        <div class="cc-modal-b">
          <table class="cc-tbl">
            <thead><tr><th>Concepto</th><th class="ta-r">Valor</th><th class="ta-r">Efectivo</th></tr></thead>
            <tbody>
              <tr v-for="m in mov.rows" :key="m.id">
                <td>{{ m.concepto }}<div v-if="m.detalle && m.detalle !== m.concepto" class="cc-sub">{{ m.detalle }}</div></td>
                <td class="ta-r">{{ fmt(m.valor) }}</td><td class="ta-r">{{ fmt(m.efectivo) }}</td>
              </tr>
            </tbody>
            <tfoot><tr><td>Total</td><td class="ta-r">{{ fmt(mov.rows.reduce((a, m) => a + m.valor, 0)) }}</td>
              <td class="ta-r">{{ fmt(mov.rows.reduce((a, m) => a + m.efectivo, 0)) }}</td></tr></tfoot>
          </table>
        </div>
      </div>
    </div>

    <!-- ══ Modal: lista de artículos vendidos por categoría ══ -->
    <div v-if="art.show" class="cc-overlay" @click.self="art.show = false">
      <div class="cc-modal cc-modal--lg">
        <div class="cc-modal-h"><b><i class="bi bi-list-ul me-1"></i>Artículos vendidos</b><button class="cc-x" @click="art.show = false"><i class="bi bi-x-lg"></i></button></div>
        <div class="cc-modal-b">
          <div v-if="art.loading" class="cc-state"><div class="spinner-border spinner-border-sm text-primary"></div></div>
          <template v-else>
            <div v-for="x in art.rows" :key="x.categoria" class="cc-art-cat">
              <div class="cc-art-h"><span>{{ x.categoria }}</span><span class="cc-cat-q">{{ x.cantidad }}</span><b>{{ fmt(x.valor) }}</b></div>
              <div v-for="i in x.items" :key="i.producto" class="cc-art-i">
                <span>{{ i.producto }}</span><span class="cc-cat-q">{{ i.cantidad }}</span><span>{{ fmt(i.valor) }}</span>
              </div>
            </div>
            <div class="cc-total"><span>Total</span><b>{{ fmt(art.total) }}</b></div>
          </template>
        </div>
      </div>
    </div>

    <!-- ══ Modal: opciones de impresión ══ -->
    <div v-if="impOpc.show" class="cc-overlay" @click.self="impOpc.show = false">
      <div class="cc-modal cc-modal--sm">
        <div class="cc-modal-h"><b><i class="bi bi-printer me-1"></i>Impresión del cuadre</b><button class="cc-x" @click="impOpc.show = false"><i class="bi bi-x-lg"></i></button></div>
        <div class="cc-modal-b">
          <p class="cc-help">El cuadre lleva los totales. Marque los detalles a anexar: en tirilla cada uno sale aparte (con corte de papel); en PDF o Excel van juntos.</p>
          <label class="cc-check"><input type="checkbox" v-model="incluir.movimientos" /> Detalle de gastos, compras y demás movimientos</label>
          <label class="cc-check"><input type="checkbox" v-model="incluir.articulos" /> Lista de artículos vendidos</label>
          <label class="cc-check"><input type="checkbox" v-model="incluir.categorias" /> Venta por categoría</label>
        </div>
        <div class="cc-modal-f">
          <button class="cc-btn" @click="impOpc.show = false">Cancelar</button>
          <button class="cc-btn cc-btn--primary" :disabled="impOpc.loading" @click="vistaPrevia">
            <i :class="impOpc.loading ? 'bi bi-arrow-repeat spin' : 'bi bi-eye'"></i> Vista previa
          </button>
        </div>
      </div>
    </div>

    <ImprimirRecibo
      v-if="impresion"
      :receiptData="impresion"
      :companyId="companyId"
      printersPath="/api/pos/recibo-impresion/impresoras"
      printPath="/api/caja/cuadre/imprimir"
      :printExtra="{ ...params(), incluir: { ...incluir } }"
      @close="impresion = null"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Swal from 'sweetalert2'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'
import { useModuleName } from '@/composables/useModuleName'
import { useCompanyStore } from '@/stores/companyStore'
import PeriodoSelector from '@/components/common/PeriodoSelector.vue'
import CurrencyInput from '@/components/CurrencyInput.vue'
import TurnoIndicator from '@/components/layout/TurnoIndicator.vue'
import ImprimirRecibo from '@/components/billing/ImprimirRecibo.vue'

const BASE = '/api/caja/cuadre'
const MODOS = [
  { v: 'todos', l: 'Todos', i: 'bi bi-collection' },
  { v: 'usuario', l: 'Usuario', i: 'bi bi-person' },
  { v: 'caja', l: 'Id_Caja', i: 'bi bi-safe2' },
]
const ORIGENES = [{ v: 'facturas', l: 'Facturas' }, { v: 'recibos', l: 'Recibos' }, { v: 'ambos', l: 'Ambos' }]
const INCLUIR_KEY = 'cuadre_caja_incluir'

const router = useRouter()
const { moduleName } = useModuleName()
const companyStore = useCompanyStore()
const companyId = computed(() => Number(companyStore.selectedCompany?.id_company || companyStore.selectedCompany?.id || 0))

const fmtMon = computed(() => new Intl.NumberFormat('es-CO', {
  style: 'currency', currency: companyStore.selectedCompany?.currency_code || 'COP', maximumFractionDigits: 0,
}))
const fmt = v => fmtMon.value.format(Math.round(Number(v) || 0))

// Selector de fecha: solo con el permiso "Consultar Facturas y Cuadres Anteriores" (Roles → Control de Acceso)
const puedeFecha = computed(() => !!opc.value.permisos?.anteriores)

const f = reactive({ fecha: '', periodo: 'dia', modo: 'todos', user_id: null, closing_id: null, origen: 'recibos' })
const opc = ref({ turnos: [], usuarios: [], pos_electronico: false })
const c = ref(null)
const loading = ref(false)
const cerrando = ref(false)
const bases = reactive({ inicial: 0, final: 0 })
const finalTocada = ref(false)
let seq = 0

const etiquetaDoc = computed(() => (c.value?.origen === 'facturas' ? 'Fac.' : c.value?.origen === 'ambos' ? 'Doc.' : 'Rbo.'))
const vacio = computed(() => f.modo === 'usuario' ? 'Seleccione el usuario' : f.modo === 'caja' ? 'Seleccione el Id_Caja' : 'Sin información')

const turnoSel = computed(() => opc.value.turnos.find(t => t.id === f.closing_id) || null)
const estado = computed(() => {
  if (f.modo !== 'caja' || !turnoSel.value) return null
  return turnoSel.value.cerrado
    ? { t: 'Finalizado', c: 'fin', i: 'bi bi-lock-fill' }
    : { t: 'Caja abierta', c: 'open', i: 'bi bi-unlock-fill' }
})
const puedeCerrar = computed(() => !!(c.value && f.modo === 'caja' && turnoSel.value && !turnoSel.value.cerrado
  && turnoSel.value.origen === 'web' && opc.value.permisos?.cierre
  && (opc.value.es_admin || turnoSel.value.user_id === opc.value.user_id)))
const tituloCierre = computed(() => {
  if (f.modo !== 'caja') return 'El cierre se hace sobre un Id_Caja'
  if (turnoSel.value?.cerrado) return 'Este Id_Caja ya está cerrado'
  if (turnoSel.value?.origen === 'escritorio') return 'Este Id_Caja se cierra desde el programa de escritorio'
  if (opc.value.permisos && !opc.value.permisos.cierre) return 'Su rol no tiene permiso para hacer el cierre de caja'
  if (turnoSel.value && !puedeCerrar.value) return 'Solo el usuario que abrió la caja o un administrador'
  return 'Cerrar la caja'
})

// Las bases son lo único editable: los totales se ajustan al instante (el servidor recalcula al cerrar/imprimir)
const valorFila = (lista, clave) => lista.find(x => x.clave === clave)?.valor || 0
const totalEntran = computed(() => c.value ? c.value.total_entran - valorFila(c.value.entran, 'base_inicial') + (Number(bases.inicial) || 0) : 0)
const totalSalen = computed(() => c.value ? c.value.total_salen - valorFila(c.value.salen, 'base_final') + (Number(bases.final) || 0) : 0)
const dineroEntregar = computed(() => totalEntran.value - totalSalen.value)
function onBaseInicial(v) { if (!finalTocada.value) bases.final = Number(v) || 0 }

function params() {
  const p = { fecha: f.fecha, periodo: f.periodo, modo: f.modo, origen: f.origen }
  if (f.modo === 'usuario') p.user_id = f.user_id
  if (f.modo === 'caja') p.closing_id = f.closing_id
  if (c.value?.editable_bases) { p.base_inicial = Number(bases.inicial) || 0; p.base_final = Number(bases.final) || 0 }
  return p
}

async function cargarOpciones() {
  const { data } = await api.get(`${BASE}/opciones`, { params: { fecha: f.fecha || undefined, periodo: f.periodo } })
  opc.value = data
  if (!f.fecha) f.fecha = data.fecha
  if (!data.pos_electronico) f.origen = 'recibos'
  if (f.modo === 'usuario' && !data.usuarios.some(u => u.id === f.user_id)) f.user_id = data.usuarios[0]?.id ?? null
  if (f.modo === 'caja' && !data.turnos.some(t => t.id === f.closing_id)) f.closing_id = data.turnos[0]?.id ?? null
}

async function cargar() {
  if ((f.modo === 'usuario' && !f.user_id) || (f.modo === 'caja' && !f.closing_id)) { c.value = null; return }
  const my = ++seq
  loading.value = true
  try {
    const p = { fecha: f.fecha, periodo: f.periodo, modo: f.modo, origen: f.origen }
    if (f.modo === 'usuario') p.user_id = f.user_id
    if (f.modo === 'caja') p.closing_id = f.closing_id
    const { data } = await api.get(BASE, { params: p })
    if (my !== seq) return
    c.value = data
    bases.inicial = data.bases.inicial
    bases.final = data.bases.final
    finalTocada.value = data.bases.final !== data.bases.inicial
  } catch (e) {
    if (my === seq) { c.value = null; showToast(e?.response?.data?.detail || 'No se pudo cargar el cuadre', 'error') }
  } finally {
    if (my === seq) loading.value = false
  }
}

async function recargarTodo() {
  try { await cargarOpciones() } catch (e) { showToast(e?.response?.data?.detail || 'No se pudieron cargar los turnos', 'error') }
  await cargar()
}

function cambiarModo(m) {
  if (f.modo === m) return
  f.modo = m
  c.value = null
  if (m === 'usuario' && !f.user_id) f.user_id = opc.value.turno_actual ? opc.value.user_id : (opc.value.usuarios[0]?.id ?? null)
  if (m === 'caja' && !opc.value.turnos.some(t => t.id === f.closing_id)) {
    const propio = opc.value.turnos.find(t => t.id === opc.value.turno_actual?.id)
    f.closing_id = propio?.id ?? opc.value.turnos[0]?.id ?? null
  }
  cargar()
}

watch(() => f.fecha, (n, o) => { if (o && n !== o) recargarTodo() })
function cambiarPeriodo(v) {
  const cambioTipo = v.periodo !== f.periodo
  f.periodo = v.periodo
  if (v.fecha !== f.fecha) f.fecha = v.fecha            // el watch de la fecha recarga
  else if (cambioTipo) recargarTodo()
}

// ── Listas (Cuentas · Otros · Anuladas) y movimientos (Ver) ─────────────────
const lista = reactive({ show: false, clave: '', titulo: '', rows: [] })
function verLista(clave) {
  const t = { cuentas: 'Cuentas', otros: 'Pagadas con otras formas de pago', anuladas: 'Anuladas' }[clave]
  Object.assign(lista, { show: true, clave, titulo: t, rows: c.value.listas[clave] || [] })
}
const mov = reactive({ show: false, titulo: '', rows: [] })
function verMov(clave, titulo) {
  Object.assign(mov, { show: true, titulo, rows: c.value.movimientos[clave] || [] })
}

// ── Lista de artículos ───────────────────────────────────────────────────────
const art = reactive({ show: false, loading: false, rows: [], total: 0 })
async function abrirArticulos() {
  Object.assign(art, { show: true, loading: true, rows: [], total: 0 })
  try {
    const { data } = await api.get(`${BASE}/articulos`, { params: params() })
    art.rows = data.categorias
    art.total = data.total
  } catch (e) {
    art.show = false
    showToast(e?.response?.data?.detail || 'No se pudo cargar la lista de artículos', 'error')
  } finally { art.loading = false }
}

// ── Cierre del turno ─────────────────────────────────────────────────────────
async function cerrarTurno() {
  if (!puedeCerrar.value) return
  const t = turnoSel.value
  const { isConfirmed } = await Swal.fire({
    title: `¿Cerrar ${t.caja} · Id_Caja ${t.id}?`,
    html: `Dinero a entregar: <b>${fmt(dineroEntregar.value)}</b><br>Base final: <b>${fmt(bases.final)}</b>`,
    icon: 'warning', showCancelButton: true,
    confirmButtonText: 'Sí, cerrar caja', cancelButtonText: 'Cancelar', confirmButtonColor: '#d97706',
  })
  if (!isConfirmed) return
  cerrando.value = true
  try {
    await api.post(`${BASE}/cerrar`, { closing_id: t.id, base_inicial: Number(bases.inicial) || 0, base_final: Number(bases.final) || 0 })
    showToast('Caja cerrada', 'success')
    window.dispatchEvent(new Event('turno-cambio'))
    router.push('/dashboard')
  } catch (e) {
    showToast(e?.response?.data?.detail || 'No se pudo cerrar la caja', 'error')
  } finally { cerrando.value = false }
}

// ── Impresión: opciones → vista previa (componente propio) ───────────────────
const impOpc = reactive({ show: false, loading: false })
const incluir = reactive({ movimientos: false, articulos: false, categorias: false })
try { Object.assign(incluir, JSON.parse(localStorage.getItem(INCLUIR_KEY) || '{}')) } catch { /* sin almacenamiento */ }
watch(incluir, v => { try { localStorage.setItem(INCLUIR_KEY, JSON.stringify(v)) } catch { /* sin almacenamiento */ } })
const impresion = ref(null)

async function vistaPrevia() {
  impOpc.loading = true
  try {
    const { data } = await api.post(`${BASE}/vista-previa`, { ...params(), incluir: { ...incluir } })
    impresion.value = {
      titulo: 'CUADRE DE CAJA', receipt_number: '', fecha: data.fecha,
      empresa: { nombre: data.empresa },
      lineas: [data.alcance, data.origen],
      secciones: data.documentos.flatMap((doc, di) => doc.secciones.map((s, si) => ({
        documento: di > 0 && si === 0 ? doc.titulo : null,
        titulo: s.titulo,
        items: s.filas.map(r => ({ label: r.label, valor: r.valor, cant: r.cant, bold: r.bold })),
      }))),
      items: [], pagos: [],
    }
    impOpc.show = false
  } catch (e) {
    showToast(e?.response?.data?.detail || 'No se pudo preparar la impresión', 'error')
  } finally { impOpc.loading = false }
}

function salir() {
  if (window.history.length > 1) router.back()
  else router.push('/dashboard')
}

onMounted(async () => {
  loading.value = true
  try {
    await cargarOpciones()
    f.origen = opc.value.origen_default || 'recibos'
    // Con turno abierto propio: arranca en su Id_Caja y la fecha de apertura
    const ta = opc.value.turno_actual
    if (ta?.id) {
      if (ta.fecha && ta.fecha !== f.fecha) { f.fecha = ta.fecha; await cargarOpciones() }
      f.modo = 'caja'
      f.closing_id = ta.id
    }
  } catch (e) {
    showToast(e?.response?.data?.detail || 'No se pudieron cargar los turnos', 'error')
  }
  await cargar()
})
</script>

<style scoped>
.cc-page { padding: 16px 20px 0; }
.cc-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; margin-bottom: 12px; }
.cc-title { font-size: 22px; font-weight: 800; color: #1e293b; margin: 0; }

.cc-filtros { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; background: #fff; border: 1.5px solid #e2e8f0; border-radius: 12px; padding: 10px 12px; margin-bottom: 14px; }
.cc-modos { display: flex; background: #f1f5f9; border-radius: 10px; padding: 3px; }
.cc-modo { border: none; background: none; padding: 7px 12px; border-radius: 8px; font-size: 13px; font-weight: 700; color: #64748b; cursor: pointer; white-space: nowrap; }
.cc-modo.active { background: #fff; color: #1d4ed8; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.cc-select { border: 1.5px solid #e2e8f0; border-radius: 10px; padding: 7px 10px; font-size: 13px; min-width: 220px; max-width: 100%; background: #fff; }
.cc-fecha { min-width: 150px; }
.cc-disabled { pointer-events: none; opacity: .6; }
.cc-origen { display: flex; gap: 4px; }
.cc-radio { display: inline-flex; align-items: center; gap: 4px; font-size: 13px; font-weight: 600; color: #475569; padding: 5px 9px; border-radius: 8px; cursor: pointer; border: 1.5px solid transparent; }
.cc-radio.active { border-color: #bfdbfe; background: #eff6ff; color: #1d4ed8; }
.cc-estado { margin-left: auto; font-size: 13px; font-weight: 800; border-radius: 999px; padding: 5px 12px; }
.cc-estado--fin { background: #fef08a; color: #713f12; }
.cc-estado--open { background: #dcfce7; color: #14532d; }

.cc-state { display: flex; flex-direction: column; align-items: center; padding: 50px 20px; color: #94a3b8; }
.cc-empty i { font-size: 36px; }

.cc-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; transition: opacity .15s; }
.cc-loading { opacity: .55; pointer-events: none; }
.cc-col { display: flex; flex-direction: column; gap: 12px; min-width: 0; }
.cc-card { background: #fff; border: 1.5px solid #e2e8f0; border-radius: 12px; padding: 0 12px 10px; overflow: hidden; }
.cc-card-t { font-size: 14px; font-weight: 800; text-align: center; margin: 0 -12px 8px; padding: 7px 10px; }
.cc-t--cyan { background: #cffafe; color: #155e75; }
.cc-t--lila { background: #e0e7ff; color: #3730a3; }
.cc-t--green { background: #dcfce7; color: #166534; }
.cc-big { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; padding: 4px 0 6px; border-bottom: 1px dashed #e2e8f0; margin-bottom: 4px; }
.cc-big span { font-weight: 800; color: #1d4ed8; }
.cc-big b { font-size: 20px; color: #0f172a; }
.cc-row { display: flex; justify-content: space-between; gap: 8px; font-size: 13px; padding: 3px 0; color: #334155; }
.cc-row b { color: #0f172a; }
.cc-none { font-size: 12px; color: #94a3b8; text-align: center; padding: 6px 0; }

.cc-counts { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; padding-top: 10px; }
.cc-count { display: flex; flex-direction: column; align-items: center; gap: 2px; background: #f8fafc; border: 1.5px solid #e2e8f0; border-radius: 10px; padding: 8px 4px; cursor: pointer; }
.cc-count span { font-size: 11px; font-weight: 700; color: #64748b; }
.cc-count b { font-size: 20px; color: #1e3a5f; }
.cc-count:hover:not(:disabled) { border-color: #1d4ed8; }
.cc-count:disabled { cursor: default; opacity: .7; }
.cc-count--red b { color: #b91c1c; }
.cc-rango { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 10px; }
.cc-rango div { display: flex; flex-direction: column; background: #ecfeff; border-radius: 8px; padding: 6px 8px; }
.cc-rango span { font-size: 11px; font-weight: 700; color: #155e75; }
.cc-rango b { font-family: ui-monospace, monospace; font-size: 14px; color: #0f172a; }

.cc-mov { display: flex; align-items: center; gap: 8px; padding: 4px 0; font-size: 13px; border-bottom: 1px solid #f1f5f9; }
.cc-mov-l { flex: 1; min-width: 0; font-weight: 700; color: #1e3a8a; }
.cc-mov-v { color: #0f172a; }
.cc-ver { border: 1px solid #cbd5e1; background: #fff; border-radius: 6px; padding: 1px 8px; font-size: 12px; font-weight: 700; color: #334155; cursor: pointer; }
.cc-ver:hover { border-color: #1d4ed8; color: #1d4ed8; }
.cc-inp { width: 140px; text-align: right; font-weight: 800; font-size: 14px; color: #0f172a; background: #fffbeb;
          border: 1.5px solid #fcd34d; border-radius: 8px; padding: 5px 10px; outline: none; transition: border-color .15s, box-shadow .15s; }
.cc-inp:focus { border-color: #f59e0b; background: #fff; box-shadow: 0 0 0 3px rgba(245,158,11,.18); }
.cc-total { display: flex; justify-content: space-between; gap: 8px; margin-top: 8px; font-weight: 800; color: #1d4ed8; }
.cc-total--red span { color: #dc2626; }
.cc-entregar { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 12px; background: #eef2ff; border-color: #c7d2fe; }
.cc-entregar span { font-weight: 800; color: #3730a3; }
.cc-entregar b { font-size: 26px; color: #1d4ed8; }

.cc-cats { max-height: 360px; overflow-y: auto; }
.cc-cat { display: grid; grid-template-columns: 1fr auto 110px; gap: 8px; font-size: 13px; padding: 4px 0; border-bottom: 1px solid #f1f5f9; }
.cc-cat b { text-align: right; }
.cc-cat-n { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 700; color: #334155; }
.cc-cat-q { text-align: right; color: #64748b; min-width: 34px; }

.cc-foot { position: sticky; bottom: 0; z-index: 20; display: flex; justify-content: flex-end; gap: 8px; margin: 14px -20px 0; padding: 10px 20px; background: #fff; border-top: 1px solid #e2e8f0; box-shadow: 0 -6px 16px rgba(15,23,42,.08); flex-wrap: wrap; }
.cc-btn { display: inline-flex; align-items: center; gap: 6px; border: 1.5px solid #cbd5e1; background: #fff; border-radius: 10px; padding: 8px 14px; font-size: 14px; font-weight: 700; color: #334155; cursor: pointer; }
.cc-btn:disabled { opacity: .5; cursor: not-allowed; }
.cc-btn--primary { background: linear-gradient(90deg,#1e3a5f,#1d4ed8); color: #fff; border-color: transparent; }
.cc-btn--warn { background: #f59e0b; color: #fff; border-color: transparent; }

.cc-overlay { position: fixed; inset: 0; background: rgba(15,23,42,.45); z-index: 1050; display: flex; align-items: center; justify-content: center; padding: 16px; }
.cc-modal { background: #fff; border-radius: 14px; width: 100%; max-width: 560px; max-height: 88dvh; display: flex; flex-direction: column; box-shadow: 0 20px 50px rgba(0,0,0,.25); }
.cc-modal--lg { max-width: 720px; }
.cc-modal--sm { max-width: 440px; }
.cc-modal-h { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid #e2e8f0; color: #1e293b; }
.cc-modal-b { padding: 12px 16px; overflow-y: auto; }
.cc-modal-f { display: flex; justify-content: flex-end; gap: 8px; padding: 10px 16px; border-top: 1px solid #e2e8f0; }
.cc-x { border: none; background: none; font-size: 16px; color: #64748b; cursor: pointer; }
.cc-tbl { width: 100%; font-size: 13px; border-collapse: collapse; }
.cc-tbl th { text-align: left; font-size: 11px; text-transform: uppercase; color: #64748b; border-bottom: 1.5px solid #e2e8f0; padding: 6px 4px; }
.cc-tbl td { padding: 6px 4px; border-bottom: 1px solid #f1f5f9; }
.cc-tbl tfoot td { font-weight: 800; border-bottom: none; }
.cc-sub { font-size: 11px; color: #64748b; }
.ta-r { text-align: right !important; }
.mono { font-family: ui-monospace, monospace; }
.cc-help { font-size: 13px; color: #475569; margin: 0 0 10px; }
.cc-check { display: flex; align-items: center; gap: 8px; font-size: 14px; padding: 6px 0; cursor: pointer; }
.cc-art-cat { margin-bottom: 10px; }
.cc-art-h { display: grid; grid-template-columns: 1fr auto 120px; gap: 8px; background: #f1f5f9; border-radius: 8px; padding: 6px 8px; font-weight: 800; color: #1e3a5f; }
.cc-art-h b { text-align: right; }
.cc-art-i { display: grid; grid-template-columns: 1fr auto 120px; gap: 8px; font-size: 13px; padding: 4px 8px 4px 18px; border-bottom: 1px solid #f1f5f9; }
.cc-art-i span:last-child { text-align: right; }
.spin { animation: cc-spin 1s linear infinite; display: inline-block; }
@keyframes cc-spin { to { transform: rotate(360deg); } }

/* Tablet: dos columnas (formas de pago / categorías abajo a lo ancho) */
@media (max-width: 1199px) {
  .cc-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .cc-grid > .cc-col:nth-child(3) { grid-column: 1 / -1; display: grid; grid-template-columns: 1fr 1fr; align-items: start; }
}
@media (max-width: 768px) {
  .cc-page { padding: 12px 12px 0; }
  .cc-title { font-size: 19px; }
  .cc-grid { grid-template-columns: 1fr; }
  .cc-grid > .cc-col:nth-child(3) { display: flex; }
  .cc-select { min-width: 0; flex: 1 1 100%; }
  .cc-estado { margin-left: 0; }
  .cc-foot { margin: 12px -12px 0; padding: 8px 12px; justify-content: stretch; }
  .cc-foot .cc-btn { flex: 1 1 calc(50% - 8px); justify-content: center; }
}
@media (max-width: 576px) {
  .cc-filtros { padding: 8px; gap: 8px; }
  .cc-modos { width: 100%; }
  .cc-modo { flex: 1; padding: 7px 6px; }
  .cc-fecha { flex: 1 1 100%; }
  .cc-origen { width: 100%; justify-content: space-between; }
  .cc-big b { font-size: 18px; }
  .cc-entregar b { font-size: 22px; }
  .cc-inp { width: 118px; font-size: 13px; padding: 5px 8px; }
  .cc-cat, .cc-art-h, .cc-art-i { grid-template-columns: 1fr auto 92px; }
  .cc-btn { font-size: 13px; padding: 8px 10px; }
}
</style>
