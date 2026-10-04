const moneda = new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 })
const numero = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 3 })

/** $ 12.500 (moneda del negocio; el agente trabaja en pesos sin decimales) */
export const pesos = (v) => moneda.format(Math.round(Number(v) || 0))

/** 1,5 · 2 · 0,264 */
export const cantidad = (v) => numero.format(Number(v) || 0)

/** Texto oscuro o blanco según el fondo (#rrggbb) */
export function textoSobre(hex) {
  const n = parseInt(String(hex).slice(1), 16)
  const lum = (0.299 * (n >> 16) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) / 255
  return lum > 0.6 ? "#1e293b" : "#ffffff"
}

/** Como el escritorio: alterna el color primario y el secundario (por posición o por fila) */
export function colorAlterno(colores, indice) {
  const c = colores?.[indice % 2] || colores?.[0]
  return c ? { background: c, color: textoSobre(c) } : null
}

/** Igual que el agente: 2.34 → filas 0.34, 1, 1; valor = precio × cantidad de cada fila */
export function valorLinea(precio, cant) {
  const enteras = Math.floor(cant + 1e-9)
  const fraccion = Math.round((cant - enteras) * 1000) / 1000
  return (fraccion > 0 ? Math.round(precio * fraccion) : 0) + enteras * Math.round(precio)
}
