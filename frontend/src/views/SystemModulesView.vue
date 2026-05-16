

<template>

  <div class="container mt-4 pb-5">

    <!-- =============================== -->
    <!-- FORM -->
    <!-- =============================== -->

    <form @submit.prevent="createModule">

      <div class="mb-2">
        <input v-model="form.name" class="form-control" placeholder="Nombre" />
      </div>

      <div class="mb-2">
        <input v-model="form.route" class="form-control" placeholder="Ruta (/users)" />
      </div>

      <div class="mb-2">
        <input v-model="form.icon" class="form-control" placeholder="Icono (bi-people)" />
      </div>

      <div class="mb-2">
        <select v-model="form.parent_id" class="form-control">
          <option :value="null">Sin padre</option>
          <option v-for="m in modules" :key="m.id" :value="m.id">
            {{ m.name }}
          </option>
        </select>
      </div>

      <button class="btn btn-primary">Crear módulo</button>

    </form>

    <!-- =============================== -->
    <!-- REPARAR PERFIL -->
    <!-- =============================== -->
    <div class="repair-panel mt-4">
      <div class="repair-header">
        <i class="bi bi-wrench-adjustable"></i>
        <span>Reparar Perfil</span>
        <span class="repair-hint">Limpia módulos inactivos, re-sincroniza jerarquía y añade permisos faltantes</span>
      </div>
      <div class="repair-body">
        <select v-model="repairProfileId" class="form-control repair-select">
          <option value="">— Seleccionar perfil —</option>
          <option v-for="p in profiles" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
        <button
          class="btn btn-repair"
          :disabled="!repairProfileId || repairing"
          @click="repairProfile"
        >
          <i v-if="repairing" class="bi bi-arrow-repeat spin"></i>
          <i v-else class="bi bi-wrench-adjustable-circle-fill"></i>
          {{ repairing ? 'Reparando...' : 'Reparar' }}
        </button>
      </div>
      <div v-if="repairResult" class="repair-result">
        <i class="bi bi-check-circle-fill"></i>
        {{ repairResult }}
      </div>
    </div>

    <!-- =============================== -->
    <!-- TREE -->
    <!-- =============================== -->

    <hr />
    <h5 class="mt-4">
      Estructura de módulos
      <span v-if="repairProfileId" class="profile-filter-badge">
        <i class="bi bi-funnel-fill"></i>
        {{ profiles.find(p => p.id === repairProfileId)?.name }}
        <button class="clear-filter" @click="repairProfileId = ''" title="Ver todos">
          <i class="bi bi-x"></i>
        </button>
      </span>
    </h5>

    <div class="mb-3">

      <select v-model="filterStatus" class="form-control w-25">
        <option value="active">Activos</option>
        <option value="inactive">Inactivos</option>
        <option value="all">Todos</option>
      </select>

    </div>

    <!-- MODO PREVIEW: árbol real del sidebar para el perfil seleccionado -->
    <template v-if="repairProfileId">
      <div v-if="profileLoading" class="text-muted py-3 text-center">
        <i class="bi bi-arrow-repeat spin"></i> Cargando estructura del perfil...
      </div>
      <div v-else-if="profileTree.length === 0" class="text-muted py-3 text-center">
        Sin módulos asignados a este perfil.
      </div>
      <ul v-else class="tree preview-tree">
        <TreeItem
          v-for="node in profileTree"
          :key="node.id"
          :item="node"
          :preview="true"
        />
      </ul>
    </template>

    <!-- MODO GLOBAL: árbol editable (sin drag — el orden se gestiona en Gestión de Menú) -->
    <ul v-else class="tree">
      <TreeItem
        v-for="element in treeModules"
        :key="element.id"
        :item="element"
        :no-drag="true"
        @delete="handleDelete"
        @edit="handleEdit"
        @toggle="handleToggle"
      />
    </ul>

  </div>

  <!-- =============================== -->
  <!-- MODAL CONFIRMAR ELIMINAR -->
  <!-- =============================== -->
  <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
    <div class="modal-content" style="max-width:380px; text-align:center">
      <div style="font-size:2rem; color:#ef4444; margin-bottom:10px">
        <i class="bi bi-trash3-fill"></i>
      </div>
      <h5 class="mb-1">Eliminar módulo</h5>
      <p class="text-muted" style="font-size:.88rem; margin-bottom:20px">
        ¿Eliminar <strong>"{{ deleteTarget.name }}"</strong>? Esta acción no se puede deshacer.
      </p>
      <div class="modal-actions">
        <button class="btn btn-danger" :disabled="deleting" @click="confirmDelete">
          <i v-if="deleting" class="bi bi-hourglass-split me-1"></i>
          {{ deleting ? 'Eliminando...' : 'Sí, eliminar' }}
        </button>
        <button class="btn btn-secondary" @click="deleteTarget = null">Cancelar</button>
      </div>
    </div>
  </div>

  <!-- =============================== -->
  <!-- MODAL EDITAR -->
  <!-- =============================== -->

  <div v-if="showEditModal" class="modal-overlay" @click.self="closeModal">

    <div class="modal-content">

      <h5 class="mb-3">Editar módulo</h5>

      <form @submit.prevent="updateModule">

        <div class="mb-2">
          <input v-model="editForm.name" class="form-control" placeholder="Nombre" />
        </div>

        <div class="mb-2">
          <input v-model="editForm.route" class="form-control" placeholder="Ruta" />
        </div>

        <div class="mb-2">
          <input v-model="editForm.icon" class="form-control" placeholder="Icono" />
        </div>

        <div class="mb-2">
          <select v-model="editForm.parent_id" class="form-control">
            <option :value="null">Sin padre</option>
            <option v-for="m in modules" :key="m.id" :value="m.id">
              {{ m.name }}
            </option>
          </select>
        </div>

        <div class="modal-actions">
          <button type="submit" class="btn btn-primary">Guardar</button>
          <button type="button" class="btn btn-secondary" @click="closeModal">
            Cancelar
          </button>
        </div>

      </form>

    </div>

  </div>

</template>


<script setup>

import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import TreeItem from "@/components/system/TreeItem.vue"
import { ref, onMounted, watch } from "vue"

/* =========================
STATE
========================= */

const form = ref({
  name: "",
  route: "",
  icon: "",
  parent_id: null
})


const modules = ref([])
const treeModules = ref([])
const showEditModal = ref(false)
const editingId = ref(null)
const filterStatus = ref("active")

const editForm = ref({ name: "", route: "", icon: "", parent_id: null })

// ── Reparar perfil ──────────────────────────────────────────────────────────
const profiles        = ref([])
const repairProfileId = ref("")
const repairing       = ref(false)
const repairResult    = ref("")
const profileTree     = ref([])      // árbol del perfil (modo preview)
const profileLoading  = ref(false)

const loadProfiles = async () => {
  try {
    const res = await api.get("/business-profiles/")
    profiles.value = res.data.data ?? res.data
  } catch {}
}

// Cuando cambia el perfil seleccionado: carga árbol real del sidebar
watch(repairProfileId, async (id) => {
  repairResult.value = ""
  if (!id) { profileTree.value = []; return }
  profileLoading.value = true
  try {
    const res = await api.get(`/menu/by-profile/${id}`)
    profileTree.value = res.data
  } catch {
    profileTree.value = []
  } finally {
    profileLoading.value = false
  }
})

const repairProfile = async () => {
  const name = profiles.value.find(p => p.id === repairProfileId.value)?.name || "este perfil"
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Reparar "${name}"?`,
    html: `<div style="text-align:left;font-size:14px;color:#475569">
      <b>1.</b> Elimina módulos inactivos del perfil<br>
      <b>2.</b> Re-sincroniza jerarquía padre-hijo<br>
      <b>3.</b> Añade permisos <code>can_view</code> faltantes a roles
    </div>`,
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, reparar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#1e3a5f"
  })
  if (!isConfirmed) return

  repairing.value = true
  repairResult.value = ""
  try {
    const res = await api.post(`/menu/repair-profile/${repairProfileId.value}`)
    const { deleted_inactive, permissions_added } = res.data
    const parts = []
    if (deleted_inactive > 0) parts.push(`${deleted_inactive} módulo(s) inactivo(s) eliminado(s)`)
    if (permissions_added > 0) parts.push(`${permissions_added} permiso(s) añadido(s)`)
    repairResult.value = parts.length ? parts.join(' · ') : 'Perfil ya estaba sincronizado'
    showToast(repairResult.value, parts.length ? "success" : "info")
  } catch (e) {
    showToast(e.response?.data?.detail || "Error reparando perfil", "error")
  } finally {
    repairing.value = false
  }
}

watch(filterStatus, () => {
  loadModules()
})


/* =========================
LOAD
========================= */

const loadModules = async () => {
  try {
    const res = await api.get("/system-modules/")

    //console.log("MODULOS BACKEND:", res.data)

    modules.value = res.data

    // 🔥 FILTRO CORRECTO
    let data = res.data

    if (filterStatus.value === "active") {
      data = data.filter(m => m.is_active)
    }

    if (filterStatus.value === "inactive") {
      data = data.filter(m => !m.is_active)
    }

    // 🔥 IMPORTANTE: usar data (no res.data)
    treeModules.value = filterTree(data)

    //console.log("TREE FINAL:", treeModules.value)

  } catch (error) {
    console.error(error)
  }
}

const filterTree = (modules) => {
  return modules
    .map(m => ({
      ...m,
      children: m.children ? filterTree(m.children) : []
    }))
    .filter(m => {
      if (filterStatus.value === "all") return true
      if (filterStatus.value === "active") return m.is_active
      if (filterStatus.value === "inactive") return !m.is_active
    })
}

/* =========================
CREATE
========================= */

const createModule = async () => {
  try {

    // 🔥 CLONAR FORM
    const payload = { ...form.value }

    // 🔥 FIX: convertir parent_id a número
    payload.parent_id = payload.parent_id 
      ? Number(payload.parent_id) 
      : null

    // 🔥 SI ES PADRE → SIN ROUTE
    if (!payload.parent_id) {
      payload.route = null
    }

    await api.post("/system-modules/", payload)

    showToast("Módulo creado", "success")

    form.value = {
      name: "",
      route: "",
      icon: "",
      parent_id: null
    }

    await loadModules()

  } catch (error) {
    console.error(error)
    showToast(error.response?.data?.detail || "Error al crear módulo", "error")
  }
}

/* =========================
DELETE
========================= */

const deleteTarget = ref(null)
const deleting     = ref(false)

const deleteModule = (id) => {
  const item = modules.value.find(m => m.id === id)
  deleteTarget.value = item ?? { id, name: `#${id}` }
}

const confirmDelete = async () => {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await api.delete(`/system-modules/${deleteTarget.value.id}`)
    showToast("Módulo eliminado", "success")
    deleteTarget.value = null
    await loadModules()
  } catch (error) {
    console.error(error)
    showToast("Error al eliminar módulo", "error")
  } finally {
    deleting.value = false
  }
}

/* =========================
HELPERS
========================= */

const getParentName = (parent_id) => {
  const parent = modules.value.find(m => m.id === parent_id)
  return parent ? parent.name : "-"
}
/* =========================
INIT
========================= */
/* =========================
BUILD TREE
========================= */
const buildTree = (list) => {

  const map = {}
  const roots = []

  // 🔥 crear mapa
  list.forEach(item => {
    map[item.id] = {
      ...item,
      children: []
    }
  })

  // 🔥 construir árbol
  list.forEach(item => {

    const parentId = item.parent_id

    if (parentId && map[parentId]) {
      map[parentId].children.push(map[item.id])
    } else {
      roots.push(map[item.id])
    }

  })

  return roots
}

const handleEdit = (item) => {
  editForm.value = {
    name: item.name,
    route: item.route,
    icon: item.icon,
    parent_id: item.parent_id
  }
  editingId.value = item.id
  showEditModal.value = true
}

const updateModule = async () => {
  try {
    const payload = { ...editForm.value }
    payload.parent_id = payload.parent_id ? Number(payload.parent_id) : null
    await api.put(`/system-modules/${editingId.value}`, payload)
    showToast("Módulo actualizado", "success")
    closeModal()
    await loadModules()
  } catch (error) {
    console.error(error)
    showToast(error.response?.data?.detail || "Error al actualizar módulo", "error")
  }
}

const closeModal = () => {
  showEditModal.value = false
  editingId.value = null
  editForm.value = { name: "", route: "", icon: "", parent_id: null }
}

const handleDelete = (item) => {
  if (item.children && item.children.length) {
    showToast("No puedes eliminar un módulo con hijos", "error")
    return
  }
  deleteTarget.value = item
}

const handleToggle = async (item) => {
  try {

    await api.put(`/system-modules/${item.id}`, {
      is_active: !item.is_active
    })

    showToast("Estado actualizado", "success")

    await loadModules()

  } catch (error) {
    console.error(error)
    showToast("Error al cambiar estado", "error")
  }
}


onMounted(() => { loadModules(); loadProfiles() })

</script>

<style scoped>

/* ── Árbol preview (sin botones de edición) ── */
.preview-tree {
  padding: 0;
  margin: 0;
  list-style: none;
}

/* ── Badge de perfil activo en el árbol ── */
.profile-filter-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 600;
  background: #1e3a5f;
  color: #93c5fd;
  padding: 2px 10px 2px 8px;
  border-radius: 20px;
  margin-left: 10px;
  vertical-align: middle;
}
.clear-filter {
  background: none;
  border: none;
  color: #93c5fd;
  cursor: pointer;
  padding: 0;
  font-size: 13px;
  line-height: 1;
  opacity: 0.7;
}
.clear-filter:hover { opacity: 1; }

/* ── Panel de reparación ── */
.repair-panel {
  background: #1e293b;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #334155;
}
.repair-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #0f172a;
  color: #e2e8f0;
  font-weight: 700;
  font-size: 14px;
}
.repair-hint {
  font-size: 11px;
  font-weight: 400;
  opacity: 0.55;
  margin-left: 4px;
}
.repair-body {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 14px 16px;
  flex-wrap: wrap;
}
.repair-select {
  flex: 1;
  min-width: 200px;
  background: #1e293b;
  color: #e2e8f0;
  border-color: #334155;
}
.btn-repair {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  background: #1e3a5f;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s;
}
.btn-repair:hover:not(:disabled) { background: #16a34a; }
.btn-repair:disabled { opacity: 0.5; cursor: not-allowed; }

.repair-result {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 8px 16px 12px;
  color: #4ade80;
  font-size: 13px;
}
.repair-result .bi { font-size: 15px; }

.spin { display: inline-block; animation: spin 0.8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);

  display: flex;
  align-items: center;
  justify-content: center;

  z-index: 2000;
}

.modal-content {
  background: #1e293b;
  padding: 20px;
  border-radius: 10px;
  width: 400px;
  color: #e2e8f0;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 10px;
}

</style>
