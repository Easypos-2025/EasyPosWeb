<template>
  <div class="pr-page">
    <div class="pr-head">
      <div>
        <h2 class="pr-title"><i class="bi bi-box-seam me-2"></i>{{ moduleName || 'Productos' }}</h2>
        <p class="pr-sub">
          Artículos que se venden en el punto de venta.
          <span v-if="cat.cargue_unitario" class="pr-chip pr-chip--imei"><i class="bi bi-upc-scan"></i> Cargue unitario (IMEI)</span>
          <span v-if="cat.con_escritorio" class="pr-chip"><i class="bi bi-pc-display"></i> Con escritorio</span>
        </p>
      </div>
      <button class="pr-btn" @click="abrirNuevo"><i class="bi bi-plus-lg me-1"></i>Nuevo producto</button>
    </div>

    <AvisoBodega :bodega="cat.administrado_por" que="El precio de venta, el mínimo, el costo, el IVA y el stock mínimo" />
    <p v-if="cat.con_escritorio" class="pr-aviso">
      <i class="bi bi-info-circle"></i> Los productos nuevos bajan al escritorio con la sincronización del catálogo. La
      cantidad se carga con la Factura de Proveedor o desde el escritorio.
    </p>

    <div class="pr-toolbar">
      <div class="pr-search">
        <i class="bi bi-search"></i>
        <input v-model.trim="buscar" class="pr-inp" placeholder="Buscar por nombre, código o categoría..." />
      </div>
      <select v-model="filtroCat" class="pr-inp pr-inp--cat">
        <option value="">Todas las categorías</option>
        <option v-for="c in $ordenAlfa(cat.categorias, 'name')" :key="c.id" :value="c.name">{{ c.name }}</option>
      </select>
      <select v-model="filtroEstado" class="pr-inp pr-inp--cat">
        <option value="activos">Activos</option>
        <option value="inactivos">Inactivos</option>
        <option value="todos">Todos</option>
      </select>
    </div>
    <div class="pr-resumen">{{ filtrados.length }} producto(s)</div>

    <div v-if="cargando" class="pr-state"><div class="spinner-border text-primary"></div></div>
    <div v-else-if="!filtrados.length" class="pr-vacio"><i class="bi bi-box-seam"></i><p>{{ productos.length ? 'Sin resultados.' : 'Aún no hay productos.' }}</p></div>
    <div v-else class="pr-lista">
      <article v-for="p in filtrados" :key="p.id" class="pr-prod" :class="{ 'pr-prod--off': p.active }">
        <div class="pr-prod-main">
          <div class="pr-prod-nombre">{{ p.name }}</div>
          <div class="pr-prod-meta">
            <span><i class="bi bi-upc"></i> {{ p.product_code || '—' }}</span>
            <span><i class="bi bi-tag"></i> {{ p.categoria || 'Sin categoría' }}</span>
            <span v-if="p.proveedor"><i class="bi bi-truck"></i> {{ p.proveedor }}</span>
            <span v-if="cat.drogueria && p.laboratorio"><i class="bi bi-capsule"></i> {{ p.laboratorio }}</span>
            <span v-if="cat.drogueria && p.vence" class="pr-chip" :class="claseVence(p.vence)"><i class="bi bi-calendar-x"></i> Vence {{ fmtFecha(p.vence) }}</span>
            <span v-if="p.extra_print" class="pr-chip pr-chip--imei">Desactivar al vender</span>
            <span v-if="p.provisional" class="pr-chip pr-chip--pend">Pendiente de bajar al escritorio</span>
            <span v-else-if="p.active" class="pr-chip">Inactivo</span>
          </div>
        </div>
        <div class="pr-prod-nums">
          <div><small>Venta</small><b>{{ fmt(p.price) }}</b></div>
          <div><small>Mínimo</small><b>{{ fmt(p.wholesale_price) }}</b></div>
          <div><small>Costo</small><b>{{ fmt(p.product_cost) }}</b></div>
          <div class="pr-stock" :class="{ 'pr-stock--bajo': p.minimum_stock && p.stock <= p.minimum_stock }"><small>Stock</small><b>{{ fmtCant(p.stock) }}</b></div>
          <div><small>Valor inv.</small><b>{{ fmt(p.valor_inventario) }}</b></div>
        </div>
        <div class="pr-prod-acc">
          <button class="pr-btn-sm" @click="abrirEditar(p)"><i class="bi bi-pencil"></i> Editar</button>
          <button class="pr-btn-sm pr-btn-sm--gris" @click="abrirLotes(p)"><i class="bi bi-stack"></i> Lotes{{ p.lotes ? ` (${p.lotes})` : '' }}</button>
          <button v-if="cat.cargue_unitario && !cat.con_escritorio" class="pr-btn-sm pr-btn-sm--imei" @click="abrirReplicar(p)"><i class="bi bi-copy"></i> Replicar</button>
          <button v-if="!p.provisional" class="pr-btn-sm pr-btn-sm--gris" @click="cambiarEstado(p)">
            <i class="bi" :class="p.active ? 'bi-toggle-off' : 'bi-toggle-on'"></i> {{ p.active ? 'Activar' : 'Desactivar' }}
          </button>
        </div>
      </article>
    </div>

    <!-- Crear / editar -->
    <div v-if="modal === 'form'" class="pr-overlay" @click.self="cerrar">
      <div class="pr-modal">
        <div class="pr-modal-head"><b>{{ form.id ? 'Editar producto' : 'Nuevo producto' }}</b><button class="pr-x" @click="cerrar"><i class="bi bi-x-lg"></i></button></div>
        <div class="pr-modal-body">
          <div class="pr-field"><label>Nombre *</label><input v-model.trim="form.name" class="pr-inp" maxlength="250" /></div>
          <div class="pr-row">
            <div class="pr-field"><label>{{ cat.cargue_unitario ? 'Código / IMEI' : 'Código (lector de barras)' }}</label>
              <input v-model.trim="form.product_code" class="pr-inp" maxlength="60" placeholder="Automático si se deja vacío" /></div>
            <div class="pr-field"><label>Categoría *</label>
              <select v-model.number="form.category_id" class="pr-inp">
                <option :value="0">— Seleccionar —</option>
                <option v-for="c in $ordenAlfa(cat.categorias, 'name')" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select></div>
          </div>
          <div class="pr-field"><label>Proveedor {{ cat.cargue_unitario ? '*' : '' }}</label>
            <select v-model.number="form.id_proveedor" class="pr-inp">
              <option :value="0">{{ cat.cargue_unitario ? '— Seleccionar —' : 'VARIOS (por defecto)' }}</option>
              <option v-for="p in $ordenAlfa(cat.proveedores, 'name')" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select></div>
          <div class="pr-row">
            <div class="pr-field"><label>Precio venta</label><CurrencyInput v-model="form.price" class="pr-inp pr-num" :disabled="valoresBloqueados" /></div>
            <div class="pr-field"><label>Precio mínimo</label><CurrencyInput v-model="form.wholesale_price" class="pr-inp pr-num" :disabled="valoresBloqueados" /></div>
          </div>
          <div class="pr-row">
            <div class="pr-field"><label>Costo</label><CurrencyInput v-model="form.product_cost" class="pr-inp pr-num" :disabled="valoresBloqueados" /></div>
            <div class="pr-field"><label>IVA %</label><input v-model.number="form.tax" type="number" min="0" max="100" class="pr-inp pr-num" :disabled="valoresBloqueados" /></div>
          </div>
          <div class="pr-row">
            <div class="pr-field"><label>Stock mínimo</label><input v-model.number="form.minimum_stock" type="number" min="0" class="pr-inp pr-num" :disabled="valoresBloqueados" /></div>
            <div v-if="!form.id" class="pr-field"><label>Cantidad inicial</label>
              <input v-if="!cat.cargue_unitario && !cat.con_escritorio" v-model.number="form.cantidad_inicial" type="number" min="0" step="1" class="pr-inp pr-num" />
              <div v-else class="pr-fijo">{{ cat.con_escritorio ? 'Con la Factura de Proveedor' : '1 (cargue unitario)' }}</div></div>
          </div>
          <div v-if="cat.drogueria" class="pr-row">
            <div class="pr-field"><label>Laboratorio</label>
              <div class="pr-lab">
                <select v-model.number="form.id_laboratorio" class="pr-inp">
                  <option :value="0">— Sin laboratorio —</option>
                  <option v-for="l in $ordenAlfa(cat.laboratorios, 'name')" :key="l.id" :value="l.id">{{ l.name }}</option>
                </select>
                <button type="button" class="pr-btn-sm" title="Nuevo laboratorio" @click="nuevoLab.abierto = !nuevoLab.abierto"><i class="bi bi-plus-lg"></i></button>
              </div>
              <div v-if="nuevoLab.abierto" class="pr-lab">
                <input v-model.trim="nuevoLab.nombre" class="pr-inp" maxlength="50" placeholder="Nombre del laboratorio" @keydown.enter.prevent="crearLab" />
                <button type="button" class="pr-btn-sm" :disabled="nuevoLab.enviando" @click="crearLab">Crear</button>
              </div></div>
            <div v-if="!form.id" class="pr-field"><label>Vencimiento del lote inicial</label><CustomDatePicker v-model="form.fecha_vence" /></div>
          </div>
          <p v-if="valoresBloqueados" class="pr-nota">Venta, mínimo, costo, IVA y stock mínimo los define la bodega central «{{ cat.administrado_por.nombre }}».</p>
          <label class="pr-switch"><input v-model="form.extra_print" type="checkbox" :disabled="cat.cargue_unitario && !form.id" /> Desactivar el producto al venderlo</label>
          <label class="pr-switch"><input v-model="form.ask_product_description" type="checkbox" /> Pedir descripción al vender</label>
          <div v-if="form.id" class="pr-field"><label>Foto</label>
            <ImageUploader :current-url="form.photo_path ? imgSrc(form.photo_path) : null" @change="b => { fotoPendiente = b; fotoEliminada = false }" @remove="fotoPendiente = null; fotoEliminada = true" /></div>
          <p v-else class="pr-nota">La foto se agrega después de guardar.</p>
        </div>
        <div class="pr-modal-foot">
          <button class="pr-btn pr-btn--sec" @click="cerrar">Cancelar</button>
          <button class="pr-btn" :disabled="enviando" @click="guardar"><span v-if="enviando" class="spinner-border spinner-border-sm me-1"></span>Guardar</button>
        </div>
      </div>
    </div>

    <!-- Lotes (costeo PEPS) -->
    <div v-if="modal === 'lotes'" class="pr-overlay" @click.self="cerrar">
      <div class="pr-modal pr-modal--ancho">
        <div class="pr-modal-head"><b>Lotes de {{ sel.name }}</b><button class="pr-x" @click="cerrar"><i class="bi bi-x-lg"></i></button></div>
        <div class="pr-modal-body">
          <p class="pr-nota">Cada compra o entrada es un lote con su costo. Las ventas gastan primero los lotes más viejos (PEPS), así la utilidad y el inventario usan el costo real de cada unidad.</p>
          <div v-if="lotes.cargando" class="pr-state"><div class="spinner-border text-primary"></div></div>
          <div v-else-if="!lotes.filas.length" class="pr-vacio"><i class="bi bi-stack"></i><p>Sin lotes con existencia. El primer movimiento crea el lote con el stock actual.</p></div>
          <div v-else class="pr-lotes">
            <div v-for="l in lotes.filas" :key="l.id" class="pr-lote">
              <div class="pr-lote-main">
                <b>{{ fmtFecha(l.fecha) }} · {{ origenLote(l.origen) }}</b>
                <small>{{ [l.proveedor, l.nro_factura ? `Factura ${l.nro_factura}` : ''].filter(Boolean).join(' · ') || '—' }}</small>
                <span v-if="l.vence" class="pr-chip" :class="claseVence(l.vence)"><i class="bi bi-calendar-x"></i> Vence {{ fmtFecha(l.vence) }}</span>
              </div>
              <div class="pr-lote-nums">
                <div><small>Disponible</small><b>{{ fmtCant(l.disponible) }} / {{ fmtCant(l.cantidad_inicial) }}</b></div>
                <div><small>Costo</small><b>{{ fmt(l.costo) }}</b></div>
                <div><small>Valor</small><b>{{ fmt(l.costo * l.disponible) }}</b></div>
              </div>
            </div>
            <div class="pr-lote-total">Valor del inventario: <b>{{ fmt(lotes.filas.reduce((a, l) => a + l.costo * l.disponible, 0)) }}</b></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Replicar por IMEI -->
    <div v-if="modal === 'replicar'" class="pr-overlay" @click.self="cerrar">
      <div class="pr-modal">
        <div class="pr-modal-head"><b>Replicar producto</b><button class="pr-x" @click="cerrar"><i class="bi bi-x-lg"></i></button></div>
        <div class="pr-modal-body">
          <div class="pr-ref">{{ sel.name }}<small>{{ sel.product_code }} · {{ fmt(sel.price) }}</small></div>
          <p class="pr-nota">Cada réplica es un producto nuevo con el mismo precio, categoría y proveedor, su propio código (IMEI) y cantidad 1.</p>
          <div class="pr-field"><label>Nombre del producto a replicar</label><input v-model.trim="rep.nombre_base" class="pr-inp" maxlength="200" /></div>
          <div v-if="!rep.codigos.length" class="pr-row pr-row--end">
            <div class="pr-field"><label>Cantidad de réplicas</label><input v-model.number="rep.cantidad" type="number" min="1" max="200" class="pr-inp pr-num" /></div>
            <button class="pr-btn" @click="iniciarReplica"><i class="bi bi-play-fill me-1"></i>Iniciar</button>
          </div>
          <template v-else>
            <div class="pr-resumen">{{ listos }} de {{ rep.codigos.length }} códigos digitados</div>
            <div class="pr-imeis">
              <div v-for="(c, i) in rep.codigos" :key="i" class="pr-imei" :class="{ 'pr-imei--dup': c.trim() && duplicados.has(c.trim()) }">
                <span>{{ i + 1 }}</span>
                <input :ref="el => (imeiRefs[i] = el)" v-model="rep.codigos[i]" class="pr-inp" maxlength="60" autocomplete="off"
                       :placeholder="`Código réplica ${i + 1}`" @keydown.enter.prevent="siguienteImei(i)" />
              </div>
            </div>
          </template>
        </div>
        <div class="pr-modal-foot">
          <button class="pr-btn pr-btn--sec" @click="rep.codigos.length ? (rep.codigos = []) : cerrar()">{{ rep.codigos.length ? 'Cancelar replicar' : 'Cerrar' }}</button>
          <button v-if="rep.codigos.length" class="pr-btn" :disabled="enviando || listos !== rep.codigos.length || duplicados.size > 0" @click="guardarReplica">
            <span v-if="enviando" class="spinner-border spinner-border-sm me-1"></span>Replicar {{ rep.codigos.length }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// Productos para comercio: misma tabla de los platos (pos_dishes), solo con lo que un comercio necesita.
import { ref, computed, onMounted, nextTick } from 'vue'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'
import { useModuleName } from '@/composables/useModuleName'
import CurrencyInput from '@/components/CurrencyInput.vue'
import ImageUploader from '@/components/ImageUploader.vue'
import AvisoBodega from '@/components/AvisoBodega.vue'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'

const { moduleName } = useModuleName()
const BASE = '/api/productos'
const FOTO = '/api/pos-catalogo/platos'
const API_BASE = import.meta.env.VITE_API_URL || ''

const productos = ref([])
const cat = ref({ categorias: [], proveedores: [], laboratorios: [], drogueria: false, cargue_unitario: false, con_escritorio: false, administrado_por: null })
const cargando = ref(true)
const buscar = ref('')
const filtroCat = ref('')
const filtroEstado = ref('activos')
const modal = ref('')
const enviando = ref(false)
const form = ref({})
const original = ref({})
const fotoPendiente = ref(null)
const fotoEliminada = ref(false)
const sel = ref(null)
const rep = ref({ nombre_base: '', cantidad: 1, codigos: [] })
const imeiRefs = ref([])
const lotes = ref({ cargando: false, filas: [] })
const nuevoLab = ref({ abierto: false, nombre: '', enviando: false })
const ORIGENES = { SALDO_INICIAL: 'Saldo inicial', FACTURA: 'Factura de proveedor', ENTRADA: 'Entrada', TRASLADO: 'Traslado',
                   AJUSTE: 'Ajuste de inventario', DEVOLUCION: 'Devolución' }
const origenLote = (o) => ORIGENES[o] || o
const fmtFecha = (f) => (f ? new Date(`${f}T00:00:00`).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' }) : '')
const claseVence = (f) => {
  const dias = (new Date(`${f}T00:00:00`) - new Date(new Date().toDateString())) / 86400000
  return dias < 0 ? 'pr-chip--vencido' : dias <= 60 ? 'pr-chip--pend' : 'pr-chip--ok'
}

const usuario = (() => { try { return JSON.parse(localStorage.getItem('user') || '{}') } catch { return {} } })()
const fmtMoneda = new Intl.NumberFormat(usuario.locale || 'es-CO', { style: 'currency', currency: usuario.currency_code || 'COP', maximumFractionDigits: 0 })
const fmt = (v) => fmtMoneda.format(Number(v) || 0)
const fmtCant = (v) => new Intl.NumberFormat('es-CO', { maximumFractionDigits: 2 }).format(Number(v) || 0)
const imgSrc = (p) => (!p ? null : (p.startsWith('blob:') || p.startsWith('http') ? p : API_BASE + p))
const errorDe = (e, porDefecto) => {
  const d = e?.response?.data?.detail
  return Array.isArray(d) ? 'Revise los valores ingresados' : (d || porDefecto)
}

const filtrados = computed(() => {
  const q = buscar.value.toLowerCase()
  return productos.value.filter(p => (filtroEstado.value === 'todos' || (filtroEstado.value === 'activos' ? !p.active : p.active))
    && (!filtroCat.value || p.categoria === filtroCat.value)
    && (!q || [p.name, p.product_code, p.categoria].some(v => (v || '').toLowerCase().includes(q))))
})
const valoresBloqueados = computed(() => !!cat.value.administrado_por && !!form.value.id)
const listos = computed(() => rep.value.codigos.filter(c => c.trim()).length)
const duplicados = computed(() => {
  const vistos = new Set(), dup = new Set()
  rep.value.codigos.forEach(c => { const k = c.trim(); if (!k) return; if (vistos.has(k)) dup.add(k); vistos.add(k) })
  return dup
})

async function cargar() {
  cargando.value = true
  try {
    const [p, c] = await Promise.all([api.get(BASE), api.get(`${BASE}/catalogos`)])
    productos.value = p.data
    cat.value = c.data
  } catch (e) { showToast(errorDe(e, 'Error cargando los productos'), 'error') }
  cargando.value = false
}

function cerrar() { if (!enviando.value) modal.value = '' }

function abrirNuevo() {
  form.value = { id: null, name: '', product_code: '', category_id: 0, id_proveedor: 0, price: 0, wholesale_price: 0,
                 product_cost: 0, tax: 0, minimum_stock: 0, cantidad_inicial: 0, extra_print: !!cat.value.cargue_unitario,
                 ask_product_description: false, photo_path: null, id_laboratorio: 0, fecha_vence: '' }
  nuevoLab.value = { abierto: false, nombre: '', enviando: false }
  fotoPendiente.value = null; fotoEliminada.value = false
  modal.value = 'form'
}

function abrirEditar(p) {
  form.value = { id: p.id, name: p.name, product_code: p.product_code, category_id: p.category_id || 0,
                 id_proveedor: p.id_proveedor || 0, price: p.price, wholesale_price: p.wholesale_price,
                 product_cost: p.product_cost, tax: p.tax, minimum_stock: p.minimum_stock, extra_print: !!p.extra_print,
                 ask_product_description: !!p.ask_product_description, photo_path: p.photo_path || null,
                 id_laboratorio: p.id_laboratorio || 0 }
  original.value = { ...form.value }
  nuevoLab.value = { abierto: false, nombre: '', enviando: false }
  fotoPendiente.value = null; fotoEliminada.value = false
  modal.value = 'form'
}

async function guardar() {
  const f = form.value
  if (!f.name) return showToast('Digite el nombre del producto', 'warning')
  if (!f.category_id) return showToast('Escoja la categoría', 'warning')
  if (cat.value.cargue_unitario && !f.id_proveedor) return showToast('Escoja el proveedor (obligatorio en cargue unitario)', 'warning')
  if (f.wholesale_price && f.price && f.wholesale_price > f.price) return showToast('El precio mínimo no puede ser mayor que el precio de venta', 'warning')
  if (cat.value.drogueria && !f.id && (f.cantidad_inicial || 0) > 0 && !f.fecha_vence) return showToast('Escoja el vencimiento del lote inicial', 'warning')
  enviando.value = true
  try {
    let id = f.id
    if (!id) {
      const { data } = await api.post(BASE, { ...f, cantidad_inicial: Math.max(0, Math.floor(f.cantidad_inicial || 0)),
                                              id_laboratorio: f.id_laboratorio || null, fecha_vence: f.fecha_vence || null })
      id = data.id
      showToast(data.aviso ? `Producto creado. ${data.aviso}` : 'Producto creado', 'success')
    } else {
      const cambios = Object.fromEntries(Object.entries(f).filter(([k, v]) => k !== 'id' && k !== 'photo_path' && v !== original.value[k]))
      if (valoresBloqueados.value) ['price', 'wholesale_price', 'product_cost', 'tax', 'minimum_stock'].forEach(k => delete cambios[k])
      if (Object.keys(cambios).length) await api.put(`${BASE}/${id}`, cambios)
      if (fotoPendiente.value) {
        const fd = new FormData(); fd.append('file', fotoPendiente.value, 'photo.webp')
        await api.post(`${FOTO}/${id}/foto`, fd)
      } else if (fotoEliminada.value) {
        await api.delete(`${FOTO}/${id}/foto`)
      }
      showToast('Producto actualizado', 'success')
    }
    enviando.value = false
    modal.value = ''
    await cargar()
  } catch (e) { showToast(errorDe(e, 'Error al guardar el producto'), 'error') }
  enviando.value = false
}

async function cambiarEstado(p) {
  try {
    await api.post(`${BASE}/${p.id}/estado`, { activo: !!p.active })
    p.active = p.active ? 0 : 1
    showToast(p.active ? 'Producto desactivado' : 'Producto activado', 'success')
  } catch (e) { showToast(errorDe(e, 'Error al cambiar el estado'), 'error') }
}

async function crearLab() {
  const nombre = nuevoLab.value.nombre
  if (!nombre || nombre.length < 2) return showToast('Digite el nombre del laboratorio', 'warning')
  nuevoLab.value.enviando = true
  try {
    const { data } = await api.post(`${BASE}/laboratorios`, { nombre })
    if (!cat.value.laboratorios.some(l => l.id === data.id)) cat.value.laboratorios.push(data)
    form.value.id_laboratorio = data.id
    nuevoLab.value = { abierto: false, nombre: '', enviando: false }
  } catch (e) { showToast(errorDe(e, 'Error al crear el laboratorio'), 'error') }
  nuevoLab.value.enviando = false
}

async function abrirLotes(p) {
  sel.value = p
  lotes.value = { cargando: true, filas: [] }
  modal.value = 'lotes'
  try {
    const { data } = await api.get(`${BASE}/${p.id}/lotes`)
    lotes.value.filas = data.lotes
  } catch (e) { showToast(errorDe(e, 'Error cargando los lotes'), 'error') }
  lotes.value.cargando = false
}

function abrirReplicar(p) {
  sel.value = p
  rep.value = { nombre_base: p.name, cantidad: 1, codigos: [] }
  modal.value = 'replicar'
}

async function iniciarReplica() {
  const n = Math.floor(rep.value.cantidad || 0)
  if (n < 1 || n > 200) return showToast('La cantidad debe estar entre 1 y 200', 'warning')
  rep.value.codigos = Array.from({ length: n }, () => '')
  imeiRefs.value = []
  await nextTick()
  imeiRefs.value[0]?.focus()
}

function siguienteImei(i) {
  const s = imeiRefs.value[i + 1]
  if (s) s.focus()
  else if (listos.value === rep.value.codigos.length && !duplicados.value.size) guardarReplica()
}

async function guardarReplica() {
  enviando.value = true
  try {
    const { data } = await api.post(`${BASE}/${sel.value.id}/replicar`, { nombre_base: rep.value.nombre_base, codigos: rep.value.codigos.map(c => c.trim()) })
    showToast(`${data.creados.length} producto(s) creados con cantidad 1`, 'success')
    enviando.value = false
    modal.value = ''
    await cargar()
  } catch (e) { showToast(errorDe(e, 'Error al replicar'), 'error') }
  enviando.value = false
}

onMounted(cargar)
</script>

<style scoped>
.pr-page { padding: 20px 24px 32px; }
.pr-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 12px; }
.pr-title { font-size: 22px; font-weight: 800; color: #1e293b; margin: 0; }
.pr-sub { font-size: 13px; color: #64748b; margin: 2px 0 0; display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.pr-chip { display: inline-flex; align-items: center; gap: 4px; font-size: 11.5px; font-weight: 700; padding: 3px 8px; border-radius: 999px; background: #eef2ff; color: #3730a3; white-space: nowrap; }
.pr-chip--imei { background: #fef3c7; color: #92400e; }
.pr-chip--pend { background: #fef9c3; color: #854d0e; }
.pr-chip--vencido { background: #fee2e2; color: #991b1b; }
.pr-chip--ok { background: #dcfce7; color: #166534; }
.pr-lab { display: flex; gap: 6px; align-items: center; }
.pr-lab + .pr-lab { margin-top: 6px; }
.pr-modal--ancho { max-width: 720px; }
.pr-lotes { display: flex; flex-direction: column; gap: 8px; }
.pr-lote { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; align-items: center; border: 1px solid #e2e8f0; border-radius: 10px; padding: 8px 10px; }
.pr-lote-main { display: flex; flex-direction: column; gap: 3px; align-items: flex-start; }
.pr-lote-main b { font-size: 13.5px; color: #1e293b; }
.pr-lote-main small { font-size: 12px; color: #64748b; }
.pr-lote-nums { display: grid; grid-template-columns: repeat(3, minmax(80px, auto)); gap: 10px; text-align: right; }
.pr-lote-nums small { display: block; font-size: 10.5px; color: #94a3b8; font-weight: 700; text-transform: uppercase; }
.pr-lote-nums b { font-size: 13px; color: #1e293b; }
.pr-lote-total { text-align: right; font-size: 14px; color: #334155; padding-top: 4px; }
.pr-aviso { font-size: 13px; color: #1e40af; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 10px; padding: 8px 12px; margin: 0 0 12px; }
.pr-toolbar { display: grid; grid-template-columns: minmax(0, 1fr) 220px 150px; gap: 8px; margin-bottom: 6px; }
.pr-search { position: relative; }
.pr-search i { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: #94a3b8; }
.pr-search .pr-inp { padding-left: 32px; }
.pr-resumen { font-size: 12.5px; color: #64748b; margin-bottom: 8px; }
.pr-state { display: flex; justify-content: center; padding: 50px; }
.pr-vacio { text-align: center; color: #94a3b8; padding: 40px 10px; }
.pr-vacio i { font-size: 34px; }
.pr-inp { border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 8px 10px; font-size: 14px; color: #1e293b; background: #fff; width: 100%; }
.pr-inp:focus { outline: none; border-color: #1d4ed8; }
.pr-inp:disabled { background: #f8fafc; color: #64748b; }
.pr-num { text-align: right; }
.pr-btn { display: inline-flex; align-items: center; justify-content: center; background: linear-gradient(90deg,#1e3a5f,#1d4ed8); color: #fff; border: none; border-radius: 10px; padding: 9px 16px; font-weight: 700; font-size: 14px; cursor: pointer; white-space: nowrap; }
.pr-btn:disabled { opacity: .55; cursor: not-allowed; }
.pr-btn--sec { background: #e2e8f0; color: #334155; }
.pr-btn-sm { display: inline-flex; align-items: center; gap: 5px; border: 1.5px solid #bfdbfe; background: #eff6ff; color: #1d4ed8; border-radius: 8px; padding: 6px 10px; font-size: 12.5px; font-weight: 700; cursor: pointer; white-space: nowrap; }
.pr-btn-sm--imei { border-color: #fde68a; background: #fffbeb; color: #92400e; }
.pr-btn-sm--gris { border-color: #e2e8f0; background: #f8fafc; color: #475569; }
.pr-lista { display: flex; flex-direction: column; gap: 8px; }
.pr-prod { display: grid; grid-template-columns: minmax(0, 1fr) auto auto; gap: 12px; align-items: center; background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 10px 12px; }
.pr-prod--off { opacity: .6; }
.pr-prod-nombre { font-weight: 800; color: #1e293b; font-size: 14px; word-break: break-word; }
.pr-prod-meta { display: flex; flex-wrap: wrap; gap: 4px 12px; font-size: 12px; color: #64748b; margin-top: 2px; }
.pr-prod-nums { display: grid; grid-template-columns: repeat(5, minmax(80px, auto)); gap: 10px; text-align: right; }
.pr-prod-nums small { display: block; font-size: 10.5px; color: #94a3b8; font-weight: 700; text-transform: uppercase; }
.pr-prod-nums b { font-size: 13.5px; color: #1e293b; }
.pr-stock b { color: #15803d; }
.pr-stock--bajo b { color: #b91c1c; }
.pr-prod-acc { display: flex; flex-direction: column; gap: 6px; }
.pr-overlay { position: fixed; inset: 0; background: rgba(15,23,42,.5); display: flex; align-items: center; justify-content: center; z-index: 1050; padding: 16px; }
.pr-modal { background: #fff; border-radius: 14px; width: 100%; max-width: 580px; max-height: 92vh; display: flex; flex-direction: column; }
.pr-modal-head { display: flex; justify-content: space-between; align-items: center; padding: 14px 16px; border-bottom: 1px solid #e2e8f0; }
.pr-modal-head b { font-size: 16px; color: #1e293b; }
.pr-x { border: none; background: none; font-size: 18px; color: #64748b; cursor: pointer; }
.pr-modal-body { padding: 14px 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
.pr-modal-foot { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 16px; border-top: 1px solid #e2e8f0; }
.pr-field { display: flex; flex-direction: column; gap: 4px; flex: 1; min-width: 0; }
.pr-field label { font-size: 12px; font-weight: 700; color: #475569; }
.pr-row { display: flex; gap: 10px; }
.pr-row--end { align-items: flex-end; }
.pr-fijo { padding: 8px 10px; background: #f8fafc; border-radius: 8px; font-size: 13px; color: #64748b; }
.pr-nota { font-size: 12px; color: #64748b; margin: 0; }
.pr-switch { display: flex; align-items: center; gap: 10px; font-size: 14px; color: #334155; cursor: pointer; margin: 0; }
.pr-switch input { width: 18px; height: 18px; accent-color: #1d4ed8; }
.pr-ref { font-weight: 800; color: #1e293b; display: flex; flex-direction: column; background: #f8fafc; border-radius: 10px; padding: 8px 10px; }
.pr-ref small { font-weight: 500; color: #64748b; }
.pr-imeis { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; }
.pr-imei { display: flex; align-items: center; gap: 6px; }
.pr-imei span { width: 26px; text-align: right; font-size: 12px; color: #94a3b8; font-weight: 700; flex-shrink: 0; }
.pr-imei--dup .pr-inp { border-color: #dc2626; background: #fef2f2; }

@media (max-width: 1024px) {
  .pr-prod { grid-template-columns: minmax(0, 1fr) auto; }
  .pr-prod-nums { grid-column: 1 / -1; grid-template-columns: repeat(5, 1fr); text-align: left; }
  .pr-prod-acc { grid-row: 1; grid-column: 2; }
}
@media (max-width: 768px) {
  .pr-page { padding: 14px 12px 80px; }
  .pr-head { flex-direction: column; align-items: stretch; }
  .pr-toolbar { grid-template-columns: 1fr 1fr; }
  .pr-search { grid-column: 1 / -1; }
  .pr-imeis { grid-template-columns: 1fr; }
  .pr-lote { grid-template-columns: 1fr; }
  .pr-lote-nums { text-align: left; }
  .pr-overlay { align-items: flex-end; padding: 0; }
  .pr-modal { max-width: none; border-radius: 14px 14px 0 0; max-height: 94vh; }
}
@media (max-width: 576px) {
  .pr-title { font-size: 18px; }
  .pr-row { flex-direction: column; gap: 10px; }
  .pr-row--end { align-items: stretch; }
  .pr-prod { grid-template-columns: 1fr; }
  .pr-prod-acc { grid-row: auto; grid-column: auto; flex-direction: row; flex-wrap: wrap; }
  .pr-prod-acc .pr-btn-sm { flex: 1; justify-content: center; }
  .pr-prod-nums { grid-template-columns: repeat(2, 1fr); }
  .pr-lote-nums { grid-template-columns: repeat(2, 1fr); }
}
</style>
