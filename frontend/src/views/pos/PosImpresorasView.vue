<template>
  <div class="crud-view">
    <div class="crud-header">
      <div>
        <h5 class="crud-titulo">Impresoras</h5>
        <p class="crud-sub">Configura las impresoras por tipo de conexión: USB, Red o Bluetooth</p>
      </div>
      <button class="btn-nuevo" @click="abrirModal()">
        <i class="bi bi-plus-lg me-1"></i>Nueva Impresora
      </button>
    </div>

    <div v-if="loading" class="estado-carga"><div class="spinner-border spinner-border-sm text-primary"></div></div>
    <div v-else-if="!items.length" class="estado-vacio">
      <i class="bi bi-printer"></i>
      <p>No hay impresoras configuradas.</p>
    </div>
    <div v-else class="printers-grid">
      <div v-for="imp in items" :key="imp.id" class="printer-card" :class="{ 'printer-card--off': !imp.is_active }">
        <div class="printer-icon" :class="`printer-icon--${imp.connection_type}`">
          <i class="bi" :class="iconForType(imp.connection_type)"></i>
        </div>
        <div class="printer-info">
          <span class="printer-nombre">{{ imp.name }}</span>
          <span class="printer-tipo">{{ labelForType(imp.connection_type) }}</span>
          <span v-if="imp.ip" class="printer-detail">{{ imp.ip }}</span>
          <span v-else-if="imp.bluetooth_address" class="printer-detail">{{ imp.bluetooth_address }}</span>
          <span v-else-if="imp.usb_device_id" class="printer-detail">{{ imp.usb_device_id }}</span>
        </div>
        <div class="printer-badge-wrap">
          <span :class="imp.is_active ? 'badge-on' : 'badge-off'">{{ imp.is_active ? 'Activa' : 'Inactiva' }}</span>
        </div>
        <div class="printer-acciones">
          <button class="btn-icono" @click="abrirModal(imp)"><i class="bi bi-pencil"></i></button>
          <button class="btn-icono btn-icono--danger" @click="eliminar(imp)"><i class="bi bi-trash"></i></button>
        </div>
      </div>
    </div>

    <!-- ── MODAL ───────────────────────────────────────────────────────────── -->
    <div v-if="modal.visible" class="modal-overlay" @click.self="cerrarModal">
      <div class="modal-card">
        <div class="modal-hdr">
          <span><i class="bi bi-printer me-2"></i>{{ modal.id ? 'Editar' : 'Nueva' }} Impresora</span>
          <button class="btn-x" @click="cerrarModal"><i class="bi bi-x-lg"></i></button>
        </div>

        <div class="modal-body">

          <!-- Selector tipo conexión -->
          <div class="campo">
            <label>Tipo de conexión *</label>
            <div class="tipo-btns">
              <button v-for="t in tipos" :key="t.value"
                :class="['tipo-btn', { 'tipo-btn--sel': modal.connection_type === t.value }]"
                @click="cambiarTipo(t.value)">
                <i :class="`bi ${t.icon}`"></i>
                <span>{{ t.label }}</span>
              </button>
            </div>
          </div>

          <!-- Nombre -->
          <div class="campo">
            <label>Nombre de la impresora *</label>
            <input v-model="modal.name" class="inp" :placeholder="placeholderNombre" />
          </div>

          <!-- ── USB ─────────────────────────────────────────────────────── -->
          <template v-if="modal.connection_type === 'usb'">
            <div class="detector-box">
              <p class="detector-hint"><i class="bi bi-info-circle me-1"></i>Conecta la impresora USB y haz clic en detectar. Requiere Chrome o Edge.</p>
              <button class="btn-detect" :disabled="detectandoUSB" @click="detectarUSB">
                <span v-if="detectandoUSB"><span class="spinner-border spinner-border-sm me-1"></span>Buscando…</span>
                <span v-else><i class="bi bi-usb-symbol me-1"></i>Detectar impresoras USB</span>
              </button>
              <div v-if="modal.usb_device_id" class="device-found">
                <i class="bi bi-check-circle-fill text-success me-1"></i>Dispositivo: <strong>{{ modal.usb_device_id }}</strong>
              </div>
              <div v-if="errorUSB" class="device-error"><i class="bi bi-exclamation-triangle me-1"></i>{{ errorUSB }}</div>
            </div>
          </template>

          <!-- ── RED ─────────────────────────────────────────────────────── -->
          <template v-if="modal.connection_type === 'network'">
            <div class="detector-box">
              <p class="detector-hint"><i class="bi bi-info-circle me-1"></i>Busca impresoras visibles en tu red (WiFi o cable) o ingresa la IP manualmente.</p>
              <div class="scan-row">
                <div class="subred-wrap">
                  <span class="subred-label">Subred:</span>
                  <input v-model="subred" class="inp inp-subred" placeholder="192.168.1" />
                  <span class="subred-label">.1–254</span>
                </div>
                <button class="btn-detect" :disabled="escaneando" @click="escanearRed">
                  <span v-if="escaneando"><span class="spinner-border spinner-border-sm me-1"></span>{{ scanProgress }}/{{ scanTotal }}…</span>
                  <span v-else><i class="bi bi-radar me-1"></i>Escanear</span>
                </button>
              </div>
              <div v-if="encontradas.length" class="found-list">
                <p class="found-title">{{ encontradas.length }} impresora(s) encontrada(s):</p>
                <button v-for="ip in encontradas" :key="ip"
                  :class="['found-item', { 'found-item--sel': modal.ip === ip }]"
                  @click="modal.ip = ip; modal.name = modal.name || `Impresora ${ip}`">
                  <i class="bi bi-printer-fill me-1"></i>{{ ip }}
                  <span v-if="modal.ip === ip" class="ms-auto"><i class="bi bi-check-lg"></i></span>
                </button>
              </div>
              <div v-else-if="escaneoHecho && !escaneando" class="device-error">No se encontraron impresoras. Intenta con otra subred o ingresa IP manualmente.</div>
              <div class="campo" style="margin-top:8px">
                <label>IP manual</label>
                <div class="ip-test-row">
                  <input v-model="modal.ip" class="inp" placeholder="192.168.1.100" />
                  <button class="btn-test" :disabled="!modal.ip || probando" @click="probarIP">
                    <span v-if="probando"><span class="spinner-border spinner-border-sm"></span></span>
                    <span v-else>Probar</span>
                  </button>
                </div>
                <span v-if="estadoIP==='online'" class="ip-status ip-online"><i class="bi bi-circle-fill me-1"></i>En línea</span>
                <span v-else-if="estadoIP==='offline'" class="ip-status ip-offline"><i class="bi bi-circle-fill me-1"></i>No responde</span>
              </div>
            </div>
          </template>

          <!-- ── BLUETOOTH ───────────────────────────────────────────────── -->
          <template v-if="modal.connection_type === 'bluetooth'">
            <div class="detector-box">
              <p class="detector-hint"><i class="bi bi-info-circle me-1"></i>Enciende la impresora BT en modo pairing. Requiere Chrome o Edge con HTTPS.</p>
              <button class="btn-detect btn-detect--bt" :disabled="detectandoBT" @click="detectarBluetooth">
                <span v-if="detectandoBT"><span class="spinner-border spinner-border-sm me-1"></span>Buscando…</span>
                <span v-else><i class="bi bi-bluetooth me-1"></i>Buscar impresora Bluetooth</span>
              </button>
              <div v-if="modal.bluetooth_address" class="device-found">
                <i class="bi bi-check-circle-fill text-success me-1"></i>Vinculado: <strong>{{ modal.name }}</strong>
                <small class="d-block text-muted">ID: {{ modal.bluetooth_address }}</small>
              </div>
              <div v-if="errorBT" class="device-error"><i class="bi bi-exclamation-triangle me-1"></i>{{ errorBT }}</div>
            </div>
          </template>

          <!-- ── TEST DE CONEXIÓN (universal, visible cuando hay datos) ─── -->
          <div v-if="puedeGuardar" class="test-box">
            <div class="test-row">
              <span class="test-label"><i class="bi bi-activity me-1"></i>Probar conexión</span>
              <button class="btn-test-conn" :disabled="testando" @click="testConexion">
                <span v-if="testando"><span class="spinner-border spinner-border-sm me-1"></span>Probando…</span>
                <span v-else><i class="bi bi-send me-1"></i>Probar ahora</span>
              </button>
            </div>
            <!-- Resultado del test -->
            <div v-if="testEstado==='online'" class="test-result test-ok">
              <i class="bi bi-check-circle-fill me-1"></i>{{ testMensaje }}
            </div>
            <div v-else-if="testEstado==='classic'" class="test-result test-warn">
              <i class="bi bi-bluetooth me-1"></i>{{ testMensaje }}
            </div>
            <div v-else-if="testEstado==='offline'" class="test-result test-fail">
              <i class="bi bi-x-circle-fill me-1"></i>{{ testMensaje }}
            </div>
            <!-- Imprimir prueba (solo BLE confirmado) -->
            <button v-if="testEstado==='online' && puedeImprimir" class="btn-print-test" :disabled="imprimiendo" @click="imprimirPrueba">
              <span v-if="imprimiendo"><span class="spinner-border spinner-border-sm me-1"></span>Imprimiendo…</span>
              <span v-else><i class="bi bi-printer-fill me-1"></i>Imprimir página de prueba</span>
            </button>
          </div>

          <div class="campo-check">
            <input type="checkbox" v-model="modal.is_active" :true-value="1" :false-value="0" id="chkA" />
            <label for="chkA">Activa</label>
          </div>
        </div>

        <div class="modal-ftr">
          <button class="btn-cancel" @click="cerrarModal">Cancelar</button>
          <button class="btn-save" :disabled="guardando || !modal.name || !puedeGuardar" @click="guardar">
            <span v-if="guardando"><span class="spinner-border spinner-border-sm me-1"></span></span>
            <i v-else class="bi bi-check-lg me-1"></i>Guardar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/apis.js'
import { showToast } from '@/utils/toast.js'

const BASE = '/api/pos-catalogo/impresoras'

const tipos = [
  { value: 'usb',       label: 'USB',      icon: 'bi-usb-symbol' },
  { value: 'network',   label: 'Red',       icon: 'bi-wifi' },
  { value: 'bluetooth', label: 'Bluetooth', icon: 'bi-bluetooth' },
]
const iconForType  = t => ({ usb:'bi-usb-symbol', network:'bi-wifi', bluetooth:'bi-bluetooth' }[t] || 'bi-printer')
const labelForType = t => ({ usb:'USB', network:'Red', bluetooth:'Bluetooth' }[t] || t)
const placeholderNombre = computed(() => ({
  usb: 'Ej: Tiquetera USB Cocina', network: 'Ej: Tiquetera Red Barra', bluetooth: 'Ej: Tiquetera BT Mesa',
}[modal.value.connection_type] || 'Nombre de la impresora'))

// ── Estado ────────────────────────────────────────────────────────────────────
const items    = ref([])
const loading  = ref(true)
const guardando= ref(false)
const modal    = ref({ visible:false, id:null, name:'', connection_type:'network', ip:'', bluetooth_address:'', usb_device_id:'', is_active:1 })

// USB
const detectandoUSB = ref(false)
const errorUSB      = ref('')
// Red
const subred       = ref('')
const escaneando   = ref(false)
const escaneoHecho = ref(false)
const encontradas  = ref([])
const scanProgress = ref(0)
const scanTotal    = ref(0)
const probando     = ref(false)
const estadoIP     = ref('')
// Bluetooth
const detectandoBT = ref(false)
const errorBT      = ref('')
// Test universal
const testando    = ref(false)
const testEstado  = ref('')   // '' | 'online' | 'offline' | 'classic'
const testMensaje = ref('')
const puedeImprimir = ref(false)
const btGattDevice  = ref(null)
const imprimiendo   = ref(false)

// UUIDs conocidos de impresoras térmicas BLE
const BLE_SERVICES = [
  { svc: 'e7810a71-73ae-499d-8c15-faa9aef0c3f2', chr: 'bef8d6c9-9c21-4c9e-b632-bd58c1009f9f' },
  { svc: '49535343-fe7d-4ae5-8fa9-9fafd205e455', chr: '49535343-8841-43f4-a8d4-ecbe34729bb3' },
  { svc: '000018f0-0000-1000-8000-00805f9b34fb', chr: '00002af1-0000-1000-8000-00805f9b34fb' },
]

const puedeGuardar = computed(() => {
  const t = modal.value.connection_type
  if (t === 'network')   return !!modal.value.ip
  if (t === 'bluetooth') return !!modal.value.bluetooth_address
  if (t === 'usb')       return !!modal.value.usb_device_id
  return false
})

// ── Carga ─────────────────────────────────────────────────────────────────────
onMounted(cargar)
async function cargar() {
  loading.value = true
  try { const{data}=await api.get(BASE); items.value=data } catch { items.value=[] }
  finally { loading.value=false }
}

// ── Modal ─────────────────────────────────────────────────────────────────────
function abrirModal(imp=null) {
  resetDetectores()
  modal.value = imp
    ? { visible:true, id:imp.id, name:imp.name, connection_type:imp.connection_type||'network', ip:imp.ip||'', bluetooth_address:imp.bluetooth_address||'', usb_device_id:imp.usb_device_id||'', is_active:imp.is_active }
    : { visible:true, id:null, name:'', connection_type:'network', ip:'', bluetooth_address:'', usb_device_id:'', is_active:1 }
  if (imp?.ip) { const p=imp.ip.split('.'); if(p.length===4) subred.value=p.slice(0,3).join('.') }
}
function cerrarModal() { modal.value.visible=false; resetDetectores() }
function cambiarTipo(t) { modal.value.connection_type=t; resetDetectores() }
function resetDetectores() {
  errorUSB.value=''; errorBT.value=''; estadoIP.value=''
  escaneando.value=false; escaneoHecho.value=false; encontradas.value=[]
  scanProgress.value=0; scanTotal.value=0
  testEstado.value=''; testMensaje.value=''; puedeImprimir.value=false
  btGattDevice.value=null
}

// ── Guardar ───────────────────────────────────────────────────────────────────
async function guardar() {
  if (!modal.value.name || !puedeGuardar.value) return
  guardando.value = true
  try {
    const p = { name:modal.value.name, connection_type:modal.value.connection_type, ip:modal.value.ip||null, bluetooth_address:modal.value.bluetooth_address||null, usb_device_id:modal.value.usb_device_id||null, is_active:modal.value.is_active }
    if (modal.value.id) await api.put(`${BASE}/${modal.value.id}`, p)
    else                await api.post(BASE, p)
    showToast('Impresora guardada', 'success')
    cerrarModal(); await cargar()
  } catch(e) { showToast(e?.response?.data?.detail || 'Error al guardar', 'error') }
  finally { guardando.value=false }
}

async function eliminar(imp) {
  const { isConfirmed } = await window.Swal.fire({
    title: `¿Eliminar "${imp.name}"?`,
    text: 'Se eliminará la impresora y sus asignaciones a artículos. Esta acción no se puede deshacer.',
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#e11d48',
    confirmButtonText: 'Sí, eliminar',
    cancelButtonText: 'Cancelar',
  })
  if (!isConfirmed) return
  try { await api.delete(`${BASE}/${imp.id}`); showToast('Impresora eliminada', 'success'); await cargar() }
  catch { showToast('Error al eliminar', 'error') }
}

// ── USB ───────────────────────────────────────────────────────────────────────
async function detectarUSB() {
  errorUSB.value = ''
  if (!navigator.usb) { errorUSB.value='Tu navegador no soporta Web USB. Usa Chrome o Edge.'; return }
  detectandoUSB.value = true
  try {
    const device = await navigator.usb.requestDevice({ filters: [{ classCode: 7 }] })
    modal.value.usb_device_id = `${device.vendorId}:${device.productId}`
    if (!modal.value.name) modal.value.name = device.productName || `Impresora USB ${device.productId}`
  } catch(e) { if (e.name !== 'NotFoundError') errorUSB.value = e.message || 'Error al conectar' }
  finally { detectandoUSB.value=false }
}

// ── Red ───────────────────────────────────────────────────────────────────────
async function detectarSubredLocal() {
  return new Promise(resolve => {
    try {
      const pc = new RTCPeerConnection({ iceServers:[] })
      pc.createDataChannel(''); let found=false
      pc.onicecandidate = e => {
        if (!e.candidate||found) return
        const m=/(\d{1,3}\.\d{1,3}\.\d{1,3})\.\d{1,3}/.exec(e.candidate.candidate)
        if (m&&!m[1].startsWith('0.')) { found=true; pc.close(); resolve(m[1]) }
      }
      pc.createOffer().then(o=>pc.setLocalDescription(o))
      setTimeout(()=>resolve(null),2000)
    } catch { resolve(null) }
  })
}

async function escanearRed() {
  encontradas.value=[]; escaneoHecho.value=false; estadoIP.value=''
  if (!subred.value) { const d=await detectarSubredLocal(); if(d) subred.value=d }
  if (!subred.value||!/^\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(subred.value)) { showToast('Ingresa una subred válida (ej: 192.168.1)','warning'); return }
  escaneando.value=true; scanTotal.value=254; scanProgress.value=0
  const found=[]; const BATCH=40
  for (let s=1;s<=254;s+=BATCH) {
    const end=Math.min(s+BATCH-1,254)
    const res=await Promise.all(Array.from({length:end-s+1},(_,i)=>probarConexion(`${subred.value}.${s+i}`)))
    res.forEach((ok,i)=>{ if(ok) found.push(`${subred.value}.${s+i}`) })
    scanProgress.value=end
  }
  encontradas.value=found; escaneoHecho.value=true; escaneando.value=false
}

async function probarConexion(ip, timeout=600) {
  return new Promise(resolve=>{
    try {
      const ws=new WebSocket(`ws://${ip}:9100`)
      const t=setTimeout(()=>{ try{ws.close()}catch{} resolve(false) },timeout)
      ws.onopen=()=>{ clearTimeout(t); ws.close(); resolve(true) }
      ws.onerror=()=>{ clearTimeout(t); resolve(false) }
    } catch { resolve(false) }
  })
}

async function probarIP() {
  if (!modal.value.ip) return
  probando.value=true; estadoIP.value=''
  const ok=await probarConexion(modal.value.ip,2000)
  estadoIP.value=ok?'online':'offline'; probando.value=false
}

// ── Bluetooth ─────────────────────────────────────────────────────────────────
async function detectarBluetooth() {
  errorBT.value=''
  if (!navigator.bluetooth) { errorBT.value='Tu navegador no soporta Bluetooth. Usa Chrome o Edge con HTTPS.'; return }
  detectandoBT.value=true
  try {
    const device = await navigator.bluetooth.requestDevice({
      acceptAllDevices: true,
      optionalServices: BLE_SERVICES.map(s=>s.svc),
    })
    modal.value.bluetooth_address = device.id
    modal.value.name = device.name || modal.value.name || 'Impresora Bluetooth'
    // Guardar referencia del objeto device para usarla en el test sin pasar por getDevices()
    btFoundDevice.value = device
  } catch(e) { if (e.name!=='NotFoundError') errorBT.value=e.message||'No se pudo conectar' }
  finally { detectandoBT.value=false }
}

// ── Test de conexión universal ────────────────────────────────────────────────
async function testConexion() {
  testando.value=true; testEstado.value=''; testMensaje.value=''; puedeImprimir.value=false; btGattDevice.value=null
  const tipo = modal.value.connection_type
  try {
    if (tipo==='network') {
      const ok=await probarConexion(modal.value.ip,2500)
      testEstado.value=ok?'online':'offline'
      testMensaje.value=ok?'Impresora en línea en puerto 9100':'Sin respuesta — verifica IP y que esté encendida'

    } else if (tipo==='usb') {
      if (!navigator.usb) { testEstado.value='offline'; testMensaje.value='Web USB no soportado en este navegador'; return }
      const [v,p]=(modal.value.usb_device_id||'0:0').split(':').map(Number)
      const devices=await navigator.usb.getDevices()
      const found=devices.some(d=>d.vendorId===v&&d.productId===p)
      testEstado.value=found?'online':'offline'
      testMensaje.value=found?'Dispositivo USB conectado y autorizado':'Dispositivo no encontrado — ¿está conectado?'

    } else if (tipo==='bluetooth') {
      if (!navigator.bluetooth) { testEstado.value='offline'; testMensaje.value='Web Bluetooth no soportado'; return }

      // 1. Usar referencia directa del dispositivo (mismo modal, mismo click de Buscar)
      let device = btFoundDevice.value

      // 2. Si no hay referencia directa, buscar en getDevices() (dispositivos autorizados previos)
      if (!device) {
        const known = await navigator.bluetooth.getDevices?.() ?? []
        device = known.find(d => d.id === modal.value.bluetooth_address) ?? null
      }

      // 3. Si tampoco está disponible → pedir re-vinculación mediante requestDevice
      if (!device) {
        testMensaje.value = 'Re-vinculando dispositivo…'
        try {
          device = await navigator.bluetooth.requestDevice({
            acceptAllDevices: true,
            optionalServices: BLE_SERVICES.map(s => s.svc),
          })
          // Actualizar referencia y address por si cambió el ID de sesión
          btFoundDevice.value = device
          modal.value.bluetooth_address = device.id
          if (device.name) modal.value.name = device.name
        } catch {
          testEstado.value = 'offline'
          testMensaje.value = 'No se pudo obtener el dispositivo — asegúrate de seleccionarlo en el diálogo'
          return
        }
      }

      // Intentar conexión GATT real
      let server
      try {
        server=await Promise.race([
          device.gatt.connect(),
          new Promise((_,rej)=>setTimeout(()=>rej(new Error('timeout')),6000)),
        ])
      } catch(e) {
        const msg=e?.message?.toLowerCase()??''
        if (msg.includes('classic')||msg.includes('br/edr')||msg.includes('not supported')||msg.includes('profile')) {
          testEstado.value='classic'
          testMensaje.value='Bluetooth Clásico (SPP/PIN) detectado. El navegador solo soporta BLE para impresión directa. Opciones: ① usa una impresora BLE ② configúrala como impresora de red WiFi'
        } else {
          testEstado.value='offline'
          testMensaje.value='Sin respuesta GATT — verifica que esté encendida y cerca'
        }
        return
      }
      // GATT conectado — buscar servicio de impresión
      let printChar=null
      for (const {svc,chr} of BLE_SERVICES) {
        try { const s=await server.getPrimaryService(svc); printChar=await s.getCharacteristic(chr); break }
        catch { continue }
      }
      if (printChar) {
        testEstado.value='online'; puedeImprimir.value=true; btGattDevice.value=device
        testMensaje.value='Impresora BLE en línea — lista para imprimir'
      } else {
        server.disconnect()
        testEstado.value='online'
        testMensaje.value='Dispositivo BLE conectado pero servicio de impresión no reconocido (UUIDs desconocidos)'
      }
    }
  } finally { testando.value=false }
}

// ── Imprimir prueba (BLE) ─────────────────────────────────────────────────────
function buildTestPrint() {
  const cmd=[0x1B,0x40, 0x1B,0x61,0x01, 0x1B,0x21,0x30]
  for (const c of 'EasyPOS') cmd.push(c.charCodeAt(0))
  cmd.push(0x0A,0x1B,0x21,0x00,0x1B,0x61,0x00)
  for (const c of '- Prueba de impresion -') cmd.push(c.charCodeAt(0))
  cmd.push(0x0A)
  const dt=new Date().toLocaleString('es-CO').replace(/[^\x00-\x7F]/g,'?')
  for (const c of dt) cmd.push(c.charCodeAt(0))
  cmd.push(0x0A,0x0A,0x0A,0x1D,0x56,0x42,0x00)
  return new Uint8Array(cmd)
}

async function imprimirPrueba() {
  if (!btGattDevice.value) return
  imprimiendo.value=true
  try {
    const server=btGattDevice.value.gatt.connected?btGattDevice.value.gatt:await btGattDevice.value.gatt.connect()
    let printChar=null
    for (const {svc,chr} of BLE_SERVICES) {
      try { const s=await server.getPrimaryService(svc); printChar=await s.getCharacteristic(chr); break }
      catch { continue }
    }
    if (!printChar) throw new Error('Servicio de impresión no encontrado')
    const data=buildTestPrint(); const CHUNK=512
    for (let i=0;i<data.length;i+=CHUNK) {
      await printChar.writeValue(data.slice(i,i+CHUNK))
      await new Promise(r=>setTimeout(r,30))
    }
    showToast('Página de prueba enviada a la impresora','success')
  } catch(e) { showToast(e.message||'Error al imprimir','error') }
  finally { imprimiendo.value=false }
}
</script>

<style scoped>
.crud-view  { padding:0; }
.crud-header { display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px; }
.crud-titulo { font-weight:700;font-size:16px;color:#1e3a5f;margin:0; }
.crud-sub    { font-size:13px;color:#64748b;margin:2px 0 0; }
.btn-nuevo   { display:flex;align-items:center;gap:6px;background:linear-gradient(90deg,#1e3a5f,#1d4ed8);color:#fff;border:none;border-radius:8px;padding:9px 16px;font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap; }
.estado-carga,.estado-vacio { display:flex;flex-direction:column;align-items:center;gap:10px;padding:60px 20px;color:#94a3b8;font-size:14px; }
.estado-vacio i { font-size:40px; }
.printers-grid { display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px; }
.printer-card  { display:flex;align-items:center;gap:12px;background:#fff;border:2px solid #e2e8f0;border-radius:12px;padding:14px;transition:border-color .15s; }
.printer-card:hover { border-color:#1d4ed8; }
.printer-card--off { opacity:.5; }
.printer-icon  { width:44px;height:44px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0; }
.printer-icon--usb       { background:#eff6ff;color:#1d4ed8; }
.printer-icon--network   { background:#f0fdf4;color:#16a34a; }
.printer-icon--bluetooth { background:#fdf4ff;color:#9333ea; }
.printer-info  { flex:1;display:flex;flex-direction:column;gap:2px; }
.printer-nombre{ font-weight:700;font-size:14px;color:#1e3a5f; }
.printer-tipo  { font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.3px;color:#94a3b8; }
.printer-detail{ font-size:12px;color:#64748b;font-family:monospace; }
.printer-badge-wrap { display:flex;flex-direction:column;align-items:flex-end; }
.badge-on  { font-size:10px;background:#dcfce7;color:#16a34a;border-radius:10px;padding:2px 8px;font-weight:700; }
.badge-off { font-size:10px;background:#f1f5f9;color:#94a3b8;border-radius:10px;padding:2px 8px; }
.printer-acciones { display:flex;gap:5px;flex-direction:column; }
.btn-icono { background:none;border:1px solid #e2e8f0;border-radius:6px;padding:5px 8px;cursor:pointer;color:#475569;font-size:13px; }
.btn-icono:hover { background:#f0f4ff;color:#1d4ed8;border-color:#1d4ed8; }
.btn-icono--danger:hover { background:#fff1f2;color:#e11d48;border-color:#e11d48; }
.modal-overlay { position:fixed;inset:0;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;z-index:1050;padding:16px; }
.modal-card    { background:#fff;border-radius:16px;width:100%;max-width:500px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.25);max-height:90vh;display:flex;flex-direction:column; }
.modal-hdr     { display:flex;justify-content:space-between;align-items:center;padding:16px 20px;background:linear-gradient(90deg,#1e3a5f,#1d4ed8);color:#fff;font-weight:700;font-size:15px;flex-shrink:0; }
.btn-x         { background:none;border:none;color:#fff;cursor:pointer;font-size:16px;opacity:.8; }
.modal-body    { padding:20px;display:flex;flex-direction:column;gap:14px;overflow-y:auto;flex:1; }
.campo         { display:flex;flex-direction:column;gap:4px; }
.campo label   { font-size:12px;font-weight:600;color:#475569; }
.inp           { border:1.5px solid #cbd5e1;border-radius:8px;padding:8px 12px;font-size:14px;color:#1e3a5f;outline:none;width:100%;box-sizing:border-box; }
.inp:focus     { border-color:#1d4ed8; }
.campo-check   { display:flex;align-items:center;gap:8px;font-size:13px;color:#475569; }
.modal-ftr     { display:flex;gap:10px;justify-content:flex-end;padding:14px 20px;border-top:1px solid #f1f5f9;flex-shrink:0; }
.btn-cancel    { background:#f1f5f9;border:none;border-radius:8px;padding:9px 18px;font-size:14px;cursor:pointer;color:#475569;font-weight:600; }
.btn-save      { background:linear-gradient(90deg,#1e3a5f,#1d4ed8);border:none;border-radius:8px;padding:9px 20px;font-size:14px;font-weight:700;color:#fff;cursor:pointer; }
.btn-save:disabled { opacity:.5;cursor:not-allowed; }
.tipo-btns { display:flex;gap:8px; }
.tipo-btn  { flex:1;display:flex;flex-direction:column;align-items:center;gap:4px;border:2px solid #e2e8f0;border-radius:10px;padding:10px 8px;cursor:pointer;background:#fff;font-size:12px;font-weight:600;color:#64748b;transition:.15s; }
.tipo-btn i { font-size:20px; }
.tipo-btn--sel { border-color:#1d4ed8;background:#eff6ff;color:#1d4ed8; }
.detector-box  { background:#f8fafc;border:1.5px solid #e2e8f0;border-radius:10px;padding:14px;display:flex;flex-direction:column;gap:10px; }
.detector-hint { font-size:12px;color:#64748b;margin:0; }
.btn-detect    { display:flex;align-items:center;justify-content:center;gap:6px;background:#1d4ed8;color:#fff;border:none;border-radius:8px;padding:10px 16px;font-size:13px;font-weight:600;cursor:pointer; }
.btn-detect:disabled { opacity:.6;cursor:not-allowed; }
.btn-detect--bt { background:#9333ea; }
.device-found  { font-size:13px;color:#1e3a5f;background:#f0fdf4;border-radius:6px;padding:8px 12px; }
.device-error  { font-size:12px;color:#dc2626;background:#fff1f2;border-radius:6px;padding:8px 12px; }
.scan-row      { display:flex;gap:8px;align-items:flex-end;flex-wrap:wrap; }
.subred-wrap   { display:flex;align-items:center;gap:4px;flex:1; }
.subred-label  { font-size:12px;color:#475569;white-space:nowrap; }
.inp-subred    { width:130px;flex:1; }
.found-list    { display:flex;flex-direction:column;gap:4px; }
.found-title   { font-size:12px;color:#475569;margin:0; }
.found-item    { display:flex;align-items:center;gap:8px;background:#fff;border:1.5px solid #e2e8f0;border-radius:8px;padding:8px 12px;font-size:13px;color:#1e3a5f;cursor:pointer;font-family:monospace;transition:.15s; }
.found-item:hover { border-color:#1d4ed8; }
.found-item--sel  { border-color:#1d4ed8;background:#eff6ff;font-weight:700; }
.ip-test-row   { display:flex;gap:8px; }
.btn-test      { background:#f1f5f9;border:1.5px solid #cbd5e1;border-radius:8px;padding:8px 14px;font-size:13px;cursor:pointer;white-space:nowrap;font-weight:600;color:#475569; }
.btn-test:disabled { opacity:.5;cursor:not-allowed; }
.ip-status     { font-size:12px;font-weight:600;display:flex;align-items:center;margin-top:4px; }
.ip-online  { color:#16a34a; }
.ip-offline { color:#dc2626; }
.test-box     { background:#f8fafc;border:1.5px solid #e2e8f0;border-radius:10px;padding:12px;display:flex;flex-direction:column;gap:8px; }
.test-row     { display:flex;align-items:center;justify-content:space-between;gap:10px; }
.test-label   { font-size:13px;font-weight:600;color:#475569; }
.btn-test-conn { display:flex;align-items:center;gap:4px;background:#0f172a;color:#fff;border:none;border-radius:8px;padding:7px 14px;font-size:12px;font-weight:600;cursor:pointer;white-space:nowrap; }
.btn-test-conn:disabled { opacity:.5;cursor:not-allowed; }
.test-result  { font-size:12px;font-weight:600;border-radius:6px;padding:7px 10px;line-height:1.4; }
.test-ok   { background:#f0fdf4;color:#16a34a; }
.test-warn { background:#fffbeb;color:#d97706; }
.test-fail { background:#fff1f2;color:#dc2626; }
.btn-print-test { display:flex;align-items:center;justify-content:center;gap:6px;background:#9333ea;color:#fff;border:none;border-radius:8px;padding:9px 14px;font-size:13px;font-weight:600;cursor:pointer;transition:opacity .15s; }
.btn-print-test:disabled { opacity:.5;cursor:not-allowed; }
@media(max-width:768px){.crud-header{flex-direction:column;gap:10px;}.printers-grid{grid-template-columns:1fr;}.tipo-btns{gap:6px;}.scan-row{flex-direction:column;}}
</style>
