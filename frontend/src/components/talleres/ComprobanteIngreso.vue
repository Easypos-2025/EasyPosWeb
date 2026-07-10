<template>
  <Teleport to="body">
    <div class="ci-overlay" @click.self="$emit('close')">
      <div class="ci-modal">

        <!-- Toolbar: acciones -->
        <div class="ci-toolbar">
          <span class="ci-toolbar-title">
            <i class="bi bi-receipt-cutoff"></i> Comprobante de Ingreso
          </span>
          <div class="ci-toolbar-btns">
            <button class="ci-btn ci-btn-print" @click="imprimir">
              <i class="bi bi-printer-fill"></i> Imprimir
            </button>
            <button class="ci-btn ci-btn-close" @click="$emit('close')">
              <i class="bi bi-x-lg"></i>
            </button>
          </div>
        </div>

        <!-- Vista previa del comprobante -->
        <div class="ci-preview-wrap">
          <div class="ci-ticket" id="ci-print-area">

            <!-- Encabezado empresa -->
            <div class="ci-company">
              <div class="ci-company-name">{{ companyName }}</div>
              <div class="ci-company-sub">COMPROBANTE DE INGRESO AL TALLER</div>
            </div>

            <div class="ci-divider">- - - - - - - - - - - - - - - - - - - - -</div>

            <!-- Info principal de la orden -->
            <div class="ci-row-kv">
              <span class="ci-k">Orden N°</span>
              <span class="ci-v ci-orden">{{ orden.numero_orden }}</span>
            </div>
            <div class="ci-row-kv">
              <span class="ci-k">Fecha ingreso</span>
              <span class="ci-v">{{ fmtFechaHora(orden.fecha_ingreso) }}</span>
            </div>
            <div v-if="orden.promesa_entrega" class="ci-row-kv">
              <span class="ci-k">Promesa entrega</span>
              <span class="ci-v">{{ fmtFecha(orden.promesa_entrega) }}</span>
            </div>

            <div class="ci-divider">· · · · · · · · · · · · · · · · · · · · ·</div>

            <!-- Vehículo -->
            <div class="ci-section-lbl">VEHÍCULO</div>
            <div class="ci-placa-box">{{ orden.placa_vehiculo }}</div>
            <div v-if="orden.tipo_vehiculo || orden.marca || orden.modelo" class="ci-row-kv">
              <span class="ci-k">Tipo / Marca</span>
              <span class="ci-v">{{ [orden.tipo_vehiculo, orden.marca, orden.modelo, orden.anio].filter(Boolean).join(' · ') }}</span>
            </div>
            <div v-if="orden.color" class="ci-row-kv">
              <span class="ci-k">Color</span>
              <span class="ci-v">{{ orden.color }}</span>
            </div>
            <div v-if="orden.km_ingreso" class="ci-row-kv">
              <span class="ci-k">Km ingreso</span>
              <span class="ci-v">{{ Number(orden.km_ingreso).toLocaleString('es-CO') }} km</span>
            </div>

            <!-- Propietario -->
            <div v-if="orden.cliente_nombre" class="ci-row-kv" style="margin-top:4px">
              <span class="ci-k">Propietario</span>
              <span class="ci-v">{{ orden.cliente_nombre }}</span>
            </div>
            <div v-if="orden.cliente_telefono" class="ci-row-kv">
              <span class="ci-k">Teléfono</span>
              <span class="ci-v">{{ orden.cliente_telefono }}</span>
            </div>
            <div v-if="orden.convenio_nombre" class="ci-row-kv">
              <span class="ci-k">Convenio</span>
              <span class="ci-v ci-convenio">{{ orden.convenio_nombre }}</span>
            </div>

            <div class="ci-divider">· · · · · · · · · · · · · · · · · · · · ·</div>

            <!-- Servicios solicitados -->
            <div class="ci-section-lbl">SERVICIOS SOLICITADOS</div>
            <div v-if="detalles.length" class="ci-items">
              <div v-for="d in detalles" :key="d.id" class="ci-item">
                <span class="ci-item-tipo">{{ tipoLabel(d.tipo_item) }}</span>
                <span class="ci-item-nombre">{{ d.nombre }}</span>
                <span v-if="d.cantidad > 1" class="ci-item-qty">× {{ d.cantidad }}</span>
                <span v-if="d.precio_unitario" class="ci-item-precio">{{ fmt(d.precio_unitario) }}</span>
              </div>
            </div>
            <div v-else-if="orden.diagnostico" class="ci-diagnostico">
              {{ orden.diagnostico }}
            </div>
            <div v-else class="ci-sin-servicios">Sin servicios registrados aún</div>

            <div class="ci-divider">· · · · · · · · · · · · · · · · · · · · ·</div>

            <!-- Personal -->
            <div class="ci-section-lbl">PERSONAL ASIGNADO</div>
            <div v-if="orden.jefe_nombre" class="ci-row-kv">
              <span class="ci-k">Jefe / Supervisor</span>
              <span class="ci-v">{{ orden.jefe_nombre }}</span>
            </div>
            <div v-for="w in workers" :key="w.worker_id" class="ci-row-kv">
              <span class="ci-k">{{ w.profession_nombre || 'Operario' }}</span>
              <span class="ci-v">{{ w.worker_nombre }}</span>
            </div>
            <div v-if="!orden.jefe_nombre && !workers.length" class="ci-row-kv">
              <span class="ci-v" style="color:#aaa">Por asignar</span>
            </div>

            <div class="ci-divider">- - - - - - - - - - - - - - - - - - - - -</div>

            <!-- Código de barras -->
            <div class="ci-barcode-wrap">
              <svg id="ci-barcode"></svg>
              <div class="ci-barcode-num">{{ orden.numero_orden }}</div>
            </div>

            <div class="ci-divider">- - - - - - - - - - - - - - - - - - - - -</div>

            <!-- Pie -->
            <div class="ci-footer">
              <p>Presente este comprobante en caja para realizar su pago.</p>
              <p>El vehículo puede ser identificado por placa o número de orden.</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Zona de impresión oculta -->
    <div id="ci-print-clone" style="display:none"></div>
  </Teleport>
</template>

<script setup>
import { onMounted, nextTick } from 'vue'
import JsBarcode from 'jsbarcode'

const props = defineProps({
  orden:       { type: Object, required: true },
  detalles:    { type: Array,  default: () => [] },
  workers:     { type: Array,  default: () => [] },
  companyName: { type: String, default: '' },
})

defineEmits(['close'])

const TIPO_LABELS = {
  mecanica:    'Mecánica',
  lavado:      'Lavado',
  latoneria:   'Latonería',
  pintura:     'Pintura',
  diagnostico: 'Diagnóstico',
  repuesto:    'Repuesto',
}

function tipoLabel(t) { return TIPO_LABELS[t] || t || '' }

function fmt(v) {
  return Number(v || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 })
}

function fmtFechaHora(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('es-CO', {
      timeZone: 'America/Bogota',
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  } catch { return iso }
}

function fmtFecha(iso) {
  if (!iso) return '—'
  const [y, m, d] = String(iso).split('T')[0].split('-')
  return `${d}/${m}/${y}`
}

function generarBarcode() {
  const num = props.orden?.numero_orden
  if (!num) return
  try {
    JsBarcode('#ci-barcode', num, {
      format:        'CODE128',
      width:         1.8,
      height:        50,
      displayValue:  false,
      margin:        2,
      background:    '#ffffff',
      lineColor:     '#000000',
    })
  } catch (e) { /* silencioso si el num no es válido */ }
}

function imprimir() {
  const contenido = document.getElementById('ci-print-area')
  if (!contenido) return

  const printWin = window.open('', '_blank', 'width=400,height=700')
  printWin.document.write(`
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>Comprobante de Ingreso</title>
      <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
          font-family: 'Courier New', monospace;
          font-size: 12px;
          color: #000;
          background: #fff;
          padding: 8px;
          width: 80mm;
        }
        .ci-company      { text-align: center; margin-bottom: 6px; }
        .ci-company-name { font-size: 14px; font-weight: bold; text-transform: uppercase; }
        .ci-company-sub  { font-size: 10px; margin-top: 2px; }
        .ci-divider      { text-align: center; font-size: 10px; color: #666; margin: 4px 0; }
        .ci-section-lbl  { font-size: 10px; font-weight: bold; text-transform: uppercase;
                           letter-spacing: 0.5px; margin: 6px 0 3px; color: #333; }
        .ci-row-kv       { display: flex; justify-content: space-between; gap: 8px;
                           margin: 2px 0; font-size: 11px; }
        .ci-k            { color: #555; flex-shrink: 0; }
        .ci-v            { font-weight: 600; text-align: right; }
        .ci-orden        { font-size: 13px; font-weight: 900; }
        .ci-placa-box    { font-size: 22px; font-weight: 900; letter-spacing: 3px;
                           text-align: center; border: 2px solid #000;
                           padding: 4px 8px; margin: 4px auto; display: inline-block; }
        .ci-convenio     { background: #eee; padding: 1px 4px; border-radius: 3px; }
        .ci-items        { margin: 2px 0; }
        .ci-item         { display: flex; align-items: center; gap: 4px; font-size: 11px; padding: 2px 0; border-bottom: 1px dotted #ddd; }
        .ci-item-tipo    { font-size: 9px; background: #eee; padding: 1px 4px; border-radius: 3px; flex-shrink: 0; }
        .ci-item-nombre  { flex: 1; }
        .ci-item-qty     { font-size: 10px; color: #666; flex-shrink: 0; }
        .ci-item-precio  { font-size: 10px; font-weight: bold; flex-shrink: 0; }
        .ci-diagnostico  { font-size: 11px; font-style: italic; color: #333; padding: 2px 0; }
        .ci-sin-servicios { font-size: 11px; color: #aaa; }
        .ci-barcode-wrap { text-align: center; margin: 8px 0 4px; }
        .ci-barcode-wrap svg { max-width: 100%; }
        .ci-barcode-num  { font-size: 10px; font-family: monospace; margin-top: 2px; }
        .ci-footer       { text-align: center; font-size: 10px; color: #555; margin-top: 6px; line-height: 1.4; }
        @media print {
          @page { size: 80mm auto; margin: 0; }
          body  { padding: 4px; }
        }
      </style>
    </head>
    <body>
      ${contenido.innerHTML}
      <script>
        if (typeof JsBarcode !== 'undefined') {
          try { JsBarcode('#ci-barcode', document.querySelector('.ci-barcode-num').textContent.trim(), { format:'CODE128', width:1.8, height:50, displayValue:false, margin:2 }); } catch(e){}
        }
        window.onload = function() { window.print(); window.close(); }
      <\/script>
    </body>
    </html>
  `)
  printWin.document.close()
}

onMounted(() => {
  nextTick(() => generarBarcode())
})
</script>

<style scoped>
/* Overlay */
.ci-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.55);
  display: flex; align-items: center; justify-content: center;
  z-index: 4000; padding: 16px;
}
.ci-modal {
  background: #f1f5f9; border-radius: 16px;
  width: 100%; max-width: 480px; max-height: 92vh;
  display: flex; flex-direction: column;
  box-shadow: 0 24px 60px rgba(0,0,0,.25);
  overflow: hidden;
}

/* Toolbar */
.ci-toolbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; background: #1e3a5f; color: #fff;
  flex-shrink: 0;
}
.ci-toolbar-title { font-size: 14px; font-weight: 700; display: flex; align-items: center; gap: 7px; }
.ci-toolbar-btns  { display: flex; gap: 8px; }
.ci-btn { display: flex; align-items: center; gap: 6px; padding: 7px 14px;
          border: none; border-radius: 8px; font-size: 12px; font-weight: 700; cursor: pointer; }
.ci-btn-print { background: #fff; color: #1e3a5f; }
.ci-btn-print:hover { background: #e0f2fe; }
.ci-btn-close { background: rgba(255,255,255,.15); color: #fff; padding: 7px 10px; }
.ci-btn-close:hover { background: rgba(255,255,255,.3); }

/* Preview scroll */
.ci-preview-wrap { flex: 1; overflow-y: auto; padding: 16px; display: flex; justify-content: center; }

/* Ticket POS */
.ci-ticket {
  background: #fff;
  font-family: 'Courier New', Courier, monospace;
  font-size: 12px;
  color: #111;
  width: 100%;
  max-width: 320px;
  padding: 14px 12px;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0,0,0,.1);
}

.ci-company      { text-align: center; margin-bottom: 8px; }
.ci-company-name { font-size: 15px; font-weight: 900; text-transform: uppercase; line-height: 1.2; }
.ci-company-sub  { font-size: 10px; color: #555; margin-top: 2px; }
.ci-divider      { text-align: center; font-size: 10px; color: #bbb; margin: 6px 0; }
.ci-section-lbl  { font-size: 9px; font-weight: 900; text-transform: uppercase;
                   letter-spacing: 1px; color: #666; margin: 8px 0 4px; }

.ci-row-kv  { display: flex; justify-content: space-between; align-items: flex-start;
              gap: 8px; margin: 2px 0; font-size: 11px; }
.ci-k       { color: #666; flex-shrink: 0; }
.ci-v       { font-weight: 700; text-align: right; word-break: break-word; }
.ci-orden   { font-size: 14px; font-weight: 900; color: #1e3a5f; }

.ci-placa-box {
  font-size: 24px; font-weight: 900; letter-spacing: 4px;
  text-align: center; border: 2.5px solid #111;
  padding: 6px 10px; margin: 6px auto; display: table;
}
.ci-convenio { background: #fef3c7; color: #92400e; padding: 1px 5px; border-radius: 4px; font-size: 10px; }

.ci-items        { margin: 3px 0; }
.ci-item {
  display: flex; align-items: flex-start; gap: 5px;
  font-size: 11px; padding: 3px 0;
  border-bottom: 1px dotted #e2e8f0;
}
.ci-item-tipo    { font-size: 9px; background: #f1f5f9; color: #475569; padding: 1px 4px;
                   border-radius: 3px; flex-shrink: 0; margin-top: 1px; }
.ci-item-nombre  { flex: 1; }
.ci-item-qty     { color: #64748b; font-size: 10px; flex-shrink: 0; }
.ci-item-precio  { font-weight: 700; font-size: 11px; flex-shrink: 0; }
.ci-diagnostico  { font-size: 11px; font-style: italic; color: #475569;
                   background: #f8fafc; border-radius: 4px; padding: 4px 6px; margin: 2px 0; }
.ci-sin-servicios { font-size: 11px; color: #94a3b8; text-align: center; padding: 4px; }

.ci-barcode-wrap { text-align: center; margin: 10px 0 4px; }
.ci-barcode-wrap svg { max-width: 100%; }
.ci-barcode-num  { font-size: 10px; font-family: monospace; color: #555; margin-top: 2px; }

.ci-footer {
  text-align: center; font-size: 10px; color: #64748b;
  margin-top: 8px; line-height: 1.5;
}
.ci-footer p { margin: 0; }

@media (max-width: 576px) {
  .ci-modal   { max-height: 98vh; border-radius: 12px; }
  .ci-ticket  { max-width: 100%; }
  .ci-btn span { display: none; }
}
</style>
