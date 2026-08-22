<template>
  <div class="pq-view">
    <div class="pq-header">
      <h2 class="pq-title"><i class="bi bi-sliders2-vertical"></i> {{ moduleName }}</h2>
    </div>

    <div class="config-grid">
      <!-- ── Capacidad del parqueadero ── -->
      <div class="pq-card">
        <h3 class="card-title"><i class="bi bi-p-square-fill"></i> Capacidad Total del Parqueadero</h3>
        <p class="card-desc">
          Define cuántos vehículos caben en el parqueadero por tipo. Estos valores se usan en el
          dashboard para mostrar plazas disponibles en tiempo real.
        </p>

        <div v-if="loading" class="pq-loader-sm">Cargando configuración...</div>

        <form v-else @submit.prevent="guardar" class="config-form">
          <div class="config-row">
            <div class="config-field">
              <label><i class="bi bi-car-front-fill" style="color:#3b82f6"></i> Plazas para Autos</label>
              <div class="input-wrap">
                <input type="number" v-model.number="form.plazas_autos" class="pq-input" min="0" placeholder="0 = sin límite" />
                <span class="input-hint">vehículos</span>
              </div>
            </div>
            <div class="config-field">
              <label><i class="bi bi-bicycle" style="color:#f59e0b"></i> Plazas para Motos</label>
              <div class="input-wrap">
                <input type="number" v-model.number="form.plazas_motos" class="pq-input" min="0" placeholder="0 = sin límite" />
                <span class="input-hint">vehículos</span>
              </div>
            </div>
            <div class="config-field">
              <label><i class="bi bi-truck-front-fill" style="color:#8b5cf6"></i> Plazas Otros</label>
              <div class="input-wrap">
                <input type="number" v-model.number="form.plazas_otros" class="pq-input" min="0" placeholder="0 = sin límite" />
                <span class="input-hint">vehículos</span>
              </div>
            </div>
          </div>

          <div class="capacidad-total">
            <span class="ct-label">Capacidad Total</span>
            <span class="ct-valor">{{ totalPlazas }}</span>
            <span class="ct-unidad">plazas</span>
          </div>

          <div class="config-actions">
            <button type="submit" class="btn-pq-primary" :disabled="saving">
              <i class="bi" :class="saving ? 'bi-hourglass-split' : 'bi-floppy-fill'"></i>
              {{ saving ? 'Guardando...' : 'Guardar Configuración' }}
            </button>
          </div>
        </form>
      </div>

      <!-- ── Info categorías ── -->
      <div class="pq-card info-card">
        <h3 class="card-title"><i class="bi bi-info-circle-fill" style="color:#3b82f6"></i> Cómo funciona</h3>
        <ul class="info-list">
          <li>
            <i class="bi bi-check-circle-fill"></i>
            Las <strong>plazas</strong> definen el total de cupos físicos del parqueadero.
          </li>
          <li>
            <i class="bi bi-check-circle-fill"></i>
            El dashboard calcula automáticamente las <strong>plazas disponibles</strong>
            restando los vehículos activos.
          </li>
          <li>
            <i class="bi bi-check-circle-fill"></i>
            Un valor de <strong>0</strong> significa sin límite definido (parqueadero ilimitado).
          </li>
          <li>
            <i class="bi bi-check-circle-fill"></i>
            Las categorías de vehículos se gestionan en el módulo
            <strong>Categorías Parqueadero</strong>.
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useCompanyStore } from '@/stores/companyStore'
import { useModuleName } from '@/composables/useModuleName'
import { showToast } from '@/utils/toast'
import api from '@/services/apis'

const companyStore = useCompanyStore()
const { moduleName } = useModuleName()

const loading = ref(false)
const saving  = ref(false)
const form    = ref({ plazas_autos: 0, plazas_motos: 0, plazas_otros: 0 })

const cid = () => companyStore.selectedCompany?.id

const totalPlazas = computed(() =>
  (form.value.plazas_autos || 0) + (form.value.plazas_motos || 0) + (form.value.plazas_otros || 0)
)

async function cargar() {
  loading.value = true
  try {
    const { data } = await api.get('/api/parqueadero/config', { params: { company_id: cid() } })
    form.value = { plazas_autos: data.plazas_autos || 0, plazas_motos: data.plazas_motos || 0, plazas_otros: data.plazas_otros || 0 }
  } catch { /* silencioso */ }
  finally { loading.value = false }
}

async function guardar() {
  saving.value = true
  try {
    await api.post('/api/parqueadero/config', form.value, { params: { company_id: cid() } })
    showToast('Configuración guardada', 'success')
  } catch { showToast('Error al guardar configuración', 'error') }
  finally { saving.value = false }
}

watch(() => companyStore.selectedCompany?.id, id => { if (id) cargar() }, { immediate: true })
</script>

<style scoped>
.pq-view    { padding: 16px; }
.pq-header  { margin-bottom: 20px; }
.pq-title   { font-size: 20px; font-weight: 700; margin: 0; display: flex; align-items: center; gap: 8px; }

.config-grid {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 16px;
  align-items: start;
}

.pq-card { background: var(--card-bg, #fff); border-radius: 12px; padding: 24px; box-shadow: 0 1px 8px rgba(0,0,0,.07); }
.card-title { font-size: 15px; font-weight: 700; margin: 0 0 8px; display: flex; align-items: center; gap: 8px; }
.card-desc  { font-size: 13px; color: #64748b; margin: 0 0 24px; line-height: 1.5; }

.config-form { display: flex; flex-direction: column; gap: 20px; }

.config-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }

.config-field { display: flex; flex-direction: column; gap: 8px; }
.config-field label { font-size: 13px; font-weight: 600; color: #374151; display: flex; align-items: center; gap: 6px; }

.input-wrap  { position: relative; }
.pq-input    { width: 100%; padding: 10px 70px 10px 14px; border: 1.5px solid var(--border, #e2e8f0); border-radius: 8px; font-size: 18px; font-weight: 700; background: var(--input-bg, #f8fafc); box-sizing: border-box; }
.pq-input:focus { outline: none; border-color: #3b82f6; }
.input-hint  { position: absolute; right: 12px; top: 50%; transform: translateY(-50%); font-size: 11px; color: #94a3b8; white-space: nowrap; }

.capacidad-total {
  display: flex;
  align-items: baseline;
  gap: 8px;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border: 1.5px solid #93c5fd;
  border-radius: 10px;
  padding: 16px 20px;
}
.ct-label  { font-size: 13px; font-weight: 600; color: #1e40af; }
.ct-valor  { font-size: 36px; font-weight: 900; color: #1d4ed8; line-height: 1; }
.ct-unidad { font-size: 14px; color: #3b82f6; font-weight: 600; }

.config-actions { display: flex; justify-content: flex-end; }
.btn-pq-primary { background: #3b82f6; color: #fff; border: none; border-radius: 8px; padding: 10px 24px; font-size: 14px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; }
.btn-pq-primary:hover { background: #2563eb; }
.btn-pq-primary:disabled { opacity: .6; cursor: not-allowed; }

.info-card { background: var(--card-bg, #fff); }
.info-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 12px; }
.info-list li { display: flex; align-items: flex-start; gap: 10px; font-size: 13px; color: #475569; line-height: 1.4; }
.info-list li .bi { color: #22c55e; font-size: 14px; flex-shrink: 0; margin-top: 1px; }

.pq-loader-sm { text-align: center; padding: 30px 20px; opacity: .5; font-size: 14px; }

@media (max-width: 768px) {
  .config-grid { grid-template-columns: 1fr; }
  .config-row  { grid-template-columns: 1fr; }
}
@media (max-width: 576px) {
  .pq-view { padding: 10px; }
  .config-row { grid-template-columns: 1fr; }
}
</style>
