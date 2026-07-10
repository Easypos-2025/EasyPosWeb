<template>
  <Teleport to="body">
    <div v-if="open" class="mau-overlay" @click.self="cerrar">
      <div class="mau-modal">

        <!-- Header -->
        <div class="mau-header">
          <div class="mau-title">
            <i class="bi" :class="tipo === 'foto' ? 'bi-images' : 'bi-folder2-open'"></i>
            <span>{{ tipo === 'foto' ? 'Fotos del Predio' : 'Documentos del Crédito' }}</span>
            <span class="mau-nro">Nro. {{ nroCredito }}</span>
          </div>
          <button class="mau-close" @click="cerrar" title="Cerrar">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>

        <!-- Body -->
        <div class="mau-body">

          <!-- Loading inicial -->
          <div v-if="loading" class="mau-estado">
            <div class="spin-lg"></div>
            <span>Cargando...</span>
          </div>

          <template v-else>

            <!-- Galería de fotos existentes -->
            <div v-if="archivos.length" class="mau-galeria">
              <div class="mau-galeria-titulo">
                <i class="bi bi-images"></i>
                {{ archivos.length }} foto{{ archivos.length !== 1 ? 's' : '' }} guardada{{ archivos.length !== 1 ? 's' : '' }}
              </div>
              <div class="mau-grid">
                <div v-for="a in archivos" :key="a.id" class="mau-item">
                  <div class="mau-thumb" @click="verArchivo(a.url)">
                    <img :src="fullUrl(a.url)" :alt="a.filename" loading="lazy" />
                    <div class="mau-thumb-hover"><i class="bi bi-zoom-in"></i></div>
                  </div>
                  <div class="mau-item-footer">
                    <span class="mau-fname" :title="a.filename">{{ a.filename }}</span>
                    <button
                      class="mau-del"
                      @click.stop="eliminar(a)"
                      :disabled="deletingId === a.id"
                      title="Eliminar"
                    >
                      <i class="bi" :class="deletingId === a.id ? 'bi-hourglass-split' : 'bi-trash-fill'"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Separador -->
            <div v-if="archivos.length" class="mau-sep"></div>

            <!-- Sección agregar: FOTOS con ImageUploaderPro (crop) -->
            <div v-if="tipo === 'foto'" class="mau-add-section">
              <div class="mau-add-label">
                <i class="bi bi-plus-circle"></i>
                Agregar foto nueva
              </div>
              <ImageUploaderPro
                :key="uploaderKey"
                label="Seleccionar foto del predio"
                :showRemove="false"
                :outputWidth="1200"
                outputFormat="jpeg"
                :outputQuality="0.85"
                @change="onImageReady"
              />
              <div v-if="uploading" class="mau-saving">
                <div class="spin-sm"></div>
                <span>Guardando foto...</span>
              </div>
              <div v-if="!archivos.length && !uploading" class="mau-empty-hint">
                <i class="bi bi-arrow-up-circle"></i>
                Sin fotos aún. Selecciona una imagen arriba para recortarla y guardarla.
              </div>
            </div>

            <!-- Sección agregar: DOCUMENTOS con input múltiple -->
            <div v-else class="mau-add-section">
              <div class="mau-add-label">
                <i class="bi bi-plus-circle"></i>
                Agregar documento
              </div>
              <input
                ref="fileInputRef"
                type="file"
                multiple
                accept=".pdf,.doc,.docx,image/*"
                style="display:none"
                @change="onFiles"
              />
              <button class="mau-btn-doc" @click="fileInputRef.click()" :disabled="uploading">
                <i class="bi bi-folder2-open"></i>
                Seleccionar archivos
              </button>
              <div v-if="uploading" class="mau-saving">
                <div class="spin-sm"></div>
                <span>Subiendo {{ uploadLabel }}</span>
              </div>
              <div v-if="!archivos.length && !uploading" class="mau-empty-hint">
                <i class="bi bi-arrow-up-circle"></i>
                Sin documentos aún. Selecciona archivos para subirlos.
              </div>
            </div>

          </template>

        </div>

        <!-- Footer -->
        <div class="mau-footer">
          <span class="mau-count">
            <i class="bi" :class="tipo === 'foto' ? 'bi-images' : 'bi-file-earmark'"></i>
            {{ archivos.length }} {{ tipo === 'foto' ? 'foto(s)' : 'documento(s)' }}
          </span>
          <button class="mau-btn-close" @click="cerrar">Cerrar</button>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'
import api from '@/services/apis'
import { showConfirm } from '@/utils/toast'
import ImageUploaderPro from '@/components/common/ImageUploaderPro.vue'

const props = defineProps({
  open:       { type: Boolean, default: false },
  nroCredito: { type: String,  default: null  },
  companyId:  { type: Number,  default: null  },
  tipo:       { type: String,  default: 'foto' },
})
const emit = defineEmits(['update:open'])

const archivos     = ref([])
const loading      = ref(false)
const uploading    = ref(false)
const uploadLabel  = ref('')
const deletingId   = ref(null)
const uploaderKey  = ref(0)
const fileInputRef = ref(null)

const API_BASE = import.meta.env.VITE_API_URL || ''

function fullUrl(u) {
  if (!u) return ''
  if (u.startsWith('http') || u.startsWith('blob:') || u.startsWith('data:')) return u
  return API_BASE + u
}

async function cargar() {
  if (!props.nroCredito || !props.companyId) return
  loading.value = true
  try {
    const { data } = await api.get(
      `/api/hipotecas/credito/${encodeURIComponent(props.nroCredito)}/adjuntos`,
      { params: { company_id: props.companyId, tipo: props.tipo } }
    )
    archivos.value = data
  } catch {
    archivos.value = []
  } finally {
    loading.value = false
  }
}

watch(() => props.open, (v) => {
  if (v) { archivos.value = []; uploaderKey.value = 0; cargar() }
})

// ── Fotos: recibe blob de ImageUploaderPro ────────────────────────────────────
async function onImageReady(blob) {
  if (!blob || uploading.value) return
  uploading.value = true
  try {
    const ext  = blob.type === 'image/webp' ? '.webp' : '.jpg'
    const file = new File([blob], `foto_${Date.now()}${ext}`, { type: blob.type || 'image/jpeg' })
    const fd   = new FormData()
    fd.append('file',       file)
    fd.append('company_id', String(props.companyId))
    fd.append('tipo',       props.tipo)
    const { data } = await api.post(
      `/api/hipotecas/credito/${encodeURIComponent(props.nroCredito)}/adjuntos`,
      fd
    )
    archivos.value.push(data)
    uploaderKey.value++  // reset ImageUploaderPro para la siguiente foto
  } catch (e) {
    console.error('Error al guardar foto:', e)
  } finally {
    uploading.value = false
  }
}

// ── Documentos: input múltiple ────────────────────────────────────────────────
async function onFiles(e) {
  const files = Array.from(e.target.files || [])
  e.target.value = ''
  if (!files.length) return
  uploading.value = true
  for (let i = 0; i < files.length; i++) {
    uploadLabel.value = `${i + 1}/${files.length}`
    const fd = new FormData()
    fd.append('file',       files[i])
    fd.append('company_id', String(props.companyId))
    fd.append('tipo',       props.tipo)
    try {
      const { data } = await api.post(
        `/api/hipotecas/credito/${encodeURIComponent(props.nroCredito)}/adjuntos`,
        fd
      )
      archivos.value.push(data)
    } catch { /* error silencioso por archivo */ }
  }
  uploading.value = false
  uploadLabel.value = ''
}

async function eliminar(a) {
  if (!(await showConfirm(`¿Eliminar "${a.filename}"?`))) return
  deletingId.value = a.id
  try {
    await api.delete(`/api/hipotecas/credito/adjunto/${a.id}`, {
      params: { company_id: props.companyId }
    })
    archivos.value = archivos.value.filter(x => x.id !== a.id)
  } catch { /* silencioso */ }
  deletingId.value = null
}

function verArchivo(url) {
  window.open(fullUrl(url), '_blank')
}

function cerrar() {
  emit('update:open', false)
}
</script>

<style scoped>
/* ── Overlay ── */
.mau-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.68);
  display: flex; align-items: flex-start; justify-content: center;
  z-index: 9990; padding: 16px; overflow-y: auto;
}

/* ── Modal ── */
.mau-modal {
  background: #fff; border-radius: 16px; overflow: hidden;
  width: 100%; max-width: 720px;
  display: flex; flex-direction: column;
  box-shadow: 0 24px 80px rgba(0,0,0,.35);
  margin: auto;
}

/* ── Header ── */
.mau-header {
  display: flex; align-items: center; justify-content: space-between; gap: 10px;
  padding: 14px 20px; background: #0f2448; flex-shrink: 0;
}
.mau-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 15px; font-weight: 700; color: #fff;
}
.mau-title .bi { font-size: 18px; color: #93c5fd; }
.mau-nro { font-size: 12px; font-weight: 400; opacity: .7; white-space: nowrap; }
.mau-close {
  background: none; border: none; color: rgba(255,255,255,.7);
  font-size: 16px; cursor: pointer; padding: 4px; line-height: 1;
}
.mau-close:hover { color: #fff; }

/* ── Body ── */
.mau-body { flex: 1; padding: 20px; overflow-y: auto; max-height: calc(80svh); max-height: calc(80vh); }

/* Estado loading */
.mau-estado {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 10px; min-height: 120px;
  color: #94a3b8; font-size: 14px;
}

/* ── Galería ── */
.mau-galeria { margin-bottom: 4px; }
.mau-galeria-titulo {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; font-weight: 700; color: #64748b;
  text-transform: uppercase; letter-spacing: .5px;
  margin-bottom: 10px;
}
.mau-galeria-titulo .bi { color: #0f2448; }

.mau-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 10px;
}
.mau-item {
  display: flex; flex-direction: column; gap: 4px;
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden;
}
.mau-thumb {
  position: relative; aspect-ratio: 1; cursor: pointer; overflow: hidden; background: #f1f5f9;
}
.mau-thumb img { width: 100%; height: 100%; object-fit: cover; display: block; transition: transform .2s; }
.mau-thumb:hover img { transform: scale(1.05); }
.mau-thumb-hover {
  position: absolute; inset: 0; background: rgba(0,0,0,.45);
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 22px; opacity: 0; transition: opacity .2s;
}
.mau-thumb:hover .mau-thumb-hover { opacity: 1; }

.mau-item-footer { display: flex; align-items: center; gap: 4px; padding: 5px 7px; }
.mau-fname {
  flex: 1; font-size: 10.5px; color: #475569;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.mau-del { background: none; border: none; color: #ef4444; font-size: 12px; cursor: pointer; padding: 2px; }
.mau-del:disabled { opacity: .4; cursor: default; }
.mau-del:not(:disabled):hover { color: #dc2626; }

/* Separador entre galería y uploader */
.mau-sep { border-top: 2px dashed #e2e8f0; margin: 18px 0; }

/* ── Sección agregar ── */
.mau-add-section { display: flex; flex-direction: column; gap: 10px; }
.mau-add-label {
  display: flex; align-items: center; gap: 7px;
  font-size: 13px; font-weight: 700; color: #0f2448;
}
.mau-add-label .bi { font-size: 16px; color: #22c55e; }

.mau-saving {
  display: flex; align-items: center; gap: 8px;
  background: #eff6ff; border-radius: 8px; padding: 8px 12px;
  font-size: 13px; color: #1d4ed8;
}
.mau-empty-hint {
  display: flex; align-items: center; gap: 8px;
  color: #94a3b8; font-size: 12px; padding: 8px 0;
}
.mau-empty-hint .bi { font-size: 18px; color: #cbd5e1; }

.mau-btn-doc {
  display: flex; align-items: center; gap: 6px;
  background: #f1f5f9; border: 1.5px solid #cbd5e1; color: #334155;
  border-radius: 10px; padding: 14px 20px; font-size: 14px; font-weight: 600;
  cursor: pointer; transition: .15s; width: 100%; justify-content: center;
}
.mau-btn-doc:hover:not(:disabled) { border-color: #0f2448; color: #0f2448; background: #eff6ff; }
.mau-btn-doc:disabled { opacity: .5; cursor: default; }

/* ── Footer ── */
.mau-footer {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 20px; border-top: 1px solid #e2e8f0; flex-shrink: 0;
}
.mau-count { display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600; color: #64748b; }
.mau-count .bi { color: #0f2448; }

.mau-btn-close {
  background: #f1f5f9; color: #475569; border: 1.5px solid #e2e8f0;
  border-radius: 8px; padding: 8px 20px; font-size: 13px;
  font-weight: 600; cursor: pointer; transition: .15s;
}
.mau-btn-close:hover { background: #e2e8f0; }

/* Spinners */
.spin-lg {
  width: 32px; height: 32px; border: 3px solid #e2e8f0;
  border-top-color: #0f2448; border-radius: 50%;
  animation: spin .7s linear infinite;
}
.spin-sm {
  width: 16px; height: 16px; border: 2px solid #bfdbfe;
  border-top-color: #1d4ed8; border-radius: 50%;
  animation: spin .7s linear infinite; flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Responsive ── */
@media (max-width: 768px) {
  .mau-grid { grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 8px; }
  .mau-body { padding: 14px; max-height: 75svh; max-height: 75vh; }
}
@media (max-width: 576px) {
  .mau-modal { border-radius: 12px; }
  .mau-header { padding: 12px 14px; }
  .mau-footer { padding: 10px 14px; }
  .mau-grid { grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 6px; }
}
</style>
