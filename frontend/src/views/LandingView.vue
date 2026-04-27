<template>
  <div class="landing-root">

    <!-- ══════════════════════════════════════════════
         NAVBAR FIJA
    ══════════════════════════════════════════════ -->
    <nav class="landing-nav">
      <div class="nav-inner">
        <a class="nav-brand" href="/landing">
          <span class="brand-easy">Easy</span><span class="brand-pos">Pos</span><span class="brand-web">Web</span>
        </a>
        <div class="nav-links">
          <a href="#perfiles"   class="nav-link-item">Perfiles</a>
          <a href="#modulos"    class="nav-link-item">Módulos</a>
          <a href="#planes"     class="nav-link-item">Planes</a>
          <a href="#contacto"   class="nav-link-item">Contacto</a>
        </div>
        <div class="nav-actions">
          <a href="/login"    class="btn-nav-outline">Iniciar Sesión</a>
          <a href="/register" class="btn-nav-solid">Empezar Gratis</a>
        </div>
        <button class="nav-hamburger" @click="mobileOpen = !mobileOpen">
          <i :class="mobileOpen ? 'bi bi-x-lg' : 'bi bi-list'"></i>
        </button>
      </div>
      <!-- Mobile menu -->
      <div class="nav-mobile" :class="{ open: mobileOpen }">
        <a href="#perfiles"  @click="mobileOpen=false">Perfiles</a>
        <a href="#modulos"   @click="mobileOpen=false">Módulos</a>
        <a href="#planes"    @click="mobileOpen=false">Planes</a>
        <a href="#contacto"  @click="mobileOpen=false">Contacto</a>
        <hr>
        <a href="/login"    class="btn-nav-outline w-100 text-center mb-2">Iniciar Sesión</a>
        <a href="/register" class="btn-nav-solid  w-100 text-center">Empezar Gratis</a>
      </div>
    </nav>

    <!-- ══════════════════════════════════════════════
         SLIDER PERFILES DE NEGOCIO  (primera sección)
    ══════════════════════════════════════════════ -->
    <section id="perfiles" class="section-perfiles">
      <div class="section-header text-center">
        <span class="section-badge">Perfiles de Negocio</span>
        <h2 class="section-title">{{ sections.profiles_intro?.title }}</h2>
        <p class="section-subtitle">{{ sections.profiles_intro?.subtitle }}</p>
      </div>

      <div v-if="profiles.length" class="profiles-slider">
        <div class="slider-track" :style="{ transform: `translateX(-${activeSlide * 100}%)` }">
          <div v-for="profile in profiles" :key="profile.id" class="slide-item">
            <div class="profile-card" :style="{ '--accent': profile.color_accent }">
              <div class="profile-image-wrap">
                <img v-if="profile.image_url" :src="profile.image_url" :alt="profile.name" class="profile-img" />
                <div v-else class="profile-img-placeholder">
                  <i :class="`bi ${profile.icon || 'bi-building'}`"></i>
                </div>
              </div>
              <div class="profile-info">
                <div class="profile-icon-badge">
                  <i :class="`bi ${profile.icon || 'bi-building'}`"></i>
                </div>
                <h3 class="profile-name">{{ profile.name }}</h3>
                <p class="profile-desc">
                  {{ profile.landing_description || profile.description || 'Solución integral para tu negocio.' }}
                </p>
                <a href="/register" class="btn-profile-cta">
                  Probar Gratis <i class="bi bi-arrow-right ms-1"></i>
                </a>
              </div>
            </div>
          </div>
        </div>

        <!-- Dots -->
        <div class="slider-dots">
          <button
            v-for="(p, i) in profiles"
            :key="i"
            class="slider-dot"
            :class="{ active: i === activeSlide }"
            @click="goToSlide(i)"
          ></button>
        </div>

        <!-- Arrows -->
        <button class="slider-arrow left"  @click="prevSlide"><i class="bi bi-chevron-left"></i></button>
        <button class="slider-arrow right" @click="nextSlide"><i class="bi bi-chevron-right"></i></button>
      </div>

      <div v-else class="text-center py-5 text-muted">
        <i class="bi bi-buildings fs-1"></i>
        <p class="mt-2">Cargando perfiles...</p>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════
         HERO  (segunda sección)
    ══════════════════════════════════════════════ -->
    <section class="hero-section">
      <div class="hero-bg-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
      </div>
      <div class="hero-content">
        <div class="hero-badge animate-fade-in">
          <i class="bi bi-lightning-charge-fill"></i> 100% en la nube · Gratis para empezar
        </div>
        <h1 class="hero-title animate-slide-up">
          {{ sections.hero?.title || 'Tu negocio, en línea. Sin complicaciones.' }}
        </h1>
        <p class="hero-subtitle animate-slide-up delay-1">
          {{ sections.hero?.subtitle }}
        </p>
        <div class="hero-actions animate-slide-up delay-2">
          <a :href="sections.hero?.cta_url || '/register'" class="btn-hero-primary">
            <i class="bi bi-rocket-takeoff-fill me-2"></i>
            {{ sections.hero?.cta_text || 'Empezar Gratis' }}
          </a>
          <a href="#planes" class="btn-hero-outline">
            <i class="bi bi-eye me-2"></i> Ver Planes
          </a>
        </div>
        <div class="hero-stats animate-fade-in delay-3">
          <div class="stat-item">
            <span class="stat-number">100%</span>
            <span class="stat-label">En línea</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-number">0$</span>
            <span class="stat-label">Para empezar</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-number">∞</span>
            <span class="stat-label">Dispositivos</span>
          </div>
        </div>
      </div>
      <div class="hero-devices animate-float">
        <div class="device-mockup">
          <div class="device-screen">
            <div class="screen-topbar"></div>
            <div class="screen-content">
              <div class="screen-line w-75"></div>
              <div class="screen-line w-50 mt-2"></div>
              <div class="screen-cards">
                <div class="screen-card green"></div>
                <div class="screen-card blue"></div>
                <div class="screen-card orange"></div>
              </div>
              <div class="screen-line w-100 mt-2"></div>
              <div class="screen-line w-60 mt-1"></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════
         MÓDULOS / CARACTERÍSTICAS
    ══════════════════════════════════════════════ -->
    <section id="modulos" class="section-modulos">
      <div class="section-header text-center">
        <span class="section-badge blue">Funcionalidades</span>
        <h2 class="section-title">{{ sections.features?.title }}</h2>
        <p class="section-subtitle">{{ sections.features?.subtitle }}</p>
      </div>
      <div class="features-grid" ref="featuresGrid">
        <div
          v-for="(feat, i) in featureItems"
          :key="i"
          class="feature-card reveal"
          :style="{ '--delay': `${(i % 4) * 0.1}s` }"
        >
          <div class="feat-icon-wrap">
            <i :class="`bi ${featureIcons[i] || 'bi-check-circle'}`"></i>
          </div>
          <p class="feat-text">{{ feat }}</p>
        </div>
      </div>

      <!-- Multidevice strip -->
      <div class="multidevice-strip">
        <div class="strip-left">
          <h3>{{ sections.multidevice?.title }}</h3>
          <p>{{ sections.multidevice?.subtitle }}</p>
          <ul class="strip-list">
            <li v-for="item in multideviceItems" :key="item">
              <i class="bi bi-check-circle-fill me-2"></i>{{ item }}
            </li>
          </ul>
          <a :href="sections.multidevice?.cta_url || '#'" class="btn-strip-cta">
            {{ sections.multidevice?.cta_text || 'Registrarse Ahora' }}
            <i class="bi bi-arrow-right ms-2"></i>
          </a>
        </div>
        <div class="strip-right">
          <div class="devices-row">
            <div class="mini-device laptop"><i class="bi bi-laptop"></i></div>
            <div class="mini-device phone"><i class="bi bi-phone"></i></div>
            <div class="mini-device tablet"><i class="bi bi-tablet"></i></div>
          </div>
        </div>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════
         PLAN GRATIS — CTA DESTACADO
    ══════════════════════════════════════════════ -->
    <section class="section-free-plan">
      <div class="free-plan-inner">
        <div class="free-plan-badge">
          <i class="bi bi-gift-fill me-2"></i> Plan Gratuito — Completamente Funcional
        </div>
        <h2 class="free-plan-title">{{ sections.free_plan?.title }}</h2>
        <p class="free-plan-subtitle">{{ sections.free_plan?.subtitle }}</p>
        <ul class="free-plan-list">
          <li v-for="item in freePlanItems" :key="item">
            <i class="bi bi-check-circle-fill"></i>
            <span>{{ item }}</span>
          </li>
        </ul>
        <div class="free-plan-cta-wrap">
          <a :href="sections.free_plan?.cta_url || '/register'" class="btn-free-primary">
            <i class="bi bi-rocket-takeoff-fill me-2"></i>
            {{ sections.free_plan?.cta_text || 'Registrarse Gratis' }}
          </a>
          <p class="free-plan-note">
            Sin tarjeta de crédito · Sin contrato · Empieza en minutos
          </p>
        </div>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════
         TABLA DE PLANES
    ══════════════════════════════════════════════ -->
    <section id="planes" class="section-planes">
      <div class="section-header text-center">
        <span class="section-badge green">Precios</span>
        <h2 class="section-title">Planes para cada etapa de tu negocio</h2>
        <p class="section-subtitle">Comienza gratis y escala cuando lo necesites</p>
      </div>

      <!-- Cards de precios -->
      <div class="pricing-cards" v-if="planData.plans?.length">
        <div
          v-for="(plan, i) in planData.plans"
          :key="plan.id"
          class="pricing-card"
          :class="{ featured: i === 2 }"
        >
          <div v-if="i === 2" class="pricing-badge">Más Popular</div>
          <div class="pricing-name">{{ plan.name }}</div>
          <div class="pricing-price">
            <span v-if="plan.price === 0" class="price-free">GRATIS</span>
            <template v-else>
              <span class="price-currency">$</span>
              <span class="price-amount">{{ formatPrice(plan.price) }}</span>
              <span class="price-period">/mes</span>
            </template>
          </div>
          <a href="/register" class="btn-pricing" :class="{ 'btn-pricing-featured': i === 2 }">
            {{ i === 0 ? 'Empezar Gratis' : 'Comenzar' }}
          </a>
        </div>
      </div>

      <!-- Tabla comparativa de features -->
      <div class="features-table-wrap" v-if="planData.feature_groups?.length">
        <table class="features-table">
          <thead>
            <tr>
              <th class="feat-col-name">Funcionalidad</th>
              <th v-for="plan in planData.plans" :key="plan.id" class="feat-col-plan">
                {{ plan.name }}
              </th>
            </tr>
          </thead>
          <tbody>
            <template v-for="group in planData.feature_groups" :key="group.category">
              <tr class="feat-group-header">
                <td :colspan="(planData.plans?.length || 0) + 1">
                  <i class="bi bi-grid-3x3-gap-fill me-2"></i>{{ group.category }}
                </td>
              </tr>
              <tr v-for="feat in group.features" :key="feat.id" class="feat-row">
                <td class="feat-name">{{ feat.feature_name }}</td>
                <td class="feat-val">{{ renderVal(feat.val_free) }}</td>
                <td class="feat-val">{{ renderVal(feat.val_basic) }}</td>
                <td class="feat-val">{{ renderVal(feat.val_standard) }}</td>
                <td class="feat-val">{{ renderVal(feat.val_premium) }}</td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════
         NOTAS IMPORTANTES
    ══════════════════════════════════════════════ -->
    <section class="section-about" v-if="sections.about?.body_text">
      <div class="about-inner">
        <div class="about-icon"><i class="bi bi-info-circle-fill"></i></div>
        <h3 class="about-title">{{ sections.about?.title }}</h3>
        <ul class="about-list">
          <li v-for="item in aboutItems" :key="item">
            <i class="bi bi-dot fs-4"></i><span>{{ item }}</span>
          </li>
        </ul>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════
         PASARELA DE PAGO (placeholder)
    ══════════════════════════════════════════════ -->
    <section class="section-payment">
      <div class="section-header text-center">
        <span class="section-badge orange">Pagos</span>
        <h2 class="section-title">Paga de forma segura</h2>
        <p class="section-subtitle">Múltiples métodos de pago disponibles próximamente</p>
      </div>
      <div class="payment-methods">
        <div class="payment-card coming-soon">
          <i class="bi bi-bank2"></i>
          <span>PSE</span>
          <div class="soon-tag">Próximamente</div>
        </div>
        <div class="payment-card coming-soon">
          <i class="bi bi-phone-fill"></i>
          <span>Nequi</span>
          <div class="soon-tag">Próximamente</div>
        </div>
        <div class="payment-card coming-soon">
          <i class="bi bi-wallet2"></i>
          <span>Daviplata</span>
          <div class="soon-tag">Próximamente</div>
        </div>
        <div class="payment-card coming-soon">
          <i class="bi bi-credit-card-2-front-fill"></i>
          <span>Tarjeta Débito / Crédito</span>
          <div class="soon-tag">Próximamente</div>
        </div>
        <div class="payment-card coming-soon">
          <i class="bi bi-cash-stack"></i>
          <span>Efectivo / Consignación</span>
          <div class="soon-tag">Próximamente</div>
        </div>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════
         FORMULARIO DE CONTACTO
    ══════════════════════════════════════════════ -->
    <section id="contacto" class="section-contacto">
      <div class="contact-grid">
        <div class="contact-info">
          <span class="section-badge white">Contáctanos</span>
          <h2 class="contact-title">{{ sections.contact?.title }}</h2>
          <p class="contact-subtitle">{{ sections.contact?.subtitle }}</p>
          <div class="contact-details">
            <div class="contact-item">
              <i class="bi bi-envelope-fill"></i>
              <span>easypos.co@gmail.com</span>
            </div>
            <div class="contact-item">
              <i class="bi bi-globe"></i>
              <span>easyposweb.com</span>
            </div>
            <div class="contact-item">
              <i class="bi bi-clock-fill"></i>
              <span>Respuesta en menos de 24 horas</span>
            </div>
          </div>
        </div>
        <div class="contact-form-wrap">
          <form class="contact-form" @submit.prevent="submitContact">
            <div class="form-row-2">
              <div class="form-group">
                <label>Nombre *</label>
                <input v-model="form.name" type="text" class="form-ctrl" :class="{ invalid: formErrors.name }" placeholder="Tu nombre completo" />
                <span v-if="formErrors.name" class="form-error">{{ formErrors.name }}</span>
              </div>
              <div class="form-group">
                <label>Empresa</label>
                <input v-model="form.company" type="text" class="form-ctrl" placeholder="Nombre de tu empresa" />
              </div>
            </div>
            <div class="form-row-2">
              <div class="form-group">
                <label>Email *</label>
                <input v-model="form.email" type="email" class="form-ctrl" :class="{ invalid: formErrors.email }" placeholder="correo@empresa.com" />
                <span v-if="formErrors.email" class="form-error">{{ formErrors.email }}</span>
              </div>
              <div class="form-group">
                <label>Teléfono</label>
                <input v-model="form.phone" type="tel" class="form-ctrl" placeholder="+57 300 000 0000" />
              </div>
            </div>
            <div class="form-group">
              <label>Mensaje *</label>
              <textarea v-model="form.message" class="form-ctrl form-textarea" :class="{ invalid: formErrors.message }" rows="5" placeholder="Cuéntanos en qué podemos ayudarte..."></textarea>
              <span v-if="formErrors.message" class="form-error">{{ formErrors.message }}</span>
            </div>
            <button type="submit" class="btn-contact-submit" :disabled="submitting">
              <span v-if="submitting"><i class="bi bi-hourglass-split me-2"></i>Enviando...</span>
              <span v-else><i class="bi bi-send-fill me-2"></i>Enviar Mensaje</span>
            </button>
            <div v-if="contactSuccess" class="contact-success">
              <i class="bi bi-check-circle-fill me-2"></i>
              Mensaje enviado. Te contactaremos pronto.
            </div>
            <div v-if="contactError" class="contact-error">
              <i class="bi bi-exclamation-circle-fill me-2"></i>
              {{ contactError }}
            </div>
          </form>
        </div>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════
         FOOTER
    ══════════════════════════════════════════════ -->
    <footer class="landing-footer">
      <div class="footer-top">
        <div class="footer-brand">
          <span class="brand-easy">Easy</span><span class="brand-pos">Pos</span><span class="brand-web">Web</span>
          <p class="footer-tagline">Tu negocio, en línea. Sin complicaciones.</p>
        </div>
        <div class="footer-links">
          <div class="footer-col">
            <h5>Producto</h5>
            <a href="#modulos">Módulos</a>
            <a href="#planes">Planes</a>
            <a href="#perfiles">Perfiles</a>
          </div>
          <div class="footer-col">
            <h5>Empresa</h5>
            <a href="#contacto">Contacto</a>
            <a href="#contacto">Soporte</a>
          </div>
          <div class="footer-col">
            <h5>Legal</h5>
            <a href="#">Términos de Uso</a>
            <a href="#">Política de Privacidad</a>
          </div>
        </div>
      </div>
      <div class="footer-bottom">
        <p>© {{ currentYear }} EasyPosWeb · easyposweb.com · easypos.co@gmail.com</p>
        <div class="footer-socials">
          <a href="#" title="Facebook"><i class="bi bi-facebook"></i></a>
          <a href="#" title="WhatsApp"><i class="bi bi-whatsapp"></i></a>
          <a href="#" title="Instagram"><i class="bi bi-instagram"></i></a>
        </div>
      </div>
    </footer>

  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from "vue"

const API = import.meta.env.VITE_API_URL || "http://localhost:8000"

const FEATURE_ICONS = [
  "bi-receipt-cutoff", "bi-cash-coin", "bi-people-fill", "bi-credit-card-2-front",
  "bi-printer-fill", "bi-bag-plus-fill", "bi-wallet2", "bi-box-seam",
  "bi-graph-up-arrow", "bi-file-earmark-excel", "bi-calculator", "bi-clipboard2-data",
  "bi-person-lock", "bi-tags-fill", "bi-bar-chart-line", "bi-pie-chart-fill",
  "bi-percent"
]

const MULTIDEVICE_ICONS = [
  "bi-laptop", "bi-phone", "bi-tablet", "bi-wifi", "bi-globe2"
]

export default {
  name: "LandingView",

  setup() {
    const sections       = reactive({})
    const profiles       = ref([])
    const planData       = reactive({ plans: [], feature_groups: [] })
    const activeSlide    = ref(0)
    const sliderTimer    = ref(null)
    const mobileOpen     = ref(false)
    const featuresGrid   = ref(null)
    const submitting     = ref(false)
    const contactSuccess = ref(false)
    const contactError   = ref("")

    const form = reactive({ name: "", email: "", phone: "", company: "", message: "" })
    const formErrors = reactive({ name: "", email: "", message: "" })

    const currentYear = new Date().getFullYear()

    // ── Computed: parsear body_text (pipe-separated) ─────────
    const featureItems = computed(() => {
      return (sections.features?.body_text || "").split("|").map(s => s.trim()).filter(Boolean)
    })

    const freePlanItems = computed(() => {
      return (sections.free_plan?.body_text || "").split("|").map(s => s.trim()).filter(Boolean)
    })

    const aboutItems = computed(() => {
      return (sections.about?.body_text || "").split("|").map(s => s.trim()).filter(Boolean)
    })

    const multideviceItems = computed(() => {
      return (sections.multidevice?.body_text || "").split("|").map(s => s.trim()).filter(Boolean)
    })

    const featureIcons = computed(() => FEATURE_ICONS)

    // ── Slider ───────────────────────────────────────────────
    function goToSlide(i) {
      activeSlide.value = i
      resetTimer()
    }
    function nextSlide() {
      activeSlide.value = (activeSlide.value + 1) % profiles.value.length
      resetTimer()
    }
    function prevSlide() {
      activeSlide.value = (activeSlide.value - 1 + profiles.value.length) % profiles.value.length
      resetTimer()
    }
    function startTimer() {
      sliderTimer.value = setInterval(() => {
        if (profiles.value.length > 1) nextSlide()
      }, 5000)
    }
    function resetTimer() {
      clearInterval(sliderTimer.value)
      startTimer()
    }

    // ── Format helpers ────────────────────────────────────────
    function formatPrice(price) {
      return new Intl.NumberFormat("es-CO").format(price)
    }

    function renderVal(val) {
      if (!val || val === "") return "—"
      const v = val.toLowerCase()
      if (v === "x") return "✓"
      if (v === "ilim") return "Ilimitado"
      return val
    }

    // ── Contacto ──────────────────────────────────────────────
    function validateForm() {
      let ok = true
      formErrors.name = formErrors.email = formErrors.message = ""
      if (!form.name.trim()) { formErrors.name = "El nombre es obligatorio"; ok = false }
      if (!form.email.trim()) { formErrors.email = "El email es obligatorio"; ok = false }
      else if (!/\S+@\S+\.\S+/.test(form.email)) { formErrors.email = "Email inválido"; ok = false }
      if (!form.message.trim()) { formErrors.message = "El mensaje es obligatorio"; ok = false }
      return ok
    }

    async function submitContact() {
      if (!validateForm()) return
      submitting.value = true
      contactSuccess.value = false
      contactError.value = ""
      try {
        const res = await fetch(`${API}/landing/contact`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ...form }),
        })
        if (!res.ok) {
          const err = await res.json()
          throw new Error(err.detail || "Error al enviar")
        }
        contactSuccess.value = true
        form.name = form.email = form.phone = form.company = form.message = ""
      } catch (e) {
        contactError.value = e.message
      } finally {
        submitting.value = false
      }
    }

    // ── Scroll reveal ─────────────────────────────────────────
    function initReveal() {
      const cards = document.querySelectorAll(".reveal")
      if (!cards.length) return
      const obs = new IntersectionObserver((entries) => {
        entries.forEach(e => {
          if (e.isIntersecting) e.target.classList.add("revealed")
        })
      }, { threshold: 0.1 })
      cards.forEach(c => obs.observe(c))
    }

    // ── Fetch data ────────────────────────────────────────────
    async function loadData() {
      try {
        const [secRes, profRes, planRes] = await Promise.all([
          fetch(`${API}/landing/sections`),
          fetch(`${API}/landing/profiles`),
          fetch(`${API}/landing/plans`),
        ])
        const [secData, profData, pData] = await Promise.all([
          secRes.json(), profRes.json(), planRes.json()
        ])

        secData.forEach(s => { sections[s.section_key] = s })
        profiles.value = profData
        planData.plans         = pData.plans         || []
        planData.feature_groups = pData.feature_groups || []

        if (profData.length > 1) startTimer()
      } catch (e) {
        console.error("Error cargando landing:", e)
      }
    }

    onMounted(async () => {
      await loadData()
      setTimeout(initReveal, 300)
    })

    onBeforeUnmount(() => clearInterval(sliderTimer.value))

    return {
      sections, profiles, planData, activeSlide, mobileOpen,
      featuresGrid, featureItems, freePlanItems, aboutItems,
      multideviceItems, featureIcons, form, formErrors,
      submitting, contactSuccess, contactError, currentYear,
      goToSlide, nextSlide, prevSlide,
      formatPrice, renderVal, submitContact,
    }
  }
}
</script>

<style scoped>
/* ════════════════════════════════════════════════════
   VARIABLES Y BASE
════════════════════════════════════════════════════ */
.landing-root {
  --primary:     #2563eb;
  --primary-dark:#1d4ed8;
  --accent:      #10b981;
  --orange:      #f59e0b;
  --dark:        #0f172a;
  --dark2:       #1e293b;
  --gray:        #64748b;
  --light:       #f8fafc;
  --white:       #ffffff;
  --radius:      12px;
  --shadow:      0 4px 24px rgba(0,0,0,.08);
  --shadow-lg:   0 12px 48px rgba(0,0,0,.15);
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  color: var(--dark);
  background: var(--white);
  overflow-x: hidden;
}

/* ════════════════════════════════════════════════════
   NAVBAR
════════════════════════════════════════════════════ */
.landing-nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 1000;
  background: rgba(255,255,255,.92);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(0,0,0,.06);
  box-shadow: 0 2px 20px rgba(0,0,0,.06);
}
.nav-inner {
  max-width: 1200px; margin: 0 auto; padding: 0 24px;
  height: 68px; display: flex; align-items: center; gap: 32px;
}
.nav-brand { text-decoration: none; font-size: 1.5rem; font-weight: 800; letter-spacing: -.5px; }
.brand-easy { color: var(--primary); }
.brand-pos  { color: var(--dark); }
.brand-web  { color: var(--accent); }
.nav-links  { display: flex; gap: 24px; flex: 1; }
.nav-link-item {
  color: var(--gray); text-decoration: none; font-size: .9rem; font-weight: 500;
  transition: color .2s;
}
.nav-link-item:hover { color: var(--primary); }
.nav-actions { display: flex; gap: 10px; align-items: center; }
.btn-nav-outline {
  padding: 8px 18px; border: 1.5px solid var(--primary); color: var(--primary);
  border-radius: 8px; font-size: .9rem; font-weight: 600; text-decoration: none;
  transition: all .2s;
}
.btn-nav-outline:hover { background: var(--primary); color: #fff; }
.btn-nav-solid {
  padding: 8px 18px; background: var(--primary); color: #fff;
  border-radius: 8px; font-size: .9rem; font-weight: 600; text-decoration: none;
  transition: all .2s;
}
.btn-nav-solid:hover { background: var(--primary-dark); }
.nav-hamburger {
  display: none; background: none; border: none; font-size: 1.5rem;
  color: var(--dark); cursor: pointer;
}
.nav-mobile {
  display: none; flex-direction: column; gap: 12px;
  padding: 16px 24px; border-top: 1px solid #eee;
}
.nav-mobile a { color: var(--dark); text-decoration: none; font-size: .95rem; }
.nav-mobile.open { display: flex; }

/* ════════════════════════════════════════════════════
   HERO
════════════════════════════════════════════════════ */
.hero-section {
  min-height: 100vh; padding-top: 68px;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 40%, #1a3a6e 100%);
  display: flex; align-items: center; position: relative; overflow: hidden;
  gap: 60px; padding-left: 10%; padding-right: 6%;
}
.hero-bg-shapes { position: absolute; inset: 0; pointer-events: none; }
.shape {
  position: absolute; border-radius: 50%;
  background: rgba(37,99,235,.15);
  animation: floatShape 8s ease-in-out infinite;
}
.shape-1 { width: 500px; height: 500px; top: -100px; right: -100px; animation-delay: 0s; }
.shape-2 { width: 300px; height: 300px; bottom: 50px; left: 30%; animation-delay: 2s; background: rgba(16,185,129,.1); }
.shape-3 { width: 200px; height: 200px; top: 40%; right: 20%; animation-delay: 4s; background: rgba(245,158,11,.08); }

@keyframes floatShape {
  0%,100% { transform: translate(0,0) scale(1); }
  50%      { transform: translate(20px,-30px) scale(1.05); }
}

.hero-content { position: relative; z-index: 1; max-width: 580px; color: #fff; }
.hero-badge {
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(37,99,235,.3); border: 1px solid rgba(37,99,235,.5);
  color: #93c5fd; padding: 6px 14px; border-radius: 20px;
  font-size: .82rem; font-weight: 600; margin-bottom: 20px;
}
.hero-title {
  font-size: clamp(2rem, 4vw, 3.2rem); font-weight: 800;
  line-height: 1.15; margin-bottom: 20px;
  background: linear-gradient(135deg, #fff 0%, #93c5fd 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.hero-subtitle {
  font-size: 1.1rem; color: #94a3b8; margin-bottom: 32px; line-height: 1.7;
}
.hero-actions { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 40px; }
.btn-hero-primary {
  display: inline-flex; align-items: center;
  background: var(--primary); color: #fff;
  padding: 14px 28px; border-radius: 10px; font-weight: 700; font-size: 1rem;
  text-decoration: none; transition: all .25s; box-shadow: 0 4px 20px rgba(37,99,235,.4);
}
.btn-hero-primary:hover { background: #1d4ed8; transform: translateY(-2px); color: #fff; }
.btn-hero-outline {
  display: inline-flex; align-items: center;
  border: 1.5px solid rgba(255,255,255,.3); color: #fff;
  padding: 14px 28px; border-radius: 10px; font-weight: 600; font-size: 1rem;
  text-decoration: none; transition: all .25s;
}
.btn-hero-outline:hover { background: rgba(255,255,255,.1); color: #fff; }
.hero-stats {
  display: flex; align-items: center; gap: 24px;
  padding: 16px 24px; background: rgba(255,255,255,.06);
  border: 1px solid rgba(255,255,255,.1); border-radius: 12px;
  backdrop-filter: blur(8px);
}
.stat-item { text-align: center; }
.stat-number { display: block; font-size: 1.6rem; font-weight: 800; color: #93c5fd; }
.stat-label  { font-size: .75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: .05em; }
.stat-divider { width: 1px; height: 36px; background: rgba(255,255,255,.15); }

/* Device mockup */
.hero-devices { position: relative; z-index: 1; flex-shrink: 0; }
.device-mockup {
  width: 280px; background: #1e293b; border-radius: 16px;
  border: 2px solid rgba(255,255,255,.1); overflow: hidden;
  box-shadow: 0 24px 60px rgba(0,0,0,.5);
}
.device-screen { background: #0f172a; }
.screen-topbar {
  height: 36px; background: #2563eb;
  border-radius: 0; margin-bottom: 0;
}
.screen-content { padding: 16px; }
.screen-line {
  height: 8px; background: #1e293b; border-radius: 4px;
}
.w-75 { width: 75%; }
.w-50 { width: 50%; }
.w-60 { width: 60%; }
.w-100 { width: 100%; }
.screen-cards { display: flex; gap: 8px; margin-top: 12px; }
.screen-card { flex: 1; height: 48px; border-radius: 6px; }
.screen-card.green  { background: #10b981; }
.screen-card.blue   { background: #2563eb; }
.screen-card.orange { background: #f59e0b; }
.animate-float { animation: floatDevice 4s ease-in-out infinite; }
@keyframes floatDevice {
  0%,100% { transform: translateY(0); }
  50%      { transform: translateY(-12px); }
}

/* ════════════════════════════════════════════════════
   ANIMACIONES HERO
════════════════════════════════════════════════════ */
@keyframes fadeIn   { from { opacity: 0; }                to { opacity: 1; } }
@keyframes slideUp  { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }

.animate-fade-in  { animation: fadeIn  .8s ease both; }
.animate-slide-up { animation: slideUp .8s ease both; }
.delay-1 { animation-delay: .2s; }
.delay-2 { animation-delay: .4s; }
.delay-3 { animation-delay: .6s; }

/* ════════════════════════════════════════════════════
   SECCIÓN COMUNES
════════════════════════════════════════════════════ */
.section-header   { margin-bottom: 48px; }
.section-badge {
  display: inline-block; padding: 4px 14px; border-radius: 20px; font-size: .78rem;
  font-weight: 700; text-transform: uppercase; letter-spacing: .08em;
  background: rgba(37,99,235,.1); color: var(--primary); margin-bottom: 12px;
}
.section-badge.blue   { background: rgba(37,99,235,.1); color: var(--primary); }
.section-badge.green  { background: rgba(16,185,129,.1); color: #059669; }
.section-badge.orange { background: rgba(245,158,11,.1); color: #d97706; }
.section-badge.white  { background: rgba(255,255,255,.15); color: #fff; }
.section-title    { font-size: clamp(1.6rem,3vw,2.2rem); font-weight: 800; margin-bottom: 12px; }
.section-subtitle { color: var(--gray); font-size: 1rem; max-width: 600px; margin: 0 auto; }

/* ════════════════════════════════════════════════════
   PERFILES SLIDER
════════════════════════════════════════════════════ */
.section-perfiles {
  min-height: 100vh;
  padding: 68px 24px 60px;
  background: var(--light);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.profiles-slider  { max-width: 900px; margin: 0 auto; position: relative; overflow: hidden; }
.slider-track {
  display: flex; transition: transform .5s cubic-bezier(.4,0,.2,1);
}
.slide-item { min-width: 100%; padding: 0 8px; }
.profile-card {
  display: flex; gap: 40px; align-items: center;
  background: #fff; border-radius: 20px; padding: 40px;
  box-shadow: var(--shadow-lg);
  border-top: 4px solid var(--accent, var(--primary));
}
.profile-image-wrap { flex-shrink: 0; }
.profile-img {
  width: 220px; height: 160px; object-fit: cover; border-radius: 12px;
}
.profile-img-placeholder {
  width: 220px; height: 160px; border-radius: 12px;
  background: linear-gradient(135deg, var(--accent, #2563eb) 0%, rgba(37,99,235,.3) 100%);
  display: flex; align-items: center; justify-content: center;
  font-size: 4rem; color: rgba(255,255,255,.9);
}
.profile-info { flex: 1; }
.profile-icon-badge {
  width: 48px; height: 48px; border-radius: 12px;
  background: linear-gradient(135deg, var(--accent, #2563eb), rgba(37,99,235,.5));
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 1.5rem; margin-bottom: 12px;
}
.profile-name { font-size: 1.6rem; font-weight: 800; margin-bottom: 10px; }
.profile-desc { color: var(--gray); line-height: 1.7; margin-bottom: 20px; }
.btn-profile-cta {
  display: inline-flex; align-items: center;
  background: var(--primary); color: #fff;
  padding: 10px 22px; border-radius: 8px; font-weight: 600; font-size: .9rem;
  text-decoration: none; transition: all .2s;
}
.btn-profile-cta:hover { background: var(--primary-dark); transform: translateX(4px); color: #fff; }

.slider-dots { display: flex; justify-content: center; gap: 8px; margin-top: 24px; }
.slider-dot {
  width: 8px; height: 8px; border-radius: 50%; border: none;
  background: #cbd5e1; cursor: pointer; transition: all .25s; padding: 0;
}
.slider-dot.active { background: var(--primary); width: 24px; border-radius: 4px; }

.slider-arrow {
  position: absolute; top: 50%; transform: translateY(-50%);
  width: 44px; height: 44px; border-radius: 50%; border: none;
  background: #fff; box-shadow: 0 2px 12px rgba(0,0,0,.15);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; font-size: 1.1rem; color: var(--dark);
  transition: all .2s; z-index: 2;
}
.slider-arrow:hover { background: var(--primary); color: #fff; }
.slider-arrow.left  { left: -20px; }
.slider-arrow.right { right: -20px; }

/* ════════════════════════════════════════════════════
   MÓDULOS
════════════════════════════════════════════════════ */
.section-modulos { padding: 96px 24px; max-width: 1200px; margin: 0 auto; }
.features-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: 16px; margin-bottom: 60px;
}
.feature-card {
  background: #fff; border: 1px solid #e2e8f0; border-radius: var(--radius);
  padding: 20px; display: flex; align-items: flex-start; gap: 14px;
  box-shadow: var(--shadow); transition: all .3s; cursor: default;
  opacity: 0; transform: translateY(20px);
  transition: opacity .5s var(--delay, 0s), transform .5s var(--delay, 0s), box-shadow .2s;
}
.feature-card.revealed { opacity: 1; transform: translateY(0); }
.feature-card:hover { box-shadow: var(--shadow-lg); transform: translateY(-3px); }
.feat-icon-wrap {
  width: 38px; height: 38px; border-radius: 10px;
  background: linear-gradient(135deg, var(--primary), #6366f1);
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 1rem; flex-shrink: 0;
}
.feat-text { font-size: .88rem; color: var(--dark); line-height: 1.5; margin: 0; padding-top: 8px; }

/* Multidevice strip */
.multidevice-strip {
  background: linear-gradient(135deg, #0f172a, #1e3a8a);
  border-radius: 20px; padding: 48px; display: flex;
  gap: 48px; align-items: center; color: #fff;
}
.strip-left { flex: 1; }
.strip-left h3 { font-size: 1.7rem; font-weight: 800; margin-bottom: 10px; }
.strip-left p  { color: #94a3b8; margin-bottom: 20px; }
.strip-list { list-style: none; padding: 0; margin-bottom: 24px; }
.strip-list li {
  display: flex; align-items: center; gap: 6px;
  color: #cbd5e1; font-size: .9rem; margin-bottom: 8px;
}
.strip-list .bi-check-circle-fill { color: var(--accent); }
.btn-strip-cta {
  display: inline-flex; align-items: center;
  background: var(--accent); color: #fff;
  padding: 12px 24px; border-radius: 10px; font-weight: 700;
  text-decoration: none; transition: all .2s;
}
.btn-strip-cta:hover { background: #059669; transform: translateX(4px); color: #fff; }
.strip-right { display: flex; align-items: center; justify-content: center; }
.devices-row { display: flex; gap: 24px; align-items: flex-end; }
.mini-device {
  display: flex; flex-direction: column; align-items: center;
  background: rgba(255,255,255,.1); border: 1px solid rgba(255,255,255,.2);
  border-radius: 12px; padding: 16px 20px; font-size: 2.4rem; color: #93c5fd;
}
.mini-device.laptop { padding: 20px 28px; }
.mini-device.tablet { font-size: 2rem; }

/* ════════════════════════════════════════════════════
   PLAN GRATIS CTA
════════════════════════════════════════════════════ */
.section-free-plan {
  background: linear-gradient(135deg, #064e3b 0%, #065f46 50%, #047857 100%);
  padding: 96px 24px;
}
.free-plan-inner {
  max-width: 720px; margin: 0 auto; text-align: center; color: #fff;
}
.free-plan-badge {
  display: inline-flex; align-items: center;
  background: rgba(255,255,255,.15); border: 1px solid rgba(255,255,255,.25);
  color: #a7f3d0; padding: 6px 16px; border-radius: 20px;
  font-size: .82rem; font-weight: 600; margin-bottom: 20px;
}
.free-plan-title {
  font-size: clamp(1.8rem, 3.5vw, 2.6rem); font-weight: 800;
  margin-bottom: 12px; line-height: 1.2;
}
.free-plan-subtitle {
  color: #6ee7b7; font-size: 1.1rem; font-weight: 600;
  letter-spacing: .05em; text-transform: uppercase; margin-bottom: 32px;
}
.free-plan-list {
  list-style: none; padding: 0; margin-bottom: 36px;
  display: flex; flex-direction: column; gap: 12px;
}
.free-plan-list li {
  display: flex; align-items: center; gap: 12px;
  background: rgba(255,255,255,.1); border: 1px solid rgba(255,255,255,.15);
  border-radius: 10px; padding: 12px 20px; font-size: 1rem;
  text-align: left;
}
.free-plan-list .bi-check-circle-fill { color: #6ee7b7; font-size: 1.2rem; flex-shrink: 0; }
.btn-free-primary {
  display: inline-flex; align-items: center; justify-content: center;
  background: #fff; color: #065f46;
  padding: 16px 36px; border-radius: 12px; font-weight: 800; font-size: 1.1rem;
  text-decoration: none; transition: all .25s; box-shadow: 0 4px 20px rgba(0,0,0,.2);
}
.btn-free-primary:hover { transform: translateY(-3px); box-shadow: 0 8px 28px rgba(0,0,0,.25); color: #064e3b; }
.free-plan-note {
  color: #a7f3d0; font-size: .82rem; margin-top: 12px;
}

/* ════════════════════════════════════════════════════
   PLANES
════════════════════════════════════════════════════ */
.section-planes { padding: 96px 24px; background: var(--light); }
.section-planes .section-header { max-width: 1200px; margin: 0 auto 48px; }

.pricing-cards {
  max-width: 900px; margin: 0 auto 60px;
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;
}
.pricing-card {
  background: #fff; border-radius: 16px; padding: 28px 20px;
  text-align: center; border: 1px solid #e2e8f0;
  box-shadow: var(--shadow); position: relative; transition: all .25s;
}
.pricing-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-lg); }
.pricing-card.featured {
  background: var(--primary); color: #fff;
  border-color: var(--primary); transform: scale(1.04);
  box-shadow: 0 8px 40px rgba(37,99,235,.4);
}
.pricing-badge {
  position: absolute; top: -14px; left: 50%; transform: translateX(-50%);
  background: var(--orange); color: #fff;
  padding: 4px 14px; border-radius: 20px; font-size: .75rem; font-weight: 700;
  white-space: nowrap;
}
.pricing-name { font-size: .85rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: .08em; margin-bottom: 12px; opacity: .8; }
.pricing-price { margin-bottom: 20px; }
.price-free { font-size: 1.8rem; font-weight: 900; color: var(--accent); }
.pricing-card.featured .price-free { color: #a7f3d0; }
.price-currency { font-size: 1.1rem; font-weight: 700; vertical-align: top; margin-top: 6px; display: inline-block; }
.price-amount  { font-size: 2rem; font-weight: 900; }
.price-period  { font-size: .82rem; opacity: .7; }
.btn-pricing {
  display: block; width: 100%; padding: 10px; border-radius: 8px;
  background: var(--light); color: var(--primary); font-weight: 700;
  text-decoration: none; font-size: .88rem; transition: all .2s;
  border: 2px solid var(--primary);
}
.btn-pricing:hover { background: var(--primary); color: #fff; }
.btn-pricing-featured {
  background: rgba(255,255,255,.2); color: #fff; border-color: rgba(255,255,255,.4);
}
.btn-pricing-featured:hover { background: rgba(255,255,255,.35); color: #fff; }

.features-table-wrap {
  max-width: 1000px; margin: 0 auto;
  overflow-x: auto; border-radius: 16px;
  box-shadow: var(--shadow-lg); border: 1px solid #e2e8f0;
}
.features-table { width: 100%; border-collapse: collapse; background: #fff; }
.features-table thead th {
  background: var(--dark2); color: #fff;
  padding: 14px 16px; font-size: .85rem; font-weight: 700;
  text-align: center;
}
.feat-col-name { text-align: left !important; width: 35%; }
.feat-col-plan  { min-width: 110px; }
.feat-group-header td {
  background: var(--primary); color: #fff;
  padding: 10px 16px; font-weight: 700; font-size: .82rem;
  text-transform: uppercase; letter-spacing: .06em;
}
.feat-row { border-bottom: 1px solid #f1f5f9; }
.feat-row:hover { background: #f8fafc; }
.feat-name { padding: 12px 16px; font-size: .88rem; color: var(--dark); }
.feat-val  {
  padding: 12px 16px; text-align: center;
  font-size: .9rem; font-weight: 600; color: var(--gray);
}
.feat-row td.feat-val:nth-child(2) { background: rgba(16,185,129,.04); }
.feat-row td.feat-val:nth-child(4) { background: rgba(37,99,235,.04); }
.feat-row td.feat-val:nth-child(5) { background: rgba(139,92,246,.06); }

/* ════════════════════════════════════════════════════
   NOTAS IMPORTANTES
════════════════════════════════════════════════════ */
.section-about { padding: 64px 24px; background: #fff; }
.about-inner {
  max-width: 780px; margin: 0 auto;
  background: #f8fafc; border-radius: 16px; padding: 40px;
  border-left: 4px solid var(--primary);
}
.about-icon { font-size: 2rem; color: var(--primary); margin-bottom: 12px; }
.about-title { font-size: 1.4rem; font-weight: 800; margin-bottom: 20px; }
.about-list { list-style: none; padding: 0; }
.about-list li {
  display: flex; align-items: flex-start; gap: 4px;
  padding: 8px 0; border-bottom: 1px solid #e2e8f0;
  font-size: .9rem; color: var(--gray); line-height: 1.6;
}
.about-list li:last-child { border-bottom: none; }
.about-list .bi-dot { color: var(--primary); flex-shrink: 0; margin-top: -2px; }

/* ════════════════════════════════════════════════════
   PASARELA DE PAGO
════════════════════════════════════════════════════ */
.section-payment { padding: 80px 24px; background: var(--light); }
.section-payment .section-header { max-width: 1200px; margin: 0 auto 40px; }
.payment-methods {
  max-width: 900px; margin: 0 auto;
  display: flex; flex-wrap: wrap; gap: 16px; justify-content: center;
}
.payment-card {
  background: #fff; border-radius: 14px; padding: 24px 32px;
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  border: 1px solid #e2e8f0; box-shadow: var(--shadow);
  min-width: 160px; position: relative;
  font-size: .9rem; font-weight: 600; color: var(--gray);
  transition: all .2s;
}
.payment-card i { font-size: 2rem; color: var(--primary); }
.payment-card.coming-soon { opacity: .75; cursor: not-allowed; }
.soon-tag {
  position: absolute; top: -10px; right: -6px;
  background: var(--orange); color: #fff;
  padding: 2px 10px; border-radius: 20px; font-size: .7rem; font-weight: 700;
}

/* ════════════════════════════════════════════════════
   CONTACTO
════════════════════════════════════════════════════ */
.section-contacto {
  padding: 96px 24px;
  background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
}
.contact-grid {
  max-width: 1100px; margin: 0 auto;
  display: grid; grid-template-columns: 1fr 1.4fr; gap: 60px; align-items: start;
}
.contact-info { color: #fff; }
.contact-title { font-size: 1.9rem; font-weight: 800; margin: 16px 0 10px; }
.contact-subtitle { color: #94a3b8; margin-bottom: 32px; line-height: 1.7; }
.contact-details { display: flex; flex-direction: column; gap: 16px; }
.contact-item {
  display: flex; align-items: center; gap: 12px;
  color: #cbd5e1; font-size: .95rem;
}
.contact-item i { color: #93c5fd; font-size: 1.2rem; flex-shrink: 0; }

.contact-form-wrap {
  background: rgba(255,255,255,.05);
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 20px; padding: 36px;
  backdrop-filter: blur(10px);
}
.contact-form { display: flex; flex-direction: column; gap: 18px; }
.form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { color: #cbd5e1; font-size: .85rem; font-weight: 600; }
.form-ctrl {
  background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.15);
  color: #fff; border-radius: 8px; padding: 10px 14px; font-size: .9rem;
  transition: border-color .2s;
}
.form-ctrl::placeholder { color: #64748b; }
.form-ctrl:focus { outline: none; border-color: #93c5fd; background: rgba(255,255,255,.12); }
.form-ctrl.invalid { border-color: #f87171; }
.form-textarea { resize: vertical; min-height: 120px; }
.form-error { color: #f87171; font-size: .78rem; }
.btn-contact-submit {
  background: var(--primary); color: #fff; border: none;
  padding: 14px; border-radius: 10px; font-weight: 700; font-size: 1rem;
  cursor: pointer; transition: all .2s; display: flex; align-items: center; justify-content: center; gap: 8px;
}
.btn-contact-submit:hover:not(:disabled) { background: var(--primary-dark); transform: translateY(-1px); }
.btn-contact-submit:disabled { opacity: .6; cursor: not-allowed; }
.contact-success {
  background: rgba(16,185,129,.2); border: 1px solid rgba(16,185,129,.4);
  color: #6ee7b7; padding: 12px 16px; border-radius: 8px; font-size: .9rem;
}
.contact-error {
  background: rgba(239,68,68,.15); border: 1px solid rgba(239,68,68,.3);
  color: #fca5a5; padding: 12px 16px; border-radius: 8px; font-size: .9rem;
}

/* ════════════════════════════════════════════════════
   FOOTER
════════════════════════════════════════════════════ */
.landing-footer { background: var(--dark); color: #fff; padding: 60px 24px 24px; }
.footer-top {
  max-width: 1100px; margin: 0 auto;
  display: flex; gap: 60px; justify-content: space-between;
  flex-wrap: wrap; padding-bottom: 40px;
  border-bottom: 1px solid rgba(255,255,255,.1);
}
.footer-brand .nav-brand { display: inline-block; margin-bottom: 10px; }
.footer-tagline { color: #64748b; font-size: .88rem; max-width: 260px; }
.footer-links { display: flex; gap: 48px; flex-wrap: wrap; }
.footer-col { display: flex; flex-direction: column; gap: 10px; }
.footer-col h5 { color: #94a3b8; font-size: .78rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: .08em; margin-bottom: 4px; }
.footer-col a { color: #64748b; text-decoration: none; font-size: .88rem; transition: color .2s; }
.footer-col a:hover { color: #fff; }
.footer-bottom {
  max-width: 1100px; margin: 24px auto 0;
  display: flex; align-items: center; justify-content: space-between;
  flex-wrap: wrap; gap: 12px; color: #64748b; font-size: .82rem;
}
.footer-socials { display: flex; gap: 16px; }
.footer-socials a { color: #64748b; font-size: 1.2rem; transition: color .2s; }
.footer-socials a:hover { color: #fff; }

/* ════════════════════════════════════════════════════
   RESPONSIVE
════════════════════════════════════════════════════ */
@media (max-width: 1024px) {
  .hero-devices { display: none; }
  .hero-section { justify-content: center; text-align: center; padding: 100px 24px 60px; }
  .hero-actions { justify-content: center; }
  .hero-stats { justify-content: center; }
  .pricing-cards { grid-template-columns: repeat(2, 1fr); }
  .pricing-card.featured { transform: scale(1); }
}

@media (max-width: 768px) {
  .nav-links, .nav-actions { display: none; }
  .nav-hamburger { display: block; }
  .profile-card { flex-direction: column; text-align: center; }
  .profile-img-placeholder, .profile-img { width: 100%; height: 180px; }
  .slider-arrow { display: none; }
  .multidevice-strip { flex-direction: column; text-align: center; }
  .contact-grid { grid-template-columns: 1fr; }
  .form-row-2 { grid-template-columns: 1fr; }
  .pricing-cards { grid-template-columns: 1fr 1fr; }
  .devices-row { display: none; }
}

@media (max-width: 480px) {
  .pricing-cards { grid-template-columns: 1fr; }
  .hero-title { font-size: 1.8rem; }
  .payment-methods { flex-direction: column; align-items: center; }
}
</style>
