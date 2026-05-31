<template>
  <div class="mesas-container">
    <!-- Header -->
    <div class="page-header">
      <div class="header-left">
        <h5 class="page-title">
          <i class="bi bi-table me-2"></i>{{ moduleName }}
        </h5>
      </div>
      <button class="btn btn-primary btn-sm" @click="abrirModal()">
        <i class="bi bi-plus-lg me-1"></i>Nueva {{ moduleName }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loadingZonas" class="text-center py-5">
      <div class="spinner-border text-primary" role="status"></div>
    </div>

    <!-- Sin zonas -->
    <div v-else-if="!zonas.length" class="empty-state">
      <i class="bi bi-grid-3x3-gap display-4 text-muted"></i>
      <p class="mt-3 text-muted">No hay zonas configuradas.</p>
      <router-link to="/pos/zonas" class="btn btn-outline-primary btn-sm">
        <i class="bi bi-plus-lg me-1"></i>Crear zonas primero
      </router-link>
    </div>

    <template v-else>
      <!-- Tabs de zonas -->
      <div class="zona-tabs">
        <button
          v-for="z in zonas"
          :key="z.id"
          class="zona-tab"
          :class="{ active: zonaActiva === z.id }"
          :style="zonaActiva === z.id ? { borderColor: z.color, color: z.color, background: z.color + '18' } : {}"
          @click="seleccionarZona(z.id)"
        >
          <i :class="`bi ${z.icon}`"></i>
          <span>{{ z.name }}</span>
          <span class="tab-counts">
            <span class="dot free"  v-if="z.free_count">{{ z.free_count }}</span>
            <span class="dot occ"   v-if="z.occupied_count">{{ z.occupied_count }}</span>
            <span class="dot bill"  v-if="z.bill_count">{{ z.bill_count }}</span>
          </span>
        </button>
      </div>

      <!-- Leyenda -->
      <div class="leyenda">
        <span class="leg-item free"><span class="leg-dot"></span>Libre</span>
        <span class="leg-item occupied"><span class="leg-dot"></span>Ocupada</span>
        <span class="leg-item bill"><span class="leg-dot"></span>Cuenta pedida</span>
        <span class="leg-item inactive"><span class="leg-dot"></span>Inactiva</span>
      </div>

      <!-- Grid de mesas -->
      <div v-if="loadingMesas" class="text-center py-4">
        <div class="spinner-border spinner-border-sm text-primary"></div>
      </div>

      <div v-else-if="mesasZona.length" class="mesas-grid">
        <div
          v-for="mesa in mesasZona"
          :key="mesa.id"
          class="mesa-card"
          :class="[`status-${mesa.status}`, { 'mesa-inactiva': !mesa.is_active }]"
          @click="mesa.is_active ? abrirEstado(mesa) : null"
        >
          <div class="mesa-status-bar"></div>
          <div class="mesa-body">
            <div class="mesa-icon">
              <i class="bi bi-grid-1x2-fill"></i>
            </div>
            <div class="mesa-name">{{ mesa.name }}</div>
            <div class="mesa-capacity">
              <i class="bi bi-people"></i> {{ mesa.capacity }}
            </div>
            <div class="mesa-badge">
              <span v-if="mesa.status === 'free'">Libre</span>
              <span v-else-if="mesa.status === 'occupied'">Ocupada</span>
              <span v-else-if="mesa.status === 'bill_requested'">Cuenta</span>
              <span v-else>Inactiva</span>
            </div>
          </div>
          <div class="mesa-footer-actions" @click.stop>
            <button
              v-if="mesa.status === 'occupied' || mesa.status === 'bill_requested'"
              class="btn-icon cancel-order"
              @click="cancelarPedido(mesa)"
              title="Cancelar pedido"
            >
              <i class="bi bi-x-circle-fill"></i>
            </button>
            <button class="btn-icon" @click="abrirModal(mesa)" title="Editar">
              <i class="bi bi-pencil-fill"></i>
            </button>
            <button class="btn-icon danger" @click="eliminar(mesa)" title="Eliminar mesa">
              <i class="bi bi-trash-fill"></i>
            </button>
          </div>
        </div>

        <!-- Botón agregar en grid -->
        <div class="mesa-card mesa-add" @click="abrirModal()">
          <i class="bi bi-plus-lg"></i>
          <span>Agregar</span>
        </div>
      </div>

      <div v-else class="empty-state-zona">
        <i class="bi bi-table text-muted" style="font-size:2rem"></i>
        <p class="text-muted mt-2 mb-3">No hay mesas en esta zona</p>
        <button class="btn btn-primary btn-sm" @click="abrirModal()">
          <i class="bi bi-plus-lg me-1"></i>Agregar mesa
        </button>
      </div>
    </template>

    <!-- Modal estado -->
    <div v-if="estadoModal.visible" class="modal-backdrop-custom" @click.self="estadoModal.visible = false">
      <div class="modal-card modal-card-sm">
        <div class="modal-card-header" :style="{ borderColor: estadoModal.mesa?.zone_color || '#1d4ed8' }">
          <h6 class="mb-0">
            <i class="bi bi-table me-2"></i>{{ estadoModal.mesa?.name }} — Cambiar estado
          </h6>
          <button class="btn-close btn-close-sm" @click="estadoModal.visible = false"></button>
        </div>
        <div class="modal-card-body">
          <div class="status-options">
            <button class="status-btn free"  @click="cambiarEstado(estadoModal.mesa, 'free')">
              <i class="bi bi-circle-fill"></i> Libre
            </button>
            <button class="status-btn occupied" @click="cambiarEstado(estadoModal.mesa, 'occupied')">
              <i class="bi bi-circle-fill"></i> Ocupada
            </button>
            <button class="status-btn bill" @click="cambiarEstado(estadoModal.mesa, 'bill_requested')">
              <i class="bi bi-circle-fill"></i> Cuenta pedida
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal crear/editar mesa -->
    <div v-if="modal.visible" class="modal-backdrop-custom" @click.self="cerrarModal">
      <div class="modal-card">
        <div class="modal-card-header">
          <h6 class="mb-0">
            <i class="bi bi-table me-2"></i>
            {{ modal.id ? 'Editar' : 'Nueva' }} {{ moduleName }}
          </h6>
          <button class="btn-close btn-close-sm" @click="cerrarModal"></button>
        </div>
        <div class="modal-card-body">
          <div class="mb-3">
            <label class="form-label">Zona <span class="text-danger">*</span></label>
            <select v-model="modal.zone_id" class="form-select">
              <option value="" disabled>Selecciona una zona</option>
              <option v-for="z in zonas" :key="z.id" :value="z.id">{{ z.name }}</option>
            </select>
          </div>
          <div class="mb-3">
            <label class="form-label">Nombre <span class="text-danger">*</span></label>
            <input v-model="modal.name" class="form-control" :placeholder="`Ej: Mesa 1, Barra 3`" maxlength="50" />
          </div>
          <div class="mb-3">
            <label class="form-label">Capacidad (personas)</label>
            <input v-model.number="modal.capacity" type="number" class="form-control" min="1" max="50" />
          </div>
          <div class="form-check form-switch">
            <input class="form-check-input" type="checkbox" v-model="modal.is_active" :true-value="1" :false-value="0" />
            <label class="form-check-label">Mesa activa</label>
          </div>
        </div>
        <div class="modal-card-footer">
          <button class="btn btn-outline-secondary btn-sm" @click="cerrarModal">Cancelar</button>
          <button class="btn btn-primary btn-sm" :disabled="guardando" @click="guardar">
            <span v-if="guardando" class="spinner-border spinner-border-sm me-1"></span>
            {{ modal.id ? 'Guardar cambios' : 'Crear mesa' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'
import { useModuleName } from '@/composables/useModuleName'
import { useCompanyStore } from '@/stores/companyStore'

const { moduleName } = useModuleName()
const companyStore = useCompanyStore()

const zonas = ref([])
const mesas = ref([])
const zonaActiva = ref(null)
const loadingZonas = ref(true)
const loadingMesas = ref(false)
const guardando = ref(false)

const estadoModal = ref({ visible: false, mesa: null })

const emptyModal = () => ({
  visible: false, id: null, zone_id: '', name: '', capacity: 4, is_active: 1
})
const modal = ref(emptyModal())

const mesasZona = computed(() =>
  mesas.value.filter(m => m.zone_id === zonaActiva.value)
)

async function cargarZonas() {
  loadingZonas.value = true
  try {
    const res = await api.get('/api/pos/zonas')
    zonas.value = res.data.filter(z => z.is_active)
    if (zonas.value.length) seleccionarZona(zonas.value[0].id)
  } catch {
    showToast('Error al cargar zonas', 'error')
  } finally {
    loadingZonas.value = false
  }
}

async function cargarMesas() {
  loadingMesas.value = true
  try {
    const res = await api.get('/api/pos/mesas')
    mesas.value = res.data
  } catch {
    showToast('Error al cargar mesas', 'error')
  } finally {
    loadingMesas.value = false
  }
}

function seleccionarZona(id) {
  zonaActiva.value = id
}

function abrirModal(mesa = null) {
  if (mesa) {
    modal.value = { visible: true, id: mesa.id, zone_id: mesa.zone_id,
      name: mesa.name, capacity: mesa.capacity, is_active: mesa.is_active }
  } else {
    modal.value = { ...emptyModal(), visible: true, zone_id: zonaActiva.value || '' }
  }
}

function cerrarModal() {
  modal.value = emptyModal()
}

async function guardar() {
  if (!modal.value.name.trim()) { showToast('El nombre es requerido', 'warning'); return }
  if (!modal.value.zone_id) { showToast('Selecciona una zona', 'warning'); return }
  guardando.value = true
  try {
    const payload = {
      zone_id: modal.value.zone_id, name: modal.value.name.trim(),
      capacity: modal.value.capacity || 4, is_active: modal.value.is_active
    }
    if (modal.value.id) {
      await api.put(`/api/pos/mesas/${modal.value.id}`, payload)
      showToast('Mesa actualizada')
    } else {
      await api.post('/api/pos/mesas', payload)
      showToast('Mesa creada')
    }
    cerrarModal()
    await cargarMesas()
    await cargarZonas()
  } catch (e) {
    showToast(e.response?.data?.detail || 'Error al guardar', 'error')
  } finally {
    guardando.value = false
  }
}

async function eliminar(mesa) {
  const ok = await window.Swal.fire({
    title: `¿Eliminar "${mesa.name}"?`,
    icon: 'warning', showCancelButton: true,
    confirmButtonText: 'Sí, eliminar', cancelButtonText: 'Cancelar',
    confirmButtonColor: '#dc3545'
  })
  if (!ok.isConfirmed) return
  try {
    await api.delete(`/api/pos/mesas/${mesa.id}`)
    showToast('Mesa eliminada')
    await cargarMesas()
    await cargarZonas()
  } catch (e) {
    showToast(e.response?.data?.detail || 'Error al eliminar', 'error')
  }
}

async function cancelarPedido(mesa) {
  const { isConfirmed, value: motivo } = await window.Swal.fire({
    title: `Cancelar pedido — ${mesa.name}`,
    text: 'Esta acción liberará la mesa. Ingresa el motivo:',
    input: 'text',
    inputPlaceholder: 'Ej: Error de captura, cliente se fue…',
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#dc2626',
    confirmButtonText: 'Cancelar pedido',
    cancelButtonText: 'Volver',
    inputValidator: (v) => !v?.trim() ? 'El motivo es requerido' : null,
  })
  if (!isConfirmed) return
  try {
    const cid = companyStore.selectedCompany?.id
    await api.delete('/api/pos/comanda/mesa/cancelar', {
      data: { table_id: mesa.id },
      headers: cid ? { 'X-Company-Id': cid } : {},
    })
    mesa.status = 'free'
    const idx = mesas.value.findIndex(m => m.id === mesa.id)
    if (idx >= 0) mesas.value[idx].status = 'free'
    await cargarZonas()
    showToast('Pedido cancelado', 'success')
  } catch (e) {
    showToast(e.response?.data?.detail || 'Error al cancelar pedido', 'error')
  }
}

function abrirEstado(mesa) {
  estadoModal.value = { visible: true, mesa }
}

async function cambiarEstado(mesa, nuevoEstado) {
  try {
    await api.patch(`/api/pos/mesas/${mesa.id}/estado`, { status: nuevoEstado })
    mesa.status = nuevoEstado
    const idx = mesas.value.findIndex(m => m.id === mesa.id)
    if (idx >= 0) mesas.value[idx].status = nuevoEstado
    estadoModal.value.visible = false
    await cargarZonas()
    showToast('Estado actualizado')
  } catch (e) {
    showToast(e.response?.data?.detail || 'Error', 'error')
  }
}

onMounted(async () => {
  await cargarZonas()
  await cargarMesas()
})
</script>

<style scoped>
.mesas-container { padding: 1rem; }

.page-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 1rem; flex-wrap: wrap; gap: .5rem;
}
.page-title { margin: 0; font-size: 1rem; font-weight: 600; }

/* Tabs de zona */
.zona-tabs {
  display: flex; gap: .4rem; overflow-x: auto;
  padding-bottom: .5rem; margin-bottom: .75rem;
  scrollbar-width: thin;
}
.zona-tab {
  display: flex; align-items: center; gap: .35rem;
  padding: .4rem .85rem; border-radius: 20px; font-size: .82rem;
  border: 1.5px solid #d1d5db; background: #fff; cursor: pointer;
  white-space: nowrap; transition: all .15s; font-weight: 500;
}
.zona-tab:hover { border-color: #6b7280; }
.zona-tab.active { font-weight: 600; }

.tab-counts { display: flex; gap: 3px; margin-left: .25rem; }
.tab-counts .dot {
  font-size: .65rem; border-radius: 10px; padding: 0 5px;
  font-weight: 700; line-height: 1.6;
}
.tab-counts .dot.free     { background: #dcfce7; color: #15803d; }
.tab-counts .dot.occ      { background: #fee2e2; color: #b91c1c; }
.tab-counts .dot.bill     { background: #fef3c7; color: #b45309; }

/* Leyenda */
.leyenda { display: flex; gap: 1rem; margin-bottom: 1rem; flex-wrap: wrap; }
.leg-item { display: flex; align-items: center; gap: .3rem; font-size: .75rem; color: #6b7280; }
.leg-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.leg-item.free .leg-dot     { background: #16a34a; }
.leg-item.occupied .leg-dot { background: #dc2626; }
.leg-item.bill .leg-dot     { background: #d97706; }
.leg-item.inactive .leg-dot { background: #9ca3af; }

/* Grid de mesas */
.mesas-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  gap: .75rem;
}

.mesa-card {
  border-radius: 10px; border: 1.5px solid #e5e7eb;
  background: #fff; overflow: hidden; cursor: pointer;
  transition: box-shadow .2s, transform .15s;
  position: relative;
}
.mesa-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.12); transform: translateY(-1px); }
.mesa-inactiva { opacity: .5; cursor: default; }

.mesa-status-bar { height: 4px; }
.status-free .mesa-status-bar        { background: #16a34a; }
.status-occupied .mesa-status-bar    { background: #dc2626; }
.status-bill_requested .mesa-status-bar { background: #d97706; }

.mesa-body {
  padding: .7rem .5rem .4rem;
  display: flex; flex-direction: column; align-items: center; text-align: center;
}
.mesa-icon { font-size: 1.6rem; margin-bottom: .25rem; }
.status-free .mesa-icon        { color: #16a34a; }
.status-occupied .mesa-icon    { color: #dc2626; }
.status-bill_requested .mesa-icon { color: #d97706; }

.mesa-name { font-weight: 600; font-size: .8rem; }
.mesa-capacity { font-size: .7rem; color: #9ca3af; margin-top: 2px; }

.mesa-badge { margin-top: .3rem; }
.mesa-badge span {
  font-size: .65rem; font-weight: 600; padding: 1px 7px;
  border-radius: 10px;
}
.status-free .mesa-badge span        { background: #dcfce7; color: #15803d; }
.status-occupied .mesa-badge span    { background: #fee2e2; color: #b91c1c; }
.status-bill_requested .mesa-badge span { background: #fef3c7; color: #b45309; }

.mesa-footer-actions {
  display: flex; justify-content: center; gap: .25rem;
  padding: .3rem; border-top: 1px solid #f3f4f6;
  background: #fafafa;
}
.btn-icon {
  width: 26px; height: 26px; border-radius: 5px; border: none;
  background: transparent; cursor: pointer; display: flex;
  align-items: center; justify-content: center; font-size: .75rem;
  transition: background .15s;
}
.btn-icon:hover { background: #e5e7eb; }
.btn-icon.danger:hover       { background: #fee2e2; color: #dc2626; }
.btn-icon.cancel-order       { color: #dc2626; }
.btn-icon.cancel-order:hover { background: #fee2e2; color: #b91c1c; }

/* Mesa agregar */
.mesa-add {
  border: 1.5px dashed #d1d5db; cursor: pointer;
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; padding: 1.5rem .5rem;
  color: #9ca3af; font-size: .8rem; gap: .3rem;
  min-height: 120px;
}
.mesa-add i { font-size: 1.3rem; }
.mesa-add:hover { border-color: #3b82f6; color: #3b82f6; background: #eff6ff; }

.empty-state { text-align: center; padding: 3rem 1rem; }
.empty-state-zona { text-align: center; padding: 2rem 1rem; }

/* Modal estado */
.modal-card-sm { max-width: 300px; }
.status-options { display: flex; flex-direction: column; gap: .6rem; }
.status-btn {
  padding: .6rem 1rem; border-radius: 8px; border: none;
  cursor: pointer; font-weight: 600; display: flex; align-items: center;
  gap: .5rem; font-size: .85rem; transition: opacity .15s;
}
.status-btn:hover { opacity: .85; }
.status-btn.free     { background: #dcfce7; color: #15803d; }
.status-btn.free i   { color: #16a34a; }
.status-btn.occupied { background: #fee2e2; color: #b91c1c; }
.status-btn.occupied i { color: #dc2626; }
.status-btn.bill     { background: #fef3c7; color: #b45309; }
.status-btn.bill i   { color: #d97706; }

/* Modal */
.modal-backdrop-custom {
  position: fixed; inset: 0; background: rgba(0,0,0,.4);
  display: flex; align-items: center; justify-content: center;
  z-index: 1050; padding: 1rem;
}
.modal-card {
  background: #fff; border-radius: 12px;
  width: 100%; max-width: 400px;
  box-shadow: 0 8px 32px rgba(0,0,0,.18); overflow: hidden;
}
.modal-card-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: .85rem 1rem; border-bottom: 2px solid #1d4ed8; background: #fafafa;
}
.modal-card-body { padding: 1rem; }
.modal-card-footer {
  padding: .75rem 1rem; border-top: 1px solid #e5e7eb;
  display: flex; justify-content: flex-end; gap: .5rem; background: #fafafa;
}

/* Responsive */
@media (max-width: 768px) {
  .mesas-grid { grid-template-columns: repeat(auto-fill, minmax(90px, 1fr)); gap: .5rem; }
}
@media (max-width: 576px) {
  .mesas-grid { grid-template-columns: repeat(3, 1fr); }
  .modal-card { max-width: 100%; border-radius: 12px 12px 0 0; align-self: flex-end; }
  .modal-backdrop-custom { align-items: flex-end; padding: 0; }
  .modal-card-sm { max-width: 100%; border-radius: 12px 12px 0 0; align-self: flex-end; }
  .zona-tab { padding: .35rem .65rem; }
}
</style>
