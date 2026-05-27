<template>

<div class="login-container">

  <div class="login-card">

    <!-- ── SELECTOR DE EMPRESA (cuentas de prueba) ── -->
    <div v-if="companyList.length">
      <div class="company-select-header">
        <button class="btn-back" @click="backToLogin">
          <span>←</span> Volver
        </button>
        <h2>Selecciona una empresa</h2>
        <p class="company-select-sub">Cuenta de prueba · elige con cuál empresa ingresar</p>
      </div>

      <div class="company-list">
        <button
          v-for="c in companyList"
          :key="c.company_id"
          class="company-option"
          :disabled="loadingCompany === c.company_id"
          @click="loginWithCompany(c.company_id)"
        >
          <span class="company-icon">🏢</span>
          <span class="company-name">{{ c.company_name }}</span>
          <span v-if="loadingCompany === c.company_id" class="company-loading">...</span>
          <span v-else class="company-arrow">→</span>
        </button>
      </div>
    </div>

    <!-- ── FORMULARIO NORMAL ── -->
    <template v-else>

      <h2>Iniciar Sesión</h2>

      <!-- ERROR -->
      <div v-if="errorMsg" class="alert-box">
        <div class="alert-icon">❌</div>
        <div class="alert-text">{{ errorMsg }}</div>
      </div>

      <!-- FORM -->
      <form @submit.prevent="login">

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
            <span class="toggle-password" @click="togglePassword">
              {{ showPassword ? "🙈" : "👁" }}
            </span>
          </div>
        </div>

        <button type="submit" :disabled="loading">
          {{ loading ? "Ingresando..." : "Ingresar" }}
        </button>

        <div class="forgot-password">
          <span @click="goToForgotPassword">¿Olvidaste tu contraseña?</span>
        </div>

      </form>

    </template>

  </div>

</div>

</template>

<script setup>

import { ref, onMounted } from "vue"
import { useRouter } from "vue-router"
import api from "../services/apis"

const email        = ref(localStorage.getItem("lastUser") || "")
const password     = ref("")
const errorMsg     = ref("")
const showPassword = ref(false)
const loading      = ref(false)
const companyList  = ref([])   // empresas para selección (cuentas de prueba)
const loadingCompany = ref(null)

const router = useRouter()

onMounted(() => {
  const regEmail = sessionStorage.getItem("reg_email")
  const regPass  = sessionStorage.getItem("reg_password")
  if (regEmail) {
    email.value    = regEmail
    password.value = regPass || ""
    sessionStorage.removeItem("reg_email")
    sessionStorage.removeItem("reg_password")
  }
})

const togglePassword = () => { showPassword.value = !showPassword.value }
const goToForgotPassword = () => { router.push("/forgot-password") }
const backToLogin = () => { companyList.value = []; errorMsg.value = "" }

async function _completeLogin(token) {
  localStorage.setItem("token", token)
  localStorage.setItem("lastUser", email.value)
  const userResponse = await api.get("/auth/me/", {
    headers: { Authorization: `Bearer ${token}` }
  })
  localStorage.setItem("user", JSON.stringify(userResponse.data))
  router.push("/dashboard")
}

const login = async () => {
  errorMsg.value = ""
  loading.value  = true
  try {
    const response = await api.post("/auth/login/", {
      email:    email.value,
      password: password.value,
    })

    // Cuenta de prueba con múltiples empresas
    if (response.data.requires_company_selection) {
      companyList.value = response.data.companies
      return
    }

    await _completeLogin(response.data.access_token)
  } catch (error) {
    errorMsg.value = error.response?.data?.detail || "No se pudo conectar con el servidor"
    setTimeout(() => { errorMsg.value = "" }, 3500)
  } finally {
    loading.value = false
  }
}

const loginWithCompany = async (companyId) => {
  errorMsg.value     = ""
  loadingCompany.value = companyId
  try {
    const response = await api.post("/auth/login/", {
      email:      email.value,
      password:   password.value,
      company_id: companyId,
    })
    await _completeLogin(response.data.access_token)
  } catch (error) {
    errorMsg.value = error.response?.data?.detail || "Error al ingresar a la empresa"
    setTimeout(() => { errorMsg.value = "" }, 3500)
  } finally {
    loadingCompany.value = null
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

/* =================================================
SELECTOR DE EMPRESA
================================================= */

.company-select-header {
  margin-bottom: 20px;
}

.btn-back {
  background: none;
  border: none;
  color: #60a5fa;
  font-size: 13px;
  cursor: pointer;
  padding: 0;
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 5px;
  width: auto;
}

.btn-back:hover { color: #93c5fd; background: none; }

.company-select-header h2 {
  margin: 0 0 4px;
  font-size: 20px;
  text-align: left;
}

.company-select-sub {
  font-size: 12px;
  color: #94a3b8;
  margin: 0;
}

.company-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.company-option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  text-align: left;
  transition: border-color 0.15s, background 0.15s;
  width: 100%;
}

.company-option:hover:not(:disabled) {
  border-color: #2563eb;
  background: #1e3a5f;
}

.company-option:disabled {
  opacity: 0.6;
  cursor: default;
}

.company-icon { font-size: 20px; flex-shrink: 0; }

.company-name {
  flex: 1;
  font-weight: 500;
}

.company-arrow {
  color: #60a5fa;
  font-size: 16px;
}

.company-loading {
  color: #94a3b8;
  font-size: 13px;
  letter-spacing: 2px;
}

/* Spinner en botón submit */
button:disabled {
  opacity: 0.7;
  cursor: default;
}

</style>