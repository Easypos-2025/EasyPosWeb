import axios from "axios"

const API = "http://127.0.0.1:8000"

export const getUserModules = async (userId) => {
  const response = await axios.get(`${API}/users/${userId}/modules`)
  return response.data
}