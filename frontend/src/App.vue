<script>
/*
========================================================
APP PRINCIPAL DEL DASHBOARD (SIMPLIFICADO)
App.vue SOLO renderiza las rutas.
========================================================
*/

import { onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import api from "@/services/apis"
import { applyTheme } from "@/utils/theme"
import EfectivoNoConfiguradoModal from "@/components/common/EfectivoNoConfiguradoModal.vue"
import { revisarEfectivo } from "@/utils/efectivoAviso"

export default {
  components: { EfectivoNoConfiguradoModal },
  setup() {
    // Forma de pago EFECTIVO (Default + Activa): se revisa al entrar y al navegar (máx. cada 2 min);
    // en Formas de Pago no se abre la ventana (es donde se corrige).
    const router = useRouter()
    router.afterEach(to => {
      const libre = ["/payment-types", "/login", "/tv/", "/pos/cocina"].some(p => to.path.startsWith(p))
      if (!libre) revisarEfectivo()
    })

    const isReady = ref(false)

    onMounted(async () => {
      try {
        // 🔥 1. CARGAR CACHE INMEDIATO
        const cachedTheme = localStorage.getItem("app_theme")

        if (cachedTheme) {
          try {
            const parsed = JSON.parse(cachedTheme)
            applyTheme(parsed)
          } catch (e) {
            console.warn("Cache inválido")
          }
        }

        // 🔥 2. CONTINUAR NORMAL
        const user = JSON.parse(localStorage.getItem("user"))
        const token = localStorage.getItem("token")
        //console.log("CARGANDO THEME GLOBAL1:", localStorage.getItem("token"))
        // 🔥 BLOQUEO TOTAL SI NO HAY TOKEN
        if (!token || !user || !user.company_id) {
          isReady.value = true
          return
        }
        //console.log("CARGANDO THEME GLOBAL2:", !user.company_id)
        const res = await api.get(`/company-theme/${user.company_id}`)
        const theme = res.data
        //console.log("CARGANDO THEME GLOBAL3:", res.data)
        if (theme) {
          applyTheme({
            topbar_color: theme.topbar_color,
            sidebar_color: theme.sidebar_color,
            bg_color: theme.bg_color,
            logo: theme.logo,
            font_size: theme.font_size,
            font_color: theme.font_family
          })
        }

      } catch (error) {
        console.error("ERROR CARGANDO THEME GLOBAL:", error)

      } finally {
        isReady.value = true // 🔥 evita el flash
      }
    })

    return {
      isReady
    }
  }
}
</script>

<template>
  <!-- =================================================
  VISTA PRINCIPAL DE RUTAS
  ================================================= -->
  <router-view v-if="isReady" />
  <EfectivoNoConfiguradoModal />
</template>
