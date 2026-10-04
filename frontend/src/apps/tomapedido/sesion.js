/**
 * Sesión del dispositivo (solo en este navegador, con prefijo propio "ag_").
 *   secreto  identifica al navegador ante el agente (para la espera de activación)
 *   token    sesión del mesero; un nuevo ingreso en otro equipo la invalida
 */
import { reactive } from "vue"

const CLAVE = "ag_sesion"

function leer() {
  try { return JSON.parse(localStorage.getItem(CLAVE) || "{}") } catch { return {} }
}

export const sesion = reactive({
  secreto: "", token: "", estado: "", usuario: "", nombre_dispositivo: "", mesero: null,
  ...leer(),
})

export function guardarSesion(cambios = {}) {
  Object.assign(sesion, cambios)
  try {
    localStorage.setItem(CLAVE, JSON.stringify({
      secreto: sesion.secreto, token: sesion.token, estado: sesion.estado, usuario: sesion.usuario,
      nombre_dispositivo: sesion.nombre_dispositivo, mesero: sesion.mesero,
    }))
  } catch { /* navegador sin almacenamiento: la sesión dura mientras la página esté abierta */ }
}

export function cerrarSesion() {
  guardarSesion({ token: "", mesero: null })
}
