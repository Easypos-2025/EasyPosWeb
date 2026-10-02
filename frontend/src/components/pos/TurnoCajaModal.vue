<template>
  <div class="modal-overlay tc-overlay">
    <div class="tc-modal">
      <div class="tc-header">
        <i class="bi bi-cash-coin"></i>
        <div>
          <h3>{{ escritorio ? 'Seleccionar caja' : 'Abrir caja' }}</h3>
          <p>{{ escritorio ? 'La caja se abre desde el programa de escritorio' : 'Antes de operar debes abrir una caja' }}</p>
        </div>
      </div>

      <div class="tc-body">
        <div v-if="loading" class="tc-loading">
          <div class="spinner-border spinner-border-sm text-primary"></div>
          <span>Cargando cajas...</span>
        </div>

        <!-- Empresa con escritorio: se usa un Id_Caja abierto desde el escritorio -->
        <template v-else-if="escritorio">
          <div v-if="!abiertas.length" class="tc-empty">
            <i class="bi bi-pc-display"></i>
            <p>No hay caja abierta.</p>
            <p class="text-muted small">Abra la caja desde el programa de escritorio y vuelva a intentar.</p>
          </div>
          <template v-else>
            <label class="tc-label">Id_Caja abiertos</label>
            <div class="tc-lista">
              <button v-for="a in abiertas" :key="a.id" type="button"
                      :class="['tc-idcaja', { 'tc-idcaja--sel': sel === a.id }]" @click="sel = a.id">
                <span class="tc-idcaja-n">#{{ a.id }}</span>
                <span class="tc-idcaja-i"><b>{{ a.caja_nombre }}</b><small>{{ a.cajero || `Cajero ${a.cajero_id}` }} · {{ fmtFecha(a.fecha) }}</small></span>
                <i v-if="sel === a.id" class="bi bi-check-circle-fill"></i>
              </button>
            </div>
          </template>
        </template>

        <div v-else-if="!cajas.length" class="tc-empty">
          <i class="bi bi-exclamation-triangle"></i>
          <p>No hay cajas configuradas para esta empresa.</p>
          <p class="text-muted small">Crea una caja en Configuración &gt; Cajas.</p>
        </div>

        <template v-else>
          <label class="tc-label">Selecciona una caja</label>
          <div class="tc-cajas">
            <button
              v-for="c in cajas"
              :key="c.id"
              type="button"
              class="tc-caja-btn"
              :class="{ 'tc-caja-btn--sel': form.register_number === c.id, 'tc-caja-btn--ocupada': c.ocupada && !c.ocupada_por_mi }"
              :disabled="c.ocupada && !c.ocupada_por_mi"
              @click="form.register_number = c.id"
            >
              <i class="bi" :class="c.type === 'main' ? 'bi-star-fill' : 'bi-cash-stack'"></i>
              <span>{{ c.name }}</span>
              <small v-if="c.ocupada && !c.ocupada_por_mi">Ocupada</small>
              <small v-else-if="c.ocupada_por_mi">Tu caja</small>
            </button>
          </div>

          <label class="tc-label">Base inicial (efectivo para vueltas)</label>
          <CurrencyInput v-model="form.base_amount" class="form-control" placeholder="0" />
        </template>
      </div>

      <div class="tc-footer">
        <button v-if="!loading && escritorio && !abiertas.length" class="btn btn-outline-secondary w-100" @click="volver">
          <i class="bi bi-arrow-left"></i> Volver
        </button>
        <button v-else-if="escritorio" class="btn btn-primary w-100" :disabled="!sel" @click="usar">
          Usar Id_Caja {{ sel ? '#' + sel : '' }}
        </button>
        <template v-else>
          <button
            class="btn btn-primary w-100"
            :disabled="!form.register_number || saving"
            @click="abrir"
          >
            <i v-if="saving" class="bi bi-arrow-repeat spin"></i>
            {{ saving ? 'Abriendo...' : 'Abrir caja' }}
          </button>
          <button class="btn btn-link w-100 tc-volver" @click="volver">Volver</button>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'
import { guardarIdCaja } from '@/services/idCaja'
import CurrencyInput from '@/components/CurrencyInput.vue'

const emit = defineEmits(['opened'])
const router = useRouter()

const cajas      = ref([])
const loading    = ref(false)
const saving     = ref(false)
const escritorio = ref(false)
const abiertas   = ref([])
const sel        = ref(null)
const form       = ref({ register_number: null, base_amount: 0 })
const avisarCambio = () => window.dispatchEvent(new Event('turno-cambio'))
const fmtFecha = d => { if (!d) return ''; const [y, m, dd] = String(d).split('-'); return `${dd}/${m}/${y}` }

async function cargar() {
  loading.value = true
  try {
    const { data } = await api.get('/api/pos/turno/estado')
    escritorio.value = !!data.escritorio
    if (escritorio.value) {
      abiertas.value = data.abiertas || []
      if (abiertas.value.length === 1) sel.value = abiertas.value[0].id
    } else {
      const r = await api.get('/api/pos/turno/cajas')
      cajas.value = r.data
      const mia = r.data.find(c => c.ocupada_por_mi)
      if (mia) form.value.register_number = mia.id
    }
  } catch {
    showToast('Error cargando cajas disponibles', 'error')
  }
  loading.value = false
}

// Escritorio: el Id_Caja elegido se envía en cada petición (X-Id-Caja) hasta que se cierre
function usar() {
  const a = abiertas.value.find(x => x.id === sel.value)
  if (!a) return
  guardarIdCaja(a.id)
  avisarCambio()
  emit('opened', a)
}

async function abrir() {
  if (!form.value.register_number) return
  saving.value = true
  try {
    const { data } = await api.post('/api/pos/turno/abrir', {
      register_number: form.value.register_number,
      base_amount: Number(form.value.base_amount) || 0,
      pc: navigator.platform || '',
    })
    showToast('Caja abierta', 'success')
    avisarCambio()
    emit('opened', data)
  } catch (e) {
    showToast(e?.response?.data?.detail ?? 'Error al abrir la caja', 'error')
    await cargar()
  }
  saving.value = false
}

function volver() {
  if (window.history.length > 1) router.back()
  else router.push('/dashboard')
}

onMounted(cargar)
</script>

<style scoped>
.tc-overlay {
  position: fixed; inset: 0; background: rgba(15, 23, 42, .55);
  display: flex; align-items: center; justify-content: center;
  z-index: 2000; padding: 16px;
}
.tc-modal {
  background: #fff; border-radius: 14px; width: 100%; max-width: 420px;
  overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,.25);
}
.tc-header {
  display: flex; align-items: center; gap: 12px;
  padding: 18px 20px; background: #eff6ff; border-bottom: 1px solid #dbeafe;
}
.tc-header i { font-size: 26px; color: #2563eb; }
.tc-header h3 { margin: 0; font-size: 16px; color: #1e293b; }
.tc-header p { margin: 2px 0 0; font-size: 12px; color: #64748b; }

.tc-body { padding: 18px 20px; }
.tc-loading, .tc-empty {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  padding: 20px 0; color: #64748b; text-align: center;
}
.tc-empty i { font-size: 24px; color: #f59e0b; }
.tc-empty p { margin: 0; }

.tc-label {
  font-size: 11px; font-weight: 700; color: #64748b;
  text-transform: uppercase; letter-spacing: .4px;
  display: block; margin: 12px 0 6px;
}
.tc-label:first-child { margin-top: 0; }

.tc-cajas { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.tc-caja-btn {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  padding: 12px 8px; border: 1.5px solid #e2e8f0; border-radius: 10px;
  background: #f8fafc; cursor: pointer; font-size: 13px; font-weight: 600; color: #334155;
  transition: all .15s;
}
.tc-caja-btn i { font-size: 18px; color: #64748b; }
.tc-caja-btn:hover:not(:disabled) { border-color: #93c5fd; background: #eff6ff; }
.tc-caja-btn--sel { border-color: #3b82f6; background: #eff6ff; }
.tc-caja-btn--sel i { color: #2563eb; }
.tc-caja-btn--ocupada { opacity: .5; cursor: not-allowed; }
.tc-caja-btn small { font-size: 10px; font-weight: 700; color: #dc2626; text-transform: uppercase; }
.tc-caja-btn--sel small { color: #16a34a; }

.tc-footer { padding: 14px 20px 20px; display: flex; flex-direction: column; gap: 6px; }
.tc-volver { font-size: 13px; color: #64748b; text-decoration: none; }
.tc-lista { display: flex; flex-direction: column; gap: 8px; max-height: 300px; overflow-y: auto; }
.tc-idcaja { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border: 1.5px solid #e2e8f0; border-radius: 10px;
             background: #f8fafc; cursor: pointer; text-align: left; }
.tc-idcaja:hover { border-color: #93c5fd; }
.tc-idcaja--sel { border-color: #3b82f6; background: #eff6ff; }
.tc-idcaja-n { font-family: ui-monospace, monospace; font-weight: 800; color: #1d4ed8; min-width: 56px; }
.tc-idcaja-i { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.tc-idcaja-i b { font-size: 13px; color: #1e293b; }
.tc-idcaja-i small { font-size: 11px; color: #64748b; }
.tc-idcaja > i { color: #2563eb; font-size: 18px; }

.spin { display: inline-block; animation: spin .7s linear infinite; }
@keyframes spin { from { transform: rotate(0) } to { transform: rotate(360deg) } }

@media (max-width: 576px) {
  .tc-cajas { grid-template-columns: 1fr; }
}
</style>
