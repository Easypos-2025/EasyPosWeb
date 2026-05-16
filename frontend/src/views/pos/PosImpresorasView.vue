<template>
  <div class="crud-view">
    <div class="crud-header">
      <div>
        <h5 class="crud-titulo">Impresoras</h5>
        <p class="crud-sub">Configura las impresoras de cocina, barra y caja</p>
      </div>
      <button class="btn-nuevo" @click="abrirModal()">
        <i class="bi bi-plus-lg me-1"></i>Nueva Impresora
      </button>
    </div>

    <div v-if="loading" class="estado-carga"><div class="spinner-border spinner-border-sm text-primary"></div></div>
    <div v-else-if="!items.length" class="estado-vacio">
      <i class="bi bi-printer"></i>
      <p>No hay impresoras configuradas.</p>
    </div>
    <table v-else class="tabla">
      <thead>
        <tr>
          <th>Nombre</th><th>Tipo</th><th>IP</th><th>Puerto</th><th>Estado</th><th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="imp in items" :key="imp.id" :class="{ 'tr-inactiva': !imp.activa }">
          <td><i class="bi bi-printer me-2 text-primary"></i>{{ imp.nombre }}</td>
          <td><span class="badge-tipo">{{ imp.tipo || '—' }}</span></td>
          <td class="text-mono">{{ imp.ip || '—' }}</td>
          <td class="text-mono">{{ imp.puerto }}</td>
          <td><span :class="imp.activa ? 'badge-activa' : 'badge-inactiva'">{{ imp.activa ? 'Activa' : 'Inactiva' }}</span></td>
          <td class="td-acciones">
            <button class="btn-icono" @click="abrirModal(imp)"><i class="bi bi-pencil"></i></button>
            <button class="btn-icono btn-icono--danger" @click="eliminar(imp.id)"><i class="bi bi-trash"></i></button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="modal.visible" class="modal-overlay" @click.self="cerrarModal">
      <div class="modal-card">
        <div class="modal-hdr">
          <span><i class="bi bi-printer me-2"></i>{{ modal.id ? 'Editar' : 'Nueva' }} Impresora</span>
          <button class="btn-x" @click="cerrarModal"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-body">
          <div class="campo"><label>Nombre *</label>
            <input v-model="modal.nombre" class="inp" placeholder="Ej: Cocina, Barra, Caja" />
          </div>
          <div class="campo-row">
            <div class="campo"><label>Tipo</label>
              <select v-model="modal.tipo" class="inp">
                <option value="">— Seleccionar —</option>
                <option value="cocina">Cocina</option>
                <option value="barra">Barra</option>
                <option value="caja">Caja</option>
                <option value="otro">Otro</option>
              </select>
            </div>
            <div class="campo"><label>Puerto</label>
              <input type="number" v-model.number="modal.puerto" class="inp" placeholder="9100" />
            </div>
          </div>
          <div class="campo"><label>IP / Dirección</label>
            <input v-model="modal.ip" class="inp" placeholder="192.168.1.x" />
          </div>
          <div class="campo-check">
            <input type="checkbox" v-model="modal.activa" :true-value="1" :false-value="0" id="chkActiva" />
            <label for="chkActiva">Activa</label>
          </div>
        </div>
        <div class="modal-ftr">
          <button class="btn-cancel" @click="cerrarModal">Cancelar</button>
          <button class="btn-save" :disabled="guardando || !modal.nombre" @click="guardar">
            <span v-if="guardando"><span class="spinner-border spinner-border-sm me-1"></span></span>
            <i v-else class="bi bi-check-lg me-1"></i>Guardar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/apis.js'

const BASE = '/api/pos-catalogo/impresoras'
const items   = ref([])
const loading = ref(true)
const guardando = ref(false)
const modal = ref({ visible:false, id:null, nombre:'', tipo:'', ip:'', puerto:9100, activa:1 })

onMounted(cargar)
async function cargar() {
  loading.value = true
  try { const {data} = await api.get(BASE); items.value = data } catch { items.value=[] }
  finally { loading.value = false }
}
function abrirModal(imp=null) {
  modal.value = imp
    ? { visible:true, id:imp.id, nombre:imp.nombre, tipo:imp.tipo||'', ip:imp.ip||'', puerto:imp.puerto, activa:imp.activa }
    : { visible:true, id:null, nombre:'', tipo:'', ip:'', puerto:9100, activa:1 }
}
function cerrarModal() { modal.value.visible=false }
async function guardar() {
  if(!modal.value.nombre) return
  guardando.value=true
  try {
    const p={nombre:modal.value.nombre,tipo:modal.value.tipo,ip:modal.value.ip,puerto:modal.value.puerto,activa:modal.value.activa}
    if(modal.value.id) await api.put(`${BASE}/${modal.value.id}`,p)
    else await api.post(BASE,p)
    cerrarModal(); await cargar()
  } catch { alert('Error al guardar') }
  finally { guardando.value=false }
}
async function eliminar(id) {
  if(!confirm('¿Desactivar esta impresora?')) return
  try { await api.delete(`${BASE}/${id}`); await cargar() } catch { alert('Error') }
}
</script>

<style scoped>
.crud-view { padding:0; }
.crud-header { display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px; }
.crud-titulo { font-weight:700;font-size:16px;color:#1e3a5f;margin:0; }
.crud-sub    { font-size:13px;color:#64748b;margin:2px 0 0; }
.btn-nuevo   { display:flex;align-items:center;gap:6px;background:linear-gradient(90deg,#1e3a5f,#1d4ed8);color:#fff;border:none;border-radius:8px;padding:9px 16px;font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap; }
.estado-carga,.estado-vacio { display:flex;flex-direction:column;align-items:center;gap:10px;padding:60px 20px;color:#94a3b8;font-size:14px; }
.estado-vacio i { font-size:40px; }
.tabla  { width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.06); }
.tabla th { background:#f8fafc;padding:10px 14px;font-size:12px;font-weight:700;color:#64748b;text-align:left;text-transform:uppercase;letter-spacing:.4px; }
.tabla td { padding:12px 14px;font-size:13px;color:#1e3a5f;border-top:1px solid #f1f5f9; }
.tr-inactiva { opacity:.5; }
.text-mono { font-family:monospace;font-size:12px; }
.badge-tipo    { background:#eff6ff;color:#1d4ed8;font-size:11px;padding:2px 8px;border-radius:10px;font-weight:600;text-transform:capitalize; }
.badge-activa  { background:#dcfce7;color:#16a34a;font-size:11px;padding:2px 8px;border-radius:10px;font-weight:600; }
.badge-inactiva{ background:#f1f5f9;color:#94a3b8;font-size:11px;padding:2px 8px;border-radius:10px; }
.td-acciones   { display:flex;gap:6px; }
.btn-icono { background:none;border:1px solid #e2e8f0;border-radius:6px;padding:5px 8px;cursor:pointer;color:#475569;font-size:13px; }
.btn-icono:hover { background:#f0f4ff;color:#1d4ed8;border-color:#1d4ed8; }
.btn-icono--danger:hover { background:#fff1f2;color:#e11d48;border-color:#e11d48; }
.modal-overlay { position:fixed;inset:0;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;z-index:1050; }
.modal-card    { background:#fff;border-radius:16px;width:100%;max-width:440px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.25); }
.modal-hdr     { display:flex;justify-content:space-between;align-items:center;padding:16px 20px;background:linear-gradient(90deg,#1e3a5f,#1d4ed8);color:#fff;font-weight:700;font-size:15px; }
.btn-x         { background:none;border:none;color:#fff;cursor:pointer;font-size:16px;opacity:.8; }
.modal-body    { padding:20px;display:flex;flex-direction:column;gap:12px; }
.campo         { display:flex;flex-direction:column;gap:4px; }
.campo label   { font-size:12px;font-weight:600;color:#475569; }
.campo-row     { display:flex;gap:12px; }
.campo-row .campo { flex:1; }
.inp           { border:1.5px solid #cbd5e1;border-radius:8px;padding:8px 12px;font-size:14px;color:#1e3a5f;outline:none;width:100%; }
.inp:focus     { border-color:#1d4ed8; }
.campo-check   { display:flex;align-items:center;gap:8px;font-size:13px;color:#475569; }
.modal-ftr     { display:flex;gap:10px;justify-content:flex-end;padding:14px 20px;border-top:1px solid #f1f5f9; }
.btn-cancel    { background:#f1f5f9;border:none;border-radius:8px;padding:9px 18px;font-size:14px;cursor:pointer;color:#475569;font-weight:600; }
.btn-save      { background:linear-gradient(90deg,#1e3a5f,#1d4ed8);border:none;border-radius:8px;padding:9px 20px;font-size:14px;font-weight:700;color:#fff;cursor:pointer; }
.btn-save:disabled { opacity:.6;cursor:not-allowed; }
@media(max-width:768px){.crud-header{flex-direction:column;gap:10px;}}
@media(max-width:576px){.campo-row{flex-direction:column;}}
</style>
