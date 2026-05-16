<template>
  <div class="crud-view">
    <div class="crud-header">
      <div>
        <h5 class="crud-titulo">Categorías de Artículos</h5>
        <p class="crud-sub">Organiza tu catálogo por categorías (Entradas, Principios, Bebidas, Servicios…)</p>
      </div>
      <button class="btn-nuevo" @click="abrirModal()">
        <i class="bi bi-plus-lg me-1"></i>Nueva Categoría
      </button>
    </div>

    <div v-if="loading" class="estado-carga">
      <div class="spinner-border spinner-border-sm text-primary"></div>
    </div>
    <div v-else-if="!items.length" class="estado-vacio">
      <i class="bi bi-tags"></i>
      <p>No hay categorías. Crea la primera para organizar tu catálogo.</p>
    </div>
    <div v-else class="cats-grid">
      <div v-for="cat in items" :key="cat.id" class="cat-card" :class="{ 'cat-card--inactiva': !cat.is_active }">
        <div class="cat-icono" :style="{ background: cat.color + '22', color: cat.color }">
          <i :class="`bi ${cat.icon}`"></i>
        </div>
        <div class="cat-info">
          <span class="cat-nombre">{{ cat.name }}</span>
          <span class="cat-desc">{{ cat.description || '—' }}</span>
          <span v-if="!cat.is_active" class="badge-inactiva">Inactiva</span>
        </div>
        <div class="cat-acciones">
          <button class="btn-icono" @click="abrirModal(cat)"><i class="bi bi-pencil"></i></button>
          <button class="btn-icono btn-icono--danger" @click="eliminar(cat.id)"><i class="bi bi-trash"></i></button>
        </div>
      </div>
    </div>

    <div v-if="modal.visible" class="modal-overlay" @click.self="cerrarModal">
      <div class="modal-card">
        <div class="modal-hdr">
          <span>{{ modal.id ? 'Editar' : 'Nueva' }} Categoría</span>
          <button class="btn-x" @click="cerrarModal"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-body">
          <div class="campo"><label>Nombre *</label>
            <input v-model="modal.name" class="inp" placeholder="Ej: Entradas, Bebidas…" />
          </div>
          <div class="campo"><label>Descripción</label>
            <input v-model="modal.description" class="inp" placeholder="Opcional" />
          </div>
          <div class="campo-row">
            <div class="campo">
              <label>Color</label>
              <input type="color" v-model="modal.color" class="inp-color" />
            </div>
            <div class="campo">
              <label>Ícono Bootstrap</label>
              <input v-model="modal.icon" class="inp" placeholder="bi-tag" />
            </div>
          </div>
          <div class="campo-check">
            <input type="checkbox" v-model="modal.is_active" :true-value="1" :false-value="0" id="chkActiva" />
            <label for="chkActiva">Activa</label>
          </div>
        </div>
        <div class="modal-ftr">
          <button class="btn-cancel" @click="cerrarModal">Cancelar</button>
          <button class="btn-save" :disabled="guardando || !modal.name" @click="guardar">
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

const BASE = '/api/pos-catalogo/categorias'
const items    = ref([])
const loading  = ref(true)
const guardando= ref(false)
const modal    = ref({ visible:false, id:null, name:'', description:'', color:'#1d4ed8', icon:'bi-tag', is_active:1 })

onMounted(cargar)

async function cargar() {
  loading.value = true
  try { const{data} = await api.get(BASE); items.value = data } catch { items.value=[] }
  finally { loading.value = false }
}
function abrirModal(cat=null) {
  modal.value = cat
    ? { visible:true, id:cat.id, name:cat.name, description:cat.description||'', color:cat.color, icon:cat.icon, is_active:cat.is_active }
    : { visible:true, id:null, name:'', description:'', color:'#1d4ed8', icon:'bi-tag', is_active:1 }
}
function cerrarModal() { modal.value.visible=false }
async function guardar() {
  if (!modal.value.name) return
  guardando.value = true
  try {
    const p={ name:modal.value.name, description:modal.value.description, color:modal.value.color, icon:modal.value.icon, is_active:modal.value.is_active }
    if (modal.value.id) await api.put(`${BASE}/${modal.value.id}`, p)
    else await api.post(BASE, p)
    cerrarModal(); await cargar()
  } catch { alert('Error al guardar') }
  finally { guardando.value=false }
}
async function eliminar(id) {
  if (!confirm('¿Desactivar esta categoría?')) return
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
.cats-grid { display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px; }
.cat-card  { display:flex;align-items:center;gap:12px;background:#fff;border:2px solid #e2e8f0;border-radius:12px;padding:14px;transition:border-color .15s; }
.cat-card:hover { border-color:#1d4ed8; }
.cat-card--inactiva { opacity:.55; }
.cat-icono { width:44px;height:44px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0; }
.cat-info  { flex:1;display:flex;flex-direction:column;gap:2px; }
.cat-nombre{ font-weight:700;font-size:14px;color:#1e3a5f; }
.cat-desc  { font-size:12px;color:#64748b; }
.badge-inactiva { display:inline-block;font-size:10px;background:#f1f5f9;color:#94a3b8;border-radius:4px;padding:1px 6px; }
.cat-acciones { display:flex;gap:6px; }
.btn-icono { background:none;border:1px solid #e2e8f0;border-radius:6px;padding:5px 8px;cursor:pointer;color:#475569;font-size:13px; }
.btn-icono:hover { background:#f0f4ff;color:#1d4ed8;border-color:#1d4ed8; }
.btn-icono--danger:hover { background:#fff1f2;color:#e11d48;border-color:#e11d48; }
.modal-overlay { position:fixed;inset:0;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;z-index:1050; }
.modal-card { background:#fff;border-radius:16px;width:100%;max-width:440px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.25); }
.modal-hdr  { display:flex;justify-content:space-between;align-items:center;padding:16px 20px;background:linear-gradient(90deg,#1e3a5f,#1d4ed8);color:#fff;font-weight:700;font-size:15px; }
.btn-x      { background:none;border:none;color:#fff;cursor:pointer;font-size:16px;opacity:.8; }
.modal-body { padding:20px;display:flex;flex-direction:column;gap:12px; }
.campo      { display:flex;flex-direction:column;gap:4px; }
.campo label{ font-size:12px;font-weight:600;color:#475569; }
.campo-row  { display:flex;gap:12px; }
.campo-row .campo { flex:1; }
.inp        { border:1.5px solid #cbd5e1;border-radius:8px;padding:8px 12px;font-size:14px;color:#1e3a5f;outline:none;width:100%; }
.inp:focus  { border-color:#1d4ed8; }
.inp-color  { width:48px;height:36px;border:1.5px solid #cbd5e1;border-radius:8px;padding:2px;cursor:pointer; }
.campo-check { display:flex;align-items:center;gap:8px;font-size:13px;color:#475569; }
.modal-ftr  { display:flex;gap:10px;justify-content:flex-end;padding:14px 20px;border-top:1px solid #f1f5f9; }
.btn-cancel { background:#f1f5f9;border:none;border-radius:8px;padding:9px 18px;font-size:14px;cursor:pointer;color:#475569;font-weight:600; }
.btn-save   { background:linear-gradient(90deg,#1e3a5f,#1d4ed8);border:none;border-radius:8px;padding:9px 20px;font-size:14px;font-weight:700;color:#fff;cursor:pointer; }
.btn-save:disabled { opacity:.6;cursor:not-allowed; }
@media(max-width:768px){.crud-header{flex-direction:column;gap:10px;}.cats-grid{grid-template-columns:1fr;}}
@media(max-width:576px){.campo-row{flex-direction:column;}}
</style>
