<template>
  <div class="cc-wrap">

    <!-- ── Panel de búsqueda ─────────────────────────────────── -->
    <div class="search-panel">

      <!-- Chips de modo -->
      <div class="mode-chips">
        <button
          v-for="m in MODOS" :key="m.id"
          class="mode-chip" :class="{ active: modoActivo === m.id }"
          @click="setModo(m.id)"
        >
          <i :class="m.icono"></i>
          <span class="chip-lbl">{{ m.label }}</span>
        </button>
      </div>

      <!-- Campo único -->
      <div class="search-input-row">
        <input
          v-model="queryActual"
          class="search-input"
          :placeholder="modoInfo.placeholder"
          @keyup.enter="buscar"
        />
        <label v-if="modoActivo === 'nombre'" class="toggle-vigentes" title="Solo vigentes">
          <input type="checkbox" v-model="soloVigentes" />
          <span>Vig.</span>
        </label>
        <button class="btn-buscar" @click="buscar" :disabled="loading || !queryActual.trim()">
          <span v-if="loading" class="spin-sm"></span>
          <span v-else><i class="bi bi-search"></i></span>
        </button>
      </div>

      <!-- Lista resultados múltiples -->
      <div v-if="listaCreditos.length > 1" class="selector-row">
        <i class="bi bi-list-ul"></i>
        <select class="sel-credito" v-model="nroSeleccionado" @change="cargarDetalle">
          <option value="">— Seleccionar crédito —</option>
          <option v-for="c in listaCreditos" :key="c.Nro_Credito" :value="c.Nro_Credito">
            {{ c.Nro_Credito }} · {{ c.cliente_nombre }} · {{ fmt(c.Valor_Actual) }} · {{ fmtFecha(c.Pago_Hasta) }}
          </option>
        </select>
      </div>

      <div v-if="errorMsg" class="alerta-error">
        <i class="bi bi-exclamation-triangle-fill"></i> {{ errorMsg }}
      </div>
    </div>

    <!-- Loading detalle -->
    <div v-if="loadingDetalle" class="estado-loading">
      <div class="spin-lg"></div> Cargando crédito...
    </div>

    <!-- ── Detalle ──────────────────────────────────────────────── -->
    <template v-if="detalle && !loadingDetalle">

      <!-- Cabecera: estado + cliente -->
      <div class="cliente-estado-row">
        <div class="cliente-card">
          <div class="cliente-nombre">{{ detalle.credito.cliente_nombre }}</div>
          <div class="cliente-datos">
            <span><i class="bi bi-person-badge"></i> {{ detalle.credito.Cliente }}</span>
            <span v-if="detalle.credito.cliente_tel"><i class="bi bi-telephone"></i> {{ detalle.credito.cliente_tel }}</span>
            <span v-if="detalle.credito.cliente_mail"><i class="bi bi-envelope"></i> {{ detalle.credito.cliente_mail }}</span>
            <span v-if="detalle.credito.cliente_dir"><i class="bi bi-geo-alt"></i> {{ detalle.credito.cliente_dir }}</span>
          </div>
        </div>
        <div class="estado-badge" :class="estadoClass">
          <i class="bi" :class="estadoIcon"></i> {{ estadoLabel }}
        </div>
      </div>

      <!-- ── Tabs ──────────────────────────────────────────────── -->
      <div class="tabs-bar">
        <button v-for="t in TABS" :key="t.id"
          class="tab-btn" :class="{ active: tabActivo === t.id }"
          @click="tabActivo = t.id">
          <i class="bi" :class="t.icono"></i>
          <span>{{ t.label }}</span>
          <span v-if="t.badge && contadorTab(t.id) > 0" class="tab-badge">{{ contadorTab(t.id) }}</span>
        </button>
      </div>

      <!-- ══ TAB: Info General ══ -->
      <div v-if="tabActivo === 'general'" class="tab-content">
        <div class="info-grid">
          <!-- Col izquierda -->
          <div class="info-col">
            <h4 class="info-section-title"><i class="bi bi-file-earmark-text"></i> Crédito</h4>
            <div class="rf-row"><span class="rf-lbl">Nro. Crédito</span><span class="rf-val rf-nro">{{ detalle.credito.Nro_Credito }}</span></div>
            <div class="rf-row"><span class="rf-lbl">Fecha Inicio</span><span class="rf-val">{{ fmtFecha(detalle.credito.Fecha) }}</span></div>
            <div class="rf-row"><span class="rf-lbl">% Interés Casa</span><span class="rf-val">{{ detalle.credito.Interes }}%</span></div>
            <div class="rf-row"><span class="rf-lbl">% Interés Socio</span><span class="rf-val">{{ detalle.credito.Interes_Socio }}%</span></div>
            <div class="rf-row"><span class="rf-lbl">Valor Inicial</span><span class="rf-val">{{ fmt(detalle.credito.Valor) }}</span></div>
            <div class="rf-row rf-highlight"><span class="rf-lbl">Valor Actual</span><span class="rf-val">{{ fmt(detalle.credito.Valor_Actual) }}</span></div>
            <div class="rf-row"><span class="rf-lbl">Día Vence</span><span class="rf-val">{{ detalle.credito.Dia_Vence }}</span></div>
            <div class="rf-row"><span class="rf-lbl">Acreedor</span><span class="rf-val">{{ detalle.credito.acreedor_nombre }}</span></div>
            <div class="rf-row"><span class="rf-lbl">Avalúo Catastral</span><span class="rf-val">{{ fmt(detalle.credito.Avaluo_Catastral) }}</span></div>
            <div class="rf-row"><span class="rf-lbl">Avalúo Comercial</span><span class="rf-val">{{ fmt(detalle.credito.Avaluo_Comercial) }}</span></div>
          </div>
          <!-- Col derecha -->
          <div class="info-col">
            <h4 class="info-section-title"><i class="bi bi-calculator-fill"></i> Estado Financiero</h4>
            <div class="rf-row"><span class="rf-lbl">Pago Hasta</span><span class="rf-val">{{ fmtFecha(detalle.credito.Pago_Hasta) }}</span></div>
            <div class="rf-row rf-mora"><span class="rf-lbl">Meses Mora</span><span class="rf-val">{{ detalle.credito.meses_mora }}</span></div>
            <div class="rf-row"><span class="rf-lbl">Cuota / Mes</span><span class="rf-val rf-cuota">{{ fmt(detalle.credito.cuota_mes) }}</span></div>
            <div class="rf-row rf-deuda"><span class="rf-lbl">Valor Deuda</span><span class="rf-val">{{ fmt(detalle.credito.valor_deuda) }}</span></div>
            <div class="rf-row"><span class="rf-lbl">Ref. Jurídica</span><span class="rf-val rf-juridica">{{ detalle.credito.Nro_Juridico || '—' }}</span></div>
            <div class="rf-row"><span class="rf-lbl">Ref. Adicional</span><span class="rf-val">{{ detalle.credito.Ref_Adicional || '—' }}</span></div>
            <div class="rf-row"><span class="rf-lbl">Ubicación Docs.</span><span class="rf-val">{{ detalle.credito.Ubicacion || '—' }}</span></div>

            <h4 class="info-section-title" style="margin-top:16px"><i class="bi bi-house"></i> Predio</h4>
            <div class="rf-row"><span class="rf-lbl">Matrícula Inm.</span><span class="rf-val">{{ detalle.credito.Matricula_Inmobiliaria || '—' }}</span></div>
            <div class="rf-row"><span class="rf-lbl">Nro. Predio</span><span class="rf-val">{{ detalle.credito.Numero_Predio || '—' }}</span></div>
            <div class="rf-row"><span class="rf-lbl">Dirección Predio</span><span class="rf-val">{{ detalle.credito.Direccion_Predio || '—' }}</span></div>
            <div class="rf-row"><span class="rf-lbl">Área Predio</span><span class="rf-val">{{ detalle.credito.Area_Predio || '—' }} m²</span></div>
          </div>
        </div>
      </div>

      <!-- ══ TAB: Pagos ══ -->
      <div v-if="tabActivo === 'pagos'" class="tab-content">
        <div v-if="!detalle.pagos.length" class="tab-empty"><i class="bi bi-inbox"></i> Sin pagos registrados</div>
        <div v-else class="table-wrap">
          <div class="table-summary">
            Total pagado: <strong>{{ fmt(totalPagado) }}</strong> · {{ detalle.pagos.length }} registros
          </div>
          <table class="det-table">
            <thead><tr>
              <th>#Pago</th><th>Fecha</th><th>Meses</th><th>Valor</th><th>Descuento</th><th>Pagado hasta</th><th>Forma pago</th><th>Empleado</th>
            </tr></thead>
            <tbody>
              <tr v-for="p in detalle.pagos" :key="p.Nro_Pago">
                <td class="td-nro">{{ p.Nro_Pago }}</td>
                <td>{{ fmtFecha(p.Fecha) }}</td>
                <td class="td-center">{{ p.Meses_Pagos }}</td>
                <td class="td-money">{{ fmt(p.Valor_pago) }}</td>
                <td class="td-money">{{ p.Descuento ? fmt(p.Descuento) : '—' }}</td>
                <td>{{ p.Mes_Pago_Hasta || '—' }}</td>
                <td>{{ p.forma_pago_desc }}</td>
                <td>{{ p.empleado_nombre }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ══ TAB: Abonos Capital ══ -->
      <div v-if="tabActivo === 'abonos'" class="tab-content">
        <div class="sub-tabs">
          <button class="sub-tab" :class="{ active: subTab === 'capital' }" @click="subTab='capital'">
            Abonos Capital ({{ detalle.abonos_capital.length }})
          </button>
          <button class="sub-tab" :class="{ active: subTab === 'parciales' }" @click="subTab='parciales'">
            Parciales ({{ detalle.abonos_parciales.length }})
          </button>
        </div>
        <!-- Abonos capital -->
        <div v-if="subTab === 'capital'">
          <div v-if="!detalle.abonos_capital.length" class="tab-empty"><i class="bi bi-inbox"></i> Sin abonos a capital</div>
          <div v-else class="table-wrap">
            <div class="table-summary">Total abonado al capital: <strong>{{ fmt(totalAbonosCapital) }}</strong></div>
            <table class="det-table">
              <thead><tr><th>#</th><th>Fecha</th><th>Valor Abono</th><th>Forma pago</th><th>Empleado</th></tr></thead>
              <tbody>
                <tr v-for="a in detalle.abonos_capital" :key="a.Nro_Abono">
                  <td class="td-nro">{{ a.Nro_Abono }}</td>
                  <td>{{ fmtFecha(a.Fecha) }}</td>
                  <td class="td-money">{{ fmt(a.Valor_Abono) }}</td>
                  <td>{{ a.forma_pago_desc }}</td>
                  <td>{{ a.empleado_nombre }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <!-- Abonos parciales -->
        <div v-if="subTab === 'parciales'">
          <div v-if="!detalle.abonos_parciales.length" class="tab-empty"><i class="bi bi-inbox"></i> Sin abonos parciales</div>
          <div v-else class="table-wrap">
            <table class="det-table">
              <thead><tr><th>#</th><th>Fecha</th><th>Valor</th><th>Pendiente</th><th>Fecha Cruce</th><th>Forma pago</th><th>Observación</th></tr></thead>
              <tbody>
                <tr v-for="a in detalle.abonos_parciales" :key="a.Nro_Abono">
                  <td class="td-nro">{{ a.Nro_Abono }}</td>
                  <td>{{ fmtFecha(a.Fecha) }}</td>
                  <td class="td-money">{{ fmt(a.Valor_Abono) }}</td>
                  <td><span :class="a.Pendiente ? 'badge-pend' : 'badge-ok'">{{ a.Pendiente ? 'Pendiente' : 'Cruzado' }}</span></td>
                  <td>{{ fmtFecha(a.Fecha_Cruce) }}</td>
                  <td>{{ a.forma_pago_desc }}</td>
                  <td class="td-obs">{{ a.Observacion || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- ══ TAB: Aumento Capital ══ -->
      <div v-if="tabActivo === 'aumentos'" class="tab-content">
        <div v-if="!detalle.aumentos_capital.length" class="tab-empty"><i class="bi bi-inbox"></i> Sin aumentos de capital</div>
        <div v-else class="table-wrap">
          <div class="table-summary">Total aumentos: <strong>{{ fmt(totalAumentos) }}</strong></div>
          <table class="det-table">
            <thead><tr><th>#</th><th>Fecha</th><th>Valor</th><th>Nro. Pagaré</th><th>Unifica En</th><th>Forma pago</th><th>Empleado</th><th>Observaciones</th></tr></thead>
            <tbody>
              <tr v-for="a in detalle.aumentos_capital" :key="a.Nro_Abono">
                <td class="td-nro">{{ a.Nro_Abono }}</td>
                <td>{{ fmtFecha(a.Fecha) }}</td>
                <td class="td-money">{{ fmt(a.Valor_Abono) }}</td>
                <td>{{ a.Nro_Pagare || '—' }}</td>
                <td class="td-money">{{ a.Unifica_En ? fmt(a.Unifica_En) : '—' }}</td>
                <td>{{ a.forma_pago_desc }}</td>
                <td>{{ a.empleado_nombre }}</td>
                <td class="td-obs">{{ a.Observaciones || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ══ TAB: Novedades ══ -->
      <div v-if="tabActivo === 'novedades'" class="tab-content">
        <div v-if="!detalle.novedades.length" class="tab-empty"><i class="bi bi-inbox"></i> Sin novedades</div>
        <div v-else class="novedades-list">
          <div v-for="n in detalle.novedades" :key="n.Nro_Novedad" class="novedad-card">
            <div class="nov-head">
              <span class="nov-fecha"><i class="bi bi-calendar3"></i> {{ fmtFecha(n.Fecha) }} {{ n.Hora ? n.Hora.substring(0,5) : '' }}</span>
              <span class="nov-user"><i class="bi bi-person"></i> {{ n.empleado_nombre }}</span>
            </div>
            <p class="nov-texto">{{ n.Observacion }}</p>
          </div>
        </div>
      </div>

      <!-- ══ TAB: Otros Deudores ══ -->
      <div v-if="tabActivo === 'deudores'" class="tab-content">
        <div v-if="!detalle.otros_deudores.length" class="tab-empty"><i class="bi bi-inbox"></i> Sin codeudores registrados</div>
        <div v-else class="table-wrap">
          <table class="det-table">
            <thead><tr><th>Cédula</th><th>Nombre</th><th>Teléfono</th><th>Email</th><th>Dirección</th></tr></thead>
            <tbody>
              <tr v-for="d in detalle.otros_deudores" :key="d.Cedula">
                <td class="td-nro">{{ d.Cedula }}</td>
                <td><span class="det-nombre">{{ d.nombres }}</span></td>
                <td>{{ d.Telefono || '—' }}</td>
                <td>{{ d.Mail || '—' }}</td>
                <td>{{ d.direccion || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ══ TAB: Escritura / Info Adicional ══ -->
      <div v-if="tabActivo === 'escritura'" class="tab-content">
        <div class="info-grid">
          <div class="info-col">
            <h4 class="info-section-title"><i class="bi bi-file-earmark-richtext"></i> Escritura Pública</h4>
            <div class="rf-row"><span class="rf-lbl">Fecha Escritura</span><span class="rf-val">{{ fmtFecha(detalle.credito.Fecha_Escritura) }}</span></div>
            <div class="rf-row"><span class="rf-lbl">Escritura</span><span class="rf-val esc-text">{{ detalle.credito.Escritura || '—' }}</span></div>
            <div class="rf-row"><span class="rf-lbl">Nro. Jurídico</span><span class="rf-val rf-juridica">{{ detalle.credito.Nro_Juridico || '—' }}</span></div>
            <div class="rf-row"><span class="rf-lbl">Obs. Jurídico</span><span class="rf-val esc-text">{{ detalle.credito.Observaciones_Juridico || '—' }}</span></div>
          </div>
          <div class="info-col">
            <h4 class="info-section-title"><i class="bi bi-map"></i> Datos Catastrales</h4>
            <div class="rf-row"><span class="rf-lbl">Matrícula Inm.</span><span class="rf-val">{{ detalle.credito.Matricula_Inmobiliaria || '—' }}</span></div>
            <div class="rf-row"><span class="rf-lbl">Número Predio</span><span class="rf-val">{{ detalle.credito.Numero_Predio || '—' }}</span></div>
            <div class="rf-row"><span class="rf-lbl">Urbano / Rural</span><span class="rf-val">{{ detalle.credito.Urbano_Rural ? 'Urbano' : 'Rural' }}</span></div>
            <div class="rf-row"><span class="rf-lbl">Dirección Predio</span><span class="rf-val">{{ detalle.credito.Direccion_Predio || '—' }}</span></div>
            <div class="rf-row"><span class="rf-lbl">Área Predio</span><span class="rf-val">{{ detalle.credito.Area_Predio || '—' }} m²</span></div>
            <div class="rf-row"><span class="rf-lbl">Año Avalúo Cat.</span><span class="rf-val">{{ detalle.credito.Ano_Avaluo_Catastral || '—' }}</span></div>
            <div class="rf-row"><span class="rf-lbl">Avalúo Catastral</span><span class="rf-val">{{ fmt(detalle.credito.Avaluo_Catastral) }}</span></div>
            <div class="rf-row"><span class="rf-lbl">Avalúo Comercial</span><span class="rf-val">{{ fmt(detalle.credito.Avaluo_Comercial) }}</span></div>
          </div>
        </div>
      </div>

    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useCompanyStore } from '@/stores/companyStore'
import api from '@/services/apis'

const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id)

// ── Búsqueda con chips ───────────────────────────────────────────────────────
const MODOS = [
  { id: 'nro',      label: 'Nro. Crédito',  icono: 'bi-file-earmark-text', placeholder: 'Ej: 1-423...' },
  { id: 'nombre',   label: 'Nombre',         icono: 'bi-person',             placeholder: 'Nombre del cliente...' },
  { id: 'ref',      label: 'Ref. Adicional', icono: 'bi-tag',                placeholder: 'Ej: P-171...' },
  { id: 'juridico', label: 'Nro. Jurídico',  icono: 'bi-building',           placeholder: 'Ej: L-145...' },
]
const modoActivo      = ref('nro')
const queryActual     = ref('')
const soloVigentes    = ref(true)
const loading         = ref(false)
const errorMsg        = ref('')
const listaCreditos   = ref([])
const nroSeleccionado = ref('')

const modoInfo = computed(() => MODOS.find(m => m.id === modoActivo.value))

function setModo(id) {
  modoActivo.value = id; queryActual.value = ''
  listaCreditos.value = []; nroSeleccionado.value = ''
  errorMsg.value = ''; detalle.value = null
}

async function buscar() {
  const q = queryActual.value.trim()
  if (!q) return
  loading.value = true; errorMsg.value = ''; listaCreditos.value = []; nroSeleccionado.value = ''
  detalle.value = null
  const params = { company_id: companyId.value }
  if      (modoActivo.value === 'nro')      params.nro      = q
  else if (modoActivo.value === 'ref')      params.ref      = q
  else if (modoActivo.value === 'juridico') params.juridico = q
  else { params.nombre = q; params.vigentes = soloVigentes.value }
  try {
    const { data } = await api.get('/api/hipotecas/creditos/buscar', { params })
    if (!data.creditos.length) { errorMsg.value = 'No se encontraron resultados.'; return }
    listaCreditos.value = data.creditos
    if (data.creditos.length === 1) {
      nroSeleccionado.value = data.creditos[0].Nro_Credito
      await cargarDetalle()
    }
  } catch { errorMsg.value = 'Error al buscar.' }
  finally { loading.value = false }
}

// ── Detalle ─────────────────────────────────────────────────────────────────
const detalle       = ref(null)
const loadingDetalle= ref(false)
const tabActivo     = ref('general')
const subTab        = ref('capital')

const TABS = [
  { id: 'general',   label: 'Info General',     icono: 'bi-file-earmark-text', badge: false },
  { id: 'pagos',     label: 'Pagos',             icono: 'bi-cash-coin',         badge: true  },
  { id: 'abonos',    label: 'Abonos',            icono: 'bi-piggy-bank',        badge: true  },
  { id: 'aumentos',  label: 'Aumento Capital',   icono: 'bi-graph-up-arrow',    badge: true  },
  { id: 'novedades', label: 'Novedades',         icono: 'bi-chat-left-text',    badge: true  },
  { id: 'deudores',  label: 'Codeudores',        icono: 'bi-people',            badge: true  },
  { id: 'escritura', label: 'Escritura',         icono: 'bi-file-earmark-richtext', badge: false },
]

function contadorTab(id) {
  if (!detalle.value) return 0
  const map = {
    pagos: detalle.value.pagos?.length,
    abonos: (detalle.value.abonos_capital?.length ?? 0) + (detalle.value.abonos_parciales?.length ?? 0),
    aumentos: detalle.value.aumentos_capital?.length,
    novedades: detalle.value.novedades?.length,
    deudores: detalle.value.otros_deudores?.length,
  }
  return map[id] ?? 0
}

async function cargarDetalle() {
  if (!nroSeleccionado.value) return
  loadingDetalle.value = true; errorMsg.value = ''; tabActivo.value = 'general'; subTab.value = 'capital'
  try {
    const { data } = await api.get(`/api/hipotecas/credito/${encodeURIComponent(nroSeleccionado.value)}`, {
      params: { company_id: companyId.value }
    })
    detalle.value = data
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || 'Error al cargar el crédito.'
    detalle.value = null
  } finally {
    loadingDetalle.value = false
  }
}

// ── Estado ──────────────────────────────────────────────────────────────────
const estadoClass = computed(() => {
  if (!detalle.value) return ''
  const c = detalle.value.credito
  if (c.Anulado)   return 'estado-anulado'
  if (c.Cancelado) return 'estado-cancelado'
  if (c.Inactivo)  return 'estado-inactivo'
  return 'estado-vigente'
})
const estadoLabel = computed(() => {
  if (!detalle.value) return ''
  const c = detalle.value.credito
  if (c.Anulado)   return 'Anulado'
  if (c.Cancelado) return 'Cancelado'
  if (c.Inactivo)  return 'Inactivo'
  return 'Vigente'
})
const estadoIcon = computed(() => {
  if (!detalle.value) return ''
  const c = detalle.value.credito
  if (c.Anulado || c.Inactivo) return 'bi-x-circle-fill'
  if (c.Cancelado) return 'bi-check-circle-fill'
  return 'bi-check-circle-fill'
})

// ── Totales ─────────────────────────────────────────────────────────────────
const totalPagado       = computed(() => detalle.value?.pagos.reduce((s, p) => s + (p.Valor_pago || 0), 0) ?? 0)
const totalAbonosCapital= computed(() => detalle.value?.abonos_capital.reduce((s, a) => s + (a.Valor_Abono || 0), 0) ?? 0)
const totalAumentos     = computed(() => detalle.value?.aumentos_capital.reduce((s, a) => s + (a.Valor_Abono || 0), 0) ?? 0)

// ── Formateo ─────────────────────────────────────────────────────────────────
function fmt(v) {
  if (v == null || v === '' || v === 0) return '$ 0'
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v)
}
function fmtFecha(v) {
  if (!v) return '—'
  const d = new Date(v + 'T00:00:00')
  return new Intl.DateTimeFormat('es-CO', { day: '2-digit', month: 'short', year: 'numeric' }).format(d)
}
</script>

<style scoped>
.cc-wrap { padding: 0 20px 48px; max-width: 1200px; margin: 0 auto; }

/* ── Search panel ── */
.search-panel { background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 14px 16px; margin-bottom: 16px; display: flex; flex-direction: column; gap: 10px; }
.mode-chips { display: flex; gap: 6px; flex-wrap: wrap; }
.mode-chip { display: flex; align-items: center; gap: 5px; background: #f1f5f9; border: 1.5px solid #e2e8f0; border-radius: 20px; padding: 5px 12px; font-size: 12px; font-weight: 600; color: #64748b; cursor: pointer; transition: all 0.15s; white-space: nowrap; }
.mode-chip:hover { background: #e2e8f0; }
.mode-chip.active { background: #0f2448; color: #fff; border-color: #0f2448; }
.mode-chip .bi { font-size: 12px; }
.search-input-row { display: flex; gap: 8px; align-items: center; }
.search-input { flex: 1; border: 1.5px solid #e2e8f0; border-radius: 8px; padding: 9px 12px; font-size: 14px; outline: none; transition: border-color 0.2s; }
.search-input:focus { border-color: #0f2448; }
.btn-buscar { background: #0f2448; color: #fff; border: none; border-radius: 8px; padding: 9px 16px; cursor: pointer; font-size: 14px; transition: background 0.2s; flex-shrink: 0; }
.btn-buscar:hover:not(:disabled) { background: #1e3a6e; }
.btn-buscar:disabled { opacity: 0.5; cursor: not-allowed; }
.toggle-vigentes { display: flex; align-items: center; gap: 4px; font-size: 12px; font-weight: 700; color: #065f46; background: #d1fae5; border-radius: 8px; padding: 7px 10px; cursor: pointer; white-space: nowrap; flex-shrink: 0; }
.toggle-vigentes input { accent-color: #065f46; }
.selector-row { display: flex; align-items: center; gap: 8px; border-top: 1px solid #f1f5f9; padding-top: 10px; }
.selector-row .bi { color: #64748b; }
.sel-credito { flex: 1; border: 1.5px solid #e2e8f0; border-radius: 8px; padding: 8px 12px; font-size: 13px; outline: none; }
.alerta-error { background: #fee2e2; color: #991b1b; border-radius: 8px; padding: 10px 14px; font-size: 13px; display: flex; align-items: center; gap: 8px; }

/* ── Loading ── */
.estado-loading { display: flex; align-items: center; gap: 12px; justify-content: center; padding: 40px; color: #64748b; font-size: 14px; }
.spin-sm { width: 16px; height: 16px; border: 2px solid #e2e8f0; border-top-color: #0f2448; border-radius: 50%; animation: spin 0.8s linear infinite; display: inline-block; }
.spin-lg { width: 28px; height: 28px; border: 3px solid #e2e8f0; border-top-color: #0f2448; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Cliente + estado ── */
.cliente-estado-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.cliente-card { flex: 1; }
.cliente-nombre { font-size: 20px; font-weight: 800; color: #0f2448; margin-bottom: 6px; }
.cliente-datos { display: flex; flex-wrap: wrap; gap: 10px; font-size: 13px; color: #64748b; }
.cliente-datos span { display: flex; align-items: center; gap: 5px; }
.estado-badge { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 700; border-radius: 20px; padding: 6px 16px; white-space: nowrap; }
.estado-vigente   { background: #d1fae5; color: #065f46; }
.estado-cancelado { background: #dbeafe; color: #1d4ed8; }
.estado-anulado, .estado-inactivo { background: #fee2e2; color: #991b1b; }

/* ── Tabs ── */
.tabs-bar { display: flex; gap: 4px; overflow-x: auto; margin-bottom: 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 0; scrollbar-width: none; }
.tabs-bar::-webkit-scrollbar { display: none; }
.tab-btn { display: flex; align-items: center; gap: 6px; padding: 10px 14px; border: none; background: none; cursor: pointer; font-size: 13px; font-weight: 600; color: #64748b; white-space: nowrap; border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all 0.15s; }
.tab-btn:hover { color: #0f2448; }
.tab-btn.active { color: #0f2448; border-bottom-color: #0f2448; }
.tab-badge { background: #ef4444; color: #fff; font-size: 10px; font-weight: 700; border-radius: 10px; padding: 1px 6px; }

/* ── Tab content ── */
.tab-content { background: #fff; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 12px 12px; padding: 20px; }
.tab-empty { display: flex; align-items: center; gap: 10px; color: #94a3b8; font-size: 14px; padding: 30px; justify-content: center; }
.tab-empty .bi { font-size: 22px; }

/* ── Info grid ── */
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.info-col { display: flex; flex-direction: column; gap: 0; }
.info-section-title { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px; color: #64748b; margin: 0 0 10px; display: flex; align-items: center; gap: 6px; }
.info-section-title .bi { color: #10b981; }
.rf-row { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; padding: 7px 0; border-bottom: 1px solid #f1f5f9; }
.rf-lbl { font-size: 12.5px; color: #64748b; flex-shrink: 0; }
.rf-val { font-size: 13px; font-weight: 600; color: #0f172a; text-align: right; }
.rf-nro     { color: #0f2448; font-size: 15px; }
.rf-cuota   { color: #065f46; font-size: 15px; }
.rf-juridica{ color: #dc2626; }
.rf-mora    { background: #fff7ed; margin: 0 -4px; padding: 7px 4px; border-radius: 4px; }
.rf-mora .rf-val { color: #ea580c; font-size: 16px; }
.rf-deuda   { background: #fef2f2; margin: 0 -4px; padding: 7px 4px; border-radius: 4px; }
.rf-deuda .rf-val { color: #dc2626; font-size: 16px; }
.rf-highlight { background: #ecfdf5; margin: 0 -4px; padding: 7px 4px; border-radius: 4px; }
.rf-highlight .rf-val { color: #065f46; font-size: 15px; }
.esc-text { font-size: 12px; font-weight: 400; max-width: 280px; text-align: right; word-break: break-word; }

/* ── Tables ── */
.table-wrap { overflow-x: auto; }
.table-summary { font-size: 12.5px; color: #64748b; margin-bottom: 10px; padding: 8px 12px; background: #f8fafc; border-radius: 8px; }
.det-table { width: 100%; border-collapse: collapse; font-size: 12.5px; min-width: 520px; }
.det-table th { background: #0f2448; color: #fff; padding: 9px 12px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.4px; white-space: nowrap; text-align: left; }
.det-table td { padding: 9px 12px; border-bottom: 1px solid #f1f5f9; color: #334155; vertical-align: top; }
.det-table tbody tr:hover { background: #f8fafc; }
.td-nro   { font-weight: 700; color: #0f2448; }
.td-money { font-weight: 600; color: #065f46; }
.td-center{ text-align: center; }
.td-obs   { font-size: 11.5px; color: #64748b; max-width: 200px; }
.det-nombre { font-weight: 600; display: block; }
.badge-pend { background: #fef3c7; color: #92400e; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 10px; }
.badge-ok   { background: #d1fae5; color: #065f46; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 10px; }

/* ── Sub tabs ── */
.sub-tabs { display: flex; gap: 6px; margin-bottom: 16px; }
.sub-tab { padding: 6px 14px; border: 1.5px solid #e2e8f0; border-radius: 20px; background: #fff; color: #64748b; font-size: 12.5px; font-weight: 600; cursor: pointer; }
.sub-tab.active { background: #0f2448; color: #fff; border-color: #0f2448; }

/* ── Novedades ── */
.novedades-list { display: flex; flex-direction: column; gap: 10px; }
.novedad-card { background: #f8fafc; border-radius: 10px; border-left: 3px solid #0f2448; padding: 12px 16px; }
.nov-head { display: flex; align-items: center; gap: 12px; margin-bottom: 6px; flex-wrap: wrap; }
.nov-fecha { font-size: 12px; color: #0f2448; font-weight: 700; display: flex; align-items: center; gap: 4px; }
.nov-user  { font-size: 12px; color: #64748b; display: flex; align-items: center; gap: 4px; }
.nov-texto { font-size: 13px; color: #334155; margin: 0; line-height: 1.5; }

/* ── Responsive ── */
@media (max-width: 768px) {
  .cc-wrap { padding: 0 12px 40px; }
  .mode-chips { gap: 4px; }
  .chip-lbl { display: none; }
  .mode-chip { padding: 6px 10px; }
  .info-grid { grid-template-columns: 1fr; gap: 0; }
  .cliente-nombre { font-size: 17px; }
  .tab-btn span:first-of-type { display: none; }
}

@media (max-width: 576px) {
  .cc-wrap { padding: 0 8px 32px; }
  .tab-btn { padding: 10px 10px; font-size: 12px; gap: 4px; }
  .tab-content { padding: 14px 10px; }
  .cliente-estado-row { flex-direction: column; }
}
</style>
