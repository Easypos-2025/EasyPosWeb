<template>
  <div class="operarios-wrap">

    <!-- ══════════════ PANEL IZQUIERDO: Profesiones + % ══════════════ -->
    <div class="panel-left">
      <div class="panel-card">
        <div class="panel-head">
          <h6><i class="bi bi-percent"></i> Roles y Porcentajes de Pago</h6>
          <p class="panel-desc">
            Configura qué porcentaje del valor del servicio recibe cada rol.
            Los tres valores deben sumar exactamente 100%.
          </p>
        </div>

        <div v-if="loadingProfs" class="loading-center">
          <i class="bi bi-hourglass-split spin"></i> Cargando...
        </div>

        <div v-else-if="professions.length === 0" class="empty-msg">
          <i class="bi bi-people"></i>
          <p>Sin roles configurados. Crea roles en <strong>Configuración → Roles de Operario</strong>.</p>
        </div>

        <div v-else class="prof-list">
          <div
            v-for="p in professions" :key="p.id"
            class="prof-item"
            :class="{ editing: editingId === p.id }"
          >
            <div class="prof-header">
              <div class="prof-name-row">
                <span class="prof-name">{{ p.name }}</span>
                <span v-if="p.total_workers" class="prof-workers">
                  <i class="bi bi-people-fill"></i> {{ p.total_workers }} operario{{ p.total_workers !== 1 ? 's' : '' }}
                </span>
              </div>
              <button
                v-if="editingId !== p.id"
                class="btn-edit"
                @click="iniciarEdicion(p)"
              >
                <i class="bi bi-pencil-fill"></i> Editar %
              </button>
            </div>

            <!-- Vista normal -->
            <div v-if="editingId !== p.id" class="pct-display">
              <div class="pct-bar">
                <div
                  class="pct-seg operario"
                  :style="{ width: p.pct_operario + '%' }"
                  :title="`Operario: ${p.pct_operario}%`"
                ></div>
                <div
                  class="pct-seg jefe"
                  :style="{ width: p.pct_jefe + '%' }"
                  :title="`Jefe: ${p.pct_jefe}%`"
                ></div>
                <div
                  class="pct-seg negocio"
                  :style="{ width: p.pct_negocio + '%' }"
                  :title="`Negocio: ${p.pct_negocio}%`"
                ></div>
              </div>
              <div class="pct-labels">
                <span class="pct-lbl operario">
                  <i class="bi bi-person-fill"></i> Operario <strong>{{ p.pct_operario }}%</strong>
                </span>
                <span class="pct-lbl jefe">
                  <i class="bi bi-person-badge-fill"></i> Jefe <strong>{{ p.pct_jefe }}%</strong>
                </span>
                <span class="pct-lbl negocio">
                  <i class="bi bi-building-fill"></i> Negocio <strong>{{ p.pct_negocio }}%</strong>
                </span>
              </div>
            </div>

            <!-- Formulario edición -->
            <div v-else class="pct-edit-form">
              <div class="pct-inputs">
                <div class="pct-input-group">
                  <label class="pct-inp-lbl operario"><i class="bi bi-person-fill"></i> Operario %</label>
                  <input
                    v-model.number="editForm.pct_operario"
                    type="number" min="0" max="100" step="0.5"
                    class="pct-inp"
                    @input="recalcNegocio"
                  />
                </div>
                <div class="pct-input-group">
                  <label class="pct-inp-lbl jefe"><i class="bi bi-person-badge-fill"></i> Jefe %</label>
                  <input
                    v-model.number="editForm.pct_jefe"
                    type="number" min="0" max="100" step="0.5"
                    class="pct-inp"
                    @input="recalcNegocio"
                  />
                </div>
                <div class="pct-input-group">
                  <label class="pct-inp-lbl negocio"><i class="bi bi-building-fill"></i> Negocio %</label>
                  <input
                    v-model.number="editForm.pct_negocio"
                    type="number" min="0" max="100" step="0.5"
                    class="pct-inp readonly"
                    readonly
                  />
                </div>
              </div>
              <div :class="['pct-suma', sumaOk ? 'ok' : 'err']">
                Suma: <strong>{{ sumaActual }}%</strong>
                <template v-if="sumaOk"> ✓</template>
                <template v-else> — debe ser 100%</template>
              </div>

              <!-- Preview barra -->
              <div class="pct-bar preview">
                <div class="pct-seg operario" :style="{ width: editForm.pct_operario + '%' }"></div>
                <div class="pct-seg jefe"     :style="{ width: editForm.pct_jefe + '%' }"></div>
                <div class="pct-seg negocio"  :style="{ width: editForm.pct_negocio + '%' }"></div>
              </div>

              <!-- Ejemplo con valor de referencia -->
              <div class="pct-ejemplo">
                <span>Ejemplo — servicio de <strong>{{ fmt(50000) }}</strong>:</span>
                <span class="ej-operario">Operario: <strong>{{ fmt(50000 * editForm.pct_operario / 100) }}</strong></span>
                <span class="ej-jefe" v-if="editForm.pct_jefe > 0">Jefe: <strong>{{ fmt(50000 * editForm.pct_jefe / 100) }}</strong></span>
                <span class="ej-negocio">Negocio: <strong>{{ fmt(50000 * editForm.pct_negocio / 100) }}</strong></span>
              </div>

              <div class="edit-actions">
                <button class="btn-cancel-edit" @click="cancelarEdicion">Cancelar</button>
                <button
                  class="btn-save-edit"
                  :disabled="!sumaOk || savingId === p.id"
                  @click="guardarConfig(p)"
                >
                  <i v-if="savingId === p.id" class="bi bi-hourglass-split spin"></i>
                  <i v-else class="bi bi-check-lg"></i>
                  Guardar
                </button>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>

    <!-- ══════════════ PANEL DERECHO: Lista de operarios ══════════════ -->
    <div class="panel-right">
      <div class="panel-card">
        <div class="panel-head">
          <h6><i class="bi bi-people-fill"></i> Operarios</h6>
          <button class="btn-refresh" @click="cargarDatos" :disabled="loadingWorkers">
            <i :class="['bi bi-arrow-clockwise', { spin: loadingWorkers }]"></i>
          </button>
        </div>

        <div v-if="loadingWorkers" class="loading-center">
          <i class="bi bi-hourglass-split spin"></i>
        </div>

        <div v-else-if="workers.length === 0" class="empty-msg">
          <i class="bi bi-person-x"></i>
          <p>Sin operarios. Crea operarios en <strong>Configuración → Operarios</strong>.</p>
        </div>

        <template v-else>
          <!-- Resumen de pendientes de liquidar -->
          <div v-if="totalPendiente > 0" class="resumen-pendiente">
            <i class="bi bi-cash-coin"></i>
            Total pendiente de pago:
            <strong>{{ fmt(totalPendiente) }}</strong>
            · {{ totalItemsPendientes }} servicio{{ totalItemsPendientes !== 1 ? 's' : '' }}
          </div>

          <div class="workers-list">
            <div
              v-for="w in workers" :key="w.id"
              class="worker-item"
              :class="{ 'has-pending': w.monto_pendiente > 0 }"
            >
              <div class="worker-avatar">{{ initials(w.name) }}</div>
              <div class="worker-info">
                <span class="worker-name">{{ w.name }}</span>
                <span class="worker-prof">{{ w.profession_nombre || 'Sin rol asignado' }}</span>
                <span v-if="w.phone" class="worker-phone">
                  <i class="bi bi-telephone-fill"></i> {{ w.phone }}
                </span>
              </div>
              <div class="worker-right">
                <div v-if="w.profession_id" class="worker-pct">
                  <span class="pct-mini operario">{{ w.pct_operario }}%</span>
                </div>
                <div v-if="w.monto_pendiente > 0" class="worker-pending">
                  <span class="pending-label">Por liquidar</span>
                  <span class="pending-amount">{{ fmt(w.monto_pendiente) }}</span>
                  <span class="pending-items">{{ w.items_pendientes }} ítem{{ w.items_pendientes !== 1 ? 's' : '' }}</span>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Toast -->
    <Teleport to="body">
      <div v-if="toast.visible" :class="['toast-msg', `toast-${toast.tipo}`]">
        <i :class="toast.tipo === 'ok' ? 'bi bi-check-circle-fill' : 'bi bi-exclamation-triangle-fill'"></i>
        {{ toast.msg }}
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useCompanyStore } from '@/stores/companyStore'
import api from '@/services/apis'

const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id)

// ── Profesiones ───────────────────────────────────────────────────────────
const professions  = ref([])
const loadingProfs = ref(false)
const editingId    = ref(null)
const savingId     = ref(null)
const editForm     = ref({ pct_operario: 0, pct_jefe: 0, pct_negocio: 100 })

const sumaActual = computed(() =>
  +(editForm.value.pct_operario + editForm.value.pct_jefe + editForm.value.pct_negocio).toFixed(2)
)
const sumaOk = computed(() => Math.abs(sumaActual.value - 100) < 0.06)

function recalcNegocio() {
  const n = 100 - (editForm.value.pct_operario || 0) - (editForm.value.pct_jefe || 0)
  editForm.value.pct_negocio = Math.max(0, Math.round(n * 100) / 100)
}

function iniciarEdicion(p) {
  editingId.value = p.id
  editForm.value  = { pct_operario: p.pct_operario, pct_jefe: p.pct_jefe, pct_negocio: p.pct_negocio }
}

function cancelarEdicion() { editingId.value = null }

async function guardarConfig(p) {
  if (!sumaOk.value) return
  savingId.value = p.id
  try {
    await api.put(`/api/talleres/profession-config/${p.id}`, {
      company_id:   companyId.value,
      pct_operario: editForm.value.pct_operario,
      pct_jefe:     editForm.value.pct_jefe,
      pct_negocio:  editForm.value.pct_negocio,
    })
    // Actualizar local
    const idx = professions.value.findIndex(x => x.id === p.id)
    if (idx >= 0) Object.assign(professions.value[idx], { ...editForm.value })
    editingId.value = null
    mostrarToast(`Porcentajes de "${p.name}" actualizados`, 'ok')
    await cargarWorkers()
  } catch (e) {
    mostrarToast(e?.response?.data?.detail ?? 'Error al guardar', 'error')
  } finally {
    savingId.value = null
  }
}

// ── Workers ───────────────────────────────────────────────────────────────
const workers      = ref([])
const loadingWorkers = ref(false)

const totalPendiente     = computed(() => workers.value.reduce((s, w) => s + (w.monto_pendiente || 0), 0))
const totalItemsPendientes = computed(() => workers.value.reduce((s, w) => s + (w.items_pendientes || 0), 0))

async function cargarProfessions() {
  if (!companyId.value) return
  loadingProfs.value = true
  try {
    const { data } = await api.get('/api/talleres/profession-config', {
      params: { company_id: companyId.value }
    })
    professions.value = data
  } catch { professions.value = [] } finally { loadingProfs.value = false }
}

async function cargarWorkers() {
  if (!companyId.value) return
  loadingWorkers.value = true
  try {
    const { data } = await api.get('/api/talleres/workers-con-config', {
      params: { company_id: companyId.value }
    })
    workers.value = data
  } catch { workers.value = [] } finally { loadingWorkers.value = false }
}

async function cargarDatos() { await Promise.all([cargarProfessions(), cargarWorkers()]) }

onMounted(cargarDatos)

// ── Helpers ───────────────────────────────────────────────────────────────
function initials(name) {
  return (name || '?').split(' ').slice(0, 2).map(s => s[0]).join('').toUpperCase()
}
function fmt(v) {
  if (v == null) return '—'
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v)
}

const toast = ref({ visible: false, msg: '', tipo: 'ok' })
function mostrarToast(msg, tipo = 'ok') {
  toast.value = { visible: true, msg, tipo }
  setTimeout(() => { toast.value.visible = false }, 3500)
}
</script>

<style scoped>
/* ── Layout ── */
.operarios-wrap {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 20px;
  align-items: start;
}

/* ── Panel card ── */
.panel-card {
  background: #fff; border: 1.5px solid #e2e8f0; border-radius: 14px;
  padding: 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.panel-head {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 10px; margin-bottom: 14px; padding-bottom: 12px; border-bottom: 1px solid #f1f5f9;
}
.panel-head h6 {
  margin: 0; font-size: 14px; font-weight: 700; color: #1e3a5f;
  display: flex; align-items: center; gap: 7px;
}
.panel-desc { font-size: 12px; color: #64748b; margin: 4px 0 0; }
.btn-refresh {
  background: #f1f5f9; border: none; border-radius: 8px; width: 30px; height: 30px;
  cursor: pointer; color: #64748b; font-size: 14px; display: flex; align-items: center; justify-content: center;
}
.btn-refresh:hover { background: #e2e8f0; }

/* ── Loading / empty ── */
.loading-center { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 32px; color: #94a3b8; }
.empty-msg {
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  padding: 32px 20px; color: #94a3b8; text-align: center;
}
.empty-msg .bi { font-size: 36px; color: #cbd5e1; }
.empty-msg p  { font-size: 13px; margin: 0; }

/* ── Lista de profesiones ── */
.prof-list { display: flex; flex-direction: column; gap: 12px; }

.prof-item {
  border: 1.5px solid #e2e8f0; border-radius: 12px; padding: 14px;
  transition: all 0.2s;
}
.prof-item.editing { border-color: #1e3a5f; box-shadow: 0 0 0 3px rgba(30,58,95,0.08); }

.prof-header { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 10px; }
.prof-name-row { display: flex; align-items: center; gap: 8px; }
.prof-name    { font-size: 14px; font-weight: 700; color: #1e3a5f; }
.prof-workers { font-size: 11px; color: #64748b; background: #f1f5f9; border-radius: 20px; padding: 1px 8px; }
.btn-edit {
  display: flex; align-items: center; gap: 5px;
  background: #f1f5f9; border: none; border-radius: 8px;
  padding: 5px 12px; font-size: 12px; font-weight: 600; color: #64748b;
  cursor: pointer; white-space: nowrap;
}
.btn-edit:hover { background: #e2e8f0; color: #1e3a5f; }

/* ── Barra de porcentaje ── */
.pct-bar {
  height: 10px; border-radius: 6px; overflow: hidden;
  display: flex; background: #f1f5f9; margin-bottom: 8px;
}
.pct-bar.preview { height: 8px; margin: 8px 0; }
.pct-seg { transition: width 0.3s; }
.pct-seg.operario { background: #3b82f6; }
.pct-seg.jefe     { background: #f59e0b; }
.pct-seg.negocio  { background: #94a3b8; }

.pct-labels { display: flex; flex-wrap: wrap; gap: 8px; }
.pct-lbl {
  display: flex; align-items: center; gap: 4px; font-size: 12px; color: #475569;
}
.pct-lbl.operario .bi { color: #3b82f6; }
.pct-lbl.jefe     .bi { color: #f59e0b; }
.pct-lbl.negocio  .bi { color: #94a3b8; }
.pct-lbl strong { color: #0f172a; }

/* ── Formulario edición % ── */
.pct-inputs { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 6px; }
.pct-input-group { display: flex; flex-direction: column; gap: 4px; }
.pct-inp-lbl {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.4px; display: flex; align-items: center; gap: 4px;
}
.pct-inp-lbl.operario { color: #3b82f6; }
.pct-inp-lbl.jefe     { color: #d97706; }
.pct-inp-lbl.negocio  { color: #64748b; }
.pct-inp {
  border: 1.5px solid #e2e8f0; border-radius: 8px;
  padding: 7px 10px; font-size: 16px; font-weight: 700; color: #1e3a5f;
  text-align: center; outline: none; transition: border-color 0.2s;
}
.pct-inp:focus { border-color: #1e3a5f; }
.pct-inp.readonly { background: #f8fafc; color: #94a3b8; cursor: not-allowed; }

.pct-suma { font-size: 12px; font-weight: 600; margin-bottom: 4px; }
.pct-suma.ok  { color: #16a34a; }
.pct-suma.err { color: #dc2626; }

.pct-ejemplo {
  display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
  background: #f8fafc; border-radius: 8px; padding: 8px 10px;
  font-size: 12px; color: #64748b; margin-top: 6px;
}
.ej-operario { color: #1d4ed8; }
.ej-jefe     { color: #d97706; }
.ej-negocio  { color: #64748b; }

.edit-actions {
  display: flex; justify-content: flex-end; gap: 8px; margin-top: 12px;
  padding-top: 10px; border-top: 1px solid #f1f5f9;
}
.btn-cancel-edit {
  background: #f1f5f9; border: none; border-radius: 8px;
  padding: 7px 16px; font-size: 13px; font-weight: 600; color: #64748b; cursor: pointer;
}
.btn-cancel-edit:hover { background: #e2e8f0; }
.btn-save-edit {
  display: flex; align-items: center; gap: 6px;
  background: #1e3a5f; color: #fff; border: none; border-radius: 8px;
  padding: 7px 18px; font-size: 13px; font-weight: 700; cursor: pointer;
}
.btn-save-edit:hover:not(:disabled) { background: #2d4f80; }
.btn-save-edit:disabled { opacity: 0.5; cursor: default; }

/* ── Workers ── */
.resumen-pendiente {
  display: flex; align-items: center; gap: 7px; flex-wrap: wrap;
  background: #fef3c7; border: 1px solid #fcd34d; border-radius: 8px;
  padding: 8px 12px; font-size: 13px; color: #92400e; margin-bottom: 12px;
}
.resumen-pendiente .bi { color: #d97706; }

.workers-list { display: flex; flex-direction: column; gap: 8px; }

.worker-item {
  display: flex; align-items: center; gap: 10px;
  border: 1.5px solid #f1f5f9; border-radius: 10px; padding: 10px 12px;
}
.worker-item.has-pending { border-color: #fcd34d; background: #fffbeb; }

.worker-avatar {
  width: 38px; height: 38px; border-radius: 50%; background: #1e3a5f;
  color: #fff; font-size: 14px; font-weight: 700; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
}
.worker-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px; }
.worker-name { font-size: 13px; font-weight: 700; color: #1e3a5f; }
.worker-prof { font-size: 11px; color: #64748b; }
.worker-phone { font-size: 11px; color: #94a3b8; display: flex; align-items: center; gap: 3px; }

.worker-right { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; flex-shrink: 0; }
.pct-mini {
  font-size: 13px; font-weight: 800; background: #dbeafe;
  color: #1d4ed8; border-radius: 20px; padding: 1px 8px;
}
.worker-pending { display: flex; flex-direction: column; align-items: flex-end; gap: 1px; }
.pending-label  { font-size: 9px; font-weight: 700; color: #d97706; text-transform: uppercase; }
.pending-amount { font-size: 14px; font-weight: 800; color: #92400e; }
.pending-items  { font-size: 10px; color: #94a3b8; }

/* ── Toast ── */
.toast-msg {
  position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
  display: flex; align-items: center; gap: 8px; padding: 12px 20px;
  border-radius: 10px; font-size: 14px; font-weight: 600; z-index: 9999;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15); animation: slideInUp 0.3s ease;
}
.toast-ok    { background: #1e3a5f; color: #fff; }
.toast-error { background: #dc2626; color: #fff; }
@keyframes slideInUp { from { opacity: 0; transform: translateX(-50%) translateY(10px); } to { opacity: 1; transform: translateX(-50%) translateY(0); } }

.spin { display: inline-block; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Responsive ── */
@media (max-width: 1024px) {
  .operarios-wrap { grid-template-columns: 1fr; }
}
@media (max-width: 768px) {
  .pct-inputs { grid-template-columns: 1fr 1fr; }
  .pct-ejemplo { flex-direction: column; gap: 4px; }
  .panel-head { flex-direction: column; align-items: flex-start; }
}
@media (max-width: 576px) {
  .pct-inputs { grid-template-columns: 1fr; }
  .worker-item { flex-wrap: wrap; }
}
</style>
