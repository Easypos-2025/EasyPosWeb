<template>
  <div class="footer-content">

    <!-- ── IZQUIERDA: marca + estado + chips (en línea) ── -->
    <div class="footer-left">
      <div class="footer-brand">
        <img
          src="/src/assets/logo.png"
          class="footer-logo"
          alt="EasyPosWeb"
          @error="e => e.target.style.display='none'"
        />
        <span class="footer-brand-name">EasyPosWeb</span>
      </div>

      <span class="footer-sep">|</span>
      <span class="footer-version">v{{ version }}</span>
      <span class="footer-sep">|</span>

      <span v-if="!online" class="footer-status offline">● Sin internet</span>
      <span v-else class="footer-status" :class="apiStatus ? 'ok' : 'warn'">
        ● {{ apiStatus ? 'API OK' : 'API sin respuesta' }}
      </span>

      <!-- Chips justo después del estado API -->
      <template v-if="chipsVisible">
        <span class="footer-sep">|</span>

        <!-- Chip 1: empresas online (solo SYSADMIN) -->
        <div
          v-if="companyStore.isSystem && onlineCompanies !== null"
          class="chip"
          :class="{ 'flash-blue': chip1Flash }"
          title="Empresas con sesión activa"
        >
          <i class="bi bi-building"></i>
          <span>{{ onlineCompanies }}</span>
        </div>

        <!-- Chip 3: usuarios conectados — siempre verde -->
        <div
          v-if="onlineUsers !== null"
          class="chip chip-green"
          title="Usuarios con sesión activa"
        >
          <i class="bi bi-people-fill"></i>
          <span>{{ onlineUsers }}</span>
        </div>
      </template>
    </div>

    <!-- ── DERECHA: copyright ── -->
    <span class="footer-copy">© 2020 EasyPosWeb</span>

    <!-- ── TOAST FLOTANTE: info del asociado nuevo (20 seg) ── -->
    <Transition name="assoc-toast">
      <div v-if="associateToast" class="assoc-toast">
        <div class="assoc-toast-body">
          <i class="bi bi-stars assoc-icon"></i>
          <div class="assoc-info">
            <span class="assoc-label">Nuevo asociado</span>
            <span class="assoc-name">{{ associateToast.name }}</span>
            <span class="assoc-meta">
              {{ associateToast.business_profile || 'General' }}
              <span class="assoc-sep">·</span>
              {{ associateToast.plan }}
            </span>
          </div>
        </div>
        <!-- Barra de progreso fija en 20 seg -->
        <div :key="toastKey" class="assoc-progress"></div>
      </div>
    </Transition>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from "vue"
import { useCompanyStore } from "@/stores/companyStore"
import api from "@/services/apis"

const companyStore = useCompanyStore()
const version      = import.meta.env.VITE_APP_VERSION || "1.0.0"
const online       = ref(navigator.onLine)
const apiStatus    = ref(false)

const TOAST_MS = 20_000   // duración del toast: 20 segundos (fijo)

// ── Chips data ────────────────────────────────────────
const onlineCompanies = ref(null)
const onlineUsers     = ref(null)
const associates      = ref([])
const tickerIndex     = ref(0)
const intervalSec     = ref(45)

const chipsVisible = computed(() =>
  (companyStore.isSystem && onlineCompanies.value !== null) ||
  onlineUsers.value !== null
)

// ── Flash chip 1 ─────────────────────────────────────
const chip1Flash = ref(false)

function triggerFlash(chipRef) {
  chipRef.value = true
  setTimeout(() => { chipRef.value = false }, intervalSec.value * 1000)
}

// ── Toast flotante asociado ───────────────────────────
const associateToast = ref(null)
const toastKey       = ref(0)
let   toastHideTimer = null

function showToastAssociate(assoc) {
  if (toastHideTimer) clearTimeout(toastHideTimer)
  associateToast.value = assoc
  toastKey.value++
  toastHideTimer = setTimeout(() => {
    associateToast.value = null
  }, TOAST_MS)
}

// ── API health ────────────────────────────────────────
const checkApi = async () => {
  try { await api.get("/auth/health/"); apiStatus.value = true }
  catch { apiStatus.value = false }
}

// ── API chips ─────────────────────────────────────────
async function loadOnlineCompanies() {
  if (!companyStore.isSystem) return
  try {
    const prev = onlineCompanies.value
    const res  = await api.get("/footer/online-companies")
    onlineCompanies.value = res.data.count
    if (prev !== null && prev !== res.data.count) triggerFlash(chip1Flash)
  } catch { onlineCompanies.value = 0 }
}

async function loadAssociates() {
  try {
    const res = await api.get("/footer/new-associates")
    intervalSec.value = res.data.interval_sec || 45
    associates.value  = res.data.associates   || []
  } catch {}
}

async function loadOnlineUsers() {
  try {
    const res = await api.get("/footer/online-users")
    onlineUsers.value = res.data.count
  } catch { onlineUsers.value = 0 }
}

// ── Ticker ────────────────────────────────────────────
let tickerTimer  = null
let refreshTimer = null
let apiTimer     = null

function startTicker() {
  if (tickerTimer) clearInterval(tickerTimer)
  if (associates.value.length === 0) return

  showToastAssociate(associates.value[tickerIndex.value])

  tickerTimer = setInterval(() => {
    tickerIndex.value = (tickerIndex.value + 1) % associates.value.length
    showToastAssociate(associates.value[tickerIndex.value])
  }, intervalSec.value * 1000)
}

// ── Conectividad ──────────────────────────────────────
window.addEventListener("online",  () => { online.value = true  })
window.addEventListener("offline", () => { online.value = false })

watch(() => companyStore.isSystem, (val) => {
  if (val !== null) loadOnlineCompanies()
}, { immediate: true })

// ── Montaje ───────────────────────────────────────────
onMounted(async () => {
  checkApi()
  apiTimer = setInterval(checkApi, 10_000)

  await loadAssociates()
  startTicker()
  await loadOnlineUsers()

  refreshTimer = setInterval(async () => {
    await loadOnlineCompanies()
    await loadOnlineUsers()
  }, 60_000)

  setInterval(async () => {
    const prev = intervalSec.value
    await loadAssociates()
    if (prev !== intervalSec.value) startTicker()
  }, 300_000)
})

onUnmounted(() => {
  if (tickerTimer)   clearInterval(tickerTimer)
  if (refreshTimer)  clearInterval(refreshTimer)
  if (apiTimer)      clearInterval(apiTimer)
  if (toastHideTimer) clearTimeout(toastHideTimer)
})
</script>

<style scoped>

.footer-content {
  display: flex;
  align-items: center;
  height: 40px;
  flex-shrink: 0;
  background: #111827;
  color: rgba(255,255,255,0.65);
  font-size: 12px;
  letter-spacing: 0.2px;
  padding: 0 16px;
  position: relative;
}

/* ── IZQUIERDA ── */
.footer-left {
  display: flex;
  align-items: center;
  gap: 7px;
  flex-shrink: 0;
  min-width: 0;
}

.footer-brand       { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.footer-logo        { height: 22px; width: auto; object-fit: contain; opacity: 0.85; }
.footer-brand-name  { font-size: 12px; font-weight: 700; letter-spacing: 0.5px; color: rgba(255,255,255,0.8); white-space: nowrap; }
.footer-sep         { opacity: 0.2; font-size: 11px; flex-shrink: 0; }
.footer-version     { opacity: 0.5; font-size: 11px; white-space: nowrap; }
.footer-status      { font-size: 11px; white-space: nowrap; }
.footer-status.ok   { color: #4ade80; }
.footer-status.warn { color: #fb923c; }
.footer-status.offline { color: #f87171; }

/* ── CHIPS (inline en footer-left) ── */
.chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 20px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.06);
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
  flex-shrink: 0;
  transition: background 0.5s ease, border-color 0.5s ease;
  cursor: default;
}

.chip .bi { font-size: 12px; opacity: 0.8; }

.chip.flash-blue  { background: rgba(99,179,237,0.22); border-color: rgba(99,179,237,0.55); }
.chip.flash-green { background: rgba(52,211,153,0.22); border-color: rgba(52,211,153,0.55); }

/* Chip 3: siempre verde */
.chip-green {
  background: rgba(34,197,94,0.15);
  border-color: rgba(34,197,94,0.4);
  color: #4ade80;
}
.chip-green .bi { opacity: 1; color: #4ade80; }

/* ── COPYRIGHT ── */
.footer-copy { margin-left: auto; white-space: nowrap; opacity: 0.35; font-size: 11px; flex-shrink: 0; padding-left: 12px; }

/* ── TOAST FLOTANTE ── */
.assoc-toast {
  position: fixed;
  bottom: 50px;
  right: 20px;
  width: 260px;
  background: #1e293b;
  border: 1px solid rgba(52,211,153,0.35);
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0,0,0,0.4);
  z-index: 500;
}

.assoc-toast-body {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
}

.assoc-icon { font-size: 20px; color: #34d399; flex-shrink: 0; }

.assoc-info { display: flex; flex-direction: column; gap: 1px; min-width: 0; }

.assoc-label {
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: #34d399;
  opacity: 0.8;
}

.assoc-name {
  font-size: 13px;
  font-weight: 700;
  color: rgba(255,255,255,0.95);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.assoc-meta {
  font-size: 11px;
  color: rgba(255,255,255,0.45);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: flex;
  align-items: center;
  gap: 4px;
}
.assoc-sep { opacity: 0.35; }

/* Barra de progreso: 20 seg fijos */
.assoc-progress {
  height: 3px;
  background: linear-gradient(90deg, #34d399, #059669);
  width: 100%;
  animation: shrink-bar 20s linear forwards;
}

@keyframes shrink-bar {
  from { width: 100%; }
  to   { width: 0%;   }
}

/* Transición del toast */
.assoc-toast-enter-active,
.assoc-toast-leave-active { transition: opacity 0.3s ease, transform 0.3s ease; }
.assoc-toast-enter-from,
.assoc-toast-leave-to     { opacity: 0; transform: translateY(10px); }

/* ── RESPONSIVE ── */
@media (max-width: 768px) {
  .footer-copy    { display: none; }
  .footer-version { display: none; }
  .footer-brand-name { display: none; }
  .footer-content { padding: 0 10px; }
  .assoc-toast    { width: 220px; right: 10px; bottom: 48px; }
}
</style>
