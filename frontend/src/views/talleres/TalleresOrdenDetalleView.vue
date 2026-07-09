<template>
  <div class="od-page">

    <!-- ── Header fijo ───────────────────────────────────────────────── -->
    <div class="od-header">
      <button class="btn-back" @click="router.push('/talleres/ordenes')" title="Volver al listado">
        <i class="bi bi-arrow-left"></i>
      </button>
      <div class="od-titulo">
        <span class="od-num">{{ orden?.numero_orden ?? '...' }}</span>
        <span :class="['es-badge', `es-${orden?.estado}`]">{{ estadoLabel(orden?.estado) }}</span>
        <span v-if="orden?.placa_vehiculo" class="od-placa">{{ orden.placa_vehiculo }}</span>
      </div>
      <div class="od-totales-mini" v-if="orden">
        <span class="tot-mini"><i class="bi bi-currency-dollar"></i> {{ fmt(totales.total) }}</span>
        <button class="btn-imprimir" @click="imprimir" title="Imprimir"><i class="bi bi-printer"></i></button>
      </div>
    </div>

    <div v-if="loadingOrden" class="od-loading">
      <i class="bi bi-arrow-repeat spin"></i> Cargando orden…
    </div>

    <template v-else-if="orden">
      <!-- ── Tabs ───────────────────────────────────────────────────── -->
      <div class="od-tabs">
        <button :class="['od-tab', { active: tab === 'editar' }]" @click="tab='editar'">
          <i class="bi bi-pencil-square"></i> Editar Orden
        </button>
        <button :class="['od-tab', { active: tab === 'historial' }]" @click="tab='historial'; cargarHistorial()">
          <i class="bi bi-clock-history"></i> Historial
        </button>
      </div>

      <!-- ════════════ TAB: EDITAR ORDEN ════════════════════════════ -->
      <div v-if="tab === 'editar'" class="tab-body">

        <!-- ▸ Acordeón: Datos del Vehículo -->
        <div class="acord-block">
          <button class="acord-head" @click="toggle('vehiculo')">
            <div class="acord-title"><i class="bi bi-car-front-fill"></i> Datos del Vehículo</div>
            <i :class="open.has('vehiculo') ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
          </button>
          <div v-if="open.has('vehiculo')" class="acord-body">
            <div class="form-grid">
              <div class="fg"><label>Placa</label>
                <input v-model="editForm.placa_vehiculo" class="fc" readonly /></div>
              <div class="fg"><label>Tipo</label>
                <input v-model="vehiculoExt.tipo" class="fc" readonly /></div>
              <div class="fg"><label>Marca</label>
                <input v-model="vehiculoExt.marca" class="fc" readonly /></div>
              <div class="fg"><label>Modelo</label>
                <input v-model="vehiculoExt.modelo" class="fc" readonly /></div>
              <div class="fg"><label>Año</label>
                <input v-model="vehiculoExt.anio" class="fc" readonly /></div>
              <div class="fg"><label>Color</label>
                <input v-model="vehiculoExt.color" class="fc" readonly /></div>
              <div class="fg"><label>Km Ingreso</label>
                <input v-model.number="editForm.km_ingreso" type="number" class="fc" /></div>
              <div class="fg"><label>Km Salida</label>
                <input v-model.number="editForm.km_salida" type="number" class="fc" /></div>
            </div>
          </div>
        </div>

        <!-- ▸ Acordeón: Datos del Cliente -->
        <div class="acord-block">
          <button class="acord-head" @click="toggle('cliente')">
            <div class="acord-title"><i class="bi bi-person-fill"></i> Datos del Cliente</div>
            <i :class="open.has('cliente') ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
          </button>
          <div v-if="open.has('cliente')" class="acord-body">
            <div class="form-grid">
              <div class="fg span2"><label>Nombre</label>
                <input :value="orden.cliente_nombre || '—'" class="fc" readonly /></div>
              <div class="fg"><label>Documento</label>
                <input :value="orden.cliente_documento || '—'" class="fc" readonly /></div>
              <div class="fg"><label>Teléfono</label>
                <input :value="orden.cliente_telefono || '—'" class="fc" readonly /></div>
              <div class="fg span2" v-if="orden.convenio_nombre"><label>Convenio empresarial</label>
                <input :value="orden.convenio_nombre" class="fc" readonly /></div>
            </div>
          </div>
        </div>

        <!-- ▸ Acordeón: Encabezado de la Orden -->
        <div class="acord-block">
          <button class="acord-head" @click="toggle('encabezado')">
            <div class="acord-title"><i class="bi bi-clipboard2-fill"></i> Encabezado de la Orden</div>
            <i :class="open.has('encabezado') ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
          </button>
          <div v-if="open.has('encabezado')" class="acord-body">
            <div class="form-grid">
              <div class="fg"><label>Fecha Ingreso</label>
                <input :value="fmtFecha(orden.fecha_ingreso)" class="fc" readonly /></div>
              <div class="fg"><label>Promesa de Entrega</label>
                <CustomDatePicker v-model="editForm.promesa_entrega" /></div>
              <div class="fg"><label>Jefe Responsable</label>
                <select v-model="editForm.jefe_responsable_id" class="fc">
                  <option :value="null">— Sin asignar —</option>
                  <option v-for="u in jefes" :key="u.id" :value="u.id">{{ u.nombre }}</option>
                </select></div>
              <div class="fg"><label>Convenio</label>
                <select v-model="editForm.convenio_id" class="fc">
                  <option :value="null">— Particular —</option>
                  <option v-for="c in convenios" :key="c.id" :value="c.id">{{ c.nombre_empresa }}</option>
                </select></div>
              <div class="fg span2"><label>Diagnóstico / Descripción del servicio</label>
                <textarea v-model="editForm.diagnostico" class="fc" rows="3"></textarea></div>
              <div class="fg span2"><label>Trabajo realizado</label>
                <textarea v-model="editForm.trabajo_realizado" class="fc" rows="3"></textarea></div>
            </div>
          </div>
        </div>

        <!-- ▸ Acordeón: Detalle de la Orden (siempre abierto) -->
        <div class="acord-block">
          <button class="acord-head" @click="toggle('detalle')">
            <div class="acord-title">
              <i class="bi bi-list-check"></i> Detalle de la Orden
              <span class="det-cnt">{{ detalles.length }} ítems · {{ fmt(totales.total) }}</span>
            </div>
            <i :class="open.has('detalle') ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
          </button>
          <div v-if="open.has('detalle')" class="acord-body">

            <!-- Totales bar -->
            <div class="totales-row">
              <div class="tc"><span class="tc-l">Servicios</span><span class="tc-v">{{ fmt(totales.servicios) }}</span></div>
              <div class="tc"><span class="tc-l">Repuestos</span><span class="tc-v">{{ fmt(totales.repuestos) }}</span></div>
              <div class="tc hl"><span class="tc-l">TOTAL</span><span class="tc-v">{{ fmt(totales.total) }}</span></div>
              <div class="tc mo"><span class="tc-l">Mano de Obra</span><span class="tc-v">{{ fmt(totales.mano_obra) }}</span></div>
            </div>

            <!-- Lista de ítems -->
            <div v-if="detalles.length === 0" class="det-empty">
              <i class="bi bi-inbox"></i> Sin ítems. Agrega servicios o repuestos abajo.
            </div>
            <div v-else class="detalles-list">
              <div v-for="d in detalles" :key="d.id" :class="['dr', `dr-${d.tipo_item}`]">
                <span :class="['dr-tipo', `dt-${d.tipo_item}`]">{{ tipoLabel(d.tipo_item) }}</span>
                <div class="dr-names">
                  <span class="dr-name">{{ d.nombre }}</span>
                  <span v-if="d.worker_nombre || d.operario_nombre" class="dr-worker">
                    <i class="bi bi-person-badge"></i> {{ d.worker_nombre ?? d.operario_nombre }}
                  </span>
                </div>
                <div class="dr-nums">
                  <span>{{ d.cantidad }} u</span>
                  <span>{{ fmt(d.precio_unitario) }}</span>
                  <span class="dr-sub">{{ fmt(d.subtotal) }}</span>
                  <span v-if="d.mano_obra_operario > 0" class="dr-mo"><i class="bi bi-person-fill"></i> {{ fmt(d.mano_obra_operario) }}</span>
                </div>
                <button v-if="!d.liq_estado || d.liq_estado === 'pendiente'"
                  class="dr-del" @click="eliminarDetalle(d)" :disabled="eliminandoId===d.id">
                  <i v-if="eliminandoId===d.id" class="bi bi-hourglass-split spin"></i>
                  <i v-else class="bi bi-trash3"></i>
                </button>
              </div>
            </div>

            <!-- Formulario agregar ítem -->
            <div class="add-item-form">
              <div class="aif-title"><i class="bi bi-plus-circle-fill"></i> Agregar Servicio / Repuesto</div>
              <div class="search-wrap">
                <input v-model="busqueda" class="fc" placeholder="Buscar por nombre o código…"
                  @input="buscarProductos" @keydown.esc="resultados=[]" />
                <i v-if="buscando" class="bi bi-hourglass-split spin abs-spin"></i>
              </div>
              <div v-if="resultados.length" class="search-results">
                <div v-for="r in resultados" :key="r.id" class="sr-item" @click="seleccionarProducto(r)">
                  <span class="sr-name">{{ r.name }}</span>
                  <span class="sr-code">{{ r.code }}</span>
                  <span class="sr-price">{{ fmt(r.base_price) }}</span>
                </div>
              </div>
              <div v-if="itemForm.producto_id" class="prod-sel">
                <span>{{ itemForm.producto_nombre }}</span>
                <button @click="limpiarProducto"><i class="bi bi-x-lg"></i></button>
              </div>
              <div class="form-grid mt8">
                <div class="fg"><label>Tipo</label>
                  <select v-model="itemForm.tipo_item" class="fc">
                    <option value="mecanica">Mecánica</option>
                    <option value="lavado">Lavado</option>
                    <option value="latoneria">Latonería</option>
                    <option value="pintura">Pintura</option>
                    <option value="repuesto">Repuesto</option>
                  </select></div>
                <div class="fg"><label>Cantidad</label>
                  <input v-model.number="itemForm.cantidad" type="number" min="0.01" step="0.01" class="fc" /></div>
                <div class="fg"><label>Precio unitario</label>
                  <input v-model.number="itemForm.precio_unitario" type="number" min="0" class="fc" /></div>
                <div class="fg"><label>Subtotal</label>
                  <div class="fc-display">{{ fmt(subtotalItem) }}</div></div>
                <div class="fg span2" v-if="itemForm.tipo_item !== 'repuesto'"><label>Operario responsable</label>
                  <select v-model="itemForm.worker_id" class="fc">
                    <option :value="null">— Sin asignar —</option>
                    <option v-for="w in workers" :key="w.id" :value="w.id">{{ w.nombre }} · {{ w.profesion ?? '' }}</option>
                  </select></div>
              </div>
              <button class="btn-agregar" :disabled="!puedeAgregar || agregando" @click="agregarDetalle">
                <i v-if="agregando" class="bi bi-hourglass-split spin"></i>
                <i v-else class="bi bi-plus-lg"></i>
                Agregar al detalle
              </button>
            </div>

          </div>
        </div>

        <!-- ── Botones de acción ──────────────────────────────────── -->
        <div class="action-bar" v-if="orden.estado !== 'cancelada'">
          <button class="btn-save" :disabled="guardando" @click="guardarCambios">
            <i v-if="guardando" class="bi bi-hourglass-split spin"></i>
            <i v-else class="bi bi-floppy-fill"></i>
            Guardar Cambios
          </button>
          <button class="btn-facturar" v-if="orden.estado !== 'entregada'" @click="facturar">
            <i class="bi bi-receipt-cutoff"></i>
            Facturar / Entregar
          </button>
          <button class="btn-cancelar" @click="cancelarOrden">
            <i class="bi bi-x-circle-fill"></i>
            Eliminar Orden
          </button>
        </div>
        <div class="action-bar" v-else>
          <div class="orden-cancelada-msg"><i class="bi bi-x-circle-fill"></i> Orden cancelada</div>
        </div>

      </div><!-- /tab editar -->

      <!-- ════════════ TAB: HISTORIAL ════════════════════════════════ -->
      <div v-if="tab === 'historial'" class="tab-body">
        <div class="hist-subtabs">
          <button :class="['hs-tab', { active: subTab==='placa' }]" @click="subTab='placa'; cargarHistPlaca()">
            <i class="bi bi-car-front-fill"></i> Esta Placa ({{ orden.placa_vehiculo }})
          </button>
          <button :class="['hs-tab', { active: subTab==='cliente' }]"
            :disabled="!orden.client_id"
            @click="subTab='cliente'; cargarHistCliente()">
            <i class="bi bi-person-fill"></i> Este Cliente
            <span v-if="!orden.client_id" class="hs-nodato">(sin cliente)</span>
          </button>
        </div>

        <div v-if="loadingHist" class="od-loading"><i class="bi bi-arrow-repeat spin"></i> Cargando…</div>
        <div v-else-if="histItems.length === 0" class="od-empty">
          <i class="bi bi-inbox"></i>
          <p>Sin historial</p>
        </div>
        <div v-else class="hist-table-wrap">
          <table class="hist-table">
            <thead>
              <tr>
                <th v-if="subTab==='cliente'">Placa</th>
                <th>Orden</th>
                <th>Fecha</th>
                <th>Estado</th>
                <th>Jefe</th>
                <th class="ta-r">Total</th>
                <th>Ítems</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="h in histItems" :key="h.id" class="hist-row">
                <td v-if="subTab==='cliente'" class="h-placa">{{ h.placa_vehiculo }}</td>
                <td class="h-num">{{ h.numero_orden }}</td>
                <td class="h-fecha">{{ fmtFecha(h.fecha_ingreso) }}</td>
                <td><span :class="['es-badge', `es-${h.estado}`]">{{ estadoLabel(h.estado) }}</span></td>
                <td class="h-jefe">{{ h.jefe_nombre || '—' }}</td>
                <td class="ta-r h-tot">{{ fmt(h.total_orden) }}</td>
                <td class="ta-c h-cnt">{{ h.cant_items }}</td>
                <td>
                  <button class="h-btn" @click="router.push(`/talleres/orden/${h.id}`)" title="Ver/Editar">
                    <i class="bi bi-arrow-right-circle-fill"></i>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div><!-- /tab historial -->

    </template>

    <!-- Toast -->
    <Teleport to="body">
      <div v-if="toast.visible" :class="['toast-msg', `toast-${toast.tipo}`]">
        <i :class="toast.tipo==='ok' ? 'bi bi-check-circle-fill' : 'bi bi-exclamation-triangle-fill'"></i>
        {{ toast.msg }}
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCompanyStore } from '@/stores/companyStore'
import api from '@/services/apis'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'

const route        = useRoute()
const router       = useRouter()
const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id)
const ordenId      = computed(() => route.params.id)

// ── Estado de acordeón ────────────────────────────────────────────────────────
const open = ref(new Set(['detalle', 'encabezado']))
function toggle(sec) {
  const s = new Set(open.value)
  s.has(sec) ? s.delete(sec) : s.add(sec)
  open.value = s
}

// ── Tabs ──────────────────────────────────────────────────────────────────────
const tab    = ref('editar')
const subTab = ref('placa')

// ── Carga de la orden ─────────────────────────────────────────────────────────
const orden          = ref(null)
const vehiculoExt    = ref({})
const detalles       = ref([])
const loadingOrden   = ref(false)

const editForm = ref({
  km_ingreso: null, km_salida: null,
  diagnostico: '', trabajo_realizado: '',
  promesa_entrega: null, jefe_responsable_id: null, convenio_id: null,
  placa_vehiculo: '',
})

async function cargarOrden() {
  if (!ordenId.value || !companyId.value) return
  loadingOrden.value = true
  try {
    const { data } = await api.get(`/api/talleres/ordenes/${ordenId.value}`, {
      params: { company_id: companyId.value }
    })
    orden.value     = data.orden ?? data
    detalles.value  = data.detalles ?? []
    vehiculoExt.value = {
      tipo:   orden.value.tipo_vehiculo || '',
      marca:  orden.value.marca || '',
      modelo: orden.value.modelo || '',
      anio:   orden.value.anio  || '',
      color:  orden.value.color || '',
    }
    editForm.value = {
      km_ingreso:          orden.value.km_ingreso ?? null,
      km_salida:           orden.value.km_salida  ?? null,
      diagnostico:         orden.value.diagnostico || '',
      trabajo_realizado:   orden.value.trabajo_realizado || '',
      promesa_entrega:     orden.value.promesa_entrega ? orden.value.promesa_entrega.split('T')[0] : null,
      jefe_responsable_id: orden.value.jefe_responsable_id ?? null,
      convenio_id:         orden.value.convenio_id ?? null,
      placa_vehiculo:      orden.value.placa_vehiculo || '',
    }
  } catch { mostrarToast('Error al cargar la orden', 'error') }
  finally  { loadingOrden.value = false }
}

// ── Guardar cambios ───────────────────────────────────────────────────────────
const guardando = ref(false)
async function guardarCambios() {
  guardando.value = true
  try {
    await api.patch(`/api/talleres/ordenes/${ordenId.value}/editar`, {
      company_id: companyId.value,
      ...editForm.value,
    })
    if (orden.value) {
      Object.assign(orden.value, editForm.value)
    }
    mostrarToast('Cambios guardados', 'ok')
  } catch (e) { mostrarToast(e?.response?.data?.detail ?? 'Error al guardar', 'error') }
  finally { guardando.value = false }
}

// ── Facturar / Entregar ────────────────────────────────────────────────────────
async function facturar() {
  if (!confirm('¿Marcar esta orden como entregada/facturada?')) return
  try {
    await api.patch(`/api/talleres/ordenes/${ordenId.value}/estado`, {
      company_id: companyId.value, estado: 'entregada',
      trabajo_realizado: editForm.value.trabajo_realizado,
      km_salida: editForm.value.km_salida,
    })
    if (orden.value) orden.value.estado = 'entregada'
    mostrarToast('Orden marcada como Entregada', 'ok')
  } catch (e) { mostrarToast(e?.response?.data?.detail ?? 'Error', 'error') }
}

// ── Cancelar / Eliminar orden ─────────────────────────────────────────────────
async function cancelarOrden() {
  if (!confirm('¿Eliminar (cancelar) esta orden? Esta acción no se puede deshacer.')) return
  try {
    await api.patch(`/api/talleres/ordenes/${ordenId.value}/estado`, {
      company_id: companyId.value, estado: 'cancelada',
    })
    mostrarToast('Orden cancelada', 'ok')
    setTimeout(() => router.push('/talleres/ordenes'), 1000)
  } catch (e) { mostrarToast(e?.response?.data?.detail ?? 'Error', 'error') }
}

// ── Workers y jefes ───────────────────────────────────────────────────────────
const workers   = ref([])
const jefes     = ref([])
const convenios = ref([])

async function cargarAuxiliares() {
  try {
    const [wRes, jRes, cRes] = await Promise.all([
      api.get('/api/talleres/workers-con-config',    { params: { company_id: companyId.value } }),
      api.get('/api/users/',                          { params: { company_id: companyId.value } }),
      api.get('/api/talleres/convenios',             { params: { company_id: companyId.value } }),
    ])
    workers.value   = wRes.data ?? []
    jefes.value     = (jRes.data?.items ?? jRes.data ?? [])
    convenios.value = cRes.data ?? []
  } catch { /* silencioso */ }
}

// ── Búsqueda de productos ─────────────────────────────────────────────────────
const busqueda   = ref('')
const resultados = ref([])
const buscando   = ref(false)
let searchTimer  = null

function buscarProductos() {
  clearTimeout(searchTimer)
  if (busqueda.value.length < 2) { resultados.value = []; return }
  searchTimer = setTimeout(async () => {
    buscando.value = true
    try {
      const { data } = await api.get('/api/talleres/productos-buscar', {
        params: { company_id: companyId.value, q: busqueda.value, limit: 10 }
      })
      resultados.value = data
    } catch { resultados.value = [] }
    finally { buscando.value = false }
  }, 300)
}
function seleccionarProducto(p) {
  itemForm.value.producto_id     = p.id
  itemForm.value.producto_nombre = p.name
  itemForm.value.precio_unitario = p.base_price ?? 0
  if (p.service_type) itemForm.value.tipo_item = p.service_type
  else if (p.inventory_behavior === 'decrement') itemForm.value.tipo_item = 'repuesto'
  busqueda.value  = ''
  resultados.value = []
}
function limpiarProducto() {
  itemForm.value.producto_id = null
  itemForm.value.producto_nombre = ''
}

// ── Formulario de ítem ────────────────────────────────────────────────────────
const itemFormDef = () => ({
  producto_id: null, producto_nombre: '',
  tipo_item: 'mecanica', cantidad: 1, precio_unitario: 0, worker_id: null,
})
const itemForm = ref(itemFormDef())
const agregando = ref(false)
const eliminandoId = ref(null)

const subtotalItem = computed(() => (itemForm.value.cantidad || 0) * (itemForm.value.precio_unitario || 0))
const puedeAgregar = computed(() => !!itemForm.value.producto_id && itemForm.value.cantidad > 0 && itemForm.value.precio_unitario >= 0)

async function agregarDetalle() {
  if (!puedeAgregar.value) return
  agregando.value = true
  try {
    const workerSel = workers.value.find(x => x.id === itemForm.value.worker_id)
    const { data } = await api.post(`/api/talleres/ordenes/${ordenId.value}/detalle`, {
      company_id:     companyId.value,
      product_id:     itemForm.value.producto_id,
      nombre:         itemForm.value.producto_nombre,
      tipo_item:      itemForm.value.tipo_item,
      cantidad:       itemForm.value.cantidad,
      precio_unitario: itemForm.value.precio_unitario,
      worker_id:      itemForm.value.worker_id || null,
      profession_id:  workerSel?.profession_id || null,
    })
    detalles.value.push({
      id: data.id ?? Date.now(),
      tipo_item:          itemForm.value.tipo_item,
      nombre:             itemForm.value.producto_nombre,
      cantidad:           itemForm.value.cantidad,
      precio_unitario:    itemForm.value.precio_unitario,
      subtotal:           data.subtotal ?? subtotalItem.value,
      mano_obra_operario: data.mano_obra_operario ?? 0,
      worker_nombre:      workerSel?.nombre ?? null,
      liq_estado:         'pendiente',
    })
    itemForm.value = itemFormDef()
    mostrarToast('Ítem agregado', 'ok')
  } catch (e) { mostrarToast(e?.response?.data?.detail ?? 'Error al agregar', 'error') }
  finally { agregando.value = false }
}

async function eliminarDetalle(d) {
  if (!confirm(`¿Eliminar "${d.nombre}"?`)) return
  eliminandoId.value = d.id
  try {
    await api.delete(`/api/talleres/ordenes/${ordenId.value}/detalle/${d.id}`, {
      params: { company_id: companyId.value }
    })
    detalles.value = detalles.value.filter(x => x.id !== d.id)
    mostrarToast('Ítem eliminado', 'ok')
  } catch (e) { mostrarToast(e?.response?.data?.detail ?? 'Error', 'error') }
  finally { eliminandoId.value = null }
}

// ── Totales ───────────────────────────────────────────────────────────────────
const totales = computed(() => {
  let servicios = 0, repuestos = 0, mano_obra = 0
  for (const d of detalles.value) {
    if (d.tipo_item === 'repuesto') repuestos += d.subtotal ?? 0
    else servicios += d.subtotal ?? 0
    mano_obra += d.mano_obra_operario ?? 0
  }
  return { servicios, repuestos, total: servicios + repuestos, mano_obra }
})

// ── Historial ─────────────────────────────────────────────────────────────────
const histItems  = ref([])
const loadingHist = ref(false)
let histPlacaCargado   = false
let histClienteCargado = false

async function cargarHistorial() {
  if (subTab.value === 'placa') cargarHistPlaca()
}
async function cargarHistPlaca() {
  if (histPlacaCargado) return
  loadingHist.value = true
  try {
    const { data } = await api.get('/api/talleres/historial/placa', {
      params: { company_id: companyId.value, placa: orden.value?.placa_vehiculo }
    })
    histItems.value  = data
    histPlacaCargado = true
  } catch { histItems.value = [] }
  finally { loadingHist.value = false }
}
async function cargarHistCliente() {
  if (histClienteCargado || !orden.value?.client_id) return
  loadingHist.value = true
  try {
    const { data } = await api.get('/api/talleres/historial/cliente', {
      params: { company_id: companyId.value, client_id: orden.value.client_id }
    })
    histItems.value    = data
    histClienteCargado = true
  } catch { histItems.value = [] }
  finally { loadingHist.value = false }
}

watch(subTab, (val) => {
  histItems.value = []
  if (val === 'placa')   { histPlacaCargado = false;   cargarHistPlaca() }
  if (val === 'cliente') { histClienteCargado = false; cargarHistCliente() }
})

// ── Imprimir ──────────────────────────────────────────────────────────────────
function imprimir() { window.print() }

// ── Helpers ───────────────────────────────────────────────────────────────────
function estadoLabel(e) {
  return { abierta:'Abierta', en_proceso:'En Proceso', terminada:'Terminada', entregada:'Entregada', cancelada:'Cancelada' }[e] ?? e ?? '—'
}
function tipoLabel(t) {
  return { mecanica:'Mecánica', lavado:'Lavado', latoneria:'Latonería', pintura:'Pintura', repuesto:'Repuesto' }[t] ?? t
}
function fmtFecha(v) {
  if (!v) return '—'
  return new Date(v).toLocaleDateString('es-CO', { day:'2-digit', month:'short', year:'numeric' })
}
function fmt(v) {
  if (v == null || v === '') return '—'
  return new Intl.NumberFormat('es-CO', { style:'currency', currency:'COP', maximumFractionDigits:0 }).format(v)
}

const toast = ref({ visible: false, msg: '', tipo: 'ok' })
function mostrarToast(msg, tipo = 'ok') {
  toast.value = { visible: true, msg, tipo }
  setTimeout(() => { toast.value.visible = false }, 3500)
}

onMounted(() => { cargarOrden(); cargarAuxiliares() })
</script>

<style scoped>
.od-page { padding: 16px; max-width: 900px; display: flex; flex-direction: column; gap: 14px; }

/* ── Header ─────────────────────────────────────────────────────────── */
.od-header { display:flex; align-items:center; gap:12px; background:#fff; border-radius:12px; padding:12px 16px; box-shadow:0 2px 8px rgba(0,0,0,.07); flex-wrap:wrap; }
.btn-back  { width:36px; height:36px; border-radius:9px; border:1.5px solid #e2e8f0; background:#f8fafc; cursor:pointer; color:#475569; display:flex; align-items:center; justify-content:center; font-size:15px; flex-shrink:0; }
.btn-back:hover { background:#eff6ff; color:#1d4ed8; border-color:#bfdbfe; }
.od-titulo { display:flex; align-items:center; gap:8px; flex:1; flex-wrap:wrap; min-width:0; }
.od-num    { font-size:17px; font-weight:800; font-family:monospace; color:#1e293b; }
.od-placa  { font-size:16px; font-weight:900; letter-spacing:2px; color:#1e293b; background:#f1f5f9; padding:3px 10px; border-radius:6px; }
.od-totales-mini { display:flex; align-items:center; gap:8px; margin-left:auto; }
.tot-mini  { font-size:16px; font-weight:700; color:#059669; display:flex; align-items:center; gap:5px; }
.btn-imprimir { width:34px; height:34px; border-radius:8px; border:1.5px solid #e2e8f0; background:#f8fafc; cursor:pointer; color:#475569; display:flex; align-items:center; justify-content:center; }
.btn-imprimir:hover { background:#f0fdf4; color:#059669; }

/* ── Estado badge ────────────────────────────────────────────────────── */
.es-badge  { font-size:11px; font-weight:700; padding:3px 9px; border-radius:20px; }
.es-abierta    { background:#dbeafe; color:#1d4ed8; }
.es-en_proceso { background:#fef3c7; color:#92400e; }
.es-terminada  { background:#dcfce7; color:#166534; }
.es-entregada  { background:#f1f5f9; color:#64748b; }
.es-cancelada  { background:#fee2e2; color:#b91c1c; }

/* ── Tabs ────────────────────────────────────────────────────────────── */
.od-tabs { display:flex; gap:4px; background:#f1f5f9; border-radius:10px; padding:4px; }
.od-tab  { display:flex; align-items:center; gap:7px; flex:1; padding:10px 14px; font-size:13px; font-weight:700; border:none; background:none; border-radius:7px; cursor:pointer; color:#64748b; justify-content:center; transition:all .12s; }
.od-tab.active { background:#fff; color:#1d4ed8; box-shadow:0 1px 4px rgba(0,0,0,.1); }
.od-tab:hover:not(.active) { background:#e2e8f0; }

.tab-body { display:flex; flex-direction:column; gap:10px; }

/* ── Acordeón ────────────────────────────────────────────────────────── */
.acord-block { border-radius:12px; border:1.5px solid #e2e8f0; background:#fff; overflow:hidden; }
.acord-head  { display:flex; align-items:center; justify-content:space-between; width:100%; padding:13px 16px; background:none; border:none; cursor:pointer; font-size:13px; font-weight:700; color:#1e293b; transition:background .1s; }
.acord-head:hover { background:#f8fafc; }
.acord-title { display:flex; align-items:center; gap:8px; color:#1e293b; }
.acord-title .bi { color:#3b82f6; font-size:15px; }
.acord-body  { padding:14px 16px; border-top:1px solid #f1f5f9; }
.det-cnt     { font-size:11px; font-weight:600; color:#64748b; background:#f1f5f9; padding:2px 8px; border-radius:20px; margin-left:8px; }

/* ── Form grid ───────────────────────────────────────────────────────── */
.form-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
.fg        { display:flex; flex-direction:column; gap:5px; }
.fg label  { font-size:11px; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:.4px; }
.span2     { grid-column:span 2; }
.mt8       { margin-top:8px; }
.fc        { border:1.5px solid #e2e8f0; border-radius:8px; padding:8px 10px; font-size:13px; color:#1e293b; outline:none; background:#fff; width:100%; box-sizing:border-box; }
.fc:focus  { border-color:#3b82f6; }
.fc[readonly] { background:#f8fafc; color:#64748b; cursor:default; }
textarea.fc { resize:vertical; }
.fc-display { border:1.5px solid #e2e8f0; border-radius:8px; padding:8px 10px; font-size:13px; color:#059669; font-weight:700; background:#f0fdf4; }

/* ── Totales row ─────────────────────────────────────────────────────── */
.totales-row { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:12px; }
.tc    { display:flex; flex-direction:column; gap:3px; padding:10px 14px; border-radius:10px; background:#f8fafc; border:1.5px solid #e2e8f0; flex:1; min-width:80px; }
.tc-l  { font-size:10px; font-weight:700; color:#94a3b8; text-transform:uppercase; }
.tc-v  { font-size:15px; font-weight:800; color:#1e293b; }
.tc.hl { background:#f0fdf4; border-color:#bbf7d0; } .tc.hl .tc-v { color:#059669; }
.tc.mo { background:#fffbeb; border-color:#fde68a; } .tc.mo .tc-v { color:#d97706; }

/* ── Detalles list ───────────────────────────────────────────────────── */
.det-empty   { display:flex; align-items:center; gap:8px; color:#94a3b8; font-size:13px; padding:16px; }
.detalles-list { display:flex; flex-direction:column; gap:6px; margin-bottom:14px; }
.dr          { display:flex; align-items:center; gap:10px; padding:10px 12px; border-radius:9px; background:#f8fafc; border:1px solid #f1f5f9; flex-wrap:wrap; }
.dr-tipo     { font-size:10px; font-weight:700; padding:2px 7px; border-radius:20px; flex-shrink:0; }
.dt-mecanica  { background:#dbeafe; color:#1d4ed8; }
.dt-lavado    { background:#cffafe; color:#0e7490; }
.dt-latoneria { background:#fef3c7; color:#92400e; }
.dt-pintura   { background:#ede9fe; color:#6d28d9; }
.dt-repuesto  { background:#f1f5f9; color:#475569; }
.dr-names    { flex:1; display:flex; flex-direction:column; gap:2px; min-width:0; }
.dr-name     { font-size:13px; font-weight:600; color:#1e293b; }
.dr-worker   { font-size:11px; color:#94a3b8; display:flex; align-items:center; gap:4px; }
.dr-nums     { display:flex; align-items:center; gap:10px; font-size:12px; color:#64748b; flex-wrap:wrap; }
.dr-sub      { font-weight:700; color:#1e293b; }
.dr-mo       { color:#d97706; font-weight:600; display:flex; align-items:center; gap:3px; }
.dr-del      { width:28px; height:28px; border-radius:7px; border:1.5px solid #fca5a5; background:#fff0f0; color:#dc2626; cursor:pointer; display:flex; align-items:center; justify-content:center; font-size:12px; flex-shrink:0; }
.dr-del:hover:not(:disabled) { background:#dc2626; color:#fff; }
.dr-del:disabled { opacity:.5; cursor:not-allowed; }

/* ── Agregar ítem ────────────────────────────────────────────────────── */
.add-item-form { border-top:1.5px dashed #e2e8f0; padding-top:14px; display:flex; flex-direction:column; gap:10px; }
.aif-title     { font-size:13px; font-weight:700; color:#374151; display:flex; align-items:center; gap:7px; }
.aif-title .bi { color:#10b981; }
.search-wrap   { position:relative; }
.abs-spin      { position:absolute; right:10px; top:50%; transform:translateY(-50%); color:#94a3b8; }
.search-results { border:1.5px solid #e2e8f0; border-radius:8px; background:#fff; max-height:200px; overflow-y:auto; }
.sr-item       { display:flex; align-items:center; gap:10px; padding:9px 12px; cursor:pointer; border-bottom:1px solid #f1f5f9; }
.sr-item:hover { background:#f0f9ff; }
.sr-name       { flex:1; font-size:13px; font-weight:600; color:#1e293b; }
.sr-code       { font-size:11px; color:#94a3b8; font-family:monospace; }
.sr-price      { font-size:12px; font-weight:700; color:#059669; }
.prod-sel      { display:flex; align-items:center; justify-content:space-between; background:#f0fdf4; border:1.5px solid #bbf7d0; border-radius:8px; padding:8px 12px; font-size:13px; font-weight:600; color:#1e293b; }
.prod-sel button { background:none; border:none; cursor:pointer; color:#94a3b8; font-size:13px; }
.btn-agregar   { display:flex; align-items:center; gap:7px; padding:10px 18px; background:#3b82f6; color:#fff; border:none; border-radius:9px; font-size:13px; font-weight:700; cursor:pointer; }
.btn-agregar:hover:not(:disabled) { background:#2563eb; }
.btn-agregar:disabled { opacity:.5; cursor:not-allowed; }

/* ── Action bar ──────────────────────────────────────────────────────── */
.action-bar     { display:flex; gap:10px; flex-wrap:wrap; padding:14px 0; border-top:2px solid #f1f5f9; }
.btn-save       { display:flex; align-items:center; gap:7px; padding:11px 22px; background:#1d4ed8; color:#fff; border:none; border-radius:10px; font-size:14px; font-weight:700; cursor:pointer; }
.btn-save:hover:not(:disabled) { background:#1e40af; }
.btn-save:disabled { opacity:.6; cursor:not-allowed; }
.btn-facturar   { display:flex; align-items:center; gap:7px; padding:11px 22px; background:#059669; color:#fff; border:none; border-radius:10px; font-size:14px; font-weight:700; cursor:pointer; }
.btn-facturar:hover { background:#047857; }
.btn-cancelar   { display:flex; align-items:center; gap:7px; padding:11px 22px; background:#fff; color:#dc2626; border:2px solid #fca5a5; border-radius:10px; font-size:14px; font-weight:700; cursor:pointer; margin-left:auto; }
.btn-cancelar:hover { background:#fee2e2; }
.orden-cancelada-msg { display:flex; align-items:center; gap:8px; color:#b91c1c; font-size:14px; font-weight:700; padding:12px 0; }

/* ── Historial ───────────────────────────────────────────────────────── */
.hist-subtabs { display:flex; gap:6px; margin-bottom:12px; flex-wrap:wrap; }
.hs-tab  { display:flex; align-items:center; gap:7px; padding:9px 16px; border-radius:9px; border:1.5px solid #e2e8f0; background:#f8fafc; font-size:13px; font-weight:600; color:#475569; cursor:pointer; transition:all .12s; }
.hs-tab.active { background:#1e3a5f; color:#fff; border-color:#1e3a5f; }
.hs-tab:disabled { opacity:.45; cursor:not-allowed; }
.hs-nodato { font-size:11px; opacity:.7; }
.hist-table-wrap { overflow-x:auto; border-radius:12px; border:1.5px solid #e2e8f0; }
.hist-table  { width:100%; border-collapse:collapse; font-size:13px; }
.hist-table thead tr { background:#f8fafc; }
.hist-table th { padding:10px 12px; text-align:left; font-size:11px; font-weight:700; color:#64748b; text-transform:uppercase; border-bottom:1.5px solid #e2e8f0; }
.hist-table td { padding:10px 12px; border-bottom:1px solid #f1f5f9; vertical-align:middle; }
.hist-row:hover td { background:#f0f9ff; }
.h-placa { font-weight:800; font-size:14px; letter-spacing:1px; }
.h-num   { font-family:monospace; font-size:12px; color:#64748b; }
.h-fecha { font-size:12px; color:#94a3b8; }
.h-jefe  { font-size:12px; color:#475569; }
.h-tot   { font-weight:700; color:#1e293b; }
.h-cnt   { color:#64748b; }
.ta-r    { text-align:right; }
.ta-c    { text-align:center; }
.h-btn   { width:30px; height:30px; border:none; border-radius:7px; background:#eff6ff; color:#1d4ed8; cursor:pointer; display:flex; align-items:center; justify-content:center; font-size:14px; }
.h-btn:hover { background:#1d4ed8; color:#fff; }

/* ── Loading / Empty ─────────────────────────────────────────────────── */
.od-loading { display:flex; align-items:center; justify-content:center; gap:10px; padding:60px; color:#94a3b8; font-size:14px; }
.od-empty   { display:flex; flex-direction:column; align-items:center; gap:8px; padding:50px; color:#94a3b8; }
.od-empty .bi { font-size:36px; color:#e2e8f0; }
.od-empty p   { font-size:13px; margin:0; }
.spin { display:inline-block; animation:spin .8s linear infinite; }
@keyframes spin { from{transform:rotate(0)} to{transform:rotate(360deg)} }

/* ── Toast ───────────────────────────────────────────────────────────── */
.toast-msg { position:fixed; bottom:24px; left:50%; transform:translateX(-50%); padding:12px 24px; border-radius:12px; font-size:14px; font-weight:600; display:flex; align-items:center; gap:8px; z-index:9999; box-shadow:0 8px 24px rgba(0,0,0,.18); animation:slideUp .2s ease; }
.toast-ok    { background:#059669; color:#fff; }
.toast-error { background:#dc2626; color:#fff; }
@keyframes slideUp { from{opacity:0;transform:translateX(-50%) translateY(12px)} to{opacity:1;transform:translateX(-50%) translateY(0)} }

/* ── Responsive 768px ────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .form-grid   { grid-template-columns: 1fr; }
  .span2       { grid-column: span 1; }
  .action-bar  { flex-direction: column; }
  .btn-cancelar { margin-left: 0; }
  .totales-row { gap: 6px; }
  .tc          { min-width: 70px; }
}

/* ── Responsive 576px ────────────────────────────────────────────────── */
@media (max-width: 576px) {
  .od-header   { flex-direction: column; align-items: flex-start; gap: 8px; }
  .od-totales-mini { margin-left: 0; }
  .dr          { flex-direction: column; align-items: flex-start; }
  .hist-table th:nth-child(5), .hist-table td:nth-child(5) { display: none; }
}
</style>
