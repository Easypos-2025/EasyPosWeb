<template>
  <div v-if="bodega" class="ab">
    <i class="bi bi-boxes"></i>
    <div>
      <b>Solo consulta: {{ que }} los administra la bodega central «{{ bodega.nombre }}».</b>
      <span>Para crear o modificar, entre a la bodega y envíelos a esta sede.</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  bodega: { type: Object, default: null },
  que: { type: String, default: 'estos datos' },
})
</script>

<style scoped>
.ab { display: flex; gap: 10px; align-items: flex-start; background: #ecfeff; border: 1px solid #a5f3fc; color: #155e75;
  border-radius: 10px; padding: 10px 12px; margin: 0 0 12px; font-size: 13.5px; }
.ab i { font-size: 20px; flex-shrink: 0; }
.ab div { display: flex; flex-direction: column; gap: 2px; }
.ab span { font-size: 12.5px; }
@media (max-width: 768px) { .ab { font-size: 13px; } }
@media (max-width: 576px) { .ab { padding: 9px 10px; } .ab i { font-size: 18px; } }
</style>
