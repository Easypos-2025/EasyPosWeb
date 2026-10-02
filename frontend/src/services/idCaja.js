/* Id_Caja elegido por el usuario en empresas que abren la caja desde el escritorio.
   Se guarda por empresa y se envía en cada petición (header X-Id-Caja); el servidor
   lo valida contra los Id_Caja abiertos de la empresa. */
const clave = () => {
  try {
    const sel = JSON.parse(localStorage.getItem("selected_company") || "null")
    return sel?.id ? `id_caja_${sel.id}` : null
  } catch { return null }
}

export function leerIdCaja() {
  try { const k = clave(); return k ? localStorage.getItem(k) : null } catch { return null }
}

export function guardarIdCaja(id) {
  try { const k = clave(); if (k) localStorage.setItem(k, String(id)) } catch { /* sin almacenamiento */ }
}
