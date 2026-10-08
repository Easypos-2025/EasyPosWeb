<template>
  <div class="acceso">
    <form class="acceso__caja" @submit.prevent="registrar" novalidate>
      <div class="acceso__logo"><Icono nombre="usuario" :tam="32" /></div>
      <h1>Registrar dispositivo</h1>
      <p class="acceso__sub">Después pida en caja que lo active en "Dispositivos nuevos".</p>

      <label class="campo">
        <span>Nombre de este dispositivo</span>
        <input v-model.trim="f.nombre_dispositivo" class="entrada" maxlength="40" placeholder="Ej: Celular Ana" autocomplete="off" />
      </label>
      <label class="campo">
        <span>Usuario</span>
        <input v-model.trim="f.usuario" class="entrada" maxlength="25" autocapitalize="none" autocomplete="username" placeholder="Sin espacios" />
      </label>
      <label class="campo">
        <span>Clave</span>
        <input v-model="f.clave" class="entrada" type="password" maxlength="64" autocomplete="new-password" />
      </label>
      <label class="campo">
        <span>Repita la clave</span>
        <input v-model="f.clave2" class="entrada" type="password" maxlength="64" autocomplete="new-password" />
      </label>

      <p v-if="error" class="acceso__error">{{ error }}</p>
      <button class="btn btn--primario btn--bloque" :disabled="enviando">
        <span v-if="enviando" class="giro" style="width:20px;height:20px;border-width:2px"></span>
        <template v-else>Registrar</template>
      </button>
      <button type="button" class="acceso__enlace" @click="$router.push('/ingresar')">Ya tengo usuario: ingresar</button>
      <VersionAgente />
    </form>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue"
import { useRouter } from "vue-router"
import Icono from "../componentes/Icono.vue"
import VersionAgente from "../componentes/VersionAgente.vue"
import { api } from "../api"
import { guardarSesion } from "../sesion"

const router = useRouter()
const f = reactive({ nombre_dispositivo: "", usuario: "", clave: "", clave2: "" })
const error = ref("")
const enviando = ref(false)

function validar() {
  if (!/^[A-Za-z0-9 ._-]{2,40}$/.test(f.nombre_dispositivo)) return "Nombre del dispositivo: de 2 a 40 letras o números, sin tildes ni símbolos."
  if (!/^[A-Za-z0-9._-]{3,25}$/.test(f.usuario)) return "Usuario: de 3 a 25 letras o números, sin espacios."
  if (f.clave.length < 4) return "La clave debe tener mínimo 4 caracteres."
  if (f.clave !== f.clave2) return "Las claves no coinciden."
  return ""
}

async function registrar() {
  error.value = validar()
  if (error.value) return
  enviando.value = true
  try {
    const r = await api.post("/dispositivos/registro", {
      nombre_dispositivo: f.nombre_dispositivo, usuario: f.usuario, clave: f.clave,
    })
    guardarSesion({ secreto: r.secreto, estado: "pendiente", usuario: r.usuario,
                    nombre_dispositivo: r.nombre_dispositivo, token: "", mesero: null })
    router.replace("/espera")
  } catch (e) {
    error.value = e.message
  } finally {
    enviando.value = false
  }
}
</script>
