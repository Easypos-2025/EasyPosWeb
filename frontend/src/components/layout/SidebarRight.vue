<template>
  <aside class="sidebar-right">

    <div class="sr-header">
      <span class="sr-title">
        <i class="bi bi-megaphone-fill"></i>
        Panel
      </span>
      <button class="btn-sr-close" @click="emit('close')" title="Cerrar panel">
        <i class="bi bi-x-lg"></i>
      </button>
    </div>

    <div class="sr-slots">
      <div v-for="(slot, si) in slots" :key="slot.slot" class="ad-slot">

        <!-- Slot activo con pieza -->
        <template v-if="slot.active && slot.pieces?.length">
          <!-- CON link: solo href válido, nunca undefined -->
          <a v-if="slot.cta_url"
            :href="slot.cta_url"
            target="_blank"
            rel="noopener noreferrer"
            class="ad-link"
          >
            <SlotContent :slot="slot" />
          </a>
          <!-- SIN link -->
          <div v-else class="ad-link">
            <SlotContent :slot="slot" />
          </div>
        </template>

        <!-- Placeholder "Paute Aquí" — IDs únicos por slot -->
        <div v-else class="ad-placeholder">
          <svg viewBox="0 0 160 200" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg" class="placeholder-svg">
            <defs>
              <linearGradient :id="`pgBg${si}`" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%"   stop-color="#2563eb"/>
                <stop offset="50%"  stop-color="#4f46e5"/>
                <stop offset="100%" stop-color="#7c3aed"/>
              </linearGradient>
              <linearGradient :id="`pgAc${si}`" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%"   stop-color="#f59e0b"/>
                <stop offset="100%" stop-color="#ef4444"/>
              </linearGradient>
              <linearGradient :id="`pgBtn${si}`" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%"   stop-color="#10b981"/>
                <stop offset="100%" stop-color="#0ea5e9"/>
              </linearGradient>
            </defs>
            <rect width="160" height="200" :fill="`url(#pgBg${si})`" rx="10"/>
            <circle cx="135" cy="28"  r="35" fill="rgba(255,255,255,0.07)"/>
            <circle cx="18"  cy="165" r="30" fill="rgba(255,255,255,0.06)"/>
            <rect x="0" y="0" width="160" height="5" :fill="`url(#pgAc${si})`" rx="2"/>
            <rect x="8" y="12" width="38" height="13" rx="6" fill="rgba(255,255,255,0.18)"/>
            <text x="27" y="21.5" text-anchor="middle" font-family="Arial,sans-serif" font-size="6.5" font-weight="800" fill="#fbbf24" letter-spacing="0.8">PUBLI</text>
            <g transform="translate(52,30) scale(1.5)" fill="rgba(255,255,255,0.95)">
              <path d="M3 9v6h4l5 5V4L7 9H3z"/>
              <path d="M16 8.5c1 .7 1.5 1.7 1.5 3s-.5 2.3-1.5 3" fill="none" stroke="rgba(255,255,255,0.95)" stroke-width="1.8" stroke-linecap="round"/>
            </g>
            <text x="130" y="70" font-family="Arial,sans-serif" font-size="14" fill="rgba(251,191,36,0.55)">✦</text>
            <text x="80" y="106" text-anchor="middle" font-family="Arial,sans-serif" font-size="15" font-weight="800" fill="#ffffff">¡Paute Aquí!</text>
            <text x="80" y="122" text-anchor="middle" font-family="Arial,sans-serif" font-size="8" fill="rgba(255,255,255,0.88)">Llega a miles de</text>
            <text x="80" y="134" text-anchor="middle" font-family="Arial,sans-serif" font-size="8" fill="rgba(255,255,255,0.88)">asociados en el país</text>
            <rect x="40" y="142" width="80" height="1.5" :fill="`url(#pgAc${si})`" rx="1" opacity="0.7"/>
            <rect x="18" y="154" width="124" height="26" rx="13" :fill="`url(#pgBtn${si})`"/>
            <rect x="18" y="154" width="124" height="26" rx="13" fill="rgba(255,255,255,0.12)"/>
            <text x="80" y="171" text-anchor="middle" font-family="Arial,sans-serif" font-size="9" font-weight="800" fill="#ffffff">→ Solicitar espacio</text>
            <rect x="0" y="190" width="160" height="10" fill="rgba(0,0,0,0.25)" rx="2"/>
            <text x="80" y="197.5" text-anchor="middle" font-family="Arial,sans-serif" font-size="6" fill="rgba(255,255,255,0.5)" letter-spacing="0.5">EasyPosWeb.com</text>
          </svg>
        </div>

      </div>
    </div>

  </aside>
</template>

<script setup>
import { ref, onMounted, onUnmounted, defineComponent, h } from "vue"
import api from "@/services/apis"

const emit = defineEmits(["close"])

// ── Sub-componente para el contenido del slot ────────────────────────────
const SlotContent = defineComponent({
  props: { slot: Object },
  setup(props) {
    return () => {
      const s = props.slot
      if (!s?.pieces?.length) return null
      const piece = s.pieces[0]
      const { piece_type, media_url, youtube_id, text_content } = piece

      const caption = (s.title && piece_type !== "text")
        ? h("div", { class: "ad-caption" }, s.title)
        : null

      if (piece_type === "image")
        return [
          h("img", { src: media_url, alt: s.title || "Pauta", class: "ad-media", loading: "lazy" }),
          caption,
        ]
      if (piece_type === "video")
        return [
          h("video", { src: media_url, autoplay: true, muted: true, loop: true, playsinline: true, preload: "metadata", class: "ad-media" }),
          caption,
        ]
      if (piece_type === "youtube")
        return h("div", { class: "ad-yt-wrap" }, [
          h("iframe", {
            src: `https://www.youtube.com/embed/${youtube_id}?autoplay=1&mute=1&loop=1&playlist=${youtube_id}&controls=0&rel=0`,
            frameborder: "0", allow: "autoplay; encrypted-media", allowfullscreen: true, class: "ad-yt"
          })
        ])
      if (piece_type === "text")
        return h("div", { class: "ad-text-wrap" }, [
          h("p", { class: "ad-title-txt" }, s.title),
          h("p", { class: "ad-body-txt" }, text_content),
        ])
      return null
    }
  }
})

// ── Datos ─────────────────────────────────────────────────────────────────
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

let refreshTimer = null
onMounted(() => {
  loadSlots()
  refreshTimer = setInterval(loadSlots, 5 * 60 * 1000)
})
onUnmounted(() => { if (refreshTimer) clearInterval(refreshTimer) })
</script>

<style scoped>
.sidebar-right {
  width: 180px;
  min-width: 180px;
  height: calc(100vh - 54px - 40px);
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  flex-shrink: 0;
  box-sizing: border-box;
}

.sr-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  background: rgba(0,0,0,0.2);
  flex-shrink: 0;
  border-bottom: 1px solid rgba(255,255,255,0.07);
}
.sr-title {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.5px; color: rgba(255,255,255,0.7);
  display: flex; align-items: center; gap: 6px;
}
.sr-title .bi { font-size: 13px; color: #f59e0b; }
.btn-sr-close {
  background: none; border: none; color: rgba(255,255,255,0.4);
  font-size: 13px; cursor: pointer; padding: 3px 5px;
  border-radius: 4px; line-height: 1;
  transition: color .15s, background .15s;
}
.btn-sr-close:hover { color: #fff; background: rgba(255,255,255,0.1); }

/* ── 3 Slots ── */
.sr-slots { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.ad-slot  {
  flex: 1; display: flex; flex-direction: column; overflow: hidden;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.ad-slot:last-child { border-bottom: none; }

.ad-link {
  display: flex; flex-direction: column; flex: 1; overflow: hidden;
  text-decoration: none; position: relative;
  transition: opacity .2s;
}
.ad-link:hover { opacity: .92; }

/* ── Placeholder ── */
.ad-placeholder { flex: 1; display: flex; align-items: center; justify-content: center; padding: 6px; }
.placeholder-svg { width: 100%; height: 100%; max-height: 100%; object-fit: contain; }

/* ── Móvil/tablet overlay (<1024px) ── */
@media (max-width: 1023px) {
  .sidebar-right {
    position: fixed; top: 54px; right: 0;
    height: calc(100dvh - 54px - 40px);
    z-index: 200; box-shadow: -4px 0 20px rgba(0,0,0,0.3);
  }
}

/* Landscape móvil: reducir altura de slots para caber en pantalla corta */
@media (max-height: 480px) and (orientation: landscape) {
  .ad-slot { min-height: 80px; }
}
</style>

<style>
/* Global para SlotContent (no scoped) */
.ad-media   { width: 100%; height: 100%; object-fit: cover; display: block; }
.ad-yt-wrap { flex: 1; overflow: hidden; background: #000; height: 100%; }
.ad-yt      { width: 100%; height: 100%; border: none; display: block; }
.ad-text-wrap {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center; padding: 10px; gap: 6px;
  background: linear-gradient(135deg,#1e293b,#0f172a); height: 100%;
}
.ad-title-txt { font-size: 11px; font-weight: 700; color: rgba(255,255,255,.9); text-align: center; margin: 0; }
.ad-body-txt  { font-size: 10px; color: rgba(255,255,255,.7); text-align: center; line-height: 1.5; margin: 0; }
.ad-caption {
  position: absolute; bottom: 0; left: 0; right: 0;
  background: linear-gradient(transparent,rgba(0,0,0,.65));
  color: #fff; font-size: 9px; font-weight: 600;
  padding: 12px 8px 5px; text-align: center;
}
</style>
