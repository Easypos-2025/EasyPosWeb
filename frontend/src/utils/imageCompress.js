/**
 * Compresión de imágenes en el navegador antes de subirlas.
 *
 * Reduce dimensiones y calidad hasta que la imagen pese menos de `maxBytes`,
 * así una foto de celular de 3–8 MB queda en ~300–700 KB y cada envío es liviano.
 * Se usa desde ImageUploaderPro y los componentes que suben fotos.
 */

export const DEFAULT_MAX_BYTES = 800 * 1024

function canvasToBlob(canvas, type, quality) {
  return new Promise(resolve => canvas.toBlob(resolve, type, quality))
}

/**
 * Canvas → Blob bajo `maxBytes`: baja la calidad por pasos y, si no alcanza,
 * reduce el tamaño del lienzo. Devuelve el mejor blob logrado.
 */
export async function canvasToBlobUnder(canvas, {
  type = 'image/jpeg', quality = 0.85, maxBytes = DEFAULT_MAX_BYTES, minQuality = 0.5,
} = {}) {
  let src = canvas
  let best = null
  for (let round = 0; round < 4; round++) {
    for (let q = quality; q >= minQuality - 0.001; q -= 0.1) {
      const blob = await canvasToBlob(src, type, q)
      if (!blob) return best
      if (!best || blob.size < best.size) best = blob
      if (blob.size <= maxBytes) return blob
    }
    // Aún pesada: reducir dimensiones un 20 % y volver a intentar
    const next = document.createElement('canvas')
    next.width  = Math.max(1, Math.round(src.width * 0.8))
    next.height = Math.max(1, Math.round(src.height * 0.8))
    const ctx = next.getContext('2d')
    if (type === 'image/jpeg') { ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, next.width, next.height) }
    ctx.drawImage(src, 0, 0, next.width, next.height)
    src = next
  }
  return best
}

async function loadImage(file) {
  // createImageBitmap respeta la orientación EXIF de las fotos del celular
  if (typeof createImageBitmap === 'function') {
    try { return await createImageBitmap(file, { imageOrientation: 'from-image' }) } catch { /* fallback */ }
  }
  const url = URL.createObjectURL(file)
  try {
    const img = new Image()
    img.src = url
    await new Promise((resolve, reject) => { img.onload = resolve; img.onerror = reject })
    return img
  } finally {
    URL.revokeObjectURL(url)
  }
}

/**
 * Comprime un File/Blob de imagen. Devuelve un Blob (JPEG por defecto).
 * Si ya es liviano y de tamaño razonable, lo devuelve sin tocar.
 */
export async function compressImage(file, {
  maxWidth = 1600, maxHeight = 1600, maxBytes = DEFAULT_MAX_BYTES,
  type = 'image/jpeg', quality = 0.85,
} = {}) {
  const img = await loadImage(file)
  const w = img.width || img.naturalWidth
  const h = img.height || img.naturalHeight

  const alreadyOk = file.size <= maxBytes && w <= maxWidth && h <= maxHeight &&
                    ['image/jpeg', 'image/webp'].includes(file.type)
  if (alreadyOk) { img.close?.(); return file }

  const scale  = Math.min(1, maxWidth / w, maxHeight / h)
  const canvas = document.createElement('canvas')
  canvas.width  = Math.max(1, Math.round(w * scale))
  canvas.height = Math.max(1, Math.round(h * scale))
  const ctx = canvas.getContext('2d')
  if (type === 'image/jpeg') { ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height) }
  ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
  img.close?.()

  return canvasToBlobUnder(canvas, { type, quality, maxBytes })
}

/** Blob comprimido → File con nombre y extensión acordes al tipo. */
export function blobToFile(blob, baseName = 'foto') {
  const ext = blob.type === 'image/webp' ? 'webp' : blob.type === 'image/png' ? 'png' : 'jpg'
  return new File([blob], `${baseName}_${Date.now()}.${ext}`, { type: blob.type || 'image/jpeg' })
}
