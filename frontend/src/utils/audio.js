// Audio compartido de la app.
// Chrome no deja iniciar sonido hasta el primer gesto del usuario (clic, toque, tecla).
// El AudioContext NO se crea antes de ese gesto (crearlo antes genera la advertencia
// "The AudioContext was not allowed to start"). Un pitido pedido antes del primer
// gesto queda pendiente y suena apenas el usuario toque la página.

let ctx = null
let desbloqueado = false
let pendiente = null
const GESTOS = ["pointerdown", "keydown", "touchstart"]

function crearContexto() {
  const AudioCtx = window.AudioContext || window.webkitAudioContext
  if (!AudioCtx) return null
  if (!ctx || ctx.state === "closed") ctx = new AudioCtx()
  return ctx
}

function sonar({ freq = 880, duracion = 0.35, volumen = 0.25 } = {}) {
  const c = crearContexto()
  if (!c) return
  const osc = c.createOscillator()
  const gain = c.createGain()
  osc.type = "sine"
  osc.frequency.value = freq
  gain.gain.setValueAtTime(0.0001, c.currentTime)
  gain.gain.exponentialRampToValueAtTime(volumen, c.currentTime + 0.01)
  gain.gain.exponentialRampToValueAtTime(0.0001, c.currentTime + duracion)
  osc.connect(gain)
  gain.connect(c.destination)
  osc.start()
  osc.stop(c.currentTime + duracion + 0.05)
}

async function alPrimerGesto() {
  GESTOS.forEach(g => window.removeEventListener(g, alPrimerGesto, true))
  try {
    const c = crearContexto()
    if (c && c.state === "suspended") await c.resume()
    desbloqueado = true
    if (pendiente) { const p = pendiente; pendiente = null; sonar(p) }
  } catch { /* audio no disponible */ }
}

if (typeof window !== "undefined") {
  GESTOS.forEach(g => window.addEventListener(g, alPrimerGesto, { capture: true, passive: true }))
}

/** Pitido corto. Si aún no hubo gesto del usuario, queda pendiente (solo el último). */
export function beep(opciones) {
  try {
    if (!desbloqueado) { pendiente = opciones || {}; return }
    sonar(opciones)
  } catch { /* audio no disponible en este navegador */ }
}
