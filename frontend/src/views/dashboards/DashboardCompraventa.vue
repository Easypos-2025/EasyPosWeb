<template>
  <div class="dashboard-content">

    <KpiStrip :kpis="kpis" :showLabels="true" />

    <div class="dash-header">
      <h6 class="dash-title">{{ companyStore.selectedCompany?.name || 'Compraventa / Joyería' }}</h6>
    </div>

    <div class="welcome-card">
      <div class="wc-icon"><i class="bi bi-gem"></i></div>
      <div class="wc-body">
        <h5>¡Bienvenido a tu panel de Compraventa / Joyería!</h5>
        <p>Gestiona tus compras y ventas de artículos, joyería, prendas de empeño y objetos de valor. Mantén el control de cada pieza con su costo, valor de venta y estado.</p>
        <div class="wc-tips">
          <span><i class="bi bi-check-circle-fill"></i> Registra artículos con costo de compra y precio de venta</span>
          <span><i class="bi bi-check-circle-fill"></i> Controla el inventario de piezas disponibles</span>
          <span><i class="bi bi-check-circle-fill"></i> Gestiona clientes compradores y proveedores</span>
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
  { icon: "bi-receipt",          label: "Transacciones",       value: "—"   },
  { icon: "bi-graph-up-arrow",   label: "Ticket promedio",     value: "$ —" },
  { icon: "bi-bag-check",        label: "Artículos vendidos",  value: "—"   },
]
</script>

<style scoped>
.dash-header  { padding: 0 0 12px; }
.dash-title   { font-size: 17px; font-weight: 700; color: #1e293b; margin: 0; }
.welcome-card {
  display: flex; gap: 20px; align-items: flex-start;
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border: 1px solid #fcd34d; border-radius: 14px; padding: 22px 24px;
}
.wc-icon { font-size: 40px; color: #d97706; flex-shrink: 0; line-height: 1; }
.wc-body h5  { font-size: 15px; font-weight: 700; color: #1e293b; margin-bottom: 6px; }
.wc-body p   { font-size: 13px; color: #475569; margin-bottom: 12px; line-height: 1.6; }
.wc-tips     { display: flex; flex-direction: column; gap: 5px; }
.wc-tips span { font-size: 12px; color: #92400e; display: flex; align-items: center; gap: 6px; }
.wc-tips .bi-check-circle-fill { color: #22c55e; }
@media (max-width: 576px) {
  .welcome-card { flex-direction: column; gap: 12px; padding: 16px; }
  .wc-icon { font-size: 30px; }
}
</style>
