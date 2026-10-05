<template>
  <div class="ad">
    <header class="barra">
      <button class="barra__btn ad__menu-btn" title="Menú" @click="menuAbierto = !menuAbierto"><Icono nombre="menu" /></button>
      <div class="barra__titulo">
        <h1>{{ empresa || "Panel de administración" }}</h1>
        <small>Panel de administración · EasyPos Agente Local</small>
      </div>
      <button class="barra__btn" title="Salir del panel" @click="salir"><Icono nombre="salir" /></button>
    </header>

    <div class="ad__cuerpo">
      <!-- Sidebar: aquí se irán agregando las utilidades que hoy están en el escritorio -->
      <div v-if="menuAbierto" class="ad__velo" @click="menuAbierto = false"></div>
      <nav class="ad__lateral" :class="{ 'ad__lateral--abierto': menuAbierto }">
        <router-link v-for="m in MENU" :key="m.ruta" :to="m.ruta" class="ad__item" :class="{ 'ad__item--activo': activo(m) }"
                     @click="menuAbierto = false">
          <Icono :nombre="m.icono" />
          <span>{{ m.nombre }}</span>
          <b v-if="m.contador && contadores[m.contador]" class="ad__badge">{{ contadores[m.contador] }}</b>
        </router-link>
        <div class="ad__sep"></div>
        <router-link to="/cuentas" class="ad__item"><Icono nombre="lista" /><span>Toma de pedidos</span></router-link>
      </nav>

      <main class="ad__contenido">
        <AvisoActualizacion />
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, provide, ref } from "vue"
import { useRoute, useRouter } from "vue-router"
import Icono from "../../componentes/Icono.vue"
import AvisoActualizacion from "../../componentes/AvisoActualizacion.vue"
import { api, guardarAdmin } from "../../api"

// Menú del panel (agregar aquí las nuevas utilidades)
const MENU = [
  { ruta: "/admin",              nombre: "Dashboard",    icono: "tablero" },
  { ruta: "/admin/errores",      nombre: "Errores",      icono: "alerta", contador: "errores" },
  { ruta: "/admin/dispositivos", nombre: "Dispositivos", icono: "celular", contador: "sinConexion" },
  { ruta: "/admin/fotos",        nombre: "Fotos de la web", icono: "foto" },
  { ruta: "/admin/clave",        nombre: "Clave",        icono: "candado" },
]

const route = useRoute()
const router = useRouter()
const menuAbierto = ref(false)
const resumen = ref(null)
const empresa = computed(() => resumen.value?.empresa || "")
const contadores = computed(() => {
  const d = resumen.value?.dispositivos || {}
  return { errores: resumen.value?.errores?.sin_resolver || 0,
           sinConexion: Math.max(0, (d.total || 0) - (d.conectados || 0) - (d.bloqueados || 0)) }
})
let temporizador = null

// El resumen lo comparten el menú (contadores) y las vistas del panel
async function cargarResumen() {
  try { resumen.value = await api.admin.get("/resumen") } catch { /* se reintenta en el próximo ciclo */ }
}
provide("resumen", resumen)
provide("actualizacion", computed(() => resumen.value?.actualizacion || null))
provide("recargarResumen", cargarResumen)
onMounted(() => { cargarResumen(); temporizador = setInterval(cargarResumen, 20000) })
onBeforeUnmount(() => clearInterval(temporizador))

const activo = (m) => (m.ruta === "/admin" ? route.path === "/admin" : route.path.startsWith(m.ruta))

function salir() {
  guardarAdmin("")
  router.replace("/admin/ingresar")
}
</script>

<style scoped>
.ad { min-height: 100vh; }
.ad__cuerpo { display: grid; grid-template-columns: 240px 1fr; min-height: calc(100vh - var(--barra-alto)); }
.ad__lateral { background: #fff; border-right: 1px solid var(--borde); padding: 14px 10px; display: flex; flex-direction: column; gap: 4px;
               position: sticky; top: var(--barra-alto); height: calc(100vh - var(--barra-alto)); overflow-y: auto; }
.ad__item { display: flex; align-items: center; gap: 10px; min-height: 46px; padding: 0 12px; border-radius: 10px;
            color: var(--texto); text-decoration: none; font-weight: 600; }
.ad__item:hover { background: var(--fondo); }
.ad__item--activo { background: var(--navy); color: #fff; }
.ad__item--activo:hover { background: var(--navy); }
.ad__item span { flex: 1; }
.ad__badge { min-width: 24px; height: 24px; padding: 0 7px; border-radius: 999px; background: var(--rojo); color: #fff;
             font-size: 12px; display: inline-flex; align-items: center; justify-content: center; }
.ad__sep { height: 1px; background: var(--borde); margin: 8px 4px; }
.ad__contenido { padding: 20px; min-width: 0; }
.ad__menu-btn { display: none; }
.ad__velo { display: none; }

@media (max-width: 1024px) {
  .ad__cuerpo { grid-template-columns: 1fr; }
  .ad__menu-btn { display: inline-flex; }
  .ad__lateral { position: fixed; z-index: 60; left: 0; top: var(--barra-alto); width: min(80vw, 280px);
                 transform: translateX(-105%); transition: transform .2s ease; box-shadow: var(--sombra); }
  .ad__lateral--abierto { transform: none; }
  .ad__velo { display: block; position: fixed; inset: var(--barra-alto) 0 0 0; z-index: 55; background: rgba(15, 23, 42, .35); }
}
@media (max-width: 768px) {
  .ad__contenido { padding: 12px; }
}
@media (max-width: 576px) {
  .ad__contenido { padding: 10px; }
}
</style>
