<template>
  <div class="ordenes-page">

    <!-- ══ PASO 0: Buscador de placa ══════════════════════════════════════ -->
    <div class="buscar-card">
      <div class="buscar-inner">
        <div class="buscar-icon-wrap"><i class="bi bi-car-front-fill"></i></div>
        <div class="buscar-texts">
          <h5>Buscar vehículo por placa</h5>
          <p>Ingresa la placa para cargar el historial o abrir una nueva orden</p>
        </div>
      </div>
      <div class="buscar-row">
        <input
          v-model="placaInput"
          class="placa-input"
          placeholder="Ej: ABC123"
          maxlength="10"
          ref="inputRef"
          @keyup.enter="buscarVehiculo"
          @input="placaInput = placaInput.toUpperCase()"
        />
        <button class="btn-buscar" :disabled="loadingBuscar || placaInput.length < 3" @click="buscarVehiculo">
          <i v-if="loadingBuscar" class="bi bi-hourglass-split spin"></i>
          <i v-else class="bi bi-search"></i>
          Buscar
        </button>
        <button v-if="buscado" class="btn-limpiar" @click="limpiarBusqueda" title="Nueva búsqueda">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>
    </div>

    <!-- ══ ÓRDENES ACTIVAS (visible cuando no se ha buscado placa) ═════════ -->
    <div v-if="!buscado" class="ordenes-activas-card">
      <div class="oa-head">
        <div class="oa-titulo">
          <i class="bi bi-list-check"></i>
          <span>Órdenes Activas</span>
          <span class="oa-badge">{{ ordenesActivas.total }}</span>
        </div>
        <div class="oa-filtros">
          <button v-for="f in FILTROS_OA" :key="f.val"
            :class="['oa-flt', { active: filtroOA === f.val }]"
            @click="filtroOA = f.val; cargarOrdenes()">
            {{ f.label }}
          </button>
        </div>
      </div>

      <div v-if="loadingOrdenes" class="oa-loading">
        <i class="bi bi-arrow-repeat spin"></i> Cargando órdenes…
      </div>
      <div v-else-if="ordenesActivas.items.length === 0" class="oa-empty">
        <i class="bi bi-inbox"></i>
        <p>No hay órdenes {{ filtroOA !== 'activas' ? 'con ese estado' : 'activas' }}</p>
      </div>
      <div v-else class="oa-table-wrap">
        <table class="oa-table">
          <thead>
            <tr>
              <th>Orden</th>
              <th>Placa</th>
              <th>Estado</th>
              <th>Fecha</th>
              <th>Jefe</th>
              <th class="ta-r">Total</th>
              <th>Acción</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="o in ordenesActivas.items" :key="o.id" class="oa-row" @click="router.push(`/talleres/orden/${o.id}`)">
              <td class="oa-num">{{ o.numero_orden }}</td>
              <td class="oa-placa">{{ o.placa_vehiculo }}</td>
              <td><span :class="['estado-badge', `es-${o.estado}`]">{{ LABELS_ESTADO[o.estado] || o.estado }}</span></td>
              <td class="oa-fecha">{{ fmtFecha(o.fecha_ingreso) }}</td>
              <td class="oa-jefe">{{ o.jefe_nombre || '—' }}</td>
              <td class="ta-r oa-total">{{ fmt(o.total_orden) }}</td>
              <td @click.stop>
                <button
                  v-if="ESTADOS_EDITABLE.includes(o.estado)"
                  class="oa-btn-open oa-btn-edit"
                  @click="router.push(`/talleres/orden/${o.id}`)"
                  title="Editar orden"
                ><i class="bi bi-pencil-fill"></i></button>
                <button
                  v-else
                  class="oa-btn-open oa-btn-view"
                  @click="router.push(`/talleres/orden/${o.id}`)"
                  title="Ver / Reimprimir"
                ><i class="bi bi-eye-fill"></i></button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Paginación -->
      <div v-if="ordenesActivas.total > paginaSize" class="oa-paginacion">
        <button :disabled="paginaActual <= 1" @click="paginaActual--; cargarOrdenes()" class="pag-btn">
          <i class="bi bi-chevron-left"></i>
        </button>
        <span class="pag-info">{{ paginaActual }} / {{ Math.ceil(ordenesActivas.total / paginaSize) }}</span>
        <button :disabled="paginaActual >= Math.ceil(ordenesActivas.total / paginaSize)" @click="paginaActual++; cargarOrdenes()" class="pag-btn">
          <i class="bi bi-chevron-right"></i>
        </button>
      </div>
    </div>

    <!-- ══ VEHÍCULO ENCONTRADO ══════════════════════════════════════════════ -->
    <template v-if="buscado && vehiculo">

      <!-- Tarjeta del vehículo -->
      <div class="vehiculo-card found">
        <div class="vc-top">
          <div class="vc-avatar"><i class="bi bi-car-front-fill"></i></div>
          <div class="vc-datos">
            <div class="vc-placa-row">
              <span class="vc-placa">{{ vehiculo.placa }}</span>
              <span class="vc-tipo-badge">{{ vehiculo.tipo || '—' }}</span>
            </div>
            <div class="vc-desc">{{ [vehiculo.marca, vehiculo.modelo, vehiculo.anio].filter(Boolean).join(' · ') || '—' }}</div>
            <div class="vc-meta">
              <span v-if="vehiculo.color"><i class="bi bi-circle-fill" style="font-size:9px"></i> {{ vehiculo.color }}</span>
              <span v-if="vehiculo.km_actual"><i class="bi bi-speedometer2"></i> {{ fmt0(vehiculo.km_actual) }} km</span>
            </div>
          </div>
          <div class="vc-actions">
            <button v-if="isAdmin" class="btn-edit-v" @click="abrirEditarVehiculo" title="Editar vehículo">
              <i class="bi bi-pencil-fill"></i>
            </button>
          </div>
        </div>
        <div v-if="vehiculo.cliente_nombre" class="vc-propietario">
          <i class="bi bi-person-fill"></i>
          <span>{{ vehiculo.cliente_nombre }}</span>
          <span v-if="vehiculo.cliente_documento" class="vc-doc">CC {{ vehiculo.cliente_documento }}</span>
          <span v-if="vehiculo.cliente_telefono" class="vc-tel"><i class="bi bi-telephone-fill"></i> {{ vehiculo.cliente_telefono }}</span>
        </div>

        <!-- Fotos del vehículo -->
        <div class="vc-fotos">
          <div v-for="f in fotosVehiculo" :key="f.id" class="foto-thumb">
            <img :src="f.photo_url" :alt="f.tipo" />
            <span class="foto-tipo-badge">{{ f.tipo }}</span>
            <button v-if="isAdmin" class="foto-del" @click="eliminarFoto(f)" title="Eliminar foto">
              <i class="bi bi-x"></i>
            </button>
          </div>
          <label class="foto-add" title="Agregar foto de ingreso">
            <i class="bi bi-camera-fill"></i>
            <span>Foto</span>
            <input type="file" accept="image/*" class="foto-file-input" @change="subirFoto" />
          </label>
        </div>
      </div>

      <!-- Tabs: Nueva Orden | Historial -->
      <div class="tabs-bar">
        <button :class="['tab-btn', { active: tabActivo === 'nueva' }]" @click="tabActivo = 'nueva'">
          <i class="bi bi-clipboard2-plus-fill"></i> Nueva Orden
        </button>
        <button :class="['tab-btn', { active: tabActivo === 'historial' }]" @click="tabActivo = 'historial'">
          <i class="bi bi-clock-history"></i> Historial
          <span v-if="historial.length" class="tab-count">{{ historial.length }}</span>
        </button>
      </div>

      <!-- TAB NUEVA ORDEN -->
      <div v-if="tabActivo === 'nueva'" class="form-card">
        <div class="form-grid">
          <div class="fg">
            <label>Tipo de servicio *</label>
            <select v-model="orden.tipo_item" class="form-ctrl">
              <option value="mecanica">🔧 Mecánica</option>
              <option value="lavado">🚿 Lavado / Estética</option>
              <option value="latoneria">🔨 Latonería</option>
              <option value="pintura">🎨 Pintura</option>
              <option value="diagnostico">🔍 Diagnóstico</option>
            </select>
          </div>
          <div class="fg">
            <label>Km al ingreso</label>
            <input v-model.number="orden.km_ingreso" type="number" class="form-ctrl" placeholder="220000" />
          </div>
          <div class="fg span2">
            <label>Diagnóstico / Descripción del trabajo</label>
            <textarea v-model="orden.diagnostico" class="form-ctrl" rows="3"
              placeholder="Describe el problema reportado o el servicio solicitado…"></textarea>
          </div>
          <div class="fg">
            <label>Jefe responsable</label>
            <select v-model="orden.jefe_responsable_id" class="form-ctrl">
              <option value="">— Sin asignar —</option>
              <option v-for="u in usuarios" :key="u.id" :value="u.id">{{ u.nombre || u.name }}</option>
            </select>
          </div>
          <div class="fg">
            <label>Operario principal</label>
            <select v-model="orden.operario_id" class="form-ctrl">
              <option value="">— Sin asignar —</option>
              <option v-for="w in workers" :key="w.id" :value="w.id">{{ w.name }}</option>
            </select>
          </div>
          <div class="fg">
            <label>¿Convenio empresarial?</label>
            <select v-model="orden.convenio_id" class="form-ctrl">
              <option value="">— Particular —</option>
              <option v-for="c in convenios" :key="c.id" :value="c.id">{{ c.nombre_empresa }}</option>
            </select>
          </div>
          <div class="fg">
            <label>Promesa de entrega</label>
            <CustomDatePicker v-model="orden.promesa_entrega" />
          </div>
        </div>
        <div class="form-actions">
          <button class="btn btn-secondary" @click="limpiarBusqueda">Cancelar</button>
          <button class="btn btn-primary" @click="abrirOrden" :disabled="loadingGuardar">
            <i v-if="loadingGuardar" class="bi bi-hourglass-split spin"></i>
            <i v-else class="bi bi-clipboard2-check-fill"></i>
            Abrir Orden de Servicio
          </button>
        </div>
      </div>

      <!-- TAB HISTORIAL -->
      <div v-if="tabActivo === 'historial'" class="historial-section">
        <div class="hist-filtros">
          <button
            v-for="f in FILTROS_HIST"
            :key="f.val"
            :class="['hf-btn', { active: filtroHist === f.val }]"
            @click="filtroHist = f.val"
          >{{ f.label }}</button>
        </div>
        <div class="hist-list">
          <div
            v-for="o in historialFiltrado"
            :key="o.id"
            class="hist-item"
            :class="`hs-${o.estado}`"
          >
            <div class="hi-left">
              <span class="hi-num">{{ o.numero_orden }}</span>
              <span :class="['hi-badge', `hb-${o.estado}`]">{{ LABELS_ESTADO[o.estado] || o.estado }}</span>
              <span class="hi-fecha">{{ fmtFecha(o.fecha_ingreso) }}</span>
            </div>
            <div class="hi-center">
              <span v-if="o.jefe_nombre" class="hi-meta"><i class="bi bi-person-fill"></i> {{ o.jefe_nombre }}</span>
              <span v-if="o.total_orden" class="hi-total">{{ fmt(o.total_orden) }}</span>
            </div>
            <div class="hi-actions">
              <button
                v-if="['abierta','en_proceso'].includes(o.estado)"
                class="btn-hist-edit"
                @click="irAOrden(o.id)"
                title="Editar orden"
              ><i class="bi bi-pencil-fill"></i> Editar</button>
              <button class="btn-hist-print" @click="imprimirOrden(o)" title="Imprimir">
                <i class="bi bi-printer-fill"></i>
              </button>
            </div>
          </div>
          <div v-if="historialFiltrado.length === 0" class="hist-empty">
            <i class="bi bi-inbox"></i>
            <p>No hay órdenes {{ filtroHist === 'abiertas' ? 'abiertas' : filtroHist === 'cerradas' ? 'cerradas' : '' }} para este vehículo.</p>
          </div>
        </div>
      </div>
    </template>

    <!-- ══ VEHÍCULO NO ENCONTRADO: WIZARD ══════════════════════════════════ -->
    <template v-if="buscado && !vehiculo">

      <!-- Indicador de pasos -->
      <div class="wizard-steps">
        <div :class="['wstep', { active: wizardStep === 1, done: wizardStep > 1 }]">
          <span class="ws-num">1</span>
          <span class="ws-label">Datos del vehículo</span>
        </div>
        <div class="ws-line"></div>
        <div :class="['wstep', { active: wizardStep === 2, done: wizardStep > 2 }]">
          <span class="ws-num">2</span>
          <span class="ws-label">Nueva orden</span>
        </div>
      </div>

      <!-- WIZARD PASO 1: Registro del vehículo -->
      <div v-if="wizardStep === 1" class="form-card">
        <div class="form-section-title"><i class="bi bi-car-front-fill"></i> Nuevo vehículo — {{ placaInput }}</div>
        <div class="form-grid">
          <div class="fg">
            <label>Tipo de vehículo *</label>
            <select v-model="nuevoVehiculo.tipo" class="form-ctrl">
              <option v-for="t in tiposVehiculo" :key="t.id" :value="t.nombre">{{ t.nombre }}</option>
            </select>
          </div>
          <div class="fg">
            <label>Marca</label>
            <input v-model="nuevoVehiculo.marca" class="form-ctrl" placeholder="Toyota, Chevrolet…" />
          </div>
          <div class="fg">
            <label>Modelo</label>
            <input v-model="nuevoVehiculo.modelo" class="form-ctrl" placeholder="Corolla, Spark…" />
          </div>
          <div class="fg">
            <label>Año</label>
            <input v-model.number="nuevoVehiculo.anio" type="number" min="1950" :max="anioActual + 1" class="form-ctrl" placeholder="2020" />
          </div>
          <div class="fg">
            <label>Color</label>
            <input v-model="nuevoVehiculo.color" class="form-ctrl" placeholder="Negro, Blanco…" />
          </div>
          <div class="fg">
            <label>Km actual</label>
            <input v-model.number="nuevoVehiculo.km_actual" type="number" min="0" class="form-ctrl" placeholder="0" />
          </div>
        </div>

        <div class="form-section-title" style="margin-top:16px"><i class="bi bi-person-fill"></i> Propietario</div>
        <div class="form-grid">
          <div class="fg span2">
            <label>Nombre completo *</label>
            <input v-model="nuevoVehiculo.cliente_nombre" class="form-ctrl" placeholder="Nombre del propietario" />
          </div>
          <div class="fg">
            <label>Documento (CC / NIT)</label>
            <input v-model="nuevoVehiculo.cliente_documento" class="form-ctrl" placeholder="123456789" />
          </div>
          <div class="fg">
            <label>Teléfono</label>
            <input v-model="nuevoVehiculo.cliente_telefono" class="form-ctrl" placeholder="300 000 0000" />
          </div>
        </div>

        <!-- Fotos de ingreso -->
        <div class="form-section-title" style="margin-top:16px"><i class="bi bi-camera-fill"></i> Fotos del vehículo al ingreso</div>
        <div class="fotos-upload-area">
          <div v-for="(f, i) in fotosNuevas" :key="i" class="foto-preview">
            <img :src="f.preview" alt="foto" />
            <button class="foto-del" @click="fotosNuevas.splice(i,1)"><i class="bi bi-x"></i></button>
          </div>
          <label class="foto-add-btn">
            <i class="bi bi-camera-fill"></i>
            <span>Agregar foto</span>
            <input type="file" accept="image/*" multiple class="foto-file-input" @change="agregarFotoNueva" />
          </label>
        </div>

        <div class="form-actions">
          <button class="btn btn-secondary" @click="limpiarBusqueda">Cancelar</button>
          <button class="btn btn-primary" @click="registrarVehiculo" :disabled="loadingGuardar">
            <i v-if="loadingGuardar" class="bi bi-hourglass-split spin"></i>
            <i v-else class="bi bi-check-lg"></i>
            Registrar vehículo
          </button>
        </div>
      </div>

      <!-- WIZARD PASO 2: Nueva orden (vehículo recién registrado) -->
      <div v-if="wizardStep === 2" class="form-card">
        <div class="form-section-title"><i class="bi bi-clipboard2-plus-fill"></i> Abrir Orden de Servicio</div>
        <div class="form-grid">
          <div class="fg">
            <label>Tipo de servicio *</label>
            <select v-model="orden.tipo_item" class="form-ctrl">
              <option value="mecanica">🔧 Mecánica</option>
              <option value="lavado">🚿 Lavado / Estética</option>
              <option value="latoneria">🔨 Latonería</option>
              <option value="pintura">🎨 Pintura</option>
              <option value="diagnostico">🔍 Diagnóstico</option>
            </select>
          </div>
          <div class="fg">
            <label>Km al ingreso</label>
            <input v-model.number="orden.km_ingreso" type="number" class="form-ctrl" />
          </div>
          <div class="fg span2">
            <label>Diagnóstico / Descripción</label>
            <textarea v-model="orden.diagnostico" class="form-ctrl" rows="3"
              placeholder="Describe el problema o servicio solicitado…"></textarea>
          </div>
          <div class="fg">
            <label>Jefe responsable</label>
            <select v-model="orden.jefe_responsable_id" class="form-ctrl">
              <option value="">— Sin asignar —</option>
              <option v-for="u in usuarios" :key="u.id" :value="u.id">{{ u.nombre || u.name }}</option>
            </select>
          </div>
          <div class="fg">
            <label>Operario principal</label>
            <select v-model="orden.operario_id" class="form-ctrl">
              <option value="">— Sin asignar —</option>
              <option v-for="w in workers" :key="w.id" :value="w.id">{{ w.name }}</option>
            </select>
          </div>
          <div class="fg">
            <label>¿Convenio empresarial?</label>
            <select v-model="orden.convenio_id" class="form-ctrl">
              <option value="">— Particular —</option>
              <option v-for="c in convenios" :key="c.id" :value="c.id">{{ c.nombre_empresa }}</option>
            </select>
          </div>
          <div class="fg">
            <label>Promesa de entrega</label>
            <CustomDatePicker v-model="orden.promesa_entrega" />
          </div>
        </div>
        <div class="form-actions">
          <button class="btn btn-secondary" @click="wizardStep = 1">Atrás</button>
          <button class="btn btn-primary" @click="abrirOrden" :disabled="loadingGuardar">
            <i v-if="loadingGuardar" class="bi bi-hourglass-split spin"></i>
            <i v-else class="bi bi-clipboard2-check-fill"></i>
            Abrir Orden de Servicio
          </button>
        </div>
      </div>
    </template>

    <!-- ══ MODAL EDITAR VEHÍCULO ══════════════════════════════════════════ -->
    <Teleport to="body">
      <div v-if="showEditVehiculo" class="modal-overlay" @click.self="showEditVehiculo = false">
        <div class="modal-box">
          <div class="mh">
            <h3><i class="bi bi-pencil-fill"></i> Editar vehículo — {{ vehiculo?.placa }}</h3>
            <button class="btn-x" @click="showEditVehiculo = false"><i class="bi bi-x-lg"></i></button>
          </div>
          <div class="mb-area">
            <div class="form-grid">
              <div class="fg">
                <label>Tipo</label>
                <select v-model="editForm.tipo" class="form-ctrl">
                  <option v-for="t in tiposVehiculo" :key="t.id" :value="t.nombre">{{ t.nombre }}</option>
                </select>
              </div>
              <div class="fg"><label>Marca</label><input v-model="editForm.marca" class="form-ctrl" /></div>
              <div class="fg"><label>Modelo</label><input v-model="editForm.modelo" class="form-ctrl" /></div>
              <div class="fg"><label>Año</label><input v-model.number="editForm.anio" type="number" class="form-ctrl" /></div>
              <div class="fg"><label>Color</label><input v-model="editForm.color" class="form-ctrl" /></div>
              <div class="fg"><label>Km actual</label><input v-model.number="editForm.km_actual" type="number" class="form-ctrl" /></div>
              <div class="form-section-title span2"><i class="bi bi-person-fill"></i> Propietario</div>
              <div class="fg span2"><label>Nombre</label><input v-model="editForm.cliente_nombre" class="form-ctrl" /></div>
              <div class="fg"><label>Documento</label><input v-model="editForm.cliente_documento" class="form-ctrl" /></div>
              <div class="fg"><label>Teléfono</label><input v-model="editForm.cliente_telefono" class="form-ctrl" /></div>
            </div>
          </div>
          <div class="mf">
            <button class="btn btn-secondary btn-sm" @click="showEditVehiculo = false">Cancelar</button>
            <button class="btn btn-primary btn-sm" @click="guardarVehiculo" :disabled="loadingGuardar">
              <i v-if="loadingGuardar" class="bi bi-hourglass-split spin"></i>
              Guardar cambios
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
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useCompanyStore } from '@/stores/companyStore'
import api from '@/services/apis'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'
import { showConfirm } from '@/utils/toast'

const router       = useRouter()
const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id)
const isAdmin      = computed(() => {
  try {
    const u = JSON.parse(localStorage.getItem('user') || '{}')
    const rol = (u?.role || '').toLowerCase()
    return rol.includes('admin') || rol.includes('sysadmin')
  } catch { return false }
})

// ── Órdenes activas (lista general) ───────────────────────────────────────
const ordenesActivas = ref({ items: [], total: 0 })
const loadingOrdenes = ref(false)
const filtroOA       = ref('activas')
const paginaActual   = ref(1)
const paginaSize     = 15

const FILTROS_OA = [
  { val: 'activas',     label: 'Activas' },
  { val: 'abierta',     label: 'Abiertas' },
  { val: 'en_proceso',  label: 'En proceso' },
  { val: 'terminada',   label: 'Terminadas' },
  { val: 'facturadas',  label: 'Facturadas' },
  { val: 'todas',       label: 'Todas' },
]

const ESTADOS_EDITABLE = ['abierta', 'en_proceso']

async function cargarOrdenes() {
  if (!companyId.value) return
  loadingOrdenes.value = true
  try {
    const params = { company_id: companyId.value, page: paginaActual.value, page_size: paginaSize }
    if (filtroOA.value === 'activas') {
      params.estado = 'abierta,en_proceso,terminada'
    } else if (filtroOA.value === 'facturadas') {
      params.estado = 'entregada'
    } else if (filtroOA.value !== 'todas') {
      params.estado = filtroOA.value
    }
    const { data } = await api.get('/api/talleres/ordenes', { params })
    ordenesActivas.value = data
  } catch { ordenesActivas.value = { items: [], total: 0 } }
  finally { loadingOrdenes.value = false }
}

async function abrirPorPlaca(placa) {
  if (!placa) return
  placaInput.value = placa.toUpperCase()
  await buscarVehiculo()
}

// ── Búsqueda ──────────────────────────────────────────────────────────────
const placaInput    = ref('')
const loadingBuscar = ref(false)
const buscado       = ref(false)
const vehiculo      = ref(null)
const historial     = ref([])
const fotosVehiculo = ref([])
const inputRef      = ref(null)

async function buscarVehiculo() {
  if (!placaInput.value || placaInput.value.length < 3) return
  loadingBuscar.value = true
  buscado.value = false; vehiculo.value = null; historial.value = []; fotosVehiculo.value = []
  try {
    const { data } = await api.get('/api/talleres/vehiculo', {
      params: { company_id: companyId.value, placa: placaInput.value }
    })
    vehiculo.value  = data.vehiculo
    historial.value = data.historial || []
    buscado.value   = true
    if (vehiculo.value) {
      orden.value.km_ingreso = vehiculo.value.km_actual || ''
      cargarFotos()
    }
  } catch { mostrarToast('Error al buscar el vehículo', 'error') }
  finally { loadingBuscar.value = false }
}

async function cargarFotos() {
  if (!vehiculo.value?.asset_id) return
  try {
    const { data } = await api.get(`/api/talleres/vehiculo/${vehiculo.value.asset_id}/fotos`, {
      params: { company_id: companyId.value }
    })
    fotosVehiculo.value = data
  } catch { /* silencioso */ }
}

function limpiarBusqueda() {
  placaInput.value = ''; buscado.value = false; vehiculo.value = null
  historial.value = []; fotosVehiculo.value = []; wizardStep.value = 1
  orden.value = { ...ORDEN_DEFAULT }; nuevoVehiculo.value = { ...NV_DEFAULT }
  cargarOrdenes()
  nextTick(() => inputRef.value?.focus())
}

// ── Fotos (vehículo existente) ────────────────────────────────────────────
async function subirFoto(e) {
  const file = e.target.files?.[0]
  if (!file || !vehiculo.value?.asset_id) return
  const fd = new FormData(); fd.append('file', file)
  try {
    const up = await api.post('/upload-image/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    const url = up.data?.url || up.data?.photo_url
    if (!url) { mostrarToast('Error al subir imagen', 'error'); return }
    await api.post(`/api/talleres/vehiculo/${vehiculo.value.asset_id}/fotos`, {
      company_id: companyId.value, photo_url: url, tipo: 'ingreso'
    })
    await cargarFotos()
  } catch { mostrarToast('Error al guardar foto', 'error') }
  e.target.value = ''
}

async function eliminarFoto(f) {
  if (!(await showConfirm('¿Eliminar esta foto?'))) return
  try {
    await api.delete(`/api/talleres/vehiculo/fotos/${f.id}`, { params: { company_id: companyId.value } })
    fotosVehiculo.value = fotosVehiculo.value.filter(x => x.id !== f.id)
  } catch { mostrarToast('Error al eliminar', 'error') }
}

// ── Tabs historial ────────────────────────────────────────────────────────
const tabActivo   = ref('nueva')
const filtroHist  = ref('todas')
const FILTROS_HIST = [
  { val: 'todas',   label: 'Todas' },
  { val: 'abiertas', label: 'Abiertas' },
  { val: 'cerradas', label: 'Cerradas' },
]
const LABELS_ESTADO = { abierta: 'Abierta', en_proceso: 'En proceso', terminada: 'Terminada', entregada: 'Entregada', cancelada: 'Cancelada', anulada: 'Anulada' }
const historialFiltrado = computed(() => {
  if (filtroHist.value === 'abiertas')
    return historial.value.filter(o => ['abierta','en_proceso','terminada'].includes(o.estado))
  if (filtroHist.value === 'cerradas')
    return historial.value.filter(o => ['entregada','cancelada','anulada'].includes(o.estado))
  return historial.value
})

function irAOrden(id) { router.push(`/talleres/orden/${id}`) }
function imprimirOrden(o) {
  window.open(`/talleres/orden/${o.id}?print=1`, '_blank')
}

// ── Wizard nuevo vehículo ─────────────────────────────────────────────────
const wizardStep   = ref(1)
const anioActual   = new Date().getFullYear()
const NV_DEFAULT   = { tipo: '', marca: '', modelo: '', anio: '', color: '', km_actual: 0,
                       cliente_nombre: '', cliente_documento: '', cliente_telefono: '' }
const nuevoVehiculo = ref({ ...NV_DEFAULT })
const fotosNuevas   = ref([])
const loadingGuardar = ref(false)

function agregarFotoNueva(e) {
  for (const f of e.target.files) {
    const reader = new FileReader()
    reader.onload = ev => fotosNuevas.value.push({ file: f, preview: ev.target.result })
    reader.readAsDataURL(f)
  }
  e.target.value = ''
}

async function registrarVehiculo() {
  if (!nuevoVehiculo.value.cliente_nombre?.trim()) {
    mostrarToast('El nombre del propietario es requerido', 'error'); return
  }
  loadingGuardar.value = true
  try {
    const rv = await api.post('/api/talleres/vehiculo', {
      company_id:         companyId.value,
      placa:              placaInput.value,
      tipo:               nuevoVehiculo.value.tipo || tiposVehiculo.value[0]?.nombre || 'auto',
      marca:              nuevoVehiculo.value.marca,
      modelo:             nuevoVehiculo.value.modelo,
      anio:               nuevoVehiculo.value.anio || null,
      color:              nuevoVehiculo.value.color,
      km_actual:          nuevoVehiculo.value.km_actual || 0,
      cliente_nombre:     nuevoVehiculo.value.cliente_nombre,
      cliente_documento:  nuevoVehiculo.value.cliente_documento,
      cliente_telefono:   nuevoVehiculo.value.cliente_telefono,
    })
    const assetId = rv.data.asset_id

    // Subir fotos nuevas
    for (const f of fotosNuevas.value) {
      try {
        const fd = new FormData(); fd.append('file', f.file)
        const up = await api.post('/upload-image/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
        const url = up.data?.url || up.data?.photo_url
        if (url) {
          await api.post(`/api/talleres/vehiculo/${assetId}/fotos`, {
            company_id: companyId.value, photo_url: url, tipo: 'ingreso'
          })
        }
      } catch { /* continua con las demás fotos */ }
    }

    vehiculo.value = { asset_id: assetId, placa: placaInput.value, ...nuevoVehiculo.value }
    orden.value.km_ingreso = nuevoVehiculo.value.km_actual || ''
    wizardStep.value = 2
    mostrarToast('Vehículo registrado', 'ok')
  } catch (e) { mostrarToast(e?.response?.data?.detail ?? 'Error al registrar', 'error') }
  finally { loadingGuardar.value = false }
}

// ── Editar vehículo ───────────────────────────────────────────────────────
const showEditVehiculo = ref(false)
const editForm = ref({})
function abrirEditarVehiculo() {
  editForm.value = { ...vehiculo.value }
  showEditVehiculo.value = true
}
async function guardarVehiculo() {
  loadingGuardar.value = true
  try {
    await api.put(`/api/talleres/vehiculo/${vehiculo.value.asset_id}`, {
      company_id: companyId.value, ...editForm.value
    })
    vehiculo.value = { ...vehiculo.value, ...editForm.value }
    showEditVehiculo.value = false
    mostrarToast('Vehículo actualizado', 'ok')
  } catch (e) { mostrarToast(e?.response?.data?.detail ?? 'Error', 'error') }
  finally { loadingGuardar.value = false }
}

// ── Formulario orden ──────────────────────────────────────────────────────
const ORDEN_DEFAULT = { tipo_item: 'mecanica', km_ingreso: '', diagnostico: '',
                        jefe_responsable_id: '', operario_id: '', convenio_id: '', promesa_entrega: '' }
const orden = ref({ ...ORDEN_DEFAULT })

async function abrirOrden() {
  if (!vehiculo.value?.asset_id) { mostrarToast('Primero registra el vehículo', 'error'); return }
  loadingGuardar.value = true
  try {
    const workers_payload = []
    if (orden.value.operario_id)
      workers_payload.push({ worker_id: orden.value.operario_id, rol: orden.value.tipo_item })

    const { data } = await api.post('/api/talleres/ordenes', {
      company_id:          companyId.value,
      placa_vehiculo:      placaInput.value,
      vehicle_id:          vehiculo.value.asset_id,
      client_id:           vehiculo.value.client_id || null,
      convenio_id:         orden.value.convenio_id || null,
      km_ingreso:          orden.value.km_ingreso || null,
      jefe_responsable_id: orden.value.jefe_responsable_id || null,
      diagnostico:         orden.value.diagnostico,
      promesa_entrega:     orden.value.promesa_entrega || null,
      workers:             workers_payload,
    })
    mostrarToast(`Orden ${data.numero_orden} creada`, 'ok')
    setTimeout(() => router.push(`/talleres/orden/${data.id}`), 700)
  } catch (e) { mostrarToast(e?.response?.data?.detail ?? 'Error al crear la orden', 'error') }
  finally { loadingGuardar.value = false }
}

// ── Datos auxiliares ──────────────────────────────────────────────────────
const usuarios      = ref([])
const workers       = ref([])
const convenios     = ref([])
const tiposVehiculo = ref([])

async function cargarAuxiliares() {
  if (!companyId.value) return
  try {
    const [ru, rw, rc, rt] = await Promise.all([
      api.get('/users/', { params: { company_id: companyId.value } }),
      api.get('/workers/', { params: { company_id: companyId.value } }),
      api.get('/api/talleres/convenios', { params: { company_id: companyId.value } }),
      api.get('/api/talleres/tipos-vehiculo', { params: { company_id: companyId.value } }),
    ])
    usuarios.value      = ru.data?.items ?? ru.data ?? []
    workers.value       = rw.data?.items ?? rw.data ?? []
    convenios.value     = rc.data ?? []
    tiposVehiculo.value = rt.data ?? []
    if (tiposVehiculo.value.length) nuevoVehiculo.value.tipo = tiposVehiculo.value[0].nombre
  } catch { /* silencioso */ }
}

// ── Toast ─────────────────────────────────────────────────────────────────
const toast = ref({ visible: false, msg: '', tipo: 'ok' })
function mostrarToast(msg, tipo = 'ok') {
  toast.value = { visible: true, msg, tipo }
  setTimeout(() => { toast.value.visible = false }, 3500)
}

// ── Helpers ───────────────────────────────────────────────────────────────
function fmt(v) {
  return Number(v||0).toLocaleString('es-CO', { style:'currency', currency:'COP', minimumFractionDigits:0 })
}
function fmt0(v) { return Number(v||0).toLocaleString('es-CO') }
function fmtFecha(v) {
  if (!v) return '—'
  return new Date(v).toLocaleDateString('es-CO', { day:'2-digit', month:'short', year:'numeric' })
}

watch(companyId, (v) => { if (v) { cargarAuxiliares(); cargarOrdenes() } })
onMounted(() => { cargarAuxiliares(); cargarOrdenes(); nextTick(() => inputRef.value?.focus()) })
</script>

<style scoped>
.ordenes-page { padding: 20px; max-width: 960px; display: flex; flex-direction: column; gap: 16px; }

/* ── Órdenes activas ──────────────────────────────────────────────────── */
.ordenes-activas-card { background:#fff; border-radius:16px; box-shadow:0 2px 8px rgba(0,0,0,.07); overflow:hidden; }
.oa-head   { display:flex; align-items:center; justify-content:space-between; padding:14px 18px; border-bottom:1.5px solid #f1f5f9; flex-wrap:wrap; gap:10px; }
.oa-titulo { display:flex; align-items:center; gap:8px; font-size:15px; font-weight:700; color:#1e293b; }
.oa-titulo .bi { color:#3b82f6; font-size:16px; }
.oa-badge  { background:#1e3a5f; color:#fff; border-radius:20px; font-size:11px; padding:2px 8px; font-weight:700; }
.oa-filtros { display:flex; gap:4px; flex-wrap:wrap; }
.oa-flt    { padding:5px 11px; border-radius:20px; border:1.5px solid #e2e8f0; background:#f8fafc; color:#475569; font-size:12px; font-weight:600; cursor:pointer; transition:all .12s; }
.oa-flt.active { background:#1e3a5f; color:#fff; border-color:#1e3a5f; }
.oa-flt:hover:not(.active) { background:#eff6ff; border-color:#bfdbfe; color:#1d4ed8; }
.oa-loading { display:flex; align-items:center; gap:8px; padding:30px; justify-content:center; color:#94a3b8; font-size:14px; }
.oa-empty  { display:flex; flex-direction:column; align-items:center; gap:8px; padding:40px; color:#94a3b8; }
.oa-empty .bi { font-size:36px; color:#e2e8f0; }
.oa-empty p   { font-size:13px; margin:0; }
.oa-table-wrap { overflow-x:auto; }
.oa-table  { width:100%; border-collapse:collapse; font-size:13px; }
.oa-table thead tr { background:#f8fafc; }
.oa-table th { padding:10px 14px; text-align:left; font-size:11px; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:.4px; border-bottom:1.5px solid #e2e8f0; white-space:nowrap; }
.oa-table td { padding:10px 14px; border-bottom:1px solid #f1f5f9; vertical-align:middle; }
.oa-row    { cursor:pointer; transition:background .1s; }
.oa-row:hover { background:#f0f9ff; }
.oa-num    { font-family:monospace; font-size:12px; color:#64748b; font-weight:600; white-space:nowrap; }
.oa-placa  { font-size:15px; font-weight:900; letter-spacing:2px; color:#1e293b; }
.oa-fecha  { font-size:12px; color:#94a3b8; white-space:nowrap; }
.oa-jefe   { font-size:12px; color:#475569; }
.oa-total  { font-weight:700; color:#1e293b; white-space:nowrap; }
.ta-r      { text-align:right; }
.oa-btn-open { width:30px; height:30px; border-radius:7px; border:none; font-size:14px; cursor:pointer; display:flex; align-items:center; justify-content:center; }
.oa-btn-edit { background:#eff6ff; color:#1d4ed8; }
.oa-btn-edit:hover { background:#1d4ed8; color:#fff; }
.oa-btn-view { background:#f0fdf4; color:#059669; }
.oa-btn-view:hover { background:#059669; color:#fff; }
.estado-badge { font-size:10px; font-weight:700; padding:3px 8px; border-radius:20px; white-space:nowrap; }
.es-abierta    { background:#dbeafe; color:#1d4ed8; }
.es-en_proceso { background:#fef3c7; color:#92400e; }
.es-terminada  { background:#dcfce7; color:#166534; }
.es-entregada  { background:#f1f5f9; color:#64748b; }
.es-cancelada  { background:#fee2e2; color:#b91c1c; }
.es-anulada    { background:#fef3c7; color:#92400e; }
.oa-paginacion { display:flex; align-items:center; justify-content:center; gap:12px; padding:12px; border-top:1px solid #f1f5f9; }
.pag-btn  { width:32px; height:32px; border-radius:8px; border:1.5px solid #e2e8f0; background:#f8fafc; cursor:pointer; color:#475569; display:flex; align-items:center; justify-content:center; }
.pag-btn:hover:not(:disabled) { background:#eff6ff; color:#1d4ed8; }
.pag-btn:disabled { opacity:.4; cursor:not-allowed; }
.pag-info { font-size:13px; font-weight:600; color:#475569; }

/* Buscador */
.buscar-card { background:#fff; border-radius:16px; padding:20px; box-shadow:0 2px 8px rgba(0,0,0,.07); }
.buscar-inner { display:flex; align-items:center; gap:14px; margin-bottom:14px; }
.buscar-icon-wrap { width:46px; height:46px; background:#eff6ff; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:22px; color:#3b82f6; flex-shrink:0; }
.buscar-texts h5 { font-size:15px; font-weight:700; color:#1e293b; margin:0 0 2px; }
.buscar-texts p  { font-size:12px; color:#64748b; margin:0; }
.buscar-row { display:flex; gap:8px; align-items:center; }
.placa-input { flex:1; font-size:18px; font-weight:800; letter-spacing:3px; text-transform:uppercase; padding:10px 14px; border:2px solid #e2e8f0; border-radius:10px; outline:none; color:#1e293b; }
.placa-input:focus { border-color:#3b82f6; }
.btn-buscar  { display:inline-flex; align-items:center; gap:6px; padding:10px 20px; background:#3b82f6; color:#fff; border:none; border-radius:10px; font-size:14px; font-weight:700; cursor:pointer; }
.btn-buscar:hover:not(:disabled) { background:#2563eb; }
.btn-buscar:disabled { opacity:.5; cursor:not-allowed; }
.btn-limpiar { width:40px; height:40px; border:1.5px solid #e2e8f0; background:#f8fafc; border-radius:9px; cursor:pointer; color:#64748b; font-size:14px; display:flex; align-items:center; justify-content:center; }
.btn-limpiar:hover { background:#fee2e2; border-color:#fca5a5; color:#dc2626; }

/* Vehículo encontrado */
.vehiculo-card.found { background:#fff; border-radius:14px; border:2px solid #86efac; padding:16px; box-shadow:0 2px 8px rgba(0,0,0,.06); }
.vc-top   { display:flex; align-items:flex-start; gap:12px; }
.vc-avatar { width:44px; height:44px; background:#dcfce7; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:22px; color:#16a34a; flex-shrink:0; }
.vc-datos { flex:1; }
.vc-placa-row { display:flex; align-items:center; gap:8px; }
.vc-placa  { font-size:20px; font-weight:900; letter-spacing:2px; color:#1e293b; }
.vc-tipo-badge { background:#eff6ff; color:#1d4ed8; font-size:10px; font-weight:700; padding:2px 8px; border-radius:20px; }
.vc-desc   { font-size:13px; color:#475569; margin-top:3px; }
.vc-meta   { display:flex; gap:10px; font-size:12px; color:#94a3b8; margin-top:3px; }
.vc-propietario { display:flex; align-items:center; gap:8px; margin-top:10px; padding-top:10px; border-top:1px solid #f0fdf4; font-size:13px; color:#374151; flex-wrap:wrap; }
.vc-doc, .vc-tel { color:#94a3b8; }
.vc-actions { flex-shrink:0; }
.btn-edit-v { width:34px; height:34px; border:1.5px solid #e2e8f0; background:#f8fafc; border-radius:8px; cursor:pointer; color:#3b82f6; font-size:13px; display:flex; align-items:center; justify-content:center; }
.btn-edit-v:hover { background:#eff6ff; border-color:#bfdbfe; }

/* Fotos vehículo */
.vc-fotos { display:flex; gap:8px; flex-wrap:wrap; margin-top:10px; padding-top:10px; border-top:1px solid #f0fdf4; }
.foto-thumb { position:relative; width:70px; height:70px; border-radius:8px; overflow:hidden; border:1.5px solid #e2e8f0; }
.foto-thumb img { width:100%; height:100%; object-fit:cover; }
.foto-tipo-badge { position:absolute; bottom:0; left:0; right:0; background:rgba(0,0,0,.5); color:#fff; font-size:9px; text-align:center; padding:2px; }
.foto-del { position:absolute; top:2px; right:2px; width:18px; height:18px; background:rgba(220,38,38,.8); border:none; border-radius:50%; color:#fff; font-size:10px; cursor:pointer; display:flex; align-items:center; justify-content:center; }
.foto-add { display:flex; flex-direction:column; align-items:center; justify-content:center; width:70px; height:70px; border-radius:8px; border:2px dashed #bfdbfe; background:#f0f9ff; color:#3b82f6; font-size:11px; gap:3px; cursor:pointer; }
.foto-add i { font-size:18px; }
.foto-file-input { display:none; }

/* Tabs */
.tabs-bar  { display:flex; gap:4px; border-bottom:2px solid #e2e8f0; }
.tab-btn   { display:flex; align-items:center; gap:7px; padding:10px 18px; font-size:13px; font-weight:700; background:none; border:none; cursor:pointer; color:#64748b; border-bottom:3px solid transparent; margin-bottom:-2px; transition:all .15s; }
.tab-btn:hover  { color:#1e3a5f; background:#f8fafc; border-radius:8px 8px 0 0; }
.tab-btn.active { color:#1e3a5f; border-bottom-color:#1e3a5f; }
.tab-count { background:#1e3a5f; color:#fff; border-radius:20px; font-size:10px; padding:1px 6px; }

/* Form card */
.form-card { background:#fff; border-radius:14px; padding:20px; box-shadow:0 2px 8px rgba(0,0,0,.07); }
.form-section-title { font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.5px; color:#64748b; display:flex; align-items:center; gap:6px; padding-bottom:8px; border-bottom:1px solid #f1f5f9; margin-bottom:12px; }
.form-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.fg        { display:flex; flex-direction:column; gap:4px; }
.fg label  { font-size:12px; font-weight:600; color:#374151; }
.span2     { grid-column: span 2; }
.form-ctrl { border:1.5px solid #e2e8f0; border-radius:8px; padding:8px 10px; font-size:13px; color:#1e293b; outline:none; background:#fff; width:100%; box-sizing:border-box; }
.form-ctrl:focus { border-color:#3b82f6; }
textarea.form-ctrl { resize:vertical; }
.form-actions { display:flex; justify-content:flex-end; gap:8px; margin-top:16px; padding-top:14px; border-top:1px solid #f1f5f9; }

/* Fotos upload (nuevo vehículo) */
.fotos-upload-area { display:flex; gap:8px; flex-wrap:wrap; }
.foto-preview { position:relative; width:80px; height:80px; border-radius:8px; overflow:hidden; border:1.5px solid #e2e8f0; }
.foto-preview img { width:100%; height:100%; object-fit:cover; }
.foto-add-btn { display:flex; flex-direction:column; align-items:center; justify-content:center; width:80px; height:80px; border-radius:8px; border:2px dashed #bfdbfe; background:#f0f9ff; color:#3b82f6; font-size:11px; gap:4px; cursor:pointer; }
.foto-add-btn i { font-size:20px; }

/* Historial */
.historial-section { background:#fff; border-radius:14px; padding:16px; box-shadow:0 2px 8px rgba(0,0,0,.07); }
.hist-filtros { display:flex; gap:6px; margin-bottom:12px; }
.hf-btn { padding:5px 14px; border-radius:20px; border:1.5px solid #e2e8f0; background:#f8fafc; font-size:12px; font-weight:600; color:#64748b; cursor:pointer; }
.hf-btn.active { background:#1e3a5f; color:#fff; border-color:#1e3a5f; }
.hist-list { display:flex; flex-direction:column; gap:8px; }
.hist-item { display:flex; align-items:center; gap:10px; padding:12px 14px; border-radius:10px; border:1.5px solid #e2e8f0; background:#f8fafc; flex-wrap:wrap; }
.hist-item.hs-abierta    { border-left:4px solid #3b82f6; }
.hist-item.hs-en_proceso { border-left:4px solid #f59e0b; }
.hist-item.hs-terminada  { border-left:4px solid #22c55e; }
.hist-item.hs-entregada  { border-left:4px solid #94a3b8; }
.hist-item.hs-cancelada  { border-left:4px solid #ef4444; opacity:.6; }
.hi-left   { display:flex; align-items:center; gap:8px; flex:1; min-width:150px; }
.hi-num    { font-size:13px; font-weight:800; color:#1e293b; }
.hi-badge  { font-size:10px; font-weight:700; padding:2px 8px; border-radius:20px; }
.hb-abierta    { background:#dbeafe; color:#1d4ed8; } .hb-en_proceso { background:#fef3c7; color:#92400e; }
.hb-terminada  { background:#dcfce7; color:#16a34a; } .hb-entregada  { background:#f1f5f9; color:#64748b; }
.hb-cancelada  { background:#fee2e2; color:#b91c1c; }
.hb-anulada    { background:#fef3c7; color:#92400e; }
.hi-fecha  { font-size:11px; color:#94a3b8; }
.hi-center { display:flex; align-items:center; gap:10px; flex:1; font-size:12px; color:#64748b; }
.hi-total  { font-weight:700; color:#1e293b; }
.hi-actions { display:flex; gap:6px; }
.btn-hist-edit  { display:inline-flex; align-items:center; gap:4px; padding:5px 12px; background:#eff6ff; color:#1d4ed8; border:1.5px solid #bfdbfe; border-radius:7px; font-size:12px; font-weight:600; cursor:pointer; }
.btn-hist-print { width:30px; height:30px; background:#f8fafc; border:1.5px solid #e2e8f0; border-radius:7px; display:flex; align-items:center; justify-content:center; cursor:pointer; color:#64748b; font-size:13px; }
.btn-hist-print:hover { background:#f0fdf4; color:#16a34a; border-color:#bbf7d0; }
.hist-empty { display:flex; flex-direction:column; align-items:center; gap:6px; padding:28px; color:#94a3b8; text-align:center; }
.hist-empty .bi { font-size:32px; color:#e2e8f0; }
.hist-empty p { font-size:13px; margin:0; }

/* Wizard pasos */
.wizard-steps { display:flex; align-items:center; gap:0; background:#fff; border-radius:12px; padding:14px 20px; box-shadow:0 2px 8px rgba(0,0,0,.06); }
.wstep { display:flex; align-items:center; gap:8px; }
.ws-num { width:28px; height:28px; border-radius:50%; background:#e2e8f0; color:#64748b; font-size:13px; font-weight:800; display:flex; align-items:center; justify-content:center; }
.ws-label { font-size:13px; font-weight:600; color:#64748b; }
.wstep.active .ws-num  { background:#3b82f6; color:#fff; }
.wstep.active .ws-label { color:#1e293b; }
.wstep.done .ws-num  { background:#22c55e; color:#fff; }
.ws-line { flex:1; height:2px; background:#e2e8f0; margin:0 12px; }

/* Modal */
.modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,.45); display:flex; align-items:center; justify-content:center; z-index:2000; padding:16px; }
.modal-box { background:#fff; border-radius:16px; width:100%; max-width:540px; max-height:90vh; display:flex; flex-direction:column; box-shadow:0 20px 60px rgba(0,0,0,.2); }
.mh  { display:flex; align-items:center; justify-content:space-between; padding:16px 20px; border-bottom:1px solid #f1f5f9; }
.mh h3 { font-size:14px; font-weight:700; color:#1e293b; margin:0; display:flex; align-items:center; gap:7px; }
.btn-x { background:none; border:none; font-size:16px; cursor:pointer; color:#94a3b8; }
.mb-area { padding:18px 20px; overflow-y:auto; }
.mf { padding:12px 20px 16px; display:flex; justify-content:flex-end; gap:8px; border-top:1px solid #f1f5f9; }

/* Btn */
.btn { display:inline-flex; align-items:center; gap:6px; padding:9px 18px; border-radius:9px; font-size:13px; font-weight:700; cursor:pointer; border:none; }
.btn-primary   { background:#3b82f6; color:#fff; } .btn-primary:hover { background:#2563eb; }
.btn-primary:disabled { opacity:.6; cursor:not-allowed; }
.btn-secondary { border:1.5px solid #e2e8f0; background:#fff; color:#64748b; }
.btn-sm { padding:6px 12px; font-size:12px; }
.spin { display:inline-block; animation:spin .8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

/* Toast */
.toast-msg { position:fixed; bottom:24px; right:24px; z-index:9999; display:flex; align-items:center; gap:8px; padding:12px 20px; border-radius:12px; font-size:13px; font-weight:600; box-shadow:0 8px 24px rgba(0,0,0,.15); }
.toast-ok    { background:#1e293b; color:#fff; }
.toast-error { background:#dc2626; color:#fff; }

/* Responsive */
@media (max-width: 768px) {
  .ordenes-page { padding: 12px; }
  .form-grid    { grid-template-columns: 1fr; }
  .span2        { grid-column: span 1; }
  .hist-item    { flex-direction: column; align-items: flex-start; gap: 6px; }
}
@media (max-width: 480px) {
  .buscar-row   { flex-wrap: wrap; }
  .placa-input  { font-size: 15px; letter-spacing: 2px; }
  .wizard-steps { padding: 10px 12px; }
  .ws-label     { display: none; }
}
</style>
