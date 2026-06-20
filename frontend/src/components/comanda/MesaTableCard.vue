<template>
  <div class="mtc-wrap" @click="$emit('click')">

    <!-- Chip superior: hora del pedido -->
    <div class="mtc-chip" :class="{ 'mtc-chip--alerta': esAlerta }">
      <i class="bi bi-clock"></i>
      <span class="mtc-chip-text">{{ horaDisplay }}</span>
    </div>

    <!-- Tablón de madera (superficie de la mesa) -->
    <div class="mtc-tablon" :class="{ 'mtc-tablon--alerta': esAlerta }">
      <span v-if="mesa.daily_seq" class="mtc-seq">#{{ mesa.daily_seq }}</span>
      <div class="mtc-nombre">{{ mesa.name }}</div>
      <div class="mtc-valor-label">Valor</div>
      <div class="mtc-valor">{{ fmt(mesa.amount) }}</div>
    </div>

    <!-- Chip inferior: mesero -->
    <div class="mtc-chip mtc-chip--mesero">
      <i class="bi bi-person"></i>
      <span class="mtc-chip-text">{{ mesa.waiter_name || '—' }}</span>
    </div>

    <!-- Botones de acción -->
    <div class="mtc-acciones" @click.stop>
      <button class="mtc-btn mtc-btn--del" @click.stop="$emit('eliminar')"
        title="Eliminar pedido (irreversible)">
        <i class="bi bi-trash"></i>
      </button>
      <button class="mtc-btn mtc-btn--fac" disabled
        title="Facturación próximamente">
        <i class="bi bi-receipt"></i>
      </button>
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
    if (open > now) open.setDate(open.getDate() - 1) // cruzó medianoche
    return (now - open) > 60 * 60 * 1000
  } catch { return false }
})
</script>

<style scoped>
/* ── Contenedor ─────────────────────────────────────────────────────────── */
.mtc-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
  cursor: pointer;
  transition: transform .2s;
  flex: 0 0 auto;
  width: 118px;   /* mobile-first: caben 3 por fila en 360px */
}
.mtc-wrap:hover { transform: scale(1.04) translateY(-2px); }

/* ── Chips (sillas alrededor de la mesa) ────────────────────────────────── */
.mtc-chip {
  background: #1e293b;
  color: #cbd5e1;
  font-size: 10px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 20px;
  box-shadow: 0 2px 6px rgba(0,0,0,.35);
  border: 1px solid #334155;
  z-index: 2;
  position: relative;
  margin-bottom: -10px;
  display: flex;
  align-items: center;
  gap: 4px;
  max-width: 110px;
}
.mtc-chip-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 80px;
}
.mtc-chip--mesero {
  margin-bottom: 0;
  margin-top: -10px;
}
.mtc-chip--alerta {
  background: #450a0a;
  color: #fca5a5;
  border-color: #ef4444;
  animation: mtc-pulse 1.5s ease-in-out infinite;
}
@keyframes mtc-pulse {
  0%, 100% { box-shadow: 0 2px 6px rgba(220,38,38,.3); }
  50%       { box-shadow: 0 2px 18px rgba(220,38,38,.75); }
}

/* ── Tablón de madera (superficie) ──────────────────────────────────────── */
.mtc-tablon {
  width: 110px;
  min-height: 95px;
  background: radial-gradient(ellipse at 38% 32%, #d4925a 0%, #a65c20 55%, #7a3d0a 100%);
  border: 4px solid #5a3008;
  border-radius: 22px;
  box-shadow:
    0 10px 24px rgba(0,0,0,.45),
    0 4px 8px rgba(0,0,0,.25),
    inset 0 2px 10px rgba(255,255,255,.12);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 1;
  padding: 14px 8px;
  transition: box-shadow .2s;
}
.mtc-tablon--alerta {
  border-color: #dc2626;
  box-shadow:
    0 10px 24px rgba(220,38,38,.4),
    0 4px 8px rgba(0,0,0,.25),
    inset 0 2px 10px rgba(255,255,255,.08);
}
.mtc-wrap:hover .mtc-tablon {
  box-shadow:
    0 14px 30px rgba(0,0,0,.5),
    0 6px 12px rgba(0,0,0,.3),
    inset 0 2px 12px rgba(255,255,255,.18);
}

/* Número de comanda */
.mtc-seq {
  position: absolute;
  top: 8px; right: 9px;
  background: rgba(0,0,0,.45);
  color: #fde68a;
  font-size: 9px;
  font-weight: 700;
  padding: 2px 5px;
  border-radius: 4px;
  line-height: 1.4;
}

.mtc-nombre {
  font-size: 16px;
  font-weight: 900;
  color: #fff;
  text-shadow: 0 2px 4px rgba(0,0,0,.6);
  text-align: center;
  line-height: 1.1;
  word-break: break-word;
  max-width: 98px;
}

.mtc-valor-label {
  font-size: 9px;
  font-weight: 700;
  color: #fde68a;
  text-transform: uppercase;
  letter-spacing: .8px;
  margin-top: 6px;
}

.mtc-valor {
  font-size: 13px;
  font-weight: 800;
  color: #86efac;
  text-shadow: 0 1px 3px rgba(0,0,0,.5);
  margin-top: 1px;
  text-align: center;
}

/* ── Botones de acción ──────────────────────────────────────────────────── */
.mtc-acciones {
  display: flex;
  gap: 6px;
  margin-top: 8px;
}
.mtc-btn {
  width: 32px;
  height: 28px;
  border-radius: 8px;
  border: 1.5px solid transparent;
  font-size: 12px;
  cursor: pointer;
  transition: background .15s, color .15s;
  display: flex;
  align-items: center;
  justify-content: center;
}
.mtc-btn--del { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }
.mtc-btn--del:hover { background: #dc2626; color: #fff; border-color: #dc2626; }
.mtc-btn--fac { background: #f0fdf4; color: #16a34a; border-color: #86efac; }
.mtc-btn--fac:disabled { opacity: .45; cursor: not-allowed; }

/* ── Responsive ─────────────────────────────────────────────────────────── */
/* Tablet: la tarjeta crece un poco */
@media (min-width: 577px) and (max-width: 768px) {
  .mtc-wrap { width: 135px; }
  .mtc-tablon { width: 126px; min-height: 105px; border-radius: 24px; }
  .mtc-nombre { font-size: 17px; }
  .mtc-chip { max-width: 126px; }
  .mtc-chip-text { max-width: 94px; }
}

/* Desktop: más grande */
@media (min-width: 769px) {
  .mtc-wrap { width: 155px; }
  .mtc-tablon { width: 145px; min-height: 115px; border-radius: 26px; padding: 18px 10px; }
  .mtc-nombre { font-size: 20px; max-width: 125px; }
  .mtc-chip { font-size: 11px; padding: 5px 12px; max-width: 144px; }
  .mtc-chip-text { max-width: 112px; }
}
</style>
