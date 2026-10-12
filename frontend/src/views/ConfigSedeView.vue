<template>
  <div class="cs-page">
    <div class="cs-head">
      <h2 class="cs-title"><i class="bi bi-shop me-2"></i>{{ moduleName || 'Configuración Sede' }}</h2>
      <p class="cs-sub">Datos generales de la empresa y de la sede, y la conexión con el programa de escritorio.</p>
      <p v-if="!loading && !puedeEditar" class="cs-solo-lectura">
        <i class="bi bi-lock-fill"></i> Solo el administrador de la empresa puede modificar esta configuración.
      </p>
    </div>

    <div v-if="loading" class="cs-state"><div class="spinner-border text-primary"></div></div>

    <div v-else class="cs-grid">
      <!-- ── Datos de la empresa ── -->
      <section class="cs-card">
        <h3 class="cs-card-ttl"><i class="bi bi-building"></i> Datos de la empresa</h3>
        <dl class="cs-fijos">
          <dt>Nombre</dt><dd>{{ empresa.nombre || '—' }}</dd>
          <dt>NIT</dt><dd>{{ empresa.nit || '—' }}</dd>
          <dt>Perfil</dt><dd>{{ empresa.perfil || '—' }}</dd>
          <dt>Estado</dt><dd>{{ empresa.activa ? 'Activa' : 'Inactiva' }}</dd>
        </dl>
        <small class="cs-nota">Nombre, NIT, perfil y estado los cambia el administrador del sistema.</small>
        <div class="cs-field">
          <label>Dirección</label>
          <input v-model.trim="empresa.direccion" class="cs-inp" maxlength="255" :disabled="!puedeEditar" />
        </div>
        <div class="cs-row">
          <div class="cs-field">
            <label>Teléfono</label>
            <input v-model.trim="empresa.telefono" class="cs-inp" maxlength="50" inputmode="tel" :disabled="!puedeEditar" />
          </div>
          <div class="cs-field">
            <label>Correo</label>
            <input v-model.trim="empresa.correo" class="cs-inp" maxlength="150" type="email" :disabled="!puedeEditar" />
          </div>
        </div>
        <button v-if="puedeEditar" class="cs-save" :disabled="guardando === 'empresa'" @click="guardarEmpresa">
          <span v-if="guardando === 'empresa'" class="spinner-border spinner-border-sm me-1"></span>
          <i v-else class="bi bi-check-lg me-1"></i>Guardar empresa
        </button>
      </section>

      <!-- ── Datos de la sede (documentos) ── -->
      <section class="cs-card">
        <h3 class="cs-card-ttl"><i class="bi bi-file-earmark-text"></i> Datos de la sede</h3>
        <small class="cs-nota">Salen en los recibos y facturas. Es la misma información de la configuración de la sede del escritorio.</small>
        <div class="cs-field">
          <label>Nombre del almacén *</label>
          <input v-model.trim="sede.Nombre_Almacen" class="cs-inp" maxlength="250" :disabled="!puedeEditar" />
        </div>
        <div class="cs-field">
          <label>Razón social</label>
          <input v-model.trim="sede.Razon_Social" class="cs-inp" maxlength="255" :disabled="!puedeEditar" />
        </div>
        <div class="cs-row">
          <div class="cs-field">
            <label>Nombre autorizado</label>
            <input v-model.trim="sede.Nombre_Autorizado" class="cs-inp" maxlength="250" :disabled="!puedeEditar" />
          </div>
          <div class="cs-field">
            <label>NIT autorizado</label>
            <input v-model.trim="sede.Nit_Autorizado" class="cs-inp" maxlength="250" :disabled="!puedeEditar" />
          </div>
        </div>
        <div class="cs-field">
          <label>Dirección de la sede</label>
          <input v-model.trim="sede.Direccion_Sede" class="cs-inp" maxlength="255" :disabled="!puedeEditar" />
        </div>
        <div class="cs-row">
          <div class="cs-field">
            <label>Correo 1</label>
            <input v-model.trim="sede.Mail_Uno" class="cs-inp" maxlength="100" type="email" :disabled="!puedeEditar" />
          </div>
          <div class="cs-field">
            <label>Correo 2</label>
            <input v-model.trim="sede.Mail_Dos" class="cs-inp" maxlength="100" type="email" :disabled="!puedeEditar" />
          </div>
        </div>
        <div class="cs-field">
          <label>Nombre del archivo del logo</label>
          <input v-model.trim="sede.Nombre_Logo_Empresa" class="cs-inp" maxlength="200" placeholder="logo.jpg" :disabled="!puedeEditar" />
        </div>
        <small v-if="sede.actualizado_por" class="cs-nota">Último cambio: {{ sede.actualizado_por || '—' }} · {{ fechaHora(sede.actualizado_en) }}</small>
        <button v-if="puedeEditar" class="cs-save" :disabled="guardando === 'sede'" @click="guardarSede">
          <span v-if="guardando === 'sede'" class="spinner-border spinner-border-sm me-1"></span>
          <i v-else class="bi bi-check-lg me-1"></i>Guardar sede
        </button>
      </section>

      <!-- ── Escritorio (Agente Local): solo empresas con agente ── -->
      <section v-if="esc?.agente" class="cs-card">
        <h3 class="cs-card-ttl"><i class="bi bi-pc-display"></i> Escritorio (Agente Local)</h3>
        <div class="cs-agente">
          <span class="cs-punto" :class="esc.agente.en_linea ? 'cs-punto--ok' : 'cs-punto--off'"></span>
          <div>
            <b>{{ esc.tiene_agente ? (esc.agente.en_linea ? 'En línea' : 'Sin conexión') : 'Agente desactivado' }}</b>
            <small>Código {{ esc.agente.codigo }} · versión {{ esc.agente.version || '—' }} · último contacto {{ fechaHora(esc.agente.ultimo_contacto) || '—' }}</small>
          </div>
        </div>
        <template v-if="esc.tiene_agente">
          <label class="cs-switch">
            <input type="checkbox" v-model="esc.pedidos_web_escritorio" :disabled="!puedeEditar" />
            <span>Enviar los pedidos web al escritorio para aceptarlos en caja</span>
          </label>
          <p v-if="esc.pedidos_web_escritorio" class="cs-help">
            Lo que se envíe desde la toma de pedido web queda "Pendiente x Aceptar" hasta que la caja del escritorio
            lo acepte; después se imprime y se cobra en el escritorio.
          </p>
          <p v-else class="cs-help cs-help--aviso">
            <i class="bi bi-exclamation-triangle-fill"></i>
            Los pedidos web no bajarán al escritorio: se cobran con el recibo de la web y se imprimen con la impresión
            de la web. Los pedidos que ya tienen algo enviado a la caja siguen bajando.
          </p>
          <small v-if="esc.cambiado_en" class="cs-nota">Último cambio: {{ esc.cambiado_por || '—' }} · {{ fechaHora(esc.cambiado_en) }}</small>
          <button v-if="puedeEditar" class="cs-save" :disabled="guardando === 'escritorio' || esc.pedidos_web_escritorio === escOriginal"
                  @click="guardarEscritorio">
            <span v-if="guardando === 'escritorio'" class="spinner-border spinner-border-sm me-1"></span>
            <i v-else class="bi bi-check-lg me-1"></i>Guardar escritorio
          </button>
        </template>
      </section>

      <!-- ── Inventario: cargue unitario (un producto por código / IMEI) ── -->
      <section class="cs-card">
        <h3 class="cs-card-ttl"><i class="bi bi-upc-scan"></i> Inventario</h3>
        <label class="cs-switch">
          <input type="checkbox" v-model="unitario" :disabled="!puedeEditar" />
          <span>Cargue unitario: un producto por cada código o IMEI</span>
        </label>
        <p class="cs-help">
          Para artículos que se venden por unidad identificada (por ejemplo celulares con IMEI): cada unidad se registra
          como un producto propio que entra al inventario con cantidad 1, exige proveedor, se puede replicar digitando
          un código por unidad y se desactiva al venderse para no volver a venderla.
        </p>
        <button v-if="puedeEditar" class="cs-save" :disabled="guardando === 'unitario' || unitario === unitarioOriginal"
                @click="guardarUnitario">
          <span v-if="guardando === 'unitario'" class="spinner-border spinner-border-sm me-1"></span>
          <i v-else class="bi bi-check-lg me-1"></i>Guardar inventario
        </button>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/apis'
import { showToast } from '@/utils/toast'
import { useModuleName } from '@/composables/useModuleName'

const { moduleName } = useModuleName()
const loading     = ref(true)
const guardando   = ref('')
const puedeEditar = ref(false)
const empresa     = ref({})
const sede        = ref({})
const esc         = ref(null)
const escOriginal = ref(null)
const unitario    = ref(false)
const unitarioOriginal = ref(false)

const fechaHora = (v) => (v ? new Date(v).toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' }) : '')
const errorDe = (e, porDefecto) => {
  const d = e?.response?.data?.detail
  return Array.isArray(d) ? 'Revise los valores ingresados' : (d || porDefecto)
}

async function cargar() {
  loading.value = true
  try {
    const { data } = await api.get('/api/config-sede')
    empresa.value = data.empresa
    sede.value = data.sede
    esc.value = data.escritorio
    escOriginal.value = data.escritorio?.pedidos_web_escritorio ?? null
    unitario.value = unitarioOriginal.value = !!data.sede?.cargar_1_inventario_automatico
    puedeEditar.value = !!data.puede_editar
  } catch (e) {
    showToast(errorDe(e, 'Error cargando la configuración de la sede'), 'error')
  }
  loading.value = false
}

async function guardarEmpresa() {
  guardando.value = 'empresa'
  try {
    const { data } = await api.put('/api/config-sede/empresa', {
      direccion: empresa.value.direccion, telefono: empresa.value.telefono, correo: empresa.value.correo,
    })
    empresa.value = data.empresa
    showToast('Datos de la empresa guardados', 'success')
  } catch (e) { showToast(errorDe(e, 'Error al guardar'), 'error') }
  guardando.value = ''
}

async function guardarSede() {
  guardando.value = 'sede'
  try {
    const { actualizado_por, actualizado_en, Id_Sede, cargar_1_inventario_automatico, ...campos } = sede.value
    const { data } = await api.put('/api/config-sede/sede', campos)
    sede.value = data.sede
    showToast('Datos de la sede guardados', 'success')
  } catch (e) { showToast(errorDe(e, 'Error al guardar'), 'error') }
  guardando.value = ''
}

async function guardarEscritorio() {
  guardando.value = 'escritorio'
  try {
    const { data } = await api.put('/api/config-sede/escritorio', { pedidos_web_escritorio: esc.value.pedidos_web_escritorio })
    esc.value = data.escritorio
    escOriginal.value = data.escritorio.pedidos_web_escritorio
    showToast('Configuración del escritorio guardada', 'success')
  } catch (e) { showToast(errorDe(e, 'Error al guardar'), 'error') }
  guardando.value = ''
}

async function guardarUnitario() {
  guardando.value = 'unitario'
  try {
    const { data } = await api.put('/api/config-sede/cargue-unitario', { cargar_1_inventario_automatico: unitario.value })
    sede.value = data.sede
    unitario.value = unitarioOriginal.value = !!data.sede.cargar_1_inventario_automatico
    showToast('Configuración de inventario guardada', 'success')
  } catch (e) { showToast(errorDe(e, 'Error al guardar'), 'error') }
  guardando.value = ''
}

onMounted(cargar)
</script>

<style scoped>
.cs-page { padding: 20px 24px 32px; }
.cs-head { margin-bottom: 16px; }
.cs-title { font-size: 22px; font-weight: 800; color: #1e293b; margin: 0; }
.cs-sub { font-size: 13px; color: #64748b; margin: 2px 0 0; }
.cs-solo-lectura { margin: 10px 0 0; font-size: 13px; color: #92400e; background: #fffbeb; border: 1px solid #fde68a;
  border-radius: 8px; padding: 8px 10px; display: inline-flex; gap: 6px; align-items: center; }
.cs-state { display: flex; justify-content: center; padding: 60px; }
.cs-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 14px; align-items: start; }
.cs-card { background: #fff; border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,.08); padding: 16px; display: flex; flex-direction: column; gap: 10px; }
.cs-card-ttl { font-size: 14px; font-weight: 800; color: #1e3a5f; margin: 0 0 2px; display: flex; align-items: center; gap: 8px; }
.cs-fijos { display: grid; grid-template-columns: auto 1fr; gap: 4px 12px; margin: 0; font-size: 13.5px; }
.cs-fijos dt { color: #64748b; font-weight: 700; }
.cs-fijos dd { margin: 0; color: #1e293b; word-break: break-word; }
.cs-nota { font-size: 11.5px; color: #94a3b8; }
.cs-field { display: flex; flex-direction: column; gap: 4px; flex: 1; min-width: 0; }
.cs-field label { font-size: 12px; font-weight: 700; color: #475569; }
.cs-row { display: flex; gap: 10px; }
.cs-inp { border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 8px 10px; font-size: 14px; color: #1e293b; background: #fff; width: 100%; }
.cs-inp:focus { outline: none; border-color: #1d4ed8; }
.cs-inp:disabled { background: #f8fafc; color: #64748b; }
.cs-switch { display: flex; align-items: center; gap: 10px; font-size: 14px; color: #334155; cursor: pointer; }
.cs-switch input { width: 18px; height: 18px; accent-color: #1d4ed8; flex-shrink: 0; }
.cs-help { font-size: 12.5px; color: #475569; margin: 0; line-height: 1.45; }
.cs-help--aviso { color: #92400e; background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 8px 10px; }
.cs-agente { display: flex; align-items: center; gap: 10px; background: #f8fafc; border-radius: 10px; padding: 10px; }
.cs-agente div { display: flex; flex-direction: column; min-width: 0; }
.cs-agente small { color: #64748b; font-size: 12px; word-break: break-word; }
.cs-punto { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
.cs-punto--ok { background: #16a34a; box-shadow: 0 0 0 3px rgba(22,163,74,.2); }
.cs-punto--off { background: #94a3b8; }
.cs-save { align-self: flex-end; display: inline-flex; align-items: center; background: linear-gradient(90deg,#1e3a5f,#1d4ed8); color: #fff;
  border: none; border-radius: 10px; padding: 9px 18px; font-weight: 700; font-size: 14px; cursor: pointer; white-space: nowrap; }
.cs-save:disabled { opacity: .55; cursor: not-allowed; }

@media (max-width: 1024px) {
  .cs-grid { grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); }
}
@media (max-width: 768px) {
  .cs-page { padding: 14px 12px 80px; }
  .cs-grid { grid-template-columns: 1fr; }
  .cs-save { align-self: stretch; justify-content: center; }
}
@media (max-width: 576px) {
  .cs-title { font-size: 18px; }
  .cs-row { flex-direction: column; gap: 10px; }
  .cs-card { padding: 12px; }
  .cs-switch { font-size: 13px; }
}
</style>
