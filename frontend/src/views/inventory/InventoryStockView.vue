<template>
  <div class="sv-wrap">

    <!-- KPI Bar -->
    <div class="kpi-bar">
      <div class="kpi-card">
        <span class="kpi-n">{{ rows.length }}</span>
        <span class="kpi-l">Total insumos</span>
      </div>
      <div class="kpi-card kpi-blue">
        <span class="kpi-n">{{ ctrlCount }}</span>
        <span class="kpi-l">Con control</span>
      </div>
      <div class="kpi-card kpi-orange">
        <span class="kpi-n">{{ critCount }}</span>
        <span class="kpi-l">Críticos</span>
      </div>
      <div class="kpi-card kpi-red">
        <span class="kpi-n">{{ outCount }}</span>
        <span class="kpi-l">Agotados</span>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters-bar">
      <div class="f-search-wrap">
        <i class="bi bi-search f-icon"></i>
        <input v-model.trim="search" @input="debouncedLoad" class="f-input" placeholder="Buscar por nombre o código..." />
      </div>

      <select v-if="categories.length" v-model="catFilter" @change="load" class="f-select">
        <option value="">Todas las categorías</option>
        <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>

      <div class="toggle-grp">
        <button @click="setActive('1')"   :class="activeFilter==='1'   ? 'tog-on' : 'tog'">Activos</button>
        <button @click="setActive('0')"   :class="activeFilter==='0'   ? 'tog-on' : 'tog'">Inactivos</button>
        <button @click="setActive('all')" :class="activeFilter==='all' ? 'tog-on' : 'tog'">Todos</button>
      </div>

      <label class="crit-lbl">
        <input type="checkbox" v-model="critFilter" @change="load" class="crit-chk" />
        <span>Solo críticos</span>
      </label>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="state-center">
      <i class="bi bi-arrow-repeat spin"></i> Cargando...
    </div>

    <template v-else>

      <!-- Desktop Table -->
      <div class="tbl-wrap d-desk">
        <table class="data-tbl">
          <thead>
            <tr>
              <th>Cód.</th>
              <th>Insumo</th>
              <th>Categoría</th>
              <th class="tr">Stock actual</th>
              <th>Unidad</th>
              <th class="tr">Mínimo</th>
              <th class="tc">Estado</th>
              <th class="tc">Historial</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in rows" :key="r.id_item" :class="rowCls(r)">
              <td class="td-muted sm">{{ r.code || '—' }}</td>
              <td>
                <strong>{{ r.description }}</strong>
                <span v-if="!r.is_active" class="badge-off">Inactivo</span>
              </td>
              <td class="td-muted">{{ r.category_name || '—' }}</td>
              <td class="tr">
                <span :class="stockCls(r)" class="fw-b">{{ fmt(r.stock_qty) }}</span>
              </td>
              <td class="td-muted">{{ r.unit_name || '—' }}</td>
              <td class="tr" @click.stop="startEdit(r)" style="cursor:pointer">
                <template v-if="editingId !== r.id_item">
                  <span class="min-val">{{ fmt(r.min_stock) }}<i class="bi bi-pencil-fill ei"></i></span>
                </template>
                <input v-else
                       v-focus
                       v-model.number="editVal"
                       type="number" min="0" step="0.001"
                       class="inp-inline"
                       @keyup.enter="saveMin(r)"
                       @keyup.escape="editingId=null"
                       @blur="saveMin(r)"
                       @click.stop />
              </td>
              <td class="tc">
                <span :class="statusBadge(r)">{{ statusLbl(r) }}</span>
              </td>
              <td class="tc">
                <button class="btn-ico" @click="openMov(r)" title="Ver movimientos">
                  <i class="bi bi-clock-history"></i>
                </button>
              </td>
            </tr>
            <tr v-if="!rows.length">
              <td colspan="8" class="empty-row">Sin insumos encontrados</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Mobile Cards -->
      <div class="cards-wrap d-mob">
        <div v-for="r in rows" :key="r.id_item"
             class="s-card"
             :class="cardCls(r)">
          <div class="sc-top">
            <div class="sc-info">
              <span class="sc-name">{{ r.description }}</span>
              <span class="sc-sub">{{ r.category_name || r.unit_name }}</span>
            </div>
            <span :class="statusBadge(r)">{{ statusLbl(r) }}</span>
          </div>
          <div class="sc-body">
            <div class="sc-stat">
              <span class="sc-lbl">Stock actual</span>
              <span :class="['sc-val fw-b', stockCls(r)]">{{ fmt(r.stock_qty) }} {{ r.unit_name }}</span>
            </div>
            <div class="sc-stat" @click.stop="startEdit(r)" style="cursor:pointer">
              <span class="sc-lbl">Mínimo</span>
              <span class="sc-val" v-if="editingId !== r.id_item">
                {{ fmt(r.min_stock) }}<i class="bi bi-pencil-fill ei-sm"></i>
              </span>
              <input v-else
                     v-focus
                     v-model.number="editVal"
                     type="number" min="0" step="0.001"
                     class="inp-inline-sm"
                     @keyup.enter="saveMin(r)"
                     @keyup.escape="editingId=null"
                     @blur="saveMin(r)"
                     @click.stop />
            </div>
            <button class="btn-mov-sm" @click="openMov(r)">
              <i class="bi bi-clock-history"></i> Movimientos
            </button>
          </div>
        </div>
        <div v-if="!rows.length" class="empty-row">Sin insumos encontrados</div>
      </div>

    </template>

    <!-- Movements Modal -->
    <teleport to="body">
      <div v-if="mov.show" class="modal-bg" @click.self="mov.show=false">
        <div class="mov-panel">
          <div class="mov-hdr">
            <div>
              <div class="mov-title">{{ mov.item?.description }}</div>
              <small class="td-muted">
                Stock: {{ fmt(mov.item?.stock_qty) }} {{ mov.item?.unit_name }} &nbsp;|&nbsp;
                Mín: {{ fmt(mov.item?.min_stock) }}
              </small>
            </div>
            <button class="btn-close-x" @click="mov.show=false"><i class="bi bi-x-lg"></i></button>
          </div>

          <div v-if="mov.loading" class="state-center"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>

          <div v-else class="mov-tbl-wrap">
            <table class="mov-tbl">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Tipo</th>
                  <th class="tr">Δ</th>
                  <th class="tr">Antes</th>
                  <th class="tr">Después</th>
                  <th>Referencia</th>
                  <th>Usuario</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="m in mov.data" :key="m.id" :class="movRowCls(m)">
                  <td class="sm">{{ fmtDate(m.movement_date || m.created_at) }}</td>
                  <td><span :class="movBadge(m)">{{ movLbl(m.movement_type) }}</span></td>
                  <td class="tr fw-b" :class="m.qty >= 0 ? 'c-green' : 'c-red'">
                    {{ m.qty >= 0 ? '+' : '' }}{{ fmt(m.qty) }}
                  </td>
                  <td class="tr td-muted sm">{{ fmt(m.qty_before) }}</td>
                  <td class="tr sm">{{ fmt(m.qty_after) }}</td>
                  <td class="sm td-muted">{{ m.reference_type }}{{ m.reference_id ? ' #' + m.reference_id : '' }}</td>
                  <td class="sm td-muted">{{ m.usuario }}</td>
                </tr>
                <tr v-if="!mov.data.length">
                  <td colspan="7" class="empty-row">Sin movimientos registrados</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </teleport>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'

const vFocus = { mounted: el => el.focus() }

const rows       = ref([])
const categories = ref([])
const loading    = ref(true)

const search      = ref('')
const catFilter   = ref('')
const activeFilter = ref('1')
const critFilter  = ref(false)

const editingId = ref(null)
const editVal   = ref(0)

const mov = ref({ show: false, item: null, loading: false, data: [] })

const ctrlCount = computed(() => rows.value.filter(r => r.control_stock).length)
const critCount = computed(() => rows.value.filter(r => itemStatus(r) === 'critical').length)
const outCount  = computed(() => rows.value.filter(r => itemStatus(r) === 'out').length)

const fmt     = v => Number(v || 0).toLocaleString('es-CO', { maximumFractionDigits: 4 })
const fmtDate = v => v ? String(v).slice(0, 10) : '—'

function itemStatus(r) {
  if (!r.control_stock || !r.min_stock) return 'none'
  if ((r.stock_qty || 0) <= 0)         return 'out'
  if ((r.stock_qty || 0) <= r.min_stock) return 'critical'
  return 'ok'
}

function statusLbl(r) {
  const s = itemStatus(r)
  if (s === 'out')      return '⛔ Agotado'
  if (s === 'critical') return '🔴 Crítico'
  if (s === 'ok')       return '✅ OK'
  return '⚪ Sin control'
}

function statusBadge(r) {
  const s = itemStatus(r)
  return { 'b-out': s === 'out', 'b-crit': s === 'critical', 'b-ok': s === 'ok', 'b-none': s === 'none' }
}

function stockCls(r) {
  const s = itemStatus(r)
  return { 'c-red': s === 'out', 'c-orange': s === 'critical', 'c-green': s === 'ok' }
}

function rowCls(r) {
  const s = itemStatus(r)
  return { 'row-out': s === 'out', 'row-crit': s === 'critical' }
}

function cardCls(r) {
  const s = itemStatus(r)
  return { 'card-out': s === 'out', 'card-crit': s === 'critical' }
}

const MOV_LBL = {
  physical: 'Inv. Físico', entry: 'Entrada', exit: 'Salida',
  sale_vb6: 'Venta VB6', sale_web: 'Venta Web', sale_online: 'Venta Online',
}
function movLbl(t) { return MOV_LBL[t] || t }

function movRowCls(m) {
  if (m.movement_type === 'entry') return 'mr-entry'
  if (m.movement_type === 'exit' || m.movement_type?.startsWith('sale')) return 'mr-exit'
  if (m.movement_type === 'physical') return 'mr-phys'
  return ''
}
function movBadge(m) {
  const t = m.movement_type
  if (t === 'physical')          return 'mb mb-blue'
  if (t === 'entry')             return 'mb mb-green'
  if (t === 'exit')              return 'mb mb-orange'
  if (t?.startsWith('sale'))     return 'mb mb-red'
  return 'mb mb-gray'
}

let timer = null
function debouncedLoad() {
  clearTimeout(timer)
  timer = setTimeout(load, 350)
}

function setActive(v) { activeFilter.value = v; load() }

async function load() {
  loading.value = true
  try {
    const p = { active: activeFilter.value, critical: critFilter.value ? 1 : 0 }
    if (search.value)    p.search = search.value
    if (catFilter.value) p.category_id = catFilter.value
    rows.value = (await api.get('/api/inventory/stock', { params: p })).data
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

async function loadCategories() {
  try { categories.value = (await api.get('/api/inventory/categories')).data }
  catch { categories.value = [] }
}

function startEdit(r) {
  editingId.value = r.id_item
  editVal.value   = r.min_stock || 0
}

async function saveMin(r) {
  if (editingId.value !== r.id_item) return
  editingId.value = null
  const nv = Number(editVal.value)
  if (nv === r.min_stock) return
  try {
    await api.patch(`/api/inventory/stock/${r.id_item}/min-stock`, { min_stock: nv })
    r.min_stock = nv
    showToast('Mínimo actualizado', 'success')
  } catch { showToast('Error al guardar', 'error') }
}

async function openMov(r) {
  mov.value = { show: true, item: r, loading: true, data: [] }
  try {
    mov.value.data = (await api.get(`/api/inventory/movements/${r.id_item}`)).data
  } catch { mov.value.data = [] }
  finally { mov.value.loading = false }
}

onMounted(() => { load(); loadCategories() })
</script>

<style scoped>
.sv-wrap { padding: 16px; }

/* KPI */
.kpi-bar { display: flex; gap: 12px; margin-bottom: 18px; flex-wrap: wrap; }
.kpi-card { flex: 1; min-width: 110px; background: #f8f9fa; border-radius: 10px; padding: 12px 16px; display: flex; flex-direction: column; gap: 2px; border: 1px solid #e9ecef; }
.kpi-blue   { background: #eff6ff; border-color: #bfdbfe; }
.kpi-orange { background: #fff7ed; border-color: #fed7aa; }
.kpi-red    { background: #fff1f2; border-color: #fecdd3; }
.kpi-n { font-size: 1.6rem; font-weight: 700; line-height: 1; }
.kpi-l { font-size: 0.75rem; color: #6b7280; font-weight: 500; }
.kpi-blue .kpi-n   { color: #2563eb; }
.kpi-orange .kpi-n { color: #ea580c; }
.kpi-red .kpi-n    { color: #dc2626; }

/* Filters */
.filters-bar { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; align-items: center; }
.f-search-wrap { position: relative; flex: 1; min-width: 200px; }
.f-icon { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: #9ca3af; font-size: 0.85rem; }
.f-input { width: 100%; padding: 8px 10px 8px 30px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 0.87rem; box-sizing: border-box; }
.f-select { padding: 8px 10px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 0.87rem; background: #fff; }
.toggle-grp { display: flex; border: 1px solid #d1d5db; border-radius: 8px; overflow: hidden; }
.tog    { padding: 7px 13px; background: #fff; border: none; cursor: pointer; font-size: 0.82rem; color: #374151; }
.tog-on { padding: 7px 13px; background: #2563eb; color: #fff; border: none; cursor: pointer; font-size: 0.82rem; font-weight: 600; }
.crit-lbl { display: flex; align-items: center; gap: 6px; font-size: 0.83rem; cursor: pointer; white-space: nowrap; }
.crit-chk { cursor: pointer; }

/* Loading */
.state-center { text-align: center; padding: 40px; color: #6b7280; }
.spin { animation: spin 1s linear infinite; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Table (desktop) */
.tbl-wrap { overflow-x: auto; border-radius: 10px; border: 1px solid #e9ecef; }
.data-tbl { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.data-tbl th { background: #f8f9fa; padding: 9px 11px; text-align: left; font-weight: 600; border-bottom: 2px solid #dee2e6; white-space: nowrap; color: #374151; }
.data-tbl td { padding: 8px 11px; border-bottom: 1px solid #f0f0f0; vertical-align: middle; }
.data-tbl tr:last-child td { border-bottom: none; }
.data-tbl tr:hover td { background: #fafafa; }
.tr { text-align: right; }
.tc { text-align: center; }
.td-muted { color: #6b7280; }
.sm { font-size: 0.8rem; }
.fw-b { font-weight: 700; }

/* Row status colors */
.row-out td  { background: #fff5f5 !important; }
.row-crit td { background: #fffbf0 !important; }

/* Inline min edit */
.min-val { cursor: pointer; white-space: nowrap; }
.ei { font-size: 0.65rem; color: #9ca3af; margin-left: 4px; opacity: 0.7; }
.ei:hover { color: #2563eb; }
.inp-inline { width: 80px; padding: 3px 6px; border: 1.5px solid #2563eb; border-radius: 5px; font-size: 0.85rem; text-align: right; }

/* Status badges */
.b-out  { background: #fee2e2; color: #dc2626; padding: 2px 8px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; white-space: nowrap; }
.b-crit { background: #ffedd5; color: #ea580c; padding: 2px 8px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; white-space: nowrap; }
.b-ok   { background: #dcfce7; color: #16a34a; padding: 2px 8px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; white-space: nowrap; }
.b-none { background: #f3f4f6; color: #6b7280; padding: 2px 8px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; white-space: nowrap; }
.badge-off { background: #f3f4f6; color: #9ca3af; padding: 1px 6px; border-radius: 20px; font-size: 0.72rem; margin-left: 6px; }

/* Stock colors */
.c-red    { color: #dc2626; }
.c-orange { color: #ea580c; }
.c-green  { color: #16a34a; }

/* Icon button */
.btn-ico { background: none; border: 1px solid #e5e7eb; border-radius: 6px; padding: 4px 8px; cursor: pointer; color: #4b5563; font-size: 0.82rem; }
.btn-ico:hover { background: #eff6ff; border-color: #bfdbfe; color: #2563eb; }

/* Empty row */
.empty-row { text-align: center; padding: 28px; color: #9ca3af; font-size: 0.87rem; }

/* Responsive toggles */
.d-desk { display: block; }
.d-mob  { display: none; }

/* Mobile Cards */
.cards-wrap { display: flex; flex-direction: column; gap: 10px; }
.s-card { background: #fff; border: 1px solid #e9ecef; border-radius: 10px; padding: 14px; }
.card-out  { border-left: 4px solid #dc2626; }
.card-crit { border-left: 4px solid #ea580c; }
.sc-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; gap: 8px; }
.sc-info { min-width: 0; }
.sc-name { font-weight: 700; font-size: 0.92rem; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sc-sub  { font-size: 0.78rem; color: #6b7280; display: block; }
.sc-body { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.sc-stat { display: flex; flex-direction: column; gap: 2px; }
.sc-lbl  { font-size: 0.72rem; color: #9ca3af; font-weight: 500; }
.sc-val  { font-size: 0.88rem; font-weight: 600; }
.ei-sm { font-size: 0.65rem; color: #9ca3af; margin-left: 3px; }
.inp-inline-sm { width: 70px; padding: 3px 5px; border: 1.5px solid #2563eb; border-radius: 5px; font-size: 0.85rem; text-align: right; }
.btn-mov-sm { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; border-radius: 6px; padding: 5px 10px; font-size: 0.78rem; cursor: pointer; margin-left: auto; font-weight: 600; }
.btn-mov-sm:hover { background: #dbeafe; }

/* Movements Modal */
.modal-bg { position: fixed; inset: 0; background: rgba(0,0,0,.5); z-index: 1100; display: flex; align-items: center; justify-content: center; padding: 12px; }
.mov-panel { background: #fff; border-radius: 14px; width: 100%; max-width: 840px; max-height: 85vh; display: flex; flex-direction: column; box-shadow: 0 24px 64px rgba(0,0,0,.2); }
.mov-hdr { display: flex; justify-content: space-between; align-items: flex-start; padding: 18px 20px 14px; border-bottom: 1px solid #e9ecef; gap: 12px; }
.mov-title { font-weight: 700; font-size: 1rem; margin-bottom: 2px; }
.btn-close-x { background: none; border: none; padding: 4px; cursor: pointer; color: #6b7280; font-size: 1.1rem; }
.btn-close-x:hover { color: #111; }
.mov-tbl-wrap { overflow: auto; flex: 1; }
.mov-tbl { width: 100%; border-collapse: collapse; font-size: 0.83rem; }
.mov-tbl th { background: #f8f9fa; padding: 8px 10px; text-align: left; font-weight: 600; border-bottom: 2px solid #dee2e6; white-space: nowrap; position: sticky; top: 0; }
.mov-tbl td { padding: 7px 10px; border-bottom: 1px solid #f0f0f0; }
.mr-entry { background: #f0fdf4 !important; }
.mr-exit  { background: #fff5f5 !important; }
.mr-phys  { background: #eff6ff !important; }
.mb { padding: 2px 7px; border-radius: 20px; font-size: 0.73rem; font-weight: 600; white-space: nowrap; }
.mb-blue   { background: #dbeafe; color: #1d4ed8; }
.mb-green  { background: #dcfce7; color: #16a34a; }
.mb-orange { background: #ffedd5; color: #ea580c; }
.mb-red    { background: #fee2e2; color: #dc2626; }
.mb-gray   { background: #f3f4f6; color: #6b7280; }

@media (max-width: 768px) {
  .d-desk { display: none; }
  .d-mob  { display: flex; flex-direction: column; }
  .kpi-card { min-width: 80px; padding: 10px 12px; }
  .kpi-n { font-size: 1.3rem; }
  .filters-bar { flex-direction: column; }
  .f-search-wrap { min-width: unset; }
  .toggle-grp .tog, .toggle-grp .tog-on { padding: 7px 10px; font-size: 0.8rem; }
  .mov-panel { max-height: 92vh; border-radius: 14px 14px 0 0; align-self: flex-end; }
}
@media (max-width: 576px) {
  .sv-wrap { padding: 10px; }
  .kpi-bar { gap: 8px; }
  .kpi-card { padding: 8px 10px; }
  .kpi-n { font-size: 1.15rem; }
}
</style>
