<template>
  <header class="topbar">

    <!-- ── IZQUIERDA: logo + selector + título empresa + ventas ── -->
    <div class="topbar-left">

      <button class="btn-icon btn-menu-left" @click="emit('toggle-sidebar')" title="Menú">
        <i class="bi bi-list"></i>
      </button>

      <!-- Logo del Asociado -->
      <div class="brand">
        <img v-if="logo" :src="logo" class="brand-logo" alt="logo" />
      </div>

      <!-- Separador solo si hay logo del asociado -->
      <div v-if="logo" class="topbar-divider"></div>

      <!-- Selector de empresa: visible cuando hay más de 1 empresa disponible -->
      <select
        v-if="companyStore.companies.length > 1"
        :value="companyStore.selectedCompany?.id"
        @change="onCompanyChange"
        class="company-select"
        title="Cambiar empresa"
      >
        <option v-for="c in companyStore.companies" :key="c.id" :value="c.id">
          {{ c.name }}
        </option>
      </select>

      <!-- Plan + vencimiento -->
      <div v-if="companyPlan.plan_name" class="plan-badge">
        <i class="bi bi-award"></i>
        <span class="plan-name">{{ companyPlan.plan_name }}</span>
        <span class="plan-exp">
          {{ companyPlan.expiration_date
            ? 'Vence: ' + formatDate(companyPlan.expiration_date)
            : 'Indefinido' }}
        </span>
      </div>

      <!-- Nombre de la empresa como título + tipo de negocio -->
      <div class="company-title-wrap">
        <span class="company-title">
          {{ companyStore.selectedCompany?.name || 'EasyPosWeb' }}
        </span>
        <span
          v-if="companyStore.selectedCompany?.business_profile_name"
          class="company-profile-type"
        >({{ companyStore.selectedCompany.business_profile_name }})</span>
      </div>

      <!-- Badge SYSADMIN -->
      <span v-if="companyStore.isSystem" class="sysadmin-badge">ADMIN</span>


    </div>

    <!-- ── DERECHA: búsqueda + usuario + logout ── -->
    <div class="topbar-right">

      <div class="search-wrap">
        <i class="bi bi-search search-icon"></i>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Buscar ayuda..."
          class="search-input"
          @keyup.enter="onSearch"
        />
      </div>

      <div class="user-info">
        <i class="bi bi-person-circle"></i>
        <div class="user-text">
          <span class="user-name">{{ user?.nombre }}</span>
          <span class="user-role">{{ user?.role }}</span>
        </div>
      </div>

      <!-- Soporte — sin funcionalidad hasta implementar módulo de tickets -->
      <button class="btn-icon btn-support" title="Abrir ticket de soporte" disabled>
        <i class="bi bi-headset"></i>
        <span class="btn-label">Soporte</span>
      </button>

      <button class="btn-icon btn-logout" @click="logout" title="Cerrar sesión">
        <i class="bi bi-box-arrow-right"></i>
      </button>

      <button class="btn-icon btn-menu-right btn-notif-toggle"
        @click="emit('toggle-sidebar-right')" title="Panel lateral">
        <i class="bi bi-layout-sidebar-reverse"></i>
        <span v-if="unreadNotif > 0" class="notif-dot-topbar">{{ unreadNotif }}</span>
      </button>

    </div>

  </header>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watchEffect } from "vue"
import { useRouter } from "vue-router"
import { getThemeState } from "@/utils/theme"
import { useCompanyStore } from "@/stores/companyStore"
import api from "@/services/apis"

const emit = defineEmits(["toggle-sidebar", "toggle-sidebar-right"])

const logo          = ref("")
const user          = ref(null)
const searchQuery   = ref("")
const theme         = getThemeState()
const companyStore  = useCompanyStore()
const router        = useRouter()
const companyPlan   = ref({ plan_name: "", expiration_date: null })
const unreadNotif   = ref(0)

async function loadUnreadCount() {
  const token = localStorage.getItem("token")
  if (!token) return
  try {
    const res = await api.get("/task-comments/notifications/unread")
    unreadNotif.value = res.data.filter(n => !n.is_read).length
  } catch {}
}

let notifTimer = null

watchEffect(() => { if (theme.logo) logo.value = theme.logo })

async function loadPlan(companyId) {
  if (!companyId) return
  try {
    const res = await api.get(`/company-plan/${companyId}`)
    companyPlan.value = res.data
  } catch {
    companyPlan.value = { plan_name: "", expiration_date: null }
  }
}

function formatDate(iso) {
  if (!iso) return ""
  const [y, m, d] = iso.split("-")
  return `${d}/${m}/${y}`
}

async function onCompanyChange(e) {
  const id      = parseInt(e.target.value)
  const company = companyStore.companies.find(c => c.id === id)
  if (company) {
    await companyStore.setCompany(company)
    await loadPlan(company.id)
  }
}

function onSearch() {
  if (searchQuery.value.trim()) console.log("Buscar ayuda:", searchQuery.value)
}

async function logout() {
  try { await api.post("/auth/logout/") } catch {}
  localStorage.removeItem("token")
  localStorage.removeItem("user")
  localStorage.removeItem("menu")
  localStorage.removeItem("selected_company")
  router.push("/login")
}

onMounted(async () => {
  const stored = localStorage.getItem("user")
  if (stored) {
    user.value = JSON.parse(stored)
    await companyStore.init(user.value)
    await loadPlan(companyStore.selectedCompany?.id)
    loadUnreadCount()
    notifTimer = setInterval(loadUnreadCount, 60000)
  }
})

onUnmounted(() => { if (notifTimer) clearInterval(notifTimer) })
</script>

<style scoped>

.topbar {
  width: 100%;
  height: 54px;
  background: var(--topbar-bg);
  color: var(--topbar-text);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 14px;
  gap: 10px;
  flex-shrink: 0;
  position: relative;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0,0,0,0.25);
}

/* ── IZQUIERDA ── */
.topbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.btn-menu-left { display: none; flex-shrink: 0; }

/* Logo del Asociado */
.brand { display: flex; align-items: center; flex-shrink: 0; }

.brand-logo {
  height: 40px;
  width: auto;
  max-width: 120px;
  object-fit: contain;
  border-radius: 4px;
  filter: drop-shadow(0 1px 2px rgba(0,0,0,0.25));
}

/* Separador */
.topbar-divider {
  width: 1px;
  height: 32px;
  background: rgba(255,255,255,0.2);
  flex-shrink: 0;
}

/* Selector de empresa */
.company-select {
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 6px;
  color: var(--topbar-text);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  outline: none;
  padding: 5px 10px;
  max-width: 220px;
  min-width: 160px;
  flex-shrink: 0;
  text-align: center;
}

.company-select option {
  background: var(--topbar-bg);
  color: var(--topbar-text);
}

/* Plan + vencimiento */
.plan-badge {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.18);
  border-radius: 20px;
  flex-shrink: 0;
}

.plan-badge .bi {
  font-size: 13px;
  color: #fbbf24;
}

.plan-name {
  font-size: 12px;
  font-weight: 700;
  color: var(--topbar-text);
  white-space: nowrap;
}

.plan-exp {
  font-size: 10px;
  opacity: 0.7;
  white-space: nowrap;
}

/* Nombre empresa + tipo de negocio */
.company-title-wrap {
  display: flex;
  align-items: baseline;
  gap: 5px;
  min-width: 0;
}

.company-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--topbar-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 220px;
  letter-spacing: 0.2px;
}

.company-profile-type {
  font-size: 12px;
  font-weight: 400;
  opacity: 0.65;
  white-space: nowrap;
  flex-shrink: 0;
}

/* Badge */
.sysadmin-badge {
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.8px;
  color: #f59e0b;
  background: rgba(245,158,11,0.18);
  border-radius: 4px;
  padding: 2px 6px;
  flex-shrink: 0;
  white-space: nowrap;
}

/* ── DERECHA ── */
.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.search-wrap { position: relative; }

.search-icon {
  position: absolute;
  left: 9px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 13px;
  opacity: 0.5;
  pointer-events: none;
}

.search-input {
  width: 170px;
  padding: 6px 10px 6px 28px;
  background: rgba(255,255,255,0.1) !important;
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 20px;
  color: var(--topbar-text) !important;
  font-size: 12px;
  outline: none;
  transition: width 0.2s, background 0.2s;
}

.search-input:focus {
  width: 210px;
  background: rgba(255,255,255,0.18) !important;
}

.search-input::placeholder { color: rgba(255,255,255,0.4) !important; }

.user-info {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 5px 12px;
  background: rgba(255,255,255,0.1);
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.12);
}

.user-info .bi { font-size: 22px; flex-shrink: 0; }

.user-text { display: flex; flex-direction: column; line-height: 1.2; }
.user-name  { font-size: 13px; font-weight: 600; white-space: nowrap; }
.user-role  { font-size: 10px; opacity: 0.6; white-space: nowrap; }

.btn-icon {
  background: none;
  border: none;
  color: var(--topbar-text);
  font-size: 20px;
  cursor: pointer;
  padding: 6px 8px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  transition: background 0.2s;
  flex-shrink: 0;
}

.btn-icon:hover      { background: rgba(255,255,255,0.12); }
.btn-logout:hover    { background: rgba(239,68,68,0.25); }
.btn-menu-right      { display: none; }

.btn-notif-toggle   { position: relative; }

.notif-dot-topbar {
  position: absolute;
  top: 2px;
  right: 2px;
  min-width: 16px;
  height: 16px;
  background: #ef4444;
  color: #fff;
  font-size: 9px;
  font-weight: 800;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 3px;
  line-height: 1;
  pointer-events: none;
}

.btn-support {
  opacity: 0.7;
  cursor: default;
  flex-direction: column;
  gap: 1px;
  padding: 4px 10px;
  border-radius: 8px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.12);
}
.btn-support:hover { background: rgba(255,255,255,0.08); }
.btn-support .bi { font-size: 17px; }

.btn-label {
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  opacity: 0.85;
  line-height: 1;
}

/* ── RESPONSIVE ── */
@media (max-width: 768px) {
  .btn-menu-left   { display: flex; }
  .btn-menu-right  { display: flex; }
  .search-wrap     { display: none; }
  .user-text       { display: none; }
  .company-title     { font-size: 13px; max-width: 110px; }
  .topbar-divider    { display: none; }
  .brand-logo        { height: 34px; }
}

@media (min-width: 769px) and (max-width: 1100px) {
  .user-role     { display: none; }
  .company-title { max-width: 180px; font-size: 15px; }
  .search-input  { width: 130px; }
}
</style>
