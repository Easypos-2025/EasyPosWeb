<template>
  <Teleport to="body">
    <div class="modal-overlay" @click.self="$emit('close')">
      <div class="modal-box">

        <div class="mh">
          <div>
            <h3><i class="bi bi-search"></i> Buscar Órdenes</h3>
            <p class="mh-sub">Por placa, número, cliente, estado o mes</p>
          </div>
          <button class="btn-x" @click="$emit('close')"><i class="bi bi-x-lg"></i></button>
        </div>

        <!-- Filtros -->
        <div class="filtros-area">
          <input v-model="q" class="form-control search-input" placeholder="Placa, nº orden, cliente…"
            @keyup.enter="buscar" autofocus />
          <div class="filtros-row">
            <select v-model="filtroEstado" class="form-control form-sel">
              <option value="">Todos los estados</option>
              <option value="abierta">Abierta</option>
              <option value="en_proceso">En proceso</option>
              <option value="terminada">Terminada</option>
              <option value="entregada">Entregada</option>
              <option value="cancelada">Cancelada</option>
            </select>
            <select v-model="filtroMes" class="form-control form-sel">
              <option value="">Todos los meses</option>
              <option v-for="m in MESES" :key="m.val" :value="m.val">{{ m.label }}</option>
            </select>
            <select v-model="filtroAnio" class="form-control form-sel">
              <option v-for="a in anios" :key="a" :value="a">{{ a }}</option>
            </select>
            <button class="btn btn-primary btn-sm" @click="buscar" :disabled="loading">
              <i v-if="loading" class="bi bi-hourglass-split spin"></i>
              <i v-else class="bi bi-search"></i>
              Buscar
            </button>
          </div>
        </div>

        <!-- Resultados -->
        <div class="results-area">
          <div v-if="loading" class="res-loading">
            <i class="bi bi-arrow-repeat spin"></i> Buscando…
          </div>
          <div v-else-if="!buscado" class="res-hint">
            <i class="bi bi-search"></i>
            <p>Ingresa al menos un criterio de búsqueda</p>
          </div>
          <div v-else-if="ordenes.length === 0" class="res-hint">
            <i class="bi bi-inbox"></i>
            <p>No se encontraron órdenes</p>
          </div>
          <div v-else>
            <p class="res-count">{{ ordenes.length }} resultado{{ ordenes.length !== 1 ? 's' : '' }}</p>
            <div class="ordenes-list">
              <div v-for="o in ordenes" :key="o.id" class="orden-row" :class="`or-${o.estado}`">
                <div class="or-left">
                  <span class="or-placa">{{ o.placa_vehiculo }}</span>
                  <span class="or-num">{{ o.numero_orden }}</span>
                  <span :class="['or-badge', `ob-${o.estado}`]">{{ LABELS_ESTADO[o.estado] || o.estado }}</span>
                </div>
                <div class="or-center">
                  <span class="or-cliente">{{ o.convenio_nombre || o.cliente_nombre || '—' }}</span>
                  <span class="or-fecha">{{ fmtFecha(o.fecha_ingreso) }}</span>
                </div>
                <div class="or-right">
                  <span class="or-total">{{ fmt(o.total_orden) }}</span>
                  <div class="or-actions">
                    <button class="btn-act" @click="irAOrden(o)" title="Ver / Editar">
                      <i class="bi bi-pencil-fill"></i>
                    </button>
                    <button class="btn-act print" @click="imprimirOrden(o)" title="Imprimir">
                      <i class="bi bi-printer-fill"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/apis'
import { useCompanyStore } from '@/stores/companyStore'

const emit = defineEmits(['close'])
const router = useRouter()
const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id)

const q            = ref('')
const filtroEstado = ref('')
const filtroMes    = ref(new Date().getMonth() + 1)
const filtroAnio   = ref(new Date().getFullYear())
const loading      = ref(false)
const buscado      = ref(false)
const ordenes      = ref([])

const MESES = [
  { val:1,label:'Enero' },{ val:2,label:'Febrero' },{ val:3,label:'Marzo' },
  { val:4,label:'Abril' },{ val:5,label:'Mayo' },  { val:6,label:'Junio' },
  { val:7,label:'Julio' },{ val:8,label:'Agosto' },{ val:9,label:'Septiembre' },
  { val:10,label:'Octubre' },{ val:11,label:'Noviembre' },{ val:12,label:'Diciembre' },
]
const LABELS_ESTADO = { abierta:'Abierta', en_proceso:'En proceso', terminada:'Terminada', entregada:'Entregada', cancelada:'Cancelada' }
const anioActual    = new Date().getFullYear()
const anios         = computed(() => Array.from({ length: 4 }, (_, i) => anioActual - i))

async function buscar() {
  loading.value = true
  buscado.value = false
  try {
    const { data } = await api.get('/api/talleres/ordenes/buscar', {
      params: {
        company_id: companyId.value,
        q:          q.value || undefined,
        estado:     filtroEstado.value || undefined,
        mes:        filtroMes.value    || undefined,
        anio:       filtroAnio.value   || undefined,
      }
    })
    ordenes.value = data
    buscado.value = true
  } catch { ordenes.value = [] }
  finally { loading.value = false }
}

function irAOrden(o) {
  emit('close')
  router.push(`/talleres/orden/${o.id}`)
}
function imprimirOrden(o) {
  window.open(`/talleres/orden/${o.id}?print=1`, '_blank')
}
function fmt(v) {
  return Number(v||0).toLocaleString('es-CO', { style:'currency', currency:'COP', minimumFractionDigits:0 })
}
function fmtFecha(v) {
  if (!v) return '—'
  return new Date(v).toLocaleDateString('es-CO', { day:'2-digit', month:'short', year:'numeric' })
}
</script>

<style scoped>
.modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,.5); display:flex; align-items:center; justify-content:center; z-index:3000; padding:16px; }
.modal-box     { background:#fff; border-radius:18px; width:100%; max-width:680px; max-height:88vh; display:flex; flex-direction:column; box-shadow:0 24px 64px rgba(0,0,0,.22); }
.mh  { display:flex; align-items:flex-start; justify-content:space-between; padding:18px 22px; border-bottom:1px solid #f1f5f9; }
.mh h3 { font-size:16px; font-weight:700; color:#1e293b; margin:0; display:flex; align-items:center; gap:8px; }
.mh-sub { font-size:12px; color:#64748b; margin:3px 0 0; }
.btn-x { background:none; border:none; font-size:17px; cursor:pointer; color:#94a3b8; }

.filtros-area { padding:16px 22px; border-bottom:1px solid #f1f5f9; display:flex; flex-direction:column; gap:10px; }
.search-input { font-size:15px; padding:10px 14px; border:2px solid #e2e8f0; border-radius:10px; }
.search-input:focus { border-color:#3b82f6; outline:none; }
.filtros-row  { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }

.results-area { flex:1; overflow-y:auto; padding:16px 22px; }
.res-loading, .res-hint { display:flex; flex-direction:column; align-items:center; gap:8px; padding:40px; color:#94a3b8; text-align:center; }
.res-hint .bi { font-size:36px; color:#e2e8f0; }
.res-hint p   { font-size:13px; margin:0; }
.res-count    { font-size:12px; color:#64748b; margin-bottom:10px; font-weight:600; }

.ordenes-list { display:flex; flex-direction:column; gap:8px; }
.orden-row    { display:flex; align-items:center; gap:12px; padding:12px 14px; border-radius:10px; border:1.5px solid #e2e8f0; background:#f8fafc; flex-wrap:wrap; }
.orden-row.or-abierta    { border-left:4px solid #3b82f6; }
.orden-row.or-en_proceso { border-left:4px solid #f59e0b; }
.orden-row.or-terminada  { border-left:4px solid #22c55e; }
.orden-row.or-entregada  { border-left:4px solid #94a3b8; }
.orden-row.or-cancelada  { border-left:4px solid #ef4444; opacity:.65; }

.or-left   { display:flex; align-items:center; gap:8px; min-width:170px; }
.or-placa  { font-size:15px; font-weight:800; letter-spacing:1px; color:#1e293b; }
.or-num    { font-size:11px; color:#94a3b8; font-family:monospace; }
.or-badge  { font-size:10px; font-weight:700; padding:2px 7px; border-radius:20px; }
.ob-abierta    { background:#dbeafe; color:#1d4ed8; } .ob-en_proceso { background:#fef3c7; color:#92400e; }
.ob-terminada  { background:#dcfce7; color:#16a34a; } .ob-entregada  { background:#f1f5f9; color:#64748b; }
.ob-cancelada  { background:#fee2e2; color:#b91c1c; }

.or-center { flex:1; display:flex; flex-direction:column; gap:2px; }
.or-cliente { font-size:13px; color:#374151; font-weight:600; }
.or-fecha   { font-size:11px; color:#94a3b8; }
.or-right   { display:flex; align-items:center; gap:10px; flex-shrink:0; }
.or-total   { font-size:14px; font-weight:800; color:#1e293b; }
.or-actions { display:flex; gap:5px; }
.btn-act    { width:30px; height:30px; border:1.5px solid #e2e8f0; background:#fff; border-radius:7px; cursor:pointer; color:#475569; font-size:12px; display:flex; align-items:center; justify-content:center; transition:all .12s; }
.btn-act:hover       { background:#eff6ff; border-color:#bfdbfe; color:#1d4ed8; }
.btn-act.print:hover { background:#f0fdf4; border-color:#bbf7d0; color:#16a34a; }

.form-control { border:1.5px solid #e2e8f0; border-radius:8px; padding:7px 10px; font-size:13px; outline:none; background:#fff; }
.form-control:focus { border-color:#3b82f6; }
.form-sel { appearance:none; padding-right:26px; background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%2364748b' stroke-width='1.5' fill='none'/%3E%3C/svg%3E"); background-repeat:no-repeat; background-position:right 8px center; }
.btn         { display:inline-flex; align-items:center; gap:5px; padding:8px 14px; border-radius:8px; font-size:13px; font-weight:600; cursor:pointer; border:none; }
.btn-primary { background:#3b82f6; color:#fff; } .btn-primary:hover { background:#2563eb; }
.btn-primary:disabled { opacity:.6; cursor:not-allowed; }
.btn-sm      { padding:7px 12px; font-size:12px; }
.spin { display:inline-block; animation:spin .8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

@media (max-width: 576px) {
  .filtros-row { flex-direction: column; align-items: stretch; }
  .or-left     { flex-wrap: wrap; }
}
</style>
