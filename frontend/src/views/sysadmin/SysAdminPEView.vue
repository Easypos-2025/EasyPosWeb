<template>
  <div class="pe-wrap">

    <!-- ── Header ── -->
    <div class="pe-header">
      <div>
        <h2 class="pe-title"><i class="bi bi-lightning-charge-fill"></i> Admin POS Electrónico</h2>
        <p class="pe-subtitle">Activa o desactiva el módulo de POS Electrónico por empresa</p>
      </div>
      <div class="pe-kpis">
        <div class="pe-kpi">
          <span class="pe-kpi-val">{{ totalCompanies }}</span>
          <span class="pe-kpi-label">Empresas</span>
        </div>
        <div class="pe-kpi pe-kpi--active">
          <span class="pe-kpi-val">{{ peActive }}</span>
          <span class="pe-kpi-label">Con PE activo</span>
        </div>
      </div>
    </div>

    <!-- ── Filtros ── -->
    <div class="pe-toolbar">
      <input
        v-model="search"
        class="pe-search"
        placeholder="Buscar empresa..."
        autocomplete="off"
        @input="load"
      />
      <div class="pe-toggle-filter">
        <button :class="['btn-filter', peOnly === false && 'active']" @click="setPeOnly(false)">
          Todas
        </button>
        <button :class="['btn-filter', peOnly === true && 'active']" @click="setPeOnly(true)">
          Solo PE activo
        </button>
      </div>
      <span v-if="loading" class="pe-loading">Cargando...</span>
    </div>

    <!-- ── Tabla ── -->
    <div class="pe-table-wrap">
      <table class="pe-table" v-if="companies.length">
        <thead>
          <tr>
            <th>Empresa</th>
            <th>Perfil</th>
            <th class="text-center">POS Electrónico</th>
            <th>Token / Clave</th>
            <th class="text-center">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in companies" :key="c.id_company">
            <td>
              <span class="company-name">{{ c.name }}</span>
            </td>
            <td class="text-muted">{{ c.profile_name || '—' }}</td>
            <td class="text-center">
              <button
                :class="['toggle-pe', c.has_pos_electronico ? 'toggle-pe--on' : 'toggle-pe--off']"
                :disabled="saving === c.id_company"
                @click="togglePE(c)"
                :title="c.has_pos_electronico ? 'Desactivar PE' : 'Activar PE'"
              >
                <i :class="c.has_pos_electronico ? 'bi bi-toggle-on' : 'bi bi-toggle-off'"></i>
                {{ c.has_pos_electronico ? 'Activo' : 'Inactivo' }}
              </button>
            </td>
            <td>
              <template v-if="c.has_pos_electronico">
                <div class="token-row">
                  <input
                    v-model="c.pos_electronico_token"
                    class="token-input"
                    placeholder="Token / clave de integración..."
                    @blur="saveToken(c)"
                  />
                  <button class="btn-save-token" @click="saveToken(c)" title="Guardar token">
                    <i class="bi bi-floppy"></i>
                  </button>
                </div>
              </template>
              <span v-else class="text-muted text-sm">—</span>
            </td>
            <td class="text-center">
              <span v-if="saving === c.id_company" class="saving-indicator">
                <i class="bi bi-arrow-repeat spin"></i>
              </span>
              <span v-else-if="saved === c.id_company" class="saved-indicator">
                <i class="bi bi-check-circle-fill"></i>
              </span>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else-if="!loading" class="pe-empty">
        <i class="bi bi-search" style="font-size:32px; color:#cbd5e1"></i>
        <p>Sin empresas que coincidan con el filtro</p>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import api from "@/services/apis"

const companies = ref([])
const loading   = ref(false)
const saving    = ref(null)
const saved     = ref(null)
const search    = ref("")
const peOnly    = ref(false)

const totalCompanies = computed(() => companies.value.length)
const peActive       = computed(() => companies.value.filter(c => c.has_pos_electronico).length)

let _searchTimer = null
function setPeOnly(val) {
  peOnly.value = val
  load()
}

async function load() {
  clearTimeout(_searchTimer)
  _searchTimer = setTimeout(async () => {
    loading.value = true
    try {
      const res = await api.get("/company-configs/", {
        params: {
          pe_only: peOnly.value,
          search: search.value || undefined,
        }
      })
      companies.value = res.data
    } catch {}
    loading.value = false
  }, 300)
}

async function togglePE(c) {
  saving.value = c.id_company
  const newVal = c.has_pos_electronico ? 0 : 1
  try {
    await api.put(`/company-configs/${c.id_company}`, {
      has_pos_electronico: newVal,
    })
    c.has_pos_electronico = newVal
    flashSaved(c.id_company)
  } catch {}
  saving.value = null
}

async function saveToken(c) {
  if (!c.has_pos_electronico) return
  saving.value = c.id_company
  try {
    await api.put(`/company-configs/${c.id_company}`, {
      pos_electronico_token: c.pos_electronico_token || null,
    })
    flashSaved(c.id_company)
  } catch {}
  saving.value = null
}

function flashSaved(id) {
  saved.value = id
  setTimeout(() => { if (saved.value === id) saved.value = null }, 2000)
}

onMounted(load)
</script>

<style scoped>
.pe-wrap {
  max-width: 1100px;
  margin: 0 auto;
  padding: 8px 0 40px;
}

/* ── Header ── */
.pe-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 20px;
}

.pe-title {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.pe-title i { color: #f59e0b; }

.pe-subtitle { font-size: 13px; color: #64748b; margin: 0; }

.pe-kpis {
  display: flex;
  gap: 12px;
}

.pe-kpi {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px 20px;
  min-width: 90px;
}

.pe-kpi--active {
  background: #fffbeb;
  border-color: #fcd34d;
}

.pe-kpi-val {
  font-size: 24px;
  font-weight: 800;
  color: #1e293b;
  line-height: 1;
}

.pe-kpi--active .pe-kpi-val { color: #d97706; }

.pe-kpi-label {
  font-size: 11px;
  color: #94a3b8;
  margin-top: 4px;
  text-transform: uppercase;
  letter-spacing: .4px;
}

/* ── Toolbar ── */
.pe-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.pe-search {
  flex: 1;
  min-width: 200px;
  padding: 9px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  color: #334155;
  background: #fff;
  outline: none;
}
.pe-search:focus { border-color: #2563eb; }

.pe-toggle-filter {
  display: flex;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}

.btn-filter {
  padding: 8px 16px;
  background: #fff;
  border: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
  transition: background 0.15s;
}
.btn-filter.active { background: #2563eb; color: #fff; }
.btn-filter:hover:not(.active) { background: #f1f5f9; }

.pe-loading { font-size: 13px; color: #94a3b8; }

/* ── Tabla ── */
.pe-table-wrap {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
}

.pe-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.pe-table thead tr {
  background: #f8fafc;
  border-bottom: 2px solid #e2e8f0;
}

.pe-table th {
  padding: 12px 16px;
  text-align: left;
  font-size: 12px;
  font-weight: 700;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: .4px;
}

.pe-table td {
  padding: 12px 16px;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
  vertical-align: middle;
}

.pe-table tbody tr:hover { background: #f8fafc; }
.pe-table tbody tr:last-child td { border-bottom: none; }

.company-name { font-weight: 600; }
.text-center { text-align: center; }
.text-muted { color: #94a3b8; }
.text-sm { font-size: 12px; }

/* Toggle PE */
.toggle-pe {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 20px;
  border: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.15s;
}
.toggle-pe--on {
  background: #dcfce7;
  color: #16a34a;
}
.toggle-pe--on:hover:not(:disabled) { background: #bbf7d0; }
.toggle-pe--off {
  background: #f1f5f9;
  color: #94a3b8;
}
.toggle-pe--off:hover:not(:disabled) { background: #e2e8f0; color: #475569; }
.toggle-pe:disabled { opacity: 0.6; cursor: default; }
.toggle-pe i { font-size: 16px; }

/* Token */
.token-row {
  display: flex;
  gap: 6px;
  align-items: center;
}

.token-input {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 13px;
  background: #f8fafc;
  color: #334155;
  outline: none;
  font-family: monospace;
}
.token-input:focus { border-color: #2563eb; background: #fff; }

.btn-save-token {
  padding: 6px 10px;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  width: auto;
}
.btn-save-token:hover { background: #1d4ed8; }

/* Indicadores */
.saving-indicator { color: #94a3b8; font-size: 18px; }
.saved-indicator   { color: #16a34a; font-size: 18px; }

.spin {
  display: inline-block;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Empty */
.pe-empty {
  padding: 60px;
  text-align: center;
  color: #94a3b8;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .pe-header { flex-direction: column; }
  .pe-kpis { width: 100%; }
  .pe-kpi { flex: 1; }
  .pe-table th:nth-child(2),
  .pe-table td:nth-child(2) { display: none; }
}

@media (max-width: 576px) {
  .pe-toolbar { flex-direction: column; align-items: stretch; }
  .pe-search { min-width: unset; }
  .token-input { font-size: 12px; }
  .pe-table th:nth-child(5),
  .pe-table td:nth-child(5) { display: none; }
}
</style>
