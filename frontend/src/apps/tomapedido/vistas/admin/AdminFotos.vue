<template>
  <div>
    <div class="cab"><h2>Fotos de la web</h2></div>
    <div class="tarjeta panel">
      <p>Copia al programa de escritorio las fotos de los productos que se subieron en EasyPosWeb. Se guardan en la
        carpeta de fotos de productos configurada en el escritorio (convertidas a JPG).</p>
      <p><b>La web manda:</b> si un producto tiene foto en EasyPosWeb, esa reemplaza la del escritorio. Si prefiere
        conservar las fotos del escritorio, no suba fotos de esos productos en la web.</p>
      <p class="sub">Se hace automáticamente una vez al día; con este botón se hace ahora.</p>
      <button class="btn btn--primario" :disabled="trabajando || !r?.nube?.configurada" @click="sincronizar">
        <span v-if="trabajando" class="giro" style="width:20px;height:20px;border-width:2px"></span>
        <template v-else><Icono nombre="foto" /> Traer fotos ahora</template>
      </button>
      <p v-if="r && !r.nube.configurada" class="aviso">El agente no tiene clave de la nube: se configura en el instalador.</p>

      <div v-if="resultado" class="res">
        <h3>Última sincronización · {{ fecha(resultado.fecha) }}</h3>
        <p v-if="resultado.error" class="aviso">{{ resultado.error }}</p>
        <ul v-else>
          <li><b>{{ resultado.descargadas }}</b> fotos descargadas</li>
          <li><b>{{ resultado.asignadas }}</b> asignadas a productos del escritorio</li>
          <li><b>{{ resultado.sin_cambios }}</b> sin cambios</li>
          <li v-if="resultado.fallidas"><b>{{ resultado.fallidas }}</b> no se pudieron descargar</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, inject, ref } from "vue"
import Icono from "../../componentes/Icono.vue"
import { api } from "../../api"
import { showToast } from "@/utils/toast"

const r = inject("resumen")
const recargarResumen = inject("recargarResumen")
const trabajando = ref(false)
const ultimo = ref(null)
const resultado = computed(() => ultimo.value || r.value?.nube?.fotos || null)
const fecha = (v) => (v ? new Date(v).toLocaleString("es-CO", { dateStyle: "short", timeStyle: "short" }) : "—")

async function sincronizar() {
  trabajando.value = true
  try {
    ultimo.value = await api.admin.post("/fotos/sincronizar")
    showToast("Fotos sincronizadas", "success", 1800)
    recargarResumen()
  } catch (e) { showToast(e.message, "error", 4000) }
  finally { trabajando.value = false }
}
</script>

<style scoped>
.cab h2 { margin: 0 0 12px; font-size: 20px; }
.panel { padding: 18px; max-width: 760px; }
.sub { color: var(--texto-suave); font-size: 14px; }
.aviso { margin-top: 12px; padding: 10px 12px; border-radius: 10px; background: var(--ambar-claro); color: #92400e; font-size: 14px; }
.res { margin-top: 18px; padding-top: 14px; border-top: 1px solid var(--borde); }
.res h3 { font-size: 15px; margin: 0 0 8px; }
.res ul { margin: 0; padding-left: 20px; }

@media (max-width: 576px) {
  .panel { padding: 14px; }
  .panel .btn { width: 100%; }
}
@media (max-width: 768px) {
  .panel { max-width: none; }
}
</style>
