<template>
  <div class="ip-wrap">

    <!-- ══ VISTA PRINCIPAL: HISTORIAL CON SELECT ════════════════════════════════ -->
    <div v-if="tab==='history'" class="tab-content">

      <!-- Header row: select + acciones + botón Tomar Inventario -->
      <div class="hist-header-row">
        <div class="hist-sel-row">
          <label class="hist-sel-lbl"><i class="bi bi-calendar3"></i> Corte:</label>
          <div v-if="loadingHistory" class="td-muted sm">
            <i class="bi bi-arrow-repeat spin"></i> Cargando...
          </div>
          <template v-else-if="!historyDates.length">
            <span class="td-muted sm">Sin inventarios registrados</span>
          </template>
          <template v-else>
            <select v-model="selectedDate" @change="loadReportFor(selectedDate)" class="hist-sel">
              <option v-for="h in historyDates" :key="h.fecha" :value="h.fecha">
                {{ fmtDate(h.fecha) }} — {{ h.items_contados }} insumos · {{ h.usuario }}
              </option>
            </select>
            <span class="hist-badge">{{ reportData.length }} ítems</span>
            <button class="btn-del-date" @click="confirmDeleteDate" title="Eliminar corte completo">
              <i class="bi bi-trash3"></i>
            </button>
          </template>
        </div>
        <button class="btn-take-inv" @click="switchToTake">
          <i class="bi bi-clipboard-check"></i> Tomar Inventario
        </button>
      </div>

      <!-- KPI Bar -->
      <div v-if="reportData.length && !loadingReport" class="kpi-bar">
        <div class="kpi-card">
          <span class="kpi-n">{{ reportData.length }}</span>
          <span class="kpi-l">Insumos contados</span>
        </div>
        <div class="kpi-card kpi-red">
          <span class="kpi-n">{{ phyFaltantes }}</span>
          <span class="kpi-l">Faltantes</span>
        </div>
        <div class="kpi-card kpi-orange">
          <span class="kpi-n">{{ phySobrantes }}</span>
          <span class="kpi-l">Sobrantes</span>
        </div>
        <div class="kpi-card kpi-green">
          <span class="kpi-n">{{ phyExactos }}</span>
          <span class="kpi-l">Exactos</span>
        </div>
      </div>

      <!-- Filters + Export -->
      <div v-if="reportData.length && !loadingReport" class="filters-bar">
        <div class="f-search-wrap">
          <i class="bi bi-search f-ico"></i>
          <input v-model.trim="phySearch" class="f-inp" placeholder="Buscar insumo o código..." />
        </div>
        <div class="toggle-grp">
          <button @click="phyFilter='all'"      :class="phyFilter==='all'      ? 'tog-on' : 'tog'">Todos</button>
          <button @click="phyFilter='faltante'" :class="phyFilter==='faltante' ? 'tog-on' : 'tog'">Faltantes</button>
          <button @click="phyFilter='sobrante'" :class="phyFilter==='sobrante' ? 'tog-on' : 'tog'">Sobrantes</button>
          <button @click="phyFilter='exacto'"   :class="phyFilter==='exacto'   ? 'tog-on' : 'tog'">Exactos</button>
        </div>
        <ExportToolbar
          :data="phyExportData"
          :columns="phyExportCols"
          filename="inventario-fisico"
          title="Inventario Físico"
        />
      </div>

      <!-- Loading reporte -->
      <div v-if="loadingReport" class="state-c sm">
        <i class="bi bi-arrow-repeat spin"></i> Cargando reporte...
      </div>

      <template v-else-if="phyGrouped.length">
        <!-- Column headers desktop -->
        <div class="list-hdr">
          <span></span>
          <span class="hdr-main">Insumo</span>
          <span class="hdr-r tr">Sistema prev.</span>
          <span class="hdr-r tr">Contado</span>
          <span class="hdr-r tr">Diferencia</span>
          <span class="hdr-act tc">Acciones</span>
        </div>

        <!-- Accordion por categoría -->
        <div v-for="group in phyGrouped" :key="group.name" class="cat-group">
          <div class="cat-hdr" :class="{ 'cat-hdr-open': openPhyCat === group.name }" @click="togglePhyCat(group.name)">
            <i class="bi bi-tag-fill cat-ico"></i>
            <span class="cat-hdr-name">{{ group.name }}</span>
            <span class="cat-hdr-cnt">{{ group.items.length }} ítem{{ group.items.length !== 1 ? 's' : '' }}</span>
            <i class="bi bi-chevron-down cat-chevron" :class="{ 'cat-chevron-open': openPhyCat === group.name }"></i>
          </div>
          <div v-show="openPhyCat === group.name" class="cards-list">
            <div v-for="r in group.items" :key="r.id" class="sc" :class="phyScCls(r)">
              <div class="sc-status">
                <span :class="phyBadge(r)" class="sb">{{ phyLbl(r) }}</span>
              </div>
              <div class="sc-main">
                <div class="sc-name">
                  {{ r.item_name }}
                  <span v-if="r.code" class="sc-code">{{ r.code }}</span>
                </div>
                <div class="sc-cat">{{ r.unit_name }}</div>
              </div>
              <div class="sc-prev">
                <span class="min-lbl">Sistema:</span>
                <span class="fw-b td-muted">{{ fmtQty(r.sistema) }}</span>
              </div>
              <div class="sc-contado">
                <span class="min-lbl">Contado:</span>
                <span class="fw-b">{{ fmtQty(r.contado) }}</span>
              </div>
              <div class="sc-diff">
                <span class="min-lbl">Dif:</span>
                <span class="fw-b" :class="r.diferencia < 0 ? 'c-red' : r.diferencia > 0 ? 'c-orange' : 'td-muted'">
                  {{ r.diferencia > 0 ? '+' : '' }}{{ fmtQty(r.diferencia) }}
                </span>
              </div>
              <div class="sc-act">
                <div class="row-actions">
                  <button class="btn-row-edit" @click.stop="openEditItem(r)" title="Editar cantidad">
                    <i class="bi bi-pencil"></i>
                  </button>
                  <button class="btn-row-del" @click.stop="deleteItem(r)" title="Eliminar ítem">
                    <i class="bi bi-x-lg"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Agregar ítem al corte -->
        <div class="add-item-bar">
          <button class="btn-add-item" @click="openAddItem">
            <i class="bi bi-plus-lg"></i> Agregar ítem a este corte
          </button>
        </div>
      </template>

      <div v-else-if="!loadingHistory && !loadingReport && selectedDate" class="state-c">
        Sin registros para este corte
        <div class="mt-sm">
          <button class="btn-add-item" @click="openAddItem">
            <i class="bi bi-plus-lg"></i> Agregar ítem
          </button>
        </div>
      </div>
      <div v-else-if="!loadingHistory && !loadingReport" class="state-c">
        Seleccione un corte para ver el reporte
      </div>
    </div>

    <!-- ══ TOMAR INVENTARIO ══════════════════════════════════════════════════════ -->
    <div v-if="tab==='take'" class="tab-content">

      <!-- Back to history -->
      <div class="take-top-bar">
        <button class="btn-back" @click="tab = 'history'">
          <i class="bi bi-arrow-left"></i> Volver al historial
        </button>
      </div>

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

      <!-- Loading items -->
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

    <!-- ══ MODAL: CONFIRM CUT ═════════════════════════════════════════════════ -->
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

      <!-- Reporte tras generar corte -->
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
            <button class="btn-cancel" @click="afterCutClose">
              <i class="bi bi-check2"></i> Cerrar y ver historial
            </button>
          </div>
        </div>
      </div>

      <!-- Modal: confirmar eliminar corte completo -->
      <div v-if="showDeleteDate" class="modal-bg" @click.self="showDeleteDate=false">
        <div class="conf-panel">
          <h6 class="conf-title c-red"><i class="bi bi-trash3 me-1"></i> Eliminar corte completo</h6>
          <p class="conf-body">
            Se eliminarán <strong>todos los registros</strong> del corte
            <strong>{{ fmtDate(selectedDate) }}</strong> ({{ reportData.length }} ítems).<br/>
            Esta acción no se puede deshacer.
          </p>
          <div class="conf-actions">
            <button class="btn-cancel" @click="showDeleteDate=false">Cancelar</button>
            <button class="btn-danger" :disabled="saving" @click="executeDeleteDate">
              <i class="bi bi-trash3"></i> {{ saving ? 'Eliminando...' : 'Eliminar corte' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Modal: editar ítem -->
      <div v-if="editRow" class="modal-bg" @click.self="editRow=null">
        <div class="conf-panel">
          <h6 class="conf-title"><i class="bi bi-pencil me-1"></i> Editar ítem</h6>
          <p class="conf-body">
            <strong>{{ editRow.item_name }}</strong> — {{ editRow.unit_name }}
          </p>
          <div class="form-field">
            <label class="ctrl-lbl">Cantidad contada</label>
            <input type="number" inputmode="decimal" step="0.001" min="0"
                   v-model="editQty" class="ctrl-inp" />
          </div>
          <div class="form-field mt-sm">
            <label class="ctrl-lbl">Observación</label>
            <input type="text" v-model="editObs" class="ctrl-inp" placeholder="Opcional..." />
          </div>
          <div class="conf-actions">
            <button class="btn-cancel" @click="editRow=null">Cancelar</button>
            <button class="btn-confirm" :disabled="saving" @click="saveEditItem">
              <i class="bi bi-check2"></i> {{ saving ? 'Guardando...' : 'Guardar' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Modal: agregar ítem al corte -->
      <div v-if="showAddItem" class="modal-bg" @click.self="showAddItem=false">
        <div class="conf-panel wide">
          <h6 class="conf-title"><i class="bi bi-plus-lg me-1"></i> Agregar ítem al corte {{ fmtDate(selectedDate) }}</h6>
          <div class="form-field">
            <label class="ctrl-lbl">Buscar insumo</label>
            <input type="text" v-model="addSearch" class="ctrl-inp"
                   placeholder="Nombre o código..." @input="filterAddItems" />
          </div>
          <div class="add-item-list">
            <div v-if="loadingAddItems" class="state-c sm"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
            <template v-else>
              <div v-for="it in filteredAddItems" :key="it.id_item"
                   class="add-item-opt" :class="{ selected: addSelItem?.id_item === it.id_item }"
                   @click="addSelItem = it">
                <span class="add-item-name">{{ it.description }}</span>
                <span class="add-item-unit td-muted">{{ it.unit_name }}</span>
              </div>
              <div v-if="!filteredAddItems.length" class="state-c sm">Sin resultados</div>
            </template>
          </div>
          <div v-if="addSelItem" class="form-field mt-sm">
            <label class="ctrl-lbl">Cantidad — <strong>{{ addSelItem.description }}</strong> ({{ addSelItem.unit_name }})</label>
            <input type="number" inputmode="decimal" step="0.001" min="0"
                   v-model="addQty" class="ctrl-inp" />
          </div>
          <div class="conf-actions">
            <button class="btn-cancel" @click="showAddItem=false">Cancelar</button>
            <button class="btn-confirm" :disabled="saving || !addSelItem" @click="saveAddItem">
              <i class="bi bi-plus-lg"></i> {{ saving ? 'Guardando...' : 'Agregar' }}
            </button>
          </div>
        </div>
      </div>

    </teleport>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'
import ExportToolbar from '@/components/common/ExportToolbar.vue'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'
import Swal from 'sweetalert2'

const tab = ref('history')

// ── HISTORY ───────────────────────────────────────────────────────────────────
const historyDates   = ref([])
const selectedDate   = ref(null)
const reportData     = ref([])
const loadingHistory = ref(false)
const loadingReport  = ref(false)

// ── Filtros del reporte ───────────────────────────────────────────────────────
const phySearch = ref('')
const phyFilter = ref('all')
const openPhyCat = ref(null)

function togglePhyCat(name) { openPhyCat.value = openPhyCat.value === name ? null : name }

// ── KPI computados ────────────────────────────────────────────────────────────
const phyFaltantes = computed(() => reportData.value.filter(r => r.diferencia < 0).length)
const phySobrantes = computed(() => reportData.value.filter(r => r.diferencia > 0).length)
const phyExactos   = computed(() => reportData.value.filter(r => r.diferencia === 0).length)

// ── Reporte filtrado + agrupado ───────────────────────────────────────────────
const filteredReport = computed(() => {
  let data = reportData.value
  const q = phySearch.value.toLowerCase()
  if (q) data = data.filter(r =>
    r.item_name.toLowerCase().includes(q) || (r.code || '').toLowerCase().includes(q)
  )
  if (phyFilter.value === 'faltante') data = data.filter(r => r.diferencia < 0)
  if (phyFilter.value === 'sobrante') data = data.filter(r => r.diferencia > 0)
  if (phyFilter.value === 'exacto')   data = data.filter(r => r.diferencia === 0)
  return data
})

const phyGrouped = computed(() => {
  const nocat = 'Sin categoría'
  const map = {}
  for (const r of filteredReport.value) {
    const key = r.category_name || nocat
    if (!map[key]) map[key] = { name: key, items: [] }
    map[key].items.push(r)
  }
  const groups = Object.values(map).sort((a, b) =>
    a.name === nocat ? 1 : b.name === nocat ? -1 : a.name.localeCompare(b.name, 'es')
  )
  groups.forEach(g => g.items.sort((a, b) => a.item_name.localeCompare(b.item_name, 'es')))
  return groups
})

// ── Export ────────────────────────────────────────────────────────────────────
const phyExportData = computed(() => {
  const result = []
  for (const g of phyGrouped.value) {
    result.push({ _sectionHeader: true, _title: g.name })
    result.push(...g.items)
  }
  return result
})
const phyExportCols = [
  { key: 'item_name',  label: 'Insumo' },
  { key: 'code',       label: 'Código' },
  { key: 'unit_name',  label: 'Unidad' },
  { key: 'sistema',    label: 'Sistema prev.', fmt: v => Number(v||0).toFixed(4) },
  { key: 'contado',    label: 'Contado',       fmt: v => Number(v||0).toFixed(4) },
  { key: 'diferencia', label: 'Diferencia',    fmt: v => Number(v||0).toFixed(4) },
]

// ── Status helpers ────────────────────────────────────────────────────────────
function phyLbl(r) {
  if (r.diferencia < 0) return '⬇ Faltante'
  if (r.diferencia > 0) return '⬆ Sobrante'
  return '✅ Exacto'
}
function phyBadge(r) {
  if (r.diferencia < 0) return 'b-out'
  if (r.diferencia > 0) return 'b-crit'
  return 'b-ok'
}
function phyScCls(r) {
  if (r.diferencia < 0) return 'sc-out'
  if (r.diferencia > 0) return 'sc-crit'
  return ''
}

// ── CRUD eliminar corte ────────────────────────────────────────────────────────
const showDeleteDate = ref(false)
function confirmDeleteDate() { showDeleteDate.value = true }
async function executeDeleteDate() {
  saving.value = true
  try {
    await api.delete(`/api/inventory/physical/date/${selectedDate.value}`)
    showToast('Corte eliminado correctamente', 'success')
    showDeleteDate.value = false
    selectedDate.value = null
    reportData.value = []
    await loadHistory()
  } catch { showToast('Error al eliminar el corte', 'error') }
  finally { saving.value = false }
}

// ── CRUD editar ítem ──────────────────────────────────────────────────────────
const editRow = ref(null)
const editQty = ref(0)
const editObs = ref('')
function openEditItem(r) {
  editRow.value = r
  editQty.value = r.contado
  editObs.value = r.observacion || ''
}
async function saveEditItem() {
  saving.value = true
  try {
    await api.patch(`/api/inventory/physical/${editRow.value.id}`, {
      cantidad: editQty.value,
      observacion: editObs.value,
    })
    showToast('Ítem actualizado', 'success')
    editRow.value = null
    await loadReportFor(selectedDate.value)
  } catch { showToast('Error al guardar', 'error') }
  finally { saving.value = false }
}

// ── CRUD eliminar ítem ────────────────────────────────────────────────────────
async function deleteItem(r) {
  const result = await Swal.fire({
    title: '¿Eliminar ítem?',
    text: `¿Eliminar "${r.item_name}" de este corte?`,
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#e11d48',
    confirmButtonText: 'Sí, eliminar',
    cancelButtonText: 'Cancelar',
  })
  if (!result.isConfirmed) return
  saving.value = true
  try {
    await api.delete(`/api/inventory/physical/${r.id}`)
    showToast('Ítem eliminado', 'success')
    await loadReportFor(selectedDate.value)
    await loadHistory()
  } catch { showToast('Error al eliminar', 'error') }
  finally { saving.value = false }
}

// ── CRUD agregar ítem al corte ────────────────────────────────────────────────
const showAddItem   = ref(false)
const addSearch     = ref('')
const addSelItem    = ref(null)
const addQty        = ref(0)
const allAddItems   = ref([])
const loadingAddItems = ref(false)
const filteredAddItems = computed(() => {
  const q = addSearch.value.toLowerCase()
  return allAddItems.value.filter(i =>
    !q || i.description.toLowerCase().includes(q) || (i.code || '').toLowerCase().includes(q)
  ).slice(0, 40)
})
async function openAddItem() {
  showAddItem.value = true
  addSearch.value = ''
  addSelItem.value = null
  addQty.value = 0
  if (!allAddItems.value.length) {
    loadingAddItems.value = true
    try {
      allAddItems.value = (await api.get('/api/inventory/stock', { params: { active: '1' } })).data
    } catch { allAddItems.value = [] }
    finally { loadingAddItems.value = false }
  }
}
async function saveAddItem() {
  saving.value = true
  try {
    await api.post('/api/inventory/physical', {
      id_item: addSelItem.value.id_item,
      cantidad: addQty.value,
      fecha: selectedDate.value,
    })
    showToast('Ítem agregado al corte', 'success')
    showAddItem.value = false
    await loadReportFor(selectedDate.value)
    await loadHistory()
  } catch (e) {
    showToast(e.response?.data?.detail || 'Error al agregar', 'error')
  } finally { saving.value = false }
}

async function loadHistory() {
  loadingHistory.value = true
  try {
    historyDates.value = (await api.get('/api/inventory/physical/dates')).data
    if (historyDates.value.length && !selectedDate.value) {
      selectedDate.value = historyDates.value[0].fecha
      await loadReportFor(selectedDate.value)
    } else if (selectedDate.value) {
      await loadReportFor(selectedDate.value)
    }
  } catch { historyDates.value = [] }
  finally { loadingHistory.value = false }
}

async function loadReportFor(fecha) {
  if (!fecha) return
  openPhyCat.value = null
  phySearch.value = ''
  phyFilter.value = 'all'
  loadingReport.value = true
  try {
    reportData.value = (await api.get(`/api/inventory/physical/report/${fecha}`)).data
    await nextTick()
    if (phyGrouped.value.length) openPhyCat.value = phyGrouped.value[0].name
  } catch { reportData.value = [] }
  finally { loadingReport.value = false }
}

// ── TAKE INVENTORY ────────────────────────────────────────────────────────────
const today      = () => new Date().toISOString().slice(0, 10)
const fecha      = ref(today())
const observacion = ref('')
const barcodeQ   = ref('')
const listFilter  = ref('')
const barcodeRef  = ref(null)
const allItems   = ref([])
const quantities  = ref({})
const inputRefs   = {}
const loadingItems = ref(false)
const saving       = ref(false)
const showConfirm  = ref(false)
const showReport   = ref(false)
const reportAfterCut = ref([])

async function switchToTake() {
  tab.value = 'take'
  if (!allItems.value.length && !loadingItems.value) await loadItems()
}

const fmtQty  = v => Number(v || 0).toLocaleString('es-CO', { maximumFractionDigits: 4 })
const fmtDate = v => {
  if (!v) return '—'
  const s = String(v).slice(0, 10)
  const [y, m, d] = s.split('-')
  return `${d}-${m}-${y}`
}

const filteredItems = computed(() => {
  const q = listFilter.value.toLowerCase()
  return allItems.value.filter(i =>
    !q || i.description.toLowerCase().includes(q) || (i.code || '').toLowerCase().includes(q)
  )
})

const countedItems = computed(() =>
  filteredItems.value.filter(i => (quantities.value[i.id_item] || 0) > 0).length
)

function setQty(id_item, val) { quantities.value[id_item] = parseFloat(val) || 0 }
function resetAll() { Object.keys(quantities.value).forEach(k => { quantities.value[k] = 0 }) }

function handleBarcode() {
  const q = barcodeQ.value.trim()
  if (!q) return
  const found = allItems.value.find(i =>
    (i.code || '').toLowerCase() === q.toLowerCase() ||
    i.description.toLowerCase().includes(q.toLowerCase())
  )
  if (found) {
    const el = inputRefs[found.id_item]
    if (el) { el.scrollIntoView({ behavior: 'smooth', block: 'center' }); setTimeout(() => el.focus(), 200) }
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
    const items = allItems.value.map(i => ({ id_item: i.id_item, cantidad: quantities.value[i.id_item] || 0 }))
    const res = await api.post('/api/inventory/physical/bulk', { fecha: fecha.value, observacion: observacion.value, items })
    showToast(`Corte generado — ${res.data.saved} items procesados`, 'success')
    try {
      reportAfterCut.value = (await api.get(`/api/inventory/physical/report/${fecha.value}`)).data
    } catch { reportAfterCut.value = [] }
    showReport.value = true
    resetAll()
  } catch {
    showToast('Error al generar el corte', 'error')
  } finally { saving.value = false }
}

async function afterCutClose() {
  showReport.value = false
  selectedDate.value = null
  await loadHistory()
  tab.value = 'history'
}

function diffCls(d) {
  if (d < 0) return 'diff-low'
  if (d > 0) return 'diff-high'
  return ''
}

onMounted(loadHistory)
</script>

<style scoped>
.ip-wrap { padding: 16px; }
.tab-content { animation: fadeIn .15s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } }

/* ── KPI Bar ── */
.kpi-bar { display: flex; gap: 12px; margin-bottom: 14px; flex-wrap: wrap; }
.kpi-card { flex: 1; min-width: 100px; background: #f8f9fa; border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; gap: 2px; border: 1px solid #e9ecef; }
.kpi-green  { background: #f0fdf4; border-color: #bbf7d0; }
.kpi-red    { background: #fff1f2; border-color: #fecdd3; }
.kpi-orange { background: #fff7ed; border-color: #fed7aa; }
.kpi-n { font-size: 1.5rem; font-weight: 700; line-height: 1; }
.kpi-l { font-size: .74rem; color: #6b7280; font-weight: 500; }
.kpi-green .kpi-n  { color: #16a34a; }
.kpi-red .kpi-n    { color: #dc2626; }
.kpi-orange .kpi-n { color: #ea580c; }

/* ── Filters bar ── */
.filters-bar { display: flex; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; align-items: center; }
.f-search-wrap { position: relative; flex: 1; min-width: 190px; }
.f-ico { position: absolute; left: 9px; top: 50%; transform: translateY(-50%); color: #9ca3af; font-size: .83rem; }
.f-inp { width: 100%; padding: 8px 10px 8px 28px; border: 1px solid #d1d5db; border-radius: 8px; font-size: .86rem; box-sizing: border-box; }
.toggle-grp { display: flex; border: 1px solid #d1d5db; border-radius: 8px; overflow: hidden; }
.tog    { padding: 7px 11px; background: #fff; border: none; cursor: pointer; font-size: .80rem; color: #374151; }
.tog-on { padding: 7px 11px; background: #2563eb; color: #fff; border: none; cursor: pointer; font-size: .80rem; font-weight: 600; }

/* ── Column headers desktop ── */
.list-hdr {
  display: none;
  padding: 4px 14px;
  font-size: .72rem; font-weight: 700; color: #9ca3af; text-transform: uppercase; letter-spacing: .04em;
  margin-bottom: 2px;
}
.hdr-main { flex: 1; }
.hdr-r    { width: 110px; }
.hdr-act  { width: 80px; }

/* ── Accordion ── */
.cat-group { margin-bottom: 10px; }
.cat-hdr {
  display: flex; align-items: center; gap: 8px;
  background: #1d4ed8; color: #fff;
  border-radius: 8px; padding: 9px 14px; cursor: pointer;
  user-select: none; transition: border-radius .15s;
}
.cat-hdr-open { border-radius: 8px 8px 0 0; }
.cat-hdr:hover { background: #1e40af; }
.cat-ico { font-size: .8rem; flex-shrink: 0; }
.cat-hdr-name { font-weight: 700; font-size: .85rem; flex: 1; }
.cat-hdr-cnt { font-size: .74rem; background: rgba(255,255,255,.2); padding: 2px 8px; border-radius: 10px; white-space: nowrap; }
.cat-chevron { font-size: .7rem; flex-shrink: 0; transition: transform .2s; margin-left: 4px; }
.cat-chevron-open { transform: rotate(180deg); }

/* ── Cards list ── */
.cards-list { display: flex; flex-direction: column; gap: 0; border: 1px solid #dbeafe; border-top: none; border-radius: 0 0 8px 8px; overflow: hidden; }

.sc {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px; background: #fff;
  border-bottom: 1px solid #f0f0f0;
}
.sc:last-child { border-bottom: none; }
.sc:hover { background: #fafbff; }
.sc-out  { border-left: 4px solid #dc2626; background: #fff5f5 !important; }
.sc-crit { border-left: 4px solid #ea580c; background: #fffbf0 !important; }

/* Status */
.sc-status { flex-shrink: 0; }
.sb { padding: 3px 8px; border-radius: 20px; font-size: .73rem; font-weight: 600; white-space: nowrap; }
.b-out  { background: #fee2e2; color: #dc2626; }
.b-crit { background: #ffedd5; color: #ea580c; }
.b-ok   { background: #dcfce7; color: #16a34a; }

/* Main */
.sc-main { flex: 1; min-width: 0; }
.sc-name { font-weight: 700; font-size: .88rem; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.sc-code { font-size: .72rem; color: #9ca3af; font-weight: 400; }
.sc-cat  { font-size: .77rem; color: #6b7280; margin-top: 1px; }

/* Data cols */
.sc-prev    { display: flex; flex-direction: column; align-items: flex-end; flex-shrink: 0; width: 100px; }
.sc-contado { display: flex; flex-direction: column; align-items: flex-end; flex-shrink: 0; width: 100px; }
.sc-diff    { display: flex; flex-direction: column; align-items: flex-end; flex-shrink: 0; width: 90px; }
.min-lbl { font-size: .73rem; color: #9ca3af; }
.fw-b { font-weight: 700; }

/* Actions */
.sc-act { flex-shrink: 0; }
.row-actions { display: flex; gap: 4px; }
.btn-row-edit { background: none; border: 1px solid #bfdbfe; color: #2563eb; border-radius: 6px; padding: 5px 8px; cursor: pointer; font-size: .82rem; }
.btn-row-edit:hover { background: #eff6ff; }
.btn-row-del  { background: none; border: 1px solid #fca5a5; color: #dc2626; border-radius: 6px; padding: 5px 8px; cursor: pointer; font-size: .82rem; }
.btn-row-del:hover { background: #fef2f2; }

/* ── Historial: header con select + botón ── */
.hist-header-row {
  display: flex; align-items: flex-start; gap: 10px;
  margin-bottom: 14px; flex-wrap: wrap;
}
.hist-sel-row {
  flex: 1; min-width: 0;
  display: flex; align-items: center; gap: 10px;
  background: #f0f9ff; border: 1px solid #bae6fd;
  border-radius: 10px; padding: 10px 14px; flex-wrap: wrap;
}
.btn-take-inv {
  background: #16a34a; color: #fff; border: none; border-radius: 10px;
  padding: 10px 18px; font-size: 0.88rem; font-weight: 700; cursor: pointer;
  display: flex; align-items: center; gap: 7px; white-space: nowrap; flex-shrink: 0;
}
.btn-take-inv:hover { background: #15803d; }
.hist-sel-lbl { font-size: 0.82rem; font-weight: 600; color: #0369a1; white-space: nowrap; }
.hist-sel {
  flex: 1; min-width: 200px;
  padding: 8px 10px; border: 1px solid #bae6fd; border-radius: 8px;
  font-size: 0.86rem; background: #fff; color: #0f172a; cursor: pointer; outline: none;
}
.hist-sel:focus { border-color: #2563eb; }
.hist-badge {
  font-size: 0.76rem; font-weight: 700;
  background: #dbeafe; color: #1d4ed8;
  padding: 3px 10px; border-radius: 20px; white-space: nowrap;
}
.btn-del-date {
  background: none; border: 1px solid #fca5a5; color: #dc2626;
  border-radius: 7px; padding: 5px 9px; cursor: pointer; font-size: 0.85rem; flex-shrink: 0;
}
.btn-del-date:hover { background: #fef2f2; }

/* ── Tomar inventario ── */
.take-top-bar { margin-bottom: 12px; }
.btn-back {
  background: none; border: 1px solid #d1d5db; border-radius: 8px;
  padding: 7px 14px; cursor: pointer; font-size: 0.85rem; color: #374151;
  display: inline-flex; align-items: center; gap: 6px;
}
.btn-back:hover { border-color: #6b7280; }
.take-controls { background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 10px; padding: 14px; margin-bottom: 14px; }
.ctrl-row { display: flex; gap: 12px; margin-bottom: 10px; flex-wrap: wrap; }
.ctrl-row:last-child { margin-bottom: 0; }
.ctrl-group { display: flex; flex-direction: column; gap: 4px; }
.flex-1 { flex: 1; min-width: 140px; }
.ctrl-lbl { font-size: 0.78rem; font-weight: 600; color: #374151; }
.ctrl-inp { padding: 8px 10px; border: 1px solid #d1d5db; border-radius: 7px; font-size: 0.87rem; background: #fff; width: 100%; box-sizing: border-box; }
.ctrl-inp:focus { outline: none; border-color: #2563eb; }

.counter-bar { display: flex; justify-content: space-between; align-items: center; padding: 8px 4px; margin-bottom: 10px; }
.cnt-info { font-size: 0.85rem; color: #374151; }
.btn-reset { background: none; border: 1px solid #d1d5db; border-radius: 6px; padding: 5px 10px; cursor: pointer; font-size: 0.8rem; color: #6b7280; }
.btn-reset:hover { border-color: #9ca3af; color: #374151; }

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

.take-footer { position: fixed; bottom: 0; left: 0; right: 0; display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: #fff; border-top: 1px solid #e9ecef; box-shadow: 0 -4px 12px rgba(0,0,0,.08); z-index: 100; }
.footer-info { font-size: 0.85rem; color: #6b7280; }
.btn-cut { background: #16a34a; color: #fff; border: none; border-radius: 10px; padding: 12px 24px; font-size: 0.92rem; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 8px; }
.btn-cut:hover:not(:disabled) { background: #15803d; }
.btn-cut:disabled { opacity: .6; cursor: not-allowed; }

/* ── Agregar ítem ── */
.add-item-bar { padding: 10px 0; }
.btn-add-item {
  background: none; border: 1px dashed #6b7280; border-radius: 8px;
  padding: 8px 16px; cursor: pointer; font-size: 0.85rem; color: #374151;
  display: inline-flex; align-items: center; gap: 6px;
}
.btn-add-item:hover { border-color: #2563eb; color: #2563eb; background: #eff6ff; }
.mt-sm { margin-top: 10px; }
.conf-panel.wide { max-width: 520px; }
.form-field { display: flex; flex-direction: column; gap: 4px; }
.add-item-list { border: 1px solid #e9ecef; border-radius: 8px; max-height: 180px; overflow-y: auto; margin-top: 6px; }
.add-item-opt { display: flex; justify-content: space-between; align-items: center; padding: 9px 12px; cursor: pointer; font-size: 0.86rem; border-bottom: 1px solid #f3f4f6; }
.add-item-opt:hover { background: #f0f9ff; }
.add-item-opt.selected { background: #dbeafe; }
.add-item-opt:last-child { border-bottom: none; }
.add-item-name { font-weight: 500; }
.add-item-unit { font-size: 0.78rem; }

/* ── Report table (modal after cut) ── */
.rep-tbl { width: 100%; border-collapse: collapse; font-size: 0.83rem; }
.rep-tbl th { background: #f8f9fa; padding: 8px 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #dee2e6; white-space: nowrap; position: sticky; top: 0; }
.rep-tbl td { padding: 7px 12px; border-bottom: 1px solid #f0f0f0; }
.diff-low  { background: #fff5f5 !important; }
.diff-high { background: #f0fdf4 !important; }

/* ── Confirm modals ── */
.modal-bg { position: fixed; inset: 0; background: rgba(0,0,0,.5); z-index: 1100; display: flex; align-items: center; justify-content: center; padding: 16px; }
.conf-panel { background: #fff; border-radius: 14px; padding: 24px; max-width: 440px; width: 100%; box-shadow: 0 20px 60px rgba(0,0,0,.2); }
.conf-title { font-size: 1.05rem; font-weight: 700; margin: 0 0 14px; }
.conf-body  { font-size: 0.88rem; line-height: 1.6; margin-bottom: 12px; }
.conf-warn  { font-size: 0.82rem; color: #ea580c; background: #fff7ed; border: 1px solid #fed7aa; border-radius: 6px; padding: 8px 10px; margin-bottom: 18px; }
.conf-actions { display: flex; justify-content: flex-end; gap: 10px; }
.btn-cancel  { background: #fff; border: 1px solid #d1d5db; border-radius: 8px; padding: 10px 18px; cursor: pointer; font-size: 0.87rem; }
.btn-confirm { background: #16a34a; color: #fff; border: none; border-radius: 8px; padding: 10px 20px; cursor: pointer; font-size: 0.87rem; font-weight: 700; display: flex; align-items: center; gap: 7px; }
.btn-confirm:disabled { opacity: .6; cursor: not-allowed; }
.btn-danger { background: #dc2626; color: #fff; border: none; border-radius: 8px; padding: 10px 18px; cursor: pointer; font-size: 0.87rem; font-weight: 700; display: flex; align-items: center; gap: 7px; }
.btn-danger:disabled { opacity: .6; cursor: not-allowed; }
.btn-danger:not(:disabled):hover { background: #b91c1c; }
.rep-panel { background: #fff; border-radius: 14px; width: 100%; max-width: 760px; max-height: 88vh; display: flex; flex-direction: column; box-shadow: 0 24px 64px rgba(0,0,0,.2); }
.rep-hdr { display: flex; justify-content: space-between; align-items: flex-start; padding: 18px 20px 14px; border-bottom: 1px solid #e9ecef; }
.rep-title { font-weight: 700; font-size: 1rem; margin-bottom: 3px; }
.rep-tbl-wrap { overflow: auto; flex: 1; }
.rep-footer { padding: 14px 20px; border-top: 1px solid #e9ecef; display: flex; justify-content: flex-end; }
.btn-close-x { background: none; border: none; padding: 4px; cursor: pointer; color: #6b7280; font-size: 1.1rem; }

/* ── Utilities ── */
.state-c { text-align: center; padding: 30px; color: #9ca3af; }
.state-c.sm { padding: 16px; font-size: 0.85rem; }
.spin { animation: spin 1s linear infinite; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }
.tr { text-align: right; }
.tc { text-align: center; }
.td-muted { color: #6b7280; }
.sm { font-size: 0.8rem; }
.c-red    { color: #dc2626; }
.c-orange { color: #ea580c; }
.c-green  { color: #16a34a; }

/* ── Desktop ── */
@media (min-width: 768px) {
  .list-hdr { display: flex; align-items: center; }
  .sc-prev, .sc-contado { width: 120px; }
  .sc-diff { width: 100px; }
}

/* ── Tablet ── */
@media (max-width: 767px) and (min-width: 577px) {
  .sc-prev, .sc-contado { width: 90px; }
  .sc-diff { width: 80px; }
  .ctrl-row { gap: 8px; }
}

/* ── Mobile ── */
@media (max-width: 576px) {
  .ip-wrap { padding: 10px; }
  .kpi-bar { gap: 6px; }
  .kpi-card { padding: 9px 10px; min-width: 70px; }
  .kpi-n { font-size: 1.2rem; }
  .filters-bar { flex-direction: column; align-items: stretch; }
  .toggle-grp .tog, .toggle-grp .tog-on { padding: 6px 7px; font-size: .76rem; }
  .sc { flex-wrap: wrap; gap: 8px; }
  .sc-status { width: 100%; order: -1; }
  .sc-main   { width: 100%; order: 0; }
  .sc-prev, .sc-contado, .sc-diff { width: auto; order: 1; flex-direction: row; align-items: center; gap: 4px; }
  .sc-act    { order: 2; margin-left: auto; }
  .hist-sel-row { flex-direction: column; align-items: stretch; }
  .hist-sel { min-width: 0; width: 100%; }
  .qty-inp { width: 72px; font-size: 0.95rem; }
  .take-footer { padding: 10px 14px; }
  .btn-cut { padding: 10px 18px; font-size: 0.88rem; }
  .rep-panel { max-height: 92vh; border-radius: 14px 14px 0 0; align-self: flex-end; }
}
</style>
