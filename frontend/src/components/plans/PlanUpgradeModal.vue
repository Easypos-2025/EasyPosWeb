<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-box">

      <!-- CABECERA -->
      <div class="modal-head">
        <div class="modal-icon"><i class="bi bi-arrow-up-circle-fill"></i></div>
        <div>
          <h2>Mejorar plan</h2>
          <p>Tu plan actual: <strong>{{ currentPlanName }}</strong>.
             Elige el plan al que deseas actualizar.</p>
        </div>
        <button class="btn-close-x" @click="$emit('close')">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>

      <!-- PASO 1: Elegir plan -->
      <template v-if="step === 1">
        <div class="currency-row">
          <i class="bi bi-currency-exchange"></i>
          <label>Moneda:</label>
          <select v-model="currency" class="currency-select" @change="loadUpgrades">
            <option v-for="code in SUPPORTED_CURRENCIES" :key="code" :value="code">
              {{ code }} — {{ CURRENCY_NAMES[code] }}
            </option>
          </select>
        </div>

        <div v-if="loading" class="up-loading">
          <i class="bi bi-hourglass-split spin"></i> Cargando planes...
        </div>
        <div v-else-if="!upgrades.length" class="up-empty">
          <i class="bi bi-check-circle-fill text-success"></i>
          Ya tienes el plan más alto disponible.
        </div>
        <div v-else class="up-grid">
          <button
            v-for="p in upgrades" :key="p.id"
            class="up-card"
            :class="{ selected: selectedPlanId === p.id }"
            @click="selectedPlanId = p.id"
          >
            <div class="up-card-name">{{ p.name }}</div>
            <div class="up-card-price">{{ formatMoney(p.price, currency) }}<small>/año</small></div>
            <div v-if="p.max_users !== -1" class="up-card-meta">
              <i class="bi bi-people me-1"></i>Hasta {{ p.max_users }} usuarios
            </div>
            <div v-else class="up-card-meta"><i class="bi bi-infinity me-1"></i>Usuarios ilimitados</div>
            <div v-if="p.description" class="up-card-desc">{{ p.description }}</div>
          </button>
        </div>

        <div class="modal-footer">
          <button class="btn-cancel" @click="$emit('close')">Cancelar</button>
          <button class="btn-primary" :disabled="!selectedPlanId || loading" @click="step = 2">
            Continuar <i class="bi bi-arrow-right ms-1"></i>
          </button>
        </div>
      </template>

      <!-- PASO 2: Subir comprobante -->
      <template v-else-if="step === 2">
        <div class="pay-summary">
          <div class="pay-summary-row">
            <span>Nuevo plan:</span>
            <strong>{{ selectedPlan?.name }}</strong>
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
            <div class="instr-row"><span class="instr-label">NIT:</span>
              <span class="copyable" @click="copy('900.123.456-7')">900.123.456-7 <i class="bi bi-copy"></i></span>
            </div>
            <div class="instr-row"><span class="instr-label">Concepto:</span>
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

        <div class="up-note">
          <i class="bi bi-info-circle me-1"></i>
          Seguirás usando tu plan actual mientras revisamos el comprobante.
        </div>

        <div class="modal-footer">
          <button class="btn-cancel" @click="step = 1">
            <i class="bi bi-arrow-left me-1"></i> Atrás
          </button>
          <button class="btn-primary"
                  :disabled="!selectedFile || submitting"
                  @click="submit">
            <span v-if="submitting">
              <i class="bi bi-hourglass-split spin me-1"></i>Enviando...
            </span>
            <span v-else>
              <i class="bi bi-send-fill me-1"></i>Enviar comprobante
            </span>
          </button>
        </div>
      </template>

      <!-- PASO 3: Confirmación -->
      <template v-else-if="step === 3">
        <div class="up-success">
          <div class="success-icon"><i class="bi bi-check-circle-fill"></i></div>
          <h3>¡Comprobante enviado!</h3>
          <p>Tu solicitud de mejora al plan <strong>{{ selectedPlan?.name }}</strong>
             está en revisión.</p>
          <p class="up-note-success">Seguirás con tu plan actual hasta que aprobemos el pago.
             Te notificaremos por correo.</p>
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

const props = defineProps({ currentPlanName: { type: String, default: "Free" } })
const emit  = defineEmits(["close", "done"])

const step          = ref(1)
const loading       = ref(false)
const submitting    = ref(false)
const upgrades      = ref([])
const selectedPlanId = ref(null)
const currency       = ref(detectCurrency())
const uploadError    = ref("")
const isDrag         = ref(false)
const selectedFile   = ref(null)
const previewUrl     = ref("")
const fileInput      = ref(null)

const selectedPlan = computed(() => upgrades.value.find(p => p.id === selectedPlanId.value))
const isImage      = computed(() => selectedFile.value?.type?.startsWith("image/") ?? false)
const refText      = computed(() => {
  const user = JSON.parse(localStorage.getItem("user") || "{}")
  return `UPGRADE-${user.company_id ?? "0"}`
})

async function loadUpgrades() {
  loading.value = true
  selectedPlanId.value = null
  try {
    const res = await api.get(`/payments/available-upgrades?currency=${currency.value}`)
    upgrades.value = res.data
  } catch { upgrades.value = [] }
  finally { loading.value = false }
}

function onFileChange(e) { setFile(e.target.files?.[0]) }
function onDrop(e) { isDrag.value = false; setFile(e.dataTransfer.files?.[0]) }
function setFile(file) {
  uploadError.value = ""
  if (!file) return
  const allowed = ["image/jpeg", "image/png", "image/webp", "application/pdf"]
  if (!allowed.includes(file.type)) { uploadError.value = "Tipo no permitido. Usa JPG, PNG, WEBP o PDF."; return }
  if (file.size > 5 * 1024 * 1024)  { uploadError.value = "El archivo supera 5 MB."; return }
  selectedFile.value = file
  previewUrl.value   = file.type.startsWith("image/") ? URL.createObjectURL(file) : "pdf"
}
function clearFile() {
  selectedFile.value = null; previewUrl.value = ""
  if (fileInput.value) fileInput.value.value = ""
}
function copy(text) { navigator.clipboard.writeText(text).catch(() => {}) }

async function submit() {
  if (!selectedFile.value || !selectedPlanId.value) return
  uploadError.value = ""
  submitting.value  = true

  // 1. Registrar la solicitud de upgrade
  try {
    await api.post("/payments/request-upgrade", {
      plan_id: selectedPlanId.value,
      currency_code: currency.value,
    })
  } catch (e) {
    // Si ya existe un upgrade_pending solo subimos el comprobante
    const msg = e.response?.data?.detail || ""
    if (!msg.includes("Ya tienes un upgrade")) {
      uploadError.value = msg || "Error al registrar el upgrade"
      submitting.value = false
      return
    }
  }

  // 2. Subir comprobante
  const fd = new FormData()
  fd.append("file", selectedFile.value)
  try {
    await api.post("/payments/submit-upgrade-receipt", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    step.value = 3
  } catch (e) {
    uploadError.value = e.response?.data?.detail || "Error al enviar el comprobante."
  } finally {
    submitting.value = false
  }
}

onMounted(loadUpgrades)
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.55);
  display: flex; align-items: center; justify-content: center;
  z-index: 9000; padding: 20px;
}
.modal-box {
  background: #fff; border-radius: 20px; padding: 28px;
  width: 100%; max-width: 600px; max-height: 90vh; overflow-y: auto;
  box-shadow: 0 24px 60px rgba(0,0,0,.35);
  font-family: 'Segoe UI', system-ui, sans-serif;
}
.modal-head {
  display: flex; align-items: flex-start; gap: 14px; margin-bottom: 20px;
}
.modal-icon {
  width: 48px; height: 48px; border-radius: 12px;
  background: #eff6ff; color: #2563eb;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.5rem; flex-shrink: 0;
}
.modal-head h2 { font-size: 1.1rem; font-weight: 800; color: #0f172a; margin: 0 0 4px; }
.modal-head p  { font-size: .84rem; color: #64748b; margin: 0; }
.btn-close-x {
  margin-left: auto; background: none; border: none;
  color: #94a3b8; font-size: 1rem; cursor: pointer; flex-shrink: 0; padding: 4px;
}
.btn-close-x:hover { color: #334155; }

.currency-row {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  background: #f8fafc; border: 1px solid #e2e8f0;
  border-radius: 8px; padding: 8px 12px; margin-bottom: 14px;
  font-size: .82rem; color: #475569;
}
.currency-row label { font-weight: 600; }
.currency-select {
  border: 1px solid #cbd5e1; border-radius: 6px;
  padding: 4px 8px; font-size: .8rem; outline: none;
  background: #fff; cursor: pointer; flex: 1; min-width: 140px;
}

.up-loading, .up-empty { text-align: center; padding: 32px; color: #94a3b8; font-size: .9rem; }
.up-empty .bi { font-size: 2rem; display: block; margin-bottom: 8px; }

.up-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 10px; margin-bottom: 16px; }
.up-card {
  border: 2px solid #e2e8f0; border-radius: 12px; padding: 16px 12px;
  background: #fff; cursor: pointer; transition: all .2s; text-align: center;
}
.up-card:hover   { border-color: #2563eb; background: #eff6ff; }
.up-card.selected { border-color: #2563eb; background: #eff6ff; }
.up-card-name  { font-weight: 800; font-size: .95rem; color: #0f172a; margin-bottom: 6px; }
.up-card-price { font-size: .9rem; font-weight: 700; color: #2563eb; margin-bottom: 4px; }
.up-card-price small { font-size: .7rem; color: #64748b; }
.up-card-meta  { font-size: .72rem; color: #64748b; margin-bottom: 4px; }
.up-card-desc  { font-size: .72rem; color: #94a3b8; }

.pay-summary { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px; margin-bottom: 14px; }
.pay-summary-row { display: flex; justify-content: space-between; font-size: .85rem; color: #475569; margin-bottom: 6px; }
.pay-summary-row.highlight { background: #eff6ff; border-radius: 6px; padding: 6px 8px; }
.price-big { color: #2563eb; font-size: 1.05rem; font-weight: 800; }

.pay-instructions { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px; margin-bottom: 14px; }
.instr-title { font-weight: 700; font-size: .85rem; color: #1e293b; margin-bottom: 10px; }
.instr-grid { display: flex; flex-direction: column; gap: 6px; }
.instr-row { display: flex; justify-content: space-between; font-size: .82rem; gap: 8px; }
.instr-label { color: #64748b; font-weight: 600; flex-shrink: 0; }
.copyable { color: #2563eb; cursor: pointer; font-weight: 600; }
.copyable:hover { text-decoration: underline; }

.upload-section { margin-bottom: 12px; }
.upload-title { font-weight: 700; font-size: .85rem; color: #1e293b; margin-bottom: 8px; }
.drop-zone {
  border: 2px dashed #cbd5e1; border-radius: 10px; padding: 20px;
  text-align: center; cursor: pointer; transition: all .2s;
  color: #64748b; font-size: .84rem; background: #f8fafc; position: relative;
}
.drop-zone:hover, .drop-zone.dragover { border-color: #2563eb; background: #eff6ff; }
.drop-zone.has-file { border-style: solid; border-color: #10b981; background: #f0fdf4; }
.preview-img { max-width: 100%; max-height: 160px; border-radius: 6px; }
.pdf-preview { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.pdf-preview p { margin: 0; font-size: .82rem; }
.btn-remove {
  position: absolute; top: 6px; right: 6px;
  background: none; border: none; color: #ef4444; font-size: 1.1rem; cursor: pointer;
}

.up-note {
  font-size: .78rem; color: #64748b;
  background: #f0fdf4; border: 1px solid #bbf7d0;
  border-radius: 8px; padding: 8px 12px; margin-bottom: 12px;
}

.up-success { text-align: center; padding: 12px 0; }
.success-icon { font-size: 3.5rem; color: #10b981; margin-bottom: 12px; }
.up-success h3 { font-size: 1.1rem; font-weight: 800; color: #0f172a; margin-bottom: 8px; }
.up-success p  { color: #64748b; font-size: .88rem; margin-bottom: 4px; }
.up-note-success { font-size: .78rem; color: #059669; background: #f0fdf4; border-radius: 8px; padding: 8px; }

.modal-footer { display: flex; gap: 10px; margin-top: 16px; justify-content: flex-end; }
.btn-primary {
  background: #2563eb; color: #fff; border: none;
  padding: 10px 20px; border-radius: 8px; font-weight: 700; font-size: .88rem;
  cursor: pointer; transition: all .2s; display: flex; align-items: center; gap: 6px;
}
.btn-primary:hover:not(:disabled) { background: #1d4ed8; }
.btn-primary:disabled { opacity: .5; cursor: not-allowed; }
.btn-cancel {
  border: 1.5px solid #e2e8f0; background: #fff; color: #64748b;
  padding: 10px 18px; border-radius: 8px; font-weight: 600; font-size: .88rem;
  cursor: pointer; transition: all .2s; display: flex; align-items: center; gap: 4px;
}
.btn-cancel:hover { border-color: #94a3b8; }

.api-error {
  background: #fef2f2; border: 1px solid #fecaca;
  color: #dc2626; padding: 8px 12px; border-radius: 6px; font-size: .82rem;
}
.spin { animation: spin 1s linear infinite; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }
.mt-3 { margin-top: 12px; }

@media (max-width: 500px) {
  .modal-box { padding: 20px 14px; }
  .up-grid   { grid-template-columns: repeat(2, 1fr); }
}
</style>
