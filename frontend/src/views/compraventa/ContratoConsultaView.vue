<template>
  <div class="cv-consulta">

    <!-- ── BÚSQUEDA ─────────────────────────────────────────────── -->
    <div class="search-panel">
      <div class="search-line">
        <!-- Por Nro. Contrato -->
        <div class="search-input-wrap">
          <span class="search-lbl">Nro. Contrato</span>
          <i class="bi bi-file-earmark-text"></i>
          <input v-model="queryNro" class="search-input" placeholder="Ej: A57944"
            @keyup.enter="buscarPorNro" />
          <button class="btn-buscar" @click="buscarPorNro" :disabled="loadingNro || !queryNro.trim()">
            <span v-if="loadingNro" class="spinner-border spinner-border-sm"></span>
            <span v-else>Buscar</span>
          </button>
        </div>

        <div class="search-sep"></div>

        <!-- Por Cédula -->
        <div class="search-input-wrap">
          <span class="search-lbl">Cédula</span>
          <i class="bi bi-person"></i>
          <input v-model="queryCedula" class="search-input" placeholder="Ej: 12345678"
            @keyup.enter="buscarPorCedula" />
          <button class="btn-buscar" @click="buscarPorCedula" :disabled="loadingCedula || !queryCedula.trim()">
            <span v-if="loadingCedula" class="spinner-border spinner-border-sm"></span>
            <span v-else>Buscar</span>
          </button>
        </div>

        <!-- Selector inline cuando hay varios contratos -->
        <select v-if="listaContratos.length" class="form-select selector-contrato"
          v-model="nroSeleccionado" @change="cargarDetalle">
          <option value="">— Seleccionar contrato —</option>
          <option v-for="c in listaContratos" :key="c.nro_contrato" :value="c.nro_contrato">
            {{ c.nro_contrato }} · {{ formatFecha(c.fecha_inicio) }} · {{ formatCurrency(c.valor_contrato) }} · {{ c.estado_descripcion }}
          </option>
        </select>
      </div>
    </div>

    <!-- Error -->
    <div v-if="errorMsg" class="alerta-error">
      <i class="bi bi-exclamation-triangle-fill"></i> {{ errorMsg }}
    </div>

    <!-- Loading detalle -->
    <div v-if="loadingDetalle" class="estado-loading">
      <div class="spinner-border text-primary"></div>
      <span>Cargando contrato...</span>
    </div>

    <!-- ── DETALLE ────────────────────────────────────────────────── -->
    <template v-if="detalle && !loadingDetalle">

      <!-- Cliente + Estado en una sola línea -->
      <div class="cliente-estado-row">
        <div class="cliente-card">
          <div class="cliente-nombre">{{ detalle.contrato.nombres }} {{ detalle.contrato.apellidos }}</div>
          <div class="cliente-datos">
            <span><i class="bi bi-person-badge"></i> {{ detalle.contrato.cedula }}</span>
            <span v-if="detalle.contrato.telefono"><i class="bi bi-telephone"></i> {{ detalle.contrato.telefono }}</span>
            <span v-if="detalle.contrato.direccion"><i class="bi bi-geo-alt"></i> {{ detalle.contrato.direccion }}</span>
          </div>
        </div>
        <div class="estado-banner" :class="estadoClass(detalle.contrato.estado)">
          <i class="bi estado-icon" :class="estadoIcon(detalle.contrato.estado)"></i>
          <span class="estado-texto">{{ detalle.contrato.estado_descripcion || estadoLabel(detalle.contrato.estado) }}</span>
        </div>
      </div>

      <!-- ── TARJETA RESUMEN FINANCIERO ── -->
      <div class="resumen-card" v-if="resumen">
        <div class="resumen-titulo">
          <i class="bi bi-calculator-fill"></i> Resumen Financiero
        </div>
        <div class="resumen-body">
          <!-- Columna izquierda -->
          <div class="resumen-col">
            <div class="rf-row">
              <span class="rf-label">Fecha Inicio</span>
              <span class="rf-val">{{ formatFecha(detalle.contrato.fecha_inicio) }}</span>
            </div>
            <div class="rf-row">
              <span class="rf-label">Valor Contrato</span>
              <span class="rf-val">{{ formatCurrency(detalle.contrato.valor_contrato) }}</span>
            </div>
            <div class="rf-row">
              <span class="rf-label">Interés</span>
              <span class="rf-val">{{ detalle.contrato.porcentaje }}%</span>
            </div>
            <div class="rf-row">
              <span class="rf-label">Cuota / Mes</span>
              <span class="rf-val">{{ formatCurrency(resumen.cuotaMes) }}</span>
            </div>
            <div class="rf-row rf-row--highlight">
              <span class="rf-label">Sobrecosto</span>
              <span class="rf-val">{{ formatCurrency(resumen.sobrecosto) }}</span>
            </div>
            <div class="rf-row">
              <span class="rf-label">Abonos</span>
              <span class="rf-val rf-abono">− {{ formatCurrency(resumen.totalAbonos) }}</span>
            </div>
            <div class="rf-row rf-row--deuda">
              <span class="rf-label">Deuda Actual</span>
              <span class="rf-val">{{ formatCurrency(resumen.deudaActual) }}</span>
            </div>
            <div class="rf-row" v-if="resumen.fechaUltimaAmpliacion">
              <span class="rf-label">Últ. Ampliación</span>
              <span class="rf-val">{{ formatFecha(resumen.fechaUltimaAmpliacion) }}</span>
            </div>
          </div>

          <!-- Divisor -->
          <div class="resumen-div"></div>

          <!-- Columna derecha -->
          <div class="resumen-col resumen-col--right">
            <div class="rf-row">
              <span class="rf-label">Plazo Pactado</span>
              <span class="rf-val">{{ detalle.contrato.nro_meses }} meses</span>
            </div>
            <div class="rf-row">
              <span class="rf-label">Meses Deuda</span>
              <span class="rf-val">{{ resumen.mesesDeuda }}</span>
            </div>
            <div class="rf-row">
              <span class="rf-label">Días Deuda</span>
              <span class="rf-val rf-dias">{{ resumen.diasDeuda }} días</span>
            </div>
            <div class="rf-row">
              <span class="rf-label">Prorrogas (meses)</span>
              <span class="rf-val">{{ resumen.sumaMesesProrrogados }}</span>
            </div>
            <div class="rf-row rf-row--total">
              <span class="rf-label">Total Meses</span>
              <span class="rf-val">{{ resumen.totalMeses }}</span>
            </div>
            <div class="rf-row">
              <span class="rf-label">Abonos Registrados</span>
              <span class="rf-val">{{ detalle.abonos?.length ?? 0 }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Layout 2 columnas -->
      <div class="layout-cols">

        <!-- ── COLUMNA IZQUIERDA: FOTOS ── -->
        <div class="col-fotos">
          <div class="seccion-titulo"><i class="bi bi-images"></i> Fotos del Contrato</div>

          <div class="fotos-grid" v-if="fotos.length">
            <div v-for="foto in fotos" :key="foto.id" class="foto-item">
              <img :src="fotoUrl(foto.url)" :alt="foto.name" @click="fotoAmpliada = foto" />
              <button class="btn-del-foto" @click="eliminarFoto(foto)">
                <i class="bi bi-trash-fill"></i>
              </button>
            </div>
          </div>
          <p v-else class="sin-fotos">Sin fotos registradas.</p>

          <div class="foto-uploader">
            <p class="foto-uploader-label"><i class="bi bi-plus-circle"></i> Agregar foto</p>
            <ImageUploaderPro
              :key="uploaderKey"
              label="Seleccionar foto"
              :showRemove="false"
              :outputWidth="1200"
              outputFormat="jpeg"
              :outputQuality="0.85"
              @change="onFotoChange"
            />
            <p v-if="uploading" class="foto-hint">
              <span class="spinner-border spinner-border-sm me-1"></span> Subiendo...
            </p>
          </div>
        </div>

        <!-- ── COLUMNA DERECHA: INFO ── -->
        <div class="col-info">

          <!-- Datos del contrato -->
          <div class="seccion">
            <div class="seccion-titulo"><i class="bi bi-file-earmark-text"></i> Datos del Contrato</div>
            <div class="cc-grid">
              <div class="cc-field"><label>Nro. Contrato</label><span>{{ detalle.contrato.nro_contrato }}</span></div>
              <div class="cc-field"><label>Fecha Inicio</label><span>{{ formatFecha(detalle.contrato.fecha_inicio) }}</span></div>
              <div class="cc-field"><label>Fecha Final</label><span>{{ formatFecha(detalle.contrato.fecha_final) }}</span></div>
              <div class="cc-field"><label>Meses</label><span>{{ detalle.contrato.nro_meses }}</span></div>
              <div class="cc-field"><label>Porcentaje</label><span>{{ detalle.contrato.porcentaje }}%</span></div>
              <div class="cc-field"><label>Valor Contrato</label><span class="val-destacado">{{ formatCurrency(detalle.contrato.valor_contrato) }}</span></div>
              <div class="cc-field"><label>Empleado</label><span>{{ detalle.contrato.cod_empleado }}</span></div>
              <div class="cc-field"><label>Fecha Registro</label><span>{{ formatFecha(detalle.contrato.Fecha_Registro) }}</span></div>
              <div v-if="detalle.contrato.Observaciones" class="cc-field cc-field--full">
                <label>Observaciones</label><span>{{ detalle.contrato.Observaciones }}</span>
              </div>
            </div>
          </div>

          <!-- Artículos -->
          <div class="seccion" v-if="detalle.articulos.length">
            <div class="seccion-titulo"><i class="bi bi-gem"></i> Artículos</div>
            <div class="tabla-wrap">
              <table class="tabla-cv">
                <thead>
                  <tr>
                    <th>Categoría</th>
                    <th>Item</th>
                    <th>Detalle</th>
                    <th>Kilate</th>
                    <th class="text-end">Peso</th>
                    <th class="text-end">Cant.</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(a, i) in detalle.articulos" :key="i">
                    <td>{{ a.cod_categoria }}</td>
                    <td>{{ a.Item_articulo }}</td>
                    <td>{{ a.detalle }}</td>
                    <td>{{ a.kilate }}</td>
                    <td class="text-end">{{ Number(a.peso).toFixed(1) }}</td>
                    <td class="text-end">{{ a.Cantidad }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Campo Observación -->
          <div class="obs-card">
            <div class="seccion-titulo"><i class="bi bi-chat-left-text"></i> Agregar Observación</div>
            <div class="obs-body">
              <textarea v-model="nuevaObs" class="obs-textarea"
                placeholder="Ej: Cliente solicita plazo hasta el 15/08/2026, extravío de artículo, acuerdo especial..."
                rows="3"></textarea>
              <div class="obs-footer">
                <span v-if="detalle.contrato.Observaciones" class="obs-existente">
                  <i class="bi bi-info-circle"></i> Ya tiene observaciones — se anexará al inicio
                </span>
                <button class="btn-guardar-obs" @click="guardarObs" :disabled="savingObs || !nuevaObs.trim()">
                  <span v-if="savingObs" class="spinner-border spinner-border-sm me-1"></span>
                  <i v-else class="bi bi-floppy me-1"></i>
                  {{ savingObs ? 'Guardando...' : 'Guardar observación' }}
                </button>
              </div>
              <div v-if="detalle.contrato.Observaciones" class="obs-actual">
                <label>Observaciones actuales:</label>
                <pre class="obs-pre">{{ detalle.contrato.Observaciones }}</pre>
              </div>
            </div>
          </div>

          <!-- Tarjeta Prorrogas (siempre visible) -->
          <div class="tarjeta-estado" :class="detalle.prorrogas.length ? 'tc-info' : 'tc-vacio'">
            <div class="tc-header">
              <i class="bi bi-arrow-repeat"></i>
              Prorrogas
              <span class="tc-badge" :title="`${detalle.prorrogas.length} registros`">
                {{ resumen?.sumaMesesProrrogados ?? 0 }} meses
              </span>
            </div>
            <div v-if="detalle.prorrogas.length" class="tc-body">
              <div class="tabla-wrap">
                <table class="tabla-cv">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Fecha</th>
                      <th>Meses</th>
                      <th class="text-end">Valor</th>
                      <th>Empleado</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(p, i) in detalle.prorrogas" :key="i">
                      <td>{{ i + 1 }}</td>
                      <td>{{ formatFecha(p.fecha_prorroga) }}</td>
                      <td>{{ p.meses_prorrogados }}</td>
                      <td class="text-end">{{ formatCurrency(p.valor_prorroga) }}</td>
                      <td>{{ p.Cod_Empleado }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div v-else class="tc-vacio-msg">
              <i class="bi bi-dash-circle"></i> Sin prorrogas registradas
            </div>
          </div>

          <!-- Tarjeta Retiro (siempre visible) -->
          <div class="tarjeta-estado" :class="detalle.retiro ? 'tc-retiro' : 'tc-vacio'">
            <div class="tc-header">
              <i class="bi bi-box-arrow-left"></i>
              Retiro
            </div>
            <div v-if="detalle.retiro" class="tc-body">
              <div class="cc-grid">
                <div class="cc-field"><label>Fecha Retiro</label><span>{{ formatFecha(detalle.retiro.fecha_retiro) }}</span></div>
                <div class="cc-field"><label>Valor Retiro</label><span class="val-destacado">{{ formatCurrency(detalle.retiro.valor_retiro) }}</span></div>
                <div class="cc-field"><label>Sobre Costo</label><span>{{ formatCurrency(detalle.retiro.sobre_costo) }}</span></div>
                <div class="cc-field"><label>Descuento</label><span>{{ formatCurrency(detalle.retiro.descuento) }}</span></div>
                <div class="cc-field"><label>Empleado</label><span>{{ detalle.retiro.Cod_Empleado }}</span></div>
                <div class="cc-field"><label>Autorizado</label><span>{{ detalle.retiro.Autorizado }}</span></div>
              </div>
            </div>
            <div v-else class="tc-vacio-msg">
              <i class="bi bi-dash-circle"></i> Sin retiro registrado — contrato activo o rematado
            </div>
          </div>

          <!-- Tarjeta Remate (siempre visible) -->
          <div class="tarjeta-estado" :class="detalle.remate ? 'tc-remate' : 'tc-vacio'">
            <div class="tc-header">
              <i class="bi bi-hammer"></i>
              Remate
            </div>
            <div v-if="detalle.remate" class="tc-body">
              <div class="cc-grid">
                <div class="cc-field"><label>Fecha Remate</label><span>{{ formatFecha(detalle.remate.fecha_remate) }}</span></div>
                <div class="cc-field"><label>Valor</label><span class="val-destacado">{{ formatCurrency(detalle.remate.valor_contrato) }}</span></div>
                <div class="cc-field"><label>Empleado</label><span>{{ detalle.remate.Cod_Empleado }}</span></div>
              </div>
            </div>
            <div v-else class="tc-vacio-msg">
              <i class="bi bi-dash-circle"></i> Sin remate registrado
            </div>
          </div>

          <!-- Tarjeta Abonos (siempre visible) -->
          <div class="tarjeta-estado" :class="detalle.abonos?.length ? 'tc-abono' : 'tc-vacio'">
            <div class="tc-header">
              <i class="bi bi-cash-coin"></i>
              Abonos a Capital
              <span class="tc-badge">{{ detalle.abonos?.length ?? 0 }}</span>
            </div>
            <div v-if="detalle.abonos?.length" class="tc-body">
              <div class="tabla-wrap">
                <table class="tabla-cv">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Fecha</th>
                      <th>Tipo</th>
                      <th class="text-end">Valor Abono</th>
                      <th>Empleado</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(a, i) in detalle.abonos" :key="i">
                      <td>{{ i + 1 }}</td>
                      <td>{{ formatFecha(a.Fecha_Abono) }}</td>
                      <td>{{ a.Cod_Tipo }}</td>
                      <td class="text-end">{{ formatCurrency(a.Valor_Abono) }}</td>
                      <td>{{ a.Cod_Empleado }}</td>
                    </tr>
                  </tbody>
                  <tfoot>
                    <tr class="tf-total">
                      <td colspan="3"><strong>Total Abonado</strong></td>
                      <td class="text-end"><strong>{{ formatCurrency(resumen?.totalAbonos) }}</strong></td>
                      <td></td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
            <div v-else class="tc-vacio-msg">
              <i class="bi bi-dash-circle"></i> Sin abonos registrados
            </div>
          </div>

          <!-- Exportar -->
          <div class="seccion">
            <div class="seccion-titulo"><i class="bi bi-printer"></i> Estado de Cuenta</div>
            <ExportToolbar
              :data="exportData"
              :columns="exportColumns"
              :filename="`contrato-${detalle.contrato.nro_contrato}`"
              :title="`Estado de Cuenta — Contrato ${detalle.contrato.nro_contrato}`"
            />
          </div>

        </div>
      </div>
    </template>

    <!-- Lightbox -->
    <div v-if="fotoAmpliada" class="lightbox" @click="fotoAmpliada = null">
      <img :src="fotoUrl(fotoAmpliada.url)" />
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useCompanyStore } from '@/stores/companyStore'
import api from '@/services/apis'
import ImageUploaderPro from '@/components/common/ImageUploaderPro.vue'
import ExportToolbar from '@/components/common/ExportToolbar.vue'

const companyStore = useCompanyStore()
const cid = computed(() => companyStore.selectedCompany?.id)

// Búsqueda
const queryNro       = ref('')
const queryCedula    = ref('')
const loadingNro     = ref(false)
const loadingCedula  = ref(false)
const loadingDetalle = ref(false)
const errorMsg       = ref('')

// Resultados
const listaContratos  = ref([])
const nroSeleccionado = ref('')
const detalle         = ref(null)

// Fotos
const fotos        = ref([])
const uploading    = ref(false)
const uploaderKey  = ref(0)
const fotoAmpliada = ref(null)

// Observación
const nuevaObs  = ref('')
const savingObs = ref(false)

// ── Búsqueda por Nro. Contrato ───────────────────────────────────────────────

async function buscarPorNro() {
  if (!queryNro.value.trim() || !cid.value) return
  resetAll()
  loadingNro.value = true
  try {
    await cargarDetalleNro(queryNro.value.trim())
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || 'Contrato no encontrado'
  } finally {
    loadingNro.value = false
  }
}

// ── Búsqueda por Cédula ──────────────────────────────────────────────────────

async function buscarPorCedula() {
  if (!queryCedula.value.trim() || !cid.value) return
  resetAll()
  loadingCedula.value = true
  try {
    const res = await api.get('/api/compraventa/contratos-por-cedula', {
      params: { company_id: cid.value, cedula: queryCedula.value.trim() }
    })
    listaContratos.value = res.data.contratos || []
    if (listaContratos.value.length === 1) {
      nroSeleccionado.value = listaContratos.value[0].nro_contrato
      await cargarDetalle()
    }
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || 'No se encontraron contratos para esa cédula'
  } finally {
    loadingCedula.value = false
  }
}

// ── Cargar detalle de un contrato ────────────────────────────────────────────

async function cargarDetalle() {
  if (!nroSeleccionado.value) return
  await cargarDetalleNro(nroSeleccionado.value)
}

async function cargarDetalleNro(nro) {
  loadingDetalle.value = true
  errorMsg.value       = ''
  detalle.value        = null
  fotos.value          = []
  try {
    const res = await api.get('/api/compraventa/contrato', {
      params: { company_id: cid.value, nro_contrato: nro }
    })
    detalle.value = res.data
    await cargarFotos(nro)
  } finally {
    loadingDetalle.value = false
  }
}

async function cargarFotos(nro) {
  try {
    const res = await api.get('/api/compraventa/contrato/fotos', {
      params: { company_id: cid.value, nro_contrato: nro }
    })
    fotos.value = res.data
  } catch {}
}

function resetAll() {
  errorMsg.value       = ''
  listaContratos.value = []
  nroSeleccionado.value = ''
  detalle.value        = null
  fotos.value          = []
}

// ── Fotos ────────────────────────────────────────────────────────────────────

async function guardarObs() {
  if (!nuevaObs.value.trim() || !detalle.value || !cid.value) return
  savingObs.value = true
  try {
    const res = await api.put('/api/compraventa/contrato/observacion',
      { observacion: nuevaObs.value.trim() },
      { params: { company_id: cid.value, nro_contrato: detalle.value.contrato.nro_contrato } }
    )
    // Actualizar observaciones en el detalle local sin recargar todo
    detalle.value.contrato.Observaciones = res.data.observaciones
    nuevaObs.value = ''
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || 'Error guardando observación'
  } finally {
    savingObs.value = false
  }
}

async function onFotoChange(blob) {
  if (!detalle.value || !cid.value) return
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', blob, `contrato_${detalle.value.contrato.nro_contrato}.jpg`)
    const res = await api.post('/api/compraventa/contrato/foto', fd, {
      params: { company_id: cid.value, nro_contrato: detalle.value.contrato.nro_contrato }
    })
    fotos.value.push(res.data)
    uploaderKey.value++
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || 'Error subiendo foto'
  } finally {
    uploading.value = false
  }
}

async function eliminarFoto(foto) {
  if (!confirm('¿Eliminar esta foto?')) return
  try {
    await api.delete(`/api/compraventa/contrato/foto/${foto.id}`)
    fotos.value = fotos.value.filter(f => f.id !== foto.id)
  } catch {}
}

function fotoUrl(url) {
  if (!url) return ''
  if (url.startsWith('http') || url.startsWith('blob:')) return url
  return (import.meta.env.VITE_API_URL || '') + url
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatCurrency(val) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 })
    .format(val ?? 0)
}

function formatFecha(val) {
  if (!val) return '—'
  return new Intl.DateTimeFormat('es-CO', { day: '2-digit', month: '2-digit', year: 'numeric' })
    .format(new Date(String(val).slice(0, 10) + 'T12:00:00'))
}

function estadoLabel(e) {
  return e === 'V' ? 'Vigente' : e === 'R' ? 'Retirado' : e === 'D' ? 'Rematado' : e || '—'
}

function estadoIcon(e) {
  return e === 'V' ? 'bi-check-circle-fill' : e === 'R' ? 'bi-box-arrow-left' : e === 'D' ? 'bi-hammer' : 'bi-circle'
}

function estadoClass(e) {
  return e === 'V' ? 'banner-v' : e === 'R' ? 'banner-r' : e === 'D' ? 'banner-d' : ''
}

// ── Resumen financiero ────────────────────────────────────────────────────────

const resumen = computed(() => {
  if (!detalle.value) return null
  const { contrato, prorrogas, abonos } = detalle.value

  // Fechas en hora local (evitar desfase UTC)
  const inicio = new Date(String(contrato.fecha_inicio).slice(0, 10) + 'T12:00:00')
  const hoy    = new Date(); hoy.setHours(12, 0, 0, 0)

  // Meses completos transcurridos
  let mesesCompletos = (hoy.getFullYear() - inicio.getFullYear()) * 12
                     + (hoy.getMonth()    - inicio.getMonth())
  let diasRestantes  = hoy.getDate() - inicio.getDate()
  if (diasRestantes < 0) {
    mesesCompletos--
    const diasUltimoMes = new Date(hoy.getFullYear(), hoy.getMonth(), 0).getDate()
    diasRestantes += diasUltimoMes
  }

  const mesesDeuda = mesesCompletos
  const diasDeuda  = diasRestantes

  // Suma de meses prorrogados (se descuenta del total)
  const sumaMesesProrrogados = prorrogas.reduce((s, p) => s + (Number(p.meses_prorrogados) || 0), 0)
  const totalMeses = mesesDeuda + (diasDeuda > 0 ? 1 : 0) - sumaMesesProrrogados

  // Cálculos financieros
  const porcentaje    = Number(contrato.porcentaje)     || 0
  const valorContrato = Number(contrato.valor_contrato) || 0
  const cuotaMes      = valorContrato * (porcentaje / 100)
  const sobrecosto    = totalMeses * cuotaMes
  const totalAbonos   = (abonos || []).reduce((s, a) => s + (Number(a.Valor_Abono) || 0), 0)
  const deudaActual   = valorContrato + sobrecosto - totalAbonos

  // Última ampliación (prorroga más reciente)
  const fechaUltimaAmpliacion = prorrogas.length
    ? prorrogas.reduce((max, p) => p.fecha_prorroga > max ? p.fecha_prorroga : max,
                       prorrogas[0].fecha_prorroga)
    : null

  return { mesesDeuda, diasDeuda, totalMeses, sumaMesesProrrogados,
           cuotaMes, sobrecosto, totalAbonos, deudaActual, fechaUltimaAmpliacion }
})

// ── Export ───────────────────────────────────────────────────────────────────

const exportColumns = [
  { key: 'c1', label: 'Campo / Detalle' },
  { key: 'c2', label: 'Valor' },
  { key: 'c3', label: 'Campo 2' },
  { key: 'c4', label: 'Valor 2' },
]

const exportData = computed(() => {
  if (!detalle.value) return []
  const { contrato, articulos, prorrogas, retiro, remate } = detalle.value
  const rows = []

  rows.push({ _sectionHeader: true, _title: 'CLIENTE' })
  rows.push({ c1: 'Nombre', c2: `${contrato.nombres || ''} ${contrato.apellidos || ''}`.trim(), c3: 'Cédula', c4: contrato.cedula })
  rows.push({ c1: 'Teléfono', c2: contrato.telefono || '—', c3: 'Dirección', c4: contrato.direccion || '—' })

  rows.push({ _sectionHeader: true, _title: 'CONTRATO' })
  rows.push({ c1: 'Nro. Contrato', c2: contrato.nro_contrato, c3: 'Estado', c4: contrato.estado_descripcion || estadoLabel(contrato.estado) })
  rows.push({ c1: 'Fecha Inicio', c2: formatFecha(contrato.fecha_inicio), c3: 'Fecha Final', c4: formatFecha(contrato.fecha_final) })
  rows.push({ c1: 'Meses', c2: contrato.nro_meses, c3: 'Porcentaje', c4: `${contrato.porcentaje}%` })
  rows.push({ c1: 'Valor Contrato', c2: formatCurrency(contrato.valor_contrato), c3: 'Empleado', c4: contrato.cod_empleado })
  if (contrato.Observaciones) rows.push({ c1: 'Observaciones', c2: contrato.Observaciones, c3: '', c4: '' })

  if (articulos.length) {
    rows.push({ _sectionHeader: true, _title: 'ARTÍCULOS' })
    rows.push({ c1: 'Categoría', c2: 'Item', c3: 'Detalle', c4: 'Kilate / Peso / Cant.' })
    articulos.forEach(a => rows.push({
      c1: a.cod_categoria, c2: a.Item_articulo, c3: a.detalle,
      c4: `${a.kilate || ''} / ${Number(a.peso).toFixed(1)} / ${a.Cantidad}`
    }))
  }

  rows.push({ _sectionHeader: true, _title: `PRORROGAS (${prorrogas.length})` })
  if (prorrogas.length) {
    prorrogas.forEach((p, i) => rows.push({
      c1: i + 1, c2: formatFecha(p.fecha_prorroga),
      c3: `${p.meses_prorrogados} mes(es)`, c4: formatCurrency(p.valor_prorroga)
    }))
  } else {
    rows.push({ c1: 'Sin prorrogas registradas', c2: '', c3: '', c4: '' })
  }

  rows.push({ _sectionHeader: true, _title: 'RETIRO' })
  if (retiro) {
    rows.push({ c1: 'Fecha Retiro', c2: formatFecha(retiro.fecha_retiro), c3: 'Valor Retiro', c4: formatCurrency(retiro.valor_retiro) })
    rows.push({ c1: 'Sobre Costo', c2: formatCurrency(retiro.sobre_costo), c3: 'Descuento', c4: formatCurrency(retiro.descuento) })
  } else {
    rows.push({ c1: 'Sin retiro registrado', c2: '', c3: '', c4: '' })
  }

  rows.push({ _sectionHeader: true, _title: 'REMATE' })
  if (remate) {
    rows.push({ c1: 'Fecha Remate', c2: formatFecha(remate.fecha_remate), c3: 'Valor', c4: formatCurrency(remate.valor_contrato) })
  } else {
    rows.push({ c1: 'Sin remate registrado', c2: '', c3: '', c4: '' })
  }

  const { abonos } = detalle.value
  rows.push({ _sectionHeader: true, _title: `ABONOS A CAPITAL (${abonos?.length ?? 0})` })
  if (abonos?.length) {
    abonos.forEach((a, i) => rows.push({
      c1: i + 1, c2: formatFecha(a.Fecha_Abono),
      c3: a.Cod_Tipo, c4: formatCurrency(a.Valor_Abono)
    }))
    rows.push({ c1: 'TOTAL ABONADO', c2: formatCurrency(resumen.value?.totalAbonos), c3: '', c4: '' })
  } else {
    rows.push({ c1: 'Sin abonos registrados', c2: '', c3: '', c4: '' })
  }

  if (resumen.value) {
    const r = resumen.value
    rows.push({ _sectionHeader: true, _title: 'RESUMEN FINANCIERO' })
    rows.push({ c1: 'Meses Deuda', c2: r.mesesDeuda, c3: 'Días Deuda', c4: r.diasDeuda })
    rows.push({ c1: 'Total Meses', c2: r.totalMeses, c3: 'Cuota/Mes', c4: formatCurrency(r.cuotaMes) })
    rows.push({ c1: 'Sobrecosto', c2: formatCurrency(r.sobrecosto), c3: 'Abonos', c4: formatCurrency(r.totalAbonos) })
    rows.push({ c1: 'DEUDA ACTUAL', c2: formatCurrency(r.deudaActual), c3: '', c4: '' })
  }

  return rows
})
</script>

<style scoped>
.cv-consulta {
  max-width: 1100px;
  margin: 0 auto;
  padding: 20px 20px 60px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* ── Búsqueda ─────────────────────────────────────────────────────────────── */
.search-panel {
  background: #fff;
  border: 1.5px solid #e2e8f0;
  border-radius: 14px;
  padding: 12px 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,.05);
}
.search-line { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.search-sep { width: 1px; height: 28px; background: #e2e8f0; flex-shrink: 0; }
.search-lbl { font-size: 11px; font-weight: 700; color: #94a3b8; white-space: nowrap; text-transform: uppercase; letter-spacing: .4px; }
.search-input-wrap {
  display: flex; align-items: center; gap: 6px;
  border: 1.5px solid #e2e8f0; border-radius: 10px;
  padding: 5px 10px; background: #f8fafc; flex: 1; min-width: 200px;
}
.search-input-wrap .bi { color: #94a3b8; font-size: 14px; flex-shrink: 0; }
.search-input { flex: 1; border: none; outline: none; background: transparent; font-size: 13px; color: #1e293b; min-width: 80px; }
.search-input::placeholder { color: #94a3b8; }
.btn-buscar {
  background: #1e3a5f; color: #fff; border: none; border-radius: 7px;
  padding: 5px 14px; font-size: 12.5px; font-weight: 600;
  cursor: pointer; white-space: nowrap; transition: background .15s; flex-shrink: 0;
}
.btn-buscar:hover:not(:disabled) { background: #1e40af; }
.btn-buscar:disabled { opacity: .55; cursor: default; }
.selector-contrato { font-size: 12.5px; flex: 2; min-width: 220px; }

/* ── Alerta error ─────────────────────────────────────────────────────────── */
.alerta-error {
  background: #fee2e2; color: #dc2626; border: 1px solid #fca5a5;
  border-radius: 10px; padding: 12px 16px; font-size: 13.5px;
  display: flex; gap: 8px; align-items: center;
}
.estado-loading { display: flex; align-items: center; gap: 12px; padding: 30px; color: #64748b; font-size: 14px; }

/* ── Cliente + Estado en una línea ────────────────────────────────────────── */
.cliente-estado-row {
  display: flex; align-items: stretch; gap: 14px;
}
.cliente-card {
  flex: 1;
  background: linear-gradient(135deg, #1e3a5f 0%, #1e40af 100%);
  border-radius: 14px; padding: 14px 20px;
}
.cliente-nombre { font-size: 18px; font-weight: 800; color: #fff; margin-bottom: 6px; }
.cliente-datos { display: flex; flex-wrap: wrap; gap: 14px; }
.cliente-datos span { font-size: 12.5px; color: #bfdbfe; display: flex; align-items: center; gap: 5px; }
.cliente-datos .bi { color: #93c5fd; }

/* Estado parpadeante */
.estado-banner {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 6px; border-radius: 14px; padding: 14px 28px;
  font-size: 18px; font-weight: 900; letter-spacing: 1px; text-transform: uppercase;
  min-width: 160px; flex-shrink: 0;
}
.estado-icon { font-size: 26px; animation: pulso 1.4s ease-in-out infinite; }
.estado-texto { animation: pulso 1.4s ease-in-out infinite; }
@keyframes pulso { 0%,100% { opacity: 1; } 50% { opacity: .35; } }
.banner-v { background: #dcfce7; color: #166534; border: 2px solid #86efac; }
.banner-r { background: #fef3c7; color: #92400e; border: 2px solid #fcd34d; }
.banner-d { background: #fee2e2; color: #991b1b; border: 2px solid #fca5a5; }

/* ── Resumen financiero ───────────────────────────────────────────────────── */
.resumen-card {
  background: #fff;
  border: 1.5px solid #e2e8f0;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,.06);
}
.resumen-titulo {
  display: flex; align-items: center; gap: 7px;
  font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .5px;
  color: #475569; padding: 11px 18px; background: #f8fafc; border-bottom: 1px solid #e2e8f0;
}
.resumen-titulo .bi { color: #1e40af; font-size: 14px; }
.resumen-body {
  display: grid; grid-template-columns: 1fr 1px 1fr;
  padding: 14px 18px; gap: 0;
}
.resumen-div { background: #e2e8f0; margin: 0 16px; }
.resumen-col { display: flex; flex-direction: column; gap: 6px; }
.resumen-col--right { padding-left: 4px; }
.rf-row { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; padding: 3px 6px; border-radius: 6px; }
.rf-row--highlight { background: #fef3c7; }
.rf-row--deuda     { background: #fee2e2; }
.rf-row--total     { background: #eff6ff; }
.rf-label { font-size: 11.5px; color: #64748b; font-weight: 500; white-space: nowrap; }
.rf-val   { font-size: 13px; font-weight: 700; color: #1e293b; text-align: right; }
.rf-abono { color: #059669; }
.rf-dias  { color: #d97706; }
.rf-row--highlight .rf-val { color: #92400e; }
.rf-row--deuda .rf-val     { color: #991b1b; font-size: 14px; }

/* Observación */
.obs-card { background: #fff; border: 1.5px solid #e2e8f0; border-radius: 14px; overflow: hidden; }
.obs-body { padding: 14px 16px; display: flex; flex-direction: column; gap: 10px; }
.obs-textarea {
  width: 100%; border: 1.5px solid #e2e8f0; border-radius: 8px;
  padding: 10px 12px; font-size: 13px; color: #1e293b; resize: vertical;
  font-family: inherit; outline: none; transition: border-color .15s;
}
.obs-textarea:focus { border-color: #1e40af; }
.obs-footer { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
.obs-existente { font-size: 11.5px; color: #d97706; display: flex; align-items: center; gap: 4px; }
.btn-guardar-obs {
  background: #1e3a5f; color: #fff; border: none; border-radius: 8px;
  padding: 8px 18px; font-size: 13px; font-weight: 600; cursor: pointer;
  display: flex; align-items: center; transition: background .15s;
}
.btn-guardar-obs:hover:not(:disabled) { background: #1e40af; }
.btn-guardar-obs:disabled { opacity: .55; cursor: default; }
.obs-actual { border-top: 1px solid #f1f5f9; padding-top: 10px; }
.obs-actual label { font-size: 10.5px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: .4px; display: block; margin-bottom: 6px; }
.obs-pre { font-size: 12px; color: #475569; white-space: pre-wrap; word-break: break-word; margin: 0; background: #f8fafc; border-radius: 6px; padding: 8px 10px; font-family: inherit; }

/* Abonos tarjeta */
.tc-abono { border-color: #6ee7b7; }
.tc-abono .tc-header { background: #d1fae5; color: #065f46; }
.tc-abono .tc-header .bi { color: #059669; }
.tf-total td { padding: 8px 12px; font-size: 13px; background: #f0fdf4; border-top: 2px solid #6ee7b7; }

/* ── Layout 2 columnas ────────────────────────────────────────────────────── */
.layout-cols {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 18px;
  align-items: start;
}

/* ── Columna fotos ────────────────────────────────────────────────────────── */
.col-fotos {
  background: #fff; border: 1.5px solid #e2e8f0; border-radius: 14px;
  padding: 0; overflow: hidden; position: sticky; top: 16px;
}
.col-fotos > .seccion-titulo { padding: 12px 16px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; }
.fotos-grid { display: flex; flex-direction: column; gap: 8px; padding: 12px; }
.foto-item { position: relative; border-radius: 8px; overflow: hidden; border: 1.5px solid #e2e8f0; aspect-ratio: 4/3; }
.foto-item img { width: 100%; height: 100%; object-fit: cover; cursor: pointer; transition: opacity .15s; }
.foto-item img:hover { opacity: .85; }
.btn-del-foto {
  position: absolute; top: 4px; right: 4px;
  background: rgba(220,38,38,.85); color: #fff; border: none; border-radius: 5px;
  width: 26px; height: 26px; display: flex; align-items: center; justify-content: center;
  cursor: pointer; font-size: 12px;
}
.sin-fotos { font-size: 12.5px; color: #94a3b8; padding: 12px 16px; margin: 0; }
.foto-uploader { padding: 12px 16px; border-top: 1px solid #f1f5f9; }
.foto-uploader-label { font-size: 12px; font-weight: 600; color: #475569; margin: 0 0 8px; display: flex; align-items: center; gap: 5px; }
.foto-hint { font-size: 11.5px; color: #64748b; margin: 6px 0 0; }

/* ── Columna info ─────────────────────────────────────────────────────────── */
.col-info { display: flex; flex-direction: column; gap: 14px; }

/* ── Secciones ────────────────────────────────────────────────────────────── */
.seccion { background: #fff; border: 1.5px solid #e2e8f0; border-radius: 14px; overflow: hidden; }
.seccion-titulo {
  display: flex; align-items: center; gap: 7px;
  font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .5px;
  color: #475569; padding: 11px 16px; background: #f8fafc; border-bottom: 1px solid #e2e8f0;
}
.seccion-titulo .bi { color: #1e40af; font-size: 13px; }

/* ── Grid campos ──────────────────────────────────────────────────────────── */
.cc-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); padding: 14px 16px; gap: 4px; }
.cc-field { display: flex; flex-direction: column; gap: 2px; padding: 5px 6px; }
.cc-field--full { grid-column: 1 / -1; }
.cc-field label { font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: .4px; }
.cc-field span { font-size: 13px; color: #1e293b; font-weight: 500; }
.val-destacado { font-size: 15px !important; font-weight: 800 !important; color: #1e3a5f !important; }

/* ── Tabla ────────────────────────────────────────────────────────────────── */
.tabla-wrap { overflow-x: auto; }
.tabla-cv { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.tabla-cv thead tr { background: #f8fafc; }
.tabla-cv th { padding: 8px 12px; font-size: 10.5px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: .4px; border-bottom: 1px solid #e2e8f0; text-align: left; white-space: nowrap; }
.tabla-cv td { padding: 7px 12px; border-bottom: 1px solid #f1f5f9; color: #334155; }
.tabla-cv tbody tr:last-child td { border-bottom: none; }
.tabla-cv tbody tr:hover td { background: #f8fafc; }
.text-end { text-align: right !important; }

/* ── Tarjetas estado ──────────────────────────────────────────────────────── */
.tarjeta-estado { border-radius: 14px; overflow: hidden; border: 1.5px solid #e2e8f0; }
.tc-header {
  display: flex; align-items: center; gap: 8px;
  font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .5px;
  padding: 11px 16px;
}
.tc-badge {
  margin-left: auto; background: rgba(0,0,0,.1);
  border-radius: 20px; padding: 1px 8px; font-size: 11px;
}
.tc-body { padding: 0; background: #fff; }
.tc-vacio-msg {
  display: flex; align-items: center; gap: 8px;
  padding: 14px 16px; font-size: 13px; color: #94a3b8; background: #fff;
}

.tc-info { border-color: #bfdbfe; }
.tc-info .tc-header { background: #eff6ff; color: #1d4ed8; }
.tc-info .tc-header .bi { color: #3b82f6; }

.tc-retiro { border-color: #fde68a; }
.tc-retiro .tc-header { background: #fef3c7; color: #92400e; }
.tc-retiro .tc-header .bi { color: #d97706; }

.tc-remate { border-color: #fca5a5; }
.tc-remate .tc-header { background: #fee2e2; color: #991b1b; }
.tc-remate .tc-header .bi { color: #ef4444; }

.tc-vacio { border-color: #e2e8f0; }
.tc-vacio .tc-header { background: #f8fafc; color: #94a3b8; }

/* ── Lightbox ─────────────────────────────────────────────────────────────── */
.lightbox {
  position: fixed; inset: 0; background: rgba(0,0,0,.88); z-index: 2000;
  display: flex; align-items: center; justify-content: center; cursor: zoom-out;
}
.lightbox img { max-width: 90vw; max-height: 90vh; border-radius: 8px; }

/* ── Responsive ───────────────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .cv-consulta { padding: 14px 14px 50px; gap: 14px; }
  .layout-cols { grid-template-columns: 1fr; }
  .col-fotos { position: static; }
  .fotos-grid { flex-direction: row; flex-wrap: wrap; }
  .foto-item { width: 110px; height: 82px; }
  .search-line { flex-direction: column; }
  .search-sep { display: none; }
  .cliente-estado-row { flex-direction: column; }
  .estado-banner { flex-direction: row; min-width: unset; padding: 12px 16px; font-size: 16px; }
}
@media (max-width: 576px) {
  .cc-grid { grid-template-columns: 1fr 1fr; }
  .tabla-cv th, .tabla-cv td { padding: 6px 8px; font-size: 11.5px; }
  .foto-item { width: 90px; height: 68px; }
}
</style>
