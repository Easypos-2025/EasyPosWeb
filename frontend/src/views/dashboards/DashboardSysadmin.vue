<template>
  <div>
    <KpiStrip :kpis="kpis" :loading="loading" />
    <div class="dash-title">Dashboard — SYSADMIN</div>
    <div class="quick-links">
      <router-link to="/sysadmin/monitor" class="btn-monitor">
        <i class="bi bi-bar-chart-line"></i> Monitor de Ventas
      </router-link>
      <router-link to="/sysadmin/admin-pe" class="btn-monitor btn-monitor--pe">
        <i class="bi bi-lightning-charge-fill"></i> Admin POS Electrónico
      </router-link>
    </div>

    <!-- Monitor de Errores -->
    <router-link to="/sysadmin/errores" class="err-card" :class="{ 'err-card--ok': !errs.sin_resolver }">
      <div class="err-head">
        <span class="err-title"><i class="bi bi-bug"></i> {{ errorsModule || "Monitor de Errores" }}</span>
        <span class="err-total">{{ errs.sin_resolver }} <small>sin resolver</small></span>
      </div>
      <div class="err-levels">
        <span class="lv lv--crit">{{ errs.criticos }} críticos</span>
        <span class="lv lv--err">{{ errs.errores }} errores</span>
        <span class="lv lv--adv">{{ errs.advertencias }} advertencias</span>
        <span class="lv lv--new">{{ errs.nuevos_24h }} nuevos 24 h</span>
        <span v-if="errs.regresiones" class="lv lv--reg">↺ {{ errs.regresiones }} regresiones</span>
        <span v-if="errs.seguridad" class="lv lv--sec">{{ errs.seguridad }} seguridad</span>
        <span v-if="errs.version" class="lv lv--ver">{{ errs.version }} por versión desactualizada</span>
      </div>
      <div v-if="errs.por_tipo?.length" class="err-types">
        <span v-for="t in errs.por_tipo" :key="t.tipo_error" class="err-type">{{ tipoLabel(t.tipo_error) }}: <b>{{ t.n }}</b></span>
      </div>
      <div v-if="errs.ultimo" class="err-last">
        Último: <b>{{ errs.ultimo.ref_code }}</b> · {{ errs.ultimo.titulo }}
      </div>
      <div v-else class="err-last">Sin errores pendientes 🎉</div>
    </router-link>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue"
import KpiStrip from "@/components/dashboard/KpiStrip.vue"
import api from "@/services/apis"
import { useModuleName } from "@/composables/useModuleName"

const loading     = ref(true)
const stats       = ref({ total_companies: 0 })
const connections = ref({ companies: [], users: [] })
const errs        = ref({ sin_resolver: 0, criticos: 0, errores: 0, advertencias: 0, nuevos_24h: 0, regresiones: 0, seguridad: 0, version: 0, por_tipo: [], ultimo: null })
const { moduleName: errorsModule } = useModuleName("/sysadmin/errores")
let _liveTimer    = null

const LIVE_INTERVAL = 20000

const TIPO_LABEL = {
  SERVIDOR: "Servidor", BASE_DATOS: "Base de datos", VISTA: "Vista", RED: "Red", SINCRONIZACION: "Sincronización",
  IMPRESION: "Impresión", INTEGRACION: "Integración", SEGURIDAD: "Seguridad", VERSION_DESACTUALIZADA: "Versión",
}
const tipoLabel = t => TIPO_LABEL[t] || t

const kpis = computed(() => [
  { icon: "bi-buildings",   label: "Asociados registrados",  value: stats.value.total_companies        },
  { icon: "bi-building",    label: "Empresas activas ahora", value: connections.value.companies.length, to: "/sysadmin/sesiones" },
  { icon: "bi-people-fill", label: "Usuarios activos ahora", value: connections.value.users.length,     to: "/sysadmin/sesiones" },
  { icon: "bi-bug-fill",    label: "Errores sin resolver",   value: errs.value.sin_resolver,            to: "/sysadmin/errores" },
])

async function loadLiveCounts() {
  try {
    const res = await api.get("/dashboard/sysadmin/active-sessions")
    connections.value = res.data
  } catch {}
}

async function loadErrors() {
  try {
    const res = await api.get("/api/error-log/summary")
    errs.value = res.data
  } catch {}
}

onMounted(async () => {
  try {
    const res = await api.get("/dashboard/stats")
    stats.value = res.data
  } catch {}
  loading.value = false
  await Promise.all([loadLiveCounts(), loadErrors()])
  _liveTimer = setInterval(() => { loadLiveCounts(); loadErrors() }, LIVE_INTERVAL)
})

onUnmounted(() => clearInterval(_liveTimer))

</script>

<style scoped>
.dash-title {
  padding: 20px 0 12px;
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
}

.quick-links {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.btn-monitor {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 22px;
  background: #0f172a;
  color: #fff;
  border-radius: 8px;
  font-weight: 600;
  font-size: 14px;
  text-decoration: none;
  transition: background 0.15s;
}
.btn-monitor:hover { background: #1e3a5f; color: #fff; }
.btn-monitor--pe { background: #92400e; }
.btn-monitor--pe:hover { background: #78350f; color: #fff; }

/* Monitor de Errores */
.err-card {
  display: block;
  margin-top: 16px;
  max-width: 720px;
  background: #fff;
  border: 1px solid #fecaca;
  border-left: 5px solid #dc2626;
  border-radius: 10px;
  padding: 14px 16px;
  text-decoration: none;
  color: #0f172a;
  transition: box-shadow 0.15s;
}
.err-card:hover { box-shadow: 0 4px 14px rgba(15, 23, 42, 0.1); color: #0f172a; }
.err-card--ok { border-color: #bbf7d0; border-left-color: #16a34a; }
.err-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.err-title { font-weight: 700; display: flex; align-items: center; gap: 8px; }
.err-total { font-size: 24px; font-weight: 800; color: #b91c1c; white-space: nowrap; }
.err-card--ok .err-total { color: #166534; }
.err-total small { font-size: 12px; font-weight: 600; color: #64748b; }
.err-levels { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
.lv { font-size: 12px; font-weight: 700; padding: 3px 10px; border-radius: 10px; }
.lv--crit { background: #dc2626; color: #fff; }
.lv--err  { background: #ffedd5; color: #9a3412; }
.lv--adv  { background: #fef3c7; color: #78350f; }
.lv--new  { background: #dbeafe; color: #1e40af; }
.lv--reg  { background: #fef3c7; color: #b45309; }
.lv--sec  { background: #ede9fe; color: #5b21b6; }
.lv--ver  { background: #f1f5f9; color: #475569; }
.err-types { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 8px; font-size: 12px; color: #475569; }
.err-last { margin-top: 8px; font-size: 13px; color: #475569; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

@media (max-width: 768px) {
  .btn-monitor { flex: 1; justify-content: center; }
  .err-card { max-width: none; }
}
@media (max-width: 576px) {
  .btn-monitor { font-size: 12px; padding: 8px 14px; }
  .err-total { font-size: 20px; }
  .err-head { flex-wrap: wrap; }
  .err-last { white-space: normal; }
}
</style>
