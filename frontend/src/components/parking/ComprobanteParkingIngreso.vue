<template>
  <Teleport to="body">
    <div class="cpi-overlay" @click.self="$emit('close')">
      <div class="cpi-modal">

        <div class="cpi-toolbar">
          <span class="cpi-toolbar-title">
            <i class="bi bi-receipt-cutoff"></i>
            {{ tipo === 'salida' ? 'Comprobante de Salida' : 'Comprobante de Ingreso' }}
          </span>
          <div class="cpi-toolbar-btns">
            <button class="cpi-btn cpi-btn-print" @click="abrirPanel">
              <i class="bi bi-printer-fill"></i> Imprimir
            </button>
            <button class="cpi-btn cpi-btn-close" @click="$emit('close')">
              <i class="bi bi-x-lg"></i>
            </button>
          </div>
        </div>

        <!-- Vista previa del comprobante -->
        <div class="cpi-preview-wrap">
          <div class="cpi-ticket" id="cpi-print-area">

            <div class="cpi-company">
              <div class="cpi-company-name">{{ companyName }}</div>
              <div class="cpi-company-sub">
                {{ tipo === 'salida' ? 'COMPROBANTE DE SALIDA — PARKING' : 'COMPROBANTE DE INGRESO — PARKING' }}
              </div>
            </div>

            <div class="cpi-divider">- - - - - - - - - - - - - - - - - -</div>

            <div class="cpi-row-kv">
              <span class="cpi-k">Orden N°</span>
              <span class="cpi-v cpi-orden">{{ orden.numero_orden }}</span>
            </div>
            <div class="cpi-row-kv">
              <span class="cpi-k">{{ tipo === 'salida' ? 'Hora salida' : 'Hora ingreso' }}</span>
              <span class="cpi-v">{{ fmtHora(tipo === 'salida' ? (orden.hora_salida || new Date().toISOString()) : orden.hora_ingreso) }}</span>
            </div>

            <div class="cpi-divider">· · · · · · · · · · · · · · · · · ·</div>

            <div class="cpi-section-lbl">VEHÍCULO</div>
            <div class="cpi-placa-box">{{ orden.placa }}</div>
            <div v-if="orden.tipo_vehiculo" class="cpi-row-kv">
              <span class="cpi-k">Tipo</span>
              <span class="cpi-v">{{ orden.tipo_vehiculo }}</span>
            </div>

            <div class="cpi-divider">· · · · · · · · · · · · · · · · · ·</div>

            <div class="cpi-section-lbl">SERVICIOS</div>
            <template v-if="items && items.length > 0">
              <div v-for="item in items" :key="item.product_id ?? item.nombre" class="cpi-row-kv">
                <span class="cpi-k">{{ item.nombre }}</span>
                <span class="cpi-v">× {{ item.cantidad }}</span>
              </div>
              <div class="cpi-total-personas">
                Total: {{ totalCantidad }} unidad{{ totalCantidad !== 1 ? 'es' : '' }}
              </div>
            </template>
            <template v-else>
              <div class="cpi-row-kv">
                <span class="cpi-k">Cantidad</span>
                <span class="cpi-v">{{ orden.adultos }}</span>
              </div>
            </template>

            <div v-if="orden.obs_portero" class="cpi-divider">· · · · · · · · · · · · · · · · · ·</div>
            <div v-if="orden.obs_portero" class="cpi-section-lbl">OBSERVACIONES</div>
            <div v-if="orden.obs_portero" class="cpi-obs">{{ orden.obs_portero }}</div>

            <div class="cpi-divider">- - - - - - - - - - - - - - - - - -</div>
            <div class="cpi-footer">
              <template v-if="tipo === 'salida'">¡Gracias por su visita!</template>
              <template v-else>Presente este comprobante en caja para realizar su pago.</template>
            </div>

          </div>
        </div>

        <!-- Panel de impresoras -->
        <div v-if="showPanel" class="cpi-panel-overlay" @click.self="showPanel = false">
          <div class="cpi-panel">
            <div class="cpi-panel-head">
              <span><i class="bi bi-printer-fill"></i> Seleccionar impresora</span>
              <button class="cpi-btn cpi-btn-close" @click="showPanel = false"><i class="bi bi-x-lg"></i></button>
            </div>
            <div v-if="loadingPrinters" class="cpi-panel-loading">
              <i class="bi bi-arrow-repeat spin"></i> Cargando impresoras…
            </div>
            <div v-else-if="printers.length === 0" class="cpi-panel-empty">
              <i class="bi bi-printer"></i>
              <p>No hay impresoras configuradas</p>
            </div>
            <div v-else class="cpi-printer-list">
              <button
                v-for="p in printers"
                :key="p.id"
                class="cpi-printer-item"
                :disabled="imprimiendoPosId === p.id"
                @click="imprimirPos(p)"
              >
                <i :class="p.ip ? 'bi bi-wifi' : 'bi bi-bluetooth'"></i>
                <span>{{ p.name }}</span>
                <i v-if="imprimiendoPosId === p.id" class="bi bi-arrow-repeat spin ms-auto"></i>
              </button>
            </div>
            <button class="cpi-btn-sistema" @click="imprimirSistema">
              <i class="bi bi-window"></i> Imprimir con sistema operativo
            </button>
          </div>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed } from 'vue'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'

const props = defineProps({
  orden:       { type: Object, required: true },
  companyName: { type: String, default: '' },
  companyId:   { type: Number, default: null },
  tipo:        { type: String, default: 'ingreso' }, // 'ingreso' | 'salida'
  items:       { type: Array,  default: () => [] },
})

const totalCantidad = computed(() =>
  (props.items || []).reduce((s, i) => s + (i.cantidad || 1), 0)
)

defineEmits(['close'])

// ── UUIDs ESC/POS BLE (mismos que ComprobanteIngreso.vue) ────────────────────
const BLE_SERVICES = [
  { service: '000018f0-0000-1000-8000-00805f9b34fb', char: '000018f1-0000-1000-8000-00805f9b34fb' },
  { service: '0000ff00-0000-1000-8000-00805f9b34fb', char: '0000ff02-0000-1000-8000-00805f9b34fb' },
  { service: '6e400001-b5a3-f393-e0a9-e50e24dcca9e', char: '6e400002-b5a3-f393-e0a9-e50e24dcca9e' },
  { service: 'e7810a71-73ae-499d-8c15-faa9aef0c3f2', char: 'bef8d6c9-9c21-4c9e-b632-bd58c1009f9f' },
  { service: '49535343-fe7d-4ae5-8fa9-9fafd205e455', char: '49535343-8841-43f4-a8d4-ecbe34729bb3' },
]

function fmtHora(dt) {
  if (!dt) return ''
  const d = new Date(dt)
  return d.toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' })
}

// ── Genera bytes ESC/POS ──────────────────────────────────────────────────────
function buildESCPOS() {
  const enc  = new TextEncoder()
  const buf  = []
  const ESC  = 0x1b
  const push = (...b) => buf.push(...b)
  const line = (t) => buf.push(...enc.encode(t + '\n'))

  push(ESC, 0x40)                              // INIT
  push(ESC, 0x61, 0x01)                        // CENTER
  push(ESC, 0x45, 0x01)                        // BOLD ON
  line(props.companyName.toUpperCase())
  line(props.tipo === 'salida' ? 'COMPROBANTE DE SALIDA' : 'COMPROBANTE DE INGRESO')
  line('PARKING SERVICE')
  push(ESC, 0x45, 0x00)                        // BOLD OFF
  line('--------------------------------')
  push(ESC, 0x61, 0x00)                        // LEFT

  const o = props.orden
  line(`Orden:  ${o.numero_orden}`)
  const fechaLabel = props.tipo === 'salida' ? 'Salida:' : 'Ingreso:'
  const fechaVal   = props.tipo === 'salida' ? (o.hora_salida || new Date().toISOString()) : o.hora_ingreso
  line(`${fechaLabel} ${fmtHora(fechaVal)}`)
  line('--------------------------------')

  push(ESC, 0x61, 0x01)
  push(ESC, 0x45, 0x01)
  line('VEHICULO')
  push(ESC, 0x45, 0x00)
  line(`[ ${(o.placa || '').toUpperCase()} ]`)
  if (o.tipo_vehiculo) line(o.tipo_vehiculo)
  push(ESC, 0x61, 0x00)

  line('--------------------------------')
  push(ESC, 0x61, 0x01)
  push(ESC, 0x45, 0x01)
  line('SERVICIOS')
  push(ESC, 0x45, 0x00)
  push(ESC, 0x61, 0x00)

  const svcItems = props.items && props.items.length > 0 ? props.items : null
  if (svcItems) {
    for (const it of svcItems) {
      const nombre = String(it.nombre).padEnd(20).slice(0, 20)
      line(`${nombre}  x ${it.cantidad}`)
    }
    const total = svcItems.reduce((s, i) => s + (i.cantidad || 1), 0)
    line(`Total: ${total} unidad${total !== 1 ? 'es' : ''}`)
  } else {
    line(`Cantidad: ${o.adultos}`)
  }

  if (o.obs_portero) {
    line('--------------------------------')
    push(ESC, 0x45, 0x01)
    line('OBS:')
    push(ESC, 0x45, 0x00)
    line(o.obs_portero)
  }

  line('--------------------------------')
  push(ESC, 0x61, 0x01)
  if (props.tipo === 'salida') {
    line('Gracias por su visita!')
  } else {
    line('Presente este comprobante')
    line('en caja para realizar su pago.')
  }
  push(0x0a, 0x0a, 0x0a)
  push(ESC, 0x69)                              // CUT

  return new Uint8Array(buf)
}

// ── Bluetooth ─────────────────────────────────────────────────────────────────
const imprimiendoPosId = ref(null)

async function imprimirBluetooth(printer) {
  if (!('bluetooth' in navigator)) {
    showToast('Web Bluetooth no disponible. Usa Chrome en Android.', 'warning', 4000)
    return
  }
  imprimiendoPosId.value = printer.id
  try {
    let device = null
    const storedId = sessionStorage.getItem(`bt_pk_${printer.id}`)
    if (storedId && navigator.bluetooth.getDevices) {
      const devs = await navigator.bluetooth.getDevices()
      device = devs.find(d => d.id === storedId) || null
    }
    if (!device) {
      device = await navigator.bluetooth.requestDevice({
        filters: [{ name: printer.name }, { namePrefix: printer.name.split('-')[0] }],
        optionalServices: BLE_SERVICES.map(s => s.service),
      })
      sessionStorage.setItem(`bt_pk_${printer.id}`, device.id)
    }

    const server = await device.gatt.connect()
    const bytes  = buildESCPOS()

    let enviado = false
    for (const { service: svcId, char: charId } of BLE_SERVICES) {
      try {
        const svc   = await server.getPrimaryService(svcId)
        const ch    = await svc.getCharacteristic(charId)
        const CHUNK = 100
        for (let i = 0; i < bytes.length; i += CHUNK) {
          const slice = bytes.slice(i, i + CHUNK)
          try { await ch.writeValueWithoutResponse(slice) }
          catch { await ch.writeValue(slice) }
          await new Promise(r => setTimeout(r, 20))
        }
        enviado = true
        break
      } catch { /* probar siguiente servicio */ }
    }

    server.disconnect()
    if (!enviado) throw new Error('No se encontró servicio ESC/POS en la impresora')
    showToast(`Impreso en "${printer.name}"`, 'success', 2000)
    showPanel.value = false
  } catch (e) {
    if (e.name === 'NotFoundError' || e.name === 'NotAllowedError') {
      showToast('Selección cancelada', 'info', 2000)
    } else {
      sessionStorage.removeItem(`bt_pk_${printer.id}`)
      showToast(e.message || 'Error Bluetooth', 'error', 4000)
    }
  }
  imprimiendoPosId.value = null
}

// ── Panel de impresoras ───────────────────────────────────────────────────────
const showPanel       = ref(false)
const printers        = ref([])
const loadingPrinters = ref(false)

async function abrirPanel() {
  showPanel.value = true
  if (printers.value.length === 0) await loadPrinters()
}

async function loadPrinters() {
  if (!props.companyId) return
  loadingPrinters.value = true
  try {
    const res = await api.get('/api/talleres/printers', {
      params: { company_id: props.companyId },
    })
    printers.value = res.data || []
  } catch {
    printers.value = []
  }
  loadingPrinters.value = false
}

async function imprimirPos(printer) {
  if (!printer.ip) {
    await imprimirBluetooth(printer)
    return
  }
  imprimiendoPosId.value = printer.id
  try {
    await api.post('/api/talleres/imprimir-comprobante', {
      company_id:   props.companyId,
      printer_id:   printer.id,
      orden:        props.orden,
      company_name: props.companyName,
    })
    showToast(`Enviado a "${printer.name}"`, 'success', 2000)
    showPanel.value = false
  } catch (e) {
    showToast(e?.response?.data?.detail || `Error al enviar a "${printer.name}"`, 'error', 3000)
  }
  imprimiendoPosId.value = null
}

function imprimirSistema() {
  showPanel.value = false
  const contenido = document.getElementById('cpi-print-area')
  if (!contenido) return
  const printWin = window.open('', '_blank', 'width=400,height=600')
  printWin.document.write(`<!DOCTYPE html><html><head>
    <meta charset="UTF-8"><title>Comprobante Parking</title>
    <style>
      * { margin:0; padding:0; box-sizing:border-box; }
      body { font-family:'Courier New',monospace; font-size:12px; color:#000; background:#fff; padding:8px; width:80mm; }
      .cpi-company { text-align:center; margin-bottom:6px; }
      .cpi-company-name { font-size:14px; font-weight:bold; text-transform:uppercase; }
      .cpi-company-sub  { font-size:10px; margin-top:2px; }
      .cpi-divider      { text-align:center; font-size:10px; color:#666; margin:4px 0; }
      .cpi-section-lbl  { font-size:10px; font-weight:bold; text-transform:uppercase; letter-spacing:.5px; margin:6px 0 3px; color:#333; }
      .cpi-row-kv       { display:flex; justify-content:space-between; gap:8px; margin:2px 0; font-size:11px; }
      .cpi-k            { color:#555; flex-shrink:0; }
      .cpi-v            { font-weight:600; text-align:right; }
      .cpi-orden        { font-size:13px; font-weight:900; }
      .cpi-placa-box    { font-size:30px; font-weight:900; letter-spacing:4px; text-align:center;
                          border:2px solid #000; padding:4px 8px; margin:4px auto; display:inline-block; }
      .cpi-total-personas { font-size:11px; font-weight:bold; margin-top:4px; }
      .cpi-row-kv .cpi-k { color:#555; }
      .cpi-row-kv .cpi-v { font-weight:600; }
      .cpi-obs          { font-size:11px; font-style:italic; color:#333; padding:2px 0; }
      .cpi-footer       { text-align:center; font-size:10px; color:#555; margin-top:6px; line-height:1.4; }
    </style>
  </head><body>${contenido.innerHTML}</body></html>`)
  printWin.document.close()
  printWin.focus()
  setTimeout(() => { printWin.print(); printWin.close() }, 250)
}
</script>

<style scoped>
.cpi-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.55);
  z-index: 1100; display: flex; align-items: center; justify-content: center; padding: 16px;
}
.cpi-modal {
  background: #fff; border-radius: 12px; width: 100%; max-width: 420px;
  max-height: 90vh; overflow-y: auto; display: flex; flex-direction: column;
}
.cpi-toolbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; border-bottom: 1px solid #e9ecef; flex-shrink: 0;
}
.cpi-toolbar-title { font-weight: 600; font-size: .95rem; display: flex; align-items: center; gap: 8px; }
.cpi-toolbar-btns  { display: flex; gap: 8px; }
.cpi-btn { border: none; border-radius: 6px; padding: 6px 12px; font-size: .85rem; cursor: pointer; display: flex; align-items: center; gap: 6px; }
.cpi-btn-print { background: #0d6efd; color: #fff; }
.cpi-btn-print:hover { background: #0b5ed7; }
.cpi-btn-close { background: #f1f3f5; color: #495057; }
.cpi-btn-close:hover { background: #dee2e6; }

.cpi-preview-wrap {
  padding: 16px; display: flex; justify-content: center; flex: 1;
}
.cpi-ticket {
  background: #fff; border: 1px dashed #ccc; border-radius: 4px;
  padding: 12px 16px; font-family: 'Courier New', monospace;
  font-size: 12px; width: 100%; max-width: 300px;
}
.cpi-company      { text-align: center; margin-bottom: 6px; }
.cpi-company-name { font-size: 14px; font-weight: bold; text-transform: uppercase; }
.cpi-company-sub  { font-size: 10px; margin-top: 2px; }
.cpi-divider      { text-align: center; font-size: 10px; color: #666; margin: 4px 0; }
.cpi-section-lbl  { font-size: 10px; font-weight: bold; text-transform: uppercase; letter-spacing: .5px; margin: 6px 0 3px; color: #333; }
.cpi-row-kv       { display: flex; justify-content: space-between; gap: 8px; margin: 2px 0; font-size: 11px; }
.cpi-k            { color: #555; flex-shrink: 0; }
.cpi-v            { font-weight: 600; text-align: right; }
.cpi-orden        { font-size: 13px; font-weight: 900; }
.cpi-placa-box    { font-size: 30px; font-weight: 900; letter-spacing: 4px; text-align: center;
                    border: 2px solid #000; padding: 6px 10px; margin: 6px auto; display: inline-block; }
.cpi-total-personas { font-size: 11px; font-weight: bold; margin-top: 4px; }
.cpi-obs          { font-size: 11px; font-style: italic; color: #333; padding: 2px 0; }
.cpi-footer       { text-align: center; font-size: 10px; color: #555; margin-top: 6px; line-height: 1.4; }

/* Panel impresoras */
.cpi-panel-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.4); z-index: 1200;
  display: flex; align-items: flex-end; justify-content: center; padding-bottom: 0;
}
.cpi-panel {
  background: #fff; border-radius: 16px 16px 0 0; width: 100%; max-width: 440px;
  padding: 16px; max-height: 60vh; overflow-y: auto;
}
.cpi-panel-head {
  display: flex; align-items: center; justify-content: space-between;
  font-weight: 600; margin-bottom: 12px;
}
.cpi-panel-loading, .cpi-panel-empty {
  text-align: center; padding: 24px; color: #6c757d; font-size: .9rem;
}
.cpi-printer-list { display: flex; flex-direction: column; gap: 8px; }
.cpi-printer-item {
  display: flex; align-items: center; gap: 10px; padding: 12px 14px;
  border: 1px solid #dee2e6; border-radius: 8px; background: #fff;
  font-size: .9rem; cursor: pointer; transition: background .15s;
}
.cpi-printer-item:hover:not(:disabled) { background: #f8f9fa; }
.cpi-printer-item:disabled { opacity: .6; cursor: default; }
.cpi-btn-sistema {
  width: 100%; margin-top: 10px; padding: 10px; border: 1px dashed #adb5bd;
  border-radius: 8px; background: #fff; color: #6c757d; font-size: .85rem;
  cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px;
}
.cpi-btn-sistema:hover { background: #f8f9fa; }

.spin { animation: spin .8s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
