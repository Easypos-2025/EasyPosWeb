<template>
  <div class="pkc-page">

    <!-- ══ KPI BAR ══════════════════════════════════════════════════════════ -->
    <div class="pkc-kpi-bar">
      <div class="pkc-kpi-card pkc-kpi-pendiente">
        <i class="bi bi-hourglass-split"></i>
        <div>
          <span class="pkc-kpi-val">{{ ordenes.length }}</span>
          <span class="pkc-kpi-lbl">Pendientes cobro</span>
        </div>
      </div>
      <div class="pkc-kpi-card pkc-kpi-personas">
        <i class="bi bi-people-fill"></i>
        <div>
          <span class="pkc-kpi-val">{{ totalPersonas }}</span>
          <span class="pkc-kpi-lbl">Personas activas</span>
        </div>
      </div>
      <div class="pkc-kpi-card pkc-kpi-pagadas">
        <i class="bi bi-check-circle-fill"></i>
        <div>
          <span class="pkc-kpi-val">{{ pagadasHoy }}</span>
          <span class="pkc-kpi-lbl">Pagadas hoy</span>
        </div>
      </div>
    </div>

    <!-- ══ FILTRO FECHA ══════════════════════════════════════════════════════ -->
    <div class="pkc-filtro-bar">
      <CustomDatePicker v-model="fechaFiltro" @update:modelValue="cargar" />
      <div class="pkc-filtro-tabs">
        <button :class="['pkc-tab', { active: soloRegistradas }]" @click="soloRegistradas = true; cargar()">
          Pendientes cobro
        </button>
        <button :class="['pkc-tab', { active: !soloRegistradas }]" @click="soloRegistradas = false; cargar()">
          Todas
        </button>
      </div>
    </div>

    <!-- ══ GRID DE TARJETAS ══════════════════════════════════════════════════ -->
    <div v-if="loading" class="pkc-loading">
      <i class="bi bi-arrow-repeat spin"></i> Cargando…
    </div>
    <div v-else-if="ordenes.length === 0" class="pkc-empty">
      <i class="bi bi-cash-coin"></i>
      <p>No hay órdenes pendientes de cobro</p>
      <small>Las órdenes aparecen aquí cuando el mesero confirma las personas</small>
    </div>
    <div v-else class="pkc-grid">
      <div
        v-for="o in ordenes" :key="o.id"
        :class="['pkc-card', `pkc-card--${o.estado}`]"
      >
        <div class="pkc-card-top">
          <span :class="['pkc-badge', `pkc-badge--${o.estado}`]">{{ LABELS_ESTADO[o.estado] }}</span>
          <span class="pkc-card-hora">{{ fmtHora(o.hora_ingreso) }}</span>
        </div>

        <div class="pkc-card-placa">{{ o.placa }}</div>
        <div v-if="o.tipo_vehiculo" class="pkc-card-tipo">{{ o.tipo_vehiculo }}</div>

        <div class="pkc-personas-summary">
          <span class="pkc-psuma"><i class="bi bi-person-fill"></i> {{ o.adultos }} adulto{{ o.adultos !== 1 ? 's' : '' }}</span>
          <span v-if="o.ninos > 0" class="pkc-psuma pkc-nino">
            <i class="bi bi-person-hearts"></i> {{ o.ninos }} niño{{ o.ninos !== 1 ? 's' : '' }}
          </span>
          <span v-if="o.mascotas > 0" class="pkc-psuma pkc-mascota">
            <i class="bi bi-circle-fill" style="font-size:.6rem"></i> {{ o.mascotas }} mascota{{ o.mascotas !== 1 ? 's' : '' }}
          </span>
        </div>

        <div v-if="o.obs_portero || o.obs_mesero" class="pkc-obs-wrap">
          <div v-if="o.obs_portero" class="pkc-obs">
            <i class="bi bi-door-open"></i> {{ o.obs_portero }}
          </div>
          <div v-if="o.obs_mesero" class="pkc-obs pkc-obs-mesero">
            <i class="bi bi-person-badge"></i> {{ o.obs_mesero }}
          </div>
        </div>

        <div v-if="o.mesero_nombre" class="pkc-confirmado-por">
          <i class="bi bi-check2"></i> Confirmado por: {{ o.mesero_nombre }}
        </div>

        <div class="pkc-card-footer">
          <span class="pkc-card-orden">{{ o.numero_orden }}</span>
          <button
            v-if="o.estado === 'registrado'"
            class="pkc-btn-pagar"
            :disabled="pagandoId === o.id"
            @click="pagar(o)"
          >
            <i v-if="pagandoId === o.id" class="bi bi-arrow-repeat spin"></i>
            <i v-else class="bi bi-cash-coin"></i>
            {{ pagandoId === o.id ? 'Procesando…' : 'Cobrar' }}
          </button>
          <span v-else class="pkc-ya-pagado">
            <i class="bi bi-check-circle-fill"></i>
            Pagado {{ fmtHora(o.hora_salida) }}
          </span>
        </div>
      </div>
    </div>

  </div>

  <!-- ══ COMPROBANTE DE SALIDA ══════════════════════════════════════════════ -->
  <ComprobanteParkingIngreso
    v-if="ordenParaSalida"
    :orden="ordenParaSalida"
    :company-name="companyStore.selectedCompany?.name || ''"
    :company-id="companyStore.selectedCompany?.id_company"
    tipo="salida"
    @close="ordenParaSalida = null"
  />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'
import { useCompanyStore } from '@/stores/companyStore'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'
import ComprobanteParkingIngreso from '@/components/parking/ComprobanteParkingIngreso.vue'

const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id_company)

const LABELS_ESTADO = {
  ingresado:  'Ingresado',
  registrado: 'Pendiente cobro',
  pagado:     'Pagado',
  cancelado:  'Cancelado',
}

// ── Estado ────────────────────────────────────────────────────────────────────
const ordenes         = ref([])
const loading         = ref(false)
const fechaFiltro     = ref(new Date().toISOString().slice(0, 10))
const soloRegistradas = ref(true)
const pagandoId       = ref(null)
const ordenParaSalida = ref(null)

// ── KPIs computados ───────────────────────────────────────────────────────────
const totalPersonas = computed(() =>
  ordenes.value
    .filter(o => o.estado === 'registrado')
    .reduce((s, o) => s + o.adultos + o.ninos + o.mascotas, 0)
)

const pagadasHoy = computed(() =>
  ordenes.value.filter(o => o.estado === 'pagado').length
)

// ── Carga ─────────────────────────────────────────────────────────────────────
async function cargar() {
  if (!companyId.value) return
  loading.value = true
  try {
    const estado = soloRegistradas.value ? 'registrado' : 'registrado,pagado'
    const res = await api.get('/api/parking/orders', {
      params: { company_id: companyId.value, fecha: fechaFiltro.value, estado },
    })
    ordenes.value = res.data
  } catch {
    showToast('Error al cargar órdenes', 'error', 3000)
  }
  loading.value = false
}

onMounted(cargar)

// ── Pagar ─────────────────────────────────────────────────────────────────────
async function pagar(orden) {
  pagandoId.value = orden.id
  try {
    await api.put(`/api/parking/orders/${orden.id}/pagar`)
    showToast('Orden cobrada correctamente', 'success', 2500)
    // Actualiza el estado localmente y guarda para imprimir recibo de salida
    const actualizada = { ...orden, estado: 'pagado', hora_salida: new Date().toISOString() }
    const idx = ordenes.value.findIndex(o => o.id === orden.id)
    if (idx !== -1) ordenes.value[idx] = actualizada
    if (soloRegistradas.value) {
      ordenes.value = ordenes.value.filter(o => o.id !== orden.id)
    }
    ordenParaSalida.value = actualizada
    // Refresca stats en la otra vista cuando vuelvan
  } catch (e) {
    showToast(e?.response?.data?.detail || 'Error al cobrar', 'error', 3000)
  }
  pagandoId.value = null
}

// ── Utilidades ────────────────────────────────────────────────────────────────
function fmtHora(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.pkc-page { padding: 16px; max-width: 1200px; margin: 0 auto; }

/* ── KPI bar ── */
.pkc-kpi-bar {
  display: flex; align-items: stretch; gap: 10px; margin-bottom: 14px; flex-wrap: wrap;
}
.pkc-kpi-card {
  display: flex; align-items: center; gap: 12px; padding: 12px 20px;
  border-radius: 10px; color: #fff; font-weight: 600; flex: 1; min-width: 130px;
}
.pkc-kpi-card i    { font-size: 1.5rem; opacity: .85; }
.pkc-kpi-val       { display: block; font-size: 1.6rem; line-height: 1; }
.pkc-kpi-lbl       { display: block; font-size: .72rem; opacity: .85; white-space: nowrap; }
.pkc-kpi-pendiente { background: #fd7e14; }
.pkc-kpi-personas  { background: #0d6efd; }
.pkc-kpi-pagadas   { background: #198754; }

/* ── Filtro ── */
.pkc-filtro-bar {
  display: flex; align-items: center; gap: 12px; margin-bottom: 14px; flex-wrap: wrap;
}
.pkc-filtro-tabs { display: flex; gap: 6px; }
.pkc-tab {
  padding: 6px 16px; border-radius: 20px; border: 1px solid #dee2e6;
  background: #fff; font-size: .82rem; cursor: pointer; transition: all .15s;
}
.pkc-tab.active { background: #0d6efd; color: #fff; border-color: #0d6efd; }

/* ── Carga / vacío ── */
.pkc-loading { text-align: center; padding: 40px; color: #6c757d; }
.pkc-empty   { text-align: center; padding: 60px 20px; color: #adb5bd; }
.pkc-empty i { font-size: 2.5rem; display: block; margin-bottom: 8px; }
.pkc-empty small { font-size: .8rem; display: block; margin-top: 6px; }

/* ── Grid tarjetas ── */
.pkc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}
.pkc-card {
  background: #fff; border-radius: 12px; padding: 14px;
  border: 2px solid #dee2e6; display: flex; flex-direction: column; gap: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,.06); transition: box-shadow .2s;
}
.pkc-card--registrado { border-color: #0d6efd; }
.pkc-card--pagado     { border-color: #d1e7dd; opacity: .75; }

.pkc-card-top {
  display: flex; align-items: center; justify-content: space-between;
}
.pkc-badge {
  font-size: .7rem; font-weight: 700; padding: 3px 8px; border-radius: 20px;
  text-transform: uppercase; letter-spacing: .3px;
}
.pkc-badge--registrado { background: #cfe2ff; color: #084298; }
.pkc-badge--pagado     { background: #d1e7dd; color: #0a3622; }
.pkc-card-hora { font-size: .75rem; color: #6c757d; }

.pkc-card-placa {
  font-size: 1.9rem; font-weight: 900; letter-spacing: 3px;
  text-align: center; color: #212529; line-height: 1;
  border: 2px solid #212529; border-radius: 6px; padding: 6px 0;
}
.pkc-card-tipo { text-align: center; font-size: .78rem; color: #6c757d; }

.pkc-personas-summary {
  display: flex; flex-direction: column; gap: 4px;
}
.pkc-psuma {
  display: flex; align-items: center; gap: 6px; font-size: .88rem; font-weight: 600;
  padding: 4px 10px; border-radius: 8px; background: #f8f9fa;
}
.pkc-nino    { background: #fff3cd; }
.pkc-mascota { background: #e2d9f3; }

.pkc-obs-wrap { display: flex; flex-direction: column; gap: 4px; }
.pkc-obs {
  font-size: .78rem; color: #6c757d; font-style: italic;
  display: flex; align-items: flex-start; gap: 5px; padding: 4px 8px;
  background: #f8f9fa; border-radius: 6px;
}
.pkc-obs-mesero { background: #e8f4fd; color: #055160; }

.pkc-confirmado-por {
  font-size: .75rem; color: #198754;
  display: flex; align-items: center; gap: 5px;
}

.pkc-card-footer {
  display: flex; align-items: center; justify-content: space-between;
  margin-top: 4px; border-top: 1px solid #f1f3f5; padding-top: 8px;
}
.pkc-card-orden { font-size: .72rem; color: #adb5bd; font-family: monospace; }

.pkc-btn-pagar {
  display: flex; align-items: center; gap: 6px; padding: 8px 16px;
  border: none; border-radius: 8px; background: #198754; color: #fff;
  font-size: .85rem; font-weight: 600; cursor: pointer; transition: background .15s;
}
.pkc-btn-pagar:hover:not(:disabled) { background: #157347; }
.pkc-btn-pagar:disabled { opacity: .6; cursor: default; }

.pkc-ya-pagado {
  font-size: .78rem; color: #198754; display: flex; align-items: center; gap: 4px;
}

.spin { animation: pkc-spin .8s linear infinite; }
@keyframes pkc-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* ── Responsive ── */
@media (max-width: 768px) {
  .pkc-kpi-card { padding: 10px 14px; }
  .pkc-kpi-val  { font-size: 1.3rem; }
  .pkc-grid     { grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 10px; }
  .pkc-card-placa { font-size: 1.5rem; }
}
@media (max-width: 576px) {
  .pkc-page { padding: 10px; }
  .pkc-kpi-bar {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px;
  }
  .pkc-kpi-card { padding: 8px 10px; gap: 6px; min-width: unset; }
  .pkc-kpi-card i { font-size: 1.1rem; }
  .pkc-kpi-val { font-size: 1.1rem; }
  .pkc-grid { grid-template-columns: 1fr; gap: 10px; }
  .pkc-filtro-bar { flex-direction: column; align-items: flex-start; gap: 8px; }
}
</style>
