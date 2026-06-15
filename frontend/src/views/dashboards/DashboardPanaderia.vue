<template>
  <div class="dashboard-content">

    <KpiStrip :kpis="kpis" :showLabels="true" />

    <div class="dash-header">
      <h6 class="dash-title">{{ companyStore.selectedCompany?.name || 'Panadería / Pastelería' }}</h6>
    </div>

    <div class="welcome-card">
      <div class="wc-icon"><i class="bi bi-cake2-fill"></i></div>
      <div class="wc-body">
        <h5>¡Bienvenido a tu panel de Panadería / Pastelería!</h5>
        <p>Administra tus ventas diarias, pedidos de tortas y encargos especiales, producción del día e inventario de insumos. Controla costos de recetas y rentabilidad por producto.</p>
        <div class="wc-tips">
          <span><i class="bi bi-check-circle-fill"></i> Registra productos y recetas con sus costos</span>
          <span><i class="bi bi-check-circle-fill"></i> Gestiona pedidos y encargos especiales</span>
          <span><i class="bi bi-check-circle-fill"></i> Controla insumos y alertas de inventario</span>
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
  { icon: "bi-cash-coin",       label: "Ventas hoy",          value: "$ —" },
  { icon: "bi-receipt",         label: "Transacciones",       value: "—"   },
  { icon: "bi-graph-up-arrow",  label: "Ticket promedio",     value: "$ —" },
  { icon: "bi-basket2",         label: "Productos vendidos",  value: "—"   },
]
</script>

<style scoped>
.dash-header  { padding: 0 0 12px; }
.dash-title   { font-size: 17px; font-weight: 700; color: #1e293b; margin: 0; }
.welcome-card {
  display: flex; gap: 20px; align-items: flex-start;
  background: linear-gradient(135deg, #fff7ed 0%, #fef3c7 100%);
  border: 1px solid #fdba74; border-radius: 14px; padding: 22px 24px;
}
.wc-icon { font-size: 40px; color: #ea580c; flex-shrink: 0; line-height: 1; }
.wc-body h5  { font-size: 15px; font-weight: 700; color: #1e293b; margin-bottom: 6px; }
.wc-body p   { font-size: 13px; color: #475569; margin-bottom: 12px; line-height: 1.6; }
.wc-tips     { display: flex; flex-direction: column; gap: 5px; }
.wc-tips span { font-size: 12px; color: #9a3412; display: flex; align-items: center; gap: 6px; }
.wc-tips .bi-check-circle-fill { color: #22c55e; }
@media (max-width: 576px) {
  .welcome-card { flex-direction: column; gap: 12px; padding: 16px; }
  .wc-icon { font-size: 30px; }
}
</style>
