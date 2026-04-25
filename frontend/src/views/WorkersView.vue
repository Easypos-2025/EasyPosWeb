<template>
  <div class="p-3">

    <!-- FILTROS + ACCIONES -->
    <div class="card p-3 mt-3">
      <div class="row g-2 align-items-end">
        <div class="col-md-4 col-12">
          <input type="text" class="form-control" placeholder="Buscar ejecutor..."
            v-model="search" />
        </div>
        <div class="col-md-3 col-6">
          <select class="form-select" v-model="filterProfession">
            <option value="">Todas las profesiones</option>
            <option v-for="p in professions" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
        </div>
        <div class="col-md-5 col-6 d-flex justify-content-end gap-2">
          <button class="btn btn-outline-secondary btn-sm" @click="openProfModal">
            <i class="bi bi-briefcase"></i> Profesiones
          </button>
          <button class="btn btn-primary" @click="openCreate">
            <i class="bi bi-person-plus-fill"></i> Nuevo ejecutor
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
            <th>Profesión</th>
            <th>Teléfono</th>
            <th style="width:120px" class="text-center">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="w in filtered" :key="w.id">
            <td class="text-muted">{{ w.id }}</td>
            <td><strong>{{ w.name }}</strong></td>
            <td>
              <span v-if="w.profession_name" class="prof-badge">{{ w.profession_name }}</span>
              <span v-else class="text-muted">—</span>
            </td>
            <td class="text-muted">{{ w.phone || '—' }}</td>
            <td class="text-center">
              <div class="d-flex gap-1 justify-content-center">
                <button class="btn btn-warning btn-sm" @click="openEdit(w)">
                  <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-danger btn-sm" @click="handleDelete(w)">
                  <i class="bi bi-trash"></i>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="filtered.length === 0">
            <td colspan="5" class="text-center text-muted py-4">
              <i class="bi bi-person-x" style="font-size:28px;display:block;margin-bottom:8px"></i>
              No hay ejecutores con estos filtros
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- MODAL CREAR / EDITAR EJECUTOR -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-box">
        <div class="modal-header-bar">
          <h2>{{ editForm.id ? 'Editar ejecutor' : 'Nuevo ejecutor' }}</h2>
          <button class="btn-close-sm" @click="closeModal"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-body-area">
          <div class="fg">
            <label>Nombre *</label>
            <input v-model="editForm.name" class="form-control"
              data-v="wname" @input="clearError" placeholder="Nombre completo" />
          </div>
          <div class="fg">
            <label>Profesión</label>
            <div class="d-flex gap-2">
              <select v-model="editForm.profession_id" class="form-select">
                <option :value="null">— Sin profesión —</option>
                <option v-for="p in professions" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
              <button type="button" class="btn btn-outline-secondary btn-sm flex-shrink-0"
                title="Agregar nueva profesión" @click="openProfModal">
                <i class="bi bi-plus-lg"></i>
              </button>
            </div>
          </div>
          <div class="fg">
            <label>Teléfono</label>
            <input v-model="editForm.phone" class="form-control" placeholder="Opcional" />
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

    <!-- MODAL GESTIÓN DE PROFESIONES -->
    <div v-if="showProfModal" class="modal-overlay" @click.self="showProfModal = false">
      <div class="modal-box">
        <div class="modal-header-bar">
          <h2><i class="bi bi-briefcase"></i> Profesiones / Oficios</h2>
          <button class="btn-close-sm" @click="showProfModal = false">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>
        <div class="modal-body-area">
          <!-- Formulario nueva profesión -->
          <div class="prof-form">
            <div class="row g-2">
              <div class="col-5">
                <input v-model="profForm.name" class="form-control form-control-sm"
                  placeholder="Nombre *" />
              </div>
              <div class="col-5">
                <input v-model="profForm.description" class="form-control form-control-sm"
                  placeholder="Descripción (opcional)" />
              </div>
              <div class="col-2">
                <button class="btn btn-primary btn-sm w-100" @click="saveProf"
                  :disabled="savingProf">
                  <i v-if="savingProf" class="bi bi-arrow-repeat spin"></i>
                  <i v-else class="bi bi-plus-lg"></i>
                </button>
              </div>
            </div>
          </div>

          <!-- Lista de profesiones -->
          <div class="prof-list mt-3">
            <div v-if="professions.length === 0" class="text-muted small text-center py-3">
              No hay profesiones registradas
            </div>
            <div v-for="p in professions" :key="p.id" class="prof-item">
              <div>
                <strong style="font-size:13px">{{ p.name }}</strong>
                <span v-if="p.description" class="text-muted ms-2" style="font-size:12px">
                  {{ p.description }}
                </span>
              </div>
              <button class="btn btn-danger btn-sm py-0 px-2" @click="deleteProf(p)"
                title="Eliminar">
                <i class="bi bi-trash" style="font-size:11px"></i>
              </button>
            </div>
          </div>
        </div>
        <div class="modal-footer-bar">
          <button class="btn btn-secondary" @click="showProfModal = false">Cerrar</button>
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

const workers     = ref([])
const professions = ref([])
const loading     = ref(true)
const saving      = ref(false)
const savingProf  = ref(false)
const showModal     = ref(false)
const showProfModal = ref(false)
const search          = ref("")
const filterProfession = ref("")

const editForm = ref({})
const profForm = ref({ name: "", description: "" })

// ── Filtrado ─────────────────────────────────────────────────────
const filtered = computed(() =>
  workers.value.filter(w => {
    const matchSearch = !search.value ||
      w.name.toLowerCase().includes(search.value.toLowerCase())
    const matchProf = !filterProfession.value ||
      w.profession_id === filterProfession.value
    return matchSearch && matchProf
  })
)

// ── Carga ────────────────────────────────────────────────────────
async function load() {
  loading.value = true
  try {
    const [wRes, pRes] = await Promise.all([
      api.get("/workers/"),
      api.get("/professions/"),
    ])
    workers.value     = wRes.data
    professions.value = pRes.data
  } catch {
    showToast("Error cargando datos", "error")
  } finally {
    loading.value = false
  }
}

// ── CRUD Ejecutores ───────────────────────────────────────────────
function openCreate() {
  editForm.value = { id: null, name: "", profession_id: null, phone: "" }
  showModal.value = true
}

function openEdit(w) {
  editForm.value = { id: w.id, name: w.name, profession_id: w.profession_id, phone: w.phone || "" }
  showModal.value = true
}

function closeModal() {
  document.querySelectorAll(".field-invalid").forEach(el => el.classList.remove("field-invalid"))
  showModal.value = false
}

function clearError(e) { e.target.classList.remove("field-invalid") }

async function save() {
  const check = validateForm([
    { value: editForm.value.name, selector: '[data-v="wname"]', label: "Nombre" }
  ])
  if (!check.valid) { showToast(check.message, "warning"); return }

  saving.value = true
  try {
    if (editForm.value.id) {
      await api.put(`/workers/${editForm.value.id}`, editForm.value)
      showToast("Ejecutor actualizado", "success")
    } else {
      await api.post("/workers/", editForm.value)
      showToast("Ejecutor creado", "success")
    }
    closeModal()
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error guardando ejecutor", "error")
  } finally {
    saving.value = false
  }
}

async function handleDelete(w) {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar "${w.name}"?`,
    text: "Esta acción no se puede deshacer.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, eliminar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/workers/${w.id}`)
    showToast("Ejecutor eliminado", "success")
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error eliminando ejecutor", "error")
  }
}

// ── CRUD Profesiones ─────────────────────────────────────────────
function openProfModal() {
  profForm.value = { name: "", description: "" }
  showProfModal.value = true
}

async function saveProf() {
  if (!profForm.value.name.trim()) {
    showToast("El nombre es obligatorio", "warning"); return
  }
  savingProf.value = true
  try {
    await api.post("/professions/", profForm.value)
    showToast("Profesión creada", "success")
    profForm.value = { name: "", description: "" }
    const res = await api.get("/professions/")
    professions.value = res.data
  } catch (e) {
    showToast(e.response?.data?.detail || "Error creando profesión", "error")
  } finally {
    savingProf.value = false
  }
}

async function deleteProf(p) {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar "${p.name}"?`,
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Eliminar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/professions/${p.id}`)
    showToast("Profesión eliminada", "success")
    const res = await api.get("/professions/")
    professions.value = res.data
  } catch (e) {
    showToast(e.response?.data?.detail || "Error eliminando profesión", "error")
  }
}

onMounted(load)
</script>

<style scoped>
.prof-badge {
  background: #eff6ff; color: #1e40af;
  font-size: 12px; font-weight: 600;
  padding: 2px 10px; border-radius: 20px;
}

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

.prof-form { background: #f8fafc; border-radius: 10px; padding: 12px; border: 1px solid #e2e8f0; }
.prof-list { display: flex; flex-direction: column; gap: 6px; max-height: 260px; overflow-y: auto; }
.prof-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 10px; background: #fff; border: 1px solid #f1f5f9; border-radius: 8px; }
.prof-item:hover { background: #f8fafc; }

.spin { display: inline-block; animation: spin 0.8s linear infinite; }
@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }
</style>
