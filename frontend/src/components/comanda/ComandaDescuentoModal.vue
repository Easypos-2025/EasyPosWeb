<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="desc-modal">

      <div class="desc-modal__header">
        <div class="desc-modal__title">
          <i class="bi bi-percent me-2 text-primary"></i>
          <span>{{ item?.dish_name }}</span>
        </div>
        <button class="close-btn" @click="$emit('close')" title="Cerrar">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>

      <div class="desc-modal__body">
        <div class="desc-current" v-if="item">
          <span class="text-muted small">Valor actual</span>
          <strong>{{ formatPrice(item.amount) }}</strong>
        </div>

        <div v-if="loading" class="desc-loading">
          <div class="spinner-border spinner-border-sm text-primary"></div>
        </div>

        <div v-else class="desc-list">
          <button
            v-for="tip in tipificaciones"
            :key="tip.id"
            class="desc-chip"
            :class="{ 'desc-chip--active': tip.id === selectedId }"
            @click="select(tip)"
          >
            <i class="bi" :class="tip.id === 0 ? 'bi-arrow-counterclockwise' : (esTipoPesos(tip) ? 'bi-cash-coin' : 'bi-tag-fill')"></i>
            <span class="desc-chip__name">{{ tip.name }}</span>
            <span class="desc-chip__value" v-if="tip.discount_percentage">{{ tip.discount_percentage }}%</span>
          </button>
          <div v-if="!tipificaciones.length" class="text-muted small text-center py-3">
            No hay tipificaciones de descuento activas
          </div>
        </div>

        <div v-if="esPesosSeleccionado" class="desc-obs">
          <label class="col-label"><i class="bi bi-cash me-1"></i>Valor a descontar (pesos)</label>
          <input v-model.number="montoPesos" type="number" min="1" class="custom-input" placeholder="Ej: 5000" />
        </div>

        <div v-if="requiereObservacion" class="desc-obs">
          <label class="col-label"><i class="bi bi-pencil me-1"></i>Observación (requerida)</label>
          <input v-model="observacion" class="custom-input" maxlength="250" placeholder="Ej: nombre del empleado / cliente..." />
        </div>
      </div>

      <div class="desc-modal__footer">
        <button class="btn btn-outline-secondary" @click="$emit('close')">
          <i class="bi bi-x me-1"></i>Cancelar
        </button>
        <button class="btn btn-primary" :disabled="!canApply || applying" @click="apply">
          <span v-if="applying" class="spinner-border spinner-border-sm me-1"></span>
          <i class="bi bi-check-lg me-1" v-else></i>Aplicar
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
  item: Object,
  orderNumber: String,
})
const emit = defineEmits(['close', 'applied'])

const tipificaciones = ref([])
const loading     = ref(false)
const applying    = ref(false)
const selectedId  = ref(null)
const observacion = ref('')
const montoPesos  = ref(null)

function formatPrice(v) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v || 0)
}

// "Descuento en Pesos": tipificación real (id != 0) sin porcentaje — se
// pide el valor por pantalla y se resta del valor de este ítem.
function esTipoPesos(tip) {
  return tip.id !== 0 && !tip.discount_percentage
}

const requiereObservacion = computed(() => {
  const tip = tipificaciones.value.find(t => t.id === selectedId.value)
  return !!tip?.ask_customer_info
})

const esPesosSeleccionado = computed(() => {
  const tip = tipificaciones.value.find(t => t.id === selectedId.value)
  return !!tip && esTipoPesos(tip)
})

const canApply = computed(() => {
  if (selectedId.value === null) return false
  if (requiereObservacion.value && !observacion.value.trim()) return false
  if (esPesosSeleccionado.value && !(montoPesos.value > 0)) return false
  return true
})

async function loadTipificaciones() {
  loading.value = true
  try {
    const { data } = await apiComanda.get('/api/pos/comanda/tipificaciones-descuento')
    tipificaciones.value = data
  } catch {
    showToast('Error cargando tipificaciones de descuento', 'error')
  }
  loading.value = false
}

function select(tip) {
  selectedId.value = tip.id
  if (!tip.ask_customer_info) observacion.value = ''
  if (!esTipoPesos(tip)) montoPesos.value = null
}

async function apply() {
  if (!canApply.value || !props.item) return
  applying.value = true
  try {
    const { data } = await apiComanda.post('/api/pos/comanda/orden/item/descuento', {
      order_number: props.orderNumber,
      dish_id: props.item.dish_id,
      item: props.item.item,
      id_tipificacion: selectedId.value,
      observacion: observacion.value.trim() || null,
      monto_pesos: esPesosSeleccionado.value ? montoPesos.value : null,
    })
    showToast(selectedId.value === 0 ? 'Descuento removido' : 'Descuento aplicado', 'success')
    emit('applied', { item: props.item, valor: data.valor, typification_id: selectedId.value })
  } catch (e) {
    showToast(e?.response?.data?.detail ?? 'Error al aplicar el descuento', 'error')
  }
  applying.value = false
}

watch(() => props.item, (newItem) => {
  if (!newItem) return
  selectedId.value = newItem.typification_id || null
  observacion.value = ''
  montoPesos.value = null
  loadTipificaciones()
}, { immediate: true })
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.5);
  display: flex; align-items: flex-end; justify-content: center; z-index: 1100;
}
.desc-modal {
  background: #fff; border-radius: 20px 20px 0 0; width: 100%; max-width: 480px;
  max-height: 85dvh; display: flex; flex-direction: column; box-shadow: 0 -8px 40px rgba(0,0,0,.2);
}
.desc-modal__header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px 14px; border-bottom: 1px solid #f1f5f9; flex-shrink: 0;
}
.desc-modal__title { font-size: 1rem; font-weight: 700; color: #1e293b; display: flex; align-items: center; min-width: 0; }
.desc-modal__title span { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.close-btn {
  flex-shrink: 0; background: #f1f5f9; border: none; border-radius: 50%;
  width: 34px; height: 34px; font-size: 1rem; color: #64748b; cursor: pointer;
  display: flex; align-items: center; justify-content: center; margin-left: 10px;
}
.close-btn:hover { background: #fee2e2; color: #ef4444; }

.desc-modal__body { flex: 1; overflow-y: auto; padding: 16px 20px; }

.desc-current {
  display: flex; justify-content: space-between; align-items: center;
  background: #f8fafc; border-radius: 10px; padding: 10px 14px; margin-bottom: 14px;
  font-size: 1rem; color: #1e293b;
}

.desc-loading { display: flex; justify-content: center; padding: 20px 0; }

.desc-list { display: flex; flex-direction: column; gap: 8px; }
.desc-chip {
  display: flex; align-items: center; gap: 8px; padding: 12px 14px;
  border: 1.5px solid #e2e8f0; border-radius: 10px; background: #fff;
  font-size: .85rem; font-weight: 600; color: #475569; cursor: pointer;
  transition: all .15s; text-align: left;
}
.desc-chip:hover { border-color: #2563eb; color: #2563eb; background: #eff6ff; }
.desc-chip--active { border-color: #2563eb; background: #dbeafe; color: #1d4ed8; }
.desc-chip__name { flex: 1; }
.desc-chip__value { font-size: .78rem; font-weight: 700; opacity: .85; }

.desc-obs { margin-top: 14px; }
.col-label {
  display: flex; align-items: center; font-size: .8rem; font-weight: 700;
  color: #475569; margin-bottom: 6px; text-transform: uppercase; letter-spacing: .04em;
}
.custom-input {
  width: 100%; padding: 10px 14px; border: 1.5px solid #e2e8f0; border-radius: 10px;
  font-size: .875rem; color: #1e293b; outline: none; transition: border-color .15s;
}
.custom-input:focus { border-color: #2563eb; }

.desc-modal__footer {
  display: flex; gap: 10px; padding: 14px 20px; border-top: 1px solid #f1f5f9;
  justify-content: flex-end; flex-shrink: 0;
}

@media (min-width: 600px) {
  .modal-overlay { align-items: center; }
  .desc-modal { border-radius: 20px; max-height: 82dvh; }
}
</style>
