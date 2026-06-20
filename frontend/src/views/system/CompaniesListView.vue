<template>
  <div class="p-3">

    <!-- FILTROS (sticky) -->
    <div class="filters-bar">
      <input type="text" class="form-control fc-search" placeholder="Buscar empresa, NIT o ID..." v-model="search" />
      <select class="form-select fc-select" v-model="filterState">
        <option value="">Todos los estados</option>
        <option value="1">Activos</option>
        <option value="0">Inactivos</option>
      </select>
      <select class="form-select fc-select" v-model="filterProfile">
        <option value="">Todos los perfiles</option>
        <option v-for="p in profiles" :key="p.id" :value="p.id">{{ p.name }}</option>
      </select>
      <select class="form-select fc-select" v-model="filterPlan">
        <option value="">Todos los planes</option>
        <option v-for="p in planOptions" :key="p.id" :value="p.id">{{ p.name }}</option>
        <option value="none">Sin plan</option>
      </select>
    </div>

    <!-- TABLA -->
    <div class="card mt-3 table-responsive">
      <table class="table table-hover mb-0">
        <thead class="table-light">
          <tr>
            <th class="col-id">ID</th>
            <th>Nombre</th>
            <th class="d-none d-sm-table-cell">NIT</th>
            <th class="d-none d-md-table-cell">Perfil</th>
            <th class="d-none d-md-table-cell">Plan</th>
            <th class="d-none d-lg-table-cell">Email</th>
            <th>Estado</th>
            <th class="col-acciones">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in filteredCompanies" :key="c.id">
            <td class="col-id"><span class="id-chip">{{ c.id }}</span></td>
            <td>
              <span class="company-name" @click="openEdit(c)" :title="'ID: ' + c.id">{{ c.name }}</span>
            </td>
            <td class="d-none d-sm-table-cell text-muted" style="font-size:12px">{{ c.identification_number }}</td>
            <td class="d-none d-md-table-cell">{{ c.business_profile_name || '—' }}</td>
            <td class="d-none d-md-table-cell">
              <span class="plan-chip" :class="!c.plan_id ? 'plan-chip--none' : 'plan-chip--ok'">
                {{ c.plan_name || 'Sin plan' }}
              </span>
            </td>
            <td class="d-none d-lg-table-cell text-muted" style="font-size:12px">{{ c.email }}</td>
            <td>
              <span :class="Number(c.state) === 1 ? 'badge bg-success' : 'badge bg-secondary'">
                {{ Number(c.state) === 1 ? 'Activo' : 'Inactivo' }}
              </span>
            </td>
            <td>
              <div class="acciones-wrap">
                <button class="btn btn-warning btn-sm btn-accion" @click="openEdit(c)" title="Editar">
                  <i class="bi bi-pencil-fill"></i>
                  <span class="d-none d-md-inline ms-1">Editar</span>
                </button>
                <button class="btn btn-danger btn-sm btn-accion" @click="handleDelete(c)" title="Eliminar">
                  <i class="bi bi-trash-fill"></i>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="filteredCompanies.length === 0">
            <td colspan="8" class="text-center text-muted py-4">No hay resultados</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- MODAL EDITAR -->
    <div v-if="showEdit" class="modal-overlay" @click.self="closeEdit">
      <div class="modal-box">
        <div class="modal-header-bar">
          <div>
            <h2>Editar empresa</h2>
            <span class="modal-id-tag">ID {{ editForm.id }}</span>
          </div>
          <button class="btn-close-sm" @click="closeEdit"><i class="bi bi-x-lg"></i></button>
        </div>

        <div class="modal-body-area">

          <!-- Datos generales -->
          <div class="section-title"><i class="bi bi-building me-1"></i>Datos generales</div>

          <div class="form-row2">
            <div class="fg">
              <label>Nombre *</label>
              <input v-model="editForm.name" data-v="nombre" class="form-control" @input="clearError($event)" />
            </div>
            <div class="fg">
              <label>NIT / Identificación *</label>
              <input v-model="editForm.identification_number" data-v="nit" class="form-control" @input="clearError($event)" />
            </div>
          </div>
          <div class="form-row2">
            <div class="fg">
              <label>DV *</label>
              <input v-model="editForm.dv" data-v="dv" class="form-control" maxlength="2" @input="clearError($event)" />
            </div>
            <div class="fg">
              <label>Teléfono *</label>
              <input v-model="editForm.phone" data-v="telefono" class="form-control" @input="clearError($event)" />
            </div>
          </div>
          <div class="fg">
            <label>Email *</label>
            <input v-model="editForm.email" type="email" data-v="email" class="form-control" @input="clearError($event)" />
          </div>
          <div class="fg">
            <label>Dirección *</label>
            <input v-model="editForm.address" data-v="direccion" class="form-control" @input="clearError($event)" />
          </div>
          <div class="fg">
            <label>Descripción</label>
            <textarea v-model="editForm.description" class="form-control" rows="2" />
          </div>
          <div class="form-row2">
            <div class="fg">
              <label>Perfil de negocio *</label>
              <select v-model="editForm.business_profile_id" data-v="perfil" class="form-select" @change="clearError($event)">
                <option value="">— Seleccionar —</option>
                <option v-for="p in profiles" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
            </div>
            <div class="fg">
              <label>Estado</label>
              <select v-model="editForm.state" class="form-select">
                <option :value="1">Activo</option>
                <option :value="0">Inactivo</option>
              </select>
            </div>
          </div>

          <!-- SIDEBAR DERECHO -->
          <div class="fg">
            <label>Panel lateral derecho (publicidad)</label>
            <button type="button"
              class="sidebar-toggle-btn"
              :class="editForm.show_sidebar_right ? 'stb--on' : 'stb--off'"
              @click="editForm.show_sidebar_right = editForm.show_sidebar_right ? 0 : 1"
            >
              <span class="stb-track"><span class="stb-thumb"></span></span>
              <span class="stb-label">
                {{ editForm.show_sidebar_right ? 'Visible para esta empresa' : 'Oculto — empresa no verá el panel de publicidad' }}
              </span>
            </button>
          </div>

          <!-- PLAN -->
          <div class="section-title mt-2"><i class="bi bi-award me-1"></i>Plan asignado</div>

          <div class="plan-current-bar" v-if="editForm.plan_id">
            <i class="bi bi-check-circle-fill" style="color:#10b981"></i>
            Plan activo: <strong>{{ editForm.plan_name }}</strong>
            <span v-if="editForm.expiration_date" class="plan-exp">
              · Vence: {{ editForm.expiration_date }}
            </span>
            <span v-else class="plan-exp">· Sin vencimiento</span>
          </div>
          <div class="plan-current-bar plan-current-bar--none" v-else>
            <i class="bi bi-exclamation-circle-fill" style="color:#f59e0b"></i>
            Esta empresa no tiene plan asignado
          </div>

          <div class="form-row2">
            <div class="fg">
              <label>{{ editForm.plan_id ? 'Cambiar plan' : 'Asignar plan' }}</label>
              <select v-model="planForm.plan_id" class="form-select">
                <option value="">— Mantener actual —</option>
                <option v-for="p in plans" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
            </div>
            <div class="fg">
              <label>Fecha vencimiento <small class="text-muted">(vacío = indefinido)</small></label>
              <CustomDatePicker v-model="planForm.expiration_date" />
            </div>
          </div>

        </div>

        <div class="modal-footer-bar">
          <button class="btn btn-secondary" @click="closeEdit">Cancelar</button>
          <button class="btn btn-primary" @click="saveEdit" :disabled="saving">
            <i v-if="saving" class="bi bi-arrow-repeat spin me-1"></i>
            {{ saving ? 'Guardando...' : 'Guardar cambios' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import { validateForm } from "@/utils/validate"
import CustomDatePicker from "@/components/common/CustomDatePicker.vue"

const companies     = ref([])
const profiles      = ref([])
const plans         = ref([])
const search        = ref("")
const filterState   = ref("")
const filterProfile = ref("")
const filterPlan    = ref("")
const showEdit      = ref(false)
const saving        = ref(false)
const editForm      = ref({})
const planForm      = ref({ plan_id: "", expiration_date: "" })

const planOptions = computed(() => {
  const seen = new Set()
  const opts = []
  for (const c of companies.value) {
    if (c.plan_id && !seen.has(c.plan_id)) {
      seen.add(c.plan_id)
      opts.push({ id: c.plan_id, name: c.plan_name })
    }
  }
  return opts.sort((a, b) => a.name.localeCompare(b.name))
})

const loadCompanies = async () => {
  try {
    const res = await api.get("/companies/")
    companies.value = res.data
  } catch {
    showToast("Error cargando empresas", "error")
  }
}

const loadProfiles = async () => {
  try {
    const res = await api.get("/business-profiles/")
    profiles.value = res.data.data || res.data
  } catch {}
}

const loadPlans = async () => {
  try {
    const res = await api.get("/plans/")
    plans.value = res.data.filter(p => p.is_active)
  } catch {}
}

const filteredCompanies = computed(() =>
  companies.value.filter(c => {
    const q = (search.value || "").toLowerCase()
    const matchSearch  = !q || (c.name || "").toLowerCase().includes(q)
                             || (c.identification_number || "").toLowerCase().includes(q)
                             || String(c.id).includes(q)
    const matchState   = filterState.value === "" || Number(c.state ?? 0) === Number(filterState.value)
    const matchProfile = filterProfile.value === "" || Number(c.business_profile_id) === Number(filterProfile.value)
    const matchPlan    = filterPlan.value === ""
                         || (filterPlan.value === "none" && !c.plan_id)
                         || Number(c.plan_id) === Number(filterPlan.value)
    return matchSearch && matchState && matchProfile && matchPlan
  })
)

function openEdit(c) {
  editForm.value = {
    id:                    c.id,
    name:                  c.name,
    identification_number: c.identification_number,
    dv:                    c.dv || "",
    phone:                 c.phone || "",
    email:                 c.email || "",
    address:               c.address || "",
    description:           c.description || "",
    business_profile_id:   c.business_profile_id,
    language_id:           c.language_id || 80,
    country_id:            c.country_id  || 46,
    department_id:         c.department_id || 1,
    municipality_id:       c.municipality_id || 1,
    type_currency_id:      c.type_currency_id || 35,
    state:                 c.state ?? 1,
    show_sidebar_right:    c.show_sidebar_right ?? 1,
    plan_id:               c.plan_id || null,
    plan_name:             c.plan_name || "Sin plan",
    expiration_date:       c.expiration_date || null,
  }
  planForm.value = { plan_id: "", expiration_date: c.expiration_date || "" }
  showEdit.value = true
}

function closeEdit() {
  document.querySelectorAll(".field-invalid").forEach(el => el.classList.remove("field-invalid"))
  showEdit.value = false
}

function clearError(e) {
  e.target.classList.remove("field-invalid")
}

async function saveEdit() {
  const f = editForm.value

  const check = validateForm([
    { value: f.name,                  selector: '[data-v="nombre"]',    label: "Nombre" },
    { value: f.identification_number, selector: '[data-v="nit"]',       label: "NIT / Identificación" },
    { value: f.dv,                    selector: '[data-v="dv"]',        label: "DV" },
    { value: f.phone,                 selector: '[data-v="telefono"]',  label: "Teléfono" },
    { value: f.email,                 selector: '[data-v="email"]',     label: "Email" },
    { value: f.address,               selector: '[data-v="direccion"]', label: "Dirección" },
    { value: f.business_profile_id,   selector: '[data-v="perfil"]',    label: "Perfil de negocio" },
  ])

  if (!check.valid) {
    showToast(check.message, "warning")
    return
  }

  // Advertir si cambió el perfil de negocio
  const original = companies.value.find(c => c.id === f.id)
  if (original && original.business_profile_id !== f.business_profile_id) {
    const { isConfirmed } = await window.Swal.fire({
      title: "¿Cambiar perfil de negocio?",
      html: `<p>Los usuarios de esta empresa pueden tener roles asignados al perfil <strong>${original.business_profile_name || 'anterior'}</strong>.</p>
             <p>Al cambiar al perfil <strong>${profiles.value.find(p => p.id === f.business_profile_id)?.name || 'nuevo'}</strong>, esos roles podrían no existir en el nuevo perfil.</p>
             <p><small>Deberás revisar y reasignar los roles de los usuarios manualmente.</small></p>`,
      icon: "warning",
      showCancelButton: true,
      confirmButtonText: "Sí, cambiar perfil",
      cancelButtonText: "Cancelar",
      confirmButtonColor: "#f59e0b"
    })
    if (!isConfirmed) return
  }

  saving.value = true
  try {
    // 1. Guardar datos de la empresa
    await api.put(`/companies/${f.id}`, f)

    // 2. Si se seleccionó un plan nuevo, asignarlo
    if (planForm.value.plan_id) {
      const planPayload = {
        plan_id: Number(planForm.value.plan_id),
        expiration_date: planForm.value.expiration_date || null,
      }
      const planRes = await api.post(`/company-plan/${f.id}`, planPayload)
      const data = planRes.data

      if (data.downgrade_applied) {
        const total = Object.values(data.blocked_summary || {}).reduce((s, arr) => s + arr.length, 0)
        showToast(`Plan asignado. ${total} registro(s) bloqueados por downgrade.`, "warning")
      } else {
        showToast(`Empresa actualizada · Plan: ${data.plan_name}`, "success")
      }
    } else {
      showToast("Empresa actualizada correctamente", "success")
    }

    closeEdit()
    await loadCompanies()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error guardando cambios", "error")
  } finally {
    saving.value = false
  }
}

async function handleDelete(c) {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar "${c.name}"?`,
    html: `<small>Los usuarios de esta empresa quedarán sin empresa asignada.<br>Esta acción no se puede deshacer.</small>`,
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, eliminar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/companies/${c.id}`)
    showToast("Empresa eliminada", "success")
    await loadCompanies()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error eliminando empresa", "error")
  }
}

onMounted(() => {
  loadCompanies()
  loadProfiles()
  loadPlans()
})
</script>

<style scoped>
/* ── Filtros sticky ── */
.filters-bar {
  position: sticky;
  top: 0;
  z-index: 20;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 10px 14px;
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
  box-shadow: 0 2px 8px rgba(0,0,0,.06);
}
.fc-search { flex: 1 1 180px; min-width: 130px; }
.fc-select  { flex: 0 1 160px; min-width: 120px; }

/* ── Tabla ── */
.col-id       { width: 52px; text-align: center; }
.col-acciones { width: 110px; white-space: nowrap; }
.id-chip {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  background: #f1f5f9;
  border-radius: 5px;
  padding: 2px 6px;
  font-family: monospace;
}
.company-name {
  cursor: pointer;
  font-weight: 500;
  color: #1e40af;
}
.company-name:hover { text-decoration: underline; }

.plan-chip {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 20px;
  white-space: nowrap;
}
.plan-chip--ok   { background: #eff6ff; color: #1d4ed8; }
.plan-chip--none { background: #fef2f2; color: #dc2626; }

.acciones-wrap { display: flex; gap: 6px; align-items: center; }
.btn-accion {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  padding: 0 10px;
  white-space: nowrap;
}

/* ── Modal ── */
.modal-overlay   { position: fixed; inset: 0; background: rgba(0,0,0,0.45); display: flex; align-items: center; justify-content: center; z-index: 1050; padding: 12px; }
.modal-box       { background: #fff; border-radius: 16px; width: 640px; max-width: 100%; max-height: 92vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
.modal-header-bar {
  display: flex; align-items: flex-start; justify-content: space-between;
  padding: 16px 22px 12px; border-bottom: 1px solid #f1f5f9; flex-shrink: 0; gap: 8px;
}
.modal-header-bar h2 { font-size: 16px; font-weight: 700; color: #1e293b; margin: 0 0 3px; }
.modal-id-tag { font-size: 11px; font-weight: 700; color: #64748b; background: #f1f5f9; padding: 1px 7px; border-radius: 20px; font-family: monospace; }
.modal-body-area { padding: 16px 22px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
.modal-footer-bar { padding: 12px 22px 16px; display: flex; justify-content: flex-end; gap: 10px; border-top: 1px solid #f1f5f9; flex-shrink: 0; }
.form-row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.fg { display: flex; flex-direction: column; gap: 4px; }
.fg label { font-size: 13px; font-weight: 500; color: #374151; }
.btn-close-sm { background: none; border: none; font-size: 18px; cursor: pointer; color: #94a3b8; border-radius: 6px; padding: 4px 8px; }
.btn-close-sm:hover { background: #f1f5f9; color: #1e293b; }
.mt-2 { margin-top: 8px; }

.section-title {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: .5px;
  padding-bottom: 6px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
}

/* Plan bar */
.plan-current-bar {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  padding: 8px 12px;
  color: #166534;
  flex-wrap: wrap;
}
.plan-current-bar--none {
  background: #fffbeb;
  border-color: #fde68a;
  color: #92400e;
}
.plan-exp { font-size: 12px; color: #64748b; }

/* Sidebar right toggle */
.sidebar-toggle-btn {
  display: inline-flex; align-items: center; gap: 10px;
  background: none; border: 1.5px solid #e2e8f0; border-radius: 8px;
  padding: 7px 12px; cursor: pointer; font-size: .82rem; font-weight: 600;
  transition: border-color .15s, background .15s; width: 100%;
}
.stb-track {
  position: relative; width: 34px; height: 18px; border-radius: 9px;
  background: #cbd5e1; flex-shrink: 0; transition: background .2s;
}
.stb-thumb {
  position: absolute; top: 2px; left: 2px; width: 14px; height: 14px;
  border-radius: 50%; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,.25);
  transition: left .2s;
}
.stb--on .stb-track { background: #22c55e; }
.stb--on .stb-thumb { left: 18px; }
.stb--on  { border-color: #bbf7d0; background: #f0fdf4; color: #15803d; }
.stb--off { border-color: #e2e8f0; color: #94a3b8; }
.stb-label { display: flex; align-items: center; gap: 5px; }

.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }

/* ── Responsive ── */
@media (max-width: 768px) {
  .modal-box { border-radius: 12px; }
  .modal-body-area { padding: 14px 16px; }
  .modal-header-bar { padding: 14px 16px 10px; }
  .modal-footer-bar { padding: 10px 16px 14px; }
  .col-acciones { width: 80px; }
  .btn-accion { padding: 0 7px; }
}
@media (max-width: 576px) {
  .filters-bar { padding: 8px 10px; gap: 8px; }
  .fc-search, .fc-select { flex: 1 1 100%; }
  .form-row2 { grid-template-columns: 1fr; }
  .sidebar-toggle-btn { font-size: .78rem; }
  .col-id { display: none; }
}
</style>
