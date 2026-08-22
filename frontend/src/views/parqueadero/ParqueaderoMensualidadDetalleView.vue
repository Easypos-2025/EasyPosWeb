<template>
  <div class="pq-view">
    <div class="pq-header">
      <button class="btn-back" @click="$router.back()">
        <i class="bi bi-arrow-left"></i>
      </button>
      <h2 class="pq-title">{{ data?.placa || '...' }}</h2>
      <div class="header-actions">
        <button class="btn-pq-ghost" @click="abrirEditar">
          <i class="bi bi-pencil-fill"></i> Editar
        </button>
        <select class="estado-select" :value="data?.estado" @change="cambiarEstado($event.target.value)"
                :class="`estado-${data?.estado}`">
          <option value="activo">Activo</option>
          <option value="moroso">Moroso</option>
          <option value="retirado">Retirado</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="pq-loader">Cargando...</div>
    <div v-else-if="!data" class="pq-empty">No encontrado</div>

    <div v-else class="detalle-grid">
      <!-- Info principal -->
      <div class="pq-card">
        <h3 class="card-title"><i class="bi bi-person-fill"></i> Datos del Abonado</h3>
        <div class="info-grid">
          <div class="info-row"><span class="info-label">Titular</span><span class="info-val">{{ data.nombre_titular }}</span></div>
          <div class="info-row"><span class="info-label">Documento</span><span class="info-val">{{ data.documento || '—' }}</span></div>
          <div class="info-row"><span class="info-label">Teléfono</span><span class="info-val">{{ data.telefono || '—' }}</span></div>
          <div class="info-row"><span class="info-label">Tipo Vehículo</span><span class="info-val" style="text-transform:capitalize">{{ data.tipo_vehiculo }}</span></div>
          <div class="info-row"><span class="info-label">Vigencia</span><span class="info-val">{{ data.fecha_inicio }} → {{ data.fecha_fin }}</span></div>
          <div class="info-row"><span class="info-label">Valor Mensual</span><span class="info-val td-money">${{ Number(data.valor_mensualidad).toLocaleString() }}</span></div>
          <div class="info-row">
            <span class="info-label">Días Restantes</span>
            <span class="info-val" :class="diasClass(data.dias_restantes)">
              {{ data.dias_restantes > 0 ? data.dias_restantes + ' días' : data.dias_restantes === 0 ? 'Hoy vence' : Math.abs(data.dias_restantes) + ' días mora' }}
            </span>
          </div>
        </div>
        <div v-if="data.observaciones" class="obs-box">
          <strong>Observaciones:</strong> {{ data.observaciones }}
        </div>
      </div>

      <!-- Fotos de evidencia -->
      <div class="pq-card">
        <div class="card-head-row">
          <h3 class="card-title"><i class="bi bi-images"></i> Fotos de Evidencia</h3>
          <button class="btn-pq-sm" @click="triggerFoto">
            <i class="bi bi-plus"></i> Agregar
          </button>
          <input ref="fotoInput" type="file" accept="image/*" capture="environment"
                 style="display:none" @change="subirFoto" />
        </div>
        <div v-if="!data.fotos?.length" class="pq-empty-sm">Sin fotos registradas</div>
        <div v-else class="fotos-grid">
          <div v-for="f in data.fotos" :key="f.id" class="foto-item">
            <img :src="f.url" @click="verFoto(f.url)" />
            <button class="btn-foto-del" @click="eliminarFoto(f.id)">
              <i class="bi bi-x-circle-fill"></i>
            </button>
          </div>
        </div>
      </div>

      <!-- Historial de pagos -->
      <div class="pq-card">
        <div class="card-head-row">
          <h3 class="card-title"><i class="bi bi-cash-coin"></i> Historial de Pagos</h3>
          <button class="btn-pq-sm btn-pq-sm--green" @click="modalPago = true">
            <i class="bi bi-plus"></i> Registrar Pago
          </button>
        </div>
        <div v-if="!data.pagos?.length" class="pq-empty-sm">Sin pagos registrados</div>
        <div v-else class="pagos-list">
          <div v-for="p in data.pagos" :key="p.id" class="pago-row">
            <div class="pago-fecha">{{ p.fecha_pago }}</div>
            <div class="pago-periodo">{{ p.periodo_desde }} → {{ p.periodo_hasta }}</div>
            <div class="pago-forma">{{ p.forma_pago }}</div>
            <div class="pago-valor">${{ Number(p.valor_pagado).toLocaleString() }}</div>
            <button class="btn-icon-sm" @click="eliminarPago(p.id)">
              <i class="bi bi-trash3"></i>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal registrar pago -->
    <div v-if="modalPago" class="pq-overlay" @click.self="modalPago = false">
      <div class="pq-modal">
        <div class="pq-modal-head">
          <h3><i class="bi bi-cash-coin"></i> Registrar Pago</h3>
          <button class="btn-close" @click="modalPago = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="pq-modal-body">
          <label>Fecha de Pago</label>
          <CustomDatePicker v-model="pagoForm.fecha_pago" />

          <label>Período Desde</label>
          <CustomDatePicker v-model="pagoForm.periodo_desde" />

          <label>Período Hasta</label>
          <CustomDatePicker v-model="pagoForm.periodo_hasta" />

          <label>Forma de Pago</label>
          <select v-model="pagoForm.forma_pago" class="pq-input">
            <option value="efectivo">Efectivo</option>
            <option value="transferencia">Transferencia</option>
            <option value="otro">Otro</option>
          </select>

          <label>Valor Pagado *</label>
          <input type="number" v-model.number="pagoForm.valor_pagado" class="pq-input" min="0" step="1000" />

          <label>Observación</label>
          <input v-model="pagoForm.observacion" class="pq-input" placeholder="Opcional" />
        </div>
        <div class="pq-modal-foot">
          <button class="btn-pq-ghost" @click="modalPago = false">Cancelar</button>
          <button class="btn-pq-primary" :disabled="savingPago" @click="guardarPago">
            <i class="bi" :class="savingPago ? 'bi-hourglass-split' : 'bi-check2'"></i>
            {{ savingPago ? 'Guardando...' : 'Guardar Pago' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Lightbox foto -->
    <div v-if="fotoLightbox" class="foto-lightbox" @click="fotoLightbox = null">
      <img :src="fotoLightbox" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useCompanyStore } from '@/stores/companyStore'
import { showToast } from '@/utils/toast'
import api from '@/services/apis'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'

const route = useRoute()
const companyStore = useCompanyStore()
const fotoInput = ref(null)

const data = ref(null)
const loading = ref(true)
const modalPago = ref(false)
const savingPago = ref(false)
const fotoLightbox = ref(null)

const hoy = () => new Date().toISOString().slice(0, 10)
const pagoFormBase = () => ({
  fecha_pago: hoy(), periodo_desde: hoy(), periodo_hasta: '',
  forma_pago: 'efectivo', valor_pagado: data.value?.valor_mensualidad || 0, observacion: '',
})
const pagoForm = ref(pagoFormBase())

const cid = () => companyStore.selectedCompany?.id_company
const menId = () => route.params.id

const diasClass = d => d < 0 ? 'dias-mora' : d <= 5 ? 'dias-alerta' : 'dias-ok'

async function cargar() {
  loading.value = true
  try {
    const { data: d } = await api.get(`/parqueadero/mensualidades/${menId()}`, { params: { company_id: cid() } })
    data.value = d
  } catch { showToast('Error al cargar mensualidad', 'error') }
  finally { loading.value = false }
}

async function cambiarEstado(est) {
  try {
    await api.patch(`/parqueadero/mensualidades/${menId()}/estado`, null, {
      params: { company_id: cid(), estado: est }
    })
    showToast('Estado actualizado', 'success')
    cargar()
  } catch { showToast('Error al cambiar estado', 'error') }
}

function abrirEditar() {
  // Navegar a la lista con el modal pre-abierto no es limpio en este context;
  // simplemente redirigir a la lista con la mensualidad seleccionada
  // Para una UX mejor, emitir evento o usar store — solución simple: router push
  window.history.back()
}

// Fotos
function triggerFoto() { fotoInput.value?.click() }

async function subirFoto(e) {
  const file = e.target.files?.[0]
  if (!file) return
  const fd = new FormData()
  fd.append('file', file)
  try {
    await api.post(`/parqueadero/mensualidades/${menId()}/fotos`, fd, {
      params: { company_id: cid() },
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    showToast('Foto agregada', 'success')
    cargar()
  } catch { showToast('Error al subir foto', 'error') }
}

async function eliminarFoto(fotoId) {
  if (!confirm('¿Eliminar esta foto?')) return
  try {
    await api.delete(`/parqueadero/mensualidades/fotos/${fotoId}`, { params: { company_id: cid() } })
    showToast('Foto eliminada', 'success')
    cargar()
  } catch { showToast('Error al eliminar', 'error') }
}

function verFoto(url) { fotoLightbox.value = url }

// Pagos
async function guardarPago() {
  if (!pagoForm.value.valor_pagado) return showToast('El valor es obligatorio', 'warn')
  if (!pagoForm.value.periodo_hasta) return showToast('La fecha de fin del período es obligatoria', 'warn')
  savingPago.value = true
  try {
    await api.post(`/parqueadero/mensualidades/${menId()}/pagos`, pagoForm.value, {
      params: { company_id: cid() }
    })
    showToast('Pago registrado', 'success')
    modalPago.value = false
    pagoForm.value = pagoFormBase()
    cargar()
  } catch { showToast('Error al guardar pago', 'error') }
  finally { savingPago.value = false }
}

async function eliminarPago(pagoId) {
  if (!confirm('¿Eliminar este pago?')) return
  try {
    await api.delete(`/parqueadero/mensualidades/pagos/${pagoId}`, { params: { company_id: cid() } })
    showToast('Pago eliminado', 'success')
    cargar()
  } catch { showToast('Error al eliminar', 'error') }
}

onMounted(cargar)
</script>

<style scoped>
.pq-view { padding: 16px; }
.pq-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
.pq-title { font-size: 24px; font-weight: 900; letter-spacing: 3px; margin: 0; flex: 1; }
.btn-back { background: none; border: 1.5px solid var(--border, #e2e8f0); border-radius: 8px; padding: 8px 12px; cursor: pointer; font-size: 18px; }
.header-actions { display: flex; align-items: center; gap: 8px; }
.pq-loader, .pq-empty { text-align: center; padding: 60px; opacity: .5; }

.detalle-grid { display: grid; grid-template-columns: 380px 1fr; gap: 16px; align-items: start; }
.pq-card { background: var(--card-bg, #fff); border-radius: 12px; padding: 20px; box-shadow: 0 1px 8px rgba(0,0,0,.07); }
.card-title { font-size: 15px; font-weight: 700; margin: 0 0 14px; display: flex; align-items: center; gap: 7px; }
.card-head-row { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.card-head-row .card-title { margin: 0; flex: 1; }

/* Info grid */
.info-grid { display: flex; flex-direction: column; gap: 10px; }
.info-row { display: flex; justify-content: space-between; align-items: center; font-size: 14px; border-bottom: 1px solid var(--border, #f1f5f9); padding-bottom: 8px; gap: 10px; }
.info-label { color: #64748b; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: .4px; min-width: 110px; }
.info-val { font-weight: 600; text-align: right; }
.td-money { color: #16a34a; font-size: 16px; }
.obs-box { margin-top: 12px; background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 10px 12px; font-size: 13px; }
.dias-ok { color: #16a34a; }
.dias-alerta { color: #d97706; }
.dias-mora { color: #dc2626; font-weight: 700; }

/* Fotos */
.fotos-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 8px; }
.foto-item { position: relative; border-radius: 8px; overflow: hidden; aspect-ratio: 1; }
.foto-item img { width: 100%; height: 100%; object-fit: cover; cursor: pointer; }
.btn-foto-del { position: absolute; top: 4px; right: 4px; background: rgba(0,0,0,.55); border: none; color: #fff; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; font-size: 14px; display: flex; align-items: center; justify-content: center; }
.pq-empty-sm { text-align: center; padding: 20px; opacity: .4; font-size: 13px; }

/* Pagos */
.pagos-list { display: flex; flex-direction: column; gap: 6px; }
.pago-row { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 8px; background: var(--row-hover, #f8fafc); font-size: 13px; }
.pago-fecha { font-weight: 700; min-width: 90px; }
.pago-periodo { flex: 1; color: #64748b; font-size: 12px; }
.pago-forma { color: #64748b; min-width: 90px; text-transform: capitalize; }
.pago-valor { font-weight: 700; color: #16a34a; min-width: 90px; text-align: right; }
.btn-icon-sm { background: none; border: none; cursor: pointer; color: #ef4444; font-size: 14px; padding: 4px; }

/* Estado select */
.estado-select { padding: 6px 12px; border-radius: 8px; border: 1.5px solid var(--border, #e2e8f0); font-size: 13px; font-weight: 700; cursor: pointer; }
.estado-activo  { background: #d1fae5; color: #065f46; border-color: #6ee7b7; }
.estado-moroso  { background: #fee2e2; color: #991b1b; border-color: #fca5a5; }
.estado-retirado { background: #f1f5f9; color: #64748b; }

/* Buttons */
.btn-pq-primary { background: #3b82f6; color: #fff; border: none; border-radius: 8px; padding: 8px 18px; font-size: 14px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; }
.btn-pq-primary:hover { background: #2563eb; }
.btn-pq-primary:disabled { opacity: .6; cursor: not-allowed; }
.btn-pq-ghost { background: transparent; border: 1.5px solid #94a3b8; color: inherit; border-radius: 8px; padding: 8px 14px; font-size: 13px; cursor: pointer; display: flex; align-items: center; gap: 6px; }
.btn-pq-sm { background: #eff6ff; border: 1px solid #bfdbfe; color: #1d4ed8; border-radius: 6px; padding: 5px 12px; font-size: 12px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 5px; }
.btn-pq-sm--green { background: #ecfdf5; border-color: #6ee7b7; color: #065f46; }

/* Modal */
.pq-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 16px; }
.pq-modal { background: var(--modal-bg, #fff); border-radius: 14px; width: 100%; max-width: 420px; overflow: hidden; }
.pq-modal-head { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--border, #e2e8f0); }
.pq-modal-head h3 { margin: 0; font-size: 17px; display: flex; align-items: center; gap: 8px; }
.btn-close { background: none; border: none; cursor: pointer; font-size: 18px; color: #64748b; }
.pq-modal-body { padding: 20px; display: flex; flex-direction: column; gap: 12px; max-height: 65vh; overflow-y: auto; }
.pq-modal-body label { font-size: 12px; font-weight: 600; color: #475569; }
.pq-modal-foot { display: flex; gap: 10px; justify-content: flex-end; padding: 14px 20px; border-top: 1px solid var(--border, #e2e8f0); }
.pq-input { width: 100%; padding: 8px 12px; border: 1.5px solid var(--border, #e2e8f0); border-radius: 8px; font-size: 14px; background: var(--input-bg, #f8fafc); box-sizing: border-box; }
.pq-input:focus { outline: none; border-color: #3b82f6; }

/* Lightbox */
.foto-lightbox { position: fixed; inset: 0; background: rgba(0,0,0,.9); z-index: 2000; display: flex; align-items: center; justify-content: center; cursor: zoom-out; }
.foto-lightbox img { max-width: 95vw; max-height: 90vh; border-radius: 8px; }

@media (max-width: 768px) {
  .detalle-grid { grid-template-columns: 1fr; }
}
@media (max-width: 576px) {
  .pq-view { padding: 10px; }
  .pq-modal { border-radius: 0; max-width: 100%; }
}
</style>
