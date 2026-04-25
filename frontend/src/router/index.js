/* ========================================= 
IMPORTACIÓN DE HERRAMIENTAS DE VUE ROUTER
========================================= */

import { createRouter, createWebHistory } from "vue-router"

/* =========================================
IMPORTACIÓN DE VISTAS
========================================= */

import LoginView from "../views/LoginView.vue"
import AssetCategoriesView from "../views/AssetCategoriesView.vue"
import MainLayout from "../components/layout/MainLayout.vue"
import DashboardView from "../views/DashboardView.vue"
import ProfilesView from "@/views/ProfilesView.vue"
import { showToast } from "@/utils/toast" // ajusta ruta si es distinta
import SystemModulesView from "@/views/SystemModulesView.vue"
import BusinessProfilesView  from "@/views/BusinessProfilesView.vue"
import UsersView from "../views/UsersView.vue"
import TareasView from "../views/TareasView.vue"
import RolesView from "../views/system/RolesView.vue"
import ForgotPassword from "@/views/auth/ForgotPassword.vue"
import ResetPassword from "@/views/auth/ResetPassword.vue"
import api from "@/services/apis"

/* =========================================
DEFINICIÓN DE RUTAS DEL SISTEMA
========================================= */

const routes = [
  
  /* =========================================
     LOGIN
  ========================================= */
  {
    path: "/login",
    name: "login",
    component: LoginView,
    meta: { title: "LoginView" }
  },

  {
    path: "/forgot-password",
    name: "forgot-password",
    component: ForgotPassword,
    meta: { title: "ForgotPassword" }
  },

  {
    path: "/reset-password",
    name: "reset-password",
    component: ResetPassword,
    meta: { title: "ResetPassword" }
  },


  /* =========================================
     LAYOUT PRINCIPAL (DASHBOARD)
  ========================================= */
  {
    path: "/",
    component: MainLayout,
    meta: { title: "MainLayout" },

    children: [

      /* REDIRECCIÓN INICIAL */
      {
        path: "",
        redirect: "dashboard"
      },

      /* DASHBOARD */
      {
        path: "dashboard",
        name: "dashboard",
        component: DashboardView,
        requiresAuth: true,
        meta: { title: "DashboardView" }
      },


      {
        path: "/configuration/users",
        name: "users",
        component: UsersView,
        requiresAuth: true,
        meta: { title: "UsersView" }
      },

      {
        path: "/configuration/assets",
        name: "assets",
        component: () => import("@/views/AssetsView.vue"),
        requiresAuth: true,
        meta: { title: "AssetsView" }
      },

      {
        path: "/configuration/workers",
        name: "WorkersView",
        component: () => import("@/views/WorkersView.vue"),
        requiresAuth: true,
        meta: { title: "WorkersView" }
      },
      {
        path: "/configuration/roles",
        name: "roles",
        component: () => import("@/views/system/RolesView.vue"),
        requiresAuth: true,
        meta: { title: "RolesView" }
      },

      {
        path: "/configuration/tasks",
        name: "tasks",
        component: TareasView,
        requiresAuth: true,
        meta: { title: "TareasView" }
      },
      {
        path: "/tasks/my-tasks",
        name: "TaskLeaderView",
        component: () => import("@/views/TaskLeaderView.vue"),
        requiresAuth: true,
        meta: { title: "TaskLeaderView" }
      },
      {
        path: "/tasks/:taskId/evidencias",
        name: "TaskEvidenciaView",
        component: () => import("@/views/TaskEvidenciaView.vue"),
        requiresAuth: true,
        meta: { title: "TaskEvidenciaView" }
      },
      {
        path: "/tasks/:taskId/materiales",
        name: "TaskMaterialesView",
        component: () => import("@/views/TaskMaterialesView.vue"),
        requiresAuth: true,
        meta: { title: "TaskMaterialesView" }
      },
      {
        path: "/tasks/supervision",
        name: "AuditorView",
        component: () => import("@/views/AuditorView.vue"),
        requiresAuth: true,
        meta: { title: "AuditorView" }
      },
      {
        path: "/tasks/:taskId/reportes",
        name: "TaskReportesView",
        component: () => import("@/views/TaskReportesView.vue"),
        requiresAuth: true,
        meta: { title: "TaskReportesView" }
      },
      {
        path: "/assets/:assetId/historial",
        name: "AssetHistoryView",
        component: () => import("@/views/AssetHistoryView.vue"),
        requiresAuth: true,
        meta: { title: "AssetHistoryView" }
      },
      {
        path: "/tasks/:taskId/analisis",
        name: "TaskAnalisisView",
        component: () => import("@/views/TaskAnalisisView.vue"),
        requiresAuth: true,
        meta: { title: "TaskAnalisisView" }
      },
      {
        path: "/tasks/reporte-general",
        name: "TaskReporteGeneralView",
        component: () => import("@/views/TaskReporteGeneralView.vue"),
        requiresAuth: true,
        meta: { title: "TaskReporteGeneralView" }
      },
      /* MÓDULOS SYSTEM
      /* PERFIL (CONFIGURACIÓN EMPRESA) */
      /* MÓDULOS EMPRESA*/  

      {
        path: "/companies/create",
        component: () => import("@/views/system/CompaniesView.vue"),
        meta: { title: "CompaniesView" }
      },
      {
        path: "/companies/list",
        component: () => import("@/views/system/CompaniesListView.vue"),
        meta: { title: "CompaniesListView" }
      },
      {
        path: "/companies/system-modules",
        name: "SystemModulesView",
        component: () => import("@/views/SystemModulesView.vue"),
        requiresAuth: true,
        meta: { title: "SystemModulesView" }
      },

      {
        path: "/companies/businessprofiles",
        name: "BusinessProfiles",
        component: () => import("@/views/BusinessProfilesView.vue"),
        meta: { title: "BusinessProfilesView" }
      },
      {
        path: "/companies/business-profiles-detail",
        name: "BusinessProfileDetail",
        component: () => import("@/views/BusinessProfileDetail.vue"),
        meta: { title: "BusinessProfileDetail" }
      },

      {
        path: "/companies/sysadmin",
        name: "SidebarMenuManagerView",
        component: () => import("@/views/sysadmin/SidebarMenuManagerView.vue"),
        requiresAuth: true,
        meta: { title: "SidebarMenuManagerView" }
      },
      {
        path: "/sysadmin/plans",
        name: "PlansView",
        component: () => import("@/views/sysadmin/PlansView.vue"),
        requiresAuth: true,
        meta: { title: "PlansView" }
      },
      {
        path: "/sysadmin/company-plans",
        name: "CompanyPlansView",
        component: () => import("@/views/sysadmin/CompanyPlansView.vue"),
        requiresAuth: true,
        meta: { title: "CompanyPlansView" }
      },



      {
        path: "/profiles",
        component: () => import("@/views/ProfilesView.vue"),
        meta: { title: "ProfilesView" }
      },
     

      /**
       * 
       */
]
  }


]

/* =========================================
CREACIÓN DEL ROUTER
========================================= */

const router = createRouter({
  history: createWebHistory(),
  routes
})

/* =========================================
PROTECCIÓN GLOBAL DE RUTAS
========================================= */
router.beforeEach(async (to, from, next) => {

  const token = localStorage.getItem("token")

  /* =========================================
     🔥 EXCEPCIONES PÚBLICAS
  ========================================= */
  if (
    to.path === "/login" ||
    to.path === "/forgot-password" ||
    to.path === "/reset-password" ||
    to.path === "/business-profiles"
  ) {
    return next()
  }

  /* =========================================
     1. SI NO HAY TOKEN
  ========================================= */
  if (!token) {
    return next("/login")
  }

  /* =========================================
     2. VALIDAR SESIÓN EN BACKEND
  ========================================= */
  try {
    await api.get("/auth/me/")
  } catch (error) {
    localStorage.removeItem("token")
    localStorage.removeItem("menu")
    localStorage.removeItem("user")
    return next("/login")
  }

  /* ========================================= 
     3. SI ESTÁ LOGUEADO Y VA A LOGIN
  ========================================= */
  if (to.path === "/login") {
    return next("/dashboard")
  }

  /* =========================================
     4. VALIDAR PERMISOS
  ========================================= */
  try {

    const menu = JSON.parse(localStorage.getItem("menu")) || []

    if (!menu.length) {
      return next()
    }

    const hasAccess = (items, path) => {
      for (const item of items) {
        if (item.route === path) return true

        if (item.children && item.children.length) {
          if (hasAccess(item.children, path)) return true
        }
      }
      return false
    }

    if (to.meta.requiresAuth) {

      const allowed = hasAccess(menu, to.path)

      if (!allowed) {
        showToast("No tienes permisos para acceder a este módulo", "error")

        localStorage.removeItem("token")
        localStorage.removeItem("menu")
        localStorage.removeItem("user")

        return next("/login")
      }
    }

  } catch (error) {
    showToast("Error validando permisos", "error")
    return next("/login")
  }

  return next()
})

/* =========================================
EXPORTACIÓN DEL ROUTER
========================================= */

export default router