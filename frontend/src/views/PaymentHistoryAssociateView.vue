<template>
  <div class="pha-view">

    <div class="pha-header">
      <div>
        <h1 class="pha-title"><i class="bi bi-clock-history me-2"></i>Historial de Pagos</h1>
        <p class="pha-sub">Registro de todos tus pagos de plan — activaciones, renovaciones y upgrades.</p>
      </div>
      <button class="btn-refresh" @click="load" :disabled="loading">
        <i class="bi bi-arrow-clockwise" :class="{ spin: loading }"></i> Actualizar
      </button>
    </div>

    <!-- CARGANDO -->
    <div v-if="loading" class="pha-empty">
      <i class="bi bi-hourglass-split spin"></i> Cargando historial...
    </div>

    <!-- VACÍO -->
    <div v-else-if="!items.length" class="pha-empty">
      <i class="bi bi-inbox fs-2 d-block mb-2"></i>
      <p>Aún no tienes registros de pago.</p>
    </div>

    <!-- LISTA -->
    <div v-else class="pha-list">
      <div
        v-for="p in items"
        :key="p.id"
        class="pha-card"
        :class="p.status"
      >
        <!-- Cabecera -->
        <div class="pha-card-head">
          <div class="pha-head-left">
            <span class="type-badge" :class="p.payment_type">
              {{ typeLabel[p.payment_type] || p.payment_type }}
            </span>
            <span class="plan-name">
              <template v-if="p.previous_plan">
                {{ p.previous_plan.name }} <i class="bi bi-arrow-right mx-1"></i>
              </template>
              {{ p.plan?.name }}
            </span>
          </div>
          <span class="status-badge" :class="p.status">
            <i :class="{
              'bi bi-check-circle-fill': p.status === 'approved',
              'bi bi-x-circle-fill':     p.status === 'rejected',
              'bi bi-hourglass-split':   p.status === 'submitted',
              'bi bi-circle':            p.status === 'pending',
            }"></i>
            {{ statusLabel[p.status] || p.status }}
          </span>
        </div>

        <!-- Detalle -->
        <div class="pha-body">
          <div class="pha-row">
            <span class="pha-label">Monto:</span>
            <span class="pha-val amount">{{ formatCurrency(p.amount, p.currency_code) }}</span>
          </div>
          <div class="pha-row" v-if="p.confirmed_amount && p.status === 'approved'">
            <span class="pha-label">Monto confirmado:</span>
            <span class="pha-val confirmed">{{ formatCurrency(p.confirmed_amount, p.currency_code) }}</span>
          </div>
          <div class="pha-row" v-if="p.reviewed_at">
            <span class="pha-label">{{ p.status === 'approved' ? 'Aprobado:' : 'Rechazado:' }}</span>
            <span class="pha-val">{{ formatDate(p.reviewed_at) }}</span>
          </div>
          <div class="pha-row" v-else-if="p.submitted_at">
            <span class="pha-label">Enviado:</span>
            <span class="pha-val">{{ formatDate(p.submitted_at) }}</span>
          </div>
          <div class="pha-row" v-else>
            <span class="pha-label">Registrado:</span>
            <span class="pha-val">{{ formatDate(p.created_at) }}</span>
          </div>
        </div>

        <!-- Razón de rechazo -->
        <div v-if="p.status === 'rejected' && p.rejection_reason" class="pha-rejection">
          <i class="bi bi-exclamation-triangle-fill flex-shrink-0"></i>
          <div>
            <p class="reject-reason">{{ p.rejection_reason }}</p>
            <p v-if="p.review_description" class="reject-detail">{{ p.review_description }}</p>
          </div>
        </div>

        <!-- Evidencias -->
        <div v-if="p.receipt_url || p.review_evidence_url" class="pha-evidence">
          <a
            v-if="p.receipt_url"
            :href="apiBase + p.receipt_url"
            target="_blank"
            class="ev-link"
          >
            <i class="bi bi-file-earmark-image me-1"></i>Mi comprobante
          </a>
          <a
            v-if="p.review_evidence_url"
            :href="apiBase + p.review_evidence_url"
            target="_blank"
            class="ev-link review"
          >
            <i class="bi bi-paperclip me-1"></i>Evidencia EasyPosWeb
          </a>
        </div>

      </div>
    </div>

  </div>
</template>

<script>
import { ref, onMounted } from "vue"
import api from "@/services/apis"

export default {
  name: "PaymentHistoryAssociateView",
  setup() {
    const apiBase = import.meta.env.VITE_API_URL || ""
    const loading = ref(true)
    const items   = ref([])

    const typeLabel = {
      activation: "Activación",
      upgrade:    "Upgrade",
      renewal:    "Renovación",
      downgrade:  "Downgrade",
    }
    const statusLabel = {
      approved:  "Aprobado",
      rejected:  "Rechazado",
      submitted: "En revisión",
      pending:   "Pendiente",
    }

    function formatCurrency(val, code = "COP") {
      if (val == null) return "—"
      return new Intl.NumberFormat("es-CO", {
        style: "currency", currency: code || "COP", maximumFractionDigits: 0,
      }).format(val)
    }

    function formatDate(dt) {
      if (!dt) return "—"
      return new Date(dt).toLocaleDateString("es-CO", {
        day: "2-digit", month: "short", year: "numeric",
      })
    }

    async function load() {
      loading.value = true
      try {
        const res = await api.get("/payments/my-history")
        items.value = res.data
      } catch {
        items.value = []
      } finally {
        loading.value = false
      }
    }

    onMounted(load)

    return { apiBase, loading, items, typeLabel, statusLabel, formatCurrency, formatDate, load }
  }
}
</script>

<style scoped>
.pha-view { padding: 24px; max-width: 780px; margin: 0 auto; font-family: 'Segoe UI', system-ui, sans-serif; }

.pha-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 24px; gap: 12px; flex-wrap: wrap;
}
.pha-title { font-size: 1.3rem; font-weight: 800; color: #0f172a; margin: 0 0 4px; }
.pha-sub   { color: #64748b; font-size: .88rem; margin: 0; }

.btn-refresh {
  border: 1.5px solid #e2e8f0; background: #fff; color: #475569;
  padding: 8px 16px; border-radius: 8px; font-size: .85rem; font-weight: 600;
  cursor: pointer; transition: all .2s; display: flex; align-items: center; gap: 6px;
  align-self: center;
}
.btn-refresh:hover:not(:disabled) { border-color: #2563eb; color: #2563eb; }

.pha-empty { text-align: center; padding: 60px 20px; color: #94a3b8; }

/* LISTA */
.pha-list { display: flex; flex-direction: column; gap: 12px; }

.pha-card {
  border: 1.5px solid #e2e8f0; border-radius: 12px;
  background: #fff; overflow: hidden;
}
.pha-card.approved { border-left: 4px solid #16a34a; }
.pha-card.rejected { border-left: 4px solid #dc2626; }
.pha-card.submitted { border-left: 4px solid #f97316; }
.pha-card.pending   { border-left: 4px solid #94a3b8; }

/* Cabecera */
.pha-card-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 14px; gap: 8px; flex-wrap: wrap;
  background: #f8fafc; border-bottom: 1px solid #f1f5f9;
}
.pha-head-left { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }

.type-badge {
  padding: 2px 9px; border-radius: 20px; font-size: .72rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: .03em; flex-shrink: 0;
}
.type-badge.activation { background: #dbeafe; color: #1d4ed8; }
.type-badge.upgrade    { background: #d1fae5; color: #065f46; }
.type-badge.renewal    { background: #ede9fe; color: #6d28d9; }
.type-badge.downgrade  { background: #fef3c7; color: #92400e; }

.plan-name { font-size: .88rem; font-weight: 600; color: #1e293b; }

.status-badge {
  padding: 3px 10px; border-radius: 20px; font-size: .76rem; font-weight: 700;
  display: flex; align-items: center; gap: 4px; flex-shrink: 0;
}
.status-badge.approved  { background: #dcfce7; color: #15803d; }
.status-badge.rejected  { background: #fee2e2; color: #b91c1c; }
.status-badge.submitted { background: #fff7ed; color: #c2410c; }
.status-badge.pending   { background: #f1f5f9; color: #64748b; }

/* Cuerpo */
.pha-body { padding: 10px 14px; display: flex; flex-direction: column; gap: 4px; }
.pha-row  { display: flex; gap: 8px; font-size: .84rem; flex-wrap: wrap; }
.pha-label { color: #64748b; font-weight: 600; min-width: 140px; flex-shrink: 0; }
.pha-val   { color: #1e293b; font-weight: 500; }
.pha-val.amount    { color: #2563eb; font-weight: 700; }
.pha-val.confirmed { color: #15803d; font-weight: 700; }

/* Rechazo */
.pha-rejection {
  display: flex; gap: 8px; align-items: flex-start;
  margin: 0 14px 12px;
  padding: 8px 12px;
  background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px;
  color: #dc2626; font-size: .82rem;
}
.reject-reason { margin: 0; font-weight: 600; color: #b91c1c; }
.reject-detail { margin: 2px 0 0; color: #7f1d1d; font-size: .78rem; }

/* Evidencias */
.pha-evidence {
  display: flex; gap: 8px; flex-wrap: wrap;
  padding: 8px 14px 12px; border-top: 1px solid #f1f5f9;
}
.ev-link {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 5px 12px; border-radius: 7px; font-size: .78rem; font-weight: 600;
  text-decoration: none; transition: all .2s;
  background: #eff6ff; color: #2563eb; border: 1.5px solid #bfdbfe;
}
.ev-link:hover { background: #dbeafe; }
.ev-link.review {
  background: #f5f3ff; color: #7c3aed; border-color: #ddd6fe;
}
.ev-link.review:hover { background: #ede9fe; }

@keyframes spin { to { transform: rotate(360deg); } }
.spin { animation: spin .7s linear infinite; display: inline-block; }

@media (max-width: 600px) {
  .pha-view { padding: 16px; }
  .pha-label { min-width: 110px; }
}
</style>
