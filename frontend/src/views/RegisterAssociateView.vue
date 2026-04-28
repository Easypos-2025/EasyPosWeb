<template>
  <div class="reg-page">
    <div class="reg-card">

      <!-- LOGO -->
      <div class="reg-brand">
        <a href="/landing">
          <span class="b-easy">Easy</span><span class="b-pos">Pos</span><span class="b-web">Web</span>
        </a>
      </div>

      <!-- ÉXITO -->
      <div v-if="success" class="reg-success">
        <div class="success-icon"><i class="bi bi-check-circle-fill"></i></div>
        <h2>¡Cuenta creada!</h2>
        <p>Tu empresa <strong>{{ successData.company }}</strong> ya está registrada.</p>
        <template v-if="successData.is_paid">
          <p class="success-sub">
            Seleccionaste el plan <strong>{{ successData.plan_name }}</strong>.
            Inicia sesión para completar el pago y activar tu cuenta.
          </p>
          <button class="btn-go-login" @click="router.push('/login')">
            <i class="bi bi-box-arrow-in-right me-2"></i>Iniciar Sesión y Pagar
          </button>
        </template>
        <template v-else>
          <p class="success-sub">Inicia sesión con <strong>{{ successData.email }}</strong></p>
          <button class="btn-go-login" @click="router.push('/login')">
            <i class="bi bi-box-arrow-in-right me-2"></i>Iniciar Sesión
          </button>
        </template>
      </div>

      <!-- FORMULARIO -->
      <template v-else>

        <!-- BARRA DE PROGRESO -->
        <div class="reg-progress">
          <template v-for="(label, idx) in stepLabels" :key="idx">
            <div class="prog-step" :class="{ active: step === idx + 1, done: step > idx + 1 }">
              <div class="prog-circle">
                <i v-if="step > idx + 1" class="bi bi-check-lg"></i>
                <span v-else>{{ idx + 1 }}</span>
              </div>
              <span class="prog-label">{{ label }}</span>
            </div>
            <div v-if="idx < stepLabels.length - 1"
                 class="prog-line" :class="{ done: step > idx + 1 }"></div>
          </template>
        </div>

        <!-- ══ PASO 1: Perfil de negocio ══ -->
        <form v-if="step === 1" class="reg-form" @submit.prevent="goStep(2)">
          <h2 class="reg-title">¿Qué tipo de negocio tienes?</h2>

          <div class="field-group" :class="{ error: err.business_profile_id }">
            <div v-if="loadingProfiles" class="loading-profiles">
              <i class="bi bi-hourglass-split"></i> Cargando perfiles...
            </div>
            <div v-else class="profile-grid">
              <button
                v-for="p in profiles"
                :key="p.id"
                type="button"
                class="profile-btn"
                :class="{ selected: form.business_profile_id === p.id }"
                :style="form.business_profile_id === p.id
                  ? { borderColor: p.color_accent, background: p.color_accent + '18' } : {}"
                @click="form.business_profile_id = p.id"
              >
                <i :class="`bi ${p.icon || 'bi-building'}`"
                   :style="{ color: p.color_accent || '#2563eb' }"></i>
                <span>{{ p.name }}</span>
              </button>
            </div>
            <span v-if="err.business_profile_id" class="field-error">{{ err.business_profile_id }}</span>
          </div>

          <button type="submit" class="btn-primary">
            Continuar <i class="bi bi-arrow-right ms-1"></i>
          </button>
          <p class="reg-login-link">¿Ya tienes cuenta? <a href="/login">Inicia sesión</a></p>
        </form>

        <!-- ══ PASO 2: Seleccionar Plan ══ -->
        <form v-else-if="step === 2" class="reg-form" @submit.prevent="goStep(3)">
          <h2 class="reg-title">Selecciona tu plan</h2>

          <!-- Selector de moneda -->
          <div class="currency-row">
            <i class="bi bi-currency-exchange"></i>
            <label>Moneda:</label>
            <select v-model="selectedCurrency" class="currency-select" @change="onCurrencyChange">
              <option v-for="code in SUPPORTED_CURRENCIES" :key="code" :value="code">
                {{ code }} — {{ CURRENCY_NAMES[code] }}
              </option>
            </select>
            <span v-if="detectedCurrency === selectedCurrency" class="currency-auto">
              <i class="bi bi-geo-alt-fill"></i> detectado automáticamente
            </span>
          </div>

          <div class="field-group" :class="{ error: err.plan_id }">
            <div v-if="loadingPlans" class="loading-profiles">
              <i class="bi bi-hourglass-split"></i> Cargando planes...
            </div>
            <div v-else class="plan-grid">
              <button
                v-for="p in plans"
                :key="p.id"
                type="button"
                class="plan-btn"
                :class="{ selected: form.plan_id === p.id, free: p.price === 0 }"
                @click="form.plan_id = p.id"
              >
                <div class="plan-badge" v-if="p.price === 0">GRATIS</div>
                <div class="plan-name">{{ p.name }}</div>
                <div class="plan-price">
                  <span v-if="p.price === 0" class="price-free">Gratis</span>
                  <span v-else class="price-paid">
                    {{ planPriceLabel(p) }}<small>/año</small>
                  </span>
                </div>
                <div class="plan-desc">{{ p.description || '' }}</div>
              </button>
            </div>
            <span v-if="err.plan_id" class="field-error">{{ err.plan_id }}</span>
          </div>

          <div class="btn-row">
            <button type="button" class="btn-back" @click="step = 1">
              <i class="bi bi-arrow-left me-1"></i> Atrás
            </button>
            <button type="submit" class="btn-primary">
              Continuar <i class="bi bi-arrow-right ms-1"></i>
            </button>
          </div>
        </form>

        <!-- ══ PASO 3: Datos de empresa ══ -->
        <form v-else-if="step === 3" class="reg-form" @submit.prevent="goStep(4)">
          <h2 class="reg-title">Datos de tu empresa</h2>

          <div class="field-group" :class="{ error: err.company_name }">
            <label>Nombre de la empresa <span class="req">*</span></label>
            <input v-model="form.company_name" type="text"
                   placeholder="Ej. Restaurante El Sabor" maxlength="150" />
            <span v-if="err.company_name" class="field-error">{{ err.company_name }}</span>
          </div>

          <div class="field-group" :class="{ error: err.identification_number }">
            <label>NIT / Identificación <span class="req">*</span></label>
            <input v-model="form.identification_number" type="text"
                   placeholder="Ej. 900123456" maxlength="50" />
            <span v-if="err.identification_number" class="field-error">{{ err.identification_number }}</span>
          </div>

          <div class="btn-row">
            <button type="button" class="btn-back" @click="step = 2">
              <i class="bi bi-arrow-left me-1"></i> Atrás
            </button>
            <button type="submit" class="btn-primary">
              Continuar <i class="bi bi-arrow-right ms-1"></i>
            </button>
          </div>
        </form>

        <!-- ══ PASO 4: Datos de cuenta ══ -->
        <form v-else-if="step === 4" class="reg-form" @submit.prevent="submitRegister">
          <h2 class="reg-title">Tu acceso de administrador</h2>

          <div class="field-group" :class="{ error: err.admin_nombre }">
            <label>Tu nombre completo <span class="req">*</span></label>
            <input v-model="form.admin_nombre" type="text"
                   placeholder="Ej. Juan Pérez" maxlength="100" />
            <span v-if="err.admin_nombre" class="field-error">{{ err.admin_nombre }}</span>
          </div>

          <div class="field-group" :class="{ error: err.admin_email }">
            <label>Correo electrónico <span class="req">*</span></label>
            <input v-model="form.admin_email" type="email" placeholder="correo@empresa.com" />
            <span v-if="err.admin_email" class="field-error">{{ err.admin_email }}</span>
          </div>

          <div class="field-group" :class="{ error: err.admin_password }">
            <label>Contraseña <span class="req">*</span></label>
            <div class="pass-wrap">
              <input v-model="form.admin_password"
                     :type="showPass ? 'text' : 'password'"
                     placeholder="Mín. 8 caracteres" />
              <button type="button" class="pass-toggle" @click="showPass = !showPass">
                <i :class="showPass ? 'bi bi-eye-slash' : 'bi bi-eye'"></i>
              </button>
            </div>
            <div class="pass-strength" v-if="form.admin_password">
              <div class="strength-bar">
                <div class="strength-fill"
                     :style="{ width: pwStrength.pct + '%', background: pwStrength.color }"></div>
              </div>
              <span class="strength-label" :style="{ color: pwStrength.color }">{{ pwStrength.label }}</span>
            </div>
            <ul class="pass-rules">
              <li :class="{ ok: /[A-Z]/.test(form.admin_password) }">
                <i class="bi" :class="/[A-Z]/.test(form.admin_password) ? 'bi-check-circle-fill' : 'bi-circle'"></i>
                Una mayúscula
              </li>
              <li :class="{ ok: /[a-z]/.test(form.admin_password) }">
                <i class="bi" :class="/[a-z]/.test(form.admin_password) ? 'bi-check-circle-fill' : 'bi-circle'"></i>
                Una minúscula
              </li>
              <li :class="{ ok: /\d/.test(form.admin_password) }">
                <i class="bi" :class="/\d/.test(form.admin_password) ? 'bi-check-circle-fill' : 'bi-circle'"></i>
                Un número
              </li>
              <li :class="{ ok: /[@$!%*?&]/.test(form.admin_password) }">
                <i class="bi" :class="/[@$!%*?&]/.test(form.admin_password) ? 'bi-check-circle-fill' : 'bi-circle'"></i>
                Un símbolo (@$!%*?&)
              </li>
              <li :class="{ ok: form.admin_password.length >= 8 }">
                <i class="bi" :class="form.admin_password.length >= 8 ? 'bi-check-circle-fill' : 'bi-circle'"></i>
                Mínimo 8 caracteres
              </li>
            </ul>
            <span v-if="err.admin_password" class="field-error">{{ err.admin_password }}</span>
          </div>

          <div class="field-group" :class="{ error: err.admin_confirm }">
            <label>Confirmar contraseña <span class="req">*</span></label>
            <div class="pass-wrap">
              <input v-model="form.admin_confirm"
                     :type="showPass2 ? 'text' : 'password'"
                     placeholder="Repite la contraseña" />
              <button type="button" class="pass-toggle" @click="showPass2 = !showPass2">
                <i :class="showPass2 ? 'bi bi-eye-slash' : 'bi bi-eye'"></i>
              </button>
            </div>
            <span v-if="err.admin_confirm" class="field-error">{{ err.admin_confirm }}</span>
          </div>

          <!-- Honeypot oculto anti-bot -->
          <input v-model="form.website" type="text" name="website"
                 autocomplete="off" tabindex="-1" aria-hidden="true"
                 style="position:absolute;left:-9999px;opacity:0;height:0;width:0;" />

          <div v-if="apiError" class="api-error">
            <i class="bi bi-exclamation-circle-fill me-2"></i>{{ apiError }}
          </div>

          <!-- Resumen del plan seleccionado -->
          <div class="plan-summary" v-if="selectedPlan">
            <i class="bi bi-gift-fill me-1" v-if="selectedPlan.price === 0"></i>
            <i class="bi bi-credit-card me-1" v-else></i>
            Plan: <strong>{{ selectedPlan.name }}</strong>
            <span v-if="selectedPlan.price === 0"> — Gratis, sin tarjeta de crédito</span>
            <span v-else>
              —
              {{ new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(selectedPlan.price) }}/año
              (pagas al activar)
            </span>
          </div>

          <div class="btn-row">
            <button type="button" class="btn-back" @click="step = 3">
              <i class="bi bi-arrow-left me-1"></i> Atrás
            </button>
            <button type="submit" class="btn-primary" :disabled="submitting">
              <span v-if="submitting">
                <i class="bi bi-hourglass-split me-1"></i>Creando cuenta...
              </span>
              <span v-else>
                <i class="bi bi-rocket-takeoff-fill me-1"></i>Terminar Registro
              </span>
            </button>
          </div>
        </form>

      </template>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from "vue"
import { useRouter } from "vue-router"
import { detectCurrency, formatMoney, CURRENCY_NAMES, SUPPORTED_CURRENCIES } from "@/utils/currency"

const API = import.meta.env.VITE_API_URL || "http://localhost:8000"

export default {
  name: "RegisterAssociateView",

  setup() {
    const router     = useRouter()
    const step       = ref(1)
    const success    = ref(false)
    const submitting = ref(false)
    const showPass   = ref(false)
    const showPass2  = ref(false)
    const apiError   = ref("")
    const profiles   = ref([])
    const plans      = ref([])
    const loadingProfiles = ref(true)
    const loadingPlans    = ref(true)
    const successData = ref({})
    const detectedCurrency = ref(detectCurrency())
    const selectedCurrency = ref(detectCurrency())

    const stepLabels = ["Perfil", "Plan", "Empresa", "Cuenta"]

    const form = reactive({
      business_profile_id: null,
      plan_id: null,
      company_name: "",
      identification_number: "",
      admin_nombre: "",
      admin_email: "",
      admin_password: "",
      admin_confirm: "",
      website: "",        // honeypot
    })

    const err = reactive({
      business_profile_id: "",
      plan_id: "",
      company_name: "",
      identification_number: "",
      admin_nombre: "",
      admin_email: "",
      admin_password: "",
      admin_confirm: "",
    })

    const selectedPlan = computed(() => plans.value.find(p => p.id === form.plan_id) || null)

    function planPrice(p) {
      return p.price_in_currency ?? p.price
    }
    function planPriceLabel(p) {
      return formatMoney(planPrice(p), selectedCurrency.value)
    }

    const pwStrength = computed(() => {
      const p = form.admin_password
      let score = 0
      if (p.length >= 8)       score++
      if (/[A-Z]/.test(p))     score++
      if (/[a-z]/.test(p))     score++
      if (/\d/.test(p))        score++
      if (/[@$!%*?&]/.test(p)) score++
      if (score <= 2) return { pct: 33,  color: "#ef4444", label: "Débil" }
      if (score <= 3) return { pct: 66,  color: "#f59e0b", label: "Media" }
      return { pct: 100, color: "#10b981", label: "Fuerte" }
    })

    function clearErr() { Object.keys(err).forEach(k => err[k] = "") }

    function goStep(target) {
      clearErr()
      apiError.value = ""
      let ok = true

      if (step.value === 1) {
        if (!form.business_profile_id) {
          err.business_profile_id = "Selecciona el tipo de negocio"
          ok = false
        }
      } else if (step.value === 2) {
        if (!form.plan_id) {
          err.plan_id = "Selecciona un plan"
          ok = false
        }
      } else if (step.value === 3) {
        if (!form.company_name.trim()) { err.company_name = "El nombre es obligatorio"; ok = false }
        if (!form.identification_number.trim()) { err.identification_number = "El NIT es obligatorio"; ok = false }
      }

      if (ok) step.value = target
    }

    async function submitRegister() {
      clearErr()
      apiError.value = ""
      let ok = true

      // Re-validar todos los pasos anteriores en caso de navegación
      if (!form.business_profile_id) { step.value = 1; err.business_profile_id = "Selecciona el tipo de negocio"; return }
      if (!form.plan_id)             { step.value = 2; err.plan_id = "Selecciona un plan"; return }
      if (!form.company_name.trim()) { step.value = 3; err.company_name = "El nombre es obligatorio"; return }
      if (!form.identification_number.trim()) { step.value = 3; err.identification_number = "El NIT es obligatorio"; return }

      if (!form.admin_nombre.trim()) { err.admin_nombre = "El nombre es obligatorio"; ok = false }
      if (!form.admin_email.trim()) {
        err.admin_email = "El correo es obligatorio"; ok = false
      } else if (!/\S+@\S+\.\S+/.test(form.admin_email)) {
        err.admin_email = "Correo inválido"; ok = false
      }
      const pwOk = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$/.test(form.admin_password)
      if (!pwOk) { err.admin_password = "La contraseña no cumple los requisitos"; ok = false }
      if (form.admin_password !== form.admin_confirm) { err.admin_confirm = "Las contraseñas no coinciden"; ok = false }
      if (!ok) return

      submitting.value = true
      try {
        const res = await fetch(`${API}/register/associate/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            company_name:          form.company_name,
            identification_number: form.identification_number,
            business_profile_id:   form.business_profile_id,
            plan_id:               form.plan_id,
            currency_code:         selectedCurrency.value,
            admin_nombre:          form.admin_nombre,
            admin_email:           form.admin_email,
            admin_password:        form.admin_password,
            website:               form.website,
          }),
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || "Error al registrar")

        successData.value = data
        sessionStorage.setItem("reg_email",    form.admin_email)
        sessionStorage.setItem("reg_password", form.admin_password)
        success.value = true
      } catch (e) {
        apiError.value = e.message
      } finally {
        submitting.value = false
      }
    }

    async function loadProfiles() {
      try {
        const res = await fetch(`${API}/landing/profiles`)
        profiles.value = await res.json()
      } catch { profiles.value = [] }
      finally { loadingProfiles.value = false }
    }

    async function loadPlans() {
      try {
        const res = await fetch(`${API}/plans/with-prices?currency=${selectedCurrency.value}`)
        plans.value = await res.json()
        const free = plans.value.find(p => p.price === 0)
        if (free && !form.plan_id) form.plan_id = free.id
      } catch { plans.value = [] }
      finally { loadingPlans.value = false }
    }

    async function onCurrencyChange() {
      loadingPlans.value = true
      await loadPlans()
    }

    onMounted(() => { loadProfiles(); loadPlans() })

    return {
      router, step, stepLabels, success, submitting, showPass, showPass2,
      apiError, profiles, plans, loadingProfiles, loadingPlans,
      successData, selectedPlan,
      detectedCurrency, selectedCurrency,
      CURRENCY_NAMES, SUPPORTED_CURRENCIES,
      form, err, pwStrength,
      planPrice, planPriceLabel, formatMoney,
      goStep, submitRegister, onCurrencyChange,
    }
  }
}
</script>

<style scoped>
.reg-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #1a3a6e 100%);
  display: flex; align-items: center; justify-content: center;
  padding: 24px;
  font-family: 'Segoe UI', system-ui, sans-serif;
}

.reg-card {
  background: #fff;
  border-radius: 20px;
  padding: 40px;
  width: 100%;
  max-width: 560px;
  box-shadow: 0 24px 60px rgba(0,0,0,.4);
}

/* LOGO */
.reg-brand { text-align: center; margin-bottom: 28px; }
.reg-brand a { text-decoration: none; font-size: 1.8rem; font-weight: 800; letter-spacing: -.5px; }
.b-easy { color: #2563eb; }
.b-pos  { color: #f97316; }   /* naranja — igual al resto de la app */
.b-web  { color: #10b981; }

/* BARRA DE PROGRESO */
.reg-progress {
  display: flex; align-items: flex-start; justify-content: center;
  margin-bottom: 28px; gap: 0;
}
.prog-step { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.prog-circle {
  width: 34px; height: 34px; border-radius: 50%;
  border: 2px solid #e2e8f0;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: .85rem; color: #94a3b8;
  transition: all .3s;
}
.prog-step.active .prog-circle { border-color: #2563eb; color: #2563eb; background: #eff6ff; }
.prog-step.done   .prog-circle { border-color: #10b981; background: #10b981; color: #fff; }
.prog-label { font-size: .7rem; color: #94a3b8; font-weight: 600; white-space: nowrap; }
.prog-step.active .prog-label { color: #2563eb; }
.prog-step.done   .prog-label { color: #10b981; }
.prog-line {
  flex: 1; height: 2px; background: #e2e8f0;
  margin: 16px 6px 0; min-width: 28px; transition: background .3s;
}
.prog-line.done { background: #10b981; }

.reg-title { font-size: 1.2rem; font-weight: 800; color: #0f172a; margin-bottom: 18px; }
.reg-form  { display: flex; flex-direction: column; gap: 16px; }

/* CAMPOS */
.field-group { display: flex; flex-direction: column; gap: 6px; }
.field-group label { font-size: .84rem; font-weight: 600; color: #334155; }
.field-group.error label { color: #ef4444; }
.req { color: #ef4444; }
.field-group input {
  border: 1.5px solid #e2e8f0; border-radius: 8px;
  padding: 10px 14px; font-size: .9rem;
  transition: border-color .2s; outline: none; color: #0f172a;
}
.field-group input:focus { border-color: #2563eb; }
.field-group.error input { border-color: #ef4444; }
.field-error { color: #ef4444; font-size: .78rem; }

/* GRID PERFILES */
.loading-profiles { color: #94a3b8; font-size: .88rem; padding: 8px 0; }
.profile-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 10px;
}
.profile-btn {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  border: 2px solid #e2e8f0; border-radius: 10px; padding: 14px 8px;
  background: #fff; cursor: pointer; transition: all .2s;
  font-size: .78rem; font-weight: 600; color: #334155; text-align: center;
  word-break: break-word; line-height: 1.3;
}
.profile-btn i { font-size: 1.5rem; }
.profile-btn:hover { border-color: #2563eb; background: #eff6ff; }
.profile-btn.selected { font-weight: 700; }

/* SELECTOR MONEDA */
.currency-row {
  display: flex; align-items: center; gap: 8px;
  background: #f8fafc; border: 1px solid #e2e8f0;
  border-radius: 8px; padding: 8px 12px; flex-wrap: wrap;
  font-size: .82rem; color: #475569;
}
.currency-row .bi-currency-exchange { color: #2563eb; font-size: 1rem; }
.currency-row label { font-weight: 600; flex-shrink: 0; }
.currency-select {
  border: 1px solid #cbd5e1; border-radius: 6px;
  padding: 4px 8px; font-size: .8rem; color: #334155;
  outline: none; background: #fff; cursor: pointer; flex: 1; min-width: 160px;
}
.currency-auto { font-size: .72rem; color: #10b981; display: flex; align-items: center; gap: 3px; }

/* GRID PLANES */
.plan-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 10px;
}
.plan-btn {
  position: relative;
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  border: 2px solid #e2e8f0; border-radius: 12px; padding: 16px 8px 12px;
  background: #fff; cursor: pointer; transition: all .2s;
  text-align: center;
}
.plan-btn:hover { border-color: #2563eb; background: #eff6ff; }
.plan-btn.selected { border-color: #2563eb; background: #eff6ff; }
.plan-btn.selected.free { border-color: #10b981; background: #f0fdf4; }
.plan-badge {
  position: absolute; top: -1px; right: -1px;
  background: #10b981; color: #fff;
  font-size: .6rem; font-weight: 800; padding: 2px 6px;
  border-radius: 0 10px 0 8px; letter-spacing: .5px;
}
.plan-name { font-weight: 800; font-size: .88rem; color: #0f172a; }
.plan-price { font-size: .82rem; }
.price-free { color: #10b981; font-weight: 800; font-size: 1rem; }
.price-paid { color: #2563eb; font-weight: 700; }
.price-paid small { font-size: .7rem; color: #64748b; }
.plan-desc { font-size: .7rem; color: #64748b; line-height: 1.3; }

/* CONTRASEÑA */
.pass-wrap { position: relative; }
.pass-wrap input {
  width: 100%; padding: 10px 42px 10px 14px;
  border: 1.5px solid #e2e8f0; border-radius: 8px;
  font-size: .9rem; outline: none; color: #0f172a; box-sizing: border-box;
}
.pass-wrap input:focus { border-color: #2563eb; }
.field-group.error .pass-wrap input { border-color: #ef4444; }
.pass-toggle {
  position: absolute; right: 12px; top: 50%; transform: translateY(-50%);
  background: none; border: none; cursor: pointer; color: #64748b; font-size: 1rem;
}
.pass-strength { margin-top: 6px; display: flex; align-items: center; gap: 10px; }
.strength-bar { flex: 1; height: 4px; background: #e2e8f0; border-radius: 2px; overflow: hidden; }
.strength-fill { height: 100%; border-radius: 2px; transition: all .3s; }
.strength-label { font-size: .75rem; font-weight: 700; white-space: nowrap; }
.pass-rules { list-style: none; padding: 0; margin: 8px 0 0; display: flex; flex-direction: column; gap: 4px; }
.pass-rules li {
  display: flex; align-items: center; gap: 6px;
  font-size: .78rem; color: #94a3b8; transition: color .2s;
}
.pass-rules li.ok { color: #10b981; }
.pass-rules li i { font-size: .85rem; }

/* RESUMEN PLAN */
.plan-summary {
  background: #f8fafc; border: 1px solid #e2e8f0;
  border-radius: 8px; padding: 10px 14px;
  font-size: .82rem; color: #475569;
}

/* BOTONES */
.btn-primary {
  background: #2563eb; color: #fff; border: none;
  padding: 13px; border-radius: 10px; font-weight: 700; font-size: .95rem;
  cursor: pointer; transition: all .2s;
  display: flex; align-items: center; justify-content: center; gap: 6px;
}
.btn-primary:hover:not(:disabled) { background: #1d4ed8; transform: translateY(-1px); }
.btn-primary:disabled { opacity: .6; cursor: not-allowed; }
.btn-row { display: flex; gap: 12px; }
.btn-back {
  border: 1.5px solid #e2e8f0; background: #fff; color: #64748b;
  padding: 13px 18px; border-radius: 10px; font-weight: 600; font-size: .9rem;
  cursor: pointer; transition: all .2s;
  display: flex; align-items: center;
}
.btn-back:hover { border-color: #94a3b8; color: #334155; }
.btn-row .btn-primary { flex: 1; }

.api-error {
  background: #fef2f2; border: 1px solid #fecaca;
  color: #dc2626; padding: 12px 14px; border-radius: 8px; font-size: .88rem;
}
.reg-login-link { text-align: center; font-size: .84rem; color: #64748b; margin: 4px 0 0; }
.reg-login-link a { color: #2563eb; font-weight: 600; text-decoration: none; }

/* ÉXITO */
.reg-success { text-align: center; padding: 20px 0; }
.success-icon { font-size: 4rem; color: #10b981; margin-bottom: 16px; }
.reg-success h2 { font-size: 1.5rem; font-weight: 800; color: #0f172a; margin-bottom: 10px; }
.reg-success p  { color: #64748b; margin-bottom: 8px; }
.success-sub { font-size: .9rem; }
.btn-go-login {
  display: inline-flex; align-items: center; justify-content: center;
  margin-top: 20px;
  background: #2563eb; color: #fff;
  padding: 13px 32px; border-radius: 10px; font-weight: 700;
  border: none; cursor: pointer; transition: all .2s;
}
.btn-go-login:hover { background: #1d4ed8; }

/* MÓVIL */
@media (max-width: 540px) {
  .reg-card { padding: 24px 16px; }
  .profile-grid { grid-template-columns: repeat(2, 1fr); }
  .plan-grid    { grid-template-columns: repeat(2, 1fr); }
  .prog-line    { min-width: 16px; }
}
</style>
