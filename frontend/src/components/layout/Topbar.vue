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

      <!-- Botón toggle sidebar derecho — siempre visible en topbar -->
      <button
        class="btn-icon btn-panel-right"
        :class="{ 'panel-active': sidebarRightOpen }"
        @click="emit('toggle-sidebar-right')"
        title="Panel lateral"
      >
        <i class="bi bi-layout-sidebar-reverse"></i>
      </button>

      <!-- Dropdown Soporte -->
      <div class="dropdown-wrap" ref="dropdownRef">
        <button
          class="btn-icon btn-support"
          @click.stop="toggleDropdown"
          title="Soporte"
        >
          <span class="support-icon-wrap">
            <i class="bi bi-headset"></i>
          </span>
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

      <!-- Mapa del Sitio -->
      <router-link to="/navigation-map" class="btn-icon btn-sitemap" title="Mapa del Sitio">
        <i class="bi bi-compass-fill sitemap-ico"></i>
        <span class="btn-label sitemap-label">Mapa del Sitio</span>
      </router-link>

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

            <!-- Panel lateral — primera acción, siempre visible -->
            <button class="dropdown-item item-panel-toggle" @click="toggleRightPanel">
              <span class="item-icon">
                <i class="bi bi-layout-sidebar-reverse"></i>
              </span>
              <span class="item-name">Panel lateral</span>
              <i class="bi item-toggle-icon"
                 :class="sidebarRightOpen ? 'bi-toggle-on' : 'bi-toggle-off'"
                 :style="sidebarRightOpen ? 'color:#22c55e;font-size:20px' : 'opacity:.4;font-size:20px'"></i>
            </button>

            <div class="dropdown-divider"></div>

            <!-- Tarjeta info usuario logueado -->
            <div class="user-info-card">
              <div class="uic-avatar"><i class="bi bi-person-circle"></i></div>
              <div class="uic-data">
                <span class="uic-name">{{ user?.nombre }}</span>
                <span class="uic-email">{{ user?.email }}</span>
                <span class="uic-role-badge">{{ user?.role }}</span>
              </div>
            </div>

            <!-- Plan activo -->
            <div v-if="companyPlan.plan_name" class="dropdown-item item-plan-info">
              <span class="item-icon"><i class="bi bi-award" style="color:#fbbf24"></i></span>
              <div class="item-plan-text">
                <span class="item-name">{{ companyPlan.plan_name }}</span>
                <span class="item-plan-exp">
                  {{ companyPlan.expiration_date ? 'Vence: ' + formatDate(companyPlan.expiration_date) : 'Indefinido' }}
                </span>
              </div>
              <button
                v-if="isAdminUser && !companyStore.isSystem"
                class="btn-upgrade-plan"
                @click.stop="userDropOpen = false; emit('open-upgrade-modal')"
                title="Mejorar plan"
              >
                <i class="bi bi-arrow-up-circle"></i> Mejorar
              </button>
            </div>

            <div class="dropdown-divider"></div>

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

              <!-- Pagos pendientes — SYSADMIN -->
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

              <!-- Pautas pendientes — SYSADMIN -->
              <button
                v-if="companyStore.isSystem"
                class="notif-subtype-item"
                :class="{ 'has-count': pendingAdsCount > 0 }"
                @click="goToAdsReview"
              >
                <span class="nsi-icon ads"><i class="bi bi-megaphone-fill"></i></span>
                <span class="nsi-label">
                  Pautas pendientes
                  <small>SYSADMIN › Gestión de Pautas</small>
                </span>
                <span class="nsi-count" :class="pendingAdsCount > 0 ? 'active' : 'zero'">
                  {{ pendingAdsCount }}
                </span>
              </button>

              <!-- Notificaciones de tarea -->
              <button class="notif-subtype-item" :class="{ 'has-count': unreadNotif > 0 }"
                @click.stop="taskNotifListOpen = !taskNotifListOpen">
                <span class="nsi-icon task-notif"><i class="bi bi-bell-fill"></i></span>
                <span class="nsi-label">
                  Notificaciones de tarea
                  <small>Avisos del administrador</small>
                </span>
                <i class="bi notif-chevron" :class="taskNotifListOpen ? 'bi-chevron-up' : 'bi-chevron-down'" style="font-size:10px;opacity:.6;flex-shrink:0"></i>
                <span class="nsi-count" :class="unreadNotif > 0 ? 'active' : 'zero'">{{ unreadNotif }}</span>
              </button>

              <!-- Lista inline de notificaciones de tarea -->
              <div v-if="taskNotifListOpen" class="tnl-panel">
                <div v-if="taskNotifList.length === 0" class="tnl-empty">
                  <i class="bi bi-bell-slash me-1"></i> Sin notificaciones pendientes
                </div>
                <div v-for="n in taskNotifList" :key="n.id" class="tnl-item" @click="goToTaskNotif(n)">
                  <div class="tnl-top">
                    <span class="tnl-task"><i class="bi bi-clipboard-check me-1"></i>{{ n.task_title || 'Tarea #' + n.task_id }}</span>
                    <span class="tnl-time">{{ fmtRelative(n.created_at) }}</span>
                  </div>
                  <div class="tnl-msg">{{ n.comment }}</div>
                  <div v-if="n.sender_name" class="tnl-from">
                    <i class="bi bi-person-circle me-1"></i>{{ n.sender_name }}
                  </div>
                </div>
              </div>


              <!-- Tareas con info incompleta — admin solamente -->
              <button
                v-if="isAdminUser"
                class="notif-subtype-item"
                :class="{ 'has-count': incompleteTaskCount > 0 }"
                @click.stop="incompleteListOpen = !incompleteListOpen"
              >
                <span class="nsi-icon incomplete"><i class="bi bi-clipboard-x-fill"></i></span>
                <span class="nsi-label">
                  Tareas incompletas
                  <small>Sin asignar o sin info completa</small>
                </span>
                <i class="bi notif-chevron" :class="incompleteListOpen ? 'bi-chevron-up' : 'bi-chevron-down'" style="font-size:10px;opacity:.6;flex-shrink:0"></i>
                <span class="nsi-count" :class="incompleteTaskCount > 0 ? 'active' : 'zero'">{{ incompleteTaskCount }}</span>
              </button>

              <!-- Lista inline de tareas incompletas -->
              <div v-if="incompleteListOpen && isAdminUser" class="tnl-panel">
                <div v-if="incompleteTaskList.length === 0" class="tnl-empty">
                  <i class="bi bi-check2-circle me-1"></i> Sin tareas pendientes
                </div>
                <div v-for="t in incompleteTaskList.slice(0, 6)" :key="t.id" class="tnl-item" @click="goToIncompleteTask(t)">
                  <div class="tnl-top">
                    <span class="tnl-task" style="color:#fb923c">
                      <i class="bi bi-clipboard-x me-1"></i>{{ t.title }}
                    </span>
                    <span class="tnl-time" :style="t.worker_id ? 'color:#fbbf24' : 'color:#f87171'">
                      {{ t.worker_id ? 'Incompleta' : 'Sin asignar' }}
                    </span>
                  </div>
                  <div v-if="t.due_date" class="tnl-from">
                    <i class="bi bi-calendar3 me-1"></i>Vence: {{ formatDate(t.due_date) }}
                  </div>
                  <div v-else class="tnl-from" style="color:#f87171">
                    <i class="bi bi-calendar-x me-1"></i>Sin fecha límite
                  </div>
                </div>
                <div v-if="incompleteTaskList.length > 6" class="tnl-more-link" @click="goToTasksView">
                  <i class="bi bi-arrow-right-circle me-1"></i>+{{ incompleteTaskList.length - 6 }} más — ver todas
                </div>
              </div>

              <!-- Solicitudes de activos — admin solamente -->
              <button
                v-if="isAdminUser"
                class="notif-subtype-item"
                :class="{ 'has-count': newInquiriesCount > 0 }"
                @click="markInquiriesRead(); userDropOpen = false; notifExpanded = false; $router.push('/assets/inquiries')"
              >
                <span class="nsi-icon news"><i class="bi bi-envelope-check-fill"></i></span>
                <span class="nsi-label">
                  Solicitudes de activos
                  <small>Nuevas consultas sin revisar</small>
                </span>
                <span class="nsi-count" :class="newInquiriesCount > 0 ? 'active' : 'zero'">{{ newInquiriesCount }}</span>
              </button>

              <!-- Nueva versión disponible -->
              <div v-if="newVersionAvailable" class="notif-version-banner">
                <div class="nvb-header">
                  <i class="bi bi-arrow-up-circle-fill"></i>
                  <span>Nueva versión disponible</span>
                </div>
                <p class="nvb-text">Hay actualizaciones pendientes. Recarga la página o cierra sesión para ver los cambios.</p>
                <div class="nvb-actions">
                  <button class="nvb-btn nvb-reload" @click.stop="dismissVersion('reload')">
                    <i class="bi bi-arrow-clockwise"></i> Recargar
                  </button>
                  <button class="nvb-btn nvb-logout" @click.stop="dismissVersion('logout')">
                    <i class="bi bi-box-arrow-right"></i> Cerrar sesión
                  </button>
                </div>
              </div>

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

            <!-- Perfil de Empresa -->
            <button
              class="dropdown-item"
              :class="{ 'item-disabled': !isPaymentActive }"
              :title="!isPaymentActive ? 'Disponible una vez activo tu plan' : 'Ver perfil de empresa'"
              @click="goProfile"
            >
              <span class="item-icon"><i class="bi bi-building"></i></span>
              <span class="item-name">Perfil de Empresa</span>
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

const props = defineProps({ sidebarRightOpen: { type: Boolean, default: true } })
const emit  = defineEmits(["toggle-sidebar", "toggle-sidebar-right", "open-upgrade-modal"])

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
const pendingAdsCount      = ref(0)
const taskNotifList        = ref([])
const taskNotifListOpen    = ref(false)
const unreadUserNotif      = ref(0)
const incompleteTaskCount  = ref(0)
const incompleteTaskList   = ref([])
const incompleteListOpen   = ref(false)
const hasNewNotif          = ref(false)
const newInquiriesCount    = ref(0)
const newVersionAvailable  = ref(false)
const newVersionValue      = ref("")

const isPaymentActive = computed(() => {
  const ps = user.value?.payment_status ?? "active"
  return ps === "active"
})

const isAdminUser = computed(() => {
  const role = user.value?.role?.toLowerCase() || ""
  return role.includes("admin")
})

const totalNotifCount = computed(() =>
  unreadNotif.value +
  (companyStore.isSystem ? pendingPaymentsCount.value : 0) +
  (companyStore.isSystem ? pendingAdsCount.value : 0) +
  (isAdminUser.value ? incompleteTaskCount.value : 0) +
  (isAdminUser.value ? newInquiriesCount.value : 0) +
  (newVersionAvailable.value ? 1 : 0)
)

// ── Audio ────────────────────────────────────────────
// Un solo AudioContext compartido; se desbloquea en el primer clic del usuario.
// Crear el contexto dentro de un timer lo deja suspendido — por eso usamos uno persistente.
let _actx = null
function _getCtx() {
  if (!_actx || _actx.state === "closed")
    _actx = new (window.AudioContext || window.webkitAudioContext)()
  return _actx
}
async function unlockAudio() {
  try {
    const c = _getCtx()
    if (c.state === "suspended") await c.resume()
    if (hasNewNotif.value) {
      hasNewNotif.value = false
      playNotifSound()
    }
  } catch {}
}
function playNotifSound() {
  try {
    const ctx = _getCtx()
    if (ctx.state === "suspended") { hasNewNotif.value = true; return }
    const t = ctx.currentTime
    // chime 1 — 880→660 Hz
    const o1 = ctx.createOscillator(), g1 = ctx.createGain()
    o1.connect(g1); g1.connect(ctx.destination)
    o1.type = "sine"
    o1.frequency.setValueAtTime(880, t)
    o1.frequency.exponentialRampToValueAtTime(660, t + 0.12)
    g1.gain.setValueAtTime(0.28, t)
    g1.gain.exponentialRampToValueAtTime(0.001, t + 0.28)
    o1.start(t); o1.stop(t + 0.28)
    // chime 2 — 1100→880 Hz, 120 ms después
    const o2 = ctx.createOscillator(), g2 = ctx.createGain()
    o2.connect(g2); g2.connect(ctx.destination)
    o2.type = "sine"
    o2.frequency.setValueAtTime(1100, t + 0.12)
    o2.frequency.exponentialRampToValueAtTime(880, t + 0.38)
    g2.gain.setValueAtTime(0.0,  t)
    g2.gain.setValueAtTime(0.20, t + 0.12)
    g2.gain.exponentialRampToValueAtTime(0.001, t + 0.55)
    o2.start(t + 0.12); o2.stop(t + 0.55)
  } catch {}
}

// ── Notificaciones ──────────────────────────────────

async function loadUnreadCount() {
  if (!localStorage.getItem("token")) return
  try {
    const taskRes = await api.get("/task-comments/notifications/unread")
    const prevTask = unreadNotif.value
    taskNotifList.value = taskRes.data
    unreadNotif.value   = taskRes.data.length
    if (unreadNotif.value > prevTask) playNotifSound()
  } catch {}
}

async function goToTaskNotif(n) {
  try { await api.patch(`/task-comments/${n.id}/read`) } catch {}
  taskNotifList.value    = taskNotifList.value.filter(x => x.id !== n.id)
  unreadNotif.value      = taskNotifList.value.length
  taskNotifListOpen.value = false
  userDropOpen.value      = false
  notifExpanded.value     = false
  router.push(`/tasks/${n.task_id}/detalle`)
}

function fmtRelative(iso) {
  if (!iso) return ""
  const mins = Math.floor((Date.now() - new Date(iso).getTime()) / 60000)
  if (mins < 1)  return "ahora"
  if (mins < 60) return `hace ${mins} min`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24)  return `hace ${hrs}h`
  return `hace ${Math.floor(hrs / 24)}d`
}

async function loadPendingPayments() {
  if (!companyStore.isSystem) return
  try {
    const res  = await api.get("/payments/pending-count")
    const prev = pendingPaymentsCount.value
    pendingPaymentsCount.value = res.data.count ?? 0
    if (pendingPaymentsCount.value > prev) playNotifSound()
  } catch {}
}

async function loadPendingAds() {
  if (!companyStore.isSystem) return
  try {
    const res  = await api.get("/ads/admin/pending-count")
    const prev = pendingAdsCount.value
    pendingAdsCount.value = res.data.count ?? 0
    if (pendingAdsCount.value > prev) playNotifSound()
  } catch {}
}

async function loadIncompleteTasks() {
  if (!isAdminUser.value) return
  try {
    const res  = await api.get("/tasks/incomplete-info")
    const prev = incompleteTaskCount.value
    const all  = [...(res.data.sin_asignar || []), ...(res.data.info_incompleta || [])]
    incompleteTaskList.value  = all
    incompleteTaskCount.value = all.length
    if (incompleteTaskCount.value > prev) playNotifSound()
  } catch {}
}

async function loadNewInquiries() {
  if (!isAdminUser.value) return
  try {
    const res  = await api.get("/asset-inquiries/new-count")
    const prev = newInquiriesCount.value
    newInquiriesCount.value = res.data.count ?? 0
    if (newInquiriesCount.value > prev) playNotifSound()
  } catch {}
}

async function markInquiriesRead() {
  try { await api.post("/asset-inquiries/mark-notified") } catch {}
  newInquiriesCount.value = 0
}

async function checkAppVersion() {
  try {
    const res = await api.get("/system-config/app_version")
    const serverVersion = res.data?.config_value || ""
    const storedVersion = localStorage.getItem("app_version") || ""
    if (serverVersion && storedVersion && serverVersion !== storedVersion) {
      newVersionAvailable.value = true
      newVersionValue.value = serverVersion
    } else if (serverVersion && !storedVersion) {
      localStorage.setItem("app_version", serverVersion)
    }
  } catch {}
}

function dismissVersion(action) {
  const v = newVersionValue.value
  if (v) localStorage.setItem("app_version", v)
  newVersionAvailable.value = false
  if (action === "reload") window.location.reload()
  else if (action === "logout") logout()
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
async function toggleDropdown() {
  await unlockAudio()
  dropdownOpen.value = !dropdownOpen.value
  if (dropdownOpen.value) userDropOpen.value = false
}

async function toggleUserDropdown() {
  await unlockAudio()
  userDropOpen.value = !userDropOpen.value
  if (userDropOpen.value) dropdownOpen.value = false
  if (!userDropOpen.value) { notifExpanded.value = false; taskNotifListOpen.value = false; incompleteListOpen.value = false }
}

function openNotifPanel() {
  userDropOpen.value  = false
  notifExpanded.value = false
  emit("toggle-sidebar-right")
}

function goToInbox() {
  userDropOpen.value  = false
  notifExpanded.value = false
  router.push("/notifications/inbox")
}

function goToPaymentReview() {
  userDropOpen.value  = false
  notifExpanded.value = false
  router.push("/sysadmin/payment-review")
}

function goToAdsReview() {
  userDropOpen.value  = false
  notifExpanded.value = false
  pendingAdsCount.value = 0
  router.push("/sysadmin/advertising")
}


function toggleRightPanel() {
  userDropOpen.value  = false
  notifExpanded.value = false
  emit("toggle-sidebar-right")
}

function goProfile() {
  if (!isPaymentActive.value) return
  userDropOpen.value = false
  router.push("/profiles")
}

function goToIncompleteTask(t) {
  userDropOpen.value    = false
  notifExpanded.value   = false
  incompleteListOpen.value = false
  router.push(`/tasks/${t.id}/detalle`)
}

function goToTasksView() {
  userDropOpen.value    = false
  notifExpanded.value   = false
  incompleteListOpen.value = false
  router.push("/tasks")
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
  // Desbloquear audio al primer clic en cualquier parte — necesario por política de navegadores
  document.addEventListener("click", unlockAudio, { once: true })

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
    loadPendingAds()
    loadIncompleteTasks()
    loadNewInquiries()
    checkAppVersion()
    sendHeartbeat()

    const [notifMs, hbMs] = await Promise.all([
      getConfigMs("topbar_notif_interval_ms",     60_000),
      getConfigMs("topbar_heartbeat_interval_ms", 180_000),
    ])
    notifTimer     = setInterval(() => { loadUnreadCount(); loadPendingPayments(); loadPendingAds(); loadIncompleteTasks(); loadNewInquiries() }, notifMs)
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
.btn-sitemap {
  margin-left: 2px;
  text-decoration: none;
  flex-direction: column;
  gap: 1px;
  padding: 4px 10px;
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(99,102,241,.18) 0%, rgba(16,185,129,.18) 100%);
  border: 1px solid rgba(99,102,241,.3);
  color: inherit;
}
.btn-sitemap:hover {
  background: linear-gradient(135deg, rgba(99,102,241,.32) 0%, rgba(16,185,129,.32) 100%);
  border-color: rgba(99,102,241,.55);
}
.sitemap-ico   { font-size: 17px; color: #818cf8; }
.sitemap-label { font-size: 9px; letter-spacing: .3px; color: rgba(255,255,255,.8); }
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
.btn-upgrade-plan {
  margin-left: auto; flex-shrink: 0; background: rgba(59,130,246,.2); color: #60a5fa;
  border: 1px solid rgba(59,130,246,.3); border-radius: 6px; padding: 3px 8px;
  font-size: 10px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 3px;
}
.btn-upgrade-plan:hover { background: rgba(59,130,246,.35); }

/* Badge en el botón SOPORTE */
.support-icon-wrap { position: relative; display: flex; align-items: center; }
.support-notif-badge {
  position: absolute; top: -5px; right: -7px;
  min-width: 16px; height: 16px;
  background: #ef4444; color: #fff;
  font-size: 8px; font-weight: 800; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  padding: 0 3px; line-height: 1; pointer-events: none;
  border: 1.5px solid var(--topbar-bg, #1e293b);
  z-index: 1;
}

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
.nsi-icon.ads      { background: rgba(245,158,11,.25);  color: #f59e0b; }

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
  min-width: 220px;
  background: #1e2535;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.4);
  padding: 6px;
  z-index: 9999;
  max-height: calc(100vh - 70px);
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,0.15) transparent;
  -webkit-overflow-scrolling: touch;
}
.dropdown-panel::-webkit-scrollbar { width: 4px; }
.dropdown-panel::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 4px; }

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

/* Banner nueva versión */
.notif-version-banner {
  margin: 4px 6px;
  background: linear-gradient(135deg, rgba(37,99,235,.25), rgba(16,185,129,.2));
  border: 1px solid rgba(96,165,250,.3);
  border-radius: 10px;
  padding: 10px 12px;
}
.nvb-header {
  display: flex; align-items: center; gap: 6px;
  font-size: .8rem; font-weight: 700; color: #60a5fa; margin-bottom: 4px;
}
.nvb-text {
  font-size: .73rem; color: rgba(255,255,255,.7); margin: 0 0 8px; line-height: 1.4;
}
.nvb-actions { display: flex; gap: 6px; }
.nvb-btn {
  flex: 1; padding: 6px 8px; border: none; border-radius: 7px; font-size: .73rem;
  font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 4px;
}
.nvb-reload { background: #2563eb; color: #fff; }
.nvb-reload:hover { background: #1d4ed8; }
.nvb-logout { background: rgba(255,255,255,.1); color: rgba(255,255,255,.85); }
.nvb-logout:hover { background: rgba(255,255,255,.15); }

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
@media (max-width: 1023px) {
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

  /* En móvil: dropdowns como fixed para evitar clipping y habilitar scroll real */
  .dropdown-panel {
    position: fixed;
    top: 62px; /* 54px topbar + 8px gap */
    right: 8px;
    left: auto;
    width: min(290px, calc(100vw - 16px));
    max-height: calc(100svh - 70px);
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
    overscroll-behavior: contain;
    touch-action: pan-y;
  }
  /* Landscape móvil: pantalla muy corta, reducir aún más */
  @media (max-height: 480px) {
    .dropdown-panel {
      max-height: calc(100svh - 65px);
      top: 58px;
    }
  }
  .company-drop-panel { right: auto; left: 8px; }
}

/* En desktop el botón de panel ya está en el dropdown CUENTA */
@media (min-width: 1024px) {
  .btn-panel-right { display: none; }
}

@media (min-width: 1024px) and (max-width: 1200px) {
  .user-role     { display: none; }
  .company-title { max-width: 180px; font-size: 15px; }
  .plan-exp      { display: none; }
}

/* <768px: ocultar botón EasyPosWeb para evitar solapamiento */
@media (max-width: 767px) {
  .btn-website   { display: none; }
  .topbar-right  { gap: 3px; }
  .btn-support   { padding: 4px 7px; }
  .btn-user-drop { padding: 4px 7px; }
}

/* ── NOTIFICACIONES DE TAREA - panel inline ── */
.nsi-icon.task-notif { background: rgba(245,158,11,.25); color: #fbbf24; }
.nsi-icon.access     { background: rgba(34,197,94,.25);  color: #4ade80; }

/* Botón toggle sidebar derecho en topbar — solo en móvil/tablet */
.btn-panel-right {
  flex-direction: column;
  gap: 1px;
  padding: 4px 10px;
  border-radius: 8px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.12);
  font-size: 18px;
  opacity: 0.6;
  transition: opacity 0.15s, background 0.15s;
}
.btn-panel-right:hover { opacity: 1; background: rgba(255,255,255,0.15); }
.btn-panel-right.panel-active { opacity: 1; background: rgba(34,197,94,0.15); border-color: rgba(34,197,94,0.35); color: #4ade80; }

/* Botón panel lateral en dropdown — destacado */
.item-panel-toggle { background: rgba(255,255,255,0.04); }
.item-panel-toggle:hover { background: rgba(255,255,255,0.1) !important; }
.item-toggle-icon { flex-shrink: 0; }

.tnl-panel {
  margin: 0 4px 4px;
  background: rgba(0,0,0,.25);
  border-radius: 8px;
  overflow-y: auto;
  max-height: 260px;
}
.tnl-empty {
  padding: 12px; font-size: .76rem;
  color: rgba(255,255,255,.4); text-align: center;
}
.tnl-item {
  padding: 9px 12px; cursor: pointer;
  border-bottom: 1px solid rgba(255,255,255,.05);
  transition: background .15s;
}
.tnl-item:hover { background: rgba(255,255,255,.08); }
.tnl-item:last-child { border-bottom: none; }
.tnl-top {
  display: flex; justify-content: space-between; align-items: center;
  gap: 6px; margin-bottom: 3px;
}
.tnl-task {
  font-size: .75rem; font-weight: 700; color: #fbbf24;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1;
}
.tnl-time { font-size: .68rem; color: rgba(255,255,255,.4); flex-shrink: 0; }
.tnl-msg {
  font-size: .78rem; color: rgba(255,255,255,.85); line-height: 1.4;
  display: -webkit-box; -webkit-line-clamp: 2;
  -webkit-box-orient: vertical; overflow: hidden; margin-bottom: 3px;
}
.tnl-from { font-size: .68rem; color: rgba(255,255,255,.4); }

/* Panel lateral — contador de notificaciones en el item-name */
.panel-notif-count {
  font-size: 10px;
  font-weight: 700;
  color: #ef4444;
  margin-left: 3px;
}

.nsi-icon.incomplete { background: rgba(251,146,60,.25); color: #fb923c; }

.tnl-more-link {
  padding: 8px 12px; font-size: .74rem; cursor: pointer;
  color: #60a5fa; text-align: center;
  border-top: 1px solid rgba(255,255,255,.05);
  transition: background .15s;
}
.tnl-more-link:hover { background: rgba(255,255,255,.06); }

/* ── Tarjeta info usuario logueado ── */
.user-info-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px 12px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
  margin-bottom: 2px;
}
.uic-avatar {
  font-size: 34px;
  opacity: 0.85;
  flex-shrink: 0;
  line-height: 1;
  color: #93c5fd;
}
.uic-data {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.uic-name {
  font-size: 13px;
  font-weight: 700;
  color: var(--topbar-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.uic-email {
  font-size: 11px;
  opacity: 0.50;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 190px;
}
.uic-role-badge {
  display: inline-block;
  margin-top: 3px;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  padding: 2px 7px;
  border-radius: 10px;
  background: rgba(96,165,250,0.18);
  color: #93c5fd;
  width: fit-content;
}
</style>
