// Orden alfabético estándar del proyecto (NORMA: todo catálogo y selector va A-Z).
// Español: ignora mayúsculas y tildes, ñ en su lugar, números naturales ("Caja 2" < "Caja 10").
const collator = new Intl.Collator("es", { sensitivity: "base", numeric: true })

export function compararTexto(a, b) {
  return collator.compare(String(a ?? "").trim(), String(b ?? "").trim())
}

/**
 * Devuelve una copia de la lista ordenada A-Z.
 * campo: nombre de propiedad, función (item) => texto, o vacío si la lista es de textos.
 */
export function ordenAlfa(lista, campo) {
  if (!Array.isArray(lista)) return []
  const valor = typeof campo === "function"
    ? campo
    : campo ? (x) => x?.[campo] : (x) => x
  return [...lista].sort((a, b) => compararTexto(valor(a), valor(b)))
}

/** Detalle de pedido: último ítem ingresado primero. */
export function ordenItemDesc(lista, campo = "item") {
  if (!Array.isArray(lista)) return []
  return [...lista].sort((a, b) => (Number(b?.[campo]) || 0) - (Number(a?.[campo]) || 0))
}
