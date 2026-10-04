<template>
  <div class="velo" @click.self="$emit('cerrar')">
    <div class="hoja">
      <div class="hoja__cab">
        <h2>Pedido · {{ titulo }}</h2>
        <button class="cerrar" @click="$emit('cerrar')"><Icono nombre="cerrar" /></button>
      </div>

      <div class="hoja__cuerpo">
        <p v-if="!lineas.length" class="vacio">No ha agregado productos.</p>
        <div v-for="l in lineas" :key="l.clave" class="linea">
          <div class="linea__info">
            <b>{{ l.nombre }}</b>
            <small v-if="l.detalle">{{ l.detalle }}</small>
            <span class="linea__precio">{{ pesos(l.unitario) }} c/u</span>
          </div>
          <div class="linea__acciones">
            <div class="mini">
              <button @click="cambiar(l, -1)" :disabled="l.cantidad <= 1"><Icono nombre="menos" :tam="16" /></button>
              <span>{{ cantidad(l.cantidad) }}</span>
              <button @click="cambiar(l, 1)" :disabled="l.cantidad >= 50"><Icono nombre="mas" :tam="16" /></button>
            </div>
            <b>{{ pesos(valorLinea(l.unitario, l.cantidad)) }}</b>
            <button class="quitar" title="Quitar" @click="$emit('quitar', l)"><Icono nombre="basura" :tam="18" /></button>
          </div>
        </div>
      </div>

      <div class="hoja__pie">
        <div class="total"><span>Total</span><b>{{ pesos(total) }}</b></div>
        <button class="btn btn--primario btn--bloque" :disabled="!lineas.length || enviando" @click="$emit('enviar')">
          <span v-if="enviando" class="giro" style="width:20px;height:20px;border-width:2px"></span>
          <template v-else><Icono nombre="enviar" /> Enviar pedido</template>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue"
import Icono from "./Icono.vue"
import { cantidad, pesos, valorLinea } from "../formato"

const props = defineProps({
  lineas: { type: Array, required: true },
  titulo: { type: String, default: "" },
  enviando: { type: Boolean, default: false },
})
defineEmits(["cerrar", "quitar", "enviar"])

const total = computed(() => props.lineas.reduce((s, l) => s + valorLinea(l.unitario, l.cantidad), 0))

// Los pasos son de 1 en 1 y conservan la fracción (1,5 → 2,5)
function cambiar(l, d) {
  l.cantidad = Math.max(Math.min(l.cantidad + d, 50), Math.min(l.cantidad, 1))
  l.cantidad = Math.round(l.cantidad * 1000) / 1000
}
</script>

<style scoped>
.linea { display: flex; flex-direction: column; gap: 8px; padding: 12px 0; border-bottom: 1px solid var(--borde); }
.linea__info b { display: block; }
.linea__info small { display: block; color: var(--texto-suave); font-size: 13px; }
.linea__precio { font-size: 13px; color: var(--texto-suave); }
.linea__acciones { display: flex; align-items: center; gap: 12px; }
.linea__acciones > b { flex: 1; text-align: right; }
.mini { display: inline-flex; align-items: center; gap: 4px; background: var(--fondo); border-radius: 10px; padding: 3px; }
.mini button { width: 34px; height: 34px; border: 0; border-radius: 8px; background: #fff; display: inline-flex; align-items: center; justify-content: center; }
.mini button:disabled { opacity: .4; }
.mini span { min-width: 44px; text-align: center; font-weight: 700; }
.quitar { width: 38px; height: 38px; border: 0; border-radius: 10px; background: var(--rojo-claro); color: var(--rojo); display: inline-flex; align-items: center; justify-content: center; }
.total { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; font-size: 18px; }
.total b { font-size: 22px; color: var(--azul); }

@media (min-width: 577px) {
  .linea { flex-direction: row; align-items: center; justify-content: space-between; }
  .linea__acciones { flex-shrink: 0; }
}
@media (max-width: 576px) {
  .total b { font-size: 20px; }
}
</style>
