<template>
  <div>
    <KpiStrip :kpis="kpis" />
    <div class="dash-title">Dashboard — Distribuidora</div>
  </div>
</template>
<script setup>
import KpiStrip from "@/components/dashboard/KpiStrip.vue"
const kpis = [
  { icon: "bi-truck",           label: "Pedidos hoy",         value: "—"   },
  { icon: "bi-check2-all",      label: "Entregas realizadas", value: "—"   },
  { icon: "bi-credit-card",     label: "Cartera",             value: "$ —" },
  { icon: "bi-box-seam",        label: "Productos activos",   value: "—"   },
]
</script>
<style scoped>
.dash-title { padding: 20px 0 0; font-size: 18px; font-weight: 700; color: #1e293b; }
</style>
