<template>
  <div class="he-wrap">

    <!-- ── Filtros ─────────────────────────────────────────────── -->
    <div class="he-filters card">
      <div class="he-filters-head" @click="filtrosVisible = !filtrosVisible">
        <span class="he-filters-label">
          <i class="bi bi-funnel-fill me-1"></i>Filtros
          <span v-if="!filtrosVisible && lista.length" class="he-filters-hint">
            {{ filtros.desde }} — {{ filtros.hasta }}
          </span>
        </span>
        <i :class="filtrosVisible ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
      </div>

      <div v-show="filtrosVisible" class="he-filters-body">
        <div class="he-filter-row">
          <div class="he-filter-group">
            <label class="he-label">Desde</label>
            <input type="date" class="form-control he-input" v-model="filtros.desde" @change="buscar" />
          </div>
          <div class="he-filter-group">
            <label class="he-label">Hasta</label>
            <input type="date" class="form-control he-input" v-model="filtros.hasta" @change="buscar" />
          </div>
          <div class="he-filter-group">
            <label class="he-label">Mesa</label>
            <input type="text" class="form-control he-input" v-model="filtros.mesa"
              placeholder="Ej: M-09" @keyup.enter="buscar" />
          </div>
          <div class="he-filter-group">
            <label class="he-label">Eliminado por</label>
            <input type="text" class="form-control he-input" v-model="filtros.quien"
              placeholder="Nombre o ID" @keyup.enter="buscar" />
          </div>
          <div class="he-filter-btns">
            <button class="btn btn-outline-secondary btn-sm" @click="irHoy">
              <i class="bi bi-calendar-check"></i> Hoy
            </button>
            <button class="btn btn-primary btn-sm" @click="buscar" :disabled="cargando">
              <i class="bi bi-search"></i> Buscar
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Totalizador ─────────────────────────────────────────── -->
    <div v-if="lista.length" class="he-totals-bar">
      <span class="he-chip">
        <i class="bi bi-trash3 me-1"></i>
        <strong>{{ lista.length }}</strong> pedidos eliminados
      </span>
      <span class="he-chip he-chip--red">
        <i class="bi bi-cash-stack me-1"></i>
        <strong>{{ fmt(totalValor) }}</strong>
      </span>
      <span class="he-chip he-chip--blue">
        <i class="bi bi-bag me-1"></i>
        <strong>{{ totalItems }}</strong> ítems
      </span>
    </div>

    <!-- ── Cargando ─────────────────────────────────────────────── -->
    <div v-if="cargando" class="he-loading">
      <div class="spinner-border text-danger" style="width:2rem;height:2rem;"></div>
      <span class="ms-2 text-muted">Cargando...</span>
    </div>

    <!-- ── Sin resultados ──────────────────────────────────────── -->
    <div v-else-if="!cargando && !lista.length" class="he-empty">
      <i class="bi bi-inbox he-empty-icon"></i>
      <p class="he-empty-text">Sin pedidos eliminados en el período seleccionado</p>
    </div>

    <!-- ── Lista de pedidos eliminados ────────────────────────── -->
    <div v-else class="he-list">
      <div v-for="orden in lista" :key="orden.id"
        class="he-card card"
        :class="{ 'he-card--open': expandido === orden.id }">

        <!-- Cabecera de la tarjeta -->
        <div class="he-card-head" @click="toggle(orden.id)">
          <div class="he-card-left">
            <span class="he-badge-mesa">{{ orden.table_name || '—' }}</span>
            <span class="he-order-num">{{ orden.order_number }}</span>
            <span class="he-hora">{{ orden.time }}</span>
          </div>
          <div class="he-card-center">
            <div class="he-quien">
              <i class="bi bi-person-x-fill text-danger me-1"></i>
              <span>{{ orden.quien_elimino || 'Desconocido' }}</span>
            </div>
            <div v-if="orden.motivo_eliminacion" class="he-motivo">
              <i class="bi bi-chat-left-text me-1"></i>
              <em>{{ orden.motivo_eliminacion }}</em>
            </div>
          </div>
          <div class="he-card-right">
            <span class="he-valor">{{ fmt(orden.amount) }}</span>
            <span class="he-items-count">{{ orden.total_items }} ítem{{ orden.total_items !== 1 ? 's' : '' }}</span>
            <i :class="expandido === orden.id ? 'bi bi-chevron-up' : 'bi bi-chevron-down'" class="he-chevron"></i>
          </div>
        </div>

        <!-- Detalle expandible -->
        <div v-if="expandido === orden.id" class="he-detail">
          <div class="he-detail-meta">
            <span><i class="bi bi-calendar3 me-1"></i>{{ orden.date }}</span>
            <span v-if="orden.notes"><i class="bi bi-card-text me-1"></i>{{ orden.notes }}</span>
          </div>
          <table class="he-table">
            <thead>
              <tr>
                <th>ID Plato</th>
                <th>It.</th>
                <th class="text-end">Cant.</th>
                <th class="text-end">Valor</th>
                <th>Novedad</th>
                <th>Cambios</th>
                <th>Hora</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="it in orden.items" :key="`${it.dish_id}-${it.item}`"
                :class="{ 'he-row-cortesia': it.complimentary }">
                <td>
                  <span v-if="it.custom_product" class="he-custom">{{ it.custom_product }}</span>
                  <span v-else>{{ it.dish_id }}</span>
                </td>
                <td class="text-muted">{{ it.item }}</td>
                <td class="text-end">{{ it.quantity }}</td>
                <td class="text-end">{{ fmt(it.amount) }}</td>
                <td>{{ it.notes || '—' }}</td>
                <td>{{ it.changes || '—' }}</td>
                <td class="text-muted">{{ it.dish_time }}</td>
              </tr>
            </tbody>
          </table>
        </div>

      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/apis'

// ── State ──────────────────────────────────────────────────────
const hoy = new Date().toISOString().slice(0, 10)
const filtros = ref({ desde: hoy, hasta: hoy, mesa: '', quien: '' })
const lista = ref([])
const cargando = ref(false)
const filtrosVisible = ref(true)
const expandido = ref(null)

// ── Computed ───────────────────────────────────────────────────
const totalValor = computed(() => lista.value.reduce((s, o) => s + (o.amount || 0), 0))
const totalItems = computed(() => lista.value.reduce((s, o) => s + (o.total_items || 0), 0))

// ── Formatters ─────────────────────────────────────────────────
function fmt(val) {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  const cc   = user.currency_code || 'COP'
  const loc  = user.locale        || 'es-CO'
  return new Intl.NumberFormat(loc, { style: 'currency', currency: cc, maximumFractionDigits: 0 }).format(val || 0)
}

// ── Métodos ────────────────────────────────────────────────────
function irHoy() {
  filtros.value.desde = hoy
  filtros.value.hasta = hoy
  buscar()
}

function toggle(id) {
  expandido.value = expandido.value === id ? null : id
}

async function buscar() {
  cargando.value = true
  expandido.value = null
  try {
    const cid = JSON.parse(localStorage.getItem('user') || '{}').company_id
    const params = {
      fecha_desde: filtros.value.desde,
      fecha_hasta: filtros.value.hasta,
    }
    if (filtros.value.mesa)  params.mesa          = filtros.value.mesa
    if (filtros.value.quien) params.quien_elimino = filtros.value.quien

    const res = await api.get('/api/pos/comanda/historico-eliminadas', {
      params,
      headers: { 'X-Company-Id': cid },
    })
    lista.value = res.data.orders || []
  } catch (e) {
    console.error(e)
  } finally {
    cargando.value = false
  }
}

onMounted(() => buscar())
</script>

<style scoped>
.he-wrap { display: flex; flex-direction: column; gap: 12px; padding: 16px; max-width: 1200px; margin: 0 auto; }

/* ── Filtros ── */
.he-filters { border-radius: 10px; overflow: hidden; }
.he-filters-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; cursor: pointer; background: var(--bs-body-bg);
  font-weight: 600; color: var(--bs-emphasis-color);
}
.he-filters-hint { font-size: .8rem; color: var(--bs-secondary-color); margin-left: 8px; font-weight: 400; }
.he-filters-body { padding: 12px 16px 16px; }
.he-filter-row { display: flex; flex-wrap: wrap; gap: 12px; align-items: flex-end; }
.he-filter-group { display: flex; flex-direction: column; gap: 4px; }
.he-label { font-size: .78rem; color: var(--bs-secondary-color); font-weight: 600; }
.he-input { height: 36px; font-size: .88rem; }
.he-filter-btns { display: flex; gap: 8px; align-items: flex-end; padding-bottom: 1px; }

/* ── Totalizador ── */
.he-totals-bar { display: flex; flex-wrap: wrap; gap: 8px; }
.he-chip {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 6px 14px; border-radius: 20px; font-size: .85rem;
  background: #f1f5f9; color: #334155;
}
.he-chip--red  { background: #fee2e2; color: #991b1b; }
.he-chip--blue { background: #dbeafe; color: #1e40af; }

/* ── Loading / Empty ── */
.he-loading { display: flex; align-items: center; padding: 24px; }
.he-empty { display: flex; flex-direction: column; align-items: center; padding: 48px 16px; color: var(--bs-secondary-color); }
.he-empty-icon { font-size: 3rem; margin-bottom: 12px; }
.he-empty-text { font-size: 1rem; }

/* ── Lista ── */
.he-list { display: flex; flex-direction: column; gap: 8px; }

/* ── Tarjeta ── */
.he-card { border-radius: 10px; overflow: hidden; border: 1.5px solid var(--bs-border-color); }
.he-card--open { border-color: #ef4444; }

.he-card-head {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 14px; cursor: pointer;
  transition: background .15s;
}
.he-card-head:hover { background: rgba(239,68,68,.05); }

.he-card-left  { display: flex; align-items: center; gap: 10px; min-width: 0; }
.he-card-center { flex: 1; display: flex; flex-direction: column; gap: 2px; min-width: 0; padding: 0 8px; }
.he-card-right { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }

.he-badge-mesa {
  background: #ef4444; color: #fff;
  padding: 3px 10px; border-radius: 20px; font-size: .8rem; font-weight: 700; white-space: nowrap;
}
.he-order-num { font-size: .78rem; color: var(--bs-secondary-color); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 160px; }
.he-hora { font-size: .8rem; color: var(--bs-secondary-color); white-space: nowrap; }

.he-quien { font-size: .85rem; font-weight: 600; color: #ef4444; }
.he-motivo { font-size: .8rem; color: var(--bs-secondary-color); }

.he-valor { font-weight: 700; font-size: .95rem; color: var(--bs-emphasis-color); }
.he-items-count { font-size: .78rem; color: var(--bs-secondary-color); white-space: nowrap; }
.he-chevron { color: var(--bs-secondary-color); font-size: .8rem; }

/* ── Detalle expandido ── */
.he-detail { padding: 0 14px 14px; border-top: 1px solid var(--bs-border-color); }
.he-detail-meta {
  display: flex; gap: 16px; flex-wrap: wrap;
  font-size: .8rem; color: var(--bs-secondary-color);
  padding: 8px 0;
}
.he-table { width: 100%; font-size: .82rem; border-collapse: collapse; }
.he-table th { font-size: .75rem; color: var(--bs-secondary-color); padding: 4px 8px; border-bottom: 1px solid var(--bs-border-color); white-space: nowrap; }
.he-table td { padding: 5px 8px; border-bottom: 1px solid var(--bs-border-color); vertical-align: top; }
.he-table tr:last-child td { border-bottom: none; }
.he-row-cortesia td { color: #16a34a; background: #f0fdf4; }
.he-custom { font-style: italic; color: var(--bs-secondary-color); }

/* ── Responsive tablet ── */
@media (max-width: 768px) {
  .he-wrap { padding: 10px; gap: 10px; }
  .he-card-head { flex-wrap: wrap; gap: 8px; }
  .he-card-center { width: 100%; padding: 0; }
  .he-order-num { max-width: 120px; }
  .he-table { font-size: .78rem; }
  .he-table th:nth-child(5),
  .he-table td:nth-child(5),
  .he-table th:nth-child(6),
  .he-table td:nth-child(6) { display: none; }
}

/* ── Responsive móvil ── */
@media (max-width: 576px) {
  .he-filter-group { width: 100%; }
  .he-filter-btns  { width: 100%; justify-content: flex-end; }
  .he-card-right   { flex-wrap: wrap; gap: 4px; }
  .he-table th:nth-child(7),
  .he-table td:nth-child(7) { display: none; }
}
</style>
