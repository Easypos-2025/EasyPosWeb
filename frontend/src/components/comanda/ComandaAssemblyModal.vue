<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="am-modal">

      <!-- Header -->
      <div class="am-header">
        <div class="am-header__info">
          <h4 class="am-header__title">{{ dish?.name }}</h4>
          <span class="am-header__sub">Seleccione las opciones del armado</span>
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

      <!-- Sin categorías -->
      <div class="am-empty" v-else-if="!categories.length">
        <i class="bi bi-sliders2 text-muted fs-2"></i>
        <p class="text-muted mt-2">Sin opciones de armado configuradas.</p>
      </div>

      <!-- Grid de columnas -->
      <div class="am-grid" v-else>
        <div
          class="am-col"
          v-for="cat in categories"
          :key="cat.category_code"
          :class="{
            'am-col--done':    !!selections[cat.category_code],
            'am-col--pending': cat.is_required && !selections[cat.category_code]
          }"
        >
          <!-- Cabecera de columna -->
          <div class="am-col__head">
            <span class="am-col__title">{{ cat.category_name }}</span>
            <span
              v-if="cat.is_required && !selections[cat.category_code]"
              class="am-badge am-badge--req"
            >Obligatorio</span>
            <span
              v-else-if="cat.is_required && selections[cat.category_code]"
              class="am-badge am-badge--done"
            ><i class="bi bi-check-lg"></i></span>
            <span v-else class="am-badge am-badge--opt">Opcional</span>
          </div>

          <!-- Ítem seleccionado visible en la cabecera si ya eligió -->
          <div class="am-col__selected-hint" v-if="selections[cat.category_code]">
            <i class="bi bi-check-circle-fill text-success me-1"></i>
            {{ selections[cat.category_code].item_name }}
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
              <i class="bi bi-check-lg am-item__check" v-if="isSelected(cat.category_code, opt.item_id)"></i>
            </button>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="am-footer" v-if="!loadingMenu">
        <div class="am-footer__price">{{ formatPrice(dish?.price * qty) }}</div>
        <button class="btn btn-outline-secondary btn-sm" @click="$emit('close')">Cancelar</button>
        <button
          class="btn btn-primary btn-sm"
          :disabled="!isValid || saving"
          @click="add"
        >
          <span v-if="saving" class="spinner-border spinner-border-sm me-2"></span>
          <i class="bi bi-plus-circle me-1" v-else></i>
          Agregar
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import apiComanda from '@/services/apiComanda'

const props = defineProps({
  dish:           Object,
  orderNumber:    String,
  orderDate:      String,
  tableId:        Number,
  preloadedNotes: { type: Array, default: () => [] },
})
const emit = defineEmits(['close', 'added'])

const qty           = ref(1)
const categories    = ref([])
const fixedProducts = ref([])
const loadingMenu   = ref(false)
const loadError     = ref(false)
const saving        = ref(false)
const selections    = ref({})  // { category_code: { item_id, item_name, discount_qty } }

const totalSelected = computed(() =>
  Object.keys(selections.value).length
)

const isValid = computed(() => {
  if (!categories.value.length) return true
  return categories.value
    .filter(c => c.is_required)
    .every(c => !!selections.value[c.category_code])
})

function availableOpts(cat) {
  return cat.options.filter(o => o.available_today)
}

function isSelected(category_code, item_id) {
  return selections.value[category_code]?.item_id === item_id
}

function toggleOption(cat, opt) {
  if (isSelected(cat.category_code, opt.item_id)) {
    if (!cat.is_required) delete selections.value[cat.category_code]
  } else {
    selections.value[cat.category_code] = {
      item_id:      opt.item_id,
      item_name:    opt.item_name,
      discount_qty: opt.discount_qty,
    }
  }
}

function formatPrice(v) {
  if (!v) return '$0'
  return new Intl.NumberFormat('es-CO', {
    style: 'currency', currency: 'COP', maximumFractionDigits: 0,
  }).format(v)
}

async function add() {
  if (!isValid.value || saving.value) return
  saving.value = true
  try {
    const assemblySelections = Object.entries(selections.value).map(([cc, sel]) => ({
      category_code: parseInt(cc),
      item_id:       sel.item_id,
      item_name:     sel.item_name,
      discount_qty:  sel.discount_qty,
    }))
    const res = await apiComanda.post('/api/pos/comanda/orden/item', {
      order_number:        props.orderNumber,
      date:                props.orderDate,
      table_id:            props.tableId,
      dish_id:             props.dish.id,
      quantity:            qty.value,
      assembly_selections: assemblySelections,
    })
    emit('added', res.data)
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al agregar el plato')
  } finally {
    saving.value = false
  }
}

watch(() => props.dish, async (dish) => {
  if (!dish) return
  selections.value    = {}
  categories.value    = []
  fixedProducts.value = []
  loadError.value     = false
  qty.value           = 1

  if (!dish.has_assembly) return

  loadingMenu.value = true
  try {
    const res = await apiComanda.get(`/api/pos/comanda/menu-diario/${dish.id}`)
    categories.value    = res.data.categories
    fixedProducts.value = res.data.fixed_products
  } catch {
    loadError.value = true
  } finally {
    loadingMenu.value = false
  }
}, { immediate: true })
</script>

<style scoped>
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
