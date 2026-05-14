<template>
  <!-- Pestaña de reapertura (visible cuando está colapsado) -->
  <button
    v-if="dismissed"
    class="ads-tab"
    @click="expand"
    title="Ver publicidad"
    aria-label="Abrir panel publicitario"
  >
    <i class="bi bi-megaphone-fill"></i>
    <span class="ads-tab-label">Pautas</span>
  </button>

  <!-- Panel lateral -->
  <aside
    v-show="!dismissed"
    class="landing-sidebar"
    :class="{ 'ls-visible': !dismissed }"
  >
    <div class="ls-header">
      <span class="ls-header-title">
        <i class="bi bi-megaphone-fill"></i>
        <span class="ls-header-text">Destacados</span>
      </span>
      <button class="ls-close" @click="dismiss" title="Ocultar" aria-label="Cerrar panel">
        <i class="bi bi-x-lg"></i>
        <span class="ls-close-label">Cerrar</span>
      </button>
    </div>

    <div class="ls-slots">
      <div v-for="(slot, si) in slots" :key="slot.slot" class="ls-slot">

        <!-- Slot activo -->
        <template v-if="slot.active && slot.pieces?.length">
          <a v-if="slot.cta_url"
            :href="slot.cta_url"
            target="_blank"
            rel="noopener noreferrer"
            class="ls-ad-link"
          >
            <component :is="renderPiece(slot.pieces[0])" />
            <div v-if="slot.title && slot.pieces[0]?.piece_type !== 'text'" class="ls-caption">
              {{ slot.title }}
            </div>
          </a>
          <div v-else class="ls-ad-link">
            <component :is="renderPiece(slot.pieces[0])" />
            <div v-if="slot.title && slot.pieces[0]?.piece_type !== 'text'" class="ls-caption">
              {{ slot.title }}
            </div>
          </div>
        </template>

        <!-- Placeholder: clic cierra el sidebar (no navega) -->
        <div class="ls-placeholder-link" @click="dismiss" title="Ocultar panel" v-else>
          <svg viewBox="0 0 180 200" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg" class="ls-placeholder-svg">
            <defs>
              <linearGradient :id="`lpBg${si}`" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%"   stop-color="#2563eb"/>
                <stop offset="50%"  stop-color="#4f46e5"/>
                <stop offset="100%" stop-color="#7c3aed"/>
              </linearGradient>
              <linearGradient :id="`lpAc${si}`" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%"   stop-color="#f59e0b"/>
                <stop offset="100%" stop-color="#ef4444"/>
              </linearGradient>
              <linearGradient :id="`lpBtn${si}`" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%"   stop-color="#10b981"/>
                <stop offset="100%" stop-color="#0ea5e9"/>
              </linearGradient>
            </defs>
            <rect width="180" height="200" :fill="`url(#lpBg${si})`" rx="10"/>
            <circle cx="150" cy="30"  r="40" fill="rgba(255,255,255,0.07)"/>
            <circle cx="20"  cy="170" r="35" fill="rgba(255,255,255,0.06)"/>
            <rect x="0" y="0" width="180" height="5" :fill="`url(#lpAc${si})`" rx="2"/>
            <rect x="10" y="12" width="40" height="14" rx="7" fill="rgba(255,255,255,0.18)"/>
            <text x="30" y="22" text-anchor="middle" font-family="Arial,sans-serif" font-size="7" font-weight="800" fill="#fbbf24" letter-spacing="0.8">PUBLI</text>
            <g transform="translate(62,32) scale(1.6)" fill="rgba(255,255,255,0.95)">
              <path d="M3 9v6h4l5 5V4L7 9H3z"/>
              <path d="M16 8.5c1 .7 1.5 1.7 1.5 3s-.5 2.3-1.5 3" fill="none" stroke="rgba(255,255,255,0.95)" stroke-width="1.8" stroke-linecap="round"/>
            </g>
            <text x="142" y="72" font-family="Arial,sans-serif" font-size="16" fill="rgba(251,191,36,0.6)">✦</text>
            <text x="90" y="105" text-anchor="middle" font-family="Arial,sans-serif" font-size="17" font-weight="800" fill="#ffffff">¡Paute Aquí!</text>
            <text x="90" y="122" text-anchor="middle" font-family="Arial,sans-serif" font-size="9"  fill="rgba(255,255,255,0.85)">Llega a miles de asociados</text>
            <text x="90" y="135" text-anchor="middle" font-family="Arial,sans-serif" font-size="9"  fill="rgba(255,255,255,0.85)">en todo el país</text>
            <rect x="50" y="143" width="80" height="1.5" :fill="`url(#lpAc${si})`" rx="1" opacity="0.7"/>
            <rect x="24" y="154" width="132" height="28" rx="14" :fill="`url(#lpBtn${si})`"/>
            <rect x="24" y="154" width="132" height="28" rx="14" fill="rgba(255,255,255,0.12)"/>
            <text x="90" y="172" text-anchor="middle" font-family="Arial,sans-serif" font-size="10" font-weight="800" fill="#ffffff">→ Solicitar espacio</text>
            <rect x="0" y="191" width="180" height="9" fill="rgba(0,0,0,0.25)" rx="2"/>
            <text x="90" y="198.5" text-anchor="middle" font-family="Arial,sans-serif" font-size="6.5" fill="rgba(255,255,255,0.5)" letter-spacing="0.5">EasyPosWeb.com</text>
          </svg>
        </div>

      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, onMounted, onUnmounted, h } from "vue"
import api from "@/services/apis"
import { sidebarDismissed as dismissed, initLandingSidebar, dismissSidebar as dismiss, expandSidebar as expand } from "@/composables/useLandingSidebar"

const slots = ref([
  { slot: 1, active: false, pieces: [] },
  { slot: 2, active: false, pieces: [] },
  { slot: 3, active: false, pieces: [] },
])

// ── Render de pieza ────────────────────────────────────────────────────────
function renderPiece(piece) {
  if (!piece) return null
  const { piece_type, media_url, youtube_id, text_content } = piece
  if (piece_type === "image")
    return h("img", { src: media_url, alt: "Pauta", class: "ls-media", loading: "lazy" })
  if (piece_type === "video")
    return h("video", { src: media_url, autoplay: true, muted: true, loop: true, playsinline: true, preload: "metadata", class: "ls-media" })
  if (piece_type === "youtube")
    return h("div", { class: "ls-yt-wrap" }, [
      h("iframe", {
        src: `https://www.youtube.com/embed/${youtube_id}?autoplay=0&mute=1&loop=1&playlist=${youtube_id}&rel=0`,
        frameborder: "0", allow: "encrypted-media", allowfullscreen: true, loading: "lazy", class: "ls-yt"
      })
    ])
  if (piece_type === "text")
    return h("div", { class: "ls-text-wrap" }, [
      h("p", { class: "ls-text-title" }, text_content)
    ])
  return null
}

// ── Cargar slots ───────────────────────────────────────────────────────────
async function loadSlots() {
  try {
    const res = await api.get("/ads/active-slots")
    if (Array.isArray(res.data)) slots.value = res.data
  } catch {}
}

let refreshTimer = null

onMounted(() => {
  initLandingSidebar()
  loadSlots()
  refreshTimer = setInterval(loadSlots, 5 * 60 * 1000)
})
onUnmounted(() => { if (refreshTimer) clearInterval(refreshTimer) })
</script>

<style scoped>
/* ═══════════════════════════════════════════════
   PANEL LATERAL — posición fija, proporcional
═══════════════════════════════════════════════ */
.landing-sidebar {
  position: fixed;
  top: 68px;                        /* debajo del navbar */
  right: 0;
  bottom: 0;
  width: 190px;
  background: rgba(10, 14, 26, 0.96);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
  z-index: 80;
  box-shadow: -4px 0 20px rgba(0,0,0,0.4);
  border-left: 1px solid rgba(255,255,255,0.1);
  /* Animación de entrada desde la derecha */
  transform: translateX(0);
  transition: transform 0.3s cubic-bezier(0.4,0,0.2,1);
  overflow-y: auto;
  scrollbar-width: none;
  padding-bottom: 60px;             /* espacio para footer landing */
}
.landing-sidebar::-webkit-scrollbar { display: none; }

/* ── Header ── */
.ls-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: rgba(0,0,0,0.25);
  border-bottom: 1px solid rgba(255,255,255,0.09);
  flex-shrink: 0;
}
.ls-header-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(255,255,255,0.65);
  display: flex;
  align-items: center;
  gap: 6px;
}
.ls-header-title .bi { color: #f59e0b; font-size: 13px; }
.ls-close {
  background: rgba(239,68,68,0.15);
  border: 1px solid rgba(239,68,68,0.3);
  color: rgba(255,255,255,0.75);
  font-size: 11px;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 6px;
  line-height: 1;
  display: flex;
  align-items: center;
  gap: 3px;
  flex-shrink: 0;
  transition: color .15s, background .15s;
}
.ls-close:hover { color: #fff; background: rgba(239,68,68,0.35); }
.ls-close-label { font-size: 9px; font-weight: 700; letter-spacing: 0.3px; }

/* ── Slots ── */
.ls-slots {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px;
  flex: 1;
}
.ls-slot {
  border-radius: 10px;
  overflow: hidden;
  background: rgba(15,23,42,0.7);
  flex: 1;
  min-height: 100px;
  position: relative;
}

.ls-ad-link, .ls-placeholder-link {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 100px;
  text-decoration: none;
  position: relative;
  overflow: hidden;
  transition: opacity .2s;
}
.ls-ad-link:hover, .ls-placeholder-link:hover { opacity: .88; }

.ls-media      { width: 100%; height: 100%; object-fit: cover; display: block; }
.ls-yt-wrap    { flex: 1; background: #000; }
.ls-yt         { width: 100%; height: 100%; border: none; display: block; }
.ls-text-wrap  {
  flex: 1; display: flex; align-items: center; justify-content: center;
  padding: 10px; background: linear-gradient(135deg,#1e3a5f,#0d4f3c);
}
.ls-text-title { font-size: 12px; font-weight: 700; color: #fff; text-align: center; margin: 0; }
.ls-caption {
  position: absolute; bottom: 0; left: 0; right: 0;
  background: linear-gradient(transparent,rgba(0,0,0,.7));
  color: #fff; font-size: 9px; font-weight: 600;
  padding: 12px 6px 5px; text-align: center;
}
.ls-placeholder-svg { width: 100%; height: 100%; display: block; }

/* ═══════════════════════════════════════════════
   PESTAÑA lateral (cuando está colapsado)
═══════════════════════════════════════════════ */
.ads-tab {
  position: fixed;
  top: 50%;
  right: 0;
  transform: translateY(-50%);
  z-index: 81;
  background: linear-gradient(180deg, #4f46e5, #7c3aed);
  color: #fff;
  border: none;
  border-radius: 8px 0 0 8px;
  padding: 12px 6px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  box-shadow: -3px 0 12px rgba(0,0,0,0.35);
  transition: background .2s, transform .2s;
}
.ads-tab:hover {
  background: linear-gradient(180deg, #6366f1, #9333ea);
  transform: translateY(-50%) translateX(-2px);
}
.ads-tab .bi { font-size: 16px; }
.ads-tab-label {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  writing-mode: vertical-lr;
  transform: rotate(180deg);
  opacity: .85;
}

/* ═══════════════════════════════════════════════
   RESPONSIVE
═══════════════════════════════════════════════ */

/* Tablet (768px – 1199px): un poco más angosto */
@media (max-width: 1199px) and (min-width: 768px) {
  .landing-sidebar { width: 155px; }
}

/* Móvil landscape (<768px landscape): más angosto */
@media (max-width: 767px) and (orientation: landscape) {
  .landing-sidebar {
    width: 110px;
    top: 54px;
    padding-bottom: 0;
    overflow: hidden;
  }
  .ls-slots { gap: 4px; padding: 4px; }
  .ls-slot  { min-height: 0; border-radius: 6px; }
}

/* Móvil portrait (<768px portrait) */
@media (max-width: 767px) and (orientation: portrait) {
  .landing-sidebar {
    width: 130px;        /* más ancho: mejor proporción de cada slot */
    top: 68px;
    padding-bottom: 0;
    overflow: hidden;
  }
  .ls-slots  { gap: 5px; padding: 5px; }
  .ls-slot   { min-height: 0; border-radius: 8px; }
  .ls-header { padding: 6px 10px; }
  .ls-header-text      { display: none; }
  .ls-header-title .bi { font-size: 14px; }
  .ls-close-label      { display: none; }
  .ls-caption          { font-size: 9px; padding: 10px 6px 5px; }
}

/* Pantallas muy pequeñas portrait (<420px) */
@media (max-width: 420px) and (orientation: portrait) {
  .landing-sidebar { width: 115px; top: 68px; }
  .ls-text-title   { font-size: 9px; }
  .ls-header       { padding: 5px 8px; }
  .ls-slots        { gap: 4px; padding: 4px; }
}
</style>
