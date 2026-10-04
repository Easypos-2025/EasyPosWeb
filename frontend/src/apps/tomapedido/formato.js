const moneda = new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 })
const numero = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 3 })

/** $ 12.500 (moneda del negocio; el agente trabaja en pesos sin decimales) */
export const pesos = (v) => moneda.format(Math.round(Number(v) || 0))

/** 1,5 · 2 · 0,264 */
export const cantidad = (v) => numero.format(Number(v) || 0)

/** Igual que el agente: 2.34 → filas 0.34, 1, 1; valor = precio × cantidad de cada fila */
export function valorLinea(precio, cant) {
  const enteras = Math.floor(cant + 1e-9)
  const fraccion = Math.round((cant - enteras) * 1000) / 1000
  return (fraccion > 0 ? Math.round(precio * fraccion) : 0) + enteras * Math.round(precio)
}
