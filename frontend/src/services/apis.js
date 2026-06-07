/* =========================================
Cliente central Axios para conectar
Vue con el backend FastAPI
========================================= */

import axios from "axios"

/* =========================================
CONFIGURACIÓN BASE
========================================= */

const port = import.meta.env.VITE_API_PORT

const host =
  window.location.hostname === "localhost"
    ? "127.0.0.1"
    : window.location.hostname

//console.log("BASE URL:", import.meta.env.VITE_API_URL)

const api = axios.create({
  /*baseURL: import.meta.env.VITE_API_URL*/
  baseURL: import.meta.env.VITE_API_URL
})

/* =========================================
INTERCEPTOR REQUEST
Agrega token automáticamente
========================================= */

api.interceptors.request.use(
  (config) => {

    const token = localStorage.getItem("token")
    /*console.log("TOKEN1:", token)*/

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)


/* =========================================
INTERCEPTOR RESPONSE
Manejo global de errores
========================================= */

let _redirecting = false

api.interceptors.response.use(
  res => res,
  err => {
    const publicPaths = ["/tv/", "/pos/cocina", "/pos/comanda/login", "/pos/comanda/"]
    const isPublicPage = publicPaths.some(p => window.location.pathname.startsWith(p))

    if (err.response?.status === 401 && !_redirecting && !isPublicPage) {
      _redirecting = true
      localStorage.removeItem("token")
      localStorage.removeItem("user")

      // Importación dinámica para evitar dependencia circular con el store
      import("@/utils/toast").then(({ showToast }) => {
        showToast("Sesión expirada. Redirigiendo al inicio de sesión...", "warning")
      }).catch(() => {})

      setTimeout(() => {
        window.location.href = "/login"
      }, 1800)
    }

    return Promise.reject(err)
  }
)


/* =========================================
EXPORTACIÓN
========================================= */

export default api