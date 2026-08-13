<template>
  <div class="vi-wrap">

    <!-- ── Tabs de navegación ─────────────────────────────── -->
    <div class="vi-tabs">
      <RouterLink to="/pos/consultas/ventas"         class="vi-tab">Consulta Ventas</RouterLink>
      <RouterLink to="/pos/consultas/ventas-producto" class="vi-tab">Venta x Producto</RouterLink>
      <RouterLink to="/pos/consultas/ventas-insumo"   class="vi-tab">Venta x Insumo</RouterLink>
    </div>

    <!-- ── Filtros (colapsable) ──────────────────────────── -->
    <div class="vi-filters card">
      <div class="vi-filters-head" @click="filtrosVisible = !filtrosVisible">
        <span class="vi-filters-label">
          <i class="bi bi-funnel-fill me-1"></i>
          <span>Filtros</span>
          <span v-if="!filtrosVisible && lista.length" class="vi-filters-hint">
            {{ fmtFecha(filtro.desde) }} — {{ fmtFecha(filtro.hasta) }}
            <template v-if="filtro.catId"> · {{ categorias.find(c=>c.id===filtro.catId)?.name }}</template>
          </span>
        </span>
        <i :class="filtrosVisible ? 'bi bi-chevron-up' : 'bi bi-chevron-down'" class="vi-chevron"></i>
      </div>

      <div v-show="filtrosVisible" class="vi-filters-body">
        <div class="vi-filter-row">

          <!-- Tipo -->
          <div class="vi-filter-group">
            <label class="vi-label">Tipo</label>
            <div class="vi-radios">
              <label v-for="op in tipoOpts" :key="op.value" class="vi-radio">
                <input type="radio" v-model="filtro.tipo" :value="op.value" @change="buscar" />
                {{ op.label }}
              </label>
            </div>
          </div>

          <!-- Fechas -->
          <div class="vi-filter-group">
            <label class="vi-label">Desde / Hasta</label>
            <div class="vi-fechas-row">
              <CustomDatePicker v-model="filtro.desde" @update:modelValue="buscar" style="width:140px" />
              <span class="vi-fecha-sep">—</span>
              <CustomDatePicker v-model="filtro.hasta" @update:modelValue="buscar" style="width:140px" />
            </div>
          </div>

          <!-- Categoría del plato -->
          <div class="vi-filter-group">
            <label class="vi-label">Categoría Plato</label>
            <select class="vi-select" v-model="filtro.catId" @change="buscar">
              <option :value="null">Todas</option>
              <option v-for="c in categorias" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>

          <!-- Acciones -->
          <div class="vi-btns-group">
            <button class="btn btn-outline-secondary vi-btn-hoy" @click="irHoy">
              <i class="bi bi-calendar-check"></i><span>Hoy</span>
            </button>
            <button class="btn btn-primary vi-btn-buscar" @click="buscar" :disabled="cargando">
              <i class="bi bi-search"></i><span>Buscar</span>
            </button>
            <button class="btn btn-outline-primary vi-btn-refresh" @click="buscar" :disabled="cargando" title="Actualizar">
              <i class="bi bi-arrow-clockwise" :class="{ spin: cargando }"></i>
            </button>
            <button class="btn btn-dark vi-btn-print" @click="abrirImprimir" :disabled="!lista.length" title="Imprimir resumen">
              <i class="bi bi-printer-fill"></i>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── KPI chips ─────────────────────────────────────── -->
    <div v-if="!cargando && lista.length" class="vi-kpi-bar">
      <span class="vi-kpi-chip">
        <span class="vi-kpi-lbl">{{ lista.length }} registros</span>
      </span>
      <span class="vi-kpi-chip vi-kpi--blue">
        <span class="vi-kpi-lbl">Insumos distintos</span>
        <strong>{{ insumosDistintos }}</strong>
      </span>
    </div>

    <!-- ── Tabla ─────────────────────────────────────────── -->
    <div class="vi-table-wrap card">

      <!-- Loading -->
      <div v-if="cargando" class="vi-placeholder">
        <div class="spinner-border text-primary" style="width:2rem;height:2rem;"></div>
      </div>

      <!-- Sin datos -->
      <div v-else-if="!lista.length" class="vi-placeholder text-muted">
        <i class="bi bi-box-seam fs-2"></i>
        <p class="mt-2 mb-0">Sin resultados. Ajusta los filtros y busca.</p>
      </div>

      <!-- Datos -->
      <template v-else>
        <!-- Buscador interno -->
        <div class="vi-search-bar">
          <i class="bi bi-search vi-search-ico"></i>
          <input v-model.trim="busqueda" class="vi-search-inp" placeholder="Filtrar por insumo o plato..." />
          <button v-if="busqueda" class="vi-search-clear" @click="busqueda=''">
            <i class="bi bi-x-circle"></i>
          </button>
        </div>

        <div class="vi-table-scroll">
          <table class="vi-table">
            <thead>
              <tr>
                <th @click="sortBy('categoria_plato')" class="sortable">
                  Cat. Plato <i :class="sortIcon('categoria_plato')"></i>
                </th>
                <th @click="sortBy('plato')" class="sortable">
                  Plato <i :class="sortIcon('plato')"></i>
                </th>
                <th @click="sortBy('insumo')" class="sortable">
                  Insumo <i :class="sortIcon('insumo')"></i>
                </th>
                <th>Unidad</th>
                <th class="ta-r" @click="sortBy('cantidad')" style="cursor:pointer">
                  Cant. <i :class="sortIcon('cantidad')"></i>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in listaFiltrada" :key="i" class="vi-row">
                <td>
                  <span class="vi-cat-badge">{{ row.categoria_plato }}</span>
                </td>
                <td class="vi-plato">{{ row.plato }}</td>
                <td class="vi-insumo">{{ row.insumo }}</td>
                <td class="vi-unidad">{{ row.unidad }}</td>
                <td class="ta-r vi-cant">{{ fmtNum(row.cantidad) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </div>

    <!-- ── Componente impresión ──────────────────────────── -->
    <ImprimirResumenProductos
      v-if="showImprimir"
      modo="insumo"
      :datos="lista"
      :filtros="filtroImprimir"
      @close="showImprimir = false"
    />

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/apis.js'
import { useCompanyStore } from '@/stores/companyStore'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'
import ImprimirResumenProductos from '@/components/billing/ImprimirResumenProductos.vue'

const companyStore = useCompanyStore()
const selectedCid  = computed(() => companyStore.selectedCompany?.id || undefined)

const fmtNum = n => Number(n || 0).toLocaleString('es-CO', { maximumFractionDigits: 4 })

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

const filtro         = ref({ tipo:'ambos', desde:localDate(), hasta:localDate(), catId:null })
const filtrosVisible = ref(true)
const cargando       = ref(false)
const lista          = ref([])
const categorias     = ref([])
const busqueda       = ref('')
const showImprimir   = ref(false)

// Sort
const sortCol = ref('plato')
const sortDir = ref(1)

function sortBy(col) {
  if (sortCol.value === col) sortDir.value *= -1
  else { sortCol.value = col; sortDir.value = col === 'cantidad' ? -1 : 1 }
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
      r.insumo?.toLowerCase().includes(q) ||
      r.plato?.toLowerCase().includes(q)  ||
      r.categoria_plato?.toLowerCase().includes(q)
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

const insumosDistintos = computed(() => {
  return new Set(lista.value.map(r => r.insumo)).size
})

const filtroImprimir = computed(() => ({
  desde:          filtro.value.desde,
  hasta:          filtro.value.hasta,
  tipo:           filtro.value.tipo,
  categoriaNombre: filtro.value.catId
    ? (categorias.value.find(c => c.id === filtro.value.catId)?.name || '')
    : '',
}))

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
    const { data } = await api.get('/api/pos-consultas/ventas-insumo', {
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
  filtro.value = { tipo:'ambos', desde:hoy, hasta:hoy, catId:null }
  buscar()
}

function abrirImprimir() { showImprimir.value = true }

onMounted(async () => {
  await cargarCategorias()
  await buscar()
})
</script>

<style scoped>
/* ── Layout ─────────────────────────────────────────────── */
.vi-wrap {
  display: flex; flex-direction: column;
  height: 100%; gap: 10px;
}
.card { border-radius: 10px; border: 1px solid #e2e8f0; background: #fff; }

/* ── Tabs ───────────────────────────────────────────────── */
.vi-tabs {
  display: flex; gap: 4px; flex-shrink: 0;
  border-bottom: 2px solid #e2e8f0;
}
.vi-tab {
  padding: 8px 16px; font-size: 13px; font-weight: 600;
  color: #64748b; text-decoration: none; border-radius: 8px 8px 0 0;
  border: 1px solid transparent; border-bottom: none; transition: all .15s; white-space: nowrap;
}
.vi-tab:hover { color: #1e40af; background: #f1f5f9; }
.vi-tab.router-link-active {
  color: #1e40af; background: #fff;
  border-color: #e2e8f0; border-bottom-color: #fff; margin-bottom: -2px;
}

/* ── Filtros ─────────────────────────────────────────────── */
.vi-filters { flex-shrink: 0; }
.vi-filters-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 16px; cursor: pointer; user-select: none;
}
.vi-filters-head:hover { background: #f8fafc; border-radius: 10px; }
.vi-filters-label { display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 700; color: #1e293b; }
.vi-filters-hint  { font-size: 11px; font-weight: 400; color: #64748b; margin-left: 6px; }
.vi-chevron { font-size: 13px; color: #64748b; }
.vi-filters-body { padding: 0 16px 12px; }
.vi-filter-row { display: flex; align-items: flex-end; gap: 12px; flex-wrap: wrap; }
.vi-filter-group { display: flex; flex-direction: column; gap: 4px; }
.vi-label { font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: .4px; }
.vi-radios { display: flex; gap: 12px; }
.vi-radio  { display: flex; align-items: center; gap: 4px; font-size: 14px; cursor: pointer; }
.vi-fechas-row { display: flex; align-items: center; gap: 6px; }
.vi-fecha-sep  { color: #94a3b8; font-size: 13px; flex-shrink: 0; }
.vi-select {
  height: 34px; border: 1px solid #cbd5e1; border-radius: 6px;
  padding: 0 10px; font-size: 13px; background: #f8fafc; outline: none; min-width: 150px;
}
.vi-select:focus { border-color: #3b82f6; background: #fff; }
.vi-btns-group { display: flex; gap: 6px; align-items: flex-end; }
.vi-btn-hoy, .vi-btn-buscar, .vi-btn-refresh, .vi-btn-print {
  height: 34px; display: flex; align-items: center; gap: 6px; white-space: nowrap;
}
.vi-btn-hoy, .vi-btn-buscar { padding: 0 14px; }
.vi-btn-refresh, .vi-btn-print { padding: 0 10px; }

/* ── KPI ─────────────────────────────────────────────────── */
.vi-kpi-bar { display: flex; flex-wrap: wrap; gap: 8px; flex-shrink: 0; padding: 4px; }
.vi-kpi-chip {
  display: flex; align-items: center; gap: 5px;
  background: #f1f5f9; border-radius: 8px; padding: 4px 12px;
  font-size: 13px; border-left: 3px solid #cbd5e1;
}
.vi-kpi--blue { background:#eff6ff; color:#1e40af; border-left-color:#3b82f6; }
.vi-kpi-lbl { font-size:10px; font-weight:600; text-transform:uppercase; letter-spacing:.3px; opacity:.7; margin-right:3px; }

/* ── Tabla ──────────────────────────────────────────────── */
.vi-table-wrap { flex: 1; display: flex; flex-direction: column; min-height: 0; overflow: hidden; }
.vi-placeholder {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center; color: #94a3b8; padding: 32px;
}

.vi-search-bar {
  display: flex; align-items: center; gap: 6px;
  padding: 10px 14px; border-bottom: 1px solid #f1f5f9; flex-shrink: 0;
}
.vi-search-ico { color: #94a3b8; font-size: 14px; }
.vi-search-inp { flex: 1; border: none; outline: none; font-size: 13px; background: transparent; color: #1e293b; }
.vi-search-clear { background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 14px; }

.vi-table-scroll { flex: 1; overflow-y: auto; }
.vi-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.vi-table thead th {
  position: sticky; top: 0; background: #f8fafc;
  padding: 8px 12px; font-size: 11px; font-weight: 700;
  text-transform: uppercase; color: #64748b;
  border-bottom: 1px solid #e2e8f0; letter-spacing: .3px; z-index: 1;
}
.vi-table thead th.sortable { cursor: pointer; user-select: none; }
.vi-table thead th.sortable:hover { color: #1e40af; }
.vi-table td { padding: 9px 12px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.vi-row:hover td { background: #f8fafc; }
.ta-r { text-align: right; }

.vi-cat-badge {
  display: inline-block; font-size: 11px; font-weight: 600;
  background: #f0fdf4; color: #166534; border-radius: 12px; padding: 2px 8px; white-space: nowrap;
}
.vi-plato  { font-weight: 600; color: #1e293b; }
.vi-insumo { color: #334155; }
.vi-unidad { color: #64748b; font-size: 12px; }
.vi-cant   { font-weight: 700; color: #1e40af; }

@keyframes spin { to { transform: rotate(360deg); } }
.spin { display: inline-block; animation: spin .7s linear infinite; }

/* ── RESPONSIVE TABLET ──────────────────────────────────── */
@media (max-width: 768px) {
  .vi-wrap { height: auto; min-height: 100%; }
  .vi-table-wrap { flex: none; overflow: visible; }
  .vi-table-scroll { overflow: visible; height: auto; }
  .vi-btn-buscar span, .vi-btn-hoy span { display: none; }
  .vi-btn-buscar, .vi-btn-hoy { padding: 0 10px; }
  .vi-tab { padding: 6px 10px; font-size: 12px; }
}

/* ── RESPONSIVE MÓVIL PEQUEÑO ───────────────────────────── */
@media (max-width: 576px) {
  .vi-filters-body { padding: 0 12px 10px; }
  .vi-filter-row { flex-direction: column; align-items: stretch; }
  .vi-btns-group { flex-direction: row; }
  .vi-btn-buscar { flex: 1; justify-content: center; }
  .vi-btn-hoy    { flex: 1; justify-content: center; }
  .vi-btn-buscar span, .vi-btn-hoy span { display: inline; }
  .vi-radios { flex-wrap: wrap; }
  .vi-select { width: 100%; }
  .vi-table thead th:nth-child(1), .vi-table td:nth-child(1) { display: none; }
  .vi-table thead th:nth-child(2), .vi-table td:nth-child(2) { display: none; }
  .vi-tabs { overflow-x: auto; }
}
</style>
