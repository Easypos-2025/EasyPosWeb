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
      <span class="leg-item"><i class="bi bi-lock-fill me-1" style="color:#ef4444"></i>Tiene registros bloqueados</span>
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
            <th class="th-c" title="Meseros POS">Meseros</th>
            <th class="th-c" title="Productos">Productos</th>
            <th class="th-c" title="Categorías">Categ.</th>
            <th class="th-c" title="Trabajadores">Trabaj.</th>
            <th class="th-c" title="Clientes">Clientes</th>
            <th class="th-c" title="Bodega">Bodega</th>
            <th class="th-c" title="Activos">Activos</th>
            <th class="th-c" title="Tareas activas">Tareas</th>
            <th class="th-c" title="Facturas/día">Fact./día</th>
            <th class="th-c" title="Recibos/día">Recib./día</th>
            <th class="th-c" title="Tareas/día">Tar./día</th>
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
            <td class="th-c"><span class="lim-val">{{ fmt(row.max_waiters) }}</span></td>
            <td class="th-c"><span class="lim-val">{{ fmt(row.max_products) }}</span></td>
            <td class="th-c"><span class="lim-val">{{ fmt(row.max_categories) }}</span></td>
            <td class="th-c"><span class="lim-val">{{ fmt(row.max_workers) }}</span></td>
            <td class="th-c"><span class="lim-val">{{ fmt(row.max_clients) }}</span></td>
            <td class="th-c"><span class="lim-val">{{ fmt(row.max_bodega_items) }}</span></td>
            <td class="th-c"><span class="lim-val">{{ fmt(row.max_assets) }}</span></td>
            <td class="th-c"><span class="lim-val">{{ fmt(row.max_tasks) }}</span></td>
            <td class="th-c"><span class="lim-val">{{ fmt(row.max_daily_invoices) }}</span></td>
            <td class="th-c"><span class="lim-val">{{ fmt(row.max_daily_receipts) }}</span></td>
            <td class="th-c"><span class="lim-val">{{ fmt(row.max_daily_tasks) }}</span></td>
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
                <button class="btn btn-sm btn-outline-danger" @click="openBlocked(row)" title="Ver registros bloqueados">
                  <i class="bi bi-lock-fill"></i>
                </button>
                <button v-if="row.is_custom" class="btn btn-sm btn-outline-secondary" @click="resetRow(row)" title="Restaurar a plan base">
                  <i class="bi bi-arrow-counterclockwise"></i>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="!loading && filtered.length === 0">
            <td colspan="16" class="text-center text-muted py-4">No hay registros con estos filtros</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- MODAL EDITAR LÍMITES -->
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

          <div class="limits-section-title">Límites por cantidad total</div>
          <div class="limits-grid">
            <div class="limit-field" v-for="f in countLimitFields" :key="f.key">
              <label>{{ f.label }}</label>
              <input v-model.number="editForm[f.key]" type="number" min="-1" class="form-control form-control-sm" />
            </div>
          </div>

          <div class="limits-section-title mt-2">Límites diarios (transacciones)</div>
          <div class="limits-grid">
            <div class="limit-field" v-for="f in dailyLimitFields" :key="f.key">
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

    <!-- MODAL REGISTROS BLOQUEADOS -->
    <div v-if="showBlocked" class="modal-overlay" @click.self="closeBlocked">
      <div class="modal-box modal-box-lg">
        <div class="mh">
          <div>
            <h3><i class="bi bi-lock-fill me-2" style="color:#ef4444"></i>Registros bloqueados — {{ blockedRow?.company_name }}</h3>
            <p class="mh-sub">Selecciona registros para desbloquearlos manualmente</p>
          </div>
          <button class="btn-x" @click="closeBlocked"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="mb-area">

          <div v-if="blockedLoading" class="table-loading">
            <i class="bi bi-arrow-repeat spin"></i> Cargando registros bloqueados...
          </div>

          <div v-else-if="blockedTotal === 0" class="blocked-empty">
            <i class="bi bi-check-circle-fill" style="color:#10b981;font-size:2rem"></i>
            <p>No hay registros bloqueados para este asociado.</p>
          </div>

          <template v-else>
            <div class="blocked-summary-bar">
              <span class="blocked-total-badge">{{ blockedTotal }} registros bloqueados en total</span>
              <span class="blocked-select-hint" v-if="selectedToUnblock.length">
                {{ selectedToUnblock.length }} seleccionado(s)
              </span>
            </div>

            <!-- Sección por recurso -->
            <div v-for="(items, resource) in blockedData.resources" :key="resource" class="blocked-resource-section">
              <div class="blocked-resource-header">
                <i :class="RESOURCE_ICONS[resource] || 'bi bi-question-circle'" class="me-2"></i>
                <strong>{{ RESOURCE_LABELS[resource] || resource }}</strong>
                <span class="blocked-count-chip">{{ items.length }}</span>
                <button class="btn-select-all" @click="toggleSelectAll(resource, items)">
                  {{ isAllSelected(resource, items) ? 'Deseleccionar todo' : 'Seleccionar todo' }}
                </button>
              </div>
              <div class="blocked-items-grid">
                <label
                  v-for="item in items" :key="item.id"
                  class="blocked-item-card"
                  :class="{ selected: isSelected(resource, item.id) }"
                >
                  <input type="checkbox"
                    :checked="isSelected(resource, item.id)"
                    @change="toggleItem(resource, item.id)"
                    class="blocked-cb"
                  />
                  <div class="blocked-item-info">
                    <span class="blocked-item-name">{{ item.name }}</span>
                    <span v-if="item.email" class="blocked-item-meta">{{ item.email }}</span>
                  </div>
                </label>
              </div>
            </div>
          </template>
        </div>

        <div class="mf" v-if="!blockedLoading && blockedTotal > 0">
          <button class="btn btn-secondary btn-sm" @click="closeBlocked">Cerrar</button>
          <button
            class="btn btn-outline-warning btn-sm"
            @click="forceDowngrade"
            :disabled="unblocking"
            title="Recalcular bloqueos según límites actuales"
          >
            <i class="bi bi-arrow-repeat me-1"></i>Recalcular bloqueos
          </button>
          <button
            class="btn btn-success btn-sm"
            :disabled="selectedToUnblock.length === 0 || unblocking"
            @click="unblockSelected"
          >
            <i v-if="unblocking" class="bi bi-arrow-repeat spin me-1"></i>
            <i v-else class="bi bi-unlock-fill me-1"></i>
            {{ unblocking ? 'Desbloqueando...' : `Desbloquear ${selectedToUnblock.length > 0 ? '(' + selectedToUnblock.length + ')' : ''}` }}
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

// Estado modal bloqueados
const showBlocked    = ref(false)
const blockedRow     = ref(null)
const blockedData    = ref({ resources: {} })
const blockedLoading = ref(false)
const unblocking     = ref(false)
const selectedToUnblock = ref([])  // [{ resource, id }]

const RESOURCE_LABELS = {
  users:        "Usuarios",
  pos_waiters:  "Meseros/Cajeros POS",
  products:     "Productos",
  categories:   "Categorías",
  workers:      "Trabajadores",
  clients:      "Clientes",
  bodega_items: "Artículos de bodega",
  assets:       "Activos",
}

const RESOURCE_ICONS = {
  users:        "bi bi-people-fill",
  pos_waiters:  "bi bi-person-badge-fill",
  products:     "bi bi-box-seam-fill",
  categories:   "bi bi-tags-fill",
  workers:      "bi bi-hammer",
  clients:      "bi bi-person-lines-fill",
  bodega_items: "bi bi-archive-fill",
  assets:       "bi bi-buildings-fill",
}

const countLimitFields = [
  { key: "max_users",        label: "Usuarios" },
  { key: "max_waiters",      label: "Meseros POS" },
  { key: "max_products",     label: "Productos" },
  { key: "max_categories",   label: "Categorías" },
  { key: "max_workers",      label: "Trabajadores" },
  { key: "max_clients",      label: "Clientes" },
  { key: "max_bodega_items", label: "Artículos bodega" },
  { key: "max_assets",       label: "Activos" },
]

const dailyLimitFields = [
  { key: "max_tasks",          label: "Tareas activas (total)" },
  { key: "max_daily_invoices", label: "Facturas por día" },
  { key: "max_daily_receipts", label: "Recibos por día" },
  { key: "max_daily_tasks",    label: "Tareas por día" },
]

const blockedTotal = computed(() =>
  Object.values(blockedData.value.resources || {}).reduce((s, arr) => s + arr.length, 0)
)

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
    if (idx !== -1) rows.value[idx] = { ...rows.value[idx], ...res.data }
    showEdit.value = false
    if (res.data.blocked_summary && Object.keys(res.data.blocked_summary).length) {
      const total = Object.values(res.data.blocked_summary).reduce((s, arr) => s + arr.length, 0)
      showToast(`Límites actualizados. ${total} registro(s) bloqueados por nuevo límite.`, "warning")
    } else {
      showToast("Límites actualizados", "success")
    }
  } catch (e) {
    showToast(e.response?.data?.detail || "Error guardando", "error")
  } finally { saving.value = false }
}

async function resetEdit() {
  saving.value = true
  try {
    const res = await api.post(`/plan-associate-limits/${editRow.value.company_id}/reset`)
    const idx = rows.value.findIndex(r => r.company_id === editRow.value.company_id)
    if (idx !== -1) rows.value[idx] = { ...rows.value[idx], ...res.data }
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
    if (idx !== -1) rows.value[idx] = { ...rows.value[idx], ...res.data }
    showToast("Restaurado al plan base", "success")
  } catch (e) { showToast(e.response?.data?.detail || "Error", "error") }
}

// ─── BLOQUEADOS ───────────────────────────────────────────
async function openBlocked(row) {
  blockedRow.value        = row
  blockedData.value       = { resources: {} }
  selectedToUnblock.value = []
  showBlocked.value       = true
  blockedLoading.value    = true
  try {
    const res = await api.get(`/plan-associate-limits/${row.company_id}/blocked`)
    blockedData.value = res.data
  } catch { showToast("Error cargando registros bloqueados", "error") }
  finally { blockedLoading.value = false }
}

function closeBlocked() {
  showBlocked.value = false
  selectedToUnblock.value = []
}

function isSelected(resource, id) {
  return selectedToUnblock.value.some(s => s.resource === resource && s.id === id)
}

function toggleItem(resource, id) {
  const idx = selectedToUnblock.value.findIndex(s => s.resource === resource && s.id === id)
  if (idx !== -1) selectedToUnblock.value.splice(idx, 1)
  else selectedToUnblock.value.push({ resource, id })
}

function isAllSelected(resource, items) {
  return items.every(item => isSelected(resource, item.id))
}

function toggleSelectAll(resource, items) {
  if (isAllSelected(resource, items)) {
    selectedToUnblock.value = selectedToUnblock.value.filter(s => s.resource !== resource)
  } else {
    items.forEach(item => {
      if (!isSelected(resource, item.id))
        selectedToUnblock.value.push({ resource, id: item.id })
    })
  }
}

async function unblockSelected() {
  if (!selectedToUnblock.value.length) return
  unblocking.value = true

  // Agrupar por recurso
  const byResource = {}
  selectedToUnblock.value.forEach(({ resource, id }) => {
    if (!byResource[resource]) byResource[resource] = []
    byResource[resource].push(id)
  })

  let totalUnblocked = 0
  let errors = 0
  for (const [resource, ids] of Object.entries(byResource)) {
    try {
      const res = await api.post(`/plan-associate-limits/${blockedRow.value.company_id}/unblock`, { resource, ids })
      totalUnblocked += res.data.unblocked?.length || 0
      // Quitar del mapa local
      blockedData.value.resources[resource] = blockedData.value.resources[resource].filter(
        item => !ids.includes(item.id)
      )
      if (!blockedData.value.resources[resource].length)
        delete blockedData.value.resources[resource]
    } catch { errors++ }
  }

  selectedToUnblock.value = []
  unblocking.value = false

  if (errors) showToast(`${totalUnblocked} desbloqueados, ${errors} error(es)`, "warning")
  else showToast(`${totalUnblocked} registro(s) desbloqueados correctamente`, "success")
}

async function forceDowngrade() {
  unblocking.value = true
  try {
    const res = await api.post(`/plan-associate-limits/${blockedRow.value.company_id}/apply-downgrade`)
    showToast(res.data.message || "Bloqueos recalculados", "info")
    // Recargar datos
    const res2 = await api.get(`/plan-associate-limits/${blockedRow.value.company_id}/blocked`)
    blockedData.value = res2.data
    selectedToUnblock.value = []
  } catch (e) {
    showToast(e.response?.data?.detail || "Error", "error")
  } finally { unblocking.value = false }
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1500px; }
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
.data-table th { background: #f8fafc; color: #475569; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: .4px; padding: 10px; border-bottom: 1px solid #e2e8f0; white-space: nowrap; }
.data-table td { padding: 9px 10px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
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

.action-row   { display: flex; gap: 4px; justify-content: center; flex-wrap: wrap; }
.btn          { display: inline-flex; align-items: center; gap: 6px; padding: 7px 14px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; transition: all .15s; border: 1.5px solid transparent; }
.btn-primary  { background: #3b82f6; color: #fff; border-color: #3b82f6; }
.btn-primary:hover:not(:disabled) { background: #2563eb; }
.btn-primary:disabled { opacity: .6; cursor: not-allowed; }
.btn-secondary { border-color: #e2e8f0; background: #fff; color: #64748b; }
.btn-success  { background: #10b981; color: #fff; border-color: #10b981; }
.btn-success:hover:not(:disabled) { background: #059669; }
.btn-success:disabled { opacity: .5; cursor: not-allowed; }
.btn-outline-primary   { background: #eff6ff; color: #1d4ed8; border-color: #bfdbfe; }
.btn-outline-secondary { background: #f8fafc; color: #475569; border-color: #e2e8f0; }
.btn-outline-danger    { background: #fef2f2; color: #dc2626; border-color: #fecaca; }
.btn-outline-danger:hover { background: #fee2e2; }
.btn-outline-warning   { background: #fffbeb; color: #b45309; border-color: #fde68a; }
.btn-sm { padding: 5px 10px; font-size: 11px; }

/* MODALES */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 2000; padding: 16px; }
.modal-box     { background: #fff; border-radius: 16px; width: 100%; max-width: 560px; max-height: 90vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,.2); }
.modal-box-lg  { max-width: 720px; }
.mh  { display: flex; align-items: flex-start; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid #f1f5f9; flex-shrink: 0; gap: 8px; }
.mh h3 { font-size: 15px; font-weight: 700; color: #1e293b; margin: 0 0 3px; }
.mh-sub { font-size: 12px; color: #64748b; margin: 0; }
.btn-x { background: none; border: none; font-size: 16px; cursor: pointer; color: #94a3b8; flex-shrink: 0; }
.mb-area { padding: 18px 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; flex: 1; }
.mf { padding: 12px 20px 16px; display: flex; justify-content: flex-end; gap: 8px; border-top: 1px solid #f1f5f9; flex-shrink: 0; flex-wrap: wrap; }

.edit-plan-info { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #475569; background: #f8fafc; border-radius: 8px; padding: 8px 12px; flex-wrap: wrap; }
.edit-hint { font-size: 12px; color: #64748b; margin: 0; }
.custom-badge { background: #fef3c7; color: #92400e; font-size: 10px; font-weight: 700; padding: 1px 7px; border-radius: 20px; }
.limits-section-title { font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: .5px; }
.mt-2 { margin-top: 4px; }
.limits-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
.limit-field { display: flex; flex-direction: column; gap: 4px; }
.limit-field label { font-size: 12px; font-weight: 600; color: #374151; }
.fg { display: flex; flex-direction: column; gap: 4px; }
.fg label { font-size: 13px; font-weight: 600; color: #374151; }

/* BLOQUEADOS */
.blocked-empty { text-align: center; padding: 24px; color: #64748b; display: flex; flex-direction: column; align-items: center; gap: 8px; }
.blocked-summary-bar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.blocked-total-badge { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; font-size: 12px; font-weight: 700; padding: 3px 10px; border-radius: 20px; }
.blocked-select-hint { font-size: 12px; color: #64748b; }

.blocked-resource-section { display: flex; flex-direction: column; gap: 8px; }
.blocked-resource-header {
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; color: #1e293b;
}
.blocked-count-chip {
  background: #ef4444; color: #fff; font-size: 10px; font-weight: 800;
  padding: 1px 7px; border-radius: 20px;
}
.btn-select-all {
  margin-left: auto; background: none; border: none; font-size: 11px;
  color: #3b82f6; cursor: pointer; font-weight: 600; padding: 2px 6px;
  border-radius: 4px;
}
.btn-select-all:hover { background: #eff6ff; }

.blocked-items-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 6px; }
.blocked-item-card {
  display: flex; align-items: flex-start; gap: 8px;
  border: 1.5px solid #e2e8f0; border-radius: 8px; padding: 8px 10px;
  cursor: pointer; transition: all .15s; background: #fff;
}
.blocked-item-card:hover  { border-color: #3b82f6; background: #eff6ff; }
.blocked-item-card.selected { border-color: #10b981; background: #f0fdf4; }
.blocked-cb { flex-shrink: 0; margin-top: 2px; cursor: pointer; }
.blocked-item-info { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.blocked-item-name { font-size: 12px; font-weight: 600; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.blocked-item-meta { font-size: 11px; color: #94a3b8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

@media (max-width: 768px) {
  .page-container { padding: 16px; }
  .limits-grid { grid-template-columns: 1fr 1fr; }
  .table-card { border-radius: 10px; }
  .blocked-items-grid { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 576px) {
  .limits-grid { grid-template-columns: 1fr; }
  .page-title  { font-size: 18px; }
  .blocked-items-grid { grid-template-columns: 1fr; }
}
</style>
