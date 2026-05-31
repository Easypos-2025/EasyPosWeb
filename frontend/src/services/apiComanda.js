import axios from "axios"

const apiComanda = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
})

apiComanda.interceptors.request.use((config) => {
  const token = localStorage.getItem("waiter_token")
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export default apiComanda
