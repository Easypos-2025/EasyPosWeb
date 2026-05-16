<template>
  <div class="img-uploader">

    <!-- Zona de preview -->
    <div class="preview-zone" @click="fileInputRef?.click()">
      <img v-if="displayUrl" :src="displayUrl" class="preview-img" alt="Foto del artículo" />
      <div v-else class="preview-placeholder">
        <i class="bi bi-image"></i>
        <span>Sin foto</span>
      </div>
      <div class="preview-hover">
        <i class="bi bi-camera-fill"></i>
        <span>Cambiar foto</span>
      </div>
    </div>

    <!-- Botones -->
    <div class="img-btns">
      <button type="button" class="btn-img" @click.stop="fileInputRef?.click()">
        <i class="bi bi-folder2-open me-1"></i>Archivo
      </button>
      <button type="button" class="btn-img" @click.stop="cameraInputRef?.click()">
        <i class="bi bi-camera me-1"></i>Cámara
      </button>
      <button v-if="previewUrl" type="button" class="btn-img btn-img--danger" @click.stop="removePhoto">
        <i class="bi bi-trash"></i>
      </button>
    </div>

    <!-- Inputs ocultos -->
    <input ref="fileInputRef"   type="file" accept="image/*"                    class="inp-hidden" @change="onFileSelected" />
    <input ref="cameraInputRef" type="file" accept="image/*" capture="environment" class="inp-hidden" @change="onFileSelected" />

    <!-- Overlay de recorte (teletransportado al body para evitar z-index del modal) -->
    <Teleport to="body">
      <div v-if="cropVisible" class="crop-overlay" @click.self="cancelCrop">
        <div class="crop-modal">

          <div class="crop-header">
            <span><i class="bi bi-crop me-2"></i>Ajustar foto</span>
            <button class="btn-crop-x" @click="cancelCrop"><i class="bi bi-x-lg"></i></button>
          </div>

          <div class="crop-body">
            <canvas
              ref="canvasRef"
              :width="CS"
              :height="CS"
              class="crop-canvas"
              @mousedown="onMouseDown"
              @mousemove="onMouseMove"
              @mouseup="stopDrag"
              @mouseleave="stopDrag"
              @wheel.prevent="onWheel"
              @touchstart.prevent="onTouchStart"
              @touchmove.prevent="onTouchMove"
              @touchend="stopDrag"
            />
            <p class="crop-hint">
              <i class="bi bi-hand-index-thumb me-1"></i>
              Arrastra · Pellizca para zoom
            </p>
            <div class="crop-zoom-btns">
              <button type="button" class="btn-zoom" @click="applyZoom(0.85, CS/2, CS/2)"><i class="bi bi-zoom-out"></i></button>
              <button type="button" class="btn-zoom" @click="applyZoom(1.15, CS/2, CS/2)"><i class="bi bi-zoom-in"></i></button>
            </div>
          </div>

          <div class="crop-footer">
            <button type="button" class="btn-crop-cancel" @click="cancelCrop">Cancelar</button>
            <button type="button" class="btn-crop-confirm" @click="confirmCrop">
              <i class="bi bi-check-lg me-1"></i>Confirmar recorte
            </button>
          </div>

        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps({
  currentUrl: { type: String, default: null },
})
const emit = defineEmits(['change', 'remove'])

const CS = 300  // tamaño del canvas en píxeles lógicos

const fileInputRef   = ref(null)
const cameraInputRef = ref(null)
const canvasRef      = ref(null)
const previewUrl     = ref(props.currentUrl)
const cropVisible    = ref(false)

// ── Estado del crop ────────────────────────────────────────────────────────────
let srcImage     = null
let imgX         = 0
let imgY         = 0
let imgScale     = 1
let isDragging   = false
let lastCX       = 0   // clientX del último evento
let lastCY       = 0
let lastPinchDist = 0
let lastPinchMX  = 0
let lastPinchMY  = 0

watch(() => props.currentUrl, v => { previewUrl.value = v })

// Las imágenes locales del servidor necesitan la URL base en desarrollo
const API_BASE = import.meta.env.VITE_API_URL || ''
const displayUrl = computed(() => {
  const u = previewUrl.value
  if (!u) return null
  if (u.startsWith('blob:') || u.startsWith('http')) return u
  return API_BASE + u
})

// ── Selección de archivo ───────────────────────────────────────────────────────
function onFileSelected(e) {
  const file = e.target.files?.[0]
  if (!file) return
  e.target.value = ''
  const reader = new FileReader()
  reader.onload = ev => loadForCrop(ev.target.result)
  reader.readAsDataURL(file)
}

function loadForCrop(dataUrl) {
  const img = new Image()
  img.onload = () => {
    srcImage = img
    // Escala inicial: el lado MAYOR llena el canvas (zoom out = imagen completa visible)
    const minSide = Math.min(img.naturalWidth, img.naturalHeight)
    imgScale = CS / minSide
    imgX = (CS - img.naturalWidth  * imgScale) / 2
    imgY = (CS - img.naturalHeight * imgScale) / 2
    cropVisible.value = true
    nextTick(() => drawCanvas())
  }
  img.src = dataUrl
}

// ── Canvas ─────────────────────────────────────────────────────────────────────
function drawCanvas() {
  const cv = canvasRef.value
  if (!cv || !srcImage) return
  const ctx = cv.getContext('2d')
  ctx.clearRect(0, 0, CS, CS)
  ctx.drawImage(srcImage, imgX, imgY, srcImage.naturalWidth * imgScale, srcImage.naturalHeight * imgScale)
  // Cuadrícula de tercios
  ctx.strokeStyle = 'rgba(255,255,255,0.25)'
  ctx.lineWidth = 1
  for (let i = 1; i < 3; i++) {
    ctx.beginPath(); ctx.moveTo(CS * i / 3, 0);  ctx.lineTo(CS * i / 3, CS);  ctx.stroke()
    ctx.beginPath(); ctx.moveTo(0, CS * i / 3);  ctx.lineTo(CS, CS * i / 3);  ctx.stroke()
  }
}

function clampImage() {
  if (!srcImage) return
  const w = srcImage.naturalWidth  * imgScale
  const h = srcImage.naturalHeight * imgScale
  imgX = w < CS ? (CS - w) / 2 : Math.min(0, Math.max(CS - w, imgX))
  imgY = h < CS ? (CS - h) / 2 : Math.min(0, Math.max(CS - h, imgY))
}

// Factor CSS → canvas (canvas puede estar escalado por CSS)
function cssToCanvas() {
  const cv = canvasRef.value
  if (!cv) return 1
  return CS / cv.getBoundingClientRect().width
}

// ── Mouse ──────────────────────────────────────────────────────────────────────
function onMouseDown(e) {
  isDragging = true
  lastCX = e.clientX; lastCY = e.clientY
}
function onMouseMove(e) {
  if (!isDragging) return
  const f = cssToCanvas()
  imgX += (e.clientX - lastCX) * f
  imgY += (e.clientY - lastCY) * f
  lastCX = e.clientX; lastCY = e.clientY
  clampImage(); drawCanvas()
}
function stopDrag() { isDragging = false }

function onWheel(e) {
  applyZoom(e.deltaY < 0 ? 1.12 : 0.88, e.clientX, e.clientY)
}

// ── Touch ──────────────────────────────────────────────────────────────────────
function onTouchStart(e) {
  if (e.touches.length === 2) {
    isDragging = false
    lastPinchDist = pinchDist(e)
    const m = pinchMid(e)
    lastPinchMX = m.x; lastPinchMY = m.y
  } else {
    isDragging = true
    lastCX = e.touches[0].clientX
    lastCY = e.touches[0].clientY
  }
}
function onTouchMove(e) {
  const f = cssToCanvas()
  if (e.touches.length === 2) {
    isDragging = false
    const dist = pinchDist(e)
    const m    = pinchMid(e)
    applyZoom(dist / lastPinchDist, m.x, m.y)
    // Pan simultáneo al pinch
    imgX += (m.x - lastPinchMX) * f
    imgY += (m.y - lastPinchMY) * f
    lastPinchDist = dist; lastPinchMX = m.x; lastPinchMY = m.y
    clampImage(); drawCanvas()
  } else if (isDragging) {
    imgX += (e.touches[0].clientX - lastCX) * f
    imgY += (e.touches[0].clientY - lastCY) * f
    lastCX = e.touches[0].clientX; lastCY = e.touches[0].clientY
    clampImage(); drawCanvas()
  }
}

function pinchDist(e) {
  return Math.hypot(e.touches[0].clientX - e.touches[1].clientX,
                    e.touches[0].clientY - e.touches[1].clientY)
}
function pinchMid(e) {
  return { x: (e.touches[0].clientX + e.touches[1].clientX) / 2,
           y: (e.touches[0].clientY + e.touches[1].clientY) / 2 }
}

// ── Zoom ───────────────────────────────────────────────────────────────────────
function applyZoom(factor, clientCX, clientCY) {
  if (!srcImage) return
  const cv   = canvasRef.value
  const rect = cv.getBoundingClientRect()
  const f    = CS / rect.width
  const cx   = (clientCX - rect.left) * f
  const cy   = (clientCY - rect.top)  * f

  const minScale = Math.max(CS / srcImage.naturalWidth, CS / srcImage.naturalHeight)
  const newScale = Math.max(minScale * 0.5, Math.min(8, imgScale * factor))
  const ratio    = newScale / imgScale
  imgX     = cx - (cx - imgX) * ratio
  imgY     = cy - (cy - imgY) * ratio
  imgScale = newScale
  clampImage(); drawCanvas()
}

// ── Acciones del crop ──────────────────────────────────────────────────────────
function cancelCrop() {
  cropVisible.value = false
  srcImage = null
}

function confirmCrop() {
  if (!canvasRef.value || !srcImage) return

  // Calcular el área del srcImage visible en el canvas
  const srcX = -imgX / imgScale
  const srcY = -imgY / imgScale
  const srcW =  CS   / imgScale
  const srcH =  CS   / imgScale

  const out    = document.createElement('canvas')
  out.width    = 800
  out.height   = 800
  const outCtx = out.getContext('2d')
  outCtx.drawImage(srcImage, srcX, srcY, srcW, srcH, 0, 0, 800, 800)

  out.toBlob(blob => {
    if (!blob) return
    if (previewUrl.value?.startsWith('blob:')) URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = URL.createObjectURL(blob)
    emit('change', blob)
    cropVisible.value = false
    srcImage = null
  }, 'image/webp', 0.88)
}

function removePhoto() {
  if (previewUrl.value?.startsWith('blob:')) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = null
  emit('remove')
}
</script>

<style scoped>
.img-uploader { display:flex; flex-direction:column; gap:8px; }

/* ── Preview ─────────────────────────────────────────────────────────────────── */
.preview-zone {
  position:relative; width:100%; height:160px; border-radius:10px;
  overflow:hidden; cursor:pointer; background:#f1f5f9;
  border:2px dashed #cbd5e1; transition:border-color .15s;
}
.preview-zone:hover { border-color:#1d4ed8; }
.preview-img { width:100%; height:100%; object-fit:cover; display:block; }
.preview-placeholder {
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  height:100%; color:#94a3b8; gap:6px;
}
.preview-placeholder i { font-size:32px; }
.preview-placeholder span { font-size:13px; }
.preview-hover {
  position:absolute; inset:0; background:rgba(0,0,0,.45); display:flex;
  flex-direction:column; align-items:center; justify-content:center;
  color:#fff; gap:4px; font-size:13px; opacity:0; transition:opacity .2s;
}
.preview-zone:hover .preview-hover { opacity:1; }
.preview-hover i { font-size:22px; }

/* ── Botones ─────────────────────────────────────────────────────────────────── */
.img-btns { display:flex; gap:8px; }
.btn-img {
  flex:1; display:flex; align-items:center; justify-content:center;
  gap:4px; border:1.5px solid #cbd5e1; background:#f8fafc; border-radius:8px;
  padding:7px 10px; font-size:12px; font-weight:600; color:#475569; cursor:pointer;
  transition:.15s;
}
.btn-img:hover { border-color:#1d4ed8; color:#1d4ed8; background:#f0f4ff; }
.btn-img--danger { flex:0; padding:7px 12px; }
.btn-img--danger:hover { border-color:#e11d48; color:#e11d48; background:#fff1f2; }
.inp-hidden { display:none; }

/* ── Overlay de crop ─────────────────────────────────────────────────────────── */
.crop-overlay {
  position:fixed; inset:0; background:rgba(0,0,0,.72);
  display:flex; align-items:center; justify-content:center; z-index:9999;
  padding:16px;
}
.crop-modal {
  background:#1e293b; border-radius:16px; overflow:hidden;
  width:100%; max-width:380px; box-shadow:0 24px 80px rgba(0,0,0,.6);
}
.crop-header {
  display:flex; justify-content:space-between; align-items:center;
  padding:14px 18px; background:#0f172a; color:#f1f5f9;
  font-weight:700; font-size:14px;
}
.btn-crop-x {
  background:none; border:none; color:#94a3b8; cursor:pointer; font-size:16px; padding:2px;
}
.btn-crop-x:hover { color:#f1f5f9; }
.crop-body { display:flex; flex-direction:column; align-items:center; gap:10px; padding:16px; }
.crop-canvas {
  width: min(300px, calc(100vw - 80px));
  height: min(300px, calc(100vw - 80px));
  border-radius:8px; display:block; cursor:grab; touch-action:none;
}
.crop-canvas:active { cursor:grabbing; }
.crop-hint { font-size:11px; color:#64748b; margin:0; text-align:center; }
.crop-zoom-btns { display:flex; gap:8px; }
.btn-zoom {
  background:#334155; border:none; border-radius:8px; width:38px; height:38px;
  color:#94a3b8; font-size:16px; cursor:pointer; display:flex; align-items:center; justify-content:center;
  transition:.15s;
}
.btn-zoom:hover { background:#475569; color:#f1f5f9; }
.crop-footer {
  display:flex; gap:10px; justify-content:flex-end;
  padding:14px 18px; border-top:1px solid #334155;
}
.btn-crop-cancel {
  background:#334155; border:none; border-radius:8px; padding:9px 16px;
  color:#94a3b8; font-size:13px; font-weight:600; cursor:pointer;
}
.btn-crop-cancel:hover { color:#f1f5f9; }
.btn-crop-confirm {
  background:linear-gradient(90deg,#1e3a5f,#1d4ed8); border:none; border-radius:8px;
  padding:9px 18px; color:#fff; font-size:13px; font-weight:700; cursor:pointer;
}
.btn-crop-confirm:hover { opacity:.9; }

@media (max-width: 576px) {
  .preview-zone { height:140px; }
}
</style>
