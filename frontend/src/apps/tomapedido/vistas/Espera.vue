<template>
  <div class="acceso">
    <div class="acceso__caja espera">
      <div class="acceso__logo"><Icono :nombre="estado === 'inactivo' ? 'candado' : 'reloj'" :tam="32" /></div>
      <h1>{{ estado === "inactivo" ? "Dispositivo desactivado" : "Esperando activación" }}</h1>
      <p class="acceso__sub">
        <template v-if="estado === 'inactivo'">Este dispositivo fue desactivado en el equipo de caja.</template>
        <template v-else>Pida en caja que active este dispositivo en <b>Dispositivos nuevos</b>.</template>
      </p>

      <div class="espera__datos tarjeta">
        <div><span>Usuario</span><b>{{ sesion.usuario }}</b></div>
        <div><span>Dispositivo</span><b>{{ sesion.nombre_dispositivo || "—" }}</b></div>
      </div>

      <div v-if="estado !== 'inactivo'" class="espera__giro"><span class="giro"></span> Revisando cada 5 segundos…</div>
      <p v-if="error" class="acceso__error">{{ error }}</p>

      <button class="btn btn--primario btn--bloque" @click="revisar(true)">Ya me activaron</button>
      <button class="acceso__enlace" @click="otroUsuario">Usar otro usuario</button>
      <VersionAgente />
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import Icono from "../componentes/Icono.vue"
import VersionAgente from "../componentes/VersionAgente.vue"
import { api } from "../api"
import { guardarSesion, sesion } from "../sesion"
import { showToast } from "@/utils/toast"

const router = useRouter()
const estado = ref("pendiente")
const error = ref("")
let temporizador = null

async function revisar(manual = false) {
  if (!sesion.secreto) return router.replace("/ingresar")
  try {
    const r = await api.get("/dispositivos/estado", null, { "X-Ag-Dispositivo": sesion.secreto })
    estado.value = r.estado
    error.value = ""
    if (r.estado === "activo") {
      guardarSesion({ estado: "activo" })
      showToast("Dispositivo activado. Ingrese su clave.", "success", 2500)
      router.replace("/ingresar")
    } else if (manual) {
      showToast("Todavía no lo han activado en caja.", "info", 2500)
    }
  } catch (e) {
    error.value = e.message
    if (e.estado === 401) {          // el agente no reconoce este navegador
      guardarSesion({ secreto: "", estado: "" })
      router.replace("/ingresar")
    }
  }
}

function otroUsuario() {
  guardarSesion({ secreto: "", estado: "", usuario: "", nombre_dispositivo: "", token: "", mesero: null })
  router.replace("/registro")
}

onMounted(() => { revisar(); temporizador = setInterval(revisar, 5000) })
onBeforeUnmount(() => clearInterval(temporizador))
</script>

<style scoped>
.espera__datos { padding: 12px 14px; margin-bottom: 16px; box-shadow: none; background: var(--fondo); }
.espera__datos div { display: flex; justify-content: space-between; gap: 10px; padding: 4px 0; font-size: 14px; }
.espera__datos span { color: var(--texto-suave); }
.espera__giro { display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 16px; color: var(--texto-suave); font-size: 14px; }
.espera__giro .giro { width: 20px; height: 20px; border-width: 2px; }
</style>
