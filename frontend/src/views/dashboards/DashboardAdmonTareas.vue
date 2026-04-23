<template>
  <div class="dashboard-content">

    <KpiStrip :kpis="kpis" :loading="loading" />
    <div class="dash-title">Dashboard — Administrador de Tareas</div>

    <!-- Área de contenido del perfil — se irá llenando según avance el módulo -->

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import KpiStrip from "@/components/dashboard/KpiStrip.vue"
import api from "@/services/apis"

const loading = ref(true)
const tasks   = ref([])

const kpis = computed(() => [
  {
    icon:  "bi-clipboard-data",
    label: "Total tareas",
    value: tasks.value.length
  },
  {
    icon:  "bi-hourglass-split",
    label: "Pendientes",
    value: tasks.value.filter(t => isPending(t)).length
  },
  {
    icon:  "bi-play-circle",
    label: "En ejecución",
    value: tasks.value.filter(t => isInProgress(t)).length
  },
  {
    icon:  "bi-check2-circle",
    label: "Completadas",
    value: tasks.value.filter(t => isDone(t)).length
  }
])

function isPending(t)    { return !t.status || t.status.toLowerCase().includes("pendiente") }
function isInProgress(t) { return t.status?.toLowerCase().includes("ejecuci") || t.status?.toLowerCase().includes("progreso") }
function isDone(t)       { return t.status?.toLowerCase().includes("complet") || t.status?.toLowerCase().includes("finaliz") }

onMounted(async () => {
  try {
    const res = await api.get("/tasks/")
    tasks.value = res.data
  } catch {}
  loading.value = false
})
</script>

<style scoped>
/* El padding lo provee .content en layout.css — no duplicar */
</style>
