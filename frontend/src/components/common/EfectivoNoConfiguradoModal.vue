<template>
  <!-- Ventana global (App.vue): forma de pago EFECTIVO sin configurar (CLAUDE.md §8.10) -->
  <div v-if="avisoEfectivo.visible" class="efx-overlay" role="alertdialog" aria-modal="true" aria-labelledby="efx-title">
    <div class="efx-card">
      <div class="efx-head">
        <i class="bi bi-cash-coin efx-icon"></i>
        <div>
          <h2 id="efx-title" class="efx-title">Falta configurar la forma de pago EFECTIVO</h2>
          <p class="efx-sub">Mientras no se corrija, el sistema no deja registrar pedidos, pagos ni movimientos de caja, ni generar reportes.</p>
        </div>
      </div>

      <div class="efx-problema">
        <div class="efx-label"><i class="bi bi-exclamation-triangle-fill"></i> ¿Qué está pasando?</div>
        <p>{{ problemaTexto }}</p>
        <p class="efx-nota">El sistema identifica el dinero en efectivo con la forma de pago marcada como <strong>Default</strong>. Debe existir <strong>una sola</strong> y debe estar <strong>Activa</strong>; con ella se calculan el cuadre de caja, el efectivo a entregar y todos los reportes de venta.</p>
      </div>

      <div class="efx-pasos">
        <div class="efx-label"><i class="bi bi-tools"></i> Cómo solucionarlo (administrador de caja)</div>
        <ol>
          <li>Entre a <strong>{{ nombrePadre }} → {{ nombreModulo }}</strong>.</li>
          <li>Edite la forma de pago <strong>EFECTIVO</strong> (o la que usen para el dinero en efectivo).</li>
          <li>Marque <strong>Predeterminado (Default)</strong> y <strong>Activo</strong>, y guarde. Las demás se desmarcan solas.</li>
          <li>Si la empresa trabaja también con el programa de escritorio, márquela allá igual (forma de pago default y activa) para que coincidan.</li>
        </ol>
      </div>

      <p v-if="!puedeConfigurar" class="efx-aviso">
        <i class="bi bi-person-badge"></i>
        Usted no tiene acceso a esa configuración: <strong>avise de inmediato al administrador de caja</strong> para que la corrija y puedan seguir trabajando.
      </p>

      <div class="efx-acciones">
        <button v-if="puedeConfigurar" class="efx-btn efx-btn-primary" @click="irAFormasPago">
          <i class="bi bi-gear"></i> Ir a {{ nombreModulo }}
        </button>
        <button v-if="tieneSesion" class="efx-btn efx-btn-sec" :disabled="revisando" @click="revisar">
          <i :class="revisando ? 'bi bi-arrow-repeat efx-spin' : 'bi bi-arrow-clockwise'"></i> Ya lo corregí, revisar
        </button>
        <button class="efx-btn efx-btn-link" @click="cerrarAvisoEfectivo">Entendido</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from "vue"
import { useRouter } from "vue-router"
import { useMenuStore } from "@/stores/menuStore"
import { avisoEfectivo, cerrarAvisoEfectivo, revisarEfectivo } from "@/utils/efectivoAviso"
import { useModuleName } from "@/composables/useModuleName"
import { showToast } from "@/utils/toast"

const RUTA = "/payment-types"
const router = useRouter()
const menuStore = useMenuStore()
const { moduleName: moduloFormasPago } = useModuleName(RUTA)
const revisando = ref(false)

const nombreModulo = computed(() => moduloFormasPago.value || "Formas de Pago")
const tieneSesion = computed(() => !!localStorage.getItem("token") && !localStorage.getItem("waiter_token"))

function enMenu(items) {
  return (items || []).some(m => m.route === RUTA || enMenu(m.children))
}
// Nombre del padre en el sidebar (system_modules), ej. "Configuración"
function padreDe(items, padre = null) {
  for (const m of items || []) {
    if (m.route === RUTA) return padre
    const p = padreDe(m.children, m)
    if (p !== undefined) return p
  }
  return undefined
}
const nombrePadre = computed(() => padreDe(menuStore.menu)?.name || "Configuración")
const puedeConfigurar = computed(() => tieneSesion.value && enMenu(menuStore.menu))

const problemaTexto = computed(() => {
  const e = avisoEfectivo.estado
  if (e && !e.ok) {
    if (e.problema === "ninguna") return "No hay ninguna forma de pago marcada como Default (Predeterminado)."
    if (e.problema === "varias") return `Hay ${e.defaults.length} formas de pago marcadas como Default (${e.defaults.join(", ")}) y solo puede haber una.`
    if (e.problema === "inactiva") return `La forma de pago Default «${e.defaults[0]}» está inactiva.`
  }
  return avisoEfectivo.mensaje || "La forma de pago EFECTIVO no está configurada."
})

function irAFormasPago() {
  cerrarAvisoEfectivo()
  router.push(RUTA)
}

async function revisar() {
  revisando.value = true
  const est = await revisarEfectivo({ forzar: true, abrir: false })
  revisando.value = false
  if (est?.ok) {
    cerrarAvisoEfectivo()
    showToast("Forma de pago EFECTIVO configurada. Ya puede continuar.", "success", 2500)
  } else if (est) {
    showToast("Todavía no está corregido", "warning", 2500)
  }
}
</script>

<style scoped>
.efx-overlay {
  position: fixed; inset: 0; z-index: 3000;
  background: rgba(15, 23, 42, .62);
  display: flex; align-items: center; justify-content: center;
  padding: 16px;
}
.efx-card {
  background: #fff; color: #1e293b;
  width: 100%; max-width: 640px; max-height: calc(100vh - 32px); overflow-y: auto;
  border-radius: 16px; border-top: 6px solid #dc2626;
  box-shadow: 0 20px 50px rgba(0, 0, 0, .3);
  padding: 24px 26px;
}
.efx-head { display: flex; gap: 14px; align-items: flex-start; margin-bottom: 16px; }
.efx-icon { font-size: 2.6rem; color: #dc2626; line-height: 1; }
.efx-title { font-size: 1.35rem; font-weight: 800; margin: 0 0 4px; color: #991b1b; }
.efx-sub { margin: 0; font-size: .95rem; color: #475569; }
.efx-label { font-weight: 700; font-size: .9rem; margin-bottom: 6px; display: flex; gap: 6px; align-items: center; }
.efx-problema {
  background: #fef2f2; border: 1px solid #fecaca; border-radius: 10px;
  padding: 12px 14px; margin-bottom: 14px;
}
.efx-problema p { margin: 0 0 6px; font-size: .95rem; }
.efx-problema .efx-label { color: #b91c1c; }
.efx-nota { font-size: .85rem !important; color: #475569; margin-bottom: 0 !important; }
.efx-pasos {
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 12px 14px; margin-bottom: 14px;
}
.efx-pasos .efx-label { color: #1d4ed8; }
.efx-pasos ol { margin: 0; padding-left: 20px; font-size: .92rem; }
.efx-pasos li { margin-bottom: 4px; }
.efx-aviso {
  background: #fffbeb; border: 1px solid #fde68a; border-radius: 10px;
  padding: 10px 14px; font-size: .92rem; margin-bottom: 14px;
}
.efx-acciones { display: flex; gap: 10px; justify-content: flex-end; flex-wrap: wrap; }
.efx-btn {
  border: 0; border-radius: 10px; padding: 10px 16px; font-weight: 700; font-size: .95rem;
  display: inline-flex; gap: 6px; align-items: center; cursor: pointer;
}
.efx-btn:disabled { opacity: .6; cursor: default; }
.efx-btn-primary { background: #1d4ed8; color: #fff; }
.efx-btn-sec { background: #e2e8f0; color: #1e293b; }
.efx-btn-link { background: transparent; color: #475569; }
.efx-spin { animation: efx-spin 1s linear infinite; }
@keyframes efx-spin { to { transform: rotate(360deg); } }

@media (max-width: 768px) {
  .efx-card { padding: 20px 18px; }
  .efx-title { font-size: 1.2rem; }
  .efx-icon { font-size: 2.2rem; }
}
@media (max-width: 576px) {
  .efx-overlay { padding: 8px; align-items: flex-end; }
  .efx-card { max-height: calc(100vh - 16px); border-radius: 14px; padding: 16px 14px; }
  .efx-head { gap: 10px; }
  .efx-title { font-size: 1.08rem; }
  .efx-sub, .efx-problema p, .efx-pasos ol, .efx-aviso { font-size: .88rem; }
  .efx-acciones { flex-direction: column-reverse; }
  .efx-btn { width: 100%; justify-content: center; }
}
</style>
