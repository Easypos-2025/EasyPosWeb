<template>
  <div class="pq-view">
    <div class="pq-header">
      <h2 class="pq-title"><i class="bi bi-box-arrow-in-right"></i> {{ moduleName }}</h2>
    </div>

    <!-- Formulario de ingreso -->
    <div class="ingreso-grid">
      <!-- Panel registro -->
      <div class="pq-card ingreso-form">
        <h3 class="card-title"><i class="bi bi-plus-circle-fill"></i> Registrar Ingreso</h3>

        <label>Servicio *</label>
        <select v-model="form.servicio_id" class="pq-input">
          <option :value="null" disabled>— Seleccionar servicio —</option>
          <option v-for="svc in servicios" :key="svc.id" :value="svc.id">
            {{ svc.nombre }} ({{ labelTipo(svc.tipo_cobro) }})
          </option>
        </select>

        <label>Placa del Vehículo *</label>
        <input v-model="form.placa" class="pq-input pq-input-placa"
               placeholder="AAA000" maxlength="10"
               @input="form.placa = form.placa.toUpperCase()"
               @keydown.enter="buscarMensualidad" />

        <!-- Alerta mensualidad activa -->
        <div v-if="mensualidadActiva" class="alert-mensualidad">
          <i class="bi bi-calendar-check-fill"></i>
          <div>
            <strong>Abonado Mensual Activo</strong><br>
            {{ mensualidadActiva.nombre_titular }} — Vence: {{ mensualidadActiva.fecha_fin }}
          </div>
        </div>

        <!-- Foto -->
        <label>Foto del Vehículo</label>
        <div class="foto-area" @click="triggerFoto" :class="{ 'foto-cargada': fotoPreview }">
          <img v-if="fotoPreview" :src="fotoPreview" class="foto-preview" />
          <div v-else class="foto-placeholder">
            <i class="bi bi-camera-fill"></i>
            <span>Tomar / Subir Foto</span>
          </div>
          <input ref="fotoInput" type="file" accept="image/*" capture="environment"
                 style="display:none" @change="onFotoChange" />
        </div>
        <button v-if="fotoPreview" class="btn-ghost-sm" @click="fotoPreview = null; form.foto_url = null">
          <i class="bi bi-x-circle"></i> Quitar foto
        </button>

        <button class="btn-pq-primary btn-registrar" :disabled="saving || !form.servicio_id || !form.placa"
                @click="registrar">
          <i class="bi" :class="saving ? 'bi-hourglass-split' : 'bi-box-arrow-in-right'"></i>
          {{ saving ? 'Registrando...' : 'Registrar Ingreso' }}
        </button>
      </div>

      <!-- Panel vehículos activos hoy -->
      <div class="pq-card activos-panel">
        <div class="activos-head">
          <h3 class="card-title"><i class="bi bi-car-front-fill"></i> Activos Hoy ({{ activos.length }})</h3>
          <button class="btn-refresh" @click="cargarActivos" :disabled="loadingActivos">
            <i class="bi bi-arrow-clockwise"></i>
          </button>
        </div>

        <div v-if="loadingActivos" class="pq-loader-sm">Cargando...</div>
        <div v-else-if="!activos.length" class="pq-empty-sm">Sin vehículos activos</div>

        <div v-else class="activos-list">
          <div v-for="v in activos" :key="v.id" class="activo-row" @click="abrirSalida(v)">
            <div class="activo-placa">{{ v.placa }}</div>
            <div class="activo-info">
              <span class="activo-servicio">{{ v.servicio_nombre }}</span>
              <span class="activo-tiempo">{{ formatTiempo(v.hora_ingreso) }}</span>
            </div>
            <div class="activo-valor">${{ (v.valor_actual || 0).toLocaleString() }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal QR / Recibo -->
    <div v-if="modalQR" class="pq-overlay" @click.self="modalQR = false">
      <div class="pq-modal">
        <div class="pq-modal-head">
          <h3><i class="bi bi-check-circle-fill" style="color:#22c55e"></i> Ingreso Registrado</h3>
          <button class="btn-close" @click="modalQR = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="pq-modal-body" style="text-align:center">
          <div class="qr-placa">{{ nuevoIngreso?.placa }}</div>
          <div class="qr-token">Token: <strong>{{ nuevoIngreso?.qr_token }}</strong></div>
          <div class="qr-servicio">{{ servicioSeleccionado?.nombre }}</div>
          <div class="qr-hora">Ingreso: {{ new Date().toLocaleTimeString('es-CO') }}</div>
          <div class="qr-code">
            <i class="bi bi-qr-code" style="font-size:80px;color:#1e3a5f"></i>
            <p style="font-size:12px;color:#64748b">Código QR para salida</p>
          </div>
        </div>
        <div class="pq-modal-foot">
          <button class="btn-pq-ghost" @click="modalQR = false">Cerrar</button>
          <button class="btn-pq-primary" @click="imprimirRecibo">
            <i class="bi bi-printer-fill"></i> Imprimir
          </button>
        </div>
      </div>
    </div>

    <!-- Modal cobro / salida -->
    <div v-if="modalSalida" class="pq-overlay" @click.self="modalSalida = false">
      <div class="pq-modal">
        <div class="pq-modal-head">
          <h3><i class="bi bi-cash-coin" style="color:#f59e0b"></i> Registrar Salida</h3>
          <button class="btn-close" @click="modalSalida = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div v-if="ingresoSeleccionado" class="pq-modal-body">
          <div class="resumen-salida">
            <div class="rs-row"><span>Placa</span><strong>{{ ingresoSeleccionado.placa }}</strong></div>
            <div class="rs-row"><span>Servicio</span><span>{{ ingresoSeleccionado.servicio_nombre }}</span></div>
            <div class="rs-row"><span>Ingreso</span><span>{{ formatFechaHora(ingresoSeleccionado.hora_ingreso) }}</span></div>
            <div class="rs-row"><span>Tiempo</span><span>{{ formatMinutos(ingresoSeleccionado.minutos_transcurridos) }}</span></div>
            <div class="rs-row rs-total"><span>Valor a Cobrar</span><strong>${{ (ingresoSeleccionado.valor_actual || 0).toLocaleString() }}</strong></div>
          </div>

          <label>Forma de Pago</label>
          <select v-model="pagoForm.forma_pago" class="pq-input">
            <option value="efectivo">Efectivo</option>
            <option value="transferencia">Transferencia</option>
            <option value="otro">Otro</option>
          </select>

          <label>Valor Cobrado</label>
          <input type="number" v-model.number="pagoForm.valor_cobrado" class="pq-input" />
        </div>
        <div class="pq-modal-foot">
          <button class="btn-pq-ghost" @click="modalSalida = false">Cancelar</button>
          <button class="btn-pq-primary" :disabled="pagando" @click="confirmarSalida">
            <i class="bi" :class="pagando ? 'bi-hourglass-split' : 'bi-cash-coin'"></i>
            {{ pagando ? 'Procesando...' : 'Confirmar Pago y Salida' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useCompanyStore } from '@/stores/companyStore'
import { useModuleName } from '@/composables/useModuleName'
import { showToast } from '@/utils/toast'
import api from '@/services/apis'

const companyStore = useCompanyStore()
const { moduleName } = useModuleName()
const fotoInput = ref(null)

const servicios = ref([])
const activos = ref([])
const loadingActivos = ref(false)
const saving = ref(false)
const pagando = ref(false)
const modalQR = ref(false)
const modalSalida = ref(false)
const nuevoIngreso = ref(null)
const ingresoSeleccionado = ref(null)
const mensualidadActiva = ref(null)
const fotoPreview = ref(null)

const form = ref({ servicio_id: null, placa: '', foto_url: null })
const pagoForm = ref({ forma_pago: 'efectivo', valor_cobrado: 0 })

const cid = () => companyStore.selectedCompany?.id_company

const servicioSeleccionado = computed(() =>
  servicios.value.find(s => s.id === form.value.servicio_id)
)

const labelTipo = t => ({ tarifa_plana: 'Tarifa Plana', por_minuto: '/min', mensualidad: 'Mensual' }[t] || t)

function formatTiempo(hora) {
  const h = new Date(hora)
  const diff = Math.floor((Date.now() - h) / 60000)
  if (diff < 60) return `${diff} min`
  return `${Math.floor(diff / 60)}h ${diff % 60}min`
}

function formatFechaHora(dt) {
  return new Date(dt).toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' })
}

function formatMinutos(min) {
  if (!min) return '0 min'
  if (min < 60) return `${min} min`
  return `${Math.floor(min / 60)}h ${min % 60}min`
}

async function cargarServicios() {
  try {
    const { data } = await api.get('/api/parqueadero/servicios', { params: { company_id: cid() } })
    servicios.value = data.filter(s => s.is_active && s.tipo_cobro !== 'mensualidad')
  } catch { /* silencioso */ }
}

async function cargarActivos() {
  loadingActivos.value = true
  try {
    const { data } = await api.get('/api/parqueadero/ingresos', { params: { company_id: cid(), estado: 'activo' } })
    activos.value = data
  } catch { /* silencioso */ }
  finally { loadingActivos.value = false }
}

async function buscarMensualidad() {
  if (!form.value.placa || form.value.placa.length < 4) return
  mensualidadActiva.value = null
  try {
    const { data } = await api.get('/api/parqueadero/mensualidades', {
      params: { company_id: cid(), estado: 'activo', q: form.value.placa }
    })
    const match = data.find(m => m.placa === form.value.placa && m.dias_restantes >= 0)
    mensualidadActiva.value = match || null
  } catch { /* silencioso */ }
}

function triggerFoto() { fotoInput.value?.click() }

async function onFotoChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  fotoPreview.value = URL.createObjectURL(file)
  // Subir inmediatamente
  const fd = new FormData()
  fd.append('file', file)
  try {
    const { data } = await api.post('/api/parqueadero/ingresos/foto', fd, {
      params: { company_id: cid() },
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    form.value.foto_url = data.url
  } catch { showToast('Error al subir foto', 'error') }
}

async function registrar() {
  if (!form.value.servicio_id) return showToast('Selecciona un servicio', 'warn')
  if (!form.value.placa.trim()) return showToast('Ingresa la placa', 'warn')
  saving.value = true
  try {
    const { data } = await api.post('/api/parqueadero/ingresos', {
      placa: form.value.placa, servicio_id: form.value.servicio_id, foto_url: form.value.foto_url,
    }, { params: { company_id: cid() } })
    nuevoIngreso.value = data
    modalQR.value = true
    // Reset form
    form.value = { servicio_id: null, placa: '', foto_url: null }
    fotoPreview.value = null
    mensualidadActiva.value = null
    cargarActivos()
  } catch { showToast('Error al registrar ingreso', 'error') }
  finally { saving.value = false }
}

function abrirSalida(v) {
  ingresoSeleccionado.value = v
  pagoForm.value = { forma_pago: 'efectivo', valor_cobrado: v.valor_actual || 0 }
  modalSalida.value = true
}

async function confirmarSalida() {
  pagando.value = true
  try {
    await api.post(`/parqueadero/ingresos/${ingresoSeleccionado.value.id}/pagar`, pagoForm.value, {
      params: { company_id: cid() }
    })
    showToast('Pago registrado — vehículo salió', 'success')
    modalSalida.value = false
    cargarActivos()
  } catch { showToast('Error al registrar pago', 'error') }
  finally { pagando.value = false }
}

function imprimirRecibo() {
  window.print()
}

onMounted(() => {
  cargarServicios()
  cargarActivos()
})
</script>

<style scoped>
.pq-view { padding: 16px; }
.pq-header { margin-bottom: 20px; }
.pq-title { font-size: 20px; font-weight: 700; margin: 0; display: flex; align-items: center; gap: 8px; }

.ingreso-grid {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 16px;
  align-items: start;
}

.pq-card { background: var(--card-bg, #fff); border-radius: 12px; padding: 20px; box-shadow: 0 1px 8px rgba(0,0,0,.07); }
.card-title { font-size: 15px; font-weight: 700; margin: 0 0 16px; display: flex; align-items: center; gap: 7px; }

.ingreso-form { display: flex; flex-direction: column; gap: 10px; }
.ingreso-form label { font-size: 12px; font-weight: 600; color: #475569; }

.pq-input { width: 100%; padding: 9px 12px; border: 1.5px solid var(--border, #e2e8f0); border-radius: 8px; font-size: 14px; background: var(--input-bg, #f8fafc); box-sizing: border-box; }
.pq-input:focus { outline: none; border-color: #3b82f6; }
.pq-input-placa { font-size: 22px; font-weight: 800; letter-spacing: 3px; text-transform: uppercase; }

.alert-mensualidad { background: #d1fae5; border: 1px solid #6ee7b7; border-radius: 8px; padding: 10px 14px; font-size: 13px; color: #065f46; display: flex; align-items: flex-start; gap: 10px; }

.foto-area { border: 2px dashed var(--border, #e2e8f0); border-radius: 10px; min-height: 120px; display: flex; align-items: center; justify-content: center; cursor: pointer; overflow: hidden; transition: border-color .2s; }
.foto-area:hover { border-color: #3b82f6; }
.foto-placeholder { display: flex; flex-direction: column; align-items: center; gap: 6px; color: #94a3b8; font-size: 13px; }
.foto-placeholder i { font-size: 32px; }
.foto-preview { width: 100%; max-height: 200px; object-fit: cover; }

.btn-ghost-sm { background: none; border: 1px solid #e2e8f0; padding: 5px 12px; border-radius: 6px; font-size: 12px; cursor: pointer; color: #64748b; }

.btn-registrar { margin-top: 6px; justify-content: center; padding: 12px; font-size: 15px; }
.btn-pq-primary { background: #3b82f6; color: #fff; border: none; border-radius: 8px; padding: 8px 18px; font-size: 14px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; }
.btn-pq-primary:hover { background: #2563eb; }
.btn-pq-primary:disabled { opacity: .6; cursor: not-allowed; }
.btn-pq-ghost { background: transparent; border: 1.5px solid #94a3b8; color: inherit; border-radius: 8px; padding: 8px 18px; font-size: 14px; cursor: pointer; }

.activos-panel { min-height: 200px; }
.activos-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.btn-refresh { background: none; border: 1px solid var(--border, #e2e8f0); border-radius: 8px; padding: 6px 10px; cursor: pointer; font-size: 16px; }
.pq-loader-sm, .pq-empty-sm { text-align: center; padding: 30px 20px; opacity: .5; font-size: 14px; }
.activos-list { display: flex; flex-direction: column; gap: 8px; }
.activo-row { display: flex; align-items: center; gap: 12px; padding: 10px 14px; border-radius: 10px; border: 1.5px solid var(--border, #e2e8f0); cursor: pointer; transition: background .15s; }
.activo-row:hover { background: #eff6ff; border-color: #93c5fd; }
.activo-placa { font-size: 18px; font-weight: 800; letter-spacing: 2px; min-width: 90px; }
.activo-info { flex: 1; min-width: 0; }
.activo-servicio { display: block; font-size: 12px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.activo-tiempo { font-size: 11px; color: #64748b; }
.activo-valor { font-weight: 700; color: #16a34a; font-size: 15px; white-space: nowrap; }

/* Modal */
.pq-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 16px; }
.pq-modal { background: var(--modal-bg, #fff); border-radius: 14px; width: 100%; max-width: 420px; overflow: hidden; }
.pq-modal-head { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--border, #e2e8f0); }
.pq-modal-head h3 { margin: 0; font-size: 17px; display: flex; align-items: center; gap: 8px; }
.btn-close { background: none; border: none; cursor: pointer; font-size: 18px; color: #64748b; }
.pq-modal-body { padding: 20px; display: flex; flex-direction: column; gap: 12px; }
.pq-modal-foot { display: flex; gap: 10px; justify-content: flex-end; padding: 14px 20px; border-top: 1px solid var(--border, #e2e8f0); }

.qr-placa { font-size: 40px; font-weight: 900; letter-spacing: 4px; margin: 10px 0 4px; }
.qr-token { font-size: 13px; color: #64748b; margin-bottom: 6px; }
.qr-servicio { font-size: 16px; font-weight: 600; }
.qr-hora { font-size: 13px; color: #64748b; margin-top: 4px; }
.qr-code { margin-top: 16px; }

.resumen-salida { background: #f8fafc; border-radius: 10px; padding: 14px; display: flex; flex-direction: column; gap: 8px; }
.rs-row { display: flex; justify-content: space-between; font-size: 14px; }
.rs-row span:first-child { color: #64748b; }
.rs-total { border-top: 1.5px solid #e2e8f0; padding-top: 8px; font-size: 16px; }
.rs-total strong { color: #16a34a; font-size: 20px; }

@media (max-width: 768px) {
  .ingreso-grid { grid-template-columns: 1fr; }
}
@media (max-width: 576px) {
  .pq-view { padding: 10px; }
  .pq-modal { border-radius: 0; max-width: 100%; }
}
</style>
