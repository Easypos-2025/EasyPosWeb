<template>
  <div class="pr-view">

    <!-- ENCABEZADO -->
    <div class="pr-header">
      <div>
        <h1 class="pr-title"><i class="bi bi-credit-card-2-back me-2"></i>Revisión de Pagos</h1>
        <p class="pr-sub">Pagos pendientes de activación, upgrade, renovación y cambio de plan.</p>
      </div>
      <div class="pr-header-right">
        <select v-model="filterType" class="filter-select" @change="load">
          <option value="">Todos los tipos</option>
          <option value="activation">Activación</option>
          <option value="upgrade">Upgrade</option>
          <option value="renewal">Renovación</option>
          <option value="downgrade">Downgrade</option>
        </select>
        <button class="btn-refresh" @click="load" :disabled="loading">
          <i class="bi bi-arrow-clockwise" :class="{ spin: loading }"></i> Actualizar
        </button>
      </div>
    </div>

    <!-- CARGANDO -->
    <div v-if="loading" class="pr-empty">
      <i class="bi bi-hourglass-split spin"></i> Cargando pagos...
    </div>

    <!-- SIN PAGOS -->
    <div v-else-if="!payments.length" class="pr-empty">
      <i class="bi bi-check-circle-fill text-success fs-2 mb-2"></i>
      <p>No hay pagos pendientes de revisión.</p>
    </div>

    <!-- LISTA DE PAGOS -->
    <div v-else class="pr-list">
      <div v-for="p in payments" :key="p.id" class="pr-card">
        <div class="pr-card-head">
          <div class="pr-company">
            <div class="pr-company-name">{{ p.company.name }}</div>
            <div class="pr-company-nit">NIT: {{ p.company.nit }}</div>
          </div>
          <div class="pr-badges">
            <span class="pr-type-badge" :class="p.payment_type">
              {{ typeLabel[p.payment_type] || p.payment_type }}
            </span>
            <span class="pr-badge" :class="p.status">
              {{ statusLabel[p.status] || p.status }}
            </span>
          </div>
        </div>

        <div class="pr-info-grid">
          <div class="pr-info-row">
            <span class="pr-info-label">Plan:</span>
            <span class="pr-info-val">{{ p.plan.name }}</span>
          </div>
          <div class="pr-info-row">
            <span class="pr-info-label">Monto:</span>
            <span class="pr-info-val amount">
              {{ formatCurrency(p.amount) }}
              <small v-if="p.currency_code && p.currency_code !== 'COP'" class="currency-tag">
                {{ p.currency_code }}
              </small>
            </span>
          </div>
          <div class="pr-info-row">
            <span class="pr-info-label">Admin:</span>
            <span class="pr-info-val">{{ p.admin_name }} — {{ p.admin_email }}</span>
          </div>
          <div class="pr-info-row">
            <span class="pr-info-label">Registrado:</span>
            <span class="pr-info-val">{{ formatDate(p.created_at) }}</span>
          </div>
          <div class="pr-info-row" v-if="p.submitted_at">
            <span class="pr-info-label">Comprobante enviado:</span>
            <span class="pr-info-val">{{ formatDate(p.submitted_at) }}</span>
          </div>
        </div>

        <!-- BANNER UPGRADE -->
        <div v-if="p.payment_type === 'upgrade'" class="upgrade-banner">
          <i class="bi bi-arrow-up-circle-fill upgrade-arrow"></i>
          <div class="upgrade-transition">
            <span class="upgrade-from">{{ p.current_plan?.name ?? '—' }}</span>
            <i class="bi bi-arrow-right upgrade-sep"></i>
            <span class="upgrade-to">{{ p.plan.name }}</span>
          </div>
          <span class="upgrade-note">El plan actual se cancelará y se activará el nuevo.</span>
        </div>

        <!-- COMPROBANTE -->
        <div class="pr-receipt" v-if="p.receipt_url">
          <div class="pr-receipt-label"><i class="bi bi-paperclip me-1"></i>Comprobante adjunto</div>
          <a :href="apiBase + p.receipt_url" target="_blank" class="pr-receipt-link">
            <template v-if="p.receipt_url.endsWith('.pdf')">
              <i class="bi bi-file-earmark-pdf text-danger me-1"></i> Ver PDF
            </template>
            <template v-else>
              <img :src="apiBase + p.receipt_url" class="pr-receipt-img" alt="Comprobante" />
            </template>
          </a>
        </div>
        <div v-else class="pr-no-receipt">
          <i class="bi bi-clock me-1"></i> El asociado aún no ha enviado comprobante.
        </div>

        <!-- ACCIONES -->
        <div class="pr-actions">
          <button
            v-if="p.payment_type === 'upgrade'"
            class="btn-upgrade" :disabled="actioning === p.id"
            @click="confirmApprove(p)"
          >
            <i class="bi bi-arrow-up-circle-fill me-1"></i> Subir de Plan
          </button>
          <button
            v-else
            class="btn-approve" :disabled="actioning === p.id"
            @click="confirmApprove(p)"
          >
            <i class="bi bi-check-circle-fill me-1"></i> Aprobar
          </button>
          <button class="btn-reject" :disabled="actioning === p.id"
                  @click="openReject(p)">
            <i class="bi bi-x-circle-fill me-1"></i> Rechazar
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL APROBAR / SUBIR DE PLAN -->
    <div v-if="approveTarget" class="pr-modal-overlay" @click.self="approveTarget = null">
      <div class="pr-modal">

        <!-- Upgrade -->
        <template v-if="approveTarget.payment_type === 'upgrade'">
          <div class="modal-icon upgrade"><i class="bi bi-arrow-up-circle-fill"></i></div>
          <h3>¿Confirmar Upgrade de Plan?</h3>
          <div class="upgrade-modal-transition">
            <span class="umt-from">{{ approveTarget.current_plan?.name ?? '—' }}</span>
            <i class="bi bi-arrow-right umt-arrow"></i>
            <span class="umt-to">{{ approveTarget.plan.name }}</span>
          </div>
          <p>
            Empresa: <strong>{{ approveTarget.company.name }}</strong><br>
            Monto pagado: <strong>{{ formatCurrency(approveTarget.amount) }}</strong>
          </p>
          <p class="modal-note">El plan actual se cancelará y se activará el nuevo por 365 días. El asociado será notificado.</p>
          <div class="modal-btns">
            <button class="btn-cancel" @click="approveTarget = null">Cancelar</button>
            <button class="btn-upgrade" :disabled="actioning === approveTarget.id" @click="doApprove">
              <span v-if="actioning === approveTarget.id">
                <i class="bi bi-hourglass-split spin me-1"></i>Procesando...
              </span>
              <span v-else><i class="bi bi-arrow-up-circle-fill me-1"></i>Confirmar Upgrade</span>
            </button>
          </div>
        </template>

        <!-- Aprobación normal -->
        <template v-else>
          <div class="modal-icon green"><i class="bi bi-check-circle-fill"></i></div>
          <h3>¿Aprobar pago?</h3>
          <p>
            Empresa: <strong>{{ approveTarget.company.name }}</strong><br>
            Plan: <strong>{{ approveTarget.plan.name }}</strong> —
            <strong>{{ formatCurrency(approveTarget.amount) }}</strong>
          </p>
          <p class="modal-note">Se activará la cuenta y se notificará al asociado por correo.</p>
          <div class="modal-btns">
            <button class="btn-cancel" @click="approveTarget = null">Cancelar</button>
            <button class="btn-approve" :disabled="actioning === approveTarget.id" @click="doApprove">
              <span v-if="actioning === approveTarget.id">
                <i class="bi bi-hourglass-split spin me-1"></i>Aprobando...
              </span>
              <span v-else>Confirmar aprobación</span>
            </button>
          </div>
        </template>

      </div>
    </div>

    <!-- MODAL RECHAZAR -->
    <div v-if="rejectTarget" class="pr-modal-overlay" @click.self="closeReject">
      <div class="pr-modal">
        <div class="modal-icon red"><i class="bi bi-x-circle-fill"></i></div>
        <h3>Rechazar comprobante</h3>
        <p>Empresa: <strong>{{ rejectTarget.company.name }}</strong></p>
        <div class="field-group" :class="{ error: rejectErr }">
          <label>Motivo de rechazo <span class="req">*</span></label>
          <textarea v-model="rejectReason" rows="3"
                    placeholder="Ej. El comprobante es ilegible, el monto no coincide..."></textarea>
          <span v-if="rejectErr" class="field-error">{{ rejectErr }}</span>
        </div>
        <p class="modal-note">El asociado recibirá este motivo por correo y podrá reenviar el comprobante.</p>
        <div class="modal-btns">
          <button class="btn-cancel" @click="closeReject">Cancelar</button>
          <button class="btn-reject" :disabled="actioning === rejectTarget.id"
                  @click="doReject">
            <span v-if="actioning === rejectTarget.id">
              <i class="bi bi-hourglass-split spin me-1"></i>Rechazando...
            </span>
            <span v-else>Confirmar rechazo</span>
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import { ref, onMounted } from "vue"
import api from "@/services/apis"

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

export default {
  name: "PaymentReviewView",

  setup() {
    const loading      = ref(true)
    const payments     = ref([])
    const actioning    = ref(null)
    const approveTarget = ref(null)
    const rejectTarget  = ref(null)
    const rejectReason  = ref("")
    const rejectErr     = ref("")
    const apiBase       = API_URL
    const filterType    = ref("")

    const statusLabel = {
      pending:   "Pendiente",
      submitted: "Comprobante enviado",
      approved:  "Aprobado",
      rejected:  "Rechazado",
    }
    const typeLabel = {
      activation: "Activación",
      upgrade:    "Upgrade",
      renewal:    "Renovación",
      downgrade:  "Downgrade",
    }

    function formatCurrency(amount) {
      return new Intl.NumberFormat("es-CO", {
        style: "currency", currency: "COP", maximumFractionDigits: 0,
      }).format(amount ?? 0)
    }

    function formatDate(dt) {
      if (!dt) return "—"
      return new Date(dt).toLocaleString("es-CO", {
        dateStyle: "medium", timeStyle: "short",
      })
    }

    async function load() {
      loading.value = true
      try {
        const url = filterType.value
          ? `/payments/pending?payment_type=${filterType.value}`
          : "/payments/pending"
        const res = await api.get(url)
        payments.value = res.data
      } catch {
        payments.value = []
      } finally {
        loading.value = false
      }
    }

    function confirmApprove(p) { approveTarget.value = p }

    async function doApprove() {
      if (!approveTarget.value) return
      actioning.value = approveTarget.value.id
      try {
        await api.put(`/payments/${approveTarget.value.id}/approve`)
        approveTarget.value = null
        await load()
      } catch (e) {
        alert(e.response?.data?.detail || "Error al aprobar")
      } finally {
        actioning.value = null
      }
    }

    function openReject(p) {
      rejectTarget.value = p
      rejectReason.value = ""
      rejectErr.value    = ""
    }
    function closeReject() {
      rejectTarget.value = null
      rejectReason.value = ""
      rejectErr.value    = ""
    }

    async function doReject() {
      if (!rejectTarget.value) return
      rejectErr.value = ""
      if (!rejectReason.value.trim()) {
        rejectErr.value = "El motivo es obligatorio"
        return
      }
      actioning.value = rejectTarget.value.id
      try {
        await api.put(`/payments/${rejectTarget.value.id}/reject`, {
          reason: rejectReason.value,
        })
        closeReject()
        await load()
      } catch (e) {
        rejectErr.value = e.response?.data?.detail || "Error al rechazar"
      } finally {
        actioning.value = null
      }
    }

    onMounted(load)

    return {
      loading, payments, actioning, approveTarget,
      rejectTarget, rejectReason, rejectErr, apiBase,
      filterType, statusLabel, typeLabel, formatCurrency, formatDate,
      load, confirmApprove, doApprove, openReject, closeReject, doReject,
    }
  }
}
</script>

<style scoped>
.pr-view { padding: 24px; max-width: 900px; margin: 0 auto; font-family: 'Segoe UI', system-ui, sans-serif; }

.pr-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 24px; gap: 12px; flex-wrap: wrap;
}
.pr-title { font-size: 1.4rem; font-weight: 800; color: #0f172a; margin: 0 0 4px; }
.pr-sub   { color: #64748b; font-size: .88rem; margin: 0; }

.pr-header-right { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }

.filter-select {
  border: 1.5px solid #e2e8f0; border-radius: 8px;
  padding: 7px 12px; font-size: .84rem; color: #334155;
  outline: none; background: #fff; cursor: pointer;
}

.btn-refresh {
  border: 1.5px solid #e2e8f0; background: #fff; color: #475569;
  padding: 8px 16px; border-radius: 8px; font-size: .85rem; font-weight: 600;
  cursor: pointer; transition: all .2s; display: flex; align-items: center; gap: 6px;
  white-space: nowrap;
}
.btn-refresh:hover:not(:disabled) { border-color: #2563eb; color: #2563eb; }

.pr-empty { text-align: center; padding: 60px 20px; color: #94a3b8; }

/* TARJETA PAGO */
.pr-list  { display: flex; flex-direction: column; gap: 16px; }
.pr-card  {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 16px;
  padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,.06);
}
.pr-card-head {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 14px; gap: 8px;
}
.pr-company-name { font-weight: 800; font-size: 1rem; color: #0f172a; }
.pr-company-nit  { font-size: .78rem; color: #94a3b8; margin-top: 2px; }

.pr-badges { display: flex; gap: 6px; flex-shrink: 0; flex-direction: column; align-items: flex-end; }

/* BADGE TIPO */
.pr-type-badge {
  padding: 3px 8px; border-radius: 20px; font-size: .68rem;
  font-weight: 700; white-space: nowrap;
}
.pr-type-badge.activation { background: #eff6ff; color: #2563eb; }
.pr-type-badge.upgrade    { background: #f0fdf4; color: #16a34a; }
.pr-type-badge.renewal    { background: #fdf4ff; color: #9333ea; }
.pr-type-badge.downgrade  { background: #fff7ed; color: #f97316; }

.currency-tag { font-size: .68rem; background: #e2e8f0; color: #475569; border-radius: 4px; padding: 1px 4px; margin-left: 4px; }

/* BADGE ESTADO */
.pr-badge {
  padding: 4px 10px; border-radius: 20px; font-size: .72rem;
  font-weight: 700; white-space: nowrap; flex-shrink: 0;
}
.pr-badge.pending   { background: #fff7ed; color: #f97316; }
.pr-badge.submitted { background: #eff6ff; color: #2563eb; }
.pr-badge.approved  { background: #f0fdf4; color: #10b981; }
.pr-badge.rejected  { background: #fef2f2; color: #ef4444; }

.pr-info-grid { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }
.pr-info-row  { display: flex; gap: 8px; font-size: .84rem; }
.pr-info-label { color: #64748b; font-weight: 600; min-width: 140px; flex-shrink: 0; }
.pr-info-val   { color: #0f172a; }
.pr-info-val.amount { font-weight: 800; color: #2563eb; font-size: .92rem; }

.pr-receipt { margin-bottom: 14px; }
.pr-receipt-label { font-size: .82rem; font-weight: 600; color: #475569; margin-bottom: 8px; }
.pr-receipt-link  { display: inline-block; text-decoration: none; color: #2563eb; font-size: .85rem; }
.pr-receipt-img {
  max-width: 100%; max-height: 220px; border-radius: 8px;
  border: 1px solid #e2e8f0; display: block; cursor: pointer;
}
.pr-no-receipt { font-size: .82rem; color: #94a3b8; margin-bottom: 14px; }

/* BANNER UPGRADE */
.upgrade-banner {
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
  background: linear-gradient(135deg, #eff6ff, #f0fdf4);
  border: 1.5px solid #86efac; border-radius: 10px;
  padding: 12px 16px; margin-bottom: 14px;
}
.upgrade-arrow { font-size: 1.4rem; color: #16a34a; flex-shrink: 0; }
.upgrade-transition { display: flex; align-items: center; gap: 8px; flex: 1; }
.upgrade-from { font-weight: 700; font-size: .9rem; color: #64748b; background: #e2e8f0; padding: 3px 10px; border-radius: 20px; }
.upgrade-sep  { color: #16a34a; font-size: 1rem; }
.upgrade-to   { font-weight: 800; font-size: .9rem; color: #15803d; background: #dcfce7; padding: 3px 10px; border-radius: 20px; }
.upgrade-note { font-size: .75rem; color: #64748b; width: 100%; margin-top: 4px; }

.pr-actions { display: flex; gap: 10px; }

.btn-upgrade {
  background: linear-gradient(135deg, #2563eb, #7c3aed); color: #fff; border: none;
  padding: 9px 18px; border-radius: 8px; font-weight: 700; font-size: .85rem;
  cursor: pointer; transition: all .2s;
  display: flex; align-items: center; gap: 4px;
  box-shadow: 0 2px 8px rgba(124,58,237,.3);
}
.btn-upgrade:hover:not(:disabled) { filter: brightness(1.1); box-shadow: 0 4px 12px rgba(124,58,237,.4); }
.btn-upgrade:disabled { opacity: .5; cursor: not-allowed; }

.btn-approve {
  background: #10b981; color: #fff; border: none;
  padding: 9px 18px; border-radius: 8px; font-weight: 700; font-size: .85rem;
  cursor: pointer; transition: all .2s;
  display: flex; align-items: center; gap: 4px;
}
.btn-approve:hover:not(:disabled) { background: #059669; }
.btn-approve:disabled { opacity: .5; cursor: not-allowed; }

.btn-reject {
  background: #ef4444; color: #fff; border: none;
  padding: 9px 18px; border-radius: 8px; font-weight: 700; font-size: .85rem;
  cursor: pointer; transition: all .2s;
  display: flex; align-items: center; gap: 4px;
}
.btn-reject:hover:not(:disabled) { background: #dc2626; }
.btn-reject:disabled { opacity: .5; cursor: not-allowed; }

/* MODAL */
.pr-modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.5);
  display: flex; align-items: center; justify-content: center; z-index: 9999;
  padding: 20px;
}
.pr-modal {
  background: #fff; border-radius: 16px; padding: 32px;
  width: 100%; max-width: 440px;
  box-shadow: 0 24px 60px rgba(0,0,0,.3);
}
.modal-icon {
  width: 56px; height: 56px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.6rem; margin: 0 auto 16px;
}
.modal-icon.green   { background: #f0fdf4; color: #10b981; }
.modal-icon.red     { background: #fef2f2; color: #ef4444; }
.modal-icon.upgrade { background: #eff6ff; color: #2563eb; }

.upgrade-modal-transition {
  display: flex; align-items: center; justify-content: center; gap: 10px;
  margin: 0 auto 12px; padding: 10px 16px;
  background: linear-gradient(135deg, #eff6ff, #f0fdf4);
  border-radius: 10px; border: 1px solid #86efac;
}
.umt-from  { font-weight: 700; color: #64748b; background: #e2e8f0; padding: 4px 12px; border-radius: 20px; font-size: .88rem; }
.umt-arrow { color: #16a34a; font-size: 1.1rem; }
.umt-to    { font-weight: 800; color: #15803d; background: #dcfce7; padding: 4px 12px; border-radius: 20px; font-size: .88rem; }
.pr-modal h3 { text-align: center; font-size: 1.1rem; font-weight: 800; color: #0f172a; margin-bottom: 10px; }
.pr-modal p  { text-align: center; color: #64748b; font-size: .88rem; margin-bottom: 8px; }
.modal-note  { font-size: .78rem; color: #94a3b8; }
.modal-btns  { display: flex; gap: 10px; margin-top: 20px; }
.modal-btns .btn-approve,
.modal-btns .btn-reject { flex: 1; justify-content: center; }
.btn-cancel {
  flex: 1; border: 1.5px solid #e2e8f0; background: #fff; color: #64748b;
  padding: 10px; border-radius: 8px; font-weight: 600; font-size: .88rem;
  cursor: pointer; transition: all .2s;
}
.btn-cancel:hover { border-color: #94a3b8; }

.field-group { display: flex; flex-direction: column; gap: 6px; }
.field-group label { font-size: .84rem; font-weight: 600; color: #334155; }
.field-group.error label { color: #ef4444; }
.req { color: #ef4444; }
.field-group textarea {
  border: 1.5px solid #e2e8f0; border-radius: 8px;
  padding: 10px 14px; font-size: .88rem; resize: vertical;
  outline: none; color: #0f172a; font-family: inherit;
}
.field-group textarea:focus { border-color: #2563eb; }
.field-group.error textarea { border-color: #ef4444; }
.field-error { color: #ef4444; font-size: .78rem; }

.spin { animation: spin 1s linear infinite; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 600px) {
  .pr-info-row { flex-direction: column; gap: 2px; }
  .pr-info-label { min-width: auto; }
  .pr-actions { flex-direction: column; }
  .modal-btns { flex-direction: column; }
}
</style>
