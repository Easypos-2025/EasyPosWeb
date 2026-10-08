<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1 class="page-title"><i class="bi bi-box-seam me-2"></i>{{ moduleName }}</h1>
        <p class="page-subtitle">Materias primas y artículos base del inventario</p>
      </div>
      <button class="btn btn-primary" @click="openCreate"><i class="bi bi-plus-lg"></i> Nuevo</button>
    </div>

    <!-- KPI -->
    <div class="kpi-bar">
      <div class="kpi-card">
        <span class="kpi-num">{{ items.length }}</span>
        <span class="kpi-label">Total</span>
      </div>
      <div class="kpi-card kpi-red">
        <span class="kpi-num">{{ lowStock.length }}</span>
        <span class="kpi-label">Stock bajo</span>
      </div>
      <div class="kpi-card kpi-green">
        <span class="kpi-num">{{ items.filter(i => i.control_stock).length }}</span>
        <span class="kpi-label">Con control</span>
      </div>
    </div>

    <div class="filters-row">
      <input v-model="search" class="form-control f-search" :placeholder="`Buscar ${moduleName.toLowerCase()} por nombre o código...`" />
      <select v-model="filterCat" class="form-select f-sel">
        <option :value="null">Todas las categorías</option>
        <option v-for="c in $ordenAlfa(categories, 'name')" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
      <select v-model="filterStock" class="form-select f-sel">
        <option value="">Todos</option>
        <option value="low">Stock bajo</option>
        <option value="ok">Stock OK</option>
      </select>
    </div>

    <!-- Tabla (tablet / PC) -->
    <div class="table-card only-desktop">
      <div v-if="loading" class="table-loading"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Id Item</th>
            <th>Código</th>
            <th>Nombre</th>
            <th>Categoría</th>
            <th>Unidad uso</th>
            <th class="text-right">Costo</th>
            <th class="text-right">Mínimo</th>
            <th class="text-center">Control</th>
            <th class="text-center">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="i in filtered" :key="i.id" :class="{ 'row-low': isLowStock(i), 'row-off': !i.is_active }">
            <td class="text-muted">{{ i.id_item || '—' }}</td>
            <td class="text-muted">{{ i.code || '—' }}</td>
            <td><strong>{{ i.description }}</strong>
              <span v-if="i.armar_plato" class="tag tag-armar" title="Opción para armar">Armar</span>
            </td>
            <td class="text-muted">{{ catName(i.category_id) }}</td>
            <td class="text-muted">{{ i.unit_name || '—' }}</td>
            <td class="text-right">{{ fmtMoney(i.cost_price) }}</td>
            <td class="text-right text-muted">{{ fmtNum(i.min_stock, 4) }}</td>
            <td class="text-center">
              <span v-if="i.control_stock" class="badge-yes">Sí</span>
              <span v-else class="badge-no">No</span>
            </td>
            <td class="text-center">
              <div class="action-row">
                <button class="btn btn-sm btn-outline-primary" @click="openEdit(i)" title="Editar"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-sm btn-outline-secondary" @click="openAdjust(i)" title="Ajustar stock"><i class="bi bi-sliders"></i></button>
              </div>
            </td>
          </tr>
          <tr v-if="filtered.length === 0">
            <td colspan="9" class="text-center text-muted py-4">Sin registros</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Tarjetas (móvil) -->
    <div class="cards only-mobile">
      <div v-if="loading" class="table-loading"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
      <template v-else>
        <div v-for="i in filtered" :key="i.id" class="s-card" :class="{ 'row-low': isLowStock(i), 'row-off': !i.is_active }" @click="openEdit(i)">
          <div class="s-card-top">
            <strong>{{ i.description }}</strong>
            <span class="text-muted">#{{ i.id_item || '—' }}</span>
          </div>
          <div class="s-card-meta">
            <span>{{ catName(i.category_id) }}</span>
            <span>{{ i.unit_name || '—' }}</span>
            <span>{{ fmtMoney(i.cost_price) }}</span>
          </div>
          <div class="s-card-tags">
            <span v-if="i.control_stock" class="badge-yes">Controla</span>
            <span v-if="i.armar_plato" class="tag tag-armar">Armar</span>
            <button class="btn btn-sm btn-outline-secondary ms-auto" @click.stop="openAdjust(i)"><i class="bi bi-sliders"></i></button>
          </div>
        </div>
        <div v-if="filtered.length === 0" class="text-center text-muted py-4">Sin registros</div>
      </template>
    </div>

    <!-- ═══ MODAL CREAR / EDITAR (3 paneles como el escritorio) ═══ -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-box modal-xl">
        <div class="mh">
          <h3><i class="bi bi-box-seam me-2"></i>{{ editing ? form.description || moduleName : `Nuevo — ${moduleName}` }}</h3>
          <button class="btn-x" @click="closeModal"><i class="bi bi-x-lg"></i></button>
        </div>

        <!-- Pestañas (solo móvil / tablet) -->
        <div class="ptabs">
          <button :class="['ptab', { active: tab === 'datos' }]" @click="tab = 'datos'"><i class="bi bi-card-text"></i> Datos</button>
          <button :class="['ptab', { active: tab === 'prov' }]" @click="tab = 'prov'"><i class="bi bi-truck"></i> Proveedores <span v-if="provSel.length" class="cnt">{{ provSel.length }}</span></button>
          <button :class="['ptab', { active: tab === 'fm' }]" @click="tab = 'fm'"><i class="bi bi-rulers"></i> Medidas <span v-if="fmSel.length" class="cnt">{{ fmSel.length }}</span></button>
        </div>

        <div class="grid3">
          <!-- ── Panel 1: Proveedores ── -->
          <section class="panel panel-prov" :class="{ 'p-hidden': tab !== 'prov' }">
            <div class="panel-ttl">Asignar proveedores</div>
            <input v-model="provSearch" class="form-control form-control-sm" placeholder="Buscar proveedor..." />
            <div class="pick-list">
              <button v-for="p in provDisponibles" :key="p.id_proveedor" class="pick-btn" @click="addProv(p)">{{ p.name }}</button>
              <div v-if="!provDisponibles.length" class="mini-empty">Sin proveedores disponibles</div>
            </div>
            <div class="sel-list">
              <div v-for="p in provSel" :key="p.id_proveedor" class="sel-row">
                <span class="sel-name">{{ p.name }}</span>
                <button class="btn-quitar" @click="provSel = provSel.filter(x => x.id_proveedor !== p.id_proveedor)">Quitar</button>
              </div>
            </div>
            <button class="btn btn-outline-primary btn-block" @click="openQuick('prov')"><i class="bi bi-plus-lg"></i> Crear nuevo proveedor</button>
          </section>

          <!-- ── Panel 2: Formas de medida ── -->
          <section class="panel panel-fm" :class="{ 'p-hidden': tab !== 'fm' }">
            <div class="panel-ttl">Seleccionar forma de medida</div>
            <input v-model="fmSearch" class="form-control form-control-sm" placeholder="Buscar forma de medida..." />
            <div class="pick-grid">
              <button v-for="m in fmDisponibles" :key="m.id" class="pick-btn" @click="addFm(m)">{{ m.name }}</button>
            </div>
            <div class="sel-list">
              <div v-for="m in fmSel" :key="m.id_forma_medida" class="sel-row">
                <span class="sel-name">{{ m.name }}</span>
                <input v-model.number="m.cant_unidades_minimas" type="number" min="0.001" step="0.001" class="form-control form-control-sm sel-qty" title="Cantidad de unidades mínimas" />
                <button class="btn-quitar" @click="fmSel = fmSel.filter(x => x.id_forma_medida !== m.id_forma_medida)">Quitar</button>
              </div>
            </div>
            <button class="btn btn-outline-primary btn-block" @click="openQuick('fm')"><i class="bi bi-plus-lg"></i> Crear nueva forma de medida</button>
          </section>

          <!-- ── Panel 3: Datos del insumo ── -->
          <section class="panel panel-datos" :class="{ 'p-hidden': tab !== 'datos' }">
            <div class="fg">
              <label>Nombre *</label>
              <input v-model="form.description" class="form-control inp-name" maxlength="255" />
            </div>
            <div class="form-row2">
              <div class="fg">
                <label>Unidad uso</label>
                <select v-model="form.unit_uso_id" class="form-select">
                  <option :value="null">— Seleccione —</option>
                  <option v-for="m in $ordenAlfa(formasUnidadUso, 'name')" :key="m.id" :value="m.id">{{ m.name }}</option>
                </select>
              </div>
              <div class="fg">
                <label>Costo por und. de uso</label>
                <CurrencyInput v-model="form.cost_price" class="form-control text-right" />
              </div>
            </div>
            <div class="form-row2">
              <div class="fg">
                <label>Stock mínimo</label>
                <input v-model.number="form.min_stock" type="number" min="0" step="0.001" class="form-control" />
              </div>
              <div class="fg" v-if="!editing">
                <label>Stock inicial</label>
                <input v-model.number="form.stock_qty" type="number" min="0" step="0.001" class="form-control" />
              </div>
            </div>
            <div class="fg">
              <label>Categoría</label>
              <div class="unit-row">
                <select v-model="form.category_id" class="form-select">
                  <option :value="null">Sin categoría</option>
                  <option v-for="c in $ordenAlfa(categories, 'name')" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
                <button type="button" class="btn-add-unit" title="Crear nueva categoría" @click="openQuick('cat')"><i class="bi bi-plus-lg"></i></button>
              </div>
            </div>

            <div class="flags">
              <label class="flag"><input type="checkbox" v-model="form.control_stock" :true-value="1" :false-value="0" /> Este producto se controla</label>
              <label class="flag"><input type="checkbox" v-model="form.producto_preparado" :true-value="1" :false-value="0" /> Producto preparado</label>
              <label class="flag"><input type="checkbox" v-model="form.opcion_cambios" :true-value="1" :false-value="0" /> Insumo para cambios</label>
              <label class="flag"><input type="checkbox" v-model="form.armar_plato" :true-value="1" :false-value="0" /> Opción para armar</label>
              <label class="flag"><input type="checkbox" v-model="form.centro_produccion" :true-value="1" :false-value="0" /> Producto centro de producción</label>
            </div>

            <div class="form-row2">
              <div class="fg">
                <label>Código insumo</label>
                <input v-model="form.code" class="form-control" maxlength="50" />
              </div>
              <div class="fg">
                <label>Fecha vencimiento</label>
                <CustomDatePicker v-model="form.fecha_vence" />
              </div>
            </div>

            <div v-if="editing" class="keys">
              <span>Id Item <b>{{ form.id_item ?? '—' }}</b></span>
              <span>Id Grupo <b>{{ form.id_grupo ?? '—' }}</b></span>
              <span>Posición <b>{{ form.posicion ?? '—' }}</b></span>
            </div>
          </section>
        </div>

        <div class="mf">
          <button v-if="editing" class="btn btn-danger-soft btn-sm me-auto" @click="deactivate" :disabled="saving">
            <i class="bi bi-slash-circle"></i> {{ form.is_active ? 'Desactivar' : 'Inactivo' }}
          </button>
          <button class="btn btn-secondary btn-sm" @click="closeModal">Salir</button>
          <button class="btn btn-primary btn-sm" @click="submit" :disabled="saving">
            <i v-if="saving" class="bi bi-arrow-repeat spin"></i>
            {{ saving ? 'Guardando...' : (editing ? 'Guardar cambios' : 'Guardar') }}
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL CREACIÓN RÁPIDA (proveedor / forma de medida / categoría) -->
    <div v-if="quick.show" class="modal-overlay modal-top" @click.self="quick.show = false">
      <div class="modal-box modal-sm">
        <div class="mh">
          <h3>{{ quickTitle }}</h3>
          <button class="btn-x" @click="quick.show = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="mb-area">
          <div class="fg">
            <label>Nombre *</label>
            <input v-model="quick.name" class="form-control" maxlength="100" @keydown.enter="submitQuick" v-focus />
          </div>
          <template v-if="quick.kind === 'prov'">
            <div class="fg"><label>NIT</label><input v-model="quick.nit" class="form-control" maxlength="50" /></div>
            <div class="fg"><label>Celular</label><input v-model="quick.cel" class="form-control" maxlength="50" /></div>
          </template>
        </div>
        <div class="mf">
          <button class="btn btn-secondary btn-sm" @click="quick.show = false">Cancelar</button>
          <button class="btn btn-primary btn-sm" @click="submitQuick" :disabled="quick.saving">
            {{ quick.saving ? 'Guardando...' : 'Crear' }}
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL AJUSTE RÁPIDO DE STOCK -->
    <div v-if="showAdjust" class="modal-overlay" @click.self="showAdjust = false">
      <div class="modal-box modal-sm">
        <div class="mh">
          <h3><i class="bi bi-sliders me-2"></i>Ajustar Stock</h3>
          <button class="btn-x" @click="showAdjust = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="mb-area">
          <div class="info-block">
            <strong>{{ adjustItem?.description }}</strong>
            <span class="text-muted">Stock actual: {{ fmtNum(adjustItem?.stock_qty, 4) }}</span>
          </div>
          <div class="fg">
            <label>Nuevo stock *</label>
            <input v-model.number="adjustForm.stock_qty" type="number" step="0.001" class="form-control" />
          </div>
          <div class="fg">
            <label>Motivo del ajuste *</label>
            <input v-model="adjustForm.adjustment_notes" class="form-control" maxlength="255" placeholder="Conteo físico, pérdida, corrección..." />
          </div>
        </div>
        <div class="mf">
          <button class="btn btn-secondary btn-sm" @click="showAdjust = false">Cancelar</button>
          <button class="btn btn-primary btn-sm" @click="submitAdjust" :disabled="saving">
            {{ saving ? 'Guardando...' : 'Ajustar' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import { useModuleName } from "@/composables/useModuleName"
import CustomDatePicker from "@/components/common/CustomDatePicker.vue"

const { moduleName } = useModuleName()
const vFocus = { mounted: el => el.focus() }

const items       = ref([])
const formas      = ref([])        // pos_measure_forms
const categories  = ref([])        // pos_product_categories
const proveedores = ref([])        // suppliers (id_proveedor)
const loading     = ref(true)
const search      = ref("")
const filterStock = ref("")
const filterCat   = ref(null)

const showModal = ref(false)
const editing   = ref(null)
const saving    = ref(false)
const form      = ref({})
const tab       = ref("datos")

const provSel    = ref([])         // [{ id_proveedor, name }]
const provSearch = ref("")
const fmSel      = ref([])         // [{ id_forma_medida, name, cant_unidades_minimas }]
const fmSearch   = ref("")

const showAdjust = ref(false)
const adjustItem = ref(null)
const adjustForm = ref({})

const quick = ref({ show: false, kind: "", name: "", nit: "", cel: "", saving: false })
const quickTitle = computed(() => ({ prov: "Nuevo proveedor", fm: "Nueva forma de medida", cat: "Nueva categoría" }[quick.value.kind]))

// Moneda: mismo formateo que el resto del POS (COP por defecto)
const _money = new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 })
const fmtMoney = v => _money.format(Number(v) || 0)
function fmtNum(val, dec = 2) {
  return Number(val || 0).toLocaleString("es-CO", { minimumFractionDigits: 0, maximumFractionDigits: dec })
}

const catMap = computed(() => Object.fromEntries(categories.value.map(c => [c.id, c.name])))
const catName = id => (id && catMap.value[id]) || "—"

function isLowStock(i) {
  return i.control_stock && i.min_stock > 0 && i.stock_qty <= i.min_stock
}
const lowStock = computed(() => items.value.filter(isLowStock))

const filtered = computed(() => {
  const q = search.value.toLowerCase()
  return items.value.filter(i => {
    const matchQ = !q || (i.description || "").toLowerCase().includes(q) || (i.code || "").toLowerCase().includes(q)
    const matchC = !filterCat.value || i.category_id === filterCat.value
    const matchS = !filterStock.value ||
      (filterStock.value === "low" && isLowStock(i)) ||
      (filterStock.value === "ok" && !isLowStock(i))
    return matchQ && matchC && matchS
  })
})

const provDisponibles = computed(() => {
  const q = provSearch.value.toLowerCase()
  const taken = new Set(provSel.value.map(p => p.id_proveedor))
  return proveedores.value.filter(p => !taken.has(p.id_proveedor) && (!q || p.name.toLowerCase().includes(q)))
})
// Unidad uso: solo formas activas (forma_medida.Activa = 1); se conserva la ya asignada aunque esté inactiva
const formasUnidadUso = computed(() =>
  formas.value.filter(m => Number(m.is_active) === 1 || m.id === form.value.unit_uso_id)
)

const fmDisponibles = computed(() => {
  const q = fmSearch.value.toLowerCase()
  const taken = new Set(fmSel.value.map(m => m.id_forma_medida))
  return formas.value.filter(m => !taken.has(m.id) && (!q || m.name.toLowerCase().includes(q)))
})

async function load() {
  loading.value = true
  try {
    const [ir, fr, cr, pr] = await Promise.all([
      api.get("/supply-items/"),
      api.get("/supply-items/catalogos/formas-medida"),
      api.get("/supply-items/catalogos/categorias"),
      api.get("/suppliers/"),
    ])
    items.value       = ir.data
    formas.value      = fr.data
    categories.value  = cr.data
    proveedores.value = pr.data.filter(p => p.is_active && p.id_proveedor)
  } catch { showToast("Error cargando información", "error") }
  finally { loading.value = false }
}

function emptyForm() {
  return { description: "", code: "", unit_uso_id: null, category_id: null, cost_price: 0, stock_qty: 0,
           min_stock: 0, control_stock: 1, producto_preparado: 0, opcion_cambios: 0, armar_plato: 0,
           centro_produccion: 0, fecha_vence: "", is_active: 1 }
}

function openCreate() {
  editing.value = null
  form.value = emptyForm()
  provSel.value = []; fmSel.value = []
  provSearch.value = ""; fmSearch.value = ""
  tab.value = "datos"
  showModal.value = true
}

async function openEdit(i) {
  editing.value = i
  form.value = { ...emptyForm(), ...i, fecha_vence: i.fecha_vence || "" }
  provSel.value = []; fmSel.value = []
  provSearch.value = ""; fmSearch.value = ""
  tab.value = "datos"
  showModal.value = true
  try {
    const [pr, fr] = await Promise.all([
      api.get(`/supply-items/${i.id}/proveedores`),
      api.get(`/supply-items/${i.id}/formas-medida`),
    ])
    provSel.value = pr.data.map(p => ({ id_proveedor: p.id_proveedor, name: p.name || `Proveedor ${p.id_proveedor}` }))
    fmSel.value   = fr.data.map(m => ({ id_forma_medida: m.id_forma_medida, name: m.name || `Medida ${m.id_forma_medida}`,
                                        cant_unidades_minimas: Number(m.cant_unidades_minimas) || 1 }))
  } catch { showToast("No se pudieron cargar proveedores / medidas", "warning") }
}

function closeModal() { showModal.value = false }

function addProv(p) { provSel.value.push({ id_proveedor: p.id_proveedor, name: p.name }) }
function addFm(m)   { fmSel.value.push({ id_forma_medida: m.id, name: m.name, cant_unidades_minimas: 1 }) }

function payload() {
  const f = form.value
  const p = {
    description: (f.description || "").trim(), code: (f.code || "").trim() || null,
    unit_uso_id: f.unit_uso_id || null, category_id: f.category_id || null,
    cost_price: Number(f.cost_price) || 0, min_stock: Number(f.min_stock) || 0,
    control_stock: f.control_stock ? 1 : 0, producto_preparado: f.producto_preparado ? 1 : 0,
    opcion_cambios: f.opcion_cambios ? 1 : 0, armar_plato: f.armar_plato ? 1 : 0,
    centro_produccion: f.centro_produccion ? 1 : 0, fecha_vence: f.fecha_vence || null,
  }
  if (!editing.value) p.stock_qty = Number(f.stock_qty) || 0
  return p
}

async function submit() {
  if (!form.value.description?.trim()) { showToast("El nombre es requerido", "warning"); tab.value = "datos"; return }
  if (fmSel.value.some(m => !(Number(m.cant_unidades_minimas) > 0))) {
    showToast("La cantidad de cada forma de medida debe ser mayor a 0", "warning"); tab.value = "fm"; return
  }
  saving.value = true
  try {
    const r = editing.value
      ? await api.put(`/supply-items/${editing.value.id}`, payload())
      : await api.post("/supply-items/", payload())
    const saved = r.data
    await Promise.all([
      api.put(`/supply-items/${saved.id}/proveedores`, { ids: provSel.value.map(p => p.id_proveedor) }),
      api.put(`/supply-items/${saved.id}/formas-medida`, {
        items: fmSel.value.map(m => ({ id_forma_medida: m.id_forma_medida, cant_unidades_minimas: Number(m.cant_unidades_minimas) })),
      }),
    ])
    const idx = items.value.findIndex(x => x.id === saved.id)
    if (idx !== -1) items.value[idx] = saved
    else items.value.unshift(saved)
    showModal.value = false
    showToast("Guardado", "success")
  } catch (e) { showToast(e.response?.data?.detail || "Error guardando", "error") }
  finally { saving.value = false }
}

async function deactivate() {
  if (!form.value.is_active) return
  saving.value = true
  try {
    const r = await api.put(`/supply-items/${editing.value.id}`, { is_active: 0 })
    const idx = items.value.findIndex(x => x.id === r.data.id)
    if (idx !== -1) items.value[idx] = r.data
    form.value.is_active = 0
    showToast("Desactivado", "success")
  } catch (e) { showToast(e.response?.data?.detail || "Error", "error") }
  finally { saving.value = false }
}

function openAdjust(i) {
  adjustItem.value = i
  adjustForm.value = { stock_qty: i.stock_qty, adjustment_notes: "" }
  showAdjust.value = true
}

async function submitAdjust() {
  if (!adjustForm.value.adjustment_notes?.trim()) { showToast("El motivo es requerido", "warning"); return }
  saving.value = true
  try {
    const r = await api.put(`/supply-items/${adjustItem.value.id}`, {
      stock_qty: Number(adjustForm.value.stock_qty) || 0, adjustment_notes: adjustForm.value.adjustment_notes.trim(),
    })
    const idx = items.value.findIndex(x => x.id === adjustItem.value.id)
    if (idx !== -1) items.value[idx] = r.data
    showAdjust.value = false
    showToast("Stock ajustado", "success")
  } catch (e) { showToast(e.response?.data?.detail || "Error", "error") }
  finally { saving.value = false }
}

function openQuick(kind) {
  quick.value = { show: true, kind, name: "", nit: "", cel: "", saving: false }
}

async function submitQuick() {
  const q = quick.value
  if (!q.name.trim()) { showToast("El nombre es requerido", "warning"); return }
  q.saving = true
  try {
    if (q.kind === "prov") {
      const { data } = await api.post("/suppliers/", { name: q.name.trim(), nit: q.nit.trim(), telefono_celular: q.cel.trim() })
      proveedores.value.push(data)
      proveedores.value.sort((a, b) => a.name.localeCompare(b.name))
      addProv(data)
    } else if (q.kind === "fm") {
      const { data } = await api.post("/supply-items/catalogos/formas-medida", { name: q.name.trim() })
      formas.value.push(data)
      formas.value.sort((a, b) => a.name.localeCompare(b.name))
      addFm(data)
    } else {
      const { data } = await api.post("/supply-items/catalogos/categorias", { name: q.name.trim() })
      categories.value.push(data)
      categories.value.sort((a, b) => a.name.localeCompare(b.name))
      form.value.category_id = data.id
    }
    q.show = false
    showToast("Creado", "success")
  } catch (e) { showToast(e.response?.data?.detail || "Error al crear", "error") }
  finally { q.saving = false }
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1200px; }
.page-header    { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; gap: 12px; flex-wrap: wrap; }
.page-title     { font-size: 22px; font-weight: 700; color: #1e293b; margin: 0 0 4px; }
.page-subtitle  { font-size: 13px; color: #64748b; margin: 0; }
.kpi-bar  { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 18px; }
.kpi-card { background: #fff; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.07); padding: 12px 18px; display: flex; align-items: baseline; gap: 8px; }
.kpi-num  { font-size: 24px; font-weight: 800; color: #1e293b; }
.kpi-label { font-size: 12px; color: #94a3b8; }
.kpi-red .kpi-num   { color: #dc2626; }
.kpi-green .kpi-num { color: #16a34a; }
.filters-row { display: flex; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
.f-search { max-width: 300px; }
.f-sel    { max-width: 200px; }
.table-card  { background: #fff; border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,.08); overflow-x: auto; }
.table-loading { padding: 40px; text-align: center; color: #94a3b8; }
.data-table  { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { background: #f8fafc; color: #475569; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: .4px; padding: 11px 12px; border-bottom: 1px solid #e2e8f0; white-space: nowrap; }
.data-table td { padding: 11px 12px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.data-table tr:hover td { background: #f8fafc; }
.row-low td, .s-card.row-low { background: #fff5f5 !important; }
.row-off { opacity: .55; }
.text-center { text-align: center; }
.text-right  { text-align: right; }
.text-muted  { color: #94a3b8; font-size: 12px; }
.py-4        { padding: 32px 0; }
.ms-auto { margin-left: auto; }
.me-auto { margin-right: auto; }
.badge-yes { background: #dcfce7; color: #16a34a; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 20px; }
.badge-no  { background: #f1f5f9; color: #94a3b8; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 20px; }
.tag       { font-size: 10px; font-weight: 700; padding: 1px 7px; border-radius: 20px; margin-left: 6px; }
.tag-armar { background: #fef9c3; color: #a16207; }
.action-row { display: flex; gap: 4px; justify-content: center; }
.info-block { background: #f8fafc; border-radius: 8px; padding: 10px 14px; display: flex; flex-direction: column; gap: 4px; font-size: 13px; }

/* Tarjetas móvil */
.cards  { display: flex; flex-direction: column; gap: 8px; }
.s-card { background: #fff; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.07); padding: 12px 14px; cursor: pointer; }
.s-card-top  { display: flex; justify-content: space-between; gap: 8px; font-size: 14px; }
.s-card-meta { display: flex; flex-wrap: wrap; gap: 10px; font-size: 12px; color: #64748b; margin: 4px 0 8px; }
.s-card-tags { display: flex; align-items: center; gap: 6px; }
.only-mobile { display: none; }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 2000; padding: 16px; }
.modal-top     { z-index: 2100; }
.modal-box     { background: #fff; border-radius: 16px; width: 100%; max-width: 520px; max-height: 92vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,.2); }
.modal-xl      { max-width: 1120px; }
.modal-sm      { max-width: 400px; }
.mh  { display: flex; align-items: center; justify-content: space-between; padding: 14px 20px; border-bottom: 1px solid #f1f5f9; }
.mh h3 { font-size: 15px; font-weight: 700; color: #1e293b; margin: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.btn-x { background: none; border: none; font-size: 16px; cursor: pointer; color: #94a3b8; }
.mb-area { padding: 18px 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; }
.mf { padding: 12px 20px 16px; display: flex; justify-content: flex-end; gap: 8px; border-top: 1px solid #f1f5f9; flex-wrap: wrap; }

.ptabs { display: none; border-bottom: 2px solid #e2e8f0; }
.ptab  { flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px; padding: 10px 6px; border: none; background: none; font-size: 12px; font-weight: 600; color: #64748b; border-bottom: 3px solid transparent; margin-bottom: -2px; cursor: pointer; }
.ptab.active { color: #1d4ed8; border-bottom-color: #1d4ed8; }
.cnt { background: #1d4ed8; color: #fff; border-radius: 999px; font-size: 10px; padding: 0 6px; }

.grid3 { display: grid; grid-template-columns: 1fr 1fr 1.25fr; gap: 14px; padding: 16px 20px; overflow-y: auto; }
.panel { display: flex; flex-direction: column; gap: 10px; min-width: 0; }
.panel-prov { background: #ecfeff; border-radius: 12px; padding: 12px; }
.panel-fm   { background: #f0fdf4; border-radius: 12px; padding: 12px; }
.panel-ttl  { font-size: 13px; font-weight: 700; color: #1e3a5f; text-align: center; }
.pick-list  { display: flex; flex-direction: column; gap: 6px; max-height: 240px; overflow-y: auto; flex-shrink: 0; }
.pick-grid  { display: grid; grid-template-columns: 1fr 1fr; grid-auto-rows: minmax(36px, auto); align-content: start;
              gap: 6px; max-height: 240px; overflow-y: auto; flex-shrink: 0; }
.pick-btn   { display: flex; align-items: center; justify-content: center; min-height: 36px; flex-shrink: 0;
              background: #fff; border: 1.5px solid #e2e8f0; border-radius: 8px; padding: 6px 8px; font-size: 12px;
              line-height: 1.2; font-weight: 600; color: #334155; cursor: pointer; text-align: center;
              overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pick-list .pick-btn { justify-content: flex-start; }
.pick-btn:hover { border-color: #3b82f6; color: #1d4ed8; }
.sel-list   { display: flex; flex-direction: column; gap: 6px; min-height: 40px; }
.sel-row    { display: flex; align-items: center; gap: 6px; background: #fff; border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 4px 6px; }
.sel-name   { flex: 1; font-size: 12px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sel-qty    { width: 80px; text-align: right; }
.btn-quitar { border: none; background: #fee2e2; color: #b91c1c; font-size: 11px; font-weight: 700; border-radius: 6px; padding: 4px 8px; cursor: pointer; }
.mini-empty { font-size: 12px; color: #94a3b8; text-align: center; padding: 10px; }
.btn-block  { width: 100%; justify-content: center; margin-top: auto; }

.panel-datos .inp-name { font-weight: 700; text-align: center; }
.flags { display: flex; flex-direction: column; gap: 6px; background: #f8fafc; border-radius: 10px; padding: 10px 12px; }
.flag  { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 600; color: #374151; cursor: pointer; }
.flag input { width: 16px; height: 16px; }
.keys  { display: flex; gap: 10px; flex-wrap: wrap; font-size: 11px; color: #0e7490; background: #ecfeff; border-radius: 8px; padding: 6px 10px; }

.fg       { display: flex; flex-direction: column; gap: 4px; }
.fg label { font-size: 12px; font-weight: 600; color: #374151; }
.form-row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.form-control-sm { padding: 5px 8px; font-size: 12px; }
.btn { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; transition: all .15s; }
.btn-primary   { background: #3b82f6; color: #fff; } .btn-primary:hover { background: #2563eb; }
.btn:disabled  { opacity: .6; cursor: not-allowed; }
.btn-secondary { border: 1.5px solid #e2e8f0; background: #fff; color: #64748b; }
.btn-danger-soft { background: #fef2f2; color: #b91c1c; border: 1.5px solid #fecaca; }
.btn-sm { padding: 6px 12px; font-size: 12px; }
.btn-outline-primary   { background: #eff6ff; color: #1d4ed8; border: 1.5px solid #bfdbfe; }
.btn-outline-secondary { background: #f8fafc; color: #475569; border: 1.5px solid #e2e8f0; }
.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
.unit-row { display: flex; gap: 6px; align-items: center; }
.unit-row .form-select { flex: 1; }
.btn-add-unit { flex-shrink: 0; width: 36px; height: 36px; background: #eff6ff; border: 1.5px solid #bfdbfe; color: #1d4ed8; border-radius: 8px; display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 16px; }

/* Tablet: pestañas en lugar de 3 columnas */
@media (max-width: 1024px) {
  .ptabs { display: flex; }
  .grid3 { grid-template-columns: 1fr; }
  .p-hidden { display: none; }
  .pick-list, .pick-grid { max-height: 300px; }
}
/* Móvil */
@media (max-width: 768px) {
  .page-container { padding: 14px; }
  .only-desktop { display: none; }
  .only-mobile  { display: flex; }
  .f-search, .f-sel { max-width: none; flex: 1 1 100%; }
  .modal-overlay { padding: 0; align-items: flex-end; }
  .modal-box { max-height: 96vh; border-radius: 16px 16px 0 0; }
  .grid3 { padding: 12px 14px; }
}
@media (max-width: 576px) {
  .page-title { font-size: 18px; }
  .kpi-card { padding: 8px 12px; }
  .kpi-num  { font-size: 18px; }
  .form-row2 { grid-template-columns: 1fr; }
  .pick-grid { grid-template-columns: 1fr 1fr; }
  .ptab { font-size: 11px; }
  .mf .btn { flex: 1; justify-content: center; }
}
</style>
