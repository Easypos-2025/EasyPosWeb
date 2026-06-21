<template>
  <div class="dashboard-content">

    <!-- KPI BAR -->
    <KpiStrip :kpis="kpis" :loading="kpiLoading" :showLabels="true" v-model="fechaKpi" />

    <!-- CABECERA -->
    <div class="dash-header">
      <h6 class="dash-title">{{ companyStore.selectedCompany?.name || 'Panel de Operaciones' }}</h6>
      <div class="dash-header-right">
        <a
          :href="tvUrl" target="_blank"
          class="btn-tv"
          :class="{ 'btn-tv--disabled': !tvToken }"
          title="Abrir Pedidos TV en pantalla"
        >
          <i class="bi bi-display me-1"></i>
          <span class="btn-tv-label">Ver Pedidos TV</span>
        </a>
        <button class="btn-tv-icon" @click="copiarUrlTV" :disabled="!tvToken"
          :title="urlCopiada ? '¡URL copiada!' : 'Copiar URL para el TV'">
          <i class="bi" :class="urlCopiada ? 'bi-clipboard-check-fill' : 'bi-clipboard'"></i>
        </button>
        <button class="btn-tv-icon btn-tv-icon--regen" @click="regenerarUrlTV" :disabled="!tvToken"
          title="Regenerar URL del TV (invalida la anterior)">
          <i class="bi bi-arrow-repeat"></i>
        </button>
        <button class="btn-refresh" @click="cargarTodo" :disabled="cargandoTodo" title="Actualizar">
          <i class="bi" :class="cargandoTodo ? 'bi-arrow-repeat spin' : 'bi-arrow-clockwise'"></i>
        </button>
      </div>
    </div>

    <!-- BARRA DE ACCIONES -->
    <div class="action-bar">
      <button class="action-btn action-btn--primary" @click="abrirWizard">
        <i class="bi bi-plus-circle-fill"></i>
        <span>Nuevo Pedido</span>
      </button>
      <button class="action-btn action-btn--llevar" @click="abrirWizardTakeout">
        <i class="bi bi-bag-check"></i>
        <span>Para Llevar</span>
      </button>
      <button class="action-btn action-btn--stock" @click="abrirModalStock">
        <i class="bi bi-exclamation-triangle"></i>
        <span>Stock</span>
        <span v-if="stockAlertas.length" class="action-btn__badge">{{ stockAlertas.length }}</span>
      </button>
      <button class="action-btn action-btn--tv" @click="abrirModalTV">
        <i class="bi bi-tv"></i>
        <span>Pedidos TV</span>
        <span v-if="pedidosTV.length" class="action-btn__badge action-btn__badge--tv">{{ pedidosTV.length }}</span>
      </button>
    </div>

    <!-- MESAS ABIERTAS -->
    <div class="mesas-section">
      <div class="wm-icon" aria-hidden="true"><i class="bi bi-basket"></i></div>
      <div v-if="mesasLoading" class="estado-carga">
        <div class="spinner-border spinner-border-sm text-primary"></div>
        <span>Cargando cuentas...</span>
      </div>
      <template v-else>
        <div v-if="!mesasOcupadas.length" class="estado-vacio">
          <i class="bi bi-check-circle"></i>
          <p>No hay cuentas abiertas en este momento.</p>
        </div>
        <div v-else class="mesas-grid">
          <MesaTableCard
            v-for="mesa in mesasOcupadasOrdenadas"
            :key="mesa.id"
            :mesa="mesa"
            @click="irAMesaExistente(mesa)"
            @eliminar="eliminarOrden(mesa)"
          />
        </div>
      </template>
    </div>

    <!-- ══ MODAL STOCK ══ -->
    <div class="modal-overlay" v-if="showStockModal" @click.self="showStockModal = false">
      <div class="modal-panel">
        <div class="modal-panel__header">
          <span><i class="bi bi-exclamation-triangle me-2 text-danger"></i>Stock Crítico</span>
          <button class="modal-close" @click="showStockModal = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-panel__body">
          <div v-if="cargandoStock" class="modal-loading">
            <div class="spinner-border spinner-border-sm text-danger"></div>
          </div>
          <div v-else-if="!stockAlertas.length" class="modal-empty">
            <i class="bi bi-check-circle-fill text-success me-2"></i>
            Todo el stock está en orden
          </div>
          <div v-else class="stock-table-wrap">
            <table class="stock-table">
              <thead>
                <tr>
                  <th>Insumo</th>
                  <th class="text-end">Stock actual</th>
                  <th class="text-end">Stock mín.</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in stockAlertas" :key="item.id">
                  <td>
                    <div class="si-name">{{ item.name }}</div>
                    <div class="si-unit">{{ item.unit_name }}</div>
                  </td>
                  <td class="text-end">
                    <span :class="item.stock_qty <= 0 ? 'text-danger fw-bold' : 'text-warning fw-bold'">
                      {{ formatNum(item.stock_qty) }}
                    </span>
                  </td>
                  <td class="text-end text-muted small">{{ formatNum(item.min_stock) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- ══ MODAL PEDIDOS TV ══ -->
    <div class="modal-overlay" v-if="showTVModal" @click.self="showTVModal = false">
      <div class="modal-panel">
        <div class="modal-panel__header">
          <span><i class="bi bi-tv me-2"></i>Pedidos en Cocina TV</span>
          <button class="modal-close" @click="showTVModal = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-panel__body">
          <div v-if="cargandoTV" class="modal-loading">
            <div class="spinner-border spinner-border-sm text-primary"></div>
          </div>
          <div v-else-if="!pedidosTV.length" class="modal-empty">
            <i class="bi bi-check-circle-fill text-success me-2"></i>
            No hay pedidos en pantalla de cocina
          </div>
          <div v-else class="tv-list">
            <div v-for="p in pedidosTV" :key="p.order_number" class="tv-card">
              <div class="tv-card__top">
                <span class="tv-card__mesa"><i class="bi bi-table me-1"></i>{{ p.table_name || 'Sin mesa' }}</span>
                <span class="tv-card__hora">{{ p.order_time }}</span>
              </div>
              <div class="tv-card__mid">
                <span class="tv-card__mesero"><i class="bi bi-person me-1"></i>{{ p.waiter_name || '—' }}</span>
                <span class="tv-card__items"><i class="bi bi-list-ul me-1"></i>{{ p.item_count }} ítem(s)</span>
              </div>
              <div v-if="p.items_preview" class="tv-card__preview">{{ p.items_preview }}</div>
              <div class="tv-card__bot">
                <span class="tv-card__monto">{{ fmt(p.amount) }}</span>
                <button class="btn-ya-salio" @click="despacharPedido(p)" :disabled="p.despachando">
                  <span v-if="p.despachando" class="spinner-border spinner-border-sm me-1"></span>
                  <i v-else class="bi bi-check2-circle me-1"></i>
                  Ya salió
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- WIZARD: NUEVO PEDIDO -->
    <div v-if="wizard.visible" class="wizard-overlay" @click.self="cerrarWizard">
      <div class="wizard-modal">
        <div class="wizard-header">
          <div class="wizard-steps">
            <span class="wstep" :class="{ active: wizard.step === 1, done: wizard.step > 1 }">
              <i class="bi bi-person-fill"></i>
              <span v-if="wizard.step > 1 && wizard.waiterId !== null">
                {{ meseros.find(m => m.id === wizard.waiterId)?.name || 'Sin asignar' }}
              </span>
              <span v-else>Mesero</span>
            </span>
            <span class="wstep-sep"></span>
            <span class="wstep" :class="{ active: wizard.step === 2 }">
              <i class="bi bi-geo-alt-fill"></i>
              <span>Mesa</span>
            </span>
          </div>
          <button class="wizard-close" @click="cerrarWizard"><i class="bi bi-x-lg"></i></button>
        </div>

        <div v-if="wizard.step === 1" class="wizard-body">
          <h6 class="wizard-section-title">¿Quién atiende la mesa?</h6>
          <div class="meseros-grid">
            <button class="mesero-card" :class="{ 'mesero-card--selected': wizard.waiterId === 0 }" @click="seleccionarMesero(0)">
              <div class="mesero-avatar mesero-avatar--none"><i class="bi bi-person-dash"></i></div>
              <span class="mesero-name">Sin asignar</span>
            </button>
            <button v-for="m in meseros" :key="m.id" class="mesero-card" :class="{ 'mesero-card--selected': wizard.waiterId === m.id }" @click="seleccionarMesero(m.id)">
              <div class="mesero-avatar">{{ m.name.charAt(0).toUpperCase() }}</div>
              <span class="mesero-name">{{ m.name }}</span>
            </button>
            <button class="mesero-card mesero-card--add" @click="wizard.showAddWaiter = !wizard.showAddWaiter">
              <div class="mesero-avatar mesero-avatar--add"><i class="bi bi-plus-lg"></i></div>
              <span class="mesero-name">Agregar</span>
            </button>
          </div>
          <div v-if="wizard.showAddWaiter" class="add-waiter-form">
            <div class="aw-row">
              <input v-model="newWaiter.name" class="campo-input" placeholder="Nombre del mesero" maxlength="80" />
              <input v-model="newWaiter.pin" class="campo-input" placeholder="PIN (4 dígitos)" maxlength="4" type="password" />
              <button class="btn-aw-save" @click="guardarNuevoMesero" :disabled="newWaiter.saving">
                <span v-if="newWaiter.saving"><div class="spinner-border spinner-border-sm"></div></span>
                <span v-else><i class="bi bi-check-lg"></i></span>
              </button>
            </div>
            <p v-if="newWaiter.error" class="text-danger small mt-1">{{ newWaiter.error }}</p>
          </div>
          <div class="wizard-footer">
            <button class="btn-cancelar" @click="cerrarWizard">Cancelar</button>
          </div>
        </div>

        <div v-if="wizard.step === 2" class="wizard-body">
          <h6 class="wizard-section-title">Selecciona la mesa</h6>
          <div v-if="mesasLoading" class="estado-carga">
            <div class="spinner-border spinner-border-sm text-primary"></div>
            <span>Cargando mesas...</span>
          </div>
          <div v-else-if="!mesas.length" class="estado-vacio">
            <i class="bi bi-grid-3x3-gap"></i>
            <p>No hay mesas configuradas.</p>
          </div>
          <div v-else class="zonas-acordeon">
            <div v-for="zona in zonas" :key="zona.id" class="zona-acordeon">
              <button class="zona-acordeon__header" :class="{ 'zona-acordeon__header--open': wizard.zonaAbierta === zona.id }" @click="wizard.zonaAbierta = wizard.zonaAbierta === zona.id ? null : zona.id">
                <span><i class="bi bi-geo-alt-fill me-2"></i>{{ zona.name }}<span class="zona-count">{{ mesasPorZona(zona.id).length }}</span></span>
                <i class="bi" :class="wizard.zonaAbierta === zona.id ? 'bi-chevron-up' : 'bi-chevron-down'"></i>
              </button>
              <div v-show="wizard.zonaAbierta === zona.id" class="zona-acordeon__body">
                <div class="mesas-grid-wizard">
                  <button v-for="mesa in mesasPorZona(zona.id)" :key="mesa.id" class="mesa-wizard-card" :class="{ 'mesa-wizard-card--libre': !mesa.ocupada, 'mesa-wizard-card--ocupada': mesa.ocupada }" :disabled="mesa.ocupada || wizard.abriendo" @click="irAComanda(mesa.id, mesa.name, wizard.waiterId ?? 0)">
                    <div class="mwc-status-bar"></div>
                    <i class="bi mwc-icon" :class="mesa.ocupada ? 'bi-person-fill' : 'bi-table'"></i>
                    <span class="mwc-name">{{ mesa.name }}</span>
                    <span class="mwc-info">
                      <span v-if="mesa.ocupada" class="mwc-badge">Ocupada</span>
                      <span v-else class="mwc-seats">{{ mesa.seats }} sillas</span>
                    </span>
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div class="wizard-footer">
            <button class="btn-cancelar" @click="wizard.step = 1" :disabled="wizard.abriendo"><i class="bi bi-arrow-left me-1"></i>Volver</button>
            <div v-if="wizard.abriendo" class="wizard-opening-hint">
              <div class="spinner-border spinner-border-sm text-primary me-2"></div>Abriendo mesa...
            </div>
          </div>
        </div>

        <div v-if="wizard.abriendo" class="wizard-loading-overlay">
          <div class="spinner-border text-primary"></div>
          <span>Abriendo mesa...</span>
        </div>
      </div>
    </div>

    <ComandaOrderDetailModal v-if="detailMesa" :table="detailMesa" @close="detailMesa = null" @cancelled="onMesaCancelled" />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import KpiStrip from '@/components/dashboard/KpiStrip.vue'
import api from '@/services/apis.js'
import apiComanda from '@/services/apiComanda.js'
import { useCompanyStore } from '@/stores/companyStore.js'
import ComandaOrderDetailModal from '@/components/comanda/ComandaOrderDetailModal.vue'
import MesaTableCard from '@/components/comanda/MesaTableCard.vue'
import { showToast } from '@/utils/toast'

const companyStore = useCompanyStore()
const router = useRouter()
const hoy = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Bogota' }).format(new Date())

const fechaKpi     = ref(hoy)
const cargandoTodo = ref(false)
const kpiLoading   = ref(true)
const mesasLoading = ref(true)
const detailMesa   = ref(null)
const cargandoStock = ref(false)
const cargandoTV   = ref(false)
const kpiData      = ref(null)
const mesas        = ref([])
const meseros      = ref([])
const stockAlertas = ref([])
const pedidosTV    = ref([])
const showStockModal = ref(false)
const showTVModal    = ref(false)

const wizard = ref({ visible: false, step: 1, waiterId: null, zonaAbierta: null, abriendo: false, showAddWaiter: false, takeout: false })
const newWaiter = ref({ name: '', pin: '', saving: false, error: '' })

const fmtCOP = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0, maximumFractionDigits: 0 })
const fmt = (v) => fmtCOP.format(v || 0)
function formatNum(val) { return Number(val || 0).toLocaleString('es-CO', { maximumFractionDigits: 2 }) }

const kpis = computed(() => {
  const d = kpiData.value
  if (!d) return [
    { icon: 'bi-receipt-cutoff', label: 'Ventas Facturas',   value: '—' },
    { icon: 'bi-journal-text',   label: 'Ventas Recibos',    value: '—' },
    { icon: 'bi-graph-up-arrow', label: 'Total Fact+Rec',    value: '—' },
    { icon: 'bi-table',          label: 'Comandas Abiertas', value: '—' },
    { icon: 'bi-globe',          label: 'Plataforma',        value: '—' },
  ]
  const totalFactRec = d.ventas_facturas.total + d.ventas_recibos.total
  const countFactRec = d.ventas_facturas.count + d.ventas_recibos.count
  return [
    { icon: 'bi-receipt-cutoff', label: `Facturas (${d.ventas_facturas.count})`,   value: fmt(d.ventas_facturas.total) },
    { icon: 'bi-journal-text',   label: `Recibos (${d.ventas_recibos.count})`,     value: fmt(d.ventas_recibos.total) },
    { icon: 'bi-graph-up-arrow', label: `Total (${countFactRec})`,                 value: fmt(totalFactRec) },
    { icon: 'bi-table',          label: `Abiertas (${d.comandas_abiertas.count})`, value: fmt(d.comandas_abiertas.total) },
    { icon: 'bi-globe',          label: `Domicilio (${d.plataforma.count})`,       value: fmt(d.plataforma.total) },
  ]
})

const selectedCid = computed(() => companyStore.selectedCompany?.id || undefined)
const tvToken    = ref('')
const urlCopiada = ref(false)
const tvUrl = computed(() => tvToken.value ? `${window.location.origin}/pos/cocina?token=${tvToken.value}` : '#')

async function cargarTvToken() {
  try {
    const cid = selectedCid.value
    const { data } = await api.get('/api/pos/comanda/cocina/tv-config', { headers: cid ? { 'X-Company-Id': String(cid) } : {} })
    tvToken.value = data.token || ''
  } catch { }
}

async function copiarUrlTV() {
  if (!tvUrl.value || tvUrl.value === '#') return
  try { await navigator.clipboard.writeText(tvUrl.value) }
  catch {
    const el = document.createElement('textarea'); el.value = tvUrl.value
    document.body.appendChild(el); el.select(); document.execCommand('copy'); document.body.removeChild(el)
  }
  urlCopiada.value = true
  setTimeout(() => { urlCopiada.value = false }, 2500)
}

async function regenerarUrlTV() {
  const { isConfirmed } = await window.Swal.fire({ title: 'Regenerar URL del TV', text: 'La URL actual dejará de funcionar. ¿Continuar?', icon: 'warning', showCancelButton: true, confirmButtonText: 'Sí, regenerar', cancelButtonText: 'Cancelar', confirmButtonColor: '#dc2626' })
  if (!isConfirmed) return
  try {
    const cid = selectedCid.value
    const { data } = await api.post('/api/pos/comanda/cocina/tv-token/regenerar', {}, { headers: cid ? { 'X-Company-Id': String(cid) } : {} })
    tvToken.value = data.token || ''
    await window.Swal.fire({ title: 'URL regenerada', text: 'Copia la nueva URL y pégala en el TV.', icon: 'success', timer: 3000, showConfirmButton: false })
  } catch { }
}

const zonas = computed(() => {
  const seen = new Set(); const result = []
  for (const m of mesas.value) { const key = m.zone_id ?? ''; if (!seen.has(key)) { seen.add(key); result.push({ id: key, name: m.zone_name || 'Sin zona' }) } }
  return result
})
const mesasOcupadas = computed(() => mesas.value.filter(m => m.ocupada))
const mesasOcupadasOrdenadas = computed(() => [...mesasOcupadas.value].sort((a, b) => (a.daily_seq || 0) - (b.daily_seq || 0)))
const mesasPorZona = (zoneId) => mesas.value.filter(m => (m.zone_id ?? '') === zoneId)

async function _silentKpis() { try { const { data } = await api.get('/api/pos-dashboard/kpis', { params: { fecha: fechaKpi.value, company_id: selectedCid.value, _t: Date.now() } }); kpiData.value = data } catch { } }
async function _silentMesas() { try { const { data } = await api.get('/api/pos-dashboard/mesas', { params: { company_id: selectedCid.value, _t: Date.now() } }); mesas.value = data } catch { } }
async function _silentTV() {
  try {
    localStorage.setItem('waiter_company_id', String(selectedCid.value))
    const { data } = await apiComanda.get('/api/pos/comanda/cocina-pedidos')
    pedidosTV.value = showTVModal.value ? data.map(p => ({ ...p, despachando: false })) : data
  } catch { }
}

function _tick() { _silentKpis(); _silentMesas(); _silentTV() }
let _timer = null
function _startRefresh() { _stopRefresh(); _timer = setInterval(_tick, 15000) }
function _stopRefresh()  { if (_timer) { clearInterval(_timer); _timer = null } }
function _onVisible()    { if (!document.hidden) _tick() }

onMounted(async () => {
  await Promise.all([cargarKpis(), cargarMesas(), cargarMeseros(), cargarStock(), cargarTvToken(), _silentTV()])
  _startRefresh()
  document.addEventListener('visibilitychange', _onVisible)
})
onUnmounted(() => { _stopRefresh(); document.removeEventListener('visibilitychange', _onVisible) })
watch(fechaKpi, () => { cargarKpis() })

async function cargarTodo() { cargandoTodo.value = true; try { await Promise.all([cargarKpis(), cargarMesas(), cargarMeseros(), cargarStock()]) } finally { cargandoTodo.value = false } }

async function cargarKpis() {
  kpiLoading.value = true
  try { const { data } = await api.get('/api/pos-dashboard/kpis', { params: { fecha: fechaKpi.value, company_id: selectedCid.value } }); kpiData.value = data }
  catch { kpiData.value = null } finally { kpiLoading.value = false }
}
async function cargarMesas() {
  mesasLoading.value = true
  try { const { data } = await api.get('/api/pos-dashboard/mesas', { params: { company_id: selectedCid.value } }); mesas.value = data }
  catch { mesas.value = [] } finally { mesasLoading.value = false }
}
async function cargarMeseros() { try { const { data } = await api.get('/api/pos-dashboard/meseros', { params: { company_id: selectedCid.value } }); meseros.value = data } catch { meseros.value = [] } }
async function cargarStock() {
  cargandoStock.value = true
  try { const { data } = await api.get('/api/pos-dashboard/stock-alertas', { params: { company_id: selectedCid.value } }); stockAlertas.value = data }
  catch { stockAlertas.value = [] } finally { cargandoStock.value = false }
}
async function cargarPedidosTV() {
  cargandoTV.value = true
  try { localStorage.setItem('waiter_company_id', String(selectedCid.value)); const { data } = await apiComanda.get('/api/pos/comanda/cocina-pedidos'); pedidosTV.value = data.map(p => ({ ...p, despachando: false })) }
  catch { pedidosTV.value = [] } finally { cargandoTV.value = false }
}

function abrirModalStock() { showStockModal.value = true; cargarStock() }
function abrirModalTV()    { showTVModal.value = true; cargarPedidosTV() }

async function despacharPedido(pedido) {
  pedido.despachando = true
  try { localStorage.setItem('waiter_company_id', String(selectedCid.value)); await apiComanda.post('/api/pos/comanda/orden/despachar', { order_number: pedido.order_number, date: pedido.date }); pedidosTV.value = pedidosTV.value.filter(p => p.order_number !== pedido.order_number) }
  catch (e) { showToast(e?.response?.data?.detail || 'Error al despachar', 'error', 3000); pedido.despachando = false }
}

function irAMesaExistente(mesa) {
  localStorage.setItem('waiter_company_id', String(selectedCid.value))
  detailMesa.value = { id: mesa.id, name: mesa.name, status: 'occupied', order_number: mesa.order_number || null, amount: mesa.amount || 0, order_time: mesa.hora_apertura || null, waiter_name: mesa.waiter_name || '', waiter_id: 0, daily_seq: mesa.daily_seq || null }
}
function onMesaCancelled() { detailMesa.value = null; _silentMesas() }

function abrirWizard() {
  wizard.value = { visible: true, step: 1, waiterId: null, zonaAbierta: zonas.value[0]?.id ?? null, abriendo: false, showAddWaiter: false, takeout: false }
  newWaiter.value = { name: '', pin: '', saving: false, error: '' }
  cargarMesas(); cargarMeseros()
}
function seleccionarMesero(waiterId) { wizard.value.waiterId = waiterId; wizard.value.showAddWaiter = false; wizard.value.step = 2 }
function abrirWizardTakeout() { irAComanda(0, 'Para Llevar', 0) }
function cerrarWizard() { wizard.value.visible = false }

async function irAComanda(tableId, tableName, waiterId) {
  wizard.value.abriendo = true
  try {
    const waiterName = meseros.value.find(m => m.id === waiterId)?.name || 'Sin asignar'
    localStorage.setItem('waiter_company_id', String(selectedCid.value))
    localStorage.setItem('pedido_ctx', JSON.stringify({ table_id: tableId, table_name: tableName, waiter_id: waiterId || 0, waiter_name: waiterName, company_id: selectedCid.value }))
    const { data } = await apiComanda.post('/api/pos/comanda/mesa/abrir', { table_id: tableId, guests_count: 1, waiter_id: waiterId || 0 })
    localStorage.setItem('pedido_ctx', JSON.stringify({ table_id: tableId, table_name: tableName, waiter_id: waiterId || 0, waiter_name: waiterName, order_number: data.order_number, date: data.date, company_id: selectedCid.value }))
    cerrarWizard(); router.push(`/pos/comanda/pedido/${tableId}`)
  } catch (e) { showToast(e?.response?.data?.detail || 'Error al abrir la mesa', 'error', 3000) }
  finally { wizard.value.abriendo = false }
}

async function eliminarOrden(mesa) {
  const { isConfirmed } = await window.Swal.fire({ title: `¿Eliminar pedido de ${mesa.name}?`, html: `<div>Esta acción <strong>no se puede revertir</strong>.</div>`, icon: 'warning', showCancelButton: true, confirmButtonText: 'Sí, eliminar', cancelButtonText: 'Cancelar', confirmButtonColor: '#dc2626' })
  if (!isConfirmed) return
  try { localStorage.setItem('waiter_company_id', String(selectedCid.value)); await apiComanda.delete('/api/pos/comanda/mesa/cancelar', { data: { table_id: mesa.id } }); await cargarMesas() }
  catch (e) { window.Swal.fire('Error', e?.response?.data?.detail || 'No se pudo eliminar el pedido', 'error') }
}

async function guardarNuevoMesero() {
  if (!newWaiter.value.name.trim()) { newWaiter.value.error = 'El nombre es obligatorio'; return }
  if (newWaiter.value.pin.length < 4) { newWaiter.value.error = 'El PIN debe tener 4 dígitos'; return }
  newWaiter.value.saving = true; newWaiter.value.error = ''
  try {
    await api.post('/api/pos-dashboard/mesero', { name: newWaiter.value.name.trim(), pin: newWaiter.value.pin, company_id: selectedCid.value })
    await cargarMeseros(); newWaiter.value = { name: '', pin: '', saving: false, error: '' }; wizard.value.showAddWaiter = false
  } catch (e) { newWaiter.value.error = e?.response?.data?.detail || 'Error al guardar' }
  finally { newWaiter.value.saving = false }
}
</script>

<style scoped>
.dash-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; gap: 10px; }
.dash-title { font-weight: 700; font-size: 15px; color: #1e3a5f; margin: 0; }
.dash-header-right { display: flex; align-items: center; gap: 8px; }
.btn-tv { display: flex; align-items: center; padding: 6px 14px; border: 1.5px solid #0f172a; border-radius: 8px; background: #0f172a; color: #f1f5f9; font-size: 13px; font-weight: 600; text-decoration: none; transition: background .15s; white-space: nowrap; }
.btn-tv:hover { background: #1e293b; color: #fff; }
.btn-tv--disabled { opacity: .5; pointer-events: none; }
.btn-tv-icon { width: 34px; height: 34px; border: 1.5px solid #0f172a; border-radius: 8px; background: #0f172a; color: #94a3b8; font-size: 15px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background .15s, color .15s; flex-shrink: 0; }
.btn-tv-icon:hover:not(:disabled) { background: #1e293b; color: #f1f5f9; }
.btn-tv-icon:disabled { opacity: .4; cursor: not-allowed; }
.btn-tv-icon--regen:hover:not(:disabled) { background: #7c3aed; border-color: #7c3aed; color: #fff; }
.btn-refresh { width: 34px; height: 34px; border: 1.5px solid #e2e8f0; border-radius: 8px; background: #fff; color: #64748b; font-size: 15px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background .15s; flex-shrink: 0; }
.btn-refresh:hover:not(:disabled) { background: #f1f5f9; color: #1d4ed8; }
.btn-refresh:disabled { opacity: .5; cursor: not-allowed; }
.spin { animation: spin .8s linear infinite; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }
.action-bar { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
.action-btn { display: flex; align-items: center; gap: 8px; padding: 11px 20px; border: none; border-radius: 10px; font-size: 14px; font-weight: 700; cursor: pointer; transition: opacity .15s, transform .15s; position: relative; white-space: nowrap; }
.action-btn:hover { opacity: .88; transform: translateY(-1px); }
.action-btn i { font-size: 1.1rem; }
.action-btn--primary { background: linear-gradient(135deg, #1e3a5f, #1d4ed8); color: #fff; box-shadow: 0 4px 12px rgba(29,78,216,.28); }
.action-btn--llevar  { background: #fff; color: #475569; border: 2px solid #cbd5e1; }
.action-btn--llevar:hover { background: #f8fafc; border-color: #64748b; }
.action-btn--stock   { background: #fff5f5; color: #dc2626; border: 2px solid #fca5a5; }
.action-btn--stock:hover { background: #fee2e2; }
.action-btn--tv      { background: #eff6ff; color: #1d4ed8; border: 2px solid #bfdbfe; }
.action-btn--tv:hover { background: #dbeafe; }
.action-btn__badge { background: #dc2626; color: #fff; font-size: 11px; font-weight: 700; padding: 1px 6px; border-radius: 10px; min-width: 20px; text-align: center; }
.action-btn__badge--tv { background: #1d4ed8; }
.mesas-section { min-height: 200px; position: relative; overflow: hidden; }
.wm-icon { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 300px; color: rgba(0,0,0,.04); pointer-events: none; user-select: none; z-index: 0; line-height: 1; }
.estado-carga, .estado-vacio { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; min-height: 160px; color: #475569; font-size: 14px; text-align: center; position: relative; z-index: 1; }
.estado-vacio i { font-size: 40px; }
.mesas-grid { display: flex; flex-wrap: wrap; gap: 16px 10px; padding: 16px 4px; position: relative; z-index: 1; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 1050; padding: 16px; }
.modal-panel { background: #fff; border-radius: 16px; width: 100%; max-width: 480px; max-height: 85dvh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,.22); overflow: hidden; }
.modal-panel__header { display: flex; align-items: center; justify-content: space-between; padding: 14px 20px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; font-weight: 700; font-size: 14px; color: #1e3a5f; flex-shrink: 0; }
.modal-close { background: none; border: none; color: #94a3b8; font-size: 16px; cursor: pointer; padding: 4px 6px; border-radius: 6px; line-height: 1; }
.modal-close:hover { background: #f1f5f9; color: #475569; }
.modal-panel__body { flex: 1; overflow-y: auto; padding: 16px; }
.modal-loading { display: flex; align-items: center; justify-content: center; padding: 32px; }
.modal-empty { display: flex; align-items: center; justify-content: center; padding: 32px 16px; font-size: 14px; color: #475569; text-align: center; }
.stock-table-wrap { overflow-x: auto; }
.stock-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.stock-table th { padding: 8px 10px; color: #64748b; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: .4px; border-bottom: 2px solid #e2e8f0; background: #fafafa; }
.stock-table td { padding: 10px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.stock-table tr:last-child td { border-bottom: none; }
.si-name { font-weight: 600; color: #1e293b; }
.si-unit { font-size: 11px; color: #94a3b8; }
.tv-list { display: flex; flex-direction: column; gap: 10px; }
.tv-card { border: 2px solid #e2e8f0; border-radius: 12px; padding: 14px; background: #fff; display: flex; flex-direction: column; gap: 8px; }
.tv-card__top { display: flex; justify-content: space-between; align-items: center; }
.tv-card__mesa { font-weight: 700; font-size: 14px; color: #1e3a5f; }
.tv-card__hora { font-size: 12px; color: #94a3b8; }
.tv-card__mid  { display: flex; gap: 12px; font-size: 12px; color: #64748b; flex-wrap: wrap; }
.tv-card__preview { font-size: 12px; color: #475569; background: #f8fafc; border-radius: 6px; padding: 6px 10px; font-style: italic; }
.tv-card__bot { display: flex; align-items: center; justify-content: space-between; margin-top: 4px; }
.tv-card__monto { font-size: 16px; font-weight: 800; color: #1e3a5f; }
.btn-ya-salio { display: flex; align-items: center; gap: 6px; padding: 8px 16px; border: none; border-radius: 8px; background: linear-gradient(135deg, #16a34a, #15803d); color: #fff; font-size: 13px; font-weight: 700; cursor: pointer; transition: opacity .15s; }
.btn-ya-salio:hover:not(:disabled) { opacity: .88; }
.btn-ya-salio:disabled { opacity: .55; cursor: not-allowed; }
.wizard-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.5); display: flex; align-items: center; justify-content: center; z-index: 1060; padding: 16px; }
.wizard-modal { background: #fff; border-radius: 16px; width: 100%; max-width: 560px; max-height: 90dvh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,.25); overflow: hidden; position: relative; }
.wizard-header { display: flex; align-items: center; justify-content: space-between; padding: 14px 20px; background: linear-gradient(90deg, #1e3a5f, #1d4ed8); color: #fff; flex-shrink: 0; }
.wizard-steps { display: flex; align-items: center; gap: 10px; }
.wstep { display: flex; align-items: center; gap: 5px; font-size: 13px; font-weight: 600; opacity: .5; transition: opacity .2s; }
.wstep.active { opacity: 1; }
.wstep.done   { opacity: .7; }
.wstep-sep { width: 30px; height: 2px; background: rgba(255,255,255,.3); border-radius: 1px; }
.wizard-close { background: none; border: none; color: rgba(255,255,255,.7); font-size: 16px; cursor: pointer; padding: 4px 8px; }
.wizard-close:hover { color: #fff; }
.wizard-body { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.wizard-section-title { font-size: 15px; font-weight: 700; color: #1e3a5f; margin: 0; }
.meseros-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 10px; }
.mesero-card { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 14px 8px; border: 2px solid #e2e8f0; border-radius: 12px; background: #fff; cursor: pointer; transition: all .15s; }
.mesero-card:hover { border-color: #1d4ed8; }
.mesero-card--selected { border-color: #1d4ed8; background: #eff6ff; }
.mesero-card--add { border-style: dashed; color: #64748b; }
.mesero-card--add:hover { border-color: #10b981; color: #10b981; }
.mesero-avatar { width: 44px; height: 44px; border-radius: 50%; background: linear-gradient(135deg, #1e3a5f, #1d4ed8); color: #fff; font-size: 1.2rem; font-weight: 700; display: flex; align-items: center; justify-content: center; }
.mesero-avatar--none { background: #e2e8f0; color: #94a3b8; }
.mesero-avatar--add  { background: #f0fdf4; color: #16a34a; font-size: 1.1rem; }
.mesero-card--selected .mesero-avatar { box-shadow: 0 0 0 3px #2563eb; }
.mesero-name { font-size: 11px; font-weight: 600; color: #334155; text-align: center; line-height: 1.3; }
.add-waiter-form { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px; }
.aw-row { display: flex; gap: 8px; align-items: center; }
.campo-input { flex: 1; border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 8px 10px; font-size: 13px; color: #1e3a5f; outline: none; min-width: 0; }
.campo-input:focus { border-color: #1d4ed8; }
.btn-aw-save { width: 38px; height: 38px; border: none; border-radius: 8px; background: #10b981; color: #fff; font-size: 16px; cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.btn-aw-save:disabled { opacity: .6; }
.zonas-acordeon { display: flex; flex-direction: column; gap: 8px; }
.zona-acordeon { border: 1.5px solid #e2e8f0; border-radius: 10px; overflow: hidden; }
.zona-acordeon__header { width: 100%; display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; background: #f8fafc; border: none; font-weight: 600; font-size: 13px; color: #1e3a5f; cursor: pointer; text-align: left; transition: background .15s; }
.zona-acordeon__header:hover { background: #f1f5f9; }
.zona-acordeon__header--open { background: #eff6ff; color: #1d4ed8; }
.zona-count { display: inline-block; background: #e2e8f0; border-radius: 10px; padding: 1px 7px; font-size: 11px; font-weight: 600; margin-left: 8px; color: #64748b; }
.zona-acordeon__body { padding: 12px; border-top: 1px solid #e2e8f0; background: #fff; }
.mesas-grid-wizard { display: grid; grid-template-columns: repeat(auto-fill, minmax(90px, 1fr)); gap: 8px; }
.mesa-wizard-card { border: 2px solid #e2e8f0; border-radius: 10px; overflow: hidden; background: #fff; cursor: pointer; text-align: center; padding: 0; transition: all .15s; display: flex; flex-direction: column; align-items: center; }
.mwc-status-bar { width: 100%; height: 4px; background: #e2e8f0; }
.mesa-wizard-card--libre .mwc-status-bar   { background: #10b981; }
.mesa-wizard-card--ocupada .mwc-status-bar { background: #ef4444; }
.mesa-wizard-card--libre:hover { border-color: #1d4ed8; transform: translateY(-1px); box-shadow: 0 3px 10px rgba(29,78,216,.15); }
.mesa-wizard-card--libre:hover .mwc-status-bar { background: #1d4ed8; }
.mesa-wizard-card--ocupada { border-color: #fca5a5; opacity: .65; cursor: not-allowed; }
.mwc-icon { font-size: 20px; margin: 10px 0 4px; }
.mesa-wizard-card--libre .mwc-icon   { color: #10b981; }
.mesa-wizard-card--ocupada .mwc-icon { color: #ef4444; }
.mwc-name  { font-size: 12px; font-weight: 700; color: #1e3a5f; padding: 0 6px; }
.mwc-info  { font-size: 10px; padding: 2px 6px 8px; }
.mwc-badge { background: #fee2e2; color: #b91c1c; border-radius: 6px; padding: 1px 5px; font-weight: 600; }
.mwc-seats { color: #10b981; font-weight: 600; }
.wizard-footer { display: flex; gap: 10px; justify-content: flex-end; padding-top: 8px; border-top: 1px solid #f1f5f9; flex-shrink: 0; }
.btn-cancelar { background: #f1f5f9; border: none; border-radius: 8px; padding: 9px 18px; font-size: 14px; cursor: pointer; color: #475569; font-weight: 600; }
.btn-cancelar:hover { background: #e2e8f0; }
.wizard-opening-hint { display: flex; align-items: center; font-size: 13px; color: #1d4ed8; font-weight: 600; }
.wizard-loading-overlay { position: absolute; inset: 0; background: rgba(255,255,255,.85); display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; font-size: 14px; color: #1e3a5f; font-weight: 600; border-radius: 16px; }
@media (max-width: 768px) {
  .dash-header { flex-direction: row; flex-wrap: wrap; }
  .btn-tv-label { display: none; }
  .btn-tv { padding: 6px 10px; }
  .action-bar { gap: 8px; }
  .action-btn { padding: 10px 14px; font-size: 13px; }
  .wm-icon { font-size: 240px; }
  .meseros-grid { grid-template-columns: repeat(auto-fill, minmax(85px, 1fr)); }
  .modal-panel { max-width: 100%; }
}
@media (max-width: 576px) {
  .action-bar { gap: 6px; }
  .action-btn { padding: 10px 12px; font-size: 12px; gap: 5px; }
  .action-btn i { font-size: 1rem; }
  .mesas-grid { gap: 12px 8px; justify-content: center; }
  .wm-icon { font-size: 180px; }
  .modal-overlay { padding: 0; align-items: flex-end; }
  .modal-panel { border-radius: 20px 20px 0 0; max-height: 88dvh; max-width: 100%; }
  .wizard-overlay { padding: 0; align-items: flex-end; }
  .wizard-modal { border-radius: 20px 20px 0 0; max-height: 92dvh; }
}
</style>
