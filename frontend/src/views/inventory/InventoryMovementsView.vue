<template>
  <div class="mv-wrap">

    <!-- Type pills -->
    <div class="type-pills">
      <button v-for="t in TYPES" :key="t.val"
        :class="['pill', { 'pill-on': typeFilter === t.val }, `pill-${t.color}`]"
        @click="setType(t.val)">
        {{ t.label }}
      </button>
    </div>

    <!-- Filters bar -->
    <div class="filters-bar">
      <div class="f-search-wrap">
        <i class="bi bi-search f-ico"></i>
        <input v-model.trim="searchItem" @input="filterClient" class="f-inp" placeholder="Buscar insumo..." />
      </div>

      <div class="date-row">
        <CustomDatePicker v-model="desde" @update:modelValue="load" placeholder="Desde" />
        <span class="date-sep">→</span>
        <CustomDatePicker v-model="hasta" @update:modelValue="load" placeholder="Hasta" />
      </div>

      <button class="btn-clear" @click="clearFilters" title="Limpiar filtros">
        <i class="bi bi-x-circle"></i>
      </button>

      <ExportToolbar
        :data="displayed"
        :columns="exportCols"
        filename="movimientos-stock"
        title="Movimientos de Stock"
      />
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
      <!-- Column headers (desktop) -->
      <div class="list-hdr">
        <span class="hdr-date">Fecha</span>
        <span class="hdr-item">Insumo</span>
        <span class="hdr-type">Tipo</span>
        <span class="hdr-qty tr">Δ Cantidad</span>
        <span class="hdr-qty tr">Antes</span>
        <span class="hdr-qty tr">Después</span>
        <span class="hdr-ref">Referencia</span>
        <span class="hdr-usr">Usuario</span>
      </div>

      <!-- Cards -->
      <div class="cards-list">
        <div v-for="m in displayed" :key="m.id" class="mc" :class="mcCls(m)">

          <!-- Left: date + user (narrow col on desktop) -->
          <div class="mc-meta">
            <span class="mc-date">{{ fmtDate(m.movement_date || m.created_at) }}</span>
            <span class="mc-usr td-muted">{{ m.usuario || '—' }}</span>
          </div>

          <!-- Center: item + type -->
          <div class="mc-main">
            <div class="mc-name">{{ m.item_name }}</div>
            <div class="mc-sub">
              <span :class="typeBadge(m)">{{ typeLbl(m.movement_type) }}</span>
              <span v-if="m.unit_name" class="td-muted">{{ m.unit_name }}</span>
            </div>
          </div>

          <!-- Right: qty deltas -->
          <div class="mc-nums">
            <div class="mc-delta fw-b" :class="m.qty >= 0 ? 'c-green' : 'c-red'">
              {{ m.qty >= 0 ? '+' : '' }}{{ fmt(m.qty) }}
            </div>
            <div class="mc-flow td-muted">
              {{ fmt(m.qty_before) }} → {{ fmt(m.qty_after) }}
            </div>
            <div v-if="m.reference_type" class="mc-ref td-muted">
              {{ m.reference_type }}{{ m.reference_id ? ' #'+m.reference_id : '' }}
            </div>
          </div>

        </div>
        <div v-if="!displayed.length" class="empty-c">Sin movimientos encontrados</div>
      </div>
    </template>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/apis'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'
import ExportToolbar    from '@/components/common/ExportToolbar.vue'

const allMovements = ref([])
const displayed    = ref([])
const loading      = ref(true)

const searchItem  = ref('')
const typeFilter  = ref('sale')
const desde       = ref('')
const hasta       = ref('')

const TYPES = [
  { val: '',         label: 'Todos',     color: 'gray'   },
  { val: 'physical', label: 'Físico',    color: 'blue'   },
  { val: 'entry',    label: 'Entrada',   color: 'green'  },
  { val: 'exit',     label: 'Salida',    color: 'orange' },
  { val: 'sale',     label: 'Ventas',    color: 'red'    },
]

const exportCols = [
  { key: 'movement_date', label: 'Fecha',    fmt: v => v ? String(v).slice(0,10) : '' },
  { key: 'item_name',     label: 'Insumo' },
  { key: 'movement_type', label: 'Tipo' },
  { key: 'qty',           label: 'Δ Cant.',  fmt: v => Number(v||0).toFixed(4) },
  { key: 'qty_before',    label: 'Antes',    fmt: v => Number(v||0).toFixed(4) },
  { key: 'qty_after',     label: 'Después',  fmt: v => Number(v||0).toFixed(4) },
  { key: 'unit_name',     label: 'Unidad' },
  { key: 'reference_type',label: 'Ref. tipo' },
  { key: 'usuario',       label: 'Usuario' },
]

const fmt     = v => Number(v || 0).toLocaleString('es-CO', { maximumFractionDigits: 4 })
const fmtDate = v => v ? String(v).slice(0, 10) : '—'

const TYPE_LBL = {
  physical: 'Inv. Físico', entry: 'Entrada', exit: 'Salida',
  sale_vb6: 'Venta VB6', sale_web: 'Venta Web', sale_online: 'Venta Online',
}
function typeLbl(t) { return TYPE_LBL[t] || t }

function typeBadge(m) {
  const t = m.movement_type
  if (t === 'physical')      return 'tb tb-blue'
  if (t === 'entry')         return 'tb tb-green'
  if (t === 'exit')          return 'tb tb-orange'
  if (t?.startsWith('sale')) return 'tb tb-red'
  return 'tb tb-gray'
}

function mcCls(m) {
  const t = m.movement_type
  if (t === 'entry')         return 'mc-entry'
  if (t === 'physical')      return 'mc-phys'
  if (t === 'exit')          return 'mc-exit'
  if (t?.startsWith('sale')) return 'mc-sale'
  return ''
}

function todayISO() {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Bogota' }).format(new Date())
}

function setType(val) { typeFilter.value = val; load() }

async function load() {
  loading.value = true
  try {
    const p = {}
    if (typeFilter.value) p.mtype = typeFilter.value
    if (desde.value)      p.desde = desde.value
    if (hasta.value)      p.hasta = hasta.value
    allMovements.value = (await api.get('/api/inventory/movements', { params: p })).data
    filterClient()
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

function filterClient() {
  const q = searchItem.value.toLowerCase()
  displayed.value = q
    ? allMovements.value.filter(m => (m.item_name || '').toLowerCase().includes(q))
    : [...allMovements.value]
}

function clearFilters() {
  searchItem.value = ''
  typeFilter.value = 'sale'
  desde.value      = todayISO()
  hasta.value      = todayISO()
  load()
}

onMounted(() => {
  desde.value = todayISO()
  hasta.value = todayISO()
  load()
})
</script>

<style scoped>
.mv-wrap { padding: 16px; }

/* Type pills */
.type-pills { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 12px; }
.pill {
  padding: 5px 14px; border-radius: 20px; border: 1.5px solid transparent;
  font-size: .82rem; font-weight: 600; cursor: pointer; background: #f3f4f6; color: #374151;
  transition: background .15s, color .15s, border-color .15s;
}
.pill:hover { filter: brightness(.95); }
.pill-on.pill-gray   { background: #6b7280; color: #fff; border-color: #6b7280; }
.pill-on.pill-blue   { background: #1d4ed8; color: #fff; border-color: #1d4ed8; }
.pill-on.pill-green  { background: #16a34a; color: #fff; border-color: #16a34a; }
.pill-on.pill-orange { background: #ea580c; color: #fff; border-color: #ea580c; }
.pill-on.pill-red    { background: #dc2626; color: #fff; border-color: #dc2626; }

/* Filters bar */
.filters-bar { display: flex; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; align-items: center; }
.f-search-wrap { position: relative; flex: 1; min-width: 170px; }
.f-ico { position: absolute; left: 9px; top: 50%; transform: translateY(-50%); color: #9ca3af; font-size: .83rem; }
.f-inp { width: 100%; padding: 8px 10px 8px 28px; border: 1px solid #d1d5db; border-radius: 8px; font-size: .86rem; box-sizing: border-box; }
.date-row { display: flex; align-items: center; gap: 6px; }
.date-sep { color: #9ca3af; font-size: .85rem; }
.btn-clear { background: none; border: 1px solid #e5e7eb; border-radius: 8px; padding: 7px 10px; cursor: pointer; color: #9ca3af; font-size: .88rem; }
.btn-clear:hover { border-color: #dc2626; color: #dc2626; }

/* Info bar */
.info-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 8px; }
.info-cnt { font-size: .82rem; color: #6b7280; }
.legend { display: flex; gap: 8px; flex-wrap: wrap; }
.lg { padding: 2px 8px; border-radius: 20px; font-size: .71rem; font-weight: 600; }
.lg-phys  { background: #dbeafe; color: #1d4ed8; }
.lg-entry { background: #dcfce7; color: #16a34a; }
.lg-exit  { background: #ffedd5; color: #ea580c; }
.lg-sale  { background: #fee2e2; color: #dc2626; }

/* Loading / empty */
.state-c { text-align: center; padding: 40px; color: #6b7280; }
.spin { animation: spin 1s linear infinite; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }
.empty-c { text-align: center; padding: 30px; color: #9ca3af; font-size: .87rem; }

/* Column headers (desktop) */
.list-hdr {
  display: none;
  padding: 4px 14px;
  font-size: .71rem; font-weight: 700; color: #9ca3af; text-transform: uppercase; letter-spacing: .04em;
  margin-bottom: 2px;
}
.hdr-date { width: 80px; flex-shrink: 0; }
.hdr-item { flex: 1; }
.hdr-type { width: 100px; flex-shrink: 0; }
.hdr-qty  { width: 80px; flex-shrink: 0; }
.hdr-ref  { width: 100px; flex-shrink: 0; }
.hdr-usr  { width: 80px; flex-shrink: 0; }

/* Cards list */
.cards-list { display: flex; flex-direction: column; gap: 5px; }

.mc {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 14px;
  background: #fff; border: 1px solid #e9ecef; border-radius: 9px;
  transition: box-shadow .15s;
}
.mc:hover { box-shadow: 0 2px 8px rgba(0,0,0,.07); }
.mc-entry { border-left: 4px solid #16a34a; background: #f0fdf4; }
.mc-phys  { border-left: 4px solid #1d4ed8; background: #eff6ff; }
.mc-exit  { border-left: 4px solid #ea580c; background: #fff7ed; }
.mc-sale  { border-left: 4px solid #dc2626; background: #fff5f5; }

/* Meta col (date + user) */
.mc-meta { flex-shrink: 0; display: flex; flex-direction: column; gap: 2px; width: 70px; }
.mc-date { font-size: .78rem; font-weight: 600; color: #374151; }
.mc-usr  { font-size: .72rem; }

/* Main col (item + badge) */
.mc-main { flex: 1; min-width: 0; }
.mc-name { font-weight: 700; font-size: .87rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.mc-sub  { display: flex; align-items: center; gap: 6px; margin-top: 2px; flex-wrap: wrap; }

/* Nums col (delta + flow + ref) */
.mc-nums { flex-shrink: 0; display: flex; flex-direction: column; align-items: flex-end; gap: 1px; }
.mc-delta { font-size: .9rem; }
.mc-flow  { font-size: .75rem; }
.mc-ref   { font-size: .72rem; }

/* Badges */
.tb { padding: 2px 7px; border-radius: 20px; font-size: .71rem; font-weight: 600; white-space: nowrap; }
.tb-blue   { background: #dbeafe; color: #1d4ed8; }
.tb-green  { background: #dcfce7; color: #16a34a; }
.tb-orange { background: #ffedd5; color: #ea580c; }
.tb-red    { background: #fee2e2; color: #dc2626; }
.tb-gray   { background: #f3f4f6; color: #6b7280; }

/* Shared */
.tr { text-align: right; }
.fw-b { font-weight: 700; }
.td-muted { color: #6b7280; }
.c-green { color: #16a34a; }
.c-red   { color: #dc2626; }

/* Desktop: row layout + header */
@media (min-width: 768px) {
  .list-hdr { display: flex; align-items: center; }
  .mc { gap: 14px; }
  .mc-meta { width: 82px; }
  .mc-nums { align-items: flex-end; min-width: 280px; flex-direction: row; align-items: center; gap: 16px; }
  .mc-delta { min-width: 80px; text-align: right; }
  .mc-flow  { min-width: 110px; text-align: right; }
  .mc-ref   { min-width: 90px; text-align: right; }
}

/* Tablet */
@media (max-width: 767px) and (min-width: 577px) {
  .mc-meta { width: 75px; }
}

/* Mobile */
@media (max-width: 576px) {
  .mv-wrap { padding: 10px; }
  .filters-bar { flex-direction: column; align-items: stretch; }
  .date-row { justify-content: space-between; }
  .mc { flex-wrap: wrap; gap: 6px; }
  .mc-meta { width: 100%; flex-direction: row; justify-content: space-between; order: 0; }
  .mc-main { width: 100%; order: 1; }
  .mc-nums { width: 100%; flex-direction: row; flex-wrap: wrap; align-items: flex-start; gap: 10px; order: 2; }
  .mc-delta { min-width: unset; font-size: .88rem; }
  .mc-flow  { min-width: unset; font-size: .74rem; }
}
</style>
