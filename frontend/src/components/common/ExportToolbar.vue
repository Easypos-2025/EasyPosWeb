<template>
  <div class="et-wrap">

    <!-- Excel -->
    <button class="et-btn et-xls" @click="exportExcel" title="Descargar Excel">
      <i class="bi bi-file-earmark-excel"></i><span class="et-lbl">Excel</span>
    </button>

    <!-- PDF (A4) -->
    <button class="et-btn et-pdf" @click="printPDF" title="Guardar / Imprimir PDF">
      <i class="bi bi-file-earmark-pdf"></i><span class="et-lbl">PDF</span>
    </button>

    <!-- Tirilla (dropdown siempre visible) -->
    <div class="et-tirilla-wrap" ref="tirRef">
      <button class="et-btn et-tir" @click="toggleMenu" title="Imprimir tirilla">
        <i class="bi bi-printer"></i>
        <span class="et-lbl">Tirilla</span>
        <i class="bi bi-chevron-down et-car" :class="{ 'et-car-open': showTirMenu }"></i>
      </button>

      <div v-if="showTirMenu" class="et-tir-menu">

        <!-- 80mm y 58mm — siempre presentes -->
        <button @click="printTirilla(80)">
          <i class="bi bi-receipt me-1"></i> 80 mm
        </button>
        <button @click="printTirilla(58)">
          <i class="bi bi-receipt me-1"></i> 58 mm
        </button>

        <!-- Impresoras de la company -->
        <template v-if="companyId">
          <div class="et-sep"></div>

          <div v-if="loadingPrinters" class="et-menu-loading">
            <i class="bi bi-arrow-repeat spin me-1"></i> Cargando…
          </div>

          <template v-else-if="printers.length">
            <button
              v-for="p in printers"
              :key="p.id"
              :disabled="sendingId === p.id"
              @click="imprimirPos(p)"
            >
              <i :class="iconoPrinter(p)" class="me-1"></i>
              {{ p.name }}
              <i v-if="sendingId === p.id" class="bi bi-arrow-repeat spin ms-auto"></i>
            </button>
            <div class="et-sep"></div>
          </template>
        </template>

        <!-- Sistema operativo (diálogo nativo) -->
        <button @click="imprimirSistema">
          <i class="bi bi-window me-1"></i> Imprimir (SO)
        </button>

      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as XLSX from 'xlsx'
import api from '@/services/apis.js'
import { showToast } from '@/utils/toast'

const props = defineProps({
  data:        { type: Array,  required: true },
  columns:     { type: Array,  required: true }, // [{ key, label, fmt?, align? }]
  filename:    { type: String, default: 'reporte' },
  title:       { type: String, default: 'Reporte' },
  companyId:   { type: Number, default: null },    // para cargar impresoras de la company
  companyName: { type: String, default: 'EasyPOS' },
})

// ── Menú ──────────────────────────────────────────────────────────────────────
const showTirMenu = ref(false)
const tirRef      = ref(null)

function toggleMenu() {
  showTirMenu.value = !showTirMenu.value
  if (showTirMenu.value && props.companyId && !printers.value.length && !loadingPrinters.value) {
    loadPrinters()
  }
}

function closeMenu(e) {
  if (tirRef.value && !tirRef.value.contains(e.target)) showTirMenu.value = false
}
onMounted(() => document.addEventListener('mousedown', closeMenu))
onUnmounted(() => document.removeEventListener('mousedown', closeMenu))

// ── Excel ─────────────────────────────────────────────────────────────────────
function cellVal(row, col) {
  const v = row[col.key]
  return col.fmt ? col.fmt(v, row) : (v ?? '')
}

function exportExcel() {
  const header   = props.columns.map(c => c.label)
  const colCount = props.columns.length
  const dataRows = props.data.flatMap(row => {
    if (row._sectionHeader) return [[row._title, ...Array(colCount - 1).fill('')]]
    return [props.columns.map(c => cellVal(row, c))]
  })
  const ws = XLSX.utils.aoa_to_sheet([header, ...dataRows])

  const range = XLSX.utils.decode_range(ws['!ref'])
  let excelRow = 1
  props.data.forEach(row => {
    if (row._sectionHeader) {
      for (let c = 0; c <= range.e.c; c++) {
        const addr = XLSX.utils.encode_cell({ r: excelRow, c })
        if (!ws[addr]) ws[addr] = { t: 's', v: '' }
        ws[addr].s = { font: { bold: true }, fill: { fgColor: { rgb: 'E8F4FD' } } }
      }
    }
    excelRow++
  })

  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Reporte')
  XLSX.writeFile(wb, `${props.filename}.xlsx`)
  showTirMenu.value = false
}

// ── HTML builder (PDF + browser tirilla) ─────────────────────────────────────
function buildHTML(mode) {
  const isTirilla = mode !== 'a4'
  const width     = mode === 'a4' ? '210mm' : `${mode}mm`
  const fs        = mode === 'a4' ? '11px' : mode === 80 ? '9px' : '8px'
  const pad       = mode === 'a4' ? '12mm' : '2mm'
  const colCount  = props.columns.length

  const hdr  = props.columns.map(c => `<th style="text-align:${c.align||'left'}">${c.label}</th>`).join('')
  const body = props.data.map(row => {
    if (row._sectionHeader) {
      return `<tr class="sec-hdr"><td colspan="${colCount}">${row._title}</td></tr>`
    }
    return `<tr>${props.columns.map(c =>
      `<td style="text-align:${c.align||'left'}">${cellVal(row, c)}</td>`
    ).join('')}</tr>`
  }).join('')

  const now = new Date().toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' })

  return `<!DOCTYPE html><html><head><meta charset="utf-8"><title>${props.title}</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:${isTirilla ? "'Courier New',monospace" : 'Arial,sans-serif'};font-size:${fs};width:${width};padding:${pad};}
h3{text-align:center;margin-bottom:4px;font-size:${mode==='a4'?'14px':'11px'};}
.co{text-align:center;font-size:${mode==='a4'?'11px':'9px'};font-weight:bold;margin-bottom:2px;}
.dt{text-align:center;font-size:${mode==='a4'?'10px':'8px'};color:#555;margin-bottom:8px;}
table{width:100%;border-collapse:collapse;}
th{border-bottom:${isTirilla?'1px solid #000':'2px solid #333'};padding:2px 4px;font-size:${mode==='a4'?'10px':fs};}
td{padding:2px 4px;border-bottom:1px ${isTirilla?'dashed':'solid'} #ddd;font-size:${fs};}
.sec-hdr td{background:${isTirilla?'#000':'#1d4ed8'};color:#fff;font-weight:bold;padding:3px 4px;border-bottom:none;}
@media print{@page{margin:0;size:${width} auto;}}
</style></head><body>
<p class="co">${props.companyName}</p>
<h3>${props.title}</h3><p class="dt">${now}</p>
<table><thead><tr>${hdr}</tr></thead><tbody>${body}</tbody></table>
</body></html>`
}

function openPrint(mode) {
  const w = window.open('', '_blank', 'width=800,height=600')
  if (!w) return
  w.document.write(buildHTML(mode))
  w.document.close()
  w.onload = () => { w.focus(); w.print() }
  showTirMenu.value = false
}

function printPDF()      { openPrint('a4') }
function printTirilla(mm){ openPrint(mm) }
function imprimirSistema(){ openPrint('a4') }

// ── ESC/POS builder ───────────────────────────────────────────────────────────
const _CM = {'á':'a','à':'a','â':'a','ä':'a','ã':'a','é':'e','è':'e','ê':'e','ë':'e','í':'i','ì':'i','î':'i','ï':'i','ó':'o','ò':'o','ô':'o','ö':'o','õ':'o','ú':'u','ù':'u','û':'u','ü':'u','ñ':'n','ç':'c','Á':'A','É':'E','Í':'I','Ó':'O','Ú':'U','Ñ':'N','Ç':'C','¿':'','¡':'','$':'$','€':'E','°':''}

function norm(t) {
  return String(t ?? '').split('').map(c => (_CM[c] !== undefined ? _CM[c] : (c.charCodeAt(0) > 127 ? '?' : c))).join('')
}

function buildESCPOS(mm) {
  const lineW = mm === 80 ? 42 : 30
  const enc   = new TextEncoder()
  const buf   = []
  const ESC   = 0x1b
  const push  = (...b) => buf.push(...b)
  const ln    = t => buf.push(...enc.encode(norm(t).slice(0, lineW) + '\n'))
  const sep   = () => ln('-'.repeat(lineW))

  // Calcular anchos de columna
  const cols     = props.columns
  const numCols  = cols.length
  // Columnas numéricas (align right) tienen ancho fijo mínimo
  const rightCols = cols.filter(c => c.align === 'right')
  const rightW    = rightCols.length > 0 ? Math.min(10, Math.floor(lineW * 0.25)) : 0
  const leftW     = Math.floor((lineW - rightW * rightCols.length - (numCols - 1)) /
                    Math.max(1, numCols - rightCols.length))

  function formatRow(values) {
    let line = ''
    cols.forEach((c, i) => {
      const v   = norm(values[i] ?? '')
      const isR = c.align === 'right'
      const w   = isR ? rightW : leftW
      if (isR) line += v.slice(-w).padStart(w)
      else     line += v.slice(0, w).padEnd(w)
      if (i < cols.length - 1) line += ' '
    })
    return line.slice(0, lineW)
  }

  push(ESC, 0x40)                    // INIT
  push(ESC, 0x61, 0x01)              // CENTER
  push(ESC, 0x45, 0x01)              // BOLD ON
  ln(props.companyName.toUpperCase())
  ln(props.title)
  push(ESC, 0x45, 0x00)              // BOLD OFF
  push(ESC, 0x61, 0x00)              // LEFT
  const now = new Date().toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' })
  ln(now)
  sep()

  // Headers
  push(ESC, 0x45, 0x01)
  ln(formatRow(cols.map(c => c.label)))
  push(ESC, 0x45, 0x00)
  sep()

  // Rows
  for (const row of props.data) {
    if (row._sectionHeader) {
      push(ESC, 0x45, 0x01)
      ln(norm(row._title))
      push(ESC, 0x45, 0x00)
      continue
    }
    ln(formatRow(cols.map(c => String(c.fmt ? c.fmt(row[c.key], row) : (row[c.key] ?? '')))))
  }

  sep()
  push(0x0a, 0x0a, 0x0a)
  push(ESC, 0x69)                    // CUT
  push(ESC, 0x40)                    // INIT

  return new Uint8Array(buf)
}

// ── Impresoras de la company ──────────────────────────────────────────────────
const printers        = ref([])
const loadingPrinters = ref(false)
const sendingId       = ref(null)

const BLE_SERVICES = [
  { service: '000018f0-0000-1000-8000-00805f9b34fb', char: '000018f1-0000-1000-8000-00805f9b34fb' },
  { service: '0000ff00-0000-1000-8000-00805f9b34fb', char: '0000ff02-0000-1000-8000-00805f9b34fb' },
  { service: '6e400001-b5a3-f393-e0a9-e50e24dcca9e', char: '6e400002-b5a3-f393-e0a9-e50e24dcca9e' },
  { service: 'e7810a71-73ae-499d-8c15-faa9aef0c3f2', char: 'bef8d6c9-9c21-4c9e-b632-bd58c1009f9f' },
  { service: '49535343-fe7d-4ae5-8fa9-9fafd205e455', char: '49535343-8841-43f4-a8d4-ecbe34729bb3' },
]

async function loadPrinters() {
  if (!props.companyId) return
  loadingPrinters.value = true
  try {
    const { data } = await api.get('/api/pos-catalogo/impresoras', {
      params: { company_id: props.companyId }
    })
    printers.value = (data || []).filter(p => p.is_active)
  } catch { printers.value = [] }
  finally { loadingPrinters.value = false }
}

function iconoPrinter(p) {
  if (p.connection_type === 'usb') return 'bi bi-usb-symbol'
  if (p.ip) return 'bi bi-wifi'
  return 'bi bi-bluetooth'
}

async function imprimirPos(printer) {
  showTirMenu.value = false
  if (printer.connection_type === 'usb') {
    await imprimirWebUSB(printer)
    return
  }
  if (!printer.ip) {
    await imprimirBluetooth(printer)
    return
  }
  // Red / IP → backend
  sendingId.value = printer.id
  try {
    const bytes  = buildESCPOS(80)
    const b64    = btoa(String.fromCharCode(...bytes))
    await api.post('/api/pos-catalogo/impresoras/print-raw', {
      printer_id: printer.id,
      company_id: props.companyId,
      data_b64:   b64,
    })
    showToast(`Enviado a "${printer.name}"`, 'success', 2000)
  } catch (e) {
    showToast(e?.response?.data?.detail || 'Error al imprimir', 'error', 4000)
  } finally {
    sendingId.value = null
  }
}

async function imprimirBluetooth(printer) {
  if (!('bluetooth' in navigator)) {
    showToast('Web Bluetooth no disponible. Usa Chrome en Android.', 'warning', 4000)
    return
  }
  sendingId.value = printer.id
  try {
    let device = null
    const storedId = sessionStorage.getItem(`bt_et_${printer.id}`)
    if (storedId && navigator.bluetooth.getDevices) {
      const devs = await navigator.bluetooth.getDevices()
      device = devs.find(d => d.id === storedId) || null
    }
    if (!device) {
      device = await navigator.bluetooth.requestDevice({
        filters: [{ name: printer.name }, { namePrefix: printer.name.split('-')[0] }],
        optionalServices: BLE_SERVICES.map(s => s.service),
      })
      sessionStorage.setItem(`bt_et_${printer.id}`, device.id)
    }
    const server = await device.gatt.connect()
    const bytes  = buildESCPOS(58)
    let enviado  = false
    for (const { service: svcId, char: charId } of BLE_SERVICES) {
      try {
        const svc  = await server.getPrimaryService(svcId)
        const ch   = await svc.getCharacteristic(charId)
        const CHUNK = 100
        for (let i = 0; i < bytes.length; i += CHUNK) {
          const slice = bytes.slice(i, i + CHUNK)
          try { await ch.writeValueWithoutResponse(slice) } catch { await ch.writeValue(slice) }
          await new Promise(r => setTimeout(r, 20))
        }
        enviado = true; break
      } catch { /* probar siguiente servicio */ }
    }
    server.disconnect()
    if (!enviado) throw new Error('No se encontró servicio ESC/POS')
    showToast(`Impreso en "${printer.name}"`, 'success', 2000)
  } catch (e) {
    if (e.name === 'NotFoundError' || e.name === 'NotAllowedError') {
      showToast('Selección cancelada', 'info', 2000)
    } else {
      sessionStorage.removeItem(`bt_et_${printer.id}`)
      showToast(e.message || 'Error Bluetooth', 'error', 4000)
    }
  } finally {
    sendingId.value = null
  }
}

async function imprimirWebUSB(printer) {
  showToast('Impresión USB próximamente disponible', 'info', 3000)
}
</script>

<style scoped>
.et-wrap { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }

.et-btn {
  display: flex; align-items: center; gap: 5px;
  padding: 6px 12px; border-radius: 7px; border: 1px solid transparent;
  font-size: .82rem; font-weight: 500; cursor: pointer; white-space: nowrap;
  transition: filter .15s;
}
.et-btn:hover { filter: brightness(.93); }
.et-lbl { display: inline; }

.et-xls { background: #16a34a; color: #fff; border-color: #15803d; }
.et-pdf { background: #dc2626; color: #fff; border-color: #b91c1c; }
.et-tir { background: #1d4ed8; color: #fff; border-color: #1e40af; }

.et-car { font-size: .65rem; transition: transform .2s; margin-left: 2px; }
.et-car-open { transform: rotate(180deg); }

/* ── Dropdown ─────────────────────────────────────────────── */
.et-tirilla-wrap { position: relative; }
.et-tir-menu {
  position: absolute; top: calc(100% + 4px); right: 0; z-index: 300;
  background: #fff; border: 1px solid #e5e7eb; border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,.13); overflow: hidden; min-width: 160px;
}
.et-tir-menu button {
  display: flex; align-items: center; width: 100%;
  padding: 10px 14px; background: none; border: none; cursor: pointer;
  font-size: .84rem; color: #374151; text-align: left;
  transition: background .12s; gap: 4px;
}
.et-tir-menu button:hover:not(:disabled) { background: #f3f4f6; }
.et-tir-menu button:disabled { opacity: .5; cursor: not-allowed; }

.et-sep {
  height: 1px; background: #e5e7eb; margin: 3px 0;
}

.et-menu-loading {
  padding: 10px 14px; font-size: .82rem; color: #6b7280;
  display: flex; align-items: center;
}

@keyframes spin { to { transform: rotate(360deg); } }
.spin { display: inline-block; animation: spin .7s linear infinite; }

@media (max-width: 576px) {
  .et-btn { padding: 5px 8px; font-size: .78rem; }
  .et-lbl { display: none; }
  .et-tir-menu { right: 0; left: auto; }
}
</style>
