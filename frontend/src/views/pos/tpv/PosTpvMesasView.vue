<template>
  <div class="mesas-view">

    <!-- Barra secundaria: usuario + selector de zona (tab nueva) + cambiar usuario -->
    <div class="tpv-topbar">
      <div class="tpv-topbar__user">
        <i class="bi bi-person-circle me-2"></i>
        <span>{{ waiterName }}</span>
      </div>
      <button
        v-if="activeMainTab === 'nueva' && zonas.length"
        class="tpv-topbar__zone-btn"
        @click="zoneMenuOpen = true"
        title="Cambiar zona"
      >
        <i class="bi bi-grid-3x3-gap me-1"></i>
        <span>{{ currentZoneName }}</span>
        <i class="bi bi-chevron-down ms-1"></i>
      </button>
      <button class="tpv-topbar__switch" @click="cambiarUsuario" title="Cambiar usuario">
        <i class="bi bi-arrow-left-right me-1"></i>
        <span>Cambiar usuario</span>
      </button>
    </div>

    <!-- ═══ TAB: ABRIR CUENTA ════════════════════════════════════════ -->
    <template v-if="activeMainTab === 'nueva'">
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
          <button class="btn-abrir-primera mt-3" @click="setTab('nueva')">
            <i class="bi bi-plus-circle me-1"></i>Abrir primera cuenta
          </button>
        </div>

        <div v-else class="cuentas-circles">
          <button
            v-for="t in openOrders"
            :key="t.id"
            class="cuenta-circulo"
            :class="{ 'cuenta-circulo--bill': t.status === 'bill_requested' }"
            @click="goToOrder(t)"
          >
            <div class="cuenta-circulo__timer">
              <i class="bi bi-clock-fill me-1"></i>{{ t.order_time }}
            </div>
            <div class="cuenta-circulo__content">
              <span class="cuenta-circulo__name">{{ t.name }}</span>
              <span class="cuenta-circulo__valor-lbl">VALOR</span>
              <span class="cuenta-circulo__amount">{{ formatCurrency(t.amount || 0) }}</span>
            </div>
            <div class="cuenta-circulo__waiter">
              <i class="bi bi-person-fill me-1"></i>{{ t.waiter_name }}
            </div>
          </button>
        </div>

      </div>
    </template>

    <!-- Loading inicial -->
    <div v-if="loading && !zonas.length && activeMainTab === 'nueva'" class="mesas-loading">
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

    <!-- Drawer selector de zonas -->
    <div class="zone-overlay" v-if="zoneMenuOpen" @click.self="zoneMenuOpen = false">
      <div class="zone-drawer">
        <div class="zone-drawer__header">
          <span>Seleccionar zona</span>
          <button class="zone-drawer__close" @click="zoneMenuOpen = false">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>
        <div class="zone-drawer__list">
          <button
            v-for="z in zonas"
            :key="z.id"
            class="zone-drawer-item"
            :class="{ 'zone-drawer-item--active': activeZone === z.id }"
            @click="selectZone(z.id)"
          >
            <i :class="`bi ${z.icon || 'bi-grid-3x3-gap'}`" class="zone-drawer-item__icon"></i>
            <span class="zone-drawer-item__name">{{ z.name }}</span>
            <span class="zone-drawer-item__count">{{ countFree(z) }}/{{ z.tables.length }}</span>
            <i class="bi bi-check2 ms-auto" v-if="activeZone === z.id" style="color:#2563eb"></i>
          </button>
        </div>
      </div>
    </div>

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
const activeMainTab = ref('abiertas')
const zoneMenuOpen  = ref(false)

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

const currentZoneName = computed(() =>
  currentZone.value?.name || 'Zona'
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

function selectZone(zoneId) {
  activeZone.value = zoneId
  zoneMenuOpen.value = false
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
  if (route.query.tab === 'nueva') activeMainTab.value = 'nueva'
  // default ya es 'abiertas'
  await loadMesas()
  pollTimer = setInterval(loadMesas, 10000)
})

watch(() => route.query.tab, (tab) => {
  if (tab === 'abiertas' || tab === 'nueva') activeMainTab.value = tab
  else activeMainTab.value = 'abiertas'
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

/* ── Barra secundaria ── */
.tpv-topbar {
  display: flex;
  align-items: center;
  gap: 8px;
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
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tpv-topbar__zone-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  border: 1px solid #475569;
  border-radius: 8px;
  background: rgba(255,255,255,.08);
  color: #e2e8f0;
  font-size: .8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all .15s;
  touch-action: manipulation;
  max-width: 140px;
  flex-shrink: 0;
}
.tpv-topbar__zone-btn span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tpv-topbar__zone-btn:hover { border-color: #94a3b8; background: rgba(255,255,255,.15); }

.tpv-topbar__switch {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  border: 1px solid #475569;
  border-radius: 8px;
  background: transparent;
  color: #94a3b8;
  font-size: .78rem;
  font-weight: 600;
  cursor: pointer;
  transition: all .15s;
  touch-action: manipulation;
  flex-shrink: 0;
}
.tpv-topbar__switch:hover { border-color: #94a3b8; color: #e2e8f0; }

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

/* ── Cuentas abiertas: círculos ── */
.cuentas-body { flex: 1; overflow-y: auto; padding: 16px; }

.cuentas-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 240px;
}

.btn-abrir-primera {
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 10px;
  padding: 8px 18px;
  font-size: .88rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: background .15s;
}
.btn-abrir-primera:hover { background: #1d4ed8; }

.cuentas-circles {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 20px;
  justify-items: center;
}

.cuenta-circulo {
  width: min(180px, 100%);
  aspect-ratio: 1;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 30%, #fcd34d 0%, #d97706 55%, #92400e 100%);
  box-shadow: 0 8px 28px rgba(146,64,14,.45), inset 0 1px 0 rgba(255,255,255,.25);
  border: 3px solid rgba(253,211,77,.3);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: pointer;
  overflow: hidden;
  text-align: center;
  padding: 20px 10px;
  transition: transform .2s, box-shadow .2s;
  touch-action: manipulation;
}
.cuenta-circulo:hover { transform: scale(1.05); box-shadow: 0 12px 36px rgba(146,64,14,.6); }
.cuenta-circulo:active { transform: scale(.97); }

.cuenta-circulo--bill {
  background: radial-gradient(circle at 35% 30%, #fb923c 0%, #c2410c 55%, #7c2d12 100%);
  box-shadow: 0 8px 28px rgba(194,65,12,.45), inset 0 1px 0 rgba(255,255,255,.2);
}

.cuenta-circulo__timer {
  position: absolute;
  top: 17%;
  background: rgba(220,38,38,.9);
  color: #fff;
  font-size: .65rem;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 3px;
  white-space: nowrap;
}

.cuenta-circulo__content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1px;
  margin-top: 12px;
}

.cuenta-circulo__name {
  font-size: 1.05rem;
  font-weight: 800;
  color: #fff;
  text-shadow: 0 1px 4px rgba(0,0,0,.4);
  line-height: 1.1;
  word-break: break-word;
}

.cuenta-circulo__valor-lbl {
  font-size: .55rem;
  font-weight: 700;
  color: rgba(255,255,255,.75);
  letter-spacing: .08em;
  text-transform: uppercase;
  margin-top: 4px;
}

.cuenta-circulo__amount {
  font-size: .88rem;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0,0,0,.3);
}

.cuenta-circulo__waiter {
  position: absolute;
  bottom: 17%;
  font-size: .65rem;
  color: rgba(255,255,255,.92);
  font-weight: 600;
  background: rgba(0,0,0,.28);
  padding: 3px 10px;
  border-radius: 10px;
  max-width: 78%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── Drawer zonas ── */
.zone-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.5);
  z-index: 620;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

.zone-drawer {
  background: #fff;
  border-radius: 20px 20px 0 0;
  max-height: 70dvh;
  display: flex;
  flex-direction: column;
  animation: zoneSlideUp .25s ease;
}

@keyframes zoneSlideUp {
  from { transform: translateY(100%); }
  to   { transform: translateY(0); }
}

.zone-drawer__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 12px;
  border-bottom: 1px solid #e2e8f0;
  font-size: .95rem;
  font-weight: 700;
  color: #1e293b;
  flex-shrink: 0;
}

.zone-drawer__close {
  background: none;
  border: none;
  font-size: 1.1rem;
  color: #64748b;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
}
.zone-drawer__close:hover { background: #f1f5f9; }

.zone-drawer__list {
  overflow-y: auto;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.zone-drawer-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border: 2px solid transparent;
  border-radius: 12px;
  background: #f8fafc;
  cursor: pointer;
  touch-action: manipulation;
  text-align: left;
  width: 100%;
  transition: all .15s;
}
.zone-drawer-item:hover { background: #eff6ff; }
.zone-drawer-item--active { background: #dbeafe; border-color: #2563eb; }

.zone-drawer-item__icon { font-size: 1.15rem; color: #64748b; width: 24px; text-align: center; }
.zone-drawer-item--active .zone-drawer-item__icon { color: #2563eb; }

.zone-drawer-item__name { flex: 1; font-size: .9rem; font-weight: 600; color: #334155; }
.zone-drawer-item--active .zone-drawer-item__name { color: #1d4ed8; }

.zone-drawer-item__count {
  background: #e2e8f0;
  color: #475569;
  font-size: .72rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
}
.zone-drawer-item--active .zone-drawer-item__count { background: #bfdbfe; color: #1d4ed8; }

@media (max-width: 768px) {
  .mesas-grid { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px; }
}

@media (max-width: 576px) {
  .mesas-body { padding: 10px; }
  .mesas-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .mesa-card  { padding: 12px 8px; }
  .tpv-topbar__switch span { display: none; }
  .cuentas-circles { grid-template-columns: repeat(2, 1fr); gap: 14px; }
  .cuenta-circulo { width: min(150px, 100%); }
}
</style>
