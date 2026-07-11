<template>
  <div class="fe-page">

    <!-- ── KPI Bar ──────────────────────────────────────────────────────────── -->
    <div class="fe-kpi-bar">
      <div class="fe-kpi-card fe-kpi--pend">
        <i class="bi bi-clock-history fe-kpi-icon"></i>
        <div class="fe-kpi-info">
          <span class="fe-kpi-val">{{ rows0.length }}</span>
          <span class="fe-kpi-lbl">Pendientes DIAN</span>
        </div>
      </div>
      <div class="fe-kpi-card fe-kpi--ok">
        <i class="bi bi-check-circle-fill fe-kpi-icon"></i>
        <div class="fe-kpi-info">
          <span class="fe-kpi-val">{{ rows1.length }}</span>
          <span class="fe-kpi-lbl">Enviadas DIAN</span>
        </div>
      </div>
      <div class="fe-kpi-card fe-kpi--total">
        <i class="bi bi-lightning-charge-fill fe-kpi-icon"></i>
        <div class="fe-kpi-info">
          <span class="fe-kpi-val">{{ fmt(totalPendiente) }}</span>
          <span class="fe-kpi-lbl">Valor pendiente</span>
        </div>
      </div>
    </div>

    <!-- ── Toolbar ───────────────────────────────────────────────────────────── -->
    <div class="fe-toolbar">
      <div class="mode-toggle">
        <button :class="['btn-mode', billMode === 'day' && 'active']" @click="setMode('day')">Día</button>
        <button :class="['btn-mode', billMode === 'month' && 'active']" @click="setMode('month')">Mes</button>
      </div>
      <CustomDatePicker v-model="billDate" @update:modelValue="cargar" />
      <span v-if="loading" class="fe-spinner">
        <i class="bi bi-arrow-repeat spin"></i>
      </span>
    </div>

    <!-- ── Tabs ──────────────────────────────────────────────────────────────── -->
    <div class="fe-tabs">
      <button :class="['fe-tab', activeTab === 0 && 'fe-tab--active']" @click="activeTab = 0">
        <i class="bi bi-clock-history"></i>
        Pendientes DIAN
        <span class="tab-badge tab-badge--pend">{{ rows0.length }}</span>
      </button>
      <button :class="['fe-tab', activeTab === 1 && 'fe-tab--active']" @click="activeTab = 1">
        <i class="bi bi-check-circle-fill"></i>
        Enviadas DIAN
        <span class="tab-badge tab-badge--ok">{{ rows1.length }}</span>
      </button>
    </div>

    <!-- ── Tabla Pendientes ───────────────────────────────────────────────────── -->
    <div v-if="activeTab === 0" class="fe-table-wrap">
      <div v-if="loading" class="fe-empty">Cargando…</div>
      <div v-else-if="!rows0.length" class="fe-empty">
        <i class="bi bi-inbox" style="font-size:32px;color:#cbd5e1;display:block;margin-bottom:8px"></i>
        Sin facturas pendientes
      </div>
      <table v-else class="fe-table">
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Prefijo</th>
            <th>Nro. Folio</th>
            <th>Valor</th>
            <th>Cuenta</th>
            <th>Cliente</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rows0" :key="r.nro_folio + r.prefijo">
            <td>{{ fmtDate(r.fecha) }}</td>
            <td><span class="pref-chip pref-chip--pend">{{ r.prefijo }}</span></td>
            <td>{{ r.nro_folio }}</td>
            <td>{{ fmt(r.valor) }}</td>
            <td>{{ r.cuenta }}</td>
            <td>{{ r.cliente }}</td>
            <td>
              <div class="action-btns">
                <button class="btn-dian btn-dian--revalidar" @click="revalidar(r)">
                  <i class="bi bi-arrow-clockwise"></i> Revalidar
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ── Tabla Enviadas ─────────────────────────────────────────────────────── -->
    <div v-if="activeTab === 1" class="fe-table-wrap">
      <div v-if="loading" class="fe-empty">Cargando…</div>
      <div v-else-if="!rows1.length" class="fe-empty">
        <i class="bi bi-inbox" style="font-size:32px;color:#cbd5e1;display:block;margin-bottom:8px"></i>
        Sin facturas enviadas para este período
      </div>
      <table v-else class="fe-table">
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Prefijo</th>
            <th>Nro. Folio</th>
            <th>Valor</th>
            <th>Cuenta</th>
            <th>Cliente</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rows1" :key="r.nro_folio + r.prefijo">
            <td>{{ fmtDate(r.fecha) }}</td>
            <td><span class="pref-chip pref-chip--ok">{{ r.prefijo }}</span></td>
            <td>{{ r.nro_folio }}</td>
            <td>{{ fmt(r.valor) }}</td>
            <td>{{ r.cuenta }}</td>
            <td>{{ r.cliente }}</td>
            <td>
              <div class="action-btns">
                <button class="btn-dian btn-dian--ver" title="Ver en DIAN">
                  <i class="bi bi-globe2"></i> Ver Dian
                </button>
                <button class="btn-dian btn-dian--mail" title="Enviar por email">
                  <i class="bi bi-envelope"></i> Mail
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useCompanyStore } from '@/stores/companyStore'
import api from '@/services/apis'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'
import { showToast } from '@/utils/toast'

const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id)

const billMode  = ref('day')
const billDate  = ref(new Date().toLocaleDateString('en-CA', { timeZone: 'America/Bogota' }))
const loading   = ref(false)
const activeTab = ref(0)
const rows0     = ref([])
const rows1     = ref([])

const totalPendiente = computed(() =>
  rows0.value.reduce((s, r) => s + Number(r.valor || 0), 0)
)

function setMode(m) {
  billMode.value = m
  cargar()
}

async function cargar() {
  if (!companyId.value) return
  loading.value = true
  try {
    const [r0, r1] = await Promise.all([
      api.get('/company-configs/pe-facturas-cliente', {
        params: { fe: 0, date: billDate.value, mode: billMode.value }
      }),
      api.get('/company-configs/pe-facturas-cliente', {
        params: { fe: 1, date: billDate.value, mode: billMode.value }
      }),
    ])
    rows0.value = r0.data || []
    rows1.value = r1.data || []
  } catch (e) {
    showToast(e?.response?.data?.detail || 'Error consultando facturas electrónicas', 'error')
  }
  loading.value = false
}

async function revalidar(r) {
  showToast(`Revalidando folio ${r.nro_folio}…`, 'info', 2000)
  // TODO: llamar al endpoint de revalidación DIAN cuando esté disponible
}

function fmt(v) {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency', currency: 'COP', maximumFractionDigits: 0
  }).format(v || 0)
}

function fmtDate(iso) {
  if (!iso) return '—'
  const [y, m, d] = iso.slice(0, 10).split('-')
  return `${d}/${m}/${y}`
}

onMounted(() => {
  if (companyId.value) cargar()
})

watch(companyId, (v) => { if (v) cargar() })
</script>

<style scoped>
.fe-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
  max-width: 1200px;
  margin: 0 auto;
}

/* ── KPI Bar ─────────────────────────────────────────────────────────────── */
.fe-kpi-bar {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.fe-kpi-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  border-radius: 12px;
  flex: 1;
  min-width: 160px;
  border: 1px solid transparent;
}
.fe-kpi--pend  { background: #fff7ed; border-color: #fed7aa; }
.fe-kpi--ok    { background: #f0fdf4; border-color: #bbf7d0; }
.fe-kpi--total { background: #eff6ff; border-color: #bfdbfe; }

.fe-kpi-icon {
  font-size: 24px;
  flex-shrink: 0;
}
.fe-kpi--pend  .fe-kpi-icon { color: #ea580c; }
.fe-kpi--ok    .fe-kpi-icon { color: #16a34a; }
.fe-kpi--total .fe-kpi-icon { color: #2563eb; }

.fe-kpi-info { display: flex; flex-direction: column; gap: 2px; }
.fe-kpi-val  { font-size: 22px; font-weight: 900; color: #1e293b; line-height: 1; }
.fe-kpi-lbl  { font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: .4px; }

/* ── Toolbar ─────────────────────────────────────────────────────────────── */
.fe-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.mode-toggle {
  display: flex;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}
.btn-mode {
  padding: 7px 18px;
  border: none;
  background: #fff;
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
  transition: all .15s;
}
.btn-mode.active { background: #1e293b; color: #fff; }
.fe-spinner { color: #64748b; font-size: 18px; }

/* ── Tabs ────────────────────────────────────────────────────────────────── */
.fe-tabs {
  display: flex;
  gap: 0;
  border-bottom: 2px solid #e2e8f0;
}
.fe-tab {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 10px 20px;
  border: none;
  background: none;
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all .15s;
}
.fe-tab:hover { color: #1e293b; background: #f8fafc; }
.fe-tab--active { color: #1d4ed8; border-bottom-color: #3b82f6; }

.tab-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;
}
.tab-badge--pend { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.tab-badge--ok   { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }

/* ── Tabla ───────────────────────────────────────────────────────────────── */
.fe-table-wrap {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}
.fe-empty {
  padding: 40px 20px;
  text-align: center;
  color: #94a3b8;
  font-size: 14px;
}
.fe-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.fe-table thead tr { background: #f8fafc; }
.fe-table th {
  padding: 10px 14px;
  text-align: left;
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: .4px;
  border-bottom: 1px solid #e2e8f0;
  white-space: nowrap;
}
.fe-table td {
  padding: 10px 14px;
  color: #1e293b;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}
.fe-table tbody tr:last-child td { border-bottom: none; }
.fe-table tbody tr:hover { background: #f8fafc; }

.pref-chip {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;
}
.pref-chip--pend { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.pref-chip--ok   { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }

.action-btns {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.btn-dian {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all .15s;
  white-space: nowrap;
}
.btn-dian--revalidar { background: #fff7ed; color: #ea580c; border-color: #fed7aa; }
.btn-dian--revalidar:hover { background: #ffedd5; }
.btn-dian--ver  { background: #eff6ff; color: #2563eb; border-color: #bfdbfe; }
.btn-dian--ver:hover { background: #dbeafe; }
.btn-dian--mail { background: #f0fdf4; color: #16a34a; border-color: #bbf7d0; }
.btn-dian--mail:hover { background: #dcfce7; }

/* ── Responsive ──────────────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .fe-page { padding: 12px; gap: 12px; }
  .fe-kpi-card { min-width: 130px; padding: 10px 14px; }
  .fe-kpi-val  { font-size: 18px; }
  .fe-table th, .fe-table td { padding: 8px 10px; }
  .fe-tab { padding: 8px 12px; font-size: 12px; }
}

@media (max-width: 576px) {
  .fe-kpi-bar { gap: 8px; }
  .fe-kpi-card { min-width: 100%; flex: 1 1 100%; }
  .fe-toolbar { gap: 8px; }
  .fe-table { font-size: 12px; }
  .fe-table th:nth-child(5),
  .fe-table td:nth-child(5) { display: none; }
  .action-btns { flex-direction: column; }
}

.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from { transform: rotate(0) } to { transform: rotate(360deg) } }
</style>
