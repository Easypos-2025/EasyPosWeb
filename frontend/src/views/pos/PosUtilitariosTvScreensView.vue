<template>
  <div class="crud-view">
    <div class="crud-header">
      <div>
        <h5 class="crud-titulo">Pantallas TV</h5>
        <p class="crud-sub">Gestión de pantallas de cocina por código de acceso</p>
      </div>
      <div class="header-actions">
        <button class="btn-refresh-tv" @click="refrescarPantallas" :disabled="refrescando"
          title="Recargar todas las pantallas TV activas">
          <span v-if="refrescando" class="spinner-border spinner-border-sm me-1"></span>
          <i v-else class="bi bi-arrow-clockwise me-1"></i>
          Recargar pantallas
        </button>
        <button class="btn-nueva" @click="abrirModal()">
          <i class="bi bi-plus-lg me-1"></i>Nueva pantalla
        </button>
      </div>
    </div>

    <!-- Panel: activar dispositivo -->
    <div class="activate-panel">
      <div class="activate-panel__icon"><i class="bi bi-tv"></i></div>
      <div class="activate-panel__body">
        <h6>Activar TV en espera</h6>
        <p>Cuando el TV muestre un código de 4 dígitos, ingrésalo aquí para autorizar esa pantalla.</p>
        <div class="activate-form">
          <input v-model="activateCode" maxlength="4" inputmode="numeric" pattern="[0-9]*"
                 class="code-input" placeholder="0000" @keyup.enter="activarDispositivo" />
          <input v-model="activateName" class="name-input" placeholder="Nombre del TV (ej: Cocina Principal)" />
          <button class="btn-activar" :disabled="activando || activateCode.length !== 4" @click="activarDispositivo">
            <span v-if="activando" class="spinner-border spinner-border-sm me-1"></span>
            <i v-else class="bi bi-check-circle me-1"></i>
            Activar
          </button>
        </div>
        <div v-if="activateMsg" class="activate-msg" :class="activateMsg.ok ? 'activate-msg--ok' : 'activate-msg--err'">
          <i class="bi" :class="activateMsg.ok ? 'bi-check-circle-fill' : 'bi-x-circle-fill'"></i>
          {{ activateMsg.text }}
        </div>
      </div>
    </div>

    <!-- Lista de pantallas -->
    <div v-if="loadingScreens" class="util-loading">
      <div class="spinner-border spinner-border-sm text-primary me-2"></div> Cargando pantallas...
    </div>

    <div v-else-if="!screens.length" class="tv-empty">
      <i class="bi bi-tv tv-empty-icon"></i>
      <p>No hay pantallas configuradas. Crea la primera.</p>
    </div>

    <div v-else class="screens-list">
      <div v-for="s in screens" :key="s.id" class="screen-card">

        <!-- Cabecera pantalla -->
        <div class="screen-card__head">
          <div class="screen-card__info">
            <div class="screen-icon"><i class="bi bi-tv-fill"></i></div>
            <div>
              <div class="screen-name">{{ s.name }}</div>
              <div class="screen-url">
                <span class="url-chip">{{ origin }}/tv/{{ s.screen_code }}</span>
                <button class="btn-copy" @click="copiarURL(s.screen_code)" title="Copiar URL">
                  <i class="bi bi-copy"></i>
                </button>
              </div>
              <div class="screen-printers">
                <span v-if="!s.printer_ids.length" class="chip-all">
                  <i class="bi bi-printer me-1"></i>Todas las secciones
                </span>
                <span v-for="pid in s.printer_ids" :key="pid" class="chip-printer">
                  <i class="bi bi-printer me-1"></i>{{ printerName(pid) }}
                </span>
              </div>
            </div>
          </div>
          <div class="screen-card__actions">
            <span class="badge-status" :class="s.is_active ? 'badge-active' : 'badge-inactive'">
              {{ s.is_active ? 'Activa' : 'Inactiva' }}
            </span>
            <button class="btn-icon" @click="abrirModal(s)" title="Editar">
              <i class="bi bi-pencil"></i>
            </button>
            <button class="btn-icon btn-icon--del" @click="eliminarPantalla(s)" title="Eliminar">
              <i class="bi bi-trash3"></i>
            </button>
          </div>
        </div>

        <!-- Dispositivos -->
        <div class="devices-section">
          <div class="devices-label">
            <i class="bi bi-display me-1"></i>
            {{ s.devices.filter(d => d.is_active).length }} dispositivo(s) activo(s)
          </div>
          <div v-if="s.devices.length" class="devices-list">
            <div v-for="d in s.devices" :key="d.id" class="device-row"
                 :class="{ 'device-row--inactive': !d.is_active }">
              <i class="bi" :class="d.is_active ? 'bi-check-circle-fill text-success' : 'bi-x-circle text-muted'"></i>
              <span class="device-name">{{ d.device_name || 'TV' }}</span>
              <span class="device-date">Activado: {{ fmtDate(d.activated_at) }}</span>
              <span v-if="d.last_seen" class="device-seen">Visto: {{ fmtDate(d.last_seen) }}</span>
              <button v-if="d.is_active" class="btn-revoke" @click="revocarDispositivo(s, d)">
                <i class="bi bi-slash-circle me-1"></i>Revocar
              </button>
            </div>
          </div>
          <div v-else class="no-devices">
            <i class="bi bi-tv me-1"></i>Ningún TV activado aún
          </div>
        </div>

      </div>
    </div>

    <!-- Modal crear/editar pantalla -->
    <div v-if="showModal" class="modal-overlay" @click.self="cerrarModal">
      <div class="modal-box">
        <div class="modal-box__head">
          <h6>{{ editando ? 'Editar pantalla' : 'Nueva pantalla TV' }}</h6>
          <button class="btn-close-modal" @click="cerrarModal"><i class="bi bi-x-lg"></i></button>
        </div>

        <div class="form-group">
          <label>Nombre de la pantalla</label>
          <input v-model="form.name" class="form-control form-control-sm"
                 placeholder="Ej: Cocina Principal, Barra, Parrilla" />
        </div>

        <div class="form-group">
          <label>Impresoras / Secciones</label>
          <div class="printer-option" @click="form.printer_ids = []">
            <span class="radio" :class="{ active: !form.printer_ids.length }"></span>
            <span>Todas las secciones (sin filtro)</span>
          </div>
          <div v-for="p in printers" :key="p.id" class="printer-option"
               @click="togglePrinter(p.id)">
            <span class="checkbox" :class="{ active: form.printer_ids.includes(p.id) }">
              <i v-if="form.printer_ids.includes(p.id)" class="bi bi-check-lg"></i>
            </span>
            <span>{{ p.name }}</span>
          </div>
        </div>

        <div class="modal-box__footer">
          <button class="btn-cancelar" @click="cerrarModal">Cancelar</button>
          <button class="btn-guardar" :disabled="guardando || !form.name.trim()" @click="guardar">
            <span v-if="guardando" class="spinner-border spinner-border-sm me-1"></span>
            {{ editando ? 'Guardar cambios' : 'Crear pantalla' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/apis'
import Swal from 'sweetalert2'
import { showToast } from '@/utils/toast'

const screens      = ref([])
const printers     = ref([])
const loadingScreens = ref(false)
const showModal    = ref(false)
const editando     = ref(null)
const guardando    = ref(false)
const form         = ref({ name: '', printer_ids: [] })

const activateCode = ref('')
const activateName = ref('')
const activando    = ref(false)
const activateMsg  = ref(null)
const refrescando  = ref(false)

const origin = window.location.origin

async function cargarScreens() {
  loadingScreens.value = true
  try {
    const res = await api.get('/api/tv/screens')
    screens.value  = res.data.screens
    printers.value = res.data.printers
  } finally {
    loadingScreens.value = false
  }
}

function printerName(pid) {
  return printers.value.find(p => p.id === pid)?.name || `#${pid}`
}

function fmtDate(val) {
  if (!val) return '—'
  return new Date(val).toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' })
}

function abrirModal(screen = null) {
  editando.value = screen
  form.value = screen
    ? { name: screen.name, printer_ids: [...screen.printer_ids] }
    : { name: '', printer_ids: [] }
  showModal.value = true
}

function cerrarModal() { showModal.value = false }

function togglePrinter(pid) {
  const idx = form.value.printer_ids.indexOf(pid)
  if (idx === -1) form.value.printer_ids.push(pid)
  else form.value.printer_ids.splice(idx, 1)
}

async function guardar() {
  if (!form.value.name.trim()) return
  guardando.value = true
  try {
    if (editando.value) {
      await api.put(`/api/tv/screens/${editando.value.id}`, form.value)
    } else {
      await api.post('/api/tv/screens', form.value)
    }
    cerrarModal()
    await cargarScreens()
  } finally {
    guardando.value = false
  }
}

async function eliminarPantalla(s) {
  const result = await Swal.fire({
    title: '¿Eliminar pantalla?',
    text: `¿Eliminar la pantalla "${s.name}" y todos sus dispositivos?`,
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#e11d48',
    confirmButtonText: 'Sí, eliminar',
    cancelButtonText: 'Cancelar',
  })
  if (!result.isConfirmed) return
  await api.delete(`/api/tv/screens/${s.id}`)
  await cargarScreens()
}

async function revocarDispositivo(screen, device) {
  const result = await Swal.fire({
    title: '¿Revocar acceso?',
    text: `¿Revocar acceso a "${device.device_name || 'TV'}"?`,
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#2563eb',
    confirmButtonText: 'Sí, revocar',
    cancelButtonText: 'Cancelar',
  })
  if (!result.isConfirmed) return
  await api.delete(`/api/tv/screens/${screen.id}/devices/${device.id}`)
  await cargarScreens()
}

async function activarDispositivo() {
  if (activateCode.value.length !== 4) return
  activando.value = true
  activateMsg.value = null
  try {
    await api.post('/api/tv/activate', {
      code: activateCode.value,
      device_name: activateName.value || 'TV',
    })
    activateMsg.value = { ok: true, text: 'Dispositivo activado correctamente. El TV ya puede mostrar los pedidos.' }
    activateCode.value = ''
    activateName.value = ''
    await cargarScreens()
  } catch (e) {
    activateMsg.value = { ok: false, text: e.response?.data?.detail || 'Código inválido o expirado' }
  } finally {
    activando.value = false
  }
}

async function refrescarPantallas() {
  refrescando.value = true
  try {
    await api.post('/api/tv/screens/force-refresh')
    window.Swal?.fire({
      title: 'Señal enviada',
      text: 'Todas las pantallas TV activas se recargarán en los próximos segundos.',
      icon: 'success',
      timer: 2500,
      showConfirmButton: false,
    })
  } catch {
    showToast('No se pudo enviar la señal de recarga.', 'error', 3000)
  } finally {
    refrescando.value = false
  }
}

function copiarURL(code) {
  navigator.clipboard?.writeText(`${origin}/tv/${code}`)
    .then(() => showToast('URL copiada al portapapeles', 'success', 2000))
    .catch(() => showToast(`URL: ${origin}/tv/${code}`, 'info', 2000))
}

onMounted(cargarScreens)
</script>

<style scoped>
/* ── Header actions ── */
.header-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }

.btn-refresh-tv {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 16px; border-radius: 8px; border: 1.5px solid #0369a1;
  background: #e0f2fe; color: #0369a1; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: background .15s, color .15s; white-space: nowrap;
}
.btn-refresh-tv:hover:not(:disabled) { background: #0369a1; color: #fff; }
.btn-refresh-tv:disabled { opacity: .55; cursor: not-allowed; }

/* ── Panel activación ── */
.activate-panel {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
  padding: 20px 24px; display: flex; gap: 16px; align-items: flex-start;
  margin-bottom: 20px;
}
.activate-panel__icon {
  width: 48px; height: 48px; border-radius: 10px;
  background: #dbeafe; display: flex; align-items: center; justify-content: center;
  font-size: 1.5rem; color: #2563eb; flex-shrink: 0;
}
.activate-panel__body { flex: 1; }
.activate-panel__body h6 { font-weight: 700; margin-bottom: 4px; font-size: .92rem; }
.activate-panel__body p  { font-size: .82rem; color: #64748b; margin-bottom: 10px; }

.activate-form { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.code-input {
  width: 90px; text-align: center; font-size: 1.6rem; font-weight: 700;
  letter-spacing: 6px; border: 2px solid #cbd5e1; border-radius: 8px;
  padding: 6px 10px; outline: none;
}
.code-input:focus { border-color: #3b82f6; }
.name-input {
  flex: 1; min-width: 180px; border: 1px solid #cbd5e1; border-radius: 8px;
  padding: 8px 12px; font-size: .88rem; outline: none;
}
.name-input:focus { border-color: #3b82f6; }

.btn-activar {
  background: #22c55e; color: #fff; border: none; border-radius: 8px;
  padding: 9px 20px; font-size: .88rem; font-weight: 600; cursor: pointer;
  display: flex; align-items: center; white-space: nowrap; transition: background .15s;
}
.btn-activar:hover:not(:disabled) { background: #16a34a; }
.btn-activar:disabled { opacity: .6; cursor: not-allowed; }

.activate-msg {
  margin-top: 10px; font-size: .84rem; display: flex; align-items: center; gap: 6px;
  padding: 8px 12px; border-radius: 8px;
}
.activate-msg--ok  { background: #d1fae5; color: #065f46; }
.activate-msg--err { background: #fee2e2; color: #991b1b; }

/* ── Empty ── */
.tv-empty {
  display: flex; flex-direction: column; align-items: center; padding: 48px 16px;
  color: #94a3b8;
}
.tv-empty-icon { font-size: 3rem; margin-bottom: 12px; }

/* ── Botón nueva pantalla ── */
.btn-nueva {
  background: #3b82f6; color: #fff; border: none; border-radius: 8px;
  padding: 9px 18px; font-size: .88rem; font-weight: 600; cursor: pointer;
  display: flex; align-items: center; white-space: nowrap;
}
.btn-nueva:hover { background: #2563eb; }

/* ── Screen cards ── */
.screens-list { display: flex; flex-direction: column; gap: 12px; }

.screen-card {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;
}
.screen-card__head {
  display: flex; align-items: flex-start; gap: 12px; padding: 16px 20px;
  justify-content: space-between;
}
.screen-card__info { display: flex; gap: 14px; align-items: flex-start; flex: 1; min-width: 0; }

.screen-icon {
  width: 44px; height: 44px; border-radius: 10px;
  background: #eff6ff; display: flex; align-items: center; justify-content: center;
  font-size: 1.3rem; color: #3b82f6; flex-shrink: 0;
}

.screen-name { font-weight: 700; font-size: .95rem; color: #1e293b; margin-bottom: 4px; }
.screen-url  { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }
.url-chip {
  font-size: .78rem; background: #f1f5f9; color: #1e40af;
  padding: 2px 8px; border-radius: 6px; font-family: monospace;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 320px;
}

.btn-copy {
  background: none; border: none; cursor: pointer; color: #64748b; font-size: .85rem;
  padding: 2px 4px; border-radius: 4px; transition: color .1s;
}
.btn-copy:hover { color: #3b82f6; }

.screen-printers { display: flex; flex-wrap: wrap; gap: 6px; }
.chip-all { font-size: .76rem; background: #f0fdf4; color: #166534; padding: 2px 8px; border-radius: 20px; }
.chip-printer { font-size: .76rem; background: #eff6ff; color: #1e40af; padding: 2px 8px; border-radius: 20px; }

.screen-card__actions { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.badge-status { font-size: .72rem; font-weight: 700; padding: 3px 10px; border-radius: 20px; }
.badge-active   { background: #d1fae5; color: #065f46; }
.badge-inactive { background: #f1f5f9; color: #64748b; }

.btn-icon {
  background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 8px;
  width: 34px; height: 34px; display: flex; align-items: center; justify-content: center;
  cursor: pointer; font-size: .9rem; color: #475569; transition: background .1s;
}
.btn-icon:hover { background: #e2e8f0; }
.btn-icon--del:hover { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }

/* ── Devices ── */
.devices-section {
  border-top: 1px solid #f1f5f9; padding: 12px 20px;
  background: #fafbfc;
}
.devices-label { font-size: .78rem; font-weight: 600; color: #64748b; margin-bottom: 8px; }
.devices-list { display: flex; flex-direction: column; gap: 6px; }
.device-row {
  display: flex; align-items: center; gap: 10px; font-size: .82rem;
  padding: 6px 10px; background: #fff; border: 1px solid #e2e8f0;
  border-radius: 8px; flex-wrap: wrap;
}
.device-row--inactive { opacity: .6; }
.device-name { font-weight: 600; color: #374151; flex: 1; min-width: 100px; }
.device-date { color: #64748b; font-size: .75rem; white-space: nowrap; }
.device-seen { color: #94a3b8; font-size: .75rem; white-space: nowrap; }

.btn-revoke {
  background: #fee2e2; color: #dc2626; border: none; border-radius: 6px;
  padding: 3px 10px; font-size: .74rem; font-weight: 600; cursor: pointer;
  display: flex; align-items: center; white-space: nowrap; transition: background .1s;
}
.btn-revoke:hover { background: #fca5a5; }
.no-devices { font-size: .8rem; color: #94a3b8; }

/* ── Modal ── */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.4);
  display: flex; align-items: center; justify-content: center; z-index: 9999;
}
.modal-box {
  background: #fff; border-radius: 14px; padding: 24px;
  max-width: 480px; width: 92%; box-shadow: 0 20px 60px rgba(0,0,0,.2);
}
.modal-box__head {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;
}
.modal-box__head h6 { font-weight: 700; font-size: 1rem; margin: 0; }
.btn-close-modal {
  background: none; border: none; cursor: pointer; font-size: 1rem; color: #64748b;
}

.form-group { margin-bottom: 16px; }
.form-group label { font-size: .8rem; font-weight: 600; color: #475569; margin-bottom: 6px; display: block; }

.printer-option {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 10px; border-radius: 8px; cursor: pointer;
  transition: background .1s; font-size: .88rem;
}
.printer-option:hover { background: #f8fafc; }

.radio {
  width: 18px; height: 18px; border-radius: 50%; border: 2px solid #cbd5e1;
  flex-shrink: 0; transition: border-color .1s;
}
.radio.active { border-color: #3b82f6; background: #3b82f6; }

.checkbox {
  width: 18px; height: 18px; border-radius: 4px; border: 2px solid #cbd5e1;
  flex-shrink: 0; display: flex; align-items: center; justify-content: center;
  font-size: .7rem; color: #fff; transition: background .1s, border-color .1s;
}
.checkbox.active { background: #3b82f6; border-color: #3b82f6; }

.modal-box__footer {
  display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px;
}
.btn-cancelar { padding: 9px 20px; border: 1px solid #d1d5db; border-radius: 8px; background: #fff; cursor: pointer; font-size: .88rem; }
.btn-guardar  { padding: 9px 20px; border: none; border-radius: 8px; background: #3b82f6; color: #fff; font-weight: 600; cursor: pointer; font-size: .88rem; display: flex; align-items: center; }
.btn-guardar:hover:not(:disabled) { background: #2563eb; }
.btn-guardar:disabled { opacity: .6; cursor: not-allowed; }

/* ── Responsive ── */
@media (max-width: 768px) {
  .activate-panel { flex-direction: column; }
  .activate-form { flex-direction: column; align-items: stretch; }
  .code-input { width: 100%; }
  .screen-card__head { flex-direction: column; gap: 10px; }
  .screen-card__actions { width: 100%; justify-content: flex-end; }
  .url-chip { max-width: 220px; }
  .device-row { gap: 6px; }
}

@media (max-width: 576px) {
  .activate-panel { padding: 14px; }
  .screen-card__head { padding: 12px; }
  .devices-section { padding: 10px 12px; }
  .device-date, .device-seen { display: none; }
}
</style>
