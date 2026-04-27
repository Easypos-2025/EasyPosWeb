<template>
  <div class="page-container">

    <!-- ENCABEZADO -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Clientes</h1>
        <p class="page-subtitle">Total: <strong>{{ clients.length }}</strong> clientes registrados</p>
      </div>
      <button class="btn btn-primary" @click="openCreate">
        <i class="bi bi-plus-lg"></i> Nuevo cliente
      </button>
    </div>

    <!-- FILTROS -->
    <div class="filters-row">
      <input v-model="search" class="form-control" placeholder="Buscar por nombre, documento..." style="max-width:300px" />
      <select v-model="filterActive" class="form-select" style="max-width:160px">
        <option value="">Todos</option>
        <option value="1">Activos</option>
        <option value="0">Inactivos</option>
      </select>
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
            <th>Documento</th>
            <th>Email</th>
            <th>Teléfono</th>
            <th>Dirección</th>
            <th class="text-center">Estado</th>
            <th class="text-center">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in filtered" :key="c.id">
            <td class="text-muted">{{ c.id }}</td>
            <td><strong>{{ c.name }}</strong></td>
            <td class="text-muted">
              <span v-if="c.document_type || c.document_number">
                {{ c.document_type }} {{ c.document_number }}
              </span>
              <span v-else>—</span>
            </td>
            <td class="text-muted">{{ c.email || '—' }}</td>
            <td class="text-muted">{{ c.phone || '—' }}</td>
            <td class="text-muted text-truncate" style="max-width:180px">{{ c.address || '—' }}</td>
            <td class="text-center">
              <span class="status-badge" :class="c.is_active ? 'badge-activo' : 'badge-inactivo'">
                {{ c.is_active ? 'Activo' : 'Inactivo' }}
              </span>
            </td>
            <td class="text-center">
              <div class="d-flex gap-1 justify-content-center">
                <button class="btn btn-warning btn-sm" @click="openEdit(c)" title="Editar">
                  <i class="bi bi-pencil"></i> Editar
                </button>
                <button class="btn btn-danger btn-sm" @click="handleDelete(c)" title="Eliminar">
                  <i class="bi bi-trash"></i>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="filtered.length === 0">
            <td colspan="8" class="text-center text-muted py-4">
              <i class="bi bi-people" style="font-size:28px;display:block;margin-bottom:8px"></i>
              No hay clientes con estos filtros
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- MODAL CREAR / EDITAR -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-box">
        <div class="modal-header-bar">
          <h2>{{ form.id ? 'Editar cliente' : 'Nuevo cliente' }}</h2>
          <button class="btn-close-x" @click="closeModal"><i class="bi bi-x-lg"></i></button>
        </div>

        <div class="modal-body-area">

          <!-- Nombre -->
          <div class="fg full">
            <label>Nombre / Razón Social *</label>
            <input v-model="form.name" data-v="name" class="form-control"
              placeholder="Nombre del cliente o empresa" @input="clearError" />
          </div>

          <div class="form-row2">
            <!-- Tipo documento -->
            <div class="fg">
              <label>Tipo de documento</label>
              <select v-model="form.document_type" class="form-select">
                <option :value="null">— Sin documento —</option>
                <option value="NIT">NIT</option>
                <option value="CC">Cédula de Ciudadanía</option>
                <option value="CE">Cédula de Extranjería</option>
                <option value="Pasaporte">Pasaporte</option>
              </select>
            </div>

            <!-- Número documento -->
            <div class="fg">
              <label>Número de documento</label>
              <input v-model="form.document_number" class="form-control" placeholder="Ej: 900123456-1" />
            </div>
          </div>

          <div class="form-row2">
            <!-- Email -->
            <div class="fg">
              <label>Correo electrónico</label>
              <input v-model="form.email" type="email" class="form-control" placeholder="correo@ejemplo.com" />
            </div>

            <!-- Teléfono -->
            <div class="fg">
              <label>Teléfono</label>
              <input v-model="form.phone" class="form-control" placeholder="Ej: 3001234567" />
            </div>
          </div>

          <!-- Dirección -->
          <div class="fg full">
            <label>Dirección</label>
            <input v-model="form.address" class="form-control" placeholder="Dirección completa" />
          </div>

          <!-- Estado (solo al editar) -->
          <div v-if="form.id" class="fg full">
            <label>Estado</label>
            <div class="d-flex gap-3 mt-1">
              <label class="d-flex align-items-center gap-2 cursor-pointer">
                <input type="radio" v-model="form.is_active" :value="1" /> Activo
              </label>
              <label class="d-flex align-items-center gap-2 cursor-pointer">
                <input type="radio" v-model="form.is_active" :value="0" /> Inactivo
              </label>
            </div>
          </div>

        </div>

        <div class="modal-footer-bar">
          <button class="btn btn-secondary" @click="closeModal">Cancelar</button>
          <button class="btn btn-primary" @click="save" :disabled="saving">
            <i v-if="saving" class="bi bi-arrow-repeat spin"></i>
            {{ saving ? 'Guardando...' : 'Guardar cliente' }}
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

const clients    = ref([])
const loading    = ref(true)
const saving     = ref(false)
const showModal  = ref(false)
const search     = ref("")
const filterActive = ref("")

const emptyForm = () => ({
  id: null, name: "", document_type: null, document_number: "",
  email: "", phone: "", address: "", is_active: 1
})
const form = ref(emptyForm())

const filtered = computed(() =>
  clients.value.filter(c => {
    const q = search.value.toLowerCase()
    const matchSearch = !q ||
      (c.name || "").toLowerCase().includes(q) ||
      (c.document_number || "").toLowerCase().includes(q) ||
      (c.email || "").toLowerCase().includes(q)
    const matchActive = filterActive.value === "" ||
      String(c.is_active) === filterActive.value
    return matchSearch && matchActive
  })
)

async function load() {
  loading.value = true
  try {
    const res = await api.get("/clients")
    clients.value = Array.isArray(res.data) ? res.data : []
  } catch {
    showToast("Error cargando clientes", "error")
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.value = emptyForm()
  showModal.value = true
}

function openEdit(c) {
  form.value = { ...c }
  showModal.value = true
}

function closeModal() {
  document.querySelectorAll(".field-invalid").forEach(el => el.classList.remove("field-invalid"))
  showModal.value = false
}

function clearError(e) {
  e.target?.classList.remove("field-invalid")
}

async function save() {
  const check = validateForm([
    { value: form.value.name, selector: '[data-v="name"]', label: "Nombre" },
  ])
  if (!check.valid) { showToast(check.message, "warning"); return }

  saving.value = true
  try {
    if (form.value.id) {
      await api.put(`/clients/${form.value.id}`, form.value)
      showToast("Cliente actualizado", "success")
    } else {
      await api.post("/clients", form.value)
      showToast("Cliente creado", "success")
    }
    closeModal()
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error guardando cliente", "error")
  } finally {
    saving.value = false
  }
}

async function handleDelete(c) {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar "${c.name}"?`,
    text: "Esta acción no se puede deshacer.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, eliminar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/clients/${c.id}`)
    showToast("Cliente eliminado", "success")
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error eliminando cliente", "error")
  }
}

onMounted(load)
</script>

<style scoped>
.page-container  { padding: 20px 24px; }
.page-header     { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 16px; }
.page-title      { font-size: 20px; font-weight: 700; color: #1e293b; margin: 0; }
.page-subtitle   { font-size: 13px; color: #64748b; margin: 2px 0 0; }
.filters-row     { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 14px; }

.table-card      { background: #fff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; }
.table-loading   { padding: 40px; text-align: center; color: #94a3b8; }
.data-table      { width: 100%; border-collapse: collapse; }
.data-table thead tr { background: #f8fafc; }
.data-table th   { padding: 10px 14px; font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.4px; border-bottom: 1px solid #e2e8f0; }
.data-table td   { padding: 10px 14px; font-size: 13px; color: #1e293b; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.data-table tbody tr:hover { background: #f8fafc; }
.text-muted      { color: #64748b !important; }
.text-truncate   { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.status-badge    { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }
.badge-activo    { background: #dcfce7; color: #15803d; }
.badge-inactivo  { background: #fee2e2; color: #b91c1c; }

.modal-overlay   { position: fixed; inset: 0; background: rgba(0,0,0,0.45); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-box       { background: #fff; border-radius: 16px; width: 580px; max-width: 95vw; max-height: 90vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
.modal-header-bar{ display: flex; align-items: center; justify-content: space-between; padding: 18px 24px 14px; border-bottom: 1px solid #f1f5f9; flex-shrink: 0; }
.modal-header-bar h2 { font-size: 17px; font-weight: 700; color: #1e293b; margin: 0; }
.modal-body-area { padding: 18px 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
.modal-footer-bar{ padding: 14px 24px 18px; display: flex; justify-content: flex-end; gap: 10px; border-top: 1px solid #f1f5f9; flex-shrink: 0; }

.fg              { display: flex; flex-direction: column; gap: 4px; }
.fg.full         { width: 100%; }
.fg label        { font-size: 13px; font-weight: 500; color: #374151; }
.form-row2       { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.btn-close-x     { background: none; border: none; font-size: 18px; cursor: pointer; color: #94a3b8; border-radius: 6px; padding: 4px 8px; }
.btn-close-x:hover { background: #f1f5f9; color: #1e293b; }
.cursor-pointer  { cursor: pointer; }

.spin { display:inline-block; animation: spin 0.8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

@media (max-width: 600px) {
  .form-row2 { grid-template-columns: 1fr; }
  .page-container { padding: 14px 12px; }
}
</style>
