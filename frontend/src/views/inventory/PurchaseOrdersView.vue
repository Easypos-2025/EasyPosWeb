<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1 class="page-title"><i class="bi bi-cart-plus me-2"></i>Entradas de Mercancía</h1>
        <p class="page-subtitle">Registra compras a proveedores y actualiza el stock automáticamente</p>
      </div>
      <button class="btn btn-primary" @click="openCreate"><i class="bi bi-plus-lg"></i> Nueva entrada</button>
    </div>

    <!-- KPI -->
    <div class="kpi-bar">
      <div class="kpi-card">
        <span class="kpi-num">{{ orders.length }}</span>
        <span class="kpi-label">Total</span>
      </div>
      <div class="kpi-card kpi-amber">
        <span class="kpi-num">{{ orders.filter(o => o.status === 'draft').length }}</span>
        <span class="kpi-label">Borrador</span>
      </div>
      <div class="kpi-card kpi-green">
        <span class="kpi-num">{{ orders.filter(o => o.status === 'confirmed').length }}</span>
        <span class="kpi-label">Confirmadas</span>
      </div>
    </div>

    <div class="table-card">
      <div v-if="loading" class="table-loading"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Proveedor</th>
            <th>Factura</th>
            <th class="text-center">Fecha</th>
            <th class="text-right">Total</th>
            <th class="text-center">Estado</th>
            <th class="text-center">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="o in orders" :key="o.id">
            <td class="text-muted">{{ o.id }}</td>
            <td>{{ o.supplier_name || 'Sin proveedor' }}</td>
            <td class="text-muted">{{ o.invoice_no || '—' }}</td>
            <td class="text-center text-muted">{{ fmtDate(o.order_date) }}</td>
            <td class="text-right"><strong>{{ fmtMoney(o.total_amount) }}</strong></td>
            <td class="text-center">
              <span class="estado-badge" :class="statusClass(o.status)">{{ statusLabel(o.status) }}</span>
            </td>
            <td class="text-center">
              <div class="action-row">
                <button class="btn btn-sm btn-outline-primary" @click="viewOrder(o)" title="Ver detalle"><i class="bi bi-eye"></i></button>
                <button v-if="o.status === 'draft'" class="btn btn-sm btn-outline-success" @click="confirmOrder(o)" title="Confirmar entrada y actualizar stock">
                  <i class="bi bi-check-lg"></i>
                </button>
                <button v-if="o.status === 'draft'" class="btn btn-sm btn-outline-danger" @click="cancelOrder(o)" title="Cancelar">
                  <i class="bi bi-x-lg"></i>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="orders.length === 0">
            <td colspan="7" class="text-center text-muted py-4">No hay entradas registradas</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- MODAL NUEVA ENTRADA -->
    <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false">
      <div class="modal-box modal-xl">
        <div class="mh">
          <h3><i class="bi bi-cart-plus me-2"></i>Nueva Entrada de Mercancía</h3>
          <button class="btn-x" @click="showCreate = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="mb-area">
          <div class="form-row3">
            <div class="fg">
              <label>Proveedor</label>
              <select v-model="createForm.supplier_id" class="form-select">
                <option :value="null">— Sin proveedor —</option>
                <option v-for="s in suppliers" :key="s.id" :value="s.id">{{ s.name }}</option>
              </select>
            </div>
            <div class="fg">
              <label>N° Factura / Remisión</label>
              <input v-model="createForm.invoice_no" class="form-control" placeholder="FAC-001" />
            </div>
            <div class="fg">
              <label>Fecha *</label>
              <input v-model="createForm.order_date" type="date" class="form-control" />
            </div>
          </div>
          <div class="fg">
            <label>Notas</label>
            <input v-model="createForm.notes" class="form-control" placeholder="Observaciones de la entrada..." />
          </div>

          <div class="section-divider">Insumos recibidos</div>

          <div class="items-list">
            <div v-for="(item, idx) in createForm.items" :key="idx" class="item-row">
              <div class="fg" style="flex:2">
                <label v-if="idx === 0">Insumo</label>
                <select v-model="item.supply_item_id" class="form-select">
                  <option :value="null">— Seleccionar insumo —</option>
                  <option v-for="si in supplyItems" :key="si.id" :value="si.id">
                    {{ si.name }}{{ si.code ? ' [' + si.code + ']' : '' }}
                  </option>
                </select>
              </div>
              <div class="fg" style="flex:1">
                <label v-if="idx === 0">Presentación</label>
                <input v-model="item.presentation_name" class="form-control" placeholder="Caja x24, Und…" />
              </div>
              <div class="fg" style="flex:1">
                <label v-if="idx === 0">Cantidad</label>
                <input v-model.number="item.qty" type="number" min="0" step="0.001" class="form-control" />
              </div>
              <div class="fg" style="flex:1">
                <label v-if="idx === 0">Precio unit.</label>
                <input v-model.number="item.unit_price" type="number" min="0" step="0.01" class="form-control" />
              </div>
              <div class="fg" style="flex:1">
                <label v-if="idx === 0">Subtotal</label>
                <div class="subtotal-cell">{{ fmtMoney((item.qty || 0) * (item.unit_price || 0)) }}</div>
              </div>
              <button class="btn-del" @click="removeItem(idx)" :style="{ marginTop: idx === 0 ? '22px' : '0' }">
                <i class="bi bi-trash"></i>
              </button>
            </div>
            <button class="btn btn-sm btn-outline-secondary" style="align-self:flex-start" @click="addItem">
              <i class="bi bi-plus-lg"></i> Agregar insumo
            </button>
          </div>

          <div class="total-row">
            <span>Total entrada:</span>
            <strong>{{ fmtMoney(orderTotal) }}</strong>
          </div>
        </div>
        <div class="mf">
          <button class="btn btn-secondary btn-sm" @click="showCreate = false">Cancelar</button>
          <button class="btn btn-outline-primary btn-sm" @click="submitCreate(false)" :disabled="saving">Guardar borrador</button>
          <button class="btn btn-primary btn-sm" @click="submitCreate(true)" :disabled="saving">
            <i v-if="saving" class="bi bi-arrow-repeat spin"></i>
            {{ saving ? 'Guardando...' : 'Guardar y confirmar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL VER DETALLE -->
    <div v-if="showDetail" class="modal-overlay" @click.self="showDetail = false">
      <div class="modal-box modal-xl">
        <div class="mh">
          <h3><i class="bi bi-cart-plus me-2"></i>Entrada #{{ detailOrder?.id }}</h3>
          <button class="btn-x" @click="showDetail = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="mb-area">
          <div class="detail-info">
            <div><i class="bi bi-truck me-1"></i><strong>{{ detailOrder?.supplier_name || 'Sin proveedor' }}</strong></div>
            <div><i class="bi bi-receipt me-1"></i>Factura: {{ detailOrder?.invoice_no || 'S/N' }}</div>
            <div><i class="bi bi-calendar me-1"></i>{{ fmtDate(detailOrder?.order_date) }}</div>
            <span class="estado-badge" :class="statusClass(detailOrder?.status)">{{ statusLabel(detailOrder?.status) }}</span>
          </div>
          <table class="data-table" v-if="detailItems.length">
            <thead>
              <tr>
                <th>Insumo</th>
                <th>Presentación</th>
                <th class="text-right">Cant.</th>
                <th class="text-right">Precio Unit.</th>
                <th class="text-right">Subtotal</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="i in detailItems" :key="i.id">
                <td>{{ i.supply_item_name }}</td>
                <td class="text-muted">{{ i.presentation_name || '—' }}</td>
                <td class="text-right">{{ i.qty }}</td>
                <td class="text-right">{{ fmtMoney(i.unit_price) }}</td>
                <td class="text-right"><strong>{{ fmtMoney(i.subtotal) }}</strong></td>
              </tr>
            </tbody>
          </table>
          <div class="total-row">
            <span>Total:</span>
            <strong>{{ fmtMoney(detailOrder?.total_amount) }}</strong>
          </div>
        </div>
        <div class="mf">
          <button class="btn btn-secondary btn-sm" @click="showDetail = false">Cerrar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

const orders     = ref([])
const suppliers  = ref([])
const supplyItems = ref([])
const loading    = ref(true)
const saving     = ref(false)

const showCreate = ref(false)
const createForm = ref({})

const showDetail  = ref(false)
const detailOrder = ref(null)
const detailItems = ref([])

const orderTotal = computed(() =>
  createForm.value.items?.reduce((s, i) => s + (i.qty || 0) * (i.unit_price || 0), 0) || 0
)

const STATUS_LABELS = { draft: "Borrador", confirmed: "Confirmada", cancelled: "Cancelada" }
const STATUS_CLASS  = { draft: "e-amber",  confirmed: "e-green",    cancelled: "e-red" }
function statusLabel(s) { return STATUS_LABELS[s] || s }
function statusClass(s) { return STATUS_CLASS[s] || "" }
function fmtDate(iso) { return iso ? new Date(iso).toLocaleDateString("es-CO", { day:"2-digit", month:"short", year:"numeric" }) : "—" }
function fmtMoney(v)  { return Number(v || 0).toLocaleString("es-CO", { style:"currency", currency:"COP", minimumFractionDigits:0 }) }

async function load() {
  loading.value = true
  try {
    const [or, sr, sir] = await Promise.all([
      api.get("/purchase-orders/"),
      api.get("/suppliers/"),
      api.get("/supply-items/"),
    ])
    orders.value      = or.data
    suppliers.value   = sr.data
    supplyItems.value = sir.data
  } catch { showToast("Error cargando datos", "error") }
  finally { loading.value = false }
}

function openCreate() {
  createForm.value = {
    supplier_id: null, invoice_no: "",
    order_date: new Date().toISOString().slice(0,10),
    notes: "", items: [{ supply_item_id: null, qty: 1, unit_price: 0, presentation_name: "" }]
  }
  showCreate.value = true
}

function addItem() {
  createForm.value.items.push({ supply_item_id: null, qty: 1, unit_price: 0, presentation_name: "" })
}

function removeItem(idx) {
  createForm.value.items.splice(idx, 1)
}

async function submitCreate(confirm) {
  const validItems = createForm.value.items.filter(i => i.supply_item_id && i.qty > 0)
  if (!validItems.length) { showToast("Agrega al menos un insumo con cantidad", "warning"); return }
  saving.value = true
  try {
    const payload = { ...createForm.value, items: validItems }
    const r = await api.post("/purchase-orders/", payload)
    orders.value.unshift(r.data)
    if (confirm) {
      await api.post(`/purchase-orders/${r.data.id}/confirm`)
      await load()
      showToast("Entrada confirmada — stock actualizado", "success")
    } else {
      showToast("Borrador guardado", "success")
    }
    showCreate.value = false
  } catch (e) { showToast(e.response?.data?.detail || "Error guardando", "error") }
  finally { saving.value = false }
}

async function viewOrder(o) {
  try {
    const r = await api.get(`/purchase-orders/${o.id}`)
    detailOrder.value = r.data
    detailItems.value = r.data.items || []
    showDetail.value  = true
  } catch { showToast("Error cargando detalle", "error") }
}

async function confirmOrder(o) {
  const { isConfirmed } = await window.Swal.fire({
    title: "¿Confirmar entrada?", text: "El stock de los insumos será actualizado.",
    icon: "question", showCancelButton: true, confirmButtonText: "Confirmar", cancelButtonText: "Cancelar"
  })
  if (!isConfirmed) return
  try {
    await api.post(`/purchase-orders/${o.id}/confirm`)
    await load()
    showToast("Entrada confirmada — stock actualizado", "success")
  } catch (e) { showToast(e.response?.data?.detail || "Error", "error") }
}

async function cancelOrder(o) {
  const { isConfirmed } = await window.Swal.fire({
    title: "¿Cancelar entrada?", icon: "warning",
    showCancelButton: true, confirmButtonText: "Sí, cancelar", cancelButtonText: "No"
  })
  if (!isConfirmed) return
  try {
    await api.patch(`/purchase-orders/${o.id}/cancel`)
    await load()
    showToast("Entrada cancelada", "success")
  } catch (e) { showToast(e.response?.data?.detail || "Error", "error") }
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1100px; }
.page-header    { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; gap: 12px; flex-wrap: wrap; }
.page-title     { font-size: 22px; font-weight: 700; color: #1e293b; margin: 0 0 4px; }
.page-subtitle  { font-size: 13px; color: #64748b; margin: 0; }
.kpi-bar  { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 18px; }
.kpi-card { background: #fff; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.07); padding: 12px 18px; display: flex; align-items: baseline; gap: 8px; }
.kpi-num  { font-size: 24px; font-weight: 800; color: #1e293b; }
.kpi-label { font-size: 12px; color: #94a3b8; }
.kpi-amber .kpi-num { color: #b45309; }
.kpi-green .kpi-num { color: #16a34a; }
.table-card    { background: #fff; border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,.08); overflow: hidden; }
.table-loading { padding: 40px; text-align: center; color: #94a3b8; }
.data-table    { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { background: #f8fafc; color: #475569; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: .4px; padding: 11px 12px; border-bottom: 1px solid #e2e8f0; }
.data-table td { padding: 11px 12px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: #f8fafc; }
.text-center { text-align: center; }
.text-right  { text-align: right; }
.text-muted  { color: #94a3b8; font-size: 12px; }
.py-4        { padding: 32px 0; }
.estado-badge { font-size: 10px; font-weight: 700; padding: 2px 9px; border-radius: 20px; white-space: nowrap; }
.e-amber { background: #fef3c7; color: #b45309; }
.e-green { background: #dcfce7; color: #16a34a; }
.e-red   { background: #fef2f2; color: #b91c1c; }
.action-row { display: flex; gap: 4px; justify-content: center; }
.section-divider { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .5px; color: #94a3b8; border-bottom: 1px solid #f1f5f9; padding-bottom: 4px; }
.items-list  { display: flex; flex-direction: column; gap: 8px; }
.item-row    { display: flex; gap: 8px; align-items: flex-end; }
.subtotal-cell { height: 38px; display: flex; align-items: center; font-size: 13px; font-weight: 700; color: #1e293b; white-space: nowrap; }
.btn-del { background: none; border: none; cursor: pointer; color: #ef4444; font-size: 14px; padding: 4px 8px; }
.total-row { display: flex; justify-content: flex-end; align-items: center; gap: 12px; font-size: 15px; color: #475569; padding-top: 8px; border-top: 2px solid #f1f5f9; }
.total-row strong { font-size: 18px; color: #1e293b; }
.detail-info { background: #f8fafc; border-radius: 10px; padding: 12px 16px; display: flex; flex-wrap: wrap; gap: 12px; font-size: 13px; color: #475569; align-items: center; }
.form-row3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 2000; padding: 16px; }
.modal-box     { background: #fff; border-radius: 16px; width: 100%; max-width: 540px; max-height: 90vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,.2); }
.modal-xl      { max-width: 860px; }
.mh  { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid #f1f5f9; flex-shrink: 0; }
.mh h3 { font-size: 15px; font-weight: 700; color: #1e293b; margin: 0; }
.btn-x { background: none; border: none; font-size: 16px; cursor: pointer; color: #94a3b8; }
.mb-area { padding: 18px 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; }
.mf { padding: 12px 20px 16px; display: flex; justify-content: flex-end; gap: 8px; border-top: 1px solid #f1f5f9; flex-shrink: 0; }
.fg       { display: flex; flex-direction: column; gap: 4px; }
.fg label { font-size: 13px; font-weight: 600; color: #374151; }
.form-row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.btn { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; transition: all .15s; }
.btn-primary   { background: #3b82f6; color: #fff; } .btn-primary:hover { background: #2563eb; }
.btn-primary:disabled { opacity: .6; cursor: not-allowed; }
.btn-secondary { border: 1.5px solid #e2e8f0; background: #fff; color: #64748b; }
.btn-sm { padding: 6px 12px; font-size: 12px; }
.btn-outline-primary   { background: #eff6ff; color: #1d4ed8; border: 1.5px solid #bfdbfe; }
.btn-outline-secondary { background: #f8fafc; color: #475569; border: 1.5px solid #e2e8f0; }
.btn-outline-success   { background: #f0fdf4; color: #16a34a; border: 1.5px solid #bbf7d0; }
.btn-outline-danger    { background: #fff5f5; color: #dc2626; border: 1.5px solid #fecaca; }
.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
@media (max-width: 640px) { .form-row3 { grid-template-columns: 1fr; } .item-row { flex-direction: column; } }
</style>
