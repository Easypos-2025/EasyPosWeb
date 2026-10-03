// Permisos especiales del rol del usuario (Roles → Control de Acceso).
// El servidor siempre valida; aquí solo se usan para mostrar u ocultar opciones.
// Se guardan por sesión (token): otro usuario en la misma pestaña vuelve a consultarlos.
import { ref, computed } from 'vue'
import api from '@/services/apis'

const claves = ref(null)
let tokenCargado = null
let cargando = null

const tokenActual = () => { try { return localStorage.getItem('token') } catch { return null } }

export async function cargarPermisos() {
  const tk = tokenActual()
  if (claves.value && tk === tokenCargado) return claves.value
  if (!cargando) {
    cargando = api.get('/roles/access/me')
      .then(r => { claves.value = new Set(r.data || []); tokenCargado = tk })
      .catch(() => { claves.value = new Set(); tokenCargado = tk })
      .finally(() => { cargando = null })
  }
  await cargando
  return claves.value
}

export function usePermisos() {
  if (tokenActual() !== tokenCargado) claves.value = null
  cargarPermisos()
  const tiene = clave => !!claves.value?.has(clave)
  return {
    listo: computed(() => claves.value !== null),
    tiene,
    anteriores: computed(() => tiene('consultar_anteriores')),
    periodos: computed(() => tiene('ver_periodos')),
  }
}
