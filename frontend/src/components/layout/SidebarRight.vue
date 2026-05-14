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
      <div v-for="slot in slots" :key="slot.slot" class="ad-slot">

        <!-- Slot activo -->
        <template v-if="slot.active && slot.pieces.length">
          <a
            :href="slot.cta_url || undefined"
            :target="slot.cta_url ? '_blank' : undefined"
            rel="noopener noreferrer"
            class="ad-link"
            @click="slot.cta_url ? null : $event.preventDefault()"
          >
            <template v-for="(piece, pi) in slot.pieces" :key="pi">

              <img
                v-if="piece.piece_type === 'image'"
                :src="piece.media_url"
                :alt="slot.title || 'Pauta'"
                class="ad-media"
                loading="lazy"
              />

              <video
                v-else-if="piece.piece_type === 'video'"
                :src="piece.media_url"
                autoplay muted loop playsinline
                preload="metadata"
                class="ad-media"
              />

              <div v-else-if="piece.piece_type === 'youtube'" class="ad-yt-wrap">
                <iframe
                  :src="`https://www.youtube.com/embed/${piece.youtube_id}?autoplay=1&mute=1&loop=1&playlist=${piece.youtube_id}&controls=0&showinfo=0&rel=0`"
                  frameborder="0"
                  allow="autoplay; encrypted-media"
                  allowfullscreen
                  class="ad-yt"
                ></iframe>
              </div>

              <div v-else-if="piece.piece_type === 'text'" class="ad-text-wrap">
                <p class="ad-title-txt">{{ slot.title }}</p>
                <p class="ad-body-txt">{{ piece.text_content }}</p>
              </div>

            </template>

            <div v-if="slot.title && slot.pieces[0]?.piece_type !== 'text'" class="ad-caption">
              {{ slot.title }}
            </div>
          </a>
        </template>

        <!-- Placeholder "Paute Aquí" -->
        <div v-else class="ad-placeholder">
          <svg viewBox="0 0 160 200" xmlns="http://www.w3.org/2000/svg" class="placeholder-svg">
            <defs>
              <linearGradient id="pgBg" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%"   stop-color="#1e3a5f"/>
                <stop offset="100%" stop-color="#0d4f3c"/>
              </linearGradient>
              <linearGradient id="pgAccent" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%"   stop-color="#2563eb"/>
                <stop offset="100%" stop-color="#10b981"/>
              </linearGradient>
            </defs>
            <rect width="160" height="200" fill="url(#pgBg)" rx="8"/>
            <rect x="0" y="0" width="160" height="4" fill="url(#pgAccent)" rx="2"/>
            <!-- Megaphone icon -->
            <g transform="translate(48, 32) scale(1.3)" fill="none" stroke="url(#pgAccent)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 9v6h4l5 5V4L7 9H3z"/>
              <path d="M16 8.5c1 .7 1.5 1.7 1.5 3s-.5 2.3-1.5 3"/>
            </g>
            <rect x="20" y="96" width="120" height="2" fill="url(#pgAccent)" rx="1" opacity="0.6"/>
            <text x="80" y="122" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" font-weight="700" fill="#ffffff">Paute Aquí</text>
            <text x="80" y="140" text-anchor="middle" font-family="Arial,sans-serif" font-size="7.5" fill="rgba(255,255,255,0.65)">Llegue a todos nuestros</text>
            <text x="80" y="152" text-anchor="middle" font-family="Arial,sans-serif" font-size="7.5" fill="rgba(255,255,255,0.65)">Asociados</text>
            <rect x="30" y="165" width="100" height="22" rx="11" fill="url(#pgAccent)" opacity="0.9"/>
            <text x="80" y="180" text-anchor="middle" font-family="Arial,sans-serif" font-size="8.5" font-weight="700" fill="#ffffff">Solicitar información</text>
          </svg>
        </div>

      </div>
    </div>

  </aside>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue"
import api from "@/services/apis"

const emit = defineEmits(["close"])

const slots = ref([
  { slot: 1, active: false, pieces: [] },
  { slot: 2, active: false, pieces: [] },
  { slot: 3, active: false, pieces: [] },
])

async function loadSlots() {
  try {
    const res = await api.get("/ads/active-slots")
    slots.value = res.data
  } catch {}
}

let refreshTimer = null

onMounted(() => {
  loadSlots()
  // Refresh every 5 minutes
  refreshTimer = setInterval(loadSlots, 5 * 60 * 1000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
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
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(255,255,255,0.7);
  display: flex;
  align-items: center;
  gap: 6px;
}
.sr-title .bi { font-size: 13px; color: #f59e0b; }

.btn-sr-close {
  background: none;
  border: none;
  color: rgba(255,255,255,0.4);
  font-size: 13px;
  cursor: pointer;
  padding: 3px 5px;
  border-radius: 4px;
  transition: color 0.15s, background 0.15s;
  line-height: 1;
}
.btn-sr-close:hover { color: #fff; background: rgba(255,255,255,0.1); }

/* ── 3 Slots ── */
.sr-slots {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ad-slot {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.ad-slot:last-child { border-bottom: none; }

/* ── Ad link wrapper ── */
.ad-link {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  text-decoration: none;
  position: relative;
}

.ad-media {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.ad-yt-wrap {
  flex: 1;
  overflow: hidden;
  background: #000;
}
.ad-yt {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
}

.ad-text-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 10px;
  gap: 6px;
}
.ad-title-txt {
  font-size: 11px;
  font-weight: 700;
  color: rgba(255,255,255,0.9);
  text-align: center;
  margin: 0;
}
.ad-body-txt {
  font-size: 10px;
  color: rgba(255,255,255,0.7);
  text-align: center;
  line-height: 1.5;
  margin: 0;
}

.ad-caption {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0,0,0,0.65));
  color: #fff;
  font-size: 9px;
  font-weight: 600;
  padding: 12px 8px 6px;
  text-align: center;
}

/* ── Placeholder ── */
.ad-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
}
.placeholder-svg {
  width: 100%;
  height: 100%;
  max-height: 100%;
  object-fit: contain;
}

/* ── Móvil overlay ── */
@media (max-width: 1023px) {
  .sidebar-right {
    position: fixed;
    top: 54px;
    right: 0;
    height: calc(100dvh - 54px - 40px);
    z-index: 200;
    box-shadow: -4px 0 20px rgba(0,0,0,0.3);
  }
}
</style>
