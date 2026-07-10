<template>
  <div class="od-page">

    <!-- ── Header fijo ───────────────────────────────────────────────── -->
    <div class="od-header">
      <button class="btn-back" @click="router.push('/talleres/ordenes')" title="Volver">
        <i class="bi bi-arrow-left"></i>
      </button>
      <div class="od-titulo">
        <span class="od-num">{{ orden?.numero_orden ?? '...' }}</span>
        <span :class="['es-badge', `es-${orden?.estado}`]">{{ estadoLabel(orden?.estado) }}</span>
        <span v-if="orden?.placa_vehiculo" class="od-placa">{{ orden.placa_vehiculo }}</span>
      </div>
      <div class="od-totales-mini" v-if="orden">
        <span class="tot-mini"><i class="bi bi-currency-dollar"></i>{{ fmt(totales.total) }}</span>
        <button class="btn-imprimir" onclick="window.print()" title="Imprimir">
          <i class="bi bi-printer"></i>
        </button>
      </div>
    </div>

    <div v-if="loadingOrden" class="od-loading">
      <i class="bi bi-arrow-repeat spin"></i> Cargando orden…
    </div>

    <template v-else-if="orden">
      <!-- ── Tabs ───────────────────────────────────────────────────── -->
      <div class="od-tabs">
        <button :class="['od-tab', { active: tab === 'editar' }]" @click="tab='editar'">
          <i class="bi bi-pencil-square"></i> Editar Orden
        </button>
        <button :class="['od-tab', { active: tab === 'historial' }]" @click="tab='historial'; cargarHistorial()">
          <i class="bi bi-clock-history"></i> Historial
        </button>
      </div>

      <!-- ════════════ TAB: EDITAR ORDEN ════════════════════════════ -->
      <div v-if="tab === 'editar'" class="tab-body">

        <!-- ▸ Acordeón: Datos del Vehículo -->
        <div class="acord-block">
          <button class="acord-head" @click="toggle('vehiculo')">
            <div class="acord-title"><i class="bi bi-car-front-fill"></i> Datos del Vehículo</div>
            <div class="acord-actions">
              <button class="acord-btn-add" @click.stop="router.push('/configuration/assets')" title="Gestionar vehículos">
                <i class="bi bi-plus-lg"></i>
              </button>
              <i :class="open.has('vehiculo') ? 'bi bi-chevron-up' : 'bi bi-chevron-down'" style="flex-shrink:0"></i>
            </div>
          </button>
          <div v-if="open.has('vehiculo')" class="acord-body">
            <!-- Fotos del vehículo -->
            <div v-if="fotos.length" class="fotos-strip">
              <div v-for="f in fotos" :key="f.id" class="foto-thumb" @click="fotoZoom = f.file_url">
                <img v-if="f.file_type === 'image'" :src="f.file_url" :alt="f.file_name" />
                <div v-else class="foto-video"><i class="bi bi-play-circle-fill"></i></div>
              </div>
            </div>
            <div class="form-grid">
              <div class="fg"><label>Placa</label>
                <div class="fc-display">{{ editForm.placa_vehiculo || '—' }}</div></div>
              <div class="fg"><label>Tipo</label>
                <div class="fc-display">{{ vehiculoExt.tipo || '—' }}</div></div>
              <div class="fg"><label>Marca</label>
                <div class="fc-display">{{ vehiculoExt.marca || '—' }}</div></div>
              <div class="fg"><label>Modelo</label>
                <div class="fc-display">{{ vehiculoExt.modelo || '—' }}</div></div>
              <div class="fg"><label>Año</label>
                <div class="fc-display">{{ vehiculoExt.anio || '—' }}</div></div>
              <div class="fg"><label>Color</label>
                <div class="fc-display">{{ vehiculoExt.color || '—' }}</div></div>
              <div class="fg"><label>Km Ingreso</label>
                <input v-model.number="editForm.km_ingreso" type="number" class="fc" placeholder="0" /></div>
              <div class="fg"><label>Km Salida</label>
                <input v-model.number="editForm.km_salida" type="number" class="fc" placeholder="0" /></div>
            </div>
          </div>
        </div>

        <!-- ▸ Acordeón: Datos del Cliente -->
        <div class="acord-block">
          <button class="acord-head" @click="toggle('cliente')">
            <div class="acord-title">
              <i class="bi bi-person-fill"></i> Datos del Cliente
              <span v-if="clienteSeleccionado" class="acord-sub">{{ clienteSeleccionado.name }}</span>
            </div>
            <div class="acord-actions">
              <button class="acord-btn-add" @click.stop="router.push('/configuration/clients')" title="Gestionar clientes">
                <i class="bi bi-plus-lg"></i>
              </button>
              <i :class="open.has('cliente') ? 'bi bi-chevron-up' : 'bi bi-chevron-down'" style="flex-shrink:0"></i>
            </div>
          </button>
          <div v-if="open.has('cliente')" class="acord-body">
            <!-- Buscador de cliente -->
            <div class="client-search-wrap">
              <label class="fg-label">Buscar / Cambiar Cliente</label>
              <div class="search-wrap">
                <input
                  v-model="clienteBusqueda"
                  class="fc"
                  placeholder="Nombre, documento o teléfono…"
                  @input="filtrarClientes"
                  @keydown.esc="clienteResultados=[]"
                />
                <i v-if="clienteSeleccionado" class="bi bi-check-circle-fill abs-ok"></i>
              </div>
              <div v-if="clienteResultados.length" class="search-results">
                <div v-for="c in clienteResultados" :key="c.id" class="sr-item" @click="seleccionarCliente(c)">
                  <span class="sr-name">{{ c.name }}</span>
                  <span class="sr-code">{{ c.document_number || '' }}</span>
                  <span class="sr-extra">{{ c.phone || '' }}</span>
                </div>
              </div>
            </div>
            <!-- Datos del cliente -->
            <div class="form-grid mt8">
              <div class="fg span2"><label>Nombre</label>
                <div class="fc-display">{{ clienteSeleccionado?.name || orden.cliente_nombre || '—' }}</div></div>
              <div class="fg"><label>Documento</label>
                <div class="fc-display">{{ clienteSeleccionado?.document_number || orden.cliente_documento || '—' }}</div></div>
              <div class="fg"><label>Teléfono</label>
                <div class="fc-display">{{ clienteSeleccionado?.phone || orden.cliente_telefono || '—' }}</div></div>
              <div class="fg span2" v-if="orden.convenio_nombre || editForm.convenio_id">
                <label>Convenio empresarial</label>
                <div class="fc-display">{{ orden.convenio_nombre || '—' }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- ▸ Acordeón: Encabezado de la Orden -->
        <div class="acord-block">
          <button class="acord-head" @click="toggle('encabezado')">
            <div class="acord-title"><i class="bi bi-clipboard2-fill"></i> Encabezado de la Orden</div>
            <i :class="open.has('encabezado') ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
          </button>
          <div v-if="open.has('encabezado')" class="acord-body">
            <div class="form-grid">
              <div class="fg"><label>Fecha Ingreso</label>
                <div class="fc-display">{{ fmtFecha(orden.fecha_ingreso) }}</div></div>
              <div class="fg"><label>Promesa de Entrega</label>
                <CustomDatePicker v-model="editForm.promesa_entrega" /></div>
              <div class="fg"><label>Jefe Responsable</label>
                <select v-model="editForm.jefe_responsable_id" class="fc">
                  <option :value="null">— Sin asignar —</option>
                  <option v-for="w in workers" :key="w.id" :value="w.id">
                    {{ w.name }}{{ w.profession_nombre ? ' · ' + w.profession_nombre : '' }}
                  </option>
                </select></div>
              <div class="fg"><label>Convenio</label>
                <select v-model="editForm.convenio_id" class="fc">
                  <option :value="null">— Particular —</option>
                  <option v-for="c in convenios" :key="c.id" :value="c.id">{{ c.nombre_empresa }}</option>
                </select></div>
              <div class="fg span2"><label>Diagnóstico / Descripción del servicio</label>
                <textarea v-model="editForm.diagnostico" class="fc" rows="3"></textarea></div>
              <div class="fg span2"><label>Trabajo realizado</label>
                <textarea v-model="editForm.trabajo_realizado" class="fc" rows="3"></textarea></div>
            </div>
          </div>
        </div>

        <!-- ▸ Acordeón: Detalle de la Orden -->
        <div class="acord-block">
          <button class="acord-head" @click="toggle('detalle')">
            <div class="acord-title">
              <i class="bi bi-list-check"></i> Detalle de la Orden
              <span class="det-cnt">{{ detalles.length }} ítems · {{ fmt(totales.total) }}</span>
            </div>
            <i :class="open.has('detalle') ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
          </button>
          <div v-if="open.has('detalle')" class="acord-body">

            <!-- Totales bar -->
            <div class="totales-row">
              <div class="tc"><span class="tc-l">Servicios</span><span class="tc-v">{{ fmt(totales.servicios) }}</span></div>
              <div class="tc"><span class="tc-l">Productos</span><span class="tc-v">{{ fmt(totales.repuestos) }}</span></div>
              <div class="tc hl"><span class="tc-l">TOTAL</span><span class="tc-v">{{ fmt(totales.total) }}</span></div>
              <div class="tc mo"><span class="tc-l">Mano de Obra</span><span class="tc-v">{{ fmt(totales.mano_obra) }}</span></div>
            </div>

            <!-- Lista de ítems -->
            <div v-if="detalles.length === 0" class="det-empty">
              <i class="bi bi-inbox"></i> Sin ítems. Agrega servicios o productos abajo.
            </div>
            <div v-else class="detalles-list">
              <div v-for="d in detalles" :key="d.id" :class="['dr', d.tipo_item === 'repuesto' ? 'dr-producto' : 'dr-servicio']">
                <span :class="['dr-tipo', d.tipo_item === 'repuesto' ? 'dt-repuesto' : 'dt-servicio']">
                  {{ d.tipo_item === 'repuesto' ? 'Producto' : 'Servicio' }}
                </span>
                <div class="dr-names">
                  <span class="dr-name">{{ d.nombre }}</span>
                  <span v-if="d.worker_nombre || d.operario_nombre" class="dr-worker">
                    <i class="bi bi-person-badge"></i> {{ d.worker_nombre ?? d.operario_nombre }}
                  </span>
                </div>
                <div class="dr-nums">
                  <span v-if="d.tipo_item === 'repuesto'">{{ d.cantidad }} u</span>
                  <span>{{ fmt(d.precio_unitario) }}</span>
                  <span class="dr-sub">{{ fmt(d.subtotal) }}</span>
                  <span v-if="d.mano_obra_operario > 0" class="dr-mo">
                    <i class="bi bi-person-fill"></i> {{ fmt(d.mano_obra_operario) }}
                  </span>
                </div>
                <button v-if="!d.liq_estado || d.liq_estado === 'pendiente'"
                  class="dr-del" @click="eliminarDetalle(d)" :disabled="eliminandoId===d.id">
                  <i v-if="eliminandoId===d.id" class="bi bi-hourglass-split spin"></i>
                  <i v-else class="bi bi-trash3"></i>
                </button>
              </div>
            </div>

            <!-- Formulario agregar ítem -->
            <div class="add-item-form">
              <div class="aif-title"><i class="bi bi-plus-circle-fill"></i> Agregar Servicio / Producto</div>

              <!-- Solo 2 opciones: SERVICIOS / PRODUCTOS -->
              <div class="tipo-btns">
                <button :class="['tipo-btn', { active: modoTipo === 'servicio' }]"
                  @click="modoTipo='servicio'; limpiarProducto()">
                  <i class="bi bi-tools"></i> Servicios
                </button>
                <button :class="['tipo-btn', { active: modoTipo === 'producto' }]"
                  @click="modoTipo='producto'; limpiarProducto()">
                  <i class="bi bi-box-seam"></i> Productos
                </button>
              </div>

              <!-- Buscador -->
              <div class="search-wrap mt8">
                <input v-model="busqueda" class="fc"
                  :placeholder="modoTipo === 'servicio'
                    ? 'Buscar servicio por nombre o código…'
                    : 'Buscar producto por nombre o código…'"
                  @input="buscarProductos" @keydown.esc="resultados=[]" />
                <i v-if="buscando" class="bi bi-hourglass-split spin abs-spin"></i>
              </div>
              <div v-if="resultados.length" class="search-results">
                <div v-for="r in resultados" :key="r.id" class="sr-item" @click="seleccionarProducto(r)">
                  <span class="sr-name">{{ r.name }}</span>
                  <span class="sr-code">{{ r.code }}</span>
                  <span class="sr-extra">{{ fmt(r.base_price) }}</span>
                </div>
              </div>

              <!-- Ítem seleccionado -->
              <div v-if="itemForm.producto_id" class="prod-sel">
                <div class="ps-info">
                  <span class="ps-name">{{ itemForm.producto_nombre }}</span>
                  <span class="ps-price">{{ fmt(itemForm.precio_unitario) }}</span>
                </div>
                <button @click="limpiarProducto" class="ps-del"><i class="bi bi-x-lg"></i></button>
              </div>

              <div v-if="itemForm.producto_id" class="form-grid mt8">
                <!-- Cantidad: solo productos -->
                <div class="fg" v-if="modoTipo === 'producto'">
                  <label>Cantidad</label>
                  <input v-model.number="itemForm.cantidad" type="number" min="1" step="1" class="fc" />
                </div>

                <!-- Subtotal / valor -->
                <div class="fg">
                  <label>{{ modoTipo === 'producto' ? 'Subtotal' : 'Valor del servicio' }}</label>
                  <div class="fc-display green">{{ fmt(subtotalItem) }}</div>
                </div>

                <!-- Operario: solo servicios -->
                <div class="fg span2" v-if="modoTipo === 'servicio'">
                  <label>Operario responsable</label>
                  <select v-model="itemForm.worker_id" class="fc">
                    <option :value="null">— Sin asignar —</option>
                    <option v-for="w in workers" :key="w.id" :value="w.id">
                      {{ w.name }}{{ w.profession_nombre ? ' · ' + w.profession_nombre : '' }}
                    </option>
                  </select>
                </div>
              </div>

              <button v-if="itemForm.producto_id"
                class="btn-agregar" :disabled="!puedeAgregar || agregando" @click="agregarDetalle">
                <i v-if="agregando" class="bi bi-hourglass-split spin"></i>
                <i v-else class="bi bi-plus-lg"></i>
                Agregar al detalle
              </button>
            </div>

          </div>
        </div>

        <!-- ── Botones de acción ──────────────────────────────────── -->
        <div class="action-bar" v-if="orden.estado !== 'cancelada' && orden.estado !== 'anulada'">
          <button class="btn-save" :disabled="guardando" @click="guardarCambios">
            <i v-if="guardando" class="bi bi-hourglass-split spin"></i>
            <i v-else class="bi bi-floppy-fill"></i>
            Guardar Cambios
          </button>

          <!-- Comprobante de ingreso: siempre disponible -->
          <button class="btn-comprobante" @click="showComprobante = true">
            <i class="bi bi-printer-fill"></i>
            Comprobante
          </button>

          <template v-if="orden.estado !== 'entregada'">
            <!-- Recibo (siempre disponible) -->
            <button class="btn-recibo" @click="showFacturarRecibo = true" :disabled="!detalles.length">
              <i class="bi bi-receipt-cutoff"></i>
              Recibo
            </button>

            <!-- PE: siempre visible; habilitado solo si la empresa tiene PE activo -->
            <button
              class="btn-facturar-pe"
              :disabled="!billingConfig.has_pos_electronico"
              :title="billingConfig.has_pos_electronico ? 'Factura Electrónica' : 'Esta empresa no tiene facturación electrónica habilitada'"
            >
              <i class="bi bi-file-earmark-text-fill"></i>
              Factura PE
            </button>
          </template>
          <div v-else class="badge-entregada">
            <i class="bi bi-check-circle-fill"></i> Entregada
          </div>

          <button class="btn-cancelar" @click="anularOrden" v-if="orden.estado !== 'anulada'">
            <i class="bi bi-slash-circle-fill"></i>
            Anular Orden
          </button>
        </div>
        <div class="action-bar" v-else>
          <div class="orden-cancelada-msg">
            <i class="bi bi-slash-circle-fill"></i>
            Orden {{ orden.estado === 'anulada' ? 'anulada' : 'cancelada' }}
          </div>
        </div>

      </div><!-- /tab editar -->

      <!-- ════════════ TAB: HISTORIAL ════════════════════════════════ -->
      <div v-if="tab === 'historial'" class="tab-body">
        <div class="hist-subtabs">
          <button :class="['hs-tab', { active: subTab==='placa' }]" @click="switchSubTab('placa')">
            <i class="bi bi-car-front-fill"></i> Esta Placa ({{ orden.placa_vehiculo }})
          </button>
          <button :class="['hs-tab', { active: subTab==='cliente' }]"
            :disabled="!orden.client_id"
            @click="switchSubTab('cliente')">
            <i class="bi bi-person-fill"></i> Este Cliente
            <span v-if="!orden.client_id" class="hs-nodato">(sin cliente)</span>
          </button>
        </div>

        <div v-if="loadingHist" class="od-loading"><i class="bi bi-arrow-repeat spin"></i> Cargando…</div>
        <div v-else-if="histItems.length === 0" class="od-empty">
          <i class="bi bi-inbox"></i><p>Sin historial registrado</p>
        </div>
        <div v-else class="hist-table-wrap">
          <table class="hist-table">
            <thead>
              <tr>
                <th v-if="subTab==='cliente'">Placa</th>
                <th>Orden</th>
                <th>Fecha</th>
                <th>Estado</th>
                <th>Jefe</th>
                <th class="ta-r">Total</th>
                <th class="ta-c">Ítems</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="h in histItems" :key="h.id" class="hist-row">
                <td v-if="subTab==='cliente'" class="h-placa">{{ h.placa_vehiculo }}</td>
                <td class="h-num">{{ h.numero_orden }}</td>
                <td class="h-fecha">{{ fmtFecha(h.fecha_ingreso) }}</td>
                <td><span :class="['es-badge', `es-${h.estado}`]">{{ estadoLabel(h.estado) }}</span></td>
                <td class="h-jefe">{{ h.jefe_nombre || '—' }}</td>
                <td class="ta-r h-tot">{{ fmt(h.total_orden) }}</td>
                <td class="ta-c h-cnt">{{ h.cant_items }}</td>
                <td>
                  <button class="h-btn" @click="router.push(`/talleres/orden/${h.id}`)" title="Ver/Editar">
                    <i class="bi bi-arrow-right-circle-fill"></i>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div><!-- /tab historial -->

    </template>

    <!-- Modal: Comprobante de Ingreso -->
    <ComprobanteIngreso
      v-if="showComprobante && orden"
      :orden="{ ...orden, ...vehiculoExt }"
      :detalles="detalles"
      :workers="ordenWorkers"
      :company-name="companyName"
      @close="showComprobante = false"
    />

    <!-- Modal: Registrar Recibo -->
    <FacturarRecibo
      v-if="showFacturarRecibo && orden"
      :orden-id="Number(ordenId)"
      :orden-numero="orden.numero_orden"
      :items="itemsParaFacturar"
      :company-id="companyId"
      @success="onReciboSuccess"
      @close="showFacturarRecibo = false"
    />

    <!-- Modal: Imprimir Recibo -->
    <ImprimirRecibo
      v-if="showImprimirRecibo && reciboData"
      :receipt-data="reciboData"
      :placa="orden?.placa_vehiculo || ''"
      :company-id="companyId"
      @close="onImprimirClose"
    />

    <!-- Zoom foto -->
    <Teleport to="body">
      <div v-if="fotoZoom" class="foto-overlay" @click="fotoZoom=null">
        <img :src="fotoZoom" class="foto-zoom-img" />
        <button class="foto-close" @click="fotoZoom=null"><i class="bi bi-x-lg"></i></button>
      </div>
    </Teleport>

    <!-- Toast -->
    <Teleport to="body">
      <div v-if="toast.visible" :class="['toast-msg', `toast-${toast.tipo}`]">
        <i :class="toast.tipo==='ok' ? 'bi bi-check-circle-fill' : 'bi bi-exclamation-triangle-fill'"></i>
        {{ toast.msg }}
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCompanyStore } from '@/stores/companyStore'
import api from '@/services/apis'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'
import FacturarRecibo from '@/components/billing/FacturarRecibo.vue'
import ImprimirRecibo from '@/components/billing/ImprimirRecibo.vue'
import ComprobanteIngreso from '@/components/talleres/ComprobanteIngreso.vue'
import { showConfirm } from '@/utils/toast'

const route        = useRoute()
const router       = useRouter()
const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id)
const billingConfig      = computed(() => companyStore.billingConfig)
const companyName        = computed(() => companyStore.selectedCompany?.name || '')
const showFacturarRecibo = ref(false)
const showImprimirRecibo = ref(false)
const showComprobante    = ref(false)
const reciboData         = ref(null)
const ordenWorkers       = ref([])
const ordenId      = computed(() => route.params.id)

// ── Acordeón ─────────────────────────────────────────────────────────────────
const open = ref(new Set(['detalle', 'encabezado']))
function toggle(sec) {
  const s = new Set(open.value)
  s.has(sec) ? s.delete(sec) : s.add(sec)
  open.value = s
}

// ── Tabs ──────────────────────────────────────────────────────────────────────
const tab    = ref('editar')
const subTab = ref('placa')

// ── Carga de la orden ─────────────────────────────────────────────────────────
const orden        = ref(null)
const vehiculoExt  = ref({})
const detalles     = ref([])
const fotos        = ref([])
const loadingOrden = ref(false)
const fotoZoom     = ref(null)

const editForm = ref({
  km_ingreso: null, km_salida: null,
  diagnostico: '', trabajo_realizado: '',
  promesa_entrega: null, jefe_responsable_id: null,
  convenio_id: null, client_id: null, placa_vehiculo: '',
})

async function cargarOrden() {
  if (!ordenId.value || !companyId.value) return
  loadingOrden.value = true
  try {
    const { data } = await api.get(`/api/talleres/ordenes/${ordenId.value}`, {
      params: { company_id: companyId.value }
    })
    orden.value       = data.orden ?? data
    detalles.value    = data.detalles ?? []
    fotos.value       = data.fotos ?? []
    ordenWorkers.value = data.workers ?? []
    vehiculoExt.value = {
      tipo:   orden.value.tipo_vehiculo || '',
      marca:  orden.value.marca  || '',
      modelo: orden.value.modelo || '',
      anio:   orden.value.anio   || '',
      color:  orden.value.color  || '',
    }
    editForm.value = {
      km_ingreso:          orden.value.km_ingreso ?? null,
      km_salida:           orden.value.km_salida  ?? null,
      diagnostico:         orden.value.diagnostico || '',
      trabajo_realizado:   orden.value.trabajo_realizado || '',
      promesa_entrega:     orden.value.promesa_entrega
                             ? orden.value.promesa_entrega.split('T')[0] : null,
      jefe_responsable_id: orden.value.jefe_responsable_id ?? null,
      convenio_id:         orden.value.convenio_id ?? null,
      client_id:           orden.value.client_id ?? null,
      placa_vehiculo:      orden.value.placa_vehiculo || '',
    }
  } catch { mostrarToast('Error al cargar la orden', 'error') }
  finally  { loadingOrden.value = false }
}

// ── Guardar cambios ───────────────────────────────────────────────────────────
const guardando = ref(false)
async function guardarCambios() {
  guardando.value = true
  try {
    await api.patch(`/api/talleres/ordenes/${ordenId.value}/editar`, {
      company_id: companyId.value,
      ...editForm.value,
    })
    if (orden.value) Object.assign(orden.value, editForm.value)
    if (clienteSeleccionado.value) {
      orden.value.cliente_nombre    = clienteSeleccionado.value.name
      orden.value.cliente_documento = clienteSeleccionado.value.document_number
      orden.value.cliente_telefono  = clienteSeleccionado.value.phone
      orden.value.client_id         = clienteSeleccionado.value.id
    }
    mostrarToast('Cambios guardados', 'ok')
  } catch (e) { mostrarToast(e?.response?.data?.detail ?? 'Error al guardar', 'error') }
  finally { guardando.value = false }
}

// ── Recibo: items para facturar ───────────────────────────────────────────────
const itemsParaFacturar = computed(() =>
  detalles.value.map(d => ({
    id:       d.id,
    nombre:   d.nombre,
    cantidad: d.cantidad ?? 1,
    precio:   d.precio_unitario ?? 0,
  }))
)

function onReciboSuccess(data) {
  showFacturarRecibo.value = false
  if (orden.value) orden.value.estado = 'entregada'
  reciboData.value = data
  showImprimirRecibo.value = true
}

function onImprimirClose() {
  showImprimirRecibo.value = false
  router.push('/talleres/ordenes')
}

// ── Anular orden ──────────────────────────────────────────────────────────────
async function anularOrden() {
  if (!(await showConfirm(
    '¿Anular esta orden? Quedará registrada como anulada y no se podrá facturar.',
    'Sí, anular'
  ))) return
  try {
    await api.patch(`/api/talleres/ordenes/${ordenId.value}/estado`, {
      company_id: companyId.value, estado: 'anulada',
    })
    if (orden.value) orden.value.estado = 'anulada'
    mostrarToast('Orden anulada', 'ok')
    setTimeout(() => router.push('/talleres/ordenes'), 1200)
  } catch (e) { mostrarToast(e?.response?.data?.detail ?? 'Error', 'error') }
}

// ── Auxiliares ────────────────────────────────────────────────────────────────
const workers   = ref([])
const convenios = ref([])
const clientes  = ref([])

async function cargarAuxiliares() {
  if (!companyId.value) return
  try {
    const [wRes, cRes, clRes] = await Promise.all([
      api.get('/api/talleres/workers-con-config', { params: { company_id: companyId.value } }),
      api.get('/api/talleres/convenios',           { params: { company_id: companyId.value } }),
      api.get('/clients'),
    ])
    workers.value   = wRes.data  ?? []
    convenios.value = cRes.data  ?? []
    clientes.value  = clRes.data ?? []
  } catch (e) { console.error('Error cargando auxiliares:', e) }
}

// ── Buscador de cliente ───────────────────────────────────────────────────────
const clienteBusqueda     = ref('')
const clienteResultados   = ref([])
const clienteSeleccionado = ref(null)

function filtrarClientes() {
  const q = clienteBusqueda.value.trim().toLowerCase()
  if (q.length < 2) { clienteResultados.value = []; return }
  clienteResultados.value = clientes.value
    .filter(c =>
      c.name?.toLowerCase().includes(q) ||
      c.document_number?.toLowerCase().includes(q) ||
      c.phone?.toLowerCase().includes(q)
    )
    .slice(0, 8)
}

function seleccionarCliente(c) {
  clienteSeleccionado.value = c
  clienteBusqueda.value     = c.name
  clienteResultados.value   = []
  editForm.value.client_id  = c.id
}

// ── Modo tipo (Servicios / Productos) ─────────────────────────────────────────
const modoTipo = ref('servicio')

// ── Búsqueda de productos ─────────────────────────────────────────────────────
const busqueda   = ref('')
const resultados = ref([])
const buscando   = ref(false)
let searchTimer  = null

function buscarProductos() {
  clearTimeout(searchTimer)
  if (busqueda.value.length < 2) { resultados.value = []; return }
  searchTimer = setTimeout(async () => {
    buscando.value = true
    try {
      const { data } = await api.get('/api/talleres/productos-buscar', {
        params: {
          company_id: companyId.value,
          q:          busqueda.value,
          item_type:  modoTipo.value,
          limit:      10,
        }
      })
      resultados.value = data
    } catch { resultados.value = [] }
    finally { buscando.value = false }
  }, 300)
}

function seleccionarProducto(p) {
  itemForm.value.producto_id     = p.id
  itemForm.value.producto_nombre = p.name
  itemForm.value.precio_unitario = p.base_price ?? 0
  itemForm.value.tipo_item = modoTipo.value === 'producto' ? 'repuesto' : (p.service_type || 'mecanica')
  busqueda.value   = ''
  resultados.value = []
}

function limpiarProducto() {
  itemForm.value.producto_id     = null
  itemForm.value.producto_nombre = ''
  itemForm.value.precio_unitario = 0
  itemForm.value.tipo_item       = modoTipo.value === 'producto' ? 'repuesto' : 'mecanica'
  busqueda.value   = ''
  resultados.value = []
}

// ── Formulario de ítem ────────────────────────────────────────────────────────
const itemFormDef = () => ({
  producto_id: null, producto_nombre: '',
  tipo_item: 'mecanica', cantidad: 1, precio_unitario: 0, worker_id: null,
})
const itemForm     = ref(itemFormDef())
const agregando    = ref(false)
const eliminandoId = ref(null)

const subtotalItem = computed(() =>
  (itemForm.value.cantidad || 1) * (itemForm.value.precio_unitario || 0)
)
const puedeAgregar = computed(() => !!itemForm.value.producto_id)

async function agregarDetalle() {
  if (!puedeAgregar.value) return
  agregando.value = true
  try {
    const esProducto = modoTipo.value === 'producto'
    const cantidad   = esProducto ? (itemForm.value.cantidad || 1) : 1
    const workerSel  = workers.value.find(x => x.id === itemForm.value.worker_id)

    const { data } = await api.post(`/api/talleres/ordenes/${ordenId.value}/detalle`, {
      company_id:      companyId.value,
      product_id:      itemForm.value.producto_id,
      nombre:          itemForm.value.producto_nombre,
      tipo_item:       itemForm.value.tipo_item,
      cantidad,
      precio_unitario: itemForm.value.precio_unitario,
      worker_id:       itemForm.value.worker_id || null,
      profession_id:   workerSel?.profession_id || null,
    })

    detalles.value.push({
      id:                 data.id ?? Date.now(),
      tipo_item:          itemForm.value.tipo_item,
      nombre:             itemForm.value.producto_nombre,
      cantidad,
      precio_unitario:    itemForm.value.precio_unitario,
      subtotal:           data.subtotal ?? subtotalItem.value,
      mano_obra_operario: data.mano_obra_operario ?? 0,
      worker_nombre:      workerSel?.name ?? null,
      liq_estado:         'pendiente',
    })
    itemForm.value = itemFormDef()
    mostrarToast('Ítem agregado', 'ok')
  } catch (e) { mostrarToast(e?.response?.data?.detail ?? 'Error al agregar', 'error') }
  finally { agregando.value = false }
}

async function eliminarDetalle(d) {
  if (!(await showConfirm(`¿Eliminar "${d.nombre}"?`))) return
  eliminandoId.value = d.id
  try {
    await api.delete(`/api/talleres/ordenes/${ordenId.value}/detalle/${d.id}`, {
      params: { company_id: companyId.value }
    })
    detalles.value = detalles.value.filter(x => x.id !== d.id)
    mostrarToast('Ítem eliminado', 'ok')
  } catch (e) { mostrarToast(e?.response?.data?.detail ?? 'Error', 'error') }
  finally { eliminandoId.value = null }
}

// ── Totales ───────────────────────────────────────────────────────────────────
const totales = computed(() => {
  let servicios = 0, repuestos = 0, mano_obra = 0
  for (const d of detalles.value) {
    if (d.tipo_item === 'repuesto') repuestos += d.subtotal ?? 0
    else servicios += d.subtotal ?? 0
    mano_obra += d.mano_obra_operario ?? 0
  }
  return { servicios, repuestos, total: servicios + repuestos, mano_obra }
})

// ── Historial ─────────────────────────────────────────────────────────────────
const histItems   = ref([])
const loadingHist = ref(false)
const histCargado = ref({ placa: false, cliente: false })

async function cargarHistorial() {
  if (subTab.value === 'placa')   cargarHistPlaca()
  if (subTab.value === 'cliente') cargarHistCliente()
}

function switchSubTab(st) {
  subTab.value      = st
  histItems.value   = []
  histCargado.value = { placa: false, cliente: false }
  cargarHistorial()
}

async function cargarHistPlaca() {
  if (histCargado.value.placa) return
  loadingHist.value = true
  try {
    const { data } = await api.get('/api/talleres/historial/placa', {
      params: { company_id: companyId.value, placa: orden.value?.placa_vehiculo }
    })
    histItems.value         = data
    histCargado.value.placa = true
  } catch { histItems.value = [] }
  finally { loadingHist.value = false }
}

async function cargarHistCliente() {
  if (histCargado.value.cliente || !orden.value?.client_id) return
  loadingHist.value = true
  try {
    const { data } = await api.get('/api/talleres/historial/cliente', {
      params: { company_id: companyId.value, client_id: orden.value.client_id }
    })
    histItems.value           = data
    histCargado.value.cliente = true
  } catch { histItems.value = [] }
  finally { loadingHist.value = false }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function estadoLabel(e) {
  return {
    abierta: 'Abierta', en_proceso: 'En Proceso',
    terminada: 'Terminada', entregada: 'Entregada',
    cancelada: 'Cancelada', anulada: 'Anulada',
  }[e] ?? e ?? '—'
}
function fmtFecha(v) {
  if (!v) return '—'
  return new Date(v).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}
function fmt(v) {
  if (v == null || v === '') return '—'
  return new Intl.NumberFormat('es-CO', {
    style: 'currency', currency: 'COP', maximumFractionDigits: 0,
  }).format(v)
}

const toast = ref({ visible: false, msg: '', tipo: 'ok' })
function mostrarToast(msg, tipo = 'ok') {
  toast.value = { visible: true, msg, tipo }
  setTimeout(() => { toast.value.visible = false }, 3500)
}

function init() {
  if (!companyId.value) return
  cargarOrden()
  cargarAuxiliares()
}

watch(companyId, (v) => { if (v) { cargarOrden(); cargarAuxiliares() } })
onMounted(init)
</script>

<style scoped>
.od-page { padding: 16px; max-width: 900px; display: flex; flex-direction: column; gap: 14px; }

/* ── Header ────────────────────────────────────────────────────────── */
.od-header { display:flex; align-items:center; gap:12px; background:#fff; border-radius:12px; padding:12px 16px; box-shadow:0 2px 8px rgba(0,0,0,.07); flex-wrap:wrap; }
.btn-back  { width:36px; height:36px; border-radius:9px; border:1.5px solid #e2e8f0; background:#f8fafc; cursor:pointer; color:#475569; display:flex; align-items:center; justify-content:center; font-size:15px; flex-shrink:0; }
.btn-back:hover { background:#eff6ff; color:#1d4ed8; border-color:#bfdbfe; }
.od-titulo { display:flex; align-items:center; gap:8px; flex:1; flex-wrap:wrap; min-width:0; }
.od-num    { font-size:17px; font-weight:800; font-family:monospace; color:#1e293b; }
.od-placa  { font-size:16px; font-weight:900; letter-spacing:2px; color:#1e293b; background:#f1f5f9; padding:3px 10px; border-radius:6px; }
.od-totales-mini { display:flex; align-items:center; gap:8px; margin-left:auto; }
.tot-mini  { font-size:16px; font-weight:700; color:#059669; display:flex; align-items:center; gap:4px; }
.btn-imprimir { width:34px; height:34px; border-radius:8px; border:1.5px solid #e2e8f0; background:#f8fafc; cursor:pointer; color:#475569; display:flex; align-items:center; justify-content:center; }
.btn-imprimir:hover { background:#f0fdf4; color:#059669; }

/* ── Estado badge ────────────────────────────────────────────────────── */
.es-badge      { font-size:11px; font-weight:700; padding:3px 9px; border-radius:20px; }
.es-abierta    { background:#dbeafe; color:#1d4ed8; }
.es-en_proceso { background:#fef3c7; color:#92400e; }
.es-terminada  { background:#dcfce7; color:#166534; }
.es-entregada  { background:#f1f5f9; color:#64748b; }
.es-cancelada  { background:#fee2e2; color:#b91c1c; }
.es-anulada    { background:#fef3c7; color:#92400e; }

/* ── Tabs ────────────────────────────────────────────────────────────── */
.od-tabs { display:flex; gap:4px; background:#f1f5f9; border-radius:10px; padding:4px; }
.od-tab  { display:flex; align-items:center; gap:7px; flex:1; padding:10px 14px; font-size:13px; font-weight:700; border:none; background:none; border-radius:7px; cursor:pointer; color:#64748b; justify-content:center; transition:all .12s; }
.od-tab.active { background:#fff; color:#1d4ed8; box-shadow:0 1px 4px rgba(0,0,0,.1); }
.od-tab:hover:not(.active) { background:#e2e8f0; }

.tab-body { display:flex; flex-direction:column; gap:10px; }

/* ── Acordeón ────────────────────────────────────────────────────────── */
.acord-block    { border-radius:12px; border:1.5px solid #e2e8f0; background:#fff; overflow:hidden; }
.acord-head     { display:flex; align-items:center; justify-content:space-between; width:100%; padding:13px 16px; background:none; border:none; cursor:pointer; font-size:13px; font-weight:700; color:#1e293b; transition:background .1s; gap:8px; }
.acord-head:hover { background:#f8fafc; }
.acord-title    { display:flex; align-items:center; gap:8px; color:#1e293b; flex:1; min-width:0; }
.acord-title .bi { color:#3b82f6; font-size:15px; flex-shrink:0; }
.acord-sub      { font-size:11px; font-weight:600; color:#64748b; background:#f1f5f9; padding:2px 8px; border-radius:20px; margin-left:6px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.acord-actions  { display:flex; align-items:center; gap:8px; flex-shrink:0; }
.acord-btn-add  { width:28px; height:28px; border-radius:7px; border:1.5px solid #bfdbfe; background:#eff6ff; color:#1d4ed8; cursor:pointer; display:flex; align-items:center; justify-content:center; font-size:13px; font-weight:700; transition:all .12s; }
.acord-btn-add:hover { background:#1d4ed8; color:#fff; border-color:#1d4ed8; }
.acord-body     { padding:14px 16px; border-top:1px solid #f1f5f9; }
.det-cnt        { font-size:11px; font-weight:600; color:#64748b; background:#f1f5f9; padding:2px 8px; border-radius:20px; margin-left:8px; }

/* ── Fotos del vehículo ──────────────────────────────────────────────── */
.fotos-strip { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:12px; }
.foto-thumb  { width:80px; height:80px; border-radius:10px; overflow:hidden; cursor:pointer; border:1.5px solid #e2e8f0; flex-shrink:0; position:relative; }
.foto-thumb img { width:100%; height:100%; object-fit:cover; }
.foto-thumb:hover { border-color:#3b82f6; transform:scale(1.03); transition:all .15s; }
.foto-video  { width:100%; height:100%; background:#1e293b; display:flex; align-items:center; justify-content:center; color:#fff; font-size:24px; }
.foto-overlay { position:fixed; inset:0; background:rgba(0,0,0,.85); z-index:9999; display:flex; align-items:center; justify-content:center; }
.foto-zoom-img { max-width:92vw; max-height:88vh; border-radius:12px; object-fit:contain; }
.foto-close { position:fixed; top:20px; right:20px; width:40px; height:40px; border-radius:50%; background:#fff; border:none; cursor:pointer; font-size:16px; display:flex; align-items:center; justify-content:center; }

/* ── Form grid ───────────────────────────────────────────────────────── */
.form-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
.fg        { display:flex; flex-direction:column; gap:5px; }
.fg label, .fg-label { font-size:11px; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:.4px; }
.span2     { grid-column:span 2; }
.mt8       { margin-top:8px; }
.fc        { border:1.5px solid #e2e8f0; border-radius:8px; padding:8px 10px; font-size:13px; color:#1e293b; outline:none; background:#fff; width:100%; box-sizing:border-box; }
.fc:focus  { border-color:#3b82f6; }
textarea.fc { resize:vertical; }
.fc-display { border:1.5px solid #e2e8f0; border-radius:8px; padding:8px 10px; font-size:13px; color:#64748b; background:#f8fafc; min-height:38px; display:flex; align-items:center; word-break:break-word; }
.fc-display.green { color:#059669; font-weight:700; background:#f0fdf4; border-color:#bbf7d0; font-size:15px; }

/* ── Cliente search ──────────────────────────────────────────────────── */
.client-search-wrap { display:flex; flex-direction:column; gap:5px; margin-bottom:4px; }
.search-wrap { position:relative; }
.abs-spin    { position:absolute; right:10px; top:50%; transform:translateY(-50%); color:#94a3b8; font-size:13px; pointer-events:none; }
.abs-ok      { position:absolute; right:10px; top:50%; transform:translateY(-50%); color:#059669; font-size:14px; pointer-events:none; }
.search-results { border:1.5px solid #e2e8f0; border-radius:8px; background:#fff; max-height:200px; overflow-y:auto; z-index:20; position:relative; box-shadow:0 4px 12px rgba(0,0,0,.08); }
.sr-item     { display:flex; align-items:center; gap:10px; padding:9px 12px; cursor:pointer; border-bottom:1px solid #f1f5f9; }
.sr-item:last-child { border-bottom:none; }
.sr-item:hover { background:#f0f9ff; }
.sr-name     { flex:1; font-size:13px; font-weight:600; color:#1e293b; }
.sr-code     { font-size:11px; color:#94a3b8; font-family:monospace; }
.sr-extra    { font-size:12px; color:#64748b; }

/* ── Totales row ─────────────────────────────────────────────────────── */
.totales-row { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:12px; }
.tc    { display:flex; flex-direction:column; gap:3px; padding:10px 14px; border-radius:10px; background:#f8fafc; border:1.5px solid #e2e8f0; flex:1; min-width:80px; }
.tc-l  { font-size:10px; font-weight:700; color:#94a3b8; text-transform:uppercase; }
.tc-v  { font-size:15px; font-weight:800; color:#1e293b; }
.tc.hl { background:#f0fdf4; border-color:#bbf7d0; } .tc.hl .tc-v { color:#059669; }
.tc.mo { background:#fffbeb; border-color:#fde68a; } .tc.mo .tc-v { color:#d97706; }

/* ── Detalles list ───────────────────────────────────────────────────── */
.det-empty   { display:flex; align-items:center; gap:8px; color:#94a3b8; font-size:13px; padding:16px; }
.detalles-list { display:flex; flex-direction:column; gap:6px; margin-bottom:14px; }
.dr          { display:flex; align-items:center; gap:10px; padding:10px 12px; border-radius:9px; background:#f8fafc; border:1px solid #f1f5f9; flex-wrap:wrap; }
.dr-tipo     { font-size:10px; font-weight:700; padding:2px 7px; border-radius:20px; flex-shrink:0; }
.dt-servicio  { background:#dbeafe; color:#1d4ed8; }
.dt-repuesto  { background:#f1f5f9; color:#475569; }
.dr-names    { flex:1; display:flex; flex-direction:column; gap:2px; min-width:0; }
.dr-name     { font-size:13px; font-weight:600; color:#1e293b; }
.dr-worker   { font-size:11px; color:#94a3b8; display:flex; align-items:center; gap:4px; }
.dr-nums     { display:flex; align-items:center; gap:10px; font-size:12px; color:#64748b; flex-wrap:wrap; }
.dr-sub      { font-weight:700; color:#1e293b; }
.dr-mo       { color:#d97706; font-weight:600; display:flex; align-items:center; gap:3px; }
.dr-del      { width:28px; height:28px; border-radius:7px; border:1.5px solid #fca5a5; background:#fff0f0; color:#dc2626; cursor:pointer; display:flex; align-items:center; justify-content:center; font-size:12px; flex-shrink:0; }
.dr-del:hover:not(:disabled) { background:#dc2626; color:#fff; }
.dr-del:disabled { opacity:.5; cursor:not-allowed; }

/* ── Agregar ítem ────────────────────────────────────────────────────── */
.add-item-form { border-top:1.5px dashed #e2e8f0; padding-top:14px; display:flex; flex-direction:column; gap:10px; }
.aif-title     { font-size:13px; font-weight:700; color:#374151; display:flex; align-items:center; gap:7px; }
.aif-title .bi { color:#10b981; }
.tipo-btns     { display:flex; gap:8px; }
.tipo-btn      { display:flex; align-items:center; gap:7px; padding:10px 20px; border-radius:10px; border:2px solid #e2e8f0; background:#f8fafc; font-size:13px; font-weight:700; color:#475569; cursor:pointer; transition:all .15s; flex:1; justify-content:center; }
.tipo-btn.active { border-color:#1d4ed8; background:#1d4ed8; color:#fff; }
.tipo-btn:hover:not(.active) { border-color:#93c5fd; background:#eff6ff; color:#1d4ed8; }
.prod-sel      { display:flex; align-items:center; justify-content:space-between; background:#f0fdf4; border:1.5px solid #bbf7d0; border-radius:8px; padding:8px 12px; }
.ps-info       { display:flex; flex-direction:column; gap:2px; }
.ps-name       { font-size:13px; font-weight:600; color:#1e293b; }
.ps-price      { font-size:12px; color:#059669; font-weight:700; }
.ps-del        { background:none; border:none; cursor:pointer; color:#94a3b8; font-size:13px; padding:4px; }
.btn-agregar   { display:flex; align-items:center; gap:7px; padding:10px 18px; background:#3b82f6; color:#fff; border:none; border-radius:9px; font-size:13px; font-weight:700; cursor:pointer; align-self:flex-start; }
.btn-agregar:hover:not(:disabled) { background:#2563eb; }
.btn-agregar:disabled { opacity:.5; cursor:not-allowed; }

/* ── Action bar ──────────────────────────────────────────────────────── */
.action-bar   { display:flex; gap:10px; flex-wrap:wrap; padding:14px 0; border-top:2px solid #f1f5f9; }
.btn-save     { display:flex; align-items:center; gap:7px; padding:11px 22px; background:#1d4ed8; color:#fff; border:none; border-radius:10px; font-size:14px; font-weight:700; cursor:pointer; }
.btn-save:hover:not(:disabled) { background:#1e40af; }
.btn-save:disabled { opacity:.6; cursor:not-allowed; }
.btn-comprobante { display:flex; align-items:center; gap:7px; padding:11px 22px; background:#64748b; color:#fff; border:none; border-radius:10px; font-size:14px; font-weight:700; cursor:pointer; }
.btn-comprobante:hover { background:#475569; }
.btn-recibo { display:flex; align-items:center; gap:7px; padding:11px 22px; background:#059669; color:#fff; border:none; border-radius:10px; font-size:14px; font-weight:700; cursor:pointer; }
.btn-recibo:hover:not(:disabled) { background:#047857; }
.btn-recibo:disabled { opacity:.5; cursor:not-allowed; }
.btn-facturar-pe { display:flex; align-items:center; gap:7px; padding:11px 22px; background:#2563eb; color:#fff; border:none; border-radius:10px; font-size:14px; font-weight:700; cursor:pointer; }
.btn-facturar-pe:hover:not(:disabled) { background:#1d4ed8; }
.btn-facturar-pe:disabled { background:#e2e8f0; color:#94a3b8; cursor:not-allowed; opacity:1; }
.badge-entregada { display:flex; align-items:center; gap:6px; background:#dcfce7; color:#166534; font-size:13px; font-weight:700; padding:10px 18px; border-radius:10px; }
.btn-cancelar { display:flex; align-items:center; gap:7px; padding:11px 22px; background:#fff; color:#dc2626; border:2px solid #fca5a5; border-radius:10px; font-size:14px; font-weight:700; cursor:pointer; margin-left:auto; }
.btn-cancelar:hover { background:#fee2e2; }
.orden-cancelada-msg { display:flex; align-items:center; gap:8px; color:#b91c1c; font-size:14px; font-weight:700; padding:12px 0; }

/* ── Historial ───────────────────────────────────────────────────────── */
.hist-subtabs { display:flex; gap:6px; margin-bottom:12px; flex-wrap:wrap; }
.hs-tab  { display:flex; align-items:center; gap:7px; padding:9px 16px; border-radius:9px; border:1.5px solid #e2e8f0; background:#f8fafc; font-size:13px; font-weight:600; color:#475569; cursor:pointer; transition:all .12s; }
.hs-tab.active { background:#1e3a5f; color:#fff; border-color:#1e3a5f; }
.hs-tab:disabled { opacity:.45; cursor:not-allowed; }
.hs-nodato { font-size:11px; opacity:.7; }
.hist-table-wrap { overflow-x:auto; border-radius:12px; border:1.5px solid #e2e8f0; }
.hist-table      { width:100%; border-collapse:collapse; font-size:13px; }
.hist-table thead tr { background:#f8fafc; }
.hist-table th   { padding:10px 12px; text-align:left; font-size:11px; font-weight:700; color:#64748b; text-transform:uppercase; border-bottom:1.5px solid #e2e8f0; }
.hist-table td   { padding:10px 12px; border-bottom:1px solid #f1f5f9; vertical-align:middle; }
.hist-row:hover td { background:#f0f9ff; }
.h-placa  { font-weight:800; font-size:14px; letter-spacing:1px; }
.h-num    { font-family:monospace; font-size:12px; color:#64748b; }
.h-fecha  { font-size:12px; color:#94a3b8; white-space:nowrap; }
.h-jefe   { font-size:12px; color:#475569; }
.h-tot    { font-weight:700; color:#1e293b; }
.h-cnt    { color:#64748b; }
.ta-r     { text-align:right; }
.ta-c     { text-align:center; }
.h-btn    { width:30px; height:30px; border:none; border-radius:7px; background:#eff6ff; color:#1d4ed8; cursor:pointer; display:flex; align-items:center; justify-content:center; font-size:14px; }
.h-btn:hover { background:#1d4ed8; color:#fff; }

/* ── Loading / Empty ─────────────────────────────────────────────────── */
.od-loading { display:flex; align-items:center; justify-content:center; gap:10px; padding:60px; color:#94a3b8; font-size:14px; }
.od-empty   { display:flex; flex-direction:column; align-items:center; gap:8px; padding:50px; color:#94a3b8; }
.od-empty .bi { font-size:36px; color:#e2e8f0; }
.od-empty p   { font-size:13px; margin:0; }
.spin { display:inline-block; animation:spin .8s linear infinite; }
@keyframes spin { from{transform:rotate(0)} to{transform:rotate(360deg)} }

/* ── Toast ───────────────────────────────────────────────────────────── */
.toast-msg   { position:fixed; bottom:24px; left:50%; transform:translateX(-50%); padding:12px 24px; border-radius:12px; font-size:14px; font-weight:600; display:flex; align-items:center; gap:8px; z-index:9999; box-shadow:0 8px 24px rgba(0,0,0,.18); animation:slideUp .2s ease; white-space:nowrap; }
.toast-ok    { background:#059669; color:#fff; }
.toast-error { background:#dc2626; color:#fff; }
@keyframes slideUp { from{opacity:0;transform:translateX(-50%) translateY(12px)} to{opacity:1;transform:translateX(-50%) translateY(0)} }

/* ── Responsive 768px ────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .form-grid    { grid-template-columns: 1fr; }
  .span2        { grid-column: span 1; }
  .action-bar   { flex-direction: column; }
  .btn-cancelar { margin-left: 0; }
  .totales-row  { gap: 6px; }
  .tc           { min-width: 70px; }
  .tipo-btns    { gap: 6px; }
}

/* ── Responsive 576px ────────────────────────────────────────────────── */
@media (max-width: 576px) {
  .od-header    { flex-direction: column; align-items: flex-start; gap: 8px; }
  .od-totales-mini { margin-left: 0; }
  .dr           { flex-direction: column; align-items: flex-start; }
  .hist-table th:nth-child(5), .hist-table td:nth-child(5) { display: none; }
  .foto-thumb   { width: 64px; height: 64px; }
}
</style>
