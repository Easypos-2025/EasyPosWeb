<template>
  <header class="topbar">

    <!-- ── IZQUIERDA: logo + selector + plan + notif-bell + título ── -->
    <div class="topbar-left">

      <button class="btn-icon btn-menu-left" @click="emit('toggle-sidebar')" title="Menú">
        <i class="bi bi-list"></i>
      </button>

      <div class="brand">
        <img v-if="logo" :src="logo" class="brand-logo" alt="logo" />
      </div>

      <div v-if="logo" class="topbar-divider"></div>

      <select
        v-if="companyStore.companies.length > 1"
        :value="companyStore.selectedCompany?.id"
        @change="onCompanyChange"
        class="company-select"
        title="Cambiar empresa"
      >
        <option v-for="c in companyStore.companies" :key="c.id" :value="c.id">
          {{ c.name }}
        </option>
      </select>

      <!-- Plan + campana de notificaciones (juntos, zona central) -->
      <div class="plan-notif-group">
        <div v-if="companyPlan.plan_name" class="plan-badge">
          <i class="bi bi-award"></i>
          <span class="plan-name">{{ companyPlan.plan_name }}</span>
          <span class="plan-exp">
            {{ companyPlan.expiration_date
              ? 'Vence: ' + formatDate(companyPlan.expiration_date)
              : 'Indefinido' }}
          </span>
        </div>

        <!-- Botón notificaciones / toggle SidebarRight -->
        <button
          class="btn-icon btn-notif-toggle"
          @click="emit('toggle-sidebar-right')"
          title="Notificaciones y panel lateral"
        >
          <i class="bi bi-bell"></i>
          <span v-if="unreadNotif > 0" class="notif-badge">{{ unreadNotif > 99 ? '99+' : unreadNotif }}</span>
        </button>
      </div>

      <!-- Nombre empresa + tipo de negocio -->
      <div class="company-title-wrap">
        <span class="company-title">
          {{ companyStore.selectedCompany?.name || 'EasyPosWeb' }}
        </span>
        <span
          v-if="companyStore.selectedCompany?.business_profile_name"
          class="company-profile-type"
        >({{ companyStore.selectedCompany.business_profile_name }})</span>
      </div>

      <span v-if="companyStore.isSystem" class="sysadmin-badge">ADMIN</span>

    </div>

    <!-- ── DERECHA: usuario + menú dropdown + logout ── -->
    <div class="topbar-right">

      <div class="user-info">
        <i class="bi bi-person-circle"></i>
        <div class="user-text">
          <span class="user-name">{{ user?.nombre }}</span>
          <span class="user-role">{{ user?.role }}</span>
        </div>
      </div>

      <!-- Dropdown dinámico -->
      <div class="dropdown-wrap" ref="dropdownRef">
        <button
          class="btn-icon btn-support"
          @click.stop="toggleDropdown"
          title="Opciones"
        >
          <i class="bi bi-headset"></i>
          <span class="btn-label">Soporte <i class="bi bi-chevron-down btn-arr"></i></span>
        </button>

        <Transition name="dropdown-fade">
          <div v-if="dropdownOpen" class="dropdown-panel">
            <div class="dropdown-header">Opciones</div>

            <button
              v-for="item in menuItems"
              :key="item.id"
              class="dropdown-item"
              :class="{ 'item-disabled': isItemPending(item) }"
              @click="handleMenuAction(item)"
              :title="isItemPending(item) ? 'Próximamente disponible' : item.name"
            >
              <span class="item-icon"><i :class="`bi ${item.icon}`"></i></span>
              <span class="item-name">{{ item.name }}</span>
              <span v-if="isItemPending(item)" class="badge-soon">Próximo</span>
            </button>

            <div v-if="menuItems.length === 0" class="dropdown-empty">
              <i class="bi bi-inbox"></i>
              Sin opciones disponibles
            </div>
          </div>
        </Transition>
      </div>

      <!-- Logout — separado del dropdown por margen -->
      <button class="btn-icon btn-logout" @click="logout" title="Cerrar sesión">
        <i class="bi bi-box-arrow-right"></i>
      </button>

    </div>

  </header>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watchEffect } from "vue"
import { useRouter } from "vue-router"
import { getThemeState } from "@/utils/theme"
import { useCompanyStore } from "@/stores/companyStore"
import api from "@/services/apis"

const emit = defineEmits(["toggle-sidebar", "toggle-sidebar-right"])

const logo         = ref("")
const user         = ref(null)
const theme        = getThemeState()
const companyStore = useCompanyStore()
const router       = useRouter()
const companyPlan  = ref({ plan_name: "", expiration_date: null })
const unreadNotif  = ref(0)
const menuItems    = ref([])
const dropdownOpen = ref(false)
const dropdownRef  = ref(null)

// ── Notificaciones ──────────────────────────────────
async function loadUnreadCount() {
  if (!localStorage.getItem("token")) return
  try {
    const res = await api.get("/task-comments/notifications/unread")
    unreadNotif.value = res.data.filter(n => !n.is_read).length
  } catch {}
}

// ── Plan ────────────────────────────────────────────
async function loadPlan(companyId) {
  if (!companyId) return
  try {
    const res = await api.get(`/company-plan/${companyId}`)
    companyPlan.value = res.data
  } catch {
    companyPlan.value = { plan_name: "", expiration_date: null }
  }
}

// ── Menú dinámico topbar ────────────────────────────
async function loadMenuItems() {
  try {
    const res = await api.get("/topbar-menu")
    menuItems.value = res.data
  } catch {}
}

function isItemPending(item) {
  // Sin ruta Y no es el modal de ayuda
  return !item.route && item.key !== "ayuda"
}

function handleMenuAction(item) {
  dropdownOpen.value = false
  if (isItemPending(item)) return
  if (item.key === "ayuda") {
    // TODO Sprint 7: abrir modal de ayuda
    return
  }
  router.push(item.route)
}

// ── Dropdown ────────────────────────────────────────
function toggleDropdown() {
  dropdownOpen.value = !dropdownOpen.value
}

function handleOutsideClick(e) {
  if (dropdownRef.value && !dropdownRef.value.contains(e.target)) {
    dropdownOpen.value = false
  }
}

// ── Heartbeat (cada 3 min) ──────────────────────────
async function sendHeartbeat() {
  try { await api.patch("/auth/heartbeat/") } catch {}
}

// ── Helpers ─────────────────────────────────────────
function formatDate(iso) {
  if (!iso) return ""
  const [y, m, d] = iso.split("-")
  return `${d}/${m}/${y}`
}

async function onCompanyChange(e) {
  const id      = parseInt(e.target.value)
  const company = companyStore.companies.find(c => c.id === id)
  if (company) {
    await companyStore.setCompany(company)
    await loadPlan(company.id)
  }
}

async function logout() {
  try { await api.post("/auth/logout/") } catch {}
  localStorage.removeItem("token")
  localStorage.removeItem("user")
  localStorage.removeItem("menu")
  localStorage.removeItem("selected_company")
  router.push("/login")
}

watchEffect(() => { if (theme.logo) logo.value = theme.logo })

let notifTimer     = null
let heartbeatTimer = null

onMounted(async () => {
  const stored = localStorage.getItem("user")
  if (stored) {
    user.value = JSON.parse(stored)
    await companyStore.init(user.value)
    await loadPlan(companyStore.selectedCompany?.id)
    await loadMenuItems()
    loadUnreadCount()
    sendHeartbeat()
    notifTimer     = setInterval(loadUnreadCount, 60_000)
    heartbeatTimer = setInterval(sendHeartbeat, 180_000)
  }
  document.addEventListener("click", handleOutsideClick)
})

onUnmounted(() => {
  if (notifTimer)     clearInterval(notifTimer)
  if (heartbeatTimer) clearInterval(heartbeatTimer)
  document.removeEventListener("click", handleOutsideClick)
})
</script>

<style scoped>

.topbar {
  width: 100%;
  height: 54px;
  background: var(--topbar-bg);
  color: var(--topbar-text);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 14px;
  gap: 10px;
  flex-shrink: 0;
  position: relative;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0,0,0,0.25);
}

/* ── IZQUIERDA ── */
.topbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.btn-menu-left { display: none; flex-shrink: 0; }

.brand { display: flex; align-items: center; flex-shrink: 0; }

.brand-logo {
  height: 40px;
  width: auto;
  max-width: 120px;
  object-fit: contain;
  border-radius: 4px;
  filter: drop-shadow(0 1px 2px rgba(0,0,0,0.25));
}

.topbar-divider {
  width: 1px;
  height: 32px;
  background: rgba(255,255,255,0.2);
  flex-shrink: 0;
}

.company-select {
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 6px;
  color: var(--topbar-text);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  outline: none;
  padding: 5px 10px;
  max-width: 220px;
  min-width: 160px;
  flex-shrink: 0;
  text-align: center;
}

.company-select option {
  background: var(--topbar-bg);
  color: var(--topbar-text);
}

/* Plan + campana juntos */
.plan-notif-group {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.plan-badge {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.18);
  border-radius: 20px;
}

.plan-badge .bi { font-size: 13px; color: #fbbf24; }

.plan-name {
  font-size: 12px;
  font-weight: 700;
  color: var(--topbar-text);
  white-space: nowrap;
}

.plan-exp {
  font-size: 10px;
  opacity: 0.7;
  white-space: nowrap;
}

/* Campana de notificaciones */
.btn-notif-toggle {
  position: relative;
  font-size: 18px;
  padding: 6px 8px;
}

.notif-badge {
  position: absolute;
  top: 1px;
  right: 1px;
  min-width: 17px;
  height: 17px;
  background: #ef4444;
  color: #fff;
  font-size: 9px;
  font-weight: 800;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 3px;
  line-height: 1;
  pointer-events: none;
  animation: notif-pop 0.3s ease;
}

@keyframes notif-pop {
  0%   { transform: scale(0.5); opacity: 0; }
  70%  { transform: scale(1.2); }
  100% { transform: scale(1);   opacity: 1; }
}

/* Empresa */
.company-title-wrap {
  display: flex;
  align-items: baseline;
  gap: 5px;
  min-width: 0;
}

.company-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--topbar-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 220px;
  letter-spacing: 0.2px;
}

.company-profile-type {
  font-size: 12px;
  font-weight: 400;
  opacity: 0.65;
  white-space: nowrap;
  flex-shrink: 0;
}

.sysadmin-badge {
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.8px;
  color: #f59e0b;
  background: rgba(245,158,11,0.18);
  border-radius: 4px;
  padding: 2px 6px;
  flex-shrink: 0;
  white-space: nowrap;
}

/* ── DERECHA ── */
.topbar-right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 5px 12px;
  background: rgba(255,255,255,0.1);
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.12);
}

.user-info .bi { font-size: 22px; flex-shrink: 0; }

.user-text { display: flex; flex-direction: column; line-height: 1.2; }
.user-name  { font-size: 13px; font-weight: 600; white-space: nowrap; }
.user-role  { font-size: 10px; opacity: 0.6; white-space: nowrap; }

/* Botones icono */
.btn-icon {
  background: none;
  border: none;
  color: var(--topbar-text);
  font-size: 20px;
  cursor: pointer;
  padding: 6px 8px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: background 0.2s;
  flex-shrink: 0;
}

.btn-icon:hover   { background: rgba(255,255,255,0.12); }
.btn-logout       { margin-left: 6px; }
.btn-logout:hover { background: rgba(239,68,68,0.25); }

/* Dropdown Soporte */
.dropdown-wrap { position: relative; }

.btn-support {
  flex-direction: column;
  gap: 1px;
  padding: 4px 10px;
  border-radius: 8px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.12);
}
.btn-support:hover { background: rgba(255,255,255,0.15); }
.btn-support .bi   { font-size: 17px; }

.btn-arr {
  font-size: 8px;
  vertical-align: middle;
  opacity: 0.7;
}

.btn-label {
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  opacity: 0.85;
  line-height: 1;
}

.dropdown-panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 210px;
  background: #1e2535;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.4);
  padding: 6px;
  z-index: 999;
}

.dropdown-header {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  opacity: 0.45;
  padding: 4px 10px 6px;
  color: var(--topbar-text);
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 9px 12px;
  background: none;
  border: none;
  border-radius: 7px;
  color: var(--topbar-text);
  font-size: 13px;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s;
}

.dropdown-item:hover { background: rgba(255,255,255,0.08); }

.dropdown-item.item-disabled {
  opacity: 0.45;
  cursor: default;
}
.dropdown-item.item-disabled:hover { background: none; }

.item-icon {
  width: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
  opacity: 0.85;
}

.item-name { flex: 1; }

.badge-soon {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.4px;
  padding: 2px 6px;
  border-radius: 10px;
  background: rgba(251,191,36,0.18);
  color: #fbbf24;
  white-space: nowrap;
  flex-shrink: 0;
}

.dropdown-empty {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  font-size: 13px;
  opacity: 0.45;
  justify-content: center;
}

/* Animación dropdown */
.dropdown-fade-enter-active,
.dropdown-fade-leave-active {
  transition: opacity 0.15s, transform 0.15s;
}
.dropdown-fade-enter-from,
.dropdown-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* ── RESPONSIVE ── */
@media (max-width: 768px) {
  .btn-menu-left    { display: flex; }
  .user-text        { display: none; }
  .company-title    { font-size: 13px; max-width: 100px; }
  .company-profile-type { display: none; }
  .topbar-divider   { display: none; }
  .brand-logo       { height: 34px; }
  .plan-name        { display: none; }
  .plan-exp         { display: none; }
  .plan-badge       { padding: 3px 6px; }
  .sysadmin-badge   { display: none; }
}

@media (min-width: 769px) and (max-width: 1100px) {
  .user-role     { display: none; }
  .company-title { max-width: 180px; font-size: 15px; }
  .plan-exp      { display: none; }
}
</style>
