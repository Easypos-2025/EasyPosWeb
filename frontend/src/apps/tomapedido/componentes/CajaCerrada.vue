<template>
  <!-- Caja cerrada (Cerrar_Dia = 1) o con otra fecha: no se puede comandar hasta abrir turno en el
       escritorio. Pantalla completa, como la de "Sin conexión": muchos usuarios no leen los avisos. -->
  <div class="cc" role="alertdialog" aria-live="assertive">
    <div class="cc__caja">
      <div class="cc__icono"><Icono nombre="candado" :tam="44" /></div>
      <h2>La caja está cerrada</h2>
      <!-- Con otra fecha se explica cuál; si solo está cerrada, el título ya lo dice -->
      <p class="cc__sub">{{ caja.motivo === "fecha" && caja.mensaje ? caja.mensaje
        : "Abra el turno en el programa de escritorio para tomar pedidos." }}</p>
      <ol class="cc__pasos">
        <li>Pida en caja que <b>abran el turno</b> en el programa de escritorio.</li>
        <li>Esta pantalla se quita sola cuando la caja quede abierta.</li>
      </ol>
      <button class="btn btn--bloque cc__btn" :disabled="probando" @click="$emit('reintentar')">
        <span v-if="probando" class="giro" style="width:20px;height:20px;border-width:2px"></span>
        <template v-else><Icono nombre="refrescar" /> Ya abrieron, reintentar</template>
      </button>
      <p class="cc__auto">Se revisa automáticamente cada pocos segundos.</p>
      <VersionAgente />
    </div>
  </div>
</template>

<script setup>
import Icono from "./Icono.vue"
import VersionAgente from "./VersionAgente.vue"
import { caja } from "../api"

defineProps({ probando: { type: Boolean, default: false } })
defineEmits(["reintentar"])
</script>

<style scoped>
.cc { position: fixed; inset: 0; z-index: 89000; display: flex; align-items: center; justify-content: center;
      padding: 16px; background: rgba(15, 23, 42, .9); }
.cc__caja { width: 100%; max-width: 440px; background: #fff; border-radius: 20px; padding: 26px 22px; text-align: center;
            box-shadow: 0 20px 50px rgba(0, 0, 0, .35); }
.cc__icono { width: 80px; height: 80px; margin: 0 auto 12px; border-radius: 50%; background: var(--ambar-claro); color: #b45309;
             display: flex; align-items: center; justify-content: center; }
.cc h2 { margin: 0 0 8px; color: var(--navy); font-size: 22px; }
.cc__sub { margin: 0 0 14px; color: var(--texto-suave); font-size: 15px; }
.cc__pasos { text-align: left; margin: 0 0 18px; padding-left: 22px; font-size: 15px; line-height: 1.45; }
.cc__pasos li { margin-bottom: 8px; }
.cc__btn { background: var(--navy); color: #fff; }
.cc__auto { margin: 10px 0 0; font-size: 12px; color: var(--texto-suave); }

@media (max-width: 768px) {
  .cc__pasos { font-size: 14px; }
}
@media (max-width: 576px) {
  .cc__caja { padding: 22px 16px; }
  .cc h2 { font-size: 20px; }
}
</style>
