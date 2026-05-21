<template>
  <div class="crud-container">
    <div class="crud-header">
      <div>
        <h2 class="crud-title"><i class="bi bi-card-text me-2 text-primary"></i>{{ moduleName }}</h2>
        <p class="crud-subtitle">Requisitos y observaciones generales para todos los activos</p>
      </div>
      <button class="btn-new" @click="openNew"><i class="bi bi-plus-lg me-1"></i>Nuevo ítem</button>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button class="tab" :class="{ active: tab === 'all' }"        @click="tab='all'">Todos</button>
      <button class="tab" :class="{ active: tab === 'requisito' }"  @click="tab='requisito'">Requisitos</button>
      <button class="tab" :class="{ active: tab === 'observacion' }" @click="tab='observacion'">Observaciones</button>
    </div>

    <div class="table-wrap">
      <div v-if="loading" class="t-loading"><div class="spinner-border text-primary"></div></div>
      <table v-else class="crud-table">
        <thead><tr><th>#</th><th>Tipo</th><th>Contenido</th><th>Orden</th><th>Activo</th><th></th></tr></thead>
        <tbody>
          <tr v-for="c in filtered" :key="c.id">
            <td class="t-id">{{ c.id }}</td>
            <td><span class="badge-type" :class="c.type === 'requisito' ? 'b-req' : 'b-obs'">{{ c.type === 'requisito' ? 'Requisito' : 'Observación' }}</span></td>
            <td class="t-content">{{ c.content }}</td>
            <td>{{ c.order_index }}</td>
            <td><span class="badge-status" :class="c.is_active ? 'b-yes' : 'b-no'">{{ c.is_active ? 'Sí' : 'No' }}</span></td>
            <td class="t-actions">
              <button class="icon-btn" @click="openEdit(c)"><i class="bi bi-pencil"></i></button>
              <button class="icon-btn del" @click="deleteItem(c)"><i class="bi bi-trash"></i></button>
            </td>
          </tr>
          <tr v-if="!loading && !filtered.length">
            <td colspan="6" class="t-empty">Sin registros</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal -->
    <teleport to="body">
      <div v-if="modal.open" class="modal-overlay" @click.self="closeModal">
        <div class="modal-box">
          <div class="modal-hdr">
            <span>{{ modal.id ? 'Editar' : 'Nuevo ítem' }}</span>
            <button class="modal-close" @click="closeModal"><i class="bi bi-x-lg"></i></button>
          </div>
          <div class="modal-body">
            <div class="field">
              <label class="lbl">Tipo *</label>
              <select v-model="form.type" class="inp">
                <option value="requisito">Requisito (para arrendar)</option>
                <option value="observacion">Observación general</option>
              </select>
            </div>
            <div class="field">
              <label class="lbl">Contenido *</label>
              <textarea v-model="form.content" class="inp inp-ta" rows="3"
                :placeholder="form.type === 'requisito' ? 'Ej: Fotocopia cédula de ciudadanía' : 'Ej: El activo incluye parqueadero cubierto'"></textarea>
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
import { ref, computed } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import { useModuleName } from "@/composables/useModuleName"

const { moduleName } = useModuleName()
const items   = ref([])
const loading = ref(false)
const saving  = ref(false)
const tab     = ref("all")
const modal   = ref({ open: false, id: null })
const form    = ref({ type: "requisito", content: "", order_index: 0, is_active: 1 })

const filtered = computed(() =>
  tab.value === "all" ? items.value : items.value.filter(c => c.type === tab.value)
)

async function load() {
  loading.value = true
  try { const r = await api.get("/asset-content/all"); items.value = r.data }
  catch { items.value = [] }
  finally { loading.value = false }
}

function openNew()  { form.value = { type: "requisito", content: "", order_index: 0, is_active: 1 }; modal.value = { open: true, id: null } }
function openEdit(c){ form.value = { ...c }; modal.value = { open: true, id: c.id } }
function closeModal(){ modal.value.open = false }

async function save() {
  if (!form.value.content.trim()) return showToast("El contenido es obligatorio", "warning")
  saving.value = true
  try {
    if (modal.value.id) await api.put(`/asset-content/${modal.value.id}`, form.value)
    else                await api.post("/asset-content/", form.value)
    showToast("Guardado", "success")
    closeModal()
    await load()
  } catch (e) { showToast(e.response?.data?.detail || "Error", "error") }
  finally { saving.value = false }
}

async function deleteItem(c) {
  const { isConfirmed } = await window.Swal.fire({
    title: "¿Eliminar?", text: `"${c.content.substring(0, 60)}…"`, icon: "warning",
    showCancelButton: true, confirmButtonText: "Sí, eliminar", confirmButtonColor: "#ef4444",
  })
  if (!isConfirmed) return
  try { await api.delete(`/asset-content/${c.id}`); showToast("Eliminado", "success"); await load() }
  catch (e) { showToast(e.response?.data?.detail || "Error", "error") }
}

load()
</script>

<style scoped>
.crud-container { padding: 20px; max-width: 860px; }
.crud-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 14px; flex-wrap: wrap; gap: 10px; }
.crud-title  { font-size: 18px; font-weight: 700; color: #1e293b; margin: 0; }
.crud-subtitle { font-size: 12px; color: #64748b; margin: 2px 0 0; }
.btn-new { background: #2563eb; color: #fff; border: none; border-radius: 8px; padding: 9px 18px; font-size: 13px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 4px; }
.btn-new:hover { background: #1d4ed8; }
.tabs { display: flex; gap: 4px; margin-bottom: 14px; border-bottom: 1px solid #e2e8f0; padding-bottom: 2px; }
.tab  { background: none; border: none; padding: 6px 14px; font-size: 13px; color: #64748b; cursor: pointer; border-radius: 6px 6px 0 0; font-weight: 600; transition: .15s; }
.tab.active { color: #2563eb; background: #eff6ff; border-bottom: 2px solid #2563eb; }
.tab:hover:not(.active) { color: #1e293b; background: #f8fafc; }
.table-wrap { overflow-x: auto; }
.t-loading { display: flex; justify-content: center; padding: 40px; }
.crud-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.crud-table th { background: #f8fafc; color: #64748b; font-weight: 700; padding: 10px 12px; text-align: left; border-bottom: 2px solid #e2e8f0; white-space: nowrap; }
.crud-table td { padding: 10px 12px; border-bottom: 1px solid #f1f5f9; color: #1e293b; vertical-align: middle; }
.crud-table tr:hover td { background: #f8fafc; }
.t-id { color: #94a3b8; font-size: 11px; }
.t-content { max-width: 340px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.t-empty { text-align: center; color: #94a3b8; padding: 24px; }
.t-actions { display: flex; gap: 6px; white-space: nowrap; }
.badge-type { font-size: 11px; font-weight: 700; border-radius: 20px; padding: 2px 8px; }
.b-req { background: rgba(37,99,235,.1); color: #1d4ed8; }
.b-obs { background: rgba(245,158,11,.1); color: #b45309; }
.badge-status { font-size: 11px; font-weight: 700; border-radius: 20px; padding: 2px 8px; }
.b-yes { background: rgba(34,197,94,.12); color: #16a34a; }
.b-no  { background: rgba(239,68,68,.1);  color: #dc2626; }
.icon-btn { background: transparent; border: 1px solid #e2e8f0; color: #64748b; border-radius: 6px; padding: 4px 8px; cursor: pointer; font-size: 13px; transition: .15s; }
.icon-btn:hover { background: #eff6ff; color: #2563eb; border-color: #93c5fd; }
.icon-btn.del:hover { background: #fef2f2; color: #dc2626; border-color: #fca5a5; }
/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 9999; padding: 16px; }
.modal-box { background: #fff; border-radius: 14px; width: 100%; max-width: 480px; box-shadow: 0 20px 60px rgba(0,0,0,.15); }
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
.inp-ta { resize: vertical; font-family: inherit; line-height: 1.5; }
.btn-cancel { background: #f8fafc; color: #64748b; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 18px; font-size: 13px; cursor: pointer; }
.btn-save   { background: #2563eb; color: #fff; border: none; border-radius: 8px; padding: 8px 20px; font-size: 13px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 4px; }
.btn-save:hover:not(:disabled) { background: #1d4ed8; }
.btn-save:disabled { opacity: .5; cursor: not-allowed; }
.spin { animation: spin .7s linear infinite; }
@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }
@media (max-width: 768px) { .crud-container { padding: 14px; } .row2 { grid-template-columns: 1fr; } }
@media (max-width: 576px) { .crud-container { padding: 10px; } }
</style>
