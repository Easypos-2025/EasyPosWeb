import { ref, watch, onMounted } from "vue"
import api from "@/services/apis"
import { useCompanyStore } from "@/stores/companyStore"

const hoy = () =>
  new Intl.DateTimeFormat("en-CA", { timeZone: "America/Bogota" }).format(new Date())

const fmtCOP = new Intl.NumberFormat("es-CO", {
  style: "currency", currency: "COP",
  minimumFractionDigits: 0, maximumFractionDigits: 0,
})
const fmt = (v) => fmtCOP.format(v || 0)

const EMPTY = [
  { icon: "bi-receipt-cutoff", label: "Ventas Facturas",   value: "—" },
  { icon: "bi-journal-text",   label: "Ventas Recibos",    value: "—" },
  { icon: "bi-graph-up-arrow", label: "Total Fact+Rec",    value: "—" },
  { icon: "bi-table",          label: "Comandas Abiertas", value: "—" },
  { icon: "bi-globe",          label: "Plataforma",        value: "—" },
]

// Fecha del dashboard, compartida: la franja de KPIs y el tablero de la Bodega Central usan la misma
export const fechaDashboard = ref(hoy())

export function useVentasKpis() {
  const companyStore = useCompanyStore()
  const loading  = ref(true)
  const fechaKpi = fechaDashboard
  const kpis     = ref([...EMPTY])

  async function cargar() {
    loading.value = true
    try {
      const cid = companyStore.selectedCompany?.id
      const { data } = await api.get("/api/pos-dashboard/kpis", {
        params: { fecha: fechaKpi.value, ...(cid ? { company_id: cid } : {}) },
      })
      // Bodega Central: Facturas, Recibos y Total son la suma de todas las sedes del grupo
      if (companyStore.billingConfig?.has_bodega_central == 1) {
        try {
          const t = (await api.get("/api/bodega-central/tablero", { params: { fecha: fechaKpi.value } })).data.totales
          data.ventas_facturas = { count: t.facturas.cantidad, total: t.facturas.total }
          data.ventas_recibos  = { count: t.recibos.cantidad,  total: t.recibos.total }
        } catch { /* sin acceso a la bodega: se dejan las de la empresa */ }
      }
      const totalFactRec = (data.ventas_facturas?.total || 0) + (data.ventas_recibos?.total || 0)
      const countFactRec = (data.ventas_facturas?.count || 0) + (data.ventas_recibos?.count || 0)
      kpis.value = [
        { icon: "bi-receipt-cutoff", label: `Facturas (${data.ventas_facturas?.count ?? 0})`,   value: fmt(data.ventas_facturas?.total) },
        { icon: "bi-journal-text",   label: `Recibos (${data.ventas_recibos?.count ?? 0})`,     value: fmt(data.ventas_recibos?.total) },
        { icon: "bi-graph-up-arrow", label: `Total (${countFactRec})`,                           value: fmt(totalFactRec) },
        { icon: "bi-table",          label: `Abiertas (${data.comandas_abiertas?.count ?? 0})`, value: fmt(data.comandas_abiertas?.total) },
        { icon: "bi-globe",          label: `Domicilio (${data.plataforma?.count ?? 0})`,       value: fmt(data.plataforma?.total) },
      ]
    } catch {
      kpis.value = [...EMPTY]
    } finally {
      loading.value = false
    }
  }

  watch(fechaKpi, cargar)
  watch(() => companyStore.billingConfig?.has_bodega_central, (v, antes) => { if (v != antes) cargar() })
  onMounted(cargar)

  return { kpis, loading, fechaKpi, cargar }
}
