<template>
  <div class="mesas-view">

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
          :class="`mesa-card--${t.status}`"
          @click="onTableClick(t)"
        >
          <div class="mesa-card__header">
            <span class="mesa-card__num">{{ t.name }}</span>
            <span class="mesa-card__seq" v-if="t.daily_seq">#{{ t.daily_seq }}</span>
          </div>
          <i class="bi mesa-card__icon"
            :class="{
              'bi-unlock-fill': t.status === 'free',
              'bi-people-fill': t.status === 'occupied',
              'bi-receipt': t.status === 'bill_requested',
            }"
          ></i>
          <div class="mesa-card__info" v-if="t.status !== 'free'">
            <span class="mesa-card__waiter">{{ t.waiter_name }}</span>
            <span class="mesa-card__time">{{ t.order_time }}</span>
            <span class="mesa-card__amount" v-if="t.amount">
              {{ formatCurrency(t.amount) }}
            </span>
          </div>
          <div class="mesa-card__status">
            <span v-if="t.status === 'free'">Disponible</span>
            <span v-else-if="t.status === 'bill_requested'">Solicitó cuenta</span>
            <span v-else>Ocupada</span>
          </div>
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="mesas-loading">
      <div class="spinner-border text-primary"></div>
      <p class="mt-3 text-muted">Cargando mesas...</p>
    </div>

    <!-- Modal abrir mesa -->
    <div class="modal-overlay" v-if="openingTable" @click.self="openingTable = null">
      <div class="open-modal">
        <h3 class="open-modal__title">
          <i class="bi bi-unlock-fill me-2 text-success"></i>
          Abrir {{ openingTable.name }}
        </h3>
        <div class="open-modal__field">
          <label class="form-label">Número de comensales</label>
          <div class="guests-control">
            <button class="guests-btn" @click="guests = Math.max(1, guests - 1)">
              <i class="bi bi-dash-lg"></i>
            </button>
            <span class="guests-value">{{ guests }}</span>
            <button class="guests-btn" @click="guests = Math.min(30, guests + 1)">
              <i class="bi bi-plus-lg"></i>
            </button>
          </div>
        </div>
        <div class="open-modal__actions">
          <button class="btn btn-outline-secondary" @click="openingTable = null">
            Cancelar
          </button>
          <button class="btn btn-success" @click="openTable" :disabled="opening">
            <span v-if="opening" class="spinner-border spinner-border-sm me-2"></span>
            Abrir Mesa
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import apiComanda from '@/services/apiComanda'

const router = useRouter()

const zonas      = ref([])
const loading    = ref(false)
const activeZone = ref(null)
const openingTable = ref(null)
const guests     = ref(2)
const opening    = ref(false)

let pollTimer = null

const currentZone = computed(() =>
  zonas.value.find(z => z.id === activeZone.value)
)

function countFree(zone) {
  return zone.tables.filter(t => t.status === 'free').length
}

function formatCurrency(v) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v)
}

onMounted(async () => {
  await loadMesas()
  pollTimer = setInterval(loadMesas, 10000)
})

onUnmounted(() => clearInterval(pollTimer))

async function loadMesas() {
  if (loading.value) return
  loading.value = true
  try {
    const res = await apiComanda.get('/api/pos/comanda/mesas')
    zonas.value = res.data
    if (!activeZone.value && res.data.length) activeZone.value = res.data[0].id
  } catch (e) {
    if (e.response?.status === 401) router.push('/pos/comanda/login')
  } finally {
    loading.value = false
  }
}

function _setCtx(tableId, tableName, waiterName) {
  const cid = localStorage.getItem('waiter_company_id')
  localStorage.setItem('pedido_ctx', JSON.stringify({
    table_id:    tableId,
    table_name:  tableName,
    waiter_name: waiterName || '',
    waiter_id:   0,
    company_id:  cid ? parseInt(cid) : 0,
  }))
}

function onTableClick(table) {
  if (table.status === 'free') {
    openingTable.value = table
    guests.value = 2
  } else {
    _setCtx(table.id, table.name, table.waiter_name)
    router.push(`/pos/comanda/pedido/${table.id}`)
  }
}

async function openTable() {
  if (opening.value) return
  opening.value = true
  try {
    const res = await apiComanda.post('/api/pos/comanda/mesa/abrir', {
      table_id:     openingTable.value.id,
      guests_count: guests.value,
    })
    const tid  = openingTable.value.id
    const name = openingTable.value.name
    _setCtx(tid, name, '')
    openingTable.value = null
    router.push(`/pos/comanda/pedido/${tid}`)
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al abrir la mesa')
  } finally {
    opening.value = false
  }
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

/* Mesa body */
.mesas-body {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
}

.mesas-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}

/* Mesa card */
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
.mesa-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,.1); }

.mesa-card--free {
  border-color: #bbf7d0;
  background: #f0fdf4;
}
.mesa-card--free .mesa-card__icon { color: #16a34a; }
.mesa-card--free .mesa-card__status { color: #16a34a; }

.mesa-card--occupied {
  border-color: #fecaca;
  background: #fff5f5;
}
.mesa-card--occupied .mesa-card__icon { color: #dc2626; }
.mesa-card--occupied .mesa-card__status { color: #dc2626; }

.mesa-card--bill_requested {
  border-color: #fde68a;
  background: #fffbeb;
}
.mesa-card--bill_requested .mesa-card__icon { color: #d97706; }
.mesa-card--bill_requested .mesa-card__status { color: #d97706; }

.mesa-card__header {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  justify-content: center;
}

.mesa-card__num {
  font-size: 1rem;
  font-weight: 700;
  color: #1e293b;
}

.mesa-card__seq {
  font-size: .7rem;
  font-weight: 700;
  background: #1e293b;
  color: #fff;
  padding: 1px 5px;
  border-radius: 6px;
}

.mesa-card__icon {
  font-size: 2rem;
}

.mesa-card__info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  width: 100%;
}

.mesa-card__waiter {
  font-size: .75rem;
  color: #475569;
  font-weight: 600;
}

.mesa-card__time {
  font-size: .7rem;
  color: #94a3b8;
}

.mesa-card__amount {
  font-size: .8rem;
  font-weight: 700;
  color: #1e293b;
}

.mesa-card__status {
  font-size: .75rem;
  font-weight: 700;
  margin-top: 4px;
}

/* Loading */
.mesas-loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

/* Modal overlay */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.open-modal {
  background: #fff;
  border-radius: 18px;
  padding: 28px 24px;
  width: 100%;
  max-width: 340px;
  box-shadow: 0 20px 60px rgba(0,0,0,.3);
}

.open-modal__title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 20px;
}

.open-modal__field {
  margin-bottom: 24px;
}

.guests-control {
  display: flex;
  align-items: center;
  gap: 20px;
  justify-content: center;
  margin-top: 8px;
}

.guests-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 2px solid #e2e8f0;
  background: #f8fafc;
  font-size: 1.2rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all .15s;
}
.guests-btn:hover { border-color: #2563eb; color: #2563eb; }

.guests-value {
  font-size: 2rem;
  font-weight: 700;
  color: #1e293b;
  min-width: 40px;
  text-align: center;
}

.open-modal__actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

/* Responsive */
@media (max-width: 768px) {
  .mesas-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 10px;
  }
}

@media (max-width: 576px) {
  .mesas-body { padding: 10px; }
  .mesas-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }
  .mesa-card { padding: 12px 8px; }
}
</style>
