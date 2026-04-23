
<template>
  <div class="sysadmin-container">

    <!-- ASIGNAR PERFIL -->
    <div class="card p-3 mt-3">
      <h5>Seleccione Business Profile</h5>

      <select v-model="selectedProfileId" class="form-select mt-2">
        <option value="">-- Seleccione un perfil --</option>
        <option
          v-for="profile in businessProfiles"
          :key="profile.id"
          :value="profile.id"
        >
          {{ profile.name }}
        </option>
      </select>

    </div>

    <!-- GESTIÓN DE MENÚ -->
    <div class="card p-3 mt-3">
      <h5>Gestión de Menú</h5>

      <div v-if="modules.length === 0">
        <small>No hay módulos cargados...</small>
      </div>

      <!-- 🔥 PADRES -->
      <draggable
        v-model="modules"
        item-key="id"
        :group="{ name: 'modules' }"
        @change="updateOrder"
      >
        <template #item="{ element }">

          <div class="border p-2 mt-2">

            <!-- PADRE -->
            <div class="fw-bold">
              {{ element.name }}
            </div>

            <!-- 🔥 HIJOS -->
            <draggable
              v-if="element.children && element.children.length > 0"
              v-model="element.children"
              item-key="id"
              :group="{ name: 'modules' }"
              class="ms-4 mt-2"
              @change="updateOrder"
            >
              <template #item="{ element: child }">
                <div class="border p-2 mt-1">
                  ↳ {{ child.name }}
                </div>
              </template>
            </draggable>

          </div>

        </template>
      </draggable>

    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, watch } from "vue";
import api from "@/services/apis";
import { showToast } from "@/utils/toast";
import { useMenuStore } from "@/stores/menuStore";
import draggable from "vuedraggable";
import { computed } from "vue"

const menuStore = useMenuStore();
const modules = ref([]);

/* =========================================
FLATTEN TREE (PARA GUARDAR)
========================================= */
function flattenTree(nodes, parentId = null) {
  let result = []

  nodes.forEach((node, index) => {
    result.push({
      id: node.id,
      parent_id: parentId,
      sort_order: index
    })

    if (node.children && node.children.length) {
      result = result.concat(flattenTree(node.children, node.id))
    }
  })

  return result
}

/* =========================================
UPDATE ORDER
========================================= */
/*function updateOrder() {
  const payload = flattenTree(modules.value)
  console.log("PAYLOAD DRAG:", payload)  // 👈 AQUÍ
  menuStore.reorderModules(payload)
}
*/

async function updateOrder() {
  try {
    const payload = flattenTree(modules.value)

    //console.log("PAYLOAD DRAG:", payload)

    await api.put("/business-profile-module/reorder/", payload)

    showToast("Orden actualizado", "success")

    // 🔥 recargar sidebar real
    await menuStore.loadMenu()

  } catch (error) {
    console.error(error)
    showToast("Error guardando orden", "error")
  }
}

/* =========================================
STATE
========================================= */
const businessProfiles = ref([]);
const selectedProfileId = ref("");

/* =========================================
LOAD PROFILES
========================================= */
const loadProfiles = async () => {
  try {
    const res = await api.get("/business-profiles/");
    businessProfiles.value = res.data.data;
  } catch (error) {
    console.error(error);
  }
};


/* =========================================
LOAD MENU POR PERFIL
========================================= */
watch(selectedProfileId, async () => {
  if (!selectedProfileId.value) return;

  try {
    const res = await api.get(
      `/menu/by-profile/${selectedProfileId.value}`
    );
    //const tree = JSON.parse(JSON.stringify(res.data))
    //modules.value = tree.filter(item => !item.parent_id)
    //modules.value = JSON.parse(JSON.stringify(res.data))
    //console.log("MENU RAW1:", res.data)  // 👈 AQUÍ
    modules.value = res.data
    //menuStore.menu = menuStore.buildTree(res.data)
    // 🔥 FORZAR RECARGA DEL SIDEBAR
    await menuStore.loadMenu()

  } catch (error) {
    console.error("Error cargando menú por perfil 1:", error);
    modules.value = [];
  }
});


/* =========================================
GUARDAR ORDEN
========================================= */
/*const assignProfile = async () => {
  try {

    const payload = flattenTree(modules.value)

    await api.put("/business-profile-module/reorder/", payload);

    showToast("Orden guardado correctamente", "success");

  } catch (error) {
    console.error(error);
    showToast("Error guardando orden", "error");
  }
};
*/

/* =========================================
INIT
========================================= */
onMounted(() => {
  loadProfiles();
});
</script>

<style scoped>
.sysadmin-container {
  padding: 20px;
}
</style>