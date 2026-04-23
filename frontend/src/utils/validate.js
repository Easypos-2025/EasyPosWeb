/**
 * validateForm — validación de formularios con foco y resaltado de campo.
 *
 * REGLA GLOBAL: Usar esta función en TODAS las vistas para validar formularios.
 * Al fallar validación: resalta el primer campo vacío en rojo y mueve el foco a él.
 *
 * @param {Array} fields  Lista de { value, selector, label }
 *   - value:    el valor del campo (string | number)
 *   - selector: selector CSS del input ('[data-v="nombre"]') o ref string
 *   - label:    nombre legible del campo (para el mensaje)
 * @returns {{ valid: boolean, message: string }}
 *
 * Uso en template: <input data-v="nombre" ... />
 * Uso en script:
 *   const result = validateForm([
 *     { value: form.nombre, selector: '[data-v="nombre"]', label: 'Nombre' },
 *     { value: form.email,  selector: '[data-v="email"]',  label: 'Email' },
 *   ])
 *   if (!result.valid) { showToast(result.message, 'warning'); return }
 */
export function validateForm(fields) {
  // Limpiar resaltados previos
  document.querySelectorAll(".field-invalid").forEach(el => el.classList.remove("field-invalid"))

  for (const field of fields) {
    const isEmpty = field.value === null
                 || field.value === undefined
                 || field.value.toString().trim() === ""

    if (isEmpty) {
      const el = document.querySelector(field.selector)
      if (el) {
        el.classList.add("field-invalid")
        el.focus()
      }
      return { valid: false, message: `El campo "${field.label}" es obligatorio` }
    }
  }

  return { valid: true, message: "" }
}
