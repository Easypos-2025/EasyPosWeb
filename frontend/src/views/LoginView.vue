<template>

<div class="login-container">

  <div class="login-card">

    <h2>Iniciar Sesión</h2>

    <!-- ERROR -->

    <div v-if="errorMsg" class="alert-box">

      <div class="alert-icon">
        ❌
      </div>

      <div class="alert-text">
        {{ errorMsg }}
      </div>

    </div>

    <!-- FORM -->

    <form @submit.prevent="login">

      <!-- EMAIL -->

      <div class="form-group">

        <label for="email">Usuario / Email</label>

        <input
          id="email"
          v-model="email"
          type="text"
          placeholder="Ingrese su usuario o email"
          required
        />

      </div>

      <!-- PASSWORD -->

      <div class="form-group">

        <label for="password">Contraseña</label>

        <div class="password-container">

          <input
            id="password"
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            placeholder="Ingrese su contraseña"
            required
          />

          <span
            class="toggle-password"
            @click="togglePassword"
          >
            {{ showPassword ? "🙈" : "👁" }}
          </span>

        </div>

      </div>

      <!-- BUTTON -->

      <button type="submit">

        Ingresar

      </button>
      <!-- RECUPERAR CONTRASEÑA -->
      <div class="forgot-password">
        <span @click="goToForgotPassword">
          ¿Olvidaste tu contraseña?
        </span>
      </div>

    </form>

  </div>

</div>

</template>

<script setup>

/* =================================================
IMPORTS
================================================= */

import { ref } from "vue"
import { useRouter } from "vue-router"
import api from "../services/apis"

/* =================================================
VARIABLES
================================================= */

const email = ref(localStorage.getItem("lastUser") || "")
const password = ref("")
const errorMsg = ref("")
const showPassword = ref(false)

const router = useRouter()

/* =================================================
TOGGLE PASSWORD
================================================= */

const togglePassword = () => {
  showPassword.value = !showPassword.value
}

/* =================================================
LOGIN
================================================= */
const goToForgotPassword = () => {
  router.push("/forgot-password")
}

const login = async () => {

  errorMsg.value = ""

  try{

    const response = await api.post("/auth/login/",{
      email: email.value,
      password: password.value
    })
    
    const token = response.data.access_token

    localStorage.setItem("token", token)
    localStorage.setItem("lastUser", email.value)

    // ✅ FIX CORRECTO (con header)
    const userResponse = await api.get("/auth/me/", {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })

    localStorage.setItem(
      "user",
      JSON.stringify(userResponse.data)
    )

    router.push("/dashboard")

  }

  catch(error){

    console.error("ERROR LOGIN:", error)

    if(error.response){
      errorMsg.value = error.response.data.detail || "Error de autenticación"
    }
    else{
      errorMsg.value = "No se pudo conectar con el servidor"
    }

    setTimeout(()=>{
      errorMsg.value = ""
    },3000)

  }

}

</script>

<style scoped>

/* =================================================
LAYOUT
================================================= */
/* 🔥 FORZAR ESTILO SOLO EN LOGIN */

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
  background:#0f172a; /* oscuro elegante */
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
TITLE
================================================= */

.login-card h2{
  margin-bottom:20px;
  text-align:center;
}

/* =================================================
ERROR
================================================= */

.alert-box{
  display:flex;
  align-items:center;
  gap:10px;
  background:#dc2626;
  color:#fff;
  padding:12px;
  border-radius:6px;
  margin-bottom:15px;
  font-weight:500;
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

/* =================================================
INPUTS
================================================= */

input{
  padding:12px;
  border:1px solid #334155;
  border-radius:6px;
  font-size:15px;
  background:#fff;
  color:#000;
}

input::placeholder{
  color:#777;
}

/* =================================================
PASSWORD
================================================= */

.password-container{
  position:relative;
  display:flex;
  align-items:center;
}

.password-container input{
  width:100%;
}

.toggle-password{
  position:absolute;
  right:10px;
  cursor:pointer;
  font-size:18px;
}

/* =================================================
BUTTON
================================================= */

button{
  width:100%;
  padding:12px;
  background:#2563eb;
  color:#fff;
  border:none;
  border-radius:6px;
  cursor:pointer;
  font-weight:500;
}

button:hover{
  background:#1d4ed8;
}

/* =================================================
RESPONSIVE
================================================= */

@media (max-width: 480px){
  .login-card{
    padding:20px;
  }
}

/* =================================================
FORGOT PASSWORD
================================================= */

.forgot-password {
  margin-top: 12px;
  text-align: center;
}

.forgot-password span {
  color: #60a5fa;
  cursor: pointer;
  font-size: 14px;
}

.forgot-password span:hover {
  text-decoration: underline;
}


</style>