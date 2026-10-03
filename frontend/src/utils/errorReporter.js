/* =========================================
Monitor de Errores — captura en el navegador
- Errores de Vue / JavaScript (VISTA) y fallas de red (RED).
- Referencia ERR-XXXXXXXX de errores del servidor para mostrarla en el toast.
- Anti-tormenta: el mismo error se envía máximo 1 vez por minuto, en lotes de
  hasta 10 y máximo 20 eventos por minuto. Nunca lanza excepciones.
========================================= */

const ENDPOINT      = "/api/error-log/client"
const FLUSH_MS      = 3000
const DEDUPE_MS     = 60000
const MAX_BATCH     = 10
const MAX_PER_MIN   = 20
const REF_TTL_MS    = 5000
const TOAST_LINK_MS = 4000

const queue = []
const seen  = new Map()
let timer = null
let windowStart = Date.now()
let sentInWindow = 0
let lastRef = null            // { ref, at }

const trunc = (v, n) => (v == null ? null : String(v).slice(0, n))

function schedule() {
  if (!timer) timer = setTimeout(flush, FLUSH_MS)
}

async function flush() {
  timer = null
  if (!queue.length) return
  const now = Date.now()
  if (now - windowStart > 60000) { windowStart = now; sentInWindow = 0 }
  const room = Math.max(0, Math.min(MAX_BATCH, MAX_PER_MIN - sentInWindow))
  if (!room) { queue.length = 0; return }
  const events = queue.splice(0, room).map(({ _at, ...e }) => e)
  queue.length = 0
  sentInWindow += events.length
  try {
    const { default: api } = await import("@/services/apis")
    const headers = {}
    // Pantallas de mesero: sin token de usuario se identifica con el token del mesero
    if (!localStorage.getItem("token")) {
      const wt = localStorage.getItem("waiter_token")
      if (wt) headers.Authorization = `Bearer ${wt}`
    }
    await api.post(ENDPOINT, { events }, { headers, _skipErrorReport: true })
  } catch { /* el reporte nunca debe molestar al usuario */ }
}

function enqueue(ev) {
  try {
    const key = [ev.kind, ev.tipo, ev.clase, (ev.mensaje || "").slice(0, 200), ev.endpoint || "", ev.ref || "", location.pathname].join("|")
    const now = Date.now()
    if (seen.get(key) > now - DEDUPE_MS) return
    seen.set(key, now)
    if (seen.size > 300) seen.clear()
    queue.push({ ...ev, _at: now })
    schedule()
  } catch { /* nada */ }
}

/** Error de vista (Vue / JS). */
export function reportError({ tipo = "VISTA", clase, mensaje, stack, componente, endpoint, http_status } = {}) {
  enqueue({
    kind: "error",
    tipo: tipo === "RED" ? "RED" : "VISTA",
    clase: trunc(clase, 150),
    mensaje: trunc(mensaje, 4000),
    stack: trunc(stack, 16000),
    vista: trunc(location.pathname, 500),
    componente: trunc(componente, 200),
    endpoint: trunc(endpoint, 500),
    http_status: Number.isInteger(http_status) ? http_status : null,
  })
}

/** El interceptor de axios guarda la referencia del último error del servidor. */
export function setLastErrorRef(ref) {
  if (ref && /^ERR-[0-9A-F]{8}$/.test(ref)) lastRef = { ref, at: Date.now() }
}

/** Referencia reciente (para el toast) — se consume una sola vez. */
export function takeRecentRef() {
  if (lastRef && Date.now() - lastRef.at < REF_TTL_MS) {
    const r = lastRef.ref
    lastRef = null
    return r
  }
  return null
}

/** Llamado por showToast(…, "error"): marca el toast en el error del servidor o del navegador. */
export function markToast(message, ref) {
  try {
    const msg = trunc(message, 500)
    if (ref) enqueue({ kind: "toast", ref, toast: msg })
    const now = Date.now()
    queue.forEach(e => {
      if (e.kind === "error" && !e.toast && now - e._at < TOAST_LINK_MS) e.toast = msg
    })
  } catch { /* nada */ }
}

/** Instala los manejadores globales. */
export function installErrorReporter(app) {
  app.config.errorHandler = (err, instance, info) => {
    const comp = instance?.$options?.name || instance?.$options?.__name || instance?.$options?.__file?.split("/").pop()
    reportError({ clase: err?.name || "Error", mensaje: `${err?.message || err} (${info})`, stack: err?.stack, componente: comp })
    console.error(err)
  }
  window.addEventListener("error", (e) => {
    if (!e?.error && !e?.message) return
    // Recursos (img/script) que no cargan no son errores de código
    if (e.target && e.target !== window) return
    reportError({ clase: e.error?.name || "Error", mensaje: e.message || String(e.error), stack: e.error?.stack,
                  componente: e.filename ? `${e.filename.split("/").pop()}:${e.lineno}` : null })
  })
  window.addEventListener("unhandledrejection", (e) => {
    const r = e?.reason
    if (r?.isAxiosError || r?.name === "CanceledError" || r?.__CANCEL__) return   // ya los trata el interceptor
    reportError({ clase: r?.name || "UnhandledRejection", mensaje: r?.message || String(r), stack: r?.stack })
  })
  window.addEventListener("pagehide", () => { if (queue.length) flush() })
}
