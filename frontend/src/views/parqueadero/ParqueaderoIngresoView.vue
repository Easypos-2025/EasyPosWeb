<template>
  <div class="pq-view">
    <div class="pq-header">
      <h2 class="pq-title"><i class="bi bi-box-arrow-in-right"></i> {{ moduleName }}</h2>
    </div>

    <div class="ingreso-layout">
      <!-- ══ PASO 1: Seleccionar servicio ══ -->
      <div class="pq-card">
        <h3 class="step-title"><span class="step-num">1</span> Seleccionar Servicio</h3>
        <div v-if="loadingSvcs" class="pq-loader-sm">Cargando servicios...</div>
        <div v-else-if="!servicios.length" class="pq-empty-sm">Sin servicios activos</div>
        <div v-else class="svc-grid">
          <div
            v-for="svc in servicios" :key="svc.id"
            class="svc-card"
            :class="{
              'svc-selected': form.servicio_id === svc.id,
              [`cat-color-${svc.id % 6}`]: true
            }"
            :style="svc.categoria_color ? { '--cat-color': svc.categoria_color } : {}"
            @click="form.servicio_id = svc.id"
          >
            <div class="svc-cat" v-if="svc.categoria_nombre">{{ svc.categoria_nombre }}</div>
            <div class="svc-nombre">{{ svc.nombre }}</div>
            <div class="svc-tipo">{{ labelTipo(svc.tipo_cobro) }}</div>
            <div class="svc-tarifa">{{ resumenTarifa(svc) }}</div>
            <div v-if="form.servicio_id === svc.id" class="svc-check">
              <i class="bi bi-check-circle-fill"></i>
            </div>
          </div>
        </div>
      </div>

      <!-- ══ PASO 2: Datos del vehículo ══ -->
      <div class="pq-card ingreso-form">
        <h3 class="step-title"><span class="step-num">2</span> Datos del Vehículo</h3>

        <!-- Placa con autocomplete -->
        <label class="field-label">Placa *</label>
        <div class="placa-wrap">
          <input
            v-model="form.placa"
            class="pq-input pq-input-placa"
            placeholder="AAA000"
            maxlength="10"
            autocomplete="off"
            @input="onPlacaInput"
            @keydown.down.prevent="sugerenciaIdx = Math.min(sugerenciaIdx + 1, sugerencias.length - 1)"
            @keydown.up.prevent="sugerenciaIdx = Math.max(sugerenciaIdx - 1, 0)"
            @keydown.enter.prevent="seleccionarSugerencia(sugerencias[sugerenciaIdx])"
            @keydown.escape="sugerencias = []"
            @blur="cerrarSugerencias"
          />
          <div v-if="sugerencias.length" class="sugerencias">
            <div
              v-for="(s, i) in sugerencias" :key="s.placa + i"
              class="sugerencia-row"
              :class="{ active: i === sugerenciaIdx }"
              @mousedown.prevent="seleccionarSugerencia(s)"
            >
              <span class="sg-placa">{{ s.placa }}</span>
              <span v-if="s.nombre_titular" class="sg-nombre">{{ s.nombre_titular }}</span>
              <span class="sg-badge" :class="s.origen === 'mensualidad' ? 'badge-men' : 'badge-ing'">
                {{ s.origen === 'mensualidad' ? 'Abonado' : 'Hist.' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Info cliente / mensualidad -->
        <div v-if="clienteInfo" class="cliente-card">
          <img v-if="clienteInfo.foto_url" :src="clienteInfo.foto_url" class="cli-foto" />
          <div class="cli-data">
            <div class="cli-nombre">{{ clienteInfo.nombre_titular || 'Consumidor Final' }}</div>
            <div v-if="clienteInfo.telefono" class="cli-tel"><i class="bi bi-telephone-fill"></i> {{ clienteInfo.telefono }}</div>
            <div v-if="clienteInfo.origen === 'mensualidad'" class="cli-men"><i class="bi bi-calendar-check-fill"></i> Abonado mensual activo</div>
          </div>
        </div>

        <!-- Alerta mensualidad activa -->
        <div v-if="mensualidadActiva" class="alert-mensualidad">
          <i class="bi bi-calendar-check-fill"></i>
          <div>
            <strong>Abonado Mensual Activo</strong><br>
            {{ mensualidadActiva.nombre_titular }} — Vence: {{ mensualidadActiva.fecha_fin }}
          </div>
        </div>

        <!-- Foto -->
        <label class="field-label">Foto del Vehículo</label>
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

        <button
          class="btn-pq-primary btn-registrar"
          :disabled="saving || !form.servicio_id || !form.placa"
          @click="registrar"
        >
          <i class="bi" :class="saving ? 'bi-hourglass-split' : 'bi-box-arrow-in-right'"></i>
          {{ saving ? 'Registrando...' : 'Registrar Ingreso' }}
        </button>
      </div>
    </div>

    <!-- ══ Modal QR / Recibo ══ -->
    <div v-if="modalQR" class="pq-overlay" @click.self="modalQR = false">
      <div class="pq-modal">
        <div class="pq-modal-head">
          <h3><i class="bi bi-check-circle-fill" style="color:#22c55e"></i> Ingreso Registrado</h3>
          <button class="btn-close" @click="modalQR = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="pq-modal-body" style="text-align:center">
          <div class="qr-recibo-label">Nro. Recibo</div>
          <div class="qr-recibo-num">#{{ nuevoIngreso?.id }}</div>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useCompanyStore } from '@/stores/companyStore'
import { useModuleName } from '@/composables/useModuleName'
import { showToast } from '@/utils/toast'
import api from '@/services/apis'

const companyStore = useCompanyStore()
const { moduleName } = useModuleName()
const fotoInput = ref(null)

const servicios     = ref([])
const loadingSvcs   = ref(false)
const saving        = ref(false)
const modalQR       = ref(false)
const nuevoIngreso  = ref(null)
const mensualidadActiva = ref(null)
const fotoPreview   = ref(null)
const clienteInfo   = ref(null)

// Autocomplete placa
const sugerencias   = ref([])
const sugerenciaIdx = ref(0)
let buscarTimer     = null

const form = ref({ servicio_id: null, placa: '', foto_url: null })

const cid = () => companyStore.selectedCompany?.id

const servicioSeleccionado = computed(() =>
  servicios.value.find(s => s.id === form.value.servicio_id)
)

const labelTipo = t => ({
  tarifa_plana: 'Tarifa Plana',
  por_minuto: '/min',
  mensualidad: 'Mensualidad'
}[t] || t)

function resumenTarifa(svc) {
  const fmt = v => `$${Number(v || 0).toLocaleString('es-CO')}`
  if (svc.tipo_cobro === 'tarifa_plana') {
    const base = fmt(svc.tarifa_base)
    const h    = svc.periodo_horas || 12
    return `${base} / ${h}h`
  }
  if (svc.tipo_cobro === 'por_minuto') return `${fmt(svc.tarifa_minuto)} / min`
  return 'Ver al registrar'
}

// ── Autocomplete placa ──────────────────────────────────────────────────────

function onPlacaInput(e) {
  form.value.placa = e.target.value.toUpperCase()
  clienteInfo.value  = null
  mensualidadActiva.value = null
  sugerencias.value  = []
  sugerenciaIdx.value = 0

  if (buscarTimer) clearTimeout(buscarTimer)
  if (form.value.placa.length < 3) return
  buscarTimer = setTimeout(buscarPlaca, 300)
}

async function buscarPlaca() {
  try {
    const { data } = await api.get('/api/parqueadero/vehiculos/buscar', {
      params: { company_id: cid(), q: form.value.placa }
    })
    sugerencias.value  = data
    sugerenciaIdx.value = 0
  } catch { /* silencioso */ }
}

function seleccionarSugerencia(s) {
  if (!s) return
  form.value.placa = s.placa
  sugerencias.value = []
  clienteInfo.value = s.nombre_titular || s.foto_url ? s : null
  if (s.origen === 'mensualidad') verificarMensualidad(s.placa)
}

function cerrarSugerencias() {
  setTimeout(() => { sugerencias.value = [] }, 150)
}

async function verificarMensualidad(placa) {
  mensualidadActiva.value = null
  try {
    const { data } = await api.get('/api/parqueadero/mensualidades', {
      params: { company_id: cid(), estado: 'activo', q: placa }
    })
    const match = data.find(m => m.placa === placa && m.dias_restantes >= 0)
    mensualidadActiva.value = match || null
  } catch { /* silencioso */ }
}

// ── Foto ──────────────────────────────────────────────────────────────────

function triggerFoto() { fotoInput.value?.click() }

async function onFotoChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  fotoPreview.value = URL.createObjectURL(file)
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

// ── Registrar ingreso ──────────────────────────────────────────────────────

async function registrar() {
  if (!form.value.servicio_id) return showToast('Selecciona un servicio', 'warn')
  if (!form.value.placa.trim()) return showToast('Ingresa la placa', 'warn')
  saving.value = true
  try {
    const { data } = await api.post('/api/parqueadero/ingresos', {
      placa:       form.value.placa,
      servicio_id: form.value.servicio_id,
      foto_url:    form.value.foto_url,
    }, { params: { company_id: cid() } })
    nuevoIngreso.value = data
    modalQR.value      = true
    form.value         = { servicio_id: null, placa: '', foto_url: null }
    fotoPreview.value  = null
    clienteInfo.value  = null
    mensualidadActiva.value = null
    sugerencias.value  = []
  } catch { showToast('Error al registrar ingreso', 'error') }
  finally { saving.value = false }
}

function imprimirRecibo() { window.print() }

// ── Carga inicial ──────────────────────────────────────────────────────────

async function cargarServicios() {
  loadingSvcs.value = true
  try {
    const { data } = await api.get('/api/parqueadero/servicios', { params: { company_id: cid() } })
    servicios.value  = data.filter(s => s.is_active && s.tipo_cobro !== 'mensualidad')
  } catch { /* silencioso */ }
  finally { loadingSvcs.value = false }
}

watch(() => companyStore.selectedCompany?.id, id => { if (id) cargarServicios() }, { immediate: true })
</script>

<style scoped>
.pq-view    { padding: 16px; }
.pq-header  { margin-bottom: 20px; }
.pq-title   { font-size: 20px; font-weight: 700; margin: 0; display: flex; align-items: center; gap: 8px; }

/* ── Layout principal ── */
.ingreso-layout {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 16px;
  align-items: start;
}

.pq-card {
  background: var(--card-bg, #fff);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 8px rgba(0,0,0,.07);
}

/* ── Pasos ── */
.step-title {
  font-size: 14px;
  font-weight: 700;
  margin: 0 0 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: .5px;
}
.step-num {
  width: 24px; height: 24px;
  background: #3b82f6;
  color: #fff;
  border-radius: 50%;
  font-size: 13px;
  font-weight: 800;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

/* ── Grilla de servicios ── */
.svc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}

.svc-card {
  position: relative;
  border: 2px solid var(--border, #e2e8f0);
  border-radius: 12px;
  padding: 14px;
  cursor: pointer;
  transition: all .2s;
  background: var(--card-bg, #fff);
  overflow: hidden;
}
.svc-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 4px;
  background: var(--cat-color, #3b82f6);
  opacity: .7;
}
.svc-card:hover { border-color: #93c5fd; background: #eff6ff; transform: translateY(-2px); }
.svc-card.svc-selected {
  border-color: #3b82f6;
  background: #eff6ff;
  box-shadow: 0 0 0 3px rgba(59,130,246,.15);
}
.svc-cat   { font-size: 10px; font-weight: 700; color: var(--cat-color, #3b82f6); text-transform: uppercase; letter-spacing: .5px; margin-bottom: 4px; }
.svc-nombre { font-size: 15px; font-weight: 700; margin-bottom: 4px; line-height: 1.2; }
.svc-tipo  { font-size: 11px; color: #64748b; margin-bottom: 6px; }
.svc-tarifa { font-size: 18px; font-weight: 800; color: #1d4ed8; }
.svc-check {
  position: absolute;
  top: 10px; right: 10px;
  color: #3b82f6;
  font-size: 18px;
}

/* ── Formulario ingreso ── */
.ingreso-form { display: flex; flex-direction: column; gap: 10px; }
.field-label  { font-size: 12px; font-weight: 600; color: #475569; }

.pq-input { width: 100%; padding: 9px 12px; border: 1.5px solid var(--border, #e2e8f0); border-radius: 8px; font-size: 14px; background: var(--input-bg, #f8fafc); box-sizing: border-box; }
.pq-input:focus { outline: none; border-color: #3b82f6; }
.pq-input-placa { font-size: 22px; font-weight: 800; letter-spacing: 3px; text-transform: uppercase; }

/* ── Autocomplete placa ── */
.placa-wrap { position: relative; }
.sugerencias {
  position: absolute;
  top: calc(100% + 4px);
  left: 0; right: 0;
  background: var(--modal-bg, #fff);
  border: 1.5px solid #93c5fd;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,.12);
  z-index: 50;
  overflow: hidden;
}
.sugerencia-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  cursor: pointer;
  transition: background .1s;
}
.sugerencia-row:hover, .sugerencia-row.active { background: #eff6ff; }
.sg-placa  { font-size: 16px; font-weight: 800; letter-spacing: 2px; flex: 1; }
.sg-nombre { font-size: 12px; color: #475569; flex: 2; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sg-badge  { font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 20px; white-space: nowrap; flex-shrink: 0; }
.badge-men { background: #d1fae5; color: #065f46; }
.badge-ing { background: #dbeafe; color: #1e40af; }

/* ── Info cliente ── */
.cliente-card {
  display: flex;
  gap: 12px;
  align-items: center;
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 10px;
  padding: 12px;
}
.cli-foto  { width: 56px; height: 56px; border-radius: 8px; object-fit: cover; flex-shrink: 0; }
.cli-data  { display: flex; flex-direction: column; gap: 3px; }
.cli-nombre { font-weight: 700; font-size: 14px; }
.cli-tel, .cli-men { font-size: 12px; color: #0369a1; display: flex; align-items: center; gap: 5px; }

.alert-mensualidad { background: #d1fae5; border: 1px solid #6ee7b7; border-radius: 8px; padding: 10px 14px; font-size: 13px; color: #065f46; display: flex; align-items: flex-start; gap: 10px; }

/* ── Foto ── */
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

.pq-loader-sm, .pq-empty-sm { text-align: center; padding: 30px 20px; opacity: .5; font-size: 14px; }

/* ── Modal ── */
.pq-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 16px; }
.pq-modal { background: var(--modal-bg, #fff); border-radius: 14px; width: 100%; max-width: 420px; overflow: hidden; }
.pq-modal-head { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--border, #e2e8f0); }
.pq-modal-head h3 { margin: 0; font-size: 17px; display: flex; align-items: center; gap: 8px; }
.btn-close { background: none; border: none; cursor: pointer; font-size: 18px; color: #64748b; }
.pq-modal-body { padding: 20px; display: flex; flex-direction: column; gap: 12px; }
.pq-modal-foot { display: flex; gap: 10px; justify-content: flex-end; padding: 14px 20px; border-top: 1px solid var(--border, #e2e8f0); }

.qr-recibo-label { font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: .5px; margin-top: 10px; }
.qr-recibo-num   { font-size: 28px; font-weight: 900; color: #1e3a5f; letter-spacing: 2px; margin-bottom: 8px; }
.qr-placa   { font-size: 40px; font-weight: 900; letter-spacing: 4px; margin: 4px 0; }
.qr-token   { font-size: 13px; color: #64748b; margin-bottom: 6px; }
.qr-servicio { font-size: 16px; font-weight: 600; }
.qr-hora    { font-size: 13px; color: #64748b; margin-top: 4px; }
.qr-code    { margin-top: 16px; }

/* ── Responsive ── */
@media (max-width: 768px) {
  .ingreso-layout { grid-template-columns: 1fr; }
  .svc-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 576px) {
  .pq-view  { padding: 10px; }
  .svc-grid { grid-template-columns: 1fr; }
  .pq-modal { border-radius: 0; max-width: 100%; }
}
</style>
