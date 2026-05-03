<template>
  <div class="inbox-wrap">

    <!-- KPI Bar -->
    <div class="kpi-bar">
      <div class="kpi-card">
        <i class="bi bi-envelope-open"></i>
        <div class="kpi-data">
          <span class="kpi-val">{{ items.length }}</span>
          <span class="kpi-lbl">Total recibidos</span>
        </div>
      </div>
      <div class="kpi-card kpi-alert">
        <i class="bi bi-bell-fill"></i>
        <div class="kpi-data">
          <span class="kpi-val">{{ unreadCount }}</span>
          <span class="kpi-lbl">Sin leer</span>
        </div>
      </div>
      <div class="kpi-card kpi-ok">
        <i class="bi bi-check2-all"></i>
        <div class="kpi-data">
          <span class="kpi-val">{{ items.length - unreadCount }}</span>
          <span class="kpi-lbl">Leídos</span>
        </div>
      </div>
      <button class="btn-compose" @click="showCompose = true">
        <i class="bi bi-pencil-square"></i> Redactar
      </button>
    </div>

    <!-- Lista -->
    <div class="inbox-content">
      <div v-if="loading" class="state-msg"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
      <div v-else-if="items.length === 0" class="state-msg">
        <i class="bi bi-inbox" style="font-size:2rem;opacity:.3"></i>
        <span>Bandeja vacía</span>
      </div>
      <div v-else class="inbox-list">
        <div
          v-for="n in items" :key="n.id"
          class="inbox-item"
          :class="{ unread: !n.is_read, expanded: expanded === n.id, 'access-notif': isAccessNotif(n) }"
          @click="toggleExpand(n)"
        >
          <div class="ii-row">
            <div class="ii-avatar" :class="avatarClass(n)">
              <i :class="avatarIcon(n)"></i>
            </div>
            <div class="ii-main">
              <div class="ii-top">
                <span class="ii-from" :class="{ 'access-from': isAccessNotif(n) }">{{ n.sender_name }}</span>
                <span class="ii-time">{{ fmtAgo(n.created_at) }}</span>
              </div>
              <div class="ii-title">
                <span v-if="isEntryNotif(n)" class="access-badge entry">
                  <i class="bi bi-box-arrow-in-right"></i> Entrada
                </span>
                <span v-else-if="isExitNotif(n)" class="access-badge exit">
                  <i class="bi bi-box-arrow-left"></i> Salida
                </span>
                {{ n.title }}
              </div>
              <div v-if="expanded !== n.id" class="ii-preview">{{ n.message }}</div>
            </div>
            <span v-if="!n.is_read" class="unread-dot"></span>
          </div>
          <div v-if="expanded === n.id" class="ii-body">
            <p class="ii-msg">{{ n.message }}</p>
            <div class="ii-actions" v-if="!isAccessNotif(n)">
              <button class="btn-reply" @click.stop="openReply(n)">
                <i class="bi bi-reply"></i> Responder
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Redactar / Responder -->
    <Teleport to="body">
      <div v-if="showCompose" class="modal-overlay" @click.self="closeCompose">
        <div class="modal-box">
          <div class="modal-header">
            <span>{{ replyTo ? `Responder a ${replyTo.sender_name}` : 'Nuevo mensaje' }}</span>
            <button class="btn-close-modal" @click="closeCompose"><i class="bi bi-x-lg"></i></button>
          </div>
          <div class="modal-body">
            <div class="fg" v-if="!replyTo">
              <label>Destinatario</label>
              <select v-model="form.receiver_id" class="fi">
                <option value="" disabled>Selecciona un usuario</option>
                <option v-for="u in recipients" :key="u.id" :value="u.id">{{ u.nombre }}</option>
              </select>
            </div>
            <div class="fg">
              <label>Asunto</label>
              <input v-model="form.title" class="fi" placeholder="Asunto del mensaje" />
            </div>
            <div class="fg">
              <label>Mensaje</label>
              <textarea v-model="form.message" class="fi" rows="5" placeholder="Escribe tu mensaje..."></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="closeCompose">Cancelar</button>
            <button class="btn-send" @click="sendMessage" :disabled="sending">
              <i class="bi bi-send"></i> {{ sending ? 'Enviando...' : 'Enviar' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

const items      = ref([])
const loading    = ref(false)
const expanded   = ref(null)
const showCompose = ref(false)
const replyTo    = ref(null)
const recipients = ref([])
const sending    = ref(false)

const form = ref({ receiver_id: "", title: "", message: "" })

const unreadCount = computed(() => items.value.filter(n => !n.is_read).length)

async function load() {
  loading.value = true
  try {
    const res = await api.get("/user-notifications/inbox")
    items.value = res.data
  } catch { items.value = [] }
  finally { loading.value = false }
}

async function loadRecipients() {
  try {
    const res = await api.get("/user-notifications/recipients")
    recipients.value = res.data
  } catch { recipients.value = [] }
}

async function toggleExpand(n) {
  if (expanded.value === n.id) { expanded.value = null; return }
  expanded.value = n.id
  if (!n.is_read) {
    try {
      await api.patch(`/user-notifications/${n.id}/read`)
      n.is_read = true
    } catch {}
  }
}

function openReply(n) {
  replyTo.value       = n
  form.value.receiver_id = n.sender_id
  form.value.title    = `Re: ${n.title}`
  form.value.message  = ""
  showCompose.value   = true
}

function closeCompose() {
  showCompose.value  = false
  replyTo.value      = null
  form.value         = { receiver_id: "", title: "", message: "" }
}

async function sendMessage() {
  const { receiver_id, title, message } = form.value
  if (!receiver_id || !title.trim() || !message.trim()) {
    showToast("Completa todos los campos", "warning"); return
  }
  sending.value = true
  try {
    await api.post("/user-notifications/send", { receiver_id, title, message })
    showToast("Mensaje enviado", "success")
    closeCompose()
  } catch (e) {
    showToast(e?.response?.data?.detail || "Error al enviar", "error")
  } finally { sending.value = false }
}

function isEntryNotif(n) { return n.title === "Entrada al sistema" }
function isExitNotif(n)  { return n.title === "Salida del sistema"  }
function isAccessNotif(n){ return isEntryNotif(n) || isExitNotif(n)  }

function avatarIcon(n) {
  if (isEntryNotif(n)) return "bi bi-box-arrow-in-right"
  if (isExitNotif(n))  return "bi bi-box-arrow-left"
  return "bi bi-person-circle"
}
function avatarClass(n) {
  if (isEntryNotif(n)) return "ii-avatar--entry"
  if (isExitNotif(n))  return "ii-avatar--exit"
  return ""
}

function fmtAgo(iso) {
  if (!iso) return ""
  const mins = Math.floor((Date.now() - new Date(iso).getTime()) / 60000)
  if (mins < 1)  return "ahora"
  if (mins < 60) return `hace ${mins} min`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24)  return `hace ${hrs}h`
  const days = Math.floor(hrs / 24)
  if (days < 7)  return `hace ${days}d`
  return new Date(iso).toLocaleDateString("es-CO", { day: "2-digit", month: "short" })
}

onMounted(() => { load(); loadRecipients() })
</script>

<style scoped>
.inbox-wrap { padding: 16px; max-width: 860px; margin: 0 auto; }

/* KPI Bar */
.kpi-bar {
  display: flex; align-items: stretch; gap: 12px;
  margin-bottom: 18px; flex-wrap: wrap;
}
.kpi-card {
  display: flex; align-items: center; gap: 10px;
  background: var(--card-bg, #1e2535);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px; padding: 12px 18px; flex: 1; min-width: 120px;
}
.kpi-card .bi { font-size: 22px; opacity: .7; color: #93c5fd; }
.kpi-alert .bi { color: #fbbf24; }
.kpi-ok    .bi { color: #22c55e; }
.kpi-data  { display: flex; flex-direction: column; line-height: 1.2; }
.kpi-val   { font-size: 22px; font-weight: 800; color: var(--text-primary, #e2e8f0); }
.kpi-lbl   { font-size: 11px; opacity: .55; }
.btn-compose {
  display: flex; align-items: center; gap: 6px;
  padding: 0 20px; background: #2563eb; color: #fff;
  border: none; border-radius: 10px; font-size: 13px; font-weight: 700;
  cursor: pointer; white-space: nowrap; transition: background .15s;
}
.btn-compose:hover { background: #1d4ed8; }

/* Lista */
.inbox-content { background: var(--card-bg, #1e2535); border-radius: 12px; overflow: hidden; border: 1px solid rgba(255,255,255,0.07); }
.state-msg { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 40px; color: rgba(255,255,255,.35); font-size: 13px; }

.inbox-list {}
.inbox-item {
  border-bottom: 1px solid rgba(255,255,255,0.05);
  cursor: pointer; transition: background .15s;
}
.inbox-item:last-child { border-bottom: none; }
.inbox-item:hover { background: rgba(255,255,255,0.04); }
.inbox-item.unread { background: rgba(59,130,246,0.07); }
.inbox-item.expanded { background: rgba(255,255,255,0.06); }

.ii-row { display: flex; align-items: flex-start; gap: 10px; padding: 12px 16px; }
.ii-avatar { font-size: 26px; color: #93c5fd; opacity: .7; flex-shrink: 0; margin-top: 2px; }
.ii-main { flex: 1; min-width: 0; }
.ii-top { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 2px; }
.ii-from { font-size: 12px; font-weight: 700; color: #93c5fd; }
.ii-time { font-size: 10px; color: rgba(255,255,255,.35); flex-shrink: 0; }
.ii-title { font-size: 13px; font-weight: 600; color: var(--text-primary, #e2e8f0); margin-bottom: 2px; }
.ii-preview {
  font-size: 11px; color: rgba(255,255,255,.5);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.unread-dot {
  width: 8px; height: 8px; background: #3b82f6; border-radius: 50%;
  flex-shrink: 0; margin-top: 8px;
}
.ii-body { padding: 0 16px 14px 52px; }
.ii-msg { font-size: 13px; color: rgba(255,255,255,.85); line-height: 1.6; margin: 0 0 10px; white-space: pre-wrap; }
.ii-actions { display: flex; gap: 8px; }
.btn-reply {
  display: flex; align-items: center; gap: 5px;
  background: rgba(37,99,235,.2); border: 1px solid rgba(96,165,250,.3);
  color: #93c5fd; border-radius: 6px; padding: 5px 12px;
  font-size: 12px; cursor: pointer; transition: background .15s;
}
.btn-reply:hover { background: rgba(37,99,235,.35); }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.55);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000; padding: 16px;
}
.modal-box {
  background: #1e2535; border: 1px solid rgba(255,255,255,.12);
  border-radius: 14px; width: 100%; max-width: 520px;
  box-shadow: 0 20px 60px rgba(0,0,0,.5);
}
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px 12px;
  border-bottom: 1px solid rgba(255,255,255,.08);
  font-size: 14px; font-weight: 700; color: #e2e8f0;
}
.btn-close-modal {
  background: none; border: none; color: rgba(255,255,255,.5);
  font-size: 16px; cursor: pointer; padding: 2px 4px; border-radius: 4px;
}
.btn-close-modal:hover { color: #fff; }
.modal-body { padding: 16px 20px; display: flex; flex-direction: column; gap: 12px; }
.fg { display: flex; flex-direction: column; gap: 5px; }
.fg label { font-size: 12px; font-weight: 600; color: rgba(255,255,255,.6); }
.fi {
  background: rgba(255,255,255,.07); border: 1px solid rgba(255,255,255,.12);
  border-radius: 7px; padding: 8px 12px; color: #e2e8f0; font-size: 13px;
  outline: none; resize: vertical;
}
.fi:focus { border-color: rgba(96,165,250,.5); }
.fi option { background: #1e2535; }
.modal-footer {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 12px 20px 16px; border-top: 1px solid rgba(255,255,255,.08);
}
.btn-cancel {
  background: none; border: 1px solid rgba(255,255,255,.15);
  color: rgba(255,255,255,.6); border-radius: 7px; padding: 7px 16px;
  font-size: 13px; cursor: pointer;
}
.btn-send {
  display: flex; align-items: center; gap: 6px;
  background: #2563eb; color: #fff; border: none;
  border-radius: 7px; padding: 7px 18px; font-size: 13px; font-weight: 700;
  cursor: pointer; transition: background .15s;
}
.btn-send:hover:not(:disabled) { background: #1d4ed8; }
.btn-send:disabled { opacity: .5; cursor: default; }

/* ── Notificaciones de acceso ── */
.inbox-item.access-notif { border-left: 3px solid rgba(99,102,241,0.4); }

.ii-avatar--entry { color: #4ade80 !important; }
.ii-avatar--exit  { color: #f87171 !important; }

.access-from { color: #a5b4fc !important; }

.access-badge {
  display: inline-flex; align-items: center; gap: 3px;
  font-size: 10px; font-weight: 700; padding: 1px 6px;
  border-radius: 10px; margin-right: 5px; vertical-align: middle;
}
.access-badge.entry { background: rgba(74,222,128,0.15); color: #4ade80; }
.access-badge.exit  { background: rgba(248,113,113,0.15); color: #f87171; }

.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }

@media (max-width: 600px) {
  .inbox-wrap { padding: 10px; }
  .kpi-bar { gap: 8px; }
  .kpi-card { padding: 10px 12px; }
  .kpi-val { font-size: 18px; }
}
</style>
