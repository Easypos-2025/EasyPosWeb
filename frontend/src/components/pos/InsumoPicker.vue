<template>
  <!-- Selector de insumos por categoría o por nombre (supply_items = inventario_porciones) -->
  <div class="ip">
    <div class="ip-cats">
      <div class="ip-ttl">Categoría</div>
      <button :class="['ip-cat', { active: cat === null }]" @click="setCat(null)">Todas</button>
      <button v-for="c in categorias" :key="c.id" :class="['ip-cat', { active: cat === c.id }]" @click="setCat(c.id)">
        {{ c.name }}
      </button>
    </div>
    <div class="ip-list">
      <div class="ip-search">
        <i class="bi bi-search"></i>
        <input v-model="q" @input="debounced" placeholder="Buscar insumo por nombre..." maxlength="60" />
      </div>
      <div v-if="loading" class="ip-empty"><span class="spinner-border spinner-border-sm"></span></div>
      <div v-else-if="!rows.length" class="ip-empty">Sin insumos</div>
      <button
        v-for="r in rows" :key="r.id_item"
        :class="['ip-row', { taken: excluded.includes(r.id_item) }]"
        :disabled="excluded.includes(r.id_item)"
        @click="$emit('select', r)"
      >
        <span class="ip-name">{{ r.description }}</span>
        <span class="ip-meta">{{ r.category_name || '' }}</span>
        <i class="bi" :class="excluded.includes(r.id_item) ? 'bi-check2' : 'bi-plus-circle'"></i>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import api from '@/services/apis.js'

const props = defineProps({
  categorias:      { type: Array,  default: () => [] },  // [{ id, name }] pos_product_categories
  defaultCategory: { type: Number, default: null },
  excluded:        { type: Array,  default: () => [] },  // id_item ya agregados
})
defineEmits(['select'])

const cat = ref(props.defaultCategory)
const q = ref('')
const rows = ref([])
const loading = ref(false)
let timer = null
let seq = 0

async function buscar() {
  const my = ++seq
  loading.value = true
  try {
    const params = { limit: 200 }
    if (cat.value) params.categoria = cat.value
    if (q.value.trim()) params.q = q.value.trim()
    const { data } = await api.get('/api/pos-catalogo/platos/insumos/buscar', { params })
    if (my === seq) rows.value = data          // descarta respuestas viejas
  } catch { if (my === seq) rows.value = [] }
  finally { if (my === seq) loading.value = false }
}
function debounced() { clearTimeout(timer); timer = setTimeout(buscar, 250) }
function setCat(id) { cat.value = id; buscar() }

watch(() => props.defaultCategory, v => { cat.value = v; buscar() })
onMounted(buscar)
</script>

<style scoped>
.ip { display: grid; grid-template-columns: 180px 1fr; gap: 10px; min-height: 260px; }
.ip-cats { display: flex; flex-direction: column; gap: 4px; max-height: 320px; overflow-y: auto; background: #eef2ff; border-radius: 10px; padding: 8px; }
.ip-ttl  { font-size: 11px; font-weight: 700; color: #3730a3; text-transform: uppercase; margin-bottom: 2px; }
.ip-cat  { border: none; background: transparent; text-align: left; padding: 6px 8px; border-radius: 6px; font-size: 12px; font-weight: 600; color: #312e81; cursor: pointer; }
.ip-cat.active { background: #4338ca; color: #fff; }
.ip-list { display: flex; flex-direction: column; gap: 4px; max-height: 320px; overflow-y: auto; }
.ip-search { display: flex; align-items: center; gap: 6px; border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 6px 10px; position: sticky; top: 0; background: #fff; }
.ip-search input { border: none; outline: none; flex: 1; font-size: 13px; }
.ip-row  { display: flex; align-items: center; gap: 8px; border: 1.5px solid #e2e8f0; background: #fff; border-radius: 8px; padding: 8px 10px; cursor: pointer; text-align: left; }
.ip-row:hover:not(:disabled) { border-color: #4338ca; }
.ip-row.taken { opacity: .5; cursor: default; }
.ip-name { flex: 1; font-size: 13px; font-weight: 600; color: #1e293b; }
.ip-meta { font-size: 11px; color: #94a3b8; }
.ip-row i { color: #4338ca; }
.ip-empty { text-align: center; color: #94a3b8; font-size: 12px; padding: 16px; }
@media (max-width: 768px) {
  .ip { grid-template-columns: 1fr; }
  .ip-cats { flex-direction: row; overflow-x: auto; max-height: none; }
  .ip-ttl { display: none; }
  .ip-cat { white-space: nowrap; }
}
@media (max-width: 576px) {
  .ip-list { max-height: 260px; }
  .ip-meta { display: none; }
}
</style>
