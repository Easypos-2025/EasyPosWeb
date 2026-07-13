<template>
  <div>
    <!-- ── Toolbar ── -->
    <div class="sl-toolbar">
      <div class="mode-toggle">
        <button :class="['btn-mode', mode === 'live'  && 'active']" @click="setMode('live')">
          <span v-if="mode === 'live'" class="live-dot"></span>Ahora
        </button>
        <button :class="['btn-mode', mode === 'day'   && 'active']" @click="setMode('day')">Día</button>
        <button :class="['btn-mode', mode === 'month' && 'active']" @click="setMode('month')">Mes</button>
      </div>
      <CustomDatePicker
        v-if="mode !== 'live'"
        v-model="selDate"
        @update:modelValue="loadConnections"
      />
      <span v-if="connLoading" class="loading-dot">⏳</span>
      <span v-if="mode === 'live' && !connLoading" class="live-status">
        <span v-if="lastUpdated" class="live-updated">{{ fmtTime(lastUpdated) }}</span>
        <span class="live-countdown">· actualiza en {{ countdown }}s</span>
      </span>
    </div>

    <!-- ── Cards ── -->
    <div class="sl-grid">

      <!-- Empresas -->
      <div class="sl-card">
        <div class="sl-card-header">
          <i class="bi bi-buildings"></i>
          <span>{{ mode === 'live' ? 'Empresas activas ahora' : 'Empresas conectadas' }}</span>
          <span class="sl-badge">{{ connections.companies.length }}</span>
        </div>
        <div class="sl-table-wrap">
          <table class="sl-table" v-if="connections.companies.length">
            <thead>
              <tr v-if="mode === 'live'">
                <th>Empresa</th><th class="tc">Usuarios</th><th>Activo hace</th>
              </tr>
              <tr v-else>
                <th>Empresa</th><th class="tc">Accesos</th><th>Último acceso</th>
              </tr>
            </thead>
            <tbody>
              <template v-if="mode === 'live'">
                <tr v-for="c in connections.companies" :key="c.id_company">
                  <td>{{ c.company_name }}</td>
                  <td class="tc"><span class="users-chip">{{ c.active_users }}</span></td>
                  <td class="tm">{{ fmtRelative(c.last_activity) }}</td>
                </tr>
              </template>
              <template v-else>
                <tr v-for="c in connections.companies" :key="c.id_company">
                  <td>{{ c.company_name }}</td>
                  <td class="tc">{{ c.login_count }}</td>
                  <td class="tm">{{ fmtDateTime(c.last_login) }}</td>
                </tr>
              </template>
            </tbody>
          </table>
          <div v-else class="sl-empty">
            {{ mode === 'live' ? 'Sin sesiones activas en este momento' : 'Sin registros para este período' }}
          </div>
        </div>
      </div>

      <!-- Usuarios -->
      <div class="sl-card">
        <div class="sl-card-header">
          <i class="bi bi-people"></i>
          <span>{{ mode === 'live' ? 'Usuarios activos ahora' : 'Usuarios conectados' }}</span>
          <span class="sl-badge">{{ connections.users.length }}</span>
        </div>
        <div class="sl-table-wrap">
          <table class="sl-table" v-if="connections.users.length">
            <thead>
              <tr v-if="mode === 'live'">
                <th>Nombre</th><th>Empresa</th><th>Activo hace</th><th>IP</th>
              </tr>
              <tr v-else>
                <th>Nombre</th><th>Empresa</th><th>Hora</th><th>IP</th>
              </tr>
            </thead>
            <tbody>
              <template v-if="mode === 'live'">
                <tr v-for="u in connections.users" :key="u.user_id">
                  <td>{{ u.name }}</td>
                  <td class="tm">{{ u.company_name }}</td>
                  <td class="tm">{{ fmtRelative(u.last_seen) }}</td>
                  <td class="tm ip-cell">{{ u.ip }}</td>
                </tr>
              </template>
              <template v-else>
                <tr v-for="u in connections.users" :key="u.user_id + u.login_time">
                  <td>{{ u.name }}</td>
                  <td class="tm">{{ u.company_name }}</td>
                  <td class="tm">{{ fmtTime(u.login_time) }}</td>
                  <td class="tm ip-cell">{{ u.ip }}</td>
                </tr>
              </template>
            </tbody>
          </table>
          <div v-else class="sl-empty">
            {{ mode === 'live' ? 'Sin sesiones activas en este momento' : 'Sin registros para este período' }}
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue"
import CustomDatePicker from "@/components/common/CustomDatePicker.vue"
import api from "@/services/apis"

const connLoading = ref(false)
const mode        = ref("live")
const selDate     = ref(new Date().toLocaleDateString("en-CA", { timeZone: "America/Bogota" }))
const connections = ref({ companies: [], users: [] })
const countdown   = ref(20)
const lastUpdated = ref(null)
let _liveTimer    = null
let _cTimer       = null

const LIVE_INTERVAL = 20000

function startCountdown() {
  clearInterval(_cTimer)
  countdown.value = LIVE_INTERVAL / 1000
  _cTimer = setInterval(() => { countdown.value = Math.max(0, countdown.value - 1) }, 1000)
}

function setMode(m) {
  mode.value = m
  clearInterval(_liveTimer)
  clearInterval(_cTimer)
  _liveTimer = null
  loadConnections()
  if (m === "live") {
    _liveTimer = setInterval(loadConnections, LIVE_INTERVAL)
    startCountdown()
  }
}

async function loadConnections() {
  connLoading.value = true
  try {
    if (mode.value === "live") {
      const res = await api.get("/dashboard/sysadmin/active-sessions")
      connections.value = res.data
      lastUpdated.value = new Date().toISOString()
      startCountdown()
    } else {
      const res = await api.get("/dashboard/sysadmin/connections", {
        params: { date: selDate.value, mode: mode.value }
      })
      connections.value = res.data
    }
  } catch {}
  connLoading.value = false
}

function fmtTime(iso) {
  if (!iso) return "—"
  return new Date(iso).toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" })
}

function fmtDateTime(iso) {
  if (!iso) return "—"
  const d = new Date(iso)
  return d.toLocaleDateString("es-CO", { day: "2-digit", month: "2-digit" }) + " " +
         d.toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" })
}

function fmtRelative(iso) {
  if (!iso) return "—"
  const mins = Math.floor((Date.now() - new Date(iso).getTime()) / 60000)
  if (mins < 1) return "justo ahora"
  if (mins === 1) return "hace 1 min"
  return `hace ${mins} min`
}

onMounted(async () => {
  await loadConnections()
  _liveTimer = setInterval(loadConnections, LIVE_INTERVAL)
  startCountdown()
})

onUnmounted(() => {
  clearInterval(_liveTimer)
  clearInterval(_cTimer)
})
</script>

<style scoped>
/* ── toolbar ── */
.sl-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.mode-toggle {
  display: flex;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  overflow: hidden;
}

.btn-mode {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 18px;
  background: #fff;
  border: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
  transition: background 0.15s, color 0.15s;
}
.btn-mode.active { background: #2563eb; color: #fff; }
.btn-mode:hover:not(.active) { background: #f1f5f9; }

.live-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #22c55e;
  display: inline-block;
  animation: live-pulse 1.4s ease-in-out infinite;
}
@keyframes live-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.4; transform: scale(0.7); }
}

.loading-dot { font-size: 18px; animation: pulse 1s infinite; }
@keyframes pulse { 0%,100% { opacity: 1 } 50% { opacity: .3 } }

.live-status { display: inline-flex; align-items: center; gap: 4px; font-size: 12px; color: #64748b; }
.live-updated { font-weight: 600; color: #22c55e; }
.live-countdown { color: #94a3b8; }

/* ── grid ── */
.sl-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.sl-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
}

.sl-card-header {
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

.sl-badge {
  margin-left: auto;
  background: #2563eb;
  color: #fff;
  border-radius: 20px;
  padding: 2px 10px;
  font-size: 12px;
  font-weight: 700;
}

.sl-table-wrap {
  max-height: calc(100vh - 260px);
  overflow-y: auto;
}

.sl-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.sl-table thead tr {
  background: #f1f5f9;
  position: sticky;
  top: 0;
  z-index: 1;
}
.sl-table th {
  padding: 8px 12px;
  text-align: left;
  font-weight: 600;
  color: #475569;
  font-size: 12px;
  border-bottom: 1px solid #e2e8f0;
}
.sl-table td {
  padding: 7px 12px;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
}
.sl-table tbody tr:hover { background: #f8fafc; }

.tc { text-align: center; }
.tm { color: #94a3b8; }
.ip-cell { font-family: monospace; font-size: 11px; }

.users-chip {
  display: inline-block;
  background: #dcfce7;
  color: #15803d;
  font-weight: 700;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 20px;
}

.sl-empty {
  padding: 24px;
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
}

/* ── responsive ── */
@media (max-width: 768px) {
  .sl-grid { grid-template-columns: 1fr; }
  .sl-toolbar { gap: 8px; }
}

@media (max-width: 576px) {
  .sl-table th:nth-child(4),
  .sl-table td:nth-child(4) { display: none; }
  .btn-mode { padding: 6px 12px; font-size: 12px; }
}
</style>
