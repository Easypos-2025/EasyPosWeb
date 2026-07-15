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
          <AccountOrderCard
            v-for="t in openOrders"
            :key="t.id"
            :order="t"
            :card-style="cardStyle || 'circular-gold'"
            :show-delete="false"
            :editing-by="t.editing_by || null"
            @click="onOpenOrder(t)"
          />
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

    <!-- Modal advertencia lock de edición -->
    <div v-if="lockWarning" class="lock-modal-backdrop" @click.self="lockWarning = null">
      <div class="lock-modal">
        <i class="bi bi-pencil-square lock-modal__icon"></i>
        <p class="lock-modal__msg">
          <strong>{{ lockWarning.editing_by }}</strong> está editando este pedido ahora.
        </p>
        <p class="lock-modal__sub">¿Quieres entrar de todas formas?</p>
        <div class="lock-modal__btns">
          <button class="lock-modal__cancel" @click="lockWarning = null">Esperar</button>
          <button class="lock-modal__confirm" @click="goToOrder(lockWarning); lockWarning = null">Entrar</button>
        </div>
      </div>
    </div>

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
import AccountOrderCard from '@/components/comanda/AccountOrderCard.vue'
import { showToast } from '@/utils/toast'
import { useCardStyle } from '@/composables/useCardStyle'

const { cardStyle, load: loadCardStyle } = useCardStyle()

const router = useRouter()
const route  = useRoute()

const zonas         = ref([])
const loading       = ref(false)
const activeZone    = ref(null)
const openingId     = ref(null)
const detailTable   = ref(null)
const activeMainTab = ref('abiertas')
const zoneMenuOpen  = ref(false)
const lockWarning   = ref(null)

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

function onOpenOrder(table) {
  if (table.editing_by) {
    lockWarning.value = table
    return
  }
  goToOrder(table)
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
  const cid = localStorage.getItem('waiter_company_id') || undefined
  await Promise.all([loadMesas(), loadCardStyle(cid)])
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
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  justify-content: center;
  align-items: center;
  padding: 4px 0;
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
  .cuentas-circles { gap: 12px; }
}

/* ── Modal lock de edición ── */
.lock-modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(0,0,0,.55);
  z-index: 700;
  display: flex; align-items: center; justify-content: center;
  padding: 16px;
}
.lock-modal {
  background: #fff;
  border-radius: 18px;
  padding: 28px 24px 20px;
  max-width: 320px; width: 100%;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0,0,0,.3);
  animation: lockSlideIn .2s ease;
}
@keyframes lockSlideIn {
  from { transform: scale(.9); opacity: 0; }
  to   { transform: scale(1);  opacity: 1; }
}
.lock-modal__icon {
  font-size: 2.4rem;
  color: #7c3aed;
  display: block;
  margin-bottom: 12px;
}
.lock-modal__msg  { font-size: .95rem; color: #1e293b; margin: 0 0 4px; }
.lock-modal__sub  { font-size: .82rem; color: #64748b; margin: 0 0 20px; }
.lock-modal__btns { display: flex; gap: 10px; }
.lock-modal__cancel {
  flex: 1; padding: 10px; border: 2px solid #e2e8f0;
  border-radius: 10px; background: #f8fafc; color: #475569;
  font-weight: 600; cursor: pointer; font-size: .88rem;
}
.lock-modal__cancel:hover { background: #f1f5f9; }
.lock-modal__confirm {
  flex: 1; padding: 10px; border: none;
  border-radius: 10px; background: #7c3aed; color: #fff;
  font-weight: 700; cursor: pointer; font-size: .88rem;
}
.lock-modal__confirm:hover { background: #6d28d9; }
</style>
