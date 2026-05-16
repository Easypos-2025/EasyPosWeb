<template>
  <div class="crud-view">
    <div class="crud-header">
      <div>
        <h5 class="crud-titulo">Lista de Precios General</h5>
        <p class="crud-sub">
          Precio de cada {{ moduleName || 'artículo' }} en la lista general.
          Se agrega automáticamente al crear un {{ moduleName || 'artículo' }}.
        </p>
      </div>
      <div class="header-tools">
        <input v-model="busqueda" class="inp-buscar" :placeholder="`Buscar ${moduleName || 'artículo'}…`" />
      </div>
    </div>

    <div v-if="loading" class="estado-carga"><div class="spinner-border spinner-border-sm text-primary"></div></div>
    <div v-else-if="!filtrados.length" class="estado-vacio">
      <i class="bi bi-currency-dollar"></i>
      <p>No hay {{ moduleName || 'artículos' }} en la lista de precios. Crea uno primero.</p>
    </div>
    <table v-else class="tabla">
      <thead>
        <tr>
          <th>{{ moduleName || 'Artículo' }}</th>
          <th>Categoría</th>
          <th>Presentación</th>
          <th class="th-precio">Precio</th>
          <th>Estado</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in filtrados" :key="item.id" :class="{ 'tr-inactiva': !item.activa }">
          <td class="td-item">
            <i class="bi bi-box-seam me-2 text-primary"></i>
            {{ item.item_name || `#${item.id_producto}` }}
          </td>
          <td>
            <span v-if="item.category_name" class="badge-cat">{{ item.category_name }}</span>
            <span v-else class="text-muted">—</span>
          </td>
          <td class="text-muted">{{ item.presentation_name || '—' }}</td>
          <td class="td-precio">
            <span v-if="editando !== item.id">{{ fmt(item.precio_producto) }}</span>
            <input v-else v-model.number="precioEdit" class="inp-precio" type="number"
              @keyup.enter="guardarPrecio(item)" @blur="guardarPrecio(item)" />
          </td>
          <td>
            <button class="badge-estado" :class="item.activa ? 'badge-activa' : 'badge-inactiva'"
              @click="toggleActiva(item)">
              {{ item.activa ? 'Activa' : 'Inactiva' }}
            </button>
          </td>
          <td>
            <button class="btn-icono" title="Editar precio" @click="iniciarEdicion(item)">
              <i class="bi bi-pencil"></i>
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/apis.js'
import { showToast } from '@/utils/toast.js'
import { useModuleName } from '@/composables/useModuleName.js'

const BASE = '/api/pos-catalogo/lista-precios'

// Nombre dinámico del módulo de artículos (lo que el admin haya configurado en system_modules)
const { moduleName } = useModuleName('/pos/platos')

const items     = ref([])
const loading   = ref(true)
const busqueda  = ref('')
const editando  = ref(null)
const precioEdit= ref(0)

const fmtCOP = new Intl.NumberFormat('es-CO', { style:'currency', currency:'COP', minimumFractionDigits:0, maximumFractionDigits:0 })
const fmt = v => fmtCOP.format(v || 0)

const filtrados = computed(() => {
  if (!busqueda.value) return items.value
  const q = busqueda.value.toLowerCase()
  return items.value.filter(i =>
    (i.item_name     || '').toLowerCase().includes(q) ||
    (i.category_name || '').toLowerCase().includes(q)
  )
})

onMounted(cargar)
async function cargar() {
  loading.value = true
  try { const{data} = await api.get(BASE); items.value = data } catch { items.value = [] }
  finally { loading.value = false }
}

function iniciarEdicion(item) {
  editando.value = item.id
  precioEdit.value = item.precio_producto
}

async function guardarPrecio(item) {
  if (editando.value !== item.id) return
  editando.value = null
  if (precioEdit.value === item.precio_producto) return
  try {
    await api.put(`${BASE}/${item.id}`, {
      precio_producto: precioEdit.value,
      id_presentacion: item.id_presentacion,
      activa: item.activa,
    })
    item.precio_producto = precioEdit.value
    showToast('Precio actualizado', 'success')
  } catch { showToast('Error al actualizar precio', 'error') }
}

async function toggleActiva(item) {
  try {
    await api.patch(`${BASE}/${item.id}/toggle`)
    item.activa = item.activa ? 0 : 1
  } catch { showToast('Error', 'error') }
}
</script>

<style scoped>
.crud-view { padding:0; }
.crud-header { display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px;gap:12px; }
.crud-titulo { font-weight:700;font-size:16px;color:#1e3a5f;margin:0; }
.crud-sub    { font-size:13px;color:#64748b;margin:2px 0 0;max-width:500px; }
.header-tools{ display:flex;align-items:center;gap:10px;flex-shrink:0; }
.inp-buscar  { border:1.5px solid #cbd5e1;border-radius:8px;padding:8px 12px;font-size:13px;color:#1e3a5f;outline:none;width:200px; }
.inp-buscar:focus { border-color:#1d4ed8; }
.estado-carga,.estado-vacio { display:flex;flex-direction:column;align-items:center;gap:10px;padding:60px 20px;color:#94a3b8;font-size:14px; }
.estado-vacio i { font-size:40px; }
.tabla  { width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.06); }
.tabla th { background:#f8fafc;padding:10px 14px;font-size:12px;font-weight:700;color:#64748b;text-align:left;text-transform:uppercase;letter-spacing:.4px; }
.tabla td { padding:11px 14px;font-size:13px;color:#1e3a5f;border-top:1px solid #f1f5f9;vertical-align:middle; }
.tr-inactiva { opacity:.5; }
.th-precio,.td-precio { text-align:right; }
.td-precio { font-size:15px;font-weight:700;color:#1e3a5f; }
.td-item   { font-weight:600; }
.badge-cat  { background:#eff6ff;color:#1d4ed8;font-size:11px;padding:2px 8px;border-radius:10px;font-weight:600; }
.badge-estado { border:none;border-radius:10px;font-size:11px;padding:3px 10px;font-weight:700;cursor:pointer;transition:.15s; }
.badge-activa  { background:#dcfce7;color:#16a34a; }
.badge-inactiva{ background:#f1f5f9;color:#94a3b8; }
.inp-precio { border:2px solid #1d4ed8;border-radius:6px;padding:4px 8px;font-size:14px;font-weight:700;color:#1e3a5f;text-align:right;width:110px;outline:none; }
.btn-icono { background:none;border:1px solid #e2e8f0;border-radius:6px;padding:5px 8px;cursor:pointer;color:#475569;font-size:13px; }
.btn-icono:hover { background:#f0f4ff;color:#1d4ed8;border-color:#1d4ed8; }
.text-muted { color:#94a3b8;font-size:12px; }
@media(max-width:768px){.crud-header{flex-direction:column;}.inp-buscar{width:100%;}}
</style>
