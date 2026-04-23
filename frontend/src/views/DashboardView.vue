<template>
  <component :is="activeDashboard" v-if="activeDashboard" />
  <div v-else class="dash-empty">
    <i class="bi bi-grid-3x3-gap"></i>
    <p>Sin dashboard configurado para este perfil.</p>
  </div>
</template>

<script setup>
import { computed } from "vue"
import { useCompanyStore } from "@/stores/companyStore"

import DashboardRestaurante   from "@/views/dashboards/DashboardRestaurante.vue"
import DashboardAdmonTareas   from "@/views/dashboards/DashboardAdmonTareas.vue"
import DashboardAlmacenModa   from "@/views/dashboards/DashboardAlmacenModa.vue"
import DashboardDrogueria     from "@/views/dashboards/DashboardDrogueria.vue"
import DashboardSysadmin      from "@/views/dashboards/DashboardSysadmin.vue"
import DashboardFruver        from "@/views/dashboards/DashboardFruver.vue"
import DashboardEstanco       from "@/views/dashboards/DashboardEstanco.vue"
import DashboardPeluqueria    from "@/views/dashboards/DashboardPeluqueria.vue"
import DashboardDistribuidora from "@/views/dashboards/DashboardDistribuidora.vue"
import DashboardLujosAutos    from "@/views/dashboards/DashboardLujosAutos.vue"
import DashboardMarketing     from "@/views/dashboards/DashboardMarketing.vue"
import DashboardMiniMarket    from "@/views/dashboards/DashboardMiniMarket.vue"

// business_profile_id → componente de dashboard
const DASHBOARD_MAP = {
  1:  DashboardRestaurante,    // Restaurante
  2:  DashboardAdmonTareas,    // Administraciones / Admon Tareas
  3:  DashboardDrogueria,      // Droguerías
  4:  DashboardSysadmin,       // SYSADMIN
  7:  DashboardFruver,         // Fruvers
  8:  DashboardEstanco,        // Estancos / Licorería
  9:  DashboardPeluqueria,     // Peluquerías / Barberías
  10: DashboardDistribuidora,  // Distribuidoras
  11: DashboardLujosAutos,     // Almacén Lujos y Autos
  12: DashboardMarketing,      // Agencia de Marketing
  13: DashboardMiniMarket,     // Mini-Market / Supermercados
  14: DashboardAlmacenModa,    // Almacenes Moda
}

const companyStore = useCompanyStore()

const activeDashboard = computed(() => {
  const profileId = companyStore.selectedCompany?.business_profile_id
  return DASHBOARD_MAP[profileId] ?? null
})
</script>

<style scoped>
.dash-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  height: 200px;
  color: #94a3b8;
}
.dash-empty .bi { font-size: 40px; }
.dash-empty p   { font-size: 15px; }
</style>
