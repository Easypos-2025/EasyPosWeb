<template>
  <div class="pkconf-page">

    <div class="pkconf-header">
      <i class="bi bi-gear-fill"></i>
      <div>
        <h5>Configuración Parking Service</h5>
        <p>Define la capacidad y el modo de operación. Los servicios a cobrar se gestionan en <strong>Productos Parking</strong>.</p>
      </div>
    </div>

    <div v-if="loading" class="pkconf-loading">
      <i class="bi bi-arrow-repeat spin"></i> Cargando configuración…
    </div>

    <div v-else class="pkconf-card">

      <!-- ── Plazas totales ── -->
      <div class="pkconf-section">
        <h6 class="pkconf-section-title"><i class="bi bi-grid-3x3-gap-fill"></i> Capacidad</h6>
        <div class="pkconf-field">
          <label>Total de plazas / puestos disponibles</label>
          <input v-model.number="form.total_plazas" type="number" min="1" class="pkconf-input"
            placeholder="Ej: 50" />
          <small>Número máximo de vehículos que pueden estar en el establecimiento al mismo tiempo.</small>
        </div>
      </div>

      <!-- ── Modo de cobro ── -->
      <div class="pkconf-section">
        <h6 class="pkconf-section-title"><i class="bi bi-cash-coin"></i> Modo de Cobro</h6>
        <div class="pkconf-modos">
          <label v-for="m in MODOS" :key="m.val"
            :class="['pkconf-modo-card', { active: form.modo_cobro === m.val }]">
            <input type="radio" v-model="form.modo_cobro" :value="m.val" style="display:none" />
            <i :class="m.icon"></i>
            <span class="pkconf-modo-nombre">{{ m.nombre }}</span>
            <span class="pkconf-modo-desc">{{ m.desc }}</span>
          </label>
        </div>
      </div>

      <!-- ── Acciones ── -->
      <div class="pkconf-actions">
        <button class="pkconf-btn-guardar" :disabled="guardando" @click="guardar">
          <i v-if="guardando" class="bi bi-arrow-repeat spin"></i>
          <i v-else class="bi bi-check-lg"></i>
          {{ guardando ? 'Guardando…' : 'Guardar Configuración' }}
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'
import { useCompanyStore } from '@/stores/companyStore'

const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id)

const MODOS = [
  { val: 'tarifa_unica', nombre: 'Tarifa Única',        icon: 'bi bi-person-check-fill', desc: 'Un precio fijo por persona, sin importar el tiempo' },
  { val: 'por_hora',     nombre: 'Por Hora',            icon: 'bi bi-hourglass-split',   desc: 'Se cobra por hora o fracción de hora transcurrida' },
  { val: 'por_minuto',   nombre: 'Por Minuto',          icon: 'bi bi-clock-fill',        desc: 'Se cobra por cada minuto que el vehículo permanece' },
  { val: 'mensualidad',  nombre: 'Mensualidad',         icon: 'bi bi-calendar2-check',   desc: 'Cobro mensual fijo, solo se registra entrada/salida' },
]

const loading   = ref(false)
const guardando = ref(false)
const form = ref({
  total_plazas: 20,
  modo_cobro:   'tarifa_unica',
})

async function cargar() {
  if (!companyId.value) return
  loading.value = true
  try {
    const res = await api.get('/api/parking/config', { params: { company_id: companyId.value } })
    form.value = { ...form.value, ...res.data }
  } catch { showToast('Error al cargar configuración', 'error', 3000) }
  loading.value = false
}

async function guardar() {
  if (!form.value.total_plazas || form.value.total_plazas < 1) {
    showToast('El número de plazas debe ser mayor a 0', 'warning', 2500)
    return
  }
  guardando.value = true
  try {
    await api.put('/api/parking/config', form.value, {
      params: { company_id: companyId.value },
    })
    showToast('Configuración guardada', 'success', 2500)
  } catch (e) { showToast(e?.response?.data?.detail || 'Error al guardar', 'error', 3000) }
  guardando.value = false
}

onMounted(cargar)
</script>

<style scoped>
.pkconf-page { padding: 16px; max-width: 700px; margin: 0 auto; }

.pkconf-header {
  display: flex; align-items: center; gap: 14px; margin-bottom: 20px;
  background: #fff; border-radius: 12px; padding: 16px 20px; border: 1px solid #e9ecef;
}
.pkconf-header i { font-size: 2rem; color: #6c757d; }
.pkconf-header h5 { margin: 0; font-weight: 700; font-size: 1rem; }
.pkconf-header p  { margin: 0; font-size: .82rem; color: #6c757d; }

.pkconf-loading { text-align: center; padding: 40px; color: #6c757d; }

.pkconf-card { background: #fff; border-radius: 14px; border: 1px solid #e9ecef; overflow: hidden; }

.pkconf-section { padding: 20px; border-bottom: 1px solid #f1f3f5; }
.pkconf-section:last-child { border-bottom: none; }
.pkconf-section-title {
  font-size: .85rem; font-weight: 700; text-transform: uppercase; letter-spacing: .5px;
  color: #6c757d; margin-bottom: 14px; display: flex; align-items: center; gap: 8px;
}

.pkconf-field { display: flex; flex-direction: column; gap: 6px; }
.pkconf-field label { font-size: .88rem; font-weight: 600; color: #495057; display: flex; align-items: center; gap: 6px; }
.pkconf-field small { font-size: .78rem; color: #adb5bd; }
.pkconf-input {
  border: 1px solid #ced4da; border-radius: 8px; padding: 10px 12px;
  font-size: .95rem; outline: none; width: 100%; transition: border-color .15s;
}
.pkconf-input:focus { border-color: #0d6efd; }
.pkconf-input-money {
  display: flex; align-items: center; border: 1px solid #ced4da; border-radius: 8px; overflow: hidden;
}
.pkconf-input-money span { background: #f8f9fa; padding: 10px 12px; font-size: .9rem; color: #6c757d; border-right: 1px solid #ced4da; }
.pkconf-input-money input { border: none; flex: 1; padding: 10px 12px; font-size: .95rem; outline: none; }

.pkconf-modos { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
.pkconf-modo-card {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  padding: 16px 12px; border: 2px solid #e9ecef; border-radius: 10px;
  cursor: pointer; text-align: center; transition: all .15s;
}
.pkconf-modo-card:hover { border-color: #0d6efd; background: #f8f9ff; }
.pkconf-modo-card.active { border-color: #0d6efd; background: #e7f1ff; }
.pkconf-modo-card i { font-size: 1.5rem; color: #6c757d; }
.pkconf-modo-card.active i { color: #0d6efd; }
.pkconf-modo-nombre { font-size: .88rem; font-weight: 700; color: #212529; }
.pkconf-modo-desc   { font-size: .75rem; color: #6c757d; line-height: 1.3; }

.pkconf-tarifas-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }

.pkconf-info-mensual {
  display: flex; gap: 10px; align-items: flex-start;
  background: #e8f4fd; border-radius: 8px; padding: 12px; font-size: .85rem; color: #055160;
}
.pkconf-info-mensual i { font-size: 1.1rem; flex-shrink: 0; margin-top: 1px; }

.pkconf-preview {
  display: flex; align-items: center; gap: 10px;
  background: #f8f9fa; border-radius: 8px; padding: 12px 16px; margin: 0 20px 16px;
  font-size: .88rem; color: #495057;
}
.pkconf-preview i { color: #0d6efd; }

.pkconf-actions { padding: 20px; display: flex; justify-content: flex-end; }
.pkconf-btn-guardar {
  padding: 11px 28px; border: none; border-radius: 10px; background: #0d6efd; color: #fff;
  font-size: .95rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px;
  transition: background .15s;
}
.pkconf-btn-guardar:hover:not(:disabled) { background: #0b5ed7; }
.pkconf-btn-guardar:disabled { opacity: .6; cursor: default; }

.spin { animation: pkconf-spin .8s linear infinite; }
@keyframes pkconf-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

@media (max-width: 576px) {
  .pkconf-page { padding: 10px; }
  .pkconf-modos { grid-template-columns: 1fr 1fr; }
  .pkconf-tarifas-grid { grid-template-columns: 1fr; }
  .pkconf-section { padding: 14px; }
}
</style>
