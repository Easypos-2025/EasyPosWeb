<template>
  <!-- Indicador de turno de caja abierto (sin botón: el cierre va en Cuadre de Caja) -->
  <div v-if="turno" :class="['ti', turno.es_de_hoy ? 'ti--hoy' : 'ti--vieja']"
       :title="turno.es_de_hoy ? 'Trabajando con caja abierta hoy' : 'Caja abierta en una fecha anterior: los recibos se registran con la fecha de apertura. Ciérrela en Cuadre de Caja.'">
    <i :class="turno.es_de_hoy ? 'bi bi-cash-coin' : 'bi bi-exclamation-triangle-fill'"></i>
    <span class="ti-main">{{ turno.caja_nombre }} · Id_Caja #{{ turno.id }}</span>
    <span class="ti-sub">
      {{ turno.es_de_hoy ? `Caja abierta hoy ${hora}` : `Caja abierta del ${fecha} — los recibos llevan esa fecha` }}
    </span>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/apis'

const router = useRouter()
const turno = ref(null)
let timer = null, quitarHook = null

const fecha = computed(() => {
  const d = turno.value?.fecha
  if (!d) return ''
  const [y, m, dd] = d.split('-')
  return `${dd}/${m}/${y}`
})
const hora = computed(() => (turno.value?.opening_datetime || '').slice(11, 16))

async function cargar() {
  if (!localStorage.getItem('token')) { turno.value = null; return }
  try {
    const { data } = await api.get('/api/pos/turno/actual')
    turno.value = data?.id ? data : null
  } catch { turno.value = null }
}

onMounted(() => {
  cargar()
  window.addEventListener('turno-cambio', cargar)
  quitarHook = router.afterEach(() => cargar())
  timer = setInterval(cargar, 120000)
})
onUnmounted(() => {
  window.removeEventListener('turno-cambio', cargar)
  if (quitarHook) quitarHook()
  clearInterval(timer)
})
</script>

<style scoped>
.ti { display: inline-flex; align-items: center; gap: 6px; border-radius: 999px; padding: 4px 12px; font-size: 12px; font-weight: 700; white-space: nowrap; margin-left: 10px; min-width: 0; }
.ti i { font-size: 14px; }
.ti-sub { font-weight: 600; opacity: .9; }
.ti-sub::before { content: '·'; margin-right: 6px; }
.ti--hoy { background: #dcfce7; color: #14532d; border: 1px solid #86efac; }
.ti--vieja { background: #fef3c7; color: #92400e; border: 1px solid #f59e0b; animation: ti-pulse 2s ease-in-out infinite; }
@keyframes ti-pulse { 0%, 100% { box-shadow: 0 0 0 0 rgba(245,158,11,.5); } 50% { box-shadow: 0 0 0 4px rgba(245,158,11,0); } }
@media (max-width: 1024px) {
  .ti-sub { display: none; }
}
@media (max-width: 768px) {
  .ti { padding: 3px 8px; margin-left: 6px; }
  .ti-main { max-width: 120px; overflow: hidden; text-overflow: ellipsis; }
}
@media (max-width: 576px) {
  .ti-main { display: none; }
  .ti { padding: 4px 7px; }
}
</style>
