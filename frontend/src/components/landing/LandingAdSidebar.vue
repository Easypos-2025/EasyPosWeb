<template>
  <div class="ad-sidebar-wrap">
    <div v-for="(slot, si) in slots" :key="slot.slot" class="ads-slot">
      <component
        :is="slot.cta_url ? 'a' : 'div'"
        v-bind="slot.cta_url ? { href: slot.cta_url, target: '_blank', rel: 'noopener noreferrer' } : {}"
        class="ads-inner"
        :class="{ 'ads-link': slot.cta_url }"
      >
        <template v-if="slot.active && slot.pieces?.length">
          <SlotPiece
            :piece="slot.pieces[slotPieceIdx[si] % slot.pieces.length]"
            :title="slot.title"
            :muted="slotMuted[si]"
          />
          <span class="ads-label">Publicidad</span>

          <button
            v-if="isMediaPiece(slot.pieces[slotPieceIdx[si] % slot.pieces.length])"
            class="ads-btn-audio"
            @click.prevent.stop="toggleAudio(si)"
            :title="slotMuted[si] ? 'Activar audio' : 'Silenciar'"
          >
            <i :class="slotMuted[si] ? 'bi bi-volume-mute-fill' : 'bi bi-volume-up-fill'"></i>
          </button>

          <div v-if="slot.pieces.length > 1" class="ads-dots">
            <span v-for="(p, pi) in slot.pieces" :key="pi"
              class="adsdot" :class="{ active: pi === slotPieceIdx[si] }"></span>
          </div>

          <div v-if="slotHasSocial(slot)" class="ads-social-icons">
            <a v-if="slot.social_instagram" :href="slot.social_instagram" target="_blank" rel="noopener" @click.stop class="ads-soc-btn soc-instagram" title="Instagram"><i class="bi bi-instagram"></i></a>
            <a v-if="slot.social_tiktok"    :href="slot.social_tiktok"    target="_blank" rel="noopener" @click.stop class="ads-soc-btn soc-tiktok"    title="TikTok"><i class="bi bi-tiktok"></i></a>
            <a v-if="slot.social_facebook"  :href="slot.social_facebook"  target="_blank" rel="noopener" @click.stop class="ads-soc-btn soc-facebook"  title="Facebook"><i class="bi bi-facebook"></i></a>
            <a v-if="slot.social_youtube_channel" :href="slot.social_youtube_channel" target="_blank" rel="noopener" @click.stop class="ads-soc-btn soc-youtube" title="YouTube"><i class="bi bi-youtube"></i></a>
            <a v-if="slot.social_website"   :href="slot.social_website"   target="_blank" rel="noopener" @click.stop class="ads-soc-btn soc-website"   title="Sitio web"><i class="bi bi-globe2"></i></a>
          </div>
        </template>

        <template v-else>
          <a href="#contacto" class="ads-placeholder">
            <div class="ads-ph-bg"></div>
            <div class="ads-ph-content">
              <div class="ads-ph-icon-wrap"><i class="bi bi-megaphone-fill ads-ph-icon"></i></div>
              <div class="ads-ph-text">
                <span class="ads-ph-title">¡Paute Aquí!</span>
                <span class="ads-ph-sub">Llega a miles de asociados</span>
              </div>
            </div>
          </a>
        </template>
      </component>
    </div>
  </div>
</template>

<!-- Sub-componente SlotPiece (vertical) -->
<script>
import { defineComponent, h, computed } from "vue"

const SOCIAL_ICONS  = { youtube: "bi-youtube", instagram: "bi-instagram", tiktok: "bi-tiktok", facebook: "bi-facebook", twitter: "bi-twitter-x", social: "bi-play-circle" }
const SOCIAL_COLORS = { youtube: "#ff0000", instagram: "#e1306c", tiktok: "#010101", facebook: "#1877f2", twitter: "#1da1f2", social: "#6b7280" }

const SlotPiece = defineComponent({
  name: "SidebarSlotPiece",
  props: { piece: Object, title: String, muted: { type: Boolean, default: true } },
  setup(props) {
    const ytSrc = computed(() => {
      if (!props.piece?.youtube_id) return ""
      return `https://www.youtube.com/embed/${props.piece.youtube_id}?autoplay=1&loop=1&playlist=${props.piece.youtube_id}&controls=0&rel=0&enablejsapi=1&mute=1`
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
      return h("video", { src: media_url, autoplay: true, muted: this.muted, loop: true, playsinline: true, preload: "metadata", class: "slot-media" })

    if (piece_type === "youtube")
      return h("div", { class: "slot-yt-wrap" }, [
        h("iframe", { key: `yt-${p.youtube_id}`, src: this.ytSrc, frameborder: "0", allow: "autoplay; encrypted-media", allowfullscreen: true, class: "slot-yt" })
      ])

    if (piece_type === "social") {
      const plat  = social_platform || "social"
      const icon  = SOCIAL_ICONS[plat]  || "bi-play-circle"
      const color = SOCIAL_COLORS[plat] || "#6b7280"
      return h("a", { href: media_url, target: "_blank", rel: "noopener noreferrer", class: "slot-social-card" }, [
        h("div", { class: "slot-social-bg", style: `background:${color}18` }),
        h("div", { class: "slot-social-content" }, [
          h("i",    { class: `bi ${icon} slot-social-icon`, style: `color:${color}` }),
          h("span", { class: "slot-social-title" }, this.title || ""),
          h("span", { class: "slot-social-cta" }, "Ver publicación →"),
        ])
      ])
    }

    if (piece_type === "text")
      return h("div", { class: "slot-text" }, [
        h("p", { class: "slot-text-title" }, this.title || ""),
        h("p", { class: "slot-text-body"  }, text_content),
      ])

    return null
  }
})

export default { components: { SlotPiece } }
</script>

<script setup>
import { ref, onMounted, onUnmounted } from "vue"
import api from "@/services/apis"

const slots        = ref([
  { slot: 1, active: false, pieces: [] },
  { slot: 2, active: false, pieces: [] },
  { slot: 3, active: false, pieces: [] },
])
const slotPieceIdx = ref([0, 0, 0])
const slotMuted    = ref([true, true, true])
const slotTimers   = [null, null, null]

function isMediaPiece(piece) {
  return piece?.piece_type === "video" || piece?.piece_type === "youtube"
}
function slotHasSocial(slot) {
  return slot?.active && (slot.social_instagram || slot.social_tiktok || slot.social_facebook || slot.social_youtube_channel || slot.social_website)
}
function toggleAudio(si) {
  slotMuted.value[si] = !slotMuted.value[si]
  const slotsEls = document.querySelectorAll(".ad-sidebar-wrap .ads-slot")
  const iframe = slotsEls[si]?.querySelector("iframe")
  if (iframe?.contentWindow) {
    const cmd = slotMuted.value[si] ? "mute" : "unMute"
    iframe.contentWindow.postMessage(JSON.stringify({ event: "command", func: cmd, args: "" }), "https://www.youtube.com")
  }
}

function scheduleSlot(si) {
  clearTimeout(slotTimers[si])
  const s = slots.value[si]
  if (!s?.pieces?.length || s.pieces.length <= 1) return
  slotTimers[si] = setTimeout(() => {
    slotPieceIdx.value[si] = (slotPieceIdx.value[si] + 1) % s.pieces.length
    scheduleSlot(si)
  }, 8_000)
}

async function loadSlots() {
  try {
    const res = await api.get("/ads/active-slots")
    if (Array.isArray(res.data)) {
      slots.value        = res.data
      slotPieceIdx.value = [0, 0, 0]
      slots.value.forEach((_, si) => scheduleSlot(si))
    }
  } catch {}
}

let refreshTimer = null
function onAdsRefresh() { loadSlots() }

onMounted(() => {
  window.addEventListener("ads-refresh", onAdsRefresh)
  loadSlots()
  refreshTimer = setInterval(loadSlots, 5 * 60 * 1000)
})

onUnmounted(() => {
  window.removeEventListener("ads-refresh", onAdsRefresh)
  if (refreshTimer) clearInterval(refreshTimer)
  slotTimers.forEach((_, i) => clearTimeout(slotTimers[i]))
})
</script>

<style scoped>
.ad-sidebar-wrap {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  height: 100%;
  padding: 8px;
  box-sizing: border-box;
  background: #0a0e1a;
}

.ads-slot {
  flex: 1;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
  min-height: 0;
}

.ads-inner {
  display: flex;
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
  text-decoration: none;
}
.ads-link { cursor: pointer; transition: opacity .2s; }
.ads-link:hover { opacity: .92; }

/* ── Placeholder ── */
.ads-placeholder {
  display: flex; width: 100%; height: 100%;
  text-decoration: none; cursor: pointer; transition: filter .2s;
}
.ads-placeholder:hover { filter: brightness(1.1); }

.ads-ph-bg {
  position: absolute; inset: 0;
  background: linear-gradient(145deg, #2563eb 0%, #4f46e5 50%, #7c3aed 100%);
}
.ads-ph-bg::before {
  content: ""; position: absolute; border-radius: 50%;
  width: 100px; height: 100px; top: -30px; right: -20px;
  background: rgba(255,255,255,.08);
}
.ads-ph-content {
  position: relative; z-index: 1;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  width: 100%; height: 100%; gap: 8px; padding: 12px;
}
.ads-ph-icon-wrap {
  width: 40px; height: 40px;
  background: rgba(255,255,255,.15); border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
}
.ads-ph-icon  { font-size: 20px; color: #fbbf24; }
.ads-ph-text  { display: flex; flex-direction: column; align-items: center; gap: 3px; }
.ads-ph-title { font-size: 13px; font-weight: 800; color: #fff; white-space: nowrap; }
.ads-ph-sub   { font-size: 10px; color: rgba(255,255,255,.8); white-space: nowrap; }

/* ── Label Publicidad ── */
.ads-label {
  position: absolute; top: 6px; right: 6px; z-index: 10;
  font-size: 8px; font-weight: 700; letter-spacing: .5px;
  text-transform: uppercase; color: rgba(255,255,255,.75);
  background: rgba(0,0,0,.45); backdrop-filter: blur(4px);
  border: 1px solid rgba(255,255,255,.15);
  border-radius: 4px; padding: 2px 5px;
  pointer-events: none; user-select: none;
}

/* ── Botón audio ── */
.ads-btn-audio {
  position: absolute; bottom: 6px; right: 6px; z-index: 10;
  width: 26px; height: 26px; border-radius: 50%;
  background: rgba(0,0,0,.55); border: 1px solid rgba(255,255,255,.25);
  color: #fff; font-size: 11px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: background .2s;
  backdrop-filter: blur(4px);
}
.ads-btn-audio:hover { background: rgba(0,0,0,.8); }

/* ── Dots piezas ── */
.ads-dots {
  position: absolute; bottom: 5px; left: 50%; transform: translateX(-50%);
  display: flex; gap: 4px; z-index: 5; pointer-events: none;
}
.adsdot {
  width: 5px; height: 5px; border-radius: 50%;
  background: rgba(255,255,255,.35); transition: background .2s;
}
.adsdot.active { background: #fff; }

/* ── Redes sociales ── */
.ads-social-icons {
  position: absolute; top: 6px; left: 6px; z-index: 10;
  display: flex; flex-direction: column; gap: 4px;
}
.ads-soc-btn {
  width: 24px; height: 24px; border-radius: 6px;
  color: #fff; font-size: 12px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  text-decoration: none; transition: transform .15s;
  box-shadow: 0 2px 5px rgba(0,0,0,.3);
}
.ads-soc-btn:hover { transform: scale(1.15); }
.soc-instagram { background: radial-gradient(circle at 30% 107%, #fdf497 0%, #fdf497 5%, #fd5949 45%, #d6249f 60%, #285AEB 90%); }
.soc-tiktok    { background: #010101; }
.soc-facebook  { background: #1877f2; }
.soc-youtube   { background: #ff0000; }
.soc-website   { background: #374151; }

@media (max-width: 768px) {
  .ad-sidebar-wrap { gap: 6px; padding: 6px; }
  .ads-slot { border-radius: 10px; }
}
@media (max-width: 576px) {
  .ad-sidebar-wrap { padding: 4px; gap: 4px; }
}
</style>
