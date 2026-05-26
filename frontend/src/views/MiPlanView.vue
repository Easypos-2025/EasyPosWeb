<template>
  <div class="plan-wrap">

    <div class="plan-header">
      <i class="bi bi-gem plan-icon"></i>
      <div>
        <h1 class="plan-title">Mi Plan</h1>
        <p class="plan-sub">Límites y uso actual del plan activo para esta empresa</p>
      </div>
    </div>

    <div v-if="loading" class="plan-loading">
      <div class="spinner"></div>
      <span>Cargando información del plan...</span>
    </div>

    <template v-else>
      <!-- Tarjeta del plan -->
      <div class="plan-card">
        <div class="plan-badge">
          <i class="bi bi-gem"></i>
          <span class="plan-name">{{ info.plan_name }}</span>
        </div>
        <div v-if="info.expiration_date" class="plan-expiry">
          <i class="bi bi-calendar-check"></i>
          Vigente hasta: <strong>{{ fmtDate(info.expiration_date) }}</strong>
        </div>
        <div v-else class="plan-expiry plan-noexp">
          <i class="bi bi-infinity"></i> Sin fecha de vencimiento
        </div>
      </div>

      <!-- Tabla de límites -->
      <div class="limits-card">
        <h2 class="limits-title"><i class="bi bi-bar-chart-line me-2"></i>Detalle de límites</h2>

        <div class="limits-grid">
          <div
            v-for="item in info.items"
            :key="item.field"
            class="limit-row"
            :class="statusClass(item)"
          >
            <div class="limit-label">
              <i :class="iconFor(item.field)"></i>
              {{ capitalize(item.label) }}
            </div>

            <div class="limit-usage">
              <template v-if="item.max === -1">
                <span class="usage-unlimited"><i class="bi bi-infinity"></i> Ilimitado</span>
              </template>
              <template v-else-if="item.current !== null && item.current !== undefined">
                <div class="usage-bar-wrap">
                  <div class="usage-bar">
                    <div class="usage-fill" :style="barStyle(item)"></div>
                  </div>
                  <span class="usage-nums">{{ item.current }} / {{ item.max }}</span>
                </div>
                <span class="usage-pct" :class="pctClass(item)">{{ pctText(item) }}</span>
              </template>
              <template v-else>
                <span class="usage-limit">Máx. {{ item.max }}</span>
              </template>
            </div>
          </div>
        </div>
      </div>

      <p class="plan-note">
        <i class="bi bi-info-circle me-1"></i>
        Para cambiar de plan o aumentar límites, contacta a soporte.
      </p>
    </template>

  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { useRouter } from "vue-router"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

const router  = useRouter()
const info    = ref({ plan_name: "", expiration_date: null, items: [] })
const loading = ref(true)

async function load() {
  // SYSADMIN no tiene empresa — redirigir a la vista de planes por asociado
  const currentUser = JSON.parse(localStorage.getItem("user") || "{}")
  if (currentUser.is_system) {
    router.replace("/sysadmin/plan-asociado")
    return
  }

  loading.value = true
  try {
    const r = await api.get("/company-plan/my-plan-info")
    info.value = r.data
  } catch (e) {
    const detail = e.response?.data?.detail
    showToast(typeof detail === "string" ? detail : "Error cargando plan", "error")
  } finally {
    loading.value = false
  }
}

function fmtDate(iso) {
  if (!iso) return ""
  return new Date(iso).toLocaleDateString("es-CO", { day: "2-digit", month: "long", year: "numeric" })
}

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1)
}

function pct(item) {
  if (!item.max || item.max === -1 || item.current === null) return 0
  return Math.min((item.current / item.max) * 100, 100)
}

function pctText(item) {
  const p = pct(item)
  if (item.current >= item.max) return "Límite alcanzado"
  return `${p.toFixed(0)}% usado`
}

function pctClass(item) {
  const p = pct(item)
  if (p >= 100) return "pct-full"
  if (p >= 80)  return "pct-warn"
  return "pct-ok"
}

function statusClass(item) {
  if (item.max === -1) return ""
  if (item.current === null) return ""
  if (item.current >= item.max) return "row-full"
  if (item.current / item.max >= 0.8) return "row-warn"
  return ""
}

function barStyle(item) {
  const p = pct(item)
  let color = "#22c55e"
  if (p >= 100) color = "#ef4444"
  else if (p >= 80) color = "#f59e0b"
  return { width: `${p}%`, background: color }
}

const ICONS = {
  max_users:          "bi bi-people",
  max_products:       "bi bi-grid",
  max_categories:     "bi bi-tags",
  max_workers:        "bi bi-person-badge",
  max_clients:        "bi bi-person-lines-fill",
  max_bodega_items:   "bi bi-box-seam",
  max_tasks:          "bi bi-check2-square",
  max_daily_invoices: "bi bi-receipt",
  max_assets:         "bi bi-building",
  max_waiters:        "bi bi-person-workspace",
  max_daily_receipts: "bi bi-file-earmark-text",
  max_daily_tasks:    "bi bi-calendar-check",
  max_roles:          "bi bi-shield-lock",
}
function iconFor(field) { return ICONS[field] || "bi bi-dash-circle" }

onMounted(load)
</script>

<style scoped>
.plan-wrap {
  padding: 24px;
  max-width: 720px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.plan-header {
  display: flex;
  align-items: center;
  gap: 14px;
}

.plan-icon {
  font-size: 32px;
  color: #6366f1;
}

.plan-title {
  font-size: 22px;
  font-weight: 700;
  margin: 0;
  color: var(--text-main, #1e293b);
}

.plan-sub {
  font-size: 13px;
  color: var(--text-muted, #64748b);
  margin: 2px 0 0;
}

.plan-loading {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 48px;
  justify-content: center;
  color: var(--text-muted, #64748b);
}

.spinner {
  width: 24px; height: 24px;
  border: 3px solid rgba(0,0,0,0.1);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Plan card ── */
.plan-card {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  border-radius: 16px;
  padding: 20px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  color: #fff;
}

.plan-badge {
  display: flex;
  align-items: center;
  gap: 10px;
}

.plan-badge .bi {
  font-size: 22px;
}

.plan-name {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 0.3px;
}

.plan-expiry {
  font-size: 13px;
  opacity: 0.88;
  display: flex;
  align-items: center;
  gap: 6px;
}

.plan-noexp { opacity: 0.7; }

/* ── Limits card ── */
.limits-card {
  background: var(--card-bg, #fff);
  border: 1px solid var(--border, #e2e8f0);
  border-radius: 14px;
  padding: 20px;
}

.limits-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-main, #1e293b);
  margin: 0 0 16px;
  display: flex;
  align-items: center;
}

.limits-grid {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.limit-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 12px;
  border-radius: 8px;
  transition: background 0.1s;
}

.limit-row:hover { background: var(--input-bg, #f8fafc); }
.row-warn { background: rgba(245,158,11,0.07) !important; }
.row-full { background: rgba(239,68,68,0.07) !important; }

.limit-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-main, #374151);
  min-width: 180px;
}

.limit-label .bi {
  color: #6366f1;
  font-size: 15px;
  width: 18px;
}

.limit-usage {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  justify-content: flex-end;
}

.usage-unlimited {
  font-size: 12px;
  color: #22c55e;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 4px;
}

.usage-limit {
  font-size: 12px;
  color: var(--text-muted, #64748b);
}

.usage-bar-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.usage-bar {
  flex: 1;
  height: 6px;
  background: var(--border, #e2e8f0);
  border-radius: 10px;
  overflow: hidden;
  min-width: 80px;
}

.usage-fill {
  height: 100%;
  border-radius: 10px;
  transition: width 0.3s;
}

.usage-nums {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-main, #1e293b);
  white-space: nowrap;
}

.usage-pct {
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
  min-width: 100px;
  text-align: right;
}

.pct-ok   { color: #16a34a; }
.pct-warn { color: #d97706; }
.pct-full { color: #dc2626; }

.plan-note {
  font-size: 12px;
  color: var(--text-muted, #94a3b8);
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0 4px;
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .plan-wrap { padding: 14px; gap: 14px; }
  .limit-label { min-width: 130px; font-size: 12px; }
  .usage-bar { min-width: 50px; }
  .usage-pct { min-width: 80px; font-size: 10px; }
}

@media (max-width: 576px) {
  .plan-wrap { padding: 10px; }
  .limit-row { flex-direction: column; align-items: flex-start; gap: 6px; }
  .limit-usage { width: 100%; justify-content: flex-start; }
}
</style>
