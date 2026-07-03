<template>
  <div class="ca-wrap">

    <!-- ── Panel de búsqueda ─────────────────────────────────── -->
    <div class="search-panel">

      <div class="search-row">
        <!-- Por Código Lista -->
        <div class="search-box">
          <label class="search-lbl"><i class="bi bi-tag"></i> Código Lista</label>
          <div class="search-input-wrap">
            <input v-model="queryCodigo" class="search-input" placeholder="Ej: A-001"
              @keyup.enter="buscarPorCodigo" />
            <button class="btn-buscar" @click="buscarPorCodigo" :disabled="loadingCodigo || !queryCodigo.trim()">
              <span v-if="loadingCodigo" class="spin-sm"></span>
              <span v-else><i class="bi bi-search"></i></span>
            </button>
          </div>
        </div>

        <div class="search-sep"><span>ó</span></div>

        <!-- Por Id Arriendo -->
        <div class="search-box">
          <label class="search-lbl"><i class="bi bi-hash"></i> Id Arriendo</label>
          <div class="search-input-wrap">
            <input v-model="queryId" class="search-input" placeholder="Ej: 42"
              @keyup.enter="buscarPorId" />
            <button class="btn-buscar" @click="buscarPorId" :disabled="loadingId || !queryId.trim()">
              <span v-if="loadingId" class="spin-sm"></span>
              <span v-else><i class="bi bi-search"></i></span>
            </button>
          </div>
        </div>
      </div>

      <!-- Fila 2: Propietario / Cliente -->
      <div class="search-row search-row-2">
        <div class="search-box">
          <label class="search-lbl"><i class="bi bi-house-door"></i> Nombre Propietario</label>
          <div class="search-input-wrap">
            <input v-model="queryPropietario" class="search-input" placeholder="Buscar por propietario..."
              @keyup.enter="buscarPorPropietario" />
            <button class="btn-buscar" @click="buscarPorPropietario" :disabled="loadingProp || !queryPropietario.trim()">
              <span v-if="loadingProp" class="spin-sm"></span>
              <span v-else><i class="bi bi-search"></i></span>
            </button>
          </div>
        </div>

        <div class="search-sep"><span>ó</span></div>

        <div class="search-box">
          <label class="search-lbl"><i class="bi bi-person"></i> Cliente Arrendatario</label>
          <div class="search-input-wrap">
            <input v-model="queryCliente" class="search-input" placeholder="Buscar por nombre..."
              @keyup.enter="buscarPorCliente" />
            <label class="toggle-activos" title="Solo activos">
              <input type="checkbox" v-model="soloActivos" />
              <span>Act.</span>
            </label>
            <button class="btn-buscar" @click="buscarPorCliente" :disabled="loadingCliente || !queryCliente.trim()">
              <span v-if="loadingCliente" class="spin-sm"></span>
              <span v-else><i class="bi bi-search"></i></span>
            </button>
          </div>
        </div>
      </div>

      <!-- Selector de resultados -->
      <div v-if="listaArriendos.length > 1" class="selector-row">
        <i class="bi bi-list-ul"></i>
        <select class="sel-arriendo" v-model="idSeleccionado" @change="cargarDetalle">
          <option value="">— Seleccionar arriendo —</option>
          <option v-for="a in listaArriendos" :key="a.Id_Arriendo" :value="a.Id_Arriendo">
            #{{ a.Id_Arriendo }} · {{ a.cliente_nombre }} · {{ a.propiedad_nombre }} · {{ fmt(a.canon) }}
          </option>
        </select>
      </div>

      <div v-if="errorMsg" class="alerta-error">
        <i class="bi bi-exclamation-triangle-fill"></i> {{ errorMsg }}
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loadingDetalle" class="estado-loading">
      <div class="spin-lg"></div> Cargando arriendo...
    </div>

    <!-- ── Detalle ─────────────────────────────────────────────── -->
    <div v-if="detalle && !loadingDetalle" class="detalle-wrap">

      <!-- Header crédito -->
      <div class="det-header">
        <div class="det-header-left">
          <span class="det-nro"># {{ detalle.arriendo.Id_Arriendo }}</span>
          <span class="det-badge" :class="estadoClass">{{ estadoLabel }}</span>
        </div>
        <div class="det-header-info">
          <span class="det-cliente"><i class="bi bi-person-fill"></i> {{ detalle.arriendo.cliente_nombre }}</span>
          <span class="det-canon"><i class="bi bi-house-fill"></i> {{ detalle.arriendo.propiedad_nombre }}</span>
        </div>
        <span class="det-valor">{{ fmt(detalle.arriendo.canon) }}<small>/mes</small></span>
      </div>

      <!-- Alerta mora -->
      <div v-if="detalle.arriendo.meses_mora > 0 && detalle.arriendo.Activo == 1" class="alerta-mora">
        <i class="bi bi-exclamation-triangle-fill"></i>
        {{ detalle.arriendo.meses_mora }} mes{{ detalle.arriendo.meses_mora > 1 ? 'es' : '' }} de mora
        · Última fecha pagada: {{ fmtFecha(detalle.arriendo.Pago_Hasta) }}
      </div>

      <!-- Tabs -->
      <div class="tabs-nav">
        <button
          v-for="tab in TABS" :key="tab.id"
          class="tab-btn" :class="{ active: tabActivo === tab.id }"
          @click="tabActivo = tab.id"
        >
          <i :class="tab.icono"></i>
          <span class="tab-lbl">{{ tab.label }}</span>
          <span v-if="tab.badge && badgeCount(tab.id)" class="tab-badge">{{ badgeCount(tab.id) }}</span>
        </button>
      </div>

      <!-- ── TAB: Info General ── -->
      <div v-if="tabActivo === 'general'" class="tab-content">
        <div class="info-grid">
          <div class="info-card">
            <span class="ic-label">Código Lista</span>
            <span class="ic-value">{{ detalle.arriendo.codigo_lista || '—' }}</span>
          </div>
          <div class="info-card">
            <span class="ic-label">Dirección Propiedad</span>
            <span class="ic-value">{{ detalle.arriendo.propiedad_dir || '—' }}</span>
          </div>
          <div class="info-card">
            <span class="ic-label">Propietario</span>
            <span class="ic-value">{{ detalle.arriendo.NombrePropietario || '—' }}</span>
          </div>
          <div class="info-card">
            <span class="ic-label">Sector</span>
            <span class="ic-value">{{ detalle.arriendo.sector || '—' }}</span>
          </div>
          <div class="info-card">
            <span class="ic-label">Cédula Cliente</span>
            <span class="ic-value">{{ detalle.arriendo.cedula_cliente }}</span>
          </div>
          <div class="info-card">
            <span class="ic-label">Teléfono</span>
            <span class="ic-value">{{ detalle.arriendo.cliente_tel || '—' }}</span>
          </div>
          <div class="info-card">
            <span class="ic-label">Asesor</span>
            <span class="ic-value">{{ detalle.arriendo.asesor_nombre || '—' }}</span>
          </div>
          <div class="info-card">
            <span class="ic-label">Canon Mensual</span>
            <span class="ic-value ic-money">{{ fmt(detalle.arriendo.canon) }}</span>
          </div>
          <div class="info-card">
            <span class="ic-label">Depósito</span>
            <span class="ic-value">{{ fmt(detalle.arriendo.Deposito) }}</span>
          </div>
          <div class="info-card">
            <span class="ic-label">Fecha Inicio</span>
            <span class="ic-value">{{ fmtFecha(detalle.arriendo.Fecha_Inicio) }}</span>
          </div>
          <div class="info-card">
            <span class="ic-label">Plazo</span>
            <span class="ic-value">{{ detalle.arriendo.Plazo_Meses }} meses</span>
          </div>
          <div class="info-card">
            <span class="ic-label">Vence Contrato</span>
            <span class="ic-value">{{ fmtFecha(detalle.arriendo.Vence) }}</span>
          </div>
          <div class="info-card">
            <span class="ic-label">Fecha Avisar</span>
            <span class="ic-value">{{ fmtFecha(detalle.arriendo.Avisar) }}</span>
          </div>
          <div class="info-card">
            <span class="ic-label">Pagado Hasta</span>
            <span class="ic-value" :class="detalle.arriendo.meses_mora > 0 ? 'ic-red' : 'ic-green'">
              {{ fmtFecha(detalle.arriendo.Pago_Hasta) }}
            </span>
          </div>
          <div class="info-card">
            <span class="ic-label">Meses de Mora</span>
            <span class="ic-value" :class="detalle.arriendo.meses_mora > 0 ? 'ic-red' : ''">
              {{ detalle.arriendo.meses_mora > 0 ? detalle.arriendo.meses_mora + ' mes(es)' : 'Al día' }}
            </span>
          </div>
          <div class="info-card">
            <span class="ic-label">Valor estimado mora</span>
            <span class="ic-value ic-red">{{ detalle.arriendo.meses_mora > 0 ? fmt(detalle.arriendo.canon * detalle.arriendo.meses_mora) : '—' }}</span>
          </div>
        </div>
      </div>

      <!-- ── TAB: Pagos ── -->
      <div v-if="tabActivo === 'pagos'" class="tab-content">
        <div v-if="!detalle.pagos.length" class="tab-empty">
          <i class="bi bi-inbox"></i> Sin pagos registrados
        </div>
        <div v-else>
          <div class="total-bar">
            <span>Total pagado:</span>
            <strong>{{ fmt(totalPagado) }}</strong>
          </div>
          <div class="table-wrap">
            <table class="det-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Fecha</th>
                  <th>Valor</th>
                  <th>Meses</th>
                  <th>Forma Pago</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(p, i) in detalle.pagos" :key="p.Nro_Pago">
                  <td>{{ i + 1 }}</td>
                  <td>{{ fmtFecha(p.Fecha_Pago) }}</td>
                  <td class="det-money">{{ fmt(p.Valor_Pago) }}</td>
                  <td>{{ p.Meses_Pagados }}</td>
                  <td>{{ p.forma_pago_desc || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

    </div><!-- /detalle-wrap -->

    <!-- Estado vacío inicial -->
    <div v-if="!detalle && !loadingDetalle && !listaArriendos.length && !errorMsg" class="estado-vacio">
      <i class="bi bi-house-door" style="font-size:48px;color:#cbd5e1;"></i>
      <p>Busca un arriendo por código, id, propietario o cliente</p>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useCompanyStore } from '@/stores/companyStore'
import api from '@/services/apis'

const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id)

// ── Búsqueda ────────────────────────────────────────────────────────────────
const queryCodigo     = ref('')
const queryId         = ref('')
const queryPropietario= ref('')
const queryCliente    = ref('')
const soloActivos     = ref(true)
const loadingCodigo   = ref(false)
const loadingId       = ref(false)
const loadingProp     = ref(false)
const loadingCliente  = ref(false)
const errorMsg        = ref('')
const listaArriendos  = ref([])
const idSeleccionado  = ref('')

async function _buscar(params, loadingRef) {
  loadingRef.value = true
  errorMsg.value = ''; listaArriendos.value = []; idSeleccionado.value = ''
  detalle.value = null
  try {
    const { data } = await api.get('/api/hipotecas/arriendos/buscar', {
      params: { company_id: companyId.value, solo_activos: soloActivos.value, ...params }
    })
    if (!data.arriendos.length) { errorMsg.value = 'No se encontraron arriendos.'; return }
    listaArriendos.value = data.arriendos
    if (data.arriendos.length === 1) {
      idSeleccionado.value = data.arriendos[0].Id_Arriendo
      await cargarDetalle()
    }
  } catch { errorMsg.value = 'Error al buscar.' }
  finally { loadingRef.value = false }
}

function buscarPorCodigo()     { if (queryCodigo.value.trim())      _buscar({ codigo: queryCodigo.value.trim() },      loadingCodigo) }
function buscarPorId()         { if (queryId.value.trim())           _buscar({ id_arr: queryId.value.trim() },          loadingId) }
function buscarPorPropietario(){ if (queryPropietario.value.trim())  _buscar({ propietario: queryPropietario.value.trim() }, loadingProp) }
function buscarPorCliente()    { if (queryCliente.value.trim())      _buscar({ cliente: queryCliente.value.trim() },    loadingCliente) }

// ── Detalle ─────────────────────────────────────────────────────────────────
const detalle        = ref(null)
const loadingDetalle = ref(false)
const tabActivo      = ref('general')

const TABS = [
  { id: 'general', label: 'Info General', icono: 'bi-file-earmark-text', badge: false },
  { id: 'pagos',   label: 'Pagos',        icono: 'bi-cash-coin',         badge: true  },
]

async function cargarDetalle() {
  if (!idSeleccionado.value) return
  loadingDetalle.value = true; detalle.value = null; tabActivo.value = 'general'
  try {
    const { data } = await api.get(`/api/hipotecas/arriendo/${idSeleccionado.value}`, {
      params: { company_id: companyId.value }
    })
    detalle.value = data
  } catch { errorMsg.value = 'Error al cargar detalle del arriendo.' }
  finally { loadingDetalle.value = false }
}

// ── Computed ─────────────────────────────────────────────────────────────────
const estadoClass = computed(() => {
  if (!detalle.value) return ''
  const a = detalle.value.arriendo
  if (!a.Activo) return 'estado-inactivo'
  if (a.meses_mora > 0) return 'estado-mora'
  return 'estado-activo'
})

const estadoLabel = computed(() => {
  if (!detalle.value) return ''
  const a = detalle.value.arriendo
  if (!a.Activo) return 'Inactivo'
  if (a.meses_mora > 0) return 'En mora'
  return 'Al día'
})

const totalPagado = computed(() =>
  detalle.value?.pagos?.reduce((s, p) => s + (Number(p.Valor_Pago) || 0), 0) || 0
)

function badgeCount(tabId) {
  if (!detalle.value) return 0
  if (tabId === 'pagos') return detalle.value.pagos?.length || 0
  return 0
}

// ── Formateo ─────────────────────────────────────────────────────────────────
const fmt = (v) => {
  if (v == null || v === '') return '—'
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v)
}

const fmtFecha = (d) => {
  if (!d) return '—'
  try {
    return new Date(d + 'T12:00:00').toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
  } catch { return d }
}
</script>

<style scoped>
.ca-wrap { padding: 0 0 40px; }

/* ── Panel búsqueda ── */
.search-panel {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 14px;
  padding: 18px 20px; margin-bottom: 20px; display: flex; flex-direction: column; gap: 14px;
}
.search-row { display: flex; align-items: flex-end; gap: 16px; flex-wrap: wrap; }
.search-row-2 { border-top: 1px dashed #e2e8f0; padding-top: 14px; }
.search-box { flex: 1; min-width: 200px; display: flex; flex-direction: column; gap: 6px; }
.search-lbl { font-size: 12px; font-weight: 600; color: #64748b; display: flex; align-items: center; gap: 5px; }
.search-input-wrap { display: flex; gap: 6px; }
.search-input {
  flex: 1; border: 1.5px solid #e2e8f0; border-radius: 8px;
  padding: 8px 12px; font-size: 14px; outline: none; transition: border-color 0.2s;
}
.search-input:focus { border-color: #0f2448; }
.search-sep { display: flex; align-items: center; padding-bottom: 2px; }
.search-sep span {
  font-size: 11px; font-weight: 700; color: #94a3b8; background: #f8fafc;
  border: 1px solid #e2e8f0; border-radius: 20px; padding: 2px 8px;
}
.toggle-activos {
  display: flex; align-items: center; gap: 4px; font-size: 12px; font-weight: 700;
  color: #065f46; background: #d1fae5; border-radius: 8px; padding: 6px 10px;
  cursor: pointer; white-space: nowrap;
}
.toggle-activos input { accent-color: #065f46; }
.btn-buscar {
  background: #0f2448; color: #fff; border: none; border-radius: 8px;
  padding: 8px 14px; cursor: pointer; font-size: 14px; transition: background 0.2s;
}
.btn-buscar:hover:not(:disabled) { background: #1e3a6e; }
.btn-buscar:disabled { opacity: 0.5; cursor: not-allowed; }
.selector-row {
  display: flex; align-items: center; gap: 8px;
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 14px;
}
.sel-arriendo {
  flex: 1; border: 1.5px solid #e2e8f0; border-radius: 8px;
  padding: 7px 10px; font-size: 13px; outline: none; background: #fff;
}
.alerta-error {
  background: #fef2f2; border: 1px solid #fecaca; border-radius: 10px;
  padding: 10px 14px; font-size: 13px; color: #dc2626; display: flex; align-items: center; gap: 7px;
}

/* ── Estado ── */
.estado-loading {
  display: flex; align-items: center; justify-content: center;
  gap: 12px; padding: 60px 20px; color: #64748b; font-size: 14px;
}
.estado-vacio {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 60px 20px; gap: 12px; color: #94a3b8; text-align: center;
}
.estado-vacio p { font-size: 14px; margin: 0; }

/* ── Header detalle ── */
.det-header {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
  padding: 14px 18px; margin-bottom: 12px; display: flex; align-items: center;
  gap: 14px; flex-wrap: wrap;
}
.det-header-left { display: flex; align-items: center; gap: 8px; }
.det-nro { font-size: 18px; font-weight: 800; color: #0f2448; }
.det-badge {
  font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 20px;
  text-transform: uppercase; letter-spacing: 0.4px;
}
.estado-activo  { background: #d1fae5; color: #065f46; }
.estado-mora    { background: #fee2e2; color: #dc2626; }
.estado-inactivo{ background: #f1f5f9; color: #64748b; }
.det-header-info { flex: 1; display: flex; flex-direction: column; gap: 3px; }
.det-cliente { font-size: 14px; font-weight: 600; color: #0f2448; display: flex; align-items: center; gap: 5px; }
.det-canon   { font-size: 12px; color: #64748b; display: flex; align-items: center; gap: 5px; }
.det-valor { font-size: 20px; font-weight: 800; color: #10b981; margin-left: auto; }
.det-valor small { font-size: 12px; font-weight: 400; color: #64748b; }

/* ── Alerta mora ── */
.alerta-mora {
  background: #fff7ed; border: 1px solid #fed7aa; border-radius: 10px;
  padding: 10px 14px; margin-bottom: 12px; font-size: 13px; color: #c2410c;
  display: flex; align-items: center; gap: 8px; font-weight: 600;
}

/* ── Tabs ── */
.tabs-nav {
  display: flex; gap: 4px; flex-wrap: wrap;
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px;
  padding: 6px; margin-bottom: 16px;
}
.tab-btn {
  display: flex; align-items: center; gap: 6px;
  background: transparent; border: none; border-radius: 8px;
  padding: 8px 14px; font-size: 13px; font-weight: 600; color: #64748b;
  cursor: pointer; transition: all 0.15s; white-space: nowrap;
}
.tab-btn.active { background: #fff; color: #0f2448; box-shadow: 0 1px 4px rgba(0,0,0,0.10); }
.tab-btn:hover:not(.active) { background: #fff; color: #0f2448; }
.tab-badge {
  background: #ef4444; color: #fff; border-radius: 12px;
  font-size: 10px; font-weight: 700; padding: 1px 6px; min-width: 18px; text-align: center;
}
.tab-content { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; }
.tab-empty {
  display: flex; align-items: center; justify-content: center;
  gap: 10px; padding: 40px; color: #94a3b8; font-size: 14px;
}

/* ── Info grid ── */
.info-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.info-card {
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 10px 14px; display: flex; flex-direction: column; gap: 3px;
}
.ic-label { font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.4px; }
.ic-value { font-size: 14px; font-weight: 600; color: #0f2448; }
.ic-money { color: #065f46; font-weight: 700; }
.ic-green { color: #059669; }
.ic-red   { color: #dc2626; }

/* ── Tabla pagos ── */
.total-bar {
  display: flex; align-items: center; justify-content: flex-end; gap: 8px;
  padding: 8px 14px; background: #f0fdf4; border: 1px solid #bbf7d0;
  border-radius: 8px; margin-bottom: 12px; font-size: 13px; color: #065f46;
}
.total-bar strong { font-size: 16px; font-weight: 800; }
.table-wrap { overflow-x: auto; }
.det-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.det-table th {
  background: #f8fafc; color: #64748b; font-size: 11px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.4px; padding: 9px 10px;
  text-align: left; border-bottom: 2px solid #e2e8f0; white-space: nowrap;
}
.det-table td { padding: 9px 10px; border-bottom: 1px solid #f1f5f9; color: #0f2448; }
.det-table tr:hover td { background: #f8fafc; }
.det-money { font-weight: 700; color: #065f46; }

/* ── Spinners ── */
.spin-sm { display: inline-block; width: 14px; height: 14px; border: 2px solid #fff; border-top-color: transparent; border-radius: 50%; animation: spin 0.7s linear infinite; }
.spin-lg { width: 28px; height: 28px; border: 3px solid #e2e8f0; border-top-color: #0f2448; border-radius: 50%; animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Responsive ── */
@media (max-width: 768px) {
  .search-row { flex-direction: column; gap: 12px; }
  .search-sep { display: none; }
  .info-grid { grid-template-columns: repeat(2, 1fr); }
  .det-header { flex-direction: column; align-items: flex-start; gap: 8px; }
  .det-valor { margin-left: 0; }
  .tab-lbl { display: none; }
  .tab-btn { padding: 8px 12px; }
}

@media (max-width: 576px) {
  .search-panel { padding: 14px; }
  .info-grid { grid-template-columns: 1fr; }
  .tabs-nav { gap: 2px; padding: 4px; }
}
</style>
