<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1 class="page-title"><i class="bi bi-grid me-2"></i>Productos</h1>
        <p class="page-subtitle">Catálogo de productos de venta con control de inventario</p>
      </div>
      <button class="btn btn-primary" @click="openCreate"><i class="bi bi-plus-lg"></i> Nuevo producto</button>
    </div>

    <div class="filters-row">
      <input v-model="search" class="form-control" placeholder="Buscar por nombre o código..." style="max-width:260px" />
      <select v-model="filterCat" class="form-select" style="max-width:180px">
        <option value="">Todas las categorías</option>
        <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
      <select v-model="filterBehavior" class="form-select" style="max-width:180px">
        <option value="">Todos los tipos</option>
        <option value="direct">Sin inventario</option>
        <option value="recipe">Receta</option>
        <option value="presentation">Presentaciones</option>
        <option value="serialized">Serializado (IMEI)</option>
        <option value="weight">Por peso</option>
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
            <th>Categoría</th>
            <th>Tipo inv.</th>
            <th class="text-right">Precio</th>
            <th class="text-right">Costo</th>
            <th class="text-center">Estado</th>
            <th class="text-center">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in filtered" :key="p.id">
            <td class="text-muted">{{ p.id }}</td>
            <td class="text-muted">{{ p.code || '—' }}</td>
            <td>
              <strong>{{ p.name }}</strong>
              <div v-if="p.description" class="sub-text">{{ p.description?.slice(0,60) }}{{ p.description?.length > 60 ? '…' : '' }}</div>
            </td>
            <td class="text-muted">{{ p.category_name || '—' }}</td>
            <td>
              <span class="behavior-badge" :class="'beh-' + p.inventory_behavior">
                {{ behaviorLabel(p.inventory_behavior) }}
              </span>
            </td>
            <td class="text-right">{{ fmtMoney(p.base_price) }}</td>
            <td class="text-right text-muted">{{ fmtMoney(p.cost_price) }}</td>
            <td class="text-center">
              <span class="badge-status" :class="p.is_active ? 'active' : 'inactive'">
                {{ p.is_active ? 'Activo' : 'Inactivo' }}
              </span>
            </td>
            <td class="text-center">
              <div class="action-row">
                <button class="btn btn-sm btn-outline-primary" @click="openEdit(p)" title="Editar"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-sm btn-outline-secondary" @click="toggleActive(p)" :title="p.is_active ? 'Desactivar' : 'Activar'">
                  <i :class="p.is_active ? 'bi bi-toggle-on text-success' : 'bi bi-toggle-off'"></i>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="filtered.length === 0">
            <td colspan="9" class="text-center text-muted py-4">No hay productos registrados</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- MODAL CREAR/EDITAR -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-box modal-lg">
        <div class="mh">
          <h3><i class="bi bi-grid me-2"></i>{{ editing ? 'Editar' : 'Nuevo' }} Producto</h3>
          <button class="btn-x" @click="showModal = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="mb-area">
          <div class="form-row2">
            <div class="fg">
              <label>Código / Referencia</label>
              <input v-model="form.code" class="form-control" placeholder="SKU-001" />
            </div>
            <div class="fg">
              <label>Nombre *</label>
              <input v-model="form.name" class="form-control" placeholder="Nombre del producto" />
            </div>
          </div>
          <div class="fg">
            <label>Descripción</label>
            <textarea v-model="form.description" class="form-control" rows="2" placeholder="Descripción opcional..."></textarea>
          </div>
          <div class="form-row2">
            <div class="fg">
              <label>Categoría</label>
              <select v-model="form.category_id" class="form-select">
                <option :value="null">— Sin categoría —</option>
                <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            <div class="fg">
              <label>Tipo de inventario *</label>
              <select v-model="form.inventory_behavior" class="form-select">
                <option value="direct">Sin control de inventario</option>
                <option value="recipe">Receta (descarga insumos)</option>
                <option value="presentation">Presentaciones (unidad/caja/blister)</option>
                <option value="serialized">Serializado (IMEI / serie única)</option>
                <option value="weight">Por peso (balanza)</option>
              </select>
            </div>
          </div>
          <div class="section-divider">Precios</div>
          <div class="form-row3">
            <div class="fg">
              <label>Precio de venta *</label>
              <CurrencyInput v-model="form.base_price" class="form-control" />
            </div>
            <div class="fg">
              <label>Costo</label>
              <CurrencyInput v-model="form.cost_price" class="form-control" />
            </div>
            <div class="fg">
              <label>% Impuesto</label>
              <input v-model.number="form.tax_rate" type="number" min="0" max="100" step="0.01" class="form-control" placeholder="0" />
            </div>
          </div>
          <div class="fg">
            <label>Stock mínimo (para alertas)</label>
            <input v-model.number="form.min_stock" type="number" min="0" step="0.001" class="form-control" />
          </div>
          <div class="section-divider">Opciones en POS</div>
          <div class="toggles-row">
            <label class="toggle-label">
              <input type="checkbox" v-model="form.ask_price" :true-value="1" :false-value="0" />
              <span>Pedir precio al vender</span>
            </label>
            <label class="toggle-label">
              <input type="checkbox" v-model="form.ask_description" :true-value="1" :false-value="0" />
              <span>Pedir descripción al vender</span>
            </label>
          </div>
          <div class="utilidad-preview" v-if="form.base_price > 0 && form.cost_price > 0">
            <span>Utilidad: <strong>{{ fmtMoney(form.base_price - form.cost_price) }}</strong></span>
            <span class="util-pct" :class="utilPct >= 30 ? 'good' : utilPct >= 10 ? 'mid' : 'low'">
              {{ utilPct.toFixed(1) }}%
            </span>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

const products    = ref([])
const categories  = ref([])
const loading     = ref(true)
const search      = ref("")
const filterCat   = ref("")
const filterBehavior = ref("")
const showModal   = ref(false)
const editing     = ref(null)
const saving      = ref(false)
const form        = ref({})

const BEHAVIOR_LABELS = {
  direct:       "Sin inv.",
  recipe:       "Receta",
  presentation: "Presentac.",
  serialized:   "Serializado",
  weight:       "Por peso",
}

function behaviorLabel(b) { return BEHAVIOR_LABELS[b] || b }

function fmtMoney(v) {
  return Number(v || 0).toLocaleString("es-CO", { style: "currency", currency: "COP", minimumFractionDigits: 0 })
}

const utilPct = computed(() => {
  const price = form.value.base_price || 0
  const cost  = form.value.cost_price  || 0
  if (!price) return 0
  return ((price - cost) / price) * 100
})

const filtered = computed(() => {
  return products.value.filter(p => {
    const q = search.value.toLowerCase()
    const matchQ   = !q || p.name.toLowerCase().includes(q) || (p.code || "").toLowerCase().includes(q)
    const matchCat = !filterCat.value || p.category_id === filterCat.value
    const matchBeh = !filterBehavior.value || p.inventory_behavior === filterBehavior.value
    return matchQ && matchCat && matchBeh
  })
})

async function load() {
  loading.value = true
  try {
    const [pr, cr] = await Promise.all([api.get("/products/"), api.get("/product-categories/")])
    products.value   = pr.data
    categories.value = cr.data
  } catch { showToast("Error cargando productos", "error") }
  finally { loading.value = false }
}

function openCreate() {
  editing.value = null
  form.value = {
    code: "", name: "", description: "", category_id: null,
    inventory_behavior: "direct", base_price: 0, cost_price: 0,
    tax_rate: 0, min_stock: 0, ask_price: 0, ask_description: 0
  }
  showModal.value = true
}

function openEdit(p) {
  editing.value = p
  form.value = { ...p }
  showModal.value = true
}

async function submit() {
  if (!form.value.name?.trim()) { showToast("El nombre es requerido", "warning"); return }
  saving.value = true
  try {
    if (editing.value) {
      const r = await api.put(`/products/${editing.value.id}`, form.value)
      const idx = products.value.findIndex(x => x.id === editing.value.id)
      if (idx !== -1) products.value[idx] = r.data
    } else {
      const r = await api.post("/products/", form.value)
      products.value.unshift(r.data)
    }
    showModal.value = false
    showToast("Producto guardado", "success")
  } catch (e) { showToast(e.response?.data?.detail || "Error", "error") }
  finally { saving.value = false }
}

async function toggleActive(p) {
  try {
    const r = await api.put(`/products/${p.id}`, { is_active: p.is_active ? 0 : 1 })
    const idx = products.value.findIndex(x => x.id === p.id)
    if (idx !== -1) products.value[idx] = r.data
  } catch { showToast("Error actualizando", "error") }
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1200px; }
.page-header    { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; gap: 12px; flex-wrap: wrap; }
.page-title     { font-size: 22px; font-weight: 700; color: #1e293b; margin: 0 0 4px; }
.page-subtitle  { font-size: 13px; color: #64748b; margin: 0; }
.filters-row    { display: flex; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
.table-card     { background: #fff; border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,.08); overflow: hidden; }
.table-loading  { padding: 40px; text-align: center; color: #94a3b8; }
.data-table     { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th  { background: #f8fafc; color: #475569; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: .4px; padding: 11px 12px; border-bottom: 1px solid #e2e8f0; }
.data-table td  { padding: 11px 12px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: #f8fafc; }
.text-center { text-align: center; }
.text-right  { text-align: right; }
.text-muted  { color: #94a3b8; font-size: 12px; }
.sub-text    { font-size: 11px; color: #94a3b8; margin-top: 2px; }
.py-4        { padding: 32px 0; }
.behavior-badge { font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 20px; white-space: nowrap; }
.beh-direct       { background: #f1f5f9; color: #64748b; }
.beh-recipe       { background: #fef9c3; color: #854d0e; }
.beh-presentation { background: #dbeafe; color: #1e40af; }
.beh-serialized   { background: #f3e8ff; color: #7e22ce; }
.beh-weight       { background: #dcfce7; color: #166534; }
.badge-status { font-size: 10px; font-weight: 700; padding: 2px 9px; border-radius: 20px; }
.badge-status.active   { background: #dcfce7; color: #16a34a; }
.badge-status.inactive { background: #f1f5f9; color: #94a3b8; }
.action-row  { display: flex; gap: 4px; justify-content: center; }
.section-divider { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .5px; color: #94a3b8; border-bottom: 1px solid #f1f5f9; padding-bottom: 4px; }
.form-row3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
.toggles-row { display: flex; gap: 20px; flex-wrap: wrap; }
.toggle-label { display: flex; align-items: center; gap: 8px; cursor: pointer; font-size: 13px; color: #374151; }
.toggle-label input[type=checkbox] { width: 16px; height: 16px; cursor: pointer; }
.utilidad-preview { background: #f8fafc; border-radius: 8px; padding: 10px 16px; display: flex; align-items: center; gap: 16px; font-size: 13px; color: #475569; }
.util-pct { font-weight: 700; font-size: 14px; }
.util-pct.good { color: #16a34a; } .util-pct.mid { color: #b45309; } .util-pct.low { color: #dc2626; }
.text-success { color: #16a34a; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 2000; padding: 16px; }
.modal-box     { background: #fff; border-radius: 16px; width: 100%; max-width: 540px; max-height: 90vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,.2); }
.modal-lg      { max-width: 600px; }
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
@media (max-width: 640px) { .form-row2, .form-row3 { grid-template-columns: 1fr; } }
</style>
