<template>
  <div class="page-wrap">

    <!-- HEADER -->
    <div class="page-header">
      <div class="page-header-left">
        <i class="bi bi-layout-text-window-reverse page-icon"></i>
        <div>
          <h1 class="page-title">Gestión de Landing Page</h1>
          <p class="page-sub">Edita textos, imágenes y tabla de planes visibles en la página pública</p>
        </div>
      </div>
      <div class="page-header-right">
        <a href="/landing" target="_blank" class="btn-preview">
          <i class="bi bi-eye me-1"></i> Ver Landing
        </a>
      </div>
    </div>

    <!-- TABS -->
    <div class="tabs-wrap">
      <button
        v-for="tab in tabs" :key="tab.key"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        <i :class="`bi ${tab.icon} me-1`"></i> {{ tab.label }}
        <span v-if="tab.key === 'contacts' && unreadCount" class="tab-badge">{{ unreadCount }}</span>
      </button>
    </div>

    <!-- ══════════════════════════════════════════════
         TAB: SECCIONES DE TEXTO
    ══════════════════════════════════════════════ -->
    <div v-if="activeTab === 'sections'" class="tab-content">
      <div v-if="loadingSections" class="loading-state"><div class="spinner"></div> Cargando...</div>
      <div v-else>
        <div
          v-for="sec in sections" :key="sec.section_key"
          class="section-card"
          :class="{ inactive: !sec.is_active }"
        >
          <div class="section-card-header">
            <div>
              <code class="sec-key">{{ sec.section_key }}</code>
              <span class="sec-type-badge">{{ sec.section_type }}</span>
            </div>
            <div class="sec-actions">
              <button class="btn-icon-sm" @click="openEditSection(sec)" title="Editar">
                <i class="bi bi-pencil-fill"></i>
              </button>
              <label class="toggle-wrap" title="Activar/Desactivar">
                <input type="checkbox" :checked="sec.is_active" @change="toggleSection(sec)" />
                <span class="toggle-slider"></span>
              </label>
            </div>
          </div>
          <h4 class="sec-title-preview">{{ sec.title || '(sin título)' }}</h4>
          <p class="sec-subtitle-preview">{{ sec.subtitle || '' }}</p>
          <div v-if="sec.image_url" class="sec-image-preview">
            <img :src="sec.image_url" alt="imagen" />
          </div>
        </div>

        <button class="btn-add-section" @click="openNewSection">
          <i class="bi bi-plus-circle-fill me-2"></i> Nueva Sección
        </button>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════
         TAB: PERFILES DE NEGOCIO
    ══════════════════════════════════════════════ -->
    <div v-if="activeTab === 'profiles'" class="tab-content">
      <div v-if="loadingProfiles" class="loading-state"><div class="spinner"></div> Cargando...</div>
      <div v-else class="profiles-grid">
        <div v-for="prof in profiles" :key="prof.id" class="profile-edit-card">
          <div class="profile-img-area">
            <img v-if="prof.image_url" :src="prof.image_url" :alt="prof.name" class="profile-thumb" />
            <div v-else class="profile-thumb-placeholder">
              <i :class="`bi ${prof.icon || 'bi-building'}`"></i>
            </div>
            <label class="btn-upload-img" :for="`upload-${prof.id}`">
              <i class="bi bi-camera-fill me-1"></i> Cambiar imagen
              <input
                :id="`upload-${prof.id}`" type="file" accept="image/*"
                style="display:none" @change="uploadProfileImage($event, prof)"
              />
            </label>
          </div>
          <div class="profile-edit-body">
            <h5 class="profile-edit-name">{{ prof.name }}</h5>
            <div class="form-row-2">
              <div class="form-group">
                <label>Ícono Bootstrap</label>
                <input v-model="prof.icon" type="text" class="form-ctrl-sm" placeholder="bi-building" />
              </div>
              <div class="form-group">
                <label>Color Acento</label>
                <div class="color-input-wrap">
                  <input v-model="prof.color_accent" type="color" class="color-picker" />
                  <input v-model="prof.color_accent" type="text" class="form-ctrl-sm" placeholder="#0d6efd" />
                </div>
              </div>
            </div>
            <div class="form-group">
              <label>Descripción para Landing</label>
              <textarea v-model="prof.landing_description" class="form-ctrl-sm form-textarea-sm"
                        rows="3" placeholder="Texto que verán los visitantes en el slider..."></textarea>
            </div>
            <button class="btn-save-profile" @click="saveProfile(prof)">
              <i class="bi bi-floppy-fill me-1"></i> Guardar
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════
         TAB: TABLA DE PLANES
    ══════════════════════════════════════════════ -->
    <div v-if="activeTab === 'features'" class="tab-content">
      <div class="features-toolbar">
        <button class="btn-add-feature" @click="openNewFeature">
          <i class="bi bi-plus-circle-fill me-1"></i> Agregar fila
        </button>
      </div>
      <div v-if="loadingFeatures" class="loading-state"><div class="spinner"></div> Cargando...</div>
      <div v-else class="features-table-wrap">
        <table class="features-table">
          <thead>
            <tr>
              <th>Categoría</th>
              <th>Funcionalidad</th>
              <th>Free</th>
              <th>Básico</th>
              <th>Estándar</th>
              <th>Premium</th>
              <th>Orden</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <template v-for="group in groupedFeatures" :key="group.category">
              <tr class="group-header-row">
                <td :colspan="8">{{ group.category }}</td>
              </tr>
              <tr v-for="feat in group.features" :key="feat.id">
                <td><span class="cat-chip">{{ feat.category }}</span></td>
                <td>
                  <input v-model="feat.feature_name" class="tbl-input" @blur="saveFeature(feat)" />
                </td>
                <td><input v-model="feat.val_free"     class="tbl-input tbl-val" @blur="saveFeature(feat)" /></td>
                <td><input v-model="feat.val_basic"    class="tbl-input tbl-val" @blur="saveFeature(feat)" /></td>
                <td><input v-model="feat.val_standard" class="tbl-input tbl-val" @blur="saveFeature(feat)" /></td>
                <td><input v-model="feat.val_premium"  class="tbl-input tbl-val" @blur="saveFeature(feat)" /></td>
                <td><input v-model.number="feat.order_index" type="number" class="tbl-input tbl-val" @blur="saveFeature(feat)" /></td>
                <td>
                  <button class="btn-del-feat" @click="deleteFeature(feat.id)" title="Eliminar">
                    <i class="bi bi-trash3-fill"></i>
                  </button>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════
         TAB: MENSAJES DE CONTACTO
    ══════════════════════════════════════════════ -->
    <div v-if="activeTab === 'contacts'" class="tab-content">
      <div v-if="loadingContacts" class="loading-state"><div class="spinner"></div> Cargando...</div>
      <div v-else>
        <div v-if="!contacts.length" class="empty-state">
          <i class="bi bi-envelope-open fs-1 text-muted"></i>
          <p class="mt-2 text-muted">No hay mensajes de contacto aún.</p>
        </div>
        <div v-for="c in contacts" :key="c.id" class="contact-msg-card" :class="{ unread: !c.is_read }">
          <div class="msg-header">
            <div>
              <strong>{{ c.name }}</strong>
              <span v-if="c.company" class="msg-company">· {{ c.company }}</span>
              <span v-if="!c.is_read" class="badge-new">Nuevo</span>
            </div>
            <span class="msg-date">{{ formatDate(c.created_at) }}</span>
          </div>
          <div class="msg-meta">
            <span><i class="bi bi-envelope me-1"></i>{{ c.email }}</span>
            <span v-if="c.phone"><i class="bi bi-telephone me-1"></i>{{ c.phone }}</span>
          </div>
          <p class="msg-body">{{ c.message }}</p>
          <div class="msg-footer">
            <button v-if="!c.is_read" class="btn-mark-read" @click="markRead(c)">
              <i class="bi bi-check2-circle me-1"></i> Marcar como leído
            </button>
            <span v-else class="msg-read-tag"><i class="bi bi-check2-all me-1"></i>Leído</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════
         MODAL: EDITAR / CREAR SECCIÓN
    ══════════════════════════════════════════════ -->
    <div v-if="sectionModal.open" class="modal-overlay" @click.self="sectionModal.open = false">
      <div class="modal-box modal-lg">
        <div class="modal-header">
          <h5><i class="bi bi-pencil-square me-2"></i>{{ sectionModal.isNew ? 'Nueva Sección' : 'Editar Sección' }}</h5>
          <button class="btn-close-modal" @click="sectionModal.open = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-body">
          <div class="form-row-2">
            <div class="form-group">
              <label>Clave única (section_key)</label>
              <input v-model="sectionModal.data.section_key" class="form-ctrl-sm"
                     :disabled="!sectionModal.isNew" placeholder="ej: hero, features, contacto" />
            </div>
            <div class="form-group">
              <label>Tipo de sección</label>
              <select v-model="sectionModal.data.section_type" class="form-ctrl-sm">
                <option value="hero">hero</option>
                <option value="slider">slider</option>
                <option value="features">features</option>
                <option value="cta">cta</option>
                <option value="about">about</option>
                <option value="contact">contact</option>
                <option value="general">general</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>Título</label>
            <input v-model="sectionModal.data.title" class="form-ctrl-sm" placeholder="Título de la sección" />
          </div>
          <div class="form-group">
            <label>Subtítulo</label>
            <input v-model="sectionModal.data.subtitle" class="form-ctrl-sm" placeholder="Subtítulo o descripción corta" />
          </div>
          <div class="form-group">
            <label>Cuerpo de texto <span class="hint">(usa | para separar ítems de lista)</span></label>
            <textarea v-model="sectionModal.data.body_text" class="form-ctrl-sm form-textarea-sm"
                      rows="5" placeholder="Texto largo. Usa | para separar cada ítem de lista."></textarea>
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label>Texto del botón CTA</label>
              <input v-model="sectionModal.data.cta_text" class="form-ctrl-sm" placeholder="Empezar Gratis" />
            </div>
            <div class="form-group">
              <label>URL del botón CTA</label>
              <input v-model="sectionModal.data.cta_url" class="form-ctrl-sm" placeholder="/invite" />
            </div>
          </div>
          <div class="form-group">
            <label>URL de imagen</label>
            <div class="image-input-row">
              <input v-model="sectionModal.data.image_url" class="form-ctrl-sm" placeholder="/uploads/landing/foto.jpg" />
              <label class="btn-upload-inline">
                <i class="bi bi-upload me-1"></i> Subir
                <input type="file" accept="image/*" style="display:none" @change="uploadSectionImage" />
              </label>
            </div>
            <img v-if="sectionModal.data.image_url" :src="sectionModal.data.image_url"
                 class="image-preview-sm mt-2" alt="preview" />
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label>Orden</label>
              <input v-model.number="sectionModal.data.order_index" type="number" class="form-ctrl-sm" />
            </div>
            <div class="form-group form-check-group">
              <label class="check-label">
                <input type="checkbox" v-model="sectionModal.data.is_active" />
                <span>Sección activa (visible en la landing)</span>
              </label>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="sectionModal.open = false">Cancelar</button>
          <button class="btn-save" @click="saveSection" :disabled="savingSection">
            <span v-if="savingSection"><i class="bi bi-hourglass-split me-1"></i>Guardando...</span>
            <span v-else><i class="bi bi-floppy-fill me-1"></i>Guardar</span>
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL: NUEVA FEATURE -->
    <div v-if="featureModal.open" class="modal-overlay" @click.self="featureModal.open = false">
      <div class="modal-box">
        <div class="modal-header">
          <h5><i class="bi bi-plus-circle me-2"></i>Nueva fila de plan</h5>
          <button class="btn-close-modal" @click="featureModal.open = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-body">
          <div class="form-row-2">
            <div class="form-group">
              <label>Categoría</label>
              <input v-model="featureModal.data.category" class="form-ctrl-sm" list="cat-list" placeholder="Módulos Básicos" />
              <datalist id="cat-list">
                <option v-for="c in allCategories" :key="c" :value="c" />
              </datalist>
            </div>
            <div class="form-group">
              <label>Nombre funcionalidad</label>
              <input v-model="featureModal.data.feature_name" class="form-ctrl-sm" placeholder="Ej: Inventarios" />
            </div>
          </div>
          <div class="form-row-4">
            <div class="form-group">
              <label>Free</label>
              <input v-model="featureModal.data.val_free" class="form-ctrl-sm" placeholder="X / x / 5" />
            </div>
            <div class="form-group">
              <label>Básico</label>
              <input v-model="featureModal.data.val_basic" class="form-ctrl-sm" />
            </div>
            <div class="form-group">
              <label>Estándar</label>
              <input v-model="featureModal.data.val_standard" class="form-ctrl-sm" />
            </div>
            <div class="form-group">
              <label>Premium</label>
              <input v-model="featureModal.data.val_premium" class="form-ctrl-sm" />
            </div>
          </div>
          <div class="form-group">
            <label>Orden dentro de categoría</label>
            <input v-model.number="featureModal.data.order_index" type="number" class="form-ctrl-sm" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="featureModal.open = false">Cancelar</button>
          <button class="btn-save" @click="createFeature">
            <i class="bi bi-plus-circle-fill me-1"></i> Agregar
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from "vue"
import { showToast } from "@/utils/toast"
import api from "@/services/apis"

export default {
  name: "LandingManagerView",

  setup() {
    const activeTab = ref("sections")
    const tabs = [
      { key: "sections",  label: "Secciones de Texto", icon: "bi-card-text" },
      { key: "profiles",  label: "Perfiles de Negocio", icon: "bi-buildings" },
      { key: "features",  label: "Tabla de Planes",     icon: "bi-table" },
      { key: "contacts",  label: "Mensajes",            icon: "bi-envelope-fill" },
    ]

    // ── Secciones ─────────────────────────────────────
    const sections        = ref([])
    const loadingSections = ref(false)
    const savingSection   = ref(false)
    const sectionModal = reactive({
      open: false, isNew: false,
      data: { section_key: "", title: "", subtitle: "", body_text: "",
              cta_text: "", cta_url: "", image_url: "", is_active: true,
              order_index: 0, section_type: "general" }
    })

    async function loadSections() {
      loadingSections.value = true
      try {
        const res = await api.get("/landing/admin/sections")
        sections.value = res.data
      } catch (e) { showToast(e.response?.data?.detail || e.message, "error") }
      finally { loadingSections.value = false }
    }

    function openEditSection(sec) {
      sectionModal.isNew = false
      Object.assign(sectionModal.data, { ...sec })
      sectionModal.open = true
    }

    function openNewSection() {
      sectionModal.isNew = true
      Object.assign(sectionModal.data, {
        section_key: "", title: "", subtitle: "", body_text: "",
        cta_text: "", cta_url: "", image_url: "", is_active: true,
        order_index: 0, section_type: "general"
      })
      sectionModal.open = true
    }

    async function saveSection() {
      savingSection.value = true
      try {
        if (sectionModal.isNew) {
          const res = await api.post("/landing/admin/sections", sectionModal.data)
          sections.value.push(res.data)
        } else {
          const res = await api.put(`/landing/admin/sections/${sectionModal.data.section_key}`, sectionModal.data)
          const idx = sections.value.findIndex(s => s.section_key === sectionModal.data.section_key)
          if (idx !== -1) sections.value[idx] = res.data
        }
        showToast("Sección guardada correctamente", "success")
        sectionModal.open = false
      } catch (e) { showToast(e.response?.data?.detail || e.message, "error") }
      finally { savingSection.value = false }
    }

    async function toggleSection(sec) {
      try {
        const res = await api.put(`/landing/admin/sections/${sec.section_key}`, { is_active: !sec.is_active })
        const idx = sections.value.findIndex(s => s.section_key === sec.section_key)
        if (idx !== -1) sections.value[idx] = res.data
        showToast(`Sección ${res.data.is_active ? "activada" : "desactivada"}`, "success")
      } catch (e) { showToast(e.response?.data?.detail || e.message, "error") }
    }

    async function uploadSectionImage(event) {
      const file = event.target.files[0]
      if (!file) return
      const fd = new FormData()
      fd.append("file", file)
      try {
        const res = await api.post("/landing/admin/upload", fd, {
          headers: { "Content-Type": "multipart/form-data" }
        })
        sectionModal.data.image_url = res.data.url
        showToast("Imagen subida", "success")
      } catch (e) { showToast("Error subiendo imagen", "error") }
    }

    // ── Perfiles ──────────────────────────────────────
    const profiles        = ref([])
    const loadingProfiles = ref(false)

    async function loadProfiles() {
      loadingProfiles.value = true
      try {
        const res = await api.get("/landing/admin/profiles")
        profiles.value = res.data
      } catch (e) { showToast(e.response?.data?.detail || e.message, "error") }
      finally { loadingProfiles.value = false }
    }

    async function saveProfile(prof) {
      try {
        await api.put(`/landing/admin/profiles/${prof.id}`, {
          image_url: prof.image_url,
          landing_description: prof.landing_description,
          icon: prof.icon,
          color_accent: prof.color_accent,
        })
        showToast("Perfil actualizado", "success")
      } catch (e) { showToast(e.response?.data?.detail || e.message, "error") }
    }

    async function uploadProfileImage(event, prof) {
      const file = event.target.files[0]
      if (!file) return
      const fd = new FormData()
      fd.append("file", file)
      try {
        const res = await api.post("/landing/admin/upload", fd, {
          headers: { "Content-Type": "multipart/form-data" }
        })
        prof.image_url = res.data.url
        await saveProfile(prof)
        showToast("Imagen actualizada", "success")
      } catch (e) { showToast("Error subiendo imagen", "error") }
    }

    // ── Features (tabla de planes) ────────────────────
    const features        = ref([])
    const loadingFeatures = ref(false)
    const featureModal = reactive({
      open: false,
      data: { category: "", feature_name: "", val_free: null, val_basic: null,
              val_standard: null, val_premium: null, order_index: 0 }
    })

    const groupedFeatures = computed(() => {
      const groups = {}
      for (const f of features.value) {
        if (!groups[f.category]) groups[f.category] = { category: f.category, features: [] }
        groups[f.category].features.push(f)
      }
      return Object.values(groups)
    })

    const allCategories = computed(() => [...new Set(features.value.map(f => f.category))])

    async function loadFeatures() {
      loadingFeatures.value = true
      try {
        const res = await api.get("/landing/admin/plan-features")
        features.value = res.data
      } catch (e) { showToast(e.response?.data?.detail || e.message, "error") }
      finally { loadingFeatures.value = false }
    }

    function openNewFeature() {
      Object.assign(featureModal.data, {
        category: "", feature_name: "", val_free: null,
        val_basic: null, val_standard: null, val_premium: null, order_index: 0
      })
      featureModal.open = true
    }

    async function saveFeature(feat) {
      try {
        await api.put(`/landing/admin/plan-features/${feat.id}`, feat)
      } catch (e) { showToast(e.response?.data?.detail || e.message, "error") }
    }

    async function createFeature() {
      try {
        const res = await api.post("/landing/admin/plan-features", featureModal.data)
        features.value.push(res.data)
        featureModal.open = false
        showToast("Fila agregada", "success")
      } catch (e) { showToast(e.response?.data?.detail || e.message, "error") }
    }

    async function deleteFeature(id) {
      if (!confirm("¿Eliminar esta fila del plan?")) return
      try {
        await api.delete(`/landing/admin/plan-features/${id}`)
        features.value = features.value.filter(f => f.id !== id)
        showToast("Fila eliminada", "success")
      } catch (e) { showToast(e.response?.data?.detail || e.message, "error") }
    }

    // ── Contactos ─────────────────────────────────────
    const contacts        = ref([])
    const loadingContacts = ref(false)
    const unreadCount     = computed(() => contacts.value.filter(c => !c.is_read).length)

    async function loadContacts() {
      loadingContacts.value = true
      try {
        const res = await api.get("/landing/admin/contacts")
        contacts.value = res.data
      } catch (e) { showToast(e.response?.data?.detail || e.message, "error") }
      finally { loadingContacts.value = false }
    }

    async function markRead(c) {
      try {
        await api.put(`/landing/admin/contacts/${c.id}/read`)
        c.is_read = true
      } catch (e) { showToast(e.response?.data?.detail || e.message, "error") }
    }

    function formatDate(dt) {
      return new Date(dt).toLocaleDateString("es-CO", {
        day: "2-digit", month: "short", year: "numeric",
        hour: "2-digit", minute: "2-digit"
      })
    }

    onMounted(() => {
      loadSections()
      loadProfiles()
      loadFeatures()
      loadContacts()
    })

    return {
      activeTab, tabs,
      sections, loadingSections, sectionModal, savingSection,
      openEditSection, openNewSection, saveSection, toggleSection, uploadSectionImage,
      profiles, loadingProfiles, saveProfile, uploadProfileImage,
      features, loadingFeatures, groupedFeatures, allCategories, featureModal,
      openNewFeature, saveFeature, createFeature, deleteFeature,
      contacts, loadingContacts, unreadCount, markRead, formatDate,
    }
  }
}
</script>

<style scoped>
.page-wrap { padding: 24px; max-width: 1200px; }

.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 28px; flex-wrap: wrap; gap: 16px; }
.page-header-left { display: flex; gap: 14px; align-items: center; }
.page-icon { font-size: 2rem; color: #2563eb; }
.page-title { font-size: 1.4rem; font-weight: 800; margin: 0; }
.page-sub   { color: #64748b; font-size: .88rem; margin: 0; }
.btn-preview {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 18px; border: 1.5px solid #2563eb; color: #2563eb;
  border-radius: 8px; font-size: .88rem; font-weight: 600; text-decoration: none;
  transition: all .2s;
}
.btn-preview:hover { background: #2563eb; color: #fff; }

/* TABS */
.tabs-wrap { display: flex; gap: 4px; margin-bottom: 24px; border-bottom: 2px solid #e2e8f0; }
.tab-btn {
  padding: 10px 18px; border: none; background: none; font-size: .9rem;
  font-weight: 600; color: #64748b; cursor: pointer; border-bottom: 2px solid transparent;
  margin-bottom: -2px; border-radius: 6px 6px 0 0; transition: all .2s; position: relative;
  display: flex; align-items: center; gap: 6px;
}
.tab-btn:hover  { color: #2563eb; background: #eff6ff; }
.tab-btn.active { color: #2563eb; border-bottom-color: #2563eb; background: #eff6ff; }
.tab-badge {
  background: #ef4444; color: #fff; border-radius: 10px;
  padding: 1px 7px; font-size: .7rem; font-weight: 700;
}

.tab-content { animation: fadeInTab .25s ease; }
@keyframes fadeInTab { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }

/* LOADING */
.loading-state { display: flex; align-items: center; gap: 12px; padding: 40px; color: #64748b; }
.spinner {
  width: 22px; height: 22px; border: 3px solid #e2e8f0;
  border-top-color: #2563eb; border-radius: 50%; animation: spin .6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* SECTION CARDS */
.section-card {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
  padding: 20px 24px; margin-bottom: 12px; transition: all .2s;
}
.section-card.inactive { opacity: .55; }
.section-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,.08); }
.section-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.sec-key { background: #f1f5f9; color: #2563eb; padding: 2px 8px; border-radius: 4px; font-size: .8rem; }
.sec-type-badge {
  background: #e0f2fe; color: #0284c7; border-radius: 10px;
  padding: 2px 10px; font-size: .72rem; font-weight: 600; margin-left: 8px;
}
.sec-actions { display: flex; align-items: center; gap: 12px; }
.btn-icon-sm {
  background: #eff6ff; border: none; color: #2563eb; width: 32px; height: 32px;
  border-radius: 8px; display: flex; align-items: center; justify-content: center; cursor: pointer;
}
.sec-title-preview { font-size: 1.05rem; font-weight: 700; margin: 0 0 4px; }
.sec-subtitle-preview { font-size: .88rem; color: #64748b; margin: 0; }
.sec-image-preview img { height: 60px; border-radius: 6px; margin-top: 10px; object-fit: cover; }

.toggle-wrap { position: relative; display: inline-flex; align-items: center; cursor: pointer; }
.toggle-wrap input { opacity: 0; width: 0; height: 0; position: absolute; }
.toggle-slider {
  width: 40px; height: 22px; background: #cbd5e1; border-radius: 20px; transition: .25s;
}
.toggle-slider::after {
  content: ""; position: absolute; width: 16px; height: 16px;
  background: #fff; border-radius: 50%; top: 3px; left: 3px; transition: .25s;
}
.toggle-wrap input:checked + .toggle-slider { background: #2563eb; }
.toggle-wrap input:checked + .toggle-slider::after { transform: translateX(18px); }

.btn-add-section {
  display: inline-flex; align-items: center; gap: 8px;
  background: #2563eb; color: #fff; border: none;
  padding: 10px 20px; border-radius: 8px; font-weight: 600; cursor: pointer;
  margin-top: 8px; transition: all .2s;
}
.btn-add-section:hover { background: #1d4ed8; }

/* PROFILES */
.profiles-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 20px; }
.profile-edit-card {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 14px;
  overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,.06);
}
.profile-img-area { position: relative; }
.profile-thumb { width: 100%; height: 160px; object-fit: cover; }
.profile-thumb-placeholder {
  width: 100%; height: 160px; background: linear-gradient(135deg, #2563eb, #6366f1);
  display: flex; align-items: center; justify-content: center;
  font-size: 3.5rem; color: rgba(255,255,255,.8);
}
.btn-upload-img {
  position: absolute; bottom: 10px; right: 10px;
  background: rgba(0,0,0,.65); color: #fff;
  padding: 6px 12px; border-radius: 6px; font-size: .8rem; cursor: pointer;
  display: flex; align-items: center; transition: background .2s;
}
.btn-upload-img:hover { background: rgba(0,0,0,.85); }
.profile-edit-body { padding: 18px; }
.profile-edit-name { font-size: 1.05rem; font-weight: 700; margin-bottom: 14px; }
.btn-save-profile {
  background: #2563eb; color: #fff; border: none;
  padding: 8px 18px; border-radius: 8px; font-weight: 600; cursor: pointer;
  font-size: .88rem; margin-top: 12px; transition: all .2s;
  display: inline-flex; align-items: center; gap: 6px;
}
.btn-save-profile:hover { background: #1d4ed8; }

/* FEATURES TABLE */
.features-toolbar { margin-bottom: 16px; }
.btn-add-feature {
  display: inline-flex; align-items: center; gap: 6px;
  background: #10b981; color: #fff; border: none;
  padding: 9px 18px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: .88rem;
}
.features-table-wrap { overflow-x: auto; border-radius: 12px; border: 1px solid #e2e8f0; }
.features-table { width: 100%; border-collapse: collapse; background: #fff; }
.features-table thead th {
  background: #1e293b; color: #fff; padding: 12px 14px;
  font-size: .82rem; font-weight: 700; text-align: left;
}
.group-header-row td {
  background: #2563eb; color: #fff; padding: 8px 14px;
  font-size: .8rem; font-weight: 700; text-transform: uppercase;
}
.cat-chip {
  background: #eff6ff; color: #2563eb; padding: 2px 8px;
  border-radius: 4px; font-size: .78rem; font-weight: 600;
}
.tbl-input {
  width: 100%; border: 1px solid #e2e8f0; border-radius: 6px;
  padding: 5px 8px; font-size: .85rem; color: #1e293b; background: #f8fafc;
}
.tbl-input:focus { border-color: #2563eb; outline: none; background: #fff; }
.tbl-val { width: 80px; text-align: center; }
.features-table td { padding: 8px 10px; border-bottom: 1px solid #f1f5f9; }
.btn-del-feat {
  background: #fee2e2; border: none; color: #ef4444; width: 30px; height: 30px;
  border-radius: 6px; cursor: pointer; display: flex; align-items: center; justify-content: center;
}
.btn-del-feat:hover { background: #ef4444; color: #fff; }

/* CONTACTS */
.empty-state { text-align: center; padding: 60px; }
.contact-msg-card {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
  padding: 20px 24px; margin-bottom: 12px; transition: all .2s;
}
.contact-msg-card.unread { border-left: 4px solid #2563eb; background: #eff6ff; }
.msg-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 8px; }
.msg-company { color: #64748b; font-size: .9rem; }
.badge-new {
  background: #2563eb; color: #fff; border-radius: 10px;
  padding: 2px 10px; font-size: .72rem; font-weight: 700; margin-left: 8px;
}
.msg-date { color: #94a3b8; font-size: .82rem; }
.msg-meta { display: flex; gap: 20px; color: #64748b; font-size: .85rem; margin-bottom: 12px; flex-wrap: wrap; }
.msg-body {
  background: #f8fafc; border-radius: 8px; padding: 12px 16px;
  color: #334155; font-size: .9rem; line-height: 1.6; margin-bottom: 12px;
  white-space: pre-wrap;
}
.msg-footer { display: flex; align-items: center; }
.btn-mark-read {
  background: #10b981; color: #fff; border: none;
  padding: 7px 16px; border-radius: 8px; font-size: .82rem; font-weight: 600;
  cursor: pointer; display: flex; align-items: center;
}
.msg-read-tag { color: #10b981; font-size: .82rem; font-weight: 600; }

/* MODAL */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.55);
  display: flex; align-items: center; justify-content: center; z-index: 2000;
  padding: 16px;
}
.modal-box {
  background: #fff; border-radius: 16px; width: 100%; max-width: 560px;
  max-height: 90vh; overflow-y: auto; box-shadow: 0 24px 60px rgba(0,0,0,.25);
}
.modal-box.modal-lg { max-width: 720px; }
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 20px 24px; border-bottom: 1px solid #e2e8f0;
}
.modal-header h5 { margin: 0; font-size: 1rem; font-weight: 700; }
.btn-close-modal { background: none; border: none; font-size: 1.2rem; cursor: pointer; color: #64748b; }
.modal-body { padding: 24px; display: flex; flex-direction: column; gap: 16px; }
.modal-footer {
  padding: 16px 24px; border-top: 1px solid #e2e8f0;
  display: flex; justify-content: flex-end; gap: 10px;
}

/* FORM CONTROLS */
.form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.form-row-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.form-group { display: flex; flex-direction: column; gap: 5px; }
.form-group label { font-size: .82rem; font-weight: 600; color: #475569; }
.hint { color: #94a3b8; font-weight: 400; font-size: .75rem; }
.form-ctrl-sm {
  border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 12px;
  font-size: .88rem; color: #1e293b; transition: border-color .2s;
}
.form-ctrl-sm:focus { outline: none; border-color: #2563eb; }
.form-ctrl-sm:disabled { background: #f1f5f9; color: #94a3b8; }
.form-textarea-sm { resize: vertical; min-height: 80px; }
.form-check-group { justify-content: flex-end; }
.check-label {
  display: flex; align-items: center; gap: 8px;
  font-size: .88rem; color: #475569; cursor: pointer; margin-top: 22px;
}
.color-input-wrap { display: flex; align-items: center; gap: 8px; }
.color-picker { width: 40px; height: 36px; border: none; border-radius: 6px; cursor: pointer; padding: 2px; }
.image-input-row { display: flex; gap: 10px; align-items: center; }
.btn-upload-inline {
  display: inline-flex; align-items: center; gap: 4px;
  background: #eff6ff; border: 1px solid #bfdbfe; color: #2563eb;
  padding: 7px 14px; border-radius: 8px; font-size: .82rem; font-weight: 600;
  cursor: pointer; white-space: nowrap;
}
.image-preview-sm { max-height: 80px; border-radius: 6px; display: block; }

.btn-cancel {
  padding: 9px 20px; border: 1.5px solid #e2e8f0; background: none;
  color: #64748b; border-radius: 8px; font-weight: 600; cursor: pointer;
}
.btn-save {
  padding: 9px 24px; background: #2563eb; color: #fff; border: none;
  border-radius: 8px; font-weight: 700; cursor: pointer; transition: all .2s;
  display: flex; align-items: center; gap: 6px;
}
.btn-save:hover { background: #1d4ed8; }
.btn-save:disabled { opacity: .6; cursor: not-allowed; }
</style>
