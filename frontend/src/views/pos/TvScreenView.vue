<template>
  <div class="tv-root">

    <!-- ══════ CARGANDO ══════ -->
    <div v-if="state === 'loading'" class="tv-center">
      <div class="spinner-border text-primary" style="width:3rem;height:3rem;"></div>
      <p class="mt-3 tv-sub">Conectando pantalla…</p>
    </div>

    <!-- ══════ NO ENCONTRADA ══════ -->
    <div v-else-if="state === 'notfound'" class="tv-center">
      <i class="bi bi-x-octagon-fill tv-big-icon text-danger"></i>
      <h4 class="tv-title">Pantalla no encontrada</h4>
      <p class="tv-sub">El código de esta URL no existe o fue desactivado.</p>
    </div>

    <!-- ══════ PENDIENTE — ACTIVACIÓN ══════ -->
    <div v-else-if="state === 'pending'" class="tv-center">
      <i class="bi bi-tv tv-big-icon"></i>
      <h4 class="tv-title">{{ screenName || 'Pantalla de Cocina' }}</h4>
      <p class="tv-sub">Esta pantalla no está activada. Ingresa el código en el panel de administración.</p>

      <div class="tv-code-box">
        <div class="tv-code-label">Código de activación</div>
        <div class="tv-code-digits">
          <span v-for="(d, i) in activationCode" :key="i" class="tv-digit">{{ d }}</span>
        </div>
        <div class="tv-code-hint">
          Ve a <strong>Utilitarios → Pantallas TV</strong> e ingresa este código
        </div>
      </div>

      <div class="tv-countdown">
        <i class="bi bi-clock me-1"></i>Expira en {{ countdown }}
      </div>
    </div>

    <!-- ══════ COCINA ACTIVA ══════ -->
    <template v-else-if="state === 'active'">

      <!-- Topbar TV -->
      <div class="tv-topbar">
        <div class="tv-topbar__name">
          <i class="bi bi-tv-fill me-2"></i>{{ screenName }}
        </div>
        <div class="tv-topbar__clock">{{ clockStr }}</div>
      </div>

      <!-- Sin pedidos -->
      <div v-if="!sections.length || sections.every(s => !s.orders.length)" class="tv-center tv-center--active">
        <i class="bi bi-check2-circle tv-big-icon text-success"></i>
        <h4 class="tv-title">Sin pedidos pendientes</h4>
        <p class="tv-sub">La cocina está al día</p>
      </div>

      <!-- Secciones por impresora -->
      <div v-else class="tv-sections">
        <div v-for="sec in sections.filter(s => s.orders.length)" :key="sec.printer_id" class="tv-section">
          <div class="tv-section__header">
            <i class="bi bi-printer me-2"></i>{{ sec.printer_name }}
            <span class="tv-section__count">{{ sec.orders.length }} pedido{{ sec.orders.length !== 1 ? 's' : '' }}</span>
          </div>

          <div class="tv-cards-grid">
            <div v-for="card in sortedOrders(sec.orders)" :key="card.order_number + card.event_type"
                 class="tv-card"
                 :class="{
                   'tv-card--nuevo':     card.event_type === 'nuevo',
                   'tv-card--agregado':  card.event_type === 'agregado',
                   'tv-card--cancelado': card.event_type === 'cancelado',
                   'tv-card--reimpresion': card.event_type === 'reimpresion',
                 }">

              <!-- Badge evento + hora comanda -->
              <div class="tv-card__badge">
                <span class="evt-badge">
                  <i class="bi" :class="{
                    'bi-bell-fill':        card.event_type === 'nuevo',
                    'bi-plus-circle-fill': card.event_type === 'agregado',
                    'bi-x-circle-fill':    card.event_type === 'cancelado',
                    'bi-arrow-repeat':     card.event_type === 'reimpresion',
                  }"></i>
                  {{ evtLabel(card.event_type) }}
                  <span class="evt-hora" v-if="card.order_hora">⏱ {{ fmtHora(card.order_hora) }}</span>
                </span>
                <span class="tv-seq" v-if="card.daily_seq">#{{ card.daily_seq }}</span>
              </div>

              <!-- Mesa + tiempo transcurrido -->
              <div class="tv-card__mesa-row">
                <span class="tv-card__mesa">{{ card.table_name || '—' }}</span>
                <span v-if="card.latest_dish_time && elapsedStr(card.latest_dish_time)"
                      class="tv-elapsed" :class="elapsedClass(card.latest_dish_time)">
                  ⏱ {{ elapsedStr(card.latest_dish_time) }}
                </span>
              </div>
              <div class="tv-card__meta" v-if="card.waiter_name">
                <span><i class="bi bi-person me-1"></i>{{ card.waiter_name }}</span>
              </div>

              <!-- Ítems -->
              <ul class="tv-items">
                <li v-for="(it, idx) in card.items" :key="idx" class="tv-item">
                  <span class="tv-qty">{{ fmtQty(it.quantity) }}×</span>
                  <span class="tv-name">{{ it.dish_name }}</span>
                  <span v-if="it.notes" class="tv-notes">{{ it.notes }}</span>
                  <span v-if="it.changes" class="tv-changes">{{ it.changes }}</span>
                  <div v-if="it.assembly && it.assembly.length" class="tv-assembly">
                    <span v-for="a in it.assembly" :key="a.name" class="tv-asm-item">
                      · {{ a.name }}
                    </span>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

    </template>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'

const route    = useRoute()
const code     = route.params.code

const nowMs          = ref(Date.now())
const state          = ref('loading')
const screenName     = ref('')
const activationCode = ref([])
const pollToken      = ref('')
const deviceToken    = ref('')
const printerFilter  = ref([])
const sections       = ref([])
const clockStr       = ref('')
const countdown      = ref('10:00')
const expiresAt      = ref(null)

const LS_TOKEN = `tv_token_${code}`
const LS_POLL  = `tv_poll_${code}`

// ── Helpers ──────────────────────────────────────────────────────
function evtLabel(t) {
  return { nuevo: 'NUEVO', agregado: 'AGREGADO', cancelado: 'CANCELADO', reimpresion: 'REIMP.' }[t] || t.toUpperCase()
}

function elapsedMin(t) {
  nowMs.value  // dependencia reactiva — se recalcula cada segundo
  if (!t) return NaN
  const s = String(t)
  const m = s.match(/(\d{1,2}):(\d{2})/)
  if (!m) return NaN
  let h = parseInt(m[1])
  const min = parseInt(m[2])
  // VB6 puede guardar hora en formato 12h: "4:22:15 p.m." → sumar 12
  if (h < 12 && /p\.?\s*m\.?/i.test(s)) h += 12
  else if (h === 12 && /a\.?\s*m\.?/i.test(s)) h = 0
  const now = new Date()
  const orderSec = h * 3600 + min * 60
  const nowSec   = now.getHours() * 3600 + now.getMinutes() * 60
  let diff = Math.floor((nowSec - orderSec) / 60)
  if (diff < 0) diff += 1440
  return diff
}

function elapsedStr(t) {
  const d = elapsedMin(t)
  if (isNaN(d) || d < 0) return ''
  if (d < 1) return '< 1m'
  if (d < 60) return `${d}m`
  return `${Math.floor(d / 60)}h ${d % 60}m`
}

function elapsedClass(t) {
  const d = elapsedMin(t)
  if (isNaN(d)) return ''
  if (d >= 15) return 'tv-elapsed--red'
  if (d >= 10) return 'tv-elapsed--orange'
  return ''
}

function sortedOrders(orders) {
  return [...orders].sort((a, b) => {
    const ta = String(a.latest_dish_time || a.order_hora || '')
    const tb = String(b.latest_dish_time || b.order_hora || '')
    return tb > ta ? 1 : tb < ta ? -1 : 0
  })
}

function fmtHora(t) {
  if (!t) return ''
  const m = String(t).match(/(\d{1,2}:\d{2})/)
  return m ? m[1] : String(t).slice(0, 5)
}

function fmtQty(q) {
  const n = parseFloat(q)
  return Number.isInteger(n) ? n : n.toFixed(1)
}

// ── Audio engine ─────────────────────────────────────────────────
let _audioCtx = null
function unlockAudio() {
  try {
    if (!_audioCtx) _audioCtx = new (window.AudioContext || window.webkitAudioContext)()
    if (_audioCtx.state === 'suspended') _audioCtx.resume()
  } catch(e) {}
}
function _beep(freq, t0, dur, type, vol) {
  if (!_audioCtx) return
  try {
    const o = _audioCtx.createOscillator(), g = _audioCtx.createGain()
    o.connect(g); g.connect(_audioCtx.destination)
    o.type = type; o.frequency.value = freq
    const t = _audioCtx.currentTime + t0
    g.gain.setValueAtTime(vol, t)
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur)
    o.start(t); o.stop(t + dur + 0.05)
  } catch(e) {}
}
function playKitchenAlert(eventType) {
  unlockAudio()
  if (_audioCtx && _audioCtx.state === 'suspended') _audioCtx.resume()
  switch (eventType) {
    case 'nuevo':
      _beep(523, 0,    0.22, 'sine',      0.35)  // C5
      _beep(784, 0.2,  0.38, 'sine',      0.35)  // G5
      break
    case 'agregado':
      _beep(659, 0,    0.28, 'sine',      0.28)  // E5 suave
      break
    case 'cancelado':
      _beep(392, 0,    0.18, 'sawtooth',  0.18)  // G4 descendente
      _beep(262, 0.15, 0.32, 'sawtooth',  0.18)  // C4
      break
    case 'reimpresion':
      _beep(440, 0,    0.09, 'square',    0.17)  // A4 × 3
      _beep(440, 0.16, 0.09, 'square',    0.17)
      _beep(440, 0.32, 0.14, 'square',    0.17)
      break
  }
}

// ── Detección de tarjetas nuevas ─────────────────────────────────
const _knownKeys = new Set()
let _firstPoll = true
const _PRIORITY = ['cancelado', 'nuevo', 'agregado', 'reimpresion']
function _cardKey(c) { return `${c.order_number}|${c.latest_dish_time}|${c.event_type}` }
function detectAndAlert(allCards) {
  if (_firstPoll) {
    allCards.forEach(c => _knownKeys.add(_cardKey(c)))
    _firstPoll = false
    return
  }
  const newTypes = new Set()
  allCards.forEach(c => {
    const k = _cardKey(c)
    if (!_knownKeys.has(k)) { newTypes.add(c.event_type); _knownKeys.add(k) }
  })
  for (const et of _PRIORITY) {
    if (newTypes.has(et)) { playKitchenAlert(et); break }
  }
  const cur = new Set(allCards.map(_cardKey))
  _knownKeys.forEach(k => { if (!cur.has(k)) _knownKeys.delete(k) })
}

// ── Clock ─────────────────────────────────────────────────────────
function updateClock() {
  clockStr.value = new Date().toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function updateCountdown() {
  if (!expiresAt.value) return
  const secs = Math.max(0, Math.floor((expiresAt.value - Date.now()) / 1000))
  const m = Math.floor(secs / 60).toString().padStart(2, '0')
  const s = (secs % 60).toString().padStart(2, '0')
  countdown.value = `${m}:${s}`
  if (secs === 0) { localStorage.removeItem(LS_POLL); initPoll() }
}

// ── API ───────────────────────────────────────────────────────────
async function callInit() {
  const dt = localStorage.getItem(LS_TOKEN) || ''
  const pt = localStorage.getItem(LS_POLL)  || ''
  const params = new URLSearchParams({ device_token: dt, poll_token: pt })
  const res = await fetch(`/api/tv/${code}/init?${params}`)
  if (res.status === 404) { state.value = 'notfound'; return null }
  if (!res.ok) throw new Error('Error de red')
  return res.json()
}

async function fetchCards() {
  const dt = localStorage.getItem(LS_TOKEN) || deviceToken.value
  if (!dt) return
  const res = await fetch(`/api/tv/${code}/cards?device_token=${dt}`)
  if (res.status === 401) { localStorage.removeItem(LS_TOKEN); deviceToken.value = ''; initPoll(); return }
  if (!res.ok) return
  const data = await res.json()
  detectAndAlert(data.flatMap(s => s.orders || []))
  sections.value = data
}

// ── Flujo principal ───────────────────────────────────────────────
let timers = []

function clearTimers() { timers.forEach(clearInterval); timers = [] }

async function initPoll() {
  clearTimers()
  try {
    const data = await callInit()
    if (!data) return

    screenName.value = data.screen_name || ''

    if (data.status === 'active') {
      state.value = 'active'
      unlockAudio()
      printerFilter.value = data.printer_ids || []
      await fetchCards()
      timers.push(setInterval(fetchCards, 8000))
      timers.push(setInterval(() => { updateClock(); nowMs.value = Date.now() }, 1000))
      updateClock()

    } else if (data.status === 'just_activated') {
      localStorage.setItem(LS_TOKEN, data.device_token)
      localStorage.removeItem(LS_POLL)
      deviceToken.value = data.device_token
      initPoll()

    } else {
      // pending
      state.value = 'active' === state.value ? 'pending' : 'pending'
      state.value = 'pending'
      activationCode.value = (data.activation_code || '????').split('')
      if (data.poll_token) {
        pollToken.value = data.poll_token
        localStorage.setItem(LS_POLL, data.poll_token)
      }
      expiresAt.value = Date.now() + (data.expires_minutes || 10) * 60 * 1000
      timers.push(setInterval(updateCountdown, 1000))
      timers.push(setInterval(initPoll, 8000))
      updateCountdown()
    }
  } catch (e) {
    if (state.value === 'loading') state.value = 'notfound'
  }
}

onMounted(initPoll)
onUnmounted(clearTimers)
</script>

<style scoped>
.tv-root {
  min-height: 100vh;
  background: #0f172a;
  color: #f1f5f9;
  font-family: 'Segoe UI', system-ui, sans-serif;
  display: flex;
  flex-direction: column;
}

/* ── Centrado (loading / pending / not found) ── */
.tv-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px;
  text-align: center;
}
.tv-center--active { flex: 1; }

.tv-big-icon { font-size: 5rem; color: #94a3b8; margin-bottom: 16px; }
.tv-title    { font-size: 1.8rem; font-weight: 700; color: #f1f5f9; margin-bottom: 8px; }
.tv-sub      { font-size: 1rem; color: #94a3b8; margin-bottom: 0; }

/* ── Código de activación ── */
.tv-code-box {
  background: #1e293b;
  border: 2px solid #334155;
  border-radius: 16px;
  padding: 28px 40px;
  margin: 24px 0 16px;
  min-width: 320px;
}
.tv-code-label {
  font-size: .9rem;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 2px;
  margin-bottom: 16px;
}
.tv-code-digits {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-bottom: 16px;
}
.tv-digit {
  width: 64px;
  height: 80px;
  background: #0f172a;
  border: 2px solid #3b82f6;
  border-radius: 12px;
  font-size: 2.8rem;
  font-weight: 800;
  color: #60a5fa;
  display: flex;
  align-items: center;
  justify-content: center;
}
.tv-code-hint { font-size: .85rem; color: #64748b; }

.tv-countdown { font-size: .9rem; color: #64748b; }

/* ── Topbar activo ── */
.tv-topbar {
  background: #1e293b;
  border-bottom: 1px solid #334155;
  padding: 10px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.tv-topbar__name  { font-size: 1rem; font-weight: 700; color: #60a5fa; }
.tv-topbar__clock { font-size: 1rem; font-weight: 600; color: #94a3b8; font-variant-numeric: tabular-nums; }

/* ── Secciones ── */
.tv-sections {
  flex: 1;
  padding: 8px;
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 10px;
  overflow-y: auto;
}
.tv-section { flex: 1 1 0; min-width: 200px; }

.tv-section__header {
  display: flex;
  align-items: center;
  font-size: .8rem;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 6px;
}
.tv-section__count {
  margin-left: auto;
  background: #334155;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: .72rem;
}

/* ── Grid de tarjetas ── */
.tv-cards-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* ── Tarjeta ── */
.tv-card {
  background: #1e293b;
  border: 2px solid #334155;
  border-radius: 12px;
  padding: 6px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.tv-card--nuevo     { border-color: #22c55e; }
.tv-card--agregado  { border-color: #f59e0b; }
.tv-card--cancelado { border-color: #ef4444; background: #1c0f0f; }
.tv-card--reimpresion { border-color: #a78bfa; }

.tv-card__badge { display: flex; align-items: center; justify-content: space-between; }

.evt-badge {
  font-size: .68rem;
  font-weight: 800;
  letter-spacing: .5px;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: 20px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.evt-hora {
  font-weight: 700;
  font-size: .9rem;
  opacity: .9;
  margin-left: 3px;
  letter-spacing: 0;
}
.tv-card--nuevo     .evt-badge { background: #14532d; color: #4ade80; }
.tv-card--agregado  .evt-badge { background: #451a03; color: #fbbf24; }
.tv-card--cancelado .evt-badge { background: #450a0a; color: #f87171; }
.tv-card--reimpresion .evt-badge { background: #2e1065; color: #c4b5fd; }

.tv-seq { font-size: .7rem; color: #475569; }

.tv-card__mesa-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}
.tv-card__mesa {
  font-size: 1.35rem;
  font-weight: 800;
  color: #f1f5f9;
  line-height: 1;
}
.tv-elapsed {
  font-size: 1.35rem;
  font-weight: 700;
  color: #64748b;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0;
}
.tv-elapsed.tv-elapsed--orange { color: #fb923c; }
.tv-elapsed.tv-elapsed--red    { color: #f87171; }
.tv-card__meta {
  display: flex;
  gap: 10px;
  font-size: .75rem;
  color: #64748b;
  flex-wrap: wrap;
}

/* ── Ítems ── */
.tv-items {
  list-style: none;
  padding: 0;
  margin: 2px 0 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
  border-top: 1px solid #334155;
  padding-top: 4px;
}
.tv-item { display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px; font-size: .88rem; }
.tv-qty  { color: #60a5fa; font-weight: 700; white-space: nowrap; }
.tv-name { color: #f1f5f9; font-weight: 600; }
.tv-notes   { color: #fbbf24; font-size: .8rem; font-style: italic; }
.tv-changes { color: #a78bfa; font-size: .8rem; }
.tv-assembly { width: 100%; padding-left: 20px; }
.tv-asm-item { font-size: .78rem; color: #64748b; margin-right: 6px; }

/* ── Responsive ── */
@media (max-width: 768px) {
  .tv-cards-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); }
  .tv-card__mesa { font-size: 1.2rem; }
  .tv-digit { width: 50px; height: 60px; font-size: 2rem; }
  .tv-title { font-size: 1.4rem; }
}

@media (max-width: 576px) {
  .tv-sections { padding: 8px; gap: 10px; }
  .tv-cards-grid { grid-template-columns: 1fr 1fr; }
  .tv-topbar { padding: 8px 12px; }
  .tv-topbar__name  { font-size: .85rem; }
  .tv-topbar__clock { font-size: .85rem; }
  .tv-code-box { padding: 20px 16px; min-width: auto; width: 100%; }
  .tv-digit { width: 42px; height: 52px; font-size: 1.6rem; gap: 6px; }
}
</style>
