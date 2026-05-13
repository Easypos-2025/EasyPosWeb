<template>
  <div class="page-container">

    <div class="page-header">
      <div>
        <h1 class="page-title"><i class="bi bi-sliders me-2"></i>Límites por Asociado</h1>
        <p class="page-subtitle">Visualiza y personaliza las cuotas de cada plan por empresa</p>
      </div>
      <div class="header-actions">
        <input v-model="search" class="form-control" placeholder="Buscar empresa o plan..." style="max-width:240px" />
        <button class="btn btn-outline-secondary btn-sm" @click="load">
          <i class="bi bi-arrow-clockwise"></i> Actualizar
        </button>
      </div>
    </div>

    <!-- Leyenda -->
    <div class="legend-bar">
      <span class="leg-item"><span class="dot dot-plan"></span>Límites del plan (sin modificar)</span>
      <span class="leg-item"><span class="dot dot-custom"></span>Límites personalizados</span>
      <span class="leg-item"><i class="bi bi-infinity me-1" style="color:#6366f1"></i>-1 = ilimitado</span>
    </div>

    <!-- Tabla -->
    <div class="table-card">
      <div v-if="loading" class="table-loading"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Empresa</th>
            <th>Plan base</th>
            <th class="th-c" title="Usuarios">Usuarios</th>
            <th class="th-c" title="Productos">Productos</th>
            <th class="th-c" title="Categorías">Categ.</th>
            <th class="th-c" title="Trabajadores">Trabaj.</th>
            <th class="th-c" title="Clientes">Clientes</th>
            <th class="th-c" title="Bodega">Bodega</th>
            <th class="th-c" title="Tareas">Tareas</th>
            <th class="th-c" title="Facturas/día">Fact./día</th>
            <th class="th-c" title="Activos">Activos</th>
            <th class="th-c">Estado</th>
            <th class="th-c">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in filtered" :key="row.company_id" :class="{ 'row-custom': row.is_custom }">
            <td>
              <strong>{{ row.company_name }}</strong>
            </td>
            <td><span class="plan-badge">{{ row.plan_name }}</span></td>
            <td class="th-c"><span class="lim-val">{{ fmt(row.max_users) }}</span></td>
            <td class="th-c"><span class="lim-val">{{ fmt(row.max_products) }}</span></td>
            <td class="th-c"><span class="lim-val">{{ fmt(row.max_categories) }}</span></td>
            <td class="th-c"><span class="lim-val">{{ fmt(row.max_workers) }}</span></td>
            <td class="th-c"><span class="lim-val">{{ fmt(row.max_clients) }}</span></td>
            <td class="th-c"><span class="lim-val">{{ fmt(row.max_bodega_items) }}</span></td>
            <td class="th-c"><span class="lim-val">{{ fmt(row.max_tasks) }}</span></td>
            <td class="th-c"><span class="lim-val">{{ fmt(row.max_daily_invoices) }}</span></td>
            <td class="th-c"><span class="lim-val">{{ fmt(row.max_assets) }}</span></td>
            <td class="th-c">
              <span class="status-badge" :class="row.is_custom ? 'st-custom' : 'st-plan'">
                {{ row.is_custom ? 'Personalizado' : 'Plan base' }}
              </span>
            </td>
            <td class="th-c">
              <div class="action-row">
                <button class="btn btn-sm btn-outline-primary" @click="openEdit(row)" title="Editar límites">
                  <i class="bi bi-pencil"></i>
                </button>
                <button v-if="row.is_custom" class="btn btn-sm btn-outline-secondary" @click="resetRow(row)" title="Restaurar a plan base">
                  <i class="bi bi-arrow-counterclockwise"></i>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="!loading && filtered.length === 0">
            <td colspan="13" class="text-center text-muted py-4">No hay registros con estos filtros</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- MODAL EDITAR -->
    <div v-if="showEdit" class="modal-overlay" @click.self="showEdit = false">
      <div class="modal-box">
        <div class="mh">
          <h3><i class="bi bi-sliders me-2"></i>Límites — {{ editRow?.company_name }}</h3>
          <button class="btn-x" @click="showEdit = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="mb-area">
          <div class="edit-plan-info">
            <i class="bi bi-award me-1" style="color:#f59e0b"></i>
            Plan base: <strong>{{ editRow?.plan_name }}</strong>
            <span class="custom-badge" v-if="editForm.is_custom">Personalizado</span>
          </div>
          <p class="edit-hint">Usa <strong>-1</strong> para ilimitado. Los cambios solo aplican a esta empresa.</p>
          <div class="limits-grid">
            <div class="limit-field" v-for="f in limitFields" :key="f.key">
              <label>{{ f.label }}</label>
              <input v-model.number="editForm[f.key]" type="number" min="-1" class="form-control form-control-sm" />
            </div>
          </div>
          <div class="fg">
            <label>Nota interna (opcional)</label>
            <textarea v-model="editForm.notes" class="form-control" rows="2"
              placeholder="Ej: asociado VIP con acceso especial..."></textarea>
          </div>
        </div>
        <div class="mf">
          <button class="btn btn-secondary btn-sm" @click="showEdit = false">Cancelar</button>
          <button v-if="editRow?.is_custom" class="btn btn-outline-secondary btn-sm" @click="resetEdit">
            <i class="bi bi-arrow-counterclockwise me-1"></i>Restaurar plan base
          </button>
          <button class="btn btn-primary btn-sm" @click="saveEdit" :disabled="saving">
            <i v-if="saving" class="bi bi-arrow-repeat spin"></i>
            {{ saving ? 'Guardando...' : 'Guardar cambios' }}
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

const rows    = ref([])
const loading = ref(true)
const search  = ref("")
const showEdit = ref(false)
const editRow  = ref(null)
const editForm = ref({})
const saving   = ref(false)

const limitFields = [
  { key: "max_users",          label: "Usuarios" },
  { key: "max_products",       label: "Productos" },
  { key: "max_categories",     label: "Categorías" },
  { key: "max_workers",        label: "Trabajadores" },
  { key: "max_clients",        label: "Clientes" },
  { key: "max_bodega_items",   label: "Artículos bodega" },
  { key: "max_tasks",          label: "Tareas activas" },
  { key: "max_daily_invoices", label: "Facturas por día" },
  { key: "max_assets",         label: "Activos" },
]

function fmt(v) { return v === -1 ? "∞" : v }

const filtered = computed(() => {
  const q = search.value.toLowerCase()
  if (!q) return rows.value
  return rows.value.filter(r =>
    r.company_name.toLowerCase().includes(q) ||
    r.plan_name.toLowerCase().includes(q)
  )
})

async function load() {
  loading.value = true
  try {
    const res = await api.get("/plan-associate-limits/")
    rows.value = res.data
  } catch { showToast("Error cargando límites", "error") }
  finally { loading.value = false }
}

function openEdit(row) {
  editRow.value  = row
  editForm.value = { ...row }
  showEdit.value = true
}

async function saveEdit() {
  saving.value = true
  try {
    const res = await api.put(`/plan-associate-limits/${editRow.value.company_id}`, editForm.value)
    const idx = rows.value.findIndex(r => r.company_id === editRow.value.company_id)
    if (idx !== -1) rows.value[idx] = res.data
    showEdit.value = false
    showToast("Límites actualizados", "success")
  } catch (e) {
    showToast(e.response?.data?.detail || "Error guardando", "error")
  } finally { saving.value = false }
}

async function resetEdit() {
  saving.value = true
  try {
    const res = await api.post(`/plan-associate-limits/${editRow.value.company_id}/reset`)
    const idx = rows.value.findIndex(r => r.company_id === editRow.value.company_id)
    if (idx !== -1) rows.value[idx] = res.data
    showEdit.value = false
    showToast("Restaurado a valores del plan base", "success")
  } catch (e) {
    showToast(e.response?.data?.detail || "Error", "error")
  } finally { saving.value = false }
}

async function resetRow(row) {
  const { isConfirmed } = await window.Swal.fire({
    title: "¿Restaurar límites?",
    text: `Se restaurarán los límites de "${row.company_name}" a los valores del plan "${row.plan_name}".`,
    icon: "question", showCancelButton: true,
    confirmButtonText: "Sí, restaurar", cancelButtonText: "Cancelar",
  })
  if (!isConfirmed) return
  try {
    const res = await api.post(`/plan-associate-limits/${row.company_id}/reset`)
    const idx = rows.value.findIndex(r => r.company_id === row.company_id)
    if (idx !== -1) rows.value[idx] = res.data
    showToast("Restaurado al plan base", "success")
  } catch (e) { showToast(e.response?.data?.detail || "Error", "error") }
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1400px; }
.page-header    { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; gap: 12px; flex-wrap: wrap; }
.page-title     { font-size: 22px; font-weight: 700; color: #1e293b; margin: 0 0 4px; }
.page-subtitle  { font-size: 13px; color: #64748b; margin: 0; }
.header-actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }

.legend-bar { display: flex; gap: 18px; font-size: 12px; color: #64748b; margin-bottom: 14px; flex-wrap: wrap; }
.leg-item   { display: flex; align-items: center; gap: 5px; }
.dot        { width: 10px; height: 10px; border-radius: 50%; }
.dot-plan   { background: #e2e8f0; }
.dot-custom { background: #fde68a; }

.table-card    { background: #fff; border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,.08); overflow-x: auto; }
.table-loading { padding: 40px; text-align: center; color: #94a3b8; }
.data-table    { width: 100%; border-collapse: collapse; font-size: 12px; }
.data-table th { background: #f8fafc; color: #475569; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: .4px; padding: 10px 10px; border-bottom: 1px solid #e2e8f0; white-space: nowrap; }
.data-table td { padding: 10px 10px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.data-table tr:last-child td { border-bottom: none; }
.th-c          { text-align: center; }
.row-custom td { background: #fffbeb !important; }
.row-custom:hover td { background: #fef3c7 !important; }
.data-table tr:hover td { background: #f8fafc; }
.text-center { text-align: center; }
.text-muted  { color: #94a3b8; font-size: 12px; }
.py-4        { padding: 32px 0; }

.plan-badge { background: #eff6ff; color: #1d4ed8; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 20px; }
.lim-val    { font-size: 13px; font-weight: 600; color: #1e293b; }

.status-badge { font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 20px; white-space: nowrap; }
.st-plan      { background: #f1f5f9; color: #475569; }
.st-custom    { background: #fef3c7; color: #92400e; }

.action-row   { display: flex; gap: 4px; justify-content: center; }
.btn          { display: inline-flex; align-items: center; gap: 6px; padding: 7px 14px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; transition: all .15s; }
.btn-primary  { background: #3b82f6; color: #fff; border: none; }
.btn-primary:hover { background: #2563eb; }
.btn-primary:disabled { opacity: .6; cursor: not-allowed; }
.btn-secondary { border: 1.5px solid #e2e8f0; background: #fff; color: #64748b; }
.btn-outline-primary   { background: #eff6ff; color: #1d4ed8; border: 1.5px solid #bfdbfe; }
.btn-outline-secondary { background: #f8fafc; color: #475569; border: 1.5px solid #e2e8f0; }
.btn-sm { padding: 5px 10px; font-size: 11px; }

/* MODAL */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 2000; padding: 16px; }
.modal-box     { background: #fff; border-radius: 16px; width: 100%; max-width: 560px; max-height: 90vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,.2); }
.mh  { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid #f1f5f9; flex-shrink: 0; }
.mh h3 { font-size: 15px; font-weight: 700; color: #1e293b; margin: 0; }
.btn-x { background: none; border: none; font-size: 16px; cursor: pointer; color: #94a3b8; }
.mb-area { padding: 18px 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; }
.mf { padding: 12px 20px 16px; display: flex; justify-content: flex-end; gap: 8px; border-top: 1px solid #f1f5f9; flex-shrink: 0; flex-wrap: wrap; }

.edit-plan-info { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #475569; background: #f8fafc; border-radius: 8px; padding: 8px 12px; flex-wrap: wrap; }
.edit-hint { font-size: 12px; color: #64748b; margin: 0; }
.custom-badge { background: #fef3c7; color: #92400e; font-size: 10px; font-weight: 700; padding: 1px 7px; border-radius: 20px; }

.limits-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
.limit-field { display: flex; flex-direction: column; gap: 4px; }
.limit-field label { font-size: 12px; font-weight: 600; color: #374151; }

.fg { display: flex; flex-direction: column; gap: 4px; }
.fg label { font-size: 13px; font-weight: 600; color: #374151; }

.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

@media (max-width: 768px) {
  .page-container { padding: 16px; }
  .limits-grid { grid-template-columns: 1fr 1fr; }
  .table-card { border-radius: 10px; }
}
@media (max-width: 576px) {
  .limits-grid { grid-template-columns: 1fr; }
  .page-title  { font-size: 18px; }
}
</style>
