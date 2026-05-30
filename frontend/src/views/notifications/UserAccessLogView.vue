<template>
  <div class="page-container">

    <div class="page-header">
      <div>
        <h1 class="page-title"><i class="bi bi-person-lines-fill me-2"></i>Log de Accesos</h1>
        <p class="page-subtitle">Registro de entradas y salidas de usuarios al sistema</p>
      </div>
      <button class="btn btn-outline-secondary btn-sm" @click="load">
        <i class="bi bi-arrow-clockwise"></i> Actualizar
      </button>
    </div>

    <!-- KPIs -->
    <div class="kpi-bar">
      <div class="kpi-card">
        <span class="kpi-num">{{ filtered.length }}</span>
        <span class="kpi-lbl">Registros</span>
      </div>
      <div class="kpi-card kpi-green">
        <span class="kpi-num">{{ filtered.filter(n => isEntry(n)).length }}</span>
        <span class="kpi-lbl">Entradas</span>
      </div>
      <div class="kpi-card kpi-red">
        <span class="kpi-num">{{ filtered.filter(n => !isEntry(n)).length }}</span>
        <span class="kpi-lbl">Salidas</span>
      </div>
    </div>

    <!-- Filtros -->
    <div class="filters-row">
      <input v-model="search" class="form-control" placeholder="Buscar usuario..." style="max-width:220px" />
      <select v-model="filterType" class="form-select" style="max-width:160px">
        <option value="">Entradas y salidas</option>
        <option value="entry">Solo entradas</option>
        <option value="exit">Solo salidas</option>
      </select>
      <CustomDatePicker v-model="filterFrom" />
      <CustomDatePicker v-model="filterTo" />
      <button v-if="search || filterType || filterFrom || filterTo" class="btn btn-outline-secondary btn-sm" @click="clearFilters">
        <i class="bi bi-x"></i> Limpiar
      </button>
    </div>

    <!-- Tabla -->
    <div class="table-card">
      <div v-if="loading" class="table-loading"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Tipo</th>
            <th>Usuario</th>
            <th>Detalle</th>
            <th class="text-center">Fecha y hora</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="n in filtered" :key="n.id">
            <td>
              <span class="access-badge" :class="isEntry(n) ? 'badge-entry' : 'badge-exit'">
                <i :class="isEntry(n) ? 'bi bi-box-arrow-in-right' : 'bi bi-box-arrow-left'"></i>
                {{ isEntry(n) ? 'Entrada' : 'Salida' }}
              </span>
            </td>
            <td><strong>{{ n.sender_name }}</strong></td>
            <td class="text-muted">{{ n.message }}</td>
            <td class="text-center text-muted">{{ fmtDate(n.created_at) }}</td>
          </tr>
          <tr v-if="!loading && filtered.length === 0">
            <td colspan="4" class="text-center text-muted py-4">
              <i class="bi bi-person-x" style="font-size:28px;display:block;margin-bottom:8px"></i>
              No hay registros con estos filtros
            </td>
          </tr>
        </tbody>
      </table>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import CustomDatePicker from "@/components/common/CustomDatePicker.vue"

const items     = ref([])
const loading   = ref(true)
const search    = ref("")
const filterType = ref("")
const filterFrom = ref("")
const filterTo   = ref("")

function isEntry(n) {
  const t = (n.title || "").toLowerCase()
  return t.includes("entrada") || t.includes("ingreso") || t.includes("login")
}

function fmtDate(iso) {
  if (!iso) return "—"
  const d = new Date(iso)
  return d.toLocaleDateString("es-CO", { day: "2-digit", month: "short", year: "numeric" }) +
         " " + d.toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" })
}

function clearFilters() {
  search.value = ""; filterType.value = ""; filterFrom.value = ""; filterTo.value = ""
}

// Solo notificaciones de acceso (entrada/salida)
const accessItems = computed(() =>
  items.value.filter(n => {
    const t = (n.title || "").toLowerCase()
    return t.includes("entrada") || t.includes("salida") || t.includes("ingreso") ||
           t.includes("login") || t.includes("logout") || t.includes("acceso")
  })
)

const filtered = computed(() => {
  let list = accessItems.value
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(n => (n.sender_name || "").toLowerCase().includes(q))
  }
  if (filterType.value === "entry") list = list.filter(n => isEntry(n))
  if (filterType.value === "exit")  list = list.filter(n => !isEntry(n))
  if (filterFrom.value) list = list.filter(n => n.created_at >= filterFrom.value)
  if (filterTo.value)   list = list.filter(n => n.created_at.slice(0, 10) <= filterTo.value)
  return list
})

async function load() {
  loading.value = true
  try {
    const res = await api.get("/user-notifications/inbox")
    items.value = res.data
  } catch { showToast("Error cargando log de accesos", "error") }
  finally { loading.value = false }
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1000px; }
.page-header    { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; gap: 12px; flex-wrap: wrap; }
.page-title     { font-size: 22px; font-weight: 700; color: #1e293b; margin: 0 0 4px; }
.page-subtitle  { font-size: 13px; color: #64748b; margin: 0; }

.kpi-bar  { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
.kpi-card { background: #fff; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.07); padding: 10px 18px; display: flex; align-items: baseline; gap: 8px; }
.kpi-num  { font-size: 22px; font-weight: 800; color: #1e293b; }
.kpi-lbl  { font-size: 12px; color: #94a3b8; }
.kpi-green .kpi-num { color: #16a34a; }
.kpi-red   .kpi-num { color: #ef4444; }

.filters-row { display: flex; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; align-items: center; }

.table-card    { background: #fff; border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,.08); overflow-x: auto; }
.table-loading { padding: 40px; text-align: center; color: #94a3b8; }
.data-table    { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { background: #f8fafc; color: #475569; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: .4px; padding: 10px 14px; border-bottom: 1px solid #e2e8f0; }
.data-table td { padding: 11px 14px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: #f8fafc; }
.text-center { text-align: center; }
.text-muted  { color: #94a3b8; font-size: 12px; }
.py-4        { padding: 32px 0; }

.access-badge { font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 20px; display: inline-flex; align-items: center; gap: 4px; }
.badge-entry  { background: #dcfce7; color: #16a34a; }
.badge-exit   { background: #fef2f2; color: #b91c1c; }

.btn { display: inline-flex; align-items: center; gap: 6px; padding: 7px 14px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; }
.btn-outline-secondary { background: #f8fafc; color: #475569; border: 1.5px solid #e2e8f0; }
.btn-sm { padding: 5px 10px; font-size: 12px; }

.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

@media (max-width: 768px) {
  .page-container { padding: 14px; }
  .filters-row .form-control,
  .filters-row .form-select { max-width: 100% !important; }
}
@media (max-width: 576px) {
  .page-container { padding: 10px; }
  .filters-row { flex-direction: column; }
}
</style>
