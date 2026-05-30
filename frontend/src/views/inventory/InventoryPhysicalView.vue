<template>
  <div class="ip-wrap">

    <!-- Tabs -->
    <div class="tab-bar">
      <button :class="tab==='take' ? 'tab-on' : 'tab'" @click="tab='take'">
        <i class="bi bi-clipboard-check"></i> Tomar Inventario
      </button>
      <button :class="tab==='history' ? 'tab-on' : 'tab'" @click="tab='history'; loadHistory()">
        <i class="bi bi-calendar3"></i> Historial de Cortes
      </button>
    </div>

    <!-- ══ TAB A: TOMAR INVENTARIO ═══════════════════════════════════════════ -->
    <div v-if="tab==='take'" class="tab-content">

      <!-- Controls top -->
      <div class="take-controls">
        <div class="ctrl-row">
          <div class="ctrl-group">
            <label class="ctrl-lbl">Fecha del corte</label>
            <CustomDatePicker v-model="fecha" />
          </div>
          <div class="ctrl-group flex-1">
            <label class="ctrl-lbl">Observación</label>
            <input type="text" v-model="observacion" class="ctrl-inp" placeholder="Opcional..." />
          </div>
        </div>
        <div class="ctrl-row">
          <div class="ctrl-group flex-1">
            <label class="ctrl-lbl"><i class="bi bi-upc-scan"></i> Buscar / Escanear código</label>
            <input type="text" v-model="barcodeQ" class="ctrl-inp"
                   placeholder="Nombre o código de barras + Enter"
                   @keyup.enter="handleBarcode" ref="barcodeRef" />
          </div>
          <div class="ctrl-group">
            <label class="ctrl-lbl">Filtrar lista</label>
            <input type="text" v-model="listFilter" class="ctrl-inp" placeholder="Filtrar..." />
          </div>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loadingItems" class="state-c">
        <i class="bi bi-arrow-repeat spin"></i> Cargando insumos...
      </div>

      <template v-else>
        <!-- Counter bar -->
        <div class="counter-bar">
          <span class="cnt-info">
            <strong>{{ countedItems }}</strong> de {{ filteredItems.length }} insumos con existencias
          </span>
          <button class="btn-reset" @click="resetAll" title="Poner todo en cero">
            <i class="bi bi-arrow-counterclockwise"></i> Reiniciar todo
          </button>
        </div>

        <!-- Item list -->
        <div class="items-list">
          <div v-for="item in filteredItems" :key="item.id_item"
               class="item-row"
               :class="{ 'item-counted': quantities[item.id_item] > 0 }">
            <div class="item-meta">
              <span class="item-name">{{ item.description }}</span>
              <span class="item-sub">{{ item.code ? item.code + ' — ' : '' }}{{ item.unit_name }}</span>
              <span class="item-sys">Sistema: {{ fmtQty(item.stock_qty) }}</span>
            </div>
            <div class="item-input-wrap">
              <input
                :ref="el => { if (el) inputRefs[item.id_item] = el }"
                type="number"
                inputmode="decimal"
                min="0"
                step="0.001"
                :value="quantities[item.id_item] ?? 0"
                @input="e => setQty(item.id_item, e.target.value)"
                class="qty-inp"
                :class="{ 'qty-filled': quantities[item.id_item] > 0 }"
                placeholder="0" />
              <span class="unit-lbl">{{ item.unit_name }}</span>
            </div>
          </div>
          <div v-if="!filteredItems.length" class="state-c">Sin insumos con control de stock</div>
        </div>

        <!-- Sticky footer -->
        <div class="take-footer">
          <span class="footer-info">{{ countedItems }} items contados</span>
          <button class="btn-cut"
                  :disabled="saving || countedItems === 0"
                  @click="confirmCut">
            <i class="bi bi-check2-circle"></i>
            {{ saving ? 'Generando...' : 'Generar Corte' }}
          </button>
        </div>
      </template>
    </div>

    <!-- ══ TAB B: HISTORIAL ══════════════════════════════════════════════════ -->
    <div v-if="tab==='history'" class="tab-content">
      <div v-if="loadingHistory" class="state-c">
        <i class="bi bi-arrow-repeat spin"></i> Cargando historial...
      </div>
      <template v-else>
        <div v-if="!historyDates.length" class="state-c">Sin inventarios físicos registrados</div>
        <div v-for="h in historyDates" :key="h.fecha" class="hist-card">
          <div class="hist-top" @click="toggleReport(h.fecha)">
            <div class="hist-info">
              <span class="hist-fecha">{{ fmtDate(h.fecha) }}</span>
              <span class="hist-sub">
                {{ h.items_contados }} insumos &nbsp;·&nbsp; {{ h.usuario }} &nbsp;·&nbsp; {{ fmtTime(h.hora_inicio) }}
              </span>
            </div>
            <i :class="reportVisible===h.fecha ? 'bi bi-chevron-up' : 'bi bi-chevron-down'" class="chevron"></i>
          </div>

          <!-- Report panel -->
          <div v-if="reportVisible===h.fecha" class="report-panel">
            <div v-if="loadingReport" class="state-c sm">Cargando reporte...</div>
            <table v-else class="rep-tbl">
              <thead>
                <tr>
                  <th>Insumo</th>
                  <th class="tr">Sistema</th>
                  <th class="tr">Contado</th>
                  <th class="tr">Diferencia</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in reportData" :key="r.id_item"
                    :class="diffCls(r.diferencia)">
                  <td>
                    <strong>{{ r.item_name }}</strong>
                    <small class="td-muted ml"> {{ r.unit_name }}</small>
                  </td>
                  <td class="tr td-muted">{{ fmtQty(r.sistema) }}</td>
                  <td class="tr">{{ fmtQty(r.contado) }}</td>
                  <td class="tr fw-b" :class="r.diferencia < 0 ? 'c-red' : r.diferencia > 0 ? 'c-green' : 'td-muted'">
                    {{ r.diferencia > 0 ? '+' : '' }}{{ fmtQty(r.diferencia) }}
                  </td>
                </tr>
                <tr v-if="!reportData.length">
                  <td colspan="4" class="state-c">Sin datos</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>
    </div>

    <!-- ══ MODAL: CONFIRM CUT ═══════════════════════════════════════════════ -->
    <teleport to="body">
      <div v-if="showConfirm" class="modal-bg" @click.self="showConfirm=false">
        <div class="conf-panel">
          <h6 class="conf-title">Confirmar Corte de Inventario</h6>
          <p class="conf-body">
            Se va a registrar el inventario físico con fecha <strong>{{ fecha }}</strong>.<br />
            <strong>{{ countedItems }}</strong> insumos con existencias.<br />
            Los insumos no contados quedarán en <strong>0</strong>.
          </p>
          <p class="conf-warn">Esta acción actualiza el stock en tiempo real.</p>
          <div class="conf-actions">
            <button class="btn-cancel" @click="showConfirm=false">Cancelar</button>
            <button class="btn-confirm" :disabled="saving" @click="executeCut">
              <i class="bi bi-check2-circle"></i> {{ saving ? 'Generando...' : 'Generar Corte' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Report after cut -->
      <div v-if="showReport" class="modal-bg" @click.self="showReport=false">
        <div class="rep-panel">
          <div class="rep-hdr">
            <div>
              <div class="rep-title">Reporte de Diferencias — {{ fecha }}</div>
              <small class="td-muted">{{ reportAfterCut.length }} insumos procesados</small>
            </div>
            <button class="btn-close-x" @click="showReport=false"><i class="bi bi-x-lg"></i></button>
          </div>
          <div class="rep-tbl-wrap">
            <table class="rep-tbl">
              <thead>
                <tr>
                  <th>Insumo</th>
                  <th>Unidad</th>
                  <th class="tr">Stock previo</th>
                  <th class="tr">Contado</th>
                  <th class="tr">Diferencia</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in reportAfterCut" :key="r.id_item" :class="diffCls(r.diferencia)">
                  <td><strong>{{ r.item_name }}</strong></td>
                  <td class="td-muted sm">{{ r.unit_name }}</td>
                  <td class="tr td-muted">{{ fmtQty(r.sistema) }}</td>
                  <td class="tr">{{ fmtQty(r.contado) }}</td>
                  <td class="tr fw-b" :class="r.diferencia < 0 ? 'c-red' : r.diferencia > 0 ? 'c-green' : 'td-muted'">
                    {{ r.diferencia > 0 ? '+' : '' }}{{ fmtQty(r.diferencia) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="rep-footer">
            <button class="btn-cancel" @click="showReport=false; tab='history'; loadHistory()">
              <i class="bi bi-check2"></i> Cerrar y ver historial
            </button>
          </div>
        </div>
      </div>
    </teleport>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'

const tab = ref('take')

// ── TAKE INVENTORY ────────────────────────────────────────────────────────────
const today     = () => new Date().toISOString().slice(0, 10)
const fecha      = ref(today())
const observacion = ref('')
const barcodeQ   = ref('')
const listFilter  = ref('')
const barcodeRef  = ref(null)

const allItems   = ref([])
const quantities  = ref({})   // { id_item: number }
const inputRefs   = {}

const loadingItems = ref(true)
const saving       = ref(false)
const showConfirm  = ref(false)
const showReport   = ref(false)
const reportAfterCut = ref([])

const fmtQty  = v => Number(v || 0).toLocaleString('es-CO', { maximumFractionDigits: 4 })
const fmtDate = v => v ? String(v).slice(0, 10) : '—'
const fmtTime = v => v ? String(v).slice(11, 16) : ''

const filteredItems = computed(() => {
  const q = listFilter.value.toLowerCase()
  return allItems.value.filter(i =>
    !q || i.description.toLowerCase().includes(q) || (i.code || '').toLowerCase().includes(q)
  )
})

const countedItems = computed(() =>
  filteredItems.value.filter(i => (quantities.value[i.id_item] || 0) > 0).length
)

function setQty(id_item, val) {
  quantities.value[id_item] = parseFloat(val) || 0
}

function resetAll() {
  Object.keys(quantities.value).forEach(k => { quantities.value[k] = 0 })
}

function handleBarcode() {
  const q = barcodeQ.value.trim()
  if (!q) return
  const found = allItems.value.find(i =>
    (i.code || '').toLowerCase() === q.toLowerCase() ||
    i.description.toLowerCase().includes(q.toLowerCase())
  )
  if (found) {
    const el = inputRefs[found.id_item]
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' })
      setTimeout(() => el.focus(), 200)
    }
  } else {
    showToast('Insumo no encontrado', 'warning')
  }
  barcodeQ.value = ''
}

async function loadItems() {
  loadingItems.value = true
  try {
    const data = (await api.get('/api/inventory/stock', { params: { active: '1' } })).data
    allItems.value = data.filter(i => i.control_stock)
    const init = {}
    allItems.value.forEach(i => { init[i.id_item] = 0 })
    quantities.value = init
  } catch (e) { console.error(e) }
  finally { loadingItems.value = false }
}

function confirmCut() { showConfirm.value = true }

async function executeCut() {
  saving.value = true
  showConfirm.value = false
  try {
    const items = allItems.value.map(i => ({
      id_item: i.id_item,
      cantidad: quantities.value[i.id_item] || 0,
    }))
    const res = await api.post('/api/inventory/physical/bulk', {
      fecha: fecha.value,
      observacion: observacion.value,
      items,
    })
    showToast(`Corte generado — ${res.data.saved} items procesados`, 'success')
    // Load differences report
    try {
      reportAfterCut.value = (await api.get(`/api/inventory/physical/report/${fecha.value}`)).data
    } catch { reportAfterCut.value = [] }
    showReport.value = true
    resetAll()
  } catch (e) {
    showToast('Error al generar el corte', 'error')
  } finally { saving.value = false }
}

// ── HISTORY ───────────────────────────────────────────────────────────────────
const historyDates  = ref([])
const loadingHistory = ref(false)
const reportVisible  = ref(null)
const reportData     = ref([])
const loadingReport  = ref(false)

async function loadHistory() {
  loadingHistory.value = true
  reportVisible.value = null
  try {
    historyDates.value = (await api.get('/api/inventory/physical/dates')).data
  } catch { historyDates.value = [] }
  finally { loadingHistory.value = false }
}

async function toggleReport(fecha) {
  if (reportVisible.value === fecha) { reportVisible.value = null; return }
  reportVisible.value = fecha
  loadingReport.value = true
  try {
    reportData.value = (await api.get(`/api/inventory/physical/report/${fecha}`)).data
  } catch { reportData.value = [] }
  finally { loadingReport.value = false }
}

function diffCls(d) {
  if (d < 0) return 'diff-low'
  if (d > 0) return 'diff-high'
  return ''
}

onMounted(loadItems)
</script>

<style scoped>
.ip-wrap { padding: 16px; }

/* Tabs */
.tab-bar { display: flex; gap: 4px; margin-bottom: 18px; background: #f3f4f6; padding: 4px; border-radius: 10px; }
.tab    { flex: 1; padding: 9px 14px; border: none; background: transparent; cursor: pointer; border-radius: 8px; font-size: 0.85rem; color: #6b7280; font-weight: 500; }
.tab-on { flex: 1; padding: 9px 14px; border: none; background: #fff; cursor: pointer; border-radius: 8px; font-size: 0.85rem; color: #1d4ed8; font-weight: 700; box-shadow: 0 1px 4px rgba(0,0,0,.1); }
.tab-content { animation: fadeIn .15s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } }

/* Controls */
.take-controls { background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 10px; padding: 14px; margin-bottom: 14px; }
.ctrl-row { display: flex; gap: 12px; margin-bottom: 10px; flex-wrap: wrap; }
.ctrl-row:last-child { margin-bottom: 0; }
.ctrl-group { display: flex; flex-direction: column; gap: 4px; }
.flex-1 { flex: 1; min-width: 140px; }
.ctrl-lbl { font-size: 0.78rem; font-weight: 600; color: #374151; }
.ctrl-inp { padding: 8px 10px; border: 1px solid #d1d5db; border-radius: 7px; font-size: 0.87rem; background: #fff; width: 100%; box-sizing: border-box; }
.ctrl-inp:focus { outline: none; border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37,99,235,.1); }

/* Counter bar */
.counter-bar { display: flex; justify-content: space-between; align-items: center; padding: 8px 4px; margin-bottom: 10px; }
.cnt-info { font-size: 0.85rem; color: #374151; }
.btn-reset { background: none; border: 1px solid #d1d5db; border-radius: 6px; padding: 5px 10px; cursor: pointer; font-size: 0.8rem; color: #6b7280; }
.btn-reset:hover { border-color: #9ca3af; color: #374151; }

/* Item list */
.items-list { display: flex; flex-direction: column; gap: 8px; max-height: calc(100vh - 320px); overflow-y: auto; padding-bottom: 80px; }
.item-row { display: flex; justify-content: space-between; align-items: center; padding: 12px 14px; background: #fff; border: 1px solid #e9ecef; border-radius: 10px; gap: 12px; }
.item-counted { border-color: #bbf7d0; background: #f0fdf4; }
.item-meta { min-width: 0; flex: 1; }
.item-name { font-weight: 600; font-size: 0.88rem; display: block; }
.item-sub  { font-size: 0.75rem; color: #9ca3af; display: block; }
.item-sys  { font-size: 0.75rem; color: #6b7280; display: block; margin-top: 2px; }
.item-input-wrap { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.qty-inp { width: 88px; padding: 10px 8px; border: 2px solid #d1d5db; border-radius: 8px; font-size: 1rem; font-weight: 700; text-align: right; background: #f9fafb; }
.qty-inp:focus { outline: none; border-color: #2563eb; background: #fff; }
.qty-filled { border-color: #16a34a !important; background: #fff !important; color: #15803d; }
.unit-lbl { font-size: 0.78rem; color: #9ca3af; min-width: 28px; }

/* Sticky footer */
.take-footer { position: fixed; bottom: 0; left: 0; right: 0; display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: #fff; border-top: 1px solid #e9ecef; box-shadow: 0 -4px 12px rgba(0,0,0,.08); z-index: 100; }
.footer-info { font-size: 0.85rem; color: #6b7280; }
.btn-cut { background: #16a34a; color: #fff; border: none; border-radius: 10px; padding: 12px 24px; font-size: 0.92rem; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 8px; }
.btn-cut:hover:not(:disabled) { background: #15803d; }
.btn-cut:disabled { opacity: .6; cursor: not-allowed; }

/* History */
.hist-card { background: #fff; border: 1px solid #e9ecef; border-radius: 10px; overflow: hidden; margin-bottom: 10px; }
.hist-top { display: flex; justify-content: space-between; align-items: center; padding: 14px 16px; cursor: pointer; user-select: none; }
.hist-top:hover { background: #f8f9fa; }
.hist-fecha { font-weight: 700; font-size: 0.95rem; display: block; }
.hist-sub   { font-size: 0.78rem; color: #6b7280; }
.chevron { color: #9ca3af; font-size: 0.9rem; }
.report-panel { border-top: 1px solid #e9ecef; overflow-x: auto; }

/* Report table */
.rep-tbl { width: 100%; border-collapse: collapse; font-size: 0.83rem; }
.rep-tbl th { background: #f8f9fa; padding: 8px 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #dee2e6; white-space: nowrap; }
.rep-tbl td { padding: 7px 12px; border-bottom: 1px solid #f0f0f0; }
.diff-low  { background: #fff5f5 !important; }
.diff-high { background: #f0fdf4 !important; }

/* Confirm modal */
.modal-bg { position: fixed; inset: 0; background: rgba(0,0,0,.5); z-index: 1100; display: flex; align-items: center; justify-content: center; padding: 16px; }
.conf-panel { background: #fff; border-radius: 14px; padding: 24px; max-width: 440px; width: 100%; box-shadow: 0 20px 60px rgba(0,0,0,.2); }
.conf-title { font-size: 1.05rem; font-weight: 700; margin: 0 0 14px; }
.conf-body  { font-size: 0.88rem; line-height: 1.6; margin-bottom: 12px; }
.conf-warn  { font-size: 0.82rem; color: #ea580c; background: #fff7ed; border: 1px solid #fed7aa; border-radius: 6px; padding: 8px 10px; margin-bottom: 18px; }
.conf-actions { display: flex; justify-content: flex-end; gap: 10px; }
.btn-cancel  { background: #fff; border: 1px solid #d1d5db; border-radius: 8px; padding: 10px 18px; cursor: pointer; font-size: 0.87rem; }
.btn-confirm { background: #16a34a; color: #fff; border: none; border-radius: 8px; padding: 10px 20px; cursor: pointer; font-size: 0.87rem; font-weight: 700; display: flex; align-items: center; gap: 7px; }
.btn-confirm:disabled { opacity: .6; cursor: not-allowed; }

/* Report modal after cut */
.rep-panel { background: #fff; border-radius: 14px; width: 100%; max-width: 760px; max-height: 88vh; display: flex; flex-direction: column; box-shadow: 0 24px 64px rgba(0,0,0,.2); }
.rep-hdr { display: flex; justify-content: space-between; align-items: flex-start; padding: 18px 20px 14px; border-bottom: 1px solid #e9ecef; }
.rep-title { font-weight: 700; font-size: 1rem; margin-bottom: 3px; }
.rep-tbl-wrap { overflow: auto; flex: 1; }
.rep-footer { padding: 14px 20px; border-top: 1px solid #e9ecef; display: flex; justify-content: flex-end; }
.btn-close-x { background: none; border: none; padding: 4px; cursor: pointer; color: #6b7280; font-size: 1.1rem; }

/* Utilities */
.state-c { text-align: center; padding: 30px; color: #9ca3af; }
.state-c.sm { padding: 16px; font-size: 0.85rem; }
.spin { animation: spin 1s linear infinite; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }
.tr { text-align: right; }
.td-muted { color: #6b7280; }
.sm { font-size: 0.8rem; }
.fw-b { font-weight: 700; }
.ml { margin-left: 4px; }
.c-red   { color: #dc2626; }
.c-green { color: #16a34a; }

@media (max-width: 768px) {
  .ctrl-row { gap: 8px; }
  .qty-inp { width: 72px; padding: 10px 6px; }
  .take-footer { padding: 10px 14px; }
  .btn-cut { padding: 10px 18px; font-size: 0.88rem; }
  .rep-panel { max-height: 92vh; border-radius: 14px 14px 0 0; align-self: flex-end; }
}
@media (max-width: 576px) {
  .ip-wrap { padding: 10px; }
  .tab-bar { margin-bottom: 12px; }
  .item-row { padding: 10px 12px; }
  .qty-inp { width: 68px; font-size: 0.95rem; }
}
</style>
