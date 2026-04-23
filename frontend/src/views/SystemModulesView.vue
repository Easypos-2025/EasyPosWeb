

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
    <!-- TREE -->
    <!-- =============================== -->

    <hr />
    <h5 class="mt-4">Estructura de módulos</h5>

    <div class="mb-3">

      <select v-model="filterStatus" class="form-control w-25">
        <option value="active">Activos</option>
        <option value="inactive">Inactivos</option>
        <option value="all">Todos</option>
      </select>

    </div>

    <draggable
      v-model="treeModules"
      item-key="id"
      class="tree"
      :group="{ name: 'modules' }"
      @end="handleDragEnd"
    >
      <template #item="{ element }">
        <div class="tree-wrapper">
          <TreeItem 
            :item="element" 
            @drag-end="handleDragEnd"
            @delete="handleDelete"
            @edit="handleEdit"
            @toggle="handleToggle"
          />
        </div>
      </template>
    </draggable>

  </div>

  <!-- =============================== -->
  <!-- MODAL EDITAR -->
  <!-- =============================== -->

  <div v-if="showEditModal" class="modal-overlay" @click.self="closeModal">

    <div class="modal-content">

      <h5 class="mb-3">Editar módulo</h5>

      <form @submit.prevent="updateModule">

        <div class="mb-2">
          <input v-model="form.name" class="form-control" placeholder="Nombre" />
        </div>

        <div class="mb-2">
          <input v-model="form.route" class="form-control" placeholder="Ruta" />
        </div>

        <div class="mb-2">
          <input v-model="form.icon" class="form-control" placeholder="Icono" />
        </div>

        <div class="mb-2">
          <select v-model="form.parent_id" class="form-control">
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
import draggable from "vuedraggable"
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
    showToast("Error al crear módulo", "error")
  }
}

/* =========================
DELETE
========================= */

const deleteModule = async (id) => {
  try {

    const confirmDelete = confirm("¿Eliminar este módulo?")
    if (!confirmDelete) return

    await api.delete(`/system-modules/${id}`)

    showToast("Módulo eliminado", "success")

    await loadModules()

  } catch (error) {
    console.error(error)
    showToast("Error al eliminar módulo", "error")
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

const flattenTree = (nodes, parentId = null) => {
  let result = []

  nodes.forEach((node, index) => {

    result.push({
      id: node.id,
      parent_id: parentId,
      order_index: index   // 🔥 NUEVO CAMPO
    })

    if (node.children && node.children.length) {
      result = result.concat(flattenTree(node.children, node.id))
    }

  })

  return result
}

const handleEdit = (item) => {

  form.value = {
    name: item.name,
    route: item.route,
    icon: item.icon,
    parent_id: item.parent_id
  }

  editingId.value = item.id
  showEditModal.value = true
}

const handleDragEnd = async () => {
  //console.log("🔥 DRAG END EJECUTADO")
  try {

    const flat = flattenTree(treeModules.value)

    //console.log("GUARDANDO FINAL:", flat)

    for (const item of flat) {
      await api.put(`/system-modules/${item.id}`, {
        parent_id: item.parent_id,
        order_index: item.order_index
      })
    }

    showToast("Orden actualizado", "success")

  } catch (error) {
    console.error(error)
    showToast("Error al guardar cambios", "error")
  }
}

const updateModule = async () => {
  try {

    const payload = { ...form.value }

    payload.parent_id = payload.parent_id 
      ? Number(payload.parent_id) 
      : null

    await api.put(`/system-modules/${editingId.value}`, payload)

    showToast("Módulo actualizado", "success")

    closeModal()
    await loadModules()

  } catch (error) {
    console.error(error)
    showToast("Error al actualizar módulo", "error")
  }
}

const closeModal = () => {
  showEditModal.value = false
  editingId.value = null
}

const handleDelete = async (item) => {
  try {

    // 🔥 VALIDAR HIJOS
    if (item.children && item.children.length) {
      showToast("No puedes eliminar un módulo con hijos", "error")
      return
    }

    // 🔥 CONFIRMAR
    const ok = confirm(`Eliminar módulo "${item.name}"?`)
    if (!ok) return

    await api.delete(`/system-modules/${item.id}`)

    showToast("Módulo eliminado", "success")

    await loadModules()

  } catch (error) {
    console.error(error)
    showToast("Error al eliminar módulo", "error")
  }
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


onMounted(loadModules)

</script>

<style scoped>

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
