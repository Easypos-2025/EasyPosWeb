<template>
  <!-- Vista en desarrollo (Registro Gastos · Compras · Otros Ingresos · Otros Egresos) -->
  <div class="mp-page">
    <h2 class="mp-title"><i :class="['bi', icono, 'me-2']"></i>{{ moduleName || $route.meta.title }}</h2>
    <div class="mp-empty">
      <i class="bi bi-cone-striped"></i>
      <p>Esta vista está en desarrollo.</p>
      <small>Los movimientos que se registren aquí se amarran al turno de caja abierto (Id_Caja) y se reflejan en el Cuadre de Caja.</small>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useModuleName } from '@/composables/useModuleName'

const route = useRoute()
const { moduleName } = useModuleName()
const icono = computed(() => route.meta.icon || 'bi-cash-stack')
</script>

<style scoped>
.mp-page { padding: 20px 24px 32px; }
.mp-title { font-size: 22px; font-weight: 800; color: #1e293b; margin: 0 0 16px; }
.mp-empty { display: flex; flex-direction: column; align-items: center; text-align: center; gap: 6px; padding: 60px 20px;
            background: #fff; border: 1.5px dashed #cbd5e1; border-radius: 14px; color: #64748b; }
.mp-empty i { font-size: 40px; color: #f59e0b; }
.mp-empty p { font-size: 16px; font-weight: 700; color: #334155; margin: 0; }
.mp-empty small { max-width: 420px; }
@media (max-width: 768px) { .mp-page { padding: 14px 12px 24px; } .mp-title { font-size: 19px; } }
@media (max-width: 576px) { .mp-empty { padding: 40px 14px; } }
</style>
