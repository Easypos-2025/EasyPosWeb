<template>
  <!-- Eliminar por fecha / eliminar huérfanos (entradas o salidas de inventario) -->
  <div class="lm">
    <button class="lm-btn" @click="abrirFechas" title="Eliminar todos los registros de una fecha">
      <i class="bi bi-calendar-x"></i> <span>Eliminar fecha</span>
    </button>
    <button class="lm-btn lm-btn--warn" @click="eliminarHuerfanos" :disabled="busy" title="Registros de insumos que ya no existen">
      <i class="bi bi-trash3"></i> <span>Eliminar huérfanos</span>
    </button>

    <teleport to="body">
      <div v-if="show" class="lm-overlay" @click.self="show = false">
        <div class="lm-box">
          <div class="lm-hdr">
            <span><i class="bi bi-calendar-x me-1"></i> Eliminar por fecha — {{ titulo }}</span>
            <button class="lm-x" @click="show = false"><i class="bi bi-x-lg"></i></button>
          </div>
          <div class="lm-body">
            <div v-if="loading" class="lm-empty"><span class="spinner-border spinner-border-sm"></span></div>
            <div v-else-if="!fechas.length" class="lm-empty">No hay registros</div>
            <div v-else class="lm-list">
              <div v-for="f in fechas" :key="f.fecha" class="lm-row">
                <div class="lm-info">
                  <span class="lm-fecha">{{ fmtFecha(f.fecha) }}</span>
                  <span class="lm-cnt">{{ f.registros }} registro(s)<template v-if="f.huerfanos"> · {{ f.huerfanos }} huérfano(s)</template></span>
                </div>
                <button class="lm-del" :disabled="busy" @click="eliminarFecha(f)"><i class="bi bi-trash"></i></button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import Swal from 'sweetalert2'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'

const props = defineProps({
  kind: { type: String, required: true, validator: v => ['entries', 'exits'].includes(v) },
})
const emit = defineEmits(['changed'])

const titulo = computed(() => props.kind === 'entries' ? 'Entradas' : 'Salidas')
const show = ref(false)
const loading = ref(false)
const busy = ref(false)
const fechas = ref([])

const fmtFecha = f => { const [y, m, d] = String(f).split('-'); return `${d}/${m}/${y}` }

async function cargarFechas() {
  loading.value = true
  try { fechas.value = (await api.get(`/api/inventory/${props.kind}/dates`)).data }
  catch (e) { showToast(e?.response?.data?.detail || 'Error cargando fechas', 'error') }
  finally { loading.value = false }
}
async function abrirFechas() { show.value = true; await cargarFechas() }

async function eliminarFecha(f) {
  const { isConfirmed } = await Swal.fire({
    title: `¿Eliminar ${titulo.value.toLowerCase()} del ${fmtFecha(f.fecha)}?`,
    html: `<p style="margin:0;color:#475569;font-size:14px">Se eliminarán <b>${f.registros}</b> registro(s) y se recalculará el stock.<br><b>Esta acción no se puede deshacer.</b></p>`,
    icon: 'warning', showCancelButton: true, confirmButtonColor: '#e11d48',
    confirmButtonText: 'Sí, eliminar', cancelButtonText: 'Cancelar',
  })
  if (!isConfirmed) return
  busy.value = true
  try {
    const { data } = await api.delete(`/api/inventory/${props.kind}/date/${f.fecha}`)
    showToast(`${data.deleted} registro(s) eliminado(s)`, 'success')
    await cargarFechas()
    emit('changed')
  } catch (e) { showToast(e?.response?.data?.detail || 'Error al eliminar', 'error') }
  finally { busy.value = false }
}

async function eliminarHuerfanos() {
  busy.value = true
  try {
    const { data } = await api.get(`/api/inventory/${props.kind}/orphans`)
    if (!data.huerfanos) { showToast('No hay registros huérfanos', 'info'); return }
    const { isConfirmed } = await Swal.fire({
      title: `¿Eliminar ${data.huerfanos} registro(s) huérfano(s)?`,
      html: '<p style="margin:0;color:#475569;font-size:14px">Son registros de insumos que ya no existen en el catálogo (se muestran como "Item #…").<br>Se recalculará el stock. <b>No se puede deshacer.</b></p>',
      icon: 'warning', showCancelButton: true, confirmButtonColor: '#e11d48',
      confirmButtonText: 'Sí, eliminar', cancelButtonText: 'Cancelar',
    })
    if (!isConfirmed) return
    const res = await api.delete(`/api/inventory/${props.kind}/orphans`)
    showToast(`${res.data.deleted} registro(s) eliminado(s)`, 'success')
    emit('changed')
  } catch (e) { showToast(e?.response?.data?.detail || 'Error al eliminar', 'error') }
  finally { busy.value = false }
}
</script>

<style scoped>
.lm { display: inline-flex; gap: 6px; flex-wrap: wrap; }
.lm-btn { display: inline-flex; align-items: center; gap: 6px; border: 1.5px solid #fecaca; background: #fff; color: #b91c1c; border-radius: 8px; padding: 7px 12px; font-size: 13px; font-weight: 700; cursor: pointer; white-space: nowrap; }
.lm-btn:hover { background: #fef2f2; }
.lm-btn:disabled { opacity: .6; cursor: not-allowed; }
.lm-btn--warn { border-color: #fed7aa; color: #c2410c; }
.lm-btn--warn:hover { background: #fff7ed; }
.lm-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 2000; padding: 16px; }
.lm-box { background: #fff; border-radius: 16px; width: 100%; max-width: 440px; max-height: 85vh; display: flex; flex-direction: column; overflow: hidden; }
.lm-hdr { display: flex; justify-content: space-between; align-items: center; padding: 14px 16px; border-bottom: 1px solid #f1f5f9; font-weight: 700; color: #1e293b; }
.lm-x { background: none; border: none; color: #94a3b8; font-size: 16px; cursor: pointer; }
.lm-body { padding: 12px 16px; overflow-y: auto; }
.lm-list { display: flex; flex-direction: column; gap: 6px; }
.lm-row { display: flex; align-items: center; gap: 10px; border: 1.5px solid #e2e8f0; border-radius: 10px; padding: 8px 12px; }
.lm-info { flex: 1; display: flex; flex-direction: column; }
.lm-fecha { font-weight: 700; color: #1e293b; font-size: 14px; }
.lm-cnt { font-size: 12px; color: #64748b; }
.lm-del { border: 1.5px solid #fecaca; background: #fff; color: #e11d48; border-radius: 8px; padding: 6px 10px; cursor: pointer; }
.lm-del:disabled { opacity: .5; cursor: not-allowed; }
.lm-empty { text-align: center; color: #94a3b8; padding: 20px; font-size: 13px; }
@media (max-width: 768px) {
  .lm-overlay { padding: 0; align-items: flex-end; }
  .lm-box { border-radius: 16px 16px 0 0; max-height: 90vh; }
}
@media (max-width: 576px) {
  .lm-btn span { display: none; }
  .lm-btn { padding: 7px 10px; }
}
</style>
