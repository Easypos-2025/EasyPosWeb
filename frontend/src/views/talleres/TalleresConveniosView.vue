<template>
  <div class="convenios-wrap">

    <!-- ══ HEADER ══ -->
    <div class="page-header-row">
      <div class="ph-left">
        <h5 class="ph-title"><i class="bi bi-building-fill"></i> Convenios Empresariales</h5>
        <p class="ph-sub">Empresas con flota. Sus órdenes se acumulan y se facturan de forma consolidada.</p>
      </div>
      <button class="btn-nuevo" @click="abrirModal()">
        <i class="bi bi-plus-lg"></i> Nuevo Convenio
      </button>
    </div>

    <!-- ══ INDICADORES ══ -->
    <div class="kpi-row">
      <div class="kpi-card blue">
        <div class="kpi-val">{{ convenios.length }}</div>
        <div class="kpi-lbl">Convenios activos</div>
      </div>
      <div class="kpi-card amber">
        <div class="kpi-val">{{ totalOrdenesPendientes }}</div>
        <div class="kpi-lbl">Órdenes por facturar</div>
      </div>
      <div class="kpi-card green">
        <div class="kpi-val">{{ fmt(totalSaldoPendiente) }}</div>
        <div class="kpi-lbl">Saldo total pendiente</div>
      </div>
    </div>

    <!-- ══ LISTA DE CONVENIOS ══ -->
    <div v-if="loading" class="loading-center">
      <i class="bi bi-hourglass-split spin"></i> Cargando convenios...
    </div>

    <div v-else-if="convenios.length === 0" class="empty-state">
      <i class="bi bi-building-x"></i>
      <h6>Sin convenios registrados</h6>
      <p>Crea el primer convenio empresarial para empezar a acumular órdenes por cliente corporativo.</p>
      <button class="btn-nuevo" @click="abrirModal()">
        <i class="bi bi-plus-lg"></i> Crear primer convenio
      </button>
    </div>

    <div v-else class="convenios-grid">
      <div
        v-for="c in convenios" :key="c.id"
        :class="['convenio-card', { inactivo: !c.activo }]"
      >
        <div class="cc-header">
          <div class="cc-empresa">
            <div class="cc-avatar">{{ initials(c.nombre_empresa) }}</div>
            <div class="cc-empresa-info">
              <span class="cc-nombre">{{ c.nombre_empresa }}</span>
              <span v-if="c.nit_empresa" class="cc-nit">NIT: {{ c.nit_empresa }}</span>
            </div>
          </div>
          <div class="cc-badges">
            <span :class="['badge-periodi', c.periodicidad_facturacion]">
              {{ labelPeriodi(c.periodicidad_facturacion) }}
            </span>
            <span :class="['badge-activo', c.activo ? 'act' : 'inact']">
              {{ c.activo ? 'Activo' : 'Inactivo' }}
            </span>
          </div>
        </div>

        <div class="cc-body">
          <div class="cc-row" v-if="c.contacto_nombre">
            <i class="bi bi-person-fill"></i>
            <span>{{ c.contacto_nombre }}</span>
            <span v-if="c.contacto_telefono" class="cc-tel">
              · <i class="bi bi-telephone-fill"></i> {{ c.contacto_telefono }}
            </span>
          </div>
          <div class="cc-row" v-if="c.contacto_email">
            <i class="bi bi-envelope-fill"></i> {{ c.contacto_email }}
          </div>
          <div class="cc-row cond">
            <i class="bi bi-calendar-check-fill"></i>
            {{ labelCond(c.condicion_pago) }}
            <template v-if="c.dias_credito"> · {{ c.dias_credito }} días de crédito</template>
          </div>
          <div v-if="c.observaciones" class="cc-obs">
            <i class="bi bi-chat-left-text"></i> {{ c.observaciones }}
          </div>
        </div>

        <!-- Saldo pendiente -->
        <div :class="['cc-saldo', { 'has-saldo': c.saldo_pendiente > 0 }]">
          <div class="cs-left">
            <span class="cs-label">Por facturar</span>
            <span class="cs-ordenes">{{ c.ordenes_pendientes ?? 0 }} orden{{ (c.ordenes_pendientes ?? 0) !== 1 ? 'es' : '' }}</span>
          </div>
          <div class="cs-monto">{{ fmt(c.saldo_pendiente ?? 0) }}</div>
        </div>

        <!-- Acciones -->
        <div class="cc-actions">
          <button class="btn-act edit" @click="abrirModal(c)">
            <i class="bi bi-pencil-fill"></i> Editar
          </button>
          <button
            :class="['btn-act', c.activo ? 'deact' : 'act-btn']"
            @click="toggleActivo(c)"
            :disabled="toggling === c.id"
          >
            <i v-if="toggling === c.id" class="bi bi-hourglass-split spin"></i>
            <i v-else :class="c.activo ? 'bi bi-pause-circle' : 'bi bi-play-circle'"></i>
            {{ c.activo ? 'Desactivar' : 'Activar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ══ MODAL CREAR / EDITAR ══ -->
    <Teleport to="body">
      <div v-if="showModal" class="modal-overlay" @click.self="cerrarModal">
        <div class="modal-box">
          <div class="modal-head">
            <h6>
              <i class="bi bi-building-fill"></i>
              {{ editando ? 'Editar Convenio' : 'Nuevo Convenio Empresarial' }}
            </h6>
            <button class="btn-close-modal" @click="cerrarModal"><i class="bi bi-x-lg"></i></button>
          </div>
          <div class="modal-body">

            <div class="section-label">Datos de la empresa</div>
            <div class="form-row2">
              <div class="fg">
                <label>Nombre de la empresa *</label>
                <input v-model="form.nombre_empresa" class="form-inp" placeholder="Empresa S.A.S" />
              </div>
              <div class="fg">
                <label>NIT / CC / RUT</label>
                <input v-model="form.nit_empresa" class="form-inp" placeholder="900.123.456-7" />
              </div>
            </div>

            <div class="section-label">Contacto</div>
            <div class="form-row3">
              <div class="fg">
                <label>Nombre del contacto</label>
                <input v-model="form.contacto_nombre" class="form-inp" placeholder="Juan Pérez" />
              </div>
              <div class="fg">
                <label>Teléfono</label>
                <input v-model="form.contacto_telefono" class="form-inp" placeholder="300 000 0000" />
              </div>
              <div class="fg">
                <label>Email</label>
                <input v-model="form.contacto_email" type="email" class="form-inp" placeholder="contacto@empresa.com" />
              </div>
            </div>

            <div class="section-label">Condiciones comerciales</div>
            <div class="form-row3">
              <div class="fg">
                <label>Periodicidad de facturación</label>
                <select v-model="form.periodicidad_facturacion" class="form-inp form-sel">
                  <option value="semanal">Semanal</option>
                  <option value="quincenal">Quincenal</option>
                  <option value="mensual">Mensual</option>
                  <option value="por_solicitud">Por solicitud</option>
                </select>
              </div>
              <div class="fg">
                <label>Condición de pago</label>
                <select v-model="form.condicion_pago" class="form-inp form-sel">
                  <option value="credito">Crédito (plazo en días)</option>
                  <option value="contado_diferido">Contado diferido</option>
                </select>
              </div>
              <div class="fg">
                <label>Días de crédito</label>
                <input v-model.number="form.dias_credito" type="number" min="1" max="365" class="form-inp" />
              </div>
            </div>

            <div class="fg">
              <label>Observaciones / notas internas</label>
              <textarea v-model="form.observaciones" class="form-inp form-ta" rows="2" placeholder="Acuerdos especiales, contacto alterno, etc."></textarea>
            </div>

            <div class="info-box">
              <i class="bi bi-info-circle-fill"></i>
              Al crear una orden de servicio para un vehículo de esta empresa, selecciona este convenio.
              Las órdenes se acumularán en estado <strong>"Por facturar"</strong> hasta que generes la factura consolidada.
            </div>

          </div>
          <div class="modal-foot">
            <button class="btn-cancel" @click="cerrarModal">Cancelar</button>
            <button
              class="btn-save"
              :disabled="!puedeGuardar || saving"
              @click="guardar"
            >
              <i v-if="saving" class="bi bi-hourglass-split spin"></i>
              <i v-else class="bi bi-check-lg"></i>
              {{ editando ? 'Actualizar' : 'Crear Convenio' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Toast -->
    <Teleport to="body">
      <div v-if="toast.visible" :class="['toast-msg', `toast-${toast.tipo}`]">
        <i :class="toast.tipo === 'ok' ? 'bi bi-check-circle-fill' : 'bi bi-exclamation-triangle-fill'"></i>
        {{ toast.msg }}
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useCompanyStore } from '@/stores/companyStore'
import api from '@/services/apis'

const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id)

// ── Datos ─────────────────────────────────────────────────────────────────
const convenios = ref([])
const loading   = ref(false)

const totalOrdenesPendientes = computed(() =>
  convenios.value.reduce((s, c) => s + (c.ordenes_pendientes ?? 0), 0)
)
const totalSaldoPendiente = computed(() =>
  convenios.value.reduce((s, c) => s + (c.saldo_pendiente ?? 0), 0)
)

async function cargar() {
  if (!companyId.value) return
  loading.value = true
  try {
    const { data } = await api.get('/api/talleres/convenios', {
      params: { company_id: companyId.value }
    })
    convenios.value = data
  } catch { convenios.value = [] } finally { loading.value = false }
}

// ── Toggle activo ──────────────────────────────────────────────────────────
const toggling = ref(null)
async function toggleActivo(c) {
  toggling.value = c.id
  try {
    const nuevoVal = c.activo ? 0 : 1
    await api.patch(`/api/talleres/convenios/${c.id}/activo`, {
      company_id: companyId.value, activo: nuevoVal
    })
    c.activo = nuevoVal
    mostrarToast(`Convenio ${nuevoVal ? 'activado' : 'desactivado'}`, 'ok')
  } catch (e) {
    mostrarToast(e?.response?.data?.detail ?? 'Error', 'error')
  } finally { toggling.value = null }
}

// ── Modal ─────────────────────────────────────────────────────────────────
const showModal = ref(false)
const editando  = ref(null)
const saving    = ref(false)

const formDefault = () => ({
  nombre_empresa:           '',
  nit_empresa:              '',
  contacto_nombre:          '',
  contacto_telefono:        '',
  contacto_email:           '',
  periodicidad_facturacion: 'mensual',
  condicion_pago:           'credito',
  dias_credito:             30,
  observaciones:            '',
})
const form = ref(formDefault())

const puedeGuardar = computed(() => form.value.nombre_empresa.trim().length >= 2)

function abrirModal(convenio = null) {
  if (convenio) {
    editando.value = convenio.id
    form.value = {
      nombre_empresa:           convenio.nombre_empresa ?? '',
      nit_empresa:              convenio.nit_empresa ?? '',
      contacto_nombre:          convenio.contacto_nombre ?? '',
      contacto_telefono:        convenio.contacto_telefono ?? '',
      contacto_email:           convenio.contacto_email ?? '',
      periodicidad_facturacion: convenio.periodicidad_facturacion ?? 'mensual',
      condicion_pago:           convenio.condicion_pago ?? 'credito',
      dias_credito:             convenio.dias_credito ?? 30,
      observaciones:            convenio.observaciones ?? '',
    }
  } else {
    editando.value = null
    form.value = formDefault()
  }
  showModal.value = true
}

function cerrarModal() {
  showModal.value = false
  editando.value  = null
}

async function guardar() {
  if (!puedeGuardar.value) return
  saving.value = true
  const payload = { ...form.value, company_id: companyId.value }
  try {
    if (editando.value) {
      await api.put(`/api/talleres/convenios/${editando.value}`, payload)
      const idx = convenios.value.findIndex(x => x.id === editando.value)
      if (idx >= 0) Object.assign(convenios.value[idx], form.value)
      mostrarToast('Convenio actualizado', 'ok')
    } else {
      const { data } = await api.post('/api/talleres/convenios', payload)
      convenios.value.unshift({
        ...form.value, id: data.id, activo: 1,
        ordenes_pendientes: 0, saldo_pendiente: 0,
      })
      mostrarToast('Convenio creado exitosamente', 'ok')
    }
    cerrarModal()
  } catch (e) {
    mostrarToast(e?.response?.data?.detail ?? 'Error al guardar', 'error')
  } finally { saving.value = false }
}

// ── Helpers ───────────────────────────────────────────────────────────────
function initials(name) {
  return (name || '?').split(' ').slice(0, 2).map(s => s[0]).join('').toUpperCase()
}
function fmt(v) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v ?? 0)
}
function labelPeriodi(v) {
  const m = { semanal: 'Semanal', quincenal: 'Quincenal', mensual: 'Mensual', por_solicitud: 'Por solicitud' }
  return m[v] ?? v
}
function labelCond(v) {
  const m = { credito: 'Crédito', contado_diferido: 'Contado diferido' }
  return m[v] ?? v
}

const toast = ref({ visible: false, msg: '', tipo: 'ok' })
function mostrarToast(msg, tipo = 'ok') {
  toast.value = { visible: true, msg, tipo }
  setTimeout(() => { toast.value.visible = false }, 3500)
}

onMounted(cargar)
</script>

<style scoped>
.convenios-wrap { display: flex; flex-direction: column; gap: 20px; }

.page-header-row {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 16px; flex-wrap: wrap;
}
.ph-title { font-size: 18px; font-weight: 800; color: #1e3a5f; margin: 0; display: flex; align-items: center; gap: 8px; }
.ph-sub   { font-size: 13px; color: #64748b; margin: 4px 0 0; }
.btn-nuevo {
  display: flex; align-items: center; gap: 7px;
  background: #1e3a5f; color: #fff; border: none; border-radius: 10px;
  padding: 10px 20px; font-size: 13px; font-weight: 700; cursor: pointer; white-space: nowrap;
}
.btn-nuevo:hover { background: #2d4f80; }

.kpi-row { display: flex; gap: 12px; flex-wrap: wrap; }
.kpi-card { flex: 1; min-width: 120px; border-radius: 12px; padding: 14px 18px; border-left: 5px solid transparent; }
.kpi-card.blue  { background: #eff6ff; border-left-color: #3b82f6; }
.kpi-card.amber { background: #fffbeb; border-left-color: #f59e0b; }
.kpi-card.green { background: #f0fdf4; border-left-color: #22c55e; }
.kpi-val { font-size: 24px; font-weight: 800; color: #1e3a5f; }
.kpi-lbl { font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.4px; }

.loading-center { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 60px; color: #94a3b8; font-size: 14px; }

.empty-state {
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  padding: 60px 20px; text-align: center; background: #fff;
  border: 1.5px dashed #e2e8f0; border-radius: 14px;
}
.empty-state .bi { font-size: 48px; color: #cbd5e1; }
.empty-state h6  { font-size: 16px; font-weight: 700; color: #1e3a5f; margin: 0; }
.empty-state p   { font-size: 13px; color: #64748b; margin: 0; max-width: 360px; }

.convenios-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }

.convenio-card {
  background: #fff; border: 1.5px solid #e2e8f0; border-radius: 14px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05); overflow: hidden; transition: box-shadow .2s;
}
.convenio-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.10); }
.convenio-card.inactivo { opacity: .65; }

.cc-header {
  display: flex; align-items: flex-start; justify-content: space-between; gap: 10px;
  padding: 14px 16px 10px; border-bottom: 1px solid #f1f5f9;
}
.cc-empresa { display: flex; align-items: center; gap: 10px; }
.cc-avatar {
  width: 40px; height: 40px; border-radius: 10px; background: #1e3a5f; color: #fff;
  font-size: 16px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.cc-empresa-info { display: flex; flex-direction: column; gap: 2px; }
.cc-nombre { font-size: 14px; font-weight: 700; color: #1e3a5f; }
.cc-nit    { font-size: 11px; color: #94a3b8; }
.cc-badges { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; flex-shrink: 0; }
.badge-periodi { font-size: 10px; font-weight: 700; border-radius: 20px; padding: 2px 8px; background: #e0e7ff; color: #4338ca; }
.badge-activo.act  { background: #dcfce7; color: #15803d; font-size: 10px; font-weight: 700; border-radius: 20px; padding: 2px 8px; }
.badge-activo.inact{ background: #f1f5f9; color: #94a3b8; font-size: 10px; font-weight: 700; border-radius: 20px; padding: 2px 8px; }

.cc-body { padding: 12px 16px; display: flex; flex-direction: column; gap: 5px; }
.cc-row  { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #475569; }
.cc-row.cond { color: #64748b; }
.cc-tel  { color: #94a3b8; }
.cc-obs  { font-size: 12px; color: #94a3b8; display: flex; align-items: flex-start; gap: 6px; }

.cc-saldo {
  display: flex; align-items: center; justify-content: space-between; gap: 10px;
  margin: 0 16px 12px; padding: 10px 12px; border-radius: 10px;
  background: #f8fafc; border: 1px solid #e2e8f0;
}
.cc-saldo.has-saldo { background: #fffbeb; border-color: #fcd34d; }
.cs-left   { display: flex; flex-direction: column; gap: 1px; }
.cs-label  { font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.4px; }
.cs-ordenes{ font-size: 12px; color: #64748b; }
.cs-monto  { font-size: 18px; font-weight: 800; color: #1e3a5f; }
.has-saldo .cs-monto { color: #92400e; }

.cc-actions { display: flex; gap: 8px; padding: 0 16px 14px; }
.btn-act {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px;
  border: none; border-radius: 8px; padding: 7px 12px; font-size: 12px; font-weight: 700; cursor: pointer;
}
.btn-act.edit      { background: #eff6ff; color: #1d4ed8; }
.btn-act.edit:hover{ background: #dbeafe; }
.btn-act.deact     { background: #fef3c7; color: #92400e; }
.btn-act.deact:hover{ background: #fde68a; }
.btn-act.act-btn   { background: #f0fdf4; color: #15803d; }
.btn-act.act-btn:hover{ background: #dcfce7; }
.btn-act:disabled  { opacity: .5; cursor: default; }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 1000;
  display: flex; align-items: center; justify-content: center; padding: 20px;
}
.modal-box {
  background: #fff; border-radius: 16px; width: 100%; max-width: 680px;
  max-height: 90vh; overflow-y: auto; display: flex; flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
}
.modal-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 20px 14px; border-bottom: 1px solid #f1f5f9;
}
.modal-head h6 { margin: 0; font-size: 15px; font-weight: 700; color: #1e3a5f; display: flex; align-items: center; gap: 8px; }
.btn-close-modal {
  background: #f1f5f9; border: none; border-radius: 8px; width: 32px; height: 32px;
  cursor: pointer; color: #64748b; font-size: 14px; display: flex; align-items: center; justify-content: center;
}
.btn-close-modal:hover { background: #e2e8f0; color: #dc2626; }
.modal-body { padding: 18px 20px; display: flex; flex-direction: column; gap: 14px; flex: 1; }
.modal-foot { display: flex; justify-content: flex-end; gap: 10px; padding: 14px 20px; border-top: 1px solid #f1f5f9; }

.section-label { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #94a3b8; margin-bottom: -6px; }
.form-row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-row3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
.fg { display: flex; flex-direction: column; gap: 4px; }
.fg label { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.4px; }
.form-inp {
  border: 1.5px solid #e2e8f0; border-radius: 8px;
  padding: 9px 12px; font-size: 14px; color: #1e3a5f; outline: none; transition: border-color .2s;
}
.form-inp:focus { border-color: #1e3a5f; }
.form-sel { appearance: none; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%2364748b' stroke-width='1.5' fill='none'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 12px center; padding-right: 32px; cursor: pointer; }
.form-ta { resize: vertical; min-height: 60px; font-family: inherit; }

.info-box {
  display: flex; align-items: flex-start; gap: 8px;
  background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 10px;
  padding: 12px 14px; font-size: 13px; color: #1d4ed8;
}
.info-box .bi { color: #3b82f6; flex-shrink: 0; margin-top: 2px; }

.btn-cancel { background: #f1f5f9; border: none; border-radius: 8px; padding: 9px 20px; font-size: 13px; font-weight: 600; color: #64748b; cursor: pointer; }
.btn-cancel:hover { background: #e2e8f0; }
.btn-save {
  display: flex; align-items: center; gap: 7px;
  background: #1e3a5f; color: #fff; border: none; border-radius: 8px;
  padding: 9px 22px; font-size: 13px; font-weight: 700; cursor: pointer;
}
.btn-save:hover:not(:disabled) { background: #2d4f80; }
.btn-save:disabled { opacity: .5; cursor: default; }

.toast-msg {
  position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
  display: flex; align-items: center; gap: 8px; padding: 12px 20px;
  border-radius: 10px; font-size: 14px; font-weight: 600; z-index: 9999;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15); animation: slideInUp 0.3s ease;
}
.toast-ok    { background: #1e3a5f; color: #fff; }
.toast-error { background: #dc2626; color: #fff; }
@keyframes slideInUp { from { opacity: 0; transform: translateX(-50%) translateY(10px); } to { opacity: 1; transform: translateX(-50%) translateY(0); } }

.spin { display: inline-block; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 768px) {
  .convenios-grid { grid-template-columns: 1fr; }
  .form-row2 { grid-template-columns: 1fr; }
  .form-row3 { grid-template-columns: 1fr; }
}
@media (max-width: 576px) {
  .kpi-row { gap: 8px; }
  .kpi-val  { font-size: 20px; }
}
</style>
