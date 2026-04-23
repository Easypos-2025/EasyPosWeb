<template>

<div class="modal">

  <div class="modal-content">

    <h2>Editar tarea</h2>

    <input v-model="localTarea.titulo" placeholder="Titulo">

    <textarea v-model="localTarea.descripcion"></textarea>

    <input type="number" v-model="localTarea.costo">

    <label>Fecha inicio</label>
    <input type="datetime-local" v-model="localTarea.fecha_inicio">

    <label>Fecha entrega</label>
    <input type="datetime-local" v-model="localTarea.fecha_entrega">

    <label>Fecha finalizacion</label>
    <input type="datetime-local" v-model="localTarea.fecha_finalizacion">

    <select v-model="localTarea.tecnico_id">

      <option
        v-for="t in tecnicos"
        :key="t.id"
        :value="t.id"
      >
        {{ t.nombre }}
      </option>

    </select>

    <br><br>

    <button @click="guardar">
      Guardar
    </button>

    <button @click="$emit('cerrar')">
      Cerrar
    </button>

  </div>

</div>

</template>

<script>

export default {

name:"ModalEditar",

props:{
tarea:Object,
tecnicos:Array
},

data(){
return{
localTarea:{}
}
},

mounted(){

/* copiamos la tarea para no modificar la prop directamente */
this.localTarea = {...this.tarea}

},

methods:{

guardar(){

this.$emit("guardar", this.localTarea)

}

}

}

</script>