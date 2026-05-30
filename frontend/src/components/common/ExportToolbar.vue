<template>
  <div class="et-wrap">
    <button class="et-btn et-xls" @click="exportExcel" title="Descargar Excel">
      <i class="bi bi-file-earmark-excel"></i><span class="et-lbl">Excel</span>
    </button>
    <button class="et-btn et-pdf" @click="printPDF" title="Imprimir / Guardar PDF">
      <i class="bi bi-file-earmark-pdf"></i><span class="et-lbl">PDF</span>
    </button>
    <div class="et-tirilla-wrap" ref="tirRef">
      <button class="et-btn et-tir" @click="showTirMenu = !showTirMenu" title="Imprimir tirilla">
        <i class="bi bi-printer"></i><span class="et-lbl">Tirilla</span>
        <i class="bi bi-chevron-down et-car" :class="{ 'et-car-open': showTirMenu }"></i>
      </button>
      <div v-if="showTirMenu" class="et-tir-menu">
        <button @click="printTirilla(80)"><i class="bi bi-receipt me-1"></i>80 mm</button>
        <button @click="printTirilla(58)"><i class="bi bi-receipt me-1"></i>58 mm</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as XLSX from 'xlsx'

const props = defineProps({
  data:     { type: Array,  required: true },
  columns:  { type: Array,  required: true }, // [{ key, label, fmt? }]
  filename: { type: String, default: 'reporte' },
  title:    { type: String, default: 'Reporte' },
})

const showTirMenu = ref(false)
const tirRef      = ref(null)

function closeMenu(e) {
  if (tirRef.value && !tirRef.value.contains(e.target)) showTirMenu.value = false
}
onMounted(() => document.addEventListener('mousedown', closeMenu))
onUnmounted(() => document.removeEventListener('mousedown', closeMenu))

function cellVal(row, col) {
  const v = row[col.key]
  return col.fmt ? col.fmt(v, row) : (v ?? '')
}

function exportExcel() {
  const header  = props.columns.map(c => c.label)
  const colCount = props.columns.length
  const dataRows = props.data.flatMap(row => {
    if (row._sectionHeader) {
      // category header row: first cell = title, rest empty
      return [[row._title, ...Array(colCount - 1).fill('')]]
    }
    return [props.columns.map(c => cellVal(row, c))]
  })
  const ws = XLSX.utils.aoa_to_sheet([header, ...dataRows])

  // Bold + gray fill for section header rows
  const range = XLSX.utils.decode_range(ws['!ref'])
  let excelRow = 1 // 0 = header
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
}

function buildHTML(mode) {
  const isTirilla = mode !== 'a4'
  const width     = mode === 'a4' ? '210mm' : `${mode}mm`
  const fs        = mode === 'a4' ? '11px' : mode === 80 ? '9px' : '8px'
  const pad       = mode === 'a4' ? '12mm' : '2mm'
  const colCount  = props.columns.length

  const hdr = props.columns.map(c => `<th>${c.label}</th>`).join('')
  const body = props.data.map(row => {
    if (row._sectionHeader) {
      return `<tr class="sec-hdr"><td colspan="${colCount}">${row._title}</td></tr>`
    }
    return `<tr>${props.columns.map(c => `<td>${cellVal(row, c)}</td>`).join('')}</tr>`
  }).join('')

  const now = new Date().toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' })

  return `<!DOCTYPE html><html><head><meta charset="utf-8"><title>${props.title}</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:${isTirilla ? "'Courier New',monospace" : 'Arial,sans-serif'};font-size:${fs};width:${width};padding:${pad};}
h3{text-align:center;margin-bottom:4px;font-size:${mode === 'a4' ? '14px' : '11px'};}
.dt{text-align:center;font-size:${mode === 'a4' ? '10px' : '8px'};color:#555;margin-bottom:8px;}
table{width:100%;border-collapse:collapse;}
th{border-bottom:${isTirilla ? '1px solid #000' : '2px solid #333'};padding:2px 4px;text-align:left;font-size:${mode === 'a4' ? '10px' : fs};}
td{padding:2px 4px;border-bottom:1px ${isTirilla ? 'dashed' : 'solid'} #ddd;font-size:${fs};}
.sec-hdr td{background:${isTirilla ? '#000' : '#1d4ed8'};color:#fff;font-weight:bold;padding:3px 4px;border-bottom:none;font-size:${mode === 'a4' ? '10px' : fs};}
@media print{@page{margin:0;size:${width} auto;}}
</style></head><body>
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
}

function printPDF() { openPrint('a4') }
function printTirilla(mm) { showTirMenu.value = false; openPrint(mm) }
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

.et-tirilla-wrap { position: relative; }
.et-tir-menu {
  position: absolute; top: calc(100% + 4px); left: 0; z-index: 200;
  background: #fff; border: 1px solid #e5e7eb; border-radius: 8px;
  box-shadow: 0 6px 20px rgba(0,0,0,.12); overflow: hidden; min-width: 120px;
}
.et-tir-menu button {
  display: flex; align-items: center; width: 100%;
  padding: 9px 14px; background: none; border: none; cursor: pointer;
  font-size: .84rem; color: #374151; text-align: left;
  transition: background .12s;
}
.et-tir-menu button:hover { background: #f3f4f6; }

@media (max-width: 576px) {
  .et-btn { padding: 5px 8px; font-size: .78rem; }
  .et-lbl { display: none; }
}
</style>
