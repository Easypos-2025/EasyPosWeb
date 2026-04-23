<template>
  <div class="dashboard-content">

    <!-- FRANJA DE INDICADORES -->
    <KpiStrip :kpis="kpis" :loading="false" />
    <div class="dash-title">Dashboard — Almacenes Moda</div>

    <!-- Área de contenido del perfil — se irá llenando según avance el módulo -->

  </div>
</template>

<script setup>
import KpiStrip from "@/components/dashboard/KpiStrip.vue"

const kpis = [
  { icon: "bi-graph-up-arrow",  label: "Ventas hoy",     value: "$ —" },
  { icon: "bi-box-seam",        label: "Productos activos", value: "—" },
  { icon: "bi-tags",            label: "Categorías",     value: "—" },
  { icon: "bi-people",          label: "Clientes hoy",   value: "—" }
]
</script>

<style scoped>
/* El padding lo provee .content en layout.css — no duplicar */
</style>
