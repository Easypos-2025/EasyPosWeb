<template>
  <div class="crud-view">
    <div class="crud-header">
      <div>
        <h5 class="crud-titulo">Cajas Registradoras</h5>
        <p class="crud-sub">Define las cajas disponibles (principal y auxiliares)</p>
      </div>
      <button class="btn-nuevo" @click="abrirModal()">
        <i class="bi bi-plus-lg me-1"></i>Nueva Caja
      </button>
    </div>

    <div v-if="loading" class="estado-carga"><div class="spinner-border spinner-border-sm text-primary"></div></div>
    <div v-else-if="!items.length" class="estado-vacio">
      <i class="bi bi-cash-stack"></i>
      <p>No hay cajas configuradas.</p>
    </div>
    <div v-else class="cajas-grid">
      <div v-for="caja in items" :key="caja.id"
           class="caja-card"
           :class="{ 'caja-card--principal': caja.tipo==='principal', 'caja-card--inactiva': !caja.activa }">
        <div class="caja-top">
          <i class="bi" :class="caja.tipo==='principal' ? 'bi-cash-coin' : 'bi-cash-stack'"></i>
          <span class="caja-tipo-badge">{{ caja.tipo }}</span>
        </div>
        <div class="caja-nombre">{{ caja.nombre }}</div>
        <div v-if="!caja.activa" class="caja-inactiva">Inactiva</div>
        <div class="caja-acciones">
          <button class="btn-icono" @click="abrirModal(caja)"><i class="bi bi-pencil"></i></button>
          <button class="btn-icono btn-icono--danger" @click="eliminar(caja.id)"><i class="bi bi-trash"></i></button>
        </div>
      </div>
    </div>

    <div v-if="modal.visible" class="modal-overlay" @click.self="cerrarModal">
      <div class="modal-card">
        <div class="modal-hdr">
          <span><i class="bi bi-cash-stack me-2"></i>{{ modal.id ? 'Editar' : 'Nueva' }} Caja</span>
          <button class="btn-x" @click="cerrarModal"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-body">
          <div class="campo"><label>Nombre *</label>
            <input v-model="modal.nombre" class="inp" placeholder="Ej: Caja Principal, Caja Bar" />
          </div>
          <div class="campo"><label>Tipo</label>
            <div class="radio-group">
              <label class="radio-opt" :class="{ 'radio-opt--sel': modal.tipo==='principal' }">
                <input type="radio" v-model="modal.tipo" value="principal" /> Principal
              </label>
              <label class="radio-opt" :class="{ 'radio-opt--sel': modal.tipo==='auxiliar' }">
                <input type="radio" v-model="modal.tipo" value="auxiliar" /> Auxiliar
              </label>
            </div>
            <p v-if="modal.tipo==='principal'" class="tip-principal">
              <i class="bi bi-info-circle me-1"></i>Solo puede haber una caja principal. Las demás se cambiarán a auxiliar.
            </p>
          </div>
          <div class="campo-check">
            <input type="checkbox" v-model="modal.activa" :true-value="1" :false-value="0" id="chkA" />
            <label for="chkA">Activa</label>
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

const BASE = '/api/pos-catalogo/cajas'
const items    = ref([])
const loading  = ref(true)
const guardando= ref(false)
const modal    = ref({ visible:false, id:null, nombre:'', tipo:'auxiliar', activa:1 })

onMounted(cargar)
async function cargar() {
  loading.value=true
  try { const{data}=await api.get(BASE); items.value=data } catch { items.value=[] }
  finally { loading.value=false }
}
function abrirModal(c=null) {
  modal.value=c
    ? { visible:true, id:c.id, nombre:c.nombre, tipo:c.tipo, activa:c.activa }
    : { visible:true, id:null, nombre:'', tipo:'auxiliar', activa:1 }
}
function cerrarModal() { modal.value.visible=false }
async function guardar() {
  if(!modal.value.nombre) return
  guardando.value=true
  try {
    const p={nombre:modal.value.nombre,tipo:modal.value.tipo,activa:modal.value.activa}
    if(modal.value.id) await api.put(`${BASE}/${modal.value.id}`,p)
    else await api.post(BASE,p)
    cerrarModal(); await cargar()
  } catch { alert('Error al guardar') }
  finally { guardando.value=false }
}
async function eliminar(id) {
  if(!confirm('¿Desactivar esta caja?')) return
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
.cajas-grid { display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px; }
.caja-card  { background:#fff;border:2px solid #e2e8f0;border-radius:12px;padding:16px;text-align:center;position:relative; }
.caja-card--principal { border-color:#1d4ed8;background:#f0f4ff; }
.caja-card--inactiva  { opacity:.5; }
.caja-top { display:flex;justify-content:center;align-items:center;gap:8px;font-size:24px;color:#1d4ed8;margin-bottom:8px; }
.caja-tipo-badge { font-size:10px;font-weight:700;text-transform:uppercase;background:#eff6ff;color:#1d4ed8;border-radius:10px;padding:2px 8px; }
.caja-nombre  { font-weight:700;font-size:15px;color:#1e3a5f;margin-bottom:8px; }
.caja-inactiva{ font-size:11px;color:#94a3b8;margin-bottom:6px; }
.caja-acciones{ display:flex;justify-content:center;gap:6px;margin-top:10px; }
.btn-icono { background:none;border:1px solid #e2e8f0;border-radius:6px;padding:5px 8px;cursor:pointer;color:#475569;font-size:13px; }
.btn-icono:hover { background:#f0f4ff;color:#1d4ed8;border-color:#1d4ed8; }
.btn-icono--danger:hover { background:#fff1f2;color:#e11d48;border-color:#e11d48; }
.modal-overlay { position:fixed;inset:0;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;z-index:1050; }
.modal-card    { background:#fff;border-radius:16px;width:100%;max-width:420px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.25); }
.modal-hdr     { display:flex;justify-content:space-between;align-items:center;padding:16px 20px;background:linear-gradient(90deg,#1e3a5f,#1d4ed8);color:#fff;font-weight:700;font-size:15px; }
.btn-x         { background:none;border:none;color:#fff;cursor:pointer;font-size:16px;opacity:.8; }
.modal-body    { padding:20px;display:flex;flex-direction:column;gap:12px; }
.campo         { display:flex;flex-direction:column;gap:4px; }
.campo label   { font-size:12px;font-weight:600;color:#475569; }
.inp           { border:1.5px solid #cbd5e1;border-radius:8px;padding:8px 12px;font-size:14px;color:#1e3a5f;outline:none;width:100%; }
.inp:focus     { border-color:#1d4ed8; }
.radio-group   { display:flex;gap:10px;margin-top:4px; }
.radio-opt     { display:flex;align-items:center;gap:6px;border:2px solid #e2e8f0;border-radius:8px;padding:8px 14px;cursor:pointer;font-size:13px;font-weight:600;color:#64748b;transition:.15s; }
.radio-opt--sel{ border-color:#1d4ed8;color:#1d4ed8;background:#eff6ff; }
.radio-opt input{ display:none; }
.tip-principal { font-size:11px;color:#f59e0b;background:#fffbeb;border-radius:6px;padding:6px 8px;margin:0; }
.campo-check   { display:flex;align-items:center;gap:8px;font-size:13px;color:#475569; }
.modal-ftr     { display:flex;gap:10px;justify-content:flex-end;padding:14px 20px;border-top:1px solid #f1f5f9; }
.btn-cancel    { background:#f1f5f9;border:none;border-radius:8px;padding:9px 18px;font-size:14px;cursor:pointer;color:#475569;font-weight:600; }
.btn-save      { background:linear-gradient(90deg,#1e3a5f,#1d4ed8);border:none;border-radius:8px;padding:9px 20px;font-size:14px;font-weight:700;color:#fff;cursor:pointer; }
.btn-save:disabled { opacity:.6;cursor:not-allowed; }
@media(max-width:768px){.crud-header{flex-direction:column;gap:10px;}}
</style>
