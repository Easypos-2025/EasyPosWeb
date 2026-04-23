import axios from "axios"

const API_URL = "http://127.0.0.1:8000/auth"

// =====================================
// LOGIN
// =====================================
export const login = async (email, password) => {
  try {
    // 1. Login
    const response = await axios.post(`${API_URL}/login`, { 
      email,
      password
    })

    const token = response.data.access_token

    // Guardar token
    localStorage.setItem("token", token)

    // 2. Obtener usuario real
    const meResponse = await axios.get(`${API_URL}/me`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })

    // 3. Guardar usuario completo
    localStorage.setItem("user", JSON.stringify(meResponse.data))

    return meResponse.data

  } catch (error) {
    throw error
  }
}