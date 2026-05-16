<template>
  <div class="crud-view">
    <!-- HEADER -->
    <div class="crud-header">
      <div>
        <h5 class="crud-titulo">Artículos de Venta</h5>
        <p class="crud-sub">Catálogo de artículos (hamburguesas, servicios, bebidas…). Al crear uno se agrega automáticamente a la lista de precios.</p>
      </div>
      <div class="header-tools">
        <input v-model="busqueda" class="inp-buscar" placeholder="Buscar…" />
        <button class="btn-nuevo" @click="abrirModalItem()">
          <i class="bi bi-plus-lg me-1"></i>Nuevo Artículo
        </button>
      </div>
    </div>

    <!-- LISTA -->
    <div v-if="loading" class="estado-carga"><div class="spinner-border spinner-border-sm text-primary"></div></div>
    <div v-else-if="!filtrados.length" class="estado-vacio">
      <i class="bi bi-box-seam"></i>
      <p>No hay artículos. Crea el primero para comenzar.</p>
    </div>
    <div v-else class="items-grid">
      <div v-for="item in filtrados" :key="item.id" class="item-card" :class="{ 'item-card--inactivo': !item.active }">
        <div class="item-top">
          <span class="item-cat" :style="{ background: (item.category_color||'#1d4ed8')+'22', color: item.category_color||'#1d4ed8' }">
            {{ item.category_name || 'Sin categoría' }}
          </span>
          <span :class="item.active ? 'badge-activo' : 'badge-inactivo'">{{ item.active ? 'Activo' : 'Inactivo' }}</span>
        </div>
        <div class="item-nombre">{{ item.name }}</div>
        <div class="item-precio">{{ fmt(item.price) }}</div>
        <div class="item-meta">
          <span title="Ingredientes en receta"><i class="bi bi-list-ul"></i> {{ item.ingredient_count }}</span>
          <span title="Impresoras asignadas"><i class="bi bi-printer"></i> {{ item.printer_count }}</span>
          <span v-if="item.tax" title="IVA"><i class="bi bi-percent"></i> {{ item.tax }}%</span>
        </div>
        <div class="item-acciones">
          <button class="btn-accion" @click="abrirModalItem(item)"><i class="bi bi-pencil"></i></button>
          <button class="btn-accion" title="Ingredientes/Receta" @click="abrirPanel(item, 'ingredientes')"><i class="bi bi-list-ul"></i></button>
          <button class="btn-accion" title="Impresoras" @click="abrirPanel(item, 'impresoras')"><i class="bi bi-printer"></i></button>
          <button class="btn-accion" title="Opciones de Armado" @click="abrirPanel(item, 'modificadores')"><i class="bi bi-sliders"></i></button>
          <button class="btn-accion btn-accion--danger" @click="eliminar(item.id)"><i class="bi bi-trash"></i></button>
        </div>
      </div>
    </div>

    <!-- MODAL CREAR/EDITAR ARTÍCULO -->
    <div v-if="modalItem.visible" class="modal-overlay" @click.self="cerrarModalItem">
      <div class="modal-card">
        <div class="modal-hdr">
          <span><i class="bi bi-box-seam me-2"></i>{{ modalItem.id ? 'Editar' : 'Nuevo' }} Artículo</span>
          <button class="btn-x" @click="cerrarModalItem"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-body">
          <div class="campo"><label>Nombre *</label>
            <input v-model="modalItem.name" class="inp" placeholder="Nombre del artículo" />
          </div>
          <div class="campo-row">
            <div class="campo"><label>Precio (COP)</label>
              <input type="number" v-model.number="modalItem.price" class="inp" placeholder="0" min="0" />
            </div>
            <div class="campo"><label>IVA %</label>
              <input type="number" v-model.number="modalItem.tax" class="inp" placeholder="0" min="0" max="100" />
            </div>
          </div>
          <div class="campo"><label>Categoría</label>
            <select v-model="modalItem.category_id" class="inp">
              <option :value="null">— Sin categoría —</option>
              <option v-for="c in categorias" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          <div class="campo"><label>Descripción</label>
            <textarea v-model="modalItem.description" class="inp" rows="2" placeholder="Descripción opcional"></textarea>
          </div>
          <div class="campo-check">
            <input type="checkbox" v-model="modalItem.active" :true-value="1" :false-value="0" id="chkA" />
            <label for="chkA">Activo en catálogo</label>
          </div>
        </div>
        <div class="modal-ftr">
          <button class="btn-cancel" @click="cerrarModalItem">Cancelar</button>
          <button class="btn-save" :disabled="guardando || !modalItem.name" @click="guardarItem">
            <span v-if="guardando"><span class="spinner-border spinner-border-sm me-1"></span></span>
            <i v-else class="bi bi-check-lg me-1"></i>Guardar
          </button>
        </div>
      </div>
    </div>

    <!-- PANEL LATERAL -->
    <div v-if="panel.visible" class="panel-overlay" @click.self="cerrarPanel">
      <div class="panel-lateral">
        <div class="panel-hdr">
          <div>
            <div class="panel-titulo">{{ panel.item?.name }}</div>
            <div class="panel-sub">{{ fmt(panel.item?.price) }}</div>
          </div>
          <button class="btn-x" @click="cerrarPanel"><i class="bi bi-x-lg"></i></button>
        </div>

        <div class="panel-tabs">
          <button :class="['ptab', { active: panel.tab==='ingredientes' }]" @click="panel.tab='ingredientes'; cargarIngredientes()">
            <i class="bi bi-list-ul me-1"></i>Receta
          </button>
          <button :class="['ptab', { active: panel.tab==='impresoras' }]" @click="panel.tab='impresoras'; cargarImpresoras()">
            <i class="bi bi-printer me-1"></i>Impresoras
          </button>
          <button :class="['ptab', { active: panel.tab==='modificadores' }]" @click="panel.tab='modificadores'; cargarModificadores()">
            <i class="bi bi-sliders me-1"></i>Armado
          </button>
        </div>

        <div class="panel-body">

          <!-- TAB: INGREDIENTES (Receta) -->
          <div v-if="panel.tab==='ingredientes'">
            <div class="sub-header">
              <span>Insumos que descuenta del inventario</span>
              <button class="btn-mini" @click="formIngrediente.visible=true"><i class="bi bi-plus"></i> Agregar</button>
            </div>
            <div v-if="panel.loadingIngredientes" class="mini-carga"><div class="spinner-border spinner-border-sm"></div></div>
            <div v-else-if="!ingredientes.length" class="mini-vacio"><i class="bi bi-list-ul"></i> Sin ingredientes</div>
            <div v-else class="receta-lista">
              <div v-for="ing in ingredientes" :key="ing.insumo_id" class="receta-item">
                <div class="receta-info">
                  <span class="receta-nombre">{{ ing.insumo_nombre }}</span>
                  <span class="receta-qty">{{ ing.cantidad }} {{ ing.unit_abrev || ing.unit_nombre || '' }}</span>
                </div>
                <button class="btn-x-sm" @click="eliminarIngrediente(ing.insumo_id)"><i class="bi bi-x"></i></button>
              </div>
            </div>
            <div v-if="formIngrediente.visible" class="mini-modal">
              <select v-model="formIngrediente.supply_item_id" class="inp-sm">
                <option :value="null">— Insumo —</option>
                <option v-for="s in insumos" :key="s.id" :value="s.id">{{ s.name }}</option>
              </select>
              <div class="mini-row">
                <input type="number" v-model.number="formIngrediente.quantity" class="inp-sm" placeholder="Cantidad" min="0.001" step="0.001" />
                <select v-model="formIngrediente.unit_id" class="inp-sm">
                  <option :value="null">— Unidad —</option>
                  <option v-for="u in unidades" :key="u.id" :value="u.id">{{ u.abreviatura || u.name }}</option>
                </select>
              </div>
              <div class="mini-modal-btns">
                <button class="btn-mini btn-mini--cancel" @click="formIngrediente.visible=false">Cancelar</button>
                <button class="btn-mini" @click="agregarIngrediente">Agregar</button>
              </div>
            </div>
          </div>

          <!-- TAB: IMPRESORAS -->
          <div v-if="panel.tab==='impresoras'">
            <div class="sub-header"><span>Destinos de impresión al comandar</span></div>
            <div v-if="panel.loadingImpresoras" class="mini-carga"><div class="spinner-border spinner-border-sm"></div></div>
            <div v-else-if="!impresoras.length" class="mini-vacio"><i class="bi bi-printer"></i> Sin impresoras configuradas</div>
            <div v-else class="imp-lista">
              <label v-for="imp in impresoras" :key="imp.id" class="imp-item" :class="{ 'imp-item--sel': imp.assigned }">
                <input type="checkbox" v-model="imp.assigned" :true-value="1" :false-value="0" @change="guardarImpresoras" />
                <i class="bi bi-printer"></i>
                <div>
                  <div class="imp-nombre">{{ imp.name }}</div>
                  <div class="imp-tipo">{{ imp.connection_type || '—' }} · {{ imp.ip || 'Sin IP' }}</div>
                </div>
              </label>
            </div>
          </div>

          <!-- TAB: MODIFICADORES (Armado) -->
          <div v-if="panel.tab==='modificadores'">
            <div class="sub-header">
              <span>Grupos de opciones al comandar</span>
              <button class="btn-mini" @click="formModificador.visible=true"><i class="bi bi-plus"></i> Grupo</button>
            </div>
            <div v-if="panel.loadingModificadores" class="mini-carga"><div class="spinner-border spinner-border-sm"></div></div>
            <div v-else-if="!modificadores.length" class="mini-vacio"><i class="bi bi-sliders"></i> Sin opciones de armado</div>
            <div v-else class="grupos-lista">
              <div v-for="g in modificadores" :key="g.id" class="grupo-card">
                <div class="grupo-hdr">
                  <span class="grupo-nombre">{{ g.name }}</span>
                  <div class="grupo-badges">
                    <span v-if="g.is_required" class="badge-req">Requerido</span>
                    <span v-if="g.is_multiple" class="badge-mul">Múltiple</span>
                  </div>
                  <div class="grupo-acc">
                    <button class="btn-mini btn-mini--sm" @click="abrirFormOpcion(g)"><i class="bi bi-plus"></i></button>
                    <button class="btn-x-sm" @click="eliminarModificador(g.id)"><i class="bi bi-trash"></i></button>
                  </div>
                </div>
                <div class="detalles-lista">
                  <div v-for="o in g.options" :key="o.id" class="detalle-item">
                    <span class="det-nombre">{{ o.name }}</span>
                    <span class="det-precio" :class="o.extra_price > 0 ? 'precio-pos' : o.extra_price < 0 ? 'precio-neg' : ''">
                      {{ o.extra_price !== 0 ? (o.extra_price > 0 ? '+' : '') + fmt(o.extra_price) : 'Incluido' }}
                    </span>
                    <button class="btn-x-sm" @click="eliminarOpcion(g.id, o.id)"><i class="bi bi-x"></i></button>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="formModificador.visible" class="mini-modal">
              <input v-model="formModificador.name" class="inp-sm" placeholder="Nombre del grupo (Tamaño, Adiciones…)" />
              <div class="mini-checks">
                <label><input type="checkbox" v-model="formModificador.is_required" :true-value="1" :false-value="0" /> Requerido</label>
                <label><input type="checkbox" v-model="formModificador.is_multiple" :true-value="1" :false-value="0" /> Múltiple</label>
              </div>
              <div class="mini-modal-btns">
                <button class="btn-mini btn-mini--cancel" @click="formModificador.visible=false">Cancelar</button>
                <button class="btn-mini" @click="crearModificador">Crear</button>
              </div>
            </div>

            <div v-if="formOpcion.visible" class="mini-modal">
              <p class="mini-label">Opción para: <b>{{ formOpcion.groupName }}</b></p>
              <input v-model="formOpcion.name" class="inp-sm" placeholder="Nombre (Pequeña, Extra queso…)" />
              <input type="number" v-model.number="formOpcion.extra_price" class="inp-sm" placeholder="Precio adicional (puede ser negativo)" />
              <div class="mini-modal-btns">
                <button class="btn-mini btn-mini--cancel" @click="formOpcion.visible=false">Cancelar</button>
                <button class="btn-mini" @click="crearOpcion">Agregar</button>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/apis.js'
import { showToast } from '@/utils/toast.js'

const BASE = '/api/pos-catalogo/platos'

const items      = ref([])
const categorias = ref([])
const insumos    = ref([])
const unidades   = ref([])
const loading    = ref(true)
const guardando  = ref(false)
const busqueda   = ref('')

const filtrados = computed(() => {
  if (!busqueda.value) return items.value
  const q = busqueda.value.toLowerCase()
  return items.value.filter(i => i.name.toLowerCase().includes(q) || (i.category_name||'').toLowerCase().includes(q))
})

const fmtCOP = new Intl.NumberFormat('es-CO', { style:'currency', currency:'COP', minimumFractionDigits:0, maximumFractionDigits:0 })
const fmt = v => fmtCOP.format(v || 0)

// ── Modales y panel ───────────────────────────────────────────────────────────
const modalItem = ref({ visible:false, id:null, name:'', price:0, category_id:null, description:'', tax:0, active:1 })
const panel = ref({ visible:false, item:null, tab:'ingredientes', loadingIngredientes:false, loadingImpresoras:false, loadingModificadores:false })

const ingredientes  = ref([])
const impresoras    = ref([])
const modificadores = ref([])

const formIngrediente = ref({ visible:false, supply_item_id:null, quantity:1, unit_id:null })
const formModificador = ref({ visible:false, name:'', is_required:0, is_multiple:0 })
const formOpcion      = ref({ visible:false, groupId:null, groupName:'', name:'', extra_price:0 })

// ── Carga inicial ─────────────────────────────────────────────────────────────
onMounted(() => Promise.all([cargarItems(), cargarCategorias(), cargarInsumos(), cargarUnidades()]))

async function cargarItems() {
  loading.value = true
  try { const{data}=await api.get(BASE); items.value=data } catch { items.value=[] }
  finally { loading.value=false }
}
async function cargarCategorias() {
  try { const{data}=await api.get('/api/pos-catalogo/categorias'); categorias.value=data.filter(c=>c.is_active) } catch { categorias.value=[] }
}
async function cargarInsumos() {
  try {
    const{data}=await api.get('/supply-items/')
    insumos.value = Array.isArray(data) ? data : (data?.items || [])
  } catch { insumos.value=[] }
}
async function cargarUnidades() {
  try { const{data}=await api.get('/unidades-medida/'); unidades.value=data } catch { unidades.value=[] }
}

// ── CRUD Artículo ─────────────────────────────────────────────────────────────
function abrirModalItem(item=null) {
  modalItem.value = item
    ? { visible:true, id:item.id, name:item.name, price:item.price, category_id:item.category_id, description:item.description||'', tax:item.tax||0, active:item.active }
    : { visible:true, id:null, name:'', price:0, category_id:null, description:'', tax:0, active:1 }
}
function cerrarModalItem() { modalItem.value.visible=false }

async function guardarItem() {
  if (!modalItem.value.name) return
  guardando.value=true
  try {
    const p={ name:modalItem.value.name, price:modalItem.value.price, category_id:modalItem.value.category_id,
              description:modalItem.value.description, tax:modalItem.value.tax, active:modalItem.value.active }
    if (modalItem.value.id) await api.put(`${BASE}/${modalItem.value.id}`, p)
    else await api.post(BASE, p)
    showToast('Artículo guardado', 'success')
    cerrarModalItem(); await cargarItems()
  } catch(e) { showToast(e?.response?.data?.detail||'Error al guardar','error') }
  finally { guardando.value=false }
}
async function eliminar(id) {
  const { isConfirmed } = await window.Swal.fire({
    title:'¿Desactivar este artículo?', text:'Se ocultará del catálogo pero se conserva el historial.',
    icon:'warning', showCancelButton:true, confirmButtonColor:'#e11d48',
    confirmButtonText:'Sí, desactivar', cancelButtonText:'Cancelar',
  })
  if (!isConfirmed) return
  try { await api.delete(`${BASE}/${id}`); showToast('Artículo desactivado','success'); await cargarItems() }
  catch { showToast('Error al desactivar','error') }
}

// ── Panel ─────────────────────────────────────────────────────────────────────
async function abrirPanel(item, tab) {
  panel.value = { visible:true, item, tab, loadingIngredientes:false, loadingImpresoras:false, loadingModificadores:false }
  if (tab==='ingredientes') await cargarIngredientes()
  if (tab==='impresoras')   await cargarImpresoras()
  if (tab==='modificadores') await cargarModificadores()
}
function cerrarPanel() { panel.value.visible=false; ingredientes.value=[]; impresoras.value=[]; modificadores.value=[] }

// ── Ingredientes / Receta ─────────────────────────────────────────────────────
async function cargarIngredientes() {
  panel.value.loadingIngredientes=true
  try { const{data}=await api.get(`${BASE}/${panel.value.item.id}/ingredientes`); ingredientes.value=data }
  catch { ingredientes.value=[] }
  finally { panel.value.loadingIngredientes=false }
}
async function agregarIngrediente() {
  if (!formIngrediente.value.supply_item_id) return
  try {
    await api.post(`${BASE}/${panel.value.item.id}/ingredientes`, {
      supply_item_id: formIngrediente.value.supply_item_id,
      quantity: formIngrediente.value.quantity,
      unit_id: formIngrediente.value.unit_id,
    })
    formIngrediente.value = { visible:false, supply_item_id:null, quantity:1, unit_id:null }
    await cargarIngredientes(); await cargarItems()
  } catch { showToast('Error al agregar ingrediente','error') }
}
async function eliminarIngrediente(insumoId) {
  const { isConfirmed } = await window.Swal.fire({ title:'¿Quitar ingrediente?', icon:'warning', showCancelButton:true, confirmButtonColor:'#e11d48', confirmButtonText:'Quitar', cancelButtonText:'Cancelar' })
  if (!isConfirmed) return
  try { await api.delete(`${BASE}/${panel.value.item.id}/ingredientes/${insumoId}`); await cargarIngredientes(); await cargarItems() }
  catch { showToast('Error','error') }
}

// ── Impresoras ────────────────────────────────────────────────────────────────
async function cargarImpresoras() {
  panel.value.loadingImpresoras=true
  try { const{data}=await api.get(`${BASE}/${panel.value.item.id}/impresoras`); impresoras.value=data }
  catch { impresoras.value=[] }
  finally { panel.value.loadingImpresoras=false }
}
async function guardarImpresoras() {
  const ids = impresoras.value.filter(i=>i.assigned).map(i=>i.id)
  try { await api.put(`${BASE}/${panel.value.item.id}/impresoras`, { printer_ids:ids }); showToast('Impresoras guardadas','success'); await cargarItems() }
  catch { showToast('Error al guardar impresoras','error') }
}

// ── Modificadores ─────────────────────────────────────────────────────────────
async function cargarModificadores() {
  panel.value.loadingModificadores=true
  try { const{data}=await api.get(`${BASE}/${panel.value.item.id}/modificadores`); modificadores.value=data }
  catch { modificadores.value=[] }
  finally { panel.value.loadingModificadores=false }
}
async function crearModificador() {
  if (!formModificador.value.name) return
  try {
    await api.post(`${BASE}/${panel.value.item.id}/modificadores`, { name:formModificador.value.name, is_required:formModificador.value.is_required, is_multiple:formModificador.value.is_multiple })
    formModificador.value.visible=false; await cargarModificadores()
  } catch { showToast('Error','error') }
}
async function eliminarModificador(gId) {
  const { isConfirmed } = await window.Swal.fire({ title:'¿Eliminar grupo y sus opciones?', icon:'warning', showCancelButton:true, confirmButtonColor:'#e11d48', confirmButtonText:'Eliminar', cancelButtonText:'Cancelar' })
  if (!isConfirmed) return
  try { await api.delete(`${BASE}/${panel.value.item.id}/modificadores/${gId}`); await cargarModificadores() } catch { showToast('Error','error') }
}
function abrirFormOpcion(g) {
  formOpcion.value = { visible:true, groupId:g.id, groupName:g.name, name:'', extra_price:0 }
}
async function crearOpcion() {
  if (!formOpcion.value.name) return
  try {
    await api.post(`${BASE}/${panel.value.item.id}/modificadores/${formOpcion.value.groupId}/opciones`, { name:formOpcion.value.name, extra_price:formOpcion.value.extra_price })
    formOpcion.value.visible=false; await cargarModificadores()
  } catch { showToast('Error','error') }
}
async function eliminarOpcion(gId, oId) {
  try { await api.delete(`${BASE}/${panel.value.item.id}/modificadores/${gId}/opciones/${oId}`); await cargarModificadores() }
  catch { showToast('Error','error') }
}
</script>

<style scoped>
.crud-view { padding:0; }
.crud-header { display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px;gap:12px; }
.crud-titulo { font-weight:700;font-size:16px;color:#1e3a5f;margin:0; }
.crud-sub    { font-size:13px;color:#64748b;margin:2px 0 0;max-width:500px; }
.header-tools{ display:flex;gap:10px;align-items:center;flex-shrink:0; }
.inp-buscar  { border:1.5px solid #cbd5e1;border-radius:8px;padding:8px 12px;font-size:13px;color:#1e3a5f;outline:none;width:180px; }
.inp-buscar:focus { border-color:#1d4ed8; }
.btn-nuevo   { display:flex;align-items:center;gap:6px;background:linear-gradient(90deg,#1e3a5f,#1d4ed8);color:#fff;border:none;border-radius:8px;padding:9px 16px;font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap; }
.estado-carga,.estado-vacio { display:flex;flex-direction:column;align-items:center;gap:10px;padding:60px 20px;color:#94a3b8;font-size:14px; }
.estado-vacio i { font-size:40px; }
.items-grid  { display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px; }
.item-card   { background:#fff;border:2px solid #e2e8f0;border-radius:12px;padding:14px;display:flex;flex-direction:column;gap:8px;transition:border-color .15s; }
.item-card:hover { border-color:#1d4ed8; }
.item-card--inactivo { opacity:.5; }
.item-top    { display:flex;justify-content:space-between;align-items:center;gap:6px; }
.item-cat    { font-size:10px;font-weight:700;border-radius:10px;padding:2px 8px;max-width:130px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap; }
.badge-activo  { font-size:10px;background:#dcfce7;color:#16a34a;border-radius:10px;padding:2px 8px;font-weight:700;white-space:nowrap; }
.badge-inactivo{ font-size:10px;background:#f1f5f9;color:#94a3b8;border-radius:10px;padding:2px 8px;white-space:nowrap; }
.item-nombre { font-weight:700;font-size:14px;color:#1e3a5f; }
.item-precio { font-size:20px;font-weight:800;color:#1d4ed8; }
.item-meta   { display:flex;gap:12px;font-size:12px;color:#94a3b8; }
.item-meta span { display:flex;align-items:center;gap:4px; }
.item-acciones { display:flex;gap:5px;margin-top:2px; }
.btn-accion  { flex:1;background:none;border:1px solid #e2e8f0;border-radius:6px;padding:5px 0;cursor:pointer;color:#475569;font-size:13px;transition:.15s; }
.btn-accion:hover { background:#f0f4ff;color:#1d4ed8;border-color:#1d4ed8; }
.btn-accion--danger:hover { background:#fff1f2;color:#e11d48;border-color:#e11d48; }
.modal-overlay { position:fixed;inset:0;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;z-index:1050; }
.modal-card  { background:#fff;border-radius:16px;width:100%;max-width:460px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.25); }
.modal-hdr   { display:flex;justify-content:space-between;align-items:center;padding:16px 20px;background:linear-gradient(90deg,#1e3a5f,#1d4ed8);color:#fff;font-weight:700;font-size:15px; }
.btn-x       { background:none;border:none;color:#fff;cursor:pointer;font-size:16px;opacity:.8; }
.btn-x:hover { opacity:1; }
.modal-body  { padding:20px;display:flex;flex-direction:column;gap:12px;max-height:70vh;overflow-y:auto; }
.campo       { display:flex;flex-direction:column;gap:4px; }
.campo label { font-size:12px;font-weight:600;color:#475569; }
.campo-row   { display:flex;gap:12px; }
.campo-row .campo { flex:1; }
.inp         { border:1.5px solid #cbd5e1;border-radius:8px;padding:8px 12px;font-size:14px;color:#1e3a5f;outline:none;width:100%; }
.inp:focus   { border-color:#1d4ed8; }
.campo-check { display:flex;align-items:center;gap:8px;font-size:13px;color:#475569; }
.modal-ftr   { display:flex;gap:10px;justify-content:flex-end;padding:14px 20px;border-top:1px solid #f1f5f9; }
.btn-cancel  { background:#f1f5f9;border:none;border-radius:8px;padding:9px 18px;font-size:14px;cursor:pointer;color:#475569;font-weight:600; }
.btn-save    { background:linear-gradient(90deg,#1e3a5f,#1d4ed8);border:none;border-radius:8px;padding:9px 20px;font-size:14px;font-weight:700;color:#fff;cursor:pointer; }
.btn-save:disabled { opacity:.6;cursor:not-allowed; }
.panel-overlay  { position:fixed;inset:0;background:rgba(0,0,0,.35);z-index:1040;display:flex;justify-content:flex-end; }
.panel-lateral  { width:100%;max-width:480px;height:100%;background:#fff;display:flex;flex-direction:column;box-shadow:-8px 0 32px rgba(0,0,0,.18);overflow:hidden; }
.panel-hdr      { display:flex;justify-content:space-between;align-items:center;padding:16px 20px;background:linear-gradient(90deg,#1e3a5f,#1d4ed8);color:#fff; }
.panel-titulo   { font-weight:700;font-size:16px; }
.panel-sub      { font-size:13px;opacity:.8; }
.panel-tabs     { display:flex;border-bottom:2px solid #e2e8f0;background:#f8fafc; }
.ptab           { flex:1;padding:12px 8px;border:none;background:none;font-size:13px;font-weight:500;color:#64748b;cursor:pointer;border-bottom:3px solid transparent;transition:.15s;margin-bottom:-2px; }
.ptab.active    { color:#1d4ed8;border-bottom-color:#1d4ed8;font-weight:700; }
.panel-body     { flex:1;overflow-y:auto;padding:16px; }
.sub-header     { display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;font-size:13px;color:#475569;font-weight:600; }
.mini-carga     { display:flex;justify-content:center;padding:30px; }
.mini-vacio     { display:flex;align-items:center;gap:8px;justify-content:center;padding:30px;color:#94a3b8;font-size:13px; }
.receta-lista   { display:flex;flex-direction:column;gap:6px;margin-bottom:12px; }
.receta-item    { display:flex;align-items:center;justify-content:space-between;background:#f8fafc;border-radius:8px;padding:8px 12px; }
.receta-info    { display:flex;flex-direction:column;gap:2px; }
.receta-nombre  { font-weight:600;font-size:13px;color:#1e3a5f; }
.receta-qty     { font-size:11px;color:#64748b; }
.btn-x-sm       { background:none;border:none;color:#94a3b8;cursor:pointer;font-size:14px;padding:2px 4px; }
.btn-x-sm:hover { color:#e11d48; }
.imp-lista      { display:flex;flex-direction:column;gap:8px; }
.imp-item       { display:flex;align-items:center;gap:12px;border:2px solid #e2e8f0;border-radius:10px;padding:10px 14px;cursor:pointer;transition:.15s; }
.imp-item--sel  { border-color:#1d4ed8;background:#f0f4ff; }
.imp-item input { display:none; }
.imp-item i     { font-size:18px;color:#1d4ed8; }
.imp-nombre     { font-weight:700;font-size:13px;color:#1e3a5f; }
.imp-tipo       { font-size:11px;color:#64748b; }
.grupos-lista   { display:flex;flex-direction:column;gap:10px;margin-bottom:12px; }
.grupo-card     { border:2px solid #e2e8f0;border-radius:10px;overflow:hidden; }
.grupo-hdr      { display:flex;align-items:center;gap:8px;padding:10px 12px;background:#f8fafc; }
.grupo-nombre   { font-weight:700;font-size:13px;color:#1e3a5f;flex:1; }
.grupo-badges   { display:flex;gap:4px; }
.badge-req      { font-size:10px;background:#fef3c7;color:#d97706;border-radius:6px;padding:1px 6px;font-weight:700; }
.badge-mul      { font-size:10px;background:#ede9fe;color:#7c3aed;border-radius:6px;padding:1px 6px;font-weight:700; }
.grupo-acc      { display:flex;gap:4px; }
.detalles-lista { padding:8px 12px;display:flex;flex-direction:column;gap:4px; }
.detalle-item   { display:flex;align-items:center;gap:8px;font-size:13px; }
.det-nombre     { flex:1;color:#1e3a5f; }
.det-precio     { font-weight:700;font-size:12px;color:#64748b; }
.precio-pos     { color:#16a34a; }
.precio-neg     { color:#e11d48; }
.mini-modal     { background:#f0f4ff;border:2px solid #1d4ed8;border-radius:10px;padding:14px;display:flex;flex-direction:column;gap:8px;margin-top:10px; }
.mini-label     { font-size:12px;color:#475569;margin:0; }
.mini-row       { display:flex;gap:8px; }
.inp-sm         { border:1.5px solid #cbd5e1;border-radius:6px;padding:6px 10px;font-size:13px;color:#1e3a5f;outline:none;width:100%; }
.inp-sm:focus   { border-color:#1d4ed8; }
.mini-checks    { display:flex;gap:14px;font-size:13px;color:#475569; }
.mini-modal-btns{ display:flex;gap:8px;justify-content:flex-end; }
.btn-mini       { display:flex;align-items:center;gap:4px;background:#1d4ed8;color:#fff;border:none;border-radius:6px;padding:6px 12px;font-size:12px;font-weight:600;cursor:pointer; }
.btn-mini--sm   { padding:3px 8px; }
.btn-mini--cancel { background:#f1f5f9;color:#475569; }
@media(max-width:768px){.crud-header{flex-direction:column;gap:10px;}.header-tools{flex-wrap:wrap;}.items-grid{grid-template-columns:1fr;}.panel-lateral{max-width:100%;}}
@media(max-width:576px){.campo-row{flex-direction:column;}}
</style>
