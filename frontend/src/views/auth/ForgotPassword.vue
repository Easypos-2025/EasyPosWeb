<template>

<div class="login-container">

  <div class="login-card">

    <h2>Recuperar Contraseña</h2>

    <!-- MENSAJE -->
    <div v-if="message" class="alert-success">
      {{ message }}
    </div>

    <!-- ERROR -->
    <div v-if="errorMsg" class="alert-box">
      {{ errorMsg }}
    </div>

    <!-- FORM -->
    <form @submit.prevent="sendRecovery">

      <div class="form-group">
        <label>Email</label>
        <input
          v-model="email"
          type="email"
          placeholder="Ingrese su email"
          required
        />
      </div>

      <button 
        :disabled="loading"
        @click="sendRecovery"
      >
        {{ loading ? "Enviando..." : "Enviar enlace de recuperación" }}
      </button>

    </form>

    <!-- VOLVER -->
    <div class="forgot-password">
      <span @click="goToLogin">
        ← Volver al login
      </span>
    </div>

  </div>

</div>

</template>

<script setup>

import { ref } from "vue"
import { useRouter } from "vue-router"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"


const email = ref("")
const message = ref("")
const errorMsg = ref("")
const loading = ref(false)
const router = useRouter()

const goToLogin = () => {
  router.push("/")
}

const sendRecovery = async () => {

  if (loading.value) return

  loading.value = true

  try {

    await api.post("/auth/forgot-password/", {
      email: email.value
    })

    // 🔥 SIEMPRE RESPUESTA GENÉRICA (SEGURIDAD)
    showToast(
      "Si el correo existe, recibirás un enlace de recuperación",
      "success"
    )

    // 🔥 REDIRIGIR A LOGIN
    setTimeout(() => {
      router.push("/login")
    }, 1500)

  } catch (error) {

    showToast(
      "Error enviando correo. Verifica conexión o contacta soporte",
      "error"
    )

  } finally {
    loading.value = false
  }
}




</script>

<style scoped>

/* reutiliza mismos estilos del login */

.login-container{
  min-height:100vh;
  display:flex;
  align-items:center;
  justify-content:center;
  background:#0f172a;
  padding:20px;
}

.login-card{
  width:100%;
  max-width:400px;
  padding:30px;
  background:#1e293b;
  border-radius:10px;
  color:#fff;
}

.form-group{
  margin-bottom:15px;
  display:flex;
  flex-direction:column;
}

input{
  padding:12px;
  border-radius:6px;
}

button{
  width:100%;
  padding:12px;
  background:#2563eb;
  color:#fff;
  border:none;
  border-radius:6px;
}

.alert-box{
  background:#dc2626;
  padding:10px;
  margin-bottom:10px;
}

.alert-success{
  background:#16a34a;
  padding:10px;
  margin-bottom:10px;
}

.forgot-password{
  margin-top:10px;
  text-align:center;
  cursor:pointer;
}

</style>