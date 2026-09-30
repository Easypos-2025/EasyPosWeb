// Bloqueo de mesa-cuenta: al entrar a una mesa queda temp_mesa_abierta.Abierta = 1 con el
// nombre del dispositivo (Abierta_Desde). Nadie más puede entrar ni modificar el pedido:
// ni otro mesero, ni otro dispositivo, ni el mismo usuario en otro equipo o pestaña.
// El token vive en sessionStorage (es de ESTA pestaña; sobrevive solo a una recarga) y el
// servidor lo valida (header X-Edit-Token) en cada operación. Se libera al salir o enviar;
// si el dispositivo se apaga, el administrador la libera en Cuentas Abiertas.
import apiComanda from "@/services/apiComanda"
import api from "@/services/apis"

function nuevoToken() {
  if (window.crypto?.randomUUID) return window.crypto.randomUUID()
  const a = new Uint8Array(16)
  window.crypto.getRandomValues(a)
  return Array.from(a, b => b.toString(16).padStart(2, "0")).join("")
}

function nombreUsuario() {
  try {
    const w = JSON.parse(localStorage.getItem("waiter_data") || "{}")
    if (w.name) return w.name
    const u = JSON.parse(localStorage.getItem("user") || "{}")
    return u.name || u.full_name || u.email || "Usuario"
  } catch { return "Usuario" }
}

// Nombre legible y estable del dispositivo (navegador · sistema · id corto), guardado en
// este equipo. Es lo que se registra en temp_mesa_abierta.Abierta_Desde.
export function nombreDispositivo() {
  try {
    let n = localStorage.getItem("device_name")
    if (n) return n
    const ua = navigator.userAgent || ""
    const nav = /Edg\//.test(ua) ? "Edge" : /OPR\//.test(ua) ? "Opera" : /Chrome\//.test(ua) ? "Chrome"
      : /Firefox\//.test(ua) ? "Firefox" : /Safari\//.test(ua) ? "Safari" : "Navegador"
    const so = /Android/.test(ua) ? "Android" : /iPhone|iPad|iPod/.test(ua) ? "iOS" : /Windows/.test(ua) ? "Windows"
      : /Mac OS X/.test(ua) ? "Mac" : /Linux/.test(ua) ? "Linux" : "Equipo"
    n = `${so}-${nav}-${nuevoToken().replace(/-/g, "").slice(0, 4).toUpperCase()}`
    localStorage.setItem("device_name", n)
    return n
  } catch { return "Dispositivo web" }
}

export function useMesaLock(getTableId) {
  let token = null
  // Por pestaña y mesa: la ventana de detalle, "Agregar más" y PAGAR de la misma pestaña
  // comparten el token (se pasan la mesa sin soltarla); cualquier otra pestaña es otro dispositivo
  const clave = () => `mesa_lock_${getTableId()}`

  function leerToken() {
    try {
      const t = sessionStorage.getItem(clave())
      if (t) return t
      const n = nuevoToken()
      sessionStorage.setItem(clave(), n)
      return n
    } catch { return nuevoToken() }
  }

  /** Toma la mesa. Lanza el error del servidor (409 si otro dispositivo la tiene). */
  async function tomar() {
    token = leerToken()
    apiComanda.defaults.headers.common["X-Edit-Token"] = token
    api.defaults.headers.common["X-Edit-Token"] = token
    await apiComanda.post(`/api/pos/comanda/mesa/${getTableId()}/editar`, {
      waiter_name: nombreUsuario(), token, device_name: nombreDispositivo(),
    })
  }

  function limpiarLocal() {
    try { sessionStorage.removeItem(clave()) } catch { /* sin almacenamiento */ }
    delete apiComanda.defaults.headers.common["X-Edit-Token"]
    delete api.defaults.headers.common["X-Edit-Token"]
    token = null
  }

  /** Pasa la mesa a la siguiente pantalla de esta pestaña (Agregar más / PAGAR) sin soltarla. */
  function traspasar() { token = null }

  /** Libera la mesa (al salir o enviar). */
  async function liberar() {
    if (!token) return
    const t = token
    limpiarLocal()
    try {
      await apiComanda.delete(`/api/pos/comanda/mesa/${getTableId()}/editar`, { params: { token: t } })
    } catch { /* si falla, el administrador puede liberarla */ }
  }

  /** Al cerrar la pestaña o el navegador: petición que sobrevive a la descarga de la página. */
  function liberarAlCerrar() {
    if (!token) return
    const t = token
    limpiarLocal()
    const auth = localStorage.getItem("waiter_token") || localStorage.getItem("token")
    const base = import.meta.env.VITE_API_URL || ""
    try {
      fetch(`${base}/api/pos/comanda/mesa/${getTableId()}/editar?token=${encodeURIComponent(t)}`, {
        method: "DELETE", keepalive: true,
        headers: {
          ...(auth ? { Authorization: `Bearer ${auth}` } : {}),
          ...(localStorage.getItem("waiter_company_id") ? { "X-Company-Id": localStorage.getItem("waiter_company_id") } : {}),
        },
      })
    } catch { /* ignorar */ }
  }

  return { tomar, liberar, liberarAlCerrar, traspasar }
}
