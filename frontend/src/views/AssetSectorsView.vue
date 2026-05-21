<template>
  <div class="crud-container">
    <div class="crud-header">
      <div>
        <h2 class="crud-title"><i class="bi bi-geo-alt-fill me-2 text-primary"></i>{{ moduleName }}</h2>
        <p class="crud-subtitle">Zonas geográficas para clasificar activos</p>
      </div>
      <button class="btn-new" @click="openNew"><i class="bi bi-plus-lg me-1"></i>Nuevo sector</button>
    </div>

    <div class="table-wrap">
      <div v-if="loading" class="t-loading"><div class="spinner-border text-primary"></div></div>
      <table v-else class="crud-table">
        <thead><tr><th>#</th><th>Nombre</th><th>Descripción</th><th>Orden</th><th>Activo</th><th></th></tr></thead>
        <tbody>
          <tr v-for="s in sectors" :key="s.id">
            <td class="t-id">{{ s.id }}</td>
            <td class="t-name">{{ s.name }}</td>
            <td class="t-desc">{{ s.description || '—' }}</td>
            <td>{{ s.order_index }}</td>
            <td><span class="badge-status" :class="s.is_active ? 'b-yes' : 'b-no'">{{ s.is_active ? 'Sí' : 'No' }}</span></td>
            <td class="t-actions">
              <button class="icon-btn" @click="openEdit(s)"><i class="bi bi-pencil"></i></button>
              <button class="icon-btn del" @click="deleteSector(s)"><i class="bi bi-trash"></i></button>
            </td>
          </tr>
          <tr v-if="!loading && !sectors.length">
            <td colspan="6" class="t-empty">Sin sectores registrados</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal -->
    <teleport to="body">
      <div v-if="modal.open" class="modal-overlay" @click.self="closeModal">
        <div class="modal-box">
          <div class="modal-hdr">
            <span>{{ modal.id ? 'Editar sector' : 'Nuevo sector' }}</span>
            <button class="modal-close" @click="closeModal"><i class="bi bi-x-lg"></i></button>
          </div>
          <div class="modal-body">
            <div class="field">
              <label class="lbl">Nombre *</label>
              <input v-model="form.name" class="inp" placeholder="Ej: Norte, Centro, El Poblado…" />
            </div>
            <div class="field">
              <label class="lbl">Descripción</label>
              <input v-model="form.description" class="inp" placeholder="Detalle opcional" />
            </div>
            <div class="row2">
              <div class="field">
                <label class="lbl">Orden</label>
                <input v-model.number="form.order_index" type="number" class="inp" min="0" />
              </div>
              <div class="field">
                <label class="lbl">Activo</label>
                <select v-model="form.is_active" class="inp">
                  <option :value="1">Sí</option><option :value="0">No</option>
                </select>
              </div>
            </div>
          </div>
          <div class="modal-ftr">
            <button class="btn-cancel" @click="closeModal">Cancelar</button>
            <button class="btn-save" :disabled="saving" @click="save">
              <i v-if="saving" class="bi bi-arrow-repeat spin me-1"></i>
              {{ saving ? 'Guardando…' : 'Guardar' }}
            </button>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import { useModuleName } from "@/composables/useModuleName"

const { moduleName } = useModuleName()
const sectors = ref([])
const loading = ref(false)
const saving  = ref(false)
const modal   = ref({ open: false, id: null })
const form    = ref({ name: "", description: "", order_index: 0, is_active: 1 })

async function load() {
  loading.value = true
  try { const r = await api.get("/asset-sectors/all"); sectors.value = r.data }
  catch { sectors.value = [] }
  finally { loading.value = false }
}

function openNew()  { form.value = { name: "", description: "", order_index: 0, is_active: 1 }; modal.value = { open: true, id: null } }
function openEdit(s){ form.value = { ...s }; modal.value = { open: true, id: s.id } }
function closeModal(){ modal.value.open = false }

async function save() {
  if (!form.value.name.trim()) return showToast("El nombre es obligatorio", "warning")
  saving.value = true
  try {
    if (modal.value.id) await api.put(`/asset-sectors/${modal.value.id}`, form.value)
    else                await api.post("/asset-sectors/", form.value)
    showToast("Guardado", "success")
    closeModal()
    await load()
  } catch (e) { showToast(e.response?.data?.detail || "Error", "error") }
  finally { saving.value = false }
}

async function deleteSector(s) {
  const { isConfirmed } = await window.Swal.fire({
    title: "¿Eliminar sector?", text: `"${s.name}"`, icon: "warning",
    showCancelButton: true, confirmButtonText: "Sí, eliminar", confirmButtonColor: "#ef4444",
  })
  if (!isConfirmed) return
  try { await api.delete(`/asset-sectors/${s.id}`); showToast("Eliminado", "success"); await load() }
  catch (e) { showToast(e.response?.data?.detail || "Error", "error") }
}

load()
</script>

<style scoped>
.crud-container { padding: 20px; max-width: 760px; }
.crud-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 18px; flex-wrap: wrap; gap: 10px; }
.crud-title  { font-size: 18px; font-weight: 700; color: #1e293b; margin: 0; }
.crud-subtitle { font-size: 12px; color: #64748b; margin: 2px 0 0; }
.btn-new { background: #2563eb; color: #fff; border: none; border-radius: 8px; padding: 9px 18px; font-size: 13px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 4px; }
.btn-new:hover { background: #1d4ed8; }
.table-wrap { overflow-x: auto; }
.t-loading { display: flex; justify-content: center; padding: 40px; }
.crud-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.crud-table th { background: #f8fafc; color: #64748b; font-weight: 700; padding: 10px 12px; text-align: left; border-bottom: 2px solid #e2e8f0; white-space: nowrap; }
.crud-table td { padding: 10px 12px; border-bottom: 1px solid #f1f5f9; color: #1e293b; vertical-align: middle; }
.crud-table tr:hover td { background: #f8fafc; }
.t-id   { color: #94a3b8; font-size: 11px; }
.t-name { font-weight: 600; }
.t-desc { color: #64748b; }
.t-empty { text-align: center; color: #94a3b8; padding: 24px; }
.t-actions { display: flex; gap: 6px; }
.badge-status { font-size: 11px; font-weight: 700; border-radius: 20px; padding: 2px 8px; }
.b-yes { background: rgba(34,197,94,.12); color: #16a34a; }
.b-no  { background: rgba(239,68,68,.1);  color: #dc2626; }
.icon-btn { background: transparent; border: 1px solid #e2e8f0; color: #64748b; border-radius: 6px; padding: 4px 8px; cursor: pointer; font-size: 13px; transition: .15s; }
.icon-btn:hover { background: #eff6ff; color: #2563eb; border-color: #93c5fd; }
.icon-btn.del:hover { background: #fef2f2; color: #dc2626; border-color: #fca5a5; }
/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 9999; padding: 16px; }
.modal-box { background: #fff; border-radius: 14px; width: 100%; max-width: 440px; box-shadow: 0 20px 60px rgba(0,0,0,.15); }
.modal-hdr { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px 12px; border-bottom: 1px solid #f1f5f9; font-size: 15px; font-weight: 700; color: #1e293b; }
.modal-close { background: none; border: none; color: #94a3b8; font-size: 16px; cursor: pointer; }
.modal-close:hover { color: #ef4444; }
.modal-body { padding: 20px; display: flex; flex-direction: column; gap: 14px; }
.modal-ftr  { display: flex; justify-content: flex-end; gap: 10px; padding: 14px 20px 18px; border-top: 1px solid #f1f5f9; }
.field { display: flex; flex-direction: column; gap: 5px; }
.row2  { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.lbl   { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: .4px; }
.inp   { border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 12px; font-size: 13px; color: #1e293b; outline: none; transition: border-color .2s; background: #fff; }
.inp:focus { border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,.15); }
.btn-cancel { background: #f8fafc; color: #64748b; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 18px; font-size: 13px; cursor: pointer; }
.btn-save   { background: #2563eb; color: #fff; border: none; border-radius: 8px; padding: 8px 20px; font-size: 13px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 4px; }
.btn-save:hover:not(:disabled) { background: #1d4ed8; }
.btn-save:disabled { opacity: .5; cursor: not-allowed; }
.spin { animation: spin .7s linear infinite; }
@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }
@media (max-width: 768px) { .crud-container { padding: 14px; } .row2 { grid-template-columns: 1fr; } }
@media (max-width: 576px) { .crud-container { padding: 10px; } }
</style>
