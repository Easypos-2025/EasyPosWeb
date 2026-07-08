<template>
  <div class="page-container">

    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title"><i class="bi bi-cash-stack"></i> Cierre de Caja</h1>
        <p class="page-subtitle">Resumen diario de ingresos, egresos y saldo neto.</p>
      </div>
      <div class="header-actions">
        <CustomDatePicker v-model="fechaSel" @update:modelValue="cargar" />
        <button class="btn btn-outline" @click="cargar" title="Actualizar">
          <i class="bi bi-arrow-clockwise"></i>
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading-center">
      <i class="bi bi-arrow-repeat spin"></i> Cargando resumen…
    </div>

    <template v-else>

      <!-- KPI Bar -->
      <div class="kpi-bar">
        <div class="kpi-card kpi-green">
          <div class="kpi-icon-w"><i class="bi bi-arrow-down-circle-fill"></i></div>
          <div class="kpi-body">
            <span class="kpi-val">{{ fmt(resumen.ingresos?.ingresos_efectivo) }}</span>
            <span class="kpi-lbl">Ingresos Efectivo</span>
          </div>
        </div>
        <div class="kpi-card kpi-blue">
          <div class="kpi-icon-w"><i class="bi bi-building-fill"></i></div>
          <div class="kpi-body">
            <span class="kpi-val">{{ fmt(resumen.ingresos?.ingresos_convenio) }}</span>
            <span class="kpi-lbl">Ingresos Convenio (CxC)</span>
          </div>
        </div>
        <div class="kpi-card kpi-red">
          <div class="kpi-icon-w"><i class="bi bi-arrow-up-circle-fill"></i></div>
          <div class="kpi-body">
            <span class="kpi-val">{{ fmt(resumen.total_egresos) }}</span>
            <span class="kpi-lbl">Total Egresos</span>
          </div>
        </div>
        <div class="kpi-card" :class="resumen.saldo_neto >= 0 ? 'kpi-green' : 'kpi-red'">
          <div class="kpi-icon-w"><i class="bi bi-wallet2"></i></div>
          <div class="kpi-body">
            <span class="kpi-val">{{ fmt(resumen.saldo_neto) }}</span>
            <span class="kpi-lbl">Saldo Neto en Caja</span>
          </div>
        </div>
      </div>

      <!-- Grid principal -->
      <div class="caja-grid">

        <!-- COLUMNA IZQUIERDA -->
        <div class="col-left">

          <!-- Ingresos del día -->
          <div class="section-card">
            <div class="sc-header">
              <span class="sc-title"><i class="bi bi-receipt text-green"></i> Ingresos del día</span>
              <span class="sc-badge">{{ resumen.ingresos?.num_ordenes || 0 }} órdenes</span>
            </div>
            <div v-if="!resumen.ordenes_dia?.length" class="sc-empty">Sin órdenes hoy</div>
            <div v-else class="sc-table-wrap">
              <table class="sc-table">
                <thead>
                  <tr><th>Orden</th><th>Placa</th><th>Cliente</th><th>Tipo</th><th class="text-right">Total</th></tr>
                </thead>
                <tbody>
                  <tr v-for="o in resumen.ordenes_dia" :key="o.id">
                    <td class="font-mono">{{ o.numero_orden }}</td>
                    <td class="font-bold">{{ o.placa_vehiculo }}</td>
                    <td class="text-muted">{{ o.convenio_nombre || o.cliente_nombre || '—' }}</td>
                    <td>
                      <span class="tipo-pill" :class="o.convenio_nombre ? 'pill-blue' : 'pill-green'">
                        {{ o.convenio_nombre ? 'Convenio' : 'Efectivo' }}
                      </span>
                    </td>
                    <td class="text-right font-bold">{{ fmt(o.total_orden) }}</td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr>
                    <td colspan="4" class="text-right font-bold">Total del día</td>
                    <td class="text-right font-bold text-green">{{ fmt(resumen.ingresos?.ingresos_total) }}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>

          <!-- Mano de obra liquidada -->
          <div class="section-card">
            <div class="sc-header">
              <span class="sc-title"><i class="bi bi-cash-coin text-amber"></i> Mano de obra pagada</span>
              <span class="sc-badge">{{ resumen.liquidaciones?.num_liquidaciones || 0 }} pagos</span>
            </div>
            <div v-if="!resumen.liquidaciones_det?.length" class="sc-empty">Sin pagos a operarios hoy</div>
            <div v-else class="liq-list">
              <div v-for="l in resumen.liquidaciones_det" :key="l.id" class="liq-row">
                <div class="lr-avatar">{{ initials(l.worker_nombre) }}</div>
                <div class="lr-info">
                  <span class="lr-nombre">{{ l.worker_nombre }}</span>
                  <span class="lr-prof">{{ l.profession_nombre || '—' }}</span>
                </div>
                <div class="lr-monto">{{ fmt(l.monto_operario) }}</div>
                <span class="lr-forma">{{ l.forma_pago }}</span>
              </div>
            </div>
            <div v-if="resumen.liquidaciones_det?.length" class="liq-total">
              <span>Total mano de obra</span>
              <span class="font-bold text-amber">{{ fmt(resumen.liquidaciones?.total_mano_obra) }}</span>
            </div>
          </div>

        </div>

        <!-- COLUMNA DERECHA -->
        <div class="col-right">

          <!-- Egresos adicionales (gastos, compras) -->
          <div class="section-card">
            <div class="sc-header">
              <span class="sc-title"><i class="bi bi-wallet-fill text-red"></i> Gastos y compras</span>
              <span class="sc-badge">{{ fmt(resumen.egresos?.total_egresos) }}</span>
            </div>

            <!-- Form nuevo egreso -->
            <div class="egreso-form">
              <input v-model="newEgreso.concepto" class="form-control" placeholder="Concepto del gasto…" />
              <div class="egreso-row2">
                <select v-model="newEgreso.categoria" class="form-control form-sel">
                  <option value="gasto">Gasto</option>
                  <option value="compra">Compra / Inventario</option>
                  <option value="nomina">Nómina</option>
                  <option value="otro">Otro</option>
                </select>
                <select v-model="newEgreso.forma_pago" class="form-control form-sel">
                  <option value="efectivo">Efectivo</option>
                  <option value="transferencia">Transferencia</option>
                  <option value="otro">Otro</option>
                </select>
                <CurrencyInput v-model="newEgreso.monto" class="form-control" style="max-width:130px" />
                <button class="btn btn-primary btn-sm" @click="agregarEgreso" :disabled="savingEgreso">
                  <i v-if="savingEgreso" class="bi bi-hourglass-split spin"></i>
                  <i v-else class="bi bi-plus-lg"></i>
                </button>
              </div>
            </div>

            <!-- Lista de egresos -->
            <div v-if="!resumen.egresos_det?.length" class="sc-empty">Sin gastos registrados hoy</div>
            <div v-else class="egreso-list">
              <div v-for="e in resumen.egresos_det" :key="e.id" class="egreso-row">
                <div class="er-cat-dot" :class="`cat-${e.categoria}`"></div>
                <div class="er-info">
                  <span class="er-concepto">{{ e.concepto }}</span>
                  <span class="er-cat">{{ CAT_LABELS[e.categoria] || e.categoria }}</span>
                </div>
                <span class="er-monto">{{ fmt(e.monto) }}</span>
                <button class="er-del" @click="eliminarEgreso(e)" title="Eliminar">
                  <i class="bi bi-trash3"></i>
                </button>
              </div>
            </div>
          </div>

          <!-- Resumen consolidado -->
          <div class="section-card resumen-card">
            <div class="sc-title" style="margin-bottom:12px"><i class="bi bi-calculator"></i> Resumen del día</div>
            <div class="res-row">
              <span>Ingresos efectivo</span>
              <span class="text-green font-bold">+ {{ fmt(resumen.ingresos?.ingresos_efectivo) }}</span>
            </div>
            <div class="res-row">
              <span>Ingresos convenio (CxC)</span>
              <span class="text-blue font-bold">+ {{ fmt(resumen.ingresos?.ingresos_convenio) }}</span>
            </div>
            <div class="res-divider"></div>
            <div class="res-row">
              <span>Mano de obra pagada</span>
              <span class="text-red font-bold">− {{ fmt(resumen.liquidaciones?.total_mano_obra) }}</span>
            </div>
            <div class="res-row">
              <span>Gastos y compras</span>
              <span class="text-red font-bold">− {{ fmt(resumen.egresos?.total_egresos) }}</span>
            </div>
            <div class="res-divider"></div>
            <div class="res-row res-total">
              <span>Saldo neto en caja</span>
              <span :class="resumen.saldo_neto >= 0 ? 'text-green' : 'text-red'">
                {{ fmt(resumen.saldo_neto) }}
              </span>
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
import { showToast } from '@/utils/toast'
import { useCompanyStore } from '@/stores/companyStore'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'
import CurrencyInput from '@/components/CurrencyInput.vue'

const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id)

const loading  = ref(true)
const resumen  = ref({})
const fechaSel = ref(new Date().toISOString().split('T')[0])

async function cargar() {
  loading.value = true
  try {
    const { data } = await api.get('/api/talleres/caja/resumen', {
      params: { company_id: companyId.value, fecha: fechaSel.value }
    })
    resumen.value = data
  } catch { showToast('Error cargando resumen de caja', 'error') }
  finally { loading.value = false }
}

// ── Egresos ───────────────────────────────────────────────────────────────
const CAT_LABELS   = { gasto: 'Gasto', compra: 'Compra', nomina: 'Nómina', otro: 'Otro' }
const savingEgreso = ref(false)
const newEgreso    = ref({ concepto: '', categoria: 'gasto', monto: 0, forma_pago: 'efectivo' })

async function agregarEgreso() {
  if (!newEgreso.value.concepto?.trim() || !(newEgreso.value.monto > 0)) {
    showToast('Completa concepto y monto', 'warning'); return
  }
  savingEgreso.value = true
  try {
    await api.post('/api/talleres/caja/egresos', {
      company_id: companyId.value,
      fecha:      fechaSel.value,
      ...newEgreso.value,
    })
    newEgreso.value = { concepto: '', categoria: 'gasto', monto: 0, forma_pago: 'efectivo' }
    await cargar()
    showToast('Egreso registrado', 'success')
  } catch (e) { showToast(e?.response?.data?.detail ?? 'Error', 'error') }
  finally { savingEgreso.value = false }
}

async function eliminarEgreso(e) {
  if (!confirm(`¿Eliminar "${e.concepto}"?`)) return
  try {
    await api.delete(`/api/talleres/caja/egresos/${e.id}`, { params: { company_id: companyId.value } })
    await cargar()
  } catch { showToast('Error al eliminar', 'error') }
}

function fmt(v) {
  return Number(v||0).toLocaleString('es-CO', { style:'currency', currency:'COP', minimumFractionDigits:0 })
}
function initials(name = '') {
  return name.trim().split(/\s+/).slice(0,2).map(p => p[0]).join('').toUpperCase()
}

onMounted(cargar)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1200px; }
.page-header    { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.page-title     { font-size: 20px; font-weight: 700; color: #1e293b; margin: 0 0 4px; display: flex; align-items: center; gap: 8px; }
.page-subtitle  { font-size: 13px; color: #64748b; margin: 0; }
.header-actions { display: flex; align-items: center; gap: 8px; }
.loading-center { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 60px; color: #94a3b8; }

/* KPI */
.kpi-bar { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
.kpi-card { background: #fff; border-radius: 14px; border: 2px solid #e2e8f0; padding: 14px 16px; display: flex; align-items: center; gap: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.05); }
.kpi-icon-w { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
.kpi-green .kpi-icon-w { background: #dcfce7; color: #16a34a; } .kpi-green { border-color: #86efac; }
.kpi-blue  .kpi-icon-w { background: #dbeafe; color: #1d4ed8; } .kpi-blue  { border-color: #93c5fd; }
.kpi-red   .kpi-icon-w { background: #fee2e2; color: #dc2626; } .kpi-red   { border-color: #fca5a5; }
.kpi-body { display: flex; flex-direction: column; }
.kpi-val  { font-size: 16px; font-weight: 800; color: #1e293b; line-height: 1.2; }
.kpi-lbl  { font-size: 11px; color: #64748b; }

/* Grid */
.caja-grid { display: grid; grid-template-columns: 1fr 380px; gap: 16px; }
.col-left, .col-right { display: flex; flex-direction: column; gap: 16px; }

/* Secciones */
.section-card { background: #fff; border-radius: 14px; padding: 16px; box-shadow: 0 1px 6px rgba(0,0,0,.07); }
.sc-header    { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.sc-title     { font-size: 13px; font-weight: 700; color: #1e293b; display: flex; align-items: center; gap: 6px; }
.sc-badge     { font-size: 11px; background: #f1f5f9; color: #64748b; padding: 2px 8px; border-radius: 20px; font-weight: 600; }
.sc-empty     { text-align: center; color: #94a3b8; font-size: 13px; padding: 20px; }

/* Tabla ingresos */
.sc-table-wrap { overflow-x: auto; }
.sc-table      { width: 100%; border-collapse: collapse; font-size: 12px; }
.sc-table th   { background: #f8fafc; color: #64748b; font-size: 11px; font-weight: 600; padding: 6px 8px; border-bottom: 1px solid #e2e8f0; text-align: left; }
.sc-table td   { padding: 7px 8px; border-bottom: 1px solid #f1f5f9; color: #374151; }
.sc-table tfoot td { background: #f8fafc; font-weight: 700; border-top: 2px solid #e2e8f0; }
.text-right { text-align: right; }
.font-mono  { font-family: monospace; font-size: 11px; }
.font-bold  { font-weight: 700; }
.text-muted { color: #94a3b8; }
.text-green { color: #16a34a; } .text-blue { color: #1d4ed8; }
.text-red   { color: #dc2626; } .text-amber { color: #d97706; }
.tipo-pill  { font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 20px; }
.pill-green { background: #dcfce7; color: #15803d; }
.pill-blue  { background: #dbeafe; color: #1d4ed8; }

/* Liquidaciones */
.liq-list  { display: flex; flex-direction: column; gap: 6px; }
.liq-row   { display: flex; align-items: center; gap: 10px; padding: 8px 10px; background: #f8fafc; border-radius: 8px; }
.lr-avatar { width: 32px; height: 32px; background: #1e3a5f; color: #fff; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 800; flex-shrink: 0; }
.lr-info   { flex: 1; display: flex; flex-direction: column; }
.lr-nombre { font-size: 13px; font-weight: 700; color: #1e293b; }
.lr-prof   { font-size: 10px; color: #94a3b8; }
.lr-monto  { font-size: 13px; font-weight: 800; color: #d97706; }
.lr-forma  { font-size: 10px; color: #94a3b8; }
.liq-total { display: flex; justify-content: space-between; padding: 10px 10px 0; margin-top: 6px; border-top: 1px solid #f1f5f9; font-size: 13px; color: #475569; }

/* Egresos */
.egreso-form  { background: #f8fafc; border-radius: 10px; padding: 12px; margin-bottom: 12px; display: flex; flex-direction: column; gap: 8px; }
.egreso-row2  { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.egreso-list  { display: flex; flex-direction: column; gap: 6px; }
.egreso-row   { display: flex; align-items: center; gap: 8px; padding: 8px 10px; border: 1px solid #f1f5f9; border-radius: 8px; }
.er-cat-dot   { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.cat-gasto    { background: #ef4444; } .cat-compra { background: #f59e0b; }
.cat-nomina   { background: #8b5cf6; } .cat-otro   { background: #94a3b8; }
.er-info      { flex: 1; display: flex; flex-direction: column; }
.er-concepto  { font-size: 13px; font-weight: 600; color: #1e293b; }
.er-cat       { font-size: 10px; color: #94a3b8; }
.er-monto     { font-size: 13px; font-weight: 800; color: #dc2626; white-space: nowrap; }
.er-del       { width: 26px; height: 26px; background: #fee2e2; border: none; border-radius: 6px; cursor: pointer; color: #dc2626; font-size: 11px; display: flex; align-items: center; justify-content: center; }

/* Resumen consolidado */
.resumen-card { background: linear-gradient(135deg, #f8fafc 0%, #fff 100%); border: 2px solid #e2e8f0; }
.res-row     { display: flex; justify-content: space-between; align-items: center; padding: 7px 0; font-size: 13px; color: #374151; }
.res-divider { height: 1px; background: #e2e8f0; margin: 4px 0; }
.res-total   { font-size: 15px; font-weight: 800; color: #1e293b; padding-top: 10px; }

/* Form */
.form-control { border: 1.5px solid #e2e8f0; border-radius: 8px; padding: 7px 10px; font-size: 13px; outline: none; background: #fff; }
.form-control:focus { border-color: #3b82f6; }
.form-sel { appearance: none; padding-right: 28px; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%2364748b' stroke-width='1.5' fill='none'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 8px center; }

/* Btn */
.btn         { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #3b82f6; color: #fff; } .btn-primary:hover { background: #2563eb; }
.btn-primary:disabled { opacity: .6; cursor: not-allowed; }
.btn-outline { border: 1.5px solid #e2e8f0; background: #fff; color: #475569; }
.btn-sm      { padding: 6px 12px; font-size: 12px; }
.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

@media (max-width: 1024px) {
  .caja-grid { grid-template-columns: 1fr; }
  .kpi-bar   { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 576px) {
  .kpi-bar   { grid-template-columns: 1fr 1fr; }
  .page-container { padding: 14px; }
  .egreso-row2 { flex-direction: column; align-items: stretch; }
}
</style>
