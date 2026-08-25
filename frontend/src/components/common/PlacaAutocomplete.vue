<template>
  <div class="pa-wrap" ref="wrapRef">
    <input
      ref="inputRef"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      class="pa-input"
      autocomplete="off"
      @input="onInput"
      @keydown="onKeydown"
      @focus="onFocus"
    />
    <ul v-if="show && sugerencias.length" class="pa-dropdown">
      <li
        v-for="(v, i) in sugerencias" :key="v.placa"
        :class="['pa-item', { 'pa-item--active': i === cursor }]"
        @mousedown.prevent="seleccionar(v)"
        @mouseover="cursor = i"
      >
        <div class="pa-item-left">
          <img v-if="v.foto_url" :src="v.foto_url" class="pa-item-foto" alt="" />
          <div v-else class="pa-item-foto pa-item-foto--ph">
            <i class="bi bi-car-front-fill"></i>
          </div>
          <div>
            <span class="pa-item-placa">{{ v.placa }}</span>
            <span v-if="v.tipo_vehiculo" class="pa-item-tipo">{{ v.tipo_vehiculo }}</span>
            <span v-if="v.marca || v.modelo" class="pa-item-det">
              {{ [v.marca, v.modelo, v.color].filter(Boolean).join(' · ') }}
            </span>
          </div>
        </div>
        <div v-if="v.propietario_nombre" class="pa-item-cliente">
          <i class="bi bi-person-fill"></i> {{ v.propietario_nombre }}
        </div>
      </li>
    </ul>
    <div v-if="show && buscando" class="pa-searching">
      <i class="bi bi-arrow-repeat pa-spin"></i> Buscando…
    </div>
    <div v-if="show && !buscando && sugerencias.length === 0 && valorLocal.length >= 3" class="pa-no-results">
      Sin coincidencias
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import api from '@/services/apis'
import { useCompanyStore } from '@/stores/companyStore'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: 'Placa' },
  disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'vehiculo-seleccionado'])

const companyStore = useCompanyStore()
const wrapRef     = ref(null)
const inputRef    = ref(null)
const sugerencias = ref([])
const buscando    = ref(false)
const show        = ref(false)
const cursor      = ref(-1)
const valorLocal  = ref(props.modelValue || '')

let _timer = null

function onInput(e) {
  const v = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '')
  valorLocal.value = v
  emit('update:modelValue', v)
  cursor.value = -1

  clearTimeout(_timer)
  if (v.length < 3) {
    sugerencias.value = []
    show.value = false
    return
  }
  show.value   = true
  buscando.value = true
  _timer = setTimeout(() => buscar(v), 300)
}

async function buscar(q) {
  const cid = companyStore.selectedCompany?.id
  if (!cid) { buscando.value = false; return }
  try {
    const res = await api.get('/api/vehicles/search', { params: { company_id: cid, q } })
    sugerencias.value = res.data
  } catch {
    sugerencias.value = []
  }
  buscando.value = false
}

function seleccionar(v) {
  valorLocal.value = v.placa
  emit('update:modelValue', v.placa)
  emit('vehiculo-seleccionado', v)
  sugerencias.value = []
  show.value = false
  cursor.value = -1
}

function onFocus() {
  if (valorLocal.value.length >= 3 && sugerencias.value.length) show.value = true
}

function onKeydown(e) {
  if (!show.value || !sugerencias.value.length) return
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    cursor.value = Math.min(cursor.value + 1, sugerencias.value.length - 1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    cursor.value = Math.max(cursor.value - 1, 0)
  } else if (e.key === 'Enter' && cursor.value >= 0) {
    e.preventDefault()
    seleccionar(sugerencias.value[cursor.value])
  } else if (e.key === 'Escape') {
    show.value = false
  }
}

function onClickOutside(e) {
  if (wrapRef.value && !wrapRef.value.contains(e.target)) {
    show.value = false
  }
}

watch(() => props.modelValue, (v) => {
  if (v !== valorLocal.value) valorLocal.value = v || ''
})

onMounted(() => document.addEventListener('mousedown', onClickOutside))
onUnmounted(() => { document.removeEventListener('mousedown', onClickOutside); clearTimeout(_timer) })
</script>

<style scoped>
.pa-wrap { position: relative; width: 100%; }

.pa-input {
  width: 100%; padding: 8px 12px; font-size: 1rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: 2px;
  border: 1.5px solid #ced4da; border-radius: 8px; outline: none;
  background: #fff; color: #212529; transition: border-color .15s;
}
.pa-input:focus  { border-color: #0d6efd; }
.pa-input:disabled { background: #f8f9fa; cursor: not-allowed; opacity: .7; }

.pa-dropdown {
  position: absolute; top: calc(100% + 4px); left: 0; right: 0; z-index: 1100;
  background: #fff; border: 1.5px solid #dee2e6; border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,.12); padding: 4px 0; margin: 0;
  list-style: none; max-height: 320px; overflow-y: auto;
}

.pa-item {
  display: flex; align-items: center; justify-content: space-between; gap: 10px;
  padding: 8px 12px; cursor: pointer; transition: background .1s;
}
.pa-item:hover, .pa-item--active { background: #f0f6ff; }

.pa-item-left { display: flex; align-items: center; gap: 10px; min-width: 0; }

.pa-item-foto {
  width: 42px; height: 42px; border-radius: 6px; object-fit: cover; flex-shrink: 0;
}
.pa-item-foto--ph {
  display: flex; align-items: center; justify-content: center;
  background: #f1f3f5; color: #ced4da; font-size: 1.1rem;
  border: 1px dashed #dee2e6;
}

.pa-item-placa {
  display: block; font-size: .95rem; font-weight: 800; letter-spacing: 2px; color: #212529;
}
.pa-item-tipo {
  display: block; font-size: .72rem; color: #6c757d; margin-top: 1px;
}
.pa-item-det {
  display: block; font-size: .7rem; color: #adb5bd; font-style: italic;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 160px;
}

.pa-item-cliente {
  font-size: .75rem; color: #0d6efd; font-weight: 600; white-space: nowrap;
  display: flex; align-items: center; gap: 4px; flex-shrink: 0;
}

.pa-searching, .pa-no-results {
  position: absolute; top: calc(100% + 4px); left: 0; right: 0; z-index: 1100;
  background: #fff; border: 1.5px solid #dee2e6; border-radius: 10px;
  padding: 10px 14px; font-size: .82rem; color: #6c757d;
  box-shadow: 0 8px 24px rgba(0,0,0,.12);
}

.pa-spin { display: inline-block; animation: pa-spin .7s linear infinite; }
@keyframes pa-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

@media (max-width: 768px) {
  .pa-input { font-size: .9rem; padding: 7px 10px; }
  .pa-item  { padding: 7px 10px; }
  .pa-item-foto { width: 36px; height: 36px; }
}
@media (max-width: 576px) {
  .pa-dropdown { max-height: 240px; }
  .pa-item-det { max-width: 100px; }
}
</style>
