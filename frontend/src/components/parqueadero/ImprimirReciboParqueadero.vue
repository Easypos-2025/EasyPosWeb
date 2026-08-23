<template>
  <Teleport to="body">
    <div class="prk-overlay">
      <div class="prk-modal">

        <!-- Header -->
        <div class="prk-header">
          <div class="prk-header-left">
            <i class="bi bi-printer-fill"></i>
            <span>Recibo de Parqueadero</span>
            <span class="prk-num">#{{ datos.id }}</span>
          </div>
          <button class="prk-close" @click="$emit('close')"><i class="bi bi-x-lg"></i></button>
        </div>

        <!-- Body -->
        <div class="prk-body">

          <!-- Preview del recibo -->
          <div class="prk-col prk-col-preview">
            <div class="prk-section-title"><i class="bi bi-eye"></i> Vista Previa</div>
            <div class="recibo-wrap" id="print-recibo-parqueadero">
              <div class="recibo">
                <div class="r-empresa">{{ nombreEmpresa }}</div>
                <div class="r-titulo">RECIBO DE PARQUEADERO</div>

                <div class="r-num">#{{ datos.id }}</div>

                <div class="r-divider">--------------------------------</div>

                <div class="r-meta">
                  <div class="r-meta-row"><span>Placa:</span><strong>{{ datos.placa }}</strong></div>
                  <div class="r-meta-row"><span>Servicio:</span><span>{{ datos.servicio_nombre }}</span></div>
                  <div class="r-meta-row"><span>Ingreso:</span><span>{{ formatFH(datos.hora_ingreso) }}</span></div>
                  <div class="r-meta-row"><span>Salida:</span><span>{{ horaActual }}</span></div>
                  <div class="r-meta-row"><span>Tiempo:</span><span>{{ formatMin(datos.minutos_transcurridos) }}</span></div>
                </div>

                <div class="r-divider">--------------------------------</div>

                <div class="r-total-wrap">
                  <span class="r-total-label">TOTAL</span>
                  <span class="r-total-val">{{ fmt(datos.valor_cobrado) }}</span>
                </div>

                <div class="r-pago">
                  <span>Forma de pago:</span>
                  <span>{{ labelPago(datos.forma_pago) }}</span>
                </div>

                <div class="r-divider">--------------------------------</div>

                <div v-if="datos.qr_token" class="r-token">
                  Token: {{ datos.qr_token }}
                </div>

                <div class="r-gracias">¡Gracias por preferirnos!</div>
              </div>
            </div>
          </div>

          <!-- Opciones -->
          <div class="prk-col prk-col-opts">
            <div class="prk-section-title"><i class="bi bi-printer"></i> Opciones de Impresión</div>

            <button class="prk-opt-btn prk-opt-pdf" @click="imprimirSistema">
              <div class="prk-opt-icon"><i class="bi bi-file-earmark-pdf-fill"></i></div>
              <div class="prk-opt-info">
                <span class="prk-opt-label">PDF / Impresora del sistema</span>
                <span class="prk-opt-desc">Abre el diálogo del navegador. Elige cualquier impresora o guarda como PDF.</span>
              </div>
              <i class="bi bi-chevron-right prk-opt-arrow"></i>
            </button>

            <div class="prk-sys-note">
              <i class="bi bi-info-circle"></i>
              El recibo se imprime en formato de 58mm. Para impresoras POS configúralas en ajustes del sistema.
            </div>
          </div>

        </div>

        <!-- Footer -->
        <div class="prk-footer">
          <button class="prk-btn-cerrar" @click="$emit('close')">
            <i class="bi bi-check2-circle"></i> Listo, cerrar
          </button>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { useCompanyStore } from '@/stores/companyStore'
import { showToast } from '@/utils/toast'

const props = defineProps({
  datos: { type: Object, required: true },
  // { id, placa, servicio_nombre, hora_ingreso, minutos_transcurridos,
  //   valor_cobrado, forma_pago, qr_token }
})
defineEmits(['close'])

const companyStore  = useCompanyStore()
const nombreEmpresa = computed(() => companyStore.selectedCompany?.name || 'EasyPosWeb')
const horaActual    = computed(() => new Date().toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' }))

function formatFH(dt) {
  if (!dt) return '—'
  const d = new Date(String(dt).replace(' ', 'T'))
  return isNaN(d) ? String(dt) : d.toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' })
}

function formatMin(min) {
  if (!min) return '0 min'
  if (min < 60) return `${min} min`
  return `${Math.floor(min / 60)}h ${min % 60}min`
}

function labelPago(v) {
  return { efectivo: 'Efectivo', transferencia: 'Transferencia', tarjeta: 'Tarjeta', otro: 'Otro' }[v] || v
}

function fmt(v) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v || 0)
}

function imprimirSistema() {
  const w = window.open('', '_blank', 'width=420,height=700,menubar=no,toolbar=no')
  if (!w) { showToast('Permite ventanas emergentes para imprimir', 'warn'); return }
  const empresa = nombreEmpresa.value
  const d = props.datos
  w.document.write(`<!DOCTYPE html><html lang="es"><head>
<meta charset="utf-8">
<title>Recibo #${d.id}</title>
<style>
@page { margin: 4mm; size: 58mm auto; }
body { font-family: 'Courier New', monospace; font-size: 12px; line-height: 1.5; color: #1a1a1a; margin: 0; padding: 8px; width: 58mm; }
.r-empresa  { text-align: center; font-size: 13px; font-weight: 700; }
.r-titulo   { text-align: center; font-size: 10px; font-weight: 700; letter-spacing: .5px; margin-top: 2px; }
.r-num      { text-align: center; font-size: 22px; font-weight: 900; letter-spacing: 2px; margin: 8px 0 4px; }
.r-divider  { text-align: center; font-size: 10px; margin: 6px 0; color: #999; }
.r-row      { display: flex; justify-content: space-between; font-size: 11px; gap: 8px; margin: 2px 0; }
.r-row span:first-child { color: #666; white-space: nowrap; }
.r-row strong { font-size: 13px; font-weight: 900; letter-spacing: 1px; }
.r-total    { display: flex; justify-content: space-between; align-items: baseline; margin: 6px 0 2px; }
.r-total-l  { font-size: 11px; font-weight: 700; }
.r-total-v  { font-size: 18px; font-weight: 900; }
.r-pago     { display: flex; justify-content: space-between; font-size: 10px; color: #555; }
.r-token    { font-size: 9px; color: #999; text-align: center; word-break: break-all; margin-top: 4px; }
.r-gracias  { text-align: center; font-size: 10px; margin-top: 10px; font-style: italic; }
</style>
</head><body>
<div class="r-empresa">${empresa}</div>
<div class="r-titulo">RECIBO DE PARQUEADERO</div>
<div class="r-num">#${d.id}</div>
<div class="r-divider">--------------------------------</div>
<div class="r-row"><span>Placa:</span><strong>${d.placa || ''}</strong></div>
<div class="r-row"><span>Servicio:</span><span>${d.servicio_nombre || ''}</span></div>
<div class="r-row"><span>Ingreso:</span><span>${formatFH(d.hora_ingreso)}</span></div>
<div class="r-row"><span>Salida:</span><span>${horaActual.value}</span></div>
<div class="r-row"><span>Tiempo:</span><span>${formatMin(d.minutos_transcurridos)}</span></div>
<div class="r-divider">--------------------------------</div>
<div class="r-total"><span class="r-total-l">TOTAL</span><span class="r-total-v">${fmt(d.valor_cobrado)}</span></div>
<div class="r-pago"><span>Forma de pago:</span><span>${labelPago(d.forma_pago)}</span></div>
<div class="r-divider">--------------------------------</div>
${d.qr_token ? `<div class="r-token">Token: ${d.qr_token}</div>` : ''}
<div class="r-gracias">¡Gracias por preferirnos!</div>
</body></html>`)
  w.document.close()
  w.focus()
  setTimeout(() => { w.print(); w.close() }, 350)
}
</script>

<style scoped>
/* ── Overlay ── */
.prk-overlay {
  position: fixed; inset: 0;
  background: rgba(15,23,42,.7);
  display: flex; align-items: center; justify-content: center;
  z-index: 9100; padding: 16px;
}

/* ── Modal ── */
.prk-modal {
  background: #fff; border-radius: 14px;
  width: 100%; max-width: 720px; max-height: 90vh;
  display: flex; flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,.25); overflow: hidden;
}

/* ── Header ── */
.prk-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; background: #0f172a; color: #fff; flex-shrink: 0;
}
.prk-header-left { display: flex; align-items: center; gap: 10px; font-size: 16px; font-weight: 700; }
.prk-num { background: rgba(255,255,255,.15); padding: 2px 10px; border-radius: 20px; font-size: 13px; }
.prk-close { background: none; border: none; color: rgba(255,255,255,.7); cursor: pointer; font-size: 18px; }
.prk-close:hover { color: #fff; }

/* ── Body ── */
.prk-body { display: flex; flex: 1; overflow: hidden; }
.prk-col { display: flex; flex-direction: column; padding: 16px 20px; overflow-y: auto; gap: 12px; }
.prk-col-preview { flex: 1; border-right: 1px solid #e2e8f0; }
.prk-col-opts    { flex: 1; }
.prk-section-title { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .5px; color: #64748b; display: flex; align-items: center; gap: 6px; flex-shrink: 0; }

/* ── Recibo (preview) ── */
.recibo-wrap { display: flex; justify-content: center; }
.recibo {
  width: 220px;
  background: #fff; padding: 16px 12px;
  border: 1px solid #e2e8f0; border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px; line-height: 1.5;
  color: #1a1a1a;
}
.r-empresa  { text-align: center; font-size: 13px; font-weight: 700; }
.r-titulo   { text-align: center; font-size: 10px; font-weight: 700; letter-spacing: .5px; margin-top: 2px; }
.r-num      { text-align: center; font-size: 22px; font-weight: 900; letter-spacing: 2px; margin: 8px 0 4px; }
.r-divider  { color: #94a3b8; text-align: center; font-size: 10px; margin: 6px 0; }
.r-meta     { display: flex; flex-direction: column; gap: 3px; }
.r-meta-row { display: flex; justify-content: space-between; font-size: 11px; gap: 8px; }
.r-meta-row span:first-child { color: #64748b; white-space: nowrap; }
.r-meta-row strong { font-size: 13px; font-weight: 900; letter-spacing: 1px; }
.r-total-wrap { display: flex; justify-content: space-between; align-items: baseline; margin: 4px 0; }
.r-total-label { font-size: 11px; font-weight: 700; }
.r-total-val   { font-size: 18px; font-weight: 900; }
.r-pago  { display: flex; justify-content: space-between; font-size: 10px; color: #475569; }
.r-token { font-size: 9px; color: #94a3b8; text-align: center; word-break: break-all; }
.r-gracias { text-align: center; font-size: 10px; margin-top: 8px; font-style: italic; }

/* ── Opciones ── */
.prk-opt-btn {
  display: flex; align-items: center; gap: 12px;
  padding: 14px; border-radius: 10px; border: 1.5px solid #e2e8f0;
  background: #fff; cursor: pointer; text-align: left; width: 100%;
  transition: all .15s;
}
.prk-opt-btn:hover { border-color: #93c5fd; background: #eff6ff; }
.prk-opt-icon { width: 40px; height: 40px; border-radius: 10px; background: #fef2f2; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.prk-opt-pdf .prk-opt-icon { background: #fef2f2; }
.prk-opt-pdf .prk-opt-icon i { color: #dc2626; font-size: 20px; }
.prk-opt-info { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.prk-opt-label { font-size: 14px; font-weight: 600; color: #1e293b; }
.prk-opt-desc  { font-size: 12px; color: #64748b; }
.prk-opt-arrow { color: #94a3b8; font-size: 14px; flex-shrink: 0; }

.prk-sys-note { background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 10px 14px; font-size: 12px; color: #0369a1; display: flex; align-items: flex-start; gap: 8px; line-height: 1.4; }

/* ── Footer ── */
.prk-footer { display: flex; justify-content: flex-end; padding: 14px 20px; border-top: 1px solid #e2e8f0; background: #f8fafc; flex-shrink: 0; }
.prk-btn-cerrar { display: flex; align-items: center; gap: 8px; padding: 10px 24px; background: #0f172a; color: #fff; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; }
.prk-btn-cerrar:hover { background: #1e293b; }

/* ── Responsive ── */
@media (max-width: 640px) {
  .prk-body { flex-direction: column; overflow-y: auto; }
  .prk-col-preview { border-right: none; border-bottom: 1px solid #e2e8f0; }
}

/* ── PRINT: solo muestra el recibo, oculta todo lo demás ── */
@media print {
  body > *:not(#prk-print-root) { display: none !important; }
  .prk-overlay { position: static !important; background: none !important; padding: 0 !important; }
  .prk-modal   { box-shadow: none !important; border-radius: 0 !important; max-height: none !important; }
  .prk-header, .prk-col-opts, .prk-footer { display: none !important; }
  .prk-body    { display: block !important; }
  .prk-col-preview { border: none !important; padding: 0 !important; }
  .recibo-wrap { justify-content: flex-start !important; }
  .recibo      { border: none !important; width: auto !important; max-width: 58mm !important; }
  @page { margin: 4mm; size: 58mm auto; }
}
</style>
