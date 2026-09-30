<template>
  <div class="pg" ref="pgRef" :style="pgStyle">
    <TurnoCajaModal v-if="!checkingTurno && !turnoAbierto" @opened="onTurnoAbierto" />

    <div v-if="loading" class="pg-state"><div class="spinner-border text-primary"></div></div>
    <div v-else-if="errorCarga" class="pg-state">
      <i class="bi bi-exclamation-triangle fs-1 text-danger"></i>
      <p>{{ errorCarga }}</p>
      <button class="pg-btn pg-btn--sec" @click="$router.back()">Volver</button>
    </div>

    <template v-else-if="datos">
      <!-- ══ ENCABEZADO: cuenta · cliente · vendedor ══ -->
      <header class="pg-hdr">
        <button class="pg-back" @click="$router.back()" title="Volver"><i class="bi bi-arrow-left"></i></button>
        <div class="pg-hdr-cuenta">
          <div class="pg-mesa">{{ datos.order.table_name || 'Cuenta' }}</div>
          <div class="pg-rec">Recibo Nro. {{ datos.consecutivo_preview }} <small>(informativo)</small></div>
        </div>
        <button class="pg-hdr-field" @click="modalCliente = true" title="Cambiar cliente">
          <span class="pg-lbl">Cliente</span>
          <span class="pg-val"><i class="bi bi-person-badge"></i> {{ cliente.nombre }}</span>
        </button>
        <label class="pg-hdr-field">
          <span class="pg-lbl">Vendedor</span>
          <select v-model.number="form.waiter_id" class="pg-select">
            <option :value="0">— Sin vendedor —</option>
            <option v-for="w in datos.waiters" :key="w.id" :value="w.id">{{ w.name }}</option>
          </select>
        </label>
      </header>

      <div class="pg-main">
        <!-- ══ PANEL IZQUIERDO: descuento · propina · domicilio · observación · formas de pago ══ -->
        <section class="pg-left">
          <div class="pg-box">
            <div class="pg-box-ttl">Descuento</div>
            <select v-model.number="form.typification_id" class="pg-select" :disabled="!elegiblesDescuento.length">
              <option :value="0">{{ elegiblesDescuento.length ? '— Sin descuento —' : 'Ítems marcados ya tienen descuento' }}</option>
              <option v-for="t in datos.typifications" :key="t.id" :value="t.id">
                {{ t.name }}{{ t.percentage ? ` (${t.percentage}%)` : ' (en pesos)' }}
              </option>
            </select>
            <div v-if="tipSel && !tipSel.percentage" class="pg-inline">
              <span class="pg-lbl">Valor a descontar</span>
              <CurrencyInput v-model="form.monto_pesos" class="pg-input text-end" />
            </div>
            <input v-if="tipSel?.ask_notes" v-model="form.desc_obs" class="pg-input" maxlength="250" placeholder="Observación del descuento (obligatoria)" />
          </div>

          <div class="pg-box pg-actions">
            <template v-if="datos.tip.enabled">
              <label class="pg-chk" :class="{ on: form.tip_mode !== 'none' }">
                <input type="checkbox" :checked="form.tip_mode !== 'none'" @change="togglePropina($event.target.checked)" />
                {{ datos.tip.label }} {{ form.tip_mode === 'manual' ? '(manual)' : `${datos.tip.percentage}%` }}
              </label>
              <button class="pg-act" @click="abrirPropinaManual"><i class="bi bi-pencil"></i> {{ datos.tip.label }} manual</button>
            </template>
            <button class="pg-act" :class="{ on: form.delivery_amount > 0 }" @click="abrirDomicilio">
              <i class="bi bi-bicycle"></i> Domicilio<span v-if="form.delivery_amount"> · {{ fmt(form.delivery_amount) }}</span>
            </button>
            <button class="pg-act" :class="{ on: !!form.observacion }" @click="abrirObservacion">
              <i class="bi bi-chat-left-text"></i> Observación
            </button>
          </div>

          <div class="pg-box pg-pagos">
            <div class="pg-box-ttl">Formas de pago</div>
            <div v-for="(p, idx) in form.payments" :key="idx" class="pg-pago">
              <select v-model.number="p.payment_method_id" class="pg-select" @change="onFormaPago(p)">
                <option v-for="pt in datos.payment_types" :key="pt.id" :value="pt.id">{{ pt.name }}</option>
              </select>
              <CurrencyInput v-model="p.amount" class="pg-input text-end" />
              <button v-if="esEfectivo(p)" class="pg-ico" title="Billetes" @click="abrirEfectivo(p)"><i class="bi bi-cash-stack"></i></button>
              <button class="pg-ico pg-ico--del" :disabled="form.payments.length === 1" @click="form.payments.splice(idx, 1)"><i class="bi bi-trash"></i></button>
            </div>
            <button class="pg-link" @click="agregarFormaPago"><i class="bi bi-plus-lg"></i> Agregar forma de pago</button>
            <div :class="['pg-cubre', diferencia < 0 ? 'bad' : 'ok']">
              <template v-if="diferencia < 0">Falta {{ fmt(-diferencia) }}</template>
              <template v-else-if="diferencia > 0">Cambio {{ fmt(diferencia) }}</template>
              <template v-else><i class="bi bi-check-circle-fill"></i> Cubre el total</template>
            </div>
          </div>
        </section>

        <!-- ══ PANEL DERECHO: pestañas vista previa / pago parcial ══ -->
        <section class="pg-right">
          <div class="pg-tabs">
            <button :class="['pg-tab', { active: tab === 'previa' }]" @click="tab = 'previa'">Vista previa</button>
            <button :class="['pg-tab', { active: tab === 'parcial' }]" @click="tab = 'parcial'">
              Pago parcial <span class="pg-count">{{ seleccion.size }}/{{ datos.items.length }}</span>
            </button>
          </div>

          <div v-if="tab === 'previa'" class="pg-tabbody">
            <table class="pg-tbl">
              <thead><tr><th class="w-cant">Cant</th><th>Producto</th><th class="text-end">Vr. und</th><th class="text-end">Total</th></tr></thead>
              <tbody>
                <tr v-for="g in grupos" :key="g.key">
                  <td class="w-cant">{{ g.qty }}</td>
                  <td>
                    <div class="pg-prod">{{ g.name }}</div>
                    <div v-if="g.armado" class="pg-arm">{{ g.armado }}</div>
                  </td>
                  <td class="text-end">{{ fmt(g.unit) }}</td>
                  <td class="text-end fw">{{ fmt(g.total) }}</td>
                </tr>
                <tr v-if="!grupos.length"><td colspan="4" class="text-center text-muted">No hay ítems marcados</td></tr>
              </tbody>
            </table>
          </div>

          <div v-else class="pg-tabbody">
            <table class="pg-tbl">
              <thead>
                <tr>
                  <th class="w-chk"><input type="checkbox" :checked="todos" :indeterminate.prop="parcial" @change="marcarTodos($event.target.checked)" title="Marcar / desmarcar todos" /></th>
                  <th class="w-cant">Ítem</th><th>Producto</th><th class="text-end">Total</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="it in datos.items" :key="it.item" :class="{ off: !seleccion.has(it.item) }" @click="toggleItem(it.item)">
                  <td class="w-chk"><input type="checkbox" :checked="seleccion.has(it.item)" @click.stop="toggleItem(it.item)" /></td>
                  <td class="w-cant">{{ it.item }}</td>
                  <td>
                    <div class="pg-prod">{{ it.quantity !== 1 ? `${it.quantity} × ` : '' }}{{ it.name }}
                      <i v-if="it.typification_id" class="bi bi-percent text-success" title="Ya tiene descuento"></i></div>
                    <div v-if="it.armado.length" class="pg-arm">{{ it.armado.join(' - ') }}</div>
                  </td>
                  <td class="text-end fw">{{ fmt(valorItem(it)) }}</td>
                </tr>
              </tbody>
            </table>
            <div class="pg-parcial-foot">Marcado: <b>{{ fmt(venta) }}</b><span v-if="seleccion.size < datos.items.length"> · queda en la cuenta: {{ fmt(restanteCuenta) }}</span></div>
          </div>
        </section>
      </div>

      <!-- ══ PIE FIJO: valores + FACTURA / RECIBO ══ -->
      <footer class="pg-foot">
        <div class="pg-vals">
          <div class="pg-v"><span>Venta</span><b>{{ fmt(venta) }}</b></div>
          <div v-if="descuento" class="pg-v pg-v--neg"><span>Descuento</span><b>-{{ fmt(descuento) }}</b></div>
          <div v-if="datos.tip.enabled" class="pg-v"><span>{{ datos.tip.label }}</span><b>{{ fmt(propina) }}</b></div>
          <div class="pg-v"><span>Domicilio</span><b>{{ fmt(form.delivery_amount) }}</b></div>
          <div class="pg-v pg-v--total"><span>TOTAL</span><b>{{ fmt(total) }}</b></div>
        </div>
        <div class="pg-btns">
          <button class="pg-btn pg-btn--fac" :disabled="!datos.has_pos_electronico" @click="facturar"
                  :title="datos.has_pos_electronico ? '' : 'Factura electrónica no habilitada para esta empresa'">
            <i class="bi bi-file-earmark-text"></i> FACTURA (F5)
          </button>
          <button class="pg-btn pg-btn--rec" :disabled="!puedeRegistrar || registrando" @click="registrar">
            <span v-if="registrando" class="spinner-border spinner-border-sm"></span>
            <i v-else class="bi bi-receipt"></i> RECIBO (F6)
          </button>
        </div>
      </footer>
    </template>

    <!-- Cliente del recibo -->
    <ComandaClienteModal v-if="modalCliente" panel title="Cliente del recibo" :current-id="cliente.id_cliente"
                         @close="modalCliente = false" @select="c => { cliente = c; modalCliente = false }" />

    <!-- Cliente del domicilio (buscar o crear) -->
    <ComandaClienteModal v-if="dom.selCliente" panel title="Cliente del domicilio" :current-id="dom.cliente?.id_cliente || 0"
                         @close="dom.selCliente = false" @select="c => { dom.cliente = c; dom.selCliente = false }" />

    <!-- Modal genérico: propina manual / domicilio / observación -->
    <div v-if="modal.show" class="pg-ov" @click.self="cerrarModal">
      <div class="pg-modal">
        <div class="pg-modal-hdr">{{ modal.title }}<button class="pg-x" @click="cerrarModal"><i class="bi bi-x-lg"></i></button></div>
        <div class="pg-modal-body">
          <template v-if="modal.kind === 'propina'">
            <label class="pg-lbl">Valor de la {{ datos.tip.label.toLowerCase() }}</label>
            <CurrencyInput v-model="modal.value" class="pg-input pg-input--big text-end" />
          </template>
          <template v-else-if="modal.kind === 'domicilio'">
            <label class="pg-lbl">Cliente</label>
            <button class="pg-select pg-selbtn" @click="dom.selCliente = true">
              <i class="bi bi-person"></i> {{ dom.cliente?.nombre || 'Seleccionar o crear cliente' }}
            </button>
            <div v-if="dom.cliente?.direccion || dom.cliente?.telefono" class="pg-arm">{{ dom.cliente.direccion }} {{ dom.cliente.telefono }}</div>
            <label class="pg-lbl">Valor del domicilio</label>
            <CurrencyInput v-model="modal.value" class="pg-input pg-input--big text-end" />
          </template>
          <template v-else>
            <label class="pg-lbl">Observación del recibo</label>
            <textarea v-model="modal.text" class="pg-input" rows="4" maxlength="250"></textarea>
          </template>
        </div>
        <div class="pg-modal-ftr">
          <button v-if="modal.kind !== 'observacion'" class="pg-btn pg-btn--sec" @click="quitarModal">Quitar</button>
          <button class="pg-btn pg-btn--rec" @click="aceptarModal">Aceptar</button>
        </div>
      </div>
    </div>

    <!-- Efectivo: billetes rápidos + valor libre -->
    <div v-if="cash.show" class="pg-ov" @click.self="cash.show = false">
      <div class="pg-modal">
        <div class="pg-modal-hdr">Efectivo recibido<button class="pg-x" @click="cash.show = false"><i class="bi bi-x-lg"></i></button></div>
        <div class="pg-modal-body">
          <div class="cash-sum">
            <div><span>A cubrir</span><b>{{ fmt(cash.aCubrir) }}</b></div>
            <div><span>Recibido</span><b>{{ fmt(cash.recibido) }}</b></div>
            <div :class="cash.recibido >= cash.aCubrir ? 'ok' : 'bad'">
              <span>{{ cash.recibido >= cash.aCubrir ? 'Cambio' : 'Falta' }}</span><b>{{ fmt(Math.abs(cash.recibido - cash.aCubrir)) }}</b>
            </div>
          </div>
          <div class="cash-grid">
            <button v-for="b in datos.cash_denominations" :key="b.value"
                    :class="['cash-card', { 'cash-card--foto': b.image_path }]" @click="cash.recibido += b.value">
              <img v-if="b.image_path" :src="imgSrc(b.image_path)" class="cash-img" alt="" loading="lazy" />
              <i v-else class="bi bi-cash"></i>
              <span class="cash-val">{{ fmt(b.value) }}</span>
            </button>
            <button class="cash-card cash-card--exact" @click="cash.recibido = cash.aCubrir"><i class="bi bi-bullseye"></i>Exacto</button>
          </div>
          <div class="pg-inline">
            <span class="pg-lbl">Valor libre</span>
            <CurrencyInput v-model="cash.libre" class="pg-input text-end" />
            <button class="pg-btn pg-btn--sec" @click="cash.recibido += Number(cash.libre) || 0; cash.libre = 0">Sumar</button>
          </div>
          <p v-if="!datos.cash_denominations.length" class="pg-arm">Configure los billetes rápidos en Formas de Pago.</p>
        </div>
        <div class="pg-modal-ftr">
          <button class="pg-btn pg-btn--sec" @click="cash.recibido = 0">Limpiar</button>
          <button class="pg-btn pg-btn--rec" @click="aceptarEfectivo">Aceptar</button>
        </div>
      </div>
    </div>

    <!-- Vista previa del recibo: Imprimir (predeterminada) · PDF · Excel · Cancelar -->
    <ImprimirRecibo
      v-if="imprimir.show && imprimir.data"
      :receiptData="imprimir.data"
      :companyId="companyId"
      printersPath="/api/pos/recibo-impresion/impresoras"
      printPath="/api/pos/recibo-impresion/imprimir"
      @close="cerrarImpresion"
    />

    <!-- Cambio en grande (se cierra solo) -->
    <div v-if="cambioVisible" class="pg-ov pg-ov--cambio" @click="cerrarCambio">
      <div class="cambio-box">
        <div class="cambio-lbl">CAMBIO</div>
        <div class="cambio-val">{{ fmt(cambioValor) }}</div>
        <div class="cambio-sub">Recibo Nro. {{ ultimoRecibo }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/apis'
import TurnoCajaModal from '@/components/pos/TurnoCajaModal.vue'
import ComandaClienteModal from '@/components/comanda/ComandaClienteModal.vue'
import ImprimirRecibo from '@/components/billing/ImprimirRecibo.vue'
import { useCompanyStore } from '@/stores/companyStore'
import { showToast } from '@/utils/toast'

const route  = useRoute()
const router = useRouter()
const orderNumber = route.params.orderNumber

const fmtCOP = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })
const fmt = v => fmtCOP.format(Math.round(Number(v) || 0))

const checkingTurno = ref(true)
const turnoAbierto  = ref(false)
const loading       = ref(true)
const errorCarga    = ref('')
const registrando   = ref(false)
const datos         = ref(null)
const companyStore  = useCompanyStore()
const companyId     = computed(() => companyStore.selectedCompany?.id || 0)
const cliente       = ref({ id_cliente: 1, nombre: 'Consumidor Final' })
const tab           = ref('previa')
const seleccion     = ref(new Set())
const modalCliente  = ref(false)

const form = reactive({
  waiter_id: 0, typification_id: 0, monto_pesos: 0, desc_obs: '',
  tip_mode: 'auto', tip_manual: 0, delivery_amount: 0, observacion: '',
  payments: [],
})
const dom   = reactive({ cliente: null, selCliente: false })
const modal = reactive({ show: false, kind: '', title: '', value: 0, text: '', continuar: false })
const cash  = reactive({ show: false, linea: null, aCubrir: 0, recibido: 0, libre: 0 })
const cambioVisible = ref(false)
const cambioValor   = ref(0)
const ultimoRecibo  = ref('')
let cambioTimer = null
const API_BASE = import.meta.env.VITE_API_URL || ''
const imgSrc = u => (!u || /^(https?:|blob:|data:)/.test(u)) ? u : API_BASE + u
// Impresión del recibo recién registrado (vista previa con la impresora predeterminada)
const imprimir = reactive({ show: false, data: null, luego: null })
let propinaPreguntada = false

// ── Carga ──────────────────────────────────────────────────────────────────
async function verificarTurno() {
  checkingTurno.value = true
  try { turnoAbierto.value = !!(await api.get('/api/pos/turno/actual')).data?.id }
  catch { turnoAbierto.value = false }
  checkingTurno.value = false
}
function onTurnoAbierto() { turnoAbierto.value = true; cargar() }

async function cargar() {
  loading.value = true
  errorCarga.value = ''
  try {
    const { data } = await api.get(`/api/pos/pago/${orderNumber}`)
    datos.value = data
    cliente.value = data.customer
    form.waiter_id = data.order.waiter_id || 0
    form.typification_id = 0; form.monto_pesos = 0; form.desc_obs = ''
    form.tip_mode = data.tip.enabled ? 'auto' : 'none'
    propinaPreguntada = false
    seleccion.value = new Set(data.items.map(i => i.item))       // todo marcado por defecto
    const def = data.payment_types.find(p => p.is_default) || data.payment_types[0]
    form.payments = [{ payment_method_id: def?.id || null, amount: 0, auto: true }]
  } catch (e) {
    errorCarga.value = e?.response?.data?.detail ?? 'Error al cargar la cuenta'
  }
  loading.value = false
}

// ── Selección (pago parcial) ─────────────────────────────────────────────────
const todos   = computed(() => datos.value && seleccion.value.size === datos.value.items.length)
const parcial = computed(() => datos.value && seleccion.value.size > 0 && !todos.value)
function toggleItem(n) {
  const s = new Set(seleccion.value)
  s.has(n) ? s.delete(n) : s.add(n)
  seleccion.value = s
}
function marcarTodos(v) { seleccion.value = new Set(v ? datos.value.items.map(i => i.item) : []) }
const marcados = computed(() => (datos.value?.items || []).filter(i => seleccion.value.has(i.item)))

// ── Descuento (misma lógica que el servidor, solo para mostrar) ─────────────
const tipSel = computed(() => datos.value?.typifications.find(t => t.id === form.typification_id) || null)
const elegiblesDescuento = computed(() => marcados.value.filter(i => !i.typification_id && i.amount > 0))
const valoresConDescuento = computed(() => {
  const v = Object.fromEntries(marcados.value.map(i => [i.item, i.amount]))
  const t = tipSel.value
  const eleg = elegiblesDescuento.value
  if (!t || !eleg.length) return v
  if (t.percentage) {
    for (const i of eleg) v[i.item] = Math.max(0, Math.round(i.original_amount * (1 - t.percentage / 100)))
  } else {
    const monto = Math.round(Number(form.monto_pesos) || 0)
    const base = eleg.reduce((s, i) => s + v[i.item], 0)
    if (monto > 0 && monto <= base) {
      let resto = monto
      eleg.forEach((i, k) => {
        let parte = k === eleg.length - 1 ? resto : Math.round(monto * v[i.item] / base)
        parte = Math.min(parte, v[i.item], resto)
        v[i.item] -= parte
        resto -= parte
      })
    }
  }
  return v
})
const valorItem = it => seleccion.value.has(it.item) ? (valoresConDescuento.value[it.item] ?? it.amount) : it.amount

// ── Totales ──────────────────────────────────────────────────────────────────
const venta     = computed(() => marcados.value.reduce((s, i) => s + (valoresConDescuento.value[i.item] ?? i.amount), 0))
const descuento = computed(() => marcados.value.reduce((s, i) => s + (i.original_amount - (valoresConDescuento.value[i.item] ?? i.amount)), 0))
const propina   = computed(() => {
  if (!datos.value?.tip.enabled || form.tip_mode === 'none') return 0
  if (form.tip_mode === 'manual') return Math.round(Number(form.tip_manual) || 0)
  return Math.round(venta.value * datos.value.tip.percentage / 100)
})
const total = computed(() => venta.value + propina.value + Math.round(Number(form.delivery_amount) || 0))
const restanteCuenta = computed(() => (datos.value?.items || []).filter(i => !seleccion.value.has(i.item)).reduce((s, i) => s + i.amount, 0))
const pagado     = computed(() => form.payments.reduce((s, p) => s + (Math.round(Number(p.amount)) || 0), 0))
const diferencia = computed(() => pagado.value - total.value)

// Vista previa agrupada por producto + armado + valor unitario
const grupos = computed(() => {
  const map = new Map()
  for (const i of marcados.value) {
    const val = valoresConDescuento.value[i.item] ?? i.amount
    const unit = i.quantity ? Math.round(val / i.quantity) : val
    const armado = i.armado.join(' - ')
    const key = `${i.name}|${armado}|${unit}`
    const g = map.get(key) || { key, name: i.name, armado, unit, qty: 0, total: 0 }
    g.qty += i.quantity; g.total += val
    map.set(key, g)
  }
  return [...map.values()]
})

// La única forma de pago "automática" sigue al total mientras el cajero no la edite
watch(total, t => { if (form.payments.length === 1 && form.payments[0].auto) form.payments[0].amount = t }, { immediate: true })
watch(() => form.payments.map(p => p.amount), (nv, ov) => {
  if (!ov) return
  form.payments.forEach((p, i) => { if (ov[i] !== undefined && nv[i] !== ov[i] && nv[i] !== total.value) p.auto = false })
})

const tipoPago = id => datos.value?.payment_types.find(p => p.id === id)
const esEfectivo = p => !!tipoPago(p.payment_method_id)?.adds_to_cash

const puedeRegistrar = computed(() =>
  !!datos.value && seleccion.value.size > 0 && total.value >= 0 && diferencia.value >= 0 &&
  form.payments.every(p => p.payment_method_id) &&
  (!tipSel.value || elegiblesDescuento.value.length) &&
  (!tipSel.value?.ask_notes || form.desc_obs.trim()) &&
  (!tipSel.value || tipSel.value.percentage || (form.monto_pesos > 0 && descuento.value > 0))
)

// ── Formas de pago ───────────────────────────────────────────────────────────
function agregarFormaPago() {
  const restante = Math.max(0, total.value - pagado.value)
  const def = datos.value.payment_types[0]
  form.payments.forEach(p => { p.auto = false })
  form.payments.push({ payment_method_id: def?.id || null, amount: restante, auto: false })
}
function onFormaPago(p) { if (esEfectivo(p)) abrirEfectivo(p) }
function abrirEfectivo(p) {
  const otros = form.payments.filter(x => x !== p).reduce((s, x) => s + (Math.round(Number(x.amount)) || 0), 0)
  cash.linea = p; cash.aCubrir = Math.max(0, total.value - otros); cash.recibido = 0; cash.libre = 0; cash.show = true
}
function aceptarEfectivo() {
  if (cash.linea) { cash.linea.amount = cash.recibido || cash.aCubrir; cash.linea.auto = false }
  cash.show = false
}

// ── Propina / domicilio / observación ────────────────────────────────────────
function togglePropina(on) { form.tip_mode = on ? 'auto' : 'none' }
function abrirPropinaManual() { Object.assign(modal, { show: true, kind: 'propina', title: `${datos.value.tip.label} manual`, value: propina.value }) }
function abrirDomicilio() {
  if (!dom.cliente) dom.cliente = cliente.value.id_cliente !== 1 ? cliente.value : null
  Object.assign(modal, { show: true, kind: 'domicilio', title: 'Domicilio', value: form.delivery_amount })
}
function abrirObservacion() { Object.assign(modal, { show: true, kind: 'observacion', title: 'Observación', text: form.observacion }) }
function aceptarModal() {
  if (modal.kind === 'propina') { form.tip_manual = Math.round(Number(modal.value) || 0); form.tip_mode = 'manual'; propinaPreguntada = true }
  else if (modal.kind === 'domicilio') {
    if ((Number(modal.value) || 0) > 0 && !dom.cliente) { showToast('Seleccione el cliente del domicilio', 'warning'); return }
    form.delivery_amount = Math.round(Number(modal.value) || 0)
  } else form.observacion = (modal.text || '').trim()
  modal.show = false
  if (modal.continuar) { modal.continuar = false; registrar() }
}
// Cerrar con la X o por fuera: no registra (si venía de RECIBO, se cancela el registro)
function cerrarModal() { modal.show = false; modal.continuar = false }
function quitarModal() {
  if (modal.kind === 'propina') { form.tip_mode = 'none'; propinaPreguntada = true }
  if (modal.kind === 'domicilio') { form.delivery_amount = 0; dom.cliente = null }
  modal.show = false
  if (modal.continuar) { modal.continuar = false; registrar() }
}

// ── Registrar ────────────────────────────────────────────────────────────────
function facturar() { showToast('La factura electrónica desde esta pantalla se habilita en la siguiente fase', 'info') }

async function registrar() {
  if (!puedeRegistrar.value || registrando.value || imprimir.show) return
  // Config. Facturación → "Preguntar valor propina": se confirma el valor antes de asentar
  if (datos.value.tip.enabled && datos.value.tip.ask_value && form.tip_mode === 'auto' && !propinaPreguntada) {
    Object.assign(modal, { show: true, kind: 'propina', title: `¿Valor de ${datos.value.tip.label}?`, value: propina.value, continuar: true })
    return
  }
  registrando.value = true
  try {
    const { data } = await api.post(`/api/pos/pago/${orderNumber}`, {
      items: [...seleccion.value],
      customer_id: cliente.value.id_cliente,
      waiter_id: form.waiter_id || null,
      descuento: tipSel.value ? {
        typification_id: tipSel.value.id,
        monto_pesos: tipSel.value.percentage ? null : Math.round(Number(form.monto_pesos) || 0),
        observacion: form.desc_obs.trim() || null,
      } : null,
      tip_mode: form.tip_mode,
      tip_amount: form.tip_mode === 'manual' ? form.tip_manual : null,
      delivery_amount: form.delivery_amount || 0,
      delivery_customer_id: form.delivery_amount ? (dom.cliente?.id_cliente || null) : null,
      observacion: form.observacion || null,
      payments: form.payments.filter(p => Number(p.amount) > 0)
        .map(p => ({ payment_method_id: p.payment_method_id, amount: Math.round(Number(p.amount)) })),
    })
    ultimoRecibo.value = data.receipt_number
    const siguiente = () => {
      if (data.remaining_items > 0) {
        showToast(`Recibo ${data.receipt_number} registrado · quedan ${data.remaining_items} ítem(s) en la cuenta`, 'success')
        cargar()
      } else {
        showToast(`Recibo Nro. ${data.receipt_number} registrado`, 'success')
        router.push('/restaurante')
      }
    }
    const previa = () => abrirImpresion(data.receipt_number, siguiente)
    if (data.change > 0) mostrarCambio(data.change, previa)
    else previa()
  } catch (e) {
    showToast(e?.response?.data?.detail ?? 'Error al registrar el recibo', 'error')
  }
  registrando.value = false
}

async function abrirImpresion(receiptNumber, luego) {
  try {
    const { data } = await api.get(`/api/pos/recibo-impresion/${encodeURIComponent(receiptNumber)}`)
    Object.assign(imprimir, { show: true, data, luego })
  } catch {
    showToast('No se pudo cargar la vista previa del recibo', 'warning')
    luego()
  }
}
function cerrarImpresion() {
  const f = imprimir.luego
  Object.assign(imprimir, { show: false, data: null, luego: null })
  if (f) f()
}

let despuesCambio = null
function mostrarCambio(valor, luego) {
  cambioValor.value = valor; cambioVisible.value = true; despuesCambio = luego
  clearTimeout(cambioTimer)
  cambioTimer = setTimeout(cerrarCambio, 5000)
}
function cerrarCambio() {
  clearTimeout(cambioTimer)
  if (!cambioVisible.value) return
  cambioVisible.value = false
  const f = despuesCambio; despuesCambio = null
  if (f) f()
}

// ── Atajos F5 / F6 ───────────────────────────────────────────────────────────
function onKey(e) {
  if (imprimir.show) return
  if (e.key === 'F6') { e.preventDefault(); registrar() }
  else if (e.key === 'F5') { e.preventDefault(); if (datos.value?.has_pos_electronico) facturar() }
  else if (e.key === 'Escape' && cambioVisible.value) cerrarCambio()
}

// La vista ocupa exactamente el alto visible: solo se desplazan las listas internas
const pgRef   = ref(null)
const pgStyle = ref({})
function ajustarAlto() {
  const el = pgRef.value
  if (!el) return
  const top    = el.getBoundingClientRect().top + (el.closest('.content')?.scrollTop || 0)
  const footer = document.querySelector('.footer')?.offsetHeight || 0
  pgStyle.value = { height: `${Math.max(420, window.innerHeight - top - footer)}px` }
}

onMounted(async () => {
  window.addEventListener('keydown', onKey)
  window.addEventListener('resize', ajustarAlto)
  ajustarAlto()
  await verificarTurno()
  if (turnoAbierto.value) await cargar()
  else loading.value = false
})
onBeforeUnmount(() => { window.removeEventListener('keydown', onKey); window.removeEventListener('resize', ajustarAlto); clearTimeout(cambioTimer) })
</script>

<style scoped>
.pg { display: flex; flex-direction: column; height: calc(100dvh - 120px); min-height: 0; overflow: hidden; margin-bottom: -40px; background: #f1f5f9; }
.pg-state { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; }

/* Encabezado */
.pg-hdr { display: flex; align-items: center; gap: 12px; padding: 10px 16px; background: #fff; border-bottom: 1px solid #e2e8f0; flex-shrink: 0; flex-wrap: wrap; }
.pg-back { width: 36px; height: 36px; border-radius: 50%; border: 1px solid #e2e8f0; background: #fff; cursor: pointer; flex-shrink: 0; }
.pg-hdr-cuenta { min-width: 140px; }
.pg-mesa { font-size: 17px; font-weight: 800; color: #1e293b; }
.pg-rec { font-size: 12px; color: #64748b; }
.pg-hdr-field { display: flex; flex-direction: column; gap: 2px; flex: 1; min-width: 180px; max-width: 320px; background: none; border: none; text-align: left; padding: 0; cursor: pointer; }
.pg-lbl { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: .3px; }
.pg-val { border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 7px 10px; font-size: 14px; font-weight: 600; color: #1d4ed8; background: #eff6ff; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pg-select, .pg-input { width: 100%; border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 7px 10px; font-size: 14px; background: #fff; color: #1e293b; }
.pg-input--big { font-size: 22px; font-weight: 800; }
.pg-selbtn { text-align: left; cursor: pointer; }

/* Cuerpo: dos paneles */
.pg-main { flex: 1; min-height: 0; display: grid; grid-template-columns: 380px 1fr; gap: 12px; padding: 12px 16px; }
.pg-left { display: flex; flex-direction: column; gap: 10px; min-height: 0; overflow-y: auto; }
.pg-box { background: #fff; border-radius: 12px; border: 1px solid #e2e8f0; padding: 10px 12px; display: flex; flex-direction: column; gap: 8px; }
.pg-box-ttl { font-size: 11px; font-weight: 800; color: #64748b; text-transform: uppercase; letter-spacing: .4px; }
.pg-inline { display: flex; align-items: center; gap: 8px; }
.pg-inline .pg-lbl { white-space: nowrap; }
.pg-actions { flex-direction: row; flex-wrap: wrap; }
.pg-act, .pg-chk { display: inline-flex; align-items: center; gap: 6px; border: 1.5px solid #cbd5e1; background: #fff; border-radius: 8px; padding: 7px 10px; font-size: 13px; font-weight: 600; color: #334155; cursor: pointer; }
.pg-act.on, .pg-chk.on { border-color: #16a34a; background: #f0fdf4; color: #15803d; }
.pg-pagos { flex: 1; min-height: 140px; }
.pg-pago { display: grid; grid-template-columns: 1.3fr 1fr auto auto; gap: 6px; align-items: center; }
.pg-ico { width: 34px; height: 34px; border-radius: 8px; border: 1.5px solid #bbf7d0; background: #f0fdf4; color: #15803d; cursor: pointer; }
.pg-ico--del { border-color: #fecaca; background: #fef2f2; color: #dc2626; }
.pg-ico:disabled { opacity: .4; cursor: not-allowed; }
.pg-link { background: none; border: none; color: #1d4ed8; font-weight: 700; font-size: 13px; text-align: left; cursor: pointer; padding: 2px 0; }
.pg-cubre { font-size: 13px; font-weight: 800; padding: 6px 10px; border-radius: 8px; }
.pg-cubre.ok { background: #dcfce7; color: #166534; }
.pg-cubre.bad { background: #fef2f2; color: #b91c1c; }

.pg-right { background: #fff; border-radius: 12px; border: 1px solid #e2e8f0; display: flex; flex-direction: column; min-height: 0; overflow: hidden; }
.pg-tabs { display: flex; border-bottom: 2px solid #e2e8f0; flex-shrink: 0; }
.pg-tab { flex: 1; padding: 10px; border: none; background: none; font-weight: 700; font-size: 13px; color: #64748b; border-bottom: 3px solid transparent; margin-bottom: -2px; cursor: pointer; }
.pg-tab.active { color: #1d4ed8; border-bottom-color: #1d4ed8; }
.pg-count { font-size: 11px; background: #eff6ff; color: #1d4ed8; border-radius: 999px; padding: 1px 8px; margin-left: 4px; }
.pg-tabbody { flex: 1; min-height: 0; overflow-y: auto; }
.pg-tbl { width: 100%; border-collapse: collapse; font-size: 13px; }
.pg-tbl th { position: sticky; top: 0; background: #f8fafc; color: #475569; font-size: 11px; text-transform: uppercase; padding: 8px 10px; border-bottom: 1px solid #e2e8f0; text-align: left; z-index: 1; }
.pg-tbl td { padding: 8px 10px; border-bottom: 1px solid #f1f5f9; vertical-align: top; }
.pg-tbl tbody tr { cursor: default; }
.pg-tabbody .pg-tbl tbody tr.off td { opacity: .45; }
.w-cant { width: 56px; } .w-chk { width: 34px; }
.pg-tbl input[type=checkbox] { width: 17px; height: 17px; cursor: pointer; }
.pg-prod { font-weight: 600; color: #1e293b; }
.pg-arm { font-size: 11px; color: #64748b; }
.fw { font-weight: 700; }
.text-end { text-align: right; } .text-center { text-align: center; } .text-muted { color: #94a3b8; }
.pg-parcial-foot { position: sticky; bottom: 0; background: #fffbeb; border-top: 1px solid #fde68a; padding: 8px 12px; font-size: 13px; color: #92400e; }

/* Pie fijo */
.pg-foot { display: flex; align-items: center; gap: 12px; padding: 10px 16px; background: #fff; border-top: 1px solid #e2e8f0; flex-shrink: 0; }
.pg-vals { flex: 1; display: flex; gap: 8px; flex-wrap: wrap; }
.pg-v { display: flex; flex-direction: column; background: #f8fafc; border-radius: 10px; padding: 6px 12px; min-width: 110px; }
.pg-v span { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; }
.pg-v b { font-size: 16px; color: #1e293b; }
.pg-v--neg b { color: #dc2626; }
.pg-v--total { background: #1e3a5f; }
.pg-v--total span { color: #bfdbfe; }
.pg-v--total b { color: #fff; font-size: 20px; }
.pg-btns { display: flex; gap: 8px; }
.pg-btn { display: inline-flex; align-items: center; justify-content: center; gap: 6px; border: none; border-radius: 10px; padding: 12px 18px; font-size: 14px; font-weight: 800; cursor: pointer; white-space: nowrap; }
.pg-btn:disabled { opacity: .5; cursor: not-allowed; }
.pg-btn--rec { background: #16a34a; color: #fff; }
.pg-btn--fac { background: #fff; color: #1d4ed8; border: 1.5px solid #bfdbfe; }
.pg-btn--sec { background: #f1f5f9; color: #475569; }

/* Modales */
.pg-ov { position: fixed; inset: 0; background: rgba(0,0,0,.5); display: flex; align-items: center; justify-content: center; z-index: 1100; padding: 16px; }
.pg-modal { background: #fff; border-radius: 16px; width: 100%; max-width: 520px; max-height: 90vh; display: flex; flex-direction: column; overflow: hidden; }
.pg-modal-hdr { display: flex; justify-content: space-between; align-items: center; padding: 14px 16px; font-weight: 800; color: #1e293b; border-bottom: 1px solid #f1f5f9; }
.pg-x { background: none; border: none; color: #94a3b8; font-size: 16px; cursor: pointer; }
.pg-modal-body { padding: 14px 16px; display: flex; flex-direction: column; gap: 8px; overflow-y: auto; }
.pg-modal-ftr { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 16px; border-top: 1px solid #f1f5f9; }
.cash-sum { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; }
.cash-sum > div { background: #f8fafc; border-radius: 10px; padding: 8px; display: flex; flex-direction: column; }
.cash-sum span { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; }
.cash-sum b { font-size: 16px; }
.cash-sum .ok b { color: #15803d; } .cash-sum .bad b { color: #dc2626; }
.cash-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.cash-card { display: flex; flex-direction: column; align-items: center; gap: 4px; border: 2px solid #bbf7d0; background: #f0fdf4; color: #14532d; border-radius: 12px; padding: 14px 6px; font-size: 16px; font-weight: 800; cursor: pointer; }
.cash-card i { font-size: 20px; }
.cash-card--foto { padding: 6px; gap: 2px; }
.cash-img { width: 100%; height: 64px; object-fit: cover; border-radius: 8px; }
.cash-val { line-height: 1.2; }
.cash-card--exact { border-color: #bfdbfe; background: #eff6ff; color: #1d4ed8; }
.pg-ov--cambio { background: rgba(15,23,42,.8); cursor: pointer; }
.cambio-box { background: #16a34a; color: #fff; border-radius: 24px; padding: 40px 60px; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,.4); }
.cambio-lbl { font-size: 22px; font-weight: 800; letter-spacing: 4px; opacity: .9; }
.cambio-val { font-size: 64px; font-weight: 900; line-height: 1.1; }
.cambio-sub { font-size: 14px; opacity: .85; margin-top: 8px; }

/* Tablet */
@media (max-width: 1024px) {
  .pg-main { grid-template-columns: 320px 1fr; }
  .pg-v { min-width: 90px; padding: 6px 8px; }
  .pg-btn { padding: 10px 12px; }
}
/* Móvil: todo en columna, pie fijo con valores y botones */
@media (max-width: 768px) {
  .pg-hdr-field { max-width: none; min-width: 100%; }
  .pg-main { display: flex; flex-direction: column; overflow-y: auto; padding: 10px; }
  .pg-left { overflow: visible; flex-shrink: 0; }
  .pg-right { flex-shrink: 0; height: 62dvh; min-height: 300px; }
  .pg-foot { flex-direction: column; align-items: stretch; position: sticky; bottom: 0; }
  .pg-vals { gap: 6px; }
  .pg-v { flex: 1; min-width: 30%; }
  .pg-btns .pg-btn { flex: 1; }
  .pg-ov { padding: 0; align-items: flex-end; }
  .pg-modal { border-radius: 16px 16px 0 0; max-width: 100%; }
  .pg-ov--cambio { align-items: center; padding: 16px; }
  .cambio-box { padding: 30px 24px; }
  .cambio-val { font-size: 48px; }
  .cash-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 576px) {
  .pg-mesa { font-size: 15px; }
  .pg-pago { grid-template-columns: 1fr 1fr auto auto; }
  .cash-grid { grid-template-columns: repeat(2, 1fr); }
  .pg-v b { font-size: 14px; }
  .pg-v--total b { font-size: 17px; }
}
</style>
