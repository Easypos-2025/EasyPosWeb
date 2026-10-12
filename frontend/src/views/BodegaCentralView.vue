<template>
  <div class="bc-page">
    <div class="bc-head">
      <h2 class="bc-title"><i class="bi bi-boxes me-2"></i>{{ moduleName || 'Bodega Central' }}</h2>
      <p v-if="info" class="bc-sub">
        {{ info.bodega.nombre }} · NIT {{ info.bodega.nit }}
        <span v-if="info.cargue_unitario" class="bc-chip bc-chip--imei"><i class="bi bi-upc-scan"></i> Cargue unitario (IMEI)</span>
      </p>
      <div v-if="info" class="bc-sedes">
        <span class="bc-sedes-lbl">Sedes:</span>
        <span v-for="s in $ordenAlfa(info.sedes, 'nombre')" :key="s.id" class="bc-chip">
          <i class="bi" :class="s.con_escritorio ? 'bi-pc-display' : 'bi-globe'"></i> {{ s.nombre }}
        </span>
        <span v-if="!info.sedes.length" class="bc-nota">No hay otras empresas activas con este NIT.</span>
      </div>
    </div>

    <div v-if="loading" class="bc-state"><div class="spinner-border text-primary"></div></div>

    <div v-else-if="bloqueo" class="bc-bloqueo">
      <i class="bi bi-lock-fill"></i>
      <div>
        <b>{{ bloqueo }}</b>
        <p>La bodega central la habilita el administrador del sistema en una empresa con el mismo NIT de sus sedes.</p>
      </div>
    </div>

    <template v-else>
      <div class="bc-tabs">
        <button v-for="t in tabs" :key="t.key" class="bc-tab" :class="{ 'bc-tab--on': tab === t.key }" @click="cambiarTab(t.key)">
          <i :class="t.icon"></i><span>{{ t.label }}</span>
        </button>
      </div>

      <!-- ── Productos ── -->
      <section v-if="tab === 'productos'" class="bc-card">
        <div class="bc-toolbar">
          <div class="bc-search">
            <i class="bi bi-search"></i>
            <input v-model.trim="buscar" class="bc-inp" placeholder="Buscar por nombre, código o categoría..." />
          </div>
          <button class="bc-btn" @click="abrirNuevo"><i class="bi bi-plus-lg me-1"></i>Nuevo producto</button>
        </div>
        <div class="bc-resumen">{{ filtrados.length }} producto(s) · {{ fmtCant(totalUnidades) }} unidad(es) en bodega</div>

        <div v-if="cargandoProductos" class="bc-state"><div class="spinner-border spinner-border-sm text-primary"></div></div>
        <div v-else-if="!filtrados.length" class="bc-vacio">
          <i class="bi bi-box-seam"></i>
          <p>{{ productos.length ? 'Sin resultados para la búsqueda.' : 'La bodega está vacía. Cree productos o importe el catálogo de una sede.' }}</p>
        </div>

        <div v-else class="bc-lista">
          <article v-for="p in filtrados" :key="p.id" class="bc-prod" :class="{ 'bc-prod--inactivo': p.active }">
            <div class="bc-prod-main">
              <div class="bc-prod-nombre">{{ p.name }}</div>
              <div class="bc-prod-meta">
                <span><i class="bi bi-upc"></i> {{ p.product_code || '—' }}</span>
                <span><i class="bi bi-tag"></i> {{ p.categoria || 'Sin categoría' }}</span>
                <span v-if="p.proveedor"><i class="bi bi-truck"></i> {{ p.proveedor }}</span>
                <span v-if="p.extra_print" class="bc-chip bc-chip--imei">Desactivar al vender</span>
              </div>
              <div v-if="p.sedes.length" class="bc-prod-sedes">
                <span v-for="s in p.sedes" :key="s.sede_id" class="bc-chip" :class="`bc-chip--${s.estado.toLowerCase()}`">{{ s.sede }}</span>
              </div>
            </div>
            <div class="bc-prod-nums">
              <div><small>Venta</small><b>{{ fmt(p.price) }}</b></div>
              <div><small>Mínimo</small><b>{{ fmt(p.wholesale_price) }}</b></div>
              <div><small>Costo</small><b>{{ fmt(p.product_cost) }}</b></div>
              <div class="bc-stock" :class="{ 'bc-stock--cero': p.stock <= 0 }"><small>Stock</small><b>{{ fmtCant(p.stock) }}</b></div>
            </div>
            <div class="bc-prod-acc">
              <button v-if="!(info.cargue_unitario && p.extra_print)" class="bc-btn-sm" @click="abrirEntrada(p)">
                <i class="bi bi-box-arrow-in-down"></i> Entrada
              </button>
              <button v-if="info.cargue_unitario" class="bc-btn-sm bc-btn-sm--imei" @click="abrirReplicar(p)">
                <i class="bi bi-copy"></i> Replicar
              </button>
            </div>
          </article>
        </div>
      </section>

      <!-- ── Importar catálogo ── -->
      <section v-if="tab === 'importar'" class="bc-card bc-card--angosta">
        <h3 class="bc-card-ttl"><i class="bi bi-cloud-download"></i> Importar el catálogo de una sede</h3>
        <p class="bc-help">
          Copia a la bodega las categorías, proveedores y productos visibles de la sede escogida, con <b>cantidad 0</b>.
          Los productos que ya existen en la bodega (mismo código) solo se vinculan con la sede. Los productos sin código
          no se importan: el código es el que une el producto de la bodega con el de cada sede.
        </p>
        <div class="bc-field">
          <label>Sede</label>
          <select v-model.number="importarSede" class="bc-inp">
            <option :value="0">— Seleccionar —</option>
            <option v-for="s in $ordenAlfa(info.sedes, 'nombre')" :key="s.id" :value="s.id">{{ s.nombre }}</option>
          </select>
        </div>
        <button class="bc-btn bc-btn--full" :disabled="!importarSede || importando" @click="importar">
          <span v-if="importando" class="spinner-border spinner-border-sm me-1"></span>
          <i v-else class="bi bi-cloud-download me-1"></i>Importar catálogo
        </button>
        <div v-if="resultadoImportar" class="bc-resultado">
          <div><b>{{ resultadoImportar.creados }}</b><small>creados</small></div>
          <div><b>{{ resultadoImportar.vinculados }}</b><small>vinculados</small></div>
          <div><b>{{ resultadoImportar.sin_codigo }}</b><small>sin código</small></div>
          <div><b>{{ resultadoImportar.omitidos }}</b><small>nombre repetido</small></div>
        </div>
      </section>

      <!-- ── Movimientos ── -->
      <section v-if="tab === 'movimientos'" class="bc-card">
        <div v-if="cargandoMov" class="bc-state"><div class="spinner-border spinner-border-sm text-primary"></div></div>
        <div v-else-if="!movimientos.length" class="bc-vacio"><i class="bi bi-journal"></i><p>Sin movimientos todavía.</p></div>
        <div v-else class="bc-movs">
          <div v-for="m in movimientos" :key="m.id" class="bc-mov">
            <span class="bc-mov-tipo" :class="`bc-mov-tipo--${m.tipo.toLowerCase()}`">{{ m.tipo }}</span>
            <div class="bc-mov-main">
              <b>{{ m.producto || m.detalle || '—' }}</b>
              <small>
                <template v-if="m.codigo">{{ m.codigo }} · </template>
                <template v-if="m.sede">{{ m.sede }} · </template>
                {{ m.usuario }} · {{ fechaHora(m.created_at) }}
              </small>
              <small v-if="m.producto && m.detalle && m.detalle !== m.producto" class="bc-mov-det">{{ m.detalle }}</small>
            </div>
            <b v-if="m.cantidad" class="bc-mov-cant">+{{ fmtCant(m.cantidad) }}</b>
          </div>
        </div>
      </section>
    </template>

    <!-- ── Modal: nuevo producto ── -->
    <div v-if="modal === 'nuevo'" class="bc-overlay" @click.self="cerrar">
      <div class="bc-modal">
        <div class="bc-modal-head"><b>Nuevo producto</b><button class="bc-x" @click="cerrar"><i class="bi bi-x-lg"></i></button></div>
        <div class="bc-modal-body">
          <div class="bc-field">
            <label>Nombre *</label>
            <input v-model.trim="nuevo.name" class="bc-inp" maxlength="250" />
          </div>
          <div class="bc-row">
            <div class="bc-field">
              <label>{{ info.cargue_unitario ? 'Código / IMEI' : 'Código' }}</label>
              <input v-model.trim="nuevo.product_code" class="bc-inp" maxlength="60" placeholder="Automático si se deja vacío" />
            </div>
            <div class="bc-field">
              <label>Categoría *</label>
              <select v-model.number="nuevo.category_id" class="bc-inp">
                <option :value="0">— Seleccionar —</option>
                <option v-for="c in $ordenAlfa(info.categorias, 'name')" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
          </div>
          <div class="bc-field">
            <label>Proveedor {{ info.cargue_unitario ? '*' : '' }}</label>
            <select v-model.number="nuevo.id_proveedor" class="bc-inp">
              <option :value="0">{{ info.cargue_unitario ? '— Seleccionar —' : 'VARIOS (por defecto)' }}</option>
              <option v-for="p in $ordenAlfa(info.proveedores, 'name')" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
          </div>
          <div class="bc-row">
            <div class="bc-field"><label>Precio venta</label><CurrencyInput v-model="nuevo.price" class="bc-inp bc-num" /></div>
            <div class="bc-field"><label>Precio mínimo</label><CurrencyInput v-model="nuevo.wholesale_price" class="bc-inp bc-num" /></div>
          </div>
          <div class="bc-row">
            <div class="bc-field"><label>Costo</label><CurrencyInput v-model="nuevo.product_cost" class="bc-inp bc-num" /></div>
            <div class="bc-field"><label>IVA %</label><input v-model.number="nuevo.tax" type="number" min="0" max="100" class="bc-inp bc-num" /></div>
          </div>
          <div class="bc-row">
            <div class="bc-field"><label>Stock mínimo</label><input v-model.number="nuevo.minimum_stock" type="number" min="0" class="bc-inp bc-num" /></div>
            <div class="bc-field">
              <label>Cantidad inicial</label>
              <input v-if="!info.cargue_unitario" v-model.number="nuevo.cantidad_inicial" type="number" min="0" step="1" class="bc-inp bc-num" />
              <div v-else class="bc-fijo">1 (cargue unitario)</div>
            </div>
          </div>
          <label class="bc-switch">
            <input v-model="nuevo.extra_print" type="checkbox" :disabled="info.cargue_unitario" />
            Desactivar el producto al venderlo
          </label>
          <label class="bc-switch">
            <input v-model="nuevo.ask_product_description" type="checkbox" />
            Pedir descripción al vender
          </label>
        </div>
        <div class="bc-modal-foot">
          <button class="bc-btn bc-btn--sec" @click="cerrar">Cancelar</button>
          <button class="bc-btn" :disabled="enviando" @click="guardarNuevo">
            <span v-if="enviando" class="spinner-border spinner-border-sm me-1"></span>Guardar
          </button>
        </div>
      </div>
    </div>

    <!-- ── Modal: entrada ── -->
    <div v-if="modal === 'entrada'" class="bc-overlay" @click.self="cerrar">
      <div class="bc-modal bc-modal--sm">
        <div class="bc-modal-head"><b>Entrada a bodega</b><button class="bc-x" @click="cerrar"><i class="bi bi-x-lg"></i></button></div>
        <div class="bc-modal-body">
          <div class="bc-prod-ref">{{ sel.name }}<small>{{ sel.product_code }} · stock actual {{ fmtCant(sel.stock) }}</small></div>
          <div class="bc-field"><label>Cantidad *</label><input v-model.number="entrada.cantidad" type="number" min="1" step="1" class="bc-inp bc-num" /></div>
          <div class="bc-field"><label>Observación</label><input v-model.trim="entrada.observacion" class="bc-inp" maxlength="200" /></div>
        </div>
        <div class="bc-modal-foot">
          <button class="bc-btn bc-btn--sec" @click="cerrar">Cancelar</button>
          <button class="bc-btn" :disabled="enviando" @click="guardarEntrada">
            <span v-if="enviando" class="spinner-border spinner-border-sm me-1"></span>Registrar
          </button>
        </div>
      </div>
    </div>

    <!-- ── Modal: replicar por IMEI ── -->
    <div v-if="modal === 'replicar'" class="bc-overlay" @click.self="cerrar">
      <div class="bc-modal">
        <div class="bc-modal-head"><b>Replicar producto</b><button class="bc-x" @click="cerrar"><i class="bi bi-x-lg"></i></button></div>
        <div class="bc-modal-body">
          <div class="bc-prod-ref">{{ sel.name }}<small>{{ sel.product_code }} · {{ fmt(sel.price) }}</small></div>
          <p class="bc-help">Cada réplica es un producto nuevo con el mismo precio, categoría y proveedor, su propio código (IMEI) y cantidad 1.</p>
          <div class="bc-field"><label>Nombre del producto a replicar</label><input v-model.trim="rep.nombre_base" class="bc-inp" maxlength="200" /></div>
          <div v-if="!rep.codigos.length" class="bc-row bc-row--end">
            <div class="bc-field"><label>Cantidad de réplicas</label><input v-model.number="rep.cantidad" type="number" min="1" max="200" step="1" class="bc-inp bc-num" /></div>
            <button class="bc-btn" @click="iniciarReplica"><i class="bi bi-play-fill me-1"></i>Iniciar</button>
          </div>
          <template v-else>
            <div class="bc-resumen">{{ codigosListos }} de {{ rep.codigos.length }} códigos digitados</div>
            <div class="bc-imeis">
              <div v-for="(c, i) in rep.codigos" :key="i" class="bc-imei" :class="{ 'bc-imei--dup': duplicados.has(c.trim()) && c.trim() }">
                <span>{{ i + 1 }}</span>
                <input :ref="el => (imeiRefs[i] = el)" v-model="rep.codigos[i]" class="bc-inp" maxlength="60"
                       :placeholder="`Código replica ${i + 1}`" autocomplete="off" @keydown.enter.prevent="siguienteImei(i)" />
              </div>
            </div>
          </template>
        </div>
        <div class="bc-modal-foot">
          <button class="bc-btn bc-btn--sec" @click="rep.codigos.length ? (rep.codigos = []) : cerrar()">
            {{ rep.codigos.length ? 'Cancelar replicar' : 'Cerrar' }}
          </button>
          <button v-if="rep.codigos.length" class="bc-btn" :disabled="enviando || codigosListos !== rep.codigos.length || duplicados.size > 0" @click="guardarReplica">
            <span v-if="enviando" class="spinner-border spinner-border-sm me-1"></span>Replicar {{ rep.codigos.length }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'
import { useModuleName } from '@/composables/useModuleName'
import CurrencyInput from '@/components/CurrencyInput.vue'

const { moduleName } = useModuleName()
const BASE = '/api/bodega-central'
const MAX_REPLICAS = 200

const loading = ref(true)
const bloqueo = ref('')
const info = ref(null)
const tab = ref('productos')
const tabs = [
  { key: 'productos', label: 'Productos', icon: 'bi bi-box-seam' },
  { key: 'importar', label: 'Importar catálogo', icon: 'bi bi-cloud-download' },
  { key: 'movimientos', label: 'Movimientos', icon: 'bi bi-journal-text' },
]

const productos = ref([])
const cargandoProductos = ref(false)
const buscar = ref('')
const movimientos = ref([])
const cargandoMov = ref(false)
const importarSede = ref(0)
const importando = ref(false)
const resultadoImportar = ref(null)

const modal = ref('')
const enviando = ref(false)
const sel = ref(null)
const nuevo = ref({})
const entrada = ref({ cantidad: 1, observacion: '' })
const rep = ref({ nombre_base: '', cantidad: 1, codigos: [], clave: '' })
const imeiRefs = ref([])

// ── Formatos (moneda del asociado) ──
const usuario = (() => { try { return JSON.parse(localStorage.getItem('user') || '{}') } catch { return {} } })()
const fmtMoneda = new Intl.NumberFormat(usuario.locale || 'es-CO', { style: 'currency', currency: usuario.currency_code || 'COP', maximumFractionDigits: 0 })
const fmt = (v) => fmtMoneda.format(Number(v) || 0)
const fmtCant = (v) => new Intl.NumberFormat('es-CO', { maximumFractionDigits: 2 }).format(Number(v) || 0)
const fechaHora = (v) => (v ? new Date(v).toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' }) : '')
const errorDe = (e, porDefecto) => {
  const d = e?.response?.data?.detail
  return Array.isArray(d) ? 'Revise los valores ingresados' : (d || porDefecto)
}
// Clave de idempotencia: repetir el envío (doble clic, red lenta) no duplica nada en el servidor
const nuevaClave = () => (window.crypto?.randomUUID ? window.crypto.randomUUID()
  : Array.from({ length: 32 }, () => Math.floor(Math.random() * 16).toString(16)).join(''))

const filtrados = computed(() => {
  const q = buscar.value.toLowerCase()
  if (!q) return productos.value
  return productos.value.filter(p => [p.name, p.product_code, p.categoria].some(v => (v || '').toLowerCase().includes(q)))
})
const totalUnidades = computed(() => filtrados.value.reduce((s, p) => s + (p.stock > 0 ? p.stock : 0), 0))
const codigosListos = computed(() => rep.value.codigos.filter(c => c.trim()).length)
const duplicados = computed(() => {
  const vistos = new Set(), dup = new Set()
  rep.value.codigos.forEach(c => { const k = c.trim(); if (!k) return; if (vistos.has(k)) dup.add(k); vistos.add(k) })
  return dup
})

async function cargar() {
  loading.value = true
  try {
    info.value = (await api.get(BASE)).data
    bloqueo.value = ''
    await cargarProductos()
  } catch (e) {
    if (e?.response?.status === 403) bloqueo.value = errorDe(e, 'La empresa no está habilitada como bodega central')
    else showToast(errorDe(e, 'Error cargando la bodega'), 'error')
  }
  loading.value = false
}

async function cargarProductos() {
  cargandoProductos.value = true
  try { productos.value = (await api.get(`${BASE}/productos`)).data }
  catch (e) { showToast(errorDe(e, 'Error cargando los productos'), 'error') }
  cargandoProductos.value = false
}

async function cargarMovimientos() {
  cargandoMov.value = true
  try { movimientos.value = (await api.get(`${BASE}/movimientos`)).data }
  catch (e) { showToast(errorDe(e, 'Error cargando los movimientos'), 'error') }
  cargandoMov.value = false
}

function cambiarTab(k) {
  tab.value = k
  if (k === 'movimientos') cargarMovimientos()
}

function cerrar() { if (!enviando.value) modal.value = '' }

// ── Nuevo producto ──
function abrirNuevo() {
  nuevo.value = {
    name: '', product_code: '', category_id: 0, id_proveedor: 0, price: 0, wholesale_price: 0, product_cost: 0,
    tax: 0, minimum_stock: 0, cantidad_inicial: 0, extra_print: !!info.value.cargue_unitario,
    ask_product_description: false, clave: nuevaClave(),
  }
  modal.value = 'nuevo'
}

async function guardarNuevo() {
  const n = nuevo.value
  if (!n.name) return showToast('Digite el nombre del producto', 'warning')
  if (!n.category_id) return showToast('Escoja la categoría', 'warning')
  if (info.value.cargue_unitario && !n.id_proveedor) return showToast('Escoja el proveedor (obligatorio en cargue unitario)', 'warning')
  if (n.wholesale_price && n.price && n.wholesale_price > n.price) return showToast('El precio mínimo no puede ser mayor que el precio de venta', 'warning')
  enviando.value = true
  try {
    await api.post(`${BASE}/productos`, { ...n, cantidad_inicial: Math.max(0, Math.floor(n.cantidad_inicial || 0)) })
    showToast('Producto creado', 'success')
    enviando.value = false
    modal.value = ''
    await cargarProductos()
  } catch (e) { showToast(errorDe(e, 'Error al crear el producto'), 'error') }
  enviando.value = false
}

// ── Entrada ──
function abrirEntrada(p) {
  sel.value = p
  entrada.value = { cantidad: 1, observacion: '', clave: nuevaClave() }
  modal.value = 'entrada'
}

async function guardarEntrada() {
  const cant = Math.floor(entrada.value.cantidad || 0)
  if (cant < 1) return showToast('La cantidad debe ser mayor a 0', 'warning')
  enviando.value = true
  try {
    await api.post(`${BASE}/entradas`, { dish_id: sel.value.id, cantidad: cant, observacion: entrada.value.observacion, clave: entrada.value.clave })
    showToast('Entrada registrada', 'success')
    enviando.value = false
    modal.value = ''
    await cargarProductos()
  } catch (e) { showToast(errorDe(e, 'Error al registrar la entrada'), 'error') }
  enviando.value = false
}

// ── Replicar (IMEI) ──
function abrirReplicar(p) {
  sel.value = p
  rep.value = { nombre_base: p.name, cantidad: 1, codigos: [], clave: '' }
  modal.value = 'replicar'
}

async function iniciarReplica() {
  const n = Math.floor(rep.value.cantidad || 0)
  if (n < 1 || n > MAX_REPLICAS) return showToast(`La cantidad debe estar entre 1 y ${MAX_REPLICAS}`, 'warning')
  rep.value.codigos = Array.from({ length: n }, () => '')
  rep.value.clave = nuevaClave()
  imeiRefs.value = []
  await nextTick()
  imeiRefs.value[0]?.focus()
}

function siguienteImei(i) {
  const sig = imeiRefs.value[i + 1]
  if (sig) sig.focus()
  else if (codigosListos.value === rep.value.codigos.length && !duplicados.value.size) guardarReplica()
}

async function guardarReplica() {
  enviando.value = true
  try {
    const { data } = await api.post(`${BASE}/replicar/${sel.value.id}`, {
      nombre_base: rep.value.nombre_base, codigos: rep.value.codigos.map(c => c.trim()), clave: rep.value.clave,
    })
    showToast(data.repetida ? 'Esta réplica ya se había registrado' : `${data.creados.length} producto(s) creados con cantidad 1`, 'success')
    enviando.value = false
    modal.value = ''
    await cargarProductos()
  } catch (e) { showToast(errorDe(e, 'Error al replicar'), 'error') }
  enviando.value = false
}

// ── Importar ──
async function importar() {
  const sede = info.value.sedes.find(s => s.id === importarSede.value)
  if (!sede) return
  const { isConfirmed } = await window.Swal.fire({
    title: '¿Importar catálogo?',
    text: `Se copiarán a la bodega los productos de ${sede.nombre} con cantidad 0.`,
    icon: 'question', showCancelButton: true, confirmButtonText: 'Importar', cancelButtonText: 'Cancelar',
  })
  if (!isConfirmed) return
  importando.value = true
  resultadoImportar.value = null
  try {
    const { data } = await api.post(`${BASE}/importar`, { sede_id: sede.id, clave: nuevaClave() })
    resultadoImportar.value = data
    showToast('Catálogo importado', 'success')
    info.value = (await api.get(BASE)).data
    await cargarProductos()
  } catch (e) { showToast(errorDe(e, 'Error al importar el catálogo'), 'error') }
  importando.value = false
}

onMounted(cargar)
</script>

<style scoped>
.bc-page { padding: 20px 24px 32px; }
.bc-head { margin-bottom: 14px; }
.bc-title { font-size: 22px; font-weight: 800; color: #1e293b; margin: 0; }
.bc-sub { font-size: 13px; color: #64748b; margin: 2px 0 0; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.bc-sedes { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; margin-top: 8px; }
.bc-sedes-lbl { font-size: 12px; font-weight: 700; color: #475569; }
.bc-nota { font-size: 12px; color: #94a3b8; }
.bc-chip { display: inline-flex; align-items: center; gap: 4px; font-size: 11.5px; font-weight: 700; padding: 3px 8px;
  border-radius: 999px; background: #eef2ff; color: #3730a3; white-space: nowrap; }
.bc-chip--imei { background: #fef3c7; color: #92400e; }
.bc-chip--vinculado { background: #dcfce7; color: #166534; }
.bc-chip--pendiente { background: #fef9c3; color: #854d0e; }
.bc-chip--error { background: #fee2e2; color: #991b1b; }
.bc-state { display: flex; justify-content: center; padding: 40px; }
.bc-bloqueo { display: flex; gap: 12px; align-items: flex-start; background: #fffbeb; border: 1px solid #fde68a; color: #92400e;
  border-radius: 12px; padding: 16px; max-width: 640px; }
.bc-bloqueo i { font-size: 22px; }
.bc-bloqueo p { margin: 4px 0 0; font-size: 13px; }

.bc-tabs { display: flex; gap: 6px; margin-bottom: 12px; overflow-x: auto; }
.bc-tab { display: inline-flex; align-items: center; gap: 6px; border: 1.5px solid #cbd5e1; background: #fff; color: #475569;
  border-radius: 10px; padding: 8px 14px; font-weight: 700; font-size: 13.5px; cursor: pointer; white-space: nowrap; }
.bc-tab--on { background: #1e3a5f; border-color: #1e3a5f; color: #fff; }

.bc-card { background: #fff; border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,.08); padding: 16px; display: flex; flex-direction: column; gap: 10px; }
.bc-card--angosta { max-width: 640px; }
.bc-card-ttl { font-size: 15px; font-weight: 800; color: #1e3a5f; margin: 0; display: flex; gap: 8px; align-items: center; }
.bc-help { font-size: 13px; color: #475569; margin: 0; line-height: 1.45; }
.bc-toolbar { display: flex; gap: 10px; align-items: center; }
.bc-search { position: relative; flex: 1; }
.bc-search i { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: #94a3b8; }
.bc-search .bc-inp { padding-left: 32px; }
.bc-resumen { font-size: 12.5px; color: #64748b; }
.bc-vacio { text-align: center; color: #94a3b8; padding: 30px 10px; }
.bc-vacio i { font-size: 34px; }

.bc-field { display: flex; flex-direction: column; gap: 4px; flex: 1; min-width: 0; }
.bc-field label { font-size: 12px; font-weight: 700; color: #475569; }
.bc-row { display: flex; gap: 10px; }
.bc-row--end { align-items: flex-end; }
.bc-inp { border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 8px 10px; font-size: 14px; color: #1e293b; background: #fff; width: 100%; }
.bc-inp:focus { outline: none; border-color: #1d4ed8; }
.bc-num { text-align: right; }
.bc-fijo { padding: 8px 10px; background: #f8fafc; border-radius: 8px; font-size: 14px; color: #64748b; }
.bc-switch { display: flex; align-items: center; gap: 10px; font-size: 14px; color: #334155; cursor: pointer; }
.bc-switch input { width: 18px; height: 18px; accent-color: #1d4ed8; flex-shrink: 0; }

.bc-btn { display: inline-flex; align-items: center; justify-content: center; background: linear-gradient(90deg,#1e3a5f,#1d4ed8);
  color: #fff; border: none; border-radius: 10px; padding: 9px 16px; font-weight: 700; font-size: 14px; cursor: pointer; white-space: nowrap; }
.bc-btn:disabled { opacity: .55; cursor: not-allowed; }
.bc-btn--sec { background: #e2e8f0; color: #334155; }
.bc-btn--full { width: 100%; }
.bc-btn-sm { display: inline-flex; align-items: center; gap: 5px; border: 1.5px solid #bfdbfe; background: #eff6ff; color: #1d4ed8;
  border-radius: 8px; padding: 6px 10px; font-size: 12.5px; font-weight: 700; cursor: pointer; white-space: nowrap; }
.bc-btn-sm--imei { border-color: #fde68a; background: #fffbeb; color: #92400e; }

.bc-lista { display: flex; flex-direction: column; gap: 8px; }
.bc-prod { display: grid; grid-template-columns: minmax(0, 1fr) auto auto; gap: 12px; align-items: center;
  border: 1px solid #e2e8f0; border-radius: 12px; padding: 10px 12px; }
.bc-prod--inactivo { opacity: .55; }
.bc-prod-nombre { font-weight: 800; color: #1e293b; font-size: 14px; word-break: break-word; }
.bc-prod-meta { display: flex; flex-wrap: wrap; gap: 4px 12px; font-size: 12px; color: #64748b; margin-top: 2px; }
.bc-prod-sedes { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; }
.bc-prod-nums { display: grid; grid-template-columns: repeat(4, minmax(80px, auto)); gap: 10px; text-align: right; }
.bc-prod-nums small { display: block; font-size: 10.5px; color: #94a3b8; font-weight: 700; text-transform: uppercase; }
.bc-prod-nums b { font-size: 13.5px; color: #1e293b; }
.bc-stock b { color: #15803d; }
.bc-stock--cero b { color: #b91c1c; }
.bc-prod-acc { display: flex; flex-direction: column; gap: 6px; }
.bc-prod-ref { font-weight: 800; color: #1e293b; display: flex; flex-direction: column; background: #f8fafc; border-radius: 10px; padding: 8px 10px; }
.bc-prod-ref small { font-weight: 500; color: #64748b; }

.bc-resultado { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.bc-resultado div { background: #f8fafc; border-radius: 10px; padding: 10px; text-align: center; display: flex; flex-direction: column; }
.bc-resultado b { font-size: 20px; color: #1e3a5f; }
.bc-resultado small { font-size: 11.5px; color: #64748b; }

.bc-movs { display: flex; flex-direction: column; }
.bc-mov { display: flex; gap: 10px; align-items: center; padding: 8px 0; border-bottom: 1px solid #f1f5f9; }
.bc-mov-tipo { font-size: 10.5px; font-weight: 800; padding: 3px 7px; border-radius: 6px; background: #e2e8f0; color: #334155; flex-shrink: 0; }
.bc-mov-tipo--entrada, .bc-mov-tipo--replica { background: #dcfce7; color: #166534; }
.bc-mov-tipo--importacion { background: #e0e7ff; color: #3730a3; }
.bc-mov-main { display: flex; flex-direction: column; min-width: 0; flex: 1; }
.bc-mov-main b { font-size: 13.5px; color: #1e293b; word-break: break-word; }
.bc-mov-main small { font-size: 12px; color: #64748b; }
.bc-mov-det { color: #94a3b8 !important; }
.bc-mov-cant { color: #15803d; }

.bc-overlay { position: fixed; inset: 0; background: rgba(15,23,42,.5); display: flex; align-items: center; justify-content: center; z-index: 1050; padding: 16px; }
.bc-modal { background: #fff; border-radius: 14px; width: 100%; max-width: 560px; max-height: 92vh; display: flex; flex-direction: column; }
.bc-modal--sm { max-width: 420px; }
.bc-modal-head { display: flex; justify-content: space-between; align-items: center; padding: 14px 16px; border-bottom: 1px solid #e2e8f0; }
.bc-modal-head b { font-size: 16px; color: #1e293b; }
.bc-x { border: none; background: none; font-size: 18px; color: #64748b; cursor: pointer; }
.bc-modal-body { padding: 14px 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
.bc-modal-foot { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 16px; border-top: 1px solid #e2e8f0; }

.bc-imeis { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; }
.bc-imei { display: flex; align-items: center; gap: 6px; }
.bc-imei span { width: 26px; text-align: right; font-size: 12px; color: #94a3b8; font-weight: 700; flex-shrink: 0; }
.bc-imei--dup .bc-inp { border-color: #dc2626; background: #fef2f2; }

@media (max-width: 1024px) {
  .bc-prod { grid-template-columns: minmax(0, 1fr) auto; }
  .bc-prod-nums { grid-column: 1 / -1; grid-template-columns: repeat(4, 1fr); text-align: left; }
  .bc-prod-acc { grid-row: 1; grid-column: 2; }
}
@media (max-width: 768px) {
  .bc-page { padding: 14px 12px 80px; }
  .bc-toolbar { flex-direction: column; align-items: stretch; }
  .bc-card--angosta { max-width: none; }
  .bc-imeis { grid-template-columns: 1fr; }
  .bc-overlay { align-items: flex-end; padding: 0; }
  .bc-modal { max-width: none; border-radius: 14px 14px 0 0; max-height: 94vh; }
}
@media (max-width: 576px) {
  .bc-title { font-size: 18px; }
  .bc-row { flex-direction: column; gap: 10px; }
  .bc-row--end { align-items: stretch; }
  .bc-prod { grid-template-columns: 1fr; }
  .bc-prod-acc { grid-row: auto; grid-column: auto; flex-direction: row; }
  .bc-prod-acc .bc-btn-sm { flex: 1; justify-content: center; }
  .bc-prod-nums { grid-template-columns: repeat(2, 1fr); }
  .bc-resultado { grid-template-columns: repeat(2, 1fr); }
  .bc-tab span { font-size: 12.5px; }
  .bc-card { padding: 12px; }
}
</style>
