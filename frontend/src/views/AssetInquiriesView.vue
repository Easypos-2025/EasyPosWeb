<template>
  <div class="p-3">

    <!-- KPI BAR -->
    <div class="kpi-bar mt-3">
      <div class="kpi-card">
        <span class="kpi-val">{{ kpis.total }}</span>
        <span class="kpi-lbl">Total consultas</span>
      </div>
      <div class="kpi-card kpi-green">
        <span class="kpi-val">{{ kpis.confirmed }}</span>
        <span class="kpi-lbl">Confirmadas</span>
      </div>
      <div class="kpi-card kpi-orange">
        <span class="kpi-val">{{ kpis.pending }}</span>
        <span class="kpi-lbl">Pendientes</span>
      </div>
    </div>

    <!-- FILTROS -->
    <div class="card p-3 mt-3">
      <div class="row g-2 align-items-end">
        <div class="col-md-3 col-12">
          <input v-model="search" type="text" class="form-control" placeholder="Buscar nombre, email, teléfono..." />
        </div>
        <div class="col-md-3 col-6">
          <select v-model="filterAsset" class="form-select">
            <option value="">Todos los activos</option>
            <option v-for="a in assets" :key="a.id" :value="a.id">
              {{ a.list_code ? `#${a.list_code} — ` : '' }}{{ a.name }}
            </option>
          </select>
        </div>
        <div class="col-md-2 col-6">
          <select v-model="filterStatus" class="form-select">
            <option value="">Todos los estados</option>
            <option value="confirmed">Confirmadas</option>
            <option value="pending">Pendientes</option>
            <option value="expired">Expiradas</option>
          </select>
        </div>
        <div class="col-md-2 col-6">
          <select v-model="filterInterest" class="form-select">
            <option value="">Todos los intereses</option>
            <option value="arriendo">Arriendo</option>
            <option value="compra">Compra</option>
            <option value="info">Información</option>
          </select>
        </div>
        <div class="col-md-2 col-6 text-end">
          <button class="btn btn-outline-secondary btn-sm" @click="load">
            <i class="bi bi-arrow-clockwise"></i> Actualizar
          </button>
        </div>
      </div>
    </div>

    <!-- TABLA DESKTOP -->
    <div class="card p-3 mt-3 table-responsive desktop-table">
      <table class="table table-hover align-middle">
        <thead>
          <tr>
            <th>Activo</th>
            <th>Interesado</th>
            <th>Contacto</th>
            <th>Interés</th>
            <th>Estado</th>
            <th>Fecha</th>
            <th style="width:100px; white-space:nowrap">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="inq in filtered" :key="inq.id" class="row-clickable" @click="openDetail(inq)">
            <td>
              <div class="fw-600">{{ inq.asset_name }}</div>
              <span v-if="inq.list_code" class="code-sm">#{{ inq.list_code }}</span>
            </td>
            <td>
              <div class="fw-600">{{ inq.name }}</div>
            </td>
            <td>
              <div class="contact-line">
                <a :href="`tel:${inq.phone}`" @click.stop class="contact-link phone-link">
                  <i class="bi bi-telephone-fill"></i> {{ inq.phone }}
                </a>
              </div>
              <div class="contact-line">
                <a :href="`mailto:${inq.email}`" @click.stop class="contact-link email-link">
                  <i class="bi bi-envelope-fill"></i> {{ inq.email }}
                </a>
              </div>
            </td>
            <td>
              <span :class="['interest-badge', `interest-${inq.interest}`]">
                {{ inq.interest_label }}
              </span>
            </td>
            <td>
              <span :class="['status-badge', `status-${inq.status}`]">
                {{ inq.status_label }}
              </span>
            </td>
            <td class="text-muted small">{{ fmtDate(inq.confirmed_at || inq.created_at) }}</td>
            <td style="white-space:nowrap" @click.stop>
              <button class="btn btn-sm btn-outline-primary me-1" @click="openDetail(inq)" title="Ver detalle">
                <i class="bi bi-eye"></i>
              </button>
              <button class="btn btn-sm btn-outline-danger" @click="handleDelete(inq)" title="Eliminar">
                <i class="bi bi-trash"></i>
              </button>
            </td>
          </tr>
          <tr v-if="filtered.length === 0">
            <td colspan="7" class="text-center text-muted py-4">Sin consultas registradas</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- TARJETAS MÓVIL -->
    <div class="mobile-list mt-3">
      <div v-for="inq in filtered" :key="inq.id" class="inq-card" @click="openDetail(inq)">
        <div class="inq-card-header">
          <div>
            <div class="fw-600">{{ inq.name }}</div>
            <div class="text-muted small">{{ inq.asset_name }}<span v-if="inq.list_code"> #{{ inq.list_code }}</span></div>
          </div>
          <div class="d-flex flex-column align-items-end gap-1">
            <span :class="['status-badge', `status-${inq.status}`]">{{ inq.status_label }}</span>
            <span :class="['interest-badge', `interest-${inq.interest}`]">{{ inq.interest_label }}</span>
          </div>
        </div>
        <div class="inq-card-contact">
          <a :href="`tel:${inq.phone}`" @click.stop class="contact-link phone-link">
            <i class="bi bi-telephone-fill"></i> {{ inq.phone }}
          </a>
          <a :href="`mailto:${inq.email}`" @click.stop class="contact-link email-link">
            <i class="bi bi-envelope-fill"></i> {{ inq.email }}
          </a>
        </div>
        <div class="inq-card-footer">
          <span class="text-muted small">{{ fmtDate(inq.confirmed_at || inq.created_at) }}</span>
        </div>
      </div>
      <div v-if="filtered.length === 0" class="mobile-empty">
        <i class="bi bi-chat-dots" style="font-size:28px;display:block;margin-bottom:8px"></i>
        Sin consultas registradas
      </div>
    </div>

    <!-- MODAL DETALLE -->
    <div v-if="selected" class="modal-overlay" @click.self="selected = null">
      <div class="detail-modal">
        <div class="detail-modal-header">
          <h2><i class="bi bi-person-lines-fill"></i> Detalle de consulta</h2>
          <button class="btn-close-sm" @click="selected = null"><i class="bi bi-x-lg"></i></button>
        </div>

        <div class="detail-body">

          <!-- Activo -->
          <div class="detail-section">
            <div class="detail-section-title">Activo consultado</div>
            <div class="detail-row">
              <span class="detail-label">Nombre</span>
              <span class="detail-val fw-600">{{ selected.asset_name }}</span>
            </div>
            <div v-if="selected.list_code" class="detail-row">
              <span class="detail-label">Código Lista</span>
              <span class="detail-val"><span class="code-sm">#{{ selected.list_code }}</span></span>
            </div>
          </div>

          <!-- Interesado -->
          <div class="detail-section">
            <div class="detail-section-title">Datos del interesado</div>
            <div class="detail-row">
              <span class="detail-label">Nombre</span>
              <span class="detail-val fw-600">{{ selected.name }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Teléfono</span>
              <a :href="`tel:${selected.phone}`" class="contact-link phone-link detail-val">
                <i class="bi bi-telephone-fill"></i> {{ selected.phone }}
              </a>
            </div>
            <div class="detail-row">
              <span class="detail-label">Email</span>
              <a :href="`mailto:${selected.email}`" class="contact-link email-link detail-val">
                <i class="bi bi-envelope-fill"></i> {{ selected.email }}
              </a>
            </div>
            <div class="detail-row">
              <span class="detail-label">Interés</span>
              <span :class="['interest-badge', `interest-${selected.interest}`]">{{ selected.interest_label }}</span>
            </div>
            <div v-if="selected.message" class="detail-row align-start">
              <span class="detail-label">Mensaje</span>
              <span class="detail-val detail-message">{{ selected.message }}</span>
            </div>
          </div>

          <!-- Estado y fechas -->
          <div class="detail-section">
            <div class="detail-section-title">Estado y fechas</div>
            <div class="detail-row">
              <span class="detail-label">Estado</span>
              <span :class="['status-badge', `status-${selected.status}`]">{{ selected.status_label }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Enviada</span>
              <span class="detail-val">{{ fmtDate(selected.created_at) }}</span>
            </div>
            <div v-if="selected.confirmed_at" class="detail-row">
              <span class="detail-label">Confirmada</span>
              <span class="detail-val">{{ fmtDate(selected.confirmed_at) }}</span>
            </div>
          </div>

        </div>

        <!-- Botones de acción rápida -->
        <div class="detail-footer">
          <a :href="`tel:${selected.phone}`" class="btn btn-success">
            <i class="bi bi-telephone-fill"></i> Llamar
          </a>
          <a :href="`https://wa.me/${selected.phone.replace(/\D/g,'')}`" target="_blank" class="btn btn-whatsapp">
            <i class="bi bi-whatsapp"></i> WhatsApp
          </a>
          <a :href="`mailto:${selected.email}`" class="btn btn-primary">
            <i class="bi bi-envelope-fill"></i> Email
          </a>
          <button class="btn btn-outline-danger" @click="handleDelete(selected)">
            <i class="bi bi-trash"></i>
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import { useModuleName } from "@/composables/useModuleName"

useModuleName()

const inquiries     = ref([])
const assets        = ref([])
const kpis          = ref({ total: 0, confirmed: 0, pending: 0 })
const search        = ref("")
const filterAsset   = ref("")
const filterStatus  = ref("")
const filterInterest = ref("")
const selected      = ref(null)

const filtered = computed(() =>
  inquiries.value.filter(i => {
    const q = search.value.toLowerCase()
    const matchSearch   = !q || i.name.toLowerCase().includes(q) ||
                          i.email.toLowerCase().includes(q) || i.phone.includes(q)
    const matchAsset    = !filterAsset.value   || i.asset_id === filterAsset.value
    const matchStatus   = !filterStatus.value  || i.status   === filterStatus.value
    const matchInterest = !filterInterest.value || i.interest === filterInterest.value
    return matchSearch && matchAsset && matchStatus && matchInterest
  })
)

function fmtDate(d) {
  if (!d) return "—"
  return new Date(d).toLocaleString("es-CO", { dateStyle: "short", timeStyle: "short" })
}

async function load() {
  try {
    const [iqRes, kpiRes, aRes] = await Promise.all([
      api.get("/asset-inquiries/"),
      api.get("/asset-inquiries/kpis"),
      api.get("/assets/"),
    ])
    inquiries.value = iqRes.data
    kpis.value      = kpiRes.data
    assets.value    = aRes.data
  } catch {
    showToast("Error cargando consultas", "error")
  }
}

function openDetail(inq) { selected.value = inq }

async function handleDelete(inq) {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar consulta de "${inq.name}"?`,
    text: "Esta acción no se puede deshacer.",
    icon: "warning", showCancelButton: true,
    confirmButtonText: "Sí, eliminar", cancelButtonText: "Cancelar",
    confirmButtonColor: "#ef4444",
  })
  if (!isConfirmed) return
  try {
    await api.delete(`/asset-inquiries/${inq.id}`)
    showToast("Consulta eliminada", "success")
    selected.value = null
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error eliminando", "error")
  }
}

onMounted(load)
</script>

<style scoped>
/* KPI */
.kpi-bar { display: flex; gap: 12px; flex-wrap: wrap; }
.kpi-card {
  flex: 1; min-width: 110px; background: #fff; border-radius: 12px;
  padding: 14px 16px; box-shadow: 0 1px 6px rgba(0,0,0,.07);
  display: flex; flex-direction: column; gap: 2px;
}
.kpi-val { font-size: 28px; font-weight: 800; color: #1e293b; }
.kpi-lbl { font-size: 12px; color: #64748b; font-weight: 500; }
.kpi-green .kpi-val { color: #10b981; }
.kpi-orange .kpi-val { color: #f59e0b; }

/* Table */
.fw-600 { font-weight: 600; }
.code-sm { font-size: 11px; font-weight: 700; background: #f1f5f9; color: #475569; padding: 1px 7px; border-radius: 6px; }
.row-clickable { cursor: pointer; }
.row-clickable:hover td { background: #f8fafc; }

/* Contact links */
.contact-line { margin-bottom: 2px; }
.contact-link { display: inline-flex; align-items: center; gap: 5px; font-size: 13px; text-decoration: none; font-weight: 500; border-radius: 6px; padding: 2px 6px; transition: background .15s; }
.phone-link { color: #10b981; }
.phone-link:hover { background: #f0fdf4; }
.email-link { color: #3b82f6; }
.email-link:hover { background: #eff6ff; }

/* Badges */
.interest-badge, .status-badge {
  display: inline-block; font-size: 11px; font-weight: 700;
  padding: 3px 10px; border-radius: 20px; white-space: nowrap;
}
.interest-arriendo { background: #eff6ff; color: #1e40af; }
.interest-compra   { background: #f0fdf4; color: #15803d; }
.interest-info     { background: #f5f3ff; color: #6d28d9; }
.status-confirmed  { background: #f0fdf4; color: #15803d; }
.status-pending    { background: #fefce8; color: #92400e; }
.status-expired    { background: #f8fafc; color: #94a3b8; }

/* Responsive */
.mobile-list  { display: none; }
.mobile-empty { padding: 40px; text-align: center; color: #94a3b8; font-size: 14px; }

@media (max-width: 768px) {
  .desktop-table { display: none; }
  .mobile-list   { display: flex; flex-direction: column; gap: 10px; }

  .inq-card { background: #fff; border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,.08); padding: 14px 16px; cursor: pointer; }
  .inq-card-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; margin-bottom: 10px; }
  .inq-card-contact { display: flex; flex-direction: column; gap: 4px; margin-bottom: 8px; }
  .inq-card-footer { padding-top: 8px; border-top: 1px solid #f1f5f9; }
}

/* Detail modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 16px; }
.detail-modal { background: #fff; border-radius: 16px; width: 520px; max-width: 100%; max-height: 92vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,.2); }
.detail-modal-header { display: flex; align-items: center; justify-content: space-between; padding: 18px 24px 14px; border-bottom: 1px solid #f1f5f9; flex-shrink: 0; }
.detail-modal-header h2 { font-size: 16px; font-weight: 700; color: #1e293b; margin: 0; display: flex; align-items: center; gap: 8px; }
.detail-modal-header .bi { color: #3b82f6; }
.btn-close-sm { background: none; border: none; font-size: 18px; cursor: pointer; color: #94a3b8; border-radius: 6px; padding: 4px 8px; }
.btn-close-sm:hover { background: #f1f5f9; }

.detail-body { padding: 16px 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 16px; }
.detail-section { display: flex; flex-direction: column; gap: 8px; }
.detail-section-title { font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: .6px; border-bottom: 1px solid #f1f5f9; padding-bottom: 4px; }
.detail-row { display: flex; align-items: center; gap: 12px; }
.detail-row.align-start { align-items: flex-start; }
.detail-label { font-size: 13px; color: #64748b; min-width: 90px; flex-shrink: 0; }
.detail-val { font-size: 14px; color: #1e293b; }
.detail-message { background: #f8fafc; border-radius: 8px; padding: 8px 12px; font-size: 13px; color: #475569; line-height: 1.5; white-space: pre-wrap; flex: 1; }

.detail-footer { display: flex; gap: 8px; padding: 14px 24px 18px; border-top: 1px solid #f1f5f9; flex-wrap: wrap; flex-shrink: 0; }
.detail-footer .btn { flex: 1; min-width: 80px; display: flex; align-items: center; justify-content: center; gap: 6px; }
.btn-whatsapp { background: #25d366; color: #fff; border: none; border-radius: 8px; padding: 7px 16px; font-weight: 600; cursor: pointer; text-decoration: none; font-size: 14px; }
.btn-whatsapp:hover { background: #1ebe5d; color: #fff; }
</style>
