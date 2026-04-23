<template>
  <div>
    <KpiStrip :kpis="kpis" />
    <div class="dash-title">Dashboard — Droguería / Farmacia</div>
  </div>
</template>
<script setup>
import KpiStrip from "@/components/dashboard/KpiStrip.vue"
const kpis = [
  { icon: "bi-graph-up-arrow",  label: "Ventas hoy",              value: "$ —" },
  { icon: "bi-capsule",         label: "Medicamentos despachados", value: "—"   },
  { icon: "bi-file-medical",    label: "Recetas atendidas",        value: "—"   },
  { icon: "bi-exclamation-triangle", label: "Stock crítico",       value: "—"   },
]
</script>
<style scoped>
.dash-title { padding: 20px 0 0; font-size: 18px; font-weight: 700; color: #1e293b; }
</style>
