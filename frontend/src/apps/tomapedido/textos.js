/**
 * Textos que dependen del tipo de negocio (Cuenta, Producto, Mesero…): los entrega el agente
 * (GET /config) y nunca se escriben quemados en las pantallas. Se guardan en el navegador para
 * mostrarlos al instante la próxima vez.
 */
import { reactive } from "vue"
import { api } from "./api"

const CLAVE = "ag_textos"

export const textos = reactive({
  cuenta: "Cuenta", cuentas: "Cuentas", producto: "Producto", productos: "Productos",
  mesero: "Mesero", meseros: "Meseros",
  ...(() => { try { return JSON.parse(localStorage.getItem(CLAVE) || "{}") } catch { return {} } })(),
})

/** Texto en minúscula para usar dentro de una frase: t("producto") → "producto" */
export const t = (clave) => (textos[clave] || "").toLowerCase()

let cargados = false
export async function cargarTextos() {
  if (cargados) return
  try {
    const r = await api.get("/config")
    Object.assign(textos, r.textos || {})
    cargados = true
    try { localStorage.setItem(CLAVE, JSON.stringify(r.textos || {})) } catch { /* sin almacenamiento */ }
  } catch { /* se usan los guardados o los de por defecto */ }
}
