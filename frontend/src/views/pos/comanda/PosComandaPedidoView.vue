<template>
  <div class="pedido-view">

    <!-- Header -->
    <div class="pedido-header">
      <button class="pedido-header__back" @click="$router.push('/pos/comanda/mesas')">
        <i class="bi bi-arrow-left"></i>
      </button>
      <div class="pedido-header__info">
        <span class="pedido-header__mesa">{{ order?.table_name }}</span>
        <span class="pedido-header__seq" v-if="order?.daily_seq">#{{ order.daily_seq }}</span>
        <span class="pedido-header__waiter">
          <i class="bi bi-person-fill me-1"></i>{{ order?.waiter_name }}
        </span>
      </div>
      <div class="pedido-header__total">
        {{ formatPrice(order?.amount || 0) }}
      </div>
      <button
        class="pedido-header__bill"
        :class="{ 'pedido-header__bill--active': order?.bill_requested }"
        @click="requestBill"
        :disabled="!order || !items.length || order.bill_requested"
        title="Solicitar cuenta"
      >
        <i class="bi bi-receipt"></i>
      </button>
    </div>

    <!-- Tabs de categorías -->
    <div class="cat-tabs" v-if="menuCategories.length">
      <button
        v-for="cat in menuCategories"
        :key="cat.category_id"
        class="cat-tab"
        :class="{ 'cat-tab--active': activeCategory === cat.category_id }"
        @click="activeCategory = cat.category_id"
      >
        {{ cat.category_name }}
      </button>
    </div>

    <!-- Body split (menu + carrito) -->
    <div class="pedido-body">

      <!-- Panel izquierdo: productos -->
      <div class="menu-panel">
        <div class="menu-grid" v-if="currentCategoryDishes.length">
          <ComandaProductCard
            v-for="dish in currentCategoryDishes"
            :key="dish.id"
            :dish="dish"
            @select="onDishSelect"
          />
        </div>
        <div v-else class="menu-empty">
          <i class="bi bi-bag-x text-muted fs-2"></i>
          <p class="text-muted mt-2">Sin productos en esta categoría</p>
        </div>
      </div>

      <!-- Panel derecho: carrito (tablet/PC) -->
      <div class="cart-panel" :class="{ 'cart-panel--open': cartOpen }">
        <div class="cart-panel__header">
          <span class="cart-panel__title">
            <i class="bi bi-bag me-2"></i>Pedido
          </span>
          <span class="cart-panel__count">{{ items.length }} platos</span>
          <button class="cart-panel__close d-md-none" @click="cartOpen = false">
            <i class="bi bi-chevron-down"></i>
          </button>
        </div>

        <div class="cart-items" v-if="items.length">
          <div
            v-for="item in items"
            :key="`${item.dish_id}-${item.item}`"
            class="cart-item"
          >
            <div class="cart-item__main">
              <span class="cart-item__qty">{{ item.quantity }}×</span>
              <div class="cart-item__detail">
                <span class="cart-item__name">{{ item.dish_name }}</span>
                <!-- Assembly selections -->
                <span
                  v-for="sel in item.assembly"
                  :key="sel.category_code"
                  class="cart-item__assembly"
                >
                  {{ sel.item_name }}
                </span>
                <!-- Notes -->
                <span v-if="item.notes" class="cart-item__notes">
                  <i class="bi bi-pencil-fill me-1"></i>{{ item.notes }}
                </span>
                <!-- Changes -->
                <span v-if="item.changes" class="cart-item__changes">
                  <i class="bi bi-arrow-left-right me-1"></i>{{ item.changes }}
                </span>
                <!-- Sent badge -->
                <span v-if="item.sent" class="cart-item__sent">
                  <i class="bi bi-check2-circle me-1"></i>Enviado a cocina
                </span>
              </div>
              <span class="cart-item__price">{{ formatPrice(item.amount) }}</span>
            </div>
            <div class="cart-item__actions">
              <button class="cart-item__btn cart-item__btn--notes" @click="openNotasModal(item)">
                <i class="bi bi-chat-text"></i>
              </button>
              <button class="cart-item__btn cart-item__btn--del" @click="removeItem(item)">
                <i class="bi bi-trash3"></i>
              </button>
            </div>
          </div>
        </div>

        <div class="cart-empty" v-else>
          <i class="bi bi-bag text-muted fs-2"></i>
          <p class="text-muted small mt-2">Toca un plato para agregar</p>
        </div>

        <!-- Carrito footer -->
        <div class="cart-footer">
          <div class="cart-total">
            <span>Total</span>
            <span class="cart-total__value">{{ formatPrice(order?.amount || 0) }}</span>
          </div>
          <button
            class="btn btn-success w-100"
            @click="sendToKitchen"
            :disabled="!unsentItems.length || sending"
          >
            <span v-if="sending" class="spinner-border spinner-border-sm me-2"></span>
            <i class="bi bi-send me-2" v-else></i>
            Enviar a Cocina
            <span class="badge bg-white text-success ms-2" v-if="unsentItems.length">
              {{ unsentItems.length }}
            </span>
          </button>
        </div>
      </div>

    </div>

    <!-- Bottom bar (mobile: toggle carrito) -->
    <div class="mobile-bar d-md-none">
      <div class="mobile-bar__total">
        <span class="text-muted small">Total</span>
        <span class="fw-bold">{{ formatPrice(order?.amount || 0) }}</span>
      </div>
      <button class="btn btn-outline-primary btn-sm" @click="cartOpen = true">
        <i class="bi bi-bag me-1"></i>
        Ver pedido
        <span class="badge bg-primary text-white ms-1" v-if="items.length">{{ items.length }}</span>
      </button>
      <button
        class="btn btn-success btn-sm"
        @click="sendToKitchen"
        :disabled="!unsentItems.length || sending"
      >
        <span v-if="sending" class="spinner-border spinner-border-sm me-1"></span>
        <i class="bi bi-send me-1" v-else></i>
        Enviar ({{ unsentItems.length }})
      </button>
    </div>

    <!-- Assembly modal -->
    <ComandaAssemblyModal
      v-if="assemblyDish"
      :dish="assemblyDish"
      :order-number="order?.order_number"
      :order-date="order?.date"
      :table-id="tableId"
      :preloaded-notes="preloadedNotes"
      @close="assemblyDish = null"
      @added="onItemAdded"
    />

    <!-- Notas modal -->
    <ComandaNotasModal
      v-if="notasItem"
      :item="notasItem"
      :preloaded-notes="preloadedNotes"
      @close="notasItem = null"
      @save="onNotasSave"
    />

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import apiComanda from '@/services/apiComanda'
import ComandaProductCard from '@/components/comanda/ComandaProductCard.vue'
import ComandaAssemblyModal from '@/components/comanda/ComandaAssemblyModal.vue'
import ComandaNotasModal from '@/components/comanda/ComandaNotasModal.vue'

const route  = useRoute()
const router = useRouter()
const tableId = computed(() => parseInt(route.params.tableId))

// Contexto pasado desde el wizard (disponible inmediatamente, antes del loadOrder)
const ctx = (() => {
  try { return JSON.parse(localStorage.getItem('pedido_ctx') || '{}') } catch { return {} }
})()

const order           = ref(ctx.table_id === parseInt(route.params.tableId) ? {
  order_number: ctx.order_number,
  date:         ctx.date,
  table_name:   ctx.table_name,
  waiter_name:  ctx.waiter_name,
  waiter_id:    ctx.waiter_id,
  amount:       0,
  bill_requested: false,
  daily_seq:    null,
} : null)
const items           = ref([])
const menuCategories  = ref([])
const activeCategory  = ref(null)
const preloadedNotes  = ref([])
const cartOpen        = ref(false)
const assemblyDish    = ref(null)
const notasItem       = ref(null)
const sending         = ref(false)

const currentCategoryDishes = computed(() => {
  const cat = menuCategories.value.find(c => c.category_id === activeCategory.value)
  return cat?.dishes || []
})

const unsentItems = computed(() => items.value.filter(i => !i.sent))

function formatPrice(v) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v)
}

onMounted(async () => {
  await Promise.all([loadOrder(), loadMenu(), loadNotes()])
})

async function loadOrder() {
  try {
    const res = await apiComanda.get(`/api/pos/comanda/mesa/${tableId.value}/orden`)
    if (res.data.order) {
      order.value = res.data.order
      items.value = res.data.items
    } else {
      // Try to open the table
      const openRes = await apiComanda.post('/api/pos/comanda/mesa/abrir', {
        table_id: tableId.value, guests_count: 1,
      })
      order.value = { order_number: openRes.data.order_number, date: openRes.data.date, amount: 0, items: [] }
    }
  } catch (e) {
    if (e.response?.status === 401) router.push('/pos/comanda/login')
  }
}

async function loadMenu() {
  try {
    const res = await apiComanda.get('/api/pos/comanda/menu')
    menuCategories.value = res.data.categories
    if (res.data.categories.length && !activeCategory.value) {
      activeCategory.value = res.data.categories[0].category_id
    }
  } catch { /* silencioso */ }
}

async function loadNotes() {
  try {
    const res = await apiComanda.get('/api/pos/comanda/novedades')
    preloadedNotes.value = res.data.notes
  } catch { /* silencioso */ }
}

function onDishSelect(dish) {
  if (dish.has_assembly) {
    assemblyDish.value = dish
  } else {
    addSimpleDish(dish)
  }
}

async function addSimpleDish(dish) {
  if (!order.value) return
  try {
    const res = await apiComanda.post('/api/pos/comanda/orden/item', {
      order_number: order.value.order_number,
      date:         order.value.date,
      table_id:     tableId.value,
      dish_id:      dish.id,
      quantity:     1,
    })
    items.value.push({
      dish_id:   dish.id,
      item:      res.data.item,
      dish_name: dish.name,
      quantity:  1,
      amount:    res.data.amount,
      notes:     null,
      changes:   null,
      assembly:  [],
      sent:      false,
    })
    if (order.value) order.value.amount = (order.value.amount || 0) + res.data.amount
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al agregar el plato')
  }
}

function onItemAdded(data) {
  assemblyDish.value = null
  // Reload order to get updated state
  loadOrder()
}

function openNotasModal(item) {
  notasItem.value = item
}

async function onNotasSave({ notes, changes }) {
  const item = notasItem.value
  if (!item || !order.value) return
  try {
    await apiComanda.put('/api/pos/comanda/orden/item', {
      order_number: order.value.order_number,
      date:         order.value.date,
      dish_id:      item.dish_id,
      item:         item.item,
      notes,
      changes,
    })
    item.notes   = notes
    item.changes = changes
    notasItem.value = null
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al guardar las novedades')
  }
}

async function removeItem(item) {
  if (!confirm(`¿Eliminar ${item.dish_name}?`)) return
  try {
    await apiComanda.delete('/api/pos/comanda/orden/item', {
      data: {
        order_number: order.value.order_number,
        date:         order.value.date,
        dish_id:      item.dish_id,
        item:         item.item,
      }
    })
    const idx = items.value.findIndex(i => i.dish_id === item.dish_id && i.item === item.item)
    if (idx >= 0) {
      if (order.value) order.value.amount = Math.max(0, (order.value.amount || 0) - item.amount)
      items.value.splice(idx, 1)
    }
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al eliminar')
  }
}

async function sendToKitchen() {
  if (!order.value || sending.value) return
  sending.value = true
  try {
    await apiComanda.post('/api/pos/comanda/orden/cocina', {
      order_number: order.value.order_number,
      date:         order.value.date,
    })
    items.value.forEach(i => { i.sent = true })
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al enviar a cocina')
  } finally {
    sending.value = false
  }
}

async function requestBill() {
  if (!order.value || order.value.bill_requested) return
  if (!confirm('¿Solicitar la cuenta para esta mesa?')) return
  try {
    await apiComanda.post('/api/pos/comanda/mesa/solicitar-cuenta', {
      table_id: tableId.value,
    })
    if (order.value) order.value.bill_requested = true
  } catch (e) {
    alert(e.response?.data?.detail || 'Error')
  }
}
</script>

<style scoped>
.pedido-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* Header */
.pedido-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.pedido-header__back {
  background: none;
  border: none;
  font-size: 1.1rem;
  color: #64748b;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 8px;
  transition: all .2s;
}
.pedido-header__back:hover { background: #f1f5f9; color: #1e293b; }

.pedido-header__info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.pedido-header__mesa {
  font-size: 1rem;
  font-weight: 700;
  color: #1e293b;
}

.pedido-header__seq {
  background: #1e293b;
  color: #fff;
  font-size: .7rem;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 8px;
}

.pedido-header__waiter {
  font-size: .8rem;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pedido-header__total {
  font-size: 1rem;
  font-weight: 700;
  color: #2563eb;
  white-space: nowrap;
}

.pedido-header__bill {
  background: none;
  border: 2px solid #e2e8f0;
  color: #64748b;
  border-radius: 10px;
  padding: 6px 10px;
  font-size: 1rem;
  cursor: pointer;
  transition: all .2s;
}
.pedido-header__bill:hover:not(:disabled) { border-color: #d97706; color: #d97706; }
.pedido-header__bill--active { border-color: #d97706; color: #d97706; background: #fffbeb; }
.pedido-header__bill:disabled { opacity: .4; cursor: not-allowed; }

/* Category tabs */
.cat-tabs {
  display: flex;
  gap: 4px;
  padding: 8px 12px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  overflow-x: auto;
  flex-shrink: 0;
  scrollbar-width: none;
}
.cat-tabs::-webkit-scrollbar { display: none; }

.cat-tab {
  padding: 7px 16px;
  border: none;
  border-radius: 20px;
  background: #f1f5f9;
  color: #475569;
  font-size: .8rem;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all .15s;
}
.cat-tab:hover { background: #e2e8f0; }
.cat-tab--active { background: #2563eb; color: #fff; }

/* Body split */
.pedido-body {
  flex: 1;
  display: flex;
  overflow: hidden;
  gap: 0;
}

/* Menu panel */
.menu-panel {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.menu-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 10px;
}

.menu-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
}

/* Cart panel (desktop: sidebar) */
.cart-panel {
  width: 320px;
  border-left: 1px solid #e2e8f0;
  background: #fff;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.cart-panel__header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  border-bottom: 1px solid #f1f5f9;
  flex-shrink: 0;
}

.cart-panel__title {
  font-weight: 700;
  color: #1e293b;
  flex: 1;
}

.cart-panel__count {
  font-size: .75rem;
  color: #94a3b8;
}

.cart-panel__close {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  font-size: 1rem;
}

.cart-items {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.cart-item {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 10px;
}

.cart-item__main {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.cart-item__qty {
  font-weight: 700;
  color: #2563eb;
  font-size: .85rem;
  white-space: nowrap;
}

.cart-item__detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.cart-item__name {
  font-size: .875rem;
  font-weight: 600;
  color: #1e293b;
}

.cart-item__assembly {
  font-size: .75rem;
  color: #64748b;
  font-weight: 500;
}

.cart-item__notes {
  font-size: .72rem;
  color: #475569;
  font-style: italic;
}

.cart-item__changes {
  font-size: .72rem;
  color: #d97706;
  font-weight: 600;
}

.cart-item__sent {
  font-size: .7rem;
  color: #16a34a;
  font-weight: 600;
}

.cart-item__price {
  font-size: .85rem;
  font-weight: 700;
  color: #1e293b;
  white-space: nowrap;
}

.cart-item__actions {
  display: flex;
  gap: 6px;
  margin-top: 8px;
  justify-content: flex-end;
}

.cart-item__btn {
  background: none;
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  padding: 4px 10px;
  font-size: .8rem;
  cursor: pointer;
  transition: all .15s;
}
.cart-item__btn--notes { color: #64748b; }
.cart-item__btn--notes:hover { border-color: #2563eb; color: #2563eb; }
.cart-item__btn--del { color: #ef4444; }
.cart-item__btn--del:hover { border-color: #ef4444; background: #fff5f5; }

.cart-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.cart-footer {
  padding: 12px;
  border-top: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex-shrink: 0;
}

.cart-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: .875rem;
  color: #475569;
}

.cart-total__value {
  font-size: 1.1rem;
  font-weight: 700;
  color: #1e293b;
}

/* Mobile bottom bar */
.mobile-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #fff;
  border-top: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.mobile-bar__total {
  display: flex;
  flex-direction: column;
  margin-right: auto;
  line-height: 1.2;
}

/* Responsive */
@media (max-width: 768px) {
  .cart-panel {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    width: 100%;
    height: 75dvh;
    border-left: none;
    border-top: 1px solid #e2e8f0;
    border-radius: 20px 20px 0 0;
    transform: translateY(100%);
    transition: transform .3s ease;
    box-shadow: 0 -8px 30px rgba(0,0,0,.15);
    z-index: 500;
  }
  .cart-panel--open {
    transform: translateY(0);
  }
  .menu-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 576px) {
  .pedido-header__waiter { display: none; }
  .menu-grid { gap: 8px; }
  .menu-panel { padding: 8px; }
}
</style>
