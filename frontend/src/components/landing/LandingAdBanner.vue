<template>
  <div class="ad-banner-wrap">

    <!-- ── Desktop / Tablet: 3 slots en fila ── -->
    <template v-if="!isMobilePortrait">
      <div v-for="(slot, si) in slots" :key="slot.slot" class="ad-slot">
        <component
          :is="slot.cta_url ? 'a' : 'div'"
          v-bind="slot.cta_url ? { href: slot.cta_url, target: '_blank', rel: 'noopener noreferrer' } : {}"
          class="slot-inner"
          :class="{ 'slot-link': slot.cta_url }"
        >
          <template v-if="slot.active && slot.pieces?.length">
            <SlotPiece
              :piece="currentSlotPiece(slot, si)"
              :title="slot.title"
              :muted="slotMuted[si]"
            />
            <!-- Botón audio (video/youtube) -->
            <button
              v-if="isMediaPiece(currentSlotPiece(slot, si))"
              class="btn-audio"
              @click.prevent.stop="toggleAudio(si)"
              :title="slotMuted[si] ? 'Activar audio' : 'Silenciar'"
            >
              <i :class="slotMuted[si] ? 'bi bi-volume-mute-fill' : 'bi bi-volume-up-fill'"></i>
            </button>
            <!-- Dots piezas múltiples -->
            <div v-if="slot.pieces.length > 1" class="slot-piece-dots">
              <span v-for="(p, pi) in slot.pieces" :key="pi"
                class="spdot" :class="{ active: pi === slotPieceIdx[si] }"></span>
            </div>
          </template>
          <!-- Placeholder → contacto -->
          <template v-else>
            <a href="#contacto" class="slot-placeholder-inner">
              <div class="ph-bg"></div>
              <div class="ph-content">
                <div class="ph-icon-wrap"><i class="bi bi-megaphone-fill ph-icon"></i></div>
                <div class="ph-text">
                  <span class="ph-title">¡Paute Aquí!</span>
                  <span class="ph-sub">Llega a miles de asociados</span>
                </div>
                <span class="ph-cta">→ Solicitar espacio</span>
              </div>
            </a>
          </template>
        </component>
      </div>
    </template>

    <!-- ── Móvil portrait: carrusel de slots ── -->
    <template v-else>
      <div class="carousel-wrap">
        <Transition name="ad-fade" mode="out-in">
          <div :key="`${currentSlot}-${slotPieceIdx[currentSlot]}`" class="ad-slot carousel-slot">
            <component
              :is="slots[currentSlot]?.cta_url ? 'a' : 'div'"
              v-bind="slots[currentSlot]?.cta_url ? { href: slots[currentSlot].cta_url, target: '_blank', rel: 'noopener noreferrer' } : {}"
              class="slot-inner"
              :class="{ 'slot-link': slots[currentSlot]?.cta_url }"
            >
              <template v-if="slots[currentSlot]?.active && slots[currentSlot]?.pieces?.length">
                <SlotPiece
                  :piece="currentSlotPiece(slots[currentSlot], currentSlot)"
                  :title="slots[currentSlot].title"
                  :muted="slotMuted[currentSlot]"
                />
                <button
                  v-if="isMediaPiece(currentSlotPiece(slots[currentSlot], currentSlot))"
                  class="btn-audio"
                  @click.prevent.stop="toggleAudio(currentSlot)"
                  :title="slotMuted[currentSlot] ? 'Activar audio' : 'Silenciar'"
                >
                  <i :class="slotMuted[currentSlot] ? 'bi bi-volume-mute-fill' : 'bi bi-volume-up-fill'"></i>
                </button>
              </template>
              <template v-else>
                <a href="#contacto" class="slot-placeholder-inner">
                  <div class="ph-bg"></div>
                  <div class="ph-content">
                    <div class="ph-icon-wrap"><i class="bi bi-megaphone-fill ph-icon"></i></div>
                    <div class="ph-text">
                      <span class="ph-title">¡Paute Aquí!</span>
                      <span class="ph-sub">Llega a miles de asociados</span>
                    </div>
                    <span class="ph-cta">→ Solicitar espacio</span>
                  </div>
                </a>
              </template>
            </component>
          </div>
        </Transition>
        <!-- Dots slots -->
        <div class="carousel-dots">
          <button v-for="i in 3" :key="i" class="c-dot"
            :class="{ active: i - 1 === currentSlot }"
            @click="goToSlot(i - 1)" :aria-label="`Pauta ${i}`"></button>
        </div>
      </div>
    </template>

  </div>
</template>

<!-- Sub-componente: renderiza una pieza (imagen/video/youtube/texto) -->
<script>
import { defineComponent, h, computed } from "vue"

const SlotPiece = defineComponent({
  name: "SlotPiece",
  props: { piece: Object, title: String, muted: { type: Boolean, default: true } },
  setup(props) {
    const ytSrc = computed(() => {
      if (!props.piece?.youtube_id) return ""
      const mute = props.muted ? "&mute=1" : ""
      return `https://www.youtube.com/embed/${props.piece.youtube_id}?autoplay=1&loop=1&playlist=${props.piece.youtube_id}&controls=0&rel=0${mute}`
    })
    return { ytSrc }
  },
  render() {
    const p = this.piece
    if (!p) return null
    const { piece_type, media_url, text_content } = p

    if (piece_type === "image")
      return h("img", { src: media_url, alt: this.title || "Pauta", class: "slot-media", loading: "lazy" })

    if (piece_type === "video")
      return h("video", {
        src: media_url, autoplay: true, muted: this.muted,
        loop: true, playsinline: true, preload: "metadata", class: "slot-media"
      })

    if (piece_type === "youtube")
      return h("div", { class: "slot-yt-wrap" }, [
        h("iframe", {
          key: this.ytSrc,   // force remount when muted changes
          src: this.ytSrc, frameborder: "0",
          allow: "autoplay; encrypted-media", allowfullscreen: true, class: "slot-yt"
        })
      ])

    if (piece_type === "text")
      return h("div", { class: "slot-text" }, [
        h("p", { class: "slot-text-title" }, this.title || ""),
        h("p", { class: "slot-text-body" }, text_content),
      ])

    return null
  }
})

export default { components: { SlotPiece } }
</script>

<script setup>
import { ref, watch, onMounted, onUnmounted } from "vue"
import api from "@/services/apis"

// ── Orientación ────────────────────────────────────────────────────────────
const isMobilePortrait = ref(false)
function checkOrientation() {
  isMobilePortrait.value = window.innerWidth < 560 && window.innerHeight > window.innerWidth
}

// ── Audio por slot ─────────────────────────────────────────────────────────
const slotMuted = ref([true, true, true])
function toggleAudio(si) { slotMuted.value[si] = !slotMuted.value[si] }
function isMediaPiece(piece) {
  return piece?.piece_type === "video" || piece?.piece_type === "youtube"
}

// ── Datos ──────────────────────────────────────────────────────────────────
const slots        = ref([
  { slot: 1, active: false, pieces: [] },
  { slot: 2, active: false, pieces: [] },
  { slot: 3, active: false, pieces: [] },
])
const slotPieceIdx = ref([0, 0, 0])
const currentSlot  = ref(0)
const slotTimers   = [null, null, null]

function currentSlotPiece(slot, si) {
  return slot.pieces[slotPieceIdx.value[si] % slot.pieces.length] ?? slot.pieces[0]
}

// ── Duración inteligente por tipo ──────────────────────────────────────────
function getVideoDuration(url) {
  return new Promise((resolve) => {
    const v = document.createElement("video")
    v.preload = "metadata"; v.src = url
    v.onloadedmetadata = () => { resolve(Math.max(v.duration * 1000, 4000)); v.src = "" }
    v.onerror         = () => resolve(60_000)
    setTimeout(()     => resolve(60_000), 8000)
  })
}

async function pieceDuration(piece) {
  if (!piece) return 8_000
  if (piece.piece_type === "video" && piece.media_url) return await getVideoDuration(piece.media_url)
  if (piece.piece_type === "youtube") return 5 * 60 * 1000
  return 8_000   // imagen / texto
}

function clearSlotTimers() {
  slotTimers.forEach((_, i) => { clearTimeout(slotTimers[i]); slotTimers[i] = null })
}

// ── Scheduling: respeta duración + avanza slot en móvil al completar ciclo ─
async function scheduleSlot(si) {
  const slot = slots.value[si]
  if (!slot?.pieces?.length) return
  if (slot.pieces.length <= 1 && !isMobilePortrait.value) return  // 1 pieza sin rotación en desktop

  const piece    = slot.pieces[slotPieceIdx.value[si]]
  const duration = await pieceDuration(piece)

  slotTimers[si] = setTimeout(() => {
    const len       = slots.value[si]?.pieces?.length ?? 1
    const nextPiece = len > 1 ? (slotPieceIdx.value[si] + 1) % len : 0
    slotPieceIdx.value[si] = nextPiece

    if (isMobilePortrait.value) {
      // Móvil: cuando las piezas del slot completan ciclo → avanzar slot
      if (nextPiece === 0) {
        currentSlot.value = (currentSlot.value + 1) % 3
        scheduleSlot(currentSlot.value)
      } else {
        scheduleSlot(si)
      }
    } else {
      scheduleSlot(si)
    }
  }, duration)
}

function startTimers() {
  clearSlotTimers()
  if (isMobilePortrait.value) {
    scheduleSlot(currentSlot.value)  // cascada en móvil
  } else {
    slots.value.forEach((_, si) => scheduleSlot(si))  // independiente en desktop
  }
}

// Reiniciar timers al cambiar orientación
watch(isMobilePortrait, () => {
  slotPieceIdx.value = [0, 0, 0]
  startTimers()
})

function goToSlot(idx) {
  clearSlotTimers()
  currentSlot.value    = idx
  slotPieceIdx.value   = [0, 0, 0]
  scheduleSlot(idx)
}

async function loadSlots() {
  try {
    const res = await api.get("/ads/active-slots")
    if (Array.isArray(res.data)) {
      slots.value        = res.data
      slotPieceIdx.value = [0, 0, 0]
      currentSlot.value  = 0
      startTimers()
    }
  } catch {}
}

let refreshTimer = null

onMounted(() => {
  checkOrientation()
  window.addEventListener("resize", () => { checkOrientation() })
  loadSlots()
  refreshTimer = setInterval(loadSlots, 5 * 60 * 1000)
})

onUnmounted(() => {
  window.removeEventListener("resize", checkOrientation)
  if (refreshTimer) clearInterval(refreshTimer)
  clearSlotTimers()
})
</script>

<style scoped>
.ad-banner-wrap {
  width: 100%; height: 100%;
  display: flex; flex-direction: row;
  gap: 5px; padding: 5px; box-sizing: border-box;
  background: #0a0e1a;
}

.ad-slot {
  flex: 1; border-radius: 10px; overflow: hidden;
  position: relative; min-width: 0;
}

.slot-inner {
  display: flex; width: 100%; height: 100%;
  position: relative; overflow: hidden; text-decoration: none;
}
.slot-link { cursor: pointer; transition: opacity .2s; }
.slot-link:hover { opacity: .9; }

/* ── Placeholder ── */
.slot-placeholder-inner {
  display: flex; width: 100%; height: 100%;
  text-decoration: none; cursor: pointer; transition: filter .2s;
}
.slot-placeholder-inner:hover { filter: brightness(1.1); }

.ph-bg {
  position: absolute; inset: 0;
  background: linear-gradient(135deg, #2563eb 0%, #4f46e5 45%, #7c3aed 100%);
}
.ph-bg::before {
  content: ""; position: absolute; border-radius: 50%;
  width: 130px; height: 130px; top: -40px; right: -30px;
  background: rgba(255,255,255,.08);
}
.ph-bg::after {
  content: ""; position: absolute; border-radius: 50%;
  width: 90px; height: 90px; bottom: -20px; left: -15px;
  background: rgba(255,255,255,.06);
}
.ph-content {
  position: relative; z-index: 1;
  display: flex; align-items: center; width: 100%; height: 100%;
  gap: 14px; padding: 0 20px;
}
.ph-icon-wrap {
  flex-shrink: 0; width: 46px; height: 46px;
  background: rgba(255,255,255,.15); border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
}
.ph-icon { font-size: 24px; color: #fbbf24; }
.ph-text { flex: 1; display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.ph-title { font-size: 16px; font-weight: 800; color: #fff; line-height: 1; white-space: nowrap; }
.ph-sub   { font-size: 12px; color: rgba(255,255,255,.8); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ph-cta {
  flex-shrink: 0;
  background: linear-gradient(90deg,#10b981,#0ea5e9);
  color: #fff; font-size: 12px; font-weight: 800;
  padding: 8px 16px; border-radius: 20px; white-space: nowrap;
}

/* ── Botón audio ── */
.btn-audio {
  position: absolute; bottom: 8px; right: 8px; z-index: 10;
  width: 28px; height: 28px; border-radius: 50%;
  background: rgba(0,0,0,.55); border: 1px solid rgba(255,255,255,.25);
  color: #fff; font-size: 12px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: background .2s, transform .15s;
  backdrop-filter: blur(4px);
}
.btn-audio:hover { background: rgba(0,0,0,.8); transform: scale(1.1); }

/* ── Dots piezas ── */
.slot-piece-dots {
  position: absolute; bottom: 5px; left: 50%; transform: translateX(-50%);
  display: flex; gap: 4px; z-index: 5; pointer-events: none;
}
.spdot {
  width: 5px; height: 5px; border-radius: 50%;
  background: rgba(255,255,255,.35); transition: background .2s, transform .2s;
}
.spdot.active { background: #fff; transform: scale(1.3); }

/* ── Carrusel móvil ── */
.carousel-wrap { flex: 1; position: relative; display: flex; flex-direction: column; }
.carousel-slot { flex: 1; }
.carousel-dots {
  position: absolute; bottom: 6px; left: 50%; transform: translateX(-50%);
  display: flex; gap: 6px; z-index: 10;
}
.c-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: rgba(255,255,255,.35); border: none; cursor: pointer;
  transition: background .2s, transform .2s; padding: 0;
}
.c-dot.active { background: #fff; transform: scale(1.25); }

/* ── Transición ── */
.ad-fade-enter-active, .ad-fade-leave-active { transition: opacity .3s; }
.ad-fade-enter-from, .ad-fade-leave-to       { opacity: 0; }

/* ── Responsive ── */
@media (max-width: 767px) {
  .ad-banner-wrap { gap: 3px; padding: 3px; }
  .ad-slot        { border-radius: 7px; }
  .ph-content     { gap: 8px; padding: 0 12px; }
  .ph-icon-wrap   { width: 36px; height: 36px; border-radius: 9px; }
  .ph-icon        { font-size: 18px; }
  .ph-title       { font-size: 13px; }
  .ph-sub         { font-size: 10px; }
  .ph-cta         { font-size: 10px; padding: 5px 10px; }
  .btn-audio      { width: 24px; height: 24px; font-size: 10px; bottom: 6px; right: 6px; }
}
@media (max-width: 420px) {
  .ph-title { font-size: 12px; }
  .ph-cta   { display: none; }
}
</style>

<!-- Estilos globales para SlotPiece (render function) -->
<style>
.slot-media {
  width: 100%; height: 100%;
  object-fit: cover; display: block; flex-shrink: 0;
}
.slot-yt-wrap {
  flex: 1; background: #000;
  width: 100%; height: 100%; display: flex;
}
.slot-yt {
  width: 100%; height: 100%;
  border: none; display: block; flex: 1;
}
.slot-text {
  flex: 1; width: 100%;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 12px; gap: 5px;
  background: linear-gradient(135deg,#1e3a5f,#0d4f3c);
}
.slot-text-title { font-size: 13px; font-weight: 700; color: #fff; text-align: center; margin: 0; }
.slot-text-body  { font-size: 11px; color: rgba(255,255,255,.75); text-align: center; line-height: 1.5; margin: 0; }
</style>
