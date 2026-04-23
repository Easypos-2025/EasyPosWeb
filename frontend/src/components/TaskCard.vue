<template>
  <div :class="['task-card', estadoColor]">
    <h3>{{ tarea.titulo }}</h3>
    <p>{{ tarea.descripcion }}</p>
    <p><strong>Encargado:</strong> {{ tarea.tecnico }}</p>
    <p><strong>Estado:</strong> {{ tarea.estado }}</p>
    <p><strong>Fecha inicio:</strong> {{ tarea.fecha_inicio }}</p>
    <p><strong>Fecha entrega:</strong> {{ tarea.fecha_entrega }}</p>
    <p><strong>Costo:</strong> {{ tarea.costo }}</p>
  </div>
</template>

<script setup>
import { computed } from "vue"

const props = defineProps({
  tarea: Object
})

const estadoColor = computed(() => {
  switch (props.tarea.estado) {
    case "pendiente": return "pendiente"
    case "en progreso": return "en-progreso"
    case "terminado": return "terminado"
    default: return ""
  }
})
</script>

<style scoped>
.task-card {
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 10px;
  color: white;
}
.pendiente { background-color: #f39c12; }
.en-progreso { background-color: #2980b9; }
.terminado { background-color: #27ae60; }
</style>
