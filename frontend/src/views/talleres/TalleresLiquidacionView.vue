<template>
  <div class="liq-page">

    <!-- ── Tabs ─────────────────────────────────────────────────────────── -->
    <div class="liq-nav">
      <button v-for="t in TABS" :key="t.id"
        :class="['liq-tab', { active: tabActivo === t.id }]"
        @click="switchTab(t.id)">
        <i :class="t.icon"></i>
        <span>{{ t.label }}</span>
      </button>
    </div>

    <!-- ═══════════════════ TAB 1: LIQUIDACIÓN DEL DÍA ════════════════════ -->
    <div v-if="tabActivo === 'dia'" class="tab-pane">

      <!-- Selector de fecha -->
      <div class="fecha-bar">
        <label class="fb-label"><i class="bi bi-calendar3"></i> Turno / Fecha</label>
        <CustomDatePicker v-model="fechaDia" @update:modelValue="cargarDia" class="fb-picker" />
        <button class="btn-hoy" @click="irHoy">Hoy</button>
      </div>

      <!-- KPI bar -->
      <div class="kpi-bar" v-if="!loadingDia">
        <div class="kpi-card kpi-blue">
          <div class="kpi-val">{{ dataDia.total_workers }}</div>
          <div class="kpi-lbl">Operarios</div>
        </div>
        <div class="kpi-card kpi-green">
          <div class="kpi-val">{{ fmt(dataDia.total_mano_obra) }}</div>
          <div class="kpi-lbl">Total Mano de Obra</div>
        </div>
        <div class="kpi-card kpi-amber">
          <div class="kpi-val">{{ selectedWorkers.size }}</div>
          <div class="kpi-lbl">Seleccionados</div>
        </div>
        <div class="kpi-card kpi-violet">
          <div class="kpi-val">{{ fmt(totalSeleccionado) }}</div>
          <div class="kpi-lbl">A Imprimir</div>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loadingDia" class="loading-state">
        <i class="bi bi-arrow-repeat spin"></i> Cargando operarios del día…
      </div>

      <!-- Empty state -->
      <div v-else-if="!loadingDia && dataDia.workers.length === 0" class="empty-state">
        <i class="bi bi-person-x"></i>
        <p>No hay operarios con servicios pendientes de liquidar para el <strong>{{ fechaDia }}</strong></p>
      </div>

      <!-- Toolbar workers -->
      <div v-else class="workers-toolbar">
        <label class="chk-all">
          <input type="checkbox" :checked="todosSeleccionados" @change="toggleTodos" />
          Seleccionar todos
        </label>
        <div class="wt-actions">
          <button class="btn-act-print" :disabled="selectedWorkers.size === 0" @click="imprimirSeleccionados">
            <i class="bi bi-printer-fill"></i> Imprimir seleccionados
          </button>
          <button class="btn-act-print all" @click="imprimirTodos">
            <i class="bi bi-printer"></i> Imprimir todos
          </button>
        </div>
      </div>

      <!-- Lista de workers -->
      <div class="workers-list" v-if="!loadingDia && dataDia.workers.length > 0">
        <div v-for="w in dataDia.workers" :key="w.worker_id" class="worker-card">
          <!-- Header del card -->
          <div class="wc-head">
            <div class="wc-left">
              <input type="checkbox"
                :checked="selectedWorkers.has(w.worker_id)"
                @change="toggleSelect(w.worker_id)"
                class="wc-chk" />
              <div class="wc-avatar" :style="{ background: avatarColor(w.worker_nombre) }">
                {{ iniciales(w.worker_nombre) }}
              </div>
              <div class="wc-info">
                <span class="wc-nombre">{{ w.worker_nombre }}</span>
                <span class="wc-prof">{{ w.profesion || '—' }}</span>
              </div>
            </div>
            <div class="wc-right">
              <div class="wc-stats">
                <span class="stat"><i class="bi bi-clipboard-check"></i> {{ w.num_ordenes }} orden{{ w.num_ordenes !== 1 ? 'es' : '' }}</span>
                <span class="stat"><i class="bi bi-tools"></i> {{ w.num_items }} servicio{{ w.num_items !== 1 ? 's' : '' }}</span>
              </div>
              <div class="wc-total">{{ fmt(w.total_pendiente) }}</div>
              <div class="wc-btns">
                <button class="wc-btn expand" @click="toggleExpand(w.worker_id)" :title="expandidos.has(w.worker_id) ? 'Ocultar detalle' : 'Ver detalle'">
                  <i :class="expandidos.has(w.worker_id) ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
                </button>
                <button class="wc-btn print" @click="imprimirWorker(w)" title="Imprimir comprobante">
                  <i class="bi bi-printer-fill"></i>
                </button>
                <button class="wc-btn pagar" @click="abrirPago(w)" title="Registrar pago">
                  <i class="bi bi-cash-coin"></i>
                </button>
              </div>
            </div>
          </div>

          <!-- Detalle expandible -->
          <div v-if="expandidos.has(w.worker_id)" class="wc-detail">
            <table class="det-table">
              <thead>
                <tr>
                  <th>Orden</th>
                  <th>Placa</th>
                  <th>Servicio</th>
                  <th>Tipo</th>
                  <th class="ta-r">Subtotal</th>
                  <th class="ta-r">M. Obra</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="d in w.detalles" :key="d.detail_id">
                  <td class="mono">{{ d.numero_orden }}</td>
                  <td class="placa-badge">{{ d.placa }}</td>
                  <td>{{ d.servicio }}</td>
                  <td><span :class="['tipo-badge', `t-${d.tipo_item}`]">{{ tipoLabel(d.tipo_item) }}</span></td>
                  <td class="ta-r">{{ fmt(d.subtotal) }}</td>
                  <td class="ta-r fw-bold text-green">{{ fmt(d.monto_operario) }}</td>
                </tr>
              </tbody>
              <tfoot>
                <tr>
                  <td colspan="5" class="ta-r fw-bold">Total mano de obra:</td>
                  <td class="ta-r fw-bold text-green">{{ fmt(w.total_pendiente) }}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════ TAB 2: HISTORIAL ══════════════════════════════ -->
    <div v-if="tabActivo === 'historial'" class="tab-pane">

      <div class="filtros-bar">
        <div class="filtros-group">
          <label>Desde</label>
          <CustomDatePicker v-model="histIni" class="f-picker" />
        </div>
        <div class="filtros-group">
          <label>Hasta</label>
          <CustomDatePicker v-model="histFin" class="f-picker" />
        </div>
        <button class="btn-buscar" @click="cargarHistorial" :disabled="loadingHist">
          <i v-if="loadingHist" class="bi bi-hourglass-split spin"></i>
          <i v-else class="bi bi-search"></i>
          Buscar
        </button>
      </div>

      <!-- KPI historial -->
      <div class="kpi-bar" v-if="dataHist.count > 0">
        <div class="kpi-card kpi-blue">
          <div class="kpi-val">{{ dataHist.count }}</div>
          <div class="kpi-lbl">Liquidaciones</div>
        </div>
        <div class="kpi-card kpi-green">
          <div class="kpi-val">{{ fmt(dataHist.total) }}</div>
          <div class="kpi-lbl">Total Pagado</div>
        </div>
        <div class="kpi-card kpi-amber">
          <div class="kpi-val">{{ new Set(dataHist.liquidaciones.map(l => l.worker_id)).size }}</div>
          <div class="kpi-lbl">Operarios</div>
        </div>
      </div>

      <div v-if="loadingHist" class="loading-state">
        <i class="bi bi-arrow-repeat spin"></i> Buscando…
      </div>
      <div v-else-if="histBuscado && dataHist.count === 0" class="empty-state">
        <i class="bi bi-inbox"></i>
        <p>No hay liquidaciones en ese período</p>
      </div>
      <div v-else-if="!histBuscado" class="empty-state">
        <i class="bi bi-search"></i>
        <p>Selecciona un rango de fechas y presiona Buscar</p>
      </div>

      <div v-else class="hist-table-wrap">
        <table class="hist-table">
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Operario</th>
              <th>Profesión</th>
              <th>Items</th>
              <th class="ta-r">Total Bruto</th>
              <th class="ta-r">Pagado</th>
              <th>Forma</th>
              <th>Registró</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="liq in dataHist.liquidaciones" :key="liq.id">
              <td class="mono">{{ liq.fecha_inicio }}</td>
              <td class="fw-bold">{{ liq.worker_nombre }}</td>
              <td><span class="prof-badge">{{ liq.profesion || '—' }}</span></td>
              <td class="ta-c">{{ liq.num_items }}</td>
              <td class="ta-r">{{ fmt(liq.total_bruto) }}</td>
              <td class="ta-r fw-bold text-green">{{ fmt(liq.monto_operario) }}</td>
              <td><span :class="['forma-badge', `fp-${liq.forma_pago}`]">{{ formaLabel(liq.forma_pago) }}</span></td>
              <td class="small-txt">{{ liq.registrado_por || '—' }}</td>
              <td>
                <button class="tbl-btn" @click="imprimirHistLiq(liq)" title="Imprimir">
                  <i class="bi bi-printer-fill"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ═══════════════════ TAB 3: RESUMEN DE VENTAS ═══════════════════════ -->
    <div v-if="tabActivo === 'ventas'" class="tab-pane">

      <div class="filtros-bar">
        <div class="filtros-group">
          <label>Desde</label>
          <CustomDatePicker v-model="vtaIni" class="f-picker" />
        </div>
        <div class="filtros-group">
          <label>Hasta</label>
          <CustomDatePicker v-model="vtaFin" class="f-picker" />
        </div>
        <button class="btn-buscar" @click="cargarVentas" :disabled="loadingVentas">
          <i v-if="loadingVentas" class="bi bi-hourglass-split spin"></i>
          <i v-else class="bi bi-bar-chart-fill"></i>
          Ver Resumen
        </button>
        <router-link to="/inventory/products" class="btn-stock">
          <i class="bi bi-boxes"></i> Stock Actual
        </router-link>
      </div>

      <div v-if="loadingVentas" class="loading-state">
        <i class="bi bi-arrow-repeat spin"></i> Calculando ventas…
      </div>
      <div v-else-if="!vtaBuscado" class="empty-state">
        <i class="bi bi-bar-chart"></i>
        <p>Selecciona un rango de fechas y presiona Ver Resumen</p>
      </div>

      <template v-else>
        <!-- KPI ventas -->
        <div class="kpi-bar">
          <div class="kpi-card kpi-blue">
            <div class="kpi-val">{{ dataVentas.num_ordenes }}</div>
            <div class="kpi-lbl">Órdenes</div>
          </div>
          <div class="kpi-card kpi-green">
            <div class="kpi-val">{{ fmt(dataVentas.total_venta) }}</div>
            <div class="kpi-lbl">Total Venta</div>
          </div>
          <div class="kpi-card kpi-amber">
            <div class="kpi-val">{{ fmt(dataVentas.total_servicios) }}</div>
            <div class="kpi-lbl">Servicios</div>
          </div>
          <div class="kpi-card kpi-violet">
            <div class="kpi-val">{{ fmt(dataVentas.total_productos) }}</div>
            <div class="kpi-lbl">Repuestos</div>
          </div>
        </div>

        <!-- Acciones -->
        <div class="ventas-actions">
          <button class="btn-print-ventas" @click="imprimirVentas('servicios')">
            <i class="bi bi-printer-fill"></i> Imprimir Servicios
          </button>
          <button class="btn-print-ventas" @click="imprimirVentas('productos')">
            <i class="bi bi-printer-fill"></i> Imprimir Repuestos
          </button>
          <button class="btn-print-ventas all" @click="imprimirVentas('todo')">
            <i class="bi bi-printer"></i> Imprimir Todo
          </button>
        </div>

        <!-- Tabla servicios -->
        <div class="venta-section" v-if="dataVentas.servicios.length > 0">
          <div class="vs-header">
            <i class="bi bi-tools"></i> Servicios
            <span class="vs-total">{{ fmt(dataVentas.total_servicios) }}</span>
          </div>
          <table class="venta-table">
            <thead>
              <tr>
                <th>Servicio</th>
                <th>Tipo</th>
                <th class="ta-c">Cant.</th>
                <th class="ta-r">Subtotal</th>
                <th class="ta-r">M. Obra</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in dataVentas.servicios" :key="`${s.tipo_item}-${s.nombre}`">
                <td>{{ s.nombre }}</td>
                <td><span :class="['tipo-badge', `t-${s.tipo_item}`]">{{ tipoLabel(s.tipo_item) }}</span></td>
                <td class="ta-c">{{ s.cantidad }}</td>
                <td class="ta-r">{{ fmt(s.total) }}</td>
                <td class="ta-r text-amber">{{ fmt(s.total_mano_obra) }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td colspan="3" class="ta-r fw-bold">Total servicios:</td>
                <td class="ta-r fw-bold text-green">{{ fmt(dataVentas.total_servicios) }}</td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </div>

        <!-- Tabla repuestos/productos -->
        <div class="venta-section" v-if="dataVentas.productos.length > 0">
          <div class="vs-header">
            <i class="bi bi-box-seam"></i> Repuestos / Productos
            <span class="vs-total">{{ fmt(dataVentas.total_productos) }}</span>
          </div>
          <table class="venta-table">
            <thead>
              <tr>
                <th>Producto</th>
                <th class="ta-c">Cant.</th>
                <th class="ta-r">Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in dataVentas.productos" :key="p.nombre">
                <td>{{ p.nombre }}</td>
                <td class="ta-c">{{ p.cantidad }}</td>
                <td class="ta-r fw-bold">{{ fmt(p.total) }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td colspan="2" class="ta-r fw-bold">Total repuestos:</td>
                <td class="ta-r fw-bold text-green">{{ fmt(dataVentas.total_productos) }}</td>
              </tr>
            </tfoot>
          </table>
        </div>

        <div v-if="dataVentas.servicios.length === 0 && dataVentas.productos.length === 0" class="empty-state">
          <i class="bi bi-inbox"></i>
          <p>Sin ventas en ese período</p>
        </div>
      </template>
    </div>

    <!-- ─── Modal Registrar Pago ────────────────────────────────────────── -->
    <Teleport to="body">
      <div v-if="showModalPago" class="modal-overlay" @click.self="showModalPago = false">
        <div class="modal-box">
          <div class="mb-head">
            <div>
              <h4><i class="bi bi-cash-coin"></i> Registrar Pago</h4>
              <p class="mb-sub">{{ workerPago?.worker_nombre }} · {{ workerPago?.profesion }}</p>
            </div>
            <button class="btn-x" @click="showModalPago = false"><i class="bi bi-x-lg"></i></button>
          </div>

          <div class="mb-body">
            <div class="mb-monto">
              <span class="lbl-monto">Total a Pagar</span>
              <span class="val-monto">{{ fmt(workerPago?.total_pendiente) }}</span>
            </div>
            <div class="mb-row">
              <label>Forma de Pago</label>
              <select v-model="formPago.forma_pago" class="mb-sel">
                <option value="efectivo">Efectivo</option>
                <option value="transferencia">Transferencia</option>
                <option value="otro">Otro</option>
              </select>
            </div>
            <div class="mb-row">
              <label>Observaciones (opcional)</label>
              <input v-model="formPago.observaciones" class="mb-inp" placeholder="Ej: Pago de jornada" maxlength="200" />
            </div>
          </div>

          <div class="mb-footer">
            <button class="btn-cancel" @click="showModalPago = false">Cancelar</button>
            <button class="btn-confirmar" :disabled="guardandoPago" @click="confirmarPago">
              <i v-if="guardandoPago" class="bi bi-hourglass-split spin"></i>
              <i v-else class="bi bi-check-circle-fill"></i>
              Confirmar Pago
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Zona de impresión (invisible en pantalla) -->
    <div id="print-zone"></div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/apis'
import { useCompanyStore } from '@/stores/companyStore'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'

const router       = useRouter()
const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id)

const TABS = [
  { id: 'dia',      label: 'Liquidación del Día',    icon: 'bi bi-cash-stack' },
  { id: 'historial',label: 'Historial',              icon: 'bi bi-clock-history' },
  { id: 'ventas',   label: 'Resumen de Ventas',      icon: 'bi bi-bar-chart-fill' },
]
const tabActivo = ref('dia')
function switchTab(id) { tabActivo.value = id }

// ── Tab 1: Día ────────────────────────────────────────────────────────────────
const fechaDia     = ref(hoy())
const loadingDia   = ref(false)
const dataDia      = ref({ workers: [], total_workers: 0, total_mano_obra: 0 })
const expandidos   = ref(new Set())
const selectedWorkers = ref(new Set())

function hoy() { return new Date().toISOString().split('T')[0] }
function irHoy() { fechaDia.value = hoy(); cargarDia() }

async function cargarDia() {
  loadingDia.value = true
  expandidos.value = new Set()
  selectedWorkers.value = new Set()
  try {
    const { data } = await api.get('/api/talleres/liquidacion/dia', {
      params: { company_id: companyId.value, fecha: fechaDia.value }
    })
    dataDia.value = data
  } catch { dataDia.value = { workers: [], total_workers: 0, total_mano_obra: 0 } }
  finally { loadingDia.value = false }
}

function toggleExpand(wid) {
  const s = new Set(expandidos.value)
  s.has(wid) ? s.delete(wid) : s.add(wid)
  expandidos.value = s
}
function toggleSelect(wid) {
  const s = new Set(selectedWorkers.value)
  s.has(wid) ? s.delete(wid) : s.add(wid)
  selectedWorkers.value = s
}
const todosSeleccionados = computed(() =>
  dataDia.value.workers.length > 0 &&
  dataDia.value.workers.every(w => selectedWorkers.value.has(w.worker_id))
)
function toggleTodos() {
  if (todosSeleccionados.value) {
    selectedWorkers.value = new Set()
  } else {
    selectedWorkers.value = new Set(dataDia.value.workers.map(w => w.worker_id))
  }
}
const totalSeleccionado = computed(() =>
  dataDia.value.workers
    .filter(w => selectedWorkers.value.has(w.worker_id))
    .reduce((sum, w) => sum + w.total_pendiente, 0)
)

// ── Modal pago ────────────────────────────────────────────────────────────────
const showModalPago  = ref(false)
const workerPago     = ref(null)
const guardandoPago  = ref(false)
const formPago       = ref({ forma_pago: 'efectivo', observaciones: '' })

function abrirPago(w) {
  workerPago.value = w
  formPago.value   = { forma_pago: 'efectivo', observaciones: '' }
  showModalPago.value = true
}
async function confirmarPago() {
  if (!workerPago.value) return
  guardandoPago.value = true
  try {
    const w = workerPago.value
    await api.post('/api/talleres/liquidacion/registrar', {
      company_id:    companyId.value,
      worker_id:     w.worker_id,
      fecha:         fechaDia.value,
      monto_operario: w.total_pendiente,
      total_bruto:   w.detalles.reduce((s, d) => s + d.subtotal, 0),
      forma_pago:    formPago.value.forma_pago,
      observaciones: formPago.value.observaciones,
      detail_ids:    w.detalles.map(d => d.detail_id),
    })
    showModalPago.value = false
    await cargarDia()
  } catch { alert('Error al registrar el pago. Intente de nuevo.') }
  finally { guardandoPago.value = false }
}

// ── Tab 2: Historial ──────────────────────────────────────────────────────────
const histIni      = ref(primerDiaMes())
const histFin      = ref(hoy())
const loadingHist  = ref(false)
const histBuscado  = ref(false)
const dataHist     = ref({ liquidaciones: [], total: 0, count: 0 })

function primerDiaMes() {
  const d = new Date(); d.setDate(1)
  return d.toISOString().split('T')[0]
}
async function cargarHistorial() {
  loadingHist.value = true
  histBuscado.value = false
  try {
    const { data } = await api.get('/api/talleres/liquidacion/historial', {
      params: { company_id: companyId.value, fecha_ini: histIni.value, fecha_fin: histFin.value }
    })
    dataHist.value  = data
    histBuscado.value = true
  } catch { dataHist.value = { liquidaciones: [], total: 0, count: 0 } }
  finally { loadingHist.value = false }
}

// ── Tab 3: Ventas ─────────────────────────────────────────────────────────────
const vtaIni        = ref(hoy())
const vtaFin        = ref(hoy())
const loadingVentas = ref(false)
const vtaBuscado    = ref(false)
const dataVentas    = ref({ servicios: [], productos: [], num_ordenes: 0, total_venta: 0, total_servicios: 0, total_productos: 0 })

async function cargarVentas() {
  loadingVentas.value = true
  vtaBuscado.value    = false
  try {
    const { data } = await api.get('/api/talleres/ventas/resumen', {
      params: { company_id: companyId.value, fecha_ini: vtaIni.value, fecha_fin: vtaFin.value }
    })
    dataVentas.value = data
    vtaBuscado.value = true
  } catch { dataVentas.value = { servicios: [], productos: [], num_ordenes: 0, total_venta: 0, total_servicios: 0, total_productos: 0 } }
  finally { loadingVentas.value = false }
}

// ── Utilidades ────────────────────────────────────────────────────────────────
function fmt(v) {
  return Number(v || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 })
}
function tipoLabel(t) {
  return { mecanica: 'Mecánica', lavado: 'Lavado', latoneria: 'Latonería', pintura: 'Pintura', repuesto: 'Repuesto' }[t] || t
}
function formaLabel(f) {
  return { efectivo: 'Efectivo', transferencia: 'Transferencia', otro: 'Otro' }[f] || f || '—'
}
function avatarColor(nombre) {
  const colors = ['#3b82f6','#10b981','#f59e0b','#8b5cf6','#ef4444','#06b6d4','#f97316','#84cc16']
  let h = 0; for (const c of (nombre || '')) h = (h * 31 + c.charCodeAt(0)) & 0xffff
  return colors[h % colors.length]
}
function iniciales(nombre) {
  return (nombre || '').split(' ').slice(0, 2).map(p => p[0]).join('').toUpperCase()
}

// ── Impresión ─────────────────────────────────────────────────────────────────
const companyNombre = computed(() => companyStore.selectedCompany?.name || '')

function htmlWorker(w, fecha) {
  const rows = w.detalles.map(d => `
    <tr>
      <td>${d.numero_orden}</td>
      <td>${d.placa || ''}</td>
      <td>${d.servicio}</td>
      <td>${tipoLabel(d.tipo_item)}</td>
      <td style="text-align:right">${fmt(d.subtotal)}</td>
      <td style="text-align:right;font-weight:bold">${fmt(d.monto_operario)}</td>
    </tr>`).join('')
  return `
    <div class="p-header">
      <h2>${companyNombre.value}</h2>
      <h3>COMPROBANTE DE PAGO — MANO DE OBRA</h3>
      <p>Fecha: <strong>${fecha}</strong> &nbsp;|&nbsp; Impreso: ${new Date().toLocaleString('es-CO')}</p>
    </div>
    <div class="p-worker">
      <strong>${w.worker_nombre}</strong> &nbsp;|&nbsp; ${w.profesion || ''}
      &nbsp;&nbsp; Servicios: ${w.num_items} &nbsp;|&nbsp; Órdenes: ${w.num_ordenes}
    </div>
    <table class="p-table">
      <thead><tr><th>Orden</th><th>Placa</th><th>Servicio</th><th>Tipo</th><th>Subtotal</th><th>Mano de Obra</th></tr></thead>
      <tbody>${rows}</tbody>
      <tfoot><tr><td colspan="5" style="text-align:right;font-weight:bold">Total a Pagar:</td>
        <td style="text-align:right;font-weight:bold;font-size:15px">${fmt(w.total_pendiente)}</td></tr></tfoot>
    </table>
    <div class="p-firma">
      <div>Firma del operario: ___________________________</div>
      <div>Entregado por: ________________________________</div>
    </div>
    <div class="p-separator"></div>`
}

function imprimirWorker(w) {
  const zona = document.getElementById('print-zone')
  if (!zona) return
  zona.innerHTML = PRINT_STYLES + htmlWorker(w, fechaDia.value)
  window.print()
}
function imprimirSeleccionados() {
  const lista = dataDia.value.workers.filter(w => selectedWorkers.value.has(w.worker_id))
  if (!lista.length) return
  const zona = document.getElementById('print-zone')
  if (!zona) return
  zona.innerHTML = PRINT_STYLES + lista.map(w => htmlWorker(w, fechaDia.value)).join('')
  window.print()
}
function imprimirTodos() {
  const lista = dataDia.value.workers
  if (!lista.length) return
  const zona = document.getElementById('print-zone')
  if (!zona) return
  zona.innerHTML = PRINT_STYLES + lista.map(w => htmlWorker(w, fechaDia.value)).join('')
  window.print()
}
function imprimirHistLiq(liq) {
  const zona = document.getElementById('print-zone')
  if (!zona) return
  zona.innerHTML = PRINT_STYLES + `
    <div class="p-header">
      <h2>${companyNombre.value}</h2>
      <h3>LIQUIDACIÓN DE OPERARIO</h3>
      <p>Fecha: <strong>${liq.fecha_inicio}</strong> &nbsp;|&nbsp; Impreso: ${new Date().toLocaleString('es-CO')}</p>
    </div>
    <div class="p-worker">
      <strong>${liq.worker_nombre}</strong> &nbsp;|&nbsp; ${liq.profesion}
    </div>
    <table class="p-table">
      <thead><tr><th>Detalle</th><th>Total Bruto</th><th>Pagado</th><th>Forma</th><th>Registró</th></tr></thead>
      <tbody><tr>
        <td>${liq.observaciones || 'Pago de mano de obra'}</td>
        <td style="text-align:right">${fmt(liq.total_bruto)}</td>
        <td style="text-align:right;font-weight:bold">${fmt(liq.monto_operario)}</td>
        <td>${formaLabel(liq.forma_pago)}</td>
        <td>${liq.registrado_por || ''}</td>
      </tr></tbody>
    </table>
    <div class="p-firma">
      <div>Firma del operario: ___________________________</div>
    </div>`
  window.print()
}
function imprimirVentas(modo) {
  const zona = document.getElementById('print-zone')
  if (!zona) return
  const periodo = vtaIni.value === vtaFin.value ? vtaIni.value : `${vtaIni.value} al ${vtaFin.value}`
  let html = PRINT_STYLES + `
    <div class="p-header">
      <h2>${companyNombre.value}</h2>
      <h3>RESUMEN DE VENTAS</h3>
      <p>Período: <strong>${periodo}</strong> &nbsp;|&nbsp; Órdenes: ${dataVentas.value.num_ordenes}</p>
    </div>`

  if (modo !== 'productos' && dataVentas.value.servicios.length > 0) {
    const rows = dataVentas.value.servicios.map(s => `
      <tr><td>${s.nombre}</td><td>${tipoLabel(s.tipo_item)}</td>
          <td style="text-align:center">${s.cantidad}</td>
          <td style="text-align:right">${fmt(s.total)}</td>
          <td style="text-align:right">${fmt(s.total_mano_obra)}</td></tr>`).join('')
    html += `<h4>SERVICIOS</h4>
      <table class="p-table">
        <thead><tr><th>Servicio</th><th>Tipo</th><th>Cant.</th><th>Total</th><th>M. Obra</th></tr></thead>
        <tbody>${rows}</tbody>
        <tfoot><tr><td colspan="3" style="text-align:right;font-weight:bold">Total servicios:</td>
          <td style="text-align:right;font-weight:bold">${fmt(dataVentas.value.total_servicios)}</td><td></td></tr></tfoot>
      </table>`
  }
  if (modo !== 'servicios' && dataVentas.value.productos.length > 0) {
    const rows = dataVentas.value.productos.map(p => `
      <tr><td>${p.nombre}</td><td style="text-align:center">${p.cantidad}</td>
          <td style="text-align:right;font-weight:bold">${fmt(p.total)}</td></tr>`).join('')
    html += `<h4>REPUESTOS / PRODUCTOS</h4>
      <table class="p-table">
        <thead><tr><th>Producto</th><th>Cant.</th><th>Total</th></tr></thead>
        <tbody>${rows}</tbody>
        <tfoot><tr><td colspan="2" style="text-align:right;font-weight:bold">Total repuestos:</td>
          <td style="text-align:right;font-weight:bold">${fmt(dataVentas.value.total_productos)}</td></tr></tfoot>
      </table>`
  }
  html += `<div class="p-total-final">TOTAL VENTA: ${fmt(dataVentas.value.total_venta)}</div>`
  zona.innerHTML = html
  window.print()
}

const PRINT_STYLES = `<style>
  body { font-family: Arial, sans-serif; font-size: 12px; color: #000; }
  .p-header { text-align: center; margin-bottom: 12px; border-bottom: 2px solid #000; padding-bottom: 8px; }
  .p-header h2 { font-size: 16px; margin: 0; }
  .p-header h3 { font-size: 13px; margin: 2px 0; }
  .p-header p  { font-size: 11px; margin: 2px 0; }
  .p-worker    { font-size: 13px; margin: 8px 0; padding: 6px; background: #f0f0f0; }
  .p-table     { width: 100%; border-collapse: collapse; margin: 8px 0; }
  .p-table th  { background: #333; color: #fff; padding: 4px 6px; text-align: left; font-size: 11px; }
  .p-table td  { padding: 4px 6px; border-bottom: 1px solid #ddd; font-size: 11px; }
  .p-table tfoot td { background: #f5f5f5; font-weight: bold; }
  .p-firma     { display: flex; justify-content: space-between; margin-top: 20px; gap: 20px; }
  .p-firma div { flex: 1; border-top: 1px solid #000; padding-top: 4px; font-size: 11px; }
  .p-separator { border-bottom: 2px dashed #aaa; margin: 20px 0; page-break-after: always; }
  .p-total-final { font-size: 16px; font-weight: bold; text-align: right; margin-top: 12px;
                   padding: 8px; border: 2px solid #000; }
  h4 { font-size: 13px; margin: 12px 0 4px; }
</style>`

onMounted(cargarDia)
</script>

<style scoped>
.liq-page { padding: 16px; max-width: 1100px; margin: 0 auto; }

/* ── Tabs ─────────────────────────────────────────────────────────────── */
.liq-nav {
  display: flex; gap: 4px; margin-bottom: 20px;
  background: #f1f5f9; border-radius: 12px; padding: 4px; overflow-x: auto;
}
.liq-tab {
  display: flex; align-items: center; gap: 6px; padding: 9px 16px;
  border: none; background: none; border-radius: 9px; cursor: pointer;
  font-size: 13px; font-weight: 600; color: #64748b; white-space: nowrap;
  transition: all .15s;
}
.liq-tab:hover  { background: #e2e8f0; color: #334155; }
.liq-tab.active { background: #fff; color: #1d4ed8; box-shadow: 0 1px 4px rgba(0,0,0,.1); }
.liq-tab .bi    { font-size: 14px; }

/* ── KPI Bar ──────────────────────────────────────────────────────────── */
.kpi-bar {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 12px; margin-bottom: 18px;
}
.kpi-card {
  border-radius: 12px; padding: 14px 16px;
  display: flex; flex-direction: column; gap: 4px;
}
.kpi-val  { font-size: 20px; font-weight: 800; color: #1e293b; }
.kpi-lbl  { font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; }
.kpi-blue   { background: #eff6ff; border: 1.5px solid #bfdbfe; }
.kpi-green  { background: #f0fdf4; border: 1.5px solid #bbf7d0; }
.kpi-amber  { background: #fffbeb; border: 1.5px solid #fde68a; }
.kpi-violet { background: #f5f3ff; border: 1.5px solid #ddd6fe; }

/* ── Fecha bar ────────────────────────────────────────────────────────── */
.fecha-bar {
  display: flex; align-items: center; gap: 10px; margin-bottom: 16px;
  background: #f8fafc; border-radius: 10px; padding: 10px 14px;
  border: 1.5px solid #e2e8f0;
}
.fb-label { font-size: 13px; font-weight: 600; color: #334155; display: flex; align-items: center; gap: 6px; white-space: nowrap; }
.fb-picker { flex: 1; max-width: 180px; }
.btn-hoy   { padding: 6px 12px; border: 1.5px solid #3b82f6; background: #eff6ff; color: #1d4ed8; border-radius: 7px; font-size: 12px; font-weight: 600; cursor: pointer; }
.btn-hoy:hover { background: #3b82f6; color: #fff; }

/* ── Workers toolbar ──────────────────────────────────────────────────── */
.workers-toolbar {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 12px; gap: 10px; flex-wrap: wrap;
}
.chk-all { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 600; color: #374151; cursor: pointer; }
.chk-all input { width: 16px; height: 16px; cursor: pointer; }
.wt-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.btn-act-print {
  display: flex; align-items: center; gap: 6px; padding: 8px 14px;
  border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; border: 1.5px solid #3b82f6;
  background: #eff6ff; color: #1d4ed8; transition: all .12s;
}
.btn-act-print.all { border-color: #10b981; background: #f0fdf4; color: #059669; }
.btn-act-print:hover:not(:disabled)     { background: #3b82f6; color: #fff; }
.btn-act-print.all:hover:not(:disabled) { background: #10b981; color: #fff; }
.btn-act-print:disabled { opacity: .45; cursor: not-allowed; }

/* ── Worker cards ─────────────────────────────────────────────────────── */
.workers-list { display: flex; flex-direction: column; gap: 10px; }
.worker-card {
  border-radius: 12px; border: 1.5px solid #e2e8f0;
  background: #fff; overflow: hidden;
  box-shadow: 0 1px 4px rgba(0,0,0,.05);
  transition: box-shadow .15s;
}
.worker-card:hover { box-shadow: 0 3px 12px rgba(0,0,0,.08); }

.wc-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 16px; gap: 12px; flex-wrap: wrap;
}
.wc-left  { display: flex; align-items: center; gap: 10px; flex: 1; min-width: 0; }
.wc-chk   { width: 16px; height: 16px; cursor: pointer; flex-shrink: 0; }
.wc-avatar {
  width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center;
  justify-content: center; color: #fff; font-weight: 700; font-size: 14px; flex-shrink: 0;
}
.wc-info    { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.wc-nombre  { font-size: 14px; font-weight: 700; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.wc-prof    { font-size: 12px; color: #64748b; }
.wc-right   { display: flex; align-items: center; gap: 14px; flex-shrink: 0; }
.wc-stats   { display: flex; flex-direction: column; gap: 3px; }
.stat       { font-size: 11px; color: #94a3b8; display: flex; align-items: center; gap: 4px; }
.wc-total   { font-size: 18px; font-weight: 800; color: #059669; min-width: 110px; text-align: right; }
.wc-btns    { display: flex; gap: 5px; }
.wc-btn {
  width: 34px; height: 34px; border-radius: 8px; border: 1.5px solid #e2e8f0;
  background: #f8fafc; cursor: pointer; display: flex; align-items: center;
  justify-content: center; font-size: 13px; color: #64748b; transition: all .12s;
}
.wc-btn.expand:hover { background: #eff6ff; color: #1d4ed8; border-color: #bfdbfe; }
.wc-btn.print:hover  { background: #f0fdf4; color: #059669; border-color: #bbf7d0; }
.wc-btn.pagar:hover  { background: #fffbeb; color: #d97706; border-color: #fde68a; }

/* ── Detalle tabla ────────────────────────────────────────────────────── */
.wc-detail { border-top: 1.5px solid #f1f5f9; padding: 0 8px 12px; overflow-x: auto; }
.det-table {
  width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 8px;
}
.det-table th  { background: #f8fafc; color: #64748b; font-size: 11px; font-weight: 700; padding: 6px 10px; text-align: left; border-bottom: 1.5px solid #e2e8f0; text-transform: uppercase; letter-spacing: .4px; }
.det-table td  { padding: 7px 10px; border-bottom: 1px solid #f1f5f9; color: #374151; }
.det-table tfoot td { background: #f8fafc; font-weight: 700; border-top: 2px solid #e2e8f0; }

/* ── Historial ────────────────────────────────────────────────────────── */
.hist-table-wrap { overflow-x: auto; }
.hist-table      { width: 100%; border-collapse: collapse; font-size: 13px; }
.hist-table th   { background: #1e3a5f; color: #fff; padding: 10px 12px; text-align: left; font-size: 11px; font-weight: 700; text-transform: uppercase; }
.hist-table td   { padding: 9px 12px; border-bottom: 1px solid #f1f5f9; }
.hist-table tr:hover td { background: #f8fafc; }

/* ── Ventas ───────────────────────────────────────────────────────────── */
.ventas-actions { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
.btn-print-ventas {
  display: flex; align-items: center; gap: 6px; padding: 8px 14px;
  border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer;
  border: 1.5px solid #6366f1; background: #eef2ff; color: #4338ca;
}
.btn-print-ventas.all { border-color: #10b981; background: #f0fdf4; color: #059669; }
.btn-print-ventas:hover     { background: #6366f1; color: #fff; }
.btn-print-ventas.all:hover { background: #10b981; color: #fff; }

.venta-section { margin-bottom: 20px; border-radius: 12px; border: 1.5px solid #e2e8f0; overflow: hidden; }
.vs-header     { display: flex; align-items: center; gap: 8px; padding: 12px 16px; background: #f8fafc; font-weight: 700; color: #1e293b; font-size: 14px; border-bottom: 1.5px solid #e2e8f0; }
.vs-total      { margin-left: auto; font-size: 16px; color: #059669; }
.venta-table   { width: 100%; border-collapse: collapse; font-size: 13px; }
.venta-table th  { background: #f1f5f9; color: #475569; font-size: 11px; font-weight: 700; padding: 8px 12px; text-transform: uppercase; }
.venta-table td  { padding: 8px 12px; border-bottom: 1px solid #f1f5f9; }
.venta-table tfoot td { background: #f8fafc; border-top: 2px solid #e2e8f0; }

/* ── Filtros comunes ──────────────────────────────────────────────────── */
.filtros-bar {
  display: flex; align-items: flex-end; gap: 12px; flex-wrap: wrap;
  margin-bottom: 16px; background: #f8fafc; border-radius: 10px;
  padding: 12px 16px; border: 1.5px solid #e2e8f0;
}
.filtros-group { display: flex; flex-direction: column; gap: 4px; }
.filtros-group label { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; }
.f-picker { min-width: 140px; }
.btn-buscar {
  display: flex; align-items: center; gap: 6px; padding: 9px 18px;
  background: #1d4ed8; color: #fff; border: none; border-radius: 8px;
  font-size: 13px; font-weight: 600; cursor: pointer;
}
.btn-buscar:hover:not(:disabled) { background: #1e40af; }
.btn-buscar:disabled { opacity: .5; cursor: not-allowed; }
.btn-stock {
  display: flex; align-items: center; gap: 6px; padding: 9px 14px;
  background: #f0fdf4; border: 1.5px solid #bbf7d0; color: #059669;
  border-radius: 8px; font-size: 13px; font-weight: 600; text-decoration: none;
}
.btn-stock:hover { background: #dcfce7; }

/* ── Shared misc ──────────────────────────────────────────────────────── */
.tipo-badge  { font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 20px; }
.t-mecanica  { background: #dbeafe; color: #1d4ed8; }
.t-lavado    { background: #cffafe; color: #0e7490; }
.t-latoneria { background: #fef3c7; color: #92400e; }
.t-pintura   { background: #ede9fe; color: #6d28d9; }
.t-repuesto  { background: #f1f5f9; color: #475569; }
.prof-badge  { font-size: 11px; background: #f1f5f9; color: #475569; padding: 2px 7px; border-radius: 20px; }
.forma-badge { font-size: 11px; padding: 2px 7px; border-radius: 20px; font-weight: 600; }
.fp-efectivo     { background: #dcfce7; color: #166534; }
.fp-transferencia{ background: #eff6ff; color: #1d4ed8; }
.fp-otro         { background: #f1f5f9; color: #475569; }
.placa-badge { font-weight: 800; font-size: 12px; letter-spacing: 1px; color: #1e293b; }
.mono        { font-family: monospace; font-size: 12px; color: #64748b; }
.ta-r  { text-align: right; }
.ta-c  { text-align: center; }
.fw-bold { font-weight: 700; }
.text-green  { color: #059669; }
.text-amber  { color: #d97706; }
.small-txt   { font-size: 11px; color: #64748b; }
.tbl-btn {
  width: 28px; height: 28px; border-radius: 6px; border: 1.5px solid #e2e8f0;
  background: #fff; cursor: pointer; color: #64748b; font-size: 12px;
  display: flex; align-items: center; justify-content: center;
}
.tbl-btn:hover { background: #f0fdf4; color: #059669; border-color: #bbf7d0; }

.loading-state { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 50px; color: #94a3b8; font-size: 14px; }
.empty-state   { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 50px; color: #94a3b8; text-align: center; }
.empty-state .bi { font-size: 40px; color: #e2e8f0; }
.empty-state p   { font-size: 13px; margin: 0; }

.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from{ transform: rotate(0deg) } to{ transform: rotate(360deg) } }

/* ── Modal ────────────────────────────────────────────────────────────── */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.5); display: flex; align-items: center; justify-content: center; z-index: 3000; padding: 16px; }
.modal-box     { background: #fff; border-radius: 16px; width: 100%; max-width: 440px; box-shadow: 0 24px 60px rgba(0,0,0,.2); overflow: hidden; }
.mb-head       { display: flex; align-items: flex-start; justify-content: space-between; padding: 18px 20px; border-bottom: 1px solid #f1f5f9; }
.mb-head h4    { font-size: 15px; font-weight: 700; margin: 0; color: #1e293b; display: flex; align-items: center; gap: 7px; }
.mb-sub        { font-size: 12px; color: #64748b; margin: 3px 0 0; }
.btn-x         { background: none; border: none; font-size: 17px; cursor: pointer; color: #94a3b8; }
.mb-body       { padding: 18px 20px; display: flex; flex-direction: column; gap: 14px; }
.mb-monto      { display: flex; align-items: center; justify-content: space-between; background: #f0fdf4; border-radius: 10px; padding: 12px 16px; border: 1.5px solid #bbf7d0; }
.lbl-monto     { font-size: 12px; font-weight: 600; color: #64748b; }
.val-monto     { font-size: 22px; font-weight: 800; color: #059669; }
.mb-row        { display: flex; flex-direction: column; gap: 6px; }
.mb-row label  { font-size: 12px; font-weight: 600; color: #374151; }
.mb-sel, .mb-inp {
  padding: 9px 12px; border: 1.5px solid #e2e8f0; border-radius: 8px; font-size: 13px; background: #fff; outline: none;
}
.mb-sel:focus, .mb-inp:focus { border-color: #3b82f6; }
.mb-footer     { display: flex; justify-content: flex-end; gap: 8px; padding: 14px 20px; border-top: 1px solid #f1f5f9; }
.btn-cancel    { padding: 9px 18px; border: 1.5px solid #e2e8f0; background: #fff; color: #64748b; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; }
.btn-confirmar {
  display: flex; align-items: center; gap: 6px; padding: 9px 18px;
  background: #059669; color: #fff; border: none; border-radius: 8px;
  font-size: 13px; font-weight: 600; cursor: pointer;
}
.btn-confirmar:hover:not(:disabled) { background: #047857; }
.btn-confirmar:disabled { opacity: .6; cursor: not-allowed; }

/* ── Responsive 768px ─────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .kpi-bar   { grid-template-columns: repeat(2, 1fr); }
  .liq-tab span { display: none; }
  .liq-tab .bi  { font-size: 18px; }
  .wc-head   { flex-direction: column; align-items: flex-start; }
  .wc-right  { width: 100%; justify-content: space-between; }
  .wc-total  { min-width: unset; }
  .hist-table th:nth-child(8), .hist-table td:nth-child(8) { display: none; }
}

/* ── Responsive 576px ─────────────────────────────────────────────────── */
@media (max-width: 576px) {
  .kpi-bar    { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .kpi-val    { font-size: 16px; }
  .fecha-bar  { flex-direction: column; align-items: stretch; }
  .fb-picker  { max-width: 100%; }
  .filtros-bar { flex-direction: column; align-items: stretch; }
  .wt-actions  { flex-direction: column; }
  .btn-act-print { justify-content: center; }
  .wc-stats   { flex-direction: row; gap: 10px; }
  .det-table th:nth-child(1), .det-table td:nth-child(1),
  .det-table th:nth-child(2), .det-table td:nth-child(2) { display: none; }
  .hist-table th:nth-child(4), .hist-table td:nth-child(4),
  .hist-table th:nth-child(5), .hist-table td:nth-child(5) { display: none; }
  .ventas-actions { flex-direction: column; }
}

/* ── Print (solo zona de impresión visible) ───────────────────────────── */
@media print {
  .liq-page    { display: none !important; }
  #print-zone  { display: block !important; }
}
</style>
