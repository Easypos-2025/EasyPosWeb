<template>
  <!-- Número de comensales con teclado tipo calculadora (variables_del_sistema.Pedir_Cantidad_Comenzales) -->
  <div class="velo" @click.self="cerrar">
    <div class="hoja teclado">
      <div class="hoja__cab">
        <h2>Comensales{{ titulo ? " · " + titulo.trim() : "" }}</h2>
        <button type="button" class="cerrar" title="Cerrar" @click="cerrar"><Icono nombre="cerrar" /></button>
      </div>
      <div class="hoja__cuerpo">
        <div class="pantalla-num" :class="{ 'pantalla-num--vacia': !numero }">
          <Icono nombre="personas" :tam="26" />
          <span>{{ numero || "0" }}</span>
        </div>
        <div class="rapidos">
          <button v-for="n in RAPIDOS" :key="'r' + n" type="button" class="rapido"
                  :class="{ 'rapido--activo': Number(numero) === n }" @click="numero = String(n)">{{ n }}</button>
        </div>
        <div class="teclas">
          <button v-for="n in [7, 8, 9, 4, 5, 6, 1, 2, 3]" :key="n" type="button" class="tecla" @click="digitar(n)">{{ n }}</button>
          <button type="button" class="tecla tecla--suave" title="Borrar todo" @click="numero = ''">C</button>
          <button type="button" class="tecla" @click="digitar(0)">0</button>
          <button type="button" class="tecla tecla--suave" title="Borrar" @click="numero = numero.slice(0, -1)">
            <Icono nombre="borrar" :tam="22" />
          </button>
        </div>
        <p class="ayuda">Entre 1 y {{ MAXIMO }}</p>
      </div>
      <div class="hoja__pie">
        <button type="button" class="btn btn--primario btn--bloque" :disabled="!valido || guardando" @click="aceptar">
          <span v-if="guardando" class="giro giro--chico"></span>
          <Icono v-else nombre="check" :tam="18" /> Aceptar
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue"
import Icono from "./Icono.vue"

const MAXIMO = 99
const RAPIDOS = [1, 2, 3, 4, 5, 6]

const props = defineProps({
  inicial: { type: Number, default: 0 },
  titulo: { type: String, default: "" },
  guardando: { type: Boolean, default: false },
})
const emit = defineEmits(["aceptar", "cerrar"])

const numero = ref(props.inicial > 0 ? String(props.inicial) : "")
const valido = computed(() => Number(numero.value) >= 1 && Number(numero.value) <= MAXIMO)

function digitar(n) {
  const nuevo = (numero.value + n).replace(/^0+/, "")
  if (Number(nuevo) <= MAXIMO) numero.value = nuevo
}

function aceptar() {
  if (valido.value && !props.guardando) emit("aceptar", Number(numero.value))
}

function cerrar() {
  if (!props.guardando) emit("cerrar")
}

// Teclado físico (PC / tablet con teclado)
function alTeclear(e) {
  if (/^[0-9]$/.test(e.key)) digitar(Number(e.key))
  else if (e.key === "Backspace") numero.value = numero.value.slice(0, -1)
  else if (e.key === "Enter") aceptar()
  else if (e.key === "Escape") cerrar()
  else return
  e.preventDefault()
}
onMounted(() => document.addEventListener("keydown", alTeclear))
onBeforeUnmount(() => document.removeEventListener("keydown", alTeclear))
</script>

<style scoped>
.velo { z-index: 60; }
.teclado { max-width: 420px; }
.cerrar { display: inline-flex; border: 0; background: none; color: var(--texto-suave); padding: 6px; }
.pantalla-num { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 10px 14px; margin-bottom: 12px;
                border-radius: 14px; background: var(--azul-claro); color: var(--azul); }
.pantalla-num span { font-size: 44px; font-weight: 800; line-height: 1; min-width: 2ch; text-align: center; }
.pantalla-num--vacia span { opacity: .35; }
.rapidos { display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; margin-bottom: 12px; }
.rapido { min-height: 40px; border: 1.5px solid var(--borde); border-radius: 10px; background: #fff; font-weight: 700; font-size: 16px; }
.rapido--activo { border-color: var(--azul); background: var(--azul); color: #fff; }
.teclas { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.tecla { display: inline-flex; align-items: center; justify-content: center; min-height: 58px; border: 0; border-radius: 14px;
         background: #fff; box-shadow: 0 1px 3px rgba(15, 23, 42, .15); font-size: 24px; font-weight: 700; user-select: none; }
.tecla:active, .rapido:active { transform: scale(.96); }
.tecla--suave { background: var(--fondo); color: var(--texto-suave); font-size: 20px; }
.ayuda { margin: 10px 0 0; text-align: center; font-size: 12px; color: var(--texto-suave); }
.giro--chico { width: 18px; height: 18px; border-width: 2px; }

@media (max-width: 768px) {
  .teclado { max-width: none; }
}
@media (max-width: 576px) {
  .pantalla-num span { font-size: 38px; }
  .tecla { min-height: 54px; font-size: 22px; }
  .rapidos { gap: 6px; }
  .rapido { min-height: 38px; font-size: 15px; }
}
</style>
