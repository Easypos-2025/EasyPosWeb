<template>
  <div class="sysads-root">

    <!-- KPI Bar -->
    <div class="kpi-bar">
      <div class="kpi-card" v-for="k in kpis" :key="k.label">
        <i :class="`bi ${k.icon}`" :style="`color:${k.color}`"></i>
        <div class="kpi-info">
          <span class="kpi-val">{{ summary[k.key] ?? 0 }}</span>
          <span class="kpi-lbl">{{ k.label }}</span>
        </div>
      </div>
      <div class="kpi-card kpi-income">
        <i class="bi bi-cash-coin" style="color:#10b981"></i>
        <div class="kpi-info">
          <span class="kpi-val">{{ fmtPrice(totalVerifiedIncome) }}</span>
          <span class="kpi-lbl">Ingresos verificados (COP)</span>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs-bar">
      <button class="tab-btn" :class="{ active: tab === 'ads' }" @click="tab='ads'">
        <i class="bi bi-megaphone me-1"></i>Pautas
      </button>
      <button class="tab-btn" :class="{ active: tab === 'payments' }" @click="tab='payments'; loadPayments()">
        <i class="bi bi-receipt me-1"></i>Pagos
        <span v-if="pendingPayCount > 0" class="tab-badge">{{ pendingPayCount }}</span>
      </button>
      <button class="tab-btn" :class="{ active: tab === 'report' }" @click="tab='report'; loadReport()">
        <i class="bi bi-bar-chart-line me-1"></i>Reporte Ingresos
      </button>
    </div>

    <!-- ── TAB: Pautas ── -->
    <template v-if="tab === 'ads'">
      <div class="section-header">
        <h5 class="section-title"><i class="bi bi-megaphone-fill me-2"></i>Gestión de Pautas</h5>
        <select v-model="filterStatus" @change="loadAds" class="filter-select">
          <option value="">Todos los estados</option>
          <option value="pending">Pendientes</option>
          <option value="approved">Aprobadas</option>
          <option value="active">Activas</option>
          <option value="paused">Pausadas</option>
          <option value="expired">Expiradas</option>
          <option value="rejected">Rechazadas</option>
        </select>
      </div>

      <div class="table-wrap">
        <div v-if="loading" class="empty-state"><div class="spinner-border spinner-border-sm text-secondary me-2"></div>Cargando...</div>
        <div v-else-if="!ads.length" class="empty-state">
          <i class="bi bi-megaphone" style="font-size:2.5rem;opacity:.3"></i>
          <p class="mt-2 mb-0">Sin pautas en este estado.</p>
        </div>
        <table v-else class="ads-table">
          <thead>
            <tr>
              <th>#</th><th>Asociado</th><th>Título</th><th>Estado</th>
              <th>Perfil</th><th>Slot</th><th>Inicio</th><th>Fin</th>
              <th>Imp.</th><th>Pago</th><th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ad in ads" :key="ad.id" :class="{ 'row-pending': ad.status==='pending' }">
              <td class="td-id">{{ ad.id }}</td>
              <td class="td-company">
                <span v-if="ad.company_id === null" class="badge-externo">Externo</span>
                {{ ad.company_name || (ad.company_id === null ? '' : '—') }}
              </td>
              <td class="td-title">{{ ad.title }}</td>
              <td><span class="status-badge" :class="ad.status">{{ statusLabel(ad.status) }}</span></td>
              <td>{{ ad.target_profile_name || 'Todos' }}</td>
              <td class="td-center">{{ ad.slot_position || '—' }}</td>
              <td>{{ fmtDate(ad.start_date) }}</td>
              <td>{{ fmtDate(ad.end_date) }}</td>
              <td class="td-center">{{ ad.impressions }}</td>
              <td><span class="pay-badge" :class="latestPayStatus(ad)">{{ latestPayLabel(ad) }}</span></td>
              <td>
                <button class="btn-act btn-view" @click="openDetail(ad)" title="Gestionar">
                  <i class="bi bi-gear"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- ── TAB: Pagos ── -->
    <template v-if="tab === 'payments'">
      <div class="section-header">
        <h5 class="section-title"><i class="bi bi-receipt me-2"></i>Pagos de Pautas</h5>
        <select v-model="filterPayStatus" @change="loadPayments" class="filter-select">
          <option value="">Todos</option>
          <option value="pending">Pendientes</option>
          <option value="verified">Verificados</option>
          <option value="rejected">Rechazados</option>
        </select>
      </div>

      <div class="table-wrap">
        <div v-if="loadingPay" class="empty-state"><div class="spinner-border spinner-border-sm text-secondary me-2"></div>Cargando...</div>
        <div v-else-if="!payments.length" class="empty-state">
          <i class="bi bi-receipt" style="font-size:2.5rem;opacity:.3"></i>
          <p class="mt-2 mb-0">Sin pagos en este estado.</p>
        </div>
        <table v-else class="ads-table">
          <thead>
            <tr>
              <th>#</th><th>Asociado</th><th>Pauta</th><th>Fecha</th>
              <th>Monto</th><th>Estado</th><th>Comprobante</th><th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="pay in payments" :key="pay.id" :class="{ 'row-pending': pay.status==='pending' }">
              <td class="td-id">{{ pay.id }}</td>
              <td class="td-company">{{ pay.company_name || '—' }}</td>
              <td class="td-title">{{ pay.ad_title || '—' }}</td>
              <td>{{ fmtDate(pay.created_at?.split('T')[0]) }}</td>
              <td class="td-amount">
                <span v-if="pay.amount">{{ fmtPrice(pay.amount) }} COP</span>
                <span v-else class="text-muted">—</span>
              </td>
              <td><span class="pay-badge" :class="pay.status">{{ payStatusLabel(pay.status) }}</span></td>
              <td>
                <a v-if="pay.receipt_url" :href="pay.receipt_url" target="_blank" rel="noopener" class="btn-receipt">
                  <i class="bi bi-file-earmark-image me-1"></i>Ver
                </a>
                <span v-else class="text-muted" style="font-size:11px">Sin comprobante</span>
              </td>
              <td class="td-actions-pay">
                <template v-if="pay.status === 'pending'">
                  <button class="btn-verify" @click="verifyPaymentDirect(pay.id, 'verified')">
                    <i class="bi bi-check-circle me-1"></i>Verificar
                  </button>
                  <button class="btn-reject-pay" @click="verifyPaymentDirect(pay.id, 'rejected')">
                    <i class="bi bi-x-circle me-1"></i>Rechazar
                  </button>
                </template>
                <span v-else class="verified-badge" :class="pay.status">
                  {{ pay.status === 'verified' ? 'Verificado' : 'Rechazado' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- ── TAB: Reporte Ingresos ── -->
    <template v-if="tab === 'report'">
      <div class="section-header">
        <h5 class="section-title"><i class="bi bi-bar-chart-line me-2"></i>Reporte de Ingresos</h5>
        <div class="report-filters">
          <select v-model="reportPeriod" @change="loadReport" class="filter-select">
            <option value="day">Por día</option>
            <option value="month">Por mes</option>
            <option value="year">Por año</option>
          </select>
        </div>
      </div>

      <div class="table-wrap">
        <div v-if="loadingReport" class="empty-state"><div class="spinner-border spinner-border-sm text-secondary me-2"></div>Cargando...</div>
        <div v-else-if="!reportData.length" class="empty-state">
          <i class="bi bi-graph-up" style="font-size:2.5rem;opacity:.3"></i>
          <p class="mt-2 mb-0">Sin ingresos verificados en el período.</p>
        </div>
        <template v-else>
          <!-- Totales -->
          <div class="report-totals">
            <div class="rt-card">
              <span class="rt-val">{{ fmtPrice(reportTotal) }}</span>
              <span class="rt-lbl">Total COP</span>
            </div>
            <div class="rt-card">
              <span class="rt-val">{{ reportQty }}</span>
              <span class="rt-lbl">Pagos verificados</span>
            </div>
            <div class="rt-card">
              <span class="rt-val">{{ fmtPrice(reportAvg) }}</span>
              <span class="rt-lbl">Promedio por pauta</span>
            </div>
          </div>
          <table class="ads-table">
            <thead>
              <tr>
                <th>Período</th>
                <th class="td-right">Cantidad</th>
                <th class="td-right">Total (COP)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in reportData" :key="row.periodo">
                <td>{{ row.periodo }}</td>
                <td class="td-right">{{ row.qty }}</td>
                <td class="td-right td-money">{{ fmtPrice(row.total) }}</td>
              </tr>
            </tbody>
          </table>
        </template>
      </div>
    </template>

    <!-- MODAL: Detail / Manage -->
    <div v-if="showModal" class="modal-backdrop" @click.self="showModal=false">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="modal-title">
            <i class="bi bi-gear-fill me-2"></i>Pauta #{{ selected.id }} — {{ selected.company_name }}
          </h6>
          <button class="btn-close-modal" @click="showModal=false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-body">

          <div class="detail-grid">
            <div class="dg-row"><span class="dg-lbl">Título</span><span class="dg-val">{{ selected.title }}</span></div>
            <div class="dg-row" v-if="selected.description"><span class="dg-lbl">Descripción</span><span class="dg-val">{{ selected.description }}</span></div>
            <div class="dg-row" v-if="selected.cta_url"><span class="dg-lbl">URL destino</span>
              <a :href="selected.cta_url" target="_blank" rel="noopener" class="dg-link">{{ selected.cta_url }}</a>
            </div>
            <div class="dg-row"><span class="dg-lbl">Perfil objetivo</span><span class="dg-val">{{ selected.target_profile_name || 'Todos' }}</span></div>
            <div class="dg-row" v-if="selected.notes_to_admin"><span class="dg-lbl">Notas del asociado</span><span class="dg-val">{{ selected.notes_to_admin }}</span></div>
            <div class="dg-row"><span class="dg-lbl">Estado</span>
              <span class="status-badge" :class="selected.status">{{ statusLabel(selected.status) }}</span>
            </div>
            <div class="dg-row" v-if="selected.rejection_reason">
              <span class="dg-lbl">Motivo rechazo</span>
              <span class="dg-val" style="color:#dc2626">{{ selected.rejection_reason }}</span>
            </div>
          </div>

          <!-- Redes sociales del anunciante -->
          <template v-if="selected.social_instagram || selected.social_tiktok || selected.social_facebook || selected.social_youtube_channel || selected.social_website">
            <div class="section-lbl mt-3">Redes sociales del anunciante</div>
            <div class="social-links-row">
              <a v-if="selected.social_instagram" :href="selected.social_instagram" target="_blank" rel="noopener" class="social-link-btn instagram" title="Instagram">
                <i class="bi bi-instagram"></i>
              </a>
              <a v-if="selected.social_tiktok" :href="selected.social_tiktok" target="_blank" rel="noopener" class="social-link-btn tiktok" title="TikTok">
                <i class="bi bi-tiktok"></i>
              </a>
              <a v-if="selected.social_facebook" :href="selected.social_facebook" target="_blank" rel="noopener" class="social-link-btn facebook" title="Facebook">
                <i class="bi bi-facebook"></i>
              </a>
              <a v-if="selected.social_youtube_channel" :href="selected.social_youtube_channel" target="_blank" rel="noopener" class="social-link-btn youtube" title="YouTube">
                <i class="bi bi-youtube"></i>
              </a>
              <a v-if="selected.social_website" :href="selected.social_website" target="_blank" rel="noopener" class="social-link-btn website" title="Sitio web">
                <i class="bi bi-globe2"></i>
              </a>
            </div>
          </template>

          <!-- Piezas -->
          <div class="section-lbl mt-3">Piezas ({{ selected.pieces?.length || 0 }}/3)</div>
          <div class="pieces-preview-row">
            <template v-if="selected.pieces?.length">
              <div v-for="p in selected.pieces" :key="p.id" class="piece-card">
                <img v-if="p.piece_type === 'image'" :src="p.media_url" class="piece-media" />
                <video v-else-if="p.piece_type === 'video'" :src="p.media_url" class="piece-media" controls muted preload="metadata" />
                <div v-else-if="p.piece_type === 'youtube'" class="piece-yt">
                  <i class="bi bi-youtube"></i><span>{{ p.youtube_id }}</span>
                </div>
                <div v-else class="piece-txt">{{ p.text_content }}</div>
                <span class="piece-type-lbl">{{ p.piece_type }}</span>
              </div>
            </template>
            <div v-else class="no-pieces">Sin piezas cargadas</div>
          </div>

          <!-- Pago -->
          <div class="section-lbl mt-3">Comprobante de pago</div>
          <div v-if="selected.payments?.length">
            <div v-for="pay in selected.payments" :key="pay.id" class="pay-card">
              <div class="pay-info">
                <span>{{ fmtDate(pay.created_at?.split('T')[0]) }}</span>
                <span class="pay-badge" :class="pay.status">{{ payStatusLabel(pay.status) }}</span>
                <span v-if="pay.amount" class="pay-amount">{{ fmtPrice(pay.amount) }} COP</span>
              </div>
              <a v-if="pay.receipt_url" :href="pay.receipt_url" target="_blank" rel="noopener" class="btn-receipt">
                <i class="bi bi-file-earmark-image me-1"></i>Ver comprobante
              </a>
              <div v-if="pay.status === 'pending'" class="pay-actions">
                <button class="btn-verify" @click="verifyPayment(pay.id, 'verified')">
                  <i class="bi bi-check-circle me-1"></i>Verificar
                </button>
                <button class="btn-reject-pay" @click="verifyPayment(pay.id, 'rejected')">
                  <i class="bi bi-x-circle me-1"></i>Rechazar
                </button>
              </div>
            </div>
          </div>
          <div v-else class="no-pieces">Sin comprobante registrado</div>

          <!-- Acciones -->
          <div class="section-lbl mt-3">Acciones</div>
          <div class="action-group">
            <button v-if="selected.status === 'pending'" class="btn-action btn-approve" @click="approveAd">
              <i class="bi bi-check-circle me-1"></i>Aprobar
            </button>
            <button v-if="selected.status === 'pending'" class="btn-action btn-reject" @click="rejectOpen = !rejectOpen">
              <i class="bi bi-x-circle me-1"></i>Rechazar
            </button>
            <div v-if="rejectOpen" class="reject-form">
              <textarea v-model="rejectReason" class="form-ctrl" rows="2" placeholder="Motivo del rechazo..."></textarea>
              <div class="sub-actions">
                <button class="btn-sub-save" @click="rejectAd"><i class="bi bi-send me-1"></i>Enviar</button>
                <button class="btn-sub-cancel" @click="rejectOpen=false;rejectReason=''">Cancelar</button>
              </div>
            </div>
            <template v-if="selected.status">
              <div class="activate-form">
                <div v-if="selected.status === 'active'" class="reconfig-note">
                  <i class="bi bi-info-circle me-1"></i>
                  Pauta activa. Puedes cambiar slot, fechas o prioridad.
                </div>
                <div v-else-if="selected.status === 'pending'" class="reconfig-note" style="background:#1e3a5f;border-color:#3b82f6">
                  <i class="bi bi-lightning-charge me-1" style="color:#60a5fa"></i>
                  Activar directamente asignará slot y cambiará el estado a <strong>activa</strong>.
                </div>
                <div class="af-row">
                  <div><label class="form-lbl">Slot *</label>
                    <select v-model="activateForm.slot_position" class="form-ctrl-sm">
                      <option :value="1">Slot 1</option><option :value="2">Slot 2</option><option :value="3">Slot 3</option>
                    </select>
                  </div>
                  <div><label class="form-lbl">Prioridad</label>
                    <input v-model.number="activateForm.priority" type="number" min="0" max="10" class="form-ctrl-sm" />
                  </div>
                  <div><label class="form-lbl">Inicio</label>
                    <CustomDatePicker v-model="activateForm.start_date" />
                  </div>
                  <div><label class="form-lbl">Fin</label>
                    <CustomDatePicker v-model="activateForm.end_date" />
                  </div>
                </div>
                <button class="btn-action btn-activate" @click="activateAd">
                  <i :class="selected.status === 'active' ? 'bi bi-pencil-square' : 'bi bi-broadcast'" class="me-1"></i>
                  {{ selected.status === 'active' ? 'Reconfigurar' : 'Activar en slot' }}
                </button>
              </div>
            </template>
            <button v-if="selected.status === 'active'" class="btn-action btn-pause" @click="pauseAd">
              <i class="bi bi-pause-circle me-1"></i>Pausar
            </button>
            <button v-if="['active','approved','paused'].includes(selected.status)" class="btn-action btn-expire" @click="expireAd">
              <i class="bi bi-calendar-x me-1"></i>Marcar expirada
            </button>
          </div>

        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showModal=false">Cerrar</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import CustomDatePicker from "@/components/common/CustomDatePicker.vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"

const tab = ref("ads")

// ── Pautas ─────────────────────────────────────────────────────────────────
const ads          = ref([])
const summary      = ref({})
const loading      = ref(false)
const filterStatus = ref("")
const showModal    = ref(false)
const selected     = ref({})
const rejectOpen   = ref(false)
const rejectReason = ref("")
const activateForm = ref({ slot_position: 1, priority: 0, start_date: "", end_date: "" })

// ── Pagos ──────────────────────────────────────────────────────────────────
const payments       = ref([])
const loadingPay     = ref(false)
const filterPayStatus = ref("pending")

const pendingPayCount = computed(() => payments.value.filter(p => p.status === "pending").length)
const totalVerifiedIncome = computed(() =>
  payments.value.filter(p => p.status === "verified").reduce((s, p) => s + (p.amount || 0), 0)
)

// ── Reporte ────────────────────────────────────────────────────────────────
const reportData   = ref([])
const loadingReport = ref(false)
const reportPeriod  = ref("month")

const reportTotal = computed(() => reportData.value.reduce((s, r) => s + r.total, 0))
const reportQty   = computed(() => reportData.value.reduce((s, r) => s + r.qty,   0))
const reportAvg   = computed(() => reportQty.value ? Math.round(reportTotal.value / reportQty.value) : 0)

const kpis = [
  { key: "pending",  label: "Pendientes", icon: "bi-hourglass-split", color: "#f59e0b" },
  { key: "active",   label: "Activas",    icon: "bi-broadcast",       color: "#22c55e" },
  { key: "paused",   label: "Pausadas",   icon: "bi-pause-circle",    color: "#6b7280" },
  { key: "expired",  label: "Expiradas",  icon: "bi-calendar-x",      color: "#9ca3af" },
]

// ── Cargar datos ───────────────────────────────────────────────────────────
async function loadAds() {
  loading.value = true
  try {
    const params = filterStatus.value ? `?status=${filterStatus.value}` : ""
    const [adsRes, sumRes] = await Promise.all([
      api.get(`/ads/admin/list${params}`),
      api.get("/ads/admin/stats/summary"),
    ])
    ads.value     = adsRes.data
    summary.value = sumRes.data
  } catch {
    showToast("Error al cargar pautas", "error")
  } finally {
    loading.value = false
  }
}

async function loadPayments() {
  loadingPay.value = true
  try {
    const params = filterPayStatus.value ? `?status=${filterPayStatus.value}` : ""
    const res = await api.get(`/ads/admin/payments/list${params}`)
    payments.value = res.data
  } catch {
    showToast("Error al cargar pagos", "error")
  } finally {
    loadingPay.value = false
  }
}

async function loadReport() {
  loadingReport.value = true
  try {
    const res = await api.get(`/ads/admin/payments/report?period=${reportPeriod.value}`)
    reportData.value = res.data
  } catch {
    showToast("Error al cargar reporte", "error")
  } finally {
    loadingReport.value = false
  }
}

// ── Detail modal ───────────────────────────────────────────────────────────
function openDetail(ad) {
  selected.value = { ...ad }
  activateForm.value = {
    slot_position: ad.slot_position || 1,
    priority:      ad.priority || 0,
    start_date:    ad.start_date || "",
    end_date:      ad.end_date || "",
  }
  rejectOpen.value   = false
  rejectReason.value = ""
  showModal.value    = true
}

// ── Sync selected desde BD (ignora filtro de lista) ──────────────────────
async function syncSelected() {
  if (!selected.value?.id) return
  try {
    const res = await api.get(`/ads/admin/${selected.value.id}`)
    selected.value = { ...res.data }
    activateForm.value = {
      slot_position: res.data.slot_position || 1,
      priority:      res.data.priority      || 0,
      start_date:    res.data.start_date    || "",
      end_date:      res.data.end_date      || "",
    }
  } catch {}
}

// ── Acciones sobre pauta ───────────────────────────────────────────────────
async function approveAd() {
  const { isConfirmed } = await window.Swal.fire({
    title: "¿Aprobar esta pauta?",
    text: `"${selected.value.title}"`,
    icon: "question",
    showCancelButton: true,
    confirmButtonText: "Sí, aprobar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#16a34a"
  })
  if (!isConfirmed) return
  try {
    const res = await api.patch(`/ads/admin/${selected.value.id}/approve`)
    selected.value = { ...selected.value, ...res.data }
    showToast(res.data.status === "pending" ? "Sin cambios (ya aprobada)" : "Pauta aprobada", "success")
    await Promise.all([loadAds(), syncSelected()])
  } catch (e) { showToast(e.response?.data?.detail || "Error", "error") }
}

async function rejectAd() {
  if (!rejectReason.value.trim()) return showToast("El motivo es requerido", "warning")
  try {
    const res = await api.patch(`/ads/admin/${selected.value.id}/reject`, { reason: rejectReason.value })
    selected.value = { ...selected.value, ...res.data }
    rejectOpen.value = false
    rejectReason.value = ""
    showToast("Pauta rechazada", "success")
    await Promise.all([loadAds(), syncSelected()])
  } catch (e) { showToast(e.response?.data?.detail || "Error", "error") }
}

async function activateAd() {
  const f = activateForm.value
  if (!f.start_date || !f.end_date) return showToast("Las fechas son requeridas", "warning")
  const wasActive = selected.value.status === "active"
  try {
    const res = await api.patch(`/ads/admin/${selected.value.id}/activate`, f)
    selected.value = { ...selected.value, ...res.data }
    const isReconfig = wasActive
    showToast(
      isReconfig ? `Pauta reconfigurada en slot ${f.slot_position}` : `Pauta activada en slot ${f.slot_position}`,
      "success"
    )
    await Promise.all([loadAds(), syncSelected()])
  } catch (e) {
    showToast(e.response?.data?.detail || "Error al activar", "error")
    await Promise.all([loadAds(), syncSelected()])
  }
}

async function pauseAd() {
  const { isConfirmed } = await window.Swal.fire({
    title: "¿Pausar esta pauta?",
    text: "La pauta dejará de mostrarse hasta que la reactives.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, pausar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#d97706"
  })
  if (!isConfirmed) return
  try {
    const res = await api.patch(`/ads/admin/${selected.value.id}/pause`)
    selected.value = { ...selected.value, ...res.data }
    showToast("Pauta pausada", "success")
    await Promise.all([loadAds(), syncSelected()])
  } catch (e) { showToast(e.response?.data?.detail || "Error", "error") }
}

async function expireAd() {
  const { isConfirmed } = await window.Swal.fire({
    title: "¿Marcar como expirada?",
    text: "Esta acción no se puede deshacer desde la UI.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, expirar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: "#ef4444"
  })
  if (!isConfirmed) return
  try {
    await api.patch(`/ads/admin/${selected.value.id}/expire`)
    showToast("Pauta marcada como expirada", "success")
    await Promise.all([loadAds(), syncSelected()])
  } catch (e) { showToast(e.response?.data?.detail || "Error", "error") }
}

// ── Verificar pago (desde modal) ───────────────────────────────────────────
async function _confirmPayAction(action) {
  const isVerify = action === "verified"
  return window.Swal.fire({
    title: isVerify ? "¿Verificar este pago?" : "¿Rechazar este pago?",
    text: isVerify
      ? "El pago quedará marcado como verificado."
      : "El asociado deberá subir un nuevo comprobante.",
    icon: isVerify ? "question" : "warning",
    showCancelButton: true,
    confirmButtonText: isVerify ? "Sí, verificar" : "Sí, rechazar",
    cancelButtonText: "Cancelar",
    confirmButtonColor: isVerify ? "#16a34a" : "#ef4444"
  })
}

async function verifyPayment(payId, action) {
  const { isConfirmed } = await _confirmPayAction(action)
  if (!isConfirmed) return
  try {
    const res = await api.patch(`/ads/admin/payments/${payId}/verify`, { action })
    const idx = selected.value.payments.findIndex(p => p.id === payId)
    if (idx >= 0) selected.value.payments[idx] = res.data
    showToast(action === "verified" ? "Pago verificado" : "Pago rechazado", "success")
    await loadAds()
  } catch (e) { showToast(e.response?.data?.detail || "Error", "error") }
}

// ── Verificar pago (desde tab Pagos) ──────────────────────────────────────
async function verifyPaymentDirect(payId, action) {
  const { isConfirmed } = await _confirmPayAction(action)
  if (!isConfirmed) return
  try {
    await api.patch(`/ads/admin/payments/${payId}/verify`, { action })
    showToast(action === "verified" ? "Pago verificado" : "Pago rechazado", "success")
    await loadPayments()
    await loadAds()
  } catch (e) { showToast(e.response?.data?.detail || "Error", "error") }
}

// ── Helpers ────────────────────────────────────────────────────────────────
function latestPayStatus(ad) { return ad.payments?.[0]?.status || "none" }
function latestPayLabel(ad) {
  return { pending:"Pendiente", verified:"Verificado", rejected:"Rechazado", none:"Sin pago" }[latestPayStatus(ad)] || "—"
}
function statusLabel(s) {
  return { pending:"Pendiente", approved:"Aprobada", active:"Activa", paused:"Pausada", expired:"Expirada", rejected:"Rechazada" }[s] || s
}
function payStatusLabel(s) {
  return { pending:"Pendiente", verified:"Verificado", rejected:"Rechazado" }[s] || s
}
function fmtDate(d) {
  if (!d) return "—"
  const [y, m, dd] = d.split("-")
  return `${dd}/${m}/${y}`
}
function fmtPrice(n) {
  if (!n && n !== 0) return "0"
  return new Intl.NumberFormat("es-CO").format(Math.round(n))
}

onMounted(() => {
  loadAds()
  loadPayments()
})
</script>

<style scoped>
.sysads-root { padding: 16px; max-width: 1200px; margin: 0 auto; }

/* KPI Bar */
.kpi-bar { display: flex; gap: 12px; margin-bottom: 18px; flex-wrap: wrap; }
.kpi-card {
  flex: 1; min-width: 110px; background: var(--card-bg, #fff);
  border-radius: 10px; padding: 12px 14px;
  display: flex; align-items: center; gap: 10px;
  box-shadow: 0 1px 4px rgba(0,0,0,.08);
}
.kpi-income { min-width: 200px; }
.kpi-card .bi { font-size: 22px; flex-shrink: 0; }
.kpi-info { display: flex; flex-direction: column; }
.kpi-val  { font-size: 20px; font-weight: 800; line-height: 1; }
.kpi-lbl  { font-size: 11px; opacity: .6; }

/* Tabs */
.tabs-bar { display: flex; gap: 4px; margin-bottom: 16px; border-bottom: 2px solid rgba(0,0,0,.08); }
.tab-btn {
  background: none; border: none; border-bottom: 2px solid transparent; margin-bottom: -2px;
  padding: 8px 16px; font-size: 13px; font-weight: 600; cursor: pointer; color: inherit;
  opacity: .6; transition: opacity .15s; display: flex; align-items: center; gap: 4px;
  position: relative;
}
.tab-btn:hover { opacity: .85; }
.tab-btn.active { opacity: 1; border-bottom-color: #2563eb; color: #2563eb; }
.tab-badge {
  background: #ef4444; color: #fff; font-size: 9px; font-weight: 800;
  border-radius: 10px; padding: 1px 5px; line-height: 1.4;
}

/* Section header */
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; flex-wrap: wrap; gap: 10px; }
.section-title  { font-size: 15px; font-weight: 700; margin: 0; }
.filter-select  { border: 1px solid rgba(0,0,0,.15); border-radius: 7px; padding: 6px 10px; font-size: 13px; background: transparent; color: inherit; }
.report-filters { display: flex; gap: 8px; }

/* Table */
.table-wrap { background: var(--card-bg, #fff); border-radius: 10px; box-shadow: 0 1px 4px rgba(0,0,0,.08); overflow-x: auto; }
.empty-state { text-align: center; padding: 40px 20px; color: #9ca3af; display: flex; flex-direction: column; align-items: center; gap: 8px; }
.ads-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.ads-table th { padding: 10px 12px; background: rgba(0,0,0,.04); font-weight: 700; text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: .4px; white-space: nowrap; }
.ads-table td { padding: 10px 12px; border-top: 1px solid rgba(0,0,0,.06); vertical-align: middle; }
.row-pending { background: rgba(245,158,11,.04); }
.td-id      { font-weight: 700; opacity: .5; width: 40px; }
.td-company { font-weight: 600; max-width: 130px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.td-title   { max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.td-center  { text-align: center; }
.td-right   { text-align: right; }
.td-money   { font-weight: 700; color: #059669; }
.td-amount  { font-weight: 600; white-space: nowrap; }
.td-actions-pay { display: flex; gap: 6px; align-items: center; white-space: nowrap; }

.badge-externo {
  display: inline-block; padding: 1px 6px; border-radius: 8px; font-size: 10px; font-weight: 700;
  background: rgba(245,158,11,.18); color: #d97706; margin-right: 4px; vertical-align: middle;
}
.status-badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 700; }
.status-badge.pending  { background: rgba(245,158,11,.15); color: #d97706; }
.status-badge.approved { background: rgba(59,130,246,.15); color: #2563eb; }
.status-badge.active   { background: rgba(34,197,94,.15);  color: #16a34a; }
.status-badge.paused   { background: rgba(107,114,128,.15); color: #6b7280; }
.status-badge.expired  { background: rgba(107,114,128,.1);  color: #9ca3af; }
.status-badge.rejected { background: rgba(239,68,68,.15);  color: #dc2626; }

.pay-badge { display: inline-block; padding: 2px 7px; border-radius: 10px; font-size: 10px; font-weight: 700; }
.pay-badge.pending   { background: rgba(245,158,11,.15); color: #d97706; }
.pay-badge.verified  { background: rgba(34,197,94,.15);  color: #16a34a; }
.pay-badge.rejected  { background: rgba(239,68,68,.15);  color: #dc2626; }
.pay-badge.none      { background: rgba(0,0,0,.06);       color: #9ca3af; }

.verified-badge { font-size: 11px; font-weight: 700; }
.verified-badge.verified { color: #16a34a; }
.verified-badge.rejected { color: #dc2626; }

.btn-act  { width: 30px; height: 30px; border: none; border-radius: 7px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 14px; }
.btn-view { background: rgba(59,130,246,.1); color: #2563eb; }

.btn-receipt   { display: inline-flex; align-items: center; background: rgba(59,130,246,.1); color: #2563eb; border: none; border-radius: 6px; padding: 4px 10px; font-size: 11px; cursor: pointer; text-decoration: none; }
.btn-verify    { background: rgba(34,197,94,.15); color: #16a34a; border: none; border-radius: 6px; padding: 5px 10px; font-size: 11px; cursor: pointer; font-weight: 600; display: flex; align-items: center; }
.btn-reject-pay { background: rgba(239,68,68,.15); color: #dc2626; border: none; border-radius: 6px; padding: 5px 10px; font-size: 11px; cursor: pointer; font-weight: 600; display: flex; align-items: center; }

/* Report totals */
.report-totals { display: flex; gap: 12px; padding: 14px; flex-wrap: wrap; border-bottom: 1px solid rgba(0,0,0,.06); }
.rt-card { background: rgba(0,0,0,.04); border-radius: 8px; padding: 10px 14px; display: flex; flex-direction: column; min-width: 120px; }
.rt-val  { font-size: 18px; font-weight: 800; color: #059669; }
.rt-lbl  { font-size: 10px; opacity: .6; }

/* Modal */
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,.5); display: flex; align-items: center; justify-content: center; z-index: 3000; padding: 16px; }
.modal-box { background: var(--card-bg, #fff); border-radius: 14px; width: 100%; max-width: 680px; max-height: 90vh; overflow-y: auto; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,.3); }
.modal-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid rgba(0,0,0,.08); flex-shrink: 0; }
.modal-title  { font-size: 15px; font-weight: 700; margin: 0; }
.btn-close-modal { background: none; border: none; font-size: 16px; cursor: pointer; opacity: .5; }
.btn-close-modal:hover { opacity: 1; }
.modal-body   { padding: 16px 20px; flex: 1; overflow-y: auto; }
.modal-footer { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 20px; border-top: 1px solid rgba(0,0,0,.08); flex-shrink: 0; }
.btn-cancel { background: none; border: 1px solid rgba(0,0,0,.15); border-radius: 7px; padding: 7px 16px; font-size: 13px; cursor: pointer; }

.section-lbl { font-size: 10px; font-weight: 700; letter-spacing: .5px; text-transform: uppercase; opacity: .5; margin-bottom: 8px; }
.mt-3 { margin-top: 14px; }

.detail-grid { display: flex; flex-direction: column; gap: 6px; }
.dg-row  { display: flex; gap: 10px; font-size: 13px; }
.dg-lbl  { min-width: 130px; font-weight: 600; opacity: .6; flex-shrink: 0; }
.dg-val  { flex: 1; }
.dg-link { color: #2563eb; word-break: break-all; }

.pieces-preview-row { display: flex; gap: 10px; flex-wrap: wrap; }
.piece-card { width: 120px; background: rgba(0,0,0,.05); border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; }
.piece-media { width: 100%; height: 80px; object-fit: cover; display: block; }
.piece-yt  { height: 80px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; color: #ef4444; font-size: 24px; }
.piece-yt span { font-size: 10px; }
.piece-txt { padding: 8px; font-size: 11px; height: 80px; overflow: hidden; }
.piece-type-lbl { font-size: 9px; font-weight: 700; text-align: center; padding: 3px; opacity: .5; text-transform: uppercase; }
.no-pieces { font-size: 13px; color: #9ca3af; padding: 10px 0; }

.pay-card { background: rgba(0,0,0,.04); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px; }
.pay-info { display: flex; align-items: center; gap: 8px; font-size: 12px; margin-bottom: 8px; flex-wrap: wrap; }
.pay-amount { font-weight: 700; color: #059669; }
.pay-actions { display: flex; gap: 6px; }

.action-group { display: flex; flex-direction: column; gap: 10px; }
.btn-action   { border: none; border-radius: 8px; padding: 8px 16px; font-size: 13px; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; width: fit-content; }
.btn-approve  { background: rgba(34,197,94,.15);   color: #16a34a; }
.btn-reject   { background: rgba(239,68,68,.15);   color: #dc2626; }
.btn-activate { background: #2563eb; color: #fff; }
.btn-pause    { background: rgba(107,114,128,.15); color: #6b7280; }
.btn-expire   { background: rgba(245,158,11,.15);  color: #d97706; }

.reject-form, .activate-form { background: rgba(0,0,0,.04); border-radius: 8px; padding: 12px; display: flex; flex-direction: column; gap: 8px; }
.reconfig-note { font-size: 11px; color: #2563eb; background: rgba(37,99,235,.08); border-radius: 6px; padding: 6px 10px; }
.af-row { display: grid; grid-template-columns: repeat(4,1fr); gap: 8px; }
.form-ctrl   { width: 100%; border: 1px solid rgba(0,0,0,.15); border-radius: 6px; padding: 7px 10px; font-size: 13px; background: transparent; color: inherit; box-sizing: border-box; }
.form-ctrl:focus { outline: none; border-color: #2563eb; }
.form-ctrl-sm { width: 100%; border: 1px solid rgba(0,0,0,.15); border-radius: 6px; padding: 5px 8px; font-size: 12px; background: transparent; color: inherit; box-sizing: border-box; }
.form-lbl { font-size: 11px; font-weight: 600; display: block; margin-bottom: 3px; opacity: .65; }
.sub-actions    { display: flex; gap: 8px; }
.btn-sub-save   { background: #2563eb; color: #fff; border: none; border-radius: 6px; padding: 6px 12px; font-size: 12px; cursor: pointer; width: fit-content; display: flex; align-items: center; }
.btn-sub-cancel { background: none; border: 1px solid rgba(0,0,0,.15); border-radius: 6px; padding: 6px 12px; font-size: 12px; cursor: pointer; }
.text-muted { opacity: .4; }

.social-links-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 4px; }
.social-link-btn {
  width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center;
  justify-content: center; font-size: 16px; text-decoration: none; transition: opacity .15s;
}
.social-link-btn:hover { opacity: .8; }
.social-link-btn.instagram { background: rgba(225,48,108,.12); color: #e1306c; }
.social-link-btn.tiktok    { background: rgba(1,1,1,.08);      color: #010101; }
.social-link-btn.facebook  { background: rgba(24,119,242,.12); color: #1877f2; }
.social-link-btn.youtube   { background: rgba(255,0,0,.1);     color: #ff0000; }
.social-link-btn.website   { background: rgba(107,114,128,.1); color: #6b7280; }

@media (max-width: 768px) {
  .af-row { grid-template-columns: 1fr 1fr; }
  .kpi-bar { gap: 8px; }
  .dg-row { flex-direction: column; gap: 2px; }
  .dg-lbl { min-width: unset; }
}
@media (max-width: 576px) {
  .sysads-root { padding: 10px; }
  .af-row { grid-template-columns: 1fr; }
}
</style>
