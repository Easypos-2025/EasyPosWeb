<template>
  <div class="task-form">
    <h2>Crear Tarea</h2>
    <form @submit.prevent="crearTarea">
      <div>
        <label>Título:</label>
        <input v-model="titulo" required />
      </div>

      <div>
        <label>Descripción:</label>
        <textarea v-model="descripcion" required></textarea>
      </div>

      <div>
        <label>Encargado:</label>
        <select v-model="encargadoId" required>
          <option v-for="u in usuarios" :key="u.id" :value="u.id">{{ u.nombre }}</option>
        </select>
      </div>

      <div>
        <label>Técnico:</label>
        <input v-model="tecnico" required />
      </div>

      <div>
        <label>Costo:</label>
        <input type="number" v-model="costo" required />
      </div>

      <div>
        <label>Fecha inicio:</label>
        <input type="date" v-model="fechaInicio" required />
      </div>

      <div>
        <label>Fecha entrega:</label>
        <input type="date" v-model="fechaEntrega" required />
      </div>

      <button type="submit">Crear Tarea</button>
    </form>

    <p v-if="mensaje">{{ mensaje }}</p>
  </div>
</template>

<script setup>
import { ref } from "vue"
import axios from "axios"

const props = defineProps({
  usuarios: Array
})
const emit = defineEmits(["tarea-creada"])

const titulo = ref("")
const descripcion = ref("")
const encargadoId = ref("")
const tecnico = ref("")
const costo = ref(0)
const fechaInicio = ref("")
const fechaEntrega = ref("")
const mensaje = ref("")

const crearTarea = async () => {
  try {
    await axios.post("http://127.0.0.1:8000/tareas", { 
      titulo: titulo.value,
      descripcion: descripcion.value,
      encargado_id: encargadoId.value,
      tecnico: tecnico.value,
      costo: parseFloat(costo.value),
      fecha_inicio: fechaInicio.value,
      fecha_entrega: fechaEntrega.value
    })
    mensaje.value = "Tarea creada correctamente!"

    // Limpiar formulario
    titulo.value = ""
    descripcion.value = ""
    encargadoId.value = ""
    tecnico.value = ""
    costo.value = 0
    fechaInicio.value = ""
    fechaEntrega.value = ""

    emit("tarea-creada")
  } catch (error) {
    console.error(error)
    mensaje.value = "Error al crear la tarea"
  }
}
</script>

<style scoped>
.task-form div { margin-bottom: 8px; }
button { cursor: pointer; padding: 5px 10px; }
</style>
