import Swal from "sweetalert2"

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

export async function showConfirm(message, confirmText = "Sí, continuar") {
  const result = await Swal.fire({
    text: message,
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: confirmText,
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#2563eb",
    cancelButtonColor: "#64748b",
    reverseButtons: true,
    customClass: { popup: "swal-confirm-popup" },
    didOpen: (el) => {
      const container = el.closest(".swal2-container")
      if (container) container.style.zIndex = "99999"
    }
  })
  return result.isConfirmed
}
