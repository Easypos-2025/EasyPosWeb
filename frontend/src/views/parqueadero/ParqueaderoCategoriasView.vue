<template>
  <div class="pq-view">
    <div class="pq-header">
      <h2 class="pq-title"><i class="bi bi-tags-fill"></i> {{ moduleName }}</h2>
      <button class="btn-pq-primary" @click="abrirModal()">
        <i class="bi bi-plus-lg"></i> Nueva Categoría
      </button>
    </div>

    <div v-if="loading" class="pq-loader">Cargando...</div>
    <div v-else-if="!categorias.length" class="pq-empty">
      <i class="bi bi-tags" style="font-size:2.5rem;opacity:.3"></i>
      <p>No hay categorías registradas</p>
    </div>

    <div v-else class="pq-grid">
      <div v-for="cat in categorias" :key="cat.id" class="pq-card-cat"
           :style="{ borderLeftColor: cat.color }">
        <div class="pq-cat-icon" :style="{ background: cat.color + '22', color: cat.color }">
          <i :class="`bi ${cat.icono}`"></i>
        </div>
        <div class="pq-cat-info">
          <span class="pq-cat-nombre">{{ cat.nombre }}</span>
          <span class="pq-cat-badge" :class="cat.is_active ? 'badge-activo' : 'badge-inactivo'">
            {{ cat.is_active ? 'Activa' : 'Inactiva' }}
          </span>
        </div>
        <div class="pq-cat-actions">
          <button class="btn-icon" title="Editar" @click="abrirModal(cat)">
            <i class="bi bi-pencil-fill"></i>
          </button>
          <button class="btn-icon btn-danger" title="Eliminar" @click="eliminar(cat)">
            <i class="bi bi-trash3-fill"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- Confirm eliminar -->
    <div v-if="confirmEliminar" class="pq-overlay" @click.self="confirmEliminar = null">
      <div class="pq-modal" style="max-width:340px">
        <div class="pq-modal-head">
          <h3>Eliminar categoría</h3>
          <button class="btn-close" @click="confirmEliminar = null"><i class="bi bi-x-lg"></i></button>
        </div>
        <div style="padding:20px;font-size:14px;line-height:1.5">
          ¿Eliminar la categoría <strong>"{{ confirmEliminar.nombre }}"</strong>? Esta acción no se puede deshacer.
        </div>
        <div class="pq-modal-foot">
          <button class="btn-pq-ghost" @click="confirmEliminar = null">Cancelar</button>
          <button class="btn-pq-primary" style="background:#dc2626" @click="ejecutarEliminar">
            <i class="bi bi-trash3-fill"></i> Eliminar
          </button>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="modal" class="pq-overlay" @click.self="modal = false">
      <div class="pq-modal">
        <div class="pq-modal-head">
          <h3>{{ form.id ? 'Editar' : 'Nueva' }} Categoría</h3>
          <button class="btn-close" @click="modal = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="pq-modal-body">
          <label>Nombre *</label>
          <input v-model="form.nombre" class="pq-input" placeholder="Ej: Autos, Motos" />

          <label>Ícono Bootstrap</label>
          <input v-model="form.icono" class="pq-input" placeholder="bi-car-front-fill" />
          <span class="pq-icon-preview"><i :class="`bi ${form.icono}`"></i> Vista previa</span>

          <label>Color</label>
          <div class="pq-color-row">
            <input type="color" v-model="form.color" class="pq-color-input" />
            <input v-model="form.color" class="pq-input pq-input-sm" placeholder="#3b82f6" />
          </div>

          <label>Orden</label>
          <input type="number" v-model.number="form.orden" class="pq-input" min="0" />

          <label class="pq-check-label">
            <input type="checkbox" v-model="form.is_active" :true-value="1" :false-value="0" />
            Activa
          </label>
        </div>
        <div class="pq-modal-foot">
          <button class="btn-pq-ghost" @click="modal = false">Cancelar</button>
          <button class="btn-pq-primary" :disabled="saving" @click="guardar">
            <i class="bi" :class="saving ? 'bi-hourglass-split' : 'bi-check2'"></i>
            {{ saving ? 'Guardando...' : 'Guardar' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useCompanyStore } from '@/stores/companyStore'
import { useModuleName } from '@/composables/useModuleName'
import { showToast } from '@/utils/toast'
import api from '@/services/apis'

const companyStore = useCompanyStore()
const { moduleName } = useModuleName()

const categorias = ref([])
const loading = ref(true)
const modal = ref(false)
const saving = ref(false)
const confirmEliminar = ref(null)

const formBase = () => ({ id: null, nombre: '', icono: 'bi-car-front-fill', color: '#3b82f6', orden: 0, is_active: 1 })
const form = ref(formBase())

const cid = () => companyStore.selectedCompany?.id

async function cargar() {
  loading.value = true
  try {
    const { data } = await api.get('/api/parqueadero/categorias', { params: { company_id: cid() } })
    categorias.value = data
  } catch { showToast('Error al cargar categorías', 'error') }
  finally { loading.value = false }
}

function abrirModal(cat = null) {
  form.value = cat
    ? { id: cat.id, nombre: cat.nombre, icono: cat.icono, color: cat.color, orden: cat.orden, is_active: cat.is_active }
    : formBase()
  modal.value = true
}

async function guardar() {
  if (!form.value.nombre.trim()) return showToast('El nombre es obligatorio', 'warn')
  saving.value = true
  try {
    const payload = { nombre: form.value.nombre, icono: form.value.icono,
                      color: form.value.color, orden: form.value.orden, is_active: form.value.is_active }
    if (form.value.id) {
      await api.put(`/parqueadero/categorias/${form.value.id}`, payload, { params: { company_id: cid() } })
    } else {
      await api.post('/api/parqueadero/categorias', payload, { params: { company_id: cid() } })
    }
    showToast('Guardado correctamente', 'success')
    modal.value = false
    cargar()
  } catch { showToast('Error al guardar', 'error') }
  finally { saving.value = false }
}

function eliminar(cat) {
  confirmEliminar.value = cat
}

async function ejecutarEliminar() {
  const cat = confirmEliminar.value
  if (!cat) return
  confirmEliminar.value = null
  try {
    await api.delete(`/parqueadero/categorias/${cat.id}`, { params: { company_id: cid() } })
    showToast('Categoría eliminada', 'success')
    cargar()
  } catch { showToast('Error al eliminar', 'error') }
}

onMounted(cargar)
</script>

<style scoped>
.pq-view { padding: 16px; }
.pq-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; gap: 12px; flex-wrap: wrap; }
.pq-title { font-size: 20px; font-weight: 700; margin: 0; display: flex; align-items: center; gap: 8px; }
.pq-loader, .pq-empty { text-align: center; padding: 60px 20px; opacity: .5; }
.pq-empty i { display: block; margin-bottom: 12px; }

.pq-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; }
.pq-card-cat {
  background: var(--card-bg, #fff);
  border-left: 4px solid #3b82f6;
  border-radius: 10px;
  padding: 16px;
  display: flex; align-items: center; gap: 14px;
  box-shadow: 0 1px 6px rgba(0,0,0,.07);
}
.pq-cat-icon { width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
.pq-cat-info { flex: 1; min-width: 0; }
.pq-cat-nombre { display: block; font-weight: 600; font-size: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.pq-cat-badge { display: inline-block; margin-top: 4px; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 20px; }
.badge-activo { background: #d1fae5; color: #065f46; }
.badge-inactivo { background: #fee2e2; color: #991b1b; }
.pq-cat-actions { display: flex; gap: 6px; }

/* Buttons */
.btn-pq-primary { background: #3b82f6; color: #fff; border: none; border-radius: 8px; padding: 8px 18px; font-size: 14px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; }
.btn-pq-primary:hover { background: #2563eb; }
.btn-pq-primary:disabled { opacity: .6; cursor: not-allowed; }
.btn-pq-ghost { background: transparent; border: 1.5px solid #94a3b8; color: inherit; border-radius: 8px; padding: 8px 18px; font-size: 14px; cursor: pointer; }
.btn-icon { background: none; border: none; cursor: pointer; padding: 6px; border-radius: 6px; font-size: 16px; color: #64748b; }
.btn-icon:hover { background: #f1f5f9; }
.btn-danger { color: #dc2626; }

/* Modal */
.pq-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 16px; }
.pq-modal { background: var(--modal-bg, #fff); border-radius: 14px; width: 100%; max-width: 420px; overflow: hidden; }
.pq-modal-head { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--border, #e2e8f0); }
.pq-modal-head h3 { margin: 0; font-size: 17px; }
.btn-close { background: none; border: none; cursor: pointer; font-size: 18px; color: #64748b; }
.pq-modal-body { padding: 20px; display: flex; flex-direction: column; gap: 10px; }
.pq-modal-body label { font-size: 13px; font-weight: 600; color: #475569; }
.pq-modal-foot { display: flex; gap: 10px; justify-content: flex-end; padding: 14px 20px; border-top: 1px solid var(--border, #e2e8f0); }
.pq-input { width: 100%; padding: 8px 12px; border: 1.5px solid var(--border, #e2e8f0); border-radius: 8px; font-size: 14px; background: var(--input-bg, #f8fafc); box-sizing: border-box; }
.pq-input:focus { outline: none; border-color: #3b82f6; }
.pq-input-sm { flex: 1; }
.pq-color-row { display: flex; align-items: center; gap: 10px; }
.pq-color-input { width: 44px; height: 36px; border: none; border-radius: 8px; cursor: pointer; padding: 2px; }
.pq-icon-preview { font-size: 13px; color: #64748b; }
.pq-check-label { display: flex; align-items: center; gap: 8px; font-size: 14px; cursor: pointer; }

@media (max-width: 768px) {
  .pq-grid { grid-template-columns: 1fr; }
  .pq-header { flex-direction: column; align-items: flex-start; }
}
@media (max-width: 576px) {
  .pq-view { padding: 10px; }
  .pq-modal { border-radius: 0; max-width: 100%; min-height: 100dvh; }
}
</style>
