<template>
  <header class="topbar">

    <!-- ── IZQUIERDA: logo + selector + plan + notif-bell + título ── -->
    <div class="topbar-left">

      <button class="btn-icon btn-menu-left" @click="emit('toggle-sidebar')" title="Menú">
        <i class="bi bi-list"></i>
      </button>

      <!-- Logo + nombre empresa agrupados (en móvil apila verticalmente) -->
      <div class="brand-block">
        <div class="brand">
          <img v-if="logo" :src="logo" class="brand-logo" alt="logo" />
        </div>
        <span class="brand-company-name">
          {{ companyStore.selectedCompany?.name || '' }}
        </span>
      </div>

      <div v-if="logo" class="topbar-divider"></div>

      <!-- Desktop: select normal -->
      <select
        v-if="companyStore.companies.length > 1"
        :value="companyStore.selectedCompany?.id"
        @change="onCompanyChange"
        class="company-select company-select-desktop"
        title="Cambiar empresa"
      >
        <option v-for="c in companyStore.companies" :key="c.id" :value="c.id">
          {{ c.name }}
        </option>
      </select>

      <!-- Móvil: icono compacto + dropdown -->
      <div
        v-if="companyStore.companies.length > 1"
        class="company-select-mobile"
        ref="companyDropRef"
      >
        <button class="btn-company-mobile" @click.stop="toggleCompanyDrop" title="Cambiar empresa">
          <i class="bi bi-buildings"></i>
          <i class="bi bi-chevron-down company-arr"></i>
        </button>
        <Transition name="dropdown-fade">
          <div v-if="companyDropOpen" class="dropdown-panel company-drop-panel">
            <div class="dropdown-header">Seleccionar empresa</div>
            <button
              v-for="c in companyStore.companies"
              :key="c.id"
              class="dropdown-item"
              :class="{ 'item-active-co': companyStore.selectedCompany?.id === c.id }"
              @click="selectCompanyMobile(c)"
            >
              <span class="item-icon"><i class="bi bi-building"></i></span>
              <span class="item-name">{{ c.name }}</span>
              <i v-if="companyStore.selectedCompany?.id === c.id" class="bi bi-check2 item-check"></i>
            </button>
          </div>
        </Transition>
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

    <!-- ── DERECHA: soporte + sitio web + usuario ── -->
    <div class="topbar-right">

      <!-- Dropdown Soporte -->
      <div class="dropdown-wrap" ref="dropdownRef">
        <button
          class="btn-icon btn-support"
          @click.stop="toggleDropdown"
          title="Soporte"
        >
          <i class="bi bi-headset"></i>
          <span class="btn-label">Soporte <i class="bi bi-chevron-down btn-arr"></i></span>
        </button>

        <Transition name="dropdown-fade">
          <div v-if="dropdownOpen" class="dropdown-panel">
            <div class="dropdown-header">Soporte</div>

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

            <template v-if="canInvite">
              <div class="dropdown-divider"></div>
              <button class="dropdown-item" @click="goInvite">
                <span class="item-icon"><i class="bi bi-link-45deg"></i></span>
                <span class="item-name">Invitar usuario</span>
              </button>
            </template>

            <div v-if="menuItems.length === 0 && !canInvite" class="dropdown-empty">
              <i class="bi bi-inbox"></i>
              Sin opciones disponibles
            </div>
          </div>
        </Transition>
      </div>

      <!-- Ver sitio web -->
      <a :href="siteUrl" target="_blank" rel="noopener"
         class="btn-icon btn-website" title="Ver sitio web">
        <i class="bi bi-globe2"></i>
        <span class="btn-label brand-label">
          <span class="bl-easy">Easy</span><span class="bl-pos">Pos</span><span class="bl-web">Web</span>
        </span>
      </a>

      <!-- Dropdown Usuario -->
      <div class="dropdown-wrap" ref="userDropRef">
        <button
          class="btn-user-drop"
          @click.stop="toggleUserDropdown"
          title="Mi cuenta"
        >
          <span class="user-icon-wrap">
            <i class="bi bi-person-circle"></i>
            <span v-if="totalNotifCount > 0" class="user-notif-badge">{{ totalNotifCount > 99 ? '99+' : totalNotifCount }}</span>
          </span>
          <div class="user-text">
            <span class="user-name">{{ user?.nombre }}</span>
            <span class="user-role">{{ user?.role }}</span>
          </div>
          <i class="bi bi-chevron-down user-arr"></i>
          <span class="user-short-label">CUENTA <i class="bi bi-chevron-down btn-arr"></i></span>
        </button>

        <Transition name="dropdown-fade">
          <div v-if="userDropOpen" class="dropdown-panel user-drop-panel">
            <div class="dropdown-header">Mi cuenta</div>

            <!-- Plan activo -->
            <div v-if="companyPlan.plan_name" class="dropdown-item item-plan-info">
              <span class="item-icon"><i class="bi bi-award" style="color:#fbbf24"></i></span>
              <div class="item-plan-text">
                <span class="item-name">{{ companyPlan.plan_name }}</span>
                <span class="item-plan-exp">
                  {{ companyPlan.expiration_date ? 'Vence: ' + formatDate(companyPlan.expiration_date) : 'Indefinido' }}
                </span>
              </div>
            </div>

            <!-- NOTIFICACIONES expandible -->
            <button class="dropdown-item notif-toggle" @click.stop="notifExpanded = !notifExpanded">
              <span class="item-icon" style="position:relative">
                <i class="bi bi-bell"></i>
                <span v-if="totalNotifCount > 0" class="notif-dot">{{ totalNotifCount > 99 ? '99+' : totalNotifCount }}</span>
              </span>
              <span class="item-name">Notificaciones{{ totalNotifCount > 0 ? ` (${totalNotifCount})` : '' }}</span>
              <i class="bi notif-chevron" :class="notifExpanded ? 'bi-chevron-up' : 'bi-chevron-down'"></i>
            </button>

            <!-- Sub-tipos de notificaciones -->
            <div v-if="notifExpanded" class="notif-subtypes">

              <!-- Pagos pendientes — SYSADMIN, funcional -->
              <button
                v-if="companyStore.isSystem"
                class="notif-subtype-item"
                :class="{ 'has-count': pendingPaymentsCount > 0 }"
                @click="goToPaymentReview"
              >
                <span class="nsi-icon payment"><i class="bi bi-credit-card-2-back"></i></span>
                <span class="nsi-label">
                  Pagos pendientes
                  <small>SYSADMIN › Revisión de Pagos</small>
                </span>
                <span class="nsi-count" :class="pendingPaymentsCount > 0 ? 'active' : 'zero'">
                  {{ pendingPaymentsCount }}
                </span>
              </button>

              <!-- Mensajes internos — funcional -->
              <button class="notif-subtype-item" :class="{ 'has-count': unreadNotif > 0 }" @click="openNotifPanel">
                <span class="nsi-icon messages"><i class="bi bi-chat-dots"></i></span>
                <span class="nsi-label">
                  Mensajes internos
                  <small>Comentarios y avisos de tu equipo</small>
                </span>
                <span class="nsi-count" :class="unreadNotif > 0 ? 'active' : 'zero'">{{ unreadNotif }}</span>
              </button>

              <!-- Novedades — próximamente -->
              <div class="notif-subtype-item disabled">
                <span class="nsi-icon news"><i class="bi bi-megaphone"></i></span>
                <span class="nsi-label">
                  Novedades EasyPosWeb
                  <small>Nuevos módulos y características</small>
                </span>
                <span class="badge-soon">Próximo</span>
              </div>

              <!-- Promociones — próximamente -->
              <div class="notif-subtype-item disabled">
                <span class="nsi-icon promo"><i class="bi bi-gift"></i></span>
                <span class="nsi-label">
                  Promociones
                  <small>Ofertas y descuentos especiales</small>
                </span>
                <span class="badge-soon">Próximo</span>
              </div>

            </div>

            <div class="dropdown-divider"></div>

            <!-- Perfil — deshabilitado si pago pendiente -->
            <button
              class="dropdown-item"
              :class="{ 'item-disabled': !isPaymentActive }"
              :title="!isPaymentActive ? 'Disponible una vez activo tu plan' : 'Ir a mi perfil'"
              @click="goProfile"
            >
              <span class="item-icon"><i class="bi bi-person-badge"></i></span>
              <span class="item-name">Mi Perfil</span>
              <span v-if="!isPaymentActive" class="badge-soon">Inactivo</span>
            </button>

            <div class="dropdown-divider"></div>

            <button class="dropdown-item item-logout" @click="logout">
              <span class="item-icon"><i class="bi bi-box-arrow-right"></i></span>
              <span class="item-name">Cerrar Sesión</span>
            </button>
          </div>
        </Transition>
      </div>

    </div>

  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watchEffect } from "vue"
import { useRouter } from "vue-router"
import { getThemeState } from "@/utils/theme"
import { useCompanyStore } from "@/stores/companyStore"
import api from "@/services/apis"

const emit = defineEmits(["toggle-sidebar", "toggle-sidebar-right"])

const siteUrl = import.meta.env.VITE_SITE_URL || window.location.origin

const logo         = ref("")
const user         = ref(null)
const theme        = getThemeState()
const companyStore = useCompanyStore()
const router       = useRouter()
const companyPlan  = ref({ plan_name: "", expiration_date: null })
const unreadNotif  = ref(0)
const menuItems    = ref([])
const dropdownOpen    = ref(false)
const dropdownRef     = ref(null)
const userDropOpen    = ref(false)
const userDropRef     = ref(null)
const companyDropOpen      = ref(false)
const companyDropRef       = ref(null)
const notifExpanded        = ref(false)
const pendingPaymentsCount = ref(0)

const isPaymentActive = computed(() => {
  const ps = user.value?.payment_status ?? "active"
  return ps === "active"
})

const totalNotifCount = computed(() =>
  unreadNotif.value + (companyStore.isSystem ? pendingPaymentsCount.value : 0)
)

// ── Notificaciones ──────────────────────────────────
async function loadUnreadCount() {
  if (!localStorage.getItem("token")) return
  try {
    const res = await api.get("/task-comments/notifications/unread")
    unreadNotif.value = res.data.filter(n => !n.is_read).length
  } catch {}
}

async function loadPendingPayments() {
  if (!companyStore.isSystem) return
  try {
    const res = await api.get("/payments/pending-count")
    pendingPaymentsCount.value = res.data.count ?? 0
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

const canInvite = computed(() => {
  if (companyStore.isSystem) return true
  const role = user.value?.role?.toLowerCase() || ""
  return role.includes("admin")
})

function goInvite() {
  dropdownOpen.value = false
  router.push("/configuration/users")
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
  if (dropdownOpen.value) userDropOpen.value = false
}

function toggleUserDropdown() {
  userDropOpen.value = !userDropOpen.value
  if (userDropOpen.value) dropdownOpen.value = false
  if (!userDropOpen.value) notifExpanded.value = false
}

function openNotifPanel() {
  userDropOpen.value  = false
  notifExpanded.value = false
  emit("toggle-sidebar-right")
}

function goToPaymentReview() {
  userDropOpen.value  = false
  notifExpanded.value = false
  router.push("/sysadmin/payment-review")
}


function goProfile() {
  if (!isPaymentActive.value) return
  userDropOpen.value = false
  router.push("/profiles")
}

function handleOutsideClick(e) {
  if (dropdownRef.value && !dropdownRef.value.contains(e.target)) dropdownOpen.value = false
  if (userDropRef.value && !userDropRef.value.contains(e.target)) {
    userDropOpen.value  = false
    notifExpanded.value = false
  }
  if (companyDropRef.value && !companyDropRef.value.contains(e.target)) companyDropOpen.value = false
}

function toggleCompanyDrop() {
  companyDropOpen.value = !companyDropOpen.value
}

async function selectCompanyMobile(company) {
  companyDropOpen.value = false
  await companyStore.setCompany(company)
  await loadPlan(company.id)
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
  companyStore.reset()
  localStorage.removeItem("token")
  localStorage.removeItem("user")
  localStorage.removeItem("menu")
  localStorage.removeItem("selected_company")
  router.push("/login")
}

watchEffect(() => { if (theme.logo) logo.value = theme.logo })

let notifTimer     = null
let heartbeatTimer = null

async function getConfigMs(key, fallback) {
  try {
    const res = await api.get(`/system-config/${key}`)
    const val = parseInt(res.data?.config_value)
    return isNaN(val) || val < 5000 ? fallback : val
  } catch { return fallback }
}

onMounted(async () => {
  const stored = localStorage.getItem("user")
  if (stored) {
    user.value = JSON.parse(stored)
    // Sincronizar payment_status desde localStorage (ya actualizado por router guard)
    watchEffect(() => {
      const fresh = localStorage.getItem("user")
      if (fresh) user.value = JSON.parse(fresh)
    })
    await companyStore.init(user.value)
    await loadPlan(companyStore.selectedCompany?.id)
    await loadMenuItems()
    loadUnreadCount()
    loadPendingPayments()
    sendHeartbeat()

    const [notifMs, hbMs] = await Promise.all([
      getConfigMs("topbar_notif_interval_ms",     60_000),
      getConfigMs("topbar_heartbeat_interval_ms", 180_000),
    ])
    notifTimer     = setInterval(() => { loadUnreadCount(); loadPendingPayments() }, notifMs)
    heartbeatTimer = setInterval(sendHeartbeat, hbMs)
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

/* Bloque logo + nombre-empresa (en móvil apila en columna) */
.brand-block {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.brand { display: flex; align-items: center; }

/* Nombre empresa debajo del logo — solo visible en móvil */
.brand-company-name {
  display: none;
  font-size: 10px;
  font-weight: 700;
  color: var(--topbar-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 72px;
  line-height: 1.1;
}

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

.company-select-desktop {
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
.company-select-desktop option {
  background: var(--topbar-bg);
  color: var(--topbar-text);
}

/* Versión móvil — solo icono + flecha */
.company-select-mobile {
  display: none;
  position: relative;
  flex-shrink: 0;
}

.btn-company-mobile {
  display: flex;
  align-items: center;
  gap: 3px;
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 6px;
  color: var(--topbar-text);
  padding: 6px 8px;
  cursor: pointer;
  font-size: 17px;
  transition: background 0.15s;
}
.btn-company-mobile:hover { background: rgba(255,255,255,0.2); }
.company-arr { font-size: 10px; opacity: 0.75; }

.company-drop-panel {
  left: 0;
  right: auto;
  min-width: 200px;
}

.item-active-co { background: rgba(255,255,255,0.1); }
.item-active-co .item-name { font-weight: 700; }
.item-check { margin-left: auto; color: #22c55e; font-size: 14px; }


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
.btn-website {
  margin-left: 2px;
  color: inherit;
  text-decoration: none;
  flex-direction: column;
  gap: 1px;
  padding: 4px 10px;
  border-radius: 8px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.12);
}
.btn-website .bi { font-size: 17px; }
.btn-website:hover { background: rgba(37,99,235,0.18); border-color: rgba(147,197,253,0.35); }

/* Colores tricolor EasyPosWeb (igual que landing) */
.brand-label { letter-spacing: 0; }
.bl-easy { color: #2563eb; }
.bl-pos  { color: #f59e0b; }
.bl-web  { color: #10b981; }
/* Dropdown usuario */
.btn-user-drop {
  display: flex; align-items: center; gap: 7px;
  padding: 5px 10px;
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 8px;
  color: var(--topbar-text);
  cursor: pointer;
  transition: background 0.2s;
  flex-shrink: 0;
}
.btn-user-drop:hover { background: rgba(255,255,255,0.18); }
.btn-user-drop .bi-person-circle { font-size: 22px; flex-shrink: 0; }
.user-arr { font-size: 9px; opacity: 0.65; flex-shrink: 0; }

.user-drop-panel { right: 0; min-width: 200px; }

/* Label corta del botón usuario — solo visible en móvil */
.user-short-label {
  display: none;
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  opacity: 0.85;
  line-height: 1;
}

.item-logout { color: #fca5a5; }
.item-logout:hover { background: rgba(239,68,68,0.2) !important; color: #fca5a5; }

/* Plan info dentro del dropdown usuario */
.item-plan-info {
  cursor: default;
  opacity: 1;
  background: rgba(251,191,36,0.08);
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.item-plan-info:hover { background: rgba(251,191,36,0.12); }
.item-plan-text { display: flex; flex-direction: column; line-height: 1.3; }
.item-plan-exp { font-size: 10px; opacity: 0.6; }

/* Badge en el botón CUENTA */
.user-icon-wrap { position: relative; display: flex; align-items: center; }
.user-notif-badge {
  position: absolute; top: -5px; right: -7px;
  min-width: 16px; height: 16px;
  background: #ef4444; color: #fff;
  font-size: 8px; font-weight: 800; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  padding: 0 3px; line-height: 1; pointer-events: none;
  border: 1.5px solid var(--topbar-bg, #1e293b);
}

/* Fila toggle de notificaciones en el dropdown */
.notif-toggle { justify-content: flex-start; }
.notif-chevron { font-size: 10px; margin-left: auto; opacity: .6; }

/* Sub-tipos de notificaciones */
.notif-subtypes {
  background: rgba(0,0,0,0.15);
  border-radius: 8px;
  margin: 2px 4px 6px;
  overflow: hidden;
}
.notif-subtype-item {
  display: flex; align-items: center; gap: 10px;
  width: 100%; padding: 8px 12px;
  background: none; border: none; border-radius: 0;
  color: var(--topbar-text); font-size: .82rem; cursor: pointer;
  text-align: left; transition: background .15s;
}
.notif-subtype-item:not(.disabled):hover { background: rgba(255,255,255,0.08); }
.notif-subtype-item.has-count { background: rgba(255,255,255,0.04); }
.notif-subtype-item.disabled { opacity: .45; cursor: default; }

.nsi-icon {
  width: 28px; height: 28px; border-radius: 6px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: .85rem;
}
.nsi-icon.payment  { background: rgba(249,115,22,.25); color: #f97316; }
.nsi-icon.messages { background: rgba(59,130,246,.25);  color: #60a5fa; }
.nsi-icon.news     { background: rgba(168,85,247,.25);  color: #c084fc; }
.nsi-icon.promo    { background: rgba(16,185,129,.25);  color: #34d399; }

.nsi-label { display: flex; flex-direction: column; flex: 1; min-width: 0; }
.nsi-label small { font-size: .68rem; opacity: .5; line-height: 1.2; }

.nsi-count {
  min-width: 20px; height: 20px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 800; padding: 0 4px; flex-shrink: 0;
}
.nsi-count.active { background: #ef4444; color: #fff; }
.nsi-count.zero   { background: rgba(255,255,255,0.1); color: rgba(255,255,255,0.4); }

/* Dot de notificaciones */
.notif-dot {
  position: absolute; top: -4px; right: -6px;
  min-width: 15px; height: 15px;
  background: #ef4444; color: #fff;
  font-size: 8px; font-weight: 800; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  padding: 0 3px; line-height: 1; pointer-events: none;
}

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

.dropdown-divider {
  height: 1px;
  background: rgba(255,255,255,0.1);
  margin: 4px 6px;
}

/* ── RESPONSIVE ── */
@media (max-width: 768px) {
  .btn-menu-left         { display: flex; }
  .user-text             { display: none; }
  .user-arr              { display: none; }
  .company-title         { font-size: 13px; max-width: 100px; }
  .company-title-wrap    { display: none; }
  .company-profile-type  { display: none; }
  .topbar-divider        { display: none; }
  .brand-logo            { height: 36px; }
  .plan-name             { display: none; }
  .plan-exp              { display: none; }
  .plan-badge            { padding: 3px 6px; }
  .sysadmin-badge        { display: none; }

  /* intercambio select empresa */
  .company-select-desktop { display: none; }
  .company-select-mobile  { display: block; }

  /* Logo + nombre empresa en columna */
  .brand-block           { flex-direction: column; align-items: flex-start; gap: 1px; }
  .brand-company-name    { display: block; }

  /* Botón usuario en columna como SOPORTE/EASYPOSWEB */
  .btn-user-drop {
    flex-direction: column;
    gap: 1px;
    padding: 4px 8px;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
  }
  .btn-user-drop .bi-person-circle { font-size: 17px; }
  .user-short-label      { display: block; }
}

@media (min-width: 769px) and (max-width: 1100px) {
  .user-role     { display: none; }
  .company-title { max-width: 180px; font-size: 15px; }
  .plan-exp      { display: none; }
}
</style>
