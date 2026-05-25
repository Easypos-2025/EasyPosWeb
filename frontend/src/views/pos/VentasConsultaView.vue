<template>
  <div class="vc-wrap">
    <!-- ── Filtros ──────────────────────────────────────────────── -->
    <div class="vc-filters card mb-3">
      <div class="vc-filter-row">
        <!-- Tipo -->
        <div class="vc-filter-group">
          <label class="vc-label">Tipo</label>
          <div class="vc-radios">
            <label v-for="op in tipoOpts" :key="op.value" class="vc-radio">
              <input type="radio" v-model="filtro.tipo" :value="op.value" @change="buscar" />
              {{ op.label }}
            </label>
          </div>
        </div>

        <!-- Desde + Hasta en la misma línea -->
        <div class="vc-filter-group">
          <label class="vc-label">Desde / Hasta</label>
          <div class="vc-fechas-row">
            <input type="date" v-model="filtro.desde" class="vc-input" @change="buscar" />
            <span class="vc-fecha-sep">—</span>
            <input type="date" v-model="filtro.hasta" class="vc-input" @change="buscar" />
          </div>
        </div>

        <button class="btn btn-outline-secondary vc-btn-hoy" @click="irHoy" title="Ir a hoy">
          <i class="bi bi-calendar-check"></i>
          <span>Hoy</span>
        </button>

        <button class="btn btn-primary vc-btn-buscar" @click="buscar" :disabled="cargandoLista">
          <i class="bi bi-search"></i>
          <span>Buscar</span>
        </button>
      </div>

      <!-- Totales: venta real + propinas + domicilios -->
      <div v-if="!cargandoLista && lista.length" class="vc-totales">
        <span class="vc-total-chip">
          <span class="vc-total-lbl">{{ lista.length }} registros</span>
        </span>
        <span class="vc-total-chip vc-total-chip--green">
          <span class="vc-total-lbl">Venta Real</span>
          <strong>{{ fmt(totalVentaReal) }}</strong>
        </span>
        <span v-if="totalPropinas > 0" class="vc-total-chip vc-total-chip--orange">
          <span class="vc-total-lbl">Propinas</span>
          <strong>{{ fmt(totalPropinas) }}</strong>
        </span>
        <span v-if="totalDomicilios > 0" class="vc-total-chip vc-total-chip--blue">
          <span class="vc-total-lbl">Domicilios</span>
          <strong>{{ fmt(totalDomicilios) }}</strong>
        </span>
      </div>
    </div>

    <!-- ── Cuerpo dos columnas ───────────────────────────────────── -->
    <div class="vc-body">

      <!-- Panel izquierdo: lista -->
      <div class="vc-panel-left card">
        <div v-if="cargandoLista" class="vc-placeholder">
          <div class="spinner-border text-primary" style="width:2rem;height:2rem;"></div>
        </div>
        <div v-else-if="!lista.length" class="vc-placeholder text-muted">
          <i class="bi bi-receipt fs-2"></i>
          <p class="mt-2 mb-0">Sin resultados</p>
        </div>
        <div v-else class="vc-list">
          <div
            v-for="item in lista"
            :key="`${item.tipo}-${item.numero}`"
            class="vc-row"
            :class="{ 'vc-row--active': seleccionado?.numero === item.numero && seleccionado?.tipo === item.tipo }"
            @click="seleccionar(item)"
          >
            <div class="vc-row-top">
              <span class="vc-folio">
                <span class="badge" :class="item.tipo === 'factura' ? 'bg-primary' : 'bg-secondary'">
                  {{ item.tipo === 'factura' ? 'FAC' : 'REC' }}
                </span>
                {{ item.numero }}
              </span>
              <span class="vc-valor">{{ fmt(ventaReal(item)) }}</span>
            </div>
            <div class="vc-row-bot">
              <span class="vc-mesa"><i class="bi bi-table"></i> {{ item.mesa || '—' }}</span>
              <span v-if="item.propina > 0" class="vc-chip-propina" title="Propina">
                +{{ fmt(item.propina) }}
              </span>
              <span v-if="item.domicilio > 0" class="vc-chip-domicilio" title="Domicilio">
                <i class="bi bi-bicycle"></i>{{ fmt(item.domicilio) }}
              </span>
              <span class="vc-hora text-muted ms-auto">{{ item.hora }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Panel derecho: detalle -->
      <div class="vc-panel-right card">
        <div v-if="!seleccionado" class="vc-placeholder text-muted">
          <i class="bi bi-arrow-left-circle fs-2"></i>
          <p class="mt-2 mb-0">Selecciona un registro</p>
        </div>

        <template v-else>
          <div v-if="cargandoDetalle" class="vc-placeholder">
            <div class="spinner-border text-primary" style="width:2rem;height:2rem;"></div>
          </div>

          <template v-else-if="detalle">
            <!-- Header -->
            <div class="vc-det-header">
              <div class="vc-det-title">
                <span class="badge" :class="seleccionado.tipo === 'factura' ? 'bg-primary' : 'bg-secondary'">
                  {{ seleccionado.tipo === 'factura' ? 'Factura' : 'Recibo' }}
                </span>
                <strong class="ms-2">{{ detalle.header.numero }}</strong>
              </div>
              <div class="vc-det-meta">
                <span><i class="bi bi-calendar3"></i> {{ detalle.header.date }}</span>
                <span><i class="bi bi-clock"></i> {{ detalle.header.hora }}</span>
                <span v-if="detalle.header.mesa"><i class="bi bi-table"></i> {{ detalle.header.mesa }}</span>
                <span v-if="detalle.header.mesero"><i class="bi bi-person"></i> {{ detalle.header.mesero }}</span>
                <span v-if="detalle.header.comensales"><i class="bi bi-people"></i> {{ detalle.header.comensales }}</span>
              </div>
              <!-- Pagos -->
              <div class="vc-det-pagos">
                <div v-if="detalle.header.efectivo > 0" class="vc-pago-row">
                  <span>Efectivo</span><span>{{ fmt(detalle.header.efectivo) }}</span>
                </div>
                <div v-if="detalle.header.tarjeta_credito > 0" class="vc-pago-row">
                  <span>T. Crédito</span><span>{{ fmt(detalle.header.tarjeta_credito) }}</span>
                </div>
                <div v-if="detalle.header.tarjeta_debito > 0" class="vc-pago-row">
                  <span>T. Débito</span><span>{{ fmt(detalle.header.tarjeta_debito) }}</span>
                </div>
                <div v-if="detalle.header.ajuste != 0" class="vc-pago-row">
                  <span>Ajuste</span><span>{{ fmt(detalle.header.ajuste) }}</span>
                </div>
                <div v-if="detalle.header.descuento > 0" class="vc-pago-row text-danger">
                  <span>Descuento</span><span>-{{ fmt(detalle.header.descuento) }}</span>
                </div>
                <div class="vc-pago-row vc-pago-total">
                  <span>Total</span><span>{{ fmt(detalle.header.total) }}</span>
                </div>
              </div>
            </div>

            <!-- Tabla de ítems -->
            <div class="vc-det-items">
              <table class="vc-table">
                <thead>
                  <tr>
                    <th>Plato</th>
                    <th class="text-center">Cant</th>
                    <th class="text-end">Precio</th>
                    <th class="text-end">Subtotal</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  <template v-for="item in detalle.items" :key="`${item.dish_id}-${item.item}`">
                    <tr class="vc-item-row">
                      <td>{{ item.plato }}</td>
                      <td class="text-center">{{ item.quantity }}</td>
                      <td class="text-end">{{ fmt(item.price) }}</td>
                      <td class="text-end">{{ fmt(item.subtotal) }}</td>
                      <td class="text-center">
                        <button
                          class="btn btn-sm btn-success vc-btn-ver"
                          @click="verInsumos(item)"
                          title="Ver insumos consumidos"
                        >
                          VER
                        </button>
                      </td>
                    </tr>
                    <!-- Fila expandida de insumos -->
                    <tr v-if="itemExpandido === `${item.dish_id}-${item.item}`" class="vc-insumos-row">
                      <td colspan="5">
                        <div v-if="cargandoInsumos" class="text-center py-2">
                          <div class="spinner-border spinner-border-sm text-success"></div>
                        </div>
                        <div v-else-if="!insumos.length" class="text-muted small ps-2">Sin insumos registrados</div>
                        <table v-else class="vc-table-insumos">
                          <thead>
                            <tr><th>Insumo</th><th class="text-end">Cantidad</th><th>Unidad</th></tr>
                          </thead>
                          <tbody>
                            <tr v-for="ins in insumos" :key="ins.item_id">
                              <td>{{ ins.insumo }}</td>
                              <td class="text-end">{{ ins.quantity }}</td>
                              <td>{{ ins.unidad }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </td>
                    </tr>
                  </template>
                </tbody>
              </table>
            </div>
          </template>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import api from '@/services/apis.js'
import { useCompanyStore } from '@/stores/companyStore'

const companyStore = useCompanyStore()
const selectedCid = computed(() => companyStore.selectedCompany?.id || undefined)

const fmtCOP = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 })
const fmt = v => fmtCOP.format(v || 0)

// Use local date (not UTC) to avoid timezone shift
function localDate() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}
const hoy = localDate()

const tipoOpts = [
  { value: 'ambos',   label: 'Ambos' },
  { value: 'factura', label: 'Facturas' },
  { value: 'recibo',  label: 'Recibos' },
]

const filtro = ref({ tipo: 'ambos', desde: hoy, hasta: hoy })

const lista          = ref([])
const cargandoLista  = ref(false)
const seleccionado   = ref(null)
const detalle        = ref(null)
const cargandoDetalle= ref(false)
const itemExpandido  = ref(null)
const insumos        = ref([])
const cargandoInsumos= ref(false)

const ventaReal      = (r) => (r.valor || 0) - (r.propina || 0) - (r.domicilio || 0)
const totalVentaReal  = computed(() => lista.value.reduce((s, r) => s + ventaReal(r), 0))
const totalPropinas   = computed(() => lista.value.reduce((s, r) => s + (r.propina   || 0), 0))
const totalDomicilios = computed(() => lista.value.reduce((s, r) => s + (r.domicilio || 0), 0))

async function buscar() {
  cargandoLista.value = true
  seleccionado.value  = null
  detalle.value       = null
  itemExpandido.value = null
  try {
    const { data } = await api.get('/api/pos-consultas/ventas', {
      params: {
        desde:      filtro.value.desde,
        hasta:      filtro.value.hasta,
        tipo:       filtro.value.tipo,
        company_id: selectedCid.value,
      }
    })
    lista.value = data
  } catch (e) {
    console.error(e)
    lista.value = []
  } finally {
    cargandoLista.value = false
    _startRefresh()
  }
}

async function seleccionar(item) {
  if (seleccionado.value?.numero === item.numero && seleccionado.value?.tipo === item.tipo) return
  seleccionado.value   = item
  detalle.value        = null
  itemExpandido.value  = null
  cargandoDetalle.value= true
  try {
    const { data } = await api.get(`/api/pos-consultas/venta-detalle/${item.tipo}/${item.numero}`, {
      params: { company_id: selectedCid.value }
    })
    detalle.value = data
  } catch (e) {
    console.error(e)
  } finally {
    cargandoDetalle.value = false
  }
}

async function verInsumos(item) {
  const key = `${item.dish_id}-${item.item}`
  if (itemExpandido.value === key) {
    itemExpandido.value = null
    return
  }
  itemExpandido.value  = key
  insumos.value        = []
  cargandoInsumos.value= true
  try {
    const { data } = await api.get('/api/pos-consultas/detalle-productos', {
      params: {
        tipo:       seleccionado.value.tipo,
        numero:     seleccionado.value.numero,
        fecha:      detalle.value.header.date,
        dish_id:    item.dish_id,
        item:       item.item,
        company_id: selectedCid.value,
      }
    })
    insumos.value = data
  } catch (e) {
    console.error(e)
    insumos.value = []
  } finally {
    cargandoInsumos.value = false
  }
}

function irHoy() {
  const hoyStr = localDate()
  filtro.value.tipo  = 'ambos'
  filtro.value.desde = hoyStr
  filtro.value.hasta = hoyStr
  buscar()
}

let _refreshTimer = null

function _startRefresh() {
  _stopRefresh()
  const hoyStr = localDate()
  if (filtro.value.hasta >= hoyStr) {
    _refreshTimer = setInterval(() => {
      if (filtro.value.hasta >= localDate()) buscar()
    }, 30000)
  }
}

function _stopRefresh() {
  if (_refreshTimer) { clearInterval(_refreshTimer); _refreshTimer = null }
}

onMounted(() => { buscar(); _startRefresh() })
onUnmounted(_stopRefresh)
</script>

<style scoped>
/* ── Layout general ─────────────────────────────────────── */
.vc-wrap {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.vc-body {
  display: flex;
  gap: 16px;
  flex: 1;
  min-height: 0;
}

.card {
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #fff;
}

/* ── Filtros ────────────────────────────────────────────── */
.vc-filters {
  padding: 12px 16px;
}

.vc-filter-row {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  flex-wrap: wrap;
}

.vc-filter-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.vc-label {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}

.vc-radios {
  display: flex;
  gap: 12px;
}

.vc-radio {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  cursor: pointer;
}

.vc-input {
  height: 34px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 0 10px;
  font-size: 13px;
  background: #f8fafc;
  outline: none;
}
.vc-input:focus { border-color: #3b82f6; background: #fff; }

.vc-btn-hoy {
  height: 34px;
  padding: 0 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.vc-btn-buscar {
  height: 34px;
  padding: 0 18px;
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.vc-fechas-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.vc-fecha-sep {
  color: #94a3b8;
  font-size: 13px;
  flex-shrink: 0;
}

.vc-totales {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  border-top: 1px solid #f1f5f9;
  padding-top: 8px;
}

.vc-total-chip {
  display: flex;
  align-items: center;
  gap: 5px;
  background: #f1f5f9;
  border-radius: 8px;
  padding: 4px 12px;
  font-size: 13px;
  border-left: 3px solid #cbd5e1;
}
.vc-total-chip--green  {
  background: #f0fdf4;
  color: #15803d;
  border-left-color: #22c55e;
}
.vc-total-chip--orange {
  background: #fff7ed;
  color: #c2410c;
  border-left-color: #f97316;
}
.vc-total-chip--blue   {
  background: #eff6ff;
  color: #1e40af;
  border-left-color: #3b82f6;
}
.vc-total-lbl {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  opacity: 0.7;
  margin-right: 3px;
}

/* ── Paneles ────────────────────────────────────────────── */
.vc-panel-left {
  width: 320px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.vc-panel-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.vc-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  padding: 32px;
}

/* ── Lista ──────────────────────────────────────────────── */
.vc-list {
  flex: 1;
  overflow-y: auto;
}

.vc-row {
  padding: 10px 14px;
  border-bottom: 1px solid #f1f5f9;
  cursor: pointer;
  transition: background 0.12s;
}
.vc-row:hover        { background: #f8fafc; }
.vc-row--active      { background: #eff6ff; border-left: 3px solid #3b82f6; }

.vc-row-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.vc-folio {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 5px;
}
.vc-valor {
  font-size: 14px;
  font-weight: 700;
  color: #16a34a;
}
.vc-row-bot {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: #64748b;
}
.vc-hora { font-size: 11px; }

.vc-chip-propina, .vc-chip-domicilio {
  font-size: 10px;
  font-weight: 700;
  border-radius: 4px;
  padding: 1px 5px;
  white-space: nowrap;
}
.vc-chip-propina  { background: #fff7ed; color: #c2410c; }
.vc-chip-domicilio{ background: #eff6ff; color: #1d4ed8; display: flex; align-items: center; gap: 3px; }

/* ── Detalle header ─────────────────────────────────────── */
.vc-det-header {
  padding: 16px;
  border-bottom: 1px solid #f1f5f9;
}
.vc-det-title {
  font-size: 16px;
  margin-bottom: 8px;
}
.vc-det-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 12px;
  color: #475569;
  margin-bottom: 10px;
}
.vc-det-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.vc-det-pagos {
  max-width: 280px;
}
.vc-pago-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  padding: 2px 0;
}
.vc-pago-total {
  border-top: 1px solid #e2e8f0;
  margin-top: 4px;
  padding-top: 4px;
  font-weight: 700;
  font-size: 14px;
}

/* ── Tabla ítems ────────────────────────────────────────── */
.vc-det-items {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px 8px;
}

.vc-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.vc-table th {
  position: sticky;
  top: 0;
  background: #f8fafc;
  padding: 8px 10px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  color: #64748b;
  border-bottom: 1px solid #e2e8f0;
  letter-spacing: 0.3px;
  z-index: 1;
}
.vc-table td {
  padding: 8px 10px;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}
.vc-item-row:hover td { background: #f8fafc; }

.vc-btn-ver {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 10px;
  letter-spacing: 0.5px;
}

/* ── Tabla insumos expandida ────────────────────────────── */
.vc-insumos-row td {
  background: #f0fdf4;
  padding: 6px 10px;
}
.vc-table-insumos {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
.vc-table-insumos th {
  padding: 4px 8px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  color: #166534;
  border-bottom: 1px solid #bbf7d0;
}
.vc-table-insumos td {
  padding: 3px 8px;
  border-bottom: 1px solid #dcfce7;
  color: #15803d;
}

/* ── RESPONSIVE ─────────────────────────────────────────── */
@media (max-width: 768px) {
  .vc-body {
    flex-direction: column;
  }
  .vc-panel-left {
    width: 100%;
    max-height: 280px;
  }
  .vc-panel-right {
    min-height: 300px;
  }
  .vc-filter-row {
    gap: 10px;
  }
  .vc-btn-buscar span, .vc-btn-hoy span { display: none; }
  .vc-btn-buscar, .vc-btn-hoy { padding: 0 12px; }
}

@media (max-width: 576px) {
  .vc-filter-row {
    flex-direction: column;
    align-items: stretch;
  }
  .vc-btn-buscar {
    width: 100%;
    justify-content: center;
  }
  .vc-btn-buscar span, .vc-btn-hoy span { display: inline; }
  .vc-radios { flex-wrap: wrap; }
  .vc-det-meta { gap: 6px; }
  .vc-table th:nth-child(3),
  .vc-table td:nth-child(3) { display: none; }
}
</style>
