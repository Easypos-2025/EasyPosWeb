<template>
  <!-- BOTÓN DISPARADOR -->
  <button type="button" class="btn-workers-modal" @click="open" :title="btnTitle">
    <i class="bi bi-person-plus"></i> {{ btnLabel }}
  </button>

  <!-- OVERLAY MODAL -->
  <teleport to="body">
    <div v-if="show" class="wm-overlay" @click.self="close">
      <div class="wm-box">

        <!-- CABECERA -->
        <div class="wm-header">
          <h2><i class="bi bi-people-fill"></i> Gestión de Ejecutores</h2>
          <button class="wm-close" @click="close"><i class="bi bi-x-lg"></i></button>
        </div>

        <div class="wm-body">

          <!-- ═══════ PROFESIONES ═══════ -->
          <div class="section-title">
            <i class="bi bi-briefcase"></i> Profesiones / Oficios
          </div>

          <div class="prof-form">
            <div class="row g-2">
              <div class="col-5">
                <input v-model="profForm.name" class="form-control form-control-sm"
                  placeholder="Nombre *" @keyup.enter="saveProf" />
              </div>
              <div class="col-5">
                <input v-model="profForm.description" class="form-control form-control-sm"
                  placeholder="Descripción (opcional)" />
              </div>
              <div class="col-2">
                <button class="btn btn-primary btn-sm w-100" @click="saveProf"
                  :disabled="savingProf">
                  <i v-if="savingProf" class="bi bi-arrow-repeat spin"></i>
                  <i v-else class="bi bi-plus-lg"></i>
                </button>
              </div>
            </div>
          </div>

          <div class="prof-list">
            <div v-if="professions.length === 0" class="empty-hint">
              Sin profesiones — agrega una arriba
            </div>
            <div v-for="p in professions" :key="p.id" class="prof-item">
              <span class="prof-name">{{ p.name }}
                <span v-if="p.description" class="prof-desc">· {{ p.description }}</span>
              </span>
              <button class="btn-del" @click="deleteProf(p)" title="Eliminar">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </div>

          <hr class="wm-divider" />

          <!-- ═══════ EJECUTORES ═══════ -->
          <div class="section-title d-flex justify-content-between align-items-center">
            <span><i class="bi bi-person-gear"></i> Ejecutores</span>
            <button class="btn btn-primary btn-sm" @click="openCreate">
              <i class="bi bi-person-plus-fill"></i> Nuevo
            </button>
          </div>

          <!-- Formulario crear/editar -->
          <div v-if="showWorkerForm" class="worker-form">
            <div class="row g-2 align-items-end">
              <div class="col-md-4 col-12">
                <label class="form-label-sm">Nombre *</label>
                <input v-model="workerForm.name" class="form-control form-control-sm"
                  placeholder="Nombre completo" data-v="wname" @input="clearErr" />
              </div>
              <div class="col-md-4 col-12">
                <label class="form-label-sm">Profesión</label>
                <select v-model="workerForm.profession_id" class="form-select form-select-sm">
                  <option :value="null">— Sin profesión —</option>
                  <option v-for="p in professions" :key="p.id" :value="p.id">{{ p.name }}</option>
                </select>
              </div>
              <div class="col-md-3 col-12">
                <label class="form-label-sm">Teléfono</label>
                <input v-model="workerForm.phone" class="form-control form-control-sm"
                  placeholder="Opcional" />
              </div>
              <div class="col-md-1 col-12 d-flex gap-1">
                <button class="btn btn-success btn-sm flex-fill" @click="saveWorker"
                  :disabled="savingWorker" title="Guardar">
                  <i v-if="savingWorker" class="bi bi-arrow-repeat spin"></i>
                  <i v-else class="bi bi-check-lg"></i>
                </button>
                <button class="btn btn-secondary btn-sm" @click="cancelWorkerForm"
                  title="Cancelar">
                  <i class="bi bi-x-lg"></i>
                </button>
              </div>
            </div>
          </div>

          <!-- Lista de ejecutores -->
          <div class="worker-list">
            <div v-if="loading" class="empty-hint">
              <i class="bi bi-arrow-repeat spin"></i> Cargando...
            </div>
            <div v-else-if="workers.length === 0" class="empty-hint">
              Sin ejecutores registrados
            </div>
            <div v-for="w in workers" :key="w.id" class="worker-item">
              <div class="worker-info">
                <strong>{{ w.name }}</strong>
                <span v-if="w.profession_name" class="prof-badge">{{ w.profession_name }}</span>
                <span v-if="w.phone" class="phone-text">{{ w.phone }}</span>
              </div>
              <div class="worker-actions">
                <button class="btn btn-warning btn-sm py-0 px-2" @click="openEdit(w)"
                  title="Editar">
                  <i class="bi bi-pencil" style="font-size:11px"></i>
                </button>
                <button class="btn btn-danger btn-sm py-0 px-2" @click="deleteWorker(w)"
                  title="Eliminar">
                  <i class="bi bi-trash" style="font-size:11px"></i>
                </button>
              </div>
            </div>
          </div>

        </div>

        <!-- PIE -->
        <div class="wm-footer">
          <span class="footer-hint">Los cambios se aplican al cerrar el modal</span>
          <button class="btn btn-primary" @click="close">
            <i class="bi bi-check2-circle"></i> Listo
          </button>
        </div>

      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

const props = defineProps({
  btnLabel: { type: String, default: "Gestionar" },
  btnTitle: { type: String, default: "Gestionar ejecutores y profesiones" },
})

const emit = defineEmits(["updated"])

const show       = ref(false)
const loading    = ref(false)
const savingProf   = ref(false)
const savingWorker = ref(false)
const showWorkerForm = ref(false)

const workers    = ref([])
const professions = ref([])

const profForm   = ref({ name: "", description: "" })
const workerForm = ref({ id: null, name: "", profession_id: null, phone: "" })

// ── Abrir / Cerrar ───────────────────────────────────────────
async function open() {
  show.value = true
  await load()
}

function close() {
  show.value = false
  showWorkerForm.value = false
  emit("updated")
}

// ── Carga ────────────────────────────────────────────────────
async function load() {
  loading.value = true
  try {
    const [wRes, pRes] = await Promise.all([
      api.get("/workers/"),
      api.get("/professions/"),
    ])
    workers.value    = wRes.data
    professions.value = pRes.data
  } catch {
    showToast("Error cargando datos", "error")
  } finally {
    loading.value = false
  }
}

// ── CRUD Profesiones ─────────────────────────────────────────
async function saveProf() {
  if (!profForm.value.name.trim()) {
    showToast("El nombre es obligatorio", "warning"); return
  }
  savingProf.value = true
  try {
    await api.post("/professions/", profForm.value)
    showToast("Profesión creada", "success")
    profForm.value = { name: "", description: "" }
    const res = await api.get("/professions/")
    professions.value = res.data
  } catch (e) {
    showToast(e.response?.data?.detail || "Error creando profesión", "error")
  } finally {
    savingProf.value = false
  }
}

async function deleteProf(p) {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar "${p.name}"?`, icon: "warning",
    showCancelButton: true, confirmButtonText: "Eliminar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/professions/${p.id}`)
    showToast("Profesión eliminada", "success")
    const res = await api.get("/professions/")
    professions.value = res.data
  } catch (e) {
    showToast(e.response?.data?.detail || "Error eliminando", "error")
  }
}

// ── CRUD Ejecutores ───────────────────────────────────────────
function openCreate() {
  workerForm.value = { id: null, name: "", profession_id: null, phone: "" }
  showWorkerForm.value = true
}

function openEdit(w) {
  workerForm.value = { id: w.id, name: w.name, profession_id: w.profession_id, phone: w.phone || "" }
  showWorkerForm.value = true
}

function cancelWorkerForm() {
  showWorkerForm.value = false
  document.querySelectorAll(".field-invalid").forEach(el => el.classList.remove("field-invalid"))
}

function clearErr(e) { e.target.classList.remove("field-invalid") }

async function saveWorker() {
  if (!workerForm.value.name.trim()) {
    showToast("El nombre es obligatorio", "warning")
    document.querySelector('[data-v="wname"]')?.classList.add("field-invalid")
    return
  }
  savingWorker.value = true
  try {
    if (workerForm.value.id) {
      await api.put(`/workers/${workerForm.value.id}`, workerForm.value)
      showToast("Ejecutor actualizado", "success")
    } else {
      await api.post("/workers/", workerForm.value)
      showToast("Ejecutor creado", "success")
    }
    showWorkerForm.value = false
    const res = await api.get("/workers/")
    workers.value = res.data
  } catch (e) {
    showToast(e.response?.data?.detail || "Error guardando ejecutor", "error")
  } finally {
    savingWorker.value = false
  }
}

async function deleteWorker(w) {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar "${w.name}"?`,
    text: "Esta acción no se puede deshacer.",
    icon: "warning",
    showCancelButton: true, confirmButtonText: "Sí, eliminar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/workers/${w.id}`)
    showToast("Ejecutor eliminado", "success")
    const res = await api.get("/workers/")
    workers.value = res.data
  } catch (e) {
    showToast(e.response?.data?.detail || "Error eliminando", "error")
  }
}
</script>

<style scoped>
/* BOTÓN DISPARADOR */
.btn-workers-modal {
  background: none; border: 1px solid #cbd5e1; border-radius: 6px;
  font-size: 12px; padding: 3px 10px; color: #64748b; cursor: pointer;
  display: inline-flex; align-items: center; gap: 4px; white-space: nowrap;
  transition: all 0.15s;
}
.btn-workers-modal:hover { background: #f1f5f9; color: #1e293b; border-color: #94a3b8; }

/* OVERLAY */
.wm-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center;
  z-index: 1100; padding: 16px;
}

/* CAJA */
.wm-box {
  background: #fff; border-radius: 18px; width: 700px; max-width: 96vw;
  max-height: 88vh; display: flex; flex-direction: column;
  box-shadow: 0 24px 64px rgba(0,0,0,0.22);
}

/* HEADER */
.wm-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 24px 14px; border-bottom: 1px solid #f1f5f9; flex-shrink: 0;
}
.wm-header h2 { font-size: 17px; font-weight: 700; color: #1e293b; margin: 0;
  display: flex; align-items: center; gap: 8px; }
.wm-close { background: none; border: none; font-size: 18px; cursor: pointer;
  color: #94a3b8; border-radius: 6px; padding: 4px 8px; }
.wm-close:hover { background: #f1f5f9; color: #1e293b; }

/* BODY */
.wm-body { padding: 18px 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }

/* FOOTER */
.wm-footer { padding: 14px 24px 18px; display: flex; justify-content: space-between;
  align-items: center; border-top: 1px solid #f1f5f9; flex-shrink: 0; }
.footer-hint { font-size: 12px; color: #94a3b8; }

/* SECTIONS */
.section-title { font-size: 13px; font-weight: 700; color: #475569;
  display: flex; align-items: center; gap: 6px; }
.wm-divider { border: none; border-top: 1px solid #f1f5f9; margin: 4px 0; }

/* PROFESIONES */
.prof-form { background: #f8fafc; border-radius: 10px; padding: 12px;
  border: 1px solid #e2e8f0; }
.prof-list { display: flex; flex-direction: column; gap: 5px;
  max-height: 120px; overflow-y: auto; }
.prof-item { display: flex; justify-content: space-between; align-items: center;
  padding: 6px 10px; background: #fff; border: 1px solid #f1f5f9; border-radius: 8px; }
.prof-item:hover { background: #f8fafc; }
.prof-name { font-size: 13px; font-weight: 600; }
.prof-desc { font-size: 12px; color: #94a3b8; font-weight: 400; }
.btn-del { background: none; border: 1px solid #fca5a5; color: #ef4444;
  border-radius: 6px; padding: 2px 8px; cursor: pointer; font-size: 12px; }
.btn-del:hover { background: #fef2f2; }

/* EJECUTORES */
.worker-form {
  background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px; padding: 12px;
}
.worker-list { display: flex; flex-direction: column; gap: 5px;
  max-height: 200px; overflow-y: auto; }
.worker-item { display: flex; justify-content: space-between; align-items: center;
  padding: 8px 12px; background: #fff; border: 1px solid #f1f5f9; border-radius: 8px; }
.worker-item:hover { background: #f8fafc; }
.worker-info { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.worker-info strong { font-size: 13px; color: #1e293b; }
.worker-actions { display: flex; gap: 4px; flex-shrink: 0; }
.prof-badge { background: #eff6ff; color: #1e40af; font-size: 11px;
  font-weight: 600; padding: 2px 8px; border-radius: 20px; }
.phone-text { font-size: 12px; color: #94a3b8; }
.form-label-sm { font-size: 12px; font-weight: 600; color: #374151;
  display: block; margin-bottom: 3px; }
.empty-hint { font-size: 13px; color: #94a3b8; text-align: center; padding: 10px; }

.spin { display: inline-block; animation: spin 0.8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
</style>
