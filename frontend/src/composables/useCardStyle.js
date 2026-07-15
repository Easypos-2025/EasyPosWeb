import { ref } from 'vue'
import api from '@/services/apis'

const _style = ref(null)
let _loaded  = false

export const CARD_STYLES = [
  { key: 'oval-wood',     label: 'Mesa de madera',  icon: 'bi-table',        desc: 'Óvalo clásico con textura de madera' },
  { key: 'circular-gold', label: 'Círculo dorado',  icon: 'bi-circle-fill',  desc: 'Círculo con gradiente dorado/amber' },
  { key: 'checkered',     label: 'Mantel cuadros',  icon: 'bi-grid-3x3',     desc: 'Estilo pizzería con cuadros rojo/blanco' },
  { key: 'minimal-card',  label: 'Tarjeta mínima',  icon: 'bi-card-text',    desc: 'Tarjeta plana con acento de color' },
  { key: 'ticket',        label: 'Ticket / Recibo', icon: 'bi-receipt-cutoff',desc: 'Comprobante estilo recibo de taquilla' },
  { key: 'bubble',        label: 'Burbuja',         icon: 'bi-chat-fill',    desc: 'Burbuja redondeada con gradiente suave' },
]

export function useCardStyle() {
  async function load(companyId) {
    if (_loaded && _style.value) return _style.value
    const cached = localStorage.getItem('pos_card_style')
    if (cached) { _style.value = cached; _loaded = true; return cached }
    try {
      const params = companyId ? { company_id: companyId } : {}
      const { data } = await api.get('/api/pos-dashboard/card-style', { params })
      _style.value = data.style || 'oval-wood'
      localStorage.setItem('pos_card_style', _style.value)
      _loaded = true
    } catch {
      _style.value = 'oval-wood'
    }
    return _style.value
  }

  async function save(style, companyId) {
    // Actualización optimista: refleja el cambio de inmediato en la UI
    const prev = _style.value
    _style.value = style
    _loaded = true
    localStorage.setItem('pos_card_style', style)
    try {
      const { data } = await api.put('/api/pos-dashboard/card-style', {
        style,
        company_id: companyId || undefined,
      })
      return data
    } catch (err) {
      // Revertir si el backend falla
      _style.value = prev
      localStorage.setItem('pos_card_style', prev || 'oval-wood')
      throw err
    }
  }

  function reset() {
    _style.value = null
    _loaded = false
    localStorage.removeItem('pos_card_style')
  }

  return { cardStyle: _style, load, save, reset, CARD_STYLES }
}
