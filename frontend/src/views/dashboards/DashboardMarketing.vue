<template>
  <div>
    <KpiStrip :kpis="kpis" />
    <div class="dash-title">Dashboard — Agencia de Marketing</div>
  </div>
</template>
<script setup>
import KpiStrip from "@/components/dashboard/KpiStrip.vue"
const kpis = [
  { icon: "bi-kanban",          label: "Proyectos activos",  value: "—" },
  { icon: "bi-megaphone",       label: "Campañas activas",   value: "—" },
  { icon: "bi-people",          label: "Clientes",           value: "—" },
  { icon: "bi-list-check",      label: "Tareas pendientes",  value: "—" },
]
</script>
<style scoped>
.dash-title { padding: 20px 0 0; font-size: 18px; font-weight: 700; color: #1e293b; }
</style>
