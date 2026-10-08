/**
 * Cliente de la API del Agente Local (mismo origen: la página la sirve el propio agente).
 * Los mensajes de error vienen del agente ya en español.
 *
 *  · conexion.ok = false cuando el dispositivo no logra hablar con el PC de caja (App.vue muestra
 *    el aviso a pantalla completa y reintenta).
 *  · Los errores que ocurren sin conexión se guardan en el dispositivo y se envían al volver.
 *  · El panel de administración usa su propia sesión (no la del mesero).
 */
import { reactive } from "vue"
import { sesion, cerrarSesion } from "./sesion"

export class ErrorApi extends Error {
  constructor(mensaje, estado) { super(mensaje); this.estado = estado }
}

export const conexion = reactive({ ok: true, desde: null })
// Versión nueva del agente lista para instalar (llega con el latido; aviso en "Cuentas abiertas")
export const actualizacion = reactive({ lista: false, aplicando: false, nueva: null, notas: null })
// Caja (turno) del escritorio: cerrada o con otra fecha → no se comanda (pantalla "Caja cerrada")
export const caja = reactive({ abierta: true, motivo: null, mensaje: null, fecha: null })
// Versión del agente (compilación) que se muestra en la toma de pedidos
export const agente = reactive({ version: null })
// Estilo de tarjetas de las cuentas abiertas (el que la empresa escogió en la web; llega con el latido)
export const preferencias = reactive({
  estilo: (() => { try { return localStorage.getItem("ag_estilo_tarjetas") || "oval-wood" } catch { return "oval-wood" } })(),
})

const COLA = "ag_cola_errores"
const ADMIN = "ag_admin"

export const admin = reactive((() => {
  try {
    const a = JSON.parse(localStorage.getItem(ADMIN) || "{}")
    return a.vence > Date.now() ? a : { token: "", vence: 0 }
  } catch { return { token: "", vence: 0 } }
})())

export function guardarAdmin(token) {
  admin.token = token
  admin.vence = token ? Date.now() + 11.5 * 3600 * 1000 : 0
  try { localStorage.setItem(ADMIN, JSON.stringify(admin)) } catch { /* sin almacenamiento */ }
}

/** Guarda un error en el dispositivo para enviarlo cuando haya conexión (máximo 50). */
export function encolarError(ev) {
  try {
    const cola = JSON.parse(localStorage.getItem(COLA) || "[]")
    cola.push({ cuando: new Date().toLocaleString("es-CO"), vista: location.hash.slice(1, 200) || "/", ...ev })
    localStorage.setItem(COLA, JSON.stringify(cola.slice(-50)))
  } catch { /* sin almacenamiento */ }
}

let enviandoCola = false
export async function enviarCola() {
  if (enviandoCola) return
  let cola
  try { cola = JSON.parse(localStorage.getItem(COLA) || "[]") } catch { cola = [] }
  if (!cola.length) return
  enviandoCola = true
  try {
    for (let i = 0; i < cola.length; i += 20) {
      await pedir("POST", "/errores", { cuerpo: { eventos: cola.slice(i, i + 20) }, silencioso: true })
    }
    localStorage.removeItem(COLA)
  } catch { /* se reintenta en la próxima conexión */ } finally {
    enviandoCola = false
  }
}

function marcarSinConexion() {
  if (conexion.ok) {
    conexion.ok = false
    conexion.desde = new Date()
    encolarError({ tipo: "RED", nivel: "ADVERTENCIA", titulo: "Sin conexión con el equipo de caja",
                   mensaje: navigator.onLine ? "El dispositivo tiene red pero no responde el agente." : "El dispositivo no tiene red." })
  }
}

function marcarConexion() {
  if (!conexion.ok) {
    conexion.ok = true
    conexion.desde = null
    enviarCola()
  }
}

async function pedir(metodo, ruta, { cuerpo, params, encabezados = {}, comoAdmin = false, silencioso = false, binario = false } = {}) {
  const url = new URL("/api/ag" + ruta, window.location.origin)
  if (params) Object.entries(params).forEach(([k, v]) => v != null && url.searchParams.set(k, v))
  const h = { ...encabezados }
  const token = comoAdmin ? admin.token : sesion.token
  if (token) h.Authorization = `Bearer ${token}`
  if (cuerpo !== undefined) h["Content-Type"] = "application/json"

  let r
  try {
    r = await fetch(url, { method: metodo, headers: h, body: cuerpo !== undefined ? JSON.stringify(cuerpo) : undefined })
  } catch {
    if (!silencioso) marcarSinConexion()
    throw new ErrorApi("Sin conexión con el equipo de caja. Revise el wifi.", 0)
  }
  marcarConexion()
  if (r.status === 304) return { noModificado: true }
  if (binario && r.ok) return { datos: await r.blob() }
  let datos = null
  try { datos = await r.json() } catch { /* respuesta sin cuerpo */ }
  if (!r.ok) {
    if (r.status === 401 && comoAdmin) {
      guardarAdmin("")
      if (!location.hash.startsWith("#/admin/ingresar")) location.hash = "#/admin/ingresar"
    } else if ((r.status === 401 || r.status === 403) && sesion.token && !comoAdmin && !ruta.startsWith("/sesion/ingresar")) {
      // Sesión vencida, reemplazada por otro ingreso o dispositivo desactivado
      cerrarSesion()
      if (!location.hash.startsWith("#/ingresar")) location.hash = "#/ingresar"
    }
    if (r.status === 409 && r.headers.get("X-Error-Code") === "CAJA_CERRADA") {
      Object.assign(caja, { abierta: false, mensaje: datos?.detail || null })
    }
    if (r.status >= 500 && !silencioso) {
      encolarError({ tipo: "VISTA", nivel: "ERROR", titulo: `Error del agente en ${ruta.split("?")[0]}`,
                     mensaje: datos?.detail || `HTTP ${r.status}` })
      enviarCola()
    }
    throw new ErrorApi(datos?.detail || "No fue posible completar la operación.", r.status)
  }
  return { datos, etag: r.headers.get("ETag") }
}

export const api = {
  get:  (ruta, params, encabezados) => pedir("GET", ruta, { params, encabezados }).then(r => r.datos ?? r),
  post: (ruta, cuerpo) => pedir("POST", ruta, { cuerpo: cuerpo ?? {} }).then(r => r.datos),
  /** Latidos y comprobaciones: si no hay respuesta se activa el aviso de "sin conexión" */
  ping: (ruta, metodo = "GET") => pedir(metodo, ruta, { cuerpo: metodo === "POST" ? {} : undefined }),
  // Carta con versión: si no cambió, el agente responde 304 y se usa la guardada
  async catalogo(cliente) {
    const guardada = cacheCarta[cliente]
    const r = await pedir("GET", "/catalogo", { params: { cliente },
      encabezados: guardada ? { "If-None-Match": guardada.version } : {} })
    if (r.noModificado) return guardada
    cacheCarta[cliente] = r.datos
    return r.datos
  },
  admin: {
    get:  (ruta, params) => pedir("GET", "/admin" + ruta, { params, comoAdmin: true }).then(r => r.datos),
    post: (ruta, cuerpo) => pedir("POST", "/admin" + ruta, { cuerpo: cuerpo ?? {}, comoAdmin: true }).then(r => r.datos),
    imagen: (ruta) => pedir("GET", "/admin" + ruta, { comoAdmin: true, binario: true }).then(r => r.datos),
  },
}

const cacheCarta = {}
