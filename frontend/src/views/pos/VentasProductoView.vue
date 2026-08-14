<template>
  <div class="vp-wrap">

    <!-- ── Tabs de navegación ─────────────────────────────── -->
    <div class="vp-tabs">
      <RouterLink to="/pos/consultas/ventas"         class="vp-tab">Consulta Ventas</RouterLink>
      <RouterLink to="/pos/consultas/ventas-producto" class="vp-tab">Venta x Producto</RouterLink>
      <RouterLink to="/pos/consultas/ventas-insumo"   class="vp-tab">Venta x Insumo</RouterLink>
    </div>

    <!-- ── Filtros (colapsable) ──────────────────────────── -->
    <div class="vp-filters card">
      <div class="vp-filters-head" @click="filtrosVisible = !filtrosVisible">
        <span class="vp-filters-label">
          <i class="bi bi-funnel-fill me-1"></i>
          <span>Filtros</span>
          <span v-if="!filtrosVisible && lista.length" class="vp-filters-hint">
            {{ fmtFecha(filtro.desde) }} — {{ fmtFecha(filtro.hasta) }}
            <template v-if="filtro.categoriaNombre"> · {{ filtro.categoriaNombre }}</template>
          </span>
        </span>
        <i :class="filtrosVisible ? 'bi bi-chevron-up' : 'bi bi-chevron-down'" class="vp-chevron"></i>
      </div>

      <div v-show="filtrosVisible" class="vp-filters-body">
        <div class="vp-filter-row">

          <!-- Tipo -->
          <div class="vp-filter-group">
            <label class="vp-label">Tipo</label>
            <div class="vp-radios">
              <label v-for="op in tipoOpts" :key="op.value" class="vp-radio">
                <input type="radio" v-model="filtro.tipo" :value="op.value" @change="buscar" />
                {{ op.label }}
              </label>
            </div>
          </div>

          <!-- Fechas -->
          <div class="vp-filter-group">
            <label class="vp-label">Desde / Hasta</label>
            <div class="vp-fechas-row">
              <CustomDatePicker v-model="filtro.desde" @update:modelValue="buscar" style="width:140px" />
              <span class="vp-fecha-sep">—</span>
              <CustomDatePicker v-model="filtro.hasta" @update:modelValue="buscar" style="width:140px" />
            </div>
          </div>

          <!-- Categoría -->
          <div class="vp-filter-group">
            <label class="vp-label">Categoría</label>
            <select class="vp-select" v-model="filtro.catId" @change="buscar">
              <option :value="null">Todas</option>
              <option v-for="c in categorias" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>

          <!-- Acciones -->
          <div class="vp-btns-group">
            <button class="btn btn-outline-secondary vp-btn-hoy" @click="irHoy">
              <i class="bi bi-calendar-check"></i><span>Hoy</span>
            </button>
            <button class="btn btn-primary vp-btn-buscar" @click="buscar" :disabled="cargando">
              <i class="bi bi-search"></i><span>Buscar</span>
            </button>
            <button class="btn btn-outline-primary vp-btn-refresh" @click="buscar" :disabled="cargando" title="Actualizar">
              <i class="bi bi-arrow-clockwise" :class="{ spin: cargando }"></i>
            </button>
            <ExportToolbar
              v-if="lista.length"
              :data="lista"
              :columns="exportColumns"
              :filename="`venta-producto_${filtro.desde}_${filtro.hasta}`"
              :title="`Venta x Producto — ${fmtFecha(filtro.desde)} al ${fmtFecha(filtro.hasta)}`"
              :companyId="selectedCid"
              :companyName="companyStore.selectedCompany?.name || 'EasyPOS'"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- ── KPI chips ─────────────────────────────────────── -->
    <div v-if="!cargando && lista.length" class="vp-kpi-bar">
      <span class="vp-kpi-chip">
        <span class="vp-kpi-lbl">{{ lista.length }} productos</span>
      </span>
      <span class="vp-kpi-chip vp-kpi--orange">
        <span class="vp-kpi-lbl">Cant. Total</span>
        <strong>{{ totalCantidad }}</strong>
      </span>
      <span class="vp-kpi-chip vp-kpi--green">
        <span class="vp-kpi-lbl">Total Ventas</span>
        <strong>{{ fmt(totalDinero) }}</strong>
      </span>
    </div>

    <!-- ── Tabla ─────────────────────────────────────────── -->
    <div class="vp-table-wrap card">

      <!-- Loading -->
      <div v-if="cargando" class="vp-placeholder">
        <div class="spinner-border text-primary" style="width:2rem;height:2rem;"></div>
      </div>

      <!-- Sin datos -->
      <div v-else-if="!lista.length" class="vp-placeholder text-muted">
        <i class="bi bi-bag-x fs-2"></i>
        <p class="mt-2 mb-0">Sin resultados. Ajusta los filtros y busca.</p>
      </div>

      <!-- Datos -->
      <template v-else>
        <!-- Buscador interno -->
        <div class="vp-search-bar">
          <i class="bi bi-search vp-search-ico"></i>
          <input v-model.trim="busqueda" class="vp-search-inp" placeholder="Filtrar por producto o categoría..." />
          <button v-if="busqueda" class="vp-search-clear" @click="busqueda=''">
            <i class="bi bi-x-circle"></i>
          </button>
        </div>

        <div class="vp-table-scroll">
          <table class="vp-table">
            <thead>
              <tr>
                <th @click="sortBy('categoria')" class="sortable">
                  Categoría <i :class="sortIcon('categoria')"></i>
                </th>
                <th @click="sortBy('plato')" class="sortable">
                  Plato / Producto <i :class="sortIcon('plato')"></i>
                </th>
                <th class="ta-r" @click="sortBy('cantidad')" style="cursor:pointer">
                  Cant. <i :class="sortIcon('cantidad')"></i>
                </th>
                <th class="ta-r" @click="sortBy('total')" style="cursor:pointer">
                  Total <i :class="sortIcon('total')"></i>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(row, i) in listaFiltrada"
                :key="i"
                class="vp-row"
              >
                <td>
                  <span class="vp-cat-badge">{{ row.categoria }}</span>
                </td>
                <td class="vp-plato">{{ row.plato }}</td>
                <td class="ta-r vp-cant">{{ row.cantidad }}</td>
                <td class="ta-r vp-total">{{ fmt(row.total) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </div>


  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/apis.js'
import { useCompanyStore } from '@/stores/companyStore'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'
import ExportToolbar from '@/components/common/ExportToolbar.vue'

const companyStore = useCompanyStore()
const selectedCid  = computed(() => companyStore.selectedCompany?.id || undefined)

const fmtCOP = new Intl.NumberFormat('es-CO', { style:'currency', currency:'COP', minimumFractionDigits:0 })
const fmt    = v => fmtCOP.format(v || 0)

function localDate() {
  return new Intl.DateTimeFormat('en-CA', { timeZone:'America/Bogota' }).format(new Date())
}
function fmtFecha(iso) {
  if (!iso) return ''
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

const tipoOpts = [
  { value:'ambos',   label:'Ambos' },
  { value:'factura', label:'Facturas' },
  { value:'recibo',  label:'Recibos' },
]

const filtro         = ref({ tipo:'ambos', desde:localDate(), hasta:localDate(), catId:null, categoriaNombre:'' })
const filtrosVisible = ref(true)
const cargando       = ref(false)
const lista          = ref([])
const categorias     = ref([])
const busqueda       = ref('')

// Sort
const sortCol = ref('total')
const sortDir = ref(-1)  // -1 desc, 1 asc

function sortBy(col) {
  if (sortCol.value === col) sortDir.value *= -1
  else { sortCol.value = col; sortDir.value = col === 'total' || col === 'cantidad' ? -1 : 1 }
}
function sortIcon(col) {
  if (sortCol.value !== col) return 'bi bi-chevron-expand text-muted opacity-50'
  return sortDir.value === -1 ? 'bi bi-chevron-down' : 'bi bi-chevron-up'
}

const listaFiltrada = computed(() => {
  let rows = lista.value
  if (busqueda.value) {
    const q = busqueda.value.toLowerCase()
    rows = rows.filter(r =>
      r.plato?.toLowerCase().includes(q) || r.categoria?.toLowerCase().includes(q)
    )
  }
  const col = sortCol.value
  const dir = sortDir.value
  return [...rows].sort((a, b) => {
    const av = a[col] ?? ''
    const bv = b[col] ?? ''
    return av < bv ? -dir : av > bv ? dir : 0
  })
})

const totalCantidad = computed(() => lista.value.reduce((s, r) => s + (r.cantidad || 0), 0))
const totalDinero   = computed(() => lista.value.reduce((s, r) => s + (r.total    || 0), 0))

const fmtCOPRaw = v => new Intl.NumberFormat('es-CO', { style:'currency', currency:'COP', minimumFractionDigits:0 }).format(v || 0)

const exportColumns = [
  { key: 'categoria', label: 'Categoría' },
  { key: 'plato',     label: 'Plato / Producto' },
  { key: 'cantidad',  label: 'Cant.', align: 'right' },
  { key: 'total',     label: 'Total', align: 'right', fmt: v => fmtCOPRaw(v) },
]

async function cargarCategorias() {
  try {
    const { data } = await api.get('/api/pos-consultas/categorias-platos', {
      params: { company_id: selectedCid.value }
    })
    categorias.value = data
  } catch(e) { console.error(e) }
}

async function buscar() {
  cargando.value = true
  try {
    const { data } = await api.get('/api/pos-consultas/ventas-producto', {
      params: {
        desde:      filtro.value.desde,
        hasta:      filtro.value.hasta,
        tipo:       filtro.value.tipo,
        cat_id:     filtro.value.catId || undefined,
        company_id: selectedCid.value,
      }
    })
    lista.value = data
    if (data.length) filtrosVisible.value = false
  } catch(e) {
    console.error(e); lista.value = []
  } finally {
    cargando.value = false
  }
}

function irHoy() {
  const hoy = localDate()
  filtro.value = { tipo:'ambos', desde:hoy, hasta:hoy, catId:null, categoriaNombre:'' }
  buscar()
}


onMounted(async () => {
  await cargarCategorias()
  await buscar()
})
</script>

<style scoped>
/* ── Layout ─────────────────────────────────────────────── */
.vp-wrap {
  display: flex; flex-direction: column;
  height: 100%; gap: 10px;
}

.card {
  border-radius: 10px; border: 1px solid #e2e8f0; background: #fff;
}

/* ── Tabs ───────────────────────────────────────────────── */
.vp-tabs {
  display: flex; gap: 4px; flex-shrink: 0;
  border-bottom: 2px solid #e2e8f0; padding-bottom: 0;
}
.vp-tab {
  padding: 8px 16px; font-size: 13px; font-weight: 600;
  color: #64748b; text-decoration: none; border-radius: 8px 8px 0 0;
  border: 1px solid transparent; border-bottom: none;
  transition: all .15s; white-space: nowrap;
}
.vp-tab:hover { color: #1e40af; background: #f1f5f9; }
.vp-tab.router-link-active {
  color: #1e40af; background: #fff;
  border-color: #e2e8f0; border-bottom-color: #fff;
  margin-bottom: -2px;
}

/* ── Filtros ─────────────────────────────────────────────── */
.vp-filters { flex-shrink: 0; }
.vp-filters-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 16px; cursor: pointer; user-select: none;
}
.vp-filters-head:hover { background: #f8fafc; border-radius: 10px; }
.vp-filters-label { display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 700; color: #1e293b; }
.vp-filters-hint  { font-size: 11px; font-weight: 400; color: #64748b; margin-left: 6px; }
.vp-chevron { font-size: 13px; color: #64748b; }
.vp-filters-body { padding: 0 16px 12px; }
.vp-filter-row { display: flex; align-items: flex-end; gap: 12px; flex-wrap: wrap; }
.vp-filter-group { display: flex; flex-direction: column; gap: 4px; }
.vp-label { font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: .4px; }
.vp-radios { display: flex; gap: 12px; }
.vp-radio  { display: flex; align-items: center; gap: 4px; font-size: 14px; cursor: pointer; }
.vp-fechas-row { display: flex; align-items: center; gap: 6px; }
.vp-fecha-sep  { color: #94a3b8; font-size: 13px; flex-shrink: 0; }
.vp-select {
  height: 34px; border: 1px solid #cbd5e1; border-radius: 6px;
  padding: 0 10px; font-size: 13px; background: #f8fafc; outline: none; min-width: 150px;
}
.vp-select:focus { border-color: #3b82f6; background: #fff; }
.vp-btns-group { display: flex; gap: 6px; align-items: flex-end; }
.vp-btn-hoy, .vp-btn-buscar, .vp-btn-refresh, .vp-btn-print {
  height: 34px; display: flex; align-items: center; gap: 6px; white-space: nowrap;
}
.vp-btn-hoy, .vp-btn-buscar { padding: 0 14px; }
.vp-btn-refresh, .vp-btn-print { padding: 0 10px; }

/* ── KPI ─────────────────────────────────────────────────── */
.vp-kpi-bar {
  display: flex; flex-wrap: wrap; gap: 8px; flex-shrink: 0; padding: 4px 4px;
}
.vp-kpi-chip {
  display: flex; align-items: center; gap: 5px;
  background: #f1f5f9; border-radius: 8px; padding: 4px 12px;
  font-size: 13px; border-left: 3px solid #cbd5e1;
}
.vp-kpi--green  { background:#f0fdf4; color:#15803d; border-left-color:#22c55e; }
.vp-kpi--orange { background:#fff7ed; color:#c2410c; border-left-color:#f97316; }
.vp-kpi-lbl { font-size:10px; font-weight:600; text-transform:uppercase; letter-spacing:.3px; opacity:.7; margin-right:3px; }

/* ── Tabla ──────────────────────────────────────────────── */
.vp-table-wrap { flex: 1; display: flex; flex-direction: column; min-height: 0; overflow: hidden; }

.vp-placeholder {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center; color: #94a3b8; padding: 32px;
}

.vp-search-bar {
  display: flex; align-items: center; gap: 6px;
  padding: 10px 14px; border-bottom: 1px solid #f1f5f9; flex-shrink: 0;
}
.vp-search-ico { color: #94a3b8; font-size: 14px; }
.vp-search-inp {
  flex: 1; border: none; outline: none; font-size: 13px;
  background: transparent; color: #1e293b;
}
.vp-search-clear { background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 14px; }

.vp-table-scroll { flex: 1; overflow-y: auto; }

.vp-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.vp-table thead th {
  position: sticky; top: 0; background: #f8fafc;
  padding: 8px 12px; font-size: 11px; font-weight: 700;
  text-transform: uppercase; color: #64748b;
  border-bottom: 1px solid #e2e8f0; letter-spacing: .3px; z-index: 1;
}
.vp-table thead th.sortable { cursor: pointer; user-select: none; }
.vp-table thead th.sortable:hover { color: #1e40af; }
.vp-table td { padding: 9px 12px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.vp-row:hover td { background: #f8fafc; }

.ta-r { text-align: right; }

.vp-cat-badge {
  display: inline-block; font-size: 11px; font-weight: 600;
  background: #eff6ff; color: #1e40af; border-radius: 12px;
  padding: 2px 8px; white-space: nowrap;
}
.vp-plato { font-weight: 600; color: #1e293b; }
.vp-cant  { font-weight: 700; color: #c2410c; }
.vp-total { font-weight: 700; color: #16a34a; }

@keyframes spin { to { transform: rotate(360deg); } }
.spin { display: inline-block; animation: spin .7s linear infinite; }

/* ── RESPONSIVE TABLET ──────────────────────────────────── */
@media (max-width: 768px) {
  .vp-wrap { height: auto; min-height: 100%; }
  .vp-table-wrap { flex: none; overflow: visible; }
  .vp-table-scroll { overflow: visible; height: auto; }
  .vp-btn-buscar span, .vp-btn-hoy span { display: none; }
  .vp-btn-buscar, .vp-btn-hoy { padding: 0 10px; }
  .vp-tab { padding: 6px 10px; font-size: 12px; }
}

/* ── RESPONSIVE MÓVIL PEQUEÑO ───────────────────────────── */
@media (max-width: 576px) {
  .vp-filters-body { padding: 0 12px 10px; }
  .vp-filter-row { flex-direction: column; align-items: stretch; }
  .vp-btns-group { flex-direction: row; }
  .vp-btn-buscar { flex: 1; justify-content: center; }
  .vp-btn-hoy    { flex: 1; justify-content: center; }
  .vp-btn-buscar span, .vp-btn-hoy span { display: inline; }
  .vp-radios { flex-wrap: wrap; }
  .vp-select { width: 100%; }
  .vp-table thead th:nth-child(1), .vp-table td:nth-child(1) { display: none; }
  .vp-tabs { overflow-x: auto; }
}
</style>
