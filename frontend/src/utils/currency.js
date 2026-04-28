/**
 * Detección de moneda a partir del locale del navegador.
 * Fallback: COP (Colombia).
 */
const LOCALE_TO_CURRENCY = {
  "es-CO": "COP", "es-MX": "MXN", "en-US": "USD", "en-CA": "CAD",
  "pt-BR": "BRL", "es-AR": "ARS", "es-PE": "PEN", "es-CL": "CLP",
  "es-VE": "VES", "es-EC": "USD", "es-BO": "BOB", "es-PY": "PYG",
  "es-UY": "UYU", "es-CR": "CRC", "es-PA": "USD", "es-DO": "DOP",
  "es-GT": "GTQ", "es-HN": "HNL", "es-SV": "USD", "es-NI": "NIO",
  "es-ES": "EUR", "fr-FR": "EUR", "de-DE": "EUR", "it-IT": "EUR",
  "en-GB": "GBP", "en-AU": "AUD", "ja-JP": "JPY", "zh-CN": "CNY",
}

export const CURRENCY_NAMES = {
  COP: "Peso colombiano",   MXN: "Peso mexicano",
  USD: "Dólar estadounidense", EUR: "Euro",
  BRL: "Real brasileño",    ARS: "Peso argentino",
  PEN: "Sol peruano",       CLP: "Peso chileno",
  GTQ: "Quetzal",           HNL: "Lempira",
  NIO: "Córdoba nicaragüense", DOP: "Peso dominicano",
  CRC: "Colón costarricense",  BOB: "Boliviano",
  PYG: "Guaraní",           UYU: "Peso uruguayo",
  CAD: "Dólar canadiense",  GBP: "Libra esterlina",
}

export const SUPPORTED_CURRENCIES = Object.keys(CURRENCY_NAMES)

/**
 * Detecta la moneda del usuario según el locale del navegador.
 * @returns {string} Código ISO 4217 (ej: "COP", "USD")
 */
export function detectCurrency() {
  const locale = navigator.language || "es-CO"
  return LOCALE_TO_CURRENCY[locale]
      || LOCALE_TO_CURRENCY[locale.substring(0, 5)]
      || "COP"
}

/**
 * Formatea un monto según la moneda dada.
 * @param {number} amount
 * @param {string} currency  ISO 4217
 * @returns {string}
 */
export function formatMoney(amount, currency = "COP") {
  if (amount === 0) return "Gratis"
  try {
    return new Intl.NumberFormat("es-CO", {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    }).format(amount)
  } catch {
    return `${currency} ${amount.toLocaleString()}`
  }
}
