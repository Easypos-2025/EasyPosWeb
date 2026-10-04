<template>
  <div class="pantalla">
    <header class="barra">
      <button class="barra__btn" @click="$router.replace('/cuentas')"><Icono nombre="atras" /></button>
      <div class="barra__titulo"><h1>{{ textos.cuentas }}</h1><small>Escoja dónde montar el pedido</small></div>
      <button class="barra__btn" title="Actualizar" @click="cargar"><Icono nombre="refrescar" /></button>
    </header>

    <main class="contenido">
      <div class="chips">
        <button v-for="z in zonas" :key="z.id" class="chip" :class="{ 'chip--activo': z.id === zonaId, 'chip--color': z.color }"
                :style="estiloZona(z)" @click="zonaId = z.id">
          {{ z.nombre }}
        </button>
      </div>

      <div class="leyenda">
        <span><i class="punto punto--libre"></i>Libre</span>
        <span><i class="punto punto--mia"></i>Mía</span>
        <span><i class="punto punto--ocupada"></i>Otro {{ t("mesero") }}</span>
        <span><i class="punto punto--abierta"></i>Abierta en otro equipo</span>
      </div>

      <div v-if="cargando && !zonas.length" class="cargando"><span class="giro"></span></div>

      <div class="mesas">
        <button v-for="m in zona?.mesas || []" :key="m.id" class="mesa" :class="'mesa--' + m.estado"
                :style="estiloMesa(m)" :disabled="ocupado" @click="tocar(m)">
          <span class="mesa__nombre">{{ m.nombre }}</span>
          <span class="mesa__estado">{{ TEXTO[m.estado] }}</span>
        </button>
      </div>
      <p v-if="zona && !zona.mesas.length && !zona.dinamica" class="vacio">Esta zona no tiene {{ t("cuentas") }} habilitadas.</p>

      <button class="btn btn--ambar btn--bloque nueva" @click="pedirNombre = true">
        <Icono nombre="mas" /> Nueva {{ t("cuenta") }}{{ zona?.dinamica ? " en " + zona.nombre : "" }}
      </button>
    </main>

    <!-- Nombre de la cuenta nueva -->
    <div v-if="pedirNombre" class="velo" @click.self="pedirNombre = false">
      <form class="hoja" @submit.prevent="cuentaNueva">
        <div class="hoja__cab">
          <h2>Nueva {{ t('cuenta') }}</h2>
          <button type="button" class="cerrar" @click="pedirNombre = false"><Icono nombre="cerrar" /></button>
        </div>
        <div class="hoja__cuerpo">
          <label class="campo">
            <span>Nombre</span>
            <input v-model.trim="nombreCuenta" class="entrada" maxlength="50" placeholder="Ej: Juan, Llevar 3, Barra" autofocus />
          </label>
        </div>
        <div class="hoja__pie">
          <button class="btn btn--primario btn--bloque" :disabled="!nombreCuenta">Continuar</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import Icono from "../componentes/Icono.vue"
import { api } from "../api"
import { showToast } from "@/utils/toast"
import { t, textos } from "../textos"

const TEXTO = { libre: "Libre", mia: "Mía", ocupada: "Ocupada", abierta: "En uso" }

const router = useRouter()
const zonas = ref([])
const zonaId = ref(null)
const cargando = ref(false)
const ocupado = ref(false)
const pedirNombre = ref(false)
const nombreCuenta = ref("")
const alto = ref(0)
const zona = computed(() => zonas.value.find(z => z.id === zonaId.value))

// Color y alto configurados en el escritorio (zonas_asientos): agilizan la toma de pedidos
function textoSobre(hex) {
  const n = parseInt(hex.slice(1), 16)
  const lum = (0.299 * (n >> 16) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) / 255
  return lum > 0.6 ? "#1e293b" : "#ffffff"
}
const estiloZona = (z) => (z.color ? { background: z.color, borderColor: z.color, color: textoSobre(z.color) } : {})
function estiloMesa(m) {
  const e = { minHeight: Math.max(64, alto.value) + "px" }
  if (m.estado === "libre" && zona.value?.color) Object.assign(e, { background: zona.value.color, color: textoSobre(zona.value.color) })
  return e
}

async function cargar() {
  cargando.value = true
  try {
    // Zonas sin mesas habilitadas no se muestran (salvo las dinámicas, donde se crean cuentas)
    const r = await api.get("/mesas")
    alto.value = r.alto || 0
    zonas.value = r.zonas.filter(z => z.mesas.length || z.dinamica)
    if (!zona.value) zonaId.value = (zonas.value.find(z => z.mesas.length) || zonas.value[0])?.id ?? null
  } catch (e) {
    showToast(e.message, "error", 3000)
  } finally {
    cargando.value = false
  }
}

async function tocar(m) {
  if (m.estado === "mia") return router.push({ path: "/cuenta", query: { nro: m.nro_pedido } })
  if (m.estado === "ocupada") return showToast(`'${m.nombre}' tiene un pedido de otro ${t("mesero")}.`, "warning", 2500)
  if (m.estado === "abierta") return showToast(`'${m.nombre}' está en uso en otro equipo.`, "warning", 2500)
  ocupado.value = true
  try {
    // Se bloquea mientras se monta el pedido (vence sola si el celular se apaga)
    await api.post("/mesas/bloquear", { id_mesa: m.id, mesa: m.nombre })
    router.push({ path: "/pedido", query: { mesa: m.id, nombre: m.nombre } })
  } catch (e) {
    showToast(e.message, "error", 3000)
    cargar()
  } finally {
    ocupado.value = false
  }
}

function cuentaNueva() {
  if (!nombreCuenta.value) return
  router.push({ path: "/pedido", query: { cuenta: nombreCuenta.value } })
}

onMounted(cargar)
</script>

<style scoped>
.pantalla { min-height: 100vh; }
.leyenda { display: flex; flex-wrap: wrap; gap: 6px 14px; margin: 2px 0 12px; font-size: 12px; color: var(--texto-suave); }
.leyenda span { display: inline-flex; align-items: center; gap: 5px; }
.chip--color.chip--activo { box-shadow: 0 0 0 3px var(--navy); }
.punto { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.punto--libre { background: #fff; border: 2px solid var(--verde); }
.punto--mia { background: var(--azul); }
.punto--ocupada { background: #94a3b8; }
.punto--abierta { background: var(--ambar); }

.mesas { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.mesa {
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px;
  min-height: 84px; padding: 8px; border-radius: 14px; border: 2px solid var(--verde);
  background: #fff; box-shadow: var(--sombra);
}
.mesa:active { transform: scale(.97); }
.mesa__nombre { font-weight: 800; font-size: 16px; text-align: center; word-break: break-word; }
.mesa__estado { font-size: 12px; opacity: .75; }
.mesa--mia { background: var(--azul); border-color: var(--azul); color: #fff; }
.mesa--ocupada { background: #e2e8f0; border-color: #cbd5e1; color: #64748b; }
.mesa--abierta { background: var(--ambar-claro); border-color: var(--ambar); }
.nueva { margin-top: 16px; }

@media (min-width: 769px) {
  .mesas { grid-template-columns: repeat(6, 1fr); }
  .nueva { max-width: 420px; }
}
@media (max-width: 768px) and (min-width: 577px) {
  .mesas { grid-template-columns: repeat(4, 1fr); }
}
@media (max-width: 576px) {
  .mesas { gap: 8px; }
  .mesa { min-height: 74px; }
  .mesa__nombre { font-size: 15px; }
}
</style>
