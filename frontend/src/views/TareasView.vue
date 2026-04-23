<template>

<div class="tareas-container">

<h2>Gestión de Tareas</h2>

<!-- FORMULARIO CREAR TAREA -->

<form class="form-tareas" @submit.prevent="crearNuevaTarea">

<div class="form-group">
<label>Título</label>
<input v-model="nuevaTarea.titulo" class="form-control" placeholder="Título de la tarea">
</div>

<div class="form-group">
<label>Descripción</label>
<textarea v-model="nuevaTarea.descripcion" class="form-control"></textarea>
</div>

<div class="form-group">
<label>Estado</label>
<select v-model="nuevaTarea.estado" class="form-control">
<option value="">Seleccione</option>
<option value="Pendiente">Pendiente</option>
<option value="Atrasada">Atrasada</option>
<option value="Terminada">Terminada</option>
</select>
</div>

<div class="form-actions">
<button class="btn btn-success">
Crear Tarea
</button>
</div>

</form>

<!-- TABLA -->

<div class="tabla-container">

<table class="table table-striped table-hover">

<thead class="table-dark">
<tr>
<th>ID</th>
<th>Título</th>
<th>Descripción</th>
<th>Estado</th>
<th>Acciones</th>
</tr>
</thead>

<tbody>

<tr v-for="t in tareas" :key="t.id">

<td>{{t.id}}</td>
<td>{{t.titulo}}</td>
<td>{{t.descripcion}}</td>
<td>

<span
class="badge bg-warning"
v-if="t.estado==='Pendiente'"
>
Pendiente
</span>

<span
class="badge bg-danger"
v-if="t.estado==='Atrasada'"
>
Atrasada
</span>

<span
class="badge bg-success"
v-if="t.estado==='Terminada'"
>
Terminada
</span>

</td>

<td>

<button
class="btn btn-primary btn-sm me-2"
@click="abrirModalEditar(t)"
>
Editar
</button>

<button
class="btn btn-danger btn-sm"
@click="eliminarTarea(t.id)"
>
Eliminar
</button>

</td>

</tr>

</tbody>

</table>

</div>

<!-- MODAL EDITAR -->

<div class="modal fade" id="modalEditarTarea">

<div class="modal-dialog">

<div class="modal-content">

<div class="modal-header">

<h5 class="modal-title">Editar Tarea</h5>

<button
type="button"
class="btn-close"
data-bs-dismiss="modal">
</button>

</div>

<div class="modal-body">

<div class="mb-3">
<label>Título</label>
<input
v-model="tareaEditar.titulo"
class="form-control">
</div>

<div class="mb-3">
<label>Descripción</label>
<textarea
v-model="tareaEditar.descripcion"
class="form-control">
</textarea>
</div>

<div class="mb-3">
<label>Estado</label>
<select
v-model="tareaEditar.estado"
class="form-control">

<option>Pendiente</option>
<option>Atrasada</option>
<option>Terminada</option>

</select>
</div>

</div>

<div class="modal-footer">

<button
class="btn btn-secondary"
data-bs-dismiss="modal">
Cancelar
</button>

<button
class="btn btn-primary"
@click="guardarEdicion">
Guardar
</button>

</div>

</div>

</div>

</div>

</div>

</template>

<script>

import Swal from "sweetalert2"

import {

obtenerTareas,
crearTarea,
eliminarTarea as eliminarTareaAPI,
actualizarTarea

} from "../services/tareasService"

export default{

data(){

return{

tareas:[],

nuevaTarea:{
titulo:"",
descripcion:"",
estado:"Pendiente"
},

tareaEditar:{
id:null,
titulo:"",
descripcion:"",
estado:""
}

}

},

mounted(){

this.cargarTareas()

},

methods:{


async cargarTareas(){

const res = await obtenerTareas()

this.tareas = res.data

},


async crearNuevaTarea(){

if(!this.nuevaTarea.titulo){

Swal.fire({
icon:"warning",
title:"Campo requerido",
text:"Debe ingresar un título"
})

return
}

await crearTarea(this.nuevaTarea)

Swal.fire({
icon:"success",
title:"Tarea creada"
})

this.nuevaTarea={
titulo:"",
descripcion:"",
estado:"Pendiente"
}

this.cargarTareas()

},


async eliminarTarea(id){

const confirmacion = await Swal.fire({

title:"¿Eliminar tarea?",
text:"Esta acción no se puede deshacer",
icon:"warning",
showCancelButton:true,
confirmButtonText:"Eliminar",
cancelButtonText:"Cancelar",
confirmButtonColor:"#d33"

})

if(confirmacion.isConfirmed){

await eliminarTareaAPI(id)

Swal.fire({
icon:"success",
title:"Tarea eliminada"
})

this.cargarTareas()

}

},


abrirModalEditar(t){

this.tareaEditar = {...t}

const modal = new bootstrap.Modal(
document.getElementById("modalEditarTarea")
)

modal.show()

},


async guardarEdicion(){

await actualizarTarea(
this.tareaEditar.id,
this.tareaEditar
)

Swal.fire({
icon:"success",
title:"Tarea actualizada"
})

const modal = bootstrap.Modal.getInstance(
document.getElementById("modalEditarTarea")
)

modal.hide()

this.cargarTareas()

}

}

}

</script>