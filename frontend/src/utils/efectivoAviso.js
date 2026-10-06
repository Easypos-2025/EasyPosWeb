/* =========================================
Aviso: forma de pago EFECTIVO sin configurar (CLAUDE.md §8.10)

EFECTIVO = la forma de pago Default y Activa de la empresa. Sin exactamente una, el servidor
bloquea registros y reportes (409 + header X-Error-Code: EFECTIVO_NO_CONFIGURADO) y aquí se
abre la ventana EfectivoNoConfiguradoModal (montada en App.vue) que explica cómo corregirlo.
========================================= */
import { reactive } from "vue"
import api from "@/services/apis"

export const EFECTIVO_NO_CONFIGURADO = "EFECTIVO_NO_CONFIGURADO"

export const avisoEfectivo = reactive({
  visible: false,
  mensaje: "",      // texto del servidor con el problema exacto
  estado: null,     // { ok, problema, defaults, mensaje } (usuarios del sistema; el mesero no lo consulta)
})

let _ultimaRevision = 0

/** ¿La respuesta de error es el bloqueo por EFECTIVO sin configurar? */
export function esErrorEfectivo(err) {
  return err?.response?.status === 409 &&
    String(err.response.headers?.["x-error-code"] || "") === EFECTIVO_NO_CONFIGURADO
}

/** Abre la ventana (desde los interceptores de axios). */
export function mostrarAvisoEfectivo(mensaje = "") {
  avisoEfectivo.mensaje = mensaje || avisoEfectivo.mensaje
  avisoEfectivo.visible = true
  if (localStorage.getItem("token")) revisarEfectivo({ forzar: true, abrir: false })
}

/**
 * Consulta el estado (usuarios del sistema). `abrir`: muestra la ventana si está mal.
 * Empresas sin formas de pago (perfiles que no cobran) no se avisan aquí: solo las bloquea el servidor.
 */
export async function revisarEfectivo({ forzar = false, abrir = true } = {}) {
  if (!localStorage.getItem("token")) return null
  if (!forzar && Date.now() - _ultimaRevision < 120000) return avisoEfectivo.estado
  _ultimaRevision = Date.now()
  try {
    const { data } = await api.get("/api/payment-types/estado-efectivo", { _skipErrorReport: true })
    avisoEfectivo.estado = data
    if (data?.ok) {
      avisoEfectivo.visible = false
    } else if (abrir && data?.total > 0) {
      avisoEfectivo.mensaje = data.mensaje
      avisoEfectivo.visible = true
    }
    return data
  } catch {
    return null
  }
}

export function cerrarAvisoEfectivo() {
  avisoEfectivo.visible = false
}
