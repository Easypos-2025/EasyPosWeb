<template>
  <div class="page-container">

    <!-- ENCABEZADO -->
    <div class="page-header">
      <div>
        <h1 class="page-title"><i class="bi bi-box-arrow-right me-2"></i>Préstamos de Bodega</h1>
        <p class="page-subtitle">Registro y control de salidas y devoluciones</p>
      </div>
      <button v-if="canManage" class="btn btn-primary" @click="openCreate">
        <i class="bi bi-plus-lg"></i> Nuevo préstamo
      </button>
    </div>

    <!-- KPI BAR -->
    <div class="kpi-bar" v-if="stats">
      <div class="kpi-card">
        <span class="kpi-num">{{ stats.total }}</span>
        <span class="kpi-label">Total</span>
      </div>
      <div class="kpi-card kpi-amber">
        <span class="kpi-num">{{ stats.pendiente_confirmacion }}</span>
        <span class="kpi-label">Pendiente QR</span>
      </div>
      <div class="kpi-card kpi-green">
        <span class="kpi-num">{{ stats.activo }}</span>
        <span class="kpi-label">Activos</span>
      </div>
      <div class="kpi-card kpi-purple">
        <span class="kpi-num">{{ stats.retorno_pendiente }}</span>
        <span class="kpi-label">Por devolver</span>
      </div>
      <div class="kpi-card kpi-blue">
        <span class="kpi-num">{{ stats.devuelto }}</span>
        <span class="kpi-label">Devueltos</span>
      </div>
    </div>

    <!-- FILTROS -->
    <div class="filters-row">
      <input v-model="search" class="form-control" placeholder="Buscar artículo o colaborador..." style="max-width:260px" />
      <select v-model="filterEstado" class="form-select" style="max-width:200px">
        <option value="">Todos los estados</option>
        <option value="pendiente_confirmacion">Pendiente confirmación</option>
        <option value="activo">Activo</option>
        <option value="retorno_pendiente">Por devolver</option>
        <option value="devuelto">Devuelto</option>
        <option value="devuelto_con_dano">Devuelto con daño</option>
      </select>
    </div>

    <!-- TABLA -->
    <div class="table-card">
      <div v-if="loading" class="table-loading"><i class="bi bi-arrow-repeat spin"></i> Cargando...</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Artículo</th>
            <th>Líder / Colaborador</th>
            <th class="text-center">Cant.</th>
            <th class="text-center">Estado</th>
            <th class="text-center">Firmó QR</th>
            <th class="text-center">Salida QR</th>
            <th class="text-center">Retorno QR</th>
            <th class="text-center">Vence</th>
            <th class="text-center">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="loan in filtered" :key="loan.id" :class="{ 'row-overdue': isOverdue(loan) }" class="row-clickable" @click.stop="openDetail(loan)">
            <td class="text-muted">{{ loan.id }}</td>
            <td>
              <strong>{{ loan.bodega_item_nombre }}</strong>
              <div v-if="loan.bodega_item_codigo" class="sub-text">{{ loan.bodega_item_codigo }}</div>
            </td>
            <td>
              <div class="leader-col">
                <span class="leader-tag"><i class="bi bi-person-badge me-1"></i>{{ loan.task_leader_nombre || '—' }}</span>
                <span v-if="loan.colaborador_nombre" class="sub-text"><i class="bi bi-person me-1"></i>{{ loan.colaborador_nombre }}</span>
              </div>
            </td>
            <td class="text-center">{{ loan.cantidad }}</td>
            <td class="text-center">
              <span class="estado-badge" :class="estadoClass(loan.estado)">
                {{ estadoLabel(loan.estado) }}
              </span>
            </td>
            <td class="text-center">
              <span v-if="loan.qr_signed_by" class="signed-tag" :class="loan.qr_signed_by === 'leader' ? 'signed-leader' : 'signed-collab'">
                <i :class="loan.qr_signed_by === 'leader' ? 'bi bi-person-badge' : 'bi bi-person'"></i>
                {{ loan.qr_signed_by === 'leader' ? 'Líder' : 'Colaborador' }}
              </span>
              <span v-else class="text-muted">—</span>
            </td>
            <td class="text-center">
              <span v-if="loan.fecha_salida_confirmada" class="date-confirmed date-out">
                <i class="bi bi-check-circle-fill me-1"></i>{{ fmtDateTime(loan.fecha_salida_confirmada) }}
              </span>
              <span v-else class="text-muted">—</span>
            </td>
            <td class="text-center">
              <span v-if="loan.fecha_retorno_confirmada" class="date-confirmed date-in">
                <i class="bi bi-check-circle-fill me-1"></i>{{ fmtDateTime(loan.fecha_retorno_confirmada) }}
              </span>
              <span v-else class="text-muted">—</span>
            </td>
            <td class="text-center" :class="isOverdue(loan) ? 'text-danger' : 'text-muted'">
              <span v-if="loan.fecha_retorno_esperada">
                <i v-if="isOverdue(loan)" class="bi bi-exclamation-triangle-fill me-1"></i>
                {{ fmtDate(loan.fecha_retorno_esperada) }}
              </span>
              <span v-else>—</span>
            </td>
            <td class="text-center" @click.stop>
              <div class="action-row">
                <button class="btn btn-sm btn-outline-primary" @click.stop="openQr(loan)" title="Ver QR">
                  <i class="bi bi-qr-code"></i>
                </button>
                <button v-if="loan.estado === 'activo' && canManage" class="btn btn-sm btn-outline-purple" @click.stop="activarRetorno(loan)" title="Activar retorno">
                  <i class="bi bi-box-arrow-in-left"></i>
                </button>
                <button v-if="['devuelto','devuelto_con_dano','retorno_pendiente','activo'].includes(loan.estado) && canManage" class="btn btn-sm btn-outline-secondary" @click.stop="openCerrar(loan)" title="Cerrar con auditoría">
                  <i class="bi bi-clipboard-check"></i>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="filtered.length === 0">
            <td colspan="10" class="text-center text-muted py-4">No hay préstamos con estos filtros</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ── MODAL NUEVO PRÉSTAMO ── -->
    <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false">
      <div class="modal-box">
        <div class="mh"><h3><i class="bi bi-plus-circle me-2"></i>Nuevo Préstamo</h3>
          <button class="btn-x" @click="showCreate = false"><i class="bi bi-x-lg"></i></button></div>
        <div class="mb-area">
          <div class="fg">
            <label>Artículo de bodega *</label>
            <select v-model="createForm.bodega_item_id" class="form-select">
              <option :value="null">— Seleccionar artículo —</option>
              <option v-for="i in bodegaItems" :key="i.id" :value="i.id"
                :disabled="i.cantidad_disponible === 0">
                {{ i.nombre }}{{ i.codigo ? ' [' + i.codigo + ']' : '' }} — Disp: {{ i.cantidad_disponible }}
              </option>
            </select>
          </div>
          <div class="fg">
            <label>Líder de tarea * <span class="label-hint">(usuario responsable del artículo)</span></label>
            <select v-model="createForm.task_leader_id" class="form-select">
              <option :value="null">— Seleccionar líder de tarea —</option>
              <option v-for="u in systemUsers" :key="u.id" :value="u.id">
                {{ u.nombre }}{{ u.email ? ' — ' + u.email : '' }}
              </option>
            </select>
          </div>
          <div class="fg">
            <label>Colaborador externo <span class="label-hint">(opcional — quien retira físicamente)</span></label>
            <select v-model="createForm.external_collaborator_id" class="form-select">
              <option :value="null">— Sin colaborador externo —</option>
              <option v-for="c in collaborators" :key="c.id" :value="c.id">
                {{ c.nombre }} — {{ c.dni }}{{ c.empresa ? ' · ' + c.empresa : '' }}
              </option>
            </select>
          </div>
          <div class="form-row2">
            <div class="fg">
              <label>Cantidad *</label>
              <input v-model.number="createForm.cantidad" type="number" min="1" class="form-control" />
            </div>
            <div class="fg">
              <label>Fecha retorno esperada</label>
              <input v-model="createForm.fecha_retorno_esperada" type="date" class="form-control" />
            </div>
          </div>
          <div class="fg">
            <label>Notas</label>
            <textarea v-model="createForm.notas" class="form-control" rows="2" placeholder="Observaciones..."></textarea>
          </div>
        </div>
        <div class="mf">
          <button class="btn btn-secondary btn-sm" @click="showCreate = false">Cancelar</button>
          <button class="btn btn-primary btn-sm" @click="submitCreate" :disabled="creating">
            <i v-if="creating" class="bi bi-arrow-repeat spin"></i>
            {{ creating ? 'Creando...' : 'Crear y generar QR' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ── MODAL QR ── -->
    <div v-if="showQr" class="modal-overlay" @click.self="showQr = false">
      <div class="modal-box modal-qr">
        <div class="mh">
          <h3><i class="bi bi-qr-code me-2"></i>QR del Préstamo #{{ selectedLoan?.id }}</h3>
          <button class="btn-x" @click="showQr = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="mb-area" style="align-items:center">
          <div class="loan-info-block">
            <div><i class="bi bi-box me-1"></i><strong>{{ selectedLoan?.bodega_item_nombre }}</strong></div>
            <div><i class="bi bi-person me-1"></i>{{ selectedLoan?.colaborador_nombre }}</div>
            <div class="mt-1">
              <span class="estado-badge" :class="estadoClass(selectedLoan?.estado)">{{ estadoLabel(selectedLoan?.estado) }}</span>
            </div>
          </div>
          <div class="qr-img-wrap" v-if="qrBlobUrl">
            <img :src="qrBlobUrl" alt="QR" class="qr-img" />
          </div>
          <div v-else class="qr-loading"><i class="bi bi-arrow-repeat spin"></i> Cargando QR...</div>
          <div class="qr-actions">
            <button class="btn btn-outline-primary btn-sm" @click="downloadQr">
              <i class="bi bi-download"></i> Descargar
            </button>
            <button class="btn btn-outline-secondary btn-sm" @click="printQr">
              <i class="bi bi-printer"></i> Imprimir
            </button>
          </div>
          <p class="qr-hint">El colaborador escanea este QR para confirmar recepción o devolución.</p>
        </div>
        <div class="mf">
          <button class="btn btn-secondary btn-sm" @click="showQr = false">Cerrar</button>
        </div>
      </div>
    </div>

    <!-- ── MODAL CERRAR CON AUDITORÍA ── -->
    <div v-if="showCerrar" class="modal-overlay" @click.self="showCerrar = false">
      <div class="modal-box">
        <div class="mh">
          <h3><i class="bi bi-clipboard-check me-2"></i>Cerrar Préstamo #{{ cerrarLoan?.id }}</h3>
          <button class="btn-x" @click="showCerrar = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="mb-area">
          <div class="loan-info-block">
            <div><strong>{{ cerrarLoan?.bodega_item_nombre }}</strong> → {{ cerrarLoan?.colaborador_nombre }}</div>
          </div>
          <div class="fg">
            <label>Estado físico del artículo *</label>
            <select v-model="cerrarForm.estado_fisico_retorno" class="form-select">
              <option value="perfecto">Perfecto estado</option>
              <option value="desgaste">Desgaste normal</option>
              <option value="dano_leve">Daño leve</option>
              <option value="dano_grave">Daño grave</option>
            </select>
          </div>
          <div class="fg">
            <label>Notas de auditoría</label>
            <textarea v-model="cerrarForm.notas" class="form-control" rows="3" placeholder="Describe el estado, daños u observaciones..."></textarea>
          </div>
        </div>
        <div class="mf">
          <button class="btn btn-secondary btn-sm" @click="showCerrar = false">Cancelar</button>
          <button class="btn btn-primary btn-sm" @click="submitCerrar" :disabled="cerrando">
            <i v-if="cerrando" class="bi bi-arrow-repeat spin"></i>
            {{ cerrando ? 'Cerrando...' : 'Cerrar préstamo' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ── MODAL DETALLE ── -->
    <div v-if="showDetail" class="modal-overlay" @click.self="showDetail = false">
      <div class="modal-box modal-detail">
        <div class="mh">
          <h3><i class="bi bi-info-circle me-2"></i>Detalle Préstamo <span class="detail-id">#{{ detailLoan?.id }}</span></h3>
          <button class="btn-x" @click="showDetail = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="mb-area">

          <!-- Estado -->
          <div class="detail-estado-row">
            <span class="estado-badge" :class="estadoClass(detailLoan?.estado)">{{ estadoLabel(detailLoan?.estado) }}</span>
            <span v-if="detailLoan?.estado_fisico_retorno" class="fisico-tag">
              <i class="bi bi-clipboard-check me-1"></i>{{ { perfecto:'Perfecto estado', desgaste:'Desgaste normal', dano_leve:'Daño leve', dano_grave:'Daño grave' }[detailLoan.estado_fisico_retorno] || detailLoan.estado_fisico_retorno }}
            </span>
          </div>

          <!-- Artículo -->
          <div class="detail-section">
            <div class="detail-section-title"><i class="bi bi-box me-1"></i>Artículo</div>
            <div class="detail-value"><strong>{{ detailLoan?.bodega_item_nombre }}</strong></div>
            <div v-if="detailLoan?.bodega_item_codigo" class="detail-sub">Código: {{ detailLoan.bodega_item_codigo }}</div>
            <div class="detail-sub">Cantidad: <strong>{{ detailLoan?.cantidad }}</strong></div>
          </div>

          <!-- Líder de tarea -->
          <div class="detail-section">
            <div class="detail-section-title"><i class="bi bi-person-badge me-1"></i>Líder de Tarea (Responsable)</div>
            <div class="detail-value"><strong>{{ detailLoan?.task_leader_nombre || '—' }}</strong></div>
            <div v-if="detailLoan?.qr_signed_by" class="detail-sub">
              <i class="bi bi-qr-code me-1"></i>Firmó QR:
              <strong>{{ detailLoan.qr_signed_by === 'leader' ? 'El líder' : 'El colaborador' }}</strong>
            </div>
          </div>

          <!-- Colaborador externo -->
          <div class="detail-section" v-if="detailLoan?.colaborador_nombre">
            <div class="detail-section-title"><i class="bi bi-person me-1"></i>Colaborador Externo</div>
            <div class="detail-value"><strong>{{ detailLoan.colaborador_nombre }}</strong></div>
            <div v-if="detailLoan?.colaborador_dni" class="detail-sub">DNI: {{ detailLoan.colaborador_dni }}</div>
            <div v-if="detailLoan?.colaborador_empresa" class="detail-sub">Empresa: {{ detailLoan.colaborador_empresa }}</div>
          </div>

          <!-- Fechas -->
          <div class="detail-section">
            <div class="detail-section-title"><i class="bi bi-calendar3 me-1"></i>Fechas</div>
            <div class="detail-dates-grid">
              <div class="detail-date-item">
                <span class="detail-date-label">Registro</span>
                <span class="detail-date-val">{{ detailLoan?.created_at ? fmtDateTime(detailLoan.created_at) : '—' }}</span>
              </div>
              <div class="detail-date-item">
                <span class="detail-date-label">Recibido (QR salida)</span>
                <span class="detail-date-val" :class="detailLoan?.fecha_salida_confirmada ? 'date-out' : ''">
                  {{ detailLoan?.fecha_salida_confirmada ? fmtDateTime(detailLoan.fecha_salida_confirmada) : '—' }}
                </span>
              </div>
              <div class="detail-date-item">
                <span class="detail-date-label">Vencimiento esperado</span>
                <span class="detail-date-val" :class="isOverdue(detailLoan) ? 'text-danger' : ''">
                  {{ detailLoan?.fecha_retorno_esperada ? fmtDate(detailLoan.fecha_retorno_esperada) : '—' }}
                </span>
              </div>
              <div class="detail-date-item">
                <span class="detail-date-label">Devuelto (QR retorno)</span>
                <span class="detail-date-val" :class="detailLoan?.fecha_retorno_confirmada ? 'date-in' : ''">
                  {{ detailLoan?.fecha_retorno_confirmada ? fmtDateTime(detailLoan.fecha_retorno_confirmada) : '—' }}
                </span>
              </div>
            </div>
          </div>

          <!-- Descripción -->
          <div class="detail-section" v-if="detailLoan?.notas">
            <div class="detail-section-title"><i class="bi bi-chat-left-text me-1"></i>Descripción / Notas</div>
            <div class="detail-notas">{{ detailLoan.notas }}</div>
          </div>

          <!-- Creado por -->
          <div v-if="detailLoan?.created_by_nombre" class="detail-footer-info">
            <i class="bi bi-person-check me-1"></i>Creado por: <strong>{{ detailLoan.created_by_nombre }}</strong>
          </div>

        </div>
        <div class="mf">
          <button class="btn btn-secondary btn-sm" @click="showDetail = false">Cerrar</button>
          <button class="btn btn-outline-primary btn-sm" @click="showDetail = false; openQr(detailLoan)">
            <i class="bi bi-qr-code me-1"></i>Ver QR
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

const apiBase  = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
const userInfo = JSON.parse(localStorage.getItem("user") || "{}")
const canManage = !['WORKER','AUDITOR'].some(r => (userInfo.role || '').toUpperCase().includes(r))

const loans        = ref([])
const bodegaItems  = ref([])
const collaborators = ref([])
const systemUsers  = ref([])
const stats        = ref(null)
const loading      = ref(true)
const search       = ref("")
const filterEstado = ref("")

const showCreate = ref(false)
const creating   = ref(false)
const createForm = ref({ bodega_item_id: null, task_leader_id: null, external_collaborator_id: null, cantidad: 1, fecha_retorno_esperada: "", notas: "" })

const showQr     = ref(false)
const selectedLoan = ref(null)
const qrBlobUrl  = ref(null)

const showCerrar = ref(false)
const cerrarLoan = ref(null)
const cerrando   = ref(false)
const cerrarForm = ref({ estado_fisico_retorno: "perfecto", notas: "" })

const showDetail = ref(false)
const detailLoan = ref(null)
function openDetail(loan) { detailLoan.value = loan; showDetail.value = true }

const ESTADO_LABELS = {
  pendiente_confirmacion: "Pendiente QR",
  activo:                 "Activo",
  retorno_pendiente:      "Por devolver",
  devuelto:               "Devuelto",
  devuelto_con_dano:      "Devuelto c/ daño",
}
const ESTADO_CLASSES = {
  pendiente_confirmacion: "e-amber",
  activo:                 "e-green",
  retorno_pendiente:      "e-purple",
  devuelto:               "e-blue",
  devuelto_con_dano:      "e-red",
}

function estadoLabel(e) { return ESTADO_LABELS[e] || e }
function estadoClass(e) { return ESTADO_CLASSES[e] || "" }
function fmtDate(iso)   { return iso ? new Date(iso).toLocaleDateString("es-CO", { day:"2-digit", month:"short", year:"numeric" }) : "" }
function fmtDateTime(iso) {
  if (!iso) return ""
  const d = new Date(iso)
  return d.toLocaleDateString("es-CO", { day:"2-digit", month:"short" }) + " " +
         d.toLocaleTimeString("es-CO", { hour:"2-digit", minute:"2-digit" })
}
function isOverdue(l) {
  return l.fecha_retorno_esperada &&
    new Date(l.fecha_retorno_esperada) < new Date() &&
    !["devuelto","devuelto_con_dano"].includes(l.estado)
}

const filtered = computed(() => {
  return loans.value.filter(l => {
    const q = search.value.toLowerCase()
    const matchSearch = !q ||
      (l.bodega_item_nombre || "").toLowerCase().includes(q) ||
      (l.task_leader_nombre || "").toLowerCase().includes(q) ||
      (l.colaborador_nombre || "").toLowerCase().includes(q)
    const matchEstado = !filterEstado.value || l.estado === filterEstado.value
    return matchSearch && matchEstado
  })
})

async function load() {
  loading.value = true
  try {
    const [lr, br, cr, ur, sr] = await Promise.all([
      api.get("/loans/"),
      api.get("/bodega-items/"),
      api.get("/external-collaborators/"),
      api.get("/users/"),
      api.get("/loans/stats"),
    ])
    loans.value        = lr.data
    bodegaItems.value  = br.data
    collaborators.value = cr.data
    systemUsers.value  = ur.data
    stats.value        = sr.data
  } catch { showToast("Error cargando datos", "error") }
  finally { loading.value = false }
}

function openCreate() {
  createForm.value = { bodega_item_id: null, task_leader_id: null, external_collaborator_id: null, cantidad: 1, fecha_retorno_esperada: "", notas: "" }
  showCreate.value = true
}

async function submitCreate() {
  if (!createForm.value.bodega_item_id)   { showToast("Selecciona un artículo", "warning"); return }
  if (!createForm.value.task_leader_id)   { showToast("El líder de tarea es obligatorio", "warning"); return }
  creating.value = true
  try {
    const r = await api.post("/loans/", createForm.value)
    loans.value.unshift(r.data)
    showCreate.value = false
    await load()
    showToast("Préstamo creado — QR listo", "success")
    openQr(r.data)
  } catch (e) {
    showToast(e.response?.data?.detail || "Error creando préstamo", "error")
  } finally { creating.value = false }
}

async function openQr(loan) {
  selectedLoan.value = loan
  qrBlobUrl.value = null
  showQr.value = true
  try {
    const token = localStorage.getItem("token")
    const res = await fetch(`${apiBase}/loans/${loan.id}/qr`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (!res.ok) throw new Error("Error QR")
    const blob = await res.blob()
    qrBlobUrl.value = URL.createObjectURL(blob)
  } catch { showToast("Error cargando QR", "error") }
}

function downloadQr() {
  if (!qrBlobUrl.value) return
  const a = document.createElement("a")
  a.href = qrBlobUrl.value
  a.download = `qr-prestamo-${selectedLoan.value?.id}.png`
  a.click()
}

function printQr() {
  if (!qrBlobUrl.value) return
  const win = window.open("", "_blank")
  const lider = selectedLoan.value?.task_leader_nombre || '—'
  const collab = selectedLoan.value?.colaborador_nombre ? ` / Colaborador: ${selectedLoan.value.colaborador_nombre}` : ''
  win.document.write(`<html><body style="text-align:center;padding:40px">
    <h2>Préstamo #${selectedLoan.value?.id}</h2>
    <p><strong>${selectedLoan.value?.bodega_item_nombre}</strong></p>
    <p style="font-size:13px">Líder: ${lider}${collab}</p>
    <img src="${qrBlobUrl.value}" style="max-width:300px" />
    <p style="margin-top:16px;font-size:12px;color:#666">Escanea para confirmar recepción o devolución</p>
  </body></html>`)
  win.document.close()
  win.focus()
  win.print()
}

async function activarRetorno(loan) {
  const { isConfirmed } = await window.Swal.fire({
    title: "¿Activar retorno?",
    text: `${loan.task_leader_nombre || loan.colaborador_nombre || 'El responsable'} escaneará el QR para confirmar la devolución de "${loan.bodega_item_nombre}".`,
    icon: "question", showCancelButton: true,
    confirmButtonText: "Sí, activar retorno", cancelButtonText: "Cancelar"
  })
  if (!isConfirmed) return
  try {
    await api.post(`/loans/${loan.id}/activar-retorno`)
    showToast("Retorno activado — comparte el QR con el colaborador", "success")
    await load()
  } catch (e) { showToast(e.response?.data?.detail || "Error", "error") }
}

function openCerrar(loan) {
  cerrarLoan.value = loan
  cerrarForm.value = { estado_fisico_retorno: "perfecto", notas: "" }
  showCerrar.value = true
}

async function submitCerrar() {
  cerrando.value = true
  try {
    await api.patch(`/loans/${cerrarLoan.value.id}/cerrar`, cerrarForm.value)
    showToast("Préstamo cerrado", "success")
    showCerrar.value = false
    await load()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error cerrando", "error")
  } finally { cerrando.value = false }
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 1200px; }
.page-header    { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; gap: 12px; flex-wrap: wrap; }
.page-title     { font-size: 22px; font-weight: 700; color: #1e293b; margin: 0 0 4px; }
.page-subtitle  { font-size: 13px; color: #64748b; margin: 0; }

/* KPI BAR */
.kpi-bar  { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 18px; }
.kpi-card { background: #fff; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.07); padding: 12px 18px; display: flex; align-items: baseline; gap: 8px; }
.kpi-num  { font-size: 24px; font-weight: 800; color: #1e293b; }
.kpi-label { font-size: 12px; color: #94a3b8; }
.kpi-amber .kpi-num  { color: #b45309; }
.kpi-green .kpi-num  { color: #16a34a; }
.kpi-purple .kpi-num { color: #7c3aed; }
.kpi-blue .kpi-num   { color: #1e40af; }

/* FILTROS */
.filters-row { display: flex; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }

/* TABLE */
.table-card   { background: #fff; border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,.08); overflow: hidden; }
.table-loading { padding: 40px; text-align: center; color: #94a3b8; }
.data-table   { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { background: #f8fafc; color: #475569; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: .4px; padding: 11px 12px; border-bottom: 1px solid #e2e8f0; }
.data-table td { padding: 11px 12px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: #f8fafc; }
.row-overdue td { background: #fff5f5 !important; }
.text-center { text-align: center; }
.text-muted  { color: #94a3b8 !important; font-size: 12px; }
.text-danger { color: #ef4444 !important; font-size: 12px; }
.sub-text    { font-size: 11px; color: #94a3b8; margin-top: 2px; }
.py-4        { padding: 32px 0; }

/* ESTADO BADGES */
.estado-badge { font-size: 10px; font-weight: 700; padding: 2px 9px; border-radius: 20px; white-space: nowrap; }
.e-amber  { background: #fef3c7; color: #b45309; }
.e-green  { background: #dcfce7; color: #16a34a; }
.e-purple { background: #f3e8ff; color: #7c3aed; }
.e-blue   { background: #dbeafe; color: #1e40af; }
.e-red    { background: #fef2f2; color: #b91c1c; }

/* ACTIONS */
.action-row { display: flex; gap: 4px; justify-content: center; flex-wrap: wrap; }
.btn-outline-purple   { background: #f3e8ff; color: #7c3aed; border: 1.5px solid #d8b4fe; }
.btn-outline-secondary { background: #f8fafc; color: #475569; border: 1.5px solid #e2e8f0; }

/* MODALES */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 2000; padding: 16px; }
.modal-box     { background: #fff; border-radius: 16px; width: 100%; max-width: 480px; max-height: 90vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,.2); }
.modal-qr      { max-width: 400px; }
.mh  { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid #f1f5f9; flex-shrink: 0; }
.mh h3 { font-size: 15px; font-weight: 700; color: #1e293b; margin: 0; display: flex; align-items: center; }
.btn-x { background: none; border: none; font-size: 16px; cursor: pointer; color: #94a3b8; }
.mb-area { padding: 18px 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; }
.mf { padding: 12px 20px 16px; display: flex; justify-content: flex-end; gap: 8px; border-top: 1px solid #f1f5f9; flex-shrink: 0; }

.fg       { display: flex; flex-direction: column; gap: 4px; }
.fg label { font-size: 13px; font-weight: 600; color: #374151; }
.form-row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

/* QR MODAL */
.loan-info-block { background: #f8fafc; border-radius: 10px; padding: 12px 16px; font-size: 13px; color: #475569; display: flex; flex-direction: column; gap: 4px; width: 100%; }
.mt-1 { margin-top: 4px; }
.qr-img-wrap { display: flex; justify-content: center; }
.qr-img      { width: 220px; height: 220px; border: 2px solid #e2e8f0; border-radius: 12px; }
.qr-loading  { padding: 40px; color: #94a3b8; display: flex; align-items: center; gap: 8px; }
.qr-actions  { display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; }
.qr-hint     { font-size: 12px; color: #94a3b8; text-align: center; margin: 0; }

.btn         { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; transition: all .15s; }
.btn-primary { background: #3b82f6; color: #fff; } .btn-primary:hover { background: #2563eb; }
.btn-primary:disabled { opacity: .6; cursor: not-allowed; }
.btn-secondary { border: 1.5px solid #e2e8f0; background: #fff; color: #64748b; }
.btn-sm { padding: 6px 12px; font-size: 12px; }
.btn-outline-primary { background: #eff6ff; color: #1d4ed8; border: 1.5px solid #bfdbfe; }

.date-confirmed { font-size: 11px; font-weight: 600; display: inline-flex; align-items: center; gap: 2px; }
.date-out { color: #16a34a; }
.date-in  { color: #1e40af; }

/* FILA CLICKEABLE */
.row-clickable { cursor: pointer; transition: background .1s; }
.row-clickable:hover td { background: #f0f7ff !important; }

/* MODAL DETALLE */
.modal-detail      { max-width: 520px; }
.detail-id         { color: #64748b; font-weight: 600; }
.detail-estado-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.fisico-tag        { font-size: 11px; background: #f1f5f9; color: #475569; border-radius: 20px; padding: 2px 10px; font-weight: 600; }
.detail-section    { background: #f8fafc; border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px; }
.detail-section-title { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .5px; color: #94a3b8; margin-bottom: 4px; }
.detail-value      { font-size: 14px; color: #1e293b; }
.detail-sub        { font-size: 12px; color: #64748b; }
.detail-dates-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.detail-date-item  { display: flex; flex-direction: column; gap: 2px; }
.detail-date-label { font-size: 11px; color: #94a3b8; font-weight: 600; }
.detail-date-val   { font-size: 13px; color: #374151; font-weight: 500; }
.detail-notas      { font-size: 13px; color: #374151; white-space: pre-wrap; line-height: 1.5; }
.detail-footer-info { font-size: 12px; color: #94a3b8; padding: 0 2px; }

/* Líder en tabla */
.leader-col   { display: flex; flex-direction: column; gap: 2px; }
.leader-tag   { font-size: 13px; font-weight: 600; color: #1e293b; display: flex; align-items: center; }

/* Badge firmó QR */
.signed-tag      { font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 20px; display: inline-flex; align-items: center; gap: 4px; }
.signed-leader   { background: #dbeafe; color: #1d4ed8; }
.signed-collab   { background: #f3e8ff; color: #7c3aed; }

/* Label hint en form */
.label-hint { font-size: 11px; color: #94a3b8; font-weight: 400; }

.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

@media (max-width: 768px) {
  .page-container { padding: 16px; }
  .page-title     { font-size: 18px; }
  .kpi-card       { padding: 10px 14px; }
  .kpi-num        { font-size: 20px; }

  .filters-row { flex-direction: column; }
  .filters-row .form-control,
  .filters-row .form-select { max-width: 100% !important; }

  /* Tabla: permitir scroll horizontal y ocultar columnas de menor prioridad */
  .table-card { overflow-x: auto; border-radius: 10px; }
  .data-table th:nth-child(1), .data-table td:nth-child(1),
  .data-table th:nth-child(6), .data-table td:nth-child(6),
  .data-table th:nth-child(7), .data-table td:nth-child(7) { display: none; }
}

@media (max-width: 576px) {
  .page-container { padding: 12px; }
  .page-title     { font-size: 16px; }
  .page-subtitle  { font-size: 12px; }
  .kpi-bar        { gap: 6px; }
  .kpi-card       { padding: 8px 12px; }
  .kpi-num        { font-size: 18px; }

  /* Ocultar también Vence en pantallas muy pequeñas */
  .data-table th:nth-child(8), .data-table td:nth-child(8) { display: none; }
  .data-table     { font-size: 12px; }
  .data-table th,
  .data-table td  { padding: 8px 8px; }

  .form-row2 { grid-template-columns: 1fr; }
  .action-row { gap: 2px; }
  .btn-sm     { padding: 5px 8px; font-size: 11px; }
}
</style>
