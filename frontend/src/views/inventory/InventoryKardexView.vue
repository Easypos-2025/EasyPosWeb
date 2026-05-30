<template>
  <div class="kx-wrap">

    <!-- ══ SELECTOR DE PRODUCTO ═══════════════════════════════════════════════ -->
    <div class="kx-sel-bar">
      <!-- Categoría -->
      <div class="kx-field">
        <label class="kx-lbl">Categoría</label>
        <select v-model="selCat" @change="onCatChange" class="kx-inp">
          <option value="">Todas</option>
          <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </div>

      <!-- Buscar por nombre o código -->
      <div class="kx-field kx-field-grow">
        <label class="kx-lbl"><i class="bi bi-upc-scan"></i> Buscar insumo o código</label>
        <input v-model="searchQ" @input="filterItems" class="kx-inp"
               placeholder="Nombre o código de barras..." />
      </div>

      <!-- Select de insumo -->
      <div class="kx-field kx-field-grow">
        <label class="kx-lbl">Insumo</label>
        <select v-model="selItem" @change="onItemSelect" class="kx-inp"
                :disabled="!filteredItems.length">
          <option value="">— Seleccione —</option>
          <option v-for="it in filteredItems" :key="it.id_item" :value="it.id_item">
            {{ it.description }}{{ it.code ? ' [' + it.code + ']' : '' }}
          </option>
        </select>
      </div>

      <!-- Fecha desde: bloqueada para no-SYSADMIN -->
      <div class="kx-field">
        <label class="kx-lbl">
          Desde (últ. inventario)
          <i v-if="!isSysAdmin" class="bi bi-lock-fill kx-lock-ico" title="Solo SYSADMIN puede cambiar esta fecha"></i>
        </label>
        <CustomDatePicker v-if="isSysAdmin" v-model="desde" @update:modelValue="reloadKardex" />
        <div v-else class="kx-inp kx-date-ro">
          {{ desde || '—' }}
        </div>
      </div>
      <div class="kx-field">
        <label class="kx-lbl">Hasta</label>
        <CustomDatePicker v-model="hasta" @update:modelValue="reloadKardex" />
      </div>
    </div>

    <!-- Info del insumo seleccionado -->
    <div v-if="kardex" class="kx-item-hdr">
      <div class="kx-item-left">
        <div class="kx-item-title">
          <i class="bi bi-box-seam"></i>
          <strong>{{ kardex.item.description }}</strong>
          <span class="kx-badge kx-cat">{{ kardex.item.category_name || 'Sin categoría' }}</span>
          <span class="kx-badge kx-unit">{{ kardex.item.unit_name }}</span>
        </div>
        <div class="kx-item-codes">
          <span v-if="kardex.item.id" class="kx-code-chip"
                @click="copyText(kardex.item.id, 'Código')"
                title="Código interno — clic para copiar">
            <i class="bi bi-hash"></i>{{ kardex.item.id }}
            <i class="bi bi-clipboard kx-clip-ico"></i>
          </span>
          <span v-if="kardex.item.code" class="kx-code-chip"
                @click="copyText(kardex.item.code, 'Código de barras')"
                title="Código de barras — clic para copiar">
            <i class="bi bi-upc-scan"></i>{{ kardex.item.code }}
            <i class="bi bi-clipboard kx-clip-ico"></i>
          </span>
        </div>
      </div>
      <div class="kx-item-right">
        <div class="kx-range-lbl">
          <i class="bi bi-calendar-range"></i>
          {{ fmtDate(kardex.desde) }} → {{ fmtDate(kardex.hasta) }}
        </div>
        <ExportToolbar
          :data="exportData"
          :columns="exportCols"
          :filename="exportFilename"
          :title="exportTitle"
        />
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="kx-state">
      <i class="bi bi-arrow-repeat spin"></i> Cargando Kardex...
    </div>

    <!-- ══ CONTENIDO PRINCIPAL ════════════════════════════════════════════════ -->
    <div v-else-if="kardex" class="kx-main">

      <!-- ── COLUMNA IZQUIERDA: resumen diario ── -->
      <div class="kx-col-left">
        <div class="kx-panel-hdr">
          <i class="bi bi-table"></i> Resumen diario
          <span class="kx-cnt">{{ kardex.daily.length }} días con movimiento</span>
        </div>

        <div class="kx-tbl-scroll">
          <table class="kx-tbl">
            <thead>
              <tr>
                <th>Fecha</th>
                <th class="tr">Inv.Ini</th>
                <th class="tr kx-col-ent">Entradas</th>
                <th class="tr kx-col-sal">Salidas</th>
                <th class="tr kx-col-ven">Ventas</th>
                <th class="tr">Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="d in kardex.daily" :key="d.fecha"
                  class="kx-row"
                  :class="{
                    'kx-row-start': d.is_start,
                    'kx-row-neg':   d.total < 0,
                    'kx-row-sel':   selectedDate === d.fecha
                  }"
                  @click="toggleDate(d.fecha)">
                <td class="kx-fecha">
                  <span v-if="d.is_start" class="kx-star" title="Inventario inicial">★</span>
                  {{ fmtDate(d.fecha) }}
                </td>
                <td class="tr kx-num-sm td-muted">{{ fmtQ(d.ini) }}</td>
                <td class="tr kx-num" :class="d.entradas > 0 ? 'c-green' : 'td-muted'">
                  {{ d.entradas > 0 ? fmtQ(d.entradas) : '—' }}
                </td>
                <td class="tr kx-num" :class="d.salidas > 0 ? 'c-orange' : 'td-muted'">
                  {{ d.salidas > 0 ? fmtQ(d.salidas) : '—' }}
                </td>
                <td class="tr kx-num" :class="d.ventas > 0 ? 'c-red' : 'td-muted'">
                  {{ d.ventas > 0 ? fmtQ(d.ventas) : '—' }}
                </td>
                <td class="tr kx-total"
                    :class="d.total < 0 ? 'c-red fw-b' : d.total === 0 ? 'td-muted' : 'fw-b'">
                  {{ fmtQ(d.total) }}
                </td>
              </tr>
              <tr v-if="!kardex.daily.length">
                <td colspan="6" class="kx-empty">
                  Sin movimientos en este rango
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ── COLUMNA DERECHA: resumen + detalle ── -->
      <div class="kx-col-right">

        <!-- Tarjetas resumen -->
        <div class="kx-summary">
          <div class="kx-sum-card kx-sum-gray">
            <span class="kx-sum-n">{{ fmtQ(kardex.start.cantidad) }}</span>
            <span class="kx-sum-l">Inventario inicial</span>
            <span class="kx-sum-date">{{ fmtDate(kardex.start.fecha) }}</span>
          </div>
          <div class="kx-sum-card kx-sum-green">
            <span class="kx-sum-n">{{ fmtQ(kardex.totals.entradas) }}</span>
            <span class="kx-sum-l">Total entradas</span>
          </div>
          <div class="kx-sum-card kx-sum-orange">
            <span class="kx-sum-n">{{ fmtQ(kardex.totals.salidas) }}</span>
            <span class="kx-sum-l">Total salidas</span>
          </div>
          <div class="kx-sum-card kx-sum-red">
            <span class="kx-sum-n">{{ fmtQ(kardex.totals.ventas) }}</span>
            <span class="kx-sum-l">Total ventas</span>
          </div>
          <div class="kx-sum-card"
               :class="kardex.totals.stock_calculado < 0 ? 'kx-sum-danger' : 'kx-sum-blue'">
            <span class="kx-sum-n fw-b">{{ fmtQ(kardex.totals.stock_calculado) }}</span>
            <span class="kx-sum-l">Stock calculado</span>
          </div>
        </div>

        <!-- Tabla de movimientos detalle -->
        <div class="kx-panel-hdr mt-12">
          <i class="bi bi-list-ul"></i> Movimientos detalle
          <span v-if="selectedDate" class="kx-date-filter">
            <i class="bi bi-calendar-day"></i> {{ fmtDate(selectedDate) }}
            <button class="kx-clr" @click="selectedDate = null" title="Ver todos">×</button>
          </span>
          <span class="kx-cnt">{{ filteredMovements.length }} registros</span>
        </div>

        <div class="kx-tbl-scroll kx-det-scroll">
          <table class="kx-tbl">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Concepto</th>
                <th class="tr">N°</th>
                <th class="tr">Cantidad</th>
                <th>Obs / Usuario</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(m, i) in filteredMovements" :key="i"
                  :class="movRowCls(m)">
                <td class="kx-fecha sm">{{ fmtDate(m.fecha) }}</td>
                <td>
                  <span :class="movBadgeCls(m)" class="kx-mb">{{ m.concepto }}</span>
                </td>
                <td class="tr sm td-muted">{{ m.numero ? '#' + m.numero : '—' }}</td>
                <td class="tr fw-b" :class="m.tipo === 'entrada' ? 'c-green' : 'c-red'">
                  {{ m.tipo === 'entrada' ? '+' : '−' }}{{ fmtQ(m.cantidad) }}
                </td>
                <td class="sm td-muted kx-obs">{{ m.obs || m.usuario || '—' }}</td>
              </tr>
              <tr v-if="!filteredMovements.length">
                <td colspan="5" class="kx-empty">
                  Sin movimientos{{ selectedDate ? ' para ' + fmtDate(selectedDate) : '' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Estado vacío -->
    <div v-else class="kx-state kx-placeholder">
      <i class="bi bi-journal-text kx-ph-ico"></i>
      <p>Seleccione un insumo para ver su Kardex</p>
      <small class="td-muted">El Kardex muestra el movimiento desde el último inventario físico</small>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'
import ExportToolbar from '@/components/common/ExportToolbar.vue'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'

// ── Rol del usuario ───────────────────────────────────────────────────────────
const _u = JSON.parse(localStorage.getItem('user') || '{}')
const isSysAdmin = _u.role === 'SYSADMIN'

// ── Selección ─────────────────────────────────────────────────────────────────
const allItems     = ref([])   // todos los insumos (activos)
const categories   = ref([])
const selCat       = ref('')
const searchQ      = ref('')
const selItem      = ref('')

const filteredItems = computed(() => {
  const q   = searchQ.value.toLowerCase()
  const cat = selCat.value
  return allItems.value.filter(it => {
    const matchCat  = !cat || String(it.category_id) === String(cat)
    const matchQ    = !q   || it.description.toLowerCase().includes(q)
                            || (it.code || '').toLowerCase().includes(q)
    return matchCat && matchQ
  })
})

function onCatChange()  { searchQ.value = ''; selItem.value = ''; kardex.value = null }
function filterItems()  { selItem.value = ''; kardex.value = null }
function onItemSelect() {
  if (selItem.value) {
    desde.value = ''  // resetear para que backend calcule la fecha del último inventario
    loadKardex()
  }
}

// ── Fechas ────────────────────────────────────────────────────────────────────
const desde = ref('')
const hasta  = ref(new Date().toISOString().slice(0, 10))

function reloadKardex() { if (selItem.value) loadKardex() }

// ── Kardex data ───────────────────────────────────────────────────────────────
const kardex      = ref(null)
const loading     = ref(false)
const selectedDate = ref(null)

const filteredMovements = computed(() => {
  if (!kardex.value) return []
  if (!selectedDate.value) return kardex.value.movements
  return kardex.value.movements.filter(m => m.fecha === selectedDate.value)
})

function toggleDate(d) {
  selectedDate.value = selectedDate.value === d ? null : d
}

// ── Helpers ───────────────────────────────────────────────────────────────────
const fmtQ    = v => Number(v || 0).toLocaleString('es-CO', { maximumFractionDigits: 4 })
const fmtDate = v => v ? String(v).slice(0, 10) : '—'

function movRowCls(m) {
  if (m.tipo === 'entrada') return 'kx-row-ent'
  if (m.tipo === 'venta')   return 'kx-row-ven'
  return 'kx-row-sal'
}
function movBadgeCls(m) {
  if (m.tipo === 'entrada') return 'kx-mb-green'
  if (m.tipo === 'venta')   return 'kx-mb-red'
  return 'kx-mb-orange'
}

// ── Export ────────────────────────────────────────────────────────────────────
const exportCols = computed(() => [
  { key: 'fecha',       label: 'Fecha' },
  { key: 'concepto',    label: 'Concepto' },
  { key: 'numero',      label: 'N°',      fmt: v => v ? '#' + v : '—' },
  { key: 'cantidad',    label: 'Cantidad', fmt: (v, row) => (row.tipo === 'entrada' ? '+' : '-') + fmtQ(v) },
  { key: 'obs_usuario', label: 'Obs/Usuario' },
])
const exportData = computed(() => {
  if (!kardex.value) return []
  return kardex.value.movements.map(m => ({
    fecha:       m.fecha,
    concepto:    m.concepto,
    numero:      m.numero,
    tipo:        m.tipo,
    cantidad:    m.cantidad,
    obs_usuario: m.obs || m.usuario || '',
  }))
})
const exportFilename = computed(() =>
  kardex.value ? `kardex-${kardex.value.item.description.replace(/\s+/g, '_')}` : 'kardex'
)
const exportTitle = computed(() =>
  kardex.value
    ? `Kardex: ${kardex.value.item.description} | ${kardex.value.desde} → ${kardex.value.hasta}`
    : 'Kardex'
)

// ── Copiar al portapapeles ────────────────────────────────────────────────────
function copyText(val, label) {
  if (!val) return
  navigator.clipboard.writeText(String(val))
    .then(() => showToast(`${label} copiado`, 'success'))
    .catch(() => showToast('No se pudo copiar', 'error'))
}

// ── Carga de datos ────────────────────────────────────────────────────────────
async function loadItems() {
  try {
    const data = (await api.get('/api/inventory/kardex/items')).data
    allItems.value = data
    // Extraer categorías únicas
    const seen = new Set()
    categories.value = []
    for (const it of data) {
      if (it.category_id && !seen.has(it.category_id)) {
        seen.add(it.category_id)
        categories.value.push({ id: it.category_id, name: it.category_name })
      }
    }
    categories.value.sort((a, b) => a.name.localeCompare(b.name, 'es'))
  } catch { allItems.value = [] }
}

async function loadKardex() {
  if (!selItem.value) return
  loading.value = true
  selectedDate.value = null
  try {
    const params = { hasta: hasta.value }
    if (desde.value) params.desde = desde.value
    const res = (await api.get(`/api/inventory/kardex/${selItem.value}`, { params })).data
    kardex.value = res
    // Siempre sincronizar 'desde' con la fecha del último inventario del insumo
    if (!desde.value || !params.desde) desde.value = res.desde
  } catch (e) {
    showToast('Error al cargar el Kardex', 'error')
    kardex.value = null
  } finally { loading.value = false }
}

onMounted(loadItems)
</script>

<style scoped>
.kx-wrap { padding: 14px; }

/* ── Selector de producto ── */
.kx-sel-bar {
  display: flex; gap: 10px; flex-wrap: wrap; align-items: flex-end;
  background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 10px;
  padding: 12px 14px; margin-bottom: 12px;
}
.kx-field { display: flex; flex-direction: column; gap: 3px; }
.kx-field-grow { flex: 1; min-width: 180px; }
.kx-lbl { font-size: .76rem; font-weight: 600; color: #374151; }
.kx-inp {
  padding: 8px 10px; border: 1px solid #d1d5db; border-radius: 7px;
  font-size: .86rem; background: #fff; width: 100%; box-sizing: border-box;
}
.kx-inp:focus { outline: none; border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37,99,235,.12); }
.kx-date-ro {
  background: #f3f4f6; color: #374151; cursor: not-allowed;
  display: flex; align-items: center; gap: 5px; min-height: 36px;
}
.kx-lock-ico { color: #9ca3af; font-size: .72rem; margin-left: 3px; }

/* ── Info del insumo ── */
.kx-item-hdr {
  display: flex; justify-content: space-between; align-items: flex-start;
  background: #1d4ed8; color: #fff; border-radius: 10px;
  padding: 10px 16px; margin-bottom: 12px; flex-wrap: wrap; gap: 10px;
}
.kx-item-left  { display: flex; flex-direction: column; gap: 6px; }
.kx-item-right { display: flex; flex-direction: column; align-items: flex-end; gap: 8px; }
.kx-item-title { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; font-size: .9rem; }
.kx-badge { padding: 2px 8px; border-radius: 10px; font-size: .74rem; font-weight: 600; }
.kx-cat  { background: rgba(255,255,255,.2); }
.kx-unit { background: rgba(255,255,255,.15); }
.kx-range-lbl { font-size: .8rem; opacity: .85; display: flex; align-items: center; gap: 5px; }

/* Chips copiables de código/barcode */
.kx-item-codes { display: flex; gap: 8px; flex-wrap: wrap; }
.kx-code-chip {
  display: inline-flex; align-items: center; gap: 4px;
  background: rgba(255,255,255,.15); color: #fff;
  padding: 3px 9px; border-radius: 20px; font-size: .75rem; font-weight: 600;
  cursor: pointer; transition: background .15s; user-select: none;
}
.kx-code-chip:hover { background: rgba(255,255,255,.28); }
.kx-clip-ico { font-size: .68rem; opacity: .75; margin-left: 2px; }

/* ── Layout principal ── */
.kx-main {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 14px;
  align-items: start;
}

/* ── Panel headers ── */
.kx-panel-hdr {
  display: flex; align-items: center; gap: 8px;
  font-size: .8rem; font-weight: 700; color: #374151;
  padding: 7px 10px; background: #f3f4f6; border-radius: 8px 8px 0 0;
  border: 1px solid #e9ecef; border-bottom: none; flex-wrap: wrap;
}
.kx-cnt { margin-left: auto; font-size: .73rem; color: #6b7280; font-weight: 400; }
.mt-12  { margin-top: 12px; }

/* ── Tablas ── */
.kx-tbl-scroll {
  border: 1px solid #e9ecef; border-radius: 0 0 8px 8px;
  overflow: auto; max-height: 480px;
}
.kx-det-scroll { max-height: 320px; }
.kx-tbl { width: 100%; border-collapse: collapse; font-size: .82rem; }
.kx-tbl th {
  background: #f8f9fa; padding: 6px 8px;
  text-align: left; font-weight: 600; font-size: .74rem;
  border-bottom: 2px solid #dee2e6; white-space: nowrap;
  position: sticky; top: 0; z-index: 1;
}
.kx-tbl td { padding: 6px 8px; border-bottom: 1px solid #f0f0f0; }
.kx-row { cursor: pointer; transition: background .1s; }
.kx-row:hover { background: #f9fafb; }
.kx-row-sel   { background: #dbeafe !important; }
.kx-row-start { background: #fefce8; border-left: 3px solid #eab308; }
.kx-row-neg   { }
.kx-fecha  { white-space: nowrap; font-size: .79rem; }
.kx-star   { color: #eab308; margin-right: 2px; }
.kx-num    { font-size: .84rem; }
.kx-num-sm { font-size: .79rem; }
.kx-total  { font-size: .86rem; min-width: 70px; }
.kx-obs    { max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.kx-col-ent th, .kx-col-ent td { color: #166534 !important; }
.kx-col-sal th, .kx-col-sal td { color: #9a3412 !important; }
.kx-col-ven th, .kx-col-ven td { color: #991b1b !important; }

/* Filas de detalle */
.kx-row-ent { background: #f0fdf4 !important; }
.kx-row-sal { background: #fff7ed !important; }
.kx-row-ven { background: #fff5f5 !important; }

/* ── Badges de concepto ── */
.kx-mb { padding: 2px 7px; border-radius: 20px; font-size: .72rem; font-weight: 700; white-space: nowrap; }
.kx-mb-green  { background: #dcfce7; color: #166534; }
.kx-mb-orange { background: #ffedd5; color: #9a3412; }
.kx-mb-red    { background: #fee2e2; color: #991b1b; }

/* ── Resumen ── */
.kx-summary {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: 8px; margin-bottom: 0;
}
.kx-sum-card {
  border-radius: 10px; padding: 12px 14px;
  display: flex; flex-direction: column; gap: 2px;
  border: 1px solid transparent; text-align: center;
}
.kx-sum-n    { font-size: 1.3rem; font-weight: 700; line-height: 1; }
.kx-sum-l    { font-size: .72rem; font-weight: 600; margin-top: 2px; }
.kx-sum-date { font-size: .68rem; margin-top: 2px; }
.kx-sum-gray   { background: #f9fafb; border-color: #e5e7eb; color: #374151; }
.kx-sum-green  { background: #f0fdf4; border-color: #bbf7d0; }
.kx-sum-green  .kx-sum-n { color: #166534; }
.kx-sum-orange { background: #fff7ed; border-color: #fed7aa; }
.kx-sum-orange .kx-sum-n { color: #9a3412; }
.kx-sum-red    { background: #fff5f5; border-color: #fecaca; }
.kx-sum-red    .kx-sum-n { color: #991b1b; }
.kx-sum-blue   { background: #eff6ff; border-color: #bfdbfe; }
.kx-sum-blue   .kx-sum-n { color: #1d4ed8; }
.kx-sum-danger { background: #fef2f2; border-color: #fca5a5; }
.kx-sum-danger .kx-sum-n { color: #dc2626; }

/* ── Filtro de fecha en detalle ── */
.kx-date-filter {
  display: inline-flex; align-items: center; gap: 4px;
  background: #dbeafe; color: #1d4ed8; padding: 2px 8px; border-radius: 10px;
  font-size: .74rem; font-weight: 600;
}
.kx-clr {
  background: none; border: none; cursor: pointer;
  color: #1d4ed8; font-size: .9rem; padding: 0 2px; line-height: 1;
}

/* ── Estados ── */
.kx-state  { text-align: center; padding: 50px; color: #6b7280; }
.kx-placeholder { padding: 60px 20px; }
.kx-ph-ico { font-size: 3rem; color: #d1d5db; display: block; margin-bottom: 12px; }
.kx-empty  { text-align: center; padding: 24px; color: #9ca3af; font-size: .86rem; }
.spin { animation: spin 1s linear infinite; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Utilidades ── */
.tr      { text-align: right; }
.fw-b    { font-weight: 700; }
.td-muted{ color: #6b7280; }
.sm      { font-size: .78rem; }
.c-green  { color: #166534; }
.c-orange { color: #9a3412; }
.c-red    { color: #dc2626; }

/* ── Responsive ── */
@media (max-width: 960px) {
  .kx-main { grid-template-columns: 1fr; }
  .kx-tbl-scroll  { max-height: 340px; }
  .kx-det-scroll  { max-height: 280px; }
}
@media (max-width: 768px) {
  .kx-sel-bar { padding: 10px; gap: 8px; }
  .kx-field-grow { min-width: 140px; }
  .kx-summary { grid-template-columns: repeat(2, 1fr); }
  .kx-item-hdr { flex-direction: column; }
  .kx-item-right { align-items: flex-start; }
}
@media (max-width: 576px) {
  .kx-wrap    { padding: 8px; }
  .kx-sel-bar { flex-direction: column; }
  .kx-field, .kx-field-grow { width: 100%; }
  .kx-summary { grid-template-columns: repeat(2, 1fr); gap: 6px; }
  .kx-sum-card { padding: 9px 10px; }
  .kx-sum-n   { font-size: 1.1rem; }
  .kx-tbl-scroll  { max-height: 260px; }
  .kx-det-scroll  { max-height: 220px; }
  .kx-item-codes { gap: 6px; }
  .kx-code-chip   { font-size: .72rem; padding: 2px 7px; }
}
</style>
