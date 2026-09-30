// Bloqueo de mesa-cuenta: mientras un dispositivo tiene la mesa abierta, ningún otro
// mesero ni dispositivo puede entrar ni modificar el pedido. El servidor valida el
// token (header X-Edit-Token) en cada operación. Se libera al salir o enviar; si el
// dispositivo se apaga, el administrador la libera desde Cuentas Abiertas.
import apiComanda from "@/services/apiComanda"

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

export function useMesaLock(getTableId) {
  let token = null
  const clave = () => `mesa_lock_${localStorage.getItem("waiter_company_id") || ""}_${getTableId()}`

  function leerToken() {
    try {
      const t = localStorage.getItem(clave())
      if (t) return t
      const n = nuevoToken()
      localStorage.setItem(clave(), n)
      return n
    } catch { return nuevoToken() }
  }

  /** Toma la mesa. Lanza el error del servidor (409 si otro dispositivo la tiene). */
  async function tomar() {
    token = leerToken()
    apiComanda.defaults.headers.common["X-Edit-Token"] = token
    await apiComanda.post(`/api/pos/comanda/mesa/${getTableId()}/editar`, {
      waiter_name: nombreUsuario(), token,
    })
  }

  function limpiarLocal() {
    try { localStorage.removeItem(clave()) } catch { /* sin almacenamiento */ }
    delete apiComanda.defaults.headers.common["X-Edit-Token"]
    token = null
  }

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

  return { tomar, liberar, liberarAlCerrar }
}
