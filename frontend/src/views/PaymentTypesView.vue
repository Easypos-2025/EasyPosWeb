<template>
  <div class="page-container">

    <!-- ── Encabezado ──────────────────────────────────────────────────── -->
    <div class="page-header">
      <div>
        <h1 class="page-title">
          <i class="bi bi-credit-card-2-front me-2"></i>{{ moduleName }}
        </h1>
        <p class="page-subtitle">Métodos de pago disponibles para recibos y facturas</p>
      </div>
      <button class="btn btn-primary" @click="openCreate">
        <i class="bi bi-plus-lg"></i> Nueva forma de pago
      </button>
    </div>

    <!-- ── Buscador ────────────────────────────────────────────────────── -->
    <div class="search-bar">
      <i class="bi bi-search"></i>
      <input v-model="search" :placeholder="`Buscar ${moduleName}...`" class="search-input" />
    </div>

    <!-- ── Estado vacío ────────────────────────────────────────────────── -->
    <div v-if="loading" class="empty-state">
      <i class="bi bi-arrow-repeat spin"></i>
      <p>Cargando...</p>
    </div>

    <div v-else-if="filtered.length === 0" class="empty-state">
      <i class="bi bi-credit-card-2-front"></i>
      <p>{{ search ? `Sin resultados para "${search}"` : 'No hay formas de pago registradas' }}</p>
      <button v-if="!search" class="btn btn-primary btn-sm" @click="openCreate">
        Agregar la primera forma de pago
      </button>
    </div>

    <!-- ── Tabla ───────────────────────────────────────────────────────── -->
    <div v-else class="sub-card p-0">
      <table class="data-table">
        <thead>
          <tr>
            <th>Nombre</th>
            <th class="text-center">Predeterminado</th>
            <th class="text-center">Suma a caja</th>
            <th class="text-center">Pedir notas</th>
            <th class="text-center">Activo</th>
            <th class="text-center">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filtered" :key="`${item.id}-${item.company_id}`">
            <td>
              <div class="pt-name">
                <i v-if="item.is_default" class="bi bi-star-fill text-warning me-1" title="Predeterminado"></i>
                <strong>{{ item.name }}</strong>
              </div>
              <div class="pt-flags">
                <span v-if="item.select_card" class="flag-chip">Tarjeta</span>
                <span v-if="item.validate_amount" class="flag-chip">Val. monto</span>
                <span v-if="item.validate_number" class="flag-chip">Val. número</span>
                <span v-if="item.ask_customer" class="flag-chip">Cliente</span>
              </div>
            </td>
            <td class="text-center">
              <span v-if="item.is_default" class="badge-default">
                <i class="bi bi-check-circle-fill"></i> Sí
              </span>
              <span v-else class="text-muted">—</span>
            </td>
            <td class="text-center">
              <span v-if="item.adds_to_cash" class="badge-yes">
                <i class="bi bi-cash"></i> Sí
              </span>
              <span v-else class="badge-no">No</span>
            </td>
            <td class="text-center">
              <span v-if="item.ask_notes" class="badge-yes">
                <i class="bi bi-pencil-square"></i> Sí
              </span>
              <span v-else class="badge-no">No</span>
            </td>
            <td class="text-center">
              <button
                :class="['toggle-btn', item.is_active ? 'toggle-on' : 'toggle-off']"
                @click="toggleActive(item)"
                :disabled="togglingId === item.id"
                :title="item.is_active ? 'Desactivar' : 'Activar'"
              >
                <i v-if="togglingId === item.id" class="bi bi-arrow-repeat spin"></i>
                <i v-else :class="item.is_active ? 'bi bi-toggle-on' : 'bi bi-toggle-off'"></i>
              </button>
            </td>
            <td class="text-center">
              <div class="action-btns">
                <button class="btn btn-sm btn-outline-primary" @click="openEdit(item)" title="Editar">
                  <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" @click="remove(item)" title="Eliminar">
                  <i class="bi bi-trash"></i>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ── Modal crear / editar ────────────────────────────────────────── -->
    <div v-if="modal" class="modal-overlay" @click.self="modal = false">
      <div class="modal-card modal-lg">
        <div class="modal-header">
          <h3>{{ editing ? 'Editar forma de pago' : 'Nueva forma de pago' }}</h3>
          <button class="modal-close" @click="modal = false"><i class="bi bi-x-lg"></i></button>
        </div>

        <div class="modal-body">
          <!-- Nombre -->
          <div class="fg mb-3">
            <label class="fg-label">Nombre <span class="text-danger">*</span></label>
            <input
              v-model="form.name"
              class="form-control"
              placeholder="Ej: Efectivo, Nequi, Transferencia..."
              autofocus
            />
          </div>

          <!-- Opciones: grid de toggles -->
          <div class="options-grid">
            <div class="opt-item" :class="{ active: form.is_active }" @click="form.is_active = !form.is_active">
              <div class="opt-icon"><i class="bi bi-power"></i></div>
              <div class="opt-info">
                <span class="opt-label">Activo</span>
                <span class="opt-desc">Disponible para usar en pagos</span>
              </div>
              <div class="opt-toggle">
                <i :class="form.is_active ? 'bi bi-toggle-on text-success' : 'bi bi-toggle-off text-muted'"></i>
              </div>
            </div>

            <div class="opt-item" :class="{ active: form.is_default }" @click="form.is_default = !form.is_default">
              <div class="opt-icon"><i class="bi bi-star"></i></div>
              <div class="opt-info">
                <span class="opt-label">Predeterminado</span>
                <span class="opt-desc">Se selecciona automáticamente</span>
              </div>
              <div class="opt-toggle">
                <i :class="form.is_default ? 'bi bi-toggle-on text-success' : 'bi bi-toggle-off text-muted'"></i>
              </div>
            </div>

            <div class="opt-item" :class="{ active: form.adds_to_cash }" @click="form.adds_to_cash = !form.adds_to_cash">
              <div class="opt-icon"><i class="bi bi-cash-stack"></i></div>
              <div class="opt-info">
                <span class="opt-label">Suma a caja</span>
                <span class="opt-desc">Suma al saldo físico de caja</span>
              </div>
              <div class="opt-toggle">
                <i :class="form.adds_to_cash ? 'bi bi-toggle-on text-success' : 'bi bi-toggle-off text-muted'"></i>
              </div>
            </div>

            <div class="opt-item" :class="{ active: form.ask_notes }" @click="form.ask_notes = !form.ask_notes">
              <div class="opt-icon"><i class="bi bi-pencil-square"></i></div>
              <div class="opt-info">
                <span class="opt-label">Pedir notas / referencia</span>
                <span class="opt-desc">Solicita un campo de texto al pagar</span>
              </div>
              <div class="opt-toggle">
                <i :class="form.ask_notes ? 'bi bi-toggle-on text-success' : 'bi bi-toggle-off text-muted'"></i>
              </div>
            </div>

            <div class="opt-item" :class="{ active: form.select_card }" @click="form.select_card = !form.select_card">
              <div class="opt-icon"><i class="bi bi-credit-card"></i></div>
              <div class="opt-info">
                <span class="opt-label">Seleccionar tarjeta</span>
                <span class="opt-desc">Requiere elegir tipo/marca de tarjeta</span>
              </div>
              <div class="opt-toggle">
                <i :class="form.select_card ? 'bi bi-toggle-on text-success' : 'bi bi-toggle-off text-muted'"></i>
              </div>
            </div>

            <div class="opt-item" :class="{ active: form.validate_amount }" @click="form.validate_amount = !form.validate_amount">
              <div class="opt-icon"><i class="bi bi-check2-circle"></i></div>
              <div class="opt-info">
                <span class="opt-label">Validar monto</span>
                <span class="opt-desc">Verifica que el monto sea exacto</span>
              </div>
              <div class="opt-toggle">
                <i :class="form.validate_amount ? 'bi bi-toggle-on text-success' : 'bi bi-toggle-off text-muted'"></i>
              </div>
            </div>

            <div class="opt-item" :class="{ active: form.validate_number }" @click="form.validate_number = !form.validate_number">
              <div class="opt-icon"><i class="bi bi-hash"></i></div>
              <div class="opt-info">
                <span class="opt-label">Validar número</span>
                <span class="opt-desc">Solicita número de transacción/aprobación</span>
              </div>
              <div class="opt-toggle">
                <i :class="form.validate_number ? 'bi bi-toggle-on text-success' : 'bi bi-toggle-off text-muted'"></i>
              </div>
            </div>

            <div class="opt-item" :class="{ active: form.ask_customer }" @click="form.ask_customer = !form.ask_customer">
              <div class="opt-icon"><i class="bi bi-person-badge"></i></div>
              <div class="opt-info">
                <span class="opt-label">Solicitar cliente</span>
                <span class="opt-desc">Requiere identificar al cliente</span>
              </div>
              <div class="opt-toggle">
                <i :class="form.ask_customer ? 'bi bi-toggle-on text-success' : 'bi bi-toggle-off text-muted'"></i>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-secondary btn-sm" @click="modal = false">Cancelar</button>
          <button class="btn btn-primary btn-sm" @click="save" :disabled="saving">
            <i v-if="saving" class="bi bi-arrow-repeat spin"></i>
            {{ saving ? 'Guardando...' : (editing ? 'Actualizar' : 'Guardar') }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { useCompanyStore } from "@/stores/companyStore"
import { useModuleName } from "@/composables/useModuleName"
import api from "@/services/apis"
import { showToast, showConfirm } from "@/utils/toast"

const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id)
const { moduleName } = useModuleName()

const items      = ref([])
const search     = ref("")
const loading    = ref(false)
const modal      = ref(false)
const saving     = ref(false)
const editing    = ref(null)
const togglingId = ref(null)

const formDef = () => ({
  name:            "",
  is_active:       true,
  is_default:      false,
  adds_to_cash:    false,
  ask_notes:       false,
  select_card:     false,
  validate_amount: false,
  validate_number: false,
  ask_customer:    false,
})
const form = ref(formDef())

const filtered = computed(() => {
  const q = search.value.toLowerCase()
  return items.value.filter(i => i.name.toLowerCase().includes(q))
})

// ── Carga ──────────────────────────────────────────────────────────────────────
async function load() {
  if (!companyId.value) return
  loading.value = true
  try {
    const res = await api.get("/api/payment-types", { params: { company_id: companyId.value } })
    items.value = res.data
  } catch {
    showToast("Error cargando formas de pago", "error")
  }
  loading.value = false
}

// ── Abrir modal ────────────────────────────────────────────────────────────────
function openCreate() {
  editing.value = null
  form.value    = formDef()
  modal.value   = true
}

function openEdit(item) {
  editing.value = item
  form.value = {
    name:            item.name,
    is_active:       !!item.is_active,
    is_default:      !!item.is_default,
    adds_to_cash:    !!item.adds_to_cash,
    ask_notes:       !!item.ask_notes,
    select_card:     !!item.select_card,
    validate_amount: !!item.validate_amount,
    validate_number: !!item.validate_number,
    ask_customer:    !!item.ask_customer,
  }
  modal.value = true
}

// ── Guardar ────────────────────────────────────────────────────────────────────
async function save() {
  if (!form.value.name.trim()) {
    showToast("El nombre es obligatorio", "warning")
    return
  }
  saving.value = true
  try {
    const payload = { ...form.value, company_id: companyId.value }
    if (editing.value) {
      await api.put(`/api/payment-types/${editing.value.id}`, payload)
      // Actualizar local
      const idx = items.value.findIndex(i => i.id === editing.value.id)
      if (idx !== -1) {
        items.value[idx] = { ...items.value[idx], ...form.value }
        // Si se marcó como default, quitar default al resto
        if (form.value.is_default) {
          items.value.forEach((it, i) => { if (i !== idx) it.is_default = 0 })
        }
      }
      showToast("Forma de pago actualizada", "success")
    } else {
      const res = await api.post("/api/payment-types", payload)
      items.value.push({
        ...res.data,
        ...form.value,
        id: res.data.id,
        company_id: companyId.value,
      })
      if (form.value.is_default) {
        items.value.forEach(it => {
          if (it.id !== res.data.id) it.is_default = 0
        })
      }
      showToast("Forma de pago creada", "success")
    }
    modal.value = false
  } catch (e) {
    showToast(e?.response?.data?.detail ?? "Error al guardar", "error")
  }
  saving.value = false
}

// ── Toggle activo ──────────────────────────────────────────────────────────────
async function toggleActive(item) {
  togglingId.value = item.id
  try {
    const res = await api.patch(`/api/payment-types/${item.id}/toggle-active`, {
      company_id: companyId.value,
    })
    item.is_active = res.data.is_active
  } catch (e) {
    showToast(e?.response?.data?.detail ?? "Error al cambiar estado", "error")
  }
  togglingId.value = null
}

// ── Eliminar ───────────────────────────────────────────────────────────────────
async function remove(item) {
  if (!(await showConfirm(`¿Eliminar "${item.name}"? Esta acción no se puede deshacer.`))) return
  try {
    await api.delete(`/api/payment-types/${item.id}`, {
      params: { company_id: companyId.value },
    })
    items.value = items.value.filter(i => i.id !== item.id)
    showToast("Forma de pago eliminada", "success")
  } catch (e) {
    showToast(e?.response?.data?.detail ?? "Error al eliminar", "error")
  }
}

onMounted(load)
</script>

<style scoped>
/* ── Opciones del modal ─────────────────────────────────────────────── */
.options-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.opt-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  background: #f8fafc;
  cursor: pointer;
  transition: all .15s;
  user-select: none;
}
.opt-item:hover  { border-color: #93c5fd; background: #eff6ff; }
.opt-item.active { border-color: #3b82f6; background: #eff6ff; }

.opt-icon {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: #e0f2fe;
  color: #0369a1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}
.opt-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.opt-label { font-size: 13px; font-weight: 700; color: #1e293b; }
.opt-desc  { font-size: 11px; color: #64748b; }
.opt-toggle { font-size: 20px; flex-shrink: 0; }

/* ── Badges / chips ─────────────────────────────────────────────────── */
.badge-default {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #fef3c7;
  color: #92400e;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: 20px;
}
.badge-yes {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #dcfce7;
  color: #166534;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: 20px;
}
.badge-no {
  display: inline-flex;
  align-items: center;
  background: #f1f5f9;
  color: #94a3b8;
  font-size: 11px;
  padding: 3px 9px;
  border-radius: 20px;
}

.flag-chip {
  display: inline-flex;
  background: #e0f2fe;
  color: #0369a1;
  font-size: 10px;
  font-weight: 600;
  padding: 1px 7px;
  border-radius: 20px;
  margin-right: 4px;
}
.pt-name  { display: flex; align-items: center; }
.pt-flags { margin-top: 3px; }

/* ── Toggle button ─────────────────────────────────────────────────── */
.toggle-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 22px;
  padding: 2px 6px;
  border-radius: 6px;
  transition: transform .1s;
  line-height: 1;
}
.toggle-btn:hover:not(:disabled) { transform: scale(1.15); }
.toggle-btn:disabled { opacity: .5; cursor: not-allowed; }
.toggle-on  { color: #16a34a; }
.toggle-off { color: #cbd5e1; }

/* ── Modal grande ───────────────────────────────────────────────────── */
.modal-lg { max-width: 680px; }

.fg-label {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: .4px;
  display: block;
  margin-bottom: 5px;
}

/* ── Responsive 768px ───────────────────────────────────────────────── */
@media (max-width: 768px) {
  .options-grid { grid-template-columns: 1fr; }
  .data-table th:nth-child(3),
  .data-table td:nth-child(3) { display: none; }
}

/* ── Responsive 576px ───────────────────────────────────────────────── */
@media (max-width: 576px) {
  .data-table th:nth-child(4),
  .data-table td:nth-child(4),
  .data-table th:nth-child(5),
  .data-table td:nth-child(5) { display: none; }
  .opt-desc { display: none; }
}

.spin { display: inline-block; animation: spin .7s linear infinite; }
@keyframes spin { from { transform: rotate(0) } to { transform: rotate(360deg) } }
</style>
