<template>
  <div class="fp-page">
    <div class="fp-head">
      <div>
        <h2 class="fp-title"><i class="bi bi-receipt-cutoff me-2"></i>{{ moduleName || 'Factura de Proveedor' }}</h2>
        <p class="fp-sub">
          La mercancía comprada entra al inventario con su costo (valor con descuento). Cada compra queda como un lote.
          <span v-if="cat.con_escritorio" class="fp-chip"><i class="bi bi-pc-display"></i> Baja al escritorio</span>
        </p>
      </div>
      <div class="fp-tabs">
        <button :class="{ on: tab === 'nueva' }" @click="tab = 'nueva'"><i class="bi bi-plus-circle"></i> Nueva</button>
        <button :class="{ on: tab === 'consulta' }" @click="irConsulta"><i class="bi bi-search"></i> Consultar</button>
      </div>
    </div>

    <!-- ═══ Nueva factura ═══ -->
    <template v-if="tab === 'nueva'">
      <section class="fp-card">
        <div class="fp-grid">
          <div class="fp-field fp-field--2"><label>Proveedor *</label>
            <select v-model.number="fac.id_proveedor" class="fp-inp">
              <option :value="0">— Seleccionar —</option>
              <option v-for="p in $ordenAlfa(cat.proveedores, 'name')" :key="p.id" :value="p.id">{{ p.name }}{{ p.nit ? ` · ${p.nit}` : '' }}</option>
            </select></div>
          <div class="fp-field"><label>N° factura *</label><input v-model.trim="fac.nro_factura" class="fp-inp" maxlength="40" /></div>
          <div class="fp-field"><label>Fecha *</label><CustomDatePicker v-model="fac.fecha" /></div>
          <div class="fp-field fp-field--full"><label>Observación</label><input v-model.trim="fac.observacion" class="fp-inp" maxlength="255" /></div>
        </div>
      </section>

      <section class="fp-card">
        <div class="fp-buscar">
          <div class="fp-search">
            <i class="bi bi-upc-scan"></i>
            <input ref="buscarRef" v-model.trim="buscar" class="fp-inp" placeholder="Código (lector) o nombre del producto..."
                   @keydown.enter.prevent="agregarPorCodigo" />
          </div>
          <button v-if="puedeCrearProducto" class="fp-btn fp-btn--sec" @click="abrirNuevoProducto"><i class="bi bi-plus-lg me-1"></i>Producto nuevo</button>
        </div>
        <div v-if="buscar && sugeridos.length" class="fp-sug">
          <button v-for="p in sugeridos" :key="p.id" class="fp-sug-item" @click="agregar(p)">
            <div><b>{{ p.name }}</b><small>{{ p.product_code || '—' }} · {{ p.categoria || 'Sin categoría' }} · Stock {{ fmtCant(p.stock) }}</small></div>
            <div class="fp-sug-costo">
              <small>Último costo</small><b>{{ p.ultimo_costo != null ? fmt(p.ultimo_costo) : fmt(p.product_cost) }}</b>
              <small v-if="p.ultima_fecha">{{ fmtFecha(p.ultima_fecha) }} · {{ p.ultimo_proveedor }}</small>
              <small>Venta {{ fmt(p.price) }}</small>
            </div>
          </button>
        </div>
        <p v-else-if="buscar && !sugeridos.length" class="fp-nota">Sin resultados para «{{ buscar }}».</p>

        <div v-if="!lineas.length" class="fp-vacio"><i class="bi bi-cart"></i><p>Agregue los productos de la factura.</p></div>
        <div v-else class="fp-lineas">
          <article v-for="(l, i) in lineas" :key="l.dish_id" class="fp-linea">
            <div class="fp-linea-head">
              <span class="fp-n">{{ i + 1 }}</span>
              <div class="fp-linea-nombre"><b>{{ l.name }}</b><small>{{ l.product_code || '—' }} · costo actual {{ fmt(l.product_cost) }}</small></div>
              <button class="fp-x" title="Quitar" @click="quitar(i)"><i class="bi bi-trash"></i></button>
            </div>
            <div class="fp-linea-campos">
              <div class="fp-field"><label>Cantidad</label><input v-model.number="l.cantidad" type="number" min="0" :step="l.porImei ? 1 : 'any'" class="fp-inp fp-num" @change="ajustarImeis(l)" /></div>
              <div class="fp-field"><label>Valor unitario</label><CurrencyInput v-model="l.valor_unitario" class="fp-inp fp-num" /></div>
              <div class="fp-field"><label>% Desc.</label><input v-model.number="l.porc_descuento" type="number" min="0" max="100" step="any" class="fp-inp fp-num" /></div>
              <div class="fp-field"><label>Valor con desc.</label><div class="fp-fijo">{{ fmt(conDesc(l)) }}</div></div>
              <div class="fp-field"><label>Total</label><div class="fp-fijo fp-fijo--b">{{ fmt(conDesc(l) * (l.cantidad || 0)) }}</div></div>
              <div v-if="cat.drogueria" class="fp-field"><label>Vence *</label><CustomDatePicker v-model="l.fecha_vence" /></div>
            </div>
            <div v-if="cat.cargue_unitario" class="fp-imei-box">
              <label class="fp-switch"><input v-model="l.porImei" type="checkbox" @change="ajustarImeis(l)" /> Registrar por IMEI (un producto por unidad: «{{ l.name }} + IMEI»)</label>
              <div v-if="l.porImei" class="fp-imeis">
                <div v-for="(c, k) in l.imeis" :key="k" class="fp-imei" :class="{ 'fp-imei--dup': c.trim() && imeisRepetidos.has(c.trim()) }">
                  <span>{{ k + 1 }}</span>
                  <input :ref="el => setImeiRef(l, k, el)" v-model="l.imeis[k]" class="fp-inp" maxlength="60" autocomplete="off"
                         :placeholder="`IMEI ${k + 1}`" @keydown.enter.prevent="siguienteImei(l, k)" />
                </div>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section v-if="lineas.length" class="fp-card fp-totales">
        <div><small>Subtotal</small><b>{{ fmt(totales.subtotal) }}</b></div>
        <div><small>Descuentos</small><b>{{ fmt(totales.descuento) }}</b></div>
        <div class="fp-total"><small>Total factura</small><b>{{ fmt(totales.total) }}</b></div>
        <button class="fp-btn" :disabled="enviando" @click="revisar"><i class="bi bi-check2-circle me-1"></i>Registrar factura</button>
      </section>
    </template>

    <!-- ═══ Consulta ═══ -->
    <template v-else>
      <section class="fp-card">
        <div class="fp-grid">
          <div class="fp-field"><label>Desde</label><CustomDatePicker v-model="filtro.desde" /></div>
          <div class="fp-field"><label>Hasta</label><CustomDatePicker v-model="filtro.hasta" /></div>
          <div class="fp-field"><label>Proveedor</label>
            <select v-model.number="filtro.id_proveedor" class="fp-inp">
              <option :value="0">Todos</option>
              <option v-for="p in $ordenAlfa(cat.proveedores, 'name')" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select></div>
          <div class="fp-field"><label>N° factura, producto o IMEI</label><input v-model.trim="filtro.texto" class="fp-inp" maxlength="60" @keydown.enter="consultar" /></div>
        </div>
        <div class="fp-acc">
          <button class="fp-btn" :disabled="consultando" @click="consultar"><i class="bi bi-search me-1"></i>Consultar</button>
          <button class="fp-btn fp-btn--sec" :disabled="!facturas.length" @click="exportar"><i class="bi bi-file-earmark-excel me-1"></i>Excel</button>
        </div>
      </section>
      <div v-if="consultando" class="fp-state"><div class="spinner-border text-primary"></div></div>
      <div v-else-if="!facturas.length" class="fp-vacio"><i class="bi bi-receipt"></i><p>Sin facturas para estos filtros.</p></div>
      <div v-else class="fp-lista">
        <article v-for="f in facturas" :key="f.id" class="fp-fac" :class="{ 'fp-fac--anulada': f.estado === 'ANULADA' }" @click="verDetalle(f)">
          <div>
            <b>{{ f.proveedor }} · Factura {{ f.nro_factura }}</b>
            <small>{{ fmtFecha(f.fecha) }} · Registro #{{ f.numero }} · {{ f.lineas }} producto(s) · {{ f.usuario }}</small>
            <div class="fp-chips">
              <span v-if="f.estado === 'ANULADA'" class="fp-chip fp-chip--rojo">Anulada</span>
              <span v-if="f.escritorio_estado !== 'NO_APLICA'" class="fp-chip" :class="claseEscritorio(f.escritorio_estado)">{{ f.escritorio_texto }}</span>
              <span v-if="f.escritorio_error && ['PENDIENTE', 'REVERSA'].includes(f.escritorio_estado)" class="fp-chip fp-chip--rojo" :title="f.escritorio_error">Con error</span>
            </div>
          </div>
          <div class="fp-fac-total"><small>Total</small><b>{{ fmt(f.total) }}</b></div>
        </article>
      </div>
    </template>

    <!-- Confirmar registro -->
    <div v-if="modal === 'confirmar'" class="fp-overlay" @click.self="cerrar">
      <div class="fp-modal">
        <div class="fp-modal-head"><b>Registrar factura</b><button class="fp-x" @click="cerrar"><i class="bi bi-x-lg"></i></button></div>
        <div class="fp-modal-body">
          <div class="fp-resumen">
            <div><small>Proveedor</small><b>{{ nombreProveedor(fac.id_proveedor) }}</b></div>
            <div><small>Factura</small><b>{{ fac.nro_factura }} · {{ fmtFecha(fac.fecha) }}</b></div>
            <div><small>Productos</small><b>{{ lineas.length }} ({{ fmtCant(lineas.reduce((a, l) => a + (l.cantidad || 0), 0)) }} unidades)</b></div>
            <div><small>Total</small><b>{{ fmt(totales.total) }}</b></div>
          </div>
          <p class="fp-nota">Al registrar: la cantidad entra al inventario, el costo de cada producto pasa a ser su valor con descuento y queda un lote por producto{{ cat.drogueria ? ' con su vencimiento' : '' }}.{{ cat.con_escritorio ? ' El agente la baja al escritorio cuando todos sus productos estén sincronizados.' : '' }}</p>
        </div>
        <div class="fp-modal-foot">
          <button class="fp-btn fp-btn--sec" @click="cerrar">Volver</button>
          <button class="fp-btn" :disabled="enviando" @click="registrar"><span v-if="enviando" class="spinner-border spinner-border-sm me-1"></span>Registrar</button>
        </div>
      </div>
    </div>

    <!-- Producto nuevo -->
    <div v-if="modal === 'producto'" class="fp-overlay" @click.self="cerrar">
      <div class="fp-modal">
        <div class="fp-modal-head"><b>Producto nuevo</b><button class="fp-x" @click="cerrar"><i class="bi bi-x-lg"></i></button></div>
        <div class="fp-modal-body">
          <div class="fp-field"><label>Nombre *</label><input v-model.trim="np.name" class="fp-inp" maxlength="250" /></div>
          <div class="fp-row">
            <div class="fp-field"><label>Código (lector)</label><input v-model.trim="np.product_code" class="fp-inp" maxlength="60" placeholder="Automático si se deja vacío" /></div>
            <div class="fp-field"><label>Categoría *</label>
              <select v-model.number="np.category_id" class="fp-inp">
                <option :value="0">— Seleccionar —</option>
                <option v-for="c in $ordenAlfa(catProd.categorias, 'name')" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select></div>
          </div>
          <div class="fp-row">
            <div class="fp-field"><label>Precio venta</label><CurrencyInput v-model="np.price" class="fp-inp fp-num" /></div>
            <div class="fp-field"><label>IVA %</label><input v-model.number="np.tax" type="number" min="0" max="100" class="fp-inp fp-num" /></div>
          </div>
          <p class="fp-nota">El proveedor es el de la factura. La cantidad y el costo se toman de la línea de la factura. Los demás datos se completan en Productos.</p>
        </div>
        <div class="fp-modal-foot">
          <button class="fp-btn fp-btn--sec" @click="cerrar">Cancelar</button>
          <button class="fp-btn" :disabled="enviando" @click="crearProducto"><span v-if="enviando" class="spinner-border spinner-border-sm me-1"></span>Crear y agregar</button>
        </div>
      </div>
    </div>

    <!-- Detalle -->
    <div v-if="modal === 'detalle'" class="fp-overlay" @click.self="cerrar">
      <div class="fp-modal fp-modal--ancho">
        <div class="fp-modal-head"><b>Factura {{ det.nro_factura }}</b><button class="fp-x" @click="cerrar"><i class="bi bi-x-lg"></i></button></div>
        <div v-if="!det.id" class="fp-state"><div class="spinner-border text-primary"></div></div>
        <div v-else class="fp-modal-body">
          <div id="fp-imprimible">
            <div class="fp-resumen">
              <div><small>Proveedor</small><b>{{ det.proveedor }}{{ det.proveedor_nit ? ` · ${det.proveedor_nit}` : '' }}</b></div>
              <div><small>Fecha</small><b>{{ fmtFecha(det.fecha) }} · Registro #{{ det.numero }}</b></div>
              <div><small>Registró</small><b>{{ det.usuario }} · {{ det.creada }}</b></div>
              <div v-if="det.escritorio_estado !== 'NO_APLICA'"><small>Escritorio</small><b>{{ det.escritorio_texto }}</b></div>
            </div>
            <p v-if="det.observacion" class="fp-nota">{{ det.observacion }}</p>
            <p v-if="det.estado === 'ANULADA'" class="fp-anulada">Anulada {{ det.anulada_en }} por {{ det.anulada_por }}: {{ det.anulada_motivo }}</p>
            <p v-if="det.escritorio_error && ['PENDIENTE', 'REVERSA'].includes(det.escritorio_estado)" class="fp-anulada">Escritorio: {{ det.escritorio_error }}</p>
            <div class="fp-det">
              <div v-for="l in det.lineas" :key="l.item" class="fp-det-l">
                <div><b>{{ l.item }}. {{ l.nombre }}</b><small>{{ l.codigo || '—' }}{{ l.fecha_vence ? ` · vence ${fmtFecha(l.fecha_vence)}` : '' }}{{ l.disponible != null ? ` · quedan ${fmtCant(l.disponible)}` : '' }}</small></div>
                <div class="fp-det-n">
                  <span>{{ fmtCant(l.cantidad) }} × {{ fmt(l.valor_unitario) }}{{ l.porc_descuento ? ` −${fmtCant(l.porc_descuento)}%` : '' }}</span>
                  <b>{{ fmt(l.total) }}</b>
                </div>
              </div>
            </div>
            <div class="fp-totales fp-totales--det">
              <div><small>Subtotal</small><b>{{ fmt(det.subtotal) }}</b></div>
              <div><small>Descuentos</small><b>{{ fmt(det.descuento) }}</b></div>
              <div class="fp-total"><small>Total</small><b>{{ fmt(det.total) }}</b></div>
            </div>
          </div>
          <div v-if="anulando.abierto" class="fp-field"><label>Motivo de la anulación *</label>
            <input v-model.trim="anulando.motivo" class="fp-inp" maxlength="255" placeholder="Mínimo 5 letras" /></div>
        </div>
        <div v-if="det.id" class="fp-modal-foot">
          <button class="fp-btn fp-btn--sec" @click="imprimir"><i class="bi bi-printer me-1"></i>Imprimir</button>
          <template v-if="det.estado === 'ACTIVA'">
            <button v-if="!anulando.abierto" class="fp-btn fp-btn--rojo" @click="anulando.abierto = true"><i class="bi bi-x-circle me-1"></i>Anular</button>
            <button v-else class="fp-btn fp-btn--rojo" :disabled="enviando || anulando.motivo.length < 5" @click="anular">
              <span v-if="enviando" class="spinner-border spinner-border-sm me-1"></span>Confirmar anulación</button>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// Factura de Proveedor: una factura completa por pantalla, sin IVA, % de descuento por línea; costo = valor con descuento.
import { ref, computed, onMounted, nextTick } from 'vue'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'
import { useModuleName } from '@/composables/useModuleName'
import CurrencyInput from '@/components/CurrencyInput.vue'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'

const { moduleName } = useModuleName()
const BASE = '/api/factura-proveedor'
const hoy = () => new Date().toLocaleDateString('en-CA')

const tab = ref('nueva')
const cat = ref({ proveedores: [], drogueria: false, cargue_unitario: false, con_escritorio: false })
const catProd = ref({ categorias: [] })
const puedeCrearProducto = ref(false)
const productos = ref([])
const buscar = ref('')
const buscarRef = ref(null)
const fac = ref({ id_proveedor: 0, nro_factura: '', fecha: hoy(), observacion: '' })
const lineas = ref([])
const modal = ref('')
const enviando = ref(false)
const np = ref({})
const filtro = ref({ desde: '', hasta: hoy(), id_proveedor: 0, texto: '' })
const facturas = ref([])
const consultando = ref(false)
const det = ref({})
const anulando = ref({ abierto: false, motivo: '' })
const imeiRefs = {}

const usuario = (() => { try { return JSON.parse(localStorage.getItem('user') || '{}') } catch { return {} } })()
const fmtMoneda = new Intl.NumberFormat(usuario.locale || 'es-CO', { style: 'currency', currency: usuario.currency_code || 'COP', maximumFractionDigits: 0 })
const fmt = (v) => fmtMoneda.format(Number(v) || 0)
const fmtCant = (v) => new Intl.NumberFormat('es-CO', { maximumFractionDigits: 2 }).format(Number(v) || 0)
const fmtFecha = (f) => (f ? new Date(`${String(f).slice(0, 10)}T00:00:00`).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' }) : '')
const errorDe = (e, porDefecto) => {
  const d = e?.response?.data?.detail
  return Array.isArray(d) ? 'Revise los valores ingresados' : (d || porDefecto)
}
const nombreProveedor = (id) => cat.value.proveedores.find(p => p.id === id)?.name || ''
const conDesc = (l) => (Number(l.valor_unitario) || 0) * (1 - (Number(l.porc_descuento) || 0) / 100)
const claseEscritorio = (e) => ({ APLICADA: 'fp-chip--verde', REVERTIDA: 'fp-chip--gris' }[e] || 'fp-chip--amarillo')

const sugeridos = computed(() => {
  const q = buscar.value.toLowerCase()
  if (!q) return []
  const usados = new Set(lineas.value.map(l => l.dish_id))
  return productos.value.filter(p => !usados.has(p.id) && [p.name, p.product_code].some(v => (v || '').toLowerCase().includes(q))).slice(0, 8)
})
const totales = computed(() => {
  const subtotal = lineas.value.reduce((a, l) => a + (Number(l.valor_unitario) || 0) * (Number(l.cantidad) || 0), 0)
  const total = lineas.value.reduce((a, l) => a + conDesc(l) * (Number(l.cantidad) || 0), 0)
  return { subtotal, total, descuento: subtotal - total }
})
const imeisRepetidos = computed(() => {
  const vistos = new Set(), dup = new Set()
  lineas.value.filter(l => l.porImei).flatMap(l => l.imeis).forEach(c => { const k = c.trim(); if (!k) return; if (vistos.has(k)) dup.add(k); vistos.add(k) })
  return dup
})

async function cargar() {
  try {
    const [c, p] = await Promise.all([api.get(`${BASE}/catalogos`), api.get(`${BASE}/productos`)])
    cat.value = c.data
    productos.value = p.data
  } catch (e) { showToast(errorDe(e, 'Error cargando la factura de proveedor'), 'error') }
  try {
    const { data } = await api.get('/api/productos/catalogos')
    catProd.value = data
    puedeCrearProducto.value = true
  } catch { puedeCrearProducto.value = false }
}

function agregar(p) {
  if (lineas.value.some(l => l.dish_id === p.id)) return showToast('Ese producto ya está en la factura', 'warning')
  lineas.value.push({ dish_id: p.id, name: p.name, product_code: p.product_code, product_cost: p.product_cost, cantidad: 1,
                      valor_unitario: Math.round(p.ultimo_costo ?? p.product_cost ?? 0), porc_descuento: 0, fecha_vence: '',
                      porImei: false, imeis: [] })
  buscar.value = ''
  nextTick(() => buscarRef.value?.focus())
}

function agregarPorCodigo() {
  const q = buscar.value.toLowerCase()
  if (!q) return
  const exacto = productos.value.find(p => (p.product_code || '').toLowerCase() === q)
  if (exacto) return agregar(exacto)
  if (sugeridos.value.length === 1) agregar(sugeridos.value[0])
}

function quitar(i) { lineas.value.splice(i, 1) }

function ajustarImeis(l) {
  if (!l.porImei) { l.imeis = []; return }
  const n = Math.max(0, Math.min(200, Math.floor(Number(l.cantidad) || 0)))
  l.cantidad = n
  l.imeis = Array.from({ length: n }, (_, k) => l.imeis[k] || '')
}
function setImeiRef(l, k, el) { (imeiRefs[l.dish_id] ||= [])[k] = el }
function siguienteImei(l, k) { imeiRefs[l.dish_id]?.[k + 1]?.focus() }

function revisar() {
  const f = fac.value
  if (!f.id_proveedor) return showToast('Escoja el proveedor', 'warning')
  if (!f.nro_factura) return showToast('Digite el número de la factura', 'warning')
  if (!f.fecha) return showToast('Escoja la fecha de la factura', 'warning')
  for (const [i, l] of lineas.value.entries()) {
    if (!(l.cantidad > 0)) return showToast(`Línea ${i + 1}: digite la cantidad`, 'warning')
    if (l.porc_descuento < 0 || l.porc_descuento > 100) return showToast(`Línea ${i + 1}: el descuento va de 0 a 100`, 'warning')
    if (cat.value.drogueria && !l.fecha_vence) return showToast(`Línea ${i + 1}: escoja el vencimiento`, 'warning')
    if (l.porImei && l.imeis.some(c => !c.trim())) return showToast(`Línea ${i + 1}: faltan IMEI por digitar`, 'warning')
  }
  if (imeisRepetidos.value.size) return showToast('Hay IMEI repetidos', 'warning')
  modal.value = 'confirmar'
}

async function registrar() {
  enviando.value = true
  try {
    const { data } = await api.post(BASE, {
      ...fac.value, observacion: fac.value.observacion || null,
      lineas: lineas.value.map(l => ({ dish_id: l.dish_id, cantidad: Number(l.cantidad), valor_unitario: Number(l.valor_unitario) || 0,
                                       porc_descuento: Number(l.porc_descuento) || 0, fecha_vence: cat.value.drogueria ? l.fecha_vence : null,
                                       imeis: l.porImei ? l.imeis.map(c => c.trim()) : null })),
    })
    showToast(`Factura registrada (registro #${data.numero}) por ${fmt(data.total)}`, 'success')
    fac.value = { id_proveedor: fac.value.id_proveedor, nro_factura: '', fecha: hoy(), observacion: '' }
    lineas.value = []
    modal.value = ''
    const { data: p } = await api.get(`${BASE}/productos`)
    productos.value = p
  } catch (e) { showToast(errorDe(e, 'Error al registrar la factura'), 'error') }
  enviando.value = false
}

function abrirNuevoProducto() {
  if (!fac.value.id_proveedor) return showToast('Escoja primero el proveedor de la factura', 'warning')
  np.value = { name: buscar.value && !/^\d+$/.test(buscar.value) ? buscar.value : '', product_code: /^\S+$/.test(buscar.value) && /\d/.test(buscar.value) ? buscar.value : '',
               category_id: 0, price: 0, tax: 0 }
  modal.value = 'producto'
}

async function crearProducto() {
  const p = np.value
  if (!p.name) return showToast('Digite el nombre del producto', 'warning')
  if (!p.category_id) return showToast('Escoja la categoría', 'warning')
  enviando.value = true
  try {
    const { data } = await api.post('/api/productos', { ...p, id_proveedor: fac.value.id_proveedor, cantidad_inicial: 0 })
    const { data: lista } = await api.get(`${BASE}/productos`)
    productos.value = lista
    const nuevo = lista.find(x => x.id === data.id)
    modal.value = ''
    if (nuevo) agregar(nuevo)
    showToast('Producto creado y agregado a la factura', 'success')
  } catch (e) { showToast(errorDe(e, 'Error al crear el producto'), 'error') }
  enviando.value = false
}

function irConsulta() {
  tab.value = 'consulta'
  if (!facturas.value.length) consultar()
}

async function consultar() {
  consultando.value = true
  try {
    const f = filtro.value
    const params = { hasta: f.hasta || undefined, desde: f.desde || undefined, id_proveedor: f.id_proveedor || undefined, texto: f.texto || undefined }
    const { data } = await api.get(BASE, { params })
    facturas.value = data
  } catch (e) { showToast(errorDe(e, 'Error consultando las facturas'), 'error') }
  consultando.value = false
}

async function verDetalle(f) {
  det.value = {}
  anulando.value = { abierto: false, motivo: '' }
  modal.value = 'detalle'
  try {
    const { data } = await api.get(`${BASE}/${f.id}`)
    det.value = data
  } catch (e) { modal.value = ''; showToast(errorDe(e, 'Error cargando la factura'), 'error') }
}

async function anular() {
  enviando.value = true
  try {
    const { data } = await api.post(`${BASE}/${det.value.id}/anular`, { motivo: anulando.value.motivo })
    showToast(data.escritorio === 'REVERSA' ? 'Factura anulada. El agente la reversa en el escritorio.' : 'Factura anulada', 'success')
    modal.value = ''
    await consultar()
    const { data: p } = await api.get(`${BASE}/productos`)
    productos.value = p
  } catch (e) { showToast(errorDe(e, 'Error al anular'), 'error') }
  enviando.value = false
}

function imprimir() {
  const html = document.getElementById('fp-imprimible')?.innerHTML || ''
  const w = window.open('', '_blank', 'width=720,height=900')
  if (!w) return showToast('Permita las ventanas emergentes para imprimir', 'warning')
  w.document.write(`<html><head><title>Factura ${det.value.nro_factura}</title><style>
    body{font-family:Arial,sans-serif;font-size:12px;color:#111;padding:16px} small{display:block;color:#555}
    .fp-resumen{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:10px} .fp-det-l{display:flex;justify-content:space-between;border-bottom:1px solid #ddd;padding:5px 0}
    .fp-det-n{text-align:right} .fp-totales{display:flex;justify-content:flex-end;gap:18px;margin-top:10px;text-align:right}
  </style></head><body><h3>Factura de proveedor ${det.value.nro_factura}</h3>${html}</body></html>`)
  w.document.close()
  w.focus()
  w.print()
}

function exportar() {
  const filas = [['Registro', 'Fecha', 'Proveedor', 'Factura', 'Productos', 'Subtotal', 'Descuentos', 'Total', 'Estado', 'Escritorio']]
  facturas.value.forEach(f => filas.push([f.numero, f.fecha, f.proveedor, f.nro_factura, f.lineas, f.subtotal, f.descuento, f.total, f.estado, f.escritorio_texto]))
  const csv = filas.map(r => r.map(v => `"${String(v ?? '').replace(/"/g, '""')}"`).join(';')).join('\r\n')
  const url = URL.createObjectURL(new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' }))
  const a = document.createElement('a')
  a.href = url
  a.download = `facturas_proveedor_${hoy()}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

function cerrar() { if (!enviando.value) modal.value = '' }

onMounted(cargar)
</script>

<style scoped>
.fp-page { padding: 20px 24px 32px; }
.fp-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 12px; }
.fp-title { font-size: 22px; font-weight: 800; color: #1e293b; margin: 0; }
.fp-sub { font-size: 13px; color: #64748b; margin: 2px 0 0; display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.fp-tabs { display: flex; background: #f1f5f9; border-radius: 10px; padding: 3px; }
.fp-tabs button { border: none; background: none; padding: 7px 14px; border-radius: 8px; font-weight: 700; font-size: 13.5px; color: #475569; cursor: pointer; white-space: nowrap; }
.fp-tabs button.on { background: #fff; color: #1d4ed8; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.fp-chip { display: inline-flex; align-items: center; gap: 4px; font-size: 11.5px; font-weight: 700; padding: 3px 8px; border-radius: 999px; background: #eef2ff; color: #3730a3; white-space: nowrap; }
.fp-chip--rojo { background: #fee2e2; color: #991b1b; }
.fp-chip--verde { background: #dcfce7; color: #166534; }
.fp-chip--amarillo { background: #fef9c3; color: #854d0e; }
.fp-chip--gris { background: #f1f5f9; color: #475569; }
.fp-chips { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }
.fp-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px; margin-bottom: 12px; }
.fp-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
.fp-field { display: flex; flex-direction: column; gap: 4px; min-width: 0; flex: 1; }
.fp-field--2 { grid-column: span 2; }
.fp-field--full { grid-column: 1 / -1; }
.fp-field label { font-size: 12px; font-weight: 700; color: #475569; }
.fp-row { display: flex; gap: 10px; }
.fp-inp { border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 8px 10px; font-size: 14px; color: #1e293b; background: #fff; width: 100%; }
.fp-inp:focus { outline: none; border-color: #1d4ed8; }
.fp-num { text-align: right; }
.fp-fijo { padding: 8px 10px; background: #f8fafc; border-radius: 8px; font-size: 14px; color: #334155; text-align: right; white-space: nowrap; }
.fp-fijo--b { font-weight: 800; color: #1e293b; }
.fp-nota { font-size: 12.5px; color: #64748b; margin: 6px 0 0; }
.fp-btn { display: inline-flex; align-items: center; justify-content: center; background: linear-gradient(90deg,#1e3a5f,#1d4ed8); color: #fff; border: none; border-radius: 10px; padding: 9px 16px; font-weight: 700; font-size: 14px; cursor: pointer; white-space: nowrap; }
.fp-btn:disabled { opacity: .55; cursor: not-allowed; }
.fp-btn--sec { background: #e2e8f0; color: #334155; }
.fp-btn--rojo { background: #dc2626; }
.fp-acc { display: flex; gap: 8px; justify-content: flex-end; margin-top: 10px; }
.fp-buscar { display: flex; gap: 8px; }
.fp-search { position: relative; flex: 1; }
.fp-search i { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: #94a3b8; }
.fp-search .fp-inp { padding-left: 32px; }
.fp-sug { border: 1px solid #e2e8f0; border-radius: 10px; margin-top: 6px; max-height: 340px; overflow-y: auto; }
.fp-sug-item { display: flex; justify-content: space-between; gap: 10px; width: 100%; text-align: left; border: none; border-bottom: 1px solid #f1f5f9; background: #fff; padding: 8px 10px; cursor: pointer; }
.fp-sug-item:hover { background: #eff6ff; }
.fp-sug-item b { display: block; font-size: 13.5px; color: #1e293b; }
.fp-sug-item small { display: block; font-size: 11.5px; color: #64748b; }
.fp-sug-costo { text-align: right; flex-shrink: 0; }
.fp-vacio { text-align: center; color: #94a3b8; padding: 28px 10px; }
.fp-vacio i { font-size: 30px; }
.fp-state { display: flex; justify-content: center; padding: 40px; }
.fp-lineas { display: flex; flex-direction: column; gap: 8px; margin-top: 10px; }
.fp-linea { border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px; }
.fp-linea-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.fp-n { width: 24px; height: 24px; border-radius: 50%; background: #eff6ff; color: #1d4ed8; font-size: 12px; font-weight: 800; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.fp-linea-nombre { flex: 1; min-width: 0; }
.fp-linea-nombre b { display: block; font-size: 14px; color: #1e293b; word-break: break-word; }
.fp-linea-nombre small { font-size: 12px; color: #64748b; }
.fp-x { border: none; background: none; font-size: 17px; color: #94a3b8; cursor: pointer; }
.fp-x:hover { color: #dc2626; }
.fp-linea-campos { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 8px; }
.fp-imei-box { margin-top: 8px; }
.fp-switch { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #334155; cursor: pointer; margin: 0; }
.fp-switch input { width: 17px; height: 17px; accent-color: #1d4ed8; }
.fp-imeis { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 6px; margin-top: 8px; }
.fp-imei { display: flex; align-items: center; gap: 6px; }
.fp-imei span { width: 26px; text-align: right; font-size: 12px; color: #94a3b8; font-weight: 700; flex-shrink: 0; }
.fp-imei--dup .fp-inp { border-color: #dc2626; background: #fef2f2; }
.fp-totales { display: flex; align-items: center; justify-content: flex-end; gap: 22px; flex-wrap: wrap; }
.fp-totales > div { text-align: right; }
.fp-totales small { display: block; font-size: 11px; color: #94a3b8; font-weight: 700; text-transform: uppercase; }
.fp-totales b { font-size: 15px; color: #1e293b; }
.fp-total b { font-size: 19px; color: #1d4ed8; }
.fp-totales--det { margin-top: 10px; }
.fp-lista { display: flex; flex-direction: column; gap: 8px; }
.fp-fac { display: flex; justify-content: space-between; gap: 12px; align-items: center; background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 10px 12px; cursor: pointer; }
.fp-fac:hover { border-color: #93c5fd; }
.fp-fac b { font-size: 14px; color: #1e293b; }
.fp-fac small { display: block; font-size: 12px; color: #64748b; }
.fp-fac--anulada { opacity: .65; }
.fp-fac-total { text-align: right; flex-shrink: 0; }
.fp-overlay { position: fixed; inset: 0; background: rgba(15,23,42,.5); display: flex; align-items: center; justify-content: center; z-index: 1050; padding: 16px; }
.fp-modal { background: #fff; border-radius: 14px; width: 100%; max-width: 560px; max-height: 92vh; display: flex; flex-direction: column; }
.fp-modal--ancho { max-width: 760px; }
.fp-modal-head { display: flex; justify-content: space-between; align-items: center; padding: 14px 16px; border-bottom: 1px solid #e2e8f0; }
.fp-modal-head b { font-size: 16px; color: #1e293b; }
.fp-modal-body { padding: 14px 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
.fp-modal-foot { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 16px; border-top: 1px solid #e2e8f0; flex-wrap: wrap; }
.fp-resumen { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.fp-resumen small { display: block; font-size: 11px; color: #94a3b8; font-weight: 700; text-transform: uppercase; }
.fp-resumen b { font-size: 14px; color: #1e293b; }
.fp-anulada { font-size: 13px; color: #991b1b; background: #fef2f2; border-radius: 8px; padding: 6px 10px; margin: 6px 0 0; }
.fp-det { display: flex; flex-direction: column; margin-top: 8px; }
.fp-det-l { display: flex; justify-content: space-between; gap: 10px; padding: 7px 0; border-bottom: 1px solid #f1f5f9; }
.fp-det-l b { display: block; font-size: 13.5px; color: #1e293b; }
.fp-det-l small { font-size: 12px; color: #64748b; }
.fp-det-n { text-align: right; flex-shrink: 0; display: flex; flex-direction: column; }
.fp-det-n span { font-size: 12px; color: #64748b; }

@media (max-width: 1024px) {
  .fp-linea-campos { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 768px) {
  .fp-page { padding: 14px 12px 80px; }
  .fp-head { flex-direction: column; align-items: stretch; }
  .fp-tabs button { flex: 1; }
  .fp-grid { grid-template-columns: 1fr 1fr; }
  .fp-field--2 { grid-column: 1 / -1; }
  .fp-imeis { grid-template-columns: 1fr 1fr; }
  .fp-overlay { align-items: flex-end; padding: 0; }
  .fp-modal { max-width: none; border-radius: 14px 14px 0 0; max-height: 94vh; }
  .fp-totales { justify-content: space-between; }
  .fp-totales .fp-btn { width: 100%; }
}
@media (max-width: 576px) {
  .fp-title { font-size: 18px; }
  .fp-grid { grid-template-columns: 1fr; }
  .fp-buscar { flex-direction: column; }
  .fp-linea-campos { grid-template-columns: 1fr 1fr; }
  .fp-imeis { grid-template-columns: 1fr; }
  .fp-row { flex-direction: column; }
  .fp-resumen { grid-template-columns: 1fr; }
  .fp-sug-item { flex-direction: column; }
  .fp-sug-costo { text-align: left; }
  .fp-fac { flex-direction: column; align-items: stretch; }
  .fp-fac-total { text-align: left; }
}
</style>
