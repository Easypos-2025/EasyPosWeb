<template>
  <div class="tpv-cfg">
    <div class="tpv-cfg__header">
      <i class="bi bi-gear-fill tpv-cfg__header-icon"></i>
      <div>
        <h1 class="tpv-cfg__title">Configuración TPV</h1>
        <p class="tpv-cfg__sub">Gestión de vendedores y configuración de conexión</p>
      </div>
    </div>

    <!-- ── Sección empleados ───────────────────────────────────────── -->
    <div class="tpv-cfg__card">
      <div class="tpv-cfg__card-head">
        <h2 class="tpv-cfg__section-title">
          <i class="bi bi-people-fill me-2"></i>Vendedores / Meseros
        </h2>
        <button class="btn-tpv-primary" @click="openNew">
          <i class="bi bi-plus-lg"></i> Nuevo
        </button>
      </div>

      <div v-if="loading" class="tpv-cfg__loading">
        <div class="spinner-border spinner-border-sm text-primary"></div>
      </div>

      <div v-else-if="loadError" class="tpv-cfg__empty">
        <i class="bi bi-exclamation-triangle-fill fs-1 text-danger"></i>
        <p class="mt-2 text-danger">{{ loadError }}</p>
        <button class="btn-tpv-secondary mt-2" @click="loadEmpleados">Reintentar</button>
      </div>

      <div v-else-if="!empleados.length" class="tpv-cfg__empty">
        <i class="bi bi-person-x fs-1 text-muted"></i>
        <p class="mt-2 text-muted">No hay vendedores registrados</p>
      </div>

      <div v-else class="tpv-cfg__table-wrap">
        <table class="tpv-table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Teléfono</th>
              <th class="text-center">Estado</th>
              <th class="text-center">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="emp in empleados" :key="emp.id">
              <td>
                <i class="bi bi-person-circle me-2 text-muted"></i>{{ emp.name }}
                <span v-if="emp.plan_blocked" class="badge-blocked ms-2">Bloqueado</span>
              </td>
              <td class="text-muted">{{ emp.phone || '—' }}</td>
              <td class="text-center">
                <button
                  class="badge-status"
                  :class="emp.status === 1 ? 'badge-status--on' : 'badge-status--off'"
                  :disabled="emp.plan_blocked"
                  @click="toggleStatus(emp)"
                  :title="emp.status === 1 ? 'Clic para desactivar' : 'Clic para activar'"
                >
                  {{ emp.status === 1 ? 'Activo' : 'Inactivo' }}
                </button>
              </td>
              <td class="text-center">
                <button class="btn-icon" title="Editar" @click="openEdit(emp)">
                  <i class="bi bi-pencil-fill"></i>
                </button>
                <button class="btn-icon btn-icon--danger" title="Eliminar" @click="confirmDelete(emp)">
                  <i class="bi bi-trash3-fill"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── Enlace para meseros ──────────────────────────────────────── -->
    <div class="tpv-cfg__card">
      <div class="tpv-cfg__card-head">
        <h2 class="tpv-cfg__section-title">
          <i class="bi bi-share-fill me-2"></i>Enlace de acceso para meseros
        </h2>
      </div>
      <p class="tpv-cfg__share-desc">
        Comparte este enlace con tus vendedores o meseros para que accedan al sistema de toma de pedidos desde cualquier dispositivo con navegador.
      </p>
      <div class="tpv-cfg__url-box">
        <span class="tpv-cfg__url-text">{{ tpvLoginUrl }}</span>
        <button
          class="btn-tpv-copy"
          :class="{ 'btn-tpv-copy--copied': copied }"
          @click="copyUrl"
          :title="copied ? '¡Copiado!' : 'Copiar enlace'"
        >
          <i :class="copied ? 'bi bi-check-lg' : 'bi bi-clipboard'"></i>
          {{ copied ? 'Copiado' : 'Copiar' }}
        </button>
      </div>
    </div>

    <!-- ── Estilo de tarjetas de mesa ───────────────────────────── -->
    <div class="tpv-cfg__card">
      <div class="tpv-cfg__card-head">
        <h2 class="tpv-cfg__section-title">
          <i class="bi bi-palette-fill me-2"></i>Estilo de tarjetas de mesa
        </h2>
      </div>
      <p class="tpv-cfg__share-desc">
        Elige cómo se visualizan las mesas/cuentas abiertas en el dashboard y en la pantalla de toma de pedidos.
      </p>
      <div class="card-style-grid">
        <button
          v-for="s in CARD_STYLES"
          :key="s.key"
          class="card-style-opt"
          :class="{ 'card-style-opt--active': selectedCardStyle === s.key }"
          @click="pickStyle(s.key)"
        >
          <!-- Preview real del estilo de tarjeta -->
          <div class="cso-preview">
            <div class="cso-preview__inner">
              <AccountOrderCard
                :order="previewOrder"
                :card-style="s.key"
                currency="COP"
                :show-delete="false"
              />
            </div>
          </div>
          <span class="card-style-opt__label">{{ s.label }}</span>
          <i v-if="selectedCardStyle === s.key" class="bi bi-check-circle-fill card-style-opt__check"></i>
          <span v-if="savingStyle === s.key" class="spinner-border spinner-border-sm card-style-opt__spinner"></span>
        </button>
      </div>
    </div>

    <!-- ── Sección conexión ───────────────────────────────────────── -->
    <div class="tpv-cfg__card">
      <div class="tpv-cfg__card-head">
        <h2 class="tpv-cfg__section-title">
          <i class="bi bi-wifi me-2"></i>Configuración de conexión
        </h2>
      </div>
      <div class="tpv-cfg__conn">
        <div class="tpv-cfg__conn-row">
          <span class="tpv-cfg__conn-label">Modo actual</span>
          <span class="badge-mode" :class="localUrlSet ? 'badge-mode--local' : 'badge-mode--web'">
            <i :class="localUrlSet ? 'bi bi-hdd-fill' : 'bi bi-cloud-fill'" class="me-1"></i>
            {{ localUrlSet ? 'Local' : 'Web (easyposweb.com)' }}
          </span>
        </div>
        <div class="tpv-cfg__conn-row">
          <span class="tpv-cfg__conn-label">URL del servidor</span>
          <span class="tpv-cfg__conn-url">{{ currentApiUrl }}</span>
        </div>
        <div class="tpv-cfg__conn-info">
          <i class="bi bi-info-circle me-1"></i>
          La URL local se configura desde el instalador <strong>EasyPosLocal</strong> (disponible en Fase 3).
          En modo web siempre se conecta a easyposweb.com.
        </div>
        <div v-if="localUrlSet" class="mt-3">
          <button class="btn-tpv-secondary" @click="clearLocalUrl">
            <i class="bi bi-arrow-counterclockwise me-1"></i> Volver a modo web
          </button>
        </div>
      </div>
    </div>

    <!-- ── Modal empleado ─────────────────────────────────────────── -->
    <div v-if="modal.open" class="tpv-modal-backdrop" @click.self="closeModal">
      <div class="tpv-modal">
        <div class="tpv-modal__head">
          <h3>{{ modal.editing ? 'Editar vendedor' : 'Nuevo vendedor' }}</h3>
          <button class="tpv-modal__close" @click="closeModal"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="tpv-modal__body">
          <div class="tpv-field">
            <label>Nombre *</label>
            <input v-model="form.name" class="tpv-input" placeholder="Nombre del vendedor" maxlength="50" />
          </div>
          <div class="tpv-field">
            <label>Teléfono</label>
            <input v-model="form.phone" class="tpv-input" placeholder="Opcional" maxlength="50" />
          </div>
          <div class="tpv-field">
            <label>PIN {{ modal.editing ? '(dejar vacío para no cambiar)' : '*' }}</label>
            <input v-model="form.password" class="tpv-input" type="password" placeholder="PIN numérico" maxlength="10" />
          </div>
          <p v-if="modal.error" class="tpv-modal__error">{{ modal.error }}</p>
        </div>
        <div class="tpv-modal__foot">
          <button class="btn-tpv-secondary" @click="closeModal">Cancelar</button>
          <button class="btn-tpv-primary" @click="saveEmpleado" :disabled="modal.saving">
            <span v-if="modal.saving" class="spinner-border spinner-border-sm me-1"></span>
            Guardar
          </button>
        </div>
      </div>
    </div>

    <!-- ── Confirm delete ─────────────────────────────────────────── -->
    <div v-if="delTarget" class="tpv-modal-backdrop" @click.self="delTarget = null">
      <div class="tpv-modal tpv-modal--sm">
        <div class="tpv-modal__head">
          <h3>Eliminar vendedor</h3>
          <button class="tpv-modal__close" @click="delTarget = null"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="tpv-modal__body">
          <p>¿Eliminar a <strong>{{ delTarget.name }}</strong>? Esta acción no se puede deshacer.</p>
        </div>
        <div class="tpv-modal__foot">
          <button class="btn-tpv-secondary" @click="delTarget = null">Cancelar</button>
          <button class="btn-tpv-danger" @click="deleteEmpleado" :disabled="deleting">
            <span v-if="deleting" class="spinner-border spinner-border-sm me-1"></span>
            Eliminar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/apis'
import { useCardStyle, CARD_STYLES } from '@/composables/useCardStyle'
import AccountOrderCard from '@/components/comanda/AccountOrderCard.vue'
import { showToast } from '@/utils/toast'

const previewOrder = {
  name: 'Mesa 5',
  amount: 45000,
  order_time: '14:30',
  waiter_name: 'Carlos',
  daily_seq: 5,
  status: 'occupied',
}

const { cardStyle: selectedCardStyle, load: loadStyle, save: saveStyle } = useCardStyle()
const savingStyle = ref(null)

async function pickStyle(key) {
  if (savingStyle.value) return
  savingStyle.value = key
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    await saveStyle(key, user.company_id || undefined)
  } catch (err) {
    showToast(err.response?.data?.detail || 'No se pudo guardar el estilo de tarjeta', 'error', 3500)
  } finally {
    savingStyle.value = null
  }
}

const empleados  = ref([])
const loading    = ref(false)
const loadError  = ref('')
const delTarget  = ref(null)
const deleting   = ref(false)

const modal = ref({ open: false, editing: false, editId: null, error: '', saving: false })
const form  = ref({ name: '', phone: '', password: '' })

const currentApiUrl = computed(() => localStorage.getItem('tpv_api_url') || import.meta.env.VITE_API_URL)
const localUrlSet   = computed(() => !!localStorage.getItem('tpv_api_url'))

const copied = ref(false)

const tpvLoginUrl = computed(() => {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const cid  = user.company_id || ''
    const base = window.location.origin
    return cid ? `${base}/pos/tpv/login?cid=${cid}` : `${base}/pos/tpv/login`
  } catch {
    return `${window.location.origin}/pos/tpv/login`
  }
})

async function copyUrl() {
  try {
    await navigator.clipboard.writeText(tpvLoginUrl.value)
  } catch {
    const el = document.createElement('textarea')
    el.value = tpvLoginUrl.value
    el.style.position = 'fixed'
    el.style.opacity  = '0'
    document.body.appendChild(el)
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
  }
  copied.value = true
  setTimeout(() => { copied.value = false }, 2500)
}

async function loadEmpleados() {
  loading.value = true
  loadError.value = ''
  try {
    const res = await api.get('/api/pos/tpv/config/empleados')
    empleados.value = res.data
  } catch (e) {
    empleados.value = []
    loadError.value = e?.response?.data?.detail || `Error ${e?.response?.status || ''}: no se pudo cargar la lista`
  } finally {
    loading.value = false
  }
}

function openNew() {
  form.value = { name: '', phone: '', password: '' }
  modal.value = { open: true, editing: false, editId: null, error: '', saving: false }
}

function openEdit(emp) {
  form.value = { name: emp.name, phone: emp.phone || '', password: '' }
  modal.value = { open: true, editing: true, editId: emp.id, error: '', saving: false }
}

function closeModal() {
  modal.value.open = false
}

async function saveEmpleado() {
  const name = form.value.name.trim()
  const pin  = form.value.password.trim()
  if (!name) { modal.value.error = 'El nombre es obligatorio'; return }
  if (!modal.value.editing && !pin) { modal.value.error = 'El PIN es obligatorio'; return }

  modal.value.saving = true
  modal.value.error  = ''
  try {
    if (modal.value.editing) {
      await api.put(`/api/pos/tpv/config/empleados/${modal.value.editId}`, form.value)
    } else {
      await api.post('/api/pos/tpv/config/empleados', form.value)
    }
    closeModal()
    await loadEmpleados()
  } catch (e) {
    modal.value.error = e?.response?.data?.detail || 'Error al guardar'
  } finally {
    modal.value.saving = false
  }
}

function confirmDelete(emp) {
  delTarget.value = emp
}

async function deleteEmpleado() {
  deleting.value = true
  try {
    await api.delete(`/api/pos/tpv/config/empleados/${delTarget.value.id}`)
    delTarget.value = null
    await loadEmpleados()
  } catch (e) {
    alert(e?.response?.data?.detail || 'Error al eliminar')
  } finally {
    deleting.value = false
  }
}

async function toggleStatus(emp) {
  try {
    const res = await api.patch(`/api/pos/tpv/config/empleados/${emp.id}/status`)
    emp.status = res.data.status
  } catch (e) {
    alert(e?.response?.data?.detail || 'Error al cambiar estado')
  }
}

function clearLocalUrl() {
  localStorage.removeItem('tpv_api_url')
}

onMounted(async () => {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  await Promise.all([loadEmpleados(), loadStyle(user.company_id || undefined)])
})
</script>

<style scoped>
.tpv-cfg {
  max-width: 860px;
  margin: 0 auto;
  padding: 1.5rem 1rem 3rem;
}

/* Header */
.tpv-cfg__header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}
.tpv-cfg__header-icon {
  font-size: 2rem;
  color: var(--bs-primary, #0d6efd);
}
.tpv-cfg__title  { font-size: 1.4rem; font-weight: 700; margin: 0; }
.tpv-cfg__sub    { font-size: .85rem; color: #6c757d; margin: 0; }

/* Cards */
.tpv-cfg__card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 1.25rem;
  margin-bottom: 1.25rem;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
}
.tpv-cfg__card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}
.tpv-cfg__section-title { font-size: 1rem; font-weight: 600; margin: 0; }
.tpv-cfg__loading { text-align: center; padding: 2rem; }
.tpv-cfg__empty   { text-align: center; padding: 2rem; }

/* Table */
.tpv-cfg__table-wrap { overflow-x: auto; }
.tpv-table { width: 100%; border-collapse: collapse; font-size: .9rem; }
.tpv-table th {
  background: #f8fafc;
  padding: .6rem .9rem;
  text-align: left;
  font-weight: 600;
  color: #475569;
  border-bottom: 2px solid #e2e8f0;
  white-space: nowrap;
}
.tpv-table td {
  padding: .65rem .9rem;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}
.tpv-table tr:last-child td { border-bottom: none; }

/* Badges */
.badge-status {
  border: none;
  border-radius: 999px;
  padding: .25rem .75rem;
  font-size: .78rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity .15s;
}
.badge-status:disabled { opacity: .5; cursor: default; }
.badge-status--on  { background: #dcfce7; color: #166534; }
.badge-status--off { background: #fee2e2; color: #991b1b; }
.badge-blocked     { background: #fef3c7; color: #92400e; border-radius: 999px; padding: .15rem .5rem; font-size: .72rem; font-weight: 600; }

/* Connection section */
.tpv-cfg__conn { display: flex; flex-direction: column; gap: .75rem; }
.tpv-cfg__conn-row { display: flex; align-items: center; gap: .75rem; flex-wrap: wrap; }
.tpv-cfg__conn-label { font-weight: 600; font-size: .88rem; min-width: 140px; color: #475569; }
.tpv-cfg__conn-url   { font-family: monospace; font-size: .85rem; color: #334155; }
.tpv-cfg__conn-info  { font-size: .82rem; color: #64748b; background: #f8fafc; border-radius: 8px; padding: .7rem 1rem; border-left: 3px solid #cbd5e1; }
.badge-mode { border-radius: 999px; padding: .3rem .9rem; font-size: .82rem; font-weight: 600; }
.badge-mode--web   { background: #dbeafe; color: #1e40af; }
.badge-mode--local { background: #fef9c3; color: #854d0e; }

/* Icon buttons */
.btn-icon {
  background: none;
  border: 1px solid #e2e8f0;
  border-radius: 7px;
  padding: .3rem .5rem;
  cursor: pointer;
  color: #475569;
  margin: 0 .15rem;
  transition: background .15s;
}
.btn-icon:hover         { background: #f1f5f9; }
.btn-icon--danger       { color: #dc3545; }
.btn-icon--danger:hover { background: #fee2e2; border-color: #fecaca; }

/* Primary / secondary / danger buttons */
.btn-tpv-primary {
  background: #0d6efd;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: .45rem 1rem;
  font-size: .88rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: .4rem;
  transition: background .15s;
}
.btn-tpv-primary:hover    { background: #0b5ed7; }
.btn-tpv-primary:disabled { opacity: .6; cursor: default; }

.btn-tpv-secondary {
  background: #f1f5f9;
  color: #334155;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: .45rem 1rem;
  font-size: .88rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: .4rem;
}
.btn-tpv-secondary:hover { background: #e2e8f0; }

.btn-tpv-danger {
  background: #dc3545;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: .45rem 1rem;
  font-size: .88rem;
  font-weight: 600;
  cursor: pointer;
}
.btn-tpv-danger:disabled { opacity: .6; cursor: default; }

/* Modal */
.tpv-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.45);
  z-index: 1050;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}
.tpv-modal {
  background: #fff;
  border-radius: 14px;
  width: 100%;
  max-width: 440px;
  box-shadow: 0 20px 60px rgba(0,0,0,.25);
}
.tpv-modal--sm { max-width: 360px; }
.tpv-modal__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e2e8f0;
}
.tpv-modal__head h3 { margin: 0; font-size: 1rem; font-weight: 700; }
.tpv-modal__close {
  background: none;
  border: none;
  font-size: 1.1rem;
  color: #64748b;
  cursor: pointer;
}
.tpv-modal__body { padding: 1.25rem; display: flex; flex-direction: column; gap: .85rem; }
.tpv-modal__foot {
  padding: 1rem 1.25rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  gap: .75rem;
  justify-content: flex-end;
}
.tpv-modal__error { color: #dc3545; font-size: .85rem; margin: 0; }

.tpv-field { display: flex; flex-direction: column; gap: .3rem; }
.tpv-field label { font-size: .83rem; font-weight: 600; color: #475569; }
.tpv-input {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: .5rem .75rem;
  font-size: .9rem;
  width: 100%;
  outline: none;
  transition: border-color .15s;
}
.tpv-input:focus { border-color: #0d6efd; }

/* Share URL */
.tpv-cfg__share-desc {
  font-size: .87rem;
  color: #64748b;
  margin: 0 0 .85rem;
}

.tpv-cfg__url-box {
  display: flex;
  align-items: center;
  gap: .75rem;
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  padding: .65rem 1rem;
  flex-wrap: wrap;
}

.tpv-cfg__url-text {
  flex: 1;
  font-family: monospace;
  font-size: .85rem;
  color: #334155;
  word-break: break-all;
  min-width: 0;
}

.btn-tpv-copy {
  background: #0d6efd;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: .4rem .9rem;
  font-size: .85rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: .4rem;
  white-space: nowrap;
  flex-shrink: 0;
  transition: background .15s;
}
.btn-tpv-copy:hover        { background: #0b5ed7; }
.btn-tpv-copy--copied      { background: #16a34a; }
.btn-tpv-copy--copied:hover { background: #15803d; }

/* Responsive */
@media (max-width: 768px) {
  .tpv-cfg { padding: 1rem .75rem 3rem; }
  .tpv-cfg__conn-label { min-width: unset; width: 100%; }
  .tpv-table th:nth-child(2),
  .tpv-table td:nth-child(2) { display: none; }
}
@media (max-width: 576px) {
  .tpv-cfg__header { flex-direction: column; align-items: flex-start; gap: .5rem; }
  .tpv-cfg__card   { padding: 1rem .75rem; }
  .tpv-modal { max-width: 100%; border-radius: 14px 14px 0 0; align-self: flex-end; }
  .tpv-modal-backdrop { align-items: flex-end; }
}

/* ── Selector de estilo de tarjeta ── */
.card-style-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-top: 4px;
}
.card-style-opt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 12px 10px 14px;
  border: 2px solid #e2e8f0;
  border-radius: 14px;
  background: #f8fafc;
  cursor: pointer;
  text-align: center;
  position: relative;
  transition: all .15s;
}
.card-style-opt:hover { border-color: #93c5fd; background: #eff6ff; }
.card-style-opt--active { border-color: #2563eb; background: #dbeafe; }

/* Contenedor de la preview real del componente */
.cso-preview {
  width: 100%;
  height: 155px;
  position: relative;
  overflow: hidden;
  border-radius: 10px;
  background: #e9eef5;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}
.cso-preview__inner {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) scale(0.62);
  transform-origin: center center;
  pointer-events: none;
}
/* Congelar hover-animations dentro de la preview */
.cso-preview :deep(.aoc-oval),
.cso-preview :deep(.aoc) {
  transition: none !important;
  cursor: default;
}
.cso-preview :deep(.aoc-oval:hover),
.cso-preview :deep(.aoc:hover) {
  transform: none !important;
  box-shadow: inherit;
}

.card-style-opt__label {
  font-size: .85rem;
  font-weight: 700;
  color: #1e293b;
}
.card-style-opt--active .card-style-opt__label { color: #1d4ed8; }

.card-style-opt__check {
  position: absolute;
  top: 10px; right: 10px;
  color: #2563eb;
  font-size: 1rem;
}
.card-style-opt__spinner {
  position: absolute;
  top: 10px; right: 10px;
  width: 14px; height: 14px;
}

@media (max-width: 768px) {
  .card-style-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 10px; }
  .cso-preview { height: 135px; }
  .cso-preview__inner { transform: translate(-50%, -50%) scale(0.55); }
}
@media (max-width: 576px) {
  .card-style-grid { grid-template-columns: 1fr 1fr; gap: 8px; }
  .card-style-opt  { padding: 8px 6px 12px; }
  .cso-preview { height: 120px; }
  .cso-preview__inner { transform: translate(-50%, -50%) scale(0.48); }
  .card-style-opt__label { font-size: .78rem; }
}
</style>
