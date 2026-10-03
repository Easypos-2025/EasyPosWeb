<template>
  <!-- Periodo de consulta: Día / Mes / Año según el Control de Acceso del rol -->
  <div class="ps">
    <div v-if="periodos" class="ps-tipos">
      <button v-for="t in TIPOS" :key="t.v" type="button" :class="['ps-tipo', { active: modelValue.periodo === t.v }]"
              @click="cambiarTipo(t.v)">{{ t.l }}</button>
    </div>

    <div v-if="modelValue.periodo === 'dia'" class="ps-dia" :title="anteriores ? '' : 'Sin permiso para consultar fechas anteriores'">
      <CustomDatePicker :modelValue="modelValue.fecha" :class="{ 'ps-off': !anteriores }" @update:modelValue="setFecha" />
    </div>

    <template v-else>
      <select v-if="modelValue.periodo === 'mes'" class="ps-sel" :value="mes" :disabled="!anteriores" @change="setMes(+$event.target.value)">
        <option v-for="(n, i) in MESES" :key="i" :value="i + 1" :disabled="!anteriores && i + 1 !== mesHoy">{{ n }}</option>
      </select>
      <select class="ps-sel" :value="anio" :disabled="!anteriores" @change="setAnio(+$event.target.value)">
        <option v-for="a in anios" :key="a" :value="a">{{ a }}</option>
      </select>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'

// modelValue: { periodo: 'dia' | 'mes' | 'anio', fecha: 'AAAA-MM-DD' }
const props = defineProps({
  modelValue: { type: Object, required: true },
  anteriores: { type: Boolean, default: false },   // permiso: fechas anteriores
  periodos:   { type: Boolean, default: false },   // permiso: mes y año
  hoy:        { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue', 'change'])

const TIPOS = [{ v: 'dia', l: 'Día' }, { v: 'mes', l: 'Mes' }, { v: 'anio', l: 'Año' }]
const MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

const hoyStr = computed(() => props.hoy || new Date().toLocaleDateString('en-CA'))
const anioHoy = computed(() => +hoyStr.value.slice(0, 4))
const mesHoy = computed(() => +hoyStr.value.slice(5, 7))
const anio = computed(() => +String(props.modelValue.fecha || hoyStr.value).slice(0, 4))
const mes = computed(() => +String(props.modelValue.fecha || hoyStr.value).slice(5, 7))
const anios = computed(() => {
  if (!props.anteriores) return [anioHoy.value]
  return Array.from({ length: 6 }, (_, i) => anioHoy.value - i)
})

const pad = n => String(n).padStart(2, '0')
function emitir(v) {
  emit('update:modelValue', v)
  emit('change', v)
}
function cambiarTipo(t) {
  if (t === props.modelValue.periodo) return
  // Sin permiso de anteriores, mes y año son siempre los actuales
  const base = props.anteriores ? (props.modelValue.fecha || hoyStr.value) : hoyStr.value
  const fecha = t === 'mes' ? `${base.slice(0, 7)}-01` : t === 'anio' ? `${base.slice(0, 4)}-01-01` : (props.anteriores ? base : hoyStr.value)
  emitir({ periodo: t, fecha: t === 'dia' && !props.anteriores ? hoyStr.value : fecha })
}
function setFecha(f) { if (f) emitir({ ...props.modelValue, fecha: f }) }
function setMes(m) { emitir({ ...props.modelValue, fecha: `${anio.value}-${pad(m)}-01` }) }
function setAnio(a) {
  emitir({ ...props.modelValue, fecha: props.modelValue.periodo === 'mes' ? `${a}-${pad(mes.value)}-01` : `${a}-01-01` })
}
</script>

<script>
// Rango (desde, hasta) de un periodo: para las consultas que trabajan con desde/hasta
export function rangoPeriodo({ periodo, fecha }) {
  const [y, m] = [+fecha.slice(0, 4), +fecha.slice(5, 7)]
  const pad = n => String(n).padStart(2, '0')
  if (periodo === 'mes') return { desde: `${y}-${pad(m)}-01`, hasta: `${y}-${pad(m)}-${pad(new Date(y, m, 0).getDate())}` }
  if (periodo === 'anio') return { desde: `${y}-01-01`, hasta: `${y}-12-31` }
  return { desde: fecha, hasta: fecha }
}
</script>

<style scoped>
.ps { display: inline-flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.ps-tipos { display: flex; background: #f1f5f9; border-radius: 10px; padding: 3px; }
.ps-tipo { border: none; background: none; padding: 6px 12px; border-radius: 8px; font-size: 13px; font-weight: 700; color: #64748b; cursor: pointer; }
.ps-tipo.active { background: #fff; color: #1d4ed8; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.ps-dia { min-width: 150px; }
.ps-off { pointer-events: none; opacity: .6; }
.ps-sel { border: 1.5px solid #e2e8f0; border-radius: 10px; padding: 6px 10px; font-size: 13px; background: #fff; min-width: 90px; }
.ps-sel:disabled { opacity: .7; }
@media (max-width: 576px) {
  .ps { width: 100%; }
  .ps-tipos { width: 100%; }
  .ps-tipo { flex: 1; }
  .ps-dia, .ps-sel { flex: 1; }
}
</style>
