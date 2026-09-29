/**
 * Impresión directa desde el navegador a impresoras USB y Bluetooth (ESC/POS).
 *
 * El servidor en la nube NO puede alcanzar una impresora conectada por USB o
 * Bluetooth al celular/PC del usuario: los bytes los arma el servidor (o el
 * componente) y se envían desde aquí con Web Bluetooth / WebUSB (Chrome).
 * Las impresoras de RED sí las atiende el servidor (IP:9100).
 */

// Servicios/características BLE habituales de impresoras térmicas ESC/POS
export const BLE_SERVICES = [
  { service: '000018f0-0000-1000-8000-00805f9b34fb', char: '000018f1-0000-1000-8000-00805f9b34fb' },
  { service: '0000ff00-0000-1000-8000-00805f9b34fb', char: '0000ff02-0000-1000-8000-00805f9b34fb' },
  { service: '6e400001-b5a3-f393-e0a9-e50e24dcca9e', char: '6e400002-b5a3-f393-e0a9-e50e24dcca9e' },
  { service: 'e7810a71-73ae-499d-8c15-faa9aef0c3f2', char: 'bef8d6c9-9c21-4c9e-b632-bd58c1009f9f' },
  { service: '49535343-fe7d-4ae5-8fa9-9fafd205e455', char: '49535343-8841-43f4-a8d4-ecbe34729bb3' },
]

export const isDirectPrinter = p => ['bluetooth', 'usb'].includes(String(p?.connection_type || '').toLowerCase())

export function base64ToBytes(b64) {
  const bin = atob(b64)
  const out = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i)
  return out
}

/** Error de "el usuario canceló la selección del dispositivo". */
export const isUserCancel = e => e?.name === 'NotFoundError' || e?.name === 'NotAllowedError'

export async function printBluetooth(printer, bytes) {
  if (!('bluetooth' in navigator)) throw new Error('Bluetooth no disponible en este navegador. Use Chrome en Android o PC.')
  const key = `bt_printer_${printer.id}`
  let device = null
  let storedId = null
  try { storedId = localStorage.getItem(key) } catch { /* sin storage */ }
  if (storedId && navigator.bluetooth.getDevices) {
    const devs = await navigator.bluetooth.getDevices()
    device = devs.find(d => d.id === storedId) || null
  }
  if (!device) {
    const name = String(printer.name || '')
    device = await navigator.bluetooth.requestDevice({
      filters: [{ name }, { namePrefix: name.split('-')[0] || name }],
      optionalServices: BLE_SERVICES.map(s => s.service),
    })
    try { localStorage.setItem(key, device.id) } catch { /* sin storage */ }
  }
  const server = device.gatt.connected ? device.gatt : await device.gatt.connect()
  try {
    for (const { service, char } of BLE_SERVICES) {
      let ch
      try { ch = await (await server.getPrimaryService(service)).getCharacteristic(char) }
      catch { continue }
      const CHUNK = 100
      for (let i = 0; i < bytes.length; i += CHUNK) {
        const slice = bytes.slice(i, i + CHUNK)
        try { await ch.writeValueWithoutResponse(slice) } catch { await ch.writeValue(slice) }
        await new Promise(r => setTimeout(r, 20))
      }
      return
    }
    try { localStorage.removeItem(key) } catch { /* sin storage */ }
    throw new Error('No se encontró el servicio de impresión (ESC/POS) en la impresora Bluetooth')
  } finally {
    try { server.disconnect() } catch { /* ya desconectada */ }
  }
}

export async function printUsb(printer, bytes) {
  if (!('usb' in navigator)) throw new Error('USB no disponible en este navegador. Use Chrome en PC o Android.')
  let vid = NaN, pid = NaN
  if (printer.usb_device_id) [vid, pid] = String(printer.usb_device_id).split(':').map(Number)
  let device = (await navigator.usb.getDevices()).find(d => d.vendorId === vid && d.productId === pid) || null
  if (!device) {
    const filters = [{ classCode: 7 }]                       // clase impresora USB
    if (!isNaN(vid)) filters.unshift({ vendorId: vid, productId: pid })
    device = await navigator.usb.requestDevice({ filters })
  }
  await device.open()
  try {
    if (device.configuration === null) await device.selectConfiguration(1)
    const iface = device.configuration.interfaces.find(i => i.alternate.interfaceClass === 7)
      || device.configuration.interfaces[0]
    await device.claimInterface(iface.interfaceNumber)
    const endpoint = iface.alternate.endpoints.find(e => e.direction === 'out' && e.type === 'bulk')
    if (!endpoint) throw new Error('No se encontró la salida de datos (bulk-out) en la impresora USB')
    const CHUNK = 4096
    for (let i = 0; i < bytes.length; i += CHUNK) {
      await device.transferOut(endpoint.endpointNumber, bytes.slice(i, i + CHUNK))
    }
    await device.releaseInterface(iface.interfaceNumber)
  } finally {
    try { await device.close() } catch { /* ya cerrada */ }
  }
}

/** Envía bytes ESC/POS a una impresora USB o Bluetooth según su tipo. */
export async function printDirect(printer, bytes) {
  const type = String(printer?.connection_type || '').toLowerCase()
  if (type === 'bluetooth') return printBluetooth(printer, bytes)
  if (type === 'usb') return printUsb(printer, bytes)
  throw new Error('La impresora no es USB ni Bluetooth')
}
