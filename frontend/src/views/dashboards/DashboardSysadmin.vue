<template>
  <div>
    <KpiStrip :kpis="kpis" :loading="loading" />

    <!-- ALERTA PAGOS PENDIENTES -->
    <div v-if="!loading && pendingPayments > 0" class="pay-alert" @click="goToPayments">
      <div class="pay-alert-left">
        <div class="pay-alert-icon"><i class="bi bi-credit-card-2-back"></i></div>
        <div>
          <div class="pay-alert-title">
            {{ pendingPayments }} pago{{ pendingPayments !== 1 ? 's' : '' }} pendiente{{ pendingPayments !== 1 ? 's' : '' }} de revisión
          </div>
          <div class="pay-alert-sub">Haz clic para revisar y aprobar o rechazar.</div>
        </div>
      </div>
      <i class="bi bi-arrow-right-circle-fill pay-alert-arrow"></i>
    </div>

    <div class="dash-title">Dashboard — SYSADMIN</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { useRouter } from "vue-router"
import KpiStrip from "@/components/dashboard/KpiStrip.vue"
import api from "@/services/apis"

const router         = useRouter()
const loading        = ref(true)
const stats          = ref({ total_companies: 0, total_users: 0, total_assets: 0, total_tasks: 0 })
const pendingPayments = ref(0)

const kpis = computed(() => [
  { icon: "bi-buildings",       label: "Asociados registrados", value: stats.value.total_companies },
  { icon: "bi-people",          label: "Usuarios totales",      value: stats.value.total_users     },
  { icon: "bi-box-seam",        label: "Activos registrados",   value: stats.value.total_assets    },
  { icon: "bi-clipboard-check", label: "Tareas registradas",    value: stats.value.total_tasks     },
])

function goToPayments() {
  router.push("/sysadmin/payment-review")
}

onMounted(async () => {
  try {
    const [statsRes, payRes] = await Promise.all([
      api.get("/dashboard/stats"),
      api.get("/payments/pending-count"),
    ])
    stats.value          = statsRes.data
    pendingPayments.value = payRes.data.count ?? 0
  } catch {}
  loading.value = false
})
</script>

<style scoped>
.dash-title { padding: 20px 0 0; font-size: 18px; font-weight: 700; color: #1e293b; }

.pay-alert {
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px; margin: 16px 0 0;
  background: #fff7ed; border: 1.5px solid #fed7aa;
  border-radius: 12px; padding: 14px 18px;
  cursor: pointer; transition: all .2s;
}
.pay-alert:hover { background: #ffedd5; border-color: #f97316; }

.pay-alert-left { display: flex; align-items: center; gap: 14px; }
.pay-alert-icon {
  width: 44px; height: 44px; border-radius: 10px;
  background: #f97316; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.2rem; flex-shrink: 0;
}
.pay-alert-title { font-weight: 700; font-size: .95rem; color: #c2410c; }
.pay-alert-sub   { font-size: .78rem; color: #ea580c; margin-top: 2px; }
.pay-alert-arrow { font-size: 1.5rem; color: #f97316; flex-shrink: 0; }
</style>
