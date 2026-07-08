<template>
  <div class="page-container">

    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title"><i class="bi bi-people-fill"></i> Equipo de Trabajo</h1>
        <p class="page-subtitle">Directorio de operarios, saldo pendiente y actividad del mes.</p>
      </div>
      <router-link to="/talleres/liquidacion" class="btn btn-primary">
        <i class="bi bi-cash-coin"></i> Ir a Liquidación
      </router-link>
    </div>

    <!-- KPI bar -->
    <div class="kpi-bar">
      <div class="kpi-card">
        <i class="bi bi-person-check-fill kpi-icon blue"></i>
        <div class="kpi-body">
          <span class="kpi-val">{{ kpis.activos }}</span>
          <span class="kpi-lbl">Operarios activos</span>
        </div>
      </div>
      <div class="kpi-card">
        <i class="bi bi-cash-stack kpi-icon amber"></i>
        <div class="kpi-body">
          <span class="kpi-val">{{ fmt(kpis.saldo_total) }}</span>
          <span class="kpi-lbl">Saldo pendiente total</span>
        </div>
      </div>
      <div class="kpi-card">
        <i class="bi bi-clipboard2-check kpi-icon green"></i>
        <div class="kpi-body">
          <span class="kpi-val">{{ kpis.ordenes_mes }}</span>
          <span class="kpi-lbl">Órdenes trabajadas este mes</span>
        </div>
      </div>
      <div class="kpi-card">
        <i class="bi bi-hourglass-split kpi-icon red"></i>
        <div class="kpi-body">
          <span class="kpi-val">{{ kpis.con_saldo }}</span>
          <span class="kpi-lbl">Pendientes de pago</span>
        </div>
      </div>
    </div>

    <!-- Filtros -->
    <div class="filters-row">
      <input v-model="search" class="form-control" placeholder="Buscar operario…" style="max-width:220px" />
      <select v-model="filterProfesion" class="form-select" style="max-width:200px">
        <option value="">Todas las profesiones</option>
        <option v-for="p in profesionesList" :key="p" :value="p">{{ p }}</option>
      </select>
      <label class="toggle-label">
        <input type="checkbox" v-model="soloConSaldo" />
        <span>Solo con saldo pendiente</span>
      </label>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-center">
      <i class="bi bi-arrow-repeat spin"></i> Cargando equipo…
    </div>

    <!-- Grupos por profesión -->
    <div v-else>
      <div v-for="grupo in grupos" :key="grupo.profesion" class="grupo-section">
        <div class="grupo-header">
          <span class="grupo-titulo">{{ grupo.profesion }}</span>
          <span class="grupo-count">{{ grupo.workers.length }} operario{{ grupo.workers.length !== 1 ? 's' : '' }}</span>
        </div>

        <div class="workers-grid">
          <div
            v-for="w in grupo.workers"
            :key="w.id"
            class="worker-card"
            :class="{ 'has-saldo': w.monto_pendiente > 0, inactive: !w.is_active }"
          >
            <!-- Fila superior: avatar + info + acción -->
            <div class="card-top">
              <div class="w-avatar" :style="{ background: avatarColor(w.name) }">
                {{ initials(w.name) }}
              </div>
              <div class="w-info">
                <div class="w-name">{{ w.name }}</div>
                <div class="w-meta">
                  <span class="prof-badge">{{ w.profession_nombre || 'Sin rol' }}</span>
                  <span v-if="!w.is_active" class="inactive-badge">Inactivo</span>
                </div>
                <div v-if="w.phone" class="w-phone">
                  <i class="bi bi-telephone-fill"></i> {{ w.phone }}
                </div>
              </div>
              <div class="w-action">
                <router-link
                  v-if="w.monto_pendiente > 0"
                  to="/talleres/liquidacion"
                  class="btn-liq"
                  :title="`Liquidar a ${w.name}`"
                >
                  <i class="bi bi-cash-coin"></i>
                  <span class="liq-text">Liquidar</span>
                </router-link>
                <span v-else class="btn-al-dia">
                  <i class="bi bi-check-circle-fill"></i>
                  <span class="liq-text">Al día</span>
                </span>
              </div>
            </div>

            <!-- Fila inferior: métricas -->
            <div class="w-metrics">
              <div class="metric">
                <span class="m-label">Saldo pendiente</span>
                <span class="m-value" :class="w.monto_pendiente > 0 ? 'val-amber' : 'val-muted'">
                  {{ fmt(w.monto_pendiente) }}
                </span>
              </div>
              <div class="metric">
                <span class="m-label">Órdenes este mes</span>
                <span class="m-value val-blue">{{ w.ordenes_mes }}</span>
              </div>
              <div class="metric">
                <span class="m-label">Ítems por liquidar</span>
                <span class="m-value" :class="w.items_pendientes > 0 ? 'val-red' : 'val-muted'">
                  {{ w.items_pendientes }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="grupos.length === 0" class="empty-state">
        <i class="bi bi-people"></i>
        <p>No hay operarios que coincidan con el filtro.</p>
        <p class="empty-hint">Registra operarios en <strong>Configuración → Trabajadores</strong>.</p>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import { useCompanyStore } from "@/stores/companyStore"

const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id)

const workers         = ref([])
const loading         = ref(true)
const search          = ref("")
const filterProfesion = ref("")
const soloConSaldo    = ref(false)

async function load() {
  loading.value = true
  try {
    const { data } = await api.get("/api/talleres/workers-con-config", {
      params: { company_id: companyId.value }
    })
    workers.value = data
  } catch { showToast("Error cargando operarios", "error") }
  finally { loading.value = false }
}

// ── KPIs ──────────────────────────────────────────────────────────────────
const kpis = computed(() => ({
  activos:     workers.value.filter(w => w.is_active).length,
  saldo_total: workers.value.reduce((s, w) => s + Number(w.monto_pendiente || 0), 0),
  ordenes_mes: workers.value.reduce((s, w) => s + Number(w.ordenes_mes || 0), 0),
  con_saldo:   workers.value.filter(w => w.monto_pendiente > 0).length,
}))

// ── Profesiones para el filtro ─────────────────────────────────────────────
const profesionesList = computed(() => {
  const set = new Set(workers.value.map(w => w.profession_nombre).filter(Boolean))
  return [...set].sort()
})

// ── Filtrado + agrupación ──────────────────────────────────────────────────
const filtrados = computed(() => {
  const q = search.value.toLowerCase()
  return workers.value.filter(w => {
    if (soloConSaldo.value && !(w.monto_pendiente > 0)) return false
    if (filterProfesion.value && w.profession_nombre !== filterProfesion.value) return false
    if (q && !w.name.toLowerCase().includes(q)) return false
    return true
  })
})

const grupos = computed(() => {
  const map = new Map()
  for (const w of filtrados.value) {
    const key = w.profession_nombre || "Sin profesión"
    if (!map.has(key)) map.set(key, [])
    map.get(key).push(w)
  }
  return [...map.entries()].map(([profesion, ws]) => ({ profesion, workers: ws }))
})

// ── Helpers ───────────────────────────────────────────────────────────────
function fmt(v) {
  return Number(v || 0).toLocaleString("es-CO", {
    style: "currency", currency: "COP", minimumFractionDigits: 0
  })
}
function initials(name = "") {
  return name.trim().split(/\s+/).slice(0, 2).map(p => p[0]).join("").toUpperCase()
}
const COLORS = ["#3b82f6","#10b981","#f59e0b","#a855f7","#ef4444","#06b6d4","#f97316","#6366f1"]
function avatarColor(name = "") {
  let h = 0
  for (const c of name) h = (h * 31 + c.charCodeAt(0)) & 0xffff
  return COLORS[h % COLORS.length]
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1200px; }

.page-header   { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.page-title    { font-size: 20px; font-weight: 700; color: #1e293b; margin: 0 0 4px; display: flex; align-items: center; gap: 8px; }
.page-subtitle { font-size: 13px; color: #64748b; margin: 0; }

/* KPI */
.kpi-bar  { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
.kpi-card {
  background: #fff; border-radius: 14px; border: 1.5px solid #e2e8f0;
  padding: 14px 18px; display: flex; align-items: center; gap: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,.05);
}
.kpi-icon       { font-size: 24px; }
.kpi-icon.blue  { color: #3b82f6; } .kpi-icon.amber { color: #f59e0b; }
.kpi-icon.green { color: #22c55e; } .kpi-icon.red   { color: #ef4444; }
.kpi-body { display: flex; flex-direction: column; }
.kpi-val  { font-size: 18px; font-weight: 800; color: #1e293b; line-height: 1.15; }
.kpi-lbl  { font-size: 11px; color: #64748b; }

/* Filtros */
.filters-row  { display: flex; gap: 10px; align-items: center; margin-bottom: 20px; flex-wrap: wrap; }
.toggle-label { display: flex; align-items: center; gap: 7px; font-size: 13px; color: #374151; cursor: pointer; }
.toggle-label input { width: 16px; height: 16px; cursor: pointer; }

.loading-center { display: flex; align-items: center; gap: 8px; padding: 48px; color: #94a3b8; justify-content: center; }

/* Grupos */
.grupo-section { margin-bottom: 28px; }
.grupo-header  { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #f1f5f9; }
.grupo-titulo  { font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: .5px; color: #475569; }
.grupo-count   { font-size: 11px; background: #f1f5f9; color: #64748b; padding: 2px 8px; border-radius: 20px; font-weight: 600; }

/* Worker cards */
.workers-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 12px; }

.worker-card {
  background: #fff;
  border: 2px solid #e2e8f0;
  border-radius: 14px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: box-shadow .15s, transform .15s;
  box-shadow: 0 1px 4px rgba(0,0,0,.05);
}
.worker-card:hover    { box-shadow: 0 6px 20px rgba(0,0,0,.1); transform: translateY(-2px); }
.worker-card.has-saldo { border-color: #fde68a; background: linear-gradient(135deg, #fffbeb 0%, #fff 60%); }
.worker-card.inactive  { opacity: .55; background: #f8fafc; }

/* Card top: avatar + info + acción */
.card-top { display: flex; align-items: flex-start; gap: 12px; }
.w-avatar {
  width: 46px; height: 46px; border-radius: 12px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 15px; font-weight: 800;
}
.w-info    { flex: 1; min-width: 0; }
.w-name    { font-size: 15px; font-weight: 700; color: #1e293b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.w-meta    { display: flex; gap: 5px; flex-wrap: wrap; margin-top: 3px; }
.prof-badge     { font-size: 10px; font-weight: 700; background: #eff6ff; color: #1d4ed8; padding: 2px 8px; border-radius: 20px; }
.inactive-badge { font-size: 10px; font-weight: 700; background: #f1f5f9; color: #94a3b8; padding: 2px 8px; border-radius: 20px; }
.w-phone   { font-size: 12px; color: #64748b; margin-top: 4px; display: flex; align-items: center; gap: 4px; }

.w-action { flex-shrink: 0; }

/* Métricas */
.w-metrics { display: flex; border-top: 1px solid #f1f5f9; padding-top: 12px; }
.metric    { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 2px; }
.metric + .metric { border-left: 1px solid #f1f5f9; }
.m-label   { font-size: 10px; color: #94a3b8; text-align: center; }
.m-value   { font-size: 14px; font-weight: 800; }
.val-amber { color: #d97706; } .val-blue { color: #2563eb; }
.val-red   { color: #dc2626; } .val-muted { color: #cbd5e1; }

/* Botones acción */
.btn-liq {
  display: inline-flex; align-items: center; gap: 5px;
  background: #fef3c7; color: #92400e; border: 1.5px solid #fde68a;
  border-radius: 8px; padding: 5px 12px; font-size: 12px; font-weight: 700;
  cursor: pointer; text-decoration: none; transition: background .12s;
}
.btn-liq:hover { background: #fde68a; }
.btn-al-dia {
  display: inline-flex; align-items: center; gap: 5px;
  color: #16a34a; font-size: 12px; font-weight: 700;
}

/* Empty */
.empty-state { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 60px 0; color: #94a3b8; text-align: center; }
.empty-state .bi { font-size: 48px; color: #cbd5e1; }
.empty-state p   { font-size: 14px; margin: 0; }
.empty-hint      { font-size: 12px !important; color: #94a3b8; }

/* Btn */
.btn { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; text-decoration: none; }
.btn-primary { background: #3b82f6; color: #fff; } .btn-primary:hover { background: #2563eb; }

.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }

/* Responsive */
@media (max-width: 900px) {
  .kpi-bar      { grid-template-columns: repeat(2, 1fr); }
  .workers-grid { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 576px) {
  .kpi-bar      { grid-template-columns: 1fr 1fr; }
  .workers-grid { grid-template-columns: 1fr; }
  .page-container { padding: 14px; }
  .filters-row  { flex-direction: column; align-items: stretch; }
  .liq-text     { display: none; }
}
</style>
