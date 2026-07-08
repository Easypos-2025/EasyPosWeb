<template>
  <div class="orden-detalle-wrap">

    <!-- ══ HEADER ORDEN ══ -->
    <div class="orden-header-card">
      <div class="oh-left">
        <div class="oh-numero">{{ orden?.numero_orden ?? '...' }}</div>
        <div class="oh-info">
          <span :class="['estado-badge', `estado-${orden?.estado}`]">
            {{ estadoLabel(orden?.estado) }}
          </span>
          <span class="oh-fecha">
            <i class="bi bi-calendar3"></i>
            {{ fmtFecha(orden?.fecha_ingreso) }}
          </span>
          <span v-if="orden?.promesa_entrega" class="oh-promesa">
            <i class="bi bi-clock-history"></i>
            Promesa: {{ fmtFecha(orden?.promesa_entrega) }}
          </span>
        </div>
      </div>

      <div class="oh-vehicle">
        <div class="oh-placa">
          <i class="bi bi-car-front-fill"></i>
          {{ orden?.placa ?? '—' }}
        </div>
        <div class="oh-vehicle-info">
          <span>{{ [orden?.marca, orden?.modelo, orden?.anio_modelo].filter(Boolean).join(' ') || '—' }}</span>
          <span v-if="orden?.color" class="oh-color">{{ orden.color }}</span>
          <span v-if="orden?.km_ingreso" class="oh-km">
            <i class="bi bi-speedometer2"></i> {{ orden.km_ingreso.toLocaleString() }} km
          </span>
        </div>
      </div>

      <div class="oh-right">
        <div v-if="orden?.cliente_nombre" class="oh-cliente">
          <i class="bi bi-person-fill"></i> {{ orden.cliente_nombre }}
        </div>
        <div class="oh-acciones">
          <!-- Cambio de estado -->
          <template v-if="orden?.estado === 'abierta'">
            <button class="btn-estado en_proceso" @click="cambiarEstado('en_proceso')">
              <i class="bi bi-play-fill"></i> Iniciar
            </button>
          </template>
          <template v-else-if="orden?.estado === 'en_proceso'">
            <button class="btn-estado terminada" @click="cambiarEstado('terminada')">
              <i class="bi bi-check2-circle"></i> Terminar
            </button>
          </template>
          <template v-else-if="orden?.estado === 'terminada'">
            <button class="btn-estado entregada" @click="cambiarEstado('entregada')">
              <i class="bi bi-box-arrow-right"></i> Entregar
            </button>
          </template>
          <button class="btn-print" @click="imprimir">
            <i class="bi bi-printer"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- Diagnóstico / observaciones -->
    <div v-if="orden?.diagnostico" class="diagnostico-bar">
      <i class="bi bi-card-text"></i>
      <strong>Diagnóstico:</strong> {{ orden.diagnostico }}
    </div>

    <!-- ══ TOTALES ══ -->
    <div class="totales-bar">
      <div class="total-chip">
        <span class="total-lbl">Servicios</span>
        <span class="total-val">{{ fmt(totales.servicios) }}</span>
      </div>
      <div class="total-chip">
        <span class="total-lbl">Repuestos</span>
        <span class="total-val">{{ fmt(totales.repuestos) }}</span>
      </div>
      <div class="total-chip highlight">
        <span class="total-lbl">TOTAL</span>
        <span class="total-val">{{ fmt(totales.total) }}</span>
      </div>
      <div class="total-chip mano-obra">
        <span class="total-lbl">Mano de obra operarios</span>
        <span class="total-val">{{ fmt(totales.mano_obra) }}</span>
      </div>
    </div>

    <!-- ══ LAYOUT DOS COLUMNAS ══ -->
    <div class="orden-body">

      <!-- ── Columna izquierda: Agregar ítem ── -->
      <div class="col-form">
        <div class="form-card">
          <h6 class="form-title"><i class="bi bi-plus-circle-fill"></i> Agregar Servicio / Repuesto</h6>

          <!-- Búsqueda de producto -->
          <div class="field-group">
            <label>Producto / Servicio</label>
            <div class="search-wrap">
              <input
                v-model="busqueda"
                placeholder="Buscar por nombre o código..."
                class="form-inp"
                @input="buscarProductos"
                @keydown.esc="resultados = []"
              />
              <i v-if="buscando" class="bi bi-hourglass-split spin abs-icon"></i>
            </div>
            <div v-if="resultados.length > 0" class="search-results">
              <div
                v-for="r in resultados" :key="r.id"
                class="result-item"
                @click="seleccionarProducto(r)"
              >
                <span class="r-name">{{ r.name }}</span>
                <span class="r-code">{{ r.code }}</span>
                <span :class="['r-tipo', r.tipo_servicio ?? 'repuesto']">
                  {{ r.tipo_display ?? r.tipo_servicio ?? 'repuesto' }}
                </span>
                <span class="r-price">{{ fmt(r.base_price) }}</span>
              </div>
            </div>
          </div>

          <!-- Producto seleccionado -->
          <div v-if="itemForm.producto_id" class="producto-sel">
            <div class="ps-info">
              <span class="ps-name">{{ itemForm.producto_nombre }}</span>
              <span class="ps-code">{{ itemForm.producto_code }}</span>
            </div>
            <button class="ps-clear" @click="limpiarProducto">
              <i class="bi bi-x-lg"></i>
            </button>
          </div>

          <div class="form-row">
            <div class="field-group">
              <label>Tipo</label>
              <select v-model="itemForm.tipo_item" class="form-inp form-sel">
                <option value="servicio">Servicio</option>
                <option value="repuesto">Repuesto</option>
                <option value="insumo">Insumo</option>
              </select>
            </div>
            <div class="field-group">
              <label>Cantidad</label>
              <input v-model.number="itemForm.cantidad" type="number" min="0.01" step="0.01" class="form-inp" />
            </div>
          </div>

          <div class="form-row">
            <div class="field-group">
              <label>Precio unitario</label>
              <input v-model.number="itemForm.precio_unitario" type="number" min="0" class="form-inp" />
            </div>
            <div class="field-group">
              <label>Subtotal</label>
              <div class="subtotal-display">{{ fmt(subtotalItem) }}</div>
            </div>
          </div>

          <!-- Operario (solo servicios) -->
          <div v-if="itemForm.tipo_item === 'servicio'" class="field-group">
            <label>Operario responsable</label>
            <select v-model="itemForm.worker_id" class="form-inp form-sel">
              <option :value="null">— Sin asignar —</option>
              <option v-for="w in workers" :key="w.id" :value="w.id">
                {{ w.name }} · {{ w.profession_nombre ?? '' }}
                <template v-if="w.pct_operario"> ({{ w.pct_operario }}%)</template>
              </option>
            </select>
            <div v-if="itemForm.worker_id && itemForm.pct_operario > 0" class="mano-obra-preview">
              Mano de obra operario:
              <strong>{{ fmt(subtotalItem * itemForm.pct_operario / 100) }}</strong>
              · {{ itemForm.pct_operario }}%
            </div>
          </div>

          <!-- Descripción -->
          <div class="field-group">
            <label>Descripción / observación</label>
            <textarea v-model="itemForm.descripcion" class="form-inp form-ta" rows="2" placeholder="Opcional..."></textarea>
          </div>

          <button
            class="btn-agregar"
            :disabled="!puedeAgregar || agregando"
            @click="agregarDetalle"
          >
            <i v-if="agregando" class="bi bi-hourglass-split spin"></i>
            <i v-else class="bi bi-plus-lg"></i>
            Agregar al detalle
          </button>
        </div>

        <!-- Operarios asignados -->
        <div v-if="ordenWorkers.length" class="workers-card">
          <h6 class="form-title"><i class="bi bi-people-fill"></i> Operarios en esta orden</h6>
          <div class="worker-chips">
            <div v-for="w in ordenWorkers" :key="w.worker_id" class="worker-chip">
              <div class="wc-avatar">{{ initials(w.worker_nombre) }}</div>
              <div class="wc-info">
                <span class="wc-name">{{ w.worker_nombre }}</span>
                <span class="wc-role">{{ w.profession_nombre ?? '' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Columna derecha: Detalle de la orden ── -->
      <div class="col-detalle">
        <div class="detalle-card">
          <h6 class="form-title">
            <i class="bi bi-list-check"></i> Detalle de la Orden
            <span class="detalle-count">{{ detalles.length }} ítem{{ detalles.length !== 1 ? 's' : '' }}</span>
          </h6>

          <div v-if="loadingDetalles" class="loading-center">
            <i class="bi bi-hourglass-split spin"></i>
          </div>
          <div v-else-if="detalles.length === 0" class="empty-detalle">
            <i class="bi bi-inbox"></i>
            <p>Sin ítems. Agrega servicios o repuestos.</p>
          </div>
          <div v-else class="detalles-list">
            <div
              v-for="d in detalles" :key="d.id"
              :class="['detalle-row', `tipo-${d.tipo_item}`]"
            >
              <div class="dr-left">
                <span :class="['dr-tipo', `tipo-${d.tipo_item}`]">{{ d.tipo_item }}</span>
                <div class="dr-names">
                  <span class="dr-name">{{ d.nombre_display ?? d.producto_nombre ?? '—' }}</span>
                  <span v-if="d.descripcion" class="dr-desc">{{ d.descripcion }}</span>
                </div>
              </div>
              <div class="dr-numbers">
                <span class="dr-qty">{{ d.cantidad }} u</span>
                <span class="dr-price">{{ fmt(d.precio_cobrado) }}</span>
                <span class="dr-sub">{{ fmt(d.subtotal) }}</span>
                <span v-if="d.mano_obra_operario > 0" class="dr-mo">
                  <i class="bi bi-person-fill"></i> {{ fmt(d.mano_obra_operario) }}
                </span>
              </div>
              <div class="dr-worker" v-if="d.worker_nombre || d.operario_nombre">
                <i class="bi bi-person-badge"></i> {{ d.worker_nombre ?? d.operario_nombre }}
              </div>
              <button
                v-if="d.liq_estado === 'pendiente' || !d.liq_estado"
                class="dr-delete"
                @click="eliminarDetalle(d)"
                :disabled="eliminandoId === d.id"
                title="Eliminar ítem"
              >
                <i v-if="eliminandoId === d.id" class="bi bi-hourglass-split spin"></i>
                <i v-else class="bi bi-trash3"></i>
              </button>
            </div>
          </div>
        </div>
      </div>

    </div><!-- /orden-body -->

    <!-- Toast -->
    <Teleport to="body">
      <div v-if="toast.visible" :class="['toast-msg', `toast-${toast.tipo}`]">
        <i :class="toast.tipo === 'ok' ? 'bi bi-check-circle-fill' : 'bi bi-exclamation-triangle-fill'"></i>
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

const route        = useRoute()
const router       = useRouter()
const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id)
const ordenId      = computed(() => route.params.id)

// ── Orden ─────────────────────────────────────────────────────────────────
const orden           = ref(null)
const detalles        = ref([])
const loadingDetalles = ref(false)

// workers asignados a la orden
const ordenWorkers = ref([])

async function cargarOrden() {
  if (!ordenId.value || !companyId.value) return
  loadingDetalles.value = true
  try {
    const { data } = await api.get(`/api/talleres/ordenes/${ordenId.value}`, {
      params: { company_id: companyId.value }
    })
    orden.value        = data.orden ?? data   // compat: si llega flat o estructurado
    detalles.value     = data.detalles ?? []
    ordenWorkers.value = data.workers ?? []
  } catch (e) {
    mostrarToast('Error al cargar la orden', 'error')
  } finally { loadingDetalles.value = false }
}

// ── Cambiar estado ────────────────────────────────────────────────────────
async function cambiarEstado(nuevoEstado) {
  try {
    await api.patch(`/api/talleres/ordenes/${ordenId.value}/estado`, {
      company_id: companyId.value,
      estado: nuevoEstado
    })
    if (orden.value) orden.value.estado = nuevoEstado
    mostrarToast(`Orden marcada como "${estadoLabel(nuevoEstado)}"`, 'ok')
  } catch (e) {
    mostrarToast(e?.response?.data?.detail ?? 'Error al cambiar estado', 'error')
  }
}

// ── Workers (para el select de operario) ──────────────────────────────────
const workers = ref([])
async function cargarWorkers() {
  if (!companyId.value) return
  try {
    const { data } = await api.get('/api/talleres/workers-con-config', {
      params: { company_id: companyId.value }
    })
    workers.value = data
  } catch { workers.value = [] }
}

// ── Búsqueda de productos ─────────────────────────────────────────────────
const busqueda  = ref('')
const resultados = ref([])
const buscando  = ref(false)
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
    } catch { resultados.value = [] } finally { buscando.value = false }
  }, 300)
}

function seleccionarProducto(p) {
  itemForm.value.producto_id            = p.id
  itemForm.value.producto_nombre        = p.name
  itemForm.value.producto_code          = p.code
  itemForm.value.precio_unitario        = p.base_price ?? 0
  itemForm.value.producto_profession_id = p.profession_id ?? null
  if (p.pct_operario) itemForm.value.pct_operario = p.pct_operario
  if (p.service_type) itemForm.value.tipo_item = 'servicio'
  else if (p.inventory_behavior === 'decrement') itemForm.value.tipo_item = 'repuesto'
  busqueda.value  = ''
  resultados.value = []
}

function limpiarProducto() {
  itemForm.value.producto_id     = null
  itemForm.value.producto_nombre = ''
  itemForm.value.producto_code   = ''
}

// ── Formulario de ítem ────────────────────────────────────────────────────
const itemFormDefault = () => ({
  producto_id:       null,
  producto_nombre:   '',
  producto_code:     '',
  producto_profession_id: null,
  tipo_item:         'servicio',
  cantidad:          1,
  precio_unitario:   0,
  worker_id:         null,
  pct_operario:      0,
  descripcion:       '',
})
const itemForm = ref(itemFormDefault())
const agregando = ref(false)

watch(() => itemForm.value.worker_id, (wid) => {
  const w = workers.value.find(x => x.id === wid)
  itemForm.value.pct_operario = w?.pct_operario ?? 0
})

const subtotalItem = computed(() =>
  (itemForm.value.cantidad || 0) * (itemForm.value.precio_unitario || 0)
)
const puedeAgregar = computed(() =>
  itemForm.value.producto_id &&
  itemForm.value.cantidad > 0 &&
  itemForm.value.precio_cobrado >= 0
)

async function agregarDetalle() {
  if (!puedeAgregar.value) return
  agregando.value = true
  try {
    const workerSel = workers.value.find(x => x.id === itemForm.value.worker_id)
    const payload = {
      company_id:    companyId.value,
      product_id:    itemForm.value.producto_id,
      nombre:        itemForm.value.producto_nombre,
      tipo_item:     itemForm.value.tipo_item,
      cantidad:      itemForm.value.cantidad,
      precio_unitario: itemForm.value.precio_unitario,
      worker_id:     itemForm.value.worker_id || null,
      profession_id: itemForm.value.producto_profession_id || workerSel?.profession_id || null,
      descripcion:   itemForm.value.descripcion || null,
    }
    const { data } = await api.post(`/api/talleres/ordenes/${ordenId.value}/detalle`, payload)
    // Enriquecer la fila para display inmediato sin recargar toda la orden
    detalles.value.push({
      id:                 data.id ?? Date.now(),
      tipo_item:          itemForm.value.tipo_item,
      nombre:             itemForm.value.producto_nombre,
      nombre_display:     itemForm.value.producto_nombre,
      descripcion:        itemForm.value.descripcion,
      cantidad:           itemForm.value.cantidad,
      precio_cobrado:     itemForm.value.precio_unitario,
      subtotal:           data.subtotal,
      mano_obra_operario: data.mano_obra_operario ?? 0,
      worker_nombre:      workerSel?.name ?? null,
      liq_estado:         'pendiente',
    })
    itemForm.value = itemFormDefault()
    mostrarToast('Ítem agregado', 'ok')
  } catch (e) {
    mostrarToast(e?.response?.data?.detail ?? 'Error al agregar', 'error')
  } finally { agregando.value = false }
}

// ── Eliminar detalle ──────────────────────────────────────────────────────
const eliminandoId = ref(null)
async function eliminarDetalle(d) {
  if (!confirm(`¿Eliminar "${d.nombre_display ?? d.producto_nombre}"?`)) return
  eliminandoId.value = d.id
  try {
    await api.delete(
      `/api/talleres/ordenes/${ordenId.value}/detalle/${d.id}`,
      { params: { company_id: companyId.value } }
    )
    detalles.value = detalles.value.filter(x => x.id !== d.id)
    mostrarToast('Ítem eliminado', 'ok')
  } catch (e) {
    mostrarToast(e?.response?.data?.detail ?? 'Error al eliminar', 'error')
  } finally { eliminandoId.value = null }
}

// ── Totales ───────────────────────────────────────────────────────────────
const totales = computed(() => {
  let servicios = 0, repuestos = 0, mano_obra = 0
  for (const d of detalles.value) {
    if (d.tipo_item === 'servicio') servicios += d.subtotal ?? 0
    else repuestos += d.subtotal ?? 0
    mano_obra += d.mano_obra_operario ?? 0
  }
  return { servicios, repuestos, total: servicios + repuestos, mano_obra }
})

// ── Imprimir ──────────────────────────────────────────────────────────────
function imprimir() { window.print() }

// ── Helpers ───────────────────────────────────────────────────────────────
function estadoLabel(e) {
  const m = { abierta: 'Abierta', en_proceso: 'En Proceso', terminada: 'Terminada', entregada: 'Entregada', cancelada: 'Cancelada' }
  return m[e] ?? e ?? '—'
}
function fmtFecha(v) {
  if (!v) return '—'
  return new Date(v).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}
function fmt(v) {
  if (v == null || v === '') return '—'
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v)
}
function initials(name) {
  return (name || '?').split(' ').slice(0, 2).map(s => s[0]).join('').toUpperCase()
}

const toast = ref({ visible: false, msg: '', tipo: 'ok' })
function mostrarToast(msg, tipo = 'ok') {
  toast.value = { visible: true, msg, tipo }
  setTimeout(() => { toast.value.visible = false }, 3500)
}

onMounted(() => {
  cargarOrden()
  cargarWorkers()
})
</script>

<style scoped>
/* ── Layout wrap ── */
.orden-detalle-wrap {
  display: flex; flex-direction: column; gap: 16px;
}

/* ── Header card ── */
.orden-header-card {
  background: #fff; border: 1.5px solid #e2e8f0; border-radius: 14px;
  padding: 16px 20px; display: flex; align-items: center; gap: 20px;
  flex-wrap: wrap; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.oh-left      { display: flex; flex-direction: column; gap: 6px; flex-shrink: 0; }
.oh-numero    { font-size: 18px; font-weight: 800; color: #1e3a5f; }
.oh-info      { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.oh-fecha, .oh-promesa { font-size: 12px; color: #64748b; display: flex; align-items: center; gap: 4px; }
.oh-vehicle   { display: flex; flex-direction: column; gap: 4px; flex: 1; }
.oh-placa     { font-size: 20px; font-weight: 800; color: #0f172a; letter-spacing: 2px; display: flex; align-items: center; gap: 8px; }
.oh-placa .bi { color: #1e3a5f; }
.oh-vehicle-info { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; font-size: 13px; color: #475569; }
.oh-color     { background: #f1f5f9; border-radius: 20px; padding: 1px 8px; font-size: 12px; }
.oh-km        { display: flex; align-items: center; gap: 3px; font-size: 12px; color: #64748b; }
.oh-right     { display: flex; flex-direction: column; align-items: flex-end; gap: 8px; flex-shrink: 0; }
.oh-cliente   { font-size: 13px; color: #475569; display: flex; align-items: center; gap: 6px; font-weight: 600; }
.oh-acciones  { display: flex; align-items: center; gap: 8px; }

/* ── Estado badges ── */
.estado-badge {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.5px; border-radius: 20px; padding: 3px 10px;
}
.estado-abierta   { background: #dbeafe; color: #1d4ed8; }
.estado-en_proceso { background: #fef3c7; color: #d97706; }
.estado-terminada { background: #dcfce7; color: #15803d; }
.estado-entregada { background: #e0e7ff; color: #4338ca; }
.estado-cancelada { background: #fee2e2; color: #dc2626; }

/* ── Botones de estado ── */
.btn-estado {
  display: flex; align-items: center; gap: 6px;
  border: none; border-radius: 8px; padding: 8px 16px;
  font-size: 13px; font-weight: 700; cursor: pointer; transition: opacity .2s;
}
.btn-estado:hover { opacity: .85; }
.btn-estado.en_proceso { background: #f59e0b; color: #fff; }
.btn-estado.terminada  { background: #22c55e; color: #fff; }
.btn-estado.entregada  { background: #6366f1; color: #fff; }
.btn-print {
  background: #f1f5f9; border: none; border-radius: 8px; width: 36px; height: 36px;
  cursor: pointer; color: #64748b; font-size: 16px; display: flex; align-items: center; justify-content: center;
}
.btn-print:hover { background: #e2e8f0; }

/* ── Diagnóstico ── */
.diagnostico-bar {
  background: #fffbeb; border: 1px solid #fcd34d; border-radius: 10px;
  padding: 10px 14px; font-size: 13px; color: #78350f;
  display: flex; align-items: flex-start; gap: 8px;
}
.diagnostico-bar .bi { margin-top: 2px; color: #d97706; flex-shrink: 0; }

/* ── Totales bar ── */
.totales-bar {
  display: flex; flex-wrap: wrap; gap: 10px;
}
.total-chip {
  display: flex; flex-direction: column; gap: 2px;
  background: #f8fafc; border: 1.5px solid #e2e8f0; border-radius: 10px;
  padding: 8px 14px; min-width: 100px;
}
.total-chip.highlight { background: #1e3a5f; border-color: #1e3a5f; }
.total-chip.mano-obra { background: #eff6ff; border-color: #bfdbfe; }
.total-lbl { font-size: 10px; text-transform: uppercase; font-weight: 700; color: #94a3b8; letter-spacing: 0.4px; }
.total-chip.highlight .total-lbl { color: #93c5fd; }
.total-chip.mano-obra .total-lbl { color: #3b82f6; }
.total-val { font-size: 16px; font-weight: 800; color: #1e3a5f; }
.total-chip.highlight .total-val { color: #fff; font-size: 18px; }
.total-chip.mano-obra .total-val { color: #1d4ed8; }

/* ── Body ── */
.orden-body {
  display: grid; grid-template-columns: 380px 1fr; gap: 16px; align-items: start;
}

/* ── Cards comunes ── */
.form-card, .detalle-card, .workers-card {
  background: #fff; border: 1.5px solid #e2e8f0; border-radius: 14px;
  padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.workers-card { margin-top: 14px; }
.form-title {
  margin: 0 0 14px; font-size: 13px; font-weight: 700; color: #1e3a5f;
  display: flex; align-items: center; gap: 7px; padding-bottom: 10px;
  border-bottom: 1px solid #f1f5f9;
}
.detalle-count { margin-left: auto; font-size: 12px; font-weight: 600; color: #94a3b8; }

/* ── Form fields ── */
.field-group { display: flex; flex-direction: column; gap: 4px; margin-bottom: 12px; }
.field-group label { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.4px; }
.form-inp {
  border: 1.5px solid #e2e8f0; border-radius: 8px;
  padding: 8px 12px; font-size: 14px; color: #1e3a5f; outline: none;
  transition: border-color .2s; background: #fff;
}
.form-inp:focus { border-color: #1e3a5f; }
.form-sel { appearance: none; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%2364748b' stroke-width='1.5' fill='none'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 12px center; padding-right: 32px; cursor: pointer; }
.form-ta { resize: vertical; min-height: 60px; font-family: inherit; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }

/* ── Búsqueda ── */
.search-wrap { position: relative; }
.abs-icon { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); color: #94a3b8; }
.search-results {
  position: absolute; left: 0; right: 0; top: calc(100% + 4px);
  background: #fff; border: 1.5px solid #e2e8f0; border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12); z-index: 200; max-height: 240px; overflow-y: auto;
}
.result-item {
  display: flex; align-items: center; gap: 8px; padding: 10px 12px;
  cursor: pointer; transition: background .15s; font-size: 13px;
  border-bottom: 1px solid #f1f5f9;
}
.result-item:last-child { border-bottom: none; }
.result-item:hover { background: #f8fafc; }
.r-name  { flex: 1; font-weight: 600; color: #1e3a5f; }
.r-code  { font-size: 11px; color: #94a3b8; }
.r-tipo  { font-size: 10px; font-weight: 700; border-radius: 20px; padding: 1px 8px; background: #dbeafe; color: #1d4ed8; }
.r-tipo.repuesto { background: #fef3c7; color: #92400e; }
.r-price { font-size: 12px; font-weight: 700; color: #15803d; white-space: nowrap; }

/* ── Producto seleccionado ── */
.producto-sel {
  display: flex; align-items: center; gap: 10px;
  background: #f0fdf4; border: 1.5px solid #86efac; border-radius: 8px;
  padding: 8px 12px; margin-bottom: 12px;
}
.ps-info { flex: 1; display: flex; flex-direction: column; gap: 1px; }
.ps-name { font-size: 13px; font-weight: 700; color: #15803d; }
.ps-code { font-size: 11px; color: #64748b; }
.ps-clear {
  background: none; border: none; color: #94a3b8; cursor: pointer;
  font-size: 14px; padding: 2px; display: flex;
}
.ps-clear:hover { color: #dc2626; }

/* ── Subtotal display ── */
.subtotal-display {
  border: 1.5px solid #e2e8f0; border-radius: 8px; padding: 8px 12px;
  font-size: 16px; font-weight: 800; color: #1e3a5f; background: #f8fafc;
}

/* ── Mano de obra preview ── */
.mano-obra-preview {
  font-size: 12px; color: #1d4ed8; background: #eff6ff;
  border-radius: 6px; padding: 5px 10px; margin-top: 4px;
}

/* ── Btn agregar ── */
.btn-agregar {
  width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px;
  background: #1e3a5f; color: #fff; border: none; border-radius: 10px;
  padding: 12px; font-size: 14px; font-weight: 700; cursor: pointer;
  transition: background .2s;
}
.btn-agregar:hover:not(:disabled) { background: #2d4f80; }
.btn-agregar:disabled { opacity: .5; cursor: default; }

/* ── Workers chips ── */
.worker-chips { display: flex; flex-direction: column; gap: 8px; }
.worker-chip  { display: flex; align-items: center; gap: 10px; padding: 6px 0; }
.wc-avatar {
  width: 32px; height: 32px; border-radius: 50%; background: #1e3a5f; color: #fff;
  font-size: 12px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.wc-info   { display: flex; flex-direction: column; gap: 1px; }
.wc-name   { font-size: 13px; font-weight: 600; color: #1e3a5f; }
.wc-role   { font-size: 11px; color: #64748b; }

/* ── Detalles list ── */
.loading-center { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 32px; color: #94a3b8; }
.empty-detalle  { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 40px; color: #94a3b8; text-align: center; }
.empty-detalle .bi { font-size: 40px; color: #cbd5e1; }
.empty-detalle p { font-size: 13px; margin: 0; }
.detalles-list { display: flex; flex-direction: column; gap: 8px; }

.detalle-row {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  border: 1.5px solid #f1f5f9; border-radius: 10px; padding: 10px 12px;
  border-left: 4px solid transparent;
}
.detalle-row.tipo-servicio { border-left-color: #3b82f6; }
.detalle-row.tipo-repuesto { border-left-color: #f59e0b; }
.detalle-row.tipo-insumo   { border-left-color: #94a3b8; }

.dr-left  { display: flex; align-items: flex-start; gap: 8px; flex: 1; min-width: 150px; }
.dr-tipo  {
  font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.4px;
  border-radius: 20px; padding: 2px 7px; white-space: nowrap; flex-shrink: 0;
}
.dr-tipo.tipo-servicio { background: #dbeafe; color: #1d4ed8; }
.dr-tipo.tipo-repuesto { background: #fef3c7; color: #92400e; }
.dr-tipo.tipo-insumo   { background: #f1f5f9; color: #64748b; }
.dr-names { display: flex; flex-direction: column; gap: 1px; }
.dr-name  { font-size: 13px; font-weight: 600; color: #1e3a5f; }
.dr-desc  { font-size: 11px; color: #64748b; }
.dr-worker { font-size: 11px; color: #94a3b8; display: flex; align-items: center; gap: 4px; white-space: nowrap; }
.dr-numbers { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }
.dr-qty   { font-size: 12px; color: #94a3b8; white-space: nowrap; }
.dr-price { font-size: 12px; color: #64748b; white-space: nowrap; }
.dr-sub   { font-size: 15px; font-weight: 700; color: #1e3a5f; white-space: nowrap; }
.dr-mo    { font-size: 11px; color: #1d4ed8; display: flex; align-items: center; gap: 3px; white-space: nowrap; }
.dr-delete {
  background: #fee2e2; border: none; border-radius: 7px; width: 30px; height: 30px;
  cursor: pointer; color: #dc2626; font-size: 13px; display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.dr-delete:hover:not(:disabled) { background: #fecaca; }
.dr-delete:disabled { opacity: .5; cursor: default; }

/* ── Toast ── */
.toast-msg {
  position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
  display: flex; align-items: center; gap: 8px; padding: 12px 20px;
  border-radius: 10px; font-size: 14px; font-weight: 600; z-index: 9999;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15); animation: slideInUp 0.3s ease;
}
.toast-ok    { background: #1e3a5f; color: #fff; }
.toast-error { background: #dc2626; color: #fff; }
@keyframes slideInUp { from { opacity: 0; transform: translateX(-50%) translateY(10px); } to { opacity: 1; transform: translateX(-50%) translateY(0); } }

.spin { display: inline-block; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Responsive ── */
@media (max-width: 1024px) {
  .orden-body { grid-template-columns: 1fr; }
}
@media (max-width: 768px) {
  .orden-header-card { gap: 12px; }
  .oh-left, .oh-vehicle, .oh-right { width: 100%; }
  .oh-right { align-items: flex-start; }
  .totales-bar { gap: 8px; }
  .total-chip { min-width: 80px; }
  .form-row { grid-template-columns: 1fr; }
}
@media (max-width: 576px) {
  .oh-numero { font-size: 15px; }
  .oh-placa  { font-size: 16px; }
  .detalle-row { flex-direction: column; align-items: flex-start; }
  .dr-numbers  { justify-content: flex-start; }
}
</style>
