<template>
  <div class="page-container">

    <!-- ENCABEZADO -->
    <div class="page-header">
      <div>
        <h1 class="page-title"><i class="bi bi-file-earmark-bar-graph"></i> Reporte General de Tareas</h1>
        <p class="page-subtitle">Exporta y analiza todas las tareas del período</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-outline-secondary" @click="exportCSV" :disabled="!filtered.length">
          <i class="bi bi-file-earmark-spreadsheet"></i> Exportar CSV
        </button>
        <button class="btn btn-outline-secondary" @click="window.print()">
          <i class="bi bi-printer"></i> Imprimir / PDF
        </button>
      </div>
    </div>

    <!-- FILTROS -->
    <div class="filters-card">
      <div class="filters-grid">
        <div class="fg">
          <label>Desde</label>
          <input v-model="filterFrom" type="date" class="form-control" />
        </div>
        <div class="fg">
          <label>Hasta</label>
          <input v-model="filterTo" type="date" class="form-control" />
        </div>
        <div class="fg">
          <label>Estado</label>
          <select v-model="filterStatus" class="form-select">
            <option value="">Todos</option>
            <option v-for="s in statuses" :key="s.id" :value="s.id">{{ s.name }}</option>
          </select>
        </div>
        <div class="fg">
          <label>Task Leader</label>
          <select v-model="filterUser" class="form-select">
            <option value="">Todos</option>
            <option :value="-1">Sin asignar</option>
            <option v-for="u in users" :key="u.id" :value="u.id">{{ u.nombre }}</option>
          </select>
        </div>
        <div class="fg">
          <label>Buscar</label>
          <input v-model="search" class="form-control" placeholder="Título o descripción..." />
        </div>
        <div class="fg actions-fg">
          <label>&nbsp;</label>
          <button class="btn btn-primary" @click="applyFilters">
            <i class="bi bi-funnel"></i> Filtrar
          </button>
          <button class="btn btn-secondary" @click="clearFilters">
            <i class="bi bi-x"></i> Limpiar
          </button>
        </div>
      </div>
    </div>

    <!-- RESUMEN RÁPIDO -->
    <div class="quick-stats" v-if="filtered.length > 0">
      <div class="qs-item">
        <strong>{{ filtered.length }}</strong> tareas
      </div>
      <div class="qs-item">
        <strong>${{ fmt(totals.budget) }}</strong> presupuesto
      </div>
      <div class="qs-item" :class="totals.cost > totals.budget && totals.budget > 0 ? 'qs-red' : ''">
        <strong>${{ fmt(totals.cost) }}</strong> costo real
      </div>
      <div class="qs-item">
        <strong>{{ avgProgress }}%</strong> avance promedio
      </div>
      <div class="qs-item qs-green">
        <strong>{{ countDone }}</strong> finalizadas
      </div>
      <div class="qs-item qs-red" v-if="countOverdue > 0">
        <strong>{{ countOverdue }}</strong> atrasadas
      </div>
    </div>

    <!-- TABLA PRINTABLE -->
    <div id="print-area">

      <!-- Cabecera impresión -->
      <div class="print-header">
        <h2>Reporte General de Tareas</h2>
        <p>Generado: {{ todayStr }}
          <span v-if="filterFrom || filterTo"> | Período: {{ filterFrom || '—' }} al {{ filterTo || 'hoy' }}</span>
        </p>
      </div>

      <div v-if="loading" class="loading-center">
        <i class="bi bi-arrow-repeat spin"></i> Cargando...
      </div>

      <div v-else-if="filtered.length === 0" class="empty-state">
        <i class="bi bi-clipboard-x"></i>
        <p>No hay tareas con estos filtros</p>
      </div>

      <div v-else class="table-card">
        <table class="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Tarea</th>
              <th class="text-center">Estado</th>
              <th>Task Leader</th>
              <th class="text-center">Avance</th>
              <th class="text-right">Presupuesto</th>
              <th class="text-right">Costo</th>
              <th>Inicio</th>
              <th>Límite</th>
              <th>Cierre</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in filtered" :key="t.id"
              :class="{ 'row-overdue': isOverdue(t) }">
              <td class="text-muted">{{ t.id }}</td>
              <td>
                <strong>{{ t.title }}</strong>
                <div v-if="t.description" class="task-desc">{{ t.description }}</div>
              </td>
              <td class="text-center">
                <span class="status-badge" :class="statusClass(t.status_id)">{{ t.status_name }}</span>
              </td>
              <td class="text-muted">{{ userName(t.assigned_to) }}</td>
              <td class="text-center">
                <div class="progress-mini">
                  <div class="progress-track-sm">
                    <div class="progress-fill-sm"
                      :class="t.progress===100?'fill-green':'fill-blue'"
                      :style="{ width: t.progress+'%' }"></div>
                  </div>
                  <span class="prog-num">{{ t.progress }}%</span>
                </div>
              </td>
              <td class="text-right text-muted">${{ fmt(t.budget_labor_cost) }}</td>
              <td class="text-right" :class="t.actual_labor_cost > t.budget_labor_cost && t.budget_labor_cost > 0 ? 'text-danger' : ''">
                ${{ fmt(t.actual_labor_cost) }}
              </td>
              <td class="text-muted">{{ fmtDate(t.start_date)||'—' }}</td>
              <td class="text-muted" :class="isOverdue(t)?'text-danger':''">{{ fmtDate(t.due_date)||'—' }}</td>
              <td class="text-muted">{{ fmtDate(t.closed_at)||'—' }}</td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="total-row">
              <td colspan="5" class="text-right"><strong>Totales ({{ filtered.length }} tareas):</strong></td>
              <td class="text-right"><strong>${{ fmt(totals.budget) }}</strong></td>
              <td class="text-right" :class="totals.cost > totals.budget && totals.budget > 0 ? 'text-danger' : ''">
                <strong>${{ fmt(totals.cost) }}</strong>
              </td>
              <td colspan="3"></td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

const allTasks  = ref([])
const statuses  = ref([])
const users     = ref([])
const loading   = ref(true)

const filterFrom   = ref("")
const filterTo     = ref("")
const filterStatus = ref("")
const filterUser   = ref("")
const search       = ref("")

const todayStr = new Date().toLocaleDateString("es-CO", {
  day:"2-digit", month:"long", year:"numeric"
})

const filtered = computed(() => {
  return allTasks.value.filter(t => {
    const matchSearch = !search.value ||
      t.title?.toLowerCase().includes(search.value.toLowerCase())
    const matchStatus = !filterStatus.value || t.status_id === Number(filterStatus.value)
    const matchUser   = filterUser.value === ""
      ? true : filterUser.value === -1 ? !t.assigned_to : t.assigned_to === Number(filterUser.value)

    let matchFrom = true, matchTo = true
    if (filterFrom.value && t.created_at)
      matchFrom = new Date(t.created_at) >= new Date(filterFrom.value)
    if (filterTo.value && t.created_at)
      matchTo   = new Date(t.created_at) <= new Date(filterTo.value + "T23:59:59")

    return matchSearch && matchStatus && matchUser && matchFrom && matchTo
  })
})

const totals = computed(() => ({
  budget: filtered.value.reduce((s, t) => s + (t.budget_labor_cost||0), 0),
  cost:   filtered.value.reduce((s, t) => s + (t.actual_labor_cost||0), 0),
}))

const avgProgress = computed(() => {
  if (!filtered.value.length) return 0
  return Math.round(filtered.value.reduce((s, t) => s + (t.progress||0), 0) / filtered.value.length)
})

const countDone    = computed(() => filtered.value.filter(t => t.status_id === 5).length)
const countOverdue = computed(() => filtered.value.filter(t => isOverdue(t)).length)

const STATUS_CLASSES = {
  1:"badge-orange",2:"badge-blue",3:"badge-green",
  4:"badge-purple",5:"badge-darkgreen",6:"badge-red",
}
function statusClass(id) { return STATUS_CLASSES[id] || "badge-gray" }
function userName(id)    { return users.value.find(u => u.id === id)?.nombre || "—" }
function isOverdue(t)    { return t.due_date && new Date(t.due_date) < new Date() && ![5,6].includes(t.status_id) }
function fmt(n)          { return Number(n||0).toLocaleString("es-CO") }
function fmtDate(iso)    { return iso ? new Date(iso).toLocaleDateString("es-CO", { day:"2-digit", month:"short", year:"numeric" }) : "" }

function applyFilters()  { /* Los filtros son reactivos, solo para trigger visual */ }
function clearFilters()  {
  filterFrom.value = ""; filterTo.value = ""; filterStatus.value = ""
  filterUser.value = ""; search.value = ""
}

function exportCSV() {
  if (!filtered.value.length) return
  const headers = ["ID","Título","Estado","Task Leader","Avance%","Presupuesto","Costo real","Inicio","Límite","Cierre"]
  const rows = filtered.value.map(t => [
    t.id, `"${t.title}"`, t.status_name, userName(t.assigned_to),
    t.progress, t.budget_labor_cost||0, t.actual_labor_cost||0,
    fmtDate(t.start_date)||"", fmtDate(t.due_date)||"", fmtDate(t.closed_at)||""
  ])
  const csv  = [headers, ...rows].map(r => r.join(";")).join("\n")
  const blob = new Blob(["﻿" + csv], { type:"text/csv;charset=utf-8;" })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement("a")
  a.href = url; a.download = `reporte_tareas_${Date.now()}.csv`
  a.click(); URL.revokeObjectURL(url)
  showToast("CSV descargado", "success")
}

async function load() {
  loading.value = true
  try {
    const [tRes, sRes, uRes] = await Promise.all([
      api.get("/tasks/"),
      api.get("/task-status/"),
      api.get("/users/"),
    ])
    allTasks.value = tRes.data
    statuses.value = sRes.data
    users.value    = uRes.data
  } catch {
    showToast("Error cargando datos", "error")
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1300px; }
.page-header    { display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:18px; flex-wrap:wrap; gap:12px; }
.page-title     { font-size:20px; font-weight:700; color:#1e293b; margin-bottom:4px; display:flex; align-items:center; gap:8px; }
.page-subtitle  { font-size:13px; color:#64748b; }
.header-actions { display:flex; gap:8px; flex-wrap:wrap; }

/* FILTERS */
.filters-card  { background:#fff; border-radius:14px; box-shadow:0 1px 6px rgba(0,0,0,0.08); padding:16px 20px; margin-bottom:16px; }
.filters-grid  { display:grid; grid-template-columns:repeat(auto-fill, minmax(160px, 1fr)); gap:12px; align-items:end; }
.fg            { display:flex; flex-direction:column; gap:4px; }
.fg label      { font-size:12px; font-weight:600; color:#374151; }
.actions-fg    { flex-direction:row; gap:8px; align-items:flex-end; }

/* QUICK STATS */
.quick-stats { display:flex; flex-wrap:wrap; gap:10px; margin-bottom:14px; }
.qs-item     { background:#fff; border-radius:10px; padding:8px 14px; box-shadow:0 1px 4px rgba(0,0,0,0.07); font-size:13px; color:#64748b; }
.qs-item strong { font-size:16px; font-weight:800; color:#1e293b; margin-right:4px; }
.qs-green strong { color:#16a34a; }
.qs-red   strong { color:#ef4444; }

/* TABLE */
.table-card   { background:#fff; border-radius:14px; box-shadow:0 1px 6px rgba(0,0,0,0.08); overflow:hidden; }
.loading-center { padding:40px; text-align:center; color:#94a3b8; }
.empty-state  { padding:48px; text-align:center; color:#94a3b8; }
.empty-state .bi { font-size:36px; display:block; margin-bottom:10px; }
.data-table   { width:100%; border-collapse:collapse; font-size:12px; }
.data-table th{ background:#f8fafc; color:#475569; font-weight:600; font-size:11px; text-transform:uppercase; letter-spacing:0.4px; padding:10px 11px; border-bottom:1px solid #e2e8f0; }
.data-table td{ padding:10px 11px; border-bottom:1px solid #f1f5f9; vertical-align:middle; }
.data-table tr:last-child td { border-bottom:none; }
.data-table tr:hover td { background:#f8fafc; }
.row-overdue td { background:#fff5f5 !important; }
.total-row td { background:#f0fdf4 !important; }
.text-center { text-align:center; }
.text-right  { text-align:right; }
.text-muted  { color:#94a3b8 !important; }
.text-danger { color:#ef4444 !important; }
.task-desc   { font-size:10px; color:#94a3b8; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:180px; }

.status-badge    { font-size:10px; font-weight:700; padding:2px 7px; border-radius:20px; white-space:nowrap; }
.badge-orange    { background:#fff7ed; color:#c2410c; }
.badge-blue      { background:#dbeafe; color:#1e40af; }
.badge-green     { background:#dcfce7; color:#16a34a; }
.badge-purple    { background:#f3e8ff; color:#7c3aed; }
.badge-darkgreen { background:#d1fae5; color:#065f46; }
.badge-red       { background:#fef2f2; color:#b91c1c; }
.badge-gray      { background:#f1f5f9; color:#64748b; }

.progress-mini    { display:flex; align-items:center; gap:4px; justify-content:center; }
.progress-track-sm{ width:42px; height:4px; background:#e2e8f0; border-radius:2px; overflow:hidden; }
.progress-fill-sm { height:100%; border-radius:2px; }
.fill-blue  { background:#3b82f6; }
.fill-green { background:#22c55e; }
.prog-num   { font-size:10px; color:#64748b; min-width:24px; }

.print-header { display:none; }

.spin { display:inline-block; animation:spin 0.8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

@media print {
  .print-header  { display:block; margin-bottom:12px; }
  .print-header h2 { font-size:15px; }
  .filters-card, .header-actions, .quick-stats { display:none !important; }
  .table-card { box-shadow:none; }
  .page-container { padding:0; }
}
</style>
