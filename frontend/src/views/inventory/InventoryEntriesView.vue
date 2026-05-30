<template>
  <div class="ie-wrap">

    <!-- KPI Bar -->
    <div class="kpi-bar">
      <div class="kpi-card kpi-green">
        <span class="kpi-n">{{ rows.length }}</span>
        <span class="kpi-l">Registros</span>
      </div>
      <div class="kpi-card kpi-blue">
        <span class="kpi-n">{{ uniqueItems }}</span>
        <span class="kpi-l">Insumos únicos</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-n">{{ groupedByCategory.length }}</span>
        <span class="kpi-l">Categorías</span>
      </div>
      <div class="kpi-card kpi-teal">
        <span class="kpi-n">{{ totalCantidadFmt }}</span>
        <span class="kpi-l">Cantidad total</span>
      </div>
    </div>

    <!-- Filters + Export + Botón -->
    <div class="filters-bar">
      <div class="f-search-wrap">
        <i class="bi bi-search f-ico"></i>
        <input v-model.trim="search" class="f-inp" placeholder="Buscar insumo o código..." />
      </div>
      <ExportToolbar
        :data="exportData"
        :columns="exportCols"
        filename="entradas-inventario"
        title="Entradas de Inventario"
      />
      <button class="btn-nueva" @click="openCreate">
        <i class="bi bi-plus-lg"></i><span class="btn-lbl"> Nueva Entrada</span>
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="state-c">
      <i class="bi bi-arrow-repeat spin"></i> Cargando...
    </div>

    <template v-else>
      <!-- Column headers desktop -->
      <div class="list-hdr">
        <span></span>
        <span class="hdr-main">Insumo</span>
        <span class="hdr-r tr">Cantidad</span>
        <span class="hdr-dat">Fecha · Empleado</span>
        <span class="hdr-act tc">Anular</span>
      </div>

      <!-- Accordion por categoría -->
      <div v-for="group in groupedByCategory" :key="group.name" class="cat-group">
        <div class="cat-hdr" :class="{ 'cat-hdr-open': openCat === group.name }" @click="toggleCat(group.name)">
          <i class="bi bi-tag-fill cat-ico"></i>
          <span class="cat-hdr-name">{{ group.name }}</span>
          <span class="cat-hdr-cnt">{{ group.items.length }} registro{{ group.items.length !== 1 ? 's' : '' }}</span>
          <i class="bi bi-chevron-down cat-chevron" :class="{ 'cat-chevron-open': openCat === group.name }"></i>
        </div>
        <div v-show="openCat === group.name" class="cards-list">
          <div v-for="r in group.items" :key="r.id" class="sc">
            <div class="sc-status">
              <span class="sb b-entry"><i class="bi bi-arrow-up-circle-fill"></i> Entrada</span>
            </div>
            <div class="sc-main">
              <div class="sc-name">
                {{ r.item_name }}
                <span v-if="r.code" class="sc-code">{{ r.code }}</span>
              </div>
              <div class="sc-meta">
                <span>{{ fmtDate(r.fecha) }}</span>
                <span v-if="r.cod_empleado" class="sep">·</span>
                <span class="td-muted">{{ r.cod_empleado }}</span>
              </div>
              <div v-if="r.observacion" class="sc-obs">{{ r.observacion }}</div>
            </div>
            <div class="sc-qty">
              <span class="fw-b c-green">+{{ fmt(r.cantidad) }}</span>
              <span class="sc-unit">{{ r.unit_name }}</span>
            </div>
            <div class="sc-act">
              <button class="btn-del-row" @click.stop="remove(r)" title="Anular entrada">
                <i class="bi bi-x-lg"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
      <div v-if="!filteredRows.length" class="empty-c">Sin registros de entradas</div>
    </template>

    <!-- Modal nueva entrada -->
    <div v-if="showModal" class="modal-bg" @click.self="showModal=false">
      <div class="iv-modal">
        <h6 class="modal-title"><i class="bi bi-arrow-up-circle me-1 c-green"></i> Nueva Entrada de Inventario</h6>
        <div class="form-group">
          <label>Insumo</label>
          <select v-model="form.id_item" class="form-control">
            <option value="">— Seleccionar —</option>
            <option v-for="s in supplyItems" :key="s.id_item" :value="s.id_item">
              {{ s.description }} — Stock: {{ fmt(s.stock_qty) }} {{ s.unit_name }}
            </option>
          </select>
        </div>
        <div class="form-row-2">
          <div class="form-group">
            <label>Fecha</label>
            <CustomDatePicker v-model="form.fecha" />
          </div>
          <div class="form-group">
            <label>Cantidad a ingresar</label>
            <input type="number" v-model.number="form.cantidad" min="0.0001" step="0.0001" class="form-control" />
          </div>
        </div>
        <div class="form-group">
          <label>Observación / Motivo</label>
          <input type="text" v-model="form.observacion" class="form-control" placeholder="Compra, devolución, ajuste…" />
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="showModal=false">Cancelar</button>
          <button class="btn-confirm" :disabled="saving || !form.id_item || form.cantidad <= 0" @click="save">
            {{ saving ? 'Guardando…' : 'Registrar entrada' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import api from '@/services/apis'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'
import ExportToolbar from '@/components/common/ExportToolbar.vue'
import { showToast } from '@/utils/toast'

const rows        = ref([])
const supplyItems = ref([])
const loading     = ref(true)
const showModal   = ref(false)
const saving      = ref(false)
const search      = ref('')
const openCat     = ref(null)

const today = () => new Date().toISOString().slice(0, 10)
const form  = ref({ id_item: '', fecha: today(), cantidad: 0, observacion: '' })

const fmt     = v => Number(v || 0).toLocaleString('es-CO', { maximumFractionDigits: 4 })
const fmtDate = v => {
  if (!v) return '—'
  const s = String(v).slice(0, 10)
  const [y, m, d] = s.split('-')
  return `${d}-${m}-${y}`
}

function toggleCat(name) { openCat.value = openCat.value === name ? null : name }

// ── Datos filtrados ──────────────────────────────────────────────────────────
const filteredRows = computed(() => {
  if (!search.value) return rows.value
  const q = search.value.toLowerCase()
  return rows.value.filter(r =>
    r.item_name.toLowerCase().includes(q) || (r.code || '').toLowerCase().includes(q)
  )
})

// ── Agrupado por categoría, dentro por nombre luego fecha desc ───────────────
const groupedByCategory = computed(() => {
  const nocat = 'Sin categoría'
  const map = {}
  for (const r of filteredRows.value) {
    const key = r.category_name || nocat
    if (!map[key]) map[key] = { name: key, items: [] }
    map[key].items.push(r)
  }
  const groups = Object.values(map).sort((a, b) =>
    a.name === nocat ? 1 : b.name === nocat ? -1 : a.name.localeCompare(b.name, 'es')
  )
  groups.forEach(g =>
    g.items.sort((a, b) =>
      a.item_name.localeCompare(b.item_name, 'es') || String(b.fecha).localeCompare(String(a.fecha))
    )
  )
  return groups
})

// ── KPI ──────────────────────────────────────────────────────────────────────
const uniqueItems     = computed(() => new Set(rows.value.map(r => r.id_item)).size)
const totalCantidadFmt = computed(() => fmt(rows.value.reduce((s, r) => s + Number(r.cantidad || 0), 0)))

// ── Export ───────────────────────────────────────────────────────────────────
const exportData = computed(() => {
  const result = []
  for (const g of groupedByCategory.value) {
    result.push({ _sectionHeader: true, _title: g.name })
    result.push(...g.items)
  }
  return result
})
const exportCols = [
  { key: 'item_name',    label: 'Insumo' },
  { key: 'code',         label: 'Código' },
  { key: 'fecha',        label: 'Fecha', fmt: v => fmtDate(v) },
  { key: 'cantidad',     label: 'Cantidad', fmt: v => Number(v||0).toFixed(4) },
  { key: 'unit_name',    label: 'Unidad' },
  { key: 'cod_empleado', label: 'Empleado', fmt: v => v || '' },
  { key: 'observacion',  label: 'Observación', fmt: v => v || '' },
]

async function load() {
  loading.value = true
  try {
    rows.value = (await api.get('/api/inventory/entries')).data
    await nextTick()
    if (groupedByCategory.value.length) openCat.value = groupedByCategory.value[0].name
  } finally { loading.value = false }
}

async function loadItems() {
  supplyItems.value = (await api.get('/api/inventory/stock')).data
}

function openCreate() {
  form.value = { id_item: '', fecha: today(), cantidad: 0, observacion: '' }
  showModal.value = true
}

async function save() {
  saving.value = true
  try {
    await api.post('/api/inventory/entries', form.value)
    showToast('Entrada registrada correctamente', 'success')
    showModal.value = false
    await load(); await loadItems()
  } catch (e) {
    showToast(e.response?.data?.detail || 'Error al registrar', 'error')
  } finally { saving.value = false }
}

async function remove(row) {
  if (!confirm(`¿Anular entrada de ${fmt(row.cantidad)} ${row.unit_name} de ${row.item_name}?\nEsto restará del stock.`)) return
  try {
    await api.delete(`/api/inventory/entries/${row.id}`)
    showToast('Entrada anulada', 'success')
    await load(); await loadItems()
  } catch { showToast('Error al anular', 'error') }
}

onMounted(() => { load(); loadItems() })
</script>

<style scoped>
.ie-wrap { padding: 16px; }

/* KPI */
.kpi-bar { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.kpi-card { flex: 1; min-width: 100px; background: #f8f9fa; border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; gap: 2px; border: 1px solid #e9ecef; }
.kpi-green { background: #f0fdf4; border-color: #bbf7d0; }
.kpi-blue  { background: #eff6ff; border-color: #bfdbfe; }
.kpi-teal  { background: #f0fdfa; border-color: #99f6e4; }
.kpi-n { font-size: 1.5rem; font-weight: 700; line-height: 1; }
.kpi-l { font-size: .74rem; color: #6b7280; font-weight: 500; }
.kpi-green .kpi-n { color: #16a34a; }
.kpi-blue .kpi-n  { color: #2563eb; }
.kpi-teal .kpi-n  { color: #0d9488; }

/* Filters */
.filters-bar { display: flex; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; align-items: center; }
.f-search-wrap { position: relative; flex: 1; min-width: 190px; }
.f-ico { position: absolute; left: 9px; top: 50%; transform: translateY(-50%); color: #9ca3af; font-size: .83rem; }
.f-inp { width: 100%; padding: 8px 10px 8px 28px; border: 1px solid #d1d5db; border-radius: 8px; font-size: .86rem; box-sizing: border-box; }
.btn-nueva {
  display: flex; align-items: center; gap: 5px;
  background: #16a34a; color: #fff; border: none;
  padding: 8px 14px; border-radius: 8px; font-size: .85rem; font-weight: 600; cursor: pointer;
  white-space: nowrap; flex-shrink: 0;
}
.btn-nueva:hover { background: #15803d; }

/* Column headers */
.list-hdr {
  display: none; padding: 4px 14px; margin-bottom: 2px;
  font-size: .72rem; font-weight: 700; color: #9ca3af; text-transform: uppercase; letter-spacing: .04em;
}
.hdr-main { flex: 1; }
.hdr-r   { width: 110px; }
.hdr-dat { width: 180px; }
.hdr-act { width: 50px; }

/* Accordion */
.cat-group { margin-bottom: 10px; }
.cat-hdr {
  display: flex; align-items: center; gap: 8px;
  background: #16a34a; color: #fff;
  border-radius: 8px; padding: 9px 14px; cursor: pointer;
  user-select: none; transition: border-radius .15s;
}
.cat-hdr-open { border-radius: 8px 8px 0 0; }
.cat-hdr:hover { background: #15803d; }
.cat-ico { font-size: .8rem; flex-shrink: 0; }
.cat-hdr-name { font-weight: 700; font-size: .85rem; flex: 1; }
.cat-hdr-cnt { font-size: .74rem; background: rgba(255,255,255,.2); padding: 2px 8px; border-radius: 10px; white-space: nowrap; }
.cat-chevron { font-size: .7rem; flex-shrink: 0; transition: transform .2s; margin-left: 4px; }
.cat-chevron-open { transform: rotate(180deg); }

/* Cards */
.cards-list { display: flex; flex-direction: column; border: 1px solid #bbf7d0; border-top: none; border-radius: 0 0 8px 8px; overflow: hidden; }
.sc {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px; background: #fff;
  border-bottom: 1px solid #f0f0f0;
}
.sc:last-child { border-bottom: none; }
.sc:hover { background: #f9fff9; }

/* Status badge */
.sc-status { flex-shrink: 0; }
.sb { padding: 3px 8px; border-radius: 20px; font-size: .73rem; font-weight: 600; white-space: nowrap; display: inline-flex; align-items: center; gap: 3px; }
.b-entry { background: #dcfce7; color: #15803d; }

/* Main */
.sc-main { flex: 1; min-width: 0; }
.sc-name { font-weight: 700; font-size: .88rem; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.sc-code { font-size: .72rem; color: #9ca3af; font-weight: 400; }
.sc-meta { font-size: .77rem; color: #374151; margin-top: 2px; display: flex; align-items: center; gap: 5px; }
.sc-obs  { font-size: .75rem; color: #6b7280; margin-top: 1px; }
.sep { color: #d1d5db; }

/* Qty */
.sc-qty { display: flex; flex-direction: column; align-items: flex-end; flex-shrink: 0; width: 100px; }
.sc-unit { font-size: .73rem; color: #9ca3af; }

/* Action */
.sc-act { flex-shrink: 0; }
.btn-del-row {
  background: none; border: 1px solid #fca5a5; color: #dc2626;
  border-radius: 6px; padding: 5px 8px; cursor: pointer; font-size: .82rem; line-height: 1;
}
.btn-del-row:hover { background: #fef2f2; }

/* Modal */
.modal-bg { position: fixed; inset: 0; background: rgba(0,0,0,.45); z-index: 1100; display: flex; align-items: center; justify-content: center; padding: 16px; }
.iv-modal { background: #fff; border-radius: 12px; padding: 24px; width: 100%; max-width: 480px; box-shadow: 0 20px 60px rgba(0,0,0,.2); }
.modal-title { margin: 0 0 16px; font-weight: 700; font-size: 1rem; }
.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: .82rem; font-weight: 600; margin-bottom: 4px; color: #374151; }
.form-control { width: 100%; padding: 8px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: .88rem; box-sizing: border-box; }
.form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
.btn-cancel  { background: #fff; border: 1px solid #d1d5db; border-radius: 8px; padding: 10px 18px; cursor: pointer; font-size: .87rem; }
.btn-confirm { background: #16a34a; color: #fff; border: none; border-radius: 8px; padding: 10px 20px; cursor: pointer; font-size: .87rem; font-weight: 700; display: flex; align-items: center; gap: 7px; }
.btn-confirm:disabled { opacity: .6; cursor: not-allowed; }

/* Utilities */
.state-c { text-align: center; padding: 40px; color: #6b7280; }
.empty-c { text-align: center; padding: 30px; color: #9ca3af; font-size: .87rem; }
.spin { animation: spin 1s linear infinite; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }
.tr { text-align: right; }
.tc { text-align: center; }
.fw-b { font-weight: 700; }
.td-muted { color: #6b7280; }
.c-green { color: #16a34a; }

/* Desktop */
@media (min-width: 768px) {
  .list-hdr { display: flex; align-items: center; }
  .sc-qty { width: 120px; }
}

/* Tablet */
@media (max-width: 767px) and (min-width: 577px) {
  .sc-qty { width: 90px; }
}

/* Mobile */
@media (max-width: 576px) {
  .ie-wrap { padding: 10px; }
  .kpi-bar { gap: 6px; }
  .kpi-card { padding: 9px 10px; min-width: 70px; }
  .kpi-n { font-size: 1.2rem; }
  .filters-bar { flex-direction: column; align-items: stretch; }
  .f-search-wrap { min-width: unset; }
  .btn-lbl { display: none; }
  .sc { flex-wrap: wrap; gap: 6px; }
  .sc-status { width: 100%; order: -1; }
  .sc-main   { width: 100%; order: 0; }
  .sc-qty    { width: auto; order: 1; }
  .sc-act    { order: 2; margin-left: auto; }
  .form-row-2 { grid-template-columns: 1fr; }
  .iv-modal { padding: 16px; }
}
</style>
