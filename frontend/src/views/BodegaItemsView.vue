<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1 class="page-title"><i class="bi bi-archive me-2"></i>Artículos de Bodega</h1>
        <p class="page-subtitle">Inventario de artículos disponibles para préstamo</p>
      </div>
      <button v-if="canManage" class="btn btn-primary" @click="openCreate">
        <i class="bi bi-plus-lg"></i> Agregar artículo
      </button>
    </div>

    <div class="search-bar">
      <i class="bi bi-search"></i>
      <input v-model="search" placeholder="Buscar artículo o código..." class="search-input" />
    </div>

    <div v-if="filtered.length === 0" class="empty-state">
      <i class="bi bi-box-seam"></i>
      <p>{{ search ? 'Sin resultados' : 'No hay artículos registrados' }}</p>
      <button v-if="!search && canManage" class="btn btn-primary btn-sm" @click="openCreate">Agregar el primero</button>
    </div>

    <div v-else class="sub-card p-0">
      <table class="data-table">
        <thead>
          <tr>
            <th>Artículo</th>
            <th class="text-center">Código</th>
            <th class="text-center">Total</th>
            <th class="text-center">Disponible</th>
            <th>Ubicación</th>
            <th v-if="canManage" class="text-center">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filtered" :key="item.id">
            <td>
              <strong>{{ item.nombre }}</strong>
              <div v-if="item.descripcion" class="item-desc">{{ item.descripcion }}</div>
            </td>
            <td class="text-center text-muted">{{ item.codigo || '—' }}</td>
            <td class="text-center">{{ item.cantidad_total }}</td>
            <td class="text-center">
              <span class="stock-chip" :class="item.cantidad_disponible === 0 ? 'stock-red' : item.cantidad_disponible < item.cantidad_total ? 'stock-amber' : 'stock-green'">
                {{ item.cantidad_disponible }}
              </span>
            </td>
            <td class="text-muted">{{ item.ubicacion_bodega || '—' }}</td>
            <td v-if="canManage" class="text-center">
              <div class="action-btns">
                <button class="btn btn-sm btn-outline-primary" @click="openEdit(item)"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-sm btn-outline-danger" @click="remove(item)"><i class="bi bi-trash"></i></button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal -->
    <div v-if="modal" class="modal-overlay" @click.self="modal = false">
      <div class="modal-card">
        <div class="modal-header">
          <h3>{{ editing ? 'Editar artículo' : 'Nuevo artículo de bodega' }}</h3>
          <button class="modal-close" @click="modal = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-body">
          <div class="form-row2">
            <div class="fg span2">
              <label>Nombre *</label>
              <input v-model="form.nombre" class="form-control" placeholder="Ej: Taladro, Escalera, Herramienta..." autofocus />
            </div>
            <div class="fg span2">
              <label>Descripción</label>
              <input v-model="form.descripcion" class="form-control" placeholder="Detalles del artículo" />
            </div>
            <div class="fg">
              <label>Código</label>
              <input v-model="form.codigo" class="form-control" placeholder="Ej: BOD-001" />
            </div>
            <div class="fg">
              <label>Cantidad total *</label>
              <input v-model.number="form.cantidad_total" type="number" min="1" class="form-control" />
            </div>
            <div class="fg">
              <label>Unidad</label>
              <select v-model="form.unidad_id" class="form-select">
                <option :value="null">— Sin unidad —</option>
                <option v-for="u in unidades" :key="u.id" :value="u.id">
                  {{ u.name }}{{ u.abreviatura ? ' (' + u.abreviatura + ')' : '' }}
                </option>
              </select>
            </div>
            <div class="fg">
              <label>Ubicación en bodega</label>
              <input v-model="form.ubicacion_bodega" class="form-control" placeholder="Ej: Estante A3, Almacén 2..." />
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
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

const userInfo  = JSON.parse(localStorage.getItem("user") || "{}")
const canManage = !['WORKER','AUDITOR'].some(r => (userInfo.role || '').toUpperCase().includes(r))

const items   = ref([])
const unidades = ref([])
const search  = ref("")
const modal   = ref(false)
const saving  = ref(false)
const editing = ref(null)
const form = ref({ nombre: "", descripcion: "", codigo: "", cantidad_total: 1, unidad_id: null, ubicacion_bodega: "" })

const filtered = computed(() => {
  const q = search.value.toLowerCase()
  return items.value.filter(i =>
    i.nombre.toLowerCase().includes(q) || (i.codigo || "").toLowerCase().includes(q)
  )
})

async function load() {
  try {
    const [ir, ur] = await Promise.all([api.get("/bodega-items/"), api.get("/unidades-medida/")])
    items.value   = ir.data
    unidades.value = ur.data
  } catch { showToast("Error cargando datos", "error") }
}

function openCreate() {
  editing.value = null
  form.value = { nombre: "", descripcion: "", codigo: "", cantidad_total: 1, unidad_id: null, ubicacion_bodega: "" }
  modal.value = true
}
function openEdit(item) {
  editing.value = item
  form.value = { nombre: item.nombre, descripcion: item.descripcion || "", codigo: item.codigo || "", cantidad_total: item.cantidad_total, unidad_id: item.unidad_id, ubicacion_bodega: item.ubicacion_bodega || "" }
  modal.value = true
}

async function save() {
  if (!form.value.nombre.trim()) { showToast("El nombre es obligatorio", "warning"); return }
  if (form.value.cantidad_total < 1) { showToast("La cantidad debe ser al menos 1", "warning"); return }
  saving.value = true
  try {
    if (editing.value) {
      const r = await api.put(`/bodega-items/${editing.value.id}`, form.value)
      const idx = items.value.findIndex(i => i.id === editing.value.id)
      if (idx !== -1) items.value[idx] = r.data
      showToast("Artículo actualizado", "success")
    } else {
      const r = await api.post("/bodega-items/", form.value)
      items.value.push(r.data)
      showToast("Artículo agregado", "success")
    }
    modal.value = false
  } catch (e) {
    showToast(e.response?.data?.detail || "Error guardando", "error")
  } finally { saving.value = false }
}

async function remove(item) {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar "${item.nombre}"?`, icon: "warning",
    showCancelButton: true, confirmButtonText: "Eliminar",
    cancelButtonText: "Cancelar", confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/bodega-items/${item.id}`)
    items.value = items.value.filter(i => i.id !== item.id)
    showToast("Artículo eliminado", "success")
  } catch (e) { showToast(e.response?.data?.detail || "Error eliminando", "error") }
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1000px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; gap: 12px; flex-wrap: wrap; }
.page-title  { font-size: 22px; font-weight: 700; color: #1e293b; margin: 0 0 4px; }
.page-subtitle { font-size: 13px; color: #64748b; margin: 0; }
.search-bar { display: flex; align-items: center; gap: 8px; background: #fff; border: 1.5px solid #e2e8f0; border-radius: 10px; padding: 8px 14px; margin-bottom: 16px; }
.search-bar .bi { color: #94a3b8; }
.search-input { border: none; outline: none; flex: 1; font-size: 14px; color: #1e293b; background: transparent; }
.empty-state { background: #fff; border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,.08); padding: 60px 24px; text-align: center; color: #94a3b8; display: flex; flex-direction: column; align-items: center; gap: 10px; }
.empty-state .bi { font-size: 40px; }
.sub-card   { background: #fff; border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,.08); }
.sub-card.p-0 { padding: 0; overflow: hidden; }
.data-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.data-table th { background: #f8fafc; color: #475569; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: .4px; padding: 11px 14px; border-bottom: 1px solid #e2e8f0; }
.data-table td { padding: 12px 14px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: #f8fafc; }
.text-center { text-align: center; }
.text-muted  { color: #94a3b8; font-size: 13px; }
.item-desc   { font-size: 11px; color: #94a3b8; margin-top: 2px; }
.stock-chip  { font-size: 12px; font-weight: 700; padding: 2px 10px; border-radius: 10px; }
.stock-green { background: #dcfce7; color: #16a34a; }
.stock-amber { background: #fef3c7; color: #b45309; }
.stock-red   { background: #fef2f2; color: #b91c1c; }
.action-btns { display: flex; gap: 6px; justify-content: center; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 3000; padding: 16px; }
.modal-card  { background: #fff; border-radius: 14px; width: 100%; max-width: 500px; box-shadow: 0 20px 50px rgba(0,0,0,.2); overflow: hidden; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid #f1f5f9; }
.modal-header h3 { font-size: 15px; font-weight: 700; color: #1e293b; margin: 0; }
.modal-close { background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 14px; }
.modal-body  { padding: 20px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 8px; padding: 14px 20px; border-top: 1px solid #f1f5f9; }
.form-row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.fg        { display: flex; flex-direction: column; gap: 4px; }
.fg label  { font-size: 13px; font-weight: 600; color: #374151; }
.span2     { grid-column: span 2; }
.btn       { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; transition: all .15s; }
.btn-primary { background: #3b82f6; color: #fff; } .btn-primary:hover { background: #2563eb; }
.btn-primary:disabled { opacity: .6; cursor: not-allowed; }
.btn-secondary { border: 1.5px solid #e2e8f0; background: #fff; color: #64748b; }
.btn-sm { padding: 6px 12px; font-size: 12px; }
.btn-outline-primary { background: #eff6ff; color: #1d4ed8; border: 1.5px solid #bfdbfe; }
.btn-outline-danger  { background: #fef2f2; color: #b91c1c; border: 1.5px solid #fecaca; }
.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
@media (max-width: 640px) { .form-row2 { grid-template-columns: 1fr; } .span2 { grid-column: span 1; } }
</style>
