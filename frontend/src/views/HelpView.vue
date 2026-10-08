<template>
  <div class="help-container" :class="{ 'show-detail': mobileDetail }">

    <!-- Header -->
    <div class="help-header">
      <h2 class="help-title"><i class="bi bi-question-circle me-2"></i>{{ moduleName || 'Centro de Ayuda' }}</h2>
      <p class="help-subtitle">Encuentra guías y tutoriales para usar la plataforma</p>
    </div>

    <div class="help-layout">

      <!-- ── Panel izquierdo: buscador + lista ── -->
      <aside class="help-sidebar">
        <div class="help-search-wrap">
          <i class="bi bi-search help-search-icon"></i>
          <input
            v-model="searchQuery"
            class="help-search"
            type="text"
            placeholder="Buscar por palabra clave..."
            maxlength="100"
            @input="onSearch"
          />
          <button v-if="searchQuery" class="help-search-clear" @click="searchQuery = ''; onSearch()" title="Limpiar">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>

        <div class="help-list">
          <div v-if="loading" class="help-loading">
            <div class="spinner-border spinner-border-sm text-primary" role="status"></div>
            <span>Cargando...</span>
          </div>

          <div v-else-if="!groupedArticles.length" class="help-empty">
            <i class="bi bi-inbox"></i>
            <p>{{ searchQuery ? `No se encontraron artículos para "${searchQuery}"` : 'No hay artículos disponibles' }}</p>
          </div>

          <template v-else>
            <div v-for="group in groupedArticles" :key="group.category" class="help-group">
              <div class="help-category-title">
                <i class="bi bi-folder2-open"></i>
                <span>{{ group.category }}</span>
                <span class="help-count">{{ group.articles.length }}</span>
              </div>
              <button
                v-for="article in group.articles"
                :key="article.id"
                :id="`help-item-${article.id}`"
                type="button"
                class="help-item"
                :class="{ active: selected?.id === article.id }"
                @click="selectArticle(article)"
              >
                <i class="bi" :class="article.gif_url ? 'bi-play-circle' : 'bi-file-earmark-text'"></i>
                <span class="help-item-title">{{ article.title }}</span>
                <i class="bi bi-chevron-right help-item-arrow"></i>
              </button>
            </div>
          </template>
        </div>
      </aside>

      <!-- ── Panel derecho: detalle ── -->
      <section class="help-detail" ref="detailRef">
        <template v-if="selected">
          <button type="button" class="help-back" @click="backToList">
            <i class="bi bi-arrow-left"></i> Volver
          </button>

          <div class="help-detail-cat"><i class="bi bi-folder2-open me-1"></i>{{ selected.category }}</div>
          <h3 class="help-detail-title">{{ selected.title }}</h3>

          <div v-if="selected.gif_url" class="help-gif-wrap" @click="openLightbox" title="Ver en pantalla completa">
            <video
              v-if="isVideo(selected.gif_url)"
              :key="selected.gif_url"
              :src="selected.gif_url"
              class="help-gif"
              autoplay loop muted playsinline
            ></video>
            <img v-else :key="selected.gif_url" :src="selected.gif_url" :alt="selected.title" class="help-gif" />
            <div class="help-gif-zoom-hint"><i class="bi bi-arrows-fullscreen"></i> Pantalla completa</div>
          </div>

          <p v-if="selected.description" class="help-description">{{ selected.description }}</p>
          <p v-else-if="!selected.gif_url" class="help-no-desc">Este artículo aún no tiene contenido.</p>
        </template>

        <div v-else class="help-placeholder">
          <i class="bi bi-hand-index"></i>
          <p>Selecciona un tema de la lista para ver la ayuda</p>
        </div>
      </section>

    </div>
  </div>

  <!-- Pantalla completa -->
  <teleport to="body">
    <Transition name="lightbox-fade">
      <div v-if="lightbox" class="help-lightbox" @click.self="closeLightbox">
        <button class="help-lb-close" @click="closeLightbox" title="Cerrar (Esc)">
          <i class="bi bi-x-lg"></i>
        </button>
        <p class="help-lb-title">{{ selected?.title }}</p>
        <video
          v-if="isVideo(selected?.gif_url)"
          :src="selected.gif_url"
          class="help-lb-img"
          autoplay loop muted playsinline controls
        ></video>
        <img v-else :src="selected?.gif_url" :alt="selected?.title" class="help-lb-img" />
      </div>
    </Transition>
  </teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick, onBeforeUnmount } from "vue"
import { useRoute, useRouter } from "vue-router"
import api from "@/services/apis"
import { useModuleName } from "@/composables/useModuleName"

const { moduleName } = useModuleName()
const route  = useRoute()
const router = useRouter()

const articles     = ref([])
const loading      = ref(false)
const searchQuery  = ref("")
const selected     = ref(null)
const mobileDetail = ref(false)   // en móvil: true = se ve el detalle, false = la lista
const lightbox     = ref(false)
const detailRef    = ref(null)
let   searchTimer  = null

function isVideo(url) {
  return /\.(mp4|webm)(\?|$)/i.test(url || "")
}

async function loadArticles() {
  loading.value = true
  try {
    const params = searchQuery.value.trim() ? { q: searchQuery.value.trim() } : {}
    const res = await api.get("/help/", { params })
    articles.value = Array.isArray(res.data) ? res.data : []
  } catch {
    articles.value = []
  } finally {
    loading.value = false
  }
  applySelection()
}

// Selecciona el artículo de ?article=ID; si no, conserva el actual o el primero (solo en pantallas grandes)
function applySelection() {
  const targetId = parseInt(route.query.article)
  const target = targetId ? articles.value.find(a => a.id === targetId) : null
  if (target) {
    selectArticle(target, false)
    return
  }
  if (selected.value && articles.value.some(a => a.id === selected.value.id)) return
  selected.value = null
  mobileDetail.value = false
  if (!isMobile() && articles.value.length) selected.value = groupedArticles.value[0].articles[0]
}

function isMobile() {
  return window.matchMedia("(max-width: 768px)").matches
}

function selectArticle(article, updateUrl = true) {
  selected.value = article
  mobileDetail.value = true
  if (updateUrl && String(route.query.article) !== String(article.id)) {
    router.replace({ query: { ...route.query, article: article.id } })
  }
  nextTick(() => {
    detailRef.value?.scrollTo?.({ top: 0 })
    document.getElementById(`help-item-${article.id}`)?.scrollIntoView({ block: "nearest" })
    if (isMobile()) window.scrollTo({ top: 0 })
  })
}

function backToList() {
  mobileDetail.value = false
  nextTick(() => {
    if (selected.value) document.getElementById(`help-item-${selected.value.id}`)?.scrollIntoView({ block: "center" })
  })
}

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(loadArticles, 300)
}

// Agrupa por categoría manteniendo el orden recibido
const groupedArticles = computed(() => {
  const map = new Map()
  for (const a of articles.value) {
    const cat = a.category || "General"
    if (!map.has(cat)) map.set(cat, [])
    map.get(cat).push(a)
  }
  return [...map.entries()].map(([category, arts]) => ({ category, articles: arts }))
})

// ── Pantalla completa ──
function onKeydown(e) {
  if (e.key === "Escape") closeLightbox()
}
function openLightbox() {
  lightbox.value = true
  document.body.style.overflow = "hidden"
  window.addEventListener("keydown", onKeydown)
}
function closeLightbox() {
  lightbox.value = false
  document.body.style.overflow = ""
  window.removeEventListener("keydown", onKeydown)
}

// El botón "?" puede cambiar ?article estando ya en esta vista
watch(() => route.query.article, (id) => {
  if (id && String(id) !== String(selected.value?.id)) applySelection()
})

onBeforeUnmount(() => {
  clearTimeout(searchTimer)
  closeLightbox()
})

loadArticles()
</script>

<style scoped>
.help-container {
  padding: 16px 16px 12px 12px;
  width: 100%;
}

/* ── Header ── */
.help-header { margin-bottom: 12px; }
.help-title {
  font-size: 22px; font-weight: 700; color: #0f172a;
  margin-bottom: 4px; display: flex; align-items: center;
}
.help-title .bi { color: #2563eb; }
.help-subtitle { font-size: 13px; color: #64748b; margin: 0; }

/* ── Layout dos paneles ── */
.help-layout {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 14px;
  height: calc(100vh - 170px);
  min-height: 460px;
}

/* ── Panel izquierdo ── */
.help-sidebar {
  display: flex; flex-direction: column; min-height: 0;
  background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
  box-shadow: 0 1px 3px rgba(15,23,42,.06);
  overflow: hidden;
}
.help-search-wrap {
  position: relative; padding: 12px; border-bottom: 1px solid #e2e8f0; background: #f8fafc;
}
.help-search-icon {
  position: absolute; left: 25px; top: 50%; transform: translateY(-50%);
  color: #94a3b8; font-size: 14px; pointer-events: none;
}
.help-search {
  width: 100%; padding: 9px 36px 9px 36px;
  background: #fff; border: 1px solid #cbd5e1;
  border-radius: 9px; color: #1e293b; font-size: 14px;
  outline: none; transition: border-color .2s;
}
.help-search:focus { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,.15); }
.help-search::placeholder { color: #94a3b8; }
.help-search-clear {
  position: absolute; right: 20px; top: 50%; transform: translateY(-50%);
  background: none; border: none; color: #64748b; cursor: pointer;
  font-size: 13px; padding: 4px;
}
.help-search-clear:hover { color: #dc2626; }

.help-list {
  flex: 1; overflow-y: auto; padding: 8px;
  scrollbar-width: thin; scrollbar-color: #cbd5e1 transparent;
}
.help-list::-webkit-scrollbar,
.help-detail::-webkit-scrollbar { width: 8px; }
.help-list::-webkit-scrollbar-thumb,
.help-detail::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 8px; }
.help-list::-webkit-scrollbar-thumb:hover,
.help-detail::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

.help-group + .help-group { margin-top: 10px; }
.help-category-title {
  display: flex; align-items: center; gap: 6px;
  font-size: 11px; font-weight: 700; color: #64748b;
  text-transform: uppercase; letter-spacing: .6px;
  padding: 8px 8px 6px;
}
.help-category-title span:first-of-type { flex: 1; }
.help-count {
  background: #f1f5f9; color: #475569; font-size: 11px; font-weight: 700;
  border-radius: 20px; padding: 1px 8px; letter-spacing: 0;
}

.help-item {
  display: flex; align-items: center; gap: 10px; width: 100%;
  background: transparent; border: none; border-left: 3px solid transparent;
  border-radius: 8px; padding: 10px 10px; margin-bottom: 2px;
  text-align: left; cursor: pointer; color: #334155; font-size: 13.5px;
  transition: background .15s, color .15s, border-color .15s;
}
.help-item > .bi:first-child { color: #94a3b8; font-size: 15px; flex-shrink: 0; }
.help-item:hover { background: #f1f5f9; color: #0f172a; }
.help-item.active {
  background: #eff6ff; color: #1d4ed8; font-weight: 600;
  border-left-color: #3b82f6;
}
.help-item.active > .bi:first-child { color: #3b82f6; }
.help-item-title { flex: 1; line-height: 1.35; }
.help-item-arrow { font-size: 11px; color: #cbd5e1; flex-shrink: 0; }
.help-item.active .help-item-arrow { color: #3b82f6; }

/* ── Panel derecho ── */
.help-detail {
  min-height: 0; overflow-y: auto;
  background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
  box-shadow: 0 1px 3px rgba(15,23,42,.06);
  padding: 24px 28px;
  scrollbar-width: thin; scrollbar-color: #cbd5e1 transparent;
}
.help-back { display: none; }

.help-detail-cat {
  display: inline-flex; align-items: center;
  font-size: 11px; font-weight: 700; color: #6d28d9;
  background: #f5f3ff; border: 1px solid #ddd6fe;
  border-radius: 6px; padding: 2px 8px; margin-bottom: 10px;
  text-transform: uppercase; letter-spacing: .4px;
}
.help-detail-title {
  font-size: 20px; font-weight: 700; color: #0f172a; margin: 0 0 16px;
}

.help-description {
  font-size: 14px; line-height: 1.75; color: #334155;
  white-space: pre-line; margin: 0;
}
.help-no-desc { color: #94a3b8; font-style: italic; }

.help-gif-wrap {
  position: relative; cursor: zoom-in;
  border-radius: 10px; overflow: hidden; margin-bottom: 18px;
  border: 1px solid #e2e8f0; background: #f8fafc;
}
.help-gif {
  display: block; width: 100%; max-height: 62vh; object-fit: contain;
}
.help-gif-zoom-hint {
  position: absolute; bottom: 10px; right: 10px;
  background: rgba(15,23,42,.72); color: #fff;
  font-size: 12px; padding: 4px 10px; border-radius: 20px;
  pointer-events: none; display: flex; align-items: center; gap: 6px;
  opacity: .85; transition: opacity .2s;
}
.help-gif-wrap:hover .help-gif-zoom-hint { opacity: 1; }

.help-placeholder, .help-loading, .help-empty {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 10px; color: #64748b; font-size: 14px; text-align: center;
}
.help-placeholder { height: 100%; }
.help-placeholder .bi { font-size: 40px; color: #cbd5e1; }
.help-loading, .help-empty { padding: 40px 12px; }
.help-empty .bi { font-size: 32px; color: #cbd5e1; }
.help-empty p { margin: 0; }

/* ── Pantalla completa ── */
.help-lightbox {
  position: fixed; inset: 0; z-index: 99999;
  background: rgba(15,23,42,.92);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 12px; padding: 56px 16px 20px;
}
.help-lb-close {
  position: absolute; top: 14px; right: 14px;
  background: rgba(255,255,255,.15); border: 1px solid rgba(255,255,255,.25); color: #fff;
  border-radius: 50%; width: 42px; height: 42px; font-size: 18px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: background .15s; z-index: 1;
}
.help-lb-close:hover { background: #ef4444; border-color: #ef4444; }
.help-lb-title {
  color: rgba(255,255,255,.9); font-size: 14px; font-weight: 600;
  text-align: center; margin: 0; max-width: 90vw;
}
.help-lb-img {
  max-width: 96vw; max-height: calc(100vh - 110px);
  object-fit: contain; border-radius: 8px;
  box-shadow: 0 20px 60px rgba(0,0,0,.5); background: #000;
}

.lightbox-fade-enter-active, .lightbox-fade-leave-active { transition: opacity .2s; }
.lightbox-fade-enter-from, .lightbox-fade-leave-to       { opacity: 0; }

/* ── Tablet ── */
@media (max-width: 992px) {
  .help-layout { grid-template-columns: 260px 1fr; gap: 14px; }
  .help-detail { padding: 20px; }
  .help-detail-title { font-size: 18px; }
}

/* ── Móvil: una sola columna, lista o detalle ── */
@media (max-width: 768px) {
  .help-container { padding: 16px; }
  .help-title     { font-size: 18px; }
  .help-header    { margin-bottom: 12px; }
  .help-layout {
    grid-template-columns: 1fr; height: auto; min-height: 0;
  }
  .help-list   { max-height: calc(100vh - 230px); }
  .help-detail { display: none; padding: 16px; overflow: visible; }

  .show-detail .help-sidebar { display: none; }
  .show-detail .help-detail  { display: block; }
  .show-detail .help-header  { display: none; }

  .help-back {
    display: inline-flex; align-items: center; gap: 6px;
    background: #eff6ff; border: 1px solid #bfdbfe; color: #1d4ed8;
    border-radius: 8px; padding: 7px 14px; font-size: 13px; font-weight: 600;
    cursor: pointer; margin-bottom: 14px;
  }
  .help-item { padding: 12px 10px; font-size: 14px; }
}
@media (max-width: 576px) {
  .help-container { padding: 10px; }
  .help-detail    { padding: 14px; }
  .help-detail-title { font-size: 17px; }
  .help-description  { font-size: 13.5px; }
  .help-gif { max-height: 320px; }
  .help-lb-close { width: 38px; height: 38px; top: 10px; right: 10px; }
}
</style>
