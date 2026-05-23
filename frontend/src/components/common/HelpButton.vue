<template>
  <button
    class="help-fab"
    :title="articleId ? 'Ver ayuda de esta vista' : 'Centro de ayuda'"
    @click="goToHelp"
  >
    <i class="bi bi-question-lg"></i>
  </button>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/apis'

const route  = useRoute()
const router = useRouter()
const articleId = ref(null)

async function fetchArticle(path) {
  try {
    const res = await api.get('/help/by-route', { params: { route: path } })
    articleId.value = res.data?.id ?? null
  } catch {
    articleId.value = null
  }
}

watch(() => route.path, path => fetchArticle(path), { immediate: true })

function goToHelp() {
  if (articleId.value) {
    router.push({ path: '/ayuda', query: { article: articleId.value } })
  } else {
    router.push('/ayuda')
  }
}
</script>

<style scoped>
.help-fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 800;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #1d4ed8;
  color: #fff;
  border: none;
  box-shadow: 0 4px 16px rgba(29, 78, 216, 0.45);
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.15s, transform 0.15s, box-shadow 0.15s;
}
.help-fab:hover {
  background: #1e40af;
  transform: scale(1.08);
  box-shadow: 0 6px 22px rgba(29, 78, 216, 0.55);
}
.help-fab:active { transform: scale(0.96); }

@media (max-width: 768px) {
  .help-fab { bottom: 18px; right: 16px; width: 40px; height: 40px; font-size: 18px; }
}
@media (max-width: 576px) {
  .help-fab { bottom: 14px; right: 12px; width: 38px; height: 38px; font-size: 17px; }
}
</style>
