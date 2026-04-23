<template>

<div class="table-container">

<table class="table">

<thead>

<tr>
<th>ID</th>
<th>Titulo</th>
<th>Tecnico</th>
<th>Estado</th>
<th>Acciones</th>
</tr>

</thead>

<tbody>

<tr v-for="t in tareas" :key="t.id">

<td>{{ t.id }}</td>
<td>{{ t.titulo }}</td>
<td>{{ t.tecnico_nombre }}</td>
<td>{{ t.estado }}</td>

<td>

<button
class="btn-editar"
@click="$emit('editar', t)"
>
Editar
</button>

<button
class="btn-eliminar"
@click="$emit('eliminar', t.id)"
>
Eliminar
</button>

</td>

</tr>

</tbody>

</table>

</div>

</template>

<script>

export default{

name:"TablaTareas",

props:{
tareas:Array
}

}

</script>