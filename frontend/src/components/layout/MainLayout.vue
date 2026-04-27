<template>
  <div class="page">

    <Topbar
      @toggle-sidebar="toggleSidebar"
      @toggle-sidebar-right="toggleSidebarRight"
    />

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

      <!-- SidebarRight: siempre visible en desktop, oculto por defecto en móvil -->
      <RightSidebar
        v-show="isDesktop || sidebarRightOpen"
        class="sidebar-right"
        @close="sidebarRightOpen = false"
      />

    </div>

    <Footer class="footer" />

  </div>
</template>

<script setup>
import Topbar from "@/components/layout/Topbar.vue"
import Sidebar from "@/components/layout/SidebarLeft.vue"
import RightSidebar from "@/components/layout/SidebarRight.vue"
import Footer from "@/components/layout/FooterBar.vue"
import { ref, onMounted, onUnmounted } from "vue"

const isDesktop = ref(window.innerWidth > 768)

// SidebarLeft
const sidebarOpen = ref(false)
const sidebarCollapsed = ref(true)

// SidebarRight — oculto por defecto en móvil
const sidebarRightOpen = ref(false)

const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value
  if (window.innerWidth < 768) {
    sidebarCollapsed.value = false
    if (sidebarOpen.value) sidebarRightOpen.value = false
  }
}

const toggleSidebarRight = () => {
  sidebarRightOpen.value = !sidebarRightOpen.value
  if (window.innerWidth < 768 && sidebarRightOpen.value) {
    sidebarOpen.value = false
  }
}

const expandSidebar = () => { sidebarCollapsed.value = false }
const collapseSidebar = () => { sidebarCollapsed.value = true }

const handleCloseSidebar = () => {
  sidebarOpen.value = false
  if (window.innerWidth >= 768) sidebarCollapsed.value = true
}

const handleResize = () => {
  const wasDesktop = isDesktop.value
  isDesktop.value = window.innerWidth > 768
  if (!wasDesktop && isDesktop.value) {
    sidebarOpen.value = false
    sidebarRightOpen.value = false
  }
}

onMounted(() => window.addEventListener("resize", handleResize))
onUnmounted(() => window.removeEventListener("resize", handleResize))
</script>

<style>
.layout {
  display: flex;
}

.layout .sidebar-left {
  width: 220px;
  transition: width 0.25s ease;
}

.layout.collapsed .sidebar-left {
  width: 70px;
}

.content {
  flex: 1;
  transition: all 0.25s ease;
}

.sidebar-menu i {
  font-size: 20px;
}
</style>
