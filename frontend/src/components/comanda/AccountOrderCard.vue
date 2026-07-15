<template>

  <!-- ═══ ESTILO: oval-wood (mesa elíptica de madera) ══════════════════════ -->
  <div v-if="cardStyle === 'oval-wood'" class="aoc-oval" @click="$emit('click')">
    <div class="aoc-oval__timer" :class="{ 'aoc-oval__timer--alert': isAlert }">
      <i class="bi bi-clock"></i>
      <span>{{ timeDisplay }}</span>
    </div>
    <button v-if="showDelete" class="aoc-oval__btn aoc-oval__btn--del"
      @click.stop="$emit('eliminar')" title="Eliminar pedido">
      <i class="bi bi-trash"></i>
    </button>
    <div class="aoc-oval__center">
      <span v-if="d.seq" class="aoc-oval__seq">#{{ d.seq }}</span>
      <div class="aoc-oval__name">{{ d.name }}</div>
      <div class="aoc-oval__valor-lbl">VALOR</div>
      <div class="aoc-oval__amount">{{ fmt(d.amount) }}</div>
    </div>
    <button v-if="showDelete" class="aoc-oval__btn aoc-oval__btn--fac"
      disabled @click.stop title="Facturar (próximamente)">
      <i class="bi bi-receipt"></i>
    </button>
    <div class="aoc-oval__waiter">
      <i class="bi bi-person-fill"></i>
      <span class="aoc-oval__waiter-txt">{{ d.waiterName }}</span>
    </div>
  </div>

  <!-- ═══ TODOS LOS DEMÁS ESTILOS (comparten estructura base) ══════════════ -->
  <button v-else
    class="aoc"
    :class="[`aoc--${cardStyle}`, { 'aoc--bill': d.billRequested }]"
    @click="$emit('click')"
  >
    <!-- Fila superior: timer + botón eliminar -->
    <div class="aoc__top">
      <span class="aoc__timer" :class="{ 'aoc__timer--alert': isAlert }">
        <i class="bi bi-clock-fill"></i>{{ timeDisplay }}
      </span>
      <button v-if="showDelete" class="aoc__del" @click.stop="$emit('eliminar')" title="Eliminar">
        <i class="bi bi-trash"></i>
      </button>
    </div>

    <!-- Cuerpo: seq + nombre + valor -->
    <div class="aoc__body">
      <span v-if="d.seq" class="aoc__seq">#{{ d.seq }}</span>
      <span class="aoc__name">{{ d.name }}</span>
      <span class="aoc__valor-lbl">VALOR</span>
      <span class="aoc__amount">{{ fmt(d.amount) }}</span>
    </div>

    <!-- Fila inferior: mesero -->
    <div class="aoc__bottom">
      <i class="bi bi-person-fill"></i>
      <span class="aoc__waiter-txt">{{ d.waiterName }}</span>
    </div>
  </button>

</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  order:      { type: Object,  required: true },
  cardStyle:  { type: String,  default: 'oval-wood' },
  showDelete: { type: Boolean, default: false },
  currency:   { type: String,  default: 'COP' },
})

defineEmits(['click', 'eliminar'])

/* ── Normalización: acepta datos de dashboard (hora_apertura/ocupada)
       y de comanda (order_time/status) ────────────────────────────── */
const d = computed(() => ({
  name:         props.order.name || '—',
  amount:       props.order.amount || 0,
  time:         props.order.order_time || props.order.hora_apertura || '',
  waiterName:   props.order.waiter_name || '—',
  seq:          props.order.daily_seq || null,
  billRequested: props.order.status === 'bill_requested',
}))

/* ── Hora formateada ─────────────────────────────────────────────── */
const timeDisplay = computed(() => {
  const t = d.value.time
  if (!t) return '—'
  return String(t).slice(0, 5)
})

/* ── Alerta si llevan más de 60 min ─────────────────────────────── */
const isAlert = computed(() => {
  const t = d.value.time
  if (!t) return false
  try {
    const [h, m] = String(t).split(':').map(Number)
    const now  = new Date()
    const open = new Date(now)
    open.setHours(h, m, 0, 0)
    if (open > now) open.setDate(open.getDate() - 1)
    return (now - open) > 60 * 60 * 1000
  } catch { return false }
})

/* ── Formato moneda ──────────────────────────────────────────────── */
const fmtCache = {}
function fmt(v) {
  if (!fmtCache[props.currency]) {
    fmtCache[props.currency] = new Intl.NumberFormat('es-CO', {
      style: 'currency', currency: props.currency,
      minimumFractionDigits: 0, maximumFractionDigits: 0,
    })
  }
  return fmtCache[props.currency].format(v || 0)
}
</script>

<style scoped>

/* ══════════════════════════════════════════════════════════════════
   ESTILO 1: oval-wood
   (óvalo elíptico con textura de mesa de madera)
   Idéntico a MesaTableCard pero unificado aquí.
══════════════════════════════════════════════════════════════════ */
.aoc-oval {
  position: relative;
  width: 185px;
  height: 145px;
  border-radius: 50%;
  background: radial-gradient(ellipse at 42% 36%,
    #f5d48a 0%, #d4912c 46%, #a05c14 76%, #6e3a08 100%);
  border: 3px solid #5a3008;
  box-shadow:
    0 16px 42px rgba(0,0,0,.42),
    0 5px 12px rgba(0,0,0,.22),
    inset 0 3px 10px rgba(255,220,120,.28),
    inset 0 -2px 7px rgba(0,0,0,.22);
  overflow: hidden;
  cursor: pointer;
  flex: 0 0 auto;
  transition: transform .2s, box-shadow .2s;
}
.aoc-oval:hover {
  transform: translateY(-5px) scale(1.04);
  box-shadow:
    0 24px 52px rgba(0,0,0,.52),
    0 8px 18px rgba(0,0,0,.28),
    inset 0 4px 12px rgba(255,220,120,.32),
    inset 0 -2px 7px rgba(0,0,0,.22);
}

.aoc-oval__center {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 95px;
  text-align: center;
  pointer-events: none;
  z-index: 1;
}
.aoc-oval__seq        { font-size: 8px; font-weight: 700; color: rgba(255,220,120,.65); line-height: 1.2; letter-spacing: .4px; }
.aoc-oval__name       { font-size: 17px; font-weight: 900; color: #fff; text-shadow: 0 2px 6px rgba(0,0,0,.75); line-height: 1.1; word-break: break-word; }
.aoc-oval__valor-lbl  { font-size: 7px; font-weight: 700; color: #fde68a; text-transform: uppercase; letter-spacing: .8px; margin-top: 4px; }
.aoc-oval__amount     { font-size: 11px; font-weight: 800; color: #86efac; text-shadow: 0 1px 4px rgba(0,0,0,.6); }

.aoc-oval__timer {
  position: absolute;
  top: 11px; left: 50%;
  transform: translateX(-50%);
  display: flex; align-items: center; gap: 3px;
  background: rgba(0,0,0,.48); color: #e2e8f0;
  font-size: 9px; font-weight: 700;
  padding: 3px 9px; border-radius: 10px;
  white-space: nowrap; backdrop-filter: blur(2px);
  z-index: 2;
}
.aoc-oval__timer--alert {
  background: rgba(185,0,0,.72); color: #fca5a5;
  animation: aoc-pulse 1.5s ease-in-out infinite;
}
@keyframes aoc-pulse {
  0%,100% { box-shadow: 0 0 0 rgba(220,38,38,.4); }
  50%      { box-shadow: 0 0 12px rgba(220,38,38,.85); }
}

.aoc-oval__waiter {
  position: absolute;
  bottom: 11px; left: 50%;
  transform: translateX(-50%);
  display: flex; align-items: center; gap: 3px;
  background: rgba(0,0,0,.48); color: #e2e8f0;
  font-size: 9px; font-weight: 700;
  padding: 3px 9px; border-radius: 10px;
  white-space: nowrap; z-index: 2;
}
.aoc-oval__waiter-txt { overflow: hidden; text-overflow: ellipsis; max-width: 72px; }

.aoc-oval__btn {
  position: absolute;
  width: 30px; height: 30px;
  border-radius: 50%; font-size: 12px;
  cursor: pointer; top: 50%;
  transform: translateY(-50%);
  display: flex; align-items: center; justify-content: center;
  transition: background .15s, transform .15s;
  z-index: 2;
}
.aoc-oval__btn--del  { left: 12px; background: rgba(200,30,30,.3); color: #fca5a5; border: 1.5px solid rgba(220,38,38,.45); }
.aoc-oval__btn--del:hover { background: rgba(200,30,30,.75); color: #fff; transform: translateY(-50%) scale(1.18); }
.aoc-oval__btn--fac  { right: 12px; background: rgba(20,150,70,.22); color: #86efac; border: 1.5px solid rgba(22,163,74,.4); }
.aoc-oval__btn--fac:disabled { opacity: .38; cursor: not-allowed; }

/* ── oval-wood responsive ── */
@media (min-width: 577px) and (max-width: 768px) {
  .aoc-oval { width: 210px; height: 165px; }
  .aoc-oval__name { font-size: 20px; }
  .aoc-oval__amount { font-size: 13px; }
  .aoc-oval__center { width: 110px; }
  .aoc-oval__timer, .aoc-oval__waiter { font-size: 10px; padding: 4px 11px; }
  .aoc-oval__timer { top: 13px; }
  .aoc-oval__waiter { bottom: 13px; }
  .aoc-oval__btn { width: 34px; height: 34px; font-size: 13px; }
  .aoc-oval__btn--del { left: 14px; }
  .aoc-oval__btn--fac { right: 14px; }
  .aoc-oval__waiter-txt { max-width: 84px; }
}
@media (min-width: 769px) {
  .aoc-oval { width: 240px; height: 190px; }
  .aoc-oval__name { font-size: 24px; }
  .aoc-oval__amount { font-size: 15px; }
  .aoc-oval__valor-lbl { font-size: 8px; }
  .aoc-oval__center { width: 128px; }
  .aoc-oval__timer, .aoc-oval__waiter { font-size: 11px; padding: 5px 13px; }
  .aoc-oval__timer { top: 16px; }
  .aoc-oval__waiter { bottom: 16px; }
  .aoc-oval__btn { width: 38px; height: 38px; font-size: 15px; }
  .aoc-oval__btn--del { left: 16px; }
  .aoc-oval__btn--fac { right: 16px; }
  .aoc-oval__waiter-txt { max-width: 100px; }
}


/* ══════════════════════════════════════════════════════════════════
   BASE COMPARTIDA (estilos 2-6)
══════════════════════════════════════════════════════════════════ */
.aoc {
  display: flex;
  flex-direction: column;
  gap: 0;
  border: none;
  cursor: pointer;
  text-align: left;
  touch-action: manipulation;
  transition: transform .18s, box-shadow .18s;
  overflow: hidden;
  position: relative;
  width: 160px;
}
.aoc:hover  { transform: translateY(-3px); }
.aoc:active { transform: scale(.97); }

.aoc__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px 4px;
  flex-shrink: 0;
}
.aoc__timer {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: .65rem; font-weight: 700;
  padding: 3px 8px; border-radius: 10px;
  white-space: nowrap;
}
.aoc__timer--alert { animation: aoc-pulse 1.5s ease-in-out infinite; }

.aoc__del {
  background: rgba(220,38,38,.15);
  color: #ef4444;
  border: 1px solid rgba(220,38,38,.3);
  border-radius: 6px;
  width: 24px; height: 24px;
  display: flex; align-items: center; justify-content: center;
  font-size: .7rem; cursor: pointer; flex-shrink: 0;
  transition: background .15s;
}
.aoc__del:hover { background: rgba(220,38,38,.5); color: #fff; }

.aoc__body {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4px 10px 6px;
  text-align: center;
}
.aoc__seq       { font-size: .6rem; font-weight: 700; opacity: .6; }
.aoc__name      { font-size: 1rem; font-weight: 800; line-height: 1.1; word-break: break-word; }
.aoc__valor-lbl { font-size: .5rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; margin-top: 4px; opacity: .75; }
.aoc__amount    { font-size: .8rem; font-weight: 700; }

.aoc__bottom {
  display: flex; align-items: center; gap: 4px;
  padding: 4px 10px 7px;
  font-size: .65rem; font-weight: 600;
  flex-shrink: 0;
}
.aoc__waiter-txt { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }


/* ══════════════════════════════════════════════════════════════════
   ESTILO 2: circular-gold
   (círculo con gradiente dorado/amber)
══════════════════════════════════════════════════════════════════ */
.aoc--circular-gold {
  width: 170px;
  aspect-ratio: 1;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 30%, #fcd34d 0%, #d97706 55%, #92400e 100%);
  box-shadow: 0 8px 28px rgba(146,64,14,.45), inset 0 1px 0 rgba(255,255,255,.25);
  border: 3px solid rgba(253,211,77,.3);
  align-items: center;
  justify-content: center;
}
.aoc--circular-gold.aoc--bill {
  background: radial-gradient(circle at 35% 30%, #fb923c 0%, #c2410c 55%, #7c2d12 100%);
  box-shadow: 0 8px 28px rgba(194,65,12,.45), inset 0 1px 0 rgba(255,255,255,.2);
}
.aoc--circular-gold:hover { box-shadow: 0 12px 36px rgba(146,64,14,.6); }

.aoc--circular-gold .aoc__top {
  position: absolute; top: 18%; left: 0; right: 0;
  padding: 0; justify-content: center;
  background: none;
}
.aoc--circular-gold .aoc__timer {
  background: rgba(220,38,38,.88); color: #fff;
}
.aoc--circular-gold .aoc__del { display: none; }

.aoc--circular-gold .aoc__body  { margin-top: 14px; background: none; }
.aoc--circular-gold .aoc__seq   { color: rgba(255,255,255,.65); }
.aoc--circular-gold .aoc__name  { color: #fff; text-shadow: 0 1px 4px rgba(0,0,0,.4); font-size: 1.05rem; }
.aoc--circular-gold .aoc__valor-lbl { color: rgba(255,255,255,.75); }
.aoc--circular-gold .aoc__amount    { color: #fff; text-shadow: 0 1px 2px rgba(0,0,0,.3); }

.aoc--circular-gold .aoc__bottom {
  position: absolute; bottom: 17%; left: 0; right: 0;
  justify-content: center; padding: 0;
  color: rgba(255,255,255,.92);
  background: none;
}
.aoc--circular-gold .aoc__bottom > * {
  background: rgba(0,0,0,.28);
  padding: 3px 10px; border-radius: 10px;
  max-width: 78%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}


/* ══════════════════════════════════════════════════════════════════
   ESTILO 3: checkered
   (mantel cuadros rojo/blanco — pizzería / italiano)
══════════════════════════════════════════════════════════════════ */
.aoc--checkered {
  border-radius: 14px;
  background: #fff;
  border: 2px solid #e5e7eb;
  box-shadow: 0 4px 14px rgba(0,0,0,.1);
}
.aoc--checkered.aoc--bill { border-color: #fcd34d; }
.aoc--checkered:hover { box-shadow: 0 8px 24px rgba(0,0,0,.16); }

.aoc--checkered .aoc__top {
  background: repeating-conic-gradient(#c0392b 0% 25%, #fff 0% 50%) 0 0 / 12px 12px;
  padding: 8px 10px;
  border-radius: 12px 12px 0 0;
}
.aoc--checkered .aoc__timer { background: rgba(0,0,0,.55); color: #fff; }
.aoc--checkered .aoc__timer--alert { background: rgba(180,0,0,.85); }

.aoc--checkered .aoc__body  { padding: 10px 10px 6px; }
.aoc--checkered .aoc__seq   { color: #94a3b8; }
.aoc--checkered .aoc__name  { color: #1e293b; font-size: 1rem; }
.aoc--checkered .aoc__valor-lbl { color: #64748b; }
.aoc--checkered .aoc__amount    { color: #c0392b; font-size: .88rem; }

.aoc--checkered .aoc__bottom { color: #475569; border-top: 1px dashed #e5e7eb; padding-top: 6px; }


/* ══════════════════════════════════════════════════════════════════
   ESTILO 4: minimal-card
   (tarjeta plana con acento de color — café / retail)
══════════════════════════════════════════════════════════════════ */
.aoc--minimal-card {
  border-radius: 12px;
  background: #fff;
  border: 1.5px solid #e2e8f0;
  border-left: 5px solid #2563eb;
  box-shadow: 0 2px 8px rgba(0,0,0,.07);
  align-items: flex-start;
}
.aoc--minimal-card.aoc--bill { border-left-color: #d97706; }
.aoc--minimal-card:hover { box-shadow: 0 6px 18px rgba(37,99,235,.14); }

.aoc--minimal-card .aoc__top { padding: 8px 10px 2px; }
.aoc--minimal-card .aoc__timer { background: #f1f5f9; color: #475569; }
.aoc--minimal-card .aoc__timer--alert { background: #fee2e2; color: #dc2626; }

.aoc--minimal-card .aoc__body  { align-items: flex-start; text-align: left; padding: 2px 10px 6px; }
.aoc--minimal-card .aoc__seq   { color: #94a3b8; }
.aoc--minimal-card .aoc__name  { color: #1e293b; font-size: 1rem; }
.aoc--minimal-card .aoc__valor-lbl { color: #64748b; }
.aoc--minimal-card .aoc__amount    { color: #2563eb; font-size: .9rem; }

.aoc--minimal-card .aoc__bottom { color: #64748b; border-top: 1px solid #f1f5f9; padding-top: 5px; }


/* ══════════════════════════════════════════════════════════════════
   ESTILO 5: ticket
   (comprobante / recibo — food truck / servicio rápido)
══════════════════════════════════════════════════════════════════ */
.aoc--ticket {
  border-radius: 0 0 10px 10px;
  background: #fff;
  border: 1.5px solid #d1d5db;
  border-top: none;
  box-shadow: 0 3px 10px rgba(0,0,0,.1);
}
.aoc--ticket::before {
  content: '';
  display: block;
  height: 12px;
  background: radial-gradient(circle at 50% 0%, transparent 6px, #fff 6px) 0 0 / 14px 12px repeat-x,
              #1e293b;
  flex-shrink: 0;
}
.aoc--ticket.aoc--bill::before { background-color: #d97706; }
.aoc--ticket:hover { box-shadow: 0 6px 20px rgba(0,0,0,.15); }

.aoc--ticket .aoc__top { padding: 6px 10px 2px; background: #f8fafc; border-bottom: 1px dashed #d1d5db; }
.aoc--ticket .aoc__timer { background: #e2e8f0; color: #475569; }
.aoc--ticket .aoc__timer--alert { background: #fee2e2; color: #dc2626; }

.aoc--ticket .aoc__body { padding: 8px 10px 4px; }
.aoc--ticket .aoc__seq  { color: #94a3b8; font-family: monospace; }
.aoc--ticket .aoc__name { color: #1e293b; font-family: monospace; font-size: .95rem; }
.aoc--ticket .aoc__valor-lbl { color: #94a3b8; font-family: monospace; }
.aoc--ticket .aoc__amount    { color: #1e293b; font-family: monospace; font-weight: 900; font-size: .9rem; }

.aoc--ticket .aoc__bottom { color: #64748b; border-top: 1px dashed #d1d5db; font-family: monospace; }


/* ══════════════════════════════════════════════════════════════════
   ESTILO 6: bubble
   (burbuja redondeada con gradiente suave — heladería / bar)
══════════════════════════════════════════════════════════════════ */
.aoc--bubble {
  border-radius: 80px;
  background: linear-gradient(145deg, #0ea5e9 0%, #0369a1 60%, #075985 100%);
  box-shadow: 0 8px 24px rgba(7,89,133,.38), inset 0 1px 0 rgba(255,255,255,.2);
  border: 2px solid rgba(14,165,233,.35);
  align-items: center;
  width: 155px;
  aspect-ratio: 0.75;
}
.aoc--bubble.aoc--bill {
  background: linear-gradient(145deg, #a855f7 0%, #7c3aed 60%, #5b21b6 100%);
  box-shadow: 0 8px 24px rgba(91,33,182,.38), inset 0 1px 0 rgba(255,255,255,.2);
  border-color: rgba(168,85,247,.35);
}
.aoc--bubble:hover { box-shadow: 0 12px 32px rgba(7,89,133,.52); }

.aoc--bubble .aoc__top { padding: 10px 10px 2px; background: none; justify-content: center; }
.aoc--bubble .aoc__timer { background: rgba(0,0,0,.3); color: #e0f2fe; }
.aoc--bubble .aoc__timer--alert { background: rgba(220,38,38,.8); color: #fff; }
.aoc--bubble .aoc__del { display: none; }

.aoc--bubble .aoc__body { padding: 6px 10px; background: none; }
.aoc--bubble .aoc__seq  { color: rgba(255,255,255,.6); }
.aoc--bubble .aoc__name { color: #fff; text-shadow: 0 1px 4px rgba(0,0,0,.35); }
.aoc--bubble .aoc__valor-lbl { color: rgba(255,255,255,.7); }
.aoc--bubble .aoc__amount    { color: #bae6fd; font-weight: 800; }

.aoc--bubble .aoc__bottom { color: rgba(255,255,255,.85); padding-bottom: 10px; background: none; justify-content: center; }
.aoc--bubble .aoc__bottom > * { background: rgba(0,0,0,.25); padding: 2px 10px; border-radius: 10px; }


/* ══════════════════════════════════════════════════════════════════
   RESPONSIVE (estilos 2-6)
══════════════════════════════════════════════════════════════════ */
@media (max-width: 768px) {
  .aoc { width: 148px; }
  .aoc--circular-gold { width: 155px; }
  .aoc--bubble { width: 140px; }
}
@media (max-width: 576px) {
  .aoc { width: 140px; }
  .aoc--circular-gold { width: 145px; }
  .aoc--bubble { width: 132px; }
  .aoc__name { font-size: .9rem; }
  .aoc__amount { font-size: .75rem; }
}
</style>
