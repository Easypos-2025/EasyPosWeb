<template>
  <div class="outbox-wrap">

    <!-- KPI Bar -->
    <div class="kpi-bar">
      <div class="kpi-card">
        <i class="bi bi-send"></i>
        <div class="kpi-data">
          <span class="kpi-val">{{ items.length }}</span>
          <span class="kpi-lbl">Total enviados</span>
        </div>
      </div>
      <div class="kpi-card kpi-ok">
        <i class="bi bi-eye"></i>
        <div class="kpi-data">
          <span class="kpi-val">{{ readCount }}</span>
          <span class="kpi-lbl">Leídos</span>
        </div>
      </div>
      <div class="kpi-card kpi-warn">
        <i class="bi bi-hourglass-split"></i>
        <div class="kpi-data">
          <span class="kpi-val">{{ items.length - readCount }}</span>
          <span class="kpi-lbl">Pendientes de lectura</span>
        </div>
      </div>
      <button class="btn-compose" @click="showCompose = true">
        <i class="bi bi-pencil-square"></i> Nuevo mensaje
      </button>
    </div>

    <!-- Lista -->
    <div class="outbox-content">
      <div v-if="loading" class="state-msg"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
      <div v-else-if="items.length === 0" class="state-msg">
        <i class="bi bi-send" style="font-size:2rem;opacity:.3"></i>
        <span>No has enviado mensajes aún</span>
      </div>
      <div v-else class="outbox-list">
        <div
          v-for="n in items" :key="n.id"
          class="outbox-item"
          :class="{ expanded: expanded === n.id }"
          @click="toggleExpand(n.id)"
        >
          <div class="oi-row">
            <div class="oi-avatar"><i class="bi bi-person-circle"></i></div>
            <div class="oi-main">
              <div class="oi-top">
                <span class="oi-to">Para: <strong>{{ n.receiver_name }}</strong></span>
                <span class="oi-time">{{ fmtAgo(n.created_at) }}</span>
              </div>
              <div class="oi-title">{{ n.title }}</div>
              <div v-if="expanded !== n.id" class="oi-preview">{{ n.message }}</div>
            </div>
            <span class="read-badge" :class="n.is_read ? 'read' : 'pending'">
              <i class="bi" :class="n.is_read ? 'bi-check2-all' : 'bi-clock'"></i>
              {{ n.is_read ? 'Leído' : 'Pendiente' }}
            </span>
          </div>
          <div v-if="expanded === n.id" class="oi-body">
            <p class="oi-msg">{{ n.message }}</p>
            <div class="oi-actions">
              <button class="btn-delete" @click.stop="deleteMsg(n.id)">
                <i class="bi bi-trash"></i> Eliminar
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Redactar -->
    <Teleport to="body">
      <div v-if="showCompose" class="modal-overlay" @click.self="closeCompose">
        <div class="modal-box">
          <div class="modal-header">
            <span>Nuevo mensaje</span>
            <button class="btn-close-modal" @click="closeCompose"><i class="bi bi-x-lg"></i></button>
          </div>
          <div class="modal-body">
            <div class="fg">
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
import Swal from 'sweetalert2'

const items      = ref([])
const loading    = ref(false)
const expanded   = ref(null)
const showCompose = ref(false)
const recipients = ref([])
const sending    = ref(false)

const form = ref({ receiver_id: "", title: "", message: "" })

const readCount = computed(() => items.value.filter(n => n.is_read).length)

async function load() {
  loading.value = true
  try {
    const res = await api.get("/user-notifications/outbox")
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

function toggleExpand(id) {
  expanded.value = expanded.value === id ? null : id
}

async function deleteMsg(id) {
  const result = await Swal.fire({
    title: '¿Eliminar mensaje?',
    text: '¿Eliminar este mensaje enviado?',
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#e11d48',
    confirmButtonText: 'Sí, eliminar',
    cancelButtonText: 'Cancelar',
  })
  if (!result.isConfirmed) return
  try {
    await api.delete(`/user-notifications/${id}`)
    items.value = items.value.filter(n => n.id !== id)
    if (expanded.value === id) expanded.value = null
    showToast("Mensaje eliminado", "success")
  } catch { showToast("Error al eliminar", "error") }
}

function closeCompose() {
  showCompose.value = false
  form.value        = { receiver_id: "", title: "", message: "" }
}

async function sendMessage() {
  const { receiver_id, title, message } = form.value
  if (!receiver_id || !title.trim() || !message.trim()) {
    showToast("Completa todos los campos", "warning"); return
  }
  sending.value = true
  try {
    const res = await api.post("/user-notifications/send", { receiver_id, title, message })
    items.value.unshift(res.data)
    showToast("Mensaje enviado", "success")
    closeCompose()
  } catch (e) {
    showToast(e?.response?.data?.detail || "Error al enviar", "error")
  } finally { sending.value = false }
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
.outbox-wrap { padding: 16px; max-width: 860px; margin: 0 auto; }

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
.kpi-ok   .bi { color: #22c55e; }
.kpi-warn .bi { color: #fbbf24; }
.kpi-data { display: flex; flex-direction: column; line-height: 1.2; }
.kpi-val  { font-size: 22px; font-weight: 800; color: var(--text-primary, #e2e8f0); }
.kpi-lbl  { font-size: 11px; opacity: .55; }
.btn-compose {
  display: flex; align-items: center; gap: 6px;
  padding: 0 20px; background: #2563eb; color: #fff;
  border: none; border-radius: 10px; font-size: 13px; font-weight: 700;
  cursor: pointer; white-space: nowrap; transition: background .15s;
}
.btn-compose:hover { background: #1d4ed8; }

.outbox-content { background: var(--card-bg, #1e2535); border-radius: 12px; overflow: hidden; border: 1px solid rgba(255,255,255,0.07); }
.state-msg { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 40px; color: rgba(255,255,255,.35); font-size: 13px; }

.outbox-item {
  border-bottom: 1px solid rgba(255,255,255,0.05);
  cursor: pointer; transition: background .15s;
}
.outbox-item:last-child { border-bottom: none; }
.outbox-item:hover { background: rgba(255,255,255,0.04); }
.outbox-item.expanded { background: rgba(255,255,255,0.06); }

.oi-row { display: flex; align-items: flex-start; gap: 10px; padding: 12px 16px; }
.oi-avatar { font-size: 26px; color: #93c5fd; opacity: .7; flex-shrink: 0; margin-top: 2px; }
.oi-main { flex: 1; min-width: 0; }
.oi-top { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 2px; }
.oi-to { font-size: 12px; color: rgba(255,255,255,.55); }
.oi-to strong { color: #93c5fd; }
.oi-time { font-size: 10px; color: rgba(255,255,255,.35); flex-shrink: 0; }
.oi-title { font-size: 13px; font-weight: 600; color: var(--text-primary, #e2e8f0); margin-bottom: 2px; }
.oi-preview { font-size: 11px; color: rgba(255,255,255,.5); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.read-badge {
  display: flex; align-items: center; gap: 4px;
  font-size: 10px; font-weight: 700; padding: 3px 8px;
  border-radius: 10px; white-space: nowrap; flex-shrink: 0; margin-top: 4px;
}
.read-badge.read    { background: rgba(34,197,94,.15); color: #22c55e; }
.read-badge.pending { background: rgba(251,191,36,.15); color: #fbbf24; }

.oi-body { padding: 0 16px 14px 52px; }
.oi-msg { font-size: 13px; color: rgba(255,255,255,.85); line-height: 1.6; margin: 0 0 10px; white-space: pre-wrap; }
.oi-actions { display: flex; }
.btn-delete {
  display: flex; align-items: center; gap: 5px;
  background: rgba(239,68,68,.15); border: 1px solid rgba(239,68,68,.3);
  color: #fca5a5; border-radius: 6px; padding: 5px 12px;
  font-size: 12px; cursor: pointer; transition: background .15s;
}
.btn-delete:hover { background: rgba(239,68,68,.28); }

/* Modal (idéntico al InboxView) */
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
  padding: 16px 20px 12px; border-bottom: 1px solid rgba(255,255,255,.08);
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

.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }

@media (max-width: 600px) {
  .outbox-wrap { padding: 10px; }
  .kpi-bar { gap: 8px; }
  .kpi-card { padding: 10px 12px; }
  .kpi-val { font-size: 18px; }
  .read-badge { display: none; }
}
</style>
