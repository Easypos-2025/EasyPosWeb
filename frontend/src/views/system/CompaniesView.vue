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

      </div>

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

const profiles = ref([])
const languages = ref([])
const countries = ref([])
const departments = ref([])
const municipalities = ref([])
const currencies = ref([])

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
  type_currency_id: "35"
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
  type_currency_id: false
})

const nameRef = ref(null)
const identificationRef = ref(null)
const dvRef = ref(null)
const addressRef = ref(null)
const phoneRef = ref(null)
const emailRef = ref(null)

const resetErrors = () => {
  Object.keys(errors.value).forEach(k => errors.value[k] = false)
}

const loadAll = async () => {
  profiles.value = (await api.get("/business-profiles/")).data.data
  languages.value = (await api.get("/languages/")).data
  countries.value = (await api.get("/countries/")).data
  departments.value = (await api.get("/departments/")).data
  municipalities.value = (await api.get("/municipalities/")).data
  currencies.value = (await api.get("/type-currencies/")).data
}

const createCompany = async () => {

  resetErrors()

  let refFocus = null
  let message = ""

  if (!form.value.name) {
    errors.value.name = true
    refFocus = nameRef
    message = "Nombre es obligatorio"
  }
  else if (!form.value.identification_number) {
    errors.value.identification_number = true
    refFocus = identificationRef
    message = "Identificación es obligatoria"
  }
  else if (!form.value.dv) {
    errors.value.dv = true
    refFocus = dvRef
    message = "DV es obligatorio"
  }
  else if (!form.value.address) {
    errors.value.address = true
    refFocus = addressRef
    message = "Dirección es obligatoria"
  }
  else if (!form.value.phone) {
    errors.value.phone = true
    refFocus = phoneRef
    message = "Teléfono es obligatorio"
  }
  else if (!form.value.email) {
    errors.value.email = true
    refFocus = emailRef
    message = "Email es obligatorio"
  }
  else if (!isValidEmail(form.value.email)) {
    errors.value.email = true
    refFocus = emailRef
    message = "Email no es válido"
  }
  else if (!form.value.business_profile_id) {
    errors.value.business_profile_id = true
    message = "Perfil es obligatorio"
  }
  else if (!form.value.language_id) {
    errors.value.language_id = true
    message = "Idioma es obligatorio"
  }
  else if (!form.value.country_id) {
    errors.value.country_id = true
    message = "País es obligatorio"
  }
  else if (!form.value.department_id) {
    errors.value.department_id = true
    message = "Departamento es obligatorio"
  }
  else if (!form.value.municipality_id) {
    errors.value.municipality_id = true
    message = "Municipio es obligatorio"
  }
  else if (!form.value.type_currency_id) {
    errors.value.type_currency_id = true
    message = "Moneda es obligatoria"
  }

  if (message) {
    showToast(message, "warning")
    if (refFocus) nextTick(() => refFocus.value?.focus())
    return
  }

  try {

    await api.post("/companies/", form.value)

    showToast("Empresa creada correctamente", "success")

    // limpiar form (manteniendo defaults)
    form.value = {
      ...form.value,
      name: "",
      identification_number: "",
      dv: "",
      address: "",
      phone: "",
      email: "",
      description: ""
    }

  } catch (error) {
    console.error(error)
    showToast("Error guardando empresa", "error")
  }
}

const isValidEmail = (email) => {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return regex.test(email)
}

onMounted(() => {
  loadAll()
})
</script>

<style scoped>
.company-form-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

/* Desktop */
@media (min-width: 768px) {
  .company-form-grid {
    grid-template-columns: 1fr 1fr;
  }
}

/* Campos que ocupan todo el ancho */
.full-width {
  grid-column: 1 / -1;
}
</style>
