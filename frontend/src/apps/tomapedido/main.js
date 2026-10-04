import { createApp } from "vue"
import { createRouter, createWebHashHistory } from "vue-router"
import App from "./App.vue"
import { admin, encolarError, enviarCola } from "./api"
import { sesion } from "./sesion"
import { cargarTextos } from "./textos"
import "./estilos.css"

// Hash: el agente solo sirve archivos estáticos (no necesita reescribir rutas)
const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: "/",              redirect: "/cuentas" },
    { path: "/registro",      component: () => import("./vistas/Registro.vue"),  meta: { publica: true } },
    { path: "/espera",        component: () => import("./vistas/Espera.vue"),    meta: { publica: true } },
    { path: "/ingresar",      component: () => import("./vistas/Ingresar.vue"),  meta: { publica: true } },
    { path: "/cuentas",       component: () => import("./vistas/Cuentas.vue") },
    { path: "/mesas",         component: () => import("./vistas/Mesas.vue") },
    { path: "/pedido",        component: () => import("./vistas/Pedido.vue") },
    { path: "/cuenta",        component: () => import("./vistas/Cuenta.vue") },

    // Panel de administración de la empresa (PC de caja): sesión propia, no la del mesero
    { path: "/admin/ingresar", component: () => import("./vistas/admin/AdminIngresar.vue"), meta: { publica: true } },
    {
      path: "/admin", component: () => import("./vistas/admin/AdminLayout.vue"), meta: { admin: true },
      children: [
        { path: "",             component: () => import("./vistas/admin/AdminDashboard.vue") },
        { path: "errores",      component: () => import("./vistas/admin/AdminErrores.vue") },
        { path: "dispositivos", component: () => import("./vistas/admin/AdminDispositivos.vue") },
        { path: "fotos",        component: () => import("./vistas/admin/AdminFotos.vue") },
        { path: "clave",        component: () => import("./vistas/admin/AdminClave.vue") },
      ],
    },
    { path: "/:pathMatch(.*)*", redirect: "/cuentas" },
  ],
})

router.beforeEach((to) => {
  if (to.meta.publica) return true
  if (to.matched.some(r => r.meta.admin)) return admin.token ? true : "/admin/ingresar"
  if (sesion.token) { cargarTextos(); return true }
  return sesion.secreto && sesion.estado === "pendiente" ? "/espera" : (sesion.usuario ? "/ingresar" : "/registro")
})

const app = createApp(App).use(router)

// Errores de pantalla: quedan en el dispositivo y se envían al agente (panel y Monitor de la nube)
app.config.errorHandler = (err, _instancia, info) => {
  console.error(err)
  encolarError({ tipo: "VISTA", nivel: "ERROR", titulo: `${err?.name || "Error"}: ${String(err?.message || err).slice(0, 150)}`,
                 detalle: `${info || ""}\n${err?.stack || ""}`.slice(0, 4000) })
  enviarCola()
}

app.mount("#app")
