<template>
  <div class="page-container">

    <div class="page-header">
      <div>
        <h1 class="page-title">
          <i class="bi bi-tags me-2"></i>{{ moduleName }}
        </h1>
        <p class="page-subtitle">Motivos de descuento aplicables a los ítems de un pedido (cortesías, promociones, empleados...)</p>
      </div>
      <button class="btn btn-primary" @click="openCreate">
        <i class="bi bi-plus-lg"></i> Nueva tipificación
      </button>
    </div>

    <div class="search-bar">
      <i class="bi bi-search"></i>
      <input v-model="search" :placeholder="`Buscar ${moduleName}...`" class="search-input" />
    </div>

    <div v-if="loading" class="empty-state">
      <i class="bi bi-arrow-repeat spin"></i>
      <p>Cargando...</p>
    </div>

    <div v-else-if="filtered.length === 0" class="empty-state">
      <i class="bi bi-tags"></i>
      <p>{{ search ? `Sin resultados para "${search}"` : 'No hay tipificaciones de descuento registradas' }}</p>
      <button v-if="!search" class="btn btn-primary btn-sm" @click="openCreate">
        Agregar la primera tipificación
      </button>
    </div>

    <div v-else class="sub-card p-0">
      <table class="data-table">
        <thead>
          <tr>
            <th>Nombre</th>
            <th class="text-center">Descuento</th>
            <th class="text-center">Solicita cliente</th>
            <th class="text-center">Activo</th>
            <th class="text-center">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filtered" :key="item.id">
            <td><strong>{{ item.name }}</strong></td>
            <td class="text-center">
              <span v-if="item.discount_percentage" class="flag-chip">{{ item.discount_percentage }}%</span>
              <span v-if="item.discount_pesos" class="flag-chip">{{ fmt(item.discount_pesos) }}</span>
              <span v-if="!item.discount_percentage && !item.discount_pesos" class="text-muted">—</span>
            </td>
            <td class="text-center">
              <span v-if="item.ask_customer_info" class="badge-yes"><i class="bi bi-person-badge"></i> Sí</span>
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

    <!-- Modal crear / editar -->
    <div v-if="modal" class="modal-overlay" @click.self="modal = false">
      <div class="modal-card">
        <div class="modal-header">
          <h3>{{ editing ? 'Editar tipificación' : 'Nueva tipificación' }}</h3>
          <button class="modal-close" @click="modal = false"><i class="bi bi-x-lg"></i></button>
        </div>

        <div class="modal-body">
          <div class="fg mb-3">
            <label class="fg-label">Nombre <span class="text-danger">*</span></label>
            <input
              v-model="form.name"
              class="form-control"
              placeholder="Ej: Cortesía, Descuento empleados, Promoción 2x1..."
              autofocus
            />
          </div>

          <div class="row g-2 mb-3">
            <div class="col-6">
              <label class="fg-label">Descuento en %</label>
              <input v-model.number="form.discount_percentage" type="number" min="0" max="100" class="form-control" placeholder="0" />
            </div>
            <div class="col-6">
              <label class="fg-label">Descuento en pesos</label>
              <input v-model.number="form.discount_pesos" type="number" min="0" class="form-control" placeholder="0" />
            </div>
          </div>

          <div class="options-grid">
            <div class="opt-item" :class="{ active: form.is_active }" @click="form.is_active = !form.is_active">
              <div class="opt-icon"><i class="bi bi-power"></i></div>
              <div class="opt-info">
                <span class="opt-label">Activo</span>
                <span class="opt-desc">Disponible para aplicar a un ítem</span>
              </div>
              <div class="opt-toggle">
                <i :class="form.is_active ? 'bi bi-toggle-on text-success' : 'bi bi-toggle-off text-muted'"></i>
              </div>
            </div>

            <div class="opt-item" :class="{ active: form.ask_customer_info }" @click="form.ask_customer_info = !form.ask_customer_info">
              <div class="opt-icon"><i class="bi bi-person-badge"></i></div>
              <div class="opt-info">
                <span class="opt-label">Solicitar cliente</span>
                <span class="opt-desc">Requiere identificar al cliente para aplicarlo</span>
              </div>
              <div class="opt-toggle">
                <i :class="form.ask_customer_info ? 'bi bi-toggle-on text-success' : 'bi bi-toggle-off text-muted'"></i>
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

const fmtCOP = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 })
const fmt = v => fmtCOP.format(v || 0)

const items      = ref([])
const search     = ref("")
const loading    = ref(false)
const modal      = ref(false)
const saving     = ref(false)
const editing    = ref(null)
const togglingId = ref(null)

const formDef = () => ({
  name: "",
  discount_percentage: 0,
  discount_pesos: 0,
  ask_customer_info: false,
  is_active: true,
})
const form = ref(formDef())

const filtered = computed(() => {
  const q = search.value.toLowerCase()
  return items.value.filter(i => i.name.toLowerCase().includes(q))
})

async function load() {
  if (!companyId.value) return
  loading.value = true
  try {
    const res = await api.get("/api/pos/tipificaciones-descuento", { params: { company_id: companyId.value } })
    items.value = res.data
  } catch {
    showToast("Error cargando tipificaciones de descuento", "error")
  }
  loading.value = false
}

function openCreate() {
  editing.value = null
  form.value    = formDef()
  modal.value   = true
}

function openEdit(item) {
  editing.value = item
  form.value = {
    name: item.name,
    discount_percentage: item.discount_percentage,
    discount_pesos: item.discount_pesos,
    ask_customer_info: !!item.ask_customer_info,
    is_active: !!item.is_active,
  }
  modal.value = true
}

async function save() {
  if (!form.value.name.trim()) {
    showToast("El nombre es obligatorio", "warning")
    return
  }
  saving.value = true
  try {
    const payload = { ...form.value, company_id: companyId.value }
    if (editing.value) {
      await api.put(`/api/pos/tipificaciones-descuento/${editing.value.id}`, payload)
      const idx = items.value.findIndex(i => i.id === editing.value.id)
      if (idx !== -1) items.value[idx] = { ...items.value[idx], ...form.value }
      showToast("Tipificación actualizada", "success")
    } else {
      const res = await api.post("/api/pos/tipificaciones-descuento", payload)
      items.value.push({ ...res.data, ...form.value, id: res.data.id, company_id: companyId.value })
      showToast("Tipificación creada", "success")
    }
    modal.value = false
  } catch (e) {
    showToast(e?.response?.data?.detail ?? "Error al guardar", "error")
  }
  saving.value = false
}

async function toggleActive(item) {
  togglingId.value = item.id
  try {
    const res = await api.patch(`/api/pos/tipificaciones-descuento/${item.id}/toggle-active`, {
      company_id: companyId.value,
    })
    item.is_active = res.data.is_active
  } catch (e) {
    showToast(e?.response?.data?.detail ?? "Error al cambiar estado", "error")
  }
  togglingId.value = null
}

async function remove(item) {
  if (!(await showConfirm(`¿Eliminar "${item.name}"? Esta acción no se puede deshacer.`))) return
  try {
    await api.delete(`/api/pos/tipificaciones-descuento/${item.id}`, {
      params: { company_id: companyId.value },
    })
    items.value = items.value.filter(i => i.id !== item.id)
    showToast("Tipificación eliminada", "success")
  } catch (e) {
    showToast(e?.response?.data?.detail ?? "Error al eliminar", "error")
  }
}

onMounted(load)
</script>

<style scoped>
/* ── Modal (no hay estilos globales para estas clases) ──────────────── */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 2000; padding: 16px; }
.modal-card    { background: #fff; border-radius: 16px; width: 100%; max-width: 560px; max-height: 92vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,.25); overflow: hidden; }
.modal-card .modal-header { display: flex; align-items: center; justify-content: space-between; padding: 14px 20px; border-bottom: 1px solid #f1f5f9; }
.modal-card .modal-header h3 { font-size: 16px; font-weight: 700; color: #1e293b; margin: 0; }
.modal-close   { background: none; border: none; font-size: 16px; color: #94a3b8; cursor: pointer; }
.modal-card .modal-body   { padding: 16px 20px; overflow-y: auto; }
.modal-card .modal-footer { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 20px 16px; border-top: 1px solid #f1f5f9; }
@media (max-width: 768px) {
  .modal-overlay { padding: 0; align-items: flex-end; }
  .modal-card { max-width: 100%; border-radius: 16px 16px 0 0; max-height: 94vh; }
}
@media (max-width: 576px) {
  .modal-card .modal-body { padding: 12px 14px; }
}

.options-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.opt-item {
  display: flex; align-items: center; gap: 10px; padding: 12px 14px;
  border: 1.5px solid #e2e8f0; border-radius: 10px; background: #f8fafc;
  cursor: pointer; transition: all .15s; user-select: none;
}
.opt-item:hover  { border-color: #93c5fd; background: #eff6ff; }
.opt-item.active { border-color: #3b82f6; background: #eff6ff; }
.opt-icon {
  width: 34px; height: 34px; border-radius: 8px; background: #e0f2fe; color: #0369a1;
  display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0;
}
.opt-info { flex: 1; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.opt-label { font-size: 13px; font-weight: 700; color: #1e293b; }
.opt-desc  { font-size: 11px; color: #64748b; }
.opt-toggle { font-size: 20px; flex-shrink: 0; }

.badge-yes {
  display: inline-flex; align-items: center; gap: 4px;
  background: #dcfce7; color: #166534; font-size: 11px; font-weight: 700;
  padding: 3px 9px; border-radius: 20px;
}
.badge-no {
  display: inline-flex; align-items: center; background: #f1f5f9; color: #94a3b8;
  font-size: 11px; padding: 3px 9px; border-radius: 20px;
}
.flag-chip {
  display: inline-flex; background: #e0f2fe; color: #0369a1; font-size: 10px; font-weight: 600;
  padding: 1px 7px; border-radius: 20px; margin: 0 2px;
}

.toggle-btn { background: none; border: none; cursor: pointer; font-size: 22px; padding: 2px 6px; border-radius: 6px; transition: transform .1s; line-height: 1; }
.toggle-btn:hover:not(:disabled) { transform: scale(1.15); }
.toggle-btn:disabled { opacity: .5; cursor: not-allowed; }
.toggle-on  { color: #16a34a; }
.toggle-off { color: #cbd5e1; }

.fg-label {
  font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase;
  letter-spacing: .4px; display: block; margin-bottom: 5px;
}

.spin { display: inline-block; animation: spin .7s linear infinite; }
@keyframes spin { from { transform: rotate(0) } to { transform: rotate(360deg) } }

@media (max-width: 768px) {
  .options-grid { grid-template-columns: 1fr; }
  .data-table th:nth-child(3), .data-table td:nth-child(3) { display: none; }
}

@media (max-width: 576px) {
  .data-table th:nth-child(2), .data-table td:nth-child(2) { display: none; }
}
</style>
