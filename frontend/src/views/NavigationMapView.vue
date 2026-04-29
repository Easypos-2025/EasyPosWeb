<template>
  <div class="nav-map">

    <!-- BANNER SUPERIOR -->
    <div class="map-banner">
      <div class="banner-left">
        <h1 class="banner-title">
          <i class="bi bi-map-fill"></i>
          Guía de módulos
        </h1>
        <p class="banner-sub">
          {{ companyName }} · {{ totalSections }} sección{{ totalSections !== 1 ? 'es' : '' }} · {{ totalModules }} módulo{{ totalModules !== 1 ? 's' : '' }} disponible{{ totalModules !== 1 ? 's' : '' }}
        </p>
      </div>
      <div class="banner-right">
        <div class="search-wrap">
          <i class="bi bi-search search-ico"></i>
          <input
            v-model="search"
            class="search-input"
            placeholder="Buscar módulo..."
            type="text"
            autocomplete="off"
          />
          <button v-if="search" class="search-clear" @click="search = ''">
            <i class="bi bi-x"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- SIN MENÚ -->
    <div v-if="!menuStore.menu.length" class="empty-state">
      <i class="bi bi-grid-3x3-gap"></i>
      <p>No hay módulos asignados a tu perfil.</p>
    </div>

    <!-- SIN RESULTADOS DE BÚSQUEDA -->
    <div v-else-if="search && !filteredSections.length && !filteredLeaves.length" class="empty-state">
      <i class="bi bi-search"></i>
      <p>No se encontró ningún módulo con "<strong>{{ search }}</strong>"</p>
    </div>

    <template v-else>

      <!-- ACCESOS DIRECTOS (hoja raíz sin hijos) -->
      <div v-if="filteredLeaves.length" class="section-block direct-section">
        <div class="section-head direct-head">
          <span class="section-head-icon"><i class="bi bi-lightning-fill"></i></span>
          <span class="section-head-name">Accesos directos</span>
          <span class="section-count">{{ filteredLeaves.length }}</span>
        </div>
        <div class="cards-row">
          <router-link
            v-for="leaf in filteredLeaves"
            :key="leaf.id"
            :to="leaf.route || '/dashboard'"
            class="mod-card mod-card--leaf"
          >
            <span class="mod-icon"><i :class="`bi ${leaf.icon || 'bi-circle'}`"></i></span>
            <span class="mod-name">{{ leaf.name }}</span>
            <span class="mod-route">{{ leaf.route }}</span>
          </router-link>
        </div>
      </div>

      <!-- SECCIONES CON HIJOS -->
      <div
        v-for="section in filteredSections"
        :key="section.id"
        class="section-block"
      >
        <!-- Cabecera de sección -->
        <div class="section-head">
          <span class="section-head-icon">
            <i :class="`bi ${section.icon || 'bi-folder'}`"></i>
          </span>
          <span class="section-head-name">{{ section.name }}</span>
          <span class="section-count">{{ section.visibleChildren.length }}</span>
          <router-link
            v-if="section.route"
            :to="section.route"
            class="section-link"
            title="Ir a la sección"
          >
            <i class="bi bi-arrow-right-circle"></i>
          </router-link>
        </div>

        <!-- Tarjetas de hijos -->
        <div class="cards-row">
          <router-link
            v-for="child in section.visibleChildren"
            :key="child.id"
            :to="child.route || '/dashboard'"
            class="mod-card"
          >
            <span class="mod-icon"><i :class="`bi ${child.icon || 'bi-circle'}`"></i></span>
            <span class="mod-name">{{ child.name }}</span>
            <span class="mod-route">{{ child.route }}</span>
          </router-link>
        </div>
      </div>

    </template>

  </div>
</template>

<script setup>
import { ref, computed } from "vue"
import { useMenuStore } from "@/stores/menuStore"
import { useCompanyStore } from "@/stores/companyStore"

const menuStore   = useMenuStore()
const companyStore = useCompanyStore()

const search = ref("")

const companyName = computed(
  () => companyStore.selectedCompany?.name || "Mi empresa"
)

// ── Nodos raíz sin hijos (accesos directos) ─────────────────────────────────
const leaves = computed(() =>
  menuStore.menu.filter(n => !n.children || n.children.length === 0)
)

// ── Secciones: nodos raíz CON hijos ─────────────────────────────────────────
const sections = computed(() =>
  menuStore.menu
    .filter(n => n.children && n.children.length > 0)
    .map(n => ({ ...n, visibleChildren: n.children }))
)

// ── Filtrado por búsqueda ────────────────────────────────────────────────────
const q = computed(() => search.value.toLowerCase().trim())

const filteredLeaves = computed(() => {
  if (!q.value) return leaves.value
  return leaves.value.filter(n => n.name.toLowerCase().includes(q.value))
})

const filteredSections = computed(() => {
  if (!q.value) return sections.value
  return sections.value
    .map(s => ({
      ...s,
      visibleChildren: s.children.filter(c =>
        c.name.toLowerCase().includes(q.value) ||
        s.name.toLowerCase().includes(q.value)
      )
    }))
    .filter(s =>
      s.name.toLowerCase().includes(q.value) ||
      s.visibleChildren.length > 0
    )
})

// ── KPIs ─────────────────────────────────────────────────────────────────────
const totalSections = computed(() => filteredSections.value.length + (filteredLeaves.value.length > 0 ? 1 : 0))
const totalModules  = computed(() => {
  const leafCount = filteredLeaves.value.length
  const childCount = filteredSections.value.reduce((acc, s) => acc + s.visibleChildren.length, 0)
  return leafCount + childCount + filteredSections.value.length
})
</script>

<style scoped>
.nav-map {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ── BANNER ── */
.map-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  background: var(--topbar-bg, #1e3a5f);
  border-radius: 16px;
  padding: 20px 24px;
  color: #fff;
}

.banner-title {
  font-size: 20px;
  font-weight: 800;
  margin: 0 0 4px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #fff;
}
.banner-sub { font-size: 13px; opacity: 0.75; margin: 0; }

/* BÚSQUEDA */
.search-wrap {
  position: relative;
  display: flex;
  align-items: center;
}
.search-ico {
  position: absolute;
  left: 12px;
  font-size: 14px;
  opacity: 0.6;
  color: #1e293b;
  pointer-events: none;
}
.search-input {
  padding: 9px 36px 9px 36px;
  border-radius: 10px;
  border: none;
  font-size: 14px;
  color: #1e293b;
  background: rgba(255,255,255,0.95);
  width: 240px;
  outline: none;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.search-input:focus { box-shadow: 0 0 0 2px rgba(255,255,255,0.5); }
.search-clear {
  position: absolute;
  right: 10px;
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  font-size: 15px;
  padding: 0;
  line-height: 1;
}

/* ── ESTADO VACÍO ── */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #94a3b8;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.empty-state .bi { font-size: 40px; display: block; margin-bottom: 12px; opacity: 0.4; }
.empty-state p    { font-size: 15px; margin: 0; }

/* ── SECCIÓN ── */
.section-block {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.07);
  overflow: hidden;
}

.section-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
  background: var(--topbar-bg, #1e3a5f);
  color: #fff;
}

.direct-head { background: #334155; }

.section-head-icon {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: rgba(255,255,255,0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}
.section-head-name {
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.1px;
  flex: 1;
}
.section-count {
  font-size: 11px;
  font-weight: 700;
  background: rgba(255,255,255,0.2);
  padding: 2px 9px;
  border-radius: 20px;
  flex-shrink: 0;
}
.section-link {
  color: rgba(255,255,255,0.7);
  font-size: 18px;
  text-decoration: none;
  flex-shrink: 0;
  transition: color 0.15s;
}
.section-link:hover { color: #fff; }

/* ── GRID DE TARJETAS ── */
.cards-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
  padding: 16px;
}

/* ── TARJETA ── */
.mod-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 18px 12px 14px;
  border-radius: 12px;
  border: 1.5px solid #f1f5f9;
  background: #f8fafc;
  text-decoration: none;
  color: #1e293b;
  transition: all 0.18s;
  text-align: center;
  cursor: pointer;
}
.mod-card:hover {
  background: var(--topbar-bg, #1e3a5f);
  border-color: var(--topbar-bg, #1e3a5f);
  color: #fff;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0,0,0,0.15);
}

.mod-card--leaf {
  border-color: #e0e7ff;
  background: #f0f4ff;
}
.mod-card--leaf:hover {
  background: #4f46e5;
  border-color: #4f46e5;
  color: #fff;
}

.mod-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(30,58,95,0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
  transition: background 0.18s;
}
.mod-card:hover .mod-icon {
  background: rgba(255,255,255,0.2);
}
.mod-card--leaf .mod-icon { background: rgba(79,70,229,0.12); }
.mod-card--leaf:hover .mod-icon { background: rgba(255,255,255,0.2); }

.mod-name {
  font-size: 12px;
  font-weight: 700;
  line-height: 1.3;
  color: inherit;
}
.mod-route {
  font-size: 10px;
  opacity: 0.5;
  font-family: monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
  color: inherit;
}

/* ── RESPONSIVE ── */
@media (max-width: 768px) {
  .nav-map       { padding: 12px; gap: 12px; }
  .map-banner    { flex-direction: column; align-items: flex-start; padding: 16px; }
  .banner-right  { width: 100%; }
  .search-wrap   { width: 100%; }
  .search-input  { width: 100%; min-width: 0; }
  .banner-title  { font-size: 17px; }
  .cards-row     { grid-template-columns: repeat(2, 1fr); gap: 8px; padding: 12px; }
  .mod-icon      { width: 40px; height: 40px; font-size: 18px; }
  .mod-card      { padding: 14px 8px 10px; }
  .mod-route     { display: none; }
}
@media (max-width: 360px) {
  .cards-row     { grid-template-columns: repeat(2, 1fr); gap: 6px; padding: 8px; }
  .mod-card      { padding: 12px 6px 8px; }
  .mod-name      { font-size: 11px; }
}
</style>
