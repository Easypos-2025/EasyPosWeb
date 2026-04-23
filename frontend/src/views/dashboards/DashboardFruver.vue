<template>
  <div>
    <KpiStrip :kpis="kpis" />
    <div class="dash-title">Dashboard — Fruver</div>
  </div>
</template>
<script setup>
import KpiStrip from "@/components/dashboard/KpiStrip.vue"
const kpis = [
  { icon: "bi-graph-up-arrow", label: "Ventas hoy",         value: "$ —"  },
  { icon: "bi-basket",         label: "Kg / Unid vendidos",  value: "—"    },
  { icon: "bi-tags",           label: "Productos activos",   value: "—"    },
  { icon: "bi-cart-check",     label: "Pedidos pendientes",  value: "—"    },
]
</script>
<style scoped>
.dash-title { padding: 20px 0 0; font-size: 18px; font-weight: 700; color: #1e293b; }
</style>
