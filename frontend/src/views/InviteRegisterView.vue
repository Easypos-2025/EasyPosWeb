<template>
  <div class="invite-page">
    <div class="invite-card">

      <!-- Logo / Brand -->
      <div class="invite-brand">
        <i class="bi bi-box-seam-fill"></i>
        <span>EasyPosWeb</span>
      </div>

      <!-- Cargando token -->
      <div v-if="loading" class="invite-loading">
        <div class="spinner"></div>
        <p>Verificando invitación...</p>
      </div>

      <!-- Token inválido / expirado -->
      <div v-else-if="tokenError" class="invite-error">
        <i class="bi bi-x-circle-fill"></i>
        <h2>Invitación no válida</h2>
        <p>{{ tokenError }}</p>
        <a href="/login" class="btn-go-login">Ir al login</a>
      </div>

      <!-- Registro exitoso -->
      <div v-else-if="registered" class="invite-success">
        <i class="bi bi-check-circle-fill"></i>
        <h2>¡Cuenta creada!</h2>
        <p>Tu cuenta fue registrada en <strong>{{ info.company_name }}</strong> con el rol <strong>{{ info.role_name }}</strong>.</p>
        <a href="/login" class="btn-go-login">Iniciar sesión</a>
      </div>

      <!-- Formulario de registro -->
      <template v-else-if="info">
        <div class="invite-header">
          <h2>Te invitaron a unirte</h2>
          <div class="invite-meta">
            <span class="invite-company"><i class="bi bi-building"></i> {{ info.company_name }}</span>
            <span class="invite-role"><i class="bi bi-shield-check"></i> {{ info.role_name }}</span>
          </div>
          <p class="invite-exp">Invitación válida hasta {{ fmtDate(info.expires_at) }}</p>
        </div>

        <form class="invite-form" @submit.prevent="register">

          <div class="field-group" :class="{ error: errors.nombre }">
            <label>Nombre completo <span class="req">*</span></label>
            <input v-model="form.nombre" type="text" placeholder="Tu nombre" maxlength="100" />
            <span v-if="errors.nombre" class="field-error">{{ errors.nombre }}</span>
          </div>

          <div class="field-group" :class="{ error: errors.email }">
            <label>Correo electrónico <span class="req">*</span></label>
            <input v-model="form.email" type="email" placeholder="correo@ejemplo.com" />
            <span v-if="errors.email" class="field-error">{{ errors.email }}</span>
          </div>

          <div class="field-group" :class="{ error: errors.password }">
            <label>Contraseña <span class="req">*</span></label>
            <div class="pass-wrap">
              <input
                v-model="form.password"
                :type="showPass ? 'text' : 'password'"
                placeholder="Mínimo 8 caracteres"
              />
              <button type="button" class="btn-eye" @click="showPass = !showPass">
                <i :class="showPass ? 'bi bi-eye-slash' : 'bi bi-eye'"></i>
              </button>
            </div>
            <span v-if="errors.password" class="field-error">{{ errors.password }}</span>
          </div>

          <div class="field-group" :class="{ error: errors.confirm }">
            <label>Confirmar contraseña <span class="req">*</span></label>
            <div class="pass-wrap">
              <input
                v-model="form.confirm"
                :type="showConfirm ? 'text' : 'password'"
                placeholder="Repite tu contraseña"
              />
              <button type="button" class="btn-eye" @click="showConfirm = !showConfirm">
                <i :class="showConfirm ? 'bi bi-eye-slash' : 'bi bi-eye'"></i>
              </button>
            </div>
            <span v-if="errors.confirm" class="field-error">{{ errors.confirm }}</span>
          </div>

          <div v-if="apiError" class="api-error">
            <i class="bi bi-exclamation-triangle"></i> {{ apiError }}
          </div>

          <button type="submit" class="btn-register" :disabled="saving">
            <i v-if="saving" class="bi bi-hourglass-split spin"></i>
            <i v-else class="bi bi-person-plus-fill"></i>
            {{ saving ? 'Creando cuenta...' : 'Crear mi cuenta' }}
          </button>

        </form>

        <p class="invite-login-link">¿Ya tienes cuenta? <a href="/login">Inicia sesión</a></p>
      </template>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { useRoute } from "vue-router"
import api from "@/services/apis"

const route = useRoute()
const token = route.params.token

const loading     = ref(true)
const tokenError  = ref("")
const registered  = ref(false)
const saving      = ref(false)
const apiError    = ref("")
const showPass    = ref(false)
const showConfirm = ref(false)
const info        = ref(null)

const form   = ref({ nombre: "", email: "", password: "", confirm: "" })
const errors = ref({ nombre: "", email: "", password: "", confirm: "" })

onMounted(async () => {
  try {
    const res = await api.get(`/invitations/${token}`)
    info.value = res.data
  } catch (e) {
    tokenError.value = e.response?.data?.detail || "Invitación no válida o expirada"
  } finally {
    loading.value = false
  }
})

function validate() {
  errors.value = { nombre: "", email: "", password: "", confirm: "" }
  let ok = true
  if (!form.value.nombre.trim()) {
    errors.value.nombre = "El nombre es obligatorio"; ok = false
  }
  if (!form.value.email.trim() || !form.value.email.includes("@")) {
    errors.value.email = "Email inválido"; ok = false
  }
  if (form.value.password.length < 8) {
    errors.value.password = "Mínimo 8 caracteres"; ok = false
  }
  if (form.value.password !== form.value.confirm) {
    errors.value.confirm = "Las contraseñas no coinciden"; ok = false
  }
  return ok
}

async function register() {
  if (!validate()) return
  saving.value  = true
  apiError.value = ""
  try {
    await api.post(`/invitations/${token}/register`, {
      nombre:   form.value.nombre.trim(),
      email:    form.value.email.trim().toLowerCase(),
      password: form.value.password,
    })
    registered.value = true
  } catch (e) {
    apiError.value = e.response?.data?.detail || "Error al crear la cuenta"
  } finally {
    saving.value = false
  }
}

function fmtDate(iso) {
  if (!iso) return ""
  return new Date(iso).toLocaleDateString("es-CO", {
    day: "2-digit", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit"
  })
}
</script>

<style scoped>
.invite-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.invite-card {
  background: #fff;
  border-radius: 20px;
  width: 100%;
  max-width: 460px;
  padding: 40px 36px;
  box-shadow: 0 30px 80px rgba(0,0,0,0.4);
}

.invite-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 28px;
  font-size: 22px;
  font-weight: 800;
  color: #1e293b;
}
.invite-brand .bi { font-size: 28px; color: #3b82f6; }

/* Loading */
.invite-loading {
  display: flex; flex-direction: column; align-items: center;
  gap: 16px; padding: 32px 0; color: #64748b;
}
.spinner {
  width: 32px; height: 32px;
  border: 3px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Error */
.invite-error {
  text-align: center; color: #ef4444;
  display: flex; flex-direction: column; align-items: center; gap: 10px;
}
.invite-error .bi { font-size: 48px; }
.invite-error h2  { font-size: 20px; font-weight: 700; color: #1e293b; margin: 0; }
.invite-error p   { font-size: 14px; color: #64748b; margin: 0; }

/* Success */
.invite-success {
  text-align: center; color: #16a34a;
  display: flex; flex-direction: column; align-items: center; gap: 10px;
}
.invite-success .bi { font-size: 48px; }
.invite-success h2  { font-size: 20px; font-weight: 700; color: #1e293b; margin: 0; }
.invite-success p   { font-size: 14px; color: #64748b; margin: 0; }

/* Header info */
.invite-header { margin-bottom: 24px; }
.invite-header h2 {
  font-size: 22px; font-weight: 700; color: #1e293b; margin: 0 0 12px;
}
.invite-meta {
  display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 8px;
}
.invite-company,
.invite-role {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 600;
}
.invite-company { background: rgba(59,130,246,0.1); color: #2563eb; }
.invite-role    { background: rgba(34,197,94,0.1);  color: #16a34a; }
.invite-exp     { font-size: 11px; color: #94a3b8; margin: 0; }

/* Form */
.invite-form { display: flex; flex-direction: column; gap: 16px; }

.field-group { display: flex; flex-direction: column; gap: 5px; }
.field-group label {
  font-size: 13px; font-weight: 600; color: #374151;
}
.req { color: #ef4444; }

.field-group input {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 14px;
  color: #1e293b;
  outline: none;
  transition: border-color 0.15s;
  width: 100%;
  box-sizing: border-box;
}
.field-group input:focus { border-color: #3b82f6; }
.field-group.error input { border-color: #ef4444; }

.field-error { font-size: 11px; color: #ef4444; }

.pass-wrap { position: relative; }
.pass-wrap input { padding-right: 42px; }
.btn-eye {
  position: absolute; right: 10px; top: 50%; transform: translateY(-50%);
  background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 15px;
}
.btn-eye:hover { color: #1e293b; }

.api-error {
  padding: 10px 14px;
  background: rgba(239,68,68,0.08);
  border: 1px solid rgba(239,68,68,0.2);
  border-radius: 8px;
  font-size: 13px;
  color: #ef4444;
  display: flex; align-items: center; gap: 8px;
}

.btn-register {
  padding: 12px;
  background: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 8px;
  transition: background 0.15s;
  margin-top: 4px;
}
.btn-register:hover:not(:disabled) { background: #2563eb; }
.btn-register:disabled { opacity: 0.65; cursor: not-allowed; }

.btn-go-login {
  display: inline-flex; align-items: center;
  margin-top: 8px;
  padding: 10px 24px;
  background: #3b82f6; color: #fff;
  border-radius: 8px; font-weight: 600; font-size: 14px;
  text-decoration: none; transition: background 0.15s;
}
.btn-go-login:hover { background: #2563eb; }

.invite-login-link {
  text-align: center; font-size: 13px; color: #64748b; margin: 16px 0 0;
}
.invite-login-link a { color: #3b82f6; font-weight: 600; text-decoration: none; }
.invite-login-link a:hover { text-decoration: underline; }

.spin { animation: spin 0.8s linear infinite; display: inline-block; }
</style>
