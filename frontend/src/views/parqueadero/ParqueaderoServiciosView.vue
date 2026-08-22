<template>
  <div class="pq-view">
    <div class="pq-header">
      <h2 class="pq-title"><i class="bi bi-gear-fill"></i> {{ moduleName }}</h2>
      <button class="btn-pq-primary" @click="abrirModal()">
        <i class="bi bi-plus-lg"></i> Nuevo Servicio
      </button>
    </div>

    <div v-if="loading" class="pq-loader">Cargando...</div>
    <div v-else-if="!servicios.length" class="pq-empty">
      <i class="bi bi-gear" style="font-size:2.5rem;opacity:.3"></i>
      <p>No hay servicios registrados</p>
    </div>

    <div v-else class="pq-table-wrap">
      <table class="pq-table">
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Categoría</th>
            <th>Tipo Cobro</th>
            <th>Tarifa</th>
            <th>Estado</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="svc in servicios" :key="svc.id">
            <td class="td-nombre">{{ svc.nombre }}</td>
            <td>
              <span v-if="svc.categoria_nombre" class="tag-cat" :style="{ background: (svc.categoria_color || '#3b82f6') + '22', color: svc.categoria_color || '#3b82f6' }">
                {{ svc.categoria_nombre }}
              </span>
              <span v-else style="opacity:.4">—</span>
            </td>
            <td><span class="tag-tipo" :class="`tipo-${svc.tipo_cobro}`">{{ labelTipo(svc.tipo_cobro) }}</span></td>
            <td class="td-tarifa">{{ resumenTarifa(svc) }}</td>
            <td><span class="pq-badge" :class="svc.is_active ? 'badge-activo' : 'badge-inactivo'">{{ svc.is_active ? 'Activo' : 'Inactivo' }}</span></td>
            <td class="td-actions">
              <button class="btn-icon" @click="abrirModal(svc)"><i class="bi bi-pencil-fill"></i></button>
              <button class="btn-icon btn-danger" @click="eliminar(svc)"><i class="bi bi-trash3-fill"></i></button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal -->
    <div v-if="modal" class="pq-overlay" @click.self="modal = false">
      <div class="pq-modal pq-modal-lg">
        <div class="pq-modal-head">
          <h3>{{ form.id ? 'Editar' : 'Nuevo' }} Servicio</h3>
          <button class="btn-close" @click="modal = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="pq-modal-body">
          <div class="form-row">
            <div class="form-col">
              <label>Nombre del Servicio *</label>
              <input v-model="form.nombre" class="pq-input" placeholder="Ej: Auto 12 Horas" />
            </div>
            <div class="form-col">
              <label>Categoría</label>
              <select v-model="form.categoria_id" class="pq-input">
                <option :value="null">— Sin categoría —</option>
                <option v-for="c in categorias" :key="c.id" :value="c.id">{{ c.nombre }}</option>
              </select>
            </div>
          </div>

          <div class="form-row">
            <div class="form-col">
              <label>Tipo de Cobro *</label>
              <select v-model="form.tipo_cobro" class="pq-input">
                <option value="tarifa_plana">Tarifa Plana (período fijo)</option>
                <option value="por_minuto">Por Minuto</option>
                <option value="mensualidad">Mensualidad</option>
              </select>
            </div>
          </div>

          <!-- Campos según tipo_cobro -->
          <template v-if="form.tipo_cobro === 'tarifa_plana'">
            <div class="form-row">
              <div class="form-col">
                <label>Tarifa Base *</label>
                <input type="number" v-model.number="form.tarifa_base" class="pq-input" min="0" step="100" />
              </div>
              <div class="form-col">
                <label>Período Base (horas)</label>
                <input type="number" v-model.number="form.periodo_horas" class="pq-input" min="1" placeholder="12" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-col">
                <label>Tarifa Adicional (por período extra)</label>
                <input type="number" v-model.number="form.tarifa_adicional" class="pq-input" min="0" step="100" />
              </div>
            </div>
          </template>

          <template v-else-if="form.tipo_cobro === 'por_minuto'">
            <div class="form-row">
              <div class="form-col">
                <label>Tarifa por Minuto *</label>
                <input type="number" v-model.number="form.tarifa_minuto" class="pq-input" min="0" step="10" />
              </div>
            </div>
          </template>

          <template v-else-if="form.tipo_cobro === 'mensualidad'">
            <div class="info-box">
              <i class="bi bi-info-circle"></i>
              El valor de la mensualidad se define al registrar cada abonado. Este servicio no cobra por tiempo.
            </div>
          </template>

          <label class="pq-check-label" style="margin-top:6px">
            <input type="checkbox" v-model="form.is_active" :true-value="1" :false-value="0" />
            Servicio activo
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

const servicios = ref([])
const categorias = ref([])
const loading = ref(true)
const modal = ref(false)
const saving = ref(false)

const formBase = () => ({
  id: null, nombre: '', categoria_id: null, tipo_cobro: 'tarifa_plana',
  tarifa_base: 0, periodo_horas: 12, tarifa_adicional: 0, tarifa_minuto: 0,
  plazas_total: 0, is_active: 1,
})
const form = ref(formBase())

const cid = () => companyStore.selectedCompany?.id

const labelTipo = t => ({ tarifa_plana: 'Tarifa Plana', por_minuto: 'Por Minuto', mensualidad: 'Mensualidad' }[t] || t)

const resumenTarifa = svc => {
  if (svc.tipo_cobro === 'tarifa_plana') return `$${(+svc.tarifa_base).toLocaleString()} / ${svc.periodo_horas || 12}h`
  if (svc.tipo_cobro === 'por_minuto') return `$${(+svc.tarifa_minuto).toLocaleString()}/min`
  return 'Mensual'
}

async function cargar() {
  loading.value = true
  try {
    const [svcs, cats] = await Promise.all([
      api.get('/api/parqueadero/servicios', { params: { company_id: cid() } }),
      api.get('/api/parqueadero/categorias', { params: { company_id: cid() } }),
    ])
    servicios.value = svcs.data
    categorias.value = cats.data.filter(c => c.is_active)
  } catch { showToast('Error al cargar servicios', 'error') }
  finally { loading.value = false }
}

function abrirModal(svc = null) {
  form.value = svc
    ? { ...formBase(), ...svc }
    : formBase()
  modal.value = true
}

async function guardar() {
  if (!form.value.nombre.trim()) return showToast('El nombre es obligatorio', 'warn')
  saving.value = true
  try {
    const payload = {
      nombre: form.value.nombre, categoria_id: form.value.categoria_id,
      tipo_cobro: form.value.tipo_cobro, tarifa_base: form.value.tarifa_base,
      periodo_horas: form.value.periodo_horas, tarifa_adicional: form.value.tarifa_adicional,
      tarifa_minuto: form.value.tarifa_minuto, plazas_total: form.value.plazas_total,
      is_active: form.value.is_active,
    }
    if (form.value.id) {
      await api.put(`/parqueadero/servicios/${form.value.id}`, payload, { params: { company_id: cid() } })
    } else {
      await api.post('/api/parqueadero/servicios', payload, { params: { company_id: cid() } })
    }
    showToast('Guardado correctamente', 'success')
    modal.value = false
    cargar()
  } catch { showToast('Error al guardar', 'error') }
  finally { saving.value = false }
}

async function eliminar(svc) {
  if (!confirm(`¿Eliminar servicio "${svc.nombre}"?`)) return
  try {
    await api.delete(`/parqueadero/servicios/${svc.id}`, { params: { company_id: cid() } })
    showToast('Servicio eliminado', 'success')
    cargar()
  } catch { showToast('No se puede eliminar (tiene registros asociados)', 'error') }
}

onMounted(cargar)
</script>

<style scoped>
.pq-view { padding: 16px; }
.pq-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; gap: 12px; flex-wrap: wrap; }
.pq-title { font-size: 20px; font-weight: 700; margin: 0; display: flex; align-items: center; gap: 8px; }
.pq-loader, .pq-empty { text-align: center; padding: 60px 20px; opacity: .5; }

.pq-table-wrap { overflow-x: auto; }
.pq-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.pq-table th { background: var(--table-head, #f1f5f9); padding: 10px 12px; text-align: left; font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: .5px; white-space: nowrap; }
.pq-table td { padding: 11px 12px; border-bottom: 1px solid var(--border, #e2e8f0); vertical-align: middle; }
.pq-table tr:hover td { background: var(--row-hover, #f8fafc); }
.td-nombre { font-weight: 600; }
.td-tarifa { font-family: monospace; }
.td-actions { display: flex; gap: 4px; }

.tag-cat { padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }
.tag-tipo { padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 700; }
.tipo-tarifa_plana { background: #dbeafe; color: #1d4ed8; }
.tipo-por_minuto   { background: #fef9c3; color: #854d0e; }
.tipo-mensualidad  { background: #f3e8ff; color: #7e22ce; }
.pq-badge { padding: 2px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; }
.badge-activo   { background: #d1fae5; color: #065f46; }
.badge-inactivo { background: #fee2e2; color: #991b1b; }

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
.pq-modal-lg { max-width: 580px; }
.pq-modal-head { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--border, #e2e8f0); }
.pq-modal-head h3 { margin: 0; font-size: 17px; }
.btn-close { background: none; border: none; cursor: pointer; font-size: 18px; color: #64748b; }
.pq-modal-body { padding: 20px; display: flex; flex-direction: column; gap: 12px; max-height: 65vh; overflow-y: auto; }
.pq-modal-foot { display: flex; gap: 10px; justify-content: flex-end; padding: 14px 20px; border-top: 1px solid var(--border, #e2e8f0); }
.pq-input { width: 100%; padding: 8px 12px; border: 1.5px solid var(--border, #e2e8f0); border-radius: 8px; font-size: 14px; background: var(--input-bg, #f8fafc); box-sizing: border-box; }
.pq-input:focus { outline: none; border-color: #3b82f6; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-col { display: flex; flex-direction: column; gap: 4px; }
.form-col label { font-size: 12px; font-weight: 600; color: #475569; }
.pq-check-label { display: flex; align-items: center; gap: 8px; font-size: 14px; cursor: pointer; }
.info-box { background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 12px 14px; font-size: 13px; color: #1d4ed8; display: flex; align-items: flex-start; gap: 8px; }

@media (max-width: 768px) {
  .form-row { grid-template-columns: 1fr; }
}
@media (max-width: 576px) {
  .pq-view { padding: 10px; }
  .pq-modal { border-radius: 0; max-width: 100%; }
}
</style>
