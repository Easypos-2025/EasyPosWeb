
<template>
  <div class="sysadmin-container">

    <!-- SELECCIONAR PERFIL -->
    <div class="card smm-card p-3 mt-3">
      <h5 class="smm-title">Seleccione Business Profile</h5>
      <select v-model="selectedProfileId" class="form-select mt-2">
        <option value="">-- Seleccione un perfil --</option>
        <option v-for="profile in businessProfiles" :key="profile.id" :value="profile.id">
          {{ profile.name }}
        </option>
      </select>
    </div>

    <!-- GESTIÓN DE MENÚ -->
    <div class="card smm-card p-3 mt-3">
      <h5 class="smm-title">
        Gestión de Menú
        <span class="smm-hint">Arrastra por el ícono <i class="bi bi-grip-vertical"></i> para reordenar</span>
      </h5>

      <div v-if="!selectedProfileId" class="smm-empty">
        <i class="bi bi-arrow-up-circle"></i> Selecciona un perfil para gestionar su menú
      </div>

      <div v-else-if="modules.length === 0" class="smm-empty">
        <i class="bi bi-inbox"></i> No hay módulos en este perfil
      </div>

      <!-- PADRES -->
      <draggable
        v-else
        v-model="modules"
        item-key="id"
        :group="{ name: 'root', pull: false, put: false }"
        handle=".drag-handle"
        @change="updateOrder"
      >
        <template #item="{ element }">
          <div class="smm-item smm-parent">
            <span class="drag-handle"><i class="bi bi-grip-vertical"></i></span>
            <span class="smm-icon">
              <i v-if="element.icon?.startsWith('bi-')" :class="`bi ${element.icon}`"></i>
              <span v-else>{{ element.icon }}</span>
            </span>
            <span class="smm-name">{{ element.name }}</span>
            <span class="smm-route">{{ element.route || '—' }}</span>

            <!-- HIJOS -->
            <draggable
              v-if="element.children?.length"
              v-model="element.children"
              item-key="id"
              :group="{ name: 'children-' + element.id, pull: false, put: false }"
              handle=".drag-handle"
              class="smm-children"
              @change="updateOrder"
            >
              <template #item="{ element: child }">
                <div class="smm-item smm-child">
                  <span class="drag-handle"><i class="bi bi-grip-vertical"></i></span>
                  <span class="smm-icon">
                    <i v-if="child.icon?.startsWith('bi-')" :class="`bi ${child.icon}`"></i>
                    <span v-else>{{ child.icon }}</span>
                  </span>
                  <span class="smm-name">{{ child.name }}</span>
                  <span class="smm-route">{{ child.route }}</span>
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
import { ref, watch } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import { useMenuStore } from "@/stores/menuStore"
import draggable from "vuedraggable"

const menuStore = useMenuStore()
const modules = ref([])
const businessProfiles = ref([])
const selectedProfileId = ref("")

function flattenTree(nodes, parentId = null) {
  let result = []
  nodes.forEach((node, index) => {
    result.push({ id: node.id, parent_id: parentId, sort_order: index })
    if (node.children?.length) {
      result = result.concat(flattenTree(node.children, node.id))
    }
  })
  return result
}

async function updateOrder() {
  try {
    const payload = flattenTree(modules.value)
    await api.put("/business-profile-module/reorder/", payload)
    showToast("Orden actualizado", "success")
    await menuStore.loadMenu()
  } catch (error) {
    console.error(error)
    showToast("Error guardando orden", "error")
  }
}

const loadProfiles = async () => {
  try {
    const res = await api.get("/business-profiles/")
    businessProfiles.value = res.data.data ?? res.data
  } catch (error) {
    console.error(error)
  }
}

watch(selectedProfileId, async () => {
  if (!selectedProfileId.value) { modules.value = []; return }
  try {
    const res = await api.get(`/menu/by-profile/${selectedProfileId.value}`)
    modules.value = res.data
    await menuStore.loadMenu()
  } catch (error) {
    console.error("Error cargando menú por perfil:", error)
    modules.value = []
  }
})

loadProfiles()
</script>

<style scoped>
.sysadmin-container {
  padding: 20px;
  max-width: 800px;
}

.smm-card {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  color: #e2e8f0;
}

.smm-title {
  font-size: 15px;
  font-weight: 700;
  color: #e2e8f0;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.smm-hint {
  font-size: 11px;
  font-weight: 400;
  color: #64748b;
}

.smm-empty {
  color: #64748b;
  padding: 24px 0;
  text-align: center;
  font-size: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.smm-empty .bi { font-size: 24px; }

/* ── Item base ── */
.smm-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 12px;
  border-radius: 8px;
  margin-top: 6px;
  background: #0f172a;
  border: 1px solid #334155;
  cursor: default;
  user-select: none;
}

.smm-parent {
  flex-wrap: wrap;
  background: #0f172a;
  border-left: 3px solid #3b82f6;
}

.smm-child {
  background: #1e293b;
  border-left: 3px solid #64748b;
}

/* ── Drag handle ── */
.drag-handle {
  color: #475569;
  font-size: 18px;
  cursor: grab;
  padding: 6px 4px;        /* área táctil generosa */
  flex-shrink: 0;
  touch-action: none;
}
.drag-handle:active { cursor: grabbing; color: #3b82f6; }

/* ── Ícono del módulo ── */
.smm-icon {
  font-size: 16px;
  color: #94a3b8;
  min-width: 22px;
  flex-shrink: 0;
}

/* ── Nombre ── */
.smm-name {
  font-size: 14px;
  font-weight: 600;
  color: #e2e8f0;
  flex: 1;
}

/* ── Ruta ── */
.smm-route {
  font-size: 11px;
  color: #475569;
  font-family: monospace;
}

/* ── Hijos ── */
.smm-children {
  width: 100%;
  margin-top: 6px;
  padding-left: 28px;
  border-left: 2px solid #1e3a5f;
}

/* =========================================
   MÓVIL — más espacio para el dedo
========================================= */
@media (max-width: 768px) {
  .smm-item {
    padding: 18px 14px;   /* más alto para que no se toque accidentalmente */
    gap: 12px;
  }

  .drag-handle {
    font-size: 22px;
    padding: 10px 8px;    /* zona táctil amplia */
  }

  .smm-name {
    font-size: 15px;
  }

  .smm-route {
    display: none;        /* evita apretado en pantalla chica */
  }

  .smm-children {
    padding-left: 20px;
  }
}

@media (max-width: 576px) {
  .sysadmin-container {
    padding: 12px;
  }

  .smm-item {
    padding: 20px 12px;
  }
}
</style>
