<template>
  <div class="lp-view">
    <div class="lp-header">
      <div>
        <h5 class="lp-title">{{ moduleName || 'Listas de Precios' }}</h5>
        <p class="lp-sub">La <b>Lista Default</b> (Consumidor Final) es el precio de los platos y se cobra a todo cliente sin lista propia. Cada cliente tiene máximo una lista activa.</p>
      </div>
      <button class="btn-primary-sm" @click="abrirNueva"><i class="bi bi-plus-lg"></i> Nueva lista</button>
    </div>

    <div class="lp-grid">
      <!-- ══ Encabezados ══ -->
      <section class="lp-panel lp-listas" :class="{ 'lp-hide-mobile': lista }">
        <div class="lp-tabs">
          <button :class="['lp-tab', { active: estado === 'activas' }]" @click="estado = 'activas'; cargarListas()">Activas</button>
          <button :class="['lp-tab', { active: estado === 'todas' }]" @click="estado = 'todas'; cargarListas()">Todas (histórico)</button>
        </div>
        <div class="lp-search">
          <i class="bi bi-search"></i>
          <input v-model="qListas" @input="debListas" placeholder="Buscar por lista o cliente..." maxlength="60" />
        </div>
        <div v-if="loadingListas" class="lp-empty"><span class="spinner-border spinner-border-sm"></span></div>
        <div v-else-if="!listas.length" class="lp-empty">Sin listas</div>
        <button v-for="l in listas" :key="l.id_lista"
                :class="['ls-row', { active: lista?.id_lista === l.id_lista, 'ls-def': l.predeterminada, off: !l.activa }]"
                @click="seleccionar(l.id_lista)">
          <div class="ls-main">
            <span class="ls-name">{{ l.nombre }}</span>
            <span class="ls-cli"><i class="bi bi-person"></i> {{ l.cliente || `Cliente ${l.id_cliente}` }}</span>
            <span class="ls-meta">No. {{ l.id_lista }} · {{ l.fecha }} · {{ l.productos }} prod.</span>
          </div>
          <div class="ls-badges">
            <span v-if="l.predeterminada" class="bdg bdg-def">Predeterminada</span>
            <span :class="['bdg', l.activa ? 'bdg-on' : 'bdg-off']">{{ l.activa ? 'Activa' : 'Histórico' }}</span>
          </div>
        </button>
      </section>

      <!-- ══ Lista seleccionada ══ -->
      <section class="lp-panel lp-detalle" :class="{ 'lp-hide-mobile': !lista }">
        <div v-if="!lista" class="lp-empty lp-empty--big">
          <i class="bi bi-currency-dollar"></i>
          <p>Seleccione una lista para ver y editar sus precios.</p>
        </div>
        <template v-else>
          <div class="det-top">
            <button class="btn-back only-mobile" @click="salirLista"><i class="bi bi-arrow-left"></i></button>
            <div class="det-grid">
              <div class="det-f"><span class="det-l">Id lista</span><b>{{ lista.id_lista }}</b></div>
              <div class="det-f"><span class="det-l">Fecha</span><b>{{ lista.fecha }}</b></div>
              <div class="det-f det-f--wide"><span class="det-l">Cliente</span><b>{{ lista.cliente || `Cliente ${lista.id_cliente}` }} <small>(Id {{ lista.id_cliente }})</small></b></div>
              <div class="det-f det-f--wide">
                <span class="det-l">Nombre</span>
                <input v-model="lista.nombre" class="inp-inline" maxlength="100" @change="guardarCabecera" />
              </div>
              <div class="det-f det-f--wide">
                <span class="det-l">Observación</span>
                <input v-model="lista.observacion" class="inp-inline" maxlength="255" placeholder="—" @change="guardarCabecera" />
              </div>
              <div class="det-f">
                <span class="det-l">Estado</span>
                <span>
                  <span v-if="lista.predeterminada" class="bdg bdg-def">Predeterminada</span>
                  <span :class="['bdg', lista.activa ? 'bdg-on' : 'bdg-off']">{{ lista.activa ? 'Activa' : 'Histórico' }}</span>
                </span>
              </div>
            </div>
          </div>

          <div class="det-actions">
            <div class="lp-search lp-search--sm">
              <i class="bi bi-search"></i>
              <input v-model="qItems" placeholder="Filtrar productos..." maxlength="60" />
            </div>
            <button v-if="!lista.activa && lista.predeterminada" class="btn-soft-ok" @click="activar"><i class="bi bi-check-circle"></i> Activar como Default</button>
            <button v-else-if="!lista.predeterminada" class="btn-soft-danger" @click="desactivar"><i class="bi bi-slash-circle"></i> Anular</button>
            <button class="btn-soft" @click="imprimir"><i class="bi bi-printer"></i> Imprimir</button>
            <button v-if="!(lista.predeterminada && lista.activa)" class="btn-soft-danger" @click="eliminar"><i class="bi bi-trash"></i> Eliminar lista</button>
            <button class="btn-primary-sm" :disabled="!cambios || guardando" @click="guardarPrecios">
              <span v-if="guardando" class="spinner-border spinner-border-sm"></span>
              <i v-else class="bi bi-floppy"></i> Guardar cambios<span v-if="cambios"> ({{ cambios }})</span>
            </button>
          </div>
          <div v-if="lista.predeterminada && lista.activa" class="info-line">
            <i class="bi bi-info-circle"></i> Es la lista Default activa: al guardar, el precio de cada plato y variante queda igual al de la lista.
          </div>
          <div v-else-if="lista.predeterminada" class="info-line">
            <i class="bi bi-clock-history"></i> Lista Default del histórico. Al activarla, sus precios pasan a los platos.
          </div>
          <div v-else-if="!lista.activa" class="info-line">
            <i class="bi bi-slash-circle"></i> Lista anulada (histórico). No se puede reactivar: para este cliente cree una lista nueva.
          </div>
          <div v-if="bajoMinimo" class="warn-line"><i class="bi bi-exclamation-triangle"></i> {{ bajoMinimo }} producto(s) por debajo del precio mínimo.</div>

          <div v-if="loadingLista" class="lp-empty"><span class="spinner-border spinner-border-sm"></span></div>
          <div v-else class="acc-wrap">
            <div v-if="!grupos.length" class="lp-empty">Sin productos</div>
            <div v-for="g in grupos" :key="g.nombre" :class="['acc-item', { open: estaAbierta(g.nombre) }]">
              <button class="acc-hdr" @click="toggleCat(g.nombre)" :aria-expanded="estaAbierta(g.nombre)">
                <i class="bi bi-chevron-right acc-chev"></i>
                <span class="acc-name">{{ g.nombre }}</span>
                <span v-if="g.cambios" class="acc-dirty">{{ g.cambios }} sin guardar</span>
                <span class="acc-count">{{ g.items.length }}</span>
              </button>
              <table v-if="estaAbierta(g.nombre)" class="tbl">
                <tbody>
                  <tr v-for="it in g.items" :key="`${it.id_producto}-${it.id_presentacion}`"
                      :class="{ 'row-warn': it.bajo_minimo, 'row-var': it.id_presentacion > 0, 'row-dirty': esCambio(it) }">
                    <td>
                      <div class="it-name">
                        <i v-if="it.id_presentacion > 0" class="bi bi-arrow-return-right text-muted me-1"></i>{{ it.name }}
                        <span v-if="it.var_default" class="chip-def">Por defecto</span>
                      </div>
                      <div v-if="it.bajo_minimo" class="it-warn">Mínimo {{ fmt(it.precio_minimo) }}</div>
                    </td>
                    <td class="text-right td-price">
                      <CurrencyInput v-model="it.precio" class="inp-price" @update:model-value="marcar(it)" />
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </template>
      </section>
    </div>

    <!-- Nueva lista -->
    <div v-if="nueva.show" class="modal-overlay" @click.self="nueva.show = false">
      <div class="modal-box">
        <div class="mh"><span>Nueva lista de precios</span><button class="btn-x" @click="nueva.show = false"><i class="bi bi-x-lg"></i></button></div>
        <div class="mb">
          <label class="lbl">Cliente *</label>
          <button class="inp inp-btn" @click="nueva.selCliente = true">
            <i class="bi bi-person-badge"></i> {{ nueva.cliente.nombre }} <small>(Id {{ nueva.cliente.id_cliente }})</small>
          </button>
          <p v-if="nueva.cliente.id_cliente === 1" class="info-line">
            <i class="bi bi-info-circle"></i> Consumidor Final = nueva <b>Lista Default</b>. La Default actual queda en el histórico y los precios de esta lista pasan a los platos.
          </p>
          <label class="lbl">Nombre *</label>
          <input v-model="nueva.nombre" class="inp" maxlength="100" placeholder="Ej: Precios octubre" />
          <label class="lbl">Observación</label>
          <input v-model="nueva.observacion" class="inp" maxlength="255" />
          <label class="lbl">Cargar precios desde</label>
          <label class="opt"><input type="radio" value="default" v-model="nueva.origen" /> Precios actuales (Lista Default) de todos los productos activos</label>
          <label class="opt"><input type="radio" value="anterior" v-model="nueva.origen" /> Precios de la lista anterior del cliente + los productos nuevos con el precio actual</label>
          <p class="info-line"><i class="bi bi-info-circle"></i> Toda lista incluye siempre todos los productos activos: los platos que se creen después se agregan solos con el precio actual.</p>
          <p class="warn-line"><i class="bi bi-info-circle"></i> Si el cliente tiene una lista activa, quedará anulada (solo una activa por cliente).</p>
        </div>
        <div class="mf">
          <button class="btn-cancel" @click="nueva.show = false">Cancelar</button>
          <button class="btn-primary-sm" :disabled="nueva.saving || !nueva.nombre.trim()" @click="crear">
            {{ nueva.saving ? 'Creando…' : 'Crear lista' }}
          </button>
        </div>
      </div>
    </div>
    <ComandaClienteModal v-if="nueva.selCliente" panel title="Cliente de la lista" :current-id="nueva.cliente.id_cliente"
                         @close="nueva.selCliente = false" @select="elegirCliente" />

    <!-- Impresión (componente propio) -->
    <ImprimirRecibo v-if="impresion" :receiptData="impresion" :companyId="companyId"
                    printersPath="/api/pos/recibo-impresion/impresoras"
                    :printPath="`${BASE}/lista/${lista?.id_lista}/imprimir`"
                    @close="impresion = null" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import Swal from 'sweetalert2'
import api from '@/services/apis.js'
import { showToast } from '@/utils/toast.js'
import { useModuleName } from '@/composables/useModuleName'
import { useCompanyStore } from '@/stores/companyStore'
import ComandaClienteModal from '@/components/comanda/ComandaClienteModal.vue'
import ImprimirRecibo from '@/components/billing/ImprimirRecibo.vue'

const BASE = '/api/pos-catalogo/listas-cliente'
const { moduleName } = useModuleName()
const companyStore = useCompanyStore()
const companyId = computed(() => companyStore.selectedCompany?.id || 0)
const fmtCOP = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })
const fmt = v => fmtCOP.format(Number(v) || 0)

const estado = ref('activas')
const qListas = ref('')
const listas = ref([])
const loadingListas = ref(false)
const lista = ref(null)
const items = ref([])
const original = ref(new Map())          // precio guardado por ítem, para saber qué cambió
const loadingLista = ref(false)
const guardando = ref(false)
const qItems = ref('')
const impresion = ref(null)
const nueva = reactive({ show: false, selCliente: false, saving: false, nombre: '', observacion: '', origen: 'default',
                         cliente: { id_cliente: 1, nombre: 'Consumidor Final' } })

let tL = null
const debListas = () => { clearTimeout(tL); tL = setTimeout(cargarListas, 250) }
const clave = it => `${it.id_producto}-${it.id_presentacion}`
const esCambio = it => original.value.get(clave(it)) !== Math.round(Number(it.precio) || 0)
const cambios = computed(() => items.value.filter(esCambio).length)
const bajoMinimo = computed(() => items.value.filter(i => i.precio_minimo && Number(i.precio) < i.precio_minimo).length)
const itemsFiltrados = computed(() => {
  const q = qItems.value.trim().toLowerCase()
  return q ? items.value.filter(i => i.name.toLowerCase().includes(q) || (i.categoria || '').toLowerCase().includes(q)) : items.value
})
// Acordeón por categoría: una sola abierta; al filtrar se muestran abiertas las que coinciden
const catAbierta = ref(null)
const grupos = computed(() => {
  const m = new Map()
  for (const it of itemsFiltrados.value) {
    const c = it.categoria || 'SIN CATEGORÍA'
    if (!m.has(c)) m.set(c, { nombre: c, items: [], cambios: 0 })
    const g = m.get(c)
    g.items.push(it)
    if (esCambio(it)) g.cambios++
  }
  return [...m.values()]
})
const estaAbierta = nombre => !!qItems.value.trim() || catAbierta.value === nombre
function toggleCat(nombre) { catAbierta.value = catAbierta.value === nombre ? null : nombre }
function marcar(it) { it.bajo_minimo = !!it.precio_minimo && Number(it.precio) < it.precio_minimo }

async function cargarListas() {
  loadingListas.value = true
  try { listas.value = (await api.get(`${BASE}/listas`, { params: { estado: estado.value, q: qListas.value.trim() || undefined } })).data }
  catch (e) { showToast(e?.response?.data?.detail || 'Error cargando listas', 'error') }
  finally { loadingListas.value = false }
}

async function confirmarDescartar() {
  if (!cambios.value) return true
  const { isConfirmed } = await Swal.fire({
    title: 'Hay cambios sin guardar', text: `${cambios.value} precio(s) modificados se perderán.`,
    icon: 'warning', showCancelButton: true, confirmButtonText: 'Descartar', cancelButtonText: 'Volver',
  })
  return isConfirmed
}

async function seleccionar(id) {
  if (lista.value?.id_lista === id) return
  if (!(await confirmarDescartar())) return
  await cargarLista(id)
}
async function cargarLista(id) {
  loadingLista.value = true
  try {
    const { data } = await api.get(`${BASE}/lista/${id}`)
    if (lista.value?.id_lista !== data.lista.id_lista) catAbierta.value = null
    lista.value = data.lista
    items.value = data.items
    original.value = new Map(data.items.map(i => [clave(i), Math.round(Number(i.precio) || 0)]))
  } catch (e) { showToast(e?.response?.data?.detail || 'Error cargando la lista', 'error') }
  finally { loadingLista.value = false }
}
async function salirLista() { if (await confirmarDescartar()) { lista.value = null; items.value = [] } }

async function guardarCabecera() {
  if (!lista.value.nombre?.trim()) { showToast('El nombre es obligatorio', 'warning'); return }
  try {
    await api.put(`${BASE}/lista/${lista.value.id_lista}`, { nombre: lista.value.nombre.trim(), observacion: lista.value.observacion || null })
    cargarListas()
  } catch (e) { showToast(e?.response?.data?.detail || 'Error', 'error') }
}

async function guardarPrecios() {
  const cambiados = items.value.filter(esCambio)
  if (!cambiados.length) return
  guardando.value = true
  try {
    await api.put(`${BASE}/lista/${lista.value.id_lista}/precios`, {
      items: cambiados.map(i => ({ id_producto: i.id_producto, id_presentacion: i.id_presentacion, precio: Math.round(Number(i.precio) || 0) })),
    })
    showToast(`${cambiados.length} precio(s) guardados`, 'success')
    await cargarLista(lista.value.id_lista)
  } catch (e) {
    const d = e?.response?.data?.detail
    showToast(Array.isArray(d) ? 'Revise los precios' : (d || 'Error al guardar'), 'error')
  }
  guardando.value = false
}

async function activar() {
  if (!(await confirmarDescartar())) return
  try {
    await api.post(`${BASE}/lista/${lista.value.id_lista}/activar`)
    showToast('Lista Default activada: sus precios rigen para los platos', 'success')
    await cargarLista(lista.value.id_lista); cargarListas()
  } catch (e) { showToast(e?.response?.data?.detail || 'Error', 'error') }
}
async function desactivar() {
  const { isConfirmed } = await Swal.fire({
    title: '¿Anular la lista?', text: 'El cliente pasará a pagar con la Lista Default.',
    icon: 'warning', showCancelButton: true, confirmButtonText: 'Sí, anular', cancelButtonText: 'Cancelar', confirmButtonColor: '#e11d48',
  })
  if (!isConfirmed) return
  try {
    await api.post(`${BASE}/lista/${lista.value.id_lista}/desactivar`)
    showToast('Lista anulada', 'success')
    await cargarLista(lista.value.id_lista); cargarListas()
  } catch (e) { showToast(e?.response?.data?.detail || 'Error', 'error') }
}

async function eliminar() {
  const { isConfirmed } = await Swal.fire({
    title: '¿Eliminar la lista?',
    text: `Se eliminará "${lista.value.nombre}" con todos sus precios. Este proceso no se puede deshacer.`,
    icon: 'warning', showCancelButton: true, confirmButtonText: 'Sí, eliminar', cancelButtonText: 'Cancelar',
    confirmButtonColor: '#e11d48',
  })
  if (!isConfirmed) return
  try {
    await api.delete(`${BASE}/lista/${lista.value.id_lista}`)
    showToast('Lista eliminada', 'success')
    lista.value = null; items.value = []; original.value = new Map()
    await cargarListas()
  } catch (e) { showToast(e?.response?.data?.detail || 'Error al eliminar la lista', 'error') }
}

function imprimir() {
  if (cambios.value) { showToast('Guarde los cambios antes de imprimir', 'warning'); return }
  const porCat = new Map()
  for (const it of items.value) {
    const c = it.categoria || 'SIN CATEGORÍA'
    if (!porCat.has(c)) porCat.set(c, [])
    porCat.get(c).push(`${it.id_presentacion ? '   ' : ''}${it.name} — ${fmt(it.precio)}`)
  }
  impresion.value = {
    titulo: 'LISTA DE PRECIOS', receipt_number: '',
    ordenNumero: `${lista.value.nombre} · No. ${lista.value.id_lista}`,
    cliente: { nombre: lista.value.cliente || `Cliente ${lista.value.id_cliente}` },
    fecha: lista.value.fecha,
    secciones: [...porCat].map(([titulo, its]) => ({ titulo, items: its })),
    items: [], pagos: [],
  }
}

function abrirNueva() {
  Object.assign(nueva, { show: true, selCliente: false, saving: false, nombre: '', observacion: '', origen: 'default',
                         cliente: { id_cliente: 1, nombre: 'Consumidor Final' } })
}
function elegirCliente(c) {
  nueva.cliente = { id_cliente: c.id_cliente, nombre: c.nombre }
  nueva.selCliente = false
}
async function crear() {
  nueva.saving = true
  try {
    const { data } = await api.post(`${BASE}/lista`, {
      id_cliente: nueva.cliente.id_cliente, nombre: nueva.nombre.trim(),
      observacion: nueva.observacion.trim() || null, origen: nueva.origen,
    })
    nueva.show = false
    showToast('Lista creada', 'success')
    estado.value = 'activas'
    await cargarListas()
    await cargarLista(data.id_lista)
  } catch (e) { showToast(e?.response?.data?.detail || 'Error creando la lista', 'error') }
  finally { nueva.saving = false }
}

onMounted(async () => {
  await cargarListas()
  const def = listas.value.find(l => l.predeterminada && l.activa)
  if (def) await cargarLista(def.id_lista)
})
</script>

<style scoped>
.lp-view { padding: 16px 20px 28px; }
.lp-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 12px; }
.lp-title { font-weight: 800; color: #1e3a5f; margin: 0; font-size: 18px; }
.lp-sub { font-size: 13px; color: #64748b; margin: 2px 0 0; max-width: 680px; }
.lp-grid { display: grid; grid-template-columns: 330px 1fr; gap: 12px; align-items: start; }
.lp-panel { background: #fff; border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,.07); padding: 12px; display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.lp-listas { max-height: calc(100dvh - 190px); overflow-y: auto; }
.lp-tabs { display: flex; background: #f1f5f9; border-radius: 10px; padding: 3px; }
.lp-tab { flex: 1; border: none; background: none; padding: 7px 8px; border-radius: 8px; font-size: 13px; font-weight: 700; color: #64748b; cursor: pointer; }
.lp-tab.active { background: #fff; color: #1d4ed8; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.lp-search { display: flex; align-items: center; gap: 6px; border: 1.5px solid #cbd5e1; border-radius: 10px; padding: 7px 10px; background: #fff; }
.lp-search input { border: none; outline: none; flex: 1; min-width: 0; font-size: 14px; }
.lp-search--sm { flex: 1; min-width: 180px; }
.lp-empty { text-align: center; color: #94a3b8; padding: 16px; font-size: 13px; }
.lp-empty--big { padding: 50px 16px; }
.lp-empty--big i { font-size: 34px; display: block; margin-bottom: 6px; }
.ls-row { display: flex; align-items: center; gap: 8px; text-align: left; border: 1.5px solid #e2e8f0; background: #fff; border-radius: 10px; padding: 9px 11px; cursor: pointer; }
.ls-row.active { border-color: #1d4ed8; background: #eff6ff; }
.ls-row.ls-def { border-color: #c7d2fe; background: #f5f7ff; }
.ls-row.ls-def.active { border-color: #4338ca; }
.ls-row.off { opacity: .7; }
.ls-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px; }
.ls-name { font-weight: 800; color: #1e3a5f; font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ls-cli, .ls-meta { font-size: 12px; color: #64748b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ls-meta { color: #94a3b8; }
.ls-badges { display: flex; flex-direction: column; align-items: flex-end; gap: 3px; }
.bdg { font-size: 10px; font-weight: 700; border-radius: 10px; padding: 2px 8px; white-space: nowrap; display: inline-block; }
.bdg-def { background: #e0e7ff; color: #4338ca; margin-right: 4px; }
.bdg-on { background: #dcfce7; color: #15803d; }
.bdg-off { background: #f1f5f9; color: #64748b; }
.det-top { display: flex; gap: 8px; align-items: flex-start; }
.det-grid { flex: 1; display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 8px; }
.det-f { display: flex; flex-direction: column; gap: 2px; grid-column: span 1; min-width: 0; }
.det-f--wide { grid-column: span 2; }
.det-l { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; }
.det-f b { color: #1e293b; font-size: 14px; overflow: hidden; text-overflow: ellipsis; }
.det-f small { color: #94a3b8; font-weight: 600; }
.inp-inline { border: 1.5px solid #e2e8f0; border-radius: 8px; padding: 6px 9px; font-size: 14px; font-weight: 600; color: #1e3a5f; width: 100%; }
.inp-inline:focus { outline: none; border-color: #1d4ed8; }
.det-actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.btn-primary-sm { display: inline-flex; align-items: center; gap: 6px; background: linear-gradient(90deg,#1e3a5f,#1d4ed8); color: #fff; border: none; border-radius: 9px; padding: 8px 14px; font-weight: 700; font-size: 13px; cursor: pointer; white-space: nowrap; }
.btn-primary-sm:disabled { opacity: .5; cursor: not-allowed; }
.btn-soft, .btn-soft-ok, .btn-soft-danger { display: inline-flex; align-items: center; gap: 6px; border-radius: 9px; padding: 8px 12px; font-weight: 700; font-size: 13px; cursor: pointer; white-space: nowrap; }
.btn-soft { background: #fff; border: 1.5px solid #cbd5e1; color: #334155; }
.btn-soft-ok { background: #f0fdf4; border: 1.5px solid #bbf7d0; color: #15803d; }
.btn-soft-danger { background: #fff1f2; border: 1.5px solid #fecdd3; color: #be123c; }
.btn-back { width: 34px; height: 34px; border-radius: 50%; border: 1px solid #e2e8f0; background: #fff; cursor: pointer; flex-shrink: 0; }
.info-line { font-size: 12px; color: #3730a3; background: #eef2ff; border-radius: 8px; padding: 7px 10px; margin: 0; }
.warn-line { font-size: 12px; color: #92400e; background: #fffbeb; border-radius: 8px; padding: 7px 10px; margin: 0; }
.tbl-wrap { max-height: calc(100dvh - 380px); min-height: 220px; overflow-y: auto; border: 1px solid #f1f5f9; border-radius: 10px; }
.tbl { width: 100%; border-collapse: collapse; font-size: 13px; }
.tbl th { position: sticky; top: 0; background: #f8fafc; z-index: 1; text-align: left; font-size: 11px; text-transform: uppercase; color: #64748b; padding: 8px 10px; border-bottom: 1px solid #e2e8f0; }
.tbl td { padding: 6px 10px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.text-right { text-align: right; } .text-center { text-align: center; } .text-muted { color: #94a3b8; }
.it-name { font-weight: 600; color: #1e293b; }
.it-warn { font-size: 11px; color: #b45309; }
.row-var td:first-child { padding-left: 24px; }
.row-var .it-name { font-weight: 500; }
.row-warn { background: #fffbeb; }
.row-dirty { background: #eff6ff; }
.chip-def { font-size: 10px; font-weight: 700; color: #15803d; background: #dcfce7; border-radius: 10px; padding: 1px 6px; margin-left: 4px; }
.inp-price { width: 120px; text-align: right; border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 5px 8px; font-weight: 700; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 1050; padding: 16px; }
.modal-box { background: #fff; border-radius: 16px; width: 100%; max-width: 460px; max-height: 90vh; display: flex; flex-direction: column; overflow: hidden; }
.mh { display: flex; justify-content: space-between; align-items: center; padding: 14px 18px; background: linear-gradient(90deg,#1e3a5f,#1d4ed8); color: #fff; font-weight: 700; }
.btn-x { background: none; border: none; color: #fff; font-size: 16px; cursor: pointer; }
.mb { padding: 14px 18px; display: flex; flex-direction: column; gap: 8px; overflow-y: auto; }
.mf { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 18px; border-top: 1px solid #f1f5f9; }
.lbl { font-size: 12px; font-weight: 700; color: #475569; }
.inp { border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 8px 10px; font-size: 14px; }
.inp-btn { text-align: left; background: #eff6ff; color: #1d4ed8; font-weight: 700; cursor: pointer; }
.inp-btn small { color: #64748b; font-weight: 600; }
.opt { display: flex; align-items: center; gap: 8px; font-size: 14px; color: #334155; }
.btn-cancel { background: #f1f5f9; border: none; border-radius: 9px; padding: 8px 16px; font-weight: 600; color: #475569; cursor: pointer; }
.only-mobile { display: none; }

@media (max-width: 1024px) {
  .lp-grid { grid-template-columns: 280px 1fr; }
  .det-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
}
@media (max-width: 768px) {
  .lp-view { padding: 12px 10px 20px; }
  .lp-header { flex-direction: column; }
  .lp-header .btn-primary-sm { width: 100%; justify-content: center; }
  .lp-grid { grid-template-columns: 1fr; }
  .lp-hide-mobile { display: none; }
  .only-mobile { display: inline-block; }
  .lp-listas { max-height: none; }
  .det-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .tbl-wrap { max-height: 60dvh; }
  .modal-overlay { padding: 0; align-items: flex-end; }
  .modal-box { border-radius: 16px 16px 0 0; max-width: 100%; }
}
@media (max-width: 576px) {
  .det-f--wide { grid-column: span 2; }
  .det-actions > * { flex: 1 1 auto; justify-content: center; }
  .lp-search--sm { flex: 1 1 100%; }
  .hide-sm { display: none; }
  .inp-price { width: 100px; }
}
.acc-wrap { display: flex; flex-direction: column; gap: 6px; max-height: calc(100dvh - 380px); min-height: 220px; overflow-y: auto; }
.acc-item { border: 1.5px solid #e2e8f0; border-radius: 10px; overflow: hidden; flex-shrink: 0; }
.acc-item.open { border-color: #bfdbfe; }
.acc-hdr { width: 100%; display: flex; align-items: center; gap: 8px; padding: 10px 12px; background: #f8fafc; border: none; cursor: pointer; text-align: left; }
.acc-item.open .acc-hdr { background: #eff6ff; }
.acc-chev { color: #64748b; transition: transform .15s; }
.acc-item.open .acc-chev { transform: rotate(90deg); }
.acc-name { flex: 1; min-width: 0; font-weight: 800; color: #1e3a5f; font-size: 13px; }
.acc-count { font-size: 11px; font-weight: 700; color: #64748b; background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1px 8px; }
.acc-dirty { font-size: 10px; font-weight: 700; color: #1d4ed8; background: #dbeafe; border-radius: 10px; padding: 1px 7px; }
.td-price { width: 140px; }
@media (max-width: 768px) { .acc-wrap { max-height: 60dvh; } }
@media (max-width: 576px) { .td-price { width: 110px; } }
</style>
