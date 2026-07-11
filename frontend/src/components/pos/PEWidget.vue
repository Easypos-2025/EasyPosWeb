<template>
  <div class="pe-widget" @click="$router.push('/pos/facturas-electronicas')">
    <div class="pe-widget-header">
      <span class="pe-widget-title">
        <i class="bi bi-lightning-charge-fill pe-icon"></i>
        Facturación Electrónica DIAN
      </span>
      <span class="pe-widget-link">Ver todas <i class="bi bi-arrow-right"></i></span>
    </div>

    <div v-if="loading" class="pe-widget-loading">
      <i class="bi bi-arrow-repeat spin"></i> Cargando…
    </div>

    <div v-else class="pe-widget-kpis">
      <div class="pe-kpi pe-kpi--pend">
        <span class="pe-kpi-val">{{ pendientes }}</span>
        <span class="pe-kpi-lbl"><i class="bi bi-clock-history"></i> Pendientes DIAN</span>
      </div>
      <div class="pe-kpi-divider"></div>
      <div class="pe-kpi pe-kpi--ok">
        <span class="pe-kpi-val">{{ enviadas }}</span>
        <span class="pe-kpi-lbl"><i class="bi bi-check-circle-fill"></i> Enviadas hoy</span>
      </div>
    </div>

    <!-- Alerta si hay pendientes -->
    <div v-if="!loading && pendientes > 0" class="pe-widget-alert">
      <i class="bi bi-exclamation-triangle-fill"></i>
      {{ pendientes }} {{ pendientes === 1 ? 'factura pendiente' : 'facturas pendientes' }} de envío a la DIAN
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useCompanyStore } from '@/stores/companyStore'
import api from '@/services/apis'

const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id)

const loading        = ref(false)
const pendientes     = ref(0)
const enviadas       = ref(0)
const valorPendiente = ref(0)
let   _timer         = null

async function cargar() {
  if (!companyId.value) return
  loading.value = true
  try {
    const today = new Date().toLocaleDateString('en-CA', { timeZone: 'America/Bogota' })
    const [r0, r1] = await Promise.all([
      api.get('/company-configs/pe-facturas-cliente', { params: { fe: 0 } }),
      api.get('/company-configs/pe-facturas-cliente', { params: { fe: 1, date: today, mode: 'day' } }),
    ])
    const pend = r0.data || []
    pendientes.value     = pend.length
    valorPendiente.value = pend.reduce((s, r) => s + Number(r.valor || 0), 0)
    enviadas.value       = (r1.data || []).length
  } catch { /* silencioso */ }
  loading.value = false
}

function iniciarTimer() {
  _timer = setInterval(cargar, 2 * 60 * 1000) // refresca cada 2 minutos
}

function fmt(v) {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency', currency: 'COP', maximumFractionDigits: 0
  }).format(v || 0)
}

onMounted(() => {
  if (companyId.value) cargar()
  iniciarTimer()
})

onUnmounted(() => {
  if (_timer) clearInterval(_timer)
})

watch(companyId, (v) => {
  if (v) cargar()
})
</script>

<style scoped>
.pe-widget {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border-radius: 14px;
  padding: 16px 20px;
  cursor: pointer;
  transition: transform .15s, box-shadow .15s;
  margin-bottom: 4px;
  border: 1px solid #334155;
}
.pe-widget:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,.25);
}

.pe-widget-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.pe-widget-title {
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 8px;
}
.pe-icon { color: #fbbf24; font-size: 16px; }

.pe-widget-link {
  font-size: 12px;
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: color .15s;
}
.pe-widget:hover .pe-widget-link { color: #e2e8f0; }

.pe-widget-loading {
  color: #94a3b8;
  font-size: 13px;
  padding: 8px 0;
}

.pe-widget-kpis {
  display: flex;
  align-items: center;
  gap: 0;
}
.pe-kpi {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 0 8px;
}
.pe-kpi:first-child { padding-left: 0; }

.pe-kpi-divider {
  width: 1px;
  height: 36px;
  background: rgba(255,255,255,.12);
  flex-shrink: 0;
}

.pe-kpi-val {
  font-size: 22px;
  font-weight: 900;
  line-height: 1;
}
.pe-kpi--pend .pe-kpi-val  { color: #fca5a5; }
.pe-kpi--ok   .pe-kpi-val  { color: #86efac; }
.pe-kpi--val  .pe-kpi-val  { color: #93c5fd; font-size: 16px; }

.pe-kpi-lbl {
  font-size: 11px;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 600;
}
.pe-kpi--pend .pe-kpi-lbl { color: #f87171; }
.pe-kpi--ok   .pe-kpi-lbl { color: #4ade80; }
.pe-kpi--val  .pe-kpi-lbl { color: #60a5fa; }

.pe-widget-alert {
  margin-top: 12px;
  background: rgba(220, 38, 38, .15);
  border: 1px solid rgba(220, 38, 38, .3);
  border-radius: 8px;
  padding: 7px 12px;
  font-size: 12px;
  color: #fca5a5;
  display: flex;
  align-items: center;
  gap: 7px;
  font-weight: 600;
}

@media (max-width: 576px) {
  .pe-widget { padding: 14px 16px; }
  .pe-kpi-val { font-size: 18px; }
  .pe-kpi--val .pe-kpi-val { font-size: 13px; }
}

.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from { transform: rotate(0) } to { transform: rotate(360deg) } }
</style>
