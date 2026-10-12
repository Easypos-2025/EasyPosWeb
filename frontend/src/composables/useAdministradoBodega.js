// Sedes con Bodega Central: proveedores, categorías, roles (y luego usuarios y formas de pago) se crean y
// modifican solo en la bodega. Las pantallas de la sede consultan esto para quedar de solo consulta
// (el servidor también lo bloquea: 403 ADMINISTRADO_POR_BODEGA).
// empresaRef (opcional): empresa escogida en la propia pantalla (Roles de SYSADMIN); sin ella, la del topbar.
import { ref, onMounted, watch } from "vue"
import api from "@/services/apis"

export function useAdministradoBodega(empresaRef = null) {
  const administradoPor = ref(null)      // { id, nombre } de la bodega, o null

  async function consultar() {
    const cid = empresaRef ? Number(empresaRef.value) || null : null
    if (empresaRef && !cid) { administradoPor.value = null; return }
    try {
      const params = cid ? { company_id: cid } : undefined
      administradoPor.value = (await api.get("/api/bodega-central/administrado", { params })).data.administrado_por
    } catch { administradoPor.value = null }
  }

  if (empresaRef) watch(empresaRef, consultar)
  onMounted(consultar)
  return { administradoPor }
}
