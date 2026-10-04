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
                  <span v-if="r.access_type && r.access_type !== 'interno'" class="rol-tipo">{{ TIPOS_ACCESO.find(t => t.v === r.access_type)?.l }}</span>
                </div>
                <div class="d-flex gap-1">
                  <button
                    class="btn btn-warning btn-sm py-0 px-1"
                    title="Editar rol"
                    @click.stop="openEditRole(r)"
                  >
                    <i class="bi bi-pencil" style="font-size:11px"></i>
                  </button>
                  <button
                    class="btn btn-danger btn-sm py-0 px-1"
                    title="Eliminar rol"
                    @click.stop="handleDeleteRole(r)"
                  >
                    <i class="bi bi-trash" style="font-size:11px"></i>
                  </button>
                </div>
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
            <div class="d-flex justify-content-between align-items-center mb-2 flex-wrap gap-2">
              <div>
                <h6 class="fw-bold mb-0">{{ selectedRole.name }}</h6>
                <small class="text-muted">{{ selectedRole.description }}</small>
              </div>
              <button v-if="tabRol === 'modulos'" class="btn btn-success btn-sm" @click="savePermissions" :disabled="saving">
                <i class="bi bi-check-lg"></i> {{ saving ? 'Guardando...' : 'Guardar permisos' }}
              </button>
              <button v-else class="btn btn-success btn-sm" @click="saveAccess" :disabled="savingAccess">
                <i class="bi bi-check-lg"></i> {{ savingAccess ? 'Guardando...' : 'Guardar control de acceso' }}
              </button>
            </div>

            <div class="role-tabs mb-3">
              <button :class="['role-tab', { active: tabRol === 'modulos' }]" @click="tabRol = 'modulos'">
                <i class="bi bi-grid"></i> Módulos
              </button>
              <button :class="['role-tab', { active: tabRol === 'acceso' }]" @click="tabRol = 'acceso'">
                <i class="bi bi-shield-check"></i> Control de Acceso
              </button>
            </div>

            <!-- Control de Acceso: permisos especiales del rol (como el escritorio) -->
            <div v-if="tabRol === 'acceso'">
              <div v-if="loadingAccess" class="text-muted small">Cargando control de acceso...</div>
              <template v-else>
                <div class="d-flex gap-2 mb-3">
                  <button class="btn btn-outline-primary btn-sm" @click="accessKeys = accessCatalog.map(a => a.perm_key)">Seleccionar todo</button>
                  <button class="btn btn-outline-secondary btn-sm" @click="accessKeys = []">Quitar todo</button>
                </div>
                <div class="access-groups">
                  <div v-for="g in accessGroups" :key="g.nombre" class="access-group">
                    <div class="access-group-t">{{ g.nombre }}</div>
                    <label v-for="a in g.items" :key="a.perm_key" class="access-item" :title="a.description || ''">
                      <input type="checkbox" :value="a.perm_key" v-model="accessKeys" />
                      <span>{{ a.name }}<small v-if="a.description">{{ a.description }}</small></span>
                    </label>
                  </div>
                </div>
              </template>
            </div>

            <div v-else-if="loadingModules" class="text-muted small">Cargando permisos...</div>

            <div v-else class="table-responsive">
              <table class="table table-hover table-sm mb-0">
                <thead class="table-light">
                  <tr>
                    <th style="min-width:200px">Módulo</th>
                    <th class="text-center">Ver</th>
                    <th class="text-center">Ver Todos</th>
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
                        :checked="getPerm(mod.id, 'can_view_all')"
                        @change="togglePerm(mod.id, 'can_view_all')" />
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
          <h2>{{ editingRoleId ? 'Editar rol' : 'Nuevo rol' }}</h2>
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
          <div class="fg">
            <label>Tipo de acceso</label>
            <select v-model="roleForm.access_type" class="form-control">
              <option v-for="t in TIPOS_ACCESO" :key="t.v" :value="t.v">{{ t.l }}</option>
            </select>
            <small class="text-muted">{{ TIPOS_ACCESO.find(t => t.v === roleForm.access_type)?.d }}</small>
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
import { ref, computed, onMounted, watch } from "vue"
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
const roleForm           = ref({ name: "", description: "", access_type: "interno" })
// Canal por el que entra quien tiene el rol (cada tipo remoto tendrá su propia URL)
const TIPOS_ACCESO = [
  { v: "interno",        l: "Interno",            d: "Personal de la empresa: panel, caja y TPV." },
  { v: "remoto_login",   l: "Remoto con login",   d: "Cliente o vendedor externo: entra con usuario a su URL y solo ve sus pedidos." },
  { v: "remoto_publico", l: "Remoto sin login",   d: "Cliente final tipo Rappi: URL pública, sin usuario; el pedido lo acepta caja o admin." },
]
const editingRoleId      = ref(null)
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

// ─── Cargar catálogo de módulos filtrado por empresa activa ──
async function loadModules(cid) {
  try {
    const params = cid ? { company_id: cid } : {}
    const res = await api.get("/system-modules/flat/", { params })
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
  allModules.value = []
  const cid = selectedCompanyId.value || null
  loadModules(cid)
  if (cid) loadRoles()
}

// ─── Seleccionar rol ─────────────────────────────────────────
function selectRole(role) {
  selectedRole.value = role
  loadRolePerms(role.id)
  loadAccess(role.id)
}

// ─── Control de Acceso (permisos especiales del rol) ─────────
const tabRol        = ref('modulos')
const accessCatalog = ref([])
const accessKeys    = ref([])
const loadingAccess = ref(false)
const savingAccess  = ref(false)
const accessGroups  = computed(() => {
  const m = new Map()
  for (const a of accessCatalog.value) {
    if (!m.has(a.group_name)) m.set(a.group_name, { nombre: a.group_name, items: [] })
    m.get(a.group_name).items.push(a)
  }
  return [...m.values()]
})

async function loadAccess(roleId) {
  loadingAccess.value = true
  try {
    if (!accessCatalog.value.length) accessCatalog.value = (await api.get('/roles/access/catalog')).data
    accessKeys.value = (await api.get(`/roles/${roleId}/access`)).data
  } catch {
    showToast('Error cargando el control de acceso', 'error')
  } finally {
    loadingAccess.value = false
  }
}

async function saveAccess() {
  savingAccess.value = true
  try {
    await api.put(`/roles/${selectedRole.value.id}/access`, { keys: accessKeys.value })
    showToast('Control de acceso guardado', 'success')
  } catch (e) {
    showToast(e.response?.data?.detail || 'Error guardando el control de acceso', 'error')
  } finally {
    savingAccess.value = false
  }
}

async function loadRolePerms(roleId) {
  loadingModules.value = true
  try {
    const res = await api.get(`/roles/${roleId}/modules/`)
    editablePerms.value = allModules.value.map(mod => {
      const found = res.data.find(r => r.module_id === mod.id)
      return {
        module_id:    mod.id,
        can_view:     found?.can_view     ?? false,
        can_view_all: found?.can_view_all ?? false,
        can_create:   found?.can_create   ?? false,
        can_edit:     found?.can_edit     ?? false,
        can_delete:   found?.can_delete   ?? false,
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
      p => p.can_view || p.can_view_all || p.can_create || p.can_edit || p.can_delete
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
  editingRoleId.value  = null
  roleForm.value       = { name: "", description: "", access_type: "interno" }
  showRoleModal.value  = true
}

function openEditRole(role) {
  editingRoleId.value  = role.id
  roleForm.value       = { name: role.name, description: role.description || "", access_type: role.access_type || "interno" }
  showRoleModal.value  = true
}

async function saveRole() {
  if (!roleForm.value.name.trim()) {
    showToast("El nombre es obligatorio", "warning")
    return
  }
  savingRole.value = true
  try {
    const payload = {
      name:        roleForm.value.name.trim().toUpperCase(),
      description: roleForm.value.description.trim(),
      access_type: roleForm.value.access_type,
    }
    if (editingRoleId.value) {
      await api.put(`/roles/${editingRoleId.value}`, payload)
      showToast("Rol actualizado", "success")
      if (selectedRole.value?.id === editingRoleId.value) {
        selectedRole.value = { ...selectedRole.value, ...payload }
      }
    } else {
      await api.post("/roles/", { ...payload, company_id: activeCompanyId.value })
      showToast("Rol creado", "success")
    }
    showRoleModal.value = false
    await loadRoles()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error guardando rol", "error")
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
  const initCid = companyStore.isSystem ? null : (activeCompanyId.value || null)
  await loadModules(initCid)
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

.role-tabs { display: inline-flex; background: #f1f5f9; border-radius: 10px; padding: 3px; }
.role-tab { border: none; background: none; padding: 6px 14px; border-radius: 8px; font-size: 13px; font-weight: 700; color: #64748b; cursor: pointer; }
.role-tab.active { background: #fff; color: #1d4ed8; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.access-groups { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }
.access-group { border: 1.5px solid #e2e8f0; border-radius: 12px; padding: 10px 12px; }
.access-group-t { font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: .4px; color: #1d4ed8; margin-bottom: 6px; }
.access-item { display: flex; align-items: flex-start; gap: 8px; padding: 5px 0; font-size: 13px; color: #1e293b; cursor: pointer; }
.access-item input { margin-top: 3px; }
.access-item small { display: block; font-size: 11px; color: #64748b; }
@media (max-width: 768px) { .access-groups { grid-template-columns: 1fr; } }
@media (max-width: 576px) { .role-tab { padding: 6px 10px; font-size: 12px; } }
.rol-tipo { display: inline-block; margin-top: 3px; font-size: 11px; font-weight: 700; background: #fef3c7; color: #92400e; border-radius: 6px; padding: 1px 7px; }
</style>
