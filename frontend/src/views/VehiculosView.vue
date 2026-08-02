<template>
  <div class="veh-container">

    <!-- ── Encabezado ── -->
    <div class="veh-header">
      <div>
        <h1 class="veh-title"><i class="bi bi-car-front-fill"></i> Vehículos</h1>
        <p class="veh-sub">Registro unificado de vehículos y propietarios</p>
      </div>
      <button class="btn-primary" @click="abrirCrear">
        <i class="bi bi-plus-lg"></i> Nuevo Vehículo
      </button>
    </div>

    <!-- ── Buscador ── -->
    <div class="veh-search-bar">
      <div class="search-input-wrap">
        <i class="bi bi-search"></i>
        <input
          v-model="q"
          class="search-input"
          placeholder="Buscar por placa, propietario, marca, documento…"
          @input="buscar"
        />
        <button v-if="q" class="search-clear" @click="q=''; buscar()">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>
    </div>

    <!-- ── Tabla ── -->
    <div class="veh-table-card">
      <div v-if="cargando" class="veh-loading">
        <i class="bi bi-arrow-repeat spin"></i> Cargando…
      </div>
      <table v-else class="veh-table">
        <thead>
          <tr>
            <th>Placa</th>
            <th>Vehículo</th>
            <th>Propietario</th>
            <th>Contacto</th>
            <th class="text-center">Órdenes</th>
            <th class="text-center">Estado</th>
            <th class="text-center">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="v in vehiculos" :key="v.id" class="veh-row" @click="abrirDetalle(v)">
            <td>
              <span class="placa-badge">{{ v.placa }}</span>
            </td>
            <td>
              <strong>{{ [v.marca, v.modelo, v.anio].filter(Boolean).join(' ') || '—' }}</strong>
              <div class="sub-text">{{ v.tipo_nombre || '' }} {{ v.color ? '· ' + v.color : '' }}</div>
            </td>
            <td>
              <span v-if="v.propietario_nombre">{{ v.propietario_nombre }}</span>
              <span v-else class="sin-propietario">Sin propietario</span>
              <div v-if="v.propietario_documento" class="sub-text">{{ v.propietario_documento }}</div>
            </td>
            <td class="sub-text">{{ v.propietario_telefono || '—' }}</td>
            <td class="text-center">
              <span class="ord-badge" title="Taller">
                <i class="bi bi-tools"></i> {{ v.total_ordenes_taller || 0 }}
              </span>
              <span class="ord-badge ord-park" title="Parking">
                <i class="bi bi-p-square-fill"></i> {{ v.total_ordenes_parking || 0 }}
              </span>
            </td>
            <td class="text-center">
              <span class="estado-badge" :class="v.is_active ? 'activo' : 'inactivo'">
                {{ v.is_active ? 'Activo' : 'Inactivo' }}
              </span>
            </td>
            <td class="text-center" @click.stop>
              <div class="action-row">
                <button class="btn-icon" title="Editar" @click="abrirEditar(v)">
                  <i class="bi bi-pencil-fill"></i>
                </button>
                <button class="btn-icon" title="Historial" @click="abrirHistorial(v)">
                  <i class="bi bi-clock-history"></i>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="!cargando && vehiculos.length === 0">
            <td colspan="7" class="text-center py-4 sub-text">
              No se encontraron vehículos
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ══ MODAL CREAR / EDITAR ══ -->
    <Teleport to="body">
      <div v-if="showModal" class="modal-overlay" @click.self="showModal=false">
        <div class="modal-box">
          <div class="modal-header">
            <h3><i class="bi bi-car-front-fill"></i> {{ editando ? 'Editar Vehículo' : 'Nuevo Vehículo' }}</h3>
            <button class="btn-x" @click="showModal=false"><i class="bi bi-x-lg"></i></button>
          </div>
          <div class="modal-body">

            <!-- Datos del vehículo -->
            <div class="section-title">Datos del vehículo</div>
            <div class="form-grid2">
              <div class="fg">
                <label>Placa *</label>
                <input v-model="form.placa" class="form-control" placeholder="ABC-123"
                       :disabled="!!editando" @input="form.placa = form.placa.toUpperCase()" />
              </div>
              <div class="fg">
                <label>Tipo de vehículo</label>
                <select v-model="form.vehicle_type_id" class="form-select">
                  <option :value="null">— Seleccionar —</option>
                  <option v-for="t in tiposVehiculo" :key="t.id" :value="t.id">{{ t.nombre }}</option>
                </select>
              </div>
              <div class="fg">
                <label>Marca</label>
                <input v-model="form.marca" class="form-control" placeholder="Toyota, Chevrolet…" />
              </div>
              <div class="fg">
                <label>Modelo</label>
                <input v-model="form.modelo" class="form-control" placeholder="Corolla, Spark…" />
              </div>
              <div class="fg">
                <label>Año</label>
                <input v-model.number="form.anio" type="number" class="form-control"
                       placeholder="2020" min="1950" :max="new Date().getFullYear()+1" />
              </div>
              <div class="fg">
                <label>Color</label>
                <input v-model="form.color" class="form-control" placeholder="Blanco, Negro…" />
              </div>
              <div class="fg">
                <label>Km actual</label>
                <input v-model.number="form.km_actual" type="number" class="form-control"
                       placeholder="0" min="0" />
              </div>
            </div>

            <!-- Propietario -->
            <div class="section-title" style="margin-top:20px">Propietario</div>

            <!-- Buscar propietario existente -->
            <div class="fg" style="margin-bottom:12px">
              <label>Buscar propietario existente</label>
              <div class="search-prop-wrap">
                <input v-model="busqProp" class="form-control"
                       placeholder="Nombre o documento…"
                       @input="buscarPropietarios" />
                <div v-if="propSugerencias.length" class="prop-dropdown">
                  <div v-for="p in propSugerencias" :key="p.id"
                       class="prop-option" @click="seleccionarPropietario(p)">
                    <strong>{{ p.nombre }}</strong>
                    <span class="sub-text">{{ p.documento }} · {{ p.total_vehiculos }} vehículo(s)</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Datos del propietario (nuevo o seleccionado) -->
            <div class="form-grid2" :class="{ 'prop-seleccionado': form.propietario_id }">
              <div class="fg fg-full">
                <label>Nombre *</label>
                <input v-model="form.propietario_nombre" class="form-control"
                       placeholder="Nombre completo del propietario" />
              </div>
              <div class="fg">
                <label>Documento</label>
                <input v-model="form.propietario_documento" class="form-control"
                       placeholder="Cédula / NIT" />
              </div>
              <div class="fg">
                <label>Teléfono</label>
                <input v-model="form.propietario_telefono" class="form-control"
                       placeholder="Celular de contacto" />
              </div>
              <div class="fg">
                <label>Email</label>
                <input v-model="form.propietario_email" class="form-control"
                       placeholder="correo@ejemplo.com" type="email" />
              </div>
            </div>
            <div v-if="form.propietario_id" class="prop-id-hint">
              <i class="bi bi-person-check-fill"></i>
              Propietario existente ID #{{ form.propietario_id }} — se actualizarán sus datos al guardar.
              <button class="link-btn" @click="limpiarPropietario">Usar otro propietario</button>
            </div>

          </div>
          <div class="modal-footer">
            <button class="btn-secondary" @click="showModal=false">Cancelar</button>
            <button class="btn-primary" @click="guardar" :disabled="guardando">
              <i v-if="guardando" class="bi bi-arrow-repeat spin"></i>
              {{ guardando ? 'Guardando…' : 'Guardar' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ══ MODAL HISTORIAL ══ -->
    <Teleport to="body">
      <div v-if="showHistorial" class="modal-overlay" @click.self="showHistorial=false">
        <div class="modal-box modal-wide">
          <div class="modal-header">
            <div>
              <h3><i class="bi bi-clock-history"></i> Historial — {{ vehiculoActivo?.placa }}</h3>
              <p class="modal-sub">
                {{ vehiculoActivo?.marca }} {{ vehiculoActivo?.modelo }}
                <span v-if="vehiculoActivo?.propietario_nombre"> · {{ vehiculoActivo.propietario_nombre }}</span>
              </p>
            </div>
            <button class="btn-x" @click="showHistorial=false"><i class="bi bi-x-lg"></i></button>
          </div>
          <div class="modal-body">
            <div v-if="cargandoHist" class="text-center py-4 sub-text">
              <i class="bi bi-arrow-repeat spin"></i> Cargando historial…
            </div>
            <div v-else-if="historial.length === 0" class="text-center py-4 sub-text">
              Este vehículo no tiene órdenes registradas.
            </div>
            <div v-else class="hist-list">
              <div v-for="h in historial" :key="h.origen+h.id" class="hist-item">
                <div class="hist-icon" :class="h.origen">
                  <i :class="h.origen === 'taller' ? 'bi bi-tools' : 'bi bi-p-square-fill'"></i>
                </div>
                <div class="hist-body">
                  <div class="hist-top">
                    <span class="hist-orden">{{ h.numero_orden }}</span>
                    <span class="hist-origen-badge" :class="h.origen">
                      {{ h.origen === 'taller' ? 'Taller' : 'Parking' }}
                    </span>
                    <span class="hist-estado" :class="h.estado">{{ h.estado }}</span>
                  </div>
                  <div class="hist-fecha">{{ fmtFecha(h.fecha) }}</div>
                  <div v-if="h.diagnostico" class="hist-desc">{{ h.diagnostico }}</div>
                  <div v-if="h.trabajo_realizado" class="hist-desc">{{ h.trabajo_realizado }}</div>
                  <div v-if="h.km_ingreso" class="sub-text">Km entrada: {{ h.km_ingreso?.toLocaleString() }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import { useCompanyStore } from "@/stores/companyStore"

const companyStore = useCompanyStore()
const companyId    = () => companyStore.selectedCompany?.id

// ── Estado ─────────────────────────────────────────────────────────────────
const vehiculos     = ref([])
const tiposVehiculo = ref([])
const cargando      = ref(true)
const q             = ref("")

let buscarTimer = null
function buscar() {
  clearTimeout(buscarTimer)
  buscarTimer = setTimeout(cargarVehiculos, 350)
}

async function cargarVehiculos() {
  cargando.value = true
  try {
    const { data } = await api.get("/api/vehicles/", {
      params: { company_id: companyId(), q: q.value || undefined }
    })
    vehiculos.value = data
  } catch { showToast("Error cargando vehículos", "error") }
  finally { cargando.value = false }
}

async function cargarTipos() {
  try {
    const { data } = await api.get("/api/vehicles/tipos", {
      params: { company_id: companyId() }
    })
    tiposVehiculo.value = data
  } catch { /* no bloquea */ }
}

onMounted(() => {
  cargarVehiculos()
  cargarTipos()
})

// ── Modal crear/editar ──────────────────────────────────────────────────────
const showModal  = ref(false)
const editando   = ref(null)
const guardando  = ref(false)
const form       = ref({})
const busqProp   = ref("")
const propSugerencias = ref([])

function resetForm() {
  form.value = {
    placa: "", vehicle_type_id: null,
    marca: "", modelo: "", anio: null, color: "", km_actual: 0,
    propietario_id: null,
    propietario_nombre: "", propietario_documento: "",
    propietario_telefono: "", propietario_email: "",
  }
  busqProp.value = ""
  propSugerencias.value = []
}

function abrirCrear() {
  editando.value = null
  resetForm()
  showModal.value = true
}

function abrirEditar(v) {
  editando.value = v
  form.value = {
    placa:               v.placa,
    vehicle_type_id:     v.vehicle_type_id,
    marca:               v.marca || "",
    modelo:              v.modelo || "",
    anio:                v.anio,
    color:               v.color || "",
    km_actual:           v.km_actual || 0,
    propietario_id:      v.propietario_id,
    propietario_nombre:  v.propietario_nombre || "",
    propietario_documento: v.propietario_documento || "",
    propietario_telefono: v.propietario_telefono || "",
    propietario_email:   v.propietario_email || "",
  }
  busqProp.value = v.propietario_nombre || ""
  propSugerencias.value = []
  showModal.value = true
}

function abrirDetalle(v) {
  abrirEditar(v)
}

let propTimer = null
async function buscarPropietarios() {
  clearTimeout(propTimer)
  if (!busqProp.value || busqProp.value.length < 2) { propSugerencias.value = []; return }
  propTimer = setTimeout(async () => {
    try {
      const { data } = await api.get("/api/vehicles/propietarios", {
        params: { company_id: companyId(), q: busqProp.value }
      })
      propSugerencias.value = data.slice(0, 6)
    } catch { /* silencioso */ }
  }, 300)
}

function seleccionarPropietario(p) {
  form.value.propietario_id        = p.id
  form.value.propietario_nombre    = p.nombre
  form.value.propietario_documento = p.documento || ""
  form.value.propietario_telefono  = p.telefono  || ""
  form.value.propietario_email     = p.email     || ""
  busqProp.value       = p.nombre
  propSugerencias.value = []
}

function limpiarPropietario() {
  form.value.propietario_id        = null
  form.value.propietario_nombre    = ""
  form.value.propietario_documento = ""
  form.value.propietario_telefono  = ""
  form.value.propietario_email     = ""
  busqProp.value = ""
}

async function guardar() {
  if (!form.value.placa?.trim()) { showToast("La placa es requerida", "warning"); return }
  guardando.value = true
  try {
    const payload = { ...form.value, company_id: companyId() }
    if (editando.value) {
      await api.put(`/api/vehicles/${editando.value.id}`, payload)
      showToast("Vehículo actualizado", "success")
    } else {
      await api.post("/api/vehicles/", payload)
      showToast("Vehículo registrado", "success")
    }
    showModal.value = false
    await cargarVehiculos()
  } catch (e) {
    showToast(e.response?.data?.detail || "Error al guardar", "error")
  } finally { guardando.value = false }
}

// ── Historial ───────────────────────────────────────────────────────────────
const showHistorial  = ref(false)
const vehiculoActivo = ref(null)
const historial      = ref([])
const cargandoHist   = ref(false)

async function abrirHistorial(v) {
  vehiculoActivo.value = v
  showHistorial.value  = true
  historial.value      = []
  cargandoHist.value   = true
  try {
    const { data } = await api.get(`/api/vehicles/${v.id}/historial`, {
      params: { company_id: companyId() }
    })
    historial.value = data.historial || []
  } catch { showToast("Error cargando historial", "error") }
  finally { cargandoHist.value = false }
}

function fmtFecha(f) {
  if (!f) return "—"
  return new Date(f).toLocaleString("es-CO", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit"
  })
}
</script>

<style scoped>
.veh-container { padding: 20px; max-width: 1200px; }

/* Header */
.veh-header { display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.veh-title   { font-size: 22px; font-weight: 700; color: #1e293b; margin: 0 0 4px;
  display: flex; align-items: center; gap: 8px; }
.veh-sub     { font-size: 13px; color: #64748b; margin: 0; }

/* Buscador */
.veh-search-bar { margin-bottom: 16px; }
.search-input-wrap {
  position: relative; max-width: 480px;
  display: flex; align-items: center;
}
.search-input-wrap .bi-search {
  position: absolute; left: 12px; color: #94a3b8; font-size: 15px;
}
.search-input {
  width: 100%; padding: 10px 36px 10px 36px;
  border: 1px solid #e2e8f0; border-radius: 10px;
  font-size: 14px; outline: none;
  transition: border-color .15s;
}
.search-input:focus { border-color: #1e3a5f; }
.search-clear {
  position: absolute; right: 10px; background: none; border: none;
  cursor: pointer; color: #94a3b8; font-size: 13px;
}

/* Tabla */
.veh-table-card {
  background: #fff; border-radius: 14px;
  box-shadow: 0 1px 6px rgba(0,0,0,.08); overflow: hidden;
}
.veh-loading { padding: 40px; text-align: center; color: #94a3b8; }
.veh-table   { width: 100%; border-collapse: collapse; font-size: 13px; }
.veh-table th {
  background: #f8fafc; color: #475569; font-weight: 600;
  font-size: 11px; text-transform: uppercase; letter-spacing: .4px;
  padding: 11px 12px; border-bottom: 1px solid #e2e8f0;
}
.veh-table td   { padding: 10px 12px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.veh-row        { cursor: pointer; transition: background .1s; }
.veh-row:hover td { background: #f8fafc; }

.placa-badge {
  display: inline-block; background: #1e3a5f; color: #fff;
  border-radius: 6px; padding: 3px 10px; font-weight: 700;
  font-size: 13px; letter-spacing: 1px;
}
.sub-text       { font-size: 11px; color: #94a3b8; margin-top: 2px; }
.sin-propietario { color: #cbd5e1; font-style: italic; font-size: 12px; }
.text-center    { text-align: center; }
.py-4           { padding-top: 32px; padding-bottom: 32px; }

.ord-badge {
  display: inline-flex; align-items: center; gap: 4px;
  background: #f1f5f9; border-radius: 20px;
  padding: 2px 8px; font-size: 11px; margin: 0 2px; color: #475569;
}
.ord-park { background: #eff6ff; color: #2563eb; }

.estado-badge { display: inline-block; border-radius: 20px; padding: 2px 10px; font-size: 11px; font-weight: 600; }
.estado-badge.activo   { background: #dcfce7; color: #16a34a; }
.estado-badge.inactivo { background: #fee2e2; color: #dc2626; }

.action-row { display: flex; gap: 6px; justify-content: center; }
.btn-icon {
  background: #f1f5f9; border: none; border-radius: 8px;
  padding: 6px 9px; cursor: pointer; color: #475569;
  transition: background .15s;
}
.btn-icon:hover { background: #e2e8f0; color: #1e3a5f; }

/* Modales */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.45);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000; padding: 16px;
}
.modal-box {
  background: #fff; border-radius: 16px;
  width: 100%; max-width: 640px;
  max-height: 92vh; display: flex; flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,.2);
}
.modal-wide { max-width: 760px; }
.modal-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  padding: 20px 24px 16px; border-bottom: 1px solid #f1f5f9;
}
.modal-header h3 { margin: 0; font-size: 17px; color: #1e293b; display: flex; align-items: center; gap: 8px; }
.modal-sub  { margin: 4px 0 0; font-size: 12px; color: #64748b; }
.modal-body { padding: 20px 24px; overflow-y: auto; flex: 1; }
.modal-footer {
  padding: 14px 24px; border-top: 1px solid #f1f5f9;
  display: flex; justify-content: flex-end; gap: 10px;
}
.btn-x { background: none; border: none; cursor: pointer; color: #64748b; font-size: 16px; }
.btn-x:hover { color: #1e293b; }

.section-title {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .6px; color: #64748b; margin-bottom: 12px;
}
.form-grid2  { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.fg          { display: flex; flex-direction: column; gap: 4px; }
.fg-full     { grid-column: 1 / -1; }
.fg label    { font-size: 12px; font-weight: 600; color: #475569; }
.form-control, .form-select {
  border: 1px solid #e2e8f0; border-radius: 8px;
  padding: 8px 12px; font-size: 13px; outline: none;
  transition: border-color .15s;
}
.form-control:focus, .form-select:focus { border-color: #1e3a5f; }
.form-control:disabled { background: #f8fafc; cursor: not-allowed; }

/* Propietario */
.search-prop-wrap { position: relative; }
.prop-dropdown {
  position: absolute; z-index: 50; top: calc(100% + 4px); left: 0; right: 0;
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,.12); overflow: hidden;
}
.prop-option {
  display: flex; flex-direction: column; gap: 2px;
  padding: 10px 14px; cursor: pointer; transition: background .1s;
}
.prop-option:hover { background: #f8fafc; }
.prop-seleccionado { border: 1.5px solid #1e3a5f; border-radius: 10px; padding: 12px; }
.prop-id-hint {
  font-size: 12px; color: #2563eb; margin-top: 8px;
  display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
}
.link-btn {
  background: none; border: none; color: #ef4444; cursor: pointer;
  font-size: 12px; text-decoration: underline;
}

/* Historial */
.hist-list   { display: flex; flex-direction: column; gap: 12px; }
.hist-item   { display: flex; gap: 12px; }
.hist-icon   {
  width: 36px; height: 36px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 15px; flex-shrink: 0;
}
.hist-icon.taller  { background: #dbeafe; color: #1d4ed8; }
.hist-icon.parking { background: #dcfce7; color: #16a34a; }
.hist-body   { flex: 1; }
.hist-top    { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.hist-orden  { font-weight: 700; font-size: 13px; color: #1e293b; }
.hist-origen-badge {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  border-radius: 20px; padding: 1px 8px;
}
.hist-origen-badge.taller  { background: #dbeafe; color: #1d4ed8; }
.hist-origen-badge.parking { background: #dcfce7; color: #16a34a; }
.hist-estado { font-size: 11px; color: #64748b; }
.hist-fecha  { font-size: 11px; color: #94a3b8; margin: 2px 0 4px; }
.hist-desc   { font-size: 12px; color: #475569; }

/* Botones */
.btn-primary {
  background: #1e3a5f; color: #fff; border: none;
  border-radius: 10px; padding: 10px 20px;
  font-size: 13px; font-weight: 600; cursor: pointer;
  display: flex; align-items: center; gap: 6px;
  transition: background .15s;
}
.btn-primary:hover    { background: #162d4a; }
.btn-primary:disabled { opacity: .6; cursor: not-allowed; }
.btn-secondary {
  background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0;
  border-radius: 10px; padding: 10px 20px;
  font-size: 13px; font-weight: 600; cursor: pointer;
}
.btn-secondary:hover { background: #e2e8f0; }

@keyframes spin { to { transform: rotate(360deg); } }
.spin { display: inline-block; animation: spin .7s linear infinite; }

/* Responsive móvil */
@media (max-width: 768px) {
  .veh-container  { padding: 12px; }
  .form-grid2     { grid-template-columns: 1fr; }
  .veh-table th:nth-child(4),
  .veh-table td:nth-child(4) { display: none; }
  .modal-box { max-width: 100%; border-radius: 12px; }
}
@media (max-width: 576px) {
  .veh-table th:nth-child(3),
  .veh-table td:nth-child(3),
  .veh-table th:nth-child(5),
  .veh-table td:nth-child(5) { display: none; }
  .veh-title { font-size: 18px; }
}
</style>
