<template>
  <div class="acceso">
    <form class="acceso__caja" @submit.prevent="ingresar" novalidate>
      <div class="acceso__logo"><Icono nombre="candado" :tam="32" /></div>
      <h1>Panel de administración</h1>
      <p class="acceso__sub">Solo para el administrador del negocio.</p>
      <label class="campo">
        <span>Clave de administrador</span>
        <input v-model="clave" class="entrada" type="password" maxlength="64" autocomplete="current-password" autofocus />
      </label>
      <p v-if="error" class="acceso__error">{{ error }}</p>
      <button class="btn btn--primario btn--bloque" :disabled="enviando || !clave">
        <span v-if="enviando" class="giro" style="width:20px;height:20px;border-width:2px"></span>
        <template v-else>Ingresar</template>
      </button>
      <button type="button" class="acceso__enlace" @click="$router.push('/cuentas')">Ir a la toma de pedidos</button>
    </form>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue"
import { useRoute, useRouter } from "vue-router"
import Icono from "../../componentes/Icono.vue"
import { api, guardarAdmin } from "../../api"

const router = useRouter()
const route = useRoute()
const clave = ref("")
const error = ref("")
const enviando = ref(false)

// Botón del programa de escritorio: llega con un código de un solo uso (vence en 30 s) y entra sin clave.
// El código se quita de la dirección de inmediato (no queda en el historial).
onMounted(async () => {
  const codigo = String(route.query.codigo || "")
  if (!codigo) return
  router.replace({ path: "/admin/ingresar" })
  if (!/^[A-Za-z0-9_-]{20,64}$/.test(codigo)) return
  enviando.value = true
  try {
    const r = await api.admin.post("/ingresar-codigo", { codigo })
    guardarAdmin(r.token)
    router.replace("/admin")
  } catch (e) {
    error.value = e.message
  } finally {
    enviando.value = false
  }
})

async function ingresar() {
  error.value = ""
  enviando.value = true
  try {
    const r = await api.admin.post("/ingresar", { clave: clave.value })
    guardarAdmin(r.token)
    router.replace("/admin")
  } catch (e) {
    error.value = e.message
    clave.value = ""
  } finally {
    enviando.value = false
  }
}
</script>
