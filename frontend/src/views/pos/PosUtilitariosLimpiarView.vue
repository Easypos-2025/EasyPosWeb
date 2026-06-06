<template>
  <div class="crud-view">
    <div class="crud-header">
      <div>
        <h5 class="crud-titulo">Utilitarios Temporales</h5>
        <p class="crud-sub">Control y auditoría de tablas temporales del servidor</p>
      </div>
    </div>

    <!-- Tabs -->
    <div class="util-tabs">
      <button class="util-tab" :class="{ active: tab === 'limpiar' }" @click="tab = 'limpiar'">
        <i class="bi bi-trash3 me-1"></i>Limpiar
      </button>
      <button class="util-tab" :class="{ active: tab === 'historico' }" @click="tab = 'historico'; cargarHistorico()">
        <i class="bi bi-clock-history me-1"></i>Histórico
      </button>
    </div>

    <!-- ══════════════ TAB: LIMPIAR ══════════════ -->
    <template v-if="tab === 'limpiar'">

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

      <!-- Panel: tablas supervisadas + botón -->
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
          <button class="btn-ejecutar" :disabled="loading" @click="confirmar">
            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
            <i v-else class="bi bi-play-circle me-2"></i>
            Ejecutar limpieza
          </button>
        </div>
      </div>

      <!-- Modal confirmación -->
      <div v-if="showConfirm" class="modal-overlay" @click.self="showConfirm = false">
        <div class="modal-box">
          <div class="modal-box__icon"><i class="bi bi-exclamation-triangle-fill"></i></div>
          <h6>¿Confirmar limpieza de temporales?</h6>
          <p>Esta acción eliminará del servidor todos los registros huérfanos de las<br>
             {{ tablas.length }} tablas temporales listadas.<br>
             <strong>No afecta pedidos activos ni datos del escritorio.</strong></p>
          <div class="modal-box__btns">
            <button class="btn-cancelar" @click="showConfirm = false">Cancelar</button>
            <button class="btn-confirmar" @click="ejecutar">Sí, limpiar</button>
          </div>
        </div>
      </div>

      <!-- Resultado -->
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
    </template>

    <!-- ══════════════ TAB: HISTÓRICO ══════════════ -->
    <template v-if="tab === 'historico'">

      <!-- Filtro fecha -->
      <div class="hist-filter card">
        <div class="hist-filter__inner">
          <div class="he-filter-group">
            <label class="he-label">Fecha</label>
            <CustomDatePicker v-model="histFecha" @update:modelValue="cargarHistorico" />
          </div>
          <button class="btn btn-primary btn-sm" @click="cargarHistorico" :disabled="histLoading">
            <i class="bi bi-search"></i> Buscar
          </button>
        </div>
        <div v-if="histOrders.length" class="hist-summary">
          <span class="he-chip">
            <i class="bi bi-archive me-1"></i>
            <strong>{{ histOrders.length }}</strong> pedidos archivados
          </span>
          <span class="he-chip he-chip--blue">
            <i class="bi bi-cash-stack me-1"></i>
            <strong>{{ fmt(histTotal) }}</strong> total comandado
          </span>
        </div>
      </div>

      <!-- Cargando -->
      <div v-if="histLoading" class="util-loading" style="padding:24px 0">
        <div class="spinner-border spinner-border-sm text-primary me-2"></div> Cargando historial...
      </div>

      <!-- Sin resultados -->
      <div v-else-if="!histLoading && !histOrders.length" class="he-empty">
        <i class="bi bi-inbox he-empty-icon"></i>
        <p class="he-empty-text">Sin registros archivados para {{ histFecha }}</p>
      </div>

      <!-- Lista -->
      <div v-else class="he-list">
        <div v-for="ord in histOrders" :key="ord.order_number"
             class="hist-card card"
             :class="{ 'hist-card--open': histExpandido === ord.order_number }">

          <!-- Cabecera -->
          <div class="hist-card-head" @click="histToggle(ord.order_number)">
            <div class="he-card-left">
              <span class="he-badge-mesa" :class="mesaBadgeClass(ord)">{{ ord.Mesa || '—' }}</span>
              <span class="he-order-num">{{ ord.order_number }}</span>
              <span class="he-hora">{{ ord.Hora }}</span>
            </div>
            <div class="he-card-center">
              <span v-if="ord.Mesero" class="hist-mesero">
                <i class="bi bi-person me-1"></i>{{ ord.Mesero }}
              </span>
              <span class="hist-reason-badge" :class="`reason-${ord.archive_reason}`">
                {{ reasonLabel(ord.archive_reason) }}
              </span>
            </div>
            <div class="he-card-right">
              <span class="he-valor">{{ fmt(ord.Valor) }}</span>
              <span class="he-items-count">{{ ord.commanded_items.length }} ítem{{ ord.commanded_items.length !== 1 ? 's' : '' }}</span>
              <i :class="histExpandido === ord.order_number ? 'bi bi-chevron-up' : 'bi bi-chevron-down'" class="he-chevron"></i>
            </div>
          </div>

          <!-- Detalle expandido -->
          <div v-if="histExpandido === ord.order_number" class="hist-detail">

            <!-- Badge eliminado -->
            <div v-if="ord.deletion" class="hist-deletion-banner">
              <i class="bi bi-person-x-fill me-2"></i>
              <strong>Eliminado por:</strong> {{ ord.deletion.quien || 'Desconocido' }}
              <span v-if="ord.deletion.motivo"> — <em>{{ ord.deletion.motivo }}</em></span>
            </div>

            <div class="hist-compare">
              <!-- Lado izquierdo: Comandado -->
              <div class="hist-col">
                <div class="hist-col__header hist-col__header--commanded">
                  <i class="bi bi-receipt me-1"></i>Comandado
                </div>
                <table class="he-table">
                  <thead>
                    <tr>
                      <th>Plato</th>
                      <th class="text-end">Cant.</th>
                      <th class="text-end">Valor</th>
                      <th>Novedad</th>
                      <th>Hora</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="it in ord.commanded_items.filter(i => i.Mostrar)" :key="it.Item">
                      <td>{{ it.Id_Plato }}</td>
                      <td class="text-end">{{ it.Cantidad }}</td>
                      <td class="text-end">{{ fmt(it.Valor) }}</td>
                      <td>{{ it.Novedad || '—' }}</td>
                      <td class="text-muted small">{{ it.Hora_Plato }}</td>
                    </tr>
                  </tbody>
                  <tfoot>
                    <tr>
                      <td colspan="2" class="text-end fw-bold">Total</td>
                      <td class="text-end fw-bold">{{ fmt(ord.Valor) }}</td>
                      <td colspan="2"></td>
                    </tr>
                  </tfoot>
                </table>
              </div>

              <!-- Lado derecho: Facturado -->
              <div class="hist-col">
                <div v-if="ord.invoice" class="hist-col__header hist-col__header--invoiced">
                  <i class="bi bi-file-earmark-check me-1"></i>
                  {{ ord.invoice.type === 'dian' ? 'Factura DIAN' : 'Recibo' }}
                  <span class="hist-inv-num"># {{ ord.invoice.number }}</span>
                </div>
                <div v-else class="hist-col__header hist-col__header--noinvoice">
                  <i class="bi bi-file-earmark-x me-1"></i>Sin factura / recibo
                </div>

                <table v-if="ord.invoice" class="he-table">
                  <thead>
                    <tr>
                      <th>Plato</th>
                      <th class="text-end">Cant.</th>
                      <th class="text-end">Valor</th>
                      <th>Notas</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="it in ord.invoice.items" :key="it.item"
                        :class="{ 'he-row-cortesia': it.complimentary }">
                      <td>{{ it.dish_id }}</td>
                      <td class="text-end">{{ it.quantity }}</td>
                      <td class="text-end">{{ fmt(it.amount) }}</td>
                      <td>{{ it.notes || '—' }}</td>
                    </tr>
                  </tbody>
                  <tfoot>
                    <tr>
                      <td colspan="2" class="text-end fw-bold">Total</td>
                      <td class="text-end fw-bold">{{ fmt(ord.invoice.amount) }}</td>
                      <td></td>
                    </tr>
                  </tfoot>
                </table>
                <div v-else class="hist-noinvoice-msg">
                  <i class="bi bi-info-circle me-1"></i>
                  Este pedido no tiene factura ni recibo registrado.
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/apis'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'

// ── State compartido ──────────────────────────────────────────
const tab = ref('limpiar')

// ── Tab Limpiar ───────────────────────────────────────────────
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
    // interceptor global maneja errores de auth
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
    await cargarEstado()
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || 'Error al ejecutar la limpieza'
  } finally {
    loading.value = false
  }
}

// ── Tab Histórico ─────────────────────────────────────────────
const hoy = new Date().toISOString().slice(0, 10)
const histFecha    = ref(hoy)
const histOrders   = ref([])
const histLoading  = ref(false)
const histExpandido = ref(null)

const histTotal = computed(() =>
  histOrders.value.reduce((s, o) => s + (o.Valor || 0), 0)
)

function fmt(val) {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  return new Intl.NumberFormat(user.locale || 'es-CO', {
    style: 'currency', currency: user.currency_code || 'COP', maximumFractionDigits: 0,
  }).format(val || 0)
}

function histToggle(np) {
  histExpandido.value = histExpandido.value === np ? null : np
}

function reasonLabel(reason) {
  const map = {
    sync_removed:  'Sync VB6',
    deleted:       'Eliminado',
    manual_cleanup:'Limpieza manual',
    cancelled:     'Cancelado',
  }
  return map[reason] || reason || '—'
}

function mesaBadgeClass(ord) {
  if (ord.deletion)                          return 'badge-mesa--deleted'
  if (ord.invoice?.type === 'dian')          return 'badge-mesa--dian'
  if (ord.invoice?.type === 'receipt')       return 'badge-mesa--receipt'
  return 'badge-mesa--orphan'
}

async function cargarHistorico() {
  if (tab.value !== 'historico') return
  histLoading.value  = true
  histExpandido.value = null
  histOrders.value   = []
  try {
    const res = await api.get('/pos/utilitarios/command-history', {
      params: { fecha: histFecha.value },
    })
    histOrders.value = res.data.orders || []
  } catch {
    // silencioso
  } finally {
    histLoading.value = false
  }
}

onMounted(cargarEstado)
</script>

<style scoped>
/* ── Tabs ── */
.util-tabs {
  display: flex; gap: 4px; margin-bottom: 16px;
  border-bottom: 2px solid #e2e8f0; padding-bottom: 0;
}
.util-tab {
  background: none; border: none; padding: 8px 20px;
  font-size: .88rem; font-weight: 600; color: #64748b; cursor: pointer;
  border-bottom: 2px solid transparent; margin-bottom: -2px;
  border-radius: 6px 6px 0 0; transition: color .15s, border-color .15s;
}
.util-tab:hover { color: #334155; }
.util-tab.active { color: #3b82f6; border-bottom-color: #3b82f6; }

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

/* ── Modal ── */
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

/* ── Resultado ── */
.util-resultado {
  margin-top: 14px; padding: 12px 16px; border-radius: 10px;
  font-size: .88rem; display: flex; align-items: center; gap: 8px;
}
.util-resultado--ok   { background: #d1fae5; color: #065f46; border: 1px solid #6ee7b7; }
.util-resultado--info { background: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe; }
.util-resultado--err  { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }

/* ── Histórico ── */
.hist-filter {
  border-radius: 10px; overflow: hidden; margin-bottom: 14px; padding: 12px 16px;
}
.hist-filter__inner { display: flex; flex-wrap: wrap; gap: 12px; align-items: flex-end; margin-bottom: 10px; }
.hist-summary { display: flex; flex-wrap: wrap; gap: 8px; }

.he-label { font-size: .78rem; color: var(--bs-secondary-color); font-weight: 600; }
.he-filter-group { display: flex; flex-direction: column; gap: 4px; }

.he-chip {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 5px 12px; border-radius: 20px; font-size: .82rem;
  background: #f1f5f9; color: #334155;
}
.he-chip--blue { background: #dbeafe; color: #1e40af; }

.he-empty { display: flex; flex-direction: column; align-items: center; padding: 48px 16px; color: var(--bs-secondary-color); }
.he-empty-icon { font-size: 3rem; margin-bottom: 12px; }
.he-empty-text { font-size: 1rem; }

.he-list { display: flex; flex-direction: column; gap: 8px; }

/* ── Hist card ── */
.hist-card { border-radius: 10px; overflow: hidden; border: 1.5px solid var(--bs-border-color); }
.hist-card--open { border-color: #3b82f6; }

.hist-card-head {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 14px; cursor: pointer; transition: background .15s;
}
.hist-card-head:hover { background: rgba(59,130,246,.04); }

.he-card-left  { display: flex; align-items: center; gap: 10px; min-width: 0; }
.he-card-center { flex: 1; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; padding: 0 8px; }
.he-card-right { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }

.he-badge-mesa {
  padding: 3px 10px; border-radius: 20px; font-size: .8rem; font-weight: 700; white-space: nowrap;
}
.badge-mesa--dian    { background: #dbeafe; color: #1e40af; }
.badge-mesa--receipt { background: #d1fae5; color: #065f46; }
.badge-mesa--deleted { background: #fee2e2; color: #991b1b; }
.badge-mesa--orphan  { background: #f3f4f6; color: #374151; }

.he-order-num { font-size: .78rem; color: var(--bs-secondary-color); overflow: hidden; text-overflow: ellipsis; max-width: 150px; white-space: nowrap; }
.he-hora { font-size: .8rem; color: var(--bs-secondary-color); white-space: nowrap; }

.hist-mesero { font-size: .82rem; color: #475569; }
.hist-reason-badge {
  font-size: .72rem; font-weight: 600; padding: 2px 8px; border-radius: 20px;
}
.reason-sync_removed   { background: #fef9c3; color: #854d0e; }
.reason-deleted        { background: #fee2e2; color: #991b1b; }
.reason-manual_cleanup { background: #ede9fe; color: #5b21b6; }
.reason-cancelled      { background: #ffedd5; color: #9a3412; }

.he-valor { font-weight: 700; font-size: .95rem; color: var(--bs-emphasis-color); }
.he-items-count { font-size: .78rem; color: var(--bs-secondary-color); white-space: nowrap; }
.he-chevron { color: var(--bs-secondary-color); font-size: .8rem; }

/* ── Detalle expandido ── */
.hist-detail { padding: 14px; border-top: 1px solid var(--bs-border-color); }

.hist-deletion-banner {
  background: #fee2e2; color: #991b1b; padding: 8px 14px;
  border-radius: 8px; font-size: .84rem; margin-bottom: 14px;
}

.hist-compare { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

.hist-col { border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden; }
.hist-col__header {
  padding: 8px 14px; font-size: .82rem; font-weight: 600;
  display: flex; align-items: center; gap: 4px;
}
.hist-col__header--commanded { background: #eff6ff; color: #1e40af; border-bottom: 1px solid #bfdbfe; }
.hist-col__header--invoiced  { background: #f0fdf4; color: #166534; border-bottom: 1px solid #bbf7d0; }
.hist-col__header--noinvoice { background: #f8fafc; color: #94a3b8; border-bottom: 1px solid #e2e8f0; }

.hist-inv-num { font-weight: 400; font-size: .78rem; margin-left: 6px; }

.hist-noinvoice-msg { padding: 20px 14px; font-size: .82rem; color: #94a3b8; text-align: center; }

.he-table { width: 100%; font-size: .82rem; border-collapse: collapse; }
.he-table th { font-size: .75rem; color: var(--bs-secondary-color); padding: 6px 10px; border-bottom: 1px solid var(--bs-border-color); white-space: nowrap; }
.he-table td { padding: 5px 10px; border-bottom: 1px solid var(--bs-border-color); vertical-align: top; }
.he-table tr:last-child td { border-bottom: none; }
.he-table tfoot td { padding: 6px 10px; background: #f8fafc; }
.he-row-cortesia td { color: #16a34a; background: #f0fdf4; }

/* ── Responsive tablet ── */
@media (max-width: 768px) {
  .util-card { flex-direction: column; }
  .util-card__action { width: 100%; }
  .btn-ejecutar { width: 100%; justify-content: center; }
  .util-table { font-size: .78rem; }
  .tbl-name code { font-size: .72rem; }
  .hist-compare { grid-template-columns: 1fr; }
  .he-card-center { width: 100%; padding: 0; }
  .he-order-num { max-width: 100px; }
  .he-table th:nth-child(4),
  .he-table td:nth-child(4),
  .he-table th:nth-child(5),
  .he-table td:nth-child(5) { display: none; }
}

/* ── Responsive móvil ── */
@media (max-width: 576px) {
  .util-card { padding: 14px; }
  .util-panel__header { font-size: .8rem; }
  .hist-filter__inner { flex-direction: column; align-items: stretch; }
  .hist-card-head { flex-wrap: wrap; gap: 8px; }
  .he-card-right { flex-wrap: wrap; gap: 4px; }
  .hist-compare { grid-template-columns: 1fr; gap: 12px; }
}
</style>
