<template>
  <div class="md-view">

    <!-- Header sticky -->
    <div class="md-header">
      <button class="md-header__back" @click="handleSalir" :disabled="saving">
        <i class="bi bi-arrow-left"></i>
      </button>
      <div class="md-header__info">
        <h5 class="md-header__title">Menú del Día</h5>
        <span class="md-header__date">
          <i class="bi bi-calendar3 me-1"></i>{{ displayDate }}
        </span>
      </div>
      <div class="md-header__actions">
        <span class="md-header__count">
          <i class="bi bi-check2-circle me-1 text-success"></i>
          {{ totalSelected }} seleccionados
        </span>
        <button class="btn btn-primary btn-sm" @click="handleGuardar" :disabled="saving || loading">
          <span v-if="saving" class="spinner-border spinner-border-sm me-1"></span>
          <i class="bi bi-floppy me-1" v-else></i>
          Guardar
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div class="md-loading" v-if="loading">
      <div class="spinner-border text-primary"></div>
      <p class="text-muted mt-2 small">Cargando menú…</p>
    </div>

    <!-- Sin datos -->
    <div class="md-empty" v-else-if="!categories.length">
      <i class="bi bi-journal-x fs-1 text-muted"></i>
      <p class="text-muted mt-2">No hay insumos configurados para menú diario.</p>
    </div>

    <!-- Columnas de categorías -->
    <div class="md-grid" v-else>
      <div
        class="md-col"
        v-for="cat in categories"
        :key="cat.group_id"
      >
        <!-- Cabecera de columna -->
        <div class="md-col__head">
          <div class="md-col__head-top">
            <span class="md-col__title">{{ cat.group_name }}</span>
            <button class="md-col__toggle" @click="toggleGroupAll(cat)">
              {{ countSelected(cat) === cat.items.length ? 'Quitar' : 'Marcar todos' }}
            </button>
          </div>
          <span class="md-col__summary"
            :class="countSelected(cat) > 0 ? 'text-success' : 'text-muted'">
            {{ countSelected(cat) }} / {{ cat.items.length }}
          </span>
        </div>

        <!-- Lista de ítems -->
        <div class="md-col__body">
          <button
            v-for="item in cat.items"
            :key="item.item_id"
            class="md-item"
            :class="{ 'md-item--on': item.is_selected }"
            @click="toggleItem(item)"
          >
            <span class="md-item__dot"></span>
            <span class="md-item__name">{{ item.item_name }}</span>
            <i class="bi bi-check-lg md-item__check" v-if="item.is_selected"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- Barra inferior acciones rápidas -->
    <div class="md-footer" v-if="!loading && categories.length">
      <button class="btn btn-outline-secondary btn-sm" @click="selectAll">
        <i class="bi bi-check2-all me-1"></i>Todo
      </button>
      <button class="btn btn-outline-secondary btn-sm" @click="clearAll">
        <i class="bi bi-x-lg me-1"></i>Ninguno
      </button>
      <span class="md-footer__total">{{ totalItems }} ítems</span>
    </div>

    <!-- Toast -->
    <div class="md-toast" :class="{ 'md-toast--show': toastMsg }">
      <i class="bi bi-check-circle-fill me-2 text-success"></i>{{ toastMsg }}
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/apis'

const router   = useRouter()
const loading  = ref(false)
const saving   = ref(false)
const toastMsg = ref('')

const targetDate  = ref('')
const displayDate = ref('')
const categories  = ref([])

const totalSelected = computed(() =>
  categories.value.reduce((acc, cat) => acc + countSelected(cat), 0)
)
const totalItems = computed(() =>
  categories.value.reduce((acc, cat) => acc + cat.items.length, 0)
)

function countSelected(cat) {
  return cat.items.filter(i => i.is_selected).length
}

function toggleGroupAll(cat) {
  const allOn = countSelected(cat) === cat.items.length
  cat.items.forEach(i => { i.is_selected = !allOn })
}

function toggleItem(item) {
  item.is_selected = !item.is_selected
}

function selectAll() {
  categories.value.forEach(cat => cat.items.forEach(i => { i.is_selected = true }))
}

function clearAll() {
  categories.value.forEach(cat => cat.items.forEach(i => { i.is_selected = false }))
}

async function loadMenu() {
  loading.value = true
  try {
    const cid = JSON.parse(localStorage.getItem('user') || '{}').company_id
    const res = await api.get('/api/pos/comanda/menu-diario-admin', {
      headers: { 'X-Company-Id': cid },
    })
    targetDate.value  = res.data.date
    categories.value  = res.data.categories
    displayDate.value = formatDisplayDate(res.data.date)
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al cargar el menú diario')
  } finally {
    loading.value = false
  }
}

async function guardar() {
  saving.value = true
  try {
    const selected = []
    categories.value.forEach(cat =>
      cat.items.forEach(item => { if (item.is_selected) selected.push(item.item_id) })
    )
    const cid = JSON.parse(localStorage.getItem('user') || '{}').company_id
    await api.post('/api/pos/comanda/menu-diario-admin/guardar',
      { date: targetDate.value, selected_ids: selected },
      { headers: { 'X-Company-Id': cid } }
    )
    showToast(selected.length
      ? `Guardado: ${selected.length} ítems activos para hoy`
      : 'Menú del día borrado'
    )
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al guardar el menú')
  } finally {
    saving.value = false
  }
}

async function handleGuardar() { await guardar() }

async function handleSalir() {
  await guardar()
  router.back()
}

function showToast(msg) {
  toastMsg.value = msg
  setTimeout(() => { toastMsg.value = '' }, 3000)
}

function formatDisplayDate(d) {
  if (!d) return ''
  const [y, m, day] = d.split('-')
  return `${day}/${m}/${y}`
}

onMounted(loadMenu)
</script>

<style scoped>
/* ══ Layout base ══ */
.md-view {
  display: flex;
  flex-direction: column;
  min-height: 100dvh;
  background: #f1f5f9;
  padding-bottom: 64px; /* espacio para footer */
}

/* ══ Header ══ */
.md-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  position: sticky;
  top: 0;
  z-index: 20;
}

.md-header__back {
  background: none;
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  padding: 6px 10px;
  color: #475569;
  cursor: pointer;
  flex-shrink: 0;
}
.md-header__back:disabled { opacity: .5; }

.md-header__info { flex: 1; min-width: 0; }

.md-header__title {
  font-size: .95rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 1px;
}

.md-header__date { font-size: .78rem; color: #64748b; }

.md-header__actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.md-header__count { font-size: .8rem; font-weight: 600; color: #166534; }

/* ══ Loading / Empty ══ */
.md-loading, .md-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

/* ══ Grid de columnas ══
   auto-fill: cuantas quepan (mín 200px), las extra se van a la siguiente fila */
.md-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
  padding: 12px;
  align-items: start;
  flex: 1;
}

/* ══ Columna ══ */
.md-col {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.md-col__head {
  padding: 10px 12px 8px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
  position: sticky;
  top: 56px; /* altura del header */
}

.md-col__head-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-bottom: 2px;
}

.md-col__title {
  font-weight: 700;
  font-size: .82rem;
  color: #1e293b;
  text-transform: uppercase;
  letter-spacing: .3px;
  flex: 1;
  min-width: 0;
}

.md-col__toggle {
  background: none;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 1px 7px;
  font-size: .68rem;
  color: #475569;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
}
.md-col__toggle:hover { background: #f1f5f9; }

.md-col__summary { font-size: .72rem; font-weight: 600; }

/* ══ Lista de ítems ══ */
.md-col__body {
  overflow-y: auto;
  max-height: calc(100dvh - 190px);
  display: flex;
  flex-direction: column;
}

.md-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  background: #fff;
  border: none;
  border-bottom: 1px solid #f1f5f9;
  text-align: left;
  cursor: pointer;
  transition: background .1s;
  width: 100%;
}
.md-item:last-child { border-bottom: none; }
.md-item:hover { background: #f8fafc; }

.md-item--on {
  background: #dcfce7;
}
.md-item--on:hover { background: #bbf7d0; }

.md-item__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #cbd5e1;
  flex-shrink: 0;
  transition: background .1s;
}
.md-item--on .md-item__dot { background: #16a34a; }

.md-item__name {
  flex: 1;
  font-size: .8rem;
  font-weight: 500;
  color: #334155;
  line-height: 1.3;
}
.md-item--on .md-item__name { color: #166534; font-weight: 600; }

.md-item__check {
  font-size: .78rem;
  color: #16a34a;
  flex-shrink: 0;
}

/* ══ Footer acciones rápidas ══ */
.md-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #fff;
  border-top: 1px solid #e2e8f0;
  z-index: 20;
}

.md-footer__total {
  margin-left: auto;
  font-size: .78rem;
  color: #94a3b8;
}

/* ══ Toast ══ */
.md-toast {
  position: fixed;
  bottom: 70px;
  left: 50%;
  transform: translateX(-50%) translateY(60px);
  background: #1e293b;
  color: #fff;
  padding: 9px 18px;
  border-radius: 20px;
  font-size: .84rem;
  font-weight: 600;
  opacity: 0;
  transition: transform .3s, opacity .3s;
  z-index: 9999;
  white-space: nowrap;
  pointer-events: none;
}
.md-toast--show { transform: translateX(-50%) translateY(0); opacity: 1; }

/* ══ Tablet: máx 2-3 columnas ══ */
@media (max-width: 1024px) {
  .md-grid { grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); }
  .md-col__body { max-height: calc(50dvh - 100px); }
}

/* ══ Mobile ≤768px: 2 columnas ══ */
@media (max-width: 768px) {
  .md-grid {
    grid-template-columns: repeat(2, 1fr);
    padding: 8px;
    gap: 8px;
  }
  .md-col__body { max-height: calc(42dvh - 60px); }
  .md-header { padding: 10px 12px; }
  .md-header__count { display: none; }
  .md-col__head { top: 52px; padding: 8px 10px 6px; }
  .md-item { padding: 6px 10px; }
  .md-item__name { font-size: .75rem; }
}

/* ══ Mobile ≤480px: 1 columna ══ */
@media (max-width: 480px) {
  .md-grid { grid-template-columns: 1fr; }
  .md-col__body { max-height: none; }
  .md-col__toggle { display: none; }
}
</style>
