<template>
  <div class="hc-wrap">

    <!-- ── Filtros ─────────────────────────────────────────────── -->
    <div class="hc-filters card">
      <div class="hc-filters-head" @click="filtrosVisible = !filtrosVisible">
        <span class="hc-filters-label">
          <i class="bi bi-funnel-fill me-1"></i>Filtros
          <span v-if="!filtrosVisible && lista.length" class="hc-filters-hint">
            {{ fmtFecha(filtro.desde) }} — {{ fmtFecha(filtro.hasta) }}
          </span>
        </span>
        <i :class="filtrosVisible ? 'bi bi-chevron-up' : 'bi bi-chevron-down'" class="hc-chevron"></i>
      </div>

      <div v-show="filtrosVisible" class="hc-filters-body">
        <div class="hc-filter-row">
          <div class="hc-filter-group">
            <label class="hc-label">Tipo</label>
            <div class="hc-radios">
              <label v-for="op in tipoOpts" :key="op.value" class="hc-radio">
                <input type="radio" v-model="filtro.tipo" :value="op.value" @change="buscar" />
                {{ op.label }}
              </label>
            </div>
          </div>

          <div class="hc-filter-group">
            <label class="hc-label">Desde / Hasta</label>
            <div class="hc-fechas-row">
              <CustomDatePicker v-model="filtro.desde" @update:modelValue="buscar" style="width:140px" />
              <span class="hc-fecha-sep">—</span>
              <CustomDatePicker v-model="filtro.hasta" @update:modelValue="buscar" style="width:140px" />
            </div>
          </div>

          <div class="hc-btns-group">
            <button class="btn btn-outline-secondary hc-btn-hoy" @click="irHoy">
              <i class="bi bi-calendar-check"></i><span>Hoy</span>
            </button>
            <button class="btn btn-primary hc-btn-buscar" @click="buscar" :disabled="cargando">
              <i class="bi bi-search"></i><span>Buscar</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Totales ─────────────────────────────────────────────── -->
    <div v-if="!cargando && lista.length" class="hc-totales-bar">
      <span class="hc-total-chip">
        <span class="hc-total-lbl">{{ lista.length }} registros</span>
      </span>
      <span class="hc-total-chip hc-total-chip--green">
        <span class="hc-total-lbl">Total</span>
        <strong>{{ fmt(totalValor) }}</strong>
      </span>
      <span class="hc-total-chip hc-total-chip--blue" v-if="cntTipo('factura')">
        <span class="hc-total-lbl">Facturas</span>
        <strong>{{ cntTipo('factura') }}</strong>
      </span>
      <span class="hc-total-chip hc-total-chip--gray" v-if="cntTipo('recibo')">
        <span class="hc-total-lbl">Recibos</span>
        <strong>{{ cntTipo('recibo') }}</strong>
      </span>
    </div>

    <!-- ── Cuerpo (lista + detalle) ───────────────────────────── -->
    <div class="hc-body" :class="{ 'hc-has-sel': !!seleccionado }">

      <!-- Panel lista -->
      <div class="hc-panel-left card">
        <div v-if="cargando" class="hc-placeholder">
          <div class="spinner-border text-primary" style="width:2rem;height:2rem;"></div>
        </div>
        <div v-else-if="!lista.length" class="hc-placeholder text-muted">
          <i class="bi bi-receipt fs-2"></i>
          <p class="mt-2 mb-0">Sin resultados</p>
        </div>
        <div v-else class="hc-list">
          <div
            v-for="item in lista"
            :key="`${item.tipo}-${item.numero}`"
            class="hc-row"
            :class="{
              'hc-row--active': seleccionado?.numero === item.numero && seleccionado?.tipo === item.tipo,
              'hc-row--diff':   hasDiff(item),
            }"
            @click="seleccionar(item)"
          >
            <div class="hc-row-top">
              <span class="hc-folio">
                <span class="badge" :class="item.tipo === 'factura' ? 'bg-primary' : 'bg-secondary'">
                  {{ item.tipo === 'factura' ? 'FAC' : 'REC' }}
                </span>
                {{ item.numero }}
              </span>
              <span v-if="hasDiff(item)" class="hc-diff-badge" title="Diferencia entre facturado y comandado">
                <i class="bi bi-exclamation-triangle-fill"></i> DIFER.
              </span>
              <span class="hc-valor">{{ fmt(item.valor) }}</span>
            </div>
            <div class="hc-row-bot">
              <span class="hc-mesa"><i class="bi bi-table"></i> {{ item.mesa || '—' }}</span>
              <span class="hc-mesero text-muted" v-if="item.mesero">
                <i class="bi bi-person"></i> {{ item.mesero }}
              </span>
              <span class="hc-hora text-muted ms-auto">{{ item.hora }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Panel detalle comparación -->
      <div class="hc-panel-right card">

        <!-- Back (móvil) -->
        <div v-if="seleccionado" class="hc-back-bar">
          <button class="hc-btn-back" @click="volverLista">
            <i class="bi bi-arrow-left"></i> Lista
          </button>
          <span class="hc-back-title">
            <span class="badge" :class="seleccionado.tipo === 'factura' ? 'bg-primary' : 'bg-secondary'">
              {{ seleccionado.tipo === 'factura' ? 'FAC' : 'REC' }}
            </span>
            {{ seleccionado.numero }}
          </span>
        </div>

        <!-- Sin selección -->
        <div v-if="!seleccionado" class="hc-placeholder text-muted">
          <i class="bi bi-arrow-left-circle fs-2"></i>
          <p class="mt-2 mb-0">Selecciona un registro</p>
        </div>

        <!-- Detalle comparación -->
        <template v-else>
          <div class="hc-det-scroll">

            <!-- Header info -->
            <div class="hc-det-header">
              <div class="hc-det-title">
                <span class="badge" :class="seleccionado.tipo === 'factura' ? 'bg-primary' : 'bg-secondary'">
                  {{ seleccionado.tipo === 'factura' ? 'Factura' : 'Recibo' }}
                </span>
                <strong class="ms-2">{{ seleccionado.numero }}</strong>
              </div>
              <div class="hc-det-meta">
                <span><i class="bi bi-calendar3"></i> {{ seleccionado.date }}</span>
                <span><i class="bi bi-clock"></i> {{ seleccionado.hora }}</span>
                <span v-if="seleccionado.mesa"><i class="bi bi-table"></i> {{ seleccionado.mesa }}</span>
                <span v-if="seleccionado.mesero"><i class="bi bi-person"></i> {{ seleccionado.mesero }}</span>
                <span v-if="seleccionado.order_number" class="hc-order-ref">
                  <i class="bi bi-hash"></i> {{ seleccionado.order_number }}
                </span>
              </div>
              <div class="hc-det-valor">
                <span class="hc-det-valor-lbl">Total facturado</span>
                <strong>{{ fmt(seleccionado.valor) }}</strong>
              </div>
            </div>

            <!-- Banner diferencia -->
            <div v-if="hasDiff(seleccionado)" class="hc-diff-banner">
              <i class="bi bi-exclamation-triangle-fill me-2"></i>
              <strong>Diferencia detectada</strong> — los ítems facturados y comandados no coinciden
            </div>

            <!-- Comparación lado a lado -->
            <div class="hc-compare">

              <!-- Columna FACTURADO -->
              <div class="hc-col">
                <div class="hc-col__hdr hc-col__hdr--inv">
                  <i class="bi bi-file-earmark-check me-1"></i>
                  Facturado
                  <span class="hc-col__count">{{ seleccionado.invoiced_items.length }} ítems</span>
                </div>
                <div v-if="seleccionado.invoiced_items.length" class="hc-col__body">
                  <table class="hc-tbl">
                    <thead><tr>
                      <th>Plato</th>
                      <th class="text-center">Cant.</th>
                      <th class="text-end">Valor</th>
                    </tr></thead>
                    <tbody>
                      <tr v-for="it in seleccionado.invoiced_items" :key="it.item">
                        <td>{{ it.dish_name }}</td>
                        <td class="text-center">{{ it.quantity }}</td>
                        <td class="text-end">{{ fmt(it.valor) }}</td>
                      </tr>
                    </tbody>
                    <tfoot>
                      <tr>
                        <td colspan="2" class="text-end fw-bold small">Total</td>
                        <td class="text-end fw-bold">
                          {{ fmt(seleccionado.invoiced_items.reduce((s,i) => s+(i.valor||0), 0)) }}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
                <div v-else class="hc-col__empty">
                  <i class="bi bi-info-circle me-1"></i>Sin ítems facturados
                </div>
              </div>

              <!-- Columna COMANDADO -->
              <div class="hc-col">
                <div class="hc-col__hdr hc-col__hdr--cmd">
                  <i class="bi bi-receipt-cutoff me-1"></i>
                  Comandado
                  <span class="hc-col__count">{{ seleccionado.commanded_items.length }} ítems</span>
                </div>
                <div v-if="seleccionado.commanded_items.length" class="hc-col__body">
                  <table class="hc-tbl">
                    <thead><tr>
                      <th>Plato</th>
                      <th class="text-center">Cant.</th>
                      <th class="text-end">Valor</th>
                      <th>Novedad</th>
                    </tr></thead>
                    <tbody>
                      <tr v-for="it in seleccionado.commanded_items" :key="it.Item">
                        <td>{{ it.dish_name }}</td>
                        <td class="text-center">{{ it.Cantidad }}</td>
                        <td class="text-end">{{ fmt(it.Valor) }}</td>
                        <td class="text-muted small">{{ it.Novedad || '—' }}</td>
                      </tr>
                    </tbody>
                    <tfoot>
                      <tr>
                        <td colspan="2" class="text-end fw-bold small">Total</td>
                        <td class="text-end fw-bold">
                          {{ fmt(seleccionado.commanded_items.reduce((s,i) => s+(i.Valor||0), 0)) }}
                        </td>
                        <td></td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
                <div v-else class="hc-col__empty">
                  <i class="bi bi-info-circle me-1"></i>
                  Sin ítems comandados archivados.
                  Los ítems se archivan al ejecutar "Limpiar Temporales".
                </div>
              </div>

            </div>
          </div>
        </template>

      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/apis'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'

function localDate() {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Bogota' }).format(new Date())
}
const hoy = localDate()

function fmtFecha(iso) {
  if (!iso) return ''
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

const fmtCOP = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 })
const fmt = v => fmtCOP.format(v || 0)

const tipoOpts = [
  { value: 'ambos',   label: 'Ambos' },
  { value: 'factura', label: 'Facturas' },
  { value: 'recibo',  label: 'Recibos' },
]

const filtro         = ref({ tipo: 'ambos', desde: hoy, hasta: hoy })
const filtrosVisible = ref(true)
const lista          = ref([])
const cargando       = ref(false)
const seleccionado   = ref(null)

const totalValor  = computed(() => lista.value.reduce((s, r) => s + (r.valor || 0), 0))
const cntTipo     = t => lista.value.filter(r => r.tipo === t).length

async function buscar() {
  cargando.value    = true
  seleccionado.value = null
  lista.value       = []
  try {
    const { data } = await api.get('/api/pos/utilitarios/command-history', {
      params: { desde: filtro.value.desde, hasta: filtro.value.hasta, tipo: filtro.value.tipo },
    })
    lista.value = data.ventas || []
    if (lista.value.length) filtrosVisible.value = false
  } catch {
    // interceptor de auth lo maneja
  } finally {
    cargando.value = false
  }
}

function irHoy() {
  filtro.value.desde = localDate()
  filtro.value.hasta = localDate()
  buscar()
}

function hasDiff(item) {
  const inv = item?.invoiced_items  || []
  const cmd = item?.commanded_items || []
  if (!cmd.length || !inv.length) return false
  if (inv.length !== cmd.length) return true
  // Agrupar cantidades por dish_id
  const invMap = {}
  inv.forEach(i => { invMap[String(i.dish_id)] = (invMap[String(i.dish_id)] || 0) + parseFloat(i.quantity || 0) })
  const cmdMap = {}
  cmd.forEach(i => { cmdMap[String(i.Id_Plato)] = (cmdMap[String(i.Id_Plato)] || 0) + parseFloat(i.Cantidad || 0) })
  const allKeys = new Set([...Object.keys(invMap), ...Object.keys(cmdMap)])
  for (const k of allKeys) {
    if (Math.abs((invMap[k] || 0) - (cmdMap[k] || 0)) > 0.01) return true
  }
  return false
}

function seleccionar(item) {
  if (seleccionado.value?.numero === item.numero && seleccionado.value?.tipo === item.tipo) return
  seleccionado.value = item
}

function volverLista() {
  seleccionado.value = null
}

onMounted(buscar)
</script>

<style scoped>
.hc-wrap { display: flex; flex-direction: column; gap: 10px; padding: 12px; max-width: 1400px; margin: 0 auto; }

/* ── Filtros ── */
.hc-filters { border-radius: 10px; overflow: hidden; }
.hc-filters-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 14px; cursor: pointer; user-select: none;
}
.hc-filters-label { font-size: .88rem; font-weight: 600; display: flex; align-items: center; gap: 6px; }
.hc-filters-hint  { font-weight: 400; color: var(--bs-secondary-color); font-size: .82rem; }
.hc-chevron { font-size: .75rem; color: var(--bs-secondary-color); }
.hc-filters-body { padding: 0 14px 12px; border-top: 1px solid var(--bs-border-color); }

.hc-filter-row   { display: flex; flex-wrap: wrap; gap: 16px; align-items: flex-end; padding-top: 12px; }
.hc-filter-group { display: flex; flex-direction: column; gap: 4px; }
.hc-label        { font-size: .78rem; color: var(--bs-secondary-color); font-weight: 600; }
.hc-radios       { display: flex; gap: 14px; }
.hc-radio        { display: flex; align-items: center; gap: 5px; font-size: .85rem; cursor: pointer; }
.hc-fechas-row   { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.hc-fecha-sep    { color: var(--bs-secondary-color); }
.hc-btns-group   { display: flex; gap: 6px; align-items: center; }
.hc-btn-hoy, .hc-btn-buscar { display: flex; align-items: center; gap: 5px; }

/* ── Totales ── */
.hc-totales-bar { display: flex; flex-wrap: wrap; gap: 8px; }
.hc-total-chip  {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 14px; border-radius: 20px; font-size: .82rem;
  background: #f1f5f9; color: #334155;
}
.hc-total-lbl              { color: var(--bs-secondary-color); }
.hc-total-chip--green      { background: #d1fae5; color: #065f46; }
.hc-total-chip--blue       { background: #dbeafe; color: #1e40af; }
.hc-total-chip--gray       { background: #f3f4f6; color: #374151; }

/* ── Cuerpo ── */
.hc-body {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 10px;
  align-items: start;
}
.hc-panel-left, .hc-panel-right {
  border-radius: 10px; overflow: hidden;
  display: flex; flex-direction: column;
  position: sticky;
  top: 12px;
  max-height: calc(100vh - 200px);
  min-height: 200px;
}
.hc-panel-left  { overflow: hidden; }
.hc-panel-right { overflow: hidden; }

/* ── Placeholder ── */
.hc-placeholder {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center; padding: 32px;
}

/* ── Lista izquierda ── */
.hc-list { overflow-y: auto; flex: 1; }
.hc-row  { padding: 8px 12px; cursor: pointer; border-bottom: 1px solid var(--bs-border-color); transition: background .12s; }
.hc-row:hover       { background: rgba(59,130,246,.05); }
.hc-row--active     { background: #eff6ff; border-left: 3px solid #3b82f6; }
.hc-row--diff       { border-left: 3px solid #f59e0b; background: #fffbeb; }
.hc-row--diff.hc-row--active { background: #fef3c7; }
.hc-diff-badge {
  display: inline-flex; align-items: center; gap: 3px;
  font-size: .68rem; font-weight: 700; color: #92400e;
  background: #fef3c7; border: 1px solid #fcd34d;
  padding: 1px 6px; border-radius: 10px; white-space: nowrap;
}
.hc-diff-banner {
  background: #fef3c7; color: #92400e; border: 1px solid #fcd34d;
  padding: 8px 12px; border-radius: 8px; font-size: .84rem;
  display: flex; align-items: center;
}
.hc-row-top { display: flex; align-items: center; justify-content: space-between; gap: 6px; }
.hc-row-bot { display: flex; align-items: center; gap: 8px; margin-top: 3px; font-size: .78rem; }
.hc-folio   { display: flex; align-items: center; gap: 6px; font-size: .85rem; font-weight: 600; }
.hc-valor   { font-weight: 700; font-size: .9rem; }
.hc-mesa    { color: #475569; }
.hc-mesero  { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 120px; }
.hc-hora    { font-size: .75rem; white-space: nowrap; }

/* ── Panel derecho ── */
.hc-back-bar {
  display: none; align-items: center; gap: 10px;
  padding: 8px 12px; border-bottom: 1px solid var(--bs-border-color);
  background: #f8fafc;
}
.hc-btn-back { background: none; border: none; color: #3b82f6; font-size: .85rem; cursor: pointer; padding: 0; display: flex; align-items: center; gap: 4px; }
.hc-back-title { display: flex; align-items: center; gap: 6px; font-weight: 600; font-size: .88rem; }

.hc-det-scroll { flex: 1; overflow-y: auto; padding: 14px; display: flex; flex-direction: column; gap: 12px; }

.hc-det-header { display: flex; flex-direction: column; gap: 6px; }
.hc-det-title  { display: flex; align-items: center; gap: 6px; }
.hc-det-meta   { display: flex; flex-wrap: wrap; gap: 10px; font-size: .82rem; color: #475569; }
.hc-det-meta span { display: flex; align-items: center; gap: 4px; }
.hc-order-ref  { color: #94a3b8; }
.hc-det-valor  { display: flex; align-items: center; gap: 8px; font-size: .9rem; }
.hc-det-valor-lbl { color: var(--bs-secondary-color); font-size: .78rem; }

/* ── Comparación ── */
.hc-compare { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.hc-col { border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden; display: flex; flex-direction: column; }
.hc-col__hdr {
  padding: 7px 12px; font-size: .82rem; font-weight: 600;
  display: flex; align-items: center; gap: 4px; border-bottom: 1px solid #e2e8f0;
}
.hc-col__hdr--inv { background: #f0fdf4; color: #166534; border-color: #bbf7d0; }
.hc-col__hdr--cmd { background: #eff6ff; color: #1e40af; border-color: #bfdbfe; }
.hc-col__count    { margin-left: auto; font-weight: 400; font-size: .75rem; opacity: .8; }

.hc-col__body { flex: 1; }
.hc-col__empty {
  padding: 20px 12px; font-size: .82rem; color: #94a3b8;
  text-align: center; background: #fafafa; flex: 1; display: flex; align-items: center; justify-content: center; flex-direction: column; gap: 4px;
}

.hc-tbl { width: 100%; font-size: .82rem; border-collapse: collapse; }
.hc-tbl th { font-size: .75rem; color: var(--bs-secondary-color); padding: 5px 10px; border-bottom: 1px solid var(--bs-border-color); white-space: nowrap; background: #f8fafc; }
.hc-tbl td { padding: 5px 10px; border-bottom: 1px solid var(--bs-border-color); vertical-align: top; }
.hc-tbl tr:last-child td { border-bottom: none; }
.hc-tbl tfoot td { padding: 5px 10px; background: #f8fafc; font-size: .8rem; }

/* ── Responsive tablet ── */
@media (max-width: 768px) {
  .hc-body { grid-template-columns: 1fr; }
  .hc-panel-left { display: block; min-height: auto; max-height: 280px; overflow-y: auto; }
  .hc-panel-right { min-height: 400px; }
  .hc-back-bar { display: flex; }
  .hc-has-sel .hc-panel-left { display: none; }
  .hc-has-sel .hc-panel-right { display: flex; }
  .hc-compare { grid-template-columns: 1fr; }
  .hc-mesero { max-width: 80px; }
}

/* ── Responsive móvil ── */
@media (max-width: 576px) {
  .hc-wrap { padding: 8px; gap: 8px; }
  .hc-filter-row { flex-direction: column; align-items: stretch; }
  .hc-btns-group { justify-content: flex-end; }
  .hc-det-scroll { padding: 10px; }
  .hc-compare { gap: 8px; }
}
</style>
