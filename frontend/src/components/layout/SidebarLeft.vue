
<template>
  <div class="sidebar-left" :class="{ 'sidebar-mobile-active': visible, 'collapsed': collapsed }" @mouseenter="handleMouseEnter" @mouseleave="handleMouseLeave">
    <!-- EMPTY -->
    <div v-if="!menu || menu.length === 0" class="sidebar-empty">
      No tienes módulos asignados
    </div>

    <!-- MENU -->
    <ul class="sidebar-menu">

      <!-- <li v-for="item in menu || []" :key="item.id"> -->
      <!--<li v-for="item in filteredMenu || []" :key="item.id">-->
      <li v-for="item in (ready ? filteredMenu : [])" :key="item.id">
        <!-- ITEM SIN HIJOS -->
        <router-link  
          v-if="!item.children || item.children.length === 0"
          :to="item.route"
          :class="{ active: route.path === item.route }"
          @click="handleNavigate"
        >
          <span class="icon">
            <i 
              v-if="item.icon && item.icon.startsWith('bi-')" 
              :class="`bi ${item.icon}`"
            ></i>
            <span v-else>{{ item.icon }}</span>
          </span>

          <span class="title">{{ item.name }}</span>
        </router-link>
        
        <!-- ITEM CON HIJOS -->
        <div v-else>

          <!-- 🔥 SOLO EXPANDE (NO CIERRA SIDEBAR) -->
          <div class="menu-parent" @click.stop="toggleMenu(item.id)">
            <span class="icon">
              <i 
                v-if="item.icon && item.icon.startsWith('bi-')" 
                :class="`bi ${item.icon}`"
              ></i>
              <span v-else>{{ item.icon }}</span>
            </span>

            <span class="title">{{ item.name }}</span>

            <i  
              class="bi"
              :class="openMenus[item.id] ? 'bi-chevron-down' : 'bi-chevron-right'"
            ></i>
          </div>

          <!-- SUBMENU -->
          <ul class="submenu" :class="{ open: openMenus[item.id] }">
            <li v-for="child in item.children || []" :key="child.id">
              <router-link 
                :to="child.route"
                :class="{ active: route.path === child.route }"
                @click="handleNavigate"
              >
                <span class="icon">
                  <i 
                    v-if="child.icon && child.icon.startsWith('bi-')" 
                    :class="`bi ${child.icon}`"
                  ></i>
                  <span v-else>{{ child.icon }}</span>
                </span>

                <span class="title">{{ child.name }}</span>
              </router-link>
            </li>
          </ul>

        </div>

      </li>

    </ul>

  </div>
</template>


<script setup>

import api from "@/services/apis"
import { ref, onMounted, watch, computed } from "vue"
import { useMenuStore } from "@/stores/menuStore"
import { useCompanyStore } from "@/stores/companyStore"
import { storeToRefs } from "pinia"
import { useRoute } from "vue-router"

const props = defineProps({
  visible: Boolean,
  collapsed: Boolean
})

const emit = defineEmits(["close", "expand", "collapse"])

const permissions = ref([])
const route = useRoute()
const menuStore = useMenuStore()
const companyStore = useCompanyStore()
const { menu } = storeToRefs(menuStore)
const roleName = ref("")
const ready = ref(false)
const roleId = ref(null)


const filteredMenu = computed(() => {
  //if (!roleName.value) return menu.value
  return filterMenuByPermissions(menu.value, permissions.value)
})


const handleNavigate = () => {
  // 🔥 SOLO EN MÓVIL
  if (window.innerWidth < 768) {
    emit("close")
  }
}

// ===== HOVER DESKTOP =====
const handleMouseEnter = () => {
  if (window.innerWidth >= 768) {
    emit("expand")
  }
}

const handleMouseLeave = () => {
  if (window.innerWidth >= 768) {
    emit("collapse")
  }
}

const loadPermissions = async () => {
  try {

    const resUser = await api.get("/auth/me/")

    //console.log("USER DATA:", resUser.data)

    roleName.value = resUser.data.role   // 🔥 AQUÍ ESTÁ EL FIX

    const roleId = resUser.data.role_id

    const res = await api.get(`/roles/${roleId}/modules/`)

    permissions.value = res.data

    //console.log("PERMISSIONS:", permissions.value)

  } catch (error) {
    console.error("Error cargando permisos", error)
  }
}

function filterMenuByPermissions(menu, permissions) {
  //console.log("filterMenuByPermissions")

  // 🔥 SYSADMIN → SIN FILTRO
  if (roleName.value === "SYSADMIN") {
    //console.log("🟢 SYSADMIN → sin filtro")
    return menu
  }

  return menu
    .map(item => {

      const perm = permissions.find(p =>
        p.module_name?.toLowerCase().trim() === item.name?.toLowerCase().trim()
      )

      let children = []

      if (item.children && item.children.length) {
        children = item.children.filter(child => {
          const childPerm = permissions.find(p =>
            p.module_name?.toLowerCase().trim() === child.name?.toLowerCase().trim()
          )
          return childPerm?.can_view
        })
      }

      if (children.length > 0) {
        return { ...item, children }
      }

      if (perm?.can_view) {
        return { ...item, children: [] }
      }

      return null
    })
    .filter(Boolean)
}

const openMenus = ref({})

const toggleMenu = (id) => {
  if (openMenus.value[id]) {
    openMenus.value = {}
  } else {
    openMenus.value = { [id]: true }
  }
}

const openParentByRoute = (path) => {
  menu.value.forEach(item => {
    if (item.children?.length) {
      const match = item.children.find(child => child.route === path)
      if (match) {
        openMenus.value = { [item.id]: true }
      }
    }
  })
}

// Cuando SYSADMIN cambia de empresa → recargar menú de esa empresa
watch(
  () => companyStore.selectedCompany?.id,
  async (newId, oldId) => {
    if (newId && newId !== oldId) {
      ready.value = false
      await menuStore.loadMenu(newId)
      ready.value = true
      openParentByRoute(route.path)
    }
  }
)

onMounted(async () => {
  await loadPermissions()
  const companyId = companyStore.selectedCompany?.id ?? null
  await menuStore.loadMenu(companyId)
  ready.value = true
  openParentByRoute(route.path)
})


</script>

<style>

/* ===== SIDEBAR BASE ===== */
.sidebar {
  height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar-left {
  position: relative;
}

/* 🔥 LÍNEA BASE (UNA SOLA) */
.sidebar-left::before {
  content: "";
  position: absolute;
  top: 0;
  right: 0;
  width: 8px;
  height: 100%;
  background: #3b82f6;
}

/* ===== MENU ===== */

.sidebar-menu{
  list-style:none;
  padding:0;
}

.sidebar-menu li{
  margin-bottom:10px;
}

.sidebar-menu a{
  position: relative;

  color:#cbd5f5;
  text-decoration:none;
  display:flex;
  align-items:center;
  gap:12px;

  padding:10px 12px;
  border-radius:10px;

  transition: all 0.2s ease;
}

/* ===== HOVER ===== */

.sidebar-menu a:hover{
  background: rgba(255,255,255,0.08);
}

.sidebar-menu a,
.menu-parent {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* ===== ICONOS ===== */

.sidebar-menu .icon {
  font-size: 20px;
  min-width: 28px;
  display:flex;
  align-items:center;
  justify-content:center;

  color: #94a3b8;
  opacity: 0.9;

  transition: all 0.2s ease;
}

/* hijos más visibles */
.submenu .icon {
  font-size: 19px;
  color: #cbd5f5;
  opacity: 1;
}

/* icono activo */
.sidebar-menu a.active .icon {
  color: #ffffff;
  transform: scale(1.1);
}

/* ===== SUBMENU ===== */

.submenu {
  list-style: none;
  padding-left: 28px;

  max-height: 0;
  overflow: hidden;

  opacity: 0;
  transform: translateY(-5px);
  transition: all 0.25s ease;
}

.submenu.open {
  max-height: none;
  opacity: 1;
  transform: translateY(0);
}

/* =====================================================
   🔥 ACTIVO MODO EXPANDIDO (FORMA CONTINUA REAL)
===================================================== */

.sidebar-menu a.active {
  background: #3b82f6;
  color: white;
  border-radius: 12px;
}

/* curva superior */
/* eliminar residuos visuales */
.sidebar-menu a.active::before,
.sidebar-menu a.active::after {
  display: none;
}



/* =====================================================
   🔥 MODO MINI
===================================================== */

.sidebar-left.collapsed .title {
  display: none;
  white-space: nowrap;
}

.sidebar-left.collapsed .menu-parent i.bi-chevron-down,
.sidebar-left.collapsed .menu-parent i.bi-chevron-right {
  display: none;
}

.sidebar-left.collapsed .sidebar-menu a,
.sidebar-left.collapsed .menu-parent {
  justify-content: center;
  padding: 12px 0;
}

/* =====================================================
   🔥 ACTIVO MINI (MISMA FORMA CONTINUA)
===================================================== */

.sidebar-left.collapsed .sidebar-menu a.active {
  background: #3b82f6;
  border-radius: 18px;

  width: 56px;
  height: 56px;

  margin: 10px auto;

  display: flex;
  align-items: center;
  justify-content: center;

  z-index: 2;
}

/* curva superior mini */
.sidebar-left.collapsed .sidebar-menu a.active::before {
  content: "";
  position: absolute;
  right: -6px;
  top: -12px;

  width: 20px;
  height: 20px;

  box-shadow: -10px 10px 0 #3b82f6;
}

/* curva inferior mini */
.sidebar-left.collapsed .sidebar-menu a.active::after {
  content: "";
  position: absolute;
  right: -6px;
  bottom: -12px;

  width: 20px;
  height: 20px;

  box-shadow: -10px -10px 0 #3b82f6;
}

/* icono activo mini */
.sidebar-left.collapsed .sidebar-menu a.active .icon {
  color: white;
  font-size: 22px;
}

/* ===== HOVER MINI ===== */

.sidebar-left.collapsed .sidebar-menu a:hover {
  background: rgba(59,130,246,0.15);
  border-radius: 12px;
}
/* =========================================
FIX SCROLL REAL SIDEBAR
========================================= */

.sidebar-left {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 🔥 CONTENEDOR DEL MENÚ */
.sidebar-menu {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding-bottom: 80px;
}


/* 🔥 Mejora en móviles */
@media (max-width: 768px) {
  .sidebar {
    height: 100vh;
    overflow-y: auto;
  }
}

/* 🔥 Landscape móvil */
@media (max-height: 500px) {
  .sidebar {
    height: 100vh;
    overflow-y: auto;
  }
}

/* =========================================
MOBILE FIX REAL
========================================= */

@media (max-width: 768px) {
  .sidebar-left {
    height: 100dvh; /* 🔥 mejor que 100vh en móviles */
  }
}
</style>