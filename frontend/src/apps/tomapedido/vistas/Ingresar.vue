<template>
  <div class="acceso">
    <form class="acceso__caja" @submit.prevent="ingresar" novalidate>
      <div class="acceso__logo"><Icono nombre="lista" :tam="32" /></div>
      <h1>Toma de Pedidos</h1>
      <p class="acceso__sub">{{ sesion.nombre_dispositivo || "Ingrese con su usuario" }}</p>

      <label class="campo">
        <span>Usuario</span>
        <input v-model.trim="usuario" class="entrada" maxlength="25" autocapitalize="none" autocomplete="username" />
      </label>
      <label class="campo">
        <span>Clave</span>
        <input ref="campoClave" v-model="clave" class="entrada" type="password" maxlength="64" autocomplete="current-password" />
      </label>

      <p v-if="error" class="acceso__error">{{ error }}</p>
      <button class="btn btn--primario btn--bloque" :disabled="enviando || !usuario || !clave">
        <span v-if="enviando" class="giro" style="width:20px;height:20px;border-width:2px"></span>
        <template v-else>Ingresar</template>
      </button>
      <button type="button" class="acceso__enlace" @click="$router.push('/registro')">Registrar este dispositivo</button>
      <p class="acceso__pie">Compilación {{ build }}</p>
    </form>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import Icono from "../componentes/Icono.vue"
import { api } from "../api"
import { guardarSesion, sesion } from "../sesion"

const router = useRouter()
const usuario = ref(sesion.usuario || "")
const clave = ref("")
const error = ref("")
const enviando = ref(false)
const campoClave = ref(null)
const build = typeof __APP_BUILD__ !== "undefined" ? __APP_BUILD__ : "dev"

async function ingresar() {
  error.value = ""
  enviando.value = true
  try {
    const r = await api.post("/sesion/ingresar", { usuario: usuario.value, clave: clave.value })
    if (r.estado === "activo") {
      guardarSesion({ token: r.token, secreto: r.secreto, estado: "activo", usuario: r.mesero.usuario,
                      nombre_dispositivo: r.mesero.nombre_dispositivo, mesero: r.mesero })
      router.replace("/cuentas")
    } else {
      guardarSesion({ secreto: r.secreto, estado: r.estado, usuario: usuario.value, token: "", mesero: null })
      router.replace("/espera")
    }
  } catch (e) {
    error.value = e.message
    clave.value = ""
  } finally {
    enviando.value = false
  }
}

onMounted(() => { if (usuario.value) campoClave.value?.focus() })
</script>
