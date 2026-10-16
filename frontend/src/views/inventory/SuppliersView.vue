<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1 class="page-title"><i class="bi bi-truck me-2"></i>{{ moduleName }}</h1>
        <p class="page-subtitle">Empresas o personas que suministran insumos y productos</p>
      </div>
      <button v-if="!administradoPor" class="btn btn-primary" @click="openCreate"><i class="bi bi-plus-lg"></i> Nuevo</button>
    </div>
    <AvisoBodega :bodega="administradoPor" que="los proveedores" />

    <div class="filters-row">
      <input v-model="search" class="form-control f-search" placeholder="Buscar por nombre, NIT o celular..." />
    </div>

    <!-- Tabla (tablet / PC) -->
    <div class="table-card only-desktop">
      <div v-if="loading" class="table-loading"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Nombre</th>
            <th>NIT</th>
            <th>Celular</th>
            <th>Teléfono fijo</th>
            <th>Email</th>
            <th class="text-center">Estado</th>
            <th class="text-center">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in filtered" :key="s.id" :class="{ 'row-off': !s.is_active }">
            <td class="text-muted">{{ s.id_proveedor ?? s.id }}</td>
            <td><strong>{{ s.name }}</strong></td>
            <td class="text-muted">{{ s.nit || '—' }}</td>
            <td>{{ s.telefono_celular || '—' }}</td>
            <td>{{ s.phone || '—' }}</td>
            <td>{{ s.email || '—' }}</td>
            <td class="text-center">
              <span class="badge-status" :class="s.is_active ? 'active' : 'inactive'">
                {{ s.is_active ? 'Activo' : 'Inactivo' }}
              </span>
            </td>
            <td class="text-center">
              <div v-if="!administradoPor" class="action-row">
                <button class="btn btn-sm btn-outline-primary" @click="openEdit(s)" title="Editar"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-sm btn-outline-warning" @click="toggleActive(s)" :title="s.is_active ? 'Desactivar' : 'Activar'">
                  <i :class="s.is_active ? 'bi bi-toggle-on' : 'bi bi-toggle-off'"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" @click="pedirEliminar(s)" title="Eliminar"><i class="bi bi-trash3"></i></button>
              </div>
            </td>
          </tr>
          <tr v-if="filtered.length === 0">
            <td colspan="8" class="text-center text-muted py-4">No hay registros</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Tarjetas (móvil) -->
    <div class="cards only-mobile">
      <div v-if="loading" class="table-loading"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
      <template v-else>
        <div v-for="s in filtered" :key="s.id" class="s-card" :class="{ 'row-off': !s.is_active }">
          <div class="s-card-top">
            <strong>{{ s.name }}</strong>
            <span class="badge-status" :class="s.is_active ? 'active' : 'inactive'">{{ s.is_active ? 'Activo' : 'Inactivo' }}</span>
          </div>
          <div class="s-card-meta">
            <span>NIT {{ s.nit || '—' }}</span>
            <span><i class="bi bi-phone"></i> {{ s.telefono_celular || '—' }}</span>
            <span v-if="s.email">{{ s.email }}</span>
          </div>
          <div v-if="!administradoPor" class="action-row s-card-acc">
            <button class="btn btn-sm btn-outline-primary" @click="openEdit(s)"><i class="bi bi-pencil"></i></button>
            <button class="btn btn-sm btn-outline-warning" @click="toggleActive(s)"><i :class="s.is_active ? 'bi bi-toggle-on' : 'bi bi-toggle-off'"></i></button>
            <button class="btn btn-sm btn-outline-danger" @click="pedirEliminar(s)"><i class="bi bi-trash3"></i></button>
          </div>
        </div>
        <div v-if="filtered.length === 0" class="text-center text-muted py-4">No hay registros</div>
      </template>
    </div>

    <!-- MODAL CREAR / EDITAR -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-box">
        <div class="mh">
          <h3><i class="bi bi-truck me-2"></i>{{ editing ? `Editar — ${editing.name}` : `Nuevo — ${moduleName}` }}</h3>
          <button class="btn-x" @click="showModal = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="mb-area">
          <ProveedorCampos v-model="form" />
        </div>
        <div class="mf">
          <button class="btn btn-secondary btn-sm" @click="showModal = false">Cancelar</button>
          <button class="btn btn-primary btn-sm" @click="submit" :disabled="saving">
            <i v-if="saving" class="bi bi-arrow-repeat spin"></i>
            {{ saving ? 'Guardando...' : 'Guardar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL ELIMINAR -->
    <div v-if="del.show" class="modal-overlay" @click.self="del.show = false">
      <div class="modal-box modal-sm">
        <div class="mh">
          <h3><i class="bi bi-trash3 me-2"></i>Eliminar proveedor</h3>
          <button class="btn-x" @click="del.show = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="mb-area">
          <div v-if="del.loading" class="table-loading"><i class="bi bi-arrow-repeat spin"></i> Revisando dónde se usa...</div>
          <template v-else-if="del.uso?.con_escritorio">
            <p class="m-0">Esta empresa trabaja con el programa de escritorio: los proveedores no se eliminan, solo se desactivan.</p>
          </template>
          <template v-else-if="del.uso?.en_uso">
            <p class="m-0"><strong>{{ del.item.name }}</strong> está en uso y no se puede eliminar. Quítelo o cambie de proveedor en:</p>
            <div v-if="del.uso.insumos.length" class="uso-bloque">
              <div class="uso-ttl">Insumos ({{ del.uso.insumos.length }})</div>
              <ul class="uso-lista"><li v-for="n in del.uso.insumos" :key="n">{{ n }}</li></ul>
            </div>
            <div v-if="del.uso.productos.length" class="uso-bloque">
              <div class="uso-ttl">Productos ({{ del.uso.productos.length }})</div>
              <ul class="uso-lista"><li v-for="n in del.uso.productos" :key="n">{{ n }}</li></ul>
            </div>
            <ul class="uso-conteos">
              <li v-for="c in conteosUso" :key="c.k">{{ c.l }}: <strong>{{ c.n }}</strong></li>
            </ul>
            <p class="text-muted m-0">Si ya no lo usa, puede desactivarlo.</p>
          </template>
          <template v-else>
            <p class="m-0">¿Eliminar definitivamente a <strong>{{ del.item.name }}</strong>? No está en uso en ningún registro.</p>
          </template>
        </div>
        <div class="mf">
          <button class="btn btn-secondary btn-sm" @click="del.show = false">Cerrar</button>
          <button v-if="!del.loading && del.uso && !del.uso.en_uso && !del.uso.con_escritorio"
                  class="btn btn-danger btn-sm" @click="eliminar" :disabled="del.saving">
            {{ del.saving ? 'Eliminando...' : 'Eliminar' }}
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
import { ordenAlfa } from "@/utils/orden"
import { useModuleName } from "@/composables/useModuleName"
import AvisoBodega from "@/components/AvisoBodega.vue"
import ProveedorCampos, { proveedorVacio, validarProveedor } from "@/components/inventory/ProveedorCampos.vue"
import { useAdministradoBodega } from "@/composables/useAdministradoBodega"

const { moduleName } = useModuleName()
const { administradoPor } = useAdministradoBodega()

const suppliers = ref([])
const loading   = ref(true)
const search    = ref("")
const showModal = ref(false)
const editing   = ref(null)
const saving    = ref(false)
const form      = ref(proveedorVacio())
const del       = ref({ show: false, item: null, uso: null, loading: false, saving: false })

const filtered = computed(() => {
  const q = search.value.toLowerCase()
  return ordenAlfa(suppliers.value.filter(s =>
    !q || s.name.toLowerCase().includes(q) || (s.nit || "").toLowerCase().includes(q)
       || (s.telefono_celular || "").includes(q)
  ), "name")
})

const ETIQUETAS = { entradas: "Entradas de inventario", salidas: "Salidas de inventario", facturas: "Facturas de proveedor",
                    lotes: "Lotes de inventario", ordenes: "Órdenes de compra", seriales: "Artículos con serial" }
const conteosUso = computed(() =>
  Object.entries(ETIQUETAS).filter(([k]) => del.value.uso?.[k]).map(([k, l]) => ({ k, l, n: del.value.uso[k] }))
)

async function load() {
  loading.value = true
  try { suppliers.value = (await api.get("/suppliers/")).data }
  catch { showToast("Error cargando proveedores", "error") }
  finally { loading.value = false }
}

function openCreate() {
  editing.value = null
  form.value = proveedorVacio()
  showModal.value = true
}

function openEdit(s) {
  editing.value = s
  form.value = { ...proveedorVacio(), ...Object.fromEntries(Object.keys(proveedorVacio()).map(k => [k, s[k] ?? ""])) }
  showModal.value = true
}

async function submit() {
  const err = validarProveedor(form.value)
  if (err) { showToast(err, "warning"); return }
  saving.value = true
  try {
    if (editing.value) {
      const r = await api.put(`/suppliers/${editing.value.id}`, form.value)
      const idx = suppliers.value.findIndex(s => s.id === editing.value.id)
      if (idx !== -1) suppliers.value[idx] = r.data
    } else {
      const r = await api.post("/suppliers/", form.value)
      suppliers.value.push(r.data)
    }
    showModal.value = false
    showToast("Proveedor guardado", "success")
  } catch (e) { showToast(e.response?.data?.detail || "Error guardando", "error") }
  finally { saving.value = false }
}

async function toggleActive(s) {
  try {
    const r = await api.put(`/suppliers/${s.id}`, { is_active: s.is_active ? 0 : 1 })
    const idx = suppliers.value.findIndex(x => x.id === s.id)
    if (idx !== -1) suppliers.value[idx] = r.data
  } catch (e) { showToast(e.response?.data?.detail || "Error actualizando", "error") }
}

async function pedirEliminar(s) {
  del.value = { show: true, item: s, uso: null, loading: true, saving: false }
  try { del.value.uso = (await api.get(`/suppliers/${s.id}/uso`)).data }
  catch (e) { del.value.show = false; showToast(e.response?.data?.detail || "No se pudo revisar el proveedor", "error") }
  finally { del.value.loading = false }
}

async function eliminar() {
  del.value.saving = true
  try {
    await api.delete(`/suppliers/${del.value.item.id}`)
    suppliers.value = suppliers.value.filter(x => x.id !== del.value.item.id)
    del.value.show = false
    showToast("Proveedor eliminado", "success")
  } catch (e) { showToast(e.response?.data?.detail || "Error eliminando", "error") }
  finally { del.value.saving = false }
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1100px; }
.page-header    { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; gap: 12px; flex-wrap: wrap; }
.page-title     { font-size: 22px; font-weight: 700; color: #1e293b; margin: 0 0 4px; }
.page-subtitle  { font-size: 13px; color: #64748b; margin: 0; }
.filters-row    { display: flex; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
.f-search       { max-width: 300px; }
.table-card     { background: #fff; border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,.08); overflow-x: auto; }
.table-loading  { padding: 40px; text-align: center; color: #94a3b8; }
.data-table     { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th  { background: #f8fafc; color: #475569; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: .4px; padding: 11px 12px; border-bottom: 1px solid #e2e8f0; white-space: nowrap; }
.data-table td  { padding: 11px 12px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: #f8fafc; }
.row-off { opacity: .6; }
.text-center { text-align: center; }
.text-muted  { color: #94a3b8; font-size: 12px; }
.py-4        { padding: 32px 0; }
.m-0 { margin: 0; }
.badge-status { font-size: 10px; font-weight: 700; padding: 2px 9px; border-radius: 20px; }
.badge-status.active   { background: #dcfce7; color: #16a34a; }
.badge-status.inactive { background: #f1f5f9; color: #94a3b8; }
.action-row  { display: flex; gap: 4px; justify-content: center; }

.cards  { display: none; flex-direction: column; gap: 8px; }
.s-card { background: #fff; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.07); padding: 12px 14px; }
.s-card-top  { display: flex; justify-content: space-between; align-items: center; gap: 8px; font-size: 14px; }
.s-card-meta { display: flex; flex-wrap: wrap; gap: 10px; font-size: 12px; color: #64748b; margin: 4px 0 8px; }
.s-card-acc  { justify-content: flex-end; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 2000; padding: 16px; }
.modal-box     { background: #fff; border-radius: 16px; width: 100%; max-width: 560px; max-height: 90vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,.2); }
.modal-sm      { max-width: 440px; }
.mh  { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid #f1f5f9; }
.mh h3 { font-size: 15px; font-weight: 700; color: #1e293b; margin: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.btn-x { background: none; border: none; font-size: 16px; cursor: pointer; color: #94a3b8; }
.mb-area { padding: 18px 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
.mf { padding: 12px 20px 16px; display: flex; justify-content: flex-end; gap: 8px; border-top: 1px solid #f1f5f9; }
.uso-bloque { background: #fff7ed; border-radius: 8px; padding: 8px 12px; }
.uso-ttl    { font-size: 12px; font-weight: 700; color: #9a3412; margin-bottom: 4px; }
.uso-lista  { margin: 0; padding-left: 18px; font-size: 13px; max-height: 160px; overflow-y: auto; }
.uso-conteos { margin: 0; padding-left: 18px; font-size: 13px; }

.btn { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; transition: all .15s; }
.btn-primary   { background: #3b82f6; color: #fff; } .btn-primary:hover { background: #2563eb; }
.btn:disabled  { opacity: .6; cursor: not-allowed; }
.btn-secondary { border: 1.5px solid #e2e8f0; background: #fff; color: #64748b; }
.btn-danger    { background: #dc2626; color: #fff; }
.btn-sm { padding: 6px 12px; font-size: 12px; }
.btn-outline-primary { background: #eff6ff; color: #1d4ed8; border: 1.5px solid #bfdbfe; }
.btn-outline-warning { background: #fffbeb; color: #b45309; border: 1.5px solid #fde68a; }
.btn-outline-danger  { background: #fff5f5; color: #dc2626; border: 1.5px solid #fecaca; }
.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

@media (max-width: 768px) {
  .page-container { padding: 14px; }
  .only-desktop { display: none; }
  .cards.only-mobile { display: flex; }
  .f-search { max-width: none; flex: 1 1 100%; }
  .modal-overlay { padding: 0; align-items: flex-end; }
  .modal-box { max-height: 96vh; border-radius: 16px 16px 0 0; }
}
@media (max-width: 576px) {
  .page-title { font-size: 18px; }
  .mf .btn { flex: 1; justify-content: center; }
}
</style>
