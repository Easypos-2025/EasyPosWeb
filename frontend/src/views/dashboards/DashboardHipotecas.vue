<template>
  <div class="dashboard-content">

    <KpiStrip :kpis="kpis" :showLabels="true" />

    <div class="dash-header">
      <h6 class="dash-title">{{ companyStore.selectedCompany?.name || 'Hipotecas / Cobros' }}</h6>
    </div>

    <div class="welcome-card">
      <div class="wc-icon"><i class="bi bi-bank2"></i></div>
      <div class="wc-body">
        <h5>¡Bienvenido a tu panel de Hipotecas y Cobros!</h5>
        <p>Administra tu cartera de créditos, préstamos hipotecarios y cuotas de cobro. Lleva el control de pagos recibidos, saldos pendientes y clientes en mora.</p>
        <div class="wc-tips">
          <span><i class="bi bi-check-circle-fill"></i> Registra préstamos con tasa, plazo y cuotas</span>
          <span><i class="bi bi-check-circle-fill"></i> Controla pagos y saldos en tiempo real</span>
          <span><i class="bi bi-check-circle-fill"></i> Genera alertas de vencimientos y mora</span>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import KpiStrip from "@/components/dashboard/KpiStrip.vue"
import { useCompanyStore } from "@/stores/companyStore"

const companyStore = useCompanyStore()

const kpis = [
  { icon: "bi-cash-coin",         label: "Recaudado hoy",       value: "$ —" },
  { icon: "bi-receipt",           label: "Cuotas cobradas",     value: "—"   },
  { icon: "bi-graph-up-arrow",    label: "Cartera total",       value: "$ —" },
  { icon: "bi-exclamation-circle",label: "En mora",             value: "—"   },
]
</script>

<style scoped>
.dash-header  { padding: 0 0 12px; }
.dash-title   { font-size: 17px; font-weight: 700; color: #1e293b; margin: 0; }
.welcome-card {
  display: flex; gap: 20px; align-items: flex-start;
  background: linear-gradient(135deg, #f0fdf4 0%, #eff6ff 100%);
  border: 1px solid #6ee7b7; border-radius: 14px; padding: 22px 24px;
}
.wc-icon { font-size: 40px; color: #059669; flex-shrink: 0; line-height: 1; }
.wc-body h5  { font-size: 15px; font-weight: 700; color: #1e293b; margin-bottom: 6px; }
.wc-body p   { font-size: 13px; color: #475569; margin-bottom: 12px; line-height: 1.6; }
.wc-tips     { display: flex; flex-direction: column; gap: 5px; }
.wc-tips span { font-size: 12px; color: #065f46; display: flex; align-items: center; gap: 6px; }
.wc-tips .bi-check-circle-fill { color: #22c55e; }
@media (max-width: 576px) {
  .welcome-card { flex-direction: column; gap: 12px; padding: 16px; }
  .wc-icon { font-size: 30px; }
}
</style>
