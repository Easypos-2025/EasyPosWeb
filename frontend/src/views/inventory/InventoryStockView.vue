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

    <!-- Último inventario -->
    <div v-if="lastInventoryDate" class="inv-date-bar">
      <i class="bi bi-calendar-check-fill inv-ico"></i>
      <span>Último inventario físico registrado: <strong>{{ lastInventoryDate }}</strong></span>
    </div>

    <!-- Filters + Export -->
    <div class="filters-bar">
      <div class="f-search-wrap">
        <i class="bi bi-search f-ico"></i>
        <input v-model.trim="search" @input="debouncedLoad" class="f-inp" placeholder="Buscar insumo o código..." />
      </div>

      <select v-model="catFilter" @change="load" class="f-sel">
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

      <ExportToolbar
        :data="exportData"
        :columns="exportCols"
        filename="stocks-actuales"
        title="Stocks Actuales"
      />
    </div>

    <!-- Loading -->
    <div v-if="loading" class="state-c">
      <i class="bi bi-arrow-repeat spin"></i> Cargando...
    </div>

    <template v-else>
      <!-- Column headers (desktop only) -->
      <div class="list-hdr">
        <span></span>
        <span class="hdr-main">Insumo</span>
        <span class="hdr-r tr">Stock actual</span>
        <span class="hdr-r tr">Stock mínimo</span>
        <span class="hdr-act tc">Historial</span>
      </div>

      <!-- Lista agrupada por categoría (cuando catFilter = '') -->
      <template v-if="catFilter === '' && groupedByCategory.length">
        <div v-for="group in groupedByCategory" :key="group.name" class="cat-group">
          <div class="cat-hdr">
            <i class="bi bi-tag-fill cat-ico"></i>
            <span class="cat-hdr-name">{{ group.name }}</span>
            <span class="cat-hdr-cnt">{{ group.items.length }} ítem{{ group.items.length !== 1 ? 's' : '' }}</span>
          </div>
          <div class="cards-list">
            <div v-for="r in group.items" :key="r.id_item" class="sc" :class="scCls(r)">
              <div class="sc-status">
                <span :class="statusBadge(r)" class="sb">{{ statusLbl(r) }}</span>
              </div>
              <div class="sc-main">
                <div class="sc-name">
                  {{ r.description }}
                  <span v-if="!r.is_active" class="badge-off">Inactivo</span>
                  <span v-if="r.code" class="sc-code">{{ r.code }}</span>
                </div>
              </div>
              <div class="sc-stock">
                <span :class="stockCls(r)" class="fw-b">{{ fmt(r.stock_qty) }}</span>
                <span class="sc-unit">{{ r.unit_name }}</span>
              </div>
              <div class="sc-min" @click.stop="startEdit(r)">
                <template v-if="editingId !== r.id_item">
                  <span class="min-lbl">Mín:</span>
                  <span class="min-val">{{ fmt(r.min_stock) }}<i class="bi bi-pencil-fill ei"></i></span>
                </template>
                <input v-else v-focus v-model.number="editVal" type="number" min="0" step="0.001"
                       class="inp-inline" @keyup.enter="saveMin(r)" @keyup.escape="editingId=null"
                       @blur="saveMin(r)" @click.stop />
              </div>
              <div class="sc-act">
                <button class="btn-mov" @click.stop="openMov(r)" title="Ver movimientos">
                  <i class="bi bi-clock-history"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
        <div v-if="!rows.length" class="empty-c">Sin insumos encontrados</div>
      </template>

      <!-- Lista plana (cuando se filtra por categoría específica) -->
      <template v-else>
        <div class="cards-list">
          <div v-for="r in rows" :key="r.id_item" class="sc" :class="scCls(r)">
            <div class="sc-status">
              <span :class="statusBadge(r)" class="sb">{{ statusLbl(r) }}</span>
            </div>
            <div class="sc-main">
              <div class="sc-name">
                {{ r.description }}
                <span v-if="!r.is_active" class="badge-off">Inactivo</span>
                <span v-if="r.code" class="sc-code">{{ r.code }}</span>
              </div>
              <div class="sc-cat">{{ r.category_name || '—' }}</div>
            </div>
            <div class="sc-stock">
              <span :class="stockCls(r)" class="fw-b">{{ fmt(r.stock_qty) }}</span>
              <span class="sc-unit">{{ r.unit_name }}</span>
            </div>
            <div class="sc-min" @click.stop="startEdit(r)">
              <template v-if="editingId !== r.id_item">
                <span class="min-lbl">Mín:</span>
                <span class="min-val">{{ fmt(r.min_stock) }}<i class="bi bi-pencil-fill ei"></i></span>
              </template>
              <input v-else v-focus v-model.number="editVal" type="number" min="0" step="0.001"
                     class="inp-inline" @keyup.enter="saveMin(r)" @keyup.escape="editingId=null"
                     @blur="saveMin(r)" @click.stop />
            </div>
            <div class="sc-act">
              <button class="btn-mov" @click.stop="openMov(r)" title="Ver movimientos">
                <i class="bi bi-clock-history"></i>
              </button>
            </div>
          </div>
          <div v-if="!rows.length" class="empty-c">Sin insumos encontrados</div>
        </div>
      </template>
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
          <div v-if="mov.loading" class="state-c"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
          <div v-else class="mov-tbl-wrap">
            <table class="mov-tbl">
              <thead>
                <tr><th>Fecha</th><th>Tipo</th><th class="tr">Δ</th><th class="tr">Antes</th><th class="tr">Después</th><th>Ref.</th><th>Usuario</th></tr>
              </thead>
              <tbody>
                <tr v-for="m in mov.data" :key="m.id" :class="movRowCls(m)">
                  <td class="sm">{{ fmtDate(m.movement_date || m.created_at) }}</td>
                  <td><span :class="movBadge(m)">{{ movLbl(m.movement_type) }}</span></td>
                  <td class="tr fw-b" :class="m.qty >= 0 ? 'c-green' : 'c-red'">{{ m.qty >= 0 ? '+' : '' }}{{ fmt(m.qty) }}</td>
                  <td class="tr sm td-muted">{{ fmt(m.qty_before) }}</td>
                  <td class="tr sm">{{ fmt(m.qty_after) }}</td>
                  <td class="sm td-muted">{{ m.reference_type }}{{ m.reference_id ? ' #'+m.reference_id : '' }}</td>
                  <td class="sm td-muted">{{ m.usuario }}</td>
                </tr>
                <tr v-if="!mov.data.length"><td colspan="7" class="empty-c">Sin movimientos</td></tr>
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
import ExportToolbar from '@/components/common/ExportToolbar.vue'

const vFocus = { mounted: el => el.focus() }

const rows       = ref([])
const categories = ref([])
const loading    = ref(true)

const search       = ref('')
const catFilter    = ref('')   // '' = todas
const activeFilter = ref('1')
const critFilter   = ref(false)
const editingId    = ref(null)
const editVal      = ref(0)
const mov          = ref({ show: false, item: null, loading: false, data: [] })

// ── Último inventario físico ─────────────────────────────────────────────────
const lastInventoryDate = computed(() => {
  const dates = rows.value
    .filter(r => r.last_inventory_date)
    .map(r => String(r.last_inventory_date).slice(0, 10))
  return dates.length ? dates.sort().at(-1) : null
})

// ── Agrupamiento por categoría (solo cuando catFilter = '') ──────────────────
const groupedByCategory = computed(() => {
  const nocat = 'Sin categoría'
  const map = {}
  for (const r of rows.value) {
    const key = r.category_name || nocat
    if (!map[key]) map[key] = { name: key, items: [] }
    map[key].items.push(r)
  }
  return Object.values(map).sort((a, b) =>
    a.name === nocat ? 1 : b.name === nocat ? -1 : a.name.localeCompare(b.name, 'es')
  )
})

// ── Export: datos con filas de cabecera de categoría cuando está en "todas" ──
const exportData = computed(() => {
  if (catFilter.value !== '') return rows.value
  const result = []
  for (const g of groupedByCategory.value) {
    result.push({ _sectionHeader: true, _title: g.name })
    result.push(...g.items)
  }
  return result
})

// ── Columnas de export: sin categoría cuando está agrupado ───────────────────
const exportCols = computed(() => {
  const base = [
    { key: 'code',        label: 'Código' },
    { key: 'description', label: 'Insumo' },
    { key: 'stock_qty',   label: 'Stock actual', fmt: v => Number(v||0).toFixed(4) },
    { key: 'unit_name',   label: 'Unidad' },
    { key: 'min_stock',   label: 'Stock mínimo', fmt: v => Number(v||0).toFixed(4) },
  ]
  if (catFilter.value !== '') {
    base.splice(2, 0, { key: 'category_name', label: 'Categoría' })
  }
  return base
})

const ctrlCount = computed(() => rows.value.filter(r => r.control_stock).length)
const critCount = computed(() => rows.value.filter(r => itemStatus(r) === 'critical').length)
const outCount  = computed(() => rows.value.filter(r => itemStatus(r) === 'out').length)

const fmt     = v => Number(v || 0).toLocaleString('es-CO', { maximumFractionDigits: 4 })
const fmtDate = v => v ? String(v).slice(0, 10) : '—'

function itemStatus(r) {
  if (!r.control_stock || !r.min_stock) return 'none'
  if ((r.stock_qty || 0) <= 0)          return 'out'
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
  return { 'b-out': s==='out', 'b-crit': s==='critical', 'b-ok': s==='ok', 'b-none': s==='none' }
}
function stockCls(r) {
  const s = itemStatus(r)
  return { 'c-red': s==='out', 'c-orange': s==='critical', 'c-green': s==='ok' }
}
function scCls(r) {
  const s = itemStatus(r)
  return { 'sc-out': s==='out', 'sc-crit': s==='critical' }
}

const MOV_LBL = { physical:'Inv.Físico', entry:'Entrada', exit:'Salida', sale_vb6:'VB6', sale_web:'Web', sale_online:'Online' }
function movLbl(t) { return MOV_LBL[t] || t }
function movRowCls(m) {
  if (m.movement_type === 'entry') return 'mr-entry'
  if (m.movement_type === 'exit' || m.movement_type?.startsWith('sale')) return 'mr-exit'
  if (m.movement_type === 'physical') return 'mr-phys'
  return ''
}
function movBadge(m) {
  const t = m.movement_type
  if (t === 'physical')       return 'mb mb-blue'
  if (t === 'entry')          return 'mb mb-green'
  if (t === 'exit')           return 'mb mb-orange'
  if (t?.startsWith('sale'))  return 'mb mb-red'
  return 'mb mb-gray'
}

let timer = null
function debouncedLoad() { clearTimeout(timer); timer = setTimeout(load, 350) }
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
  try {
    categories.value = (await api.get('/api/inventory/categories')).data
    // catFilter empieza vacío → muestra todas agrupadas
  } catch { categories.value = [] }
}

function startEdit(r) { editingId.value = r.id_item; editVal.value = r.min_stock || 0 }

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
  try { mov.value.data = (await api.get(`/api/inventory/movements/${r.id_item}`)).data }
  catch { mov.value.data = [] }
  finally { mov.value.loading = false }
}

onMounted(async () => {
  await loadCategories()
  load()
})
</script>

<style scoped>
.sv-wrap { padding: 16px; }

/* KPI */
.kpi-bar { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.kpi-card { flex: 1; min-width: 100px; background: #f8f9fa; border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; gap: 2px; border: 1px solid #e9ecef; }
.kpi-blue   { background: #eff6ff; border-color: #bfdbfe; }
.kpi-orange { background: #fff7ed; border-color: #fed7aa; }
.kpi-red    { background: #fff1f2; border-color: #fecdd3; }
.kpi-n { font-size: 1.5rem; font-weight: 700; line-height: 1; }
.kpi-l { font-size: .74rem; color: #6b7280; font-weight: 500; }
.kpi-blue .kpi-n   { color: #2563eb; }
.kpi-orange .kpi-n { color: #ea580c; }
.kpi-red .kpi-n    { color: #dc2626; }

/* Último inventario */
.inv-date-bar {
  display: flex; align-items: center; gap: 7px;
  background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px;
  padding: 7px 12px; margin-bottom: 10px; font-size: .83rem; color: #166534;
}
.inv-ico { color: #16a34a; font-size: .88rem; flex-shrink: 0; }

/* Agrupamiento por categoría */
.cat-group { margin-bottom: 18px; }
.cat-hdr {
  display: flex; align-items: center; gap: 8px;
  background: #1d4ed8; color: #fff;
  border-radius: 8px 8px 0 0; padding: 7px 14px; margin-bottom: 0;
}
.cat-ico { font-size: .8rem; flex-shrink: 0; }
.cat-hdr-name { font-weight: 700; font-size: .85rem; flex: 1; }
.cat-hdr-cnt {
  font-size: .74rem; background: rgba(255,255,255,.2);
  padding: 2px 8px; border-radius: 10px; white-space: nowrap;
}
/* cards dentro de grupo: bordes redondeados solo abajo */
.cat-group .cards-list { border: 1px solid #dbeafe; border-top: none; border-radius: 0 0 8px 8px; overflow: hidden; }
.cat-group .cards-list .sc { border-radius: 0; border-left: none; border-right: none; border-top: none; }
.cat-group .cards-list .sc:last-child { border-bottom: none; }

/* Filters */
.filters-bar { display: flex; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; align-items: center; }
.f-search-wrap { position: relative; flex: 1; min-width: 190px; }
.f-ico { position: absolute; left: 9px; top: 50%; transform: translateY(-50%); color: #9ca3af; font-size: .83rem; }
.f-inp { width: 100%; padding: 8px 10px 8px 28px; border: 1px solid #d1d5db; border-radius: 8px; font-size: .86rem; box-sizing: border-box; }
.f-sel { padding: 8px 10px; border: 1px solid #d1d5db; border-radius: 8px; font-size: .86rem; background: #fff; }
.toggle-grp { display: flex; border: 1px solid #d1d5db; border-radius: 8px; overflow: hidden; }
.tog    { padding: 7px 12px; background: #fff; border: none; cursor: pointer; font-size: .81rem; color: #374151; }
.tog-on { padding: 7px 12px; background: #2563eb; color: #fff; border: none; cursor: pointer; font-size: .81rem; font-weight: 600; }
.crit-lbl { display: flex; align-items: center; gap: 5px; font-size: .82rem; cursor: pointer; white-space: nowrap; }
.crit-chk { cursor: pointer; }

/* Loading / empty */
.state-c { text-align: center; padding: 40px; color: #6b7280; }
.spin { animation: spin 1s linear infinite; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }
.empty-c { text-align: center; padding: 30px; color: #9ca3af; font-size: .87rem; }

/* Column headers (desktop) */
.list-hdr {
  display: none;
  padding: 4px 14px;
  font-size: .72rem; font-weight: 700; color: #9ca3af; text-transform: uppercase; letter-spacing: .04em;
  margin-bottom: 2px;
}
.hdr-main { flex: 1; }
.hdr-r    { width: 120px; }
.hdr-act  { width: 50px; }

/* Cards list */
.cards-list { display: flex; flex-direction: column; gap: 6px; }

.sc {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px;
  background: #fff; border: 1px solid #e9ecef; border-radius: 10px;
  transition: box-shadow .15s;
}
.sc:hover { box-shadow: 0 2px 10px rgba(0,0,0,.07); }
.sc-out  { border-left: 4px solid #dc2626; background: #fff5f5; }
.sc-crit { border-left: 4px solid #ea580c; background: #fffbf0; }

/* Status col */
.sc-status { flex-shrink: 0; }
.sb { padding: 3px 8px; border-radius: 20px; font-size: .73rem; font-weight: 600; white-space: nowrap; }
.b-out  { background: #fee2e2; color: #dc2626; }
.b-crit { background: #ffedd5; color: #ea580c; }
.b-ok   { background: #dcfce7; color: #16a34a; }
.b-none { background: #f3f4f6; color: #9ca3af; }

/* Main (name+cat) */
.sc-main { flex: 1; min-width: 0; }
.sc-name { font-weight: 700; font-size: .88rem; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.sc-code { font-size: .72rem; color: #9ca3af; font-weight: 400; }
.sc-cat  { font-size: .77rem; color: #6b7280; margin-top: 1px; }
.badge-off { background: #f3f4f6; color: #9ca3af; padding: 1px 5px; border-radius: 10px; font-size: .7rem; font-weight: 400; }

/* Stock */
.sc-stock { display: flex; flex-direction: column; align-items: flex-end; flex-shrink: 0; width: 90px; }
.sc-unit  { font-size: .73rem; color: #9ca3af; }

/* Min */
.sc-min { display: flex; align-items: center; gap: 4px; cursor: pointer; flex-shrink: 0; width: 100px; justify-content: flex-end; }
.min-lbl { font-size: .73rem; color: #9ca3af; }
.min-val { font-size: .84rem; }
.ei { font-size: .62rem; color: #9ca3af; margin-left: 3px; }
.inp-inline { width: 72px; padding: 3px 6px; border: 1.5px solid #2563eb; border-radius: 5px; font-size: .84rem; text-align: right; }

/* Action */
.sc-act { flex-shrink: 0; }
.btn-mov { background: #f3f4f6; border: 1px solid #e5e7eb; border-radius: 7px; padding: 5px 9px; cursor: pointer; color: #4b5563; font-size: .82rem; }
.btn-mov:hover { background: #eff6ff; border-color: #bfdbfe; color: #2563eb; }

/* Shared */
.tr { text-align: right; }
.tc { text-align: center; }
.fw-b { font-weight: 700; }
.td-muted { color: #6b7280; }
.sm { font-size: .79rem; }
.c-red    { color: #dc2626; }
.c-orange { color: #ea580c; }
.c-green  { color: #16a34a; }

/* Movements modal */
.modal-bg { position: fixed; inset: 0; background: rgba(0,0,0,.45); z-index: 1100; display: flex; align-items: center; justify-content: center; padding: 12px; }
.mov-panel { background: #fff; border-radius: 14px; width: 100%; max-width: 840px; max-height: 88vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,.2); }
.mov-hdr { display: flex; justify-content: space-between; align-items: flex-start; padding: 16px 20px 12px; border-bottom: 1px solid #e9ecef; gap: 10px; }
.mov-title { font-weight: 700; font-size: .98rem; margin-bottom: 2px; }
.btn-close-x { background: none; border: none; padding: 4px; cursor: pointer; color: #6b7280; font-size: 1.1rem; }
.btn-close-x:hover { color: #111; }
.mov-tbl-wrap { overflow: auto; flex: 1; }
.mov-tbl { width: 100%; border-collapse: collapse; font-size: .82rem; }
.mov-tbl th { background: #f8f9fa; padding: 8px 10px; text-align: left; font-weight: 600; border-bottom: 2px solid #dee2e6; white-space: nowrap; position: sticky; top: 0; }
.mov-tbl td { padding: 7px 10px; border-bottom: 1px solid #f0f0f0; }
.mr-entry { background: #f0fdf4 !important; }
.mr-exit  { background: #fff5f5 !important; }
.mr-phys  { background: #eff6ff !important; }
.mb { padding: 2px 6px; border-radius: 20px; font-size: .71rem; font-weight: 600; white-space: nowrap; }
.mb-blue   { background: #dbeafe; color: #1d4ed8; }
.mb-green  { background: #dcfce7; color: #16a34a; }
.mb-orange { background: #ffedd5; color: #ea580c; }
.mb-red    { background: #fee2e2; color: #dc2626; }
.mb-gray   { background: #f3f4f6; color: #6b7280; }

/* Desktop: show header + wider cards */
@media (min-width: 768px) {
  .list-hdr { display: flex; align-items: center; }
  .sc { gap: 14px; }
  .sc-stock { width: 120px; }
  .sc-min   { width: 120px; }
  .mov-panel { max-height: 82vh; }
}

/* Tablet */
@media (max-width: 767px) and (min-width: 577px) {
  .sc-stock { width: 80px; }
  .sc-min   { width: 90px; }
}

/* Mobile */
@media (max-width: 576px) {
  .sv-wrap { padding: 10px; }
  .kpi-bar { gap: 6px; }
  .kpi-card { padding: 9px 10px; min-width: 70px; }
  .kpi-n { font-size: 1.2rem; }
  .filters-bar { flex-direction: column; align-items: stretch; }
  .f-search-wrap { min-width: unset; }
  .toggle-grp .tog, .toggle-grp .tog-on { padding: 6px 8px; font-size: .78rem; }
  /* Stack card right side */
  .sc { flex-wrap: wrap; gap: 8px; }
  .sc-status { width: 100%; order: -1; }
  .sc-main   { width: 100%; order: 0; }
  .sc-stock  { width: auto; order: 1; }
  .sc-min    { width: auto; order: 2; }
  .sc-act    { order: 3; margin-left: auto; }
  /* Modal */
  .mov-panel { max-height: 92vh; border-radius: 14px 14px 0 0; align-self: flex-end; }
}
</style>
