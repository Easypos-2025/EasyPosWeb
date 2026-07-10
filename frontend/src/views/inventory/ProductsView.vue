<template>
  <div class="page-container">

    <!-- Tabs -->
    <div class="tabs-bar">
      <button :class="['tab-btn', { active: tab === 'servicio' }]" @click="tab = 'servicio'">
        <i class="bi bi-tools"></i> Servicios
        <span class="tab-count">{{ counts.servicio }}</span>
      </button>
      <button :class="['tab-btn', { active: tab === 'producto' }]" @click="tab = 'producto'">
        <i class="bi bi-box-seam-fill"></i> Productos / Repuestos
        <span class="tab-count">{{ counts.producto }}</span>
      </button>
    </div>

    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">
          <i :class="tab === 'servicio' ? 'bi bi-tools' : 'bi bi-box-seam-fill'"></i>
          {{ tab === 'servicio' ? 'Catálogo de Servicios' : 'Catálogo de Productos / Repuestos' }}
        </h1>
        <p class="page-subtitle">
          {{ tab === 'servicio'
            ? 'Lavados, cambios de aceite, mano de obra… sin control de inventario.'
            : 'Repuestos, insumos y accesorios con control de stock.' }}
        </p>
      </div>
      <button class="btn btn-primary" @click="openCreate">
        <i class="bi bi-plus-lg"></i>
        {{ tab === 'servicio' ? 'Nuevo Servicio' : 'Nuevo Producto' }}
      </button>
    </div>

    <!-- Filtros -->
    <div class="filters-row">
      <input v-model="search" class="form-control" :placeholder="`Buscar ${tab === 'servicio' ? 'servicio' : 'producto'}…`" style="max-width:260px" />
      <select v-model="filterCat" class="form-select" style="max-width:180px">
        <option value="">Todas las categorías</option>
        <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
      <select v-if="tab === 'producto'" v-model="filterBehavior" class="form-select" style="max-width:200px">
        <option value="">Todos los tipos</option>
        <option value="decrement">Inventario simple (repuesto)</option>
        <option value="recipe">Receta (descarga insumos)</option>
        <option value="presentation">Presentaciones (unidad/caja)</option>
        <option value="serialized">Serializado (IMEI / serie)</option>
        <option value="weight">Por peso (balanza)</option>
      </select>
    </div>

    <!-- Tabla -->
    <div class="table-card">
      <div v-if="loading" class="table-loading"><i class="bi bi-arrow-repeat spin"></i> Cargando…</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Código</th>
            <th>Nombre</th>
            <th>Categoría</th>
            <th v-if="tab === 'producto'">Tipo inv.</th>
            <th class="text-right">Precio</th>
            <th v-if="tab === 'producto'" class="text-right">Costo</th>
            <th v-if="tab === 'servicio'" class="text-center">Participantes</th>
            <th class="text-center">Estado</th>
            <th class="text-center">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in filtered" :key="p.id">
            <td class="text-muted">{{ p.id }}</td>
            <td class="text-muted">{{ p.code || '—' }}</td>
            <td>
              <strong>{{ p.name }}</strong>
              <div v-if="p.description" class="sub-text">{{ p.description?.slice(0,60) }}{{ p.description?.length > 60 ? '…' : '' }}</div>
            </td>
            <td class="text-muted">{{ p.category_name || '—' }}</td>
            <td v-if="tab === 'producto'">
              <span class="behavior-badge" :class="'beh-' + p.inventory_behavior">
                {{ behaviorLabel(p.inventory_behavior) }}
              </span>
            </td>
            <td class="text-right">{{ fmtMoney(p.base_price) }}</td>
            <td v-if="tab === 'producto'" class="text-right text-muted">{{ fmtMoney(p.cost_price) }}</td>
            <td v-if="tab === 'servicio'" class="text-center">
              <button class="btn-participants" @click="abrirParticipantes(p)" :title="`Participantes de ${p.name}`">
                <i class="bi bi-people-fill"></i>
                <span v-if="p.num_participantes > 0" class="part-count">{{ p.num_participantes }}</span>
              </button>
            </td>
            <td class="text-center">
              <span class="badge-status" :class="p.is_active ? 'active' : 'inactive'">
                {{ p.is_active ? 'Activo' : 'Inactivo' }}
              </span>
            </td>
            <td class="text-center">
              <div class="action-row">
                <button class="btn btn-sm btn-outline-primary" @click="openEdit(p)" title="Editar"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-sm btn-outline-secondary" @click="toggleActive(p)" :title="p.is_active ? 'Desactivar' : 'Activar'">
                  <i :class="p.is_active ? 'bi bi-toggle-on text-success' : 'bi bi-toggle-off'"></i>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="filtered.length === 0">
            <td :colspan="tab === 'servicio' ? 8 : 9" class="text-center text-muted py-4">
              No hay {{ tab === 'servicio' ? 'servicios' : 'productos' }} registrados
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ══ MODAL CREAR/EDITAR ══ -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-box modal-lg">
        <div class="mh">
          <h3>
            <i :class="tab === 'servicio' ? 'bi bi-tools' : 'bi bi-box-seam-fill'"></i>
            {{ editing ? 'Editar' : 'Nuevo' }} {{ tab === 'servicio' ? 'Servicio' : 'Producto' }}
          </h3>
          <button class="btn-x" @click="showModal = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="mb-area">
          <div class="form-row2">
            <div class="fg">
              <label>Código / Referencia</label>
              <input v-model="form.code" class="form-control" placeholder="SKU-001" />
            </div>
            <div class="fg">
              <label>Nombre *</label>
              <input v-model="form.name" class="form-control" :placeholder="tab === 'servicio' ? 'Ej: Lavado sencillo' : 'Ej: Correa distribución'" />
            </div>
          </div>
          <div class="fg">
            <label>Descripción</label>
            <textarea v-model="form.description" class="form-control" rows="2" placeholder="Descripción opcional…"></textarea>
          </div>
          <div class="form-row2">
            <div class="fg">
              <label>Categoría</label>
              <select v-model="form.category_id" class="form-select">
                <option :value="null">— Sin categoría —</option>
                <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            <!-- Solo productos tienen control de inventario -->
            <div v-if="tab === 'producto'" class="fg">
              <label>Tipo de inventario *</label>
              <select v-model="form.inventory_behavior" class="form-select">
                <option value="decrement">Inventario simple (descuenta al vender)</option>
                <option value="recipe">Receta (descarga insumos)</option>
                <option value="presentation">Presentaciones (unidad/caja/blister)</option>
                <option value="serialized">Serializado (IMEI / serie única)</option>
                <option value="weight">Por peso (balanza)</option>
              </select>
            </div>
            <div v-else class="fg">
              <label>Tipo de servicio</label>
              <select v-model="form.service_category" class="form-select">
                <option value="">— General —</option>
                <option value="lavado">Lavado / Estética</option>
                <option value="mecanica">Mecánica</option>
                <option value="latoneria">Latonería y Pintura</option>
                <option value="diagnostico">Diagnóstico</option>
                <option value="otro">Otro</option>
              </select>
            </div>
          </div>

          <div class="section-divider">Precios</div>
          <div :class="tab === 'producto' ? 'form-row3' : 'form-row2'">
            <div class="fg">
              <label>Precio de venta *</label>
              <CurrencyInput v-model="form.base_price" class="form-control" />
            </div>
            <div v-if="tab === 'producto'" class="fg">
              <label>Costo</label>
              <CurrencyInput v-model="form.cost_price" class="form-control" />
            </div>
            <div class="fg">
              <label>% Impuesto</label>
              <input v-model.number="form.tax_rate" type="number" min="0" max="100" step="0.01" class="form-control" placeholder="0" />
            </div>
          </div>

          <div v-if="tab === 'producto'" class="fg">
            <label>Stock mínimo (para alertas)</label>
            <input v-model.number="form.min_stock" type="number" min="0" step="0.001" class="form-control" />
          </div>

          <div class="section-divider">Opciones en POS</div>
          <div class="toggles-row">
            <label class="toggle-label">
              <input type="checkbox" v-model="form.ask_price" :true-value="1" :false-value="0" />
              <span>Pedir precio al vender</span>
            </label>
            <label class="toggle-label">
              <input type="checkbox" v-model="form.ask_description" :true-value="1" :false-value="0" />
              <span>Pedir descripción al vender</span>
            </label>
          </div>

          <div v-if="tab === 'producto' && form.base_price > 0 && form.cost_price > 0" class="utilidad-preview">
            <span>Utilidad: <strong>{{ fmtMoney(form.base_price - form.cost_price) }}</strong></span>
            <span class="util-pct" :class="utilPct >= 30 ? 'good' : utilPct >= 10 ? 'mid' : 'low'">
              {{ utilPct.toFixed(1) }}%
            </span>
          </div>

          <!-- Aviso servicios: agregar participantes después de guardar -->
          <div v-if="tab === 'servicio' && !editing" class="info-hint">
            <i class="bi bi-info-circle-fill"></i>
            Después de guardar, usa el botón <strong><i class="bi bi-people-fill"></i></strong> en la tabla para configurar quién participa en este servicio y su % de pago.
          </div>
        </div>
        <div class="mf">
          <button class="btn btn-secondary btn-sm" @click="showModal = false">Cancelar</button>
          <button class="btn btn-primary btn-sm" @click="submit" :disabled="saving">
            <i v-if="saving" class="bi bi-arrow-repeat spin"></i>
            {{ saving ? 'Guardando…' : 'Guardar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ══ MODAL PARTICIPANTES ══ -->
    <Teleport to="body">
      <div v-if="showPart" class="modal-overlay" @click.self="showPart = false">
        <div class="modal-box" style="max-width:560px">
          <div class="mh">
            <div>
              <h3><i class="bi bi-people-fill"></i> Participantes del Servicio</h3>
              <p class="mh-sub">{{ partServicio?.name }}</p>
            </div>
            <button class="btn-x" @click="showPart = false"><i class="bi bi-x-lg"></i></button>
          </div>
          <div class="mb-area">
            <!-- Barra de distribución visual -->
            <div class="dist-bar-wrap">
              <div class="dist-bar">
                <div
                  v-for="(p, i) in partData.participantes" :key="p.id"
                  class="dist-seg"
                  :style="{ width: p.pct_pago + '%', background: PART_COLORS[i % PART_COLORS.length] }"
                  :title="`${p.profession_nombre}: ${p.pct_pago}%`"
                ></div>
                <div
                  class="dist-seg negocio"
                  :style="{ width: partData.negocio_pct + '%' }"
                  title="Negocio"
                ></div>
              </div>
              <div class="dist-labels">
                <span v-for="(p, i) in partData.participantes" :key="p.id" class="dl-item">
                  <span class="dl-dot" :style="{ background: PART_COLORS[i % PART_COLORS.length] }"></span>
                  {{ p.rol_display || p.profession_nombre }} <strong>{{ p.pct_pago }}%</strong>
                </span>
                <span class="dl-item">
                  <span class="dl-dot negocio"></span>
                  Negocio <strong>{{ partData.negocio_pct }}%</strong>
                </span>
              </div>
            </div>

            <!-- Lista participantes -->
            <div v-if="loadingPart" class="loading-center">
              <i class="bi bi-hourglass-split spin"></i>
            </div>
            <div v-else class="part-list">
              <div v-for="p in partData.participantes" :key="p.id" class="part-row">
                <div class="pr-info">
                  <span class="pr-prof">{{ p.profession_nombre }}</span>
                  <input v-model="p.rol_display" class="pr-rol-input" placeholder="Etiqueta (ej: Lavador principal)" />
                </div>
                <div class="pr-pct">{{ p.pct_pago }}%</div>
                <button class="pr-del" @click="eliminarParticipante(p)" title="Eliminar">
                  <i class="bi bi-trash3"></i>
                </button>
              </div>
              <div v-if="partData.participantes.length === 0" class="empty-part">
                <i class="bi bi-people"></i>
                <p>Sin participantes. El 100% va al negocio.</p>
              </div>
            </div>

            <!-- Agregar participante -->
            <div class="add-part-form">
              <div class="section-divider">Agregar participante</div>
              <div class="add-part-row">
                <select v-model="newPart.profession_id" class="form-control form-sel">
                  <option :value="null">— Selecciona rol —</option>
                  <option v-for="prof in professions" :key="prof.id" :value="prof.id">{{ prof.name }}</option>
                </select>
                <input v-model="newPart.rol_display" class="form-control" placeholder="Etiqueta (opcional)" style="max-width:170px" />
                <div class="pct-wrap">
                  <input v-model.number="newPart.pct_pago" type="number" min="1" max="100" step="0.5" class="form-control" style="max-width:80px" placeholder="%" />
                  <span class="pct-hint">/ {{ partData.negocio_pct }}% disp.</span>
                </div>
                <button class="btn btn-primary btn-sm" :disabled="!newPart.profession_id || !newPart.pct_pago || savingPart" @click="agregarParticipante">
                  <i v-if="savingPart" class="bi bi-hourglass-split spin"></i>
                  <i v-else class="bi bi-plus-lg"></i>
                </button>
              </div>
            </div>
          </div>
          <div class="mf">
            <button class="btn btn-secondary btn-sm" @click="showPart = false">Cerrar</button>
          </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue"
import api from "@/services/apis"
import { showToast, showConfirm } from "@/utils/toast"
import { useCompanyStore } from "@/stores/companyStore"
import CurrencyInput from "@/components/CurrencyInput.vue"

const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id)

// ── Estado general ─────────────────────────────────────────────────────────
const tab      = ref("servicio")
const products = ref([])
const categories   = ref([])
const professions  = ref([])
const loading      = ref(true)
const search       = ref("")
const filterCat    = ref("")
const filterBehavior = ref("")

// ── Conteos por pestaña ────────────────────────────────────────────────────
const counts = computed(() => ({
  servicio: products.value.filter(p => p.item_type === "servicio").length,
  producto: products.value.filter(p => p.item_type === "producto" || !p.item_type).length,
}))

// ── Filtrado ───────────────────────────────────────────────────────────────
const filtered = computed(() => {
  return products.value.filter(p => {
    const tipoOk  = tab.value === "servicio"
      ? p.item_type === "servicio"
      : (p.item_type === "producto" || !p.item_type)
    const q       = search.value.toLowerCase()
    const matchQ  = !q || p.name.toLowerCase().includes(q) || (p.code || "").toLowerCase().includes(q)
    const matchCat = !filterCat.value || p.category_id === filterCat.value
    const matchBeh = !filterBehavior.value || p.inventory_behavior === filterBehavior.value
    return tipoOk && matchQ && matchCat && matchBeh
  })
})

// ── Carga ──────────────────────────────────────────────────────────────────
async function load() {
  loading.value = true
  try {
    const [pr, cr, pfr] = await Promise.all([
      api.get("/products/"),
      api.get("/product-categories/"),
      api.get("/professions/"),
    ])
    products.value    = pr.data
    categories.value  = cr.data
    professions.value = pfr.data
  } catch { showToast("Error cargando datos", "error") }
  finally { loading.value = false }
}

// ── Modal crear/editar ─────────────────────────────────────────────────────
const showModal = ref(false)
const editing   = ref(null)
const saving    = ref(false)
const form      = ref({})

const BEHAVIOR_LABELS = {
  direct: "Servicio", decrement: "Repuesto", recipe: "Receta",
  presentation: "Presentac.", serialized: "Serializado", weight: "Por peso",
}
function behaviorLabel(b) { return BEHAVIOR_LABELS[b] || b }
function fmtMoney(v) {
  return Number(v || 0).toLocaleString("es-CO", { style: "currency", currency: "COP", minimumFractionDigits: 0 })
}
const utilPct = computed(() => {
  const price = form.value.base_price || 0
  const cost  = form.value.cost_price  || 0
  return price ? ((price - cost) / price) * 100 : 0
})

function openCreate() {
  editing.value = null
  form.value = {
    code: "", name: "", description: "", category_id: null,
    item_type: tab.value,
    inventory_behavior: tab.value === "servicio" ? "direct" : "decrement",
    base_price: 0, cost_price: 0, tax_rate: 0, min_stock: 0,
    ask_price: 0, ask_description: 0, service_category: "",
  }
  showModal.value = true
}
function openEdit(p) {
  editing.value = p
  form.value = { ...p, service_category: p.service_category ?? "" }
  showModal.value = true
}

async function submit() {
  if (!form.value.name?.trim()) { showToast("El nombre es requerido", "warning"); return }
  saving.value = true
  try {
    const payload = { ...form.value, item_type: tab.value }
    if (tab.value === "servicio") payload.inventory_behavior = "direct"
    if (editing.value) {
      const r = await api.put(`/products/${editing.value.id}`, payload)
      const idx = products.value.findIndex(x => x.id === editing.value.id)
      if (idx !== -1) products.value[idx] = r.data
    } else {
      const r = await api.post("/products/", payload)
      products.value.unshift(r.data)
    }
    showModal.value = false
    showToast(tab.value === "servicio" ? "Servicio guardado" : "Producto guardado", "success")
  } catch (e) { showToast(e.response?.data?.detail || "Error", "error") }
  finally { saving.value = false }
}

async function toggleActive(p) {
  try {
    const r = await api.put(`/products/${p.id}`, { is_active: p.is_active ? 0 : 1 })
    const idx = products.value.findIndex(x => x.id === p.id)
    if (idx !== -1) products.value[idx] = r.data
  } catch { showToast("Error actualizando", "error") }
}

// ── Modal Participantes ────────────────────────────────────────────────────
const showPart     = ref(false)
const partServicio = ref(null)
const partData     = ref({ participantes: [], total_asignado: 0, negocio_pct: 100 })
const loadingPart  = ref(false)
const savingPart   = ref(false)
const PART_COLORS  = ["#3b82f6","#f59e0b","#22c55e","#a855f7","#ef4444","#06b6d4"]

const newPart = ref({ profession_id: null, rol_display: "", pct_pago: 0 })

async function abrirParticipantes(p) {
  partServicio.value = p
  showPart.value     = true
  await cargarParticipantes()
}

async function cargarParticipantes() {
  if (!partServicio.value || !companyId.value) return
  loadingPart.value = true
  try {
    const { data } = await api.get(`/api/talleres/servicios/${partServicio.value.id}/participantes`, {
      params: { company_id: companyId.value }
    })
    partData.value = data
  } catch { partData.value = { participantes: [], total_asignado: 0, negocio_pct: 100 } }
  finally { loadingPart.value = false }
}

async function agregarParticipante() {
  if (!newPart.value.profession_id || !newPart.value.pct_pago) return
  savingPart.value = true
  try {
    await api.post(`/api/talleres/servicios/${partServicio.value.id}/participantes`, {
      company_id:   companyId.value,
      profession_id: newPart.value.profession_id,
      rol_display:  newPart.value.rol_display || null,
      pct_pago:     newPart.value.pct_pago,
    })
    newPart.value = { profession_id: null, rol_display: "", pct_pago: 0 }
    await cargarParticipantes()
    // Actualizar counter en tabla
    const idx = products.value.findIndex(x => x.id === partServicio.value.id)
    if (idx >= 0) products.value[idx].num_participantes = partData.value.participantes.length
  } catch (e) {
    showToast(e?.response?.data?.detail ?? "Error al agregar", "error")
  } finally { savingPart.value = false }
}

async function eliminarParticipante(p) {
  if (!(await showConfirm(`¿Eliminar participante "${p.profession_nombre}"?`))) return
  try {
    await api.delete(`/api/talleres/servicios/participantes/${p.id}`, {
      params: { company_id: companyId.value }
    })
    await cargarParticipantes()
  } catch { showToast("Error al eliminar", "error") }
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1200px; }

/* Tabs */
.tabs-bar { display: flex; gap: 4px; margin-bottom: 20px; border-bottom: 2px solid #e2e8f0; }
.tab-btn {
  display: flex; align-items: center; gap: 7px;
  padding: 10px 20px; font-size: 13px; font-weight: 700;
  background: none; border: none; cursor: pointer;
  color: #64748b; border-bottom: 3px solid transparent; margin-bottom: -2px;
  transition: all .15s;
}
.tab-btn:hover { color: #1e3a5f; background: #f8fafc; border-radius: 8px 8px 0 0; }
.tab-btn.active { color: #1e3a5f; border-bottom-color: #1e3a5f; }
.tab-count {
  background: #e2e8f0; color: #64748b; border-radius: 20px;
  font-size: 11px; padding: 1px 7px; font-weight: 700;
}
.tab-btn.active .tab-count { background: #1e3a5f; color: #fff; }

.page-header    { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; gap: 12px; flex-wrap: wrap; }
.page-title     { font-size: 20px; font-weight: 700; color: #1e293b; margin: 0 0 4px; display: flex; align-items: center; gap: 8px; }
.page-subtitle  { font-size: 13px; color: #64748b; margin: 0; }
.filters-row    { display: flex; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
.table-card     { background: #fff; border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,.08); overflow: hidden; }
.table-loading  { padding: 40px; text-align: center; color: #94a3b8; }
.data-table     { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th  { background: #f8fafc; color: #475569; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: .4px; padding: 11px 12px; border-bottom: 1px solid #e2e8f0; }
.data-table td  { padding: 11px 12px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: #f8fafc; }
.text-center { text-align: center; }
.text-right  { text-align: right; }
.text-muted  { color: #94a3b8; font-size: 12px; }
.sub-text    { font-size: 11px; color: #94a3b8; margin-top: 2px; }
.py-4        { padding: 32px 0; }

.behavior-badge { font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 20px; white-space: nowrap; }
.beh-direct     { background: #eff6ff; color: #1d4ed8; }
.beh-decrement  { background: #fef3c7; color: #92400e; }
.beh-recipe     { background: #fef9c3; color: #854d0e; }
.beh-presentation { background: #dbeafe; color: #1e40af; }
.beh-serialized { background: #f3e8ff; color: #7e22ce; }
.beh-weight     { background: #dcfce7; color: #166534; }

.badge-status { font-size: 10px; font-weight: 700; padding: 2px 9px; border-radius: 20px; }
.badge-status.active   { background: #dcfce7; color: #16a34a; }
.badge-status.inactive { background: #f1f5f9; color: #94a3b8; }
.action-row  { display: flex; gap: 4px; justify-content: center; }

/* Participantes btn */
.btn-participants {
  position: relative; background: #eff6ff; border: 1.5px solid #bfdbfe;
  border-radius: 8px; width: 36px; height: 28px; cursor: pointer; color: #1d4ed8;
  font-size: 14px; display: inline-flex; align-items: center; justify-content: center;
}
.btn-participants:hover { background: #dbeafe; }
.part-count {
  position: absolute; top: -6px; right: -6px; background: #1e3a5f; color: #fff;
  border-radius: 10px; font-size: 10px; font-weight: 700; padding: 0 4px; min-width: 16px; text-align: center;
}

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 2000; padding: 16px; }
.modal-box     { background: #fff; border-radius: 16px; width: 100%; max-width: 540px; max-height: 90vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,.2); }
.modal-lg      { max-width: 620px; }
.mh  { display: flex; align-items: flex-start; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid #f1f5f9; gap: 12px; }
.mh h3 { font-size: 15px; font-weight: 700; color: #1e293b; margin: 0; display: flex; align-items: center; gap: 7px; }
.mh-sub { font-size: 12px; color: #64748b; margin: 3px 0 0; }
.btn-x { background: none; border: none; font-size: 16px; cursor: pointer; color: #94a3b8; flex-shrink: 0; }
.mb-area { padding: 18px 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; }
.mf { padding: 12px 20px 16px; display: flex; justify-content: flex-end; gap: 8px; border-top: 1px solid #f1f5f9; }
.fg       { display: flex; flex-direction: column; gap: 4px; }
.fg label { font-size: 13px; font-weight: 600; color: #374151; }
.form-row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-row3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
.section-divider { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .5px; color: #94a3b8; border-bottom: 1px solid #f1f5f9; padding-bottom: 4px; }
.toggles-row { display: flex; gap: 20px; flex-wrap: wrap; }
.toggle-label { display: flex; align-items: center; gap: 8px; cursor: pointer; font-size: 13px; color: #374151; }
.toggle-label input[type=checkbox] { width: 16px; height: 16px; cursor: pointer; }
.utilidad-preview { background: #f8fafc; border-radius: 8px; padding: 10px 16px; display: flex; align-items: center; gap: 16px; font-size: 13px; color: #475569; }
.util-pct { font-weight: 700; font-size: 14px; }
.util-pct.good { color: #16a34a; } .util-pct.mid { color: #b45309; } .util-pct.low { color: #dc2626; }
.info-hint { display: flex; align-items: flex-start; gap: 8px; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 10px 14px; font-size: 13px; color: #1d4ed8; }
.info-hint .bi { color: #3b82f6; flex-shrink: 0; margin-top: 2px; }
.form-sel { appearance: none; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%2364748b' stroke-width='1.5' fill='none'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 12px center; padding-right: 32px; }

/* Participantes */
.dist-bar-wrap { background: #f8fafc; border-radius: 10px; padding: 12px; }
.dist-bar { height: 12px; border-radius: 6px; overflow: hidden; display: flex; background: #e2e8f0; margin-bottom: 10px; }
.dist-seg { transition: width .3s; }
.dist-seg.negocio { background: #94a3b8; }
.dist-labels { display: flex; flex-wrap: wrap; gap: 10px; }
.dl-item { display: flex; align-items: center; gap: 5px; font-size: 12px; color: #475569; }
.dl-dot { width: 10px; height: 10px; border-radius: 3px; display: inline-block; }
.dl-dot.negocio { background: #94a3b8; }

.part-list { display: flex; flex-direction: column; gap: 6px; }
.part-row {
  display: flex; align-items: center; gap: 8px;
  background: #f8fafc; border-radius: 8px; padding: 8px 10px;
}
.pr-info { flex: 1; display: flex; flex-direction: column; gap: 3px; }
.pr-prof { font-size: 13px; font-weight: 700; color: #1e3a5f; }
.pr-rol-input {
  border: 1px solid #e2e8f0; border-radius: 6px; padding: 3px 7px;
  font-size: 11px; color: #64748b; background: #fff; outline: none;
}
.pr-pct  { font-size: 16px; font-weight: 800; color: #1e3a5f; white-space: nowrap; min-width: 45px; text-align: right; }
.pr-del  { background: #fee2e2; border: none; border-radius: 6px; width: 28px; height: 28px; cursor: pointer; color: #dc2626; font-size: 12px; display: flex; align-items: center; justify-content: center; }
.pr-del:hover { background: #fecaca; }
.empty-part { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 24px; color: #94a3b8; text-align: center; }
.empty-part .bi { font-size: 28px; color: #cbd5e1; }
.empty-part p { font-size: 13px; margin: 0; }

.add-part-form { margin-top: 4px; }
.add-part-row  { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
.pct-wrap { display: flex; align-items: center; gap: 4px; }
.pct-hint { font-size: 11px; color: #94a3b8; white-space: nowrap; }

.loading-center { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 24px; color: #94a3b8; }

.text-success { color: #16a34a; }
.btn { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; transition: all .15s; }
.btn-primary   { background: #3b82f6; color: #fff; } .btn-primary:hover { background: #2563eb; }
.btn-primary:disabled { opacity: .6; cursor: not-allowed; }
.btn-secondary { border: 1.5px solid #e2e8f0; background: #fff; color: #64748b; }
.btn-sm { padding: 6px 12px; font-size: 12px; }
.btn-outline-primary   { background: #eff6ff; color: #1d4ed8; border: 1.5px solid #bfdbfe; }
.btn-outline-secondary { background: #f8fafc; color: #475569; border: 1.5px solid #e2e8f0; }
.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

@media (max-width: 768px) {
  .tabs-bar { gap: 2px; }
  .tab-btn  { padding: 8px 12px; font-size: 12px; }
}
@media (max-width: 640px) {
  .form-row2, .form-row3 { grid-template-columns: 1fr; }
  .add-part-row { flex-direction: column; align-items: stretch; }
}
</style>
