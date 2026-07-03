<template>
  <div class="dash-fer">

    <!-- Marca de agua -->
    <div class="wm-bg" aria-hidden="true">
      <i class="bi bi-tools       wm-1"></i>
      <i class="bi bi-hammer      wm-2"></i>
      <i class="bi bi-wrench-adjustable wm-3"></i>
    </div>

    <!-- KPI BAR -->
    <KpiStrip :kpis="kpis" :loading="loading" :showLabels="true" v-model="fechaKpi" />

    <!-- CABECERA -->
    <div class="dash-header">
      <div class="dash-header-left">
        <h6 class="dash-empresa">{{ companyStore.selectedCompany?.name || 'Ferretería' }}</h6>
        <span class="dash-perfil-tag">
          <i class="bi bi-tools"></i> Ferretería
        </span>
      </div>
      <span class="dash-fecha">{{ fechaHoy }}</span>
    </div>

  </div>
</template>

<script setup>
import { computed } from 'vue'
import KpiStrip from '@/components/dashboard/KpiStrip.vue'
import { useVentasKpis } from '@/composables/useVentasKpis'
import { useCompanyStore } from '@/stores/companyStore'

const companyStore = useCompanyStore()
const { kpis, loading, fechaKpi } = useVentasKpis()

const fechaHoy = computed(() =>
  new Intl.DateTimeFormat('es-CO', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' })
    .format(new Date())
)
</script>

<style scoped>
.dash-fer {
  position: relative;
  min-height: 80vh;
  padding: 0 24px 48px;
  overflow: hidden;
}

/* ── Marca de agua ── */
.wm-bg { position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden; }
.wm-1 {
  position: absolute; font-size: 420px; color: #b45309; opacity: 0.04;
  bottom: -80px; right: -60px; transform: rotate(-12deg);
}
.wm-2 {
  position: absolute; font-size: 180px; color: #92400e; opacity: 0.045;
  top: 40px; left: -30px; transform: rotate(20deg);
}
.wm-3 {
  position: absolute; font-size: 120px; color: #d97706; opacity: 0.05;
  top: 220px; right: 24%; transform: rotate(-30deg);
}

/* ── Header ── */
.dash-header {
  position: relative; z-index: 1;
  display: flex; align-items: flex-start; justify-content: space-between; gap: 12px;
  padding: 20px 0 14px; border-bottom: 1px solid #e2e8f0; margin-bottom: 20px;
}
.dash-empresa { margin: 0 0 4px; font-size: 20px; font-weight: 700; color: #1c1917; line-height: 1.2; }
.dash-perfil-tag {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 12px; font-weight: 600; color: #92400e;
  background: #fef3c7; border: 1px solid #fcd34d; border-radius: 20px;
  padding: 2px 10px; text-transform: uppercase; letter-spacing: 0.5px;
}
.dash-fecha { font-size: 13px; color: #64748b; white-space: nowrap; padding-top: 2px; text-transform: capitalize; }

/* ── Responsive ── */
@media (max-width: 768px) {
  .dash-fer { padding: 0 16px 40px; }
  .dash-header { flex-direction: column; gap: 4px; }
  .wm-1 { font-size: 280px; }
  .wm-2 { font-size: 110px; }
}
@media (max-width: 576px) {
  .dash-fer { padding: 0 12px 32px; }
  .dash-empresa { font-size: 17px; }
  .wm-1 { font-size: 200px; bottom: -40px; right: -20px; }
  .wm-2 { font-size: 80px; }
  .wm-3 { display: none; }
}
</style>
