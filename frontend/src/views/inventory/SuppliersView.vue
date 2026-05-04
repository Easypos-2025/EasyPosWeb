<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1 class="page-title"><i class="bi bi-truck me-2"></i>Proveedores</h1>
        <p class="page-subtitle">Empresas o personas que suministran insumos y productos</p>
      </div>
      <button class="btn btn-primary" @click="openCreate"><i class="bi bi-plus-lg"></i> Nuevo proveedor</button>
    </div>

    <div class="filters-row">
      <input v-model="search" class="form-control" placeholder="Buscar por nombre o NIT..." style="max-width:280px" />
    </div>

    <div class="table-card">
      <div v-if="loading" class="table-loading"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Nombre</th>
            <th>NIT</th>
            <th>Contacto</th>
            <th>Teléfono</th>
            <th>Email</th>
            <th class="text-center">Estado</th>
            <th class="text-center">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in filtered" :key="s.id">
            <td class="text-muted">{{ s.id }}</td>
            <td><strong>{{ s.name }}</strong></td>
            <td class="text-muted">{{ s.nit || '—' }}</td>
            <td>{{ s.contact_name || '—' }}</td>
            <td>{{ s.phone || '—' }}</td>
            <td>{{ s.email || '—' }}</td>
            <td class="text-center">
              <span class="badge-status" :class="s.is_active ? 'active' : 'inactive'">
                {{ s.is_active ? 'Activo' : 'Inactivo' }}
              </span>
            </td>
            <td class="text-center">
              <div class="action-row">
                <button class="btn btn-sm btn-outline-primary" @click="openEdit(s)" title="Editar"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-sm btn-outline-danger" @click="toggleActive(s)" :title="s.is_active ? 'Desactivar' : 'Activar'">
                  <i :class="s.is_active ? 'bi bi-toggle-on' : 'bi bi-toggle-off'"></i>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="filtered.length === 0">
            <td colspan="8" class="text-center text-muted py-4">No hay proveedores registrados</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- MODAL -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-box">
        <div class="mh">
          <h3><i class="bi bi-truck me-2"></i>{{ editing ? 'Editar' : 'Nuevo' }} Proveedor</h3>
          <button class="btn-x" @click="showModal = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="mb-area">
          <div class="form-row2">
            <div class="fg">
              <label>Nombre / Empresa *</label>
              <input v-model="form.name" class="form-control" placeholder="Nombre del proveedor" />
            </div>
            <div class="fg">
              <label>NIT / Documento</label>
              <input v-model="form.nit" class="form-control" placeholder="900.123.456-7" />
            </div>
          </div>
          <div class="form-row2">
            <div class="fg">
              <label>Persona de contacto</label>
              <input v-model="form.contact_name" class="form-control" placeholder="Nombre del contacto" />
            </div>
            <div class="fg">
              <label>Teléfono</label>
              <input v-model="form.phone" class="form-control" placeholder="300 000 0000" />
            </div>
          </div>
          <div class="fg">
            <label>Email</label>
            <input v-model="form.email" class="form-control" type="email" placeholder="proveedor@empresa.com" />
          </div>
          <div class="fg">
            <label>Dirección</label>
            <input v-model="form.address" class="form-control" placeholder="Dirección del proveedor" />
          </div>
          <div class="fg">
            <label>Notas</label>
            <textarea v-model="form.notes" class="form-control" rows="2" placeholder="Observaciones adicionales..."></textarea>
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

const suppliers = ref([])
const loading   = ref(true)
const search    = ref("")
const showModal = ref(false)
const editing   = ref(null)
const saving    = ref(false)
const form      = ref({})

const filtered = computed(() => {
  const q = search.value.toLowerCase()
  return suppliers.value.filter(s =>
    !q || s.name.toLowerCase().includes(q) || (s.nit || "").toLowerCase().includes(q)
  )
})

async function load() {
  loading.value = true
  try { suppliers.value = (await api.get("/suppliers/")).data }
  catch { showToast("Error cargando proveedores", "error") }
  finally { loading.value = false }
}

function openCreate() {
  editing.value = null
  form.value = { name: "", nit: "", contact_name: "", phone: "", email: "", address: "", notes: "" }
  showModal.value = true
}

function openEdit(s) {
  editing.value = s
  form.value = { ...s }
  showModal.value = true
}

async function submit() {
  if (!form.value.name?.trim()) { showToast("El nombre es requerido", "warning"); return }
  saving.value = true
  try {
    if (editing.value) {
      const r = await api.put(`/suppliers/${editing.value.id}`, form.value)
      const idx = suppliers.value.findIndex(s => s.id === editing.value.id)
      if (idx !== -1) suppliers.value[idx] = r.data
    } else {
      const r = await api.post("/suppliers/", form.value)
      suppliers.value.unshift(r.data)
    }
    showModal.value = false
    showToast("Proveedor guardado", "success")
  } catch (e) { showToast(e.response?.data?.detail || "Error guardando", "error") }
  finally { saving.value = false }
}

async function toggleActive(s) {
  try {
    const r = await api.put(`/suppliers/${s.id}`, { is_active: s.is_active ? 0 : 1 })
    const idx = suppliers.value.findIndex(x => x.id === s.id)
    if (idx !== -1) suppliers.value[idx] = r.data
  } catch { showToast("Error actualizando", "error") }
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1100px; }
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
.text-muted  { color: #94a3b8; font-size: 12px; }
.py-4        { padding: 32px 0; }
.badge-status { font-size: 10px; font-weight: 700; padding: 2px 9px; border-radius: 20px; }
.badge-status.active   { background: #dcfce7; color: #16a34a; }
.badge-status.inactive { background: #f1f5f9; color: #94a3b8; }
.action-row  { display: flex; gap: 4px; justify-content: center; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 2000; padding: 16px; }
.modal-box     { background: #fff; border-radius: 16px; width: 100%; max-width: 520px; max-height: 90vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,.2); }
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
@media (max-width: 640px) { .form-row2 { grid-template-columns: 1fr; } }
</style>
