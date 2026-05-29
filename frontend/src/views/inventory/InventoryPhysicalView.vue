<template>
  <div class="inv-physical-view">
    <div class="iv-header">
      <h5 class="iv-title">Inventarios Físicos</h5>
      <button class="btn-primary-sm" @click="openCreate">+ Nuevo Conteo</button>
    </div>

    <div class="iv-table-wrap">
      <table class="iv-table">
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Insumo</th>
            <th>Cantidad</th>
            <th>Unidad</th>
            <th>Usuario</th>
            <th>Observación</th>
            <th class="text-center">Estado</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading"><td colspan="7" class="text-center py-3">Cargando…</td></tr>
          <tr v-else-if="!rows.length"><td colspan="7" class="text-center py-3 text-muted">Sin registros</td></tr>
          <tr v-for="r in rows" :key="r.id">
            <td>{{ r.fecha }}</td>
            <td>
              <strong>{{ r.item_name }}</strong>
              <small class="text-muted d-block">{{ r.unit_name }}</small>
            </td>
            <td class="text-end fw-bold">{{ fmt(r.cantidad) }}</td>
            <td>{{ r.unit_name }}</td>
            <td>{{ r.cod_usuario }}</td>
            <td class="text-muted small">{{ r.observacion }}</td>
            <td class="text-center">
              <span v-if="r.autorizada" class="badge-ok">Autorizado</span>
              <button v-else class="badge-pending" @click="authorize(r)">Pendiente</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal nuevo conteo -->
    <div v-if="showModal" class="iv-modal-bg" @click.self="showModal=false">
      <div class="iv-modal">
        <h6 class="modal-title">Nuevo Inventario Físico</h6>
        <div class="form-group">
          <label>Insumo</label>
          <select v-model="form.id_item" class="form-control">
            <option value="">— Seleccionar —</option>
            <option v-for="s in supplyItems" :key="s.id_item" :value="s.id_item">
              {{ s.description }} ({{ s.unit_name }}) — Stock: {{ fmt(s.stock_qty) }}
            </option>
          </select>
        </div>
        <div class="form-row-2">
          <div class="form-group">
            <label>Fecha</label>
            <input type="date" v-model="form.fecha" class="form-control" />
          </div>
          <div class="form-group">
            <label>Cantidad contada</label>
            <input type="number" v-model.number="form.cantidad" min="0" step="0.0001" class="form-control" />
          </div>
        </div>
        <div class="form-group">
          <label>Observación</label>
          <input type="text" v-model="form.observacion" class="form-control" placeholder="Opcional" />
        </div>
        <div class="form-group">
          <label class="d-flex align-items-center gap-2">
            <input type="checkbox" v-model="form.autorizada" :true-value="1" :false-value="0" />
            Autorizar y aplicar al stock inmediatamente
          </label>
        </div>
        <div class="modal-actions">
          <button class="btn-outline" @click="showModal=false">Cancelar</button>
          <button class="btn-primary-sm" :disabled="saving" @click="save">
            {{ saving ? 'Guardando…' : 'Guardar' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/apis'

const rows = ref([])
const supplyItems = ref([])
const loading = ref(true)
const showModal = ref(false)
const saving = ref(false)

const today = () => new Date().toISOString().slice(0, 10)
const form = ref({ id_item: '', fecha: today(), cantidad: 0, observacion: '', autorizada: 1 })
const fmt = (v) => Number(v || 0).toLocaleString('es-CO', { maximumFractionDigits: 4 })

async function load() {
  loading.value = true
  try { rows.value = (await api.get('/api/inventory/physical')).data }
  finally { loading.value = false }
}

async function loadItems() {
  supplyItems.value = (await api.get('/api/inventory/stock')).data
}

function openCreate() {
  form.value = { id_item: '', fecha: today(), cantidad: 0, observacion: '', autorizada: 1 }
  showModal.value = true
}

async function save() {
  if (!form.value.id_item || form.value.cantidad < 0) return
  saving.value = true
  try {
    await api.post('/api/inventory/physical', form.value)
    showModal.value = false
    await load(); await loadItems()
  } catch (e) { console.error(e) }
  finally { saving.value = false }
}

async function authorize(row) {
  if (!confirm(`¿Autorizar conteo de ${row.item_name}: ${fmt(row.cantidad)} ${row.unit_name}?\nEsto actualizará el stock.`)) return
  await api.patch(`/api/inventory/physical/${row.id}/authorize`)
  await load()
}

onMounted(() => { load(); loadItems() })
</script>

<style scoped>
.inv-physical-view { padding: 16px; }
.iv-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 8px; }
.iv-title { margin: 0; font-size: 1.1rem; font-weight: 600; }
.iv-table-wrap { overflow-x: auto; }
.iv-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.iv-table th { background: #f8f9fa; padding: 8px 10px; text-align: left; font-weight: 600; border-bottom: 2px solid #dee2e6; white-space: nowrap; }
.iv-table td { padding: 7px 10px; border-bottom: 1px solid #f0f0f0; vertical-align: middle; }
.iv-table tr:hover td { background: #fafafa; }
.badge-ok { background: #d1fae5; color: #065f46; padding: 2px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; }
.badge-pending { background: #fef3c7; color: #92400e; padding: 2px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; border: none; cursor: pointer; }
.badge-pending:hover { background: #fde68a; }
.btn-primary-sm { background: #2563eb; color: #fff; border: none; padding: 7px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.85rem; }
.btn-primary-sm:disabled { opacity: .6; cursor: not-allowed; }
.btn-outline { background: transparent; border: 1px solid #dee2e6; padding: 7px 16px; border-radius: 6px; cursor: pointer; }
.iv-modal-bg { position: fixed; inset: 0; background: rgba(0,0,0,.45); z-index: 1050; display: flex; align-items: center; justify-content: center; padding: 16px; }
.iv-modal { background: #fff; border-radius: 12px; padding: 24px; width: 100%; max-width: 480px; box-shadow: 0 20px 60px rgba(0,0,0,.2); }
.modal-title { margin: 0 0 16px; font-weight: 700; }
.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: 0.82rem; font-weight: 600; margin-bottom: 4px; color: #374151; }
.form-control { width: 100%; padding: 8px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 0.88rem; box-sizing: border-box; }
.form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
.text-center { text-align: center; }
.text-end { text-align: right; }
.text-muted { color: #6b7280; }
.fw-bold { font-weight: 700; }
.small { font-size: 0.78rem; }
.d-block { display: block; }
.d-flex { display: flex; }
.align-items-center { align-items: center; }
.gap-2 { gap: 8px; }
.py-3 { padding-top: 12px; padding-bottom: 12px; }

@media (max-width: 768px) {
  .iv-table { font-size: 0.8rem; }
  .iv-table th, .iv-table td { padding: 6px 8px; }
  .form-row-2 { grid-template-columns: 1fr; }
}
@media (max-width: 576px) {
  .iv-header { flex-direction: column; align-items: flex-start; }
  .iv-modal { padding: 16px; }
}
</style>
