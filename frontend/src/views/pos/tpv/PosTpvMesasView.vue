<template>
  <div class="mesas-view">

    <!-- Header: usuario logueado + cambiar usuario -->
    <div class="tpv-topbar">
      <div class="tpv-topbar__user">
        <i class="bi bi-person-circle me-2"></i>
        <span>{{ waiterName }}</span>
      </div>
      <button class="tpv-topbar__switch" @click="cambiarUsuario" title="Cambiar usuario">
        <i class="bi bi-arrow-left-right me-1"></i>
        Cambiar usuario
      </button>
    </div>

    <!-- Tabs principales: Abrir cuenta | Cuentas abiertas -->
    <div class="main-tabs">
      <button
        class="main-tab"
        :class="{ 'main-tab--active': activeMainTab === 'nueva' }"
        @click="setTab('nueva')"
      >
        <i class="bi bi-plus-circle me-1"></i>Abrir cuenta
      </button>
      <button
        class="main-tab"
        :class="{ 'main-tab--active': activeMainTab === 'abiertas' }"
        @click="setTab('abiertas')"
      >
        <i class="bi bi-list-ul me-1"></i>Cuentas abiertas
        <span class="main-tab__badge" v-if="openOrders.length">{{ openOrders.length }}</span>
      </button>
    </div>

    <!-- ═══ TAB: ABRIR CUENTA ════════════════════════════════════════ -->
    <template v-if="activeMainTab === 'nueva'">

      <!-- Tabs de zonas -->
      <div class="zona-tabs" v-if="zonas.length">
        <button
          v-for="z in zonas"
          :key="z.id"
          class="zona-tab"
          :class="{ 'zona-tab--active': activeZone === z.id }"
          @click="activeZone = z.id"
        >
          <i :class="`bi ${z.icon || 'bi-grid'} me-1`"></i>
          {{ z.name }}
          <span class="zona-tab__badge">{{ countFree(z) }}/{{ z.tables.length }}</span>
        </button>
      </div>

      <!-- Grid de mesas -->
      <div class="mesas-body" v-if="currentZone">
        <div class="mesas-grid">
          <button
            v-for="t in currentZone.tables"
            :key="t.id"
            class="mesa-card"
            :class="[`mesa-card--${t.status}`, { 'mesa-card--opening': openingId === t.id }]"
            @click="onTableClick(t)"
            :disabled="openingId === t.id"
          >
            <div class="mesa-card__header">
              <span class="mesa-card__num">{{ t.name }}</span>
              <span class="mesa-card__seq" v-if="t.daily_seq">#{{ t.daily_seq }}</span>
            </div>
            <span v-if="openingId === t.id" class="spinner-border spinner-border-sm mesa-card__icon text-success"></span>
            <i v-else class="bi mesa-card__icon"
              :class="{
                'bi-unlock-fill': t.status === 'free',
                'bi-people-fill': t.status === 'occupied',
                'bi-receipt':     t.status === 'bill_requested',
              }"
            ></i>
            <div class="mesa-card__info" v-if="t.status !== 'free'">
              <span class="mesa-card__waiter">{{ t.waiter_name }}</span>
              <span class="mesa-card__time">{{ t.order_time }}</span>
              <span class="mesa-card__amount" v-if="t.amount">{{ formatCurrency(t.amount) }}</span>
            </div>
            <div class="mesa-card__status">
              <span v-if="t.status === 'free'">Disponible</span>
              <span v-else-if="t.status === 'bill_requested'">Solicitó cuenta</span>
              <span v-else>Ocupada</span>
            </div>
          </button>
        </div>
      </div>

    </template>

    <!-- ═══ TAB: CUENTAS ABIERTAS ════════════════════════════════════ -->
    <template v-else>
      <div class="cuentas-body">

        <div v-if="loading && !zonas.length" class="cuentas-empty">
          <div class="spinner-border text-primary"></div>
        </div>

        <div v-else-if="!openOrders.length" class="cuentas-empty">
          <i class="bi bi-bag-check fs-1 text-muted"></i>
          <p class="text-muted mt-2">No hay cuentas abiertas</p>
        </div>

        <div v-else class="cuentas-list">
          <button
            v-for="t in openOrders"
            :key="t.id"
            class="cuenta-card"
            :class="`cuenta-card--${t.status}`"
            @click="goToOrder(t)"
          >
            <div class="cuenta-card__left">
              <span class="cuenta-card__name">{{ t.name }}</span>
              <span class="cuenta-card__zone">{{ t.zone_name }}</span>
            </div>
            <div class="cuenta-card__center">
              <span class="cuenta-card__waiter"><i class="bi bi-person-fill me-1"></i>{{ t.waiter_name }}</span>
              <span class="cuenta-card__time"><i class="bi bi-clock me-1"></i>{{ t.order_time }}</span>
            </div>
            <div class="cuenta-card__right">
              <span class="cuenta-card__amount">{{ formatCurrency(t.amount || 0) }}</span>
              <span class="cuenta-card__status-badge"
                :class="t.status === 'bill_requested' ? 'cuenta-badge--bill' : 'cuenta-badge--open'">
                {{ t.status === 'bill_requested' ? 'Cuenta' : 'En curso' }}
              </span>
            </div>
            <i class="bi bi-chevron-right cuenta-card__arrow"></i>
          </button>
        </div>

      </div>
    </template>

    <!-- Loading inicial (solo tab nueva) -->
    <div v-if="activeMainTab === 'nueva' && loading && !zonas.length" class="mesas-loading">
      <div class="spinner-border text-primary"></div>
      <p class="mt-3 text-muted">Cargando...</p>
    </div>

    <!-- Modal detalle pedido (solo tab nueva) -->
    <ComandaOrderDetailModal
      v-if="detailTable"
      :table="detailTable"
      @close="detailTable = null"
      @cancelled="onOrderCancelled"
    />

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import apiComanda from '@/services/apiComanda'
import ComandaOrderDetailModal from '@/components/comanda/ComandaOrderDetailModal.vue'
import { showToast } from '@/utils/toast'

const router = useRouter()
const route  = useRoute()

const zonas         = ref([])
const loading       = ref(false)
const activeZone    = ref(null)
const openingId     = ref(null)
const detailTable   = ref(null)
const activeMainTab = ref('nueva')

let pollTimer = null

const waiterName = computed(() => {
  try {
    const d = JSON.parse(localStorage.getItem('waiter_data') || '{}')
    return d.name || 'Usuario'
  } catch { return 'Usuario' }
})

const currentZone = computed(() =>
  zonas.value.find(z => z.id === activeZone.value)
)

const openOrders = computed(() =>
  zonas.value.flatMap(z =>
    z.tables
      .filter(t => t.status !== 'free')
      .map(t => ({ ...t, zone_name: z.name }))
  )
)

function setTab(tab) {
  activeMainTab.value = tab
}

function goToOrder(table) {
  _setCtx(table.id, table.name)
  router.push(`/pos/tpv/pedido/${table.id}`)
}

function countFree(zone) {
  return zone.tables.filter(t => t.status === 'free').length
}

function formatCurrency(v) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v)
}

onMounted(async () => {
  if (route.query.tab === 'abiertas') activeMainTab.value = 'abiertas'
  await loadMesas()
  pollTimer = setInterval(loadMesas, 10000)
})

watch(() => route.query.tab, (tab) => {
  if (tab === 'abiertas' || tab === 'nueva') activeMainTab.value = tab
})

onUnmounted(() => clearInterval(pollTimer))

function _todayStr() {
  return new Date().toISOString().slice(0, 10)
}

function _checkDateChange() {
  const loginDate = localStorage.getItem('waiter_login_date')
  if (loginDate && loginDate !== _todayStr()) {
    cambiarUsuario()
    return true
  }
  return false
}

async function loadMesas() {
  if (_checkDateChange()) return
  if (loading.value) return
  loading.value = true
  try {
    const res = await apiComanda.get('/api/pos/comanda/mesas')
    zonas.value = res.data
    if (!activeZone.value && res.data.length) activeZone.value = res.data[0].id
  } catch (e) {
    if (e.response?.status === 401) router.push('/pos/tpv/login')
  } finally {
    loading.value = false
  }
}

function _setCtx(tableId, tableName) {
  const cid = localStorage.getItem('waiter_company_id')
  const waiter = (() => { try { return JSON.parse(localStorage.getItem('waiter_data') || '{}') } catch { return {} } })()
  localStorage.setItem('pedido_ctx', JSON.stringify({
    table_id:    tableId,
    table_name:  tableName,
    waiter_name: waiter.name || '',
    waiter_id:   waiter.id   || 0,
    company_id:  cid ? parseInt(cid) : 0,
  }))
}

function onTableClick(table) {
  if (table.status === 'free') {
    openTable(table)
  } else {
    detailTable.value = table
  }
}

function onOrderCancelled() {
  detailTable.value = null
  loadMesas()
}

async function openTable(table) {
  if (openingId.value) return
  openingId.value = table.id
  try {
    await apiComanda.post('/api/pos/comanda/mesa/abrir', {
      table_id:     table.id,
      guests_count: 1,
    })
    _setCtx(table.id, table.name)
    router.push(`/pos/tpv/pedido/${table.id}`)
  } catch (e) {
    showToast(e.response?.data?.detail || 'Error al abrir la cuenta', 'error', 3000)
  } finally {
    openingId.value = null
  }
}

function cambiarUsuario() {
  localStorage.removeItem('waiter_token')
  localStorage.removeItem('waiter_data')
  localStorage.removeItem('waiter_login_date')
  router.push('/pos/tpv/login')
}
</script>

<style scoped>
.mesas-view {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* Topbar usuario */
.tpv-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  background: #1e293b;
  flex-shrink: 0;
}

.tpv-topbar__user {
  display: flex;
  align-items: center;
  color: #e2e8f0;
  font-size: .85rem;
  font-weight: 600;
}

.tpv-topbar__switch {
  display: flex;
  align-items: center;
  padding: 5px 12px;
  border: 1px solid #475569;
  border-radius: 8px;
  background: transparent;
  color: #94a3b8;
  font-size: .78rem;
  font-weight: 600;
  cursor: pointer;
  transition: all .15s;
  touch-action: manipulation;
}
.tpv-topbar__switch:hover { border-color: #94a3b8; color: #e2e8f0; }

/* Zona tabs */
.zona-tabs {
  display: flex;
  gap: 4px;
  padding: 10px 12px 0;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  overflow-x: auto;
  flex-shrink: 0;
  scrollbar-width: none;
}
.zona-tabs::-webkit-scrollbar { display: none; }

.zona-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: none;
  border-bottom: 3px solid transparent;
  background: none;
  color: #64748b;
  font-size: .875rem;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  transition: all .2s;
  border-radius: 8px 8px 0 0;
}
.zona-tab:hover { color: #1e293b; background: #f1f5f9; }
.zona-tab--active { color: #2563eb; border-bottom-color: #2563eb; }

.zona-tab__badge {
  background: #e2e8f0;
  color: #475569;
  font-size: .7rem;
  padding: 1px 6px;
  border-radius: 10px;
  font-weight: 700;
}
.zona-tab--active .zona-tab__badge { background: #dbeafe; color: #1d4ed8; }

/* Mesas */
.mesas-body { flex: 1; overflow-y: auto; padding: 14px; }

.mesas-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}

.mesa-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px 10px;
  border: 2px solid transparent;
  border-radius: 14px;
  cursor: pointer;
  transition: all .2s;
  text-align: center;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
}
.mesa-card:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,.1); }
.mesa-card:disabled { opacity: .7; cursor: not-allowed; }
.mesa-card--opening { border-color: #bbf7d0 !important; }

.mesa-card--free         { border-color: #bbf7d0; background: #f0fdf4; }
.mesa-card--free .mesa-card__icon   { color: #16a34a; }
.mesa-card--free .mesa-card__status { color: #16a34a; }

.mesa-card--occupied     { border-color: #fecaca; background: #fff5f5; }
.mesa-card--occupied .mesa-card__icon   { color: #dc2626; }
.mesa-card--occupied .mesa-card__status { color: #dc2626; }

.mesa-card--bill_requested { border-color: #fde68a; background: #fffbeb; }
.mesa-card--bill_requested .mesa-card__icon   { color: #d97706; }
.mesa-card--bill_requested .mesa-card__status { color: #d97706; }

.mesa-card__header { display: flex; align-items: center; gap: 6px; width: 100%; justify-content: center; }
.mesa-card__num    { font-size: 1rem; font-weight: 700; color: #1e293b; }
.mesa-card__seq    { font-size: .7rem; font-weight: 700; background: #1e293b; color: #fff; padding: 1px 5px; border-radius: 6px; }
.mesa-card__icon   { font-size: 2rem; }
.mesa-card__info   { display: flex; flex-direction: column; align-items: center; gap: 2px; width: 100%; }
.mesa-card__waiter { font-size: .75rem; color: #475569; font-weight: 600; }
.mesa-card__time   { font-size: .7rem; color: #94a3b8; }
.mesa-card__amount { font-size: .8rem; font-weight: 700; color: #1e293b; }
.mesa-card__status { font-size: .75rem; font-weight: 700; margin-top: 4px; }

.mesas-loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

/* ── Tabs principales ── */
.main-tabs {
  display: flex;
  background: #fff;
  border-bottom: 2px solid #e2e8f0;
  flex-shrink: 0;
}

.main-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 13px 8px;
  border: none;
  border-bottom: 3px solid transparent;
  margin-bottom: -2px;
  background: none;
  color: #64748b;
  font-size: .9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all .2s;
  touch-action: manipulation;
}
.main-tab:hover { color: #1e293b; background: #f8fafc; }
.main-tab--active { color: #2563eb; border-bottom-color: #2563eb; }

.main-tab__badge {
  background: #fee2e2;
  color: #dc2626;
  font-size: .7rem;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 10px;
  line-height: 1.4;
}
.main-tab--active .main-tab__badge { background: #dbeafe; color: #1d4ed8; }

/* ── Cuentas abiertas ── */
.cuentas-body { flex: 1; overflow-y: auto; padding: 12px; }

.cuentas-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
}

.cuentas-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cuenta-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 14px;
  background: #fff;
  cursor: pointer;
  text-align: left;
  width: 100%;
  transition: all .2s;
  box-shadow: 0 1px 4px rgba(0,0,0,.05);
  touch-action: manipulation;
}
.cuenta-card:hover { border-color: #2563eb; box-shadow: 0 4px 14px rgba(37,99,235,.12); transform: translateY(-1px); }
.cuenta-card:active { transform: scale(.99); }
.cuenta-card--bill_requested { border-color: #fde68a; background: #fffbeb; }
.cuenta-card--bill_requested:hover { border-color: #d97706; }

.cuenta-card__left {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 90px;
}
.cuenta-card__name {
  font-size: 1.05rem;
  font-weight: 700;
  color: #1e293b;
}
.cuenta-card__zone {
  font-size: .72rem;
  color: #94a3b8;
  font-weight: 500;
}

.cuenta-card__center {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.cuenta-card__waiter {
  font-size: .78rem;
  color: #475569;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.cuenta-card__time {
  font-size: .75rem;
  color: #94a3b8;
}

.cuenta-card__right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  flex-shrink: 0;
}
.cuenta-card__amount {
  font-size: .95rem;
  font-weight: 700;
  color: #1e293b;
  white-space: nowrap;
}
.cuenta-card__status-badge {
  font-size: .7rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
  white-space: nowrap;
}
.cuenta-badge--open { background: #fee2e2; color: #dc2626; }
.cuenta-badge--bill { background: #fef3c7; color: #d97706; }

.cuenta-card__arrow {
  color: #cbd5e1;
  font-size: .85rem;
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .mesas-grid { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px; }
}

@media (max-width: 576px) {
  .mesas-body { padding: 10px; }
  .mesas-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .mesa-card  { padding: 12px 8px; }
  .tpv-topbar__switch span { display: none; }
  .main-tab { font-size: .82rem; padding: 11px 6px; }
  .cuenta-card { padding: 12px; gap: 8px; }
  .cuenta-card__left { min-width: 70px; }
}
</style>
