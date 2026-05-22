<template>
  <div class="zonas-container">
    <!-- Header -->
    <div class="page-header">
      <div class="header-left">
        <h5 class="page-title">
          <i class="bi bi-grid-3x3-gap me-2"></i>{{ moduleName }}
        </h5>
        <span class="badge bg-secondary ms-2">{{ items.length }}</span>
      </div>
      <button class="btn btn-primary btn-sm" @click="abrirModal()">
        <i class="bi bi-plus-lg me-1"></i>Nueva {{ moduleName }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status"></div>
    </div>

    <!-- Grid de zonas -->
    <div v-else-if="items.length" class="zonas-grid">
      <div
        v-for="zona in items"
        :key="zona.id"
        class="zona-card"
        :class="{ 'zona-inactiva': !zona.is_active }"
      >
        <div class="zona-color-bar" :style="{ background: zona.color }"></div>
        <div class="zona-body">
          <div class="zona-icon-wrap" :style="{ background: zona.color + '22', color: zona.color }">
            <i :class="`bi ${zona.icon}`"></i>
          </div>
          <div class="zona-info">
            <div class="zona-name">{{ zona.name }}</div>
            <div class="zona-desc" v-if="zona.description">{{ zona.description }}</div>
            <div class="zona-stats">
              <span class="stat free"><i class="bi bi-circle-fill"></i> {{ zona.free_count ?? 0 }} libre</span>
              <span class="stat occupied"><i class="bi bi-circle-fill"></i> {{ zona.occupied_count ?? 0 }} ocup.</span>
              <span class="stat bill"><i class="bi bi-circle-fill"></i> {{ zona.bill_count ?? 0 }} cuenta</span>
            </div>
          </div>
          <div class="zona-actions">
            <span class="badge" :class="zona.is_active ? 'bg-success-subtle text-success' : 'bg-secondary-subtle text-secondary'">
              {{ zona.is_active ? 'Activa' : 'Inactiva' }}
            </span>
            <div class="zona-btn-group mt-2">
              <button class="btn btn-sm btn-outline-primary" @click="abrirModal(zona)" title="Editar">
                <i class="bi bi-pencil"></i>
              </button>
              <button class="btn btn-sm btn-outline-danger" @click="eliminar(zona)" title="Desactivar">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </div>
        </div>
        <div class="zona-footer">
          <small class="text-muted">
            <i class="bi bi-table me-1"></i>{{ zona.table_count ?? 0 }} mesa(s) en total
          </small>
        </div>
      </div>
    </div>

    <!-- Vacío -->
    <div v-else class="empty-state">
      <i class="bi bi-grid-3x3-gap display-4 text-muted"></i>
      <p class="mt-3 text-muted">No hay zonas registradas</p>
      <button class="btn btn-primary" @click="abrirModal()">
        <i class="bi bi-plus-lg me-1"></i>Crear primera zona
      </button>
    </div>

    <!-- Modal crear/editar -->
    <div v-if="modal.visible" class="modal-backdrop-custom" @click.self="cerrarModal">
      <div class="modal-card">
        <div class="modal-card-header" :style="{ borderColor: modal.color }">
          <h6 class="mb-0">
            <i :class="`bi ${modal.icon} me-2`" :style="{ color: modal.color }"></i>
            {{ modal.id ? 'Editar' : 'Nueva' }} {{ moduleName }}
          </h6>
          <button class="btn-close btn-close-sm" @click="cerrarModal"></button>
        </div>
        <div class="modal-card-body">
          <div class="mb-3">
            <label class="form-label">Nombre <span class="text-danger">*</span></label>
            <input v-model="modal.name" class="form-control" :placeholder="`Nombre de la ${moduleName}`" maxlength="100" />
          </div>
          <div class="mb-3">
            <label class="form-label">Descripción</label>
            <input v-model="modal.description" class="form-control" placeholder="Descripción opcional" maxlength="255" />
          </div>
          <div class="row g-3 mb-3">
            <div class="col-6">
              <label class="form-label">Color</label>
              <div class="color-picker-row">
                <input type="color" v-model="modal.color" class="form-control form-control-color" />
                <div class="color-presets">
                  <span v-for="c in colorPresets" :key="c" class="color-dot" :style="{ background: c }"
                        :class="{ active: modal.color === c }" @click="modal.color = c"></span>
                </div>
              </div>
            </div>
            <div class="col-6">
              <label class="form-label">Ícono</label>
              <div class="icon-selector">
                <span v-for="ic in iconOptions" :key="ic" class="icon-opt" :class="{ active: modal.icon === ic }"
                      :style="modal.icon === ic ? { background: modal.color, color: '#fff' } : {}"
                      @click="modal.icon = ic">
                  <i :class="`bi ${ic}`"></i>
                </span>
              </div>
            </div>
          </div>
          <div class="form-check form-switch">
            <input class="form-check-input" type="checkbox" v-model="modal.is_active" :true-value="1" :false-value="0" />
            <label class="form-check-label">Zona activa</label>
          </div>
        </div>
        <div class="modal-card-footer">
          <button class="btn btn-outline-secondary btn-sm" @click="cerrarModal">Cancelar</button>
          <button class="btn btn-primary btn-sm" :disabled="guardando" @click="guardar">
            <span v-if="guardando" class="spinner-border spinner-border-sm me-1"></span>
            {{ modal.id ? 'Guardar cambios' : 'Crear zona' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'
import { useModuleName } from '@/composables/useModuleName'

const { moduleName } = useModuleName()
const BASE = '/api/pos/zonas'

const items = ref([])
const loading = ref(true)
const guardando = ref(false)

const colorPresets = ['#1d4ed8','#0891b2','#059669','#d97706','#dc2626','#7c3aed','#db2777','#374151']
const iconOptions = [
  'bi-grid','bi-house','bi-cup-hot','bi-tree','bi-brightness-high',
  'bi-wind','bi-stars','bi-geo-alt','bi-easel','bi-columns-gap'
]

const emptyModal = () => ({
  visible: false, id: null, name: '', description: '',
  color: '#1d4ed8', icon: 'bi-grid', is_active: 1
})
const modal = ref(emptyModal())

async function cargar() {
  loading.value = true
  try {
    const res = await api.get(BASE)
    items.value = res.data
  } catch {
    showToast('Error al cargar zonas', 'error')
  } finally {
    loading.value = false
  }
}

function abrirModal(zona = null) {
  if (zona) {
    modal.value = { visible: true, id: zona.id, name: zona.name,
      description: zona.description || '', color: zona.color,
      icon: zona.icon, is_active: zona.is_active }
  } else {
    modal.value = { ...emptyModal(), visible: true }
  }
}

function cerrarModal() {
  modal.value = emptyModal()
}

async function guardar() {
  if (!modal.value.name.trim()) {
    showToast('El nombre es requerido', 'warning'); return
  }
  guardando.value = true
  try {
    const payload = {
      name: modal.value.name.trim(), description: modal.value.description || null,
      color: modal.value.color, icon: modal.value.icon, is_active: modal.value.is_active
    }
    if (modal.value.id) {
      await api.put(`${BASE}/${modal.value.id}`, payload)
      showToast('Zona actualizada')
    } else {
      await api.post(BASE, payload)
      showToast('Zona creada')
    }
    cerrarModal()
    await cargar()
  } catch (e) {
    showToast(e.response?.data?.detail || 'Error al guardar', 'error')
  } finally {
    guardando.value = false
  }
}

async function eliminar(zona) {
  const ok = await window.Swal.fire({
    title: `¿Desactivar "${zona.name}"?`,
    text: 'La zona quedará inactiva. Las mesas activas deben desactivarse primero.',
    icon: 'warning', showCancelButton: true,
    confirmButtonText: 'Sí, desactivar', cancelButtonText: 'Cancelar',
    confirmButtonColor: '#dc3545'
  })
  if (!ok.isConfirmed) return
  try {
    await api.delete(`${BASE}/${zona.id}`)
    showToast('Zona desactivada')
    await cargar()
  } catch (e) {
    showToast(e.response?.data?.detail || 'Error al eliminar', 'error')
  }
}

onMounted(cargar)
</script>

<style scoped>
.zonas-container { padding: 1rem; }

.page-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 1.25rem; flex-wrap: wrap; gap: .5rem;
}
.header-left { display: flex; align-items: center; }
.page-title { margin: 0; font-size: 1rem; font-weight: 600; }

.zonas-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}

.zona-card {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
  transition: box-shadow .2s;
}
.zona-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.1); }
.zona-inactiva { opacity: .55; }

.zona-color-bar { height: 5px; }

.zona-body {
  display: flex; align-items: flex-start; gap: .75rem;
  padding: .9rem 1rem .6rem;
}
.zona-icon-wrap {
  width: 42px; height: 42px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.25rem; flex-shrink: 0;
}
.zona-info { flex: 1; min-width: 0; }
.zona-name { font-weight: 600; font-size: .9rem; }
.zona-desc { font-size: .78rem; color: #6b7280; margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.zona-stats { display: flex; gap: .5rem; margin-top: .4rem; flex-wrap: wrap; }
.stat { font-size: .7rem; display: flex; align-items: center; gap: 3px; }
.stat i { font-size: .45rem; }
.stat.free i { color: #16a34a; }
.stat.occupied i { color: #dc2626; }
.stat.bill i { color: #d97706; }

.zona-actions { display: flex; flex-direction: column; align-items: flex-end; }
.zona-btn-group { display: flex; gap: .3rem; }

.zona-footer {
  border-top: 1px solid #f3f4f6;
  padding: .4rem 1rem;
  background: #fafafa;
}

.empty-state {
  text-align: center; padding: 3rem 1rem;
}

/* Modal */
.modal-backdrop-custom {
  position: fixed; inset: 0; background: rgba(0,0,0,.4);
  display: flex; align-items: center; justify-content: center;
  z-index: 1050; padding: 1rem;
}
.modal-card {
  background: #fff; border-radius: 12px;
  width: 100%; max-width: 440px;
  box-shadow: 0 8px 32px rgba(0,0,0,.18);
  overflow: hidden;
}
.modal-card-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: .85rem 1rem; border-bottom: 2px solid #1d4ed8;
  background: #fafafa;
}
.modal-card-body { padding: 1rem; }
.modal-card-footer {
  padding: .75rem 1rem; border-top: 1px solid #e5e7eb;
  display: flex; justify-content: flex-end; gap: .5rem;
  background: #fafafa;
}

.color-picker-row { display: flex; align-items: center; gap: .5rem; flex-wrap: wrap; }
.color-presets { display: flex; gap: .3rem; flex-wrap: wrap; }
.color-dot {
  width: 20px; height: 20px; border-radius: 50%; cursor: pointer;
  border: 2px solid transparent; transition: transform .15s;
}
.color-dot.active, .color-dot:hover { transform: scale(1.25); border-color: #111; }

.icon-selector { display: flex; flex-wrap: wrap; gap: .3rem; }
.icon-opt {
  width: 32px; height: 32px; border-radius: 6px; display: flex;
  align-items: center; justify-content: center; cursor: pointer;
  border: 1px solid #d1d5db; font-size: .95rem;
  transition: all .15s;
}
.icon-opt:hover { background: #f3f4f6; }
.icon-opt.active { border-color: transparent; }

/* Responsive */
@media (max-width: 768px) {
  .zonas-grid { grid-template-columns: 1fr 1fr; }
  .zona-icon-wrap { width: 36px; height: 36px; font-size: 1rem; }
}
@media (max-width: 576px) {
  .zonas-grid { grid-template-columns: 1fr; }
  .modal-card { max-width: 100%; border-radius: 12px 12px 0 0; align-self: flex-end; }
  .modal-backdrop-custom { align-items: flex-end; padding: 0; }
}
</style>
