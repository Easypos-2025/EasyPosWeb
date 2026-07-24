<template>
  <div class="pkm-page">

    <!-- ══ KPI BAR (clickables = filtros) ══════════════════════════════════ -->
    <div class="pkm-kpi-bar">
      <div :class="['pkm-kpi-card pkm-kpi-sinconf', { 'pkm-kpi-active': filtroEstado === 'ingresado' }]"
        @click="filtroEstado = 'ingresado'">
        <i class="bi bi-door-open-fill"></i>
        <div>
          <span class="pkm-kpi-val">{{ cntIngresado }}</span>
          <span class="pkm-kpi-lbl">Sin confirmar</span>
        </div>
      </div>
      <div :class="['pkm-kpi-card pkm-kpi-conf', { 'pkm-kpi-active': filtroEstado === 'registrado' }]"
        @click="filtroEstado = 'registrado'">
        <i class="bi bi-person-check-fill"></i>
        <div>
          <span class="pkm-kpi-val">{{ cntRegistrado }}</span>
          <span class="pkm-kpi-lbl">Confirmadas</span>
        </div>
      </div>
      <div :class="['pkm-kpi-card pkm-kpi-pagadas', { 'pkm-kpi-active': filtroEstado === 'pagado' }]"
        @click="filtroEstado = 'pagado'">
        <i class="bi bi-cash-coin"></i>
        <div>
          <span class="pkm-kpi-val">{{ cntPagado }}</span>
          <span class="pkm-kpi-lbl">Pagadas</span>
        </div>
      </div>
    </div>

    <!-- ══ FILTRO FECHA ══════════════════════════════════════════════════════ -->
    <div class="pkm-filtro-bar">
      <CustomDatePicker v-model="fechaFiltro" @update:modelValue="cargar" />
    </div>

    <!-- ══ GRID DE TARJETAS ══════════════════════════════════════════════════ -->
    <div v-if="loading" class="pkm-loading">
      <i class="bi bi-arrow-repeat spin"></i> Cargando…
    </div>
    <div v-else-if="ordenesFiltradas.length === 0" class="pkm-empty">
      <i class="bi bi-check2-circle"></i>
      <p v-if="filtroEstado === 'ingresado'">No hay vehículos pendientes de confirmación</p>
      <p v-else>No hay ingresos confirmados aún</p>
      <small>Las tarjetas aparecen aquí cuando el portero registra un ingreso</small>
    </div>
    <div v-else class="pkm-grid">
      <div
        v-for="o in ordenesFiltradas" :key="o.id"
        :class="['pkm-card', { 'pkm-card--confirmado': o.estado === 'registrado', 'pkm-card--pagado': o.estado === 'pagado' }]"
        @click="o.estado !== 'pagado' && abrirConfirmar(o)"
      >
        <div class="pkm-card-top">
          <span :class="['pkm-badge-nuevo',
            o.estado === 'registrado' && 'pkm-badge-confirmado',
            o.estado === 'pagado' && 'pkm-badge-pagado']">
            {{ o.estado === 'pagado' ? 'Pagado' : o.estado === 'registrado' ? 'Confirmado' : 'Pendiente confirmación' }}
          </span>
          <span class="pkm-card-hora">{{ fmtHora(o.hora_ingreso) }}</span>
        </div>
        <div class="pkm-card-placa">{{ o.placa }}</div>
        <div v-if="o.tipo_vehiculo" class="pkm-card-tipo">{{ o.tipo_vehiculo }}</div>
        <div class="pkm-card-servicios">
          <span class="pkm-svc-pill">
            <i class="bi bi-list-check"></i>
            {{ o.adultos }} servicio{{ o.adultos !== 1 ? 's' : '' }}
          </span>
        </div>
        <div v-if="o.obs_portero" class="pkm-card-obs">
          <i class="bi bi-door-open"></i> {{ o.obs_portero }}
        </div>
        <div class="pkm-card-footer">
          <span class="pkm-card-orden">{{ o.numero_orden }}</span>
          <span v-if="o.estado === 'ingresado'" class="pkm-tap-hint"><i class="bi bi-hand-index"></i> Toca para confirmar</span>
          <span v-else-if="o.estado === 'pagado'" class="pkm-confirmado-por pkm-pagado-txt"><i class="bi bi-cash-coin"></i> Pagado en caja</span>
          <span v-else class="pkm-confirmado-por"><i class="bi bi-check2-all"></i> {{ o.mesero_nombre || 'Confirmado' }}</span>
        </div>
      </div>
    </div>

  </div>

  <!-- ══ MODAL CONFIRMAR INGRESO ══════════════════════════════════════════ -->
  <Teleport to="body">
    <div v-if="showModal" class="pkm-modal-overlay" @click.self="showModal = false">
      <div class="pkm-modal">
        <div class="pkm-modal-head">
          <span>
            <i :class="ordenSeleccionada?.estado === 'registrado' ? 'bi bi-pencil-square' : 'bi bi-clipboard2-check-fill'"></i>
            {{ ordenSeleccionada?.estado === 'registrado' ? 'Editar Servicios' : 'Confirmar Ingreso' }}
          </span>
          <button class="pkm-modal-close" @click="showModal = false"><i class="bi bi-x-lg"></i></button>
        </div>

        <div class="pkm-modal-body" v-if="ordenSeleccionada">
          <div class="pkm-ord-placa-big">{{ ordenSeleccionada.placa }}</div>
          <p class="pkm-ord-sub">{{ ordenSeleccionada.numero_orden }} · {{ fmtHora(ordenSeleccionada.hora_ingreso) }}</p>

          <div v-if="ordenSeleccionada.obs_portero" class="pkm-obs-portero">
            <i class="bi bi-info-circle"></i>
            <span><strong>Portero:</strong> {{ ordenSeleccionada.obs_portero }}</span>
          </div>

          <!-- Selector de servicios editable -->
          <div class="pkm-servicios-wrap">
            <div class="pkm-servicios-title">
              <i class="bi bi-list-check"></i> Servicios
              <span class="pkm-svc-hint">Modifica o agrega servicios</span>
            </div>
            <div v-if="loadingItems" class="pkm-servicios-loading">
              <i class="bi bi-arrow-repeat spin"></i> Cargando…
            </div>
            <div v-else-if="productos.length === 0" class="pkm-servicios-empty">
              Sin productos configurados
            </div>
            <div v-else class="pkm-servicios-list">
              <div v-for="p in productos" :key="p.id"
                :class="['pkm-svc-row-edit', { selected: seleccionMesero[p.id]?.activo }]">
                <label class="pkm-svc-check">
                  <input type="checkbox"
                    :checked="seleccionMesero[p.id]?.activo"
                    @change="toggleSvc(p)"
                  />
                  <span class="pkm-svc-nombre">{{ p.name }}</span>
                </label>
                <div v-if="seleccionMesero[p.id]?.activo" class="pkm-qty-wrap">
                  <button class="pkm-qty-btn" @click="cambiarQty(p.id, -1)">−</button>
                  <span class="pkm-qty-val">{{ seleccionMesero[p.id].cantidad }}</span>
                  <button class="pkm-qty-btn" @click="cambiarQty(p.id, 1)">+</button>
                </div>
              </div>
            </div>
            <div v-if="totalItemsMesero > 0" class="pkm-total-resumen">
              Total: <strong>{{ totalItemsMesero }}</strong> unidad{{ totalItemsMesero !== 1 ? 'es' : '' }}
            </div>
          </div>

          <div class="pkm-field">
            <label>Observaciones adicionales</label>
            <textarea v-model="formMesero.obs_mesero" class="pkm-input" rows="2"
              placeholder="Notas del mesero (no reemplaza la del portero)…"></textarea>
          </div>

        </div>

        <div class="pkm-modal-footer">
          <button class="pkm-btn-cancel" @click="showModal = false">Cancelar</button>
          <button class="pkm-btn-confirmar" :disabled="confirmando || loadingItems" @click="confirmar">
            <i v-if="confirmando" class="bi bi-arrow-repeat spin"></i>
            <i v-else :class="ordenSeleccionada?.estado === 'registrado' ? 'bi bi-floppy' : 'bi bi-check2-all'"></i>
            {{ confirmando ? 'Guardando…' : ordenSeleccionada?.estado === 'registrado' ? 'Guardar Cambios' : 'Confirmar y Enviar a Caja' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'
import { useCompanyStore } from '@/stores/companyStore'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'

const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id)

const ordenes           = ref([])
const loading           = ref(false)
const loadingItems      = ref(false)
const fechaFiltro       = ref(new Date().toISOString().slice(0, 10))
const filtroEstado      = ref('ingresado')
const showModal         = ref(false)
const confirmando       = ref(false)
const ordenSeleccionada = ref(null)


const formMesero       = ref({ obs_mesero: '' })
const productos        = ref([])
const seleccionMesero  = ref({})
const ordenesFiltradas = computed(() => ordenes.value.filter(o => o.estado === filtroEstado.value))
const cntIngresado     = computed(() => ordenes.value.filter(o => o.estado === 'ingresado').length)
const cntRegistrado    = computed(() => ordenes.value.filter(o => o.estado === 'registrado').length)
const cntPagado        = computed(() => ordenes.value.filter(o => o.estado === 'pagado').length)
const totalItemsMesero = computed(() =>
  Object.values(seleccionMesero.value).filter(v => v.activo).reduce((s, v) => s + v.cantidad, 0)
)
const itemsParaEnviar  = computed(() =>
  productos.value
    .filter(p => seleccionMesero.value[p.id]?.activo)
    .map(p => ({ product_id: p.id, nombre: p.name, cantidad: seleccionMesero.value[p.id].cantidad }))
)

async function cargar(silent = false) {
  if (!companyId.value) return
  if (!silent) loading.value = true
  try {
    const res = await api.get('/api/parking/orders', {
      params: { company_id: companyId.value, fecha: fechaFiltro.value, estado: 'ingresado,registrado,pagado' },
    })
    ordenes.value = res.data
  } catch { if (!silent) showToast('Error al cargar órdenes', 'error', 3000) }
  if (!silent) loading.value = false
}

watch(companyId, v => { if (v) cargar() }, { immediate: true })

let _autoRefresh = null
onMounted(() => {
  _autoRefresh = setInterval(() => { if (!showModal.value) cargar(true) }, 30000)
})
onUnmounted(() => clearInterval(_autoRefresh))

async function abrirConfirmar(orden) {
  ordenSeleccionada.value = orden
  formMesero.value        = { obs_mesero: '' }
  seleccionMesero.value   = {}
  showModal.value         = true
  loadingItems.value      = true
  try {
    const needProds = productos.value.length === 0
    const calls = [api.get(`/api/parking/orders/${orden.id}/items`)]
    if (needProds) calls.push(api.get('/api/parking/products', { params: { company_id: companyId.value } }))
    const [rItems, rProds] = await Promise.all(calls)
    if (rProds) productos.value = rProds.data
    // Pre-popular selección con los ítems existentes
    for (const item of rItems.data) {
      if (item.product_id) {
        seleccionMesero.value[item.product_id] = { activo: true, cantidad: item.cantidad }
      }
    }
  } catch {}
  loadingItems.value = false
}

function toggleSvc(p) {
  seleccionMesero.value[p.id] = seleccionMesero.value[p.id]?.activo
    ? { activo: false, cantidad: 1 }
    : { activo: true, cantidad: 1 }
}

function cambiarQty(pid, delta) {
  const actual = seleccionMesero.value[pid]?.cantidad || 1
  seleccionMesero.value[pid] = { activo: true, cantidad: Math.max(1, actual + delta) }
}

async function confirmar() {
  if (!ordenSeleccionada.value) return
  if (itemsParaEnviar.value.length === 0) {
    showToast('Selecciona al menos un servicio', 'warning', 2500)
    return
  }
  confirmando.value = true
  try {
    await api.put(`/api/parking/orders/${ordenSeleccionada.value.id}/registrar`, {
      obs_mesero: formMesero.value.obs_mesero || null,
      items: itemsParaEnviar.value,
    })
    const eraIngresado = ordenSeleccionada.value.estado === 'ingresado'
    showToast(eraIngresado ? 'Confirmado y enviado a caja' : 'Servicios actualizados', 'success', 2500)
    showModal.value = false
    const idx = ordenes.value.findIndex(o => o.id === ordenSeleccionada.value.id)
    if (idx !== -1) {
      const nuevoEstado = eraIngresado ? 'registrado' : ordenes.value[idx].estado
      ordenes.value[idx] = { ...ordenes.value[idx], estado: nuevoEstado }
    }
  } catch (e) { showToast(e?.response?.data?.detail || 'Error al confirmar', 'error', 3000) }
  confirmando.value = false
}

function fmtHora(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.pkm-page { padding: 16px; max-width: 900px; margin: 0 auto; }

/* KPI Bar */
.pkm-kpi-bar { display: flex; gap: 10px; margin-bottom: 14px; }
.pkm-kpi-card { display: flex; align-items: center; gap: 10px; padding: 10px 14px; border-radius: 10px; color: #fff; font-weight: 600; flex: 1; cursor: pointer; transition: filter .15s; }
.pkm-kpi-card:hover { filter: brightness(1.1); }
.pkm-kpi-card i { font-size: 1.4rem; opacity: .85; }
.pkm-kpi-val { display: block; font-size: 1.4rem; line-height: 1; }
.pkm-kpi-lbl { display: block; font-size: .7rem; opacity: .85; white-space: nowrap; }
.pkm-kpi-sinconf { background: #fd7e14; }
.pkm-kpi-conf    { background: #198754; }
.pkm-kpi-pagadas { background: #0d6efd; }
.pkm-kpi-active  { outline: 3px solid #fff; outline-offset: -3px; box-shadow: 0 0 0 3px rgba(0,0,0,.25); }

.pkm-filtro-bar { margin-bottom: 14px; display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }

.pkm-loading { text-align: center; padding: 40px; color: #6c757d; }
.pkm-empty   { text-align: center; padding: 60px 20px; color: #adb5bd; }
.pkm-empty i { font-size: 2.5rem; display: block; margin-bottom: 8px; }
.pkm-empty small { font-size: .8rem; display: block; margin-top: 6px; }

.pkm-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.pkm-card {
  background: #fff; border-radius: 12px; padding: 14px; cursor: pointer;
  border: 2px solid #ffc107; display: flex; flex-direction: column; gap: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,.06); transition: all .2s;
}
.pkm-card:hover { border-color: #fd7e14; transform: translateY(-2px); box-shadow: 0 4px 14px rgba(0,0,0,.1); }
.pkm-card-top { display: flex; align-items: center; justify-content: space-between; }
.pkm-badge-nuevo { font-size: .7rem; font-weight: 700; padding: 3px 8px; border-radius: 20px; background: #fff3cd; color: #856404; text-transform: uppercase; }
.pkm-badge-confirmado { background: #d1e7dd !important; color: #0a3622 !important; }
.pkm-badge-pagado     { background: #cfe2ff !important; color: #084298 !important; }
.pkm-card--confirmado { border-color: #198754; }
.pkm-card--pagado     { border-color: #0d6efd; cursor: default; opacity: .85; }
.pkm-pagado-txt { font-size: .72rem; color: #0d6efd; display: flex; align-items: center; gap: 4px; font-weight: 600; }
.pkm-card-placa { font-size: 1.8rem; font-weight: 900; letter-spacing: 3px; text-align: center; border: 2px solid #212529; border-radius: 6px; padding: 4px 0; color: #212529; background: #fff; }
.pkm-confirmado-por { font-size: .72rem; color: #198754; display: flex; align-items: center; gap: 4px; font-weight: 600; }
.pkm-card-hora { font-size: .75rem; color: #6c757d; }

.pkm-card-tipo  { text-align: center; font-size: .78rem; color: #6c757d; }
.pkm-card-servicios { display: flex; justify-content: center; }
.pkm-svc-pill { display: inline-flex; align-items: center; gap: 4px; background: #e7f1ff; border: 1px solid #c2d8ff; padding: 3px 10px; border-radius: 20px; font-size: .82rem; font-weight: 600; color: #084298; }
.pkm-card-obs { font-size: .78rem; color: #6c757d; font-style: italic; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.pkm-card-footer { display: flex; align-items: center; justify-content: space-between; border-top: 1px solid #f1f3f5; padding-top: 6px; margin-top: 2px; }
.pkm-card-orden { font-size: .72rem; color: #adb5bd; font-family: monospace; }
.pkm-tap-hint   { font-size: .72rem; color: #fd7e14; display: flex; align-items: center; gap: 4px; }

/* Modal */
.pkm-modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.5); z-index: 1050; display: flex; align-items: center; justify-content: center; padding: 16px; }
.pkm-modal { background: #fff; border-radius: 14px; width: 100%; max-width: 420px; max-height: 90vh; overflow-y: auto; display: flex; flex-direction: column; }
.pkm-modal-head { display: flex; align-items: center; justify-content: space-between; padding: 14px 18px; border-bottom: 1px solid #e9ecef; font-weight: 700; font-size: .95rem; position: sticky; top: 0; background: #fff; z-index: 1; }
.pkm-modal-close { border: none; background: #f1f3f5; border-radius: 6px; padding: 5px 9px; cursor: pointer; }
.pkm-modal-body { padding: 18px; display: flex; flex-direction: column; gap: 14px; flex: 1; }
.pkm-modal-footer { padding: 14px 18px; border-top: 1px solid #e9ecef; display: flex; gap: 10px; justify-content: flex-end; }
.pkm-ord-placa-big { font-size: 2.2rem; font-weight: 900; letter-spacing: 4px; text-align: center; border: 2px solid #212529; border-radius: 8px; padding: 8px; }
.pkm-ord-sub { text-align: center; font-size: .82rem; color: #6c757d; margin-top: 4px; }
.pkm-obs-portero { font-size: .82rem; background: #fff3cd; color: #664d03; padding: 8px 12px; border-radius: 8px; border-left: 3px solid #ffc107; display: flex; gap: 8px; }

/* Servicios en modal */
.pkm-servicios-wrap { background: #f8f9fa; border-radius: 10px; padding: 12px; display: flex; flex-direction: column; gap: 8px; }
.pkm-servicios-title { display: flex; align-items: center; gap: 6px; font-size: .82rem; font-weight: 700; color: #495057; flex-wrap: wrap; }
.pkm-svc-hint { font-size: .72rem; color: #0d6efd; font-weight: 400; margin-left: auto; }
.pkm-servicios-loading { text-align: center; font-size: .85rem; color: #6c757d; padding: 8px; }
.pkm-servicios-empty   { text-align: center; font-size: .82rem; color: #adb5bd; }
.pkm-servicios-list { display: flex; flex-direction: column; gap: 6px; }
.pkm-svc-row-edit {
  display: flex; align-items: center; justify-content: space-between; gap: 8px;
  padding: 8px 10px; border: 1.5px solid #e9ecef; border-radius: 8px;
  background: #fff; transition: border-color .15s, background .15s;
}
.pkm-svc-row-edit.selected { border-color: #0d6efd; background: #f0f6ff; }
.pkm-svc-check { display: flex; align-items: center; gap: 8px; cursor: pointer; flex: 1; }
.pkm-svc-check input[type="checkbox"] { width: 16px; height: 16px; cursor: pointer; accent-color: #0d6efd; flex-shrink: 0; }
.pkm-svc-nombre { font-size: .88rem; font-weight: 600; color: #212529; }
.pkm-qty-wrap { display: flex; align-items: center; gap: 4px; flex-shrink: 0; }
.pkm-qty-btn { width: 24px; height: 24px; border: 1.5px solid #0d6efd; border-radius: 5px; background: #fff; color: #0d6efd; font-size: .9rem; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.pkm-qty-btn:hover { background: #0d6efd; color: #fff; }
.pkm-qty-val { font-size: .88rem; font-weight: 700; min-width: 18px; text-align: center; }
.pkm-total-resumen { text-align: right; font-size: .82rem; color: #495057; padding-top: 4px; border-top: 1px solid #dee2e6; }

.pkm-field { display: flex; flex-direction: column; gap: 5px; }
.pkm-field label { font-size: .82rem; font-weight: 600; color: #495057; }
.pkm-input { border: 1px solid #ced4da; border-radius: 8px; padding: 9px 12px; font-size: .9rem; outline: none; width: 100%; }
.pkm-btn-cancel { padding: 9px 18px; border: 1px solid #ced4da; border-radius: 8px; background: #fff; color: #495057; font-size: .9rem; cursor: pointer; }
.pkm-btn-confirmar { padding: 9px 20px; border: none; border-radius: 8px; background: #198754; color: #fff; font-size: .9rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; }
.pkm-btn-confirmar:hover:not(:disabled) { background: #157347; }
.pkm-btn-confirmar:disabled { opacity: .6; cursor: default; }

.spin { animation: pkm-spin .8s linear infinite; }
@keyframes pkm-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

@media (max-width: 768px) {
  .pkm-grid { grid-template-columns: repeat(auto-fill, minmax(165px, 1fr)); }
  .pkm-card-placa { font-size: 1.5rem; }
}
@media (max-width: 576px) {
  .pkm-page { padding: 10px; }
  .pkm-header { flex-direction: column; align-items: flex-start; gap: 10px; }
  .pkm-pendientes-badge { align-self: flex-end; }
  .pkm-grid { grid-template-columns: 1fr 1fr; gap: 8px; }
  .pkm-card { padding: 10px; }
  .pkm-card-placa { font-size: 1.3rem; letter-spacing: 2px; }
  .pkm-modal { max-width: 100%; border-radius: 14px 14px 0 0; }
  .pkm-modal-overlay { align-items: flex-end; padding: 0; }
}
</style>
