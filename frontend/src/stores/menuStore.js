import { defineStore } from "pinia"
import api from "@/services/apis"
//import { useAuthStore } from "@/stores/authStore" // 🔥 IMPORTANTE

export const useMenuStore = defineStore("menu", {

  state: () => ({
    menu: [],        // 🔥 sidebar (NO tocar)
    menuProfile: []  // 🔥 sysadmin (NO tocar)
  }),

  actions: {

    /* =========================================
    LOAD SIDEBAR
    companyId: opcional — si se pasa carga el menú
    de esa empresa (usado por SYSADMIN al cambiar empresa)
    ========================================= */
    async loadMenu(companyId = null) {
      try {
        const params = companyId ? { company_id: companyId } : {}
        const res = await api.get("/menu/my-menu/", { params })
        this.menu = this.buildTree(res.data)
      } catch (error) {
        console.error("Error cargando menú:", error)
        this.menu = []
      }
    },


    /* =========================================
    REORDER (DRAG & DROP)
    ========================================= */
    async reorderModules(payload) {

      try {

        //console.log("ENVIANDO AL BACK:", payload) // 👈

        await api.put("/business-profile-module/reorder/", payload)

        //console.log("GUARDADO OK") // 👈


        // 🔥 RECARGAR SIDEBAR (YA CON PARAM CORRECTO)
        await this.loadMenu()

      } catch (error) {
        console.error("Error reordenando módulos", error)
      }
    },

    /* =========================================
    BUILD TREE (NO TOCAR)
    ========================================= */
    buildTree(items) {

      const map = {}
      const roots = []

      // 🔥 indexar
      items.forEach(item => {
        map[item.id] = { ...item, children: [] }
      })

      // 🔥 jerarquía
      items.forEach(item => {
        if (item.parent_id) {
          if (map[item.parent_id]) {
            map[item.parent_id].children.push(map[item.id])
          }
        } else {
          roots.push(map[item.id])
        }
      })

      return roots
    }

  }

})