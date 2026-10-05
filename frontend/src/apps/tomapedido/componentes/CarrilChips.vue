<template>
  <!-- Carril horizontal (categorías, zonas…): flechas grandes cuando hay más a un lado,
       rueda del mouse y arrastre táctil; el chip activo se acomoda a la vista -->
  <div class="carril">
    <button v-show="hayIzq" class="carril__flecha carril__flecha--izq" aria-label="Ver anteriores" @click="mover(-1)">
      <Icono nombre="atras" :tam="26" />
    </button>
    <div ref="pista" class="carril__pista" @scroll.passive="medir" @wheel="rueda">
      <slot />
    </div>
    <button v-show="hayDer" class="carril__flecha carril__flecha--der" aria-label="Ver siguientes" @click="mover(1)">
      <Icono nombre="atras" :tam="26" class="girar" />
    </button>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"
import Icono from "./Icono.vue"

const props = defineProps({ activo: { type: [Number, String], default: null } })

const pista = ref(null)
const hayIzq = ref(false)
const hayDer = ref(false)
let observador = null
let cambios = null

function medir() {
  const p = pista.value
  if (!p) return
  hayIzq.value = p.scrollLeft > 4
  hayDer.value = p.scrollLeft + p.clientWidth < p.scrollWidth - 4
}

function mover(sentido) {
  const p = pista.value
  p.scrollBy({ left: sentido * Math.max(160, p.clientWidth * 0.75), behavior: "smooth" })
}

// Rueda vertical del mouse → desplazamiento horizontal (Windows sin pantalla táctil)
function rueda(e) {
  const p = pista.value
  if (Math.abs(e.deltaY) > Math.abs(e.deltaX) && p.scrollWidth > p.clientWidth) {
    e.preventDefault()
    p.scrollBy({ left: e.deltaY, behavior: "auto" })
  }
}

// El chip activo (clase *--activo) se acomoda a la vista
async function mostrarActivo() {
  await nextTick()
  const el = pista.value?.querySelector("[class*='--activo']")
  el?.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" })
}

watch(() => props.activo, mostrarActivo)
onMounted(() => {
  medir()
  observador = new ResizeObserver(medir)
  observador.observe(pista.value)
  // Los chips cambian (carga de datos): se vuelve a medir
  cambios = new MutationObserver(medir)
  cambios.observe(pista.value, { childList: true })
  mostrarActivo()
})
onBeforeUnmount(() => { observador?.disconnect(); cambios?.disconnect() })
</script>

<style scoped>
.carril { position: relative; }
.carril__pista { display: flex; gap: 8px; overflow-x: auto; padding: 2px 0 8px; scrollbar-width: none; scroll-behavior: smooth; }
.carril__pista::-webkit-scrollbar { display: none; }
.carril__flecha {
  position: absolute; top: 50%; transform: translateY(calc(-50% - 3px)); z-index: 2;
  width: 44px; height: 44px; border-radius: 50%; border: 0;
  background: var(--navy); color: #fff; box-shadow: 0 4px 14px rgba(15, 23, 42, .35);
  display: inline-flex; align-items: center; justify-content: center;
}
.carril__flecha:active { transform: translateY(calc(-50% - 3px)) scale(.94); }
.carril__flecha--izq { left: -4px; }
.carril__flecha--der { right: -4px; }
.girar { transform: rotate(180deg); }
/* Desvanecido para que se note que hay más contenido detrás de la flecha */
.carril__flecha--izq::after, .carril__flecha--der::after { content: ""; position: absolute; top: -6px; bottom: -6px; width: 40px; z-index: -1; pointer-events: none; }
.carril__flecha--izq::after { left: 0; background: linear-gradient(90deg, var(--fondo), transparent); }
.carril__flecha--der::after { right: 0; background: linear-gradient(-90deg, var(--fondo), transparent); }

@media (max-width: 768px) {
  .carril__flecha { width: 40px; height: 40px; }
}
@media (max-width: 576px) {
  .carril__flecha { width: 38px; height: 38px; }
}
</style>
