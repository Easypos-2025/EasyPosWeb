<template>
  <div class="pr-view">

    <!-- ENCABEZADO -->
    <div class="pr-header">
      <div>
        <h1 class="pr-title"><i class="bi bi-credit-card-2-back me-2"></i>Revisión de Pagos</h1>
        <p class="pr-sub">Pagos pendientes de activación, upgrade, renovación y cambio de plan.</p>
      </div>
      <div class="pr-header-right">
        <select v-if="activeTab === 'review'" v-model="filterType" class="filter-select" @change="load">
          <option value="">Todos los tipos</option>
          <option value="activation">Activación</option>
          <option value="upgrade">Upgrade</option>
          <option value="renewal">Renovación</option>
          <option value="downgrade">Downgrade</option>
        </select>
        <button class="btn-refresh" @click="activeTab === 'review' ? load() : loadBlocked()" :disabled="loading || loadingBlocked">
          <i class="bi bi-arrow-clockwise" :class="{ spin: loading || loadingBlocked }"></i> Actualizar
        </button>
      </div>
    </div>

    <!-- TABS -->
    <div class="pr-tabs">
      <button class="pr-tab" :class="{ active: activeTab === 'review' }" @click="activeTab = 'review'">
        <i class="bi bi-inbox"></i> Pagos pendientes
        <span v-if="payments.length" class="pr-tab-badge">{{ payments.length }}</span>
      </button>
      <button class="pr-tab" :class="{ active: activeTab === 'blocked' }" @click="activeTab = 'blocked'; loadBlocked()">
        <i class="bi bi-lock-fill"></i> Empresas bloqueadas
        <span v-if="blockedCompanies.length" class="pr-tab-badge pr-tab-badge-warn">{{ blockedCompanies.length }}</span>
      </button>
    </div>

    <!-- ══════ TAB: REVISIÓN DE PAGOS ══════ -->
    <template v-if="activeTab === 'review'">

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

    </template><!-- fin TAB review -->

    <!-- ══════ TAB: EMPRESAS BLOQUEADAS ══════ -->
    <template v-if="activeTab === 'blocked'">

      <div v-if="loadingBlocked" class="pr-empty">
        <i class="bi bi-hourglass-split spin"></i> Cargando empresas bloqueadas...
      </div>

      <div v-else-if="!blockedCompanies.length" class="pr-empty">
        <i class="bi bi-check-circle-fill text-success fs-2 mb-2"></i>
        <p>No hay empresas bloqueadas en este momento.</p>
      </div>

      <div v-else class="bl-list">
        <div class="bl-info-banner">
          <i class="bi bi-info-circle-fill me-2"></i>
          Estas empresas quedaron bloqueadas en el proceso de pago (caída de conexión u otro imprevisto).
          Al desbloquear, su estado se restablece a <strong>activo</strong> y los pagos pendientes se cancelan automáticamente.
        </div>

        <div v-for="c in blockedCompanies" :key="c.company_id" class="bl-card">
          <div class="bl-card-left">
            <div class="bl-lock-icon"><i class="bi bi-lock-fill"></i></div>
            <div class="bl-info">
              <div class="bl-company-name">{{ c.company_name }}</div>
              <div class="bl-company-nit">NIT: {{ c.nit }}</div>
              <div v-if="c.admin_name" class="bl-admin">
                <i class="bi bi-person me-1"></i>{{ c.admin_name }}
                <span v-if="c.admin_email"> · {{ c.admin_email }}</span>
              </div>
              <div v-if="c.plan_name" class="bl-plan">
                <i class="bi bi-award me-1"></i>Plan activo: {{ c.plan_name }}
              </div>
            </div>
          </div>

          <div class="bl-card-right">
            <div class="bl-status-wrap">
              <span class="bl-status-badge" :class="c.payment_status">
                {{ statusLabel[c.payment_status] || c.payment_status }}
              </span>
              <span v-if="c.upgrade_status" class="bl-upgrade-badge">
                {{ c.upgrade_status }}
              </span>
            </div>
            <div v-if="c.latest_payment" class="bl-payment-info">
              <span class="bl-pay-type">{{ typeLabel[c.latest_payment.type] || c.latest_payment.type }}</span>
              <span class="bl-pay-amount">{{ formatCurrency(c.latest_payment.amount) }}</span>
              <span v-if="c.latest_payment.created_at" class="bl-pay-date">
                Desde: {{ formatDate(c.latest_payment.created_at) }}
              </span>
            </div>
            <button
              class="bl-btn-unlock"
              :disabled="unblocking === c.company_id"
              @click="doUnblock(c)"
            >
              <i v-if="unblocking === c.company_id" class="bi bi-arrow-repeat spin me-1"></i>
              <i v-else class="bi bi-unlock-fill me-1"></i>
              {{ unblocking === c.company_id ? 'Desbloqueando...' : 'Desbloquear' }}
            </button>
          </div>
        </div>
      </div>

    </template><!-- fin TAB blocked -->

    <!-- MODAL APROBAR / SUBIR DE PLAN -->
    <div v-if="approveTarget" class="pr-modal-overlay" @click.self="closeApprove">
      <div class="pr-modal pr-modal-lg">

        <div class="modal-header-row">
          <div class="modal-icon" :class="approveTarget.payment_type === 'upgrade' ? 'upgrade' : 'green'">
            <i :class="approveTarget.payment_type === 'upgrade' ? 'bi bi-arrow-up-circle-fill' : 'bi bi-check-circle-fill'"></i>
          </div>
          <h3>{{ approveTarget.payment_type === 'upgrade' ? 'Confirmar Upgrade de Plan' : 'Aprobar Pago' }}</h3>
        </div>

        <!-- Transición de plan (upgrade) -->
        <div v-if="approveTarget.payment_type === 'upgrade'" class="upgrade-modal-transition">
          <span class="umt-from">{{ approveTarget.current_plan?.name ?? '—' }}</span>
          <i class="bi bi-arrow-right umt-arrow"></i>
          <span class="umt-to">{{ approveTarget.plan.name }}</span>
        </div>

        <p class="modal-company-info">
          <strong>{{ approveTarget.company.name }}</strong> —
          {{ approveTarget.payment_type === 'upgrade' ? approveTarget.plan.name : `Plan ${approveTarget.plan.name}` }} —
          <strong>{{ formatCurrency(approveTarget.amount) }}</strong>
        </p>

        <!-- ALERTA DUPLICADO -->
        <div v-if="duplicateInfo" class="duplicate-alert">
          <i class="bi bi-exclamation-triangle-fill me-2"></i>
          <div>
            <strong>Recibo duplicado detectado</strong>
            <p>Este N° de recibo del mismo banco ya fue registrado en otro pago aprobado:</p>
            <ul>
              <li>Empresa: <strong>{{ duplicateInfo.company_name }}</strong></li>
              <li>Fecha: {{ duplicateInfo.payment_date ?? '—' }}</li>
              <li>Monto: {{ formatCurrency(duplicateInfo.amount) }}</li>
            </ul>
            <p>Verifica el número de recibo antes de continuar.</p>
          </div>
        </div>

        <!-- FORMULARIO DE EVIDENCIA -->
        <div class="evidence-form">
          <div class="ev-title"><i class="bi bi-shield-check me-2"></i>Evidencia de aprobación</div>

          <div class="ev-row">
            <div class="field-group" :class="{ error: approveErr.receipt_number }">
              <label>N° Recibo bancario <span class="req">*</span></label>
              <input v-model="approveForm.receipt_number" type="text" placeholder="Ej. 2024-0012345" />
              <span v-if="approveErr.receipt_number" class="field-error">{{ approveErr.receipt_number }}</span>
            </div>
            <div class="field-group" :class="{ error: approveErr.bank_origin }">
              <label>Banco origen (del asociado) <span class="req">*</span></label>
              <select v-model="approveForm.bank_origin">
                <option value="" disabled>Selecciona banco...</option>
                <option v-for="b in BANKS_CO" :key="b" :value="b">{{ b }}</option>
              </select>
              <span v-if="approveErr.bank_origin" class="field-error">{{ approveErr.bank_origin }}</span>
            </div>
          </div>

          <div class="ev-row">
            <div class="field-group" :class="{ error: approveErr.payment_date }">
              <label>Fecha del pago <span class="req">*</span></label>
              <CustomDatePicker v-model="approveForm.payment_date" />
              <span v-if="approveErr.payment_date" class="field-error">{{ approveErr.payment_date }}</span>
            </div>
            <div class="field-group">
              <label>Monto confirmado</label>
              <input v-model="approveForm.confirmed_amount" type="number" step="1" :placeholder="`${approveTarget.amount}`" />
            </div>
          </div>

          <div class="field-group">
            <label>Descripción / observaciones</label>
            <textarea v-model="approveForm.review_description" rows="2" placeholder="Pago verificado correctamente. Ref. interna..."></textarea>
          </div>

          <div class="field-group">
            <label>Evidencia del banco (opcional)</label>
            <div class="ev-upload" @click="$refs.approveFileInput.click()" :class="{ 'has-file': approveFile }">
              <template v-if="!approveFile">
                <i class="bi bi-cloud-upload me-2"></i> Adjuntar comprobante del banco
              </template>
              <template v-else>
                <i class="bi bi-paperclip me-2 text-success"></i> {{ approveFile.name }}
                <button type="button" class="ev-remove-file" @click.stop="approveFile = null">
                  <i class="bi bi-x"></i>
                </button>
              </template>
            </div>
            <input ref="approveFileInput" type="file"
                   accept="image/jpeg,image/png,image/webp,application/pdf"
                   style="display:none" @change="e => approveFile = e.target.files[0]" />
          </div>
        </div>

        <div class="modal-dates-info">
          <i class="bi bi-calendar-range me-1"></i>
          Período del plan:
          <strong>{{ planStartDate }}</strong>
          <i class="bi bi-arrow-right mx-1"></i>
          <strong>{{ planEndDate }}</strong>
          <span class="dates-note">(30 días)</span>
        </div>
        <div v-if="approveErr.general" class="error-general">
          <i class="bi bi-exclamation-circle me-1"></i>{{ approveErr.general }}
        </div>

        <div class="modal-btns">
          <button class="btn-cancel" @click="closeApprove">Cancelar</button>
          <button
            :class="approveTarget.payment_type === 'upgrade' ? 'btn-upgrade' : 'btn-approve'"
            :disabled="actioning === approveTarget.id"
            @click="doApprove"
          >
            <span v-if="actioning === approveTarget.id">
              <i class="bi bi-hourglass-split spin me-1"></i>Procesando...
            </span>
            <span v-else>
              <i :class="approveTarget.payment_type === 'upgrade' ? 'bi bi-arrow-up-circle-fill' : 'bi bi-check-circle-fill'" class="me-1"></i>
              {{ approveTarget.payment_type === 'upgrade' ? 'Confirmar Upgrade' : 'Confirmar aprobación' }}
            </span>
          </button>
        </div>

      </div>
    </div>

    <!-- MODAL RECHAZAR -->
    <div v-if="rejectTarget" class="pr-modal-overlay" @click.self="closeReject">
      <div class="pr-modal pr-modal-lg">
        <div class="modal-header-row">
          <div class="modal-icon red"><i class="bi bi-x-circle-fill"></i></div>
          <h3>Rechazar comprobante</h3>
        </div>
        <p class="modal-company-info">Empresa: <strong>{{ rejectTarget.company.name }}</strong></p>

        <div class="evidence-form">
          <div class="ev-title"><i class="bi bi-file-earmark-x me-2"></i>Evidencia de rechazo</div>

          <div class="field-group" :class="{ error: rejectErr }">
            <label>Motivo breve <span class="req">*</span> <small>(se enviará al asociado)</small></label>
            <input v-model="rejectReason" type="text" placeholder="Ej. Monto no coincide, comprobante ilegible..." />
            <span v-if="rejectErr" class="field-error">{{ rejectErr }}</span>
          </div>

          <div class="field-group">
            <label>Descripción detallada <small>(registro interno)</small></label>
            <textarea v-model="rejectForm.review_description" rows="3"
                      placeholder="Detalle adicional del motivo de rechazo, observaciones internas..."></textarea>
          </div>

          <div class="field-group">
            <label>Evidencia de rechazo (opcional)</label>
            <div class="ev-upload" @click="$refs.rejectFileInput.click()" :class="{ 'has-file': rejectFile }">
              <template v-if="!rejectFile">
                <i class="bi bi-cloud-upload me-2"></i> Adjuntar evidencia del rechazo
              </template>
              <template v-else>
                <i class="bi bi-paperclip me-2 text-success"></i> {{ rejectFile.name }}
                <button type="button" class="ev-remove-file" @click.stop="rejectFile = null">
                  <i class="bi bi-x"></i>
                </button>
              </template>
            </div>
            <input ref="rejectFileInput" type="file"
                   accept="image/jpeg,image/png,image/webp,application/pdf"
                   style="display:none" @change="e => rejectFile = e.target.files[0]" />
          </div>
        </div>

        <p class="modal-note">El asociado recibirá el motivo breve por correo y podrá reenviar el comprobante.</p>
        <div class="modal-btns">
          <button class="btn-cancel" @click="closeReject">Cancelar</button>
          <button class="btn-reject" :disabled="actioning === rejectTarget.id" @click="doReject">
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
import { ref, computed, onMounted } from "vue"
import api from "@/services/apis"
import CustomDatePicker from "@/components/common/CustomDatePicker.vue"

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

const BANKS_CO = [
  "Bancolombia", "Banco de Bogotá", "Davivienda", "BBVA Colombia",
  "Banco de Occidente", "Banco Popular", "Banco Caja Social", "Banco Agrario",
  "Nequi", "Daviplata", "Nubank", "Banco Itaú", "Banco GNB Sudameris",
  "Banco Falabella", "Banco Pichincha", "Lulo Bank", "Rappipay", "Otro",
]

export default {
  name: "PaymentReviewView",
  components: { CustomDatePicker },

  setup() {
    const loading       = ref(true)
    const payments      = ref([])
    const actioning     = ref(null)
    const filterType    = ref("")
    const apiBase       = API_URL
    const activeTab     = ref("review")

    // Empresas bloqueadas
    const blockedCompanies = ref([])
    const loadingBlocked   = ref(false)
    const unblocking       = ref(null)

    // Aprobar
    const approveTarget = ref(null)
    const approveFile   = ref(null)
    const duplicateInfo = ref(null)
    const approveForm   = ref({ receipt_number: "", bank_origin: "", payment_date: "", confirmed_amount: "", review_description: "" })
    const approveErr    = ref({})

    // Rechazar
    const rejectTarget  = ref(null)
    const rejectReason  = ref("")
    const rejectFile    = ref(null)
    const rejectErr     = ref("")
    const rejectForm    = ref({ review_description: "" })

    function addDays(dateStr, days) {
      const d = dateStr ? new Date(dateStr) : new Date()
      d.setDate(d.getDate() + days)
      return d.toLocaleDateString("es-CO", { day: "2-digit", month: "short", year: "numeric" })
    }
    function fmtDateShort(dateStr) {
      if (!dateStr) return new Date().toLocaleDateString("es-CO", { day: "2-digit", month: "short", year: "numeric" })
      return new Date(dateStr).toLocaleDateString("es-CO", { day: "2-digit", month: "short", year: "numeric" })
    }

    const planStartDate = computed(() => fmtDateShort(approveForm.value?.payment_date))
    const planEndDate   = computed(() => addDays(approveForm.value?.payment_date, 30))

    const statusLabel = { pending: "Pendiente", submitted: "Comprobante enviado", approved: "Aprobado", rejected: "Rechazado" }
    const typeLabel   = { activation: "Activación", upgrade: "Upgrade", renewal: "Renovación", downgrade: "Downgrade" }

    function formatCurrency(amount) {
      return new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(amount ?? 0)
    }
    function formatDate(dt) {
      if (!dt) return "—"
      return new Date(dt).toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" })
    }

    async function load() {
      loading.value = true
      try {
        const url = filterType.value ? `/payments/pending?payment_type=${filterType.value}` : "/payments/pending"
        payments.value = (await api.get(url)).data
      } catch { payments.value = [] }
      finally { loading.value = false }
    }

    function confirmApprove(p) {
      approveTarget.value = p
      approveFile.value   = null
      duplicateInfo.value = null
      approveErr.value    = {}
      approveForm.value   = {
        receipt_number:     "",
        bank_origin:        "",
        payment_date:       new Date().toISOString().split("T")[0],
        confirmed_amount:   p.amount ?? "",
        review_description: "",
      }
    }
    function closeApprove() {
      approveTarget.value = null
      duplicateInfo.value = null
      approveFile.value   = null
    }

    async function doApprove() {
      if (!approveTarget.value) return
      approveErr.value    = {}
      duplicateInfo.value = null

      // Validación frontend
      const errs = {}
      if (!approveForm.value.receipt_number.trim()) errs.receipt_number = "Requerido"
      if (!approveForm.value.bank_origin.trim())    errs.bank_origin    = "Requerido"
      if (!approveForm.value.payment_date)          errs.payment_date   = "Requerido"
      if (Object.keys(errs).length) { approveErr.value = errs; return }

      actioning.value = approveTarget.value.id
      const fd = new FormData()
      fd.append("receipt_number",     approveForm.value.receipt_number.trim())
      fd.append("bank_origin",        approveForm.value.bank_origin.trim())
      fd.append("payment_date",       approveForm.value.payment_date)
      if (approveForm.value.confirmed_amount) fd.append("confirmed_amount", approveForm.value.confirmed_amount)
      if (approveForm.value.review_description) fd.append("review_description", approveForm.value.review_description.trim())
      if (approveFile.value) fd.append("file", approveFile.value)

      try {
        await api.put(`/payments/${approveTarget.value.id}/approve`, fd, {
          headers: { "Content-Type": "multipart/form-data" },
        })
        closeApprove()
        await load()
      } catch (e) {
        const detail = e.response?.data?.detail
        if (e.response?.status === 409 && detail?.duplicate) {
          duplicateInfo.value = detail.duplicate
        } else {
          approveErr.value = { general: (typeof detail === "string" ? detail : detail?.message) || "Error al aprobar" }
        }
      } finally {
        actioning.value = null
      }
    }

    function openReject(p) {
      rejectTarget.value = p
      rejectReason.value = ""
      rejectFile.value   = null
      rejectErr.value    = ""
      rejectForm.value   = { review_description: "" }
    }
    function closeReject() {
      rejectTarget.value = null
      rejectReason.value = ""
      rejectFile.value   = null
      rejectErr.value    = ""
    }

    async function doReject() {
      if (!rejectTarget.value) return
      rejectErr.value = ""
      if (!rejectReason.value.trim()) { rejectErr.value = "El motivo es obligatorio"; return }

      actioning.value = rejectTarget.value.id
      const fd = new FormData()
      fd.append("reason", rejectReason.value.trim())
      if (rejectForm.value.review_description) fd.append("review_description", rejectForm.value.review_description.trim())
      if (rejectFile.value) fd.append("file", rejectFile.value)

      try {
        await api.put(`/payments/${rejectTarget.value.id}/reject`, fd, {
          headers: { "Content-Type": "multipart/form-data" },
        })
        closeReject()
        await load()
      } catch (e) {
        rejectErr.value = e.response?.data?.detail || "Error al rechazar"
      } finally {
        actioning.value = null
      }
    }

    // ── Empresas bloqueadas ──────────────────────────────────────
    async function loadBlocked() {
      loadingBlocked.value = true
      try {
        blockedCompanies.value = (await api.get("/payments/blocked-companies")).data
      } catch { blockedCompanies.value = [] }
      finally { loadingBlocked.value = false }
    }

    async function doUnblock(company) {
      const { isConfirmed, value: reason } = await window.Swal.fire({
        title: `¿Desbloquear "${company.company_name}"?`,
        html: `
          <p style="font-size:13px;color:#64748b;margin-bottom:12px">
            Se restablecerá el acceso y se cancelarán los pagos pendientes.<br>
            <strong>Esta acción queda registrada.</strong>
          </p>
          <input id="swal-reason" class="swal2-input" style="font-size:13px"
            placeholder="Nota interna (opcional)">
        `,
        icon: "warning",
        showCancelButton: true,
        confirmButtonText: "Sí, desbloquear",
        cancelButtonText: "Cancelar",
        confirmButtonColor: "#2563eb",
        preConfirm: () => document.getElementById("swal-reason")?.value?.trim() || ""
      })
      if (!isConfirmed) return

      unblocking.value = company.company_id
      try {
        await api.post(`/payments/unblock-company/${company.company_id}`, { reason: reason || "" })
        window.Swal.fire({
          icon: "success", title: "Empresa desbloqueada",
          text: `${company.company_name} ya puede acceder a la plataforma.`,
          timer: 2500, showConfirmButton: false,
        })
        await loadBlocked()
      } catch (e) {
        window.Swal.fire("Error", e.response?.data?.detail || "No se pudo desbloquear la empresa", "error")
      } finally {
        unblocking.value = null
      }
    }

    onMounted(load)

    return {
      BANKS_CO,
      loading, payments, actioning, filterType, apiBase,
      activeTab, blockedCompanies, loadingBlocked, unblocking,
      approveTarget, approveFile, duplicateInfo, approveForm, approveErr,
      rejectTarget, rejectReason, rejectFile, rejectErr, rejectForm,
      statusLabel, typeLabel, formatCurrency, formatDate,
      planStartDate, planEndDate,
      load, confirmApprove, closeApprove, doApprove,
      openReject, closeReject, doReject,
      loadBlocked, doUnblock,
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
  display: flex; align-items: flex-start; justify-content: center; z-index: 9999;
  padding: 12px; overflow-y: auto;
}
.pr-modal {
  background: #fff; border-radius: 14px; padding: 14px 16px;
  width: 100%; max-width: 500px;
  box-shadow: 0 20px 50px rgba(0,0,0,.3);
  margin: auto 0;
}
.modal-header-row {
  display: flex; align-items: center; gap: 8px; margin-bottom: 6px;
}
.modal-header-row h3 { margin: 0; text-align: left; font-size: .96rem; }
.modal-icon {
  width: 30px; height: 30px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: .95rem;
}
.modal-icon.green   { background: #f0fdf4; color: #10b981; }
.modal-icon.red     { background: #fef2f2; color: #ef4444; }
.modal-icon.upgrade { background: #eff6ff; color: #2563eb; }

.upgrade-modal-transition {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  margin: 0 auto 8px; padding: 6px 12px;
  background: linear-gradient(135deg, #eff6ff, #f0fdf4);
  border-radius: 8px; border: 1px solid #86efac;
}
.umt-from  { font-weight: 700; color: #64748b; background: #e2e8f0; padding: 4px 12px; border-radius: 20px; font-size: .88rem; }
.umt-arrow { color: #16a34a; font-size: 1.1rem; }
.umt-to    { font-weight: 800; color: #15803d; background: #dcfce7; padding: 4px 12px; border-radius: 20px; font-size: .88rem; }
.pr-modal-lg { max-width: 560px; }

.pr-modal h3 { font-size: .94rem; font-weight: 800; color: #0f172a; margin-bottom: 4px; }
.pr-modal p  { color: #64748b; font-size: .82rem; margin-bottom: 4px; }
.modal-company-info { font-size: .82rem; color: #475569; margin-bottom: 6px; }
.modal-btns  { display: flex; gap: 8px; margin-top: 10px; }
.modal-btns .btn-approve,
.modal-btns .btn-reject,
.modal-btns .btn-upgrade { flex: 1; justify-content: center; }
.btn-cancel {
  flex: 1; border: 1.5px solid #e2e8f0; background: #fff; color: #64748b;
  padding: 10px; border-radius: 8px; font-weight: 600; font-size: .88rem;
  cursor: pointer; transition: all .2s;
}
.btn-cancel:hover { border-color: #94a3b8; }

/* FORMULARIO DE EVIDENCIA */
.evidence-form {
  background: #f8fafc; border: 1px solid #e2e8f0;
  border-radius: 8px; padding: 8px 10px; margin-bottom: 8px;
}
.ev-title { font-size: .78rem; font-weight: 700; color: #475569; margin-bottom: 6px; }
.ev-row   { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }

.field-group { display: flex; flex-direction: column; gap: 3px; margin-bottom: 6px; }
.field-group:last-child { margin-bottom: 0; }
.field-group label { font-size: .74rem; font-weight: 600; color: #334155; }
.field-group label small { font-weight: 400; color: #94a3b8; }
.field-group.error label { color: #ef4444; }
.req { color: #ef4444; }
.field-group input,
.field-group select,
.field-group textarea {
  border: 1.5px solid #e2e8f0; border-radius: 6px;
  padding: 6px 10px; font-size: .82rem; resize: vertical;
  outline: none; color: #0f172a; font-family: inherit; background: #fff;
  width: 100%; box-sizing: border-box;
}
.field-group select { cursor: pointer; appearance: auto; }
.field-group input:focus,
.field-group select:focus,
.field-group textarea:focus { border-color: #2563eb; }
.field-group.error input,
.field-group.error select,
.field-group.error textarea { border-color: #ef4444; }
.field-error { color: #ef4444; font-size: .7rem; }

.ev-upload {
  border: 1.5px dashed #cbd5e1; border-radius: 8px; padding: 10px 14px;
  text-align: center; cursor: pointer; font-size: .82rem; color: #64748b;
  transition: all .2s; position: relative; background: #fff;
  display: flex; align-items: center; justify-content: center;
}
.ev-upload:hover   { border-color: #2563eb; color: #2563eb; }
.ev-upload.has-file { border-style: solid; border-color: #10b981; color: #059669; justify-content: flex-start; }
.ev-remove-file {
  margin-left: auto; background: none; border: none;
  color: #ef4444; cursor: pointer; font-size: .9rem; padding: 0 2px;
}

/* ALERTA DUPLICADO */
.duplicate-alert {
  display: flex; gap: 10px; align-items: flex-start;
  background: #fef2f2; border: 1.5px solid #fecaca;
  border-radius: 8px; padding: 12px 14px;
  color: #dc2626; font-size: .82rem; margin-bottom: 12px;
}
.duplicate-alert strong { display: block; margin-bottom: 4px; }
.duplicate-alert p  { margin: 2px 0; }
.duplicate-alert ul { margin: 4px 0; padding-left: 16px; }
.duplicate-alert li { margin: 2px 0; }

/* Error general */
.error-general {
  background: #fef2f2; border: 1px solid #fecaca;
  color: #dc2626; padding: 8px 12px; border-radius: 7px;
  font-size: .82rem; margin-bottom: 10px; text-align: center;
}

/* Fechas informativas en modal */
.modal-dates-info {
  display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: 4px;
  background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 7px;
  padding: 5px 10px; font-size: .76rem; color: #0369a1; margin-bottom: 6px;
}
.modal-dates-info strong { color: #0f172a; }
.dates-note { color: #64748b; font-size: .72rem; margin-left: 4px; }

/* Responsive: campos del formulario en columna en pantallas pequeñas */
@media (max-width: 540px) {
  .pr-modal { padding: 20px 16px; }
  .ev-row   { grid-template-columns: 1fr; }
}

.spin { animation: spin 1s linear infinite; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 600px) {
  .pr-info-row { flex-direction: column; gap: 2px; }
  .pr-info-label { min-width: auto; }
  .pr-actions { flex-direction: column; }
  .modal-btns { flex-direction: column; }
}

/* ══ TABS ══ */
.pr-tabs {
  display: flex; gap: 4px; margin-bottom: 20px;
  border-bottom: 2px solid #f1f5f9;
}
.pr-tab {
  display: flex; align-items: center; gap: 7px;
  padding: 10px 18px; border: none; background: none;
  font-size: .88rem; font-weight: 600; color: #94a3b8;
  cursor: pointer; border-bottom: 2px solid transparent;
  margin-bottom: -2px; transition: all .15s;
}
.pr-tab:hover  { color: #475569; }
.pr-tab.active { color: #2563eb; border-bottom-color: #2563eb; }
.pr-tab-badge {
  min-width: 20px; height: 20px; border-radius: 10px;
  background: #ef4444; color: #fff;
  font-size: 10px; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
  padding: 0 5px;
}
.pr-tab-badge-warn { background: #f59e0b; }

/* ══ EMPRESAS BLOQUEADAS ══ */
.bl-info-banner {
  display: flex; align-items: flex-start; gap: 8px;
  background: #fffbeb; border: 1px solid #fde68a;
  border-radius: 10px; padding: 12px 16px;
  font-size: .84rem; color: #92400e; margin-bottom: 16px;
  line-height: 1.5;
}

.bl-list { display: flex; flex-direction: column; gap: 12px; }

.bl-card {
  background: #fff; border: 1.5px solid #fde68a;
  border-radius: 14px; padding: 16px 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,.05);
  display: flex; align-items: flex-start;
  justify-content: space-between; gap: 16px; flex-wrap: wrap;
}

.bl-card-left  { display: flex; align-items: flex-start; gap: 14px; flex: 1; min-width: 0; }
.bl-lock-icon  {
  width: 40px; height: 40px; border-radius: 10px; flex-shrink: 0;
  background: #fef3c7; color: #d97706;
  display: flex; align-items: center; justify-content: center; font-size: 18px;
}
.bl-info            { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.bl-company-name    { font-size: 1rem; font-weight: 800; color: #0f172a; }
.bl-company-nit     { font-size: .8rem; color: #94a3b8; }
.bl-admin           { font-size: .8rem; color: #64748b; }
.bl-plan            { font-size: .8rem; color: #2563eb; }

.bl-card-right {
  display: flex; flex-direction: column; align-items: flex-end;
  gap: 8px; flex-shrink: 0;
}
.bl-status-wrap { display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }
.bl-status-badge {
  font-size: .75rem; font-weight: 700; padding: 3px 10px;
  border-radius: 20px; white-space: nowrap;
}
.bl-status-badge.pending_payment  { background: #fff7ed; color: #c2410c; }
.bl-status-badge.payment_submitted{ background: #dbeafe; color: #1e40af; }
.bl-status-badge.payment_rejected { background: #fef2f2; color: #b91c1c; }
.bl-status-badge.expired          { background: #f1f5f9; color: #475569; }
.bl-upgrade-badge {
  font-size: .75rem; font-weight: 700; padding: 3px 10px;
  border-radius: 20px; background: #f3e8ff; color: #7c3aed;
}
.bl-payment-info {
  display: flex; flex-direction: column; align-items: flex-end;
  gap: 2px; font-size: .78rem; color: #64748b;
}
.bl-pay-type   { color: #475569; font-weight: 600; }
.bl-pay-amount { color: #1e293b; font-weight: 700; font-size: .9rem; }
.bl-pay-date   { font-size: .73rem; color: #94a3b8; }

.bl-btn-unlock {
  display: flex; align-items: center; gap: 5px;
  padding: 8px 16px; border-radius: 8px;
  background: #2563eb; color: #fff;
  border: none; font-size: .84rem; font-weight: 700;
  cursor: pointer; transition: all .2s;
  white-space: nowrap;
}
.bl-btn-unlock:hover:not(:disabled) { background: #1d4ed8; }
.bl-btn-unlock:disabled { opacity: .5; cursor: not-allowed; }

@media (max-width: 640px) {
  .bl-card       { flex-direction: column; }
  .bl-card-right { align-items: flex-start; width: 100%; }
  .bl-btn-unlock { width: 100%; justify-content: center; }
}
</style>
