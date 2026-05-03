<template>
  <aside class="sidebar-right">

    <!-- Cabecera con botón de cierre -->
    <div class="sr-header">
      <span class="sr-title">
        <i class="bi bi-megaphone-fill"></i>
        Panel
      </span>
      <button class="btn-sr-close" @click="emit('close')" title="Cerrar panel">
        <i class="bi bi-x-lg"></i>
      </button>
    </div>

    <!-- Slots de publicidad (activos desde SYSADMIN cuando se configure) -->
    <template v-for="(slot, index) in adSlots" :key="index">
      <div class="slot slot-ad" v-if="slot.active">

        <img v-if="slot.type === 'image'" :src="slot.mediaUrl" :alt="slot.title" class="ad-img" />

        <video v-else-if="slot.type === 'video'" :src="slot.mediaUrl"
          autoplay muted loop playsinline class="ad-img" />

        <div v-else-if="slot.type === 'audio'" class="ad-audio-wrap">
          <i class="bi bi-music-note-beamed"></i>
          <audio controls :src="slot.mediaUrl" class="ad-audio" />
          <p v-if="slot.title" class="ad-title">{{ slot.title }}</p>
        </div>

        <div v-else-if="slot.type === 'text'" class="ad-text-wrap">
          <p v-if="slot.title" class="ad-title">{{ slot.title }}</p>
          <p class="ad-text">{{ slot.content }}</p>
        </div>

        <div class="ad-social" v-if="slot.social && slot.social.length">
          <a v-for="(red, i) in slot.social" :key="i" :href="red.url"
            target="_blank" rel="noopener" class="social-btn" :title="red.label">
            <i :class="`bi ${red.icon}`"></i>
          </a>
        </div>

      </div>
    </template>

    <!-- Placeholder cuando no hay publicidad configurada -->
    <div v-if="adSlots.every(s => !s.active)" class="sr-placeholder">
      <i class="bi bi-megaphone"></i>
      <span>Mensajes publicitarios</span>
      <small>Próximamente disponible</small>
    </div>

  </aside>
</template>

<script setup>
import { ref } from "vue"

const emit = defineEmits(["close"])

const adSlots = ref([
  { active: false, type: "image", mediaUrl: "", title: "", content: "", social: [] },
  { active: false, type: "image", mediaUrl: "", title: "", content: "", social: [] },
])
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

/* ── Cabecera ── */
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

/* ── Placeholder publicidad ── */
.sr-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px 14px;
  color: rgba(255,255,255,0.25);
  text-align: center;
}
.sr-placeholder .bi { font-size: 32px; opacity: 0.4; }
.sr-placeholder span { font-size: 12px; font-weight: 600; }
.sr-placeholder small { font-size: 10px; opacity: 0.6; line-height: 1.4; }

/* ── Slot publicidad ── */
.slot-ad {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ad-img    { width: 100%; height: 100%; object-fit: cover; }
.ad-audio-wrap {
  display: flex; flex-direction: column;
  align-items: center; gap: 6px; padding: 8px;
  color: var(--sidebar-text);
}
.ad-audio-wrap .bi { font-size: 24px; opacity: 0.7; }
.ad-audio  { width: 100%; height: 28px; }
.ad-text-wrap { padding: 10px; }
.ad-title  { font-size: 11px; font-weight: 600; color: rgba(255,255,255,0.9); margin-bottom: 4px; text-align: center; }
.ad-text   { font-size: 11px; color: rgba(255,255,255,0.7); line-height: 1.5; text-align: center; }

.ad-social {
  display: flex; align-items: center; justify-content: center;
  gap: 6px; padding: 5px 6px;
  background: rgba(0,0,0,0.15); flex-shrink: 0; flex-wrap: wrap;
}
.social-btn {
  color: rgba(255,255,255,0.8); font-size: 14px; text-decoration: none;
  width: 26px; height: 26px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 6px; transition: background 0.2s;
}
.social-btn:hover { background: rgba(255,255,255,0.15); color: #fff; }

/* ── Móvil/tablet (<1024px): overlay flotante con botón de cierre visible ── */
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
