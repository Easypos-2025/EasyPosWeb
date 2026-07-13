<template>
  <div>
    <KpiStrip :kpis="kpis" :loading="loading" />
    <div class="dash-title">Dashboard — SYSADMIN</div>
    <div class="quick-links">
      <router-link to="/sysadmin/monitor" class="btn-monitor">
        <i class="bi bi-bar-chart-line"></i> Monitor de Ventas
      </router-link>
      <router-link to="/sysadmin/admin-pe" class="btn-monitor btn-monitor--pe">
        <i class="bi bi-lightning-charge-fill"></i> Admin POS Electrónico
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue"
import KpiStrip from "@/components/dashboard/KpiStrip.vue"
import api from "@/services/apis"

const loading     = ref(true)
const stats       = ref({ total_companies: 0 })
const connections = ref({ companies: [], users: [] })
let _liveTimer    = null

const LIVE_INTERVAL = 20000

const kpis = computed(() => [
  { icon: "bi-buildings",   label: "Asociados registrados",  value: stats.value.total_companies        },
  { icon: "bi-building",    label: "Empresas activas ahora", value: connections.value.companies.length, to: "/sysadmin/sesiones" },
  { icon: "bi-people-fill", label: "Usuarios activos ahora", value: connections.value.users.length,     to: "/sysadmin/sesiones" },
])

async function loadLiveCounts() {
  try {
    const res = await api.get("/dashboard/sysadmin/active-sessions")
    connections.value = res.data
  } catch {}
}

onMounted(async () => {
  try {
    const res = await api.get("/dashboard/stats")
    stats.value = res.data
  } catch {}
  loading.value = false
  await loadLiveCounts()
  _liveTimer = setInterval(loadLiveCounts, LIVE_INTERVAL)
})

onUnmounted(() => clearInterval(_liveTimer))

</script>

<style scoped>
.dash-title {
  padding: 20px 0 12px;
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
}

.quick-links {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.btn-monitor {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 22px;
  background: #0f172a;
  color: #fff;
  border-radius: 8px;
  font-weight: 600;
  font-size: 14px;
  text-decoration: none;
  transition: background 0.15s;
}
.btn-monitor:hover { background: #1e3a5f; color: #fff; }
.btn-monitor--pe { background: #92400e; }
.btn-monitor--pe:hover { background: #78350f; color: #fff; }

@media (max-width: 768px) {
  .btn-monitor { flex: 1; justify-content: center; }
}
@media (max-width: 576px) {
  .btn-monitor { font-size: 12px; padding: 8px 14px; }
}
</style>
