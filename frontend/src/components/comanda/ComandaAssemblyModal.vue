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

        <!-- Sin opciones del día -->
        <div v-if="!categories.length" class="no-options">
          <i class="bi bi-calendar-x text-muted fs-2"></i>
          <p class="text-muted mt-2">No hay menú del día configurado para este plato.</p>
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

        <!-- Novedades -->
        <div class="assembly-cat">
          <div class="assembly-cat__header">
            <span class="assembly-cat__name">
              <i class="bi bi-chat-text me-1 text-secondary"></i>
              Novedades <small class="text-muted fw-normal">(opcional)</small>
            </span>
          </div>
          <div class="chips">
            <button
              v-for="n in preloadedNotes"
              :key="n.id"
              class="chip"
              :class="{ 'chip--active': selectedNotes.includes(n.name) }"
              @click="toggleNote(n.name)"
            >{{ n.name }}</button>
          </div>
          <input
            v-model="customNote"
            type="text"
            class="form-control form-control-sm mt-2"
            placeholder="Comentario libre..."
            maxlength="200"
          />
        </div>

        <!-- Cantidad -->
        <div class="assembly-qty">
          <label class="fw-semibold text-secondary me-3">Cantidad</label>
          <div class="qty-control">
            <button class="qty-btn" @click="qty = Math.max(1, qty - 1)">
              <i class="bi bi-dash-lg"></i>
            </button>
            <span class="qty-val">{{ qty }}</span>
            <button class="qty-btn" @click="qty++">
              <i class="bi bi-plus-lg"></i>
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

const categories   = ref([])
const fixedProducts = ref([])
const loadingMenu  = ref(false)
const saving       = ref(false)
const selections   = ref({})  // { category_code: { item_id, item_name, discount_qty } }
const selectedNotes = ref([])
const customNote   = ref('')
const qty          = ref(1)

watch(() => props.dish, async (dish) => {
  if (!dish) return
  qty.value = 1
  selections.value = {}
  selectedNotes.value = []
  customNote.value = ''

  if (!dish.has_assembly) {
    categories.value = []
    return
  }

  loadingMenu.value = true
  try {
    const res = await apiComanda.get(`/api/pos/comanda/menu-diario/${dish.id}`)
    categories.value    = res.data.categories
    fixedProducts.value = res.data.fixed_products

    // Pre-select defaults
    for (const cat of categories.value) {
      const defaultOpt = cat.options.find(o => o.is_default && o.available_today)
      if (defaultOpt) {
        selections.value[cat.category_code] = {
          item_id:      defaultOpt.item_id,
          item_name:    defaultOpt.item_name,
          discount_qty: defaultOpt.discount_qty,
        }
      }
    }
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

function toggleNote(name) {
  const idx = selectedNotes.value.indexOf(name)
  if (idx >= 0) selectedNotes.value.splice(idx, 1)
  else selectedNotes.value.push(name)
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

    const parts = [...selectedNotes.value]
    if (customNote.value.trim()) parts.push(customNote.value.trim())

    const res = await apiComanda.post('/api/pos/comanda/orden/item', {
      order_number:        props.orderNumber,
      date:                props.orderDate,
      table_id:            props.tableId,
      dish_id:             props.dish.id,
      quantity:            qty.value,
      notes:               parts.join(' | ') || null,
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

/* Chips novedades */
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.chip {
  padding: 5px 12px;
  border: 1.5px solid #e2e8f0;
  border-radius: 16px;
  background: #fff;
  font-size: .78rem;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  transition: all .15s;
}
.chip:hover { border-color: #64748b; }
.chip--active { border-color: #64748b; background: #1e293b; color: #fff; }

/* Cantidad */
.assembly-qty {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 4px;
}

.qty-control {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #f1f5f9;
  border-radius: 30px;
  padding: 4px;
}

.qty-btn {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: none;
  background: #fff;
  color: #1e293b;
  font-size: 1rem;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0,0,0,.1);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all .15s;
}
.qty-btn:hover { background: #2563eb; color: #fff; }

.qty-val {
  font-size: 1.2rem;
  font-weight: 700;
  color: #1e293b;
  min-width: 28px;
  text-align: center;
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
