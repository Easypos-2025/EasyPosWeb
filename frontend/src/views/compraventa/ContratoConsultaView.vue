<template>
  <div class="cv-consulta">

    <!-- Buscador -->
    <div class="search-bar">
      <i class="bi bi-search search-icon"></i>
      <input
        v-model="query"
        class="search-input"
        placeholder="Buscar por Nro. Contrato o Cédula..."
        @keyup.enter="buscar"
      />
      <button class="btn-buscar" @click="buscar" :disabled="loading || !query.trim()">
        <span v-if="loading" class="spinner-border spinner-border-sm"></span>
        <span v-else>Buscar</span>
      </button>
    </div>

    <!-- Error -->
    <div v-if="errorMsg" class="alerta-error">
      <i class="bi bi-exclamation-triangle-fill"></i> {{ errorMsg }}
    </div>

    <!-- Lista de resultados (cuando hay múltiples) -->
    <div v-if="!selectedIdx && resultados.length > 1" class="resultados-lista">
      <p class="resultados-titulo">{{ resultados.length }} contratos encontrados — selecciona uno:</p>
      <div v-for="(r, i) in resultados" :key="i" class="resultado-item" @click="selectedIdx = i">
        <div class="ri-nro">{{ r.contrato.nro_contrato }}</div>
        <div class="ri-info">
          Cédula: {{ r.contrato.cedula }} ·
          Inicio: {{ formatFecha(r.contrato.fecha_inicio) }} ·
          Valor: {{ formatCurrency(r.contrato.valor_contrato) }}
        </div>
        <span class="ri-estado" :class="estadoClass(r.contrato.estado)">
          {{ estadoLabel(r.contrato.estado) }}
        </span>
      </div>
    </div>

    <!-- Detalle del contrato -->
    <template v-if="detalle">

      <!-- Botón volver (si había múltiples) -->
      <button v-if="resultados.length > 1" class="btn-volver" @click="selectedIdx = null">
        <i class="bi bi-arrow-left"></i> Volver a resultados
      </button>

      <!-- === ENCABEZADO CONTRATO === -->
      <div class="card-contrato">
        <div class="card-contrato-header">
          <div>
            <span class="cc-nro">Contrato {{ detalle.contrato.nro_contrato }}</span>
            <span class="cc-cedula">Cédula: {{ detalle.contrato.cedula }}</span>
          </div>
          <span class="estado-badge" :class="estadoClass(detalle.contrato.estado)">
            <i class="bi" :class="estadoIcon(detalle.contrato.estado)"></i>
            {{ estadoLabel(detalle.contrato.estado) }}
          </span>
        </div>
        <div class="cc-grid">
          <div class="cc-field"><label>Fecha Inicio</label><span>{{ formatFecha(detalle.contrato.fecha_inicio) }}</span></div>
          <div class="cc-field"><label>Fecha Final</label><span>{{ formatFecha(detalle.contrato.fecha_final) }}</span></div>
          <div class="cc-field"><label>Meses</label><span>{{ detalle.contrato.nro_meses }}</span></div>
          <div class="cc-field"><label>Porcentaje</label><span>{{ detalle.contrato.porcentaje }}%</span></div>
          <div class="cc-field"><label>Valor Contrato</label><span class="val-destacado">{{ formatCurrency(detalle.contrato.valor_contrato) }}</span></div>
          <div class="cc-field"><label>Empleado</label><span>{{ detalle.contrato.cod_empleado }}</span></div>
          <div class="cc-field"><label>Hora Registro</label><span>{{ detalle.contrato.hora }}</span></div>
          <div class="cc-field"><label>Fecha Registro</label><span>{{ formatFecha(detalle.contrato.Fecha_Registro) }}</span></div>
          <div v-if="detalle.contrato.Observaciones" class="cc-field cc-field--full">
            <label>Observaciones</label><span>{{ detalle.contrato.Observaciones }}</span>
          </div>
        </div>
        <div class="cc-prorrogas-badge" v-if="detalle.prorrogas.length">
          <i class="bi bi-arrow-repeat"></i>
          {{ detalle.prorrogas.length }} prórroga{{ detalle.prorrogas.length > 1 ? 's' : '' }} registrada{{ detalle.prorrogas.length > 1 ? 's' : '' }}
        </div>
      </div>

      <!-- === ARTÍCULOS === -->
      <div class="seccion" v-if="detalle.articulos.length">
        <div class="seccion-titulo"><i class="bi bi-gem"></i> Artículos del Contrato</div>
        <div class="tabla-wrap">
          <table class="tabla-cv">
            <thead>
              <tr>
                <th>Categoría</th>
                <th>Item</th>
                <th>Detalle</th>
                <th>Kilate</th>
                <th class="text-end">Peso</th>
                <th class="text-end">Cantidad</th>
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

      <!-- === PRORROGAS === -->
      <div class="seccion" v-if="detalle.prorrogas.length">
        <div class="seccion-titulo"><i class="bi bi-arrow-repeat"></i> Prorrogas ({{ detalle.prorrogas.length }})</div>
        <div class="tabla-wrap">
          <table class="tabla-cv">
            <thead>
              <tr>
                <th>#</th>
                <th>Fecha</th>
                <th>Meses</th>
                <th class="text-end">Valor Prórroga</th>
                <th>Tipo</th>
                <th>Empleado</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(p, i) in detalle.prorrogas" :key="i">
                <td>{{ i + 1 }}</td>
                <td>{{ formatFecha(p.fecha_prorroga) }}</td>
                <td>{{ p.meses_prorrogados }}</td>
                <td class="text-end">{{ formatCurrency(p.valor_prorroga) }}</td>
                <td>{{ p.cod_tipo }}</td>
                <td>{{ p.Cod_Empleado }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- === RETIRO === -->
      <div class="seccion seccion--retiro" v-if="detalle.retiro">
        <div class="seccion-titulo"><i class="bi bi-box-arrow-left"></i> Información de Retiro</div>
        <div class="cc-grid">
          <div class="cc-field"><label>Fecha Retiro</label><span>{{ formatFecha(detalle.retiro.fecha_retiro) }}</span></div>
          <div class="cc-field"><label>Valor Retiro</label><span class="val-destacado">{{ formatCurrency(detalle.retiro.valor_retiro) }}</span></div>
          <div class="cc-field"><label>Sobre Costo</label><span>{{ formatCurrency(detalle.retiro.sobre_costo) }}</span></div>
          <div class="cc-field"><label>Descuento</label><span>{{ formatCurrency(detalle.retiro.descuento) }}</span></div>
          <div class="cc-field"><label>Tipo</label><span>{{ detalle.retiro.cod_tipo }}</span></div>
          <div class="cc-field"><label>Empleado</label><span>{{ detalle.retiro.Cod_Empleado }}</span></div>
          <div class="cc-field"><label>Autorizado</label><span>{{ detalle.retiro.Autorizado }}</span></div>
        </div>
      </div>

      <!-- === REMATE === -->
      <div class="seccion seccion--remate" v-if="detalle.remate">
        <div class="seccion-titulo"><i class="bi bi-hammer"></i> Información de Remate</div>
        <div class="cc-grid">
          <div class="cc-field"><label>Fecha Remate</label><span>{{ formatFecha(detalle.remate.fecha_remate) }}</span></div>
          <div class="cc-field"><label>Valor</label><span class="val-destacado">{{ formatCurrency(detalle.remate.valor_contrato) }}</span></div>
          <div class="cc-field"><label>Empleado</label><span>{{ detalle.remate.Cod_Empleado }}</span></div>
        </div>
      </div>

      <!-- === FOTOS === -->
      <div class="seccion">
        <div class="seccion-titulo"><i class="bi bi-images"></i> Fotos del Contrato</div>

        <!-- Grid fotos existentes -->
        <div class="fotos-grid" v-if="fotos.length">
          <div v-for="foto in fotos" :key="foto.id" class="foto-item">
            <img :src="fotoUrl(foto.url)" :alt="foto.name" @click="verFoto(foto)" />
            <button class="btn-del-foto" @click="eliminarFoto(foto)" title="Eliminar">
              <i class="bi bi-trash-fill"></i>
            </button>
          </div>
        </div>
        <p v-else class="sin-fotos">Sin fotos registradas para este contrato.</p>

        <!-- Uploader -->
        <div class="foto-uploader">
          <ImageUploaderPro
            :key="uploaderKey"
            label="Agregar foto"
            :showRemove="false"
            :outputWidth="1200"
            outputFormat="jpeg"
            :outputQuality="0.85"
            @change="onFotoChange"
          />
          <p class="foto-hint" v-if="uploading"><span class="spinner-border spinner-border-sm me-1"></span> Subiendo foto...</p>
        </div>
      </div>

      <!-- === IMPRIMIR / EXPORTAR === -->
      <div class="seccion">
        <div class="seccion-titulo"><i class="bi bi-printer"></i> Estado de Cuenta</div>
        <ExportToolbar
          :data="exportData"
          :columns="exportColumns"
          :filename="`contrato-${detalle.contrato.nro_contrato}`"
          :title="`Estado de Cuenta — Contrato ${detalle.contrato.nro_contrato}`"
        />
      </div>

    </template>

    <!-- Lightbox foto -->
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

const query       = ref('')
const loading     = ref(false)
const errorMsg    = ref('')
const resultados  = ref([])
const selectedIdx = ref(null)
const fotos       = ref([])
const uploading   = ref(false)
const uploaderKey = ref(0)
const fotoAmpliada = ref(null)

const detalle = computed(() => {
  if (resultados.value.length === 0) return null
  if (resultados.value.length === 1) return resultados.value[0]
  if (selectedIdx.value !== null)    return resultados.value[selectedIdx.value]
  return null
})

// ── Búsqueda ────────────────────────────────────────────────────────────────

async function buscar() {
  if (!query.value.trim() || !cid.value) return
  loading.value   = true
  errorMsg.value  = ''
  resultados.value = []
  selectedIdx.value = null
  fotos.value     = []
  try {
    const res = await api.get('/api/compraventa/contrato', {
      params: { company_id: cid.value, q: query.value.trim() }
    })
    resultados.value = res.data.contratos || []
    if (resultados.value.length === 0) errorMsg.value = 'No se encontraron contratos para esa búsqueda.'
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || 'Error al consultar'
  } finally {
    loading.value = false
  }
}

// ── Cargar fotos cuando cambia el detalle ────────────────────────────────────

watch(detalle, async (d) => {
  fotos.value = []
  if (!d || !cid.value) return
  try {
    const res = await api.get('/api/compraventa/contrato/fotos', {
      params: { company_id: cid.value, nro_contrato: d.contrato.nro_contrato }
    })
    fotos.value = res.data
  } catch {}
})

// ── Upload foto ───────────────────────────────────────────────────────────────

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

function verFoto(foto) { fotoAmpliada.value = foto }

function fotoUrl(url) {
  if (!url) return ''
  if (url.startsWith('http') || url.startsWith('blob:')) return url
  return (import.meta.env.VITE_API_URL || '') + url
}

// ── Helpers de formato ────────────────────────────────────────────────────────

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
  return e === 'V' ? 'estado-v' : e === 'R' ? 'estado-r' : e === 'D' ? 'estado-d' : ''
}

// ── Export / Impresión ────────────────────────────────────────────────────────

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

  rows.push({ _sectionHeader: true, _title: 'INFORMACIÓN DEL CONTRATO' })
  rows.push({ c1: 'Nro. Contrato', c2: contrato.nro_contrato, c3: 'Cédula', c4: contrato.cedula })
  rows.push({ c1: 'Fecha Inicio',  c2: formatFecha(contrato.fecha_inicio), c3: 'Fecha Final', c4: formatFecha(contrato.fecha_final) })
  rows.push({ c1: 'Meses',         c2: contrato.nro_meses, c3: 'Porcentaje', c4: `${contrato.porcentaje}%` })
  rows.push({ c1: 'Valor Contrato',c2: formatCurrency(contrato.valor_contrato), c3: 'Estado', c4: estadoLabel(contrato.estado) })
  rows.push({ c1: 'Empleado',      c2: contrato.cod_empleado, c3: 'Fecha Registro', c4: formatFecha(contrato.Fecha_Registro) })
  if (contrato.Observaciones) rows.push({ c1: 'Observaciones', c2: contrato.Observaciones, c3: '', c4: '' })

  if (articulos.length) {
    rows.push({ _sectionHeader: true, _title: 'ARTÍCULOS DEL CONTRATO' })
    rows.push({ c1: 'Categoría', c2: 'Item', c3: 'Detalle', c4: 'Kilate / Peso / Cant.' })
    for (const a of articulos) {
      rows.push({
        c1: a.cod_categoria,
        c2: a.Item_articulo,
        c3: a.detalle,
        c4: `${a.kilate || ''} / ${Number(a.peso).toFixed(1)} / ${a.Cantidad}`
      })
    }
  }

  if (prorrogas.length) {
    rows.push({ _sectionHeader: true, _title: `PRORROGAS (${prorrogas.length})` })
    rows.push({ c1: '#', c2: 'Fecha', c3: 'Meses', c4: 'Valor Prórroga' })
    prorrogas.forEach((p, i) => {
      rows.push({ c1: i + 1, c2: formatFecha(p.fecha_prorroga), c3: p.meses_prorrogados, c4: formatCurrency(p.valor_prorroga) })
    })
  }

  if (retiro) {
    rows.push({ _sectionHeader: true, _title: 'INFORMACIÓN DE RETIRO' })
    rows.push({ c1: 'Fecha Retiro', c2: formatFecha(retiro.fecha_retiro), c3: 'Valor Retiro', c4: formatCurrency(retiro.valor_retiro) })
    rows.push({ c1: 'Sobre Costo',  c2: formatCurrency(retiro.sobre_costo), c3: 'Descuento', c4: formatCurrency(retiro.descuento) })
  }

  if (remate) {
    rows.push({ _sectionHeader: true, _title: 'INFORMACIÓN DE REMATE' })
    rows.push({ c1: 'Fecha Remate', c2: formatFecha(remate.fecha_remate), c3: 'Valor', c4: formatCurrency(remate.valor_contrato) })
  }

  return rows
})
</script>

<style scoped>
.cv-consulta {
  max-width: 960px;
  margin: 0 auto;
  padding: 20px 20px 60px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Buscador */
.search-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fff;
  border: 1.5px solid #e2e8f0;
  border-radius: 12px;
  padding: 10px 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,.05);
}
.search-icon { font-size: 18px; color: #94a3b8; flex-shrink: 0; }
.search-input { flex: 1; border: none; outline: none; font-size: 15px; background: transparent; color: #1e293b; }
.search-input::placeholder { color: #94a3b8; }
.btn-buscar {
  background: #1e3a5f; color: #fff; border: none; border-radius: 8px;
  padding: 8px 20px; font-size: 13px; font-weight: 600; cursor: pointer;
  white-space: nowrap; transition: background .15s;
}
.btn-buscar:hover:not(:disabled) { background: #1e40af; }
.btn-buscar:disabled { opacity: .6; cursor: default; }

/* Error */
.alerta-error {
  background: #fee2e2; color: #dc2626; border: 1px solid #fca5a5;
  border-radius: 10px; padding: 12px 16px; font-size: 13.5px; font-weight: 500;
  display: flex; gap: 8px; align-items: center;
}

/* Lista resultados */
.resultados-titulo { font-size: 13px; color: #64748b; margin: 0 0 10px; font-weight: 600; }
.resultados-lista { display: flex; flex-direction: column; gap: 8px; }
.resultado-item {
  display: flex; align-items: center; gap: 12px;
  background: #fff; border: 1.5px solid #e2e8f0; border-radius: 10px;
  padding: 12px 16px; cursor: pointer; transition: border-color .15s, box-shadow .15s;
}
.resultado-item:hover { border-color: #1e40af; box-shadow: 0 2px 8px rgba(30,64,175,.12); }
.ri-nro { font-size: 15px; font-weight: 700; color: #1e3a5f; min-width: 80px; }
.ri-info { font-size: 12.5px; color: #64748b; flex: 1; }

/* Botón volver */
.btn-volver {
  display: inline-flex; align-items: center; gap: 6px;
  background: none; border: 1.5px solid #e2e8f0; border-radius: 8px;
  padding: 6px 14px; font-size: 13px; font-weight: 600; color: #475569;
  cursor: pointer; transition: border-color .15s;
}
.btn-volver:hover { border-color: #64748b; }

/* Estado badges */
.estado-badge, .ri-estado {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 11px; font-weight: 700; border-radius: 20px; padding: 3px 10px;
  text-transform: uppercase; letter-spacing: .5px; white-space: nowrap;
}
.estado-v { background: #dcfce7; color: #166534; }
.estado-r { background: #fef3c7; color: #92400e; }
.estado-d { background: #fee2e2; color: #991b1b; }

/* Card contrato */
.card-contrato {
  background: #fff; border: 1.5px solid #e2e8f0; border-radius: 14px;
  overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,.06);
}
.card-contrato-header {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  background: linear-gradient(135deg, #1e3a5f 0%, #1e40af 100%);
  padding: 16px 20px;
}
.cc-nro { font-size: 18px; font-weight: 800; color: #fff; display: block; }
.cc-cedula { font-size: 12px; color: #bfdbfe; }
.cc-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0; padding: 16px 20px;
}
.cc-field { display: flex; flex-direction: column; gap: 2px; padding: 6px 8px; }
.cc-field--full { grid-column: 1 / -1; }
.cc-field label { font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: .5px; }
.cc-field span { font-size: 13.5px; color: #1e293b; font-weight: 500; }
.val-destacado { font-size: 15px !important; font-weight: 800 !important; color: #1e3a5f !important; }
.cc-prorrogas-badge {
  display: flex; align-items: center; gap: 6px;
  margin: 0 20px 14px; padding: 8px 12px;
  background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px;
  font-size: 12.5px; font-weight: 600; color: #1d4ed8;
}

/* Secciones */
.seccion { background: #fff; border: 1.5px solid #e2e8f0; border-radius: 14px; overflow: hidden; }
.seccion-titulo {
  display: flex; align-items: center; gap: 8px;
  font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .5px;
  color: #475569; padding: 12px 18px;
  background: #f8fafc; border-bottom: 1px solid #e2e8f0;
}
.seccion-titulo .bi { color: #1e40af; font-size: 14px; }
.seccion--retiro .seccion-titulo .bi { color: #d97706; }
.seccion--remate .seccion-titulo .bi { color: #dc2626; }
.seccion--retiro { border-color: #fde68a; }
.seccion--remate { border-color: #fca5a5; }

/* Tabla */
.tabla-wrap { overflow-x: auto; }
.tabla-cv { width: 100%; border-collapse: collapse; font-size: 13px; }
.tabla-cv thead tr { background: #f8fafc; }
.tabla-cv th { padding: 9px 14px; font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: .4px; white-space: nowrap; border-bottom: 1px solid #e2e8f0; text-align: left; }
.tabla-cv td { padding: 8px 14px; border-bottom: 1px solid #f1f5f9; color: #334155; }
.tabla-cv tbody tr:last-child td { border-bottom: none; }
.tabla-cv tbody tr:hover td { background: #f8fafc; }
.text-end { text-align: right !important; }

/* Fotos */
.fotos-grid { display: flex; flex-wrap: wrap; gap: 10px; padding: 16px 18px 0; }
.foto-item { position: relative; width: 120px; height: 120px; border-radius: 10px; overflow: hidden; border: 1.5px solid #e2e8f0; }
.foto-item img { width: 100%; height: 100%; object-fit: cover; cursor: pointer; transition: opacity .15s; }
.foto-item img:hover { opacity: .85; }
.btn-del-foto {
  position: absolute; top: 4px; right: 4px;
  background: rgba(220,38,38,.85); color: #fff; border: none; border-radius: 5px;
  width: 24px; height: 24px; display: flex; align-items: center; justify-content: center;
  cursor: pointer; font-size: 11px;
}
.sin-fotos { font-size: 13px; color: #94a3b8; padding: 16px 18px; margin: 0; }
.foto-uploader { padding: 16px 18px; max-width: 260px; }
.foto-hint { font-size: 12px; color: #64748b; margin: 8px 0 0; }

/* Lightbox */
.lightbox {
  position: fixed; inset: 0; background: rgba(0,0,0,.85); z-index: 2000;
  display: flex; align-items: center; justify-content: center; cursor: zoom-out;
}
.lightbox img { max-width: 90vw; max-height: 90vh; border-radius: 8px; box-shadow: 0 20px 60px rgba(0,0,0,.5); }

/* Responsive */
@media (max-width: 768px) {
  .cv-consulta { padding: 14px 14px 50px; gap: 14px; }
  .cc-grid { grid-template-columns: repeat(2, 1fr); }
  .foto-item { width: 100px; height: 100px; }
}
@media (max-width: 576px) {
  .cc-grid { grid-template-columns: 1fr 1fr; }
  .tabla-cv th, .tabla-cv td { padding: 7px 10px; font-size: 12px; }
  .foto-item { width: 80px; height: 80px; }
  .search-bar { flex-wrap: wrap; }
  .btn-buscar { width: 100%; }
}
</style>
