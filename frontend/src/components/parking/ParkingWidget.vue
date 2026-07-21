<template>
  <div class="pkw-widget" @click="$router.push('/parking/caja')">
    <div class="pkw-header">
      <span class="pkw-title">
        <i class="bi bi-p-circle-fill pkw-icon"></i>
        Parking Service
      </span>
      <span class="pkw-link">Ver cobros <i class="bi bi-arrow-right"></i></span>
    </div>

    <div v-if="loading" class="pkw-loading">
      <i class="bi bi-arrow-repeat spin"></i> Cargando…
    </div>

    <div v-else class="pkw-kpis">
      <div class="pkw-kpi pkw-kpi--pendientes">
        <span class="pkw-kpi-val">{{ pendientes }}</span>
        <span class="pkw-kpi-lbl"><i class="bi bi-hourglass-split"></i> Pendientes cobro</span>
      </div>
      <div class="pkw-kpi-divider"></div>
      <div class="pkw-kpi pkw-kpi--ocupadas">
        <span class="pkw-kpi-val">{{ ocupadas }}</span>
        <span class="pkw-kpi-lbl"><i class="bi bi-car-front-fill"></i> Ocupadas</span>
      </div>
      <div class="pkw-kpi-divider"></div>
      <div class="pkw-kpi pkw-kpi--pagadas">
        <span class="pkw-kpi-val">{{ pagadas }}</span>
        <span class="pkw-kpi-lbl"><i class="bi bi-check-circle-fill"></i> Pagadas hoy</span>
      </div>
    </div>

    <div v-if="!loading && pendientes > 0" class="pkw-alert">
      <i class="bi bi-exclamation-triangle-fill"></i>
      {{ pendientes }} {{ pendientes === 1 ? 'orden pendiente' : 'órdenes pendientes' }} de cobro
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useCompanyStore } from '@/stores/companyStore'
import api from '@/services/apis'

const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id_company)

const loading    = ref(false)
const pendientes = ref(0)
const ocupadas   = ref(0)
const pagadas    = ref(0)
let   _timer     = null

async function cargar() {
  if (!companyId.value) return
  loading.value = true
  try {
    const hoy = new Date().toISOString().slice(0, 10)
    const [r1, r2, r3] = await Promise.all([
      api.get('/api/parking/orders', { params: { company_id: companyId.value, fecha: hoy, estado: 'registrado' } }),
      api.get('/api/parking/stats',  { params: { company_id: companyId.value, fecha: hoy } }),
      api.get('/api/parking/orders', { params: { company_id: companyId.value, fecha: hoy, estado: 'pagado' } }),
    ])
    pendientes.value = r1.data.length
    ocupadas.value   = r2.data.ocupadas || 0
    pagadas.value    = r3.data.length
  } catch {}
  loading.value = false
}

onMounted(() => {
  cargar()
  _timer = setInterval(cargar, 60000)
})
onUnmounted(() => { if (_timer) clearInterval(_timer) })
</script>

<style scoped>
.pkw-widget {
  background: #fff; border-radius: 12px; padding: 14px 18px; cursor: pointer;
  border: 1px solid #e9ecef; margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,.06); transition: box-shadow .2s;
}
.pkw-widget:hover { box-shadow: 0 4px 14px rgba(0,0,0,.1); }
.pkw-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 12px;
}
.pkw-title { font-weight: 700; font-size: .9rem; display: flex; align-items: center; gap: 7px; }
.pkw-icon  { color: #0d6efd; font-size: 1.1rem; }
.pkw-link  { font-size: .78rem; color: #0d6efd; display: flex; align-items: center; gap: 4px; }

.pkw-loading { text-align: center; padding: 10px; color: #6c757d; font-size: .85rem; }

.pkw-kpis { display: flex; align-items: center; gap: 4px; }
.pkw-kpi { flex: 1; text-align: center; padding: 4px 6px; }
.pkw-kpi-val { display: block; font-size: 1.4rem; font-weight: 900; line-height: 1; }
.pkw-kpi-lbl { display: block; font-size: .7rem; color: #6c757d; margin-top: 2px; white-space: nowrap; }
.pkw-kpi--pendientes .pkw-kpi-val { color: #fd7e14; }
.pkw-kpi--ocupadas   .pkw-kpi-val { color: #dc3545; }
.pkw-kpi--pagadas    .pkw-kpi-val { color: #198754; }
.pkw-kpi-divider { width: 1px; height: 36px; background: #e9ecef; flex-shrink: 0; }

.pkw-alert {
  margin-top: 10px; background: #fff3cd; border-radius: 8px;
  padding: 7px 12px; font-size: .82rem; color: #664d03;
  display: flex; align-items: center; gap: 8px;
}
.pkw-alert i { color: #fd7e14; }

.spin { animation: pkw-spin .8s linear infinite; }
@keyframes pkw-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
