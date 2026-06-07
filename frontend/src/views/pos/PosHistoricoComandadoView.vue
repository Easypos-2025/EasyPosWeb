<template>
  <div class="hc-wrap">

    <!-- Filtro fecha -->
    <div class="hc-filter card">
      <div class="hc-filter__inner">
        <div class="he-filter-group">
          <label class="he-label">Fecha</label>
          <CustomDatePicker v-model="fecha" @update:modelValue="buscar" />
        </div>
        <button class="btn btn-primary btn-sm" @click="buscar" :disabled="loading">
          <i class="bi bi-search me-1"></i>Buscar
        </button>
      </div>

      <div v-if="orders.length" class="hc-chips">
        <span class="hc-chip">
          <i class="bi bi-list-check me-1"></i>
          <strong>{{ orders.length }}</strong> pedidos
        </span>
        <span class="hc-chip hc-chip--green" v-if="countByType('receipt')">
          <i class="bi bi-receipt me-1"></i>
          <strong>{{ countByType('receipt') }}</strong> recibos
        </span>
        <span class="hc-chip hc-chip--blue" v-if="countByType('dian')">
          <i class="bi bi-file-earmark-text me-1"></i>
          <strong>{{ countByType('dian') }}</strong> facturas DIAN
        </span>
        <span class="hc-chip hc-chip--red" v-if="countByType('deleted')">
          <i class="bi bi-trash3 me-1"></i>
          <strong>{{ countByType('deleted') }}</strong> eliminados
        </span>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="hc-loading">
      <div class="spinner-border spinner-border-sm text-primary me-2"></div> Cargando...
    </div>

    <!-- Sin resultados -->
    <div v-else-if="!loading && !orders.length" class="hc-empty">
      <i class="bi bi-inbox hc-empty-icon"></i>
      <p>Sin pedidos facturados ni eliminados para {{ fecha }}</p>
    </div>

    <!-- Lista -->
    <div v-else class="hc-list">
      <div v-for="ord in orders" :key="ord.order_number"
           class="hc-card card"
           :class="{ 'hc-card--open': expandido === ord.order_number }">

        <!-- Cabecera -->
        <div class="hc-card-head" @click="toggle(ord.order_number)">
          <div class="hc-head-left">
            <span class="hc-badge-mesa" :class="badgeClass(ord.doc_type)">
              {{ ord.table_name || '—' }}
            </span>
            <span class="hc-order-num">{{ ord.order_number }}</span>
            <span class="hc-hora">{{ ord.time }}</span>
          </div>
          <div class="hc-head-center">
            <span v-if="ord.waiter" class="hc-waiter">
              <i class="bi bi-person me-1"></i>{{ ord.waiter }}
            </span>
            <span class="hc-doc-badge" :class="`doc-${ord.doc_type}`">
              <i :class="docIcon(ord.doc_type)" class="me-1"></i>{{ docLabel(ord.doc_type) }}
              <span v-if="ord.invoice?.number"> #{{ ord.invoice.number }}</span>
            </span>
          </div>
          <div class="hc-head-right">
            <span class="hc-amount">{{ fmt(ord.amount) }}</span>
            <i :class="expandido === ord.order_number ? 'bi bi-chevron-up' : 'bi bi-chevron-down'" class="hc-chevron"></i>
          </div>
        </div>

        <!-- Detalle expandido -->
        <div v-if="expandido === ord.order_number" class="hc-detail">

          <!-- Banner eliminado -->
          <div v-if="ord.deletion" class="hc-del-banner">
            <i class="bi bi-person-x-fill me-2"></i>
            <strong>Eliminado por:</strong> {{ ord.deletion.quien || 'Desconocido' }}
            <span v-if="ord.deletion.motivo"> — <em>{{ ord.deletion.motivo }}</em></span>
          </div>

          <div class="hc-compare">
            <!-- Comandado -->
            <div class="hc-col">
              <div class="hc-col__hdr hc-col__hdr--cmd">
                <i class="bi bi-receipt-cutoff me-1"></i>Comandado
                <span v-if="!ord.commanded_items.length" class="hc-col__note">(sin registro archivado)</span>
              </div>
              <div v-if="ord.commanded_items.length" class="hc-col__body">
                <table class="hc-tbl">
                  <thead><tr>
                    <th>Plato</th><th class="text-end">Cant.</th>
                    <th class="text-end">Valor</th><th>Novedad</th>
                  </tr></thead>
                  <tbody>
                    <tr v-for="it in ord.commanded_items" :key="it.Item">
                      <td>{{ it.Id_Plato }}</td>
                      <td class="text-end">{{ it.Cantidad }}</td>
                      <td class="text-end">{{ fmt(it.Valor) }}</td>
                      <td class="text-muted small">{{ it.Novedad || '—' }}</td>
                    </tr>
                  </tbody>
                  <tfoot>
                    <tr>
                      <td colspan="2" class="text-end fw-bold small">Total</td>
                      <td class="text-end fw-bold">{{ fmt(ord.commanded_items.reduce((s,i)=>s+(i.Valor||0),0)) }}</td>
                      <td></td>
                    </tr>
                  </tfoot>
                </table>
              </div>
              <div v-else class="hc-col__empty">
                <i class="bi bi-info-circle me-1"></i>
                Los ítems comandados se archivan automáticamente cuando el pedido
                pasa por la limpieza de temporales.
              </div>
            </div>

            <!-- Facturado -->
            <div class="hc-col">
              <div class="hc-col__hdr" :class="ord.invoice ? 'hc-col__hdr--inv' : 'hc-col__hdr--noinv'">
                <i :class="ord.invoice ? 'bi bi-file-earmark-check me-1' : 'bi bi-file-earmark-x me-1'"></i>
                <span v-if="ord.invoice">
                  {{ ord.invoice.type === 'dian' ? 'Factura DIAN' : 'Recibo' }}
                  <span class="hc-col__note"># {{ ord.invoice.number }}</span>
                </span>
                <span v-else>Sin factura / recibo</span>
              </div>
              <div v-if="ord.invoice?.items?.length" class="hc-col__body">
                <table class="hc-tbl">
                  <thead><tr>
                    <th>Plato</th><th class="text-end">Cant.</th>
                    <th class="text-end">Valor</th><th>Notas</th>
                  </tr></thead>
                  <tbody>
                    <tr v-for="it in ord.invoice.items" :key="it.item"
                        :class="{ 'hc-row-cort': it.complimentary }">
                      <td>{{ it.dish_id }}</td>
                      <td class="text-end">{{ it.quantity }}</td>
                      <td class="text-end">{{ fmt(it.amount) }}</td>
                      <td class="text-muted small">{{ it.notes || '—' }}</td>
                    </tr>
                  </tbody>
                  <tfoot>
                    <tr>
                      <td colspan="2" class="text-end fw-bold small">Total</td>
                      <td class="text-end fw-bold">{{ fmt(ord.invoice.amount) }}</td>
                      <td></td>
                    </tr>
                  </tfoot>
                </table>
              </div>
              <div v-else class="hc-col__empty">
                <i class="bi bi-info-circle me-1"></i>Sin detalle de ítems registrado.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/apis'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'

const hoy    = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Bogota' }).format(new Date())
const fecha  = ref(hoy)
const orders = ref([])
const loading    = ref(false)
const expandido  = ref(null)

function countByType(type) {
  return orders.value.filter(o => o.doc_type === type).length
}

function fmt(val) {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  return new Intl.NumberFormat(user.locale || 'es-CO', {
    style: 'currency', currency: user.currency_code || 'COP', maximumFractionDigits: 0,
  }).format(val || 0)
}

function toggle(np) {
  expandido.value = expandido.value === np ? null : np
}

function badgeClass(type) {
  return { receipt: 'badge--receipt', dian: 'badge--dian', deleted: 'badge--deleted' }[type] || 'badge--other'
}
function docIcon(type) {
  return { receipt: 'bi bi-receipt', dian: 'bi bi-file-earmark-text', deleted: 'bi bi-trash3' }[type] || 'bi bi-question'
}
function docLabel(type) {
  return { receipt: 'Recibo', dian: 'Factura DIAN', deleted: 'Eliminado' }[type] || type
}

async function buscar() {
  loading.value   = true
  expandido.value = null
  orders.value    = []
  try {
    const res = await api.get('/api/pos/utilitarios/command-history', {
      params: { fecha: fecha.value },
    })
    orders.value = res.data.orders || []
  } catch {
    // silencioso — auth lo maneja el interceptor
  } finally {
    loading.value = false
  }
}

onMounted(buscar)
</script>

<style scoped>
.hc-wrap { display: flex; flex-direction: column; gap: 12px; padding: 16px; max-width: 1200px; margin: 0 auto; }

/* ── Filtro ── */
.hc-filter { border-radius: 10px; overflow: hidden; padding: 12px 16px; }
.hc-filter__inner { display: flex; flex-wrap: wrap; gap: 12px; align-items: flex-end; margin-bottom: 10px; }
.he-filter-group { display: flex; flex-direction: column; gap: 4px; }
.he-label { font-size: .78rem; color: var(--bs-secondary-color); font-weight: 600; }
.hc-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.hc-chip {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 5px 12px; border-radius: 20px; font-size: .82rem;
  background: #f1f5f9; color: #334155;
}
.hc-chip--green  { background: #d1fae5; color: #065f46; }
.hc-chip--blue   { background: #dbeafe; color: #1e40af; }
.hc-chip--red    { background: #fee2e2; color: #991b1b; }

/* ── Loading / Empty ── */
.hc-loading { display: flex; align-items: center; padding: 24px; font-size: .88rem; color: var(--bs-secondary-color); }
.hc-empty   { display: flex; flex-direction: column; align-items: center; padding: 48px 16px; color: var(--bs-secondary-color); }
.hc-empty-icon { font-size: 3rem; margin-bottom: 12px; }

/* ── Lista ── */
.hc-list { display: flex; flex-direction: column; gap: 8px; }

/* ── Tarjeta ── */
.hc-card { border-radius: 10px; overflow: hidden; border: 1.5px solid var(--bs-border-color); }
.hc-card--open { border-color: #3b82f6; }

.hc-card-head {
  display: flex; align-items: center; gap: 12px; padding: 10px 14px;
  cursor: pointer; transition: background .15s;
}
.hc-card-head:hover { background: rgba(59,130,246,.04); }

.hc-head-left   { display: flex; align-items: center; gap: 10px; min-width: 0; }
.hc-head-center { flex: 1; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; padding: 0 8px; }
.hc-head-right  { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }

.hc-badge-mesa {
  padding: 3px 10px; border-radius: 20px; font-size: .8rem; font-weight: 700; white-space: nowrap;
}
.badge--receipt { background: #d1fae5; color: #065f46; }
.badge--dian    { background: #dbeafe; color: #1e40af; }
.badge--deleted { background: #fee2e2; color: #991b1b; }
.badge--other   { background: #f3f4f6; color: #374151; }

.hc-order-num { font-size: .78rem; color: var(--bs-secondary-color); overflow: hidden; text-overflow: ellipsis; max-width: 150px; white-space: nowrap; }
.hc-hora      { font-size: .8rem; color: var(--bs-secondary-color); white-space: nowrap; }
.hc-waiter    { font-size: .82rem; color: #475569; }
.hc-amount    { font-weight: 700; font-size: .95rem; }
.hc-chevron   { font-size: .8rem; color: var(--bs-secondary-color); }

.hc-doc-badge {
  font-size: .72rem; font-weight: 600; padding: 2px 8px; border-radius: 20px;
  display: inline-flex; align-items: center;
}
.doc-receipt { background: #d1fae5; color: #065f46; }
.doc-dian    { background: #dbeafe; color: #1e40af; }
.doc-deleted { background: #fee2e2; color: #991b1b; }

/* ── Detalle ── */
.hc-detail { padding: 14px; border-top: 1px solid var(--bs-border-color); }

.hc-del-banner {
  background: #fee2e2; color: #991b1b; padding: 8px 14px;
  border-radius: 8px; font-size: .84rem; margin-bottom: 14px;
}

.hc-compare { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

.hc-col { border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden; }
.hc-col__hdr {
  padding: 8px 14px; font-size: .82rem; font-weight: 600;
  display: flex; align-items: center; gap: 4px; border-bottom: 1px solid #e2e8f0;
}
.hc-col__hdr--cmd   { background: #eff6ff; color: #1e40af; border-color: #bfdbfe; }
.hc-col__hdr--inv   { background: #f0fdf4; color: #166534; border-color: #bbf7d0; }
.hc-col__hdr--noinv { background: #f8fafc; color: #94a3b8; }
.hc-col__note { font-weight: 400; font-size: .75rem; margin-left: 6px; opacity: .8; }

.hc-col__body { padding: 0; }
.hc-col__empty {
  padding: 20px 14px; font-size: .82rem; color: #94a3b8;
  text-align: center; background: #fafafa;
}

.hc-tbl { width: 100%; font-size: .82rem; border-collapse: collapse; }
.hc-tbl th { font-size: .75rem; color: var(--bs-secondary-color); padding: 6px 10px; border-bottom: 1px solid var(--bs-border-color); white-space: nowrap; }
.hc-tbl td { padding: 5px 10px; border-bottom: 1px solid var(--bs-border-color); vertical-align: top; }
.hc-tbl tr:last-child td { border-bottom: none; }
.hc-tbl tfoot td { padding: 6px 10px; background: #f8fafc; }
.hc-row-cort td { color: #16a34a; background: #f0fdf4; }

/* ── Responsive tablet ── */
@media (max-width: 768px) {
  .hc-wrap { padding: 10px; gap: 10px; }
  .hc-compare { grid-template-columns: 1fr; }
  .hc-head-center { width: 100%; padding: 0; }
  .hc-order-num { max-width: 100px; }
}

/* ── Responsive móvil ── */
@media (max-width: 576px) {
  .hc-filter__inner { flex-direction: column; align-items: stretch; }
  .hc-card-head { flex-wrap: wrap; gap: 8px; }
  .hc-head-right { flex-wrap: wrap; gap: 4px; }
  .hc-compare { grid-template-columns: 1fr; gap: 12px; }
}
</style>
