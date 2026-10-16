<template>
  <!-- El usuario logueado queda como empleado y mesero (mismo código, ligado a su usuario) -->
  <div class="am-fondo" @click.self="$emit('close')">
    <div class="am-box">
      <div class="am-h">
        <h3><i class="bi bi-person-plus me-2"></i>Agregarme como mesero</h3>
        <button class="am-x" @click="$emit('close')"><i class="bi bi-x-lg"></i></button>
      </div>
      <div class="am-body">
        <div class="am-yo">
          <strong>{{ nombre || 'Usuario' }}</strong>
          <span>{{ email }}</span>
        </div>
        <div class="am-fg">
          <label>Teléfono *</label>
          <input v-model="f.phone" class="form-control" maxlength="50" inputmode="tel" v-focus />
        </div>
        <div class="am-fg">
          <label>Tipo de empleado *</label>
          <select v-model="f.employee_type" class="form-select">
            <option :value="null">— Seleccione —</option>
            <option v-for="t in tiposOrden" :key="t.cod_tipo" :value="t.cod_tipo">{{ t.name }}</option>
          </select>
        </div>
        <div class="am-fg">
          <label>Clave (PIN) *</label>
          <input v-model="f.pin" class="form-control" type="password" inputmode="numeric" maxlength="8"
                 autocomplete="new-password" placeholder="4 a 8 números" @keydown.enter="guardar" />
        </div>
      </div>
      <div class="am-f">
        <button class="am-btn am-sec" @click="$emit('close')">Cancelar</button>
        <button class="am-btn am-pri" @click="guardar" :disabled="saving">{{ saving ? 'Guardando...' : 'Agregarme' }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import api from "@/services/apis"
import { showToast } from "@/utils/toast"
import { ordenAlfa } from "@/utils/orden"

const props = defineProps({ tipos: { type: Array, default: null } })
const emit = defineEmits(["close", "creado"])
const vFocus = { mounted: el => el.focus() }

const f = ref({ phone: "", employee_type: null, pin: "" })
const lista = ref(props.tipos || [])
const nombre = ref("")
const email = ref("")
const saving = ref(false)
const tiposOrden = computed(() => ordenAlfa(lista.value, "name"))

onMounted(async () => {
  try {
    const [y, t] = await Promise.all([api.get("/api/personal/yo"), props.tipos ? null : api.get("/api/personal/tipos")])
    nombre.value = y.data.nombre
    email.value = y.data.email
    if (t) lista.value = t.data
  } catch (e) { showToast(e.response?.data?.detail || "No se pudo cargar la información", "error") }
})

async function guardar() {
  const v = f.value
  if (!v.phone.trim()) return showToast("El teléfono es obligatorio", "warning")
  if (v.employee_type === null) return showToast("Seleccione el tipo de empleado", "warning")
  if (!/^\d{4,8}$/.test(v.pin)) return showToast("La clave debe tener de 4 a 8 números", "warning")
  saving.value = true
  try {
    const { data } = await api.post("/api/personal/agregarme", { phone: v.phone.trim(), employee_type: v.employee_type, pin: v.pin })
    showToast("Quedó registrado como mesero", "success")
    emit("creado", data)
  } catch (e) { showToast(e.response?.data?.detail || "No se pudo registrar", "error") }
  finally { saving.value = false }
}
</script>

<style scoped>
.am-fondo { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 2100; padding: 16px; }
.am-box { background: #fff; border-radius: 16px; width: 100%; max-width: 420px; box-shadow: 0 20px 60px rgba(0,0,0,.2); display: flex; flex-direction: column; }
.am-h { display: flex; align-items: center; justify-content: space-between; padding: 14px 20px; border-bottom: 1px solid #f1f5f9; }
.am-h h3 { font-size: 15px; font-weight: 700; margin: 0; color: #1e293b; }
.am-x { background: none; border: none; font-size: 16px; color: #94a3b8; cursor: pointer; }
.am-body { padding: 16px 20px; display: flex; flex-direction: column; gap: 12px; }
.am-yo { display: flex; flex-direction: column; background: #f8fafc; border-radius: 10px; padding: 10px 12px; font-size: 13px; }
.am-yo span { color: #64748b; font-size: 12px; }
.am-fg { display: flex; flex-direction: column; gap: 4px; }
.am-fg label { font-size: 12px; font-weight: 600; color: #374151; }
.am-f { padding: 12px 20px 16px; display: flex; justify-content: flex-end; gap: 8px; border-top: 1px solid #f1f5f9; }
.am-btn { border: none; border-radius: 8px; padding: 8px 16px; font-size: 13px; font-weight: 600; cursor: pointer; }
.am-btn:disabled { opacity: .6; cursor: not-allowed; }
.am-pri { background: #3b82f6; color: #fff; }
.am-sec { background: #fff; color: #64748b; border: 1.5px solid #e2e8f0; }
@media (max-width: 768px) {
  .am-fondo { padding: 0; align-items: flex-end; }
  .am-box { max-width: none; border-radius: 16px 16px 0 0; }
}
@media (max-width: 576px) {
  .am-f .am-btn { flex: 1; }
}
</style>
