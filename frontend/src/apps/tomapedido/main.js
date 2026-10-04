import { createApp } from "vue"
import { createRouter, createWebHashHistory } from "vue-router"
import App from "./App.vue"
import { sesion } from "./sesion"
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
    { path: "/:pathMatch(.*)*", redirect: "/cuentas" },
  ],
})

router.beforeEach((to) => {
  if (to.meta.publica) return true
  if (sesion.token) return true
  return sesion.secreto && sesion.estado === "pendiente" ? "/espera" : (sesion.usuario ? "/ingresar" : "/registro")
})

createApp(App).use(router).mount("#app")
