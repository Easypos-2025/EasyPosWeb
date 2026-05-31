<template>
  <div class="dashboard-content">

    <!-- KPI BAR -->
    <KpiStrip :kpis="kpis" :loading="kpiLoading" :showLabels="true" v-model="fechaKpi" />

    <!-- CABECERA -->
    <div class="dash-header">
      <h6 class="dash-title">{{ companyStore.selectedCompany?.name || 'Panel de Operaciones' }}</h6>
      <div class="dash-header-right">
        <a :href="`/pos/cocina?cid=${selectedCid}`" target="_blank" class="btn-tv" title="Abrir Cocina TV">
          <i class="bi bi-display me-1"></i>
          <span class="btn-tv-label">Ver Cocina TV</span>
        </a>
        <button class="btn-refresh" @click="cargarTodo" :disabled="cargandoTodo" title="Actualizar">
          <i class="bi" :class="cargandoTodo ? 'bi-arrow-repeat spin' : 'bi-arrow-clockwise'"></i>
        </button>
      </div>
    </div>

    <!-- CUERPO: tabs + sidebar -->
    <div class="dash-body">

      <!-- ── Columna principal ── -->
      <div class="dash-main">
        <ul class="nav nav-tabs dash-tabs" role="tablist">
          <li class="nav-item">
            <button class="nav-link" :class="{ active: tabActivo === 'nueva' }" @click="tabActivo = 'nueva'">
              <i class="bi bi-plus-circle me-1"></i>Nuevo Pedido
            </button>
          </li>
          <li class="nav-item">
            <button class="nav-link" :class="{ active: tabActivo === 'abiertas' }" @click="tabActivo = 'abiertas'; cargarAbiertas()">
              <i class="bi bi-table me-1"></i>Abiertas
              <span v-if="abiertas.length" class="badge badge-abierta ms-1">{{ abiertas.length }}</span>
            </button>
          </li>
          <li class="nav-item">
            <button class="nav-link" :class="{ active: tabActivo === 'facturadas' }" @click="tabActivo = 'facturadas'; cargarFacturadas()">
              <i class="bi bi-receipt me-1"></i>Facturadas
              <span v-if="facturadas.length" class="badge badge-facturada ms-1">{{ facturadas.length }}</span>
            </button>
          </li>
        </ul>

        <div class="tab-content dash-tab-content">

          <!-- TAB: NUEVO PEDIDO -->
          <div v-show="tabActivo === 'nueva'" class="tab-pane-inner">
            <!-- Botón principal para iniciar pedido -->
            <div class="nuevo-pedido-hero">
              <button class="btn-iniciar" @click="abrirWizard">
                <i class="bi bi-plus-circle-fill"></i>
                <span>Iniciar Nuevo Pedido</span>
              </button>
              <button class="btn-accion btn-accion--llevar" @click="abrirWizardTakeout">
                <i class="bi bi-bag-check"></i>
                <span>Para Llevar</span>
              </button>
            </div>

            <!-- Mini-resumen de mesas abiertas -->
            <div v-if="mesasLoading" class="estado-carga">
              <div class="spinner-border spinner-border-sm text-primary"></div>
              <span>Cargando mesas...</span>
            </div>
            <template v-else>
              <div class="zona-label"><i class="bi bi-geo-alt"></i> Estado de mesas</div>
              <div v-if="!mesas.length" class="estado-vacio">
                <i class="bi bi-grid-3x3-gap"></i>
                <p>No hay mesas configuradas.</p>
              </div>
              <template v-else>
                <div class="mesas-leyenda">
                  <span class="leyenda-item"><span class="leyenda-dot leyenda-dot--libre"></span>Libre</span>
                  <span class="leyenda-item"><span class="leyenda-dot leyenda-dot--ocupada"></span>Ocupada</span>
                  <span class="leyenda-item"><span class="leyenda-dot leyenda-dot--cuenta"></span>Pide cuenta</span>
                </div>
                <template v-for="zona in zonas" :key="zona.id">
                  <div class="zona-label"><i class="bi bi-geo-alt"></i> {{ zona.name }}</div>
                  <div class="mesas-grid">
                    <div
                      v-for="mesa in mesasPorZona(zona.id)"
                      :key="mesa.id"
                      class="mesa-card"
                      :class="{
                        'mesa-card--libre':    !mesa.ocupada && !mesa.bill_requested,
                        'mesa-card--ocupada':   mesa.ocupada && !mesa.bill_requested,
                        'mesa-card--cuenta':    mesa.bill_requested,
                      }"
                      @click="handleMesaClick(mesa)"
                    >
                      <div class="mesa-status-bar"></div>
                      <div class="mesa-icon">
                        <i class="bi" :class="mesa.bill_requested ? 'bi-receipt' : mesa.ocupada ? 'bi-person-fill' : 'bi-table'"></i>
                      </div>
                      <div class="mesa-nombre">{{ mesa.name }}</div>
                      <div class="mesa-info">
                        <template v-if="mesa.ocupada || mesa.bill_requested">
                          <span v-if="mesa.daily_seq" class="mesa-seq">#{{ mesa.daily_seq }}</span>
                          <span class="mesa-mesero">{{ mesa.waiter_name || '—' }}</span>
                          <span class="mesa-monto">{{ fmt(mesa.amount) }}</span>
                        </template>
                        <span v-else class="mesa-seats">{{ mesa.seats }} sillas</span>
                      </div>
                    </div>
                  </div>
                </template>
              </template>
            </template>
          </div>

          <!-- TAB: ABIERTAS -->
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
                  <span class="comanda-mesa"><i class="bi bi-table me-1"></i>{{ cmd.table_name || 'Sin mesa' }}</span>
                  <span class="comanda-hora">{{ cmd.hora_apertura }}</span>
                </div>
                <div class="comanda-mid">
                  <span class="comanda-mesero"><i class="bi bi-person me-1"></i>{{ cmd.waiter_name || '—' }}</span>
                  <span class="comanda-items"><i class="bi bi-list-ul me-1"></i>{{ cmd.item_count }} ítem(s)</span>
                  <span v-if="cmd.guests_count" class="comanda-guests"><i class="bi bi-people me-1"></i>{{ cmd.guests_count }}</span>
                </div>
                <div class="comanda-bot">
                  <span class="comanda-monto">{{ fmt(cmd.amount) }}</span>
                  <span class="comanda-num"># {{ cmd.order_number }}</span>
                </div>
                <div v-if="cmd.notes" class="comanda-notas"><i class="bi bi-chat-left-text me-1"></i>{{ cmd.notes }}</div>
              </div>
            </div>
          </div>

          <!-- TAB: FACTURADAS -->
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
                  <span class="comanda-mesa"><i class="bi bi-table me-1"></i>{{ cmd.table_name || 'Sin mesa' }}</span>
                  <span class="comanda-hora">{{ cmd.hora_cierre }}</span>
                </div>
                <div class="comanda-mid">
                  <span class="comanda-mesero"><i class="bi bi-person me-1"></i>{{ cmd.waiter_name || '—' }}</span>
                  <span v-if="cmd.guests_count" class="comanda-guests"><i class="bi bi-people me-1"></i>{{ cmd.guests_count }}</span>
                </div>
                <div class="comanda-bot">
                  <span class="comanda-monto">{{ fmt(cmd.amount) }}</span>
                  <span class="comanda-num">Fctr: {{ cmd.invoice_number }}</span>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div><!-- /dash-main -->

      <!-- ── Sidebar ── -->
      <div class="dash-side">
        <!-- Stock crítico -->
        <div class="side-section">
          <div class="side-header">
            <span><i class="bi bi-exclamation-triangle me-1 text-danger"></i>Stock crítico</span>
            <span v-if="stockAlertas.length" class="badge bg-danger">{{ stockAlertas.length }}</span>
          </div>
          <div v-if="cargandoStock" class="side-loading">
            <div class="spinner-border spinner-border-sm text-danger"></div>
          </div>
          <div v-else-if="!stockAlertas.length" class="side-ok">
            <i class="bi bi-check-circle-fill text-success me-1"></i>
            <span>Todo en orden</span>
          </div>
          <div v-else class="stock-list">
            <div v-for="item in stockAlertas" :key="item.id" class="stock-item">
              <div class="stock-item-info">
                <div class="stock-item-name">{{ item.name }}</div>
                <div class="stock-item-unit">{{ item.unit_name || '' }}</div>
              </div>
              <div class="stock-item-nums">
                <span :class="item.stock_qty <= 0 ? 'text-danger fw-bold' : 'text-warning fw-bold'">
                  {{ formatNum(item.stock_qty) }}
                </span>
                <span class="text-muted small"> / {{ formatNum(item.min_stock) }}</span>
              </div>
            </div>
          </div>
        </div>
        <!-- Últimas transacciones -->
        <div class="side-section">
          <div class="side-header">
            <span><i class="bi bi-clock-history me-1"></i>Últimas transacciones</span>
            <span class="badge bg-secondary-subtle text-secondary small">{{ fechaKpi === hoy ? 'Hoy' : fechaKpi }}</span>
          </div>
          <div v-if="cargandoTx" class="side-loading">
            <div class="spinner-border spinner-border-sm text-primary"></div>
          </div>
          <div v-else-if="!transacciones.length" class="side-empty">Sin transacciones</div>
          <div v-else class="tx-wrap">
            <table class="tx-table">
              <thead><tr><th>Hora</th><th>Tipo</th><th>N°</th><th class="text-end">Total</th></tr></thead>
              <tbody>
                <tr v-for="tx in transacciones" :key="tx.tipo + tx.numero">
                  <td class="tx-hora">{{ tx.hora?.substring(0,5) }}</td>
                  <td><span class="badge-tx" :class="tx.tipo === 'Factura' ? 'tx-fact' : 'tx-rec'">{{ tx.tipo }}</span></td>
                  <td class="tx-num">{{ tx.numero }}</td>
                  <td class="text-end tx-total">{{ fmt(tx.total) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

    </div><!-- /dash-body -->

    <!-- ══════════════════════════════════════════════════════════
         WIZARD: NUEVO PEDIDO (mesero → zona/mesa en acordeón)
    ══════════════════════════════════════════════════════════ -->
    <div v-if="wizard.visible" class="wizard-overlay" @click.self="cerrarWizard">
      <div class="wizard-modal">

        <!-- Header -->
        <div class="wizard-header">
          <div class="wizard-steps">
            <span class="wstep" :class="{ active: wizard.step === 1, done: wizard.step > 1 }">
              <i class="bi bi-person-fill"></i>
              <span v-if="wizard.step > 1 && wizard.waiterId !== null">
                {{ meseros.find(m => m.id === wizard.waiterId)?.name || 'Sin asignar' }}
              </span>
              <span v-else>Mesero</span>
            </span>
            <span class="wstep-sep"></span>
            <span class="wstep" :class="{ active: wizard.step === 2, done: wizard.step > 2 }">
              <i class="bi bi-geo-alt-fill"></i>
              <span v-if="wizard.step > 2 && wizard.mesaSeleccionada">
                {{ wizard.mesaSeleccionada.name }}
              </span>
              <span v-else>Mesa</span>
            </span>
            <span class="wstep-sep"></span>
            <span class="wstep" :class="{ active: wizard.step === 3 }">
              <i class="bi bi-bug"></i> Debug
            </span>
          </div>
          <button class="wizard-close" @click="cerrarWizard"><i class="bi bi-x-lg"></i></button>
        </div>

        <!-- PASO 1: MESERO -->
        <div v-if="wizard.step === 1" class="wizard-body">
          <h6 class="wizard-section-title">¿Quién atiende la mesa?</h6>

          <div class="meseros-grid">
            <!-- Opción sin asignar -->
            <button
              class="mesero-card"
              :class="{ 'mesero-card--selected': wizard.waiterId === 0 }"
              @click="seleccionarMesero(0)"
            >
              <div class="mesero-avatar mesero-avatar--none"><i class="bi bi-person-dash"></i></div>
              <span class="mesero-name">Sin asignar</span>
            </button>

            <!-- Meseros -->
            <button
              v-for="m in meseros"
              :key="m.id"
              class="mesero-card"
              :class="{ 'mesero-card--selected': wizard.waiterId === m.id }"
              @click="seleccionarMesero(m.id)"
            >
              <div class="mesero-avatar">{{ m.name.charAt(0).toUpperCase() }}</div>
              <span class="mesero-name">{{ m.name }}</span>
            </button>

            <!-- Agregar mesero -->
            <button class="mesero-card mesero-card--add" @click="wizard.showAddWaiter = !wizard.showAddWaiter">
              <div class="mesero-avatar mesero-avatar--add"><i class="bi bi-plus-lg"></i></div>
              <span class="mesero-name">Agregar</span>
            </button>
          </div>

          <!-- Mini formulario agregar mesero -->
          <div v-if="wizard.showAddWaiter" class="add-waiter-form">
            <div class="aw-row">
              <input v-model="newWaiter.name" class="campo-input" placeholder="Nombre del mesero" maxlength="80" />
              <input v-model="newWaiter.pin" class="campo-input" placeholder="PIN (4 dígitos)" maxlength="4" type="password" />
              <button class="btn-aw-save" @click="guardarNuevoMesero" :disabled="newWaiter.saving">
                <span v-if="newWaiter.saving"><div class="spinner-border spinner-border-sm"></div></span>
                <span v-else><i class="bi bi-check-lg"></i></span>
              </button>
            </div>
            <p v-if="newWaiter.error" class="text-danger small mt-1">{{ newWaiter.error }}</p>
          </div>

          <div class="wizard-footer">
            <button class="btn-cancelar" @click="cerrarWizard">Cancelar</button>
          </div>
        </div>

        <!-- PASO 2: ZONA + MESA (acordeón) -->
        <div v-if="wizard.step === 2" class="wizard-body">
          <h6 class="wizard-section-title">Selecciona la mesa</h6>

          <div v-if="mesasLoading" class="estado-carga">
            <div class="spinner-border spinner-border-sm text-primary"></div>
            <span>Cargando mesas...</span>
          </div>
          <div v-else-if="!mesas.length" class="estado-vacio">
            <i class="bi bi-grid-3x3-gap"></i>
            <p>No hay mesas configuradas.</p>
            <!-- DEBUG temporal -->
            <div class="debug-card mt-2" style="text-align:left">
              <table class="debug-table">
                <tr><td class="debug-key">selectedCid</td><td class="debug-val">{{ selectedCid ?? 'undefined' }}</td></tr>
                <tr><td class="debug-key">mesas.length</td><td class="debug-val">{{ mesas.length }}</td></tr>
                <tr><td class="debug-key">error</td><td class="debug-val" style="color:#f87171">{{ mesasError || 'ninguno' }}</td></tr>
                <tr><td class="debug-key">companyStore</td><td class="debug-val">{{ companyStore.selectedCompany?.id ?? 'null' }} / {{ companyStore.selectedCompany?.name ?? '?' }}</td></tr>
              </table>
            </div>
          </div>
          <div v-else class="zonas-acordeon">
            <div
              v-for="zona in zonas"
              :key="zona.id"
              class="zona-acordeon"
            >
              <!-- Header zona -->
              <button
                class="zona-acordeon__header"
                :class="{ 'zona-acordeon__header--open': wizard.zonaAbierta === zona.id }"
                @click="wizard.zonaAbierta = wizard.zonaAbierta === zona.id ? null : zona.id"
              >
                <span>
                  <i class="bi bi-geo-alt-fill me-2"></i>
                  {{ zona.name }}
                  <span class="zona-count">{{ mesasPorZona(zona.id).length }}</span>
                </span>
                <i class="bi" :class="wizard.zonaAbierta === zona.id ? 'bi-chevron-up' : 'bi-chevron-down'"></i>
              </button>

              <!-- Mesas de la zona -->
              <div v-show="wizard.zonaAbierta === zona.id" class="zona-acordeon__body">
                <div class="mesas-grid-wizard">
                  <button
                    v-for="mesa in mesasPorZona(zona.id)"
                    :key="mesa.id"
                    class="mesa-wizard-card"
                    :class="{
                      'mesa-wizard-card--libre':    !mesa.ocupada && !mesa.bill_requested,
                      'mesa-wizard-card--ocupada':   mesa.ocupada && !mesa.bill_requested,
                      'mesa-wizard-card--cuenta':    mesa.bill_requested,
                    }"
                    :disabled="mesa.ocupada || mesa.bill_requested"
                    @click="seleccionarMesaWizard(mesa)"
                  >
                    <div class="mwc-status-bar"></div>
                    <i class="bi mwc-icon"
                      :class="mesa.bill_requested ? 'bi-receipt' : mesa.ocupada ? 'bi-person-fill' : 'bi-table'">
                    </i>
                    <span class="mwc-name">{{ mesa.name }}</span>
                    <span class="mwc-info">
                      <span v-if="mesa.ocupada || mesa.bill_requested" class="mwc-badge">
                        {{ mesa.bill_requested ? 'Cuenta' : 'Ocupada' }}
                      </span>
                      <span v-else class="mwc-seats">{{ mesa.seats }} sillas</span>
                    </span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div class="wizard-footer">
            <button class="btn-cancelar" @click="wizard.step = 1">
              <i class="bi bi-arrow-left me-1"></i>Volver
            </button>
          </div>
        </div>

        <!-- PASO 3: DEBUG — verificación temporal de datos recolectados -->
        <div v-if="wizard.step === 3" class="wizard-body">
          <h6 class="wizard-section-title"><i class="bi bi-bug me-2 text-warning"></i>Verificación de datos (temporal)</h6>
          <div class="debug-card">
            <table class="debug-table">
              <tbody>
                <tr>
                  <td class="debug-key">company_id</td>
                  <td class="debug-val">{{ selectedCid }}</td>
                </tr>
                <tr>
                  <td class="debug-key">waiter_id</td>
                  <td class="debug-val">{{ wizard.waiterId ?? 0 }}
                    <span class="debug-hint">{{ meseros.find(m => m.id === wizard.waiterId)?.name || (wizard.waiterId === 0 || wizard.waiterId === null ? 'Sin asignar' : '?') }}</span>
                  </td>
                </tr>
                <tr>
                  <td class="debug-key">table_id</td>
                  <td class="debug-val">{{ wizard.mesaSeleccionada?.id }}
                    <span class="debug-hint">{{ wizard.mesaSeleccionada?.name }}</span>
                  </td>
                </tr>
                <tr>
                  <td class="debug-key">zone_id</td>
                  <td class="debug-val">{{ wizard.mesaSeleccionada?.zone_id }}
                    <span class="debug-hint">{{ wizard.mesaSeleccionada?.zone_name }}</span>
                  </td>
                </tr>
                <tr>
                  <td class="debug-key">guests_count</td>
                  <td class="debug-val">1</td>
                </tr>
                <tr>
                  <td class="debug-key">waiter_company_id<br><small>(localStorage)</small></td>
                  <td class="debug-val">{{ selectedCid }}</td>
                </tr>
                <tr>
                  <td class="debug-key">token usado</td>
                  <td class="debug-val debug-token">{{ tokenDebugPrefix }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="wizard-footer">
            <button class="btn-cancelar" @click="wizard.step = 2">
              <i class="bi bi-arrow-left me-1"></i>Volver
            </button>
            <button class="btn-wizard-next" @click="irAComanda(wizard.mesaSeleccionada.id, wizard.mesaSeleccionada.name, wizard.waiterId ?? 0)" :disabled="wizard.abriendo">
              <span v-if="wizard.abriendo"><div class="spinner-border spinner-border-sm me-1"></div></span>
              <span v-else><i class="bi bi-check-circle me-1"></i></span>
              Abrir mesa
            </button>
          </div>
        </div>

        <!-- Loading state al abrir mesa -->
        <div v-if="wizard.abriendo" class="wizard-loading-overlay">
          <div class="spinner-border text-primary"></div>
          <span>Abriendo mesa...</span>
        </div>

      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import KpiStrip from '@/components/dashboard/KpiStrip.vue'
import api from '@/services/apis.js'
import apiComanda from '@/services/apiComanda.js'
import { useCompanyStore } from '@/stores/companyStore.js'

const companyStore = useCompanyStore()
const router = useRouter()
const hoy = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Bogota' }).format(new Date())

const fechaKpi       = ref(hoy)
const tabActivo      = ref('nueva')
const cargandoTodo   = ref(false)

const kpiLoading        = ref(true)
const mesasLoading      = ref(true)
const abiertasLoading   = ref(false)
const facturadasLoading = ref(false)
const cargandoStock     = ref(false)
const cargandoTx        = ref(false)

const kpiData       = ref(null)
const mesas         = ref([])
const meseros       = ref([])
const abiertas      = ref([])
const facturadas    = ref([])
const stockAlertas  = ref([])
const transacciones = ref([])

// ── Wizard nuevo pedido ───────────────────────────────────────────────────────
const wizard = ref({
  visible: false,
  step: 1,
  waiterId: null,
  zonaAbierta: null,
  abriendo: false,
  showAddWaiter: false,
  takeout: false,
  mesaSeleccionada: null,   // { id, name, zone_id, zone_name }
})
const newWaiter = ref({ name: '', pin: '', saving: false, error: '' })

// ── Formato ──────────────────────────────────────────────────────────────────
const fmtCOP = new Intl.NumberFormat('es-CO', {
  style: 'currency', currency: 'COP',
  minimumFractionDigits: 0, maximumFractionDigits: 0,
})
const fmt = (v) => fmtCOP.format(v || 0)
function formatNum(val) {
  return Number(val || 0).toLocaleString('es-CO', { maximumFractionDigits: 2 })
}

// ── KPIs ─────────────────────────────────────────────────────────────────────
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

const selectedCid  = computed(() => companyStore.selectedCompany?.id || undefined)
const zonas        = computed(() => {
  const seen = new Set()
  const result = []
  for (const m of mesas.value) {
    const key = m.zone_id ?? ''
    if (!seen.has(key)) { seen.add(key); result.push({ id: key, name: m.zone_name || 'Sin zona' }) }
  }
  return result
})
const mesasPorZona = (zoneId) => mesas.value.filter(m => (m.zone_id ?? '') === zoneId)

// ── Auto-refresh ──────────────────────────────────────────────────────────────
async function _silentKpis() {
  try {
    const { data } = await api.get('/api/pos-dashboard/kpis', {
      params: { fecha: fechaKpi.value, company_id: selectedCid.value, _t: Date.now() }
    })
    kpiData.value = data
  } catch { }
}
async function _silentMesas() {
  try {
    const { data } = await api.get('/api/pos-dashboard/mesas', {
      params: { company_id: selectedCid.value, _t: Date.now() }
    })
    mesas.value = data
  } catch { }
}
function _tick() {
  _silentKpis()
  _silentMesas()
  if (tabActivo.value === 'abiertas') cargarAbiertas()
}

let _timer = null
function _startRefresh() { _stopRefresh(); _timer = setInterval(_tick, 15000) }
function _stopRefresh()  { if (_timer) { clearInterval(_timer); _timer = null } }
function _onVisible()    { if (!document.hidden) _tick() }

onMounted(async () => {
  await Promise.all([
    cargarKpis(), cargarMesas(), cargarMeseros(), cargarStock(), cargarTransacciones()
  ])
  _startRefresh()
  document.addEventListener('visibilitychange', _onVisible)
})
onUnmounted(() => {
  _stopRefresh()
  document.removeEventListener('visibilitychange', _onVisible)
})

watch(fechaKpi, () => {
  cargarKpis()
  cargarTransacciones()
  if (tabActivo.value === 'facturadas') cargarFacturadas()
})

// ── Carga de datos ────────────────────────────────────────────────────────────
async function cargarTodo() {
  cargandoTodo.value = true
  try {
    await Promise.all([
      cargarKpis(), cargarMesas(), cargarMeseros(), cargarStock(), cargarTransacciones()
    ])
  } finally {
    cargandoTodo.value = false
  }
}

async function cargarKpis() {
  kpiLoading.value = true
  try {
    const { data } = await api.get('/api/pos-dashboard/kpis', {
      params: { fecha: fechaKpi.value, company_id: selectedCid.value }
    })
    kpiData.value = data
  } catch { kpiData.value = null }
  finally { kpiLoading.value = false }
}

const tokenDebugPrefix = computed(() => {
  const t = window.localStorage?.getItem('waiter_token') || window.localStorage?.getItem('token') || ''
  return t ? t.substring(0, 40) + '…' : '(sin token)'
})

const mesasError = ref('')
async function cargarMesas() {
  mesasLoading.value = true
  mesasError.value = ''
  try {
    const cid = selectedCid.value
    const { data } = await api.get('/api/pos-dashboard/mesas', {
      params: { company_id: cid }
    })
    mesas.value = data
    if (!data.length) mesasError.value = `API ok pero 0 mesas (cid=${cid})`
  } catch (e) {
    mesas.value = []
    mesasError.value = e?.response?.data?.detail || e?.message || 'Error desconocido'
  }
  finally { mesasLoading.value = false }
}

async function cargarMeseros() {
  try {
    const { data } = await api.get('/api/pos-dashboard/meseros', {
      params: { company_id: selectedCid.value }
    })
    meseros.value = data
  } catch { meseros.value = [] }
}

async function cargarAbiertas() {
  if (abiertasLoading.value) return
  abiertasLoading.value = true
  try {
    const { data } = await api.get('/api/pos-dashboard/abiertas', {
      params: { company_id: selectedCid.value }
    })
    abiertas.value = data
  } catch { abiertas.value = [] }
  finally { abiertasLoading.value = false }
}

async function cargarFacturadas() {
  if (facturadasLoading.value) return
  facturadasLoading.value = true
  try {
    const { data } = await api.get('/api/pos-dashboard/facturadas', {
      params: { fecha: fechaKpi.value, company_id: selectedCid.value }
    })
    facturadas.value = data
  } catch { facturadas.value = [] }
  finally { facturadasLoading.value = false }
}

async function cargarStock() {
  cargandoStock.value = true
  try {
    const { data } = await api.get('/api/pos-dashboard/stock-alertas', {
      params: { company_id: selectedCid.value }
    })
    stockAlertas.value = data
  } catch { stockAlertas.value = [] }
  finally { cargandoStock.value = false }
}

async function cargarTransacciones() {
  cargandoTx.value = true
  try {
    const { data } = await api.get('/api/pos-dashboard/ultimas-transacciones', {
      params: { fecha: fechaKpi.value, company_id: selectedCid.value }
    })
    transacciones.value = data
  } catch { transacciones.value = [] }
  finally { cargandoTx.value = false }
}

// ── Mesa click desde vista de estado ─────────────────────────────────────────
function handleMesaClick(mesa) {
  if (!mesa.ocupada && !mesa.bill_requested) {
    abrirWizard()
    wizard.value.zonaAbierta = mesa.zone_id ?? null
  }
}

// ── Wizard ────────────────────────────────────────────────────────────────────
function abrirWizard() {
  wizard.value = {
    visible: true, step: 1,
    waiterId: null, zonaAbierta: zonas.value[0]?.id ?? null,
    abriendo: false, showAddWaiter: false, takeout: false,
    mesaSeleccionada: null,
  }
  newWaiter.value = { name: '', pin: '', saving: false, error: '' }
  // Forzar recarga para asegurar datos frescos
  cargarMesas()
  cargarMeseros()
}

function seleccionarMesero(waiterId) {
  wizard.value.waiterId = waiterId
  wizard.value.showAddWaiter = false
  wizard.value.step = 2
}

function abrirWizardTakeout() {
  // Para Llevar: va directo al pedido con table_id=0
  irAComanda(0, 'Para Llevar', 0)
}

function cerrarWizard() { wizard.value.visible = false }

function seleccionarMesaWizard(mesa) {
  if (mesa.ocupada || mesa.bill_requested) return
  wizard.value.mesaSeleccionada = mesa
  wizard.value.step = 3
}

async function irAComanda(tableId, tableName, waiterId) {
  wizard.value.abriendo = true
  try {
    localStorage.setItem('waiter_company_id', String(selectedCid.value))

    const { data } = await apiComanda.post('/api/pos/comanda/mesa/abrir', {
      table_id:     tableId,
      guests_count: 1,
      waiter_id:    waiterId || 0,
    })

    // Guardar contexto del wizard para que PosComandaPedidoView lo muestre
    const waiterName = meseros.value.find(m => m.id === waiterId)?.name || 'Sin asignar'
    localStorage.setItem('pedido_ctx', JSON.stringify({
      table_id:    tableId,
      table_name:  tableName,
      waiter_id:   waiterId || 0,
      waiter_name: waiterName,
      order_number: data.order_number,
      date:         data.date,
      company_id:   selectedCid.value,
    }))

    cerrarWizard()
    router.push(`/pos/comanda/pedido/${tableId}`)
  } catch (e) {
    alert(e?.response?.data?.detail || 'Error al abrir la mesa')
  } finally {
    wizard.value.abriendo = false
  }
}

async function guardarNuevoMesero() {
  if (!newWaiter.value.name.trim()) {
    newWaiter.value.error = 'El nombre es obligatorio'
    return
  }
  if (newWaiter.value.pin.length < 4) {
    newWaiter.value.error = 'El PIN debe tener 4 dígitos'
    return
  }
  newWaiter.value.saving = true
  newWaiter.value.error = ''
  try {
    await api.post('/api/pos-dashboard/mesero', {
      name:       newWaiter.value.name.trim(),
      pin:        newWaiter.value.pin,
      company_id: selectedCid.value,
    })
    await cargarMeseros()
    newWaiter.value = { name: '', pin: '', saving: false, error: '' }
    wizard.value.showAddWaiter = false
  } catch (e) {
    newWaiter.value.error = e?.response?.data?.detail || 'Error al guardar'
  } finally {
    newWaiter.value.saving = false
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
  gap: 10px;
}
.dash-title { font-weight: 700; font-size: 15px; color: #1e3a5f; margin: 0; }
.dash-header-right { display: flex; align-items: center; gap: 8px; }

.btn-tv {
  display: flex;
  align-items: center;
  padding: 6px 14px;
  border: 1.5px solid #0f172a;
  border-radius: 8px;
  background: #0f172a;
  color: #f1f5f9;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  transition: background .15s;
  white-space: nowrap;
}
.btn-tv:hover { background: #1e293b; color: #fff; }

.btn-refresh {
  width: 34px;
  height: 34px;
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
  color: #64748b;
  font-size: 15px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background .15s;
  flex-shrink: 0;
}
.btn-refresh:hover:not(:disabled) { background: #f1f5f9; color: #1d4ed8; }
.btn-refresh:disabled { opacity: .5; cursor: not-allowed; }
.spin { animation: spin .8s linear infinite; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Layout ───────────────────────────────────────────────────────────────── */
.dash-body {
  display: grid;
  grid-template-columns: 1fr 290px;
  gap: 16px;
  align-items: start;
}
.dash-main { min-width: 0; }

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
.dash-tabs .nav-link.active { color: #1d4ed8; border-bottom-color: #1d4ed8; background: transparent; font-weight: 700; }
.badge-abierta   { background: #f59e0b; color: #fff; font-size: 11px; padding: 2px 6px; border-radius: 10px; }
.badge-facturada { background: #10b981; color: #fff; font-size: 11px; padding: 2px 6px; border-radius: 10px; }

.dash-tab-content { padding-top: 16px; }
.tab-pane-inner   { min-height: 200px; }

/* ── Nuevo pedido hero ────────────────────────────────────────────────────── */
.nuevo-pedido-hero {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.btn-iniciar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #1e3a5f, #1d4ed8);
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: opacity .15s, transform .15s;
  box-shadow: 0 4px 12px rgba(29,78,216,.3);
}
.btn-iniciar:hover { opacity: .92; transform: translateY(-1px); }
.btn-iniciar i { font-size: 1.3rem; }

.btn-accion--llevar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 18px;
  border: 2px solid #64748b;
  border-radius: 10px;
  background: #fff;
  color: #64748b;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all .15s;
}
.btn-accion--llevar:hover { background: #64748b; color: #fff; }

/* ── Estados ──────────────────────────────────────────────────────────────── */
.estado-carga, .estado-vacio {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 120px;
  color: #94a3b8;
  font-size: 14px;
  text-align: center;
}
.estado-vacio i { font-size: 40px; }

/* ── Leyenda ──────────────────────────────────────────────────────────────── */
.mesas-leyenda {
  display: flex;
  gap: 16px;
  margin-bottom: 10px;
  font-size: 12px;
  color: #64748b;
}
.leyenda-item { display: flex; align-items: center; gap: 5px; }
.leyenda-dot  { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.leyenda-dot--libre   { background: #10b981; }
.leyenda-dot--ocupada { background: #ef4444; }
.leyenda-dot--cuenta  { background: #f59e0b; }

/* ── Zonas y mesas ────────────────────────────────────────────────────────── */
.zona-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .5px;
  color: #94a3b8;
  margin: 14px 0 8px;
}
.mesas-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 10px;
}
.mesa-card {
  border-radius: 12px;
  border: 2px solid #e2e8f0;
  overflow: hidden;
  text-align: center;
  cursor: pointer;
  transition: transform .15s, box-shadow .15s, border-color .15s;
  background: #fff;
}
.mesa-status-bar { height: 4px; background: #e2e8f0; }
.mesa-card--libre   .mesa-status-bar { background: #10b981; }
.mesa-card--ocupada .mesa-status-bar { background: #ef4444; }
.mesa-card--cuenta  .mesa-status-bar { background: #f59e0b; }
.mesa-card--libre:hover { border-color: #1d4ed8; transform: translateY(-2px); box-shadow: 0 4px 16px rgba(29,78,216,.15); }
.mesa-card--libre:hover .mesa-status-bar { background: #1d4ed8; }
.mesa-card--ocupada { border-color: #fca5a5; background: #fff5f5; cursor: default; }
.mesa-card--cuenta  { border-color: #fcd34d; background: #fffbeb; cursor: default; }
.mesa-icon { font-size: 22px; padding-top: 12px; margin-bottom: 4px; }
.mesa-card--libre   .mesa-icon { color: #10b981; }
.mesa-card--ocupada .mesa-icon { color: #ef4444; }
.mesa-card--cuenta  .mesa-icon { color: #d97706; }
.mesa-nombre { font-weight: 700; font-size: 13px; color: #1e3a5f; margin-bottom: 6px; padding: 0 8px; }
.mesa-info   { font-size: 11px; display: flex; flex-direction: column; gap: 2px; padding: 0 8px 10px; }
.mesa-seq    { color: #1d4ed8; font-weight: 700; font-size: 12px; }
.mesa-mesero { color: #64748b; }
.mesa-monto  { color: #1e3a5f; font-weight: 700; }
.mesa-seats  { color: #10b981; font-weight: 600; }

/* ── Comandas ─────────────────────────────────────────────────────────────── */
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
.comanda-top  { display: flex; justify-content: space-between; align-items: center; }
.comanda-mesa { font-weight: 700; font-size: 14px; color: #1e3a5f; }
.comanda-hora { font-size: 12px; color: #94a3b8; }
.comanda-mid  { display: flex; gap: 10px; flex-wrap: wrap; font-size: 12px; color: #64748b; }
.comanda-bot  { display: flex; justify-content: space-between; align-items: center; margin-top: 4px; }
.comanda-monto { font-size: 18px; font-weight: 800; color: #1e3a5f; }
.comanda-num   { font-size: 11px; color: #94a3b8; }
.comanda-notas {
  font-size: 11px; color: #64748b;
  background: #f8fafc; border-radius: 6px; padding: 4px 8px;
}

/* ── Sidebar ──────────────────────────────────────────────────────────────── */
.dash-side { display: flex; flex-direction: column; gap: 14px; }
.side-section {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,.04);
}
.side-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid #f1f5f9;
  font-weight: 600;
  font-size: 13px;
  background: #fafafa;
}
.side-loading { display: flex; align-items: center; justify-content: center; padding: 20px; }
.side-ok { display: flex; align-items: center; gap: 6px; padding: 14px; font-size: 13px; color: #374151; }
.side-empty { padding: 14px; font-size: 13px; color: #94a3b8; text-align: center; }

.stock-list { padding: 4px 0; }
.stock-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  border-bottom: 1px solid #f9fafb;
}
.stock-item:last-child { border-bottom: none; }
.stock-item-name { font-size: 13px; font-weight: 500; color: #1e293b; }
.stock-item-unit { font-size: 11px; color: #94a3b8; }
.stock-item-nums { font-size: 13px; }

.tx-wrap { overflow-x: auto; }
.tx-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.tx-table th {
  padding: 6px 10px; color: #64748b; font-weight: 600; font-size: 11px;
  text-transform: uppercase; border-bottom: 1px solid #f1f5f9; background: #fafafa;
}
.tx-table td { padding: 7px 10px; border-bottom: 1px solid #f9fafb; }
.tx-table tr:last-child td { border-bottom: none; }
.tx-hora  { color: #64748b; font-size: 11px; white-space: nowrap; }
.tx-num   { color: #374151; font-family: monospace; font-size: 11px; }
.tx-total { font-weight: 700; color: #1e293b; white-space: nowrap; }
.badge-tx { font-size: 10px; padding: 2px 6px; border-radius: 8px; font-weight: 600; }
.tx-fact  { background: #dbeafe; color: #1d4ed8; }
.tx-rec   { background: #ede9fe; color: #6d28d9; }

/* ══════════════════════════════════════════════════════════
   WIZARD MODAL
══════════════════════════════════════════════════════════ */
.wizard-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
  padding: 16px;
}
.wizard-modal {
  background: #fff;
  border-radius: 16px;
  width: 100%;
  max-width: 560px;
  max-height: 90dvh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,.25);
  overflow: hidden;
  position: relative;
}

/* Header wizard */
.wizard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  background: linear-gradient(90deg, #1e3a5f, #1d4ed8);
  color: #fff;
  flex-shrink: 0;
}
.wizard-steps { display: flex; align-items: center; gap: 10px; }
.wstep {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  font-weight: 600;
  opacity: .5;
  transition: opacity .2s;
}
.wstep.active { opacity: 1; }
.wstep.done   { opacity: .7; }
.wstep-sep {
  width: 30px;
  height: 2px;
  background: rgba(255,255,255,.3);
  border-radius: 1px;
}
.wizard-close {
  background: none;
  border: none;
  color: rgba(255,255,255,.7);
  font-size: 16px;
  cursor: pointer;
  padding: 4px 8px;
}
.wizard-close:hover { color: #fff; }

/* Body wizard */
.wizard-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.wizard-section-title {
  font-size: 15px;
  font-weight: 700;
  color: #1e3a5f;
  margin: 0;
}

/* Meseros */
.meseros-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 10px;
}
.mesero-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 14px 8px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  background: #fff;
  cursor: pointer;
  transition: all .15s;
}
.mesero-card:hover { border-color: #1d4ed8; }
.mesero-card--selected { border-color: #1d4ed8; background: #eff6ff; }
.mesero-card--add { border-style: dashed; color: #64748b; }
.mesero-card--add:hover { border-color: #10b981; color: #10b981; }

.mesero-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1e3a5f, #1d4ed8);
  color: #fff;
  font-size: 1.2rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}
.mesero-avatar--none { background: #e2e8f0; color: #94a3b8; }
.mesero-avatar--add  { background: #f0fdf4; color: #16a34a; font-size: 1.1rem; }
.mesero-card--selected .mesero-avatar { box-shadow: 0 0 0 3px #2563eb; }

.mesero-name { font-size: 11px; font-weight: 600; color: #334155; text-align: center; line-height: 1.3; }

/* Agregar mesero form */
.add-waiter-form {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 12px;
}
.aw-row { display: flex; gap: 8px; align-items: center; }
.campo-input {
  flex: 1;
  border: 1.5px solid #cbd5e1;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
  color: #1e3a5f;
  outline: none;
  min-width: 0;
}
.campo-input:focus { border-color: #1d4ed8; }
.btn-aw-save {
  width: 38px;
  height: 38px;
  border: none;
  border-radius: 8px;
  background: #10b981;
  color: #fff;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.btn-aw-save:disabled { opacity: .6; }

/* Acordeón zonas */
.zonas-acordeon { display: flex; flex-direction: column; gap: 8px; }
.zona-acordeon { border: 1.5px solid #e2e8f0; border-radius: 10px; overflow: hidden; }
.zona-acordeon__header {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f8fafc;
  border: none;
  font-weight: 600;
  font-size: 13px;
  color: #1e3a5f;
  cursor: pointer;
  text-align: left;
  transition: background .15s;
}
.zona-acordeon__header:hover { background: #f1f5f9; }
.zona-acordeon__header--open { background: #eff6ff; color: #1d4ed8; }
.zona-count {
  display: inline-block;
  background: #e2e8f0;
  border-radius: 10px;
  padding: 1px 7px;
  font-size: 11px;
  font-weight: 600;
  margin-left: 8px;
  color: #64748b;
}

.zona-acordeon__body { padding: 12px; border-top: 1px solid #e2e8f0; background: #fff; }
.mesas-grid-wizard {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
  gap: 8px;
}
.mesa-wizard-card {
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  cursor: pointer;
  text-align: center;
  padding: 0;
  transition: all .15s;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.mwc-status-bar { width: 100%; height: 4px; background: #e2e8f0; }
.mesa-wizard-card--libre .mwc-status-bar   { background: #10b981; }
.mesa-wizard-card--ocupada .mwc-status-bar { background: #ef4444; }
.mesa-wizard-card--cuenta .mwc-status-bar  { background: #f59e0b; }
.mesa-wizard-card--libre:hover { border-color: #1d4ed8; transform: translateY(-1px); box-shadow: 0 3px 10px rgba(29,78,216,.15); }
.mesa-wizard-card--libre:hover .mwc-status-bar { background: #1d4ed8; }
.mesa-wizard-card--ocupada,
.mesa-wizard-card--cuenta { border-color: #fca5a5; opacity: .65; cursor: not-allowed; }
.mesa-wizard-card--cuenta { border-color: #fcd34d; }

.mwc-icon { font-size: 20px; margin: 10px 0 4px; }
.mesa-wizard-card--libre .mwc-icon   { color: #10b981; }
.mesa-wizard-card--ocupada .mwc-icon { color: #ef4444; }
.mesa-wizard-card--cuenta .mwc-icon  { color: #d97706; }
.mwc-name  { font-size: 12px; font-weight: 700; color: #1e3a5f; padding: 0 6px; }
.mwc-info  { font-size: 10px; padding: 2px 6px 8px; }
.mwc-badge { background: #fee2e2; color: #b91c1c; border-radius: 6px; padding: 1px 5px; font-weight: 600; }
.mesa-wizard-card--cuenta .mwc-badge { background: #fef3c7; color: #92400e; }
.mwc-seats { color: #10b981; font-weight: 600; }

/* Footer wizard */
.wizard-footer {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  padding-top: 8px;
  border-top: 1px solid #f1f5f9;
  flex-shrink: 0;
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
.btn-wizard-next {
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
.btn-wizard-next:hover { opacity: .9; }

/* Debug card (paso 3 temporal) */
.debug-card {
  background: #0f172a;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 16px;
  overflow-x: auto;
}
.debug-table { width: 100%; border-collapse: collapse; font-family: monospace; }
.debug-table tr + tr td { border-top: 1px solid #1e293b; }
.debug-key {
  color: #94a3b8;
  font-size: 12px;
  padding: 6px 14px 6px 0;
  white-space: nowrap;
  vertical-align: middle;
  min-width: 140px;
}
.debug-val {
  color: #4ade80;
  font-size: 13px;
  font-weight: 700;
  padding: 6px 0;
  vertical-align: middle;
}
.debug-hint {
  color: #fbbf24;
  font-size: 11px;
  font-weight: 400;
  margin-left: 10px;
}
.debug-token { font-size: 10px; color: #60a5fa; word-break: break-all; }

/* Loading overlay */
.wizard-loading-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255,255,255,.85);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 14px;
  color: #1e3a5f;
  font-weight: 600;
  border-radius: 16px;
}

/* ── Responsive ───────────────────────────────────────────────────────────── */
@media (max-width: 1100px) {
  .dash-body { grid-template-columns: 1fr; }
  .dash-side { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
}
@media (max-width: 768px) {
  .dash-header { flex-direction: row; flex-wrap: wrap; }
  .btn-tv-label { display: none; }
  .btn-tv { padding: 6px 10px; }
  .mesas-grid    { grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); }
  .comandas-grid { grid-template-columns: 1fr; }
  .dash-tabs .nav-link { padding: 8px 10px; font-size: 12px; }
  .dash-side { grid-template-columns: 1fr; }
  .nuevo-pedido-hero { flex-wrap: wrap; }
  .meseros-grid { grid-template-columns: repeat(auto-fill, minmax(85px, 1fr)); }
}
@media (max-width: 576px) {
  .mesas-grid  { grid-template-columns: repeat(3, 1fr); }
  .mesas-leyenda { font-size: 11px; gap: 10px; }
  .dash-side { display: flex; flex-direction: column; }
  .wizard-overlay { padding: 0; align-items: flex-end; }
  .wizard-modal { border-radius: 20px 20px 0 0; max-height: 92dvh; }
}
</style>
