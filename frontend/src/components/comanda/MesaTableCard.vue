<template>
  <!-- El óvalo ES el componente — todo va dentro, clip elíptico -->
  <div class="mtc-oval" @click="$emit('click')">

    <!-- Comensal SUPERIOR: hora del pedido -->
    <div class="mtc-cm mtc-cm--top" :class="{ 'mtc-cm--alerta': esAlerta }">
      <i class="bi bi-clock"></i>
      <span>{{ horaDisplay }}</span>
    </div>

    <!-- Comensal IZQUIERDO: eliminar -->
    <button class="mtc-cm mtc-cm--left mtc-cm--del"
      @click.stop="$emit('eliminar')"
      title="Eliminar pedido (irreversible)">
      <i class="bi bi-trash"></i>
    </button>

    <!-- INFO central: seq + nombre + valor -->
    <div class="mtc-centro">
      <span v-if="mesa.daily_seq" class="mtc-seq">#{{ mesa.daily_seq }}</span>
      <div class="mtc-nombre">{{ mesa.name }}</div>
      <div class="mtc-valor-label">Valor</div>
      <div class="mtc-valor">{{ fmt(mesa.amount) }}</div>
    </div>

    <!-- Comensal DERECHO: facturar -->
    <button class="mtc-cm mtc-cm--right mtc-cm--fac"
      disabled
      title="Facturación próximamente"
      @click.stop>
      <i class="bi bi-receipt"></i>
    </button>

    <!-- Comensal INFERIOR: mesero -->
    <div class="mtc-cm mtc-cm--bottom">
      <i class="bi bi-person-fill"></i>
      <span class="mtc-mesero-txt">{{ mesa.waiter_name || '—' }}</span>
    </div>

  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  mesa: { type: Object, required: true }
})

defineEmits(['click', 'eliminar', 'facturar'])

const fmtCOP = new Intl.NumberFormat('es-CO', {
  style: 'currency', currency: 'COP',
  minimumFractionDigits: 0, maximumFractionDigits: 0,
})
const fmt = (v) => fmtCOP.format(v || 0)

const horaDisplay = computed(() => {
  if (!props.mesa.hora_apertura) return '—'
  return String(props.mesa.hora_apertura).slice(0, 5)
})

const esAlerta = computed(() => {
  if (!props.mesa.hora_apertura) return false
  try {
    const parts = String(props.mesa.hora_apertura).split(':')
    const h = parseInt(parts[0], 10)
    const m = parseInt(parts[1], 10)
    const now = new Date()
    const open = new Date(now)
    open.setHours(h, m, 0, 0)
    if (open > now) open.setDate(open.getDate() - 1)
    return (now - open) > 60 * 60 * 1000
  } catch { return false }
})
</script>

<style scoped>
/*
  Móvil (≤576px): óvalo 185×145px — 2 por fila en 380px: 2×185+8=378 ✓
  Todos los comensales verificados dentro de la elipse con overflow:hidden.

  Semiejes: a=92.5, b=72.5
  Top/Bottom chip (±35px horiz, ±60.5px vert): (35/92.5)²+(60.5/72.5)²=0.838 < 1 ✓
  Left/Right btn (borde izq en x=14): (78.5/92.5)²=0.721 < 1 ✓
*/

/* ── Óvalo — contenedor y superficie de madera ───────────────────────────── */
.mtc-oval {
  position: relative;
  width: 185px;
  height: 145px;
  border-radius: 50%;
  background: radial-gradient(
    ellipse at 42% 36%,
    #f5d48a 0%,
    #d4912c 46%,
    #a05c14 76%,
    #6e3a08 100%
  );
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
.mtc-oval:hover {
  transform: translateY(-5px) scale(1.04);
  box-shadow:
    0 24px 52px rgba(0,0,0,.52),
    0 8px 18px rgba(0,0,0,.28),
    inset 0 4px 12px rgba(255,220,120,.32),
    inset 0 -2px 7px rgba(0,0,0,.22);
}

/* ── Centro — seq + nombre + valor ──────────────────────────────────────── */
.mtc-centro {
  position: absolute;
  top: 50%;
  left: 50%;
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

.mtc-seq {
  font-size: 8px;
  font-weight: 700;
  color: rgba(255,220,120,.65);
  line-height: 1.2;
  letter-spacing: .4px;
}
.mtc-nombre {
  font-size: 17px;
  font-weight: 900;
  color: #fff;
  text-shadow: 0 2px 6px rgba(0,0,0,.75);
  line-height: 1.1;
  word-break: break-word;
}
.mtc-valor-label {
  font-size: 7px;
  font-weight: 700;
  color: #fde68a;
  text-transform: uppercase;
  letter-spacing: .8px;
  margin-top: 4px;
}
.mtc-valor {
  font-size: 11px;
  font-weight: 800;
  color: #86efac;
  text-shadow: 0 1px 4px rgba(0,0,0,.6);
}

/* ── Comensales — base ───────────────────────────────────────────────────── */
.mtc-cm {
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  z-index: 2;
}

/* Chips de info: top y bottom */
.mtc-cm--top,
.mtc-cm--bottom {
  background: rgba(0,0,0,.48);
  color: #e2e8f0;
  font-size: 9px;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: 10px;
  white-space: nowrap;
  left: 50%;
  transform: translateX(-50%);
  backdrop-filter: blur(2px);
}
.mtc-cm--top    { top: 11px; }
.mtc-cm--bottom { bottom: 11px; }

.mtc-mesero-txt {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 72px;
}

/* Alerta: pedido > 60 min */
.mtc-cm--alerta {
  background: rgba(185,0,0,.72);
  color: #fca5a5;
  animation: mtc-pulse 1.5s ease-in-out infinite;
}
@keyframes mtc-pulse {
  0%,100% { box-shadow: 0 0 0 rgba(220,38,38,.4); }
  50%      { box-shadow: 0 0 12px rgba(220,38,38,.85); }
}

/* Botones acción: left y right */
.mtc-cm--left,
.mtc-cm--right {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: 1.5px solid transparent;
  font-size: 12px;
  cursor: pointer;
  top: 50%;
  transform: translateY(-50%);
  transition: background .15s, transform .15s;
}
.mtc-cm--left  { left: 12px; }
.mtc-cm--right { right: 12px; }

.mtc-cm--del {
  background: rgba(200,30,30,.3);
  color: #fca5a5;
  border-color: rgba(220,38,38,.45);
}
.mtc-cm--del:hover {
  background: rgba(200,30,30,.75);
  color: #fff;
  transform: translateY(-50%) scale(1.18);
}
.mtc-cm--fac {
  background: rgba(20,150,70,.22);
  color: #86efac;
  border-color: rgba(22,163,74,.4);
}
.mtc-cm--fac:disabled { opacity: .38; cursor: not-allowed; }

/* ── Responsive ─────────────────────────────────────────────────────────── */

/* Tablet (577–768px) */
@media (min-width: 577px) and (max-width: 768px) {
  .mtc-oval    { width: 210px; height: 165px; }
  .mtc-nombre  { font-size: 20px; }
  .mtc-valor   { font-size: 13px; }
  .mtc-centro  { width: 110px; }
  .mtc-cm--top, .mtc-cm--bottom { font-size: 10px; padding: 4px 11px; }
  .mtc-cm--top    { top: 13px; }
  .mtc-cm--bottom { bottom: 13px; }
  .mtc-cm--left, .mtc-cm--right { width: 34px; height: 34px; font-size: 13px; }
  .mtc-cm--left  { left: 14px; }
  .mtc-cm--right { right: 14px; }
  .mtc-mesero-txt { max-width: 84px; }
}

/* Desktop (769px+) */
@media (min-width: 769px) {
  .mtc-oval    { width: 240px; height: 190px; }
  .mtc-nombre  { font-size: 24px; }
  .mtc-valor   { font-size: 15px; }
  .mtc-valor-label { font-size: 8px; }
  .mtc-centro  { width: 128px; }
  .mtc-cm--top, .mtc-cm--bottom { font-size: 11px; padding: 5px 13px; }
  .mtc-cm--top    { top: 16px; }
  .mtc-cm--bottom { bottom: 16px; }
  .mtc-cm--left, .mtc-cm--right { width: 38px; height: 38px; font-size: 15px; }
  .mtc-cm--left  { left: 16px; }
  .mtc-cm--right { right: 16px; }
  .mtc-mesero-txt { max-width: 100px; }
}
</style>
