<template>
  <div>
    <KpiStrip :kpis="kpis" />
    <div class="dash-title">Dashboard — Peluquería / Barbería</div>
  </div>
</template>
<script setup>
import KpiStrip from "@/components/dashboard/KpiStrip.vue"
const kpis = [
  { icon: "bi-scissors",       label: "Servicios hoy",       value: "—"   },
  { icon: "bi-person-check",   label: "Clientes atendidos",  value: "—"   },
  { icon: "bi-graph-up-arrow", label: "Ingresos hoy",        value: "$ —" },
  { icon: "bi-calendar-check", label: "Turnos pendientes",   value: "—"   },
]
</script>
<style scoped>
.dash-title { padding: 20px 0 0; font-size: 18px; font-weight: 700; color: #1e293b; }
</style>
