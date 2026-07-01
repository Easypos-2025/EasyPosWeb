<template>
  <div class="dash-cv">

    <!-- Marca de agua de fondo -->
    <div class="wm-bg" aria-hidden="true">
      <i class="bi bi-gem        wm-icon-1"></i>
      <i class="bi bi-arrow-left-right wm-icon-2"></i>
      <i class="bi bi-gem        wm-icon-3"></i>
    </div>

    <!-- Header -->
    <div class="dash-header">
      <div class="dash-header-left">
        <h6 class="dash-empresa">{{ empresa }}</h6>
        <span class="dash-perfil-tag">
          <i class="bi bi-shop-window"></i> Compra - Ventas
        </span>
      </div>
      <span class="dash-fecha">{{ fechaHoy }}</span>
    </div>

    <!-- Banner bienvenida -->
    <div class="welcome-banner">
      <div class="wb-icon-wrap">
        <i class="bi bi-gem"></i>
      </div>
      <div class="wb-text">
        <h5>Bienvenido a Compra - Ventas</h5>
        <p>
          Gestiona tus operaciones de compra y venta, controla el inventario de
          artículos valuados y lleva el seguimiento de clientes y proveedores
          desde un solo lugar.
        </p>
      </div>
    </div>

    <!-- Accesos rápidos -->
    <p class="section-label">
      <i class="bi bi-lightning-charge-fill"></i> Accesos rápidos
    </p>
    <div class="accesos-grid">
      <button class="acceso-card" @click="ir('/pos/compras')">
        <i class="bi bi-cart-plus"></i>
        <span>Registrar<br>Compra</span>
      </button>
      <button class="acceso-card gold" @click="ir('/pos/ventas')">
        <i class="bi bi-bag-check"></i>
        <span>Registrar<br>Venta</span>
      </button>
      <button class="acceso-card" @click="ir('/inventario')">
        <i class="bi bi-boxes"></i>
        <span>Inventario</span>
      </button>
      <button class="acceso-card" @click="ir('/clientes')">
        <i class="bi bi-people"></i>
        <span>Clientes /<br>Proveedores</span>
      </button>
      <button class="acceso-card" @click="ir('/tasaciones')">
        <i class="bi bi-scales"></i>
        <span>Tasaciones</span>
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
.dash-cv {
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
  font-size: 380px;
  color: #b45309;
  opacity: 0.05;
  bottom: -60px;
  right: -50px;
  transform: rotate(-20deg);
}
.wm-icon-2 {
  position: absolute;
  font-size: 180px;
  color: #1e3a5f;
  opacity: 0.04;
  top: 60px;
  left: -30px;
  transform: rotate(12deg);
}
.wm-icon-3 {
  position: absolute;
  font-size: 90px;
  color: #f59e0b;
  opacity: 0.06;
  top: 180px;
  right: 18%;
  transform: rotate(30deg);
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
  color: #1e3a5f;
  line-height: 1.2;
}
.dash-perfil-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 600;
  color: #b45309;
  background: #fef3c7;
  border: 1px solid #fcd34d;
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
  background: linear-gradient(135deg, #1e3a5f 0%, #1e40af 100%);
  border-radius: 16px;
  padding: 28px 28px;
  margin-bottom: 28px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(30,58,95,0.18);
}
.wb-icon-wrap {
  flex-shrink: 0;
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: rgba(245,158,11,0.18);
  border: 1px solid rgba(245,158,11,0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30px;
  color: #f59e0b;
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
  color: #bfdbfe;
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
.section-label .bi { color: #f59e0b; font-size: 13px; }

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
  border-color: #1e40af;
  box-shadow: 0 4px 16px rgba(30,64,175,0.14);
  transform: translateY(-2px);
}
.acceso-card .bi {
  font-size: 26px;
  color: #1e3a5f;
}
.acceso-card span {
  font-size: 12.5px;
  font-weight: 600;
  color: #334155;
  line-height: 1.4;
}
.acceso-card.gold {
  background: linear-gradient(135deg, #78350f 0%, #b45309 100%);
  border-color: #b45309;
}
.acceso-card.gold .bi  { color: #fef3c7; }
.acceso-card.gold span { color: #fef3c7; }
.acceso-card.gold:hover {
  border-color: #92400e;
  box-shadow: 0 4px 16px rgba(180,83,9,0.25);
}

/* ───────────────── responsive ───────────────── */
@media (max-width: 768px) {
  .dash-cv { padding: 0 16px 40px; }
  .accesos-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; }
  .welcome-banner { flex-direction: column; text-align: center; padding: 22px 20px; }
  .dash-header { flex-direction: column; gap: 6px; }
  .dash-fecha { font-size: 12px; }
  .wm-icon-1 { font-size: 260px; }
  .wm-icon-2 { font-size: 120px; }
}

@media (max-width: 576px) {
  .dash-cv { padding: 0 12px 32px; }
  .accesos-grid { grid-template-columns: repeat(2, 1fr); gap: 10px; }
  .acceso-card { padding: 18px 8px; }
  .acceso-card .bi { font-size: 22px; }
  .acceso-card span { font-size: 11.5px; }
  .dash-empresa { font-size: 17px; }
  .wb-icon-wrap { width: 50px; height: 50px; font-size: 24px; }
  .wb-text h5 { font-size: 15px; }
  .wb-text p  { font-size: 12.5px; }
  .wm-icon-1 { font-size: 190px; bottom: -30px; right: -20px; }
  .wm-icon-2 { font-size: 90px; }
  .wm-icon-3 { display: none; }
}
</style>
