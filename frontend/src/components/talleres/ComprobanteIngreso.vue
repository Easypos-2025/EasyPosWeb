<template>
  <Teleport to="body">
    <div class="ci-overlay" @click.self="$emit('close')">
      <div class="ci-modal">

        <!-- Toolbar -->
        <div class="ci-toolbar">
          <span class="ci-toolbar-title">
            <i class="bi bi-receipt-cutoff"></i> Comprobante de Ingreso
          </span>
          <div class="ci-toolbar-btns">
            <button class="ci-btn ci-btn-print" @click="abrirPanel">
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

            <div class="ci-company">
              <div class="ci-company-name">{{ companyName }}</div>
              <div class="ci-company-sub">COMPROBANTE DE INGRESO AL TALLER</div>
            </div>

            <div class="ci-divider">- - - - - - - - - - - - - - - - - - - - -</div>

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

            <div class="ci-barcode-wrap">
              <svg id="ci-barcode"></svg>
              <div class="ci-barcode-num">{{ orden.numero_orden }}</div>
            </div>

            <div class="ci-divider">- - - - - - - - - - - - - - - - - - - - -</div>

            <div class="ci-footer">
              <p>Presente este comprobante en caja para realizar su pago.</p>
              <p>El vehículo puede ser identificado por placa o número de orden.</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Panel selector de impresoras ──────────────────────────────────── -->
    <div v-if="showPanel" class="cp-panel-overlay" @click.self="showPanel = false">
      <div class="cp-panel">

        <div class="cp-panel-header">
          <span><i class="bi bi-printer-fill"></i> Seleccionar impresora</span>
          <button class="cp-panel-close" @click="showPanel = false">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>

        <!-- Tabs -->
        <div class="cp-tabs">
          <button :class="['cp-tab', { active: panelTab === 'taller' }]" @click="panelTab = 'taller'">
            <i class="bi bi-printer-fill"></i> Impresoras del taller
          </button>
          <button :class="['cp-tab', { active: panelTab === 'sistema' }]" @click="panelTab = 'sistema'">
            <i class="bi bi-display"></i> Sistema / PDF
          </button>
        </div>

        <!-- Tab: impresoras del taller -->
        <div v-if="panelTab === 'taller'" class="cp-tab-body">
          <div v-if="loadingPrinters" class="cp-empty">
            <i class="bi bi-arrow-repeat spin"></i> Cargando impresoras…
          </div>
          <div v-else-if="printers.length === 0" class="cp-empty">
            <i class="bi bi-printer" style="font-size:28px;display:block;margin-bottom:6px;color:#cbd5e1"></i>
            No hay impresoras configuradas para este taller.
            <br/>
            <a href="/pos/impresoras" target="_blank" class="cp-link">Ir a configurar impresoras →</a>
          </div>
          <button
            v-for="p in printers"
            :key="p.id"
            class="cp-printer-btn"
            @click="imprimirPos(p)"
            :disabled="imprimiendoPosId === p.id"
          >
            <div class="cp-printer-icon">
              <i class="bi bi-printer-fill"></i>
            </div>
            <div class="cp-printer-info">
              <span class="cp-printer-name">{{ p.name }}</span>
              <span class="cp-printer-sub">
                <span v-if="p.ip">{{ p.ip }}:{{ p.port }}</span>
                <span v-else class="cp-bt-label"><i class="bi bi-bluetooth"></i> Imprime via diálogo del sistema</span>
                <span v-if="p.connection_type" class="cp-chip">{{ p.connection_type }}</span>
              </span>
            </div>
            <i v-if="imprimiendoPosId === p.id" class="bi bi-arrow-repeat spin cp-arrow"></i>
            <i v-else class="bi bi-chevron-right cp-arrow"></i>
          </button>
        </div>

        <!-- Tab: sistema / PDF -->
        <div v-if="panelTab === 'sistema'" class="cp-tab-body">
          <button class="cp-printer-btn cp-sistema" @click="imprimirSistema">
            <div class="cp-printer-icon cp-icon-pdf">
              <i class="bi bi-file-earmark-pdf-fill"></i>
            </div>
            <div class="cp-printer-info">
              <span class="cp-printer-name">PDF / Impresora del sistema</span>
              <span class="cp-printer-sub">Abre el diálogo del navegador. Elige cualquier impresora instalada o guarda como PDF.</span>
            </div>
            <i class="bi bi-chevron-right cp-arrow"></i>
          </button>
          <div class="cp-note">
            <i class="bi bi-info-circle"></i>
            Usa esta opción si tu impresora está instalada como dispositivo del sistema operativo o quieres guardar como PDF.
          </div>
        </div>

      </div>
    </div>

    <!-- Zona de impresión oculta -->
    <div id="ci-print-clone" style="display:none"></div>
  </Teleport>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import JsBarcode from 'jsbarcode'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'

const props = defineProps({
  orden:       { type: Object, required: true },
  detalles:    { type: Array,  default: () => [] },
  workers:     { type: Array,  default: () => [] },
  companyName: { type: String, default: '' },
  companyId:   { type: Number, default: null },
})

defineEmits(['close'])

// ── Estado panel impresoras ───────────────────────────────────────────────────
const showPanel        = ref(false)
const panelTab         = ref('taller')
const printers         = ref([])
const loadingPrinters  = ref(false)
const imprimiendoPosId = ref(null)

async function abrirPanel() {
  showPanel.value  = true
  panelTab.value   = 'taller'
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
    // Bluetooth/USB: el backend no puede conectarse, usar sistema del móvil
    showPanel.value = false
    imprimirSistema()
    return
  }
  imprimiendoPosId.value = printer.id
  try {
    await api.post('/api/talleres/imprimir-comprobante', {
      company_id:   props.companyId,
      printer_id:   printer.id,
      orden:        props.orden,
      detalles:     props.detalles,
      workers:      props.workers,
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

// ── Helpers ───────────────────────────────────────────────────────────────────
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
      format:       'CODE128',
      width:        1.8,
      height:       50,
      displayValue: false,
      margin:       2,
      background:   '#ffffff',
      lineColor:    '#000000',
    })
  } catch (e) { /* silencioso */ }
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

/* ── Panel selector de impresoras ──────────────────────────────────────────── */
.cp-panel-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.45);
  display: flex; align-items: flex-end; justify-content: center;
  z-index: 5000;
}
.cp-panel {
  background: #fff;
  border-radius: 20px 20px 0 0;
  width: 100%; max-width: 520px;
  max-height: 75vh;
  display: flex; flex-direction: column;
  box-shadow: 0 -8px 40px rgba(0,0,0,.2);
  overflow: hidden;
}
.cp-panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; background: #1e293b; color: #fff;
  font-size: 15px; font-weight: 700; flex-shrink: 0;
}
.cp-panel-close {
  background: rgba(255,255,255,.15); border: none; color: #fff;
  border-radius: 8px; padding: 6px 10px; cursor: pointer; font-size: 14px;
}
.cp-panel-close:hover { background: rgba(255,255,255,.3); }

.cp-tabs {
  display: flex; border-bottom: 2px solid #e2e8f0; flex-shrink: 0;
}
.cp-tab {
  flex: 1; padding: 12px 8px; border: none; background: none;
  font-size: 13px; font-weight: 600; color: #64748b; cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 6px;
  border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all .15s;
}
.cp-tab:hover { color: #1e293b; background: #f8fafc; }
.cp-tab.active { color: #1d4ed8; border-bottom-color: #3b82f6; background: #eff6ff; }

.cp-tab-body {
  flex: 1; overflow-y: auto; padding: 12px 16px;
  display: flex; flex-direction: column; gap: 10px;
}

.cp-printer-btn {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px; border: 1.5px solid #e2e8f0; border-radius: 12px;
  background: #fff; cursor: pointer; width: 100%; text-align: left;
  transition: all .15s; flex-shrink: 0;
}
.cp-printer-btn:hover:not(:disabled) { border-color: #3b82f6; background: #eff6ff; }
.cp-printer-btn:disabled { opacity: .5; cursor: not-allowed; }
.cp-sistema { border-color: #dc2626; background: #fff5f5; }
.cp-sistema:hover { background: #fee2e2 !important; border-color: #b91c1c !important; }

.cp-printer-icon {
  width: 40px; height: 40px; border-radius: 10px;
  background: #dcfce7; color: #16a34a;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; flex-shrink: 0;
}
.cp-icon-pdf { background: #fee2e2; color: #dc2626; }

.cp-printer-info {
  flex: 1; display: flex; flex-direction: column; gap: 3px; min-width: 0;
}
.cp-printer-name { font-size: 14px; font-weight: 700; color: #1e293b; }
.cp-printer-sub  { font-size: 11px; color: #64748b; line-height: 1.4; }
.cp-arrow        { color: #94a3b8; font-size: 14px; flex-shrink: 0; }
.cp-chip {
  display: inline-block; background: #f1f5f9; color: #475569;
  font-size: 10px; padding: 1px 6px; border-radius: 20px; margin-left: 6px;
}

.cp-empty {
  font-size: 13px; color: #94a3b8; padding: 24px 12px;
  text-align: center; line-height: 1.8;
}
.cp-link { color: #3b82f6; text-decoration: underline; }

.cp-note {
  font-size: 12px; color: #64748b; background: #f8fafc;
  border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 14px;
  display: flex; gap: 8px; align-items: flex-start; line-height: 1.5;
}
.cp-note i { flex-shrink: 0; margin-top: 2px; color: #3b82f6; }
.cp-bt-label { color: #6366f1; font-style: italic; }

@media (max-width: 576px) {
  .ci-modal   { max-height: 98vh; border-radius: 12px; }
  .ci-ticket  { max-width: 100%; }
  .cp-panel   { max-height: 85vh; border-radius: 16px 16px 0 0; }
}

.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from { transform: rotate(0) } to { transform: rotate(360deg) } }
</style>
