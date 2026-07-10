<template>
  <div class="pe-wrap">

    <!-- ══ PANEL IZQUIERDO ══ -->
    <aside class="pe-left">
      <div class="left-header">
        <span class="left-title">
          <i class="bi bi-lightning-charge-fill" style="color:#f59e0b"></i>
          POS Electrónico
        </span>
        <span class="left-badge">{{ companies.length }}</span>
      </div>

      <!-- Filtros -->
      <div class="left-filters">
        <select v-model="profileFilter" class="pe-select">
          <option value="">Todos los perfiles</option>
          <option v-for="p in profiles" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
        <input
          v-model="companySearch"
          class="pe-search"
          placeholder="Buscar empresa..."
          autocomplete="off"
        />
      </div>

      <!-- Lista -->
      <div class="company-list">
        <button
          v-for="c in filteredCompanies"
          :key="c.id_company"
          :class="['company-item', selectedCompany?.id_company === c.id_company && 'active']"
          @click="selectCompany(c)"
        >
          <span class="company-item-name">{{ c.name }}</span>
          <button
            class="pe-mini-toggle"
            :class="c.has_pos_electronico ? 'pmt--on' : 'pmt--off'"
            :disabled="toggling === c.id_company"
            @click.stop="togglePE(c)"
            :title="c.has_pos_electronico ? 'Desactivar PE' : 'Activar PE'"
          >
            <i :class="c.has_pos_electronico ? 'bi bi-lightning-charge-fill' : 'bi bi-lightning-charge'"></i>
          </button>
        </button>
        <div v-if="!filteredCompanies.length" class="list-empty">Sin resultados</div>
      </div>
    </aside>

    <!-- ══ PANEL DERECHO ══ -->
    <main class="pe-right">

      <!-- Placeholder -->
      <div v-if="!selectedCompany" class="right-placeholder">
        <i class="bi bi-lightning-charge placeholder-icon"></i>
        <p>Selecciona una empresa para ver sus facturas electrónicas</p>
      </div>

      <template v-else>
        <div class="right-header">
          <div>
            <h2 class="right-title">{{ selectedCompany.name }}</h2>
            <span class="right-profile">{{ selectedCompany.business_profile_name }}</span>
          </div>
          <div class="billing-toolbar">
            <div class="mode-toggle">
              <button :class="['btn-mode', billMode === 'day' && 'active']" @click="setBillMode('day')">Día</button>
              <button :class="['btn-mode', billMode === 'month' && 'active']" @click="setBillMode('month')">Mes</button>
            </div>
            <CustomDatePicker v-model="billDate" variant="dark" @update:modelValue="loadFacturas" />
            <span v-if="billLoading" class="bill-spinner">⏳</span>
          </div>
        </div>

        <!-- Tabs -->
        <div class="pe-tabs">
            <button :class="['pe-tab', activeTab === 0 && 'pe-tab--active']" @click="setTab(0)">
              <i class="bi bi-clock-history"></i>
              Pendientes DIAN
              <span class="tab-badge tab-badge--pend">{{ rows0.length }}</span>
            </button>
            <button :class="['pe-tab', activeTab === 1 && 'pe-tab--active']" @click="setTab(1)">
              <i class="bi bi-check-circle-fill"></i>
              Enviadas DIAN
              <span class="tab-badge tab-badge--ok">{{ rows1.length }}</span>
            </button>
          </div>

          <!-- Tabla Pendientes (FEExitosa=0) -->
          <div v-if="activeTab === 0" class="pe-table-wrap">
            <div v-if="billLoading" class="table-loading">Cargando...</div>
            <div v-else-if="!rows0.length" class="table-empty">
              <i class="bi bi-inbox" style="font-size:28px;color:#cbd5e1"></i>
              <p>Sin facturas pendientes para este período</p>
            </div>
            <table v-else class="pe-table">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Prefijo</th>
                  <th>Nro. Folio</th>
                  <th class="text-right">Valor</th>
                  <th>Cuenta</th>
                  <th>Cliente</th>
                  <th class="text-center">Acciones</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in rows0" :key="r.nro_folio + r.prefijo">
                  <td>{{ fmtDate(r.fecha) }}</td>
                  <td><span class="prefix-chip">{{ r.prefijo }}</span></td>
                  <td class="font-mono">{{ r.nro_folio }}</td>
                  <td class="text-right font-bold">{{ fmt(r.valor) }}</td>
                  <td class="text-muted">{{ r.cuenta }}</td>
                  <td class="td-cliente">{{ r.cliente }}</td>
                  <td class="text-center">
                    <button class="btn-dian btn-dian--revalidar" title="Reenviar a DIAN">
                      <i class="bi bi-arrow-repeat"></i> Revalidar
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Tabla Enviadas (FEExitosa=1) -->
          <div v-if="activeTab === 1" class="pe-table-wrap">
            <div v-if="billLoading" class="table-loading">Cargando...</div>
            <div v-else-if="!rows1.length" class="table-empty">
              <i class="bi bi-inbox" style="font-size:28px;color:#cbd5e1"></i>
              <p>Sin facturas enviadas para este período</p>
            </div>
            <table v-else class="pe-table">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Prefijo</th>
                  <th>Nro. Folio</th>
                  <th class="text-right">Valor</th>
                  <th>Cuenta</th>
                  <th>Cliente</th>
                  <th class="text-center">Acciones</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in rows1" :key="r.nro_folio + r.prefijo">
                  <td>{{ fmtDate(r.fecha) }}</td>
                  <td><span class="prefix-chip prefix-chip--ok">{{ r.prefijo }}</span></td>
                  <td class="font-mono">{{ r.nro_folio }}</td>
                  <td class="text-right font-bold">{{ fmt(r.valor) }}</td>
                  <td class="text-muted">{{ r.cuenta }}</td>
                  <td class="td-cliente">{{ r.cliente }}</td>
                  <td class="text-center">
                    <div class="action-btns">
                      <button class="btn-dian btn-dian--reimp" title="Re-Imprimir">
                        <i class="bi bi-printer"></i> Re-Imprime
                      </button>
                      <button class="btn-dian btn-dian--dian" title="Ver en DIAN">
                        <i class="bi bi-globe2"></i> Ver Dian
                      </button>
                      <button class="btn-dian btn-dian--mail" title="Enviar por email">
                        <i class="bi bi-envelope"></i> Mail
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
      </template>
    </main>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import CustomDatePicker from "@/components/common/CustomDatePicker.vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

// ── Empresas PE ────────────────────────────────────────────────────────────
const allCompanies  = ref([])
const profiles      = ref([])
const profileFilter = ref("")
const companySearch = ref("")
const selectedCompany = ref(null)
const toggling      = ref(null)

const companies = computed(() => {
  return allCompanies.value.filter(c => c.has_pos_electronico)
})

const filteredCompanies = computed(() => {
  let list = companies.value
  if (profileFilter.value) list = list.filter(c => c.business_profile_id == profileFilter.value)
  const q = companySearch.value.toLowerCase().trim()
  if (q) list = list.filter(c => c.name.toLowerCase().includes(q))
  return list
})

async function loadCompanies() {
  try {
    const res = await api.get("/company-configs/", { params: { pe_only: false } })
    allCompanies.value = (res.data || [])
      .sort((a, b) => a.name.localeCompare(b.name, "es"))
    // Perfiles únicos
    const pMap = {}
    allCompanies.value.forEach(c => {
      if (c.business_profile_id && c.profile_name)
        pMap[c.business_profile_id] = c.profile_name
    })
    profiles.value = Object.entries(pMap)
      .map(([id, name]) => ({ id: Number(id), name }))
      .sort((a, b) => a.name.localeCompare(b.name, "es"))
  } catch {}
}

async function togglePE(c) {
  toggling.value = c.id_company
  const newVal = c.has_pos_electronico ? 0 : 1
  try {
    await api.put(`/company-configs/${c.id_company}`, { has_pos_electronico: newVal })
    c.has_pos_electronico = newVal
    if (!newVal && selectedCompany.value?.id_company === c.id_company) {
      selectedCompany.value = null
    }
  } catch {
    showToast("Error actualizando PE", "error")
  }
  toggling.value = null
}

function selectCompany(c) {
  selectedCompany.value = c
  rows0.value = []
  rows1.value = []
  loadFacturas()
}

// ── Facturas PE ────────────────────────────────────────────────────────────
const billMode    = ref("day")
const billDate    = ref(new Date().toLocaleDateString("en-CA", { timeZone: "America/Bogota" }))
const billLoading = ref(false)
const activeTab   = ref(0)
const rows0       = ref([])
const rows1       = ref([])

function setBillMode(m) {
  billMode.value = m
  if (selectedCompany.value) loadFacturas()
}

function setTab(t) {
  activeTab.value = t
}

async function loadFacturas() {
  if (!selectedCompany.value) return
  billLoading.value = true
  try {
    const [r0, r1] = await Promise.all([
      api.get(`/company-configs/${selectedCompany.value.id_company}/pe-facturas`, {
        params: { date: billDate.value, mode: billMode.value, fe: 0 }
      }),
      api.get(`/company-configs/${selectedCompany.value.id_company}/pe-facturas`, {
        params: { date: billDate.value, mode: billMode.value, fe: 1 }
      }),
    ])
    rows0.value = r0.data
    rows1.value = r1.data
  } catch (e) {
    showToast(e?.response?.data?.detail || "Error consultando facturas PE", "error")
  }
  billLoading.value = false
}

// ── Utilidades ─────────────────────────────────────────────────────────────
function fmt(v) {
  return new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(v || 0)
}

function fmtDate(iso) {
  if (!iso) return "—"
  const [y, m, d] = iso.slice(0, 10).split("-")
  return `${d}/${m}/${y}`
}

onMounted(loadCompanies)
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════
   LAYOUT
═══════════════════════════════════════════════════════ */
.pe-wrap {
  display: flex;
  gap: 0;
  height: calc(100vh - 120px);
  min-height: 500px;
  background: #f8fafc;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
}

/* ═══════════════════════════════════════════════════════
   PANEL IZQUIERDO
═══════════════════════════════════════════════════════ */
.pe-left {
  width: 260px;
  min-width: 200px;
  background: #fff;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.left-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px 10px;
  border-bottom: 1px solid #f1f5f9;
}

.left-title {
  font-weight: 700;
  font-size: 14px;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 6px;
}

.left-badge {
  background: #fef3c7;
  border: 1px solid #fcd34d;
  color: #92400e;
  border-radius: 20px;
  padding: 2px 10px;
  font-size: 12px;
  font-weight: 700;
}

.left-filters {
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-bottom: 1px solid #f1f5f9;
}

.pe-select,
.pe-search {
  width: 100%;
  padding: 7px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 13px;
  background: #f8fafc;
  color: #334155;
  outline: none;
}
.pe-select:focus,
.pe-search:focus { border-color: #f59e0b; }

.company-list {
  flex: 1;
  overflow-y: auto;
}

.company-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  background: none;
  border: none;
  border-bottom: 1px solid #f1f5f9;
  cursor: pointer;
  text-align: left;
  transition: background 0.1s;
}
.company-item:hover { background: #fffbeb; }
.company-item.active { background: #fef3c7; border-left: 3px solid #f59e0b; }

.company-item-name {
  flex: 1;
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.3;
  text-align: left;
}

.pe-mini-toggle {
  flex-shrink: 0;
  border: none;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.15s;
}
.pmt--on  { background: #dcfce7; color: #16a34a; }
.pmt--off { background: #f1f5f9; color: #94a3b8; }
.pmt--on:hover:not(:disabled)  { background: #bbf7d0; }
.pmt--off:hover:not(:disabled) { background: #e2e8f0; color: #475569; }
.pe-mini-toggle:disabled { opacity: 0.5; cursor: default; }

.list-empty {
  padding: 20px;
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
}

/* ═══════════════════════════════════════════════════════
   PANEL DERECHO
═══════════════════════════════════════════════════════ */
.pe-right {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.right-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #94a3b8;
  gap: 12px;
}
.placeholder-icon { font-size: 48px; color: #fcd34d; }
.right-placeholder p { font-size: 15px; }

.right-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 20px 24px 16px;
  border-bottom: 1px solid #e2e8f0;
  background: #fff;
}

.right-title {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 4px;
}
.right-profile {
  font-size: 12px;
  color: #64748b;
  background: #f1f5f9;
  padding: 2px 10px;
  border-radius: 20px;
}

.billing-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.mode-toggle {
  display: flex;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  overflow: hidden;
}
.btn-mode {
  padding: 7px 16px;
  background: #fff;
  border: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
  transition: background 0.15s;
}
.btn-mode.active { background: #f59e0b; color: #fff; }
.btn-mode:hover:not(.active) { background: #f1f5f9; }

.bill-spinner { font-size: 18px; }

/* Sin DB externa */
.no-ext-db {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: 12px;
  color: #64748b;
  text-align: center;
  padding: 40px;
}
.no-ext-db p { font-size: 14px; margin: 0; }

/* Tabs */
.pe-tabs {
  display: flex;
  border-bottom: 2px solid #e2e8f0;
  background: #fff;
  padding: 0 24px;
}

.pe-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  color: #64748b;
  transition: all 0.15s;
  margin-bottom: -2px;
}
.pe-tab:hover { color: #f59e0b; }
.pe-tab--active { color: #92400e; border-bottom-color: #f59e0b; }

.tab-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 20px;
}
.tab-badge--pend { background: #fee2e2; color: #dc2626; }
.tab-badge--ok   { background: #dcfce7; color: #16a34a; }

/* Tabla */
.pe-table-wrap {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
}

.table-loading,
.table-empty {
  padding: 48px;
  text-align: center;
  color: #94a3b8;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}

.pe-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}

.pe-table thead tr {
  background: #f8fafc;
  border-bottom: 2px solid #e2e8f0;
}

.pe-table th {
  padding: 10px 12px;
  text-align: left;
  font-size: 11px;
  font-weight: 700;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: .4px;
}

.pe-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
  vertical-align: middle;
}
.pe-table tbody tr:last-child td { border-bottom: none; }
.pe-table tbody tr:hover { background: #fffbeb; }

.text-right  { text-align: right; }
.text-center { text-align: center; }
.text-muted  { color: #94a3b8; font-size: 12px; }
.font-mono   { font-family: monospace; font-size: 13px; }
.font-bold   { font-weight: 600; }

.prefix-chip {
  background: #f1f5f9;
  color: #475569;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  font-family: monospace;
}
.prefix-chip--ok { background: #dcfce7; color: #15803d; }

.td-cliente {
  max-width: 180px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Botones DIAN */
.action-btns {
  display: flex;
  gap: 4px;
  justify-content: center;
  flex-wrap: wrap;
}

.btn-dian {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 11px;
  font-weight: 600;
  transition: all 0.15s;
  white-space: nowrap;
}

.btn-dian--revalidar { background: #fee2e2; color: #dc2626; }
.btn-dian--revalidar:hover { background: #fecaca; }

.btn-dian--reimp { background: #dbeafe; color: #1d4ed8; }
.btn-dian--reimp:hover { background: #bfdbfe; }

.btn-dian--dian { background: #f1f5f9; color: #475569; }
.btn-dian--dian:hover { background: #e2e8f0; }

.btn-dian--mail { background: #d1fae5; color: #065f46; }
.btn-dian--mail:hover { background: #a7f3d0; }

/* ═══════════════════════════════════════════════════════
   RESPONSIVE
═══════════════════════════════════════════════════════ */
@media (max-width: 768px) {
  .pe-wrap {
    flex-direction: column;
    height: auto;
    min-height: unset;
  }
  .pe-left {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #e2e8f0;
    max-height: 220px;
  }
  .right-header { padding: 14px 16px 12px; }
  .pe-tabs { padding: 0 16px; }
  .pe-table-wrap { padding: 12px 16px; }
  .td-cliente { max-width: 100px; }
}

@media (max-width: 576px) {
  .pe-left { max-height: 180px; }
  .pe-tab { padding: 10px 12px; font-size: 13px; }
  .pe-table th:nth-child(5),
  .pe-table td:nth-child(5) { display: none; }
  .action-btns { flex-direction: column; }
  .btn-dian { justify-content: center; }
}
</style>
