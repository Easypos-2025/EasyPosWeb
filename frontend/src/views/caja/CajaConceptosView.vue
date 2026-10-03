<template>
  <div class="cn-page">
    <div class="cn-head">
      <div>
        <h2 class="cn-title"><i class="bi bi-tags me-2"></i>{{ moduleName || 'Conceptos de Caja' }}</h2>
        <p class="cn-sub">Conceptos y subconceptos de Gastos, Compras, Otros Egresos y Otros Ingresos. No se eliminan: se desactivan.</p>
      </div>
      <button class="cn-btn-new" @click="abrir()"><i class="bi bi-plus-lg me-1"></i>Nuevo concepto</button>
    </div>

    <div class="cn-toolbar">
      <div class="cn-tabs">
        <button :class="['cn-tab', { active: !tipo }]" @click="tipo = null; cargar()">Todos</button>
        <button v-for="(n, k) in tipos" :key="k" :class="['cn-tab', { active: tipo === +k }]" @click="tipo = +k; cargar()">{{ n }}</button>
      </div>
      <div class="cn-search">
        <i class="bi bi-search"></i>
        <input v-model="q" @input="deb" :placeholder="`Buscar ${moduleName || 'concepto'}...`" maxlength="50" />
      </div>
    </div>

    <div v-if="loading" class="cn-state"><div class="spinner-border spinner-border-sm text-primary"></div></div>
    <div v-else-if="!rows.length" class="cn-state cn-empty"><i class="bi bi-tags"></i><p>No hay conceptos{{ q ? ' con ese nombre' : '' }}.</p></div>
    <div v-else class="cn-grid">
      <div v-for="c in rows" :key="c.concept_id" :class="['cn-card', `cn-card--t${c.concept_type}`, { 'cn-card--off': !c.is_active }]">
        <div class="cn-card-top">
          <span class="cn-code">#{{ c.concept_id }}</span>
          <span :class="['cn-chip', `cn-chip--t${c.concept_type}`]">{{ tipos[c.concept_type] }}</span>
          <span v-if="!c.is_active" class="cn-chip cn-chip--off">Inactivo</span>
        </div>
        <div class="cn-name">{{ c.description }}</div>
        <div class="cn-stats"><i class="bi bi-diagram-2"></i> {{ c.subconceptos }} subconceptos</div>
        <div class="cn-actions">
          <button class="cn-ico" title="Subconceptos" @click="verSub(c)"><i class="bi bi-diagram-2"></i></button>
          <button class="cn-ico" title="Editar" @click="abrir(c)"><i class="bi bi-pencil"></i></button>
          <button class="cn-ico" :title="c.is_active ? 'Desactivar' : 'Activar'" @click="toggle(c)">
            <i :class="c.is_active ? 'bi bi-toggle-on text-success' : 'bi bi-toggle-off'"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- Modal concepto -->
    <div v-if="modal.show" class="cn-overlay" @click.self="modal.show = false">
      <div class="cn-modal">
        <div class="cn-modal-h"><b>{{ modal.id ? 'Editar concepto' : 'Nuevo concepto' }}</b><button class="cn-x" @click="modal.show = false"><i class="bi bi-x-lg"></i></button></div>
        <div class="cn-modal-b">
          <label class="cn-lbl">Descripción</label>
          <input v-model="modal.description" class="form-control" maxlength="50" @keyup.enter="guardar" />
          <label class="cn-lbl">Tipo</label>
          <div class="cn-tipos">
            <button v-for="(n, k) in tipos" :key="k" type="button" :class="['cn-tipo', { active: modal.concept_type === +k }]" @click="modal.concept_type = +k">{{ n }}</button>
          </div>
          <label class="cn-check"><input type="checkbox" v-model="modal.is_active" /> Activo</label>
        </div>
        <div class="cn-modal-f">
          <button class="btn btn-secondary" @click="modal.show = false">Cancelar</button>
          <button class="btn btn-primary" :disabled="guardando || !modal.description.trim() || !modal.concept_type" @click="guardar">
            {{ guardando ? 'Guardando...' : 'Guardar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal subconceptos -->
    <div v-if="sub.show" class="cn-overlay" @click.self="sub.show = false">
      <div class="cn-modal cn-modal--lg">
        <div class="cn-modal-h"><b><i class="bi bi-diagram-2 me-1"></i>Subconceptos de {{ sub.concepto?.description }}</b><button class="cn-x" @click="sub.show = false"><i class="bi bi-x-lg"></i></button></div>
        <div class="cn-modal-b">
          <div class="cn-sub-new">
            <input v-model="sub.nuevo" class="form-control" maxlength="50" placeholder="Nuevo subconcepto" @keyup.enter="crearSub" />
            <button class="btn btn-primary" :disabled="!sub.nuevo.trim() || sub.guardando" @click="crearSub"><i class="bi bi-plus-lg"></i></button>
          </div>
          <div v-if="sub.loading" class="cn-state"><div class="spinner-border spinner-border-sm text-primary"></div></div>
          <div v-else-if="!sub.rows.length" class="cn-none">Sin subconceptos</div>
          <div v-for="s in sub.rows" :key="s.subconcept_id" :class="['cn-sub-row', { 'cn-card--off': !s.is_active }]">
            <span class="cn-code">#{{ s.subconcept_id }}</span>
            <input v-if="s.editando" v-model="s.description" class="form-control form-control-sm" maxlength="50" @keyup.enter="guardarSub(s)" />
            <span v-else class="cn-sub-n">{{ s.description }}</span>
            <button v-if="s.editando" class="cn-ico" title="Guardar" @click="guardarSub(s)"><i class="bi bi-check-lg"></i></button>
            <button v-else class="cn-ico" title="Editar" @click="s.editando = true"><i class="bi bi-pencil"></i></button>
            <button class="cn-ico" :title="s.is_active ? 'Desactivar' : 'Activar'" @click="s.is_active = !s.is_active; guardarSub(s)">
              <i :class="s.is_active ? 'bi bi-toggle-on text-success' : 'bi bi-toggle-off'"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'
import { useModuleName } from '@/composables/useModuleName'

const BASE = '/api/caja/conceptos'
const { moduleName } = useModuleName()

const tipos = ref({ 1: 'Gastos', 2: 'Compras', 3: 'Otros Egresos', 4: 'Otros Ingresos' })
const rows = ref([])
const loading = ref(true)
const guardando = ref(false)
const tipo = ref(null)
const q = ref('')
let t = null, seq = 0

async function cargar() {
  const my = ++seq
  loading.value = true
  try {
    const { data } = await api.get(BASE, { params: { tipo: tipo.value || undefined, q: q.value.trim() || undefined } })
    if (my !== seq) return
    tipos.value = data.tipos
    rows.value = data.conceptos
  } catch (e) {
    if (my === seq) showToast(e?.response?.data?.detail || 'No se pudieron cargar los conceptos', 'error')
  } finally {
    if (my === seq) loading.value = false
  }
}
function deb() { clearTimeout(t); t = setTimeout(cargar, 300) }

const modal = reactive({ show: false, id: null, description: '', concept_type: null, is_active: true })
function abrir(c) {
  Object.assign(modal, c
    ? { show: true, id: c.concept_id, description: c.description, concept_type: c.concept_type, is_active: c.is_active }
    : { show: true, id: null, description: '', concept_type: tipo.value || 1, is_active: true })
}
async function guardar() {
  if (!modal.description.trim() || !modal.concept_type) return
  guardando.value = true
  try {
    const body = { description: modal.description.trim(), concept_type: modal.concept_type, is_active: modal.is_active }
    if (modal.id) await api.put(`${BASE}/${modal.id}`, body)
    else await api.post(BASE, body)
    showToast('Concepto guardado', 'success')
    modal.show = false
    cargar()
  } catch (e) {
    showToast(e?.response?.data?.detail || 'No se pudo guardar el concepto', 'error')
  } finally { guardando.value = false }
}
async function toggle(c) {
  try {
    await api.put(`${BASE}/${c.concept_id}`, { description: c.description, concept_type: c.concept_type, is_active: !c.is_active })
    c.is_active = !c.is_active
  } catch (e) { showToast(e?.response?.data?.detail || 'No se pudo actualizar', 'error') }
}

const sub = reactive({ show: false, concepto: null, rows: [], loading: false, nuevo: '', guardando: false })
async function verSub(c) {
  Object.assign(sub, { show: true, concepto: c, rows: [], loading: true, nuevo: '' })
  try {
    const { data } = await api.get(`${BASE}/${c.concept_id}/sub`)
    sub.rows = data.subconceptos.map(s => ({ ...s, editando: false }))
  } catch (e) {
    showToast(e?.response?.data?.detail || 'No se pudieron cargar los subconceptos', 'error')
  } finally { sub.loading = false }
}
async function crearSub() {
  if (!sub.nuevo.trim()) return
  sub.guardando = true
  try {
    const { data } = await api.post(`${BASE}/${sub.concepto.concept_id}/sub`, { description: sub.nuevo.trim(), is_active: true })
    sub.rows.push({ ...data, editando: false })
    sub.nuevo = ''
    sub.concepto.subconceptos++
  } catch (e) {
    showToast(e?.response?.data?.detail || 'No se pudo crear el subconcepto', 'error')
  } finally { sub.guardando = false }
}
async function guardarSub(s) {
  try {
    const { data } = await api.put(`${BASE}/${sub.concepto.concept_id}/sub/${s.subconcept_id}`,
      { description: s.description.trim(), is_active: s.is_active })
    Object.assign(s, data, { editando: false })
  } catch (e) {
    showToast(e?.response?.data?.detail || 'No se pudo guardar el subconcepto', 'error')
    verSub(sub.concepto)
  }
}

onMounted(cargar)
</script>

<style scoped>
.cn-page { padding: 20px 24px 32px; }
.cn-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 14px; }
.cn-title { font-size: 22px; font-weight: 800; color: #1e293b; margin: 0; }
.cn-sub { font-size: 13px; color: #64748b; margin: 2px 0 0; max-width: 640px; }
.cn-btn-new { display: inline-flex; align-items: center; background: linear-gradient(90deg,#1e3a5f,#1d4ed8); color: #fff; border: none;
              border-radius: 10px; padding: 9px 16px; font-weight: 700; font-size: 14px; white-space: nowrap; cursor: pointer; }
.cn-toolbar { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-bottom: 14px; }
.cn-tabs { display: flex; background: #f1f5f9; border-radius: 10px; padding: 3px; flex-wrap: wrap; }
.cn-tab { border: none; background: none; padding: 7px 12px; border-radius: 8px; font-size: 13px; font-weight: 700; color: #64748b; cursor: pointer; }
.cn-tab.active { background: #fff; color: #1d4ed8; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.cn-search { flex: 1; min-width: 200px; max-width: 360px; display: flex; align-items: center; gap: 6px; background: #fff;
             border: 1.5px solid #e2e8f0; border-radius: 10px; padding: 7px 10px; color: #94a3b8; }
.cn-search input { border: none; outline: none; flex: 1; font-size: 14px; min-width: 0; }
.cn-state { display: flex; flex-direction: column; align-items: center; padding: 40px 20px; color: #94a3b8; }
.cn-empty i { font-size: 36px; }
.cn-none { font-size: 13px; color: #94a3b8; text-align: center; padding: 10px; }
.cn-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 12px; }
.cn-card { background: #fff; border: 1.5px solid #e2e8f0; border-radius: 12px; padding: 12px 14px; display: flex; flex-direction: column; gap: 6px; }
.cn-card--off { opacity: .55; }
.cn-card-top { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.cn-code { font-size: 12px; font-weight: 800; color: #94a3b8; font-family: ui-monospace, monospace; }
.cn-chip { font-size: 10px; font-weight: 700; border-radius: 10px; padding: 2px 8px; background: #f1f5f9; color: #475569; }
.cn-chip--t1 { background: #fee2e2; color: #b91c1c; }
.cn-chip--t2 { background: #ffedd5; color: #c2410c; }
.cn-chip--t3 { background: #fce7f3; color: #be185d; }
.cn-chip--t4 { background: #dcfce7; color: #15803d; }
.cn-chip--off { background: #e2e8f0; color: #475569; }
.cn-name { font-size: 15px; font-weight: 800; color: #1e3a5f; word-break: break-word; }
.cn-stats { font-size: 12px; color: #64748b; }
.cn-actions { display: flex; justify-content: flex-end; gap: 6px; margin-top: auto; }
.cn-ico { background: none; border: 1px solid #e2e8f0; border-radius: 8px; padding: 5px 9px; cursor: pointer; color: #475569; }
.cn-ico:hover { border-color: #1d4ed8; color: #1d4ed8; }
.cn-overlay { position: fixed; inset: 0; background: rgba(15,23,42,.45); z-index: 1050; display: flex; align-items: center; justify-content: center; padding: 16px; }
.cn-modal { background: #fff; border-radius: 14px; width: 100%; max-width: 440px; max-height: 88dvh; display: flex; flex-direction: column; box-shadow: 0 20px 50px rgba(0,0,0,.25); }
.cn-modal--lg { max-width: 560px; }
.cn-modal-h { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid #e2e8f0; }
.cn-modal-b { padding: 14px 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
.cn-modal-f { display: flex; justify-content: flex-end; gap: 8px; padding: 10px 16px; border-top: 1px solid #e2e8f0; }
.cn-x { border: none; background: none; font-size: 16px; color: #64748b; cursor: pointer; }
.cn-lbl { font-size: 12px; font-weight: 700; color: #475569; margin-top: 4px; }
.cn-tipos { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.cn-tipo { border: 1.5px solid #e2e8f0; background: #f8fafc; border-radius: 10px; padding: 8px; font-size: 13px; font-weight: 700; color: #475569; cursor: pointer; }
.cn-tipo.active { border-color: #1d4ed8; background: #eff6ff; color: #1d4ed8; }
.cn-check { display: flex; align-items: center; gap: 8px; font-size: 14px; margin-top: 6px; cursor: pointer; }
.cn-sub-new { display: flex; gap: 6px; margin-bottom: 6px; }
.cn-sub-row { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px solid #f1f5f9; }
.cn-sub-n { flex: 1; min-width: 0; font-size: 14px; font-weight: 600; color: #1e293b; }
.cn-sub-row .form-control { flex: 1; }
@media (max-width: 768px) {
  .cn-page { padding: 14px 12px 24px; }
  .cn-title { font-size: 19px; }
  .cn-head { flex-direction: column; }
  .cn-search { max-width: none; }
}
@media (max-width: 576px) {
  .cn-btn-new { width: 100%; justify-content: center; }
  .cn-tab { padding: 6px 8px; font-size: 12px; }
  .cn-grid { grid-template-columns: 1fr; }
}
</style>
