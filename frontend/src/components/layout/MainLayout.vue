<template>
  <div class="page">

    <Topbar
      :sidebar-right-open="sidebarRightOpen"
      @toggle-sidebar="toggleSidebar"
      @toggle-sidebar-right="toggleSidebarRight"
      @open-upgrade-modal="showUpgradeModal = true"
    />

    <!-- OVERLAY BLOQUEANTE: plan vencido — cubre todo el contenido -->
    <div v-if="paymentStatus === 'expired'" class="plan-expired-overlay">
      <div class="plan-expired-card">
        <div class="pec-icon"><i class="bi bi-alarm-fill"></i></div>
        <h2 class="pec-title">Tu plan venció</h2>
        <p class="pec-text">
          Para continuar usando EasyPosWeb debes renovar tu plan.
          Haz clic en el botón de abajo, sube tu comprobante de pago y
          en minutos estarás activo nuevamente.
        </p>
        <button class="pec-btn" @click="goRenew">
          <i class="bi bi-credit-card-2-front me-2"></i>Renovar plan ahora
        </button>
        <p class="pec-hint">¿Necesitas ayuda? Contáctanos en soporte.</p>
      </div>
    </div>

    <!-- BANNER: upgrade en revisión (NO bloqueante) -->
    <div v-else-if="upgradeStatus === 'upgrade_pending'" class="plan-banner banner-upgrade">
      <i class="bi bi-arrow-up-circle-fill me-2"></i>
      <span>Tu solicitud de mejora de plan está en revisión. Seguirás con tu plan actual mientras tanto.</span>
      <button class="banner-btn-outline" @click="showUpgradeModal = true">Ver detalle</button>
    </div>

    <div class="layout" :class="{ collapsed: sidebarCollapsed }">

      <Sidebar
        v-show="isDesktop || sidebarOpen"
        :collapsed="sidebarCollapsed"
        :visible="sidebarOpen"
        @expand="expandSidebar"
        @collapse="collapseSidebar"
        @close="handleCloseSidebar"
      />

      <main class="content">
        <router-view />
      </main>

      <RightSidebar
        v-show="sidebarRightOpen"
        class="sidebar-right"
        @close="sidebarRightOpen = false"
      />

    </div>

    <Footer class="footer" />

    <HelpButton />

    <!-- Modal upgrade (vista rápida del estado) -->
    <PlanUpgradeModal
      v-if="showUpgradeModal"
      :current-plan-name="activePlanName"
      @close="showUpgradeModal = false"
      @done="showUpgradeModal = false; refreshUser()"
    />

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from "vue"
import { useRouter, useRoute } from "vue-router"
import Topbar from "@/components/layout/Topbar.vue"
import Sidebar from "@/components/layout/SidebarLeft.vue"
import RightSidebar from "@/components/layout/SidebarRight.vue"
import Footer from "@/components/layout/FooterBar.vue"
import PlanUpgradeModal from "@/components/plans/PlanUpgradeModal.vue"
import HelpButton from "@/components/common/HelpButton.vue"
import api from "@/services/apis"

const router    = useRouter()
const route     = useRoute()
const isDesktop = ref(window.innerWidth >= 1024)

const sidebarOpen      = ref(false)
const sidebarCollapsed = ref(true)
const sidebarRightOpen = ref(window.innerWidth >= 1024)
const showUpgradeModal = ref(false)

const paymentStatus  = ref("")
const upgradeStatus  = ref("")
const activePlanName = ref("")

function readUserState() {
  const raw = localStorage.getItem("user")
  if (!raw) return
  const u = JSON.parse(raw)
  paymentStatus.value = u.payment_status ?? "active"
  upgradeStatus.value = u.upgrade_status ?? null
}

async function refreshUser() {
  try {
    const res = await api.get("/auth/me/")
    const u   = JSON.parse(localStorage.getItem("user") || "{}")
    const merged = { ...u, ...res.data }
    localStorage.setItem("user", JSON.stringify(merged))
    paymentStatus.value = merged.payment_status ?? "active"
    upgradeStatus.value = merged.upgrade_status ?? null
  } catch {}
}

function goRenew() { router.push("/payment-pending") }

const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value
  if (window.innerWidth < 1024) {
    sidebarCollapsed.value = false
    if (sidebarOpen.value) sidebarRightOpen.value = false
  }
}
const toggleSidebarRight = () => {
  sidebarRightOpen.value = !sidebarRightOpen.value
  if (window.innerWidth < 1024 && sidebarRightOpen.value) sidebarOpen.value = false
}
const expandSidebar  = () => { sidebarCollapsed.value = false }
const collapseSidebar = () => { sidebarCollapsed.value = true }
const handleCloseSidebar = () => {
  sidebarOpen.value = false
  if (window.innerWidth >= 1024) sidebarCollapsed.value = true
}
const handleResize = () => {
  const was = isDesktop.value
  isDesktop.value = window.innerWidth >= 1024
  if (!was && isDesktop.value) {
    // Al pasar a desktop (≥1024px): cerrar overlay izquierdo y abrir panel derecho
    sidebarOpen.value      = false
    sidebarRightOpen.value = true
  }
  if (was && !isDesktop.value) {
    // Al pasar a móvil/tablet (<1024px): cerrar ambos sidebars
    sidebarOpen.value      = false
    sidebarRightOpen.value = false
  }
}

watch(() => route.path, () => {
  sidebarOpen.value = false
  if (window.innerWidth < 1024) sidebarRightOpen.value = false
})

function checkFirstLogin() {
  const u = JSON.parse(localStorage.getItem("user") || "{}")
  if (!u.id || u.is_system) return          // SYSADMIN no necesita bienvenida
  const seen = localStorage.getItem(`welcome_seen_${u.id}`)
  if (!seen && router.currentRoute.value.path !== "/bienvenida") {
    router.push("/bienvenida")
  }
}

onMounted(() => {
  window.addEventListener("resize", handleResize)
  readUserState()
  refreshUser()
  checkFirstLogin()
})
onUnmounted(() => window.removeEventListener("resize", handleResize))
</script>

<style>
.layout { display: flex; }
.layout .sidebar-left { width: 220px; transition: width 0.25s ease; }
.layout.collapsed .sidebar-left { width: 70px; }
.content {
  flex: 1; overflow-y: auto; padding-bottom: 40px; transition: all 0.25s ease;
}
.sidebar-menu i { font-size: 20px; }
</style>

<style scoped>
/* Overlay bloqueante — plan vencido */
.plan-expired-overlay {
  position: fixed; inset: 0; z-index: 9999;
  background: rgba(15,23,42,.85);
  display: flex; align-items: center; justify-content: center;
  padding: 20px;
}
.plan-expired-card {
  background: #fff; border-radius: 20px; max-width: 440px; width: 100%;
  padding: 36px 32px; box-shadow: 0 30px 80px rgba(0,0,0,.4);
  display: flex; flex-direction: column; align-items: center; gap: 16px; text-align: center;
}
.pec-icon { font-size: 52px; color: #ef4444; }
.pec-title { font-size: 22px; font-weight: 800; color: #1e293b; margin: 0; }
.pec-text  { font-size: 14px; color: #475569; line-height: 1.6; margin: 0; }
.pec-btn {
  background: #ef4444; color: #fff; border: none; border-radius: 10px;
  padding: 12px 28px; font-size: 15px; font-weight: 700; cursor: pointer; width: 100%;
  display: flex; align-items: center; justify-content: center;
}
.pec-btn:hover { background: #dc2626; }
.pec-hint { font-size: 12px; color: #94a3b8; margin: 0; }

/* Banners de estado de plan */
.plan-banner {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  padding: 10px 18px; font-size: .84rem; font-weight: 600;
  position: sticky; top: 0; z-index: 90;
}
.banner-upgrade {
  background: #eff6ff; color: #1d4ed8; border-bottom: 2px solid #bfdbfe;
}
.banner-btn-outline {
  margin-left: auto; background: transparent; color: #2563eb;
  border: 1.5px solid #2563eb; border-radius: 6px; padding: 4px 12px;
  font-size: .8rem; font-weight: 700; cursor: pointer; white-space: nowrap;
}
.banner-btn-outline:hover { background: #dbeafe; }
</style>
