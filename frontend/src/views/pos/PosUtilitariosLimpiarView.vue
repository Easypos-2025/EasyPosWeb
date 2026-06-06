<template>
  <div class="crud-view">
    <div class="crud-header">
      <div>
        <h5 class="crud-titulo">Limpiar Temporales</h5>
        <p class="crud-sub">Elimina del servidor los pedidos que ya no existen en el sistema de escritorio</p>
      </div>
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
            <th v-if="resultado" class="text-end">Eliminados</th>
            <th v-if="resultado" class="text-center">Estado</th>
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
            <td v-if="resultado" class="text-end">
              <span class="badge-count badge-deleted">
                {{ (resultado.byTable[t.name] ?? 0).toLocaleString() }}
              </span>
            </td>
            <td v-if="resultado" class="text-center">
              <i v-if="(resultado.byTable[t.name] ?? 0) > 0"
                 class="bi bi-check-circle-fill text-success"></i>
              <i v-else class="bi bi-dash-circle text-muted"></i>
            </td>
          </tr>
        </tbody>
        <tfoot v-if="resultado">
          <tr class="tbl-total">
            <td colspan="2"><strong>Total eliminados</strong></td>
            <td></td>
            <td class="text-end">
              <strong>{{ (resultado.deleted_headers + resultado.deleted_details).toLocaleString() }}</strong>
            </td>
            <td></td>
          </tr>
        </tfoot>
      </table>
    </div>

    <!-- Descripción + botón -->
    <div class="util-card">
      <div class="util-card__icon"><i class="bi bi-trash3-fill"></i></div>
      <div class="util-card__body">
        <h6>¿Qué se elimina?</h6>
        <ul class="util-card__list">
          <li><i class="bi bi-check2-circle text-success"></i> Pedidos con estado Cancelado</li>
          <li><i class="bi bi-check2-circle text-success"></i> Pedidos en histórico de eliminados</li>
          <li><i class="bi bi-check2-circle text-success"></i> Pedidos facturados (factura / recibo)</li>
          <li><i class="bi bi-check2-circle text-success"></i> Pedidos que ya no llegan en el ciclo de sync</li>
        </ul>
        <div class="util-card__nota">
          <i class="bi bi-info-circle"></i>
          Los pedidos web (canal online) <strong>no se verán afectados</strong>.
          Esta operación es segura e idempotente.
        </div>
      </div>
      <div class="util-card__action">
        <button class="btn-ejecutar" :disabled="loading" @click="confirmar">
          <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
          <i v-else class="bi bi-play-circle me-2"></i>
          Ejecutar limpieza
        </button>
      </div>
    </div>

    <!-- Modal confirmación -->
    <div v-if="showConfirm" class="modal-overlay" @click.self="showConfirm=false">
      <div class="modal-box">
        <div class="modal-box__icon"><i class="bi bi-exclamation-triangle-fill"></i></div>
        <h6>¿Confirmar limpieza de temporales?</h6>
        <p>Esta acción eliminará del servidor web todos los pedidos huérfanos.<br>
           <strong>No afecta pedidos activos ni datos del escritorio.</strong></p>
        <div class="modal-box__btns">
          <button class="btn-cancelar" @click="showConfirm=false">Cancelar</button>
          <button class="btn-confirmar" @click="ejecutar">Sí, limpiar</button>
        </div>
      </div>
    </div>

    <!-- Alerta resultado -->
    <div v-if="resultado" class="util-resultado"
         :class="(resultado.deleted_headers + resultado.deleted_details) > 0 ? 'util-resultado--ok' : 'util-resultado--info'">
      <i class="bi" :class="(resultado.deleted_headers + resultado.deleted_details) > 0
        ? 'bi-check-circle-fill' : 'bi-info-circle-fill'"></i>
      <span v-if="(resultado.deleted_headers + resultado.deleted_details) > 0">
        Limpieza completada —
        <strong>{{ resultado.deleted_headers }} cabeceras</strong> y
        <strong>{{ resultado.deleted_details }} registros de detalle</strong> eliminados.
      </span>
      <span v-else>No se encontraron registros huérfanos. Las tablas están limpias.</span>
    </div>

    <div v-if="errorMsg" class="util-resultado util-resultado--err">
      <i class="bi bi-x-circle-fill"></i> {{ errorMsg }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/apis'

const loadingStatus = ref(false)
const loading       = ref(false)
const showConfirm   = ref(false)
const tablas        = ref([])
const resultado     = ref(null)
const errorMsg      = ref(null)

async function cargarEstado() {
  loadingStatus.value = true
  try {
    const res = await api.get('/pos/utilitarios/temp-status')
    tablas.value = res.data.tables
  } catch {
    // silencioso — el error de auth lo maneja el interceptor global
  } finally {
    loadingStatus.value = false
  }
}

function confirmar() {
  resultado.value = null
  errorMsg.value  = null
  showConfirm.value = true
}

async function ejecutar() {
  showConfirm.value = false
  loading.value = true
  resultado.value = null
  errorMsg.value  = null
  try {
    const res = await api.post('/pos/utilitarios/cleanup-temp')
    const byTable = {}
    for (const t of (res.data.tables || [])) byTable[t.name] = t.deleted
    resultado.value = {
      deleted_headers: res.data.deleted_headers ?? 0,
      deleted_details: res.data.deleted_details  ?? 0,
      byTable,
    }
    // Recargar estado actualizado
    await cargarEstado()
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || 'Error al ejecutar la limpieza'
  } finally {
    loading.value = false
  }
}

onMounted(cargarEstado)
</script>

<style scoped>
/* Panel tabla */
.util-panel {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 16px;
}
.util-panel__header {
  background: #f8fafc;
  padding: 12px 18px;
  font-size: .85rem;
  font-weight: 600;
  color: #475569;
  border-bottom: 1px solid #e2e8f0;
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
.util-table tfoot .tbl-total { background: #f8fafc; border-top: 2px solid #e2e8f0; }
.util-table tfoot td { padding: 10px 14px; font-size: .84rem; }

.row-dirty td { color: #374151; }
.row-clean td { color: #9ca3af; }

.tbl-name { padding: 10px 14px; }
.tbl-name code { font-size: .78rem; background: #f1f5f9; padding: 2px 6px; border-radius: 4px; color: #1e40af; }
.tbl-label { padding: 10px 14px; color: #6b7280; }

.badge-count {
  display: inline-block; min-width: 36px; text-align: center;
  padding: 2px 10px; border-radius: 20px; font-size: .78rem; font-weight: 700;
}
.badge-warn    { background: #fef3c7; color: #92400e; }
.badge-ok      { background: #d1fae5; color: #065f46; }
.badge-deleted { background: #fee2e2; color: #991b1b; }

/* Card info + botón */
.util-card {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
  padding: 20px 24px; display: flex; gap: 18px; align-items: flex-start;
}
.util-card__icon {
  width: 48px; height: 48px; border-radius: 10px;
  background: #fff3cd; display: flex; align-items: center; justify-content: center;
  font-size: 1.5rem; color: #e67e22; flex-shrink: 0;
}
.util-card__body { flex: 1; }
.util-card__body h6 { font-weight: 700; margin-bottom: 8px; font-size: .92rem; }
.util-card__list { list-style: none; padding: 0; margin: 0 0 10px; display: flex; flex-direction: column; gap: 3px; }
.util-card__list li { font-size: .82rem; display: flex; align-items: center; gap: 6px; color: #374151; }
.util-card__nota {
  font-size: .79rem; color: #6b7280;
  background: #f8fafc; border-left: 3px solid #3b82f6;
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

/* Modal */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.45);
  display: flex; align-items: center; justify-content: center; z-index: 9999;
}
.modal-box {
  background: #fff; border-radius: 14px; padding: 32px 28px;
  max-width: 420px; width: 90%; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,.2);
}
.modal-box__icon { font-size: 2.4rem; color: #e67e22; margin-bottom: 12px; }
.modal-box h6 { font-weight: 700; font-size: 1rem; margin-bottom: 8px; }
.modal-box p  { font-size: .87rem; color: #64748b; margin-bottom: 20px; }
.modal-box__btns { display: flex; gap: 10px; justify-content: center; }
.btn-cancelar  { padding: 9px 22px; border: 1px solid #d1d5db; border-radius: 8px; background: #fff; cursor: pointer; font-size: .88rem; }
.btn-confirmar { padding: 9px 22px; border: none; border-radius: 8px; background: #e67e22; color: #fff; font-weight: 600; cursor: pointer; font-size: .88rem; }
.btn-confirmar:hover { background: #d35400; }

/* Resultado */
.util-resultado {
  margin-top: 14px; padding: 12px 16px; border-radius: 10px;
  font-size: .88rem; display: flex; align-items: center; gap: 8px;
}
.util-resultado--ok   { background: #d1fae5; color: #065f46; border: 1px solid #6ee7b7; }
.util-resultado--info { background: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe; }
.util-resultado--err  { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }

/* Responsive */
@media (max-width: 768px) {
  .util-card { flex-direction: column; }
  .util-card__action { width: 100%; }
  .btn-ejecutar { width: 100%; justify-content: center; }
  .util-table { font-size: .78rem; }
  .tbl-name code { font-size: .72rem; }
}
@media (max-width: 576px) {
  .util-card { padding: 14px; }
  .util-panel__header { font-size: .8rem; }
}
</style>
