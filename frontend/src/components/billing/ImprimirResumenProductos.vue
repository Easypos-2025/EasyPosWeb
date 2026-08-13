<template>
  <Teleport to="body">
    <div class="irp-overlay">
      <div class="irp-modal">

        <!-- Header -->
        <div class="irp-header">
          <div class="irp-header-left">
            <i class="bi bi-printer-fill"></i>
            <span>{{ titulo }}</span>
          </div>
          <div class="irp-header-actions">
            <button class="irp-btn-print" @click="imprimir">
              <i class="bi bi-printer"></i> Imprimir
            </button>
            <button class="irp-close" @click="$emit('close')">
              <i class="bi bi-x-lg"></i>
            </button>
          </div>
        </div>

        <!-- Body -->
        <div class="irp-body">

          <!-- Vista previa -->
          <div id="print-resumen" class="irp-preview">

            <!-- Encabezado del reporte -->
            <div class="rp-empresa">{{ nombreEmpresa }}</div>
            <div class="rp-titulo">{{ titulo }}</div>
            <div class="rp-periodo">
              Periodo: {{ fmtFecha(filtros.desde) }} — {{ fmtFecha(filtros.hasta) }}
              &nbsp;·&nbsp; Tipo: {{ labelTipo }}
              <template v-if="filtros.categoriaNombre">
                &nbsp;·&nbsp; Categoría: {{ filtros.categoriaNombre }}
              </template>
            </div>
            <div class="rp-divider"></div>

            <!-- Tabla productos -->
            <template v-if="modo === 'producto'">
              <table class="rp-table">
                <thead>
                  <tr>
                    <th>Categoría</th>
                    <th>Plato / Producto</th>
                    <th class="ta-r">Cant.</th>
                    <th class="ta-r">Total</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in datos" :key="i">
                    <td>{{ row.categoria }}</td>
                    <td>{{ row.plato }}</td>
                    <td class="ta-r">{{ row.cantidad }}</td>
                    <td class="ta-r">{{ fmt(row.total) }}</td>
                  </tr>
                </tbody>
              </table>
              <div class="rp-divider"></div>
              <div class="rp-totales">
                <div class="rp-tot-row">
                  <span>Total productos</span>
                  <strong>{{ totalCantidad }}</strong>
                </div>
                <div class="rp-tot-row rp-tot-main">
                  <span>Total ventas</span>
                  <strong>{{ fmt(totalDinero) }}</strong>
                </div>
              </div>
            </template>

            <!-- Tabla insumos -->
            <template v-else>
              <table class="rp-table">
                <thead>
                  <tr>
                    <th>Plato</th>
                    <th>Insumo</th>
                    <th>Unidad</th>
                    <th class="ta-r">Cant.</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in datos" :key="i">
                    <td>{{ row.plato }}</td>
                    <td>{{ row.insumo }}</td>
                    <td>{{ row.unidad }}</td>
                    <td class="ta-r">{{ row.cantidad }}</td>
                  </tr>
                </tbody>
              </table>
              <div class="rp-divider"></div>
              <div class="rp-totales">
                <div class="rp-tot-row rp-tot-main">
                  <span>Total registros</span>
                  <strong>{{ datos.length }}</strong>
                </div>
              </div>
            </template>

            <div class="rp-footer">Generado: {{ ahora }}</div>
          </div>

        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { useCompanyStore } from '@/stores/companyStore'

const props = defineProps({
  modo:    { type: String, default: 'producto' }, // 'producto' | 'insumo'
  datos:   { type: Array,  default: () => [] },
  filtros: { type: Object, default: () => ({}) }, // { desde, hasta, tipo, categoriaNombre }
})
defineEmits(['close'])

const companyStore  = useCompanyStore()
const nombreEmpresa = computed(() => companyStore.selectedCompany?.name || 'EasyPOS')

const titulo = computed(() =>
  props.modo === 'producto' ? 'Venta por Producto' : 'Consumo de Insumos'
)

const TIPO_LABELS = { ambos: 'Facturas y Recibos', factura: 'Facturas', recibo: 'Recibos' }
const labelTipo   = computed(() => TIPO_LABELS[props.filtros.tipo] || 'Todos')

const fmtCOP = new Intl.NumberFormat('es-CO', { style:'currency', currency:'COP', minimumFractionDigits:0 })
const fmt    = v => fmtCOP.format(v || 0)

function fmtFecha(iso) {
  if (!iso) return ''
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

const totalCantidad = computed(() => props.datos.reduce((s, r) => s + (r.cantidad || 0), 0))
const totalDinero   = computed(() => props.datos.reduce((s, r) => s + (r.total    || 0), 0))

const ahora = new Intl.DateTimeFormat('es-CO', {
  dateStyle: 'short', timeStyle: 'short', timeZone: 'America/Bogota'
}).format(new Date())

function imprimir() {
  const el = document.getElementById('print-resumen')
  if (!el) return
  const win = window.open('', '_blank', 'width=800,height=700')
  win.document.write(`
    <!DOCTYPE html><html><head><meta charset="utf-8">
    <title>${titulo.value}</title>
    <style>
      body { font-family: Arial, sans-serif; font-size: 12px; color: #1e293b; padding: 20px; }
      .rp-empresa { font-size: 16px; font-weight: 700; text-align: center; margin-bottom: 4px; }
      .rp-titulo  { font-size: 14px; font-weight: 700; text-align: center; color: #1e40af; margin-bottom: 4px; }
      .rp-periodo { font-size: 11px; text-align: center; color: #64748b; margin-bottom: 12px; }
      .rp-divider { border-top: 1.5px solid #e2e8f0; margin: 10px 0; }
      table { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
      th { background: #f1f5f9; padding: 6px 8px; font-size: 10px; text-transform: uppercase; letter-spacing: .4px; border-bottom: 1.5px solid #cbd5e1; text-align: left; }
      td { padding: 5px 8px; border-bottom: 1px solid #f1f5f9; font-size: 11px; }
      .ta-r { text-align: right; }
      .rp-tot-row { display: flex; justify-content: space-between; padding: 3px 0; font-size: 12px; }
      .rp-tot-main { font-size: 14px; font-weight: 700; margin-top: 6px; padding-top: 6px; border-top: 1.5px solid #e2e8f0; }
      .rp-footer { text-align: right; font-size: 10px; color: #94a3b8; margin-top: 20px; }
    </style></head><body>
    ${el.innerHTML}
    </body></html>
  `)
  win.document.close()
  win.focus()
  setTimeout(() => { win.print(); win.close() }, 400)
}
</script>

<style scoped>
.irp-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.5);
  z-index: 9999; display: flex; align-items: center; justify-content: center;
  padding: 16px;
}
.irp-modal {
  background: #fff; border-radius: 14px;
  width: min(720px, 100%); max-height: 90vh;
  display: flex; flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,.25);
}
.irp-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px; border-bottom: 1px solid #e2e8f0;
  background: #1e3a5f; color: #fff; border-radius: 14px 14px 0 0;
  flex-shrink: 0;
}
.irp-header-left { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 700; }
.irp-header-actions { display: flex; align-items: center; gap: 8px; }
.irp-btn-print {
  display: flex; align-items: center; gap: 6px; padding: 6px 14px;
  background: #fff; color: #1e3a5f; border: none; border-radius: 8px;
  font-size: 13px; font-weight: 700; cursor: pointer;
}
.irp-btn-print:hover { background: #e0f2fe; }
.irp-close {
  background: none; border: none; color: #fff; font-size: 18px;
  cursor: pointer; padding: 4px 6px; border-radius: 6px;
}
.irp-close:hover { background: rgba(255,255,255,.15); }
.irp-body { flex: 1; overflow-y: auto; padding: 20px; }

/* Preview del reporte */
.irp-preview {
  max-width: 640px; margin: 0 auto;
  border: 1px solid #e2e8f0; border-radius: 10px; padding: 24px;
  background: #fff;
}
.rp-empresa { font-size: 16px; font-weight: 700; text-align: center; margin-bottom: 4px; color: #1e293b; }
.rp-titulo  { font-size: 14px; font-weight: 700; text-align: center; color: #1e40af; margin-bottom: 4px; }
.rp-periodo { font-size: 11px; text-align: center; color: #64748b; margin-bottom: 12px; }
.rp-divider { border-top: 1.5px solid #e2e8f0; margin: 10px 0; }

.rp-table { width: 100%; border-collapse: collapse; margin-bottom: 8px; font-size: 12px; }
.rp-table th {
  background: #f1f5f9; padding: 6px 8px;
  font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .4px;
  border-bottom: 1.5px solid #cbd5e1; text-align: left;
}
.rp-table td { padding: 5px 8px; border-bottom: 1px solid #f1f5f9; }
.ta-r { text-align: right; }

.rp-totales { max-width: 260px; margin-left: auto; }
.rp-tot-row { display: flex; justify-content: space-between; font-size: 12px; padding: 2px 0; }
.rp-tot-main { font-size: 14px; font-weight: 700; border-top: 1.5px solid #e2e8f0; margin-top: 6px; padding-top: 6px; }

.rp-footer { text-align: right; font-size: 10px; color: #94a3b8; margin-top: 20px; }

/* Responsive */
@media (max-width: 768px) {
  .irp-modal { max-height: 95vh; border-radius: 10px; }
  .irp-body  { padding: 14px; }
  .irp-preview { padding: 16px; }
}
@media (max-width: 576px) {
  .rp-table th:nth-child(1), .rp-table td:nth-child(1) { display: none; }
  .irp-btn-print span { display: none; }
}
</style>
