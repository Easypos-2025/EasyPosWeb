<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-box">

      <!-- CABECERA -->
      <div class="modal-head">
        <div class="modal-icon warn"><i class="bi bi-arrow-down-circle-fill"></i></div>
        <div>
          <h2>Cambiar a plan inferior</h2>
          <p>Plan actual: <strong>{{ currentPlanName }}</strong>.
             Elige el plan al que deseas cambiar.</p>
        </div>
        <button class="btn-close-x" @click="$emit('close')">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>

      <!-- PASO 1: Elegir plan + cláusula legal -->
      <template v-if="step === 1">

        <div class="legal-box">
          <div class="legal-title"><i class="bi bi-shield-exclamation me-2"></i>Aviso importante</div>
          <p>Al cambiar a un plan inferior, las funcionalidades que superen los límites del nuevo plan
             quedarán <strong>inaccesibles pero no se eliminarán</strong>. Si en el futuro actualizas
             tu plan, volverán a estar disponibles.</p>
          <p>Esta acción quedará registrada con fecha y hora como parte de tu historial de cuenta.</p>
          <p class="legal-clause">
            Conforme a los <a href="/clausulas-legales" target="_blank">Términos y Condiciones de EasyPosWeb</a>,
            el cambio de plan es responsabilidad exclusiva del titular de la cuenta y no genera derecho
            a reembolso proporcional del período ya pagado.
          </p>
        </div>

        <div class="currency-row">
          <i class="bi bi-currency-exchange"></i>
          <label>Moneda:</label>
          <select v-model="currency" class="currency-select" @change="loadDowngrades">
            <option v-for="code in SUPPORTED_CURRENCIES" :key="code" :value="code">
              {{ code }} — {{ CURRENCY_NAMES[code] }}
            </option>
          </select>
        </div>

        <div v-if="loading" class="up-loading">
          <i class="bi bi-hourglass-split spin"></i> Cargando planes...
        </div>
        <div v-else-if="!downgrades.length" class="up-empty">
          No hay planes inferiores disponibles.
        </div>
        <div v-else class="down-grid">
          <button
            v-for="p in downgrades" :key="p.id"
            class="down-card"
            :class="{ selected: selectedPlanId === p.id, free: p.is_free }"
            @click="selectedPlanId = p.id"
          >
            <div class="down-badge" v-if="p.is_free">GRATIS</div>
            <div class="down-name">{{ p.name }}</div>
            <div class="down-price">
              <span v-if="p.is_free" class="price-free">Sin costo</span>
              <span v-else class="price-paid">{{ formatMoney(p.price, currency) }}<small>/año</small></span>
            </div>
          </button>
        </div>

        <!-- Checkbox de aceptación + firma -->
        <div v-if="selectedPlanId" class="accept-section">
          <label class="accept-check">
            <input type="checkbox" v-model="legalAccepted" />
            <span>Entiendo y acepto las condiciones. Las funcionalidades adicionales quedarán
                  inaccesibles al cambiar de plan.</span>
          </label>

          <div v-if="legalAccepted" class="confirm-name-wrap">
            <label class="confirm-name-label">
              Para confirmar, escribe el nombre de tu empresa:
            </label>
            <input v-model="confirmName" type="text" class="confirm-name-input"
                   :placeholder="companyName" />
            <p v-if="nameErr" class="field-error">{{ nameErr }}</p>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn-cancel" @click="$emit('close')">Cancelar</button>
          <button class="btn-warn"
                  :disabled="!selectedPlanId || !legalAccepted || submitting"
                  @click="proceed">
            <span v-if="submitting">
              <i class="bi bi-hourglass-split spin me-1"></i>Procesando...
            </span>
            <span v-else>Confirmar cambio de plan</span>
          </button>
        </div>
      </template>

      <!-- PASO 2: Pago requerido (si el plan inferior es de pago) -->
      <template v-else-if="step === 2">
        <div class="pay-summary">
          <div class="pay-summary-row">
            <span>Nuevo plan:</span><strong>{{ selectedPlan?.name }}</strong>
          </div>
          <div class="pay-summary-row highlight">
            <span>Valor a pagar:</span>
            <strong class="price-big">{{ formatMoney(selectedPlan?.price ?? 0, currency) }}</strong>
          </div>
        </div>

        <div class="pay-instructions">
          <div class="instr-title"><i class="bi bi-bank me-2"></i>Datos para tu transferencia</div>
          <div class="instr-grid">
            <div class="instr-row"><span class="instr-label">Banco:</span><span>Bancolombia</span></div>
            <div class="instr-row"><span class="instr-label">Tipo:</span><span>Cuenta de Ahorros</span></div>
            <div class="instr-row">
              <span class="instr-label">N° Cuenta:</span>
              <span class="copyable" @click="copy('123-456789-12')">123-456789-12 <i class="bi bi-copy"></i></span>
            </div>
            <div class="instr-row">
              <span class="instr-label">Concepto:</span>
              <span class="copyable" @click="copy(refText)">{{ refText }} <i class="bi bi-copy"></i></span>
            </div>
          </div>
        </div>

        <div class="upload-section">
          <div class="upload-title"><i class="bi bi-upload me-2"></i>Sube tu comprobante</div>
          <div class="drop-zone"
               :class="{ dragover: isDrag, 'has-file': previewUrl }"
               @dragover.prevent="isDrag = true"
               @dragleave="isDrag = false"
               @drop.prevent="onDrop"
               @click="$refs.fileInput.click()">
            <template v-if="!previewUrl">
              <i class="bi bi-cloud-upload fs-2 mb-1"></i>
              <p>Arrastra o <strong>haz clic</strong> para seleccionar</p>
              <small>JPG, PNG, WEBP o PDF — máx. 5 MB</small>
            </template>
            <template v-else>
              <img v-if="isImage" :src="previewUrl" class="preview-img" />
              <div v-else class="pdf-preview">
                <i class="bi bi-file-earmark-pdf fs-1 text-danger"></i>
                <p>{{ selectedFile?.name }}</p>
              </div>
              <button type="button" class="btn-remove" @click.stop="clearFile">
                <i class="bi bi-x-circle-fill"></i>
              </button>
            </template>
          </div>
          <input ref="fileInput" type="file"
                 accept="image/jpeg,image/png,image/webp,application/pdf"
                 style="display:none" @change="onFileChange" />
          <div v-if="uploadError" class="api-error mt-2">
            <i class="bi bi-exclamation-circle-fill me-1"></i>{{ uploadError }}
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn-cancel" @click="step = 1">
            <i class="bi bi-arrow-left me-1"></i> Atrás
          </button>
          <button class="btn-primary"
                  :disabled="!selectedFile || submittingReceipt"
                  @click="submitReceipt">
            <span v-if="submittingReceipt">
              <i class="bi bi-hourglass-split spin me-1"></i>Enviando...
            </span>
            <span v-else><i class="bi bi-send-fill me-1"></i>Enviar comprobante</span>
          </button>
        </div>
      </template>

      <!-- PASO 3: Confirmación -->
      <template v-else-if="step === 3">
        <div class="up-success">
          <div class="success-icon ok"><i class="bi bi-check-circle-fill"></i></div>
          <h3>{{ successMsg }}</h3>
          <p>{{ successDetail }}</p>
          <button class="btn-primary mt-3" @click="$emit('done')">
            <i class="bi bi-check2 me-1"></i>Entendido
          </button>
        </div>
      </template>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import api from "@/services/apis"
import { detectCurrency, formatMoney, CURRENCY_NAMES, SUPPORTED_CURRENCIES } from "@/utils/currency"

const props = defineProps({
  currentPlanName: { type: String, default: "" },
  companyName:     { type: String, default: "" },
})
const emit = defineEmits(["close", "done"])

const step          = ref(1)
const loading       = ref(false)
const submitting    = ref(false)
const submittingReceipt = ref(false)
const downgrades    = ref([])
const selectedPlanId = ref(null)
const currency       = ref(detectCurrency())
const legalAccepted  = ref(false)
const confirmName    = ref("")
const nameErr        = ref("")
const uploadError    = ref("")
const isDrag         = ref(false)
const selectedFile   = ref(null)
const previewUrl     = ref("")
const fileInput      = ref(null)
const successMsg     = ref("")
const successDetail  = ref("")

const selectedPlan = computed(() => downgrades.value.find(p => p.id === selectedPlanId.value))
const isImage      = computed(() => selectedFile.value?.type?.startsWith("image/") ?? false)
const refText      = computed(() => {
  const user = JSON.parse(localStorage.getItem("user") || "{}")
  return `DOWNGRADE-${user.company_id ?? "0"}`
})

async function loadDowngrades() {
  loading.value = true
  selectedPlanId.value = null
  try {
    const res = await api.get(`/payments/available-downgrades?currency=${currency.value}`)
    downgrades.value = res.data
  } catch { downgrades.value = [] }
  finally { loading.value = false }
}

async function proceed() {
  nameErr.value = ""
  if (!confirmName.value.trim() ||
      confirmName.value.trim().toLowerCase() !== props.companyName.toLowerCase()) {
    nameErr.value = "El nombre no coincide con el de tu empresa"
    return
  }

  submitting.value = true
  try {
    const res = await api.post("/payments/request-downgrade", {
      plan_id:        selectedPlanId.value,
      currency_code:  currency.value,
      legal_accepted: true,
    })
    if (res.data.requires_payment) {
      step.value = 2
    } else {
      successMsg.value    = "¡Plan cambiado exitosamente!"
      successDetail.value = `Ahora estás en el plan ${selectedPlan.value?.name}. Las funciones extra quedan inaccesibles.`
      step.value = 3
    }
  } catch (e) {
    nameErr.value = e.response?.data?.detail || "Error al procesar el cambio"
  } finally {
    submitting.value = false
  }
}

function onFileChange(e) { setFile(e.target.files?.[0]) }
function onDrop(e) { isDrag.value = false; setFile(e.dataTransfer.files?.[0]) }
function setFile(file) {
  uploadError.value = ""
  if (!file) return
  const allowed = ["image/jpeg", "image/png", "image/webp", "application/pdf"]
  if (!allowed.includes(file.type)) { uploadError.value = "Tipo no permitido."; return }
  if (file.size > 5 * 1024 * 1024)  { uploadError.value = "El archivo supera 5 MB."; return }
  selectedFile.value = file
  previewUrl.value   = file.type.startsWith("image/") ? URL.createObjectURL(file) : "pdf"
}
function clearFile() {
  selectedFile.value = null; previewUrl.value = ""
  if (fileInput.value) fileInput.value.value = ""
}
function copy(text) { navigator.clipboard.writeText(text).catch(() => {}) }

async function submitReceipt() {
  if (!selectedFile.value) return
  uploadError.value = ""
  submittingReceipt.value = true
  const fd = new FormData()
  fd.append("file", selectedFile.value)
  try {
    await api.post("/payments/submit-receipt", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    successMsg.value    = "Comprobante enviado"
    successDetail.value = "Estamos revisando tu pago. Tu plan actual permanece activo mientras tanto."
    step.value = 3
  } catch (e) {
    uploadError.value = e.response?.data?.detail || "Error al enviar el comprobante."
  } finally {
    submittingReceipt.value = false
  }
}

onMounted(loadDowngrades)
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.55);
  display: flex; align-items: center; justify-content: center;
  z-index: 9000; padding: 20px;
}
.modal-box {
  background: #fff; border-radius: 20px; padding: 28px;
  width: 100%; max-width: 580px; max-height: 90vh; overflow-y: auto;
  box-shadow: 0 24px 60px rgba(0,0,0,.35);
  font-family: 'Segoe UI', system-ui, sans-serif;
}
.modal-head {
  display: flex; align-items: flex-start; gap: 14px; margin-bottom: 16px;
}
.modal-icon {
  width: 48px; height: 48px; border-radius: 12px;
  background: #fef3c7; color: #f59e0b;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.5rem; flex-shrink: 0;
}
.modal-icon.warn { background: #fef3c7; color: #f59e0b; }
.modal-head h2 { font-size: 1.1rem; font-weight: 800; color: #0f172a; margin: 0 0 4px; }
.modal-head p  { font-size: .84rem; color: #64748b; margin: 0; }
.btn-close-x {
  margin-left: auto; background: none; border: none;
  color: #94a3b8; font-size: 1rem; cursor: pointer; flex-shrink: 0; padding: 4px;
}

.legal-box {
  background: #fffbeb; border: 1.5px solid #fde68a;
  border-radius: 10px; padding: 14px 16px; margin-bottom: 14px; font-size: .84rem;
}
.legal-title { font-weight: 800; color: #92400e; margin-bottom: 8px; font-size: .9rem; }
.legal-box p  { color: #78350f; margin-bottom: 6px; line-height: 1.5; }
.legal-clause { font-size: .78rem; color: #9a6003; }
.legal-clause a { color: #b45309; font-weight: 600; }

.currency-row {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  background: #f8fafc; border: 1px solid #e2e8f0;
  border-radius: 8px; padding: 8px 12px; margin-bottom: 12px;
  font-size: .82rem; color: #475569;
}
.currency-row label { font-weight: 600; }
.currency-select {
  border: 1px solid #cbd5e1; border-radius: 6px;
  padding: 4px 8px; font-size: .8rem; outline: none;
  background: #fff; cursor: pointer; flex: 1; min-width: 140px;
}

.up-loading, .up-empty { text-align: center; padding: 24px; color: #94a3b8; font-size: .88rem; }
.down-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px; margin-bottom: 14px; }
.down-card {
  position: relative; border: 2px solid #e2e8f0; border-radius: 12px;
  padding: 14px 10px; background: #fff; cursor: pointer;
  transition: all .2s; text-align: center;
}
.down-card:hover   { border-color: #f59e0b; background: #fffbeb; }
.down-card.selected { border-color: #f59e0b; background: #fffbeb; }
.down-card.free.selected { border-color: #10b981; background: #f0fdf4; }
.down-badge {
  position: absolute; top: -1px; right: -1px;
  background: #10b981; color: #fff;
  font-size: .6rem; font-weight: 800; padding: 2px 6px;
  border-radius: 0 10px 0 8px;
}
.down-name  { font-weight: 800; font-size: .9rem; color: #0f172a; margin-bottom: 6px; }
.down-price { font-size: .82rem; }
.price-free { color: #10b981; font-weight: 800; }
.price-paid { color: #f59e0b; font-weight: 700; }
.price-paid small { font-size: .7rem; color: #64748b; }

.accept-section { margin-bottom: 14px; }
.accept-check {
  display: flex; gap: 10px; align-items: flex-start;
  font-size: .84rem; color: #334155; cursor: pointer; line-height: 1.5;
}
.accept-check input { flex-shrink: 0; margin-top: 2px; }
.confirm-name-wrap { margin-top: 12px; }
.confirm-name-label { font-size: .82rem; font-weight: 600; color: #475569; display: block; margin-bottom: 6px; }
.confirm-name-input {
  width: 100%; border: 1.5px solid #e2e8f0; border-radius: 8px;
  padding: 9px 12px; font-size: .88rem; outline: none; color: #0f172a;
  box-sizing: border-box;
}
.confirm-name-input:focus { border-color: #f59e0b; }
.field-error { color: #ef4444; font-size: .78rem; margin-top: 4px; }

/* reutilizados de PlanUpgradeModal */
.pay-summary, .pay-instructions, .upload-section, .drop-zone,
.preview-img, .pdf-preview, .copyable, .instr-row, .instr-label,
.instr-grid, .instr-title, .btn-remove { /* igual que PlanUpgradeModal */ }

.pay-summary { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px; margin-bottom: 14px; }
.pay-summary-row { display: flex; justify-content: space-between; font-size: .85rem; color: #475569; margin-bottom: 6px; }
.pay-summary-row.highlight { background: #fffbeb; border-radius: 6px; padding: 6px 8px; }
.price-big { color: #f59e0b; font-size: 1.05rem; font-weight: 800; }
.pay-instructions { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px; margin-bottom: 14px; }
.instr-title { font-weight: 700; font-size: .85rem; color: #1e293b; margin-bottom: 10px; }
.instr-grid { display: flex; flex-direction: column; gap: 6px; }
.instr-row { display: flex; justify-content: space-between; font-size: .82rem; gap: 8px; }
.instr-label { color: #64748b; font-weight: 600; flex-shrink: 0; }
.copyable { color: #2563eb; cursor: pointer; font-weight: 600; }
.upload-section { margin-bottom: 12px; }
.upload-title { font-weight: 700; font-size: .85rem; color: #1e293b; margin-bottom: 8px; }
.drop-zone {
  border: 2px dashed #cbd5e1; border-radius: 10px; padding: 20px;
  text-align: center; cursor: pointer; transition: all .2s;
  color: #64748b; font-size: .84rem; background: #f8fafc; position: relative;
}
.drop-zone:hover, .drop-zone.dragover { border-color: #f59e0b; background: #fffbeb; }
.drop-zone.has-file { border-style: solid; border-color: #10b981; background: #f0fdf4; }
.preview-img { max-width: 100%; max-height: 160px; border-radius: 6px; }
.pdf-preview { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.pdf-preview p { margin: 0; font-size: .82rem; }
.btn-remove {
  position: absolute; top: 6px; right: 6px;
  background: none; border: none; color: #ef4444; font-size: 1.1rem; cursor: pointer;
}

.up-success { text-align: center; padding: 12px 0; }
.success-icon { font-size: 3.5rem; margin-bottom: 12px; }
.success-icon.ok { color: #10b981; }
.up-success h3 { font-size: 1.1rem; font-weight: 800; color: #0f172a; margin-bottom: 8px; }
.up-success p  { color: #64748b; font-size: .88rem; }

.modal-footer { display: flex; gap: 10px; margin-top: 16px; justify-content: flex-end; }
.btn-primary {
  background: #2563eb; color: #fff; border: none;
  padding: 10px 20px; border-radius: 8px; font-weight: 700; font-size: .88rem;
  cursor: pointer; transition: all .2s; display: flex; align-items: center; gap: 6px;
}
.btn-primary:hover:not(:disabled) { background: #1d4ed8; }
.btn-primary:disabled { opacity: .5; cursor: not-allowed; }
.btn-warn {
  background: #f59e0b; color: #fff; border: none;
  padding: 10px 20px; border-radius: 8px; font-weight: 700; font-size: .88rem;
  cursor: pointer; transition: all .2s; display: flex; align-items: center; gap: 6px;
}
.btn-warn:hover:not(:disabled) { background: #d97706; }
.btn-warn:disabled { opacity: .5; cursor: not-allowed; }
.btn-cancel {
  border: 1.5px solid #e2e8f0; background: #fff; color: #64748b;
  padding: 10px 18px; border-radius: 8px; font-weight: 600; font-size: .88rem;
  cursor: pointer; display: flex; align-items: center; gap: 4px;
}
.api-error {
  background: #fef2f2; border: 1px solid #fecaca;
  color: #dc2626; padding: 8px 12px; border-radius: 6px; font-size: .82rem;
}
.spin { animation: spin 1s linear infinite; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }
.mt-3 { margin-top: 12px; }
</style>
