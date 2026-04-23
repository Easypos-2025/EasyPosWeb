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

api.interceptors.response.use(
  res => res,
  err => {
  //console.log("API URL:", import.meta.env.VITE_API_URL)
    if (err.response?.status === 401) {
      localStorage.removeItem("token")
      localStorage.removeItem("user")

      //window.location.href = "/login"
    }

    return Promise.reject(err)
  }
)


/* =========================================
EXPORTACIÓN
========================================= */

export default api