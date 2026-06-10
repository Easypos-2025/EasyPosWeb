<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="od-modal">

      <!-- Header -->
      <div class="od-header">
        <div class="od-header__info">
          <div class="od-header__top">
            <span class="od-header__mesa">{{ table.name }}</span>
            <span class="od-header__seq" v-if="table.daily_seq">#{{ table.daily_seq }}</span>
            <span class="od-status" :class="`od-status--${table.status}`">{{ statusLabel }}</span>
          </div>
          <div class="od-header__sub">
            <i class="bi bi-person me-1"></i>{{ table.waiter_name || 'Sin mesero' }}
            <span class="ms-3" v-if="table.order_time">
              <i class="bi bi-clock me-1"></i>{{ table.order_time }}
            </span>
          </div>
        </div>
        <div class="od-header__right">
          <span class="od-header__total">{{ formatCurrency(order?.amount ?? table.amount ?? 0) }}</span>
          <button class="od-close" @click="$emit('close')">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>
      </div>

      <!-- Loading items -->
      <div class="od-loading" v-if="loading">
        <div class="spinner-border spinner-border-sm text-primary"></div>
        <span class="ms-2 text-muted small">Cargando pedido…</span>
      </div>

      <!-- Items list -->
      <div class="od-items" v-else-if="groupedItems.length">
        <div v-for="group in groupedItems" :key="group.key" class="od-item">
          <span class="od-item__qty">{{ group.qty }}×</span>
          <div class="od-item__detail">
            <span class="od-item__name">{{ group.dish_name }}</span>
            <span
              v-for="sel in group.assembly"
              :key="sel.category_code"
              class="od-item__asm"
            >{{ sel.item_name }}</span>
            <span v-if="group.notes" class="od-item__notes">
              <i class="bi bi-pencil-fill me-1"></i>{{ group.notes }}
            </span>
          </div>
          <span class="od-item__price">{{ formatCurrency(group.totalAmount) }}</span>
          <i
            class="bi bi-check2-circle od-item__sent"
            v-if="!group.hasUnsent"
            title="Enviado a cocina"
          ></i>
        </div>
      </div>
      <div class="od-empty" v-else-if="!loading">
        <i class="bi bi-bag-x text-muted me-2"></i>
        <span class="text-muted small">Sin ítems registrados</span>
      </div>

      <!-- Action buttons -->
      <div class="od-actions">
        <button class="od-btn od-btn--outline" disabled title="Próximamente">
          <i class="bi bi-printer"></i>
          <span>Reimprimir</span>
        </button>
        <button class="od-btn od-btn--info" @click="enviarTV" :disabled="enviando || !groupedItems.length">
          <span v-if="enviando" class="spinner-border spinner-border-sm"></span>
          <i class="bi bi-tv" v-else></i>
          <span>{{ tvOk ? 'Enviado ✓' : 'Enviar a TV' }}</span>
        </button>
        <button class="od-btn od-btn--primary" @click="agregarMas">
          <i class="bi bi-plus-circle"></i>
          <span>Agregar más</span>
        </button>
        <button class="od-btn od-btn--success" disabled title="Próximamente">
          <i class="bi bi-receipt"></i>
          <span>Facturar</span>
        </button>
        <button class="od-btn od-btn--danger" @click="eliminarPedido" :disabled="cancelando">
          <span v-if="cancelando" class="spinner-border spinner-border-sm"></span>
          <i class="bi bi-trash3" v-else></i>
          <span>Eliminar pedido</span>
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiComanda from '@/services/apiComanda'

const props = defineProps({
  table: { type: Object, required: true },
})
const emit = defineEmits(['close', 'cancelled'])

const router    = useRouter()
const loading   = ref(false)
const enviando  = ref(false)
const cancelando = ref(false)
const tvOk      = ref(false)
const order     = ref(null)
const rawItems  = ref([])

const statusLabel = computed(() => {
  const m = { occupied: 'Ocupada', bill_requested: 'Solicitó cuenta', free: 'Libre' }
  return m[props.table.status] || props.table.status
})

// Grouping
function _assemblyKey(assembly) {
  return JSON.stringify(
    [...(assembly || [])].sort((a, b) => (a.category_code ?? 0) - (b.category_code ?? 0))
  )
}

const groupedItems = computed(() => {
  const groups = []
  const map = new Map()
  for (const item of rawItems.value) {
    const k = `${item.dish_id}|${_assemblyKey(item.assembly)}|${item.notes || ''}|${item.changes || ''}`
    if (map.has(k)) {
      const g = map.get(k)
      g.qty += item.quantity
      g.totalAmount += item.amount
      g.allItems.push(item)
      if (!item.sent) g.hasUnsent = true
    } else {
      const g = {
        key: k, dish_id: item.dish_id, dish_name: item.dish_name,
        qty: item.quantity, totalAmount: item.amount,
        assembly: item.assembly, notes: item.notes, changes: item.changes,
        hasUnsent: !item.sent, allItems: [item],
      }
      map.set(k, g)
      groups.push(g)
    }
  }
  return groups
})

function formatCurrency(v) {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency', currency: 'COP', maximumFractionDigits: 0,
  }).format(v || 0)
}

onMounted(async () => {
  loading.value = true
  try {
    const params = {}
    if (props.table.order_number) params.order_number = props.table.order_number
    const res = await apiComanda.get(`/api/pos/comanda/mesa/${props.table.id}/orden`, { params })
    if (res.data.order) {
      order.value    = res.data.order
      rawItems.value = res.data.items || []
    }
  } catch { /* silencioso — puede no haber pedido activo */ }
  finally { loading.value = false }
})

async function enviarTV() {
  if (!order.value || enviando.value) return
  enviando.value = true
  try {
    await apiComanda.post('/api/pos/comanda/orden/reenviar', {
      order_number: order.value.order_number,
      date:         order.value.date,
    })
    tvOk.value = true
    setTimeout(() => { tvOk.value = false }, 3000)
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al reenviar a TV')
  } finally {
    enviando.value = false
  }
}

function agregarMas() {
  const cid = localStorage.getItem('waiter_company_id')
  localStorage.setItem('pedido_ctx', JSON.stringify({
    table_id:     props.table.id,
    table_name:   props.table.name,
    waiter_name:  props.table.waiter_name || '',
    waiter_id:    props.table.waiter_id || 0,
    company_id:   cid ? parseInt(cid) : 0,
    order_number: order.value?.order_number || props.table.order_number,
    date:         order.value?.date || null,
  }))
  router.push(`/pos/comanda/pedido/${props.table.id}`)
}

async function eliminarPedido() {
  if (!confirm(`¿Eliminar el pedido de ${props.table.name}? Esta acción no se puede deshacer.`)) return
  cancelando.value = true
  try {
    await apiComanda.delete('/api/pos/comanda/mesa/cancelar', {
      data: { table_id: props.table.id },
    })
    emit('cancelled', props.table.id)
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al eliminar el pedido')
  } finally {
    cancelando.value = false
  }
}

function reimprimir() { /* placeholder */ }
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.5);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 1100;
}

.od-modal {
  background: #fff;
  border-radius: 20px 20px 0 0;
  width: 100%;
  max-width: 560px;
  max-height: 88dvh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 -8px 40px rgba(0,0,0,.2);
  overflow: hidden;
}

/* ── Header ── */
.od-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 18px 12px;
  border-bottom: 1px solid #f1f5f9;
  flex-shrink: 0;
}

.od-header__info { flex: 1; min-width: 0; }

.od-header__top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.od-header__mesa {
  font-size: 1.1rem;
  font-weight: 800;
  color: #1e293b;
}

.od-header__seq {
  font-size: .85rem;
  font-weight: 600;
  color: #64748b;
  background: #f1f5f9;
  padding: 1px 8px;
  border-radius: 8px;
}

.od-status {
  font-size: .7rem;
  font-weight: 700;
  padding: 2px 9px;
  border-radius: 10px;
}
.od-status--occupied       { background: #dbeafe; color: #1d4ed8; }
.od-status--bill_requested { background: #fef9c3; color: #92400e; }

.od-header__sub {
  font-size: .8rem;
  color: #64748b;
}

.od-header__right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.od-header__total {
  font-size: 1.15rem;
  font-weight: 800;
  color: #2563eb;
}

.od-close {
  background: none;
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  padding: 5px 9px;
  color: #64748b;
  cursor: pointer;
}

/* ── Loading / Empty ── */
.od-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  flex-shrink: 0;
}

.od-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  flex-shrink: 0;
}

/* ── Items ── */
.od-items {
  overflow-y: auto;
  flex: 1;
  padding: 8px 0;
}

.od-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 18px;
  border-bottom: 1px solid #f8fafc;
}
.od-item:last-child { border-bottom: none; }

.od-item__qty {
  font-size: .9rem;
  font-weight: 700;
  color: #2563eb;
  min-width: 28px;
  flex-shrink: 0;
  padding-top: 1px;
}

.od-item__detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.od-item__name {
  font-size: .88rem;
  font-weight: 600;
  color: #1e293b;
}

.od-item__asm {
  font-size: .75rem;
  color: #475569;
}
.od-item__asm::before { content: '• '; color: #94a3b8; }

.od-item__notes {
  font-size: .73rem;
  color: #92400e;
  font-style: italic;
}

.od-item__price {
  font-size: .85rem;
  font-weight: 600;
  color: #334155;
  flex-shrink: 0;
  padding-top: 1px;
}

.od-item__sent {
  color: #16a34a;
  font-size: .85rem;
  flex-shrink: 0;
  padding-top: 2px;
}

/* ── Actions ── */
.od-actions {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  padding: 12px 16px 16px;
  border-top: 1px solid #f1f5f9;
  flex-shrink: 0;
}

.od-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 8px;
  border: none;
  border-radius: 10px;
  font-size: .72rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity .15s;
  line-height: 1.2;
}
.od-btn i { font-size: 1.15rem; }
.od-btn:disabled { opacity: .45; cursor: not-allowed; }

.od-btn--outline  { background: #f1f5f9; color: #475569; }
.od-btn--info     { background: #dbeafe; color: #1d4ed8; }
.od-btn--primary  { background: #2563eb; color: #fff; }
.od-btn--success  { background: #dcfce7; color: #166534; }
.od-btn--danger   { background: #fee2e2; color: #dc2626; }

.od-btn--primary:not(:disabled):hover  { background: #1d4ed8; }
.od-btn--danger:not(:disabled):hover   { background: #fca5a5; }

/* ── Responsive ── */
@media (min-width: 640px) {
  .modal-overlay { align-items: center; }
  .od-modal { border-radius: 20px; max-height: 85dvh; }
  .od-actions { grid-template-columns: repeat(5, 1fr); }
}

@media (max-width: 576px) {
  .od-header { padding: 14px 14px 10px; }
  .od-item { padding: 7px 14px; }
  .od-actions { padding: 10px 12px 14px; gap: 6px; }
  .od-btn { padding: 8px 6px; font-size: .68rem; }
  .od-btn i { font-size: 1rem; }
}
</style>
