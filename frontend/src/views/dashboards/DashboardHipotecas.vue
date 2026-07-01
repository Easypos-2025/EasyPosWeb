<template>
  <div class="dash-hip">

    <!-- Marca de agua de fondo -->
    <div class="wm-bg" aria-hidden="true">
      <i class="bi bi-house-door   wm-icon-1"></i>
      <i class="bi bi-calendar-check wm-icon-2"></i>
      <i class="bi bi-cash-stack   wm-icon-3"></i>
    </div>

    <!-- Header -->
    <div class="dash-header">
      <div class="dash-header-left">
        <h6 class="dash-empresa">{{ empresa }}</h6>
        <span class="dash-perfil-tag">
          <i class="bi bi-bank2"></i> Cobros - Hipotecas
        </span>
      </div>
      <span class="dash-fecha">{{ fechaHoy }}</span>
    </div>

    <!-- Banner bienvenida -->
    <div class="welcome-banner">
      <div class="wb-icon-wrap">
        <i class="bi bi-house-door"></i>
      </div>
      <div class="wb-text">
        <h5>Bienvenido a Cobros - Hipotecas</h5>
        <p>
          Administra préstamos e hipotecas, registra cobros y cuotas, controla
          tu cartera activa y lleva el seguimiento detallado de cada cliente
          con su calendario de pagos.
        </p>
      </div>
    </div>

    <!-- Accesos rápidos -->
    <p class="section-label">
      <i class="bi bi-lightning-charge-fill"></i> Accesos rápidos
    </p>
    <div class="accesos-grid">
      <button class="acceso-card green" @click="ir('/hipotecas/nueva')">
        <i class="bi bi-house-plus"></i>
        <span>Nueva<br>Hipoteca</span>
      </button>
      <button class="acceso-card" @click="ir('/cobros/registrar')">
        <i class="bi bi-cash-coin"></i>
        <span>Registrar<br>Cobro</span>
      </button>
      <button class="acceso-card" @click="ir('/cartera')">
        <i class="bi bi-briefcase"></i>
        <span>Cartera<br>Activa</span>
      </button>
      <button class="acceso-card" @click="ir('/cobros/calendario')">
        <i class="bi bi-calendar-check"></i>
        <span>Calendario<br>de Pagos</span>
      </button>
      <button class="acceso-card" @click="ir('/clientes')">
        <i class="bi bi-people"></i>
        <span>Clientes</span>
      </button>
      <button class="acceso-card" @click="ir('/reportes')">
        <i class="bi bi-bar-chart-line"></i>
        <span>Reportes</span>
      </button>
    </div>

  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useCompanyStore } from '@/stores/companyStore'

const companyStore = useCompanyStore()
const router       = useRouter()

const empresa = computed(() => companyStore.selectedCompany?.name ?? '')

const fechaHoy = computed(() =>
  new Intl.DateTimeFormat('es-CO', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
  }).format(new Date())
)

function ir(ruta) { router.push(ruta) }
</script>

<style scoped>
/* ───────────────── contenedor ───────────────── */
.dash-hip {
  position: relative;
  min-height: 80vh;
  padding: 0 24px 48px;
  overflow: hidden;
}

/* ───────────────── marca de agua ───────────────── */
.wm-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}
.wm-icon-1 {
  position: absolute;
  font-size: 420px;
  color: #065f46;
  opacity: 0.045;
  bottom: -80px;
  right: -60px;
  transform: rotate(-8deg);
}
.wm-icon-2 {
  position: absolute;
  font-size: 160px;
  color: #0f2448;
  opacity: 0.05;
  top: 50px;
  left: -20px;
  transform: rotate(15deg);
}
.wm-icon-3 {
  position: absolute;
  font-size: 100px;
  color: #10b981;
  opacity: 0.055;
  top: 200px;
  right: 22%;
  transform: rotate(-25deg);
}

/* ───────────────── header ───────────────── */
.dash-header {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 24px 0 16px;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 24px;
}
.dash-empresa {
  margin: 0 0 4px;
  font-size: 20px;
  font-weight: 700;
  color: #0f2448;
  line-height: 1.2;
}
.dash-perfil-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 600;
  color: #065f46;
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  border-radius: 20px;
  padding: 2px 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.dash-fecha {
  font-size: 13px;
  color: #64748b;
  white-space: nowrap;
  padding-top: 2px;
  text-transform: capitalize;
}

/* ───────────────── banner bienvenida ───────────────── */
.welcome-banner {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 20px;
  background: linear-gradient(135deg, #0f2448 0%, #065f46 100%);
  border-radius: 16px;
  padding: 28px 28px;
  margin-bottom: 28px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(15,36,72,0.20);
}
.wb-icon-wrap {
  flex-shrink: 0;
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: rgba(16,185,129,0.18);
  border: 1px solid rgba(16,185,129,0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30px;
  color: #10b981;
}
.wb-text h5 {
  margin: 0 0 6px;
  font-size: 17px;
  font-weight: 700;
  color: #fff;
}
.wb-text p {
  margin: 0;
  font-size: 13.5px;
  color: #a7f3d0;
  line-height: 1.6;
}

/* ───────────────── accesos rápidos ───────────────── */
.section-label {
  position: relative;
  z-index: 1;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: #64748b;
  margin: 0 0 14px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.section-label .bi { color: #10b981; font-size: 13px; }

.accesos-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}
.acceso-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: #fff;
  border: 1.5px solid #e2e8f0;
  border-radius: 14px;
  padding: 22px 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.acceso-card:hover {
  border-color: #065f46;
  box-shadow: 0 4px 16px rgba(6,95,70,0.14);
  transform: translateY(-2px);
}
.acceso-card .bi {
  font-size: 26px;
  color: #0f2448;
}
.acceso-card span {
  font-size: 12.5px;
  font-weight: 600;
  color: #334155;
  line-height: 1.4;
}
.acceso-card.green {
  background: linear-gradient(135deg, #064e3b 0%, #065f46 100%);
  border-color: #065f46;
}
.acceso-card.green .bi  { color: #a7f3d0; }
.acceso-card.green span { color: #d1fae5; }
.acceso-card.green:hover {
  border-color: #047857;
  box-shadow: 0 4px 16px rgba(6,95,70,0.30);
}

/* ───────────────── responsive ───────────────── */
@media (max-width: 768px) {
  .dash-hip { padding: 0 16px 40px; }
  .accesos-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; }
  .welcome-banner { flex-direction: column; text-align: center; padding: 22px 20px; }
  .dash-header { flex-direction: column; gap: 6px; }
  .dash-fecha { font-size: 12px; }
  .wm-icon-1 { font-size: 280px; }
  .wm-icon-2 { font-size: 110px; }
}

@media (max-width: 576px) {
  .dash-hip { padding: 0 12px 32px; }
  .accesos-grid { grid-template-columns: repeat(2, 1fr); gap: 10px; }
  .acceso-card { padding: 18px 8px; }
  .acceso-card .bi { font-size: 22px; }
  .acceso-card span { font-size: 11.5px; }
  .dash-empresa { font-size: 17px; }
  .wb-icon-wrap { width: 50px; height: 50px; font-size: 24px; }
  .wb-text h5 { font-size: 15px; }
  .wb-text p  { font-size: 12.5px; }
  .wm-icon-1 { font-size: 200px; bottom: -40px; right: -20px; }
  .wm-icon-2 { font-size: 80px; }
  .wm-icon-3 { display: none; }
}
</style>
