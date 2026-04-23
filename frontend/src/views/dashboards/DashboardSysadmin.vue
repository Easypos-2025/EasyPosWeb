<template>
  <div>
    <KpiStrip :kpis="kpis" :loading="loading" />
    <div class="dash-title">Dashboard — SYSADMIN</div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from "vue"
import KpiStrip from "@/components/dashboard/KpiStrip.vue"
import api from "@/services/apis"

const loading = ref(true)
const stats   = ref({ total_companies: 0, total_users: 0, total_assets: 0, total_tasks: 0 })

const kpis = computed(() => [
  { icon: "bi-buildings",       label: "Asociados registrados", value: stats.value.total_companies },
  { icon: "bi-people",          label: "Usuarios totales",      value: stats.value.total_users     },
  { icon: "bi-box-seam",        label: "Activos registrados",   value: stats.value.total_assets    },
  { icon: "bi-clipboard-check", label: "Tareas registradas",    value: stats.value.total_tasks     },
])

onMounted(async () => {
  try {
    const res = await api.get("/dashboard/stats")
    stats.value = res.data
  } catch {}
  loading.value = false
})
</script>
<style scoped>
.dash-title { padding: 20px 0 0; font-size: 18px; font-weight: 700; color: #1e293b; }
</style>
