
<template>

<div class="login-container">

  <div class="login-card">

    <h2>Nueva Contraseña</h2>

    <!-- MENSAJE -->
    <div v-if="message" class="alert-success">
      {{ message }}
    </div>

    <!-- ERROR -->
    <div v-if="errorMsg" class="alert-box">
      {{ errorMsg }}
    </div>

    <form @submit.prevent="resetPassword">

      <!-- PASSWORD -->
      <div class="form-group">
        <label>Nueva contraseña</label>
        <input
          v-model="password"
          type="password"
          required
        />

        <!-- 🔐 VALIDACIÓN EN VIVO -->
        <div v-if="!success" class="password-rules">

          <small :class="passwordRules.length ? 'text-success' : 'text-danger'">
            ✔ Mínimo 8 caracteres
          </small><br>

          <small :class="passwordRules.upper ? 'text-success' : 'text-danger'">
            ✔ Una mayúscula
          </small><br>

          <small :class="passwordRules.lower ? 'text-success' : 'text-danger'">
            ✔ Una minúscula
          </small><br>

          <small :class="passwordRules.number ? 'text-success' : 'text-danger'">
            ✔ Un número
          </small><br>

          <small :class="passwordRules.special ? 'text-success' : 'text-danger'">
            ✔ Un carácter especial
          </small>

        </div>

      </div>

      <!-- CONFIRM PASSWORD -->
      <div class="form-group">
        <label>Confirmar contraseña</label>
        <input
          v-model="confirmPassword"
          type="password"
          required
        />

        <small v-if="!success" :class="matchPassword ? 'text-success' : 'text-danger'">
          {{ matchPassword ? "✔ Coinciden" : "Las contraseñas no coinciden" }}
        </small>
      </div>

      <button type="submit">
        Cambiar contraseña
      </button>

    </form>

  </div>

</div>

</template>

<script setup>

import { ref, computed } from "vue"
import { useRoute } from "vue-router"
import api from "@/services/apis"
import { useRouter } from "vue-router"

// =========================
// STATE
// =========================

const router = useRouter()

const password = ref("")
const confirmPassword = ref("")
const message = ref("")
const errorMsg = ref("")
const success = ref(false)

const route = useRoute()

// =========================
// VALIDACIÓN PASSWORD
// =========================

const passwordRules = computed(() => {
  const value = password.value || ""

  return {
    length: value.length >= 8,
    upper: /[A-Z]/.test(value),
    lower: /[a-z]/.test(value),
    number: /[0-9]/.test(value),
    special: /[!@#$%^&*(),.?":{}|<>]/.test(value)
  }
})

const isPasswordValid = computed(() =>
  Object.values(passwordRules.value).every(v => v)
)

const matchPassword = computed(() =>
  password.value && password.value === confirmPassword.value
)

// =========================
// RESET PASSWORD
// =========================

const resetPassword = async () => {

  errorMsg.value = ""
  message.value = ""

  // 🔥 VALIDACIONES FRONT
  if (!isPasswordValid.value) {
    errorMsg.value = "La contraseña no cumple los requisitos"
    return
  }

  if (!matchPassword.value) {
    errorMsg.value = "Las contraseñas no coinciden"
    return
  }

  try {

    //const token = route.query.token
    const token = route.query.token || ""
    //console.log("TOKEN2:", token)
    await api.post("/auth/reset-password/", {
      token,
      new_password: password.value
    })

    message.value = "Contraseña actualizada correctamente"
    success.value = true

    password.value = ""
    confirmPassword.value = ""

    setTimeout(() => {
      router.push("/login")
    }, 2000)

  } catch (error) {

    errorMsg.value =
      error.response?.data?.detail || "Error al cambiar contraseña"

  }
}

</script>


<style scoped>
/* =================================================
LAYOUT (IGUAL LOGIN)
================================================= */

.login-container input {
  color: #000 !important;
  background-color: #ffffff !important;
}

.login-container input::placeholder {
  color: #666 !important;
}

.login-container{
  min-height:100vh;
  display:flex;
  align-items:center;
  justify-content:center;
  background:#0f172a;
  padding:20px;
}

/* =================================================
CARD
================================================= */

.login-card{
  width:100%;
  max-width:400px;
  padding:30px;
  background:#1e293b;
  border-radius:10px;
  box-shadow:0 10px 25px rgba(0,0,0,0.3);
  color:#fff;
}

/* =================================================
FORM
================================================= */

.form-group{
  margin-bottom:15px;
  display:flex;
  flex-direction:column;
}

.form-group label{
  margin-bottom:5px;
  font-size:14px;
}

input{
  padding:12px;
  border:1px solid #334155;
  border-radius:6px;
  font-size:15px;
}

button{
  width:100%;
  padding:12px;
  background:#2563eb;
  color:#fff;
  border:none;
  border-radius:6px;
  cursor:pointer;
}

button:hover{
  background:#1d4ed8;
}

/* =================================================
ALERTAS
================================================= */

.alert-box{
  background:#dc2626;
  padding:10px;
  margin-bottom:10px;
  border-radius:6px;
}

.alert-success{
  background:#16a34a;
  padding:10px;
  margin-bottom:10px;
  border-radius:6px;
}

</style>