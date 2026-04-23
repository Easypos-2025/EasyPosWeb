<template>
  <div class="dashboard-content">

    <KpiStrip :kpis="kpis" :loading="false" />
    <div class="dash-title">Dashboard — Restaurante</div>

    <!-- Área de contenido del perfil — se irá llenando según avance el módulo -->

  </div>
</template>

<script setup>
import KpiStrip from "@/components/dashboard/KpiStrip.vue"

// Placeholders hasta implementar el módulo de ventas / pedidos
const kpis = [
  { icon: "bi-graph-up-arrow",  label: "Ventas hoy",     value: "$ —" },
  { icon: "bi-receipt",         label: "Pedidos hoy",    value: "—" },
  { icon: "bi-table",           label: "Mesas activas",  value: "—" },
  { icon: "bi-bullseye",        label: "Meta del día",   value: "—%" }
]
</script>

<style scoped>
/* El padding lo provee .content en layout.css — no duplicar */
</style>
