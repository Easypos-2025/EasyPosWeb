
<template>
  <div class="container mt-4 pb-5">

    <!-- INDICADOR DE PLAN -->
    <div v-if="!planInfo.can_add && !isSysAdmin" class="plan-limit-banner">
      <i class="bi bi-lock-fill"></i>
      <div>
        <strong>Límite alcanzado — Plan {{ planInfo.plan_name }}</strong>
        <span>Tienes {{ planInfo.current }} de {{ planInfo.max }} usuarios permitidos.
          Actualiza tu plan para agregar más.</span>
      </div>
    </div>

    <div v-if="planInfo.max !== -1 && !isSysAdmin" class="plan-usage-bar">
      <div class="plan-usage-info">
        <span><i class="bi bi-people"></i> Usuarios: {{ planInfo.current }} / {{ planInfo.max }}</span>
        <span class="plan-name-badge">{{ planInfo.plan_name }}</span>
      </div>
      <div class="usage-track">
        <div
          class="usage-fill"
          :class="planInfo.current >= planInfo.max ? 'fill-red' : planInfo.current >= planInfo.max * 0.8 ? 'fill-amber' : 'fill-green'"
          :style="{ width: Math.min((planInfo.current / planInfo.max) * 100, 100) + '%' }"
        ></div>
      </div>
    </div>

    <!-- FORM -->
    <form @submit.prevent="createUser" autocomplete="off">

      <!-- anti autofill -->
      <input type="text" name="fakeuser" style="display:none">
      <input type="password" name="fakepassword" style="display:none">

      <div class="mb-2">
        <label>Nombre</label>
        <input v-model="form.nombre" class="form-control" placeholder="Nombre" />
      </div>

      <div class="mb-2">
        <label>Email</label>
        <input 
          v-model="form.email"
          type="text"
          class="form-control"
          placeholder="Email"
          autocomplete="new-password"
          name="email_random"
        />
      </div>

      <div class="mb-2">
        <label>Contraseña</label>
        <input 
          v-model="form.password"
          type="password"
          class="form-control"
          placeholder="Password"
          autocomplete="new-password"
          name="password_random"
        />
        <div class="password-rules">

          <small :class="passwordRules.length ? 'text-success' : 'text-danger'">
            ✔ Mínimo 8 caracteres
          </small><br>

          <small :class="passwordRules.upper ? 'text-success' : 'text-danger'">
            ✔ Al menos una mayúscula
          </small><br>

          <small :class="passwordRules.lower ? 'text-success' : 'text-danger'">
            ✔ Al menos una minúscula
          </small><br>

          <small :class="passwordRules.number ? 'text-success' : 'text-danger'">
            ✔ Al menos un número
          </small><br>

          <small :class="passwordRules.special ? 'text-success' : 'text-danger'">
            ✔ Al menos un carácter especial
          </small>

        </div>

      </div>

      <div class="mb-2">
        <label>Seleccione Rol</label>

        <select v-model="form.role_id" class="form-control">
          <option disabled :value="null">
            -- Seleccione un rol --
          </option>

          <option v-for="role in roles" :key="role.id" :value="role.id">
            {{ role.name }}
          </option>
        </select>

      </div>

      <button
        v-if="can('Users', 'can_create')"
        class="btn btn-primary"
        :disabled="!planInfo.can_add && !isSysAdmin"
        :title="!planInfo.can_add && !isSysAdmin ? 'Límite de usuarios alcanzado. Actualiza tu plan.' : ''"
      >
        Crear Usuario
      </button>
      <span v-if="!planInfo.can_add && !isSysAdmin" class="limit-inline-msg">
        <i class="bi bi-lock"></i> Actualiza tu plan para crear más usuarios
      </span>

    </form>

    <!-- ── INVITACIÓN POR LINK ── -->
    <div v-if="isSysAdmin || isAdmin" class="invite-section">
      <div class="invite-section-header">
        <div>
          <strong><i class="bi bi-link-45deg"></i> Invitar por link</strong>
          <small>Genera un link de registro válido por 48 h</small>
        </div>
        <button class="btn btn-outline-primary btn-sm" @click="openInviteModal">
          <i class="bi bi-plus-lg"></i> Generar invitación
        </button>
      </div>
    </div>

    <!-- Modal invitación -->
    <Teleport to="body">
      <div v-if="showInviteModal" class="inv-overlay" @click.self="closeInviteModal">
        <div class="inv-card">
          <div class="inv-header">
            <h3><i class="bi bi-link-45deg"></i> Generar link de invitación</h3>
            <button class="inv-close" @click="closeInviteModal"><i class="bi bi-x-lg"></i></button>
          </div>

          <div class="inv-body" v-if="!inviteLink">
            <label class="inv-label">Selecciona el rol que tendrá el invitado</label>
            <select v-model="inviteRoleId" class="form-control">
              <option :value="null" disabled>-- Selecciona un rol --</option>
              <option v-for="r in roles" :key="r.id" :value="r.id">{{ r.name }}</option>
            </select>
            <button class="btn btn-primary mt-3 w-100" :disabled="!inviteRoleId || generatingInvite" @click="generateInvite">
              <i v-if="generatingInvite" class="bi bi-hourglass-split"></i>
              <i v-else class="bi bi-link-45deg"></i>
              {{ generatingInvite ? 'Generando...' : 'Generar link' }}
            </button>
          </div>

          <div class="inv-body" v-else>
            <p class="inv-success-msg"><i class="bi bi-check-circle-fill text-success"></i> Link generado — válido por 48 horas</p>
            <div class="inv-link-box">
              <span class="inv-link-text">{{ inviteLink }}</span>
              <button class="inv-copy-btn" @click="copyInviteLink" :title="copied ? 'Copiado!' : 'Copiar link'">
                <i :class="copied ? 'bi bi-check-lg' : 'bi bi-clipboard'"></i>
              </button>
            </div>
            <p class="inv-hint">Comparte este link por WhatsApp, correo o mensaje directo.</p>
            <button class="btn btn-outline-secondary btn-sm mt-2" @click="resetInvite">
              <i class="bi bi-arrow-counterclockwise"></i> Generar otro
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <hr />

    <!-- LISTADO -->
    <h4>Usuarios</h4>

    <div class="mb-3">
      <input v-model="search" class="form-control" placeholder="Buscar..." />
    </div>

    <div class="table-responsive">
      <div v-if="isSysAdmin" class="mb-3">
        <select 
          v-model="selectedCompany" 
          @change="handleCompanyChange"
          class="form-control"
        >

          <option :value="null">Mi empresa</option>
          <option value="all">Todas las empresas</option>

          <option 
            v-for="c in companies" 
            :key="c.id" 
            :value="c.id"
          >
            {{ c.name }}
          </option>

        </select>

      </div>

      <table class="table table-bordered">
        <thead>
          <tr>
            <th>Nombre</th>
            <th class="d-none d-md-table-cell">Email</th>
            <th>Rol</th>
            <th>Acciones</th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="user in filteredUsers" :key="user.id">
            <td>{{ user.nombre }}</td>
            <td class="d-none d-md-table-cell">{{ user.email }}</td>
            <td>{{ getRoleName(user.role_id) }}</td>
            <td class="d-flex gap-2">
              <button v-if="can('Users', 'can_edit')" class="btn btn-sm btn-warning" @click="openEdit(user)">
                Editar
              </button>
              <button v-if="can('Users', 'can_delete')" class="btn btn-sm btn-danger" @click="askDeleteUser(user.id)">
                Eliminar
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

  </div>

  <!-- MODAL EDIT -->
  <div v-if="showModal" class="modal-backdrop">
    <div class="modal-card">

      <h5>Editar Usuario</h5>

      <input v-model="editForm.nombre" class="form-control mb-2" />
      <input v-model="editForm.email" class="form-control mb-2" />
      <div class="mb-2">
        <label class="d-flex align-items-center gap-2">
          <input type="checkbox" v-model="editForm.is_active" />
          <span>Usuario activo</span>
        </label>
      </div>

      <div class="mb-2">
        <label>Rol</label>
        <select v-model="editForm.role_id" class="form-control">
          <option v-for="role in roles" :key="role.id" :value="role.id">
            {{ role.name }}
          </option>
        </select>
      </div>

      <div class="d-flex gap-2">
        <button class="btn btn-primary" @click="updateUser">Guardar</button>
        <button class="btn btn-secondary" @click="closeModal">Cancelar</button>
      </div>

    </div>
  </div>
<div v-if="showDeleteModal" class="modal-backdrop">
  <div class="modal-card">

    <h5>Eliminar Usuario</h5>
    <p>¿Estás seguro?</p>

    <div class="d-flex gap-2">
      <button class="btn btn-danger" @click="confirmDelete">
        Eliminar
      </button>

      <button class="btn btn-secondary" @click="showDeleteModal=false">
        Cancelar
      </button>
    </div>

  </div>
</div>

</template>

<script setup>
import { ref, onMounted, computed } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"


const search = ref("")
const roles = ref([])

const companies = ref([])
const showModal = ref(false)
const showDeleteModal = ref(false)
const userToDelete = ref(null)
const currentUser = JSON.parse(localStorage.getItem("user")) || {}
const isSysAdmin  = currentUser.is_system
const isAdmin     = (currentUser.role || "").toLowerCase().includes("admin")

const planInfo = ref({ current: 0, max: -1, plan_name: "", can_add: true })
const usersRaw = ref([])
const selectedCompany = ref(null)
const permissions = ref([])

// ── Invitación por link ──────────────────────────────
const showInviteModal  = ref(false)
const inviteRoleId     = ref(null)
const inviteLink       = ref("")
const generatingInvite = ref(false)
const copied           = ref(false)

function openInviteModal()  { showInviteModal.value = true }
function closeInviteModal() { showInviteModal.value = false; resetInvite() }
function resetInvite()      { inviteLink.value = ""; inviteRoleId.value = null; copied.value = false }

async function generateInvite() {
  if (!inviteRoleId.value) return
  generatingInvite.value = true
  try {
    const payload = { role_id: inviteRoleId.value }
    // Si SYSADMIN tiene empresa seleccionada, la incluye
    if (isSysAdmin && selectedCompany.value && selectedCompany.value !== "all") {
      payload.company_id = selectedCompany.value
    }
    const res = await api.post("/invitations", payload)
    inviteLink.value = `${window.location.origin}/invite/${res.data.token}`
  } catch (e) {
    showToast(e.response?.data?.detail || "Error generando invitación", "error")
  } finally {
    generatingInvite.value = false
  }
}

async function copyInviteLink() {
  try {
    await navigator.clipboard.writeText(inviteLink.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    showToast("No se pudo copiar, cópialo manualmente", "warning")
  }
}



const form = ref({
  nombre: "",
  email: "",
  password: "",
  role_id: null,
  is_active: true
})

const editForm = ref({
  id: null,
  nombre: "",
  email: "",
  role_id: null,
  is_active: true
})



const passwordRules = computed(() => {

  const value = form.value.password || ""

  return {
    length: value.length >= 8,
    upper: /[A-Z]/.test(value),
    lower: /[a-z]/.test(value),
    number: /[0-9]/.test(value),
    special: /[!@#$%^&*(),.?":{}|<>]/.test(value)
  }

})


const loadCompanies = async () => {
  try {
    //console.log("➡️ loadCompanies START")
  

    const res = await api.get("/companies/")
    //console.log("🏢 COMPANIES DATA:", res.data) 
    //console.log("✅ loadCompanies OK")
    companies.value = res.data
  } catch (e) {
    //console.log("🏢 COMPANIES:", res.data)  
    showToast("Error cargando empresas", "error")
  }
}

const resetForm = () => {
  form.value = {
    nombre: "",
    email: "",
    password: "",
    role_id: null
  }
}

const filteredUsers = computed(() => {
  //
  return usersRaw.value.filter(u => {

    // 🔥 EMPRESA
    const matchCompany =
      selectedCompany.value === null ||
      selectedCompany.value === "all" ||
      u.company_id == selectedCompany.value

    // 🔥 BUSQUEDA
    const matchName =
      !search.value ||
      u.nombre.toLowerCase().includes(search.value.toLowerCase())
    //console.log("➡️ filteredUsers return",matchCompany && matchName)
    return matchCompany && matchName
  })

})


const loadRoles = async (companyId = null) => {
  try {
    let url = "/roles/"
    if (isSysAdmin) {
      const cid = companyId
        || (selectedCompany.value && selectedCompany.value !== "all" ? selectedCompany.value : null)
        || JSON.parse(localStorage.getItem("selected_company") || "null")?.id
      if (cid) url = `/roles/?company_id=${cid}`
    }
    const res = await api.get(url)
    roles.value = res.data
  } catch {
    roles.value = []
  }
}

const loadUsers = async (companyId = null) => {
  //console.log("➡️ loadUsers START", companyId)
  let url = "/users/"
   
  if (companyId !== null && companyId !== undefined) {
    url += `?company_id=${companyId}`
  }

  const res = await api.get(url)
  //console.log("✅ loadUsers OK")
  usersRaw.value = Array.isArray(res.data)
    ? res.data
    : (res.data.data || [])

  //console.log("🟢 RESPONSE DATA:", res.data)
}


const loadCurrentUser = async () => {
  //console.log("➡️ loadCurrentUser START") 
  const res = await api.get("/auth/me/")
  //console.log("✅ loadCurrentUser OK")
  //console.log("✅ loadCurrentUser DATA,res.data")
  currentUser.value = res.data
}


const handleCompanyChange = async () => {

  const currentUser = JSON.parse(localStorage.getItem("user"))

  if (selectedCompany.value === null) {
    await loadUsers(currentUser.company_id)
    await loadRoles(currentUser.company_id)
    return
  }

  if (selectedCompany.value === "all") {
    await loadUsers("all")
    return
  }

  await loadUsers(selectedCompany.value)
  await loadRoles(selectedCompany.value)
}


const getRoleName = (id) => {
  const r = roles.value.find(x => x.id === id)
  return r ? r.name : "N/A"
}

const createUser = async () => {
  if (!form.value.nombre || !form.value.email || !form.value.password || !form.value.role_id) {
    showToast("Todos los campos son obligatorios","error")
    return
  }
  if (!Object.values(passwordRules.value).every(v => v)) {
    showToast("La contraseña no cumple los requisitos", "error")
    return
  }

  const currentUser = JSON.parse(localStorage.getItem("user"))

  try {
    await api.post("/users/", { ...form.value, company_id: currentUser.company_id }) 
    showToast("Usuario creado","success")
    resetForm()
    loadUsers()
    loadPlanLimit()
  } catch (e) {
    const errors = e.response?.data?.detail

    if (Array.isArray(errors)) {
      // 🔥 errores de validación Pydantic
      const msg = errors.map(err => err.msg).join(", ")
      showToast(msg, "error")
    } else {
      showToast(errors || "Error", "error")
    }
  }
}

const openEdit = (u) => {
  editForm.value = {
    id: u.id,
    nombre: u.nombre,
    email: u.email,
    role_id: u.role_id,
    is_active: u.is_active
  }

  showModal.value = true
}


const closeModal = () => showModal.value = false

const updateUser = async () => {
  try {
    await api.put(`/users/${editForm.value.id}`, editForm.value)
    showToast("Actualizado","success")
    closeModal()
    loadUsers()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error","error")
  }
}

const askDeleteUser = (id) => {
  userToDelete.value = id
  showDeleteModal.value = true
}

const confirmDelete = async () => {
  try {
    await api.delete(`/users/${userToDelete.value}`)

    showToast("Usuario eliminado", "success")

    showDeleteModal.value = false
    userToDelete.value = null

    await loadUsers()

  } catch (e) {
    showToast(e.response?.data?.detail || "Error", "error")
  }
}

const loadPlanLimit = async () => {
  try {
    const res = await api.get("/users/plan-limit")
    planInfo.value = res.data
  } catch {}
}

const loadPermissions = async () => {
  try {
    //console.log("➡️ loadPermissions START")   
    const resUser = await api.get("/auth/me/")
    //console.log("👤 auth/me OK")
    const roleId = resUser.data.role_id
    //console.log("ROLE ID:", roleId)
    const res = await api.get(`/roles/${roleId}/modules/`)
    //console.log("✅ loadPermissions OK")
    //console.log("✅ loadPermissions DATA OK",res.data)
    permissions.value = res.data
    // 🔥 DEBUG AQUÍ
    //console.log("PERMISSIONS:", permissions.value)

  } catch (error) {
    console.error("Error loading permissions", error)
  }
}

const can = (moduleName, action) => {

  // 💥 SYSADMIN TODO
  if (currentUser?.is_system) return true
   
  const mod = permissions.value.find(p => 
    p.module_name?.toLowerCase().trim() === moduleName.toLowerCase().trim()
  )

  if (!mod) return false

  return mod[action] === true
}



onMounted(async () => {
  loadRoles()
  loadCompanies()
  await loadCurrentUser()
  await loadPermissions()
  await loadPlanLimit()

  // 🔥 obtener usuario actual
  const res = await api.get("/auth/me/")

  const user = res.data

  //console.log("👤 USER LOGUEADO:", user)
  //console.log("👤 COMPANY :", user.company_id)
  // 🔥 cargar SOLO su empresa
  await loadUsers(user.company_id)

  // 🔥 setear select en su empresa
  selectedCompany.value = user.company_id

})


</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  top:0;left:0;width:100%;height:100%;
  background: rgba(0,0,0,.5);
  display:flex;align-items:center;justify-content:center;
}
.modal-card {
  background:#fff;padding:20px;border-radius:8px;
  width:100%;max-width:400px;
}

/* ── PLAN LIMIT BANNER ── */
.plan-limit-banner {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: #fef2f2;
  border: 1px solid #fca5a5;
  border-left: 4px solid #ef4444;
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 16px;
  color: #7f1d1d;
}

.plan-limit-banner .bi { font-size: 20px; color: #ef4444; flex-shrink: 0; margin-top: 1px; }
.plan-limit-banner div { display: flex; flex-direction: column; gap: 3px; }
.plan-limit-banner strong { font-size: 14px; }
.plan-limit-banner span  { font-size: 13px; opacity: 0.85; }

/* ── BARRA DE USO ── */
.plan-usage-bar {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 10px 14px;
  margin-bottom: 16px;
}

.plan-usage-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  font-size: 13px;
  color: #475569;
}

.plan-name-badge {
  font-size: 11px;
  font-weight: 700;
  background: #dbeafe;
  color: #1e40af;
  padding: 2px 8px;
  border-radius: 20px;
}

.usage-track {
  height: 6px;
  background: #e2e8f0;
  border-radius: 3px;
  overflow: hidden;
}

.usage-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.4s ease;
}

.fill-green { background: #22c55e; }
.fill-amber  { background: #f59e0b; }
.fill-red    { background: #ef4444; }

/* ── MENSAJE INLINE ── */
.limit-inline-msg {
  font-size: 12px;
  color: #ef4444;
  margin-left: 10px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

/* ── Invitación ── */
.invite-section {
  margin: 16px 0;
  padding: 14px 16px;
  background: #f0f7ff;
  border: 1px solid #bfdbfe;
  border-radius: 10px;
}
.invite-section-header {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
}
.invite-section-header strong {
  display: flex; align-items: center; gap: 6px;
  font-size: 14px; color: #1e40af;
}
.invite-section-header small {
  display: block; font-size: 12px; color: #64748b; font-weight: 400; margin-top: 2px;
}

.inv-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center;
  z-index: 1500; padding: 16px;
}
.inv-card {
  background: #fff; border-radius: 14px;
  width: 100%; max-width: 480px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  overflow: hidden;
}
.inv-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #f1f5f9;
}
.inv-header h3 {
  font-size: 16px; font-weight: 700; color: #1e293b; margin: 0;
  display: flex; align-items: center; gap: 8px;
}
.inv-close {
  background: none; border: none; font-size: 16px;
  cursor: pointer; color: #94a3b8;
}
.inv-close:hover { color: #1e293b; }
.inv-body { padding: 20px; display: flex; flex-direction: column; }
.inv-label { font-size: 13px; font-weight: 600; color: #374151; margin-bottom: 8px; }

.inv-success-msg {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; font-weight: 600; color: #1e293b; margin: 0 0 12px;
}
.inv-link-box {
  display: flex; align-items: center; gap: 8px;
  background: #f8fafc; border: 1px solid #e2e8f0;
  border-radius: 8px; padding: 10px 12px;
}
.inv-link-text {
  flex: 1; font-size: 12px; color: #475569;
  word-break: break-all; line-height: 1.4;
}
.inv-copy-btn {
  background: #3b82f6; border: none; color: #fff;
  border-radius: 6px; padding: 6px 10px;
  cursor: pointer; font-size: 14px; flex-shrink: 0;
  transition: background 0.15s;
}
.inv-copy-btn:hover { background: #2563eb; }
.inv-hint { font-size: 12px; color: #94a3b8; margin: 8px 0 0; }
</style>