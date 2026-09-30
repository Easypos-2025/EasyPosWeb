<template>
  <div class="md-view">
    <!-- Encabezado -->
    <div class="md-header">
      <button class="md-back" @click="salir" :disabled="saving" title="Salir (guarda los cambios)">
        <i class="bi bi-arrow-left"></i>
      </button>
      <div class="md-header__info">
        <h5 class="md-title">{{ moduleName || 'Menú del Día' }}</h5>
        <span class="md-date">
          <i class="bi bi-calendar3 me-1"></i>{{ fmtFecha(hoy.date) }}
          <span v-if="hoy.menu_id" class="md-menu-id">Menú No. {{ hoy.menu_id }}</span>
        </span>
      </div>
      <div class="md-header__actions">
        <span v-if="tab === 'hoy'" class="md-count"><i class="bi bi-check2-circle me-1 text-success"></i>{{ totalSel }} marcados</span>
        <span v-if="saving" class="md-saving"><span class="spinner-border spinner-border-sm me-1"></span>Guardando…</span>
      </div>
    </div>

    <!-- Pestañas -->
    <div class="md-tabs">
      <button :class="['md-tab', { active: tab === 'hoy' }]" @click="tab = 'hoy'"><i class="bi bi-journal-check me-1"></i>Menú de hoy</button>
      <button :class="['md-tab', { active: tab === 'consulta' }]" @click="abrirConsulta"><i class="bi bi-search me-1"></i>Consulta</button>
    </div>

    <!-- ══ MENÚ DE HOY ══ -->
    <section v-if="tab === 'hoy'" class="md-body">
      <div class="md-toolbar">
        <button class="md-btn md-btn--sec" @click="expandirTodo(!todoAbierto)">
          <i :class="todoAbierto ? 'bi bi-arrows-collapse' : 'bi bi-arrows-expand'"></i> {{ todoAbierto ? 'Contraer' : 'Expandir' }} todo
        </button>
        <button class="md-btn md-btn--print" :disabled="loading || saving" @click="imprimirHoy">
          <i class="bi bi-printer"></i> Imprimir
        </button>
      </div>

      <div v-if="loading" class="md-state"><div class="spinner-border text-primary"></div></div>
      <div v-else-if="!categorias.length" class="md-state">
        <i class="bi bi-journal-x fs-1 text-muted"></i>
        <p class="text-muted mt-2">No hay categorías de armado activas. Márquelas en Categorías de Productos.</p>
      </div>
      <div v-else class="md-acc">
        <div v-for="c in categorias" :key="c.group_id" :class="['md-acc-item', { open: abiertas.has(c.group_id) }]">
          <button class="md-acc-hdr" @click="toggleCat(c.group_id)" :aria-expanded="abiertas.has(c.group_id)">
            <i class="bi bi-chevron-right md-acc-chev"></i>
            <span class="md-acc-name">{{ c.group_name }}</span>
            <span v-if="!c.items.length" class="md-acc-empty">Sin insumos de armado</span>
            <span v-else :class="['md-acc-count', { on: nSel(c) }]">{{ nSel(c) }} / {{ c.items.length }}</span>
          </button>
          <div v-if="abiertas.has(c.group_id)" class="md-acc-body">
            <p v-if="!c.items.length" class="md-acc-note">Esta categoría no tiene insumos marcados como "Armar Plato".</p>
            <label v-for="it in c.items" :key="it.item_id" :class="['md-check', { on: it.is_selected }]">
              <input type="checkbox" v-model="it.is_selected" />
              <span>{{ it.item_name }}</span>
            </label>
          </div>
        </div>
      </div>
    </section>

    <!-- ══ CONSULTA ══ -->
    <section v-else class="md-body">
      <div class="md-toolbar">
        <div class="md-date-pick">
          <span class="md-lbl">Fecha</span>
          <CustomDatePicker v-model="consulta.date" @update:modelValue="cargarConsulta" style="width:150px" />
        </div>
        <button class="md-btn md-btn--print" :disabled="consulta.loading || !consulta.data?.categories.length" @click="imprimir(consulta.data)">
          <i class="bi bi-printer"></i> Imprimir
        </button>
      </div>
      <div v-if="consulta.loading" class="md-state"><div class="spinner-border text-primary"></div></div>
      <div v-else-if="!consulta.data?.categories.length" class="md-state">
        <i class="bi bi-calendar-x fs-1 text-muted"></i>
        <p class="text-muted mt-2">No hay menú armado para el {{ fmtFecha(consulta.date) }}.</p>
      </div>
      <div v-else class="md-consulta">
        <div class="md-consulta-hdr">Menú No. {{ consulta.data.menu_id }} · {{ fmtFecha(consulta.data.date) }}</div>
        <div v-for="c in consulta.data.categories" :key="c.name" class="md-consulta-cat">
          <div class="md-consulta-name">{{ c.name }}</div>
          <ul><li v-for="i in c.items" :key="i">{{ i }}</li></ul>
        </div>
      </div>
    </section>

    <!-- Impresión: componente propio (vista previa · impresora predeterminada · PDF · Excel) -->
    <ImprimirRecibo
      v-if="impresion"
      :receiptData="impresion.data"
      :companyId="companyId"
      printersPath="/api/pos/recibo-impresion/impresoras"
      printPath="/api/pos/comanda/menu-diario-admin/imprimir"
      :printExtra="{ date: impresion.date }"
      @close="impresion = null"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, onBeforeRouteLeave } from 'vue-router'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'
import { useModuleName } from '@/composables/useModuleName'
import { useCompanyStore } from '@/stores/companyStore'
import CustomDatePicker from '@/components/common/CustomDatePicker.vue'
import ImprimirRecibo from '@/components/billing/ImprimirRecibo.vue'

const BASE = '/api/pos/comanda/menu-diario-admin'
const router = useRouter()
const { moduleName } = useModuleName()
const companyStore = useCompanyStore()
const companyId = computed(() => companyStore.selectedCompany?.id || 0)

const tab = ref('hoy')
const loading = ref(true)
const saving = ref(false)
const hoy = reactive({ date: '', menu_id: null })
const categorias = ref([])
const abiertas = ref(new Set())          // acordeón: todas cerradas al entrar
let inicial = ''                          // insumos marcados al entrar (para saber si hubo cambios)

const marcados = () => categorias.value.flatMap(c => c.items.filter(i => i.is_selected).map(i => i.item_id)).sort((a, b) => a - b)
const huella = () => marcados().join(',')
const totalSel = computed(() => categorias.value.reduce((s, c) => s + nSel(c), 0))
const nSel = c => c.items.filter(i => i.is_selected).length
const todoAbierto = computed(() => categorias.value.length > 0 && abiertas.value.size === categorias.value.length)

function toggleCat(id) {
  const s = new Set(abiertas.value)
  s.has(id) ? s.delete(id) : s.add(id)
  abiertas.value = s
}
function expandirTodo(v) { abiertas.value = new Set(v ? categorias.value.map(c => c.group_id) : []) }

function fmtFecha(d) {
  if (!d) return ''
  const [y, m, day] = d.split('-')
  return `${day}/${m}/${y}`
}

async function cargar() {
  loading.value = true
  try {
    const { data } = await api.get(BASE)
    Object.assign(hoy, { date: data.date, menu_id: data.menu_id })
    categorias.value = data.categories
    inicial = huella()
  } catch (e) {
    showToast(e?.response?.data?.detail || 'Error al cargar el menú del día', 'error', 3500)
  } finally { loading.value = false }
}

// Guarda solo si cambió lo marcado (se agregaron o quitaron insumos). Sin marcados → se borra el menú del día.
async function guardarSiCambio() {
  if (loading.value || huella() === inicial) return true
  saving.value = true
  try {
    const { data } = await api.post(`${BASE}/guardar`, { date: hoy.date, selected_ids: marcados() })
    hoy.menu_id = data.menu_id
    inicial = huella()
    showToast(data.selected_count ? `Menú del día guardado (${data.selected_count} insumos)` : 'Menú del día eliminado', 'success')
    return true
  } catch (e) {
    showToast(e?.response?.data?.detail || 'Error al guardar el menú', 'error', 3500)
    return false
  } finally { saving.value = false }
}

async function salir() {
  if (await guardarSiCambio()) router.back()
}
onBeforeRouteLeave(async () => { await guardarSiCambio() })

// ── Impresión ────────────────────────────────────────────────────────────────
const impresion = ref(null)
function imprimir(menu) {
  if (!menu?.categories?.length) { showToast('No hay insumos marcados para imprimir', 'warning'); return }
  impresion.value = {
    date: menu.date,
    data: {
      titulo: 'MENÚ DEL DÍA',
      receipt_number: '',
      ordenNumero: menu.menu_id ? `Menú No. ${menu.menu_id}` : '',
      fecha: fmtFecha(menu.date),
      secciones: menu.categories.map(c => ({ titulo: c.name, items: c.items })),
      items: [], pagos: [],
    },
  }
}
async function imprimirHoy() {
  if (!(await guardarSiCambio())) return        // se imprime lo guardado
  try { imprimir((await api.get(`${BASE}/consulta`, { params: { date: hoy.date } })).data) }
  catch (e) { showToast(e?.response?.data?.detail || 'No se pudo cargar el menú', 'error') }
}

// ── Consulta de otras fechas ─────────────────────────────────────────────────
const consulta = reactive({ date: '', data: null, loading: false })
async function abrirConsulta() {
  await guardarSiCambio()
  tab.value = 'consulta'
  if (!consulta.date) { consulta.date = hoy.date; cargarConsulta() }
}
async function cargarConsulta() {
  if (!consulta.date) return
  consulta.loading = true
  try { consulta.data = (await api.get(`${BASE}/consulta`, { params: { date: consulta.date } })).data }
  catch (e) { consulta.data = null; showToast(e?.response?.data?.detail || 'Error al consultar', 'error') }
  finally { consulta.loading = false }
}

onMounted(cargar)
</script>

<style scoped>
.md-view { display: flex; flex-direction: column; min-height: 100%; background: #f1f5f9; }
.md-header { display: flex; align-items: center; gap: 12px; padding: 12px 18px; background: #fff; border-bottom: 1px solid #e2e8f0; position: sticky; top: 0; z-index: 5; }
.md-back { width: 38px; height: 38px; border-radius: 50%; border: 1px solid #e2e8f0; background: #fff; cursor: pointer; flex-shrink: 0; }
.md-header__info { flex: 1; min-width: 0; }
.md-title { margin: 0; font-weight: 800; color: #1e293b; font-size: 18px; }
.md-date { font-size: 13px; color: #64748b; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.md-menu-id { font-weight: 700; color: #4338ca; background: #e0e7ff; border-radius: 10px; padding: 1px 8px; font-size: 12px; }
.md-header__actions { display: flex; align-items: center; gap: 10px; font-size: 13px; font-weight: 600; color: #334155; }
.md-saving { color: #1d4ed8; }
.md-tabs { display: flex; gap: 4px; padding: 10px 18px 0; }
.md-tab { border: none; background: #e2e8f0; color: #475569; padding: 8px 16px; border-radius: 10px 10px 0 0; font-weight: 700; font-size: 13px; cursor: pointer; }
.md-tab.active { background: #fff; color: #1d4ed8; }
.md-body { background: #fff; margin: 0 18px 18px; border-radius: 0 12px 12px 12px; padding: 14px; flex: 1; }
.md-toolbar { display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 12px; }
.md-btn { display: inline-flex; align-items: center; gap: 6px; border: none; border-radius: 10px; padding: 9px 16px; font-weight: 700; font-size: 13px; cursor: pointer; }
.md-btn:disabled { opacity: .5; cursor: not-allowed; }
.md-btn--sec { background: #f1f5f9; color: #475569; }
.md-btn--print { background: linear-gradient(90deg,#1e3a5f,#1d4ed8); color: #fff; }
.md-state { display: flex; flex-direction: column; align-items: center; padding: 50px 16px; text-align: center; }

/* Acordeón */
.md-acc { display: flex; flex-direction: column; gap: 8px; }
.md-acc-item { border: 1.5px solid #e2e8f0; border-radius: 12px; overflow: hidden; }
.md-acc-item.open { border-color: #bfdbfe; }
.md-acc-hdr { width: 100%; display: flex; align-items: center; gap: 10px; padding: 12px 14px; background: #f8fafc; border: none; cursor: pointer; text-align: left; }
.md-acc-item.open .md-acc-hdr { background: #eff6ff; }
.md-acc-chev { transition: transform .15s; color: #64748b; }
.md-acc-item.open .md-acc-chev { transform: rotate(90deg); }
.md-acc-name { flex: 1; min-width: 0; font-weight: 800; color: #1e3a5f; font-size: 14px; }
.md-acc-count { font-size: 12px; font-weight: 700; color: #94a3b8; background: #fff; border-radius: 10px; padding: 2px 9px; border: 1px solid #e2e8f0; }
.md-acc-count.on { color: #15803d; border-color: #bbf7d0; background: #f0fdf4; }
.md-acc-empty { font-size: 11px; font-weight: 700; color: #b45309; background: #fef3c7; border-radius: 10px; padding: 2px 9px; }
.md-acc-body { padding: 10px 14px 14px; display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 6px; }
.md-acc-note { grid-column: 1 / -1; margin: 0; font-size: 13px; color: #94a3b8; }
.md-check { display: flex; align-items: center; gap: 10px; padding: 9px 12px; border: 1.5px solid #e2e8f0; border-radius: 10px; cursor: pointer; font-size: 14px; color: #334155; user-select: none; }
.md-check input { width: 18px; height: 18px; accent-color: #16a34a; flex-shrink: 0; }
.md-check.on { border-color: #86efac; background: #f0fdf4; color: #14532d; font-weight: 600; }

/* Consulta */
.md-date-pick { display: flex; align-items: center; gap: 8px; }
.md-lbl { font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase; }
.md-consulta-hdr { font-weight: 800; color: #4338ca; margin-bottom: 10px; }
.md-consulta { display: flex; flex-direction: column; gap: 10px; }
.md-consulta-cat { border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 14px; }
.md-consulta-name { font-weight: 800; color: #1e3a5f; margin-bottom: 4px; }
.md-consulta-cat ul { margin: 0; padding-left: 18px; color: #334155; font-size: 14px; }

@media (max-width: 1024px) {
  .md-acc-body { grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); }
}
@media (max-width: 768px) {
  .md-header { padding: 10px 12px; }
  .md-tabs { padding: 8px 10px 0; }
  .md-body { margin: 0 10px 12px; padding: 12px; }
  .md-acc-body { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 576px) {
  .md-title { font-size: 16px; }
  .md-header__actions .md-count { display: none; }
  .md-tab { flex: 1; padding: 8px 6px; }
  .md-toolbar .md-btn { flex: 1; justify-content: center; }
  .md-acc-body { grid-template-columns: 1fr; padding: 8px 10px 12px; }
  .md-acc-hdr { padding: 11px 12px; }
}
</style>
