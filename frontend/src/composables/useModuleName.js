/**
 * Devuelve el nombre del módulo desde system_modules (vía menuStore),
 * según la ruta actual o una ruta explícita.
 *
 * Regla global: todos los captions de una vista deben usar este composable
 * en lugar de texto quemado, para que cambiar el nombre en BD lo actualice
 * automáticamente en toda la interfaz.
 *
 * Uso básico (ruta actual):
 *   const { moduleName } = useModuleName()
 *
 * Uso con ruta explícita (para referenciar otro módulo, ej: padre):
 *   const { moduleName } = useModuleName('/configuration/assets')
 */

import { computed } from "vue"
import { useRoute } from "vue-router"
import { useMenuStore } from "@/stores/menuStore"

function flattenMenu(items) {
  const result = []
  for (const item of (items || [])) {
    result.push(item)
    if (item.children?.length) result.push(...flattenMenu(item.children))
  }
  return result
}

export function useModuleName(routePath = null) {
  const route     = useRoute()
  const menuStore = useMenuStore()

  const moduleName = computed(() => {
    const path = routePath ?? route.path
    return flattenMenu(menuStore.menu).find(m => m.route === path)?.name ?? ""
  })

  return { moduleName }
}
