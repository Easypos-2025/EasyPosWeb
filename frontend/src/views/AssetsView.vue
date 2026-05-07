<template>
  <div class="p-3">

    <!-- FILTROS -->
    <div class="card p-3 mt-3">
      <div class="row g-2 align-items-end">
        <div class="col-md-3 col-12">
          <input type="text" class="form-control" :placeholder="`Buscar ${moduleName}...`" v-model="search" />
        </div>
        <div class="col-md-2 col-6">
          <select class="form-select" v-model="filterCategory">
            <option value="">Todas las categorías</option>
            <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
        <div class="col-md-2 col-6">
          <select class="form-select" v-model="filterClient">
            <option value="">Todos los clientes</option>
            <option v-for="c in clients" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
        <div class="col-md-2 col-6">
          <select class="form-select" v-model="filterStatus">
            <option value="">Todos</option>
            <option value="1">Vigente</option>
            <option value="0">Inactivo</option>
          </select>
        </div>
        <div class="col-md-3 col-12 text-end">
          <button class="btn btn-primary btn-nuevo-activo" @click="openCreate">
            <i class="bi bi-plus-lg"></i> Nuevo {{ moduleName }}
          </button>
        </div>
      </div>
    </div>

    <!-- TABLA DESKTOP -->
    <div class="card p-3 mt-3 table-responsive desktop-table">
      <table class="table table-hover align-middle">
        <thead>
          <tr>
            <th style="width:80px">Cód.</th>
            <th>Nombre</th>
            <th>Categoría</th>
            <th>Canon</th>
            <th style="width:90px">Venta</th>
            <th style="width:90px">Estado</th>
            <th style="width:150px; white-space:nowrap">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in filtered" :key="a.id">
            <td><span class="code-badge">{{ a.list_code ?? '—' }}</span></td>
            <td>
              <div class="fw-600">{{ a.name }}</div>
              <div v-if="a.short_name" class="text-muted small">{{ a.short_name }}</div>
            </td>
            <td>{{ a.category_name || categoryName(a.category_id) }}</td>
            <td>{{ a.canon_value != null ? fmt(a.canon_value) : '—' }}</td>
            <td>
              <span v-if="a.has_sale_option" class="badge bg-success">Sí</span>
              <span v-else class="badge bg-light text-secondary">No</span>
            </td>
            <td>
              <span :class="['badge', a.is_active ? 'bg-primary' : 'bg-secondary']">
                {{ a.is_active ? 'Vigente' : 'Inactivo' }}
              </span>
            </td>
            <td style="white-space:nowrap">
              <button class="btn btn-warning btn-sm me-1" @click="openEdit(a)">
                <i class="bi bi-pencil"></i> Editar
              </button>
              <button class="btn btn-danger btn-sm" @click="handleDelete(a)">
                <i class="bi bi-trash"></i>
              </button>
            </td>
          </tr>
          <tr v-if="filtered.length === 0">
            <td colspan="7" class="text-center text-muted py-4">No hay resultados</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- TARJETAS MÓVIL -->
    <div class="mobile-list mt-3">
      <div v-for="a in filtered" :key="a.id" class="asset-mobile-card">
        <div class="amc-header">
          <div>
            <span class="amc-name">{{ a.name }}</span>
            <span v-if="a.short_name" class="amc-shortname">{{ a.short_name }}</span>
          </div>
          <div class="d-flex gap-1 align-items-center flex-shrink-0">
            <span v-if="a.list_code" class="amc-code">#{{ a.list_code }}</span>
            <span class="amc-cat">{{ a.category_name || categoryName(a.category_id) }}</span>
          </div>
        </div>
        <div class="amc-row" v-if="a.canon_value != null">
          <i class="bi bi-cash"></i>
          <span>Canon: <strong>{{ fmt(a.canon_value) }}</strong></span>
        </div>
        <div class="amc-row" v-if="a.address || a.location">
          <i class="bi bi-geo-alt"></i>
          <span>{{ a.address || a.location }}</span>
        </div>
        <div class="amc-row" v-if="a.client_name">
          <i class="bi bi-person"></i>
          <span>{{ a.client_name }}</span>
        </div>
        <div class="amc-footer">
          <span v-if="a.has_sale_option" class="badge bg-success">Opción de Venta</span>
          <span :class="['badge', a.is_active ? 'bg-primary' : 'bg-secondary']">
            {{ a.is_active ? 'Vigente' : 'Inactivo' }}
          </span>
          <div class="amc-actions">
            <button class="btn btn-warning btn-sm" @click="openEdit(a)">
              <i class="bi bi-pencil"></i> Editar
            </button>
            <button class="btn btn-danger btn-sm" @click="handleDelete(a)">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </div>
      </div>
      <div v-if="filtered.length === 0" class="mobile-empty">
        <i class="bi bi-box-seam" style="font-size:28px;display:block;margin-bottom:8px"></i>
        No hay resultados
      </div>
    </div>

    <!-- MODAL CREAR / EDITAR -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-box">
        <div class="modal-header-bar">
          <h2>{{ editForm.id ? `Editar ${moduleName}` : `Nuevo ${moduleName}` }}</h2>
          <div class="header-actions-row">
            <button
              v-if="editForm.id && editForm.list_code"
              class="btn-qr"
              @click="openQr"
              title="Ver / Descargar QR"
            >
              <i class="bi bi-qr-code"></i> QR
            </button>
            <button class="btn-close-sm" @click="closeModal"><i class="bi bi-x-lg"></i></button>
          </div>
        </div>

        <!-- TABS -->
        <div class="tab-nav">
          <button :class="['tab-btn', activeTab === 'general' && 'active']" @click="activeTab = 'general'">
            <i class="bi bi-house"></i> General
          </button>
          <button :class="['tab-btn', activeTab === 'valores' && 'active']" @click="activeTab = 'valores'">
            <i class="bi bi-cash-stack"></i> Valores
          </button>
          <button :class="['tab-btn', activeTab === 'legal' && 'active']" @click="activeTab = 'legal'">
            <i class="bi bi-file-earmark-text"></i> Legal
          </button>
          <button
            :class="['tab-btn', activeTab === 'fotos' && 'active']"
            :disabled="!editForm.id"
            :title="!editForm.id ? 'Guarda el activo primero' : 'Fotos y videos'"
            @click="activeTab = 'fotos'"
          >
            <i class="bi bi-images"></i> Fotos
          </button>
        </div>

        <div class="modal-body-area">

          <!-- TAB GENERAL -->
          <template v-if="activeTab === 'general'">
            <div class="row g-2">
              <div class="col-8">
                <div class="fg">
                  <label>Nombre *</label>
                  <input v-model="editForm.name" data-v="name" class="form-control" @input="clearError($event)" />
                </div>
              </div>
              <div class="col-4">
                <div class="fg">
                  <label>Nombre corto</label>
                  <input v-model="editForm.short_name" class="form-control" placeholder="Alias" />
                </div>
              </div>
            </div>
            <div class="fg">
              <label>Categoría *</label>
              <select v-model="editForm.category_id" data-v="category" class="form-select" @change="clearError($event)">
                <option value="">— Seleccionar —</option>
                <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            <div class="row g-2">
              <div class="col-6">
                <div class="fg">
                  <label>Propietario</label>
                  <select v-model="editForm.owner_id" class="form-select">
                    <option :value="null">— Sin propietario —</option>
                    <option v-for="c in clients" :key="c.id" :value="c.id">{{ c.name }}</option>
                  </select>
                </div>
              </div>
              <div class="col-6">
                <div class="fg">
                  <label>Arrendatario</label>
                  <select v-model="editForm.client_id" class="form-select">
                    <option :value="null">— Sin arrendatario —</option>
                    <option v-for="c in clients" :key="c.id" :value="c.id">{{ c.name }}</option>
                  </select>
                </div>
              </div>
            </div>
            <div class="row g-2">
              <div class="col-6">
                <div class="fg">
                  <label>Teléfono</label>
                  <input v-model="editForm.phone" class="form-control" placeholder="Ej: 300 000 0000" />
                </div>
              </div>
              <div class="col-6">
                <div class="fg">
                  <label>Sector</label>
                  <input v-model.number="editForm.sector_id" type="number" class="form-control" placeholder="ID de sector" />
                </div>
              </div>
            </div>
            <div class="fg">
              <label>Dirección</label>
              <input v-model="editForm.address" class="form-control" placeholder="Calle / Carrera / Avenida..." />
            </div>
            <div class="fg">
              <label>Ubicación / Ciudad</label>
              <input v-model="editForm.location" class="form-control" placeholder="Ciudad, Municipio..." />
            </div>
            <div class="fg">
              <label>Descripción</label>
              <textarea v-model="editForm.description" class="form-control" rows="3" />
            </div>
          </template>

          <!-- TAB VALORES -->
          <template v-if="activeTab === 'valores'">
            <div class="fg">
              <label>Valor Canon (arriendo)</label>
              <input v-model.number="editForm.canon_value" type="number" min="0" step="1000" class="form-control" placeholder="0" />
              <span v-if="editForm.canon_value" class="hint-fmt">{{ fmt(editForm.canon_value) }}</span>
            </div>
            <div class="check-row">
              <input type="checkbox" id="chk-venta" v-model="editForm.has_sale_option" :true-value="1" :false-value="0" class="form-check-input" />
              <label for="chk-venta" class="check-label">¿Tiene Opción de Venta?</label>
            </div>
            <div class="fg">
              <label>Valor Venta</label>
              <input v-model.number="editForm.sale_price" type="number" min="0" step="1000" class="form-control" placeholder="0" />
              <span v-if="editForm.sale_price" class="hint-fmt">{{ fmt(editForm.sale_price) }}</span>
            </div>
            <div class="row g-2">
              <div class="col-6">
                <div class="fg">
                  <label>Avalúo Catastral</label>
                  <input v-model.number="editForm.cadastral_value" type="number" min="0" class="form-control" placeholder="0" />
                  <span v-if="editForm.cadastral_value" class="hint-fmt">{{ fmt(editForm.cadastral_value) }}</span>
                </div>
              </div>
              <div class="col-6">
                <div class="fg">
                  <label>Avalúo Comercial</label>
                  <input v-model.number="editForm.commercial_value" type="number" min="0" class="form-control" placeholder="0" />
                  <span v-if="editForm.commercial_value" class="hint-fmt">{{ fmt(editForm.commercial_value) }}</span>
                </div>
              </div>
            </div>
            <div class="row g-2">
              <div class="col-6">
                <div class="fg">
                  <label>Año Avalúo</label>
                  <input v-model.number="editForm.appraisal_year" type="number" min="1990" :max="currentYear" class="form-control" placeholder="2024" />
                </div>
              </div>
              <div class="col-6">
                <div class="fg">
                  <label>Tipo Adquisición</label>
                  <select v-model="editForm.acquisition_type" class="form-select">
                    <option value="">— Seleccionar —</option>
                    <option>Compra</option>
                    <option>Herencia</option>
                    <option>Donación</option>
                    <option>Permuta</option>
                    <option>Remate</option>
                    <option>Otro</option>
                  </select>
                </div>
              </div>
            </div>
          </template>

          <!-- TAB LEGAL -->
          <template v-if="activeTab === 'legal'">
            <div class="row g-2">
              <div class="col-6">
                <div class="fg">
                  <label>Código de Lista</label>
                  <input v-model.number="editForm.list_code" type="number" class="form-control" placeholder="Único por activo" />
                </div>
              </div>
              <div class="col-6">
                <div class="fg">
                  <label>Matrícula</label>
                  <input v-model="editForm.registration" class="form-control" placeholder="Nro. matrícula inmobiliaria" />
                </div>
              </div>
            </div>
            <div class="fg">
              <label>Número de Predio</label>
              <input v-model="editForm.property_number" class="form-control" placeholder="Número catastral del predio" />
            </div>
            <div class="fg">
              <label>Referencia Adicional</label>
              <input v-model="editForm.additional_reference" class="form-control" placeholder="Datos adicionales de identificación" />
            </div>
            <div class="check-row">
              <input type="checkbox" id="chk-rented" v-model="editForm.is_rented" :true-value="1" :false-value="0" class="form-check-input" />
              <label for="chk-rented" class="check-label">¿Actualmente arrendada?</label>
            </div>
            <div class="check-row">
              <input type="checkbox" id="chk-active" v-model="editForm.is_active" :true-value="1" :false-value="0" class="form-check-input" />
              <label for="chk-active" class="check-label">¿Vigente / Activa?</label>
            </div>
          </template>

          <!-- TAB FOTOS -->
          <template v-if="activeTab === 'fotos'">
            <AssetMediaGallery v-if="editForm.id" :asset-id="editForm.id" />
          </template>

        </div>

        <div class="modal-footer-bar">
          <button class="btn btn-secondary" @click="closeModal">Cancelar</button>
          <button class="btn btn-primary" @click="save" :disabled="saving">
            {{ saving ? 'Guardando...' : 'Guardar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL QR -->
    <div v-if="showQr" class="modal-overlay" @click.self="showQr = false">
      <div class="qr-modal-box">

        <!-- Header -->
        <div class="qr-modal-header">
          <div>
            <h3><i class="bi bi-qr-code"></i> Activo #{{ editForm.list_code }}</h3>
            <p class="qr-url-text">{{ qrUrl }}</p>
          </div>
          <button class="btn-close-sm" @click="showQr = false"><i class="bi bi-x-lg"></i></button>
        </div>

        <!-- Tabs -->
        <div class="qr-tabs">
          <button :class="['qr-tab', qrTab === 'code' && 'active']" @click="qrTab = 'code'">
            <i class="bi bi-qr-code-scan"></i> Código QR
          </button>
          <button :class="['qr-tab', qrTab === 'preview' && 'active']" @click="switchPreview">
            <i class="bi bi-phone"></i> Vista previa
          </button>
        </div>

        <!-- Tab: QR Code -->
        <div v-if="qrTab === 'code'" class="qr-tab-body">
          <div class="qr-canvas-wrap">
            <canvas ref="qrCanvas" class="qr-canvas"></canvas>
          </div>
          <div class="qr-actions">
            <button class="btn btn-outline-secondary btn-sm" @click="copyUrl">
              <i class="bi" :class="urlCopied ? 'bi-check-lg' : 'bi-clipboard'"></i>
              {{ urlCopied ? 'Copiado' : 'Copiar URL' }}
            </button>
            <button class="btn btn-primary btn-sm" @click="downloadQr">
              <i class="bi bi-download"></i> Descargar PNG
            </button>
          </div>
        </div>

        <!-- Tab: Vista Previa -->
        <div v-if="qrTab === 'preview'" class="qr-tab-body qr-preview-body">
          <div v-if="previewLoading" class="preview-loading">
            <div class="preview-spinner"></div>
            <span>Cargando vista previa...</span>
          </div>
          <template v-else-if="previewData">
            <div class="phone-frame">
              <div class="phone-screen">

                <!-- Brand bar -->
                <div class="pp-header">
                  <span class="pp-brand">
                    <span style="color:#2563eb">Easy</span><span style="color:#f59e0b">Pos</span><span style="color:#10b981">Web</span>
                  </span>
                  <span v-if="previewData.list_code" class="pp-code">#{{ previewData.list_code }}</span>
                </div>

                <!-- Foto principal -->
                <div class="pp-photo-wrap">
                  <img
                    v-if="previewData.media && previewData.media.length && previewData.media[0].file_type === 'image'"
                    :src="previewData.media[0].file_url"
                    class="pp-photo"
                  />
                  <div v-else class="pp-no-photo">
                    <i class="bi bi-house-door" style="font-size:32px;color:#cbd5e1"></i>
                    <span>Sin fotos</span>
                  </div>
                  <span v-if="previewData.media && previewData.media.length > 1" class="pp-photo-count">
                    <i class="bi bi-images"></i> {{ previewData.media.length }}
                  </span>
                </div>

                <!-- Info -->
                <div class="pp-body">
                  <span class="pp-cat">{{ previewData.category_name }}</span>
                  <div class="pp-name">{{ previewData.name }}</div>
                  <div v-if="previewData.short_name" class="pp-short">{{ previewData.short_name }}</div>
                  <div v-if="previewData.address || previewData.location" class="pp-location">
                    <i class="bi bi-geo-alt-fill"></i>
                    {{ previewData.address || previewData.location }}
                  </div>

                  <!-- Valores -->
                  <div class="pp-values">
                    <div v-if="previewData.canon_value != null" class="pp-val-card green">
                      <span class="pp-val-lbl">Canon</span>
                      <span class="pp-val-amt">{{ fmt(previewData.canon_value) }}<span class="pp-val-per">/mes</span></span>
                    </div>
                    <div v-if="previewData.has_sale_option" class="pp-val-card yellow">
                      <i class="bi bi-tag-fill"></i>
                      <span class="pp-val-lbl">Opción de Venta</span>
                    </div>
                  </div>

                  <!-- Estado -->
                  <div class="pp-badges">
                    <span v-if="previewData.is_rented" class="pp-badge pp-rented">Ocupado</span>
                    <span v-else class="pp-badge pp-free">Disponible</span>
                  </div>

                  <!-- Descripción snippet -->
                  <p v-if="previewData.description" class="pp-desc">{{ previewData.description.substring(0,120) }}{{ previewData.description.length > 120 ? '...' : '' }}</p>

                  <!-- Formulario placeholder -->
                  <div class="pp-form-placeholder">
                    <i class="bi bi-chat-dots-fill"></i>
                    <span>Formulario de contacto disponible</span>
                  </div>
                </div>

              </div>
            </div>
            <p class="preview-hint">
              <i class="bi bi-info-circle"></i>
              Esta es una representación de lo que verán los interesados al escanear el QR.
            </p>
          </template>
        </div>

        <!-- Footer siempre visible -->
        <div class="qr-modal-footer">
          <button class="btn btn-secondary btn-sm" @click="showQr = false">Cerrar</button>
          <a :href="qrUrl" target="_blank" class="btn btn-outline-primary btn-sm">
            <i class="bi bi-box-arrow-up-right"></i> Abrir página
          </a>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import { validateForm } from "@/utils/validate"
import { useModuleName } from "@/composables/useModuleName"
import AssetMediaGallery from "@/components/AssetMediaGallery.vue"
import QRCode from "qrcode"

const { moduleName } = useModuleName()

const currentYear = new Date().getFullYear()

const assets        = ref([])
const categories    = ref([])
const clients       = ref([])
const search        = ref("")
const filterCategory = ref("")
const filterClient  = ref("")
const filterStatus  = ref("")
const showModal     = ref(false)
const saving        = ref(false)
const activeTab     = ref("general")
const editForm      = ref({})
const showQr        = ref(false)
const qrCanvas      = ref(null)
const qrUrl         = ref("")
const qrTab         = ref("code")
const urlCopied     = ref(false)
const previewData   = ref(null)
const previewLoading = ref(false)

const EMPTY_FORM = () => ({
  id: null, name: "", short_name: "", category_id: "", client_id: null, owner_id: null,
  description: "", location: "", address: "", phone: "", sector_id: null,
  is_rented: 0, is_active: 1, has_sale_option: 0,
  canon_value: null, cadastral_value: null, commercial_value: null, sale_price: null,
  appraisal_year: null, acquisition_type: "", registration: "", property_number: "",
  additional_reference: "", list_code: null,
})

const filtered = computed(() =>
  assets.value.filter(a => {
    const matchSearch   = (a.name || "").toLowerCase().includes(search.value.toLowerCase()) ||
                          String(a.list_code || "").includes(search.value)
    const matchCategory = !filterCategory.value || a.category_id === filterCategory.value
    const matchClient   = !filterClient.value   || a.client_id   === filterClient.value
    const matchStatus   = filterStatus.value === "" || String(a.is_active) === filterStatus.value
    return matchSearch && matchCategory && matchClient && matchStatus
  })
)

function fmt(val) {
  if (val == null || val === "") return "—"
  return new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(val)
}

function categoryName(id) {
  return categories.value.find(c => c.id === id)?.name || "—"
}

async function load() {
  try {
    const [aRes, cRes, clRes] = await Promise.all([
      api.get("/assets/"),
      api.get("/asset-categories/"),
      api.get("/clients"),
    ])
    assets.value     = aRes.data
    categories.value = cRes.data
    clients.value    = clRes.data.filter(c => c.is_active)
  } catch {
    showToast("Error cargando activos", "error")
  }
}

function openCreate() {
  editForm.value = EMPTY_FORM()
  activeTab.value = "general"
  showModal.value = true
}

function openEdit(a) {
  editForm.value  = { ...a }
  activeTab.value = "general"
  showModal.value = true
}

function closeModal() {
  document.querySelectorAll(".field-invalid").forEach(el => el.classList.remove("field-invalid"))
  showModal.value = false
}

function clearError(e) {
  e.target.classList.remove("field-invalid")
}

async function save() {
  const f = editForm.value
  const check = validateForm([
    { value: f.name,        selector: '[data-v="name"]',     label: "Nombre" },
    { value: f.category_id, selector: '[data-v="category"]', label: "Categoría" },
  ])
  if (!check.valid) { showToast(check.message, "warning"); activeTab.value = "general"; return }

  saving.value = true
  try {
    if (f.id) {
      await api.put(`/assets/${f.id}`, f)
      showToast("Activo actualizado", "success")
    } else {
      await api.post("/assets/", f)
      showToast("Activo creado", "success")
    }
    closeModal()
    await load()
  } catch (e) {
    const msg = e.response?.data?.detail || "Error guardando activo"
    showToast(msg, "error")
    if (msg.includes("Código de Lista")) activeTab.value = "legal"
  } finally {
    saving.value = false
  }
}

async function handleDelete(a) {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar "${a.name}"?`,
    text: "Esta acción no se puede deshacer.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, eliminar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/assets/${a.id}`)
    showToast("Activo eliminado", "success")
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error eliminando activo", "error")
  }
}

async function openQr() {
  qrUrl.value     = `${window.location.origin}/activo/${editForm.value.list_code}`
  qrTab.value     = "code"
  previewData.value = null
  urlCopied.value = false
  showQr.value    = true
  await nextTick()
  await renderQr()
}

async function renderQr() {
  await nextTick()
  if (qrCanvas.value) {
    await QRCode.toCanvas(qrCanvas.value, qrUrl.value, {
      width: 260, margin: 2,
      color: { dark: "#1e293b", light: "#ffffff" },
    })
  }
}

async function switchPreview() {
  qrTab.value = "preview"
  if (previewData.value) return
  previewLoading.value = true
  try {
    const res = await api.get(`/public/activo/${editForm.value.list_code}`)
    previewData.value = res.data
  } catch {
    showToast("Error cargando vista previa", "error")
  } finally {
    previewLoading.value = false
  }
}

async function copyUrl() {
  try {
    await navigator.clipboard.writeText(qrUrl.value)
    urlCopied.value = true
    setTimeout(() => { urlCopied.value = false }, 2000)
  } catch {
    showToast("No se pudo copiar", "error")
  }
}

function downloadQr() {
  if (!qrCanvas.value) return
  const link = document.createElement("a")
  link.download = `qr-activo-${editForm.value.list_code}.png`
  link.href = qrCanvas.value.toDataURL("image/png")
  link.click()
}

onMounted(load)
</script>

<style scoped>
/* ── Modal ── */
.modal-overlay  { position: fixed; inset: 0; background: rgba(0,0,0,0.45); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-box      { background: #fff; border-radius: 16px; width: 580px; max-width: 95vw; max-height: 92vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
.modal-header-bar { display: flex; align-items: center; justify-content: space-between; padding: 18px 24px 0; flex-shrink: 0; }
.modal-header-bar h2 { font-size: 17px; font-weight: 700; color: #1e293b; margin: 0; }
.modal-body-area  { padding: 16px 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
.modal-footer-bar { padding: 14px 24px 18px; display: flex; justify-content: flex-end; gap: 10px; border-top: 1px solid #f1f5f9; flex-shrink: 0; }
.btn-close-sm { background: none; border: none; font-size: 18px; cursor: pointer; color: #94a3b8; border-radius: 6px; padding: 4px 8px; }
.btn-close-sm:hover { background: #f1f5f9; color: #1e293b; }

/* ── Tabs ── */
.tab-nav { display: flex; gap: 2px; padding: 12px 24px 0; border-bottom: 1px solid #e2e8f0; flex-shrink: 0; }
.tab-btn { background: none; border: none; border-bottom: 2px solid transparent; padding: 8px 14px; font-size: 13px; font-weight: 600; color: #64748b; cursor: pointer; margin-bottom: -1px; display: flex; align-items: center; gap: 6px; border-radius: 6px 6px 0 0; transition: color .15s; }
.tab-btn:hover { color: #1e293b; }
.tab-btn.active { color: #2563eb; border-bottom-color: #2563eb; background: #eff6ff; }
.tab-btn:disabled { opacity: .4; cursor: not-allowed; }

/* ── Header actions ── */
.header-actions-row { display: flex; align-items: center; gap: 8px; }
.btn-qr {
  display: flex; align-items: center; gap: 5px;
  background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px;
  color: #15803d; font-size: 13px; font-weight: 600; padding: 5px 12px;
  cursor: pointer; transition: background .15s;
}
.btn-qr:hover { background: #dcfce7; }

/* ── QR Modal ── */
.qr-modal-box {
  background: #fff; border-radius: 16px; width: 420px; max-width: 95vw; max-height: 92vh;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
  display: flex; flex-direction: column; overflow: hidden;
}
.qr-modal-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  padding: 16px 20px 10px; flex-shrink: 0;
}
.qr-modal-header h3 { font-size: 15px; font-weight: 700; margin: 0 0 3px; color: #1e293b; display: flex; align-items: center; gap: 7px; }
.qr-modal-header h3 .bi { color: #10b981; }
.qr-url-text { font-size: 11px; color: #64748b; margin: 0; word-break: break-all; }

.qr-tabs { display: flex; border-bottom: 1px solid #e2e8f0; flex-shrink: 0; padding: 0 8px; }
.qr-tab { flex: 1; background: none; border: none; border-bottom: 2px solid transparent; padding: 9px; font-size: 13px; font-weight: 600; color: #64748b; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px; margin-bottom: -1px; transition: color .15s; }
.qr-tab:hover { color: #1e293b; }
.qr-tab.active { color: #2563eb; border-bottom-color: #2563eb; }

.qr-tab-body { flex: 1; overflow-y: auto; }
.qr-canvas-wrap { display: flex; justify-content: center; padding: 16px 0 8px; }
.qr-canvas { border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,.1); }
.qr-actions { display: flex; justify-content: center; gap: 10px; padding: 8px 16px 16px; }

/* Preview tab */
.qr-preview-body { background: #f1f5f9; padding: 12px; display: flex; flex-direction: column; align-items: center; gap: 10px; }

.preview-loading { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 40px; color: #64748b; font-size: 14px; }
.preview-spinner { width: 32px; height: 32px; border: 3px solid #e2e8f0; border-top-color: #3b82f6; border-radius: 50%; animation: spin .7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Phone frame mockup */
.phone-frame {
  width: 240px; background: #1e293b; border-radius: 28px;
  padding: 10px 8px; box-shadow: 0 8px 32px rgba(0,0,0,.35);
}
.phone-screen { background: #f1f5f9; border-radius: 20px; overflow: hidden; max-height: 420px; overflow-y: auto; }

/* Public page miniature */
.pp-header { display: flex; align-items: center; justify-content: space-between; padding: 8px 10px 6px; background: #fff; }
.pp-brand  { font-size: 13px; font-weight: 800; }
.pp-code   { font-size: 10px; font-weight: 700; background: #eff6ff; color: #2563eb; padding: 2px 7px; border-radius: 20px; }

.pp-photo-wrap { position: relative; height: 110px; background: #f8fafc; }
.pp-photo      { width: 100%; height: 100%; object-fit: cover; }
.pp-no-photo   { height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; color: #94a3b8; font-size: 11px; }
.pp-photo-count { position: absolute; bottom: 5px; right: 5px; background: rgba(0,0,0,.55); color: #fff; font-size: 10px; padding: 2px 6px; border-radius: 6px; display: flex; align-items: center; gap: 3px; }

.pp-body { padding: 8px 10px 10px; display: flex; flex-direction: column; gap: 4px; }
.pp-cat  { font-size: 9px; font-weight: 700; background: #eff6ff; color: #1e40af; padding: 1px 7px; border-radius: 20px; align-self: flex-start; }
.pp-name { font-size: 13px; font-weight: 800; color: #1e293b; }
.pp-short { font-size: 10px; color: #64748b; }
.pp-location { font-size: 10px; color: #64748b; display: flex; align-items: flex-start; gap: 3px; }
.pp-location .bi { color: #3b82f6; font-size: 10px; flex-shrink: 0; margin-top: 1px; }

.pp-values { display: flex; gap: 5px; flex-wrap: wrap; margin-top: 4px; }
.pp-val-card { flex: 1; min-width: 80px; border-radius: 7px; padding: 6px 7px; display: flex; flex-direction: column; gap: 1px; }
.pp-val-card.green  { background: #f0fdf4; border: 1px solid #bbf7d0; }
.pp-val-card.yellow { background: #fefce8; border: 1px solid #fde68a; flex-direction: row; align-items: center; gap: 4px; }
.pp-val-card.yellow .bi { color: #f59e0b; font-size: 11px; }
.pp-val-lbl  { font-size: 8px; font-weight: 700; color: #64748b; text-transform: uppercase; }
.pp-val-amt  { font-size: 11px; font-weight: 800; color: #15803d; }
.pp-val-per  { font-size: 8px; color: #64748b; font-weight: 400; }

.pp-badges { display: flex; gap: 4px; }
.pp-badge  { font-size: 9px; font-weight: 700; padding: 2px 7px; border-radius: 20px; }
.pp-free   { background: #f0fdf4; color: #15803d; }
.pp-rented { background: #fef3c7; color: #92400e; }

.pp-desc { font-size: 10px; color: #64748b; line-height: 1.4; margin: 2px 0 0; }
.pp-form-placeholder { margin-top: 6px; background: #eff6ff; border: 1px dashed #93c5fd; border-radius: 7px; padding: 7px 10px; font-size: 10px; color: #3b82f6; display: flex; align-items: center; gap: 5px; font-weight: 600; }

.preview-hint { font-size: 11px; color: #64748b; text-align: center; margin: 0; display: flex; align-items: flex-start; gap: 5px; max-width: 260px; line-height: 1.4; }

.qr-modal-footer {
  display: flex; justify-content: flex-end; gap: 8px;
  padding: 12px 20px 16px; border-top: 1px solid #f1f5f9; flex-shrink: 0;
}

/* ── Form fields ── */
.fg       { display: flex; flex-direction: column; gap: 4px; }
.fg label { font-size: 13px; font-weight: 500; color: #374151; }
.hint-fmt { font-size: 12px; color: #10b981; font-weight: 600; margin-top: 2px; }
.check-row  { display: flex; align-items: center; gap: 10px; padding: 6px 0; }
.check-label { font-size: 14px; font-weight: 500; color: #374151; cursor: pointer; margin: 0; }

/* ── Table extras ── */
.code-badge { background: #f1f5f9; color: #475569; font-size: 12px; font-weight: 700; padding: 2px 8px; border-radius: 6px; }
.fw-600 { font-weight: 600; }

/* ── RESPONSIVE ── */
.mobile-list  { display: none; }
.mobile-empty { padding: 40px; text-align: center; color: #94a3b8; font-size: 14px; }

@media (max-width: 768px) {
  .desktop-table { display: none; }
  .mobile-list   { display: flex; flex-direction: column; gap: 10px; }
  .modal-box { width: 95vw; }

  .asset-mobile-card {
    background: #fff;
    border-radius: 14px;
    box-shadow: 0 1px 6px rgba(0,0,0,.08);
    padding: 14px 16px;
  }
  .amc-header  { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 8px; gap: 8px; }
  .amc-name    { font-size: 15px; font-weight: 700; color: #1e293b; display: block; }
  .amc-shortname { font-size: 12px; color: #64748b; display: block; }
  .amc-code    { font-size: 11px; background: #f1f5f9; color: #475569; font-weight: 700; padding: 2px 7px; border-radius: 6px; white-space: nowrap; }
  .amc-cat     { font-size: 11px; background: #eff6ff; color: #1e40af; font-weight: 600; padding: 2px 9px; border-radius: 20px; white-space: nowrap; }
  .amc-row     { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #64748b; margin-bottom: 4px; }
  .amc-row .bi { color: #94a3b8; font-size: 13px; }
  .amc-footer  { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-top: 10px; padding-top: 10px; border-top: 1px solid #f1f5f9; }
  .amc-actions { display: flex; gap: 8px; margin-left: auto; }

  .tab-btn { padding: 7px 10px; font-size: 12px; }
}

@media (max-width: 576px) {
  .tab-nav { gap: 0; padding: 10px 12px 0; }
  .tab-btn { padding: 7px 8px; font-size: 11px; }
  .tab-btn .bi { display: none; }
  .btn-nuevo-activo { width: 100%; }
  .amc-footer { flex-direction: column; align-items: flex-start; }
  .amc-actions { margin-left: 0; width: 100%; }
  .amc-actions .btn { flex: 1; }
}
</style>
