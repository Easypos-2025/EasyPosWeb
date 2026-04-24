<template>
  <div class="page-container">

    <!-- ENCABEZADO -->
    <div class="page-header">
      <div class="header-left">
        <button class="btn-back" @click="$router.back()">
          <i class="bi bi-arrow-left"></i>
        </button>
        <div>
          <h1 class="page-title">
            <i class="bi bi-tools"></i> Materiales y Gastos
          </h1>
          <p class="page-subtitle" v-if="task">{{ task.title }}</p>
        </div>
      </div>
    </div>

    <!-- RESUMEN DE COSTOS -->
    <div class="cost-summary" v-if="task">
      <div class="cost-card cost-budget">
        <i class="bi bi-cash-stack"></i>
        <div>
          <span class="cost-label">Presupuesto</span>
          <span class="cost-value">${{ fmt(task.budget_labor_cost) }}</span>
        </div>
      </div>
      <div class="cost-card cost-materials">
        <i class="bi bi-boxes"></i>
        <div>
          <span class="cost-label">Total materiales</span>
          <span class="cost-value">${{ fmt(totalMaterials) }}</span>
        </div>
      </div>
      <div class="cost-card cost-expenses">
        <i class="bi bi-receipt"></i>
        <div>
          <span class="cost-label">Total gastos</span>
          <span class="cost-value">${{ fmt(totalExpenses) }}</span>
        </div>
      </div>
      <div class="cost-card" :class="costStatus">
        <i class="bi" :class="costStatus === 'cost-ok' ? 'bi-check-circle' : 'bi-exclamation-triangle'"></i>
        <div>
          <span class="cost-label">Costo real total</span>
          <span class="cost-value">${{ fmt(totalMaterials + totalExpenses) }}</span>
          <span class="cost-diff" v-if="task.budget_labor_cost > 0">
            {{ diffLabel }}
          </span>
        </div>
      </div>
    </div>

    <!-- TABS -->
    <div class="main-tabs">
      <button class="main-tab" :class="{ active: tab === 'materials' }" @click="tab = 'materials'">
        <i class="bi bi-boxes"></i> Materiales
        <span class="tab-badge">{{ materials.length }}</span>
      </button>
      <button class="main-tab" :class="{ active: tab === 'expenses' }" @click="tab = 'expenses'">
        <i class="bi bi-receipt"></i> Gastos pagados
        <span class="tab-badge">{{ expenses.length }}</span>
      </button>
    </div>

    <!-- ══════════════ MATERIALES ══════════════ -->
    <div v-if="tab === 'materials'">

      <!-- Formulario material -->
      <div class="form-card">
        <h3 class="form-title">Registrar material / herramienta</h3>
        <div class="form-row3">
          <div class="fg col2">
            <label>Nombre *</label>
            <input v-model="matForm.name" class="form-control" data-v="matname"
              placeholder="Ej: Cemento, Taladro, Cable..." @input="clearErr" />
          </div>
          <div class="fg">
            <label>Unidad</label>
            <select v-model="matForm.unit" class="form-select">
              <option value="">—</option>
              <option v-for="u in units" :key="u" :value="u">{{ u }}</option>
            </select>
          </div>
          <div class="fg">
            <label>Cantidad</label>
            <input v-model.number="matForm.quantity" type="number" min="0.01" step="0.01"
              class="form-control" placeholder="1" />
          </div>
          <div class="fg">
            <label>Costo unitario ($)</label>
            <input v-model.number="matForm.unit_cost" type="number" min="0"
              class="form-control" placeholder="0" />
          </div>
          <div class="fg total-col">
            <label>Total</label>
            <div class="total-display">
              ${{ fmt(matForm.quantity * matForm.unit_cost) }}
            </div>
          </div>
        </div>
        <button class="btn btn-primary btn-sm mt-2" @click="addMaterial" :disabled="savingMat">
          <i v-if="savingMat" class="bi bi-arrow-repeat spin"></i>
          <i v-else class="bi bi-plus-lg"></i>
          {{ savingMat ? 'Guardando...' : 'Agregar material' }}
        </button>
      </div>

      <!-- Lista materiales -->
      <div class="list-card">
        <div v-if="materials.length === 0" class="empty-list">
          <i class="bi bi-box-seam"></i>
          <p>No hay materiales registrados aún</p>
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>Material / Herramienta</th>
              <th class="text-center">Unidad</th>
              <th class="text-center">Cantidad</th>
              <th class="text-right">Costo unit.</th>
              <th class="text-right">Total</th>
              <th class="text-center">Acción</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in materials" :key="m.id">
              <td><strong>{{ m.name }}</strong></td>
              <td class="text-center text-muted">{{ m.unit || '—' }}</td>
              <td class="text-center">{{ m.quantity }}</td>
              <td class="text-right text-muted">${{ fmt(m.unit_cost) }}</td>
              <td class="text-right"><strong>${{ fmt(m.total_cost) }}</strong></td>
              <td class="text-center">
                <button class="btn btn-danger btn-sm" @click="delMaterial(m)">
                  <i class="bi bi-trash"></i>
                </button>
              </td>
            </tr>
            <tr class="total-row">
              <td colspan="4" class="text-right"><strong>Total materiales:</strong></td>
              <td class="text-right"><strong class="total-value">${{ fmt(totalMaterials) }}</strong></td>
              <td></td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>

    <!-- ══════════════ GASTOS ══════════════ -->
    <div v-if="tab === 'expenses'">

      <!-- Formulario gasto -->
      <div class="form-card">
        <h3 class="form-title">Registrar gasto pagado</h3>
        <div class="form-row3">
          <div class="fg col2">
            <label>Concepto *</label>
            <input v-model="expForm.concept" class="form-control" data-v="expconcept"
              placeholder="Ej: Compra de materiales, Transporte..." @input="clearErr" />
          </div>
          <div class="fg">
            <label>Monto ($) *</label>
            <input v-model.number="expForm.amount" type="number" min="0"
              class="form-control" placeholder="0" />
          </div>
          <div class="fg">
            <label>Fecha de pago</label>
            <input v-model="expForm.payment_date" type="date" class="form-control" />
          </div>
          <div class="fg">
            <label>N° Recibo / Factura</label>
            <input v-model="expForm.receipt_ref" class="form-control" placeholder="Opcional" />
          </div>
        </div>
        <button class="btn btn-primary btn-sm mt-2" @click="addExpense" :disabled="savingExp">
          <i v-if="savingExp" class="bi bi-arrow-repeat spin"></i>
          <i v-else class="bi bi-plus-lg"></i>
          {{ savingExp ? 'Guardando...' : 'Registrar gasto' }}
        </button>
      </div>

      <!-- Lista gastos -->
      <div class="list-card">
        <div v-if="expenses.length === 0" class="empty-list">
          <i class="bi bi-receipt-cutoff"></i>
          <p>No hay gastos registrados aún</p>
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>Concepto</th>
              <th class="text-center">Fecha</th>
              <th class="text-center">N° Recibo</th>
              <th class="text-right">Monto</th>
              <th class="text-center">Acción</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="e in expenses" :key="e.id">
              <td><strong>{{ e.concept }}</strong></td>
              <td class="text-center text-muted">{{ fmtDate(e.payment_date) }}</td>
              <td class="text-center text-muted">{{ e.receipt_ref || '—' }}</td>
              <td class="text-right"><strong>${{ fmt(e.amount) }}</strong></td>
              <td class="text-center">
                <button class="btn btn-danger btn-sm" @click="delExpense(e)">
                  <i class="bi bi-trash"></i>
                </button>
              </td>
            </tr>
            <tr class="total-row">
              <td colspan="3" class="text-right"><strong>Total gastos:</strong></td>
              <td class="text-right"><strong class="total-value">${{ fmt(totalExpenses) }}</strong></td>
              <td></td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { useRoute } from "vue-router"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import { validateForm } from "@/utils/validate"

const route  = useRoute()
const taskId = route.params.taskId

const task      = ref(null)
const materials = ref([])
const expenses  = ref([])
const tab       = ref("materials")
const savingMat = ref(false)
const savingExp = ref(false)

const units = ["unidad", "kg", "g", "litros", "ml", "m", "m²", "m³", "rollo", "caja", "bolsa", "par"]

const matForm = ref({ name: "", unit: "", quantity: 1, unit_cost: 0 })
const expForm = ref({ concept: "", amount: 0, payment_date: "", receipt_ref: "" })

const totalMaterials = computed(() => materials.value.reduce((s, m) => s + (m.total_cost || 0), 0))
const totalExpenses  = computed(() => expenses.value.reduce((s, e) => s + (e.amount || 0), 0))

const costStatus = computed(() => {
  if (!task.value?.budget_labor_cost) return "cost-neutral"
  const total = totalMaterials.value + totalExpenses.value
  return total <= task.value.budget_labor_cost ? "cost-ok" : "cost-over"
})

const diffLabel = computed(() => {
  const budget = task.value?.budget_labor_cost || 0
  const total  = totalMaterials.value + totalExpenses.value
  const diff   = budget - total
  if (diff >= 0) return `✓ Quedan $${fmt(diff)}`
  return `⚠ Excede $${fmt(Math.abs(diff))}`
})

function fmt(n)      { return Number(n || 0).toLocaleString("es-CO", { minimumFractionDigits: 0 }) }
function fmtDate(iso){ return iso ? new Date(iso).toLocaleDateString("es-CO", { day:"2-digit", month:"short", year:"numeric" }) : "—" }
function clearErr(e) { e.target.classList.remove("field-invalid") }

async function load() {
  try {
    const [taskRes, matRes, expRes] = await Promise.all([
      api.get(`/tasks/${taskId}`),
      api.get(`/task-materials/${taskId}`),
      api.get(`/task-expenses/${taskId}`),
    ])
    task.value      = taskRes.data
    materials.value = matRes.data
    expenses.value  = expRes.data
  } catch {
    showToast("Error cargando datos", "error")
  }
}

async function addMaterial() {
  const check = validateForm([
    { value: matForm.value.name, selector: '[data-v="matname"]', label: "Nombre del material" }
  ])
  if (!check.valid) { showToast(check.message, "warning"); return }

  savingMat.value = true
  try {
    await api.post(`/task-materials/${taskId}`, matForm.value)
    showToast("Material registrado", "success")
    matForm.value = { name: "", unit: "", quantity: 1, unit_cost: 0 }
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error guardando", "error")
  } finally {
    savingMat.value = false
  }
}

async function delMaterial(m) {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar "${m.name}"?`, icon: "warning",
    showCancelButton: true, confirmButtonText: "Eliminar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  await api.delete(`/task-materials/${m.id}`)
  showToast("Material eliminado", "success")
  await load()
}

async function addExpense() {
  const check = validateForm([
    { value: expForm.value.concept, selector: '[data-v="expconcept"]', label: "Concepto del gasto" }
  ])
  if (!check.valid) { showToast(check.message, "warning"); return }
  if (!expForm.value.amount || expForm.value.amount <= 0) {
    showToast("El monto debe ser mayor a 0", "warning"); return
  }

  savingExp.value = true
  try {
    await api.post(`/task-expenses/${taskId}`, expForm.value)
    showToast("Gasto registrado", "success")
    expForm.value = { concept: "", amount: 0, payment_date: "", receipt_ref: "" }
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error guardando", "error")
  } finally {
    savingExp.value = false
  }
}

async function delExpense(e) {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar "${e.concept}"?`, icon: "warning",
    showCancelButton: true, confirmButtonText: "Eliminar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  await api.delete(`/task-expenses/${e.id}`)
  showToast("Gasto eliminado", "success")
  await load()
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1000px; }
.page-header    { display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:20px; }
.header-left    { display:flex; align-items:flex-start; gap:12px; }
.btn-back       { background:#f1f5f9; border:none; border-radius:8px; padding:8px 12px; cursor:pointer; font-size:16px; color:#475569; }
.btn-back:hover { background:#e2e8f0; }
.page-title     { font-size:20px; font-weight:700; color:#1e293b; margin:0 0 4px; display:flex; align-items:center; gap:8px; }
.page-subtitle  { font-size:13px; color:#64748b; margin:0; }

/* RESUMEN COSTOS */
.cost-summary { display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; margin-bottom:20px; }
.cost-card    { background:#fff; border-radius:12px; padding:14px 16px; box-shadow:0 1px 4px rgba(0,0,0,0.07); display:flex; align-items:center; gap:12px; border-left:4px solid #e2e8f0; }
.cost-card .bi { font-size:22px; flex-shrink:0; }
.cost-card div { display:flex; flex-direction:column; gap:2px; min-width:0; }
.cost-label   { font-size:11px; color:#94a3b8; text-transform:uppercase; letter-spacing:0.4px; }
.cost-value   { font-size:18px; font-weight:800; color:#1e293b; }
.cost-diff    { font-size:11px; font-weight:600; }
.cost-budget   { border-left-color:#94a3b8; }
.cost-budget .bi { color:#94a3b8; }
.cost-materials { border-left-color:#3b82f6; }
.cost-materials .bi { color:#3b82f6; }
.cost-expenses  { border-left-color:#f59e0b; }
.cost-expenses .bi { color:#f59e0b; }
.cost-ok        { border-left-color:#22c55e; }
.cost-ok .bi    { color:#22c55e; }
.cost-ok .cost-diff { color:#16a34a; }
.cost-over      { border-left-color:#ef4444; }
.cost-over .bi  { color:#ef4444; }
.cost-over .cost-diff { color:#ef4444; }
.cost-neutral   { border-left-color:#94a3b8; }

/* TABS */
.main-tabs { display:flex; gap:8px; margin-bottom:16px; border-bottom:2px solid #f1f5f9; padding-bottom:0; }
.main-tab  { padding:10px 20px; border:none; background:none; font-size:14px; font-weight:600; color:#94a3b8; cursor:pointer; border-bottom:2px solid transparent; margin-bottom:-2px; display:flex; align-items:center; gap:8px; transition:all 0.15s; }
.main-tab:hover  { color:#3b82f6; }
.main-tab.active { color:#3b82f6; border-bottom-color:#3b82f6; }
.tab-badge { font-size:11px; background:#e2e8f0; color:#475569; border-radius:10px; padding:1px 8px; }

/* FORM */
.form-card  { background:#fff; border-radius:14px; box-shadow:0 1px 6px rgba(0,0,0,0.08); padding:18px 20px; margin-bottom:16px; }
.form-title { font-size:14px; font-weight:700; color:#475569; margin:0 0 14px; }
.form-row3  { display:grid; grid-template-columns:1fr 1fr 1fr 1fr auto; gap:10px; align-items:end; flex-wrap:wrap; }
.fg         { display:flex; flex-direction:column; gap:4px; }
.fg.col2    { grid-column:span 2; }
.fg label   { font-size:12px; font-weight:600; color:#374151; }
.total-col  { min-width:90px; }
.total-display { height:38px; display:flex; align-items:center; font-size:16px; font-weight:700; color:#22c55e; background:#f0fdf4; border-radius:8px; padding:0 12px; border:1px solid #bbf7d0; }

/* TABLE */
.list-card   { background:#fff; border-radius:14px; box-shadow:0 1px 6px rgba(0,0,0,0.08); overflow:hidden; }
.data-table  { width:100%; border-collapse:collapse; font-size:14px; }
.data-table th { background:#f8fafc; color:#475569; font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:0.4px; padding:11px 14px; border-bottom:1px solid #e2e8f0; }
.data-table td { padding:12px 14px; border-bottom:1px solid #f1f5f9; vertical-align:middle; }
.data-table tr:last-child td { border-bottom:none; }
.data-table tr:hover td      { background:#f8fafc; }
.total-row td { background:#f0fdf4 !important; }
.total-value  { font-size:16px; color:#16a34a; }
.text-center { text-align:center; }
.text-right  { text-align:right; }
.text-muted  { color:#94a3b8 !important; font-size:13px; }

.empty-list { padding:40px; text-align:center; color:#94a3b8; }
.empty-list .bi { font-size:36px; display:block; margin-bottom:10px; }

.spin { display:inline-block; animation:spin 0.8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

@media (max-width:768px) {
  .cost-summary { grid-template-columns:1fr 1fr; }
  .form-row3    { grid-template-columns:1fr 1fr; }
  .fg.col2      { grid-column:span 2; }
}
</style>
