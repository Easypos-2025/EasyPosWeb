<template>
  <Teleport to="body">
    <div class="ir-overlay">
      <div class="ir-modal">

        <!-- ── Header ── -->
        <div class="ir-header">
          <div class="ir-header-left">
            <i class="bi bi-printer-fill"></i>
            <span>Imprimir Recibo</span>
            <span class="ir-rn">#{{ receiptData.receipt_number }}</span>
          </div>
          <button class="ir-close" @click="cerrar"><i class="bi bi-x-lg"></i></button>
        </div>

        <!-- ── Body ── -->
        <div class="ir-body">

          <!-- COLUMNA IZQUIERDA: Preview del recibo -->
          <div class="ir-col ir-col-preview">
            <div class="ir-section-title">
              <i class="bi bi-eye"></i> Vista Previa
            </div>

            <!-- Recibo (también sirve como zona de impresión) -->
            <div class="recibo-wrap" id="print-receipt">
              <div class="recibo">
                <div class="r-empresa">{{ nombreEmpresa }}</div>
                <div class="r-titulo">RECIBO DE VENTA</div>
                <div class="r-meta">
                  <div>Recibo N°: <strong>{{ receiptData.receipt_number }}</strong></div>
                  <div>Orden: <strong>{{ receiptData.ordenNumero }}</strong></div>
                  <div v-if="placa">Placa: <strong>{{ placa }}</strong></div>
                  <div>Fecha: <strong>{{ receiptData.fecha }}</strong></div>
                  <div v-if="receiptData.hora">Hora: <strong>{{ receiptData.hora }}</strong></div>
                </div>
                <div class="r-divider">--------------------------------</div>

                <table class="r-items">
                  <thead>
                    <tr>
                      <th class="r-th-name">Descripción</th>
                      <th class="r-th-cant">Cant</th>
                      <th class="r-th-val">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="it in receiptData.items" :key="it.nombre">
                      <td>{{ it.nombre }}</td>
                      <td class="ta-c">{{ it.cantidad }}</td>
                      <td class="ta-r">{{ fmt(it.precio * it.cantidad) }}</td>
                    </tr>
                  </tbody>
                </table>

                <div class="r-divider">--------------------------------</div>

                <div class="r-totales">
                  <div class="r-tot-row">
                    <span>Subtotal</span>
                    <span>{{ fmt(receiptData.subtotal) }}</span>
                  </div>
                  <div v-if="receiptData.tip" class="r-tot-row">
                    <span>{{ receiptData.tipLabel || 'Propina' }}</span>
                    <span>{{ fmt(receiptData.tip) }}</span>
                  </div>
                  <div class="r-tot-row r-tot-grand">
                    <span>TOTAL</span>
                    <span>{{ fmt(receiptData.total) }}</span>
                  </div>
                </div>

                <div class="r-divider">--------------------------------</div>

                <div class="r-pagos">
                  <div class="r-pagos-title">Formas de pago:</div>
                  <div v-for="p in receiptData.pagos" :key="p.name" class="r-pago-row">
                    <span>{{ p.name }}</span>
                    <span>{{ fmt(p.amount) }}</span>
                  </div>
                </div>

                <div class="r-divider">--------------------------------</div>
                <div class="r-gracias">¡Gracias por su preferencia!</div>
              </div>
            </div>
          </div>

          <!-- COLUMNA DERECHA: Opciones de impresión con tabs -->
          <div class="ir-col ir-col-options">

            <!-- Tabs -->
            <div class="ir-tabs">
              <button :class="['ir-tab', { active: tab === 'configuradas' }]"
                      @click="tab = 'configuradas'">
                <i class="bi bi-printer-fill"></i> Impresoras del taller
              </button>
              <button :class="['ir-tab', { active: tab === 'sistema' }]"
                      @click="tab = 'sistema'">
                <i class="bi bi-display"></i> Sistema / PDF
              </button>
            </div>

            <!-- TAB: Impresoras configuradas (DEFAULT) -->
            <div v-if="tab === 'configuradas'" class="ir-tab-body">
              <div v-if="loadingPrinters" class="ir-pos-empty">
                <i class="bi bi-arrow-repeat spin"></i> Cargando impresoras…
              </div>
              <div v-else-if="printers.length === 0" class="ir-pos-empty">
                <i class="bi bi-printer" style="font-size:28px;display:block;margin-bottom:6px;color:#cbd5e1"></i>
                No hay impresoras configuradas para este taller.
                <br/>
                <a href="/pos/impresoras" target="_blank" class="ir-link">Ir a configurar impresoras →</a>
              </div>
              <button
                v-for="p in printers"
                :key="p.id"
                class="ir-opt-btn ir-opt-pos"
                @click="imprimirPos(p)"
                :disabled="imprimiendoPosId === p.id"
              >
                <div class="ir-opt-icon ir-icon-pos">
                  <i class="bi bi-printer-fill"></i>
                </div>
                <div class="ir-opt-info">
                  <span class="ir-opt-label">{{ p.name }}</span>
                  <span class="ir-opt-desc">
                    <span v-if="p.ip">{{ p.ip }}:{{ p.port }}</span>
                    <span v-else>Sin IP configurada</span>
                    <span v-if="p.connection_type" class="ir-conn-chip">{{ p.connection_type }}</span>
                  </span>
                </div>
                <i v-if="imprimiendoPosId === p.id" class="bi bi-arrow-repeat spin ir-opt-arrow"></i>
                <i v-else class="bi bi-chevron-right ir-opt-arrow"></i>
              </button>
            </div>

            <!-- TAB: Sistema / PDF -->
            <div v-if="tab === 'sistema'" class="ir-tab-body">
              <button class="ir-opt-btn ir-opt-pdf" @click="imprimirSistema">
                <div class="ir-opt-icon"><i class="bi bi-file-earmark-pdf-fill"></i></div>
                <div class="ir-opt-info">
                  <span class="ir-opt-label">PDF / Impresora del sistema</span>
                  <span class="ir-opt-desc">Abre el diálogo del navegador. Elige cualquier impresora instalada o guarda como PDF.</span>
                </div>
                <i class="bi bi-chevron-right ir-opt-arrow"></i>
              </button>
              <div class="ir-sys-note">
                <i class="bi bi-info-circle"></i>
                Usa esta opción si tu impresora está instalada como dispositivo del sistema operativo o quieres guardar el recibo como PDF.
              </div>
            </div>

          </div>

        </div>

        <!-- ── Footer ── -->
        <div class="ir-footer">
          <button class="ir-btn-cerrar" @click="cerrar">
            <i class="bi bi-check2-circle"></i> Listo, cerrar
          </button>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import api from "@/services/apis"
import { useCompanyStore } from "@/stores/companyStore"
import { showToast } from "@/utils/toast"

const props = defineProps({
  receiptData: { type: Object, required: true },
  placa:       { type: String, default: "" },
  companyId:   { type: Number, required: true },
})

const emit = defineEmits(["close"])

const companyStore   = useCompanyStore()
const printers         = ref([])
const loadingPrinters  = ref(true)
const imprimiendoPosId = ref(null)
const tab              = ref('configuradas')

const nombreEmpresa = computed(
  () => companyStore.selectedCompany?.name || "EasyPos"
)

// ── Carga impresoras ──────────────────────────────────────────────────────────
async function loadPrinters() {
  loadingPrinters.value = true
  try {
    const res = await api.get("/api/talleres/printers", {
      params: { company_id: props.companyId },
    })
    printers.value = res.data || []
  } catch {
    printers.value = []
  }
  loadingPrinters.value = false
}

// ── Imprimir sistema (PDF / cualquier impresora) ──────────────────────────────
function imprimirSistema() {
  window.print()
}

// ── Imprimir en impresora POS (via backend socket) ───────────────────────────
async function imprimirPos(printer) {
  if (!printer.ip) {
    showToast(`La impresora "${printer.name}" no tiene IP configurada`, "warning", 3000)
    return
  }
  imprimiendoPosId.value = printer.id
  try {
    await api.post("/api/talleres/imprimir-pos", {
      company_id:     props.companyId,
      printer_id:     printer.id,
      receipt_number: props.receiptData.receipt_number,
    })
    showToast(`Enviado a "${printer.name}"`, "success", 2000)
  } catch (e) {
    showToast(e?.response?.data?.detail || `Error al enviar a "${printer.name}"`, "error", 3000)
  }
  imprimiendoPosId.value = null
}

function cerrar() {
  emit("close")
}

// ── Formato moneda ────────────────────────────────────────────────────────────
function fmt(v) {
  return new Intl.NumberFormat("es-CO", {
    style: "currency", currency: "COP", maximumFractionDigits: 0,
  }).format(v || 0)
}

onMounted(loadPrinters)
</script>

<style scoped>
/* ── Overlay ─────────────────────────────────────────────────────────── */
.ir-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9100;
  padding: 16px;
}

/* ── Modal ───────────────────────────────────────────────────────────── */
.ir-modal {
  background: #fff;
  border-radius: 14px;
  width: 100%;
  max-width: 820px;
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 64px rgba(0,0,0,.3);
  overflow: hidden;
}

/* ── Header ──────────────────────────────────────────────────────────── */
.ir-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: #1e293b;
  color: #fff;
  flex-shrink: 0;
}
.ir-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 700;
}
.ir-rn {
  background: rgba(255,255,255,.15);
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 13px;
}
.ir-close {
  background: none;
  border: none;
  color: rgba(255,255,255,.7);
  cursor: pointer;
  font-size: 18px;
  padding: 4px;
  border-radius: 6px;
}
.ir-close:hover { color: #fff; }

/* ── Body ────────────────────────────────────────────────────────────── */
.ir-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.ir-col {
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 16px 20px;
  gap: 12px;
}

.ir-col-preview {
  flex: 0 0 300px;
  border-right: 1px solid #e2e8f0;
  background: #f8fafc;
}

.ir-col-options {
  flex: 1;
}

/* ── Section title ───────────────────────────────────────────────────── */
.ir-section-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .5px;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

/* ── Recibo preview ──────────────────────────────────────────────────── */
.recibo-wrap {
  flex: 1;
  display: flex;
  justify-content: center;
}

.recibo {
  background: #fff;
  border: 1px dashed #cbd5e1;
  border-radius: 6px;
  padding: 16px 14px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #1e293b;
  width: 240px;
  line-height: 1.6;
}

.r-empresa { font-weight: 900; font-size: 13px; text-align: center; }
.r-titulo  { font-weight: 700; text-align: center; margin-bottom: 6px; letter-spacing: 1px; }
.r-meta    { font-size: 11px; margin-bottom: 4px; }
.r-meta div { display: flex; justify-content: space-between; gap: 8px; }

.r-divider { color: #94a3b8; font-size: 11px; margin: 4px 0; letter-spacing: 0; text-align: center; }

.r-items { width: 100%; border-collapse: collapse; font-size: 11px; }
.r-items th { font-size: 10px; font-weight: 700; padding-bottom: 3px; }
.r-th-name { text-align: left; }
.r-th-cant, .r-th-val { text-align: right; }
.r-items td { padding: 1px 0; vertical-align: top; }
.r-items td:nth-child(2) { text-align: center; }
.r-items td:nth-child(3) { text-align: right; white-space: nowrap; }

.r-totales { font-size: 11px; }
.r-tot-row { display: flex; justify-content: space-between; gap: 8px; }
.r-tot-grand { font-weight: 900; font-size: 13px; margin-top: 3px; }

.r-pagos { font-size: 11px; }
.r-pagos-title { font-weight: 700; margin-bottom: 2px; }
.r-pago-row { display: flex; justify-content: space-between; gap: 8px; }

.r-gracias { text-align: center; font-style: italic; font-size: 11px; color: #64748b; }

.ta-c { text-align: center; }
.ta-r { text-align: right; }

/* ── Opciones de impresión ───────────────────────────────────────────── */
.ir-opt-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 1.5px solid #e2e8f0;
  border-radius: 12px;
  background: #fff;
  cursor: pointer;
  width: 100%;
  text-align: left;
  transition: all .15s;
  flex-shrink: 0;
}
.ir-opt-btn:hover:not(:disabled) { border-color: #3b82f6; background: #eff6ff; }
.ir-opt-btn:disabled { opacity: .5; cursor: not-allowed; }

.ir-opt-pdf { border-color: #dc2626; background: #fff5f5; }
.ir-opt-pdf:hover:not(:disabled) { background: #fee2e2; border-color: #b91c1c; }

.ir-opt-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #dbeafe;
  color: #1d4ed8;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}
.ir-opt-pdf .ir-opt-icon { background: #fee2e2; color: #dc2626; }
.ir-icon-pos { background: #dcfce7; color: #16a34a; }

.ir-opt-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}
.ir-opt-label { font-size: 14px; font-weight: 700; color: #1e293b; }
.ir-opt-desc  { font-size: 11px; color: #64748b; line-height: 1.4; }
.ir-opt-arrow { color: #94a3b8; font-size: 14px; flex-shrink: 0; }

/* ── Tabs ────────────────────────────────────────────────────────────── */
.ir-tabs {
  display: flex;
  border-bottom: 2px solid #e2e8f0;
  gap: 0;
  flex-shrink: 0;
}
.ir-tab {
  flex: 1;
  padding: 10px 12px;
  border: none;
  background: none;
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all .15s;
}
.ir-tab:hover { color: #1e293b; background: #f8fafc; }
.ir-tab.active { color: #1d4ed8; border-bottom-color: #3b82f6; background: #eff6ff; }

.ir-tab-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-top: 4px;
  flex: 1;
  overflow-y: auto;
}

.ir-sys-note {
  font-size: 12px;
  color: #64748b;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px 14px;
  display: flex;
  gap: 8px;
  align-items: flex-start;
  line-height: 1.5;
}
.ir-sys-note i { flex-shrink: 0; margin-top: 2px; color: #3b82f6; }

/* ── Sección POS ─────────────────────────────────────────────────────── */
.ir-loading-chip { color: #3b82f6; font-size: 12px; }
.ir-pos-empty { font-size: 13px; color: #94a3b8; padding: 20px 12px; text-align: center; line-height: 1.8; }
.ir-link { color: #3b82f6; text-decoration: underline; }
.ir-conn-chip {
  display: inline-block;
  background: #f1f5f9;
  color: #475569;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 20px;
  margin-left: 6px;
}

/* ── Footer ──────────────────────────────────────────────────────────── */
.ir-footer {
  padding: 14px 20px;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
  display: flex;
  justify-content: flex-end;
  flex-shrink: 0;
}
.ir-btn-cerrar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 26px;
  background: #1e293b;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: background .15s;
}
.ir-btn-cerrar:hover { background: #0f172a; }

/* ── Print CSS: solo imprime el recibo ───────────────────────────────── */
@media print {
  body > *:not(.ir-overlay) { display: none !important; }
  .ir-overlay { position: static !important; background: none !important; padding: 0 !important; }
  .ir-modal { box-shadow: none !important; max-height: none !important; border-radius: 0 !important; }
  .ir-header, .ir-col-options, .ir-footer { display: none !important; }
  .ir-col-preview {
    border: none !important;
    background: none !important;
    flex: 1 !important;
    padding: 0 !important;
  }
  .ir-body { overflow: visible !important; }
  .recibo-wrap { justify-content: flex-start; }
  .recibo { border: none !important; width: 100% !important; max-width: 300px; font-size: 11pt; }
}

/* ── Responsive ──────────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .ir-body { flex-direction: column; }
  .ir-col-preview { flex: 0 0 auto; border-right: none; border-bottom: 1px solid #e2e8f0; }
  .recibo { width: 100%; max-width: 280px; }
}

@media (max-width: 576px) {
  .ir-modal { max-height: 98vh; border-radius: 10px; }
  .ir-col-preview { display: none; }
}

.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from { transform: rotate(0) } to { transform: rotate(360deg) } }
</style>
