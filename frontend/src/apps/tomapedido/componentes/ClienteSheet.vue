<template>
  <div class="velo" @click.self="$emit('cerrar')">
    <div class="hoja">
      <div class="hoja__cab">
        <h2>Cliente del pedido</h2>
        <button class="cerrar" @click="$emit('cerrar')"><Icono nombre="cerrar" /></button>
      </div>
      <div class="hoja__cuerpo">
        <p class="nota">Los precios salen de la lista de precios del cliente.</p>
        <div class="buscar">
          <Icono nombre="buscar" />
          <input v-model="texto" class="entrada" placeholder="Nombre o cédula (mínimo 3)" autofocus @input="buscarLuego" />
        </div>

        <button class="cliente" :class="{ 'cliente--activo': actual?.id === porDefecto.id }" @click="$emit('escoger', porDefecto)">
          <b>{{ porDefecto.nombre }}</b><small>Cliente por defecto</small>
        </button>
        <div v-if="buscando" class="cargando"><span class="giro"></span></div>
        <p v-else-if="texto.length >= 3 && !resultados.length" class="vacio">Sin resultados.</p>
        <button v-for="c in resultados" :key="c.id" class="cliente" :class="{ 'cliente--activo': actual?.id === c.id }"
                @click="$emit('escoger', c)">
          <b>{{ c.nombre }}</b>
          <small>{{ c.cedula }}<template v-if="c.tiene_lista"> · con lista de precios</template></small>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue"
import Icono from "./Icono.vue"
import { api } from "../api"
import { showToast } from "@/utils/toast"

defineProps({ actual: Object, porDefecto: { type: Object, required: true } })
defineEmits(["escoger", "cerrar"])

const texto = ref("")
const resultados = ref([])
const buscando = ref(false)
let espera = null

function buscarLuego() {
  clearTimeout(espera)
  if (texto.value.trim().length < 3) { resultados.value = []; return }
  espera = setTimeout(buscar, 350)
}

async function buscar() {
  buscando.value = true
  try {
    resultados.value = await api.get("/clientes", { q: texto.value.trim() })
  } catch (e) {
    showToast(e.message, "error", 3000)
  } finally {
    buscando.value = false
  }
}
</script>

<style scoped>
.nota { margin: 0 0 10px; color: var(--texto-suave); font-size: 14px; }
.buscar { position: relative; margin-bottom: 12px; }
.buscar .icono { position: absolute; left: 14px; top: 14px; color: var(--texto-suave); }
.buscar .entrada { padding-left: 42px; }
.cliente { display: block; width: 100%; text-align: left; padding: 12px 14px; margin-bottom: 8px; border-radius: 12px; border: 1.5px solid var(--borde); background: #fff; }
.cliente b { display: block; }
.cliente small { color: var(--texto-suave); }
.cliente--activo { border-color: var(--azul); background: var(--azul-claro); }
</style>
