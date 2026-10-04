<template>
  <!-- Aviso a pantalla completa: muchos usuarios no leen los mensajes y creen que "no funciona" -->
  <div class="sc" role="alertdialog" aria-live="assertive">
    <div class="sc__caja">
      <div class="sc__icono"><Icono nombre="wifi" :tam="44" /></div>
      <h2>Sin conexión con la caja</h2>
      <p class="sc__sub">Este dispositivo no logra comunicarse con el equipo de caja{{ desde ? ` (desde las ${desde})` : "" }}.
        Mientras tanto no se pueden tomar pedidos.</p>
      <ol class="sc__pasos">
        <li>Verifique que este dispositivo esté conectado al <b>wifi del negocio</b> (no a datos móviles).</li>
        <li>Verifique que el <b>equipo de caja esté encendido</b>.</li>
        <li>Si sigue igual, <b>avise en caja</b>: el programa EasyPos Agente debe estar abierto.</li>
      </ol>
      <button class="btn btn--bloque sc__btn" :disabled="probando" @click="$emit('reintentar')">
        <span v-if="probando" class="giro" style="width:20px;height:20px;border-width:2px"></span>
        <template v-else><Icono nombre="refrescar" /> Reintentar ahora</template>
      </button>
      <p class="sc__auto">Se vuelve a intentar automáticamente cada pocos segundos.</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue"
import Icono from "./Icono.vue"
import { conexion } from "../api"

defineProps({ probando: { type: Boolean, default: false } })
defineEmits(["reintentar"])

const desde = computed(() => conexion.desde
  ? conexion.desde.toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" }) : "")
</script>

<style scoped>
.sc { position: fixed; inset: 0; z-index: 90000; display: flex; align-items: center; justify-content: center;
      padding: 16px; background: rgba(127, 29, 29, .92); }
.sc__caja { width: 100%; max-width: 440px; background: #fff; border-radius: 20px; padding: 26px 22px; text-align: center;
            box-shadow: 0 20px 50px rgba(0, 0, 0, .35); animation: pulso 2s ease-in-out infinite; }
@keyframes pulso { 50% { box-shadow: 0 20px 60px rgba(220, 38, 38, .55); } }
.sc__icono { width: 80px; height: 80px; margin: 0 auto 12px; border-radius: 50%; background: var(--rojo-claro); color: var(--rojo);
             display: flex; align-items: center; justify-content: center; }
.sc h2 { margin: 0 0 8px; color: var(--rojo); font-size: 22px; }
.sc__sub { margin: 0 0 14px; color: var(--texto-suave); font-size: 15px; }
.sc__pasos { text-align: left; margin: 0 0 18px; padding-left: 22px; font-size: 15px; line-height: 1.45; }
.sc__pasos li { margin-bottom: 8px; }
.sc__btn { background: var(--rojo); color: #fff; }
.sc__auto { margin: 10px 0 0; font-size: 12px; color: var(--texto-suave); }

@media (max-width: 576px) {
  .sc__caja { padding: 22px 16px; }
  .sc h2 { font-size: 20px; }
}
@media (max-width: 768px) {
  .sc__pasos { font-size: 14px; }
}
</style>
