<template>
  <div class="ad-banner-wrap">

    <!-- ── Desktop / Tablet: 3 slots en fila ── -->
    <template v-if="!isMobilePortrait">
      <div v-for="(slot, si) in slots" :key="slot.slot" class="ad-slot">
        <SlotItem :slot="slot" :si="si" />
      </div>
    </template>

    <!-- ── Móvil portrait: carrusel de 1 slot ── -->
    <template v-else>
      <div class="carousel-wrap">
        <Transition name="ad-fade" mode="out-in">
          <div :key="currentSlot" class="ad-slot carousel-slot">
            <SlotItem :slot="slots[currentSlot]" :si="currentSlot" />
          </div>
        </Transition>
        <!-- Indicador de puntos -->
        <div class="carousel-dots">
          <button
            v-for="i in 3" :key="i"
            class="c-dot"
            :class="{ active: i - 1 === currentSlot }"
            @click="goToSlot(i - 1)"
            :aria-label="`Pauta ${i}`"
          ></button>
        </div>
      </div>
    </template>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, h, computed } from "vue"
import api from "@/services/apis"

// ── Detección móvil portrait ───────────────────────────────────────────────
const isMobilePortrait = ref(false)

function checkOrientation() {
  isMobilePortrait.value = window.innerWidth < 560 && window.innerHeight > window.innerWidth
}

// ── Datos slots ────────────────────────────────────────────────────────────
const slots = ref([
  { slot: 1, active: false, pieces: [] },
  { slot: 2, active: false, pieces: [] },
  { slot: 3, active: false, pieces: [] },
])

async function loadSlots() {
  try {
    const res = await api.get("/ads/active-slots")
    if (Array.isArray(res.data)) slots.value = res.data
  } catch {}
}

// ── Carrusel móvil ─────────────────────────────────────────────────────────
const currentSlot = ref(0)
let carouselTimer = null

function goToSlot(idx) {
  currentSlot.value = idx
  resetCarouselTimer()
}

function nextCarousel() {
  currentSlot.value = (currentSlot.value + 1) % 3
}

function resetCarouselTimer() {
  if (carouselTimer) clearInterval(carouselTimer)
  if (isMobilePortrait.value) carouselTimer = setInterval(nextCarousel, 4500)
}

// ── Sub-componente: un slot con su contenido ───────────────────────────────
const SlotItem = {
  props: { slot: Object, si: Number },
  setup(props) {
    return () => {
      const s = props.slot

      // Slot activo con pieza
      if (s?.active && s.pieces?.length) {
        const piece  = s.pieces[0]
        const inner  = renderPiece(piece, s.title)
        const caption = (s.title && piece.piece_type !== "text")
          ? h("div", { class: "ad-caption" }, s.title)
          : null

        if (s.cta_url) {
          return h("a", {
            href: s.cta_url, target: "_blank", rel: "noopener noreferrer",
            class: "slot-inner slot-link"
          }, [inner, caption])
        }
        return h("div", { class: "slot-inner" }, [inner, caption])
      }

      // Placeholder → sección #contacto
      return h("a", { href: "#contacto", class: "slot-inner slot-placeholder" }, [
        h("div", { class: "ph-bg" }),
        h("div", { class: "ph-content" }, [
          h("div", { class: "ph-icon-wrap" }, [
            h("i", { class: "bi bi-megaphone-fill ph-icon" })
          ]),
          h("div", { class: "ph-text" }, [
            h("span", { class: "ph-title" }, "¡Paute Aquí!"),
            h("span", { class: "ph-sub" }, "Llega a miles de asociados"),
          ]),
          h("span", { class: "ph-cta" }, "→ Solicitar espacio"),
        ]),
      ])
    }
  }
}

function renderPiece(piece, title) {
  const { piece_type, media_url, youtube_id, text_content } = piece
  if (piece_type === "image")
    return h("img", { src: media_url, alt: title || "Pauta", class: "slot-media", loading: "lazy" })
  if (piece_type === "video")
    return h("video", { src: media_url, autoplay: true, muted: true, loop: true, playsinline: true, preload: "metadata", class: "slot-media" })
  if (piece_type === "youtube")
    return h("div", { class: "slot-yt-wrap" }, [
      h("iframe", {
        src: `https://www.youtube.com/embed/${youtube_id}?autoplay=1&mute=1&loop=1&playlist=${youtube_id}&controls=0&rel=0`,
        frameborder: "0", allow: "autoplay; encrypted-media", allowfullscreen: true, class: "slot-yt"
      })
    ])
  if (piece_type === "text")
    return h("div", { class: "slot-text" }, [
      h("p", { class: "slot-text-title" }, title || ""),
      h("p", { class: "slot-text-body" }, text_content),
    ])
  return null
}

// ── Lifecycle ──────────────────────────────────────────────────────────────
let refreshTimer = null

onMounted(() => {
  checkOrientation()
  window.addEventListener("resize", checkOrientation)
  loadSlots()
  refreshTimer = setInterval(loadSlots, 5 * 60 * 1000)
  resetCarouselTimer()
})

onUnmounted(() => {
  window.removeEventListener("resize", checkOrientation)
  if (carouselTimer) clearInterval(carouselTimer)
  if (refreshTimer)  clearInterval(refreshTimer)
})
</script>

<style scoped>
/* ── Contenedor principal ── */
.ad-banner-wrap {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: row;
  gap: 4px;
  padding: 4px;
  box-sizing: border-box;
  background: #0f172a;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}

/* ── Slot ── */
.ad-slot {
  flex: 1;
  border-radius: 10px;
  overflow: hidden;
  position: relative;
}

.slot-inner {
  display: flex;
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
  text-decoration: none;
}

.slot-link { cursor: pointer; transition: opacity .2s; }
.slot-link:hover { opacity: .92; }

/* ── Media ── */
.slot-media   { width: 100%; height: 100%; object-fit: cover; display: block; }
.slot-yt-wrap { flex: 1; background: #000; }
.slot-yt      { width: 100%; height: 100%; border: none; display: block; }
.slot-text    { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 12px; gap: 6px; }
.slot-text-title { font-size: 13px; font-weight: 700; color: #fff; text-align: center; margin: 0; }
.slot-text-body  { font-size: 11px; color: rgba(255,255,255,.75); text-align: center; line-height: 1.5; margin: 0; }
.ad-caption {
  position: absolute; bottom: 0; left: 0; right: 0;
  background: linear-gradient(transparent,rgba(0,0,0,.7));
  color: #fff; font-size: 11px; font-weight: 600;
  padding: 20px 10px 8px; text-align: center;
}

/* ── Placeholder ── */
.slot-placeholder {
  cursor: pointer;
  transition: filter .2s;
  text-decoration: none;
}
.slot-placeholder:hover { filter: brightness(1.08); }

.ph-bg {
  position: absolute; inset: 0;
  background: linear-gradient(135deg, #2563eb 0%, #4f46e5 45%, #7c3aed 100%);
}
/* Círculos decorativos */
.ph-bg::before, .ph-bg::after {
  content: ""; position: absolute; border-radius: 50%;
  background: rgba(255,255,255,0.07);
}
.ph-bg::before { width: 120px; height: 120px; top: -30px; right: -20px; }
.ph-bg::after  { width: 80px;  height: 80px;  bottom: -15px; left: -10px; }

.ph-content {
  position: relative; z-index: 1;
  display: flex; align-items: center;
  width: 100%; height: 100%;
  gap: 12px; padding: 0 16px;
}

.ph-icon-wrap {
  flex-shrink: 0;
  width: 44px; height: 44px;
  background: rgba(255,255,255,0.15);
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
}
.ph-icon { font-size: 22px; color: #fbbf24; }

.ph-text {
  flex: 1; display: flex; flex-direction: column; gap: 3px; min-width: 0;
}
.ph-title { font-size: 15px; font-weight: 800; color: #fff; line-height: 1; }
.ph-sub   { font-size: 11px; color: rgba(255,255,255,.75); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.ph-cta {
  flex-shrink: 0;
  background: linear-gradient(90deg,#10b981,#0ea5e9);
  color: #fff; font-size: 11px; font-weight: 800;
  padding: 7px 14px; border-radius: 20px; white-space: nowrap;
}

/* ── Carrusel móvil ── */
.carousel-wrap {
  flex: 1; position: relative;
  display: flex; flex-direction: column;
}
.carousel-slot { flex: 1; }

.carousel-dots {
  position: absolute; bottom: 6px; left: 50%; transform: translateX(-50%);
  display: flex; gap: 5px; z-index: 10;
}
.c-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: rgba(255,255,255,.35); border: none; cursor: pointer;
  transition: background .2s, transform .2s; padding: 0;
}
.c-dot.active { background: #fff; transform: scale(1.2); }

/* ── Transición carrusel ── */
.ad-fade-enter-active, .ad-fade-leave-active { transition: opacity .3s; }
.ad-fade-enter-from, .ad-fade-leave-to       { opacity: 0; }

/* ── Responsive: reducir padding/gap en móvil ── */
@media (max-width: 767px) {
  .ad-banner-wrap { gap: 3px; padding: 3px; }
  .ad-slot        { border-radius: 7px; }
  .ph-content     { gap: 8px; padding: 0 10px; }
  .ph-icon-wrap   { width: 34px; height: 34px; border-radius: 9px; }
  .ph-icon        { font-size: 17px; }
  .ph-title       { font-size: 13px; }
  .ph-sub         { font-size: 10px; }
  .ph-cta         { font-size: 10px; padding: 5px 10px; }
  .ad-caption     { font-size: 9px; padding: 14px 8px 5px; }
}

@media (max-width: 420px) {
  .ph-title  { font-size: 12px; }
  .ph-cta    { display: none; }
}
</style>
