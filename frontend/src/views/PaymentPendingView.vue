<template>
  <div class="pp-page">
    <div class="pp-card">

      <!-- LOGO + TÍTULO en fila -->
      <div class="pp-top-row">
        <div class="pp-brand">
          <span class="b-easy">Easy</span><span class="b-pos">Pos</span><span class="b-web">Web</span>
        </div>
        <div class="pp-top-divider"></div>
        <div class="pp-top-tagline">Portal de pagos</div>
      </div>

      <!-- CARGANDO -->
      <div v-if="loading" class="pp-loading">
        <i class="bi bi-hourglass-split spin"></i> Verificando estado...
      </div>

      <!-- ACTIVO (edge case) -->
      <div v-else-if="paymentStatus === 'active'" class="pp-state-block">
        <div class="pp-icon green"><i class="bi bi-check-circle-fill"></i></div>
        <h2>¡Tu cuenta está activa!</h2>
        <p>Tu plan ya fue activado. Puedes ingresar al dashboard.</p>
        <button class="btn-primary" @click="goToDashboard">
          <i class="bi bi-rocket-takeoff-fill me-1"></i> Ir al Dashboard
        </button>
      </div>

      <!-- PANTALLA DE ESPERA (comprobante enviado) -->
      <div v-else-if="showWaitScreen" class="pp-wait">
        <div v-if="paymentStatus === 'active'" class="pp-activated">
          <div class="pp-icon green"><i class="bi bi-check-circle-fill"></i></div>
          <h2>¡Pago aprobado!</h2>
          <p>Tu plan ha sido activado. Ya puedes ingresar.</p>
          <button class="btn-activated" @click="goToDashboard">
            <i class="bi bi-rocket-takeoff-fill me-1"></i> Activado — Ingresar
          </button>
        </div>

        <div v-else>
          <div class="pp-icon orange"><i class="bi bi-clock-history"></i></div>
          <h2>Comprobante enviado</h2>
          <p>
            Estamos revisando tu comprobante para el plan
            <strong>{{ waitPlanName }}</strong>.
            Te notificaremos por correo cuando sea procesado.
          </p>

          <div class="wait-status-row">
            <span class="wait-dot pulsing"></span>
            <span class="wait-label">En revisión por el equipo EasyPosWeb…</span>
          </div>

          <div class="wait-actions">
            <button class="btn-back" @click="showWaitScreen = false">
              <i class="bi bi-arrow-left me-1"></i> Modificar y reenviar
            </button>
            <button class="btn-outline" @click="refreshStatus" :disabled="refreshing">
              <i class="bi bi-arrow-clockwise me-1" :class="{ spin: refreshing }"></i>
              Verificar estado
            </button>
          </div>

          <p class="wait-hint">
            <i class="bi bi-info-circle me-1"></i>
            El botón <strong>Activado</strong> aparecerá aquí cuando EasyPosWeb confirme tu pago.
          </p>
        </div>
      </div>

      <!-- FORMULARIO PRINCIPAL -->
      <template v-else>

        <!-- Encabezado -->
        <div class="pp-header">
          <div class="pp-icon" :class="paymentStatus === 'expired' ? 'red' : 'orange'">
            <i :class="paymentStatus === 'expired' ? 'bi bi-alarm' : 'bi bi-credit-card-2-front'"></i>
          </div>
          <h2 v-if="paymentStatus === 'expired'">Tu plan venció</h2>
          <h2 v-else>Activa tu plan</h2>
          <p>Selecciona el plan a renovar, sube tu comprobante y lo activamos en minutos. Este proceso puede durar entre una y dos horas; por favor espera a que se active tu plataforma. Gracias por tu comprensión.</p>
        </div>

        <!-- Rechazo previo con evidencia -->
        <div v-if="paymentStatus === 'payment_rejected' && rejectionReason" class="rejection-box">
          <i class="bi bi-exclamation-triangle-fill me-2 flex-shrink-0"></i>
          <div class="rejection-body">
            <strong>Tu comprobante fue rechazado</strong>
            <p class="rejection-reason">{{ rejectionReason }}</p>
            <p v-if="rejectionDetail" class="rejection-detail">{{ rejectionDetail }}</p>
            <a v-if="rejectionEvidenceUrl"
               :href="apiBase + rejectionEvidenceUrl"
               target="_blank" class="rejection-evidence-link">
              <i class="bi bi-paperclip me-1"></i>Ver evidencia adjunta
            </a>
          </div>
        </div>

        <!-- SELECTOR DE PLANES -->
        <div class="plan-section">
          <div class="plan-section-title">
            <i class="bi bi-grid-1x2 me-2"></i>Selecciona tu plan
          </div>
          <div v-if="loadingPlans" class="plans-loading">
            <i class="bi bi-hourglass-split spin me-1"></i> Cargando planes...
          </div>
          <div v-else class="plans-grid">
            <div
              v-for="plan in plans"
              :key="plan.id"
              class="plan-card"
              :class="{
                selected: selectedPlanId === plan.id,
                current: plan.is_current,
              }"
              @click="selectedPlanId = plan.id"
            >
              <div class="plan-card-top">
                <span class="plan-name">{{ plan.name }}</span>
                <span v-if="plan.is_current" class="plan-badge current-badge">Actual</span>
                <span v-else class="plan-badge upgrade-badge">Upgrade</span>
              </div>
              <div class="plan-price">
                {{ formatCurrency(plan.price, plan.currency) }}
                <span class="plan-period">/año</span>
              </div>
              <div class="plan-users">
                <i class="bi bi-people me-1"></i>
                {{ plan.max_users === -1 ? 'Usuarios ilimitados' : `${plan.max_users} usuario${plan.max_users > 1 ? 's' : ''}` }}
              </div>
              <div class="plan-check" :class="{ visible: selectedPlanId === plan.id }">
                <i class="bi bi-check-circle-fill"></i>
              </div>
            </div>
          </div>
        </div>

        <!-- INSTRUCCIONES DE PAGO -->
        <div class="pay-instructions">
          <div class="instr-title">
            <i class="bi bi-bank me-2"></i>Datos para tu transferencia
          </div>
          <div class="instr-grid">
            <div class="instr-row">
              <span class="instr-label">Banco:</span>
              <span class="instr-val">Bancolombia</span>
            </div>
            <div class="instr-row">
              <span class="instr-label">Tipo:</span>
              <span class="instr-val">Cuenta de Ahorros</span>
            </div>
            <div class="instr-row">
              <span class="instr-label">N° Cuenta:</span>
              <span class="instr-val copyable" @click="copy('123-456789-12')">
                123-456789-12 <i class="bi bi-copy ms-1"></i>
              </span>
            </div>
            <div class="instr-row">
              <span class="instr-label">A nombre de:</span>
              <span class="instr-val">EasyPosWeb SAS</span>
            </div>
            <div class="instr-row">
              <span class="instr-label">NIT:</span>
              <span class="instr-val copyable" @click="copy('900.123.456-7')">
                900.123.456-7 <i class="bi bi-copy ms-1"></i>
              </span>
            </div>
            <div class="instr-row highlight">
              <span class="instr-label">Valor a pagar:</span>
              <span class="instr-val amount">
                {{ selectedPlan ? formatCurrency(selectedPlan.price, selectedPlan.currency) : '—' }}
              </span>
            </div>
            <div class="instr-row">
              <span class="instr-label">Concepto:</span>
              <span class="instr-val copyable" @click="copy(referenceText)">
                {{ referenceText }} <i class="bi bi-copy ms-1"></i>
              </span>
            </div>
          </div>
          <p class="instr-note">
            <i class="bi bi-info-circle me-1"></i>
            Escribe el concepto exacto en tu transferencia para que podamos identificar tu pago.
          </p>
        </div>

        <!-- SUBIR COMPROBANTE -->
        <div class="upload-section">
          <div class="upload-title"><i class="bi bi-upload me-2"></i>Sube tu comprobante</div>
          <div
            class="drop-zone"
            :class="{ dragover: isDrag, 'has-file': previewUrl }"
            @dragover.prevent="isDrag = true"
            @dragleave="isDrag = false"
            @drop.prevent="onDrop"
            @click="$refs.fileInput.click()"
          >
            <template v-if="!previewUrl">
              <i class="bi bi-cloud-upload fs-2 mb-2"></i>
              <p>Arrastra tu comprobante aquí o <strong>haz clic para seleccionar</strong></p>
              <small>JPG, PNG, WEBP o PDF — máx. 5 MB</small>
            </template>
            <template v-else>
              <img v-if="isImage" :src="previewUrl" class="preview-img" alt="Comprobante" />
              <div v-else class="pdf-preview">
                <i class="bi bi-file-earmark-pdf fs-1 text-danger"></i>
                <p>{{ selectedFile?.name }}</p>
              </div>
              <button type="button" class="btn-remove-file" @click.stop="clearFile">
                <i class="bi bi-x-circle-fill"></i>
              </button>
            </template>
          </div>
          <input ref="fileInput" type="file"
                 accept="image/jpeg,image/png,image/webp,application/pdf"
                 style="display:none" @change="onFileChange" />
          <div v-if="uploadError" class="api-error mt-2">
            <i class="bi bi-exclamation-circle-fill me-2"></i>{{ uploadError }}
          </div>
        </div>

        <!-- BOTONES -->
        <div class="pp-footer-btns">
          <button class="btn-logout" @click="logout">
            <i class="bi bi-box-arrow-right me-1"></i> Salir
          </button>
          <button class="btn-primary" :disabled="!selectedFile || !selectedPlanId || submitting" @click="submitReceipt">
            <span v-if="submitting">
              <i class="bi bi-hourglass-split me-1 spin"></i> Enviando...
            </span>
            <span v-else>
              <i class="bi bi-send-fill me-1"></i> Enviar comprobante
            </span>
          </button>
        </div>

      </template>

    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from "vue"
import { useRouter } from "vue-router"
import api from "@/services/apis"

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000"

export default {
  name: "PaymentPendingView",

  setup() {
    const router        = useRouter()
    const loading       = ref(true)
    const loadingPlans  = ref(true)
    const refreshing    = ref(false)
    const submitting    = ref(false)
    const paymentStatus = ref("")
    const rejectionReason     = ref("")
    const rejectionDetail     = ref("")
    const rejectionEvidenceUrl = ref("")
    const apiBase             = API_BASE
    const showWaitScreen  = ref(false)
    const waitPlanName    = ref("")
    const plans         = ref([])
    const selectedPlanId = ref(null)
    const selectedFile  = ref(null)
    const previewUrl    = ref("")
    const uploadError   = ref("")
    const isDrag        = ref(false)
    const fileInput     = ref(null)
    let pollTimer       = null

    const isImage = computed(() => selectedFile.value?.type?.startsWith("image/") ?? false)
    const selectedPlan = computed(() => plans.value.find(p => p.id === selectedPlanId.value) ?? null)

    const referenceText = computed(() => {
      const user = JSON.parse(localStorage.getItem("user") || "{}")
      return `PLAN-${user.company_id ?? "0"}`
    })

    function formatCurrency(amount, currency = "COP") {
      if (!amount && amount !== 0) return "—"
      return new Intl.NumberFormat("es-CO", {
        style: "currency", currency: currency || "COP", maximumFractionDigits: 0,
      }).format(amount)
    }

    async function loadStatus() {
      try {
        const res = await api.get("/payments/my-status")
        paymentStatus.value        = res.data.payment_status
        rejectionReason.value      = res.data.payment?.rejection_reason      ?? ""
        rejectionDetail.value      = res.data.payment?.review_description    ?? ""
        rejectionEvidenceUrl.value = res.data.payment?.review_evidence_url   ?? ""
        if (res.data.payment?.status === "submitted") {
          waitPlanName.value  = res.data.plan?.name ?? ""
          showWaitScreen.value = true
        }
      } catch {
        paymentStatus.value = "pending_payment"
      } finally {
        loading.value = false
      }
    }

    async function loadPlans() {
      loadingPlans.value = true
      try {
        const user = JSON.parse(localStorage.getItem("user") || "{}")
        const currency = user.currency_code ?? "COP"
        const res = await api.get(`/payments/available-plans?currency=${currency}`)
        plans.value = res.data
        const current = res.data.find(p => p.is_current)
        selectedPlanId.value = current?.id ?? res.data[0]?.id ?? null
      } catch {
        plans.value = []
      } finally {
        loadingPlans.value = false
      }
    }

    async function refreshStatus() {
      refreshing.value = true
      try {
        const res = await api.get("/payments/my-status")
        paymentStatus.value = res.data.payment_status
        if (res.data.payment_status === "active") {
          stopPolling()
        }
      } catch {} finally {
        refreshing.value = false
      }
    }

    function startPolling() {
      stopPolling()
      pollTimer = setInterval(async () => {
        try {
          const res = await api.get("/payments/my-status")
          paymentStatus.value = res.data.payment_status
          if (res.data.payment_status === "active") {
            stopPolling()
          }
        } catch {}
      }, 10000)
    }

    function stopPolling() {
      if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
    }

    function onFileChange(e) { setFile(e.target.files?.[0]) }
    function onDrop(e)       { isDrag.value = false; setFile(e.dataTransfer.files?.[0]) }

    function setFile(file) {
      uploadError.value = ""
      if (!file) return
      const allowed = ["image/jpeg", "image/png", "image/webp", "application/pdf"]
      if (!allowed.includes(file.type)) {
        uploadError.value = "Tipo no permitido. Usa JPG, PNG, WEBP o PDF."
        return
      }
      if (file.size > 5 * 1024 * 1024) {
        uploadError.value = "El archivo supera el límite de 5 MB."
        return
      }
      selectedFile.value = file
      previewUrl.value   = file.type.startsWith("image/") ? URL.createObjectURL(file) : "pdf"
    }

    function clearFile() {
      selectedFile.value = null
      previewUrl.value   = ""
      if (fileInput.value) fileInput.value.value = ""
    }

    async function submitReceipt() {
      if (!selectedFile.value || !selectedPlanId.value) return
      uploadError.value = ""
      submitting.value  = true

      try {
        // Paso 1: crear/actualizar el registro de pago con el plan seleccionado
        const user = JSON.parse(localStorage.getItem("user") || "{}")
        await api.post("/payments/request-renewal", {
          plan_id:       selectedPlanId.value,
          currency_code: user.currency_code ?? "COP",
        })

        // Paso 2: subir el comprobante
        const fd = new FormData()
        fd.append("file", selectedFile.value)
        await api.post("/payments/submit-receipt", fd, {
          headers: { "Content-Type": "multipart/form-data" },
        })

        waitPlanName.value   = selectedPlan.value?.name ?? ""
        showWaitScreen.value = true
        await loadStatus()
        startPolling()
      } catch (e) {
        uploadError.value = e.response?.data?.detail || "Error al enviar el comprobante."
      } finally {
        submitting.value = false
      }
    }

    function goToDashboard() { router.push("/dashboard") }

    function logout() {
      localStorage.removeItem("token")
      localStorage.removeItem("user")
      localStorage.removeItem("selected_company")
      router.push("/login")
    }

    function copy(text) { navigator.clipboard.writeText(text).catch(() => {}) }

    onMounted(() => { loadStatus(); loadPlans() })
    onUnmounted(stopPolling)

    return {
      loading, loadingPlans, refreshing, submitting,
      paymentStatus, rejectionReason, rejectionDetail, rejectionEvidenceUrl, apiBase,
      showWaitScreen, waitPlanName,
      plans, selectedPlanId, selectedPlan,
      selectedFile, previewUrl, uploadError, isDrag, fileInput, isImage,
      referenceText, formatCurrency, refreshStatus,
      onFileChange, onDrop, clearFile, submitReceipt,
      goToDashboard, logout, copy,
    }
  }
}
</script>

<style scoped>
.pp-page {
  height: 100%;
  overflow-y: auto;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #1a3a6e 100%);
  display: flex; align-items: flex-start; justify-content: center;
  padding: 32px 16px;
  font-family: 'Segoe UI', system-ui, sans-serif;
}

.pp-card {
  background: #fff; border-radius: 20px; padding: 40px;
  width: 100%; max-width: 600px;
  box-shadow: 0 24px 60px rgba(0,0,0,.4);
}

/* LOGO + TÍTULO EN FILA */
.pp-top-row {
  display: flex; align-items: center; gap: 12px;
  margin-bottom: 18px;
}
.pp-brand { font-size: 1.5rem; font-weight: 800; flex-shrink: 0; }
.b-easy { color: #2563eb; }
.b-pos  { color: #f97316; }
.b-web  { color: #10b981; }
.pp-top-divider { width: 1px; height: 24px; background: #e2e8f0; flex-shrink: 0; }
.pp-top-tagline { font-size: .78rem; font-weight: 600; color: #94a3b8; letter-spacing: .5px; text-transform: uppercase; }

/* ESTADOS */
.pp-loading, .pp-state-block { text-align: center; padding: 40px 0; }
.pp-state-block h2 { font-size: 1.4rem; font-weight: 800; color: #0f172a; margin: 12px 0 8px; }
.pp-state-block p  { color: #64748b; margin-bottom: 20px; }

.pp-icon {
  width: 72px; height: 72px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 2rem; margin: 0 auto 16px;
}
.pp-icon.orange { background: #fff7ed; color: #f97316; }
.pp-icon.green  { background: #f0fdf4; color: #10b981; }
.pp-icon.red    { background: #fef2f2; color: #ef4444; }

/* ENCABEZADO FORMULARIO */
.pp-header { text-align: center; margin-bottom: 20px; }
.pp-header h2 { font-size: 1.2rem; font-weight: 700; color: #0f172a; margin-bottom: 6px; }
.pp-header p  { color: #64748b; font-size: .88rem; }

/* RECHAZO */
.rejection-box {
  display: flex; gap: 10px; align-items: flex-start;
  background: #fef2f2; border: 1px solid #fecaca;
  color: #dc2626; padding: 12px 14px; border-radius: 8px;
  font-size: .85rem; margin-bottom: 16px;
}
.rejection-body { display: flex; flex-direction: column; gap: 4px; }
.rejection-reason { margin: 2px 0 0; color: #b91c1c; font-weight: 600; }
.rejection-detail { margin: 0; color: #7f1d1d; font-size: .8rem; }
.rejection-evidence-link {
  display: inline-flex; align-items: center; gap: 4px;
  color: #dc2626; font-size: .78rem; text-decoration: underline; margin-top: 2px;
}
.rejection-evidence-link:hover { color: #991b1b; }

/* SELECTOR DE PLANES */
.plan-section { margin-bottom: 20px; }
.plan-section-title {
  font-weight: 700; font-size: .9rem; color: #1e293b; margin-bottom: 12px;
}
.plans-loading { color: #64748b; font-size: .85rem; padding: 8px 0; }
.plans-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px;
}
.plan-card {
  border: 2px solid #e2e8f0; border-radius: 12px; padding: 14px 12px;
  cursor: pointer; transition: all .2s; position: relative;
  background: #f8fafc;
}
.plan-card:hover  { border-color: #93c5fd; background: #eff6ff; }
.plan-card.selected { border-color: #2563eb; background: #eff6ff; box-shadow: 0 0 0 3px rgba(37,99,235,.15); }
.plan-card.current.selected { border-color: #2563eb; }

.plan-card-top { display: flex; align-items: center; justify-content: space-between; gap: 4px; margin-bottom: 6px; }
.plan-name { font-weight: 700; font-size: .9rem; color: #0f172a; }
.plan-badge {
  font-size: .65rem; font-weight: 700; padding: 2px 6px; border-radius: 20px;
  white-space: nowrap;
}
.current-badge  { background: #dcfce7; color: #15803d; }
.upgrade-badge  { background: #fef9c3; color: #92400e; }

.plan-price { font-size: 1rem; font-weight: 800; color: #2563eb; margin-bottom: 4px; }
.plan-period { font-size: .7rem; font-weight: 400; color: #94a3b8; }
.plan-users  { font-size: .75rem; color: #64748b; }

.plan-check {
  position: absolute; top: 8px; right: 8px;
  color: #2563eb; font-size: 1rem; opacity: 0; transition: opacity .15s;
}
.plan-check.visible { opacity: 1; }

/* INSTRUCCIONES */
.pay-instructions {
  background: #f8fafc; border: 1px solid #e2e8f0;
  border-radius: 12px; padding: 16px; margin-bottom: 20px;
}
.instr-title { font-weight: 700; font-size: .9rem; color: #1e293b; margin-bottom: 12px; }
.instr-grid  { display: flex; flex-direction: column; gap: 8px; }
.instr-row   { display: flex; justify-content: space-between; align-items: center; font-size: .85rem; gap: 8px; }
.instr-row.highlight { background: #eff6ff; border-radius: 6px; padding: 6px 8px; }
.instr-label { color: #64748b; font-weight: 600; flex-shrink: 0; }
.instr-val   { color: #0f172a; text-align: right; }
.instr-val.copyable { color: #2563eb; cursor: pointer; font-weight: 600; }
.instr-val.copyable:hover { text-decoration: underline; }
.instr-val.amount { font-size: 1.1rem; font-weight: 800; color: #2563eb; }
.instr-note  { font-size: .75rem; color: #94a3b8; margin-top: 10px; margin-bottom: 0; }

/* UPLOAD */
.upload-section { margin-bottom: 20px; }
.upload-title { font-weight: 700; font-size: .9rem; color: #1e293b; margin-bottom: 10px; }
.drop-zone {
  border: 2px dashed #cbd5e1; border-radius: 12px; padding: 28px;
  text-align: center; cursor: pointer; transition: all .2s;
  color: #64748b; font-size: .88rem; position: relative; background: #f8fafc;
}
.drop-zone:hover, .drop-zone.dragover { border-color: #2563eb; background: #eff6ff; }
.drop-zone.has-file { border-style: solid; border-color: #10b981; background: #f0fdf4; }
.drop-zone p { margin: 4px 0; }
.preview-img { max-width: 100%; max-height: 200px; border-radius: 8px; }
.pdf-preview { display: flex; flex-direction: column; align-items: center; gap: 8px; color: #334155; }
.pdf-preview p { margin: 0; font-size: .85rem; font-weight: 600; }
.btn-remove-file {
  position: absolute; top: 8px; right: 8px;
  background: none; border: none; color: #ef4444; font-size: 1.2rem; cursor: pointer;
}

/* PANTALLA DE ESPERA */
.pp-wait { text-align: center; padding: 10px 0; }
.pp-wait h2 { font-size: 1.2rem; font-weight: 800; color: #0f172a; margin-bottom: 8px; }
.pp-wait p  { color: #64748b; font-size: .9rem; margin-bottom: 16px; }

.wait-status-row {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  margin: 16px 0; font-size: .85rem; color: #64748b;
}
.wait-dot {
  width: 10px; height: 10px; border-radius: 50%; background: #f97316; flex-shrink: 0;
}
.wait-dot.pulsing { animation: pulse-dot 1.5s ease-in-out infinite; }
@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: .4; transform: scale(.7); }
}

.wait-actions { display: flex; flex-direction: column; gap: 10px; margin: 20px 0; }
.wait-hint { font-size: .78rem; color: #94a3b8; }

/* Activado */
.pp-activated { text-align: center; }
.pp-activated h2 { font-size: 1.3rem; font-weight: 800; color: #15803d; margin-bottom: 8px; }
.pp-activated p  { color: #64748b; margin-bottom: 20px; }
.btn-activated {
  background: linear-gradient(135deg, #10b981, #059669);
  color: #fff; border: none; padding: 14px 28px; border-radius: 12px;
  font-weight: 800; font-size: 1rem; cursor: pointer; transition: all .2s;
  display: inline-flex; align-items: center; gap: 8px;
  box-shadow: 0 4px 15px rgba(16,185,129,.4);
  animation: glow-green 2s ease-in-out infinite;
}
.btn-activated:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(16,185,129,.5); }
@keyframes glow-green {
  0%, 100% { box-shadow: 0 4px 15px rgba(16,185,129,.4); }
  50%       { box-shadow: 0 4px 25px rgba(16,185,129,.7); }
}

/* BOTONES */
.btn-primary {
  background: #2563eb; color: #fff; border: none;
  padding: 12px 20px; border-radius: 10px; font-weight: 700; font-size: .92rem;
  cursor: pointer; transition: all .2s;
  display: flex; align-items: center; justify-content: center; gap: 6px; width: 100%;
}
.btn-primary:hover:not(:disabled) { background: #1d4ed8; }
.btn-primary:disabled { opacity: .5; cursor: not-allowed; }

.btn-back {
  border: 1.5px solid #e2e8f0; background: #fff; color: #64748b;
  padding: 12px 20px; border-radius: 10px; font-weight: 600; font-size: .88rem;
  cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px; width: 100%;
}
.btn-back:hover { border-color: #94a3b8; color: #334155; }

.btn-outline {
  border: 1.5px solid #2563eb; background: #fff; color: #2563eb;
  padding: 12px 20px; border-radius: 10px; font-weight: 600; font-size: .88rem;
  cursor: pointer; transition: all .2s; width: 100%;
  display: flex; align-items: center; justify-content: center; gap: 6px;
}
.btn-outline:disabled { opacity: .5; cursor: not-allowed; }

.btn-logout {
  border: 1.5px solid #e2e8f0; background: #fff; color: #94a3b8;
  padding: 12px 20px; border-radius: 10px; font-weight: 600; font-size: .88rem;
  cursor: pointer; transition: all .2s;
  display: flex; align-items: center; justify-content: center; gap: 6px;
}
.btn-logout:hover { border-color: #ef4444; color: #ef4444; }

.pp-footer-btns { display: flex; gap: 10px; margin-top: 8px; }
.pp-footer-btns .btn-primary { flex: 1; }

.api-error {
  background: #fef2f2; border: 1px solid #fecaca;
  color: #dc2626; padding: 10px 14px; border-radius: 8px; font-size: .85rem;
}

.spin { animation: spin 1s linear infinite; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 480px) {
  .pp-card { padding: 24px 16px; }
  .plans-grid { grid-template-columns: 1fr 1fr; }
  .instr-row { flex-direction: column; align-items: flex-start; }
  .instr-val { text-align: left; }
  .pp-footer-btns { flex-direction: column; }
}

</style>
