<template>
  <div>
    <KpiStrip :kpis="kpis" :loading="loading" :showLabels="true" v-model="fechaKpi" />
  </div>
</template>
<script setup>
import KpiStrip from "@/components/dashboard/KpiStrip.vue"
import { useVentasKpis } from "@/composables/useVentasKpis"
const { kpis, loading, fechaKpi } = useVentasKpis()
</script>
<style scoped>
</style>
