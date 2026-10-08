<template>
  <!-- Registro Gastos · Registro Compras · Otros Ingresos · Otros Egresos (misma vista, el tipo sale de la ruta) -->
  <div class="mv-page">
    <div class="mv-head">
      <h2 class="mv-title"><i :class="['bi', icono, 'me-2']"></i>{{ moduleName || opc.titulo }}</h2>
      <TurnoIndicator />
    </div>

    <div v-if="opcCargadas && !opc.caja" class="mv-aviso">
      <i class="bi bi-exclamation-triangle"></i>
      <span>No hay un Id_Caja abierto: puede consultar, pero para registrar debe abrir o seleccionar la caja.</span>
      <button class="mv-btn mv-btn--warn" @click="pedirCaja = true"><i class="bi bi-safe2"></i> Caja</button>
    </div>

    <!-- ══ Barra ══ -->
    <div class="mv-bar">
      <PeriodoSelector v-model="per" :anteriores="!!opc.permisos.anteriores" :periodos="!!opc.permisos.periodos"
                       :hoy="opc.hoy" @change="cargar" />
      <div class="mv-bar-btns">
        <button class="mv-btn" :disabled="loading" title="Actualizar" @click="cargar"><i :class="['bi bi-arrow-clockwise', { spin: loading }]"></i></button>
        <button class="mv-btn" :disabled="!lista.rows.length" @click="imprimir"><i class="bi bi-printer"></i><span>Imprimir</span></button>
        <button class="mv-btn mv-btn--primary" :disabled="!opc.caja" :title="opc.caja ? '' : 'Debe abrir la caja'" @click="nuevo">
          <i class="bi bi-plus-lg"></i><span>Nuevo</span>
        </button>
      </div>
    </div>

    <div class="mv-totales">
      <span class="mv-chip">{{ lista.registros }} registros<template v-if="lista.registros > lista.rows.length"> (se listan {{ lista.rows.length }})</template></span>
      <span class="mv-chip mv-chip--total">Total <b>{{ fmt(lista.total) }}</b></span>
      <span v-if="lista.anulados" class="mv-chip mv-chip--off">{{ lista.anulados }} anulados</span>
    </div>

    <!-- ══ Listado ══ -->
    <div v-if="loading && !lista.rows.length" class="mv-state"><div class="spinner-border spinner-border-sm text-primary"></div></div>
    <div v-else-if="!lista.rows.length" class="mv-state mv-empty"><i :class="['bi', icono]"></i><p>Sin movimientos en el periodo.</p></div>
    <div v-else :class="['mv-list', { 'mv-loading': loading }]">
      <div v-for="r in lista.rows" :key="r.id" :class="['mv-row', { 'mv-row--off': r.anulado }]">
        <div class="mv-row-main">
          <div class="mv-row-top">
            <span class="mv-num">#{{ r.id }}</span>
            <span class="mv-fecha">{{ fmtFecha(r.fecha) }}</span>
            <span class="mv-tag">Id_Caja {{ r.id_caja }}</span>
            <span v-if="r.origen === 'escritorio'" class="mv-tag mv-tag--desk">escritorio</span>
            <span v-if="r.anulado" class="mv-tag mv-tag--off">ANULADO</span>
          </div>
          <div class="mv-concepto">{{ r.concepto || 'Sin concepto' }}<span v-if="r.subconcepto"> · {{ r.subconcepto }}</span></div>
          <div v-if="r.detalle" class="mv-det">{{ r.detalle }}</div>
          <div class="mv-meta">
            <span v-if="r.cajero"><i class="bi bi-person"></i> {{ r.cajero }}</span>
            <span v-if="r.formas"><i class="bi bi-credit-card"></i> {{ r.formas }}</span>
          </div>
          <div v-if="r.anulado && r.motivo" class="mv-motivo"><i class="bi bi-x-octagon"></i> {{ r.motivo }}</div>
        </div>
        <div class="mv-row-side">
          <b :class="['mv-valor', { 'mv-valor--off': r.anulado }]">{{ fmt(r.valor) }}</b>
          <button v-if="puedeAnular(r)" class="mv-anular" @click="pedirAnular(r)"><i class="bi bi-x-circle"></i> Anular</button>
        </div>
      </div>
    </div>

    <!-- ══ Modal: nuevo movimiento ══ -->
    <div v-if="form.show" class="mv-overlay" @click.self="form.show = false">
      <div class="mv-modal">
        <div class="mv-modal-h">
          <b><i :class="['bi', icono, 'me-1']"></i>Nuevo · {{ moduleName || opc.titulo }}</b>
          <button class="mv-x" @click="form.show = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="mv-modal-b">
          <div class="mv-caja-info"><i class="bi bi-safe2"></i> Id_Caja {{ opc.caja?.id }} · {{ opc.caja?.caja }} · {{ fmtFecha(opc.caja?.fecha) }}</div>

          <label class="mv-lbl">Concepto</label>
          <select v-model.number="form.concept_id" class="mv-inp" @change="form.sub_concept_id = 0">
            <option :value="0" disabled>Seleccione el concepto</option>
            <option v-for="c in $ordenAlfa(opc.conceptos, 'nombre')" :key="c.id" :value="c.id">{{ c.nombre }}</option>
          </select>
          <small v-if="!opc.conceptos.length" class="mv-help">No hay conceptos activos: créelos en Configuración → Conceptos de Caja.</small>

          <template v-if="subconceptos.length">
            <label class="mv-lbl">Subconcepto</label>
            <select v-model.number="form.sub_concept_id" class="mv-inp">
              <option :value="0">Ninguno</option>
              <option v-for="s in $ordenAlfa(subconceptos, 'nombre')" :key="s.id" :value="s.id">{{ s.nombre }}</option>
            </select>
          </template>

          <label class="mv-lbl">Valor</label>
          <CurrencyInput v-model="form.amount" class="mv-inp mv-inp--money" @update:model-value="onValor" />

          <label class="mv-lbl">Detalle</label>
          <textarea v-model="form.detail" class="mv-inp" rows="2" maxlength="255" placeholder="Descripción del movimiento"></textarea>

          <div class="mv-fp-head">
            <label class="mv-lbl mb-0">Formas de pago</label>
            <button class="mv-link" type="button" @click="agregarPago"><i class="bi bi-plus-circle"></i> Agregar</button>
          </div>
          <div v-for="(p, i) in form.pagos" :key="i" class="mv-fp">
            <select v-model.number="p.payment_method_id" class="mv-inp">
              <option v-for="fp in $ordenAlfa(opc.formas_pago, 'name')" :key="fp.id" :value="fp.id">{{ fp.name }}</option>
            </select>
            <CurrencyInput v-model="p.amount" class="mv-inp mv-inp--money" />
            <button v-if="form.pagos.length > 1" class="mv-x" type="button" @click="form.pagos.splice(i, 1)"><i class="bi bi-trash"></i></button>
            <input v-if="pideNota(p)" v-model="p.notes" class="mv-inp mv-fp-nota" maxlength="255" placeholder="Observación (obligatoria)" />
          </div>
          <div :class="['mv-cuadra', { 'mv-cuadra--bad': diferencia !== 0 }]">
            {{ diferencia === 0 ? 'Formas de pago completas' : diferencia > 0 ? `Falta asignar ${fmt(diferencia)}` : `Sobran ${fmt(-diferencia)}` }}
          </div>
        </div>
        <div class="mv-modal-f">
          <button class="mv-btn" @click="form.show = false">Cancelar</button>
          <button class="mv-btn mv-btn--primary" :disabled="!valido || form.saving" @click="guardar">
            <i :class="form.saving ? 'bi bi-arrow-repeat spin' : 'bi bi-check-lg'"></i> Registrar
          </button>
        </div>
      </div>
    </div>

    <!-- ══ Modal: anular ══ -->
    <div v-if="anu.row" class="mv-overlay" @click.self="anu.row = null">
      <div class="mv-modal mv-modal--sm">
        <div class="mv-modal-h"><b><i class="bi bi-x-circle me-1"></i>Anular movimiento #{{ anu.row.id }}</b><button class="mv-x" @click="anu.row = null"><i class="bi bi-x-lg"></i></button></div>
        <div class="mv-modal-b">
          <p class="mv-help">{{ anu.row.concepto }} · {{ fmt(anu.row.valor) }}. El movimiento no se elimina: queda anulado y deja de sumar en el Cuadre de Caja.</p>
          <label class="mv-lbl">Motivo</label>
          <textarea v-model="anu.reason" class="mv-inp" rows="3" maxlength="255" placeholder="¿Por qué se anula?"></textarea>
        </div>
        <div class="mv-modal-f">
          <button class="mv-btn" @click="anu.row = null">Cancelar</button>
          <button class="mv-btn mv-btn--danger" :disabled="anu.reason.trim().length < 3 || anu.saving" @click="anular">
            <i :class="anu.saving ? 'bi bi-arrow-repeat spin' : 'bi bi-x-circle'"></i> Anular
          </button>
        </div>
      </div>
    </div>

    <TurnoCajaModal v-if="pedirCaja" @opened="onCaja" />

    <ImprimirRecibo
      v-if="impresion"
      :receiptData="impresion"
      :companyId="companyId"
      printersPath="/api/pos/recibo-impresion/impresoras"
      :printPath="`${base}/imprimir`"
      :printExtra="{ periodo: per.periodo, fecha: per.fecha }"
      @close="impresion = null"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'
import { useModuleName } from '@/composables/useModuleName'
import { useCompanyStore } from '@/stores/companyStore'
import PeriodoSelector from '@/components/common/PeriodoSelector.vue'
import CurrencyInput from '@/components/CurrencyInput.vue'
import TurnoIndicator from '@/components/layout/TurnoIndicator.vue'
import TurnoCajaModal from '@/components/pos/TurnoCajaModal.vue'
import ImprimirRecibo from '@/components/billing/ImprimirRecibo.vue'

const route = useRoute()
const { moduleName } = useModuleName()
const companyStore = useCompanyStore()
const companyId = computed(() => Number(companyStore.selectedCompany?.id_company || companyStore.selectedCompany?.id || 0))

const tipo = computed(() => route.path.split('/').pop())
const base = computed(() => `/api/caja/movimientos/${tipo.value}`)
const icono = computed(() => route.meta.icon || 'bi-cash-stack')

const fmtMon = computed(() => new Intl.NumberFormat('es-CO', {
  style: 'currency', currency: companyStore.selectedCompany?.currency_code || 'COP', maximumFractionDigits: 0,
}))
const fmt = v => fmtMon.value.format(Math.round(Number(v) || 0))
const fmtFecha = f => (f ? `${String(f).slice(8, 10)}/${String(f).slice(5, 7)}/${String(f).slice(0, 4)}` : '')

const opc = ref({ titulo: '', conceptos: [], formas_pago: [], caja: null, permisos: {}, hoy: '' })
const opcCargadas = ref(false)
const per = ref({ periodo: 'dia', fecha: '' })
const lista = ref({ rows: [], registros: 0, total: 0, anulados: 0 })
const loading = ref(false)
const pedirCaja = ref(false)
const impresion = ref(null)
let seq = 0

async function cargarOpciones() {
  try {
    const { data } = await api.get(`${base.value}/opciones`)
    opc.value = data
    if (!per.value.fecha) per.value = { periodo: 'dia', fecha: data.hoy }
  } catch (e) {
    showToast(e?.response?.data?.detail || 'No se pudieron cargar las opciones', 'error')
  } finally {
    opcCargadas.value = true
  }
}

async function cargar() {
  const my = ++seq
  loading.value = true
  try {
    const { data } = await api.get(base.value, { params: { periodo: per.value.periodo, fecha: per.value.fecha || undefined } })
    if (my === seq) lista.value = data
  } catch (e) {
    if (my === seq) lista.value = { rows: [], registros: 0, total: 0, anulados: 0 }
    showToast(e?.response?.data?.detail || 'No se pudo consultar los movimientos', 'error')
  } finally {
    if (my === seq) loading.value = false
  }
}

async function iniciar() {
  per.value = { periodo: 'dia', fecha: '' }
  lista.value = { rows: [], registros: 0, total: 0, anulados: 0 }
  await cargarOpciones()
  await cargar()
}

async function onCaja() {
  pedirCaja.value = false
  await cargarOpciones()
}

// ── Nuevo movimiento ──
const form = reactive({ show: false, saving: false, concept_id: 0, sub_concept_id: 0, amount: 0, detail: '', pagos: [] })
const subconceptos = computed(() => opc.value.conceptos.find(c => c.id === form.concept_id)?.subconceptos || [])
const fpDefecto = () => (opc.value.formas_pago.find(f => f.es_efectivo) || opc.value.formas_pago.find(f => f.is_default) || opc.value.formas_pago[0])?.id
const pideNota = p => !!opc.value.formas_pago.find(f => f.id === p.payment_method_id)?.ask_notes
const diferencia = computed(() => Math.round(Number(form.amount) || 0) - form.pagos.reduce((a, p) => a + Math.round(Number(p.amount) || 0), 0))
const valido = computed(() => form.concept_id && Number(form.amount) > 0 && diferencia.value === 0
  && form.pagos.every(p => p.payment_method_id && (!pideNota(p) || (p.notes || '').trim())))

function nuevo() {
  if (!opc.value.caja) { pedirCaja.value = true; return }
  Object.assign(form, { show: true, saving: false, concept_id: 0, sub_concept_id: 0, amount: 0, detail: '',
                        pagos: [{ payment_method_id: fpDefecto(), amount: 0, notes: '' }] })
}
// Con una sola forma de pago, toma todo el valor (EFECTIVO por defecto)
function onValor(v) { if (form.pagos.length === 1) form.pagos[0].amount = Number(v) || 0 }
function agregarPago() {
  form.pagos.push({ payment_method_id: fpDefecto(), amount: Math.max(diferencia.value, 0), notes: '' })
}

async function guardar() {
  form.saving = true
  try {
    const { data } = await api.post(base.value, {
      concept_id: form.concept_id, sub_concept_id: form.sub_concept_id || 0, amount: Number(form.amount),
      detail: form.detail || null,
      payments: form.pagos.map(p => ({ payment_method_id: p.payment_method_id, amount: Number(p.amount) || 0, notes: p.notes || null })),
    })
    showToast(`Movimiento #${data.id} registrado en el Id_Caja ${data.id_caja}`, 'success')
    form.show = false
    await cargar()
  } catch (e) {
    showToast(e?.response?.data?.detail || 'No se pudo registrar el movimiento', 'error')
    if (e?.response?.status === 409) await cargarOpciones()
  } finally {
    form.saving = false
  }
}

// ── Anular ──
const anu = reactive({ row: null, reason: '', saving: false })
const puedeAnular = r => !r.anulado && r.origen === 'web' && r.caja_abierta && opc.value.permisos.anular
function pedirAnular(r) { Object.assign(anu, { row: r, reason: '', saving: false }) }
async function anular() {
  anu.saving = true
  try {
    await api.post(`${base.value}/${anu.row.id}/anular`, { reason: anu.reason.trim() })
    showToast(`Movimiento #${anu.row.id} anulado`, 'success')
    anu.row = null
    await cargar()
  } catch (e) {
    showToast(e?.response?.data?.detail || 'No se pudo anular', 'error')
  } finally {
    anu.saving = false
  }
}

// ── Imprimir (vista previa, tirilla, PDF, Excel) ──
function imprimir() {
  const l = lista.value
  const rango = l.desde === l.hasta ? fmtFecha(l.desde) : `${fmtFecha(l.desde)} al ${fmtFecha(l.hasta)}`
  const tot = [{ label: 'Registros', valor: null, cant: l.registros }]
  if (l.anulados) tot.push({ label: 'Anulados', valor: null, cant: l.anulados })
  tot.push({ label: 'TOTAL', valor: l.total, bold: true })
  impresion.value = {
    titulo: (moduleName.value || l.titulo || '').toUpperCase(), receipt_number: '', fecha: rango, lineas: [],
    secciones: [
      { titulo: 'Movimientos', items: l.rows.map(r => ({
          label: `#${r.id} ${fmtFecha(r.fecha).slice(0, 5)} ${r.concepto}${r.subconcepto ? ' · ' + r.subconcepto : ''}${r.anulado ? ' (ANULADO)' : ''}`,
          valor: r.anulado ? null : r.valor, cant: r.anulado ? 'ANULADO' : undefined })) },
      { titulo: 'Totales', items: tot },
    ],
    items: [], pagos: [],
  }
}

watch(() => route.path, p => { if (p.startsWith('/caja/')) iniciar() })
onMounted(iniciar)
</script>

<style scoped>
.mv-page { padding: 20px 24px 32px; }
.mv-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 14px; }
.mv-title { font-size: 22px; font-weight: 800; color: #1e293b; margin: 0; }
.mv-aviso { display: flex; align-items: center; gap: 10px; background: #fffbeb; border: 1.5px solid #fcd34d; color: #92400e;
            border-radius: 12px; padding: 10px 14px; margin-bottom: 12px; font-size: 14px; }
.mv-aviso > i { font-size: 18px; }
.mv-aviso > span { flex: 1; }
.mv-bar { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap;
          background: #fff; border: 1.5px solid #e2e8f0; border-radius: 14px; padding: 10px 12px; }
.mv-bar-btns { display: flex; gap: 8px; }
.mv-btn { display: inline-flex; align-items: center; gap: 6px; border: 1.5px solid #e2e8f0; background: #fff; color: #334155;
          border-radius: 10px; padding: 7px 14px; font-size: 14px; font-weight: 700; cursor: pointer; }
.mv-btn:disabled { opacity: .5; cursor: not-allowed; }
.mv-btn--primary { background: #2563eb; border-color: #2563eb; color: #fff; }
.mv-btn--danger { background: #dc2626; border-color: #dc2626; color: #fff; }
.mv-btn--warn { background: #f59e0b; border-color: #f59e0b; color: #fff; }
.mv-totales { display: flex; gap: 8px; flex-wrap: wrap; margin: 12px 0; }
.mv-chip { background: #f1f5f9; color: #475569; border-radius: 999px; padding: 5px 12px; font-size: 13px; font-weight: 600; }
.mv-chip--total { background: #dcfce7; color: #166534; }
.mv-chip--off { background: #fee2e2; color: #991b1b; }
.mv-state { display: flex; flex-direction: column; align-items: center; padding: 50px 16px; color: #64748b; }
.mv-empty i { font-size: 38px; color: #cbd5e1; }
.mv-empty p { margin: 8px 0 0; font-weight: 600; }
.mv-list { display: flex; flex-direction: column; gap: 8px; }
.mv-loading { opacity: .6; }
.mv-row { display: flex; gap: 12px; background: #fff; border: 1.5px solid #e2e8f0; border-radius: 12px; padding: 12px 14px; }
.mv-row--off { background: #f8fafc; }
.mv-row-main { flex: 1; min-width: 0; }
.mv-row-top { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; font-size: 12px; }
.mv-num { font-weight: 800; color: #1d4ed8; }
.mv-fecha { color: #64748b; }
.mv-tag { background: #eef2ff; color: #3730a3; border-radius: 6px; padding: 1px 7px; font-weight: 700; }
.mv-tag--desk { background: #f1f5f9; color: #475569; }
.mv-tag--off { background: #fee2e2; color: #b91c1c; }
.mv-concepto { font-weight: 700; color: #1e293b; margin-top: 4px; }
.mv-det { color: #475569; font-size: 13px; margin-top: 2px; word-break: break-word; }
.mv-meta { display: flex; gap: 12px; flex-wrap: wrap; color: #64748b; font-size: 12px; margin-top: 4px; }
.mv-motivo { color: #b91c1c; font-size: 12px; margin-top: 4px; }
.mv-row-side { display: flex; flex-direction: column; align-items: flex-end; justify-content: space-between; gap: 8px; }
.mv-valor { font-size: 16px; color: #0f172a; white-space: nowrap; }
.mv-valor--off { text-decoration: line-through; color: #94a3b8; }
.mv-anular { border: none; background: none; color: #dc2626; font-size: 13px; font-weight: 700; cursor: pointer; padding: 0; }
.mv-overlay { position: fixed; inset: 0; background: rgba(15, 23, 42, .5); display: flex; align-items: center; justify-content: center; z-index: 1050; padding: 16px; }
.mv-modal { background: #fff; border-radius: 16px; width: 100%; max-width: 520px; max-height: 92vh; display: flex; flex-direction: column; }
.mv-modal--sm { max-width: 420px; }
.mv-modal-h, .mv-modal-f { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 14px 16px; }
.mv-modal-h { border-bottom: 1px solid #e2e8f0; }
.mv-modal-f { border-top: 1px solid #e2e8f0; justify-content: flex-end; }
.mv-modal-b { padding: 14px 16px; overflow-y: auto; }
.mv-x { border: none; background: none; color: #64748b; font-size: 16px; cursor: pointer; padding: 4px 6px; }
.mv-caja-info { background: #eff6ff; color: #1e40af; border-radius: 10px; padding: 8px 12px; font-size: 13px; font-weight: 600; margin-bottom: 6px; }
.mv-lbl { display: block; font-size: 13px; font-weight: 700; color: #334155; margin: 10px 0 4px; }
.mv-inp { width: 100%; border: 1.5px solid #e2e8f0; border-radius: 10px; padding: 8px 10px; font-size: 14px; background: #fff; }
.mv-inp--money { text-align: right; font-weight: 700; }
.mv-help { color: #64748b; font-size: 12px; }
.mv-fp-head { display: flex; align-items: center; justify-content: space-between; margin-top: 12px; }
.mv-link { border: none; background: none; color: #2563eb; font-weight: 700; font-size: 13px; cursor: pointer; }
.mv-fp { display: grid; grid-template-columns: 1fr 140px auto; gap: 6px; align-items: center; margin-top: 6px; }
.mv-fp-nota { grid-column: 1 / -1; }
.mv-cuadra { margin-top: 8px; font-size: 13px; font-weight: 700; color: #166534; }
.mv-cuadra--bad { color: #b91c1c; }
.spin { animation: mv-spin 1s linear infinite; display: inline-block; }
@keyframes mv-spin { to { transform: rotate(360deg); } }

@media (max-width: 1024px) {
  .mv-page { padding: 18px 16px 28px; }
}
@media (max-width: 768px) {
  .mv-page { padding: 14px 12px 24px; }
  .mv-title { font-size: 19px; }
  .mv-bar { flex-direction: column; align-items: stretch; }
  .mv-bar-btns { justify-content: flex-end; }
  .mv-aviso { flex-wrap: wrap; }
}
@media (max-width: 576px) {
  .mv-bar-btns .mv-btn { flex: 1; justify-content: center; }
  .mv-bar-btns .mv-btn span { display: none; }
  .mv-row { flex-direction: column; gap: 6px; }
  .mv-row-side { flex-direction: row; align-items: center; }
  .mv-fp { grid-template-columns: 1fr 110px auto; }
  .mv-overlay { padding: 0; align-items: flex-end; }
  .mv-modal { border-radius: 16px 16px 0 0; max-height: 95vh; }
}
</style>
