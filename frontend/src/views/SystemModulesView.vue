

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
          <option v-for="m in $ordenAlfa(modules, 'name')" :key="m.id" :value="m.id">
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
          <option v-for="p in $ordenAlfa(profiles, 'name')" :key="p.id" :value="p.id">{{ p.name }}</option>
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
          :no-drag="true"
          @delete="handleDelete"
          @edit="handleEdit"
          @toggle="handleToggle"
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
  <div v-if="deleteTarget" class="modal-overlay" @click.self="closeDelete">
    <div class="modal-content del-modal" :class="{ 'del-modal--wide': preview?.children?.length }">
      <div class="del-head">
        <i class="bi bi-trash3-fill del-icon"></i>
        <div class="del-head-txt">
          <h5 class="mb-0">Eliminar "{{ deleteTarget.name }}"</h5>
          <small v-if="preview" class="del-usage">
            <template v-if="preview.profiles.length">
              Perfiles: {{ preview.profiles.map(p => p.name).join(', ') }}
            </template>
            <template v-else>Sin perfiles</template>
            · {{ preview.roles }} rol(es)
          </small>
        </div>
        <button class="del-close" @click="closeDelete" title="Cerrar"><i class="bi bi-x-lg"></i></button>
      </div>

      <div v-if="previewLoading" class="text-muted py-3 text-center">
        <i class="bi bi-arrow-repeat spin"></i> Revisando dependencias...
      </div>

      <template v-else-if="preview">
        <!-- Sin hijos: confirmación simple -->
        <p v-if="!preview.children.length" class="del-msg">
          ¿Eliminar este módulo? Se quitará de los perfiles y roles que lo tienen. Esta acción no se puede deshacer.
        </p>

        <!-- Con hijos: gestionar cada hijo -->
        <template v-else>
          <p class="del-msg">
            Tiene <strong>{{ preview.children.length }}</strong> módulo(s) hijo(s). Elimínelos, muévalos a otro padre
            o déjelos como padre para poder eliminar este módulo.
          </p>

          <label class="del-all">
            <input type="checkbox" :checked="allSelected" @change="toggleAll($event.target.checked)" />
            Seleccionar todos
          </label>

          <ul class="del-list">
            <li v-for="c in preview.children" :key="c.id" class="del-item">
              <div class="del-row">
                <input type="checkbox" class="del-chk" :value="c.id" v-model="selectedIds"
                       :disabled="c.grandchildren > 0 || busy" />
                <div class="del-info">
                  <div class="del-name">
                    {{ c.name }}
                    <span v-if="!c.is_active" class="del-tag del-tag--off">Inactivo</span>
                    <span v-if="c.grandchildren" class="del-tag del-tag--warn" title="Tiene sus propios hijos">
                      <i class="bi bi-diagram-3"></i> {{ c.grandchildren }} hijo(s)
                    </span>
                  </div>
                  <div class="del-route">{{ c.route || 'Sin ruta' }}</div>
                  <div class="del-meta">
                    {{ c.profiles.length ? c.profiles.map(p => p.name).join(', ') : 'Sin perfiles' }}
                    · {{ c.roles }} rol(es)
                  </div>
                </div>
                <div class="del-acts">
                  <button class="btn btn-sm btn-outline-info" :disabled="busy"
                          @click="toggleMove(c.id)">
                    <i class="bi bi-arrow-left-right"></i> Mover
                  </button>
                  <button class="btn btn-sm btn-outline-light" :disabled="busy"
                          @click="moveChild(c, null)">
                    <i class="bi bi-arrow-bar-up"></i> Dejar como padre
                  </button>
                </div>
              </div>

              <!-- Panel mover -->
              <div v-if="moveOpenId === c.id" class="del-move">
                <input v-model="moveSearch" class="form-control form-control-sm" placeholder="Buscar nuevo padre..." />
                <select v-model="moveParentId" class="form-control form-control-sm" size="5">
                  <option v-for="m in $ordenAlfa(parentOptions(c.id), 'label')" :key="m.id" :value="m.id">
                    {{ m.label }}
                  </option>
                </select>
                <label class="del-add">
                  <input type="checkbox" v-model="moveAddParent" />
                  Agregar el nuevo padre a los perfiles donde no esté
                </label>
                <div class="del-move-acts">
                  <button class="btn btn-sm btn-primary" :disabled="!moveParentId || busy"
                          @click="moveChild(c, moveParentId)">
                    Mover aquí
                  </button>
                  <button class="btn btn-sm btn-secondary" @click="moveOpenId = null">Cancelar</button>
                </div>
              </div>
            </li>
          </ul>

          <button class="btn btn-sm btn-danger del-batch" :disabled="!selectedIds.length || busy"
                  @click="deleteSelected">
            <i class="bi bi-trash3"></i> Eliminar seleccionados ({{ selectedIds.length }})
          </button>
        </template>

        <div class="modal-actions">
          <button class="btn btn-danger" :disabled="deleting || busy || preview.children.length > 0"
                  :title="preview.children.length ? 'Primero resuelva los módulos hijos' : ''"
                  @click="confirmDelete">
            <i v-if="deleting" class="bi bi-hourglass-split me-1"></i>
            {{ deleting ? 'Eliminando...' : 'Eliminar padre' }}
          </button>
          <button class="btn btn-secondary" @click="closeDelete">Cancelar</button>
        </div>
      </template>
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
            <option v-for="m in $ordenAlfa(modules, 'name')" :key="m.id" :value="m.id">
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
import { ref, computed, onMounted, watch } from "vue"

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

const deleteTarget   = ref(null)   // { id: system_modules.id, name }
const deleting       = ref(false)
const preview        = ref(null)   // dependencias del módulo a eliminar
const previewLoading = ref(false)
const selectedIds    = ref([])
const busy           = ref(false)
const moveOpenId     = ref(null)
const moveSearch     = ref("")
const moveParentId   = ref(null)
const moveAddParent  = ref(false)

const errMsg = (e, fallback) => e?.response?.data?.detail || fallback

const loadPreview = async () => {
  previewLoading.value = !preview.value
  try {
    const { data } = await api.get(`/system-modules/${deleteTarget.value.id}/delete-preview`)
    preview.value = data
    const valid = new Set(data.children.filter(c => !c.grandchildren).map(c => c.id))
    selectedIds.value = selectedIds.value.filter(id => valid.has(id))
  } catch (e) {
    showToast(errMsg(e, "Error revisando el módulo"), "error")
    closeDelete()
  } finally {
    previewLoading.value = false
  }
}

const openDelete = (smId, name) => {
  deleteTarget.value = { id: smId, name }
  preview.value = null
  selectedIds.value = []
  moveOpenId.value = null
  loadPreview()
}

const closeDelete = () => {
  if (busy.value || deleting.value) return
  deleteTarget.value = null
  preview.value = null
  moveOpenId.value = null
}

const allSelected = computed(() => {
  const sel = (preview.value?.children || []).filter(c => !c.grandchildren)
  return sel.length > 0 && sel.every(c => selectedIds.value.includes(c.id))
})

const toggleAll = (checked) => {
  selectedIds.value = checked
    ? preview.value.children.filter(c => !c.grandchildren).map(c => c.id)
    : []
}

// Lista plana de módulos para elegir nuevo padre
const flatModules = computed(() => {
  const out = []
  const walk = (nodes, depth) => {
    for (const n of nodes || []) {
      out.push({ id: n.id, name: n.name, label: `${"— ".repeat(depth)}${n.name}` })
      walk(n.children, depth + 1)
    }
  }
  walk(modules.value, 0)
  return out
})

const parentOptions = (childId) => {
  const q = moveSearch.value.trim().toLowerCase()
  const exclude = new Set([childId, deleteTarget.value?.id])
  return flatModules.value.filter(m =>
    !exclude.has(m.id) && (!q || m.name.toLowerCase().includes(q)))
}

const toggleMove = (childId) => {
  moveOpenId.value = moveOpenId.value === childId ? null : childId
  moveSearch.value = ""
  moveParentId.value = null
  moveAddParent.value = false
}

const moveChild = async (child, newParentId) => {
  busy.value = true
  try {
    const { data } = await api.post(`/system-modules/${child.id}/move`, {
      new_parent_id: newParentId,
      add_parent_to_profiles: newParentId ? moveAddParent.value : false,
    })
    let msg = newParentId ? `"${child.name}" movido` : `"${child.name}" quedó como padre`
    if (data.added_parent_profiles?.length)
      msg += `. Padre agregado a: ${data.added_parent_profiles.join(", ")}`
    if (data.root_profiles?.length)
      msg += `. Quedó sin padre en: ${data.root_profiles.join(", ")} (el nuevo padre no está en ese perfil)`
    const warn = data.root_profiles?.length > 0
    showToast(msg, warn ? "warning" : "success", warn || data.added_parent_profiles?.length ? 6000 : 1500)
    moveOpenId.value = null
    await Promise.all([loadPreview(), loadModules()])
  } catch (e) {
    showToast(errMsg(e, "Error al mover el módulo"), "error")
  } finally {
    busy.value = false
  }
}

const deleteSelected = async () => {
  const names = preview.value.children.filter(c => selectedIds.value.includes(c.id)).map(c => c.name)
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar ${names.length} módulo(s)?`,
    html: `<div style="text-align:left;font-size:14px;color:#475569">${names.map(escapeHtml).join("<br>")}</div>
           <div style="margin-top:8px;font-size:13px">Se quitarán de perfiles y roles. No se puede deshacer.</div>`,
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, eliminar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#dc2626",
  })
  if (!isConfirmed) return
  busy.value = true
  try {
    const { data } = await api.post("/system-modules/delete-batch", { ids: selectedIds.value })
    showToast(`${data.deleted} módulo(s) eliminado(s)`, "success")
    selectedIds.value = []
    await Promise.all([loadPreview(), loadModules()])
  } catch (e) {
    showToast(errMsg(e, "Error al eliminar módulos"), "error")
  } finally {
    busy.value = false
  }
}

const escapeHtml = (s) => String(s ?? "").replace(/[&<>"']/g, ch =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]))

const confirmDelete = async () => {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await api.delete(`/system-modules/${deleteTarget.value.id}`)
    showToast("Módulo eliminado", "success")
    deleting.value = false
    closeDelete()
    await loadModules()
  } catch (error) {
    showToast(errMsg(error, "Error al eliminar módulo"), "error")
    await loadPreview()
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

function findSmIdByRoute(route, nodes) {
  for (const n of nodes) {
    if (n.route === route) return n.id
    const found = findSmIdByRoute(route, n.children || [])
    if (found) return found
  }
  return null
}

const handleEdit = async (item) => {
  // Prioridad: module_id explícito → buscar por ruta en modules → item.id
  let smId = item.module_id
  if (!smId && item.route) smId = findSmIdByRoute(item.route, modules.value)
  if (!smId) smId = item.id

  editingId.value = smId
  try {
    const { data } = await api.get(`/system-modules/${smId}`)
    editForm.value = { name: data.name, route: data.route, icon: data.icon, parent_id: data.parent_id }
  } catch {
    editForm.value = { name: item.name, route: item.route, icon: item.icon, parent_id: null }
  }
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

// En la vista por perfil los nodos traen id = business_profile_modules.id y module_id = system_modules.id
const smIdOf = (item) => item.module_id ?? item.id

const handleDelete = (item) => {
  openDelete(smIdOf(item), item.name)
}

const handleToggle = async (item) => {
  try {

    await api.put(`/system-modules/${smIdOf(item)}`, {
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

/* ── Modal eliminar con dependencias ── */
.del-modal { width: 420px; max-width: calc(100vw - 32px); max-height: 90vh; overflow-y: auto; }
.del-modal--wide { width: 680px; }
.del-head { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 10px; }
.del-icon { font-size: 1.6rem; color: #ef4444; line-height: 1; }
.del-head-txt { flex: 1; min-width: 0; }
.del-head-txt h5 { word-break: break-word; }
.del-usage { color: #94a3b8; font-size: 12px; }
.del-close { background: none; border: none; color: #94a3b8; font-size: 16px; cursor: pointer; padding: 2px; }
.del-close:hover { color: #e2e8f0; }
.del-msg { font-size: 13px; color: #cbd5e1; margin: 6px 0 12px; }
.del-all { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #cbd5e1; margin-bottom: 6px; cursor: pointer; }
.del-list { list-style: none; padding: 0; margin: 0 0 12px; display: flex; flex-direction: column; gap: 8px; }
.del-item { background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 10px; }
.del-row { display: flex; align-items: flex-start; gap: 10px; }
.del-chk { margin-top: 4px; flex-shrink: 0; }
.del-info { flex: 1; min-width: 0; }
.del-name { font-weight: 600; font-size: 14px; display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
.del-route { font-family: monospace; font-size: 12px; color: #93c5fd; word-break: break-all; }
.del-meta { font-size: 12px; color: #94a3b8; }
.del-tag { font-size: 10px; font-weight: 600; padding: 1px 7px; border-radius: 10px; }
.del-tag--off { background: #334155; color: #cbd5e1; }
.del-tag--warn { background: #78350f; color: #fde68a; }
.del-acts { display: flex; flex-direction: column; gap: 6px; flex-shrink: 0; }
.del-acts .btn { white-space: nowrap; font-size: 12px; }
.del-move { margin-top: 10px; display: flex; flex-direction: column; gap: 6px; border-top: 1px dashed #334155; padding-top: 10px; }
.del-move .form-control { background: #1e293b; color: #e2e8f0; border-color: #334155; }
.del-add { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #cbd5e1; cursor: pointer; }
.del-move-acts { display: flex; gap: 6px; justify-content: flex-end; }
.del-batch { margin-bottom: 4px; }

@media (max-width: 768px) {
  .del-modal--wide { width: 100%; }
  .del-row { flex-wrap: wrap; }
  .del-acts { flex-direction: row; width: 100%; padding-left: 24px; }
  .del-acts .btn { flex: 1; }
}

@media (max-width: 576px) {
  .del-modal { padding: 14px; max-height: 94vh; }
  .del-acts { padding-left: 0; flex-direction: column; }
  .del-move-acts .btn, .del-batch, .modal-actions .btn { flex: 1; }
  .del-batch { width: 100%; }
  .modal-actions { flex-direction: column-reverse; }
}

</style>
