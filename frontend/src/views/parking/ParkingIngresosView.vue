<template>
  <div class="pk-page">

    <!-- ══ KPI BAR ══════════════════════════════════════════════════════════ -->
    <div class="pk-kpi-bar">
      <button class="pk-btn-nuevo" @click="abrirModalNuevo">
        <i class="bi bi-plus-circle-fill"></i>
        <span>Nuevo Ingreso</span>
      </button>
      <div class="pk-kpi-card pk-kpi-disponibles">
        <i class="bi bi-p-circle-fill"></i>
        <div>
          <span class="pk-kpi-val">{{ stats.disponibles }}</span>
          <span class="pk-kpi-lbl">Disponibles</span>
        </div>
      </div>
      <div class="pk-kpi-card pk-kpi-ocupadas">
        <i class="bi bi-car-front-fill"></i>
        <div>
          <span class="pk-kpi-val">{{ stats.ocupadas }}</span>
          <span class="pk-kpi-lbl">Ocupadas</span>
        </div>
      </div>
      <div class="pk-kpi-card pk-kpi-total">
        <i class="bi bi-grid-3x3-gap-fill"></i>
        <div>
          <span class="pk-kpi-val">{{ stats.total_plazas }}</span>
          <span class="pk-kpi-lbl">Total · {{ stats.pct_ocupacion }}%</span>
        </div>
      </div>
    </div>

    <!-- ══ BARRA DE BÚSQUEDA ════════════════════════════════════════════════ -->
    <div class="pk-search-bar">
      <div class="pk-search-group">
        <i class="bi bi-hash pk-search-icon"></i>
        <input v-model="busId" type="number" class="pk-search-input" placeholder="Nro Recibo"
               @keydown.enter="aplicarBusqueda" />
      </div>
      <div class="pk-search-group">
        <i class="bi bi-car-front-fill pk-search-icon"></i>
        <input v-model="busPlaca" class="pk-search-input" placeholder="Placa"
               @input="busPlaca = busPlaca.toUpperCase()" @keydown.enter="aplicarBusqueda" />
      </div>
      <div class="pk-search-group">
        <i class="bi bi-qr-code-scan pk-search-icon"></i>
        <input v-model="busQR" class="pk-search-input" placeholder="Código QR / Token"
               @keydown.enter="aplicarBusqueda" />
      </div>
      <button class="pk-btn-buscar" @click="aplicarBusqueda"><i class="bi bi-search"></i></button>
      <button v-if="busId || busPlaca || busQR" class="pk-btn-clear" @click="limpiarBusqueda">
        <i class="bi bi-x-lg"></i>
      </button>
    </div>

    <!-- ══ FILTRO FECHA ══════════════════════════════════════════════════════ -->
    <div class="pk-filtro-bar">
      <div class="pk-filtro-fecha">
        <CustomDatePicker v-model="fechaFiltro" @update:modelValue="cargar" />
      </div>
      <div class="pk-filtros-estado">
        <button v-for="f in FILTROS" :key="f.val"
          :class="['pk-flt', { active: filtroEstado === f.val }]"
          @click="filtroEstado = f.val; cargar()">
          {{ f.label }}
        </button>
      </div>
    </div>

    <!-- ══ GRID DE TARJETAS ══════════════════════════════════════════════════ -->
    <div v-if="loading" class="pk-loading">
      <i class="bi bi-arrow-repeat spin"></i> Cargando…
    </div>
    <div v-else-if="ordenes.length === 0" class="pk-empty">
      <i class="bi bi-car-front"></i>
      <p>No hay ingresos para esta fecha</p>
    </div>
    <div v-else class="pk-grid">
      <ParkingOrderCard
        v-for="o in ordenesFiltradas" :key="o.id"
        :orden="o"
        mode="portero"
        @card-click="onClickCard"
        @reprint="abrirReimpresion"
      />
    </div>

  </div>

  <!-- ══ MODAL NUEVO INGRESO ═══════════════════════════════════════════════ -->
  <Teleport to="body">
    <div v-if="showModalNuevo" class="pk-modal-overlay" @click.self="cerrarModalNuevo">
      <div class="pk-modal">
        <div class="pk-modal-head">
          <span><i class="bi bi-car-front-fill"></i> Nuevo Ingreso</span>
          <button class="pk-modal-close" @click="cerrarModalNuevo"><i class="bi bi-x-lg"></i></button>
        </div>

        <div class="pk-modal-body">
          <!-- Placa -->
          <div class="pk-field pk-field--required">
            <label>Placa <span class="req">*</span></label>
            <div class="pk-placa-wrap">
              <input v-model="form.placa" class="pk-input pk-placa-input"
                placeholder="Ej: ABC123" maxlength="10" autocomplete="off"
                @input="form.placa = form.placa.toUpperCase(); buscarPlaca()" />
              <span v-if="buscandoPlaca" class="pk-placa-hint pk-placa-buscando">
                <i class="bi bi-arrow-repeat spin"></i> Buscando…
              </span>
              <span v-else-if="vehicleFound" class="pk-placa-hint pk-placa-ok">
                <i class="bi bi-check-circle-fill"></i> Vehículo encontrado
              </span>
            </div>
          </div>

          <!-- Tipo vehículo — read-only si el vehículo ya fue encontrado -->
          <div v-if="vehicleFound && form.vehicle_type_id" class="pk-field">
            <label>Tipo de Vehículo</label>
            <div class="pk-vtype-found">
              <template v-for="t in vehicleTypes" :key="t.id">
                <span v-if="t.id === form.vehicle_type_id" class="pk-vtype-found-badge">
                  <i :class="`bi ${t.icono || 'bi-car-front-fill'}`"></i>
                  {{ t.nombre }}
                  <span class="pk-vtype-found-lock"><i class="bi bi-lock-fill"></i></span>
                </span>
              </template>
            </div>
          </div>

          <!-- Tipo vehículo — seleccionable si vehículo nuevo -->
          <div v-else-if="vehicleTypes.length && !vehicleFound" class="pk-field">
            <label>Tipo de Vehículo</label>
            <div class="pk-vtype-grid">
              <button
                v-for="t in vehicleTypes" :key="t.id" type="button"
                :class="['pk-vtype-card', { 'pk-vtype-selected': form.vehicle_type_id === t.id }]"
                @click="form.vehicle_type_id = t.id"
              >
                <i :class="`bi ${t.icono || 'bi-car-front-fill'}`"></i>
                <span>{{ t.nombre }}</span>
              </button>
            </div>
          </div>

          <!-- Hora ingreso -->
          <div class="pk-field pk-field--required">
            <label>Hora de Ingreso <span class="req">*</span></label>
            <input v-model="form.hora_ingreso" type="datetime-local" class="pk-input" />
          </div>

          <!-- Personas -->
          <div class="pk-personas-row">
            <div class="pk-field pk-field--required pk-field--num">
              <label><i class="bi bi-person-fill"></i> Adultos <span class="req">*</span></label>
              <div class="pk-counter">
                <button type="button" @click="form.adultos = Math.max(1, form.adultos - 1)">−</button>
                <span>{{ form.adultos }}</span>
                <button type="button" @click="form.adultos++">+</button>
              </div>
            </div>
            <div class="pk-field pk-field--num">
              <label><i class="bi bi-person-hearts"></i> Niños</label>
              <div class="pk-counter">
                <button type="button" @click="form.ninos = Math.max(0, form.ninos - 1)">−</button>
                <span>{{ form.ninos }}</span>
                <button type="button" @click="form.ninos++">+</button>
              </div>
            </div>
            <div class="pk-field pk-field--num">
              <label><i class="bi bi-circle-fill" style="font-size:.7rem"></i> Mascotas</label>
              <div class="pk-counter">
                <button type="button" @click="form.mascotas = Math.max(0, form.mascotas - 1)">−</button>
                <span>{{ form.mascotas }}</span>
                <button type="button" @click="form.mascotas++">+</button>
              </div>
            </div>
          </div>

          <!-- Foto -->
          <div class="pk-field">
            <label>Foto del Vehículo
              <span v-if="vehicleFound && form.foto_url" class="pk-foto-label-hint">
                <i class="bi bi-check-circle-fill" style="color:#198754"></i> foto registrada
              </span>
            </label>
            <div class="pk-foto-area">
              <img v-if="form.foto_url" :src="form.foto_url" class="pk-foto-preview" alt="Foto vehículo" />
              <div v-else class="pk-foto-placeholder">
                <i class="bi bi-camera"></i>
                <span>Sin foto</span>
              </div>
              <div class="pk-foto-btns">
                <label class="pk-btn-foto">
                  <i class="bi bi-camera-fill"></i> Tomar / Subir
                  <input type="file" accept="image/*" capture="environment"
                    style="display:none" @change="onFotoChange" />
                </label>
                <button v-if="form.foto_url" type="button" class="pk-btn-foto-rm"
                  @click="form.foto_url = null">
                  <i class="bi bi-trash"></i>
                </button>
              </div>
            </div>
          </div>

          <!-- Observaciones portero -->
          <div class="pk-field">
            <label>Observaciones</label>
            <textarea v-model="form.obs_portero" class="pk-input" rows="2"
              placeholder="Daños visibles, notas de ingreso…"></textarea>
          </div>
        </div>

        <div class="pk-modal-footer">
          <button class="pk-btn-cancel" @click="cerrarModalNuevo">Cancelar</button>
          <button class="pk-btn-guardar" :disabled="guardando" @click="guardarNuevo">
            <i v-if="guardando" class="bi bi-arrow-repeat spin"></i>
            <i v-else class="bi bi-check-lg"></i>
            {{ guardando ? 'Guardando…' : 'Registrar Ingreso' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- ══ MODAL MESERO: confirmar personas ══════════════════════════════════ -->
  <Teleport to="body">
    <div v-if="showModalMesero" class="pk-modal-overlay" @click.self="showModalMesero = false">
      <div class="pk-modal pk-modal--mesero">
        <div class="pk-modal-head">
          <span><i class="bi bi-people-fill"></i> Confirmar Personas</span>
          <button class="pk-modal-close" @click="showModalMesero = false"><i class="bi bi-x-lg"></i></button>
        </div>

        <div class="pk-modal-body" v-if="ordenSeleccionada">
          <!-- Foto del vehículo -->
          <div v-if="ordenSeleccionada.foto_url" class="pk-modal-foto">
            <img :src="ordenSeleccionada.foto_url" alt="Foto vehículo" class="pk-modal-foto-img" />
          </div>
          <div class="pk-ord-placa-big">{{ ordenSeleccionada.placa }}</div>
          <p class="pk-ord-sub">
            <strong>#{{ ordenSeleccionada.id }}</strong> · {{ ordenSeleccionada.numero_orden }} · {{ fmtHora(ordenSeleccionada.hora_ingreso) }}
          </p>
          <p class="pk-obs-portero-label" v-if="ordenSeleccionada.obs_portero">
            <i class="bi bi-info-circle"></i> Obs. portero: {{ ordenSeleccionada.obs_portero }}
          </p>

          <div class="pk-personas-row">
            <div class="pk-field pk-field--required pk-field--num">
              <label><i class="bi bi-person-fill"></i> Adultos <span class="req">*</span></label>
              <div class="pk-counter">
                <button type="button" @click="formMesero.adultos = Math.max(1, formMesero.adultos - 1)">−</button>
                <span>{{ formMesero.adultos }}</span>
                <button type="button" @click="formMesero.adultos++">+</button>
              </div>
            </div>
            <div class="pk-field pk-field--num">
              <label><i class="bi bi-person-hearts"></i> Niños</label>
              <div class="pk-counter">
                <button type="button" @click="formMesero.ninos = Math.max(0, formMesero.ninos - 1)">−</button>
                <span>{{ formMesero.ninos }}</span>
                <button type="button" @click="formMesero.ninos++">+</button>
              </div>
            </div>
            <div class="pk-field pk-field--num">
              <label><i class="bi bi-circle-fill" style="font-size:.7rem"></i> Mascotas</label>
              <div class="pk-counter">
                <button type="button" @click="formMesero.mascotas = Math.max(0, formMesero.mascotas - 1)">−</button>
                <span>{{ formMesero.mascotas }}</span>
                <button type="button" @click="formMesero.mascotas++">+</button>
              </div>
            </div>
          </div>

          <div class="pk-field">
            <label>Observaciones adicionales</label>
            <textarea v-model="formMesero.obs_mesero" class="pk-input" rows="2"
              placeholder="Notas del mesero (no reemplaza la del portero)…"></textarea>
          </div>
        </div>

        <div class="pk-modal-footer">
          <button class="pk-btn-cancel" @click="showModalMesero = false">Cancelar</button>
          <button class="pk-btn-guardar pk-btn-registrar" :disabled="confirmando" @click="confirmarMesero">
            <i v-if="confirmando" class="bi bi-arrow-repeat spin"></i>
            <i v-else class="bi bi-check2-all"></i>
            {{ confirmando ? 'Confirmando…' : 'Confirmar y Enviar a Caja' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- ══ COMPROBANTE DE IMPRESIÓN ══════════════════════════════════════════ -->
  <ComprobanteParkingIngreso
    v-if="ordenParaImprimir"
    :orden="ordenParaImprimir"
    :company-name="companyStore.selectedCompany?.name || ''"
    :company-id="companyStore.selectedCompany?.id"
    tipo="ingreso"
    @close="ordenParaImprimir = null"
  />
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'
import { useCompanyStore } from '@/stores/companyStore'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'
import ComprobanteParkingIngreso from '@/components/parking/ComprobanteParkingIngreso.vue'
import ParkingOrderCard from '@/components/parking/ParkingOrderCard.vue'

const companyStore = useCompanyStore()
const companyId = computed(() => companyStore.selectedCompany?.id)

const FILTROS = [
  { val: 'activos',    label: 'Activos' },
  { val: 'ingresado',  label: 'Ingresados' },
  { val: 'registrado', label: 'Confirmados' },
  { val: 'todos',      label: 'Todos' },
]

const LABELS_ESTADO = {
  ingresado:  'Ingresado',
  registrado: 'Confirmado',
  pagado:     'Pagado',
  cancelado:  'Cancelado',
}

// ── Estado ────────────────────────────────────────────────────────────────────
const ordenes          = ref([])
const stats            = ref({ disponibles: 0, ocupadas: 0, total_plazas: 0, pct_ocupacion: 0 })
const vehicleTypes     = ref([])
const loading          = ref(false)
const fechaFiltro      = ref(new Date().toISOString().slice(0, 10))
const filtroEstado     = ref('activos')

const showModalNuevo   = ref(false)
const guardando        = ref(false)
const ordenParaImprimir = ref(null)

const showModalMesero  = ref(false)
const confirmando      = ref(false)
const ordenSeleccionada = ref(null)

// Búsqueda
const busId    = ref('')
const busPlaca = ref('')
const busQR    = ref('')
const busActivo = ref({ id: '', placa: '', qr: '' })

const ordenesFiltradas = computed(() => {
  const { id, placa, qr } = busActivo.value
  if (!id && !placa && !qr) return ordenes.value
  return ordenes.value.filter(o => {
    if (id && String(o.id) !== id.trim()) return false
    if (placa && !o.placa?.includes(placa.trim().toUpperCase())) return false
    if (qr && !o.numero_orden?.toUpperCase().includes(qr.trim().toUpperCase())) return false
    return true
  })
})

const buscandoPlaca = ref(false)
const vehicleFound  = ref(false)
let _placaTimer = null

const form = ref({
  placa:           '',
  vehicle_type_id: null,
  hora_ingreso:    '',
  adultos:         1,
  ninos:           0,
  mascotas:        0,
  foto_url:        null,
  obs_portero:     '',
})

const formMesero = ref({ adultos: 1, ninos: 0, mascotas: 0, obs_mesero: '' })

// ── Carga ─────────────────────────────────────────────────────────────────────
async function cargar() {
  if (!companyId.value) return
  loading.value = true
  try {
    const estadoParam = filtroEstado.value === 'activos'
      ? 'ingresado,registrado'
      : filtroEstado.value === 'todos'
        ? undefined
        : filtroEstado.value

    const [ordRes, statsRes] = await Promise.all([
      api.get('/api/parking/orders', {
        params: { company_id: companyId.value, fecha: fechaFiltro.value, estado: estadoParam },
      }),
      api.get('/api/parking/stats', {
        params: { company_id: companyId.value, fecha: fechaFiltro.value },
      }),
    ])
    ordenes.value = ordRes.data
    stats.value   = statsRes.data
  } catch {
    showToast('Error al cargar ingresos', 'error', 3000)
  }
  loading.value = false
}

async function cargarVehicleTypes() {
  if (!companyId.value) return
  try {
    const res = await api.get('/api/parking/vehicle-types', {
      params: { company_id: companyId.value },
    })
    vehicleTypes.value = res.data
  } catch {}
}

onMounted(() => {
  cargar()
  cargarVehicleTypes()
})

// ── Nuevo ingreso ─────────────────────────────────────────────────────────────
function buscarPlaca() {
  vehicleFound.value = false
  clearTimeout(_placaTimer)
  const p = form.value.placa.trim()
  if (p.length < 5) return
  _placaTimer = setTimeout(async () => {
    if (!companyId.value) return
    buscandoPlaca.value = true
    try {
      const { data } = await api.get('/api/parking/vehicle', {
        params: { placa: p, company_id: companyId.value },
      })
      if (data && data.placa) {
        vehicleFound.value = true
        if (data.vehicle_type_id) form.value.vehicle_type_id = data.vehicle_type_id
        if (data.foto_url)        form.value.foto_url = data.foto_url
      }
    } catch {}
    buscandoPlaca.value = false
  }, 500)
}

function abrirModalNuevo() {
  const now = new Date()
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset())
  form.value = {
    placa:           '',
    vehicle_type_id: null,
    hora_ingreso:    now.toISOString().slice(0, 16),
    adultos:         1,
    ninos:           0,
    mascotas:        0,
    foto_url:        null,
    obs_portero:     '',
  }
  vehicleFound.value  = false
  buscandoPlaca.value = false
  showModalNuevo.value = true
}

function cerrarModalNuevo() {
  showModalNuevo.value = false
}

async function onFotoChange(e) {
  const file = e.target.files[0]
  if (!file) return
  const formData = new FormData()
  formData.append('file', file)
  try {
    const res = await api.post(`/api/parking/photos/upload?company_id=${companyId.value}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    form.value.foto_url = res.data.url
  } catch {
    const reader = new FileReader()
    reader.onload = (ev) => { form.value.foto_url = ev.target.result }
    reader.readAsDataURL(file)
  }
}

async function guardarNuevo() {
  if (!form.value.placa.trim()) {
    showToast('La placa es requerida', 'warning', 2500)
    return
  }
  if (form.value.adultos < 1) {
    showToast('Se requiere al menos 1 adulto', 'warning', 2500)
    return
  }
  if (!form.value.hora_ingreso) {
    showToast('La hora de ingreso es requerida', 'warning', 2500)
    return
  }
  guardando.value = true
  try {
    const vtype = vehicleTypes.value.find(t => t.id === form.value.vehicle_type_id)
    const items = []
    if (form.value.adultos > 0)  items.push({ nombre: 'Adulto',  cantidad: form.value.adultos })
    if (form.value.ninos > 0)    items.push({ nombre: 'Niño',    cantidad: form.value.ninos   })
    if (form.value.mascotas > 0) items.push({ nombre: 'Mascota', cantidad: form.value.mascotas })
    if (!items.length) items.push({ nombre: 'Adulto', cantidad: 1 })

    const res = await api.post('/api/parking/orders', {
      company_id:        companyId.value,
      placa:             form.value.placa.trim().toUpperCase(),
      vehicle_type_name: vtype?.nombre || null,
      hora_ingreso:      form.value.hora_ingreso + ':00',
      foto_url:          form.value.foto_url,
      obs_portero:       form.value.obs_portero || null,
      items,
    })
    showToast('Ingreso registrado', 'success', 2000)
    cerrarModalNuevo()
    await cargar()
    ordenParaImprimir.value = res.data
  } catch (e) {
    showToast(e?.response?.data?.detail || 'Error al registrar ingreso', 'error', 3000)
  }
  guardando.value = false
}

// ── Reimprimir ────────────────────────────────────────────────────────────────
function abrirReimpresion(orden) {
  ordenParaImprimir.value = orden
}

// ── Click en tarjeta ──────────────────────────────────────────────────────────
function onClickCard(orden) {
  if (orden.estado !== 'ingresado') return
  ordenSeleccionada.value = orden
  formMesero.value = {
    adultos:    orden.adultos,
    ninos:      orden.ninos,
    mascotas:   orden.mascotas,
    obs_mesero: '',
  }
  showModalMesero.value = true
}

async function confirmarMesero() {
  if (!ordenSeleccionada.value) return
  if (formMesero.value.adultos < 1) {
    showToast('Se requiere al menos 1 adulto', 'warning', 2500)
    return
  }
  confirmando.value = true
  try {
    await api.put(`/api/parking/orders/${ordenSeleccionada.value.id}/registrar`, {
      adultos:    formMesero.value.adultos,
      ninos:      formMesero.value.ninos,
      mascotas:   formMesero.value.mascotas,
      obs_mesero: formMesero.value.obs_mesero || null,
    })
    showToast('Orden confirmada y enviada a caja', 'success', 2500)
    showModalMesero.value = false
    await cargar()
  } catch (e) {
    showToast(e?.response?.data?.detail || 'Error al confirmar', 'error', 3000)
  }
  confirmando.value = false
}

// ── Búsqueda ─────────────────────────────────────────────────────────────────
function aplicarBusqueda() {
  busActivo.value = { id: busId.value, placa: busPlaca.value, qr: busQR.value }
}

function limpiarBusqueda() {
  busId.value = ''
  busPlaca.value = ''
  busQR.value = ''
  busActivo.value = { id: '', placa: '', qr: '' }
}

// Limpiar búsqueda cuando se recarga la lista
watch(ordenes, () => { busActivo.value = { id: '', placa: '', qr: '' } })

// ── Utilidades ────────────────────────────────────────────────────────────────
function fmtHora(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.pk-page { padding: 16px; max-width: 1200px; margin: 0 auto; }

/* ── KPI bar ── */
.pk-kpi-bar {
  display: flex; align-items: stretch; gap: 10px; margin-bottom: 14px; flex-wrap: wrap;
}
.pk-btn-nuevo {
  display: flex; align-items: center; gap: 8px; padding: 10px 18px;
  background: #0d6efd; color: #fff; border: none; border-radius: 10px;
  font-size: .9rem; font-weight: 600; cursor: pointer; white-space: nowrap;
  transition: background .15s;
}
.pk-btn-nuevo:hover { background: #0b5ed7; }
.pk-kpi-card {
  display: flex; align-items: center; gap: 10px; padding: 10px 16px;
  border-radius: 10px; color: #fff; font-weight: 600; min-width: 110px; flex: 1;
}
.pk-kpi-card i { font-size: 1.4rem; opacity: .85; }
.pk-kpi-val   { display: block; font-size: 1.4rem; line-height: 1; }
.pk-kpi-lbl   { display: block; font-size: .72rem; opacity: .85; white-space: nowrap; }
.pk-kpi-disponibles { background: #198754; }
.pk-kpi-ocupadas    { background: #dc3545; }
.pk-kpi-total       { background: #6c757d; }

/* ── Búsqueda ── */
.pk-search-bar {
  display: flex; align-items: center; gap: 8px; margin-bottom: 12px; flex-wrap: wrap;
  background: #f8f9fa; border-radius: 10px; padding: 10px 14px; border: 1px solid #e9ecef;
}
.pk-search-group {
  display: flex; align-items: center; gap: 6px; flex: 1; min-width: 120px;
}
.pk-search-icon { color: #6c757d; font-size: .9rem; flex-shrink: 0; }
.pk-search-input {
  border: 1px solid #dee2e6; border-radius: 6px; padding: 6px 10px;
  font-size: .85rem; outline: none; width: 100%; background: #fff;
}
.pk-search-input:focus { border-color: #0d6efd; }
.pk-btn-buscar {
  padding: 7px 14px; border: none; border-radius: 8px;
  background: #0d6efd; color: #fff; cursor: pointer; font-size: .9rem; flex-shrink: 0;
}
.pk-btn-buscar:hover { background: #0b5ed7; }
.pk-btn-clear {
  padding: 7px 10px; border: 1px solid #ced4da; border-radius: 8px;
  background: #fff; color: #6c757d; cursor: pointer; font-size: .9rem; flex-shrink: 0;
}
.pk-btn-clear:hover { background: #f1f3f5; }

/* ── Búsqueda placa ── */
.pk-placa-wrap { position: relative; }
.pk-placa-hint { display: block; font-size: .75rem; margin-top: 4px; }
.pk-placa-buscando { color: #6c757d; }
.pk-placa-ok       { color: #198754; font-weight: 600; }

/* Tipo de vehículo auto-detectado (read-only) */
.pk-vtype-found { display: flex; gap: 8px; margin-top: 4px; }
.pk-vtype-found-badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 14px; border: 2px solid #198754; border-radius: 10px;
  background: #d1e7dd; color: #0a3622; font-weight: 700; font-size: .9rem;
}
.pk-vtype-found-badge i { font-size: 1.2rem; }
.pk-vtype-found-lock { font-size: .7rem; opacity: .7; margin-left: 2px; }
.pk-foto-label-hint { font-size: .75rem; font-weight: 400; margin-left: 6px; }

/* ── Tarjetas tipo vehículo ── */
.pk-vtype-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 8px; margin-top: 6px;
}
.pk-vtype-card {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  padding: 10px 8px; border: 2px solid #dee2e6; border-radius: 10px;
  background: #fff; cursor: pointer; font-size: .78rem; color: #495057;
  transition: all .15s; line-height: 1.2;
}
.pk-vtype-card i { font-size: 1.4rem; color: #6c757d; }
.pk-vtype-card:hover { border-color: #0d6efd; color: #0d6efd; }
.pk-vtype-card:hover i { color: #0d6efd; }
.pk-vtype-selected { border-color: #0d6efd !important; background: #e7f1ff; color: #0d6efd !important; }
.pk-vtype-selected i { color: #0d6efd !important; }

/* ── Foto en tarjeta ── */
.pk-card-foto { width: 100%; height: 80px; overflow: hidden; border-radius: 8px; margin-bottom: 6px; }
.pk-card-foto-img { width: 100%; height: 100%; object-fit: cover; }
.pk-card-id {
  font-size: .78rem; font-weight: 800; color: #0d6efd;
  text-align: center; letter-spacing: 1px;
}

/* ── Foto en modal ── */
.pk-modal-foto { width: 100%; }
.pk-modal-foto-img { width: 100%; max-height: 180px; object-fit: cover; border-radius: 8px; }

/* ── Filtro barra ── */
.pk-filtro-bar {
  display: flex; align-items: center; gap: 12px; margin-bottom: 14px; flex-wrap: wrap;
}
.pk-filtros-estado { display: flex; gap: 6px; flex-wrap: wrap; }
.pk-flt {
  padding: 6px 14px; border-radius: 20px; border: 1px solid #dee2e6;
  background: #fff; font-size: .82rem; cursor: pointer; transition: all .15s;
}
.pk-flt.active { background: #0d6efd; color: #fff; border-color: #0d6efd; }

/* ── Grid tarjetas ── */
.pk-loading { text-align: center; padding: 40px; color: #6c757d; }
.pk-empty   { text-align: center; padding: 60px 20px; color: #adb5bd; }
.pk-empty i { font-size: 2.5rem; display: block; margin-bottom: 8px; }

.pk-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}
.pk-card {
  background: #fff; border-radius: 12px; padding: 14px;
  border: 2px solid #e9ecef; cursor: pointer; transition: all .2s;
  display: flex; flex-direction: column; gap: 6px; box-shadow: 0 1px 4px rgba(0,0,0,.06);
}
.pk-card:hover { transform: translateY(-2px); box-shadow: 0 4px 14px rgba(0,0,0,.1); }
.pk-card--pagado   { opacity: .65; cursor: default; border-color: #d1e7dd; }
.pk-card--cancelado { opacity: .5; cursor: default; }

.pk-card--ingresado { border-color: #ffc107; }
.pk-card--ingresado:hover { border-color: #fd7e14; }
.pk-card--registrado { border-color: #0d6efd; }

.pk-card-top {
  display: flex; align-items: center; justify-content: space-between;
}
.pk-badge {
  font-size: .7rem; font-weight: 700; padding: 3px 8px; border-radius: 20px;
  text-transform: uppercase; letter-spacing: .3px;
}
.pk-badge--ingresado  { background: #fff3cd; color: #856404; }
.pk-badge--registrado { background: #cfe2ff; color: #084298; }
.pk-badge--pagado     { background: #d1e7dd; color: #0a3622; }
.pk-badge--cancelado  { background: #f8d7da; color: #842029; }

.pk-card-hora { font-size: .75rem; color: #6c757d; }
.pk-card-placa {
  font-size: 1.8rem; font-weight: 900; letter-spacing: 3px;
  text-align: center; color: #212529; line-height: 1;
  border: 2px solid #212529; border-radius: 6px;
  padding: 4px 0;
}
.pk-card-tipo { text-align: center; font-size: .78rem; color: #6c757d; }

.pk-card-personas { display: flex; gap: 6px; justify-content: center; flex-wrap: wrap; }
.pk-persona-pill {
  display: inline-flex; align-items: center; gap: 4px;
  background: #f8f9fa; border: 1px solid #dee2e6;
  padding: 3px 10px; border-radius: 20px; font-size: .82rem; font-weight: 600;
}
.pk-nino    { background: #fff3cd; border-color: #ffc107; }
.pk-mascota { background: #e2d9f3; border-color: #6f42c1; }

.pk-card-obs {
  font-size: .78rem; color: #6c757d; font-style: italic;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.pk-card-footer {
  display: flex; align-items: center; justify-content: space-between;
  margin-top: 4px; border-top: 1px solid #f1f3f5; padding-top: 6px;
}
.pk-card-orden { font-size: .72rem; color: #adb5bd; font-family: monospace; }
.pk-card-quien { font-size: .72rem; color: #6c757d; }

/* ── Modal ── */
.pk-modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.5);
  z-index: 1050; display: flex; align-items: center; justify-content: center; padding: 16px;
}
.pk-modal {
  background: #fff; border-radius: 14px; width: 100%; max-width: 480px;
  max-height: 90vh; overflow-y: auto; display: flex; flex-direction: column;
}
.pk-modal--mesero { max-width: 420px; }
.pk-modal-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px; border-bottom: 1px solid #e9ecef;
  font-weight: 700; font-size: .95rem;
}
.pk-modal-close {
  border: none; background: #f1f3f5; border-radius: 6px;
  padding: 5px 9px; cursor: pointer; color: #495057;
}
.pk-modal-body { padding: 18px; display: flex; flex-direction: column; gap: 14px; flex: 1; }
.pk-modal-footer {
  padding: 14px 18px; border-top: 1px solid #e9ecef;
  display: flex; gap: 10px; justify-content: flex-end;
}

.pk-field { display: flex; flex-direction: column; gap: 5px; }
.pk-field label { font-size: .82rem; font-weight: 600; color: #495057; }
.req { color: #dc3545; }
.pk-input {
  border: 1px solid #ced4da; border-radius: 8px; padding: 9px 12px;
  font-size: .9rem; outline: none; width: 100%; transition: border-color .15s;
}
.pk-input:focus { border-color: #0d6efd; }
.pk-placa-input {
  font-size: 1.4rem; font-weight: 900; letter-spacing: 3px;
  text-align: center; text-transform: uppercase;
}

.pk-personas-row {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;
}
.pk-field--num { align-items: center; text-align: center; }
.pk-counter {
  display: flex; align-items: center; justify-content: center; gap: 8px; margin-top: 2px;
}
.pk-counter button {
  width: 32px; height: 32px; border-radius: 50%; border: 1px solid #ced4da;
  background: #fff; font-size: 1.1rem; cursor: pointer; display: flex;
  align-items: center; justify-content: center; transition: all .15s;
}
.pk-counter button:hover { background: #0d6efd; color: #fff; border-color: #0d6efd; }
.pk-counter span { font-size: 1.2rem; font-weight: 700; min-width: 28px; text-align: center; }

.pk-foto-area { display: flex; flex-direction: column; gap: 8px; }
.pk-foto-preview { width: 100%; max-height: 160px; object-fit: cover; border-radius: 8px; }
.pk-foto-placeholder {
  height: 80px; border: 2px dashed #ced4da; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  gap: 8px; color: #adb5bd; font-size: .9rem;
}
.pk-foto-placeholder i { font-size: 1.5rem; }
.pk-foto-btns { display: flex; gap: 8px; }
.pk-btn-foto {
  flex: 1; padding: 8px 12px; border: 1px solid #0d6efd; border-radius: 8px;
  background: #fff; color: #0d6efd; font-size: .85rem; cursor: pointer;
  text-align: center; display: flex; align-items: center; justify-content: center; gap: 6px;
}
.pk-btn-foto:hover { background: #e7f1ff; }
.pk-btn-foto-rm {
  padding: 8px 12px; border: 1px solid #dc3545; border-radius: 8px;
  background: #fff; color: #dc3545; cursor: pointer;
}
.pk-btn-foto-rm:hover { background: #fdf0f0; }

.pk-btn-cancel {
  padding: 9px 18px; border: 1px solid #ced4da; border-radius: 8px;
  background: #fff; color: #495057; font-size: .9rem; cursor: pointer;
}
.pk-btn-guardar {
  padding: 9px 20px; border: none; border-radius: 8px;
  background: #0d6efd; color: #fff; font-size: .9rem; font-weight: 600;
  cursor: pointer; display: flex; align-items: center; gap: 6px; transition: background .15s;
}
.pk-btn-guardar:hover:not(:disabled) { background: #0b5ed7; }
.pk-btn-guardar:disabled { opacity: .6; cursor: default; }
.pk-btn-registrar { background: #198754; }
.pk-btn-registrar:hover:not(:disabled) { background: #157347; }

.pk-ord-placa-big {
  font-size: 2.2rem; font-weight: 900; letter-spacing: 4px;
  text-align: center; border: 2px solid #212529; border-radius: 8px; padding: 8px;
}
.pk-ord-sub { text-align: center; font-size: .82rem; color: #6c757d; margin-top: 4px; }
.pk-obs-portero-label {
  font-size: .82rem; background: #fff3cd; color: #664d03;
  padding: 8px 12px; border-radius: 8px; border-left: 3px solid #ffc107;
}

.spin { animation: pk-spin .8s linear infinite; }
@keyframes pk-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* ── Responsive ── */
@media (max-width: 768px) {
  .pk-kpi-bar { gap: 8px; }
  .pk-btn-nuevo { padding: 10px 14px; font-size: .85rem; }
  .pk-kpi-card { min-width: 90px; padding: 8px 12px; }
  .pk-kpi-val  { font-size: 1.2rem; }
  .pk-grid     { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 10px; }
  .pk-card-placa { font-size: 1.5rem; }
}
@media (max-width: 576px) {
  .pk-page { padding: 10px; }
  .pk-kpi-bar {
    display: grid; grid-template-columns: 1fr 1fr;
  }
  .pk-btn-nuevo { grid-column: 1 / -1; justify-content: center; }
  .pk-grid { grid-template-columns: 1fr 1fr; gap: 8px; }
  .pk-card { padding: 10px; }
  .pk-card-placa { font-size: 1.3rem; letter-spacing: 2px; }
  .pk-filtro-bar { flex-direction: column; align-items: flex-start; gap: 8px; }
  .pk-personas-row { grid-template-columns: repeat(3, 1fr); gap: 6px; }
  .pk-modal { max-width: 100%; border-radius: 14px 14px 0 0; }
  .pk-modal-overlay { align-items: flex-end; padding: 0; }
}
</style>
