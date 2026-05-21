import { defineStore } from "pinia"
import api from "@/services/apis"

const EMPTY = { can_view: false, can_view_all: false, can_create: false, can_edit: false, can_delete: false }

export const usePermissionsStore = defineStore("permissions", {
  state: () => ({
    perms: [],       // array de { module_route, can_view, can_view_all, can_create, can_edit, can_delete }
    isSystem: false, // rol de sistema (SYSADMIN) → acceso total
    loaded: false,
  }),

  getters: {
    // Devuelve los flags de permisos para una ruta de módulo dada
    forRoute: (state) => (route) => {
      if (state.isSystem) return { can_view: true, can_view_all: true, can_create: true, can_edit: true, can_delete: true }
      return state.perms.find(p => p.module_route === route) ?? { ...EMPTY }
    },
  },

  actions: {
    async load() {
      if (this.loaded) return
      try {
        const [userRes, roleRes] = await Promise.all([
          api.get("/auth/me/"),
          // role_id se obtiene del primer request
        ])
        const roleId = userRes.data.role_id
        this.isSystem = !!userRes.data.is_system
        if (!this.isSystem) {
          const permsRes = await api.get(`/roles/${roleId}/modules/`)
          this.perms = permsRes.data
        }
        this.loaded = true
      } catch (e) {
        console.error("Error cargando permisos", e)
      }
    },

    reset() {
      this.perms = []
      this.isSystem = false
      this.loaded = false
    },
  },
})
