<template>
  <!-- Campos de la tabla proveedores del escritorio. Obligatorios: Empresa, NIT y Teléfono celular -->
  <div class="pc">
    <div class="fg">
      <label>Nombre / Empresa *</label>
      <input :value="modelValue.name" @input="set('name', $event)" class="form-control" maxlength="255"
             placeholder="Nombre del proveedor" v-focus />
    </div>
    <div class="pc-row2">
      <div class="fg">
        <label>NIT *</label>
        <input :value="modelValue.nit" @input="set('nit', $event)" class="form-control" maxlength="50" placeholder="900123456-7" />
      </div>
      <div class="fg">
        <label>Teléfono celular *</label>
        <input :value="modelValue.telefono_celular" @input="set('telefono_celular', $event)" class="form-control"
               maxlength="50" inputmode="tel" placeholder="300 000 0000" />
      </div>
    </div>
    <div class="pc-row2">
      <div class="fg">
        <label>Teléfono fijo</label>
        <input :value="modelValue.phone" @input="set('phone', $event)" class="form-control" maxlength="50" inputmode="tel" />
      </div>
      <div class="fg">
        <label>Email</label>
        <input :value="modelValue.email" @input="set('email', $event)" class="form-control" type="email" maxlength="255"
               placeholder="proveedor@empresa.com" />
      </div>
    </div>
    <div class="fg">
      <label>Dirección</label>
      <input :value="modelValue.address" @input="set('address', $event)" class="form-control" maxlength="50" />
    </div>
    <div class="fg">
      <label>Observaciones</label>
      <input :value="modelValue.notes" @input="set('notes', $event)" class="form-control" maxlength="50" />
    </div>
  </div>
</template>

<script>
const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/

export function proveedorVacio() {
  return { name: "", nit: "", telefono_celular: "", phone: "", email: "", address: "", notes: "" }
}

// Devuelve el primer error o "" si está completo
export function validarProveedor(f) {
  if (!String(f.name || "").trim()) return "El nombre del proveedor es obligatorio"
  if (!String(f.nit || "").trim()) return "El NIT es obligatorio"
  if (!String(f.telefono_celular || "").trim()) return "El teléfono celular es obligatorio"
  if (f.email && !EMAIL.test(String(f.email).trim())) return "El correo no es válido"
  return ""
}
</script>

<script setup>
const props = defineProps({ modelValue: { type: Object, required: true } })
const emit = defineEmits(["update:modelValue"])
const vFocus = { mounted: el => el.focus() }

function set(campo, e) {
  emit("update:modelValue", { ...props.modelValue, [campo]: e.target.value })
}
</script>

<style scoped>
.pc { display: flex; flex-direction: column; gap: 12px; }
.pc-row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.fg { display: flex; flex-direction: column; gap: 4px; }
.fg label { font-size: 12px; font-weight: 600; color: #374151; }
@media (max-width: 768px) {
  .pc { gap: 10px; }
}
@media (max-width: 576px) {
  .pc-row2 { grid-template-columns: 1fr; }
}
</style>
