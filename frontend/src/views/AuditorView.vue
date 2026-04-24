<template>
  <div class="page-container">

    <!-- ENCABEZADO -->
    <div class="page-header">
      <div>
        <h1 class="page-title">
          <i class="bi bi-binoculars"></i> Supervisión de Tareas
        </h1>
        <p class="page-subtitle">Seguimiento, asignación y comunicación con Task Leaders</p>
      </div>
    </div>

    <!-- MINI STATS -->
    <div class="mini-stats" v-if="stats">
      <div class="stat-chip" v-for="s in statChips" :key="s.label">
        <span class="chip-num" :style="{ color: s.color }">{{ s.value }}</span>
        <span class="chip-label">{{ s.label }}</span>
      </div>
    </div>

    <!-- FILTROS -->
    <div class="filters-row">
      <input v-model="search" class="form-control" placeholder="Buscar tarea..."
        style="max-width:240px" />

      <select v-model="filterStatus" class="form-select" style="max-width:170px">
        <option value="">Todos los estados</option>
        <option v-for="s in statuses" :key="s.id" :value="s.id">{{ s.name }}</option>
      </select>

      <select v-model="filterUser" class="form-select" style="max-width:180px">
        <option value="">Todos los líderes</option>
        <option :value="-1">Sin asignar</option>
        <option v-for="u in taskLeaders" :key="u.id" :value="u.id">{{ u.nombre }}</option>
      </select>
    </div>

    <!-- TABLA PRINCIPAL -->
    <div class="table-card">
      <div v-if="loading" class="table-loading">
        <i class="bi bi-arrow-repeat spin"></i> Cargando...
      </div>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Tarea</th>
            <th>Activo</th>
            <th class="text-center">Estado</th>
            <th>Task Leader</th>
            <th class="text-center">Avance</th>
            <th>Vence</th>
            <th class="text-center">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in filtered" :key="t.id"
            :class="{ 'row-overdue': isOverdue(t) }">
            <td class="text-muted">{{ t.id }}</td>
            <td>
              <strong>{{ t.title }}</strong>
              <div v-if="t.description" class="task-desc">{{ t.description }}</div>
            </td>
            <td class="text-muted">{{ assetName(t.asset_id) }}</td>
            <td class="text-center">
              <span class="status-badge" :class="statusClass(t.status_id)">
                {{ t.status_name }}
              </span>
            </td>
            <td>
              <span v-if="t.assigned_to" class="user-chip">
                <i class="bi bi-person-fill"></i>
                {{ userName(t.assigned_to) }}
              </span>
              <span v-else class="text-muted">Sin asignar</span>
            </td>
            <td class="text-center">
              <div class="progress-mini">
                <div class="progress-track-sm">
                  <div class="progress-fill-sm"
                    :class="t.progress === 100 ? 'fill-green' : 'fill-blue'"
                    :style="{ width: t.progress + '%' }"></div>
                </div>
                <span class="prog-num">{{ t.progress }}%</span>
              </div>
            </td>
            <td :class="isOverdue(t) ? 'text-danger' : 'text-muted'">
              <span v-if="t.due_date">
                <i v-if="isOverdue(t)" class="bi bi-exclamation-triangle-fill me-1"></i>
                {{ fmtDate(t.due_date) }}
              </span>
              <span v-else>—</span>
            </td>
            <td class="text-center">
              <div class="action-row">
                <button class="btn btn-warning btn-sm" @click="openAssign(t)"
                  title="Asignar Task Leader">
                  <i class="bi bi-person-plus"></i>
                </button>
                <button class="btn btn-info btn-sm" @click="openMessage(t)"
                  title="Enviar mensaje al Task Leader">
                  <i class="bi bi-chat-dots"></i>
                </button>
                <button class="btn btn-secondary btn-sm"
                  @click="$router.push(`/tasks/${t.id}/evidencias`)"
                  title="Ver evidencias">
                  <i class="bi bi-camera"></i>
                </button>
                <button v-if="t.asset_id" class="btn btn-secondary btn-sm"
                  @click="$router.push(`/assets/${t.asset_id}/historial`)"
                  title="Historial del activo">
                  <i class="bi bi-clock-history"></i>
                </button>
                <button class="btn btn-secondary btn-sm"
                  @click="$router.push(`/tasks/${t.id}/reportes`)"
                  title="Reportes de avance">
                  <i class="bi bi-bar-chart-steps"></i>
                </button>
                <button class="btn btn-secondary btn-sm"
                  @click="$router.push(`/tasks/${t.id}/analisis`)"
                  title="Análisis de ejecución">
                  <i class="bi bi-graph-up-arrow"></i>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="filtered.length === 0">
            <td colspan="8" class="text-center text-muted py-4">
              No hay tareas con estos filtros
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- MODAL ASIGNAR TASK LEADER -->
    <div v-if="showAssign" class="modal-overlay" @click.self="showAssign = false">
      <div class="modal-box">
        <div class="modal-header-bar">
          <h2><i class="bi bi-person-plus"></i> Asignar Task Leader</h2>
          <button class="btn-close-x" @click="showAssign = false">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>
        <div class="modal-body-area">
          <div class="task-info-block">
            <strong>{{ assigningTask?.title }}</strong>
          </div>
          <div class="fg">
            <label>Selecciona el Task Leader responsable</label>
            <select v-model="assignUserId" class="form-select">
              <option :value="null">— Sin asignar —</option>
              <option v-for="u in taskLeaders" :key="u.id" :value="u.id">
                {{ u.nombre }}
              </option>
            </select>
          </div>
        </div>
        <div class="modal-footer-bar">
          <button class="btn btn-secondary" @click="showAssign = false">Cancelar</button>
          <button class="btn btn-primary" @click="saveAssign" :disabled="saving">
            <i v-if="saving" class="bi bi-arrow-repeat spin"></i>
            {{ saving ? 'Guardando...' : 'Asignar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL ENVIAR MENSAJE -->
    <div v-if="showMsg" class="modal-overlay" @click.self="showMsg = false">
      <div class="modal-box">
        <div class="modal-header-bar">
          <h2><i class="bi bi-chat-dots"></i> Enviar mensaje al Task Leader</h2>
          <button class="btn-close-x" @click="showMsg = false">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>
        <div class="modal-body-area">

          <div class="task-info-block">
            <strong>{{ msgTask?.title }}</strong>
            <span v-if="msgTask?.assigned_to" class="ms-2 text-muted">
              → {{ userName(msgTask?.assigned_to) }}
            </span>
          </div>

          <!-- Historial de comentarios -->
          <div class="comments-history" v-if="comments.length > 0">
            <div v-for="c in comments" :key="c.id"
              class="comment-item"
              :class="c.is_notification ? 'comment-notif' : 'comment-note'"
            >
              <div class="comment-header">
                <span class="comment-who">
                  <i class="bi" :class="c.is_notification ? 'bi-megaphone' : 'bi-chat'"></i>
                  {{ c.is_notification ? 'Notificación' : 'Comentario' }}
                </span>
                <span class="comment-date">{{ fmtDateTime(c.created_at) }}</span>
              </div>
              <p class="comment-text">{{ c.comment }}</p>
            </div>
          </div>
          <div v-else class="empty-comments">
            <i class="bi bi-chat-square-text"></i> Sin mensajes previos en esta tarea
          </div>

          <div class="fg">
            <label>Nuevo mensaje para el Task Leader</label>
            <textarea v-model="msgText" class="form-control" rows="3"
              placeholder="Escribe aquí tu mensaje, consulta o instrucción..." />
          </div>

          <div class="msg-type">
            <label>
              <input type="checkbox" v-model="msgIsNotif" />
              Marcar como <strong>notificación urgente</strong>
              (aparece en el panel lateral del Task Leader)
            </label>
          </div>
        </div>
        <div class="modal-footer-bar">
          <button class="btn btn-secondary" @click="showMsg = false">Cancelar</button>
          <button class="btn btn-primary" @click="sendMessage" :disabled="sendingMsg">
            <i v-if="sendingMsg" class="bi bi-arrow-repeat spin"></i>
            <i v-else class="bi bi-send"></i>
            {{ sendingMsg ? 'Enviando...' : 'Enviar mensaje' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

const tasks    = ref([])
const statuses = ref([])
const assets   = ref([])
const users    = ref([])
const stats    = ref(null)
const comments = ref([])
const loading  = ref(true)

const search       = ref("")
const filterStatus = ref("")
const filterUser   = ref("")

const showAssign  = ref(false)
const assigningTask = ref(null)
const assignUserId  = ref(null)
const saving      = ref(false)

const showMsg     = ref(false)
const msgTask     = ref(null)
const msgText     = ref("")
const msgIsNotif  = ref(false)
const sendingMsg  = ref(false)

// Solo usuarios con rol Task Leader / no SYSADMIN
const taskLeaders = computed(() =>
  users.value.filter(u => !u.is_system)
)

const statChips = computed(() => {
  if (!stats.value) return []
  return [
    { label: "Total",       value: stats.value.total,      color: "#1e293b" },
    { label: "Pendientes",  value: stats.value.pendiente,  color: "#f59e0b" },
    { label: "En Progreso", value: stats.value.progreso,   color: "#22c55e" },
    { label: "Atrasadas",   value: stats.value.atrasadas,  color: "#ef4444" },
    { label: "Finalizadas", value: stats.value.finalizada, color: "#065f46" },
  ]
})

const filtered = computed(() =>
  tasks.value.filter(t => {
    const matchSearch = !search.value ||
      t.title.toLowerCase().includes(search.value.toLowerCase())
    const matchStatus = !filterStatus.value ||
      t.status_id === Number(filterStatus.value)
    const matchUser = filterUser.value === ""
      ? true
      : filterUser.value === -1
        ? !t.assigned_to
        : t.assigned_to === Number(filterUser.value)
    return matchSearch && matchStatus && matchUser
  })
)

const STATUS_CLASSES = {
  1: "badge-orange", 2: "badge-blue", 3: "badge-green",
  4: "badge-purple", 5: "badge-darkgreen", 6: "badge-red",
}
function statusClass(id) { return STATUS_CLASSES[id] || "badge-gray" }
function assetName(id)   { return assets.value.find(a => a.id === id)?.name || "—" }
function userName(id)    { return users.value.find(u => u.id === id)?.nombre || "—" }
function isOverdue(t)    { return t.due_date && new Date(t.due_date) < new Date() && ![5,6].includes(t.status_id) }
function fmtDate(iso)    { return iso ? new Date(iso).toLocaleDateString("es-CO", { day:"2-digit", month:"short", year:"numeric" }) : "" }
function fmtDateTime(iso){ return iso ? new Date(iso).toLocaleString("es-CO", { day:"2-digit", month:"short", hour:"2-digit", minute:"2-digit" }) : "" }

async function load() {
  loading.value = true
  try {
    const [taskRes, statRes, assetsRes, usersRes, statsRes] = await Promise.all([
      api.get("/tasks/"),
      api.get("/task-status/"),
      api.get("/assets/"),
      api.get("/users/"),
      api.get("/tasks/stats"),
    ])
    tasks.value    = taskRes.data
    statuses.value = statRes.data
    assets.value   = assetsRes.data
    users.value    = usersRes.data
    stats.value    = statsRes.data
  } catch {
    showToast("Error cargando datos", "error")
  } finally {
    loading.value = false
  }
}

// ── ASIGNAR ──────────────────────────────────────────────────
function openAssign(task) {
  assigningTask.value = task
  assignUserId.value  = task.assigned_to || null
  showAssign.value    = true
}

async function saveAssign() {
  saving.value = true
  try {
    await api.put(`/tasks/${assigningTask.value.id}`, {
      assigned_to: assignUserId.value,
      status_id:   assignUserId.value ? 2 : 1   // → Asignada o Pendiente
    })
    showToast("Tarea asignada correctamente", "success")
    showAssign.value = false
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error asignando", "error")
  } finally {
    saving.value = false
  }
}

// ── MENSAJE ──────────────────────────────────────────────────
async function openMessage(task) {
  msgTask.value    = task
  msgText.value    = ""
  msgIsNotif.value = false
  showMsg.value    = true
  try {
    const res = await api.get(`/task-comments/${task.id}`)
    comments.value = res.data
  } catch {
    comments.value = []
  }
}

async function sendMessage() {
  if (!msgText.value.trim()) {
    showToast("Escribe un mensaje antes de enviar", "warning"); return
  }
  sendingMsg.value = true
  try {
    await api.post(`/task-comments/${msgTask.value.id}`, {
      comment:         msgText.value.trim(),
      is_notification: msgIsNotif.value,
    })
    showToast("Mensaje enviado al Task Leader", "success")
    showMsg.value = false
  } catch (e) {
    showToast(e.response?.data?.detail || "Error enviando mensaje", "error")
  } finally {
    sendingMsg.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1300px; }
.page-header    { margin-bottom: 18px; }
.page-title     { font-size: 20px; font-weight: 700; color: #1e293b; display:flex; align-items:center; gap:8px; margin-bottom:4px; }
.page-subtitle  { font-size: 13px; color: #64748b; }

/* MINI STATS */
.mini-stats { display:flex; flex-wrap:wrap; gap:10px; margin-bottom:18px; }
.stat-chip  { background:#fff; border-radius:10px; padding:10px 16px; box-shadow:0 1px 4px rgba(0,0,0,0.07); display:flex; align-items:baseline; gap:8px; }
.chip-num   { font-size:22px; font-weight:800; }
.chip-label { font-size:12px; color:#94a3b8; }

/* FILTROS */
.filters-row { display:flex; gap:10px; margin-bottom:14px; flex-wrap:wrap; }

/* TABLE */
.table-card   { background:#fff; border-radius:14px; box-shadow:0 1px 6px rgba(0,0,0,0.08); overflow:hidden; }
.table-loading{ padding:40px; text-align:center; color:#94a3b8; }
.data-table   { width:100%; border-collapse:collapse; font-size:13px; }
.data-table th{ background:#f8fafc; color:#475569; font-weight:600; font-size:11px; text-transform:uppercase; letter-spacing:0.4px; padding:11px 12px; border-bottom:1px solid #e2e8f0; }
.data-table td{ padding:11px 12px; border-bottom:1px solid #f1f5f9; vertical-align:middle; }
.data-table tr:last-child td { border-bottom:none; }
.data-table tr:hover td { background:#f8fafc; }
.row-overdue td { background:#fff5f5 !important; }

.text-center  { text-align:center; }
.text-muted   { color:#94a3b8 !important; font-size:12px; }
.text-danger  { color:#ef4444 !important; font-size:12px; }
.task-desc    { font-size:11px; color:#94a3b8; margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:240px; }

/* STATUS BADGES */
.status-badge    { font-size:10px; font-weight:700; padding:2px 9px; border-radius:20px; white-space:nowrap; }
.badge-orange    { background:#fff7ed; color:#c2410c; }
.badge-blue      { background:#dbeafe; color:#1e40af; }
.badge-green     { background:#dcfce7; color:#16a34a; }
.badge-purple    { background:#f3e8ff; color:#7c3aed; }
.badge-darkgreen { background:#d1fae5; color:#065f46; }
.badge-red       { background:#fef2f2; color:#b91c1c; }
.badge-gray      { background:#f1f5f9; color:#64748b; }

/* USER CHIP */
.user-chip { display:inline-flex; align-items:center; gap:4px; font-size:12px; color:#475569; background:#f1f5f9; border-radius:20px; padding:2px 8px; }

/* PROGRESS */
.progress-mini { display:flex; align-items:center; gap:5px; justify-content:center; }
.progress-track-sm { width:50px; height:5px; background:#e2e8f0; border-radius:3px; overflow:hidden; }
.progress-fill-sm  { height:100%; border-radius:3px; }
.fill-blue  { background:#3b82f6; }
.fill-green { background:#22c55e; }
.prog-num   { font-size:11px; color:#64748b; min-width:26px; }

/* ACTIONS */
.action-row { display:flex; gap:4px; justify-content:center; flex-wrap:wrap; }

/* MODAL */
.modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.45); display:flex; align-items:center; justify-content:center; z-index:1000; }
.modal-box     { background:#fff; border-radius:16px; width:540px; max-width:95vw; max-height:90vh; display:flex; flex-direction:column; box-shadow:0 20px 60px rgba(0,0,0,0.2); }
.modal-header-bar  { display:flex; align-items:center; justify-content:space-between; padding:16px 22px 12px; border-bottom:1px solid #f1f5f9; flex-shrink:0; }
.modal-header-bar h2 { font-size:15px; font-weight:700; color:#1e293b; margin:0; display:flex; align-items:center; gap:7px; }
.modal-body-area   { padding:18px 22px; overflow-y:auto; display:flex; flex-direction:column; gap:14px; }
.modal-footer-bar  { padding:12px 22px 16px; display:flex; justify-content:flex-end; gap:8px; border-top:1px solid #f1f5f9; flex-shrink:0; }

.task-info-block { padding:10px 14px; background:#f8fafc; border-radius:10px; font-size:13px; }
.fg label { font-size:13px; font-weight:600; color:#374151; }
.btn-close-x { background:none; border:none; font-size:17px; cursor:pointer; color:#94a3b8; }
.btn-close-x:hover { color:#1e293b; }

/* COMENTARIOS */
.comments-history { max-height:200px; overflow-y:auto; display:flex; flex-direction:column; gap:8px; }
.comment-item    { border-radius:10px; padding:10px 14px; }
.comment-notif   { background:#fff7ed; border:1px solid #fed7aa; }
.comment-note    { background:#f8fafc; border:1px solid #e2e8f0; }
.comment-header  { display:flex; justify-content:space-between; margin-bottom:4px; }
.comment-who     { font-size:11px; font-weight:700; color:#475569; display:flex; align-items:center; gap:4px; }
.comment-date    { font-size:10px; color:#94a3b8; }
.comment-text    { font-size:13px; color:#1e293b; margin:0; line-height:1.5; }
.empty-comments  { padding:16px; text-align:center; color:#94a3b8; font-size:13px; display:flex; align-items:center; gap:6px; justify-content:center; }

.msg-type label  { display:flex; align-items:center; gap:8px; font-size:13px; cursor:pointer; color:#475569; }
.msg-type input  { width:15px; height:15px; }

.spin { display:inline-block; animation:spin 0.8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
</style>
