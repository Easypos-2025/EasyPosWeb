<!--
  TaskTooltip — muestra info completa de una tarea al hover (PC) o long-press (móvil).
  Props:
    task      — objeto tarea
    assetName — string nombre del activo
  Emits:
    (nada, solo visual)
-->
<template>
  <div
    class="tt-wrapper"
    @mouseenter="onMouseEnter"
    @mouseleave="onMouseLeave"
    @touchstart.passive="onTouchStart"
    @touchend.passive="onTouchEnd"
    @touchmove.passive="onTouchEnd"
  >
    <!-- Contenido del slot (título, activo, etc.) -->
    <slot />

    <!-- TOOLTIP DESKTOP (posicionado dinámicamente) -->
    <Teleport to="body">
      <div
        v-if="showTooltip && !isMobile"
        class="tt-box"
        :style="tooltipStyle"
        @mouseenter="cancelHide"
        @mouseleave="onMouseLeave"
      >
        <div class="tt-header">
          <span class="tt-status" :class="statusClass(task.status_id)">{{ task.status_name }}</span>
          <span v-if="isOverdue" class="tt-overdue"><i class="bi bi-exclamation-triangle-fill"></i> Atrasada</span>
        </div>
        <p class="tt-title">{{ task.title }}</p>
        <div v-if="assetName && assetName !== '—'" class="tt-row">
          <i class="bi bi-building"></i> {{ assetName }}
        </div>
        <div v-if="task.description" class="tt-desc">{{ task.description }}</div>
        <div class="tt-meta">
          <span v-if="task.assigned_to_name"><i class="bi bi-person-check"></i> {{ task.assigned_to_name }}</span>
          <span v-if="task.worker_name"><i class="bi bi-tools"></i> {{ task.worker_name }}</span>
          <span v-if="task.due_date"><i class="bi bi-calendar3"></i> {{ fmtDate(task.due_date) }}</span>
        </div>
        <div v-if="task.progress > 0" class="tt-progress">
          <div class="tt-bar"><div class="tt-fill" :style="{ width: task.progress + '%' }"></div></div>
          <span>{{ task.progress }}%</span>
        </div>
      </div>
    </Teleport>

    <!-- MODAL MÓVIL (centrado) -->
    <Teleport to="body">
      <div v-if="showTooltip && isMobile" class="tt-modal-overlay" @click="showTooltip = false">
        <div class="tt-modal" @click.stop>
          <button class="tt-modal-close" @click="showTooltip = false"><i class="bi bi-x-lg"></i></button>
          <div class="tt-header">
            <span class="tt-status" :class="statusClass(task.status_id)">{{ task.status_name }}</span>
            <span v-if="isOverdue" class="tt-overdue"><i class="bi bi-exclamation-triangle-fill"></i> Atrasada</span>
          </div>
          <p class="tt-title">{{ task.title }}</p>
          <div v-if="assetName && assetName !== '—'" class="tt-row">
            <i class="bi bi-building"></i> {{ assetName }}
          </div>
          <div v-if="task.description" class="tt-desc">{{ task.description }}</div>
          <div class="tt-meta">
            <span v-if="task.assigned_to_name"><i class="bi bi-person-check"></i> {{ task.assigned_to_name }}</span>
            <span v-if="task.worker_name"><i class="bi bi-tools"></i> {{ task.worker_name }}</span>
            <span v-if="task.due_date"><i class="bi bi-calendar3"></i> {{ fmtDate(task.due_date) }}</span>
          </div>
          <div v-if="task.progress > 0" class="tt-progress">
            <div class="tt-bar"><div class="tt-fill" :style="{ width: task.progress + '%' }"></div></div>
            <span>{{ task.progress }}%</span>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed } from "vue"

const props = defineProps({
  task:      { type: Object,  required: true },
  assetName: { type: String,  default: "—" },
})

const showTooltip  = ref(false)
const tooltipStyle = ref({})
const isMobile     = ref(window.matchMedia("(hover: none)").matches)

let hoverTimer  = null
let hideTimer   = null
let touchTimer  = null

// ── PC: hover ─────────────────────────────────────────────────
function onMouseEnter(e) {
  clearTimeout(hideTimer)
  hoverTimer = setTimeout(() => {
    positionTooltip(e)
    showTooltip.value = true
  }, 250)
}

function onMouseLeave() {
  clearTimeout(hoverTimer)
  hideTimer = setTimeout(() => { showTooltip.value = false }, 120)
}

function cancelHide() {
  clearTimeout(hideTimer)
}

function positionTooltip(e) {
  const TOOLTIP_W = 260
  const TOOLTIP_H = 180
  const VP_W = window.innerWidth
  const VP_H = window.innerHeight
  const rect = e.currentTarget.getBoundingClientRect()

  let left = rect.left
  let top  = rect.bottom + 6

  if (left + TOOLTIP_W > VP_W - 12) left = VP_W - TOOLTIP_W - 12
  if (top  + TOOLTIP_H > VP_H - 12) top  = rect.top - TOOLTIP_H - 6

  tooltipStyle.value = {
    position: "fixed",
    top:      top  + "px",
    left:     left + "px",
    zIndex:   "9999",
  }
}

// ── Móvil: long press ─────────────────────────────────────────
function onTouchStart() {
  touchTimer = setTimeout(() => { showTooltip.value = true }, 600)
}

function onTouchEnd() {
  clearTimeout(touchTimer)
}

// ── Helpers ────────────────────────────────────────────────────
const STATUS_CLASSES = {
  1: "tt-s-orange", 2: "tt-s-blue",  3: "tt-s-green",
  4: "tt-s-purple", 5: "tt-s-dark",  6: "tt-s-red",
}
function statusClass(id) { return STATUS_CLASSES[id] || "tt-s-gray" }

const isOverdue = computed(() =>
  props.task.due_date &&
  new Date(props.task.due_date) < new Date() &&
  ![5, 6].includes(props.task.status_id)
)

function fmtDate(iso) {
  if (!iso) return ""
  return new Date(iso).toLocaleDateString("es-CO", { day: "2-digit", month: "2-digit", year: "numeric" })
}
</script>

<style scoped>
.tt-wrapper { display: contents; }

/* ── TOOLTIP DESKTOP ── */
.tt-box {
  background: #1e293b;
  color: #f1f5f9;
  border-radius: 12px;
  padding: 12px 14px;
  width: 260px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.35);
  pointer-events: auto;
  animation: tt-in 0.15s ease;
}
@keyframes tt-in {
  from { opacity: 0; transform: translateY(4px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ── MODAL MÓVIL ── */
.tt-modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center;
  z-index: 9999;
}
.tt-modal {
  background: #1e293b; color: #f1f5f9;
  border-radius: 16px; padding: 20px;
  width: 320px; max-width: 90vw;
  position: relative;
  box-shadow: 0 20px 60px rgba(0,0,0,0.4);
}
.tt-modal-close {
  position: absolute; top: 12px; right: 14px;
  background: none; border: none; color: rgba(255,255,255,0.5);
  font-size: 16px; cursor: pointer;
}
.tt-modal-close:hover { color: #fff; }

/* ── CONTENIDO COMPARTIDO ── */
.tt-header  { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.tt-status  { font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 20px; }
.tt-s-orange { background: #fff7ed; color: #c2410c; }
.tt-s-blue   { background: #dbeafe; color: #1e40af; }
.tt-s-green  { background: #dcfce7; color: #16a34a; }
.tt-s-purple { background: #f3e8ff; color: #7c3aed; }
.tt-s-dark   { background: #d1fae5; color: #065f46; }
.tt-s-red    { background: #fef2f2; color: #b91c1c; }
.tt-s-gray   { background: #f1f5f9; color: #64748b; }
.tt-overdue  { font-size: 10px; color: #fca5a5; display: flex; align-items: center; gap: 3px; }

.tt-title { font-size: 13px; font-weight: 700; color: #f8fafc; margin: 0 0 6px; line-height: 1.35; }
.tt-row   { font-size: 11px; color: rgba(255,255,255,0.6); display: flex; align-items: center; gap: 5px; margin-bottom: 4px; }
.tt-desc  { font-size: 11px; color: rgba(255,255,255,0.55); line-height: 1.45; margin-bottom: 8px;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.tt-meta  { display: flex; flex-direction: column; gap: 3px; margin-bottom: 8px; }
.tt-meta span { font-size: 11px; color: rgba(255,255,255,0.55); display: flex; align-items: center; gap: 5px; }

.tt-progress { display: flex; align-items: center; gap: 8px; }
.tt-bar  { flex: 1; height: 4px; background: rgba(255,255,255,0.15); border-radius: 3px; overflow: hidden; }
.tt-fill { height: 100%; background: #3b82f6; border-radius: 3px; }
.tt-progress span { font-size: 11px; color: rgba(255,255,255,0.5); min-width: 28px; }
</style>
