<template>
  <div>
    <!-- Widget PE: visible solo si la company tiene POS Electrónico activo y no es SYSADMIN -->
    <PEWidget v-if="hasPE" class="pe-widget-top" />
    <!-- Widget Parking: visible cuando el módulo Parking Service está activo -->
    <ParkingWidget v-if="hasParking" />

    <component :is="activeDashboard" v-if="activeDashboard" />
    <div v-else class="dash-empty">
      <i class="bi bi-grid-3x3-gap"></i>
      <p>Sin dashboard configurado para este perfil.</p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from "vue"
import { useRouter } from "vue-router"
import { useCompanyStore } from "@/stores/companyStore"
import PEWidget      from "@/components/pos/PEWidget.vue"
import ParkingWidget from "@/components/parking/ParkingWidget.vue"

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
import DashboardCompraventa   from "@/views/dashboards/DashboardCompraventa.vue"
import DashboardHipotecas     from "@/views/dashboards/DashboardHipotecas.vue"
import DashboardPanaderia     from "@/views/dashboards/DashboardPanaderia.vue"
import DashboardServicecar    from "@/views/dashboards/DashboardServicecar.vue"
import DashboardFerreterias   from "@/views/dashboards/DashboardFerreterias.vue"
import DashboardParqueadero   from "@/views/parqueadero/DashboardParqueaderoView.vue"

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
  15: DashboardServicecar,     // Servicars
  16: DashboardPanaderia,      // Panaderías - Pastelerías
  17: DashboardHipotecas,      // Hipotecas - Cobros
  19: DashboardCompraventa,    // Compraventas - Joyerías
  20: DashboardFerreterias,    // Ferreterías
  24: DashboardParqueadero,    // Parqueadero
}

const router       = useRouter()
const companyStore  = useCompanyStore()

onMounted(() => {
  const userData  = JSON.parse(localStorage.getItem("user") || "{}")
  const homeRoute = userData.home_route
  if (homeRoute && homeRoute !== "/dashboard") {
    router.replace(homeRoute)
  }
})

const activeDashboard = computed(() => {
  const profileId = companyStore.selectedCompany?.business_profile_id
  const dash = DASHBOARD_MAP[profileId] ?? null
  if (dash === DashboardSysadmin && !companyStore.isSystem) return null
  return dash
})

const hasPE = computed(() =>
  !companyStore.isSystem &&
  companyStore.billingConfig?.has_pos_electronico == 1
)

const hasParking = computed(() =>
  !companyStore.isSystem &&
  companyStore.billingConfig?.has_parking == 1
)
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
.pe-widget-top  { margin: 0 0 16px; }
</style>
