<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1 class="page-title"><i class="bi bi-box-seam me-2"></i>Insumos</h1>
        <p class="page-subtitle">Materias primas y artículos base del inventario</p>
      </div>
      <button class="btn btn-primary" @click="openCreate"><i class="bi bi-plus-lg"></i> Nuevo insumo</button>
    </div>

    <!-- KPI -->
    <div class="kpi-bar">
      <div class="kpi-card">
        <span class="kpi-num">{{ items.length }}</span>
        <span class="kpi-label">Total insumos</span>
      </div>
      <div class="kpi-card kpi-red">
        <span class="kpi-num">{{ lowStock.length }}</span>
        <span class="kpi-label">Stock bajo</span>
      </div>
      <div class="kpi-card kpi-green">
        <span class="kpi-num">{{ items.filter(i => i.control_stock).length }}</span>
        <span class="kpi-label">Con control</span>
      </div>
    </div>

    <div class="filters-row">
      <input v-model="search" class="form-control" placeholder="Buscar por nombre o código..." style="max-width:280px" />
      <select v-model="filterStock" class="form-select" style="max-width:180px">
        <option value="">Todos</option>
        <option value="low">Stock bajo</option>
        <option value="ok">Stock OK</option>
      </select>
    </div>

    <div class="table-card">
      <div v-if="loading" class="table-loading"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Código</th>
            <th>Nombre</th>
            <th>Unidad</th>
            <th class="text-right">Costo</th>
            <th class="text-right">Stock</th>
            <th class="text-right">Mínimo</th>
            <th class="text-center">Control</th>
            <th class="text-center">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="i in filtered" :key="i.id" :class="{ 'row-low': isLowStock(i) }">
            <td class="text-muted">{{ i.id }}</td>
            <td class="text-muted">{{ i.code || '—' }}</td>
            <td>
              <strong>{{ i.name }}</strong>
              <div v-if="i.description" class="sub-text">{{ i.description }}</div>
            </td>
            <td class="text-muted">{{ i.unit_name || '—' }}</td>
            <td class="text-right">{{ fmtNum(i.cost_price) }}</td>
            <td class="text-right" :class="isLowStock(i) ? 'text-danger fw-bold' : ''">
              <i v-if="isLowStock(i)" class="bi bi-exclamation-triangle-fill me-1"></i>
              {{ fmtNum(i.stock_qty, 4) }}
            </td>
            <td class="text-right text-muted">{{ fmtNum(i.min_stock, 4) }}</td>
            <td class="text-center">
              <span v-if="i.control_stock" class="badge-yes">Sí</span>
              <span v-else class="badge-no">No</span>
            </td>
            <td class="text-center">
              <div class="action-row">
                <button class="btn btn-sm btn-outline-primary" @click="openEdit(i)" title="Editar"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-sm btn-outline-secondary" @click="openAdjust(i)" title="Ajustar stock"><i class="bi bi-sliders"></i></button>
              </div>
            </td>
          </tr>
          <tr v-if="filtered.length === 0">
            <td colspan="9" class="text-center text-muted py-4">No hay insumos registrados</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- MODAL CREAR/EDITAR -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-box">
        <div class="mh">
          <h3><i class="bi bi-box-seam me-2"></i>{{ editing ? 'Editar' : 'Nuevo' }} Insumo</h3>
          <button class="btn-x" @click="showModal = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="mb-area">
          <div class="form-row2">
            <div class="fg">
              <label>Código</label>
              <input v-model="form.code" class="form-control" placeholder="INS-001" />
            </div>
            <div class="fg">
              <label>Nombre *</label>
              <input v-model="form.name" class="form-control" placeholder="Nombre del insumo" />
            </div>
          </div>
          <div class="fg">
            <label>Descripción</label>
            <input v-model="form.description" class="form-control" placeholder="Descripción breve..." />
          </div>
          <div class="form-row2">
            <div class="fg">
              <label>Unidad de medida</label>
              <select v-model="form.unit_id" class="form-select">
                <option :value="null">— Sin unidad —</option>
                <option v-for="u in units" :key="u.id" :value="u.id">{{ u.name }} ({{ u.abreviatura }})</option>
              </select>
            </div>
            <div class="fg">
              <label>Costo unitario</label>
              <input v-model.number="form.cost_price" type="number" min="0" step="0.01" class="form-control" />
            </div>
          </div>
          <div class="form-row2">
            <div class="fg">
              <label>{{ editing ? 'Ajustar stock a' : 'Stock inicial' }}</label>
              <input v-model.number="form.stock_qty" type="number" min="0" step="0.001" class="form-control" />
            </div>
            <div class="fg">
              <label>Stock mínimo (alerta)</label>
              <input v-model.number="form.min_stock" type="number" min="0" step="0.001" class="form-control" />
            </div>
          </div>
          <div class="fg" v-if="editing && form.stock_qty !== editing.stock_qty">
            <label>Motivo del ajuste</label>
            <input v-model="form.adjustment_notes" class="form-control" placeholder="Ej: Conteo físico, corrección..." />
          </div>
          <div class="fg">
            <label>% Merma</label>
            <input v-model.number="form.waste_pct" type="number" min="0" max="100" step="0.01" class="form-control" placeholder="0" />
          </div>
          <div class="toggle-row">
            <label class="toggle-label">
              <input type="checkbox" v-model="form.control_stock" :true-value="1" :false-value="0" />
              <span>Controlar inventario</span>
            </label>
          </div>
        </div>
        <div class="mf">
          <button class="btn btn-secondary btn-sm" @click="showModal = false">Cancelar</button>
          <button class="btn btn-primary btn-sm" @click="submit" :disabled="saving">
            <i v-if="saving" class="bi bi-arrow-repeat spin"></i>
            {{ saving ? 'Guardando...' : 'Guardar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL AJUSTE RÁPIDO DE STOCK -->
    <div v-if="showAdjust" class="modal-overlay" @click.self="showAdjust = false">
      <div class="modal-box modal-sm">
        <div class="mh">
          <h3><i class="bi bi-sliders me-2"></i>Ajustar Stock</h3>
          <button class="btn-x" @click="showAdjust = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="mb-area">
          <div class="info-block">
            <strong>{{ adjustItem?.name }}</strong>
            <span class="text-muted">Stock actual: {{ fmtNum(adjustItem?.stock_qty, 4) }}</span>
          </div>
          <div class="fg">
            <label>Nuevo stock *</label>
            <input v-model.number="adjustForm.stock_qty" type="number" min="0" step="0.001" class="form-control" />
          </div>
          <div class="fg">
            <label>Motivo del ajuste *</label>
            <input v-model="adjustForm.adjustment_notes" class="form-control" placeholder="Conteo físico, pérdida, corrección..." />
          </div>
        </div>
        <div class="mf">
          <button class="btn btn-secondary btn-sm" @click="showAdjust = false">Cancelar</button>
          <button class="btn btn-primary btn-sm" @click="submitAdjust" :disabled="saving">
            {{ saving ? 'Guardando...' : 'Ajustar' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

const items      = ref([])
const units      = ref([])
const loading    = ref(true)
const search     = ref("")
const filterStock = ref("")
const showModal  = ref(false)
const editing    = ref(null)
const saving     = ref(false)
const form       = ref({})

const showAdjust  = ref(false)
const adjustItem  = ref(null)
const adjustForm  = ref({})

const lowStock = computed(() => items.value.filter(i => isLowStock(i)))

function isLowStock(i) {
  return i.control_stock && i.min_stock > 0 && i.stock_qty <= i.min_stock
}

const filtered = computed(() => {
  return items.value.filter(i => {
    const q = search.value.toLowerCase()
    const matchQ = !q || i.name.toLowerCase().includes(q) || (i.code || "").toLowerCase().includes(q)
    const matchStock = !filterStock.value ||
      (filterStock.value === "low" && isLowStock(i)) ||
      (filterStock.value === "ok"  && !isLowStock(i))
    return matchQ && matchStock
  })
})

function fmtNum(val, dec = 2) {
  return Number(val || 0).toLocaleString("es-CO", { minimumFractionDigits: 0, maximumFractionDigits: dec })
}

async function load() {
  loading.value = true
  try {
    const [ir, ur] = await Promise.all([api.get("/supply-items/"), api.get("/unidades-medida/")])
    items.value = ir.data
    units.value = ur.data
  } catch { showToast("Error cargando insumos", "error") }
  finally { loading.value = false }
}

function openCreate() {
  editing.value = null
  form.value = { code: "", name: "", description: "", unit_id: null, cost_price: 0, stock_qty: 0, min_stock: 0, waste_pct: 0, control_stock: 1 }
  showModal.value = true
}

function openEdit(i) {
  editing.value = i
  form.value = { ...i, adjustment_notes: "" }
  showModal.value = true
}

function openAdjust(i) {
  adjustItem.value = i
  adjustForm.value = { stock_qty: i.stock_qty, adjustment_notes: "" }
  showAdjust.value = true
}

async function submit() {
  if (!form.value.name?.trim()) { showToast("El nombre es requerido", "warning"); return }
  saving.value = true
  try {
    if (editing.value) {
      const r = await api.put(`/supply-items/${editing.value.id}`, form.value)
      const idx = items.value.findIndex(x => x.id === editing.value.id)
      if (idx !== -1) items.value[idx] = r.data
    } else {
      const r = await api.post("/supply-items/", form.value)
      items.value.unshift(r.data)
    }
    showModal.value = false
    showToast("Insumo guardado", "success")
  } catch (e) { showToast(e.response?.data?.detail || "Error guardando", "error") }
  finally { saving.value = false }
}

async function submitAdjust() {
  if (!adjustForm.value.adjustment_notes?.trim()) { showToast("El motivo es requerido", "warning"); return }
  saving.value = true
  try {
    const r = await api.put(`/supply-items/${adjustItem.value.id}`, adjustForm.value)
    const idx = items.value.findIndex(x => x.id === adjustItem.value.id)
    if (idx !== -1) items.value[idx] = r.data
    showAdjust.value = false
    showToast("Stock ajustado", "success")
  } catch (e) { showToast(e.response?.data?.detail || "Error", "error") }
  finally { saving.value = false }
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1100px; }
.page-header    { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; gap: 12px; flex-wrap: wrap; }
.page-title     { font-size: 22px; font-weight: 700; color: #1e293b; margin: 0 0 4px; }
.page-subtitle  { font-size: 13px; color: #64748b; margin: 0; }
.kpi-bar  { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 18px; }
.kpi-card { background: #fff; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.07); padding: 12px 18px; display: flex; align-items: baseline; gap: 8px; }
.kpi-num  { font-size: 24px; font-weight: 800; color: #1e293b; }
.kpi-label { font-size: 12px; color: #94a3b8; }
.kpi-red .kpi-num   { color: #dc2626; }
.kpi-green .kpi-num { color: #16a34a; }
.filters-row { display: flex; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
.table-card  { background: #fff; border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,.08); overflow: hidden; }
.table-loading { padding: 40px; text-align: center; color: #94a3b8; }
.data-table  { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { background: #f8fafc; color: #475569; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: .4px; padding: 11px 12px; border-bottom: 1px solid #e2e8f0; }
.data-table td { padding: 11px 12px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: #f8fafc; }
.row-low td { background: #fff5f5 !important; }
.text-center { text-align: center; }
.text-right  { text-align: right; }
.text-muted  { color: #94a3b8; font-size: 12px; }
.text-danger { color: #ef4444; }
.fw-bold     { font-weight: 700; }
.sub-text    { font-size: 11px; color: #94a3b8; margin-top: 2px; }
.py-4        { padding: 32px 0; }
.badge-yes { background: #dcfce7; color: #16a34a; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 20px; }
.badge-no  { background: #f1f5f9; color: #94a3b8; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 20px; }
.action-row { display: flex; gap: 4px; justify-content: center; }
.info-block { background: #f8fafc; border-radius: 8px; padding: 10px 14px; display: flex; flex-direction: column; gap: 4px; font-size: 13px; }
.toggle-row { display: flex; align-items: center; }
.toggle-label { display: flex; align-items: center; gap: 8px; cursor: pointer; font-size: 13px; font-weight: 600; color: #374151; }
.toggle-label input[type=checkbox] { width: 16px; height: 16px; cursor: pointer; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 2000; padding: 16px; }
.modal-box     { background: #fff; border-radius: 16px; width: 100%; max-width: 520px; max-height: 90vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,.2); }
.modal-sm      { max-width: 400px; }
.mh  { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid #f1f5f9; }
.mh h3 { font-size: 15px; font-weight: 700; color: #1e293b; margin: 0; }
.btn-x { background: none; border: none; font-size: 16px; cursor: pointer; color: #94a3b8; }
.mb-area { padding: 18px 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; }
.mf { padding: 12px 20px 16px; display: flex; justify-content: flex-end; gap: 8px; border-top: 1px solid #f1f5f9; }
.fg       { display: flex; flex-direction: column; gap: 4px; }
.fg label { font-size: 13px; font-weight: 600; color: #374151; }
.form-row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.btn { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; transition: all .15s; }
.btn-primary   { background: #3b82f6; color: #fff; } .btn-primary:hover { background: #2563eb; }
.btn-primary:disabled { opacity: .6; cursor: not-allowed; }
.btn-secondary { border: 1.5px solid #e2e8f0; background: #fff; color: #64748b; }
.btn-sm { padding: 6px 12px; font-size: 12px; }
.btn-outline-primary   { background: #eff6ff; color: #1d4ed8; border: 1.5px solid #bfdbfe; }
.btn-outline-secondary { background: #f8fafc; color: #475569; border: 1.5px solid #e2e8f0; }
.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
@media (max-width: 640px) { .form-row2 { grid-template-columns: 1fr; } }
</style>
