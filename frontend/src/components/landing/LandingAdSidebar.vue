<template>
  <aside class="landing-sidebar">
    <div class="ls-header">
      <i class="bi bi-megaphone-fill"></i>
      <span>Destacados</span>
    </div>

    <div class="ls-slots">
      <div v-for="slot in slots" :key="slot.slot" class="ls-slot">

        <template v-if="slot.active && slot.pieces.length">
          <a
            :href="slot.cta_url || undefined"
            :target="slot.cta_url ? '_blank' : undefined"
            rel="noopener noreferrer"
            class="ls-ad-link"
            @click="slot.cta_url ? null : $event.preventDefault()"
          >
            <template v-for="(piece, pi) in slot.pieces.slice(0, 1)" :key="pi">

              <img
                v-if="piece.piece_type === 'image'"
                :src="piece.media_url"
                :alt="slot.title || 'Pauta'"
                class="ls-media"
                loading="lazy"
              />

              <!-- Video: no autoplay en landing, usa preload=metadata + poster -->
              <video
                v-else-if="piece.piece_type === 'video'"
                :src="piece.media_url"
                autoplay muted loop playsinline
                preload="metadata"
                class="ls-media"
              />

              <div v-else-if="piece.piece_type === 'youtube'" class="ls-yt-wrap">
                <iframe
                  :src="`https://www.youtube.com/embed/${piece.youtube_id}?autoplay=0&mute=1&loop=1&playlist=${piece.youtube_id}&rel=0`"
                  frameborder="0"
                  allow="encrypted-media"
                  allowfullscreen
                  loading="lazy"
                  class="ls-yt"
                ></iframe>
              </div>

              <div v-else-if="piece.piece_type === 'text'" class="ls-text-wrap">
                <p class="ls-text-title">{{ slot.title }}</p>
                <p class="ls-text-body">{{ piece.text_content }}</p>
              </div>

            </template>

            <div v-if="slot.title && slot.pieces[0]?.piece_type !== 'text'" class="ls-caption">
              {{ slot.title }}
            </div>
          </a>
        </template>

        <!-- Placeholder -->
        <a href="/register" class="ls-placeholder-link" v-else>
          <svg viewBox="0 0 180 200" xmlns="http://www.w3.org/2000/svg" class="ls-placeholder-svg">
            <defs>
              <linearGradient id="lpBg" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%"   stop-color="#1e3a5f"/>
                <stop offset="100%" stop-color="#0d4f3c"/>
              </linearGradient>
              <linearGradient id="lpAccent" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%"   stop-color="#2563eb"/>
                <stop offset="100%" stop-color="#10b981"/>
              </linearGradient>
            </defs>
            <rect width="180" height="200" fill="url(#lpBg)" rx="8"/>
            <rect x="0" y="0" width="180" height="4" fill="url(#lpAccent)" rx="2"/>
            <g transform="translate(58, 30) scale(1.4)" fill="none" stroke="url(#lpAccent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 9v6h4l5 5V4L7 9H3z"/>
              <path d="M16 8.5c1 .7 1.5 1.7 1.5 3s-.5 2.3-1.5 3"/>
            </g>
            <rect x="24" y="94" width="132" height="2" fill="url(#lpAccent)" rx="1" opacity="0.6"/>
            <text x="90" y="118" text-anchor="middle" font-family="Arial,sans-serif" font-size="14" font-weight="700" fill="#ffffff">Paute Aquí</text>
            <text x="90" y="136" text-anchor="middle" font-family="Arial,sans-serif" font-size="8" fill="rgba(255,255,255,0.65)">Llegue a todos nuestros</text>
            <text x="90" y="148" text-anchor="middle" font-family="Arial,sans-serif" font-size="8" fill="rgba(255,255,255,0.65)">Asociados EasyPosWeb</text>
            <rect x="28" y="162" width="124" height="24" rx="12" fill="url(#lpAccent)" opacity="0.9"/>
            <text x="90" y="178" text-anchor="middle" font-family="Arial,sans-serif" font-size="9" font-weight="700" fill="#ffffff">Solicitar información</text>
          </svg>
        </a>

      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue"
import api from "@/services/apis"

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
  refreshTimer = setInterval(loadSlots, 5 * 60 * 1000)
})
onUnmounted(() => { if (refreshTimer) clearInterval(refreshTimer) })
</script>

<style scoped>
.landing-sidebar {
  position: sticky;
  top: 80px;
  width: 190px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-self: flex-start;
}

.ls-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(255,255,255,0.5);
  padding: 0 4px 4px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.ls-header .bi { color: #f59e0b; font-size: 12px; }

.ls-slots { display: flex; flex-direction: column; gap: 8px; }

.ls-slot {
  border-radius: 10px;
  overflow: hidden;
  background: rgba(0,0,0,0.3);
  height: 200px;
  position: relative;
}

.ls-ad-link, .ls-placeholder-link {
  display: flex;
  flex-direction: column;
  height: 100%;
  text-decoration: none;
  position: relative;
  overflow: hidden;
}

.ls-media {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.ls-yt-wrap { flex: 1; background: #000; }
.ls-yt { width: 100%; height: 100%; border: none; display: block; }

.ls-text-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px;
  gap: 6px;
  background: linear-gradient(135deg, #1e3a5f, #0d4f3c);
}
.ls-text-title { font-size: 13px; font-weight: 700; color: #fff; text-align: center; margin: 0; }
.ls-text-body  { font-size: 11px; color: rgba(255,255,255,.75); text-align: center; line-height: 1.5; margin: 0; }

.ls-caption {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  background: linear-gradient(transparent, rgba(0,0,0,.65));
  color: #fff; font-size: 10px; font-weight: 600;
  padding: 14px 8px 6px;
  text-align: center;
}

.ls-placeholder-svg {
  width: 100%;
  height: 100%;
  display: block;
  transition: opacity .2s;
}
.ls-placeholder-link:hover .ls-placeholder-svg { opacity: 0.85; }

/* Ocultar en pantallas pequeñas */
@media (max-width: 1100px) {
  .landing-sidebar { display: none; }
}
</style>
