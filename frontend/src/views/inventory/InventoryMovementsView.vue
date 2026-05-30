<template>
  <div class="mv-wrap">

    <!-- Filters -->
    <div class="filters-bar">
      <div class="f-search">
        <i class="bi bi-search f-ico"></i>
        <input v-model.trim="searchItem" @input="filterClient" class="f-inp" placeholder="Buscar insumo..." />
      </div>

      <select v-model="mtypeFilter" @change="load" class="f-sel">
        <option value="">Todos los tipos</option>
        <option value="physical">Inventario Físico</option>
        <option value="entry">Entrada</option>
        <option value="exit">Salida</option>
        <option value="sale_vb6">Venta VB6</option>
        <option value="sale_web">Venta Web</option>
        <option value="sale_online">Venta Online</option>
      </select>

      <div class="date-row">
        <input type="date" v-model="desde" @change="load" class="f-date" />
        <span class="date-sep">→</span>
        <input type="date" v-model="hasta" @change="load" class="f-date" />
      </div>

      <button class="btn-clear" @click="clearFilters" title="Limpiar filtros">
        <i class="bi bi-x-circle"></i>
      </button>
    </div>

    <!-- Info bar -->
    <div class="info-bar">
      <span class="info-cnt">{{ displayed.length }} movimientos</span>
      <div class="legend">
        <span class="lg lg-phys">Físico</span>
        <span class="lg lg-entry">Entrada</span>
        <span class="lg lg-exit">Salida</span>
        <span class="lg lg-sale">Venta</span>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="state-c">
      <i class="bi bi-arrow-repeat spin"></i> Cargando...
    </div>

    <template v-else>
      <!-- Desktop Table -->
      <div class="tbl-wrap d-desk">
        <table class="data-tbl">
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Insumo</th>
              <th>Tipo</th>
              <th class="tr">Δ Cantidad</th>
              <th class="tr">Antes</th>
              <th class="tr">Después</th>
              <th>Referencia</th>
              <th>Usuario</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in displayed" :key="m.id" :class="rowCls(m)">
              <td class="sm">{{ fmtDate(m.movement_date || m.created_at) }}</td>
              <td>
                <strong>{{ m.item_name }}</strong>
                <small v-if="m.unit_name" class="td-muted ml">{{ m.unit_name }}</small>
              </td>
              <td><span :class="typeBadge(m)">{{ typeLbl(m.movement_type) }}</span></td>
              <td class="tr fw-b" :class="m.qty >= 0 ? 'c-green' : 'c-red'">
                {{ m.qty >= 0 ? '+' : '' }}{{ fmt(m.qty) }}
              </td>
              <td class="tr td-muted sm">{{ fmt(m.qty_before) }}</td>
              <td class="tr fw-b sm">{{ fmt(m.qty_after) }}</td>
              <td class="sm td-muted">{{ m.reference_type }}{{ m.reference_id ? ' #' + m.reference_id : '' }}</td>
              <td class="sm td-muted">{{ m.usuario || '—' }}</td>
            </tr>
            <tr v-if="!displayed.length">
              <td colspan="8" class="empty-cell">Sin movimientos encontrados</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Mobile Cards -->
      <div class="cards-wrap d-mob">
        <div v-for="m in displayed" :key="m.id" class="mv-card" :class="rowCls(m)">
          <div class="mcard-top">
            <div class="mcard-main">
              <span class="mcard-name">{{ m.item_name }}</span>
              <span class="mcard-date">{{ fmtDate(m.movement_date || m.created_at) }}</span>
            </div>
            <span :class="typeBadge(m)">{{ typeLbl(m.movement_type) }}</span>
          </div>
          <div class="mcard-body">
            <div class="mcs">
              <span class="mcl">Delta</span>
              <span class="mcv fw-b" :class="m.qty >= 0 ? 'c-green' : 'c-red'">
                {{ m.qty >= 0 ? '+' : '' }}{{ fmt(m.qty) }} {{ m.unit_name }}
              </span>
            </div>
            <div class="mcs">
              <span class="mcl">Antes</span>
              <span class="mcv td-muted">{{ fmt(m.qty_before) }}</span>
            </div>
            <div class="mcs">
              <span class="mcl">Después</span>
              <span class="mcv">{{ fmt(m.qty_after) }}</span>
            </div>
          </div>
          <div v-if="m.usuario || m.reference_type" class="mcard-footer">
            <span class="mcs-ref td-muted">{{ m.reference_type }}{{ m.reference_id ? ' #' + m.reference_id : '' }}</span>
            <span class="mcs-user td-muted">{{ m.usuario }}</span>
          </div>
        </div>
        <div v-if="!displayed.length" class="empty-cell">Sin movimientos encontrados</div>
      </div>

    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/apis'

const allMovements = ref([])
const displayed    = ref([])
const loading      = ref(true)

const searchItem  = ref('')
const mtypeFilter = ref('')
const desde       = ref('')
const hasta       = ref('')

const fmt     = v => Number(v || 0).toLocaleString('es-CO', { maximumFractionDigits: 4 })
const fmtDate = v => v ? String(v).slice(0, 10) : '—'

const TYPE_LBL = {
  physical: 'Inv. Físico',
  entry: 'Entrada',
  exit: 'Salida',
  sale_vb6: 'Venta VB6',
  sale_web: 'Venta Web',
  sale_online: 'Venta Online',
}
function typeLbl(t) { return TYPE_LBL[t] || t }

function typeBadge(m) {
  const t = m.movement_type
  if (t === 'physical')       return 'tb tb-blue'
  if (t === 'entry')          return 'tb tb-green'
  if (t === 'exit')           return 'tb tb-orange'
  if (t?.startsWith('sale'))  return 'tb tb-red'
  return 'tb tb-gray'
}

function rowCls(m) {
  const t = m.movement_type
  if (t === 'entry')         return 'mr-entry'
  if (t === 'physical')      return 'mr-phys'
  if (t === 'exit')          return 'mr-exit'
  if (t?.startsWith('sale')) return 'mr-sale'
  return ''
}

async function load() {
  loading.value = true
  try {
    const p = {}
    if (mtypeFilter.value) p.mtype = mtypeFilter.value
    if (desde.value)       p.desde = desde.value
    if (hasta.value)       p.hasta = hasta.value
    allMovements.value = (await api.get('/api/inventory/movements', { params: p })).data
    filterClient()
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

function filterClient() {
  const q = searchItem.value.toLowerCase().trim()
  displayed.value = q
    ? allMovements.value.filter(m => (m.item_name || '').toLowerCase().includes(q))
    : [...allMovements.value]
}

function clearFilters() {
  searchItem.value  = ''
  mtypeFilter.value = ''
  desde.value       = ''
  hasta.value       = ''
  load()
}

onMounted(load)
</script>

<style scoped>
.mv-wrap { padding: 16px; }

/* Filters */
.filters-bar { display: flex; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; align-items: center; }
.f-search { position: relative; flex: 1; min-width: 180px; }
.f-ico { position: absolute; left: 9px; top: 50%; transform: translateY(-50%); color: #9ca3af; font-size: 0.83rem; }
.f-inp { width: 100%; padding: 8px 10px 8px 28px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 0.87rem; box-sizing: border-box; }
.f-sel { padding: 8px 10px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 0.87rem; background: #fff; }
.date-row { display: flex; align-items: center; gap: 6px; }
.f-date { padding: 7px 9px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 0.84rem; }
.date-sep { color: #9ca3af; font-size: 0.85rem; }
.btn-clear { background: none; border: 1px solid #e5e7eb; border-radius: 8px; padding: 7px 11px; cursor: pointer; color: #9ca3af; font-size: 0.9rem; }
.btn-clear:hover { border-color: #dc2626; color: #dc2626; }

/* Info bar */
.info-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px; }
.info-cnt { font-size: 0.83rem; color: #6b7280; }
.legend { display: flex; gap: 8px; flex-wrap: wrap; }
.lg { padding: 2px 8px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; }
.lg-phys  { background: #dbeafe; color: #1d4ed8; }
.lg-entry { background: #dcfce7; color: #16a34a; }
.lg-exit  { background: #ffedd5; color: #ea580c; }
.lg-sale  { background: #fee2e2; color: #dc2626; }

/* Table */
.tbl-wrap { overflow-x: auto; border-radius: 10px; border: 1px solid #e9ecef; }
.data-tbl { width: 100%; border-collapse: collapse; font-size: 0.84rem; }
.data-tbl th { background: #f8f9fa; padding: 9px 11px; text-align: left; font-weight: 600; border-bottom: 2px solid #dee2e6; white-space: nowrap; color: #374151; }
.data-tbl td { padding: 7px 11px; border-bottom: 1px solid #f0f0f0; vertical-align: middle; }
.data-tbl tr:last-child td { border-bottom: none; }
.data-tbl tr:hover td { filter: brightness(.97); }
.tr { text-align: right; }
.td-muted { color: #6b7280; }
.sm { font-size: 0.79rem; }
.fw-b { font-weight: 700; }
.ml { margin-left: 4px; }
.c-red   { color: #dc2626; }
.c-green { color: #16a34a; }

/* Row colors */
.mr-entry { background: #f0fdf4; }
.mr-phys  { background: #eff6ff; }
.mr-exit  { background: #fff7ed; }
.mr-sale  { background: #fff5f5; }

/* Type badges */
.tb { padding: 2px 7px; border-radius: 20px; font-size: 0.73rem; font-weight: 600; white-space: nowrap; }
.tb-blue   { background: #dbeafe; color: #1d4ed8; }
.tb-green  { background: #dcfce7; color: #16a34a; }
.tb-orange { background: #ffedd5; color: #ea580c; }
.tb-red    { background: #fee2e2; color: #dc2626; }
.tb-gray   { background: #f3f4f6; color: #6b7280; }

/* Empty */
.empty-cell { text-align: center; padding: 28px; color: #9ca3af; font-size: 0.87rem; }

/* Loading */
.state-c { text-align: center; padding: 40px; color: #6b7280; }
.spin { animation: spin 1s linear infinite; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Responsive */
.d-desk { display: block; }
.d-mob  { display: none; }

/* Mobile Cards */
.cards-wrap { display: flex; flex-direction: column; gap: 10px; }
.mv-card { border-radius: 10px; padding: 12px 14px; border: 1px solid #e9ecef; }
.mr-entry.mv-card { border-left: 4px solid #16a34a; }
.mr-phys.mv-card  { border-left: 4px solid #1d4ed8; }
.mr-exit.mv-card  { border-left: 4px solid #ea580c; }
.mr-sale.mv-card  { border-left: 4px solid #dc2626; }
.mcard-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; gap: 8px; }
.mcard-main { min-width: 0; }
.mcard-name { font-weight: 700; font-size: 0.9rem; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mcard-date { font-size: 0.76rem; color: #9ca3af; display: block; margin-top: 2px; }
.mcard-body { display: flex; gap: 14px; margin-bottom: 6px; flex-wrap: wrap; }
.mcs { display: flex; flex-direction: column; gap: 1px; }
.mcl { font-size: 0.7rem; color: #9ca3af; font-weight: 500; }
.mcv { font-size: 0.87rem; font-weight: 600; }
.mcard-footer { display: flex; justify-content: space-between; padding-top: 6px; border-top: 1px solid #f0f0f0; }
.mcs-ref, .mcs-user { font-size: 0.76rem; }

@media (max-width: 768px) {
  .d-desk { display: none; }
  .d-mob  { display: flex; flex-direction: column; }
  .filters-bar { flex-direction: column; align-items: stretch; }
  .f-sel { width: 100%; }
  .date-row { justify-content: space-between; }
  .f-date { flex: 1; }
}
@media (max-width: 576px) {
  .mv-wrap { padding: 10px; }
  .date-row { flex-wrap: wrap; }
}
</style>
