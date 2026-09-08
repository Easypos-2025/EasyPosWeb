<template>
  <div class="crud-view ca-wrap">
    <div class="crud-header">
      <div>
        <h5 class="crud-titulo">{{ moduleName || 'Cuentas Abiertas' }}</h5>
        <p class="crud-sub">Pedidos montados sin facturar — mesas fijas, dinámicas y domicilios</p>
      </div>
      <button class="btn btn-outline-primary ca-btn-refresh" :disabled="cargandoLista" @click="refrescarLista" title="Actualizar">
        <i class="bi bi-arrow-clockwise" :class="{ spin: cargandoLista }"></i>
      </button>
    </div>

    <!-- Totales -->
    <div v-if="!cargandoLista && lista.length" class="ca-totales-bar">
      <span class="ca-total-chip">
        <span class="ca-total-lbl">{{ lista.length }} cuentas</span>
      </span>
      <span class="ca-total-chip ca-total-chip--green">
        <span class="ca-total-lbl">Total comprometido</span>
        <strong>{{ fmt(totalMontado) }}</strong>
      </span>
    </div>

    <!-- Cuerpo -->
    <div class="ca-body" :class="{ 'ca-has-selection': !!seleccionado }">

      <!-- Panel izquierdo: lista -->
      <div class="ca-panel-left card">
        <div v-if="cargandoLista" class="ca-placeholder">
          <div class="spinner-border text-primary" style="width:2rem;height:2rem;"></div>
        </div>
        <div v-else-if="!lista.length" class="ca-placeholder text-muted">
          <i class="bi bi-check-circle fs-2"></i>
          <p class="mt-2 mb-0">No hay cuentas abiertas en este momento</p>
        </div>
        <div v-else class="ca-list">
          <div
            v-for="cta in lista"
            :key="cta.order_number"
            class="ca-row"
            :class="{ 'ca-row--active': seleccionado?.order_number === cta.order_number }"
            @click="seleccionar(cta)"
          >
            <div class="ca-row-top">
              <span class="ca-mesa">
                <span class="badge" :class="tipoBadgeClass(cta.tipo_cuenta)">{{ tipoBadgeLabel(cta.tipo_cuenta) }}</span>
                {{ cta.table_name || '—' }}
                <i v-if="cta.is_web" class="bi bi-globe2 ca-web-icon" title="Pedido desde carta digital (web)"></i>
              </span>
              <span class="ca-valor">{{ fmt(cta.amount) }}</span>
            </div>
            <div class="ca-row-bot">
              <span><i class="bi bi-hash"></i>{{ cta.order_number }}</span>
              <span><i class="bi bi-person"></i>{{ cta.waiter_name || '—' }}</span>
              <span><i class="bi bi-egg-fried"></i>{{ cta.item_count }} ítems</span>
              <span class="ca-hora text-muted ms-auto"><i class="bi bi-clock"></i>{{ cta.hora_apertura?.slice(0,5) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Panel derecho: detalle -->
      <div class="ca-panel-right card">
        <div v-if="seleccionado" class="ca-back-bar">
          <button class="ca-btn-back" @click="volverLista">
            <i class="bi bi-arrow-left"></i> Lista
          </button>
          <span class="ca-back-title">{{ seleccionado.table_name }}</span>
        </div>

        <div v-if="!seleccionado" class="ca-placeholder text-muted">
          <i class="bi bi-arrow-left-circle fs-2"></i>
          <p class="mt-2 mb-0">Selecciona una cuenta</p>
        </div>

        <template v-else>
          <div v-if="cargandoDetalle" class="ca-placeholder">
            <div class="spinner-border text-primary" style="width:2rem;height:2rem;"></div>
          </div>

          <template v-else-if="detalle">
            <div class="ca-det-scroll">
              <div class="ca-det-header">
                <div class="ca-det-title-row">
                  <div class="ca-det-title">
                    <span class="badge" :class="tipoBadgeClass(seleccionado.tipo_cuenta)">{{ tipoBadgeLabel(seleccionado.tipo_cuenta) }}</span>
                    <strong class="ms-2">{{ detalle.header.mesa }}</strong>
                  </div>
                </div>
                <div class="ca-det-meta">
                  <span><i class="bi bi-hash"></i>{{ detalle.header.numero }}</span>
                  <span><i class="bi bi-calendar3"></i>{{ detalle.header.fecha }}</span>
                  <span><i class="bi bi-clock"></i>{{ detalle.header.hora?.slice(0,5) }}</span>
                  <span v-if="detalle.header.mesero"><i class="bi bi-person"></i>{{ detalle.header.mesero }}</span>
                  <span v-if="detalle.header.comensales"><i class="bi bi-people"></i>{{ detalle.header.comensales }}</span>
                </div>
                <div v-if="detalle.header.novedad" class="ca-det-novedad">
                  <i class="bi bi-chat-left-text"></i> {{ detalle.header.novedad }}
                </div>
                <div class="ca-det-total">
                  <span>Comprometido hasta ahora</span>
                  <strong>{{ fmt(detalle.header.total) }}</strong>
                </div>
              </div>

              <div class="ca-det-items">
                <table class="ca-table">
                  <thead>
                    <tr>
                      <th>Producto / Novedades</th>
                      <th class="text-center">Cant</th>
                      <th class="text-end">Subtotal</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    <template v-for="it in detalle.items" :key="it.item">
                      <tr class="ca-item-row">
                        <td>
                          <div class="ca-item-name">{{ it.plato }}</div>
                          <div class="ca-item-tags" v-if="it.notes || it.changes || it.complimentary">
                            <span v-if="it.notes" class="ci-tag ci-note">{{ it.notes }}</span>
                            <span v-if="it.changes" class="ci-tag ci-change">{{ it.changes }}</span>
                            <span v-if="it.complimentary" class="ci-tag ci-courtesy">Cortesía</span>
                          </div>
                        </td>
                        <td class="text-center">{{ it.quantity }}</td>
                        <td class="text-end">{{ fmt(it.subtotal) }}</td>
                        <td class="text-center">
                          <button class="btn btn-sm btn-success ca-btn-ver" @click="verInsumos(it)">VER</button>
                        </td>
                      </tr>
                      <tr v-if="itemExpandido === it.item" class="ca-insumos-row">
                        <td colspan="4">
                          <div v-if="cargandoInsumos" class="text-center py-2">
                            <div class="spinner-border spinner-border-sm text-success"></div>
                          </div>
                          <div v-else-if="!insumos.length" class="text-muted small ps-2">Sin insumos registrados</div>
                          <table v-else class="ca-table-insumos">
                            <thead><tr><th>Insumo</th><th class="text-end">Cantidad</th><th>Unidad</th></tr></thead>
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
            </div>
          </template>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import api from '@/services/apis.js'
import { useModuleName } from '@/composables/useModuleName'

const { moduleName } = useModuleName()

const fmtCOP = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 })
const fmt = v => fmtCOP.format(v || 0)

const TIPO_LABELS = { fija: 'FIJA', dinamica: 'DINÁMICA', domicilio: 'DOMICILIO', sin_asignar: 'SIN MESA' }
const TIPO_CLASSES = {
  fija: 'bg-secondary', dinamica: 'bg-warning text-dark',
  domicilio: 'bg-info text-dark', sin_asignar: 'bg-danger',
}
const tipoBadgeLabel = t => TIPO_LABELS[t] || t
const tipoBadgeClass = t => TIPO_CLASSES[t] || 'bg-secondary'

const lista           = ref([])
const cargandoLista   = ref(false)
const seleccionado    = ref(null)
const detalle         = ref(null)
const cargandoDetalle = ref(false)
const itemExpandido   = ref(null)
const insumos         = ref([])
const cargandoInsumos = ref(false)

const totalMontado = computed(() => lista.value.reduce((s, r) => s + (r.amount || 0), 0))

async function cargarLista() {
  cargandoLista.value = true
  try {
    const { data } = await api.get('/api/pos/utilitarios/cuentas-abiertas')
    lista.value = data
  } catch (e) {
    console.error(e); lista.value = []
  } finally {
    cargandoLista.value = false
  }
}

async function refrescarLista() {
  if (cargandoLista.value) return
  cargandoLista.value = true
  try {
    const { data } = await api.get('/api/pos/utilitarios/cuentas-abiertas')
    lista.value = data
    if (seleccionado.value) {
      const sigue = data.find(c => c.order_number === seleccionado.value.order_number)
      if (sigue) await cargarDetalle(sigue, false)
      else volverLista()
    }
  } catch (e) { console.error(e) }
  finally { cargandoLista.value = false }
}

async function cargarDetalle(cta, showSpinner = true) {
  if (showSpinner) cargandoDetalle.value = true
  try {
    const { data } = await api.get(`/api/pos/utilitarios/cuenta-detalle/${cta.order_number}`)
    detalle.value = data
  } catch (e) { console.error(e) }
  finally { cargandoDetalle.value = false }
}

async function seleccionar(cta) {
  if (seleccionado.value?.order_number === cta.order_number) return
  seleccionado.value  = cta
  detalle.value       = null
  itemExpandido.value = null
  await cargarDetalle(cta)
}

function volverLista() {
  seleccionado.value  = null
  detalle.value       = null
  itemExpandido.value = null
}

async function verInsumos(it) {
  if (itemExpandido.value === it.item) { itemExpandido.value = null; return }
  itemExpandido.value   = it.item
  insumos.value         = []
  cargandoInsumos.value = true
  try {
    const { data } = await api.get('/api/pos/utilitarios/cuenta-insumos', {
      params: {
        order_number: seleccionado.value.order_number,
        fecha:        detalle.value.header.fecha,
        dish_id:      it.dish_id,
        item:         it.item,
      }
    })
    insumos.value = data
  } catch (e) { console.error(e); insumos.value = [] }
  finally { cargandoInsumos.value = false }
}

let timer = null
onMounted(() => {
  cargarLista()
  timer = setInterval(refrescarLista, 15000)
})
onBeforeUnmount(() => { if (timer) clearInterval(timer) })
</script>

<style scoped>
.ca-wrap { display: flex; flex-direction: column; height: 100%; gap: 10px; }
.crud-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }
.ca-btn-refresh { height: 34px; display: flex; align-items: center; gap: 6px; flex-shrink: 0; }

@keyframes spin { to { transform: rotate(360deg); } }
.spin { display: inline-block; animation: spin .7s linear infinite; }

.ca-totales-bar { display: flex; flex-wrap: wrap; gap: 8px; flex-shrink: 0; }
.ca-total-chip {
  display: flex; align-items: center; gap: 5px;
  background: #f1f5f9; border-radius: 8px;
  padding: 4px 12px; font-size: 13px; border-left: 3px solid #cbd5e1;
}
.ca-total-chip--green { background:#f0fdf4; color:#15803d; border-left-color:#22c55e; }
.ca-total-lbl { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px; opacity: .7; margin-right: 3px; }

.card { border-radius: 10px; border: 1px solid #e2e8f0; background: #fff; }
.ca-body { display: flex; gap: 16px; flex: 1; min-height: 0; }

.ca-panel-left { width: 340px; flex-shrink: 0; display: flex; flex-direction: column; overflow: hidden; }
.ca-panel-right { flex: 1; display: flex; flex-direction: column; overflow: hidden; min-width: 0; }
.ca-placeholder { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #94a3b8; padding: 32px; }

.ca-list { flex: 1; overflow-y: auto; }
.ca-row { padding: 10px 14px; border-bottom: 1px solid #f1f5f9; cursor: pointer; transition: background .12s; }
.ca-row:hover { background: #f8fafc; }
.ca-row--active { background: #eff6ff; border-left: 3px solid #3b82f6; }
.ca-row-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; gap: 8px; }
.ca-mesa { font-size: 13px; font-weight: 700; color: #1e293b; display: flex; align-items: center; gap: 5px; }
.ca-valor { font-size: 14px; font-weight: 700; color: #16a34a; white-space: nowrap; }
.ca-row-bot { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; font-size: 11px; color: #64748b; }
.ca-hora { display: flex; align-items: center; gap: 3px; }
.ca-web-icon { color: #0ea5e9; }

.ca-back-bar { display: none; align-items: center; gap: 10px; padding: 10px 14px; border-bottom: 1px solid #e2e8f0; background: #f8fafc; flex-shrink: 0; }
.ca-btn-back { display: flex; align-items: center; gap: 5px; background: none; border: 1.5px solid #1d4ed8; border-radius: 6px; padding: 5px 12px; font-size: 13px; font-weight: 600; color: #1d4ed8; cursor: pointer; }
.ca-back-title { font-size: 14px; font-weight: 700; color: #1e293b; }

.ca-det-scroll { flex: 1; overflow-y: auto; display: flex; flex-direction: column; }
.ca-det-header { padding: 14px 16px; border-bottom: 1px solid #f1f5f9; flex-shrink: 0; }
.ca-det-title-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.ca-det-meta { display: flex; flex-wrap: wrap; gap: 10px; font-size: 12px; color: #475569; margin-bottom: 8px; }
.ca-det-meta span { display: flex; align-items: center; gap: 4px; }
.ca-det-novedad { font-size: 12px; color: #92400e; background: #fffbeb; border-radius: 6px; padding: 4px 8px; margin-bottom: 8px; }
.ca-det-total { display: flex; justify-content: space-between; font-size: 13px; font-weight: 700; max-width: 280px; }

.ca-det-items { flex: 1; padding: 0 8px 16px; }
.ca-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.ca-table th { position: sticky; top: 0; background: #f8fafc; padding: 8px 10px; font-size: 11px; font-weight: 700; text-transform: uppercase; color: #64748b; border-bottom: 1px solid #e2e8f0; letter-spacing: 0.3px; z-index: 1; }
.ca-table td { padding: 8px 10px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.ca-item-row:hover td { background: #f8fafc; }
.ca-btn-ver { font-size: 11px; font-weight: 700; padding: 2px 10px; letter-spacing: 0.5px; }

.ca-insumos-row td { background: #f0fdf4; padding: 6px 10px; }
.ca-table-insumos { width: 100%; border-collapse: collapse; font-size: 12px; }
.ca-table-insumos th { padding: 4px 8px; font-size: 10px; font-weight: 700; text-transform: uppercase; color: #166534; border-bottom: 1px solid #bbf7d0; }
.ca-table-insumos td { padding: 3px 8px; border-bottom: 1px solid #dcfce7; color: #15803d; }

.ca-item-name { font-size: 13px; }
.ca-item-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }
.ci-tag { display: inline-block; font-size: 10px; font-weight: 600; background: #f1f5f9; color: #475569; border-radius: 4px; padding: 1px 6px; border: 1px solid #e2e8f0; white-space: nowrap; }
.ci-note     { background:#fefce8; color:#854d0e; border-color:#fde68a; }
.ci-change   { background:#fdf2f8; color:#86198f; border-color:#f0abfc; }
.ci-courtesy { background:#eff6ff; color:#1d4ed8; border-color:#bfdbfe; }

/* ── RESPONSIVE TABLET ── */
@media (max-width: 768px) {
  .ca-wrap { height: auto; min-height: 100%; }
  .ca-body { flex: none; display: flex; flex-direction: column; gap: 10px; min-height: 0; }
  .ca-panel-left { width: 100%; height: auto; overflow: visible; flex: none; }
  .ca-body.ca-has-selection .ca-panel-left { display: none; }
  .ca-panel-right { flex: none; height: auto; overflow: visible; }
  .ca-body:not(.ca-has-selection) .ca-panel-right { display: none; }
  .ca-list { overflow: visible; height: auto; }
  .ca-det-scroll { overflow: visible; height: auto; flex: none; }
  .ca-det-items { flex: none; }
  .ca-back-bar { display: flex; }
  .ca-totales-bar { position: sticky; top: 0; z-index: 15; border-radius: 8px; padding: 6px 8px; margin: 0; background: var(--color-bg, #f1f5f9); }
}

/* ── RESPONSIVE MÓVIL PEQUEÑO ── */
@media (max-width: 576px) {
  .ca-row-bot { gap: 6px; }
  .ca-totales-bar { gap: 6px; }
  .ca-total-chip { padding: 3px 8px; font-size: 12px; }
  .ca-det-meta { gap: 6px; }
}

/* ── LANDSCAPE MÓVIL ── */
@media (max-width: 768px) and (orientation: landscape) {
  .ca-wrap { height: auto; min-height: 100%; }
  .ca-body { flex-direction: row; gap: 12px; }
  .ca-body.ca-has-selection .ca-panel-left { display: flex !important; width: 240px; flex-shrink: 0; max-height: 50vh; overflow-y: auto; }
  .ca-body:not(.ca-has-selection) .ca-panel-right { display: flex !important; }
  .ca-panel-right { flex: 1; }
  .ca-list { overflow-y: auto; max-height: calc(50vh - 20px); height: auto; }
  .ca-det-scroll { overflow-y: auto; max-height: calc(50vh - 20px); height: auto; flex: 1; }
  .ca-back-bar { display: none; }
}
</style>
