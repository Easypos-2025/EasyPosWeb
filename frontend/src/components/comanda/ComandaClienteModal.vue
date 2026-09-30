<template>
  <!-- Selector de cliente del pedido (por defecto Consumidor Final, id 1) -->
  <div class="cm-overlay" @click.self="$emit('close')">
    <div class="cm-box">
      <div class="cm-hdr">
        <span><i class="bi bi-person-badge me-1"></i> {{ title }}</span>
        <button class="cm-x" @click="$emit('close')"><i class="bi bi-x-lg"></i></button>
      </div>

      <div v-if="!creando" class="cm-body">
        <div class="cm-search">
          <i class="bi bi-search"></i>
          <input v-model="q" @input="deb" placeholder="Nombre, cédula o teléfono..." maxlength="60" v-focus />
        </div>
        <div v-if="loading" class="cm-empty"><span class="spinner-border spinner-border-sm"></span></div>
        <div v-else class="cm-list">
          <button v-for="c in rows" :key="c.id_cliente"
                  :class="['cm-row', { active: c.id_cliente === currentId }]"
                  :disabled="saving" @click="$emit('select', c)">
            <div class="cm-main">
              <span class="cm-name">{{ c.nombre }}</span>
              <span class="cm-doc">{{ c.cedula || '—' }}{{ c.telefono ? ' · ' + c.telefono : '' }}</span>
            </div>
            <i v-if="c.id_cliente === currentId" class="bi bi-check-circle-fill"></i>
          </button>
          <div v-if="!rows.length" class="cm-empty">Sin resultados</div>
        </div>
        <button class="cm-add" @click="abrirCrear"><i class="bi bi-person-plus"></i> Crear cliente</button>
      </div>

      <div v-else class="cm-body">
        <label class="cm-lbl">Nombre *</label>
        <input v-model="nuevo.nombres" class="cm-inp" maxlength="150" v-focus />
        <label class="cm-lbl">Cédula / NIT</label>
        <input v-model="nuevo.cedula" class="cm-inp" maxlength="50" inputmode="numeric" />
        <label class="cm-lbl">Teléfono</label>
        <input v-model="nuevo.telefono" class="cm-inp" maxlength="50" inputmode="tel" />
        <label class="cm-lbl">Dirección</label>
        <input v-model="nuevo.direccion" class="cm-inp" maxlength="255" />
        <div class="cm-ftr">
          <button class="cm-btn cm-btn--sec" @click="creando = false">Volver</button>
          <button class="cm-btn" :disabled="saving || !nuevo.nombres.trim()" @click="crear">
            {{ saving ? 'Guardando…' : 'Crear y asignar' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import apiComanda from '@/services/apiComanda'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'

const props = defineProps({
  currentId: { type: Number, default: 1 },
  saving:    { type: Boolean, default: false },
  title:     { type: String, default: 'Cliente del pedido' },
  // Pantallas del panel (pago/caja) usan la sesión del usuario; la comanda usa la del mesero
  panel:     { type: Boolean, default: false },
})
const http = () => props.panel ? api : apiComanda
const basePath = () => props.panel ? '/api/pos-catalogo/listas-cliente/clientes' : '/api/pos/comanda/clientes'
const emit = defineEmits(['close', 'select'])
const vFocus = { mounted: el => el.focus() }

const q = ref('')
const rows = ref([])
const loading = ref(false)
const creando = ref(false)
const nuevo = ref({ nombres: '', cedula: '', telefono: '', direccion: '' })
let t = null, seq = 0

async function buscar() {
  const my = ++seq
  loading.value = true
  try {
    const { data } = await http().get(basePath(), { params: { q: q.value.trim() || undefined } })
    if (my === seq) rows.value = data
  } catch (e) { if (my === seq) showToast(e?.response?.data?.detail || 'Error cargando clientes', 'error') }
  finally { if (my === seq) loading.value = false }
}
const deb = () => { clearTimeout(t); t = setTimeout(buscar, 250) }

function abrirCrear() {
  nuevo.value = { nombres: q.value.trim(), cedula: '', telefono: '', direccion: '' }
  creando.value = true
}
async function crear() {
  try {
    const { data } = await http().post(basePath(), {
      nombres: nuevo.value.nombres.trim(), cedula: nuevo.value.cedula.trim() || null,
      telefono: nuevo.value.telefono.trim() || null, direccion: nuevo.value.direccion.trim() || null,
    })
    emit('select', data)
  } catch (e) { showToast(e?.response?.data?.detail || 'Error creando cliente', 'error') }
}

onMounted(buscar)
</script>

<style scoped>
.cm-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.55); display: flex; align-items: center; justify-content: center; z-index: 1150; padding: 16px; }
.cm-box { background: #fff; border-radius: 16px; width: 100%; max-width: 460px; max-height: 88vh; display: flex; flex-direction: column; overflow: hidden; }
.cm-hdr { display: flex; justify-content: space-between; align-items: center; padding: 14px 16px; background: linear-gradient(90deg,#1e3a5f,#1d4ed8); color: #fff; font-weight: 700; }
.cm-x { background: none; border: none; color: #fff; font-size: 16px; cursor: pointer; }
.cm-body { padding: 14px 16px; display: flex; flex-direction: column; gap: 8px; overflow-y: auto; }
.cm-search { display: flex; align-items: center; gap: 6px; border: 1.5px solid #cbd5e1; border-radius: 10px; padding: 9px 12px; }
.cm-search input { border: none; outline: none; flex: 1; font-size: 15px; min-width: 0; }
.cm-list { display: flex; flex-direction: column; gap: 6px; max-height: 50vh; overflow-y: auto; }
.cm-row { display: flex; align-items: center; gap: 8px; border: 1.5px solid #e2e8f0; background: #fff; border-radius: 10px; padding: 10px 12px; cursor: pointer; text-align: left; }
.cm-row.active { border-color: #16a34a; background: #f0fdf4; color: #15803d; }
.cm-main { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.cm-name { font-weight: 700; font-size: 14px; color: #1e3a5f; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cm-doc { font-size: 12px; color: #94a3b8; }
.cm-empty { text-align: center; color: #94a3b8; font-size: 13px; padding: 14px; }
.cm-add { background: none; border: 1.5px dashed #93c5fd; color: #1d4ed8; border-radius: 10px; padding: 10px; font-weight: 700; cursor: pointer; }
.cm-lbl { font-size: 12px; font-weight: 700; color: #475569; margin-top: 2px; }
.cm-inp { border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 9px 10px; font-size: 15px; }
.cm-ftr { display: flex; gap: 8px; margin-top: 8px; }
.cm-btn { flex: 1; background: linear-gradient(90deg,#1e3a5f,#1d4ed8); color: #fff; border: none; border-radius: 10px; padding: 11px; font-weight: 700; cursor: pointer; }
.cm-btn:disabled { opacity: .6; cursor: not-allowed; }
.cm-btn--sec { background: #f1f5f9; color: #475569; }
@media (max-width: 768px) {
  .cm-overlay { padding: 0; align-items: flex-end; }
  .cm-box { border-radius: 16px 16px 0 0; max-height: 92vh; }
}
@media (max-width: 576px) {
  .cm-row { padding: 9px 10px; }
  .cm-name { font-size: 13px; }
}
</style>
