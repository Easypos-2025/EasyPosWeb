<template>
  <div class="dashboard-content">

    <!-- KPI BAR -->
    <KpiStrip :kpis="kpis" :loading="kpiLoading" :showLabels="true" v-model="fechaKpi" />

    <!-- CABECERA: título + fechero -->
    <div class="dash-header">
      <h6 class="dash-title">{{ companyStore.selectedCompany?.name || 'Panel de Operaciones' }}</h6>
      <div class="fechero-wrap">
        <i class="bi bi-calendar3"></i>
        <input type="date" class="fechero-input" v-model="fecha" @change="onFechaChange" />
      </div>
    </div>

    <!-- TABS -->
    <ul class="nav nav-tabs dash-tabs" role="tablist">
      <li class="nav-item">
        <button
          class="nav-link"
          :class="{ active: tabActivo === 'nueva' }"
          @click="tabActivo = 'nueva'"
        >
          <i class="bi bi-plus-circle me-1"></i>Nueva Mesa / Pedido
        </button>
      </li>
      <li class="nav-item">
        <button
          class="nav-link"
          :class="{ active: tabActivo === 'abiertas' }"
          @click="tabActivo = 'abiertas'; cargarAbiertas()"
        >
          <i class="bi bi-table me-1"></i>Abiertas
          <span v-if="abiertas.length" class="badge badge-abierta ms-1">{{ abiertas.length }}</span>
        </button>
      </li>
      <li class="nav-item">
        <button
          class="nav-link"
          :class="{ active: tabActivo === 'facturadas' }"
          @click="tabActivo = 'facturadas'; cargarFacturadas()"
        >
          <i class="bi bi-receipt me-1"></i>Facturadas
          <span v-if="facturadas.length" class="badge badge-facturada ms-1">{{ facturadas.length }}</span>
        </button>
      </li>
    </ul>

    <div class="tab-content dash-tab-content">

      <!-- TAB 1: NUEVA MESA / PEDIDO -->
      <div v-show="tabActivo === 'nueva'" class="tab-pane-inner">
        <div v-if="mesasLoading" class="estado-carga">
          <div class="spinner-border spinner-border-sm text-primary"></div>
          <span>Cargando mesas...</span>
        </div>
        <div v-else-if="!mesas.length" class="estado-vacio">
          <i class="bi bi-grid-3x3-gap"></i>
          <p>No hay mesas configuradas. Sincroniza el software de escritorio primero.</p>
        </div>
        <template v-else>
          <!-- Acciones rápidas -->
          <div class="acciones-rapidas">
            <button class="btn-accion" @click="abrirModalTakeout">
              <i class="bi bi-bag-check"></i>
              <span>Para Llevar</span>
            </button>
            <button class="btn-accion btn-accion--web">
              <i class="bi bi-globe"></i>
              <span>Pedido Web</span>
            </button>
          </div>

          <!-- Grid de mesas por zona -->
          <template v-for="zona in zonas" :key="zona">
            <div class="zona-label">
              <i class="bi bi-geo-alt"></i> {{ zona || 'Sin zona' }}
            </div>
            <div class="mesas-grid">
              <div
                v-for="mesa in mesasPorZona(zona)"
                :key="mesa.id"
                class="mesa-card"
                :class="{
                  'mesa-card--libre': !mesa.ocupada,
                  'mesa-card--ocupada': mesa.ocupada
                }"
                @click="!mesa.ocupada && abrirModalMesa(mesa)"
              >
                <div class="mesa-icon">
                  <i class="bi" :class="mesa.ocupada ? 'bi-person-fill' : 'bi-table'"></i>
                </div>
                <div class="mesa-nombre">{{ mesa.name }}</div>
                <div class="mesa-info">
                  <span v-if="mesa.ocupada">
                    <span class="mesa-estado ocupada">Ocupada</span>
                    <span class="mesa-mesero">{{ mesa.waiter_name || 'Sin mesero' }}</span>
                    <span class="mesa-monto">{{ fmt(mesa.amount) }}</span>
                  </span>
                  <span v-else class="mesa-estado libre">
                    {{ mesa.seats }} sillas
                  </span>
                </div>
              </div>
            </div>
          </template>
        </template>
      </div>

      <!-- TAB 2: ABIERTAS -->
      <div v-show="tabActivo === 'abiertas'" class="tab-pane-inner">
        <div v-if="abiertasLoading" class="estado-carga">
          <div class="spinner-border spinner-border-sm text-warning"></div>
          <span>Cargando comandas abiertas...</span>
        </div>
        <div v-else-if="!abiertas.length" class="estado-vacio">
          <i class="bi bi-check-circle"></i>
          <p>No hay comandas abiertas en este momento.</p>
        </div>
        <div v-else class="comandas-grid">
          <div v-for="cmd in abiertas" :key="cmd.order_number" class="comanda-card comanda-card--abierta">
            <div class="comanda-top">
              <span class="comanda-mesa">
                <i class="bi bi-table me-1"></i>{{ cmd.table_name || 'Sin mesa' }}
              </span>
              <span class="comanda-hora">{{ cmd.hora_apertura }}</span>
            </div>
            <div class="comanda-mid">
              <span class="comanda-mesero">
                <i class="bi bi-person me-1"></i>{{ cmd.waiter_name || '—' }}
              </span>
              <span class="comanda-items">
                <i class="bi bi-list-ul me-1"></i>{{ cmd.item_count }} ítem(s)
              </span>
              <span v-if="cmd.guests_count" class="comanda-guests">
                <i class="bi bi-people me-1"></i>{{ cmd.guests_count }}
              </span>
            </div>
            <div class="comanda-bot">
              <span class="comanda-monto">{{ fmt(cmd.amount) }}</span>
              <span class="comanda-num"># {{ cmd.order_number }}</span>
            </div>
            <div v-if="cmd.notes" class="comanda-notas">
              <i class="bi bi-chat-left-text me-1"></i>{{ cmd.notes }}
            </div>
          </div>
        </div>
      </div>

      <!-- TAB 3: FACTURADAS -->
      <div v-show="tabActivo === 'facturadas'" class="tab-pane-inner">
        <div v-if="facturadasLoading" class="estado-carga">
          <div class="spinner-border spinner-border-sm text-success"></div>
          <span>Cargando facturadas...</span>
        </div>
        <div v-else-if="!facturadas.length" class="estado-vacio">
          <i class="bi bi-receipt"></i>
          <p>No hay ventas facturadas para esta fecha.</p>
        </div>
        <div v-else class="comandas-grid">
          <div v-for="cmd in facturadas" :key="cmd.order_number" class="comanda-card comanda-card--facturada">
            <div class="comanda-top">
              <span class="comanda-mesa">
                <i class="bi bi-table me-1"></i>{{ cmd.table_name || 'Sin mesa' }}
              </span>
              <span class="comanda-hora">{{ cmd.hora_cierre }}</span>
            </div>
            <div class="comanda-mid">
              <span class="comanda-mesero">
                <i class="bi bi-person me-1"></i>{{ cmd.waiter_name || '—' }}
              </span>
              <span v-if="cmd.guests_count" class="comanda-guests">
                <i class="bi bi-people me-1"></i>{{ cmd.guests_count }}
              </span>
            </div>
            <div class="comanda-bot">
              <span class="comanda-monto">{{ fmt(cmd.amount) }}</span>
              <span class="comanda-num">Fctr: {{ cmd.invoice_number }}</span>
            </div>
          </div>
        </div>
      </div>

    </div><!-- /tab-content -->

    <!-- MODAL ABRIR MESA -->
    <div v-if="modalMesa.visible" class="modal-overlay" @click.self="cerrarModal">
      <div class="modal-card">
        <div class="modal-header-custom">
          <span><i class="bi bi-table me-2"></i>{{ modalMesa.nombre }}</span>
          <button class="btn-close-modal" @click="cerrarModal"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-body-custom">
          <div class="campo-grupo">
            <label>Mesero</label>
            <select v-model="modalMesa.waiter_id" class="campo-select">
              <option value="0">— Sin asignar —</option>
              <option v-for="m in meseros" :key="m.id" :value="m.id">{{ m.name }}</option>
            </select>
          </div>
          <div class="campo-grupo">
            <label>Comensales</label>
            <input type="number" v-model.number="modalMesa.guests_count" min="1" class="campo-input" placeholder="Cantidad de personas" />
          </div>
          <div class="campo-grupo">
            <label>Notas <small class="text-muted">(opcional)</small></label>
            <input type="text" v-model="modalMesa.notes" class="campo-input" placeholder="Alergias, preferencias..." maxlength="250" />
          </div>
        </div>
        <div class="modal-footer-custom">
          <button class="btn-cancelar" @click="cerrarModal">Cancelar</button>
          <button class="btn-abrir" :disabled="modalMesa.guardando" @click="confirmarAbrirMesa">
            <span v-if="modalMesa.guardando">
              <span class="spinner-border spinner-border-sm me-1"></span>Abriendo...
            </span>
            <span v-else><i class="bi bi-check-lg me-1"></i>Abrir Mesa</span>
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import KpiStrip from '@/components/dashboard/KpiStrip.vue'
import api from '@/services/apis.js'
import { useCompanyStore } from '@/stores/companyStore.js'

const companyStore = useCompanyStore()

// ── Estado ────────────────────────────────────────────────────────────────────
const fecha      = ref(new Date().toISOString().slice(0, 10))  // controla tab Facturadas
const fechaKpi   = ref(new Date().toISOString().slice(0, 10))  // controla KPIs Facturas/Recibos
const tabActivo  = ref('nueva')

const kpiLoading        = ref(true)
const mesasLoading      = ref(true)
const abiertasLoading   = ref(false)
const facturadasLoading = ref(false)

const kpiData    = ref(null)
const mesas      = ref([])
const meseros    = ref([])
const abiertas   = ref([])
const facturadas = ref([])

const modalMesa = ref({
  visible: false, id: 0, nombre: '',
  waiter_id: 0, guests_count: 1, notes: '', guardando: false,
})

// ── Formato moneda COP ────────────────────────────────────────────────────────
const fmtCOP = new Intl.NumberFormat('es-CO', {
  style: 'currency', currency: 'COP',
  minimumFractionDigits: 0, maximumFractionDigits: 0,
})
const fmt = (v) => fmtCOP.format(v || 0)

// ── KPIs computados ───────────────────────────────────────────────────────────
const kpis = computed(() => {
  const d = kpiData.value
  if (!d) return [
    { icon: 'bi-receipt-cutoff', label: 'Ventas Facturas',   value: '—' },
    { icon: 'bi-journal-text',   label: 'Ventas Recibos',    value: '—' },
    { icon: 'bi-graph-up-arrow', label: 'Total Fact+Rec',    value: '—' },
    { icon: 'bi-table',          label: 'Comandas Abiertas', value: '—' },
    { icon: 'bi-globe',          label: 'Plataforma',        value: '—' },
  ]
  const totalFactRec = d.ventas_facturas.total + d.ventas_recibos.total
  const countFactRec = d.ventas_facturas.count + d.ventas_recibos.count
  return [
    { icon: 'bi-receipt-cutoff', label: `Facturas (${d.ventas_facturas.count})`,   value: fmt(d.ventas_facturas.total) },
    { icon: 'bi-journal-text',   label: `Recibos (${d.ventas_recibos.count})`,     value: fmt(d.ventas_recibos.total) },
    { icon: 'bi-graph-up-arrow', label: `Total (${countFactRec})`,                 value: fmt(totalFactRec) },
    { icon: 'bi-table',          label: `Abiertas (${d.comandas_abiertas.count})`, value: fmt(d.comandas_abiertas.total) },
    { icon: 'bi-globe',          label: `Plataforma (${d.plataforma.count})`,      value: fmt(d.plataforma.total) },
  ]
})

// ── Zonas de mesas ────────────────────────────────────────────────────────────
const zonas = computed(() => [...new Set(mesas.value.map(m => m.zone_id || ''))])
const mesasPorZona = (zona) => mesas.value.filter(m => (m.zone_id || '') === zona)

// ── Carga inicial ─────────────────────────────────────────────────────────────
onMounted(() => Promise.all([cargarKpis(), cargarMesas(), cargarMeseros()]))

watch(fechaKpi, () => cargarKpis())

const selectedCid = computed(() => companyStore.selectedCompany?.id || undefined)

async function cargarKpis() {
  kpiLoading.value = true
  try {
    const { data } = await api.get('/api/pos-dashboard/kpis', { params: { fecha: fechaKpi.value, company_id: selectedCid.value } })
    kpiData.value = data
  } catch {
    kpiData.value = null
  } finally {
    kpiLoading.value = false
  }
}

async function cargarMesas() {
  mesasLoading.value = true
  try {
    const { data } = await api.get('/api/pos-dashboard/mesas', { params: { company_id: selectedCid.value } })
    mesas.value = data
  } catch {
    mesas.value = []
  } finally {
    mesasLoading.value = false
  }
}

async function cargarMeseros() {
  try {
    const { data } = await api.get('/api/pos-dashboard/meseros', { params: { company_id: selectedCid.value } })
    meseros.value = data
  } catch {
    meseros.value = []
  }
}

async function cargarAbiertas() {
  if (abiertasLoading.value) return
  abiertasLoading.value = true
  try {
    const { data } = await api.get('/api/pos-dashboard/abiertas', { params: { company_id: selectedCid.value } })
    abiertas.value = data
  } catch {
    abiertas.value = []
  } finally {
    abiertasLoading.value = false
  }
}

async function cargarFacturadas() {
  if (facturadasLoading.value) return
  facturadasLoading.value = true
  try {
    const { data } = await api.get('/api/pos-dashboard/facturadas', { params: { fecha: fecha.value, company_id: selectedCid.value } })
    facturadas.value = data
  } catch {
    facturadas.value = []
  } finally {
    facturadasLoading.value = false
  }
}

function onFechaChange() {
  if (tabActivo.value === 'facturadas') cargarFacturadas()
}

// ── Modal ─────────────────────────────────────────────────────────────────────
function abrirModalMesa(mesa) {
  modalMesa.value = { visible: true, id: mesa.id, nombre: mesa.name, waiter_id: 0, guests_count: 1, notes: '', guardando: false }
}
function abrirModalTakeout() {
  modalMesa.value = { visible: true, id: 0, nombre: 'Para Llevar', waiter_id: 0, guests_count: 1, notes: '', guardando: false }
}
function cerrarModal() { modalMesa.value.visible = false }

async function confirmarAbrirMesa() {
  modalMesa.value.guardando = true
  try {
    await api.post('/api/pos-dashboard/abrir-mesa', {
      table_id:     modalMesa.value.id,
      table_name:   modalMesa.value.nombre,
      waiter_id:    modalMesa.value.waiter_id,
      guests_count: modalMesa.value.guests_count,
      notes:        modalMesa.value.notes,
      delivery:     0,
    }, { params: { company_id: selectedCid.value } })
    cerrarModal()
    await Promise.all([cargarMesas(), cargarKpis()])
    tabActivo.value = 'abiertas'
    await cargarAbiertas()
  } catch (e) {
    alert(e?.response?.data?.detail || 'Error al abrir la mesa')
  } finally {
    modalMesa.value.guardando = false
  }
}
</script>

<style scoped>
/* ── Cabecera ─────────────────────────────────────────────────────────────── */
.dash-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.dash-title {
  font-weight: 700;
  font-size: 15px;
  color: #1e3a5f;
  margin: 0;
}
.fechero-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #f0f4ff;
  border: 1px solid #c7d7f5;
  border-radius: 8px;
  padding: 5px 10px;
  color: #1d4ed8;
  font-size: 13px;
}
.fechero-input {
  border: none;
  background: transparent;
  color: #1d4ed8;
  font-size: 13px;
  font-weight: 600;
  outline: none;
  cursor: pointer;
}

/* ── Tabs ─────────────────────────────────────────────────────────────────── */
.dash-tabs { border-bottom: 2px solid #e2e8f0; margin-bottom: 0; gap: 2px; }
.dash-tabs .nav-link {
  border: none;
  border-bottom: 3px solid transparent;
  border-radius: 0;
  color: #64748b;
  font-size: 13px;
  font-weight: 500;
  padding: 10px 16px;
  transition: color .15s, border-color .15s;
}
.dash-tabs .nav-link:hover { color: #1d4ed8; }
.dash-tabs .nav-link.active {
  color: #1d4ed8;
  border-bottom-color: #1d4ed8;
  background: transparent;
  font-weight: 700;
}
.badge-abierta   { background: #f59e0b; color: #fff; font-size: 11px; padding: 2px 6px; border-radius: 10px; }
.badge-facturada { background: #10b981; color: #fff; font-size: 11px; padding: 2px 6px; border-radius: 10px; }

.dash-tab-content { padding-top: 16px; }
.tab-pane-inner   { min-height: 200px; }

/* ── Estados ──────────────────────────────────────────────────────────────── */
.estado-carga, .estado-vacio {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 180px;
  color: #94a3b8;
  font-size: 14px;
  text-align: center;
}
.estado-vacio i { font-size: 40px; }

/* ── Acciones rápidas ─────────────────────────────────────────────────────── */
.acciones-rapidas { display: flex; gap: 10px; margin-bottom: 20px; }
.btn-accion {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 2px solid #1d4ed8;
  border-radius: 8px;
  background: #fff;
  color: #1d4ed8;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background .15s, color .15s;
}
.btn-accion:hover      { background: #1d4ed8; color: #fff; }
.btn-accion--web       { border-color: #7c3aed; color: #7c3aed; }
.btn-accion--web:hover { background: #7c3aed; color: #fff; }

/* ── Zonas ────────────────────────────────────────────────────────────────── */
.zona-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .5px;
  color: #94a3b8;
  margin: 16px 0 8px;
}

/* ── Grid de mesas ────────────────────────────────────────────────────────── */
.mesas-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 10px;
}
.mesa-card {
  border-radius: 12px;
  border: 2px solid #e2e8f0;
  padding: 12px;
  text-align: center;
  cursor: pointer;
  transition: transform .15s, box-shadow .15s, border-color .15s;
  background: #fff;
}
.mesa-card--libre:hover {
  border-color: #1d4ed8;
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(29,78,216,.15);
}
.mesa-card--ocupada { border-color: #f59e0b; background: #fffbeb; cursor: default; }
.mesa-icon { font-size: 22px; margin-bottom: 4px; }
.mesa-card--libre   .mesa-icon { color: #10b981; }
.mesa-card--ocupada .mesa-icon { color: #f59e0b; }
.mesa-nombre { font-weight: 700; font-size: 13px; color: #1e3a5f; margin-bottom: 4px; }
.mesa-info   { font-size: 11px; display: flex; flex-direction: column; gap: 2px; }
.mesa-estado.libre   { color: #10b981; font-weight: 600; }
.mesa-estado.ocupada { color: #f59e0b; font-weight: 600; }
.mesa-mesero { color: #64748b; }
.mesa-monto  { color: #1e3a5f; font-weight: 700; }

/* ── Grid de comandas ─────────────────────────────────────────────────────── */
.comandas-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}
.comanda-card {
  border-radius: 12px;
  border: 2px solid #e2e8f0;
  padding: 14px;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.comanda-card--abierta  { border-color: #f59e0b; background: #fffdf5; }
.comanda-card--facturada { border-color: #10b981; background: #f0fdf7; }
.comanda-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.comanda-mesa { font-weight: 700; font-size: 14px; color: #1e3a5f; }
.comanda-hora { font-size: 12px; color: #94a3b8; }
.comanda-mid  { display: flex; gap: 10px; flex-wrap: wrap; font-size: 12px; color: #64748b; }
.comanda-bot  { display: flex; justify-content: space-between; align-items: center; margin-top: 4px; }
.comanda-monto { font-size: 18px; font-weight: 800; color: #1e3a5f; }
.comanda-num   { font-size: 11px; color: #94a3b8; }
.comanda-notas {
  font-size: 11px;
  color: #64748b;
  background: #f8fafc;
  border-radius: 6px;
  padding: 4px 8px;
}

/* ── Modal ────────────────────────────────────────────────────────────────── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
}
.modal-card {
  background: #fff;
  border-radius: 16px;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 20px 60px rgba(0,0,0,.25);
  overflow: hidden;
}
.modal-header-custom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(90deg, #1e3a5f, #1d4ed8);
  color: #fff;
  font-weight: 700;
  font-size: 15px;
}
.btn-close-modal { background: none; border: none; color: #fff; cursor: pointer; font-size: 16px; opacity: .8; }
.btn-close-modal:hover { opacity: 1; }
.modal-body-custom  { padding: 20px; display: flex; flex-direction: column; gap: 14px; }
.campo-grupo        { display: flex; flex-direction: column; gap: 4px; }
.campo-grupo label  { font-size: 12px; font-weight: 600; color: #475569; }
.campo-select,
.campo-input {
  border: 1.5px solid #cbd5e1;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 14px;
  color: #1e3a5f;
  outline: none;
  transition: border-color .15s;
  width: 100%;
}
.campo-select:focus,
.campo-input:focus { border-color: #1d4ed8; }
.modal-footer-custom {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  padding: 14px 20px;
  border-top: 1px solid #f1f5f9;
}
.btn-cancelar {
  background: #f1f5f9;
  border: none;
  border-radius: 8px;
  padding: 9px 18px;
  font-size: 14px;
  cursor: pointer;
  color: #475569;
  font-weight: 600;
}
.btn-cancelar:hover { background: #e2e8f0; }
.btn-abrir {
  background: linear-gradient(90deg, #1e3a5f, #1d4ed8);
  border: none;
  border-radius: 8px;
  padding: 9px 20px;
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  cursor: pointer;
  transition: opacity .15s;
}
.btn-abrir:disabled { opacity: .6; cursor: not-allowed; }

/* ── Responsive ───────────────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .dash-header   { flex-direction: column; align-items: flex-start; gap: 10px; }
  .mesas-grid    { grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); }
  .comandas-grid { grid-template-columns: 1fr; }
  .dash-tabs .nav-link { padding: 8px 10px; font-size: 12px; }
}
@media (max-width: 576px) {
  .acciones-rapidas { flex-direction: column; }
  .mesas-grid { grid-template-columns: repeat(3, 1fr); }
}
</style>
