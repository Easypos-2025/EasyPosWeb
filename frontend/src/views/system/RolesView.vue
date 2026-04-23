<template>
  <div class="roles-container">

    <h1 class="title">Roles & Permisos</h1>

    <div class="content">

      <!-- =========================
      LISTADO ROLES
      ========================= -->
      <div class="roles-list">

        <h2>Roles</h2>

        <div v-if="loading">Cargando...</div>

        <ul v-else>
          <li
            v-for="role in roles"
            :key="role.id"
            :class="{ active: selectedRole?.id === role.id }"
            @click="selectRole(role)"
          >
            <strong>{{ role.name }}</strong>
            <small>{{ role.description }}</small>
          </li>
        </ul>

      </div>

      <!-- =========================
      DETALLE
      ========================= -->
      <div class="roles-detail">

        <div v-if="!selectedRole">
          Selecciona un rol
        </div>

        <div v-else>
          <h2>{{ selectedRole.name }}</h2>
          <p>{{ selectedRole.description }}</p>

          <div v-if="loadingModules">
             Cargando permisos...
          </div>

          <div v-else class="permissions-table  custom-scroll-x">
            <div class="table-wrapper">
              <table class="permissions-table">
                <thead>
                  <tr>
                    <th>Módulo</th>
                    <th>Ver</th>
                    <th>Crear</th>
                    <th>Editar</th>
                    <th>Eliminar</th>
                  </tr>
                </thead>

                <tbody>
                  <tr v-for="mod in allModules" :key="mod.id">
                    <td>{{ mod.name }}</td>

                    <td>
                      <input
                        type="checkbox"
                        :checked="getPermission(mod.id, 'can_view')"
                        @change="togglePermission(mod.id, 'can_view')"
                      />
                    </td>

                    <td>
                      <input
                        type="checkbox"
                        :checked="getPermission(mod.id, 'can_create')"
                        @change="togglePermission(mod.id, 'can_create')"
                      />
                    </td>

                    <td>
                      <input
                        type="checkbox"
                        :checked="getPermission(mod.id, 'can_edit')"
                        @change="togglePermission(mod.id, 'can_edit')"
                      />
                    </td>

                    <td>
                      <input
                        type="checkbox"
                        :checked="getPermission(mod.id, 'can_delete')"
                        @change="togglePermission(mod.id, 'can_delete')"
                      />
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="mt-3 text-end">
              <button class="btn btn-success" @click="savePermissions">
                Guardar permisos
              </button>
            </div>

          </div>

        </div>

      </div>

    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

const roles = ref([])
const selectedRole = ref(null)
const loading = ref(false)
const allModules = ref([])
const loadingModules = ref(false)
const editablePermissions = ref([])

/* =========================
GET ROLES
========================= */
const fetchRoles = async () => {
  try {
    loading.value = true
    const res = await api.get("/roles/")
    roles.value = res.data
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

/* =========================
GET ALL MODULES
========================= */
const fetchAllModules = async () => {
  try {
    const res = await api.get("/system-modules/flat/")
    allModules.value = res.data
  } catch (error) {
    console.error(error)
  }
}

/* =========================
SELECT ROLE
========================= */
const selectRole = (role) => {
  selectedRole.value = role
  fetchRoleModules(role.id)
}

/* =========================
LOAD ROLE PERMISSIONS
========================= */
const fetchRoleModules = async (roleId) => {
  try {
    loadingModules.value = true

    const res = await api.get(`/roles/${roleId}/modules/`)

    // 🔥 CLAVE: SIEMPRE llenar TODOS los módulos
    editablePermissions.value = allModules.value.map(mod => {
      const existing = res.data.find(r => r.module_id === mod.id)

      return {
        module_id: mod.id,
        can_view: existing?.can_view || false,
        can_create: existing?.can_create || false,
        can_edit: existing?.can_edit || false,
        can_delete: existing?.can_delete || false
      }
    })

  } catch (error) {
    console.error(error)
  } finally {
    loadingModules.value = false
  }
}

/* =========================
GET PERMISSION (FIX)
========================= */
const getPermission = (moduleId, key) => {
  const found = editablePermissions.value.find(m => m.module_id === moduleId)
  return found ? found[key] : false
}

/* =========================
TOGGLE (FIX REAL)
========================= */
const togglePermission = (moduleId, key) => {
  editablePermissions.value = editablePermissions.value.map(p => {
    if (p.module_id === moduleId) {
      return {
        ...p,
        [key]: !p[key]
      }
    }
    return p
  })
}

/* =========================
SAVE
========================= */
const savePermissions = async () => {
  try {

    const payload = editablePermissions.value.filter(p =>
      p.can_view || p.can_create || p.can_edit || p.can_delete
    )

    await api.post(
      `/roles/${selectedRole.value.id}/modules/`,
      payload
    )

    showToast("Permisos guardados correctamente", "success")

    fetchRoleModules(selectedRole.value.id)

  } catch (error) {
    console.error(error)
    showToast("Error al guardar permisos", "error")
  }
}

/* =========================
INIT
========================= */
onMounted(() => {
  fetchRoles()
  fetchAllModules()
})
</script>


<style scoped>
.roles-container {
  padding: 20px;
}

.title {
  margin-bottom: 20px;
}

.content {
  display: flex;
  gap: 20px;
}

/* LISTA */
.roles-list {
  width: 300px;
  border-right: 1px solid #ddd;
}

.roles-list ul {
  list-style: none;
  padding: 0;
}

.roles-list li {
  padding: 10px;
  cursor: pointer;
  border-bottom: 1px solid #eee;
}

.roles-list li.active {
  background: #f0f0f0;
}

/* DETALLE */
.roles-detail {
  flex: 1;
}

.permissions-table table {
  border-collapse: collapse;
  min-width: 700px; /* 🔥 clave */
}


/* opcional: mejorar visibilidad */
.permissions-table th,
.permissions-table td {
  padding: 8px;
  white-space: nowrap;
}

.permissions-table th {
  background: #f5f5f5;
}

.table-wrapper {
  overflow-x: auto;
  width: 100%;
}

/* 👇 hint visual */
.table-wrapper::after {
  content: "← Desliza →";
  display: block;
  font-size: 12px;
  text-align: right;
  color: #888;
  margin-top: 4px;
}

/* 🔥 FORZAR QUE LA TABLA SEA MÁS ANCHA */
.permissions-table {
  min-width: 700px;
  border-collapse: collapse;
}


@media (max-width: 768px) {
  table {
    min-width: 600px;
  }
}


</style>