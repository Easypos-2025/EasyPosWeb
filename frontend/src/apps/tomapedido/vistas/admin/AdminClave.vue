<template>
  <div>
    <div class="cab"><h2>Clave del administrador</h2></div>
    <form class="tarjeta panel" @submit.prevent="cambiar" novalidate>
      <p class="sub">Al cambiarla se cierran las sesiones del panel abiertas en otros equipos.</p>
      <label class="campo"><span>Clave actual</span>
        <input v-model="f.actual" class="entrada" type="password" maxlength="64" autocomplete="current-password" /></label>
      <label class="campo"><span>Nueva clave (mínimo 6)</span>
        <input v-model="f.nueva" class="entrada" type="password" maxlength="64" autocomplete="new-password" /></label>
      <label class="campo"><span>Repita la nueva clave</span>
        <input v-model="f.nueva2" class="entrada" type="password" maxlength="64" autocomplete="new-password" /></label>
      <p v-if="error" class="error">{{ error }}</p>
      <button class="btn btn--primario" :disabled="enviando">Cambiar clave</button>
    </form>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue"
import { api, guardarAdmin } from "../../api"
import { showToast } from "@/utils/toast"

const f = reactive({ actual: "", nueva: "", nueva2: "" })
const error = ref("")
const enviando = ref(false)

async function cambiar() {
  error.value = !f.actual ? "Digite la clave actual."
    : f.nueva.length < 6 ? "La nueva clave debe tener mínimo 6 caracteres."
    : f.nueva !== f.nueva2 ? "Las claves nuevas no coinciden." : ""
  if (error.value) return
  enviando.value = true
  try {
    const r = await api.admin.post("/clave", { actual: f.actual, nueva: f.nueva })
    guardarAdmin(r.token)
    Object.assign(f, { actual: "", nueva: "", nueva2: "" })
    showToast("Clave cambiada", "success", 1800)
  } catch (e) { error.value = e.message }
  finally { enviando.value = false }
}
</script>

<style scoped>
.cab h2 { margin: 0 0 12px; font-size: 20px; }
.panel { padding: 18px; max-width: 460px; }
.sub { color: var(--texto-suave); font-size: 14px; margin: 0 0 14px; }
.error { color: var(--rojo); font-size: 14px; }

@media (max-width: 576px) {
  .panel { padding: 14px; max-width: none; }
  .panel .btn { width: 100%; }
}
@media (max-width: 768px) {
  .panel { max-width: none; }
}
</style>
