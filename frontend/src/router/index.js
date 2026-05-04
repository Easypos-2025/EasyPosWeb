/* ========================================= 
IMPORTACIÓN DE HERRAMIENTAS DE VUE ROUTER
========================================= */

import { createRouter, createWebHistory } from "vue-router"

/* =========================================
IMPORTACIÓN DE VISTAS
========================================= */

import LoginView from "../views/LoginView.vue"
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
  /* Landing en raíz — la URL queda como easyposweb.com sin /landing */
  {
    path: "/",
    name: "landing",
    component: () => import("@/views/LandingView.vue"),
    meta: { title: "EasyPosWeb — Tu negocio en línea" }
  },

  /* /landing redirige a / para no romper bookmarks ni links internos */
  {
    path: "/landing",
    redirect: "/"
  },

  {
    path: "/landing/perfil/:id",
    name: "LandingProfile",
    component: () => import("@/views/LandingProfileView.vue"),
    meta: { title: "EasyPosWeb — Propuesta personalizada" }
  },

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
    path: "/invite/:token",
    name: "InviteRegister",
    component: () => import("@/views/InviteRegisterView.vue"),
    meta: { title: "Registro por invitación" }
  },

  {
    path: "/register",
    name: "RegisterAssociate",
    component: () => import("@/views/RegisterAssociateView.vue"),
    meta: { title: "Crear cuenta — EasyPosWeb" }
  },

  {
    path: "/payment-pending",
    name: "PaymentPending",
    component: () => import("@/views/PaymentPendingView.vue"),
    meta: { title: "Activa tu plan — EasyPosWeb" }
  },
  {
    path: "/payment-history",
    name: "PaymentHistoryAssociate",
    component: () => import("@/views/PaymentHistoryAssociateView.vue"),
    requiresAuth: true,
    meta: { title: "Historial de Pagos" }
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
  // ── Página pública QR préstamo (sin auth, sin layout) ──────────
  {
    path: "/prestamo-qr/:token",
    name: "QrPrestamoPublic",
    component: () => import("@/views/QrPrestamoPublic.vue"),
    meta: { title: "Confirmar Préstamo" }
  },

  {
    path: "/",
    component: MainLayout,
    meta: { title: "MainLayout" },

    children: [

      /* REDIRECCIÓN INICIAL */
      {
        path: "",
        redirect: "/dashboard"
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
        path: "/configuration/asset-categories",
        name: "AssetCategoriesView",
        component: () => import("@/views/AssetCategoriesView.vue"),
        requiresAuth: true,
        meta: { title: "Categorías de Activos" }
      },

      {
        path: "/configuration/clients",
        name: "ClientsView",
        component: () => import("@/views/ClientsView.vue"),
        requiresAuth: true,
        meta: { title: "ClientsView" }
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
        path: "/tasks/completar-info",
        name: "TaskCompletarInfoView",
        component: () => import("@/views/TaskCompletarInfoView.vue"),
        requiresAuth: true,
        meta: { title: "TaskCompletarInfoView" }
      },

      {
        path: "/notifications/inbox",
        name: "NotificationsInbox",
        component: () => import("@/views/notifications/InboxView.vue"),
        requiresAuth: true,
        meta: { title: "Bandeja de Entrada" }
      },
      {
        path: "/notifications/outbox",
        name: "NotificationsOutbox",
        component: () => import("@/views/notifications/OutboxView.vue"),
        requiresAuth: true,
        meta: { title: "Mensajes Enviados" }
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
        path: "/tasks/:taskId/detalle",
        name: "TareaDetalleView",
        component: () => import("@/views/TareaDetalleView.vue"),
        requiresAuth: true,
        meta: { title: "TareaDetalleView" }
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

      {
        path: "/novedades",
        name: "NovedadesView",
        component: () => import("@/views/NovedadesView.vue"),
        meta: { title: "Registro de Novedades" }
      },

      {
        path: "/soporte/ticket",
        name: "SoporteTicketView",
        component: () => import("@/views/SoporteTicketView.vue"),
        meta: { title: "Tickets de Soporte" }
      },

      {
        path: "/sysadmin/topbar-menu",
        name: "TopbarMenuManagerView",
        component: () => import("@/views/sysadmin/TopbarMenuManagerView.vue"),
        meta: { title: "Gestión Menú Topbar" }
      },

      {
        path: "/sysadmin/system-config",
        name: "SystemConfigView",
        component: () => import("@/views/sysadmin/SystemConfigView.vue"),
        meta: { title: "Configuración del Sistema" }
      },

      {
        path: "/sysadmin/email-footer",
        name: "EmailFooterConfigView",
        component: () => import("@/views/sysadmin/EmailFooterConfigView.vue"),
        meta: { title: "Firma de Email" }
      },

      {
        path: "/sysadmin/landing-manager",
        name: "LandingManagerView",
        component: () => import("@/views/sysadmin/LandingManagerView.vue"),
        requiresAuth: true,
        meta: { title: "Gestión Landing Page" }
      },

      {
        path: "/sysadmin/payment-review",
        name: "PaymentReviewView",
        component: () => import("@/views/sysadmin/PaymentReviewView.vue"),
        requiresAuth: true,
        meta: { title: "Revisión de Pagos" }
      },
      {
        path: "/sysadmin/payment-history",
        name: "PaymentHistoryView",
        component: () => import("@/views/sysadmin/PaymentHistoryView.vue"),
        requiresAuth: true,
        meta: { title: "Historial de Pagos" }
      },

      {
        path: "/navigation-map",
        name: "NavigationMapView",
        component: () => import("@/views/NavigationMapView.vue"),
        requiresAuth: true,
        meta: { title: "Guía de Módulos" }
      },

      {
        path: "/sysadmin/menu-map",
        name: "ProfileMenuMapView",
        component: () => import("@/views/sysadmin/ProfileMenuMapView.vue"),
        requiresAuth: true,
        meta: { title: "Mapa de Menú por Perfil" }
      },

      // ── Facturación (placeholders) ──────────────────────────────
      {
        path: "/facturacion/ventas/factura",
        name: "FacturacionFacturaView",
        component: () => import("@/views/FacturacionFacturaView.vue"),
        requiresAuth: true,
        meta: { title: "Factura" }
      },
      {
        path: "/facturacion/ventas/recibo",
        name: "FacturacionReciboView",
        component: () => import("@/views/FacturacionReciboView.vue"),
        requiresAuth: true,
        meta: { title: "Recibo" }
      },
      {
        path: "/facturacion/reportes/facturas",
        name: "FacturacionReporteFacturasView",
        component: () => import("@/views/FacturacionReporteFacturasView.vue"),
        requiresAuth: true,
        meta: { title: "Reporte de Facturas" }
      },
      {
        path: "/facturacion/reportes/recibos",
        name: "FacturacionReporteRecibosView",
        component: () => import("@/views/FacturacionReporteRecibosView.vue"),
        requiresAuth: true,
        meta: { title: "Reporte de Recibos" }
      },

      // ── Préstamos de bodega ─────────────────────────────────────
      {
        path: "/configuration/colaboradores-externos",
        name: "ColaboradoresExternosView",
        component: () => import("@/views/ColaboradoresExternosView.vue"),
        requiresAuth: true,
        meta: { title: "Colaboradores Externos" }
      },
      {
        path: "/configuration/bodega",
        name: "BodegaItemsView",
        component: () => import("@/views/BodegaItemsView.vue"),
        requiresAuth: true,
        meta: { title: "Bodega" }
      },
      {
        path: "/loans/prestamos",
        name: "LoansView",
        component: () => import("@/views/LoansView.vue"),
        requiresAuth: true,
        meta: { title: "Préstamos" }
      },

      // ── Catálogos de tareas ─────────────────────────────────────
      {
        path: "/configuration/insumos",
        name: "InsumosCrudView",
        component: () => import("@/views/InsumosCrudView.vue"),
        requiresAuth: true,
        meta: { title: "Insumos" }
      },
      {
        path: "/configuration/unidades-medida",
        name: "UnidadesMedidaView",
        component: () => import("@/views/UnidadesMedidaView.vue"),
        requiresAuth: true,
        meta: { title: "Unidades de Medida" }
      },
      {
        path: "/configuration/conceptos-gastos",
        name: "ConceptosGastosView",
        component: () => import("@/views/ConceptosGastosView.vue"),
        requiresAuth: true,
        meta: { title: "Conceptos de Gasto" }
      },
      {
        path: "/configuration/conceptos-compras",
        name: "ConceptosComprasView",
        component: () => import("@/views/ConceptosComprasView.vue"),
        requiresAuth: true,
        meta: { title: "Conceptos de Compra" }
      },

      // ── Inventario ─────────────────────────────────────────────────
      {
        path: "/inventory/suppliers",
        name: "SuppliersView",
        component: () => import("@/views/inventory/SuppliersView.vue"),
        requiresAuth: true,
        meta: { title: "Proveedores" }
      },
      {
        path: "/inventory/supply-items",
        name: "SupplyItemsView",
        component: () => import("@/views/inventory/SupplyItemsView.vue"),
        requiresAuth: true,
        meta: { title: "Insumos" }
      },
      {
        path: "/inventory/categories",
        name: "ProductCategoriesView",
        component: () => import("@/views/inventory/ProductCategoriesView.vue"),
        requiresAuth: true,
        meta: { title: "Categorías de Producto" }
      },
      {
        path: "/inventory/price-lists",
        name: "PriceListsView",
        component: () => import("@/views/inventory/PriceListsView.vue"),
        requiresAuth: true,
        meta: { title: "Listas de Precios" }
      },
      {
        path: "/inventory/products",
        name: "ProductsView",
        component: () => import("@/views/inventory/ProductsView.vue"),
        requiresAuth: true,
        meta: { title: "Productos" }
      },
      {
        path: "/inventory/purchase-orders",
        name: "PurchaseOrdersView",
        component: () => import("@/views/inventory/PurchaseOrdersView.vue"),
        requiresAuth: true,
        meta: { title: "Entradas de Mercancía" }
      },
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
    to.path === "/" ||
    to.path === "/login" ||
    to.path === "/landing" ||
    to.path === "/forgot-password" ||
    to.path === "/reset-password" ||
    to.path === "/business-profiles" ||
    to.path === "/register" ||
    to.path === "/payment-pending" ||
    to.path.startsWith("/invite/") ||
    to.path.startsWith("/landing/perfil/") ||
    to.path.startsWith("/prestamo-qr/")
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
  let meData = null
  try {
    const meRes = await api.get("/auth/me/")
    meData = meRes.data
    localStorage.setItem("user", JSON.stringify({ ...JSON.parse(localStorage.getItem("user") || "{}"), ...meData }))
  } catch (error) {
    localStorage.removeItem("token")
    localStorage.removeItem("menu")
    localStorage.removeItem("user")
    return next("/login")
  }

  /* =========================================
     2b. GUARD DE PAGO PENDIENTE
     Si la empresa no está activa → solo puede ir a /payment-pending y /soporte/ticket
  ========================================= */
  const paymentStatus = meData?.payment_status ?? "active"
  const isSystem      = meData?.is_system ?? false
  // Estados que requieren ir a /payment-pending (bloquean el dashboard)
  const blockedStatuses   = ["pending_payment", "payment_submitted", "payment_rejected", "expired"]
  const allowedWithBlocked = ["/payment-pending", "/soporte/ticket"]

  if (!isSystem && blockedStatuses.includes(paymentStatus) && !allowedWithBlocked.includes(to.path)) {
    return next("/payment-pending")
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

    if (to.meta.requiresAuth && !isSystem) {

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