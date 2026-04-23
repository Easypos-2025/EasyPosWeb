<template>
  <aside class="sidebar-right">

    <div
      v-for="(slot, index) in adSlots"
      :key="index"
      class="ad-slot"
    >
      <!-- ── ÁREA DE MEDIA ── -->
      <div class="ad-media-area">
        <template v-if="slot.active">

          <!-- Imagen -->
          <img
            v-if="slot.type === 'image'"
            :src="slot.mediaUrl"
            :alt="slot.title"
            class="ad-img"
          />

          <!-- Video -->
          <video
            v-else-if="slot.type === 'video'"
            :src="slot.mediaUrl"
            autoplay muted loop playsinline
            class="ad-video"
          />

          <!-- Audio -->
          <div v-else-if="slot.type === 'audio'" class="ad-audio-wrap">
            <i class="bi bi-music-note-beamed"></i>
            <audio controls :src="slot.mediaUrl" class="ad-audio" />
            <p v-if="slot.title" class="ad-title">{{ slot.title }}</p>
          </div>

          <!-- Texto -->
          <div v-else-if="slot.type === 'text'" class="ad-text-wrap">
            <p v-if="slot.title" class="ad-title">{{ slot.title }}</p>
            <p class="ad-text">{{ slot.content }}</p>
          </div>

        </template>

        <!-- Sin pauta activa -->
        <div v-else class="ad-empty">
          <i class="bi bi-image"></i>
          <span>Espacio {{ index + 1 }}</span>
        </div>
      </div>

      <!-- ── REDES SOCIALES ── -->
      <div class="ad-social" v-if="slot.active && slot.social && slot.social.length">
        <a
          v-for="(red, i) in slot.social"
          :key="i"
          :href="red.url"
          target="_blank"
          rel="noopener"
          class="social-btn"
          :title="red.label"
        >
          <i :class="`bi ${red.icon}`"></i>
        </a>
      </div>
      <div v-else class="ad-social ad-social--empty">
        <i class="bi bi-share" title="Redes sociales"></i>
      </div>

    </div>

  </aside>
</template>

<script setup>
import { ref } from "vue"

defineEmits(["close"])

// Estructura base de cada slot — se llenará desde el módulo de pautas (SYSADMIN)
const adSlots = ref([
  {
    active: false,
    type: "image",       // image | video | audio | text
    mediaUrl: "",
    title: "",
    content: "",
    social: []           // [{ icon: "bi-instagram", label: "Instagram", url: "" }]
  },
  {
    active: false,
    type: "image",
    mediaUrl: "",
    title: "",
    content: "",
    social: []
  },
  {
    active: false,
    type: "image",
    mediaUrl: "",
    title: "",
    content: "",
    social: []
  }
])
</script>

<style scoped>

.sidebar-right {
  width: 180px;
  min-width: 180px;
  height: calc(100vh - 60px - 40px);
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  flex-shrink: 0;
  box-sizing: border-box;
}

/* ── SLOT ── */
.ad-slot {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-bottom: 1px solid rgba(255,255,255,0.07);
  overflow: hidden;
  min-height: 0;
}

.ad-slot:last-child {
  border-bottom: none;
}

/* ── ÁREA MEDIA ── */
.ad-media-area {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
}

.ad-img,
.ad-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.ad-audio-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 8px;
  color: var(--sidebar-text);
}

.ad-audio-wrap .bi {
  font-size: 26px;
  opacity: 0.7;
}

.ad-audio {
  width: 100%;
  height: 28px;
}

.ad-text-wrap {
  padding: 10px;
}

.ad-title {
  font-size: 11px;
  font-weight: 600;
  color: rgba(255,255,255,0.9);
  margin-bottom: 4px;
  text-align: center;
}

.ad-text {
  font-size: 11px;
  color: rgba(255,255,255,0.7);
  line-height: 1.5;
  text-align: center;
}

/* Placeholder vacío */
.ad-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  color: rgba(255,255,255,0.18);
}

.ad-empty .bi {
  font-size: 24px;
}

.ad-empty span {
  font-size: 10px;
}

/* ── REDES SOCIALES ── */
.ad-social {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 5px 6px;
  background: rgba(0,0,0,0.15);
  flex-shrink: 0;
  flex-wrap: wrap;
}

.ad-social--empty {
  opacity: 0.2;
}

.social-btn {
  color: rgba(255,255,255,0.8);
  font-size: 14px;
  text-decoration: none;
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: background 0.2s, color 0.2s;
}

.social-btn:hover {
  background: rgba(255,255,255,0.15);
  color: #fff;
}

/* Móvil — posición superpuesta */
@media (max-width: 768px) {
  .sidebar-right {
    position: fixed;
    top: 60px;
    right: 0;
    height: calc(100dvh - 60px - 40px);
    z-index: 200;
    box-shadow: -4px 0 20px rgba(0,0,0,0.3);
  }
}
</style>
