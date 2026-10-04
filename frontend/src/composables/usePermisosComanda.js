// Permisos del rol de quien opera la comanda / TPV (mesero con PIN o usuario).
// El servidor siempre valida; aquí solo se usan para mostrar u ocultar opciones.
import { ref } from 'vue'
import apiComanda from '@/services/apiComanda'

export function usePermisosComanda() {
  const claves = ref(new Set())
  const listo = ref(false)
  const cargar = async () => {
    try { claves.value = new Set((await apiComanda.get('/api/pos/comanda/permisos')).data || []) }
    catch { claves.value = new Set() }
    finally { listo.value = true }
  }
  cargar()
  return { listo, cargar, tiene: clave => claves.value.has(clave) }
}
