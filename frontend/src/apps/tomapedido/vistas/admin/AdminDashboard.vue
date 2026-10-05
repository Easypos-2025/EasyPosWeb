<template>
  <div>
    <div class="cab">
      <h2>Dashboard</h2>
      <button class="btn btn--chico" @click="recargar"><Icono nombre="refrescar" :tam="16" /> Actualizar</button>
    </div>

    <div v-if="!r" class="cargando"><span class="giro"></span></div>
    <template v-else>
      <div class="kpis">
        <router-link to="/admin/errores" class="kpi tarjeta" :class="{ 'kpi--alerta': r.errores.sin_resolver }">
          <span class="kpi__ico kpi__ico--rojo"><Icono nombre="alerta" /></span>
          <b>{{ r.errores.sin_resolver }}</b>
          <span>Errores sin resolver</span>
          <small>{{ r.errores.criticos }} críticos · {{ r.errores.errores }} errores · {{ r.errores.advertencias }} avisos</small>
        </router-link>
        <router-link to="/admin/errores" class="kpi tarjeta">
          <span class="kpi__ico kpi__ico--ambar"><Icono nombre="wifi" /></span>
          <b>{{ r.errores.conexion }}</b>
          <span>Problemas de conexión</span>
          <small>{{ r.errores.nuevos_24h }} errores nuevos en 24 h · {{ r.errores.regresiones }} repetidos</small>
        </router-link>
        <router-link to="/admin/dispositivos" class="kpi tarjeta" :class="{ 'kpi--alerta': sinConexion }">
          <span class="kpi__ico kpi__ico--azul"><Icono nombre="celular" /></span>
          <b>{{ r.dispositivos.conectados }} / {{ r.dispositivos.total - r.dispositivos.bloqueados }}</b>
          <span>Dispositivos conectados</span>
          <small>{{ sinConexion ? `${sinConexion} sin conexión` : "Todos conectados" }}{{ r.dispositivos.bloqueados ? ` · ${r.dispositivos.bloqueados} bloqueados` : "" }}</small>
        </router-link>
        <div class="kpi tarjeta">
          <span class="kpi__ico kpi__ico--verde"><Icono nombre="lista" /></span>
          <b>{{ r.pedidos_abiertos }}</b>
          <span>Pedidos abiertos desde dispositivos</span>
          <small>Pendientes de facturar en caja</small>
        </div>
      </div>

      <div class="fila">
        <div class="tarjeta panel">
          <h3><Icono nombre="nube" :tam="18" /> Conexión con la nube</h3>
          <p :class="nubeOk ? 'ok' : 'mal'">{{ r.nube.mensaje || "Sin información todavía." }}</p>
          <dl>
            <dt>Empresa en la nube</dt><dd>{{ r.nube.empresa || "—" }}</dd>
            <dt>Último contacto</dt><dd>{{ fecha(r.nube.ultimo_ok) }}</dd>
            <dt>Versión del agente</dt><dd>{{ r.version }}</dd>
            <template v-if="r.actualizacion?.ultimo">
              <dt>Última actualización</dt>
              <dd :class="r.actualizacion.ultimo.estado === 'OK' ? 'ok' : 'mal'">
                {{ r.actualizacion.ultimo.estado === "OK" ? "Correcta" : "Falló (volvió a la anterior)" }}
                · {{ r.actualizacion.ultimo.desde }} → {{ r.actualizacion.ultimo.hacia }}
              </dd>
            </template>
          </dl>
        </div>
        <div class="tarjeta panel qr">
          <h3><Icono nombre="celular" :tam="18" /> Toma de pedidos en los dispositivos</h3>
          <p>Escanee el código con el celular (conectado al wifi del negocio) o escriba la dirección en el navegador:</p>
          <img v-if="qr" :src="qr" alt="Código QR de la toma de pedidos" />
          <code>{{ r.direccion }}</code>
          <small>En el celular: menú del navegador → "Agregar a pantalla de inicio" para dejar el ícono.</small>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, inject, onBeforeUnmount, onMounted, ref } from "vue"
import Icono from "../../componentes/Icono.vue"
import { api } from "../../api"

const r = inject("resumen")
const recargar = inject("recargarResumen")
const qr = ref("")

const sinConexion = computed(() => {
  const d = r.value?.dispositivos || {}
  return Math.max(0, (d.total || 0) - (d.conectados || 0) - (d.bloqueados || 0))
})
const nubeOk = computed(() => !!r.value?.nube?.ultimo_ok &&
  (!r.value.nube.ultimo_error || new Date(r.value.nube.ultimo_ok) >= new Date(r.value.nube.ultimo_error)))

const fecha = (v) => (v ? new Date(v).toLocaleString("es-CO", { dateStyle: "short", timeStyle: "short" }) : "—")

onMounted(async () => {
  try { qr.value = URL.createObjectURL(await api.admin.imagen("/qr.png")) } catch { /* sin QR */ }
})
onBeforeUnmount(() => qr.value && URL.revokeObjectURL(qr.value))
</script>

<style scoped>
.cab { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.cab h2 { margin: 0; font-size: 20px; }
.kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 14px; }
.kpi { display: flex; flex-direction: column; gap: 2px; padding: 16px; color: var(--texto); text-decoration: none; }
.kpi b { font-size: 28px; line-height: 1.1; margin-top: 6px; }
.kpi > span:not(.kpi__ico) { font-weight: 600; }
.kpi small { color: var(--texto-suave); }
.kpi--alerta { box-shadow: 0 0 0 2px var(--rojo), var(--sombra); }
.kpi__ico { width: 40px; height: 40px; border-radius: 12px; display: inline-flex; align-items: center; justify-content: center; }
.kpi__ico--rojo { background: var(--rojo-claro); color: var(--rojo); }
.kpi__ico--ambar { background: var(--ambar-claro); color: #b45309; }
.kpi__ico--azul { background: var(--azul-claro); color: var(--azul); }
.kpi__ico--verde { background: var(--verde-claro); color: var(--verde); }
.fila { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.panel { padding: 16px; }
.panel h3 { display: flex; align-items: center; gap: 8px; margin: 0 0 10px; font-size: 16px; }
.panel p { margin: 0 0 10px; }
.ok { color: var(--verde); font-weight: 600; }
.mal { color: #b45309; font-weight: 600; }
dl { display: grid; grid-template-columns: auto 1fr; gap: 6px 14px; margin: 0; font-size: 14px; }
dt { color: var(--texto-suave); }
dd { margin: 0; font-weight: 600; }
.qr { text-align: center; }
.qr p { font-size: 14px; color: var(--texto-suave); }
.qr img { width: 180px; height: 180px; image-rendering: pixelated; }
.qr code { display: block; margin: 8px 0; font-size: 18px; font-weight: 700; color: var(--navy); }
.qr small { color: var(--texto-suave); }

@media (max-width: 1200px) {
  .kpis { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  .fila { grid-template-columns: 1fr; }
}
@media (max-width: 576px) {
  .kpis { grid-template-columns: 1fr; }
  .kpi b { font-size: 24px; }
}
</style>
