<template>
  <div class="velo" @click.self="$emit('cerrar')">
    <div class="hoja">
      <div class="hoja__cab">
        <h2>{{ plato.nombre }}</h2>
        <button class="cerrar" @click="$emit('cerrar')"><Icono nombre="cerrar" /></button>
      </div>

      <div class="hoja__cuerpo">
        <!-- Presentaciones: obligatorio escoger una -->
        <section v-if="plato.presentaciones" class="bloque">
          <h3>Presentación</h3>
          <div class="presentaciones">
            <button v-for="p in plato.presentaciones" :key="p.id" class="pres" :class="{ 'pres--activa': presentacion?.id === p.id }"
                    @click="presentacion = p">
              <b>{{ p.nombre }}</b>
              <span>{{ pesos(p.precio) }}</span>
              <small v-if="p.unidades !== 1">descarga {{ cantidad(p.unidades) }}</small>
            </button>
          </div>
        </section>

        <!-- Precio digitado (solo platos con "pedir precio") -->
        <section v-if="plato.pedir_precio" class="bloque">
          <label class="campo">
            <span>Precio de venta</span>
            <input v-model="precioTxt" class="entrada" inputmode="numeric" placeholder="$ 0" @input="soloDigitos" />
          </label>
          <small v-if="plato.impuesto_aparte" class="nota">Se suma el impuesto ({{ plato.impuesto_aparte }} %).</small>
        </section>

        <!-- Descripción (solo platos con "pedir descripción") -->
        <section v-if="plato.pedir_descripcion" class="bloque">
          <label class="campo">
            <span>Descripción</span>
            <input v-model="descripcion" class="entrada" maxlength="150" />
          </label>
        </section>

        <!-- Menú del día / armado -->
        <section v-if="plato.armado" class="bloque">
          <div v-if="cargandoOps" class="cargando"><span class="giro"></span></div>
          <p v-else-if="errorOps" class="aviso">{{ errorOps }}</p>
          <!-- Acordeón (orden alfabético): solo un grupo abierto; el encabezado dice cuántos lleva escogidos -->
          <div v-for="g in grupos" :key="g.grupo" class="grupo" :class="{ 'grupo--abierto': abierto === g.grupo }">
            <button type="button" class="grupo__cab" :aria-expanded="abierto === g.grupo" @click="abrir(g)">
              <span class="grupo__nombre">{{ g.nombre }}</span>
              <span class="grupo__cuenta" :class="{ 'grupo__cuenta--falta': g.exigir && !seleccion[g.grupo]?.size }">
                {{ seleccion[g.grupo]?.size || 0 }} {{ (seleccion[g.grupo]?.size || 0) === 1 ? "seleccionado" : "seleccionados" }}
              </span>
              <small>{{ g.exigir ? "obligatorio · " : "" }}{{ g.max ? `máximo ${g.max}` : "libre" }}</small>
              <Icono nombre="atras" :tam="18" class="grupo__flecha" />
            </button>
            <div v-show="abierto === g.grupo" class="opciones">
              <button v-for="o in g.opciones" :key="o.id" class="opcion" :class="{ 'opcion--activa': elegida(g, o) }"
                      @click="alternar(g, o)">
                <Icono v-if="elegida(g, o)" nombre="check" :tam="16" />
                <span>{{ o.nombre }}</span>
                <small v-if="o.precio">+{{ pesos(o.precio) }}</small>
              </button>
            </div>
          </div>
        </section>

        <!-- Novedades de la categoría -->
        <section v-if="novedades.length" class="bloque">
          <h3>Novedades</h3>
          <div class="opciones">
            <button v-for="n in novedades" :key="n.id" class="opcion" :class="{ 'opcion--activa': novSel.has(n.id) }"
                    @click="novSel.has(n.id) ? novSel.delete(n.id) : novSel.add(n.id)">
              <Icono v-if="novSel.has(n.id)" nombre="check" :tam="16" />
              <span>{{ n.nombre }}</span>
            </button>
          </div>
        </section>

        <!-- Novedad libre: lo que no está en la lista (va a la comanda) -->
        <section class="bloque">
          <h3>Otra novedad <small>{{ nota.length }}/{{ MAX_NOTA }}</small></h3>
          <input v-model="nota" class="entrada" :maxlength="MAX_NOTA" placeholder="Escriba aquí si no está en la lista"
                 enterkeyhint="done" autocomplete="off" />
        </section>

        <!-- Cantidad (admite decimales: fruver, distribuidoras) -->
        <section class="bloque">
          <h3>Cantidad</h3>
          <div class="cantidad">
            <button class="paso" :disabled="cant <= 1" @click="sumar(-1)"><Icono nombre="menos" /></button>
            <input v-model="cantTxt" class="entrada cantidad__valor" inputmode="decimal" @blur="normalizar" />
            <button class="paso" @click="sumar(1)"><Icono nombre="mas" /></button>
          </div>
        </section>
      </div>

      <div class="hoja__pie">
        <p v-if="error" class="aviso">{{ error }}</p>
        <button class="btn btn--primario btn--bloque" :disabled="bloqueado" @click="agregar">
          Agregar · {{ pesos(total) }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue"
import Icono from "./Icono.vue"
import { api } from "../api"
import { cantidad, pesos, valorLinea } from "../formato"
import { showToast } from "@/utils/toast"

const props = defineProps({
  plato: { type: Object, required: true },
  novedades: { type: Array, default: () => [] },
})
const emit = defineEmits(["agregar", "cerrar"])

const presentacion = ref(props.plato.presentaciones?.[0] || null)
const precioTxt = ref("")
const descripcion = ref(props.plato.nombre)
const novSel = reactive(new Set())
const MAX_NOTA = 100
const nota = ref("")
const cantTxt = ref("1")
const grupos = ref([])
const abierto = ref(null)               // grupo desplegado del acordeón
const seleccion = reactive({})          // grupo → Set de ids
const cargandoOps = ref(false)
const errorOps = ref("")
const error = ref("")

const cant = computed(() => {
  const n = Number(String(cantTxt.value).replace(",", "."))
  return Number.isFinite(n) ? Math.round(n * 1000) / 1000 : 0
})
const adicional = computed(() => grupos.value.reduce((s, g) =>
  s + g.opciones.filter(o => seleccion[g.grupo]?.has(o.id)).reduce((a, o) => a + o.precio, 0), 0))
const unitario = computed(() => {
  let base
  if (props.plato.pedir_precio) {
    const p = Number(precioTxt.value || 0)
    base = Math.round(p + p * (props.plato.impuesto_aparte || 0) / 100)
  } else {
    base = presentacion.value ? presentacion.value.precio : props.plato.precio
  }
  return base + adicional.value
})
const total = computed(() => valorLinea(unitario.value, cant.value))
const bloqueado = computed(() => cargandoOps.value || (props.plato.armado === "menu" && !!errorOps.value))

function soloDigitos() { precioTxt.value = precioTxt.value.replace(/\D/g, "").slice(0, 9) }
function normalizar() { if (cant.value > 0) cantTxt.value = String(cant.value) }
function sumar(d) {
  const n = Math.max(1, Math.min(50, Math.round((cant.value + d) * 1000) / 1000))
  cantTxt.value = String(n)
}

const elegida = (g, o) => !!seleccion[g.grupo]?.has(o.id)
function abrir(g) {
  abierto.value = abierto.value === g.grupo ? null : g.grupo
}

function alternar(g, o) {
  const s = seleccion[g.grupo] || (seleccion[g.grupo] = new Set())
  if (s.has(o.id)) return s.delete(o.id)
  if (g.max === 1) s.clear()
  else if (g.max && s.size >= g.max) return showToast(`Máximo ${g.max} en ${g.nombre}.`, "warning", 2000)
  s.add(o.id)
}

async function cargarOpciones() {
  if (!props.plato.armado) return
  cargandoOps.value = true
  try {
    const r = await api.get(`/catalogo/plato/${props.plato.id}/opciones`)
    grupos.value = r.grupos
    abierto.value = r.grupos[0]?.grupo ?? null       // solo el primero desplegado
    for (const g of r.grupos) {
      seleccion[g.grupo] = new Set()
      for (const o of g.opciones.filter(x => x.por_defecto)) {
        if (!g.max || seleccion[g.grupo].size < g.max) seleccion[g.grupo].add(o.id)
      }
    }
  } catch (e) {
    errorOps.value = e.message
  } finally {
    cargandoOps.value = false
  }
}

function validar() {
  if (!(cant.value > 0) || cant.value > 50) return "La cantidad debe estar entre 0,001 y 50."
  if (props.plato.presentaciones && !presentacion.value) return "Escoja la presentación."
  if (props.plato.pedir_precio && !(Number(precioTxt.value) > 0)) return "Digite el precio de venta."
  if (props.plato.pedir_descripcion && !descripcion.value.trim()) return "Digite la descripción."
  for (const g of grupos.value) {
    if (g.exigir && !seleccion[g.grupo]?.size) {
      abierto.value = g.grupo                      // muestra el grupo que falta
      return `Escoja una opción de ${g.nombre}.`
    }
  }
  return ""
}

function agregar() {
  error.value = validar()
  if (error.value) return
  const opciones = [], textos = []
  for (const g of grupos.value) {
    for (const o of g.opciones.filter(x => seleccion[g.grupo]?.has(x.id))) {
      opciones.push({ grupo: g.grupo, id: o.id })
      textos.push(o.nombre)
    }
  }
  const novs = props.novedades.filter(n => novSel.has(n.id))
  const libre = nota.value.replace(/\s+/g, " ").trim().toUpperCase()
  emit("agregar", {
    clave: `${Date.now()}-${Math.random()}`,
    id_plato: props.plato.id,
    nombre: props.plato.pedir_descripcion ? descripcion.value.trim()
          : presentacion.value ? `${props.plato.nombre} - ${presentacion.value.nombre}` : props.plato.nombre,
    presentacion: presentacion.value ? presentacion.value.id : null,
    cantidad: cant.value,
    precio: props.plato.pedir_precio ? Number(precioTxt.value) : null,
    descripcion: props.plato.pedir_descripcion ? descripcion.value.trim() : null,
    novedades: novs.map(n => n.id),
    nota: libre || null,
    opciones,
    detalle: [...novs.map(n => n.nombre), ...(libre ? [libre] : []), ...textos].join(" · "),
    adicional: adicional.value,
    unitario: unitario.value,
  })
}

onMounted(cargarOpciones)
</script>

<style scoped>
.bloque { margin-bottom: 18px; }
.bloque h3 { margin: 0 0 8px; font-size: 15px; }
.bloque h3 small { font-weight: 500; color: var(--texto-suave); margin-left: 6px; font-size: 12px; }
.grupo { border: 1.5px solid var(--borde); border-radius: 12px; background: #fff; overflow: hidden; }
.grupo + .grupo { margin-top: 10px; }
.grupo--abierto { border-color: var(--azul); }
.grupo__cab { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 10px; width: 100%; min-height: 52px;
              padding: 10px 12px; border: 0; background: transparent; text-align: left; font: inherit; }
.grupo__nombre { font-weight: 700; font-size: 15px; }
.grupo__cuenta { font-size: 12px; font-weight: 700; padding: 2px 9px; border-radius: 999px; background: var(--azul-claro); color: var(--azul); }
.grupo__cuenta--falta { background: var(--ambar-claro); color: #92400e; }
.grupo__cab small { color: var(--texto-suave); font-size: 12px; }
.grupo__flecha { margin-left: auto; transform: rotate(-90deg); transition: transform .15s; color: var(--texto-suave); }
.grupo--abierto .grupo__flecha { transform: rotate(90deg); }
.grupo .opciones { padding: 0 12px 12px; }
.nota { color: var(--texto-suave); }
.aviso { margin: 0 0 10px; padding: 10px 12px; border-radius: 10px; background: var(--ambar-claro); color: #92400e; font-size: 14px; }

.presentaciones { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.pres { display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 10px 6px; border-radius: 12px; border: 2px solid var(--borde); background: #fff; }
.pres b { font-size: 14px; }
.pres span { font-weight: 700; color: var(--azul); }
.pres small { font-size: 11px; color: var(--texto-suave); }
.pres--activa { border-color: var(--azul); background: var(--azul-claro); }

.opciones { display: flex; flex-wrap: wrap; gap: 8px; }
.opcion {
  display: inline-flex; align-items: center; gap: 6px; min-height: 40px; padding: 0 12px;
  border-radius: 999px; border: 1.5px solid var(--borde); background: #fff; font-size: 14px;
}
.opcion small { color: var(--verde); font-weight: 700; }
.opcion--activa { background: var(--navy); border-color: var(--navy); color: #fff; }
.opcion--activa small { color: #bbf7d0; }

.cantidad { display: flex; align-items: center; gap: 10px; }
.paso { width: 52px; height: 52px; border-radius: 14px; border: 0; background: var(--azul-claro); color: var(--azul); display: inline-flex; align-items: center; justify-content: center; }
.paso:disabled { opacity: .4; }
.cantidad__valor { flex: 1; text-align: center; font-size: 20px; font-weight: 700; }

@media (max-width: 576px) {
  .presentaciones { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  .paso { width: 48px; height: 48px; }
}
</style>
