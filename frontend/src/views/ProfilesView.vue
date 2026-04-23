<template>
<div class="profiles-wrap">

  <!-- ══════════════════════════════════════
       COLUMNA IZQUIERDA — Datos de empresa (35%)
  ══════════════════════════════════════ -->
  <div class="col-company">

    <h2 class="section-title">
      <i class="bi bi-building"></i> Datos de Empresa
    </h2>

    <div v-if="loading" class="loading-msg">Cargando...</div>

    <template v-else>
      <div class="form-grid">

        <div class="fg full">
          <label>Nombre</label>
          <input v-model="company.name" class="fi" />
        </div>

        <div class="fg">
          <label>Documento / NIT</label>
          <input v-model="company.identification_number" class="fi" />
        </div>

        <div class="fg">
          <label>Email</label>
          <input v-model="company.email" type="email" class="fi" />
        </div>

        <div class="fg">
          <label>Teléfono</label>
          <input v-model="company.phone" class="fi" />
        </div>

        <div class="fg">
          <label>Dirección</label>
          <input v-model="company.address" class="fi" />
        </div>

        <div class="fg full">
          <label>Descripción <span class="optional">(opcional)</span></label>
          <textarea v-model="company.description" class="fi" rows="2"></textarea>
        </div>

      </div>

      <div class="col-footer">
        <button class="btn btn-primary" @click="saveCompany">
          <i class="bi bi-floppy"></i> Guardar empresa
        </button>
      </div>
    </template>

  </div>

  <!-- ══════════════════════════════════════
       COLUMNA DERECHA — Configuración de Tema (65%)
  ══════════════════════════════════════ -->
  <div class="col-theme">

    <h2 class="section-title">
      <i class="bi bi-palette"></i> Configuración de Tema
    </h2>

    <div v-if="!isProfileReady" class="loading-msg">Cargando perfil...</div>

    <template v-else>

      <!-- Fila de colores + tamaño de fuente -->
      <div class="colors-row">

        <div class="color-ctrl">
          <label>Topbar</label>
          <input type="color" v-model="perfil.topbar_color" />
        </div>

        <div class="color-ctrl">
          <label>Sidebar</label>
          <input type="color" v-model="perfil.sidebar_color" />
        </div>

        <div class="color-ctrl">
          <label>Fondo</label>
          <input type="color" v-model="perfil.bg_color" />
        </div>

        <div class="color-ctrl">
          <label>Fuente</label>
          <input type="color" v-model="perfil.font_color" />
        </div>

        <div class="size-ctrl">
          <label>Tamaño fuente</label>
          <select v-model="perfil.font_size" class="fi fi-sm">
            <option :value="13">13px — Pequeño</option>
            <option :value="14">14px</option>
            <option :value="15">15px</option>
            <option :value="16">16px — Normal</option>
            <option :value="17">17px</option>
            <option :value="18">18px — Grande</option>
            <option :value="20">20px — Muy grande</option>
            <option :value="22">22px</option>
          </select>
        </div>

      </div>

      <!-- Logo: editor + preview + actual -->
      <div class="logo-section-label">
        <i class="bi bi-image"></i>
        Logo de la empresa
        <span class="optional">— edita y recorta antes de guardar</span>
      </div>

      <ImageUploader
        :currentLogo="currentLogo"
        @update:image="val => perfil.value.logo = val"
      />

      <div class="col-footer">
        <button class="btn btn-primary" @click="saveTheme">
          <i class="bi bi-floppy"></i> Guardar tema
        </button>
      </div>

    </template>

  </div>

</div>
</template>


<script setup>

import { ref, watch, watchEffect, onMounted, nextTick } from "vue"
import { applyTheme, getThemeState } from "@/utils/theme"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import ImageUploader from "@/components/common/ImageUploader.vue"
import { useCompanyStore } from "@/stores/companyStore"

const companyStore = useCompanyStore()
const themeState   = getThemeState()   // mismo estado que usa el Topbar

const isProfileReady  = ref(false)
const loading         = ref(false)
const themeOriginal   = ref(null)
const currentLogo     = ref("")      // ref dedicado para el ImageUploader

// Cuando el companyStore carga el logo (para el topbar), lo usamos aquí también
watchEffect(() => {
  if (themeState.logo) currentLogo.value = themeState.logo
})

const company = ref({
  id_company: null, name: "", description: "",
  identification_number: "", email: "", phone: "", address: ""
})

const perfil = ref({
  topbar_color: "#1e3a5f", sidebar_color: "#1a2535",
  bg_color: "#f1f5f9", logo: "", font_size: 16, font_color: "#1e293b"
})

const getCompanyId = () => companyStore.selectedCompany?.id ?? null

const loadCompany = async (id) => {
  const companyId = id ?? getCompanyId()
  if (!companyId) return
  loading.value = true
  try {
    const res = await api.get(`/companies/${companyId}`)
    company.value = res.data
  } catch (e) {
    console.error("ERROR LOADING COMPANY:", e)
  } finally {
    loading.value = false
  }
}

const saveCompany = async () => {
  try {
    await api.put(`/companies/${getCompanyId()}`, company.value)
    showToast("Empresa actualizada correctamente", "success")
  } catch {
    showToast("Error al actualizar empresa", "error")
  }
}

const saveTheme = async () => {
  const companyId = getCompanyId()
  if (!companyId) return
  try {
    const res = await api.put(`/company-theme/${companyId}`, perfil.value)
    showToast("Tema actualizado correctamente", "success")
    applyTheme(res.data)          // actualiza themeState.logo → watchEffect → currentLogo
    themeOriginal.value = res.data
  } catch {
    showToast("Error guardando tema", "error")
  }
}

const loadPerfil = async (id) => {
  const companyId = id ?? getCompanyId()
  if (!companyId) return
  try {
    // Paso 1: colores rápidos (sin logo) — muestra el formulario de inmediato
    const colorsRes = await api.get(`/company-theme/${companyId}/colors`)
    const colors = colorsRes.data
    perfil.value = {
      topbar_color:  colors.topbar_color  || "#1e3a5f",
      sidebar_color: colors.sidebar_color || "#1a2535",
      bg_color:      colors.bg_color      || "#f1f5f9",
      logo:          perfil.value.logo    || "",   // mantener logo previo mientras carga
      font_size:     colors.font_size     || 16,
      font_color:    colors.font_color    || "#1e293b"
    }
    applyTheme(perfil.value)

    // El logo ya está en themeState.logo (cargado por companyStore)
    // El watchEffect de arriba lo propaga automáticamente al ImageUploader

  } catch (e) {
    console.error("ERROR CARGANDO THEME:", e)
  }
}

watch(perfil, (v) => applyTheme(v), { deep: true })

watch(
  () => companyStore.selectedCompany,
  async (newC, oldC) => {
    if (newC?.id && newC?.id !== oldC?.id) {
      isProfileReady.value = false
      await Promise.all([loadCompany(newC.id), loadPerfil(newC.id)])
      await nextTick()
      isProfileReady.value = true
    }
  }
)

onMounted(async () => {
  await Promise.all([loadCompany(), loadPerfil()])
  await nextTick()
  isProfileReady.value = true
})

</script>


<style scoped>

/* ── LAYOUT PRINCIPAL 35 / 65 ── */
.profiles-wrap {
  display: grid;
  grid-template-columns: 35% 1fr;
  gap: 24px;
  padding: 20px;
  height: 100%;
  min-height: 0;
  align-items: start;
}

/* ── COLUMNAS ── */
.col-company,
.col-theme {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.08);
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ── TÍTULO ── */
.section-title {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 4px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f1f5f9;
}

/* ── FORM GRID (empresa) ── */
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.fg {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.fg.full { grid-column: span 2; }

.fg label {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.optional { font-weight: 400; text-transform: none; letter-spacing: 0; color: #94a3b8; }

/* ── INPUT BASE ── */
.fi {
  padding: 8px 11px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  color: #1e293b !important;
  background: #f8fafc !important;
  outline: none;
  transition: border 0.15s;
  width: 100%;
}
.fi:focus { border-color: #3b82f6; background: #fff !important; }

.fi-sm { max-width: 180px; }

/* ── COLORES + FUENTE ── */
.colors-row {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  flex-wrap: wrap;
  padding: 14px 16px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.color-ctrl {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}

.color-ctrl label,
.size-ctrl label {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  white-space: nowrap;
}

.color-ctrl input[type="color"] {
  width: 44px;
  height: 36px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  padding: 2px;
  background: none;
}

.size-ctrl {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-left: auto;
}

/* ── LABEL LOGO ── */
.logo-section-label {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
}

/* ── PIE DE COLUMNA ── */
.col-footer {
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid #f1f5f9;
  display: flex;
  justify-content: flex-start;
}

.loading-msg {
  color: #94a3b8;
  font-size: 14px;
  padding: 20px 0;
}

/* ── RESPONSIVE ── */
@media (max-width: 900px) {
  .profiles-wrap {
    grid-template-columns: 1fr;
  }
  .form-grid {
    grid-template-columns: 1fr;
  }
  .fg.full { grid-column: span 1; }
}
</style>
