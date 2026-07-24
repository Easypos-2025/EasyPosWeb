import { computed } from 'vue'
import { useMenuStore } from '@/stores/menuStore'

export function useParkingMode() {
  const menuStore = useMenuStore()

  const getRoutes = () => {
    const routes = []
    const flatten = (items) => {
      for (const item of items) {
        if (item.route) routes.push(item.route)
        if (item.children?.length) flatten(item.children)
      }
    }
    flatten(menuStore.menu)
    return routes
  }

  const isParkingPortero = computed(() => {
    const routes = getRoutes()
    return routes.length > 0 && routes.includes('/parking/portero') && !routes.includes('/dashboard')
  })

  const isParkingMesero = computed(() => {
    const routes = getRoutes()
    return routes.length > 0 && routes.includes('/parking/mesero') && !routes.includes('/parking/portero') && !routes.includes('/dashboard')
  })

  const isParkingRole = computed(() => isParkingPortero.value || isParkingMesero.value)

  return { isParkingPortero, isParkingMesero, isParkingRole }
}
