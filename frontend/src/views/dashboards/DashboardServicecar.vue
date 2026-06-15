<template>
  <div class="dashboard-content">

    <KpiStrip :kpis="kpis" :showLabels="true" />

    <div class="dash-header">
      <h6 class="dash-title">{{ companyStore.selectedCompany?.name || 'Servicar' }}</h6>
    </div>

    <div class="welcome-card">
      <div class="wc-icon"><i class="bi bi-wrench-adjustable-circle-fill"></i></div>
      <div class="wc-body">
        <h5>¡Bienvenido a tu panel de Servicar!</h5>
        <p>Controla los servicios de tu taller: órdenes de trabajo, vehículos en proceso, repuestos utilizados y facturación por servicio. Ten visibilidad completa del estado de cada vehículo.</p>
        <div class="wc-tips">
          <span><i class="bi bi-check-circle-fill"></i> Registra órdenes de trabajo por vehículo</span>
          <span><i class="bi bi-check-circle-fill"></i> Controla repuestos e insumos utilizados</span>
          <span><i class="bi bi-check-circle-fill"></i> Factura servicios y lleva historial por cliente</span>
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
  { icon: "bi-cash-coin",        label: "Ventas hoy",          value: "$ —" },
  { icon: "bi-receipt",          label: "Servicios facturados", value: "—"  },
  { icon: "bi-graph-up-arrow",   label: "Ticket promedio",     value: "$ —" },
  { icon: "bi-car-front-fill",   label: "Vehículos atendidos", value: "—"   },
]
</script>

<style scoped>
.dash-header  { padding: 0 0 12px; }
.dash-title   { font-size: 17px; font-weight: 700; color: #1e293b; margin: 0; }
.welcome-card {
  display: flex; gap: 20px; align-items: flex-start;
  background: linear-gradient(135deg, #f8fafc 0%, #e0f2fe 100%);
  border: 1px solid #7dd3fc; border-radius: 14px; padding: 22px 24px;
}
.wc-icon { font-size: 40px; color: #0369a1; flex-shrink: 0; line-height: 1; }
.wc-body h5  { font-size: 15px; font-weight: 700; color: #1e293b; margin-bottom: 6px; }
.wc-body p   { font-size: 13px; color: #475569; margin-bottom: 12px; line-height: 1.6; }
.wc-tips     { display: flex; flex-direction: column; gap: 5px; }
.wc-tips span { font-size: 12px; color: #0c4a6e; display: flex; align-items: center; gap: 6px; }
.wc-tips .bi-check-circle-fill { color: #22c55e; }
@media (max-width: 576px) {
  .welcome-card { flex-direction: column; gap: 12px; padding: 16px; }
  .wc-icon { font-size: 30px; }
}
</style>
