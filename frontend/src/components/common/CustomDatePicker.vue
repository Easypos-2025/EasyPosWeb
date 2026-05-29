<template>
  <div class="cdp-wrap" ref="wrapRef">
    <div class="cdp-trigger" @click="toggle" :class="{ 'cdp-open': open }">
      <i class="bi bi-calendar3 cdp-ico"></i>
      <span class="cdp-val">{{ displayValue }}</span>
      <i class="bi bi-chevron-down cdp-arr"></i>
    </div>

    <Teleport to="body">
      <div v-if="open" class="cdp-backdrop" @mousedown.self="open = false">
        <div class="cdp-panel" ref="panelRef" :style="panelStyle">

          <!-- ── Header ── -->
          <div class="cdp-hdr">
            <button class="cdp-nav-btn" @click.stop="shift(-1)" title="Mes anterior">
              <i class="bi bi-chevron-left"></i>
            </button>
            <div class="cdp-hdr-center">
              <button class="cdp-lbl" :class="{ active: mode === 'month' }" @click.stop="toggleMode('month')">
                {{ MESES[vm] }}
              </button>
              <button class="cdp-lbl" :class="{ active: mode === 'year' }" @click.stop="toggleMode('year')">
                {{ vy }}
              </button>
            </div>
            <button class="cdp-nav-btn" @click.stop="shift(1)" title="Mes siguiente">
              <i class="bi bi-chevron-right"></i>
            </button>
          </div>

          <!-- ── Calendario ── -->
          <div v-if="mode === 'cal'" class="cdp-grid">
            <div class="cdp-dow" v-for="d in DIAS" :key="d">{{ d }}</div>
            <div
              v-for="cell in cells" :key="cell.key"
              class="cdp-cell"
              :class="{
                'cell-empty': !cell.day,
                'cell-today': cell.isToday,
                'cell-sel':   cell.isSel,
              }"
              @click="cell.day && pick(cell.y, cell.m, cell.day)"
            >{{ cell.day || '' }}</div>
          </div>

          <!-- ── Selector de mes ── -->
          <div v-else-if="mode === 'month'" class="cdp-month-grid">
            <button
              v-for="(m, i) in MESES_CORTO" :key="i"
              class="cdp-m-btn"
              :class="{ 'cdp-m-active': i === vm }"
              @click.stop="vm = i; mode = 'cal'"
            >{{ m }}</button>
          </div>

          <!-- ── Selector de año ── -->
          <div v-else-if="mode === 'year'" class="cdp-year-section">
            <div class="cdp-year-nav">
              <button class="cdp-nav-btn" @click.stop="yearOffset -= 12"><i class="bi bi-chevron-left"></i></button>
              <span class="cdp-year-range">{{ yearRange[0] }} – {{ yearRange[yearRange.length - 1] }}</span>
              <button class="cdp-nav-btn" @click.stop="yearOffset += 12"><i class="bi bi-chevron-right"></i></button>
            </div>
            <div class="cdp-year-grid">
              <button
                v-for="y in yearRange" :key="y"
                class="cdp-y-btn"
                :class="{ 'cdp-y-active': y === vy }"
                @click.stop="vy = y; mode = 'cal'"
              >{{ y }}</button>
            </div>
          </div>

          <!-- ── Footer ── -->
          <div class="cdp-footer">
            <button class="cdp-btn-hoy" @click="selectToday">
              <i class="bi bi-calendar-check me-1"></i>Hoy
            </button>
            <button class="cdp-btn-cls" @click="open = false">Cerrar</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onUnmounted } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: 'DD/MM/AAAA' },
})
const emit = defineEmits(['update:modelValue'])

const DIAS        = ['Dom','Lun','Mar','Mié','Jue','Vie','Sáb']
const MESES       = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
const MESES_CORTO = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']

function todayISO() {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Bogota' }).format(new Date())
}
const TODAY = todayISO()

const open       = ref(false)
const mode       = ref('cal')
const wrapRef    = ref(null)
const panelStyle = ref({ position: 'fixed', top: '0px', left: '0px' })
const yearOffset = ref(0)

// Mes y año visibles en el calendario
const _initYear  = () => props.modelValue ? +props.modelValue.split('-')[0] : +TODAY.split('-')[0]
const _initMonth = () => props.modelValue ? +props.modelValue.split('-')[1] - 1 : +TODAY.split('-')[1] - 1

const vm = ref(_initMonth())
const vy = ref(_initYear())

// Valor mostrado en el trigger
const displayValue = computed(() => {
  if (!props.modelValue) return props.placeholder
  const [y, m, d] = props.modelValue.split('-')
  return `${d}/${m}/${y}`
})

// Celdas del calendario
const cells = computed(() => {
  const firstDow    = new Date(vy.value, vm.value, 1).getDay()
  const daysInMonth = new Date(vy.value, vm.value + 1, 0).getDate()
  const result      = []
  for (let i = 0; i < firstDow; i++) {
    result.push({ key: `e${i}`, day: 0 })
  }
  for (let d = 1; d <= daysInMonth; d++) {
    const ds = `${vy.value}-${String(vm.value + 1).padStart(2,'0')}-${String(d).padStart(2,'0')}`
    result.push({
      key: `d${d}`, day: d, y: vy.value, m: vm.value,
      isToday: ds === TODAY,
      isSel:   ds === props.modelValue,
    })
  }
  // Completar última fila hasta múltiplo de 7
  const total = firstDow + daysInMonth
  const rem   = total % 7
  if (rem) {
    for (let i = 0; i < 7 - rem; i++) result.push({ key: `f${i}`, day: 0 })
  }
  return result
})

// Rango de años para el selector
const yearRange = computed(() => {
  const center = vy.value + yearOffset.value
  return Array.from({ length: 12 }, (_, i) => center - 5 + i)
})

function toggleMode(m) {
  mode.value     = mode.value === m ? 'cal' : m
  yearOffset.value = 0
}

function shift(dir) {
  let m = vm.value + dir, y = vy.value
  if (m < 0)  { m = 11; y-- }
  if (m > 11) { m = 0;  y++ }
  vm.value = m; vy.value = y
}

function pick(y, m, d) {
  const ds = `${y}-${String(m + 1).padStart(2,'0')}-${String(d).padStart(2,'0')}`
  emit('update:modelValue', ds)
  open.value = false
}

function selectToday() {
  emit('update:modelValue', TODAY)
  const [y, m] = TODAY.split('-')
  vy.value = +y; vm.value = +m - 1
  open.value = false
}

function positionPanel() {
  if (!wrapRef.value) return
  const rect = wrapRef.value.getBoundingClientRect()
  const winW = window.innerWidth
  const winH = window.innerHeight

  if (winW < 600) {
    panelStyle.value = { position:'fixed', top:'50%', left:'50%', transform:'translate(-50%,-50%)' }
    return
  }
  let top  = rect.bottom + 6
  let left = rect.left
  if (top + 360 > winH) top = Math.max(4, rect.top - 366)
  if (left + 288 > winW) left = winW - 294
  if (left < 4) left = 4
  panelStyle.value = { position:'fixed', top:`${top}px`, left:`${left}px` }
}

function toggle() {
  if (open.value) { open.value = false; return }
  if (props.modelValue) {
    const [y, m] = props.modelValue.split('-')
    vy.value = +y; vm.value = +m - 1
  } else {
    const [y, m] = TODAY.split('-')
    vy.value = +y; vm.value = +m - 1
  }
  mode.value = 'cal'; yearOffset.value = 0
  open.value = true
  nextTick(positionPanel)
}

onUnmounted(() => { open.value = false })
</script>

<style scoped>
/* ── Trigger ─────────────────────────────────────────── */
.cdp-wrap    { position: relative; display: inline-block; width: 100%; }
.cdp-trigger {
  display: flex; align-items: center; gap: .4rem;
  padding: .32rem .6rem; border: 1px solid var(--bs-border-color, #dee2e6);
  border-radius: .375rem; background: #fff; cursor: pointer;
  font-size: .85rem; user-select: none; transition: border-color .15s;
  min-width: 130px;
}
.cdp-trigger:hover, .cdp-trigger.cdp-open { border-color: var(--primary-color, #3b82f6); }
.cdp-ico  { color: #6b7280; font-size: .85rem; flex-shrink: 0; }
.cdp-val  { flex: 1; color: #374151; }
.cdp-arr  { color: #9ca3af; font-size: .7rem; flex-shrink: 0; transition: transform .2s; }
.cdp-open .cdp-arr { transform: rotate(180deg); }

/* ── Backdrop ────────────────────────────────────────── */
.cdp-backdrop {
  position: fixed; inset: 0; z-index: 9998;
  background: transparent;
}

/* ── Panel ───────────────────────────────────────────── */
.cdp-panel {
  z-index: 9999; width: 288px;
  background: #fff; border: 1px solid #e5e7eb;
  border-radius: .6rem; box-shadow: 0 8px 30px rgba(0,0,0,.15);
  padding: .75rem; user-select: none;
}

/* ── Header ──────────────────────────────────────────── */
.cdp-hdr {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: .6rem;
}
.cdp-hdr-center { display: flex; align-items: center; gap: .3rem; }
.cdp-nav-btn {
  background: none; border: none; cursor: pointer; padding: .25rem .4rem;
  border-radius: .35rem; color: #374151; font-size: .85rem; line-height: 1;
  transition: background .15s;
}
.cdp-nav-btn:hover { background: #f3f4f6; }
.cdp-lbl {
  background: none; border: none; cursor: pointer; font-weight: 600;
  font-size: .88rem; color: #111827; padding: .2rem .35rem;
  border-radius: .3rem; transition: background .15s, color .15s;
}
.cdp-lbl:hover, .cdp-lbl.active { background: var(--primary-color, #3b82f6); color: #fff; }

/* ── Grilla calendario ───────────────────────────────── */
.cdp-grid {
  display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px;
  margin-bottom: .5rem;
}
.cdp-dow {
  text-align: center; font-size: .7rem; font-weight: 600;
  color: #6b7280; padding: .2rem 0;
}
.cdp-cell {
  text-align: center; font-size: .82rem; padding: .3rem 0;
  border-radius: .3rem; cursor: pointer; color: #374151;
  transition: background .12s, color .12s;
}
.cdp-cell:not(.cell-empty):hover { background: #eff6ff; color: #1d4ed8; }
.cell-empty  { cursor: default; }
.cell-today  { font-weight: 700; color: var(--primary-color, #2563eb); }
.cell-sel    {
  background: var(--primary-color, #2563eb) !important;
  color: #fff !important; font-weight: 700; border-radius: 50%;
}

/* ── Selector mes ────────────────────────────────────── */
.cdp-month-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: .35rem;
  margin-bottom: .5rem;
}
.cdp-m-btn {
  background: #f9fafb; border: 1px solid #e5e7eb; border-radius: .35rem;
  padding: .4rem .2rem; font-size: .82rem; cursor: pointer; color: #374151;
  transition: background .12s, color .12s;
}
.cdp-m-btn:hover    { background: #eff6ff; border-color: #93c5fd; }
.cdp-m-active       { background: var(--primary-color, #2563eb) !important; color: #fff !important; border-color: transparent !important; }

/* ── Selector año ────────────────────────────────────── */
.cdp-year-section   { margin-bottom: .5rem; }
.cdp-year-nav {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: .4rem;
}
.cdp-year-range { font-size: .8rem; color: #6b7280; font-weight: 600; }
.cdp-year-grid  {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: .3rem;
}
.cdp-y-btn {
  background: #f9fafb; border: 1px solid #e5e7eb; border-radius: .35rem;
  padding: .35rem .1rem; font-size: .82rem; cursor: pointer; color: #374151;
  transition: background .12s;
}
.cdp-y-btn:hover  { background: #eff6ff; border-color: #93c5fd; }
.cdp-y-active     { background: var(--primary-color, #2563eb) !important; color: #fff !important; border-color: transparent !important; }

/* ── Footer ──────────────────────────────────────────── */
.cdp-footer {
  display: flex; justify-content: space-between; align-items: center;
  border-top: 1px solid #f3f4f6; padding-top: .5rem; margin-top: .25rem;
}
.cdp-btn-hoy {
  background: none; border: 1px solid var(--primary-color, #2563eb);
  color: var(--primary-color, #2563eb); border-radius: .35rem;
  padding: .25rem .6rem; font-size: .8rem; cursor: pointer;
  transition: background .15s, color .15s;
}
.cdp-btn-hoy:hover { background: var(--primary-color, #2563eb); color: #fff; }
.cdp-btn-cls {
  background: none; border: 1px solid #e5e7eb; color: #6b7280;
  border-radius: .35rem; padding: .25rem .6rem; font-size: .8rem; cursor: pointer;
  transition: background .15s;
}
.cdp-btn-cls:hover { background: #f3f4f6; }

/* ── Mobile ──────────────────────────────────────────── */
@media (max-width: 576px) {
  .cdp-panel { width: 290px; }
  .cdp-cell  { font-size: .78rem; padding: .28rem 0; }
}
</style>
