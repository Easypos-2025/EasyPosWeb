<template>
  <div class="monitor-wrap">

    <!-- ══ PANEL IZQUIERDO — Lista de empresas ══ -->
    <aside class="monitor-left">
      <div class="left-header">
        <span class="left-title">Empresas</span>
        <span class="left-count">{{ filteredCompanies.length }}</span>
      </div>

      <!-- Filtro por perfil -->
      <div class="left-filters">
        <select v-model="profileFilter" class="profile-select">
          <option value="">Todos los perfiles</option>
          <option v-for="p in profiles" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
        <input
          v-model="companySearch"
          class="company-search"
          placeholder="Buscar empresa..."
          autocomplete="off"
        />
      </div>

      <!-- Lista -->
      <div class="company-list">
        <button
          v-for="c in filteredCompanies"
          :key="c.id"
          :class="['company-item', selectedCompany?.id === c.id && 'active']"
          @click="selectCompany(c)"
        >
          <span class="company-item-name">{{ c.name }}</span>
          <span class="company-item-profile">{{ c.business_profile_name }}</span>
        </button>
        <div v-if="!filteredCompanies.length" class="list-empty">Sin resultados</div>
      </div>
    </aside>

    <!-- ══ PANEL DERECHO — Detalle de empresa ══ -->
    <main class="monitor-right">

      <!-- Placeholder -->
      <div v-if="!selectedCompany" class="right-placeholder">
        <i class="bi bi-arrow-left-circle placeholder-icon"></i>
        <p>Selecciona una empresa para ver su facturación</p>
      </div>

      <template v-else>
        <div class="right-header">
          <div>
            <h2 class="right-title">{{ selectedCompany.name }}</h2>
            <span class="right-profile">{{ selectedCompany.business_profile_name }}</span>
          </div>
          <!-- Filtro fecha compartido -->
          <div class="billing-toolbar">
            <div class="mode-toggle">
              <button :class="['btn-mode', billMode === 'day' && 'active']" @click="setBillMode('day')">Día</button>
              <button :class="['btn-mode', billMode === 'month' && 'active']" @click="setBillMode('month')">Mes</button>
            </div>
            <CustomDatePicker v-model="billDate" variant="dark" @update:modelValue="loadBilling" />
            <span v-if="billLoading" class="bill-spinner">⏳</span>
          </div>
        </div>

        <!-- Cards facturación -->
        <div class="bill-cards">

          <button class="bill-card bill-card--fact" @click="openModal('factura')" :disabled="billLoading">
            <div class="bill-card-icon"><i class="bi bi-receipt-cutoff"></i></div>
            <div class="bill-card-body">
              <div class="bill-card-label">Facturas</div>
              <div class="bill-card-count">{{ billing.facturas.count }}</div>
              <div class="bill-card-total">{{ fmt(billing.facturas.total) }}</div>
            </div>
            <div class="bill-card-cta">Ver detalle →</div>
          </button>

          <button class="bill-card bill-card--rec" @click="openModal('recibo')" :disabled="billLoading">
            <div class="bill-card-icon"><i class="bi bi-file-earmark-text"></i></div>
            <div class="bill-card-body">
              <div class="bill-card-label">Recibos</div>
              <div class="bill-card-count">{{ billing.recibos.count }}</div>
              <div class="bill-card-total">{{ fmt(billing.recibos.total) }}</div>
            </div>
            <div class="bill-card-cta">Ver detalle →</div>
          </button>

        </div>
      </template>
    </main>

    <!-- ══ MODAL DETALLE VENTAS ══ -->
    <Teleport to="body">
      <div v-if="modal.show" class="modal-overlay" @click.self="modal.show = false">
        <div class="modal-box">
          <div class="modal-header">
            <span class="modal-title">
              {{ modal.tipo === 'factura' ? 'Facturas' : 'Recibos' }} — {{ selectedCompany?.name }}
            </span>
            <button class="modal-close" @click="modal.show = false">✕</button>
          </div>

          <div class="modal-toolbar">
            <span class="modal-subtitle">
              {{ billMode === 'day' ? fmtDateDisplay(billDate) : billDate.slice(0,7) }}
              · {{ modal.rows.length }} registros
              · Total: {{ fmt(modal.rows.reduce((s,r) => s + Number(r.valor), 0)) }}
            </span>
          </div>

          <div v-if="modal.loading" class="modal-loading">Cargando...</div>
          <div v-else-if="!modal.rows.length" class="modal-empty">Sin registros</div>
          <div v-else class="modal-table-wrap">
            <table class="modal-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Fecha</th>
                  <th>Hora</th>
                  <th>Turno</th>
                  <th class="text-right">Valor</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in modal.rows" :key="row.numero">
                  <td>{{ row.numero }}</td>
                  <td>{{ fmtDateDisplay(row.date) }}</td>
                  <td>{{ row.hora }}</td>
                  <td>{{ row.turno }}</td>
                  <td class="text-right">{{ fmt(row.valor) }}</td>
                  <td>
                    <button class="btn-detail" @click="openDetailModal(row)" title="Ver items">
                      <i class="bi bi-eye"></i>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ══ MODAL ITEMS DE UNA VENTA ══ -->
    <Teleport to="body">
      <div v-if="detailModal.show" class="modal-overlay" @click.self="detailModal.show = false">
        <div class="modal-box modal-box--sm">
          <div class="modal-header">
            <span class="modal-title">
              {{ detailModal.tipo === 'factura' ? 'Factura' : 'Recibo' }} #{{ detailModal.numero }}
            </span>
            <button class="modal-close" @click="detailModal.show = false">✕</button>
          </div>
          <div v-if="detailModal.loading" class="modal-loading">Cargando...</div>
          <div v-else-if="detailModal.items.length" class="modal-table-wrap">
            <table class="modal-table">
              <thead>
                <tr><th>Producto</th><th class="text-right">Cant.</th><th class="text-right">Subtotal</th></tr>
              </thead>
              <tbody>
                <tr v-for="it in detailModal.items" :key="it.item">
                  <td>{{ it.plato }}</td>
                  <td class="text-right">{{ it.quantity }}</td>
                  <td class="text-right">{{ fmt(it.subtotal) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="modal-empty">Sin items</div>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import CustomDatePicker from "@/components/common/CustomDatePicker.vue"
import api from "@/services/apis"

// ── Empresas ───────────────────────────────────────────────────────────────
const allCompanies  = ref([])
const profiles      = ref([])
const profileFilter = ref("")
const companySearch = ref("")
const selectedCompany = ref(null)

const filteredCompanies = computed(() => {
  let list = allCompanies.value
  if (profileFilter.value) list = list.filter(c => c.business_profile_id === profileFilter.value)
  const q = companySearch.value.toLowerCase().trim()
  if (q) list = list.filter(c => c.name.toLowerCase().includes(q))
  return list
})

async function loadCompanies() {
  try {
    const res = await api.get("/companies/")
    allCompanies.value = (res.data.data || res.data || [])
      .filter(c => c.state)
      .sort((a, b) => a.name.localeCompare(b.name, "es"))
    // Perfiles únicos
    const pMap = {}
    allCompanies.value.forEach(c => {
      if (c.business_profile_id && c.business_profile_name)
        pMap[c.business_profile_id] = c.business_profile_name
    })
    profiles.value = Object.entries(pMap)
      .map(([id, name]) => ({ id: Number(id), name }))
      .sort((a, b) => a.name.localeCompare(b.name, "es"))
  } catch {}
}

function selectCompany(c) {
  selectedCompany.value = c
  billing.value = { facturas: { count: 0, total: 0 }, recibos: { count: 0, total: 0 } }
  loadBilling()
}

// ── Facturación ─────────────────────────────────────────────────────────────
const billMode    = ref("day")
const billDate    = ref(new Date().toLocaleDateString("en-CA", { timeZone: "America/Bogota" }))
const billLoading = ref(false)
const billing     = ref({ facturas: { count: 0, total: 0 }, recibos: { count: 0, total: 0 } })

function setBillMode(m) {
  billMode.value = m
  if (selectedCompany.value) loadBilling()
}

async function loadBilling() {
  if (!selectedCompany.value) return
  billLoading.value = true
  try {
    const res = await api.get("/dashboard/sysadmin/company-billing", {
      params: {
        company_id: selectedCompany.value.id,
        date: billDate.value,
        mode: billMode.value,
      }
    })
    billing.value = res.data
  } catch {}
  billLoading.value = false
}

// ── Modal lista ventas ───────────────────────────────────────────────────────
const modal = ref({ show: false, tipo: "factura", loading: false, rows: [] })

async function openModal(tipo) {
  modal.value = { show: true, tipo, loading: true, rows: [] }
  try {
    const desde = billMode.value === "month"
      ? billDate.value.slice(0, 7) + "-01"
      : billDate.value
    const hasta = billMode.value === "month"
      ? lastDayOfMonth(billDate.value)
      : billDate.value
    const res = await api.get("/api/pos-consultas/ventas", {
      params: {
        company_id: selectedCompany.value.id,
        tipo,
        desde,
        hasta,
      }
    })
    modal.value.rows = res.data
  } catch {}
  modal.value.loading = false
}

// ── Modal detalle items ──────────────────────────────────────────────────────
const detailModal = ref({ show: false, tipo: "", numero: "", loading: false, items: [] })

async function openDetailModal(row) {
  detailModal.value = { show: true, tipo: modal.value.tipo, numero: row.numero, loading: true, items: [] }
  try {
    const res = await api.get(`/api/pos-consultas/venta-detalle/${modal.value.tipo}/${row.numero}`, {
      params: { company_id: selectedCompany.value.id, fecha: row.date }
    })
    detailModal.value.items = res.data.items || []
  } catch {}
  detailModal.value.loading = false
}

// ── Utilidades ───────────────────────────────────────────────────────────────
function fmt(v) {
  return new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(v || 0)
}

function fmtDateDisplay(iso) {
  if (!iso) return "—"
  const [y, m, d] = iso.slice(0, 10).split("-")
  return `${d}/${m}/${y}`
}

function lastDayOfMonth(iso) {
  const [y, m] = iso.slice(0, 7).split("-")
  return new Date(Number(y), Number(m), 0).toISOString().slice(0, 10)
}

onMounted(loadCompanies)
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════
   LAYOUT
═══════════════════════════════════════════════════════ */
.monitor-wrap {
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
.monitor-left {
  width: 280px;
  min-width: 220px;
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
  font-size: 15px;
  color: #1e293b;
}

.left-count {
  background: #e2e8f0;
  border-radius: 20px;
  padding: 2px 10px;
  font-size: 12px;
  color: #475569;
  font-weight: 600;
}

.left-filters {
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-bottom: 1px solid #f1f5f9;
}

.profile-select,
.company-search {
  width: 100%;
  padding: 7px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 13px;
  background: #f8fafc;
  color: #334155;
  outline: none;
}
.profile-select:focus,
.company-search:focus { border-color: #2563eb; }

.company-list {
  flex: 1;
  overflow-y: auto;
}

.company-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  width: 100%;
  padding: 10px 16px;
  background: none;
  border: none;
  border-bottom: 1px solid #f1f5f9;
  cursor: pointer;
  text-align: left;
  transition: background 0.1s;
}
.company-item:hover { background: #f8fafc; }
.company-item.active { background: #eff6ff; border-left: 3px solid #2563eb; }

.company-item-name {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.3;
}
.company-item-profile {
  font-size: 11px;
  color: #94a3b8;
}

.list-empty {
  padding: 20px;
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
}

/* ═══════════════════════════════════════════════════════
   PANEL DERECHO
═══════════════════════════════════════════════════════ */
.monitor-right {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
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
.placeholder-icon { font-size: 48px; }
.right-placeholder p { font-size: 15px; }

.right-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 24px;
}

.right-title {
  font-size: 20px;
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

/* Toolbar facturación */
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
  transition: background 0.15s, color 0.15s;
}
.btn-mode.active { background: #2563eb; color: #fff; }
.btn-mode:hover:not(.active) { background: #f1f5f9; }

.bill-spinner { font-size: 18px; }

/* Cards */
.bill-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.bill-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 28px 20px 20px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  background: #fff;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s, transform 0.1s;
  text-align: center;
}
.bill-card:hover:not(:disabled) {
  border-color: #2563eb;
  box-shadow: 0 4px 16px rgba(37,99,235,.12);
  transform: translateY(-2px);
}
.bill-card:disabled { opacity: 0.6; cursor: default; }

.bill-card--fact { border-top: 4px solid #2563eb; }
.bill-card--rec  { border-top: 4px solid #0891b2; }

.bill-card-icon { font-size: 32px; color: #94a3b8; }
.bill-card--fact .bill-card-icon { color: #2563eb; }
.bill-card--rec  .bill-card-icon { color: #0891b2; }

.bill-card-label {
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: .5px;
}
.bill-card-count {
  font-size: 36px;
  font-weight: 800;
  color: #1e293b;
  line-height: 1;
}
.bill-card-total {
  font-size: 16px;
  font-weight: 600;
  color: #475569;
}
.bill-card-cta {
  font-size: 12px;
  color: #2563eb;
  margin-top: 4px;
}

/* ═══════════════════════════════════════════════════════
   MODALES
═══════════════════════════════════════════════════════ */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-box {
  background: #fff;
  border-radius: 12px;
  width: 100%;
  max-width: 780px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,.2);
}
.modal-box--sm { max-width: 500px; }

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
}
.modal-title {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}
.modal-close {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #64748b;
  padding: 4px 8px;
  border-radius: 4px;
  width: auto;
}
.modal-close:hover { background: #f1f5f9; }

.modal-toolbar {
  padding: 10px 20px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}
.modal-subtitle { font-size: 13px; color: #64748b; }

.modal-loading,
.modal-empty {
  padding: 40px;
  text-align: center;
  color: #94a3b8;
  font-size: 14px;
}

.modal-table-wrap {
  overflow-y: auto;
  flex: 1;
}

.modal-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.modal-table thead tr {
  background: #f1f5f9;
  position: sticky;
  top: 0;
}
.modal-table th {
  padding: 10px 14px;
  text-align: left;
  font-weight: 600;
  color: #475569;
  font-size: 12px;
  border-bottom: 1px solid #e2e8f0;
}
.modal-table td {
  padding: 9px 14px;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
}
.modal-table tbody tr:hover { background: #f8fafc; }
.text-right { text-align: right; }

.btn-detail {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 5px;
  padding: 4px 9px;
  cursor: pointer;
  color: #475569;
  width: auto;
}
.btn-detail:hover { background: #e2e8f0; }

/* ═══════════════════════════════════════════════════════
   RESPONSIVE
═══════════════════════════════════════════════════════ */
@media (max-width: 768px) {
  .monitor-wrap {
    flex-direction: column;
    height: auto;
    min-height: unset;
  }
  .monitor-left {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #e2e8f0;
    max-height: 240px;
  }
  .monitor-right { padding: 16px; }
  .right-header { flex-direction: column; }
  .bill-cards { grid-template-columns: 1fr; }
}

@media (max-width: 576px) {
  .monitor-left { max-height: 200px; }
  .bill-card { padding: 20px 14px 16px; }
  .bill-card-count { font-size: 28px; }
  .modal-box { max-height: 95vh; border-radius: 8px; }
}
</style>
