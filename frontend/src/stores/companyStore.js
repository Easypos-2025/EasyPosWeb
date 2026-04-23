import { defineStore } from "pinia"
import { ref } from "vue"
import api from "@/services/apis"
import { applyTheme } from "@/utils/theme"

export const useCompanyStore = defineStore("company", () => {
  const selectedCompany = ref(null)   // { id, name, business_profile_id, business_profile_name }
  const companies       = ref([])
  const isSystem        = ref(false)

  async function loadTheme(companyId) {
    if (!companyId) return
    try {
      // 1. Colores primero — respuesta rápida, no incluye el logo (TEXT pesado)
      const colorsRes = await api.get(`/company-theme/${companyId}/colors`)
      applyTheme(colorsRes.data)

      // 2. Logo en segundo plano — no bloquea la UI
      api.get(`/company-theme/${companyId}`)
        .then(res => { if (res.data?.logo) applyTheme(res.data) })
        .catch(() => {})
    } catch {}
  }

  async function setCompany(company) {
    selectedCompany.value = company
    localStorage.setItem("selected_company", JSON.stringify(company))
    if (company?.id) await loadTheme(company.id)
  }

  async function init(userFromStorage) {
    // Llama /auth/me para obtener is_system real (no depender del localStorage)
    let meData = userFromStorage
    try {
      const res = await api.get("/auth/me/")
      meData = res.data
      // Actualizar localStorage con datos frescos (incluye is_system)
      localStorage.setItem("user", JSON.stringify({ ...userFromStorage, ...meData }))
    } catch {}

    isSystem.value = meData?.is_system ?? false

    if (isSystem.value) {
      // SYSADMIN: cargar todas las empresas
      try {
        const res = await api.get("/companies/")
        companies.value = res.data
      } catch {
        companies.value = []
      }

      // Restaurar empresa seleccionada desde localStorage
      const stored = localStorage.getItem("selected_company")
      if (stored) {
        const parsed   = JSON.parse(stored)
        const stillOk  = companies.value.find(c => c.id === parsed.id)
        selectedCompany.value = stillOk ? parsed : (companies.value[0] ?? null)
      } else {
        selectedCompany.value = companies.value[0] ?? null
      }

    } else {
      // Asociado normal: cargar empresas con el mismo NIT (puede tener varias)
      const companyNit = meData?.identification_number ?? null
      const companyId  = meData?.company_id ?? userFromStorage?.company_id

      try {
        // Intentar obtener todas las empresas del mismo NIT
        const allRes = await api.get("/companies/")
        const myNitCompany = allRes.data.find(c => c.id === companyId)
        const nit = myNitCompany?.identification_number ?? null

        if (nit) {
          companies.value = allRes.data.filter(c => c.identification_number === nit)
        } else {
          companies.value = myNitCompany ? [myNitCompany] : []
        }
      } catch {
        companies.value = []
      }

      // Empresa activa: restaurar selección o usar la del usuario
      const stored = localStorage.getItem("selected_company")
      if (stored) {
        const parsed  = JSON.parse(stored)
        const stillOk = companies.value.find(c => c.id === parsed.id)
        selectedCompany.value = stillOk ? parsed : (companies.value.find(c => c.id === companyId) ?? companies.value[0] ?? null)
      } else {
        selectedCompany.value = companies.value.find(c => c.id === companyId) ?? companies.value[0] ?? null
      }
    }

    if (selectedCompany.value?.id) {
      localStorage.setItem("selected_company", JSON.stringify(selectedCompany.value))
      await loadTheme(selectedCompany.value.id)
    }
  }

  return { selectedCompany, companies, isSystem, setCompany, init }
})
