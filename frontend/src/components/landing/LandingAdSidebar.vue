<template>
  <aside class="landing-sidebar">
    <div class="ls-header">
      <i class="bi bi-megaphone-fill"></i>
      <span>Destacados</span>
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
            <div v-if="slot.title && slot.pieces[0]?.piece_type !== 'text'" class="ls-caption">{{ slot.title }}</div>
          </a>
          <div v-else class="ls-ad-link">
            <component :is="renderPiece(slot.pieces[0])" />
            <div v-if="slot.title && slot.pieces[0]?.piece_type !== 'text'" class="ls-caption">{{ slot.title }}</div>
          </div>
        </template>

        <!-- Placeholder "Paute Aquí" — IDs únicos por slot -->
        <a href="https://easyposweb.com/register" class="ls-placeholder-link" v-else>
          <svg viewBox="0 0 180 200" xmlns="http://www.w3.org/2000/svg" class="ls-placeholder-svg">
            <defs>
              <!-- Fondo: azul vibrante → púrpura -->
              <linearGradient :id="`lpBg${si}`" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%"   stop-color="#2563eb"/>
                <stop offset="50%"  stop-color="#4f46e5"/>
                <stop offset="100%" stop-color="#7c3aed"/>
              </linearGradient>
              <!-- Acento: ámbar → naranja -->
              <linearGradient :id="`lpAc${si}`" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%"   stop-color="#f59e0b"/>
                <stop offset="100%" stop-color="#ef4444"/>
              </linearGradient>
              <!-- Botón: verde vibrante -->
              <linearGradient :id="`lpBtn${si}`" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%"   stop-color="#10b981"/>
                <stop offset="100%" stop-color="#0ea5e9"/>
              </linearGradient>
            </defs>
            <!-- Fondo principal -->
            <rect width="180" height="200" :fill="`url(#lpBg${si})`" rx="10"/>
            <!-- Patrón decorativo: círculos difusos -->
            <circle cx="150" cy="30"  r="40" fill="rgba(255,255,255,0.07)"/>
            <circle cx="20"  cy="170" r="35" fill="rgba(255,255,255,0.06)"/>
            <circle cx="90"  cy="100" r="60" fill="rgba(255,255,255,0.04)"/>
            <!-- Franja superior ámbar -->
            <rect x="0" y="0" width="180" height="5" :fill="`url(#lpAc${si})`" rx="2"/>
            <!-- Badge "PUBLI" -->
            <rect x="10" y="12" width="40" height="14" rx="7" fill="rgba(255,255,255,0.18)"/>
            <text x="30" y="22" text-anchor="middle" font-family="Arial,sans-serif" font-size="7" font-weight="800" fill="#fbbf24" letter-spacing="0.8">PUBLI</text>
            <!-- Icono megáfono (más grande y lleno) -->
            <g transform="translate(62,32) scale(1.6)" fill="rgba(255,255,255,0.95)">
              <path d="M3 9v6h4l5 5V4L7 9H3z"/>
              <path d="M16 8.5c1 .7 1.5 1.7 1.5 3s-.5 2.3-1.5 3" fill="none" stroke="rgba(255,255,255,0.95)" stroke-width="1.8" stroke-linecap="round"/>
            </g>
            <!-- Estrella decorativa -->
            <text x="142" y="72" font-family="Arial,sans-serif" font-size="16" fill="rgba(251,191,36,0.6)">✦</text>
            <!-- Título principal -->
            <text x="90" y="105" text-anchor="middle" font-family="Arial,sans-serif" font-size="17" font-weight="800" fill="#ffffff">¡Paute Aquí!</text>
            <!-- Subtítulo -->
            <text x="90" y="122" text-anchor="middle" font-family="Arial,sans-serif" font-size="9" fill="rgba(255,255,255,0.85)">Llega a miles de asociados</text>
            <text x="90" y="135" text-anchor="middle" font-family="Arial,sans-serif" font-size="9" fill="rgba(255,255,255,0.85)">en todo el país</text>
            <!-- Separador decorativo -->
            <rect x="50" y="143" width="80" height="1.5" :fill="`url(#lpAc${si})`" rx="1" opacity="0.7"/>
            <!-- Botón CTA -->
            <rect x="24" y="154" width="132" height="28" rx="14" :fill="`url(#lpBtn${si})`"/>
            <rect x="24" y="154" width="132" height="28" rx="14" fill="rgba(255,255,255,0.12)"/>
            <text x="90" y="172" text-anchor="middle" font-family="Arial,sans-serif" font-size="10" font-weight="800" fill="#ffffff">→ Solicitar espacio</text>
            <!-- Franja inferior marca -->
            <rect x="0" y="191" width="180" height="9" fill="rgba(0,0,0,0.25)" rx="2"/>
            <text x="90" y="198" text-anchor="middle" font-family="Arial,sans-serif" font-size="6.5" fill="rgba(255,255,255,0.5)" letter-spacing="0.5">EasyPosWeb.com</text>
          </svg>
        </a>

      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, onMounted, onUnmounted, h } from "vue"
import api from "@/services/apis"

const slots = ref([
  { slot: 1, active: false, pieces: [] },
  { slot: 2, active: false, pieces: [] },
  { slot: 3, active: false, pieces: [] },
])

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

async function loadSlots() {
  try {
    const res = await api.get("/ads/active-slots")
    if (Array.isArray(res.data)) slots.value = res.data
  } catch {}
}

let refreshTimer = null
onMounted(() => {
  loadSlots()
  refreshTimer = setInterval(loadSlots, 5 * 60 * 1000)
})
onUnmounted(() => { if (refreshTimer) clearInterval(refreshTimer) })
</script>

<style scoped>
/* ── Desktop: columna fija a la derecha (controlado por parent .landing-fixed-sidebar) ── */
.landing-sidebar {
  width: 190px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ls-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(255,255,255,0.55);
  padding: 0 4px 6px;
  border-bottom: 1px solid rgba(255,255,255,0.12);
}
.ls-header .bi { color: #f59e0b; font-size: 13px; }

.ls-slots { display: flex; flex-direction: column; gap: 8px; }

.ls-slot {
  border-radius: 12px;
  overflow: hidden;
  background: rgba(15,23,42,0.75);
  height: 200px;
  position: relative;
  box-shadow: 0 4px 16px rgba(0,0,0,0.4);
}

.ls-ad-link, .ls-placeholder-link {
  display: flex;
  flex-direction: column;
  height: 100%;
  text-decoration: none;
  position: relative;
  overflow: hidden;
  transition: opacity .2s;
}
.ls-ad-link:hover, .ls-placeholder-link:hover { opacity: .88; }

.ls-media      { width: 100%; height: 100%; object-fit: cover; display: block; }
.ls-yt-wrap    { flex: 1; background: #000; height: 100%; }
.ls-yt         { width: 100%; height: 100%; border: none; display: block; }
.ls-text-wrap  {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center; padding: 12px; gap: 6px;
  background: linear-gradient(135deg,#1e3a5f,#0d4f3c); height: 100%;
}
.ls-text-title { font-size: 13px; font-weight: 700; color: #fff; text-align: center; margin: 0; }
.ls-caption {
  position: absolute; bottom: 0; left: 0; right: 0;
  background: linear-gradient(transparent,rgba(0,0,0,.65));
  color: #fff; font-size: 10px; font-weight: 600;
  padding: 14px 8px 6px; text-align: center;
}
.ls-placeholder-svg { width: 100%; height: 100%; display: block; }

/* ── Móvil landscape: fila horizontal en la base (visible en landscape ≥480px) ── */
@media (max-width: 1199px) and (orientation: landscape) {
  .landing-sidebar {
    width: auto;
    flex-direction: row;
    gap: 6px;
    padding: 0 4px;
  }
  .ls-header { display: none; }
  .ls-slots {
    flex-direction: row;
    gap: 6px;
    width: 100%;
  }
  .ls-slot {
    flex: 1;
    height: 110px;
    border-radius: 8px;
  }
  .ls-caption { font-size: 8px; padding: 8px 4px 4px; }
}

/* ── Móvil portrait: ocultar (controlled by parent) ── */
</style>
