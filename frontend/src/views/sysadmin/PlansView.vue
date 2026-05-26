<template>
  <div class="page-container">

    <!-- ENCABEZADO -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Planes de suscripción</h1>
        <p class="page-subtitle">Define los límites de cada plan. -1 = ilimitado · 0 = no incluido</p>
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

      <div v-else class="table-scroll-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Nombre</th>
              <th class="text-right">Precio/mes</th>
              <th class="text-center" title="Usuarios">Usrs</th>
              <th class="text-center" title="Roles">Roles</th>
              <th class="text-center" title="Productos">Prods</th>
              <th class="text-center" title="Categorías">Cats</th>
              <th class="text-center" title="Trabajadores">Work.</th>
              <th class="text-center" title="Meseros/Cajeros POS">Wait.</th>
              <th class="text-center" title="Clientes">Clts</th>
              <th class="text-center" title="Artículos bodega">Bodg</th>
              <th class="text-center" title="Activos">Actvs</th>
              <th class="text-center" title="Tareas activas">Tarea</th>
              <th class="text-center" title="Facturas diarias">F/día</th>
              <th class="text-center" title="Recibos diarios">R/día</th>
              <th class="text-center" title="Tareas diarias">T/día</th>
              <th class="text-center">Estado</th>
              <th class="text-center">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="plan in plans" :key="plan.id">
              <td class="text-muted">{{ plan.id }}</td>
              <td><strong>{{ plan.name }}</strong></td>
              <td class="text-right">{{ plan.price > 0 ? '$' + plan.price.toLocaleString('es-CO') : 'Gratis' }}</td>
              <td class="text-center lim-cell">{{ lv(plan.max_users) }}</td>
              <td class="text-center lim-cell">{{ lv(plan.max_roles) }}</td>
              <td class="text-center lim-cell">{{ lv(plan.max_products) }}</td>
              <td class="text-center lim-cell">{{ lv(plan.max_categories) }}</td>
              <td class="text-center lim-cell">{{ lv(plan.max_workers) }}</td>
              <td class="text-center lim-cell">{{ lv(plan.max_waiters) }}</td>
              <td class="text-center lim-cell">{{ lv(plan.max_clients) }}</td>
              <td class="text-center lim-cell">{{ lv(plan.max_bodega_items) }}</td>
              <td class="text-center lim-cell">{{ lv(plan.max_assets) }}</td>
              <td class="text-center lim-cell">{{ lv(plan.max_tasks) }}</td>
              <td class="text-center lim-cell">{{ lv(plan.max_daily_invoices) }}</td>
              <td class="text-center lim-cell">{{ lv(plan.max_daily_receipts) }}</td>
              <td class="text-center lim-cell">{{ lv(plan.max_daily_tasks) }}</td>
              <td class="text-center">
                <span class="badge" :class="plan.is_active ? 'badge-green' : 'badge-gray'">
                  {{ plan.is_active ? 'Activo' : 'Inactivo' }}
                </span>
              </td>
              <td class="text-center">
                <div class="d-flex gap-1 justify-content-center">
                  <button class="btn btn-warning btn-sm" @click="openEdit(plan)" title="Editar">
                    <i class="bi bi-pencil"></i>
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
              <td colspan="18" class="text-center text-muted" style="padding:32px">
                No hay planes registrados.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- MODAL CREAR / EDITAR -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-box modal-wide">
        <div class="modal-header">
          <h2>{{ editMode ? 'Editar plan' : 'Nuevo plan' }}</h2>
          <button class="btn-icon-sm" @click="closeModal"><i class="bi bi-x-lg"></i></button>
        </div>

        <div class="modal-body">
          <!-- Fila 1: nombre + precio -->
          <div class="form-row two">
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

          <!-- Sección: Acceso y roles -->
          <div class="limits-section">
            <div class="limits-section-title">
              <i class="bi bi-people"></i> Acceso y roles
            </div>
            <div class="form-row three">
              <div class="form-group">
                <label>Máx. usuarios <small>(-1=∞)</small></label>
                <input v-model.number="form.max_users" type="number" min="-1" class="form-input" />
              </div>
              <div class="form-group">
                <label>Máx. roles <small class="auto-tag">= usuarios</small></label>
                <input :value="form.max_roles" class="form-input input-auto" readonly
                       title="Se sincroniza automáticamente con Máx. usuarios" />
              </div>
              <div class="form-group">
                <label>Máx. trabajadores <small>(-1=∞)</small></label>
                <input v-model.number="form.max_workers" type="number" min="-1" class="form-input" />
              </div>
            </div>
            <div class="form-row two">
              <div class="form-group">
                <label>Máx. meseros/cajeros POS <small>(-1=∞)</small></label>
                <input v-model.number="form.max_waiters" type="number" min="-1" class="form-input" />
              </div>
              <div class="form-group">
                <label>Máx. clientes <small>(-1=∞)</small></label>
                <input v-model.number="form.max_clients" type="number" min="-1" class="form-input" />
              </div>
            </div>
          </div>

          <!-- Sección: Catálogo e inventario -->
          <div class="limits-section">
            <div class="limits-section-title">
              <i class="bi bi-grid"></i> Catálogo e inventario
            </div>
            <div class="form-row three">
              <div class="form-group">
                <label>Máx. productos <small>(-1=∞)</small></label>
                <input v-model.number="form.max_products" type="number" min="-1" class="form-input" />
              </div>
              <div class="form-group">
                <label>Máx. categorías <small>(-1=∞)</small></label>
                <input v-model.number="form.max_categories" type="number" min="-1" class="form-input" />
              </div>
              <div class="form-group">
                <label>Máx. art. bodega <small>(-1=∞)</small></label>
                <input v-model.number="form.max_bodega_items" type="number" min="-1" class="form-input" />
              </div>
            </div>
            <div class="form-row two">
              <div class="form-group">
                <label>Máx. activos <small>(-1=∞)</small></label>
                <input v-model.number="form.max_assets" type="number" min="-1" class="form-input" />
              </div>
              <div class="form-group">
                <label>Máx. tareas activas <small>(-1=∞)</small></label>
                <input v-model.number="form.max_tasks" type="number" min="-1" class="form-input" />
              </div>
            </div>
          </div>

          <!-- Sección: Límites diarios -->
          <div class="limits-section">
            <div class="limits-section-title">
              <i class="bi bi-calendar-day"></i> Límites diarios
            </div>
            <div class="form-row three">
              <div class="form-group">
                <label>Facturas/día <small>(-1=∞)</small></label>
                <input v-model.number="form.max_daily_invoices" type="number" min="-1" class="form-input" />
              </div>
              <div class="form-group">
                <label>Recibos/día <small>(-1=∞)</small></label>
                <input v-model.number="form.max_daily_receipts" type="number" min="-1" class="form-input" />
              </div>
              <div class="form-group">
                <label>Tareas/día <small>(-1=∞)</small></label>
                <input v-model.number="form.max_daily_tasks" type="number" min="-1" class="form-input" />
              </div>
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

        <div class="add-price-form">
          <h4>Agregar / actualizar precio</h4>
          <div class="form-row two">
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
import { ref, onMounted, watch } from "vue"
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
  max_workers: -1, max_clients: -1, max_bodega_items: -1,
  max_tasks: -1, max_daily_invoices: -1, max_assets: -1,
  max_waiters: -1, max_daily_receipts: -1, max_daily_tasks: -1,
  max_roles: 1,
  price: 0, is_active: true,
})

const form = ref(emptyForm())

watch(() => form.value.max_users, (val) => {
  form.value.max_roles = val
})

function lv(v) {
  if (v === -1 || v === undefined || v === null) return "∞"
  if (v === 0) return "—"
  return v
}

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
  pricesPlan.value       = plan
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
.page-container { padding: 24px; max-width: 100%; }
.page-header    { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 24px; gap: 16px; flex-wrap: wrap; }
.page-title     { font-size: 20px; font-weight: 700; color: #1e293b; margin-bottom: 4px; }
.page-subtitle  { font-size: 13px; color: #64748b; }

/* TABLE */
.table-card        { background: #fff; border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,0.08); overflow: hidden; }
.table-scroll-wrap { overflow-x: auto; }
.table-loading     { padding: 40px; text-align: center; color: #94a3b8; font-size: 15px; }
.data-table  { width: 100%; border-collapse: collapse; font-size: 13px; min-width: 1000px; }
.data-table th { background: #f8fafc; color: #475569; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.4px; padding: 11px 10px; border-bottom: 1px solid #e2e8f0; white-space: nowrap; }
.data-table td { padding: 11px 10px; border-bottom: 1px solid #f1f5f9; color: #1e293b; vertical-align: middle; }
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: #f8fafc; }

.lim-cell { font-size: 12px; font-weight: 600; color: #475569; }

.text-center { text-align: center; }
.text-right  { text-align: right; }
.text-muted  { color: #94a3b8 !important; }

.badge       { font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 20px; }
.badge-green { background: #dcfce7; color: #16a34a; }
.badge-gray  { background: #f1f5f9; color: #94a3b8; }

.btn-action  { background: none; border: 1px solid #e2e8f0; border-radius: 6px; padding: 5px 9px; cursor: pointer; font-size: 14px; transition: all 0.15s; }
.btn-edit:hover   { background: #eff6ff; border-color: #3b82f6; color: #3b82f6; }
.btn-delete:hover { background: #fef2f2; border-color: #ef4444; color: #ef4444; }

.d-flex             { display: flex; }
.gap-1              { gap: 4px; }
.justify-content-center { justify-content: center; }

/* MODAL */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.45); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 16px; }
.modal-box     { background: #fff; border-radius: 16px; width: 680px; max-width: 98vw; max-height: 90vh; overflow-y: auto; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
.modal-wide    { width: 780px; }
.modal-header  { display: flex; align-items: center; justify-content: space-between; padding: 20px 24px 16px; border-bottom: 1px solid #f1f5f9; position: sticky; top: 0; background: #fff; z-index: 1; }
.modal-header h2 { font-size: 17px; font-weight: 700; color: #1e293b; }
.modal-body    { padding: 20px 24px; display: flex; flex-direction: column; gap: 14px; }
.modal-footer  { padding: 16px 24px 20px; display: flex; justify-content: flex-end; gap: 10px; border-top: 1px solid #f1f5f9; position: sticky; bottom: 0; background: #fff; }

/* Sections */
.limits-section       { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px 16px; display: flex; flex-direction: column; gap: 12px; }
.limits-section-title { font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; display: flex; align-items: center; gap: 6px; }

/* Auto tag */
.auto-tag { color: #3b82f6; font-weight: 600; }
.input-auto { background: #eff6ff !important; color: #1d4ed8 !important; font-weight: 700; cursor: default; }

/* FORM */
.form-row      { display: grid; gap: 12px; }
.form-row.two  { grid-template-columns: 1fr 1fr; }
.form-row.three { grid-template-columns: 1fr 1fr 1fr; }
.form-group     { display: flex; flex-direction: column; gap: 5px; }
.form-group label { font-size: 13px; font-weight: 500; color: #374151; }
.form-group label small { font-weight: 400; color: #94a3b8; }
.form-input   { padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 14px; outline: none; color: #1e293b !important; background: #fff !important; width: 100%; box-sizing: border-box; }
.form-input:focus { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.1); }
.checkbox-group label { display: flex; align-items: center; gap: 8px; font-size: 14px; cursor: pointer; }
.checkbox-group input[type=checkbox] { width: 16px; height: 16px; }

/* Modal precios */
.prices-modal { max-width: 560px; }
.prices-note  { font-size: .82rem; color: #64748b; margin: 0 24px 14px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 14px; }
.prices-table-wrap { margin: 0 24px 16px; border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden; }
.add-price-form { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px; margin: 0 24px 14px; }
.add-price-form h4 { font-size: .88rem; font-weight: 700; color: #334155; margin-bottom: 12px; }

/* BUTTONS */
.btn-primary   { background: #3b82f6; color: #fff; border: none; border-radius: 8px; padding: 9px 18px; font-size: 14px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; transition: background 0.2s; }
.btn-primary:hover:not(:disabled) { background: #2563eb; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-secondary { background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; border-radius: 8px; padding: 9px 18px; font-size: 14px; font-weight: 500; cursor: pointer; }
.btn-secondary:hover { background: #e2e8f0; }
.btn-icon-sm   { background: none; border: none; cursor: pointer; font-size: 18px; color: #94a3b8; padding: 4px; border-radius: 6px; }
.btn-icon-sm:hover { background: #f1f5f9; color: #1e293b; }

.btn { border-radius: 6px; padding: 5px 9px; cursor: pointer; font-size: 13px; border: 1px solid transparent; }
.btn-warning { background: #fef9c3; color: #b45309; border-color: #fbbf24; }
.btn-warning:hover { background: #fde68a; }
.btn-info    { background: #e0f2fe; color: #0369a1; border-color: #38bdf8; }
.btn-info:hover { background: #bae6fd; }
.btn-danger  { background: #fee2e2; color: #b91c1c; border-color: #fca5a5; }
.btn-danger:hover { background: #fecaca; }
.btn-sm { padding: 4px 8px; font-size: 12px; }

.spin { display: inline-block; animation: spin 0.8s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* RESPONSIVE */
@media (max-width: 768px) {
  .page-container { padding: 14px; }
  .modal-wide { width: 98vw; }
  .form-row.three { grid-template-columns: 1fr 1fr; }
  .form-row.two   { grid-template-columns: 1fr; }
}

@media (max-width: 576px) {
  .page-container { padding: 10px; }
  .form-row.three { grid-template-columns: 1fr; }
  .modal-box { border-radius: 12px; }
  .modal-body { padding: 14px 16px; }
}
</style>
