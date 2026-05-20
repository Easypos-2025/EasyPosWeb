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
            <!-- Label: Publicidad -->
            <span class="ad-label">Publicidad</span>
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
            <!-- Iconos redes sociales del anunciante -->
            <div v-if="slotHasSocial(slot)" class="slot-social-icons">
              <a v-if="slot.social_instagram" :href="slot.social_instagram" target="_blank" rel="noopener" @click.stop class="slot-soc-btn soc-instagram" title="Instagram"><i class="bi bi-instagram"></i></a>
              <a v-if="slot.social_tiktok" :href="slot.social_tiktok" target="_blank" rel="noopener" @click.stop class="slot-soc-btn soc-tiktok" title="TikTok"><i class="bi bi-tiktok"></i></a>
              <a v-if="slot.social_facebook" :href="slot.social_facebook" target="_blank" rel="noopener" @click.stop class="slot-soc-btn soc-facebook" title="Facebook"><i class="bi bi-facebook"></i></a>
              <a v-if="slot.social_youtube_channel" :href="slot.social_youtube_channel" target="_blank" rel="noopener" @click.stop class="slot-soc-btn soc-youtube" title="YouTube"><i class="bi bi-youtube"></i></a>
              <a v-if="slot.social_website" :href="slot.social_website" target="_blank" rel="noopener" @click.stop class="slot-soc-btn soc-website" title="Sitio web"><i class="bi bi-globe2"></i></a>
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
                <!-- Label: Publicidad -->
                <span class="ad-label">Publicidad</span>
                <button
                  v-if="isMediaPiece(currentSlotPiece(slots[currentSlot], currentSlot))"
                  class="btn-audio"
                  @click.prevent.stop="toggleAudio(currentSlot)"
                  :title="slotMuted[currentSlot] ? 'Activar audio' : 'Silenciar'"
                >
                  <i :class="slotMuted[currentSlot] ? 'bi bi-volume-mute-fill' : 'bi bi-volume-up-fill'"></i>
                </button>
                <!-- Iconos redes sociales -->
                <div v-if="slotHasSocial(slots[currentSlot])" class="slot-social-icons">
                  <a v-if="slots[currentSlot].social_instagram" :href="slots[currentSlot].social_instagram" target="_blank" rel="noopener" @click.stop class="slot-soc-btn soc-instagram" title="Instagram"><i class="bi bi-instagram"></i></a>
                  <a v-if="slots[currentSlot].social_tiktok" :href="slots[currentSlot].social_tiktok" target="_blank" rel="noopener" @click.stop class="slot-soc-btn soc-tiktok" title="TikTok"><i class="bi bi-tiktok"></i></a>
                  <a v-if="slots[currentSlot].social_facebook" :href="slots[currentSlot].social_facebook" target="_blank" rel="noopener" @click.stop class="slot-soc-btn soc-facebook" title="Facebook"><i class="bi bi-facebook"></i></a>
                  <a v-if="slots[currentSlot].social_youtube_channel" :href="slots[currentSlot].social_youtube_channel" target="_blank" rel="noopener" @click.stop class="slot-soc-btn soc-youtube" title="YouTube"><i class="bi bi-youtube"></i></a>
                  <a v-if="slots[currentSlot].social_website" :href="slots[currentSlot].social_website" target="_blank" rel="noopener" @click.stop class="slot-soc-btn soc-website" title="Sitio web"><i class="bi bi-globe2"></i></a>
                </div>
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

const SOCIAL_ICONS = {
  youtube: "bi-youtube", instagram: "bi-instagram", tiktok: "bi-tiktok",
  facebook: "bi-facebook", twitter: "bi-twitter-x", social: "bi-play-circle",
}
const SOCIAL_COLORS = {
  youtube: "#ff0000", instagram: "#e1306c", tiktok: "#010101",
  facebook: "#1877f2", twitter: "#1da1f2", social: "#6b7280",
}

const SlotPiece = defineComponent({
  name: "SlotPiece",
  props: { piece: Object, title: String, muted: { type: Boolean, default: true } },
  setup(props) {
    const ytSrc = computed(() => {
      if (!props.piece?.youtube_id) return ""
      return `https://www.youtube.com/embed/${props.piece.youtube_id}?autoplay=1&controls=0&rel=0&enablejsapi=1&mute=1`
    })
    return { ytSrc }
  },
  render() {
    const p = this.piece
    if (!p) return null
    const { piece_type, media_url, text_content, social_platform } = p

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
          key: `yt-${p.youtube_id}`,
          src: this.ytSrc, frameborder: "0",
          allow: "autoplay; encrypted-media", allowfullscreen: true, class: "slot-yt"
        })
      ])

    if (piece_type === "social") {
      const plat = social_platform || "social"
      const icon = SOCIAL_ICONS[plat] || "bi-play-circle"
      const color = SOCIAL_COLORS[plat] || "#6b7280"
      return h("a", { href: media_url, target: "_blank", rel: "noopener noreferrer", class: "slot-social-card" }, [
        h("div", { class: "slot-social-bg", style: `background:${color}18` }),
        h("div", { class: "slot-social-content" }, [
          h("i", { class: `bi ${icon} slot-social-icon`, style: `color:${color}` }),
          h("span", { class: "slot-social-title" }, this.title || ""),
          h("span", { class: "slot-social-cta" }, "Ver publicación →"),
        ])
      ])
    }

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
import { ref, watch, nextTick, onMounted, onUnmounted } from "vue"
import api from "@/services/apis"

// ── Orientación ────────────────────────────────────────────────────────────
const isMobilePortrait = ref(false)
function checkOrientation() {
  isMobilePortrait.value = window.innerWidth < 560 && window.innerHeight > window.innerWidth
}

// ── Audio por slot ─────────────────────────────────────────────────────────
const slotMuted = ref([true, true, true])
function toggleAudio(si) {
  slotMuted.value[si] = !slotMuted.value[si]
  let iframe = null
  if (isMobilePortrait.value) {
    iframe = document.querySelector('.carousel-wrap .ad-slot iframe')
  } else {
    const adSlots = document.querySelectorAll('.ad-banner-wrap > .ad-slot')
    iframe = adSlots[si]?.querySelector('iframe')
  }
  if (iframe?.contentWindow) {
    const cmd = slotMuted.value[si] ? 'mute' : 'unMute'
    iframe.contentWindow.postMessage(JSON.stringify({ event: 'command', func: cmd, args: '' }), 'https://www.youtube.com')
  }
}
function isMediaPiece(piece) {
  return piece?.piece_type === "video" || piece?.piece_type === "youtube"
}
function slotHasSocial(slot) {
  return slot?.active && (slot.social_instagram || slot.social_tiktok || slot.social_facebook || slot.social_youtube_channel || slot.social_website)
}

// ── Datos ──────────────────────────────────────────────────────────────────
const slots        = ref([
  { slot: 1, active: false, pieces: [] },
  { slot: 2, active: false, pieces: [] },
  { slot: 3, active: false, pieces: [] },
])
const slotPieceIdx  = ref([0, 0, 0])
const currentSlot   = ref(0)
const slotTimers    = [null, null, null]
const pauseCleanups = [null, null, null]

function cleanPauseCleanup(si) {
  if (pauseCleanups[si]) { pauseCleanups[si](); pauseCleanups[si] = null }
}

// Avanza la pieza del slot si (extrae la lógica del timeout para reusar en pausa)
function advancePiece(si) {
  cleanPauseCleanup(si)
  clearTimeout(slotTimers[si])
  const len       = slots.value[si]?.pieces?.length ?? 1
  const nextPiece = len > 1 ? (slotPieceIdx.value[si] + 1) % len : 0
  slotPieceIdx.value[si] = nextPiece

  if (isMobilePortrait.value) {
    if (nextPiece === 0) {
      const nextSi = (si + 1) % 3
      currentSlot.value = nextSi
      scheduleSlot(nextSi)
    } else {
      scheduleSlot(si)
    }
  } else {
    scheduleSlot(si)
  }
}

function attachPauseListener(si, piece) {
  if (piece.piece_type === "video") {
    nextTick(() => {
      let video = null
      if (isMobilePortrait.value) {
        video = document.querySelector('.carousel-wrap .ad-slot video')
      } else {
        video = document.querySelectorAll('.ad-banner-wrap > .ad-slot')[si]?.querySelector('video')
      }
      if (!video) return
      const onPause = () => { if (!video.ended) advancePiece(si) }
      video.addEventListener('pause', onPause)
      pauseCleanups[si] = () => video.removeEventListener('pause', onPause)
    })
  } else if (piece.piece_type === "youtube") {
    const onMsg = (evt) => {
      if (evt.origin !== 'https://www.youtube.com') return
      let iframe = null
      if (isMobilePortrait.value) {
        iframe = document.querySelector('.carousel-wrap .ad-slot iframe')
      } else {
        iframe = document.querySelectorAll('.ad-banner-wrap > .ad-slot')[si]?.querySelector('iframe')
      }
      if (evt.source !== iframe?.contentWindow) return
      try {
        const d = JSON.parse(evt.data)
        // playerState 0 = ended (avanzar); ignorar 2 = paused (puede dispararse al cargar)
        if (d.event === 'infoDelivery' && d.info?.playerState === 0) advancePiece(si)
      } catch {}
    }
    window.addEventListener('message', onMsg)
    pauseCleanups[si] = () => window.removeEventListener('message', onMsg)
  }
}

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
  // Timeout de fallback si el evento 'ended' no llega (proxy, iframe restrictions)
  if (piece.piece_type === "youtube") return isMobilePortrait.value ? 20_000 : 3 * 60 * 1000
  return 8_000   // imagen / texto
}

function clearSlotTimers() {
  slotTimers.forEach((_, i) => { clearTimeout(slotTimers[i]); slotTimers[i] = null; cleanPauseCleanup(i) })
}

// ── Scheduling: respeta duración + detecta pausa para avanzar anticipadamente ─
async function scheduleSlot(si) {
  cleanPauseCleanup(si)
  const slot = slots.value[si]
  if (!slot?.pieces?.length) {
    // Slot vacío en móvil: mostrar placeholder 5s y luego avanzar
    if (isMobilePortrait.value) {
      slotTimers[si] = setTimeout(() => advancePiece(si), 5_000)
    }
    return
  }
  if (slot.pieces.length <= 1 && !isMobilePortrait.value) return  // 1 pieza sin rotación en desktop

  const piece    = slot.pieces[slotPieceIdx.value[si]]
  const duration = await pieceDuration(piece)
  slotTimers[si] = setTimeout(() => advancePiece(si), duration)
  attachPauseListener(si, piece)
}

function startTimers() {
  clearSlotTimers()
  if (isMobilePortrait.value) {
    currentSlot.value = 0
    scheduleSlot(0)
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
    if (!Array.isArray(res.data)) return
    // Solo reiniciar rotación si cambiaron los ads asignados a los slots
    const changed = res.data.some((s, i) =>
      s.ad_id !== slots.value[i]?.ad_id ||
      s.pieces?.length !== slots.value[i]?.pieces?.length
    )
    slots.value = res.data
    if (changed) {
      slotPieceIdx.value = [0, 0, 0]
      currentSlot.value  = 0
      startTimers()
    }
  } catch {}
}

let refreshTimer = null

function onAdsRefresh() { loadSlots() }

onMounted(() => {
  checkOrientation()
  window.addEventListener("resize", checkOrientation)
  window.addEventListener("ads-refresh", onAdsRefresh)
  loadSlots()
  refreshTimer = setInterval(loadSlots, 5 * 60 * 1000)
})

onUnmounted(() => {
  window.removeEventListener("resize", checkOrientation)
  window.removeEventListener("ads-refresh", onAdsRefresh)
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

/* ── Label Publicidad (top-right) ── */
.ad-label {
  position: absolute; top: 7px; right: 7px; z-index: 10;
  font-size: 9px; font-weight: 700; letter-spacing: .5px;
  text-transform: uppercase; color: rgba(255,255,255,.75);
  background: rgba(0,0,0,.45); backdrop-filter: blur(4px);
  border: 1px solid rgba(255,255,255,.15);
  border-radius: 4px; padding: 2px 6px;
  pointer-events: none; user-select: none;
}

/* ── Iconos redes sociales del anunciante ── */
.slot-social-icons {
  position: absolute; top: 8px; left: 8px; z-index: 10;
  display: flex; flex-direction: column; gap: 5px;
}
.slot-soc-btn {
  width: 28px; height: 28px; border-radius: 7px;
  border: none; color: #fff; font-size: 14px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  text-decoration: none; transition: transform .15s, filter .15s;
  box-shadow: 0 2px 6px rgba(0,0,0,.35);
}
.slot-soc-btn:hover { transform: scale(1.15); filter: brightness(1.1); }

/* Colores reales de cada red social */
.soc-instagram {
  background: radial-gradient(circle at 30% 107%, #fdf497 0%, #fdf497 5%, #fd5949 45%, #d6249f 60%, #285AEB 90%);
}
.soc-tiktok    { background: #010101; }
.soc-tiktok i  { background: linear-gradient(135deg, #69c9d0, #ee1d52); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.soc-facebook  { background: #1877f2; }
.soc-youtube   { background: #ff0000; }
.soc-website   { background: #374151; }

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

/* Pieza tipo social (Instagram, TikTok, etc.) */
.slot-social-card {
  flex: 1; width: 100%; height: 100%;
  display: flex; position: relative;
  text-decoration: none; cursor: pointer;
}
.slot-social-bg { position: absolute; inset: 0; }
.slot-social-content {
  position: relative; z-index: 1;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  width: 100%; height: 100%; gap: 8px; padding: 12px;
}
.slot-social-icon  { font-size: 36px; }
.slot-social-title { font-size: 13px; font-weight: 700; color: #fff; text-align: center; }
.slot-social-cta   { font-size: 11px; color: rgba(255,255,255,.8); }
</style>
