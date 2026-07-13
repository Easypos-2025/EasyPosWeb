<template>
  <div class="tpv-pedido">

    <!-- Header -->
    <div class="tpv-header">
      <button class="tpv-header__back" @click="cancelOrder" title="Volver a mesas">
        <i class="bi bi-arrow-left"></i>
      </button>
      <div class="tpv-header__info">
        <span class="tpv-header__mesa">{{ order?.table_name }}</span>
        <span class="tpv-header__seq" v-if="order?.daily_seq">#{{ order.daily_seq }}</span>
        <span class="tpv-header__waiter">
          <i class="bi bi-person-fill me-1"></i>{{ order?.waiter_name }}
        </span>
      </div>
      <div class="tpv-header__total">{{ formatPrice(localTotal) }}</div>
    </div>

    <!-- Categorías mobile (scroll horizontal) -->
    <div class="tpv-cats-mobile d-md-none" v-if="menuCategories.length">
      <button
        v-for="cat in menuCategories"
        :key="cat.category_id"
        class="tpv-cat-mob-btn"
        :class="{ 'tpv-cat-mob-btn--active': activeCategory === cat.category_id }"
        @click="selectCategory(cat.category_id)"
      >
        {{ cat.category_name }}
      </button>
    </div>

    <!-- Body principal -->
    <div class="tpv-body">

      <!-- Sidebar categorías (desktop/tablet) -->
      <div class="tpv-cats d-none d-md-flex">
        <button
          v-for="cat in menuCategories"
          :key="cat.category_id"
          class="tpv-cat-item"
          :class="{ 'tpv-cat-item--active': activeCategory === cat.category_id }"
          @click="selectCategory(cat.category_id)"
        >
          <div class="tpv-cat-item__img" v-if="cat.photo_path">
            <img :src="photoUrl(cat.photo_path)" :alt="cat.category_name" loading="lazy" />
          </div>
          <div class="tpv-cat-item__icon" v-else>
            <i class="bi bi-grid-3x3-gap"></i>
          </div>
          <span class="tpv-cat-item__name">{{ cat.category_name }}</span>
        </button>
      </div>

      <!-- Grid de productos -->
      <div class="tpv-products">
        <div class="tpv-grid" v-if="currentCategoryDishes.length">
          <button
            v-for="dish in currentCategoryDishes"
            :key="dish.id"
            class="tpv-product"
            :class="{ 'tpv-product--no-img': !dish.photo_path }"
            @click="onDishSelect(dish)"
          >
            <div class="tpv-product__img" v-if="dish.photo_path">
              <img :src="photoUrl(dish.photo_path)" :alt="dish.name" loading="lazy" />
            </div>
            <div class="tpv-product__body">
              <span class="tpv-product__name">{{ dish.name }}</span>
              <div class="tpv-product__footer">
                <span class="tpv-product__price">{{ formatPrice(dish.price) }}</span>
                <span class="tpv-product__badge" v-if="dish.has_assembly">
                  <i class="bi bi-sliders2"></i>
                </span>
              </div>
            </div>
          </button>
        </div>
        <div v-else class="tpv-empty">
          <i class="bi bi-bag-x fs-2 text-muted"></i>
          <p class="text-muted mt-2 small">Sin productos en esta categoría</p>
        </div>
      </div>

      <!-- Panel carrito (desktop sidebar) -->
      <div class="tpv-cart" :class="{ 'tpv-cart--open': cartOpen }">
        <div class="tpv-cart__header">
          <span class="tpv-cart__title"><i class="bi bi-bag me-2"></i>Pedido</span>
          <span class="tpv-cart__count">{{ visibleItemsCount }} ítems</span>
          <button class="tpv-cart__close d-md-none" @click="cartOpen = false">
            <i class="bi bi-chevron-down"></i>
          </button>
        </div>

        <div class="tpv-cart__items" v-if="groupedItems.length">
          <div
            v-for="group in groupedItems"
            :key="group.key"
            class="cart-item"
            :class="{ 'cart-item--sent': !group.hasUnsent }"
          >
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
                @click="openNotasModal(group.allItems[group.allItems.length - 1])"
              >
                <i class="bi bi-chat-text"></i>
              </button>
              <button class="cart-item__btn cart-item__btn--del" @click="removeGroupItem(group)">
                <i class="bi bi-trash3"></i>
              </button>
            </div>
            <div class="cart-item__tags" v-if="group.assembly?.length || group.notes || group.changes || !group.hasUnsent">
              <span v-for="sel in group.assembly" :key="sel.category_code" class="ci-tag">{{ sel.item_name }}</span>
              <span v-if="group.notes"   class="ci-tag ci-note">{{ group.notes }}</span>
              <span v-if="group.changes" class="ci-tag ci-change">{{ group.changes }}</span>
              <span v-if="!group.hasUnsent" class="ci-sent">✓ enviado</span>
            </div>
          </div>
        </div>

        <div class="tpv-cart__empty" v-if="!groupedItems.length">
          <i class="bi bi-bag fs-2 text-muted"></i>
          <p class="text-muted small mt-2">Toca un producto para agregar</p>
        </div>

        <div class="tpv-cart__footer">
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
            <span class="badge bg-white text-success ms-2" v-if="newItemsCount">{{ newItemsCount }}</span>
          </button>
          <button class="btn btn-outline-secondary w-100 btn-sm" @click="cancelOrder">
            <i class="bi bi-x-circle me-1"></i>Cancelar
          </button>
        </div>
      </div>

    </div>

    <!-- Barra inferior mobile -->
    <div class="tpv-mobile-bar d-md-none">
      <div class="tpv-mobile-bar__total">
        <span class="text-muted small">Total</span>
        <span class="fw-bold">{{ formatPrice(localTotal) }}</span>
      </div>
      <button class="btn btn-outline-primary btn-sm" @click="cartOpen = true">
        <i class="bi bi-bag me-1"></i>Ver
        <span class="badge bg-primary text-white ms-1" v-if="visibleItemsCount">{{ visibleItemsCount }}</span>
      </button>
      <button class="btn btn-success btn-sm" @click="submitOrder" :disabled="!hasChanges || sending">
        <span v-if="sending" class="spinner-border spinner-border-sm me-1"></span>
        <i class="bi bi-send me-1" v-else></i>Enviar
      </button>
      <button class="btn btn-outline-secondary btn-sm" @click="cancelOrder">
        <i class="bi bi-x-circle"></i>
      </button>
    </div>

    <!-- Modal armado -->
    <ComandaAssemblyModal
      v-if="assemblyDish"
      :dish="assemblyDish"
      :preloaded-notes="preloadedNotes"
      @close="assemblyDish = null"
      @added="onItemAdded"
    />

    <!-- Modal notas -->
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
import ComandaAssemblyModal from '@/components/comanda/ComandaAssemblyModal.vue'
import ComandaNotasModal from '@/components/comanda/ComandaNotasModal.vue'
import Swal from 'sweetalert2'
import { showToast } from '@/utils/toast'

const API_BASE = import.meta.env.VITE_API_URL || ''

const route   = useRoute()
const router  = useRouter()
const tableId = computed(() => parseInt(route.params.tableId))

const ctx = (() => {
  try { return JSON.parse(localStorage.getItem('pedido_ctx') || '{}') } catch { return {} }
})()

const order          = ref(ctx.table_id === parseInt(route.params.tableId) ? {
  order_number:   ctx.order_number,
  date:           ctx.date,
  table_name:     ctx.table_name,
  waiter_name:    ctx.waiter_name,
  daily_seq:      null,
} : null)
const items          = ref([])
const menuCategories = ref([])
const activeCategory = ref(null)
const preloadedNotes = ref([])
const cartOpen       = ref(false)
const assemblyDish   = ref(null)
const notasItem      = ref(null)
const sending        = ref(false)
let _tempId = -1

function photoUrl(path) {
  if (!path) return null
  if (path.startsWith('blob:') || path.startsWith('http')) return path
  return API_BASE + path
}

function formatPrice(v) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v || 0)
}

function _assemblyKey(assembly) {
  return JSON.stringify(
    [...(assembly || [])].sort((a, b) => (a.category_code ?? 0) - (b.category_code ?? 0))
  )
}

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
      g.qty         += item.quantity
      g.totalAmount += item.amount
      g.allItems.push(item)
      if (!item.sent || item.isNew) g.hasUnsent = true
    } else {
      map.set(k, {
        key: k, dish_id: item.dish_id, dish_name: item.dish_name,
        qty: item.quantity, totalAmount: item.amount,
        assembly: item.assembly, notes: item.notes, changes: item.changes,
        hasUnsent: !item.sent || item.isNew,
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

onMounted(async () => {
  if (ctx.company_id) localStorage.setItem('waiter_company_id', String(ctx.company_id))
  await Promise.all([loadOrder(), loadMenu(), loadNotes()])
})

async function loadOrder() {
  try {
    const params = {}
    if (ctx.order_number) params.order_number = ctx.order_number
    const res = await apiComanda.get(`/api/pos/comanda/mesa/${tableId.value}/orden`, { params })
    if (res.data.order) {
      order.value = res.data.order
      items.value = res.data.items.map(i => ({
        ...i, isNew: false, _deleted: false, _dirty: false,
        _origQty: i.quantity, _origNotes: i.notes, _origChanges: i.changes,
      }))
    } else if (!ctx.order_number) {
      const openRes = await apiComanda.post('/api/pos/comanda/mesa/abrir', {
        table_id: tableId.value, guests_count: 1,
      })
      order.value = { order_number: openRes.data.order_number, date: openRes.data.date, amount: 0 }
    }
  } catch (e) {
    if (e.response?.status === 401) router.push('/pos/tpv/login')
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

function selectCategory(catId) {
  activeCategory.value = catId
  nextTick(() => {
    const btn = document.querySelector('.tpv-cat-mob-btn.tpv-cat-mob-btn--active')
    if (btn) btn.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
  })
}

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
  const lastNew = [...group.allItems].reverse().find(i => i.isNew)
  if (lastNew) {
    const idx = items.value.indexOf(lastNew)
    if (idx >= 0) items.value.splice(idx, 1)
    return
  }
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
    title: '¿Eliminar producto?',
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
  if (!item || item._deleted || (item.sent && !item.isNew)) return
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

async function submitOrder() {
  if (!order.value || sending.value) return
  if (!hasChanges.value) { router.push('/pos/tpv/mesas'); return }
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
        order_number: order.value.order_number, date: order.value.date,
        dish_id: di.dish_id, item: di.item, quantity: di.quantity,
        notes: di.notes, changes: di.changes,
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
        order_number: order.value.order_number, date: order.value.date,
      })
    }
    router.push('/pos/tpv/mesas')
  } catch (e) {
    showToast(e.response?.data?.detail || 'Error al enviar', 'error', 3000)
  } finally {
    sending.value = false
  }
}

function cancelOrder() {
  router.push('/pos/tpv/mesas')
}
</script>

<style scoped>
.tpv-pedido {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  background: #f8fafc;
}

/* ── Header ── */
.tpv-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.tpv-header__back {
  width: 38px; height: 38px;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  background: #f8fafc;
  color: #475569;
  font-size: 1rem;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  transition: all .15s;
}
.tpv-header__back:hover { border-color: #2563eb; color: #2563eb; background: #eff6ff; }

.tpv-header__info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.tpv-header__mesa  { font-size: 1rem; font-weight: 700; color: #1e293b; }
.tpv-header__seq   { background: #1e293b; color: #fff; font-size: .7rem; font-weight: 700; padding: 2px 7px; border-radius: 8px; }
.tpv-header__waiter { font-size: .8rem; color: #64748b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tpv-header__total  { font-size: 1rem; font-weight: 700; color: #2563eb; white-space: nowrap; }

/* ── Categorías mobile ── */
.tpv-cats-mobile {
  display: flex;
  gap: 8px;
  padding: 10px 12px;
  overflow-x: auto;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
  scrollbar-width: none;
}
.tpv-cats-mobile::-webkit-scrollbar { display: none; }

.tpv-cat-mob-btn {
  padding: 9px 20px;
  border: 2px solid #e2e8f0;
  border-radius: 24px;
  background: #f8fafc;
  color: #475569;
  font-size: .88rem;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  transition: all .15s;
  touch-action: manipulation;
}
.tpv-cat-mob-btn:hover { background: #e2e8f0; }
.tpv-cat-mob-btn--active { background: #2563eb; color: #fff; border-color: #2563eb; }

/* ── Body ── */
.tpv-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* ── Sidebar categorías (desktop) ── */
.tpv-cats {
  width: 130px;
  flex-shrink: 0;
  flex-direction: column;
  gap: 4px;
  padding: 10px 8px;
  overflow-y: auto;
  background: #fff;
  border-right: 1px solid #e2e8f0;
  scrollbar-width: none;
}
.tpv-cats::-webkit-scrollbar { display: none; }

.tpv-cat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  padding: 10px 6px;
  border: 2px solid transparent;
  border-radius: 12px;
  background: #f8fafc;
  cursor: pointer;
  transition: all .15s;
  width: 100%;
  touch-action: manipulation;
  min-height: 72px;
  justify-content: center;
}
.tpv-cat-item:hover { background: #eff6ff; border-color: #bfdbfe; }
.tpv-cat-item--active { background: #dbeafe; border-color: #2563eb; }

.tpv-cat-item__img {
  width: 44px; height: 44px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
}
.tpv-cat-item__img img { width: 100%; height: 100%; object-fit: cover; }

.tpv-cat-item__icon {
  width: 44px; height: 44px;
  border-radius: 8px;
  background: #e2e8f0;
  display: flex; align-items: center; justify-content: center;
  color: #64748b;
  font-size: 1.2rem;
  flex-shrink: 0;
}
.tpv-cat-item--active .tpv-cat-item__icon { background: #bfdbfe; color: #1d4ed8; }

.tpv-cat-item__name {
  font-size: .72rem;
  font-weight: 700;
  color: #334155;
  text-align: center;
  line-height: 1.2;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
}
.tpv-cat-item--active .tpv-cat-item__name { color: #1d4ed8; }

/* ── Grid productos ── */
.tpv-products {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.tpv-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 10px;
}

.tpv-product {
  display: flex;
  flex-direction: column;
  border: 1.5px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
  cursor: pointer;
  transition: all .2s;
  min-height: 110px;
  padding: 0;
  touch-action: manipulation;
}
.tpv-product:hover  { border-color: #2563eb; box-shadow: 0 4px 12px rgba(37,99,235,.15); transform: translateY(-2px); }
.tpv-product:active { transform: scale(.97); }

.tpv-product__img {
  width: 100%;
  aspect-ratio: 4/3;
  overflow: hidden;
  background: #f1f5f9;
  flex-shrink: 0;
}
.tpv-product__img img { width: 100%; height: 100%; object-fit: cover; }

/* Sin imagen: texto ocupa todo el espacio */
.tpv-product--no-img {
  background: linear-gradient(145deg, #1e293b, #334155);
  border-color: #334155;
  justify-content: center;
}
.tpv-product--no-img .tpv-product__body {
  flex: 1;
  justify-content: center;
  padding: 12px;
}
.tpv-product--no-img .tpv-product__name {
  color: #fff;
  font-size: .9rem;
  -webkit-line-clamp: 4;
  text-align: center;
}
.tpv-product--no-img .tpv-product__price { color: #93c5fd; }

.tpv-product__body {
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.tpv-product__name {
  font-size: .82rem;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.tpv-product__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
}

.tpv-product__price {
  font-size: .88rem;
  font-weight: 700;
  color: #2563eb;
}

.tpv-product__badge {
  background: #fef3c7;
  color: #d97706;
  padding: 2px 6px;
  border-radius: 6px;
  font-size: .7rem;
}

.tpv-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
}

/* ── Carrito ── */
.tpv-cart {
  width: 300px;
  border-left: 1px solid #e2e8f0;
  background: #fff;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.tpv-cart__header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  border-bottom: 1px solid #f1f5f9;
  flex-shrink: 0;
}

.tpv-cart__title { font-weight: 700; color: #1e293b; flex: 1; }
.tpv-cart__count { font-size: .75rem; color: #94a3b8; }

.tpv-cart__close {
  background: none; border: none;
  color: #94a3b8; cursor: pointer; font-size: 1rem;
}

.tpv-cart__items {
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

.cart-item__main { display: flex; gap: 6px; align-items: center; }

.cart-item__qty-ctrl { display: flex; flex-direction: row; align-items: center; gap: 2px; flex-shrink: 0; }

.qty-btn {
  width: 20px; height: 20px;
  border-radius: 4px;
  border: 1.5px solid #e2e8f0;
  background: #fff;
  color: #2563eb;
  font-size: .6rem;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all .15s; padding: 0;
}
.qty-btn:hover { background: #eff6ff; border-color: #2563eb; }

.cart-item__qty { font-weight: 700; color: #2563eb; font-size: .8rem; min-width: 16px; text-align: center; }

.cart-item__name {
  flex: 1; font-size: .82rem; font-weight: 600; color: #1e293b;
  min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

.cart-item__price { font-size: .8rem; font-weight: 700; color: #1e293b; white-space: nowrap; flex-shrink: 0; }

.cart-item__btn {
  background: none; border: 1.5px solid transparent;
  border-radius: 7px; padding: 4px 8px; font-size: .8rem;
  cursor: pointer; transition: all .15s; flex-shrink: 0;
  line-height: 1; display: flex; align-items: center; justify-content: center;
}
.cart-item__btn--notes { color: #2563eb; background: #eff6ff; border-color: #bfdbfe; }
.cart-item__btn--notes:hover:not(:disabled) { background: #dbeafe; }
.cart-item__btn--notes:disabled { color: #cbd5e1; background: #f8fafc; border-color: #e2e8f0; cursor: not-allowed; }
.cart-item__btn--del { color: #dc2626; background: #fff1f2; border-color: #fecaca; }
.cart-item__btn--del:hover { background: #fee2e2; }

.cart-item__tags { margin: 3px 0 0; display: flex; flex-wrap: wrap; gap: 3px; }
.ci-tag {
  background: #f1f5f9; color: #475569; font-size: .6rem; font-weight: 600;
  padding: 1px 5px; border-radius: 4px; border: 1px solid #e2e8f0;
  text-transform: uppercase;
}
.ci-note   { background: #fef3c7; color: #92400e; border-color: #fcd34d; font-style: italic; font-weight: 400; text-transform: none; }
.ci-change { background: #fff7ed; color: #c2410c; border-color: #fed7aa; text-transform: none; }
.ci-sent   { color: #16a34a; font-size: .65rem; font-weight: 700; align-self: center; }

.tpv-cart__empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; }

.tpv-cart__footer {
  padding: 12px;
  border-top: 1px solid #e2e8f0;
  display: flex; flex-direction: column; gap: 8px; flex-shrink: 0;
}

.cart-total { display: flex; justify-content: space-between; align-items: center; font-size: .875rem; color: #475569; }
.cart-total__value { font-size: 1.1rem; font-weight: 700; color: #1e293b; }

/* ── Barra mobile ── */
.tpv-mobile-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #fff;
  border-top: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.tpv-mobile-bar__total { display: flex; flex-direction: column; margin-right: auto; line-height: 1.2; }

/* ── Responsive ── */
@media (max-width: 768px) {
  .tpv-cart {
    position: fixed;
    bottom: 0; left: 0; right: 0;
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
  .tpv-cart--open { transform: translateY(0); }

  .tpv-grid { grid-template-columns: repeat(3, 1fr); gap: 8px; }
  .tpv-products { padding: 8px; }
}

@media (max-width: 576px) {
  .tpv-header__waiter { display: none; }
  .tpv-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .tpv-product { min-height: 100px; }
}
</style>
