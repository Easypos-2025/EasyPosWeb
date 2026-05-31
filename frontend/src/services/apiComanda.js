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

export default apiComanda
