<template>
  <div class="page-container">

    <div class="page-header">
      <div>
        <h1 class="page-title"><i class="bi bi-rulers me-2"></i>{{ moduleName }}</h1>
        <p class="page-subtitle">Unidades con que se usan y compran los insumos (forma_medida del escritorio)</p>
      </div>
      <button class="btn btn-primary" @click="openCreate"><i class="bi bi-plus-lg"></i> Nueva</button>
    </div>

    <div class="filters-row">
      <div class="search-bar">
        <i class="bi bi-search"></i>
        <input v-model="search" :placeholder="`Buscar ${moduleName.toLowerCase()}...`" class="search-input" maxlength="60" />
      </div>
      <div class="seg">
        <button v-for="o in ESTADOS" :key="o.v" :class="{ on: estado === o.v }" @click="estado = o.v">{{ o.l }}</button>
      </div>
    </div>

    <div v-if="loading" class="empty-state"><i class="bi bi-arrow-repeat spin"></i><p>Cargando...</p></div>

    <div v-else-if="!filtered.length" class="empty-state">
      <i class="bi bi-rulers"></i>
      <p>{{ search ? `Sin resultados para "${search}"` : 'No hay registros' }}</p>
    </div>

    <div v-else class="list">
      <div v-for="f in filtered" :key="f.id" class="row-item" :class="{ off: !f.is_active }">
        <div class="ri-main">
          <strong>{{ f.name }}</strong>
          <span class="ri-id">#{{ f.id }}</span>
        </div>
        <label class="switch" :title="f.is_active ? 'Activa: se puede escoger en los insumos' : 'Inactiva: no se ofrece en los insumos'">
          <input type="checkbox" :checked="!!f.is_active" :disabled="f._saving" @change="toggleActiva(f)" />
          <span class="slider"></span>
          <span class="sw-lbl">{{ f.is_active ? 'Activa' : 'Inactiva' }}</span>
        </label>
        <button class="btn btn-sm btn-outline-primary" @click="openEdit(f)" title="Editar"><i class="bi bi-pencil"></i></button>
      </div>
    </div>

    <div v-if="modal" class="modal-overlay" @click.self="modal = false">
      <div class="modal-card">
        <div class="mh">
          <h3>{{ editing ? `Editar — ${editing.name}` : `Nueva — ${moduleName}` }}</h3>
          <button class="btn-x" @click="modal = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="mb-area">
          <div class="fg">
            <label>Nombre *</label>
            <input v-model="form.name" class="form-control" maxlength="100" placeholder="Ej: Kilo (s), Unidad, Botella (s)"
                   @keydown.enter="save" v-focus />
          </div>
          <label class="chk">
            <input type="checkbox" v-model="form.is_active" :true-value="1" :false-value="0" />
            Activa (se puede escoger como unidad de uso de los insumos)
          </label>
        </div>
        <div class="mf">
          <button class="btn btn-secondary btn-sm" @click="modal = false">Cancelar</button>
          <button class="btn btn-primary btn-sm" @click="save" :disabled="saving">{{ saving ? 'Guardando...' : 'Guardar' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import { ordenAlfa } from "@/utils/orden"
import { useModuleName } from "@/composables/useModuleName"

const { moduleName } = useModuleName()
const vFocus = { mounted: el => el.focus() }

const ESTADOS = [{ v: "", l: "Todas" }, { v: "1", l: "Activas" }, { v: "0", l: "Inactivas" }]
const BASE = "/supply-items/catalogos/formas-medida"

const items   = ref([])
const loading = ref(true)
const search  = ref("")
const estado  = ref("")
const modal   = ref(false)
const saving  = ref(false)
const editing = ref(null)
const form    = ref({ name: "", is_active: 1 })

const filtered = computed(() => {
  const q = search.value.toLowerCase()
  return ordenAlfa(items.value.filter(i =>
    (!q || (i.name || "").toLowerCase().includes(q)) &&
    (estado.value === "" || String(Number(i.is_active)) === estado.value)
  ), "name")
})

async function load() {
  loading.value = true
  try { items.value = (await api.get(`${BASE}`)).data }
  catch { showToast("Error cargando formas de medida", "error") }
  finally { loading.value = false }
}

function openCreate() {
  editing.value = null
  form.value = { name: "", is_active: 1 }
  modal.value = true
}

function openEdit(f) {
  editing.value = f
  form.value = { name: f.name, is_active: Number(f.is_active) ? 1 : 0 }
  modal.value = true
}

async function save() {
  const name = form.value.name.trim()
  if (!name) { showToast("El nombre es obligatorio", "warning"); return }
  saving.value = true
  try {
    if (editing.value) {
      const { data } = await api.put(`${BASE}/${editing.value.id}`, { name, is_active: form.value.is_active })
      Object.assign(editing.value, data)
    } else {
      const { data } = await api.post(`${BASE}`, { name })
      if (!form.value.is_active) Object.assign(data, (await api.put(`${BASE}/${data.id}`, { is_active: 0 })).data)
      items.value.push(data)
    }
    modal.value = false
    showToast("Guardado", "success")
  } catch (e) { showToast(e.response?.data?.detail || "Error al guardar", "error") }
  finally { saving.value = false }
}

async function toggleActiva(f) {
  f._saving = true
  try {
    const { data } = await api.put(`${BASE}/${f.id}`, { is_active: f.is_active ? 0 : 1 })
    f.is_active = data.is_active
  } catch (e) { showToast(e.response?.data?.detail || "Error al actualizar", "error") }
  finally { f._saving = false }
}

onMounted(load)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 760px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; flex-wrap: wrap; margin-bottom: 18px; }
.page-title { font-size: 22px; font-weight: 700; color: #1e293b; margin: 0 0 4px; }
.page-subtitle { font-size: 13px; color: #64748b; margin: 0; }
.filters-row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-bottom: 14px; }
.search-bar { display: flex; align-items: center; gap: 8px; background: #fff; border: 1.5px solid #e2e8f0; border-radius: 10px; padding: 0 12px; flex: 1; min-width: 200px; max-width: 360px; }
.search-bar i { color: #94a3b8; }
.search-input { border: none; outline: none; padding: 9px 0; font-size: 13px; width: 100%; background: transparent; }
.seg { display: flex; background: #f1f5f9; border-radius: 10px; padding: 3px; }
.seg button { border: none; background: none; padding: 6px 12px; border-radius: 8px; font-size: 12px; font-weight: 700; color: #64748b; cursor: pointer; }
.seg button.on { background: #fff; color: #1d4ed8; box-shadow: 0 1px 3px rgba(0,0,0,.08); }

.empty-state { text-align: center; color: #94a3b8; padding: 40px 0; }
.empty-state i { font-size: 28px; }
.list { background: #fff; border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,.08); overflow: hidden; }
.row-item { display: flex; align-items: center; gap: 12px; padding: 10px 14px; border-bottom: 1px solid #f1f5f9; }
.row-item:last-child { border-bottom: none; }
.row-item.off .ri-main strong { color: #94a3b8; }
.ri-main { flex: 1; min-width: 0; display: flex; align-items: baseline; gap: 8px; }
.ri-main strong { font-size: 14px; color: #1e293b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ri-id { font-size: 11px; color: #94a3b8; }

.switch { display: inline-flex; align-items: center; gap: 8px; cursor: pointer; position: relative; }
.switch input { position: absolute; opacity: 0; width: 0; height: 0; }
.slider { width: 36px; height: 20px; background: #cbd5e1; border-radius: 999px; position: relative; transition: background .15s; flex-shrink: 0; }
.slider::after { content: ""; position: absolute; top: 2px; left: 2px; width: 16px; height: 16px; background: #fff; border-radius: 50%; transition: transform .15s; }
.switch input:checked + .slider { background: #16a34a; }
.switch input:checked + .slider::after { transform: translateX(16px); }
.switch input:disabled + .slider { opacity: .6; }
.sw-lbl { font-size: 12px; font-weight: 600; color: #475569; min-width: 56px; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 2000; padding: 16px; }
.modal-card { background: #fff; border-radius: 16px; width: 100%; max-width: 420px; box-shadow: 0 20px 60px rgba(0,0,0,.2); display: flex; flex-direction: column; }
.mh { display: flex; align-items: center; justify-content: space-between; padding: 14px 20px; border-bottom: 1px solid #f1f5f9; }
.mh h3 { font-size: 15px; font-weight: 700; margin: 0; color: #1e293b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.btn-x { background: none; border: none; font-size: 16px; color: #94a3b8; cursor: pointer; }
.mb-area { padding: 18px 20px; display: flex; flex-direction: column; gap: 14px; }
.mf { padding: 12px 20px 16px; display: flex; justify-content: flex-end; gap: 8px; border-top: 1px solid #f1f5f9; }
.fg { display: flex; flex-direction: column; gap: 4px; }
.fg label { font-size: 12px; font-weight: 600; color: #374151; }
.chk { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #374151; cursor: pointer; }
.chk input { width: 16px; height: 16px; }

.btn { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #3b82f6; color: #fff; }
.btn:disabled { opacity: .6; cursor: not-allowed; }
.btn-secondary { border: 1.5px solid #e2e8f0; background: #fff; color: #64748b; }
.btn-sm { padding: 6px 12px; font-size: 12px; }
.btn-outline-primary { background: #eff6ff; color: #1d4ed8; border: 1.5px solid #bfdbfe; }
.spin { display: inline-block; animation: spin .8s linear infinite; }
@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }

@media (max-width: 768px) {
  .page-container { padding: 14px; }
  .search-bar { max-width: none; flex: 1 1 100%; }
  .modal-overlay { padding: 0; align-items: flex-end; }
  .modal-card { max-width: none; border-radius: 16px 16px 0 0; }
}
@media (max-width: 576px) {
  .page-title { font-size: 18px; }
  .seg { width: 100%; }
  .seg button { flex: 1; }
  .sw-lbl { display: none; }
  .mf .btn { flex: 1; justify-content: center; }
}
</style>
