<template>
  <div>
    <KpiStrip :kpis="kpis" />
    <div class="dash-title">Dashboard — Almacén Lujos y Autos</div>
  </div>
</template>
<script setup>
import KpiStrip from "@/components/dashboard/KpiStrip.vue"
const kpis = [
  { icon: "bi-graph-up-arrow", label: "Ventas hoy",         value: "$ —" },
  { icon: "bi-car-front",      label: "Productos vendidos",  value: "—"   },
  { icon: "bi-file-earmark",   label: "Cotizaciones",        value: "—"   },
  { icon: "bi-exclamation-circle", label: "Stock bajo",      value: "—"   },
]
</script>
<style scoped>
.dash-title { padding: 20px 0 0; font-size: 18px; font-weight: 700; color: #1e293b; }
</style>
