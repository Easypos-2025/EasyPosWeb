<template>
  <div class="landing-root">

    <!-- ══════════════════════════════════════════════
         NAVBAR
    ══════════════════════════════════════════════ -->
    <nav class="landing-nav">
      <div class="nav-inner">
        <a class="nav-brand" href="/">
          <span class="brand-easy">Easy</span><span class="brand-pos">Pos</span><span class="brand-web">Web</span>
        </a>
        <div class="nav-links">
          <a href="#info"     class="nav-link-item">Características</a>
          <a href="#planes"   class="nav-link-item">Planes</a>
          <a href="#contacto" class="nav-link-item">Contacto</a>
        </div>
        <div class="nav-actions">
          <a href="/login"    class="btn-nav-outline">Iniciar Sesión</a>
          <a href="/register" class="btn-nav-solid">Empezar Gratis</a>
        </div>
        <button class="nav-hamburger" @click="mobileOpen = !mobileOpen">
          <i :class="mobileOpen ? 'bi bi-x-lg' : 'bi bi-list'"></i>
        </button>
      </div>
      <div class="nav-mobile" :class="{ open: mobileOpen }">
        <a href="#info"     @click="mobileOpen=false">Características</a>
        <a href="#planes"   @click="mobileOpen=false">Planes</a>
        <a href="#contacto" @click="mobileOpen=false">Contacto</a>
        <hr>
        <a href="/login"    class="btn-nav-outline w-100 text-center mb-2">Iniciar Sesión</a>
        <a href="/register" class="btn-nav-solid w-100 text-center">Empezar Gratis</a>
      </div>
    </nav>

    <!-- ══════════════════════════════════════════════
         BANDA "PROPUESTA PERSONALIZADA"
    ══════════════════════════════════════════════ -->
    <div v-if="profile" class="proposal-strip" :style="{ '--pcolor': profile.color_accent || '#2563eb' }">
      <div class="proposal-strip-inner">
        <div class="proposal-left">
          <i class="bi bi-file-earmark-person-fill me-2"></i>
          <strong>Propuesta personalizada</strong>
          <span class="sep">·</span>
          <span>Solución para <strong>{{ profile.name }}</strong></span>
        </div>
        <div class="proposal-right">
          <i class="bi bi-share-fill me-1"></i>
          <button class="btn-copy-link" @click="copyLink">
            {{ copied ? '¡Enlace copiado!' : 'Copiar enlace' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════
         SLIDE HERO — PERFIL ÚNICO (FULL SCREEN)
    ══════════════════════════════════════════════ -->
    <section class="section-hero-profile" :style="heroStyle">
      <div class="hero-overlay"></div>

      <!-- Cargando -->
      <div v-if="loading" class="hero-loading">
        <div class="spinner"></div>
        <p>Cargando propuesta...</p>
      </div>

      <!-- No encontrado -->
      <div v-else-if="!profile" class="hero-not-found">
        <i class="bi bi-exclamation-triangle-fill"></i>
        <h2>Perfil no encontrado</h2>
        <p>El perfil de negocio solicitado no existe o no está disponible.</p>
        <a href="/" class="btn-slide-cta">Ver todos los perfiles</a>
      </div>

      <!-- Perfil encontrado -->
      <div v-else class="hero-profile-content">
        <div class="slide-tag">
          <i :class="`bi ${profile.icon || 'bi-building'}`"></i>
          <span>Perfil de Negocio</span>
        </div>
        <h1 class="hero-profile-name">{{ profile.name }}</h1>
        <p class="hero-profile-desc">
          {{ profile.landing_description || profile.description || 'Solución integral para tu negocio.' }}
        </p>
        <div class="hero-profile-actions">
          <a href="/register" class="btn-slide-cta">
            <i class="bi bi-rocket-takeoff-fill me-2"></i>Probar Gratis
          </a>
          <a href="#planes" class="btn-slide-outline">
            Ver planes <i class="bi bi-arrow-down ms-1"></i>
          </a>
        </div>
      </div>

      <!-- Scroll hint -->
      <div v-if="profile" class="slide-scroll-hint">
        <i class="bi bi-chevron-down"></i>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════
         SECCIÓN INFO / CARACTERÍSTICAS  id="info"
    ══════════════════════════════════════════════ -->
    <section id="info" class="section-info">
      <div class="info-inner">

        <!-- Presentación del perfil -->
        <div v-if="profile" class="profile-detail-card" :style="{ '--accent': profile.color_accent || 'var(--primary)' }">
          <div class="pdc-icon">
            <i :class="`bi ${profile.icon || 'bi-building'}`"></i>
          </div>
          <div class="pdc-body">
            <h2>¿Qué es el perfil <em>{{ profile.name }}</em>?</h2>
            <p>
              EasyPosWeb adapta todas sus funcionalidades al modelo de negocio de <strong>{{ profile.name }}</strong>,
              ofreciendo una experiencia pensada para las necesidades específicas de este sector.
            </p>
          </div>
        </div>

        <!-- Features -->
        <div class="section-header text-center">
          <span class="section-badge blue">Funcionalidades incluidas</span>
          <h2 class="section-title">{{ sections.features?.title || 'Todo lo que necesitas' }}</h2>
          <p class="section-subtitle">{{ sections.features?.subtitle }}</p>
        </div>
        <div class="features-grid">
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
            <h3>{{ sections.multidevice?.title || 'Accede desde cualquier dispositivo' }}</h3>
            <p>{{ sections.multidevice?.subtitle }}</p>
            <ul class="strip-list">
              <li v-for="item in multideviceItems" :key="item">
                <i class="bi bi-check-circle-fill me-2"></i>{{ item }}
              </li>
            </ul>
            <a href="/register" class="btn-strip-cta">
              Registrarse Ahora <i class="bi bi-arrow-right ms-2"></i>
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

        <!-- Escritorio strip -->
        <div class="desktop-strip">
          <div class="desktop-strip-icon"><i class="bi bi-laptop-fill"></i></div>
          <div class="desktop-strip-body">
            <h3>También disponible como aplicación de escritorio</h3>
            <p>EasyPosWeb cuenta con versión instalable en PC — funciona sin internet y sincroniza cuando recupera conexión. Ideal para negocios con conectividad limitada.</p>
          </div>
          <a href="#contacto" class="btn-desktop-strip">
            <i class="bi bi-envelope-fill me-2"></i>Solicitar info
          </a>
        </div>

      </div>
    </section>

    <!-- ══════════════════════════════════════════════
         PLANES
    ══════════════════════════════════════════════ -->
    <section id="planes" class="section-planes">
      <div class="section-header text-center">
        <span class="section-badge green">Precios</span>
        <h2 class="section-title">Elige el plan que se adapta a tu negocio</h2>
        <p class="section-subtitle">Comienza gratis. Escala cuando lo necesites.</p>
      </div>

      <!-- Planes web/cloud -->
      <div class="plans-group-label">
        <i class="bi bi-cloud-fill me-2"></i>Planes Web / Cloud
      </div>
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

      <!-- Tabla comparativa -->
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

      <!-- Planes Escritorio y Mixto -->
      <div class="desktop-plans-wrap">
        <div class="desktop-plans-header">
          <div class="plans-group-label desktop-variant">
            <i class="bi bi-laptop-fill me-2"></i>Planes con versión escritorio
          </div>
          <p>¿Tu negocio necesita operar sin internet? Tenemos planes específicos para ti.</p>
        </div>
        <div class="desktop-plan-cards">
          <div class="desktop-plan-card">
            <div class="dplan-icon"><i class="bi bi-laptop"></i></div>
            <div class="dplan-name">Plan Escritorio</div>
            <div class="dplan-tag">Solo app instalada</div>
            <p class="dplan-desc">Aplicación instalada en tu PC. Opera offline y sincroniza al conectar. Ideal para negocios con internet inestable.</p>
            <ul class="dplan-features">
              <li><i class="bi bi-check-circle-fill"></i> Acceso sin internet</li>
              <li><i class="bi bi-check-circle-fill"></i> Instalación en Windows</li>
              <li><i class="bi bi-check-circle-fill"></i> Sincronización automática</li>
              <li><i class="bi bi-check-circle-fill"></i> Soporte técnico incluido</li>
            </ul>
            <a href="#contacto" class="btn-dplan">
              Consultar precio <i class="bi bi-arrow-right ms-1"></i>
            </a>
          </div>
          <div class="desktop-plan-card featured">
            <div class="dplan-badge"><i class="bi bi-star-fill me-1"></i>Recomendado</div>
            <div class="dplan-icon mixed">
              <i class="bi bi-laptop-fill"></i>
              <i class="bi bi-plus-lg mx-1 plus-icon"></i>
              <i class="bi bi-cloud-fill"></i>
            </div>
            <div class="dplan-name">Plan Mixto</div>
            <div class="dplan-tag featured-tag">Escritorio + Web</div>
            <p class="dplan-desc">Lo mejor de ambos mundos: app de escritorio + acceso web desde cualquier dispositivo con sincronización en tiempo real.</p>
            <ul class="dplan-features">
              <li><i class="bi bi-check-circle-fill"></i> App escritorio + acceso web</li>
              <li><i class="bi bi-check-circle-fill"></i> Múltiples dispositivos</li>
              <li><i class="bi bi-check-circle-fill"></i> Sincronización en tiempo real</li>
              <li><i class="bi bi-check-circle-fill"></i> Soporte prioritario</li>
            </ul>
            <a href="#contacto" class="btn-dplan featured">
              Consultar precio <i class="bi bi-arrow-right ms-1"></i>
            </a>
          </div>
        </div>
      </div>
    </section>

    <!-- ══════════════════════════════════════════════
         CONTACTO
    ══════════════════════════════════════════════ -->
    <section id="contacto" class="section-contacto">
      <div class="contact-grid">
        <div class="contact-info">
          <span class="section-badge white">Contáctanos</span>
          <h2 class="contact-title">{{ sections.contact?.title || 'Hablemos de tu negocio' }}</h2>
          <p class="contact-subtitle">{{ sections.contact?.subtitle || 'Cuéntanos sobre tu empresa y te ayudamos a encontrar el plan ideal.' }}</p>
          <div class="contact-details">
            <div class="contact-item">
              <i class="bi bi-envelope-fill"></i><span>easypos.co@gmail.com</span>
            </div>
            <div class="contact-item">
              <i class="bi bi-globe"></i><span>easyposweb.com</span>
            </div>
            <div class="contact-item">
              <i class="bi bi-clock-fill"></i><span>Respuesta en menos de 24 horas</span>
            </div>
          </div>
          <!-- Referencia al perfil -->
          <div v-if="profile" class="contact-profile-ref">
            <i :class="`bi ${profile.icon || 'bi-building'} me-2`"></i>
            Consulta relacionada con perfil: <strong>{{ profile.name }}</strong>
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
              <i class="bi bi-check-circle-fill me-2"></i>Mensaje enviado. Te contactaremos pronto.
            </div>
            <div v-if="contactError" class="contact-error">
              <i class="bi bi-exclamation-circle-fill me-2"></i>{{ contactError }}
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
          <a class="nav-brand" href="/">
            <span class="brand-easy">Easy</span><span class="brand-pos">Pos</span><span class="brand-web">Web</span>
          </a>
          <p class="footer-tagline">Tu negocio, en línea. Sin complicaciones.</p>
          <a href="/" class="footer-back-link">
            <i class="bi bi-arrow-left me-1"></i>Ver todos los perfiles
          </a>
        </div>
        <div class="footer-links">
          <div class="footer-col">
            <h5>Propuesta</h5>
            <a href="#info">Características</a>
            <a href="#planes">Planes</a>
            <a href="#contacto">Contacto</a>
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
import { ref, reactive, computed, onMounted } from "vue"
import { useRoute } from "vue-router"

const API = import.meta.env.VITE_API_URL || "http://localhost:8000"

const FEATURE_ICONS = [
  "bi-receipt-cutoff", "bi-cash-coin", "bi-people-fill", "bi-credit-card-2-front",
  "bi-printer-fill", "bi-bag-plus-fill", "bi-wallet2", "bi-box-seam",
  "bi-graph-up-arrow", "bi-file-earmark-excel", "bi-calculator", "bi-clipboard2-data",
  "bi-person-lock", "bi-tags-fill", "bi-bar-chart-line", "bi-pie-chart-fill",
  "bi-percent"
]

const SLIDE_GRADIENTS = [
  "linear-gradient(145deg, #0f2460 0%, #1a3a8a 50%, #1565c0 100%)",
  "linear-gradient(145deg, #0a3d22 0%, #1b6b3a 50%, #22874a 100%)",
  "linear-gradient(145deg, #3b0764 0%, #5b21b6 50%, #7c3aed 100%)",
  "linear-gradient(145deg, #7c1d0a 0%, #b91c1c 50%, #dc2626 100%)",
  "linear-gradient(145deg, #7c2d12 0%, #c2410c 50%, #ea580c 100%)",
  "linear-gradient(145deg, #042f2e 0%, #065f46 50%, #059669 100%)",
]

export default {
  name: "LandingProfileView",

  setup() {
    const route  = useRoute()
    const profile   = ref(null)
    const sections  = reactive({})
    const planData  = reactive({ plans: [], feature_groups: [] })
    const loading   = ref(true)
    const copied    = ref(false)
    const mobileOpen    = ref(false)
    const submitting    = ref(false)
    const contactSuccess = ref(false)
    const contactError  = ref("")

    const form       = reactive({ name: "", email: "", phone: "", company: "", message: "" })
    const formErrors = reactive({ name: "", email: "", message: "" })
    const currentYear = new Date().getFullYear()

    // ── Fondo del hero según el perfil ────────────────────────
    const heroStyle = computed(() => {
      if (!profile.value) return { background: "#0f172a" }
      if (profile.value.image_url) {
        return { backgroundImage: `url(${profile.value.image_url})` }
      }
      const id = profile.value.id ?? 0
      return { background: SLIDE_GRADIENTS[id % SLIDE_GRADIENTS.length] }
    })

    // ── Computed: parsear body_text ────────────────────────────
    const featureItems = computed(() =>
      (sections.features?.body_text || "").split("|").map(s => s.trim()).filter(Boolean)
    )
    const multideviceItems = computed(() =>
      (sections.multidevice?.body_text || "").split("|").map(s => s.trim()).filter(Boolean)
    )
    const featureIcons = computed(() => FEATURE_ICONS)

    // ── Copiar enlace ──────────────────────────────────────────
    function copyLink() {
      navigator.clipboard.writeText(window.location.href).then(() => {
        copied.value = true
        setTimeout(() => { copied.value = false }, 2500)
      })
    }

    // ── Helpers ────────────────────────────────────────────────
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
      if (!form.name.trim())    { formErrors.name    = "El nombre es obligatorio"; ok = false }
      if (!form.email.trim())   { formErrors.email   = "El email es obligatorio";  ok = false }
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
      const obs = new IntersectionObserver(
        entries => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add("revealed") }),
        { threshold: 0.1 }
      )
      cards.forEach(c => obs.observe(c))
    }

    // ── Carga de datos — perfil primero, resto en background ────
    async function loadData() {
      loading.value = true
      const profileId = route.params.id
      const NC = { cache: "no-store" }

      // FASE 1: solo perfiles → muestra el hero de inmediato
      try {
        const profData = await fetch(`${API}/landing/profiles`, NC).then(r => r.json())
        profile.value = profData.find(p => String(p.id) === String(profileId)) || null
      } catch (e) {
        console.error("Error cargando perfil:", e)
      } finally {
        loading.value = false
      }

      // FASE 2: secciones y planes en background
      try {
        const [secRes, planRes] = await Promise.all([
          fetch(`${API}/landing/sections`, NC),
          fetch(`${API}/landing/plans`,    NC),
        ])
        const [secData, pData] = await Promise.all([secRes.json(), planRes.json()])
        secData.forEach(s => { sections[s.section_key] = s })
        planData.plans          = pData.plans          || []
        planData.feature_groups = pData.feature_groups || []
      } catch (e) {
        console.error("Error cargando secciones/planes:", e)
      }
    }

    onMounted(async () => {
      await loadData()
      setTimeout(initReveal, 300)
    })

    return {
      profile, sections, planData, loading, copied,
      mobileOpen, submitting, contactSuccess, contactError,
      currentYear, heroStyle,
      featureItems, multideviceItems, featureIcons,
      form, formErrors,
      copyLink, formatPrice, renderVal, submitContact,
    }
  }
}
</script>

<style scoped>
/* ════════════════════════════════════════════════════
   BASE
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
.nav-link-item { color: var(--gray); text-decoration: none; font-size: .9rem; font-weight: 500; transition: color .2s; }
.nav-link-item:hover { color: var(--primary); }
.nav-actions { display: flex; gap: 10px; align-items: center; }
.btn-nav-outline {
  padding: 8px 18px; border: 1.5px solid var(--primary); color: var(--primary);
  border-radius: 8px; font-size: .9rem; font-weight: 600; text-decoration: none; transition: all .2s;
}
.btn-nav-outline:hover { background: var(--primary); color: #fff; }
.btn-nav-solid {
  padding: 8px 18px; background: var(--primary); color: #fff;
  border-radius: 8px; font-size: .9rem; font-weight: 600; text-decoration: none; transition: all .2s;
}
.btn-nav-solid:hover { background: var(--primary-dark); }
.nav-hamburger { display: none; background: none; border: none; font-size: 1.5rem; color: var(--dark); cursor: pointer; }
.nav-mobile { display: none; flex-direction: column; gap: 12px; padding: 16px 24px; border-top: 1px solid #eee; }
.nav-mobile a { color: var(--dark); text-decoration: none; font-size: .95rem; }
.nav-mobile.open { display: flex; }

/* ════════════════════════════════════════════════════
   BANDA PROPUESTA PERSONALIZADA
════════════════════════════════════════════════════ */
.proposal-strip {
  position: fixed;
  top: 68px; left: 0; right: 0;
  z-index: 999;
  background: var(--pcolor, #2563eb);
  color: #fff;
  font-size: .82rem;
  font-weight: 600;
}
.proposal-strip-inner {
  max-width: 1200px; margin: 0 auto;
  padding: 8px 24px;
  display: flex; align-items: center; justify-content: space-between;
  gap: 16px;
}
.proposal-left { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.proposal-left .sep { opacity: .5; margin: 0 2px; }
.proposal-right { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.btn-copy-link {
  background: rgba(255,255,255,.2); border: 1px solid rgba(255,255,255,.35);
  color: #fff; padding: 3px 12px; border-radius: 6px;
  font-size: .78rem; font-weight: 700; cursor: pointer; transition: all .2s;
}
.btn-copy-link:hover { background: rgba(255,255,255,.35); }

/* ════════════════════════════════════════════════════
   HERO PERFIL — FULL SCREEN
════════════════════════════════════════════════════ */
.section-hero-profile {
  height: 100vh;
  padding-top: calc(68px + 36px); /* navbar + banda */
  position: relative;
  overflow: hidden;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}
.hero-overlay {
  position: absolute; inset: 0;
  background: linear-gradient(
    to bottom,
    rgba(0,0,0,.05) 0%,
    rgba(0,0,0,.15) 30%,
    rgba(0,0,0,.60) 65%,
    rgba(0,0,0,.90) 100%
  );
}
.hero-loading, .hero-not-found {
  position: absolute; inset: 0;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  color: #fff; gap: 16px; z-index: 2;
}
.hero-not-found i { font-size: 3rem; color: #f87171; }
.hero-not-found h2 { font-size: 2rem; font-weight: 800; }
.hero-not-found p { color: #94a3b8; font-size: 1rem; }
.spinner {
  width: 40px; height: 40px;
  border: 3px solid rgba(255,255,255,.2);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin .8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.hero-profile-content {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  padding: 0 8% 90px;
  color: #fff; max-width: 860px; z-index: 2;
}
.slide-tag {
  display: inline-flex; align-items: center; gap: 10px;
  background: rgba(255,255,255,.14); border: 1px solid rgba(255,255,255,.28);
  backdrop-filter: blur(8px); color: rgba(255,255,255,.95);
  padding: 8px 18px; border-radius: 24px;
  font-size: .82rem; font-weight: 700; text-transform: uppercase; letter-spacing: .08em;
  margin-bottom: 20px;
}
.hero-profile-name {
  font-size: clamp(2.4rem, 6vw, 4.8rem); font-weight: 900;
  margin: 0 0 18px; line-height: 1.06;
  text-shadow: 0 2px 24px rgba(0,0,0,.5); letter-spacing: -.02em;
}
.hero-profile-desc {
  font-size: clamp(1rem, 1.5vw, 1.25rem); color: rgba(255,255,255,.82);
  margin-bottom: 32px; max-width: 600px; line-height: 1.72;
  text-shadow: 0 1px 10px rgba(0,0,0,.4);
}
.hero-profile-actions { display: flex; gap: 14px; flex-wrap: wrap; }
.btn-slide-cta {
  display: inline-flex; align-items: center;
  background: var(--primary); color: #fff;
  padding: 14px 30px; border-radius: 10px; font-weight: 700; font-size: 1rem;
  text-decoration: none; transition: all .25s;
  box-shadow: 0 4px 24px rgba(37,99,235,.5);
}
.btn-slide-cta:hover { background: var(--primary-dark); transform: translateY(-2px); color: #fff; }
.btn-slide-outline {
  display: inline-flex; align-items: center;
  border: 1.5px solid rgba(255,255,255,.4); color: rgba(255,255,255,.9);
  padding: 14px 28px; border-radius: 10px; font-weight: 600; font-size: 1rem;
  text-decoration: none; transition: all .25s; backdrop-filter: blur(4px);
}
.btn-slide-outline:hover { background: rgba(255,255,255,.12); color: #fff; }
.slide-scroll-hint {
  position: absolute; bottom: 30px; left: 50%;
  transform: translateX(-50%);
  color: rgba(255,255,255,.55); font-size: 1.4rem;
  animation: bounceDown 2.2s ease-in-out infinite; z-index: 10; pointer-events: none;
}
@keyframes bounceDown {
  0%,100% { transform: translateX(-50%) translateY(0); opacity: .55; }
  50%      { transform: translateX(-50%) translateY(9px); opacity: .95; }
}

/* ════════════════════════════════════════════════════
   SECCIÓN INFO
════════════════════════════════════════════════════ */
.section-info { padding: 80px 24px 60px; background: var(--white); }
.info-inner { max-width: 1180px; margin: 0 auto; }

/* Tarjeta presentación del perfil */
.profile-detail-card {
  display: flex; gap: 28px; align-items: flex-start;
  background: var(--light); border-radius: 16px; padding: 32px;
  border-left: 5px solid var(--accent, var(--primary));
  margin-bottom: 56px; box-shadow: var(--shadow);
}
.pdc-icon {
  width: 60px; height: 60px; border-radius: 14px;
  background: linear-gradient(135deg, var(--accent, var(--primary)), rgba(37,99,235,.4));
  display: flex; align-items: center; justify-content: center;
  font-size: 1.8rem; color: #fff; flex-shrink: 0;
}
.pdc-body h2 { font-size: 1.4rem; font-weight: 800; margin-bottom: 8px; }
.pdc-body h2 em { font-style: normal; color: var(--primary); }
.pdc-body p { color: var(--gray); line-height: 1.7; margin: 0; }

/* Sección header */
.section-header   { margin-bottom: 40px; }
.section-badge {
  display: inline-block; padding: 4px 14px; border-radius: 20px; font-size: .78rem;
  font-weight: 700; text-transform: uppercase; letter-spacing: .08em;
  background: rgba(37,99,235,.1); color: var(--primary); margin-bottom: 12px;
}
.section-badge.blue   { background: rgba(37,99,235,.1); color: var(--primary); }
.section-badge.green  { background: rgba(16,185,129,.1); color: #059669; }
.section-badge.white  { background: rgba(255,255,255,.15); color: #fff; }
.section-title    { font-size: clamp(1.5rem,2.5vw,2rem); font-weight: 800; margin-bottom: 12px; }
.section-subtitle { color: var(--gray); font-size: 1rem; max-width: 620px; margin: 0 auto; }

/* Features grid */
.features-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: 16px; margin-bottom: 56px;
}
.feature-card {
  background: #fff; border: 1px solid #e2e8f0; border-radius: var(--radius);
  padding: 20px; display: flex; align-items: flex-start; gap: 14px;
  box-shadow: var(--shadow); cursor: default;
  opacity: 0; transform: translateY(20px);
  transition: opacity .5s var(--delay,0s), transform .5s var(--delay,0s), box-shadow .2s;
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
  gap: 48px; align-items: center; color: #fff; margin-bottom: 28px;
}
.strip-left { flex: 1; }
.strip-left h3 { font-size: 1.6rem; font-weight: 800; margin-bottom: 10px; }
.strip-left p  { color: #94a3b8; margin-bottom: 20px; }
.strip-list { list-style: none; padding: 0; margin-bottom: 24px; }
.strip-list li { display: flex; align-items: center; gap: 6px; color: #cbd5e1; font-size: .9rem; margin-bottom: 8px; }
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

/* Desktop strip */
.desktop-strip {
  display: flex; align-items: center; gap: 24px;
  background: linear-gradient(135deg, #1e1b4b, #312e81);
  border-radius: 16px; padding: 28px 32px; color: #fff;
}
.desktop-strip-icon { font-size: 2.4rem; color: #a78bfa; flex-shrink: 0; }
.desktop-strip-body { flex: 1; }
.desktop-strip-body h3 { font-size: 1.15rem; font-weight: 800; margin-bottom: 6px; }
.desktop-strip-body p  { color: #a5b4fc; font-size: .9rem; margin: 0; line-height: 1.6; }
.btn-desktop-strip {
  display: inline-flex; align-items: center;
  background: #7c3aed; color: #fff; flex-shrink: 0;
  padding: 10px 20px; border-radius: 8px; font-weight: 700; font-size: .88rem;
  text-decoration: none; transition: all .2s; white-space: nowrap;
}
.btn-desktop-strip:hover { background: #6d28d9; color: #fff; }

/* ════════════════════════════════════════════════════
   PLANES
════════════════════════════════════════════════════ */
.section-planes { padding: 80px 24px; background: var(--light); }
.section-planes .section-header { max-width: 1000px; margin: 0 auto 40px; }

.plans-group-label {
  max-width: 900px; margin: 0 auto 16px;
  font-size: .78rem; font-weight: 800; text-transform: uppercase;
  letter-spacing: .1em; color: var(--gray);
  display: flex; align-items: center;
}
.plans-group-label.desktop-variant { color: #7c3aed; margin-top: 8px; margin-bottom: 10px; }

.pricing-cards {
  max-width: 900px; margin: 0 auto 48px;
  display: grid; grid-template-columns: repeat(4,1fr); gap: 16px;
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
  padding: 4px 14px; border-radius: 20px; font-size: .75rem; font-weight: 700; white-space: nowrap;
}
.pricing-name { font-size: .85rem; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 12px; opacity: .8; }
.pricing-price { margin-bottom: 20px; }
.price-free { font-size: 1.8rem; font-weight: 900; color: var(--accent); }
.pricing-card.featured .price-free { color: #a7f3d0; }
.price-currency { font-size: 1.1rem; font-weight: 700; vertical-align: top; margin-top: 6px; display: inline-block; }
.price-amount { font-size: 2rem; font-weight: 900; }
.price-period { font-size: .82rem; opacity: .7; }
.btn-pricing {
  display: block; width: 100%; padding: 10px; border-radius: 8px;
  background: var(--light); color: var(--primary); font-weight: 700;
  text-decoration: none; font-size: .88rem; transition: all .2s;
  border: 2px solid var(--primary);
}
.btn-pricing:hover { background: var(--primary); color: #fff; }
.btn-pricing-featured { background: rgba(255,255,255,.2); color: #fff; border-color: rgba(255,255,255,.4); }
.btn-pricing-featured:hover { background: rgba(255,255,255,.35); color: #fff; }

.features-table-wrap {
  max-width: 1000px; margin: 0 auto 40px;
  overflow-x: auto; border-radius: 16px;
  box-shadow: var(--shadow-lg); border: 1px solid #e2e8f0;
}
.features-table { width: 100%; border-collapse: collapse; background: #fff; }
.features-table thead th {
  background: var(--dark2); color: #fff;
  padding: 14px 16px; font-size: .85rem; font-weight: 700; text-align: center;
}
.feat-col-name { text-align: left !important; width: 35%; }
.feat-col-plan  { min-width: 110px; }
.feat-group-header td { background: var(--primary); color: #fff; padding: 10px 16px; font-weight: 700; font-size: .82rem; text-transform: uppercase; letter-spacing: .06em; }
.feat-row { border-bottom: 1px solid #f1f5f9; }
.feat-row:hover { background: #f8fafc; }
.feat-name { padding: 12px 16px; font-size: .88rem; color: var(--dark); }
.feat-val  { padding: 12px 16px; text-align: center; font-size: .9rem; font-weight: 600; color: var(--gray); }

/* Planes escritorio/mixto */
.desktop-plans-wrap {
  max-width: 1000px; margin: 0 auto;
  background: #fff; border-radius: 20px;
  border: 2px dashed #e2e8f0; padding: 32px 32px 36px;
}
.desktop-plans-header { margin-bottom: 24px; }
.desktop-plans-header p { color: var(--gray); font-size: .92rem; margin: 6px 0 0; }
.desktop-plan-cards { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.desktop-plan-card {
  background: var(--light); border-radius: 16px; padding: 28px;
  border: 1px solid #e2e8f0; position: relative; transition: all .25s;
}
.desktop-plan-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-lg); }
.desktop-plan-card.featured { background: var(--dark2); border-color: var(--dark2); color: #fff; }
.dplan-badge {
  position: absolute; top: -13px; left: 50%; transform: translateX(-50%);
  background: linear-gradient(135deg, #7c3aed, #5b21b6);
  color: #fff; padding: 4px 16px; border-radius: 20px; font-size: .72rem; font-weight: 700; white-space: nowrap;
}
.dplan-icon { font-size: 2rem; color: var(--primary); margin-bottom: 12px; display: flex; align-items: center; }
.dplan-icon.mixed { color: #a78bfa; }
.plus-icon { font-size: 1.2rem; color: #64748b; }
.dplan-name { font-size: 1.3rem; font-weight: 800; margin-bottom: 4px; }
.dplan-tag {
  display: inline-block; font-size: .72rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: .08em; color: var(--gray);
  background: rgba(0,0,0,.06); padding: 3px 10px; border-radius: 6px; margin-bottom: 12px;
}
.dplan-tag.featured-tag { background: rgba(167,139,250,.2); color: #a78bfa; }
.dplan-desc { font-size: .88rem; line-height: 1.6; margin-bottom: 20px; color: var(--gray); }
.desktop-plan-card.featured .dplan-desc { color: #94a3b8; }
.dplan-features { list-style: none; padding: 0; margin-bottom: 24px; display: flex; flex-direction: column; gap: 8px; }
.dplan-features li { display: flex; align-items: center; gap: 10px; font-size: .88rem; color: var(--gray); }
.desktop-plan-card.featured .dplan-features li { color: #cbd5e1; }
.dplan-features .bi-check-circle-fill { color: var(--accent); flex-shrink: 0; }
.btn-dplan {
  display: inline-flex; align-items: center;
  padding: 10px 22px; border-radius: 8px; font-weight: 700; font-size: .9rem;
  text-decoration: none; transition: all .2s; background: var(--primary); color: #fff;
}
.btn-dplan:hover { background: var(--primary-dark); transform: translateX(3px); color: #fff; }
.btn-dplan.featured { background: #7c3aed; }
.btn-dplan.featured:hover { background: #6d28d9; }

/* ════════════════════════════════════════════════════
   CONTACTO
════════════════════════════════════════════════════ */
.section-contacto {
  padding: 80px 24px;
  background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
}
.contact-grid {
  max-width: 1100px; margin: 0 auto;
  display: grid; grid-template-columns: 1fr 1.4fr; gap: 60px; align-items: start;
}
.contact-info { color: #fff; }
.contact-title { font-size: 1.9rem; font-weight: 800; margin: 16px 0 10px; }
.contact-subtitle { color: #94a3b8; margin-bottom: 32px; line-height: 1.7; }
.contact-details { display: flex; flex-direction: column; gap: 16px; margin-bottom: 24px; }
.contact-item { display: flex; align-items: center; gap: 12px; color: #cbd5e1; font-size: .95rem; }
.contact-item i { color: #93c5fd; font-size: 1.2rem; flex-shrink: 0; }
.contact-profile-ref {
  background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.12);
  border-radius: 10px; padding: 12px 16px;
  color: #cbd5e1; font-size: .88rem; display: flex; align-items: center; gap: 6px;
}
.contact-profile-ref strong { color: #93c5fd; }
.contact-form-wrap {
  background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.1);
  border-radius: 20px; padding: 36px; backdrop-filter: blur(10px);
}
.contact-form { display: flex; flex-direction: column; gap: 18px; }
.form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { color: #cbd5e1; font-size: .85rem; font-weight: 600; }
.form-ctrl {
  background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.15);
  color: #fff; border-radius: 8px; padding: 10px 14px; font-size: .9rem; transition: border-color .2s;
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
.contact-success { background: rgba(16,185,129,.2); border: 1px solid rgba(16,185,129,.4); color: #6ee7b7; padding: 12px 16px; border-radius: 8px; font-size: .9rem; }
.contact-error { background: rgba(239,68,68,.15); border: 1px solid rgba(239,68,68,.3); color: #fca5a5; padding: 12px 16px; border-radius: 8px; font-size: .9rem; }

/* ════════════════════════════════════════════════════
   FOOTER
════════════════════════════════════════════════════ */
.landing-footer { background: var(--dark); color: #fff; padding: 56px 24px 24px; }
.footer-top {
  max-width: 1100px; margin: 0 auto;
  display: flex; gap: 60px; justify-content: space-between;
  flex-wrap: wrap; padding-bottom: 36px;
  border-bottom: 1px solid rgba(255,255,255,.1);
}
.footer-tagline { color: #64748b; font-size: .88rem; max-width: 240px; margin: 8px 0; }
.footer-back-link {
  display: inline-flex; align-items: center;
  color: #93c5fd; font-size: .82rem; text-decoration: none; margin-top: 4px;
  transition: color .2s;
}
.footer-back-link:hover { color: #fff; }
.footer-links { display: flex; gap: 48px; flex-wrap: wrap; }
.footer-col { display: flex; flex-direction: column; gap: 10px; }
.footer-col h5 { color: #94a3b8; font-size: .78rem; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 4px; }
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
  .pricing-cards { grid-template-columns: repeat(2,1fr); }
  .pricing-card.featured { transform: scale(1); }
}
@media (max-width: 768px) {
  .nav-links, .nav-actions { display: none; }
  .nav-hamburger { display: block; }
  .hero-profile-name { font-size: 2rem; }
  .hero-profile-content { padding: 0 6% 100px; }
  .proposal-strip-inner { flex-direction: column; gap: 8px; }
  .multidevice-strip { flex-direction: column; text-align: center; }
  .devices-row { display: none; }
  .contact-grid { grid-template-columns: 1fr; }
  .form-row-2 { grid-template-columns: 1fr; }
  .pricing-cards { grid-template-columns: 1fr 1fr; }
  .desktop-plan-cards { grid-template-columns: 1fr; }
  .desktop-strip { flex-direction: column; text-align: center; }
  .profile-detail-card { flex-direction: column; }
}
@media (max-width: 480px) {
  .pricing-cards { grid-template-columns: 1fr; }
  .hero-profile-actions { flex-direction: column; }
  .btn-slide-cta, .btn-slide-outline { justify-content: center; }
}
</style>
