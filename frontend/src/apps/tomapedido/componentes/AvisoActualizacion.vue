<template>
  <!-- Opción A: actualizar el agente con un clic (la B es automática al abrir turno) -->
  <div v-if="a?.disponible" class="av tarjeta">
    <div class="av__ico"><Icono nombre="refrescar" :tam="26" /></div>
    <div class="av__txt">
      <b>Actualización disponible: versión {{ a.nueva }}</b>
      <small v-if="a.notas">{{ a.notas }}</small>
      <small>Si no la aplica ahora, se instala sola al abrir el próximo turno. Tarda menos de un minuto.</small>
      <small v-if="a.error" class="av__error">{{ a.error }}</small>
    </div>
    <button class="btn btn--primario" :disabled="!a.lista || a.aplicando" @click="actualizar">
      <span v-if="!a.lista" class="giro" style="width:18px;height:18px;border-width:2px"></span>
      {{ a.lista ? "Actualizar ahora" : "Descargando…" }}
    </button>
  </div>

  <div v-if="trabajando" class="velo av__velo">
    <div class="av__progreso tarjeta">
      <span class="giro"></span>
      <h3>Actualizando a la versión {{ a?.nueva }}…</h3>
      <p>No cierre esta ventana. Los dispositivos verán unos segundos el aviso de "sin conexión" y luego siguen normal.</p>
      <p v-if="mensaje" class="av__error">{{ mensaje }}</p>
    </div>
  </div>
</template>

<script setup>
import { inject, ref } from "vue"
import Icono from "./Icono.vue"
import { api } from "../api"
import { showConfirm, showToast } from "@/utils/toast"

const a = inject("actualizacion")
const trabajando = ref(false)
const mensaje = ref("")

// Versión que responde el agente (sin pasar por el aviso de "sin conexión": durante la
// actualización el agente se detiene unos segundos a propósito)
async function versionAgente() {
  try {
    const r = await fetch("/api/ag/salud", { cache: "no-store" })
    return r.ok ? (await r.json()).version : null
  } catch { return null }
}

async function actualizar() {
  if (!(await showConfirm(`¿Actualizar el agente a la versión ${a.value.nueva}? Se detiene menos de un minuto.`, "Sí, actualizar"))) return
  try {
    await api.admin.post("/actualizar")
  } catch (e) {
    showToast(e.message, "error", 4000)
    return
  }
  trabajando.value = true
  const nueva = a.value.nueva
  const fin = Date.now() + 3 * 60 * 1000
  while (Date.now() < fin) {
    await new Promise(r => setTimeout(r, 3000))
    const v = await versionAgente()
    if (v === nueva) { location.reload(); return }
  }
  mensaje.value = "La actualización no se completó; el agente volvió a la versión anterior. Revise la sección Errores."
  setTimeout(() => location.reload(), 6000)
}
</script>

<style scoped>
.av { display: flex; align-items: center; gap: 14px; padding: 14px 16px; margin-bottom: 14px; border: 2px solid var(--azul); }
.av__ico { width: 46px; height: 46px; flex-shrink: 0; border-radius: 12px; background: var(--azul-claro); color: var(--azul);
           display: inline-flex; align-items: center; justify-content: center; }
.av__txt { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.av__txt small { color: var(--texto-suave); }
.av__error { color: var(--rojo) !important; }
.av__velo { align-items: center; z-index: 95000; }
.av__progreso { max-width: 420px; margin: 16px; padding: 26px 22px; text-align: center; }
.av__progreso h3 { margin: 14px 0 8px; }
.av__progreso p { color: var(--texto-suave); font-size: 14px; }
.av__progreso .giro { margin: 0 auto; display: block; }

@media (max-width: 768px) {
  .av { flex-wrap: wrap; }
  .av .btn { width: 100%; }
}
@media (max-width: 576px) {
  .av { padding: 12px; }
}
</style>
