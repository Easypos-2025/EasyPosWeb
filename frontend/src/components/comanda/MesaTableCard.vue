<template>
  <div class="mtc-wrap" @click="$emit('click')">

    <!-- Chip hora — flota encima del óvalo -->
    <div class="mtc-chip mtc-chip--hora" :class="{ 'mtc-chip--alerta': esAlerta }">
      <i class="bi bi-clock"></i>
      <span>{{ horaDisplay }}</span>
    </div>

    <!-- Óvalo de madera flotante -->
    <div class="mtc-oval">
      <span v-if="mesa.daily_seq" class="mtc-seq">#{{ mesa.daily_seq }}</span>
      <div class="mtc-nombre">{{ mesa.name }}</div>
      <div class="mtc-valor-label">Valor</div>
      <div class="mtc-valor">{{ fmt(mesa.amount) }}</div>
    </div>

    <!-- Chip mesero — flota debajo del óvalo -->
    <div class="mtc-chip mtc-chip--mesero">
      <i class="bi bi-person-fill"></i>
      <span class="mtc-chip-text">{{ mesa.waiter_name || '—' }}</span>
    </div>

    <!-- Botones acción -->
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
    if (open > now) open.setDate(open.getDate() - 1)
    return (now - open) > 60 * 60 * 1000
  } catch { return false }
})
</script>

<style scoped>
/* ── Wrapper: 100 % transparente — sin caja, sin borde ──────────────────── */
.mtc-wrap {
  background: transparent;
  border: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 7px;
  cursor: pointer;
  transition: transform .2s;
  flex: 0 0 auto;
}
.mtc-wrap:hover { transform: translateY(-6px) scale(1.03); }

/* ── Chips flotantes (hora / mesero) ─────────────────────────────────────── */
.mtc-chip {
  background: #1e293b;
  color: #cbd5e1;
  font-size: 11px;
  font-weight: 600;
  padding: 5px 14px;
  border-radius: 20px;
  border: 1px solid rgba(255,255,255,.09);
  box-shadow: 0 3px 10px rgba(0,0,0,.55);
  display: flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
  max-width: 148px;
}
.mtc-chip span,
.mtc-chip-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 112px;
}
.mtc-chip--alerta {
  background: #450a0a;
  color: #fca5a5;
  border-color: rgba(220,38,38,.5);
  animation: mtc-pulse 1.5s ease-in-out infinite;
}
@keyframes mtc-pulse {
  0%, 100% { box-shadow: 0 3px 10px rgba(220,38,38,.3); }
  50%       { box-shadow: 0 3px 22px rgba(220,38,38,.75); }
}

/* ── Óvalo de madera (la mesa) ───────────────────────────────────────────── */
.mtc-oval {
  width: 148px;
  height: 112px;
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
    0 20px 50px rgba(0,0,0,.75),
    0 6px 16px rgba(0,0,0,.45),
    inset 0 3px 12px rgba(255,220,120,.3),
    inset 0 -2px 8px rgba(0,0,0,.25);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  transition: box-shadow .2s;
}
.mtc-wrap:hover .mtc-oval {
  box-shadow:
    0 28px 60px rgba(0,0,0,.8),
    0 8px 20px rgba(0,0,0,.5),
    inset 0 4px 14px rgba(255,220,120,.35),
    inset 0 -2px 8px rgba(0,0,0,.25);
}

/* Número de comanda */
.mtc-seq {
  position: absolute;
  top: 12px; right: 14px;
  background: rgba(0,0,0,.5);
  color: #fde68a;
  font-size: 9px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  line-height: 1.4;
}

.mtc-nombre {
  font-size: 18px;
  font-weight: 900;
  color: #fff;
  text-shadow: 0 2px 6px rgba(0,0,0,.7);
  text-align: center;
  line-height: 1.1;
  padding: 0 12px;
  word-break: break-word;
}
.mtc-valor-label {
  font-size: 9px;
  font-weight: 700;
  color: #fde68a;
  text-transform: uppercase;
  letter-spacing: .8px;
  margin-top: 5px;
}
.mtc-valor {
  font-size: 14px;
  font-weight: 800;
  color: #86efac;
  text-shadow: 0 1px 4px rgba(0,0,0,.6);
  text-align: center;
  padding: 0 8px;
}

/* ── Botones ─────────────────────────────────────────────────────────────── */
.mtc-acciones {
  display: flex;
  gap: 8px;
}
.mtc-btn {
  width: 34px;
  height: 30px;
  border-radius: 8px;
  border: 1.5px solid transparent;
  font-size: 12px;
  cursor: pointer;
  transition: background .15s, color .15s;
  display: flex;
  align-items: center;
  justify-content: center;
}
.mtc-btn--del { background: rgba(220,38,38,.2); color: #f87171; border-color: rgba(220,38,38,.35); }
.mtc-btn--del:hover { background: #dc2626; color: #fff; border-color: #dc2626; }
.mtc-btn--fac { background: rgba(22,163,74,.15); color: #4ade80; border-color: rgba(22,163,74,.3); }
.mtc-btn--fac:disabled { opacity: .4; cursor: not-allowed; }

/* ── Responsive ─────────────────────────────────────────────────────────── */
@media (max-width: 576px) {
  .mtc-oval { width: 118px; height: 90px; }
  .mtc-nombre { font-size: 14px; }
  .mtc-valor { font-size: 12px; }
  .mtc-chip { font-size: 10px; padding: 4px 11px; max-width: 118px; }
  .mtc-chip span, .mtc-chip-text { max-width: 86px; }
  .mtc-wrap { gap: 6px; }
}

@media (min-width: 769px) {
  .mtc-oval { width: 168px; height: 126px; }
  .mtc-nombre { font-size: 22px; }
  .mtc-valor { font-size: 15px; }
  .mtc-chip { font-size: 12px; padding: 6px 16px; max-width: 166px; }
  .mtc-chip span, .mtc-chip-text { max-width: 130px; }
  .mtc-wrap { gap: 9px; }
}
</style>
