<template>
  <div class="pk-page">

    <!-- ══ KPI BAR (clickables = filtros) ══════════════════════════════════ -->
    <div class="pk-kpi-bar">
      <button class="pk-btn-nuevo" @click="abrirModalNuevo">
        <i class="bi bi-plus-circle-fill"></i>
        <span>Nuevo Ingreso</span>
      </button>
      <div :class="['pk-kpi-card pk-kpi-ingresado', { 'pk-kpi-active': filtroEstado === 'ingresado' }]"
        @click="filtroEstado = filtroEstado === 'ingresado' ? '' : 'ingresado'; cargar()">
        <i class="bi bi-door-open-fill"></i>
        <div>
          <span class="pk-kpi-val">{{ stats.cnt_ingresado ?? 0 }}</span>
          <span class="pk-kpi-pct">{{ pctIngresado }}% de capacidad</span>
          <span class="pk-kpi-lbl">Ingresados</span>
        </div>
      </div>
      <div :class="['pk-kpi-card pk-kpi-confirmado', { 'pk-kpi-active': filtroEstado === 'registrado' }]"
        @click="filtroEstado = filtroEstado === 'registrado' ? '' : 'registrado'; cargar()">
        <i class="bi bi-person-check-fill"></i>
        <div>
          <span class="pk-kpi-val">{{ stats.cnt_registrado ?? 0 }}</span>
          <span class="pk-kpi-pct">{{ pctRegistrado }}% de capacidad</span>
          <span class="pk-kpi-lbl">Confirmados</span>
        </div>
      </div>
      <div :class="['pk-kpi-card pk-kpi-parasalir', { 'pk-kpi-active': filtroEstado === 'pagado' }]"
        @click="filtroEstado = filtroEstado === 'pagado' ? '' : 'pagado'; cargar()">
        <i class="bi bi-car-front-fill"></i>
        <div>
          <span class="pk-kpi-val">{{ stats.cnt_pagado ?? 0 }}</span>
          <span v-if="pctPagado > 0" class="pk-kpi-pct">{{ pctPagado }}% de activos</span>
          <span class="pk-kpi-lbl">Para salir</span>
        </div>
      </div>
      <div class="pk-kpi-card pk-kpi-disponible">
        <i class="bi bi-p-square-fill"></i>
        <div>
          <span class="pk-kpi-val">{{ stats.disponibles ?? 0 }}</span>
          <span class="pk-kpi-pct">{{ pctDisponible }}% libres · {{ stats.total_plazas ?? 0 }} plazas</span>
          <span class="pk-kpi-lbl">Disponibles</span>
        </div>
      </div>
    </div>

    <!-- ══ GRID DE TARJETAS ══════════════════════════════════════════════════ -->
    <div v-if="loading" class="pk-loading">
      <i class="bi bi-arrow-repeat spin"></i> Cargando…
    </div>
    <div v-else-if="ordenes.length === 0" class="pk-empty">
      <i class="bi bi-car-front"></i>
      <p>No hay ingresos activos</p>
    </div>
    <div v-else class="pk-grid">
      <div v-for="o in ordenes" :key="o.id" :class="['pk-card', `pk-card--${o.estado}`]">
        <div class="pk-card-top">
          <span :class="['pk-badge', `pk-badge--${o.estado}`]">{{ LABELS_ESTADO[o.estado] }}</span>
          <span class="pk-card-hora">{{ fmtHora(o.hora_ingreso) }}</span>
        </div>
        <div class="pk-card-placa">{{ o.placa }}</div>
        <div v-if="o.tipo_vehiculo" class="pk-card-tipo">{{ o.tipo_vehiculo }}</div>
        <div class="pk-card-items">
          <template v-if="o.items && o.items.length">
            <span v-for="it in o.items" :key="it.nombre" class="pk-svc-pill">
              {{ it.nombre }} <strong>×{{ it.cantidad }}</strong>
            </span>
          </template>
          <span v-else class="pk-svc-pill">
            <i class="bi bi-list-check"></i> {{ o.adultos }} servicio{{ o.adultos !== 1 ? 's' : '' }}
          </span>
        </div>
        <div v-if="o.obs_portero" class="pk-card-obs">
          <i class="bi bi-chat-left-text"></i> {{ o.obs_portero }}
        </div>
        <div class="pk-card-footer">
          <span class="pk-card-orden">{{ o.numero_orden }}</span>
          <div class="pk-card-acciones">
            <button v-if="o.estado === 'ingresado'" class="pk-btn-reimprimir" title="Reimprimir comprobante"
              @click="ordenParaImprimir = o">
              <i class="bi bi-printer"></i>
            </button>
            <button v-if="o.estado === 'pagado'" class="pk-btn-salida" title="Confirmar salida"
              :disabled="marcandoSalida === o.id"
              @click="confirmarSalida(o)">
              <i v-if="marcandoSalida === o.id" class="bi bi-arrow-repeat spin"></i>
              <i v-else class="bi bi-door-open-fill"></i>
              Salida
            </button>
          </div>
        </div>
      </div>
    </div>

  </div>

  <!-- ══ MODAL NUEVO INGRESO ═══════════════════════════════════════════════ -->
  <Teleport to="body">
    <div v-if="showModalNuevo" class="pk-modal-overlay" @click.self="cerrarModalNuevo">
      <div class="pk-modal">
        <div class="pk-modal-head">
          <span><i class="bi bi-car-front-fill"></i> Nuevo Ingreso</span>
          <button class="pk-modal-close" @click="cerrarModalNuevo"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="pk-modal-body">

          <!-- PLACA -->
          <div class="pk-field pk-field--required">
            <label>Placa <span class="req">*</span></label>
            <div class="pk-placa-wrap">
              <input v-model="form.placa" class="pk-input pk-placa-input"
                placeholder="Ej: ABC123" maxlength="10" autocomplete="off"
                @input="onPlacaInput"
                @blur="cerrarSugerencias"
                @focus="showSugerencias = sugerencias.length > 0"
                @keydown.escape="showSugerencias = false" />
              <i v-if="buscandoVehiculo" class="bi bi-arrow-repeat spin pk-placa-spin"></i>
              <i v-else-if="placaActiva" class="bi bi-exclamation-triangle-fill pk-placa-warn"></i>
              <i v-else-if="vehiculoEncontrado" class="bi bi-check-circle-fill pk-placa-ok"></i>

              <!-- Dropdown de sugerencias -->
              <div v-if="showSugerencias && sugerencias.length" class="pk-sugerencias">
                <button
                  v-for="v in sugerencias" :key="v.id"
                  type="button"
                  :class="['pk-sugerencia-item', { 'pk-sug--activo': v.activo_en_parking }]"
                  @mousedown.prevent="seleccionarSugerencia(v)"
                >
                  <div class="pk-sug-placa">{{ v.placa }}</div>
                  <div class="pk-sug-info">
                    <span>{{ v.propietario_nombre || 'Sin propietario' }}</span>
                    <span v-if="v.tipo_nombre" class="pk-sug-tipo">· {{ v.tipo_nombre }}</span>
                  </div>
                  <span v-if="v.activo_en_parking" class="pk-sug-badge">En Patio</span>
                </button>
              </div>
            </div>
            <small v-if="vehiculoEncontrado && !placaActiva" class="pk-hint-ok">
              <i class="bi bi-info-circle"></i> Vehículo registrado — datos cargados automáticamente
            </small>
            <div v-if="placaActiva" class="pk-alerta-activa">
              <i class="bi bi-exclamation-triangle-fill"></i>
              Esta placa ya tiene un ingreso activo en el parqueadero. Registre la salida antes de crear un nuevo ingreso.
            </div>
          </div>

          <!-- TIPO DE VEHÍCULO: solo para vehículos nuevos no registrados -->
          <div v-if="!vehiculoEncontrado" class="pk-field">
            <label>Tipo de Vehículo</label>
            <div v-if="vehicleTypes.length" class="pk-vtype-list">
              <button
                v-for="t in vehicleTypes" :key="t.id"
                type="button"
                :class="['pk-vtype-btn', { 'pk-vtype-btn--sel': form.vehicle_type_id === t.id }]"
                @click="form.vehicle_type_id = form.vehicle_type_id === t.id ? null : t.id"
              >
                <i v-if="form.vehicle_type_id === t.id" class="bi bi-check-circle-fill"></i>
                {{ t.nombre }}
              </button>
            </div>
            <small v-else class="pk-hint-vtype">Sin tipos configurados</small>
          </div>
          <!-- Vehículo existente: mostrar tipo ya guardado -->
          <div v-else-if="form.vehicle_type_id" class="pk-field">
            <label>Tipo de Vehículo</label>
            <span class="pk-tipo-readonly">
              <i class="bi bi-check-circle-fill" style="color:#16a34a"></i>
              {{ vehicleTypes.find(t => t.id === form.vehicle_type_id)?.nombre || 'Registrado' }}
            </span>
          </div>

          <!-- FOTO DEL VEHÍCULO -->
          <div class="pk-field">
            <label>Foto del Vehículo</label>
            <ImageUploaderPro
              :current-url="vehiculoFotoUrl"
              :show-remove="false"
              label="Sin foto · Toca para capturar"
              :output-width="800"
              :output-quality="0.82"
              @change="onFotoChange"
            />
          </div>

          <!-- SERVICIOS -->
          <div class="pk-field pk-field--required">
            <label>Servicios <span class="req">*</span></label>
            <div v-if="loadingProductos" class="pk-svc-loading">
              <i class="bi bi-arrow-repeat spin"></i> Cargando servicios…
            </div>
            <div v-else-if="productos.length === 0" class="pk-svc-empty">
              <i class="bi bi-exclamation-triangle"></i>
              Sin servicios configurados. Agrégalos en <strong>Productos Parking</strong>.
            </div>
            <div v-else class="pk-svc-list">
              <div
                v-for="prod in productos" :key="prod.id"
                :class="['pk-svc-item', { 'pk-svc-item--sel': estaSeleccionado(prod.id) }]"
              >
                <button type="button" class="pk-svc-toggle" @click="toggleItem(prod)">
                  <i :class="estaSeleccionado(prod.id) ? 'bi bi-check-square-fill' : 'bi bi-square'"></i>
                  <span>{{ prod.name }}</span>
                </button>
                <div v-if="estaSeleccionado(prod.id)" class="pk-counter pk-svc-counter">
                  <button type="button" @click="cambiarCantidad(prod, -1)">−</button>
                  <span>{{ itemsSeleccionados[prod.id]?.cantidad || 1 }}</span>
                  <button type="button" @click="cambiarCantidad(prod, 1)">+</button>
                </div>
              </div>
            </div>
            <small v-if="itemsActivos.length > 0" class="pk-svc-resumen">
              {{ itemsActivos.length }} tipo{{ itemsActivos.length !== 1 ? 's' : '' }} ·
              {{ totalCantidad }} unidad{{ totalCantidad !== 1 ? 'es' : '' }} seleccionadas
            </small>
          </div>

          <!-- OBSERVACIONES -->
          <div class="pk-field">
            <label>Observaciones</label>
            <textarea v-model="form.obs_portero" class="pk-input" rows="2"
              placeholder="Daños visibles, notas de ingreso…"></textarea>
          </div>

        </div>
        <div class="pk-modal-footer">
          <button class="pk-btn-cancel" @click="cerrarModalNuevo">Cancelar</button>
          <button class="pk-btn-guardar" :disabled="guardando || placaActiva" @click="guardarNuevo">
            <i v-if="guardando" class="bi bi-arrow-repeat spin"></i>
            <i v-else class="bi bi-check-lg"></i>
            {{ guardando ? 'Guardando…' : 'Registrar Ingreso' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <ComprobanteParkingIngreso
    v-if="ordenParaImprimir"
    :orden="ordenParaImprimir"
    :items="ordenParaImprimir.items || []"
    :company-name="companyStore.selectedCompany?.name || ''"
    :company-id="companyStore.selectedCompany?.id"
    tipo="ingreso"
    @close="ordenParaImprimir = null"
  />
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'
import { useCompanyStore } from '@/stores/companyStore'
import ImageUploaderPro from '@/components/common/ImageUploaderPro.vue'
import ComprobanteParkingIngreso from '@/components/parking/ComprobanteParkingIngreso.vue'

const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id)

const FILTROS = [
  { val: 'ingresado',  label: 'Ingresados'  },
  { val: 'registrado', label: 'Confirmados' },
  { val: 'pagado',     label: 'Para salir'  },
  { val: 'cancelado',  label: 'Cancelados'  },
]
const LABELS_ESTADO = {
  ingresado:  'Ingresado',
  registrado: 'Confirmado',
  pagado:     'Para salir',
  cancelado:  'Cancelado',
  salido:     'Salido',
}

const ordenes            = ref([])
const stats              = ref({ disponibles: 0, ocupadas: 0, total_plazas: 0, pct_ocupacion: 0 })

const pctIngresado  = computed(() => stats.value.total_plazas ? Math.round((stats.value.cnt_ingresado || 0) / stats.value.total_plazas * 100) : 0)
const pctRegistrado = computed(() => stats.value.total_plazas ? Math.round((stats.value.cnt_registrado || 0) / stats.value.total_plazas * 100) : 0)
const pctPagado     = computed(() => { const a = (stats.value.cnt_ingresado || 0) + (stats.value.cnt_registrado || 0); return a ? Math.round((stats.value.cnt_pagado || 0) / a * 100) : 0 })
const pctDisponible = computed(() => stats.value.total_plazas ? Math.round((stats.value.disponibles || 0) / stats.value.total_plazas * 100) : 0)
const productos          = ref([])
const vehicleTypes       = ref([])
const loading            = ref(false)
const loadingProductos   = ref(false)
const marcandoSalida     = ref(null)
function hoyLocal() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}
const fechaFiltro        = ref(hoyLocal())
const filtroEstado       = ref('')
const showModalNuevo     = ref(false)
const guardando          = ref(false)
const ordenParaImprimir  = ref(null)
const buscandoVehiculo   = ref(false)
const vehiculoEncontrado = ref(false)
const vehiculoFotoUrl    = ref(null)
const nuevaFotoBlob      = ref(null)
const sugerencias        = ref([])
const showSugerencias    = ref(false)
const placaActiva        = ref(false)

const form             = ref({ placa: '', vehicle_type_id: null, obs_portero: '' })
const itemsSeleccionados = ref({}) // { [product_id]: { product_id, nombre, cantidad, checked } }

const itemsActivos = computed(() =>
  Object.values(itemsSeleccionados.value).filter(i => i.checked)
)
const totalCantidad = computed(() =>
  itemsActivos.value.reduce((s, i) => s + (i.cantidad || 1), 0)
)

function estaSeleccionado(id) {
  return !!itemsSeleccionados.value[id]?.checked
}

function toggleItem(prod) {
  const k = prod.id
  if (itemsSeleccionados.value[k]?.checked) {
    itemsSeleccionados.value[k] = { ...itemsSeleccionados.value[k], checked: false }
  } else {
    itemsSeleccionados.value[k] = { product_id: prod.id, nombre: prod.name, cantidad: 1, checked: true }
  }
}

function cambiarCantidad(prod, delta) {
  const k = prod.id
  if (!itemsSeleccionados.value[k]) {
    itemsSeleccionados.value[k] = { product_id: prod.id, nombre: prod.name, cantidad: 1, checked: true }
    return
  }
  const nuevo = (itemsSeleccionados.value[k].cantidad || 1) + delta
  if (nuevo < 1) {
    itemsSeleccionados.value[k] = { ...itemsSeleccionados.value[k], checked: false, cantidad: 1 }
  } else {
    itemsSeleccionados.value[k] = { ...itemsSeleccionados.value[k], cantidad: nuevo, checked: true }
  }
}


async function cargar(silent = false) {
  if (!companyId.value) return
  if (!silent) loading.value = true
  try {
    // Órdenes: sin fecha → todos los activos. KPI stats: con fecha → métricas del día
    const [r1, r2] = await Promise.all([
      api.get('/api/parking/orders', { params: { company_id: companyId.value, estado: filtroEstado.value } }),
      api.get('/api/parking/stats',  { params: { company_id: companyId.value, fecha: fechaFiltro.value } }),
    ])
    ordenes.value = r1.data
    stats.value   = r2.data
  } catch { if (!silent) showToast('Error al cargar ingresos', 'error', 3000) }
  if (!silent) loading.value = false
}

async function confirmarSalida(orden) {
  marcandoSalida.value = orden.id
  try {
    await api.put(`/api/parking/orders/${orden.id}/salida`)
    showToast('Salida registrada', 'success', 2000)
    ordenes.value = ordenes.value.filter(o => o.id !== orden.id)
    const r2 = await api.get('/api/parking/stats', { params: { company_id: companyId.value, fecha: fechaFiltro.value } })
    stats.value = r2.data
  } catch (e) { showToast(e?.response?.data?.detail || 'Error al registrar salida', 'error', 3000) }
  marcandoSalida.value = null
}

async function cargarProductos() {
  if (!companyId.value) return
  loadingProductos.value = true
  try {
    const res = await api.get('/api/parking/products', { params: { company_id: companyId.value } })
    productos.value = res.data
  } catch {}
  loadingProductos.value = false
}

async function cargarVehicleTypes() {
  if (!companyId.value) return
  try {
    const res = await api.get('/api/parking/vehicle-types', { params: { company_id: companyId.value } })
    vehicleTypes.value = res.data
  } catch {}
}

let _autoRefresh = null
onMounted(() => {
  cargar(); cargarProductos(); cargarVehicleTypes()
  _autoRefresh = setInterval(() => { if (!showModalNuevo.value) cargar(true) }, 30000)
})
onUnmounted(() => clearInterval(_autoRefresh))

function abrirModalNuevo() {
  form.value               = { placa: '', vehicle_type_id: null, obs_portero: '' }
  vehiculoFotoUrl.value    = null
  nuevaFotoBlob.value      = null
  vehiculoEncontrado.value = false
  placaActiva.value        = false
  sugerencias.value        = []
  showSugerencias.value    = false
  itemsSeleccionados.value = {}
  showModalNuevo.value     = true
}
function cerrarModalNuevo() { showModalNuevo.value = false }

let placaTimer = null
function onPlacaInput() {
  form.value.placa           = form.value.placa.toUpperCase()
  vehiculoEncontrado.value   = false
  vehiculoFotoUrl.value      = null
  form.value.vehicle_type_id = null
  placaActiva.value          = false
  sugerencias.value          = []
  showSugerencias.value      = false
  clearTimeout(placaTimer)
  const p = form.value.placa.trim()
  if (p.length < 3) return
  placaTimer = setTimeout(() => buscarSugerencias(p), 400)
}

async function buscarSugerencias(placa) {
  buscandoVehiculo.value = true
  try {
    const res = await api.get(`/api/vehicles/placa/${encodeURIComponent(placa)}`, {
      params: { company_id: companyId.value },
    })
    sugerencias.value = res.data

    // Si hay coincidencia exacta, auto-aplicarla sin mostrar dropdown
    const exacto = res.data.find(v => v.placa === placa)
    if (exacto) {
      aplicarVehiculo(exacto)
      showSugerencias.value = false
    } else {
      showSugerencias.value = res.data.length > 0
    }
  } catch {}
  buscandoVehiculo.value = false
}

function aplicarVehiculo(v) {
  vehiculoEncontrado.value = true
  vehiculoFotoUrl.value    = v.foto_url || null
  placaActiva.value        = !!v.activo_en_parking
  if (v.vehicle_type_id) {
    form.value.vehicle_type_id = v.vehicle_type_id
  } else if (v.tipo_nombre) {
    const match = vehicleTypes.value.find(t =>
      t.nombre.toLowerCase() === v.tipo_nombre.toLowerCase()
    )
    if (match) form.value.vehicle_type_id = match.id
  }
}

function seleccionarSugerencia(v) {
  form.value.placa      = v.placa
  showSugerencias.value = false
  aplicarVehiculo(v)
}

function cerrarSugerencias() {
  // Timeout para que mousedown en sugerencia registre antes del blur
  setTimeout(() => { showSugerencias.value = false }, 150)
}

function onFotoChange(blob) {
  nuevaFotoBlob.value = blob
}

function blobToBase64(blob) {
  return new Promise(resolve => {
    const reader = new FileReader()
    reader.onload = e => resolve(e.target.result)
    reader.readAsDataURL(blob)
  })
}

async function guardarNuevo() {
  if (!form.value.placa.trim()) { showToast('La placa es requerida', 'warning', 2500); return }
  if (placaActiva.value) { showToast('Esta placa ya tiene un ingreso activo. Registre la salida primero.', 'warning', 3500); return }
  const items = itemsActivos.value
  if (items.length === 0) { showToast('Selecciona al menos un servicio', 'warning', 2500); return }

  let foto_url = vehiculoFotoUrl.value
  if (nuevaFotoBlob.value) {
    foto_url = await blobToBase64(nuevaFotoBlob.value)
  }

  guardando.value = true
  try {
    const tipoNombre = vehicleTypes.value.find(t => t.id === form.value.vehicle_type_id)?.nombre || null
    const res = await api.post('/api/parking/orders', {
      company_id:        companyId.value,
      placa:             form.value.placa.trim().toUpperCase(),
      vehicle_type_name: tipoNombre,
      foto_url,
      items:             items.map(i => ({ product_id: i.product_id, nombre: i.nombre, cantidad: i.cantidad })),
      obs_portero:       form.value.obs_portero || null,
    })
    showToast('Ingreso registrado', 'success', 2000)
    cerrarModalNuevo()
    await cargar()
    ordenParaImprimir.value = { ...res.data, items }
  } catch (e) { showToast(e?.response?.data?.detail || 'Error al registrar ingreso', 'error', 3000) }
  guardando.value = false
}

function fmtHora(dt) {
  if (!dt) return ''
  const d = new Date(String(dt).replace(' ', 'T'))
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  return `${h}:${m}`
}
</script>

<style scoped>
.pk-page { padding: 16px; max-width: 1200px; margin: 0 auto; }

/* KPI Bar */
.pk-kpi-bar { display: flex; align-items: stretch; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
.pk-btn-nuevo { display: flex; align-items: center; gap: 8px; padding: 10px 18px; background: #0d6efd; color: #fff; border: none; border-radius: 10px; font-size: .9rem; font-weight: 600; cursor: pointer; white-space: nowrap; }
.pk-btn-nuevo:hover { background: #0b5ed7; }
.pk-kpi-card { display: flex; align-items: center; gap: 10px; padding: 10px 16px; border-radius: 10px; color: #fff; font-weight: 600; min-width: 110px; flex: 1; }
.pk-kpi-card i { font-size: 1.4rem; opacity: .85; }
.pk-kpi-val  { display: block; font-size: 1.4rem; line-height: 1; }
.pk-kpi-lbl  { display: block; font-size: .72rem; opacity: .85; white-space: nowrap; }
.pk-kpi-ingresado  { background: #fd7e14; cursor: pointer; }
.pk-kpi-confirmado { background: #0d6efd; cursor: pointer; }
.pk-kpi-parasalir  { background: #198754; cursor: pointer; }
.pk-kpi-disponible { background: #6f42c1; }
.pk-kpi-pct        { display: block; font-size: .68rem; opacity: .85; white-space: nowrap; margin-top: 1px; }
.pk-kpi-card:hover { filter: brightness(1.1); }
.pk-kpi-active     { outline: 3px solid #fff; outline-offset: -3px; box-shadow: 0 0 0 3px rgba(0,0,0,.25); }

/* Barra de filtros: solo tabs de estado (fecha removida) */
.pk-filtro-bar    { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; flex-wrap: wrap; }

/* Grid vacío / loading */
.pk-loading { text-align: center; padding: 40px; color: #6c757d; }
.pk-empty   { text-align: center; padding: 60px 20px; color: #adb5bd; }
.pk-empty i { font-size: 2.5rem; display: block; margin-bottom: 8px; }

/* Cards */
.pk-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 12px; }
.pk-card { background: #fff; border-radius: 12px; padding: 14px; border: 2px solid #e9ecef; display: flex; flex-direction: column; gap: 6px; box-shadow: 0 1px 4px rgba(0,0,0,.06); }
.pk-card--ingresado  { border-color: #fd7e14; background: #fff8f0; }
.pk-card--registrado { border-color: #0d6efd; background: #f0f6ff; }
.pk-card--pagado     { border-color: #198754; background: #f0fff4; opacity: .85; }
.pk-card--cancelado  { opacity: .5; }
.pk-card-top { display: flex; align-items: center; justify-content: space-between; }
.pk-badge { font-size: .7rem; font-weight: 700; padding: 3px 8px; border-radius: 20px; text-transform: uppercase; }
.pk-badge--ingresado  { background: #fff3cd; color: #856404; }
.pk-badge--registrado { background: #cfe2ff; color: #084298; }
.pk-badge--pagado     { background: #d1e7dd; color: #0a3622; }
.pk-badge--cancelado  { background: #f8d7da; color: #842029; }
.pk-card-hora   { font-size: .75rem; color: #6c757d; }
.pk-card-placa  { font-size: 1.8rem; font-weight: 900; letter-spacing: 3px; text-align: center; border: 2px solid #212529; border-radius: 6px; padding: 4px 0; color: #212529; background: #fff; }
.pk-card-tipo   { text-align: center; font-size: .78rem; color: #6c757d; }
.pk-card-items { display: flex; flex-wrap: wrap; gap: 4px; }
.pk-svc-pill { display: inline-flex; align-items: center; gap: 4px; background: #e7f1ff; border: 1px solid #c2d8ff; padding: 3px 10px; border-radius: 20px; font-size: .78rem; font-weight: 500; color: #084298; }
.pk-svc-pill strong { font-weight: 700; }
.pk-card-obs  { font-size: .78rem; color: #6c757d; font-style: italic; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.pk-card-footer { display: flex; align-items: center; justify-content: space-between; margin-top: 4px; border-top: 1px solid #f1f3f5; padding-top: 6px; }
.pk-card-orden { font-size: .72rem; color: #adb5bd; font-family: monospace; }
.pk-card-acciones { display: flex; gap: 6px; }
.pk-btn-reimprimir { border: none; background: #f8f9fa; border-radius: 6px; padding: 4px 8px; cursor: pointer; color: #6c757d; font-size: .8rem; }
.pk-btn-reimprimir:hover { background: #e9ecef; }
.pk-btn-salida { border: none; background: #198754; color: #fff; border-radius: 6px; padding: 5px 10px; cursor: pointer; font-size: .8rem; font-weight: 600; display: flex; align-items: center; gap: 4px; }
.pk-btn-salida:hover:not(:disabled) { background: #157347; }
.pk-btn-salida:disabled { opacity: .6; cursor: default; }

/* Modal */
.pk-modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.5); z-index: 1050; display: flex; align-items: center; justify-content: center; padding: 16px; }
.pk-modal { background: #fff; border-radius: 14px; width: 100%; max-width: 500px; max-height: 92vh; overflow-y: auto; display: flex; flex-direction: column; }
.pk-modal-head { display: flex; align-items: center; justify-content: space-between; padding: 14px 18px; border-bottom: 1px solid #e9ecef; font-weight: 700; font-size: .95rem; position: sticky; top: 0; background: #fff; z-index: 1; }
.pk-modal-close { border: none; background: #f1f3f5; border-radius: 6px; padding: 5px 9px; cursor: pointer; }
.pk-modal-body { padding: 18px; display: flex; flex-direction: column; gap: 14px; flex: 1; }
.pk-modal-footer { padding: 14px 18px; border-top: 1px solid #e9ecef; display: flex; gap: 10px; justify-content: flex-end; position: sticky; bottom: 0; background: #fff; }

/* Campos */
.pk-field { display: flex; flex-direction: column; gap: 5px; }
.pk-field label { font-size: .82rem; font-weight: 600; color: #495057; }
.req { color: #dc3545; }
.pk-input { border: 1px solid #ced4da; border-radius: 8px; padding: 9px 12px; font-size: .9rem; outline: none; width: 100%; color: #212529; background: #fff; }
.pk-input:focus { border-color: #0d6efd; }

/* Placa */
.pk-placa-wrap { position: relative; }
.pk-placa-input { font-size: 1.4rem; font-weight: 900; letter-spacing: 3px; text-align: center; text-transform: uppercase; padding-right: 36px; }
.pk-placa-spin { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); color: #6c757d; font-size: 1rem; }
.pk-placa-ok   { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); color: #198754; font-size: 1rem; }
.pk-placa-warn { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); color: #dc3545; font-size: 1rem; }
.pk-hint-ok { font-size: .78rem; color: #198754; display: flex; align-items: center; gap: 4px; }

/* Autocomplete dropdown de placa */
.pk-sugerencias { position: absolute; top: calc(100% + 4px); left: 0; right: 0; background: #fff; border: 1px solid #ced4da; border-radius: 8px; box-shadow: 0 6px 20px rgba(0,0,0,.15); z-index: 200; max-height: 200px; overflow-y: auto; }
.pk-sugerencia-item { display: flex; align-items: center; gap: 10px; width: 100%; padding: 10px 14px; border: none; background: none; cursor: pointer; text-align: left; border-bottom: 1px solid #f1f3f5; }
.pk-sugerencia-item:last-child { border-bottom: none; }
.pk-sugerencia-item:hover { background: #f8f9fa; }
.pk-sug--activo { background: #fff8e1; }
.pk-sug--activo:hover { background: #fff0b3; }
.pk-sug-placa { font-size: 1rem; font-weight: 900; letter-spacing: 2px; color: #212529; min-width: 80px; }
.pk-sug-info  { flex: 1; font-size: .78rem; color: #6c757d; display: flex; gap: 4px; align-items: center; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.pk-sug-tipo  { color: #adb5bd; }
.pk-sug-badge { font-size: .68rem; font-weight: 700; background: #856404; color: #fff; padding: 2px 8px; border-radius: 20px; white-space: nowrap; flex-shrink: 0; }

/* Advertencia placa activa */
.pk-alerta-activa { background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 10px 14px; font-size: .82rem; font-weight: 600; color: #856404; display: flex; align-items: flex-start; gap: 8px; }
.pk-alerta-activa i { color: #dc3545; flex-shrink: 0; margin-top: 1px; }

/* Selector de tipo de vehículo — chips táctiles (sin select nativo) */
.pk-vtype-list { display: flex; flex-wrap: wrap; gap: 8px; }
.pk-vtype-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 10px 18px; border: 2px solid #dee2e6; border-radius: 10px;
  background: #fff; font-size: .9rem; font-weight: 500; color: #495057;
  cursor: pointer; transition: all .15s; min-height: 44px;
}
.pk-vtype-btn:hover    { border-color: #0d6efd; color: #0d6efd; }
.pk-vtype-btn--sel     { border-color: #0d6efd; background: #e7f1ff; color: #0d6efd; font-weight: 700; }
.pk-vtype-btn--sel i   { color: #0d6efd; }
.pk-hint-vtype         { font-size: .78rem; color: #adb5bd; }

/* Selector de servicios */
.pk-svc-loading { text-align: center; padding: 12px; color: #6c757d; font-size: .85rem; }
.pk-svc-empty   { text-align: center; padding: 12px; color: #6c757d; font-size: .85rem; background: #fff3cd; border-radius: 8px; }
.pk-svc-list  { display: flex; flex-direction: column; gap: 6px; max-height: 220px; overflow-y: auto; border: 1px solid #e9ecef; border-radius: 8px; padding: 8px; }
.pk-svc-item  { display: flex; align-items: center; justify-content: space-between; padding: 8px 10px; border-radius: 8px; border: 1px solid #e9ecef; transition: all .15s; }
.pk-svc-item--sel { background: #e7f1ff; border-color: #c2d8ff; }
.pk-svc-toggle { flex: 1; display: flex; align-items: center; gap: 8px; background: none; border: none; cursor: pointer; font-size: .88rem; color: #212529; text-align: left; padding: 0; }
.pk-svc-toggle i { font-size: 1rem; color: #6c757d; flex-shrink: 0; }
.pk-svc-item--sel .pk-svc-toggle i { color: #0d6efd; }
.pk-svc-counter { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.pk-counter { display: flex; align-items: center; gap: 6px; }
.pk-svc-counter button { width: 28px; height: 28px; border-radius: 50%; border: 1px solid #ced4da; background: #fff; font-size: 1rem; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.pk-svc-counter button:hover { background: #0d6efd; color: #fff; border-color: #0d6efd; }
.pk-svc-counter span { font-size: 1rem; font-weight: 700; min-width: 22px; text-align: center; color: #212529; }
.pk-svc-resumen { font-size: .78rem; color: #0d6efd; font-weight: 600; }

/* Acciones */
.pk-btn-cancel  { padding: 9px 18px; border: 1px solid #ced4da; border-radius: 8px; background: #fff; color: #495057; font-size: .9rem; cursor: pointer; }
.pk-btn-guardar { padding: 9px 20px; border: none; border-radius: 8px; background: #0d6efd; color: #fff; font-size: .9rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; }
.pk-btn-guardar:hover:not(:disabled) { background: #0b5ed7; }
.pk-btn-guardar:disabled { opacity: .6; cursor: default; }

.spin { animation: pk-spin .8s linear infinite; }
@keyframes pk-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

@media (max-width: 768px) {
  .pk-kpi-bar { gap: 8px; }
  .pk-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 10px; }
  .pk-card-placa { font-size: 1.5rem; }
}
@media (max-width: 576px) {
  .pk-page { padding: 10px; }
  .pk-kpi-bar { display: grid; grid-template-columns: 1fr 1fr; }
  .pk-btn-nuevo { grid-column: 1 / -1; justify-content: center; }
  .pk-grid { grid-template-columns: 1fr 1fr; gap: 8px; }
  .pk-card { padding: 10px; }
  .pk-card-placa { font-size: 1.3rem; letter-spacing: 2px; }
  .pk-filtro-bar { flex-direction: column; align-items: flex-start; }
  .pk-modal { max-width: 100%; border-radius: 14px 14px 0 0; }
  .pk-modal-overlay { align-items: flex-end; padding: 0; }
}
</style>
