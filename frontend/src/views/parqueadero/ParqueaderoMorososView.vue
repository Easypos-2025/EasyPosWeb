<template>
  <div class="pq-view">
    <div class="pq-header">
      <h2 class="pq-title"><i class="bi bi-exclamation-triangle-fill" style="color:#ef4444"></i> {{ moduleName }}</h2>
      <button class="btn-refresh" @click="cargar" :disabled="loading">
        <i class="bi bi-arrow-clockwise"></i>
      </button>
    </div>

    <div v-if="loading" class="pq-loader">Cargando...</div>
    <div v-else-if="!morosos.length" class="pq-empty">
      <i class="bi bi-check-circle" style="font-size:2.5rem;color:#22c55e"></i>
      <p>Sin morosos activos</p>
    </div>

    <div v-else>
      <p class="morosos-count">{{ morosos.length }} abonado(s) con mora pendiente, ordenados por días de mora.</p>
      <div class="pq-table-wrap">
        <table class="pq-table">
          <thead>
            <tr>
              <th>Mora</th>
              <th>Placa</th>
              <th>Titular</th>
              <th>Teléfono</th>
              <th>Venció</th>
              <th>Último Pago</th>
              <th>Valor Mensual</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in morosos" :key="m.id">
              <td>
                <span class="mora-badge" :class="moraClass(m.dias_mora)">
                  {{ m.dias_mora != null && !isNaN(Number(m.dias_mora)) ? Number(m.dias_mora) : '?' }} días
                </span>
              </td>
              <td class="td-placa">{{ m.placa }}</td>
              <td>{{ m.nombre_titular }}</td>
              <td>
                <a v-if="m.telefono" :href="`tel:${m.telefono}`" class="tel-link">
                  <i class="bi bi-telephone-fill"></i> {{ m.telefono }}
                </a>
                <span v-else>—</span>
              </td>
              <td>{{ m.fecha_fin }}</td>
              <td>{{ m.ultimo_pago || '—' }}</td>
              <td class="td-mono">${{ (Number(m.valor_mensualidad) || 0).toLocaleString() }}</td>
              <td class="td-actions">
                <router-link :to="`/parqueadero/mensualidades/${m.id}`" class="btn-icon" title="Ver detalle">
                  <i class="bi bi-eye-fill"></i>
                </router-link>
                <button class="btn-icon btn-check" title="Marcar activo (pagó)" @click="marcarActivo(m)">
                  <i class="bi bi-check-circle-fill"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Confirm activar -->
    <div v-if="confirmActivar" class="pq-overlay" @click.self="confirmActivar = null">
      <div class="pq-modal" style="max-width:340px">
        <div class="pq-modal-head">
          <h3>Confirmar activación</h3>
          <button class="btn-icon" @click="confirmActivar = null"><i class="bi bi-x-lg"></i></button>
        </div>
        <div style="padding:20px;font-size:14px;line-height:1.5">
          ¿Confirmar que <strong>{{ confirmActivar.nombre_titular || 'este abonado' }}</strong> realizó el pago?
          Se marcará como <strong>activo</strong>.
        </div>
        <div class="pq-modal-foot">
          <button class="btn-pq-ghost" @click="confirmActivar = null">No</button>
          <button class="btn-pq-primary" @click="ejecutarMarcarActivo"><i class="bi bi-check2"></i> Sí, activar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useCompanyStore } from '@/stores/companyStore'
import { useModuleName } from '@/composables/useModuleName'
import { showToast } from '@/utils/toast'
import api from '@/services/apis'

const companyStore = useCompanyStore()
const { moduleName } = useModuleName()

const morosos = ref([])
const loading = ref(true)
const confirmActivar = ref(null)

const cid = () => companyStore.selectedCompany?.id_company

const moraClass = d => {
  const n = Number(d)
  if (isNaN(n)) return 'mora-baja'
  return n > 30 ? 'mora-alta' : n > 10 ? 'mora-media' : 'mora-baja'
}

async function cargar() {
  loading.value = true
  try {
    const { data } = await api.get('/parqueadero/morosos', { params: { company_id: cid() } })
    morosos.value = data
  } catch { showToast('Error al cargar morosos', 'error') }
  finally { loading.value = false }
}

function marcarActivo(m) {
  confirmActivar.value = m
}

async function ejecutarMarcarActivo() {
  const m = confirmActivar.value
  if (!m) return
  confirmActivar.value = null
  try {
    await api.patch(`/parqueadero/mensualidades/${m.id}/estado`, null, {
      params: { company_id: cid(), estado: 'activo' }
    })
    showToast('Marcado como activo', 'success')
    cargar()
  } catch { showToast('Error al cambiar estado', 'error') }
}

onMounted(cargar)
</script>

<style scoped>
.pq-view { padding: 16px; }
.pq-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; gap: 12px; }
.pq-title { font-size: 20px; font-weight: 700; margin: 0; display: flex; align-items: center; gap: 8px; }
.btn-refresh { background: none; border: 1.5px solid var(--border, #e2e8f0); border-radius: 8px; padding: 8px 12px; cursor: pointer; font-size: 16px; }
.pq-loader, .pq-empty { text-align: center; padding: 60px 20px; opacity: .5; }
.pq-empty i { display: block; margin-bottom: 12px; }

.morosos-count { font-size: 13px; color: #64748b; margin-bottom: 12px; }

.pq-table-wrap { overflow-x: auto; }
.pq-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.pq-table th { background: var(--table-head, #f1f5f9); padding: 10px 12px; text-align: left; font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase; white-space: nowrap; }
.pq-table td { padding: 11px 12px; border-bottom: 1px solid var(--border, #e2e8f0); vertical-align: middle; }
.pq-table tr:hover td { background: #fff7f7; }
.td-placa { font-size: 16px; font-weight: 800; letter-spacing: 2px; }
.td-mono { font-family: monospace; }
.td-actions { display: flex; gap: 4px; }

.mora-badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 800; }
.mora-alta   { background: #fee2e2; color: #7f1d1d; }
.mora-media  { background: #fef3c7; color: #92400e; }
.mora-baja   { background: #fef9c3; color: #713f12; }

.tel-link { color: #2563eb; text-decoration: none; display: flex; align-items: center; gap: 4px; font-size: 13px; }
.tel-link:hover { text-decoration: underline; }

.btn-icon { background: none; border: none; cursor: pointer; padding: 6px; border-radius: 6px; font-size: 16px; color: #64748b; text-decoration: none; display: inline-flex; align-items: center; }
.btn-icon:hover { background: #f1f5f9; }
.btn-check { color: #22c55e; }
.btn-check:hover { background: #f0fdf4; }

@media (max-width: 576px) {
  .pq-view { padding: 10px; }
}

.pq-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 16px; }
.pq-modal { background: var(--modal-bg, #fff); border-radius: 14px; width: 100%; overflow: hidden; }
.pq-modal-head { display: flex; align-items: center; justify-content: space-between; padding: 14px 18px; border-bottom: 1px solid var(--border, #e2e8f0); }
.pq-modal-head h3 { margin: 0; font-size: 16px; }
.pq-modal-foot { display: flex; gap: 10px; justify-content: flex-end; padding: 14px 18px; border-top: 1px solid var(--border, #e2e8f0); }
.btn-pq-primary { background: #3b82f6; color: #fff; border: none; border-radius: 8px; padding: 8px 16px; font-size: 14px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; }
.btn-pq-ghost { background: transparent; border: 1.5px solid #94a3b8; color: inherit; border-radius: 8px; padding: 8px 14px; font-size: 13px; cursor: pointer; }
</style>
