<template>
  <div class="cf-page">
    <div class="cf-head">
      <div>
        <h2 class="cf-title"><i class="bi bi-receipt-cutoff me-2"></i>{{ moduleName || 'Configuración Facturación' }}</h2>
        <p class="cf-sub">Propina, impresión, impuestos y textos de recibos y facturas.</p>
      </div>
      <button class="cf-save" :disabled="saving || loading" @click="guardar">
        <span v-if="saving" class="spinner-border spinner-border-sm me-1"></span>
        <i v-else class="bi bi-check-lg me-1"></i>Guardar
      </button>
    </div>

    <div v-if="loading" class="cf-state"><div class="spinner-border text-primary"></div></div>

    <div v-else class="cf-grid">
      <!-- ── Propina ── -->
      <section class="cf-card">
        <h3 class="cf-card-ttl"><i class="bi bi-cash-coin"></i> Propina</h3>
        <label class="cf-switch"><input type="checkbox" v-model="cfg.liquidar_propina" /><span>Liquidar propina</span></label>
        <div class="cf-field">
          <label>Porcentaje de propina (%)</label>
          <input v-model.number="cfg.porcentaje_propina" type="number" min="0" max="100" step="0.5" class="cf-inp cf-inp--num" :disabled="!cfg.liquidar_propina" />
        </div>
        <label class="cf-switch"><input type="checkbox" v-model="cfg.preguntar_valor_propina" :disabled="!cfg.liquidar_propina" /><span>Preguntar el valor de la propina al pagar</span></label>
        <label class="cf-switch"><input type="checkbox" v-model="cfg.imprimir_resolucion_propina" /><span>Imprimir texto de la Superintendencia</span></label>
        <div class="cf-field">
          <label>Texto de la Superintendencia (propina)</label>
          <textarea v-model="cfg.resolucion_propina" rows="5" maxlength="3000" class="cf-inp"></textarea>
        </div>
      </section>

      <!-- ── Impresión ── -->
      <section class="cf-card">
        <h3 class="cf-card-ttl"><i class="bi bi-printer"></i> Impresión</h3>
        <div class="cf-field">
          <label>Impresora de recibos / facturas</label>
          <select v-model="cfg.impresora_facturas" class="cf-inp">
            <option :value="null">— Sin impresora —</option>
            <option v-for="p in $ordenAlfa(printers, 'name')" :key="p.id" :value="p.id">{{ p.name }}{{ p.connection_type ? ` · ${p.connection_type}` : '' }}</option>
          </select>
          <small>Se usa cuando la caja del turno no tiene impresora propia (vista Cajas).</small>
        </div>
        <div class="cf-row">
          <div class="cf-field">
            <label>Copias por impresión</label>
            <input v-model.number="cfg.cantidad_impresiones_factura" type="number" min="0" max="5" class="cf-inp cf-inp--num" />
          </div>
        </div>
        <label class="cf-switch"><input type="checkbox" v-model="cfg.imprimir_encabezado_factura" /><span>Imprimir encabezado (NIT, dirección, teléfono)</span></label>
        <label class="cf-switch"><input type="checkbox" v-model="cfg.imprimir_datos_legales" /><span>Imprimir datos legales</span></label>
        <label class="cf-switch"><input type="checkbox" v-model="cfg.imprimir_datos_cliente" /><span>Imprimir datos del cliente</span></label>
        <label class="cf-switch"><input type="checkbox" v-model="cfg.imprimir_recibo_domiciliario" /><span>Imprimir recibo para el domiciliario</span></label>
        <label class="cf-switch"><input type="checkbox" v-model="cfg.imprimir_logo_factura" /><span>Imprimir logo</span></label>
        <div class="cf-field">
          <label>Nombre del archivo de logo</label>
          <input v-model="cfg.nombre_logo_factura" maxlength="200" class="cf-inp" :disabled="!cfg.imprimir_logo_factura" />
        </div>
        <div class="cf-field">
          <label>Mensaje al pie del recibo / factura</label>
          <input v-model="cfg.mensaje_factura" maxlength="255" class="cf-inp" placeholder="Gracias por su compra" />
        </div>
      </section>

      <!-- ── Impuestos ── -->
      <section class="cf-card">
        <h3 class="cf-card-ttl"><i class="bi bi-percent"></i> Impuestos</h3>
        <div class="cf-row">
          <div class="cf-field">
            <label>IVA (%)</label>
            <input v-model.number="cfg.impuesto_iva" type="number" min="0" max="100" step="0.01" class="cf-inp cf-inp--num" />
          </div>
          <div class="cf-field">
            <label>Impoconsumo (%)</label>
            <input v-model.number="cfg.impuesto_impoconsumo" type="number" min="0" max="100" step="0.01" class="cf-inp cf-inp--num" />
          </div>
          <div class="cf-field">
            <label>Retefuente (%)</label>
            <input v-model.number="cfg.impuesto_rete_fuente" type="number" min="0" max="100" step="0.01" class="cf-inp cf-inp--num" />
          </div>
        </div>
        <label class="cf-switch"><input type="checkbox" v-model="cfg.paga_impuesto" /><span>Paga impuesto</span></label>
        <label class="cf-switch"><input type="checkbox" v-model="cfg.precios_incluyen_impuesto" /><span>Los precios incluyen impuesto</span></label>
      </section>

      <!-- ── Numeración y cliente por defecto ── -->
      <section class="cf-card">
        <h3 class="cf-card-ttl"><i class="bi bi-123"></i> Numeración y cliente por defecto</h3>
        <div class="cf-field">
          <label>Texto de numeración</label>
          <input v-model="cfg.texto_numeracion" maxlength="100" class="cf-inp" placeholder="Factura" />
        </div>
        <div class="cf-row">
          <div class="cf-field">
            <label>Longitud consecutivo sistema</label>
            <input v-model.number="cfg.longitud_factura_sistema" type="number" min="0" max="99" class="cf-inp cf-inp--num" />
          </div>
          <div class="cf-field">
            <label>Longitud consecutivo manual</label>
            <input v-model.number="cfg.longitud_factura_manual" type="number" min="0" max="99" class="cf-inp cf-inp--num" />
          </div>
        </div>
        <div class="cf-field">
          <label>Nombre cliente por defecto</label>
          <input v-model="cfg.nombre_cliente_facturacion_varia" maxlength="100" class="cf-inp" />
        </div>
        <div class="cf-row">
          <div class="cf-field">
            <label>Documento cliente por defecto</label>
            <input v-model="cfg.codigo_cliente_facturacion_varia" maxlength="100" class="cf-inp" inputmode="numeric" />
          </div>
          <div class="cf-field">
            <label>Id cliente por defecto</label>
            <input v-model.number="cfg.id_cliente_facturacion_varia" type="number" min="0" class="cf-inp cf-inp--num" />
          </div>
        </div>
      </section>

      <!-- ── Operación ── -->
      <section class="cf-card">
        <h3 class="cf-card-ttl"><i class="bi bi-sliders"></i> Operación</h3>
        <label class="cf-switch"><input type="checkbox" v-model="cfg.usar_precuenta" /><span>Usar precuenta</span></label>
        <label class="cf-switch"><input type="checkbox" v-model="cfg.usar_comanda_corta" /><span>Usar comanda corta</span></label>
        <label class="cf-switch"><input type="checkbox" v-model="cfg.activar_precio_x_mayor" /><span>Activar precio por mayor</span></label>
        <label class="cf-switch"><input type="checkbox" v-model="cfg.usa_lector_barras" /><span>Usa lector de código de barras</span></label>
        <div class="cf-field">
          <label>Tipo de moneda</label>
          <input v-model.number="cfg.tipo_moneda" type="number" min="0" max="9" class="cf-inp cf-inp--num" />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'
import { useModuleName } from '@/composables/useModuleName'

const { moduleName } = useModuleName()
const cfg      = ref({})
const printers = ref([])
const loading  = ref(true)
const saving   = ref(false)

async function cargar() {
  loading.value = true
  try {
    const { data } = await api.get('/api/config-facturacion')
    cfg.value = { ...data.config, impresora_facturas: data.config.impresora_facturas || null }
    printers.value = data.printers
  } catch (e) {
    showToast(e?.response?.data?.detail || 'Error cargando la configuración', 'error')
  }
  loading.value = false
}

async function guardar() {
  saving.value = true
  try {
    const { data } = await api.put('/api/config-facturacion', cfg.value)
    cfg.value = { ...data.config, impresora_facturas: data.config.impresora_facturas || null }
    showToast('Configuración guardada', 'success')
  } catch (e) {
    const d = e?.response?.data?.detail
    showToast(Array.isArray(d) ? 'Revise los valores ingresados' : (d || 'Error al guardar'), 'error')
  }
  saving.value = false
}

onMounted(cargar)
</script>

<style scoped>
.cf-page { padding: 20px 24px 32px; }
.cf-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 16px; }
.cf-title { font-size: 22px; font-weight: 800; color: #1e293b; margin: 0; }
.cf-sub { font-size: 13px; color: #64748b; margin: 2px 0 0; }
.cf-save { display: inline-flex; align-items: center; background: linear-gradient(90deg,#1e3a5f,#1d4ed8); color: #fff; border: none;
  border-radius: 10px; padding: 10px 22px; font-weight: 700; font-size: 14px; cursor: pointer; white-space: nowrap; }
.cf-save:disabled { opacity: .6; cursor: not-allowed; }
.cf-state { display: flex; justify-content: center; padding: 60px; }
.cf-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 14px; align-items: start; }
.cf-card { background: #fff; border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,.08); padding: 16px; display: flex; flex-direction: column; gap: 10px; }
.cf-card-ttl { font-size: 14px; font-weight: 800; color: #1e3a5f; margin: 0 0 2px; display: flex; align-items: center; gap: 8px; }
.cf-field { display: flex; flex-direction: column; gap: 4px; flex: 1; min-width: 0; }
.cf-field label { font-size: 12px; font-weight: 700; color: #475569; }
.cf-field small { font-size: 11px; color: #94a3b8; }
.cf-row { display: flex; gap: 10px; }
.cf-inp { border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 8px 10px; font-size: 14px; color: #1e293b; background: #fff; width: 100%; }
.cf-inp:focus { outline: none; border-color: #1d4ed8; }
.cf-inp:disabled { background: #f8fafc; color: #94a3b8; }
.cf-inp--num { text-align: right; }
textarea.cf-inp { resize: vertical; font-size: 13px; }
.cf-switch { display: flex; align-items: center; gap: 10px; font-size: 14px; color: #334155; cursor: pointer; }
.cf-switch input { width: 18px; height: 18px; accent-color: #1d4ed8; flex-shrink: 0; }

@media (max-width: 1024px) {
  .cf-grid { grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); }
}
@media (max-width: 768px) {
  .cf-page { padding: 14px 12px 90px; }
  .cf-head { flex-direction: column; }
  .cf-save { position: fixed; left: 12px; right: 12px; bottom: 56px; justify-content: center; z-index: 50; box-shadow: 0 6px 20px rgba(29,78,216,.35); }
  .cf-grid { grid-template-columns: 1fr; }
}
@media (max-width: 576px) {
  .cf-title { font-size: 18px; }
  .cf-row { flex-direction: column; gap: 10px; }
  .cf-card { padding: 12px; }
  .cf-switch { font-size: 13px; }
}
</style>
