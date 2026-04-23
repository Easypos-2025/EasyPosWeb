<!-- =========================================
ASSET CATEGORIES VIEW
=========================================

Vista para gestionar las categorías de activos

Funciones:
- Listar categorías
- Crear categorías
- Editar categorías
- Eliminar categorías

========================================= -->

<template>

<div class="page-container">

<h2>Asset Categories</h2>

<!-- FORMULARIO -->

<div class="form-container">

<form @submit.prevent="saveCategory">

<input
v-model="form.name"
placeholder="Category Name"
required
/>

<input
v-model="form.description"
placeholder="Description"
/>

<button type="submit">

{{ editing ? "Update Category" : "Create Category" }}

</button>

<button
type="button"
v-if="editing"
@click="resetForm"
>

Cancel

</button>

</form>

</div>

<hr>

<!-- TABLA -->

<table class="table">

<thead>

<tr>

<th>ID</th>
<th>Name</th>
<th>Description</th>
<th>Actions</th>

</tr>

</thead>

<tbody>

<tr
v-for="category in categories"
:key="category.id"
>

<td>{{ category.id }}</td>

<td>{{ category.name }}</td>

<td>{{ category.description }}</td>

<td>

<button @click="editCategory(category)">

Edit

</button>

<button @click="deleteCategory(category.id)">

Delete

</button>

</td>

</tr>

</tbody>

</table>

</div>

</template>

<script>

/* =========================================
IMPORT SERVICES
========================================= */

import {

getAssetCategories,
createAssetCategory,
updateAssetCategory,
deleteAssetCategory

} from "../services/assetCategoryService"

/* =========================================
COMPONENT
========================================= */

export default {

name:"AssetCategoriesView",

data(){

return{

categories:[],

form:{

name:"",
description:""

},

editing:false,

editingId:null

}

},

/* =========================================
LOAD DATA
========================================= */

mounted(){

this.loadCategories()

},

methods:{

/* =========================================
LOAD CATEGORIES
========================================= */

async loadCategories(){

try{

this.categories = await getAssetCategories()

}catch(error){

console.error("Error loading categories",error)

}

},

/* =========================================
SAVE CATEGORY
========================================= */

async saveCategory(){

try{

if(this.editing){

await updateAssetCategory(

this.editingId,

this.form

)

}else{

await createAssetCategory(

this.form

)

}

this.resetForm()

this.loadCategories()

}catch(error){

console.error("Error saving category",error)

}

},

/* =========================================
EDIT CATEGORY
========================================= */

editCategory(category){

this.form = {

name:category.name,

description:category.description

}

this.editing=true

this.editingId=category.id

},

/* =========================================
DELETE CATEGORY
========================================= */

async deleteCategory(id){

if(!confirm("Delete this category?")) return

try{

await deleteAssetCategory(id)

this.loadCategories()

}catch(error){

console.error("Error deleting category",error)

}

},

/* =========================================
RESET FORM
========================================= */

resetForm(){

this.form={

name:"",
description:""

}

this.editing=false

this.editingId=null

}

}

}

</script>

<style scoped>

.page-container{

padding:20px;

}

.form-container{

margin-bottom:20px;

}

input{

margin:5px;

padding:8px;

}

button{

margin:5px;

padding:8px 12px;

cursor:pointer;

}

.table{

width:100%;

border-collapse:collapse;

}

.table th,
.table td{

border:1px solid #ccc;

padding:8px;

text-align:left;

}

</style>