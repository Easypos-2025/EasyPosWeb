<template>
  <div class="p-3">

    <!-- ================= FORM ================= -->
    <div class="card p-3 mt-3">

      <div class="company-form-grid">

        <!-- NAME -->
        <div>
          <label class="form-label">
            <span class="text-danger">*</span> Nombre Company
          </label>
          <input ref="nameRef" v-model="form.name" class="form-control"
            :class="{ 'is-invalid': errors.name }"/>
        </div>

        <!-- IDENTIFICATION -->
        <div>
          <label class="form-label">
            <span class="text-danger">*</span> Identificación Nit
          </label>
          <input ref="identificationRef" v-model="form.identification_number" class="form-control"
            :class="{ 'is-invalid': errors.identification_number }"/>
        </div>

        <!-- Digito Verificacion DV -->
        <div>
          <label class="form-label">
            <span class="text-danger">*</span> DV
          </label>
          <input ref="dvRef" v-model="form.dv" class="form-control"
            :class="{ 'is-invalid': errors.dv }"/>
        </div>

        <!-- ADDRESS -->
        <div>
          <label class="form-label">
            <span class="text-danger">*</span> Dirección
          </label>
          <input ref="addressRef" v-model="form.address" class="form-control"
            :class="{ 'is-invalid': errors.address }"/>
        </div>

        <!-- PHONE -->
        <div>
          <label class="form-label">
            <span class="text-danger">*</span> Teléfono Movil
          </label>
          <input ref="phoneRef" v-model="form.phone" class="form-control"
            :class="{ 'is-invalid': errors.phone }"/>
        </div>

        <!-- EMAIL -->
        <div>
          <label class="form-label">
            <span class="text-danger">*</span> Email
          </label>
          <input ref="emailRef" v-model="form.email" class="form-control"
            :class="{ 'is-invalid': errors.email }"/>
        </div>

        <!-- RELACIONALES -->
        <div>
          <select v-model="form.business_profile_id" class="form-select"
            :class="{ 'is-invalid': errors.business_profile_id }">
            <option value="">Perfil (Tipo Negocio)</option>
            <option v-for="p in profiles" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
        </div>

        <div>
          <select v-model="form.language_id" class="form-select"
            :class="{ 'is-invalid': errors.language_id }">
            <option value="">Idioma *</option>
            <option v-for="l in languages" :key="l.id" :value="l.id">{{ l.name }}</option>
          </select>
        </div>

        <div>
          <select v-model="form.country_id" class="form-select"
            :class="{ 'is-invalid': errors.country_id }">
            <option value="">País *</option>
            <option v-for="c in countries" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>

        <div>
          <select v-model="form.department_id" class="form-select"
            :class="{ 'is-invalid': errors.department_id }">
            <option value="">Departamento *</option>
            <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.name }}</option>
          </select>
        </div>

        <div>
          <select v-model="form.municipality_id" class="form-select"
            :class="{ 'is-invalid': errors.municipality_id }">
            <option value="">Municipio *</option>
            <option v-for="m in municipalities" :key="m.id" :value="m.id">{{ m.name }}</option>
          </select>
        </div>

        <div>
          <select v-model="form.type_currency_id" class="form-select"
            :class="{ 'is-invalid': errors.type_currency_id }">
            <option value="">Moneda *</option>
            <option v-for="t in currencies" :key="t.id" :value="t.id">{{ t.name }}</option>
          </select>
        </div>

        <!-- DESCRIPTION (full width) -->
        <div class="full-width">
          <textarea v-model="form.description" class="form-control" placeholder="Descripción (Optional)"></textarea>
        </div>

        <!-- STATE -->
        <div>
          <select v-model="form.state" class="form-select">
            <option :value="1">Activo</option>
            <option :value="0">Inactivo</option>
          </select>
        </div>

        <!-- SIDEBAR DERECHO -->
        <div>
          <label class="form-label">Panel lateral derecho (publicidad)</label>
          <div class="sidebar-toggle-wrap">
            <button type="button"
              class="sidebar-toggle-btn"
              :class="form.show_sidebar_right ? 'stb--on' : 'stb--off'"
              @click="form.show_sidebar_right = form.show_sidebar_right ? 0 : 1"
            >
              <span class="stb-track">
                <span class="stb-thumb"></span>
              </span>
              <span class="stb-label">
                <i class="bi" :class="form.show_sidebar_right ? 'bi-layout-sidebar-reverse' : 'bi-layout-sidebar-reverse'"></i>
                {{ form.show_sidebar_right ? 'Visible' : 'Oculto para esta empresa' }}
              </span>
            </button>
            <p class="sidebar-toggle-hint">
              <i class="bi bi-info-circle"></i>
              Si se desactiva, la empresa nunca verá el panel de publicidad ni el botón para abrirlo.
            </p>
          </div>
        </div>

      </div>

      <!-- ── PLAN ──────────────────────────────────────────── -->
      <div class="plan-section mt-4">
        <div class="plan-section-header">
          <i class="bi bi-award me-1"></i>Plan a asignar
          <span class="plan-section-hint">Opcional — se puede asignar después desde Lista Empresas</span>
        </div>
        <div class="plan-section-body">
          <div class="plan-grid">
            <div class="plan-fg">
              <label>Plan</label>
              <select v-model="planForm.plan_id" class="form-select">
                <option value="">— Sin plan por ahora —</option>
                <option v-for="p in plans" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
            </div>
            <div class="plan-fg">
              <label>Fecha de vencimiento <small class="text-muted">(vacío = indefinido)</small></label>
              <CustomDatePicker v-model="planForm.expiration_date" />
            </div>
          </div>
          <p v-if="planForm.plan_id" class="plan-preview-note">
            <i class="bi bi-info-circle me-1"></i>
            El plan <strong>{{ plans.find(p => p.id === planForm.plan_id)?.name }}</strong> se asignará automáticamente al crear la empresa.
          </p>
        </div>
      </div>

      <!-- ── BD EXTERNA ─────────────────────────────────────────── -->
      <div class="ext-db-section mt-4">
        <button type="button" class="ext-db-toggle" @click="showExtDb = !showExtDb">
          <i class="bi" :class="showExtDb ? 'bi-chevron-down' : 'bi-chevron-right'"></i>
          <i class="bi bi-database-gear ms-1"></i>
          Base de datos externa
          <span v-if="form.ext_db_host" class="ext-db-badge">Configurada</span>
          <span v-else class="ext-db-badge ext-db-badge--none">Sin configurar · usa easyposweb</span>
        </button>

        <div v-if="showExtDb" class="ext-db-body">
          <p class="ext-db-hint">
            <i class="bi bi-info-circle"></i>
            Dejar vacío para usar la base de datos principal (<strong>easyposweb</strong>).
            Solo completar si este perfil tiene su propia DB (mismo servidor u otro).
          </p>

          <div class="ext-db-grid">
            <div class="ext-field ext-field--host">
              <label>Servidor (host / IP)</label>
              <input v-model="form.ext_db_host" class="form-control form-control-sm"
                placeholder="Ej: 192.168.1.100 o mi-servidor.com" />
            </div>

            <div class="ext-field ext-field--port">
              <label>Puerto</label>
              <input v-model.number="form.ext_db_port" type="number" class="form-control form-control-sm"
                placeholder="3306" min="1" max="65535" />
            </div>

            <div class="ext-field ext-field--name">
              <label>Nombre de la base de datos</label>
              <input v-model="form.ext_db_name" class="form-control form-control-sm"
                placeholder="Ej: compraventa_db" />
            </div>

            <div class="ext-field ext-field--user">
              <label>Usuario</label>
              <input v-model="form.ext_db_user" class="form-control form-control-sm"
                placeholder="Ej: vb6user" />
            </div>

            <div class="ext-field ext-field--pass">
              <label>Contraseña</label>
              <div class="pass-wrap">
                <input v-model="form.ext_db_password" :type="showPass ? 'text' : 'password'"
                  class="form-control form-control-sm"
                  :placeholder="form.ext_db_has_password ? '(guardada — dejar vacío para no cambiarla)' : 'Contraseña'" />
                <button type="button" class="pass-eye" @click="showPass = !showPass" tabindex="-1">
                  <i class="bi" :class="showPass ? 'bi-eye-slash' : 'bi-eye'"></i>
                </button>
              </div>
            </div>
          </div>

          <!-- Resultado del test -->
          <div v-if="testResult" class="test-result"
            :class="testResult.ok ? 'test-result--ok' : 'test-result--err'">
            <i class="bi" :class="testResult.ok ? 'bi-check-circle-fill' : 'bi-x-circle-fill'"></i>
            {{ testResult.message }}
          </div>

          <div class="ext-db-actions">
            <button type="button" class="btn btn-sm btn-outline-secondary"
              :disabled="testing" @click="clearExtDb">
              <i class="bi bi-trash"></i> Limpiar
            </button>
            <button type="button" class="btn btn-sm btn-outline-primary"
              :disabled="testing || !form.ext_db_host" @click="testConnection">
              <span v-if="testing" class="spinner-border spinner-border-sm me-1"></span>
              <i v-else class="bi bi-plug-fill me-1"></i>
              {{ testing ? 'Probando...' : 'Probar conexión' }}
            </button>
          </div>
        </div>
      </div>
      <!-- ── /BD EXTERNA ─────────────────────────────────────────── -->

      <button class="btn btn-primary mt-3" @click="createCompany">
        Guardar
      </button>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import CustomDatePicker from "@/components/common/CustomDatePicker.vue"

const profiles      = ref([])
const languages     = ref([])
const countries     = ref([])
const departments   = ref([])
const municipalities = ref([])
const currencies    = ref([])
const plans         = ref([])
const planForm      = ref({ plan_id: "", expiration_date: "" })

const showExtDb  = ref(false)
const showPass   = ref(false)
const testing    = ref(false)
const testResult = ref(null)

const form = ref({
  name: "",
  identification_number: "",
  dv: "",
  address: "",
  phone: "",
  email: "",
  description: "",
  state: 1,
  business_profile_id: "",
  language_id: "80",
  country_id: "46",
  department_id: "",
  municipality_id: "",
  type_currency_id: "35",
  // BD externa
  ext_db_host: "",
  ext_db_port: 3306,
  ext_db_name: "",
  ext_db_user: "",
  ext_db_password: "",
  ext_db_has_password: false,
  // UI
  show_sidebar_right: 1,
})

const errors = ref({
  name: false,
  identification_number: false,
  dv: false,
  address: false,
  phone: false,
  email: false,
  business_profile_id: false,
  language_id: false,
  country_id: false,
  department_id: false,
  municipality_id: false,
  type_currency_id: false,
})

const nameRef           = ref(null)
const identificationRef = ref(null)
const dvRef             = ref(null)
const addressRef        = ref(null)
const phoneRef          = ref(null)
const emailRef          = ref(null)

const resetErrors = () => {
  Object.keys(errors.value).forEach(k => errors.value[k] = false)
}

const loadAll = async () => {
  profiles.value      = (await api.get("/business-profiles/")).data.data
  languages.value     = (await api.get("/languages/")).data
  countries.value     = (await api.get("/countries/")).data
  departments.value   = (await api.get("/departments/")).data
  municipalities.value = (await api.get("/municipalities/")).data
  currencies.value    = (await api.get("/type-currencies/")).data
  const pRes = await api.get("/plans/")
  plans.value = pRes.data.filter(p => p.is_active)
}

const clearExtDb = () => {
  form.value.ext_db_host     = ""
  form.value.ext_db_port     = 3306
  form.value.ext_db_name     = ""
  form.value.ext_db_user     = ""
  form.value.ext_db_password = ""
  form.value.ext_db_has_password = false
  testResult.value = null
}

const testConnection = async () => {
  testing.value    = true
  testResult.value = null
  try {
    const res = await api.post(`/companies/0/test-db`, {
      ext_db_host:     form.value.ext_db_host,
      ext_db_port:     form.value.ext_db_port,
      ext_db_name:     form.value.ext_db_name,
      ext_db_user:     form.value.ext_db_user,
      ext_db_password: form.value.ext_db_password,
    })
    testResult.value = res.data
  } catch (e) {
    testResult.value = { ok: false, message: e.response?.data?.detail || "Error de conexión" }
  } finally {
    testing.value = false
  }
}

const createCompany = async () => {
  resetErrors()
  testResult.value = null

  let refFocus = null
  let message  = ""

  if (!form.value.name) {
    errors.value.name = true; refFocus = nameRef; message = "Nombre es obligatorio"
  } else if (!form.value.identification_number) {
    errors.value.identification_number = true; refFocus = identificationRef; message = "Identificación es obligatoria"
  } else if (!form.value.dv) {
    errors.value.dv = true; refFocus = dvRef; message = "DV es obligatorio"
  } else if (!form.value.address) {
    errors.value.address = true; refFocus = addressRef; message = "Dirección es obligatoria"
  } else if (!form.value.phone) {
    errors.value.phone = true; refFocus = phoneRef; message = "Teléfono es obligatorio"
  } else if (!form.value.email) {
    errors.value.email = true; refFocus = emailRef; message = "Email es obligatorio"
  } else if (!isValidEmail(form.value.email)) {
    errors.value.email = true; refFocus = emailRef; message = "Email no es válido"
  } else if (!form.value.business_profile_id) {
    errors.value.business_profile_id = true; message = "Perfil es obligatorio"
  } else if (!form.value.language_id) {
    errors.value.language_id = true; message = "Idioma es obligatorio"
  } else if (!form.value.country_id) {
    errors.value.country_id = true; message = "País es obligatorio"
  } else if (!form.value.department_id) {
    errors.value.department_id = true; message = "Departamento es obligatorio"
  } else if (!form.value.municipality_id) {
    errors.value.municipality_id = true; message = "Municipio es obligatorio"
  } else if (!form.value.type_currency_id) {
    errors.value.type_currency_id = true; message = "Moneda es obligatoria"
  }

  if (message) {
    showToast(message, "warning")
    if (refFocus) nextTick(() => refFocus.value?.focus())
    return
  }

  try {
    const res = await api.post("/companies/", form.value)
    const newId = res.data?.id

    // Asignar plan si fue seleccionado
    if (newId && planForm.value.plan_id) {
      try {
        await api.post(`/company-plan/${newId}`, {
          plan_id:         Number(planForm.value.plan_id),
          expiration_date: planForm.value.expiration_date || null,
        })
        const planName = plans.value.find(p => p.id === planForm.value.plan_id)?.name || ""
        showToast(`Empresa creada · Plan "${planName}" asignado`, "success")
      } catch {
        showToast("Empresa creada, pero hubo un error al asignar el plan. Asígnalo desde Lista Empresas.", "warning")
      }
    } else {
      showToast("Empresa creada correctamente", "success")
    }

    form.value = {
      ...form.value,
      name: "", identification_number: "", dv: "", address: "",
      phone: "", email: "", description: "",
      ext_db_host: "", ext_db_port: 3306, ext_db_name: "",
      ext_db_user: "", ext_db_password: "", ext_db_has_password: false,
    }
    planForm.value = { plan_id: "", expiration_date: "" }
    showExtDb.value = false
  } catch (error) {
    console.error(error)
    showToast("Error guardando empresa", "error")
  }
}

const isValidEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)

onMounted(() => { loadAll() })
</script>

<style scoped>
.company-form-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}
@media (min-width: 768px) {
  .company-form-grid { grid-template-columns: 1fr 1fr; }
}
.full-width { grid-column: 1 / -1; }

/* ── BD Externa ── */
.ext-db-section {
  border: 1.5px dashed #cbd5e1;
  border-radius: 10px;
  overflow: hidden;
}
.ext-db-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 6px;
  background: #f8fafc;
  border: none;
  padding: 10px 14px;
  font-size: .88rem;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  text-align: left;
}
.ext-db-toggle:hover { background: #f1f5f9; }
.ext-db-badge {
  margin-left: auto;
  font-size: .72rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 20px;
  background: #dcfce7;
  color: #15803d;
}
.ext-db-badge--none {
  background: #f1f5f9;
  color: #94a3b8;
  font-weight: 500;
}
.ext-db-body {
  padding: 14px 16px;
  background: #fff;
  border-top: 1px solid #e2e8f0;
}
.ext-db-hint {
  font-size: .8rem;
  color: #64748b;
  margin-bottom: 14px;
  background: #f8fafc;
  border-radius: 6px;
  padding: 8px 10px;
}
.ext-db-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}
@media (min-width: 576px) {
  .ext-db-grid {
    grid-template-columns: 3fr 1fr;
  }
  .ext-field--name  { grid-column: 1; }
  .ext-field--port  { grid-column: 2; }
  .ext-field--user  { grid-column: 1; }
  .ext-field--pass  { grid-column: 1 / -1; }
}
@media (min-width: 768px) {
  .ext-db-grid {
    grid-template-columns: 3fr 1fr 2fr 2fr;
  }
  .ext-field--host { grid-column: 1 / 3; }
  .ext-field--port { grid-column: 3; }
  .ext-field--name { grid-column: 4; }
  .ext-field--user { grid-column: 1 / 3; }
  .ext-field--pass { grid-column: 3 / 5; }
}
.ext-field label {
  display: block;
  font-size: .78rem;
  color: #64748b;
  margin-bottom: 4px;
}
.pass-wrap { position: relative; }
.pass-eye {
  position: absolute;
  right: 8px; top: 50%;
  transform: translateY(-50%);
  background: none; border: none;
  color: #94a3b8; cursor: pointer;
  padding: 0;
}
.ext-db-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 14px;
}
.test-result {
  margin-top: 10px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: .82rem;
  display: flex;
  align-items: center;
  gap: 6px;
}
.test-result--ok  { background: #dcfce7; color: #15803d; }
.test-result--err { background: #fee2e2; color: #dc2626; }

/* ── Sidebar right toggle ── */
.sidebar-toggle-wrap { display: flex; flex-direction: column; gap: 6px; }
.sidebar-toggle-btn {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: none;
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  padding: 8px 12px;
  cursor: pointer;
  font-size: .85rem;
  font-weight: 600;
  transition: border-color .15s, background .15s;
  width: 100%;
}
.sidebar-toggle-btn:hover { background: #f8fafc; }
.stb-track {
  position: relative;
  width: 36px;
  height: 20px;
  border-radius: 10px;
  background: #cbd5e1;
  flex-shrink: 0;
  transition: background .2s;
}
.stb-thumb {
  position: absolute;
  top: 3px; left: 3px;
  width: 14px; height: 14px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,.25);
  transition: left .2s;
}
.stb--on .stb-track { background: #22c55e; border-color: #22c55e; }
.stb--on .stb-thumb { left: 19px; }
.stb--on { border-color: #bbf7d0; background: #f0fdf4; color: #15803d; }
.stb--off .stb-track { background: #e2e8f0; }
.stb--off { border-color: #e2e8f0; color: #94a3b8; }
.stb-label { display: flex; align-items: center; gap: 5px; }
.sidebar-toggle-hint {
  font-size: .75rem;
  color: #94a3b8;
  margin: 0;
  line-height: 1.4;
  display: flex;
  gap: 4px;
  align-items: flex-start;
}
@media (max-width: 576px) {
  .sidebar-toggle-btn { font-size: .8rem; padding: 7px 10px; }
}

/* ── Plan section ── */
.plan-section {
  border: 1.5px solid #bfdbfe;
  border-radius: 10px;
  overflow: hidden;
}
.plan-section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #eff6ff;
  padding: 10px 14px;
  font-size: .88rem;
  font-weight: 700;
  color: #1d4ed8;
}
.plan-section-hint {
  margin-left: auto;
  font-size: .72rem;
  font-weight: 400;
  color: #64748b;
}
.plan-section-body {
  padding: 14px 16px;
  background: #fff;
  border-top: 1px solid #dbeafe;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.plan-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.plan-fg { display: flex; flex-direction: column; gap: 4px; }
.plan-fg label { font-size: 13px; font-weight: 500; color: #374151; }
.plan-preview-note {
  font-size: 12px;
  color: #1d4ed8;
  background: #eff6ff;
  border-radius: 6px;
  padding: 7px 10px;
  margin: 0;
}
@media (max-width: 576px) {
  .plan-grid { grid-template-columns: 1fr; }
  .plan-section-hint { display: none; }
}
</style>
