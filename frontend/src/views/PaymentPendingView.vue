<template>
  <div class="pp-page">
    <div class="pp-card">

      <!-- LOGO -->
      <div class="pp-brand">
        <span class="b-easy">Easy</span><span class="b-pos">Pos</span><span class="b-web">Web</span>
      </div>

      <!-- CARGANDO -->
      <div v-if="loading" class="pp-loading">
        <i class="bi bi-hourglass-split spin"></i> Verificando estado...
      </div>

      <!-- APROBADO (edge case: llegó aquí pero ya está activo) -->
      <div v-else-if="paymentStatus === 'active'" class="pp-approved">
        <div class="pp-icon green"><i class="bi bi-check-circle-fill"></i></div>
        <h2>¡Tu cuenta está activa!</h2>
        <p>Tu plan ya fue activado. Puedes ingresar al dashboard.</p>
        <button class="btn-primary" @click="goToDashboard">
          <i class="bi bi-rocket-takeoff-fill me-1"></i> Ir al Dashboard
        </button>
      </div>

      <!-- MODAL DE ESPERA (submitted o enviando) -->
      <div v-else-if="showWaitModal" class="pp-wait">
        <div class="pp-icon orange"><i class="bi bi-clock-history"></i></div>
        <h2>Comprobante enviado</h2>
        <p>Estamos revisando tu comprobante de pago para el plan
          <strong>{{ payment?.plan?.name }}</strong>.
          Te notificaremos por correo cuando sea procesado.</p>

        <!-- Razón de rechazo (si viene de rejected) -->
        <div v-if="payment?.payment?.rejection_reason" class="rejection-box">
          <i class="bi bi-exclamation-triangle-fill me-1"></i>
          <strong>Rechazo anterior:</strong> {{ payment.payment.rejection_reason }}
        </div>

        <div class="wait-actions">
          <button class="btn-back" @click="showWaitModal = false">
            <i class="bi bi-arrow-left me-1"></i> Modificar y reenviar
          </button>
          <button class="btn-outline" @click="refreshStatus" :disabled="refreshing">
            <i class="bi bi-arrow-clockwise me-1" :class="{ spin: refreshing }"></i>
            Actualizar estado
          </button>
          <button class="btn-primary btn-start" :disabled="paymentStatus !== 'active'" @click="goToDashboard">
            <i class="bi bi-rocket-takeoff-fill me-1"></i> Empezar
          </button>
        </div>

        <p class="wait-hint">
          <i class="bi bi-info-circle me-1"></i>
          El botón <strong>Empezar</strong> se habilitará cuando EasyPosWeb confirme tu pago.
        </p>
      </div>

      <!-- FORMULARIO PRINCIPAL -->
      <template v-else>
        <div class="pp-header">
          <div class="pp-icon" :class="paymentStatus === 'expired' ? 'red' : 'orange'">
            <i :class="paymentStatus === 'expired' ? 'bi bi-alarm' : 'bi bi-credit-card-2-front'"></i>
          </div>
          <h2 v-if="paymentStatus === 'expired'">
            Tu plan <strong>{{ payment?.plan?.name }}</strong> venció
          </h2>
          <h2 v-else>Activa tu plan <strong>{{ payment?.plan?.name }}</strong></h2>
          <p v-if="paymentStatus === 'expired'">
            Para continuar usando EasyPosWeb, renueva tu plan realizando el pago y subiendo el comprobante.
          </p>
          <p v-else>
            Realiza el pago por transferencia bancaria y sube tu comprobante para activar tu cuenta.
          </p>
        </div>

        <!-- Razón de rechazo si venía rechazado -->
        <div v-if="paymentStatus === 'payment_rejected' && payment?.payment?.rejection_reason"
             class="rejection-box">
          <i class="bi bi-exclamation-triangle-fill me-2"></i>
          <div>
            <strong>Tu comprobante anterior fue rechazado:</strong>
            <p class="mb-0">{{ payment.payment.rejection_reason }}</p>
          </div>
        </div>

        <!-- INSTRUCCIONES DE PAGO -->
        <div class="pay-instructions">
          <div class="instr-title">
            <i class="bi bi-bank me-2"></i> Datos para tu transferencia
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
                {{ formatCurrency(payment?.payment?.amount) }}
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
          <button class="btn-primary" :disabled="!selectedFile || submitting" @click="submitReceipt">
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
import { ref, computed, onMounted } from "vue"
import { useRouter } from "vue-router"
import api from "@/services/apis"

export default {
  name: "PaymentPendingView",

  setup() {
    const router      = useRouter()
    const loading     = ref(true)
    const refreshing  = ref(false)
    const submitting  = ref(false)
    const payment     = ref(null)
    const paymentStatus = ref("")
    const showWaitModal = ref(false)
    const selectedFile  = ref(null)
    const previewUrl    = ref("")
    const uploadError   = ref("")
    const isDrag        = ref(false)
    const fileInput     = ref(null)

    const isImage = computed(() =>
      selectedFile.value?.type?.startsWith("image/") ?? false
    )

    const referenceText = computed(() => {
      const user = JSON.parse(localStorage.getItem("user") || "{}")
      return `PLAN-${user.company_id ?? "0"}`
    })

    function formatCurrency(amount) {
      if (!amount && amount !== 0) return "—"
      return new Intl.NumberFormat("es-CO", {
        style: "currency", currency: "COP", maximumFractionDigits: 0,
      }).format(amount)
    }

    async function loadStatus() {
      try {
        const res = await api.get("/payments/my-status")
        payment.value = res.data
        paymentStatus.value = res.data.payment_status

        if (res.data.payment?.status === "submitted") {
          showWaitModal.value = true
        }
      } catch {
        paymentStatus.value = "pending_payment"
      } finally {
        loading.value = false
      }
    }

    async function refreshStatus() {
      refreshing.value = true
      try {
        const res = await api.get("/payments/my-status")
        payment.value = res.data
        paymentStatus.value = res.data.payment_status

        if (res.data.payment_status === "active") {
          showWaitModal.value = false
        }
      } catch {} finally {
        refreshing.value = false
      }
    }

    function onFileChange(e) {
      const file = e.target.files?.[0]
      setFile(file)
    }

    function onDrop(e) {
      isDrag.value = false
      const file = e.dataTransfer.files?.[0]
      setFile(file)
    }

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
      if (file.type.startsWith("image/")) {
        previewUrl.value = URL.createObjectURL(file)
      } else {
        previewUrl.value = "pdf"
      }
    }

    function clearFile() {
      selectedFile.value = null
      previewUrl.value   = ""
      if (fileInput.value) fileInput.value.value = ""
    }

    async function submitReceipt() {
      if (!selectedFile.value) return
      uploadError.value = ""
      submitting.value  = true

      const fd = new FormData()
      fd.append("file", selectedFile.value)

      try {
        await api.post("/payments/submit-receipt", fd, {
          headers: { "Content-Type": "multipart/form-data" },
        })
        await loadStatus()
        showWaitModal.value = true
      } catch (e) {
        uploadError.value = e.response?.data?.detail || "Error al enviar el comprobante."
      } finally {
        submitting.value = false
      }
    }

    function goToDashboard() {
      router.push("/dashboard")
    }

    function logout() {
      localStorage.removeItem("token")
      localStorage.removeItem("user")
      localStorage.removeItem("selected_company")
      router.push("/login")
    }

    function copy(text) {
      navigator.clipboard.writeText(text).catch(() => {})
    }

    onMounted(loadStatus)

    return {
      loading, refreshing, submitting, payment, paymentStatus,
      showWaitModal, selectedFile, previewUrl, uploadError,
      isDrag, fileInput, isImage, referenceText,
      formatCurrency, refreshStatus, onFileChange, onDrop,
      clearFile, submitReceipt, goToDashboard, logout, copy,
    }
  }
}
</script>

<style scoped>
.pp-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #1a3a6e 100%);
  display: flex; align-items: flex-start; justify-content: center;
  padding: 32px 16px;
  font-family: 'Segoe UI', system-ui, sans-serif;
}

.pp-card {
  background: #fff; border-radius: 20px; padding: 40px;
  width: 100%; max-width: 580px;
  box-shadow: 0 24px 60px rgba(0,0,0,.4);
}

/* LOGO */
.pp-brand { text-align: center; margin-bottom: 20px; font-size: 1.8rem; font-weight: 800; }
.b-easy { color: #2563eb; }
.b-pos  { color: #f97316; }
.b-web  { color: #10b981; }

/* ESTADOS ESPECIALES */
.pp-loading { text-align: center; padding: 40px; color: #64748b; font-size: 1rem; }
.pp-approved { text-align: center; padding: 20px 0; }
.pp-approved h2 { font-size: 1.4rem; font-weight: 800; color: #0f172a; margin: 12px 0 8px; }
.pp-approved p  { color: #64748b; margin-bottom: 20px; }

/* ÍCONO CIRCULAR */
.pp-icon {
  width: 72px; height: 72px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 2rem; margin: 0 auto 16px;
}
.pp-icon.orange { background: #fff7ed; color: #f97316; }
.pp-icon.green  { background: #f0fdf4; color: #10b981; }
.pp-icon.red    { background: #fef2f2; color: #ef4444; }

/* ENCABEZADO */
.pp-header { text-align: center; margin-bottom: 24px; }
.pp-header h2 { font-size: 1.2rem; font-weight: 700; color: #0f172a; margin-bottom: 6px; }
.pp-header p  { color: #64748b; font-size: .88rem; }

/* RECHAZO */
.rejection-box {
  display: flex; gap: 10px; align-items: flex-start;
  background: #fef2f2; border: 1px solid #fecaca;
  color: #dc2626; padding: 12px 14px; border-radius: 8px;
  font-size: .85rem; margin-bottom: 16px;
}
.rejection-box p { margin: 4px 0 0; color: #b91c1c; }

/* INSTRUCCIONES */
.pay-instructions {
  background: #f8fafc; border: 1px solid #e2e8f0;
  border-radius: 12px; padding: 16px; margin-bottom: 20px;
}
.instr-title {
  font-weight: 700; font-size: .9rem; color: #1e293b; margin-bottom: 12px;
}
.instr-grid { display: flex; flex-direction: column; gap: 8px; }
.instr-row {
  display: flex; justify-content: space-between; align-items: center;
  font-size: .85rem; gap: 8px;
}
.instr-row.highlight { background: #eff6ff; border-radius: 6px; padding: 6px 8px; }
.instr-label { color: #64748b; font-weight: 600; flex-shrink: 0; }
.instr-val { color: #0f172a; text-align: right; }
.instr-val.copyable { color: #2563eb; cursor: pointer; font-weight: 600; }
.instr-val.copyable:hover { text-decoration: underline; }
.instr-val.amount { font-size: 1.1rem; font-weight: 800; color: #2563eb; }
.instr-note { font-size: .75rem; color: #94a3b8; margin-top: 10px; margin-bottom: 0; }

/* UPLOAD */
.upload-section { margin-bottom: 20px; }
.upload-title { font-weight: 700; font-size: .9rem; color: #1e293b; margin-bottom: 10px; }
.drop-zone {
  border: 2px dashed #cbd5e1; border-radius: 12px; padding: 28px;
  text-align: center; cursor: pointer; transition: all .2s;
  color: #64748b; font-size: .88rem; position: relative;
  background: #f8fafc;
}
.drop-zone:hover, .drop-zone.dragover { border-color: #2563eb; background: #eff6ff; }
.drop-zone.has-file { border-style: solid; border-color: #10b981; background: #f0fdf4; }
.drop-zone p { margin: 4px 0; }
.preview-img { max-width: 100%; max-height: 200px; border-radius: 8px; }
.pdf-preview { display: flex; flex-direction: column; align-items: center; gap: 8px; color: #334155; }
.pdf-preview p { margin: 0; font-size: .85rem; font-weight: 600; }
.btn-remove-file {
  position: absolute; top: 8px; right: 8px;
  background: none; border: none; color: #ef4444;
  font-size: 1.2rem; cursor: pointer; line-height: 1;
}

/* MODAL ESPERA */
.pp-wait { text-align: center; }
.pp-wait h2 { font-size: 1.2rem; font-weight: 800; color: #0f172a; margin-bottom: 8px; }
.pp-wait p  { color: #64748b; font-size: .9rem; margin-bottom: 16px; }
.wait-actions {
  display: flex; flex-direction: column; gap: 10px; margin: 20px 0;
}
.wait-hint { font-size: .78rem; color: #94a3b8; }

/* BOTONES */
.btn-primary {
  background: #2563eb; color: #fff; border: none;
  padding: 12px 20px; border-radius: 10px; font-weight: 700; font-size: .92rem;
  cursor: pointer; transition: all .2s;
  display: flex; align-items: center; justify-content: center; gap: 6px; width: 100%;
}
.btn-primary:hover:not(:disabled) { background: #1d4ed8; }
.btn-primary:disabled { opacity: .5; cursor: not-allowed; }
.btn-start:not(:disabled) { background: #10b981; }
.btn-start:not(:disabled):hover { background: #059669; }

.btn-back {
  border: 1.5px solid #e2e8f0; background: #fff; color: #64748b;
  padding: 12px 20px; border-radius: 10px; font-weight: 600; font-size: .88rem;
  cursor: pointer; transition: all .2s;
  display: flex; align-items: center; justify-content: center; gap: 6px; width: 100%;
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
  .instr-row { flex-direction: column; align-items: flex-start; }
  .instr-val { text-align: left; }
  .pp-footer-btns { flex-direction: column; }
}
</style>
