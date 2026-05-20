<template>
  <div class="ve-page">
    <div class="ve-card">
      <img src="/src/assets/logo.png" class="ve-logo" alt="EasyPosWeb"
           @error="e => e.target.style.display='none'" />

      <!-- Cargando -->
      <div v-if="state === 'loading'" class="ve-body">
        <div class="spinner-border ve-spinner" role="status"></div>
        <p class="ve-msg">Verificando tu cuenta…</p>
      </div>

      <!-- Éxito -->
      <div v-else-if="state === 'ok'" class="ve-body">
        <div class="ve-icon ok"><i class="bi bi-check-circle-fill"></i></div>
        <h2 class="ve-title">¡Cuenta activada!</h2>
        <p class="ve-msg">Tu correo ha sido verificado. Ya puedes iniciar sesión.</p>
        <p v-if="email" class="ve-email">{{ email }}</p>
        <button class="ve-btn" @click="goLogin">
          <i class="bi bi-box-arrow-in-right me-2"></i>Iniciar sesión
        </button>
      </div>

      <!-- Error -->
      <div v-else class="ve-body">
        <div class="ve-icon error"><i class="bi bi-x-circle-fill"></i></div>
        <h2 class="ve-title">Enlace inválido</h2>
        <p class="ve-msg">{{ errorMsg }}</p>
        <button class="ve-btn ve-btn-outline" @click="goRegister">
          <i class="bi bi-person-plus me-2"></i>Registrarse de nuevo
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"

const route  = useRoute()
const router = useRouter()
const state    = ref("loading")
const email    = ref("")
const errorMsg = ref("El enlace de verificación es inválido o ha expirado.")

const API = import.meta.env.VITE_API_URL || ""

onMounted(async () => {
  const token = route.query.token
  if (!token) { state.value = "error"; return }
  try {
    const res = await fetch(`${API}/register/verify-email?token=${encodeURIComponent(token)}`)
    const data = await res.json()
    if (res.ok) {
      email.value = data.email || ""
      state.value = "ok"
    } else {
      errorMsg.value = data.detail || errorMsg.value
      state.value = "error"
    }
  } catch {
    state.value = "error"
  }
})

function goLogin()    { router.push("/login") }
function goRegister() { router.push("/register") }
</script>

<style scoped>
.ve-page {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  padding: 24px;
}
.ve-card {
  background: #fff; border-radius: 16px; padding: 40px 36px;
  max-width: 420px; width: 100%; text-align: center;
  box-shadow: 0 20px 60px rgba(0,0,0,.25);
}
.ve-logo { height: 42px; margin-bottom: 28px; }
.ve-spinner { color: #2563eb; width: 40px; height: 40px; margin-bottom: 16px; }
.ve-icon { font-size: 56px; margin-bottom: 12px; }
.ve-icon.ok    { color: #10b981; }
.ve-icon.error { color: #ef4444; }
.ve-title { font-size: 20px; font-weight: 800; color: #0f172a; margin-bottom: 8px; }
.ve-msg   { font-size: 14px; color: #64748b; margin-bottom: 6px; }
.ve-email { font-size: 13px; font-weight: 700; color: #2563eb; margin-bottom: 20px; }
.ve-body  { display: flex; flex-direction: column; align-items: center; }
.ve-btn {
  display: inline-flex; align-items: center; margin-top: 16px;
  background: #2563eb; color: #fff; border: none;
  border-radius: 8px; padding: 11px 24px; font-size: 14px;
  font-weight: 700; cursor: pointer; transition: background .15s;
}
.ve-btn:hover { background: #1d4ed8; }
.ve-btn-outline {
  background: transparent; border: 2px solid #2563eb; color: #2563eb;
}
.ve-btn-outline:hover { background: #eff6ff; }
</style>
