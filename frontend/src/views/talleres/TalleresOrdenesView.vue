<template>
  <div class="ordenes-wrap">

    <!-- ══════════════ PANEL IZQUIERDO: Búsqueda + Formulario ══════════════ -->
    <div class="panel-left">

      <!-- Buscador de placa -->
      <div class="buscar-card">
        <div class="buscar-header">
          <i class="bi bi-car-front-fill buscar-icon"></i>
          <div>
            <h5 class="buscar-title">Buscar vehículo por placa</h5>
            <p class="buscar-sub">Ingresa la placa para cargar el historial o abrir una nueva orden</p>
          </div>
        </div>
        <div class="buscar-row">
          <input
            v-model="placaInput"
            class="placa-input"
            placeholder="Ej: ABC123"
            maxlength="10"
            @keyup.enter="buscarVehiculo"
            @input="placaInput = placaInput.toUpperCase()"
          />
          <button class="btn-buscar" :disabled="loadingBuscar || placaInput.length < 3" @click="buscarVehiculo">
            <i v-if="loadingBuscar" class="bi bi-hourglass-split spin"></i>
            <i v-else class="bi bi-search"></i>
            Buscar
          </button>
        </div>
      </div>

      <!-- Tarjeta del vehículo encontrado / formulario registro -->
      <template v-if="buscado">

        <!-- Vehículo encontrado -->
        <div v-if="vehiculo" class="vehiculo-card found">
          <div class="vc-header">
            <i class="bi bi-check-circle-fill vc-ok"></i>
            <div>
              <span class="vc-placa">{{ vehiculo.placa }}</span>
              <span class="vc-tipo">{{ labelTipo(vehiculo.tipo) }}</span>
            </div>
            <button class="btn-icon" title="Cambiar vehículo" @click="limpiarBusqueda">
              <i class="bi bi-x-circle"></i>
            </button>
          </div>
          <div class="vc-grid">
            <div class="vc-field"><span class="vc-lbl">Marca / Modelo</span><span class="vc-val">{{ [vehiculo.marca, vehiculo.modelo].filter(Boolean).join(' ') || '—' }}</span></div>
            <div class="vc-field"><span class="vc-lbl">Año</span><span class="vc-val">{{ vehiculo.anio || '—' }}</span></div>
            <div class="vc-field"><span class="vc-lbl">Color</span><span class="vc-val">{{ vehiculo.color || '—' }}</span></div>
            <div class="vc-field"><span class="vc-lbl">Km actual</span><span class="vc-val">{{ vehiculo.km_actual ? fmt0(vehiculo.km_actual) + ' km' : '—' }}</span></div>
            <div class="vc-field span2"><span class="vc-lbl">Propietario</span><span class="vc-val">{{ vehiculo.cliente_nombre || '—' }} <span class="vc-cedula">{{ vehiculo.cliente_documento }}</span></span></div>
            <div class="vc-field"><span class="vc-lbl">Teléfono</span><span class="vc-val">{{ vehiculo.cliente_telefono || '—' }}</span></div>
          </div>
        </div>

        <!-- Vehículo no encontrado → formulario de registro rápido -->
        <div v-else class="vehiculo-card new">
          <div class="vc-header">
            <i class="bi bi-plus-circle-fill vc-new"></i>
            <div>
              <span class="vc-placa">{{ placaInput }}</span>
              <span class="vc-tipo nuevo">Vehículo nuevo — completar datos</span>
            </div>
          </div>
          <div class="form-grid">
            <div class="form-group">
              <label>Tipo *</label>
              <select v-model="nuevoVehiculo.tipo" class="form-ctrl">
                <option v-for="t in tiposVehiculo" :key="t.id" :value="String(t.id)">
                  {{ t.nombre }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>Marca</label>
              <input v-model="nuevoVehiculo.marca" class="form-ctrl" placeholder="Toyota, Chevrolet…" />
            </div>
            <div class="form-group">
              <label>Modelo</label>
              <input v-model="nuevoVehiculo.modelo" class="form-ctrl" placeholder="Corolla, Spark…" />
            </div>
            <div class="form-group">
              <label>Año</label>
              <input v-model="nuevoVehiculo.anio" type="number" class="form-ctrl" placeholder="2022" min="1950" :max="anioActual" />
            </div>
            <div class="form-group">
              <label>Color</label>
              <input v-model="nuevoVehiculo.color" class="form-ctrl" placeholder="Blanco, Negro…" />
            </div>
            <div class="form-group">
              <label>Km actual</label>
              <input v-model="nuevoVehiculo.km_actual" type="number" class="form-ctrl" placeholder="45000" min="0" />
            </div>
            <div class="form-group span2">
              <label>Nombre del propietario *</label>
              <input v-model="nuevoVehiculo.cliente_nombre" class="form-ctrl" placeholder="Nombre completo" />
            </div>
            <div class="form-group">
              <label>Documento</label>
              <input v-model="nuevoVehiculo.cliente_documento" class="form-ctrl" placeholder="Cédula / NIT" />
            </div>
            <div class="form-group">
              <label>Teléfono</label>
              <input v-model="nuevoVehiculo.cliente_telefono" class="form-ctrl" placeholder="3001234567" />
            </div>
          </div>
        </div>

        <!-- Formulario apertura de orden -->
        <div class="orden-form-card">
          <h6 class="form-section-title">
            <i class="bi bi-clipboard2-plus-fill"></i> Datos de la orden
          </h6>
          <div class="form-grid">
            <div class="form-group">
              <label>Tipo de servicio *</label>
              <select v-model="orden.tipo_item" class="form-ctrl">
                <option value="mecanica">🔧 Mecánica</option>
                <option value="lavado">🚿 Lavado / Estética</option>
                <option value="latoneria">🔨 Latonería</option>
                <option value="pintura">🎨 Pintura</option>
              </select>
            </div>
            <div class="form-group">
              <label>Km al ingreso</label>
              <input v-model="orden.km_ingreso" type="number" class="form-ctrl" placeholder="45200" min="0" />
            </div>
            <div class="form-group span2">
              <label>Diagnóstico inicial / Descripción del trabajo</label>
              <textarea v-model="orden.diagnostico" class="form-ctrl" rows="3"
                placeholder="Describe el problema reportado o el servicio solicitado…"></textarea>
            </div>
          </div>

          <!-- Asignación de personal -->
          <h6 class="form-section-title mt">
            <i class="bi bi-people-fill"></i> Asignación de personal
          </h6>
          <div class="form-grid">
            <div class="form-group">
              <label>Jefe responsable</label>
              <select v-model="orden.jefe_responsable_id" class="form-ctrl">
                <option value="">— Sin asignar —</option>
                <option v-for="u in usuarios" :key="u.id" :value="u.id">{{ u.full_name }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>Operario principal</label>
              <select v-model="orden.operario_id" class="form-ctrl">
                <option value="">— Sin asignar —</option>
                <option v-for="w in workers" :key="w.id" :value="w.id">
                  {{ w.name }} <template v-if="w.profession_nombre">— {{ w.profession_nombre }}</template>
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>¿Convenio empresarial?</label>
              <select v-model="orden.convenio_id" class="form-ctrl">
                <option value="">— Particular —</option>
                <option v-for="cv in convenios" :key="cv.id" :value="cv.id">{{ cv.nombre_empresa }}</option>
              </select>
            </div>
          </div>

          <div class="form-actions">
            <button class="btn-cancel-form" @click="limpiarBusqueda">
              <i class="bi bi-x"></i> Cancelar
            </button>
            <button class="btn-abrir" :disabled="loadingGuardar || !puedeGuardar" @click="abrirOrden">
              <i v-if="loadingGuardar" class="bi bi-hourglass-split spin"></i>
              <i v-else class="bi bi-clipboard2-check-fill"></i>
              Abrir Orden de Servicio
            </button>
          </div>
        </div>

      </template>

      <!-- Estado inicial (sin búsqueda) -->
      <div v-else class="empty-state">
        <i class="bi bi-car-front empty-icon"></i>
        <p>Ingresa la placa del vehículo para comenzar</p>
      </div>

    </div>

    <!-- ══════════════ PANEL DERECHO: Historial del vehículo / Lista de órdenes ══════════════ -->
    <div class="panel-right">

      <!-- Historial del vehículo buscado -->
      <template v-if="vehiculo && historial.length > 0">
        <div class="historial-header">
          <h6 class="historial-title">
            <i class="bi bi-clock-history"></i>
            Historial de {{ vehiculo.placa }}
          </h6>
          <span class="hist-count">{{ historial.length }} visita{{ historial.length !== 1 ? 's' : '' }}</span>
        </div>

        <!-- Métricas de frecuencia -->
        <div v-if="metricas" class="metricas-row">
          <div class="metrica-chip">
            <i class="bi bi-calendar-check"></i>
            Última visita: <strong>{{ fmtFecha(metricas.ultima_visita) }}</strong>
          </div>
          <div v-if="metricas.dias_desde" class="metrica-chip">
            <i class="bi bi-clock"></i>
            Hace {{ metricas.dias_desde }} días
          </div>
        </div>

        <div class="historial-list">
          <div
            v-for="h in historial" :key="h.id"
            class="hist-item"
            :class="`hs-${h.estado}`"
          >
            <div class="hist-top">
              <span class="hist-num">{{ h.numero_orden }}</span>
              <span :class="['hist-badge', `hb-${h.estado}`]">{{ labelEstado(h.estado) }}</span>
              <span class="hist-fecha">{{ fmtFecha(h.fecha_ingreso) }}</span>
            </div>
            <div class="hist-body">
              <p v-if="h.trabajo_realizado" class="hist-trabajo">{{ h.trabajo_realizado }}</p>
              <p v-else-if="h.diagnostico" class="hist-trabajo text-muted">{{ h.diagnostico }}</p>
            </div>
            <div class="hist-foot">
              <span v-if="h.km_ingreso" class="hist-meta"><i class="bi bi-speedometer2"></i> {{ fmt0(h.km_ingreso) }} km</span>
              <span v-if="h.jefe_nombre" class="hist-meta"><i class="bi bi-person-fill"></i> {{ h.jefe_nombre }}</span>
              <span v-if="h.total_orden" class="hist-total">{{ fmt(h.total_orden) }}</span>
            </div>
          </div>
        </div>
      </template>

      <!-- Sin historial -->
      <template v-else-if="vehiculo && historial.length === 0">
        <div class="historial-header">
          <h6 class="historial-title"><i class="bi bi-clock-history"></i> Historial</h6>
        </div>
        <div class="no-hist">
          <i class="bi bi-clipboard2-x"></i>
          <p>Primera visita de este vehículo</p>
        </div>
      </template>

      <!-- Lista general de órdenes del día -->
      <template v-else>
        <div class="historial-header">
          <h6 class="historial-title">
            <i class="bi bi-list-check"></i> Órdenes del día
          </h6>
          <button class="btn-icon" @click="cargarOrdenes" :disabled="loadingOrdenes">
            <i :class="['bi bi-arrow-clockwise', { spin: loadingOrdenes }]"></i>
          </button>
        </div>

        <!-- Filtro de estado -->
        <div class="filtro-estados">
          <button
            v-for="f in FILTROS"
            :key="f.valor"
            :class="['filtro-btn', { active: filtroEstado === f.valor }]"
            @click="filtroEstado = f.valor; cargarOrdenes()"
          >
            {{ f.label }}
            <span v-if="f.valor && conteos[f.valor]" class="filtro-count">{{ conteos[f.valor] }}</span>
          </button>
        </div>

        <div v-if="loadingOrdenes" class="loading-row">
          <i class="bi bi-hourglass-split spin"></i> Cargando...
        </div>

        <div v-else-if="ordenes.length === 0" class="no-hist">
          <i class="bi bi-clipboard2-x"></i>
          <p>Sin órdenes {{ filtroEstado ? 'con ese estado' : 'hoy' }}</p>
        </div>

        <div v-else class="historial-list">
          <div
            v-for="o in ordenes" :key="o.id"
            class="hist-item clickable"
            :class="`hs-${o.estado}`"
            @click="verOrden(o)"
          >
            <div class="hist-top">
              <span class="hist-num">{{ o.numero_orden }}</span>
              <span :class="['hist-badge', `hb-${o.estado}`]">{{ labelEstado(o.estado) }}</span>
              <span class="hist-fecha">{{ fmtHora(o.fecha_ingreso) }}</span>
            </div>
            <div class="hist-body">
              <strong class="hist-placa">{{ o.placa_vehiculo }}</strong>
              <span class="hist-cliente"> — {{ o.cliente_nombre || 'Sin cliente' }}</span>
            </div>
            <div class="hist-foot">
              <span v-if="o.jefe_nombre" class="hist-meta"><i class="bi bi-person-fill"></i> {{ o.jefe_nombre }}</span>
              <span v-if="o.cant_items" class="hist-meta"><i class="bi bi-list-ul"></i> {{ o.cant_items }} ítems</span>
              <span v-if="o.total_orden" class="hist-total">{{ fmt(o.total_orden) }}</span>
              <span v-if="o.convenio_nombre" class="hist-convenio">
                <i class="bi bi-building-fill"></i> {{ o.convenio_nombre }}
              </span>
            </div>
          </div>
        </div>
      </template>

    </div>

    <!-- Toast de confirmación -->
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

// ── Estado búsqueda ───────────────────────────────────────────────────────
const placaInput    = ref('')
const loadingBuscar = ref(false)
const buscado       = ref(false)
const vehiculo      = ref(null)
const historial     = ref([])

const metricas = computed(() => {
  if (!historial.value.length) return null
  const ultima = historial.value[0]?.fecha_ingreso
  if (!ultima) return null
  const dias = Math.floor((Date.now() - new Date(ultima)) / 86400000)
  return { ultima_visita: ultima, dias_desde: dias }
})

async function buscarVehiculo() {
  if (!placaInput.value || placaInput.value.length < 3) return
  loadingBuscar.value = true
  buscado.value       = false
  vehiculo.value      = null
  historial.value     = []
  try {
    const { data } = await api.get('/api/talleres/vehiculo', {
      params: { company_id: companyId.value, placa: placaInput.value }
    })
    vehiculo.value  = data.vehiculo
    historial.value = data.historial
    buscado.value   = true
    if (vehiculo.value) {
      // Pre-llenar km ingreso con el km actual del vehículo
      orden.value.km_ingreso = vehiculo.value.km_actual || ''
    }
  } catch {
    mostrarToast('Error al buscar el vehículo', 'error')
  } finally {
    loadingBuscar.value = false
  }
}

function limpiarBusqueda() {
  placaInput.value = ''
  buscado.value    = false
  vehiculo.value   = null
  historial.value  = []
  orden.value      = { ...ORDEN_DEFAULT }
  nuevoVehiculo.value = { ...NV_DEFAULT }
  cargarOrdenes()
}

// ── Formulario nuevo vehículo ─────────────────────────────────────────────
const anioActual = new Date().getFullYear()
const NV_DEFAULT = { tipo: '', marca: '', modelo: '', anio: '', color: '', km_actual: 0, cliente_nombre: '', cliente_documento: '', cliente_telefono: '' }
const nuevoVehiculo = ref({ ...NV_DEFAULT })

// ── Formulario orden ──────────────────────────────────────────────────────
const ORDEN_DEFAULT = { tipo_item: 'mecanica', km_ingreso: '', diagnostico: '', jefe_responsable_id: '', operario_id: '', convenio_id: '' }
const orden          = ref({ ...ORDEN_DEFAULT })
const loadingGuardar = ref(false)

const puedeGuardar = computed(() => {
  if (!placaInput.value) return false
  if (!vehiculo.value && !nuevoVehiculo.value.cliente_nombre) return false
  return true
})

async function abrirOrden() {
  if (!puedeGuardar.value) return
  loadingGuardar.value = true
  try {
    let vehicleId  = vehiculo.value?.asset_id ?? null
    let clienteId  = vehiculo.value?.client_id ?? null

    // Si el vehículo es nuevo → registrar primero
    if (!vehiculo.value) {
      const rv = await api.post('/api/talleres/vehiculo', {
        company_id:      companyId.value,
        placa:           placaInput.value,
        tipo:            nuevoVehiculo.value.tipo,
        marca:           nuevoVehiculo.value.marca,
        modelo:          nuevoVehiculo.value.modelo,
        anio:            nuevoVehiculo.value.anio || null,
        color:           nuevoVehiculo.value.color,
        km_actual:       nuevoVehiculo.value.km_actual || 0,
        // TODO: crear cliente si no existe (implementar en sprint siguiente)
        client_id:       null,
      })
      vehicleId = rv.data.asset_id
    }

    const workers = []
    if (orden.value.operario_id) {
      workers.push({ worker_id: orden.value.operario_id, rol: orden.value.tipo_item })
    }

    const { data } = await api.post('/api/talleres/ordenes', {
      company_id:          companyId.value,
      placa_vehiculo:      placaInput.value,
      vehicle_id:          vehicleId,
      client_id:           clienteId,
      convenio_id:         orden.value.convenio_id || null,
      km_ingreso:          orden.value.km_ingreso  || null,
      jefe_responsable_id: orden.value.jefe_responsable_id || null,
      diagnostico:         orden.value.diagnostico,
      workers,
    })

    mostrarToast(`Orden ${data.numero_orden} creada exitosamente`, 'ok')
    limpiarBusqueda()
  } catch (e) {
    mostrarToast(e?.response?.data?.detail ?? 'Error al crear la orden', 'error')
  } finally {
    loadingGuardar.value = false
  }
}

// ── Lista de órdenes del día ──────────────────────────────────────────────
const FILTROS = [
  { valor: '',           label: 'Todas' },
  { valor: 'abierta',    label: 'Abiertas' },
  { valor: 'en_proceso', label: 'En proceso' },
  { valor: 'terminada',  label: 'Terminadas' },
  { valor: 'entregada',  label: 'Entregadas' },
]

const filtroEstado  = ref('')
const ordenes       = ref([])
const loadingOrdenes= ref(false)
const conteos       = ref({})

async function cargarOrdenes() {
  if (!companyId.value) return
  loadingOrdenes.value = true
  try {
    const hoy = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Bogota' }).format(new Date())
    const params = { company_id: companyId.value, fecha_desde: hoy, fecha_hasta: hoy, page_size: 50 }
    if (filtroEstado.value) params.estado = filtroEstado.value

    const { data } = await api.get('/api/talleres/ordenes', { params })
    ordenes.value = data.items
  } catch {
    ordenes.value = []
  } finally {
    loadingOrdenes.value = false
  }
}

function verOrden(o) {
  // Por ahora muestra la placa en el buscador para ver el historial
  placaInput.value = o.placa_vehiculo
  buscarVehiculo()
}

// ── Datos auxiliares ──────────────────────────────────────────────────────
const usuarios       = ref([])
const workers        = ref([])
const convenios      = ref([])
const tiposVehiculo  = ref([])

async function cargarAuxiliares() {
  if (!companyId.value) return
  try {
    const [ru, rw, rc, rt] = await Promise.all([
      api.get('/users/',    { params: { company_id: companyId.value } }),
      api.get('/workers/',  { params: { company_id: companyId.value } }),
      api.get('/api/talleres/convenios',     { params: { company_id: companyId.value } }),
      api.get('/api/talleres/tipos-vehiculo', { params: { company_id: companyId.value } }),
    ])
    usuarios.value      = ru.data?.items ?? ru.data ?? []
    workers.value       = rw.data?.items ?? rw.data ?? []
    convenios.value     = rc.data ?? []
    tiposVehiculo.value = rt.data ?? []
    // Pre-seleccionar el primero disponible
    if (tiposVehiculo.value.length && !nuevoVehiculo.value.tipo) {
      nuevoVehiculo.value.tipo = String(tiposVehiculo.value[0].id)
    }
  } catch { /* silencioso */ }
}

onMounted(() => { cargarOrdenes(); cargarAuxiliares() })

// ── Toast ─────────────────────────────────────────────────────────────────
const toast = ref({ visible: false, msg: '', tipo: 'ok' })
function mostrarToast(msg, tipo = 'ok') {
  toast.value = { visible: true, msg, tipo }
  setTimeout(() => { toast.value.visible = false }, 3500)
}

// ── Helpers ───────────────────────────────────────────────────────────────
const LABELS_ESTADO  = { abierta: 'Abierta', en_proceso: 'En proceso', terminada: 'Terminada', entregada: 'Entregada', cancelada: 'Cancelada' }
function labelTipo(v) {
  if (!v) return '—'
  // Si es un id numérico, buscar en la lista dinámica
  const found = tiposVehiculo.value.find(t => String(t.id) === String(v) || t.nombre === v)
  return found ? found.nombre : v
}
function labelEstado(v) { return LABELS_ESTADO[v] ?? v }

function fmt(v) {
  if (v == null) return '—'
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v)
}
function fmt0(v) { return v ? new Intl.NumberFormat('es-CO').format(v) : '—' }
function fmtFecha(v) {
  if (!v) return '—'
  return new Intl.DateTimeFormat('es-CO', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(v))
}
function fmtHora(v) {
  if (!v) return '—'
  return new Intl.DateTimeFormat('es-CO', { hour: '2-digit', minute: '2-digit' }).format(new Date(v))
}
</script>

<style scoped>
/* ── Layout ── */
.ordenes-wrap {
  display: grid;
  grid-template-columns: 420px 1fr;
  gap: 20px;
  min-height: calc(100vh - 120px);
  align-items: start;
}

/* ── Panel izquierdo ── */
.panel-left { display: flex; flex-direction: column; gap: 14px; }

/* ── Buscador ── */
.buscar-card {
  background: #fff; border: 1.5px solid #e2e8f0; border-radius: 14px;
  padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.buscar-header { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.buscar-icon   { font-size: 28px; color: #1e3a5f; flex-shrink: 0; }
.buscar-title  { margin: 0; font-size: 15px; font-weight: 700; color: #1e3a5f; }
.buscar-sub    { margin: 2px 0 0; font-size: 12px; color: #64748b; }
.buscar-row    { display: flex; gap: 8px; }
.placa-input {
  flex: 1; border: 2px solid #e2e8f0; border-radius: 10px;
  padding: 10px 14px; font-size: 18px; font-weight: 800; color: #1e3a5f;
  letter-spacing: 2px; text-transform: uppercase; outline: none;
  transition: border-color 0.2s;
}
.placa-input:focus { border-color: #1e3a5f; }
.btn-buscar {
  display: flex; align-items: center; gap: 6px;
  background: #1e3a5f; color: #fff; border: none; border-radius: 10px;
  padding: 10px 18px; font-size: 14px; font-weight: 700; cursor: pointer;
  white-space: nowrap; transition: background 0.2s;
}
.btn-buscar:hover:not(:disabled) { background: #2d4f80; }
.btn-buscar:disabled { opacity: 0.5; cursor: default; }

/* ── Tarjeta vehículo ── */
.vehiculo-card {
  background: #fff; border-radius: 14px; padding: 14px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.vehiculo-card.found { border: 2px solid #22c55e; }
.vehiculo-card.new   { border: 2px solid #f59e0b; }
.vc-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.vc-ok   { font-size: 22px; color: #22c55e; }
.vc-new  { font-size: 22px; color: #f59e0b; }
.vc-placa { font-size: 20px; font-weight: 900; color: #1e3a5f; letter-spacing: 1px; display: block; }
.vc-tipo  { font-size: 11px; color: #64748b; }
.vc-tipo.nuevo { color: #d97706; font-weight: 600; }
.btn-icon {
  margin-left: auto; background: #f1f5f9; border: none; border-radius: 8px;
  width: 30px; height: 30px; cursor: pointer; color: #64748b; font-size: 16px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.btn-icon:hover { background: #e2e8f0; color: #1e3a5f; }
.vc-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.vc-field { display: flex; flex-direction: column; gap: 2px; }
.vc-field.span2 { grid-column: 1 / -1; }
.vc-lbl   { font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase; }
.vc-val   { font-size: 13px; font-weight: 600; color: #1e3a5f; }
.vc-cedula{ font-size: 11px; color: #94a3b8; font-weight: 400; margin-left: 4px; }

/* ── Formulario orden ── */
.orden-form-card {
  background: #fff; border: 1.5px solid #e2e8f0; border-radius: 14px;
  padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.form-section-title {
  display: flex; align-items: center; gap: 7px;
  font-size: 13px; font-weight: 700; color: #1e3a5f; margin: 0 0 12px;
}
.form-section-title.mt { margin-top: 14px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-group.span2 { grid-column: 1 / -1; }
.form-group label { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; }
.form-ctrl {
  border: 1.5px solid #e2e8f0; border-radius: 8px;
  padding: 8px 10px; font-size: 13px; color: #1e3a5f; outline: none;
  transition: border-color 0.2s; background: #fff;
  width: 100%; box-sizing: border-box;
}
.form-ctrl:focus { border-color: #1e3a5f; }
textarea.form-ctrl { resize: vertical; min-height: 72px; }

.form-actions {
  display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px;
  padding-top: 14px; border-top: 1px solid #f1f5f9;
}
.btn-cancel-form {
  display: flex; align-items: center; gap: 6px;
  background: #f1f5f9; color: #64748b; border: none; border-radius: 8px;
  padding: 9px 16px; font-size: 13px; font-weight: 600; cursor: pointer;
}
.btn-cancel-form:hover { background: #e2e8f0; }
.btn-abrir {
  display: flex; align-items: center; gap: 7px;
  background: #ea580c; color: #fff; border: none; border-radius: 10px;
  padding: 10px 20px; font-size: 14px; font-weight: 700; cursor: pointer;
  transition: background 0.2s;
}
.btn-abrir:hover:not(:disabled) { background: #c2410c; }
.btn-abrir:disabled { opacity: 0.5; cursor: default; }

/* ── Empty state ── */
.empty-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 12px; padding: 48px 24px; color: #94a3b8; text-align: center;
}
.empty-icon { font-size: 56px; color: #cbd5e1; }
.empty-state p { font-size: 14px; margin: 0; }

/* ── Panel derecho ── */
.panel-right {
  background: #fff; border: 1.5px solid #e2e8f0; border-radius: 14px;
  padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  max-height: calc(100vh - 120px); overflow-y: auto; position: sticky; top: 20px;
}

.historial-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #f1f5f9;
}
.historial-title { margin: 0; font-size: 14px; font-weight: 700; color: #1e3a5f; display: flex; align-items: center; gap: 7px; }
.hist-count { font-size: 12px; color: #94a3b8; }

/* Métricas frecuencia */
.metricas-row { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
.metrica-chip {
  display: inline-flex; align-items: center; gap: 5px;
  background: #f1f5f9; border-radius: 20px; padding: 3px 10px;
  font-size: 12px; color: #475569;
}
.metrica-chip .bi { color: #1e3a5f; }

/* Filtros estado */
.filtro-estados { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 12px; }
.filtro-btn {
  display: inline-flex; align-items: center; gap: 4px;
  background: #f1f5f9; border: 1.5px solid transparent; border-radius: 20px;
  padding: 4px 12px; font-size: 12px; font-weight: 600; color: #64748b;
  cursor: pointer; transition: all 0.18s;
}
.filtro-btn:hover  { border-color: #1e3a5f; color: #1e3a5f; }
.filtro-btn.active { background: #1e3a5f; color: #fff; }
.filtro-count { background: rgba(255,255,255,0.25); border-radius: 10px; padding: 0 5px; font-size: 10px; }

.loading-row { display: flex; align-items: center; gap: 8px; color: #94a3b8; font-size: 14px; padding: 24px; justify-content: center; }

/* Lista de historial / órdenes */
.historial-list { display: flex; flex-direction: column; gap: 8px; }

.hist-item {
  border: 1.5px solid #f1f5f9; border-radius: 10px; padding: 10px 12px;
  border-left-width: 4px;
}
.hist-item.clickable { cursor: pointer; transition: all 0.18s; }
.hist-item.clickable:hover { background: #f8fafc; transform: translateX(2px); }
.hs-abierta    { border-left-color: #3b82f6; }
.hs-en_proceso { border-left-color: #f97316; }
.hs-terminada  { border-left-color: #22c55e; }
.hs-entregada  { border-left-color: #94a3b8; }
.hs-cancelada  { border-left-color: #ef4444; opacity: 0.6; }

.hist-top { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.hist-num { font-size: 12px; font-weight: 800; color: #1e3a5f; }
.hist-badge { padding: 1px 7px; border-radius: 20px; font-size: 10px; font-weight: 700; }
.hb-abierta    { background: #dbeafe; color: #1d4ed8; }
.hb-en_proceso { background: #ffedd5; color: #ea580c; }
.hb-terminada  { background: #dcfce7; color: #16a34a; }
.hb-entregada  { background: #f1f5f9; color: #64748b; }
.hb-cancelada  { background: #fee2e2; color: #dc2626; }
.hist-fecha  { margin-left: auto; font-size: 11px; color: #94a3b8; white-space: nowrap; }

.hist-body { margin-bottom: 4px; }
.hist-trabajo { font-size: 12px; color: #475569; margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.hist-placa  { font-size: 14px; font-weight: 800; color: #1e3a5f; letter-spacing: 0.5px; }
.hist-cliente{ font-size: 13px; color: #64748b; }

.hist-foot { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.hist-meta { font-size: 11px; color: #94a3b8; display: flex; align-items: center; gap: 3px; }
.hist-total { margin-left: auto; font-size: 13px; font-weight: 700; color: #16a34a; }
.hist-convenio { font-size: 11px; color: #d97706; display: flex; align-items: center; gap: 3px; font-weight: 600; }

.no-hist {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 10px; padding: 40px 20px; color: #94a3b8; text-align: center;
}
.no-hist .bi { font-size: 36px; }
.no-hist p   { font-size: 13px; margin: 0; }

/* ── Toast ── */
.toast-msg {
  position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
  display: flex; align-items: center; gap: 8px;
  padding: 12px 20px; border-radius: 10px;
  font-size: 14px; font-weight: 600; z-index: 9999;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  animation: slideInUp 0.3s ease;
}
.toast-ok    { background: #1e3a5f; color: #fff; }
.toast-error { background: #dc2626; color: #fff; }
@keyframes slideInUp { from { opacity: 0; transform: translateX(-50%) translateY(10px); } to { opacity: 1; transform: translateX(-50%) translateY(0); } }

/* ── Spinner ── */
.spin { display: inline-block; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Responsive ── */
@media (max-width: 1024px) {
  .ordenes-wrap { grid-template-columns: 1fr; }
  .panel-right  { max-height: none; position: static; }
}

@media (max-width: 768px) {
  .form-grid   { grid-template-columns: 1fr; }
  .form-group.span2 { grid-column: 1; }
  .vc-grid     { grid-template-columns: 1fr; }
  .vc-field.span2   { grid-column: 1; }
  .buscar-row  { flex-direction: column; }
  .placa-input { font-size: 16px; }
  .form-actions { flex-direction: column; }
  .btn-abrir, .btn-cancel-form { width: 100%; justify-content: center; }
}

@media (max-width: 576px) {
  .filtro-estados { gap: 4px; }
  .filtro-btn     { padding: 3px 9px; font-size: 11px; }
  .historial-title{ font-size: 13px; }
}
</style>
