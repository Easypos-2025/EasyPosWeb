<template>
  <div class="page-container">

    <!-- ENCABEZADO -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Gestión de Planes por Empresa</h1>
        <p class="page-subtitle">Asigna, cambia o consulta el plan activo de cada asociado.</p>
      </div>
    </div>

    <!-- RESUMEN POR PLAN -->
    <div class="plan-summary">
      <div
        v-for="(group, planName) in groupedByPlan"
        :key="planName"
        class="plan-chip"
        :class="{ 'plan-chip--active': filterPlan === planName }"
        @click="filterPlan = filterPlan === planName ? '' : planName"
      >
        <span class="chip-name">{{ planName }}</span>
        <span class="chip-count">{{ group.length }}</span>
      </div>
      <div class="plan-chip plan-chip--total" @click="filterPlan = ''">
        <span class="chip-name">Todos</span>
        <span class="chip-count">{{ rows.length }}</span>
      </div>
    </div>

    <!-- FILTROS -->
    <div class="filters-row">
      <input v-model="search" class="form-control" placeholder="Buscar empresa..." style="max-width:280px" />
      <select v-model="filterPlan" class="form-select" style="max-width:200px">
        <option value="">Todos los planes</option>
        <option v-for="p in plans" :key="p.id" :value="p.name">{{ p.name }}</option>
      </select>
    </div>

    <!-- TABLA -->
    <div class="table-card">
      <div v-if="loading" class="table-loading">
        <i class="bi bi-arrow-repeat spin"></i> Cargando...
      </div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Empresa</th>
            <th>NIT</th>
            <th class="text-center">Plan actual</th>
            <th class="text-center">Precio/mes</th>
            <th class="text-center">Inicio</th>
            <th class="text-center">Vencimiento</th>
            <th class="text-center">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in filtered" :key="row.company_id">
            <td><strong>{{ row.company_name }}</strong></td>
            <td class="text-muted">{{ row.identification_number }}</td>
            <td class="text-center">
              <span class="plan-badge" :class="badgeClass(row.plan_name)">
                {{ row.plan_name }}
              </span>
            </td>
            <td class="text-center text-muted">
              {{ row.price > 0 ? '$' + row.price.toLocaleString('es-CO') : 'Gratis' }}
            </td>
            <td class="text-center text-muted">{{ fmt(row.start_date) }}</td>
            <td class="text-center">
              <span v-if="row.expiration_date" :class="isExpired(row.expiration_date) ? 'text-danger' : 'text-muted'">
                {{ fmt(row.expiration_date) }}
                <i v-if="isExpired(row.expiration_date)" class="bi bi-exclamation-triangle-fill text-danger ms-1"></i>
              </span>
              <span v-else class="text-muted">Indefinido</span>
            </td>
            <td class="text-center">
              <button class="btn btn-warning btn-sm" @click="openChange(row)">
                <i class="bi bi-pencil"></i> Cambiar plan
              </button>
            </td>
          </tr>
          <tr v-if="filtered.length === 0">
            <td colspan="7" class="text-center text-muted py-4">Sin resultados</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- MODAL CAMBIAR PLAN -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-box">
        <div class="modal-header-bar">
          <h2>Cambiar plan — {{ editing.company_name }}</h2>
          <button class="btn-close-x" @click="showModal = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-body-area">

          <div class="current-plan-info">
            <i class="bi bi-award"></i>
            Plan actual: <strong>{{ editing.plan_name }}</strong>
            <span class="text-muted ms-2">
              ({{ editing.expiration_date ? 'Vence: ' + fmt(editing.expiration_date) : 'Indefinido' }})
            </span>
          </div>

          <div class="fg">
            <label>Nuevo plan *</label>
            <select v-model="form.plan_id" class="form-select" data-v="plan">
              <option value="">— Seleccionar —</option>
              <option v-for="p in plans" :key="p.id" :value="p.id">
                {{ p.name }} — {{ p.price > 0 ? '$' + p.price.toLocaleString('es-CO') + '/mes' : 'Gratis' }}
                (máx {{ p.max_users === -1 ? '∞' : p.max_users }} usuarios)
              </option>
            </select>
          </div>

          <div class="fg">
            <label>Fecha de vencimiento <small class="text-muted">(dejar vacío = indefinido / plan Free)</small></label>
            <input v-model="form.expiration_date" type="date" class="form-control" />
          </div>

        </div>
        <div class="modal-footer-bar">
          <button class="btn btn-secondary" @click="showModal = false">Cancelar</button>
          <button class="btn btn-primary" @click="savePlan" :disabled="saving">
            {{ saving ? 'Guardando...' : 'Guardar cambio' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

const loading = ref(true)
const saving  = ref(false)
const rows    = ref([])
const plans   = ref([])
const search  = ref("")
const filterPlan = ref("")
const showModal  = ref(false)
const editing    = ref({})
const form       = ref({ plan_id: "", expiration_date: "" })

// Agrupación por plan para el resumen superior
const groupedByPlan = computed(() => {
  return rows.value.reduce((acc, r) => {
    if (!acc[r.plan_name]) acc[r.plan_name] = []
    acc[r.plan_name].push(r)
    return acc
  }, {})
})

const filtered = computed(() =>
  rows.value.filter(r => {
    const matchSearch = !search.value ||
      r.company_name.toLowerCase().includes(search.value.toLowerCase()) ||
      r.identification_number.includes(search.value)
    const matchPlan = !filterPlan.value || r.plan_name === filterPlan.value
    return matchSearch && matchPlan
  })
)

function fmt(iso) {
  if (!iso) return ""
  const [y, m, d] = iso.split("-")
  return `${d}/${m}/${y}`
}

function isExpired(iso) {
  return iso && new Date(iso) < new Date()
}

function badgeClass(name) {
  const map = { Free: "badge-gray", Básico: "badge-blue", Estándar: "badge-green", Premium: "badge-gold" }
  return map[name] || "badge-gray"
}

async function load() {
  loading.value = true
  try {
    const [companiesRes, plansRes] = await Promise.all([
      api.get("/companies/"),
      api.get("/plans/")
    ])
    plans.value = plansRes.data

    // Para cada empresa cargar su plan activo
    const empresas = companiesRes.data
    const planData = await Promise.all(
      empresas.map(c => api.get(`/company-plan/${c.id}`).then(r => ({
        company_id:           c.id,
        company_name:         c.name,
        identification_number: c.identification_number,
        ...r.data
      })).catch(() => ({
        company_id: c.id, company_name: c.name,
        identification_number: c.identification_number,
        plan_name: "Sin plan", price: 0,
        start_date: null, expiration_date: null
      })))
    )
    rows.value = planData
  } catch {
    showToast("Error cargando datos", "error")
  } finally {
    loading.value = false
  }
}

function openChange(row) {
  editing.value = row
  const plan = plans.value.find(p => p.name === row.plan_name)
  form.value = {
    plan_id:         plan?.id || "",
    expiration_date: row.expiration_date?.split("T")[0] || ""
  }
  showModal.value = true
}

async function savePlan() {
  if (!form.value.plan_id) {
    showToast("Selecciona un plan", "warning")
    return
  }
  saving.value = true
  try {
    await api.post(`/company-plan/${editing.value.company_id}`, {
      plan_id:         form.value.plan_id,
      expiration_date: form.value.expiration_date || null
    })
    showToast("Plan actualizado correctamente", "success")
    showModal.value = false
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error guardando", "error")
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page-container  { padding: 24px; max-width: 1200px; }
.page-header     { margin-bottom: 20px; }
.page-title      { font-size: 20px; font-weight: 700; color: #1e293b; margin-bottom: 4px; }
.page-subtitle   { font-size: 13px; color: #64748b; }

/* RESUMEN CHIPS */
.plan-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 18px;
}

.plan-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.plan-chip:hover          { border-color: #3b82f6; background: #eff6ff; }
.plan-chip--active        { background: #3b82f6; border-color: #3b82f6; color: #fff; }
.plan-chip--active .chip-count { background: rgba(255,255,255,0.25); }
.plan-chip--total         { border-style: dashed; }

.chip-name  { font-size: 13px; font-weight: 600; }
.chip-count {
  font-size: 11px; font-weight: 700;
  background: #e2e8f0; color: #475569;
  border-radius: 10px; padding: 1px 8px;
}

/* FILTROS */
.filters-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

/* TABLE */
.table-card  { background:#fff; border-radius:14px; box-shadow:0 1px 6px rgba(0,0,0,0.08); overflow:hidden; }
.table-loading { padding:40px; text-align:center; color:#94a3b8; }
.data-table  { width:100%; border-collapse:collapse; font-size:14px; }
.data-table th { background:#f8fafc; color:#475569; font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:0.4px; padding:12px 16px; border-bottom:1px solid #e2e8f0; }
.data-table td { padding:13px 16px; border-bottom:1px solid #f1f5f9; vertical-align:middle; }
.data-table tr:last-child td { border-bottom:none; }
.data-table tr:hover td { background:#f8fafc; }
.text-center { text-align:center; }
.text-muted  { color:#94a3b8 !important; font-size:13px; }
.text-danger { color:#ef4444 !important; }

/* BADGES */
.plan-badge  { font-size:11px; font-weight:700; padding:3px 10px; border-radius:20px; }
.badge-gray  { background:#f1f5f9; color:#64748b; }
.badge-blue  { background:#dbeafe; color:#1e40af; }
.badge-green { background:#dcfce7; color:#16a34a; }
.badge-gold  { background:#fef9c3; color:#a16207; }

/* MODAL */
.modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.45); display:flex; align-items:center; justify-content:center; z-index:1000; }
.modal-box     { background:#fff; border-radius:16px; width:520px; max-width:95vw; box-shadow:0 20px 60px rgba(0,0,0,0.2); }
.modal-header-bar { display:flex; align-items:center; justify-content:space-between; padding:18px 24px 14px; border-bottom:1px solid #f1f5f9; }
.modal-header-bar h2 { font-size:16px; font-weight:700; color:#1e293b; margin:0; }
.modal-body-area { padding:20px 24px; display:flex; flex-direction:column; gap:14px; }
.modal-footer-bar { padding:14px 24px 18px; display:flex; justify-content:flex-end; gap:10px; border-top:1px solid #f1f5f9; }

.current-plan-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #f0fdf4;
  border-radius: 10px;
  font-size: 14px;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.fg { display:flex; flex-direction:column; gap:5px; }
.fg label { font-size:13px; font-weight:600; color:#374151; }

.btn-close-x { background:none; border:none; font-size:18px; cursor:pointer; color:#94a3b8; }
.btn-close-x:hover { color:#1e293b; }

.spin { animation: spin 0.8s linear infinite; display:inline-block; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
</style>
