<template>
  <div class="iup-root">

    <!-- Zona de preview / drop -->
    <div
      class="iup-preview"
      :class="{ 'iup-preview--drag': isDragging }"
      @click="triggerFile"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="onDrop"
    >
      <img v-if="displayUrl" :src="displayUrl" class="iup-preview__img" :alt="label" />
      <div v-else class="iup-preview__empty">
        <i class="bi bi-image"></i>
        <span>{{ label }}</span>
      </div>
      <div class="iup-preview__hover">
        <i class="bi bi-camera-fill"></i>
        <span>Cambiar foto</span>
      </div>
    </div>

    <!-- Botones -->
    <div class="iup-btns">
      <button type="button" class="iup-btn" @click.stop="triggerFile">
        <i class="bi bi-folder2-open me-1"></i>Archivo
      </button>
      <button type="button" class="iup-btn" @click.stop="triggerCamera">
        <i class="bi bi-camera me-1"></i>Cámara
      </button>
      <button v-if="showRemove && previewUrl" type="button" class="iup-btn iup-btn--danger" @click.stop="removePhoto">
        <i class="bi bi-trash"></i>
      </button>
    </div>

    <!-- Inputs ocultos -->
    <input ref="fileRef"   type="file" accept="image/*"                     class="iup-hidden" @change="onFileSelected" />
    <input ref="cameraRef" type="file" accept="image/*" capture="environment" class="iup-hidden" @change="onFileSelected" />

    <!-- Modal editor -->
    <Teleport to="body">
      <div v-if="editorOpen" class="iup-overlay" @click.self="cancelEdit">
        <div class="iup-modal">

          <div class="iup-modal__header">
            <span class="iup-modal__title"><i class="bi bi-crop me-2"></i>Ajustar foto</span>
            <div class="iup-ratio-btns">
              <button :class="['iup-ratio-btn', { active: cropRatio === 0 }]"      @click="cropRatio = 0">Libre</button>
              <button :class="['iup-ratio-btn', { active: cropRatio === 1 }]"      @click="cropRatio = 1">1:1</button>
              <button :class="['iup-ratio-btn', { active: cropRatio === 16/9 }]"   @click="cropRatio = 16/9">16:9</button>
              <button :class="['iup-ratio-btn', { active: cropRatio === 4/3 }]"    @click="cropRatio = 4/3">4:3</button>
            </div>
            <button class="iup-modal__close" @click="cancelEdit"><i class="bi bi-x-lg"></i></button>
          </div>

          <div class="iup-modal__area">
            <Cropper
              ref="cropperRef"
              :src="rawSrc"
              image-restriction="none"
              :auto-zoom="true"
              :stencil-props="{ movable: true, resizable: true, aspectRatio: cropRatio || undefined }"
            />
          </div>

          <div class="iup-modal__footer">
            <div class="iup-rotate-btns">
              <button type="button" class="iup-rotate-btn" title="Girar izquierda" @click="rotate(-90)">
                <i class="bi bi-arrow-counterclockwise"></i>
              </button>
              <button type="button" class="iup-rotate-btn" title="Girar derecha" @click="rotate(90)">
                <i class="bi bi-arrow-clockwise"></i>
              </button>
            </div>
            <div class="iup-footer-spacer"></div>
            <button type="button" class="iup-btn-cancel" @click="cancelEdit">Cancelar</button>
            <button type="button" class="iup-btn-confirm" @click="confirmEdit">
              <i class="bi bi-check-lg me-1"></i>Confirmar
            </button>
          </div>

        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Cropper } from 'vue-advanced-cropper'
import 'vue-advanced-cropper/dist/style.css'

const props = defineProps({
  currentUrl:    { type: String,  default: null  },
  outputWidth:   { type: Number,  default: 800   },
  outputHeight:  { type: Number,  default: null  },   // null = igual a outputWidth (cuadrado)
  outputFormat:  { type: String,  default: 'webp' },
  outputQuality: { type: Number,  default: 0.88  },
  label:         { type: String,  default: 'Sin foto' },
  showRemove:    { type: Boolean, default: true   },
})
const emit = defineEmits(['change', 'remove'])

const fileRef    = ref(null)
const cameraRef  = ref(null)
const cropperRef = ref(null)
const previewUrl = ref(props.currentUrl)
const rawSrc     = ref('')
const editorOpen = ref(false)
const cropRatio  = ref(0)
const isDragging = ref(false)

watch(() => props.currentUrl, v => { previewUrl.value = v })

const API_BASE   = import.meta.env.VITE_API_URL || ''
const displayUrl = computed(() => {
  const u = previewUrl.value
  if (!u) return null
  if (u.startsWith('blob:') || u.startsWith('http') || u.startsWith('data:')) return u
  return API_BASE + u
})

function triggerFile()   { fileRef.value?.click() }
function triggerCamera() { cameraRef.value?.click() }

function onDrop(e) {
  isDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file?.type.startsWith('image/')) openEditor(file)
}

function onFileSelected(e) {
  const file = e.target.files?.[0]
  if (!file) return
  e.target.value = ''
  openEditor(file)
}

function openEditor(file) {
  if (rawSrc.value) URL.revokeObjectURL(rawSrc.value)
  rawSrc.value    = URL.createObjectURL(file)
  cropRatio.value = 0
  editorOpen.value = true
}

function rotate(deg) {
  cropperRef.value?.rotate(deg)
}

async function confirmEdit() {
  if (!cropperRef.value) return
  const { canvas } = cropperRef.value.getResult()
  if (!canvas) return

  const W = props.outputWidth
  const H = props.outputHeight ?? props.outputWidth

  const out    = document.createElement('canvas')
  out.width    = W
  out.height   = H
  out.getContext('2d').drawImage(canvas, 0, 0, W, H)

  const mime = props.outputFormat === 'webp' ? 'image/webp' : 'image/jpeg'
  const blob = await new Promise(r => out.toBlob(r, mime, props.outputQuality))
  if (!blob) return

  if (previewUrl.value?.startsWith('blob:')) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = URL.createObjectURL(blob)
  emit('change', blob)
  closeEditor()
}

function cancelEdit() { closeEditor() }
function closeEditor() {
  editorOpen.value = false
  if (rawSrc.value) { URL.revokeObjectURL(rawSrc.value); rawSrc.value = '' }
}

function removePhoto() {
  if (previewUrl.value?.startsWith('blob:')) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = null
  emit('remove')
}
</script>

<style scoped>
/* ── Root ───────────────────────────────────────────────────────────────────── */
.iup-root { display: flex; flex-direction: column; gap: 8px; }

/* ── Preview zone ───────────────────────────────────────────────────────────── */
.iup-preview {
  position: relative; width: 100%; height: 160px;
  border-radius: 10px; overflow: hidden; cursor: pointer;
  background: #f1f5f9; border: 2px dashed #cbd5e1; transition: border-color .15s;
}
.iup-preview:hover,
.iup-preview--drag { border-color: #1d4ed8; background: #eff6ff; }
.iup-preview__img  { width: 100%; height: 100%; object-fit: cover; display: block; }
.iup-preview__empty {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; height: 100%; color: #94a3b8; gap: 6px;
}
.iup-preview__empty i    { font-size: 32px; }
.iup-preview__empty span { font-size: 13px; }
.iup-preview__hover {
  position: absolute; inset: 0; background: rgba(0,0,0,.45);
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; color: #fff; gap: 4px;
  font-size: 13px; opacity: 0; transition: opacity .2s;
}
.iup-preview:hover .iup-preview__hover { opacity: 1; }
.iup-preview__hover i { font-size: 22px; }

/* ── Botones de acción ──────────────────────────────────────────────────────── */
.iup-btns  { display: flex; gap: 8px; }
.iup-btn {
  flex: 1; display: flex; align-items: center; justify-content: center;
  gap: 4px; border: 1.5px solid #cbd5e1; background: #f8fafc;
  border-radius: 8px; padding: 7px 10px; font-size: 12px;
  font-weight: 600; color: #475569; cursor: pointer; transition: .15s;
}
.iup-btn:hover          { border-color: #1d4ed8; color: #1d4ed8; background: #f0f4ff; }
.iup-btn--danger        { flex: 0; padding: 7px 12px; }
.iup-btn--danger:hover  { border-color: #e11d48; color: #e11d48; background: #fff1f2; }
.iup-hidden             { display: none; }

/* ── Overlay ────────────────────────────────────────────────────────────────── */
.iup-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.72);
  display: flex; align-items: center; justify-content: center;
  z-index: 9999; padding: 16px;
}

/* ── Modal ──────────────────────────────────────────────────────────────────── */
.iup-modal {
  background: #1e293b; border-radius: 16px; overflow: hidden;
  width: 100%; max-width: 680px; max-height: 92vh;
  display: flex; flex-direction: column;
  box-shadow: 0 24px 80px rgba(0,0,0,.6);
}

.iup-modal__header {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  padding: 14px 18px; background: #0f172a; flex-shrink: 0;
}
.iup-modal__title {
  font-size: 15px; font-weight: 700; color: #f1f5f9; flex-shrink: 0;
}
.iup-modal__close {
  background: none; border: none; color: #94a3b8; cursor: pointer;
  font-size: 17px; padding: 2px; margin-left: auto; flex-shrink: 0;
}
.iup-modal__close:hover { color: #f1f5f9; }

/* ── Ratio buttons ──────────────────────────────────────────────────────────── */
.iup-ratio-btns { display: flex; gap: 5px; flex-wrap: wrap; }
.iup-ratio-btn {
  padding: 4px 11px; border-radius: 20px;
  border: 1px solid #334155; background: #1e293b;
  font-size: 12px; font-weight: 500; cursor: pointer;
  transition: all .15s; color: #94a3b8;
}
.iup-ratio-btn:hover        { border-color: #64748b; color: #f1f5f9; }
.iup-ratio-btn.active       { background: #1d4ed8; border-color: #1d4ed8; color: #fff; }

/* ── Crop area ──────────────────────────────────────────────────────────────── */
.iup-modal__area {
  flex: 1; min-height: 280px; max-height: 55vh;
  background: #0f172a; overflow: hidden; position: relative;
}

/* ── Footer ─────────────────────────────────────────────────────────────────── */
.iup-modal__footer {
  display: flex; align-items: center; gap: 10px;
  padding: 13px 18px; border-top: 1px solid #334155; flex-shrink: 0;
}
.iup-footer-spacer { flex: 1; }

.iup-rotate-btns { display: flex; gap: 6px; }
.iup-rotate-btn {
  background: #334155; border: none; border-radius: 8px;
  width: 38px; height: 38px; color: #94a3b8; font-size: 17px;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: .15s;
}
.iup-rotate-btn:hover { background: #475569; color: #f1f5f9; }

.iup-btn-cancel {
  background: #334155; border: none; border-radius: 8px;
  padding: 9px 16px; color: #94a3b8; font-size: 13px;
  font-weight: 600; cursor: pointer; transition: .15s;
}
.iup-btn-cancel:hover { color: #f1f5f9; }

.iup-btn-confirm {
  background: linear-gradient(90deg,#1e3a5f,#1d4ed8); border: none;
  border-radius: 8px; padding: 9px 18px; color: #fff;
  font-size: 13px; font-weight: 700; cursor: pointer;
  display: flex; align-items: center; transition: opacity .15s;
}
.iup-btn-confirm:hover { opacity: .9; }

/* ── Responsive ─────────────────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .iup-preview  { height: 150px; }
  .iup-modal    { max-width: 100%; }
  .iup-modal__area { min-height: 240px; }
}
@media (max-width: 576px) {
  .iup-preview  { height: 130px; }
  .iup-modal__footer { flex-wrap: wrap; }
  .iup-ratio-btns { flex-wrap: wrap; }
  .iup-footer-spacer { display: none; }
}
</style>
