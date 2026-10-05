<template>
  <!-- Solo si la empresa tiene agente local: QR para abrir la toma de pedidos de la red del negocio -->
  <div v-if="agente?.existe" class="alw" :class="{ 'alw--abierto': abierto }">
    <button class="alw-cab" @click="alternar">
      <i class="bi bi-qr-code"></i>
      <span class="alw-tit">Toma de pedidos en la red local</span>
      <span class="alw-estado" :class="agente.en_linea ? 'ok' : 'off'">{{ agente.en_linea ? "Agente en línea" : "Agente sin contacto" }}</span>
      <i class="bi" :class="abierto ? 'bi-chevron-up' : 'bi-chevron-down'"></i>
    </button>
    <div v-if="abierto" class="alw-cuerpo">
      <img v-if="qr" :src="qr" alt="Código QR de la toma de pedidos" class="alw-qr" />
      <div class="alw-info">
        <p v-if="agente.url_local">Escanee el código con el celular <b>conectado al wifi del negocio</b>, o escriba
          en el navegador:</p>
        <p v-else>El agente aún no ha reportado su dirección en la red local.</p>
        <code v-if="agente.url_local">{{ agente.url_local }}</code>
        <small>Funciona solo dentro de la red del negocio. En el celular: menú del navegador → "Agregar a pantalla de
          inicio" para dejar el ícono.</small>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue"
import api from "@/services/apis"

const agente = ref(null)
const qr = ref("")
const CLAVE = "dash_agente_abierto"
// Plegada por defecto; el navegador recuerda la elección
const abierto = ref((() => { try { return localStorage.getItem(CLAVE) === "1" } catch { return false } })())

async function cargarQr() {
  if (qr.value || !agente.value?.url_local) return
  try {
    const { data } = await api.get("/api/mi-agente-local/qr.png", { responseType: "blob" })
    qr.value = URL.createObjectURL(data)
  } catch { /* sin QR */ }
}

function alternar() {
  abierto.value = !abierto.value
  try { localStorage.setItem(CLAVE, abierto.value ? "1" : "0") } catch { /* sin almacenamiento */ }
  if (abierto.value) cargarQr()
}

onMounted(async () => {
  try { agente.value = (await api.get("/api/mi-agente-local")).data } catch { agente.value = null }
  if (abierto.value) cargarQr()
})
onBeforeUnmount(() => qr.value && URL.revokeObjectURL(qr.value))
</script>

<style scoped>
.alw { background: #fff; border-radius: 14px; box-shadow: 0 1px 3px rgba(15,23,42,.08), 0 4px 12px rgba(15,23,42,.06); margin: 0 0 14px; overflow: hidden; }
.alw-cab { display: flex; align-items: center; gap: 10px; width: 100%; padding: 12px 16px; border: 0; background: transparent; text-align: left; font-weight: 600; }
.alw-cab > .bi:first-child { font-size: 20px; color: #1e3a5f; }
.alw-tit { flex: 1; }
.alw-estado { font-size: 12px; font-weight: 700; padding: 3px 10px; border-radius: 999px; }
.alw-estado.ok { background: #dcfce7; color: #166534; }
.alw-estado.off { background: #fef3c7; color: #92400e; }
.alw-cuerpo { display: flex; align-items: center; gap: 18px; padding: 0 16px 16px; }
.alw-qr { width: 150px; height: 150px; flex-shrink: 0; image-rendering: pixelated; }
.alw-info p { margin: 0 0 6px; font-size: 14px; color: #475569; }
.alw-info code { display: block; font-size: 18px; font-weight: 700; color: #1e3a5f; margin-bottom: 6px; word-break: break-all; }
.alw-info small { color: #64748b; }

@media (max-width: 768px) {
  .alw-cuerpo { flex-direction: column; text-align: center; }
}
@media (max-width: 576px) {
  .alw-cab { padding: 10px 12px; }
  .alw-tit { font-size: 14px; }
  .alw-qr { width: 140px; height: 140px; }
}
</style>
