<template>
  <div class="page-container">

    <!-- ENCABEZADO -->
    <div class="page-header">
      <div class="header-left">
        <button class="btn-back" @click="$router.back()">
          <i class="bi bi-arrow-left"></i>
        </button>
        <div>
          <h1 class="page-title">
            <i class="bi bi-clock-history"></i> Historial del Activo
          </h1>
          <p class="page-subtitle" v-if="asset">
            <strong>{{ asset.name }}</strong>
            <span v-if="asset.location" class="ms-2 text-muted">
              <i class="bi bi-geo-alt"></i> {{ asset.location }}
            </span>
          </p>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn btn-outline-secondary" @click="exportCSV">
          <i class="bi bi-file-earmark-spreadsheet"></i> Exportar CSV
        </button>
        <button class="btn btn-outline-secondary" @click="printReport">
          <i class="bi bi-printer"></i> Imprimir / PDF
        </button>
      </div>
    </div>

    <!-- RESUMEN STATS DEL ACTIVO -->
    <div class="asset-stats" v-if="data">
      <div class="astat" v-for="s in assetStats" :key="s.label">
        <span class="astat-num" :style="{ color: s.color }">{{ s.value }}</span>
        <span class="astat-label">{{ s.label }}</span>
      </div>
    </div>

    <!-- FILTRO POR ESTADO -->
    <div class="filters-row">
      <select v-model="filterStatusId" class="form-select" style="max-width:180px"
        @change="loadHistory">
        <option value="">Todos los estados</option>
        <option v-for="s in statuses" :key="s.id" :value="s.id">{{ s.name }}</option>
      </select>
      <input v-model="search" class="form-control" placeholder="Buscar tarea..."
        style="max-width:220px" />
    </div>

    <!-- TABLA HISTORIAL (para imprimir) -->
    <div class="history-table-wrap" id="printable-area">

      <!-- Cabecera de impresión -->
      <div class="print-header">
        <h2>Historial de Tareas — {{ asset?.name }}</h2>
        <p>{{ asset?.location }} | Generado: {{ todayStr }}</p>
        <p v-if="filterStatusId">Estado: {{ statusName(Number(filterStatusId)) }}</p>
      </div>

      <div v-if="loading" class="loading-center">
        <i class="bi bi-arrow-repeat spin"></i>
      </div>

      <div v-else-if="filtered.length === 0" class="empty-state">
        <i class="bi bi-clipboard-x"></i>
        <p>No hay tareas con estos filtros</p>
      </div>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Tarea</th>
            <th class="text-center">Estado</th>
            <th>Responsable</th>
            <th class="text-center">Avance</th>
            <th class="text-right">Presupuesto</th>
            <th class="text-right">Costo real</th>
            <th>Inicio</th>
            <th>Cierre</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in filtered" :key="t.id">
            <td class="text-muted">{{ t.id }}</td>
            <td>
              <strong>{{ t.title }}</strong>
              <div v-if="t.description" class="task-desc">{{ t.description }}</div>
            </td>
            <td class="text-center">
              <span class="status-badge" :class="statusClass(t.status_id)">
                {{ t.status_name }}
              </span>
            </td>
            <td class="text-muted">{{ t.assigned_name }}</td>
            <td class="text-center">
              <div class="progress-mini">
                <div class="progress-track-sm">
                  <div class="progress-fill-sm"
                    :class="t.progress === 100 ? 'fill-green' : 'fill-blue'"
                    :style="{ width: t.progress + '%' }"></div>
                </div>
                <span class="prog-num">{{ t.progress }}%</span>
              </div>
            </td>
            <td class="text-right text-muted">${{ fmt(t.budget) }}</td>
            <td class="text-right" :class="t.actual_cost > t.budget && t.budget > 0 ? 'text-danger' : ''">
              ${{ fmt(t.actual_cost) }}
            </td>
            <td class="text-muted">{{ fmtDate(t.start_date) || '—' }}</td>
            <td class="text-muted">{{ fmtDate(t.closed_at) || '—' }}</td>
          </tr>
        </tbody>
        <tfoot>
          <tr class="total-row">
            <td colspan="5" class="text-right"><strong>Totales:</strong></td>
            <td class="text-right"><strong>${{ fmt(totalBudget) }}</strong></td>
            <td class="text-right" :class="totalCost > totalBudget && totalBudget > 0 ? 'text-danger' : ''">
              <strong>${{ fmt(totalCost) }}</strong>
            </td>
            <td colspan="2"></td>
          </tr>
        </tfoot>
      </table>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { useRoute } from "vue-router"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

const route   = useRoute()
const assetId = route.params.assetId

const asset          = ref(null)
const data           = ref(null)
const statuses       = ref([])
const loading        = ref(true)
const search         = ref("")
const filterStatusId = ref("")

const todayStr = new Date().toLocaleDateString("es-CO", {
  day:"2-digit", month:"long", year:"numeric"
})

const filtered = computed(() => {
  if (!data.value) return []
  return data.value.tasks.filter(t =>
    !search.value || t.title.toLowerCase().includes(search.value.toLowerCase())
  )
})

const totalBudget = computed(() => filtered.value.reduce((s, t) => s + (t.budget||0), 0))
const totalCost   = computed(() => filtered.value.reduce((s, t) => s + (t.actual_cost||0), 0))

const assetStats = computed(() => {
  if (!data.value) return []
  const tasks = data.value.tasks
  return [
    { label: "Total tareas",   value: tasks.length,                                 color: "#1e293b" },
    { label: "Finalizadas",    value: tasks.filter(t => t.status_id === 5).length,  color: "#065f46" },
    { label: "En curso",       value: tasks.filter(t => [2,3,4].includes(t.status_id)).length, color: "#3b82f6" },
    { label: "Pendientes",     value: tasks.filter(t => t.status_id === 1).length,  color: "#f59e0b" },
    { label: "Presup. total",  value: "$" + fmt(tasks.reduce((s,t)=>s+(t.budget||0),0)), color: "#64748b" },
    { label: "Costo real",     value: "$" + fmt(tasks.reduce((s,t)=>s+(t.actual_cost||0),0)), color: "#64748b" },
  ]
})

const STATUS_CLASSES = {
  1:"badge-orange",2:"badge-blue",3:"badge-green",
  4:"badge-purple",5:"badge-darkgreen",6:"badge-red",
}
function statusClass(id) { return STATUS_CLASSES[id] || "badge-gray" }
function statusName(id)  { return statuses.value.find(s => s.id === id)?.name || "—" }
function fmt(n)          { return Number(n||0).toLocaleString("es-CO") }
function fmtDate(iso)    { return iso ? new Date(iso).toLocaleDateString("es-CO", { day:"2-digit", month:"short", year:"numeric" }) : "" }

async function loadHistory() {
  loading.value = true
  try {
    const url = `/assets/${assetId}/history` +
      (filterStatusId.value ? `?status_id=${filterStatusId.value}` : "")
    const res = await api.get(url)
    data.value  = res.data
    asset.value = res.data.asset
  } catch {
    showToast("Error cargando historial", "error")
  } finally {
    loading.value = false
  }
}

async function loadStatuses() {
  try {
    const res = await api.get("/task-status/")
    statuses.value = res.data
  } catch {}
}

// ── Exportar CSV ────────────────────────────────────────────────
function exportCSV() {
  if (!filtered.value.length) { showToast("No hay datos para exportar", "warning"); return }

  const headers = ["ID","Título","Estado","Responsable","Avance%","Presupuesto","Costo real","Inicio","Cierre"]
  const rows = filtered.value.map(t => [
    t.id, `"${t.title}"`, t.status_name, t.assigned_name,
    t.progress, t.budget||0, t.actual_cost||0,
    fmtDate(t.start_date)||"", fmtDate(t.closed_at)||""
  ])

  const csv = [headers, ...rows].map(r => r.join(";")).join("\n")
  const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8;" })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement("a")
  a.href     = url
  a.download = `historial_${asset.value?.name?.replace(/\s+/g,"_")}_${Date.now()}.csv`
  a.click()
  URL.revokeObjectURL(url)
  showToast("CSV descargado", "success")
}

// ── Imprimir / PDF ──────────────────────────────────────────────
function printReport() {
  window.print()
}

onMounted(async () => {
  await Promise.all([loadHistory(), loadStatuses()])
})
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1200px; }
.page-header    { display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:18px; flex-wrap:wrap; gap:12px; }
.header-left    { display:flex; align-items:flex-start; gap:12px; }
.btn-back       { background:#f1f5f9; border:none; border-radius:8px; padding:8px 12px; cursor:pointer; font-size:16px; color:#475569; }
.btn-back:hover { background:#e2e8f0; }
.page-title     { font-size:20px; font-weight:700; color:#1e293b; margin:0 0 4px; display:flex; align-items:center; gap:8px; }
.page-subtitle  { font-size:13px; color:#64748b; margin:0; display:flex; align-items:center; gap:6px; }
.header-actions { display:flex; gap:8px; flex-wrap:wrap; }
.text-muted     { color:#94a3b8 !important; font-size:12px; }
.text-danger    { color:#ef4444 !important; }

/* STATS */
.asset-stats { display:flex; flex-wrap:wrap; gap:10px; margin-bottom:18px; }
.astat       { background:#fff; border-radius:10px; padding:10px 16px; box-shadow:0 1px 4px rgba(0,0,0,0.07); display:flex; align-items:baseline; gap:7px; }
.astat-num   { font-size:20px; font-weight:800; }
.astat-label { font-size:11px; color:#94a3b8; }

/* FILTROS */
.filters-row { display:flex; gap:10px; margin-bottom:14px; flex-wrap:wrap; }

/* TABLE */
.history-table-wrap { background:#fff; border-radius:14px; box-shadow:0 1px 6px rgba(0,0,0,0.08); overflow:hidden; }
.loading-center     { padding:40px; text-align:center; color:#94a3b8; }
.empty-state        { padding:48px; text-align:center; color:#94a3b8; }
.empty-state .bi    { font-size:36px; display:block; margin-bottom:10px; }
.data-table         { width:100%; border-collapse:collapse; font-size:13px; }
.data-table th      { background:#f8fafc; color:#475569; font-weight:600; font-size:11px; text-transform:uppercase; letter-spacing:0.4px; padding:11px 12px; border-bottom:1px solid #e2e8f0; }
.data-table td      { padding:11px 12px; border-bottom:1px solid #f1f5f9; vertical-align:middle; }
.data-table tr:last-child td { border-bottom:none; }
.data-table tr:hover td { background:#f8fafc; }
.total-row td       { background:#f0fdf4 !important; }
.text-center { text-align:center; }
.text-right  { text-align:right; }
.task-desc   { font-size:11px; color:#94a3b8; margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:200px; }

/* STATUS */
.status-badge    { font-size:10px; font-weight:700; padding:2px 8px; border-radius:20px; white-space:nowrap; }
.badge-orange    { background:#fff7ed; color:#c2410c; }
.badge-blue      { background:#dbeafe; color:#1e40af; }
.badge-green     { background:#dcfce7; color:#16a34a; }
.badge-purple    { background:#f3e8ff; color:#7c3aed; }
.badge-darkgreen { background:#d1fae5; color:#065f46; }
.badge-red       { background:#fef2f2; color:#b91c1c; }
.badge-gray      { background:#f1f5f9; color:#64748b; }

/* PROGRESS */
.progress-mini    { display:flex; align-items:center; gap:5px; justify-content:center; }
.progress-track-sm{ width:48px; height:5px; background:#e2e8f0; border-radius:3px; overflow:hidden; }
.progress-fill-sm { height:100%; border-radius:3px; }
.fill-blue  { background:#3b82f6; }
.fill-green { background:#22c55e; }
.prog-num   { font-size:11px; color:#64748b; min-width:26px; }

/* IMPRESIÓN */
.print-header { display:none; }

@media print {
  .print-header { display:block; margin-bottom:16px; }
  .print-header h2 { font-size:16px; }
  .btn-back, .header-actions, .filters-row, .asset-stats { display:none !important; }
  .history-table-wrap { box-shadow:none; }
  .page-container { padding:0; }
}

.spin { display:inline-block; animation:spin 0.8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
</style>
