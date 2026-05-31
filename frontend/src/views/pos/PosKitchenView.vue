<template>
  <div class="kitchen-view">

    <!-- Header TV -->
    <div class="kitchen-header">
      <div class="kitchen-header__brand">
        <i class="bi bi-display me-2"></i>
        <span>Cocina</span>
      </div>
      <div class="kitchen-header__time">{{ currentTime }}</div>
      <div class="kitchen-header__info">
        <span class="kitchen-header__dot" :class="connected ? 'kitchen-header__dot--ok' : 'kitchen-header__dot--err'"></span>
        {{ connected ? 'En línea' : 'Sin conexión' }}
      </div>
    </div>

    <!-- Columnas por impresora -->
    <div class="kitchen-columns" v-if="printers.length">
      <div
        v-for="printer in printers"
        :key="printer.printer_id"
        class="kitchen-col"
      >
        <div class="kitchen-col__header">
          <i class="bi bi-printer-fill me-2"></i>
          {{ printer.printer_name }}
          <span class="kitchen-col__count" v-if="printer.orders.length">
            {{ printer.orders.length }}
          </span>
        </div>

        <div class="kitchen-col__body">
          <div v-if="!printer.orders.length" class="kitchen-col__empty">
            <i class="bi bi-check-circle text-success fs-2"></i>
            <p class="text-muted small mt-2">Sin pedidos</p>
          </div>

          <div
            v-for="order in printer.orders"
            :key="order.order_number"
            class="kitchen-card"
            :class="timeClass(order.latest_dish_time)"
          >
            <!-- Card header con semáforo de tiempo -->
            <div class="kitchen-card__header" :class="timeClass(order.latest_dish_time)">
              <div class="kitchen-card__left">
                <span class="kitchen-card__seq">#{{ order.daily_seq }}</span>
                <span class="kitchen-card__mesa">{{ order.table_name }}</span>
              </div>
              <div class="kitchen-card__right">
                <span class="kitchen-card__waiter">{{ order.waiter_name }}</span>
                <span class="kitchen-card__time">{{ formatTime(order.order_time) }}</span>
                <span class="kitchen-card__elapsed" :class="timeClass(order.latest_dish_time)">
                  <i class="bi bi-stopwatch me-1"></i>
                  {{ elapsed(order.latest_dish_time) }}
                </span>
              </div>
            </div>

            <!-- Bill requested indicator -->
            <div class="kitchen-card__bill" v-if="order.bill_requested">
              <i class="bi bi-receipt me-1"></i>Solicitó cuenta
            </div>

            <!-- Items -->
            <div class="kitchen-card__items">
              <div
                v-for="(item, idx) in order.items"
                :key="`${item.dish_id}-${item.item}`"
                class="kitchen-item"
                :class="{ 'kitchen-item--sep': idx > 0 }"
              >
                <div class="kitchen-item__main">
                  <span class="kitchen-item__qty">{{ item.quantity }}×</span>
                  <span class="kitchen-item__name">{{ item.dish_name }}</span>
                </div>
                <!-- Assembly -->
                <div class="kitchen-item__assembly" v-if="item.assembly?.length">
                  <span
                    v-for="sel in item.assembly"
                    :key="sel.category_code"
                    class="kitchen-item__sel"
                  >
                    <i class="bi bi-dot"></i>{{ sel.item_name }}
                  </span>
                </div>
                <!-- Novedades -->
                <div class="kitchen-item__notes" v-if="item.notes">
                  <i class="bi bi-pencil-fill me-1"></i>{{ item.notes }}
                </div>
                <!-- Cambios -->
                <div class="kitchen-item__changes" v-if="item.changes">
                  <i class="bi bi-arrow-left-right me-1"></i>{{ item.changes }}
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>

    <!-- Sin impresoras / sin datos -->
    <div v-else-if="!loading" class="kitchen-empty">
      <i class="bi bi-printer text-muted" style="font-size:4rem"></i>
      <h4 class="text-muted mt-3">No hay impresoras configuradas</h4>
      <p class="text-muted">Configure impresoras en el panel de administración</p>
    </div>

    <div v-if="loading" class="kitchen-loading">
      <div class="spinner-border text-light spinner-border-sm"></div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const route  = useRoute()
const companyId = ref(route.query.cid || localStorage.getItem('waiter_company_id') || '')

const printers    = ref([])
const loading     = ref(false)
const connected   = ref(false)
const currentTime = ref('')
const now         = ref(new Date())

let pollTimer  = null
let clockTimer = null

onMounted(async () => {
  updateClock()
  clockTimer = setInterval(updateClock, 1000)
  await loadKitchen()
  pollTimer = setInterval(loadKitchen, 8000)
})

onUnmounted(() => {
  clearInterval(pollTimer)
  clearInterval(clockTimer)
})

function updateClock() {
  now.value = new Date()
  currentTime.value = now.value.toLocaleTimeString('es-CO', {
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  })
}

async function loadKitchen() {
  if (!companyId.value) return
  if (loading.value) return
  loading.value = true
  try {
    const base = import.meta.env.VITE_API_URL
    const res  = await axios.get(`${base}/api/pos/comanda/cocina?company_id=${companyId.value}`)
    printers.value = res.data
    connected.value = true
  } catch {
    connected.value = false
  } finally {
    loading.value = false
  }
}

function formatTime(t) {
  if (!t) return ''
  return t.substring(0, 5) // HH:MM
}

function elapsed(dishTime) {
  if (!dishTime) return ''
  const sent = new Date(dishTime.replace(' ', 'T'))
  const diff  = Math.floor((now.value - sent) / 60000)
  if (diff < 1) return '< 1 min'
  return `${diff} min`
}

function timeClass(dishTime) {
  if (!dishTime) return ''
  const sent = new Date(dishTime.replace(' ', 'T'))
  const diff  = Math.floor((now.value - sent) / 60000)
  if (diff >= 15) return 'time--red'
  if (diff >= 10) return 'time--orange'
  return ''
}
</script>

<style scoped>
.kitchen-view {
  display: flex;
  flex-direction: column;
  height: 100dvh;
  background: #0f172a;
  color: #f1f5f9;
  overflow: hidden;
  font-family: system-ui, -apple-system, sans-serif;
}

/* Header */
.kitchen-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 20px;
  height: 52px;
  background: #1e293b;
  border-bottom: 1px solid #334155;
  flex-shrink: 0;
}

.kitchen-header__brand {
  display: flex;
  align-items: center;
  font-size: 1rem;
  font-weight: 700;
  color: #f1f5f9;
}

.kitchen-header__time {
  font-size: 1.3rem;
  font-weight: 700;
  font-family: monospace;
  color: #94a3b8;
  margin-left: auto;
}

.kitchen-header__info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: .8rem;
  color: #64748b;
}

.kitchen-header__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.kitchen-header__dot--ok { background: #22c55e; }
.kitchen-header__dot--err { background: #ef4444; animation: pulse 1s infinite; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: .3; }
}

/* Columns */
.kitchen-columns {
  flex: 1;
  display: flex;
  overflow: hidden;
  gap: 1px;
  background: #1e293b;
}

.kitchen-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #0f172a;
  min-width: 0;
}

.kitchen-col__header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #1e293b;
  font-size: .85rem;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: .5px;
  border-bottom: 2px solid #2563eb;
  flex-shrink: 0;
}

.kitchen-col__count {
  background: #2563eb;
  color: #fff;
  font-size: .7rem;
  padding: 2px 7px;
  border-radius: 10px;
  margin-left: auto;
}

.kitchen-col__body {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  scrollbar-width: thin;
  scrollbar-color: #334155 transparent;
}

.kitchen-col__empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  opacity: .5;
}

/* Kitchen card */
.kitchen-card {
  background: #1e293b;
  border: 1.5px solid #334155;
  border-radius: 12px;
  overflow: hidden;
  transition: border-color .3s;
}
.kitchen-card.time--orange { border-color: #f59e0b; }
.kitchen-card.time--red    { border-color: #ef4444; }

/* Pulsing animation for urgent cards */
.kitchen-card.time--red {
  animation: urgentPulse 2s ease-in-out infinite;
}
@keyframes urgentPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0); }
  50%       { box-shadow: 0 0 0 4px rgba(239,68,68,.3); }
}

.kitchen-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 10px 12px 8px;
  background: #273549;
  gap: 8px;
}
.kitchen-card__header.time--orange { background: #451a03; }
.kitchen-card__header.time--red    { background: #450a0a; }

.kitchen-card__left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.kitchen-card__seq {
  background: #f1f5f9;
  color: #0f172a;
  font-size: .75rem;
  font-weight: 800;
  padding: 2px 7px;
  border-radius: 6px;
}

.kitchen-card__mesa {
  font-size: 1rem;
  font-weight: 700;
  color: #f1f5f9;
}

.kitchen-card__right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.kitchen-card__waiter {
  font-size: .72rem;
  color: #94a3b8;
}

.kitchen-card__time {
  font-size: .75rem;
  color: #64748b;
}

.kitchen-card__elapsed {
  font-size: .78rem;
  font-weight: 700;
  color: #22c55e;
}
.kitchen-card__elapsed.time--orange { color: #f59e0b; }
.kitchen-card__elapsed.time--red    { color: #ef4444; }

.kitchen-card__bill {
  background: #d97706;
  color: #fff;
  font-size: .72rem;
  font-weight: 700;
  padding: 3px 12px;
  text-align: center;
}

/* Items */
.kitchen-card__items {
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.kitchen-item { }
.kitchen-item--sep {
  border-top: 1px solid #1e293b;
  padding-top: 8px;
}

.kitchen-item__main {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.kitchen-item__qty {
  font-size: .85rem;
  font-weight: 700;
  color: #60a5fa;
  white-space: nowrap;
}

.kitchen-item__name {
  font-size: .9rem;
  font-weight: 700;
  color: #f1f5f9;
}

.kitchen-item__assembly {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
  padding-left: 20px;
}

.kitchen-item__sel {
  font-size: .75rem;
  color: #94a3b8;
  display: flex;
  align-items: center;
}

.kitchen-item__notes {
  margin-top: 4px;
  padding-left: 20px;
  font-size: .75rem;
  color: #94a3b8;
  font-style: italic;
}

.kitchen-item__changes {
  margin-top: 3px;
  padding-left: 20px;
  font-size: .75rem;
  color: #f59e0b;
  font-weight: 600;
}

/* Empty / loading */
.kitchen-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.kitchen-loading {
  position: fixed;
  top: 60px;
  right: 16px;
  opacity: .5;
}

/* Responsive */
@media (max-width: 768px) {
  .kitchen-columns {
    overflow-x: auto;
    scroll-snap-type: x mandatory;
  }
  .kitchen-col {
    min-width: 280px;
    scroll-snap-align: start;
  }
}

@media (max-width: 576px) {
  .kitchen-col { min-width: 260px; }
  .kitchen-col__body { padding: 8px; }
  .kitchen-card__header { padding: 8px 10px 6px; }
  .kitchen-card__items { padding: 8px 10px; }
}
</style>
