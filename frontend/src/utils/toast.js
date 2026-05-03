import Swal from "sweetalert2"

/**
 * showToast — pequeño toast de esquina con SweetAlert2.
 *
 * REGLA GLOBAL: Usar siempre esta función para feedback al usuario.
 * Nunca usar alert(), ni console.log como feedback visual.
 *
 * @param {string} message  Texto a mostrar
 * @param {string} type     'success' | 'error' | 'warning' | 'info'
 * @param {number} timer    Milisegundos antes de cerrar (default 1500)
 */
export function showToast(message, type = "success", timer = 1500) {
  Swal.fire({
    toast: true,
    title: message,
    icon: type === "warning" ? "warning"
        : type === "error"   ? "error"
        : type === "info"    ? "info"
        :                      "success",
    timer,
    timerProgressBar: true,
    showConfirmButton: false,
    position: "bottom-end",
    customClass: {
      popup: "swal-toast-popup",
      title: "swal-toast-title"
    },
    didOpen: (el) => {
      // Garantiza visibilidad sobre modales de recorte (z-index: 2000)
      const container = el.closest(".swal2-container")
      if (container) container.style.zIndex = "99999"
    }
  })
}
