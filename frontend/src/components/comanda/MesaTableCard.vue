<template>
  <!-- La escena contiene la mesa + las 4 sillas. El clic en cualquier parte la abre -->
  <div class="mtc-scene" @click="$emit('click')">

    <!-- Silla SUPERIOR: hora del pedido -->
    <div class="mtc-silla mtc-silla--top" :class="{ 'mtc-silla--alerta': esAlerta }">
      <i class="bi bi-clock"></i>
      <span>{{ horaDisplay }}</span>
    </div>

    <!-- Silla IZQUIERDA: eliminar -->
    <button class="mtc-silla mtc-silla--left mtc-silla--del"
      @click.stop="$emit('eliminar')"
      title="Eliminar pedido (irreversible)">
      <i class="bi bi-trash"></i>
    </button>

    <!-- MESA — óvalo de madera (centro) -->
    <div class="mtc-oval">
      <span v-if="mesa.daily_seq" class="mtc-seq">#{{ mesa.daily_seq }}</span>
      <div class="mtc-nombre">{{ mesa.name }}</div>
      <div class="mtc-valor-label">Valor</div>
      <div class="mtc-valor">{{ fmt(mesa.amount) }}</div>
    </div>

    <!-- Silla DERECHA: facturar -->
    <button class="mtc-silla mtc-silla--right mtc-silla--fac"
      disabled
      title="Facturación próximamente"
      @click.stop>
      <i class="bi bi-receipt"></i>
    </button>

    <!-- Silla INFERIOR: mesero -->
    <div class="mtc-silla mtc-silla--bottom">
      <i class="bi bi-person-fill"></i>
      <span class="mtc-chip-text">{{ mesa.waiter_name || '—' }}</span>
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
  Dimensiones mobile-first (≤576px):
    Óvalo:   116px × 88px
    Sillas laterales (btn):  28px × 28px, gap 9px del borde del óvalo
    Sillas verticales (chip): 24px alto,  gap 8px del borde del óvalo
    Escena:  (28+9+116+9+28) × (24+8+88+8+24) = 190 × 152px
    2 por fila en 390px: 2×190 + 10 = 390px ✓
*/

/* ── Escena (contenedor relativo sin fondo) ──────────────────────────────── */
.mtc-scene {
  position: relative;
  width: 190px;
  height: 152px;
  cursor: pointer;
  flex: 0 0 auto;
  transition: transform .2s;
}
.mtc-scene:hover { transform: translateY(-5px) scale(1.03); }

/* ── Óvalo central ───────────────────────────────────────────────────────── */
.mtc-oval {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 116px;
  height: 88px;
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
    0 18px 45px rgba(0,0,0,.45),
    0 5px 14px rgba(0,0,0,.25),
    inset 0 3px 10px rgba(255,220,120,.3),
    inset 0 -2px 7px rgba(0,0,0,.25);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1;
  transition: box-shadow .2s;
}
.mtc-scene:hover .mtc-oval {
  box-shadow:
    0 26px 55px rgba(0,0,0,.55),
    0 8px 18px rgba(0,0,0,.3),
    inset 0 4px 12px rgba(255,220,120,.35),
    inset 0 -2px 7px rgba(0,0,0,.25);
}

/* Número de comanda */
.mtc-seq {
  position: absolute;
  top: 8px; right: 10px;
  background: rgba(0,0,0,.5);
  color: #fde68a;
  font-size: 8px;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 4px;
  line-height: 1.4;
}

.mtc-nombre {
  font-size: 14px;
  font-weight: 900;
  color: #fff;
  text-shadow: 0 2px 5px rgba(0,0,0,.7);
  text-align: center;
  line-height: 1.1;
  padding: 0 8px;
  word-break: break-word;
}
.mtc-valor-label {
  font-size: 8px;
  font-weight: 700;
  color: #fde68a;
  text-transform: uppercase;
  letter-spacing: .7px;
  margin-top: 4px;
}
.mtc-valor {
  font-size: 11px;
  font-weight: 800;
  color: #86efac;
  text-shadow: 0 1px 3px rgba(0,0,0,.6);
  text-align: center;
  padding: 0 6px;
}

/* ── Sillas — base compartida ────────────────────────────────────────────── */
.mtc-silla {
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  z-index: 2;
}

/* Sillas INFO (chip oscuro — top y bottom) */
.mtc-silla--top,
.mtc-silla--bottom {
  background: #1e293b;
  color: #cbd5e1;
  font-size: 10px;
  font-weight: 600;
  padding: 4px 11px;
  border-radius: 20px;
  border: 1px solid rgba(255,255,255,.09);
  box-shadow: 0 3px 10px rgba(0,0,0,.35);
  white-space: nowrap;
  left: 50%;
  transform: translateX(-50%);
}
.mtc-silla--top    { top: 0; }
.mtc-silla--bottom { bottom: 0; }

.mtc-chip-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 88px;
}

/* Alerta en hora */
.mtc-silla--alerta {
  background: #450a0a;
  color: #fca5a5;
  border-color: rgba(220,38,38,.5);
  animation: mtc-pulse 1.5s ease-in-out infinite;
}
@keyframes mtc-pulse {
  0%, 100% { box-shadow: 0 3px 8px rgba(220,38,38,.3); }
  50%       { box-shadow: 0 3px 20px rgba(220,38,38,.75); }
}

/* Sillas ACCIÓN (botón circular — left y right) */
.mtc-silla--left,
.mtc-silla--right {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1.5px solid transparent;
  font-size: 12px;
  cursor: pointer;
  transition: background .15s, color .15s, transform .15s;
  top: 50%;
  transform: translateY(-50%);
}
.mtc-silla--left  { left: 0; }
.mtc-silla--right { right: 0; }

.mtc-silla--del {
  background: rgba(220,38,38,.15);
  color: #ef4444;
  border-color: rgba(220,38,38,.35);
}
.mtc-silla--del:hover {
  background: #dc2626;
  color: #fff;
  transform: translateY(-50%) scale(1.15);
}
.mtc-silla--fac {
  background: rgba(22,163,74,.12);
  color: #22c55e;
  border-color: rgba(22,163,74,.3);
}
.mtc-silla--fac:disabled {
  opacity: .4;
  cursor: not-allowed;
}

/* ── Responsive ─────────────────────────────────────────────────────────── */

/* Tablet */
@media (min-width: 577px) and (max-width: 768px) {
  /* Óvalo: 134×102  Escena: (32+10+134+10+32)×(26+9+102+9+26) = 218×172 */
  .mtc-scene { width: 218px; height: 172px; }
  .mtc-oval  { width: 134px; height: 102px; }
  .mtc-nombre { font-size: 16px; }
  .mtc-valor  { font-size: 12px; }
  .mtc-silla--top, .mtc-silla--bottom { font-size: 11px; padding: 5px 13px; }
  .mtc-silla--left, .mtc-silla--right { width: 32px; height: 32px; font-size: 13px; }
}

/* Desktop */
@media (min-width: 769px) {
  /* Óvalo: 154×116  Escena: (36+12+154+12+36)×(28+10+116+10+28) = 250×192 */
  .mtc-scene { width: 250px; height: 192px; }
  .mtc-oval  { width: 154px; height: 116px; }
  .mtc-nombre { font-size: 20px; }
  .mtc-valor  { font-size: 14px; }
  .mtc-valor-label { font-size: 9px; margin-top: 5px; }
  .mtc-silla--top, .mtc-silla--bottom { font-size: 12px; padding: 5px 15px; }
  .mtc-chip-text { max-width: 110px; }
  .mtc-silla--left, .mtc-silla--right { width: 36px; height: 36px; font-size: 14px; }
}
</style>
