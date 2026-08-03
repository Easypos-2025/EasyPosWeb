<template>
  <div class="pkc-page">

    <!-- ══ KPI BAR — clickables como filtros ════════════════════════════════ -->
    <div class="pkc-kpi-bar">
      <div :class="['pkc-kpi-card pkc-kpi-sinconfirmar', { 'pkc-kpi-active': filtroEstado === 'ingresado' }]"
        @click="filtroEstado = 'ingresado'; cargar()">
        <i class="bi bi-hourglass-split"></i>
        <div>
          <span class="pkc-kpi-val">{{ stats.cnt_ingresado || 0 }}</span>
          <span class="pkc-kpi-pct">{{ pctIngresado }}% de capacidad</span>
          <span class="pkc-kpi-lbl">Por confirmar</span>
        </div>
      </div>
      <div :class="['pkc-kpi-card pkc-kpi-pendiente', { 'pkc-kpi-active': filtroEstado === 'registrado' }]"
        @click="filtroEstado = 'registrado'; cargar()">
        <i class="bi bi-cash-coin"></i>
        <div>
          <span class="pkc-kpi-val">{{ stats.cnt_registrado || 0 }}</span>
          <span class="pkc-kpi-pct">{{ pctRegistrado }}% de capacidad</span>
          <span class="pkc-kpi-lbl">Pendientes cobro</span>
        </div>
      </div>
      <div :class="['pkc-kpi-card pkc-kpi-pagadas', { 'pkc-kpi-active': filtroEstado === 'pagado' }]"
        @click="filtroEstado = 'pagado'; cargar()">
        <i class="bi bi-check-circle-fill"></i>
        <div>
          <span class="pkc-kpi-val">{{ stats.cnt_pagado || 0 }}</span>
          <span v-if="pctPagado > 0" class="pkc-kpi-pct">{{ pctPagado }}% de activos</span>
          <span class="pkc-kpi-lbl">Pagadas · {{ fmtMini(stats.recaudo_hoy) }}</span>
        </div>
      </div>
      <div class="pkc-kpi-card pkc-kpi-disponible">
        <i class="bi bi-p-square-fill"></i>
        <div>
          <span class="pkc-kpi-val">{{ stats.disponibles || 0 }}</span>
          <span class="pkc-kpi-pct">{{ pctDisponible }}% libres · {{ stats.total_plazas || 0 }} plazas</span>
          <span class="pkc-kpi-lbl">Disponibles</span>
        </div>
      </div>
    </div>

    <!-- ══ KPI SERVICIOS ════════════════════════════════════════════════════ -->
    <div v-if="statsServicios.length" class="pkc-svc-kpi-bar">
      <div v-for="s in statsServicios" :key="s.servicio" class="pkc-svc-kpi-card">
        <span class="pkc-svc-kpi-nom">{{ s.servicio }}</span>
        <div class="pkc-svc-kpi-nums">
          <div class="pkc-svc-kpi-col">
            <span class="pkc-svc-kpi-val">{{ s.total_dia }}</span>
            <span class="pkc-svc-kpi-lbl">hoy</span>
          </div>
          <span class="pkc-svc-kpi-sep">|</span>
          <div class="pkc-svc-kpi-col">
            <span class="pkc-svc-kpi-val pkc-svc-kpi-val--activo">{{ s.activos_ahora }}</span>
            <span class="pkc-svc-kpi-lbl">en patio</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ══ FILTRO FECHA ══════════════════════════════════════════════════════ -->
    <div class="pkc-filtro-bar">
      <CustomDatePicker v-model="fechaFiltro" @update:modelValue="cargar" />
      <span class="pkc-filtro-hint">
        <i class="bi bi-info-circle"></i>
        Toca un indicador para filtrar
      </span>
    </div>

    <!-- ══ GRID DE TARJETAS ══════════════════════════════════════════════════ -->
    <div v-if="loading" class="pkc-loading">
      <i class="bi bi-arrow-repeat spin"></i> Cargando…
    </div>
    <div v-else-if="ordenes.length === 0" class="pkc-empty">
      <i class="bi bi-cash-coin"></i>
      <p>No hay órdenes pendientes de cobro</p>
      <small>Las órdenes aparecen aquí cuando el mesero confirma las personas</small>
    </div>
    <div v-else class="pkc-grid">
      <div
        v-for="o in ordenes" :key="o.id"
        :class="['pkc-card', `pkc-card--${o.estado}`]"
      >
        <div class="pkc-card-top">
          <span :class="['pkc-badge', `pkc-badge--${o.estado}`]">{{ LABELS_ESTADO[o.estado] }}</span>
          <span class="pkc-card-hora">{{ fmtHora(o.hora_ingreso) }}</span>
        </div>

        <div class="pkc-card-placa">{{ o.placa }}</div>
        <div v-if="o.tipo_vehiculo" class="pkc-card-tipo">{{ o.tipo_vehiculo }}</div>

        <div class="pkc-card-items">
          <template v-if="o.items && o.items.length">
            <span v-for="it in o.items" :key="it.nombre" class="pkc-item-pill">
              {{ it.nombre }} <strong>×{{ it.cantidad }}</strong>
            </span>
          </template>
          <span v-else class="pkc-item-pill">
            <i class="bi bi-list-check"></i> {{ o.adultos }} servicio{{ o.adultos !== 1 ? 's' : '' }}
          </span>
        </div>

        <div v-if="o.obs_portero || o.obs_mesero" class="pkc-obs-wrap">
          <div v-if="o.obs_portero" class="pkc-obs">
            <i class="bi bi-door-open"></i> {{ o.obs_portero }}
          </div>
          <div v-if="o.obs_mesero" class="pkc-obs pkc-obs-mesero">
            <i class="bi bi-person-badge"></i> {{ o.obs_mesero }}
          </div>
        </div>

        <div v-if="o.mesero_nombre" class="pkc-confirmado-por">
          <i class="bi bi-check2"></i> {{ o.mesero_nombre }}
        </div>

        <div class="pkc-card-footer">
          <span class="pkc-card-orden">{{ o.numero_orden }}</span>
          <div class="pkc-card-acciones">
            <button
              v-if="o.estado === 'ingresado'"
              class="pkc-btn-eliminar"
              title="Cancelar ingreso"
              @click="abrirCancelacion(o)"
            >
              <i class="bi bi-trash3"></i>
            </button>
            <button v-if="o.estado === 'registrado'" class="pkc-btn-pagar" @click="abrirCobro(o)">
              <i class="bi bi-cash-coin"></i> Cobrar
            </button>
            <button v-else-if="o.estado === 'pagado'" class="pkc-btn-reimprimir" @click="abrirReimpresion(o)">
              <i class="bi bi-printer-fill"></i> Reimprimir
            </button>
          </div>
        </div>
      </div>
    </div>

  </div>

  <!-- ══ MODAL COBRO ══════════════════════════════════════════════════════════ -->
  <div v-if="showCobro" class="pkc-overlay" @click.self="showCobro = false">
    <div class="pkc-modal">

      <div class="pkc-modal-header">
        <div>
          <h5><i class="bi bi-cash-coin me-2"></i>Liquidar Parking</h5>
          <span class="pkc-modal-sub">{{ ordenCobro?.numero_orden }}</span>
        </div>
        <button class="pkc-btn-close" @click="showCobro = false"><i class="bi bi-x-lg"></i></button>
      </div>

      <!-- Info orden -->
      <div class="pkc-cobro-info">
        <div class="pkc-cobro-placa">{{ ordenCobro?.placa }}</div>
        <div class="pkc-cobro-personas">
          <span><i class="bi bi-person-fill"></i> {{ ordenCobro?.adultos }} adulto{{ ordenCobro?.adultos !== 1 ? 's' : '' }}</span>
          <span v-if="ordenCobro?.ninos > 0"><i class="bi bi-person-hearts"></i> {{ ordenCobro?.ninos }} niño{{ ordenCobro?.ninos !== 1 ? 's' : '' }}</span>
          <span v-if="ordenCobro?.mascotas > 0"><i class="bi bi-circle-fill" style="font-size:.5rem"></i> {{ ordenCobro?.mascotas }} mascota{{ ordenCobro?.mascotas !== 1 ? 's' : '' }}</span>
        </div>
        <div v-if="ordenCobro?.mesero_nombre" class="pkc-cobro-confirmado">
          <i class="bi bi-check2-circle"></i> Confirmado por: {{ ordenCobro.mesero_nombre }}
        </div>
      </div>

      <!-- Lista de servicios -->
      <div class="pkc-modal-body">
        <div v-if="loadingProductos" class="pkc-loading-sm">
          <i class="bi bi-arrow-repeat spin"></i> Cargando servicios…
        </div>
        <div v-else-if="productos.length === 0" class="pkc-sin-productos">
          <i class="bi bi-box-seam"></i>
          <p>No hay servicios configurados</p>
          <small>Crea los productos en <strong>Productos Parking</strong> del menú</small>
        </div>
        <div v-else>
          <div class="pkc-servicios-title">Servicios a cobrar <span style="font-weight:400;color:#0d6efd;font-size:.72rem;">· Pre-cargados del ingreso</span></div>
          <div class="pkc-servicios-list">
            <div
              v-for="p in productos" :key="p.id"
              :class="['pkc-servicio-row', { selected: seleccion[p.id]?.activo }]"
            >
              <label class="pkc-servicio-check">
                <input
                  type="checkbox"
                  :checked="seleccion[p.id]?.activo"
                  @change="toggleServicio(p)"
                />
                <span class="pkc-servicio-nombre">{{ p.name }}</span>
              </label>
              <div class="pkc-servicio-right">
                <span class="pkc-servicio-precio">{{ fmt(p.base_price) }}</span>
                <span v-if="p.tax_rate > 0" class="pkc-servicio-iva">+{{ p.tax_rate }}% IVA</span>
                <div v-if="seleccion[p.id]?.activo" class="pkc-qty-wrap">
                  <button class="pkc-qty-btn" @click="cambiarCantidad(p.id, -1)">−</button>
                  <span class="pkc-qty-val">{{ seleccion[p.id].cantidad }}</span>
                  <button class="pkc-qty-btn" @click="cambiarCantidad(p.id, 1)">+</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Totales -->
      <div v-if="lineasSeleccionadas.length > 0" class="pkc-totales">
        <div class="pkc-total-row" v-for="l in lineasSeleccionadas" :key="l.product_id">
          <span>{{ l.nombre }} × {{ l.cantidad }}</span>
          <span>{{ fmt(l.subtotal_bruto) }}</span>
        </div>
        <div class="pkc-total-sep"></div>
        <div class="pkc-total-row pkc-total-sub">
          <span>Subtotal</span>
          <span>{{ fmt(totalBruto) }}</span>
        </div>
        <div v-if="totalImpuesto > 0" class="pkc-total-row pkc-total-iva">
          <span>Impuestos</span>
          <span>{{ fmt(totalImpuesto) }}</span>
        </div>
        <div class="pkc-total-row pkc-total-final">
          <span>TOTAL</span>
          <span>{{ fmt(totalFinal) }}</span>
        </div>
      </div>

      <div class="pkc-modal-footer">
        <button class="pkc-btn-cancelar" @click="showCobro = false">Cancelar</button>
        <button
          class="pkc-btn-confirmar"
          :disabled="lineasSeleccionadas.length === 0 || pagando"
          @click="confirmarCobro"
        >
          <i v-if="pagando" class="bi bi-arrow-repeat spin"></i>
          <i v-else class="bi bi-check-lg"></i>
          {{ pagando ? 'Procesando…' : `Confirmar cobro${totalFinal > 0 ? ' · ' + fmt(totalFinal) : ''}` }}
        </button>
      </div>

    </div>
  </div>

  <!-- ══ MODAL CANCELACIÓN ══════════════════════════════════════════════════ -->
  <div v-if="showCancelacion" class="pkc-overlay" @click.self="showCancelacion = false">
    <div class="pkc-modal pkc-modal--cancel">
      <div class="pkc-modal-header">
        <div>
          <h5><i class="bi bi-trash3 me-2" style="color:#dc3545"></i>Cancelar Ingreso</h5>
          <span class="pkc-modal-sub">{{ ordenCancelacion?.numero_orden }} · {{ ordenCancelacion?.placa }}</span>
        </div>
        <button class="pkc-btn-close" @click="showCancelacion = false"><i class="bi bi-x-lg"></i></button>
      </div>
      <div class="pkc-cancel-body">
        <div class="pkc-cancel-warn">
          <i class="bi bi-exclamation-triangle-fill"></i>
          Esta acción cancelará el ingreso y quedará registrado en el historial de cancelaciones.
        </div>
        <label class="pkc-cancel-label">Motivo de cancelación <span style="color:#dc3545">*</span></label>
        <textarea
          v-model="motivoCancelacion"
          class="pkc-cancel-textarea"
          rows="3"
          placeholder="Ej: Vehículo salió inmediatamente, era una prueba, visita familiar sin cargo…"
          maxlength="300"
        ></textarea>
        <small class="pkc-cancel-count">{{ motivoCancelacion.length }}/300</small>
      </div>
      <div class="pkc-modal-footer">
        <button class="pkc-btn-cancelar" @click="showCancelacion = false">Volver</button>
        <button
          class="pkc-btn-cancel-confirm"
          :disabled="!motivoCancelacion.trim() || cancelando"
          @click="confirmarCancelacion"
        >
          <i v-if="cancelando" class="bi bi-arrow-repeat spin"></i>
          <i v-else class="bi bi-trash3"></i>
          {{ cancelando ? 'Cancelando…' : 'Confirmar cancelación' }}
        </button>
      </div>
    </div>
  </div>

  <!-- ══ COMPROBANTE DE SALIDA / REIMPRESIÓN ═════════════════════════════════ -->
  <ComprobanteParkingIngreso
    v-if="ordenParaSalida"
    :orden="ordenParaSalida"
    :items="itemsParaSalida"
    :company-name="companyStore.selectedCompany?.name || ''"
    :company-id="companyStore.selectedCompany?.id"
    tipo="salida"
    @close="ordenParaSalida = null; itemsParaSalida = []"
  />
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'
import { useCompanyStore } from '@/stores/companyStore'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'
import ComprobanteParkingIngreso from '@/components/parking/ComprobanteParkingIngreso.vue'

const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id)

const LABELS_ESTADO = {
  ingresado:  'Ingresado',
  registrado: 'Pendiente cobro',
  pagado:     'Pagado',
  cancelado:  'Cancelado',
}

// ── Estado principal ──────────────────────────────────────────────────────────
const ordenes       = ref([])
const stats              = ref({ cnt_ingresado: 0, cnt_registrado: 0, cnt_pagado: 0, recaudo_hoy: 0 })
const statsServicios     = ref([])
const loading       = ref(false)
function hoyLocal() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}
const fechaFiltro   = ref(hoyLocal())
const filtroEstado  = ref('registrado')
const ordenParaSalida   = ref(null)
const itemsParaSalida   = ref([])

// ── Modal cobro ───────────────────────────────────────────────────────────────
const showCobro        = ref(false)
const ordenCobro       = ref(null)
const productos        = ref([])
const loadingProductos = ref(false)
const seleccion        = ref({})  // { [product_id]: { activo, cantidad } }
const pagando          = ref(false)

// ── Líneas y totales del modal ────────────────────────────────────────────────
const lineasSeleccionadas = computed(() => {
  return productos.value
    .filter(p => seleccion.value[p.id]?.activo)
    .map(p => {
      const qty        = seleccion.value[p.id].cantidad
      const bruto      = p.base_price * qty
      const iva        = bruto * ((p.tax_rate || 0) / 100)
      return {
        product_id:     p.id,
        nombre:         p.name,
        precio_unitario: p.base_price,
        impuesto_pct:   p.tax_rate || 0,
        cantidad:       qty,
        subtotal_bruto: bruto,
        impuesto:       iva,
        subtotal:       bruto + iva,
      }
    })
})

const totalBruto    = computed(() => lineasSeleccionadas.value.reduce((s, l) => s + l.subtotal_bruto, 0))
const totalImpuesto = computed(() => lineasSeleccionadas.value.reduce((s, l) => s + l.impuesto, 0))
const totalFinal    = computed(() => lineasSeleccionadas.value.reduce((s, l) => s + l.subtotal, 0))

const pctIngresado  = computed(() => stats.value.total_plazas ? Math.round((stats.value.cnt_ingresado || 0) / stats.value.total_plazas * 100) : 0)
const pctRegistrado = computed(() => stats.value.total_plazas ? Math.round((stats.value.cnt_registrado || 0) / stats.value.total_plazas * 100) : 0)
const pctPagado     = computed(() => { const a = (stats.value.cnt_ingresado || 0) + (stats.value.cnt_registrado || 0); return a ? Math.round((stats.value.cnt_pagado || 0) / a * 100) : 0 })
const pctDisponible = computed(() => stats.value.total_plazas ? Math.round((stats.value.disponibles || 0) / stats.value.total_plazas * 100) : 0)

// ── Carga órdenes + stats ─────────────────────────────────────────────────────
async function cargar(silent = false) {
  if (!companyId.value) return
  if (!silent) loading.value = true
  try {
    const [r1, r2, r3] = await Promise.all([
      api.get('/api/parking/orders', {
        params: { company_id: companyId.value, fecha: fechaFiltro.value, estado: filtroEstado.value },
      }),
      api.get('/api/parking/stats', {
        params: { company_id: companyId.value, fecha: fechaFiltro.value },
      }),
      api.get('/api/parking/stats/servicios', {
        params: { company_id: companyId.value, fecha: fechaFiltro.value },
      }),
    ])
    ordenes.value        = r1.data
    stats.value          = r2.data
    statsServicios.value = r3.data
  } catch {
    if (!silent) showToast('Error al cargar órdenes', 'error', 3000)
  }
  if (!silent) loading.value = false
}

// ── Abrir modal cobro ─────────────────────────────────────────────────────────
async function abrirCobro(orden) {
  ordenCobro.value = orden
  seleccion.value  = {}
  showCobro.value  = true
  loadingProductos.value = true
  try {
    const calls = [api.get(`/api/parking/orders/${orden.id}/items`)]
    if (productos.value.length === 0) {
      calls.push(api.get('/api/parking/products', { params: { company_id: companyId.value } }))
    }
    const [rItems, rProds] = await Promise.all(calls)
    if (rProds) productos.value = rProds.data
    // Pre-popular con ítems ya confirmados
    for (const item of rItems.data) {
      if (item.product_id) {
        seleccion.value[item.product_id] = { activo: true, cantidad: item.cantidad }
      }
    }
  } catch {
    showToast('Error al cargar servicios', 'error', 3000)
  }
  loadingProductos.value = false
}

function toggleServicio(p) {
  if (seleccion.value[p.id]?.activo) {
    seleccion.value[p.id] = { activo: false, cantidad: 1 }
  } else {
    seleccion.value[p.id] = { activo: true, cantidad: 1 }
  }
}

function cambiarCantidad(pid, delta) {
  const actual = seleccion.value[pid]?.cantidad || 1
  const nueva  = Math.max(1, actual + delta)
  seleccion.value[pid] = { activo: true, cantidad: nueva }
}

// ── Confirmar cobro ───────────────────────────────────────────────────────────
async function confirmarCobro() {
  if (lineasSeleccionadas.value.length === 0) return
  pagando.value = true
  try {
    const items = lineasSeleccionadas.value.map(l => ({
      product_id:      l.product_id,
      nombre:          l.nombre,
      precio_unitario: l.precio_unitario,
      impuesto_pct:    l.impuesto_pct,
      cantidad:        l.cantidad,
      subtotal:        l.subtotal,
    }))
    await api.put(`/api/parking/orders/${ordenCobro.value.id}/pagar`, { items })
    showToast('Orden cobrada correctamente', 'success', 2500)

    const actualizada = { ...ordenCobro.value, estado: 'pagado', hora_salida: new Date().toISOString() }
    const idx = ordenes.value.findIndex(o => o.id === ordenCobro.value.id)
    if (idx !== -1) ordenes.value[idx] = actualizada
    if (filtroEstado.value === 'registrado') ordenes.value = ordenes.value.filter(o => o.id !== ordenCobro.value.id)
    const r2 = await api.get('/api/parking/stats', { params: { company_id: companyId.value, fecha: fechaFiltro.value } })
    stats.value = r2.data

    showCobro.value       = false
    itemsParaSalida.value = lineasSeleccionadas.value.map(l => ({ nombre: l.nombre, cantidad: l.cantidad }))
    ordenParaSalida.value = actualizada
  } catch (e) {
    showToast(e?.response?.data?.detail || 'Error al cobrar', 'error', 3000)
  }
  pagando.value = false
}

// ── Cancelar ingreso ──────────────────────────────────────────────────────────
const showCancelacion   = ref(false)
const ordenCancelacion  = ref(null)
const motivoCancelacion = ref('')
const cancelando        = ref(false)

function abrirCancelacion(orden) {
  ordenCancelacion.value  = orden
  motivoCancelacion.value = ''
  showCancelacion.value   = true
}

async function confirmarCancelacion() {
  if (!motivoCancelacion.value.trim()) {
    showToast('El motivo es requerido', 'warning', 2500)
    return
  }
  cancelando.value = true
  try {
    await api.put(`/api/parking/orders/${ordenCancelacion.value.id}/cancelar`, {
      company_id: companyId.value,
      motivo:     motivoCancelacion.value.trim(),
    })
    showToast('Ingreso cancelado y registrado en historial', 'success', 2500)
    ordenes.value = ordenes.value.filter(o => o.id !== ordenCancelacion.value.id)
    showCancelacion.value = false
    const r2 = await api.get('/api/parking/stats', { params: { company_id: companyId.value, fecha: fechaFiltro.value } })
    stats.value = r2.data
  } catch (e) {
    showToast(e?.response?.data?.detail || 'Error al cancelar', 'error', 3000)
  }
  cancelando.value = false
}

// ── Reimprimir tiquete de salida ──────────────────────────────────────────────
async function abrirReimpresion(orden) {
  try {
    const res = await api.get(`/api/parking/orders/${orden.id}/items`)
    itemsParaSalida.value = res.data.map(i => ({ nombre: i.nombre, cantidad: i.cantidad }))
  } catch {
    itemsParaSalida.value = []
  }
  ordenParaSalida.value = orden
}

// ── Utilidades ────────────────────────────────────────────────────────────────
function fmtHora(dt) {
  if (!dt) return ''
  const d = new Date(String(dt).replace(' ', 'T'))
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  return `${h}:${m}`
}

function fmt(val) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(val || 0)
}

function fmtMini(val) {
  if (!val) return ''
  if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`
  if (val >= 1000)    return `$${(val / 1000).toFixed(0)}K`
  return fmt(val)
}

watch(companyId, (v) => { if (v) cargar() }, { immediate: true })

let _autoRefresh = null
onMounted(() => {
  _autoRefresh = setInterval(() => { if (!showCobro.value) cargar(true) }, 30000)
})
onUnmounted(() => clearInterval(_autoRefresh))
</script>

<style scoped>
.pkc-page { padding: 16px; max-width: 1200px; margin: 0 auto; }

/* ── KPI bar ── */
.pkc-kpi-bar { display: flex; align-items: stretch; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
.pkc-kpi-card {
  display: flex; align-items: center; gap: 12px; padding: 12px 20px;
  border-radius: 10px; color: #fff; font-weight: 600; flex: 1; min-width: 130px;
}
.pkc-kpi-card i { font-size: 1.5rem; opacity: .85; }
.pkc-kpi-val    { display: block; font-size: 1.6rem; line-height: 1; }
.pkc-kpi-pct    { display: block; font-size: .68rem; opacity: .85; white-space: nowrap; margin-top: 1px; }
.pkc-kpi-lbl    { display: block; font-size: .72rem; opacity: .85; white-space: nowrap; }
.pkc-kpi-sinconfirmar { background: #fd7e14; cursor: pointer; transition: filter .15s; }
.pkc-kpi-pendiente    { background: #0d6efd; cursor: pointer; transition: filter .15s; }
.pkc-kpi-pagadas      { background: #198754; cursor: pointer; transition: filter .15s; }
.pkc-kpi-disponible   { background: #6f42c1; cursor: default; }
.pkc-kpi-card:hover   { filter: brightness(1.1); }
.pkc-kpi-active       { outline: 3px solid #fff; outline-offset: 2px; box-shadow: 0 0 0 5px rgba(0,0,0,.25); }

/* ── Filtro ── */
.pkc-filtro-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; flex-wrap: wrap; }
.pkc-filtro-hint { font-size: .78rem; color: #6c757d; display: flex; align-items: center; gap: 4px; }
.pkc-tab {
  padding: 6px 16px; border-radius: 20px; border: 1px solid #dee2e6;
  background: #fff; font-size: .82rem; cursor: pointer; transition: all .15s;
}
.pkc-tab.active { background: #0d6efd; color: #fff; border-color: #0d6efd; }

/* ── Carga / vacío ── */
.pkc-loading { text-align: center; padding: 40px; color: #6c757d; }
.pkc-empty   { text-align: center; padding: 60px 20px; color: #adb5bd; }
.pkc-empty i { font-size: 2.5rem; display: block; margin-bottom: 8px; }
.pkc-empty small { font-size: .8rem; display: block; margin-top: 6px; }

/* ── Grid tarjetas ── */
.pkc-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }
.pkc-card {
  background: #fff; border-radius: 12px; padding: 14px;
  border: 2px solid #dee2e6; display: flex; flex-direction: column; gap: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
}
.pkc-card--ingresado  { border-color: #fd7e14; background: #fff8f0; }
.pkc-card--registrado { border-color: #0d6efd; background: #f0f6ff; }
.pkc-card--pagado     { border-color: #198754; background: #f0fff4; opacity: .85; }

.pkc-card-top { display: flex; align-items: center; justify-content: space-between; }
.pkc-badge {
  font-size: .7rem; font-weight: 700; padding: 3px 8px; border-radius: 20px;
  text-transform: uppercase; letter-spacing: .3px;
}
.pkc-badge--registrado { background: #cfe2ff; color: #084298; }
.pkc-badge--pagado     { background: #d1e7dd; color: #0a3622; }
.pkc-card-hora { font-size: .75rem; color: #6c757d; }

.pkc-card-placa {
  font-size: 1.9rem; font-weight: 900; letter-spacing: 3px;
  text-align: center; color: #212529; line-height: 1;
  border: 2px solid #212529; border-radius: 6px; padding: 6px 0;
}
.pkc-card-tipo { text-align: center; font-size: .78rem; color: #6c757d; }

.pkc-card-items { display: flex; flex-wrap: wrap; gap: 4px; }
.pkc-item-pill {
  display: inline-flex; align-items: center; gap: 4px; font-size: .82rem;
  padding: 3px 9px; border-radius: 8px; background: #e7f1ff; color: #084298;
  border: 1px solid #c2d8ff;
}
.pkc-item-pill strong { font-weight: 700; }

.pkc-svc-pill {
  display: flex; align-items: center; gap: 6px; font-size: .85rem; font-weight: 600;
  padding: 4px 10px; border-radius: 8px; background: #e7f1ff; color: #084298;
  border: 1px solid #c2d8ff;
}

.pkc-obs-wrap { display: flex; flex-direction: column; gap: 4px; }
.pkc-obs {
  font-size: .78rem; color: #6c757d; font-style: italic;
  display: flex; align-items: flex-start; gap: 5px; padding: 4px 8px;
  background: #f8f9fa; border-radius: 6px;
}
.pkc-obs-mesero { background: #e8f4fd; color: #055160; }

.pkc-confirmado-por { font-size: .75rem; color: #198754; display: flex; align-items: center; gap: 5px; }

.pkc-card-footer {
  display: flex; align-items: center; justify-content: space-between;
  margin-top: 4px; border-top: 1px solid #f1f3f5; padding-top: 8px;
}
.pkc-card-orden   { font-size: .72rem; color: #adb5bd; font-family: monospace; }
.pkc-card-acciones { display: flex; align-items: center; gap: 6px; }

.pkc-btn-eliminar {
  display: flex; align-items: center; justify-content: center;
  width: 32px; height: 32px;
  border: 1.5px solid #dc3545; border-radius: 8px; background: #fff; color: #dc3545;
  font-size: .85rem; cursor: pointer; transition: all .15s; flex-shrink: 0;
}
.pkc-btn-eliminar:hover { background: #dc3545; color: #fff; }

.pkc-btn-pagar {
  display: flex; align-items: center; gap: 6px; padding: 8px 16px;
  border: none; border-radius: 8px; background: #198754; color: #fff;
  font-size: .85rem; font-weight: 600; cursor: pointer; transition: background .15s;
}
.pkc-btn-pagar:hover { background: #157347; }

.pkc-ya-pagado { font-size: .78rem; color: #198754; display: flex; align-items: center; gap: 4px; }
.pkc-btn-reimprimir {
  display: flex; align-items: center; gap: 5px; padding: 6px 12px;
  border: 1px solid #6c757d; border-radius: 8px; background: #fff; color: #6c757d;
  font-size: .8rem; cursor: pointer; transition: all .15s;
}
.pkc-btn-reimprimir:hover { background: #6c757d; color: #fff; }

/* ── Modal overlay ── */
.pkc-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.5);
  display: flex; align-items: center; justify-content: center;
  z-index: 1050; padding: 12px;
}
.pkc-modal {
  background: #fff; border-radius: 16px; width: 100%; max-width: 520px;
  max-height: 90vh; display: flex; flex-direction: column; overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,.25);
}

/* ── Modal header ── */
.pkc-modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 20px; border-bottom: 1px solid #e9ecef;
}
.pkc-modal-header h5 { margin: 0; font-weight: 700; font-size: 1rem; }
.pkc-modal-sub { font-size: .78rem; color: #6c757d; font-family: monospace; }
.pkc-btn-close {
  border: none; background: none; font-size: 1rem; color: #6c757d; cursor: pointer; padding: 4px 8px;
}

/* ── Info orden ── */
.pkc-cobro-info {
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
  padding: 12px 20px; background: #f8f9fa; border-bottom: 1px solid #e9ecef;
}
.pkc-cobro-placa {
  font-size: 1.3rem; font-weight: 900; letter-spacing: 2px;
  border: 2px solid #212529; border-radius: 6px; padding: 4px 10px;
}
.pkc-cobro-personas { display: flex; gap: 10px; flex-wrap: wrap; }
.pkc-cobro-personas span {
  display: flex; align-items: center; gap: 4px; font-size: .84rem;
  font-weight: 600; background: #fff; padding: 4px 10px; border-radius: 8px;
  border: 1px solid #dee2e6;
}
.pkc-cobro-confirmado { font-size: .78rem; color: #198754; display: flex; align-items: center; gap: 5px; width: 100%; }

/* ── Body modal ── */
.pkc-modal-body { flex: 1; overflow-y: auto; padding: 16px 20px; }
.pkc-loading-sm { text-align: center; padding: 20px; color: #6c757d; font-size: .9rem; }
.pkc-sin-productos { text-align: center; padding: 30px 20px; color: #adb5bd; }
.pkc-sin-productos i { font-size: 2rem; display: block; margin-bottom: 8px; }
.pkc-sin-productos p { margin: 0 0 6px; font-size: .9rem; }
.pkc-sin-productos small { font-size: .8rem; }

.pkc-servicios-title {
  font-size: .78rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: .5px; color: #6c757d; margin-bottom: 10px;
}
.pkc-servicios-list { display: flex; flex-direction: column; gap: 8px; }

.pkc-servicio-row {
  display: flex; align-items: center; justify-content: space-between; gap: 10px;
  padding: 10px 14px; border: 1.5px solid #e9ecef; border-radius: 10px;
  transition: border-color .15s, background .15s; cursor: pointer;
}
.pkc-servicio-row.selected { border-color: #0d6efd; background: #f0f6ff; }

.pkc-servicio-check {
  display: flex; align-items: center; gap: 10px; cursor: pointer; flex: 1; min-width: 0;
}
.pkc-servicio-check input[type="checkbox"] { width: 18px; height: 18px; flex-shrink: 0; cursor: pointer; accent-color: #0d6efd; }
.pkc-servicio-nombre { font-size: .9rem; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.pkc-servicio-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.pkc-servicio-precio { font-size: .88rem; font-weight: 700; color: #212529; }
.pkc-servicio-iva { font-size: .72rem; color: #6c757d; }

.pkc-qty-wrap { display: flex; align-items: center; gap: 4px; }
.pkc-qty-btn {
  width: 26px; height: 26px; border: 1.5px solid #0d6efd; border-radius: 6px;
  background: #fff; color: #0d6efd; font-size: 1rem; font-weight: 700;
  cursor: pointer; display: flex; align-items: center; justify-content: center; line-height: 1;
}
.pkc-qty-btn:hover { background: #0d6efd; color: #fff; }
.pkc-qty-val { font-size: .9rem; font-weight: 700; min-width: 20px; text-align: center; }

/* ── Totales ── */
.pkc-totales {
  border-top: 1px solid #e9ecef; padding: 14px 20px;
  display: flex; flex-direction: column; gap: 6px;
}
.pkc-total-row {
  display: flex; justify-content: space-between; align-items: center;
  font-size: .85rem; color: #495057;
}
.pkc-total-sep { height: 1px; background: #e9ecef; margin: 4px 0; }
.pkc-total-sub  { font-weight: 600; color: #212529; }
.pkc-total-iva  { color: #6c757d; }
.pkc-total-final {
  font-size: 1.1rem; font-weight: 800; color: #198754;
  padding-top: 4px; border-top: 2px solid #198754; margin-top: 2px;
}

/* ── Footer modal ── */
.pkc-modal-footer {
  display: flex; gap: 10px; padding: 14px 20px; border-top: 1px solid #e9ecef;
  justify-content: flex-end;
}
.pkc-btn-cancelar {
  padding: 10px 20px; border: 1.5px solid #dee2e6; border-radius: 8px;
  background: #fff; color: #6c757d; font-size: .9rem; cursor: pointer;
}
.pkc-btn-cancelar:hover { background: #f8f9fa; }
.pkc-btn-confirmar {
  display: flex; align-items: center; gap: 6px; padding: 10px 22px;
  border: none; border-radius: 8px; background: #198754; color: #fff;
  font-size: .9rem; font-weight: 700; cursor: pointer; transition: background .15s;
}
.pkc-btn-confirmar:hover:not(:disabled) { background: #157347; }
.pkc-btn-confirmar:disabled { opacity: .55; cursor: default; }

.spin { animation: pkc-spin .8s linear infinite; }
@keyframes pkc-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* ── Modal cancelación ── */
.pkc-modal--cancel  { max-width: 440px; }
.pkc-cancel-body    { padding: 18px 20px; display: flex; flex-direction: column; gap: 10px; }
.pkc-cancel-warn {
  background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px;
  padding: 12px 14px; font-size: .82rem; font-weight: 600; color: #856404;
  display: flex; align-items: flex-start; gap: 8px;
}
.pkc-cancel-warn i { color: #dc3545; flex-shrink: 0; margin-top: 2px; }
.pkc-cancel-label   { font-size: .82rem; font-weight: 600; color: #495057; }
.pkc-cancel-textarea {
  border: 1.5px solid #ced4da; border-radius: 8px; padding: 10px 12px;
  font-size: .88rem; outline: none; resize: vertical; width: 100%; color: #212529;
  font-family: inherit;
}
.pkc-cancel-textarea:focus { border-color: #dc3545; }
.pkc-cancel-count   { font-size: .72rem; color: #adb5bd; text-align: right; }
.pkc-btn-cancel-confirm {
  display: flex; align-items: center; gap: 6px; padding: 10px 20px;
  border: none; border-radius: 8px; background: #dc3545; color: #fff;
  font-size: .9rem; font-weight: 700; cursor: pointer; transition: background .15s;
}
.pkc-btn-cancel-confirm:hover:not(:disabled) { background: #bb2d3b; }
.pkc-btn-cancel-confirm:disabled { opacity: .55; cursor: default; }

/* ── Responsive ── */
@media (max-width: 768px) {
  .pkc-kpi-card { padding: 10px 14px; }
  .pkc-kpi-val  { font-size: 1.3rem; }
  .pkc-grid     { grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 10px; }
  .pkc-card-placa { font-size: 1.5rem; }
  .pkc-modal { max-height: 95vh; border-radius: 12px 12px 0 0; margin-top: auto; }
}
@media (max-width: 576px) {
  .pkc-page { padding: 10px; }
  .pkc-kpi-bar { display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px; }
  .pkc-kpi-card { padding: 8px 10px; gap: 6px; min-width: unset; }
  .pkc-kpi-card i { font-size: 1.1rem; }
  .pkc-kpi-val { font-size: 1.1rem; }
  .pkc-grid { grid-template-columns: 1fr; gap: 10px; }
  .pkc-filtro-bar { flex-direction: column; align-items: flex-start; gap: 8px; }
  .pkc-cobro-personas { flex-direction: column; gap: 6px; }
  .pkc-modal-footer { flex-direction: column; }
  .pkc-btn-confirmar, .pkc-btn-cancelar { width: 100%; justify-content: center; }
  .pkc-overlay { align-items: flex-end; padding: 0; }
  .pkc-svc-kpi-bar { gap: 6px; }
  .pkc-svc-kpi-card { padding: 8px 12px; min-width: 90px; }
  .pkc-svc-kpi-nom { font-size: 0.65rem; }
  .pkc-svc-kpi-val { font-size: 1.1rem; }
}

/* ── KPI Servicios ── */
.pkc-svc-kpi-bar {
  display: flex; flex-wrap: wrap; gap: 8px;
  margin-bottom: 12px;
}
.pkc-svc-kpi-card {
  display: flex; flex-direction: column; align-items: center;
  gap: 4px; padding: 10px 16px; border-radius: 10px;
  background: #1e293b; color: #fff;
  min-width: 110px; flex: 1;
}
.pkc-svc-kpi-nom {
  font-size: 0.7rem; text-transform: uppercase;
  letter-spacing: .06em; color: #94a3b8; font-weight: 600;
}
.pkc-svc-kpi-nums {
  display: flex; align-items: center; gap: 8px;
}
.pkc-svc-kpi-col {
  display: flex; flex-direction: column; align-items: center; gap: 1px;
}
.pkc-svc-kpi-val {
  font-size: 1.25rem; font-weight: 700; line-height: 1;
}
.pkc-svc-kpi-val--activo { color: #34d399; }
.pkc-svc-kpi-lbl {
  font-size: 0.6rem; color: #64748b; text-transform: uppercase;
}
.pkc-svc-kpi-sep { color: #334155; font-size: 1.1rem; }

@media (max-width: 768px) {
  .pkc-svc-kpi-card { padding: 8px 12px; min-width: 90px; }
}
</style>
