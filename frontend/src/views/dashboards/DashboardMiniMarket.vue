<template>
  <div>
    <KpiStrip :kpis="kpis" />
    <div class="dash-title">Dashboard — Mini-Market / Supermercado</div>
  </div>
</template>
<script setup>
import KpiStrip from "@/components/dashboard/KpiStrip.vue"
const kpis = [
  { icon: "bi-graph-up-arrow",      label: "Ventas hoy",          value: "$ —" },
  { icon: "bi-receipt",             label: "Tickets hoy",         value: "—"   },
  { icon: "bi-exclamation-triangle",label: "Productos bajo stock", value: "—"   },
  { icon: "bi-people",              label: "Clientes hoy",        value: "—"   },
]
</script>
<style scoped>
.dash-title { padding: 20px 0 0; font-size: 18px; font-weight: 700; color: #1e293b; }
</style>
