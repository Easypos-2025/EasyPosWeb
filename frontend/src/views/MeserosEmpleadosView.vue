<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1 class="page-title"><i class="bi bi-person-badge me-2"></i>{{ moduleName }}</h1>
        <p class="page-subtitle">Cada registro queda como empleado y como mesero con el mismo código</p>
      </div>
      <div v-if="!conEscritorio" class="hdr-acc">
        <button v-if="!yo" class="btn btn-outline-primary" @click="abrirAgregarme" :disabled="loading">
          <i class="bi bi-person-plus"></i> Agregarme como mesero
        </button>
        <button class="btn btn-primary" @click="openCreate"><i class="bi bi-plus-lg"></i> Nuevo</button>
      </div>
    </div>

    <div v-if="conEscritorio" class="aviso">
      <i class="bi bi-pc-display"></i>
      Esta empresa trabaja con el programa de escritorio: los meseros y empleados se crean allí y se suben solos a la web.
    </div>

    <div class="filters-row">
      <input v-model="search" class="form-control f-search" :placeholder="`Buscar ${moduleName.toLowerCase()} por nombre, código o teléfono...`" />
      <select v-model="filtroTipo" class="form-select f-sel">
        <option value="">Todos los tipos</option>
        <option v-for="t in $ordenAlfa(tipos, 'name')" :key="t.cod_tipo" :value="String(t.cod_tipo)">{{ t.name }}</option>
      </select>
      <select v-model="filtroEstado" class="form-select f-sel">
        <option value="">Todos</option>
        <option value="1">Activos</option>
        <option value="0">Inactivos</option>
      </select>
      <ExportToolbar :data="filtered" :columns="exportCols" filename="meseros-empleados" :title="moduleName" />
    </div>

    <!-- Tabla (tablet / PC) -->
    <div class="table-card only-desktop">
      <div v-if="loading" class="table-loading"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Código</th>
            <th>Nombre</th>
            <th>Teléfono</th>
            <th>Usuario</th>
            <th>Tipo</th>
            <th>Rol</th>
            <th class="text-center">Estado</th>
            <th v-if="!conEscritorio" class="text-center">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in filtered" :key="p.id" :class="{ 'row-off': !p.status }">
            <td class="text-muted">{{ p.id }}</td>
            <td>
              <strong>{{ p.name }}</strong>
              <span v-if="p.user_id && p.user_id === miUsuario" class="tag tag-yo">Yo</span>
              <span v-if="!p.es_mesero" class="tag" title="No está en meseros">Solo empleado</span>
              <span v-if="!p.es_empleado" class="tag" title="No está en empleados">Solo mesero</span>
            </td>
            <td>{{ p.phone || '—' }}</td>
            <td class="text-muted">{{ p.login || '—' }}</td>
            <td>{{ p.tipo || '—' }}</td>
            <td class="text-muted">{{ p.rol || '—' }}</td>
            <td class="text-center">
              <span class="badge-status" :class="p.status ? 'active' : 'inactive'">{{ p.status ? 'Activo' : 'Inactivo' }}</span>
            </td>
            <td v-if="!conEscritorio" class="text-center">
              <button class="btn btn-sm btn-outline-primary" @click="openEdit(p)" title="Editar"><i class="bi bi-pencil"></i></button>
            </td>
          </tr>
          <tr v-if="!filtered.length">
            <td :colspan="conEscritorio ? 7 : 8" class="text-center text-muted py-4">No hay registros</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Tarjetas (móvil) -->
    <div class="cards only-mobile">
      <div v-if="loading" class="table-loading"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
      <template v-else>
        <div v-for="p in filtered" :key="p.id" class="s-card" :class="{ 'row-off': !p.status }"
             @click="!conEscritorio && openEdit(p)">
          <div class="s-card-top">
            <strong>{{ p.name }} <span v-if="p.user_id && p.user_id === miUsuario" class="tag tag-yo">Yo</span></strong>
            <span class="badge-status" :class="p.status ? 'active' : 'inactive'">{{ p.status ? 'Activo' : 'Inactivo' }}</span>
          </div>
          <div class="s-card-meta">
            <span>#{{ p.id }}</span>
            <span>{{ p.tipo || '—' }}</span>
            <span><i class="bi bi-phone"></i> {{ p.phone || '—' }}</span>
          </div>
        </div>
        <div v-if="!filtered.length" class="text-center text-muted py-4">No hay registros</div>
      </template>
    </div>

    <!-- MODAL CREAR / EDITAR -->
    <div v-if="modal" class="modal-overlay" @click.self="modal = false">
      <div class="modal-box">
        <div class="mh">
          <h3>{{ editing ? `Editar — ${editing.name}` : `Nuevo — ${moduleName}` }}</h3>
          <button class="btn-x" @click="modal = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="mb-area">
          <div class="fg">
            <label>Nombre *</label>
            <input v-model="form.name" class="form-control" maxlength="50" v-focus />
          </div>
          <div class="row2">
            <div class="fg">
              <label>Teléfono *</label>
              <input v-model="form.phone" class="form-control" maxlength="50" inputmode="tel" />
            </div>
            <div class="fg">
              <label>Tipo de empleado *</label>
              <select v-model="form.employee_type" class="form-select">
                <option :value="null">— Seleccione —</option>
                <option v-for="t in $ordenAlfa(tipos, 'name')" :key="t.cod_tipo" :value="t.cod_tipo">{{ t.name }}</option>
              </select>
            </div>
          </div>
          <div class="fg">
            <label>Dirección</label>
            <input v-model="form.address" class="form-control" maxlength="50" />
          </div>
          <div class="row2">
            <div class="fg">
              <label>Usuario de ingreso</label>
              <input v-model="form.login" class="form-control" maxlength="25" placeholder="Se genera si lo deja vacío" />
            </div>
            <div class="fg">
              <label>Clave (PIN) {{ editing ? '' : '*' }}</label>
              <input v-model="form.pin" class="form-control" type="password" inputmode="numeric" maxlength="8"
                     autocomplete="new-password" :placeholder="editing ? 'Déjela vacía para no cambiarla' : '4 a 8 números'" />
            </div>
          </div>
          <div class="row2">
            <div class="fg">
              <label>Rol</label>
              <select v-model="form.role_id" class="form-select">
                <option :value="null">— Por defecto (VENDEDOR-MESERO) —</option>
                <option v-for="r in $ordenAlfa(roles, 'name')" :key="r.id" :value="r.id">{{ r.name }}</option>
              </select>
            </div>
            <div class="fg">
              <label>Estado</label>
              <select v-model="form.status" class="form-select">
                <option :value="1">Activo</option>
                <option :value="0">Inactivo</option>
              </select>
            </div>
          </div>
        </div>
        <div class="mf">
          <button class="btn btn-secondary btn-sm" @click="modal = false">Cancelar</button>
          <button class="btn btn-primary btn-sm" @click="save" :disabled="saving">{{ saving ? 'Guardando...' : 'Guardar' }}</button>
        </div>
      </div>
    </div>

    <AgregarmeMeseroModal v-if="showAgregarme" :tipos="tipos" @close="showAgregarme = false" @creado="onAgregado" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import { ordenAlfa } from "@/utils/orden"
import { useModuleName } from "@/composables/useModuleName"
import ExportToolbar from "@/components/common/ExportToolbar.vue"
import AgregarmeMeseroModal from "@/components/pos/AgregarmeMeseroModal.vue"

const { moduleName } = useModuleName()
const vFocus = { mounted: el => el.focus() }
const PIN = /^\d{4,8}$/

const items         = ref([])
const tipos         = ref([])
const roles         = ref([])
const conEscritorio = ref(false)
const yo            = ref(null)
const miUsuario     = ref(null)
const loading       = ref(true)
const search        = ref("")
const filtroTipo    = ref("")
const filtroEstado  = ref("")
const modal         = ref(false)
const saving        = ref(false)
const editing       = ref(null)
const form          = ref({})
const showAgregarme = ref(false)

const filtered = computed(() => {
  const q = search.value.toLowerCase()
  return ordenAlfa(items.value.filter(p =>
    (!q || (p.name || "").toLowerCase().includes(q) || String(p.id).includes(q) || (p.phone || "").includes(q)) &&
    (filtroTipo.value === "" || String(p.employee_type) === filtroTipo.value) &&
    (filtroEstado.value === "" || String(Number(p.status)) === filtroEstado.value)
  ), "name")
})

const exportCols = [
  { key: "id", label: "Código" },
  { key: "name", label: "Nombre" },
  { key: "phone", label: "Teléfono", fmt: v => v || "" },
  { key: "login", label: "Usuario", fmt: v => v || "" },
  { key: "tipo", label: "Tipo", fmt: v => v || "" },
  { key: "rol", label: "Rol", fmt: v => v || "" },
  { key: "status", label: "Estado", fmt: v => (v ? "Activo" : "Inactivo") },
]

async function load() {
  loading.value = true
  try {
    const [l, t, y] = await Promise.all([api.get("/api/personal/"), api.get("/api/personal/tipos"), api.get("/api/personal/yo")])
    items.value = l.data.items
    conEscritorio.value = l.data.con_escritorio
    tipos.value = t.data
    yo.value = y.data.registro
    miUsuario.value = y.data.registro?.user_id ?? null
  } catch (e) { showToast(e.response?.data?.detail || "Error cargando meseros y empleados", "error") }
  finally { loading.value = false }
  if (!conEscritorio.value) {
    // Mismos roles asignables a meseros que en Configuración TPV
    try { roles.value = (await api.get("/api/pos/tpv/config/roles")).data || [] } catch { roles.value = [] }
  }
}

function vacio() {
  return { name: "", phone: "", address: "", login: "", pin: "", employee_type: null, role_id: null, status: 1 }
}

function openCreate() {
  editing.value = null
  form.value = vacio()
  modal.value = true
}

function openEdit(p) {
  editing.value = p
  form.value = { name: p.name, phone: p.phone || "", address: p.address || "", login: p.login || "", pin: "",
                 employee_type: p.employee_type, role_id: p.role_id || null, status: Number(p.status) ? 1 : 0 }
  modal.value = true
}

async function save() {
  const f = form.value
  if (!f.name.trim()) return showToast("El nombre es obligatorio", "warning")
  if (!f.phone.trim()) return showToast("El teléfono es obligatorio", "warning")
  if (f.employee_type === null) return showToast("Seleccione el tipo de empleado", "warning")
  if (!editing.value && !f.pin) return showToast("La clave (PIN) es obligatoria", "warning")
  if (f.pin && !PIN.test(f.pin)) return showToast("La clave debe tener de 4 a 8 números", "warning")
  const body = { name: f.name.trim(), phone: f.phone.trim(), address: f.address.trim(), login: f.login.trim() || null,
                 employee_type: f.employee_type, role_id: f.role_id, status: f.status }
  if (f.pin) body.pin = f.pin
  saving.value = true
  try {
    if (editing.value) {
      const { data } = await api.put(`/api/personal/${editing.value.id}`, body)
      items.value = items.value.map(x => (x.id === data.id ? data : x))
    } else {
      const { data } = await api.post("/api/personal/", body)
      items.value.push(data)
    }
    modal.value = false
    showToast("Guardado", "success")
  } catch (e) { showToast(e.response?.data?.detail || "Error al guardar", "error") }
  finally { saving.value = false }
}

function abrirAgregarme() { showAgregarme.value = true }
function onAgregado(reg) {
  showAgregarme.value = false
  yo.value = reg
  miUsuario.value = reg.user_id
  items.value.push(reg)
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1100px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; flex-wrap: wrap; margin-bottom: 18px; }
.page-title { font-size: 22px; font-weight: 700; color: #1e293b; margin: 0 0 4px; }
.page-subtitle { font-size: 13px; color: #64748b; margin: 0; }
.hdr-acc { display: flex; gap: 8px; flex-wrap: wrap; }
.aviso { display: flex; gap: 10px; align-items: center; background: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe; border-radius: 10px; padding: 10px 14px; font-size: 13px; margin-bottom: 14px; }
.filters-row { display: flex; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; align-items: center; }
.f-search { max-width: 320px; }
.f-sel { max-width: 180px; }
.table-card { background: #fff; border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,.08); overflow-x: auto; }
.table-loading { padding: 40px; text-align: center; color: #94a3b8; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { background: #f8fafc; color: #475569; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: .4px; padding: 11px 12px; border-bottom: 1px solid #e2e8f0; white-space: nowrap; }
.data-table td { padding: 10px 12px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.data-table tr:hover td { background: #f8fafc; }
.row-off { opacity: .6; }
.text-center { text-align: center; }
.text-muted { color: #94a3b8; font-size: 12px; }
.py-4 { padding: 32px 0; }
.tag { font-size: 10px; font-weight: 700; padding: 1px 7px; border-radius: 20px; margin-left: 6px; background: #f1f5f9; color: #64748b; }
.tag-yo { background: #dcfce7; color: #15803d; }
.badge-status { font-size: 10px; font-weight: 700; padding: 2px 9px; border-radius: 20px; }
.badge-status.active { background: #dcfce7; color: #16a34a; }
.badge-status.inactive { background: #f1f5f9; color: #94a3b8; }
.cards { display: none; flex-direction: column; gap: 8px; }
.s-card { background: #fff; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.07); padding: 12px 14px; cursor: pointer; }
.s-card-top { display: flex; justify-content: space-between; align-items: center; gap: 8px; font-size: 14px; }
.s-card-meta { display: flex; flex-wrap: wrap; gap: 10px; font-size: 12px; color: #64748b; margin-top: 4px; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 2000; padding: 16px; }
.modal-box { background: #fff; border-radius: 16px; width: 100%; max-width: 560px; max-height: 92vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,.2); }
.mh { display: flex; align-items: center; justify-content: space-between; padding: 14px 20px; border-bottom: 1px solid #f1f5f9; }
.mh h3 { font-size: 15px; font-weight: 700; margin: 0; color: #1e293b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.btn-x { background: none; border: none; font-size: 16px; color: #94a3b8; cursor: pointer; }
.mb-area { padding: 18px 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
.mf { padding: 12px 20px 16px; display: flex; justify-content: flex-end; gap: 8px; border-top: 1px solid #f1f5f9; }
.fg { display: flex; flex-direction: column; gap: 4px; }
.fg label { font-size: 12px; font-weight: 600; color: #374151; }
.row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.btn { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #3b82f6; color: #fff; }
.btn:disabled { opacity: .6; cursor: not-allowed; }
.btn-secondary { border: 1.5px solid #e2e8f0; background: #fff; color: #64748b; }
.btn-sm { padding: 6px 12px; font-size: 12px; }
.btn-outline-primary { background: #eff6ff; color: #1d4ed8; border: 1.5px solid #bfdbfe; }
.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }
@media (max-width: 768px) {
  .page-container { padding: 14px; }
  .only-desktop { display: none; }
  .cards.only-mobile { display: flex; }
  .f-search, .f-sel { max-width: none; flex: 1 1 45%; }
  .modal-overlay { padding: 0; align-items: flex-end; }
  .modal-box { max-height: 96vh; border-radius: 16px 16px 0 0; }
}
@media (max-width: 576px) {
  .page-title { font-size: 18px; }
  .hdr-acc, .hdr-acc .btn { width: 100%; justify-content: center; }
  .f-search, .f-sel { flex: 1 1 100%; }
  .row2 { grid-template-columns: 1fr; }
  .mf .btn { flex: 1; justify-content: center; }
}
</style>
