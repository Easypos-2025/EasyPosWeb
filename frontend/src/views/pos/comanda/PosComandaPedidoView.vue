<template>
  <div class="pedido-view">

    <!-- Header -->
    <div class="pedido-header">
      <div class="pedido-header__info">
        <span class="pedido-header__mesa">{{ order?.table_name }}</span>
        <span class="pedido-header__seq" v-if="order?.daily_seq">#{{ order.daily_seq }}</span>
        <span class="pedido-header__waiter">
          <i class="bi bi-person-fill me-1"></i>{{ order?.waiter_name }}
        </span>
      </div>
      <div class="pedido-header__total">
        {{ formatPrice(localTotal) }}
      </div>
    </div>

    <!-- Tabs de categorías -->
    <div class="cat-tabs-wrap" v-if="menuCategories.length">
      <button class="cat-arrow cat-arrow--left" @click="scrollCats(-1)" aria-label="Anterior">
        <i class="bi bi-chevron-left"></i>
      </button>
      <div class="cat-tabs" ref="catTabsRef">
        <button
          v-for="cat in menuCategories"
          :key="cat.category_id"
          class="cat-tab"
          :class="{ 'cat-tab--active': activeCategory === cat.category_id }"
          @click="selectCategory(cat.category_id)"
        >
          {{ cat.category_name }}
        </button>
      </div>
      <button class="cat-arrow cat-arrow--right" @click="scrollCats(1)" aria-label="Siguiente">
        <i class="bi bi-chevron-right"></i>
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
          <span class="cart-panel__count">{{ visibleItemsCount }} platos</span>
          <span class="cart-panel__count" v-if="groupedItems.length !== visibleItemsCount" style="font-size:.72rem;color:#94a3b8;margin-left:4px">({{ groupedItems.length }} líneas)</span>
          <button class="cart-panel__close d-md-none" @click="cartOpen = false">
            <i class="bi bi-chevron-down"></i>
          </button>
        </div>

        <div class="cart-items" v-if="groupedItems.length">
          <div
            v-for="group in groupedItems"
            :key="group.key"
            class="cart-item"
            :class="{ 'cart-item--unsent': group.hasUnsent, 'cart-item--sent': !group.hasUnsent }"
          >
            <!-- Fila única: [-] qty [+] · nombre · precio · notas · borrar -->
            <div class="cart-item__main">
              <div class="cart-item__qty-ctrl">
                <button class="qty-btn" @click.stop="removeGroupItem(group)"><i class="bi bi-dash-lg"></i></button>
                <span class="cart-item__qty">{{ group.qty }}</span>
                <button class="qty-btn" @click.stop="addGroupItem(group)"><i class="bi bi-plus-lg"></i></button>
              </div>
              <span class="cart-item__name">{{ group.dish_name }}</span>
              <span class="cart-item__price">{{ formatPrice(group.totalAmount) }}</span>
              <button
                class="cart-item__btn cart-item__btn--notes"
                :disabled="group.lastSent"
                :title="group.lastSent ? 'Plato ya enviado a cocina' : 'Agregar nota'"
                @click="openNotasModal(group.allItems[group.allItems.length - 1])"
              >
                <i class="bi bi-chat-text"></i>
              </button>
              <button class="cart-item__btn cart-item__btn--del" @click="removeGroupItem(group)">
                <i class="bi bi-trash3"></i>
              </button>
            </div>
            <!-- Segunda fila: pills de armado · notas · estado -->
            <div
              class="cart-item__tags"
              v-if="group.assembly?.length || group.notes || group.changes || !group.hasUnsent"
            >
              <span v-for="sel in group.assembly" :key="sel.category_code" class="ci-tag">{{ sel.item_name }}</span>
              <span v-if="group.notes" class="ci-tag ci-note">{{ group.notes }}</span>
              <span v-if="group.changes" class="ci-tag ci-change">{{ group.changes }}</span>
              <span v-if="!group.hasUnsent" class="ci-sent">✓ enviado</span>
            </div>
          </div>
        </div>

        <div class="cart-empty" v-if="!groupedItems.length">
          <i class="bi bi-bag text-muted fs-2"></i>
          <p class="text-muted small mt-2">Toca un plato para agregar</p>
        </div>

        <!-- Carrito footer -->
        <div class="cart-footer">
          <div class="cart-total">
            <span>Total</span>
            <span class="cart-total__value">{{ formatPrice(localTotal) }}</span>
          </div>
          <button
            class="btn btn-success w-100"
            @click="submitOrder"
            :disabled="!hasChanges || sending"
          >
            <span v-if="sending" class="spinner-border spinner-border-sm me-2"></span>
            <i class="bi bi-send me-2" v-else></i>
            Enviar
            <span class="badge bg-white text-success ms-2" v-if="newItemsCount">
              {{ newItemsCount }}
            </span>
          </button>
          <button class="btn btn-outline-secondary w-100 btn-sm" @click="cancelOrder">
            <i class="bi bi-x-circle me-1"></i>Cancelar
          </button>
        </div>
      </div>

    </div>

    <!-- Bottom bar (mobile: toggle carrito) -->
    <div class="mobile-bar d-md-none">
      <div class="mobile-bar__total">
        <span class="text-muted small">Total</span>
        <span class="fw-bold">{{ formatPrice(localTotal) }}</span>
      </div>
      <button class="btn btn-outline-primary btn-sm" @click="cartOpen = true">
        <i class="bi bi-bag me-1"></i>
        Ver
        <span class="badge bg-primary text-white ms-1" v-if="visibleItemsCount">{{ visibleItemsCount }}</span>
      </button>
      <button
        class="btn btn-success btn-sm"
        @click="submitOrder"
        :disabled="!hasChanges || sending"
      >
        <span v-if="sending" class="spinner-border spinner-border-sm me-1"></span>
        <i class="bi bi-send me-1" v-else></i>
        Enviar
      </button>
      <button class="btn btn-outline-secondary btn-sm mobile-bar__cancel" @click="cancelOrder">
        <i class="bi bi-x-circle"></i>
      </button>
    </div>

    <!-- Assembly modal -->
    <ComandaAssemblyModal
      v-if="assemblyDish"
      :dish="assemblyDish"
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
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import apiComanda from '@/services/apiComanda'
import ComandaProductCard from '@/components/comanda/ComandaProductCard.vue'
import ComandaAssemblyModal from '@/components/comanda/ComandaAssemblyModal.vue'
import ComandaNotasModal from '@/components/comanda/ComandaNotasModal.vue'
import Swal from 'sweetalert2'
import { showToast } from '@/utils/toast'

const route   = useRoute()
const router  = useRouter()
const tableId = computed(() => parseInt(route.params.tableId))

const ctx = (() => {
  try { return JSON.parse(localStorage.getItem('pedido_ctx') || '{}') } catch { return {} }
})()

const order          = ref(ctx.table_id === parseInt(route.params.tableId) ? {
  order_number:  ctx.order_number,
  date:          ctx.date,
  table_name:    ctx.table_name,
  waiter_name:   ctx.waiter_name,
  waiter_id:     ctx.waiter_id,
  amount:        0,
  bill_requested: false,
  daily_seq:     null,
} : null)
const items          = ref([])
const menuCategories = ref([])
const activeCategory = ref(null)
const preloadedNotes = ref([])
const cartOpen       = ref(false)
const assemblyDish   = ref(null)
const notasItem      = ref(null)
const sending        = ref(false)
const catTabsRef     = ref(null)
let _tempId = -1

// ── Helpers ────────────────────────────────────────────────────────────────
function _assemblyKey(assembly) {
  return JSON.stringify(
    [...(assembly || [])].sort((a, b) => (a.category_code ?? 0) - (b.category_code ?? 0))
  )
}

function formatPrice(v) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v || 0)
}

// ── Computed ───────────────────────────────────────────────────────────────
const currentCategoryDishes = computed(() => {
  const cat = menuCategories.value.find(c => c.category_id === activeCategory.value)
  return cat?.dishes || []
})

const groupedItems = computed(() => {
  const groups = []
  const map    = new Map()
  for (const item of items.value) {
    if (item._deleted) continue
    const k = `${item.dish_id}|${_assemblyKey(item.assembly)}|${item.notes || ''}|${item.changes || ''}`
    if (map.has(k)) {
      const g = map.get(k)
      g.qty        += item.quantity
      g.totalAmount += item.amount
      g.allItems.push(item)
      if (!item.sent || item.isNew) g.hasUnsent = true
      if (item.isNew) g.hasNew = true
    } else {
      map.set(k, {
        key: k, dish_id: item.dish_id, dish_name: item.dish_name,
        qty: item.quantity, totalAmount: item.amount,
        assembly: item.assembly, notes: item.notes, changes: item.changes,
        hasUnsent: !item.sent || item.isNew,
        hasNew: item.isNew,
        allItems: [item],
      })
      groups.push(map.get(k))
    }
  }
  for (const g of groups) {
    g.lastSent  = g.allItems.every(i => i.sent && !i.isNew)
    g.unitPrice = g.qty > 0 ? Math.round(g.totalAmount / g.qty) : 0
  }
  return groups
})

const localTotal = computed(() =>
  items.value.filter(i => !i._deleted).reduce((s, i) => s + i.amount, 0)
)

const hasChanges = computed(() =>
  items.value.some(i => i.isNew || i._dirty || i._deleted)
)

const newItemsCount = computed(() =>
  items.value.filter(i => i.isNew && !i._deleted).length
)

const visibleItemsCount = computed(() =>
  items.value.filter(i => !i._deleted).length
)

// ── Lifecycle ──────────────────────────────────────────────────────────────
onMounted(async () => {
  if (ctx.company_id) localStorage.setItem('waiter_company_id', String(ctx.company_id))
  await Promise.all([loadOrder(), loadMenu(), loadNotes()])
})

// ── Data loading ───────────────────────────────────────────────────────────
async function loadOrder() {
  try {
    const params = {}
    if (ctx.order_number) params.order_number = ctx.order_number
    const res = await apiComanda.get(`/api/pos/comanda/mesa/${tableId.value}/orden`, { params })
    if (res.data.order) {
      order.value = res.data.order
      items.value = res.data.items.map(i => ({
        ...i,
        isNew:        false,
        _deleted:     false,
        _dirty:       false,
        _origQty:     i.quantity,
        _origNotes:   i.notes,
        _origChanges: i.changes,
      }))
    } else if (!ctx.order_number) {
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

// ── Navigation ─────────────────────────────────────────────────────────────
function scrollCats(dir) {
  if (!catTabsRef.value) return
  catTabsRef.value.scrollBy({ left: dir * 200, behavior: 'smooth' })
}

function selectCategory(catId) {
  activeCategory.value = catId
  nextTick(() => {
    const btn = catTabsRef.value?.querySelector('.cat-tab--active')
    if (btn) btn.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
  })
}

// ── Local item management (no API calls) ───────────────────────────────────
function onDishSelect(dish) {
  if (dish.has_assembly) assemblyDish.value = dish
  else addSimpleDish(dish)
}

function addSimpleDish(dish) {
  items.value.push({
    dish_id: dish.id, item: _tempId--,
    dish_name: dish.name, quantity: 1, amount: dish.price || 0,
    notes: null, changes: null, assembly: [],
    sent: false, isNew: true, _deleted: false, _dirty: false,
  })
}

function onItemAdded({ dish, assemblySelections, qty }) {
  assemblyDish.value = null
  items.value.push({
    dish_id: dish.id, item: _tempId--,
    dish_name: dish.name, quantity: qty, amount: (dish.price || 0) * qty,
    notes: null, changes: null, assembly: assemblySelections,
    sent: false, isNew: true, _deleted: false, _dirty: false,
  })
}

function addGroupItem(group) {
  items.value.push({
    dish_id: group.dish_id, item: _tempId--,
    dish_name: group.dish_name, quantity: 1, amount: group.unitPrice,
    notes: group.notes || null, changes: group.changes || null,
    assembly: group.assembly || [],
    sent: false, isNew: true, _deleted: false, _dirty: false,
  })
}

function removeGroupItem(group) {
  // Prefer removing the last unsubmitted (new) item first
  const lastNew = [...group.allItems].reverse().find(i => i.isNew)
  if (lastNew) {
    const idx = items.value.indexOf(lastNew)
    if (idx >= 0) items.value.splice(idx, 1)
    return
  }
  // All items are from DB — decrease qty on last item
  const last = group.allItems[group.allItems.length - 1]
  if (last.quantity <= 1) {
    removeItem(last)
  } else {
    const unitPrice = Math.round(last.amount / last.quantity)
    last.quantity -= 1
    last.amount    = unitPrice * last.quantity
    last._dirty    = true
  }
}

async function removeItem(item) {
  const result = await Swal.fire({
    title: '¿Eliminar plato?',
    text: `¿Eliminar "${item.dish_name}" del pedido?`,
    icon: 'warning', showCancelButton: true,
    confirmButtonColor: '#e11d48',
    confirmButtonText: 'Sí, eliminar', cancelButtonText: 'Cancelar',
  })
  if (!result.isConfirmed) return
  if (item.isNew) {
    const idx = items.value.indexOf(item)
    if (idx >= 0) items.value.splice(idx, 1)
  } else {
    item._deleted = true
  }
}

function openNotasModal(item) {
  if (!item || item._deleted || item.sent && !item.isNew) return
  let categoryId = null
  for (const cat of menuCategories.value) {
    if (cat.dishes?.some(d => d.id === item.dish_id)) { categoryId = cat.category_id; break }
  }
  notasItem.value = { ...item, category_id: categoryId }
}

function onNotasSave({ notes, changes }) {
  const item = notasItem.value
  if (!item) return
  const original = items.value.find(i => i.item === item.item && i.dish_id === item.dish_id)
  if (original) {
    original.notes   = notes
    original.changes = changes
    if (!original.isNew) original._dirty = true
  }
  notasItem.value = null
}

// ── Submit / Cancel ────────────────────────────────────────────────────────
async function submitOrder() {
  if (!order.value || sending.value) return
  if (!hasChanges.value) { router.push('/restaurante'); return }
  sending.value = true
  try {
    const newItems = items.value.filter(i => i.isNew && !i._deleted)
    for (const ni of newItems) {
      await apiComanda.post('/api/pos/comanda/orden/item', {
        order_number:        order.value.order_number,
        date:                order.value.date,
        table_id:            tableId.value,
        dish_id:             ni.dish_id,
        quantity:            ni.quantity,
        assembly_selections: ni.assembly || [],
        notes:               ni.notes || null,
        changes:             ni.changes || null,
      })
    }
    const dirtyItems = items.value.filter(i => !i.isNew && i._dirty && !i._deleted)
    for (const di of dirtyItems) {
      await apiComanda.put('/api/pos/comanda/orden/item', {
        order_number: order.value.order_number,
        date:         order.value.date,
        dish_id:      di.dish_id,
        item:         di.item,
        quantity:     di.quantity,
        notes:        di.notes,
        changes:      di.changes,
      })
    }
    const deletedItems = items.value.filter(i => !i.isNew && i._deleted)
    for (const del of deletedItems) {
      await apiComanda.delete('/api/pos/comanda/orden/item', {
        data: { order_number: order.value.order_number, date: order.value.date, dish_id: del.dish_id, item: del.item }
      })
    }
    if (newItems.length) {
      await apiComanda.post('/api/pos/comanda/orden/cocina', {
        order_number: order.value.order_number,
        date:         order.value.date,
      })
    }
    router.push('/restaurante')
  } catch (e) {
    showToast(e.response?.data?.detail || 'Error al enviar', 'error', 3000)
  } finally {
    sending.value = false
  }
}

function cancelOrder() {
  router.push('/restaurante')
}
</script>

<style scoped>
.pedido-view {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
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
.cat-tabs-wrap {
  display: flex;
  align-items: center;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
  padding: 0 4px;
}

.cat-arrow {
  flex-shrink: 0;
  width: 32px;
  height: 100%;
  min-height: 52px;
  border: none;
  background: none;
  color: #94a3b8;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color .15s;
  padding: 0;
}
.cat-arrow:hover { color: #2563eb; }

.cat-tabs {
  display: flex;
  gap: 8px;
  padding: 10px 4px;
  overflow-x: auto;
  flex: 1;
  scrollbar-width: none;
}
.cat-tabs::-webkit-scrollbar { display: none; }

.cat-tab {
  padding: 10px 24px;
  border: 2px solid #e2e8f0;
  border-radius: 24px;
  background: #f8fafc;
  color: #475569;
  font-size: .9rem;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  transition: all .15s;
  letter-spacing: .01em;
}
.cat-tab:hover { background: #e2e8f0; border-color: #cbd5e1; }
.cat-tab--active { background: #2563eb; color: #fff; border-color: #2563eb; }

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
  padding: 6px 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.cart-item {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 6px 8px;
}
.cart-item--sent { background: #f0fdf4; border-color: #bbf7d0; }

.cart-item__main {
  display: flex;
  gap: 6px;
  align-items: center;
}

.cart-item__qty-ctrl {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}

.qty-btn {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  border: 1.5px solid #e2e8f0;
  background: #fff;
  color: #2563eb;
  font-size: .6rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all .15s;
  padding: 0;
}
.qty-btn:hover { background: #eff6ff; border-color: #2563eb; }
.qty-btn:active { transform: scale(.9); }

.cart-item__qty {
  font-weight: 700;
  color: #2563eb;
  font-size: .8rem;
  min-width: 16px;
  text-align: center;
}

.cart-item__name {
  flex: 1;
  font-size: .82rem;
  font-weight: 600;
  color: #1e293b;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cart-item__price {
  font-size: .8rem;
  font-weight: 700;
  color: #1e293b;
  white-space: nowrap;
  flex-shrink: 0;
}

.cart-item__btn {
  background: none;
  border: none;
  border-radius: 6px;
  padding: 3px 5px;
  font-size: .78rem;
  cursor: pointer;
  transition: all .15s;
  flex-shrink: 0;
  line-height: 1;
}
.cart-item__btn--notes { color: #94a3b8; }
.cart-item__btn--notes:hover:not(:disabled) { color: #2563eb; background: #eff6ff; }
.cart-item__btn--notes:disabled { color: #e2e8f0; cursor: not-allowed; }
.cart-item__btn--del { color: #fca5a5; }
.cart-item__btn--del:hover { color: #ef4444; background: #fff5f5; }

/* Pills de armado/notas */
.cart-item__tags {
  margin: 3px 0 0;
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
}
.ci-tag {
  background: #f1f5f9;
  color: #475569;
  font-size: .6rem;
  font-weight: 600;
  padding: 1px 5px;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
  text-transform: uppercase;
  letter-spacing: .02em;
}
.ci-note   { background: #fef3c7; color: #92400e; border-color: #fcd34d; font-style: italic; font-weight: 400; text-transform: none; }
.ci-change { background: #fff7ed; color: #c2410c; border-color: #fed7aa; font-weight: 700; text-transform: none; }
.ci-sent   { color: #16a34a; font-size: .65rem; font-weight: 700; align-self: center; }

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

.mobile-bar__cancel {
  flex-shrink: 0;
  padding: 6px 10px;
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
  .cat-tab {
    padding: 9px 20px;
    font-size: .85rem;
  }
  .cat-arrow {
    min-height: 48px;
    width: 28px;
  }
}

@media (max-width: 576px) {
  .pedido-header__waiter { display: none; }
  .menu-grid { gap: 8px; }
  .menu-panel { padding: 8px; }
  .cat-tab {
    padding: 8px 16px;
    font-size: .82rem;
  }
  .cat-arrow { width: 24px; font-size: .85rem; }
}
</style>
