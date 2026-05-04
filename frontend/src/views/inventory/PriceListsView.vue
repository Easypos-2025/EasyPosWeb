<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1 class="page-title"><i class="bi bi-currency-dollar me-2"></i>Listas de Precios</h1>
        <p class="page-subtitle">Define precios especiales por tipo de cliente o canal de venta</p>
      </div>
      <button class="btn btn-primary" @click="openCreate"><i class="bi bi-plus-lg"></i> Nueva lista</button>
    </div>

    <div class="lists-grid">
      <div v-if="loading" class="table-loading"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
      <template v-else>
        <div v-for="pl in priceLists" :key="pl.id" class="list-card" :class="{ 'list-default': pl.is_default }">
          <div class="list-card-header">
            <div class="list-name-block">
              <strong>{{ pl.name }}</strong>
              <span v-if="pl.is_default" class="badge-default">Predeterminada</span>
            </div>
            <div class="list-actions">
              <button class="btn btn-sm btn-outline-primary" @click="openEdit(pl)" title="Editar"><i class="bi bi-pencil"></i></button>
              <button v-if="!pl.is_default" class="btn btn-sm btn-outline-danger" @click="remove(pl)" title="Eliminar"><i class="bi bi-trash"></i></button>
              <button v-if="!pl.is_default" class="btn btn-sm btn-outline-secondary" @click="setDefault(pl)" title="Marcar como predeterminada">
                <i class="bi bi-star"></i>
              </button>
            </div>
          </div>
          <div v-if="pl.description" class="list-desc">{{ pl.description }}</div>
        </div>
        <div v-if="priceLists.length === 0" class="empty-state">
          No hay listas de precios.<br>Crea al menos una lista predeterminada para tus clientes.
        </div>
      </template>
    </div>

    <!-- MODAL -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-box">
        <div class="mh">
          <h3><i class="bi bi-currency-dollar me-2"></i>{{ editing ? 'Editar' : 'Nueva' }} Lista de Precios</h3>
          <button class="btn-x" @click="showModal = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="mb-area">
          <div class="fg">
            <label>Nombre *</label>
            <input v-model="form.name" class="form-control" placeholder="Ej: Lista Pública, Mayorista, Distribuidores" />
          </div>
          <div class="fg">
            <label>Descripción</label>
            <input v-model="form.description" class="form-control" placeholder="Descripción de cuándo aplicar esta lista..." />
          </div>
          <div class="toggle-row">
            <label class="toggle-label">
              <input type="checkbox" v-model="form.is_default" :true-value="1" :false-value="0" />
              <span>Lista predeterminada (aplica a clientes sin lista asignada)</span>
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
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

const priceLists = ref([])
const loading    = ref(true)
const showModal  = ref(false)
const editing    = ref(null)
const saving     = ref(false)
const form       = ref({})

async function load() {
  loading.value = true
  try { priceLists.value = (await api.get("/price-lists/")).data }
  catch { showToast("Error cargando listas", "error") }
  finally { loading.value = false }
}

function openCreate() {
  editing.value = null
  form.value = { name: "", description: "", is_default: priceLists.value.length === 0 ? 1 : 0 }
  showModal.value = true
}

function openEdit(pl) {
  editing.value = pl
  form.value = { ...pl }
  showModal.value = true
}

async function submit() {
  if (!form.value.name?.trim()) { showToast("El nombre es requerido", "warning"); return }
  saving.value = true
  try {
    if (editing.value) {
      const r = await api.put(`/price-lists/${editing.value.id}`, form.value)
      await load()
    } else {
      await api.post("/price-lists/", form.value)
      await load()
    }
    showModal.value = false
    showToast("Lista guardada", "success")
  } catch (e) { showToast(e.response?.data?.detail || "Error", "error") }
  finally { saving.value = false }
}

async function remove(pl) {
  const { isConfirmed } = await window.Swal.fire({
    title: "¿Eliminar lista?", text: `"${pl.name}" dejará de estar disponible.`,
    icon: "warning", showCancelButton: true, confirmButtonText: "Sí, eliminar", cancelButtonText: "Cancelar"
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/price-lists/${pl.id}`)
    await load()
    showToast("Lista eliminada", "success")
  } catch (e) { showToast(e.response?.data?.detail || "Error", "error") }
}

async function setDefault(pl) {
  try {
    await api.put(`/price-lists/${pl.id}`, { ...pl, is_default: 1 })
    await load()
    showToast(`"${pl.name}" es ahora la lista predeterminada`, "success")
  } catch (e) { showToast(e.response?.data?.detail || "Error", "error") }
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 800px; }
.page-header    { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; gap: 12px; flex-wrap: wrap; }
.page-title     { font-size: 22px; font-weight: 700; color: #1e293b; margin: 0 0 4px; }
.page-subtitle  { font-size: 13px; color: #64748b; margin: 0; }
.lists-grid  { display: flex; flex-direction: column; gap: 10px; }
.table-loading { padding: 40px; text-align: center; color: #94a3b8; }
.empty-state   { text-align: center; color: #94a3b8; padding: 40px; background: #fff; border-radius: 14px; line-height: 1.8; }
.list-card { background: #fff; border-radius: 12px; padding: 16px 20px; box-shadow: 0 1px 4px rgba(0,0,0,.07); border-left: 4px solid #e2e8f0; }
.list-default  { border-left-color: #3b82f6; }
.list-card-header { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
.list-name-block  { display: flex; align-items: center; gap: 8px; }
.list-name-block strong { font-size: 14px; color: #1e293b; }
.badge-default { font-size: 10px; font-weight: 700; background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 20px; }
.list-desc { font-size: 12px; color: #94a3b8; margin-top: 6px; }
.list-actions { display: flex; gap: 4px; }
.toggle-row { display: flex; align-items: flex-start; }
.toggle-label { display: flex; align-items: flex-start; gap: 8px; cursor: pointer; font-size: 13px; color: #374151; line-height: 1.5; }
.toggle-label input[type=checkbox] { width: 16px; height: 16px; cursor: pointer; margin-top: 2px; flex-shrink: 0; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 2000; padding: 16px; }
.modal-box     { background: #fff; border-radius: 16px; width: 100%; max-width: 440px; max-height: 90vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,.2); }
.mh  { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid #f1f5f9; }
.mh h3 { font-size: 15px; font-weight: 700; color: #1e293b; margin: 0; }
.btn-x { background: none; border: none; font-size: 16px; cursor: pointer; color: #94a3b8; }
.mb-area { padding: 18px 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; }
.mf { padding: 12px 20px 16px; display: flex; justify-content: flex-end; gap: 8px; border-top: 1px solid #f1f5f9; }
.fg       { display: flex; flex-direction: column; gap: 4px; }
.fg label { font-size: 13px; font-weight: 600; color: #374151; }
.btn { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; transition: all .15s; }
.btn-primary   { background: #3b82f6; color: #fff; } .btn-primary:hover { background: #2563eb; }
.btn-primary:disabled { opacity: .6; cursor: not-allowed; }
.btn-secondary { border: 1.5px solid #e2e8f0; background: #fff; color: #64748b; }
.btn-sm { padding: 6px 12px; font-size: 12px; }
.btn-outline-primary   { background: #eff6ff; color: #1d4ed8; border: 1.5px solid #bfdbfe; }
.btn-outline-danger    { background: #fff5f5; color: #dc2626; border: 1.5px solid #fecaca; }
.btn-outline-secondary { background: #f8fafc; color: #475569; border: 1.5px solid #e2e8f0; }
.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
</style>
