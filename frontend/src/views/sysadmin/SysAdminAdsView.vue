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
    </div>

    <!-- Header + filtros -->
    <div class="section-header">
      <h5 class="section-title"><i class="bi bi-megaphone-fill me-2"></i>Gestión de Pautas</h5>
      <div class="filter-wrap">
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
    </div>

    <!-- Tabla -->
    <div class="table-wrap">
      <div v-if="loading" class="empty-state">
        <div class="spinner-border spinner-border-sm text-secondary me-2"></div>Cargando...
      </div>
      <div v-else-if="!ads.length" class="empty-state">
        <i class="bi bi-megaphone" style="font-size:2.5rem;opacity:.3"></i>
        <p class="mt-2 mb-0">Sin pautas en este estado.</p>
      </div>
      <table v-else class="ads-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Asociado</th>
            <th>Título</th>
            <th>Estado</th>
            <th>Perfil</th>
            <th>Slot</th>
            <th>Inicio</th>
            <th>Fin</th>
            <th>Imp.</th>
            <th>Pago</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ad in ads" :key="ad.id" :class="{ 'row-pending': ad.status==='pending' }">
            <td class="td-id">{{ ad.id }}</td>
            <td class="td-company">{{ ad.company_name || '—' }}</td>
            <td class="td-title">{{ ad.title }}</td>
            <td><span class="status-badge" :class="ad.status">{{ statusLabel(ad.status) }}</span></td>
            <td>{{ ad.target_profile_name || 'Todos' }}</td>
            <td class="td-center">{{ ad.slot_position || '—' }}</td>
            <td>{{ fmtDate(ad.start_date) }}</td>
            <td>{{ fmtDate(ad.end_date) }}</td>
            <td class="td-center">{{ ad.impressions }}</td>
            <td>
              <span class="pay-badge" :class="latestPayStatus(ad)">{{ latestPayLabel(ad) }}</span>
            </td>
            <td class="td-actions">
              <button class="btn-act btn-view" @click="openDetail(ad)" title="Ver detalle / gestionar">
                <i class="bi bi-gear"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- MODAL: Detail / Manage -->
    <div v-if="showModal" class="modal-backdrop" @click.self="showModal=false">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="modal-title">
            <i class="bi bi-gear-fill me-2"></i>
            Pauta #{{ selected.id }} — {{ selected.company_name }}
          </h6>
          <button class="btn-close-modal" @click="showModal=false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-body">

          <!-- Info general -->
          <div class="detail-grid">
            <div class="dg-row"><span class="dg-lbl">Título</span><span class="dg-val">{{ selected.title }}</span></div>
            <div class="dg-row" v-if="selected.description"><span class="dg-lbl">Descripción</span><span class="dg-val">{{ selected.description }}</span></div>
            <div class="dg-row" v-if="selected.cta_url"><span class="dg-lbl">URL destino</span>
              <a :href="selected.cta_url" target="_blank" rel="noopener" class="dg-link">{{ selected.cta_url }}</a>
            </div>
            <div class="dg-row"><span class="dg-lbl">Perfil objetivo</span><span class="dg-val">{{ selected.target_profile_name || 'Todos' }}</span></div>
            <div class="dg-row" v-if="selected.notes_to_admin"><span class="dg-lbl">Notas del asociado</span><span class="dg-val">{{ selected.notes_to_admin }}</span></div>
            <div class="dg-row"><span class="dg-lbl">Estado actual</span>
              <span class="status-badge" :class="selected.status">{{ statusLabel(selected.status) }}</span>
            </div>
            <div class="dg-row" v-if="selected.rejection_reason">
              <span class="dg-lbl">Motivo rechazo</span><span class="dg-val" style="color:#dc2626">{{ selected.rejection_reason }}</span>
            </div>
          </div>

          <!-- Piezas preview -->
          <div class="section-lbl mt-3">Piezas multimedia ({{ selected.pieces?.length || 0 }}/3)</div>
          <div class="pieces-preview-row">
            <template v-if="selected.pieces?.length">
              <div v-for="p in selected.pieces" :key="p.id" class="piece-card">
                <img v-if="p.piece_type === 'image'" :src="p.media_url" class="piece-media" />
                <video v-else-if="p.piece_type === 'video'" :src="p.media_url" class="piece-media" controls muted preload="metadata" />
                <div v-else-if="p.piece_type === 'youtube'" class="piece-yt">
                  <i class="bi bi-youtube"></i>
                  <span>{{ p.youtube_id }}</span>
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
                <span>Enviado: {{ fmtDate(pay.created_at?.split('T')[0]) }}</span>
                <span class="pay-badge" :class="pay.status">{{ payStatusLabel(pay.status) }}</span>
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

          <!-- Acciones SYSADMIN -->
          <div class="section-lbl mt-3">Acciones</div>
          <div class="action-group">

            <!-- Aprobar (solo pendiente) -->
            <button
              v-if="selected.status === 'pending'"
              class="btn-action btn-approve" @click="approveAd"
            ><i class="bi bi-check-circle me-1"></i>Aprobar</button>

            <!-- Rechazar (solo pendiente) -->
            <button
              v-if="selected.status === 'pending'"
              class="btn-action btn-reject" @click="rejectOpen = !rejectOpen"
            ><i class="bi bi-x-circle me-1"></i>Rechazar</button>

            <!-- Rechazar: motivo -->
            <div v-if="rejectOpen" class="reject-form">
              <textarea v-model="rejectReason" class="form-ctrl" rows="2" placeholder="Motivo del rechazo..."></textarea>
              <button class="btn-sub-save" @click="rejectAd"><i class="bi bi-send me-1"></i>Enviar rechazo</button>
              <button class="btn-sub-cancel" @click="rejectOpen=false;rejectReason=''">Cancelar</button>
            </div>

            <!-- Activar (aprobada o pausada) -->
            <template v-if="selected.status === 'approved' || selected.status === 'paused'">
              <div class="activate-form">
                <div class="af-row">
                  <div>
                    <label class="form-lbl">Slot *</label>
                    <select v-model="activateForm.slot_position" class="form-ctrl-sm">
                      <option :value="1">Slot 1</option>
                      <option :value="2">Slot 2</option>
                      <option :value="3">Slot 3</option>
                    </select>
                  </div>
                  <div>
                    <label class="form-lbl">Prioridad</label>
                    <input v-model.number="activateForm.priority" type="number" min="0" max="10" class="form-ctrl-sm" />
                  </div>
                  <div>
                    <label class="form-lbl">Inicio</label>
                    <input v-model="activateForm.start_date" type="date" class="form-ctrl-sm" />
                  </div>
                  <div>
                    <label class="form-lbl">Fin</label>
                    <input v-model="activateForm.end_date" type="date" class="form-ctrl-sm" />
                  </div>
                </div>
                <button class="btn-action btn-activate" @click="activateAd">
                  <i class="bi bi-broadcast me-1"></i>Activar pauta
                </button>
              </div>
            </template>

            <!-- Pausar (activa) -->
            <button
              v-if="selected.status === 'active'"
              class="btn-action btn-pause" @click="pauseAd"
            ><i class="bi bi-pause-circle me-1"></i>Pausar</button>

            <!-- Expirar manualmente -->
            <button
              v-if="['active','approved','paused'].includes(selected.status)"
              class="btn-action btn-expire" @click="expireAd"
            ><i class="bi bi-calendar-x me-1"></i>Marcar expirada</button>

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
import { ref, onMounted } from "vue"
import api from "@/services/apis"

const ads         = ref([])
const summary     = ref({})
const loading     = ref(false)
const filterStatus = ref("")
const showModal   = ref(false)
const selected    = ref({})
const saving      = ref(false)
const rejectOpen  = ref(false)
const rejectReason = ref("")
const activateForm = ref({ slot_position: 1, priority: 0, start_date: "", end_date: "" })

const kpis = [
  { key: "pending",  label: "Pendientes", icon: "bi-hourglass-split", color: "#f59e0b" },
  { key: "active",   label: "Activas",    icon: "bi-broadcast",       color: "#22c55e" },
  { key: "paused",   label: "Pausadas",   icon: "bi-pause-circle",    color: "#6b7280" },
  { key: "expired",  label: "Expiradas",  icon: "bi-calendar-x",      color: "#9ca3af" },
]

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
  } finally {
    loading.value = false
  }
}

function openDetail(ad) {
  selected.value = { ...ad }
  activateForm.value = {
    slot_position: ad.slot_position || 1,
    priority: ad.priority || 0,
    start_date: ad.start_date || "",
    end_date: ad.end_date || "",
  }
  rejectOpen.value   = false
  rejectReason.value = ""
  showModal.value    = true
}

async function approveAd() {
  if (!confirm("¿Aprobar esta pauta?")) return
  try {
    const res = await api.patch(`/ads/admin/${selected.value.id}/approve`)
    selected.value = { ...selected.value, ...res.data }
    await loadAds()
  } catch (e) {
    alert(e.response?.data?.detail || "Error")
  }
}

async function rejectAd() {
  if (!rejectReason.value.trim()) return alert("El motivo es requerido")
  try {
    const res = await api.patch(`/ads/admin/${selected.value.id}/reject`, { reason: rejectReason.value })
    selected.value = { ...selected.value, ...res.data }
    rejectOpen.value = false
    rejectReason.value = ""
    await loadAds()
  } catch (e) {
    alert(e.response?.data?.detail || "Error")
  }
}

async function activateAd() {
  const f = activateForm.value
  if (!f.start_date || !f.end_date) return alert("Las fechas son requeridas")
  if (!f.slot_position) return alert("El slot es requerido")
  try {
    const res = await api.patch(`/ads/admin/${selected.value.id}/activate`, f)
    selected.value = { ...selected.value, ...res.data }
    await loadAds()
  } catch (e) {
    alert(e.response?.data?.detail || "Error al activar")
  }
}

async function pauseAd() {
  if (!confirm("¿Pausar esta pauta?")) return
  try {
    const res = await api.patch(`/ads/admin/${selected.value.id}/pause`)
    selected.value = { ...selected.value, ...res.data }
    await loadAds()
  } catch (e) {
    alert(e.response?.data?.detail || "Error")
  }
}

async function expireAd() {
  if (!confirm("¿Marcar como expirada esta pauta?")) return
  try {
    await api.patch(`/ads/admin/${selected.value.id}/expire`)
    selected.value = { ...selected.value, status: "expired" }
    await loadAds()
  } catch (e) {
    alert(e.response?.data?.detail || "Error")
  }
}

async function verifyPayment(payId, action) {
  const label = action === "verified" ? "verificar" : "rechazar"
  if (!confirm(`¿${label} este pago?`)) return
  try {
    const res = await api.patch(`/ads/admin/payments/${payId}/verify`, { action })
    const idx = selected.value.payments.findIndex(p => p.id === payId)
    if (idx >= 0) selected.value.payments[idx] = res.data
    await loadAds()
  } catch (e) {
    alert(e.response?.data?.detail || "Error")
  }
}

function latestPayStatus(ad) {
  return ad.payments?.[0]?.status || "none"
}
function latestPayLabel(ad) {
  const map = { pending: "Pendiente", verified: "Verificado", rejected: "Rechazado", none: "Sin pago" }
  return map[latestPayStatus(ad)] || "—"
}
function statusLabel(s) {
  const map = { pending:"Pendiente", approved:"Aprobada", active:"Activa", paused:"Pausada", expired:"Expirada", rejected:"Rechazada" }
  return map[s] || s
}
function payStatusLabel(s) {
  const map = { pending:"Pendiente", verified:"Verificado", rejected:"Rechazado" }
  return map[s] || s
}
function fmtDate(d) {
  if (!d) return "—"
  const [y, m, dd] = d.split("-")
  return `${dd}/${m}/${y}`
}

onMounted(loadAds)
</script>

<style scoped>
.sysads-root { padding: 16px; max-width: 1200px; margin: 0 auto; }

.kpi-bar { display: flex; gap: 12px; margin-bottom: 18px; flex-wrap: wrap; }
.kpi-card {
  flex: 1; min-width: 110px; background: var(--card-bg, #fff);
  border-radius: 10px; padding: 12px 14px;
  display: flex; align-items: center; gap: 10px;
  box-shadow: 0 1px 4px rgba(0,0,0,.08);
}
.kpi-card .bi { font-size: 22px; flex-shrink: 0; }
.kpi-info { display: flex; flex-direction: column; }
.kpi-val  { font-size: 20px; font-weight: 800; line-height: 1; }
.kpi-lbl  { font-size: 11px; opacity: .6; }

.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; flex-wrap: wrap; gap: 10px; }
.section-title  { font-size: 15px; font-weight: 700; margin: 0; }
.filter-wrap { display: flex; gap: 8px; }
.filter-select { border: 1px solid rgba(0,0,0,.15); border-radius: 7px; padding: 6px 10px; font-size: 13px; background: transparent; color: inherit; }

.table-wrap { background: var(--card-bg, #fff); border-radius: 10px; box-shadow: 0 1px 4px rgba(0,0,0,.08); overflow-x: auto; }
.empty-state { text-align: center; padding: 40px 20px; color: #9ca3af; display: flex; flex-direction: column; align-items: center; gap: 8px; }
.ads-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.ads-table th { padding: 10px 12px; background: rgba(0,0,0,.04); font-weight: 700; text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: .4px; white-space: nowrap; }
.ads-table td { padding: 10px 12px; border-top: 1px solid rgba(0,0,0,.06); vertical-align: middle; }
.row-pending { background: rgba(245,158,11,.04); }
.td-id { font-weight: 700; opacity: .5; width: 40px; }
.td-company { font-weight: 600; max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.td-title   { max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.td-center  { text-align: center; }
.td-actions { white-space: nowrap; }

.status-badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 700; }
.status-badge.pending  { background: rgba(245,158,11,.15); color: #d97706; }
.status-badge.approved { background: rgba(59,130,246,.15); color: #2563eb; }
.status-badge.active   { background: rgba(34,197,94,.15);  color: #16a34a; }
.status-badge.paused   { background: rgba(107,114,128,.15); color: #6b7280; }
.status-badge.expired  { background: rgba(107,114,128,.1);  color: #9ca3af; }
.status-badge.rejected { background: rgba(239,68,68,.15);   color: #dc2626; }

.pay-badge { display: inline-block; padding: 2px 7px; border-radius: 10px; font-size: 10px; font-weight: 700; }
.pay-badge.pending   { background: rgba(245,158,11,.15); color: #d97706; }
.pay-badge.verified  { background: rgba(34,197,94,.15);  color: #16a34a; }
.pay-badge.rejected  { background: rgba(239,68,68,.15);  color: #dc2626; }
.pay-badge.none      { background: rgba(0,0,0,.06);       color: #9ca3af; }

.btn-act { width: 30px; height: 30px; border: none; border-radius: 7px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 14px; }
.btn-view { background: rgba(59,130,246,.1); color: #2563eb; }

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

/* Pieces preview */
.pieces-preview-row { display: flex; gap: 10px; flex-wrap: wrap; }
.piece-card {
  width: 120px; background: rgba(0,0,0,.05); border-radius: 8px;
  overflow: hidden; display: flex; flex-direction: column; position: relative;
}
.piece-media { width: 100%; height: 80px; object-fit: cover; display: block; }
.piece-yt  { height: 80px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; color: #ef4444; font-size: 24px; }
.piece-yt span { font-size: 10px; color: inherit; }
.piece-txt { padding: 8px; font-size: 11px; color: #374151; height: 80px; overflow: hidden; }
.piece-type-lbl { font-size: 9px; font-weight: 700; text-align: center; padding: 3px; opacity: .5; text-transform: uppercase; }
.no-pieces { font-size: 13px; color: #9ca3af; padding: 10px 0; }

/* Pay card */
.pay-card { background: rgba(0,0,0,.04); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px; }
.pay-info { display: flex; align-items: center; gap: 8px; font-size: 12px; margin-bottom: 8px; }
.btn-receipt { display: inline-flex; align-items: center; background: rgba(59,130,246,.1); color: #2563eb; border: none; border-radius: 6px; padding: 5px 10px; font-size: 12px; cursor: pointer; text-decoration: none; margin-bottom: 8px; }
.pay-actions { display: flex; gap: 6px; }
.btn-verify     { background: rgba(34,197,94,.15); color: #16a34a; border: none; border-radius: 6px; padding: 5px 12px; font-size: 12px; cursor: pointer; font-weight: 600; }
.btn-reject-pay { background: rgba(239,68,68,.15);  color: #dc2626; border: none; border-radius: 6px; padding: 5px 12px; font-size: 12px; cursor: pointer; font-weight: 600; }

/* Acciones SYSADMIN */
.action-group { display: flex; flex-direction: column; gap: 10px; }
.btn-action { border: none; border-radius: 8px; padding: 8px 16px; font-size: 13px; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; width: fit-content; }
.btn-approve  { background: rgba(34,197,94,.15);   color: #16a34a; }
.btn-reject   { background: rgba(239,68,68,.15);   color: #dc2626; }
.btn-activate { background: #2563eb; color: #fff; }
.btn-pause    { background: rgba(107,114,128,.15); color: #6b7280; }
.btn-expire   { background: rgba(245,158,11,.15);  color: #d97706; }

.reject-form, .activate-form { background: rgba(0,0,0,.04); border-radius: 8px; padding: 12px; display: flex; flex-direction: column; gap: 8px; }
.af-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.form-ctrl { width: 100%; border: 1px solid rgba(0,0,0,.15); border-radius: 6px; padding: 7px 10px; font-size: 13px; background: transparent; color: inherit; box-sizing: border-box; }
.form-ctrl:focus { outline: none; border-color: #2563eb; }
.form-ctrl-sm { width: 100%; border: 1px solid rgba(0,0,0,.15); border-radius: 6px; padding: 5px 8px; font-size: 12px; background: transparent; color: inherit; box-sizing: border-box; }
.form-lbl { font-size: 11px; font-weight: 600; display: block; margin-bottom: 3px; opacity: .65; }
.btn-sub-save   { background: #2563eb; color: #fff; border: none; border-radius: 6px; padding: 6px 12px; font-size: 12px; cursor: pointer; width: fit-content; }
.btn-sub-cancel { background: none; border: 1px solid rgba(0,0,0,.15); border-radius: 6px; padding: 6px 12px; font-size: 12px; cursor: pointer; }

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
