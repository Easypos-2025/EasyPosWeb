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
        <button :class="['pg-hdr-field', { 'pg-hdr-field--locked': clienteFijo }]" @click="abrirClienteRecibo"
                :title="clienteFijo ? 'El pedido se montó con la lista de este cliente: se factura a él' : 'Cambiar cliente'">
          <span class="pg-lbl">Cliente</span>
          <span class="pg-val"><i :class="clienteFijo ? 'bi bi-lock-fill' : 'bi bi-person-badge'"></i> {{ cliente.nombre }}</span>
        </button>
        <label class="pg-hdr-field">
          <span class="pg-lbl">Vendedor</span>
          <select v-model.number="form.waiter_id" class="pg-select">
            <option :value="0">— Sin vendedor —</option>
            <option v-for="w in $ordenAlfa(datos.waiters, 'name')" :key="w.id" :value="w.id">{{ w.name }}</option>
          </select>
        </label>
      </header>
      <div v-if="datos.turno && !datos.turno.es_de_hoy" class="pg-fecha-turno">
        <i class="bi bi-calendar-event"></i>
        El recibo se registrará con la <b>fecha de apertura de la caja: {{ fmtFechaTurno(datos.turno.fecha) }}</b>
        ({{ datos.turno.caja }} · Id_Caja #{{ datos.turno.id }}), no con la fecha actual.
      </div>

      <div class="pg-main">
        <!-- ══ PANEL IZQUIERDO: descuento · propina · domicilio · observación · formas de pago ══ -->
        <section class="pg-left">
          <div v-if="permisosRol.tiene('realizar_descuentos')" class="pg-box">
            <div class="pg-box-ttl">Descuento</div>
            <select v-model.number="form.typification_id" class="pg-select" :disabled="!elegiblesDescuento.length">
              <option :value="0">{{ elegiblesDescuento.length ? '— Sin descuento —' : 'Ítems marcados ya tienen descuento' }}</option>
              <option v-for="t in $ordenAlfa(datos.typifications, 'name')" :key="t.id" :value="t.id">
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
                <input type="checkbox" :checked="form.tip_mode !== 'none'" :disabled="!puedePropina"
                       @change="togglePropina($event.target.checked)" />
                {{ datos.tip.label }} {{ form.tip_mode === 'manual' ? '(manual)' : `${datos.tip.percentage}%` }}
              </label>
              <button v-if="puedePropina" class="pg-act" @click="abrirPropinaManual"><i class="bi bi-pencil"></i> {{ datos.tip.label }} manual</button>
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
              <select v-model.number="p.payment_method_id" class="pg-select">
                <option v-for="pt in $ordenAlfa(datos.payment_types, 'name')" :key="pt.id" :value="pt.id">{{ pt.name }}</option>
              </select>
              <CurrencyInput v-model="p.amount" class="pg-input text-end" />
              <button class="pg-ico pg-ico--del" :disabled="form.payments.length === 1" @click="form.payments.splice(idx, 1)"><i class="bi bi-trash"></i></button>
            </div>
            <button class="pg-link" @click="agregarFormaPago"><i class="bi bi-plus-lg"></i> Agregar forma de pago</button>
            <div :class="['pg-cubre', diferencia === 0 && seleccion.size ? 'ok' : 'bad']">
              <template v-if="!seleccion.size">Marque los ítems a pagar</template>
              <template v-else-if="diferencia < 0">Falta {{ fmt(-diferencia) }}</template>
              <template v-else-if="diferencia > 0">Supera el total en {{ fmt(diferencia) }}</template>
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
                <tr v-for="it in $ordenItemDesc(datos.items)" :key="it.item" :class="{ off: !seleccion.has(it.item) }" @click="toggleItem(it.item)">
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
          <button class="pg-btn pg-btn--fac" :disabled="!datos.has_pos_electronico || !puedeRegistrar" @click="facturar"
                  :title="datos.has_pos_electronico ? '' : 'Factura electrónica no habilitada para esta empresa'">
            <i class="bi bi-file-earmark-text"></i> FACTURA (F5)
          </button>
          <button class="pg-btn pg-btn--rec" :disabled="!puedeRegistrar || registrando || !permisosRol.tiene('generar_recibo')"
                  :title="permisosRol.tiene('generar_recibo') ? '' : 'Su rol no tiene permiso para generar recibos'" @click="registrar">
            <span v-if="registrando" class="spinner-border spinner-border-sm"></span>
            <i v-else class="bi bi-receipt"></i> RECIBO (F6)
          </button>
          <button v-if="datos.use_precuenta" class="pg-btn pg-btn--pre" :disabled="!seleccion.size || cargandoPrecuenta" @click="cuentaPrevia">
            <span v-if="cargandoPrecuenta" class="spinner-border spinner-border-sm"></span>
            <i v-else class="bi bi-file-earmark-ruled"></i> CUENTA PREVIA
          </button>
          <button class="pg-btn pg-btn--sec" @click="salir"><i class="bi bi-box-arrow-left"></i> SALIR</button>
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

    <!-- ¿Con cuánto paga el cliente? — el cambio se calcula en la misma ventana -->
    <div v-if="cash.show" class="pg-ov" @click.self="cash.show = false">
      <div class="pg-modal pg-modal--cash">
        <div class="pg-modal-hdr">Pago en efectivo<button class="pg-x" @click="cash.show = false"><i class="bi bi-x-lg"></i></button></div>
        <div class="pg-modal-body">
          <div class="cash-apagar"><span>Efectivo a pagar</span><b>{{ fmt(cash.aPagar) }}</b></div>
          <label class="cash-q" for="cash-recibido">¿Con cuánto paga el cliente?</label>
          <CurrencyInput id="cash-recibido" ref="cashInput" v-model="cash.recibido" class="pg-input cash-inp text-end"
                         @keyup.enter="confirmarEfectivo" />
          <div class="cash-grid">
            <button v-for="b in datos.cash_denominations" :key="b.value"
                    :class="['cash-card', { 'cash-card--foto': b.image_path }]" @click="cash.recibido = (Number(cash.recibido) || 0) + b.value">
              <img v-if="b.image_path" :src="imgSrc(b.image_path)" class="cash-img" alt="" loading="lazy" />
              <i v-else class="bi bi-cash"></i>
              <span class="cash-val">+ {{ fmt(b.value) }}</span>
            </button>
            <button class="cash-card cash-card--exact" @click="cash.recibido = cash.aPagar"><i class="bi bi-bullseye"></i>Exacto</button>
          </div>
          <div :class="['cash-cambio', cashRecibido >= cash.aPagar ? 'ok' : 'bad']">
            <span>{{ cashRecibido >= cash.aPagar ? 'CAMBIO' : 'FALTA' }}</span>
            <b>{{ fmt(Math.abs(cashRecibido - cash.aPagar)) }}</b>
          </div>
        </div>
        <div class="pg-modal-ftr">
          <button class="pg-btn pg-btn--sec" @click="cash.recibido = 0">Limpiar</button>
          <button class="pg-btn pg-btn--rec" :disabled="cashRecibido < cash.aPagar || registrando" @click="confirmarEfectivo">
            <span v-if="registrando" class="spinner-border spinner-border-sm"></span>
            <i v-else class="bi bi-receipt"></i> Registrar recibo
          </button>
        </div>
      </div>
    </div>

    <!-- Vista previa del recibo: Imprimir (predeterminada) · PDF · Excel · Cancelar -->
    <ImprimirRecibo
      v-if="imprimir.show && imprimir.data"
      :receiptData="imprimir.data"
      :companyId="companyId"
      printersPath="/api/pos/recibo-impresion/impresoras"
      :printPath="imprimir.printPath"
      :printExtra="imprimir.printExtra"
      :obligar="imprimir.obligar"
      @close="cerrarImpresion"
    />

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
import { useMesaLock } from '@/composables/useMesaLock'
import { showToast } from '@/utils/toast'
import { usePermisos } from '@/composables/usePermisos'
// Control de Acceso del rol (el servidor también valida)
const permisosRol = usePermisos()

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
const fmtFechaTurno = d => { if (!d) return ''; const [y, m, dd] = String(d).split('-'); return `${dd}/${m}/${y}` }
// Pedido montado con la lista de un cliente (≠ Consumidor Final): se factura a ese cliente
const clienteFijo   = computed(() => (datos.value?.customer?.id_cliente || 1) !== 1)
function abrirClienteRecibo() {
  if (clienteFijo.value) {
    showToast('El pedido se montó con la lista de precios de este cliente. Si está mal, elimine el pedido y móntelo de nuevo.', 'warning', 4500)
    return
  }
  modalCliente.value = true
}
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
const cash  = reactive({ show: false, aPagar: 0, recibido: 0 })
const cashInput = ref(null)
const cashRecibido = computed(() => Math.round(Number(cash.recibido) || 0))
const cargandoPrecuenta = ref(false)
const API_BASE = import.meta.env.VITE_API_URL || ''
const imgSrc = u => (!u || /^(https?:|blob:|data:)/.test(u)) ? u : API_BASE + u
// Impresión del recibo recién registrado (vista previa con la impresora predeterminada)
const imprimir = reactive({ show: false, data: null, luego: null, printPath: '', printExtra: null, obligar: false })
let propinaPreguntada = false

// ── Carga ──────────────────────────────────────────────────────────────────
async function verificarTurno() {
  checkingTurno.value = true
  try {
    const t = (await api.get('/api/pos/turno/actual')).data
    turnoAbierto.value = !!t?.id
  }
  catch { turnoAbierto.value = false }
  checkingTurno.value = false
}
function onTurnoAbierto() { turnoAbierto.value = true; iniciar() }

// La pantalla de pago tiene la mesa-cuenta abierta (temp_mesa_abierta.Abierta = 1): nadie más
// puede entrar a la cuenta mientras se cobra. Si viene del detalle de la cuenta, es la misma
// pestaña y conserva la mesa; si otro dispositivo la tiene, no se puede pagar.
const mesaId   = ref(null)
const mesaLock = useMesaLock(() => mesaId.value)
async function iniciar() {
  loading.value = true
  try {
    const { data } = await api.get(`/api/pos/pago/${encodeURIComponent(orderNumber)}/bloqueo`)
    if (data.table_id != null) {
      mesaId.value = data.table_id
      await mesaLock.tomar()
      window.addEventListener('pagehide', mesaLock.liberarAlCerrar)
    }
  } catch (e) {
    errorCarga.value = e?.response?.data?.detail ?? 'No se pudo abrir la cuenta'
    loading.value = false
    return
  }
  await cargar()
}

// despuesDePago: tras un pago parcial la cuenta queda limpia y SIN ítems marcados
// (el cajero marca los del siguiente pago); en la primera carga se marcan todos.
async function cargar(despuesDePago = false) {
  loading.value = true
  errorCarga.value = ''
  try {
    const { data } = await api.get(`/api/pos/pago/${orderNumber}`)
    datos.value = data
    cliente.value = data.customer
    form.waiter_id = data.order.waiter_id || 0
    form.typification_id = 0; form.monto_pesos = 0; form.desc_obs = ''
    form.tip_mode = data.tip.enabled ? 'auto' : 'none'
    form.tip_manual = 0; form.delivery_amount = 0; form.observacion = ''
    dom.cliente = null
    propinaPreguntada = false
    seleccion.value = new Set(despuesDePago ? [] : data.items.map(i => i.item))
    reiniciarPagos()
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

// Cualquier cambio en el total (ítems, descuento, propina, domicilio) reinicia las
// formas de pago: una sola línea de EFECTIVO (default) por el nuevo total.
function formaPagoDefault() {
  const tipos = datos.value?.payment_types || []
  return tipos.find(p => p.is_default) || tipos.find(p => p.es_efectivo) || tipos[0] || null
}
function reiniciarPagos() {
  form.payments = [{ payment_method_id: formaPagoDefault()?.id || null, amount: total.value }]
}
watch(total, () => { if (datos.value) reiniciarPagos() })

const tipoPago = id => datos.value?.payment_types.find(p => p.id === id)
const esEfectivo = p => !!tipoPago(p.payment_method_id)?.es_efectivo

// Pago exacto; venta en $0 solo si es por descuento (cortesía / 100 %)
const puedeRegistrar = computed(() =>
  !!datos.value && seleccion.value.size > 0 && diferencia.value === 0 &&
  (venta.value > 0 || descuento.value > 0) &&
  form.payments.length > 0 && form.payments.every(p => p.payment_method_id) &&
  (!tipSel.value || elegiblesDescuento.value.length) &&
  (!tipSel.value?.ask_notes || form.desc_obs.trim()) &&
  (!tipSel.value || tipSel.value.percentage || (form.monto_pesos > 0 && descuento.value > 0))
)

// ── Formas de pago ───────────────────────────────────────────────────────────
function agregarFormaPago() {
  const restante = Math.max(0, total.value - pagado.value)
  const def = formaPagoDefault()
  form.payments.push({ payment_method_id: def?.id || null, amount: restante })
}
const efectivoAPagar = computed(() => form.payments.filter(esEfectivo).reduce((s, p) => s + (Math.round(Number(p.amount)) || 0), 0))

// ── Propina / domicilio / observación ────────────────────────────────────────
function togglePropina(on) { if (puedePropina.value) form.tip_mode = on ? 'auto' : 'none' }
// Quitar / cambiar la propina: "Cambiar Propina" del rol, o la empresa pide el valor en cada recibo
const puedePropina = computed(() => permisosRol.tiene('cambiar_propina') || !!datos.value?.tip?.ask_value)
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
  // Hay efectivo: preguntar con cuánto paga el cliente (el cambio se ve en la misma ventana)
  if (efectivoAPagar.value > 0) {
    Object.assign(cash, { show: true, aPagar: efectivoAPagar.value, recibido: 0 })
    setTimeout(() => document.getElementById('cash-recibido')?.focus(), 50)
    return
  }
  await enviarRecibo(null)
}

function confirmarEfectivo() {
  if (cashRecibido.value < cash.aPagar || registrando.value) return
  enviarRecibo(cashRecibido.value)
}

function cuerpoCalculo() {
  return {
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
    observacion: form.observacion || null,
  }
}

async function enviarRecibo(recibido) {
  if (registrando.value) return
  registrando.value = true
  try {
    const { data } = await api.post(`/api/pos/pago/${orderNumber}`, {
      ...cuerpoCalculo(),
      delivery_customer_id: form.delivery_amount ? (dom.cliente?.id_cliente || null) : null,
      payments: form.payments.map(p => ({ payment_method_id: p.payment_method_id, amount: Math.round(Number(p.amount) || 0) })),
      cash_received: recibido,
    })
    cash.show = false
    const cambio = data.change > 0 ? ` · Cambio ${fmt(data.change)}` : ''
    const siguiente = () => {
      if (data.remaining_items > 0) {
        showToast(`Recibo ${data.receipt_number} registrado${cambio} · quedan ${data.remaining_items} ítem(s) en la cuenta`, 'success')
        cargar(true)
      } else {
        showToast(`Recibo Nro. ${data.receipt_number} registrado${cambio}`, 'success')
        router.push('/restaurante')
      }
    }
    abrirImpresion(data.receipt_number, siguiente)
  } catch (e) {
    showToast(e?.response?.data?.detail ?? 'Error al registrar el recibo', 'error')
  }
  registrando.value = false
}

// ── Cuenta previa (informativa: no graba nada) ───────────────────────────────
async function cuentaPrevia() {
  if (!seleccion.value.size || cargandoPrecuenta.value) return
  cargandoPrecuenta.value = true
  try {
    const cuerpo = cuerpoCalculo()
    const { data } = await api.post(`/api/pos/pago/${orderNumber}/precuenta`, cuerpo)
    Object.assign(imprimir, { show: true, data, luego: null,
      printPath: `/api/pos/pago/${encodeURIComponent(orderNumber)}/precuenta/imprimir`, printExtra: cuerpo })
  } catch (e) {
    showToast(e?.response?.data?.detail ?? 'No se pudo generar la cuenta previa', 'error')
  }
  cargandoPrecuenta.value = false
}

function salir() { router.push('/restaurante') }


async function abrirImpresion(receiptNumber, luego) {
  try {
    const { data } = await api.get(`/api/pos/recibo-impresion/${encodeURIComponent(receiptNumber)}`)
    Object.assign(imprimir, { show: true, data, luego, printPath: '/api/pos/recibo-impresion/imprimir', printExtra: null,
                              obligar: permisosRol.tiene('obligar_imprimir') })
  } catch {
    showToast('No se pudo cargar la vista previa del recibo', 'warning')
    luego()
  }
}
function cerrarImpresion() {
  const f = imprimir.luego
  Object.assign(imprimir, { show: false, data: null, luego: null, printPath: '', printExtra: null, obligar: false })
  if (f) f()
}


// ── Atajos F5 / F6 ───────────────────────────────────────────────────────────
function onKey(e) {
  if (imprimir.show) return
  if (cash.show) { if (e.key === 'Escape') cash.show = false; return }
  if (e.key === 'F6') { e.preventDefault(); registrar() }
  else if (e.key === 'F5') { e.preventDefault(); if (datos.value?.has_pos_electronico && puedeRegistrar.value) facturar() }
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
  if (turnoAbierto.value) await iniciar()
  else loading.value = false
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey); window.removeEventListener('resize', ajustarAlto)
  window.removeEventListener('pagehide', mesaLock.liberarAlCerrar)
  mesaLock.liberar()
})
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
.pg-modal--cash { max-width: 560px; }
.cash-apagar { display: flex; justify-content: space-between; align-items: baseline; background: #f8fafc; border-radius: 10px; padding: 10px 14px; }
.cash-apagar span { font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase; }
.cash-apagar b { font-size: 22px; color: #1e293b; }
.cash-q { font-size: 20px; font-weight: 900; color: #1e3a5f; text-align: center; margin-top: 4px; }
.cash-inp { font-size: 30px !important; font-weight: 900; padding: 10px 14px !important; border: 2.5px solid #1d4ed8 !important; }
.cash-cambio { display: flex; justify-content: space-between; align-items: center; border-radius: 14px; padding: 12px 18px; }
.cash-cambio span { font-size: 18px; font-weight: 900; letter-spacing: 3px; }
.cash-cambio b { font-size: 40px; font-weight: 900; line-height: 1.1; }
.cash-cambio.ok { background: #16a34a; color: #fff; }
.cash-cambio.bad { background: #fef2f2; color: #b91c1c; }
.pg-btn--pre { background: #fff; color: #7c3aed; border: 1.5px solid #ddd6fe; }

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
  .pg-btns { display: grid; grid-template-columns: 1fr 1fr; }
  .cash-cambio b { font-size: 32px; }
  .cash-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 576px) {
  .pg-mesa { font-size: 15px; }
  .pg-pago { grid-template-columns: 1fr 1fr auto auto; }
  .cash-grid { grid-template-columns: repeat(2, 1fr); }
  .pg-v b { font-size: 14px; }
  .pg-v--total b { font-size: 17px; }
}
.pg-hdr-field--locked .pg-val { background: #f1f5f9; color: #475569; cursor: not-allowed; }
.pg-fecha-turno { flex-shrink: 0; margin: 8px 16px 0; padding: 8px 12px; border-radius: 10px; background: #fffbeb; border: 1px solid #fcd34d; color: #92400e; font-size: 13px; }
@media (max-width: 576px) { .pg-fecha-turno { margin: 6px 10px 0; font-size: 12px; } }
</style>
