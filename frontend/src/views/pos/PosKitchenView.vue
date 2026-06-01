<template>
  <div class="kitchen-view">

    <!-- ── Header TV ──────────────────────────────────────────────────────── -->
    <div class="kh">
      <div class="kh__brand">
        <i class="bi bi-display"></i>
        <span>Cocina</span>
      </div>
      <div class="kh__status">
        <span class="kh__dot" :class="connected ? 'kh__dot--ok' : 'kh__dot--err'"></span>
        {{ connected ? 'En línea' : 'Sin conexión' }}
      </div>
      <div class="kh__time">{{ currentTime }}</div>
    </div>

    <!-- ── Columnas por impresora ─────────────────────────────────────────── -->
    <div class="kcols" v-if="printers.length">
      <div
        v-for="(printer, idx) in printers"
        :key="printer.printer_id"
        class="kcol"
      >
        <!-- Cabecera de columna -->
        <div class="kcol__hdr">
          <i class="bi bi-printer-fill"></i>
          {{ printer.printer_name }}
          <span class="kcol__badge" v-if="printer.orders.length">
            {{ printer.orders.length }}
          </span>
        </div>

        <!-- Cuerpo con tarjetas -->
        <div class="kcol__body" :ref="el => setColBody(el, idx)">
          <div v-if="!printer.orders.length" class="kcol__empty">
            <i class="bi bi-check-circle-fill"></i>
            <p>Sin pedidos</p>
          </div>

          <div
            v-for="order in printer.orders"
            :key="order.order_number"
            class="kcard"
            :class="timeClass(order.latest_dish_time)"
          >
            <!-- Cabecera de la tarjeta -->
            <div class="kcard__hdr">
              <!-- Fila 1: nro + mesa + tiempo -->
              <div class="kcard__row1">
                <div class="kcard__ident">
                  <span class="kcard__seq">#{{ order.daily_seq }}</span>
                  <span class="kcard__mesa">{{ order.table_name }}</span>
                </div>
                <span
                  class="kcard__elapsed"
                  :class="timeClass(order.latest_dish_time)"
                >
                  <i class="bi bi-stopwatch-fill"></i>
                  {{ elapsed(order.latest_dish_time) || '0 min' }}
                </span>
              </div>
              <!-- Fila 2: mesero -->
              <div class="kcard__waiter">
                <i class="bi bi-person-fill"></i>
                {{ order.waiter_name || '—' }}
              </div>
            </div>

            <!-- Solicitud de cuenta -->
            <div class="kcard__bill" v-if="order.bill_requested">
              <i class="bi bi-receipt"></i> Solicitó cuenta
            </div>

            <!-- Lista de productos -->
            <div class="kcard__items">
              <div
                v-for="(item, idx) in order.items"
                :key="`${item.dish_id}-${item.item}`"
                class="kitem"
                :class="{ 'kitem--sep': idx > 0 }"
              >
                <div class="kitem__main">
                  <span class="kitem__qty">{{ item.quantity }}×</span>
                  <span class="kitem__name">{{ item.dish_name }}</span>
                </div>
                <!-- Armado/Assembly -->
                <div class="kitem__mods" v-if="item.assembly?.length">
                  <span
                    v-for="sel in item.assembly"
                    :key="sel.category_code"
                    class="kitem__mod"
                  >
                    <i class="bi bi-dot"></i>{{ sel.item_name }}
                  </span>
                </div>
                <!-- Notas -->
                <div class="kitem__note" v-if="item.notes">
                  <i class="bi bi-pencil-fill"></i> {{ item.notes }}
                </div>
                <!-- Cambios -->
                <div class="kitem__change" v-if="item.changes">
                  <i class="bi bi-arrow-left-right"></i> {{ item.changes }}
                </div>
              </div>
            </div>

          </div><!-- /kcard -->
        </div><!-- /kcol__body -->
      </div><!-- /kcol -->
    </div><!-- /kcols -->

    <!-- Sin impresoras activas -->
    <div v-else-if="!loading" class="kitchen-empty">
      <i class="bi bi-printer"></i>
      <h4>No hay impresoras configuradas</h4>
      <p>Active al menos una impresora en el panel de administración</p>
    </div>

    <div v-if="loading" class="kitchen-loading">
      <div class="spinner-border text-light spinner-border-sm"></div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, onBeforeUpdate } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const route     = useRoute()
const companyId = ref(route.query.cid || localStorage.getItem('waiter_company_id') || '')

const printers    = ref([])
const loading     = ref(false)
const connected   = ref(false)
const currentTime = ref('')
const now         = ref(new Date())

// ── Auto-scroll por columna ────────────────────────────────────────────────
const colBodies = []
let scrollRAF   = null

onBeforeUpdate(() => { colBodies.length = 0 })

function setColBody(el, idx) {
  if (el) colBodies[idx] = el
}

function stopAutoScroll() {
  if (scrollRAF) { cancelAnimationFrame(scrollRAF); scrollRAF = null }
}

function startAutoScroll() {
  stopAutoScroll()
  const states = colBodies.map(() => ({ dir: 1, pause: 0 }))
  let last = 0

  function tick(ts) {
    const dt = Math.min(ts - last, 100)  // cap delta a 100ms
    last = ts
    colBodies.forEach((col, i) => {
      if (!col) return
      const max = col.scrollHeight - col.clientHeight
      if (max < 8) return
      const s = states[i]
      s.pause = Math.max(0, s.pause - dt)
      if (s.pause > 0) return
      col.scrollTop += s.dir * 0.7
      if (col.scrollTop >= max - 1) {
        col.scrollTop = max
        s.dir = -1
        s.pause = 3000   // pausa 3 s al llegar al fondo
      } else if (col.scrollTop <= 1) {
        col.scrollTop = 0
        s.dir = 1
        s.pause = 1500   // pausa 1.5 s al volver al inicio
      }
    })
    scrollRAF = requestAnimationFrame(tick)
  }
  scrollRAF = requestAnimationFrame(tick)
}
// ──────────────────────────────────────────────────────────────────────────

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
  stopAutoScroll()
})

function updateClock() {
  now.value = new Date()
  currentTime.value = now.value.toLocaleTimeString('es-CO', {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
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
    await nextTick()
    startAutoScroll()
  }
}

function elapsed(t) {
  if (!t) return ''
  const sent = new Date(t.replace(' ', 'T'))
  const diff  = Math.floor((now.value - sent) / 60000)
  if (diff < 1) return '< 1 min'
  return `${diff} min`
}

function timeClass(t) {
  if (!t) return ''
  const sent = new Date(t.replace(' ', 'T'))
  const diff  = Math.floor((now.value - sent) / 60000)
  if (diff >= 15) return 'time--red'
  if (diff >= 10) return 'time--orange'
  return ''
}
</script>

<style scoped>
/* ══════════════════════════════════════════════════════════
   BASE — optimizado para pantalla TV en cocina
   ══════════════════════════════════════════════════════════ */
.kitchen-view {
  display: flex;
  flex-direction: column;
  height: 100dvh;
  background: #0f172a;
  color: #f1f5f9;
  overflow: hidden;
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
}

/* ── Header ──────────────────────────────────────────────── */
.kh {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 0 28px;
  height: 64px;
  background: #1e293b;
  border-bottom: 3px solid #2563eb;
  flex-shrink: 0;
}

.kh__brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1.5rem;
  font-weight: 800;
  color: #f1f5f9;
  letter-spacing: .5px;
}
.kh__brand i { font-size: 1.3rem; color: #60a5fa; }

.kh__status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  color: #94a3b8;
}

.kh__dot {
  width: 11px; height: 11px;
  border-radius: 50%;
  flex-shrink: 0;
}
.kh__dot--ok  { background: #22c55e; }
.kh__dot--err { background: #ef4444; animation: blink 1s infinite; }

@keyframes blink {
  0%, 100% { opacity: 1; }
  50%       { opacity: .25; }
}

.kh__time {
  margin-left: auto;
  font-size: 2rem;
  font-weight: 700;
  font-family: 'Courier New', monospace;
  color: #64748b;
  letter-spacing: 3px;
}

/* ── Columnas ────────────────────────────────────────────── */
.kcols {
  flex: 1;
  display: flex;
  overflow: hidden;
  background: #0a1120;
  gap: 2px;
}

.kcol {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #0f172a;
  min-width: 0;
  border-right: 1px solid #1e293b;
}
.kcol:last-child { border-right: none; }

.kcol__hdr {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
  background: #1e293b;
  font-size: 1.3rem;
  font-weight: 900;
  color: #60a5fa;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  border-bottom: 3px solid #2563eb;
  flex-shrink: 0;
}
.kcol__hdr i { font-size: 1.1rem; }

.kcol__badge {
  background: #2563eb;
  color: #fff;
  font-size: 1rem;
  font-weight: 800;
  padding: 2px 11px;
  border-radius: 14px;
  margin-left: auto;
}

.kcol__body {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  scrollbar-width: thin;
  scrollbar-color: #334155 transparent;
}

.kcol__empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  opacity: .4;
  color: #94a3b8;
}
.kcol__empty i  { font-size: 4rem; color: #22c55e; }
.kcol__empty p  { font-size: 1.2rem; margin: 0; }

/* ── Tarjeta ─────────────────────────────────────────────── */
.kcard {
  background: #1e293b;
  border: 2.5px solid #334155;
  border-radius: 16px;
  overflow: visible;        /* NO clipear el contenido */
  flex-shrink: 0;           /* nunca comprimir la tarjeta */
  transition: background .35s, border-color .35s, box-shadow .35s;
}
/* Estado orange: 10–14 min */
.kcard.time--orange {
  background: #431407;
  border-color: #ea580c;
}

/* Estado rojo: 15+ min */
.kcard.time--red {
  background: #3b0a0a;
  border-color: #dc2626;
  animation: urgent 2.5s ease-in-out infinite;
}
@keyframes urgent {
  0%, 100% { box-shadow: 0 0 0 0 rgba(220,38,38,0); }
  50%       { box-shadow: 0 0 0 8px rgba(220,38,38,.22); }
}

/* Cabecera de tarjeta */
.kcard__hdr {
  padding: 16px 18px 12px;
  background: rgba(0,0,0,.28);
  border-bottom: 1px solid rgba(255,255,255,.07);
  border-radius: 14px 14px 0 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.kcard__row1 {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.kcard__ident {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.kcard__seq {
  background: #f1f5f9;
  color: #0f172a;
  font-size: 1.15rem;
  font-weight: 900;
  padding: 4px 11px;
  border-radius: 8px;
  flex-shrink: 0;
  letter-spacing: .5px;
}

.kcard__mesa {
  font-size: 2.1rem;
  font-weight: 900;
  color: #f1f5f9;
  text-transform: uppercase;
  letter-spacing: .5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Badge tiempo transcurrido */
.kcard__elapsed {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 1.85rem;
  font-weight: 900;
  padding: 5px 16px;
  border-radius: 12px;
  background: rgba(34,197,94,.13);
  color: #4ade80;
  white-space: nowrap;
  font-family: 'Courier New', monospace;
  flex-shrink: 0;
}
.kcard__elapsed i { font-size: 1.4rem; }
.kcard__elapsed.time--orange {
  background: rgba(249,115,22,.18);
  color: #fb923c;
}
.kcard__elapsed.time--red {
  background: rgba(239,68,68,.18);
  color: #f87171;
}

/* Mesero */
.kcard__waiter {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 1.25rem;
  font-weight: 600;
  color: #cbd5e1;
}
.kcard__waiter i { font-size: 1.1rem; color: #94a3b8; }

/* Solicitud de cuenta */
.kcard__bill {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #92400e;
  color: #fef3c7;
  font-size: 1.15rem;
  font-weight: 700;
  padding: 7px 18px;
  letter-spacing: .5px;
}

/* ── Productos ───────────────────────────────────────────── */
.kcard__items {
  padding: 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.kitem { }
.kitem--sep {
  border-top: 1px solid rgba(255,255,255,.09);
  padding-top: 12px;
}

.kitem__main {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.kitem__qty {
  font-size: 1.55rem;
  font-weight: 900;
  color: #60a5fa;
  white-space: nowrap;
  min-width: 2.8rem;
  font-family: 'Courier New', monospace;
}

.kitem__name {
  font-size: 1.55rem;
  font-weight: 700;
  color: #f1f5f9;
  line-height: 1.2;
  text-transform: uppercase;
  letter-spacing: .3px;
}

/* Modificadores / Armado */
.kitem__mods {
  display: flex;
  flex-wrap: wrap;
  gap: 2px 0;
  margin-top: 6px;
  padding-left: 4rem;
}
.kitem__mod {
  display: flex;
  align-items: center;
  font-size: 1.05rem;
  color: #94a3b8;
  font-weight: 500;
}
.kitem__mod i { font-size: 1.3rem; }

/* Notas */
.kitem__note {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-top: 5px;
  padding-left: 4rem;
  font-size: 1rem;
  color: #94a3b8;
  font-style: italic;
}

/* Cambios */
.kitem__change {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-top: 5px;
  padding-left: 4rem;
  font-size: 1rem;
  color: #fbbf24;
  font-weight: 600;
}

/* ── Estado vacío / cargando ─────────────────────────────── */
.kitchen-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  color: #64748b;
}
.kitchen-empty i   { font-size: 5rem; }
.kitchen-empty h4  { font-size: 1.6rem; margin: 0; }
.kitchen-empty p   { font-size: 1.15rem; margin: 0; }

.kitchen-loading {
  position: fixed;
  top: 74px;
  right: 20px;
  opacity: .5;
}

/* ── Responsive tablet ───────────────────────────────────── */
@media (max-width: 768px) {
  .kh { height: 54px; padding: 0 16px; }
  .kh__brand  { font-size: 1.1rem; }
  .kh__time   { font-size: 1.4rem; }
  .kitchen-columns {
    overflow-x: auto;
    scroll-snap-type: x mandatory;
  }
  .kcol      { min-width: 310px; scroll-snap-align: start; }
  .kcard__mesa    { font-size: 1.5rem; }
  .kcard__elapsed { font-size: 1.3rem; }
  .kcard__waiter  { font-size: 1rem; }
  .kitem__qty, .kitem__name { font-size: 1.2rem; }
  .kitem__mod, .kitem__note, .kitem__change { font-size: .9rem; }
}

/* ── Responsive móvil ────────────────────────────────────── */
@media (max-width: 576px) {
  .kcol           { min-width: 270px; }
  .kcol__hdr      { font-size: 1rem; padding: 10px 14px; }
  .kcard__mesa    { font-size: 1.3rem; }
  .kcard__elapsed { font-size: 1.1rem; padding: 4px 10px; }
  .kcard__waiter  { font-size: .95rem; }
  .kitem__qty, .kitem__name { font-size: 1.1rem; }
  .kitem__mods, .kitem__note, .kitem__change { padding-left: 2.8rem; }
}
</style>
