<template>
  <div class="mtc-card" :class="{ 'mtc-card--alerta': esAlerta }" @click="$emit('click')">

    <!-- Badge de número de comanda -->
    <span v-if="mesa.daily_seq" class="mtc-seq">#{{ mesa.daily_seq }}</span>

    <!-- Chip hora -->
    <div class="mtc-chip mtc-chip--hora" :class="{ 'mtc-chip--alerta': esAlerta }">
      <i class="bi bi-clock"></i>
      <span>{{ horaDisplay }}</span>
    </div>

    <!-- Mesa oval (superficie de madera) -->
    <div class="mtc-oval">
      <div class="mtc-nombre">{{ mesa.name }}</div>
      <div class="mtc-valor-label">Valor</div>
      <div class="mtc-valor">{{ fmt(mesa.amount) }}</div>
    </div>

    <!-- Chip mesero -->
    <div class="mtc-chip mtc-chip--mesero">
      <i class="bi bi-person-fill"></i>
      <span class="mtc-chip-text">{{ mesa.waiter_name || '—' }}</span>
    </div>

    <!-- Botones -->
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
/* ── Tarjeta contenedora (da el efecto flotante oscuro) ─────────────────── */
.mtc-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 10px 10px 8px;
  background: #1a2535;
  border-radius: 18px;
  border: 1px solid rgba(255,255,255,.07);
  box-shadow:
    0 8px 24px rgba(0,0,0,.55),
    0 2px 8px rgba(0,0,0,.35);
  cursor: pointer;
  transition: transform .2s, box-shadow .2s;
  flex: 0 0 auto;
  width: 148px;           /* 2 por fila en 360px: 2×148+10=306px */
}
.mtc-card:hover {
  transform: translateY(-5px) scale(1.02);
  box-shadow:
    0 16px 36px rgba(0,0,0,.65),
    0 4px 12px rgba(0,0,0,.4);
}
.mtc-card--alerta {
  border-color: rgba(220,38,38,.35);
  box-shadow:
    0 8px 24px rgba(220,38,38,.3),
    0 2px 8px rgba(0,0,0,.3);
}

/* Badge número de comanda */
.mtc-seq {
  position: absolute;
  top: 8px; right: 10px;
  background: #1d4ed8;
  color: #fff;
  font-size: 9px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 6px;
  line-height: 1.4;
}

/* ── Chips (hora / mesero) ───────────────────────────────────────────────── */
.mtc-chip {
  width: 100%;
  background: rgba(255,255,255,.07);
  border: 1px solid rgba(255,255,255,.10);
  border-radius: 10px;
  color: #94a3b8;
  font-size: 10px;
  font-weight: 600;
  padding: 4px 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
}
.mtc-chip span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.mtc-chip--hora { color: #cbd5e1; }
.mtc-chip--alerta {
  background: rgba(220,38,38,.18);
  border-color: rgba(220,38,38,.4);
  color: #fca5a5;
  animation: mtc-pulse 1.5s ease-in-out infinite;
}
@keyframes mtc-pulse {
  0%, 100% { box-shadow: none; }
  50%       { box-shadow: 0 0 10px rgba(220,38,38,.5); }
}
.mtc-chip--mesero { color: #94a3b8; }

/* ── Superficie oval de madera ───────────────────────────────────────────── */
.mtc-oval {
  width: 128px;
  height: 96px;
  border-radius: 50%;                      /* verdadero óvalo */
  background: radial-gradient(
    ellipse at 42% 35%,
    #f5d090 0%,
    #d4922c 45%,
    #a05c14 80%,
    #7a3d08 100%
  );
  border: 3px solid #6b3408;
  box-shadow:
    0 8px 20px rgba(0,0,0,.5),
    inset 0 3px 10px rgba(255,220,130,.25),
    inset 0 -3px 8px rgba(0,0,0,.2);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: box-shadow .2s;
}
.mtc-card:hover .mtc-oval {
  box-shadow:
    0 12px 28px rgba(0,0,0,.55),
    inset 0 3px 12px rgba(255,220,130,.3),
    inset 0 -3px 8px rgba(0,0,0,.2);
}

.mtc-nombre {
  font-size: 15px;
  font-weight: 900;
  color: #fff;
  text-shadow: 0 2px 5px rgba(0,0,0,.7);
  text-align: center;
  line-height: 1.1;
  padding: 0 10px;
  word-break: break-word;
}
.mtc-valor-label {
  font-size: 8px;
  font-weight: 700;
  color: #fde68a;
  text-transform: uppercase;
  letter-spacing: .8px;
  margin-top: 5px;
}
.mtc-valor {
  font-size: 12px;
  font-weight: 800;
  color: #86efac;
  text-shadow: 0 1px 3px rgba(0,0,0,.5);
  text-align: center;
  padding: 0 6px;
}

/* ── Botones ─────────────────────────────────────────────────────────────── */
.mtc-acciones {
  display: flex;
  gap: 6px;
}
.mtc-btn {
  flex: 1;
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
.mtc-btn--del { background: rgba(220,38,38,.15); color: #f87171; border-color: rgba(220,38,38,.3); }
.mtc-btn--del:hover { background: #dc2626; color: #fff; border-color: #dc2626; }
.mtc-btn--fac { background: rgba(22,163,74,.12); color: #4ade80; border-color: rgba(22,163,74,.25); }
.mtc-btn--fac:disabled { opacity: .4; cursor: not-allowed; }

/* ── Responsive ─────────────────────────────────────────────────────────── */
@media (min-width: 577px) and (max-width: 768px) {
  .mtc-card { width: 158px; }
  .mtc-oval { width: 138px; height: 106px; }
  .mtc-nombre { font-size: 16px; }
}

@media (min-width: 769px) {
  .mtc-card { width: 170px; }
  .mtc-oval { width: 150px; height: 114px; }
  .mtc-nombre { font-size: 18px; }
  .mtc-chip { font-size: 11px; padding: 5px 10px; }
  .mtc-valor { font-size: 13px; }
}
</style>
