<template>
  <div class="ph-view">

    <!-- ENCABEZADO -->
    <div class="ph-header">
      <div>
        <h1 class="ph-title"><i class="bi bi-clock-history me-2"></i>Historial de Pagos</h1>
        <p class="ph-sub">Registro completo de pagos aprobados, rechazados y cambios de plan.</p>
      </div>
      <button class="btn-refresh" @click="load" :disabled="loading">
        <i class="bi bi-arrow-clockwise" :class="{ spin: loading }"></i> Actualizar
      </button>
    </div>

    <!-- FILTROS -->
    <div class="ph-filters">
      <div class="filter-tabs">
        <button
          v-for="t in statusTabs"
          :key="t.value"
          class="tab-btn"
          :class="{ active: filterStatus === t.value }"
          @click="filterStatus = t.value; page = 1; load()"
        >
          <i :class="t.icon"></i> {{ t.label }}
        </button>
      </div>
      <div class="filter-row">
        <!-- Filtro rápido por año -->
        <div class="year-btns">
          <button
            v-for="y in yearOptions"
            :key="y"
            class="year-btn"
            :class="{ active: activeYear === y }"
            @click="selectYear(y)"
          >{{ y}}</button>
          <button
            class="year-btn"
            :class="{ active: activeYear === null && (filterDateFrom || filterDateTo) }"
            @click="activeYear = null"
            title="Rango personalizado"
          ><i class="bi bi-calendar3"></i></button>
        </div>

        <select v-model="filterType" class="filter-select" @change="page = 1; load()">
          <option value="">Todos los tipos</option>
          <option value="activation">Activación</option>
          <option value="upgrade">Upgrade</option>
          <option value="renewal">Renovación</option>
          <option value="downgrade">Downgrade</option>
        </select>

        <template v-if="activeYear === null">
          <CustomDatePicker
            v-model="filterDateFrom"
            @update:modelValue="page = 1; load()"
          />
          <CustomDatePicker
            v-model="filterDateTo"
            @update:modelValue="page = 1; load()"
          />
        </template>

        <button v-if="filterType || filterDateFrom || filterDateTo || activeYear" class="btn-clear" @click="clearFilters">
          <i class="bi bi-x-circle me-1"></i>Limpiar
        </button>
      </div>
    </div>

    <!-- CARGANDO -->
    <div v-if="loading" class="ph-empty">
      <i class="bi bi-hourglass-split spin"></i> Cargando historial...
    </div>

    <!-- SIN RESULTADOS -->
    <div v-else-if="!items.length" class="ph-empty">
      <i class="bi bi-inbox fs-2 mb-2 d-block"></i>
      <p>No hay registros con los filtros aplicados.</p>
    </div>

    <!-- LISTA -->
    <div v-else class="ph-list">
      <div v-for="p in items" :key="p.id" class="ph-card" :class="p.status">

        <!-- Cabecera tarjeta -->
        <div class="ph-card-head">
          <div class="ph-company">
            <div class="ph-company-name">{{ p.company.name }}</div>
            <div class="ph-company-nit">NIT: {{ p.company.nit }}</div>
          </div>
          <div class="ph-badges">
            <span class="ph-type-badge" :class="p.payment_type">
              {{ typeLabel[p.payment_type] || p.payment_type }}
            </span>
            <span class="ph-badge" :class="p.status">
              <i :class="p.status === 'approved' ? 'bi bi-check-circle-fill' : 'bi bi-x-circle-fill'"></i>
              {{ statusLabel[p.status] || p.status }}
            </span>
          </div>
        </div>

        <!-- Banner upgrade/downgrade -->
        <div v-if="p.current_plan && p.payment_type !== 'activation'" class="ph-plan-banner">
          <span class="plan-from">{{ p.current_plan.name }}</span>
          <i class="bi bi-arrow-right mx-2"></i>
          <span class="plan-to">{{ p.plan.name }}</span>
        </div>

        <!-- Info principal -->
        <div class="ph-info-grid">
          <div class="ph-info-row" v-if="!p.current_plan || p.payment_type === 'activation'">
            <span class="ph-info-label">Plan:</span>
            <span class="ph-info-val">{{ p.plan.name }}</span>
          </div>
          <div class="ph-info-row">
            <span class="ph-info-label">Monto solicitado:</span>
            <span class="ph-info-val amount">
              {{ formatCurrency(p.amount, p.currency_code) }}
              <small v-if="p.currency_code && p.currency_code !== 'COP'" class="currency-tag">{{ p.currency_code }}</small>
            </span>
          </div>
          <div class="ph-info-row" v-if="p.confirmed_amount">
            <span class="ph-info-label">Monto confirmado:</span>
            <span class="ph-info-val amount confirmed">
              {{ formatCurrency(p.confirmed_amount, p.currency_code) }}
            </span>
          </div>
          <div class="ph-info-row">
            <span class="ph-info-label">Admin:</span>
            <span class="ph-info-val">{{ p.admin_name }} — {{ p.admin_email }}</span>
          </div>
          <div class="ph-info-row" v-if="p.submitted_at">
            <span class="ph-info-label">Comprobante enviado:</span>
            <span class="ph-info-val">{{ formatDate(p.submitted_at) }}</span>
          </div>
          <div class="ph-info-row" v-if="p.reviewed_at">
            <span class="ph-info-label">{{ p.status === 'approved' ? 'Aprobado el:' : 'Rechazado el:' }}</span>
            <span class="ph-info-val">{{ formatDate(p.reviewed_at) }}</span>
          </div>
          <div class="ph-info-row" v-if="p.reviewed_by_name">
            <span class="ph-info-label">Revisado por:</span>
            <span class="ph-info-val">{{ p.reviewed_by_name }}</span>
          </div>
        </div>

        <!-- Bloque aprobación -->
        <div v-if="p.status === 'approved'" class="ph-approval-block">
          <div class="block-title"><i class="bi bi-bank me-1"></i>Datos de pago confirmados</div>
          <div class="ph-info-grid">
            <div class="ph-info-row" v-if="p.receipt_number">
              <span class="ph-info-label">N° Comprobante:</span>
              <span class="ph-info-val mono">{{ p.receipt_number }}</span>
            </div>
            <div class="ph-info-row" v-if="p.bank_origin">
              <span class="ph-info-label">Banco origen:</span>
              <span class="ph-info-val">{{ p.bank_origin }}</span>
            </div>
            <div class="ph-info-row" v-if="p.payment_date">
              <span class="ph-info-label">Fecha del pago:</span>
              <span class="ph-info-val">{{ p.payment_date }}</span>
            </div>
            <div class="ph-info-row" v-if="p.review_description">
              <span class="ph-info-label">Observaciones:</span>
              <span class="ph-info-val">{{ p.review_description }}</span>
            </div>
          </div>
        </div>

        <!-- Bloque rechazo -->
        <div v-if="p.status === 'rejected'" class="ph-rejection-block">
          <div class="block-title"><i class="bi bi-exclamation-triangle me-1"></i>Motivo de rechazo</div>
          <p class="rejection-reason">{{ p.rejection_reason }}</p>
          <p v-if="p.review_description" class="rejection-detail">{{ p.review_description }}</p>
        </div>

        <!-- Evidencias -->
        <div class="ph-evidence-row">
          <a
            v-if="p.receipt_url"
            :href="apiBase + p.receipt_url"
            target="_blank"
            class="evidence-link receipt"
          >
            <i class="bi bi-file-earmark-image me-1"></i>Comprobante del asociado
          </a>
          <a
            v-if="p.review_evidence_url"
            :href="apiBase + p.review_evidence_url"
            target="_blank"
            class="evidence-link review"
          >
            <i class="bi bi-paperclip me-1"></i>Evidencia del revisor
          </a>
        </div>

      </div>
    </div>

    <!-- PAGINACIÓN -->
    <div v-if="totalPages > 1" class="ph-pagination">
      <button class="pg-btn" :disabled="page <= 1" @click="changePage(page - 1)">
        <i class="bi bi-chevron-left"></i>
      </button>
      <span class="pg-info">Página {{ page }} de {{ totalPages }} ({{ total }} registros)</span>
      <button class="pg-btn" :disabled="page >= totalPages" @click="changePage(page + 1)">
        <i class="bi bi-chevron-right"></i>
      </button>
    </div>
    <div v-else-if="!loading && items.length" class="ph-total">
      {{ total }} registro{{ total !== 1 ? 's' : '' }}
    </div>

  </div>
</template>

<script>
import { ref, onMounted } from "vue"
import api from "@/services/apis"
import CustomDatePicker from "@/components/common/CustomDatePicker.vue"

export default {
  name: "PaymentHistoryView",
  components: { CustomDatePicker },
  setup() {
    const apiBase       = import.meta.env.VITE_API_URL || ""
    const loading       = ref(false)
    const items         = ref([])
    const total         = ref(0)
    const totalPages    = ref(1)
    const page          = ref(1)
    const filterStatus  = ref("")
    const filterType    = ref("")
    const filterDateFrom = ref("")
    const filterDateTo   = ref("")
    const activeYear     = ref(new Date().getFullYear())

    const currentYear = new Date().getFullYear()
    const yearOptions = Array.from({ length: 4 }, (_, i) => currentYear - i)

    const statusTabs = [
      { value: "",         label: "Todos",          icon: "bi bi-list-ul" },
      { value: "approved", label: "Aprobados",      icon: "bi bi-check-circle" },
      { value: "rejected", label: "Rechazados",     icon: "bi bi-x-circle" },
    ]

    const statusLabel = {
      approved: "Aprobado",
      rejected: "Rechazado",
    }
    const typeLabel = {
      activation: "Activación",
      upgrade:    "Upgrade",
      renewal:    "Renovación",
      downgrade:  "Downgrade",
    }

    function formatCurrency(val, code = "COP") {
      if (val == null) return "—"
      return new Intl.NumberFormat("es-CO", {
        style:    "currency",
        currency: code || "COP",
        maximumFractionDigits: 0,
      }).format(val)
    }

    function formatDate(dt) {
      if (!dt) return "—"
      return new Date(dt).toLocaleString("es-CO", {
        day: "2-digit", month: "short", year: "numeric",
        hour: "2-digit", minute: "2-digit",
      })
    }

    function selectYear(y) {
      activeYear.value     = y
      filterDateFrom.value = `${y}-01-01`
      filterDateTo.value   = `${y}-12-31`
      page.value = 1
      load()
    }

    async function load() {
      loading.value = true
      try {
        const params = { page: page.value, page_size: 20 }
        if (filterStatus.value)   params.status       = filterStatus.value
        if (filterType.value)     params.payment_type = filterType.value
        if (filterDateFrom.value) params.date_from    = filterDateFrom.value
        if (filterDateTo.value)   params.date_to      = filterDateTo.value
        const res     = await api.get("/payments/history", { params })
        items.value   = res.data.items
        total.value   = res.data.total
        totalPages.value = res.data.pages
      } catch {
        items.value = []
      } finally {
        loading.value = false
      }
    }

    function changePage(p) {
      page.value = p
      load()
    }

    function clearFilters() {
      filterType.value     = ""
      filterDateFrom.value = ""
      filterDateTo.value   = ""
      activeYear.value     = null
      page.value           = 1
      load()
    }

    onMounted(() => selectYear(currentYear))

    return {
      apiBase, loading, items, total, totalPages, page,
      filterStatus, filterType, filterDateFrom, filterDateTo, activeYear, yearOptions,
      statusTabs, statusLabel, typeLabel,
      formatCurrency, formatDate, load, changePage, clearFilters, selectYear,
    }
  }
}
</script>

<style scoped>
.ph-view { padding: 24px; max-width: 960px; margin: 0 auto; font-family: 'Segoe UI', system-ui, sans-serif; }

.ph-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 20px; gap: 12px; flex-wrap: wrap;
}
.ph-title { font-size: 1.4rem; font-weight: 800; color: #0f172a; margin: 0 0 4px; }
.ph-sub   { color: #64748b; font-size: .88rem; margin: 0; }

.btn-refresh {
  border: 1.5px solid #e2e8f0; background: #fff; color: #475569;
  padding: 8px 16px; border-radius: 8px; font-size: .85rem; font-weight: 600;
  cursor: pointer; transition: all .2s; display: flex; align-items: center; gap: 6px;
  white-space: nowrap; align-self: center;
}
.btn-refresh:hover:not(:disabled) { border-color: #2563eb; color: #2563eb; }

/* FILTROS */
.ph-filters { margin-bottom: 20px; display: flex; flex-direction: column; gap: 10px; }

.filter-tabs { display: flex; gap: 6px; flex-wrap: wrap; }
.tab-btn {
  padding: 7px 16px; border-radius: 20px; border: 1.5px solid #e2e8f0;
  background: #fff; color: #475569; font-size: .84rem; font-weight: 600;
  cursor: pointer; transition: all .2s; display: flex; align-items: center; gap: 6px;
}
.tab-btn:hover  { border-color: #2563eb; color: #2563eb; }
.tab-btn.active { background: #2563eb; border-color: #2563eb; color: #fff; }

.filter-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }

.year-btns { display: flex; gap: 4px; }
.year-btn {
  padding: 6px 12px; border-radius: 8px; border: 1.5px solid #e2e8f0;
  background: #fff; color: #475569; font-size: .82rem; font-weight: 700;
  cursor: pointer; transition: all .2s;
}
.year-btn:hover  { border-color: #6366f1; color: #6366f1; }
.year-btn.active { background: #6366f1; border-color: #6366f1; color: #fff; }
.filter-select {
  border: 1.5px solid #e2e8f0; border-radius: 8px;
  padding: 7px 12px; font-size: .84rem; color: #334155;
  outline: none; background: #fff; cursor: pointer;
}
.btn-clear {
  border: 1.5px solid #fca5a5; background: #fff5f5; color: #dc2626;
  padding: 7px 14px; border-radius: 8px; font-size: .83rem; font-weight: 600;
  cursor: pointer; transition: all .2s;
}
.btn-clear:hover { background: #fee2e2; }

/* VACÍO */
.ph-empty { text-align: center; padding: 60px 20px; color: #94a3b8; }

/* LISTA */
.ph-list { display: flex; flex-direction: column; gap: 14px; }

.ph-card {
  border: 1.5px solid #e2e8f0; border-radius: 12px;
  background: #fff; overflow: hidden;
  transition: box-shadow .2s;
}
.ph-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,.07); }
.ph-card.approved { border-left: 4px solid #16a34a; }
.ph-card.rejected { border-left: 4px solid #dc2626; }

/* Cabecera */
.ph-card-head {
  display: flex; justify-content: space-between; align-items: flex-start;
  padding: 14px 16px 10px; gap: 10px; flex-wrap: wrap;
  background: #f8fafc; border-bottom: 1px solid #f1f5f9;
}
.ph-company-name { font-weight: 700; color: #0f172a; font-size: .95rem; }
.ph-company-nit  { color: #64748b; font-size: .78rem; }

.ph-badges { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }

.ph-type-badge {
  padding: 3px 10px; border-radius: 20px; font-size: .74rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: .04em;
}
.ph-type-badge.activation { background: #dbeafe; color: #1d4ed8; }
.ph-type-badge.upgrade    { background: #d1fae5; color: #065f46; }
.ph-type-badge.renewal    { background: #ede9fe; color: #6d28d9; }
.ph-type-badge.downgrade  { background: #fef3c7; color: #92400e; }

.ph-badge {
  padding: 3px 10px; border-radius: 20px; font-size: .78rem; font-weight: 700;
  display: flex; align-items: center; gap: 4px;
}
.ph-badge.approved { background: #dcfce7; color: #15803d; }
.ph-badge.rejected { background: #fee2e2; color: #b91c1c; }

/* Plan banner (upgrade/downgrade) */
.ph-plan-banner {
  margin: 10px 16px 0;
  padding: 7px 14px;
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  font-size: .84rem;
  font-weight: 600;
  color: #0369a1;
  display: flex;
  align-items: center;
}
.plan-from { color: #64748b; }
.plan-to   { color: #0f172a; }

/* Info grid */
.ph-info-grid { padding: 12px 16px; display: flex; flex-direction: column; gap: 5px; }
.ph-info-row  { display: flex; gap: 8px; flex-wrap: wrap; font-size: .84rem; }
.ph-info-label { color: #64748b; min-width: 150px; flex-shrink: 0; }
.ph-info-val   { color: #1e293b; font-weight: 500; }
.ph-info-val.amount   { color: #0f172a; font-weight: 700; }
.ph-info-val.confirmed { color: #15803d; }
.ph-info-val.mono { font-family: 'Courier New', monospace; font-size: .82rem; }

/* Bloque aprobación */
.ph-approval-block {
  margin: 0 16px 12px;
  padding: 12px 14px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 10px;
}
.ph-approval-block .block-title { color: #166534; font-size: .82rem; font-weight: 700; margin-bottom: 8px; }

/* Bloque rechazo */
.ph-rejection-block {
  margin: 0 16px 12px;
  padding: 12px 14px;
  background: #fff5f5;
  border: 1px solid #fecaca;
  border-radius: 10px;
}
.ph-rejection-block .block-title { color: #b91c1c; font-size: .82rem; font-weight: 700; margin-bottom: 6px; }
.rejection-reason { color: #7f1d1d; font-size: .88rem; font-weight: 600; margin: 0 0 4px; }
.rejection-detail { color: #991b1b; font-size: .83rem; margin: 0; }

/* Evidencias */
.ph-evidence-row {
  display: flex; gap: 10px; flex-wrap: wrap;
  padding: 10px 16px 14px;
  border-top: 1px solid #f1f5f9;
}
.evidence-link {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 6px 14px; border-radius: 8px;
  font-size: .82rem; font-weight: 600;
  text-decoration: none; transition: all .2s;
}
.evidence-link.receipt {
  background: #eff6ff; color: #2563eb; border: 1.5px solid #bfdbfe;
}
.evidence-link.receipt:hover { background: #dbeafe; }
.evidence-link.review {
  background: #f5f3ff; color: #7c3aed; border: 1.5px solid #ddd6fe;
}
.evidence-link.review:hover { background: #ede9fe; }

/* Paginación */
.ph-pagination {
  display: flex; align-items: center; justify-content: center;
  gap: 16px; margin-top: 24px;
}
.pg-btn {
  width: 36px; height: 36px; border-radius: 8px;
  border: 1.5px solid #e2e8f0; background: #fff; color: #475569;
  cursor: pointer; font-size: 1rem; display: flex; align-items: center; justify-content: center;
  transition: all .2s;
}
.pg-btn:hover:not(:disabled) { border-color: #2563eb; color: #2563eb; }
.pg-btn:disabled { opacity: .4; cursor: default; }
.pg-info { color: #64748b; font-size: .85rem; }

.ph-total { text-align: center; color: #94a3b8; font-size: .83rem; margin-top: 16px; }

@keyframes spin { to { transform: rotate(360deg); } }
.spin { animation: spin .7s linear infinite; display: inline-block; }

@media (max-width: 600px) {
  .ph-view { padding: 16px; }
  .ph-info-label { min-width: 120px; }
}
</style>
