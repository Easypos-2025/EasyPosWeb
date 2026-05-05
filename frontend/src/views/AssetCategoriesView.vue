<template>
  <div class="p-3">

    <!-- KPI -->
    <div class="kpi-bar">
      <div class="kpi-card">
        <i class="bi bi-tags-fill kpi-icon"></i>
        <div class="kpi-body">
          <span class="kpi-value">{{ categories.length }}</span>
          <span class="kpi-label">{{ moduleName }}</span>
        </div>
      </div>
    </div>

    <!-- FILTROS + ACCIONES -->
    <div class="card p-3 mt-3">
      <div class="row g-2 align-items-end">
        <div class="col-md-8 col-12">
          <input
            type="text"
            class="form-control"
            :placeholder="`Buscar ${moduleName}...`"
            v-model="search"
          />
        </div>
        <div class="col-md-4 col-12 d-flex justify-content-end">
          <button class="btn btn-primary" @click="openCreate">
            <i class="bi bi-plus-lg"></i> Nuevo {{ moduleName }}
          </button>
        </div>
      </div>
    </div>

    <!-- TABLA -->
    <div class="card p-3 mt-3 table-responsive">
      <div v-if="loading" class="text-center text-muted py-4">
        <i class="bi bi-arrow-repeat spin"></i> Cargando...
      </div>
      <table v-else class="table table-hover mb-0">
        <thead class="table-light">
          <tr>
            <th>#</th>
            <th>Nombre</th>
            <th>Descripción</th>
            <th>{{ assetModuleName }}</th>
            <th style="width:110px" class="text-center">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="cat in filtered" :key="cat.id">
            <td class="text-muted">{{ cat.id }}</td>
            <td>
              <span class="cat-badge">
                <i class="bi bi-tag-fill"></i> {{ cat.name }}
              </span>
            </td>
            <td class="text-muted">{{ cat.description || '—' }}</td>
            <td>
              <span class="asset-count">{{ cat.asset_count ?? '—' }}</span>
            </td>
            <td class="text-center">
              <div class="d-flex gap-1 justify-content-center">
                <button class="btn btn-warning btn-sm" @click="openEdit(cat)" title="Editar">
                  <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-danger btn-sm" @click="handleDelete(cat)" title="Eliminar">
                  <i class="bi bi-trash"></i>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="filtered.length === 0">
            <td colspan="5" class="text-center text-muted py-4">
              <i class="bi bi-tags" style="font-size:28px;display:block;margin-bottom:8px"></i>
              No hay {{ moduleName }}{{ search ? ' con ese filtro' : '' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- MODAL CREAR / EDITAR -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-box">
        <div class="modal-header-bar">
          <h2>{{ form.id ? `Editar ${moduleName}` : `Nuevo ${moduleName}` }}</h2>
          <button class="btn-close-sm" @click="closeModal">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>
        <div class="modal-body-area">
          <div class="fg">
            <label>Nombre *</label>
            <input
              v-model="form.name"
              class="form-control"
              data-v="catname"
              @input="clearError"
              placeholder="Ej: Maquinaria, Vehículos, Equipos de cómputo"
            />
          </div>
          <div class="fg">
            <label>Descripción <span class="opt">(opcional)</span></label>
            <textarea
              v-model="form.description"
              class="form-control"
              rows="3"
              placeholder="Descripción breve de la categoría"
            ></textarea>
          </div>
        </div>
        <div class="modal-footer-bar">
          <button class="btn btn-secondary" @click="closeModal">Cancelar</button>
          <button class="btn btn-primary" @click="save" :disabled="saving">
            <i v-if="saving" class="bi bi-arrow-repeat spin"></i>
            {{ saving ? 'Guardando...' : (form.id ? 'Actualizar' : 'Crear') }}
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
import { useModuleName } from "@/composables/useModuleName"

const { moduleName }                  = useModuleName()
const { moduleName: assetModuleName } = useModuleName("/configuration/assets")

const categories = ref([])
const loading    = ref(true)
const saving     = ref(false)
const showModal  = ref(false)
const search     = ref("")

const form = ref({ id: null, name: "", description: "" })

const filtered = computed(() =>
  categories.value.filter(c =>
    !search.value ||
    c.name.toLowerCase().includes(search.value.toLowerCase()) ||
    (c.description || "").toLowerCase().includes(search.value.toLowerCase())
  )
)

async function load() {
  loading.value = true
  try {
    const res = await api.get("/asset-categories/")
    categories.value = res.data
  } catch {
    showToast("Error cargando categorías", "error")
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.value = { id: null, name: "", description: "" }
  showModal.value = true
}

function openEdit(cat) {
  form.value = { id: cat.id, name: cat.name, description: cat.description || "" }
  showModal.value = true
}

function closeModal() {
  document.querySelectorAll(".field-invalid").forEach(el => el.classList.remove("field-invalid"))
  showModal.value = false
}

function clearError(e) { e.target.classList.remove("field-invalid") }

async function save() {
  const check = validateForm([
    { value: form.value.name, selector: '[data-v="catname"]', label: "Nombre" }
  ])
  if (!check.valid) { showToast(check.message, "warning"); return }

  saving.value = true
  try {
    if (form.value.id) {
      await api.put(`/asset-categories/${form.value.id}`, form.value)
      showToast("Categoría actualizada", "success")
    } else {
      await api.post("/asset-categories/", form.value)
      showToast("Categoría creada", "success")
    }
    closeModal()
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error guardando categoría", "error")
  } finally {
    saving.value = false
  }
}

async function handleDelete(cat) {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar "${cat.name}"?`,
    text: "Los activos con esta categoría quedarán sin categorizar.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, eliminar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/asset-categories/${cat.id}`)
    showToast("Categoría eliminada", "success")
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error eliminando categoría", "error")
  }
}

onMounted(load)
</script>

<style scoped>
/* KPI bar */
.kpi-bar {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 4px;
}
.kpi-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #fff;
  border-radius: 12px;
  padding: 14px 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.07);
  min-width: 160px;
}
.kpi-icon { font-size: 26px; color: #3b82f6; }
.kpi-body { display: flex; flex-direction: column; line-height: 1.2; }
.kpi-value { font-size: 22px; font-weight: 800; color: #1e293b; }
.kpi-label { font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.4px; }

/* Badges */
.cat-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: #eff6ff;
  color: #1e40af;
  font-size: 12px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 20px;
}
.cat-badge .bi { font-size: 11px; }

.asset-count {
  display: inline-block;
  background: #f0fdf4;
  color: #166534;
  font-size: 12px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 12px;
}

/* Modal */
.modal-overlay  { position: fixed; inset: 0; background: rgba(0,0,0,0.45); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-box      { background: #fff; border-radius: 16px; width: 480px; max-width: 95vw; max-height: 90vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
.modal-header-bar { display: flex; align-items: center; justify-content: space-between; padding: 18px 24px 14px; border-bottom: 1px solid #f1f5f9; flex-shrink: 0; }
.modal-header-bar h2 { font-size: 17px; font-weight: 700; color: #1e293b; margin: 0; }
.modal-body-area  { padding: 18px 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; }
.modal-footer-bar { padding: 14px 24px 18px; display: flex; justify-content: flex-end; gap: 10px; border-top: 1px solid #f1f5f9; flex-shrink: 0; }
.fg       { display: flex; flex-direction: column; gap: 4px; }
.fg label { font-size: 13px; font-weight: 500; color: #374151; }
.opt      { font-weight: 400; color: #94a3b8; }
.btn-close-sm { background: none; border: none; font-size: 18px; cursor: pointer; color: #94a3b8; border-radius: 6px; padding: 4px 8px; }
.btn-close-sm:hover { background: #f1f5f9; color: #1e293b; }

.spin { display: inline-block; animation: spin 0.8s linear infinite; }
@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }
</style>
