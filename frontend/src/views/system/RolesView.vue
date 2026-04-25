<template>
  <div class="p-3">

    <!-- CABECERA -->
    <div class="card p-3 mt-3">
      <div class="row g-2 align-items-end">

        <!-- Selector de empresa (solo SYSADMIN) -->
        <div v-if="companyStore.isSystem" class="col-md-5 col-12">
          <label class="form-label mb-1" style="font-size:13px;font-weight:600">Empresa</label>
          <select class="form-select" v-model="selectedCompanyId" @change="onCompanyChange">
            <option value="">— Seleccionar empresa —</option>
            <option v-for="c in companyStore.companies" :key="c.id" :value="c.id">
              {{ c.name }}
            </option>
          </select>
        </div>

        <!-- Nombre empresa (usuario normal) -->
        <div v-else class="col-md-5 col-12">
          <label class="form-label mb-1" style="font-size:13px;font-weight:600">Empresa</label>
          <div class="form-control-plaintext fw-semibold" style="font-size:15px">
            {{ companyStore.selectedCompany?.name || '—' }}
          </div>
        </div>

        <div class="col-md-4 col-12 d-flex align-items-end">
          <span class="text-muted" style="font-size:13px">
            {{ roles.length }} rol(es) registrados
          </span>
        </div>

        <div class="col-md-3 col-12 text-end">
          <button
            class="btn btn-primary btn-sm"
            :disabled="!activeCompanyId"
            @click="openCreateRole"
          >
            <i class="bi bi-plus-lg"></i> Nuevo rol
          </button>
        </div>

      </div>
    </div>

    <!-- CONTENIDO PRINCIPAL -->
    <div class="row g-3 mt-1">

      <!-- LISTA DE ROLES -->
      <div class="col-md-3 col-12">
        <div class="card p-3">
          <h6 class="fw-bold mb-3">Roles</h6>

          <div v-if="loadingRoles" class="text-muted small">Cargando...</div>

          <div v-else-if="!activeCompanyId" class="text-muted small">
            Selecciona una empresa
          </div>

          <div v-else-if="roles.length === 0" class="text-muted small">
            Sin roles para esta empresa
          </div>

          <ul v-else class="list-unstyled mb-0">
            <li
              v-for="r in roles"
              :key="r.id"
              class="role-item"
              :class="{ active: selectedRole?.id === r.id }"
              @click="selectRole(r)"
            >
              <div class="d-flex justify-content-between align-items-center">
                <div>
                  <div class="fw-semibold" style="font-size:14px">{{ r.name }}</div>
                  <div class="text-muted" style="font-size:12px">{{ r.description || '—' }}</div>
                </div>
                <button
                  class="btn btn-danger btn-sm py-0 px-1"
                  title="Eliminar rol"
                  @click.stop="handleDeleteRole(r)"
                >
                  <i class="bi bi-trash" style="font-size:11px"></i>
                </button>
              </div>
            </li>
          </ul>
        </div>
      </div>

      <!-- TABLA DE PERMISOS -->
      <div class="col-md-9 col-12">
        <div class="card p-3">

          <div v-if="!selectedRole" class="text-muted py-5 text-center">
            <i class="bi bi-shield-lock" style="font-size:36px;opacity:0.3"></i>
            <div class="mt-2">Selecciona un rol para gestionar sus permisos</div>
          </div>

          <template v-else>
            <div class="d-flex justify-content-between align-items-center mb-3">
              <div>
                <h6 class="fw-bold mb-0">{{ selectedRole.name }}</h6>
                <small class="text-muted">{{ selectedRole.description }}</small>
              </div>
              <button class="btn btn-success btn-sm" @click="savePermissions" :disabled="saving">
                <i class="bi bi-check-lg"></i> {{ saving ? 'Guardando...' : 'Guardar permisos' }}
              </button>
            </div>

            <div v-if="loadingModules" class="text-muted small">Cargando permisos...</div>

            <div v-else class="table-responsive">
              <table class="table table-hover table-sm mb-0">
                <thead class="table-light">
                  <tr>
                    <th style="min-width:200px">Módulo</th>
                    <th class="text-center">Ver</th>
                    <th class="text-center">Crear</th>
                    <th class="text-center">Editar</th>
                    <th class="text-center">Eliminar</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="mod in allModules" :key="mod.id">
                    <td style="font-size:13px">{{ mod.name }}</td>
                    <td class="text-center">
                      <input type="checkbox"
                        :checked="getPerm(mod.id, 'can_view')"
                        @change="togglePerm(mod.id, 'can_view')" />
                    </td>
                    <td class="text-center">
                      <input type="checkbox"
                        :checked="getPerm(mod.id, 'can_create')"
                        @change="togglePerm(mod.id, 'can_create')" />
                    </td>
                    <td class="text-center">
                      <input type="checkbox"
                        :checked="getPerm(mod.id, 'can_edit')"
                        @change="togglePerm(mod.id, 'can_edit')" />
                    </td>
                    <td class="text-center">
                      <input type="checkbox"
                        :checked="getPerm(mod.id, 'can_delete')"
                        @change="togglePerm(mod.id, 'can_delete')" />
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>

        </div>
      </div>

    </div>

    <!-- MODAL NUEVO ROL -->
    <div v-if="showRoleModal" class="modal-overlay" @click.self="showRoleModal = false">
      <div class="modal-box">
        <div class="modal-header-bar">
          <h2>Nuevo rol</h2>
          <button class="btn-close-sm" @click="showRoleModal = false">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>
        <div class="modal-body-area">
          <div class="fg">
            <label>Nombre *</label>
            <input v-model="roleForm.name" class="form-control" placeholder="Ej: SUPERVISOR" />
          </div>
          <div class="fg">
            <label>Descripción</label>
            <input v-model="roleForm.description" class="form-control" />
          </div>
        </div>
        <div class="modal-footer-bar">
          <button class="btn btn-secondary" @click="showRoleModal = false">Cancelar</button>
          <button class="btn btn-primary" @click="saveRole" :disabled="savingRole">
            {{ savingRole ? 'Guardando...' : 'Guardar' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import { useCompanyStore } from "@/stores/companyStore"

const companyStore = useCompanyStore()

const roles              = ref([])
const selectedRole       = ref(null)
const allModules         = ref([])
const editablePerms      = ref([])
const loadingRoles       = ref(false)
const loadingModules     = ref(false)
const saving             = ref(false)
const showRoleModal      = ref(false)
const savingRole         = ref(false)
const roleForm           = ref({ name: "", description: "" })
const selectedCompanyId  = ref("")

// Empresa activa: SYSADMIN usa el selector; ADMIN usa la suya
const activeCompanyId = computed(() =>
  companyStore.isSystem
    ? (selectedCompanyId.value || null)
    : (companyStore.selectedCompany?.id || null)
)

// ─── Cargar roles de la empresa activa ───────────────────────
async function loadRoles() {
  if (!activeCompanyId.value) return
  loadingRoles.value = true
  selectedRole.value = null
  editablePerms.value = []
  try {
    const res = await api.get("/roles/", { params: { company_id: activeCompanyId.value } })
    roles.value = res.data
  } catch {
    showToast("Error cargando roles", "error")
  } finally {
    loadingRoles.value = false
  }
}

// ─── Cargar catálogo de módulos (una vez) ────────────────────
async function loadModules() {
  try {
    const res = await api.get("/system-modules/flat/")
    allModules.value = res.data
  } catch {
    showToast("Error cargando módulos", "error")
  }
}

// ─── Cambio de empresa (SYSADMIN) ────────────────────────────
function onCompanyChange() {
  roles.value = []
  selectedRole.value = null
  editablePerms.value = []
  loadRoles()
}

// ─── Seleccionar rol ─────────────────────────────────────────
function selectRole(role) {
  selectedRole.value = role
  loadRolePerms(role.id)
}

async function loadRolePerms(roleId) {
  loadingModules.value = true
  try {
    const res = await api.get(`/roles/${roleId}/modules/`)
    editablePerms.value = allModules.value.map(mod => {
      const found = res.data.find(r => r.module_id === mod.id)
      return {
        module_id:  mod.id,
        can_view:   found?.can_view   ?? false,
        can_create: found?.can_create ?? false,
        can_edit:   found?.can_edit   ?? false,
        can_delete: found?.can_delete ?? false,
      }
    })
  } catch {
    showToast("Error cargando permisos del rol", "error")
  } finally {
    loadingModules.value = false
  }
}

// ─── Helpers de permisos ─────────────────────────────────────
function getPerm(moduleId, key) {
  return editablePerms.value.find(p => p.module_id === moduleId)?.[key] ?? false
}

function togglePerm(moduleId, key) {
  editablePerms.value = editablePerms.value.map(p =>
    p.module_id === moduleId ? { ...p, [key]: !p[key] } : p
  )
}

// ─── Guardar permisos ─────────────────────────────────────────
async function savePermissions() {
  saving.value = true
  try {
    const payload = editablePerms.value.filter(
      p => p.can_view || p.can_create || p.can_edit || p.can_delete
    )
    await api.post(`/roles/${selectedRole.value.id}/modules/`, payload)
    showToast("Permisos guardados", "success")
  } catch {
    showToast("Error guardando permisos", "error")
  } finally {
    saving.value = false
  }
}

// ─── Crear rol ────────────────────────────────────────────────
function openCreateRole() {
  roleForm.value = { name: "", description: "" }
  showRoleModal.value = true
}

async function saveRole() {
  if (!roleForm.value.name.trim()) {
    showToast("El nombre es obligatorio", "warning")
    return
  }
  savingRole.value = true
  try {
    await api.post("/roles/", {
      name:        roleForm.value.name.trim().toUpperCase(),
      description: roleForm.value.description.trim(),
      company_id:  activeCompanyId.value,
    })
    showToast("Rol creado", "success")
    showRoleModal.value = false
    await loadRoles()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error creando rol", "error")
  } finally {
    savingRole.value = false
  }
}

// ─── Eliminar rol ─────────────────────────────────────────────
async function handleDeleteRole(role) {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar rol "${role.name}"?`,
    text: "Se eliminarán también todos sus permisos asignados.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, eliminar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#ef4444",
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/roles/${role.id}`)
    showToast("Rol eliminado", "success")
    if (selectedRole.value?.id === role.id) {
      selectedRole.value = null
      editablePerms.value = []
    }
    await loadRoles()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error eliminando rol", "error")
  }
}

// ─── Init ─────────────────────────────────────────────────────
onMounted(async () => {
  await loadModules()
  // SYSADMIN: espera que el usuario seleccione empresa en el dropdown
  // ADMIN normal: carga roles de su empresa automáticamente
  if (!companyStore.isSystem && activeCompanyId.value) {
    await loadRoles()
  }
})
</script>

<style scoped>
.role-item {
  padding: 10px 8px;
  cursor: pointer;
  border-bottom: 1px solid #f1f5f9;
  border-radius: 6px;
  transition: background 0.15s;
}
.role-item:hover   { background: #f8fafc; }
.role-item.active  { background: #eff6ff; border-left: 3px solid #3b82f6; }

.modal-overlay  { position: fixed; inset: 0; background: rgba(0,0,0,0.45); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-box      { background: #fff; border-radius: 16px; width: 460px; max-width: 95vw; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
.modal-header-bar { display: flex; align-items: center; justify-content: space-between; padding: 18px 24px 14px; border-bottom: 1px solid #f1f5f9; }
.modal-header-bar h2 { font-size: 17px; font-weight: 700; color: #1e293b; margin: 0; }
.modal-body-area  { padding: 18px 24px; display: flex; flex-direction: column; gap: 12px; }
.modal-footer-bar { padding: 14px 24px 18px; display: flex; justify-content: flex-end; gap: 10px; border-top: 1px solid #f1f5f9; }
.fg       { display: flex; flex-direction: column; gap: 4px; }
.fg label { font-size: 13px; font-weight: 500; color: #374151; }
.btn-close-sm { background: none; border: none; font-size: 18px; cursor: pointer; color: #94a3b8; border-radius: 6px; padding: 4px 8px; }
.btn-close-sm:hover { background: #f1f5f9; color: #1e293b; }
</style>
