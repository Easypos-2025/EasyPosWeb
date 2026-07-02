<template>
  <div class="dash-cv">

    <!-- Marca de agua -->
    <div class="wm-bg" aria-hidden="true">
      <i class="bi bi-gem        wm-icon-1"></i>
      <i class="bi bi-arrow-left-right wm-icon-2"></i>
      <i class="bi bi-gem        wm-icon-3"></i>
    </div>

    <!-- Header -->
    <div class="dash-header">
      <div class="dash-header-left">
        <h6 class="dash-empresa">{{ empresa }}</h6>
        <span class="dash-perfil-tag">
          <i class="bi bi-shop-window"></i> Compra - Ventas
        </span>
      </div>
      <div class="dash-header-right">
        <CustomDatePicker v-model="fecha" />
        <button class="btn-reload" @click="cargar" :disabled="loading" title="Recargar">
          <i class="bi bi-arrow-repeat" :class="{ spin: loading }"></i>
        </button>
      </div>
    </div>

    <!-- Sin BD externa configurada -->
    <div v-if="errorMsg" class="estado-aviso">
      <i class="bi bi-database-exclamation"></i>
      <p>{{ errorMsg }}</p>
    </div>

    <!-- Loading -->
    <div v-else-if="loading" class="estado-loading">
      <div class="spinner-border text-primary" role="status"></div>
      <span>Cargando movimientos...</span>
    </div>

    <!-- Sin datos -->
    <div v-else-if="grupos.length === 0" class="estado-vacio">
      <i class="bi bi-inbox"></i>
      <p>Sin movimientos para el {{ fechaFormateada }}</p>
    </div>

    <!-- KPIs por grupo -->
    <div v-else class="kpi-bar">
      <div v-for="grupo in grupos" :key="'kpi-'+grupo.descripcion" class="kpi-card">
        <span class="kpi-label">{{ grupo.descripcion }}</span>
        <span class="kpi-value">{{ formatCurrency(grupo.total) }}</span>
        <span class="kpi-count">{{ grupo.items.length }} mov.</span>
      </div>
    </div>

    <!-- Tarjetas por grupo -->
    <div v-if="grupos.length > 0" class="grupos-grid">
      <div v-for="grupo in grupos" :key="grupo.descripcion" class="grupo-card">
        <div class="grupo-header">
          <i class="bi bi-tag-fill"></i>
          {{ grupo.descripcion }}
          <span class="grupo-count">{{ grupo.items.length }}</span>
        </div>
        <div class="grupo-total">
          Total: <strong>{{ formatCurrency(grupo.total) }}</strong>
        </div>
        <div class="grupo-tabla">
          <div class="tabla-head">
            <span>Fecha</span>
            <span>Nro. Transacción</span>
            <span class="text-end">Valor</span>
          </div>
          <div v-for="item in grupo.items" :key="item.nro_movimiento" class="tabla-row">
            <span>{{ formatFecha(item.fecha_movimiento) }}</span>
            <span class="nro-trans">{{ item.nro_transaccion }}</span>
            <span class="text-end valor">{{ formatCurrency(item.valor_movimiento) }}</span>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useCompanyStore } from '@/stores/companyStore'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'
import api from '@/services/apis'

const companyStore = useCompanyStore()
const empresa  = computed(() => companyStore.selectedCompany?.name ?? '')
const loading  = ref(false)
const errorMsg = ref('')
const movimientos = ref([])

const hoy = () => new Date().toISOString().slice(0, 10)
const fecha = ref(hoy())

const fechaFormateada = computed(() =>
  new Intl.DateTimeFormat('es-CO', { day: '2-digit', month: 'long', year: 'numeric' })
    .format(new Date(fecha.value + 'T12:00:00'))
)

const grupos = computed(() => {
  const map = {}
  for (const m of movimientos.value) {
    const key = m.descripcion || '(Sin descripción)'
    if (!map[key]) map[key] = { descripcion: key, items: [], total: 0 }
    map[key].items.push(m)
    map[key].total += Number(m.valor_movimiento) || 0
  }
  return Object.values(map).sort((a, b) => a.descripcion.localeCompare(b.descripcion))
})

function formatCurrency(val) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 })
    .format(val ?? 0)
}

function formatFecha(val) {
  if (!val) return '—'
  return new Intl.DateTimeFormat('es-CO', { day: '2-digit', month: '2-digit', year: 'numeric' })
    .format(new Date(val))
}

async function cargar() {
  const cid = companyStore.selectedCompany?.id
  if (!cid) return
  loading.value  = true
  errorMsg.value = ''
  movimientos.value = []
  try {
    const res = await api.get('/api/compraventa/movimientos', {
      params: { company_id: cid, fecha: fecha.value }
    })
    movimientos.value = res.data.movimientos || []
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || 'Error cargando movimientos'
  } finally {
    loading.value = false
  }
}

watch(fecha, cargar)
onMounted(cargar)
</script>

<style scoped>
.dash-cv {
  position: relative;
  min-height: 80vh;
  padding: 0 24px 48px;
  overflow: hidden;
}

/* Marca de agua */
.wm-bg { position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden; }
.wm-icon-1 { position: absolute; font-size: 380px; color: #b45309; opacity: 0.05; bottom: -60px; right: -50px; transform: rotate(-20deg); }
.wm-icon-2 { position: absolute; font-size: 180px; color: #1e3a5f; opacity: 0.04; top: 60px; left: -30px; transform: rotate(12deg); }
.wm-icon-3 { position: absolute; font-size: 90px; color: #f59e0b; opacity: 0.06; top: 180px; right: 18%; transform: rotate(30deg); }

/* Header */
.dash-header {
  position: relative; z-index: 1;
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 20px 0 16px;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 20px;
}
.dash-empresa { margin: 0 0 4px; font-size: 18px; font-weight: 700; color: #1e3a5f; }
.dash-perfil-tag {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 11px; font-weight: 600; color: #b45309;
  background: #fef3c7; border: 1px solid #fcd34d;
  border-radius: 20px; padding: 2px 10px; text-transform: uppercase;
}
.dash-header-right { display: flex; align-items: center; gap: 8px; }
.btn-reload {
  width: 36px; height: 36px; border-radius: 8px;
  border: 1.5px solid #e2e8f0; background: #fff;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; color: #64748b; font-size: 16px;
  transition: border-color .15s;
}
.btn-reload:hover { border-color: #1e40af; color: #1e40af; }

/* Estados */
.estado-aviso, .estado-loading, .estado-vacio {
  position: relative; z-index: 1;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 12px; padding: 60px 20px; color: #94a3b8; text-align: center;
}
.estado-aviso .bi, .estado-vacio .bi { font-size: 40px; }
.estado-aviso { color: #f59e0b; }
.estado-aviso .bi { font-size: 48px; }

/* KPI bar */
.kpi-bar {
  position: relative; z-index: 1;
  display: flex; flex-wrap: wrap; gap: 10px;
  margin-bottom: 20px;
}
.kpi-card {
  flex: 1 1 160px;
  background: #fff;
  border: 1.5px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px 16px;
  display: flex; flex-direction: column; gap: 2px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.kpi-label {
  font-size: 11px; font-weight: 700; color: #64748b;
  text-transform: uppercase; letter-spacing: 0.5px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.kpi-value {
  font-size: 16px; font-weight: 800; color: #1e3a5f;
  line-height: 1.2;
}
.kpi-count {
  font-size: 11px; color: #94a3b8;
}

/* Grid de grupos */
.grupos-grid {
  position: relative; z-index: 1;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

/* Tarjeta de grupo */
.grupo-card {
  background: #fff;
  border: 1.5px solid #e2e8f0;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.grupo-header {
  display: flex; align-items: center; gap: 8px;
  background: linear-gradient(135deg, #1e3a5f 0%, #1e40af 100%);
  color: #fff; font-size: 14px; font-weight: 700;
  padding: 12px 16px;
}
.grupo-header .bi { color: #fcd34d; font-size: 14px; }
.grupo-count {
  margin-left: auto;
  background: rgba(255,255,255,0.2);
  border-radius: 20px; padding: 1px 8px;
  font-size: 11px; font-weight: 700;
}
.grupo-total {
  padding: 8px 16px;
  font-size: 12px; color: #64748b;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}
.grupo-total strong { color: #1e3a5f; font-size: 13px; }

/* Tabla interna */
.grupo-tabla { padding: 8px 0; }
.tabla-head {
  display: grid; grid-template-columns: 90px 1fr 110px;
  padding: 4px 16px 6px;
  font-size: 10px; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: 0.5px;
  border-bottom: 1px solid #f1f5f9;
}
.tabla-row {
  display: grid; grid-template-columns: 90px 1fr 110px;
  padding: 6px 16px;
  font-size: 12px; color: #334155;
  border-bottom: 1px solid #f8fafc;
  transition: background .1s;
}
.tabla-row:last-child { border-bottom: none; }
.tabla-row:hover { background: #f8fafc; }
.nro-trans { color: #64748b; font-size: 11px; }
.valor { font-weight: 600; color: #1e3a5f; }
.text-end { text-align: right; }

/* Spin */
.spin { animation: spin .7s linear infinite; display: inline-block; }
@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }

/* Responsive */
@media (max-width: 768px) {
  .dash-cv { padding: 0 16px 40px; }
  .grupos-grid { grid-template-columns: 1fr; }
  .dash-header { flex-direction: column; align-items: flex-start; gap: 10px; }
  .dash-header-right { width: 100%; }
}
@media (max-width: 576px) {
  .dash-cv { padding: 0 12px 32px; }
  .tabla-head, .tabla-row { grid-template-columns: 80px 1fr 95px; font-size: 11px; padding: 5px 12px; }
}
</style>
