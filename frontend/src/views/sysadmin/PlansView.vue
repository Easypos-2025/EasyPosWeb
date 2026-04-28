<template>
  <div class="page-container">

    <!-- ENCABEZADO -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Planes de suscripción</h1>
        <p class="page-subtitle">Define los límites de cada plan. -1 significa ilimitado.</p>
      </div>
      <button class="btn-primary" @click="openCreate">
        <i class="bi bi-plus-lg"></i> Nuevo plan
      </button>
    </div>

    <!-- TABLA -->
    <div class="table-card">
      <div v-if="loading" class="table-loading">
        <i class="bi bi-arrow-repeat spin"></i> Cargando...
      </div>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Nombre</th>
            <th>Descripción</th>
            <th class="text-center">Usuarios</th>
            <th class="text-center">Productos</th>
            <th class="text-center">Categorías</th>
            <th class="text-right">Precio / mes</th>
            <th class="text-center">Activo</th>
            <th class="text-center">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="plan in plans" :key="plan.id">
            <td class="text-muted">{{ plan.id }}</td>
            <td><strong>{{ plan.name }}</strong></td>
            <td class="text-muted">{{ plan.description || '—' }}</td>
            <td class="text-center">{{ plan.max_users === -1 ? '∞' : plan.max_users }}</td>
            <td class="text-center">{{ plan.max_products === -1 ? '∞' : plan.max_products }}</td>
            <td class="text-center">{{ plan.max_categories === -1 ? '∞' : plan.max_categories }}</td>
            <td class="text-right">{{ plan.price > 0 ? '$' + plan.price.toLocaleString('es-CO') : 'Gratis' }}</td>
            <td class="text-center">
              <span class="badge" :class="plan.is_active ? 'badge-green' : 'badge-gray'">
                {{ plan.is_active ? 'Activo' : 'Inactivo' }}
              </span>
            </td>
            <td class="text-center">
              <div class="d-flex gap-1 justify-content-center">
                <button class="btn btn-warning btn-sm" @click="openEdit(plan)" title="Editar">
                  <i class="bi bi-pencil"></i> Editar
                </button>
                <button class="btn btn-info btn-sm" @click="openPrices(plan)" title="Precios por moneda">
                  <i class="bi bi-currency-exchange"></i>
                </button>
                <button class="btn btn-danger btn-sm" @click="confirmDelete(plan)" title="Eliminar">
                  <i class="bi bi-trash"></i>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="plans.length === 0">
            <td colspan="9" class="text-center text-muted" style="padding:32px">
              No hay planes registrados.
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- MODAL CREAR / EDITAR -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-box">
        <div class="modal-header">
          <h2>{{ editMode ? 'Editar plan' : 'Nuevo plan' }}</h2>
          <button class="btn-icon-sm" @click="closeModal"><i class="bi bi-x-lg"></i></button>
        </div>

        <div class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label>Nombre *</label>
              <input v-model="form.name" class="form-input" placeholder="Ej: Premium" />
            </div>
            <div class="form-group">
              <label>Precio mensual ($)</label>
              <input v-model.number="form.price" type="number" min="0" class="form-input" />
            </div>
          </div>

          <div class="form-group">
            <label>Descripción</label>
            <textarea v-model="form.description" class="form-input" rows="2" />
          </div>

          <div class="form-row three">
            <div class="form-group">
              <label>Máx. usuarios <small>(-1 = ∞)</small></label>
              <input v-model.number="form.max_users" type="number" min="-1" class="form-input" />
            </div>
            <div class="form-group">
              <label>Máx. productos <small>(-1 = ∞)</small></label>
              <input v-model.number="form.max_products" type="number" min="-1" class="form-input" />
            </div>
            <div class="form-group">
              <label>Máx. categorías <small>(-1 = ∞)</small></label>
              <input v-model.number="form.max_categories" type="number" min="-1" class="form-input" />
            </div>
          </div>

          <div class="form-group checkbox-group">
            <label>
              <input type="checkbox" v-model="form.is_active" />
              Plan activo (visible para asignar a empresas)
            </label>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn-secondary" @click="closeModal">Cancelar</button>
          <button class="btn-primary" @click="save" :disabled="saving">
            <i v-if="saving" class="bi bi-arrow-repeat spin"></i>
            {{ saving ? 'Guardando...' : 'Guardar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL PRECIOS POR MONEDA -->
    <div v-if="showPricesModal" class="modal-overlay" @click.self="showPricesModal = false">
      <div class="modal-box prices-modal">
        <div class="modal-header">
          <h2><i class="bi bi-currency-exchange me-2"></i>Precios de "{{ pricesPlan?.name }}" por moneda</h2>
          <button class="btn-icon-sm" @click="showPricesModal = false"><i class="bi bi-x-lg"></i></button>
        </div>

        <p class="prices-note">
          El precio base (COP) es el valor de la columna "Precio" del plan.
          Aquí puedes agregar o editar precios en otras monedas para usuarios de otros países.
        </p>

        <div class="prices-table-wrap">
          <table class="data-table" v-if="planPrices.length">
            <thead>
              <tr>
                <th>Moneda</th><th class="text-right">Valor</th><th class="text-center">Activo</th><th class="text-center">Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="pp in planPrices" :key="pp.id">
                <td><strong>{{ pp.currency_code }}</strong></td>
                <td class="text-right">{{ pp.amount.toLocaleString('es-CO') }}</td>
                <td class="text-center">
                  <span class="badge" :class="pp.is_active ? 'badge-green' : 'badge-gray'">
                    {{ pp.is_active ? 'Activo' : 'Inactivo' }}
                  </span>
                </td>
                <td class="text-center">
                  <button class="btn-action btn-delete" @click="deletePrice(pp.currency_code)">
                    <i class="bi bi-trash"></i>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          <p v-else class="text-muted text-center" style="padding:16px">
            No hay precios en otras monedas. El sistema usa COP por defecto.
          </p>
        </div>

        <!-- Agregar nuevo precio -->
        <div class="add-price-form">
          <h4>Agregar / actualizar precio</h4>
          <div class="form-row">
            <div class="form-group">
              <label>Moneda</label>
              <select v-model="newPriceCurrency" class="form-input">
                <option value="">-- Seleccionar --</option>
                <option v-for="c in availableCurrencies" :key="c" :value="c">{{ c }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>Valor</label>
              <input v-model.number="newPriceAmount" type="number" min="0" class="form-input" placeholder="Ej: 50000" />
            </div>
          </div>
          <button class="btn-primary" :disabled="!newPriceCurrency || !newPriceAmount || savingPrice" @click="savePrice">
            <i v-if="savingPrice" class="bi bi-arrow-repeat spin"></i>
            {{ savingPrice ? 'Guardando...' : 'Guardar precio' }}
          </button>
        </div>

        <div class="modal-footer">
          <button class="btn-secondary" @click="showPricesModal = false">Cerrar</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

import { SUPPORTED_CURRENCIES } from "@/utils/currency"

const plans   = ref([])
const loading = ref(true)
const saving  = ref(false)
const showModal = ref(false)
const editMode  = ref(false)

const emptyForm = () => ({
  id: null, name: "", description: "",
  max_users: 1, max_products: -1, max_categories: -1,
  price: 0, is_active: true
})

const form = ref(emptyForm())

// Precios por moneda
const showPricesModal  = ref(false)
const pricesPlan       = ref(null)
const planPrices       = ref([])
const newPriceCurrency = ref("")
const newPriceAmount   = ref(0)
const savingPrice      = ref(false)
const availableCurrencies = SUPPORTED_CURRENCIES

async function load() {
  loading.value = true
  try {
    const res = await api.get("/plans/")
    plans.value = res.data
  } catch {
    showToast("Error cargando planes", "error")
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.value = emptyForm()
  editMode.value = false
  showModal.value = true
}

function openEdit(plan) {
  form.value = { ...plan }
  editMode.value = true
  showModal.value = true
}

function closeModal() {
  showModal.value = false
}

async function save() {
  if (!form.value.name.trim()) {
    showToast("El nombre del plan es obligatorio", "warning")
    return
  }
  saving.value = true
  try {
    if (editMode.value) {
      await api.put(`/plans/${form.value.id}`, form.value)
      showToast("Plan actualizado", "success")
    } else {
      await api.post("/plans/", form.value)
      showToast("Plan creado", "success")
    }
    closeModal()
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error guardando plan", "error")
  } finally {
    saving.value = false
  }
}

async function confirmDelete(plan) {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar "${plan.name}"?`,
    text: "Esta acción no se puede deshacer.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, eliminar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/plans/${plan.id}`)
    showToast("Plan eliminado", "success")
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error eliminando plan", "error")
  }
}

async function openPrices(plan) {
  pricesPlan.value      = plan
  newPriceCurrency.value = ""
  newPriceAmount.value   = 0
  showPricesModal.value  = true
  try {
    const res = await api.get(`/plans/${plan.id}/prices`)
    planPrices.value = res.data
  } catch { planPrices.value = [] }
}

async function savePrice() {
  if (!newPriceCurrency.value || !newPriceAmount.value) return
  savingPrice.value = true
  try {
    await api.put(`/plans/${pricesPlan.value.id}/prices/${newPriceCurrency.value}`, {
      amount: newPriceAmount.value, is_active: true,
    })
    showToast(`Precio en ${newPriceCurrency.value} guardado`, "success")
    const res = await api.get(`/plans/${pricesPlan.value.id}/prices`)
    planPrices.value = res.data
    newPriceCurrency.value = ""
    newPriceAmount.value   = 0
  } catch (e) {
    showToast(e.response?.data?.detail || "Error guardando precio", "error")
  } finally { savingPrice.value = false }
}

async function deletePrice(currency) {
  try {
    await api.delete(`/plans/${pricesPlan.value.id}/prices/${currency}`)
    showToast(`Precio en ${currency} eliminado`, "success")
    planPrices.value = planPrices.value.filter(p => p.currency_code !== currency)
  } catch (e) {
    showToast(e.response?.data?.detail || "Error eliminando precio", "error")
  }
}

onMounted(load)
</script>

<style scoped>
.page-container  { padding: 24px; max-width: 1100px; }
.page-header     { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 24px; gap: 16px; flex-wrap: wrap; }
.page-title      { font-size: 20px; font-weight: 700; color: #1e293b; margin-bottom: 4px; }
.page-subtitle   { font-size: 13px; color: #64748b; }

/* TABLE */
.table-card { background: #fff; border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,0.08); overflow: hidden; }
.table-loading { padding: 40px; text-align: center; color: #94a3b8; font-size: 15px; }
.data-table  { width: 100%; border-collapse: collapse; font-size: 14px; }
.data-table th { background: #f8fafc; color: #475569; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; padding: 12px 16px; border-bottom: 1px solid #e2e8f0; }
.data-table td { padding: 13px 16px; border-bottom: 1px solid #f1f5f9; color: #1e293b; vertical-align: middle; }
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: #f8fafc; }

.text-center { text-align: center; }
.text-right  { text-align: right; }
.text-muted  { color: #94a3b8 !important; }

.badge       { font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 20px; }
.badge-green { background: #dcfce7; color: #16a34a; }
.badge-gray  { background: #f1f5f9; color: #94a3b8; }

.action-btns { display: flex; gap: 6px; justify-content: center; }
.btn-action  { background: none; border: 1px solid #e2e8f0; border-radius: 6px; padding: 5px 9px; cursor: pointer; font-size: 14px; transition: all 0.15s; }
.btn-edit:hover   { background: #eff6ff; border-color: #3b82f6; color: #3b82f6; }
.btn-delete:hover { background: #fef2f2; border-color: #ef4444; color: #ef4444; }

/* Modal precios */
.prices-modal { max-width: 560px; }
.prices-note  { font-size: .82rem; color: #64748b; margin-bottom: 14px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 14px; }
.prices-table-wrap { margin-bottom: 16px; border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden; }
.add-price-form { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px; margin-bottom: 14px; }
.add-price-form h4 { font-size: .88rem; font-weight: 700; color: #334155; margin-bottom: 12px; }
.btn-info { background: none; border: 1px solid #0ea5e9; color: #0ea5e9; border-radius: 6px; padding: 4px 8px; cursor: pointer; font-size: 13px; }
.btn-info:hover { background: #e0f2fe; }

/* MODAL */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.45); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-box     { background: #fff; border-radius: 16px; width: 580px; max-width: 95vw; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
.modal-header  { display: flex; align-items: center; justify-content: space-between; padding: 20px 24px 16px; border-bottom: 1px solid #f1f5f9; }
.modal-header h2 { font-size: 17px; font-weight: 700; color: #1e293b; }
.modal-body    { padding: 20px 24px; display: flex; flex-direction: column; gap: 14px; }
.modal-footer  { padding: 16px 24px 20px; display: flex; justify-content: flex-end; gap: 10px; border-top: 1px solid #f1f5f9; }

.form-row       { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.form-row.three { grid-template-columns: 1fr 1fr 1fr; }
.form-group     { display: flex; flex-direction: column; gap: 5px; }
.form-group label { font-size: 13px; font-weight: 500; color: #374151; }
.form-group label small { font-weight: 400; color: #94a3b8; }
.form-input   { padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 14px; outline: none; color: #1e293b !important; background: #fff !important; }
.form-input:focus { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.1); }
.checkbox-group label { display: flex; align-items: center; gap: 8px; font-size: 14px; cursor: pointer; }
.checkbox-group input[type=checkbox] { width: 16px; height: 16px; }

/* BUTTONS */
.btn-primary   { background: #3b82f6; color: #fff; border: none; border-radius: 8px; padding: 9px 18px; font-size: 14px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; transition: background 0.2s; }
.btn-primary:hover:not(:disabled) { background: #2563eb; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-secondary { background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; border-radius: 8px; padding: 9px 18px; font-size: 14px; font-weight: 500; cursor: pointer; }
.btn-secondary:hover { background: #e2e8f0; }
.btn-icon-sm   { background: none; border: none; cursor: pointer; font-size: 18px; color: #94a3b8; padding: 4px; border-radius: 6px; }
.btn-icon-sm:hover { background: #f1f5f9; color: #1e293b; }

.spin { display: inline-block; animation: spin 0.8s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
