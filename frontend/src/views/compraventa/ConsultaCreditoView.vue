<template>
  <div class="cc-wrap">

    <!-- ── Panel de búsqueda ─────────────────────────────────── -->
    <div class="search-panel">
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
      <div class="search-input-row">
        <input v-model="queryActual" class="search-input" :placeholder="modoInfo.placeholder" @keyup.enter="buscar" />
        <label v-if="modoActivo === 'nombre'" class="toggle-vigentes" title="Solo vigentes">
          <input type="checkbox" v-model="soloVigentes" /><span>Vig.</span>
        </label>
        <button class="btn-buscar" @click="buscar" :disabled="loading || !queryActual.trim()">
          <span v-if="loading" class="spin-sm"></span>
          <span v-else><i class="bi bi-search"></i></span>
        </button>
      </div>
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

    <!-- ── Banners parpadeantes (misma línea) ── -->
    <div v-if="detalle && (detalle.credito.Nota_Tipo_Pago || totalAbonosPendientes > 0)" class="banners-row">
      <div v-if="detalle.credito.Nota_Tipo_Pago" class="obs-banner obs-nota">
        <i class="bi bi-exclamation-triangle-fill"></i>
        <span>{{ detalle.credito.Nota_Tipo_Pago }}</span>
      </div>
      <div v-if="totalAbonosPendientes > 0" class="obs-banner obs-pendientes">
        <i class="bi bi-clock-fill"></i>
        <span>Abonos pendientes por <strong>{{ fmt(totalAbonosPendientes) }}</strong></span>
      </div>
    </div>

    <!-- Loading detalle -->
    <div v-if="loadingDetalle" class="estado-loading">
      <div class="spin-lg"></div> Cargando crédito...
    </div>

    <!-- ── Detalle ──────────────────────────────────────────────── -->
    <template v-if="detalle && !loadingDetalle">

      <!-- Cabecera: cliente + estado + botones impresión -->
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
        <div class="header-right">
          <div class="estado-badge" :class="estadoClass">
            <i class="bi" :class="estadoIcon"></i> {{ estadoLabel }}
          </div>
          <div class="action-btns">
            <button class="btn-action btn-fotos" @click="abrirCargaFotos" title="Cargar fotos de la propiedad">
              <i class="bi bi-camera-fill"></i><span class="action-lbl"> Fotos</span>
            </button>
            <button class="btn-action btn-docs" @click="abrirCargaDocs" title="Cargar documentos del crédito">
              <i class="bi bi-file-earmark-arrow-up-fill"></i><span class="action-lbl"> Documentos</span>
            </button>
          </div>
          <div class="print-btns">
            <button class="btn-print" @click="imprimirResumen" title="Estado Cuenta Resumen">
              <i class="bi bi-printer"></i><span class="print-lbl"> Resumen</span>
            </button>
            <button class="btn-print btn-print-det" @click="imprimirDetalle" title="Estado Cuenta Con Detalle Pagos">
              <i class="bi bi-file-earmark-text"></i><span class="print-lbl"> Detalle Pagos</span>
            </button>
          </div>
        </div>
      </div>

      <!-- ── Tabs ── -->
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

      <!-- ══ TAB: Info Cliente ══ -->
      <div v-if="tabActivo === 'cliente'" class="tab-content">
        <div v-if="!clienteEntradas.length" class="tab-empty"><i class="bi bi-person-x"></i> Sin datos del cliente</div>
        <div v-else class="info-grid">
          <div class="info-col">
            <h4 class="info-section-title"><i class="bi bi-person-vcard"></i> Datos del Cliente</h4>
            <template v-for="(e, i) in clienteEntradas.slice(0, Math.ceil(clienteEntradas.length / 2))" :key="e.key">
              <div class="rf-row">
                <span class="rf-lbl">{{ e.label }}</span>
                <span class="rf-val" :class="{ 'rf-nro': e.key === 'cedula' }">{{ e.display }}</span>
              </div>
            </template>
          </div>
          <div class="info-col">
            <h4 class="info-section-title"><i class="bi bi-card-list"></i> &nbsp;</h4>
            <template v-for="e in clienteEntradas.slice(Math.ceil(clienteEntradas.length / 2))" :key="e.key">
              <div class="rf-row">
                <span class="rf-lbl">{{ e.label }}</span>
                <span class="rf-val">{{ e.display }}</span>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- ══ TAB: Pagos ══ -->
      <div v-if="tabActivo === 'pagos'" class="tab-content">
        <div v-if="!detalle.pagos.length" class="tab-empty"><i class="bi bi-inbox"></i> Sin pagos registrados</div>
        <div v-else>
          <div class="pagos-toolbar">
            <div class="year-filter">
              <i class="bi bi-calendar3"></i>
              <select class="sel-anio" v-model="anioSeleccionado">
                <option value="">Todos los años</option>
                <option v-for="a in aniosPagos" :key="a" :value="a">{{ a }}</option>
              </select>
            </div>
            <div class="table-summary">
              Total pagado: <strong>{{ fmt(totalPagadoFiltrado) }}</strong>
              · {{ pagosFiltrados.length }} registro{{ pagosFiltrados.length !== 1 ? 's' : '' }}
              <span v-if="anioSeleccionado" class="anio-tag">año {{ anioSeleccionado }}</span>
            </div>
          </div>
          <div class="table-wrap">
            <table class="det-table">
              <thead><tr>
                <th>#Pago</th><th>Fecha</th><th>Meses</th><th>Valor</th><th>Descuento</th><th>Pagado hasta</th><th>Forma pago</th><th>Empleado</th>
              </tr></thead>
              <tbody>
                <tr v-for="p in pagosFiltrados" :key="p.Nro_Pago">
                  <td class="td-nro">{{ p.Nro_Pago }}</td>
                  <td>{{ fmtFecha(p.Fecha) }}</td>
                  <td class="td-center">{{ p.Meses_Pagos }}</td>
                  <td class="td-money">{{ fmt(p.Valor_pago) }}</td>
                  <td class="td-money">{{ p.Descuento ? fmt(p.Descuento) : '—' }}</td>
                  <td>{{ p.Mes_Pago_Hasta || '—' }}</td>
                  <td>{{ p.forma_pago_desc }}</td>
                  <td>{{ p.empleado_nombre }}</td>
                </tr>
                <tr v-if="!pagosFiltrados.length">
                  <td colspan="8" class="td-empty-year">Sin pagos en el año {{ anioSeleccionado }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- ══ TAB: Abonos ══ -->
      <div v-if="tabActivo === 'abonos'" class="tab-content">
        <div class="sub-tabs">
          <button class="sub-tab" :class="{ active: subTab === 'capital' }" @click="subTab='capital'">
            Abonos Capital ({{ detalle.abonos_capital.length }})
          </button>
          <button class="sub-tab" :class="{ active: subTab === 'cruce' }" @click="subTab='cruce'">
            Cruce de Abonos ({{ abonosCruzados.length }})
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
        <!-- Cruce de abonos (Pendiente = 0) -->
        <div v-if="subTab === 'cruce'">
          <div v-if="!abonosCruzados.length" class="tab-empty"><i class="bi bi-inbox"></i> Sin abonos cruzados</div>
          <div v-else class="table-wrap">
            <div class="table-summary">{{ abonosCruzados.length }} abono{{ abonosCruzados.length !== 1 ? 's' : '' }} cruzado{{ abonosCruzados.length !== 1 ? 's' : '' }}</div>
            <table class="det-table">
              <thead><tr><th>#</th><th>Fecha</th><th>Valor</th><th>Fecha Cruce</th><th>Forma pago</th><th>Observación</th></tr></thead>
              <tbody>
                <tr v-for="a in abonosCruzados" :key="a.Nro_Abono">
                  <td class="td-nro">{{ a.Nro_Abono }}</td>
                  <td>{{ fmtFecha(a.Fecha) }}</td>
                  <td class="td-money">{{ fmt(a.Valor_Abono) }}</td>
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

      <!-- ══ TAB: Codeudores ══ -->
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

      <!-- ══ TAB: Escritura ══ -->
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

    <!-- Modales de adjuntos (Teleport to body — fuera del v-if) -->
    <MultiAttachUploader
      v-model:open="fotosOpen"
      :nro-credito="detalle?.credito.Nro_Credito"
      :company-id="companyId"
      tipo="foto"
    />
    <MultiAttachUploader
      v-model:open="docsOpen"
      :nro-credito="detalle?.credito.Nro_Credito"
      :company-id="companyId"
      tipo="documento"
    />

  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useCompanyStore } from '@/stores/companyStore'
import api from '@/services/apis'
import MultiAttachUploader from '@/components/common/MultiAttachUploader.vue'

const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id)

// Modales de adjuntos
const fotosOpen = ref(false)
const docsOpen  = ref(false)

// ── Búsqueda ─────────────────────────────────────────────────────────────────
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

// ── Detalle ──────────────────────────────────────────────────────────────────
const detalle          = ref(null)
const loadingDetalle   = ref(false)
const tabActivo        = ref('general')
const subTab           = ref('capital')
const anioSeleccionado = ref('')

// Al cambiar de empresa, limpiar estado para evitar 500 en hipotecas endpoint
watch(companyId, () => {
  listaCreditos.value   = []
  detalle.value         = null
  nroSeleccionado.value = ''
  queryActual.value     = ''
  errorMsg.value        = ''
  fotosOpen.value       = false
  docsOpen.value        = false
})

const TABS = [
  { id: 'general',   label: 'Info General',  icono: 'bi-file-earmark-text',    badge: false },
  { id: 'cliente',   label: 'Info Cliente',  icono: 'bi-person-vcard',         badge: false },
  { id: 'pagos',     label: 'Pagos',         icono: 'bi-cash-coin',            badge: true  },
  { id: 'abonos',    label: 'Abonos',        icono: 'bi-piggy-bank',           badge: true  },
  { id: 'aumentos',  label: 'Aum. Capital',  icono: 'bi-graph-up-arrow',       badge: true  },
  { id: 'novedades', label: 'Novedades',     icono: 'bi-chat-left-text',       badge: true  },
  { id: 'deudores',  label: 'Codeudores',    icono: 'bi-people',               badge: true  },
  { id: 'escritura', label: 'Escritura',     icono: 'bi-file-earmark-richtext',badge: false },
]

function contadorTab(id) {
  if (!detalle.value) return 0
  const map = {
    pagos:     detalle.value.pagos?.length,
    abonos:    (detalle.value.abonos_capital?.length ?? 0) + (abonosCruzados.value?.length ?? 0),
    aumentos:  detalle.value.aumentos_capital?.length,
    novedades: detalle.value.novedades?.length,
    deudores:  detalle.value.otros_deudores?.length,
  }
  return map[id] ?? 0
}

async function cargarDetalle() {
  if (!nroSeleccionado.value) return
  loadingDetalle.value = true; errorMsg.value = ''
  tabActivo.value = 'general'; subTab.value = 'capital'
  anioSeleccionado.value = new Date().getFullYear()
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

// ── Info Cliente ──────────────────────────────────────────────────────────────
const LABELS_CLIENTE = {
  cedula: 'Cédula', nombres: 'Nombre completo', direccion: 'Dirección',
  Telefono: 'Teléfono', Celular: 'Celular', Mail: 'Email', Fax: 'Fax',
  Barrio: 'Barrio', Ciudad: 'Ciudad', Departamento: 'Departamento',
  Fecha_Nacimiento: 'Fecha Nacimiento', Actividad: 'Actividad / Profesión',
  Empresa: 'Empresa', Cargo: 'Cargo', Ingresos: 'Ingresos',
  Referencias: 'Referencias', Observaciones: 'Observaciones',
  Fecha_Ingreso: 'Fecha Ingreso', Estado_Civil: 'Estado Civil',
  Sexo: 'Sexo', Estrato: 'Estrato', NIT: 'NIT',
}
const SKIP_CLIENTE = new Set(['cedula']) // ya se muestra en cabecera

const clienteEntradas = computed(() => {
  const d = detalle.value?.cliente_detalle
  if (!d) return []
  return Object.entries(d)
    .filter(([k, v]) => {
      if (SKIP_CLIENTE.has(k)) return false
      if (v === null || v === '' || v === 0 || v === false) return false
      if (typeof v === 'object') return false  // buffers/dates complejos
      return true
    })
    .map(([k, v]) => ({
      key: k,
      label: LABELS_CLIENTE[k] || k.replace(/_/g, ' '),
      display: v instanceof Date ? fmtFecha(v.toISOString().split('T')[0])
               : (String(v).match(/^\d{4}-\d{2}-\d{2}/) ? fmtFecha(v) : v),
    }))
})

// ── Filtro años ───────────────────────────────────────────────────────────────
const aniosPagos = computed(() => {
  if (!detalle.value?.pagos.length) return []
  const s = new Set(detalle.value.pagos
    .map(p => p.Fecha ? new Date(p.Fecha + 'T00:00:00').getFullYear() : null)
    .filter(Boolean))
  return [...s].sort((a, b) => b - a)
})

const pagosFiltrados = computed(() => {
  if (!detalle.value?.pagos.length) return []
  if (!anioSeleccionado.value) return detalle.value.pagos
  return detalle.value.pagos.filter(p =>
    p.Fecha && new Date(p.Fecha + 'T00:00:00').getFullYear() == anioSeleccionado.value
  )
})

// ── Abonos filtrados ──────────────────────────────────────────────────────────
const abonosCruzados = computed(() =>
  detalle.value?.abonos_parciales.filter(a => !a.Pendiente) ?? []
)
const totalAbonosPendientes = computed(() =>
  detalle.value?.abonos_parciales
    .filter(a => a.Pendiente)
    .reduce((s, a) => s + (a.Valor_Abono || 0), 0) ?? 0
)

// ── Estado ────────────────────────────────────────────────────────────────────
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
  return (c.Anulado || c.Inactivo) ? 'bi-x-circle-fill' : 'bi-check-circle-fill'
})

// ── Totales ───────────────────────────────────────────────────────────────────
const totalPagadoFiltrado = computed(() =>
  pagosFiltrados.value.reduce((s, p) => s + (p.Valor_pago || 0), 0)
)
const totalAbonosCapital = computed(() =>
  detalle.value?.abonos_capital.reduce((s, a) => s + (a.Valor_Abono || 0), 0) ?? 0
)
const totalAumentos = computed(() =>
  detalle.value?.aumentos_capital.reduce((s, a) => s + (a.Valor_Abono || 0), 0) ?? 0
)

// ── Formateo ──────────────────────────────────────────────────────────────────
function fmt(v) {
  if (v == null || v === '' || v === 0) return '$ 0'
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v)
}
function fmtFecha(v) {
  if (!v) return '—'
  const d = new Date(v + 'T00:00:00')
  return new Intl.DateTimeFormat('es-CO', { day: '2-digit', month: 'short', year: 'numeric' }).format(d)
}

function abrirCargaFotos() { fotosOpen.value = true }
function abrirCargaDocs()  { docsOpen.value  = true }

// ── Impresión ─────────────────────────────────────────────────────────────────
function printStyles() {
  return `body{font-family:Arial,sans-serif;font-size:12px;color:#111;margin:20px}
    h1{font-size:16px;margin:0 0 4px;text-align:center}h2{font-size:13px;margin:0 0 12px;text-align:center;color:#444}
    .fecha{text-align:right;font-size:11px;color:#666;margin-bottom:12px}
    .sec{font-size:11px;font-weight:bold;text-transform:uppercase;letter-spacing:.5px;color:#0f2448;border-bottom:2px solid #0f2448;padding-bottom:2px;margin:14px 0 8px}
    table{width:100%;border-collapse:collapse;margin-bottom:12px}
    th{background:#0f2448;color:#fff;padding:6px 8px;font-size:11px;text-align:left}
    td{padding:5px 8px;border-bottom:1px solid #e5e5e5;font-size:11px}
    tr:nth-child(even) td{background:#f9f9f9}
    .kv td:first-child{width:40%;font-weight:600;color:#555}
    .total{font-size:12px;font-weight:bold;text-align:right;margin-top:6px}
    .obs{background:#fff8e1;border-left:4px solid #f59e0b;padding:8px 12px;margin:10px 0;font-size:12px}
    @media print{body{margin:0}}`
}

function imprimirResumen() {
  if (!detalle.value) return
  const c   = detalle.value.credito
  const hoy = new Intl.DateTimeFormat('es-CO', { day:'2-digit', month:'long', year:'numeric' }).format(new Date())
  const empresa = companyStore.selectedCompany?.name || ''
  const html = `<!DOCTYPE html><html><head><meta charset="utf-8">
    <title>Estado Cuenta Resumen - ${c.Nro_Credito}</title>
    <style>${printStyles()}</style></head><body>
    <h1>${empresa}</h1><h2>ESTADO DE CUENTA — RESUMEN</h2>
    <div class="fecha">Generado: ${hoy}</div>
    ${c.Nota_Tipo_Pago ? `<div class="obs"><strong>Nota:</strong> ${c.Nota_Tipo_Pago}</div>` : ''}
    <div class="sec">Datos del Cliente</div>
    <table class="kv"><tbody>
      <tr><td>Nombre</td><td>${c.cliente_nombre}</td></tr>
      <tr><td>Cédula</td><td>${c.Cliente}</td></tr>
      ${c.cliente_tel ? `<tr><td>Teléfono</td><td>${c.cliente_tel}</td></tr>` : ''}
      ${c.cliente_mail ? `<tr><td>Email</td><td>${c.cliente_mail}</td></tr>` : ''}
    </tbody></table>
    <div class="sec">Estado del Crédito</div>
    <table class="kv"><tbody>
      <tr><td>Nro. Crédito</td><td><strong>${c.Nro_Credito}</strong></td></tr>
      <tr><td>Valor Inicial</td><td>${fmt(c.Valor)}</td></tr>
      <tr><td>Valor Actual</td><td><strong>${fmt(c.Valor_Actual)}</strong></td></tr>
      <tr><td>% Interés Casa</td><td>${c.Interes}%</td></tr>
      <tr><td>% Interés Socio</td><td>${c.Interes_Socio}%</td></tr>
      <tr><td>Cuota / Mes</td><td>${fmt(c.cuota_mes)}</td></tr>
      <tr><td>Pago Hasta</td><td>${fmtFecha(c.Pago_Hasta)}</td></tr>
      <tr><td>Meses en Mora</td><td><strong>${c.meses_mora}</strong></td></tr>
      <tr><td>Valor Deuda</td><td><strong>${fmt(c.valor_deuda)}</strong></td></tr>
      <tr><td>Estado</td><td>${estadoLabel.value}</td></tr>
    </tbody></table>
    <div class="sec">Totales</div>
    <table class="kv"><tbody>
      <tr><td>Total Intereses Pagados</td><td>${fmt(detalle.value.pagos.reduce((s,p)=>s+(p.Valor_pago||0),0))}</td></tr>
      <tr><td>Total Abonos a Capital</td><td>${fmt(totalAbonosCapital.value)}</td></tr>
      <tr><td>Total Aumentos Capital</td><td>${fmt(totalAumentos.value)}</td></tr>
      ${totalAbonosPendientes.value > 0 ? `<tr><td>Abonos Parciales Pendientes</td><td><strong>${fmt(totalAbonosPendientes.value)}</strong></td></tr>` : ''}
    </tbody></table>
  </body></html>`
  const w = window.open('', '_blank', 'width=800,height=600')
  w.document.write(html); w.document.close(); w.focus()
  setTimeout(() => w.print(), 400)
}

function imprimirDetalle() {
  if (!detalle.value) return
  const c   = detalle.value.credito
  const hoy = new Intl.DateTimeFormat('es-CO', { day:'2-digit', month:'long', year:'numeric' }).format(new Date())
  const empresa = companyStore.selectedCompany?.name || ''
  const pagos = pagosFiltrados.value
  const periodo = anioSeleccionado.value ? `Año ${anioSeleccionado.value}` : 'Todos los años'
  const totalPagos = pagos.reduce((s, p) => s + (p.Valor_pago || 0), 0)
  const filas = pagos.map(p => `<tr>
    <td>${p.Nro_Pago}</td><td>${fmtFecha(p.Fecha)}</td>
    <td style="text-align:center">${p.Meses_Pagos}</td>
    <td>${fmt(p.Valor_pago)}</td><td>${p.Descuento ? fmt(p.Descuento) : '—'}</td>
    <td>${p.Mes_Pago_Hasta||'—'}</td><td>${p.forma_pago_desc}</td></tr>`).join('')
  const html = `<!DOCTYPE html><html><head><meta charset="utf-8">
    <title>Estado Cuenta Detalle - ${c.Nro_Credito}</title>
    <style>${printStyles()}</style></head><body>
    <h1>${empresa}</h1><h2>ESTADO DE CUENTA CON DETALLE DE PAGOS</h2>
    <div class="fecha">Generado: ${hoy}</div>
    ${c.Nota_Tipo_Pago ? `<div class="obs"><strong>Nota:</strong> ${c.Nota_Tipo_Pago}</div>` : ''}
    <div class="sec">Datos del Cliente</div>
    <table class="kv"><tbody>
      <tr><td>Nombre</td><td>${c.cliente_nombre}</td></tr>
      <tr><td>Cédula</td><td>${c.Cliente}</td></tr>
    </tbody></table>
    <div class="sec">Estado del Crédito</div>
    <table class="kv"><tbody>
      <tr><td>Nro. Crédito</td><td><strong>${c.Nro_Credito}</strong></td></tr>
      <tr><td>Valor Actual</td><td><strong>${fmt(c.Valor_Actual)}</strong></td></tr>
      <tr><td>Cuota / Mes</td><td>${fmt(c.cuota_mes)}</td></tr>
      <tr><td>Pago Hasta</td><td>${fmtFecha(c.Pago_Hasta)}</td></tr>
      <tr><td>Meses en Mora</td><td><strong>${c.meses_mora}</strong></td></tr>
      <tr><td>Valor Deuda</td><td><strong>${fmt(c.valor_deuda)}</strong></td></tr>
      <tr><td>Estado</td><td>${estadoLabel.value}</td></tr>
    </tbody></table>
    <div class="sec">Pagos Realizados — ${periodo}</div>
    ${pagos.length ? `<table><thead><tr>
      <th>#Pago</th><th>Fecha</th><th>Meses</th><th>Valor</th><th>Descuento</th><th>Pagado Hasta</th><th>Forma Pago</th>
    </tr></thead><tbody>${filas}</tbody></table>
    <div class="total">Total (${periodo}): ${fmt(totalPagos)} — ${pagos.length} registros</div>`
    : '<p style="color:#888;font-size:11px">Sin pagos en el período.</p>'}
  </body></html>`
  const w = window.open('', '_blank', 'width=900,height=700')
  w.document.write(html); w.document.close(); w.focus()
  setTimeout(() => w.print(), 400)
}
</script>

<style scoped>
.cc-wrap { padding: 0 20px 48px; max-width: 1200px; margin: 0 auto; }

/* ── Search panel ── */
.search-panel { background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 14px 16px; margin-bottom: 12px; display: flex; flex-direction: column; gap: 10px; }
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

/* ── Banners parpadeantes ── */
.banners-row { display: flex; gap: 10px; margin-bottom: 12px; flex-wrap: wrap; }
.obs-banner {
  flex: 1; min-width: 200px;
  display: flex; align-items: center; gap: 10px;
  border-radius: 10px; padding: 10px 16px;
  font-size: 13px; font-weight: 600;
  animation: parpadeo 1.6s ease-in-out infinite;
}
.obs-nota      { background: #fef3c7; border: 1.5px solid #f59e0b; color: #92400e; }
.obs-nota .bi  { color: #d97706; font-size: 16px; flex-shrink: 0; }
.obs-pendientes { background: #cffafe; border: 1.5px solid #06b6d4; color: #164e63; }
.obs-pendientes .bi { color: #0891b2; font-size: 16px; flex-shrink: 0; }
@keyframes parpadeo { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

/* ── Loading ── */
.estado-loading { display: flex; align-items: center; gap: 12px; justify-content: center; padding: 40px; color: #64748b; font-size: 14px; }
.spin-sm { width: 16px; height: 16px; border: 2px solid #e2e8f0; border-top-color: #0f2448; border-radius: 50%; animation: spin 0.8s linear infinite; display: inline-block; }
.spin-lg { width: 28px; height: 28px; border: 3px solid #e2e8f0; border-top-color: #0f2448; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Cliente + estado ── */
.cliente-estado-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.cliente-card { flex: 1; min-width: 0; }
.cliente-nombre { font-size: 20px; font-weight: 800; color: #0f2448; margin-bottom: 6px; }
.cliente-datos { display: flex; flex-wrap: wrap; gap: 10px; font-size: 13px; color: #64748b; }
.cliente-datos span { display: flex; align-items: center; gap: 5px; }
.header-right { display: flex; flex-direction: column; align-items: flex-end; gap: 8px; flex-shrink: 0; }
.estado-badge { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 700; border-radius: 20px; padding: 6px 16px; white-space: nowrap; }
.estado-vigente   { background: #d1fae5; color: #065f46; }
.estado-cancelado { background: #dbeafe; color: #1d4ed8; }
.estado-anulado, .estado-inactivo { background: #fee2e2; color: #991b1b; }
.action-btns { display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }
.btn-action { display: flex; align-items: center; gap: 5px; border: 1.5px solid; border-radius: 8px; padding: 6px 12px; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.15s; white-space: nowrap; }
.btn-fotos { background: #fff; border-color: #7c3aed; color: #7c3aed; }
.btn-fotos:hover { background: #7c3aed; color: #fff; }
.btn-docs  { background: #fff; border-color: #0369a1; color: #0369a1; }
.btn-docs:hover  { background: #0369a1; color: #fff; }
.print-btns { display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }
.btn-print { display: flex; align-items: center; gap: 5px; background: #fff; border: 1.5px solid #0f2448; color: #0f2448; border-radius: 8px; padding: 6px 12px; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.15s; white-space: nowrap; }
.btn-print:hover { background: #0f2448; color: #fff; }
.btn-print-det { border-color: #065f46; color: #065f46; }
.btn-print-det:hover { background: #065f46; color: #fff; }

/* ── Tabs ── */
.tabs-bar { display: flex; gap: 2px; overflow-x: auto; border-bottom: 2px solid #e2e8f0; scrollbar-width: none; padding: 0 4px; }
.tabs-bar::-webkit-scrollbar { display: none; }
.tab-btn { display: flex; align-items: center; gap: 6px; padding: 9px 14px; border: none; background: none; cursor: pointer; font-size: 13px; font-weight: 600; color: #64748b; white-space: nowrap; border-bottom: 3px solid transparent; margin-bottom: -2px; border-radius: 8px 8px 0 0; transition: all 0.18s; }
.tab-btn:hover { color: #0f2448; background: #f1f5f9; }
.tab-btn.active { color: #0f2448; border-bottom-color: #0f2448; background: #e8eef7; font-weight: 700; }
.tab-badge { background: #ef4444; color: #fff; font-size: 10px; font-weight: 700; border-radius: 10px; padding: 1px 6px; }

/* ── Tab content ── */
.tab-content { background: #fff; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 12px 12px; padding: 20px; }
.tab-empty { display: flex; align-items: center; gap: 10px; color: #94a3b8; font-size: 14px; padding: 30px; justify-content: center; }
.tab-empty .bi { font-size: 22px; }

/* ── Filtro año ── */
.pagos-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
.year-filter { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #64748b; }
.year-filter .bi { color: #0f2448; }
.sel-anio { border: 1.5px solid #e2e8f0; border-radius: 8px; padding: 6px 10px; font-size: 13px; font-weight: 600; color: #0f2448; outline: none; cursor: pointer; }
.sel-anio:focus { border-color: #0f2448; }
.anio-tag { background: #dbeafe; color: #1d4ed8; font-size: 11px; font-weight: 700; border-radius: 10px; padding: 2px 8px; margin-left: 6px; }
.td-empty-year { text-align: center; color: #94a3b8; padding: 24px; font-size: 13px; }

/* ── Info grid ── */
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.info-col { display: flex; flex-direction: column; }
.info-section-title { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px; color: #64748b; margin: 0 0 10px; display: flex; align-items: center; gap: 6px; }
.info-section-title .bi { color: #10b981; }
.rf-row { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; padding: 7px 0; border-bottom: 1px solid #f1f5f9; }
.rf-lbl { font-size: 12.5px; color: #64748b; flex-shrink: 0; }
.rf-val { font-size: 13px; font-weight: 600; color: #0f172a; text-align: right; word-break: break-word; max-width: 55%; }
.rf-nro     { color: #0f2448; font-size: 15px; }
.rf-cuota   { color: #065f46; font-size: 15px; }
.rf-juridica{ color: #dc2626; }
.rf-mora    { background: #fff7ed; margin: 0 -4px; padding: 7px 4px; border-radius: 4px; }
.rf-mora .rf-val { color: #ea580c; font-size: 16px; }
.rf-deuda   { background: #fef2f2; margin: 0 -4px; padding: 7px 4px; border-radius: 4px; }
.rf-deuda .rf-val { color: #dc2626; font-size: 16px; }
.rf-highlight { background: #ecfdf5; margin: 0 -4px; padding: 7px 4px; border-radius: 4px; }
.rf-highlight .rf-val { color: #065f46; font-size: 15px; }
.esc-text { font-size: 12px; font-weight: 400; text-align: right; word-break: break-word; }

/* ── Tables ── */
.table-wrap { overflow-x: auto; }
.table-summary { font-size: 12.5px; color: #64748b; padding: 8px 12px; background: #f8fafc; border-radius: 8px; margin-bottom: 10px; }
.det-table { width: 100%; border-collapse: collapse; font-size: 12.5px; min-width: 520px; }
.det-table th { background: #0f2448; color: #fff; padding: 9px 12px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.4px; white-space: nowrap; text-align: left; }
.det-table td { padding: 9px 12px; border-bottom: 1px solid #f1f5f9; color: #334155; vertical-align: top; }
.det-table tbody tr:hover { background: #f8fafc; }
.td-nro   { font-weight: 700; color: #0f2448; }
.td-money { font-weight: 600; color: #065f46; }
.td-center{ text-align: center; }
.td-obs   { font-size: 11.5px; color: #64748b; max-width: 200px; }
.det-nombre { font-weight: 600; display: block; }

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
  .chip-lbl { display: none; }
  .mode-chip { padding: 6px 10px; }
  .info-grid { grid-template-columns: 1fr; gap: 0; }
  .cliente-nombre { font-size: 17px; }
  .tab-btn span:first-of-type { display: none; }
  .header-right { align-items: flex-start; }
  .print-lbl { display: none; }
  .action-lbl { display: none; }
  .banners-row { flex-direction: column; }
  .pagos-toolbar { flex-direction: column; align-items: flex-start; }
}
@media (max-width: 576px) {
  .cc-wrap { padding: 0 8px 32px; }
  .tab-btn { padding: 10px 10px; font-size: 12px; gap: 4px; }
  .tab-content { padding: 14px 10px; }
  .cliente-estado-row { flex-direction: column; }
  .header-right { width: 100%; flex-direction: row; justify-content: space-between; align-items: center; }
}
</style>
