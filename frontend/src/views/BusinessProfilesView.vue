
<template> 
  <div class="container mt-4 pb-5">
    <h2>Business Profiles</h2>

    <!-- 🔹 Form -->
    <div class="card p-3 mb-4">
      <h5>Crear Perfil</h5>

      <input v-model="form.name" class="form-control mb-2" placeholder="Nombre" />
      
      <input v-model="form.description" class="form-control mb-2" placeholder="Descripción" />

      <div class="form-check mb-2">
        <input type="checkbox" v-model="form.is_active" class="form-check-input" />
        <label class="form-check-label">Activo</label>
      </div>

      <!-- ✅ BOTÓN CORRECTO -->
      <button 
        class="btn btn-primary"
        @click="saveProfile"
      >
        Crear Perfil
      </button>
    </div>

    <!-- 🔹 Tabla -->
    <div class="table-responsive">
      <table class="table table-bordered">
        <thead>
          <tr>
            <th>ID</th>
            <th>Nombre</th>
            <th>Descripción</th>
            <th>Activo</th>
            <th>Acciones</th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="item in profiles" :key="item.id">
            <td>{{ item.id }}</td>
            <td>{{ item.name }}</td>
            
              <td style="max-width: 250px;">
                <div 
                  class="text-truncate"
                  style="cursor: pointer;"
                  @click="openDescription(item.description)"
                >
                  {{ item.description }}
                </div>
              </td>


            <td>{{ item.is_active ? 'Sí' : 'No' }}</td>

            <td>
              <div class="d-flex flex-column flex-md-row gap-1">
                
                <button 
                  class="btn btn-warning btn-sm w-100"
                  @click="openEditModal(item)"
                >
                  Editar
                </button>

                <button 
                  class="btn btn-danger btn-sm w-100"
                  @click="deleteProfile(item.id)"
                >
                  Eliminar
                </button>

              </div>
            </td>

          </tr>
        </tbody>
      </table>
    </div>
  </div>
  <!-- MODAL-->
<div v-if="showEditModal" class="modal fade show d-block">
  <div class="modal-dialog">
    <div class="modal-content">

      <div class="modal-header">
        <h5 class="modal-title">Editar Perfil</h5>
        <button class="btn-close" @click="showEditModal = false"></button>
      </div>

      <div class="modal-body">

        <input v-model="editForm.name" class="form-control mb-2" />
        <input v-model="editForm.description" class="form-control mb-2" />

        <div class="form-check">
          <input type="checkbox" v-model="editForm.is_active" class="form-check-input" />
          <label class="form-check-label">Activo</label>
        </div>

      </div>

      <div class="modal-footer">
        <button class="btn btn-secondary" @click="showEditModal = false">
          Cancelar
        </button>

        <button class="btn btn-success" @click="updateProfile">
          Guardar
        </button>
      </div>

    </div>
  </div>
</div>
<!-- 🔹 MODAL DESCRIPCIÓN -->
<div v-if="showDescModal" class="modal fade show d-block">
  <div class="modal-dialog">
    <div class="modal-content">

      <div class="modal-header">
        <h5 class="modal-title">Descripción</h5>
        <button class="btn-close" @click="showDescModal = false"></button>
      </div>

      <div class="modal-body">
        {{ selectedDescription }}
      </div>

    </div>
  </div>
</div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from "@/services/apis"

// =============================
// STATE
// =============================
const profiles = ref([])
const showDescModal = ref(false)
const selectedDescription = ref("")


const form = ref({
  name: '',
  description: '',
  is_active: true
})

const showEditModal = ref(false)
const openDescription = (desc) => {
  selectedDescription.value = desc
  showDescModal.value = true
}

const editForm = ref({
  id: null,
  name: "",
  description: "",
  is_active: true
})

// =============================
// TOAST
// =============================
const showToast = (msg, type = 'success') => {
  window.dispatchEvent(new CustomEvent('toast', {
    detail: { message: msg, type }
  }))
}

// =============================
// LOAD PROFILES (ÚNICA FUNCIÓN)
// =============================
const fetchProfiles = async () => {
  try {
    const res = await api.get('/business-profiles/')
    profiles.value = res.data.data
  } catch (error) {
    console.error(error)
    showToast('Error cargando perfiles', 'error')
  }
}

// =============================
// CREATE
// =============================
const saveProfile = async () => {
  try {
    await api.post('/business-profiles/', form.value)

    showToast('Perfil creado correctamente', 'success')

    resetForm()
    await fetchProfiles()

  } catch (error) {
    console.error(error)
    showToast('Error creando perfil', 'error')
  }
}

// =============================
// EDIT (ABRIR MODAL)
// =============================
const openEditModal = (profile) => {
  editForm.value = {
    id: profile.id,
    name: profile.name,
    description: profile.description,
    is_active: profile.is_active
  }

  showEditModal.value = true
}

// =============================
// UPDATE (MODAL)
// =============================
const updateProfile = async () => {
  try {
    await api.put(`/business-profiles/${editForm.value.id}`, editForm.value)

    showToast("Perfil actualizado correctamente", "success")

    showEditModal.value = false

    await fetchProfiles()

  } catch (error) {
    console.error(error)
    showToast("Error al actualizar perfil", "error")
  }
}

// =============================
// DELETE
// =============================
const deleteProfile = (id) => {

  // 🔥 toast tipo confirmación
  window.dispatchEvent(new CustomEvent('toast-confirm', {
    detail: {
      message: "¿Eliminar perfil?",
      onConfirm: async () => {
        try {
          await api.delete(`/business-profiles/${id}`)

          showToast("Perfil eliminado correctamente", "success")

          await fetchProfiles()

        } catch (error) {
          console.error(error)
          showToast("Error al eliminar perfil", "error")
        }
      }
    }
  }))
}

// =============================
// RESET FORM
// =============================
const resetForm = () => {
  form.value = {
    name: '',
    description: '',
    is_active: true
  }
}

// =============================
// INIT
// =============================
onMounted(() => {
  fetchProfiles()
})
</script>

