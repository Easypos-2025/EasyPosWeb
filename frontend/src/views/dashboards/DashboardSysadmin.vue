<template>
  <div>
    <KpiStrip :kpis="kpis" :loading="loading" />

    <div class="dash-title">Dashboard — SYSADMIN</div>

    <!-- ── Filtro compartido + accesos rápidos ── -->
    <div class="conn-toolbar">
      <div class="mode-toggle">
        <button :class="['btn-mode', mode === 'day' && 'active']" @click="setMode('day')">Día</button>
        <button :class="['btn-mode', mode === 'month' && 'active']" @click="setMode('month')">Mes</button>
      </div>
      <CustomDatePicker v-model="selDate" variant="dark" @update:modelValue="loadConnections" />
      <span v-if="connLoading" class="conn-loading-dot">⏳</span>
      <div class="toolbar-spacer"></div>
      <router-link to="/sysadmin/monitor" class="btn-monitor">
        <i class="bi bi-bar-chart-line"></i> Monitor de Ventas
      </router-link>
      <router-link to="/sysadmin/admin-pe" class="btn-monitor btn-monitor--pe">
        <i class="bi bi-lightning-charge-fill"></i> Admin POS Electrónico
      </router-link>
    </div>

    <!-- ── Cards conexiones ── -->
    <div class="conn-grid">

      <!-- Empresas conectadas -->
      <div class="conn-card">
        <div class="conn-card-header">
          <i class="bi bi-buildings"></i>
          Empresas conectadas
          <span class="conn-badge">{{ connections.companies.length }}</span>
        </div>
        <div class="conn-table-wrap">
          <table class="conn-table" v-if="connections.companies.length">
            <thead>
              <tr><th>Empresa</th><th>Logins</th><th>Último</th></tr>
            </thead>
            <tbody>
              <tr v-for="c in connections.companies" :key="c.company_id">
                <td>{{ c.company_name }}</td>
                <td class="text-center">{{ c.login_count }}</td>
                <td class="text-muted">{{ fmtTime(c.last_login) }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="conn-empty">Sin registros para este período</div>
        </div>
      </div>

      <!-- Usuarios conectados -->
      <div class="conn-card">
        <div class="conn-card-header">
          <i class="bi bi-people"></i>
          Usuarios conectados
          <span class="conn-badge">{{ connections.users.length }}</span>
        </div>
        <div class="conn-table-wrap">
          <table class="conn-table" v-if="connections.users.length">
            <thead>
              <tr><th>Nombre</th><th>Empresa</th><th>Hora</th><th>IP</th></tr>
            </thead>
            <tbody>
              <tr v-for="u in connections.users" :key="u.user_id + u.login_time">
                <td>{{ u.name }}</td>
                <td class="text-muted">{{ u.company_name }}</td>
                <td class="text-muted">{{ fmtTime(u.login_time) }}</td>
                <td class="text-muted">{{ u.ip }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="conn-empty">Sin registros para este período</div>
        </div>
      </div>

    </div>


  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import KpiStrip from "@/components/dashboard/KpiStrip.vue"
import CustomDatePicker from "@/components/common/CustomDatePicker.vue"
import api from "@/services/apis"

const loading     = ref(true)
const connLoading = ref(false)
const stats       = ref({ total_companies: 0, total_users: 0, total_assets: 0, total_tasks: 0 })
const mode        = ref("day")
const selDate     = ref(new Date().toLocaleDateString("en-CA", { timeZone: "America/Bogota" }))
const connections = ref({ companies: [], users: [] })

const kpis = computed(() => [
  { icon: "bi-buildings",       label: "Asociados registrados", value: stats.value.total_companies },
  { icon: "bi-people",          label: "Usuarios totales",      value: stats.value.total_users     },
  { icon: "bi-box-seam",        label: "Activos registrados",   value: stats.value.total_assets    },
  { icon: "bi-clipboard-check", label: "Tareas registradas",    value: stats.value.total_tasks     },
])

function setMode(m) {
  mode.value = m
  loadConnections()
}

async function loadConnections() {
  connLoading.value = true
  try {
    const res = await api.get("/dashboard/sysadmin/connections", {
      params: { date: selDate.value, mode: mode.value }
    })
    connections.value = res.data
  } catch {}
  connLoading.value = false
}

function fmtTime(iso) {
  if (!iso) return "—"
  const d = new Date(iso)
  return d.toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" })
}

onMounted(async () => {
  try {
    const res = await api.get("/dashboard/stats")
    stats.value = res.data
  } catch {}
  loading.value = false
  await loadConnections()
})
</script>

<style scoped>
.dash-title {
  padding: 20px 0 12px;
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
}

/* ── toolbar ── */
.conn-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.toolbar-spacer { flex: 1; }

.mode-toggle {
  display: flex;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  overflow: hidden;
}

.btn-mode {
  padding: 7px 18px;
  background: #fff;
  border: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
  transition: background 0.15s, color 0.15s;
}
.btn-mode.active {
  background: #2563eb;
  color: #fff;
}
.btn-mode:hover:not(.active) { background: #f1f5f9; }

.conn-loading-dot { font-size: 18px; animation: pulse 1s infinite; }
@keyframes pulse { 0%,100% { opacity: 1 } 50% { opacity: .3 } }

/* ── grid ── */
.conn-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.conn-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
}

.conn-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  font-weight: 600;
  font-size: 14px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  color: #1e293b;
}

.conn-badge {
  margin-left: auto;
  background: #2563eb;
  color: #fff;
  border-radius: 20px;
  padding: 2px 10px;
  font-size: 12px;
  font-weight: 700;
}

.conn-table-wrap {
  max-height: 300px;
  overflow-y: auto;
}

.conn-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.conn-table thead tr {
  background: #f1f5f9;
  position: sticky;
  top: 0;
  z-index: 1;
}
.conn-table th {
  padding: 8px 12px;
  text-align: left;
  font-weight: 600;
  color: #475569;
  font-size: 12px;
  border-bottom: 1px solid #e2e8f0;
}
.conn-table td {
  padding: 7px 12px;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
}
.conn-table tbody tr:hover { background: #f8fafc; }
.text-center { text-align: center; }
.text-muted  { color: #94a3b8 !important; }

.conn-empty {
  padding: 24px;
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
}

/* ── botón monitor ── */
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

/* ── responsive ── */
@media (max-width: 768px) {
  .conn-grid { grid-template-columns: 1fr; }
  .conn-toolbar { gap: 8px; }
  .toolbar-spacer { display: none; }
  .btn-monitor { flex: 1; justify-content: center; }
}

@media (max-width: 576px) {
  .conn-table th:nth-child(3),
  .conn-table td:nth-child(3) { display: none; }
  .btn-mode { padding: 6px 12px; font-size: 12px; }
  .btn-monitor { font-size: 12px; padding: 8px 14px; }
}
</style>
