<template>
  <div class="pq-view">
    <div class="pq-header">
      <h2 class="pq-title"><i class="bi bi-calendar-month-fill"></i> {{ moduleName }}</h2>
      <button class="btn-pq-primary" @click="abrirModal()">
        <i class="bi bi-plus-lg"></i> Nueva Mensualidad
      </button>
    </div>

    <!-- Filtros -->
    <div class="filtros-bar">
      <button v-for="f in filtros" :key="f.val" class="btn-filtro"
              :class="{ active: filtroActivo === f.val }" @click="filtroActivo = f.val; cargar()">
        {{ f.label }}
      </button>
      <input v-model="busqueda" class="search-input" placeholder="Buscar placa, nombre..."
             @input="cargar" />
    </div>

    <div v-if="loading" class="pq-loader">Cargando...</div>
    <div v-else-if="!mensualidades.length" class="pq-empty">
      <i class="bi bi-calendar-x" style="font-size:2.5rem;opacity:.3"></i>
      <p>No hay mensualidades registradas</p>
    </div>

    <div v-else class="pq-table-wrap">
      <table class="pq-table">
        <thead>
          <tr>
            <th>Placa</th>
            <th>Titular</th>
            <th>Teléfono</th>
            <th>Vence</th>
            <th>Días Restantes</th>
            <th>Valor</th>
            <th>Estado</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in mensualidades" :key="m.id" :class="{ 'row-moroso': m.dias_restantes < 0 }">
            <td class="td-placa">{{ m.placa }}</td>
            <td>{{ m.nombre_titular }}</td>
            <td>{{ m.telefono || '—' }}</td>
            <td>{{ m.fecha_fin }}</td>
            <td :class="diasClass(m.dias_restantes)">
              <span v-if="m.dias_restantes > 0">{{ m.dias_restantes }} días</span>
              <span v-else-if="m.dias_restantes === 0">Hoy</span>
              <span v-else>{{ Math.abs(m.dias_restantes) }} días mora</span>
            </td>
            <td class="td-mono">${{ Number(m.valor_mensualidad).toLocaleString() }}</td>
            <td>
              <span class="pq-badge" :class="`badge-${m.estado}`">{{ m.estado }}</span>
            </td>
            <td class="td-actions">
              <router-link :to="`/parqueadero/mensualidades/${m.id}`" class="btn-icon" title="Ver detalle">
                <i class="bi bi-eye-fill"></i>
              </router-link>
              <button class="btn-icon" title="Editar" @click="abrirModal(m)">
                <i class="bi bi-pencil-fill"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal nuevo/editar -->
    <div v-if="modal" class="pq-overlay" @click.self="modal = false">
      <div class="pq-modal pq-modal-lg">
        <div class="pq-modal-head">
          <h3>{{ form.id ? 'Editar' : 'Nueva' }} Mensualidad</h3>
          <button class="btn-close" @click="modal = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="pq-modal-body">
          <div class="form-row">
            <div class="form-col">
              <label>Placa *</label>
              <input v-model="form.placa" class="pq-input pq-input-placa"
                     placeholder="AAA000" @input="form.placa = form.placa.toUpperCase()" />
            </div>
            <div class="form-col">
              <label>Tipo Vehículo</label>
              <select v-model="form.tipo_vehiculo" class="pq-input">
                <option value="auto">Auto</option>
                <option value="moto">Moto</option>
                <option value="camioneta">Camioneta</option>
                <option value="otro">Otro</option>
              </select>
            </div>
          </div>

          <div class="form-row">
            <div class="form-col">
              <label>Nombre Titular *</label>
              <input v-model="form.nombre_titular" class="pq-input" placeholder="Nombre completo" />
            </div>
            <div class="form-col">
              <label>Documento</label>
              <input v-model="form.documento" class="pq-input" placeholder="CC o NIT" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-col">
              <label>Teléfono</label>
              <input v-model="form.telefono" class="pq-input" placeholder="Número de contacto" />
            </div>
            <div class="form-col">
              <label>Valor Mensualidad *</label>
              <input type="number" v-model.number="form.valor_mensualidad" class="pq-input" min="0" step="1000" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-col">
              <label>Fecha Inicio *</label>
              <CustomDatePicker v-model="form.fecha_inicio" />
            </div>
            <div class="form-col">
              <label>Fecha Fin *</label>
              <CustomDatePicker v-model="form.fecha_fin" />
            </div>
          </div>

          <label>Observaciones</label>
          <textarea v-model="form.observaciones" class="pq-input pq-textarea" rows="3"
                    placeholder="Notas adicionales..."></textarea>
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
import { ref, onMounted, watch } from 'vue'
import { useCompanyStore } from '@/stores/companyStore'
import { useModuleName } from '@/composables/useModuleName'
import { showToast } from '@/utils/toast'
import api from '@/services/apis'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'

const companyStore = useCompanyStore()
const { moduleName } = useModuleName()

const mensualidades = ref([])
const loading = ref(true)
const modal = ref(false)
const saving = ref(false)
const filtroActivo = ref(null)
const busqueda = ref('')

const filtros = [
  { val: null, label: 'Todos' },
  { val: 'activo', label: 'Activos' },
  { val: 'moroso', label: 'Morosos' },
  { val: 'retirado', label: 'Retirados' },
]

const hoy = () => new Date().toISOString().slice(0, 10)
const formBase = () => ({
  id: null, placa: '', tipo_vehiculo: 'auto', nombre_titular: '',
  documento: '', telefono: '', fecha_inicio: hoy(), fecha_fin: '',
  valor_mensualidad: 0, observaciones: '',
})
const form = ref(formBase())

const cid = () => companyStore.selectedCompany?.id_company

const diasClass = d => d < 0 ? 'dias-mora' : d <= 5 ? 'dias-alerta' : 'dias-ok'

async function cargar() {
  loading.value = true
  try {
    const params = { company_id: cid() }
    if (filtroActivo.value) params.estado = filtroActivo.value
    if (busqueda.value.trim()) params.q = busqueda.value.trim()
    const { data } = await api.get('/parqueadero/mensualidades', { params })
    mensualidades.value = data
  } catch { showToast('Error al cargar', 'error') }
  finally { loading.value = false }
}

function abrirModal(m = null) {
  form.value = m
    ? { ...formBase(), ...m }
    : formBase()
  modal.value = true
}

async function guardar() {
  if (!form.value.placa.trim()) return showToast('La placa es obligatoria', 'warn')
  if (!form.value.nombre_titular.trim()) return showToast('El nombre es obligatorio', 'warn')
  if (!form.value.fecha_inicio || !form.value.fecha_fin) return showToast('Las fechas son obligatorias', 'warn')
  saving.value = true
  try {
    const payload = {
      placa: form.value.placa, tipo_vehiculo: form.value.tipo_vehiculo,
      nombre_titular: form.value.nombre_titular, documento: form.value.documento,
      telefono: form.value.telefono, fecha_inicio: form.value.fecha_inicio,
      fecha_fin: form.value.fecha_fin, valor_mensualidad: form.value.valor_mensualidad,
      observaciones: form.value.observaciones,
    }
    if (form.value.id) {
      await api.put(`/parqueadero/mensualidades/${form.value.id}`, payload, { params: { company_id: cid() } })
    } else {
      await api.post('/parqueadero/mensualidades', payload, { params: { company_id: cid() } })
    }
    showToast('Guardado correctamente', 'success')
    modal.value = false
    cargar()
  } catch { showToast('Error al guardar', 'error') }
  finally { saving.value = false }
}

onMounted(cargar)
</script>

<style scoped>
.pq-view { padding: 16px; }
.pq-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; gap: 12px; flex-wrap: wrap; }
.pq-title { font-size: 20px; font-weight: 700; margin: 0; display: flex; align-items: center; gap: 8px; }
.pq-loader, .pq-empty { text-align: center; padding: 60px 20px; opacity: .5; }

.filtros-bar { display: flex; gap: 8px; align-items: center; margin-bottom: 16px; flex-wrap: wrap; }
.btn-filtro { background: var(--card-bg, #fff); border: 1.5px solid var(--border, #e2e8f0); border-radius: 20px; padding: 6px 16px; font-size: 13px; cursor: pointer; font-weight: 600; }
.btn-filtro.active { background: #3b82f6; color: #fff; border-color: #3b82f6; }
.search-input { flex: 1; min-width: 180px; padding: 8px 12px; border: 1.5px solid var(--border, #e2e8f0); border-radius: 8px; font-size: 14px; background: var(--input-bg, #f8fafc); }
.search-input:focus { outline: none; border-color: #3b82f6; }

.pq-table-wrap { overflow-x: auto; }
.pq-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.pq-table th { background: var(--table-head, #f1f5f9); padding: 10px 12px; text-align: left; font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase; white-space: nowrap; }
.pq-table td { padding: 11px 12px; border-bottom: 1px solid var(--border, #e2e8f0); vertical-align: middle; }
.pq-table tr:hover td { background: var(--row-hover, #f8fafc); }
.row-moroso td { background: #fff7f7 !important; }
.td-placa { font-size: 16px; font-weight: 800; letter-spacing: 2px; }
.td-mono { font-family: monospace; }
.td-actions { display: flex; gap: 4px; }
.dias-ok { color: #16a34a; font-weight: 600; }
.dias-alerta { color: #d97706; font-weight: 700; }
.dias-mora { color: #dc2626; font-weight: 700; }
.pq-badge { padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; text-transform: capitalize; }
.badge-activo   { background: #d1fae5; color: #065f46; }
.badge-moroso   { background: #fee2e2; color: #991b1b; }
.badge-retirado { background: #f1f5f9; color: #64748b; }

/* Buttons */
.btn-pq-primary { background: #3b82f6; color: #fff; border: none; border-radius: 8px; padding: 8px 18px; font-size: 14px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; }
.btn-pq-primary:hover { background: #2563eb; }
.btn-pq-primary:disabled { opacity: .6; cursor: not-allowed; }
.btn-pq-ghost { background: transparent; border: 1.5px solid #94a3b8; color: inherit; border-radius: 8px; padding: 8px 18px; font-size: 14px; cursor: pointer; }
.btn-icon { background: none; border: none; cursor: pointer; padding: 6px; border-radius: 6px; font-size: 16px; color: #64748b; text-decoration: none; display: inline-flex; align-items: center; }
.btn-icon:hover { background: #f1f5f9; }

/* Modal */
.pq-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 16px; }
.pq-modal { background: var(--modal-bg, #fff); border-radius: 14px; width: 100%; max-width: 420px; overflow: hidden; }
.pq-modal-lg { max-width: 600px; }
.pq-modal-head { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--border, #e2e8f0); }
.pq-modal-head h3 { margin: 0; font-size: 17px; }
.btn-close { background: none; border: none; cursor: pointer; font-size: 18px; color: #64748b; }
.pq-modal-body { padding: 20px; display: flex; flex-direction: column; gap: 12px; max-height: 70vh; overflow-y: auto; }
.pq-modal-foot { display: flex; gap: 10px; justify-content: flex-end; padding: 14px 20px; border-top: 1px solid var(--border, #e2e8f0); }
.pq-input { width: 100%; padding: 8px 12px; border: 1.5px solid var(--border, #e2e8f0); border-radius: 8px; font-size: 14px; background: var(--input-bg, #f8fafc); box-sizing: border-box; }
.pq-input:focus { outline: none; border-color: #3b82f6; }
.pq-input-placa { font-size: 20px; font-weight: 800; letter-spacing: 2px; }
.pq-textarea { resize: vertical; min-height: 80px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-col { display: flex; flex-direction: column; gap: 4px; }
.form-col label { font-size: 12px; font-weight: 600; color: #475569; }

@media (max-width: 768px) {
  .form-row { grid-template-columns: 1fr; }
}
@media (max-width: 576px) {
  .pq-view { padding: 10px; }
  .pq-modal { border-radius: 0; max-width: 100%; }
}
</style>
