<template>
  <div class="page">

    <Topbar
      @toggle-sidebar="toggleSidebar"
      @toggle-sidebar-right="toggleSidebarRight"
    />

    <!-- BANNER: plan vencido (bloqueante) -->
    <div v-if="paymentStatus === 'expired'" class="plan-banner banner-expired">
      <i class="bi bi-exclamation-triangle-fill me-2"></i>
      <span>Tu plan venció. Renuévalo para continuar usando todas las funciones.</span>
      <button class="banner-btn" @click="goRenew">Renovar ahora</button>
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
        v-show="isDesktop || sidebarRightOpen"
        class="sidebar-right"
        @close="sidebarRightOpen = false"
      />

    </div>

    <Footer class="footer" />

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
import { ref, computed, onMounted, onUnmounted } from "vue"
import { useRouter } from "vue-router"
import Topbar from "@/components/layout/Topbar.vue"
import Sidebar from "@/components/layout/SidebarLeft.vue"
import RightSidebar from "@/components/layout/SidebarRight.vue"
import Footer from "@/components/layout/FooterBar.vue"
import PlanUpgradeModal from "@/components/plans/PlanUpgradeModal.vue"
import api from "@/services/apis"

const router    = useRouter()
const isDesktop = ref(window.innerWidth > 768)

const sidebarOpen      = ref(false)
const sidebarCollapsed = ref(true)
const sidebarRightOpen = ref(false)
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
  if (window.innerWidth < 768) {
    sidebarCollapsed.value = false
    if (sidebarOpen.value) sidebarRightOpen.value = false
  }
}
const toggleSidebarRight = () => {
  sidebarRightOpen.value = !sidebarRightOpen.value
  if (window.innerWidth < 768 && sidebarRightOpen.value) sidebarOpen.value = false
}
const expandSidebar  = () => { sidebarCollapsed.value = false }
const collapseSidebar = () => { sidebarCollapsed.value = true }
const handleCloseSidebar = () => {
  sidebarOpen.value = false
  if (window.innerWidth >= 768) sidebarCollapsed.value = true
}
const handleResize = () => {
  const was = isDesktop.value
  isDesktop.value = window.innerWidth > 768
  if (!was && isDesktop.value) {
    sidebarOpen.value = false
    sidebarRightOpen.value = false
  }
}

onMounted(() => {
  window.addEventListener("resize", handleResize)
  readUserState()
  refreshUser()
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
/* Banners de estado de plan */
.plan-banner {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  padding: 10px 18px; font-size: .84rem; font-weight: 600;
  position: sticky; top: 0; z-index: 90;
}
.banner-expired {
  background: #fef2f2; color: #b91c1c; border-bottom: 2px solid #fca5a5;
}
.banner-upgrade {
  background: #eff6ff; color: #1d4ed8; border-bottom: 2px solid #bfdbfe;
}
.banner-btn {
  margin-left: auto; background: #ef4444; color: #fff;
  border: none; border-radius: 6px; padding: 5px 14px;
  font-size: .8rem; font-weight: 700; cursor: pointer; white-space: nowrap;
}
.banner-btn:hover { background: #dc2626; }
.banner-btn-outline {
  margin-left: auto; background: transparent; color: #2563eb;
  border: 1.5px solid #2563eb; border-radius: 6px; padding: 4px 12px;
  font-size: .8rem; font-weight: 700; cursor: pointer; white-space: nowrap;
}
.banner-btn-outline:hover { background: #dbeafe; }
</style>
