import { ref, onMounted } from "vue"
import api from "@/services/apis"
import { useCompanyStore } from "@/stores/companyStore"

const fmt = (v) =>
  new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(v)

export function useVentasKpis() {
  const companyStore = useCompanyStore()
  const loading = ref(true)

  const kpis = ref([
    { icon: "bi-cash-coin",       label: "Ventas hoy",      value: "—" },
    { icon: "bi-receipt",         label: "Facturas",        value: "—" },
    { icon: "bi-file-text",       label: "Recibos",         value: "—" },
    { icon: "bi-graph-up-arrow",  label: "Ticket promedio", value: "—" },
  ])

  async function cargar() {
    loading.value = true
    try {
      const cid = companyStore.selectedCompany?.id
      const params = cid ? `?company_id=${cid}` : ""
      const { data } = await api.get(`/api/pos-dashboard/kpis${params}`)

      const totalVentas = (data.ventas_facturas?.total || 0) + (data.ventas_recibos?.total || 0)
      const totalTx     = (data.ventas_facturas?.count || 0) + (data.ventas_recibos?.count || 0)
      const ticket      = totalTx > 0 ? Math.round(totalVentas / totalTx) : 0

      kpis.value = [
        { icon: "bi-cash-coin",      label: "Ventas hoy",      value: fmt(totalVentas) },
        { icon: "bi-receipt",        label: "Facturas",        value: data.ventas_facturas?.count ?? 0 },
        { icon: "bi-file-text",      label: "Recibos",         value: data.ventas_recibos?.count  ?? 0 },
        { icon: "bi-graph-up-arrow", label: "Ticket promedio", value: ticket > 0 ? fmt(ticket) : "—" },
      ]
    } catch {
      // mantiene los "—" si falla la carga
    } finally {
      loading.value = false
    }
  }

  onMounted(cargar)

  return { kpis, loading, cargar }
}
