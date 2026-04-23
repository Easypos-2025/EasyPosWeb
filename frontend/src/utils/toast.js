import Swal from "sweetalert2"

/**
 * showToast — alerta central grande con animación SweetAlert2.
 *
 * REGLA GLOBAL: Usar siempre esta función para feedback al usuario.
 * Nunca usar alert(), toasts de esquina, ni console.log como feedback visual.
 *
 * @param {string} message  Texto a mostrar
 * @param {string} type     'success' | 'error' | 'warning' | 'info'
 * @param {number} timer    Milisegundos antes de cerrar (default 2500)
 */
export function showToast(message, type = "success", timer = 2500) {
  Swal.fire({
    title: message,
    icon: type === "warning" ? "warning"
        : type === "error"   ? "error"
        : type === "info"    ? "info"
        :                      "success",
    timer,
    timerProgressBar: true,
    showConfirmButton: false,
    position: "center",
    customClass: {
      popup: "swal-toast-popup",
      title: "swal-toast-title"
    }
  })
}
