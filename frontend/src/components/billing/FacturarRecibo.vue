<template>
  <Teleport to="body">
    <div class="fr-overlay" @click.self="$emit('close')">
      <div class="fr-modal">

        <!-- ── Header ── -->
        <div class="fr-header">
          <div class="fr-header-left">
            <i class="bi bi-receipt-cutoff"></i>
            <span>Registrar Recibo</span>
            <span v-if="ordenNumero" class="fr-orden-tag">#{{ ordenNumero }}</span>
          </div>
          <button class="fr-close" @click="$emit('close')">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>

        <!-- ── Body ── -->
        <div class="fr-body">

          <!-- COLUMNA IZQUIERDA: Resumen de la orden -->
          <div class="fr-col fr-col-items">
            <div class="fr-section-title">
              <i class="bi bi-list-ul"></i> Ítems de la Orden
            </div>

            <div class="fr-items-wrap">
              <table class="fr-table">
                <thead>
                  <tr>
                    <th>Descripción</th>
                    <th class="ta-c">Cant.</th>
                    <th class="ta-r">Precio</th>
                    <th class="ta-r">Total</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="!items.length">
                    <td colspan="4" class="fr-empty">Sin ítems en la orden</td>
                  </tr>
                  <tr v-for="it in items" :key="it.id">
                    <td class="fr-td-name">{{ it.nombre }}</td>
                    <td class="ta-c">{{ it.cantidad }}</td>
                    <td class="ta-r">{{ fmt(it.precio) }}</td>
                    <td class="ta-r fw-bold">{{ fmt(it.precio * it.cantidad) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Totales -->
            <div class="fr-totals">
              <div class="fr-total-row">
                <span>Subtotal</span>
                <span>{{ fmt(subtotal) }}</span>
              </div>
              <div v-if="billingConfig.has_tip" class="fr-total-row fr-tip-row">
                <span>
                  {{ billingConfig.tip_label || 'Propina' }}
                  ({{ billingConfig.tip_percentage }}%)
                </span>
                <span>{{ fmt(tipAmount) }}</span>
              </div>
              <div class="fr-total-row fr-grand-total">
                <span>Total a Cobrar</span>
                <span>{{ fmt(grandTotal) }}</span>
              </div>
            </div>
          </div>

          <!-- COLUMNA DERECHA: Formas de pago -->
          <div class="fr-col fr-col-payments">
            <div class="fr-section-title">
              <i class="bi bi-cash-coin"></i> Formas de Pago
            </div>

            <div v-if="loadingTypes" class="fr-loading">Cargando formas de pago...</div>
            <template v-else>
              <div class="fr-payments-list">
                <div v-for="(pago, i) in pagos" :key="i" class="fr-payment-row">
                  <select v-model="pago.payment_method_id" class="fr-select">
                    <option value="">Seleccionar método...</option>
                    <option v-for="pt in paymentTypes" :key="pt.id" :value="pt.id">
                      {{ pt.name }}
                    </option>
                  </select>
                  <input
                    v-model.number="pago.amount"
                    type="number"
                    min="0"
                    class="fr-amount"
                    placeholder="0"
                    @focus="$event.target.select()"
                  />
                  <button class="fr-btn-remove" @click="removePago(i)" title="Quitar">
                    <i class="bi bi-trash3"></i>
                  </button>
                </div>

                <div v-if="!pagos.length" class="fr-empty">
                  Agrega al menos una forma de pago
                </div>
              </div>

              <button class="fr-btn-add" @click="addPago">
                <i class="bi bi-plus-circle"></i> Agregar forma de pago
              </button>

              <!-- Resumen de pago -->
              <div class="fr-pay-summary">
                <div class="fr-ps-row">
                  <span>Total a cobrar:</span>
                  <span class="fw-bold">{{ fmt(grandTotal) }}</span>
                </div>
                <div class="fr-ps-row">
                  <span>Pagado:</span>
                  <span :class="totalPagado >= grandTotal ? 'text-green' : 'text-muted'">
                    {{ fmt(totalPagado) }}
                  </span>
                </div>
                <div v-if="pendiente > 1" class="fr-ps-row fr-ps-pending">
                  <span>Pendiente:</span>
                  <span class="text-red">{{ fmt(pendiente) }}</span>
                </div>
                <div v-else-if="totalPagado >= grandTotal" class="fr-ps-ok">
                  <i class="bi bi-check-circle-fill"></i> Pago completo
                </div>
              </div>
            </template>
          </div>

        </div>

        <!-- ── Footer ── -->
        <div class="fr-footer">
          <button class="fr-btn-cancel" @click="$emit('close')" :disabled="saving">
            Cancelar
          </button>
          <button
            class="fr-btn-submit"
            :disabled="!canSubmit || saving"
            @click="registrar"
          >
            <i v-if="!saving" class="bi bi-receipt-cutoff"></i>
            <span v-if="saving">⏳ Registrando...</span>
            <span v-else>Registrar Recibo</span>
          </button>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

const props = defineProps({
  ordenId:     { type: Number, required: true },
  ordenNumero: { type: [String, Number], default: "" },
  items:       { type: Array, default: () => [] },
  companyId:   { type: Number, required: true },
})

const emit = defineEmits(["success", "close"])

// ── Estado ──────────────────────────────────────────────────────────────────
const paymentTypes   = ref([])
const billingConfig  = ref({ has_tip: 0, tip_percentage: 0, tip_label: "Propina" })
const pagos          = ref([])
const loadingTypes   = ref(true)
const saving         = ref(false)

// ── Cálculos ─────────────────────────────────────────────────────────────────
const subtotal = computed(() =>
  props.items.reduce((s, it) => s + (parseFloat(it.precio) * parseFloat(it.cantidad)), 0)
)

const tipAmount = computed(() => {
  if (!billingConfig.value.has_tip) return 0
  // Recibo: propina sobre el total de la cuenta (no aplica impuesto)
  return Math.round(subtotal.value * (parseFloat(billingConfig.value.tip_percentage) / 100))
})

const grandTotal  = computed(() => subtotal.value + tipAmount.value)
const totalPagado = computed(() => pagos.value.reduce((s, p) => s + (parseFloat(p.amount) || 0), 0))
const pendiente   = computed(() => grandTotal.value - totalPagado.value)

const canSubmit = computed(() =>
  pagos.value.length > 0 &&
  pagos.value.every(p => p.payment_method_id && (parseFloat(p.amount) || 0) > 0) &&
  Math.abs(pendiente.value) <= 1 &&
  props.items.length > 0
)

// ── Carga inicial ─────────────────────────────────────────────────────────────
async function loadData() {
  loadingTypes.value = true
  try {
    const [typesRes, cfgRes] = await Promise.all([
      api.get("/api/talleres/payment-types", { params: { company_id: props.companyId } }),
      api.get("/api/talleres/billing-config", { params: { company_id: props.companyId } }),
    ])
    paymentTypes.value  = typesRes.data || []
    billingConfig.value = cfgRes.data   || billingConfig.value

    // Pre-llenar con el primer método activo
    const def = paymentTypes.value.find(p => p.is_default) || paymentTypes.value[0]
    pagos.value = [{
      payment_method_id: def?.id || "",
      amount: grandTotal.value,
      notes: "",
    }]
  } catch {
    showToast("Error cargando formas de pago", "error")
  }
  loadingTypes.value = false
}

// Cuando cambia el grandTotal (p.ej. al abrir), sincronizar el primer pago si hay uno solo
watch(grandTotal, (val) => {
  if (pagos.value.length === 1) pagos.value[0].amount = val
})

// ── Métodos de pago ──────────────────────────────────────────────────────────
function addPago() {
  pagos.value.push({ payment_method_id: "", amount: Math.max(0, pendiente.value), notes: "" })
}

function removePago(i) {
  pagos.value.splice(i, 1)
}

// ── Registrar recibo ──────────────────────────────────────────────────────────
async function registrar() {
  if (!canSubmit.value) return
  saving.value = true
  try {
    const res = await api.post(`/api/talleres/ordenes/${props.ordenId}/recibo`, {
      company_id: props.companyId,
      pagos: pagos.value.map(p => ({
        payment_method_id: p.payment_method_id,
        amount: parseFloat(p.amount),
        notes: p.notes || "",
      })),
    })
    showToast(`Recibo #${res.data.receipt_number} registrado`, "success", 2500)
    emit("success", res.data)
  } catch (e) {
    showToast(e?.response?.data?.detail || "Error al registrar recibo", "error", 3000)
  }
  saving.value = false
}

// ── Formato moneda ────────────────────────────────────────────────────────────
function fmt(v) {
  return new Intl.NumberFormat("es-CO", {
    style: "currency", currency: "COP", maximumFractionDigits: 0,
  }).format(v || 0)
}

onMounted(loadData)
</script>

<style scoped>
/* ── Overlay ─────────────────────────────────────────────────────────── */
.fr-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9000;
  padding: 16px;
}

/* ── Modal ───────────────────────────────────────────────────────────── */
.fr-modal {
  background: #fff;
  border-radius: 14px;
  width: 100%;
  max-width: 860px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,.25);
  overflow: hidden;
}

/* ── Header ──────────────────────────────────────────────────────────── */
.fr-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: #0f172a;
  color: #fff;
  flex-shrink: 0;
}

.fr-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 700;
}

.fr-orden-tag {
  background: rgba(255,255,255,.15);
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
}

.fr-close {
  background: none;
  border: none;
  color: rgba(255,255,255,.7);
  cursor: pointer;
  font-size: 18px;
  padding: 4px;
  border-radius: 6px;
  line-height: 1;
  transition: color .15s;
}
.fr-close:hover { color: #fff; }

/* ── Body ────────────────────────────────────────────────────────────── */
.fr-body {
  display: flex;
  gap: 0;
  flex: 1;
  overflow: hidden;
}

.fr-col {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.fr-col-items {
  flex: 1.2;
  border-right: 1px solid #e2e8f0;
}

.fr-col-payments {
  flex: 1;
}

.fr-col-items,
.fr-col-payments {
  padding: 16px 20px;
  overflow-y: auto;
  gap: 12px;
}

/* ── Section title ───────────────────────────────────────────────────── */
.fr-section-title {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .5px;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
  flex-shrink: 0;
}

/* ── Items table ─────────────────────────────────────────────────────── */
.fr-items-wrap {
  flex: 1;
  overflow-y: auto;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  margin-bottom: 10px;
}

.fr-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.fr-table thead tr {
  background: #f8fafc;
  position: sticky;
  top: 0;
}

.fr-table th {
  padding: 8px 10px;
  font-size: 11px;
  font-weight: 700;
  color: #475569;
  text-transform: uppercase;
  border-bottom: 1px solid #e2e8f0;
  white-space: nowrap;
}

.fr-table td {
  padding: 8px 10px;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
}

.fr-table tbody tr:last-child td { border-bottom: none; }
.fr-td-name { max-width: 160px; }

/* ── Totales ─────────────────────────────────────────────────────────── */
.fr-totals {
  background: #f8fafc;
  border-radius: 8px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex-shrink: 0;
}

.fr-total-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #475569;
}

.fr-tip-row { color: #92400e; }

.fr-grand-total {
  border-top: 2px solid #e2e8f0;
  padding-top: 8px;
  margin-top: 2px;
  font-size: 16px;
  font-weight: 800;
  color: #0f172a;
}

/* ── Formas de pago ──────────────────────────────────────────────────── */
.fr-payments-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 10px;
}

.fr-payment-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.fr-select {
  flex: 1.5;
  padding: 8px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 13px;
  background: #f8fafc;
  color: #334155;
  outline: none;
  min-width: 0;
}
.fr-select:focus { border-color: #2563eb; background: #fff; }

.fr-amount {
  flex: 1;
  padding: 8px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
  background: #f8fafc;
  outline: none;
  text-align: right;
  min-width: 0;
}
.fr-amount:focus { border-color: #2563eb; background: #fff; }

.fr-btn-remove {
  flex-shrink: 0;
  background: #fee2e2;
  color: #dc2626;
  border: none;
  border-radius: 8px;
  width: 32px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 13px;
  transition: background .15s;
}
.fr-btn-remove:hover { background: #fecaca; }

.fr-btn-add {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: 1.5px dashed #cbd5e1;
  border-radius: 8px;
  padding: 8px 14px;
  font-size: 13px;
  color: #64748b;
  cursor: pointer;
  width: 100%;
  justify-content: center;
  transition: all .15s;
  margin-bottom: 14px;
}
.fr-btn-add:hover { border-color: #2563eb; color: #2563eb; background: #eff6ff; }

/* ── Resumen pago ─────────────────────────────────────────────────────── */
.fr-pay-summary {
  background: #f8fafc;
  border-radius: 8px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: auto;
}

.fr-ps-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #475569;
}

.fr-ps-pending {
  border-top: 1px dashed #fca5a5;
  padding-top: 6px;
  margin-top: 2px;
  font-weight: 700;
}

.fr-ps-ok {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #16a34a;
  font-weight: 600;
  font-size: 13px;
  border-top: 1px solid #dcfce7;
  padding-top: 6px;
  margin-top: 2px;
}

/* ── Footer ──────────────────────────────────────────────────────────── */
.fr-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
  flex-shrink: 0;
}

.fr-btn-cancel {
  padding: 10px 22px;
  background: #fff;
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  transition: all .15s;
}
.fr-btn-cancel:hover:not(:disabled) { background: #f1f5f9; }
.fr-btn-cancel:disabled { opacity: .5; cursor: default; }

.fr-btn-submit {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 26px;
  background: #059669;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: background .15s;
}
.fr-btn-submit:hover:not(:disabled) { background: #047857; }
.fr-btn-submit:disabled { opacity: .5; cursor: not-allowed; }

/* ── Utilidades ──────────────────────────────────────────────────────── */
.ta-c { text-align: center; }
.ta-r { text-align: right; }
.fw-bold { font-weight: 700; }
.text-green { color: #16a34a; font-weight: 700; }
.text-red   { color: #dc2626; }
.text-muted { color: #94a3b8; }
.fr-empty { text-align: center; color: #94a3b8; font-size: 13px; padding: 20px; }
.fr-loading { color: #94a3b8; font-size: 13px; text-align: center; padding: 24px; }

/* ── Responsive ──────────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .fr-body { flex-direction: column; overflow-y: auto; }
  .fr-col-items { border-right: none; border-bottom: 1px solid #e2e8f0; }
  .fr-col-items,
  .fr-col-payments { max-height: none; overflow-y: visible; }
  .fr-items-wrap { max-height: 200px; }
}

@media (max-width: 576px) {
  .fr-modal { max-height: 98vh; border-radius: 10px; }
  .fr-payment-row { flex-wrap: wrap; }
  .fr-select { flex: 1 1 100%; }
  .fr-amount { flex: 1; }
  .fr-footer { flex-direction: column; }
  .fr-btn-cancel, .fr-btn-submit { width: 100%; justify-content: center; }
}
</style>
