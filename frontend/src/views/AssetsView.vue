<template>
  <div class="p-3">

    <!-- FILTROS -->
    <div class="card p-3 mt-3">
      <div class="row g-2 align-items-end">
        <div class="col-md-5 col-12">
          <input type="text" class="form-control" placeholder="Buscar activo..." v-model="search" />
        </div>
        <div class="col-md-4 col-6">
          <select class="form-select" v-model="filterCategory">
            <option value="">Todas las categorías</option>
            <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
        <div class="col-md-3 col-6 text-end">
          <button class="btn btn-primary" @click="openCreate">
            <i class="bi bi-plus-lg"></i> Nuevo activo
          </button>
        </div>
      </div>
    </div>

    <!-- TABLA -->
    <div class="card p-3 mt-3 table-responsive">
      <table class="table table-hover">
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Categoría</th>
            <th>Ubicación</th>
            <th>Descripción</th>
            <th style="width:120px">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in filtered" :key="a.id">
            <td>{{ a.name }}</td>
            <td>{{ categoryName(a.category_id) }}</td>
            <td>{{ a.location || '—' }}</td>
            <td class="text-truncate" style="max-width:220px">{{ a.description || '—' }}</td>
            <td>
              <button class="btn btn-warning btn-sm me-1" @click="openEdit(a)">
                <i class="bi bi-pencil"></i> Editar
              </button>
              <button class="btn btn-danger btn-sm" @click="handleDelete(a)">
                <i class="bi bi-trash"></i>
              </button>
            </td>
          </tr>
          <tr v-if="filtered.length === 0">
            <td colspan="5" class="text-center text-muted py-4">No hay resultados</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- MODAL CREAR / EDITAR -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-box">
        <div class="modal-header-bar">
          <h2>{{ editForm.id ? 'Editar activo' : 'Nuevo activo' }}</h2>
          <button class="btn-close-sm" @click="closeModal"><i class="bi bi-x-lg"></i></button>
        </div>

        <div class="modal-body-area">
          <div class="fg">
            <label>Nombre *</label>
            <input v-model="editForm.name" data-v="name" class="form-control" @input="clearError($event)" />
          </div>
          <div class="fg">
            <label>Categoría *</label>
            <select v-model="editForm.category_id" data-v="category" class="form-select" @change="clearError($event)">
              <option value="">— Seleccionar —</option>
              <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          <div class="fg">
            <label>Ubicación</label>
            <input v-model="editForm.location" class="form-control" />
          </div>
          <div class="fg">
            <label>Descripción</label>
            <textarea v-model="editForm.description" class="form-control" rows="3" />
          </div>
        </div>

        <div class="modal-footer-bar">
          <button class="btn btn-secondary" @click="closeModal">Cancelar</button>
          <button class="btn btn-primary" @click="save" :disabled="saving">
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
import { validateForm } from "@/utils/validate"

const assets     = ref([])
const categories = ref([])
const search          = ref("")
const filterCategory  = ref("")
const showModal  = ref(false)
const saving     = ref(false)
const editForm   = ref({})

const filtered = computed(() =>
  assets.value.filter(a => {
    const matchSearch   = (a.name || "").toLowerCase().includes(search.value.toLowerCase())
    const matchCategory = !filterCategory.value || a.category_id === filterCategory.value
    return matchSearch && matchCategory
  })
)

function categoryName(id) {
  return categories.value.find(c => c.id === id)?.name || "—"
}

async function load() {
  try {
    const [aRes, cRes] = await Promise.all([
      api.get("/assets/"),
      api.get("/asset-categories/"),
    ])
    assets.value     = aRes.data
    categories.value = cRes.data
  } catch {
    showToast("Error cargando activos", "error")
  }
}

function openCreate() {
  editForm.value = { id: null, name: "", category_id: "", location: "", description: "" }
  showModal.value = true
}

function openEdit(a) {
  editForm.value = { ...a }
  showModal.value = true
}

function closeModal() {
  document.querySelectorAll(".field-invalid").forEach(el => el.classList.remove("field-invalid"))
  showModal.value = false
}

function clearError(e) {
  e.target.classList.remove("field-invalid")
}

async function save() {
  const f = editForm.value
  const check = validateForm([
    { value: f.name,        selector: '[data-v="name"]',     label: "Nombre" },
    { value: f.category_id, selector: '[data-v="category"]', label: "Categoría" },
  ])
  if (!check.valid) { showToast(check.message, "warning"); return }

  saving.value = true
  try {
    if (f.id) {
      await api.put(`/assets/${f.id}`, f)
      showToast("Activo actualizado", "success")
    } else {
      await api.post("/assets/", f)
      showToast("Activo creado", "success")
    }
    closeModal()
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error guardando activo", "error")
  } finally {
    saving.value = false
  }
}

async function handleDelete(a) {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar "${a.name}"?`,
    text: "Esta acción no se puede deshacer.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, eliminar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/assets/${a.id}`)
    showToast("Activo eliminado", "success")
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error eliminando activo", "error")
  }
}

onMounted(load)
</script>

<style scoped>
.modal-overlay  { position: fixed; inset: 0; background: rgba(0,0,0,0.45); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-box      { background: #fff; border-radius: 16px; width: 520px; max-width: 95vw; max-height: 90vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
.modal-header-bar { display: flex; align-items: center; justify-content: space-between; padding: 18px 24px 14px; border-bottom: 1px solid #f1f5f9; flex-shrink: 0; }
.modal-header-bar h2 { font-size: 17px; font-weight: 700; color: #1e293b; margin: 0; }
.modal-body-area  { padding: 18px 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
.modal-footer-bar { padding: 14px 24px 18px; display: flex; justify-content: flex-end; gap: 10px; border-top: 1px solid #f1f5f9; flex-shrink: 0; }
.fg       { display: flex; flex-direction: column; gap: 4px; }
.fg label { font-size: 13px; font-weight: 500; color: #374151; }
.btn-close-sm { background: none; border: none; font-size: 18px; cursor: pointer; color: #94a3b8; border-radius: 6px; padding: 4px 8px; }
.btn-close-sm:hover { background: #f1f5f9; color: #1e293b; }
</style>
