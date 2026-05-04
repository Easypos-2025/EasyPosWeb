<template>
  <div class="page-container">

    <div class="page-header">
      <div>
        <h1 class="page-title"><i class="bi bi-rulers me-2"></i>Unidades de Medida</h1>
        <p class="page-subtitle">Catálogo de unidades usadas en materiales</p>
      </div>
      <button class="btn btn-primary" @click="openCreate">
        <i class="bi bi-plus-lg"></i> Agregar unidad
      </button>
    </div>

    <div class="search-bar">
      <i class="bi bi-search"></i>
      <input v-model="search" placeholder="Buscar unidad..." class="search-input" />
    </div>

    <div v-if="filtered.length === 0" class="empty-state">
      <i class="bi bi-rulers"></i>
      <p>{{ search ? 'Sin resultados para "' + search + '"' : 'No hay unidades registradas' }}</p>
      <button v-if="!search" class="btn btn-primary btn-sm" @click="openCreate">
        Agregar la primera unidad
      </button>
    </div>

    <div v-else class="sub-card p-0">
      <table class="data-table">
        <thead>
          <tr>
            <th>Nombre</th>
            <th class="text-center">Abreviatura</th>
            <th class="text-center">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filtered" :key="item.id">
            <td><strong>{{ item.name }}</strong></td>
            <td class="text-center">
              <span v-if="item.abreviatura" class="abr-chip">{{ item.abreviatura }}</span>
              <span v-else class="text-muted">—</span>
            </td>
            <td class="text-center">
              <div class="action-btns">
                <button class="btn btn-sm btn-outline-primary" @click="openEdit(item)" title="Editar">
                  <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" @click="remove(item)" title="Eliminar">
                  <i class="bi bi-trash"></i>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="modal" class="modal-overlay" @click.self="modal = false">
      <div class="modal-card">
        <div class="modal-header">
          <h3>{{ editing ? 'Editar unidad' : 'Nueva unidad' }}</h3>
          <button class="modal-close" @click="modal = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-body">
          <div class="fg">
            <label>Nombre *</label>
            <input v-model="form.name" class="form-control" placeholder="Ej: Kilogramo, Metro, Litro..." autofocus />
          </div>
          <div class="fg mt-3">
            <label>Abreviatura</label>
            <input v-model="form.abreviatura" class="form-control" placeholder="Ej: kg, m, lt" />
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

const items   = ref([])
const search  = ref("")
const modal   = ref(false)
const saving  = ref(false)
const editing = ref(null)
const form = ref({ name: "", abreviatura: "" })

const filtered = computed(() => {
  const q = search.value.toLowerCase()
  return items.value.filter(i =>
    i.name.toLowerCase().includes(q) || (i.abreviatura || "").toLowerCase().includes(q)
  )
})

async function load() {
  try {
    const res = await api.get("/unidades-medida/")
    items.value = res.data
  } catch {
    showToast("Error cargando unidades", "error")
  }
}

function openCreate() {
  editing.value = null
  form.value = { name: "", abreviatura: "" }
  modal.value = true
}

function openEdit(item) {
  editing.value = item
  form.value = { name: item.name, abreviatura: item.abreviatura || "" }
  modal.value = true
}

async function save() {
  if (!form.value.name.trim()) { showToast("El nombre es obligatorio", "warning"); return }
  saving.value = true
  try {
    if (editing.value) {
      const res = await api.put(`/unidades-medida/${editing.value.id}`, form.value)
      const idx = items.value.findIndex(i => i.id === editing.value.id)
      if (idx !== -1) items.value[idx] = res.data
      showToast("Unidad actualizada", "success")
    } else {
      const res = await api.post("/unidades-medida/", form.value)
      items.value.push(res.data)
      items.value.sort((a, b) => a.name.localeCompare(b.name))
      showToast("Unidad agregada", "success")
    }
    modal.value = false
  } catch (e) {
    showToast(e.response?.data?.detail || "Error guardando", "error")
  } finally {
    saving.value = false
  }
}

async function remove(item) {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar "${item.name}"?`,
    text: "Esta acción no se puede deshacer.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, eliminar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/unidades-medida/${item.id}`)
    items.value = items.value.filter(i => i.id !== item.id)
    showToast("Unidad eliminada", "success")
  } catch (e) {
    showToast(e.response?.data?.detail || "Error eliminando", "error")
  }
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 900px; }
.page-header    { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; gap: 12px; flex-wrap: wrap; }
.page-title     { font-size: 22px; font-weight: 700; color: #1e293b; margin: 0 0 4px; }
.page-subtitle  { font-size: 13px; color: #64748b; margin: 0; }

.search-bar     { display: flex; align-items: center; gap: 8px; background: #fff; border: 1.5px solid #e2e8f0; border-radius: 10px; padding: 8px 14px; margin-bottom: 16px; }
.search-bar .bi { color: #94a3b8; }
.search-input   { border: none; outline: none; flex: 1; font-size: 14px; color: #1e293b; background: transparent; }

.empty-state    { background: #fff; border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,.08); padding: 60px 24px; text-align: center; color: #94a3b8; display: flex; flex-direction: column; align-items: center; gap: 10px; }
.empty-state .bi { font-size: 40px; }
.empty-state p  { font-size: 14px; margin: 0; }

.sub-card     { background: #fff; border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,.08); margin-bottom: 16px; }
.sub-card.p-0 { padding: 0; overflow: hidden; }
.data-table   { width: 100%; border-collapse: collapse; font-size: 14px; }
.data-table th { background: #f8fafc; color: #475569; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: .4px; padding: 11px 14px; border-bottom: 1px solid #e2e8f0; }
.data-table td { padding: 12px 14px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: #f8fafc; }
.text-center  { text-align: center; }
.text-muted   { color: #94a3b8; font-size: 13px; }
.abr-chip     { background: #eff6ff; color: #1d4ed8; font-size: 12px; font-weight: 700; padding: 2px 10px; border-radius: 10px; }

.action-btns { display: flex; gap: 6px; justify-content: center; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 3000; padding: 16px; }
.modal-card    { background: #fff; border-radius: 14px; width: 100%; max-width: 440px; box-shadow: 0 20px 50px rgba(0,0,0,.2); overflow: hidden; }
.modal-header  { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid #f1f5f9; }
.modal-header h3 { font-size: 15px; font-weight: 700; color: #1e293b; margin: 0; }
.modal-close   { background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 14px; }
.modal-body    { padding: 20px; }
.modal-footer  { display: flex; justify-content: flex-end; gap: 8px; padding: 14px 20px; border-top: 1px solid #f1f5f9; }

.fg       { display: flex; flex-direction: column; gap: 4px; }
.fg label { font-size: 13px; font-weight: 600; color: #374151; }
.mt-3     { margin-top: 14px; }

.btn         { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; transition: all .15s; }
.btn-primary { background: #3b82f6; color: #fff; }
.btn-primary:hover { background: #2563eb; }
.btn-primary:disabled { opacity: .6; cursor: not-allowed; }
.btn-secondary { border: 1.5px solid #e2e8f0; background: #fff; color: #64748b; }
.btn-secondary:hover { border-color: #94a3b8; }
.btn-sm      { padding: 6px 12px; font-size: 12px; }
.btn-outline-primary { background: #eff6ff; color: #1d4ed8; border: 1.5px solid #bfdbfe; }
.btn-outline-primary:hover { background: #dbeafe; }
.btn-outline-danger  { background: #fef2f2; color: #b91c1c; border: 1.5px solid #fecaca; }
.btn-outline-danger:hover  { background: #fee2e2; }

.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
</style>
