<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="assembly-modal">
      <div class="assembly-modal__header">
        <div>
          <h4 class="assembly-modal__title">{{ dish?.name }}</h4>
          <p class="assembly-modal__subtitle">Seleccione las opciones</p>
        </div>
        <button class="close-btn" @click="$emit('close')">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>

      <div class="assembly-modal__body" v-if="!loadingMenu">

        <!-- Sin opciones configuradas -->
        <div v-if="loadError" class="no-options">
          <i class="bi bi-exclamation-triangle text-warning fs-2"></i>
          <p class="text-muted mt-2">Error al cargar las opciones. Intente de nuevo.</p>
        </div>
        <div v-else-if="!categories.length" class="no-options">
          <i class="bi bi-sliders2 text-muted fs-2"></i>
          <p class="text-muted mt-2">Sin opciones de armado configuradas para este plato.</p>
        </div>

        <!-- Categorías de armado -->
        <div v-for="cat in categories" :key="cat.category_code" class="assembly-cat">
          <div class="assembly-cat__header">
            <span class="assembly-cat__name">
              {{ cat.category_name }}
            </span>
            <span class="assembly-cat__rule">
              <span v-if="cat.is_required" class="badge bg-danger">Obligatorio</span>
              <span class="text-muted ms-1" v-if="cat.max_choices > 1">
                (máx {{ cat.max_choices }})
              </span>
            </span>
          </div>

          <!-- Sin opciones disponibles hoy -->
          <p v-if="!cat.options.filter(o => o.available_today).length" class="text-muted small ps-2">
            Sin opciones disponibles hoy en esta categoría
          </p>

          <div class="assembly-options">
            <button
              v-for="opt in cat.options.filter(o => o.available_today)"
              :key="opt.item_id"
              class="assembly-option"
              :class="{ 'assembly-option--selected': isSelected(cat.category_code, opt.item_id) }"
              @click="toggleOption(cat, opt)"
            >
              <span class="assembly-option__check">
                <i class="bi bi-check-lg" v-if="isSelected(cat.category_code, opt.item_id)"></i>
              </span>
              {{ opt.item_name }}
            </button>
          </div>
        </div>

      </div>

      <div v-else class="assembly-loading">
        <div class="spinner-border text-primary"></div>
      </div>

      <div class="assembly-modal__footer">
        <div class="assembly-modal__total">
          {{ formatPrice(dish?.price * qty) }}
        </div>
        <button class="btn btn-outline-secondary" @click="$emit('close')">Cancelar</button>
        <button
          class="btn btn-primary"
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

const categories    = ref([])
const fixedProducts = ref([])
const loadingMenu   = ref(false)
const loadError     = ref(false)
const saving        = ref(false)
const selections    = ref({})  // { category_code: { item_id, item_name, discount_qty } }

watch(() => props.dish, async (dish) => {
  if (!dish) return
  selections.value = {}
  categories.value = []
  loadError.value  = false

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

const isValid = computed(() => {
  if (!categories.value.length) return true
  return categories.value
    .filter(c => c.is_required)
    .every(c => !!selections.value[c.category_code])
})

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
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v)
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
      quantity:            1,
      assembly_selections: assemblySelections,
    })
    emit('added', res.data)
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al agregar el plato')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.55);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 1100;
}

.assembly-modal {
  background: #fff;
  border-radius: 20px 20px 0 0;
  width: 100%;
  max-width: 640px;
  max-height: 90dvh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 -8px 40px rgba(0,0,0,.2);
}

.assembly-modal__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 18px 20px 12px;
  border-bottom: 1px solid #f1f5f9;
  flex-shrink: 0;
}

.assembly-modal__title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 2px;
}

.assembly-modal__subtitle {
  font-size: .8rem;
  color: #94a3b8;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.1rem;
  color: #94a3b8;
  cursor: pointer;
}

.assembly-modal__body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.no-options {
  text-align: center;
  padding: 24px 0;
}

.assembly-cat {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 14px;
}

.assembly-cat__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.assembly-cat__name {
  font-weight: 700;
  font-size: .9rem;
  color: #334155;
  text-transform: uppercase;
  letter-spacing: .5px;
}

.assembly-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.assembly-option {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1.5px solid #e2e8f0;
  border-radius: 20px;
  background: #fff;
  font-size: .875rem;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  transition: all .15s;
}
.assembly-option:hover { border-color: #2563eb; color: #2563eb; }
.assembly-option--selected {
  border-color: #2563eb;
  background: #2563eb;
  color: #fff;
}

.assembly-option__check {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid currentColor;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: .75rem;
}
.assembly-option--selected .assembly-option__check {
  background: rgba(255,255,255,.25);
  border-color: transparent;
}

/* Footer */
.assembly-modal__footer {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid #f1f5f9;
  flex-shrink: 0;
}

.assembly-modal__total {
  font-size: 1.1rem;
  font-weight: 700;
  color: #2563eb;
  margin-right: auto;
}

/* Responsive */
@media (min-width: 640px) {
  .modal-overlay { align-items: center; }
  .assembly-modal { border-radius: 20px; max-height: 85dvh; }
}

@media (max-width: 576px) {
  .assembly-modal__body { padding: 12px 14px; gap: 12px; }
  .assembly-modal__footer { padding: 12px 14px; }
}
</style>
