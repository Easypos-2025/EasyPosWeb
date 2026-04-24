<template>
  <aside class="sidebar-right">

    <!-- ── SLOT 1: NOTIFICACIONES (prioridad sobre publicidad) ── -->
    <div class="slot slot-notif" v-if="notifications.length > 0 || loadingNotif">

      <div class="slot-header">
        <span class="slot-title">
          <i class="bi bi-bell-fill"></i>
          Mensajes
          <span v-if="unreadCount > 0" class="notif-badge">{{ unreadCount }}</span>
        </span>
        <button v-if="unreadCount > 0" class="btn-mark-read" @click="markAllRead"
          title="Marcar todo como leído">
          <i class="bi bi-check2-all"></i>
        </button>
      </div>

      <div v-if="loadingNotif" class="notif-loading">
        <i class="bi bi-arrow-repeat spin"></i>
      </div>

      <div v-else class="notif-list">
        <div
          v-for="n in notifications"
          :key="n.id"
          class="notif-item"
          :class="{ unread: !n.is_read }"
          @click="openTask(n.task_id)"
        >
          <div class="notif-dot" v-if="!n.is_read"></div>
          <div class="notif-body">
            <p class="notif-text">{{ n.comment }}</p>
            <span class="notif-meta">
              <i class="bi bi-clipboard"></i> Tarea #{{ n.task_id }}
              · {{ fmtAgo(n.created_at) }}
            </span>
          </div>
        </div>
        <div v-if="notifications.length === 0" class="notif-empty">
          <i class="bi bi-check2-circle"></i>
          <span>Sin mensajes pendientes</span>
        </div>
      </div>
    </div>

    <!-- ── SLOTS 2 y 3: PUBLICIDAD (ocultos si vacíos) ── -->
    <template v-for="(slot, index) in adSlots" :key="index">
      <div class="slot slot-ad" v-if="slot.active">

        <!-- Imagen -->
        <img v-if="slot.type === 'image'" :src="slot.mediaUrl" :alt="slot.title" class="ad-img" />

        <!-- Video -->
        <video v-else-if="slot.type === 'video'" :src="slot.mediaUrl"
          autoplay muted loop playsinline class="ad-img" />

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

        <!-- Redes sociales -->
        <div class="ad-social" v-if="slot.social && slot.social.length">
          <a v-for="(red, i) in slot.social" :key="i" :href="red.url"
            target="_blank" rel="noopener" class="social-btn" :title="red.label">
            <i :class="`bi ${red.icon}`"></i>
          </a>
        </div>

      </div>
      <!-- Slot vacío → no se muestra nada (oculto por diseño del perfil) -->
    </template>

  </aside>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue"
import { useRouter } from "vue-router"
import api from "@/services/apis"

const router = useRouter()

// ── Publicidad (se llenará desde SYSADMIN cuando llegue ese módulo) ──
const adSlots = ref([
  { active: false, type: "image", mediaUrl: "", title: "", content: "", social: [] },
  { active: false, type: "image", mediaUrl: "", title: "", content: "", social: [] },
])

// ── Notificaciones ────────────────────────────────────────────
const notifications = ref([])
const loadingNotif  = ref(false)
let   refreshTimer  = null

const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)

async function loadNotifications() {
  const token = localStorage.getItem("token")
  if (!token) return
  loadingNotif.value = true
  try {
    const res = await api.get("/task-comments/notifications/unread")
    notifications.value = res.data
  } catch {
    // Sin notificaciones o usuario sin sesión activa — no bloquear
  } finally {
    loadingNotif.value = false
  }
}

async function markAllRead() {
  const unread = notifications.value.filter(n => !n.is_read)
  await Promise.allSettled(
    unread.map(n => api.patch(`/task-comments/${n.id}/read`))
  )
  notifications.value = notifications.value.map(n => ({ ...n, is_read: true }))
}

function openTask(taskId) {
  router.push(`/tasks/${taskId}/reportes`)
}

function fmtAgo(iso) {
  if (!iso) return ""
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1)  return "ahora"
  if (mins < 60) return `hace ${mins} min`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24)  return `hace ${hrs} h`
  return `hace ${Math.floor(hrs / 24)} d`
}

onMounted(() => {
  loadNotifications()
  // Actualizar notificaciones cada 60 segundos
  refreshTimer = setInterval(loadNotifications, 60000)
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

/* ── SLOT GENÉRICO ── */
.slot {
  border-bottom: 1px solid rgba(255,255,255,0.07);
}
.slot:last-child { border-bottom: none; }

/* ── NOTIFICACIONES ── */
.slot-notif {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.slot-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px 6px;
  background: rgba(0,0,0,0.15);
  flex-shrink: 0;
}

.slot-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  color: rgba(255,255,255,0.75);
  display: flex;
  align-items: center;
  gap: 5px;
}

.notif-badge {
  background: #ef4444;
  color: #fff;
  font-size: 9px;
  font-weight: 800;
  border-radius: 10px;
  padding: 1px 5px;
  line-height: 1.4;
}

.btn-mark-read {
  background: none;
  border: none;
  color: rgba(255,255,255,0.5);
  font-size: 14px;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 4px;
  transition: color 0.15s;
}
.btn-mark-read:hover { color: #22c55e; }

.notif-loading {
  padding: 20px;
  text-align: center;
  color: rgba(255,255,255,0.3);
  font-size: 18px;
}

.notif-list {
  flex: 1;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,0.1) transparent;
}

.notif-item {
  display: flex;
  gap: 8px;
  padding: 10px 10px 8px;
  cursor: pointer;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  transition: background 0.15s;
  position: relative;
}

.notif-item:hover { background: rgba(255,255,255,0.07); }

.notif-item.unread {
  background: rgba(59,130,246,0.12);
}
.notif-item.unread:hover { background: rgba(59,130,246,0.2); }

.notif-dot {
  width: 6px;
  height: 6px;
  background: #3b82f6;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 5px;
}

.notif-body {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.notif-text {
  font-size: 11px;
  color: rgba(255,255,255,0.88);
  margin: 0;
  line-height: 1.4;
  /* Limitar a 3 líneas */
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notif-meta {
  font-size: 10px;
  color: rgba(255,255,255,0.4);
  display: flex;
  align-items: center;
  gap: 3px;
}

.notif-empty {
  padding: 20px 10px;
  text-align: center;
  color: rgba(255,255,255,0.25);
  font-size: 11px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
.notif-empty .bi { font-size: 20px; }

/* ── PUBLICIDAD ── */
.slot-ad {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ad-img    { width:100%; height:100%; object-fit:cover; }
.ad-audio-wrap { display:flex; flex-direction:column; align-items:center; gap:6px; padding:8px; color:var(--sidebar-text); }
.ad-audio-wrap .bi { font-size:24px; opacity:0.7; }
.ad-audio  { width:100%; height:28px; }
.ad-text-wrap { padding:10px; }
.ad-title  { font-size:11px; font-weight:600; color:rgba(255,255,255,0.9); margin-bottom:4px; text-align:center; }
.ad-text   { font-size:11px; color:rgba(255,255,255,0.7); line-height:1.5; text-align:center; }

.ad-social {
  display:flex; align-items:center; justify-content:center;
  gap:6px; padding:5px 6px;
  background:rgba(0,0,0,0.15); flex-shrink:0; flex-wrap:wrap;
}
.social-btn {
  color:rgba(255,255,255,0.8); font-size:14px; text-decoration:none;
  width:26px; height:26px; display:flex; align-items:center; justify-content:center;
  border-radius:6px; transition:background 0.2s;
}
.social-btn:hover { background:rgba(255,255,255,0.15); color:#fff; }

/* Móvil */
@media (max-width: 768px) {
  .sidebar-right {
    position: fixed; top: 54px; right: 0;
    height: calc(100dvh - 54px - 40px);
    z-index: 200;
    box-shadow: -4px 0 20px rgba(0,0,0,0.3);
  }
}

.spin { display:inline-block; animation:spin 0.8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
</style>
