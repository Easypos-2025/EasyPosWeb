<template>
  <div class="cp-page">
    <div class="cp-head">
      <div>
        <h2 class="cp-title"><i class="bi bi-diagram-3 me-2"></i>{{ moduleName || 'Categorías de Productos' }}</h2>
        <p class="cp-sub">Agrupan los insumos. Las de <b>armado</b> son las opciones que el cliente escoge en los platos de armado y en el menú del día.</p>
      </div>
      <button class="cp-btn-new" @click="abrir()"><i class="bi bi-plus-lg me-1"></i>Nueva categoría</button>
    </div>

    <div class="cp-toolbar">
      <div class="cp-tabs">
        <button v-for="t in TIPOS" :key="t.v" :class="['cp-tab', { active: tipo === t.v }]" @click="tipo = t.v; cargar()">{{ t.l }}</button>
      </div>
      <div class="cp-search">
        <i class="bi bi-search"></i>
        <input v-model="q" @input="deb" :placeholder="`Buscar ${moduleName || 'categoría'}...`" maxlength="60" />
      </div>
    </div>

    <div v-if="loading" class="cp-state"><div class="spinner-border spinner-border-sm text-primary"></div></div>
    <div v-else-if="!rows.length" class="cp-state cp-empty">
      <i class="bi bi-diagram-3"></i><p>No hay categorías{{ q ? ' con ese nombre' : '' }}.</p>
    </div>
    <div v-else class="cp-grid">
      <div v-for="c in rows" :key="c.id" :class="['cp-card', { 'cp-card--off': !c.is_active, 'cp-card--armado': c.is_assembly }]">
        <div class="cp-card-top">
          <span class="cp-code">#{{ c.id }}</span>
          <span v-if="c.is_assembly" class="cp-chip cp-chip--armado"><i class="bi bi-sliders"></i> Armado</span>
          <span v-else class="cp-chip">Normal</span>
          <span v-if="!c.is_active" class="cp-chip cp-chip--off">Inactiva</span>
        </div>
        <div class="cp-name">{{ c.name }}</div>
        <div class="cp-stats">
          <span title="Insumos activos en la categoría"><i class="bi bi-box-seam"></i> {{ c.insumos }} insumos</span>
          <span v-if="c.is_assembly" title="Insumos marcados Armar Plato"><i class="bi bi-check2-square"></i> {{ c.insumos_armado }} de armado</span>
          <span v-if="c.platos" title="Platos que la usan en su armado"><i class="bi bi-egg-fried"></i> {{ c.platos }} platos</span>
        </div>
        <div v-if="c.is_assembly && (c.require_selection || c.print_assembly_changes_only)" class="cp-flags">
          <span v-if="c.require_selection">Exige selección</span>
          <span v-if="c.print_assembly_changes_only">Imprime solo cambios</span>
        </div>
        <div class="cp-actions">
          <button class="cp-ico" title="Editar" @click="abrir(c)"><i class="bi bi-pencil"></i></button>
          <button v-if="c.is_active" class="cp-ico cp-ico--danger" title="Desactivar" @click="desactivar(c)"><i class="bi bi-slash-circle"></i></button>
        </div>
      </div>
    </div>

    <!-- Modal crear / editar -->
    <div v-if="modal.show" class="cp-ov" @click.self="modal.show = false">
      <div class="cp-modal">
        <div class="cp-modal-hdr">
          <span>{{ modal.id ? `Editar ${moduleName || 'categoría'} #${modal.id}` : `Nueva ${moduleName || 'categoría'}` }}</span>
          <button class="cp-x" @click="modal.show = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="cp-modal-body">
          <label class="cp-lbl">Nombre *</label>
          <input v-model="modal.name" class="cp-inp" maxlength="100" placeholder="Ej: 02 PROTEINAS" @keyup.enter="guardar" />

          <label class="cp-switch">
            <input type="checkbox" v-model="modal.is_assembly" />
            <span><b>Categoría de armado</b><small>Sus insumos se ofrecen como opciones en los platos de armado y en el menú del día.</small></span>
          </label>
          <template v-if="modal.is_assembly">
            <label class="cp-switch">
              <input type="checkbox" v-model="modal.require_selection" />
              <span>Exigir selección</span>
            </label>
            <label class="cp-switch">
              <input type="checkbox" v-model="modal.print_assembly_changes_only" />
              <span>Imprimir el armado solo si hay cambios</span>
            </label>
          </template>
          <label class="cp-switch">
            <input type="checkbox" v-model="modal.is_active" />
            <span>Activa</span>
          </label>
        </div>
        <div class="cp-modal-ftr">
          <button class="cp-btn cp-btn--sec" @click="modal.show = false">Cancelar</button>
          <button class="cp-btn" :disabled="guardando || !modal.name.trim()" @click="guardar">
            <span v-if="guardando" class="spinner-border spinner-border-sm me-1"></span>
            <i v-else class="bi bi-check-lg me-1"></i>Guardar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/services/apis'
import Swal from 'sweetalert2'
import { showToast } from '@/utils/toast'
import { useModuleName } from '@/composables/useModuleName'

const BASE = '/api/pos-catalogo/categorias-productos'
const TIPOS = [{ v: 'todas', l: 'Todas' }, { v: 'armado', l: 'De armado' }, { v: 'normal', l: 'Normales' }]
const { moduleName } = useModuleName()

const rows = ref([])
const loading = ref(true)
const guardando = ref(false)
const tipo = ref('todas')
const q = ref('')
const modal = reactive({ show: false, id: null, name: '', is_assembly: false, is_active: true,
                         require_selection: false, print_assembly_changes_only: false })
let t = null, seq = 0

async function cargar() {
  const my = ++seq
  loading.value = true
  try {
    const { data } = await api.get(BASE, { params: { tipo: tipo.value, q: q.value.trim() || undefined } })
    if (my === seq) rows.value = data
  } catch (e) {
    if (my === seq) showToast(e?.response?.data?.detail || 'Error cargando categorías', 'error')
  } finally { if (my === seq) loading.value = false }
}
const deb = () => { clearTimeout(t); t = setTimeout(cargar, 250) }

function abrir(c = null) {
  Object.assign(modal, c
    ? { show: true, id: c.id, name: c.name, is_assembly: c.is_assembly, is_active: c.is_active,
        require_selection: c.require_selection, print_assembly_changes_only: c.print_assembly_changes_only }
    : { show: true, id: null, name: '', is_assembly: false, is_active: true,
        require_selection: false, print_assembly_changes_only: false })
}

async function guardar() {
  if (!modal.name.trim() || guardando.value) return
  guardando.value = true
  const body = { name: modal.name.trim(), is_assembly: modal.is_assembly, is_active: modal.is_active,
                 require_selection: modal.is_assembly && modal.require_selection,
                 print_assembly_changes_only: modal.is_assembly && modal.print_assembly_changes_only }
  try {
    if (modal.id) await api.put(`${BASE}/${modal.id}`, body)
    else await api.post(BASE, body)
    showToast('Categoría guardada', 'success')
    modal.show = false
    cargar()
  } catch (e) {
    const d = e?.response?.data?.detail
    showToast(Array.isArray(d) ? 'Revise los datos' : (d || 'Error al guardar'), 'error')
  }
  guardando.value = false
}

async function desactivar(c) {
  const { isConfirmed } = await Swal.fire({
    title: '¿Desactivar la categoría?',
    text: `${c.name} dejará de ofrecerse${c.is_assembly ? ' en el armado y el menú del día' : ''}. Puede reactivarla editándola.`,
    icon: 'warning', showCancelButton: true,
    confirmButtonText: 'Sí, desactivar', cancelButtonText: 'Cancelar', confirmButtonColor: '#e11d48',
  })
  if (!isConfirmed) return
  try { await api.delete(`${BASE}/${c.id}`); showToast('Categoría desactivada', 'success'); cargar() }
  catch (e) { showToast(e?.response?.data?.detail || 'Error al desactivar', 'error') }
}

onMounted(cargar)
</script>

<style scoped>
.cp-page { padding: 20px 24px 32px; }
.cp-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 14px; }
.cp-title { font-size: 22px; font-weight: 800; color: #1e293b; margin: 0; }
.cp-sub { font-size: 13px; color: #64748b; margin: 2px 0 0; max-width: 640px; }
.cp-btn-new { display: inline-flex; align-items: center; background: linear-gradient(90deg,#1e3a5f,#1d4ed8); color: #fff; border: none;
  border-radius: 10px; padding: 10px 18px; font-weight: 700; font-size: 14px; cursor: pointer; white-space: nowrap; }
.cp-toolbar { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-bottom: 14px; }
.cp-tabs { display: flex; background: #f1f5f9; border-radius: 10px; padding: 3px; }
.cp-tab { border: none; background: none; padding: 7px 14px; border-radius: 8px; font-size: 13px; font-weight: 700; color: #64748b; cursor: pointer; }
.cp-tab.active { background: #fff; color: #1d4ed8; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.cp-search { flex: 1; min-width: 200px; max-width: 360px; display: flex; align-items: center; gap: 6px; background: #fff;
  border: 1.5px solid #cbd5e1; border-radius: 10px; padding: 8px 12px; }
.cp-search input { border: none; outline: none; flex: 1; font-size: 14px; min-width: 0; }
.cp-state { display: flex; flex-direction: column; align-items: center; padding: 50px 20px; color: #94a3b8; }
.cp-empty i { font-size: 36px; }
.cp-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 12px; }
.cp-card { background: #fff; border: 1.5px solid #e2e8f0; border-radius: 12px; padding: 12px 14px; display: flex; flex-direction: column; gap: 6px; }
.cp-card--armado { border-color: #c7d2fe; background: #fafaff; }
.cp-card--off { opacity: .55; }
.cp-card-top { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.cp-code { font-size: 12px; font-weight: 800; color: #94a3b8; font-family: ui-monospace, monospace; }
.cp-chip { font-size: 10px; font-weight: 700; border-radius: 10px; padding: 2px 8px; background: #f1f5f9; color: #475569; }
.cp-chip--armado { background: #e0e7ff; color: #4338ca; }
.cp-chip--off { background: #fee2e2; color: #b91c1c; }
.cp-name { font-size: 15px; font-weight: 800; color: #1e3a5f; word-break: break-word; }
.cp-stats { display: flex; flex-wrap: wrap; gap: 10px; font-size: 12px; color: #64748b; }
.cp-flags { display: flex; flex-wrap: wrap; gap: 6px; }
.cp-flags span { font-size: 11px; color: #92400e; background: #fef3c7; border-radius: 8px; padding: 1px 7px; }
.cp-actions { display: flex; justify-content: flex-end; gap: 6px; margin-top: auto; }
.cp-ico { background: none; border: 1px solid #e2e8f0; border-radius: 8px; padding: 5px 9px; cursor: pointer; color: #475569; }
.cp-ico:hover { border-color: #1d4ed8; color: #1d4ed8; }
.cp-ico--danger:hover { border-color: #e11d48; color: #e11d48; }
.cp-ov { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 1050; padding: 16px; }
.cp-modal { background: #fff; border-radius: 16px; width: 100%; max-width: 440px; max-height: 90vh; display: flex; flex-direction: column; overflow: hidden; }
.cp-modal-hdr { display: flex; justify-content: space-between; align-items: center; padding: 14px 18px; background: linear-gradient(90deg,#1e3a5f,#1d4ed8); color: #fff; font-weight: 700; }
.cp-x { background: none; border: none; color: #fff; font-size: 16px; cursor: pointer; }
.cp-modal-body { padding: 16px 18px; display: flex; flex-direction: column; gap: 10px; overflow-y: auto; }
.cp-lbl { font-size: 12px; font-weight: 700; color: #475569; }
.cp-inp { border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 9px 12px; font-size: 15px; text-transform: uppercase; }
.cp-inp:focus { outline: none; border-color: #1d4ed8; }
.cp-switch { display: flex; align-items: flex-start; gap: 10px; font-size: 14px; color: #334155; cursor: pointer; }
.cp-switch input { width: 18px; height: 18px; margin-top: 2px; accent-color: #1d4ed8; flex-shrink: 0; }
.cp-switch small { display: block; font-size: 12px; color: #94a3b8; }
.cp-modal-ftr { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 18px; border-top: 1px solid #f1f5f9; }
.cp-btn { display: inline-flex; align-items: center; background: linear-gradient(90deg,#1e3a5f,#1d4ed8); color: #fff; border: none; border-radius: 10px; padding: 10px 18px; font-weight: 700; cursor: pointer; }
.cp-btn:disabled { opacity: .6; cursor: not-allowed; }
.cp-btn--sec { background: #f1f5f9; color: #475569; }

@media (max-width: 1024px) {
  .cp-grid { grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); }
}
@media (max-width: 768px) {
  .cp-page { padding: 14px 12px 24px; }
  .cp-head { flex-direction: column; }
  .cp-btn-new { width: 100%; justify-content: center; }
  .cp-search { max-width: none; }
  .cp-ov { padding: 0; align-items: flex-end; }
  .cp-modal { border-radius: 16px 16px 0 0; max-width: 100%; }
}
@media (max-width: 576px) {
  .cp-title { font-size: 18px; }
  .cp-tabs { width: 100%; }
  .cp-tab { flex: 1; padding: 7px 6px; }
  .cp-grid { grid-template-columns: 1fr; gap: 8px; }
  .cp-card { padding: 10px 12px; }
}
</style>
