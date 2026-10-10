<template>
  <!-- Celular/tablet: hoja que se abre con "Ver pedido". PC (panel): siempre visible a la derecha,
       se va llenando mientras se monta el pedido y se envía sin pasos previos. -->
  <div :class="panel ? 'panel' : 'velo'" @click.self="!panel && $emit('cerrar')">
    <div :class="panel ? 'panel__caja tarjeta' : 'hoja'">
      <div class="hoja__cab">
        <h2>Pedido · {{ titulo }}<small v-if="panel && lineas.length"> ({{ lineas.length }})</small></h2>
        <button v-if="!panel" class="cerrar" @click="$emit('cerrar')"><Icono nombre="cerrar" /></button>
      </div>

      <div class="hoja__cuerpo">
        <h3 v-if="enviados.length" class="seccion">Por enviar</h3>
        <p v-if="!lineas.length" class="vacio">{{ panel ? `Toque un ${t("producto")} para agregarlo al pedido.` : `No ha agregado ${t("productos")}.` }}</p>
        <div v-for="l in lineasDesc" :key="l.clave" class="linea">
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

        <!-- Agregando a una cuenta abierta: lo ya enviado, solo para consulta (Impreso = 1 → no se elimina) -->
        <template v-if="enviados.length">
          <h3 class="seccion seccion--enviado">Ya enviado</h3>
          <div v-for="l in enviadosDesc" :key="'e' + l.depende" class="linea linea--enviada">
            <div class="linea__info">
              <b>{{ cantidad(l.cantidad) }} × {{ l.nombre }}</b>
              <small v-if="l.novedad">{{ l.novedad }}</small>
              <span class="estado" :class="l.impreso ? 'estado--impreso' : 'estado--pendiente'">
                <Icono :nombre="l.impreso ? 'impresora' : 'reloj'" :tam="12" />
                {{ l.impreso ? "Impreso" : "Por imprimir" }}
              </span>
            </div>
            <b class="linea__valor">{{ pesos(l.subtotal) }}</b>
          </div>
        </template>
      </div>

      <div class="hoja__pie">
        <div v-if="enviados.length" class="subtotal"><span>Por enviar</span><b>{{ pesos(total) }}</b></div>
        <div class="total"><span>{{ enviados.length ? "Total cuenta" : "Total" }}</span><b>{{ pesos(total + totalEnviado) }}</b></div>
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
import { t } from "../textos"

const props = defineProps({
  lineas: { type: Array, required: true },
  titulo: { type: String, default: "" },
  enviando: { type: Boolean, default: false },
  panel: { type: Boolean, default: false },
  enviados: { type: Array, default: () => [] },     // lo ya enviado de la cuenta (al agregar productos)
})
defineEmits(["cerrar", "quitar", "enviar"])

// Último agregado, primero en mostrar
const lineasDesc = computed(() => [...props.lineas].reverse())

// Ítem descendente (Depende = primer ítem de la línea), igual que la vista de la cuenta
const enviadosDesc = computed(() => [...props.enviados].sort((a, b) => b.depende - a.depende))
const totalEnviado = computed(() => props.enviados.reduce((s, l) => s + (l.subtotal || 0), 0))

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
.seccion { margin: 4px 0 2px; font-size: 12px; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; color: var(--azul); }
.seccion--enviado { margin-top: 18px; color: var(--texto-suave); }
.linea--enviada { flex-direction: row; align-items: center; justify-content: space-between; gap: 10px; padding: 10px 0; opacity: .75; }
.linea--enviada .linea__info { min-width: 0; }
.linea--enviada .linea__info b { font-weight: 600; word-break: break-word; }
.linea__valor { flex-shrink: 0; font-weight: 600; color: var(--texto-suave); }
.estado { display: inline-flex; align-items: center; gap: 4px; margin-top: 4px; padding: 1px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; }
.estado--impreso { background: var(--verde-claro); color: var(--verde); }
.estado--pendiente { background: var(--ambar-claro); color: #92400e; }
.subtotal { display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 14px; color: var(--texto-suave); }
.total { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; font-size: 18px; }
.total b { font-size: 22px; color: var(--azul); }

/* Panel fijo (PC) */
.panel { height: 100%; }
.panel__caja { display: flex; flex-direction: column; height: 100%; overflow: hidden; padding: 0; }
.panel__caja .hoja__cab h2 small { font-size: 14px; color: var(--texto-suave); font-weight: 600; }
.panel__caja .linea { flex-direction: column; align-items: stretch; }
.panel__caja .linea--enviada { flex-direction: row; align-items: center; }
.panel__caja .vacio { margin-top: 30px; }

@media (min-width: 577px) {
  .linea { flex-direction: row; align-items: center; justify-content: space-between; }
  .linea__acciones { flex-shrink: 0; }
}
@media (max-width: 768px) {
  .linea--enviada { padding: 9px 0; }
}
@media (max-width: 576px) {
  .total b { font-size: 20px; }
  .linea--enviada .linea__info b { font-size: 14px; }
}
</style>
