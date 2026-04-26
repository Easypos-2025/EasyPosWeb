<template>
  <div class="page-wrap">

    <!-- ── HEADER ── -->
    <div class="page-header">
      <div class="page-header-left">
        <i class="bi bi-grid-3x3-gap-fill page-icon"></i>
        <div>
          <h1 class="page-title">Gestión Menú Topbar</h1>
          <p class="page-sub">Activa, desactiva y configura las opciones del menú desplegable del topbar</p>
        </div>
      </div>
      <button class="btn-primary" @click="openCreate">
        <i class="bi bi-plus-lg"></i> Nueva opción
      </button>
    </div>

    <!-- ── PREVIEW DROPDOWN ── -->
    <div class="preview-bar">
      <span class="preview-label"><i class="bi bi-eye"></i> Vista previa del menú</span>
      <div class="preview-menu">
        <div v-for="item in activeItems" :key="item.id" class="preview-item" :class="{ pending: isPending(item) }">
          <i :class="`bi ${item.icon || 'bi-grid'}`"></i>
          <span>{{ item.name }}</span>
          <span v-if="item.min_plan_id" class="preview-plan-tag">Plan {{ item.min_plan_id }}+</span>
          <span v-if="isPending(item)" class="preview-soon">Próximo</span>
        </div>
        <div v-if="!activeItems.length" class="preview-empty">Sin ítems activos</div>
      </div>
    </div>

    <!-- ── TABLA ── -->
    <div class="table-card">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div><span>Cargando...</span>
      </div>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th class="col-order">#</th>
            <th class="col-icon">Icono</th>
            <th>Nombre</th>
            <th>Clave</th>
            <th>Ruta</th>
            <th>Evidencia</th>
            <th>Plan mín.</th>
            <th class="col-center">Activo</th>
            <th class="col-act">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in items"
            :key="item.id"
            :class="{ 'row-inactive': !item.is_active }"
          >
            <td class="col-order td-order">
              <div class="order-btns">
                <button @click="moveUp(item)"   :disabled="item.order_index === minOrder" class="btn-order"><i class="bi bi-chevron-up"></i></button>
                <button @click="moveDown(item)" :disabled="item.order_index === maxOrder" class="btn-order"><i class="bi bi-chevron-down"></i></button>
              </div>
            </td>
            <td class="col-icon">
              <div class="icon-preview">
                <i :class="`bi ${item.icon || 'bi-grid'}`"></i>
              </div>
            </td>
            <td class="td-name">{{ item.name }}</td>
            <td><code class="td-key">{{ item.key }}</code></td>
            <td class="td-route">
              <span v-if="item.route" class="route-tag">{{ item.route }}</span>
              <span v-else class="no-route">—</span>
            </td>
            <td class="col-center">
              <i v-if="item.has_evidence" class="bi bi-check-circle-fill ev-yes" title="Requiere evidencia"></i>
              <i v-else class="bi bi-dash-circle ev-no"></i>
            </td>
            <td class="col-center">
              <span v-if="item.min_plan_id" class="plan-tag">Plan {{ item.min_plan_id }}+</span>
              <span v-else class="all-plans">Todos</span>
            </td>
            <td class="col-center">
              <button
                class="toggle-btn"
                :class="item.is_active ? 'toggle-on' : 'toggle-off'"
                @click="toggleActive(item)"
                :title="item.is_active ? 'Desactivar' : 'Activar'"
              >
                <span class="toggle-knob"></span>
              </button>
            </td>
            <td class="col-act td-actions">
              <button class="btn-tbl-edit" @click="openEdit(item)" title="Editar"><i class="bi bi-pencil"></i></button>
              <button class="btn-tbl-del"  @click="handleDelete(item)" title="Eliminar"><i class="bi bi-trash3"></i></button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ══════════════════════════════════════════════
         MODAL CREAR / EDITAR
    ══════════════════════════════════════════════ -->
    <Teleport to="body">
      <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
        <div class="modal-box">

          <div class="modal-header-bar">
            <h2>{{ editMode ? 'Editar opción' : 'Nueva opción del menú' }}</h2>
            <button class="btn-close-x" @click="closeModal"><i class="bi bi-x-lg"></i></button>
          </div>

          <div class="modal-body">

            <div class="form-row">
              <div class="form-group flex-1" :class="{ 'has-error': errors.name }">
                <label>Nombre <span class="req">*</span></label>
                <input v-model="form.name" type="text" placeholder="Ej: Registro Novedades" maxlength="100" />
                <span v-if="errors.name" class="error-msg">{{ errors.name }}</span>
              </div>
              <div class="form-group" style="width:160px" :class="{ 'has-error': errors.key }">
                <label>Clave única <span class="req">*</span></label>
                <input v-model="form.key" type="text" placeholder="novedades" maxlength="50" :disabled="editMode" />
                <span v-if="errors.key" class="error-msg">{{ errors.key }}</span>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group flex-1">
                <label>Icono Bootstrap</label>
                <div class="icon-input-row">
                  <input v-model="form.icon" type="text" placeholder="bi-exclamation-triangle" />
                  <div class="icon-preview-sm"><i :class="`bi ${form.icon || 'bi-grid'}`"></i></div>
                </div>
                <span class="field-hint">Nombre de la clase Bootstrap Icons (sin el prefijo "bi ")</span>
              </div>
              <div class="form-group flex-1">
                <label>Ruta Vue</label>
                <input v-model="form.route" type="text" placeholder="/novedades" />
                <span class="field-hint">Dejar vacío si aún no tiene vista</span>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group flex-1">
                <label>Plan mínimo requerido</label>
                <select v-model="form.min_plan_id">
                  <option :value="null">Todos los planes</option>
                  <option v-for="p in plans" :key="p.id" :value="p.id">Plan {{ p.id }} — {{ p.name }}</option>
                </select>
                <span class="field-hint">Si el asociado no tiene este plan, la opción no aparece</span>
              </div>
              <div class="form-group flex-1">
                <label>Orden</label>
                <input v-model.number="form.order_index" type="number" min="0" step="1" />
              </div>
            </div>

            <div class="form-row checkboxes-row">
              <label class="check-label">
                <input type="checkbox" v-model="form.has_evidence" />
                <span>Requiere evidencia (foto/archivo adjunto)</span>
              </label>
              <label class="check-label">
                <input type="checkbox" v-model="form.is_active" />
                <span>Activo</span>
              </label>
            </div>

          </div>

          <div class="modal-footer-bar">
            <button class="btn-secondary" @click="closeModal">Cancelar</button>
            <button class="btn-primary" :disabled="saving" @click="save">
              <span v-if="saving"><i class="bi bi-hourglass-split"></i> Guardando...</span>
              <span v-else><i class="bi bi-check-lg"></i> {{ editMode ? 'Actualizar' : 'Crear' }}</span>
            </button>
          </div>

        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

const items   = ref([])
const plans   = ref([])
const loading = ref(true)
const saving  = ref(false)

const showModal = ref(false)
const editMode  = ref(false)
const errors    = ref({ name: "", key: "" })

const emptyForm = () => ({
  id: null, name: "", key: "", icon: "bi-grid", route: "",
  has_evidence: false, min_plan_id: null, is_active: true, order_index: 0
})
const form = ref(emptyForm())

// ── Computed ────────────────────────────────────────
const activeItems = computed(() =>
  items.value.filter(i => i.is_active).sort((a, b) => a.order_index - b.order_index)
)
const minOrder = computed(() => Math.min(...items.value.map(i => i.order_index), 0))
const maxOrder = computed(() => Math.max(...items.value.map(i => i.order_index), 0))

function isPending(item) {
  return !item.route && item.key !== "ayuda"
}

// ── Carga ────────────────────────────────────────────
async function load() {
  loading.value = true
  try {
    const [itemsRes, plansRes] = await Promise.all([
      api.get("/topbar-menu/all"),
      api.get("/plans/")
    ])
    items.value = itemsRes.data.sort((a, b) => a.order_index - b.order_index)
    plans.value = plansRes.data
  } catch {
    showToast("Error cargando datos", "error")
  } finally {
    loading.value = false
  }
}

// ── Ordenar ──────────────────────────────────────────
async function moveUp(item) {
  const sorted = [...items.value].sort((a, b) => a.order_index - b.order_index)
  const idx    = sorted.findIndex(i => i.id === item.id)
  if (idx <= 0) return
  await swapOrder(sorted[idx], sorted[idx - 1])
}

async function moveDown(item) {
  const sorted = [...items.value].sort((a, b) => a.order_index - b.order_index)
  const idx    = sorted.findIndex(i => i.id === item.id)
  if (idx >= sorted.length - 1) return
  await swapOrder(sorted[idx], sorted[idx + 1])
}

async function swapOrder(a, b) {
  try {
    await Promise.all([
      api.put(`/topbar-menu/${a.id}`, { order_index: b.order_index }),
      api.put(`/topbar-menu/${b.id}`, { order_index: a.order_index }),
    ])
    await load()
  } catch { showToast("Error al reordenar", "error") }
}

// ── Toggle activo ────────────────────────────────────
async function toggleActive(item) {
  try {
    await api.put(`/topbar-menu/${item.id}`, { is_active: !item.is_active })
    item.is_active = !item.is_active
    showToast(item.is_active ? "Activado" : "Desactivado", "success")
  } catch { showToast("Error al actualizar", "error") }
}

// ── Crear / Editar ───────────────────────────────────
function openCreate() {
  form.value  = emptyForm()
  form.value.order_index = items.value.length
  editMode.value  = false
  errors.value = { name: "", key: "" }
  showModal.value = true
}

function openEdit(item) {
  form.value  = { ...item, route: item.route || "" }
  editMode.value  = true
  errors.value = { name: "", key: "" }
  showModal.value = true
}

function closeModal() { showModal.value = false }

function validate() {
  errors.value = { name: "", key: "" }
  let ok = true
  if (!form.value.name.trim()) { errors.value.name = "El nombre es obligatorio"; ok = false }
  if (!form.value.key.trim())  { errors.value.key  = "La clave es obligatoria";  ok = false }
  return ok
}

async function save() {
  if (!validate()) return
  saving.value = true
  const payload = {
    name:        form.value.name.trim(),
    key:         form.value.key.trim(),
    icon:        form.value.icon.trim() || "bi-grid",
    route:       form.value.route.trim() || null,
    has_evidence: form.value.has_evidence,
    min_plan_id: form.value.min_plan_id || null,
    is_active:   form.value.is_active,
    order_index: form.value.order_index,
  }
  try {
    if (editMode.value) {
      await api.put(`/topbar-menu/${form.value.id}`, payload)
      showToast("Opción actualizada", "success")
    } else {
      await api.post("/topbar-menu", payload)
      showToast("Opción creada", "success")
    }
    closeModal()
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error al guardar", "error")
  } finally {
    saving.value = false
  }
}

// ── Eliminar ─────────────────────────────────────────
async function handleDelete(item) {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar "${item.name}"?`,
    text: "Esta opción dejará de aparecer en el menú.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Eliminar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/topbar-menu/${item.id}`)
    showToast("Eliminado", "success")
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error", "error")
  }
}

onMounted(load)
</script>

<style scoped>
.page-wrap { padding: 24px; display: flex; flex-direction: column; gap: 20px; }

.page-header { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.page-header-left { display: flex; align-items: center; gap: 14px; }
.page-icon  { font-size: 30px; color: #6366f1; }
.page-title { font-size: 22px; font-weight: 700; margin: 0; color: var(--text-main, #1e293b); }
.page-sub   { font-size: 12px; color: var(--text-muted, #64748b); margin: 2px 0 0; }

/* Preview bar */
.preview-bar {
  background: var(--card-bg, #fff);
  border: 1px solid var(--border, #e2e8f0);
  border-radius: 10px;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}
.preview-label { font-size: 11px; font-weight: 700; color: var(--text-muted, #64748b); display: flex; align-items: center; gap: 6px; white-space: nowrap; }
.preview-menu  { display: flex; gap: 6px; flex-wrap: wrap; }
.preview-item  { display: flex; align-items: center; gap: 6px; padding: 5px 12px; border-radius: 7px; background: var(--input-bg, #f1f5f9); font-size: 12px; color: var(--text-main, #374151); }
.preview-item.pending { opacity: 0.5; }
.preview-plan-tag { font-size: 9px; font-weight: 700; background: rgba(59,130,246,0.12); color: #2563eb; padding: 1px 5px; border-radius: 8px; }
.preview-soon { font-size: 9px; font-weight: 700; background: rgba(245,158,11,0.15); color: #d97706; padding: 1px 5px; border-radius: 8px; }
.preview-empty { font-size: 12px; color: var(--text-muted, #94a3b8); font-style: italic; }

/* Tabla */
.table-card { background: var(--card-bg, #fff); border-radius: 12px; border: 1px solid var(--border, #e2e8f0); overflow: hidden; }
.loading-state { display: flex; align-items: center; gap: 12px; padding: 40px; justify-content: center; color: var(--text-muted, #64748b); }
.spinner { width: 22px; height: 22px; border: 3px solid rgba(0,0,0,0.1); border-top-color: #6366f1; border-radius: 50%; animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { padding: 10px 14px; text-align: left; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.4px; color: var(--text-muted, #94a3b8); background: var(--input-bg, #f8fafc); border-bottom: 1px solid var(--border, #e2e8f0); }
.data-table td { padding: 11px 14px; border-bottom: 1px solid var(--border, #f1f5f9); color: var(--text-main, #374151); vertical-align: middle; }
.data-table tbody tr:last-child td { border-bottom: none; }
.row-inactive td { opacity: 0.45; }

.col-order  { width: 64px; }
.col-icon   { width: 56px; }
.col-center { text-align: center; }
.col-act    { width: 90px; }

.order-btns { display: flex; flex-direction: column; gap: 2px; align-items: center; }
.btn-order  { background: none; border: 1px solid var(--border, #e2e8f0); border-radius: 4px; padding: 1px 5px; cursor: pointer; font-size: 11px; color: var(--text-muted, #94a3b8); line-height: 1; }
.btn-order:disabled { opacity: 0.3; cursor: default; }
.btn-order:not(:disabled):hover { background: var(--input-bg, #f1f5f9); }

.icon-preview { width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; background: var(--input-bg, #f1f5f9); border-radius: 8px; font-size: 16px; }

.td-name  { font-weight: 600; }
.td-key   { font-size: 11px; background: var(--input-bg, #f1f5f9); padding: 2px 7px; border-radius: 4px; color: #6366f1; font-family: monospace; }
.td-route .route-tag { font-size: 11px; background: rgba(34,197,94,0.1); color: #16a34a; padding: 2px 7px; border-radius: 4px; font-family: monospace; }
.td-route .no-route  { color: var(--text-muted, #94a3b8); font-size: 13px; }

.ev-yes { color: #22c55e; font-size: 16px; }
.ev-no  { color: var(--text-muted, #cbd5e1); font-size: 16px; }

.plan-tag  { font-size: 11px; font-weight: 700; background: rgba(59,130,246,0.12); color: #2563eb; padding: 2px 8px; border-radius: 10px; }
.all-plans { font-size: 11px; color: var(--text-muted, #94a3b8); }

/* Toggle switch */
.toggle-btn {
  width: 40px; height: 22px;
  border-radius: 11px;
  border: none;
  cursor: pointer;
  position: relative;
  transition: background 0.2s;
  flex-shrink: 0;
}
.toggle-on  { background: #22c55e; }
.toggle-off { background: #cbd5e1; }
.toggle-knob {
  position: absolute;
  top: 3px;
  width: 16px; height: 16px;
  background: #fff;
  border-radius: 50%;
  transition: left 0.2s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.25);
}
.toggle-on  .toggle-knob { left: 21px; }
.toggle-off .toggle-knob { left: 3px;  }

.td-actions { display: flex; gap: 5px; justify-content: center; }
.btn-tbl-edit { padding: 5px 9px; border-radius: 6px; border: none; font-size: 13px; cursor: pointer; background: rgba(99,102,241,0.1); color: #6366f1; }
.btn-tbl-edit:hover { background: rgba(99,102,241,0.2); }
.btn-tbl-del  { padding: 5px 9px; border-radius: 6px; border: none; font-size: 13px; cursor: pointer; background: rgba(239,68,68,0.1); color: #ef4444; }
.btn-tbl-del:hover  { background: rgba(239,68,68,0.2); }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.55); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 16px; }
.modal-box { background: var(--card-bg, #fff); border-radius: 14px; width: 100%; max-width: 640px; max-height: 90vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden; }
.modal-header-bar { display: flex; align-items: center; justify-content: space-between; padding: 18px 20px; border-bottom: 1px solid var(--border, #e2e8f0); }
.modal-header-bar h2 { font-size: 17px; font-weight: 700; margin: 0; color: var(--text-main, #1e293b); }
.modal-body { padding: 20px; overflow-y: auto; flex: 1; display: flex; flex-direction: column; gap: 14px; }
.modal-footer-bar { display: flex; gap: 10px; padding: 14px 20px; border-top: 1px solid var(--border, #e2e8f0); justify-content: flex-end; }

.form-row { display: flex; gap: 12px; flex-wrap: wrap; }
.flex-1   { flex: 1; min-width: 160px; }
.form-group { display: flex; flex-direction: column; gap: 5px; }
.form-group label { font-size: 12px; font-weight: 600; color: var(--text-main, #374151); }
.req { color: #ef4444; }
.form-group input,
.form-group select { border: 1px solid var(--border, #d1d5db); border-radius: 7px; padding: 8px 11px; font-size: 13px; outline: none; background: var(--input-bg, #f9fafb); color: var(--text-main, #1e293b); transition: border-color 0.15s; }
.form-group input:focus,
.form-group select:focus { border-color: #6366f1; background: #fff; }
.has-error input { border-color: #ef4444; }
.error-msg { font-size: 11px; color: #ef4444; }
.field-hint { font-size: 10px; color: var(--text-muted, #94a3b8); }

.icon-input-row { display: flex; gap: 8px; align-items: center; }
.icon-input-row input { flex: 1; }
.icon-preview-sm { width: 34px; height: 34px; display: flex; align-items: center; justify-content: center; background: var(--input-bg, #f1f5f9); border-radius: 7px; font-size: 17px; flex-shrink: 0; }

.checkboxes-row { gap: 20px; align-items: center; padding: 4px 0; }
.check-label { display: flex; align-items: center; gap: 8px; font-size: 13px; cursor: pointer; color: var(--text-main, #374151); }
.check-label input { width: 15px; height: 15px; cursor: pointer; accent-color: #6366f1; }

.btn-primary   { display: flex; align-items: center; gap: 6px; padding: 9px 18px; background: #6366f1; color: #fff; border: none; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; }
.btn-primary:hover    { background: #4f46e5; }
.btn-primary:disabled { background: #94a3b8; cursor: default; }
.btn-secondary { padding: 9px 18px; background: var(--input-bg, #f1f5f9); border: 1px solid var(--border, #e2e8f0); border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; color: var(--text-main, #374151); }
.btn-secondary:hover { background: #e2e8f0; }
.btn-close-x   { background: none; border: none; font-size: 16px; cursor: pointer; color: var(--text-muted, #94a3b8); padding: 4px; }
.btn-close-x:hover { color: #ef4444; }

@media (max-width: 768px) {
  .page-wrap { padding: 14px; }
  .data-table .td-route, .data-table .col-icon { display: none; }
}
</style>
