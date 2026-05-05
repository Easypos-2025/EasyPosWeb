<template>

  <li class="tree-node">

    <!-- ITEM -->
    <div 
      class="tree-item"
      :class="{ 'is-parent': hasChildren }"
      :style="{ marginLeft: level * 40 + 'px' }"
    >

      <!-- IZQUIERDA -->
      <div class="left">

        <span class="dot"></span>

        <span class="icon">
          {{ hasChildren ? "📁" : "📄" }}
        </span>

        <span class="name">
          <!-- {{ item.name }} ({{ item.children?.length || 0 }})-->
          <span class="name">{{ item.name }}</span>
        </span>


      </div>

      <!-- DERECHA: acciones (ocultas en modo preview) -->
      <div v-if="!preview" class="actions">
        <button class="btn btn-sm btn-warning" @click.stop="emit('edit', item)">Editar</button>
        <button class="btn btn-sm btn-danger" @click.stop="emit('delete', item)">Eliminar</button>
        <button
          class="btn btn-sm"
          :class="item.is_active ? 'btn-success' : 'btn-secondary'"
          @click.stop="emit('toggle', item)"
        >{{ item.is_active ? "Activo" : "Inactivo" }}</button>
      </div>

      <!-- RUTA en modo preview -->
      <span v-else class="preview-route">{{ item.route }}</span>

    </div>

    <!-- HIJOS: draggable solo si no está en modo noDrag ni preview -->
    <template v-if="hasChildren">
      <draggable
        v-if="!preview && !noDrag"
        v-model="item.children"
        item-key="id"
        :group="{ name: 'modules' }"
        class="tree-children"
        @end="emit('drag-end')"
      >
        <template #item="{ element }">
          <TreeItem
            :item="element"
            :level="level + 1"
            :no-drag="noDrag"
            @drag-end="emit('drag-end')"
            @delete="emit('delete', $event)"
            @edit="emit('edit', $event)"
            @toggle="emit('toggle', $event)"
          />
        </template>
      </draggable>

      <!-- noDrag: lista estática pero con botones de edición -->
      <ul v-else-if="noDrag && !preview" class="tree-children preview-children">
        <TreeItem
          v-for="child in item.children"
          :key="child.id"
          :item="child"
          :level="level + 1"
          :no-drag="true"
          @delete="emit('delete', $event)"
          @edit="emit('edit', $event)"
          @toggle="emit('toggle', $event)"
        />
      </ul>

      <ul v-else class="tree-children preview-children">
        <TreeItem
          v-for="child in item.children"
          :key="child.id"
          :item="child"
          :level="level + 1"
          :preview="true"
        />
      </ul>
    </template>

  </li>

</template>

<script setup>
import draggable from "vuedraggable"
import { computed } from "vue"

const props = defineProps({
  item: Object,
  level: { type: Number, default: 0 },
  preview: { type: Boolean, default: false },
  noDrag: { type: Boolean, default: false }
})

const emit = defineEmits([
  "drag-end",
  "delete",
  "edit",
  "toggle"
])

const hasChildren = computed(() => {
  return props.item.children && props.item.children.length
})
</script>

<style scoped>

/* ===== TREE ===== */

.tree-node {
  list-style: none;
}

/* ===== ITEM ===== */

.tree-item {
  display: flex;
  justify-content: space-between;
  align-items: center;

  background: #1e293b;
  color: #e2e8f0;

  padding: 10px 12px;
  border-radius: 8px;
  margin-bottom: 6px;

  transition: all 0.2s ease;
}

/* hover */
.tree-item:hover {
  background: #334155;
}

/* ===== PADRE ===== */

.is-parent {
  background: #020617; /* 🔥 mucho más oscuro */
  font-weight: 700;
  border-left: 4px solid #3b82f6;
}

/* ===== IZQUIERDA ===== */

.left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon {
  font-size: 14px;
}

.name {
  font-size: 13px;
}

/* ===== DOT ===== */

.dot {
  width: 6px;
  height: 6px;
  background: #3b82f6;
  border-radius: 50%;
}

/* ===== BOTONES ===== */

.actions {
  display: flex;
  gap: 6px;
}

.actions .btn {
  font-size: 11px;
  padding: 4px 8px;
}

/* ===== HIJOS ===== */

.tree-children {
  margin-left: 14px;
  padding-left: 14px;
  border-left: 2px solid #3b82f6; /* 🔥 más visible */
}

/* ===== MOBILE ===== */

@media (max-width: 600px) {

  .tree-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .actions {
    width: 100%;
    display: flex;
    gap: 6px;
  }

  .actions .btn {
    flex: 1;
  }

}

.tree-item:not(.is-parent) {
  background: #1e293b;
}

.preview-route {
  font-size: 11px;
  font-family: monospace;
  color: #64748b;
  opacity: 0.8;
}

.preview-children {
  padding: 0;
  margin: 0;
  list-style: none;
}

</style>