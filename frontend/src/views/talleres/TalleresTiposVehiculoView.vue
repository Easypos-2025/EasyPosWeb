<template>
  <div class="page-container">

    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title"><i class="bi bi-car-front-fill"></i> Tipos de Vehículo</h1>
        <p class="page-subtitle">Configura las categorías de vehículos que atiende el taller.</p>
      </div>
      <button class="btn btn-primary" @click="openCreate">
        <i class="bi bi-plus-lg"></i> Nuevo tipo
      </button>
    </div>

    <!-- Grid de tipos -->
    <div v-if="loading" class="loading-center">
      <i class="bi bi-arrow-repeat spin"></i> Cargando…
    </div>

    <div v-else class="tipos-grid">
      <div
        v-for="t in tipos"
        :key="t.id"
        class="tipo-card"
        :class="{ inactive: !t.activo }"
      >
        <div class="tipo-icon">
          <i :class="`bi ${t.icono}`"></i>
        </div>
        <div class="tipo-info">
          <span class="tipo-nombre">{{ t.nombre }}</span>
          <span class="tipo-badge" :class="t.activo ? 'badge-active' : 'badge-inactive'">
            {{ t.activo ? 'Activo' : 'Inactivo' }}
          </span>
        </div>
        <div class="tipo-actions">
          <button class="btn-icon" @click="openEdit(t)" title="Editar">
            <i class="bi bi-pencil"></i>
          </button>
          <button class="btn-icon" @click="toggleActivo(t)" :title="t.activo ? 'Desactivar' : 'Activar'">
            <i :class="t.activo ? 'bi bi-toggle-on text-success' : 'bi bi-toggle-off text-muted'"></i>
          </button>
        </div>
      </div>

      <div v-if="tipos.length === 0" class="empty-state">
        <i class="bi bi-car-front"></i>
        <p>Sin tipos de vehículo. Crea el primero.</p>
      </div>
    </div>

    <!-- Modal crear/editar -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-box">
        <div class="mh">
          <h3><i class="bi bi-car-front-fill"></i> {{ editing ? 'Editar Tipo' : 'Nuevo Tipo' }}</h3>
          <button class="btn-x" @click="showModal = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="mb-area">
          <div class="fg">
            <label>Nombre *</label>
            <input v-model="form.nombre" class="form-control" placeholder="Ej: Automóvil / Carro" autofocus />
          </div>

          <!-- Selección de ícono -->
          <div class="fg">
            <label>Ícono Bootstrap Icons</label>
            <div class="icon-picker">
              <button
                v-for="ic in ICONOS_OPCIONES"
                :key="ic.value"
                class="ic-opt"
                :class="{ selected: form.icono === ic.value }"
                @click="form.icono = ic.value"
                :title="ic.label"
              >
                <i :class="`bi ${ic.value}`"></i>
                <span>{{ ic.label }}</span>
              </button>
            </div>
            <div class="icon-preview">
              Seleccionado: <i :class="`bi ${form.icono}`" style="font-size:20px; margin-left:6px;"></i>
              <span class="text-muted" style="font-size:12px; margin-left:6px;">{{ form.icono }}</span>
            </div>
          </div>

          <div class="fg">
            <label>Orden de visualización</label>
            <input v-model.number="form.orden" type="number" min="0" step="1" class="form-control" style="max-width:120px" />
          </div>
        </div>
        <div class="mf">
          <button class="btn btn-secondary btn-sm" @click="showModal = false">Cancelar</button>
          <button class="btn btn-primary btn-sm" @click="submit" :disabled="saving">
            <i v-if="saving" class="bi bi-arrow-repeat spin"></i>
            {{ saving ? 'Guardando…' : 'Guardar' }}
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
import { useCompanyStore } from "@/stores/companyStore"

const companyStore = useCompanyStore()
const companyId    = computed(() => companyStore.selectedCompany?.id)

const tipos   = ref([])
const loading = ref(true)

const ICONOS_OPCIONES = [
  { value: "bi-car-front",        label: "Carro" },
  { value: "bi-car-front-fill",   label: "Carro lleno" },
  { value: "bi-truck",            label: "Camión" },
  { value: "bi-truck-front",      label: "Camión frente" },
  { value: "bi-bicycle",          label: "Moto/Bici" },
  { value: "bi-bus-front-fill",   label: "Bus/Van" },
  { value: "bi-ev-front",         label: "Eléctrico" },
  { value: "bi-tools",            label: "Otro" },
]

async function load() {
  loading.value = true
  try {
    const { data } = await api.get("/api/talleres/tipos-vehiculo", { params: { company_id: companyId.value } })
    tipos.value = data
  } catch { showToast("Error cargando tipos", "error") }
  finally { loading.value = false }
}

// Modal
const showModal = ref(false)
const editing   = ref(null)
const saving    = ref(false)
const form      = ref({ nombre: "", icono: "bi-car-front", orden: 0 })

function openCreate() {
  editing.value = null
  form.value    = { nombre: "", icono: "bi-car-front", orden: tipos.value.length + 1 }
  showModal.value = true
}
function openEdit(t) {
  editing.value = t
  form.value    = { nombre: t.nombre, icono: t.icono, orden: t.orden }
  showModal.value = true
}

async function submit() {
  if (!form.value.nombre?.trim()) { showToast("El nombre es requerido", "warning"); return }
  saving.value = true
  try {
    if (editing.value) {
      const { data } = await api.put(`/api/talleres/tipos-vehiculo/${editing.value.id}`, {
        company_id: companyId.value,
        ...form.value,
      })
      const idx = tipos.value.findIndex(x => x.id === editing.value.id)
      if (idx !== -1) tipos.value[idx] = data
    } else {
      const { data } = await api.post("/api/talleres/tipos-vehiculo", {
        company_id: companyId.value,
        ...form.value,
      })
      tipos.value.push(data)
    }
    showModal.value = false
    showToast("Tipo guardado", "success")
  } catch (e) { showToast(e?.response?.data?.detail ?? "Error", "error") }
  finally { saving.value = false }
}

async function toggleActivo(t) {
  try {
    const { data } = await api.put(`/api/talleres/tipos-vehiculo/${t.id}`, {
      company_id: companyId.value,
      activo: t.activo ? 0 : 1,
    })
    const idx = tipos.value.findIndex(x => x.id === t.id)
    if (idx !== -1) tipos.value[idx] = data
  } catch { showToast("Error actualizando", "error") }
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 900px; }
.page-header    { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; flex-wrap: wrap; gap: 12px; }
.page-title     { font-size: 20px; font-weight: 700; color: #1e293b; margin: 0 0 4px; display: flex; align-items: center; gap: 8px; }
.page-subtitle  { font-size: 13px; color: #64748b; margin: 0; }

.loading-center { display: flex; align-items: center; gap: 8px; padding: 40px; color: #94a3b8; }

/* Grid */
.tipos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 14px;
}
.tipo-card {
  background: #fff;
  border-radius: 14px;
  border: 2px solid #e2e8f0;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: all .15s;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
}
.tipo-card:hover { border-color: #3b82f6; box-shadow: 0 4px 12px rgba(59,130,246,.12); }
.tipo-card.inactive { opacity: .5; background: #f8fafc; }

.tipo-icon {
  width: 44px; height: 44px; border-radius: 10px;
  background: #eff6ff; color: #1d4ed8;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; flex-shrink: 0;
}
.tipo-info    { flex: 1; display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.tipo-nombre  { font-size: 14px; font-weight: 700; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tipo-badge   { font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 20px; width: fit-content; }
.badge-active   { background: #dcfce7; color: #16a34a; }
.badge-inactive { background: #f1f5f9; color: #94a3b8; }
.tipo-actions { display: flex; gap: 4px; flex-shrink: 0; }

.btn-icon {
  width: 30px; height: 30px; border: 1.5px solid #e2e8f0;
  border-radius: 7px; background: #f8fafc;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; font-size: 13px; color: #475569;
  transition: all .12s;
}
.btn-icon:hover { background: #eff6ff; border-color: #bfdbfe; color: #1d4ed8; }

.empty-state {
  grid-column: 1 / -1;
  display: flex; flex-direction: column; align-items: center;
  gap: 8px; padding: 48px; color: #94a3b8; text-align: center;
}
.empty-state .bi { font-size: 40px; color: #cbd5e1; }
.empty-state p { font-size: 14px; margin: 0; }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 2000; padding: 16px; }
.modal-box     { background: #fff; border-radius: 16px; width: 100%; max-width: 480px; box-shadow: 0 20px 60px rgba(0,0,0,.2); }
.mh  { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid #f1f5f9; }
.mh h3 { font-size: 15px; font-weight: 700; color: #1e293b; margin: 0; display: flex; align-items: center; gap: 7px; }
.btn-x { background: none; border: none; font-size: 16px; cursor: pointer; color: #94a3b8; }
.mb-area { padding: 18px 20px; display: flex; flex-direction: column; gap: 14px; }
.mf { padding: 12px 20px 16px; display: flex; justify-content: flex-end; gap: 8px; border-top: 1px solid #f1f5f9; }
.fg       { display: flex; flex-direction: column; gap: 5px; }
.fg label { font-size: 13px; font-weight: 600; color: #374151; }

/* Icon picker */
.icon-picker {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}
.ic-opt {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  padding: 10px 8px; border: 2px solid #e2e8f0; border-radius: 10px;
  background: #f8fafc; cursor: pointer; font-size: 22px; color: #475569;
  transition: all .12s;
}
.ic-opt span { font-size: 10px; color: #94a3b8; }
.ic-opt:hover   { border-color: #3b82f6; background: #eff6ff; color: #1d4ed8; }
.ic-opt.selected { border-color: #1d4ed8; background: #dbeafe; color: #1d4ed8; }
.icon-preview { display: flex; align-items: center; padding: 8px 0; }

/* Utils */
.btn { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; }
.btn-primary   { background: #3b82f6; color: #fff; } .btn-primary:hover { background: #2563eb; }
.btn-primary:disabled { opacity: .6; cursor: not-allowed; }
.btn-secondary { border: 1.5px solid #e2e8f0; background: #fff; color: #64748b; }
.btn-sm { padding: 6px 12px; font-size: 12px; }
.text-muted  { color: #94a3b8; }
.text-success { color: #16a34a; }
.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

@media (max-width: 768px) {
  .tipos-grid { grid-template-columns: 1fr 1fr; }
  .icon-picker { grid-template-columns: repeat(4, 1fr); }
}
@media (max-width: 480px) {
  .tipos-grid { grid-template-columns: 1fr; }
  .page-container { padding: 16px; }
}
</style>
