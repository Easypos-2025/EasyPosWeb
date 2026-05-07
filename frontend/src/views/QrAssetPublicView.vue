<template>
  <div class="pub-page">

    <!-- LOADING -->
    <div v-if="loading" class="pub-state">
      <div class="pub-spinner"></div>
      <p>Cargando información...</p>
    </div>

    <!-- ERROR -->
    <div v-else-if="error" class="pub-state pub-error">
      <i class="bi bi-exclamation-circle-fill" style="font-size:48px;color:#ef4444"></i>
      <h3>Activo no disponible</h3>
      <p>{{ error }}</p>
    </div>

    <!-- CONFIRMACIÓN DE EMAIL -->
    <div v-else-if="confirming" class="pub-state">
      <div v-if="confirmLoading" class="pub-spinner"></div>
      <template v-else-if="confirmResult === 'confirmed' || confirmResult === 'already_confirmed'">
        <i class="bi bi-check-circle-fill" style="font-size:48px;color:#10b981"></i>
        <h3>¡Solicitud confirmada!</h3>
        <p>Gracias <strong>{{ confirmName }}</strong>. Nos pondremos en contacto contigo pronto.</p>
      </template>
      <template v-else>
        <i class="bi bi-x-circle-fill" style="font-size:48px;color:#ef4444"></i>
        <h3>Enlace no válido</h3>
        <p>Este enlace ya fue usado o no es válido.</p>
      </template>
    </div>

    <!-- FICHA PÚBLICA DEL ACTIVO -->
    <template v-else-if="asset">

      <!-- HEADER -->
      <div class="pub-header">
        <div class="pub-brand">
          <span class="brand-txt">
            <span class="b-blue">Easy</span><span class="b-amber">Pos</span><span class="b-green">Web</span>
          </span>
        </div>
        <span v-if="asset.list_code" class="pub-code"># {{ asset.list_code }}</span>
      </div>

      <!-- CARRUSEL DE FOTOS -->
      <div v-if="asset.media && asset.media.length > 0" class="pub-carousel">
        <div class="carousel-track" :style="{ transform: `translateX(-${slide * 100}%)` }">
          <template v-for="(m, i) in asset.media" :key="i">
            <div class="carousel-slide">
              <img v-if="m.file_type === 'image'" :src="m.file_url" class="carousel-img" />
              <video v-else :src="m.file_url" class="carousel-img" controls />
            </div>
          </template>
        </div>
        <button v-if="slide > 0"                        class="car-btn car-prev" @click="slide--"><i class="bi bi-chevron-left"></i></button>
        <button v-if="slide < asset.media.length - 1"   class="car-btn car-next" @click="slide++"><i class="bi bi-chevron-right"></i></button>
        <div class="car-dots">
          <span v-for="(_, i) in asset.media" :key="i" :class="['car-dot', i === slide && 'active']" @click="slide = i"></span>
        </div>
      </div>
      <div v-else class="pub-no-photo">
        <i class="bi bi-house-door" style="font-size:48px;color:#cbd5e1"></i>
      </div>

      <!-- INFO PRINCIPAL -->
      <div class="pub-card">
        <div class="pub-cat">{{ asset.category_name }}</div>
        <h1 class="pub-title">{{ asset.name }}</h1>
        <p v-if="asset.short_name" class="pub-subtitle">{{ asset.short_name }}</p>

        <div v-if="asset.address || asset.location" class="pub-detail-row">
          <i class="bi bi-geo-alt-fill"></i>
          <span>{{ asset.address || asset.location }}</span>
        </div>

        <!-- VALORES -->
        <div class="pub-values">
          <div v-if="asset.canon_value != null" class="pub-value-card">
            <span class="pvc-label">Valor Canon</span>
            <span class="pvc-amount">{{ fmt(asset.canon_value) }}</span>
            <span class="pvc-period">/ mes</span>
          </div>
          <div v-if="asset.has_sale_option" class="pub-value-card pub-sale">
            <i class="bi bi-tag-fill"></i>
            <span class="pvc-label">Opción de Venta</span>
            <span class="pvc-consult">Consultar precio</span>
          </div>
        </div>

        <!-- ESTADO -->
        <div class="pub-badges">
          <span v-if="asset.is_rented" class="pub-badge pub-badge-rented">
            <i class="bi bi-person-fill"></i> Ocupado
          </span>
          <span v-else class="pub-badge pub-badge-available">
            <i class="bi bi-check-circle-fill"></i> Disponible
          </span>
        </div>

        <!-- DESCRIPCIÓN -->
        <p v-if="asset.description" class="pub-desc">{{ asset.description }}</p>
      </div>

      <!-- FORMULARIO DE CONTACTO -->
      <div class="pub-card pub-form-card">
        <h2 class="pub-form-title">
          <i class="bi bi-chat-dots-fill"></i>
          ¿Te interesa este activo?
        </h2>

        <!-- ÉXITO -->
        <div v-if="formSent" class="pub-form-success">
          <i class="bi bi-envelope-check-fill" style="font-size:36px;color:#10b981"></i>
          <h3>¡Solicitud enviada!</h3>
          <p>
            Te enviamos un correo a <strong>{{ sentEmail }}</strong>.
            Por favor confírmalo para completar tu solicitud.
          </p>
        </div>

        <template v-else>
          <!-- Honeypot: campo invisible que los bots llenan -->
          <div style="position:absolute;left:-9999px;top:-9999px;opacity:0;pointer-events:none" aria-hidden="true">
            <input v-model="form.hp_field" tabindex="-1" autocomplete="off" />
          </div>

          <div class="pf-group">
            <label>Nombre completo *</label>
            <input v-model.trim="form.name" class="pf-input" placeholder="Tu nombre" maxlength="100" />
          </div>
          <div class="pf-group">
            <label>Teléfono *</label>
            <input v-model.trim="form.phone" class="pf-input" type="tel" placeholder="300 000 0000" maxlength="20" />
          </div>
          <div class="pf-group">
            <label>Correo electrónico *</label>
            <input v-model.trim="form.email" class="pf-input" type="email" placeholder="tu@correo.com" maxlength="150" />
          </div>
          <div class="pf-group">
            <label>Me interesa para</label>
            <div class="pf-interest-row">
              <button
                v-for="opt in interests" :key="opt.value"
                type="button"
                :class="['pf-interest-btn', form.interest === opt.value && 'active']"
                @click="form.interest = opt.value"
              >
                <i :class="'bi ' + opt.icon"></i> {{ opt.label }}
              </button>
            </div>
          </div>
          <div class="pf-group">
            <label>Mensaje (opcional)</label>
            <textarea v-model.trim="form.message" class="pf-input" rows="3" placeholder="¿Tienes alguna pregunta específica?" maxlength="2000"></textarea>
          </div>

          <p v-if="formError" class="pf-error"><i class="bi bi-exclamation-triangle-fill"></i> {{ formError }}</p>

          <button class="pf-submit" @click="submitForm" :disabled="submitting">
            <span v-if="submitting"><i class="bi bi-arrow-repeat spin"></i> Enviando...</span>
            <span v-else><i class="bi bi-send-fill"></i> Enviar solicitud</span>
          </button>
          <p class="pf-privacy">
            <i class="bi bi-shield-lock-fill"></i>
            Tu información es privada y solo se usará para contactarte sobre este activo.
          </p>
        </template>
      </div>

      <!-- FOOTER -->
      <div class="pub-footer">
        <span class="brand-txt sm">
          <span class="b-blue">Easy</span><span class="b-amber">Pos</span><span class="b-green">Web</span>
        </span>
        <span>Gestión de activos e inmuebles</span>
      </div>

    </template>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue"
import { useRoute } from "vue-router"
import axios from "axios"

const route = useRoute()

const loading       = ref(true)
const error         = ref("")
const asset         = ref(null)
const slide         = ref(0)
const formSent      = ref(false)
const sentEmail     = ref("")
const submitting    = ref(false)
const formError     = ref("")
const confirming    = ref(false)
const confirmLoading = ref(false)
const confirmResult  = ref("")
const confirmName    = ref("")

const BASE = import.meta.env.VITE_API_URL || "/api"

const form = reactive({
  name: "", phone: "", email: "", interest: "info", message: "", hp_field: "",
})

const interests = [
  { value: "arriendo", label: "Arriendo", icon: "bi-house-door" },
  { value: "compra",   label: "Compra",   icon: "bi-bag-check"  },
  { value: "info",     label: "Más info", icon: "bi-info-circle" },
]

function fmt(val) {
  if (val == null) return ""
  return new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(val)
}

async function load() {
  const token = route.params.confirmToken
  if (token) {
    confirming.value     = true
    confirmLoading.value = true
    loading.value        = false
    try {
      const res = await axios.get(`/api/public/inquiry/confirm/${token}`)
      confirmResult.value = res.data.message
      confirmName.value   = res.data.name || ""
    } catch {
      confirmResult.value = "error"
    } finally {
      confirmLoading.value = false
    }
    return
  }

  const code = route.params.listCode
  try {
    const res = await axios.get(`/api/public/activo/${code}`)
    asset.value = res.data
  } catch (e) {
    error.value = e.response?.data?.detail || "Activo no encontrado"
  } finally {
    loading.value = false
  }
}

async function submitForm() {
  formError.value = ""
  if (!form.name)  { formError.value = "El nombre es obligatorio"; return }
  if (!form.phone) { formError.value = "El teléfono es obligatorio"; return }
  if (!form.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    formError.value = "Ingresa un correo electrónico válido"; return
  }

  submitting.value = true
  try {
    const code = route.params.listCode
    await axios.post(`/api/public/activo/${code}/inquiry`, { ...form })
    sentEmail.value = form.email
    formSent.value  = true
  } catch (e) {
    formError.value = e.response?.data?.detail || "Error enviando solicitud. Intenta de nuevo."
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>

<style scoped>
* { box-sizing: border-box; }

.pub-page {
  min-height: 100vh;
  background: #f1f5f9;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #1e293b;
  max-width: 520px;
  margin: 0 auto;
  padding-bottom: 32px;
}

/* Estado loading/error/confirm */
.pub-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-height: 60vh; gap: 14px; text-align: center; padding: 32px;
  color: #64748b;
}
.pub-state h3 { color: #1e293b; margin: 0; font-size: 20px; }
.pub-state p  { margin: 0; font-size: 14px; }
.pub-error { color: #ef4444; }

.pub-spinner {
  width: 40px; height: 40px; border: 4px solid #e2e8f0;
  border-top-color: #3b82f6; border-radius: 50%;
  animation: spin .8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Header */
.pub-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px 12px; background: #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
}
.pub-brand {}
.pub-code {
  font-size: 13px; font-weight: 700; color: #3b82f6;
  background: #eff6ff; padding: 4px 12px; border-radius: 20px;
}
.brand-txt { font-size: 20px; font-weight: 800; letter-spacing: -0.5px; }
.brand-txt.sm { font-size: 14px; }
.b-blue  { color: #2563eb; }
.b-amber { color: #f59e0b; }
.b-green { color: #10b981; }

/* Carrusel */
.pub-carousel {
  position: relative; overflow: hidden; background: #000;
  height: 260px;
}
.carousel-track {
  display: flex; height: 100%;
  transition: transform .35s ease;
}
.carousel-slide { min-width: 100%; height: 100%; flex-shrink: 0; }
.carousel-img   { width: 100%; height: 100%; object-fit: cover; }

.car-btn {
  position: absolute; top: 50%; transform: translateY(-50%);
  background: rgba(0,0,0,.45); border: none; color: #fff;
  width: 38px; height: 38px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; font-size: 18px; z-index: 2;
}
.car-prev { left: 10px; }
.car-next { right: 10px; }

.car-dots {
  position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%);
  display: flex; gap: 6px;
}
.car-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: rgba(255,255,255,.5); cursor: pointer; transition: background .2s;
}
.car-dot.active { background: #fff; }

.pub-no-photo {
  height: 140px; display: flex; align-items: center; justify-content: center;
  background: #f8fafc;
}

/* Cards */
.pub-card {
  background: #fff; margin: 10px 12px 0;
  border-radius: 14px; padding: 18px 16px;
  box-shadow: 0 1px 6px rgba(0,0,0,.06);
}

.pub-cat {
  font-size: 12px; font-weight: 600; color: #3b82f6;
  background: #eff6ff; display: inline-block;
  padding: 2px 10px; border-radius: 20px; margin-bottom: 8px;
}
.pub-title    { font-size: 22px; font-weight: 800; margin: 0 0 2px; }
.pub-subtitle { font-size: 14px; color: #64748b; margin: 0 0 10px; }

.pub-detail-row {
  display: flex; align-items: flex-start; gap: 8px;
  font-size: 14px; color: #475569; margin: 8px 0;
}
.pub-detail-row .bi { color: #3b82f6; flex-shrink: 0; margin-top: 2px; }

/* Valores */
.pub-values { display: flex; gap: 10px; flex-wrap: wrap; margin: 14px 0 10px; }
.pub-value-card {
  flex: 1; min-width: 140px;
  background: #f0fdf4; border: 1px solid #bbf7d0;
  border-radius: 10px; padding: 12px 14px;
  display: flex; flex-direction: column; gap: 2px;
}
.pub-sale {
  background: #fefce8; border-color: #fde68a;
  flex-direction: row; align-items: center; gap: 8px; flex-wrap: wrap;
}
.pub-sale .bi { color: #f59e0b; font-size: 18px; }
.pvc-label   { font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: .4px; }
.pvc-amount  { font-size: 20px; font-weight: 800; color: #15803d; }
.pvc-period  { font-size: 12px; color: #64748b; }
.pvc-consult { font-size: 14px; font-weight: 700; color: #b45309; }

/* Badges */
.pub-badges { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px; }
.pub-badge  {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 12px; font-weight: 600; padding: 4px 12px; border-radius: 20px;
}
.pub-badge-available { background: #f0fdf4; color: #15803d; }
.pub-badge-rented    { background: #fef3c7; color: #92400e; }

.pub-desc { font-size: 14px; color: #475569; line-height: 1.6; margin: 8px 0 0; }

/* Formulario */
.pub-form-card { position: relative; overflow: hidden; }
.pub-form-title {
  font-size: 17px; font-weight: 700; margin: 0 0 16px;
  display: flex; align-items: center; gap: 8px; color: #1e293b;
}
.pub-form-title .bi { color: #3b82f6; }

.pf-group { margin-bottom: 12px; }
.pf-group label { display: block; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 4px; }
.pf-input {
  width: 100%; padding: 10px 12px; border: 1px solid #e2e8f0;
  border-radius: 8px; font-size: 14px; color: #1e293b;
  background: #f8fafc; outline: none; transition: border-color .15s;
  font-family: inherit;
}
.pf-input:focus { border-color: #3b82f6; background: #fff; }

.pf-interest-row { display: flex; gap: 8px; flex-wrap: wrap; }
.pf-interest-btn {
  flex: 1; min-width: 90px;
  padding: 9px 10px; border: 1px solid #e2e8f0;
  border-radius: 8px; background: #f8fafc;
  font-size: 13px; font-weight: 600; color: #475569;
  cursor: pointer; transition: all .15s;
  display: flex; align-items: center; justify-content: center; gap: 5px;
}
.pf-interest-btn.active {
  background: #2563eb; border-color: #2563eb; color: #fff;
}

.pf-error {
  background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px;
  padding: 10px 12px; font-size: 13px; color: #dc2626;
  display: flex; align-items: center; gap: 8px; margin-bottom: 12px;
}

.pf-submit {
  width: 100%; padding: 13px; background: #2563eb; color: #fff;
  border: none; border-radius: 10px; font-size: 15px; font-weight: 700;
  cursor: pointer; transition: background .15s;
  display: flex; align-items: center; justify-content: center; gap: 8px;
}
.pf-submit:hover:not(:disabled) { background: #1d4ed8; }
.pf-submit:disabled { opacity: .6; cursor: not-allowed; }

.pf-privacy {
  font-size: 11px; color: #94a3b8; text-align: center;
  margin: 10px 0 0; display: flex; align-items: center; justify-content: center; gap: 5px;
}

.pub-form-success {
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  text-align: center; padding: 10px 0 6px;
}
.pub-form-success h3 { font-size: 18px; font-weight: 700; color: #1e293b; margin: 0; }
.pub-form-success p  { font-size: 14px; color: #64748b; margin: 0; }

/* Footer */
.pub-footer {
  display: flex; flex-direction: column; align-items: center;
  gap: 4px; padding: 24px 0 8px;
  color: #94a3b8; font-size: 12px; text-align: center;
}

.spin { animation: spin .7s linear infinite; display: inline-block; }

@media (min-width: 480px) {
  .pub-carousel { height: 320px; }
}
</style>
