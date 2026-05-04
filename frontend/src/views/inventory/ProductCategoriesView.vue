<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1 class="page-title"><i class="bi bi-tags me-2"></i>Categorías de Producto</h1>
        <p class="page-subtitle">Agrupa tus productos para facilitar la búsqueda y el reporte</p>
      </div>
      <button class="btn btn-primary" @click="openCreate"><i class="bi bi-plus-lg"></i> Nueva categoría</button>
    </div>

    <div class="filters-row">
      <input v-model="search" class="form-control" placeholder="Buscar categoría..." style="max-width:260px" />
    </div>

    <div class="categories-grid">
      <div v-if="loading" class="table-loading"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
      <template v-else>
        <div v-for="c in filtered" :key="c.id" class="cat-card">
          <div class="cat-icon" :style="{ background: c.color || '#e2e8f0' }">
            <i :class="c.icon || 'bi bi-tag'" style="font-size:20px; color:#fff;"></i>
          </div>
          <div class="cat-info">
            <strong>{{ c.name }}</strong>
            <div v-if="c.description" class="sub-text">{{ c.description }}</div>
          </div>
          <div class="cat-actions">
            <button class="btn btn-sm btn-outline-primary" @click="openEdit(c)" title="Editar"><i class="bi bi-pencil"></i></button>
            <button class="btn btn-sm btn-outline-danger" @click="remove(c)" title="Eliminar"><i class="bi bi-trash"></i></button>
          </div>
        </div>
        <div v-if="filtered.length === 0" class="empty-state">No hay categorías creadas aún</div>
      </template>
    </div>

    <!-- MODAL -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-box">
        <div class="mh">
          <h3><i class="bi bi-tags me-2"></i>{{ editing ? 'Editar' : 'Nueva' }} Categoría</h3>
          <button class="btn-x" @click="showModal = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="mb-area">
          <div class="fg">
            <label>Nombre *</label>
            <input v-model="form.name" class="form-control" placeholder="Nombre de la categoría" />
          </div>
          <div class="fg">
            <label>Descripción</label>
            <input v-model="form.description" class="form-control" placeholder="Descripción opcional" />
          </div>
          <div class="form-row2">
            <div class="fg">
              <label>Ícono Bootstrap</label>
              <input v-model="form.icon" class="form-control" placeholder="bi bi-tag" />
              <span class="hint">ej: bi bi-bag, bi bi-cup-hot, bi bi-capsule</span>
            </div>
            <div class="fg">
              <label>Color</label>
              <input v-model="form.color" type="color" class="form-control form-control-color" style="height:38px;padding:2px 6px;" />
            </div>
          </div>
          <div class="preview-cat" v-if="form.name">
            <div class="cat-icon" :style="{ background: form.color || '#e2e8f0' }">
              <i :class="form.icon || 'bi bi-tag'" style="font-size:20px;color:#fff;"></i>
            </div>
            <strong>{{ form.name }}</strong>
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

const categories = ref([])
const loading    = ref(true)
const search     = ref("")
const showModal  = ref(false)
const editing    = ref(null)
const saving     = ref(false)
const form       = ref({})

const filtered = computed(() => {
  const q = search.value.toLowerCase()
  return categories.value.filter(c => !q || c.name.toLowerCase().includes(q))
})

async function load() {
  loading.value = true
  try { categories.value = (await api.get("/product-categories/")).data }
  catch { showToast("Error cargando categorías", "error") }
  finally { loading.value = false }
}

function openCreate() {
  editing.value = null
  form.value = { name: "", description: "", icon: "bi bi-tag", color: "#3b82f6" }
  showModal.value = true
}

function openEdit(c) {
  editing.value = c
  form.value = { ...c }
  showModal.value = true
}

async function submit() {
  if (!form.value.name?.trim()) { showToast("El nombre es requerido", "warning"); return }
  saving.value = true
  try {
    if (editing.value) {
      const r = await api.put(`/product-categories/${editing.value.id}`, form.value)
      const idx = categories.value.findIndex(x => x.id === editing.value.id)
      if (idx !== -1) categories.value[idx] = r.data
    } else {
      const r = await api.post("/product-categories/", form.value)
      categories.value.push(r.data)
    }
    showModal.value = false
    showToast("Categoría guardada", "success")
  } catch (e) { showToast(e.response?.data?.detail || "Error", "error") }
  finally { saving.value = false }
}

async function remove(c) {
  const { isConfirmed } = await window.Swal.fire({
    title: "¿Eliminar categoría?", text: `"${c.name}" dejará de estar disponible.`,
    icon: "warning", showCancelButton: true, confirmButtonText: "Sí, eliminar", cancelButtonText: "Cancelar"
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/product-categories/${c.id}`)
    categories.value = categories.value.filter(x => x.id !== c.id)
    showToast("Categoría eliminada", "success")
  } catch (e) { showToast(e.response?.data?.detail || "Error", "error") }
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1000px; }
.page-header    { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; gap: 12px; flex-wrap: wrap; }
.page-title     { font-size: 22px; font-weight: 700; color: #1e293b; margin: 0 0 4px; }
.page-subtitle  { font-size: 13px; color: #64748b; margin: 0; }
.filters-row    { display: flex; gap: 10px; margin-bottom: 14px; }
.categories-grid { display: flex; flex-direction: column; gap: 8px; }
.table-loading   { padding: 40px; text-align: center; color: #94a3b8; }
.empty-state     { text-align: center; color: #94a3b8; padding: 40px; background: #fff; border-radius: 14px; }
.cat-card { background: #fff; border-radius: 12px; padding: 14px 16px; box-shadow: 0 1px 4px rgba(0,0,0,.07); display: flex; align-items: center; gap: 14px; }
.cat-icon { width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.cat-info { flex: 1; font-size: 14px; color: #1e293b; }
.sub-text { font-size: 12px; color: #94a3b8; margin-top: 2px; }
.cat-actions { display: flex; gap: 4px; }
.preview-cat { display: flex; align-items: center; gap: 12px; background: #f8fafc; border-radius: 10px; padding: 12px 16px; font-size: 14px; color: #1e293b; }
.hint { font-size: 11px; color: #94a3b8; margin-top: 2px; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 2000; padding: 16px; }
.modal-box     { background: #fff; border-radius: 16px; width: 100%; max-width: 440px; max-height: 90vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,.2); }
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
.btn-outline-primary { background: #eff6ff; color: #1d4ed8; border: 1.5px solid #bfdbfe; }
.btn-outline-danger  { background: #fff5f5; color: #dc2626; border: 1.5px solid #fecaca; }
.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
</style>
