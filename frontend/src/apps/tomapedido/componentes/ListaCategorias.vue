<template>
  <!-- Categorías en lista vertical (columna fija en PC y panel lateral en celular/tablet) -->
  <nav class="categorias">
    <button v-for="(c, i) in categorias" :key="c.id" class="categoria"
            :class="{ 'categoria--activa': c.id === activa }" :style="c.id === activa ? null : estilo(i)"
            @click="$emit('escoger', c.id)">
      <img v-if="c.foto" :src="c.foto" class="categoria__foto" alt="" loading="lazy" />
      <span class="categoria__nombre">{{ c.nombre }}</span>
      <small>{{ conteo[c.id] || 0 }}</small>
    </button>
  </nav>
</template>

<script setup>
import { colorAlterno } from "../formato"

const props = defineProps({
  categorias: { type: Array, default: () => [] },
  activa: { type: Number, default: null },
  conteo: { type: Object, default: () => ({}) },
  colores: { type: Array, default: () => [] },     // primario y secundario del escritorio
})
defineEmits(["escoger"])

const estilo = (i) => colorAlterno(props.colores, i)
</script>

<style scoped>
.categorias { display: flex; flex-direction: column; gap: 6px; }
.categoria {
  display: flex; align-items: center; gap: 10px;
  min-height: 52px; padding: 6px 12px; border: 0; border-radius: 12px; background: #fff;
  box-shadow: var(--sombra); text-align: left; font-weight: 600;
}
.categoria__foto { width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; object-fit: cover; background: #fff; }
.categoria__nombre { flex: 1; min-width: 0; word-break: break-word; }
.categoria small { flex-shrink: 0; padding: 2px 8px; border-radius: 999px; background: rgba(255, 255, 255, .7); color: var(--texto-suave); font-size: 12px; }
.categoria--activa { background: var(--navy); color: #fff; }
.categoria--activa small { background: rgba(255, 255, 255, .18); color: #fff; }

@media (max-width: 576px) {
  .categoria { min-height: 50px; }
  .categoria__foto { width: 36px; height: 36px; }
}
@media (max-width: 768px) {
  .categorias { gap: 5px; }
}
</style>
