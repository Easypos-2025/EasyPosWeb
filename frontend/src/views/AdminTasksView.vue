<template>
  <div class="page-container">

    <div class="page-header">
      <div>
        <h1 class="page-title"><i class="bi bi-bar-chart-line me-2"></i>Informes de Tareas</h1>
        <p class="page-subtitle">Análisis y resumen del estado general de tareas</p>
      </div>
    </div>

    <!-- KPI BAR -->
    <div class="kpi-bar" v-if="stats">
      <div class="kpi-card">
        <span class="kpi-num">{{ stats.total }}</span>
        <span class="kpi-label">Total</span>
      </div>
      <div class="kpi-card kpi-orange">
        <span class="kpi-num">{{ stats.pendiente }}</span>
        <span class="kpi-label">Pendientes</span>
      </div>
      <div class="kpi-card kpi-blue">
        <span class="kpi-num">{{ stats.asignada }}</span>
        <span class="kpi-label">Asignadas</span>
      </div>
      <div class="kpi-card kpi-purple">
        <span class="kpi-num">{{ stats.progreso }}</span>
        <span class="kpi-label">En Progreso</span>
      </div>
      <div class="kpi-card kpi-green">
        <span class="kpi-num">{{ stats.finalizada }}</span>
        <span class="kpi-label">Finalizadas</span>
      </div>
      <div class="kpi-card kpi-red">
        <span class="kpi-num">{{ stats.atrasadas }}</span>
        <span class="kpi-label">Atrasadas</span>
      </div>
    </div>

    <!-- PRÓXIMAMENTE -->
    <div class="coming-soon">
      <i class="bi bi-bar-chart-steps"></i>
      <h2>Módulo de Informes</h2>
      <p>Aquí se mostrarán reportes detallados por periodo, responsable, activo y estado de las tareas.</p>
      <div class="feature-list">
        <span class="feat-chip"><i class="bi bi-calendar3"></i> Reportes por periodo</span>
        <span class="feat-chip"><i class="bi bi-person-check"></i> Por responsable</span>
        <span class="feat-chip"><i class="bi bi-building"></i> Por activo</span>
        <span class="feat-chip"><i class="bi bi-graph-up"></i> Tendencias</span>
        <span class="feat-chip"><i class="bi bi-download"></i> Exportar PDF / Excel</span>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import api from "@/services/apis"

const stats = ref(null)

onMounted(async () => {
  try {
    const res = await api.get("/tasks/stats")
    stats.value = res.data
  } catch {
    // stats son opcionales en esta vista
  }
})
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1100px; }
.page-header    { margin-bottom: 20px; }
.page-title     { font-size: 22px; font-weight: 700; color: #1e293b; margin: 0 0 4px; display: flex; align-items: center; }
.page-subtitle  { font-size: 13px; color: #64748b; margin: 0; }

.kpi-bar  { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 28px; }
.kpi-card { background: #fff; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.07); padding: 14px 20px; display: flex; flex-direction: column; align-items: center; min-width: 90px; gap: 2px; }
.kpi-num  { font-size: 26px; font-weight: 800; color: #1e293b; }
.kpi-label{ font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: .4px; }
.kpi-orange .kpi-num { color: #ea580c; }
.kpi-blue   .kpi-num { color: #2563eb; }
.kpi-purple .kpi-num { color: #7c3aed; }
.kpi-green  .kpi-num { color: #16a34a; }
.kpi-red    .kpi-num { color: #dc2626; }

.coming-soon {
  background: #fff;
  border-radius: 16px;
  border: 2px dashed #e2e8f0;
  padding: 60px 40px;
  text-align: center;
  color: #94a3b8;
}
.coming-soon .bi { font-size: 52px; display: block; margin-bottom: 16px; color: #cbd5e1; }
.coming-soon h2 { font-size: 20px; font-weight: 700; color: #475569; margin-bottom: 8px; }
.coming-soon p  { font-size: 14px; color: #64748b; max-width: 480px; margin: 0 auto 24px; }

.feature-list { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
.feat-chip {
  display: inline-flex; align-items: center; gap: 5px;
  background: #f1f5f9; color: #475569;
  font-size: 12px; font-weight: 600;
  padding: 5px 12px; border-radius: 20px;
  border: 1px solid #e2e8f0;
}

@media (max-width: 768px) {
  .page-container { padding: 16px 14px; }
  .kpi-card { padding: 10px 14px; min-width: 70px; }
  .kpi-num  { font-size: 20px; }
  .coming-soon { padding: 40px 20px; }
  .coming-soon .bi { font-size: 40px; }
}
@media (max-width: 576px) {
  .kpi-bar { gap: 7px; }
  .kpi-card { min-width: 60px; padding: 8px 10px; }
  .kpi-num  { font-size: 18px; }
  .coming-soon { padding: 30px 16px; }
}
</style>
