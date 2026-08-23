<template>
  <ImprimirRecibo
    :receiptData="receiptData"
    :placa="datos.placa || ''"
    :companyId="companyId"
    printersPath="/api/talleres/printers"
    printPath="/api/talleres/imprimir-pos"
    @close="$emit('close')"
  />
</template>

<script setup>
import { computed } from 'vue'
import { useCompanyStore } from '@/stores/companyStore'
import ImprimirRecibo from '@/components/billing/ImprimirRecibo.vue'

const props = defineProps({
  datos: { type: Object, required: true },
  // { id, placa, servicio_nombre, hora_ingreso, minutos_transcurridos,
  //   valor_cobrado, forma_pago, qr_token, receipt_number (opcional) }
})
defineEmits(['close'])

const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id || 0)

const PAGO_LABEL = { efectivo: 'Efectivo', transferencia: 'Transferencia', tarjeta: 'Tarjeta', otro: 'Otro' }

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

const receiptData = computed(() => {
  const d = props.datos
  const val = d.valor_cobrado || 0
  return {
    // receipt_number: si tenemos el de pos_receipts lo usamos; si no, el ID del ingreso
    receipt_number: d.receipt_number || String(d.id),
    ordenNumero:    `PRK-${d.id} · ${formatMin(d.minutos_transcurridos)}`,
    items: [{
      nombre:   `${d.servicio_nombre || 'Servicio'}  ·  Ingreso: ${formatFH(d.hora_ingreso)}`,
      cantidad: 1,
      precio:   val,
    }],
    subtotal: val,
    tip:      0,
    total:    val,
    pagos:    [{ name: PAGO_LABEL[d.forma_pago] || (d.forma_pago || 'Pendiente'), amount: val }],
    fecha:    formatFH(d.hora_ingreso).split(',')[0] || '',
    hora:     new Date().toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' }),
  }
})
</script>
