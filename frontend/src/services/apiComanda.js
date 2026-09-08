import axios from "axios"

const apiComanda = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
})

apiComanda.interceptors.request.use((config) => {
  // Usa waiter_token (mesero) o el token regular del admin como fallback
  const token = localStorage.getItem("waiter_token") || localStorage.getItem("token")
  if (token) config.headers.Authorization = `Bearer ${token}`

  // Envía company_id como header para que el backend lo use cuando el JWT no lo trae
  const cid = localStorage.getItem("waiter_company_id")
  if (cid) config.headers["X-Company-Id"] = cid

  return config
})

// Si un waiter_token viejo/inválido queda guardado (ej. sesión de mesero
// expirada), bloquea silenciosamente todas las acciones de comanda del admin
// con 401, aunque su token normal siga vigente. Al recibir 401 con un
// waiter_token puesto, lo descarta y reintenta una vez con el token del admin.
apiComanda.interceptors.response.use(
  res => res,
  async err => {
    const original = err.config
    const usedWaiterToken = !!localStorage.getItem("waiter_token")
    const adminToken = localStorage.getItem("token")

    if (err.response?.status === 401 && usedWaiterToken && adminToken && !original._retriedWithAdminToken) {
      localStorage.removeItem("waiter_token")
      original._retriedWithAdminToken = true
      original.headers.Authorization = `Bearer ${adminToken}`
      return apiComanda(original)
    }

    return Promise.reject(err)
  }
)

export default apiComanda
