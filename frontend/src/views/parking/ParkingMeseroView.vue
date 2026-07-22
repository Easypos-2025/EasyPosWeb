<template>
  <div class="pkm-page">

    <!-- ══ HEADER ════════════════════════════════════════════════════════════ -->
    <div class="pkm-header">
      <div class="pkm-header-info">
        <i class="bi bi-person-badge-fill"></i>
        <div>
          <h6>Confirmación de Ingresos</h6>
          <p>Toca una tarjeta para confirmar el servicio y enviar a cobro</p>
        </div>
      </div>
      <div class="pkm-pendientes-badge">
        <span class="pkm-count">{{ ordenes.length }}</span>
        <span class="pkm-count-lbl">pendientes</span>
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
    <div v-else-if="ordenes.length === 0" class="pkm-empty">
      <i class="bi bi-check2-circle"></i>
      <p>No hay vehículos pendientes de confirmación</p>
      <small>Las tarjetas aparecen aquí cuando el portero registra un ingreso</small>
    </div>
    <div v-else class="pkm-grid">
      <div
        v-for="o in ordenes" :key="o.id"
        class="pkm-card"
        @click="abrirConfirmar(o)"
      >
        <div class="pkm-card-top">
          <span class="pkm-badge-nuevo">Pendiente confirmación</span>
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
          <span class="pkm-tap-hint"><i class="bi bi-hand-index"></i> Toca para confirmar</span>
        </div>
      </div>
    </div>

  </div>

  <!-- ══ MODAL CONFIRMAR INGRESO ══════════════════════════════════════════ -->
  <Teleport to="body">
    <div v-if="showModal" class="pkm-modal-overlay" @click.self="showModal = false">
      <div class="pkm-modal">
        <div class="pkm-modal-head">
          <span><i class="bi bi-clipboard2-check-fill"></i> Confirmar Ingreso</span>
          <button class="pkm-modal-close" @click="showModal = false"><i class="bi bi-x-lg"></i></button>
        </div>

        <div class="pkm-modal-body" v-if="ordenSeleccionada">
          <div class="pkm-ord-placa-big">{{ ordenSeleccionada.placa }}</div>
          <p class="pkm-ord-sub">{{ ordenSeleccionada.numero_orden }} · {{ fmtHora(ordenSeleccionada.hora_ingreso) }}</p>

          <div v-if="ordenSeleccionada.obs_portero" class="pkm-obs-portero">
            <i class="bi bi-info-circle"></i>
            <span><strong>Portero:</strong> {{ ordenSeleccionada.obs_portero }}</span>
          </div>

          <!-- Servicios registrados -->
          <div class="pkm-servicios-wrap">
            <div class="pkm-servicios-title">
              <i class="bi bi-list-check"></i> Servicios registrados
            </div>
            <div v-if="loadingItems" class="pkm-servicios-loading">
              <i class="bi bi-arrow-repeat spin"></i> Cargando…
            </div>
            <div v-else-if="itemsOrden.length === 0" class="pkm-servicios-empty">
              Sin detalle de servicios disponible
            </div>
            <div v-else class="pkm-servicios-list">
              <div v-for="item in itemsOrden" :key="item.id" class="pkm-svc-row">
                <span class="pkm-svc-nombre">{{ item.nombre }}</span>
                <span class="pkm-svc-qty">× {{ item.cantidad }}</span>
              </div>
            </div>
            <div class="pkm-total-resumen">
              Total: <strong>{{ totalItems }}</strong> unidad{{ totalItems !== 1 ? 'es' : '' }}
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
            <i v-else class="bi bi-check2-all"></i>
            {{ confirmando ? 'Confirmando…' : 'Confirmar y Enviar a Caja' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
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
const showModal         = ref(false)
const confirmando       = ref(false)
const ordenSeleccionada = ref(null)
const itemsOrden        = ref([])

const formMesero    = ref({ obs_mesero: '' })
const totalItems    = computed(() => itemsOrden.value.reduce((s, i) => s + (i.cantidad || 1), 0))

async function cargar() {
  if (!companyId.value) return
  loading.value = true
  try {
    const res = await api.get('/api/parking/orders', {
      params: { company_id: companyId.value, fecha: fechaFiltro.value, estado: 'ingresado' },
    })
    ordenes.value = res.data
  } catch { showToast('Error al cargar órdenes', 'error', 3000) }
  loading.value = false
}

onMounted(cargar)

async function abrirConfirmar(orden) {
  ordenSeleccionada.value = orden
  formMesero.value        = { obs_mesero: '' }
  itemsOrden.value        = []
  showModal.value         = true
  loadingItems.value      = true
  try {
    const res = await api.get(`/api/parking/orders/${orden.id}/items`)
    itemsOrden.value = res.data
  } catch {}
  loadingItems.value = false
}

async function confirmar() {
  if (!ordenSeleccionada.value) return
  confirmando.value = true
  try {
    await api.put(`/api/parking/orders/${ordenSeleccionada.value.id}/registrar`, {
      obs_mesero: formMesero.value.obs_mesero || null,
    })
    showToast('Confirmado y enviado a caja', 'success', 2500)
    showModal.value = false
    ordenes.value   = ordenes.value.filter(o => o.id !== ordenSeleccionada.value.id)
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

.pkm-header {
  display: flex; align-items: center; justify-content: space-between;
  background: #fff; border-radius: 12px; padding: 14px 18px;
  border: 1px solid #e9ecef; margin-bottom: 14px; gap: 12px;
}
.pkm-header-info { display: flex; align-items: center; gap: 12px; flex: 1; }
.pkm-header-info i { font-size: 2rem; color: #0d6efd; }
.pkm-header-info h6 { margin: 0; font-weight: 700; font-size: .95rem; }
.pkm-header-info p  { margin: 0; font-size: .8rem; color: #6c757d; }
.pkm-pendientes-badge { display: flex; flex-direction: column; align-items: center; background: #ffc107; border-radius: 12px; padding: 8px 16px; flex-shrink: 0; }
.pkm-count     { font-size: 1.8rem; font-weight: 900; color: #212529; line-height: 1; }
.pkm-count-lbl { font-size: .7rem; font-weight: 600; color: #495057; }

.pkm-filtro-bar { margin-bottom: 14px; }

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
.pkm-card-hora { font-size: .75rem; color: #6c757d; }
.pkm-card-placa { font-size: 1.8rem; font-weight: 900; letter-spacing: 3px; text-align: center; border: 2px solid #212529; border-radius: 6px; padding: 4px 0; }
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
.pkm-servicios-title { display: flex; align-items: center; gap: 6px; font-size: .82rem; font-weight: 700; color: #495057; }
.pkm-servicios-loading { text-align: center; font-size: .85rem; color: #6c757d; padding: 8px; }
.pkm-servicios-empty   { text-align: center; font-size: .82rem; color: #adb5bd; }
.pkm-servicios-list { display: flex; flex-direction: column; gap: 4px; }
.pkm-svc-row { display: flex; align-items: center; justify-content: space-between; font-size: .88rem; padding: 4px 0; border-bottom: 1px solid #e9ecef; }
.pkm-svc-row:last-child { border-bottom: none; }
.pkm-svc-nombre { color: #212529; }
.pkm-svc-qty    { font-weight: 700; color: #0d6efd; }
.pkm-total-resumen { text-align: right; font-size: .82rem; color: #495057; }

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
