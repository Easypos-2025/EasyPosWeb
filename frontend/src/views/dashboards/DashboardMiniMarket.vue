<template>
  <div>
    <KpiStrip :kpis="kpis" :loading="loading" :showLabels="true" />
    <div class="dash-title">Dashboard — Mini-Market / Supermercado</div>
  </div>
</template>
<script setup>
import KpiStrip from "@/components/dashboard/KpiStrip.vue"
import { useVentasKpis } from "@/composables/useVentasKpis"
const { kpis, loading } = useVentasKpis()
</script>
<style scoped>
.dash-title { padding: 20px 0 0; font-size: 18px; font-weight: 700; color: #1e293b; }
</style>
