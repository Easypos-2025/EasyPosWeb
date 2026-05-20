<template>
  <div class="help-container">

    <!-- Header -->
    <div class="help-header">
      <h2 class="help-title"><i class="bi bi-question-circle me-2"></i>Centro de Ayuda</h2>
      <p class="help-subtitle">Encuentra guías y tutoriales para usar la plataforma</p>

      <div class="help-search-wrap">
        <i class="bi bi-search help-search-icon"></i>
        <input
          v-model="searchQuery"
          class="help-search"
          type="text"
          placeholder="Buscar por palabra clave..."
          @input="onSearch"
        />
        <button v-if="searchQuery" class="help-search-clear" @click="searchQuery = ''; onSearch()">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>
    </div>

    <!-- Cargando -->
    <div v-if="loading" class="help-loading">
      <div class="spinner-border text-primary" role="status"></div>
      <span>Cargando artículos...</span>
    </div>

    <!-- Sin resultados -->
    <div v-else-if="!loading && groupedArticles.length === 0" class="help-empty">
      <i class="bi bi-inbox"></i>
      <p>{{ searchQuery ? 'No se encontraron artículos para "' + searchQuery + '"' : 'No hay artículos disponibles' }}</p>
    </div>

    <!-- Grupos de categorías -->
    <div v-else class="help-groups">
      <div v-for="group in groupedArticles" :key="group.category" class="help-group">
        <h3 class="help-category-title">
          <i class="bi bi-folder2-open me-2"></i>{{ group.category }}
          <span class="help-count">{{ group.articles.length }}</span>
        </h3>

        <div class="help-cards">
          <div
            v-for="article in group.articles"
            :key="article.id"
            class="help-card"
            :class="{ expanded: expanded[article.id] }"
          >
            <!-- Card header — clic para expandir -->
            <div class="help-card-header" @click="toggle(article.id)">
              <div class="help-card-title">
                <i class="bi bi-file-earmark-text me-2 text-primary"></i>
                {{ article.title }}
              </div>
              <i class="bi help-chevron" :class="expanded[article.id] ? 'bi-chevron-up' : 'bi-chevron-down'"></i>
            </div>

            <!-- Card body — descripción + GIF -->
            <Transition name="help-expand">
              <div v-if="expanded[article.id]" class="help-card-body">
                <p v-if="article.description" class="help-description" v-html="formatDesc(article.description)"></p>
                <div v-if="article.gif_url" class="help-gif-wrap" @click="openLightbox(article.gif_url, article.title)">
                  <img
                    :src="article.gif_url"
                    :alt="article.title"
                    class="help-gif"
                    loading="lazy"
                  />
                  <div class="help-gif-zoom-hint"><i class="bi bi-zoom-in"></i> Clic para ampliar</div>
                </div>
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </div>

  </div>

  <!-- Lightbox GIF -->
  <teleport to="body">
    <Transition name="lightbox-fade">
      <div v-if="lightbox.open" class="help-lightbox" @click="closeLightbox" @keydown.esc="closeLightbox" tabindex="0">
        <button class="help-lb-close" @click.stop="closeLightbox"><i class="bi bi-x-lg"></i></button>
        <div class="help-lb-inner" @click.stop>
          <p class="help-lb-title">{{ lightbox.title }}</p>
          <img :src="lightbox.src" :alt="lightbox.title" class="help-lb-img" />
        </div>
      </div>
    </Transition>
  </teleport>
</template>

<script setup>
import { ref, computed } from "vue"
import api from "@/services/apis"
import { useModuleName } from "@/composables/useModuleName"

const { moduleName } = useModuleName()

const articles     = ref([])
const loading      = ref(false)
const searchQuery  = ref("")
const expanded     = ref({})
const lightbox     = ref({ open: false, src: "", title: "" })
let   searchTimer  = null

async function loadArticles() {
  loading.value = true
  try {
    const params = searchQuery.value.trim() ? { q: searchQuery.value.trim() } : {}
    const res = await api.get("/help/", { params })
    articles.value = res.data
  } catch {
    articles.value = []
  } finally {
    loading.value = false
  }
}

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(loadArticles, 300)
}

function toggle(id) {
  expanded.value = { ...expanded.value, [id]: !expanded.value[id] }
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

// Convierte saltos de línea en <br>
function formatDesc(text) {
  return text.replace(/\n/g, "<br>")
}

function openLightbox(src, title) {
  lightbox.value = { open: true, src, title }
  document.body.style.overflow = "hidden"
}
function closeLightbox() {
  lightbox.value.open = false
  document.body.style.overflow = ""
}

loadArticles()
</script>

<style scoped>
.help-container {
  padding: 24px;
  max-width: 860px;
  margin: 0 auto;
}

/* ── Header ── */
.help-header { margin-bottom: 28px; }

.help-title {
  font-size: 22px;
  font-weight: 700;
  color: #e2e8f0;
  margin-bottom: 4px;
}
.help-subtitle {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 18px;
}

/* ── Barra de búsqueda ── */
.help-search-wrap {
  position: relative;
  max-width: 480px;
}
.help-search-icon {
  position: absolute;
  left: 13px; top: 50%; transform: translateY(-50%);
  color: #64748b; font-size: 15px; pointer-events: none;
}
.help-search {
  width: 100%; padding: 10px 40px 10px 38px;
  background: #1e293b; border: 1px solid #334155;
  border-radius: 10px; color: #e2e8f0; font-size: 14px;
  outline: none; transition: border-color .2s;
}
.help-search:focus { border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,.2); }
.help-search::placeholder { color: #475569; }
.help-search-clear {
  position: absolute; right: 10px; top: 50%; transform: translateY(-50%);
  background: none; border: none; color: #64748b; cursor: pointer;
  font-size: 13px; padding: 4px;
}
.help-search-clear:hover { color: #e2e8f0; }

/* ── Loading / empty ── */
.help-loading, .help-empty {
  display: flex; flex-direction: column; align-items: center;
  gap: 12px; padding: 60px 0; color: #64748b; font-size: 14px;
}
.help-empty .bi { font-size: 36px; }

/* ── Grupos ── */
.help-groups { display: flex; flex-direction: column; gap: 28px; }

.help-category-title {
  font-size: 14px; font-weight: 700;
  color: #94a3b8; text-transform: uppercase; letter-spacing: .6px;
  display: flex; align-items: center; gap: 6px;
  margin-bottom: 12px; padding-bottom: 8px;
  border-bottom: 1px solid #1e293b;
}
.help-count {
  background: #334155; color: #94a3b8;
  font-size: 11px; font-weight: 700;
  border-radius: 20px; padding: 1px 8px;
  letter-spacing: 0;
}

/* ── Cards ── */
.help-cards { display: flex; flex-direction: column; gap: 8px; }

.help-card {
  background: #1e293b; border: 1px solid #334155;
  border-radius: 10px; overflow: hidden;
  transition: border-color .2s;
}
.help-card.expanded { border-color: #3b82f6; }

.help-card-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 16px; cursor: pointer; user-select: none;
  transition: background .15s;
}
.help-card-header:hover { background: rgba(59,130,246,.05); }

.help-card-title {
  font-size: 14px; font-weight: 600; color: #e2e8f0;
  display: flex; align-items: center;
}
.help-chevron { color: #64748b; font-size: 13px; flex-shrink: 0; }

/* ── Body ── */
.help-card-body { padding: 0 16px 18px; }

.help-description {
  font-size: 13px; line-height: 1.7; color: #94a3b8;
  margin-bottom: 14px; margin-top: 4px;
}

.help-gif-wrap {
  border-radius: 8px; overflow: hidden;
  border: 1px solid #334155; background: #0f172a;
  max-width: 100%; cursor: zoom-in; position: relative;
}
.help-gif-wrap:hover .help-gif-zoom-hint { opacity: 1; }
.help-gif-zoom-hint {
  position: absolute; bottom: 8px; right: 8px;
  background: rgba(0,0,0,.65); color: #fff;
  font-size: 11px; padding: 3px 9px; border-radius: 20px;
  pointer-events: none; opacity: 0; transition: opacity .2s;
  display: flex; align-items: center; gap: 4px;
}
.help-gif {
  display: block; width: 100%; max-height: 420px;
  object-fit: contain; transition: transform .2s;
}
.help-gif-wrap:hover .help-gif { transform: scale(1.01); }

/* ── Lightbox ── */
.help-lightbox {
  position: fixed; inset: 0; z-index: 99999;
  background: rgba(0,0,0,.88);
  display: flex; align-items: center; justify-content: center;
  padding: 20px; cursor: zoom-out;
  backdrop-filter: blur(6px);
}
.help-lb-close {
  position: absolute; top: 16px; right: 16px;
  background: rgba(255,255,255,.15); border: none; color: #fff;
  border-radius: 50%; width: 36px; height: 36px; font-size: 16px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: background .15s; z-index: 1;
}
.help-lb-close:hover { background: rgba(239,68,68,.6); }
.help-lb-inner {
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  max-width: 90vw; max-height: 90vh; cursor: default;
}
.help-lb-title {
  color: rgba(255,255,255,.8); font-size: 13px; font-weight: 600;
  text-align: center; margin: 0;
}
.help-lb-img {
  max-width: 90vw; max-height: 82vh;
  object-fit: contain; border-radius: 8px;
  box-shadow: 0 20px 60px rgba(0,0,0,.5);
}

/* Transición lightbox */
.lightbox-fade-enter-active, .lightbox-fade-leave-active { transition: opacity .2s; }
.lightbox-fade-enter-from, .lightbox-fade-leave-to       { opacity: 0; }

/* ── Transición expand ── */
.help-expand-enter-active,
.help-expand-leave-active { transition: opacity .2s, transform .2s; }
.help-expand-enter-from,
.help-expand-leave-to     { opacity: 0; transform: translateY(-6px); }

/* ── Responsive ── */
@media (max-width: 768px) {
  .help-container { padding: 16px; }
  .help-title     { font-size: 18px; }
  .help-card-header { padding: 12px 14px; }
  .help-card-title  { font-size: 13px; }
}
@media (max-width: 576px) {
  .help-container { padding: 12px; }
  .help-search-wrap { max-width: 100%; }
}
</style>
