/**
 * Cliente de la API del Agente Local (mismo origen: la página la sirve el propio agente).
 * Los mensajes de error vienen del agente ya en español.
 */
import { sesion, cerrarSesion } from "./sesion"

export class ErrorApi extends Error {
  constructor(mensaje, estado) { super(mensaje); this.estado = estado }
}

async function pedir(metodo, ruta, { cuerpo, params, encabezados = {} } = {}) {
  const url = new URL("/api/ag" + ruta, window.location.origin)
  if (params) Object.entries(params).forEach(([k, v]) => v != null && url.searchParams.set(k, v))
  const h = { ...encabezados }
  if (sesion.token) h.Authorization = `Bearer ${sesion.token}`
  if (cuerpo !== undefined) h["Content-Type"] = "application/json"

  let r
  try {
    r = await fetch(url, { method: metodo, headers: h, body: cuerpo !== undefined ? JSON.stringify(cuerpo) : undefined })
  } catch {
    throw new ErrorApi("Sin conexión con el equipo de caja. Revise el wifi.", 0)
  }
  if (r.status === 304) return { noModificado: true }
  let datos = null
  try { datos = await r.json() } catch { /* respuesta sin cuerpo */ }
  if (!r.ok) {
    // Sesión vencida, reemplazada por otro ingreso o dispositivo desactivado
    if ((r.status === 401 || r.status === 403) && sesion.token && !ruta.startsWith("/sesion/ingresar")) {
      cerrarSesion()
      if (!location.hash.startsWith("#/ingresar")) location.hash = "#/ingresar"
    }
    throw new ErrorApi(datos?.detail || "No fue posible completar la operación.", r.status)
  }
  return { datos, etag: r.headers.get("ETag") }
}

export const api = {
  get:  (ruta, params, encabezados) => pedir("GET", ruta, { params, encabezados }).then(r => r.datos ?? r),
  post: (ruta, cuerpo) => pedir("POST", ruta, { cuerpo: cuerpo ?? {} }).then(r => r.datos),
  // Carta con versión: si no cambió, el agente responde 304 y se usa la guardada
  async catalogo(cliente) {
    const guardada = cacheCarta[cliente]
    const r = await pedir("GET", "/catalogo", { params: { cliente },
      encabezados: guardada ? { "If-None-Match": guardada.version } : {} })
    if (r.noModificado) return guardada
    cacheCarta[cliente] = r.datos
    return r.datos
  },
}

const cacheCarta = {}
