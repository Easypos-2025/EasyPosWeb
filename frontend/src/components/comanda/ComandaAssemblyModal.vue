<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="am-modal">

      <!-- Header -->
      <div class="am-header">
        <div class="am-header__info">
          <h4 class="am-header__title">{{ dish?.name }}</h4>
          <span class="am-header__sub">{{ variants.length ? 'Seleccione el tamaño y las opciones' : 'Seleccione las opciones del armado' }}</span>
        </div>
        <div class="am-header__right">
          <span class="am-header__status" v-if="!loadingMenu && categories.length">
            <i class="bi bi-check2-circle me-1 text-success"></i>
            {{ totalSelected }} / {{ categories.length }}
          </span>
          <button class="am-close" @click="$emit('close')">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>
      </div>

      <!-- Loading -->
      <div class="am-loading" v-if="loadingMenu">
        <div class="spinner-border text-primary"></div>
        <p class="text-muted mt-2 small">Cargando opciones…</p>
      </div>

      <!-- Error -->
      <div class="am-empty" v-else-if="loadError">
        <i class="bi bi-exclamation-triangle text-warning fs-2"></i>
        <p class="text-muted mt-2">Error al cargar las opciones.</p>
      </div>

      <!-- Tamaño (variantes): Personal / Dúo / Familiar… -->
      <div v-if="!loadingMenu && !loadError && variants.length" class="am-variants">
        <span class="am-variants__lbl">Tamaño</span>
        <div class="am-variants__list">
          <button v-for="v in variants" :key="v.id"
                  :class="['am-variant', { 'am-variant--on': variant?.id === v.id }]" @click="elegirVariante(v)">
            <span class="am-variant__name">{{ v.name }}</span>
            <span class="am-variant__price">{{ formatPrice(v.price) }}</span>
          </button>
        </div>
      </div>

      <!-- Sin categorías -->
      <div class="am-empty" v-else-if="!loadingMenu && !loadError && !categories.length && !variants.length">
        <i class="bi bi-sliders2 text-muted fs-2"></i>
        <p class="text-muted mt-2">Sin opciones de armado configuradas.</p>
      </div>

      <!-- Grid de columnas -->
      <div class="am-grid" v-if="!loadingMenu && !loadError && categories.length">
        <div
          class="am-col"
          v-for="cat in categories"
          :key="cat.category_code"
          :class="{
            'am-col--done':    selCount(cat) > 0,
            'am-col--pending': esObligatoria(cat) && selCount(cat) !== maxDe(cat)
          }"
        >
          <!-- Cabecera de columna -->
          <div class="am-col__head">
            <span class="am-col__title">{{ cat.category_name }}</span>
            <span v-if="esObligatoria(cat) && selCount(cat) !== maxDe(cat)" class="am-badge am-badge--req">Elegir {{ maxDe(cat) }} ({{ selCount(cat) }}/{{ maxDe(cat) }})</span>
            <span v-else-if="esObligatoria(cat)" class="am-badge am-badge--done"><i class="bi bi-check-lg"></i></span>
            <span v-else class="am-badge am-badge--opt">Opcional</span>
          </div>

          <!-- Elegidos -->
          <div class="am-col__selected-hint" v-if="selCount(cat)">
            <i class="bi bi-check-circle-fill text-success me-1"></i>
            {{ resumen(cat) }}
          </div>

          <!-- Sin opciones hoy -->
          <div class="am-col__empty-opt" v-if="!availableOpts(cat).length">
            <span class="text-muted small">Sin opciones disponibles hoy</span>
          </div>

          <!-- Lista de ítems -->
          <div class="am-col__body">
            <button
              v-for="opt in availableOpts(cat)"
              :key="opt.item_id"
              class="am-item"
              :class="{ 'am-item--on': isSelected(cat.category_code, opt.item_id) }"
              @click="toggleOption(cat, opt)"
            >
              <span class="am-item__dot"></span>
              <span class="am-item__name">{{ opt.item_name }}</span>
              <span v-if="opt.supply_price > 0" class="am-item__extra">+{{ formatPrice(opt.supply_price) }}</span>
              <template v-if="variant && vecesElegido(cat.category_code, opt.item_id)">
                <span class="am-item__count">×{{ vecesElegido(cat.category_code, opt.item_id) }}</span>
                <span class="am-item__minus" role="button" title="Quitar uno" @click.stop="quitarUno(cat, opt)"><i class="bi bi-dash-lg"></i></span>
              </template>
              <i class="bi bi-check-lg am-item__check" v-else-if="isSelected(cat.category_code, opt.item_id)"></i>
            </button>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="am-footer" v-if="!loadingMenu">
        <div class="am-footer__price">{{ formatPrice(unitPrice * qty) }}</div>
        <button class="btn btn-outline-secondary btn-sm" @click="$emit('close')">Cancelar</button>
        <button
          class="btn btn-primary btn-sm"
          :disabled="!isValid"
          @click="add"
        >
          <i class="bi bi-plus-circle me-1"></i>
          Agregar
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import apiComanda from '@/services/apiComanda'
import { showToast } from '@/utils/toast'

const props = defineProps({
  dish:           Object,
  preloadedNotes: { type: Array, default: () => [] },
  customerId:     { type: Number, default: 1 },     // precios de la lista del cliente del pedido
})
const emit = defineEmits(['close', 'added'])

const qty           = ref(1)
const variants      = ref([])     // [{ id, name, price, is_default, assembly: { category_code: max_choices } }]
const variant       = ref(null)
const categories    = ref([])
const fixedProducts = ref([])
const loadingMenu   = ref(false)
const loadError     = ref(false)
const selections    = ref({})  // { category_code: [ { item_id, item_name, supply_price } ] }

const selCount = cat => (selections.value[cat.category_code] || []).length

const totalSelected = computed(() =>
  categories.value.filter(c => selCount(c) > 0).length
)

// Precio mostrado = precio base + valor adicional de lo elegido (el definitivo lo calcula el servidor)
const extraPrice = computed(() =>
  Object.values(selections.value).flat().reduce((s, o) => s + (Number(o.supply_price) || 0), 0)
)
const unitPrice = computed(() => (Number(variant.value ? variant.value.price : props.dish?.price) || 0) + extraPrice.value)

// Opciones por categoría: las de la variante (Personal 2, Dúo 3, Familiar 4) o las del plato
const maxDe = cat => (variant.value?.assembly?.[cat.category_code]) || cat.max_choices
// Con variante (tamaño) completar la cantidad de sabores es siempre obligatorio
const esObligatoria = cat => !!cat.is_required || !!variant.value

const isValid = computed(() => {
  if (variants.value.length && !variant.value) return false
  if (!categories.value.length) return true
  // Exigir cantidad → exactamente las opciones permitidas; si no, libre
  return categories.value.every(c => !esObligatoria(c) || selCount(c) === maxDe(c))
})

const vecesElegido = (cc, itemId) => (selections.value[cc] || []).filter(o => o.item_id === itemId).length
function resumen(cat) {
  const cnt = new Map()
  for (const o of selections.value[cat.category_code] || []) cnt.set(o.item_name, (cnt.get(o.item_name) || 0) + 1)
  return [...cnt].map(([n, c]) => (c > 1 ? `${n} ×${c}` : n)).join(', ')
}
function quitarUno(cat, opt) {
  const list = [...(selections.value[cat.category_code] || [])]
  const i = list.map(o => o.item_id).lastIndexOf(opt.item_id)
  if (i >= 0) { list.splice(i, 1); selections.value[cat.category_code] = list }
}
// Al cambiar de tamaño se recorta lo elegido si supera las opciones de la nueva variante
function elegirVariante(v) {
  variant.value = v
  for (const c of categories.value) {
    const list = selections.value[c.category_code] || []
    if (list.length > maxDe(c)) selections.value[c.category_code] = list.slice(0, maxDe(c))
  }
}

function availableOpts(cat) {
  return cat.options.filter(o => o.available_today)
}

function isSelected(category_code, item_id) {
  return (selections.value[category_code] || []).some(o => o.item_id === item_id)
}

function toggleOption(cat, opt) {
  const cc = cat.category_code
  const list = selections.value[cc] || []
  // Con variante: cada toque suma una porción del sabor (Jamón ×2 + Cordero ×2), hasta el máximo
  if (variant.value) {
    if (list.length >= maxDe(cat)) {
      showToast(`${cat.category_name}: ya eligió ${maxDe(cat)}. Quite uno con "−" para cambiar.`, 'warning')
      return
    }
    selections.value[cc] = [...list, { item_id: opt.item_id, item_name: opt.item_name, supply_price: opt.supply_price || 0 }]
    return
  }
  if (isSelected(cc, opt.item_id)) {
    selections.value[cc] = list.filter(o => o.item_id !== opt.item_id)
    return
  }
  const pick = { item_id: opt.item_id, item_name: opt.item_name, supply_price: opt.supply_price || 0 }
  if (!cat.is_required) { selections.value[cc] = [...list, pick]; return }   // libre: una, varias o todas
  if (cat.max_choices <= 1) selections.value[cc] = [pick]                    // exige 1: reemplaza
  else if (list.length < cat.max_choices) selections.value[cc] = [...list, pick]
  else showToast(`${cat.category_name}: debe elegir exactamente ${cat.max_choices}`, 'warning')
}

function formatPrice(v) {
  if (!v) return '$0'
  return new Intl.NumberFormat('es-CO', {
    style: 'currency', currency: 'COP', maximumFractionDigits: 0,
  }).format(v)
}

function add() {
  if (!isValid.value) return
  const assemblySelections = []
  for (const [cc, list] of Object.entries(selections.value)) {
    for (const sel of list) {
      assemblySelections.push({
        category_code: parseInt(cc),
        item_id:       sel.item_id,
        item_name:     sel.item_name,
        supply_price:  sel.supply_price || 0,
      })
    }
  }
  emit('added', { dish: props.dish, assemblySelections, qty: qty.value, variant: variant.value })
}

watch(() => props.dish, async (dish) => {
  if (!dish) return
  selections.value    = {}
  variants.value      = []
  variant.value       = null
  categories.value    = []
  fixedProducts.value = []
  loadError.value     = false
  qty.value           = 1

  if (!dish.has_assembly && !dish.has_variants) return

  loadingMenu.value = true
  try {
    const res = await apiComanda.get(`/api/pos/comanda/menu-diario/${dish.id}`, { params: { customer_id: props.customerId || 1 } })
    categories.value    = res.data.categories
    fixedProducts.value = res.data.fixed_products
    variants.value      = res.data.variants || []
    variant.value       = variants.value.find(v => v.is_default) || variants.value[0] || null
    // Preseleccionar las opciones marcadas "por defecto" (Por_Default), hasta el máximo permitido
    for (const c of categories.value) {
      let defs = c.options.filter(o => o.is_default && o.available_today)
      if (c.is_required || variant.value) defs = defs.slice(0, maxDe(c))
      if (defs.length) selections.value[c.category_code] = defs.map(o => ({
        item_id: o.item_id, item_name: o.item_name, supply_price: o.supply_price || 0,
      }))
    }
  } catch {
    loadError.value = true
  } finally {
    loadingMenu.value = false
  }
}, { immediate: true })
</script>

<style scoped>
.am-variants { padding: 12px 18px; background: #fff; border-bottom: 1px solid #e2e8f0; flex-shrink: 0; }
.am-variants__lbl { display: block; font-size: .72rem; font-weight: 800; color: #64748b; text-transform: uppercase; margin-bottom: 6px; }
.am-variants__list { display: flex; gap: 8px; flex-wrap: wrap; }
.am-variant { flex: 1 1 120px; display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 10px 8px;
  border: 2px solid #e2e8f0; border-radius: 12px; background: #fff; cursor: pointer; }
.am-variant--on { border-color: #1d4ed8; background: #eff6ff; }
.am-variant__name { font-weight: 800; color: #1e293b; font-size: .95rem; }
.am-variant__price { font-weight: 700; color: #1d4ed8; font-size: .85rem; }
.am-item__count { font-size: .8rem; font-weight: 900; color: #fff; background: #16a34a; border-radius: 999px; padding: 1px 8px; margin-left: auto; }
.am-item__minus { display: inline-flex; align-items: center; justify-content: center; width: 26px; height: 26px; border-radius: 50%;
  background: #fee2e2; color: #b91c1c; margin-left: 6px; flex-shrink: 0; }
@media (max-width: 576px) {
  .am-variants { padding: 10px 12px; }
  .am-variant { flex: 1 1 30%; padding: 8px 4px; }
  .am-variant__name { font-size: .85rem; }
}
.am-item__extra { font-size: .72rem; font-weight: 700; color: #b45309; background: #fef3c7; border-radius: 999px; padding: 1px 7px; margin-left: auto; white-space: nowrap; }
/* ── Overlay ── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.55);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 1100;
}

/* ── Modal ── */
.am-modal {
  background: #f1f5f9;
  border-radius: 20px 20px 0 0;
  width: 100%;
  max-width: 900px;
  max-height: 88dvh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 -8px 40px rgba(0,0,0,.2);
  overflow: hidden;
}

/* ── Header ── */
.am-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 14px 18px 12px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.am-header__info { flex: 1; min-width: 0; }

.am-header__title {
  font-size: 1rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.am-header__sub { font-size: .78rem; color: #94a3b8; }

.am-header__right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.am-header__status {
  font-size: .8rem;
  font-weight: 600;
  color: #166534;
}

.am-close {
  background: none;
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  padding: 5px 9px;
  color: #64748b;
  cursor: pointer;
}
.am-close:hover { background: #f1f5f9; }

/* ── Loading / Empty ── */
.am-loading, .am-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

/* ── Grid ── */
.am-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 10px;
  padding: 12px;
  overflow-y: auto;
  flex: 1;
  align-items: start;
}

/* ── Columna ── */
.am-col {
  background: #fff;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
  transition: border-color .15s;
}
.am-col--done    { border-color: #22c55e; }
.am-col--pending { border-color: #f87171; }

.am-col__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  padding: 9px 12px 7px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}
.am-col--done .am-col__head    { background: #f0fdf4; }
.am-col--pending .am-col__head { background: #fff5f5; }

.am-col__title {
  font-weight: 700;
  font-size: .78rem;
  color: #1e293b;
  text-transform: uppercase;
  letter-spacing: .4px;
  flex: 1;
  min-width: 0;
}

/* Badges */
.am-badge {
  font-size: .65rem;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 10px;
  flex-shrink: 0;
  white-space: nowrap;
}
.am-badge--req  { background: #fee2e2; color: #dc2626; }
.am-badge--done { background: #dcfce7; color: #16a34a; }
.am-badge--opt  { background: #f1f5f9; color: #64748b; }

/* Hint del ítem seleccionado */
.am-col__selected-hint {
  padding: 5px 12px 4px;
  font-size: .75rem;
  font-weight: 600;
  color: #166534;
  background: #f0fdf4;
  border-bottom: 1px solid #d1fae5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.am-col__empty-opt {
  padding: 10px 12px;
  text-align: center;
}

/* ── Lista de ítems ── */
.am-col__body {
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  max-height: calc(50dvh - 80px);
}

.am-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  background: #fff;
  border: none;
  border-bottom: 1px solid #f1f5f9;
  text-align: left;
  cursor: pointer;
  transition: background .1s;
  width: 100%;
}
.am-item:last-child { border-bottom: none; }
.am-item:hover { background: #f8fafc; }

.am-item--on { background: #dcfce7; }
.am-item--on:hover { background: #bbf7d0; }

.am-item__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #cbd5e1;
  flex-shrink: 0;
  transition: background .1s;
}
.am-item--on .am-item__dot { background: #16a34a; }

.am-item__name {
  flex: 1;
  font-size: .8rem;
  font-weight: 500;
  color: #334155;
  line-height: 1.3;
}
.am-item--on .am-item__name { color: #166534; font-weight: 600; }

.am-item__check {
  font-size: .75rem;
  color: #16a34a;
  flex-shrink: 0;
}

/* ── Footer ── */
.am-footer {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 18px;
  background: #fff;
  border-top: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.am-footer__price {
  font-size: 1.05rem;
  font-weight: 700;
  color: #2563eb;
  margin-right: auto;
}

/* ── Responsive ── */
@media (min-width: 640px) {
  .modal-overlay { align-items: center; }
  .am-modal { border-radius: 20px; max-height: 85dvh; }
}

@media (max-width: 768px) {
  .am-grid {
    grid-template-columns: repeat(2, 1fr);
    padding: 8px;
    gap: 8px;
  }
  .am-col__body { max-height: calc(40dvh - 60px); }
  .am-header { padding: 12px 14px 10px; }
  .am-header__status { display: none; }
  .am-modal { max-height: 90dvh; }
}

@media (max-width: 576px) {
  .am-grid {
    grid-template-columns: repeat(2, 1fr);
    padding: 6px;
    gap: 6px;
  }
  .am-col__body { max-height: calc(35dvh - 50px); }
  .am-item { padding: 6px 10px; }
  .am-item__name { font-size: .75rem; }
  .am-footer { padding: 10px 14px; }
}
</style>
