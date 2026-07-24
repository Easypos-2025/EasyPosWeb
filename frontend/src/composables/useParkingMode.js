import { computed } from 'vue'

function getMenuRoutes() {
  try {
    const menu = JSON.parse(localStorage.getItem('menu') || '[]')
    const routes = []
    const flatten = (items) => {
      for (const item of items) {
        if (item.route) routes.push(item.route)
        if (item.children?.length) flatten(item.children)
      }
    }
    flatten(menu)
    return routes
  } catch { return [] }
}

export function useParkingMode() {
  // Detecta modo parking exclusivo por menú, sin depender del nombre del rol.
  // Funciona con cualquier nombre de rol (PORTERO, VIGILANTE, ENTRADA, etc.)
  const isParkingPortero = computed(() => {
    const routes = getMenuRoutes()
    if (!routes.length) return false
    const nonParking = routes.filter(r => r && !r.startsWith('/parking'))
    return nonParking.length === 0 && routes.includes('/parking/portero') && !routes.includes('/parking/mesero') && !routes.includes('/parking/caja')
  })

  const isParkingMesero = computed(() => {
    const routes = getMenuRoutes()
    if (!routes.length) return false
    const nonParking = routes.filter(r => r && !r.startsWith('/parking'))
    return nonParking.length === 0 && routes.includes('/parking/mesero') && !routes.includes('/parking/portero') && !routes.includes('/parking/caja')
  })

  const isParkingRole = computed(() => isParkingPortero.value || isParkingMesero.value)

  return { isParkingPortero, isParkingMesero, isParkingRole }
}
