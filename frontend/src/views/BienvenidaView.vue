<template>
  <div class="bienvenida-wrap">

    <!-- ── HERO ── -->
    <div class="hero-band">
      <div class="hero-inner">
        <div class="hero-icon-wrap">
          <i class="bi bi-stars hero-star"></i>
        </div>
        <div class="hero-text">
          <span class="hero-sub">Bienvenido a</span>
          <h1 class="hero-title">
            ¡Ya eres parte de la familia
            <span class="brand-name">EasyPosWeb</span>!
          </h1>
          <p class="hero-desc">
            Esta guía rápida te mostrará los pasos para comenzar a configurar tu plataforma
            y sacarle el máximo provecho desde el primer día.
          </p>
        </div>
      </div>
    </div>

    <!-- ── STEPS ── -->
    <div class="steps-section">
      <h2 class="steps-title">¿Por dónde empiezo?</h2>

      <div v-if="loading" class="loading-steps">
        <div class="spinner-border text-primary" role="status"></div>
        <span>Cargando guía...</span>
      </div>

      <div v-else-if="steps.length" class="steps-grid">
        <div
          v-for="step in steps"
          :key="step.id"
          class="step-card"
        >
          <div class="step-number">{{ step.step_number }}</div>
          <div class="step-icon-wrap">
            <i :class="['bi', step.icon]"></i>
          </div>
          <div class="step-body">
            <h3 class="step-title">{{ step.title }}</h3>
            <p class="step-desc">{{ step.description }}</p>
          </div>
          <router-link
            v-if="step.route_hint"
            :to="step.route_hint"
            class="step-btn"
            @click="markSeen"
          >
            Ir ahora <i class="bi bi-arrow-right-short"></i>
          </router-link>
        </div>
      </div>

      <div v-else class="no-steps">
        <i class="bi bi-info-circle"></i>
        <p>No hay pasos configurados para tu perfil aún.</p>
      </div>
    </div>

    <!-- ── FOOTER ACCIONES ── -->
    <div class="actions-band">
      <router-link to="/navigation-map" class="btn-guide" @click="markSeen">
        <i class="bi bi-map"></i>
        Ver guía completa de módulos
      </router-link>
      <button class="btn-start" @click="goStart">
        <i class="bi bi-rocket-takeoff"></i>
        Comenzar
      </button>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { useRouter }      from "vue-router"
import api                from "@/services/apis"

const router  = useRouter()
const steps   = ref([])
const loading = ref(true)

function markSeen() {
  const u = JSON.parse(localStorage.getItem("user") || "{}")
  if (u.id) localStorage.setItem(`welcome_seen_${u.id}`, "1")
}

function goStart() {
  markSeen()
  router.push("/dashboard")
}

onMounted(async () => {
  try {
    const res = await api.get("/welcome-steps")
    steps.value = res.data
  } catch {}
  loading.value = false
  // Marcar como visto al llegar aquí (el usuario ya lo vio)
  markSeen()
})
</script>

<style scoped>
.bienvenida-wrap {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f8f9fb;
}

/* ── HERO ── */
.hero-band {
  background: linear-gradient(135deg, var(--color-primary, #0d6efd) 0%, #1a3a6b 100%);
  color: #fff;
  padding: 48px 24px 40px;
}
.hero-inner {
  max-width: 860px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 28px;
}
.hero-icon-wrap {
  flex-shrink: 0;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: rgba(255,255,255,.18);
  display: flex;
  align-items: center;
  justify-content: center;
}
.hero-star { font-size: 2.4rem; color: #ffd700; }
.hero-sub  { font-size: .85rem; opacity: .8; display: block; margin-bottom: 4px; text-transform: uppercase; letter-spacing: .08em; }
.hero-title {
  font-size: clamp(1.4rem, 3vw, 2rem);
  font-weight: 700;
  margin: 0 0 10px;
  line-height: 1.25;
}
.brand-name { color: #ffd700; }
.hero-desc  { margin: 0; opacity: .88; font-size: .97rem; line-height: 1.55; }

/* ── STEPS ── */
.steps-section {
  flex: 1;
  max-width: 960px;
  width: 100%;
  margin: 0 auto;
  padding: 40px 20px 24px;
}
.steps-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 28px;
}
.loading-steps {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #64748b;
  padding: 20px 0;
}
.steps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 18px;
}
.step-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 22px 20px 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  position: relative;
  transition: box-shadow .2s, transform .2s;
}
.step-card:hover {
  box-shadow: 0 6px 24px rgba(13,110,253,.10);
  transform: translateY(-2px);
}
.step-number {
  position: absolute;
  top: 14px;
  right: 16px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-primary, #0d6efd);
  color: #fff;
  font-size: .78rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}
.step-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(13,110,253,.10);
  display: flex;
  align-items: center;
  justify-content: center;
}
.step-icon-wrap i { font-size: 1.5rem; color: var(--color-primary, #0d6efd); }
.step-title { font-size: 1rem; font-weight: 700; color: #1e293b; margin: 0; }
.step-desc  { font-size: .875rem; color: #475569; line-height: 1.55; margin: 0; flex: 1; }
.step-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: .82rem;
  font-weight: 600;
  color: var(--color-primary, #0d6efd);
  text-decoration: none;
  margin-top: 4px;
  transition: gap .15s;
}
.step-btn:hover { gap: 8px; }

.no-steps {
  text-align: center;
  color: #94a3b8;
  padding: 40px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}
.no-steps i { font-size: 2rem; }

/* ── ACCIONES ── */
.actions-band {
  background: #fff;
  border-top: 1px solid #e2e8f0;
  padding: 20px 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  flex-wrap: wrap;
}
.btn-guide {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 11px 24px;
  border-radius: 8px;
  border: 2px solid var(--color-primary, #0d6efd);
  color: var(--color-primary, #0d6efd);
  font-weight: 600;
  font-size: .92rem;
  text-decoration: none;
  transition: background .18s, color .18s;
}
.btn-guide:hover { background: var(--color-primary, #0d6efd); color: #fff; }
.btn-start {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 11px 28px;
  border-radius: 8px;
  border: none;
  background: var(--color-primary, #0d6efd);
  color: #fff;
  font-weight: 700;
  font-size: .92rem;
  cursor: pointer;
  transition: opacity .18s;
}
.btn-start:hover { opacity: .88; }

/* ── RESPONSIVE ── */
@media (max-width: 768px) {
  .hero-inner { flex-direction: column; text-align: center; gap: 16px; }
  .hero-icon-wrap { width: 64px; height: 64px; }
  .steps-grid { grid-template-columns: 1fr; }
}
@media (max-width: 576px) {
  .hero-band { padding: 32px 16px 28px; }
  .steps-section { padding: 28px 14px 16px; }
  .actions-band { flex-direction: column; }
  .btn-guide, .btn-start { width: 100%; justify-content: center; }
}
</style>
