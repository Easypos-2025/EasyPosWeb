<template>
  <div class="pago-wrap">

    <TurnoCajaModal v-if="!checkingTurno && !turnoAbierto" @opened="onTurnoAbierto" />

    <div v-if="loading" class="pago-loading">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-else-if="errorCarga" class="pago-error">
      <i class="bi bi-exclamation-triangle fs-1 text-danger"></i>
      <p>{{ errorCarga }}</p>
      <button class="btn btn-outline-secondary" @click="$router.back()">Volver</button>
    </div>

    <template v-else-if="datos">
      <div class="pago-header">
        <button class="pago-back" @click="$router.back()"><i class="bi bi-arrow-left"></i></button>
        <div class="pago-header__info">
          <h1>{{ datos.order.table_name || 'Pago' }}</h1>
          <span class="pago-consecutivo">Recibo Nro. {{ datos.consecutivo_preview }} <small>(informativo)</small></span>
        </div>
      </div>

      <div class="pago-body">

        <!-- Items -->
        <div class="pago-card">
          <div class="pago-card__title"><i class="bi bi-list-ul"></i> Ítems</div>
          <div class="pago-item" v-for="it in datos.items" :key="it.item">
            <span class="pago-item__qty">{{ it.quantity }}×</span>
            <span class="pago-item__name">
              {{ it.name }}
              <i v-if="it.typification_id" class="bi bi-percent text-success ms-1" title="Tiene descuento"></i>
            </span>
            <span class="pago-item__amount">{{ fmt(it.amount) }}</span>
          </div>
        </div>

        <!-- Cliente / Vendedor -->
        <div class="pago-card">
          <div class="pago-field">
            <label>Cliente</label>
            <select v-model="form.customer_id" class="form-select">
              <option :value="datos.default_customer_id">Consumidor Final</option>
              <option v-for="c in clientes" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          <div class="pago-field">
            <label>Vendedor</label>
            <select v-model="form.waiter_id" class="form-select">
              <option :value="0">—</option>
              <option v-for="w in datos.waiters" :key="w.id" :value="w.id">{{ w.name }}</option>
            </select>
          </div>
        </div>

        <!-- Descuento general -->
        <div class="pago-card">
          <div class="pago-field">
            <label>
              % Descuento general
              <span v-if="datos.has_item_discount" class="text-muted small">
                (deshabilitado: ya hay ítems con descuento individual)
              </span>
            </label>
            <input
              v-model.number="form.discount_percentage"
              type="number" min="0" max="100" class="form-control"
              :disabled="datos.has_item_discount"
              placeholder="0"
            />
          </div>
        </div>

        <!-- Propina -->
        <div class="pago-card" v-if="datos.tip.enabled">
          <div class="pago-field pago-field--row">
            <div>
              <label>{{ datos.tip.label }}</label>
              <input v-model.number="form.tip_amount" type="number" min="0" class="form-control" :disabled="quitarPropina" />
            </div>
            <label class="pago-check">
              <input type="checkbox" v-model="quitarPropina" /> Quitar propina
            </label>
          </div>
        </div>

        <!-- Domicilio -->
        <div class="pago-card" v-if="datos.order.is_delivery">
          <div class="pago-field">
            <label>Valor domicilio</label>
            <input v-model.number="form.delivery_amount" type="number" min="0" class="form-control" placeholder="0" />
          </div>
        </div>

        <!-- Observación -->
        <div class="pago-card">
          <div class="pago-field">
            <label>Observación</label>
            <input v-model="form.observacion" class="form-control" maxlength="250" placeholder="Opcional" />
          </div>
        </div>

        <!-- Resumen -->
        <div class="pago-card pago-resumen">
          <div class="pago-resumen__row"><span>Subtotal</span><strong>{{ fmt(datos.subtotal) }}</strong></div>
          <div class="pago-resumen__row" v-if="descuentoGeneralValor"><span>Descuento</span><strong class="text-danger">-{{ fmt(descuentoGeneralValor) }}</strong></div>
          <div class="pago-resumen__row" v-if="propinaEfectiva"><span>{{ datos.tip.label }}</span><strong>{{ fmt(propinaEfectiva) }}</strong></div>
          <div class="pago-resumen__row" v-if="form.delivery_amount"><span>Domicilio</span><strong>{{ fmt(form.delivery_amount) }}</strong></div>
          <div class="pago-resumen__row pago-resumen__total"><span>TOTAL A PAGAR</span><strong>{{ fmt(totalAPagar) }}</strong></div>
        </div>

        <!-- Formas de pago -->
        <div class="pago-card">
          <div class="pago-card__title"><i class="bi bi-credit-card"></i> Forma(s) de pago</div>
          <div class="pago-pago-row" v-for="(p, idx) in form.payments" :key="idx">
            <select v-model.number="p.payment_method_id" class="form-select">
              <option v-for="pt in datos.payment_types" :key="pt.id" :value="pt.id">{{ pt.name }}</option>
            </select>
            <input v-model.number="p.amount" type="number" min="0" class="form-control" placeholder="Valor" />
            <button class="pago-pago-del" @click="quitarFormaPago(idx)" :disabled="form.payments.length === 1">
              <i class="bi bi-x-lg"></i>
            </button>
          </div>
          <button class="btn btn-sm btn-outline-primary mt-2" @click="agregarFormaPago">
            <i class="bi bi-plus-lg"></i> Agregar forma de pago
          </button>
          <div class="pago-pago-check" :class="{ 'pago-pago-check--ok': diferenciaPago === 0, 'pago-pago-check--bad': diferenciaPago !== 0 }">
            <span v-if="diferenciaPago === 0"><i class="bi bi-check-circle-fill"></i> Cubre el total</span>
            <span v-else>Faltan / sobran {{ fmt(Math.abs(diferenciaPago)) }}</span>
          </div>
        </div>

      </div>

      <div class="pago-footer">
        <button class="btn btn-outline-secondary" disabled title="Próximamente (requiere factura electrónica)">
          <i class="bi bi-file-earmark-text"></i> Facturar (F5)
        </button>
        <button class="btn btn-success" :disabled="!puedeRegistrar || registrando" @click="registrar">
          <span v-if="registrando" class="spinner-border spinner-border-sm me-1"></span>
          <i class="bi bi-receipt" v-else></i> Recibo (F6)
        </button>
      </div>
    </template>

  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/apis'
import TurnoCajaModal from '@/components/pos/TurnoCajaModal.vue'
import { showToast } from '@/utils/toast'

const route  = useRoute()
const router = useRouter()
const orderNumber = route.params.orderNumber

const fmtCOP = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 })
const fmt = v => fmtCOP.format(v || 0)

const checkingTurno = ref(true)
const turnoAbierto   = ref(false)
const loading    = ref(true)
const errorCarga = ref('')
const registrando = ref(false)
const datos = ref(null)
const clientes = ref([])
const quitarPropina = ref(false)

const form = reactive({
  customer_id: null,
  waiter_id: 0,
  discount_percentage: 0,
  tip_amount: 0,
  delivery_amount: 0,
  observacion: '',
  payments: [{ payment_method_id: null, amount: 0 }],
})

async function verificarTurno() {
  checkingTurno.value = true
  try {
    const { data } = await api.get('/api/pos/turno/actual')
    turnoAbierto.value = !!data?.id
  } catch { turnoAbierto.value = false }
  checkingTurno.value = false
}
function onTurnoAbierto() { turnoAbierto.value = true }

async function cargar() {
  loading.value = true
  errorCarga.value = ''
  try {
    const { data } = await api.get(`/api/pos/pago/${orderNumber}`)
    datos.value = data
    form.customer_id = data.default_customer_id
    form.waiter_id = data.order.waiter_id || 0
    form.tip_amount = data.tip.suggested || 0
    const defaultPt = data.payment_types.find(p => p.is_default) || data.payment_types[0]
    form.payments = [{ payment_method_id: defaultPt?.id || null, amount: 0 }]
  } catch (e) {
    errorCarga.value = e?.response?.data?.detail ?? 'Error al cargar la cuenta'
  }
  loading.value = false
}

async function cargarClientes() {
  try {
    const { data } = await api.get('/clients')
    clientes.value = data
  } catch { clientes.value = [] }
}

const descuentoGeneralValor = computed(() => {
  if (!datos.value || datos.value.has_item_discount || !form.discount_percentage) return 0
  return Math.round(datos.value.subtotal * form.discount_percentage / 100)
})

const propinaEfectiva = computed(() => quitarPropina.value ? 0 : (form.tip_amount || 0))

const totalAPagar = computed(() => {
  if (!datos.value) return 0
  const base = datos.value.subtotal - descuentoGeneralValor.value
  return base + propinaEfectiva.value + (form.delivery_amount || 0)
})

const sumaPagos = computed(() => form.payments.reduce((s, p) => s + (Number(p.amount) || 0), 0))
const diferenciaPago = computed(() => Math.round(sumaPagos.value - totalAPagar.value))

const puedeRegistrar = computed(() =>
  !!datos.value && diferenciaPago.value === 0 && form.payments.every(p => p.payment_method_id) && totalAPagar.value >= 0
)

// Autocompleta el monto de la única forma de pago cuando cambia el total
watch(totalAPagar, (nuevo) => {
  if (form.payments.length === 1) form.payments[0].amount = nuevo
})

function agregarFormaPago() {
  const restante = Math.max(0, totalAPagar.value - sumaPagos.value)
  const defaultPt = datos.value?.payment_types?.[0]?.id || null
  form.payments.push({ payment_method_id: defaultPt, amount: restante })
}
function quitarFormaPago(idx) {
  if (form.payments.length === 1) return
  form.payments.splice(idx, 1)
}

async function registrar() {
  if (!puedeRegistrar.value) return
  registrando.value = true
  try {
    const { data } = await api.post(`/api/pos/pago/${orderNumber}`, {
      customer_id: form.customer_id,
      waiter_id: form.waiter_id || null,
      discount_percentage: datos.value.has_item_discount ? 0 : (form.discount_percentage || 0),
      tip_amount: propinaEfectiva.value,
      delivery_amount: form.delivery_amount || 0,
      observacion: form.observacion || null,
      payments: form.payments.map(p => ({ payment_method_id: p.payment_method_id, amount: p.amount })),
    })
    showToast(`Recibo Nro. ${data.receipt_number} registrado`, 'success')
    router.push('/restaurante')
  } catch (e) {
    showToast(e?.response?.data?.detail ?? 'Error al registrar el recibo', 'error')
  }
  registrando.value = false
}

onMounted(async () => {
  await verificarTurno()
  await Promise.all([cargar(), cargarClientes()])
})
</script>

<style scoped>
.pago-wrap { display: flex; flex-direction: column; height: 100%; background: #f8fafc; }
.pago-loading, .pago-error {
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px;
}

.pago-header {
  display: flex; align-items: center; gap: 12px; padding: 14px 16px;
  background: #fff; border-bottom: 1px solid #e2e8f0; flex-shrink: 0;
}
.pago-back {
  width: 36px; height: 36px; border-radius: 50%; border: 1px solid #e2e8f0; background: #fff;
  display: flex; align-items: center; justify-content: center; cursor: pointer; flex-shrink: 0;
}
.pago-header__info h1 { font-size: 16px; font-weight: 800; color: #1e293b; margin: 0; }
.pago-consecutivo { font-size: 12px; color: #64748b; }

.pago-body { flex: 1; overflow-y: auto; padding: 12px 16px 100px; display: flex; flex-direction: column; gap: 12px; }

.pago-card { background: #fff; border-radius: 12px; border: 1px solid #e2e8f0; padding: 14px; }
.pago-card__title { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .4px; color: #64748b; margin-bottom: 10px; display: flex; align-items: center; gap: 6px; }

.pago-item { display: flex; align-items: center; gap: 8px; padding: 6px 0; font-size: 14px; border-bottom: 1px solid #f1f5f9; }
.pago-item:last-child { border-bottom: none; }
.pago-item__qty { color: #64748b; font-weight: 700; }
.pago-item__name { flex: 1; color: #1e293b; }
.pago-item__amount { font-weight: 700; color: #1e293b; }

.pago-field { margin-bottom: 10px; }
.pago-field:last-child { margin-bottom: 0; }
.pago-field label { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: .3px; display: block; margin-bottom: 5px; }
.pago-field--row { display: flex; align-items: flex-end; gap: 12px; flex-wrap: wrap; }
.pago-field--row > div { flex: 1; min-width: 140px; }
.pago-check { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #475569; white-space: nowrap; padding-bottom: 8px; }

.pago-resumen__row { display: flex; justify-content: space-between; padding: 4px 0; font-size: 14px; color: #475569; }
.pago-resumen__total { border-top: 1px solid #e2e8f0; margin-top: 6px; padding-top: 10px; font-size: 16px; font-weight: 800; color: #1e293b; }

.pago-pago-row { display: flex; gap: 8px; margin-bottom: 8px; align-items: center; }
.pago-pago-row .form-select { flex: 1.4; }
.pago-pago-row .form-control { flex: 1; }
.pago-pago-del {
  width: 34px; height: 34px; flex-shrink: 0; border-radius: 8px; border: 1px solid #fecaca;
  background: #fef2f2; color: #ef4444; display: flex; align-items: center; justify-content: center; cursor: pointer;
}
.pago-pago-del:disabled { opacity: .4; cursor: not-allowed; }
.pago-pago-check { margin-top: 8px; font-size: 13px; font-weight: 700; padding: 6px 10px; border-radius: 8px; }
.pago-pago-check--ok  { background: #dcfce7; color: #166534; }
.pago-pago-check--bad { background: #fef2f2; color: #b91c1c; }

.pago-footer {
  position: sticky; bottom: 0; display: flex; gap: 10px; padding: 12px 16px;
  background: #fff; border-top: 1px solid #e2e8f0;
}
.pago-footer .btn { flex: 1; }

@media (max-width: 576px) {
  .pago-header__info h1 { font-size: 14px; }
  .pago-field--row { flex-direction: column; align-items: stretch; }
}
</style>
