import axios from "axios"

const API = "http://127.0.0.1:8000/tareas"


// OBTENER TODAS LAS TAREAS
export const obtenerTareas = () => {
return axios.get(API)
}


// CREAR TAREA
export const crearTarea = (tarea) => {
return axios.post(API, tarea)
}


// ACTUALIZAR TAREA
export const actualizarTarea = (id, tarea) => {
return axios.put(`${API}/${id}`, tarea)
}


// ELIMINAR TAREA
export const eliminarTarea = (id) => {
return axios.delete(`${API}/${id}`)
}