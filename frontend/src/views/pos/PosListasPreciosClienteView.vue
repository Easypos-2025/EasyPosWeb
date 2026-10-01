<template>
  <div class="lp-view">
    <div class="lp-header">
      <div>
        <h5 class="lp-title">{{ moduleName }}</h5>
        <p class="lp-sub">La <b>lista general</b> tiene todos los productos con su precio. Cada cliente puede tener una lista propia que la reemplaza.</p>
      </div>
    </div>

    <div class="lp-grid">
      <!-- ── Clientes ── -->
      <section class="lp-panel lp-clientes" :class="{ 'lp-hide-mobile': cliente }">
        <div class="lp-search">
          <i class="bi bi-search"></i>
          <input v-model="qCliente" @input="debBuscarClientes" placeholder="Buscar cliente por nombre, cédula o teléfono..." maxlength="60" />
        </div>
        <button :class="['cli-row', 'cli-general', { active: general }]" @click="seleccionarGeneral">
          <div class="cli-main">
            <span class="cli-name"><i class="bi bi-list-ul me-1"></i> Lista general (por defecto)</span>
            <span class="cli-doc">Todos los productos activos y sus variantes</span>
          </div>
        </button>
        <button class="btn-link-add" @click="abrirCrearCliente"><i class="bi bi-person-plus"></i> Crear cliente</button>
        <div v-if="loadingClientes" class="lp-empty"><span class="spinner-border spinner-border-sm"></span></div>
        <div v-else-if="!clientes.length" class="lp-empty">Sin clientes</div>
        <button v-for="c in clientes" :key="c.id_cliente"
                :class="['cli-row', { active: cliente?.id_cliente === c.id_cliente, 'cli-cf': c.id_cliente === 1 }]"
                @click="seleccionarCliente(c)">
          <div class="cli-main">
            <span class="cli-name">{{ c.nombre }}</span>
            <span class="cli-doc">{{ c.cedula || '—' }}</span>
          </div>
          <span v-if="c.lista_activa" class="cli-tag" :title="c.lista_activa"><i class="bi bi-tags-fill"></i></span>
        </button>
      </section>

      <!-- ── Listas del cliente ── -->
      <section class="lp-panel lp-detalle" :class="{ 'lp-hide-mobile': !cliente }">
        <div v-if="!cliente" class="lp-empty lp-empty--big">
          <i class="bi bi-person-lines-fill"></i>
          <p>Seleccione un cliente para ver o crear su lista de precios.</p>
        </div>
        <template v-else>
          <div class="det-hdr">
            <button class="btn-back only-mobile" @click="cliente = null; lista = null"><i class="bi bi-arrow-left"></i></button>
            <div class="det-cli">
              <div class="det-cli-name">{{ cliente.nombre }}</div>
              <div class="det-cli-doc">{{ cliente.cedula || 'Sin cédula' }} · Id {{ cliente.id_cliente }}</div>
            </div>
            <button v-if="cliente.id_cliente !== 1 && !general" class="btn-primary-sm" @click="abrirNuevaLista"><i class="bi bi-plus-lg"></i> Nueva lista</button>
          </div>

          <div v-if="general" class="info-line">
            <i class="bi bi-info-circle"></i> Es el precio de cada producto y variante: cambiarlo aquí cambia el precio del plato (y al revés). Se cobra cuando el cliente no tiene lista propia activa.
          </div>
          <div v-else-if="cliente.id_cliente === 1" class="info-line">
            <i class="bi bi-info-circle"></i> Consumidor Final paga siempre el precio de la carta; no se le asigna lista.
          </div>

          <!-- Historial de listas -->
          <div v-if="listas.length" class="listas-chips">
            <button v-for="l in listas" :key="l.id_lista"
                    :class="['lchip', { active: lista?.id_lista === l.id_lista, on: l.activa }]"
                    @click="cargarLista(l.id_lista)">
              <span class="lchip-dot"></span>{{ l.nombre }}
              <small>{{ l.productos }} prod.</small>
            </button>
          </div>
          <div v-else-if="cliente.id_cliente !== 1 && !general" class="lp-empty">El cliente no tiene listas. Cree una con "Nueva lista".</div>

          <!-- Lista seleccionada -->
          <div v-if="lista" class="lista-box">
            <div class="lista-top">
              <div class="lista-info">
                <div v-if="general" class="lista-name"><span class="lista-general-name">{{ lista.nombre }}</span></div>
                <div v-else class="lista-name">
                  <input v-model="lista.nombre" class="inp-inline" maxlength="100" @change="guardarCabecera" />
                  <span :class="['badge-st', lista.activa ? 'st-on' : 'st-off']">{{ lista.activa ? 'Activa' : 'Inactiva' }}</span>
                </div>
                <template v-if="!general">
                  <input v-model="lista.observacion" class="inp-inline inp-obs" maxlength="255" placeholder="Observación…" @change="guardarCabecera" />
                  <div class="lista-meta">{{ lista.fecha || '' }} · {{ lista.usuario || '' }}</div>
                </template>
              </div>
              <template v-if="!general">
                <button v-if="lista.activa" class="btn-soft-danger" @click="toggleActiva(false)"><i class="bi bi-pause-circle"></i> Desactivar</button>
                <button v-else class="btn-soft-ok" @click="toggleActiva(true)"><i class="bi bi-check-circle"></i> Activar</button>
              </template>
            </div>

            <div class="add-row">
              <div class="lp-search lp-search--sm">
                <i class="bi bi-search"></i>
                <input v-model="qItems" placeholder="Filtrar productos de la lista..." maxlength="60" />
              </div>
              <button v-if="!general" class="btn-link-add" @click="abrirAgregar"><i class="bi bi-plus-circle"></i> Agregar producto</button>
            </div>
            <div v-if="bajoMinimo" class="warn-line"><i class="bi bi-exclamation-triangle"></i> {{ bajoMinimo }} producto(s) por debajo del precio mínimo.</div>

            <div v-if="loadingLista" class="lp-empty"><span class="spinner-border spinner-border-sm"></span></div>
            <table v-else class="tbl">
              <thead><tr><th>Producto</th><th class="hide-sm">Categoría</th><th v-if="!general" class="text-right hide-sm">General</th><th class="text-right">{{ general ? 'Precio' : 'Precio cliente' }}</th><th></th></tr></thead>
              <tbody>
                <tr v-for="it in itemsFiltrados" :key="`${it.id_producto}-${it.id_presentacion}`"
                    :class="{ 'row-warn': it.bajo_minimo, 'row-off': it.desactivado, 'row-var': it.id_presentacion > 0 }">
                  <td>
                    <div class="it-name">
                      <i v-if="it.id_presentacion > 0" class="bi bi-arrow-return-right text-muted me-1"></i>{{ it.name }}
                      <span v-if="it.var_default" class="chip-def">Por defecto</span>
                    </div>
                    <div v-if="it.bajo_minimo" class="it-warn">Mínimo {{ fmt(it.precio_minimo) }}</div>
                  </td>
                  <td class="hide-sm text-muted">{{ it.categoria || '—' }}</td>
                  <td v-if="!general" class="text-right hide-sm text-muted">{{ fmt(it.precio_base) }}</td>
                  <td class="text-right">
                    <CurrencyInput :model-value="it.precio" class="inp-price" @update:model-value="v => editarPrecio(it, v)" />
                  </td>
                  <td><button v-if="!general && !it.id_presentacion" class="btn-x-sm" @click="quitar(it)" title="Quitar (con sus variantes)"><i class="bi bi-x-lg"></i></button></td>
                </tr>
                <tr v-if="!itemsFiltrados.length"><td colspan="5" class="text-center text-muted">Sin productos</td></tr>
              </tbody>
            </table>
          </div>
        </template>
      </section>
    </div>

    <!-- Nueva lista -->
    <div v-if="modalNueva.show" class="modal-overlay" @click.self="modalNueva.show = false">
      <div class="modal-box">
        <div class="mh"><span>Nueva lista — {{ cliente?.nombre }}</span><button class="btn-x" @click="modalNueva.show = false"><i class="bi bi-x-lg"></i></button></div>
        <div class="mb">
          <label class="lbl">Nombre *</label>
          <input v-model="modalNueva.nombre" class="inp" maxlength="100" placeholder="Ej: Mayorista octubre" />
          <label class="lbl">Observación</label>
          <input v-model="modalNueva.observacion" class="inp" maxlength="255" />
          <label class="lbl">Cargar precios desde</label>
          <label class="opt"><input type="radio" value="platos" v-model="modalNueva.origen" /> Todos los productos activos con su precio de carta</label>
          <label class="opt" :class="{ disabled: !listas.length }"><input type="radio" value="anterior" v-model="modalNueva.origen" :disabled="!listas.length" /> Copiar la lista anterior del cliente</label>
          <p v-if="listas.some(l => l.activa)" class="warn-line"><i class="bi bi-info-circle"></i> La lista activa actual quedará desactivada.</p>
        </div>
        <div class="mf">
          <button class="btn-cancel" @click="modalNueva.show = false">Cancelar</button>
          <button class="btn-primary-sm" :disabled="modalNueva.saving || !modalNueva.nombre.trim()" @click="crearLista">
            {{ modalNueva.saving ? 'Creando…' : 'Crear lista' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Agregar producto -->
    <div v-if="modalAgregar.show" class="modal-overlay" @click.self="modalAgregar.show = false">
      <div class="modal-box">
        <div class="mh"><span>Agregar producto a la lista</span><button class="btn-x" @click="modalAgregar.show = false"><i class="bi bi-x-lg"></i></button></div>
        <div class="mb">
          <div class="lp-search">
            <i class="bi bi-search"></i>
            <input v-model="modalAgregar.q" @input="debBuscarProductos" placeholder="Buscar producto..." maxlength="60" />
          </div>
          <div class="prod-list">
            <button v-for="p in productosDisponibles" :key="p.id" class="prod-row" @click="agregarProducto(p)">
              <span class="prod-name">{{ p.name }}</span>
              <span class="text-muted">{{ fmt(p.price) }}</span>
              <i class="bi bi-plus-circle"></i>
            </button>
            <div v-if="!productosDisponibles.length" class="lp-empty">Sin productos por agregar</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Crear cliente -->
    <div v-if="modalCliente.show" class="modal-overlay" @click.self="modalCliente.show = false">
      <div class="modal-box">
        <div class="mh"><span>Nuevo cliente</span><button class="btn-x" @click="modalCliente.show = false"><i class="bi bi-x-lg"></i></button></div>
        <div class="mb">
          <label class="lbl">Nombre *</label><input v-model="modalCliente.nombres" class="inp" maxlength="150" />
          <label class="lbl">Cédula / NIT</label><input v-model="modalCliente.cedula" class="inp" maxlength="50" />
          <label class="lbl">Teléfono</label><input v-model="modalCliente.telefono" class="inp" maxlength="50" />
          <label class="lbl">Dirección</label><input v-model="modalCliente.direccion" class="inp" maxlength="255" />
        </div>
        <div class="mf">
          <button class="btn-cancel" @click="modalCliente.show = false">Cancelar</button>
          <button class="btn-primary-sm" :disabled="modalCliente.saving || !modalCliente.nombres.trim()" @click="crearCliente">Crear</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/apis.js'
import { showToast } from '@/utils/toast.js'
import { useModuleName } from '@/composables/useModuleName'

const BASE = '/api/pos-catalogo/listas-cliente'
const { moduleName } = useModuleName()
const fmtCOP = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })
const fmt = v => fmtCOP.format(Number(v) || 0)

const clientes = ref([])
const qCliente = ref('')
const loadingClientes = ref(false)
const cliente = ref(null)
const listas = ref([])
const lista = ref(null)
const items = ref([])
const loadingLista = ref(false)
const qItems = ref('')
const general = ref(false)          // lista general (por defecto): Id_Lista = 0

const modalNueva   = ref({ show: false, nombre: '', observacion: '', origen: 'platos', saving: false })
const modalAgregar = ref({ show: false, q: '', productos: [] })
const modalCliente = ref({ show: false, nombres: '', cedula: '', telefono: '', direccion: '', saving: false })

let tCli = null, tProd = null
const debBuscarClientes = () => { clearTimeout(tCli); tCli = setTimeout(buscarClientes, 250) }
const debBuscarProductos = () => { clearTimeout(tProd); tProd = setTimeout(buscarProductos, 250) }

const itemsFiltrados = computed(() => {
  const q = qItems.value.trim().toLowerCase()
  return q ? items.value.filter(i => i.name.toLowerCase().includes(q)) : items.value
})
const bajoMinimo = computed(() => items.value.filter(i => i.bajo_minimo).length)
const productosDisponibles = computed(() => {
  const ya = new Set(items.value.filter(i => !i.id_presentacion).map(i => i.id_producto))
  return modalAgregar.value.productos.filter(p => !ya.has(p.id))
})

async function buscarClientes() {
  loadingClientes.value = true
  try { clientes.value = (await api.get(`${BASE}/clientes`, { params: { q: qCliente.value || undefined } })).data }
  catch (e) { showToast(e?.response?.data?.detail || 'Error cargando clientes', 'error') }
  finally { loadingClientes.value = false }
}

async function seleccionarGeneral() {
  general.value = true
  cliente.value = { id_cliente: 0, nombre: 'Lista general (por defecto)', cedula: '' }
  listas.value = []
  loadingLista.value = true
  try {
    const { data } = await api.get(`${BASE}/general`)
    lista.value = data.lista
    items.value = data.items
  } catch (e) { showToast(e?.response?.data?.detail || 'Error cargando la lista general', 'error') }
  finally { loadingLista.value = false }
}

async function seleccionarCliente(c) {
  general.value = false
  lista.value = null; items.value = []
  try {
    const { data } = await api.get(`${BASE}/cliente/${c.id_cliente}`)
    cliente.value = data.cliente
    listas.value = data.listas
    const activa = data.listas.find(l => l.activa) || data.listas[0]
    if (activa) await cargarLista(activa.id_lista)
  } catch (e) { showToast(e?.response?.data?.detail || 'Error cargando cliente', 'error') }
}

async function recargarListas() {
  const { data } = await api.get(`${BASE}/cliente/${cliente.value.id_cliente}`)
  listas.value = data.listas
}

async function cargarLista(id) {
  loadingLista.value = true
  try {
    const { data } = await api.get(`${BASE}/lista/${id}`)
    lista.value = data.lista
    items.value = data.items
  } catch (e) { showToast(e?.response?.data?.detail || 'Error cargando lista', 'error') }
  finally { loadingLista.value = false }
}

function abrirNuevaLista() {
  modalNueva.value = { show: true, nombre: '', observacion: '', origen: 'platos', saving: false }
}
async function crearLista() {
  const m = modalNueva.value
  m.saving = true
  try {
    const { data } = await api.post(`${BASE}/lista`, {
      id_cliente: cliente.value.id_cliente, nombre: m.nombre.trim(), observacion: m.observacion.trim() || null, origen: m.origen,
    })
    m.show = false
    showToast('Lista creada', 'success')
    await recargarListas()
    await cargarLista(data.id_lista)
    buscarClientes()
  } catch (e) { showToast(e?.response?.data?.detail || 'Error creando lista', 'error') }
  finally { m.saving = false }
}

async function guardarCabecera() {
  if (!lista.value.nombre?.trim()) { showToast('El nombre es obligatorio', 'warning'); return }
  try {
    await api.put(`${BASE}/lista/${lista.value.id_lista}`, { nombre: lista.value.nombre.trim(), observacion: lista.value.observacion || null })
    await recargarListas()
  } catch (e) { showToast(e?.response?.data?.detail || 'Error', 'error') }
}

async function toggleActiva(activar) {
  try {
    await api.post(`${BASE}/lista/${lista.value.id_lista}/${activar ? 'activar' : 'desactivar'}`)
    lista.value.activa = activar ? 1 : 0
    await recargarListas()
    buscarClientes()
    showToast(activar ? 'Lista activada' : 'Lista desactivada', 'success')
  } catch (e) { showToast(e?.response?.data?.detail || 'Error', 'error') }
}

async function editarPrecio(it, v) {
  const precio = Number(v) || 0
  if (precio === it.precio) return
  try {
    const url = general.value ? `${BASE}/general/item/${it.id_producto}` : `${BASE}/lista/${lista.value.id_lista}/item/${it.id_producto}`
    const { data } = await api.put(url, { precio }, { params: { presentacion: it.id_presentacion || 0 } })
    it.precio = precio
    // En la general, plato y variante por defecto quedan iguales: recargar para reflejarlo
    if (general.value && (it.var_default || !it.id_presentacion)) seleccionarGeneral()
    it.bajo_minimo = data.bajo_minimo
    if (data.bajo_minimo) showToast(`${it.name}: queda por debajo del precio mínimo`, 'warning')
  } catch (e) { showToast(e?.response?.data?.detail || 'Error', 'error') }
}

async function quitar(it) {
  try {
    await api.delete(`${BASE}/lista/${lista.value.id_lista}/item/${it.id_producto}`)
    items.value = items.value.filter(x => x.id_producto !== it.id_producto)
    recargarListas()
  } catch (e) { showToast(e?.response?.data?.detail || 'Error', 'error') }
}

async function abrirAgregar() {
  modalAgregar.value = { show: true, q: '', productos: [] }
  await buscarProductos()
}
async function buscarProductos() {
  try { modalAgregar.value.productos = (await api.get(`${BASE}/productos`, { params: { q: modalAgregar.value.q || undefined } })).data }
  catch { modalAgregar.value.productos = [] }
}
async function agregarProducto(p) {
  try {
    await api.post(`${BASE}/lista/${lista.value.id_lista}/item`, { id_producto: p.id, precio: p.price || 0 })
    await cargarLista(lista.value.id_lista)
    recargarListas()
    showToast(`${p.name} agregado`, 'success')
  } catch (e) { showToast(e?.response?.data?.detail || 'Error', 'error') }
}

function abrirCrearCliente() {
  modalCliente.value = { show: true, nombres: '', cedula: '', telefono: '', direccion: '', saving: false }
}
async function crearCliente() {
  const m = modalCliente.value
  m.saving = true
  try {
    const { data } = await api.post(`${BASE}/clientes`, {
      nombres: m.nombres.trim(), cedula: m.cedula.trim() || null, telefono: m.telefono.trim() || null, direccion: m.direccion.trim() || null,
    })
    m.show = false
    showToast('Cliente creado', 'success')
    await buscarClientes()
    await seleccionarCliente(data)
  } catch (e) { showToast(e?.response?.data?.detail || 'Error creando cliente', 'error') }
  finally { m.saving = false }
}

onMounted(buscarClientes)
</script>

<style scoped>
.lp-view { padding: 0; }
.lp-header { margin-bottom: 14px; }
.lp-title { font-weight: 700; font-size: 16px; color: #1e3a5f; margin: 0; }
.lp-sub { font-size: 13px; color: #64748b; margin: 2px 0 0; }
.lp-grid { display: grid; grid-template-columns: 320px 1fr; gap: 14px; align-items: start; }
.lp-panel { background: #fff; border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,.08); padding: 12px; min-width: 0; }
.lp-clientes { display: flex; flex-direction: column; gap: 6px; max-height: calc(100vh - 180px); overflow-y: auto; }
.lp-search { display: flex; align-items: center; gap: 6px; border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 7px 10px; background: #fff; }
.lp-search input { border: none; outline: none; flex: 1; font-size: 13px; min-width: 0; }
.lp-search--sm { flex: 1; }
.btn-link-add { background: none; border: none; color: #1d4ed8; font-size: 13px; font-weight: 700; cursor: pointer; text-align: left; padding: 4px 2px; white-space: nowrap; }
.cli-row { display: flex; align-items: center; gap: 8px; border: 1.5px solid #e2e8f0; background: #fff; border-radius: 10px; padding: 8px 10px; cursor: pointer; text-align: left; }
.cli-row:hover { border-color: #93c5fd; }
.cli-row.active { border-color: #1d4ed8; background: #eff6ff; }
.cli-cf { background: #f8fafc; }
.cli-main { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.cli-name { font-weight: 700; font-size: 13px; color: #1e3a5f; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cli-doc { font-size: 11px; color: #94a3b8; }
.cli-tag { color: #16a34a; }
.lp-empty { text-align: center; color: #94a3b8; font-size: 13px; padding: 16px; }
.lp-empty--big { padding: 60px 20px; }
.lp-empty--big i { font-size: 40px; display: block; margin-bottom: 8px; }
.det-hdr { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.det-cli { flex: 1; min-width: 0; }
.det-cli-name { font-weight: 800; font-size: 15px; color: #1e3a5f; }
.det-cli-doc { font-size: 12px; color: #64748b; }
.btn-back { border: none; background: #f1f5f9; border-radius: 8px; padding: 6px 10px; cursor: pointer; }
.btn-primary-sm { display: inline-flex; align-items: center; gap: 6px; background: linear-gradient(90deg,#1e3a5f,#1d4ed8); color: #fff; border: none; border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 700; cursor: pointer; white-space: nowrap; }
.btn-primary-sm:disabled { opacity: .6; cursor: not-allowed; }
.btn-cancel { background: #f1f5f9; border: none; border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 600; color: #475569; cursor: pointer; }
.btn-soft-danger { background: #fef2f2; border: 1.5px solid #fecaca; color: #b91c1c; border-radius: 8px; padding: 6px 12px; font-size: 12px; font-weight: 700; cursor: pointer; white-space: nowrap; }
.btn-soft-ok { background: #f0fdf4; border: 1.5px solid #bbf7d0; color: #15803d; border-radius: 8px; padding: 6px 12px; font-size: 12px; font-weight: 700; cursor: pointer; white-space: nowrap; }
.info-line { font-size: 12px; color: #1e40af; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 8px 10px; margin-bottom: 10px; }
.warn-line { font-size: 12px; color: #b45309; background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 6px 10px; margin: 6px 0; }
.listas-chips { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }
.lchip { display: flex; align-items: center; gap: 6px; border: 1.5px solid #e2e8f0; background: #f8fafc; border-radius: 999px; padding: 5px 12px; font-size: 12px; font-weight: 700; color: #475569; cursor: pointer; }
.lchip small { font-weight: 500; color: #94a3b8; }
.lchip-dot { width: 8px; height: 8px; border-radius: 50%; background: #cbd5e1; }
.lchip.on .lchip-dot { background: #16a34a; }
.lchip.active { border-color: #1d4ed8; background: #eff6ff; color: #1d4ed8; }
.lista-box { border: 1.5px solid #e2e8f0; border-radius: 12px; padding: 10px; }
.lista-top { display: flex; gap: 10px; align-items: flex-start; margin-bottom: 8px; }
.lista-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.lista-name { display: flex; align-items: center; gap: 8px; }
.inp-inline { border: 1.5px solid transparent; border-radius: 6px; padding: 3px 6px; font-size: 14px; font-weight: 700; color: #1e3a5f; min-width: 0; flex: 1; }
.inp-inline:hover, .inp-inline:focus { border-color: #cbd5e1; outline: none; }
.inp-obs { font-size: 12px; font-weight: 500; color: #64748b; }
.lista-meta { font-size: 11px; color: #94a3b8; padding-left: 6px; }
.badge-st { font-size: 10px; font-weight: 700; border-radius: 999px; padding: 2px 8px; white-space: nowrap; }
.st-on { background: #dcfce7; color: #15803d; }
.st-off { background: #f1f5f9; color: #94a3b8; }
.add-row { display: flex; gap: 8px; align-items: center; margin-bottom: 6px; }
.tbl { width: 100%; border-collapse: collapse; font-size: 13px; }
.tbl th { background: #f8fafc; color: #475569; font-weight: 700; font-size: 11px; text-transform: uppercase; padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: left; }
.tbl td { padding: 6px 8px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.row-warn td { background: #fffbeb; }
.row-off { opacity: .55; }
.it-name { font-weight: 600; color: #1e3a5f; }
.it-warn { font-size: 11px; color: #b45309; }
.inp-price { width: 120px; text-align: right; border: 1.5px solid #cbd5e1; border-radius: 6px; padding: 4px 8px; font-size: 13px; }
.text-right { text-align: right; }
.text-center { text-align: center; }
.text-muted { color: #94a3b8; }
.btn-x-sm { background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 14px; }
.btn-x-sm:hover { color: #e11d48; }
.only-mobile { display: none; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 1050; padding: 16px; }
.modal-box { background: #fff; border-radius: 16px; width: 100%; max-width: 480px; max-height: 90vh; display: flex; flex-direction: column; overflow: hidden; }
.mh { display: flex; justify-content: space-between; align-items: center; padding: 14px 18px; background: linear-gradient(90deg,#1e3a5f,#1d4ed8); color: #fff; font-weight: 700; font-size: 14px; }
.btn-x { background: none; border: none; color: #fff; cursor: pointer; font-size: 16px; }
.mb { padding: 16px 18px; display: flex; flex-direction: column; gap: 6px; overflow-y: auto; }
.mf { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 18px; border-top: 1px solid #f1f5f9; }
.lbl { font-size: 12px; font-weight: 700; color: #475569; margin-top: 4px; }
.inp { border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 8px 10px; font-size: 14px; }
.opt { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #334155; cursor: pointer; }
.opt.disabled { opacity: .5; cursor: not-allowed; }
.prod-list { display: flex; flex-direction: column; gap: 4px; max-height: 50vh; overflow-y: auto; margin-top: 6px; }
.prod-row { display: flex; align-items: center; gap: 8px; border: 1.5px solid #e2e8f0; background: #fff; border-radius: 8px; padding: 8px 10px; cursor: pointer; text-align: left; }
.prod-row:hover { border-color: #1d4ed8; }
.prod-name { flex: 1; font-weight: 600; font-size: 13px; color: #1e3a5f; }
.prod-row i { color: #1d4ed8; }

@media (max-width: 1024px) {
  .lp-grid { grid-template-columns: 260px 1fr; }
}
@media (max-width: 768px) {
  .lp-grid { grid-template-columns: 1fr; }
  .lp-hide-mobile { display: none; }
  .only-mobile { display: inline-flex; }
  .lp-clientes { max-height: none; }
  .modal-overlay { padding: 0; align-items: flex-end; }
  .modal-box { border-radius: 16px 16px 0 0; max-height: 92vh; }
}
@media (max-width: 576px) {
  .hide-sm { display: none; }
  .inp-price { width: 96px; }
  .lista-top { flex-direction: column; }
  .add-row { flex-direction: column; align-items: stretch; }
  .det-hdr { flex-wrap: wrap; }
}
.cli-general { border-color: #c7d2fe; background: #eef2ff; margin-bottom: 6px; }
.cli-general.active { border-color: #4338ca; }
.lista-general-name { font-weight: 800; color: #3730a3; font-size: 15px; }
.row-var td:first-child { padding-left: 22px; }
.row-var .it-name { font-weight: 500; }
.chip-def { font-size: 10px; font-weight: 700; color: #15803d; background: #dcfce7; border-radius: 10px; padding: 1px 6px; margin-left: 4px; }
</style>
