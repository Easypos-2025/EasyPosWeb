<template>
  <div class="page-container">

    <div class="page-header">
      <div>
        <h1 class="page-title"><i class="bi bi-bar-chart-line me-2"></i>Métricas del Asociado</h1>
        <p class="page-subtitle">Análisis y estadísticas de operación</p>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════
         SECCIÓN 1: SALUD DE TAREAS
    ══════════════════════════════════════════════ -->
    <div class="metric-section">
      <div class="section-header">
        <i class="bi bi-clipboard2-check-fill section-icon tasks"></i>
        <div>
          <h2 class="section-title">Tareas</h2>
          <p class="section-sub">Salud general del proyecto · {{ stats.total }} tareas en total</p>
        </div>
        <router-link to="/tasks" class="section-link">Ver tareas <i class="bi bi-arrow-right"></i></router-link>
      </div>

      <div v-if="loadingStats" class="metric-loading"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
      <div v-else class="metrics-grid">

        <!-- % Pendientes -->
        <div class="metric-card">
          <div class="mc-icon mc-orange"><i class="bi bi-hourglass-split"></i></div>
          <div class="mc-body">
            <span class="mc-value">{{ pct(stats.pendiente) }}</span>
            <span class="mc-label">% Pendientes</span>
            <div class="mc-bar"><div class="mc-fill mc-fill-orange" :style="{ width: pct(stats.pendiente) }"></div></div>
            <span class="mc-abs">{{ stats.pendiente }} tareas</span>
          </div>
        </div>

        <!-- % En Ejecución -->
        <div class="metric-card">
          <div class="mc-icon mc-green"><i class="bi bi-play-circle-fill"></i></div>
          <div class="mc-body">
            <span class="mc-value">{{ pct(stats.progreso + stats.revision) }}</span>
            <span class="mc-label">% En Ejecución</span>
            <div class="mc-bar"><div class="mc-fill mc-fill-green" :style="{ width: pct(stats.progreso + stats.revision) }"></div></div>
            <span class="mc-abs">{{ stats.progreso + stats.revision }} tareas ({{ stats.progreso }} en progreso · {{ stats.revision }} en revisión)</span>
          </div>
        </div>

        <!-- % Atrasadas -->
        <div class="metric-card" :class="{ 'mc-alert': stats.atrasadas > 0 }">
          <div class="mc-icon mc-red"><i class="bi bi-exclamation-triangle-fill"></i></div>
          <div class="mc-body">
            <span class="mc-value">{{ pct(stats.atrasadas) }}</span>
            <span class="mc-label">% Atrasadas</span>
            <div class="mc-bar"><div class="mc-fill mc-fill-red" :style="{ width: pct(stats.atrasadas) }"></div></div>
            <span class="mc-abs">{{ stats.atrasadas }} tareas vencidas</span>
          </div>
        </div>

        <!-- % Completadas -->
        <div class="metric-card">
          <div class="mc-icon mc-teal"><i class="bi bi-check2-circle"></i></div>
          <div class="mc-body">
            <span class="mc-value">{{ pct(stats.finalizada) }}</span>
            <span class="mc-label">% Completadas</span>
            <div class="mc-bar"><div class="mc-fill mc-fill-teal" :style="{ width: pct(stats.finalizada) }"></div></div>
            <span class="mc-abs">{{ stats.finalizada }} finalizadas · {{ stats.cancelada }} canceladas</span>
          </div>
        </div>

        <!-- Sin asignar -->
        <div class="metric-card">
          <div class="mc-icon mc-amber"><i class="bi bi-person-dash-fill"></i></div>
          <div class="mc-body">
            <span class="mc-value">{{ stats.sin_asignar }}</span>
            <span class="mc-label">Sin asignar</span>
            <div class="mc-bar"><div class="mc-fill mc-fill-amber" :style="{ width: pct(stats.sin_asignar) }"></div></div>
            <span class="mc-abs">Tareas sin líder de tarea</span>
          </div>
        </div>

        <!-- Info incompleta -->
        <div class="metric-card">
          <div class="mc-icon mc-purple"><i class="bi bi-clipboard-x-fill"></i></div>
          <div class="mc-body">
            <span class="mc-value">{{ stats.info_incompleta }}</span>
            <span class="mc-label">Info incompleta</span>
            <div class="mc-bar"><div class="mc-fill mc-fill-purple" :style="{ width: pct(stats.info_incompleta) }"></div></div>
            <span class="mc-abs">Tareas con datos faltantes</span>
          </div>
        </div>

      </div>
    </div>

    <!-- ══════════════════════════════════════════════
         PRÓXIMAS SECCIONES
    ══════════════════════════════════════════════ -->
    <div class="coming-soon-grid">

      <div class="cs-card">
        <div class="cs-icon"><i class="bi bi-receipt-cutoff"></i></div>
        <h3 class="cs-title">Ventas</h3>
        <p class="cs-text">Facturación, ingresos y tendencias</p>
        <span class="cs-badge">Próximamente</span>
      </div>

      <div class="cs-card">
        <div class="cs-icon"><i class="bi bi-people-fill"></i></div>
        <h3 class="cs-title">Clientes</h3>
        <p class="cs-text">Nuevos clientes, retención y actividad</p>
        <span class="cs-badge">Próximamente</span>
      </div>

      <div class="cs-card">
        <div class="cs-icon"><i class="bi bi-cash-coin"></i></div>
        <h3 class="cs-title">Gastos</h3>
        <p class="cs-text">Control de costos y presupuestos</p>
        <span class="cs-badge">Próximamente</span>
      </div>

      <div class="cs-card">
        <div class="cs-icon"><i class="bi bi-boxes"></i></div>
        <h3 class="cs-title">Inventario</h3>
        <p class="cs-text">Stock, rotación y bodega</p>
        <span class="cs-badge">Próximamente</span>
      </div>

    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import api from "@/services/apis"

const stats = ref({
  total: 0, pendiente: 0, progreso: 0, revision: 0,
  finalizada: 0, cancelada: 0, atrasadas: 0,
  sin_asignar: 0, info_incompleta: 0,
})
const loadingStats = ref(true)

function pct(n) {
  const t = stats.value.total
  if (!t || n === undefined) return "0%"
  return Math.round((n / t) * 100) + "%"
}

onMounted(async () => {
  try {
    const res = await api.get("/tasks/stats")
    stats.value = res.data
  } catch {}
  loadingStats.value = false
})
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1100px; }
.page-header    { margin-bottom: 24px; }
.page-title     { font-size: 22px; font-weight: 700; color: #1e293b; margin: 0 0 4px; }
.page-subtitle  { font-size: 13px; color: #64748b; margin: 0; }

/* SECCIÓN */
.metric-section  { background: #fff; border-radius: 16px; box-shadow: 0 1px 6px rgba(0,0,0,.08); padding: 20px 24px; margin-bottom: 24px; }
.section-header  { display: flex; align-items: center; gap: 14px; margin-bottom: 20px; flex-wrap: wrap; }
.section-icon    { font-size: 26px; }
.section-icon.tasks { color: #3b82f6; }
.section-title   { font-size: 17px; font-weight: 700; color: #1e293b; margin: 0; }
.section-sub     { font-size: 12px; color: #94a3b8; margin: 0; }
.section-link    { margin-left: auto; font-size: 12px; font-weight: 600; color: #3b82f6; text-decoration: none; display: flex; align-items: center; gap: 4px; white-space: nowrap; }
.section-link:hover { color: #1d4ed8; }

.metric-loading { padding: 32px; text-align: center; color: #94a3b8; }

/* GRID DE MÉTRICAS */
.metrics-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }

.metric-card {
  background: #f8fafc; border-radius: 12px; padding: 14px 16px;
  display: flex; align-items: flex-start; gap: 14px;
  border: 1.5px solid #f1f5f9; transition: border-color .2s;
}
.metric-card:hover    { border-color: #dbeafe; }
.metric-card.mc-alert { border-color: #fecaca; background: #fff5f5; }

.mc-icon {
  width: 42px; height: 42px; border-radius: 10px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 19px;
}
.mc-orange { background: #fff7ed; color: #ea580c; }
.mc-green  { background: #f0fdf4; color: #16a34a; }
.mc-red    { background: #fef2f2; color: #dc2626; }
.mc-teal   { background: #f0fdfa; color: #0d9488; }
.mc-amber  { background: #fffbeb; color: #d97706; }
.mc-purple { background: #f5f3ff; color: #7c3aed; }

.mc-body  { flex: 1; display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.mc-value { font-size: 26px; font-weight: 800; color: #1e293b; line-height: 1; }
.mc-label { font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: .4px; }

.mc-bar   { height: 5px; background: #e2e8f0; border-radius: 3px; overflow: hidden; margin: 2px 0; }
.mc-fill  { height: 100%; border-radius: 3px; transition: width .6s ease; }
.mc-fill-orange { background: #f97316; }
.mc-fill-green  { background: #22c55e; }
.mc-fill-red    { background: #ef4444; }
.mc-fill-teal   { background: #14b8a6; }
.mc-fill-amber  { background: #f59e0b; }
.mc-fill-purple { background: #8b5cf6; }

.mc-abs { font-size: 11px; color: #94a3b8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* COMING SOON */
.coming-soon-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
.cs-card {
  background: #fff; border-radius: 14px; box-shadow: 0 1px 4px rgba(0,0,0,.06);
  padding: 20px; display: flex; flex-direction: column; align-items: center;
  gap: 8px; text-align: center; border: 1.5px dashed #e2e8f0;
}
.cs-icon  { font-size: 28px; color: #cbd5e1; }
.cs-title { font-size: 14px; font-weight: 700; color: #94a3b8; margin: 0; }
.cs-text  { font-size: 12px; color: #cbd5e1; margin: 0; line-height: 1.4; }
.cs-badge { font-size: 10px; font-weight: 700; background: #f1f5f9; color: #94a3b8; padding: 2px 10px; border-radius: 20px; }

.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

@media (max-width: 900px) {
  .metrics-grid      { grid-template-columns: repeat(2, 1fr); }
  .coming-soon-grid  { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 576px) {
  .page-container    { padding: 12px; }
  .metric-section    { padding: 16px; }
  .metrics-grid      { grid-template-columns: 1fr; }
  .coming-soon-grid  { grid-template-columns: repeat(2, 1fr); }
  .mc-value          { font-size: 22px; }
}
</style>
