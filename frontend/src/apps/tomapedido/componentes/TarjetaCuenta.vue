<template>
  <!-- Tarjeta de una cuenta abierta con el estilo que la empresa escogió en la web
       (company_configs.pos_card_style). Mismo diseño de AccountOrderCard.vue de la web, sin
       eliminar ni facturar: desde la toma de pedidos no se elimina nada. -->
  <button v-if="estilo === 'oval-wood'" class="aoc-oval" @click="$emit('abrir')">
    <span class="aoc-oval__timer" :class="{ 'aoc-oval__timer--alert': alerta }">
      <Icono nombre="reloj" :tam="11" /><span>{{ hora }}</span>
    </span>
    <span class="aoc-oval__center">
      <span class="aoc-oval__name">{{ cuenta.mesa }}</span>
      <span class="aoc-oval__valor-lbl">VALOR</span>
      <span class="aoc-oval__amount">{{ pesos(cuenta.total) }}</span>
    </span>
    <span class="aoc-oval__waiter">
      <Icono nombre="usuario" :tam="11" /><span class="aoc-oval__waiter-txt">{{ cuenta.mesero || "—" }}</span>
    </span>
  </button>

  <button v-else class="aoc" :class="`aoc--${estilo}`" @click="$emit('abrir')">
    <span class="aoc__top">
      <span class="aoc__timer" :class="{ 'aoc__timer--alert': alerta }"><Icono nombre="reloj" :tam="11" />{{ hora }}</span>
    </span>
    <span class="aoc__body">
      <span class="aoc__name">{{ cuenta.mesa }}</span>
      <span class="aoc__valor-lbl">VALOR</span>
      <span class="aoc__amount">{{ pesos(cuenta.total) }}</span>
    </span>
    <span class="aoc__bottom">
      <span class="aoc__waiter"><Icono nombre="usuario" :tam="11" /><span class="aoc__waiter-txt">{{ cuenta.mesero || "—" }}</span></span>
    </span>
  </button>
</template>

<script setup>
import { computed } from "vue"
import Icono from "./Icono.vue"
import { pesos } from "../formato"

const props = defineProps({
  cuenta: { type: Object, required: true },
  estilo: { type: String, default: "oval-wood" },
  ahora: { type: Number, default: () => Date.now() },        // para refrescar la alerta sin recargar
})
defineEmits(["abrir"])

// La hora llega como la guarda el escritorio: "01:20:08 PM" (toma de pedidos) o "13:09:54" (caja)
const minutosDelDia = computed(() => {
  const m = String(props.cuenta.hora || "").trim().match(/^(\d{1,2}):(\d{2})(?::\d{2})?\s*([AaPp])?/)
  if (!m) return null
  let h = Number(m[1]) % 24
  const pm = m[3] && m[3].toLowerCase() === "p"
  if (m[3]) h = (h % 12) + (pm ? 12 : 0)
  return h * 60 + Number(m[2])
})
const hora = computed(() => {
  const t = minutosDelDia.value
  return t == null ? "—" : `${String(Math.floor(t / 60)).padStart(2, "0")}:${String(t % 60).padStart(2, "0")}`
})
// Alerta (como la web): la cuenta lleva más de 60 minutos abierta
const alerta = computed(() => {
  const t = minutosDelDia.value
  if (t == null) return false
  const d = new Date(props.ahora)
  let transcurrido = d.getHours() * 60 + d.getMinutes() - t
  if (transcurrido < 0) transcurrido += 24 * 60
  return transcurrido > 60
})
</script>

<style scoped>
button { font: inherit; padding: 0; }

/* ═══ 1. oval-wood (mesa elíptica de madera) ═══ */
.aoc-oval {
  position: relative; width: 185px; height: 145px; border-radius: 50%;
  background: radial-gradient(ellipse at 42% 36%, #f5d48a 0%, #d4912c 46%, #a05c14 76%, #6e3a08 100%);
  border: 3px solid #5a3008;
  box-shadow: 0 16px 42px rgba(0,0,0,.42), 0 5px 12px rgba(0,0,0,.22),
              inset 0 3px 10px rgba(255,220,120,.28), inset 0 -2px 7px rgba(0,0,0,.22);
  overflow: hidden; cursor: pointer; flex: 0 0 auto; transition: transform .2s;
}
.aoc-oval:active { transform: scale(.97); }
.aoc-oval__center {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  width: 70%; text-align: center; pointer-events: none; z-index: 1;
}
.aoc-oval__name { font-size: 17px; font-weight: 900; color: #fff; text-shadow: 0 2px 6px rgba(0,0,0,.75); line-height: 1.1; word-break: break-word; }
.aoc-oval__valor-lbl { font-size: 7px; font-weight: 700; color: #fde68a; text-transform: uppercase; letter-spacing: .8px; margin-top: 4px; }
.aoc-oval__amount { font-size: 12px; font-weight: 800; color: #86efac; text-shadow: 0 1px 4px rgba(0,0,0,.6); }
.aoc-oval__timer, .aoc-oval__waiter {
  position: absolute; left: 50%; transform: translateX(-50%);
  display: flex; align-items: center; gap: 3px;
  background: rgba(0,0,0,.48); color: #e2e8f0; font-size: 10px; font-weight: 700;
  padding: 3px 9px; border-radius: 10px; white-space: nowrap; z-index: 2;
}
.aoc-oval__timer { top: 11px; }
.aoc-oval__waiter { bottom: 11px; }
.aoc-oval__timer--alert { background: rgba(185,0,0,.72); color: #fca5a5; animation: aoc-pulse 1.5s ease-in-out infinite; }
.aoc-oval__waiter-txt { overflow: hidden; text-overflow: ellipsis; max-width: 90px; }
@keyframes aoc-pulse {
  0%, 100% { box-shadow: 0 0 0 rgba(220,38,38,.4); }
  50% { box-shadow: 0 0 12px rgba(220,38,38,.85); }
}

/* ═══ Base compartida (estilos 2-6) ═══ */
.aoc {
  display: flex; flex-direction: column; border: none; cursor: pointer; text-align: left;
  touch-action: manipulation; transition: transform .18s; overflow: hidden; position: relative;
  width: 160px; padding-bottom: 6px;
}
.aoc:active { transform: scale(.97); }
.aoc__top { display: flex; align-items: center; justify-content: space-between; padding: 6px 10px 4px; flex-shrink: 0; }
.aoc__timer { display: inline-flex; align-items: center; gap: 4px; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 10px; white-space: nowrap; }
.aoc__timer--alert { animation: aoc-pulse 1.5s ease-in-out infinite; }
.aoc__body { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 4px 10px 6px; text-align: center; }
.aoc__name { font-size: 16px; font-weight: 800; line-height: 1.1; word-break: break-word; }
.aoc__valor-lbl { font-size: 8px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; margin-top: 4px; opacity: .75; }
.aoc__amount { font-size: 13px; font-weight: 700; }
.aoc__bottom { display: flex; align-items: center; padding: 4px 10px 4px; font-size: 11px; font-weight: 600; flex-shrink: 0; }
.aoc__waiter { display: inline-flex; align-items: center; gap: 4px; min-width: 0; }
.aoc__waiter-txt { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* ═══ 2. circular-gold ═══ */
.aoc--circular-gold {
  width: 170px; aspect-ratio: 1; border-radius: 50%; padding-bottom: 0;
  background: radial-gradient(circle at 35% 30%, #fcd34d 0%, #d97706 55%, #92400e 100%);
  box-shadow: 0 8px 28px rgba(146,64,14,.45), inset 0 1px 0 rgba(255,255,255,.25);
  border: 3px solid rgba(253,211,77,.3); align-items: center; justify-content: center;
}
.aoc--circular-gold .aoc__top { position: absolute; top: 18%; left: 0; right: 0; padding: 0; justify-content: center; }
.aoc--circular-gold .aoc__timer { background: rgba(220,38,38,.88); color: #fff; }
.aoc--circular-gold .aoc__top { top: 14%; }
.aoc--circular-gold .aoc__body { flex: 0 0 auto; padding: 0 18px; }
.aoc--circular-gold .aoc__name {
  color: #fff; text-shadow: 0 1px 4px rgba(0,0,0,.4);
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;   /* máx. 2 líneas */
}
.aoc--circular-gold .aoc__valor-lbl { color: rgba(255,255,255,.75); }
.aoc--circular-gold .aoc__amount { color: #fff; text-shadow: 0 1px 2px rgba(0,0,0,.3); }
.aoc--circular-gold .aoc__bottom { position: absolute; bottom: 12%; left: 0; right: 0; justify-content: center; padding: 0; color: rgba(255,255,255,.92); }
.aoc--circular-gold .aoc__waiter { background: rgba(0,0,0,.28); padding: 3px 10px; border-radius: 10px; max-width: 78%; }

/* ═══ 3. checkered (mantel de cuadros) ═══ */
.aoc--checkered { border-radius: 14px; background: #fff; border: 2px solid #e5e7eb; box-shadow: 0 4px 14px rgba(0,0,0,.1); }
.aoc--checkered .aoc__top { background: repeating-conic-gradient(#c0392b 0% 25%, #fff 0% 50%) 0 0 / 12px 12px; padding: 8px 10px; border-radius: 12px 12px 0 0; }
.aoc--checkered .aoc__timer { background: rgba(0,0,0,.55); color: #fff; }
.aoc--checkered .aoc__timer--alert { background: rgba(180,0,0,.85); }
.aoc--checkered .aoc__body { padding: 10px 10px 6px; }
.aoc--checkered .aoc__name { color: #1e293b; }
.aoc--checkered .aoc__valor-lbl { color: #64748b; }
.aoc--checkered .aoc__amount { color: #c0392b; }
.aoc--checkered .aoc__bottom { color: #475569; border-top: 1px dashed #e5e7eb; padding-top: 6px; }

/* ═══ 4. minimal-card ═══ */
.aoc--minimal-card {
  border-radius: 12px; background: #fff; border: 1.5px solid #e2e8f0; border-left: 5px solid #2563eb;
  box-shadow: 0 2px 8px rgba(0,0,0,.07); align-items: flex-start;
}
.aoc--minimal-card .aoc__top { padding: 8px 10px 2px; }
.aoc--minimal-card .aoc__timer { background: #f1f5f9; color: #475569; }
.aoc--minimal-card .aoc__timer--alert { background: #fee2e2; color: #dc2626; }
.aoc--minimal-card .aoc__body { align-items: flex-start; text-align: left; padding: 2px 10px 6px; }
.aoc--minimal-card .aoc__name { color: #1e293b; }
.aoc--minimal-card .aoc__valor-lbl { color: #64748b; }
.aoc--minimal-card .aoc__amount { color: #2563eb; }
.aoc--minimal-card .aoc__bottom { color: #64748b; border-top: 1px solid #f1f5f9; padding-top: 5px; align-self: stretch; }

/* ═══ 5. ticket (recibo) ═══ */
.aoc--ticket { border-radius: 0 0 10px 10px; background: #fff; border: 1.5px solid #d1d5db; border-top: none; box-shadow: 0 3px 10px rgba(0,0,0,.1); }
.aoc--ticket::before {
  content: ""; display: block; height: 12px; flex-shrink: 0;
  background: radial-gradient(circle at 50% 0%, transparent 6px, #fff 6px) 0 0 / 14px 12px repeat-x, #1e293b;
}
.aoc--ticket .aoc__top { padding: 6px 10px 2px; background: #f8fafc; border-bottom: 1px dashed #d1d5db; }
.aoc--ticket .aoc__timer { background: #e2e8f0; color: #475569; }
.aoc--ticket .aoc__timer--alert { background: #fee2e2; color: #dc2626; }
.aoc--ticket .aoc__body { padding: 8px 10px 4px; }
.aoc--ticket .aoc__name, .aoc--ticket .aoc__amount { color: #1e293b; font-family: monospace; }
.aoc--ticket .aoc__amount { font-weight: 900; }
.aoc--ticket .aoc__valor-lbl { color: #94a3b8; font-family: monospace; }
.aoc--ticket .aoc__bottom { color: #64748b; border-top: 1px dashed #d1d5db; font-family: monospace; }

/* ═══ 6. bubble ═══ */
.aoc--bubble {
  border-radius: 80px; width: 155px; aspect-ratio: .75; align-items: center;
  background: linear-gradient(145deg, #0ea5e9 0%, #0369a1 60%, #075985 100%);
  box-shadow: 0 8px 24px rgba(7,89,133,.38), inset 0 1px 0 rgba(255,255,255,.2);
  border: 2px solid rgba(14,165,233,.35);
}
.aoc--bubble .aoc__top { padding: 12px 10px 2px; justify-content: center; }
.aoc--bubble .aoc__timer { background: rgba(0,0,0,.3); color: #e0f2fe; }
.aoc--bubble .aoc__timer--alert { background: rgba(220,38,38,.8); color: #fff; }
.aoc--bubble .aoc__body { padding: 6px 10px; }
.aoc--bubble .aoc__name { color: #fff; text-shadow: 0 1px 4px rgba(0,0,0,.35); }
.aoc--bubble .aoc__valor-lbl { color: rgba(255,255,255,.7); }
.aoc--bubble .aoc__amount { color: #bae6fd; font-weight: 800; }
.aoc--bubble .aoc__top, .aoc--bubble .aoc__body, .aoc--bubble .aoc__bottom { align-self: stretch; }
.aoc--bubble .aoc__bottom { color: rgba(255,255,255,.85); padding-bottom: 12px; justify-content: center; }
.aoc--bubble .aoc__waiter { background: rgba(0,0,0,.25); padding: 2px 10px; border-radius: 10px; max-width: 90%; }

/* ═══ Tamaños: PC más grandes, celular más compactas ═══ */
@media (min-width: 769px) {
  .aoc-oval { width: 240px; height: 190px; }
  .aoc-oval__name { font-size: 24px; }
  .aoc-oval__amount { font-size: 15px; }
  .aoc-oval__valor-lbl { font-size: 8px; }
  .aoc-oval__timer, .aoc-oval__waiter { font-size: 12px; padding: 5px 13px; }
  .aoc-oval__timer { top: 16px; }
  .aoc-oval__waiter { bottom: 16px; }
  .aoc-oval__waiter-txt { max-width: 120px; }
}
@media (max-width: 768px) {
  .aoc { width: 148px; }
  .aoc--circular-gold { width: 155px; }
  .aoc--bubble { width: 140px; }
}
@media (max-width: 576px) {
  .aoc-oval { width: 160px; height: 126px; }
  .aoc-oval__name { font-size: 15px; }
  .aoc-oval__amount { font-size: 11px; }
  .aoc-oval__timer { top: 9px; }
  .aoc-oval__waiter { bottom: 9px; }
  .aoc-oval__waiter-txt { max-width: 76px; }
  .aoc { width: 152px; }
  .aoc--circular-gold { width: 165px; }
  .aoc--circular-gold .aoc__name { font-size: 14px; }
  .aoc--bubble { width: 140px; }
  .aoc__name { font-size: 14px; }
  .aoc__amount { font-size: 12px; }
}
</style>
