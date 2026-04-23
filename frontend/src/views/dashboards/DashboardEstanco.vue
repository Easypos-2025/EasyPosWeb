<template>
  <div>
    <KpiStrip :kpis="kpis" />
    <div class="dash-title">Dashboard — Estanco / Licorería</div>
  </div>
</template>
<script setup>
import KpiStrip from "@/components/dashboard/KpiStrip.vue"
const kpis = [
  { icon: "bi-graph-up-arrow", label: "Ventas hoy",      value: "$ —" },
  { icon: "bi-box2",           label: "Productos vendidos", value: "—" },
  { icon: "bi-cash-stack",     label: "Caja actual",       value: "$ —" },
  { icon: "bi-people",         label: "Clientes hoy",      value: "—"  },
]
</script>
<style scoped>
.dash-title { padding: 20px 0 0; font-size: 18px; font-weight: 700; color: #1e293b; }
</style>
