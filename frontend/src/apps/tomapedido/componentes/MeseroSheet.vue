<template>
  <!-- A quién se le asigna el pedido: los meseros del día que registró la caja (un mismo
       dispositivo lo usan varios meseros). Sin escoger no se puede montar el pedido. -->
  <div class="velo" @click.self="cerrable && $emit('cerrar')">
    <div class="hoja">
      <div class="hoja__cab">
        <h2>¿Qué {{ t("mesero") }} toma el pedido?</h2>
        <button v-if="cerrable" class="cerrar" @click="$emit('cerrar')"><Icono nombre="cerrar" /></button>
      </div>
      <div class="hoja__cuerpo">
        <p v-if="titulo" class="nota">{{ titulo }}</p>
        <div class="meseros">
          <button v-for="m in meseros" :key="m.cod" class="mesero" :class="{ 'mesero--activo': m.cod === actual }"
                  @click="$emit('escoger', m)">
            <span class="mesero__ico"><Icono nombre="usuario" :tam="20" /></span>
            <b>{{ m.nombre }}</b>
            <Icono v-if="m.cod === actual" nombre="check" :tam="18" />
          </button>
        </div>
      </div>
      <div v-if="!cerrable" class="hoja__pie">
        <button class="btn btn--bloque" @click="$emit('volver')"><Icono nombre="atras" :tam="18" /> Volver</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import Icono from "./Icono.vue"
import { t } from "../textos"

defineProps({
  meseros: { type: Array, required: true },
  actual: { type: Number, default: null },
  titulo: { type: String, default: "" },
  cerrable: { type: Boolean, default: true },     // la primera vez es obligatorio escoger
})
defineEmits(["escoger", "cerrar", "volver"])
</script>

<style scoped>
.nota { margin: 0 0 12px; color: var(--texto-suave); font-size: 14px; }
.meseros { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.mesero { display: flex; align-items: center; gap: 10px; min-height: 58px; padding: 10px 12px; text-align: left;
          border-radius: 12px; border: 1.5px solid var(--borde); background: #fff; font-size: 15px; }
.mesero b { flex: 1; min-width: 0; overflow-wrap: anywhere; line-height: 1.2; }
.mesero__ico { width: 36px; height: 36px; flex-shrink: 0; border-radius: 50%; background: var(--azul-claro); color: var(--azul);
               display: inline-flex; align-items: center; justify-content: center; }
.mesero--activo { border-color: var(--azul); background: var(--azul-claro); color: var(--navy); }

@media (max-width: 768px) {
  .mesero { min-height: 54px; }
}
@media (max-width: 576px) {
  .meseros { grid-template-columns: 1fr; }
  .mesero { font-size: 16px; }
}
</style>
