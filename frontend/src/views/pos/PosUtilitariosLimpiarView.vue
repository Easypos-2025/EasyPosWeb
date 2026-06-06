<template>
  <div class="crud-view">
    <div class="crud-header">
      <div>
        <h5 class="crud-titulo">Utilitarios Temporales</h5>
        <p class="crud-sub">Control y limpieza de tablas temporales del servidor</p>
      </div>
    </div>

    <!-- Header acción -->
    <div class="util-action-bar">
      <button class="btn-refresh" :disabled="loadingStatus" @click="cargarEstado" title="Actualizar estado">
        <i class="bi" :class="loadingStatus ? 'bi-arrow-repeat spin' : 'bi-arrow-clockwise'"></i>
      </button>
    </div>

    <!-- Tabla de estado de tablas temp_ -->
    <div class="util-panel">
      <div class="util-panel__header">
        <i class="bi bi-table me-2"></i>Estado actual de tablas temporales
      </div>

      <div v-if="loadingStatus" class="util-loading">
        <div class="spinner-border spinner-border-sm text-primary me-2"></div> Cargando estado...
      </div>

      <table v-else class="util-table">
        <thead>
          <tr>
            <th>Tabla</th>
            <th>Descripción</th>
            <th class="text-end">Registros actuales</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in tablas" :key="t.name"
              :class="{ 'row-dirty': t.records > 0, 'row-clean': t.records === 0 }">
            <td class="tbl-name"><code>{{ t.name }}</code></td>
            <td class="tbl-label">{{ t.label }}</td>
            <td class="text-end">
              <span class="badge-count" :class="t.records > 0 ? 'badge-warn' : 'badge-ok'">
                {{ t.records.toLocaleString() }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Card info + botón ejecutar -->
    <div class="util-card">
      <div class="util-card__icon"><i class="bi bi-database-fill-check"></i></div>
      <div class="util-card__body">
        <h6>Tablas temporales bajo control</h6>
        <ul class="util-card__list">
          <li v-for="t in tablas" :key="t.name">
            <i class="bi bi-table text-primary"></i>
            <code>{{ t.name }}</code>
            <span class="tbl-desc">— {{ t.label }}</span>
          </li>
        </ul>
        <div class="util-card__nota">
          <i class="bi bi-shield-check me-1"></i>
          Solo se eliminan registros <strong>huérfanos</strong> de estas tablas temporales.
          Los datos del sistema de escritorio y las tablas de producción no se ven afectados.
        </div>
      </div>
      <div class="util-card__action">
        <button class="btn-ejecutar" :disabled="loadingStatus" @click="abrirModalLimpieza">
          <i class="bi bi-play-circle me-2"></i>
          Ejecutar limpieza
        </button>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════════════════
         MODAL PROGRESO LIMPIEZA
    ══════════════════════════════════════════════════════════ -->
    <div v-if="showModal" class="modal-overlay">
      <div class="modal-box">

        <!-- Encabezado -->
        <div class="modal-box__head">
          <div class="modal-box__icon">
            <i v-if="!cleanDone && !cleanError" class="bi bi-arrow-repeat spin text-primary"></i>
            <i v-else-if="cleanError"           class="bi bi-x-circle-fill text-danger"></i>
            <i v-else                            class="bi bi-check-circle-fill text-success"></i>
          </div>
          <h6 class="modal-box__title">
            <span v-if="!cleanDone && !cleanError">Ejecutando limpieza…</span>
            <span v-else-if="cleanError">Error en la limpieza</span>
            <span v-else>Limpieza completada</span>
          </h6>
        </div>

        <!-- Checklist de tablas -->
        <ul class="clean-checklist">
          <li v-for="t in cleanChecklist" :key="t.name" class="clean-item">
            <!-- Icono estado -->
            <span class="clean-icon">
              <span v-if="t.state === 'pending'"  class="ci-dot"></span>
              <span v-else-if="t.state === 'running'" class="spinner-border spinner-border-sm text-primary"></span>
              <i v-else-if="t.state === 'done'"   class="bi bi-check-circle-fill text-success"></i>
              <i v-else-if="t.state === 'error'"  class="bi bi-x-circle-fill text-danger"></i>
            </span>
            <!-- Info tabla -->
            <span class="clean-label">
              <code>{{ t.name }}</code>
              <span class="clean-desc">{{ t.label }}</span>
            </span>
            <!-- Resultado -->
            <span v-if="t.state === 'done'" class="clean-result">
              <span v-if="t.deleted > 0" class="badge-deleted">−{{ t.deleted }}</span>
              <span v-else class="badge-clean">OK</span>
            </span>
          </li>
        </ul>

        <!-- Total resultado -->
        <div v-if="cleanDone && !cleanError" class="clean-total"
             :class="totalEliminados > 0 ? 'clean-total--ok' : 'clean-total--info'">
          <i class="bi" :class="totalEliminados > 0 ? 'bi-check-circle-fill' : 'bi-info-circle-fill'"></i>
          <span v-if="totalEliminados > 0">
            {{ totalEliminados }} registro{{ totalEliminados !== 1 ? 's' : '' }} huérfano{{ totalEliminados !== 1 ? 's' : '' }} eliminado{{ totalEliminados !== 1 ? 's' : '' }}
          </span>
          <span v-else>No se encontraron registros huérfanos. Las tablas están limpias.</span>
        </div>

        <div v-if="cleanError" class="clean-total clean-total--err">
          <i class="bi bi-x-circle-fill"></i> {{ cleanError }}
        </div>

        <!-- Botón cerrar -->
        <div class="modal-box__footer">
          <button v-if="cleanDone || cleanError" class="btn-cerrar" @click="cerrarModal">
            <i class="bi bi-x-lg me-1"></i>Cerrar
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/apis'

// ── Estado general ────────────────────────────────────────────
const loadingStatus = ref(false)
const tablas        = ref([])

async function cargarEstado() {
  loadingStatus.value = true
  try {
    const res = await api.get('/api/pos/utilitarios/temp-status')
    tablas.value = res.data.tables
  } catch {
    // interceptor global maneja errores de auth
  } finally {
    loadingStatus.value = false
  }
}

// ── Modal progreso ────────────────────────────────────────────
const showModal      = ref(false)
const cleanDone      = ref(false)
const cleanError     = ref(null)
const cleanChecklist = ref([])

const totalEliminados = computed(() =>
  cleanChecklist.value.reduce((s, t) => s + (t.deleted || 0), 0)
)

function abrirModalLimpieza() {
  // Inicializar checklist con tablas en estado "pending"
  cleanChecklist.value = tablas.value.map(t => ({
    name:    t.name,
    label:   t.label,
    state:   'pending',
    deleted: 0,
  }))
  cleanDone.value  = false
  cleanError.value = null
  showModal.value  = true

  // Marcar todas como "running" (la API es una sola llamada)
  cleanChecklist.value.forEach(t => { t.state = 'running' })

  ejecutarLimpieza()
}

async function ejecutarLimpieza() {
  try {
    const res = await api.post('/api/pos/utilitarios/cleanup-temp')
    const byTable = {}
    for (const t of (res.data.tables || [])) byTable[t.name] = t.deleted

    cleanChecklist.value.forEach(t => {
      t.state   = 'done'
      t.deleted = byTable[t.name] ?? 0
    })
    cleanDone.value = true
    await cargarEstado()
  } catch (e) {
    cleanError.value = e.response?.data?.detail || 'Error al ejecutar la limpieza'
    cleanChecklist.value.forEach(t => { if (t.state === 'running') t.state = 'error' })
    cleanDone.value = true
  }
}

function cerrarModal() {
  showModal.value = false
}

onMounted(cargarEstado)
</script>

<style scoped>
/* ── Action bar ── */
.util-action-bar {
  display: flex; justify-content: flex-end; margin-bottom: 10px;
}

/* ── Panel tabla ── */
.util-panel {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
  overflow: hidden; margin-bottom: 16px;
}
.util-panel__header {
  background: #f8fafc; padding: 12px 18px; font-size: .85rem;
  font-weight: 600; color: #475569; border-bottom: 1px solid #e2e8f0;
}
.util-loading { padding: 20px 18px; font-size: .85rem; color: #64748b; display: flex; align-items: center; }

.util-table { width: 100%; border-collapse: collapse; font-size: .84rem; }
.util-table thead th {
  background: #f1f5f9; padding: 10px 14px;
  text-align: left; font-weight: 600; color: #475569;
  border-bottom: 1px solid #e2e8f0;
}
.util-table tbody tr { border-bottom: 1px solid #f1f5f9; transition: background .1s; }
.util-table tbody tr:hover { background: #f8fafc; }

.row-dirty td { color: #374151; }
.row-clean td { color: #9ca3af; }

.tbl-name { padding: 10px 14px; }
.tbl-name code { font-size: .78rem; background: #f1f5f9; padding: 2px 6px; border-radius: 4px; color: #1e40af; }
.tbl-label { padding: 10px 14px; color: #6b7280; }

.badge-count {
  display: inline-block; min-width: 36px; text-align: center;
  padding: 2px 10px; border-radius: 20px; font-size: .78rem; font-weight: 700;
}
.badge-warn { background: #fef3c7; color: #92400e; }
.badge-ok   { background: #d1fae5; color: #065f46; }

/* ── Card info + botón ── */
.util-card {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
  padding: 20px 24px; display: flex; gap: 18px; align-items: flex-start;
}
.util-card__icon {
  width: 48px; height: 48px; border-radius: 10px;
  background: #dbeafe; display: flex; align-items: center; justify-content: center;
  font-size: 1.5rem; color: #2563eb; flex-shrink: 0;
}
.util-card__body { flex: 1; }
.util-card__body h6 { font-weight: 700; margin-bottom: 8px; font-size: .92rem; }
.util-card__list { list-style: none; padding: 0; margin: 0 0 10px; display: flex; flex-direction: column; gap: 4px; }
.util-card__list li { font-size: .82rem; display: flex; align-items: center; gap: 8px; color: #374151; }
.util-card__list li code { font-size: .78rem; background: #f1f5f9; padding: 1px 5px; border-radius: 4px; color: #1e40af; }
.tbl-desc { color: #6b7280; }
.util-card__nota {
  font-size: .79rem; color: #334155;
  background: #f0fdf4; border-left: 3px solid #22c55e;
  border-radius: 0 6px 6px 0; padding: 7px 12px;
}
.util-card__action { flex-shrink: 0; display: flex; align-items: center; }

.btn-ejecutar {
  background: #e67e22; color: #fff; border: none; border-radius: 8px;
  padding: 10px 20px; font-size: .88rem; font-weight: 600;
  cursor: pointer; display: flex; align-items: center; transition: background .15s;
}
.btn-ejecutar:hover:not(:disabled) { background: #d35400; }
.btn-ejecutar:disabled { opacity: .6; cursor: not-allowed; }

.btn-refresh {
  background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 8px;
  width: 36px; height: 36px; display: flex; align-items: center; justify-content: center;
  cursor: pointer; font-size: 1rem; color: #475569; transition: background .15s;
}
.btn-refresh:hover:not(:disabled) { background: #e2e8f0; }

.spin { animation: spin .7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Modal overlay ── */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.45);
  display: flex; align-items: center; justify-content: center; z-index: 9999;
}
.modal-box {
  background: #fff; border-radius: 16px; padding: 28px 24px;
  max-width: 440px; width: 92%; box-shadow: 0 20px 60px rgba(0,0,0,.22);
}
.modal-box__head {
  display: flex; align-items: center; gap: 12px; margin-bottom: 20px;
}
.modal-box__icon { font-size: 1.8rem; line-height: 1; }
.modal-box__title { font-weight: 700; font-size: 1rem; margin: 0; }
.modal-box__footer { margin-top: 20px; display: flex; justify-content: flex-end; }

/* ── Checklist ── */
.clean-checklist {
  list-style: none; padding: 0; margin: 0;
  display: flex; flex-direction: column; gap: 0;
  border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden;
}
.clean-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px; border-bottom: 1px solid #f1f5f9;
  font-size: .84rem;
}
.clean-item:last-child { border-bottom: none; }

.clean-icon { width: 22px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.ci-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #d1d5db; display: inline-block;
}

.clean-label { flex: 1; display: flex; align-items: center; gap: 8px; min-width: 0; }
.clean-label code {
  font-size: .76rem; background: #f1f5f9; padding: 2px 6px;
  border-radius: 4px; color: #1e40af; white-space: nowrap;
}
.clean-desc { color: #6b7280; font-size: .79rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.clean-result { flex-shrink: 0; }
.badge-deleted {
  display: inline-block; padding: 2px 9px; border-radius: 20px;
  font-size: .76rem; font-weight: 700; background: #fee2e2; color: #991b1b;
}
.badge-clean {
  display: inline-block; padding: 2px 9px; border-radius: 20px;
  font-size: .76rem; font-weight: 700; background: #d1fae5; color: #065f46;
}

/* ── Total ── */
.clean-total {
  margin-top: 14px; padding: 10px 14px; border-radius: 10px;
  font-size: .86rem; display: flex; align-items: center; gap: 8px;
}
.clean-total--ok   { background: #d1fae5; color: #065f46; border: 1px solid #6ee7b7; }
.clean-total--info { background: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe; }
.clean-total--err  { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }

/* ── Botón cerrar ── */
.btn-cerrar {
  background: #3b82f6; color: #fff; border: none; border-radius: 8px;
  padding: 9px 22px; font-size: .88rem; font-weight: 600;
  cursor: pointer; display: flex; align-items: center; transition: background .15s;
}
.btn-cerrar:hover { background: #2563eb; }

/* ── Responsive tablet ── */
@media (max-width: 768px) {
  .util-card { flex-direction: column; }
  .util-card__action { width: 100%; }
  .btn-ejecutar { width: 100%; justify-content: center; }
  .util-table { font-size: .78rem; }
  .tbl-name code { font-size: .72rem; }
  .clean-desc { display: none; }
}

/* ── Responsive móvil ── */
@media (max-width: 576px) {
  .util-card { padding: 14px; }
  .util-panel__header { font-size: .8rem; }
  .modal-box { padding: 20px 16px; }
  .clean-item { padding: 9px 10px; }
  .clean-label code { font-size: .72rem; }
}
</style>
