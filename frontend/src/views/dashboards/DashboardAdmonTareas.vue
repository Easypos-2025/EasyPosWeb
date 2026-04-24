<template>
  <div>
    <KpiStrip :kpis="kpis" :loading="loading" />
    <div class="dash-title">Dashboard — Administrador de Tareas</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import KpiStrip from "@/components/dashboard/KpiStrip.vue"
import api from "@/services/apis"

const loading = ref(true)
const stats   = ref({
  total: 0, pendiente: 0, asignada: 0,
  progreso: 0, revision: 0, finalizada: 0,
  cancelada: 0, atrasadas: 0
})

const kpis = computed(() => [
  {
    icon:  "bi-hourglass-split",
    label: "Pendientes",
    value: stats.value.pendiente
  },
  {
    icon:  "bi-play-circle",
    label: "En progreso",
    value: stats.value.progreso
  },
  {
    icon:  "bi-exclamation-triangle",
    label: "Atrasadas",
    value: stats.value.atrasadas
  },
  {
    icon:  "bi-check2-circle",
    label: "Finalizadas",
    value: stats.value.finalizada
  },
])

onMounted(async () => {
  try {
    const res = await api.get("/tasks/stats")
    stats.value = res.data
  } catch {}
  loading.value = false
})
</script>

<style scoped>
.dash-title {
  padding: 20px 0 0;
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
}
</style>
