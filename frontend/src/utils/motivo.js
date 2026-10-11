/**
 * Motivo obligatorio para pedir a la caja del escritorio que elimine productos o cancele una cuenta
 * (empresas con Agente Local, S2). El servidor responde 428 cuando falta: se pide y se reintenta.
 *
 *   await conMotivo((motivo) => api.delete(url, { data: { ..., motivo } }), 'Eliminar producto')
 *
 * Si el usuario cancela el diálogo se lanza un error con `cancelado = true` (el llamador lo ignora).
 */
import Swal from "sweetalert2"

export async function pedirMotivo(titulo, explicacion) {
  const r = await Swal.fire({
    title: titulo,
    text: explicacion || "La caja del escritorio debe aceptar la solicitud.",
    input: "textarea",
    inputPlaceholder: "Motivo (obligatorio)",
    inputAttributes: { maxlength: "255", "aria-label": "Motivo" },
    showCancelButton: true,
    confirmButtonText: "Enviar a caja",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#dc2626",
    reverseButtons: true,
    inputValidator: (v) => ((v || "").trim().length < 3 ? "Escriba el motivo (mínimo 3 letras)" : undefined),
    didOpen: (el) => {
      const c = el.closest(".swal2-container")
      if (c) c.style.zIndex = "99999"
    },
  })
  return r.isConfirmed ? (r.value || "").trim() : null
}

export async function conMotivo(llamada, titulo) {
  try {
    return await llamada(null)
  } catch (e) {
    if (e?.response?.status !== 428) throw e
    const motivo = await pedirMotivo(titulo, e.response.data?.detail)
    if (!motivo) throw Object.assign(new Error("cancelado"), { cancelado: true })
    return await llamada(motivo)
  }
}

export const esCancelado = (e) => !!e?.cancelado
