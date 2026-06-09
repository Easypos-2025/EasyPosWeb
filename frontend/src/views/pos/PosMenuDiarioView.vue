<template>
  <div class="menu-diario-view">

    <!-- Header -->
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
      <p class="text-muted mt-2">Cargando menú…</p>
    </div>

    <!-- Sin datos -->
    <div class="md-empty" v-else-if="!categories.length">
      <i class="bi bi-journal-x fs-1 text-muted"></i>
      <p class="text-muted mt-2">No hay insumos configurados para menú diario.</p>
      <p class="text-muted small">Verifique que existan categorías con <em>percentage=1</em> y suministros con <em>control_stock=1</em>.</p>
    </div>

    <!-- Categorías -->
    <div class="md-body" v-else>

      <!-- Barra de selección rápida -->
      <div class="md-quick-bar">
        <button class="btn btn-outline-secondary btn-sm" @click="selectAll">
          <i class="bi bi-check2-all me-1"></i>Todo
        </button>
        <button class="btn btn-outline-secondary btn-sm" @click="clearAll">
          <i class="bi bi-x-lg me-1"></i>Ninguno
        </button>
        <div class="md-quick-bar__spacer"></div>
        <span class="md-quick-bar__total">
          {{ totalItems }} ítems disponibles
        </span>
      </div>

      <!-- Acordeón de categorías -->
      <div
        v-for="cat in categories"
        :key="cat.group_id"
        class="md-cat"
        :class="{ 'md-cat--open': openGroups.has(cat.group_id) }"
      >
        <!-- Cabecera -->
        <button class="md-cat__head" @click="toggleGroup(cat.group_id)">
          <div class="md-cat__head-left">
            <span class="md-cat__name">{{ cat.group_name }}</span>
            <span class="md-cat__summary">
              {{ countSelected(cat) }} / {{ cat.items.length }} seleccionados
            </span>
          </div>
          <div class="md-cat__head-right">
            <span
              class="md-cat__badge"
              :class="countSelected(cat) === cat.items.length ? 'md-cat__badge--full' : countSelected(cat) > 0 ? 'md-cat__badge--partial' : 'md-cat__badge--none'"
            >
              {{ countSelected(cat) === cat.items.length ? 'Completo' : countSelected(cat) > 0 ? 'Parcial' : 'Sin selección' }}
            </span>
            <button class="md-cat__toggle-btn" @click.stop="toggleGroupAll(cat)">
              {{ countSelected(cat) === cat.items.length ? 'Quitar todos' : 'Marcar todos' }}
            </button>
            <i class="bi ms-2" :class="openGroups.has(cat.group_id) ? 'bi-chevron-up' : 'bi-chevron-down'"></i>
          </div>
        </button>

        <!-- Items -->
        <div class="md-cat__body" v-if="openGroups.has(cat.group_id)">
          <div class="md-items-grid">
            <button
              v-for="item in cat.items"
              :key="item.item_id"
              class="md-item"
              :class="{ 'md-item--selected': item.is_selected }"
              @click="toggleItem(item)"
            >
              <span class="md-item__check">
                <i class="bi bi-check-lg" v-if="item.is_selected"></i>
              </span>
              <span class="md-item__name">{{ item.item_name }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast de confirmación -->
    <div class="md-toast" :class="{ 'md-toast--show': toastMsg }" v-if="toastMsg">
      <i class="bi bi-check-circle-fill me-2 text-success"></i>
      {{ toastMsg }}
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
const openGroups  = ref(new Set())

const totalSelected = computed(() => categories.value.reduce((acc, cat) => acc + countSelected(cat), 0))
const totalItems    = computed(() => categories.value.reduce((acc, cat) => acc + cat.items.length, 0))

function countSelected(cat) {
  return cat.items.filter(i => i.is_selected).length
}

function toggleGroup(id) {
  const s = new Set(openGroups.value)
  s.has(id) ? s.delete(id) : s.add(id)
  openGroups.value = s
}

function toggleGroupAll(cat) {
  const allSelected = countSelected(cat) === cat.items.length
  cat.items.forEach(i => { i.is_selected = !allSelected })
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

    // Abrir todos los grupos por defecto
    openGroups.value = new Set(res.data.categories.map(c => c.group_id))
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
    categories.value.forEach(cat => {
      cat.items.forEach(item => {
        if (item.is_selected) selected.push(item.item_id)
      })
    })

    const cid = JSON.parse(localStorage.getItem('user') || '{}').company_id
    await api.post('/api/pos/comanda/menu-diario-admin/guardar',
      { date: targetDate.value, selected_ids: selected },
      { headers: { 'X-Company-Id': cid } }
    )

    showToast(selected.length ? `Menú guardado: ${selected.length} ítems activos` : 'Menú del día borrado')
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al guardar el menú')
  } finally {
    saving.value = false
  }
}

async function handleGuardar() {
  await guardar()
}

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
.menu-diario-view {
  display: flex;
  flex-direction: column;
  min-height: 100dvh;
  background: #f1f5f9;
}

/* ── Header ── */
.md-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  position: sticky;
  top: 0;
  z-index: 10;
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

.md-header__info {
  flex: 1;
  min-width: 0;
}

.md-header__title {
  font-size: 1rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 2px;
}

.md-header__date {
  font-size: .8rem;
  color: #64748b;
}

.md-header__actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.md-header__count {
  font-size: .82rem;
  font-weight: 600;
  color: #166534;
}

/* ── Loading / Empty ── */
.md-loading, .md-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

/* ── Body ── */
.md-body {
  padding: 14px 14px 80px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* ── Barra rápida ── */
.md-quick-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}

.md-quick-bar__spacer { flex: 1; }

.md-quick-bar__total {
  font-size: .78rem;
  color: #94a3b8;
}

/* ── Categoría acordeón ── */
.md-cat {
  background: #fff;
  border: 1.5px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  transition: border-color .15s;
}
.md-cat--open { border-color: #2563eb; }

.md-cat__head {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  background: #f8fafc;
  border: none;
  cursor: pointer;
  text-align: left;
  gap: 8px;
}
.md-cat--open .md-cat__head { background: #eff6ff; }

.md-cat__head-left { display: flex; flex-direction: column; gap: 2px; flex: 1; min-width: 0; }
.md-cat__head-right { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }

.md-cat__name {
  font-weight: 700;
  font-size: .9rem;
  color: #1e293b;
  text-transform: uppercase;
  letter-spacing: .4px;
}

.md-cat__summary {
  font-size: .75rem;
  color: #64748b;
}

.md-cat__badge {
  font-size: .7rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 20px;
}
.md-cat__badge--full    { background: #dcfce7; color: #166534; }
.md-cat__badge--partial { background: #fef9c3; color: #854d0e; }
.md-cat__badge--none    { background: #fee2e2; color: #991b1b; }

.md-cat__toggle-btn {
  background: none;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 2px 8px;
  font-size: .72rem;
  color: #475569;
  cursor: pointer;
  white-space: nowrap;
}
.md-cat__toggle-btn:hover { background: #f1f5f9; }

.md-cat__body {
  padding: 12px 14px 14px;
  border-top: 1px solid #e2e8f0;
}

/* ── Grid de ítems ── */
.md-items-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.md-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1.5px solid #e2e8f0;
  border-radius: 20px;
  background: #fff;
  font-size: .85rem;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  transition: all .15s;
}
.md-item:hover { border-color: #2563eb; color: #2563eb; }
.md-item--selected {
  border-color: #16a34a;
  background: #16a34a;
  color: #fff;
}

.md-item__check {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid currentColor;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: .7rem;
  flex-shrink: 0;
}
.md-item--selected .md-item__check {
  background: rgba(255,255,255,.25);
  border-color: transparent;
}

/* ── Toast ── */
.md-toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%) translateY(80px);
  background: #1e293b;
  color: #fff;
  padding: 10px 20px;
  border-radius: 20px;
  font-size: .88rem;
  font-weight: 600;
  opacity: 0;
  transition: transform .3s, opacity .3s;
  z-index: 9999;
  white-space: nowrap;
}
.md-toast--show {
  transform: translateX(-50%) translateY(0);
  opacity: 1;
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .md-header { padding: 10px 12px; gap: 8px; }
  .md-header__count { display: none; }
  .md-body { padding: 10px 10px 80px; gap: 8px; }
  .md-cat__head { padding: 10px 12px; }
  .md-item { padding: 7px 11px; font-size: .82rem; }
}

@media (max-width: 576px) {
  .md-header__title { font-size: .9rem; }
  .md-header__date  { font-size: .72rem; }
  .md-body { padding: 8px 8px 80px; gap: 7px; }
  .md-cat__name { font-size: .83rem; }
  .md-items-grid { gap: 6px; }
  .md-item { padding: 6px 10px; font-size: .8rem; }
  .md-cat__toggle-btn { display: none; }
}
</style>
